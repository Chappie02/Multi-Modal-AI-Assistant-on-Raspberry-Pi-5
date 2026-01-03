"""
Mode Manager Module
Handles switching between Chat Mode and Object Detection Mode.

This module provides:
- Mode state management
- Voice-based mode switching
- Hardware switch support (optional)
- Mode-specific behavior routing
"""

from enum import Enum
from typing import Callable, Optional, List
import RPi.GPIO as GPIO


class SystemMode(Enum):
    """System operation modes."""
    CHAT = "chat"
    OBJECT_DETECTION = "object_detection"
    IDLE = "idle"


class ModeManager:
    """
    Manages system mode switching and state.
    
    Supports:
    - Voice-based mode switching
    - Hardware button switching (optional)
    - Mode change callbacks
    """
    
    def __init__(self, initial_mode: SystemMode = SystemMode.CHAT):
        """
        Initialize mode manager.
        
        Args:
            initial_mode: Starting mode
        """
        self.current_mode = initial_mode
        self.mode_change_callbacks: List[Callable[[SystemMode], None]] = []
        
        # Hardware switch (optional)
        self.hw_switch_pin = None
        self.hw_switch_enabled = False
        
    def set_mode(self, mode: SystemMode, notify: bool = True):
        """
        Change system mode.
        
        Args:
            mode: New mode to set
            notify: If True, call mode change callbacks
        """
        if mode == self.current_mode:
            return
        
        old_mode = self.current_mode
        self.current_mode = mode
        
        if notify:
            for callback in self.mode_change_callbacks:
                try:
                    callback(mode)
                except Exception as e:
                    print(f"Mode change callback error: {e}")
    
    def get_mode(self) -> SystemMode:
        """Get current mode."""
        return self.current_mode
    
    def is_chat_mode(self) -> bool:
        """Check if in chat mode."""
        return self.current_mode == SystemMode.CHAT
    
    def is_object_detection_mode(self) -> bool:
        """Check if in object detection mode."""
        return self.current_mode == SystemMode.OBJECT_DETECTION
    
    def handle_voice_command(self, text: str) -> bool:
        """
        Process voice command for mode switching.
        
        Args:
            text: Voice command text
        
        Returns:
            True if mode was changed, False otherwise
        """
        text_lower = text.lower()
        
        # Chat mode commands
        if any(phrase in text_lower for phrase in [
            "switch to chat mode",
            "chat mode",
            "enable chat",
            "talk mode"
        ]):
            self.set_mode(SystemMode.CHAT)
            return True
        
        # Object detection mode commands
        if any(phrase in text_lower for phrase in [
            "switch to object detection mode",
            "object detection mode",
            "detection mode",
            "vision mode",
            "camera mode"
        ]):
            self.set_mode(SystemMode.OBJECT_DETECTION)
            return True
        
        # Object detection trigger phrase
        if any(phrase in text_lower for phrase in [
            "what is this",
            "what are these",
            "detect objects",
            "identify objects"
        ]):
            # If in chat mode, switch to object detection temporarily
            if self.current_mode == SystemMode.CHAT:
                self.set_mode(SystemMode.OBJECT_DETECTION)
                return True
        
        return False
    
    def register_mode_change_callback(self, callback: Callable[[SystemMode], None]):
        """
        Register callback for mode changes.
        
        Args:
            callback: Function to call when mode changes
        """
        self.mode_change_callbacks.append(callback)
    
    def setup_hardware_switch(self, pin: int, pull_up: bool = True):
        """
        Setup hardware button for mode switching (optional).
        
        Args:
            pin: GPIO pin number for button
            pull_up: If True, use pull-up resistor
        """
        self.hw_switch_pin = pin
        GPIO.setmode(GPIO.BCM)
        
        if pull_up:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        # Add interrupt handler
        GPIO.add_event_detect(
            pin,
            GPIO.FALLING if pull_up else GPIO.RISING,
            callback=self._hw_switch_callback,
            bouncetime=300
        )
        
        self.hw_switch_enabled = True
    
    def _hw_switch_callback(self, channel):
        """Hardware switch interrupt handler."""
        # Toggle between chat and object detection
        if self.current_mode == SystemMode.CHAT:
            self.set_mode(SystemMode.OBJECT_DETECTION)
        else:
            self.set_mode(SystemMode.CHAT)
    
    def cleanup(self):
        """Clean up hardware resources."""
        if self.hw_switch_enabled and self.hw_switch_pin:
            GPIO.remove_event_detect(self.hw_switch_pin)
            self.hw_switch_enabled = False

