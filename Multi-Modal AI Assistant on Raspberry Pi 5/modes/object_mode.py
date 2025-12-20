"""
Object Detection Mode Implementation
Handles camera-based object detection using YOLOv8 and scene summarization using LLM.
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple
from ultralytics import YOLO
from llama_cpp import Llama

from utils.camera_utils import CameraManager


class ObjectMode:
    """Handles object detection mode functionality."""
    
    def __init__(self):
        """Initialize object detection mode with YOLOv8 and LLM."""
        self.yolo_model: Optional[YOLO] = None
        self.llm: Optional[Llama] = None
        self.camera_manager: Optional[CameraManager] = None
        
        self._initialize_models()
        self._initialize_camera()
    
    def _initialize_models(self):
        """Initialize YOLOv8 and LLM models."""
        try:
            # Initialize YOLOv8 model
            print("Loading YOLOv8 model...")
            self.yolo_model = YOLO('yolov8n.pt')  # nano version for Pi 5
            print("✅ YOLOv8 model loaded successfully!")
            
            # Initialize LLM for scene summarization
            print("Loading LLM for scene summarization...")
            model_paths = [
                "./models/llama-7b-q4_0.gguf",
                "./models/llama-7b.gguf",
                "/home/pi/models/llama-7b-q4_0.gguf",
                "/home/pi/models/llama-7b.gguf",
                "llama-7b-q4_0.gguf"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                raise FileNotFoundError(
                    "LLM model file not found for scene summarization."
                )
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=1024,  # Smaller context for summarization
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            
            print("✅ LLM for scene summarization loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing models: {e}")
            raise
    
    def _initialize_camera(self):
        """Initialize camera manager."""
        try:
            self.camera_manager = CameraManager()
            print("✅ Camera initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            raise
    
    def capture_and_detect(self) -> Tuple[np.ndarray, List[str]]:
        """Capture an image and detect objects."""
        if not self.camera_manager or not self.yolo_model:
            raise RuntimeError("Camera or YOLO model not initialized")
        
        # Capture image
        print("Capturing image...")
        image = self.camera_manager.capture_image()
        
        if image is None:
            raise RuntimeError("Failed to capture image")
        
        # Run object detection
        print("Running object detection...")
        results = self.yolo_model(image)
        
        # Extract detected objects
        detected_objects = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.yolo_model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Only include objects with confidence > 0.5
                    if confidence > 0.5:
                        detected_objects.append(class_name)
        
        return image, detected_objects
    
    def generate_scene_summary(self, detected_objects: List[str]) -> str:
        """Generate a natural language summary of the detected scene."""
        if not self.llm:
            return "❌ LLM not available for scene summarization."
        
        if not detected_objects:
            return "No objects detected in the scene."
        
        # Create prompt for scene summarization
        objects_text = ", ".join(detected_objects)
        prompt = f"""Based on the detected objects: {objects_text}

Provide a brief, natural description of what this scene likely represents. Keep it concise and conversational, as if describing what you see to someone.

Scene description:"""
        
        try:
            response = self.llm(
                prompt,
                max_tokens=128,
                temperature=0.7,
                top_p=0.9,
                stop=["\n\n", "Human:", "System:"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                summary = response['choices'][0]['text'].strip()
                return summary
            else:
                return f"I can see {objects_text} in this scene."
                
        except Exception as e:
            return f"I can see {objects_text} in this scene."
    
    def analyze_scene(self):
        """Analyze the current scene and provide a summary."""
        try:
            # Capture image and detect objects
            image, detected_objects = self.capture_and_detect()
            
            # Print detected objects
            if detected_objects:
                print(f"Detected objects: {', '.join(detected_objects)}")
            else:
                print("No objects detected in the scene.")
            
            # Generate and print scene summary
            summary = self.generate_scene_summary(detected_objects)
            print(f"Summary: {summary}")
            
        except Exception as e:
            print(f"❌ Error analyzing scene: {e}")
    
    def run(self):
        """Run the object detection mode loop."""
        if not self.yolo_model or not self.camera_manager:
            print("❌ Object detection mode not available. Models not initialized.")
            return
        
        print("Object detection mode is ready!")
        print("Commands:")
        print("  'what is this' - Analyze the current scene")
        print("  'exit' - Return to main menu")
        
        while True:
            try:
                user_input = input("\nObject Mode> ").strip().lower()
                
                if user_input == "exit":
                    print("Exiting object detection mode...")
                    break
                elif user_input == "what is this":
                    self.analyze_scene()
                else:
                    print("❌ Unknown command. Type 'what is this' or 'exit'.")
                
            except KeyboardInterrupt:
                print("\n\nExiting object detection mode...")
                break
            except Exception as e:
                print(f"❌ Error in object detection mode: {e}")
                print("Please try again or type 'exit' to return to main menu.")
        
        # Clean up camera resources
        if self.camera_manager:
            self.camera_manager.cleanup()
        
        print("Object detection mode ended.")
