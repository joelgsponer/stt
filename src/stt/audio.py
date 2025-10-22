"""Audio capture and processing utilities."""

import logging
import queue
import threading
from typing import Iterator

import numpy as np
import sounddevice as sd

from .config import CHANNELS, CHUNK_SIZE, SAMPLE_RATE

logger = logging.getLogger(__name__)


class AudioStream:
    """Manages audio input stream from microphone."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        chunk_size: int = CHUNK_SIZE,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.audio_queue: queue.Queue = queue.Queue()
        self.stream = None
        self._stop_event = threading.Event()

    def _callback(self, indata, frames, time, status):
        """Callback for sounddevice stream."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        # Convert to bytes and put in queue
        self.audio_queue.put(bytes(indata))

    def start(self):
        """Start the audio stream."""
        logger.info(
            f"Starting audio stream (rate={self.sample_rate}, "
            f"channels={self.channels}, chunk={self.chunk_size})"
        )
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.chunk_size,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        """Stop the audio stream."""
        if self.stream:
            logger.info("Stopping audio stream")
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def read(self) -> bytes:
        """Read audio data from the queue."""
        return self.audio_queue.get()

    def iter_audio(self) -> Iterator[bytes]:
        """Iterate over audio chunks."""
        while not self._stop_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                yield chunk
            except queue.Empty:
                continue

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def calculate_energy(audio_data: bytes) -> float:
    """Calculate the energy level of audio data."""
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    return float(np.sqrt(np.mean(audio_array**2)))


def is_silence(audio_data: bytes, threshold: float = 500) -> bool:
    """Check if audio data is below the silence threshold."""
    return calculate_energy(audio_data) < threshold
