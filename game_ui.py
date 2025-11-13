#!/usr/bin/env python3
"""
Rogue Signal Protocol - UI Utilities

Core UI utility functions and helper classes.
Provides safe console rendering, window management, and universal input handling.
Extracted from RogueSignalProtocol.py for better organization.
"""

import time

import tcod.event

# Import game modules


def render_char_safe(console, x, y, char, fg=None, bg=None) -> None:
    """
    Render character to console with color validation and error handling.

    Validates color tuples, converts to RGB format, and uses TCOD print.
    Raises ValueError on invalid colors (strings, out-of-range values).

    Args:
        console: TCOD console to render to
        x: X coordinate
        y: Y coordinate
        char: Character or string to render
        fg: Foreground color as RGB tuple (optional)
        bg: Background color as RGB tuple (optional)

    Raises:
        ValueError: If color format is invalid
    """

    def validate_color(color):
        """Validate and convert color to RGB tuple."""
        if color is None:
            return None
        if isinstance(color, str):
            raise ValueError(f"String color '{color}' not allowed - use RGB tuple")
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            r, g, b = int(color[0]), int(color[1]), int(color[2])
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                raise ValueError(f"Color values must be 0-255: {color}")
            return (r, g, b)
        raise ValueError(f"Invalid color format: {color}")

    # Validate colors and let failures bubble up
    fg = validate_color(fg)
    bg = validate_color(bg)

    # Render with validated colors using TCOD
    try:
        if fg is not None and bg is not None:
            console.print(x, y, char, fg=fg, bg=bg)
        elif fg is not None:
            console.print(x, y, char, fg=fg)
        elif bg is not None:
            console.print(x, y, char, bg=bg)
        else:
            console.print(x, y, char)
    except Exception as e:
        # Log rendering failures (especially for Unicode characters)
        import logging

        logging.error(
            f"render_char_safe failed at ({x}, {y}): char={repr(char)}, fg={fg}, bg={bg}, error={e}"
        )
        # Try fallback with simple ASCII
        try:
            console.print(
                x,
                y,
                "?",
                fg=(255, 255, 0) if fg is None else fg,
                bg=(0, 0, 0) if bg is None else bg,
            )
        except Exception:
            pass  # Give up if even fallback fails


class WindowManager:
    """
    Manages dynamic window sizing and pixel dimension calculations.

    Provides cached window dimensions to avoid excessive SDL calls.
    Calculates background image rectangles with aspect ratio preservation.
    Constrains backgrounds to left 60% of window for menu separation.

    Key attributes:
        context: TCOD context with SDL window access
        _cached_dimensions: Cached window size (refreshed every 0.1s)
    """

    def __init__(self, context):
        self.context = context
        self._cached_dimensions = None
        self._last_check_time = 0

    def get_window_pixel_dimensions(self):
        """
        Get current window pixel dimensions with caching.

        Caches dimensions for 0.1 seconds to avoid excessive SDL calls.
        Falls back to conservative estimate if window unavailable.

        Returns:
            Tuple of (width, height) in pixels
        """
        # Cache dimensions for 0.1 seconds to avoid excessive SDL calls
        current_time = time.time()
        if self._cached_dimensions is None or current_time - self._last_check_time > 0.1:

            # Get actual window size via SDL
            window = self.context.sdl_window
            if window:
                width, height = window.size
                self._cached_dimensions = (width, height)
                self._last_check_time = current_time
            else:
                # Fallback to estimated dimensions
                self._cached_dimensions = (800, 600)  # Conservative estimate

        return self._cached_dimensions

    def calculate_background_rect(self, image_size):
        """
        Calculate rectangle for background image constrained to left 60% of window.

        Maintains aspect ratio while fitting background in left portion only.
        This creates separation between background graphics and right-side menus.

        Args:
            image_size: Tuple of (image_width, image_height) in pixels

        Returns:
            Tuple of (x, y, width, height) for SDL destination rectangle
        """
        window_width, window_height = self.get_window_pixel_dimensions()
        img_width, img_height = image_size

        # CONSTRAINT: Limit graphics to left 60% of screen width for true separation
        graphics_area_width = int(window_width * 0.6)  # Graphics get 60% of width

        # Calculate scale to fit within LEFT AREA ONLY (not full screen)
        scale_x = graphics_area_width / img_width  # Scale to fit in left area width
        scale_y = window_height / img_height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit entirely in left area

        # Position within left area only
        scaled_width = int(img_width * scale)
        scaled_height = int(img_height * scale)
        x = 0  # Left-align within graphics area
        y = (window_height - scaled_height) // 2  # Center vertically

        return (x, y, scaled_width, scaled_height)


