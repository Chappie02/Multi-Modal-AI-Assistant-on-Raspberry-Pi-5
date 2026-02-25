import logging
import subprocess


class TextToSpeech:
    """
    Simple offline TTS using `espeak`.
    """

    def __init__(self, voice: str = "en") -> None:
        self.log = logging.getLogger("tts")
        self.voice = voice

    def speak(self, text: str) -> None:
        if not text:
            return
        try:
            subprocess.run(
                ["espeak", "-v", self.voice, text],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            self.log.exception("TTS failed for text: %s", text)

