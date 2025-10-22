"""Main entry point for the speech-to-text application."""

import logging
import os
import sys
import threading

from colorama import Fore, Style, init
from pynput import keyboard

from .audio import AudioStream
from .audio_feedback import clipboard_ready_sound_async, wake_word_detected_sound
from .clipboard import copy_to_clipboard, get_clipboard_content, paste_at_cursor
from .config import LOG_LEVEL, PASTE_WORD, WAKE_WORD, WHISPER_MODEL
from .transcribe import SpeechRecognizer

# Initialize colorama
init(autoreset=True)

# Global flag for keyboard trigger
keyboard_trigger = {"active": False, "recording": False}


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


def on_press(key):
    """Handle keyboard press events."""
    try:
        if key == keyboard.Key.enter:
            if not keyboard_trigger["recording"]:
                # Start recording
                keyboard_trigger["active"] = True
                keyboard_trigger["recording"] = True
            else:
                # Stop recording
                keyboard_trigger["active"] = True
                keyboard_trigger["recording"] = False
    except AttributeError:
        pass


def run():
    """Main application loop."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Clear screen
    os.system('clear' if os.name != 'nt' else 'cls')

    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}🎤  Speech-to-Text with Wake Word Detection")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Wake word:{Style.RESET_ALL} '{Fore.GREEN}{WAKE_WORD}{Style.RESET_ALL}' (transcribe)")
    print(f"{Fore.YELLOW}Paste word:{Style.RESET_ALL} '{Fore.GREEN}{PASTE_WORD}{Style.RESET_ALL}' (paste clipboard)")
    print(f"{Fore.YELLOW}Keyboard:{Style.RESET_ALL} {Fore.GREEN}Enter{Style.RESET_ALL} (manual transcribe)")
    print(f"{Fore.YELLOW}Model:{Style.RESET_ALL} {Fore.GREEN}{WHISPER_MODEL}{Style.RESET_ALL}")
    print(f"\n{Fore.MAGENTA}Press Ctrl+C to exit{Style.RESET_ALL}\n")

    try:
        # Start keyboard listener in background
        listener = keyboard.Listener(on_press=on_press)
        listener.start()

        # Initialize components (will download model on first run)
        print(f"{Fore.BLUE}Loading model...{Style.RESET_ALL}", end="", flush=True)
        recognizer = SpeechRecognizer()
        print(f"\r{Fore.GREEN}✓ Model loaded{Style.RESET_ALL}                    ")

        # Start audio stream
        with AudioStream() as audio_stream:
            print(f"\n{Fore.CYAN}👂 Listening for '{Fore.GREEN}{WAKE_WORD}{Fore.CYAN}' or '{Fore.GREEN}{PASTE_WORD}{Fore.CYAN}' (or press Enter)...{Style.RESET_ALL}\n")

            while True:
                # Listen for wake word, paste word, or keyboard trigger
                result, trigger = recognizer.listen_continuous(audio_stream, keyboard_trigger)

                if trigger == "interrupt":
                    # User interrupted
                    break
                elif trigger == "paste":
                    # Paste clipboard content
                    clipboard_content = get_clipboard_content()
                    if clipboard_content:
                        print(f"\n{Fore.BLUE}📋 Pasting clipboard content...{Style.RESET_ALL}")
                        if paste_at_cursor():
                            print(f"{Fore.GREEN}✓ Pasted at cursor{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}✗ Failed to paste{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠ Clipboard is empty{Style.RESET_ALL}")
                elif trigger in ["wake", "keyboard"]:
                    # Transcribe speech (from voice or keyboard trigger)
                    if result:
                        print(f"\n{Fore.WHITE}📝 {Style.BRIGHT}{result}{Style.RESET_ALL}")

                        # Copy to clipboard
                        if copy_to_clipboard(result):
                            print(f"{Fore.GREEN}✓ Copied to clipboard{Style.RESET_ALL}")
                            # Play success sound
                            clipboard_ready_sound_async()
                        else:
                            print(f"{Fore.RED}✗ Failed to copy to clipboard{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠ No speech detected{Style.RESET_ALL}")

                print(f"\n{Fore.CYAN}👂 Listening for '{Fore.GREEN}{WAKE_WORD}{Fore.CYAN}' or '{Fore.GREEN}{PASTE_WORD}{Fore.CYAN}' (or press Enter)...{Style.RESET_ALL}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Fore.CYAN}👋 Goodbye!{Style.RESET_ALL}")
        if 'listener' in locals():
            listener.stop()
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        if 'listener' in locals():
            listener.stop()
        sys.exit(1)


if __name__ == "__main__":
    run()