class UniversalInputHandler:
    """
    Universal input handler for all menu and UI screens.

    Provides reusable input handling methods for common UI patterns:
    - List navigation (up/down with optional wrap-around)
    - Dialog navigation (toggle between options)
    - Value adjustment (left/right for settings)
    - Key checking (confirm, escape, any key)

    Defines common key sets as class constants for consistency.
    All methods are static as this is a pure utility class.
    """

    # Define common key sets
    NAVIGATION_UP = (tcod.event.KeySym.UP, tcod.event.KeySym.W, tcod.event.KeySym.KP_8)
    NAVIGATION_DOWN = (tcod.event.KeySym.DOWN, tcod.event.KeySym.S, tcod.event.KeySym.KP_2)
    NAVIGATION_LEFT = (tcod.event.KeySym.LEFT, tcod.event.KeySym.A, tcod.event.KeySym.KP_4)
    NAVIGATION_RIGHT = (tcod.event.KeySym.RIGHT, tcod.event.KeySym.D, tcod.event.KeySym.KP_6)
    CONFIRM = (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER)

    @staticmethod
    def handle_list_navigation(
        screen_instance, event, option_count: int, wrap_around: bool = True, callback=None
    ) -> bool:
        """Handle up/down navigation for list-based screens.

        Args:
            screen_instance: The screen object with selected_option attribute
            event: The input event
            option_count: Number of options in the list
            wrap_around: Whether to wrap around at ends
            callback: Optional callback function to call with direction (-1 or 1)

        Returns:
            True if input was handled, False otherwise
        """
        if event.sym in UniversalInputHandler.NAVIGATION_UP:
            if callback:
                callback(-1)
            elif wrap_around:
                screen_instance.selected_option = (
                    screen_instance.selected_option - 1
                ) % option_count
            else:
                screen_instance.selected_option = max(0, screen_instance.selected_option - 1)
            return True
        elif event.sym in UniversalInputHandler.NAVIGATION_DOWN:
            if callback:
                callback(1)
            elif wrap_around:
                screen_instance.selected_option = (
                    screen_instance.selected_option + 1
                ) % option_count
            else:
                screen_instance.selected_option = min(
                    option_count - 1, screen_instance.selected_option + 1
                )
            return True
        return False

    @staticmethod
    def handle_dialog_navigation(screen_instance, event, option_count: int = 2) -> bool:
        """Handle navigation for simple dialogs (usually 2 options).

        Args:
            screen_instance: The screen object with a selection attribute
            event: The input event
            option_count: Number of options (default 2 for Yes/No dialogs)

        Returns:
            True if input was handled, False otherwise
        """
        selection_attr = getattr(
            screen_instance, "warning_selection", getattr(screen_instance, "selected_option", None)
        )
        if selection_attr is None:
            return False

        if event.sym in (
            UniversalInputHandler.NAVIGATION_UP + UniversalInputHandler.NAVIGATION_DOWN
        ):
            # For simple dialogs, any up/down toggles between options
            if hasattr(screen_instance, "warning_selection"):
                screen_instance.warning_selection = 1 - screen_instance.warning_selection
            else:
                screen_instance.selected_option = 1 - screen_instance.selected_option
            return True
        return False

    @staticmethod
    def handle_value_adjustment(screen_instance, event, adjust_callback) -> bool:
        """Handle left/right adjustment for settings or values.

        Args:
            screen_instance: The screen object
            event: The input event
            adjust_callback: Function to call with direction (-1 or 1)

        Returns:
            True if input was handled, False otherwise
        """
        if event.sym in UniversalInputHandler.NAVIGATION_LEFT:
            adjust_callback(-1)
            return True
        elif event.sym in UniversalInputHandler.NAVIGATION_RIGHT:
            adjust_callback(1)
            return True
        return False

    @staticmethod
    def is_confirm_key(event) -> bool:
        """Check if the event is a confirm key (Enter/Return)."""
        return event.sym in UniversalInputHandler.CONFIRM

    @staticmethod
    def is_escape_key(event) -> bool:
        """Check if the event is an escape key."""
        return event.sym == tcod.event.KeySym.ESCAPE

    @staticmethod
    def handle_any_key_screen(event) -> bool:
        """Handle input for screens that return on any key press."""
        return True  # Any key should trigger a return action
