#!/usr/bin/env python3
"""
Unit tests for CoordinateHelpers class.

Tests coordinate calculations, bounds clamping, alpha region setting,
and character-to-pixel coordinate conversion.
"""

import numpy as np
import tcod.console

from game_coordinate_helpers import CoordinateHelpers


class TestCenterBox:
    """Test center_box() method for box positioning calculations."""

    def test_center_box_simple(self):
        """center_box correctly centers a box on a standard console."""
        # Center a 40x20 box on an 80x50 console
        x, y = CoordinateHelpers.center_box(40, 20, 80, 50)

        assert x == 20  # (80 - 40) // 2 = 20
        assert y == 15  # (50 - 20) // 2 = 15

    def test_center_box_exact_fit(self):
        """center_box handles box that exactly fits the console."""
        x, y = CoordinateHelpers.center_box(80, 50, 80, 50)

        assert x == 0
        assert y == 0

    def test_center_box_odd_dimensions(self):
        """center_box handles odd dimensions correctly."""
        # 41x21 box on 80x50 console
        x, y = CoordinateHelpers.center_box(41, 21, 80, 50)

        # center_x = 80 // 2 = 40, start_x = 40 - 41 // 2 = 40 - 20 = 20
        # center_y = 50 // 2 = 25, start_y = 25 - 21 // 2 = 25 - 10 = 15
        assert x == 20
        assert y == 15

    def test_center_box_small_box(self):
        """center_box handles small boxes."""
        # 10x5 box on 80x50 console
        x, y = CoordinateHelpers.center_box(10, 5, 80, 50)

        assert x == 35  # center_x = 40, start_x = 40 - 10 // 2 = 40 - 5 = 35
        assert y == 23  # center_y = 25, start_y = 25 - 5 // 2 = 25 - 2 = 23

    def test_center_box_different_console_size(self):
        """center_box works with non-standard console sizes."""
        # 20x15 box on 54x27 console (game area size)
        x, y = CoordinateHelpers.center_box(20, 15, 54, 27)

        assert x == 17  # (54 - 20) // 2 = 17
        assert y == 6  # (27 - 15) // 2 = 6


class TestClampBounds:
    """Test clamp_bounds() method for boundary enforcement."""

    def test_clamp_bounds_no_clamping_needed(self):
        """clamp_bounds returns unchanged values when box fits."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 10, 20, 15, 80, 50)

        assert x == 10
        assert y == 10
        assert w == 20
        assert h == 15

    def test_clamp_bounds_right_edge(self):
        """clamp_bounds truncates width at right edge."""
        # Box at x=70 with width=20 on 80-wide console
        x, y, w, h = CoordinateHelpers.clamp_bounds(70, 10, 20, 15, 80, 50)

        assert x == 70
        assert y == 10
        assert w == 10  # Truncated to fit (80 - 70 = 10)
        assert h == 15

    def test_clamp_bounds_bottom_edge(self):
        """clamp_bounds truncates height at bottom edge."""
        # Box at y=40 with height=15 on 50-high console
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 40, 20, 15, 80, 50)

        assert x == 10
        assert y == 40
        assert w == 20
        assert h == 10  # Truncated to fit (50 - 40 = 10)

    def test_clamp_bounds_negative_position(self):
        """clamp_bounds clamps negative positions to 0."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(-5, -10, 20, 15, 80, 50)

        assert x == 0
        assert y == 0
        assert w == 20
        assert h == 15

    def test_clamp_bounds_exceeds_both_edges(self):
        """clamp_bounds handles box exceeding both width and height."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(70, 45, 20, 15, 80, 50)

        assert x == 70
        assert y == 45
        assert w == 10  # Truncated
        assert h == 5  # Truncated

    def test_clamp_bounds_completely_out_of_bounds(self):
        """clamp_bounds handles completely out-of-bounds box."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(90, 60, 20, 15, 80, 50)

        assert x == 79  # Clamped to max_width - 1
        assert y == 49  # Clamped to max_height - 1
        assert w == 1  # Only 1 column available
        assert h == 1  # Only 1 row available

    def test_clamp_bounds_zero_dimensions(self):
        """clamp_bounds handles zero-sized boxes."""
        x, y, w, h = CoordinateHelpers.clamp_bounds(10, 10, 0, 0, 80, 50)

        assert x == 10
        assert y == 10
        assert w == 0
        assert h == 0


