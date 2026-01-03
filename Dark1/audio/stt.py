"""
Speech-to-Text Module
Offline STT using Vosk (lightweight) or Whisper (accurate).

This module provides:
- Offline speech recognition
- Real-time transcription
- Audio recording and processing
"""

import pyaudio
import wave
import json
from typing import Optional
import threading
import time
import io

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("Vosk not available. Install with: pip install vosk")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class SpeechToText:
    """
    Offline speech-to-text engine.
    
    Uses Vosk by default (lightweight, fast) or Whisper (more accurate).
    """
    
    def __init__(self, 
                 model_path: str = "vosk-model-small-en-us-0.15",
                 use_whisper: bool = False,
                 whisper_model: str = "base"):
        """
        Initialize STT engine.
        
        Args:
            model_path: Path to Vosk model directory
            use_whisper: If True, use Whisper instead of Vosk
            whisper_model: Whisper model size (tiny, base, small, medium)
        """
        self.model_path = model_path
        self.use_whisper = use_whisper
        self.whisper_model_name = whisper_model
        
        self.vosk_model = None
        self.whisper_model = None
        self.pa = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Load STT model.
        
        Returns:
            True if initialization successful
        """
        try:
            if self.use_whisper and WHISPER_AVAILABLE:
                # Load Whisper model
                print(f"Loading Whisper model: {self.whisper_model_name}")
                self.whisper_model = whisper.load_model(self.whisper_model_name)
                self._initialized = True
                return True
            
            elif VOSK_AVAILABLE:
                # Load Vosk model
                print(f"Loading Vosk model from: {self.model_path}")
                self.vosk_model = Model(self.model_path)
                self._initialized = True
                return True
            
            else:
                print("No STT engine available. Install vosk or whisper.")
                return False
                
        except Exception as e:
            print(f"STT initialization failed: {e}")
            return False
    
    def record_audio(self, duration: float = 5.0, sample_rate: int = 16000) -> bytes:
        """
        Record audio from microphone.
        
        Args:
            duration: Recording duration in seconds
            sample_rate: Sample rate in Hz (16kHz recommended)
        
        Returns:
            Audio data as bytes
        """
        if not self.pa:
            self.pa = pyaudio.PyAudio()
        
        chunk = 1024
        format = pyaudio.paInt16
        channels = 1
        
        stream = self.pa.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk
        )
        
        frames = []
        num_chunks = int(sample_rate / chunk * duration)
        
        print("Recording...")
        for _ in range(num_chunks):
            data = stream.read(chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Combine frames
        audio_data = b''.join(frames)
        return audio_data
    
    def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio data as bytes
            sample_rate: Sample rate of audio
        
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self._initialized:
            if not self.initialize():
                return None
        
        try:
            if self.use_whisper and self.whisper_model:
                # Use Whisper
                # Convert bytes to numpy array
                import numpy as np
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                result = self.whisper_model.transcribe(audio_np, language="en")
                return result["text"].strip()
            
            elif self.vosk_model:
                # Use Vosk
                rec = KaldiRecognizer(self.vosk_model, sample_rate)
                rec.SetWords(True)
                
                # Process audio in chunks
                text_parts = []
                chunk_size = 4000
                
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    if rec.AcceptWaveform(chunk):
                        result = json.loads(rec.Result())
                        if 'text' in result:
                            text_parts.append(result['text'])
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if 'text' in final_result:
                    text_parts.append(final_result['text'])
                
                return ' '.join(text_parts).strip()
            
            return None
            
        except Exception as e:
            print(f"Transcription failed: {e}")
            return None
    
    def listen_and_transcribe(self, duration: float = 5.0) -> Optional[str]:
        """
        Record audio and transcribe in one step.
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            Transcribed text or None
        """
        audio_data = self.record_audio(duration)
        return self.transcribe(audio_data)
    
    def cleanup(self):
        """Clean up resources."""
        if self.pa:
            self.pa.terminate()
            self.pa = None

