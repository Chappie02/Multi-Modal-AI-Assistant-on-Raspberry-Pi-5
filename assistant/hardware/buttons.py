import logging
import time
from dataclasses import dataclass
from enum import Enum, auto

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover - not on Pi
    GPIO = None


class ButtonEventType(Enum):
    K2_OBJECT_DETECT = auto()
    K3_SHORT_CAPTURE = auto()
    K1_LONG_CHAT_START = auto()
    K1_LONG_CHAT_END = auto()


@dataclass
class ButtonEvent:
    event_type: ButtonEventType


class ButtonListener:
    """
    Single thread that monitors buttons and pushes ButtonEvent into a queue.

    - K2: object detection (single press)
    - K3: short press (< 1s) → image capture
    - K1: long press (>= 1s) → push-to-talk chat

    For K1 long press chat:
      - On K1 press crossing 1s threshold: send K1_LONG_CHAT_START
      - On K1 release after long press:   send K1_LONG_CHAT_END
    """

    K1_PIN = 17  # Push-to-talk (long press)
    K2_PIN = 27  # Object detection
    K3_PIN = 22  # Image capture (short press)

    def __init__(self, event_queue) -> None:
        self.log = logging.getLogger("buttons")
        self.event_queue = event_queue

        self._k1_pressed = False
        self._k1_press_time = 0.0
        self._k1_long_sent = False

        self._k3_pressed = False
        self._k3_press_time = 0.0

        # Track whether GPIO was successfully initialised.
        self._gpio_ok = False

        try:
            if GPIO is None:
                raise RuntimeError("RPi.GPIO not available.")

            GPIO.setmode(GPIO.BCM)
            for pin in (self.K1_PIN, self.K2_PIN, self.K3_PIN):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._gpio_ok = True
        except RuntimeError as e:
            # Common when running off‑Pi or without proper /dev/mem access.
            # Treat as "no GPIO available" but do not crash or spam a traceback.
            self._gpio_ok = False
            self.log.error("GPIO unavailable, running without buttons: %s", e)
        except Exception as e:
            self._gpio_ok = False
            self.log.exception("Failed to initialize GPIO: %s", e)

    def _read_pin(self, pin: int) -> bool:
        """
        Returns True if button is pressed (active low).
        """
        if GPIO is None or not getattr(self, "_gpio_ok", False):
            return False
        try:
            return GPIO.input(pin) == GPIO.LOW
        except Exception:
            self.log.exception("Failed to read GPIO pin %s", pin)
            return False

    def run(self) -> None:
        self.log.info("Button listener thread started.")
        try:
            while True:
                self._poll_k1()
                self._poll_k2()
                self._poll_k3()
                time.sleep(0.01)
        except Exception:
            self.log.exception("Button listener crashed.")

    # -------------------------------------------------
    # K1 – push-to-talk (long press >= 1s)
    # -------------------------------------------------
    def _poll_k1(self) -> None:
        if GPIO is None:
            return
        try:
            pressed = self._read_pin(self.K1_PIN)
            now = time.time()

            if pressed and not self._k1_pressed:
                self._k1_pressed = True
                self._k1_press_time = now
                self._k1_long_sent = False

            if self._k1_pressed and not pressed:
                duration = now - self._k1_press_time
                if duration >= 1.0 and self._k1_long_sent:
                    self.event_queue.put(ButtonEvent(ButtonEventType.K1_LONG_CHAT_END))
                self._k1_pressed = False
                self._k1_long_sent = False

            if self._k1_pressed and not self._k1_long_sent:
                duration = now - self._k1_press_time
                if duration >= 1.0:
                    self._k1_long_sent = True
                    self.event_queue.put(ButtonEvent(ButtonEventType.K1_LONG_CHAT_START))
        except Exception:
            self.log.exception("Error polling K1.")

    # -------------------------------------------------
    # K2 – object detection
    # -------------------------------------------------
    def _poll_k2(self) -> None:
        if GPIO is None:
            return
        try:
            pressed = self._read_pin(self.K2_PIN)
            if pressed:
                # simple edge detection debounce
                time.sleep(0.03)
                if self._read_pin(self.K2_PIN):
                    self.event_queue.put(ButtonEvent(ButtonEventType.K2_OBJECT_DETECT))
                    # wait for release
                    while self._read_pin(self.K2_PIN):
                        time.sleep(0.02)
        except Exception:
            self.log.exception("Error polling K2.")

    # -------------------------------------------------
    # K3 – short press only (image capture)
    # -------------------------------------------------
    def _poll_k3(self) -> None:
        if GPIO is None:
            return
        try:
            pressed = self._read_pin(self.K3_PIN)
            now = time.time()

            if pressed and not self._k3_pressed:
                self._k3_pressed = True
                self._k3_press_time = now

            if self._k3_pressed and not pressed:
                duration = now - self._k3_press_time
                if duration < 1.0:
                    self.event_queue.put(ButtonEvent(ButtonEventType.K3_SHORT_CAPTURE))
                self._k3_pressed = False
        except Exception:
            self.log.exception("Error polling K3.")

