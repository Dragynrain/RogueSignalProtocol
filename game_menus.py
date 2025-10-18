#!/usr/bin/env python3
"""
Menu system and background graphics.
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
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_audio import SoundManager
from game_ui import render_char_safe, WindowManager, UniversalInputHandler
from game_menu_background import MenuBackground
from game_menu_help_lore import LoreMenu, HelpMenu
from game_menu_utilities import MenuRenderingUtils


# ============================================================================
# MAIN MENU SYSTEM
# ============================================================================

class MainMenu:
    """Main menu for New Game/Continue options."""
    
    def __init__(self, background=None):
        self.selected_option = 0
        self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Graphics Preview", "Exit"] if SaveGameManager.save_exists() else ["New Game", "Settings", "Help", "Lore", "Graphics Preview", "Exit"]
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game
        self.background = background
    
    def refresh_options(self, show_continue: bool = True) -> None:
        """Refresh menu options. Set show_continue=False when accessed from mid-game."""
        if show_continue and SaveGameManager.save_exists():
            self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Graphics Preview", "Exit"]
            self.mid_game_mode = False
        else:
            self.options = ["New Game", "Settings", "Help", "Lore", "Graphics Preview", "Exit"]
            self.mid_game_mode = not show_continue  # True when accessed from mid-game
        # Reset selection to prevent index out of bounds
        self.selected_option = 0
        # Reset warning state when refreshing options
        self.show_warning = False
    
    def _has_background(self) -> bool:
        """Check if background is available and should be displayed."""
        return (self.background and 
                self.background.should_load_background() and 
                self.background.background_texture)
    
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
    
    def _clear_text_areas_only(self, console):
        """Create true separation: left 60% transparent for graphics, right 40% opaque for menu."""
        layout = self._get_menu_layout_params()
        MenuRenderingUtils.clear_text_areas_only(console, layout)
    
    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu screen."""
        
        # TCOD is a console-based library, not designed for large background images
        # For true graphics, we would need tcod.sdl.render, but that's complex
        # For now, we'll use the traditional centered menu with optional CP437 glyph art
        
        self._render_enhanced_menu(console)
    
    def _get_menu_layout_params(self):
        """Calculate menu positioning based on graphics mode, window state, and optimal visibility."""
        if self._has_background():
            # Graphics mode with background - calculate optimal positioning
            return self._calculate_background_aware_layout()
        else:
            # Glyph mode or no background - center everything
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }

    def _render_right_side_box(self, console: tcod.console.Console, height: int, border_color: tuple, y_offset: int = 0):
        """Render a right-side menu box with consistent positioning and styling.

        Args:
            console: The console to render to
            height: Height of the box
            border_color: Color for the box border
            y_offset: Vertical offset for positioning (0 = centered)

        Returns:
            dict: Box dimensions and positions for content rendering
        """
        layout = self._get_menu_layout_params()
        return MenuRenderingUtils.render_right_side_box(console, layout, height, border_color, y_offset)
    
    def _calculate_background_aware_layout(self):
        """Calculate sophisticated layout for background mode based on window dimensions."""
        return MenuRenderingUtils.calculate_background_aware_layout(self.background)
    
    def _render_enhanced_menu(self, console: tcod.console.Console) -> None:
        """Render an enhanced menu with dynamic positioning based on background state."""
        # Calculate menu height based on content
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Full height for main menu
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, Colors.CYAN, y_offset=3)
        
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
        subtitle = "Cyberpunk Stealth Exfiltration"

        if box['use_background_layout']:
            # Title content within narrow box - split into multiple lines to fit
            render_char_safe(console, box['center_x'] - 10, 6, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
            # Split title into multiple lines
            render_char_safe(console, box['center_x'] - 6, 7, "ROGUE SIGNAL", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 4, 8, "PROTOCOL", fg=Colors.CYAN, bg=Colors.BLACK)
            # Center the version properly in the box
            version_x = box['center_x'] - len(version) // 2
            render_char_safe(console, version_x, 9, version, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)
            # Split subtitle into two lines
            render_char_safe(console, box['center_x'] - 8, 11, "Cyberpunk Stealth", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 6, 12, "Exfiltration", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 10, 13, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
        else:
            # Glyph mode - centered positioning
            title = "ROGUE SIGNAL PROTOCOL"
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 6, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 8, title, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2, 9, subtitle, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 10, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
    
    def _render_version_info(self, console: tcod.console.Console, box: dict) -> None:
        """Render author information."""
        author_info = "by Adam Forster"

        from data_loading import DataLoader
        from game_entities import ensure_color_tuple
        config = DataLoader.load_config()
        help_text_color = ensure_color_tuple(config.get("colors", {}).get("ui", {}).get("help_text", [128, 128, 128]))

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
        start_y = 21
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            prefix = "> " if i == self.selected_option else "  "
            
            if box['use_background_layout']:
                # Background mode - centered within narrow box
                x_pos = box['center_x'] - len(option) // 2 - 1
            else:
                # Glyph mode - centered
                x_pos = GameConfig.SCREEN_WIDTH // 2 - len(option) // 2 - 1
                
            render_char_safe(console, 
                x_pos, start_y + i * 2,
                f"{prefix}{option}", fg=color, bg=Colors.BLACK
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
        from data_loading import DataLoader
        from game_entities import ensure_color_tuple
        config = DataLoader.load_config()
        help_text_color = ensure_color_tuple(config.get("colors", {}).get("ui", {}).get("help_text", [128, 128, 128]))

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
                "UP/DOWN or W/S: Navigate", fg=help_text_color, bg=Colors.BLACK
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
            
            render_char_safe(console, 
                option_x, 
                options_start_y + i,
                f"{prefix}{option_text}", fg=color, bg=Colors.BLACK
            )
    
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
            elif option == "Lore":
                return "lore"
            elif option == "Graphics Preview":
                return "graphics_preview"
            elif option == "Exit":
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


# LoreMenu and HelpMenu are imported from game_menu_help_lore.py
# Do not create duplicate class definitions


class SettingsMenu:
    """Settings menu for audio, graphics, and help options."""

    def __init__(self, settings: GameSettings, menu_background=None, sound_manager=None):
        self.settings = settings
        self.menu_background = menu_background  # Reference to background manager
        self.background = menu_background  # Alias for consistency with MainMenu
        self.sound_manager = sound_manager  # For live volume updates and sound previews
        self.selected_option = 0
        self.options = [
            {"name": "Master Volume", "type": "volume", "key": "master"},
            {"name": "SFX Volume", "type": "volume", "key": "sfx"},
            {"name": "Music Volume", "type": "volume", "key": "music"},
            {"name": "Graphics Mode", "type": "toggle", "key": "graphics_mode",
             "values": ["Classic", "Graphics"]},
            {"name": "--- Dialogues ---", "type": "section_header"},
            {"name": "Overclock Warnings", "type": "dialogue_toggle", "key": "show_overclock_warning"},
            {"name": "Back", "type": "action"}
        ]
    
    def _has_background(self) -> bool:
        """Check if background is available and should be displayed."""
        return (self.background and 
                self.background.should_load_background() and 
                self.background.background_texture)
    
    def _get_menu_layout_params(self):
        """Calculate menu positioning based on graphics mode, window state, and optimal visibility."""
        if self._has_background():
            # Graphics mode with background - calculate optimal positioning
            return self._calculate_background_aware_layout()
        else:
            # Glyph mode or no background - center everything
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }

    def _calculate_background_aware_layout(self):
        """Calculate sophisticated layout for background mode based on window dimensions."""
        return MenuRenderingUtils.calculate_background_aware_layout(self.background)
    
    def _clear_text_areas_only(self, console):
        """Create true separation: left 60% transparent for graphics, right 40% opaque for menu."""
        layout = self._get_menu_layout_params()
        MenuRenderingUtils.clear_text_areas_only(console, layout)

    def _render_right_side_box(self, console: tcod.console.Console, height: int, border_color: tuple, y_offset: int = 0):
        """Render a right-side menu box with consistent positioning and styling.

        Args:
            console: The console to render to
            height: Height of the box
            border_color: Color for the box border
            y_offset: Vertical offset for positioning (0 = centered)

        Returns:
            dict: Box dimensions and positions for content rendering
        """
        layout = self._get_menu_layout_params()

        if layout['use_background_layout']:
            # Graphics mode - narrow box on right side
            box_width = 28
            box_right = GameConfig.SCREEN_WIDTH - 2
            box_left = box_right - box_width

            if y_offset == 0:
                # Centered positioning
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                # Custom offset
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
            # Glyph mode - larger centered box
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

            # Draw simple glyph border
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

    def render(self, console: tcod.console.Console) -> None:
        """Render the settings menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Calculate menu height (account for all options including dialogue toggles)
        menu_height = 30  # Increased for dialogue preferences section
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, Colors.WHITE)
        
        # Title
        title = "SETTINGS"
        if box['use_background_layout']:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        else:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options
        start_y = box['top'] + 5
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            option_y = start_y + i * 2

            if box['use_background_layout']:
                # Narrow box layout
                name_x = box['content_left'] + 1

                # Option name (truncate if needed for narrow box)
                name = option["name"]
                if len(name) > 15 and option["type"] != "section_header":  # Truncate for narrow box
                    name = name[:12] + "..."

                # Section headers
                if option["type"] == "section_header":
                    render_char_safe(console, name_x, option_y, name, fg=Colors.CYAN, bg=Colors.BLACK)
                else:
                    render_char_safe(console, name_x, option_y, name, fg=color, bg=Colors.BLACK)

                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 8  # Shorter bar for narrow box
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar - more compact
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    render_char_safe(console, name_x, option_y + 1, f"{bar} {volume_percent}%", fg=color, bg=Colors.BLACK)

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        render_char_safe(console, name_x, option_y + 1, f"< {current_value} >", fg=color, bg=Colors.BLACK)

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    render_char_safe(console, name_x, option_y + 1, f"{status} Enabled", fg=color, bg=Colors.BLACK)
            else:
                # Glyph mode - wider layout
                # Option name
                if option["type"] == "section_header":
                    render_char_safe(console, box['content_left'] + 2, option_y, option["name"], fg=Colors.CYAN, bg=Colors.BLACK)
                else:
                    render_char_safe(console, box['content_left'] + 2, option_y, option["name"], fg=color, bg=Colors.BLACK)

                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 20
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    render_char_safe(console, box['content_left'] + 18, option_y, f"{bar} {volume_percent}%", fg=color, bg=Colors.BLACK)

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        render_char_safe(console, box['content_left'] + 18, option_y, f"< {current_value} >", fg=color, bg=Colors.BLACK)

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    render_char_safe(console, box['content_left'] + 18, option_y, f"{status} Enabled", fg=color, bg=Colors.BLACK)
        
        # Instructions
        if box['use_background_layout']:
            # Compact instructions for narrow box
            instructions = [
                "↑↓: Navigate",
                "←→: Adjust", 
                "Enter: Select",
                "Esc: Back"
            ]
            inst_start_y = box['bottom'] - 6
        else:
            # Full instructions for glyph mode
            instructions = [
                "Arrow Keys/WASD: Navigate",
                "Left/Right or A/D: Adjust volumes/toggle options", 
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
        """Handle settings menu input. Returns action: 'back', 'exit', or ''."""

        # Handle navigation with section header skipping
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.options), False, self._navigate_skip_headers):
            return ""

        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            option = self.options[self.selected_option]
            if option["type"] == "action":
                if option["name"] == "Back":
                    return "back"

        # Handle value adjustment using universal handler
        if UniversalInputHandler.handle_value_adjustment(self, event, self._adjust_setting):
            return ""

        # Handle escape
        if UniversalInputHandler.is_escape_key(event):
            return "back"

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
                            "node_activate", "exploit_shadow_step"
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
    
