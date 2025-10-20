#!/usr/bin/env python3
"""
Rogue Signal Protocol - Base Menu Class

Shared base class for all menu screens to eliminate duplication.
Provides common background detection, layout calculation, and rendering helpers.
Subclasses implement render() and handle_input() for specific menu behavior.
"""

import tcod
from typing import Optional

from game_config import GameConfig
from game_menu_utilities import MenuRenderingUtils


class BaseMenu:
    """
    Base class for all menu screens with common functionality.

    Provides shared methods for:
    - Background detection
    - Layout calculation
    - Text area clearing
    - Box rendering

    Subclasses must implement:
    - render(console) - Main rendering method
    - handle_input(event) - Input handling logic
    """

    def __init__(self, background=None):
        """
        Initialize base menu.

        Args:
            background: Optional MenuBackground instance
        """
        self.background = background
        self.selected_option = 0
        self.options = []

    def _has_background(self) -> bool:
        """
        Check if background is available and should be displayed.

        Returns:
            True if background should be rendered, False otherwise
        """
        return (self.background and
                self.background.should_load_background() and
                self.background.background_texture)

    def _get_menu_layout_params(self) -> dict:
        """
        Calculate menu positioning based on graphics mode and background.

        Returns:
            Dict with layout parameters:
            - title_x: X position for title
            - menu_x: X position for menu items
            - use_background_layout: Whether using background layout
            - layout_zone: 'center' or 'right'
        """
        if self._has_background():
            return self._calculate_background_aware_layout()
        else:
            # Glyph mode or no background - center everything
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }

    def _calculate_background_aware_layout(self) -> dict:
        """
        Calculate layout when background is present.

        Uses MenuRenderingUtils for consistent calculation.

        Returns:
            Dict with layout parameters
        """
        return MenuRenderingUtils.calculate_background_aware_layout(self.background)

    def _clear_text_areas_only(self, console: tcod.console.Console) -> None:
        """
        Clear text areas while preserving background graphics.

        Creates separation: left portion transparent for graphics,
        right portion opaque for menu text.

        Args:
            console: Console to clear
        """
        layout = self._get_menu_layout_params()
        MenuRenderingUtils.clear_text_areas_only(console, layout)

    def _render_right_side_box(self, console: tcod.console.Console,
                               height: int, border_color: tuple, y_offset: int = 0) -> int:
        """
        Render menu box using shared utilities.

        Args:
            console: Console to render to
            height: Box height in characters
            border_color: RGB tuple for border
            y_offset: Vertical offset from center

        Returns:
            Start Y position of the box
        """
        layout = self._get_menu_layout_params()
        return MenuRenderingUtils.render_right_side_box(
            console, layout, height, border_color, y_offset
        )

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the menu. Must be implemented by subclasses.

        Args:
            console: Console to render to

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement render()")

    def handle_input(self, event) -> Optional[str]:
        """
        Handle input events. Must be implemented by subclasses.

        Args:
            event: Input event to handle

        Returns:
            Action string or None

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement handle_input()")
