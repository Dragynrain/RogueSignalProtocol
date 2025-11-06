#!/usr/bin/env python3
"""
Rogue Signal Protocol - Menu System

Main menu implementation with settings, graphics preview, and navigation.
Includes MainMenu, SettingsMenu, and GraphicsPreviewMenu classes.
Handles background rendering coordination and menu state management.
Extracted from RogueSignalProtocol.py for better organization.
"""

import tcod
import logging
import time
import os
import random
import sys

# Import game modules
from game_config import GameSettings, GameConfig
from game_entities import Colors
from game_color_manager import ColorManager
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_audio import SoundManager
from game_ui import render_char_safe, WindowManager, UniversalInputHandler
from game_menu_background import MenuBackground
from game_menu_help_lore import LoreMenu, HelpMenu
from game_menu_utilities import MenuRenderingUtils
from game_menu_base import BaseMenu
from game_coordinate_helpers import CoordinateHelpers


# ============================================================================
# MAIN MENU SYSTEM
# ============================================================================

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
        base_options = ["New Game", "Settings", "Help", "Achievements", "Data Fragments"]

        # Only show Graphics Preview if in graphics mode AND the menu exists
        if (self.settings and self.settings.graphics_mode == "graphics" and
            self.menus and 'graphics_preview_menu' in self.menus):
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
        can_save = (active_game is not None and
                   active_game.player.cpu > 0 and
                   not active_game.game_over)

        # Determine Exit button text based on whether there's a game to save
        exit_text = "Save and Exit" if can_save else "Exit"

        # Build base options
        base_options = ["New Game", "Settings", "Help", "Achievements", "Data Fragments"]

        # Only show Graphics Preview if in graphics mode AND the menu exists
        if (self.settings and self.settings.graphics_mode == "graphics" and
            self.menus and 'graphics_preview_menu' in self.menus):
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
        
        # TCOD is a console-based library, not designed for large background images
        # For true graphics, we would need tcod.sdl.render, but that's complex
        # For now, we'll use the traditional centered menu with optional CP437 glyph art
        
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
        self._render_story_progress(console, box)
    
    def _render_menu_title(self, console: tcod.console.Console, box: dict) -> None:
        """Render the main menu title and decorations."""
        version = "Version 0.8.0 Alpha"
        subtitle = "Cyberspace Stealth Exfiltration"

        # Get UI color from settings
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        if box['use_background_layout']:
            # Title content within narrow box - split into multiple lines to fit
            render_char_safe(console, box['center_x'] - 10, 6, "═" * 20, fg=ui_color, bg=Colors.BLACK)
            # Split title into multiple lines
            render_char_safe(console, box['center_x'] - 6, 7, "ROGUE SIGNAL", fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 4, 8, "PROTOCOL", fg=ui_color, bg=Colors.BLACK)
            # Center the version properly in the box
            version_x = box['center_x'] - len(version) // 2
            render_char_safe(console, version_x, 9, version, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)
            # Split subtitle into two lines
            render_char_safe(console, box['center_x'] - 8, 11, "Cyberspace Stealth", fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 6, 12, "Exfiltration", fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 10, 13, "═" * 20, fg=ui_color, bg=Colors.BLACK)
        else:
            # Glyph mode - centered positioning
            title = "ROGUE SIGNAL PROTOCOL"
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 6, "═" * 40, fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 8, title, fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2, 9, subtitle, fg=ui_color, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 10, "═" * 40, fg=ui_color, bg=Colors.BLACK)
    
    def _render_version_info(self, console: tcod.console.Console, box: dict) -> None:
        """Render author information."""
        author_info = "by Adam Forster"

        # Use bright cyan for all control hints
        help_text_color = Colors.CYAN

        if box['use_background_layout']:
            # Background mode - position within narrow box
            render_char_safe(console,
                box['center_x'] - len(author_info) // 2, 15,
                author_info, fg=help_text_color, bg=Colors.BLACK
            )
        else:
            # Glyph mode - centered
            render_char_safe(console,
                GameConfig.SCREEN_WIDTH // 2 - len(author_info) // 2, 11,
                author_info, fg=help_text_color, bg=Colors.BLACK
            )
    
    def _render_menu_options(self, console: tcod.console.Console, box: dict) -> None:
        """Render the main menu options."""
        start_y = 21  # Back to original Y position (box itself is shifted)
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            bg_color = ColorManager.get("backgrounds", "menu_highlight") if i == self.selected_option else Colors.BLACK
            prefix = "> " if i == self.selected_option else "  "

            if box['use_background_layout']:
                # Background mode - centered within box (box itself is shifted)
                x_pos = box['center_x'] - len(option) // 2 - 1
            else:
                # Glyph mode - centered
                x_pos = GameConfig.SCREEN_WIDTH // 2 - len(option) // 2 - 1

            render_char_safe(console,
                x_pos, start_y + i * 2,
                f"{prefix}{option}", fg=color, bg=bg_color
            )
    
    def _render_save_info(self, console: tcod.console.Console, box: dict) -> None:
        """Render save file information if available."""
        if SaveGameManager.save_exists():
            save_timestamp = SaveGameManager.get_save_timestamp()
            if save_timestamp:
                start_y = 21
                if box['use_background_layout']:
                    # Background mode - position within narrow box
                    save_text = "Save found"
                    continue_text = "Continue to resume"
                    render_char_safe(console, 
                        box['center_x'] - len(save_text) // 2, start_y + len(self.options) * 2 + 2,
                        save_text, fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    render_char_safe(console, 
                        box['center_x'] - len(continue_text) // 2, start_y + len(self.options) * 2 + 3,
                        continue_text, fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    saved_text = f"Saved: {save_timestamp[:16]}"
                    render_char_safe(console, 
                        box['center_x'] - len(saved_text) // 2, start_y + len(self.options) * 2 + 4,
                        saved_text, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
                    )
                else:
                    # Glyph mode - centered
                    render_char_safe(console,
                        GameConfig.SCREEN_WIDTH // 2 - 15, start_y + len(self.options) * 2 + 2,
                        "Save file found - Continue to resume", fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    render_char_safe(console,
                        GameConfig.SCREEN_WIDTH // 2 - 12, start_y + len(self.options) * 2 + 3,
                        f"Last saved: {save_timestamp}", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
                    )
    
    def _render_controls_help(self, console: tcod.console.Console, box: dict) -> None:
        """Render control instructions."""
        # Use bright cyan for all control hints
        help_text_color = Colors.CYAN

        if box['use_background_layout']:
            # Background mode - position within narrow box
            nav_text = "↕/W/S: Navigate"
            select_text = "Enter: Select"
            render_char_safe(console,
                box['center_x'] - len(nav_text) // 2, GameConfig.SCREEN_HEIGHT - 6,
                nav_text, fg=help_text_color, bg=Colors.BLACK
            )
            render_char_safe(console,
                box['center_x'] - len(select_text) // 2, GameConfig.SCREEN_HEIGHT - 5,
                select_text, fg=help_text_color, bg=Colors.BLACK
            )
        else:
            # Glyph mode - centered
            render_char_safe(console,
                GameConfig.SCREEN_WIDTH // 2 - 15, GameConfig.SCREEN_HEIGHT - 6,
                "↕ or W/S: Navigate", fg=help_text_color, bg=Colors.BLACK
            )
            render_char_safe(console,
                GameConfig.SCREEN_WIDTH // 2 - 10, GameConfig.SCREEN_HEIGHT - 5,
                "Enter: Select", fg=help_text_color, bg=Colors.BLACK
            )
    
    def _render_story_progress(self, console: tcod.console.Console, box: dict) -> None:
        """Render story fragment progress information."""
        if SaveGameManager.save_exists():
            story_manager = StoryFragmentManager()
            discovered, total = story_manager.get_fragment_count()
            if box['use_background_layout']:
                # Background mode - position within narrow box
                fragment_text = f"Fragments: {discovered}/{total}"
                render_char_safe(console, 
                    box['center_x'] - len(fragment_text) // 2, GameConfig.SCREEN_HEIGHT - 2,
                    fragment_text, fg=Colors.CYAN, bg=Colors.BLACK
                )
            else:
                # Glyph mode - centered
                render_char_safe(console,
                    GameConfig.SCREEN_WIDTH // 2 - 12, GameConfig.SCREEN_HEIGHT - 2,
                    f"Story Fragments: {discovered}/{total}", fg=Colors.CYAN, bg=Colors.BLACK
                )
    
    
    def _render_warning_dialog(self, console: tcod.console.Console) -> None:
        """Render save deletion warning dialog with background-aware positioning."""
        # Calculate dialog height
        dialog_height = 22
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, dialog_height, Colors.RED)
        
        # Title
        render_char_safe(console, box['center_x'] - 3, box['top'] + 2, "WARNING", fg=Colors.RED, bg=Colors.BLACK)
        
        # Message - adjust for narrow box
        if box['use_background_layout']:
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
                "Continue?"
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
                "Are you sure you want to continue?"
            ]
        
        for i, msg in enumerate(messages):
            msg_x = box['content_left'] + 1 if len(msg) <= box['content_width'] else box['content_left']
            render_char_safe(console, msg_x, box['top'] + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options
        options = ["Yes, Delete Save", "No, Go Back"]
        options_start_y = box['bottom'] - 4

        for i, option in enumerate(options):
            color = Colors.RED if i == self.warning_selection and i == 0 else Colors.YELLOW if i == self.warning_selection else Colors.WHITE
            prefix = "> " if i == self.warning_selection else "  "

            if box['use_background_layout']:
                # Narrow box - shorter option text and center alignment
                short_options = ["Yes, Delete", "No, Go Back"]
                option_text = short_options[i]
                option_x = box['center_x'] - len(option_text) // 2 - 1
            else:
                # Glyph mode - use full option text
                option_text = option
                option_x = box['center_x'] - len(option_text) // 2 - 1

            full_text = f"{prefix}{option_text}"
            render_char_safe(console,
                option_x,
                options_start_y + i,
                full_text, fg=color, bg=Colors.BLACK
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
            elif option == "Data Fragments":
                return "lore"
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
        if not hasattr(event, 'tile') or event.tile is None:
            return False

        # The menu loop already converted pixel to tile coordinates
        # event.tile is already in tile space (0-79, 0-49)
        try:
            tile_x = int(event.tile.x)
            tile_y = int(event.tile.y)
        except (TypeError, ValueError, AttributeError):
            return False

        # Check if hovering over option 0
        if (hasattr(self, 'warning_option_0_y') and
            hasattr(self, 'warning_option_0_x_range') and
            self.warning_option_0_y is not None and
            self.warning_option_0_x_range is not None):

            start_x, end_x = self.warning_option_0_x_range
            if tile_y == self.warning_option_0_y and start_x <= tile_x < end_x:
                self.warning_selection = 0
                return True

        # Check if hovering over option 1
        if (hasattr(self, 'warning_option_1_y') and
            hasattr(self, 'warning_option_1_x_range') and
            self.warning_option_1_y is not None and
            self.warning_option_1_x_range is not None):

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


# LoreMenu and HelpMenu are imported from game_menu_help_lore.py
# Do not create duplicate class definitions


class SettingsMenu(BaseMenu):
    """Settings menu for audio, graphics, and help options."""

    def __init__(self, settings: GameSettings, menu_background=None, sound_manager=None):
        super().__init__(menu_background)
        self.settings = settings
        self.menu_background = menu_background  # Reference to background manager
        self.sound_manager = sound_manager  # For live volume updates and sound previews
        self.options = [
            {"name": "Master Volume", "type": "volume", "key": "master"},
            {"name": "SFX Volume", "type": "volume", "key": "sfx"},
            {"name": "Music Volume", "type": "volume", "key": "music"},
            {"name": "Graphics Mode", "type": "toggle", "key": "graphics_mode",
             "values": ["Classic", "Graphics"]},
            {"name": "UI Color", "type": "ui_color", "key": "ui_color",
             "values": ["Cyan", "Purple", "Magenta", "Golden", "Crimson", "Azure", "Emerald", "Ivory"]},
            {"name": "Overclock Warnings", "type": "dialogue_toggle", "key": "show_overclock_warning"},
            {"name": "Export Debug Package", "type": "action"},
            {"name": "Back", "type": "action"}
        ]

        # Debug export confirmation dialogue state
        self.show_export_confirmation = False
        self.export_confirmation_selection = 0

        # Stored coordinates for confirmation dialog click detection
        self.confirm_option_0_x_range = None  # (start_x, end_x) for "Yes"
        self.confirm_option_1_x_range = None  # (start_x, end_x) for "No"

    def render(self, console: tcod.console.Console) -> None:
        """Render the settings menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Show confirmation dialogue if active
        if self.show_export_confirmation:
            self._render_export_confirmation_dialog(console)
            return

        # Calculate menu height - match Main Menu for consistent transitions
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Same as Main Menu (46 tiles)

        # Get UI color for decorations
        ui_color = self.settings.get_ui_color_rgb()

        # Render the right-side box using common method (match Main Menu y_offset)
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)
        
        # Title
        title = "SETTINGS"
        if box['use_background_layout']:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        else:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options - use more spacing in graphics mode for better readability
        start_y = box['top'] + 5
        spacing = 3 if box['use_background_layout'] else 2
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            bg_color = ColorManager.get("backgrounds", "menu_highlight") if i == self.selected_option else Colors.BLACK
            option_y = start_y + i * spacing

            if box['use_background_layout']:
                # Narrow box layout
                name_x = box['content_left'] + 1

                # Option name (no truncation needed - values are on separate lines)
                name = option["name"]

                # Section headers
                if option["type"] == "section_header":
                    render_char_safe(console, name_x, option_y, name, fg=ui_color, bg=Colors.BLACK)
                else:
                    render_char_safe(console, name_x, option_y, name, fg=color, bg=bg_color)

                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 8  # Shorter bar for narrow box
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar with directional hints - more compact
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    # Add arrows to show click left=down, click right=up
                    bar_text = f"< {bar} > {volume_percent}%"
                    render_char_safe(console, name_x, option_y + 1, bar_text, fg=color, bg=bg_color)

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        render_char_safe(console, name_x, option_y + 1, f"< {current_value} >", fg=color, bg=bg_color)

                elif option["type"] == "ui_color":
                    current_value = self.settings.ui_color.capitalize()
                    # Show the color name in its actual color for preview
                    color_rgb = self.settings.get_ui_color_rgb()
                    render_char_safe(console, name_x, option_y + 1, f"< {current_value} >", fg=color_rgb, bg=bg_color)

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    # Render on next line for narrow box (like volume controls)
                    render_char_safe(console, name_x, option_y + 1, f"{status} Enabled", fg=color, bg=bg_color)
            else:
                # Glyph mode - wider layout
                # Option name
                if option["type"] == "section_header":
                    render_char_safe(console, box['content_left'] + 2, option_y, option["name"], fg=ui_color, bg=Colors.BLACK)
                else:
                    render_char_safe(console, box['content_left'] + 2, option_y, option["name"], fg=color, bg=bg_color)

                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 14  # Shortened from 20 to prevent overflow in glyph mode
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar with directional hints
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    # Add arrows to show click left=down, click right=up
                    bar_text = f"< {bar} > {volume_percent}%"
                    render_char_safe(console, box['content_left'] + 18, option_y, bar_text, fg=color, bg=bg_color)

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        render_char_safe(console, box['content_left'] + 18, option_y, f"< {current_value} >", fg=color, bg=bg_color)

                elif option["type"] == "ui_color":
                    current_value = self.settings.ui_color.capitalize()
                    # Show the color name in its actual color for preview
                    color_rgb = self.settings.get_ui_color_rgb()
                    render_char_safe(console, box['content_left'] + 18, option_y, f"< {current_value} >", fg=color_rgb, bg=bg_color)

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    # Render on next line (like volume controls) to avoid overlap
                    render_char_safe(console, box['content_left'] + 2, option_y + 1, f"{status} Enabled", fg=color, bg=bg_color)
        
        # Instructions
        if box['use_background_layout']:
            # Compact instructions for narrow box (graphics mode)
            instructions = [
                "↕/WASD: Navigate",
                "←→/A/D: Adjust",
                "Enter: Select",
                "Esc: Back"
            ]
            inst_start_y = box['bottom'] - 6
        else:
            # Full instructions for glyph mode
            instructions = [
                "↕/WASD: Navigate",
                "←→ or A/D: Adjust",
                "Enter: Select",
                "Escape: Back"
            ]
            inst_start_y = box['bottom'] - 6
        
        for i, instruction in enumerate(instructions):
            if box['use_background_layout']:
                # Center in narrow box
                inst_x = box['center_x'] - len(instruction) // 2
            else:
                # Center in wide box
                inst_x = box['center_x'] - len(instruction) // 2
            
            render_char_safe(console, inst_x, inst_start_y + i, instruction, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)
    
    def handle_input(self, event) -> str:
        """Handle settings menu input. Returns action: 'back', 'exit', 'export_debug_confirmed', or ''."""

        # Priority: Handle confirmation dialogue if active
        if self.show_export_confirmation:
            return self._handle_confirmation_input(event)

        # Handle navigation with section header skipping
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.options), False, self._navigate_skip_headers):
            return ""

        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            option = self.options[self.selected_option]
            if option["type"] == "action":
                if option["name"] == "Back":
                    return "back"
                elif option["name"] == "Export Debug Package":
                    # Show confirmation dialogue instead of exporting immediately
                    self.show_export_confirmation = True
                    self.export_confirmation_selection = 0  # Default to "No"
                    return ""
            elif option["type"] == "toggle":
                # Trigger toggle with Enter key (same as in _adjust_setting)
                self._adjust_setting(1)  # Direction doesn't matter for toggles
                return ""
            elif option["type"] == "dialogue_toggle":
                # Trigger dialogue toggle with Enter key
                self._adjust_setting(1)  # Direction doesn't matter for toggles
                return ""

        # Handle value adjustment using universal handler
        if UniversalInputHandler.handle_value_adjustment(self, event, self._adjust_setting):
            return ""

        # Handle escape
        if UniversalInputHandler.is_escape_key(event):
            return "back"

        return ""

    def _handle_confirmation_input(self, event) -> str:
        """Handle input for export confirmation dialogue."""
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_dialog_navigation(self, event, attr_prefix="export_confirmation"):
            return ""

        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            if self.export_confirmation_selection == 0:  # Yes, Export
                self.show_export_confirmation = False
                return "export_debug_confirmed"
            else:  # No, Cancel
                self.show_export_confirmation = False
        elif UniversalInputHandler.is_escape_key(event):
            self.show_export_confirmation = False

        return ""

    def _navigate_skip_headers(self, direction: int):
        """Navigate options while skipping section headers."""
        old_selection = self.selected_option

        # Move in the specified direction
        if direction == -1:
            self.selected_option = max(0, self.selected_option - 1)
        else:
            self.selected_option = min(len(self.options) - 1, self.selected_option + 1)

        # Skip section headers
        while (self.selected_option != old_selection and
               self.options[self.selected_option]["type"] == "section_header"):
            if direction == -1:
                self.selected_option = max(0, self.selected_option - 1)
            else:
                self.selected_option = min(len(self.options) - 1, self.selected_option + 1)

            # Prevent infinite loop if all options are headers
            if self.selected_option == old_selection:
                break
    
    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - update selection in settings menu or confirmation dialogue."""
        if not hasattr(event, 'tile') or event.tile is None:
            return False

        # Priority: Handle confirmation dialogue if active
        if self.show_export_confirmation:
            return self._handle_confirmation_mouse_motion(event)

        from game_config import GameConfig

        try:
            tile_x = int(event.tile.x)
            tile_y = int(event.tile.y)
        except (TypeError, ValueError, AttributeError):
            return False

        # Calculate box dimensions the same way render() does
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Must match render() method (46 tiles)
        y_offset = 3  # Must match render() method
        layout = self._get_menu_layout_params()

        # Calculate box top (same logic as _render_right_side_box with y_offset)
        if layout['use_background_layout']:
            box_top = y_offset - 1  # With y_offset=3, box_top = 2
        else:
            box_top = (GameConfig.SCREEN_HEIGHT - menu_height) // 2

        # Options start at box_top + 5 with spacing (3 in graphics mode, 2 in glyph mode)
        start_y = box_top + 5
        spacing = 3 if layout['use_background_layout'] else 2

        # Calculate which option was hovered
        if tile_y >= start_y:
            option_index = (tile_y - start_y) // spacing

            if 0 <= option_index < len(self.options):
                # Skip section headers - they're not selectable
                if self.options[option_index]["type"] == "section_header":
                    return False

                self.selected_option = option_index
                return True

        return False

    def _handle_confirmation_mouse_motion(self, event) -> bool:
        """Handle mouse motion in confirmation dialog - update selection."""
        if not hasattr(event, 'tile') or event.tile is None:
            return False

        try:
            tile_x = int(event.tile.x)
            tile_y = int(event.tile.y)
        except (TypeError, ValueError, AttributeError):
            return False

        # Check if hovering over option 0
        if (hasattr(self, 'confirm_option_0_y') and
            hasattr(self, 'confirm_option_0_x_range') and
            self.confirm_option_0_y is not None and
            self.confirm_option_0_x_range is not None):

            start_x, end_x = self.confirm_option_0_x_range
            if tile_y == self.confirm_option_0_y and start_x <= tile_x < end_x:
                self.export_confirmation_selection = 0
                return True

        # Check if hovering over option 1
        if (hasattr(self, 'confirm_option_1_y') and
            hasattr(self, 'confirm_option_1_x_range') and
            self.confirm_option_1_y is not None and
            self.confirm_option_1_x_range is not None):

            start_x, end_x = self.confirm_option_1_x_range
            if tile_y == self.confirm_option_1_y and start_x <= tile_x < end_x:
                self.export_confirmation_selection = 1
                return True

        return False

    def _handle_confirmation_mouse_click(self, event) -> str:
        """Handle mouse click in confirmation dialog - execute selected option."""
        # Update selection based on click position
        self._handle_confirmation_mouse_motion(event)

        # Execute the selected option (same as pressing Enter)
        if self.export_confirmation_selection == 0:  # Yes, Export
            self.show_export_confirmation = False
            return "export_debug_confirmed"
        else:  # No, Cancel
            self.show_export_confirmation = False
            return ""

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - activate clicked option (for toggle/action types) or confirmation dialogue."""
        # Priority: Handle confirmation dialogue if active
        if self.show_export_confirmation:
            return self._handle_confirmation_mouse_click(event)

        # First update selection based on click position
        if not self.handle_mouse_motion(event):
            return ""

        option = self.options[self.selected_option]

        # Handle different option types
        if option["type"] == "action":
            if option["name"] == "Back":
                return "back"
            elif option["name"] == "Export Debug Package":
                # Show confirmation dialogue
                self.show_export_confirmation = True
                self.export_confirmation_selection = 0  # Default to "No"
                return ""
        elif option["type"] == "toggle":
            # Toggle the value (same as pressing Enter)
            if option["key"] == "graphics_mode":
                current_mode = self.settings.graphics_mode
                new_mode = "graphics" if current_mode == "glyph" else "glyph"
                self.settings.set_graphics_mode(new_mode)

                # Immediately update background to reflect the change
                if self.menu_background:
                    self.menu_background.reload_if_mode_changed()
                    logging.info(f"Graphics mode changed to {new_mode} via mouse - background updated")
        elif option["type"] == "dialogue_toggle":
            # Toggle dialogue preference
            dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
            current_value = dialogue_prefs.get(option["key"], True)
            new_value = not current_value

            # Update preference
            if not hasattr(self.settings, 'dialogue_preferences'):
                self.settings.dialogue_preferences = {}
            self.settings.dialogue_preferences[option["key"]] = new_value
            self.settings.save_settings()
            logging.info(f"Dialogue preference '{option['key']}' set to {new_value} via mouse")
        elif option["type"] == "ui_color":
            # UI color selector: clicking left side cycles backward, right side cycles forward
            # Determine which half of the color display was clicked
            try:
                tile_x = int(event.tile.x)
            except (TypeError, ValueError, AttributeError):
                return ""

            # Calculate color display position using actual box dimensions
            menu_height = GameConfig.SCREEN_HEIGHT - 4  # Must match render() method (46 tiles)
            layout = self._get_menu_layout_params()

            if layout['use_background_layout']:
                # Graphics mode - narrow box (28 chars wide)
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1
                # UI color rendered at: name_x = content_left + 1 (on second line, like volume)
                # Text format: "< ColorName >"
                color_start_x = content_left + 1
            else:
                # Glyph mode - wide box (50 chars wide)
                box_width = 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2
                # UI color rendered at: content_left + 18
                # Text format: "< ColorName >"
                color_start_x = content_left + 18

            # The color text is formatted as "< ColorName >"
            # Example: "< Cyan >" has length 8
            # Get current color name to calculate width
            current_color_name = self.settings.ui_color.capitalize()
            color_display_width = len(f"< {current_color_name} >")
            color_mid = color_start_x + (color_display_width // 2)

            # Left half = previous color, right half = next color
            direction = -1 if tile_x < color_mid else 1
            self._adjust_setting(direction)
        elif option["type"] == "volume":
            # Volume sliders: clicking left side decreases, right side increases
            # (left = 0%, right = 100%)
            # Determine which half of the slider bar was clicked
            try:
                tile_x = int(event.tile.x)
            except (TypeError, ValueError, AttributeError):
                return ""

            # Calculate slider bar position using actual box dimensions
            # Must match the rendering code exactly
            menu_height = GameConfig.SCREEN_HEIGHT - 4  # Must match render() method (46 tiles)
            layout = self._get_menu_layout_params()

            if layout['use_background_layout']:
                # Graphics mode - narrow box (28 chars wide)
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1

                # Bar rendered at: name_x = content_left + 1
                # Bar text: "<- [========] +> 100%"
                bar_start_x = content_left + 1
                bar_length = 8  # Graphics mode uses short bar

                # The "[" bracket is at bar_start_x + 3 (after "<- ")
                # Actual bar content starts at bar_start_x + 4
                bracket_x = bar_start_x + 3
                bar_content_start = bar_start_x + 4
                bar_content_end = bar_content_start + bar_length - 1
                bar_mid = (bar_content_start + bar_content_end) // 2
            else:
                # ASCII mode - wide box (50 chars wide)
                box_width = 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2

                # Bar rendered at: content_left + 18
                # Bar text: "<- [==============] +> 100%"
                bar_start_x = content_left + 18
                bar_length = 14  # ASCII mode bar (shortened to fit in box)

                # The "[" bracket is at bar_start_x + 3 (after "<- ")
                # Actual bar content starts at bar_start_x + 4
                bracket_x = bar_start_x + 3
                bar_content_start = bar_start_x + 4
                bar_content_end = bar_content_start + bar_length - 1
                bar_mid = (bar_content_start + bar_content_end) // 2

            # Left half = decrease (toward 0%), right half = increase (toward 100%)
            direction = -1 if tile_x < bar_mid else 1
            self._adjust_setting(direction)

        return ""

    def _render_export_confirmation_dialog(self, console: tcod.console.Console) -> None:
        """Render debug export confirmation dialog with background-aware positioning."""
        # Calculate dialog height
        dialog_height = 26

        # Render the right-side box using common method
        box = self._render_right_side_box(console, dialog_height, Colors.GOLDEN)

        # Title
        render_char_safe(console, box['center_x'] - 10, box['top'] + 2, "EXPORT DEBUG PACKAGE", fg=Colors.GOLDEN, bg=Colors.BLACK)

        # Message - adjust for narrow box
        if box['use_background_layout']:
            # Narrow box - break text into shorter lines
            messages = [
                "This will create a",
                "debug package with:",
                "",
                "• Save files",
                "• Settings",
                "• Game logs",
                "• Metrics",
                "• System info",
                "",
                "Saved to:",
                "debug_exports/",
                "",
                "This helps devs",
                "fix bugs.",
                "",
                "Continue?"
            ]
        else:
            # Glyph mode - use longer lines
            messages = [
                "This will create a debug package containing:",
                "",
                "• Your save files and settings",
                "• Game logs and metrics",
                "• System information",
                "",
                "This package can help developers fix bugs.",
                "",
                "Package will be saved to:",
                "  debug_exports/debug_YYYY-MM-DD_HHMM.zip",
                "",
                "Continue?"
            ]

        for i, msg in enumerate(messages):
            msg_x = box['content_left'] + 1 if len(msg) <= box['content_width'] else box['content_left']
            render_char_safe(console, msg_x, box['top'] + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK)

        # Options
        options = ["Yes, Export", "No, Cancel"]
        options_start_y = box['bottom'] - 4

        for i, option in enumerate(options):
            color = Colors.GOLDEN if i == self.export_confirmation_selection and i == 0 else Colors.YELLOW if i == self.export_confirmation_selection else Colors.WHITE
            prefix = "> " if i == self.export_confirmation_selection else "  "

            if box['use_background_layout']:
                # Narrow box - shorter option text and center alignment
                short_options = ["Yes, Export", "No, Cancel"]
                option_text = short_options[i]
                option_x = box['center_x'] - len(option_text) // 2 - 1
            else:
                # Glyph mode - use full option text
                option_text = option
                option_x = box['center_x'] - len(option_text) // 2 - 1

            full_text = f"{prefix}{option_text}"
            render_char_safe(console,
                option_x,
                options_start_y + i,
                full_text, fg=color, bg=Colors.BLACK
            )

            # Store X range for click detection (includes prefix)
            start_x = option_x
            end_x = option_x + len(full_text)
            if i == 0:
                self.confirm_option_0_x_range = (start_x, end_x)
                self.confirm_option_0_y = options_start_y + i
            else:
                self.confirm_option_1_x_range = (start_x, end_x)
                self.confirm_option_1_y = options_start_y + i

    def _adjust_setting(self, direction: int):
        """Adjust the currently selected setting."""
        option = self.options[self.selected_option]

        if option["type"] == "volume":
            current_percent = self.settings.get_volume_percent(option["key"])
            new_percent = max(0, min(100, current_percent + (direction * 5)))
            self.settings.set_volume_percent(option["key"], new_percent)

            # Update sound manager volumes immediately for live feedback
            if self.sound_manager:
                self.sound_manager.update_volumes()

                # Play a preview sound for the adjusted volume type
                import random
                try:
                    if option["key"] == "sfx":
                        # Play a random sound effect to preview volume
                        preview_sounds = [
                            "player_move", "item_pickup_code", "ui_menu_open",
                            "node_activate", "exploit_system_hop"
                        ]
                        sound_id = random.choice(preview_sounds)
                        if sound_id in self.sound_manager.sounds:
                            self.sound_manager.play_sound(sound_id)
                    elif option["key"] == "music":
                        # Update music volume immediately (if music is playing)
                        pass  # Music volume is already updated by update_volumes()
                except Exception as e:
                    logging.debug(f"Could not play volume preview sound: {e}")

        elif option["type"] == "toggle":
            if option["key"] == "graphics_mode":
                current_mode = self.settings.graphics_mode
                new_mode = "graphics" if current_mode == "glyph" else "glyph"
                self.settings.set_graphics_mode(new_mode)

                # Immediately update background to reflect the change
                if self.menu_background:
                    self.menu_background.reload_if_mode_changed()
                    logging.info(f"Graphics mode changed to {new_mode} - background updated")

        elif option["type"] == "ui_color":
            # Cycle through UI colors
            colors = ["cyan", "purple", "magenta", "golden", "crimson", "azure", "emerald", "ivory"]
            current_idx = colors.index(self.settings.ui_color) if self.settings.ui_color in colors else 0
            new_idx = (current_idx + direction) % len(colors)
            self.settings.set_ui_color(colors[new_idx])
            logging.info(f"UI color changed to {colors[new_idx]}")

        elif option["type"] == "dialogue_toggle":
            # Toggle dialogue preference
            dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
            current_value = dialogue_prefs.get(option["key"], True)
            new_value = not current_value

            # Update preference
            if not hasattr(self.settings, 'dialogue_preferences'):
                self.settings.dialogue_preferences = {}
            self.settings.dialogue_preferences[option["key"]] = new_value
            self.settings.save_settings()
            logging.info(f"Dialogue preference '{option['key']}' set to {new_value}")
    