class TestSetAlphaRegion:
    """Test set_alpha_region() method for transparency manipulation."""

    def test_set_alpha_region_opaque(self):
        """set_alpha_region correctly sets region to opaque."""
        console = tcod.console.Console(width=80, height=50)

        # Set entire console transparent first
        console.rgba["bg"][:, :, 3] = 0

        # Make a region opaque
        CoordinateHelpers.set_alpha_region(console, x=20, y=15, width=40, height=20, alpha=255)

        # Check that the region is opaque
        for y in range(15, 35):
            for x in range(20, 60):
                assert console.rgba["bg"][y, x, 3] == 255

        # Check that outside the region is still transparent
        assert console.rgba["bg"][14, 20, 3] == 0  # Above
        assert console.rgba["bg"][35, 20, 3] == 0  # Below
        assert console.rgba["bg"][15, 19, 3] == 0  # Left
        assert console.rgba["bg"][15, 60, 3] == 0  # Right

    def test_set_alpha_region_transparent(self):
        """set_alpha_region correctly sets region to transparent."""
        console = tcod.console.Console(width=80, height=50)

        # Set entire console opaque first
        console.rgba["bg"][:, :, 3] = 255

        # Make game area transparent
        CoordinateHelpers.set_alpha_region(console, x=0, y=1, width=54, height=27, alpha=0)

        # Check that the game area is transparent
        for y in range(1, 28):
            for x in range(0, 54):
                assert console.rgba["bg"][y, x, 3] == 0

        # Check that outside the region is still opaque
        assert console.rgba["bg"][0, 0, 3] == 255  # Above game area
        assert console.rgba["bg"][28, 0, 3] == 255  # Below game area
        assert console.rgba["bg"][1, 54, 3] == 255  # Right of game area

    def test_set_alpha_region_partial_transparency(self):
        """set_alpha_region handles partial transparency values."""
        console = tcod.console.Console(width=80, height=50)

        # Set to 50% transparency (alpha=128)
        CoordinateHelpers.set_alpha_region(console, x=10, y=10, width=20, height=10, alpha=128)

        # Check the region has correct alpha
        for y in range(10, 20):
            for x in range(10, 30):
                assert console.rgba["bg"][y, x, 3] == 128

    def test_set_alpha_region_clamping(self):
        """set_alpha_region clamps region to console bounds."""
        console = tcod.console.Console(width=80, height=50)

        # Try to set alpha beyond console bounds
        CoordinateHelpers.set_alpha_region(console, x=70, y=45, width=20, height=10, alpha=255)

        # Should only affect the valid region (70-79, 45-49)
        for y in range(45, 50):
            for x in range(70, 80):
                assert console.rgba["bg"][y, x, 3] == 255

        # Should not crash or affect invalid regions

    def test_set_alpha_region_single_cell(self):
        """set_alpha_region handles single-cell regions."""
        console = tcod.console.Console(width=80, height=50)

        # Set single cell
        CoordinateHelpers.set_alpha_region(console, x=40, y=25, width=1, height=1, alpha=200)

        assert console.rgba["bg"][25, 40, 3] == 200

        # Check neighbors are unaffected (default should be 255)
        assert console.rgba["bg"][24, 40, 3] == 255
        assert console.rgba["bg"][26, 40, 3] == 255
        assert console.rgba["bg"][25, 39, 3] == 255
        assert console.rgba["bg"][25, 41, 3] == 255

    def test_set_alpha_region_full_console(self):
        """set_alpha_region handles full-console regions."""
        console = tcod.console.Console(width=80, height=50)

        # Set entire console transparent
        CoordinateHelpers.set_alpha_region(console, x=0, y=0, width=80, height=50, alpha=0)

        # Check all cells are transparent
        assert np.all(console.rgba["bg"][:, :, 3] == 0)

    def test_set_alpha_region_correct_indexing(self):
        """set_alpha_region uses correct [y, x] indexing (regression test)."""
        console = tcod.console.Console(width=80, height=50)

        # Set transparency at a specific position
        # If indexing is wrong, this will set transparency at the transposed position
        CoordinateHelpers.set_alpha_region(console, x=10, y=20, width=1, height=1, alpha=100)

        # Check correct position has alpha=100
        assert console.rgba["bg"][20, 10, 3] == 100  # [y=20, x=10] is correct

        # Check transposed position is NOT affected (should be default 255)
        assert console.rgba["bg"][10, 20, 3] == 255  # [y=10, x=20] should be untouched


