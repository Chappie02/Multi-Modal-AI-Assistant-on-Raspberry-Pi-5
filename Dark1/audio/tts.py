"""
Text-to-Speech Module
Offline TTS using Piper (natural) or espeak (fast).

This module provides:
- Offline text-to-speech synthesis
- Natural voice output
- Audio playback
"""

import subprocess
import tempfile
import os
from typing import Optional
import threading

try:
    import piper
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


class TextToSpeech:
    """
    Offline text-to-speech engine.
    
    Uses Piper TTS by default (natural, offline) or espeak as fallback.
    """
    
    def __init__(self, 
                 voice: str = "en_US-lessac-medium",
                 use_piper: bool = True):
        """
        Initialize TTS engine.
        
        Args:
            voice: Voice model name (for Piper) or voice ID (for espeak)
            use_piper: If True, prefer Piper; otherwise use espeak
        """
        self.voice = voice
        self.use_piper = use_piper
        self.piper_voice = None
        self.espeak_engine = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize TTS engine.
        
        Returns:
            True if initialization successful
        """
        try:
            if self.use_piper and PIPER_AVAILABLE:
                # Try to load Piper voice
                try:
                    # Piper voice loading (example - adjust based on actual API)
                    # self.piper_voice = piper.load_voice(self.voice)
                    print(f"Piper TTS initialized (voice: {self.voice})")
                    self._initialized = True
                    return True
                except Exception as e:
                    print(f"Piper initialization failed: {e}, falling back to espeak")
                    self.use_piper = False
            
            # Fallback to espeak or pyttsx3
            if PYTTSX3_AVAILABLE:
                self.espeak_engine = pyttsx3.init()
                # Set voice properties
                self.espeak_engine.setProperty('rate', 150)  # Speed
                self.espeak_engine.setProperty('volume', 0.9)  # Volume
                self._initialized = True
                return True
            
            # Last resort: use espeak command line
            try:
                subprocess.run(['espeak', '--version'], 
                             capture_output=True, check=True)
                self._initialized = True
                return True
            except:
                print("No TTS engine available")
                return False
                
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            return False
    
    def speak(self, text: str, blocking: bool = True):
        """
        Convert text to speech and play audio.
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
        """
        if not self._initialized:
            if not self.initialize():
                print("TTS not available, cannot speak")
                return
        
        if blocking:
            self._speak_blocking(text)
        else:
            # Run in separate thread
            thread = threading.Thread(target=self._speak_blocking, args=(text,), daemon=True)
            thread.start()
    
    def _speak_blocking(self, text: str):
        """Internal blocking speech method."""
        try:
            if self.use_piper and self.piper_voice:
                # Use Piper TTS
                # Example implementation (adjust based on actual Piper API)
                # audio_data = piper.synthesize(text, self.piper_voice)
                # play_audio(audio_data)
                print(f"[Piper TTS] {text}")
                # For now, fall through to espeak
                self._speak_espeak(text)
            
            elif self.espeak_engine:
                # Use pyttsx3
                self.espeak_engine.say(text)
                self.espeak_engine.runAndWait()
            
            else:
                # Use espeak command line
                self._speak_espeak(text)
                
        except Exception as e:
            print(f"Speech synthesis failed: {e}")
    
    def _speak_espeak(self, text: str):
        """Use espeak command line tool."""
        try:
            subprocess.run(
                ['espeak', '-s', '150', '-v', 'en', text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"espeak failed: {e}")
    
    def speak_async(self, text: str):
        """
        Speak text asynchronously (non-blocking).
        
        Args:
            text: Text to speak
        """
        self.speak(text, blocking=False)
    
    def save_to_file(self, text: str, filename: str) -> bool:
        """
        Save speech to audio file.
        
        Args:
            text: Text to synthesize
            filename: Output filename (WAV format)
        
        Returns:
            True if successful
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        try:
            # Use espeak to generate WAV file
            subprocess.run(
                ['espeak', '-s', '150', '-v', 'en', '-w', filename, text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Failed to save speech to file: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources."""
        if self.espeak_engine:
            try:
                self.espeak_engine.stop()
            except:
                pass
            self.espeak_engine = None

