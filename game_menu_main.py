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
from game_config import GameConfig
from game_entities import Colors
from game_menu_base import BaseMenu
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_ui import UniversalInputHandler, render_char_safe


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

    def __init__(self, background=None, settings=None, menus=None):
        super().__init__(background)
        self.settings = settings  # Store settings to check graphics mode
        self.menus = menus  # Reference to menus dict to check if graphics_preview_menu exists
        self.options = self._build_options_list()
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game

        # Stored coordinates for warning dialog click detection
        self.warning_option_0_x_range = None  # (start_x, end_x) for "Yes, Delete"
        self.warning_option_1_x_range = None  # (start_x, end_x) for "No, Go Back"

    def _build_options_list(self):
        """Build the options list based on save state and graphics mode."""
        # Get fragment count for menu display
        story_manager = StoryFragmentManager()
        discovered, total = story_manager.get_fragment_count()

        base_options = [
            "New Game",
            "Settings",
            "Help",
            "Achievements",
            f"Data Fragments ({discovered}/{total})",
            "About",
        ]

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
            return ["Continue Game"] + base_options
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
            "Settings",
            "Help",
            "Achievements",
            f"Data Fragments ({discovered}/{total})",
            "About",
        ]

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
            self.options = ["Continue Game"] + base_options
            self.mid_game_mode = False
        else:
            self.options = base_options
            self.mid_game_mode = not show_continue  # True when accessed from mid-game

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
        version = "Version 0.8.0 Alpha"
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
        start_y = 21  # Back to original Y position (box itself is shifted)
        for i, option in enumerate(self.options):
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
                start_y = 21
                if box["use_background_layout"]:
                    # Background mode - position within narrow box
                    save_text = "Save found"
                    continue_text = "Continue to resume"
                    render_char_safe(
                        console,
                        box["center_x"] - len(save_text) // 2,
                        start_y + len(self.options) * 2 + 2,
                        save_text,
                        fg=Colors.GREEN,
                        bg=Colors.BLACK,
                    )
                    render_char_safe(
                        console,
                        box["center_x"] - len(continue_text) // 2,
                        start_y + len(self.options) * 2 + 3,
                        continue_text,
                        fg=Colors.GREEN,
                        bg=Colors.BLACK,
                    )
                    saved_text = f"Saved: {save_timestamp[:16]}"
                    render_char_safe(
                        console,
                        box["center_x"] - len(saved_text) // 2,
                        start_y + len(self.options) * 2 + 4,
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
        """Render control instructions."""
        # Use bright cyan for all control hints
        help_text_color = Colors.CYAN

        if box["use_background_layout"]:
            # Background mode - position within narrow box
            nav_text = "↕/W/S: Navigate"
            select_text = "Enter: Select"
            render_char_safe(
                console,
                box["center_x"] - len(nav_text) // 2,
                GameConfig.SCREEN_HEIGHT - 6,
                nav_text,
                fg=help_text_color,
                bg=Colors.BLACK,
            )
            render_char_safe(
                console,
                box["center_x"] - len(select_text) // 2,
                GameConfig.SCREEN_HEIGHT - 5,
                select_text,
                fg=help_text_color,
                bg=Colors.BLACK,
            )
        else:
            # Glyph mode - centered
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - 15,
                GameConfig.SCREEN_HEIGHT - 6,
                "↕ or W/S: Navigate",
                fg=help_text_color,
                bg=Colors.BLACK,
            )
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - 10,
                GameConfig.SCREEN_HEIGHT - 5,
                "Enter: Select",
                fg=help_text_color,
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

    def handle_input(self, event) -> str:
        """Handle menu input. Returns action: 'continue', 'new_game', 'exit', or ''."""
        if self.show_warning:
            return self._handle_warning_input(event)
        else:
            return self._handle_menu_input(event)

    def _handle_menu_input(self, event) -> str:
        """Handle main menu input."""
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.options)):
            return ""

        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            option = self.options[self.selected_option]
            if option == "Continue Game":
                return "continue"
            elif option == "New Game":
                if SaveGameManager.save_exists() and not self.mid_game_mode:
                    self.show_warning = True
                    self.warning_selection = 1  # Default to "No"
                else:
                    return "new_game"
            elif option == "Settings":
                return "settings"
            elif option == "Help":
                return "help"
            elif option == "Achievements":
                return "achievements"
            elif option.startswith("Data Fragments"):
                return "lore"
            elif option == "About":
                return "about"
            elif option == "Graphics Preview":
                return "graphics_preview"
            elif "Exit" in option:  # Matches both "Exit" and "Save and Exit"
                return "exit"
        # ESC disabled on main menu to prevent accidental exit

        return ""

    def _handle_warning_input(self, event) -> str:
        """Handle warning dialog input."""
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_dialog_navigation(self, event):
            return ""

        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            if self.warning_selection == 0:  # Yes, Delete Save
                SaveGameManager.delete_save()
                return "new_game"
            else:  # No, Go Back
                self.show_warning = False
        elif UniversalInputHandler.is_escape_key(event):
            self.show_warning = False

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - update selection in menu or warning dialog."""
        if self.show_warning:
            return self._handle_warning_mouse_motion(event)
        else:
            # Use base class implementation for main menu
            return super().handle_mouse_motion(event)

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - activate option in menu or warning dialog."""
        if self.show_warning:
            return self._handle_warning_mouse_click(event)

        # Get the action from base class
        action = super().handle_mouse_click(event)

        # If clicking "New Game" with existing save, show warning instead
        if action == "new_game" and SaveGameManager.save_exists() and not self.mid_game_mode:
            self.show_warning = True
            self.warning_selection = 1  # Default to "No"
            return ""  # Don't execute new_game yet

        return action

    def _handle_warning_mouse_motion(self, event) -> bool:
        """Handle mouse motion in warning dialog - update selection."""
        if not hasattr(event, "tile") or event.tile is None:
            return False

        # The menu loop already converted pixel to tile coordinates
        # event.tile is already in tile space (0-79, 0-49)
        try:
            tile_x = int(event.tile.x)
            tile_y = int(event.tile.y)
        except (TypeError, ValueError, AttributeError) as e:
            logging.debug(f"Mouse event tile coordinate conversion failed in warning menu: {e}")
            return False

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
                return True

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
                return True

        return False

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
