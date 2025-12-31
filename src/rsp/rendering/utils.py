#!/usr/bin/env python3
"""
Rogue Signal Protocol - Rendering Utilities

Shared rendering utility functions used across multiple rendering subsystems.
Extracted from game_rendering_core to prevent circular dependencies.
"""

import tcod

from rsp.entities.base import Colors, ensure_color_tuple
from rsp.ui.common import render_char_safe
from rsp.utils.unicode import GameGlyphs


def draw_bordered_box(
    console: tcod.console.Console,
    start_x: int,
    start_y: int,
    width: int,
    height: int,
    border_color: tuple,
    bg_color: tuple,
):
    """
    Draw a bordered box with background fill using TCOD primitives.

    Uses TCOD's built-in draw_rect and draw_frame for efficiency.
    Ensures color values are tuples to prevent TCOD ColorRGB errors.

    Args:
        console: TCOD console to draw on
        start_x: Left edge of box
        start_y: Top edge of box
        width: Box width in characters
        height: Box height in characters
        border_color: RGB tuple for border color
        bg_color: RGB tuple for background fill
    """
    # Ensure colors are tuples to prevent TCOD ColorRGB errors
    border_color = ensure_color_tuple(border_color)
    bg_color = ensure_color_tuple(bg_color)

    # Draw background
    console.draw_rect(start_x, start_y, width, height, ord(" "), fg=Colors.WHITE, bg=bg_color)

    # Draw double-line border manually (using GameGlyphs constants)
    # Top border
    render_char_safe(
        console, start_x, start_y, GameGlyphs.WALL_TOP_LEFT, fg=border_color, bg=bg_color
    )
    for x in range(start_x + 1, start_x + width - 1):
        render_char_safe(
            console, x, start_y, GameGlyphs.WALL_HORIZONTAL, fg=border_color, bg=bg_color
        )
    render_char_safe(
        console,
        start_x + width - 1,
        start_y,
        GameGlyphs.WALL_TOP_RIGHT,
        fg=border_color,
        bg=bg_color,
    )

    # Side borders
    for y in range(start_y + 1, start_y + height - 1):
        render_char_safe(
            console, start_x, y, GameGlyphs.WALL_VERTICAL, fg=border_color, bg=bg_color
        )
        render_char_safe(
            console, start_x + width - 1, y, GameGlyphs.WALL_VERTICAL, fg=border_color, bg=bg_color
        )

    # Bottom border
    render_char_safe(
        console,
        start_x,
        start_y + height - 1,
        GameGlyphs.WALL_BOTTOM_LEFT,
        fg=border_color,
        bg=bg_color,
    )
    for x in range(start_x + 1, start_x + width - 1):
        render_char_safe(
            console,
            x,
            start_y + height - 1,
            GameGlyphs.WALL_HORIZONTAL,
            fg=border_color,
            bg=bg_color,
        )
    render_char_safe(
        console,
        start_x + width - 1,
        start_y + height - 1,
        GameGlyphs.WALL_BOTTOM_RIGHT,
        fg=border_color,
        bg=bg_color,
    )
