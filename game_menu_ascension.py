#!/usr/bin/env python3
"""
Ascension Selection Menu for Rogue Signal Protocol.

Provides a scrollable menu for selecting ascension level (0-20).
Shows lock/unlock state, cumulative modifiers, and victory counts.
"""

import logging

import tcod
import tcod.constants

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
    13: "Node Degradation",
    14: "Memory Constraints",
    15: "Network Cascade",
    16: "Exposed Topology",
    17: "Thermal Signature",
    18: "Streamlined Systems",
    19: "Node Scarcity",
    20: "Decaying Shadows",
}

# Modifier descriptions for display (player-friendly text)
MODIFIER_DESCRIPTIONS = {
    1: "Scanners +1 vision",
    2: "Enemies +10 CPU",
    3: "Trace builds faster over time",
    4: "Enemies deal +20% damage",
    5: "All enemies +1 vision",
    6: "Fewer blind spots per floor",
    7: "Detection raises trace faster",
    8: "Heat cools down slower",
    9: "+5 enemies per floor",
    10: "Player vision 15->12",
    11: "-2 codes per floor (min 3)",
    12: "Tougher enemy types spawn more often",
    13: "Nodes have limited uses",
    14: "Starting RAM 8->6",
    15: "Alert range 6->10",
    16: "More open level layouts",
    17: "Melee +5 heat",
    18: "-1 upgrades per floor",
    19: "-1 nodes per floor",
    20: "Blind spots vanish when you leave them",
}


class AscensionMenu(BaseMenu):
    """
    Ascension level selection menu.

    Displays all 21 ascension levels (0-20) with lock indicators,
    cumulative modifier descriptions, and navigation controls.
    """

    def __init__(
        self,
        highest_unlocked: int = 0,
        background=None,
        initial_level: int = 0,
        view_only: bool = False,
    ):
        """
        Initialize ascension menu.

        Args:
            highest_unlocked: Highest ascension level unlocked
            background: Optional MenuBackground instance
            initial_level: Initial selection (current ascension level)
            view_only: If True, shows info only (no selection changes during gameplay)
        """
        super().__init__(background)
        self.highest_unlocked = highest_unlocked
        self.total_levels = 21  # A0-A20
        self.current_selection = initial_level
        self.scroll_offset = 0  # For scrolling display
        self.visible_levels = 10  # How many levels visible at once
        self.view_only = view_only

        # Build options list for base class compatibility
        self.options = [f"A{i}" for i in range(self.total_levels)]

    @property
    def selected_level(self) -> int:
        """Alias for current_selection for external use."""
        return self.current_selection

    @selected_level.setter
    def selected_level(self, value: int) -> None:
        """Set selected level (alias for current_selection)."""
        self.current_selection = value

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
        return InputContext.ASCENSION_MENU

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

        # Title (show "CURRENT ASCENSION" in view_only mode)
        title = "CURRENT ASCENSION" if self.view_only else "ASCENSION"
        render_char_safe(
            console,
            box["center_x"] - len(title) // 2,
            box["top"] + 2,
            title,
            fg=Colors.ELECTRIC_PURPLE,
            bg=Colors.BLACK,
        )

        # Subtitle with current selection info (truncate to fit box)
        current_level = self.current_selection
        level_name = ASCENSION_NAMES.get(current_level, f"Ascension {current_level}")
        subtitle = f"A{current_level}: {level_name}"
        max_subtitle_width = box["content_width"] - 2
        if len(subtitle) > max_subtitle_width:
            subtitle = subtitle[: max_subtitle_width - 2] + ".."
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

        if self.view_only:
            # View-only mode: only show close controls
            controls = "N/Esc: Close" if not box["use_background_layout"] else "B: Close"
        elif box["use_background_layout"]:
            controls = "D-pad:Nav Enter:Select"
        else:
            # Shortened to fit within 50-char box (was overlapping frame)
            controls = "Arrows:Nav | Enter:Select | Esc:Back"

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
        # Must match render(): y_offset=3, menu_height=SCREEN_HEIGHT-4
        # Background: box_top = y_offset - 1 = 2, Glyph: box_top = y_offset = 3
        # Use _has_background() directly to match render behavior
        has_bg = self._has_background()
        box_top = 2 if has_bg else 3
        list_start_y = box_top + 6

        if list_start_y <= tile_y < list_start_y + self.visible_levels:
            clicked_index = tile_y - list_start_y
            clicked_level = self.scroll_offset + clicked_index

            if 0 <= clicked_level < self.total_levels:
                self.current_selection = clicked_level
                self._update_scroll()

                # In view_only mode, clicking just navigates
                if self.view_only:
                    return ""

                # Click selects and confirms (same as Enter key)
                result = self.confirm_selection()
                if result == "selected":
                    return "back"
                # Locked level - just update selection, no action
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
        # Must match render(): y_offset=3, menu_height=SCREEN_HEIGHT-4
        # Background: box_top = y_offset - 1 = 2, Glyph: box_top = y_offset = 3
        # Use _has_background() directly to match render behavior
        has_bg = self._has_background()
        box_top = 2 if has_bg else 3
        list_start_y = box_top + 6

        if list_start_y <= tile_y < list_start_y + self.visible_levels:
            hovered_index = tile_y - list_start_y
            hovered_level = self.scroll_offset + hovered_index

            if 0 <= hovered_level < self.total_levels:
                self.current_selection = hovered_level

        return ""

    def handle_mouse_wheel(self, event) -> str:
        """Handle mouse wheel - scroll through ascension levels."""
        if hasattr(event, "y"):
            if event.y > 0:
                # Scroll up
                for _ in range(3):
                    self.navigate_up()
            elif event.y < 0:
                # Scroll down
                for _ in range(3):
                    self.navigate_down()
        return ""


