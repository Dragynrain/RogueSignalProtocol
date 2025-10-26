#!/usr/bin/env python3
"""
Critical tests for rendering coordinate system conversions.

These tests catch the most common bugs in the codebase:
1. [y, x] vs [x, y] array indexing confusion
2. Out-of-bounds array access
3. Coordinate conversion errors between systems
4. Bounds clamping failures

Context: These bugs caused significant debugging time. This test suite
prevents regression and catches issues early in development.

Reference: .claude/TCOD_GUIDE.md section on coordinate systems
"""

import pytest
import numpy as np
from unittest.mock import Mock
from game_coordinate_helpers import CoordinateHelpers


class TestCenterBoxCalculations:
    """Test box centering calculations."""

    def test_center_box_perfect_fit(self):
        """Centering a 40x20 box in 80x50 console."""
        x, y = CoordinateHelpers.center_box(40, 20, 80, 50)

        # Expected: center at (40, 25), box starts at (20, 15)
        assert x == 20, "Box should start at x=20"
        assert y == 15, "Box should start at y=15"

    def test_center_box_odd_dimensions(self):
        """Centering with odd dimensions uses integer division."""
        x, y = CoordinateHelpers.center_box(41, 21, 80, 50)

        # center_x = 40, center_y = 25
        # start_x = 40 - 41//2 = 40 - 20 = 20
        # start_y = 25 - 21//2 = 25 - 10 = 15
        assert x == 20
        assert y == 15

    def test_center_box_small_in_large(self):
        """Centering small box in large console."""
        x, y = CoordinateHelpers.center_box(10, 5, 100, 50)

        # center at (50, 25), box starts at (45, 23)
        # 50 - 10//2 = 45, 25 - 5//2 = 23
        assert x == 45
        assert y == 23

    def test_center_box_minimum_size(self):
        """Centering 1x1 box."""
        x, y = CoordinateHelpers.center_box(1, 1, 10, 10)

        # center at (5, 5), box starts at (5, 5)
        assert x == 5
        assert y == 5


