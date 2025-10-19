"""
Coordinate and bounds utilities for console rendering.

This module provides reusable coordinate calculations and array manipulation utilities.
All methods use (x, y) parameter order for clarity, but internally handle TCOD's [y, x]
array indexing to prevent common transparency and positioning bugs.

Key Principle: Pass coordinates as (x, y), access TCOD arrays as [y, x].
"""

from typing import Tuple
import tcod.console


class CoordinateHelpers:
    """
    Reusable coordinate and bounds utilities for console rendering.

    All methods use (x, y) parameter order in function signatures for clarity.
    Internally converts to [y, x] when accessing TCOD numpy arrays to prevent
    the most common source of transparency and positioning bugs in this codebase.

    Usage:
        # Calculate centered box position
        x, y = CoordinateHelpers.center_box(40, 20, 80, 50)

        # Set transparency for a region
        CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=0)

        # Convert console coordinates to pixel coordinates
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=10, console_y=5, window_width=1920, window_height=1080
        )
    """

    @staticmethod
    def center_box(box_width: int, box_height: int,
                   console_width: int, console_height: int) -> Tuple[int, int]:
        """
        Calculate top-left position to center a box within a console area.

        Args:
            box_width: Width of the box to center
            box_height: Height of the box to center
            console_width: Width of the containing area
            console_height: Height of the containing area

        Returns:
            Tuple of (start_x, start_y) representing the top-left corner position

        Example:
            # Center a 40x20 box on an 80x50 console
            x, y = CoordinateHelpers.center_box(40, 20, 80, 50)
            # Returns (20, 15)
        """
        center_x = console_width // 2
        center_y = console_height // 2

        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        return (start_x, start_y)

    @staticmethod
    def clamp_bounds(x: int, y: int, width: int, height: int,
                     max_width: int, max_height: int) -> Tuple[int, int, int, int]:
        """
        Clamp a rectangular region to fit within array bounds.

        Ensures that a box defined by (x, y, width, height) fits entirely within
        the bounds (0, 0, max_width, max_height). Adjusts position and/or dimensions
        as needed.

        Args:
            x: Left edge of the region
            y: Top edge of the region
            width: Width of the region
            height: Height of the region
            max_width: Maximum width boundary (exclusive)
            max_height: Maximum height boundary (exclusive)

        Returns:
            Tuple of (clamped_x, clamped_y, clamped_width, clamped_height)

        Example:
            # Clamp a box that extends beyond console bounds
            x, y, w, h = CoordinateHelpers.clamp_bounds(70, 40, 20, 15, 80, 50)
            # Returns (70, 40, 10, 10) - truncated to fit
        """
        # Clamp position to be within bounds
        clamped_x = max(0, min(x, max_width - 1))
        clamped_y = max(0, min(y, max_height - 1))

        # Calculate available space from clamped position
        available_width = max_width - clamped_x
        available_height = max_height - clamped_y

        # Clamp dimensions to fit in available space
        clamped_width = max(0, min(width, available_width))
        clamped_height = max(0, min(height, available_height))

        return (clamped_x, clamped_y, clamped_width, clamped_height)

    @staticmethod
    def set_alpha_region(console: tcod.console.Console,
                         x: int, y: int, width: int, height: int,
                         alpha: int) -> None:
        """
        Set alpha transparency for a rectangular region of the console.

        CRITICAL: This method handles TCOD's [y, x] array indexing internally.
        Parameters use (x, y) order for clarity, but array access uses [y, x].

        Args:
            console: TCOD console to modify
            x: Left edge of the region (in x coordinate)
            y: Top edge of the region (in y coordinate)
            width: Width of the region
            height: Height of the region
            alpha: Alpha value (0 = fully transparent, 255 = fully opaque)

        Example:
            # Make a dialogue box region opaque
            CoordinateHelpers.set_alpha_region(console, x=20, y=15, width=40, height=20, alpha=255)

            # Make game area transparent for sprite rendering
            CoordinateHelpers.set_alpha_region(console, x=0, y=1, width=54, height=27, alpha=0)

        Note:
            This is where we fix the [y, x] vs [x, y] confusion once and for all.
            Loop order is y-outer, x-inner to match TCOD array indexing [y, x].
        """
        # Get console dimensions for bounds checking
        console_height, console_width = console.rgba["bg"].shape[:2]

        # Clamp the region to console bounds
        x, y, width, height = CoordinateHelpers.clamp_bounds(
            x, y, width, height, console_width, console_height
        )

        # Set alpha for the region
        # CRITICAL: Loop order (y outer, x inner) matches TCOD indexing [y, x]
        # This prevents the transposed transparency bug that plagued this codebase
        for row in range(y, y + height):
            for col in range(x, x + width):
                # Access pattern: [y, x, channel] NOT [x, y, channel]
                console.rgba["bg"][row, col, 3] = alpha

    @staticmethod
    def char_to_pixel_coords(console_x: int, console_y: int,
                            window_width: int, window_height: int,
                            console_width: int = 80, console_height: int = 50) -> Tuple[int, int]:
        """
        Convert console character coordinates to SDL pixel coordinates.

        Used for positioning SDL sprites to align with console text. The console
        is rendered as a texture that scales to fill the window, so we need to
        calculate where each character position maps to in pixel space.

        Args:
            console_x: X position in console character grid
            console_y: Y position in console character grid
            window_width: Window width in pixels (from context.sdl_window.size)
            window_height: Window height in pixels
            console_width: Console width in characters (default 80)
            console_height: Console height in characters (default 50)

        Returns:
            Tuple of (pixel_x, pixel_y) in SDL window coordinate space

        Example:
            # Position a sprite at console character (10, 5)
            window_w, window_h = context.sdl_window.size
            pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
                10, 5, window_w, window_h
            )
            sdl_renderer.copy(sprite_texture, dstrect=(pixel_x, pixel_y, w, h))
        """
        # Calculate how many pixels each console character occupies
        pixels_per_char_x = window_width / console_width
        pixels_per_char_y = window_height / console_height

        # Convert to pixel coordinates
        pixel_x = int(console_x * pixels_per_char_x)
        pixel_y = int(console_y * pixels_per_char_y)

        return (pixel_x, pixel_y)