class AscensionUnlockScreen(BaseMenu):
    """
    Screen shown after victory when a new ascension level is unlocked.

    Displays:
    - "ASCENSION X UNLOCKED!" message
    - The new modifier description
    - Press Enter/click to continue
    """

    def __init__(self, unlocked_level: int, background=None):
        """
        Initialize unlock screen.

        Args:
            unlocked_level: The new ascension level that was unlocked (1-20)
            background: Optional MenuBackground instance
        """
        super().__init__(background)
        self.unlocked_level = unlocked_level
        self.level_name = ASCENSION_NAMES.get(unlocked_level, f"Ascension {unlocked_level}")
        self.modifier_desc = MODIFIER_DESCRIPTIONS.get(unlocked_level, "Unknown modifier")
        self.is_first_unlock = unlocked_level == 1

    def _get_explanation_text(self) -> list[str]:
        """Get explanation text for first-time unlock."""
        if self.is_first_unlock:
            return [
                "Ascension levels add permanent difficulty",
                "modifiers that stack as you progress.",
                "Beat your highest level to unlock more.",
            ]
        return []

    def get_context(self) -> InputContext:
        """Return unlock screen context (uses GAME_OVER like victory screen)."""
        return InputContext.GAME_OVER

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an action on the unlock screen.

        Args:
            action: The action to execute

        Returns:
            True if screen should close
        """
        if action in (InputAction.CONFIRM, InputAction.CANCEL):
            return True
        return False

    def render(self, console: tcod.console.Console) -> None:
        """Render the unlock screen."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        self._render_unlock_message(console)

    def _render_unlock_message(self, console: tcod.console.Console) -> None:
        """Render the unlock message with decorations."""
        use_background_layout = self._has_background()

        if use_background_layout:
            self._render_with_background(console)
        else:
            self._render_centered(console)

    def _render_with_background(self, console: tcod.console.Console) -> None:
        """Render unlock message in right-side box (background mode)."""
        # Taller box for first unlock to fit explanation
        box_height = 30 if self.is_first_unlock else 25

        # Render the right-side box
        box = self._render_right_side_box(console, box_height, Colors.CYAN, y_offset=0)

        # Title
        title = "ASCENSION UNLOCKED!"
        title_x = box["center_x"] - len(title) // 2
        render_char_safe(console, title_x, box["top"] + 3, title, fg=Colors.YELLOW, bg=Colors.BLACK)

        # Decorative line
        line_width = box["content_width"] - 4
        line_x = box["center_x"] - line_width // 2
        render_char_safe(
            console, line_x, box["top"] + 4, "=" * line_width, fg=Colors.CYAN, bg=Colors.BLACK
        )

        y_offset = 0

        # First unlock explanation - use word wrapping to fit in box
        explanation = self._get_explanation_text()
        if explanation:
            # Join explanation lines and word-wrap within box width
            explanation_text = " ".join(explanation)
            wrap_width = box["content_width"] - 2
            lines_printed = console.print(
                x=box["content_left"] + 1,
                y=box["top"] + 6,
                string=explanation_text,
                fg=(200, 200, 200),
                width=wrap_width,
            )
            y_offset = lines_printed + 1

        # Level info - use word wrapping for long names
        level_text = f"A{self.unlocked_level}: {self.level_name}"
        wrap_width = box["content_width"] - 2
        if len(level_text) <= wrap_width:
            # Short enough to center
            level_x = box["center_x"] - len(level_text) // 2
            render_char_safe(
                console,
                level_x,
                box["top"] + 7 + y_offset,
                level_text,
                fg=Colors.GREEN,
                bg=Colors.BLACK,
            )
        else:
            # Use word wrap
            console.print(
                x=box["content_left"] + 1,
                y=box["top"] + 7 + y_offset,
                string=level_text,
                fg=Colors.GREEN,
                width=wrap_width,
            )

        # New modifier
        new_text = "NEW MODIFIER:"
        new_x = box["center_x"] - len(new_text) // 2
        render_char_safe(
            console, new_x, box["top"] + 10 + y_offset, new_text, fg=Colors.WHITE, bg=Colors.BLACK
        )

        # Modifier description - use word wrapping for long descriptions
        if len(self.modifier_desc) <= wrap_width:
            # Short enough to center
            modifier_x = box["center_x"] - len(self.modifier_desc) // 2
            render_char_safe(
                console,
                modifier_x,
                box["top"] + 12 + y_offset,
                self.modifier_desc,
                fg=Colors.CYAN,
                bg=Colors.BLACK,
            )
        else:
            # Use word wrap
            console.print(
                x=box["content_left"] + 1,
                y=box["top"] + 12 + y_offset,
                string=self.modifier_desc,
                fg=Colors.CYAN,
                width=wrap_width,
            )

        # Narrative text - use word wrapping to fit in box
        narrative = "The network has adapted to your tactics."
        wrap_width = box["content_width"] - 2
        console.print(
            x=box["content_left"] + 1,
            y=box["top"] + 16 + y_offset,
            string=narrative,
            fg=(150, 150, 150),
            width=wrap_width,
        )

        # Prompt
        prompt = "[Press Enter to continue]"
        prompt_x = box["center_x"] - len(prompt) // 2
        render_char_safe(
            console, prompt_x, box["bottom"] - 3, prompt, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK
        )

    def _render_centered(self, console: tcod.console.Console) -> None:
        """Render unlock message centered (glyph mode)."""
        center_x = console.width // 2
        start_y = 10 if self.is_first_unlock else 12

        # Title with decoration
        title = "====== ASCENSION UNLOCKED! ======"
        title_x = center_x - len(title) // 2
        render_char_safe(console, title_x, start_y, title, fg=Colors.YELLOW, bg=Colors.BLACK)

        y_offset = 0

        # First unlock explanation - use word wrapping for consistency
        explanation = self._get_explanation_text()
        if explanation:
            explanation_text = " ".join(explanation)
            lines_printed = console.print(
                x=center_x - 30,  # Center a 60-char wide block
                y=start_y + 3,
                string=explanation_text,
                fg=(200, 200, 200),
                width=60,
                alignment=tcod.constants.CENTER,
            )
            y_offset = lines_printed + 1

        # Level info
        level_text = f"A{self.unlocked_level}: {self.level_name}"
        level_x = center_x - len(level_text) // 2
        render_char_safe(
            console, level_x, start_y + 4 + y_offset, level_text, fg=Colors.GREEN, bg=Colors.BLACK
        )

        # New modifier
        new_text = "NEW MODIFIER:"
        new_x = center_x - len(new_text) // 2
        render_char_safe(
            console, new_x, start_y + 7 + y_offset, new_text, fg=Colors.WHITE, bg=Colors.BLACK
        )

        modifier_x = center_x - len(self.modifier_desc) // 2
        render_char_safe(
            console,
            modifier_x,
            start_y + 9 + y_offset,
            self.modifier_desc,
            fg=Colors.CYAN,
            bg=Colors.BLACK,
        )

        # Narrative text - use word wrapping for consistency
        narrative = "The network has adapted to your tactics."
        console.print(
            x=center_x - 30,  # Center a 60-char wide block
            y=start_y + 13 + y_offset,
            string=narrative,
            fg=(150, 150, 150),
            width=60,
            alignment=tcod.constants.CENTER,
        )

        # Prompt
        prompt = "[Press Enter to continue]"
        prompt_x = center_x - len(prompt) // 2
        render_char_safe(
            console,
            prompt_x,
            start_y + 17 + y_offset,
            prompt,
            fg=Colors.ELECTRIC_PURPLE,
            bg=Colors.BLACK,
        )

    def handle_input(self, event: tcod.event.Event) -> bool:
        """
        Handle input for unlock screen.

        Args:
            event: TCOD event

        Returns:
            True if screen should close
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in [
                tcod.event.KeySym.SPACE,
                tcod.event.KeySym.RETURN,
                tcod.event.KeySym.KP_ENTER,
                tcod.event.KeySym.ESCAPE,
            ]:
                return True
        elif isinstance(event, tcod.event.MouseButtonDown):
            return True
        return False
