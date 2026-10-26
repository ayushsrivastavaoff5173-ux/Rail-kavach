import cv2
import time
import numpy as np

from app.ai.detector import RailKavachDetector


class VideoManager:

    def __init__(self, video_source=0):

        self.video_source = video_source

        self.detector = RailKavachDetector()

        self.cap = None

        self.running = False

        self.frame_count = 0

        self.start_time = time.time()

        self.fps = 0

        self.current_stats = {
            "people_count": 0,
            "density": "NORMAL",
            "alert": False,
            "zone_count": 0,
            "zone_alert": False,
            "fps": 0
        }

        # Crowd monitoring zone
        self.zone_points = np.array([
            (100, 100),
            (500, 100),
            (500, 400),
            (100, 400)
        ], dtype=np.int32)

        self.zone_alert = False

    # -----------------------------------
    # START CAMERA
    # -----------------------------------

    def start(self):

        if self.running and self.cap is not None:
            if self.cap.isOpened():
                print("Camera already running")
                return

        self.cap = cv2.VideoCapture(self.video_source)

        if not self.cap.isOpened():

            self.cap.release()
            self.cap = None

            raise RuntimeError(
                "Unable to open video source"
            )

        self.running = True

        self.frame_count = 0

        self.start_time = time.time()

        print("RailKavach Video Engine Started")

    # -----------------------------------
    # PROCESS FRAME
    # -----------------------------------

    def process_frame(self):

        if not self.running or self.cap is None:

            return None, None

        success, frame = self.cap.read()

        if not success:

            print("Unable to read camera frame")

            return None, None

        # -----------------------------------
        # AI DETECTION
        # -----------------------------------

        detections = self.detector.detect(frame)

        annotated_frame = self.detector.draw_detections(
            frame,
            detections
        )

        people_count = len(detections)

        zone_count = 0

        # -----------------------------------
        # CROWD ZONE DETECTION
        # -----------------------------------

        for detection in detections:

            x1, y1, x2, y2 = detection["bbox"]

            center_x = int((x1 + x2) / 2)

            center_y = int((y1 + y2) / 2)

            center = (
                float(center_x),
                float(center_y)
            )

            result = cv2.pointPolygonTest(
                self.zone_points,
                center,
                False
            )

            if result >= 0:

                zone_count += 1

        # -----------------------------------
        # CROWD ALERT
        # -----------------------------------

        self.zone_alert = zone_count > 5

        # -----------------------------------
        # CROWD DENSITY
        # -----------------------------------

        if people_count <= 5:

            density = "NORMAL"

            alert_color = (0, 255, 0)

        elif people_count <= 15:

            density = "MEDIUM"

            alert_color = (0, 255, 255)

        else:

            density = "HIGH"

            alert_color = (0, 0, 255)

        alert = density == "HIGH"

        # -----------------------------------
        # FPS CALCULATION
        # -----------------------------------

        self.frame_count += 1

        elapsed_time = time.time() - self.start_time

        if elapsed_time > 0:

            self.fps = round(
                self.frame_count / elapsed_time,
                2
            )

        # -----------------------------------
        # DRAW CROWD ZONE
        # -----------------------------------

        cv2.polylines(
            annotated_frame,
            [self.zone_points],
            True,
            (
                (0, 0, 255)
                if self.zone_alert
                else (0, 255, 0)
            ),
            2
        )

        # -----------------------------------
        # PEOPLE COUNT
        # -----------------------------------

        cv2.putText(
            annotated_frame,
            f"People Count: {people_count}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # -----------------------------------
        # CROWD DENSITY
        # -----------------------------------

        cv2.putText(
            annotated_frame,
            f"Crowd Density: {density}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            alert_color,
            2
        )

        # -----------------------------------
        # FPS
        # -----------------------------------

        cv2.putText(
            annotated_frame,
            f"FPS: {self.fps}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # -----------------------------------
        # ZONE COUNT
        # -----------------------------------

        cv2.putText(
            annotated_frame,
            f"Zone People: {zone_count}",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # -----------------------------------
        # HIGH CROWD ALERT
        # -----------------------------------

        if density == "HIGH":

            cv2.putText(
                annotated_frame,
                "HIGH CROWD ALERT!",
                (20, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                alert_color,
                2
            )

        # -----------------------------------
        # ZONE ALERT
        # -----------------------------------

        if self.zone_alert:

            cv2.putText(
                annotated_frame,
                "ZONE CROWD ALERT!",
                (20, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        # -----------------------------------
        # UPDATE STATISTICS
        # -----------------------------------

        self.current_stats = {

            "people_count": people_count,

            "density": density,

            "alert": alert,

            "zone_count": zone_count,

            "zone_alert": self.zone_alert,

            "fps": self.fps

        }

        return annotated_frame, detections

    # -----------------------------------
    # LIVE CAMERA WINDOW
    # -----------------------------------

    def show_live_camera(self):

        if not self.running:

            self.start()

        print(
            "RailKavach Live Camera Started"
        )

        print(
            "Press Q to close camera window"
        )

        try:

            while self.running:

                frame, detections = self.process_frame()

                if frame is None:

                    print(
                        "Camera frame unavailable"
                    )

                    break

                cv2.imshow(
                    "RailKavach - Live AI Detection",
                    frame
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):

                    break

        except Exception as e:

            print(
                f"Live Camera Error: {e}"
            )

        finally:

            self.stop()

    # -----------------------------------
    # STOP CAMERA
    # -----------------------------------

    def stop(self):

        self.running = False

        if self.cap is not None:

            self.cap.release()

            self.cap = None

        cv2.destroyAllWindows()

        print(
            "RailKavach Video Engine Stopped"
        )