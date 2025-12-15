#!/usr/bin/env python3
"""
Ascension Selection Menu for Rogue Signal Protocol.

Provides a scrollable menu for selecting ascension level (0-20).
Shows lock/unlock state, cumulative modifiers, and victory counts.
"""

import logging

import tcod

from game_ascension import calculate_ascension_modifiers
from game_color_manager import ColorManager
from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_input_actions import InputAction, InputContext
from game_menu_base import BaseMenu
from game_ui import render_char_safe


# Ascension level names for display
ASCENSION_NAMES = {
    0: "Base Game",
    1: "Enhanced Monitoring",
    2: "Hardened Processes",
    3: "Residual Signatures",
    4: "Aggressive Protocols",
    5: "Wide-Spectrum Sensors",
    6: "Shrinking Shadows",
    7: "Trace Persistence",
    8: "Thermal Decay",
    9: "Crowded Networks",
    10: "Signal Fog",
    11: "Data Drought",
    12: "Threat Escalation",
    13: "Degraded Infrastructure",
    14: "Memory Constraints",
    15: "Network Cascade",
    16: "Exposed Topology",
    17: "Thermal Signature",
    18: "Streamlined Systems",
    19: "Failing Infrastructure",
    20: "Decaying Shadows",
}

# Modifier descriptions for display (player-friendly text)
MODIFIER_DESCRIPTIONS = {
    1: "Scanner +1 vision",
    2: "Enemies +10 CPU",
    3: "2x trace gain",
    4: "+20% enemy damage",
    5: "All enemies +1 vision",
    6: "-1% blind spots/floor",
    7: "+0.2 hostile trace",
    8: "Heat reduction halved",
    9: "+5 enemies/floor",
    10: "Player vision 15->12",
    11: "-2 codes/floor (min 3)",
    12: "Tougher enemy mix",
    13: "Nodes have capacity",
    14: "Starting RAM 8->6",
    15: "Alert range 6->10",
    16: "Open map generation",
    17: "Melee +5 heat",
    18: "-1 upgrades/floor",
    19: "-1 nodes/floor",
    20: "Blind spots consumed",
}


