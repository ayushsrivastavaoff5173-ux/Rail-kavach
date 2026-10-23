import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from schemas.telemetry import TelemetryMessage
from services.alert_service import AlertService
from services.connection_manager import ConnectionManager
from services.detector import PersonDetector
from services.video_processor import VideoProcessor
from services.zone_service import ZoneService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("railkavach.main")

detector = PersonDetector()
zone_service = ZoneService(settings.ZONE_NAME, settings.ZONE_POLYGON)
alert_service = AlertService()
processor = VideoProcessor(detector, zone_service, alert_service)
manager = ConnectionManager()


class SourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


def build_telemetry_json() -> str:
    return TelemetryMessage(**processor.get_telemetry()).model_dump_json()


async def telemetry_loop() -> None:
    while True:
        try:
            if manager.count > 0:
                await manager.broadcast(build_telemetry_json())
        except Exception:
            logger.exception("Telemetry broadcast failed")
        await asyncio.sleep(settings.TELEMETRY_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    processor.start()
    task = asyncio.create_task(telemetry_loop())
    logger.info("RailKavach backend started")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.info("Telemetry loop stopped")
    await asyncio.to_thread(processor.stop)
    logger.info("RailKavach backend stopped")


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "endpoints": ["/health", "/alerts", "/sources", "/source", "/video_feed", "/ws/telemetry"],
    }


@app.get("/health")
async def health():
    return {
        "backend": "ok",
        "model": {
            "loaded": detector.loaded,
            "name": detector.model_name,
            "error": detector.error,
        },
        "videoProcessing": processor.get_health(),
        "websocket": {
            "available": True,
            "endpoint": "/ws/telemetry",
            "connectedClients": manager.count,
        },
    }


@app.get("/alerts")
async def get_alerts(limit: int = Query(20, ge=1, le=100)):
    return {"alerts": alert_service.recent(limit)}


@app.get("/sources")
async def get_sources():
    return processor.get_sources()


@app.post("/source")
async def change_source(body: SourceRequest):
    try:
        processor.set_source(body.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"requested": body.name}


async def mjpeg_stream(request: Request):
    last_frame = None
    while True:
        if await request.is_disconnected():
            break
        frame = processor.get_jpeg()
        if frame is not last_frame and frame:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            last_frame = frame
        await asyncio.sleep(0.05)


@app.get("/video_feed")
async def video_feed(request: Request):
    return StreamingResponse(
        mjpeg_stream(request),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.websocket("/ws/telemetry")
async def telemetry_ws(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        logger.warning("Rejected WebSocket from origin %s", origin)
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        await websocket.send_text(build_telemetry_json())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        manager.disconnect(websocket)
        