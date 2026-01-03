"""
Wake Word Detection Module
Handles wake word activation for hands-free operation.

This module provides:
- Wake word detection using Porcupine (offline, low latency)
- Alternative simple keyword matching
- Continuous listening with minimal CPU usage
"""

import pvporcupine
import pyaudio
import struct
from typing import Callable, Optional
import threading
import time


class WakeWordDetector:
    """
    Wake word detector using Porcupine.
    
    Porcupine is an offline wake word engine that supports
    custom wake words. For this project, we'll use a built-in
    wake word or create a custom "Hey Pi" model.
    """
    
    def __init__(self, 
                 wake_word_path: Optional[str] = None,
                 sensitivity: float = 0.5,
                 access_key: Optional[str] = None):
        """
        Initialize wake word detector.
        
        Args:
            wake_word_path: Path to custom wake word .ppn file
                          If None, uses built-in wake word
            sensitivity: Detection sensitivity (0.0-1.0)
            access_key: Porcupine access key (required for custom wake words)
        """
        self.wake_word_path = wake_word_path
        self.sensitivity = sensitivity
        self.access_key = access_key
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        self.is_listening = False
        self.callback: Optional[Callable] = None
        self._listening_thread = None
        
    def initialize(self) -> bool:
        """
        Initialize Porcupine and audio stream.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize Porcupine
            if self.wake_word_path:
                # Custom wake word
                if not self.access_key:
                    print("Warning: Access key required for custom wake word")
                    return False
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.wake_word_path],
                    sensitivities=[self.sensitivity]
                )
            else:
                # Use built-in wake word (e.g., "Hey Google", "Alexa")
                # For "Hey Pi", we'd need a custom model
                # Fallback: use a simple keyword matching approach
                print("Using simple keyword matching (Porcupine not configured)")
                return self._init_simple_detector()
            
            # Initialize PyAudio
            self.pa = pyaudio.PyAudio()
            
            # Open audio stream
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            return True
            
        except Exception as e:
            print(f"Wake word detector initialization failed: {e}")
            print("Falling back to simple keyword matching")
            return self._init_simple_detector()
    
    def _init_simple_detector(self) -> bool:
        """
        Initialize simple keyword-based detector.
        This is a fallback when Porcupine is not available.
        """
        # Simple detector doesn't need special initialization
        # It will work with STT output
        return True
    
    def set_callback(self, callback: Callable):
        """
        Set callback function to call when wake word is detected.
        
        Args:
            callback: Function to call (no arguments)
        """
        self.callback = callback
    
    def start_listening(self):
        """Start continuous wake word detection."""
        if self.is_listening:
            return
        
        if not self.porcupine:
            # Use simple detector mode
            print("Simple wake word detector: will check STT output")
            self.is_listening = True
            return
        
        self.is_listening = True
        self._listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listening_thread.start()
    
    def _listen_loop(self):
        """Main listening loop (runs in separate thread)."""
        try:
            while self.is_listening:
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    # Wake word detected!
                    if self.callback:
                        self.callback()
                        
        except Exception as e:
            print(f"Wake word listening error: {e}")
    
    def check_text_for_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word (for simple detector mode).
        
        Args:
            text: Text to check
            
        Returns:
            True if wake word detected
        """
        text_lower = text.lower()
        wake_words = ["hey pi", "hey pie", "wake up", "assistant"]
        
        for wake_word in wake_words:
            if wake_word in text_lower:
                return True
        
        return False
    
    def stop_listening(self):
        """Stop wake word detection."""
        self.is_listening = False
        
        if self._listening_thread:
            self._listening_thread.join(timeout=1.0)
            self._listening_thread = None
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        
        if self.audio_stream:
            self.audio_stream.close()
            self.audio_stream = None
        
        if self.pa:
            self.pa.terminate()
            self.pa = None
        
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

