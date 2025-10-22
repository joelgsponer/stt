"""Cross-platform clipboard operations."""

import logging
import platform
import subprocess
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
