"""
Voice Synthesis & Natural Audio Speech Service for InboxPilot AI.
Uses gTTS (Google Text-to-Speech) with pyttsx3/espeak offline fallback and audio hardware playback.
"""

import os
import time
import tempfile
import threading
import queue
from pathlib import Path
from typing import Optional

from gtts import gTTS
from config.settings import settings
from utils.logger import logger

# Initialize pygame mixer silently if available
PYGAME_AVAILABLE = False
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False


class VoiceService:
    """
    Text-to-Speech Engine with queueing and synchronous completion options.
    """

    def __init__(self):
        self.enabled = settings.VOICE_ENABLED
        self.lang = settings.VOICE_LANG
        self.tld = settings.VOICE_TLD
        self.speech_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._worker_thread.start()

    def speak(self, text: str, priority: bool = False) -> None:
        """
        Enqueues text to be spoken asynchronously.
        """
        if not self.enabled or not text.strip():
            logger.info(f"[VOICE DISABLED / SKIPPED] Text: '{text[:50]}...'")
            return

        logger.info(f"[VOICE ENQUEUED] Spoken text: '{text[:80]}...'")
        self.speech_queue.put(text)

    def speak_sync(self, text: str) -> None:
        """
        Synthesizes and speaks text synchronously (blocking until audio finishes playing).
        """
        if not self.enabled or not text.strip():
            return
        logger.info(f"[VOICE SPEAKING LIVE] '{text[:80]}...'")
        self._synthesize_and_play(text)

    def wait_until_done(self) -> None:
        """
        Waits for all enqueued audio speech items in queue to finish playing.
        """
        self.speech_queue.join()

    def _speech_worker(self) -> None:
        """
        Worker thread executing queued audio speech sequentially.
        """
        while True:
            try:
                text = self.speech_queue.get()
                if text is None:
                    break
                self._synthesize_and_play(text)
                self.speech_queue.task_done()
            except Exception as e:
                logger.error(f"Error in speech worker thread: {e}")

    def _synthesize_and_play(self, text: str) -> None:
        """
        Generates audio MP3 file via gTTS and plays it via available system sound driver.
        """
        temp_file = None
        try:
            # Create temporary MP3 file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_file = fp.name

            # Synthesize voice via gTTS
            tts = gTTS(text=text, lang=self.lang, tld=self.tld, slow=False)
            tts.save(temp_file)

            # Play audio file
            self._play_audio_file(temp_file)

        except Exception as e:
            logger.warning(f"gTTS Speech synthesis failed: {e}. Trying offline text-to-speech fallback...")
            self._offline_tts_fallback(text)
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    time.sleep(0.3)
                    os.remove(temp_file)
                except Exception:
                    pass

    def _play_audio_file(self, file_path: str) -> None:
        """
        Plays MP3 audio using Pygame mixer or system fallback commands (mpg123/ffplay/aplay/paplay).
        """
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                return
            except Exception as e:
                logger.warning(f"Pygame audio playback failed: {e}. Falling back to system utilities.")

        # System command fallback on Linux / OS
        for cmd in [
            f"mpg123 -q '{file_path}'",
            f"ffplay -nodisp -autoexit -loglevel quiet '{file_path}'",
            f"paplay '{file_path}'",
            f"aplay '{file_path}'"
        ]:
            ret = os.system(cmd)
            if ret == 0:
                return

        logger.warning("No audio player utility found. Voice text processed without hardware audio output.")

    def _offline_tts_fallback(self, text: str) -> None:
        """
        Offline TTS fallback using espeak or spd-say.
        """
        cleaned_text = text.replace("'", "'\\''")
        for cmd in [f"spd-say '{cleaned_text}'", f"espeak '{cleaned_text}'"]:
            ret = os.system(cmd)
            if ret == 0:
                return


# Singleton voice service instance
voice_service = VoiceService()
