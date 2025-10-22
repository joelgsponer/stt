# STT - Voice-Activated Speech-to-Text

A command-line tool that listens for trigger words to either transcribe speech to clipboard or paste clipboard content at your cursor. Works offline using [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition.

## Features

- **Multiple trigger methods**:
  - Wake word ("hey") - Transcribe speech to clipboard
  - Paste word ("engage") - Paste clipboard at cursor position
  - Keyboard (Ctrl+Shift+Enter) - Manual transcription trigger
- **Offline speech recognition**: Uses OpenAI Whisper models, no internet required after initial download
- **Cross-platform clipboard**: Automatically copies transcriptions to clipboard (macOS & Linux)
- **Keyboard automation**: Seamlessly paste text at cursor position
- **High accuracy**: Whisper provides excellent transcription quality
- **Customizable**: Easy configuration for trigger words and audio parameters

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
1. Listen for trigger words ("hey" or "engage" by default) or keyboard input (Ctrl+Shift+Enter)
2. When "hey" is detected or Ctrl+Shift+Enter is pressed:
   - Start recording your speech
   - After 2 seconds of silence, transcribe and copy to clipboard
3. When "engage" is detected:
   - Paste clipboard content at your current cursor position
4. Return to listening for triggers

**Keyboard Control**: Press Ctrl+Shift+Enter to start recording. Press it again to stop immediately, or recording will automatically stop after 2 seconds of silence.

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
# Trigger words
WAKE_WORD = "hey"        # Transcribe speech to clipboard
PASTE_WORD = "engage"    # Paste clipboard at cursor

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

### Trigger words not detected
- Speak clearly and at normal volume
- Try adjusting `SILENCE_THRESHOLD`
- Trigger word detection processes 2-second windows of audio
- Lower background noise improves detection
- Avoid common words that appear in normal speech (e.g., "hey")

### Paste not working
- Ensure the application you want to paste into has focus
- On macOS, you may need to grant accessibility permissions
- Check that clipboard contains text content

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
2. **Trigger Word Detection**: Continuously processes 2-second audio windows with Whisper, listening for wake word or paste word
3. **Speech Recognition**: When wake word detected, records until silence is detected, then transcribes with Whisper
4. **Clipboard Operations**:
   - Copy: Uses platform-specific commands (pbcopy on macOS, xclip/xsel on Linux)
   - Paste: Uses `pyautogui` to simulate keyboard shortcuts (Cmd+V or Ctrl+V)

## Tips

- **For transcription**:
  - Voice: Say the wake word ("hey"), wait for the recording indicator, then speak your text
  - Keyboard: Press Ctrl+Shift+Enter to start, press again to stop (or wait for auto-stop after silence)
- **For pasting**: Say the paste word ("engage") while focused on the target application
- **Keyboard method** is useful when you want immediate control without voice activation
- Use unique trigger words that don't appear in normal speech
- Speak naturally - no need to pause between words
- If transcription quality is poor, try a larger Whisper model
- Adjust `SILENCE_THRESHOLD` if it's too sensitive or not sensitive enough

## Performance Notes

- **Trigger word detection** uses Whisper on 2-second audio chunks, so there's a ~2-second polling interval
- **Transcription** is very accurate but may take a few seconds depending on model size and hardware
- **Paste operation** is nearly instantaneous once triggered
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
