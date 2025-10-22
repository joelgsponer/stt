"""Audio feedback using system beeps and tones."""

import logging
import platform
import subprocess
import threading

import numpy as np
import sounddevice as sd

from .config import SAMPLE_RATE

logger = logging.getLogger(__name__)


def play_beep(frequency: int = 800, duration: float = 0.15, volume: float = 0.3):
    """
    Play a simple beep tone.

    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        volume: Volume (0.0 to 1.0)
    """
    try:
        # Generate sine wave
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        tone = np.sin(frequency * 2 * np.pi * t) * volume

        # Play the tone
        sd.play(tone, SAMPLE_RATE)
        sd.wait()
    except Exception as e:
        logger.error(f"Failed to play beep: {e}")
        # Fallback to system beep
        _system_beep()


def play_beep_async(frequency: int = 800, duration: float = 0.15, volume: float = 0.3):
    """Play a beep without blocking."""
    thread = threading.Thread(
        target=play_beep, args=(frequency, duration, volume), daemon=True
    )
    thread.start()


def _system_beep():
    """Fallback to system beep."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", "/System/Library/Sounds/Tink.aiff"],
                         check=False, capture_output=True)
        elif system == "Linux":
            subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
                         check=False, capture_output=True)
    except Exception as e:
        logger.debug(f"System beep failed: {e}")


def wake_word_detected_sound():
    """Play a rising tone when wake word is detected."""
    try:
        # Two-tone ascending beep
        play_beep(frequency=600, duration=0.1, volume=0.3)
        play_beep(frequency=800, duration=0.1, volume=0.3)
    except Exception as e:
        logger.error(f"Failed to play wake word sound: {e}")


def clipboard_ready_sound():
    """Play a confirmation sound when text is copied to clipboard."""
    try:
        # Three quick beeps
        for freq in [1000, 1200, 1400]:
            t = np.linspace(0, 0.08, int(SAMPLE_RATE * 0.08), False)
            tone = np.sin(freq * 2 * np.pi * t) * 0.25
            sd.play(tone, SAMPLE_RATE)
            sd.wait()
    except Exception as e:
        logger.error(f"Failed to play clipboard sound: {e}")


def clipboard_ready_sound_async():
    """Play clipboard ready sound without blocking."""
    thread = threading.Thread(target=clipboard_ready_sound, daemon=True)
    thread.start()
