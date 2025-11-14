"""File path resolution system with portable/AppData fallback for Windows.

This module handles the determination of where user data (saves, logs, metrics)
should be stored, with the following priority:

1. Portable mode: Try to use directories relative to the executable/script
2. AppData mode: Fall back to %LOCALAPPDATA%\\RogueSignalProtocol if portable fails
3. Fatal error: If both fail, display error and exit

This ensures the game works in both portable installations (USB drives, user folders)
and system installations (C:\\Program Files).
"""

import ctypes
import os
import sys
from pathlib import Path

# Module-level cache for the data directory
_data_directory: Path | None = None
_is_portable_mode: bool | None = None


def get_application_directory() -> Path:
    """Get the directory containing the application executable or script.

    Returns:
        Path: Absolute path to application directory
    """
    if getattr(sys, "frozen", False):
        # Running as compiled exe
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


def _test_write_permission(directory: Path) -> bool:
    """Test if we can write to a directory by creating/deleting a test file.

    Args:
        directory: Directory to test

    Returns:
        True if writable, False otherwise
    """
    try:
        # Ensure directory exists
        directory.mkdir(parents=True, exist_ok=True)

        # Try to create and delete a test file
        test_file = directory / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except (OSError, PermissionError):
        return False


def _get_appdata_directory() -> Path:
    """Get the Windows AppData\\Local path for this application.

    Returns:
        Path: %LOCALAPPDATA%\\RogueSignalProtocol
    """
    appdata = os.getenv("LOCALAPPDATA")
    if not appdata:
        # Fallback if LOCALAPPDATA not set (shouldn't happen on Windows 7+)
        appdata = os.path.expanduser("~\\AppData\\Local")

    return Path(appdata) / "RogueSignalProtocol"


def initialize_data_directories() -> bool:
    """Initialize and test data directories with fallback logic.

    This should be called ONCE at application startup, before logging or any
    file operations. It determines the base directory for all user data.

    Priority order:
    1. Try portable mode (./saves/, ./logs/, ./metrics/ relative to executable)
    2. Try AppData mode (%LOCALAPPDATA%\\RogueSignalProtocol\\...)
    3. If both fail, return False (caller should display error and exit)

    Returns:
        True if successful, False if all options failed
    """
    global _data_directory, _is_portable_mode

    # Try portable mode first
    portable_base = get_application_directory()
    portable_test_dir = portable_base / "logs"

    if _test_write_permission(portable_test_dir):
        _data_directory = portable_base
        _is_portable_mode = True
        return True

    # Portable mode failed, try AppData
    appdata_base = _get_appdata_directory()
    appdata_test_dir = appdata_base / "logs"

    if _test_write_permission(appdata_test_dir):
        _data_directory = appdata_base
        _is_portable_mode = False
        return True

    # Both failed
    return False


def get_data_directory() -> Path:
    """Get the base directory for all user data (saves, logs, metrics).

    Must call initialize_data_directories() first.

    Returns:
        Path: Base directory for user data

    Raises:
        RuntimeError: If initialize_data_directories() was not called
    """
    global _data_directory

    if _data_directory is None:
        raise RuntimeError(
            "get_data_directory() called before initialize_data_directories(). "
            "Call initialize_data_directories() at application startup."
        )

    return _data_directory


def is_portable_mode() -> bool:
    """Check if running in portable mode (vs AppData mode).

    Returns:
        True if portable, False if using AppData

    Raises:
        RuntimeError: If initialize_data_directories() was not called
    """
    global _is_portable_mode

    if _is_portable_mode is None:
        raise RuntimeError(
            "is_portable_mode() called before initialize_data_directories(). "
            "Call initialize_data_directories() at application startup."
        )

    return _is_portable_mode


def show_fatal_error_and_exit(message: str, title: str = "Rogue Signal Protocol - Error") -> None:
    """Display a fatal error message and exit the application.

    Uses Windows MessageBox API for native dialog (works even without TCOD initialized).

    Args:
        message: Error message to display
        title: Dialog title
    """
    # Display Windows MessageBox
    try:
        # MB_OK | MB_ICONERROR | MB_SYSTEMMODAL
        MB_OK = 0x00000000
        MB_ICONERROR = 0x00000010
        MB_SYSTEMMODAL = 0x00001000

        ctypes.windll.user32.MessageBoxW(
            0, message, title, MB_OK | MB_ICONERROR | MB_SYSTEMMODAL  # No parent window
        )
    except Exception:
        # Fallback to console print if MessageBox fails
        print(f"\n{'=' * 60}")
        print(f"FATAL ERROR: {title}")
        print(f"{'=' * 60}")
        print(f"\n{message}\n")
        print(f"{'=' * 60}\n")

    sys.exit(1)


def get_mode_description() -> str:
    """Get a human-readable description of the current mode.

    Returns:
        String describing portable or AppData mode with path
    """
    if is_portable_mode():
        return f"Portable mode: {get_data_directory()}"
    else:
        return f"AppData mode: {get_data_directory()}"
