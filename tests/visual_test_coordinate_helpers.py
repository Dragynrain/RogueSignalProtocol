#!/usr/bin/env python3
"""
Visual test for CoordinateHelpers.

This script creates a simple visual demonstration of the CoordinateHelpers
functionality by rendering boxes at various positions on a console.

Run this script manually to visually verify:
- center_box() positions boxes correctly
- set_alpha_region() affects the correct regions
- Coordinate calculations are accurate

Usage:
    python tests/visual_test_coordinate_helpers.py
"""

import tcod
import tcod.console
import tcod.event

from font_loader_freetype import load_truetype_font_custom
from game_coordinate_helpers import CoordinateHelpers


def render_box_outline(
    console: tcod.console.Console, x: int, y: int, width: int, height: int, color: tuple
):
    """Draw a box outline at the specified position."""
    # Top and bottom borders
    for i in range(width):
        if 0 <= x + i < console.width and 0 <= y < console.height:
            console.print(x + i, y, "-", fg=color)
        if 0 <= x + i < console.width and 0 <= y + height - 1 < console.height:
            console.print(x + i, y + height - 1, "-", fg=color)

    # Left and right borders
    for i in range(height):
        if 0 <= x < console.width and 0 <= y + i < console.height:
            console.print(x, y + i, "|", fg=color)
        if 0 <= x + width - 1 < console.width and 0 <= y + i < console.height:
            console.print(x + width - 1, y + i, "|", fg=color)

    # Corners
    if 0 <= x < console.width and 0 <= y < console.height:
        console.print(x, y, "+", fg=color)
    if 0 <= x + width - 1 < console.width and 0 <= y < console.height:
        console.print(x + width - 1, y, "+", fg=color)
    if 0 <= x < console.width and 0 <= y + height - 1 < console.height:
        console.print(x, y + height - 1, "+", fg=color)
    if 0 <= x + width - 1 < console.width and 0 <= y + height - 1 < console.height:
        console.print(x + width - 1, y + height - 1, "+", fg=color)


def main():
    """Run visual test of coordinate helpers."""
    # Create console
    console_width = 80
    console_height = 50
    console = tcod.console.Console(width=console_width, height=console_height)

    # Create TCOD context with KreativeSquare font (same as main game)
    tileset = load_truetype_font_custom("../KreativeSquare.ttf", 64, 64)
    with tcod.context.new(
        width=console_width,
        height=console_height,
        tileset=tileset,
        title="CoordinateHelpers Visual Test",
        vsync=True,
    ) as context:
        running = True
        test_stage = 0

        while running:
            console.clear()

            # Test different scenarios
            if test_stage == 0:
                # Test 1: Centered box
                console.print(2, 1, "Test 1: Centered Box (40x20)", fg=(255, 255, 255))
                console.print(2, 2, "Press SPACE for next test, ESC to exit", fg=(128, 128, 128))

                box_w, box_h = 40, 20
                x, y = CoordinateHelpers.center_box(box_w, box_h, console_width, console_height)
                render_box_outline(console, x, y, box_w, box_h, (0, 255, 0))

                # Show coordinates
                console.print(x + 2, y + 1, f"Position: ({x}, {y})", fg=(255, 255, 0))
                console.print(x + 2, y + 2, f"Size: {box_w}x{box_h}", fg=(255, 255, 0))

            elif test_stage == 1:
                # Test 2: Multiple centered boxes of different sizes
                console.print(2, 1, "Test 2: Multiple Centered Boxes", fg=(255, 255, 255))
                console.print(2, 2, "Press SPACE for next test, ESC to exit", fg=(128, 128, 128))

                boxes = [(60, 30), (40, 20), (20, 10)]
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

                for (box_w, box_h), color in zip(boxes, colors):
                    x, y = CoordinateHelpers.center_box(box_w, box_h, console_width, console_height)
                    render_box_outline(console, x, y, box_w, box_h, color)

            elif test_stage == 2:
                # Test 3: Alpha region visualization
                console.print(2, 1, "Test 3: Alpha Region (Opaque in center)", fg=(255, 255, 255))
                console.print(2, 2, "Green areas are opaque (alpha=255)", fg=(128, 128, 128))
                console.print(2, 3, "Press SPACE for next test, ESC to exit", fg=(128, 128, 128))

                # Make entire console transparent
                CoordinateHelpers.set_alpha_region(
                    console, 0, 0, console_width, console_height, alpha=0
                )

                # Make center region opaque
                box_w, box_h = 50, 25
                x, y = CoordinateHelpers.center_box(box_w, box_h, console_width, console_height)
                CoordinateHelpers.set_alpha_region(console, x, y, box_w, box_h, alpha=255)

                # Draw the opaque region (should show as green background)
                render_box_outline(console, x, y, box_w, box_h, (0, 255, 0))
                console.print(x + 2, y + 1, "OPAQUE REGION", fg=(255, 255, 0))
                console.print(x + 2, y + 2, "Alpha = 255", fg=(255, 255, 0))

            elif test_stage == 3:
                # Test 4: Bounds clamping
                console.print(2, 1, "Test 4: Bounds Clamping", fg=(255, 255, 255))
                console.print(2, 2, "Red: Original, Green: Clamped", fg=(128, 128, 128))
                console.print(2, 3, "Press SPACE for next test, ESC to exit", fg=(128, 128, 128))

                # Original box that exceeds bounds
                orig_x, orig_y, orig_w, orig_h = 70, 40, 20, 15

                # Show original position (red)
                console.print(
                    2, 5, f"Original: ({orig_x}, {orig_y}) {orig_w}x{orig_h}", fg=(255, 0, 0)
                )

                # Clamped box
                clamp_x, clamp_y, clamp_w, clamp_h = CoordinateHelpers.clamp_bounds(
                    orig_x, orig_y, orig_w, orig_h, console_width, console_height
                )
                render_box_outline(console, clamp_x, clamp_y, clamp_w, clamp_h, (0, 255, 0))

                console.print(
                    2, 6, f"Clamped: ({clamp_x}, {clamp_y}) {clamp_w}x{clamp_h}", fg=(0, 255, 0)
                )

            elif test_stage == 4:
                # Test 5: Pixel coordinate conversion
                console.print(2, 1, "Test 5: Char-to-Pixel Conversion", fg=(255, 255, 255))
                console.print(2, 2, "Console positions mapped to pixels", fg=(128, 128, 128))
                console.print(2, 3, "Press SPACE to restart, ESC to exit", fg=(128, 128, 128))

                # Simulate 1920x1080 window
                window_w, window_h = 1920, 1080

                test_positions = [
                    (0, 0),
                    (40, 25),
                    (79, 49),
                    (20, 10),
                ]

                y_offset = 5
                for console_x, console_y in test_positions:
                    pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
                        console_x, console_y, window_w, window_h
                    )

                    console.print(
                        5, y_offset, f"Console ({console_x:2d}, {console_y:2d})", fg=(255, 255, 0)
                    )
                    console.print(25, y_offset, "->", fg=(128, 128, 128))
                    console.print(
                        30, y_offset, f"Pixel ({pixel_x:4d}, {pixel_y:4d})", fg=(0, 255, 255)
                    )

                    y_offset += 2

            # Handle events
            context.present(console)

            for event in tcod.event.wait():
                if isinstance(event, tcod.event.Quit):
                    running = False
                elif isinstance(event, tcod.event.KeyDown):
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        running = False
                    elif event.sym == tcod.event.KeySym.SPACE:
                        test_stage = (test_stage + 1) % 5

        print("Visual test completed successfully!")


if __name__ == "__main__":
    main()
