"""Configuration for the speech-to-text application."""

import os
from pathlib import Path

# Wake word configuration
WAKE_WORD = "hello"

# Audio configuration
SAMPLE_RATE = 16000  # Whisper works with 16kHz
CHANNELS = 1  # Mono audio
CHUNK_SIZE = 8000  # Process audio in chunks

# Recording configuration
SILENCE_THRESHOLD = 5  # Energy threshold for silence detection (lowered for sensitive mics)
SILENCE_DURATION = 2.0  # Seconds of silence before stopping recording
MAX_RECORDING_DURATION = 30.0  # Maximum recording duration in seconds
MIN_RECORDING_DURATION = 0.5  # Minimum recording duration in seconds

# Auto-calibration
AUTO_CALIBRATE_THRESHOLD = True  # Automatically adjust threshold based on ambient noise

# Whisper model configuration
# Options: "tiny", "base", "small", "medium", "large"
# tiny: fastest, least accurate (~75MB)
# base: good balance (~150MB)
# small: better accuracy (~500MB)
WHISPER_MODEL = "base"  # Default model size

# Logging
LOG_LEVEL = os.getenv("STT_LOG_LEVEL", "INFO")
