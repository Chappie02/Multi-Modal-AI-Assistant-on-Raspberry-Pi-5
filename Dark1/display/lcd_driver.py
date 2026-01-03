"""
ST7789P LCD Driver for Waveshare 1.83-inch LCD Module Rev2
Hardware-specific SPI communication implementation.

This driver implements the ST7789P controller protocol without using
vendor libraries. It handles SPI initialization, display configuration,
and pixel data transfer with proper chunking for Raspberry Pi SPI limits.

Hardware Connections:
- VCC → 3.3V
- GND → GND
- DIN (MOSI) → GPIO10 (Pin 19)
- CLK (SCLK) → GPIO11 (Pin 23)
- CS → GPIO8 / CE0 (Pin 24)
- DC → GPIO25 (Pin 22)
- RST → GPIO27 (Pin 13)
- BL → GPIO18 (Pin 12)
"""

import spidev
import RPi.GPIO as GPIO
import time
from typing import Tuple, Optional
import numpy as np

# ST7789P Command Set
ST7789_NOP = 0x00
ST7789_SWRESET = 0x01
ST7789_RDDID = 0x04
ST7789_RDDST = 0x09
ST7789_SLPIN = 0x10
ST7789_SLPOUT = 0x11
ST7789_PTLON = 0x12
ST7789_NORON = 0x13
ST7789_INVOFF = 0x20
ST7789_INVON = 0x21
ST7789_DISPOFF = 0x28
ST7789_DISPON = 0x29
ST7789_CASET = 0x2A
ST7789_RASET = 0x2B
ST7789_RAMWR = 0x2C
ST7789_RAMRD = 0x2E
ST7789_PTLAR = 0x30
ST7789_COLMOD = 0x3A
ST7789_MADCTL = 0x36
ST7789_PORCTRL = 0xB2
ST7789_GCTRL = 0xB7
ST7789_VCOMS = 0xBB
ST7789_LCMCTRL = 0xC0
ST7789_VDVVRHEN = 0xC2
ST7789_VRHS = 0xC3
ST7789_VDVS = 0xC4
ST7789_FRCTRL2 = 0xC6
ST7789_PWCTRL1 = 0xD0
ST7789_PVGAMCTRL = 0xE0
ST7789_NVGAMCTRL = 0xE1

# GPIO Pin Definitions
PIN_DC = 25      # Data/Command pin
PIN_RST = 27     # Reset pin
PIN_BL = 18      # Backlight pin
SPI_CS = 0       # CE0 (GPIO8)
SPI_BUS = 0      # SPI0

# Display Dimensions
LCD_WIDTH = 240
LCD_HEIGHT = 284
LCD_SIZE = (LCD_WIDTH, LCD_HEIGHT)

# SPI Configuration
SPI_MAX_SPEED = 40000000  # 40 MHz (can be reduced if unstable)
SPI_MODE = 0b00
SPI_CHUNK_SIZE = 4096     # Maximum bytes per SPI transfer


