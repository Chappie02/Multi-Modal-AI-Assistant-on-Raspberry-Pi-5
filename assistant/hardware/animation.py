import logging
import threading
import time
from typing import Optional

from .oled import OledDisplay

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


class AnimationManager:
    """
    Manages the continuous robot eye animation in a dedicated thread.

    The public API is pause()/resume(). The run() method is intended to be
    used as the target of the single animation thread.
    """

    def __init__(self, oled: OledDisplay) -> None:
        self.log = logging.getLogger("animation")
        self.oled = oled
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

        # internal eye state
        self.WIDTH = OledDisplay.WIDTH
        self.HEIGHT = OledDisplay.HEIGHT
        self.ref_eye_height = 40
        self.ref_eye_width = 40
        self.ref_space_between_eye = 10
        self.ref_corner_radius = 10

        self.left_eye_height = self.ref_eye_height
        self.left_eye_width = self.ref_eye_width
        self.right_eye_height = self.ref_eye_height
        self.right_eye_width = self.ref_eye_width

        self.left_eye_x = 32
        self.left_eye_y = 32
        self.right_eye_x = 32 + self.ref_eye_width + self.ref_space_between_eye
        self.right_eye_y = 32

        self.image = None
        self.draw = None
        try:
            if Image is not None:
                self.image = Image.new("1", (self.WIDTH, self.HEIGHT))
                self.draw = ImageDraw.Draw(self.image)
        except Exception:
            self.log.exception("Failed to create animation image buffer.")

    # -------------------------------------------------
    # Public control
    # -------------------------------------------------
    def pause(self) -> None:
        try:
            self._pause_event.set()
        except Exception:
            self.log.exception("Failed to pause animation.")

    def resume(self) -> None:
        try:
            self._pause_event.clear()
        except Exception:
            self.log.exception("Failed to resume animation.")

    def stop(self) -> None:
        try:
            self._stop_event.set()
        except Exception:
            self.log.exception("Failed to stop animation.")

    # -------------------------------------------------
    # Internal drawing helpers
    # -------------------------------------------------
    def _draw_eyes(self) -> None:
        if self.oled.display is None or self.image is None or self.draw is None:
            return
        try:
            self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=0)

            lx = int(self.left_eye_x - self.left_eye_width / 2)
            ly = int(self.left_eye_y - self.left_eye_height / 2)
            rx = int(self.right_eye_x - self.right_eye_width / 2)
            ry = int(self.right_eye_y - self.right_eye_height / 2)

            self.draw.rounded_rectangle(
                (lx, ly, lx + self.left_eye_width, ly + self.left_eye_height),
                radius=self.ref_corner_radius,
                fill=255,
            )

            self.draw.rounded_rectangle(
                (rx, ry, rx + self.right_eye_width, ry + self.right_eye_height),
                radius=self.ref_corner_radius,
                fill=255,
            )

            self.oled.display.image(self.image)
            self.oled.display.show()
        except Exception:
            self.log.exception("Failed to draw eyes.")

    def _center_eyes(self) -> None:
        self.left_eye_height = self.ref_eye_height
        self.left_eye_width = self.ref_eye_width
        self.right_eye_height = self.ref_eye_height
        self.right_eye_width = self.ref_eye_width

        self.left_eye_x = (
            self.WIDTH // 2 - self.ref_eye_width // 2 - self.ref_space_between_eye // 2
        )
        self.left_eye_y = self.HEIGHT // 2
        self.right_eye_x = (
            self.WIDTH // 2 + self.ref_eye_width // 2 + self.ref_space_between_eye // 2
        )
        self.right_eye_y = self.HEIGHT // 2
        self._draw_eyes()

    def _blink(self, speed: int = 12) -> None:
        try:
            for _ in range(3):
                self.left_eye_height -= speed
                self.right_eye_height -= speed
                self._draw_eyes()
                time.sleep(0.02)

            for _ in range(3):
                self.left_eye_height += speed
                self.right_eye_height += speed
                self._draw_eyes()
                time.sleep(0.02)
        except Exception:
            self.log.exception("Blink animation failed.")

    def _slow_move(self, direction: str, steps: int = 10, delay: float = 0.05) -> None:
        try:
            dx = 2 if direction == "right" else -2
            for _ in range(steps):
                self.left_eye_x += dx
                self.right_eye_x += dx
                self._draw_eyes()
                time.sleep(delay)
        except Exception:
            self.log.exception("Slow move animation failed.")

    # -------------------------------------------------
    # Main loop – 5s sequence
    # -------------------------------------------------
    def run(self) -> None:
        """
        Continuous loop:
          - Center
          - Slow left
          - Center
          - Slow right
          - Blink
        """
        self.log.info("Animation thread started.")

        while not self._stop_event.is_set():
            try:
                if self._pause_event.is_set():
                    time.sleep(0.05)
                    continue

                start = time.time()

                # Center
                self._center_eyes()
                time.sleep(0.5)

                # Slow left
                self._slow_move("left")
                time.sleep(0.3)

                # Center
                self._center_eyes()
                time.sleep(0.3)

                # Slow right
                self._slow_move("right")
                time.sleep(0.3)

                # Back to center and blink
                self._center_eyes()
                self._blink()

                # Ensure roughly 5s total
                elapsed = time.time() - start
                remaining = max(0.0, 5.0 - elapsed)
                time.sleep(remaining)
            except Exception:
                self.log.exception("Animation loop iteration failed.")
                time.sleep(0.1)

        self.log.info("Animation thread exiting.")

