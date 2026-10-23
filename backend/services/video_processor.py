import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Union

import cv2
import numpy as np

from config import settings
from schemas import telemetry as t
from services.alert_service import AlertService
from services.detector import PersonDetector
from services.zone_service import ZoneService

logger = logging.getLogger("railkavach.video")

STATUS_COLORS = {
    settings.STATUS_GREEN: (0, 200, 0),
    settings.STATUS_YELLOW: (0, 200, 255),
    settings.STATUS_RED: (0, 0, 255),
}

PLACEHOLDER_TITLES = {
    t.PROCESSING_STARTING: "STARTING",
    t.PROCESSING_NO_SOURCE: "NO VIDEO SOURCE",
    t.PROCESSING_MODEL_UNAVAILABLE: "AI MODEL UNAVAILABLE",
    t.PROCESSING_ERROR: "PROCESSING ERROR",
}


class VideoProcessor:
    def __init__(self, detector: PersonDetector, zone_service: ZoneService, alert_service: AlertService) -> None:
        self.detector = detector
        self.zone_service = zone_service
        self.alert_service = alert_service

        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._source_changed = threading.Event()
        self._lock = threading.Lock()
        self._requested_source = settings.DEFAULT_SOURCE
        self._state: Dict = {
            "status": t.PROCESSING_STARTING,
            "error": None,
            "personCount": 0,
            "density": settings.STATUS_OFFLINE,
            "fps": 0.0,
            "source": "none",
        }
        self._jpeg: bytes = self._make_placeholder(t.PROCESSING_STARTING, "Loading AI model, please wait...")

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="video-processor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._source_changed.set()
        if self._thread is not None:
            self._thread.join(timeout=10)

    def set_source(self, name: str) -> None:
        sources = settings.get_available_sources()
        if name not in sources:
            raise ValueError(f"Unknown source '{name}'. Available: {', '.join(sources)}")
        with self._lock:
            self._requested_source = name
        self._source_changed.set()

    def get_sources(self) -> Dict:
        with self._lock:
            requested = self._requested_source
        return {"requested": requested, "available": list(settings.get_available_sources())}

    def get_jpeg(self) -> bytes:
        with self._lock:
            return self._jpeg

    def get_health(self) -> Dict:
        with self._lock:
            state = dict(self._state)
            requested = self._requested_source
        return {
            "status": state["status"],
            "error": state["error"],
            "requestedSource": requested,
            "activeSource": state["source"],
            "threadAlive": self._thread is not None and self._thread.is_alive(),
        }

    def get_telemetry(self) -> Dict:
        with self._lock:
            state = dict(self._state)

        running = state["status"] == t.PROCESSING_RUNNING
        density = state["density"] if running else settings.STATUS_OFFLINE

        return {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "zone": settings.ZONE_NAME,
            "personCount": state["personCount"] if running else 0,
            "maxCapacity": settings.MAX_CAPACITY,
            "densityStatus": density,
            "fps": state["fps"] if running else 0.0,
            "evacuationRoute": settings.EVACUATION_TEXT[density],
            "activeSource": state["source"] if running else "none",
            "status": state["status"],
            "error": state["error"],
            "alerts": self.alert_service.recent(5),
        }

    def _run(self) -> None:
        if not self.detector.load():
            self._go_offline(
                t.PROCESSING_MODEL_UNAVAILABLE,
                self.detector.error or "AI model could not be loaded",
                "AI_MODEL_UNAVAILABLE",
                "CRITICAL",
            )

        while not self._stop.is_set():
            if not self.detector.loaded:
                self._stop.wait(1.0)
                continue

            self._source_changed.clear()
            with self._lock:
                name = self._requested_source

            sources = settings.get_available_sources()
            if name not in sources:
                self._go_offline(
                    t.PROCESSING_NO_SOURCE,
                    f"Video source '{name}' not found. Put the video inside backend/videos/ or use 'webcam'.",
                    "CAMERA_DISCONNECTED",
                    "WARNING",
                )
            else:
                self._process_source(name, sources[name])

            if not self._stop.is_set() and not self._source_changed.is_set():
                self._source_changed.wait(timeout=settings.CAMERA_RETRY_SECONDS)

    def _open_capture(self, name: str, source: Union[int, str]) -> cv2.VideoCapture:
        if name == settings.WEBCAM_SOURCE_NAME:
            backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
            return cv2.VideoCapture(int(source), backend)
        return cv2.VideoCapture(str(source))

    def _process_source(self, name: str, source: Union[int, str]) -> None:
        is_file = name != settings.WEBCAM_SOURCE_NAME
        cap = None

        try:
            cap = self._open_capture(name, source)
            if not cap.isOpened():
                if is_file:
                    message = f"Could not open video file '{name}'. It may be corrupted or use an unsupported codec."
                else:
                    message = "Webcam not available. Connect a camera and close other apps that use it."
                self._go_offline(t.PROCESSING_NO_SOURCE, message, "CAMERA_DISCONNECTED", "WARNING")
                return

            native_fps = cap.get(cv2.CAP_PROP_FPS) if is_file else 0.0
            frame_interval = 1.0 / native_fps if 1.0 <= native_fps <= 120.0 else 0.0

            fps = 0.0
            frames_since_rewind = 0
            logger.info("Processing source: %s", name)

            while not self._stop.is_set() and not self._source_changed.is_set():
                loop_start = time.perf_counter()

                ok, frame = cap.read()
                if not ok or frame is None:
                    if is_file and settings.LOOP_VIDEO_FILES and frames_since_rewind > 0:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        frames_since_rewind = 0
                        continue
                    if is_file:
                        message = f"Video file '{name}' ended or could not be read."
                    else:
                        message = "Webcam stopped sending frames (camera disconnected?)."
                    self._go_offline(t.PROCESSING_NO_SOURCE, message, "CAMERA_DISCONNECTED", "WARNING")
                    return

                frames_since_rewind += 1

                detections = self.detector.detect(frame)
                height, width = frame.shape[:2]

                inside: List = []
                outside: List = []
                for detection in detections:
                    if self.zone_service.contains(detection, width, height):
                        inside.append(detection)
                    else:
                        outside.append(detection)

                count = len(inside)
                density = self._classify(count)
                jpeg = self._annotate_and_encode(frame, inside, outside, count, density)

                elapsed = time.perf_counter() - loop_start
                instant = 1.0 / elapsed if elapsed > 0 else 0.0
                fps = instant if fps == 0.0 else 0.9 * fps + 0.1 * instant

                self._update_running(count, density, round(fps, 1), name, jpeg)
                self._raise_crowd_alert(count, density)

                if frame_interval > elapsed:
                    self._stop.wait(frame_interval - elapsed)
        except Exception as exc:
            logger.exception("Video processing failed")
            self._go_offline(
                t.PROCESSING_ERROR,
                f"Video processing failed: {exc}",
                "VIDEO_PROCESSING_FAILURE",
                "CRITICAL",
            )
        finally:
            if cap is not None:
                cap.release()

    def _classify(self, count: int) -> str:
        ratio = count / settings.MAX_CAPACITY
        if ratio >= settings.RED_RATIO:
            return settings.STATUS_RED
        if ratio >= settings.YELLOW_RATIO:
            return settings.STATUS_YELLOW
        return settings.STATUS_GREEN

    def _raise_crowd_alert(self, count: int, density: str) -> None:
        if density == settings.STATUS_RED:
            self.alert_service.raise_alert(
                "CROWD_CRITICAL",
                "CRITICAL",
                f"Critical crowd: {count} people detected, configured capacity {settings.MAX_CAPACITY}",
                settings.ZONE_NAME,
            )
        elif density == settings.STATUS_YELLOW:
            self.alert_service.raise_alert(
                "CROWD_WARNING",
                "WARNING",
                f"Crowd warning: {count} people detected, configured capacity {settings.MAX_CAPACITY}",
                settings.ZONE_NAME,
            )

    def _update_running(self, count: int, density: str, fps: float, source: str, jpeg: bytes) -> None:
        with self._lock:
            self._state = {
                "status": t.PROCESSING_RUNNING,
                "error": None,
                "personCount": count,
                "density": density,
                "fps": fps,
                "source": source,
            }
            self._jpeg = jpeg

    def _go_offline(self, status: str, message: str, alert_type: str, severity: str) -> None:
        logger.warning("%s: %s", status, message)
        placeholder = self._make_placeholder(status, message)
        with self._lock:
            self._state = {
                "status": status,
                "error": message,
                "personCount": 0,
                "density": settings.STATUS_OFFLINE,
                "fps": 0.0,
                "source": "none",
            }
            self._jpeg = placeholder
        self.alert_service.raise_alert(alert_type, severity, message, settings.ZONE_NAME)

    def _annotate_and_encode(self, frame, inside: List, outside: List, count: int, density: str) -> bytes:
        height, width = frame.shape[:2]
        color = STATUS_COLORS.get(density, (200, 200, 200))
        scale = max(0.6, width / 1280.0)
        thickness = max(2, int(width / 640))

        polygon = self.zone_service.polygon_pixels(width, height)
        if polygon is not None:
            cv2.polylines(frame, [polygon], True, (255, 200, 0), thickness)

        for x1, y1, x2, y2, _ in outside:
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (150, 150, 150), 1)

        for x1, y1, x2, y2, _ in inside:
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)

        bar_height = int(40 * scale)
        cv2.rectangle(frame, (0, 0), (width, bar_height), (0, 0, 0), -1)
        label = f"{settings.ZONE_NAME}  Count: {count}/{settings.MAX_CAPACITY}  {density}"
        cv2.putText(frame, label, (10, int(28 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.8 * scale, color, 2)

        if width > settings.STREAM_MAX_WIDTH:
            new_height = int(height * settings.STREAM_MAX_WIDTH / width)
            frame = cv2.resize(frame, (settings.STREAM_MAX_WIDTH, new_height), interpolation=cv2.INTER_AREA)

        ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, settings.JPEG_QUALITY])
        if not ok:
            raise RuntimeError("Could not encode frame as JPEG")
        return buffer.tobytes()

    def _make_placeholder(self, status: str, detail: str) -> bytes:
        title = PLACEHOLDER_TITLES.get(status, "NO VIDEO")
        image = np.zeros((540, 960, 3), dtype=np.uint8)
        cv2.putText(image, title, (40, 240), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        cv2.putText(image, detail[:70], (40, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
        if len(detail) > 70:
            cv2.putText(image, detail[70:140], (40, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
        ok, buffer = cv2.imencode(".jpg", image)
        return buffer.tobytes() if ok else b""