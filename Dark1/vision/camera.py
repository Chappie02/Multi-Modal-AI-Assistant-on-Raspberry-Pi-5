"""
Camera Module for Raspberry Pi Camera
Wrapper around Picamera2 for easy image capture.

This module provides a simple interface for:
- Camera initialization and configuration
- Single frame capture
- Image preprocessing for YOLO
"""

from picamera2 import Picamera2
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import time


class Camera:
    """
    Camera interface for Raspberry Pi Camera.
    
    Handles camera initialization, configuration, and frame capture.
    Optimized for object detection use cases.
    """
    
    def __init__(self, width: int = 640, height: int = 480):
        """
        Initialize camera.
        
        Args:
            width: Capture width (default: 640 for YOLO)
            height: Capture height (default: 480 for YOLO)
        """
        self.width = width
        self.height = height
        self.camera = None
        self._initialized = False
        
    def initialize(self):
        """Initialize and configure camera."""
        try:
            self.camera = Picamera2()
            
            # Configure camera for still capture
            # Using main stream for high quality
            config = self.camera.create_still_configuration(
                main={"size": (self.width, self.height)},
                buffer_count=1
            )
            self.camera.configure(config)
            
            # Start camera
            self.camera.start()
            time.sleep(0.1)  # Allow camera to stabilize
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Camera initialization failed: {e}")
            self._initialized = False
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Returns:
            NumPy array of shape (height, width, 3) in RGB format,
            or None if capture fails
        """
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            # Capture frame
            array = self.camera.capture_array()
            
            # Picamera2 returns BGR by default, convert to RGB
            if len(array.shape) == 3:
                # Convert BGR to RGB
                array = array[:, :, ::-1]
            
            return array
            
        except Exception as e:
            print(f"Frame capture failed: {e}")
            return None
    
    def capture_image(self) -> Optional[Image.Image]:
        """
        Capture a single frame as PIL Image.
        
        Returns:
            PIL Image in RGB format, or None if capture fails
        """
        frame = self.capture_frame()
        if frame is None:
            return None
        
        return Image.fromarray(frame)
    
    def capture_for_yolo(self, target_size: Tuple[int, int] = (640, 640)) -> Optional[np.ndarray]:
        """
        Capture and preprocess frame for YOLO inference.
        
        Args:
            target_size: Target size for YOLO (width, height)
            
        Returns:
            Preprocessed array ready for YOLO, or None if capture fails
        """
        frame = self.capture_frame()
        if frame is None:
            return None
        
        # Resize to target size
        img = Image.fromarray(frame)
        img_resized = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize to [0, 1]
        array = np.array(img_resized, dtype=np.float32) / 255.0
        
        # YOLO expects (batch, height, width, channels)
        # Convert to (1, height, width, 3)
        array = np.expand_dims(array, axis=0)
        
        return array
    
    def is_available(self) -> bool:
        """Check if camera is available and initialized."""
        return self._initialized
    
    def cleanup(self):
        """Stop camera and release resources."""
        if self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
            except:
                pass
            self.camera = None
            self._initialized = False

