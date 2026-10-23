import logging
from typing import List, Optional, Tuple

from config import settings

logger = logging.getLogger("railkavach.detector")

Detection = Tuple[float, float, float, float, float]


class PersonDetector:
    def __init__(self) -> None:
        self.model = None
        self.loaded = False
        self.error: Optional[str] = None
        self.model_name = "yolov8n.pt"

    def load(self) -> bool:
        try:
            from ultralytics import YOLO

            if settings.MODEL_FILE.exists():
                model_path = str(settings.MODEL_FILE)
            else:
                logger.info("yolov8n.pt not found locally, ultralytics will try to download it")
                model_path = "yolov8n.pt"

            model = YOLO(model_path)
            class_name = model.names.get(settings.PERSON_CLASS_ID)
            if class_name != "person":
                raise RuntimeError(
                    f"Class {settings.PERSON_CLASS_ID} is '{class_name}', expected 'person'"
                )

            self.model = model
            self.loaded = True
            self.error = None
            logger.info("YOLO model loaded")
            return True
        except Exception as exc:
            self.model = None
            self.loaded = False
            self.error = f"Could not load YOLO model: {exc}"
            logger.exception("Model loading failed")
            return False

    def detect(self, frame) -> List[Detection]:
        if not self.loaded or self.model is None:
            raise RuntimeError("YOLO model is not loaded")

        results = self.model.predict(
            frame,
            classes=[settings.PERSON_CLASS_ID],
            conf=settings.CONFIDENCE_THRESHOLD,
            imgsz=settings.INFERENCE_IMAGE_SIZE,
            verbose=False,
        )
        if not results:
            return []

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []

        detections: List[Detection] = []
        for xyxy, conf, cls in zip(boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist()):
            if int(cls) != settings.PERSON_CLASS_ID:
                continue
            x1, y1, x2, y2 = xyxy
            detections.append((x1, y1, x2, y2, conf))
        return detections
    