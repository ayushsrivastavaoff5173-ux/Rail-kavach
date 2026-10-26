from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

import threading
import os
import uuid
import cv2

from app.videos.video_manager import VideoManager

router = APIRouter()

video_manager = None

UPLOAD_DIR = os.path.abspath("uploads")
PROCESSED_DIR = os.path.join(UPLOAD_DIR, "processed")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


@router.get("/status")
def get_status():
    return {
        "project": "RailKavach",
        "status": "online",
        "version": "2.0"
    }


@router.post("/video/start")
def start_video():
    global video_manager

    try:
        if video_manager is not None:
            video_manager.stop()
            video_manager = None

        video_manager = VideoManager(video_source=0)
        video_manager.start()

        return {
            "status": "video_started",
            "camera_open": True
        }

    except Exception as e:
        video_manager = None

        raise HTTPException(
            status_code=500,
            detail=f"Camera failed: {str(e)}"
        )


@router.post("/video/live")
def start_live_camera():
    global video_manager

    try:
        if video_manager is None:
            video_manager = VideoManager(video_source=0)

        if not video_manager.running:
            video_manager.start()

        camera_thread = threading.Thread(
            target=video_manager.show_live_camera,
            daemon=True
        )

        camera_thread.start()

        return {
            "status": "live_camera_started",
            "message": "Live camera window started"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/video/detect")
def detect_people():
    global video_manager

    if video_manager is None:
        raise HTTPException(
            status_code=400,
            detail="Video not started. Start webcam first."
        )

    try:
        frame, detections = video_manager.process_frame()

        if frame is None:
            raise HTTPException(
                status_code=500,
                detail="Unable to read video frame"
            )

        return {
            "status": "success",
            "people_detected": len(detections),
            "detections": detections
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/video/stats")
def get_crowd_stats():
    global video_manager

    if video_manager is None:
        raise HTTPException(
            status_code=400,
            detail="Video not started. Start webcam first."
        )

    return {
        "status": "success",
        "crowd_stats": video_manager.current_stats
    }


@router.post("/video/upload")
def upload_video(file: UploadFile = File(...)):
    input_path = None
    output_path = None
    manager = None
    writer = None

    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is missing"
            )

        extension = os.path.splitext(file.filename)[1].lower()

        allowed_extensions = [
            ".mp4",
            ".avi",
            ".mov",
            ".mkv"
        ]

        if extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail="Unsupported video format"
            )

        video_id = uuid.uuid4().hex

        input_filename = f"{video_id}_input{extension}"
        output_filename = f"{video_id}_processed.mp4"

        input_path = os.path.join(
            UPLOAD_DIR,
            input_filename
        )

        output_path = os.path.join(
            PROCESSED_DIR,
            output_filename
        )

        with open(input_path, "wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                buffer.write(chunk)

        manager = VideoManager(video_source=input_path)
        manager.start()

        cap = manager.cap

        fps = cap.get(cv2.CAP_PROP_FPS)

        width = int(
            cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        )

        height = int(
            cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

        total_frames = int(
            cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )

        if fps <= 0:
            fps = 25.0

        if width <= 0 or height <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid video dimensions"
            )

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        writer = cv2.VideoWriter(
            output_path,
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():
            raise RuntimeError(
                "Unable to create processed video"
            )

        processed_frames = 0

        while True:
            frame, detections = manager.process_frame()

            if frame is None:
                break

            writer.write(frame)
            processed_frames += 1

        writer.release()
        writer = None

        manager.stop()
        manager = None

        if not os.path.exists(output_path):
            raise RuntimeError(
                "Processed video was not generated"
            )

        if os.path.getsize(output_path) == 0:
            raise RuntimeError(
                "Processed video is empty"
            )

        return {
            "status": "success",
            "message": "Video processed successfully",
            "original_filename": file.filename,
            "processed_filename": output_filename,
            "processed_video_url": f"/video/processed/{output_filename}",
            "download_url": f"/video/processed/{output_filename}",
            "total_frames": total_frames,
            "processed_frames": processed_frames
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video processing failed: {str(e)}"
        )

    finally:
        if writer is not None:
            writer.release()

        if manager is not None:
            manager.stop()

        file.file.close()


@router.get("/video/processed/{filename}")
def download_processed_video(filename: str):
    if os.path.basename(filename) != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename"
        )

    if not filename.endswith("_processed.mp4"):
        raise HTTPException(
            status_code=400,
            detail="Invalid processed video filename"
        )

    file_path = os.path.join(
        PROCESSED_DIR,
        filename
    )

    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=404,
            detail="Processed video not found"
        )

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename
    )

