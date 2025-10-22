"""Speech recognition and transcription using OpenAI Whisper."""

import io
import logging
import os
import sys
import time
from typing import Optional

import numpy as np
import whisper
from colorama import Fore, Style

from .audio import AudioStream, calculate_energy
from .audio_feedback import wake_word_detected_sound
from .config import (
    AUTO_CALIBRATE_THRESHOLD,
    MAX_RECORDING_DURATION,
    MIN_RECORDING_DURATION,
    PASTE_WORD,
    SAMPLE_RATE,
    SILENCE_DURATION,
    SILENCE_THRESHOLD,
    WAKE_WORD,
    WHISPER_MODEL,
)

logger = logging.getLogger(__name__)


class SpeechRecognizer:
    """Handles speech recognition using OpenAI Whisper."""

    def __init__(self, model_name: str = WHISPER_MODEL):
        """Initialize the speech recognizer with a Whisper model."""
        logger.info(f"Loading Whisper model: {model_name}")
        logger.info(
            "First run will download the model. This may take a few minutes..."
        )
        self.model = whisper.load_model(model_name)
        logger.info("Model loaded successfully")

        self.silence_threshold = SILENCE_THRESHOLD
        self.calibrated = False

    def calibrate_threshold(self, audio_stream: AudioStream) -> None:
        """Calibrate the silence threshold based on ambient noise."""
        if not AUTO_CALIBRATE_THRESHOLD or self.calibrated:
            return

        print(f"{Fore.BLUE}Calibrating...{Style.RESET_ALL}", end="", flush=True)

        energy_samples = []
        start_time = time.time()

        while time.time() - start_time < 2.0:
            audio_data = audio_stream.read()
            energy = calculate_energy(audio_data)
            energy_samples.append(energy)

        if energy_samples:
            avg_noise = np.mean(energy_samples)
            # Set threshold to 1.5x the average noise level, with a minimum
            self.silence_threshold = max(3, int(avg_noise * 1.5))
            print(f"\r{Fore.GREEN}✓ Calibrated{Style.RESET_ALL} (threshold: {self.silence_threshold})       ")
            self.calibrated = True

    def transcribe_audio(self, audio_stream: AudioStream, keyboard_trigger: dict = None) -> str:
        """
        Transcribe audio from the stream until silence is detected or manual stop.

        Args:
            audio_stream: AudioStream object providing audio data
            keyboard_trigger: Optional dict with 'stop_requested' flag for manual stop

        Returns:
            Transcribed text
        """
        logger.info("Starting transcription...")

        audio_chunks = []
        silence_start = None
        recording_start = time.time()
        has_audio = False

        while True:
            # Check for manual stop via keyboard
            if keyboard_trigger and keyboard_trigger.get("stop_requested", False):
                logger.info("Manual stop requested")
                break

            # Check max recording duration
            if time.time() - recording_start > MAX_RECORDING_DURATION:
                logger.info("Max recording duration reached")
                break

            # Read audio chunk
            audio_data = audio_stream.read()
            energy = calculate_energy(audio_data)

            # Track if we've received any actual audio
            if energy >= self.silence_threshold:
                has_audio = True
                silence_start = None
            elif has_audio:
                # Only start counting silence after we've had some audio
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > SILENCE_DURATION:
                    logger.info("Silence detected, stopping recording")
                    break

            # Collect audio data
            audio_chunks.append(audio_data)

        # Check if we have enough audio
        recording_duration = time.time() - recording_start
        if recording_duration < MIN_RECORDING_DURATION or not has_audio:
            logger.warning("Recording too short or no audio detected")
            return ""

        # Combine all audio chunks
        audio_bytes = b"".join(audio_chunks)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0  # Normalize to [-1, 1]

        # Transcribe with Whisper (suppress progress bar)
        # Redirect stderr to suppress tqdm progress bars
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        try:
            result = self.model.transcribe(
                audio_array, language="en", fp16=False, verbose=False
            )
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr

        transcription = result["text"].strip()
        return transcription

    def detect_wake_word(
        self, audio_stream: AudioStream, wake_word: str = WAKE_WORD
    ) -> bool:
        """
        Listen for the wake word in the audio stream.

        Args:
            audio_stream: AudioStream object providing audio data
            wake_word: Wake word to detect

        Returns:
            True if wake word detected
        """
        logger.debug("Listening for wake word...")

        # Collect audio for a short period
        audio_chunks = []
        wake_word_duration = 2.0  # Listen for 2 seconds at a time
        start_time = time.time()

        while time.time() - start_time < wake_word_duration:
            audio_data = audio_stream.read()
            energy = calculate_energy(audio_data)

            # Collect all audio, not just above threshold (Whisper handles noise well)
            audio_chunks.append(audio_data)

        if not audio_chunks:
            return False

        # Combine audio chunks
        audio_bytes = b"".join(audio_chunks)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0

        # Quick transcription with Whisper (suppress progress bar)
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        try:
            result = self.model.transcribe(
                audio_array, language="en", fp16=False, verbose=False
            )
            text = result["text"].lower().strip()

            # Normalize wake word for comparison
            wake_word_normalized = wake_word.lower().strip()

            if wake_word_normalized in text:
                # Play wake word detection sound
                wake_word_detected_sound()
                return True
        except Exception as e:
            logger.error(f"Error during wake word detection: {e}")
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr

        return False

    def detect_trigger_word(self, audio_stream: AudioStream) -> Optional[str]:
        """
        Listen for either wake word or paste word.

        Args:
            audio_stream: AudioStream object providing audio data

        Returns:
            "wake" if wake word detected, "paste" if paste word detected, None otherwise
        """
        logger.debug("Listening for trigger words...")

        # Collect audio for a short period
        audio_chunks = []
        trigger_word_duration = 2.0  # Listen for 2 seconds at a time
        start_time = time.time()

        while time.time() - start_time < trigger_word_duration:
            audio_data = audio_stream.read()
            audio_chunks.append(audio_data)

        if not audio_chunks:
            return None

        # Combine audio chunks
        audio_bytes = b"".join(audio_chunks)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0

        # Quick transcription with Whisper (suppress progress bar)
        old_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        try:
            result = self.model.transcribe(
                audio_array, language="en", fp16=False, verbose=False
            )
            text = result["text"].lower().strip()

            # Check for paste word first (higher priority)
            paste_word_normalized = PASTE_WORD.lower().strip()
            if paste_word_normalized in text:
                wake_word_detected_sound()
                return "paste"

            # Check for wake word
            wake_word_normalized = WAKE_WORD.lower().strip()
            if wake_word_normalized in text:
                wake_word_detected_sound()
                return "wake"

        except Exception as e:
            logger.error(f"Error during trigger word detection: {e}")
        finally:
            sys.stderr.close()
            sys.stderr = old_stderr

        return None

    def listen_continuous(self, audio_stream: AudioStream, keyboard_trigger: dict = None) -> tuple[Optional[str], str]:
        """
        Continuously listen for wake word, paste word, or keyboard trigger.

        Args:
            audio_stream: AudioStream object providing audio data
            keyboard_trigger: Dict with 'active' and 'recording' flags for keyboard control

        Returns:
            Tuple of (transcribed text or None, trigger type "wake", "paste", or "keyboard")
        """
        # Calibrate on first run
        self.calibrate_threshold(audio_stream)

        logger.info(f"Listening for trigger words: '{WAKE_WORD}' or '{PASTE_WORD}'")

        try:
            while True:
                # Check for keyboard trigger
                if keyboard_trigger and keyboard_trigger["active"]:
                    keyboard_trigger["active"] = False  # Reset flag
                    if keyboard_trigger["recording"]:
                        # Start recording
                        wake_word_detected_sound()
                        print(f"{Fore.GREEN}⌨️  Recording (keyboard)... Press Ctrl+Shift+Enter to stop{Style.RESET_ALL}")
                        transcription = self.transcribe_audio(audio_stream, keyboard_trigger)
                        keyboard_trigger["recording"] = False  # Reset after done
                        keyboard_trigger["stop_requested"] = False  # Reset stop flag
                        return (transcription, "keyboard")

                # Listen for voice triggers
                trigger = self.detect_trigger_word(audio_stream)
                if trigger == "wake":
                    print(f"{Fore.GREEN}🎤 Recording...{Style.RESET_ALL}")
                    transcription = self.transcribe_audio(audio_stream)
                    return (transcription, "wake")
                elif trigger == "paste":
                    return (None, "paste")
        except KeyboardInterrupt:
            return (None, "interrupt")
