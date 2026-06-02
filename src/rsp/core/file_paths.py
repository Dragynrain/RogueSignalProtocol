"""Cross-platform file path resolution with portable/system fallback.

This module handles the determination of where user data (saves, logs, metrics)
should be stored, with the following priority:

1. Portable mode: Try to use directories relative to the executable/script
2. System mode: Fall back to platform-appropriate user data directory:
   - Windows: %LOCALAPPDATA%\\RogueSignalProtocol
   - Linux: ~/.local/share/RogueSignalProtocol
3. Fatal error: If both fail, display error and exit

This ensures the game works in both portable installations (USB drives, user folders)
and system installations (C:\\Program Files, /usr/local/games, etc.).
"""

import logging
import sys
from pathlib import Path

from platformdirs import user_data_dir

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
        # Running as script - use current working directory (project root)
        return Path.cwd()


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
    except OSError:
        # Catches OSError and its subclasses (including PermissionError)
        return False


def _get_system_data_directory() -> Path:
    """Get the system-specific user data directory for this application.

    Uses platformdirs for cross-platform path resolution:
    - Windows: %LOCALAPPDATA%\\RogueSignalProtocol
    - Linux: ~/.local/share/RogueSignalProtocol

    Note: appauthor=False maintains backward compatibility with existing
    Windows saves (avoids adding author subdirectory).

    Returns:
        Path: Platform-appropriate user data directory
    """
    return Path(user_data_dir("RogueSignalProtocol", appauthor=False))


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

    # Portable mode failed, try system data directory
    system_base = _get_system_data_directory()
    system_test_dir = system_base / "logs"

    if _test_write_permission(system_test_dir):
        _data_directory = system_base
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

    Uses tcod for cross-platform error display (a visible window, which matters on
    Windows where the console is hidden). Falls back to console if tcod fails.

    Args:
        message: Error message to display
        title: Dialog title
    """
    # Try a windowed error screen via tcod (no audio/extra deps needed)
    try:
        import tcod.console
        import tcod.context
        import tcod.event

        width, height = 72, 22
        max_width = width - 4
        console = tcod.console.Console(width, height)

        # Word-wrap the message (honoring explicit newlines) to the console width.
        lines = []
        for paragraph in message.split("\n"):
            if not paragraph:
                lines.append("")
                continue
            current_line = ""
            for word in paragraph.split():
                test_line = f"{current_line} {word}".strip()
                if len(test_line) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

        text_color = (255, 100, 100)
        instruction_color = (180, 180, 180)

        with tcod.context.new(columns=width, rows=height, title=title) as context:
            running = True
            while running:
                console.clear()
                console.print(2, 1, title[:max_width], fg=text_color)
                y_offset = 3
                for line in lines:
                    if y_offset >= height - 2:
                        break
                    console.print(2, y_offset, line, fg=text_color)
                    y_offset += 1
                console.print(
                    2, height - 2, "Press any key or close the window to exit",
                    fg=instruction_color,
                )
                context.present(console)

                for event in tcod.event.wait():
                    if isinstance(
                        event,
                        (tcod.event.Quit, tcod.event.KeyDown, tcod.event.MouseButtonDown),
                    ):
                        running = False
                        break

    except Exception as e:
        # Fallback to console print if the windowed dialog fails
        logging.warning(f"Windowed error dialog failed: {e}, falling back to console")
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
