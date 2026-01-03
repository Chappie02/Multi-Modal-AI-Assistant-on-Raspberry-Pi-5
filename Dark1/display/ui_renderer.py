"""
UI Renderer for LCD Display
Handles token-by-token text streaming, UI states, and animations.

This module provides high-level rendering functions for:
- Token-by-token text streaming (for LLM responses)
- UI state management (idle, listening, thinking, speaking)
- Simple animations (robot eyes, status indicators)
- Text wrapping and scrolling
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional, Tuple
import time
from display.lcd_driver import ST7789Driver

# Display dimensions
LCD_WIDTH = 240
LCD_HEIGHT = 284

# Color definitions (RGB565 format)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F
COLOR_YELLOW = 0xFFE0
COLOR_CYAN = 0x07FF
COLOR_MAGENTA = 0xF81F

# UI State constants
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_THINKING = "thinking"
STATE_SPEAKING = "speaking"
STATE_DETECTING = "detecting"


class UIRenderer:
    """
    High-level UI renderer for the LCD display.
    
    Features:
    - Token-by-token text streaming
    - State-based UI rendering
    - Text wrapping and scrolling
    - Simple animations
    """
    
    def __init__(self, lcd_driver: ST7789Driver):
        """
        Initialize UI renderer.
        
        Args:
            lcd_driver: Initialized ST7789Driver instance
        """
        self.lcd = lcd_driver
        self.current_state = STATE_IDLE
        self.text_buffer = []  # List of words/tokens
        self.font_size = 16
        self.line_spacing = 4
        self.margin = 8
        
        # Try to load a font, fallback to default if not available
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.font_size)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", self.font_size)
            except:
                self.font = ImageFont.load_default()
        
        # Animation state
        self.animation_frame = 0
        self.last_animation_time = time.time()
        
    def clear(self):
        """Clear display and reset text buffer."""
        self.lcd.clear(COLOR_BLACK)
        self.text_buffer = []
        
    def set_state(self, state: str):
        """
        Set UI state and render appropriate display.
        
        Args:
            state: One of STATE_IDLE, STATE_LISTENING, STATE_THINKING, etc.
        """
        self.current_state = state
        self._render_state()
        
    def _render_state(self):
        """Render the current UI state."""
        if self.current_state == STATE_IDLE:
            self._render_idle()
        elif self.current_state == STATE_LISTENING:
            self._render_listening()
        elif self.current_state == STATE_THINKING:
            self._render_thinking()
        elif self.current_state == STATE_DETECTING:
            self._render_detecting()
        # STATE_SPEAKING is handled by token streaming
        
    def _render_idle(self):
        """Render idle state with robot eyes animation."""
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        # Calculate eye positions
        eye_size = 30
        eye_spacing = 60
        center_x = LCD_WIDTH // 2
        center_y = LCD_HEIGHT // 2
        
        # Animate eyes (blinking effect)
        current_time = time.time()
        if current_time - self.last_animation_time > 0.1:  # Update every 100ms
            self.animation_frame = (self.animation_frame + 1) % 20
            self.last_animation_time = current_time
        
        # Blink every 2 seconds (20 frames * 0.1s)
        eye_open = 1.0 if (self.animation_frame < 18) else 0.3
        
        # Draw left eye
        left_eye_y = center_y - int(eye_size * eye_open / 2)
        draw.ellipse([
            center_x - eye_spacing - eye_size, center_y - eye_size,
            center_x - eye_spacing, center_y + eye_size
        ], fill='cyan', outline='white', width=2)
        
        # Draw right eye
        draw.ellipse([
            center_x + eye_spacing, center_y - eye_size,
            center_x + eye_spacing + eye_size, center_y + eye_size
        ], fill='cyan', outline='white', width=2)
        
        # Draw status text
        draw.text((center_x, LCD_HEIGHT - 30), "Ready", 
                 font=self.font, fill='white', anchor='mt')
        
        # Convert to RGB565 and display
        self._display_image(img)
        
    def _render_listening(self):
        """Render listening state with pulsing animation."""
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        center_x = LCD_WIDTH // 2
        center_y = LCD_HEIGHT // 2
        
        # Pulsing circle animation
        current_time = time.time()
        pulse = int(10 * abs(np.sin(current_time * 3)))  # Pulse 3 times per second
        
        # Draw microphone icon (simplified)
        mic_size = 40 + pulse
        draw.ellipse([
            center_x - mic_size // 2, center_y - mic_size // 2,
            center_x + mic_size // 2, center_y + mic_size // 2
        ], fill='green', outline='white', width=2)
        
        # Draw text
        draw.text((center_x, center_y + 50), "Listening...", 
                 font=self.font, fill='white', anchor='mt')
        
        self._display_image(img)
        
    def _render_thinking(self):
        """Render thinking state with spinner animation."""
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        center_x = LCD_WIDTH // 2
        center_y = LCD_HEIGHT // 2
        
        # Spinner animation
        current_time = time.time()
        angle = int((current_time * 100) % 360)
        
        # Draw spinner (rotating dots)
        for i in range(8):
            dot_angle = (angle + i * 45) % 360
            rad = np.radians(dot_angle)
            x = center_x + int(30 * np.cos(rad))
            y = center_y + int(30 * np.sin(rad))
            draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill='yellow')
        
        # Draw text
        draw.text((center_x, center_y + 50), "Thinking...", 
                 font=self.font, fill='white', anchor='mt')
        
        self._display_image(img)
        
    def _render_detecting(self):
        """Render object detection state."""
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        center_x = LCD_WIDTH // 2
        center_y = LCD_HEIGHT // 2
        
        # Draw camera icon (simplified)
        draw.rectangle([
            center_x - 30, center_y - 20,
            center_x + 30, center_y + 20
        ], fill='blue', outline='white', width=2)
        
        # Draw text
        draw.text((center_x, center_y + 40), "Detecting...", 
                 font=self.font, fill='white', anchor='mt')
        
        self._display_image(img)
        
    def append_token(self, token: str):
        """
        Append a token to the text buffer and update display.
        This is called for each token as the LLM generates it.
        
        Args:
            token: Token string to append (can be a word or partial word)
        """
        # Add token to buffer
        if token.strip():
            self.text_buffer.append(token)
            
        # Render current text
        self._render_text()
        
    def set_text(self, text: str):
        """
        Set full text at once (for non-streaming updates).
        
        Args:
            text: Complete text string
        """
        # Split into words
        self.text_buffer = text.split()
        self._render_text()
        
    def _render_text(self):
        """
        Render text buffer to display with word wrapping.
        """
        if not self.text_buffer:
            return
            
        # Create image
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        # Combine tokens into text
        full_text = ' '.join(self.text_buffer)
        
        # Word wrap text
        lines = self._wrap_text(full_text, LCD_WIDTH - 2 * self.margin)
        
        # Draw lines
        y = self.margin
        max_lines = (LCD_HEIGHT - 2 * self.margin) // (self.font_size + self.line_spacing)
        
        # Show only the last N lines if text overflows
        start_line = max(0, len(lines) - max_lines)
        
        for line in lines[start_line:]:
            draw.text((self.margin, y), line, font=self.font, fill='white')
            y += self.font_size + self.line_spacing
            if y >= LCD_HEIGHT - self.margin:
                break
        
        self._display_image(img)
        
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width pixels.
        
        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            
        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        for word in words:
            # Measure word width
            bbox = self.font.getbbox(word)
            word_width = bbox[2] - bbox[0]
            space_width = self.font.getbbox(' ')[2] - self.font.getbbox(' ')[0]
            
            # Check if word fits on current line
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                # Start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width + space_width
        
        # Add last line
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines if lines else ['']
    
    def _display_image(self, img: Image.Image):
        """
        Convert PIL Image to RGB565 and display on LCD.
        
        Args:
            img: PIL Image (RGB mode)
        """
        # Resize if needed (should already be correct size)
        if img.size != (LCD_WIDTH, LCD_HEIGHT):
            img = img.resize((LCD_WIDTH, LCD_HEIGHT), Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(img, dtype=np.uint8)
        
        # Display using LCD driver
        self.lcd.write_pixels(img_array)
        
    def show_object_detection(self, objects: List[Tuple[str, float]]):
        """
        Display object detection results.
        
        Args:
            objects: List of (label, confidence) tuples
        """
        img = Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT), color='black')
        draw = ImageDraw.Draw(img)
        
        # Title
        draw.text((LCD_WIDTH // 2, 10), "Detected Objects", 
                 font=self.font, fill='cyan', anchor='mt')
        
        # List objects
        y = 40
        for i, (label, conf) in enumerate(objects[:8]):  # Max 8 objects
            text = f"{label} ({conf:.0%})"
            draw.text((self.margin, y), text, font=self.font, fill='white')
            y += self.font_size + self.line_spacing
            
        self._display_image(img)
        
    def cleanup(self):
        """Clean up resources."""
        self.clear()

