import logging
import threading
import time

from .oled import OledDisplay

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None


class AnimationManager:
    """
    Continuous 5-second robot eye animation.

    Sequence:
        Center
        Slow Left
        Center
        Slow Right
        Blink
    """

    def __init__(self, oled: OledDisplay) -> None:
        self.log = logging.getLogger("animation")
        self.oled = oled

        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

        self.WIDTH = OledDisplay.WIDTH
        self.HEIGHT = OledDisplay.HEIGHT

        # Eye reference settings
        self.ref_eye_height = 40
        self.ref_eye_width = 40
        self.ref_space_between_eye = 10
        self.ref_corner_radius = 10

        # Initial state
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
    # Public Control
    # -------------------------------------------------

    def pause(self) -> None:
        self._pause_event.set()

    def resume(self) -> None:
        self._pause_event.clear()

    def stop(self) -> None:
        self._stop_event.set()

    # -------------------------------------------------
    # Drawing Helpers
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
            # Use the OLED helper so that any display rotation is applied
            # consistently for both text and animations.
            self.oled.show_image(self.image)

        except Exception:
            self.log.exception("Failed to draw eyes.")

    def _center_eyes(self) -> None:
        self.left_eye_height = self.ref_eye_height
        self.right_eye_height = self.ref_eye_height

        self.left_eye_x = (
            self.WIDTH // 2 - self.ref_eye_width // 2 - self.ref_space_between_eye // 2
        )
        self.left_eye_y = self.HEIGHT // 2

        self.right_eye_x = (
            self.WIDTH // 2 + self.ref_eye_width // 2 + self.ref_space_between_eye // 2
        )
        self.right_eye_y = self.HEIGHT // 2

        self._draw_eyes()

    def _slow_move(self, direction: str) -> None:
        try:
            original_left = self.left_eye_x
            original_right = self.right_eye_x

            dx = 2 if direction == "right" else -2

            for _ in range(12):
                self.left_eye_x += dx
                self.right_eye_x += dx
                self._draw_eyes()
                time.sleep(0.03)

            # Restore center
            self.left_eye_x = original_left
            self.right_eye_x = original_right
            self._draw_eyes()

        except Exception:
            self.log.exception("Slow move animation failed.")

    def _blink(self) -> None:
        try:
            original_height = self.ref_eye_height

            # Close
            for h in range(original_height, 4, -8):
                self.left_eye_height = h
                self.right_eye_height = h
                self._draw_eyes()
                time.sleep(0.02)

            # Open
            for h in range(4, original_height + 1, 8):
                self.left_eye_height = h
                self.right_eye_height = h
                self._draw_eyes()
                time.sleep(0.02)

            # Reset
            self.left_eye_height = self.ref_eye_height
            self.right_eye_height = self.ref_eye_height
            self._draw_eyes()

        except Exception:
            self.log.exception("Blink animation failed.")

    # -------------------------------------------------
    # Main Animation Loop
    # -------------------------------------------------

    def run(self) -> None:
        self.log.info("Animation thread started.")

        while not self._stop_event.is_set():
            try:
                if self._pause_event.is_set():
                    time.sleep(0.05)
                    continue

                cycle_start = time.time()

                # 1. Center
                self._center_eyes()
                time.sleep(0.7)

                # 2. Slow Left
                self._slow_move("left")
                time.sleep(0.5)

                # 3. Center
                self._center_eyes()
                time.sleep(0.5)

                # 4. Slow Right
                self._slow_move("right")
                time.sleep(0.5)

                # 5. Blink
                self._blink()

                # Ensure total ~5 seconds
                elapsed = time.time() - cycle_start
                remaining = max(0.0, 5.0 - elapsed)
                time.sleep(remaining)

            except Exception:
                self.log.exception("Animation loop iteration failed.")
                time.sleep(0.1)

        self.log.info("Animation thread exiting.")
