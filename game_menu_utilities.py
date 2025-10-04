#!/usr/bin/env python3
"""
Shared menu rendering utilities to eliminate duplication across menu classes.
Consolidated from game_menus.py refactoring.
"""

import tcod
from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe


class MenuRenderingUtils:
    """Shared utilities for menu rendering across MainMenu, SettingsMenu, etc."""

    @staticmethod
    def render_right_side_box(console: tcod.console.Console, layout: dict, height: int,
                              border_color: tuple, y_offset: int = 0) -> dict:
        """Render a right-side menu box with consistent positioning and styling.

        Args:
            console: The console to render to
            layout: Layout parameters from get_menu_layout_params()
            height: Height of the box
            border_color: Color for the box border
            y_offset: Vertical offset for positioning (0 = centered)

        Returns:
            dict: Box dimensions and positions for content rendering
        """
        if layout['use_background_layout']:
            # Graphics mode - narrow box on right side
            box_width = 28
            box_right = GameConfig.SCREEN_WIDTH - 2
            box_left = box_right - box_width

            if y_offset == 0:
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                box_top = y_offset

            box_bottom = box_top + height - 1

            # Ensure box fits within screen bounds
            box_top = max(1, min(box_top, GameConfig.SCREEN_HEIGHT - height - 1))
            box_bottom = box_top + height - 1

            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0),
                             bg_blend=tcod.constants.BKGND_SET)

            # Draw border with Unicode box characters
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, "│", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, "│", fg=border_color, bg=Colors.BLACK)
            for x in range(box_left, box_right + 1):
                render_char_safe(console, x, box_top, "─", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, "─", fg=border_color, bg=Colors.BLACK)

            # Box corners
            render_char_safe(console, box_left, box_top, "┌", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_top, "┐", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_left, box_bottom, "└", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_bottom, "┘", fg=border_color, bg=Colors.BLACK)

            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 1,
                'content_right': box_right - 1,
                'content_top': box_top + 1,
                'content_width': box_width - 2,
                'use_background_layout': True
            }
        else:
            # ASCII mode - larger centered box
            box_width = 50
            box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
            box_right = box_left + box_width - 1

            if y_offset == 0:
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                box_top = y_offset

            box_bottom = box_top + height - 1

            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0),
                             bg_blend=tcod.constants.BKGND_SET)

            # Draw simple ASCII border
            for x in range(box_left, box_left + box_width):
                render_char_safe(console, x, box_top, '=', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, '=', fg=border_color, bg=Colors.BLACK)
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, '|', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, '|', fg=border_color, bg=Colors.BLACK)

            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 2,
                'content_right': box_right - 2,
                'content_top': box_top + 1,
                'content_width': box_width - 4,
                'use_background_layout': False
            }

    @staticmethod
    def calculate_background_aware_layout(background) -> dict:
        """Calculate layout for background mode based on window dimensions.

        Args:
            background: MenuBackground instance or None

        Returns:
            dict: Layout parameters with positioning information
        """
        # Get actual window dimensions if available
        window_width, window_height = 800, 800  # Default fallback

        if background and background.window_manager:
            try:
                window_width, window_height = background.window_manager.get_window_pixel_dimensions()
            except (AttributeError, TypeError, ValueError):
                pass  # Use defaults if retrieval fails

        # Calculate dynamic positioning based on window aspect ratio
        aspect_ratio = window_width / window_height if window_height > 0 else 1.0

        # Position menu far right to avoid left-aligned background graphics
        if aspect_ratio > 1.2:
            # Wide window
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.85)
            layout_zone = 'right'
        elif aspect_ratio < 0.8:
            # Tall window
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.8)
            layout_zone = 'upper'
        else:
            # Square-ish window
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.82)
            layout_zone = 'right_center'

        # Ensure minimum margins
        min_margin = 5
        max_x = GameConfig.SCREEN_WIDTH - min_margin - 20
        text_x_offset = min(text_x_offset, max_x)
        text_x_offset = max(text_x_offset, min_margin + 10)

        return {
            'title_x': text_x_offset - 10,
            'menu_x': text_x_offset,
            'use_background_layout': True,
            'layout_zone': layout_zone,
            'window_aspect': aspect_ratio,
            'window_size': (window_width, window_height)
        }

    @staticmethod
    def clear_text_areas_only(console: tcod.console.Console, layout: dict) -> None:
        """Create separation: left 60% transparent for graphics, right 40% opaque for menu.

        Args:
            console: Console to clear
            layout: Layout parameters from get_menu_layout_params()
        """
        if layout['use_background_layout']:
            # ENFORCED SEPARATION: 60% graphics area, 40% menu area
            graphics_boundary = int(console.width * 0.6)

            # Left 60%: Make transparent for SDL graphics
            for y in range(console.height):
                for x in range(0, graphics_boundary):
                    console.rgba[x, y] = (
                        ord(' '),           # Empty character
                        (255, 255, 255, 0), # Transparent foreground
                        (0, 0, 0, 0)        # Transparent background
                    )

            # Right 40%: Clear for text menu (opaque)
            for y in range(console.height):
                for x in range(graphics_boundary, console.width):
                    render_char_safe(console, x, y, ' ', fg=(255, 255, 255), bg=(0, 0, 0))
        else:
            # ASCII mode: clear entire console
            console.clear()
