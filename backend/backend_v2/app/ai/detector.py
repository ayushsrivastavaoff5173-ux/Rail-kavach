
import time
import cv2
from sympy import python
from ultralytics import YOLO


class RailKavachDetector:

    def __init__(self, model_path="yolov8n.pt"):
        print("Loading RailKavach AI Model...")

        self.model = YOLO(model_path)

        self.last_inference_time = 0
        self.fps = 0

        print("AI Model Loaded Successfully!")

    def detect(self, frame):
        start_time = time.perf_counter()

        results = self.model.track(
            source=frame,
            classes=[0],
            conf=0.05,
            imgsz=640,
            persist=True,
            verbose=False
        )

        detections = []

        for result in results:
            boxes = result.boxes

            if boxes is None:
                continue

            for box in boxes:
                track_id = None

                if box.id is not None:
                    track_id = int(box.id[0])

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                confidence = float(box.conf[0])

                detections.append({
                    "class": "person",
                    "id": track_id,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2]
                })

        elapsed = time.perf_counter() - start_time

        self.last_inference_time = elapsed * 1000

        if elapsed > 0:
            self.fps = 1 / elapsed

        return detections

    def draw_detections(self, frame, detections):
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            confidence = detection["confidence"]
            track_id = detection.get("id")

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            if track_id is not None:
                label = f"Person ID: {track_id} | {confidence:.2f}"
            else:
                label = f"Person | {confidence:.2f}"

            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        return frame



