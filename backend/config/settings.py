import os
from pathlib import Path
from typing import Dict, Optional, Union

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "videos"

APP_NAME = "RailKavach AI Backend"
APP_VERSION = "0.1.0"

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

MODEL_FILE = BASE_DIR / "yolov8n.pt"
PERSON_CLASS_ID = 0
CONFIDENCE_THRESHOLD = 0.35
INFERENCE_IMAGE_SIZE = 640

WEBCAM_SOURCE_NAME = "webcam"
WEBCAM_INDEX = 0
ALLOWED_VIDEO_EXTENSIONS = (".mp4", ".avi", ".mov", ".mkv")

DEFAULT_SOURCE = os.getenv("RAILKAVACH_SOURCE", WEBCAM_SOURCE_NAME)

LOOP_VIDEO_FILES = True
CAMERA_RETRY_SECONDS = 5

STREAM_MAX_WIDTH = 960
JPEG_QUALITY = 70
TELEMETRY_INTERVAL_SECONDS = 0.5

ZONE_NAME = "FOB-1 (Charbagh North)"
ZONE_POLYGON: Optional[list] = None

MAX_CAPACITY = 45
YELLOW_RATIO = 0.75
RED_RATIO = 1.00

STATUS_GREEN = "GREEN"
STATUS_YELLOW = "YELLOW"
STATUS_RED = "RED"
STATUS_OFFLINE = "OFFLINE"

EVACUATION_TEXT = {
    STATUS_GREEN: "All clear. Normal passenger flow.",
    STATUS_YELLOW: "Moderate crowd buildup. Demo guidance: stand by for gate control.",
    STATUS_RED: "High crowd density. Demo guidance: divert passengers to the alternate bridge "
                "(configured demo text, not an official instruction).",
    STATUS_OFFLINE: "No live video source. Crowd monitoring is NOT active.",
}

ALERT_COOLDOWN_SECONDS = 30
MAX_STORED_ALERTS = 100

if MAX_CAPACITY <= 0:
    raise ValueError("MAX_CAPACITY must be greater than 0")
if not (0 < YELLOW_RATIO < RED_RATIO):
    raise ValueError("Thresholds must satisfy 0 < YELLOW_RATIO < RED_RATIO")


def get_available_sources() -> Dict[str, Union[int, str]]:
    sources: Dict[str, Union[int, str]] = {WEBCAM_SOURCE_NAME: WEBCAM_INDEX}
    if VIDEOS_DIR.is_dir():
        for path in sorted(VIDEOS_DIR.iterdir()):
            if path.is_file() and path.suffix.lower() in ALLOWED_VIDEO_EXTENSIONS:
                sources[path.name] = str(path)
    return sources