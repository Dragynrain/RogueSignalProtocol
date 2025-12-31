#!/usr/bin/env python3
"""
Menu Mouse Event Handling Utilities

Provides mouse event coordinate conversion for MENU/UI SCREENS ONLY.

**SCOPE:** This is for console-based UI (menus, settings, help screens)
**NOT FOR:** In-game world coordinates (see InputHandler._mouse_pixel_to_world)

Why this exists:
- TCOD's context.convert_event() is unreliable in multi-layer rendering
- Works in some contexts but returns (0,0) in others
- Manual conversion using CoordinateHelpers works consistently

See .claude/MOUSE_COORDINATE_HANDLING.md for details.
See .claude/TCOD_GUIDE.md section "Mouse Coordinate Conversion" for technical background.
"""

import copy

import tcod.event

from rsp.rendering.coordinates import CoordinateHelpers


class MenuMouseHandler:
    """
    Menu/UI mouse event handling with automatic coordinate conversion.

    **USE FOR:** Main menu, settings, graphics preview, help screens, achievements
    **DON'T USE FOR:** In-game gameplay (use InputHandler._mouse_pixel_to_world instead)

    This converts pixel coordinates to console tile coordinates (80x50 grid).
    For world coordinates (game map positions), see InputHandler in game_input.py.
    """

    @staticmethod
    def convert_to_tile_coords(event: tcod.event.Event, context) -> tcod.event.Event | None:
        """
        Convert mouse event from pixel coordinates to tile coordinates.

        Args:
            event: Raw mouse event with pixel coordinates
            context: TCOD context (for window size)

        Returns:
            New event with .tile attribute set to tile coordinates,
            or None if conversion fails

        Example:
            >>> for event in tcod.event.get():
            ...     if event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
            ...         event = MouseEventHandler.convert_to_tile_coords(event, context)
            ...         if event is None:
            ...             continue
            ...     if event.type == "MOUSEBUTTONDOWN":
            ...         tile_x, tile_y = event.tile
            ...         print(f"Clicked tile: ({tile_x}, {tile_y})")
        """
        # Must have pixel coordinates
        if not hasattr(event, "pixel") or event.pixel is None:
            return None

        pixel_x, pixel_y = event.pixel

        # Get window size dynamically
        if hasattr(context, "sdl_window") and context.sdl_window:
            window_w, window_h = context.sdl_window.size
        else:
            # Fallback to default (should rarely be needed)
            window_w, window_h = (800, 600)

        # Convert pixel coordinates to tile coordinates
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x, pixel_y, window_w, window_h
        )

        # Create new event with tile coordinates stored in both .tile and .position attributes
        # (.position is TCOD standard, .tile is for backward compatibility)
        converted_event = copy.copy(event)
        coord_tuple = type(event.pixel)(tile_x, tile_y)
        converted_event.tile = coord_tuple
        converted_event.position = coord_tuple  # TCOD standard attribute

        return converted_event

    @staticmethod
    def get_tile_coords(event: tcod.event.Event) -> tuple[int, int] | None:
        """
        Extract tile coordinates from a converted mouse event.

        Args:
            event: Mouse event (should have been converted via convert_to_tile_coords)

        Returns:
            (tile_x, tile_y) tuple, or None if event has no tile coordinates

        Example:
            >>> coords = MouseEventHandler.get_tile_coords(event)
            >>> if coords:
            ...     tile_x, tile_y = coords
            ...     print(f"Mouse at: ({tile_x}, {tile_y})")
        """
        if not hasattr(event, "tile") or event.tile is None:
            return None

        return (int(event.tile.x), int(event.tile.y))

    @staticmethod
    def is_left_click(event: tcod.event.Event) -> bool:
        """
        Check if event is a left mouse button click.

        Args:
            event: Mouse event to check

        Returns:
            True if this is a left button click, False otherwise
        """
        return (
            isinstance(event, tcod.event.MouseButtonDown)
            and event.button == tcod.event.MouseButton.LEFT
        )

    @staticmethod
    def is_right_click(event: tcod.event.Event) -> bool:
        """
        Check if event is a right mouse button click.

        Args:
            event: Mouse event to check

        Returns:
            True if this is a right button click, False otherwise
        """
        return (
            isinstance(event, tcod.event.MouseButtonDown)
            and event.button == tcod.event.MouseButton.RIGHT
        )

    @staticmethod
    def is_in_rect(
        tile_x: int, tile_y: int, rect_x: int, rect_y: int, rect_width: int, rect_height: int
    ) -> bool:
        """
        Check if tile coordinates are within a rectangular region.

        Args:
            tile_x: X coordinate to check
            tile_y: Y coordinate to check
            rect_x: Rectangle left edge
            rect_y: Rectangle top edge
            rect_width: Rectangle width
            rect_height: Rectangle height

        Returns:
            True if (tile_x, tile_y) is inside the rectangle

        Example:
            >>> # Check if mouse is over a menu button
            >>> coords = MouseEventHandler.get_tile_coords(event)
            >>> if coords and MouseEventHandler.is_in_rect(*coords, button_x, button_y, 10, 2):
            ...     print("Mouse over button!")
        """
        return rect_x <= tile_x < rect_x + rect_width and rect_y <= tile_y < rect_y + rect_height
