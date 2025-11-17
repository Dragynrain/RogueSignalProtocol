"""Cross-platform utilities for detecting and handling platform-specific behavior.

This module centralizes all platform detection logic to avoid scattered sys.platform
checks throughout the codebase. Use these functions instead of direct platform checks.
"""

import ctypes
import logging
import sys


def is_windows() -> bool:
    """Check if running on Windows.

    Returns:
        True if Windows, False otherwise
    """
    return sys.platform == "win32"


def is_linux() -> bool:
    """Check if running on Linux.

    Returns:
        True if Linux, False otherwise
    """
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    """Check if running on macOS.

    Returns:
        True if macOS, False otherwise
    """
    return sys.platform == "darwin"


def get_platform_name() -> str:
    """Get human-readable platform name.

    Returns:
        Platform name: "Windows", "Linux", "macOS", or "Unknown"
    """
    if is_windows():
        return "Windows"
    if is_linux():
        return "Linux"
    if is_macos():
        return "macOS"
    return "Unknown"


def set_dpi_awareness() -> None:
    """Set DPI awareness on Windows for proper high-DPI scaling.

    This must be called BEFORE importing tcod to ensure proper scaling on high-DPI
    displays. On non-Windows platforms, this is a no-op.

    On Windows:
    - Tries PROCESS_PER_MONITOR_DPI_AWARE (Windows 8.1+)
    - Falls back to SetProcessDPIAware (Windows 7/8)
    - Silently succeeds if DPI awareness is unavailable

    The game will still run if this fails, but may be scaled by Windows.
    """
    if not is_windows():
        # DPI awareness is Windows-specific, nothing to do on other platforms
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        logging.debug("DPI awareness enabled (per-monitor)")
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()  # Fallback for Windows 7/8
            logging.debug("DPI awareness enabled (fallback)")
        except Exception:
            # DPI awareness unavailable - game will still run but may be scaled
            logging.debug("DPI awareness unavailable")
