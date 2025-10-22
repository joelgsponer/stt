"""Main entry point for the speech-to-text application."""

import logging
import os
import sys

from colorama import Fore, Style, init

from .audio import AudioStream
from .audio_feedback import clipboard_ready_sound_async
from .clipboard import copy_to_clipboard
from .config import LOG_LEVEL, WAKE_WORD, WHISPER_MODEL
from .transcribe import SpeechRecognizer

# Initialize colorama
init(autoreset=True)


def setup_logging():
    """Configure logging for the application - suppress most output."""
    # Only show warnings and errors
    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
    )
    # Silence verbose libraries
    logging.getLogger("whisper").setLevel(logging.ERROR)
    logging.getLogger("numba").setLevel(logging.ERROR)
    logging.getLogger("openai_whisper").setLevel(logging.ERROR)


def run():
    """Main application loop."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Clear screen
    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}🎤  Speech-to-Text with Wake Word Detection")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Wake word:{Style.RESET_ALL} '{Fore.GREEN}{WAKE_WORD}{Style.RESET_ALL}'")
    print(f"{Fore.YELLOW}Model:{Style.RESET_ALL} {Fore.GREEN}{WHISPER_MODEL}{Style.RESET_ALL}")
    print(f"\n{Fore.MAGENTA}Press Ctrl+C to exit{Style.RESET_ALL}\n")

    try:
        # Initialize components (will download model on first run)
        print(f"{Fore.BLUE}Loading model...{Style.RESET_ALL}", end="", flush=True)
        recognizer = SpeechRecognizer()
        print(f"\r{Fore.GREEN}✓ Model loaded{Style.RESET_ALL}                    ")

        # Start audio stream
        with AudioStream() as audio_stream:
            print(f"\n{Fore.CYAN}👂 Listening for '{Fore.GREEN}{WAKE_WORD}{Fore.CYAN}'...{Style.RESET_ALL}\n")

            while True:
                # Listen for wake word and transcribe
                transcription = recognizer.listen_continuous(audio_stream)

                if transcription is None:
                    # User interrupted
                    break

                if transcription:
                    print(f"\n{Fore.WHITE}📝 {Style.BRIGHT}{transcription}{Style.RESET_ALL}")

                    # Copy to clipboard
                    if copy_to_clipboard(transcription):
                        print(f"{Fore.GREEN}✓ Copied to clipboard{Style.RESET_ALL}")
                        # Play success sound
                        clipboard_ready_sound_async()
                    else:
                        print(f"{Fore.RED}✗ Failed to copy to clipboard{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠ No speech detected{Style.RESET_ALL}")

                print(f"\n{Fore.CYAN}👂 Listening for '{Fore.GREEN}{WAKE_WORD}{Fore.CYAN}'...{Style.RESET_ALL}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    run()
