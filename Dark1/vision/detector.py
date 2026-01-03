"""
YOLO Object Detection Module
Handles object detection using YOLOv8 or YOLOv5.

This module provides:
- YOLO model loading and inference
- Post-processing (NMS, confidence filtering)
- Result formatting for LLM consumption
"""

import numpy as np
from typing import List, Tuple, Optional
import torch
from ultralytics import YOLO
import cv2


class ObjectDetector:
    """
    YOLO-based object detector.
    
    Supports YOLOv8 (recommended) and can be adapted for YOLOv5.
    Optimized for Raspberry Pi 5 with quantized models.
    """
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.25):
        """
        Initialize object detector.
        
        Args:
            model_path: Path to YOLO model file (.pt or .onnx)
                       Use "yolov8n.pt" for nano (fastest)
                       Use "yolov5s.pt" for small (more accurate)
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self._initialized = False
        
    def initialize(self):
        """
        Load YOLO model.
        This may take a few seconds on first run.
        """
        try:
            # Load YOLO model
            # YOLOv8 is recommended for better performance
            self.model = YOLO(self.model_path)
            
            # Warm up model with dummy inference
            dummy_input = np.zeros((1, 640, 640, 3), dtype=np.float32)
            self.model.predict(dummy_input, verbose=False)
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"YOLO model loading failed: {e}")
            print("Make sure ultralytics is installed: pip install ultralytics")
            self._initialized = False
            return False
    
    def detect(self, image: np.ndarray) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
        """
        Detect objects in an image.
        
        Args:
            image: Input image as numpy array (RGB format, any size)
                  Will be resized to 640x640 internally
        
        Returns:
            List of (label, confidence, bbox) tuples where:
            - label: Object class name (e.g., "person", "laptop")
            - confidence: Detection confidence (0.0-1.0)
            - bbox: Bounding box (x1, y1, x2, y2) in original image coordinates
        """
        if not self._initialized:
            if not self.initialize():
                return []
        
        try:
            # Run inference
            # YOLO model handles resizing internally
            results = self.model.predict(
                image,
                conf=self.confidence_threshold,
                verbose=False,
                device='cpu'  # Pi 5 uses CPU
            )
            
            detections = []
            
            # Parse results
            if len(results) > 0:
                result = results[0]
                
                # Extract boxes, scores, and class IDs
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    # Get box coordinates (xyxy format)
                    box = boxes.xyxy[i].cpu().numpy()
                    x1, y1, x2, y2 = box.astype(int)
                    
                    # Get confidence
                    confidence = float(boxes.conf[i].cpu().numpy())
                    
                    # Get class name
                    class_id = int(boxes.cls[i].cpu().numpy())
                    class_name = result.names[class_id]
                    
                    detections.append((
                        class_name,
                        confidence,
                        (x1, y1, x2, y2)
                    ))
            
            # Sort by confidence (highest first)
            detections.sort(key=lambda x: x[1], reverse=True)
            
            return detections
            
        except Exception as e:
            print(f"Object detection failed: {e}")
            return []
    
    def format_for_llm(self, detections: List[Tuple[str, float, Tuple[int, int, int, int]]]) -> str:
        """
        Format detection results as natural language for LLM.
        
        Args:
            detections: List of (label, confidence, bbox) tuples
        
        Returns:
            Formatted string describing detected objects
        """
        if not detections:
            return "No objects detected."
        
        # Group by label and count
        object_counts = {}
        for label, conf, bbox in detections:
            if label not in object_counts:
                object_counts[label] = []
            object_counts[label].append(conf)
        
        # Build description
        parts = []
        for label, confidences in object_counts.items():
            count = len(confidences)
            avg_conf = sum(confidences) / len(confidences)
            
            if count == 1:
                parts.append(f"a {label} (confidence: {avg_conf:.0%})")
            else:
                parts.append(f"{count} {label}s (avg confidence: {avg_conf:.0%})")
        
        return "Detected: " + ", ".join(parts) + "."
    
    def is_available(self) -> bool:
        """Check if detector is initialized and ready."""
        return self._initialized
    
    def cleanup(self):
        """Clean up model resources."""
        self.model = None
        self._initialized = False

