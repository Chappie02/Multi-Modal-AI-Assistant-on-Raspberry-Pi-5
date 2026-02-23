import logging
from typing import Optional

try:
    import vosk
except Exception:  # pragma: no cover
    vosk = None


class SpeechToText:
    """
    Offline STT using Vosk.
    Expects a model folder at models/vosk/.
    """

    def __init__(self, model_path: str = "models/vosk") -> None:
        self.log = logging.getLogger("stt")
        self.model = None
        try:
            if vosk is None:
                raise RuntimeError("vosk is not installed.")
            self.model = vosk.Model(model_path)
        except Exception as e:
            self.log.exception("Failed to load Vosk model: %s", e)

    def transcribe(self, wav_path: str) -> Optional[str]:
        if self.model is None or vosk is None:
            self.log.error("STT model not available.")
            return None
        try:
            import wave
            import json

            wf = wave.open(wav_path, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                self.log.warning("Unexpected audio format for STT.")

            rec = vosk.KaldiRecognizer(self.model, wf.getframerate())
            text_fragments = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    if "text" in res and res["text"]:
                        text_fragments.append(res["text"])

            final_res = json.loads(rec.FinalResult())
            if "text" in final_res and final_res["text"]:
                text_fragments.append(final_res["text"])

            full_text = " ".join(text_fragments).strip()
            self.log.info("STT result: %s", full_text)
            return full_text
        except Exception:
            self.log.exception("STT transcription failed.")
            return None