class AscensionMenu(BaseMenu):
    """
    Ascension level selection menu.

    Displays all 21 ascension levels (0-20) with lock indicators,
    cumulative modifier descriptions, and navigation controls.
    """

    def __init__(self, highest_unlocked: int = 0, background=None, initial_level: int = 0):
        """
        Initialize ascension menu.

        Args:
            highest_unlocked: Highest ascension level unlocked
            background: Optional MenuBackground instance
            initial_level: Initial selection (current ascension level)
        """
        super().__init__(background)
        self.highest_unlocked = highest_unlocked
        self.total_levels = 21  # A0-A20
        self.current_selection = initial_level
        self.scroll_offset = 0  # For scrolling display
        self.visible_levels = 10  # How many levels visible at once

        # Build options list for base class compatibility
        self.options = [f"A{i}" for i in range(self.total_levels)]

    def is_level_selectable(self, level: int) -> bool:
        """
        Check if a level can be selected.

        Args:
            level: Ascension level (0-20)

        Returns:
            True if level is unlocked and selectable
        """
        return 0 <= level <= self.highest_unlocked

    def get_modifiers_for_level(self, level: int) -> str:
        """
        Get modifier description string for a level.

        Returns cumulative modifiers for unlocked levels,
        or "???" for locked levels.

        Args:
            level: Ascension level (0-20)

        Returns:
            Modifier description string
        """
        if level > self.highest_unlocked:
            return "???"

        if level == 0:
            return "Base game - no modifiers"

        # Build cumulative modifier list
        modifiers = []
        for lv in range(1, level + 1):
            if lv in MODIFIER_DESCRIPTIONS:
                modifiers.append(MODIFIER_DESCRIPTIONS[lv])

        return ", ".join(modifiers) if modifiers else "Base game - no modifiers"

    def navigate_up(self):
        """Navigate up in level list with wraparound."""
        self.current_selection = (self.current_selection - 1) % self.total_levels
        self._update_scroll()

    def navigate_down(self):
        """Navigate down in level list with wraparound."""
        self.current_selection = (self.current_selection + 1) % self.total_levels
        self._update_scroll()

    def _update_scroll(self):
        """Update scroll offset to keep selection visible."""
        # Keep selection in visible range
        if self.current_selection < self.scroll_offset:
            self.scroll_offset = self.current_selection
        elif self.current_selection >= self.scroll_offset + self.visible_levels:
            self.scroll_offset = self.current_selection - self.visible_levels + 1

    def get_selected_level(self) -> int:
        """Get the currently selected level."""
        return self.current_selection

    def confirm_selection(self) -> str:
        """
        Confirm the current selection.

        Returns:
            "selected" if level is unlocked and saved
            "locked" if level is locked
        """
        if not self.is_level_selectable(self.current_selection):
            return "locked"

        # Save selection to settings
        settings = GameSettings.get_instance()
        settings.set_ascension_level(self.current_selection)
        logging.info(f"Ascension level set to A{self.current_selection}")
        return "selected"

    def get_context(self) -> InputContext:
        """Return input context for this menu."""
        return InputContext.SETTINGS  # Uses same context as settings menus

    def execute_action(self, action: InputAction) -> str:
        """
        Execute an action on the menu.

        Args:
            action: The action to execute

        Returns:
            Action string ("back", "selected", or "")
        """
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self.navigate_up()
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self.navigate_down()
            return ""
        elif action == InputAction.CONFIRM:
            result = self.confirm_selection()
            if result == "selected":
                return "back"  # Return to main menu after selection
            # Locked - play error sound or flash
            return ""
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    def render(self, console: tcod.console.Console) -> None:
        """Render the ascension selection menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Calculate menu height
        menu_height = GameConfig.SCREEN_HEIGHT - 4

        # Get UI color for decorations
        settings = GameSettings.get_instance()
        ui_color = settings.get_ui_color_rgb() if settings else Colors.CYAN

        # Render the right-side box
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)

        # Title
        title = "ASCENSION"
        if box["use_background_layout"]:
            render_char_safe(
                console,
                box["center_x"] - len(title) // 2,
                box["top"] + 2,
                title,
                fg=Colors.ELECTRIC_PURPLE,
                bg=Colors.BLACK,
            )
        else:
            render_char_safe(
                console,
                box["center_x"] - len(title) // 2,
                box["top"] + 2,
                title,
                fg=Colors.ELECTRIC_PURPLE,
                bg=Colors.BLACK,
            )

        # Subtitle with current selection info
        current_level = self.current_selection
        level_name = ASCENSION_NAMES.get(current_level, f"Ascension {current_level}")
        subtitle = f"A{current_level}: {level_name}"
        render_char_safe(
            console,
            box["center_x"] - len(subtitle) // 2,
            box["top"] + 4,
            subtitle,
            fg=Colors.CYAN,
            bg=Colors.BLACK,
        )

        # Render level list
        self._render_level_list(console, box)

        # Render modifier details for selected level
        self._render_modifier_details(console, box)

        # Render controls help
        self._render_controls(console, box)

    def _render_level_list(self, console: tcod.console.Console, box: dict) -> None:
        """Render the scrollable level list."""
        list_start_y = box["top"] + 6
        list_x = box["center_x"] - 10

        # Show scroll indicator at top if needed
        if self.scroll_offset > 0:
            render_char_safe(
                console, box["center_x"], list_start_y - 1, "^", fg=Colors.CYAN, bg=Colors.BLACK
            )

        # Render visible levels
        for i in range(self.visible_levels):
            level = self.scroll_offset + i
            if level >= self.total_levels:
                break

            y = list_start_y + i

            # Determine level state
            is_selected = level == self.current_selection
            is_unlocked = self.is_level_selectable(level)

            # Choose colors
            if is_selected:
                fg_color = Colors.YELLOW
                bg_color = ColorManager.get("backgrounds", "menu_highlight")
                prefix = "> "
            elif is_unlocked:
                fg_color = Colors.WHITE
                bg_color = Colors.BLACK
                prefix = "  "
            else:
                fg_color = Colors.DARK_GRAY
                bg_color = Colors.BLACK
                prefix = "  "

            # Lock indicator
            lock = "" if is_unlocked else "[X]"

            # Level text
            level_text = f"{prefix}A{level:2d} {lock}"
            render_char_safe(console, list_x, y, level_text, fg=fg_color, bg=bg_color)

        # Show scroll indicator at bottom if needed
        if self.scroll_offset + self.visible_levels < self.total_levels:
            render_char_safe(
                console,
                box["center_x"],
                list_start_y + self.visible_levels,
                "v",
                fg=Colors.CYAN,
                bg=Colors.BLACK,
            )

    def _render_modifier_details(self, console: tcod.console.Console, box: dict) -> None:
        """Render modifier details for selected level."""
        details_y = box["top"] + 18
        details_x = box["content_left"] + 1
        max_width = box["content_width"] - 2

        # Get modifiers for selected level
        modifiers = self.get_modifiers_for_level(self.current_selection)

        # Header
        render_char_safe(
            console, details_x, details_y, "Modifiers:", fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK
        )

        # Word-wrap the modifiers text
        if modifiers == "???":
            render_char_safe(
                console, details_x, details_y + 1, "???", fg=Colors.DARK_GRAY, bg=Colors.BLACK
            )
        else:
            # Split by comma and render each modifier
            mod_list = modifiers.split(", ")
            y = details_y + 1
            for mod in mod_list:
                if y < box["bottom"] - 4:  # Leave room for controls
                    render_char_safe(
                        console,
                        details_x,
                        y,
                        f"- {mod[:max_width - 2]}",
                        fg=Colors.CYAN,
                        bg=Colors.BLACK,
                    )
                    y += 1

    def _render_controls(self, console: tcod.console.Console, box: dict) -> None:
        """Render control hints."""
        controls_y = box["bottom"] - 2

        if box["use_background_layout"]:
            controls = "D-pad:Nav Enter:Select"
        else:
            controls = "Arrow Keys: Navigate | Enter: Select | Esc: Back"

        render_char_safe(
            console,
            box["center_x"] - len(controls) // 2,
            controls_y,
            controls,
            fg=Colors.CYAN,
            bg=Colors.BLACK,
        )

    def handle_left_click(self, event) -> str:
        """Handle left mouse click on level list."""
        # Get tile coordinates
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break
                    except (TypeError, ValueError, AttributeError):
                        continue

        if tile_y is None:
            return ""

        # Calculate which level was clicked
        layout = self._get_menu_layout_params()
        box_top = 5 if layout["use_background_layout"] else 5
        list_start_y = box_top + 6

        if list_start_y <= tile_y < list_start_y + self.visible_levels:
            clicked_index = tile_y - list_start_y
            clicked_level = self.scroll_offset + clicked_index

            if 0 <= clicked_level < self.total_levels:
                self.current_selection = clicked_level

                # Double-click behavior: if clicking already selected, confirm
                return ""

        return ""

    def handle_mouse_motion(self, event) -> str:
        """Handle mouse motion for hover highlighting."""
        # Get tile coordinates
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break
                    except (TypeError, ValueError, AttributeError):
                        continue

        if tile_y is None:
            return ""

        # Calculate which level is hovered
        layout = self._get_menu_layout_params()
        box_top = 5 if layout["use_background_layout"] else 5
        list_start_y = box_top + 6

        if list_start_y <= tile_y < list_start_y + self.visible_levels:
            hovered_index = tile_y - list_start_y
            hovered_level = self.scroll_offset + hovered_index

            if 0 <= hovered_level < self.total_levels:
                self.current_selection = hovered_level

        return ""