class TestClampBounds:
    """Test bounds clamping - CRITICAL for preventing array access bugs."""

    def test_clamp_bounds_within_limits(self):
        """Region fully within bounds - no clamping needed."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 10, 20, 15, 80, 50)

        assert x == 10
        assert y == 10
        assert w == 20
        assert h == 15

    def test_clamp_bounds_exceeds_right_edge(self):
        """Region extends past right edge - width clamped."""
        # Box at (70, 10) with width 20 would go to x=90, but max is 80
        x, y, w, h = CoordinateHelpers.clamp_bounds(70, 10, 20, 15, 80, 50)

        assert x == 70, "X position unchanged"
        assert y == 10, "Y position unchanged"
        assert w == 10, "Width clamped to fit (80 - 70 = 10)"
        assert h == 15, "Height unchanged"

    def test_clamp_bounds_exceeds_bottom_edge(self):
        """Region extends past bottom edge - height clamped."""
        # Box at (10, 40) with height 15 would go to y=55, but max is 50
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 40, 20, 15, 80, 50)

        assert x == 10
        assert y == 40
        assert w == 20
        assert h == 10, "Height clamped to fit (50 - 40 = 10)"

    def test_clamp_bounds_negative_position(self):
        """Negative position clamped to 0."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(-5, -10, 20, 15, 80, 50)

        assert x == 0, "Negative X clamped to 0"
        assert y == 0, "Negative Y clamped to 0"
        # Width/height recalculated from clamped position
        assert w == 20, "Width preserved"
        assert h == 15, "Height preserved"

    def test_clamp_bounds_completely_out_of_bounds(self):
        """Region completely beyond bounds."""
        # Position at (100, 100) with console 80x50
        x, y, w, h = CoordinateHelpers.clamp_bounds(100, 100, 20, 15, 80, 50)

        # Position clamped to max valid position
        assert x == 79, "X clamped to max_width - 1"
        assert y == 49, "Y clamped to max_height - 1"
        # No space available from clamped position
        assert w == 1, "Only 1 pixel width available"
        assert h == 1, "Only 1 pixel height available"

    def test_clamp_bounds_zero_dimensions(self):
        """Zero-sized region."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 10, 0, 0, 80, 50)

        assert x == 10
        assert y == 10
        assert w == 0
        assert h == 0


class TestSetAlphaRegion:
    """
    CRITICAL: Test [y, x] array indexing correctness.

    This is where most transparency bugs occur. The test ensures
    set_alpha_region correctly uses [row, col] = [y, x] indexing.
    """

    def create_mock_console(self, width, height):
        """Create a mock console with proper rgba array structure."""
        console = Mock()
        console.width = width
        console.height = height

        # Create RGBA array: [height, width, 4 channels]
        # This matches TCOD's actual structure
        rgba_array = np.zeros((height, width, 4), dtype=np.uint8)
        console.rgba = {"bg": rgba_array}

        return console

    def test_set_alpha_region_basic(self):
        """Set alpha for a simple region - verify [y, x] indexing."""
        console = self.create_mock_console(80, 50)

        # Set alpha for region at x=10, y=5, size 30x15
        CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=255)

        # Verify correct region modified
        for y in range(5, 20):  # y from 5 to 19 (height=15)
            for x in range(10, 40):  # x from 10 to 39 (width=30)
                alpha_value = console.rgba["bg"][y, x, 3]  # [y, x] indexing
                assert alpha_value == 255, f"Alpha at [{y}, {x}] should be 255, got {alpha_value}"

        # Verify outside region not modified
        assert console.rgba["bg"][4, 10, 3] == 0, "Row above should be untouched"
        assert console.rgba["bg"][5, 9, 3] == 0, "Column left should be untouched"
        assert console.rgba["bg"][20, 10, 3] == 0, "Row below should be untouched"
        assert console.rgba["bg"][5, 40, 3] == 0, "Column right should be untouched"

    def test_set_alpha_region_full_transparency(self):
        """Set full transparency (alpha=0) for game rendering area."""
        console = self.create_mock_console(80, 50)

        # Initialize all to opaque
        console.rgba["bg"][:, :, 3] = 255

        # Make game area transparent (common operation)
        CoordinateHelpers.set_alpha_region(console, x=0, y=1, width=54, height=27, alpha=0)

        # Verify transparency applied
        for y in range(1, 28):
            for x in range(0, 54):
                assert console.rgba["bg"][y, x, 3] == 0, f"Pixel [{y}, {x}] should be transparent"

        # Verify edges remain opaque
        assert console.rgba["bg"][0, 0, 3] == 255, "Top edge should remain opaque"
        assert console.rgba["bg"][28, 0, 3] == 255, "Bottom edge should remain opaque"
        assert console.rgba["bg"][1, 54, 3] == 255, "Right edge should remain opaque"

    def test_set_alpha_region_out_of_bounds_clamped(self):
        """Region extending beyond console bounds is safely clamped."""
        console = self.create_mock_console(80, 50)

        # Try to set alpha beyond console bounds - should clamp
        CoordinateHelpers.set_alpha_region(console, x=70, y=40, width=20, height=15, alpha=128)

        # Should only modify up to console bounds
        # x: 70 to 79 (width clamped to 10)
        # y: 40 to 49 (height clamped to 10)
        for y in range(40, 50):
            for x in range(70, 80):
                assert console.rgba["bg"][y, x, 3] == 128

        # No crash from out-of-bounds access
        # (This is what we're really testing - safety)

    def test_set_alpha_region_negative_position_clamped(self):
        """Negative position is clamped safely."""
        console = self.create_mock_console(80, 50)

        # Negative position - should clamp to (0, 0)
        CoordinateHelpers.set_alpha_region(console, x=-5, y=-10, width=15, height=20, alpha=200)

        # Should start from (0, 0) with full width/height
        for y in range(0, 20):
            for x in range(0, 15):
                assert console.rgba["bg"][y, x, 3] == 200

    def test_set_alpha_region_single_pixel(self):
        """Set alpha for single pixel - edge case."""
        console = self.create_mock_console(80, 50)

        CoordinateHelpers.set_alpha_region(console, x=40, y=25, width=1, height=1, alpha=99)

        assert console.rgba["bg"][25, 40, 3] == 99, "Single pixel should be set"
        # Verify neighbors untouched
        assert console.rgba["bg"][24, 40, 3] == 0
        assert console.rgba["bg"][26, 40, 3] == 0
        assert console.rgba["bg"][25, 39, 3] == 0
        assert console.rgba["bg"][25, 41, 3] == 0


class TestCharToPixelConversion:
    """Test console character to pixel coordinate conversion."""

    def test_char_to_pixel_standard_resolution(self):
        """Test conversion with 1920x1080 window."""
        # Console 80x50, window 1920x1080
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=10, console_y=5,
            window_width=1920, window_height=1080
        )

        # pixels_per_char_x = 1920 / 80 = 24
        # pixels_per_char_y = 1080 / 50 = 21.6
        expected_x = int(10 * (1920 / 80))  # 10 * 24 = 240
        expected_y = int(5 * (1080 / 50))   # 5 * 21.6 = 108

        assert pixel_x == expected_x
        assert pixel_y == expected_y

    def test_char_to_pixel_4k_resolution(self):
        """Test conversion with 4K resolution."""
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=40, console_y=25,
            window_width=3840, window_height=2160
        )

        # pixels_per_char_x = 3840 / 80 = 48
        # pixels_per_char_y = 2160 / 50 = 43.2
        expected_x = int(40 * 48)      # 1920
        expected_y = int(25 * 43.2)    # 1080

        assert pixel_x == expected_x
        assert pixel_y == expected_y

    def test_char_to_pixel_origin(self):
        """Test conversion at origin (0, 0)."""
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=0, console_y=0,
            window_width=1280, window_height=800
        )

        assert pixel_x == 0
        assert pixel_y == 0

    def test_char_to_pixel_bottom_right(self):
        """Test conversion at bottom-right corner."""
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=79, console_y=49,  # Last valid console position
            window_width=1920, window_height=1080
        )

        # Should be near but not at window edge (since char occupies space)
        expected_x = int(79 * (1920 / 80))  # 1896
        expected_y = int(49 * (1080 / 50))  # 1058

        assert pixel_x == expected_x
        assert pixel_y == expected_y
        assert pixel_x < 1920  # Not at edge yet
        assert pixel_y < 1080


class TestPixelToCharConversion:
    """Test pixel to console character coordinate conversion."""

    def test_pixel_to_char_standard_click(self):
        """Test converting mouse click to console coordinates."""
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=400, pixel_y=300,
            window_width=1280, window_height=800
        )

        # pixels_per_tile_x = 1280 / 80 = 16
        # pixels_per_tile_y = 800 / 50 = 16
        # tile_x = 400 / 16 = 25
        # tile_y = 300 / 16 = 18
        assert tile_x == 25
        assert tile_y == 18

    def test_pixel_to_char_clamping_beyond_bounds(self):
        """Test that out-of-bounds pixels clamp to console edges."""
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=9999, pixel_y=9999,  # Way beyond window
            window_width=1280, window_height=800
        )

        # Should clamp to max valid console position
        assert tile_x == 79, "X should clamp to max console width - 1"
        assert tile_y == 49, "Y should clamp to max console height - 1"

    def test_pixel_to_char_negative_position(self):
        """Test that negative pixels clamp to (0, 0)."""
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=-100, pixel_y=-200,
            window_width=1280, window_height=800
        )

        assert tile_x == 0, "Negative X should clamp to 0"
        assert tile_y == 0, "Negative Y should clamp to 0"

    def test_pixel_to_char_origin(self):
        """Test conversion at pixel origin."""
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=0, pixel_y=0,
            window_width=1920, window_height=1080
        )

        assert tile_x == 0
        assert tile_y == 0


class TestPixelToSpriteGrid:
    """Test pixel to sprite grid conversion for graphics mode."""

    def test_pixel_to_sprite_grid_player_position(self):
        """Test converting player sprite position."""
        # Player at viewport (13, 11) with 97x80 tiles renders at (1261, 880)
        grid_x, grid_y = CoordinateHelpers.pixel_to_sprite_grid(
            pixel_x=1261, pixel_y=880,
            sprite_tile_width=97, sprite_tile_height=80
        )

        assert grid_x == 13, "Should convert back to grid x=13"
        assert grid_y == 11, "Should convert back to grid y=11"

    def test_pixel_to_sprite_grid_origin(self):
        """Test sprite grid conversion at origin."""
        grid_x, grid_y = CoordinateHelpers.pixel_to_sprite_grid(
            pixel_x=0, pixel_y=0,
            sprite_tile_width=100, sprite_tile_height=80
        )

        assert grid_x == 0
        assert grid_y == 0

    def test_pixel_to_sprite_grid_high_resolution(self):
        """Test sprite grid with large tiles (4K resolution)."""
        # 4K window with large sprite tiles
        grid_x, grid_y = CoordinateHelpers.pixel_to_sprite_grid(
            pixel_x=2000, pixel_y=1600,
            sprite_tile_width=200, sprite_tile_height=160
        )

        assert grid_x == 10  # 2000 / 200
        assert grid_y == 10  # 1600 / 160

    def test_pixel_to_sprite_grid_fractional_position(self):
        """Test that fractional grid positions round down."""
        # Click at pixel 150 with tile width 100 -> grid 1 (not 1.5)
        grid_x, grid_y = CoordinateHelpers.pixel_to_sprite_grid(
            pixel_x=150, pixel_y=125,
            sprite_tile_width=100, sprite_tile_height=100
        )

        assert grid_x == 1, "Should truncate to grid 1"
        assert grid_y == 1, "Should truncate to grid 1"


class TestCoordinateSystemIntegration:
    """
    Integration tests for coordinate systems working together.

    Tests the full pipeline: console -> pixel -> sprite grid
    """

    def test_round_trip_char_to_pixel_to_char(self):
        """Test converting char->pixel->char returns same position."""
        original_x, original_y = 40, 25
        window_w, window_h = 1920, 1080

        # Convert to pixels
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            original_x, original_y, window_w, window_h
        )

        # Convert back to chars
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x, pixel_y, window_w, window_h
        )

        assert tile_x == original_x, "Round trip should preserve X"
        assert tile_y == original_y, "Round trip should preserve Y"

    def test_sprite_grid_matches_viewport_coordinates(self):
        """Test sprite grid coordinates align with viewport."""
        # Viewport uses sprite tiles - ensure conversion is consistent
        viewport_x, viewport_y = 13, 11
        tile_width, tile_height = 97, 80

        # Sprite at viewport position
        pixel_x = viewport_x * tile_width
        pixel_y = viewport_y * tile_height

        # Convert back
        grid_x, grid_y = CoordinateHelpers.pixel_to_sprite_grid(
            pixel_x, pixel_y, tile_width, tile_height
        )

        assert grid_x == viewport_x
        assert grid_y == viewport_y


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases that commonly cause bugs."""

    def test_zero_width_region(self):
        """Zero-width region should not crash."""
        console = Mock()
        console.width = 80
        console.height = 50
        rgba_array = np.zeros((50, 80, 4), dtype=np.uint8)
        console.rgba = {"bg": rgba_array}

        # Should handle gracefully
        CoordinateHelpers.set_alpha_region(console, x=10, y=10, width=0, height=5, alpha=255)

        # Nothing should change (but no crash)
        assert np.all(console.rgba["bg"][:, :, 3] == 0)

    def test_maximum_size_region(self):
        """Full console-sized region."""
        console = Mock()
        console.width = 80
        console.height = 50
        rgba_array = np.zeros((50, 80, 4), dtype=np.uint8)
        console.rgba = {"bg": rgba_array}

        CoordinateHelpers.set_alpha_region(console, x=0, y=0, width=80, height=50, alpha=255)

        # Entire console should be set
        assert np.all(console.rgba["bg"][:, :, 3] == 255)

    def test_single_row_region(self):
        """Single-row region (height=1)."""
        console = Mock()
        console.width = 80
        console.height = 50
        rgba_array = np.zeros((50, 80, 4), dtype=np.uint8)
        console.rgba = {"bg": rgba_array}

        CoordinateHelpers.set_alpha_region(console, x=0, y=25, width=80, height=1, alpha=128)

        # Only row 25 should be set
        assert np.all(console.rgba["bg"][25, :, 3] == 128)
        assert np.all(console.rgba["bg"][24, :, 3] == 0)
        assert np.all(console.rgba["bg"][26, :, 3] == 0)

    def test_single_column_region(self):
        """Single-column region (width=1)."""
        console = Mock()
        console.width = 80
        console.height = 50
        rgba_array = np.zeros((50, 80, 4), dtype=np.uint8)
        console.rgba = {"bg": rgba_array}

        CoordinateHelpers.set_alpha_region(console, x=40, y=0, width=1, height=50, alpha=200)

        # Only column 40 should be set
        assert np.all(console.rgba["bg"][:, 40, 3] == 200)
        assert np.all(console.rgba["bg"][:, 39, 3] == 0)
        assert np.all(console.rgba["bg"][:, 41, 3] == 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