class TestCharToPixelCoords:
    """Test char_to_pixel_coords() method for coordinate conversion."""

    def test_char_to_pixel_origin(self):
        """char_to_pixel_coords handles origin (0, 0)."""
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=0, console_y=0, window_width=1920, window_height=1080
        )

        assert pixel_x == 0
        assert pixel_y == 0

    def test_char_to_pixel_standard_resolution(self):
        """char_to_pixel_coords converts correctly for standard resolution."""
        # 1920x1080 window with 80x50 console
        # Each char = 24x21.6 pixels
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=10, console_y=5, window_width=1920, window_height=1080
        )

        assert pixel_x == 240  # 10 * (1920/80) = 10 * 24 = 240
        assert pixel_y == 108  # 5 * (1080/50) = 5 * 21.6 = 108

    def test_char_to_pixel_high_resolution(self):
        """char_to_pixel_coords works with high-resolution windows."""
        # 2560x1440 window
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=40, console_y=25, window_width=2560, window_height=1440
        )

        assert pixel_x == 1280  # 40 * (2560/80) = 40 * 32 = 1280
        assert pixel_y == 720  # 25 * (1440/50) = 25 * 28.8 = 720

    def test_char_to_pixel_corner(self):
        """char_to_pixel_coords handles bottom-right corner."""
        # Bottom-right of 80x50 console
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=79, console_y=49, window_width=1600, window_height=1000
        )

        assert pixel_x == 1580  # 79 * (1600/80) = 79 * 20 = 1580
        assert pixel_y == 980  # 49 * (1000/50) = 49 * 20 = 980

    def test_char_to_pixel_custom_console_size(self):
        """char_to_pixel_coords works with custom console dimensions."""
        # Game area is 54x27 in graphics mode
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=27,
            console_y=13,
            window_width=1920,
            window_height=1080,
            console_width=54,
            console_height=27,
        )

        # Each char = 1920/54 = 35.55 pixels wide, 1080/27 = 40 pixels tall
        assert pixel_x == 960  # 27 * 35.555... = 960
        assert pixel_y == 520  # 13 * 40 = 520

    def test_char_to_pixel_fractional_pixels(self):
        """char_to_pixel_coords handles fractional pixel positions."""
        # Position that results in fractional pixels
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=15, console_y=7, window_width=1366, window_height=768
        )

        # Should be integer values (truncated)
        assert isinstance(pixel_x, int)
        assert isinstance(pixel_y, int)

        # 15 * (1366/80) = 15 * 17.075 = 256.125 -> 256
        # 7 * (768/50) = 7 * 15.36 = 107.52 -> 107
        assert pixel_x == 256
        assert pixel_y == 107

    def test_char_to_pixel_small_window(self):
        """char_to_pixel_coords works with small windows."""
        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            console_x=40, console_y=25, window_width=800, window_height=600
        )

        assert pixel_x == 400  # 40 * (800/80) = 40 * 10 = 400
        assert pixel_y == 300  # 25 * (600/50) = 25 * 12 = 300


