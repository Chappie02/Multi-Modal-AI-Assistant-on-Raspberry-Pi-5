import logging
import os
import time
from datetime import datetime
from typing import Optional, Tuple
import sys

sys.path.append("/usr/lib/python3/dist-packages")
try:
    from picamera2 import Picamera2
except Exception:  # pragma: no cover
    Picamera2 = None

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover
    YOLO = None


class VisionSystem:
    """
    Handles camera capture and optional YOLOv8 object detection.
    """

    def __init__(
        self,
        yolo_model_path: str = "models/yolo.pt",
        image_dir: str = "storage/images",
    ) -> None:
        self.log = logging.getLogger("vision")
        self.image_dir = image_dir
        os.makedirs(self.image_dir, exist_ok=True)

        self.cam = None
        try:
            if Picamera2 is None:
                raise RuntimeError("Picamera2 not available.")
            self.cam = Picamera2()
            self.cam.configure(self.cam.create_still_configuration())
            self.cam.start()
        except Exception as e:
            self.log.exception("Failed to initialize camera: %s", e)
            self.cam = None

        self.yolo = None
        try:
            if YOLO is None:
                raise RuntimeError("ultralytics YOLO not available.")
            self.yolo = YOLO(yolo_model_path)
        except Exception as e:
            self.log.exception("Failed to load YOLO model: %s", e)
            self.yolo = None

    # -------------------------------------------------
    # Capture helpers
    # -------------------------------------------------
    def _capture_image(self) -> Optional[str]:
        if self.cam is None:
            self.log.error("Camera not available.")
            return None
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.image_dir, f"capture_{ts}.jpg")
            self.cam.capture_file(path)
            self.log.info("Captured image %s", path)
            return path
        except Exception:
            self.log.exception("Failed to capture image.")
            return None

    # Feature 2 – image capture only
    def capture_and_save_image(self) -> Optional[str]:
        return self._capture_image()

    # -------------------------------------------------
    # Feature 1 – object detection
    # -------------------------------------------------
    def detect_first_object(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns (image_path, first_label)
        """
        image_path = self._capture_image()
        if image_path is None:
            return None, None

        if self.yolo is None:
            self.log.error("YOLO model not available.")
            return image_path, None

        try:
            self.log.info("Running YOLO detection (may take 30s+ on first run)...")
            results = self.yolo(image_path, verbose=False)
            if not results:
                self.log.info("YOLO returned no results.")
                return image_path, None

            r = results[0]
            if r.boxes is None or len(r.boxes) == 0:
                self.log.info("No objects detected in image.")
                return image_path, None

            box = r.boxes[0]
            cls_idx = int(box.cls[0].item())
            label = r.names.get(cls_idx, str(cls_idx))
            self.log.info("Detected object: %s", label)
            return image_path, label
        except Exception:
            self.log.exception("YOLO detection failed.")
            return image_path, None

