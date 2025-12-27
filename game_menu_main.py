#!/usr/bin/env python3
"""
Main Menu for Rogue Signal Protocol.

Provides the primary game menu with options for:
- Continue/New Game
- Settings, Help, Achievements
- Data Fragments, About
- Graphics Preview (when in graphics mode)
- Exit (with save prompt)
"""

import logging

import tcod

from game_color_manager import ColorManager
from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_help_hints import get_main_menu_help
from game_menu_base import BaseMenu
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_ui import render_char_safe


class MainMenu(BaseMenu):
    """
    Main menu for game launch and mid-game access.

    Provides options: Continue, New Game, Settings, Help, Achievements, Data Fragments, Graphics Preview, Exit.
    Dynamically adjusts options based on save file existence and mid-game context.
    Shows confirmation dialog for destructive actions (New Game when save exists).

    Key attributes:
        options: Current menu options list (refreshed dynamically)
        show_warning: Whether new game warning dialog is active
        mid_game_mode: True when accessed from in-game (hides Continue option)
    """

    def __init__(self, background=None, menus=None):
        super().__init__(background)
        self.menus = menus  # Reference to menus dict to check if graphics_preview_menu exists
        self.options = self._build_options_list()
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game
        self.last_action = None  # Track last menu action for selection memory

        # Stored coordinates for warning dialog click detection
        self.warning_option_0_x_range = None  # (start_x, end_x) for "Yes, Delete"
        self.warning_option_1_x_range = None  # (start_x, end_x) for "No, Go Back"
        self.warning_option_0_y = None  # Y coordinate for "Yes, Delete"
        self.warning_option_1_y = None  # Y coordinate for "No, Go Back"

    @property
    def settings(self):
        """Get settings from global singleton."""
        return GameSettings.get_instance()

    def restore_selection_after_submenu(self):
        """Restore menu selection to the item that was selected when entering a submenu."""
        if self.last_action:
            # Map actions to option names
            action_to_option = {
                "ascension": "Ascension",  # Partial match OK since it has (A#) suffix
                "settings": "Settings",
                "controls": "Controls",
                "help": "Help",
                "achievements": "Achievements",
                "lore": "Data Fragments",  # Partial match OK since it has count suffix
                "about": "About",
                "graphics_preview": "Graphics Preview",
            }

            target_option = action_to_option.get(self.last_action)
            if target_option:
                # Find the option (handle partial matches for "Data Fragments (X/Y)")
                for i, option in enumerate(self.options):
                    if target_option in option or option == target_option:
                        self.selected_option = i
                        break
            self.last_action = None  # Clear after restoring

    def _build_options_list(self):
        """Build the options list based on save state and graphics mode."""
        # Get fragment count for menu display
        story_manager = StoryFragmentManager()
        discovered, total = story_manager.get_fragment_count()

        base_options = [
            "New Game",
        ]

        # Only show Ascension option if A1+ is unlocked
        if self.settings and self.settings.get_highest_ascension_unlocked() > 0:
            current_level = self.settings.get_ascension_level()
            base_options.append(f"Ascension (A{current_level})")

        base_options.extend(
            [
                "Settings",
                "Controls",
                "Help",
                "Achievements",
                f"Data Fragments ({discovered}/{total})",
                "About",
            ]
        )

        # Only show Graphics Preview if in graphics mode AND the menu exists
        if (
            self.settings
            and self.settings.graphics_mode == "graphics"
            and self.menus
            and "graphics_preview_menu" in self.menus
        ):
            base_options.append("Graphics Preview")

        base_options.append("Exit")

        # Add Continue Game at the start if save exists
        if SaveGameManager.save_exists():
            save_info = SaveGameManager.get_save_info()
            if save_info and save_info.get("ascension_level", 0) > 0:
                continue_text = f"Continue (A{save_info['ascension_level']})"
            else:
                continue_text = "Continue"
            return [continue_text] + base_options
        return base_options

    def refresh_options(self, show_continue: bool = True, active_game=None) -> None:
        """
        Refresh menu options.

        Args:
            show_continue: Set False when accessed from mid-game
            active_game: If provided, indicates there's an active game that will be saved on exit
        """
        # Track if there's an active game in memory that can be saved
        # Don't allow saving if player is dead (cpu <= 0 or game_over)
        can_save = (
            active_game is not None and active_game.player.cpu > 0 and not active_game.game_over
        )

        # Determine Exit button text based on whether there's a game to save
        exit_text = "Save and Exit" if can_save else "Exit"

        # Get fragment count for menu display
        story_manager = StoryFragmentManager()
        discovered, total = story_manager.get_fragment_count()

        # Build base options
        base_options = [
            "New Game",
        ]

        # Only show Ascension option if A1+ is unlocked
        if self.settings and self.settings.get_highest_ascension_unlocked() > 0:
            current_level = self.settings.get_ascension_level()
            base_options.append(f"Ascension (A{current_level})")

        base_options.extend(
            [
                "Settings",
                "Controls",
                "Help",
                "Achievements",
                f"Data Fragments ({discovered}/{total})",
                "About",
            ]
        )

        # Only show Graphics Preview if in graphics mode AND the menu exists
        if (
            self.settings
            and self.settings.graphics_mode == "graphics"
            and self.menus
            and "graphics_preview_menu" in self.menus
        ):
            base_options.append("Graphics Preview")

        base_options.append(exit_text)

        if show_continue and SaveGameManager.save_exists():
            save_info = SaveGameManager.get_save_info()
            if save_info and save_info.get("ascension_level", 0) > 0:
                continue_text = f"Continue (A{save_info['ascension_level']})"
            else:
                continue_text = "Continue"
            self.options = [continue_text] + base_options
        else:
            self.options = base_options

        # mid_game_mode = True when there's an active game that can be resumed
        # This enables START button to toggle back to game
        self.mid_game_mode = can_save  # True when active_game is valid and player is alive

        # Reset selection to prevent index out of bounds
        self.selected_option = 0
        # Reset warning state when refreshing options
        self.show_warning = False

    def render(self, console: tcod.console.Console) -> None:
        """Render the main menu with optional background."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        if self.show_warning:
            self._render_warning_dialog(console)
        else:
            self._render_main_menu(console)

    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu screen."""
        self._render_enhanced_menu(console)

    def _render_enhanced_menu(self, console: tcod.console.Console) -> None:
        """Render an enhanced menu with dynamic positioning based on background state."""
        # Calculate menu height based on content
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Full height for main menu

        # Get UI color from settings for border
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)

        # Render each section of the menu
        self._render_menu_title(console, box)
        self._render_version_info(console, box)
        self._render_menu_options(console, box)
        self._render_save_info(console, box)
        self._render_controls_help(console, box)

    def _render_menu_title(self, console: tcod.console.Console, box: dict) -> None:
        """Render the main menu title and decorations."""
        version = "Version 0.9.0 Beta"
        subtitle = "Cyberspace Stealth Exfiltration"

        # Get UI color from settings
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        if box["use_background_layout"]:
            # Title content within narrow box - split into multiple lines to fit
            render_char_safe(
                console, box["center_x"] - 10, 6, "═" * 20, fg=ui_color, bg=Colors.BLACK
            )
            # Split title into multiple lines
            render_char_safe(
                console, box["center_x"] - 6, 7, "ROGUE SIGNAL", fg=ui_color, bg=Colors.BLACK
            )
            render_char_safe(
                console, box["center_x"] - 4, 8, "PROTOCOL", fg=ui_color, bg=Colors.BLACK
            )
            # Center the version properly in the box
            version_x = box["center_x"] - len(version) // 2
            render_char_safe(
                console, version_x, 9, version, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK
            )
            # Split subtitle into two lines
            render_char_safe(
                console, box["center_x"] - 8, 11, "Cyberspace Stealth", fg=ui_color, bg=Colors.BLACK
            )
            render_char_safe(
                console, box["center_x"] - 6, 12, "Exfiltration", fg=ui_color, bg=Colors.BLACK
            )
            render_char_safe(
                console, box["center_x"] - 10, 13, "═" * 20, fg=ui_color, bg=Colors.BLACK
            )
        else:
            # Glyph mode - centered positioning
            title = "ROGUE SIGNAL PROTOCOL"
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - 20,
                6,
                "═" * 40,
                fg=ui_color,
                bg=Colors.BLACK,
            )
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - len(title) // 2,
                8,
                title,
                fg=ui_color,
                bg=Colors.BLACK,
            )
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2,
                9,
                subtitle,
                fg=ui_color,
                bg=Colors.BLACK,
            )
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - 20,
                10,
                "═" * 40,
                fg=ui_color,
                bg=Colors.BLACK,
            )

    def _render_version_info(self, console: tcod.console.Console, box: dict) -> None:
        """Render author information."""
        author_info = "by Adam Forster"

        # Use bright cyan for all control hints
        help_text_color = Colors.CYAN

        if box["use_background_layout"]:
            # Background mode - position within narrow box
            render_char_safe(
                console,
                box["center_x"] - len(author_info) // 2,
                15,
                author_info,
                fg=help_text_color,
                bg=Colors.BLACK,
            )
        else:
            # Glyph mode - centered
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - len(author_info) // 2,
                11,
                author_info,
                fg=help_text_color,
                bg=Colors.BLACK,
            )

    def _render_menu_options(self, console: tcod.console.Console, box: dict) -> None:
        """Render the main menu options."""
        # Position depends on layout - graphics mode needs options higher to avoid help text overlap
        start_y = 19 if box["use_background_layout"] else 21
        for i, option in enumerate(self.options):
            # Ascension option gets special color to stand out
            if option.startswith("Ascension"):
                color = Colors.YELLOW if i == self.selected_option else Colors.CYAN
            else:
                color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            bg_color = (
                ColorManager.get("backgrounds", "menu_highlight")
                if i == self.selected_option
                else Colors.BLACK
            )
            prefix = "> " if i == self.selected_option else "  "
            full_text = f"{prefix}{option}"

            if box["use_background_layout"]:
                # Background mode - centered within box (box itself is shifted)
                x_pos = box["center_x"] - len(full_text) // 2
            else:
                # Glyph mode - centered
                x_pos = GameConfig.SCREEN_WIDTH // 2 - len(full_text) // 2

            render_char_safe(console, x_pos, start_y + i * 2, full_text, fg=color, bg=bg_color)

    def _render_save_info(self, console: tcod.console.Console, box: dict) -> None:
        """Render save file information if available."""
        if SaveGameManager.save_exists():
            save_timestamp = SaveGameManager.get_save_timestamp()
            if save_timestamp:
                # Match menu options start_y
                start_y = 19 if box["use_background_layout"] else 21
                if box["use_background_layout"]:
                    # Background mode - position within narrow box
                    # Cap save info position to avoid overlapping controls at y=45
                    # Save info needs 3 lines, so max start is 42 (42, 43, 44)
                    save_info_y = min(start_y + len(self.options) * 2 + 2, 42)
                    save_text = "Save found"
                    continue_text = "Continue to resume"
                    render_char_safe(
                        console,
                        box["center_x"] - len(save_text) // 2,
                        save_info_y,
                        save_text,
                        fg=Colors.GREEN,
                        bg=Colors.BLACK,
                    )
                    render_char_safe(
                        console,
                        box["center_x"] - len(continue_text) // 2,
                        save_info_y + 1,
                        continue_text,
                        fg=Colors.GREEN,
                        bg=Colors.BLACK,
                    )
                    saved_text = f"Saved: {save_timestamp[:16]}"
                    render_char_safe(
                        console,
                        box["center_x"] - len(saved_text) // 2,
                        save_info_y + 2,
                        saved_text,
                        fg=Colors.LIGHT_GRAY,
                        bg=Colors.BLACK,
                    )
                else:
                    # Glyph mode - centered
                    render_char_safe(
                        console,
                        GameConfig.SCREEN_WIDTH // 2 - 15,
                        start_y + len(self.options) * 2 + 2,
                        "Save file found - Continue to resume",
                        fg=Colors.GREEN,
                        bg=Colors.BLACK,
                    )
                    render_char_safe(
                        console,
                        GameConfig.SCREEN_WIDTH // 2 - 12,
                        start_y + len(self.options) * 2 + 3,
                        f"Last saved: {save_timestamp}",
                        fg=Colors.LIGHT_GRAY,
                        bg=Colors.BLACK,
                    )

    def _render_controls_help(self, console: tcod.console.Console, box: dict) -> None:
        """Render control instructions - dynamically reflects current bindings."""
        help_text = get_main_menu_help(box["use_background_layout"], self.input_mapper)

        if box["use_background_layout"]:
            # Narrow box (26 char content) - ultra compact, +1 for visual centering
            render_char_safe(
                console,
                box["center_x"] - len(help_text) // 2 + 1,
                GameConfig.SCREEN_HEIGHT - 5,
                help_text,
                fg=Colors.CYAN,
                bg=Colors.BLACK,
            )
        else:
            # Wide box - full format
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - len(help_text) // 2,
                GameConfig.SCREEN_HEIGHT - 5,
                help_text,
                fg=Colors.CYAN,
                bg=Colors.BLACK,
            )

    def _render_warning_dialog(self, console: tcod.console.Console) -> None:
        """Render save deletion warning dialog with background-aware positioning."""
        # Calculate dialog height
        dialog_height = 22

        # Render the right-side box using common method
        box = self._render_right_side_box(console, dialog_height, Colors.RED)

        # Title
        render_char_safe(
            console, box["center_x"] - 3, box["top"] + 2, "WARNING", fg=Colors.RED, bg=Colors.BLACK
        )

        # Message - adjust for narrow box
        if box["use_background_layout"]:
            # Narrow box - break text into shorter lines
            messages = [
                "Starting a new game",
                "will delete your",
                "current progress.",
                "",
                "You will lose:",
                "• Current level",
                "• Character stats",
                "• Equipment",
                "",
                "Story fragments",
                "are never lost.",
                "",
                "Continue?",
            ]
        else:
            # Glyph mode - use original longer lines
            messages = [
                "Starting a new game will delete your",
                "current progress permanently.",
                "",
                "You will lose your current level,",
                "character stats, and equipment.",
                "",
                "Story fragments are never lost.",
                "",
                "Are you sure you want to continue?",
            ]

        for i, msg in enumerate(messages):
            msg_x = (
                box["content_left"] + 1 if len(msg) <= box["content_width"] else box["content_left"]
            )
            render_char_safe(
                console, msg_x, box["top"] + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK
            )

        # Options
        options = ["Yes, Delete Save", "No, Go Back"]
        options_start_y = box["bottom"] - 4

        for i, option in enumerate(options):
            color = (
                Colors.RED
                if i == self.warning_selection and i == 0
                else Colors.YELLOW if i == self.warning_selection else Colors.WHITE
            )
            prefix = "> " if i == self.warning_selection else "  "

            if box["use_background_layout"]:
                # Narrow box - shorter option text and center alignment
                short_options = ["Yes, Delete", "No, Go Back"]
                option_text = short_options[i]
                option_x = box["center_x"] - len(option_text) // 2 - 1
            else:
                # Glyph mode - use full option text
                option_text = option
                option_x = box["center_x"] - len(option_text) // 2 - 1

            full_text = f"{prefix}{option_text}"
            render_char_safe(
                console, option_x, options_start_y + i, full_text, fg=color, bg=Colors.BLACK
            )

            # Store X range for click detection (includes prefix)
            start_x = option_x
            end_x = option_x + len(full_text)
            if i == 0:
                self.warning_option_0_x_range = (start_x, end_x)
                self.warning_option_0_y = options_start_y + i
            else:
                self.warning_option_1_x_range = (start_x, end_x)
                self.warning_option_1_y = options_start_y + i

    def select_current_option(self) -> str:
        """
        Trigger selection of currently highlighted option.

        Returns menu action string ('continue', 'new_game', 'settings', etc.)
        """
        if not self.options or self.selected_option >= len(self.options):
            return ""

        if self.show_warning:
            # Handle warning dialog selection
            if self.warning_selection == 0:  # "Yes"
                return "new_game"
            else:  # "No"
                self.show_warning = False
                return ""

        option = self.options[self.selected_option]
        logging.debug(f"[MENU] Selected option: '{option}'")

        if option.startswith("Continue"):
            return "continue"
        elif option == "New Game":
            save_exists = SaveGameManager.save_exists()
            if save_exists:
                self.show_warning = True
                self.warning_selection = 1  # Default to "No"
                return ""
            else:
                return "new_game"
        elif option.startswith("Ascension"):
            self.last_action = "ascension"
            return "ascension"
        elif option == "Settings":
            self.last_action = "settings"
            return "settings"
        elif option == "Controls":
            self.last_action = "controls"
            return "controls"
        elif option == "Help":
            self.last_action = "help"
            return "help"
        elif option == "Achievements":
            self.last_action = "achievements"
            return "achievements"
        elif option.startswith("Data Fragments"):
            self.last_action = "lore"
            return "lore"
        elif option == "About":
            self.last_action = "about"
            return "about"
        elif option == "Graphics Preview":
            self.last_action = "graphics_preview"
            return "graphics_preview"
        elif "Exit" in option:  # Matches both "Exit" and "Save and Exit"
            return "exit"

        return ""

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS
    # ========================================================================

    def get_context(self):
        """Return input context - DIALOGUE for warning dialog, MAIN_MENU otherwise."""
        from game_input_actions import InputContext

        return InputContext.DIALOGUE if self.show_warning else InputContext.MAIN_MENU

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        import logging

        from game_input_actions import InputAction

        # Movement keys become navigation in menu context
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            if self.show_warning:
                self.warning_selection = 0 if self.warning_selection == 1 else 1
            else:
                old_selection = self.selected_option
                self.navigate_up()
                new_selection = self.selected_option
                logging.debug(f"[MAIN MENU NAV] NAVIGATE_UP: {old_selection} -> {new_selection}")
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            if self.show_warning:
                self.warning_selection = 1 if self.warning_selection == 0 else 0
            else:
                old_selection = self.selected_option
                self.navigate_down()
                new_selection = self.selected_option
                logging.debug(f"[MAIN MENU NAV] NAVIGATE_DOWN: {old_selection} -> {new_selection}")
            return ""
        elif action == InputAction.CONFIRM:
            if self.show_warning:
                if self.warning_selection == 0:  # "Yes, Delete Save"
                    return "new_game"
                else:  # "No, Go Back"
                    self.show_warning = False
                    return ""
            else:
                return self.select_current_option()
        elif action == InputAction.CANCEL:
            if self.show_warning:
                self.show_warning = False
            # CANCEL on main menu is disabled (no accidental exit)
            return ""
        elif action == InputAction.EXIT_TO_MENU:
            # START button pressed - if mid-game mode, return to game
            if self.mid_game_mode:
                return "continue"
            # Not in mid-game mode, START does nothing
            return ""

        return ""

    # ========================================================================
    # MOUSE HANDLING (override BaseMenu for warning dialog support)
    # ========================================================================

    def handle_mouse_motion(self, event) -> str:
        """Handle mouse motion - update selection in menu or warning dialog."""
        if self.show_warning:
            self._handle_warning_mouse_motion(event)
        else:
            # Use base class implementation for main menu
            super().handle_mouse_motion(event)
        return ""

    def handle_left_click(self, event) -> str:
        """Handle left mouse click - activate option in menu or warning dialog."""
        if self.show_warning:
            return self._handle_warning_mouse_click(event)

        # Get the action from base class
        action = super().handle_left_click(event)

        # If clicking "New Game" with existing save, show warning instead
        if action == "new_game" and SaveGameManager.save_exists():
            self.show_warning = True
            self.warning_selection = 1  # Default to "No"
            return ""  # Don't execute new_game yet

        return action

    def handle_right_click(self, event) -> str:
        """Handle right mouse click."""
        if self.show_warning:
            # Right-click on warning = go back (same as "No, Go Back")
            self.show_warning = False
            return ""
        else:
            # Right-click on main menu does nothing (no accidental exit)
            return ""

    # ========================================================================
    # WARNING DIALOG MOUSE HANDLING
    # ========================================================================

    def _handle_warning_mouse_motion(self, event):
        """Handle mouse motion in warning dialog - update selection."""
        # Prefer event.tile, fall back to event.position for test compatibility
        # Use try/except because Mock objects pass hasattr checks
        tile_x = tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_x = int(coord_source.x)
                        tile_y = int(coord_source.y)
                        break  # Found valid coordinates
                    except (TypeError, ValueError, AttributeError):
                        continue  # Try next attribute
        if tile_x is None or tile_y is None:
            return

        # Check if hovering over option 0
        if (
            hasattr(self, "warning_option_0_y")
            and hasattr(self, "warning_option_0_x_range")
            and self.warning_option_0_y is not None
            and self.warning_option_0_x_range is not None
        ):

            start_x, end_x = self.warning_option_0_x_range
            if tile_y == self.warning_option_0_y and start_x <= tile_x < end_x:
                self.warning_selection = 0
                return

        # Check if hovering over option 1
        if (
            hasattr(self, "warning_option_1_y")
            and hasattr(self, "warning_option_1_x_range")
            and self.warning_option_1_y is not None
            and self.warning_option_1_x_range is not None
        ):

            start_x, end_x = self.warning_option_1_x_range
            if tile_y == self.warning_option_1_y and start_x <= tile_x < end_x:
                self.warning_selection = 1
                return

    def _handle_warning_mouse_click(self, event) -> str:
        """Handle mouse click in warning dialog - activate clicked option."""
        # Update selection based on click position
        self._handle_warning_mouse_motion(event)

        # Execute the selected option (same as pressing Enter)
        if self.warning_selection == 0:  # Yes, Delete Save
            SaveGameManager.delete_save()
            return "new_game"
        else:  # No, Go Back
            self.show_warning = False
            return ""