class TestPixelToCharCoords:
    """Test pixel_to_char_coords() method for mouse coordinate conversion."""

    def test_pixel_to_char_origin(self):
        """pixel_to_char_coords handles origin (0, 0)."""
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=0, pixel_y=0, window_width=1920, window_height=1080
        )

        assert tile_x == 0
        assert tile_y == 0

    def test_pixel_to_char_standard_resolution(self):
        """pixel_to_char_coords converts correctly for standard resolution."""
        # 1920x1080 window with 80x50 console
        # Click at pixel (240, 108) should be tile (10, 5)
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=240, pixel_y=108, window_width=1920, window_height=1080
        )

        assert tile_x == 10  # 240 * (80/1920) = 240 * 0.0416... = 10
        assert tile_y == 5  # 108 * (50/1080) = 108 * 0.0462... = 5

    def test_pixel_to_char_inverse_of_char_to_pixel(self):
        """pixel_to_char_coords is the inverse of char_to_pixel_coords."""
        # Convert console coords to pixels, then back
        original_x, original_y = 15, 20

        pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
            original_x, original_y, 1920, 1080
        )

        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(pixel_x, pixel_y, 1920, 1080)

        assert tile_x == original_x
        assert tile_y == original_y

    def test_pixel_to_char_fractional_result(self):
        """pixel_to_char_coords handles fractional tile positions."""
        # Click at pixel (250, 110) - between tiles
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=250, pixel_y=110, window_width=1920, window_height=1080
        )

        # Should be integer values (truncated)
        assert isinstance(tile_x, int)
        assert isinstance(tile_y, int)

        # 250 * (80/1920) = 250 * 0.0416... = 10.416... -> 10
        # 110 * (50/1080) = 110 * 0.0462... = 5.092... -> 5
        assert tile_x == 10
        assert tile_y == 5

    def test_pixel_to_char_corner(self):
        """pixel_to_char_coords handles bottom-right corner."""
        # Click near bottom-right of window
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=1580, pixel_y=980, window_width=1600, window_height=1000
        )

        assert tile_x == 79  # 1580 * (80/1600) = 1580 * 0.05 = 79
        assert tile_y == 49  # 980 * (50/1000) = 980 * 0.05 = 49

    def test_pixel_to_char_small_window(self):
        """pixel_to_char_coords works with small windows."""
        # 800x600 window, click at (400, 300)
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            pixel_x=400, pixel_y=300, window_width=800, window_height=600
        )

        assert tile_x == 40  # 400 * (80/800) = 400 * 0.1 = 40
        assert tile_y == 25  # 300 * (50/600) = 300 * 0.0833... = 25


class TestIntegration:
    """Integration tests combining multiple CoordinateHelpers methods."""

    def test_center_and_clamp(self):
        """Centered box can be clamped if too large."""
        # Try to center a box larger than the console
        x, y = CoordinateHelpers.center_box(100, 60, 80, 50)

        # This will give negative positions
        assert x == -10
        assert y == -5

        # Clamp to valid bounds
        x, y, w, h = CoordinateHelpers.clamp_bounds(x, y, 100, 60, 80, 50)

        assert x == 0
        assert y == 0
        assert w == 80
        assert h == 50

    def test_center_and_set_alpha(self):
        """Centered box can have alpha set correctly."""
        console = tcod.console.Console(width=80, height=50)

        # Center a dialogue box
        box_w, box_h = 40, 20
        x, y = CoordinateHelpers.center_box(box_w, box_h, 80, 50)

        # Make it opaque
        CoordinateHelpers.set_alpha_region(console, x, y, box_w, box_h, alpha=255)

        # Verify the centered region is opaque
        for row in range(y, y + box_h):
            for col in range(x, x + box_w):
                assert console.rgba["bg"][row, col, 3] == 255

    def test_workflow_dialogue_rendering(self):
        """Simulate typical dialogue rendering workflow."""
        console = tcod.console.Console(width=80, height=50)

        # Step 1: Make entire console transparent
        CoordinateHelpers.set_alpha_region(console, 0, 0, 80, 50, alpha=0)

        # Step 2: Center dialogue box
        dialogue_w, dialogue_h = 50, 15
        dialogue_x, dialogue_y = CoordinateHelpers.center_box(dialogue_w, dialogue_h, 80, 50)

        # Step 3: Make dialogue area opaque
        CoordinateHelpers.set_alpha_region(
            console, dialogue_x, dialogue_y, dialogue_w, dialogue_h, alpha=255
        )

        # Verify: dialogue region opaque, rest transparent
        for y in range(50):
            for x in range(80):
                if (
                    dialogue_x <= x < dialogue_x + dialogue_w
                    and dialogue_y <= y < dialogue_y + dialogue_h
                ):
                    assert console.rgba["bg"][y, x, 3] == 255  # Dialogue area opaque
                else:
                    assert console.rgba["bg"][y, x, 3] == 0  # Rest transparent
