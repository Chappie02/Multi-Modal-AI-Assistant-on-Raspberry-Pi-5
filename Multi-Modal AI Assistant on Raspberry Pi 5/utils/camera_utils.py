"""
Camera Utilities
Handles camera operations for the Raspberry Pi camera module.
"""

import cv2
import numpy as np
from typing import Optional
import time


class CameraManager:
    """Manages camera operations for object detection."""
    
    def __init__(self, camera_index: int = 0, resolution: tuple = (640, 480)):
        """
        Initialize camera manager.
        
        Args:
            camera_index: Camera device index (usually 0 for default camera)
            resolution: Camera resolution (width, height)
        """
        self.camera_index = camera_index
        self.resolution = resolution
        self.cap: Optional[cv2.VideoCapture] = None
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera capture."""
        try:
            # Try different camera backends for Raspberry Pi
            backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    if self.cap.isOpened():
                        print(f"✅ Camera initialized with backend: {backend}")
                        break
                except:
                    continue
            
            if not self.cap or not self.cap.isOpened():
                # Fallback to default
                self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise RuntimeError("Could not open camera")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Allow camera to warm up
            time.sleep(1)
            
            print(f"Camera initialized: {self.resolution[0]}x{self.resolution[1]}")
            
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            raise
    
    def capture_image(self) -> Optional[np.ndarray]:
        """
        Capture a single image from the camera.
        
        Returns:
            Captured image as numpy array, or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            print("❌ Camera not initialized")
            return None
        
        try:
            # Capture frame
            ret, frame = self.cap.read()
            
            if not ret:
                print("❌ Failed to capture frame")
                return None
            
            # Convert BGR to RGB (OpenCV uses BGR by default)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            return frame_rgb
            
        except Exception as e:
            print(f"❌ Error capturing image: {e}")
            return None
    
    def test_camera(self) -> bool:
        """
        Test if camera is working properly.
        
        Returns:
            True if camera is working, False otherwise
        """
        try:
            image = self.capture_image()
            return image is not None
        except:
            return False
    
    def cleanup(self):
        """Clean up camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Camera resources cleaned up.")


def test_camera_connection(camera_index: int = 0) -> bool:
    """
    Test camera connection without initializing full camera manager.
    
    Args:
        camera_index: Camera device index to test
        
    Returns:
        True if camera is accessible, False otherwise
    """
    try:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        return False
    except:
        return False


def list_available_cameras() -> list:
    """
    List available camera devices.
    
    Returns:
        List of available camera indices
    """
    available_cameras = []
    
    for i in range(5):  # Check first 5 camera indices
        if test_camera_connection(i):
            available_cameras.append(i)
    
    return available_cameras