class ST7789Driver:
    """
    Low-level driver for ST7789P TFT LCD controller.
    
    This class handles:
    - SPI communication initialization
    - Display hardware reset and configuration
    - Command/data separation via DC pin
    - RGB565 pixel data transfer with chunking
    - Backlight control
    """
    
    def __init__(self):
        """Initialize GPIO pins and SPI interface."""
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        self.spi = None
        self._gpio_initialized = False
        
    def initialize(self):
        """
        Initialize GPIO pins and SPI bus.
        Must be called before any display operations.
        """
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configure control pins
        GPIO.setup(PIN_DC, GPIO.OUT)
        GPIO.setup(PIN_RST, GPIO.OUT)
        GPIO.setup(PIN_BL, GPIO.OUT)
        
        # Initialize pins to default states
        GPIO.output(PIN_DC, GPIO.LOW)
        GPIO.output(PIN_RST, GPIO.HIGH)
        GPIO.output(PIN_BL, GPIO.LOW)  # Backlight off initially
        
        self._gpio_initialized = True
        
        # Initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_CS)
        self.spi.max_speed_hz = SPI_MAX_SPEED
        self.spi.mode = SPI_MODE
        self.spi.bits_per_word = 8
        
        # Perform hardware reset and initialization sequence
        self._hardware_reset()
        self._init_display()
        
        # Enable backlight
        self.set_backlight(True)
        
    def _hardware_reset(self):
        """Perform hardware reset sequence."""
        GPIO.output(PIN_RST, GPIO.LOW)
        time.sleep(0.01)  # 10ms
        GPIO.output(PIN_RST, GPIO.HIGH)
        time.sleep(0.12)  # 120ms wait after reset
        
    def _write_command(self, cmd: int):
        """
        Send a command byte to the display.
        
        Args:
            cmd: Command byte (0x00-0xFF)
        """
        GPIO.output(PIN_DC, GPIO.LOW)  # Command mode
        self.spi.xfer2([cmd])
        
    def _write_data(self, data: bytes):
        """
        Send data bytes to the display.
        
        Args:
            data: Bytes to send (can be list or bytes object)
        """
        GPIO.output(PIN_DC, GPIO.HIGH)  # Data mode
        
        # Convert to list if needed
        if isinstance(data, bytes):
            data = list(data)
        elif isinstance(data, int):
            data = [data]
            
        # Send data in chunks to respect SPI buffer limits
        for i in range(0, len(data), SPI_CHUNK_SIZE):
            chunk = data[i:i + SPI_CHUNK_SIZE]
            self.spi.xfer2(chunk)
    
    def _init_display(self):
        """Initialize display with ST7789P configuration sequence."""
        # Software reset
        self._write_command(ST7789_SWRESET)
        time.sleep(0.15)
        
        # Sleep out
        self._write_command(ST7789_SLPOUT)
        time.sleep(0.12)
        
        # Memory access control (MADCTL)
        # MY=0, MX=0, MV=0, ML=0, BGR=1, MH=0
        self._write_command(ST7789_MADCTL)
        self._write_data(0x00)
        
        # Interface pixel format: 16-bit RGB565
        self._write_command(ST7789_COLMOD)
        self._write_data(0x55)  # 16-bit/pixel
        
        # Porch control
        self._write_command(ST7789_PORCTRL)
        self._write_data([0x0C, 0x0C, 0x00, 0x33, 0x33])
        
        # Gate control
        self._write_command(ST7789_GCTRL)
        self._write_data(0x35)
        
        # VCOM setting
        self._write_command(ST7789_VCOMS)
        self._write_data(0x19)
        
        # LCM control
        self._write_command(ST7789_LCMCTRL)
        self._write_data(0x2C)
        
        # VDV and VRH command enable
        self._write_command(ST7789_VDVVRHEN)
        self._write_data(0x01)
        
        # VRH set
        self._write_command(ST7789_VRHS)
        self._write_data(0x12)
        
        # VDV set
        self._write_command(ST7789_VDVS)
        self._write_data(0x20)
        
        # Frame rate control
        self._write_command(ST7789_FRCTRL2)
        self._write_data(0x0F)
        
        # Power control 1
        self._write_command(ST7789_PWCTRL1)
        self._write_data([0xA4, 0xA1])
        
        # Positive voltage gamma control
        self._write_command(ST7789_PVGAMCTRL)
        self._write_data([
            0xD0, 0x04, 0x0D, 0x11, 0x13, 0x2B, 0x3F, 0x54,
            0x4C, 0x18, 0x0D, 0x0B, 0x1F, 0x23
        ])
        
        # Negative voltage gamma control
        self._write_command(ST7789_NVGAMCTRL)
        self._write_data([
            0xD0, 0x04, 0x0C, 0x11, 0x13, 0x2C, 0x3F, 0x44,
            0x51, 0x2F, 0x1F, 0x1F, 0x20, 0x23
        ])
        
        # Display inversion off
        self._write_command(ST7789_INVOFF)
        
        # Normal display mode on
        self._write_command(ST7789_NORON)
        time.sleep(0.01)
        
        # Display on
        self._write_command(ST7789_DISPON)
        time.sleep(0.02)
        
    def set_backlight(self, state: bool):
        """
        Control backlight.
        
        Args:
            state: True to enable, False to disable
        """
        if self._gpio_initialized:
            GPIO.output(PIN_BL, GPIO.HIGH if state else GPIO.LOW)
    
    def set_window(self, x0: int, y0: int, x1: int, y1: int):
        """
        Set the active display window for pixel writes.
        
        Args:
            x0, y0: Top-left corner (inclusive)
            x1, y1: Bottom-right corner (inclusive)
        """
        # Column address set
        self._write_command(ST7789_CASET)
        self._write_data([
            (x0 >> 8) & 0xFF, x0 & 0xFF,
            (x1 >> 8) & 0xFF, x1 & 0xFF
        ])
        
        # Row address set
        self._write_command(ST7789_RASET)
        self._write_data([
            (y0 >> 8) & 0xFF, y0 & 0xFF,
            (y1 >> 8) & 0xFF, y1 & 0xFF
        ])
        
        # Memory write command
        self._write_command(ST7789_RAMWR)
    
    def write_pixels(self, pixels: np.ndarray):
        """
        Write pixel data to display.
        
        Args:
            pixels: NumPy array of shape (height, width) with uint16 RGB565 values
                    or (height, width, 3) with uint8 RGB values
        """
        if pixels.dtype == np.uint8 and len(pixels.shape) == 3:
            # Convert RGB888 to RGB565
            r = (pixels[:, :, 0] >> 3).astype(np.uint16)
            g = (pixels[:, :, 1] >> 2).astype(np.uint16)
            b = (pixels[:, :, 2] >> 3).astype(np.uint16)
            pixels = (r << 11) | (g << 5) | b
        
        # Ensure uint16 and correct shape
        pixels = pixels.astype(np.uint16)
        height, width = pixels.shape
        
        # Set window to full area
        self.set_window(0, 0, width - 1, height - 1)
        
        # Convert to bytes (little-endian: LSB first)
        pixel_bytes = pixels.tobytes()
        
        # Send in chunks
        GPIO.output(PIN_DC, GPIO.HIGH)
        for i in range(0, len(pixel_bytes), SPI_CHUNK_SIZE):
            chunk = pixel_bytes[i:i + SPI_CHUNK_SIZE]
            self.spi.xfer2(list(chunk))
    
    def clear(self, color: int = 0x0000):
        """
        Clear entire display with a solid color.
        
        Args:
            color: RGB565 color value (default: black)
        """
        # Create a full-screen array of the color
        pixels = np.full((self.height, self.width), color, dtype=np.uint16)
        self.write_pixels(pixels)
    
    def cleanup(self):
        """Clean up GPIO and SPI resources."""
        if self._gpio_initialized:
            self.set_backlight(False)
            GPIO.cleanup()
        if self.spi:
            self.spi.close()
            self.spi = None

