#!/usr/bin/env python3
"""
Unit tests for MenuMouseHandler class.

Tests mouse coordinate conversion for menu/UI screens, helper methods,
and edge cases.
"""

from unittest.mock import Mock

import tcod.event

from game_mouse_utils import MenuMouseHandler


class FakePixel:
    """Mock pixel coordinate object matching tcod.event structure.

    TCOD's pixel object supports both tuple unpacking and attribute access.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        """Support tuple unpacking: pixel_x, pixel_y = event.pixel"""
        return iter((self.x, self.y))


class TestConvertToTileCoords:
    """Test convert_to_tile_coords() method for menu coordinate conversion."""

    def test_convert_basic_coordinates(self):
        """Convert pixel coordinates to tile coordinates in standard window."""
        # Mock event with pixel coordinates
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = FakePixel(400, 300)  # Center of 800x600 window

        # Mock context with 800x600 window
        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        converted = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert converted is not None
        assert hasattr(converted, "tile")
        # Center of 80x50 console should be around (40, 25)
        assert converted.tile.x == 40
        assert converted.tile.y == 25

    def test_convert_top_left_corner(self):
        """Convert coordinates at top-left corner (0, 0)."""
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = FakePixel(0, 0)

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        converted = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert converted is not None
        assert converted.tile.x == 0
        assert converted.tile.y == 0

    def test_convert_bottom_right_corner(self):
        """Convert coordinates at bottom-right corner."""
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = FakePixel(799, 599)  # Just inside 800x600 window

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        converted = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert converted is not None
        # Should be at or near (79, 49) - the bottom-right of 80x50 console
        assert converted.tile.x == 79
        assert converted.tile.y == 49

    def test_convert_different_window_size(self):
        """Convert coordinates with non-standard window size."""
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = FakePixel(640, 480)  # Center of 1280x960 window

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (1280, 960)

        converted = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert converted is not None
        assert hasattr(converted, "tile")
        # Center of 80x50 console
        assert converted.tile.x == 40
        assert converted.tile.y == 25

    def test_convert_preserves_other_attributes(self):
        """Conversion preserves other event attributes."""
        original_event = Mock(spec=tcod.event.MouseMotion)
        original_event.type = "MOUSEMOTION"
        original_event.pixel = FakePixel(400, 300)
        original_event.button = tcod.event.MouseButton.LEFT

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        converted = MenuMouseHandler.convert_to_tile_coords(original_event, context)

        # Converted event should have tile attribute
        assert hasattr(converted, "tile")
        assert converted.tile is not None
        # Other attributes should be preserved
        assert converted.type == "MOUSEMOTION"
        assert converted.button == tcod.event.MouseButton.LEFT

    def test_convert_no_pixel_attribute(self):
        """Return None when event has no pixel attribute."""
        event = Mock(spec=tcod.event.KeyDown)
        event.type = "KEYDOWN"
        # No pixel attribute

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        result = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert result is None

    def test_convert_pixel_is_none(self):
        """Return None when event.pixel is None."""
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = None

        context = Mock()
        context.sdl_window = Mock()
        context.sdl_window.size = (800, 600)

        result = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert result is None

    def test_convert_no_sdl_window_uses_fallback(self):
        """Use fallback window size when sdl_window not available."""
        event = Mock(spec=tcod.event.MouseMotion)
        event.type = "MOUSEMOTION"
        event.pixel = FakePixel(400, 300)

        context = Mock()
        context.sdl_window = None

        # Should still work using fallback (800, 600)
        converted = MenuMouseHandler.convert_to_tile_coords(event, context)

        assert converted is not None
        assert hasattr(converted, "tile")
        assert converted.tile.x == 40
        assert converted.tile.y == 25


class TestGetTileCoords:
    """Test get_tile_coords() helper method."""

    def test_get_tile_coords_from_converted_event(self):
        """Extract tile coordinates from converted event."""
        event = Mock()
        event.tile = FakePixel(10, 20)

        coords = MenuMouseHandler.get_tile_coords(event)

        assert coords is not None
        assert coords == (10, 20)

    def test_get_tile_coords_with_floats(self):
        """Convert float coordinates to integers."""
        event = Mock()
        event.tile = FakePixel(10.7, 20.3)

        coords = MenuMouseHandler.get_tile_coords(event)

        assert coords == (10, 20)

    def test_get_tile_coords_no_tile_attribute(self):
        """Return None when event has no tile attribute."""
        event = Mock(spec=tcod.event.KeyDown)
        # No tile attribute

        coords = MenuMouseHandler.get_tile_coords(event)

        assert coords is None

    def test_get_tile_coords_tile_is_none(self):
        """Return None when event.tile is None."""
        event = Mock()
        event.tile = None

        coords = MenuMouseHandler.get_tile_coords(event)

        assert coords is None


class TestMouseButtonChecks:
    """Test is_left_click() and is_right_click() methods."""

    def test_is_left_click_true(self):
        """Detect left mouse button click."""
        # Use real tcod event (isinstance check requires it)
        event = tcod.event.MouseButtonDown(pixel=(100, 100), button=tcod.event.MouseButton.LEFT)

        assert MenuMouseHandler.is_left_click(event) is True

    def test_is_left_click_wrong_button(self):
        """Return False for non-left button."""
        event = Mock()
        event.type = "MOUSEBUTTONDOWN"
        event.button = tcod.event.MouseButton.RIGHT

        assert MenuMouseHandler.is_left_click(event) is False

    def test_is_left_click_wrong_event_type(self):
        """Return False for non-click event."""
        event = Mock()
        event.type = "MOUSEMOTION"
        event.button = tcod.event.MouseButton.LEFT

        assert MenuMouseHandler.is_left_click(event) is False

    def test_is_left_click_no_button_attribute(self):
        """Return False when event has no button attribute."""
        event = Mock(spec=tcod.event.KeyDown)
        event.type = "MOUSEBUTTONDOWN"
        # No button attribute

        assert MenuMouseHandler.is_left_click(event) is False

    def test_is_right_click_true(self):
        """Detect right mouse button click."""
        # Use real tcod event (isinstance check requires it)
        event = tcod.event.MouseButtonDown(pixel=(100, 100), button=tcod.event.MouseButton.RIGHT)

        assert MenuMouseHandler.is_right_click(event) is True

    def test_is_right_click_wrong_button(self):
        """Return False for non-right button."""
        event = Mock()
        event.type = "MOUSEBUTTONDOWN"
        event.button = tcod.event.MouseButton.LEFT

        assert MenuMouseHandler.is_right_click(event) is False

    def test_is_right_click_wrong_event_type(self):
        """Return False for non-click event."""
        event = Mock()
        event.type = "MOUSEMOTION"
        event.button = tcod.event.MouseButton.RIGHT

        assert MenuMouseHandler.is_right_click(event) is False


class TestIsInRect:
    """Test is_in_rect() method for rectangular region checking."""

    def test_is_in_rect_center(self):
        """Coordinate in center of rectangle."""
        # Rectangle at (10, 10) with size 20x10
        result = MenuMouseHandler.is_in_rect(20, 15, 10, 10, 20, 10)

        assert result is True

    def test_is_in_rect_top_left_corner(self):
        """Coordinate at top-left corner (inclusive)."""
        result = MenuMouseHandler.is_in_rect(10, 10, 10, 10, 20, 10)

        assert result is True

    def test_is_in_rect_bottom_right_edge_exclusive(self):
        """Coordinate at bottom-right edge (exclusive)."""
        # Rectangle (10, 10) size 20x10 means right edge is x=30, bottom is y=20
        # x=30 and y=20 should be OUTSIDE (exclusive)
        result = MenuMouseHandler.is_in_rect(30, 20, 10, 10, 20, 10)

        assert result is False

    def test_is_in_rect_just_inside_bottom_right(self):
        """Coordinate just inside bottom-right corner."""
        # Last valid coordinate inside rectangle
        result = MenuMouseHandler.is_in_rect(29, 19, 10, 10, 20, 10)

        assert result is True

    def test_is_in_rect_left_edge(self):
        """Coordinate on left edge (inclusive)."""
        result = MenuMouseHandler.is_in_rect(10, 15, 10, 10, 20, 10)

        assert result is True

    def test_is_in_rect_right_edge(self):
        """Coordinate on right edge (exclusive)."""
        result = MenuMouseHandler.is_in_rect(30, 15, 10, 10, 20, 10)

        assert result is False

    def test_is_in_rect_top_edge(self):
        """Coordinate on top edge (inclusive)."""
        result = MenuMouseHandler.is_in_rect(20, 10, 10, 10, 20, 10)

        assert result is True

    def test_is_in_rect_bottom_edge(self):
        """Coordinate on bottom edge (exclusive)."""
        result = MenuMouseHandler.is_in_rect(20, 20, 10, 10, 20, 10)

        assert result is False

    def test_is_in_rect_outside_left(self):
        """Coordinate outside rectangle to the left."""
        result = MenuMouseHandler.is_in_rect(9, 15, 10, 10, 20, 10)

        assert result is False

    def test_is_in_rect_outside_above(self):
        """Coordinate outside rectangle above."""
        result = MenuMouseHandler.is_in_rect(20, 9, 10, 10, 20, 10)

        assert result is False

    def test_is_in_rect_single_tile(self):
        """Rectangle of size 1x1."""
        # Only coordinate (5, 5) should be inside
        assert MenuMouseHandler.is_in_rect(5, 5, 5, 5, 1, 1) is True
        assert MenuMouseHandler.is_in_rect(6, 5, 5, 5, 1, 1) is False
        assert MenuMouseHandler.is_in_rect(5, 6, 5, 5, 1, 1) is False

    def test_is_in_rect_menu_button_scenario(self):
        """Real-world scenario: checking if mouse is over a menu button."""
        # Button at (30, 20) with text "Start Game" (10 chars wide, 1 tall)
        button_x, button_y = 30, 20
        button_width, button_height = 10, 1

        # Mouse over button
        assert (
            MenuMouseHandler.is_in_rect(35, 20, button_x, button_y, button_width, button_height)
            is True
        )

        # Mouse just left of button
        assert (
            MenuMouseHandler.is_in_rect(29, 20, button_x, button_y, button_width, button_height)
            is False
        )

        # Mouse just right of button
        assert (
            MenuMouseHandler.is_in_rect(40, 20, button_x, button_y, button_width, button_height)
            is False
        )

        # Mouse above button
        assert (
            MenuMouseHandler.is_in_rect(35, 19, button_x, button_y, button_width, button_height)
            is False
        )

        # Mouse below button
        assert (
            MenuMouseHandler.is_in_rect(35, 21, button_x, button_y, button_width, button_height)
            is False
        )
