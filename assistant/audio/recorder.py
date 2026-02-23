import logging
import tempfile
import wave
from typing import Optional

try:
    import sounddevice as sd
except Exception:  # pragma: no cover
    sd = None


class AudioRecorder:
    """
    Simple blocking recorder using sounddevice.

    For push-to-talk:
      - start(): begin recording into an in-memory buffer
      - stop(): write buffer to temp WAV file and return path
    """

    def __init__(self, samplerate: int = 16000, channels: int = 1) -> None:
        self.log = logging.getLogger("recorder")
        self.samplerate = samplerate
        self.channels = channels
        self._buffer = []
        self._stream = None

    def start(self) -> None:
        if sd is None:
            self.log.error("sounddevice not available, cannot record.")
            return
        try:
            self._buffer = []

            def callback(indata, frames, time_info, status):  # type: ignore[override]
                if status:
                    self.log.warning("Recorder status: %s", status)
                self._buffer.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                callback=callback,
            )
            self._stream.start()
        except Exception:
            self.log.exception("Failed to start recording.")
            self._stream = None
            self._buffer = []

    def stop(self) -> Optional[str]:
        if sd is None:
            return None
        try:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
        except Exception:
            self.log.exception("Failed to stop recording stream.")
        finally:
            self._stream = None

        try:
            if not self._buffer:
                return None

            import numpy as np

            data = np.concatenate(self._buffer, axis=0)

            tmp = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, prefix="assistant_audio_"
            )
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.samplerate)
                wf.writeframes((data * 32767).astype("int16").tobytes())

            path = tmp.name
            self.log.info("Saved audio to %s", path)
            return path
        except Exception:
            self.log.exception("Failed to save recorded audio.")
            return None

