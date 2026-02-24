import logging
from typing import List

try:
    import board
    import busio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_ssd1306
except Exception:  # pragma: no cover - hardware not available on dev machine
    board = None
    busio = None
    Image = None
    ImageDraw = None
    ImageFont = None
    adafruit_ssd1306 = None


class OledDisplay:
    WIDTH = 128
    HEIGHT = 64

    def __init__(self) -> None:
        self.log = logging.getLogger("oled")
        self.display = None
        self.image = None
        self.draw = None
        self.font = None
        # When True, the rendered buffer is rotated 180 degrees before
        # being sent to the physical display. Useful when the OLED module
        # is mounted upside‑down.
        self.rotate_180 = True

        try:
            if busio is None or adafruit_ssd1306 is None or Image is None:
                raise RuntimeError("OLED hardware libraries not available.")

            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = adafruit_ssd1306.SSD1306_I2C(
                self.WIDTH, self.HEIGHT, i2c
            )
            self.image = Image.new("1", (self.WIDTH, self.HEIGHT))
            self.draw = ImageDraw.Draw(self.image)
            try:
                self.font = ImageFont.load_default()
            except Exception:
                self.font = None

            self.clear()
        except Exception as e:
            self.log.exception("Failed to initialize OLED: %s", e)

    def clear(self) -> None:
        try:
            if self.display is None:
                return
            self.display.fill(0)
            self.display.show()
        except Exception:
            self.log.exception("Failed to clear OLED.")

    def _push_image(self, image) -> None:
        """
        Push a PIL image to the OLED, applying rotation if configured.
        """
        if self.display is None:
            return
        try:
            to_show = image
            if self.rotate_180 and Image is not None:
                to_show = image.rotate(180)
            self.display.image(to_show)
            self.display.show()
        except Exception:
            self.log.exception("Failed to push image to OLED.")

    def _draw_text_lines(self, lines: List[str]) -> None:
        if self.display is None or self.image is None or self.draw is None:
            return
        try:
            self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=0)
            y = 0
            for line in lines[:4]:
                self.draw.text((0, y), line, font=self.font, fill=255)
                y += 16
            self._push_image(self.image)
        except Exception:
            self.log.exception("Failed to draw text on OLED.")

    def show_text(self, lines: List[str]) -> None:
        try:
            self._draw_text_lines(lines)
        except Exception:
            self.log.exception("show_text failed.")

    def show_streaming_text(self, text: str) -> None:
        """
        For streaming LLM tokens. We keep only the last few lines that fit.
        """
        try:
            # naive word wrap based on character count
            max_chars_per_line = 21
            words = text.split()
            lines: List[str] = []
            current = ""

            for w in words:
                if len(current) + 1 + len(w) > max_chars_per_line:
                    lines.append(current)
                    current = w
                else:
                    if current:
                        current += " " + w
                    else:
                        current = w
            if current:
                lines.append(current)

            self._draw_text_lines(lines[-4:])
        except Exception:
            self.log.exception("show_streaming_text failed.")

    def show_image(self, image) -> None:
        """
        Public helper for other components (like the animation manager)
        to draw a pre‑rendered PIL image on the OLED with the same
        rotation behavior.
        """
        try:
            self._push_image(image)
        except Exception:
            self.log.exception("show_image failed.")

