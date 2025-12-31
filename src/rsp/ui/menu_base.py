#!/usr/bin/env python3
"""
Rogue Signal Protocol - Base Menu Class

Shared base class for all menu screens to eliminate duplication.
Provides common background detection, layout calculation, and rendering helpers.
Subclasses implement render() and execute_action() for specific menu behavior.
"""


import tcod

from rsp.core.config import GameConfig
from rsp.input.base import BaseInputHandler
from rsp.input.device_tracker import InputDeviceType, set_last_device
from rsp.ui.menu_utilities import MenuRenderingUtils


class BaseMenu(BaseInputHandler):
    """
    Base class for all menu screens with common functionality.

    Inherits unified input handling from BaseInputHandler.
    Provides shared methods for:
    - Unified keyboard/gamepad/mouse input (via BaseInputHandler)
    - Background detection
    - Layout calculation
    - Text area clearing
    - Box rendering

    Subclasses must implement:
    - render(console) - Main rendering method
    - get_context() - Return the appropriate InputContext
    - execute_action(action) - Handle InputAction values
    """

    def __init__(self, background=None):
        """
        Initialize base menu.

        Args:
            background: Optional MenuBackground instance
        """
        # Initialize input handling (game=None for menus, renderer set by game loop)
        super().__init__(game=None, renderer=None)

        # Menu-specific attributes
        self.background = background
        self.selected_option = 0
        self.options = []

    def navigate_up(self):
        """Navigate up in menu options (with wraparound)."""
        if self.options:
            self.selected_option = (self.selected_option - 1) % len(self.options)

    def navigate_down(self):
        """Navigate down in menu options (with wraparound)."""
        if self.options:
            self.selected_option = (self.selected_option + 1) % len(self.options)

    def _has_background(self) -> bool:
        """
        Check if background is available and should be displayed.

        Returns:
            True if background should be rendered, False otherwise
        """
        return (
            self.background
            and self.background.should_load_background()
            and self.background.background_texture
        )

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
                "title_x": GameConfig.SCREEN_WIDTH // 2,
                "menu_x": GameConfig.SCREEN_WIDTH // 2,
                "use_background_layout": False,
                "layout_zone": "center",
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

    def _render_right_side_box(
        self, console: tcod.console.Console, height: int, border_color: tuple, y_offset: int = 0
    ) -> int:
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

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS (implemented for menus)
    # ========================================================================

    def get_default_return(self) -> str:
        """Menus return empty string by default."""
        return ""

    # NOTE: get_context() and execute_action() must be implemented by subclasses

    # ========================================================================
    # RENDERING (menu-specific, not in BaseInputHandler)
    # ========================================================================

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the menu. Must be implemented by subclasses.

        Args:
            console: Console to render to

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement render()")

    # ========================================================================
    # MOUSE HANDLING (override BaseInputHandler defaults)
    # ========================================================================

    def handle_mouse_click(self, event) -> str:
        """
        Handle mouse click events - dispatch to left/right click handlers.

        This is the main entry point for mouse clicks from the game loop.
        Dispatches to handle_left_click or handle_right_click based on button.

        Args:
            event: Mouse button down event

        Returns:
            Action string (same as execute_action would return)
        """
        # Track input device for dynamic help text (mouse = keyboard mode)
        set_last_device(InputDeviceType.KEYBOARD)

        # Check if we have the button attribute
        if not hasattr(event, "button"):
            return ""

        # Dispatch to appropriate handler based on button
        if event.button == tcod.event.MouseButton.LEFT:
            return self.handle_left_click(event)
        elif event.button == tcod.event.MouseButton.RIGHT:
            return self.handle_right_click(event)

        # Unknown button - ignore
        return ""

    def handle_mouse_motion(self, event) -> str:
        """
        Handle mouse motion events - update selection based on hover.

        Default implementation for menus with vertical option lists.
        Subclasses can override for custom behavior.

        Args:
            event: Mouse motion event with tile coordinates

        Returns:
            Empty string (hover doesn't trigger action)
        """
        import logging

        if not self.options:
            return ""

        # Check for tile coordinates (set by MenuMouseHandler.convert_to_tile_coords)
        # Prefer event.tile, fall back to event.position for test compatibility
        # Use try/except because Mock objects pass hasattr checks
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break  # Found valid coordinates
                    except (TypeError, ValueError, AttributeError):
                        continue  # Try next attribute
        if tile_y is None:
            return ""

        # After MenuMouseHandler.convert_to_tile_coords(), coordinates are (0-79, 0-49)
        # Menu options Y position depends on graphics mode:
        # - Graphics mode (with background): start_y = 19
        # - Glyph mode: start_y = 21
        layout = self._get_menu_layout_params()
        start_y = 19 if layout["use_background_layout"] else 21
        spacing = 2

        if tile_y >= start_y:
            option_index = (tile_y - start_y) // spacing
            if 0 <= option_index < len(self.options):
                old_selection = self.selected_option
                self.selected_option = option_index
                logging.debug(
                    f"[MOUSE HOVER] Changed selection: {old_selection} -> {self.selected_option}"
                )

        return ""

    def handle_left_click(self, event) -> str:
        """
        Handle left mouse click - activate clicked option.

        Default implementation for menus with vertical option lists.
        Subclasses can override for custom behavior.

        Args:
            event: Mouse click event with tile coordinates

        Returns:
            Action string (same as execute_action would return)
        """
        if not self.options:
            return ""

        # Check for tile coordinates (set by MenuMouseHandler.convert_to_tile_coords)
        # Prefer event.tile, fall back to event.position for test compatibility
        # Use try/except because Mock objects pass hasattr checks
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break  # Found valid coordinates
                    except (TypeError, ValueError, AttributeError):
                        continue  # Try next attribute
        if tile_y is None:
            return ""

        # After MenuMouseHandler.convert_to_tile_coords(), coordinates are (0-79, 0-49)
        # Menu options Y position depends on graphics mode:
        # - Graphics mode (with background): start_y = 19
        # - Glyph mode: start_y = 21
        layout = self._get_menu_layout_params()
        start_y = 19 if layout["use_background_layout"] else 21
        spacing = 2

        # Calculate which option was clicked
        if tile_y >= start_y:
            option_index = (tile_y - start_y) // spacing

            if 0 <= option_index < len(self.options):
                # Update selection
                self.selected_option = option_index

                # Activate this option (same as pressing Enter)
                action = self._get_action_for_option(option_index)
                return action if action else ""

        return ""

    def handle_right_click(self, event) -> str:
        """
        Handle right mouse click - universal back/cancel.

        Args:
            event: Mouse click event

        Returns:
            "back" action string
        """
        # Headless mode check
        if self.renderer is None:
            return ""

        return "back"

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_action_for_option(self, option_index: int) -> str | None:
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
        elif "Ascension" in option_text:
            return "ascension"
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
