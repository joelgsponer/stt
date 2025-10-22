"""Cross-platform clipboard operations."""

import logging
import platform
import subprocess
import time
from typing import Optional

logger = logging.getLogger(__name__)


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to the system clipboard.

    Works on macOS and Linux. Falls back to pyperclip if platform-specific
    commands fail.

    Args:
        text: Text to copy to clipboard

    Returns:
        True if successful, False otherwise
    """
    if not text:
        logger.warning("Empty text provided, nothing to copy")
        return False

    system = platform.system()
    logger.debug(f"Detected platform: {system}")

    try:
        if system == "Darwin":  # macOS
            return _copy_macos(text)
        elif system == "Linux":
            return _copy_linux(text)
        else:
            logger.warning(f"Unsupported platform: {system}, trying pyperclip")
            return _copy_pyperclip(text)
    except Exception as e:
        logger.error(f"Failed to copy to clipboard: {e}")
        # Try fallback to pyperclip
        try:
            return _copy_pyperclip(text)
        except Exception as fallback_error:
            logger.error(f"Fallback to pyperclip failed: {fallback_error}")
            return False


def _copy_macos(text: str) -> bool:
    """Copy text to clipboard on macOS using pbcopy."""
    process = subprocess.Popen(
        ["pbcopy"], stdin=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(text.encode("utf-8"))

    if process.returncode != 0:
        logger.error(f"pbcopy failed: {stderr.decode()}")
        return False

    logger.info("Text copied to clipboard (macOS)")
    return True


def _copy_linux(text: str) -> bool:
    """Copy text to clipboard on Linux using xclip or xsel."""
    # Try xclip first
    try:
        process = subprocess.Popen(
            ["xclip", "-selection", "clipboard"],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(text.encode("utf-8"))

        if process.returncode == 0:
            logger.info("Text copied to clipboard (Linux/xclip)")
            return True
        else:
            logger.warning(f"xclip failed: {stderr.decode()}")
    except FileNotFoundError:
        logger.debug("xclip not found, trying xsel")

    # Try xsel as fallback
    try:
        process = subprocess.Popen(
            ["xsel", "--clipboard", "--input"],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(text.encode("utf-8"))

        if process.returncode == 0:
            logger.info("Text copied to clipboard (Linux/xsel)")
            return True
        else:
            logger.error(f"xsel failed: {stderr.decode()}")
            return False
    except FileNotFoundError:
        logger.error("Neither xclip nor xsel found on Linux system")
        return False


def _copy_pyperclip(text: str) -> bool:
    """Fallback to pyperclip for clipboard operations."""
    try:
        import pyperclip

        pyperclip.copy(text)
        logger.info("Text copied to clipboard (pyperclip)")
        return True
    except ImportError:
        logger.error("pyperclip not installed")
        return False
    except Exception as e:
        logger.error(f"pyperclip failed: {e}")
        return False


def get_clipboard_content() -> Optional[str]:
    """
    Get text from the system clipboard.

    Returns:
        Clipboard text content or None if failed
    """
    system = platform.system()
    logger.debug(f"Getting clipboard content from platform: {system}")

    try:
        if system == "Darwin":  # macOS
            return _get_macos()
        elif system == "Linux":
            return _get_linux()
        else:
            logger.warning(f"Unsupported platform: {system}, trying pyperclip")
            return _get_pyperclip()
    except Exception as e:
        logger.error(f"Failed to get clipboard content: {e}")
        # Try fallback to pyperclip
        try:
            return _get_pyperclip()
        except Exception as fallback_error:
            logger.error(f"Fallback to pyperclip failed: {fallback_error}")
            return None


def _get_macos() -> Optional[str]:
    """Get clipboard content on macOS using pbpaste."""
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Got clipboard content (macOS)")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"pbpaste failed: {e.stderr}")
        return None
    except FileNotFoundError:
        logger.error("pbpaste not found")
        return None


def _get_linux() -> Optional[str]:
    """Get clipboard content on Linux using xclip or xsel."""
    # Try xclip first
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Got clipboard content (Linux/xclip)")
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("xclip failed, trying xsel")

    # Try xsel as fallback
    try:
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Got clipboard content (Linux/xsel)")
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Neither xclip nor xsel could get clipboard content")
        return None


def _get_pyperclip() -> Optional[str]:
    """Fallback to pyperclip for getting clipboard content."""
    try:
        import pyperclip

        content = pyperclip.paste()
        logger.info("Got clipboard content (pyperclip)")
        return content
    except ImportError:
        logger.error("pyperclip not installed")
        return None
    except Exception as e:
        logger.error(f"pyperclip failed: {e}")
        return None


def paste_at_cursor() -> bool:
    """
    Paste clipboard content at the current cursor position.

    Uses keyboard automation to simulate Cmd+V (macOS) or Ctrl+V (Linux/Windows).

    Returns:
        True if successful, False otherwise
    """
    system = platform.system()
    logger.debug(f"Pasting at cursor on platform: {system}")

    if system == "Darwin":  # macOS
        # Try AppleScript first as it's more reliable on macOS
        try:
            # Use keystroke command which works better with accessibility
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                logger.info("Pasted using AppleScript")
                return True
            else:
                logger.warning(f"AppleScript paste failed: {result.stderr}")
        except Exception as e:
            logger.warning(f"AppleScript method failed: {e}")

    # Try pyautogui as fallback or for non-macOS
    try:
        import pyautogui

        # Longer delay to ensure focus
        time.sleep(0.2)

        if system == "Darwin":  # macOS
            # Press and hold Command, press v, release both
            pyautogui.keyDown('command')
            time.sleep(0.05)
            pyautogui.press('v')
            time.sleep(0.05)
            pyautogui.keyUp('command')
        else:  # Linux/Windows
            # Press and hold Ctrl, press v, release both
            pyautogui.keyDown('ctrl')
            time.sleep(0.05)
            pyautogui.press('v')
            time.sleep(0.05)
            pyautogui.keyUp('ctrl')

        logger.info("Pasted clipboard content at cursor using pyautogui")
        return True
    except ImportError:
        logger.error("pyautogui not installed")
        return False
    except Exception as e:
        logger.error(f"Failed to paste at cursor: {e}")
        return False
