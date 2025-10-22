# STT - Voice-Activated Speech-to-Text

A command-line tool that listens for a wake word (e.g., "hey james") and then transcribes your speech to the clipboard. Works offline using [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition.

## Features

- **Wake word detection**: Continuously listens for your custom wake word
- **Offline speech recognition**: Uses OpenAI Whisper models, no internet required after initial download
- **Cross-platform clipboard**: Automatically copies transcriptions to clipboard (macOS & Linux)
- **High accuracy**: Whisper provides excellent transcription quality
- **Customizable**: Easy configuration for wake words and audio parameters

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Microphone access
- ~150MB disk space for the default Whisper model

### Platform-Specific Requirements

**macOS:**
- Microphone permissions (system will prompt on first run)
- `pbcopy` (included by default)

**Linux:**
- `xclip` or `xsel` for clipboard operations:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install xclip
  # or
  sudo apt-get install xsel

  # Fedora
  sudo dnf install xclip
  ```
- PortAudio (usually required for sounddevice):
  ```bash
  # Ubuntu/Debian
  sudo apt-get install portaudio19-dev

  # Fedora
  sudo dnf install portaudio-devel
  ```

## Installation

1. **Clone or download this repository**

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

   This will install all required packages including PyTorch and OpenAI Whisper.

## Usage

### Basic Usage

Run the program:
```bash
uv run stt
```

**First run**: The program will automatically download the Whisper model (~150MB for the default "base" model). This only happens once.

The program will:
1. Start listening for the wake word ("hey james" by default)
2. When detected, it will notify and start recording
3. Speak your text
4. After you stop speaking (2 seconds of silence), it will transcribe and copy to clipboard
5. Return to listening for the wake word

Press `Ctrl+C` to exit.

### Installing as a Command

To install the tool globally:
```bash
uv pip install -e .
```

Then you can run it from anywhere:
```bash
stt
```

## Configuration

Edit `src/stt/config.py` to customize:

```python
# Wake word
WAKE_WORD = "hey james"  # Change to your preferred wake word

# Audio settings
SAMPLE_RATE = 16000      # Whisper works with 16kHz
SILENCE_THRESHOLD = 500  # Adjust based on your microphone
SILENCE_DURATION = 2.0   # Seconds of silence before stopping

# Whisper model size
WHISPER_MODEL = "base"   # Options: "tiny", "base", "small", "medium", "large"
```

### Whisper Model Options

Choose based on your needs:

- **tiny** (~75MB): Fastest, least accurate - good for quick commands
- **base** (~150MB): **Default** - good balance of speed and accuracy
- **small** (~500MB): Better accuracy, slower
- **medium** (~1.5GB): High accuracy, requires more resources
- **large** (~3GB): Best accuracy, slowest

## Troubleshooting

### Microphone not working
- Check microphone permissions in system settings
- Verify your default input device is set correctly
- Try adjusting `SILENCE_THRESHOLD` in config.py

### Wake word not detected
- Speak clearly and at normal volume
- Try adjusting `SILENCE_THRESHOLD`
- The wake word detection processes 2-second windows of audio
- Lower background noise improves detection

### Linux clipboard not working
- Install `xclip` or `xsel` (see Platform-Specific Requirements)
- Check X11 display is available

### Slow performance
- Use a smaller Whisper model (e.g., "tiny" or "base")
- Ensure you're not running other resource-intensive applications
- On macOS with Apple Silicon, PyTorch should automatically use the GPU

### Model download fails
- Check your internet connection
- Models are downloaded from Hugging Face on first run
- You can manually download models and place them in `~/.cache/whisper/`

## Project Structure

```
stt/
├── src/
│   └── stt/
│       ├── __init__.py         # Package initialization
│       ├── main.py             # Main entry point
│       ├── config.py           # Configuration settings
│       ├── audio.py            # Audio capture
│       ├── transcribe.py       # Speech recognition with Whisper
│       └── clipboard.py        # Clipboard operations
├── pyproject.toml             # Project configuration
└── README.md                  # This file
```

## How It Works

1. **Audio Capture**: Uses `sounddevice` to capture audio from your microphone in real-time
2. **Wake Word Detection**: Continuously processes 2-second audio windows with Whisper, looking for your wake word
3. **Speech Recognition**: Once activated, records until silence is detected, then transcribes with Whisper
4. **Clipboard**: Uses platform-specific commands (pbcopy on macOS, xclip/xsel on Linux) to copy text

## Tips

- Use a 2-3 word wake phrase for better detection
- Speak naturally - no need to pause between words
- If transcription quality is poor, try a larger Whisper model
- Adjust `SILENCE_THRESHOLD` if it's too sensitive or not sensitive enough
- For faster wake word detection, consider lowering the wake word duration in `transcribe.py`

## Performance Notes

- **Wake word detection** uses Whisper on 2-second audio chunks, so there's a ~2-second polling interval
- **Transcription** is very accurate but may take a few seconds depending on model size and hardware
- **Memory usage** varies by model:
  - tiny/base: ~1-2GB RAM
  - small: ~2-4GB RAM
  - medium/large: 4GB+ RAM

## License

This project uses:
- [OpenAI Whisper](https://github.com/openai/whisper) - MIT License
- [PyTorch](https://pytorch.org/) - BSD License
- [sounddevice](https://github.com/spatialaudio/python-sounddevice) - MIT License
- [pyperclip](https://github.com/asweigart/pyperclip) - BSD License

## Contributing

Feel free to open issues or submit pull requests for improvements!
