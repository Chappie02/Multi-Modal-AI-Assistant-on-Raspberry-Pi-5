#!/usr/bin/env python3
"""
Raspberry Pi 5 Multimodal LLM Assistant - Main Orchestrator

This is the main entry point that coordinates all system components:
- Audio input/output (wake word, STT, TTS)
- LLM inference with token streaming
- Object detection (YOLO)
- RAG memory
- LCD display
- Mode management

Run with: sudo python3 main.py
(Requires sudo for GPIO/SPI access)
"""

import sys
import time
import signal
import threading
from typing import Optional

# Import all modules
from display.lcd_driver import ST7789Driver
from display.ui_renderer import UIRenderer, STATE_IDLE, STATE_LISTENING, STATE_THINKING, STATE_SPEAKING, STATE_DETECTING
from vision.camera import Camera
from vision.detector import ObjectDetector
from audio.wake_word import WakeWordDetector
from audio.stt import SpeechToText
from audio.tts import TextToSpeech
from core.llm_engine import LLMEngine
from core.rag_memory import RAGMemory
from core.mode_manager import ModeManager, SystemMode


class MultimodalAssistant:
    """
    Main orchestrator for the multimodal LLM assistant.
    
    Coordinates all subsystems and handles the main event loop.
    """
    
    def __init__(self):
        """Initialize all system components."""
        print("Initializing Raspberry Pi 5 Multimodal LLM Assistant...")
        
        # Display system
        print("  - Initializing LCD display...")
        self.lcd_driver = ST7789Driver()
        self.lcd_driver.initialize()
        self.ui = UIRenderer(self.lcd_driver)
        self.ui.clear()
        self.ui.set_state(STATE_IDLE)
        
        # Vision system
        print("  - Initializing camera...")
        self.camera = Camera(width=640, height=480)
        self.camera.initialize()
        
        print("  - Initializing object detector...")
        self.detector = ObjectDetector(model_path="yolov8n.pt")
        self.detector.initialize()
        
        # Audio system
        print("  - Initializing wake word detector...")
        self.wake_word = WakeWordDetector()
        self.wake_word.initialize()
        self.wake_word.set_callback(self._on_wake_word_detected)
        
        print("  - Initializing speech-to-text...")
        self.stt = SpeechToText()
        self.stt.initialize()
        
        print("  - Initializing text-to-speech...")
        self.tts = TextToSpeech()
        self.tts.initialize()
        
        # Core AI system
        print("  - Initializing LLM engine...")
        self.llm = LLMEngine(
            model_path="models/gemma-2-2b-it-q4_k_m.gguf",
            n_threads=4,
            temperature=0.7
        )
        self.llm.initialize()
        
        print("  - Initializing RAG memory...")
        self.rag = RAGMemory()
        
        # Mode management
        print("  - Initializing mode manager...")
        self.mode_manager = ModeManager(initial_mode=SystemMode.CHAT)
        self.mode_manager.register_mode_change_callback(self._on_mode_changed)
        
        # State management
        self.is_running = True
        self.processing_lock = threading.Lock()
        
        print("\nInitialization complete! System ready.")
        print("Say 'Hey Pi' to activate, or 'what is this?' for object detection.\n")
        
    def _on_wake_word_detected(self):
        """Callback when wake word is detected."""
        if not self.processing_lock.acquire(blocking=False):
            return  # Already processing
        
        try:
            self._handle_wake_word()
        finally:
            self.processing_lock.release()
    
    def _handle_wake_word(self):
        """Handle wake word activation."""
        # Update UI
        self.ui.set_state(STATE_LISTENING)
        
        # Record and transcribe
        user_input = self.stt.listen_and_transcribe(duration=5.0)
        
        if not user_input or not user_input.strip():
            self.ui.set_state(STATE_IDLE)
            return
        
        # Check for mode switching commands
        if self.mode_manager.handle_voice_command(user_input):
            self.ui.set_text("Mode changed")
            time.sleep(1)
            self.ui.set_state(STATE_IDLE)
            return
        
        # Process based on current mode
        if self.mode_manager.is_chat_mode():
            self._handle_chat_mode(user_input)
        elif self.mode_manager.is_object_detection_mode():
            # Check if trigger phrase
            if any(phrase in user_input.lower() for phrase in [
                "what is this", "what are these", "detect", "identify"
            ]):
                self._handle_object_detection()
            else:
                # Switch to chat mode for regular questions
                self._handle_chat_mode(user_input)
    
    def _handle_chat_mode(self, user_input: str):
        """Handle chat mode interaction."""
        # Update UI
        self.ui.set_state(STATE_THINKING)
        
        # Retrieve relevant context from RAG
        context = self.rag.retrieve_context(user_input, top_k=3, mode="chat")
        
        # Format prompt with context
        prompt = self.llm.format_with_context(user_input, context)
        
        # Generate response with token streaming
        self.ui.set_state(STATE_SPEAKING)
        self.ui.clear()
        
        response_tokens = []
        full_response = ""
        
        def token_callback(token: str):
            """Callback for each generated token."""
            response_tokens.append(token)
            full_response += token
            # Update display token-by-token
            self.ui.append_token(token)
        
        # Generate response
        for token in self.llm.generate(prompt, max_tokens=256, token_callback=token_callback):
            pass  # Tokens handled by callback
        
        # Store in RAG memory
        self.rag.store_conversation(user_input, full_response, mode="chat")
        
        # Speak response
        self.tts.speak(full_response, blocking=True)
        
        # Return to idle
        time.sleep(1)
        self.ui.set_state(STATE_IDLE)
    
    def _handle_object_detection(self):
        """Handle object detection mode."""
        # Update UI
        self.ui.set_state(STATE_DETECTING)
        
        # Capture frame
        frame = self.camera.capture_frame()
        if frame is None:
            self.ui.set_text("Camera error")
            time.sleep(2)
            self.ui.set_state(STATE_IDLE)
            return
        
        # Run object detection
        detections = self.detector.detect(frame)
        
        if not detections:
            self.ui.set_text("No objects detected")
            self.tts.speak("No objects detected")
            time.sleep(2)
            self.ui.set_state(STATE_IDLE)
            return
        
        # Show detections on display
        detection_list = [(label, conf) for label, conf, _ in detections]
        self.ui.show_object_detection(detection_list)
        
        # Format for LLM
        detection_text = self.detector.format_for_llm(detections)
        
        # Generate natural explanation
        prompt = f"Explain these detected objects in a natural, conversational way: {detection_text}"
        
        self.ui.set_state(STATE_THINKING)
        time.sleep(0.5)
        
        # Generate explanation with streaming
        self.ui.set_state(STATE_SPEAKING)
        self.ui.clear()
        
        explanation_tokens = []
        full_explanation = ""
        
        def token_callback(token: str):
            explanation_tokens.append(token)
            full_explanation += token
            self.ui.append_token(token)
        
        for token in self.llm.generate(prompt, max_tokens=128, token_callback=token_callback):
            pass
        
        # Store in RAG
        labels = [label for label, _, _ in detections]
        self.rag.store_object_detection(labels, full_explanation)
        
        # Speak explanation
        self.tts.speak(full_explanation, blocking=True)
        
        # Return to idle
        time.sleep(1)
        self.ui.set_state(STATE_IDLE)
    
    def _on_mode_changed(self, new_mode: SystemMode):
        """Callback when mode changes."""
        mode_text = {
            SystemMode.CHAT: "Chat Mode",
            SystemMode.OBJECT_DETECTION: "Detection Mode",
            SystemMode.IDLE: "Idle"
        }
        self.ui.set_text(f"Mode: {mode_text.get(new_mode, 'Unknown')}")
        time.sleep(1)
        self.ui.set_state(STATE_IDLE)
    
    def run(self):
        """Main event loop."""
        # Start wake word detection
        self.wake_word.start_listening()
        
        # Also check STT output for wake words (fallback)
        print("System running. Waiting for wake word...")
        
        try:
            while self.is_running:
                # Main loop - wake word detection handles activation
                # For simple wake word detector, we can also listen continuously
                time.sleep(0.1)
                
                # Update idle animation
                if self.ui.current_state == STATE_IDLE:
                    self.ui._render_idle()
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nShutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components."""
        print("Cleaning up resources...")
        self.is_running = False
        
        # Stop wake word detection
        self.wake_word.stop_listening()
        
        # Cleanup all components
        self.ui.cleanup()
        self.lcd_driver.cleanup()
        self.camera.cleanup()
        self.detector.cleanup()
        self.stt.cleanup()
        self.tts.cleanup()
        self.llm.cleanup()
        self.rag.cleanup()
        self.mode_manager.cleanup()
        
        print("Shutdown complete.")


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C)."""
    print("\nReceived interrupt signal")
    if 'assistant' in globals():
        assistant.shutdown()
    sys.exit(0)


def main():
    """Main entry point."""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if running as root (required for GPIO/SPI)
    import os
    if os.geteuid() != 0:
        print("ERROR: This script must be run with sudo for GPIO/SPI access")
        print("Usage: sudo python3 main.py")
        sys.exit(1)
    
    # Create and run assistant
    global assistant
    assistant = MultimodalAssistant()
    assistant.run()


if __name__ == "__main__":
    main()

