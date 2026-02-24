import logging
import time
from typing import Optional

from hardware.animation import AnimationManager
from hardware.buttons import ButtonEvent, ButtonEventType
from hardware.oled import OledDisplay
from audio.recorder import AudioRecorder
from audio.stt import SpeechToText
from audio.tts import TextToSpeech
from ai.llm import LlmChat
from ai.vision import VisionSystem
from rag.retriever import RagRetriever


class Controller:
    """
    Central coordinator.

    - All heavy work runs in the main thread via handle_event.
    - Animation runs in its own thread (managed by AnimationManager).
    - ButtonListener runs in its own thread and pushes ButtonEvent into a queue.
    """

    def __init__(
        self,
        oled: OledDisplay,
        animation: AnimationManager,
        event_queue,
    ) -> None:
        self.log = logging.getLogger("controller")
        self.oled = oled
        self.animation = animation
        self.event_queue = event_queue

        # Subsystems
        self.vision = VisionSystem()
        self.recorder = AudioRecorder()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.llm = LlmChat()

        # RAG subsystem (optional but preferred). If initialisation fails,
        # the assistant will still operate in plain LLM mode.
        self.rag: Optional[RagRetriever] = None
        try:
            self.rag = RagRetriever()
        except Exception:
            self.log.exception("Failed to initialise RAG. Falling back to plain LLM.")

        self._chat_recording = False

    # -------------------------------------------------
    # Event entry point
    # -------------------------------------------------
    def handle_event(self, event: ButtonEvent) -> None:
        try:
            if event.event_type == ButtonEventType.K2_OBJECT_DETECT:
                self._handle_object_detection()
            elif event.event_type == ButtonEventType.K3_SHORT_CAPTURE:
                self._handle_image_capture()
            elif event.event_type == ButtonEventType.K1_LONG_CHAT_START:
                self._handle_chat_start()
            elif event.event_type == ButtonEventType.K1_LONG_CHAT_END:
                self._handle_chat_end()
        except Exception as e:
            self.log.exception("Error handling event %s: %s", event, e)
            self._return_to_idle()

    # -------------------------------------------------
    # Feature 1 – Object detection (K2)
    # -------------------------------------------------
    def _handle_object_detection(self) -> None:
        self.log.info("Object detection triggered.")
        try:
            self.animation.pause()
            self.oled.show_text(["Object detect..."])

            image, label = self.vision.detect_first_object()
            self.log.info("Object detection result: label=%s", label)

            if label:
                msg = f"Object: {label}"
                self.oled.show_text([msg])
                try:
                    self.tts.speak(label)
                except Exception:
                    self.log.exception("TTS failed during object detection.")
            else:
                self.oled.show_text(["No object"])
                try:
                    self.tts.speak("No object detected.")
                except Exception:
                    self.log.exception("TTS failed for 'no object'.")

            time.sleep(2.5)
        except Exception:
            self.log.exception("Object detection failed.")
        finally:
            self._return_to_idle()

    # -------------------------------------------------
    # Feature 2 – Image capture (K3 short)
    # -------------------------------------------------
    def _handle_image_capture(self) -> None:
        self.log.info("Image capture triggered (short press).")
        try:
            self.animation.pause()
            self.oled.show_text(["Capturing image..."])

            saved_path = self.vision.capture_and_save_image()
            if saved_path:
                self.oled.show_text(["Image Saved"])
            else:
                self.oled.show_text(["Save failed"])

            time.sleep(2.0)
        except Exception:
            self.log.exception("Image capture failed.")
        finally:
            self._return_to_idle()

    # -------------------------------------------------
    # Feature 3 – LLM chat (K1 hold >= 1s)
    # -------------------------------------------------
    def _handle_chat_start(self) -> None:
        self.log.info("Chat start (K1 hold detected).")
        try:
            self.animation.pause()
            self.oled.clear()
            self.oled.show_text(["Listening..."])
            self.recorder.start()
            self._chat_recording = True
        except Exception:
            self.log.exception("Failed to start recording for chat.")
            self._chat_recording = False
            self._return_to_idle()

    def _handle_chat_end(self) -> None:
        self.log.info("Chat end (button released).")
        try:
            if not self._chat_recording:
                self.log.warning("Chat end received but recording was not active.")
                self._return_to_idle()
                return

            audio_path = None
            try:
                audio_path = self.recorder.stop()
            finally:
                self._chat_recording = False

            if not audio_path:
                self.oled.show_text(["No audio"])
                time.sleep(1.0)
                return

            # STT
            self.oled.show_text(["Transcribing..."])
            try:
                user_text = self.stt.transcribe(audio_path) or ""
            except Exception:
                self.log.exception("STT failed.")
                user_text = ""

            if not user_text.strip():
                self.oled.show_text(["Didn't hear", "anything."])
                try:
                    self.tts.speak("I didn't hear anything.")
                except Exception:
                    self.log.exception("TTS failed after empty STT.")
                time.sleep(1.5)
                return

            # LLM with optional RAG context (K1 only).
            self.log.info("User said: %s", user_text)
            self.oled.show_text(["Thinking..."])

            context_chunks = []
            if self.rag is not None:
                try:
                    context_chunks = self.rag.retrieve_context(user_text, top_k=3)
                except Exception:
                    # Any failure here should not break the chat experience.
                    self.log.exception(
                        "RAG retrieval failed, falling back to normal LLM."
                    )
                    context_chunks = []

            full_response = ""
            try:
                for token in self.llm.stream_chat(
                    user_text, context_chunks=context_chunks or None
                ):
                    full_response += token
                    self.oled.show_streaming_text(full_response)
            except Exception:
                self.log.exception("LLM streaming failed.")

            if not full_response.strip():
                full_response = "I had a problem answering."

            # Keep the final text on the OLED briefly before TTS starts.
            time.sleep(2.0)

            try:
                self.tts.speak(full_response)
            except Exception:
                self.log.exception("TTS failed for LLM response.")

            # Persist this turn into the vector store so that future
            # retrieval can use conversational history as additional context.
            if self.rag is not None:
                try:
                    self.rag.add_conversation(user_text, full_response)
                except Exception:
                    self.log.exception("Failed to store conversation in RAG.")

        except Exception:
            self.log.exception("Chat flow failed.")
        finally:
            self._return_to_idle()

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------
    def _return_to_idle(self) -> None:
        try:
            self.oled.clear()
        except Exception:
            self.log.exception("Failed to clear OLED when returning to idle.")
        try:
            self.animation.resume()
        except Exception:
            self.log.exception("Failed to resume animation.")

