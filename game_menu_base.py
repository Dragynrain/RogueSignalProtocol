#!/usr/bin/env python3
"""
Rogue Signal Protocol - Base Menu Class

Shared base class for all menu screens to eliminate duplication.
Provides common background detection, layout calculation, and rendering helpers.
Subclasses implement render() and handle_input() for specific menu behavior.
"""

import logging
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
        Handle input events. Must be implemented by subclass.

        Args:
            event: Input event to handle

        Returns:
            Action string or None

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement handle_input()")

    def handle_mouse_motion(self, event) -> bool:
        """
        Handle mouse motion events - update selection based on hover.

        Default implementation for menus with vertical option lists.
        Subclasses can override for custom behavior.

        Args:
            event: Mouse motion event with tile coordinates

        Returns:
            True if event was handled, False otherwise
        """
        if not self.options:
            return False

        # Check if position coordinates are available (tile is deprecated)
        if not hasattr(event, 'position') or event.position is None:
            return False

        # After context.convert_event(), position contains TILE coordinates
        tile_x = int(event.position.x)
        tile_y = int(event.position.y)

        # Menu options start at Y=21 (original position, box itself is shifted)
        start_y = 21
        spacing = 2

        # Calculate which option was hovered
        if tile_y >= start_y:
            option_index = (tile_y - start_y) // spacing
            if 0 <= option_index < len(self.options):
                self.selected_option = option_index
                return True

        return False

    def handle_mouse_click(self, event) -> Optional[str]:
        """
        Handle mouse click events - activate clicked option.

        Default implementation for menus with vertical option lists.
        Subclasses can override for custom behavior.

        Args:
            event: Mouse click event with tile coordinates

        Returns:
            Action string (same as handle_input would return), or None
        """
        if not self.options:
            return None

        # Check if position coordinates are available (tile is deprecated)
        if not hasattr(event, 'position') or event.position is None:
            return None

        # After context.convert_event(), position contains TILE coordinates (0-79, 0-49)
        tile_x = int(event.position.x)
        tile_y = int(event.position.y)

        # Menu options start at Y=21 (original position, box itself is shifted)
        start_y = 21
        spacing = 2

        # Calculate which option was clicked
        if tile_y >= start_y:
            option_index = (tile_y - start_y) // spacing

            if 0 <= option_index < len(self.options):
                # Update selection
                self.selected_option = option_index

                # Activate this option (same as pressing Enter)
                action = self._get_action_for_option(option_index)
                return action

        return None

    def _get_action_for_option(self, option_index: int) -> Optional[str]:
        """
        Get the action string for a menu option.

        Default implementation maps option text to action.
        Subclasses can override for custom action mapping.

        Args:
            option_index: Index of the selected option

        Returns:
            Action string, or None
        """
        if option_index < 0 or option_index >= len(self.options):
            return None

        option_text = self.options[option_index]

        # Map option text to action (same logic as keyboard input)
        if "Continue" in option_text:
            return "continue"
        elif "New Game" in option_text:
            return "new_game"
        elif "Settings" in option_text:
            return "settings"
        elif "Help" in option_text:
            return "help"
        elif "Achievements" in option_text:
            return "achievements"
        elif "Data Fragments" in option_text:
            return "lore"
        elif "About" in option_text:
            return "about"
        elif "Graphics Preview" in option_text:
            return "graphics_preview"
        elif "Exit" in option_text:
            return "exit"
        elif "Back" in option_text:
            return "back"

        return None
