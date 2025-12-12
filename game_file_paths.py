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

    Uses pygame for cross-platform error display. Falls back to console if pygame fails.

    Args:
        message: Error message to display
        title: Dialog title
    """
    # Try pygame-based error screen (cross-platform)
    try:
        import pygame

        pygame.init()
        screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption(title)

        # Colors
        bg_color = (40, 40, 40)
        text_color = (255, 100, 100)
        instruction_color = (180, 180, 180)

        # Fonts
        try:
            title_font = pygame.font.Font(None, 36)
            message_font = pygame.font.Font(None, 24)
        except Exception:
            title_font = pygame.font.SysFont("arial", 28)
            message_font = pygame.font.SysFont("arial", 18)

        # Render title
        title_surface = title_font.render(title, True, text_color)

        # Word-wrap message into lines
        words = message.split()
        lines = []
        current_line = ""
        max_width = 580

        for word in words:
            test_line = current_line + " " + word if current_line else word
            test_surface = message_font.render(test_line, True, text_color)
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Render instruction
        instruction = "Press any key or click to exit"
        instruction_surface = message_font.render(instruction, True, instruction_color)

        # Event loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    running = False

            # Draw
            screen.fill(bg_color)
            screen.blit(title_surface, (30, 30))

            y_offset = 80
            for line in lines:
                line_surface = message_font.render(line, True, text_color)
                screen.blit(line_surface, (30, y_offset))
                y_offset += 28

            screen.blit(instruction_surface, (30, 440))
            pygame.display.flip()

        pygame.quit()

    except Exception:
        # Fallback to console print if pygame fails
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
