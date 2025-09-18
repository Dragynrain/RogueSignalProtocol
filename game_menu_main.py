#!/usr/bin/env python3
"""
Main Menu - Split from game_menus.py
Main menu for New Game/Continue options with background-aware positioning.
"""

import tcod
from tcod import constants

from game_config import GameConfig
from game_entities import Colors
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_ui import render_char_safe, UniversalInputHandler


class MainMenu:
    """Main menu for New Game/Continue options."""
    
    def __init__(self, background=None):
        self.selected_option = 0
        self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"] if SaveGameManager.save_exists() else ["New Game", "Settings", "Help", "Lore", "Exit"]
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game
        self.background = background
    
    def refresh_options(self, show_continue: bool = True) -> None:
        """Refresh menu options. Set show_continue=False when accessed from mid-game."""
        if show_continue and SaveGameManager.save_exists():
            self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"]
            self.mid_game_mode = False
        else:
            self.options = ["New Game", "Settings", "Help", "Lore", "Exit"]
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
        
        if layout['use_background_layout']:
            # ENFORCED SEPARATION: 60% graphics area, 40% menu area
            graphics_boundary = int(console.width * 0.6)  # Hard boundary at 60%
            
            # Left 60%: Make transparent for SDL graphics
            for y in range(console.height):
                for x in range(0, graphics_boundary):
                    # Set background alpha to 0 (fully transparent)
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
    
    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu screen."""
        
        # TCOD is a console-based library, not designed for large background images
        # For true graphics, we would need tcod.sdl.render, but that's complex
        # For now, we'll use the traditional centered menu with optional ASCII art
        
        self._render_enhanced_menu(console)
    
    def _get_menu_layout_params(self):
        """Calculate menu positioning based on graphics mode, window state, and optimal visibility."""
        if self._has_background():
            # Graphics mode with background - calculate optimal positioning
            return self._calculate_background_aware_layout()
        else:
            # ASCII mode or no background - center everything
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
    
    def _calculate_background_aware_layout(self):
        """Calculate sophisticated layout for background mode based on window dimensions."""
        # Get actual window dimensions if available
        window_width, window_height = 800, 800  # Default fallback
        
        if (self.background and 
            self.background.window_manager):
            try:
                window_width, window_height = self.background.window_manager.get_window_pixel_dimensions()
            except:
                pass  # Use defaults if window detection fails
        
        # Calculate dynamic positioning based on window aspect ratio and size
        aspect_ratio = window_width / window_height if window_height > 0 else 1.0
        
        # Position menu to avoid overlap with left-aligned background graphics
        # Since image is left-aligned, menu needs to be positioned far right
        if aspect_ratio > 1.2:
            # Wide window - use far right positioning to avoid image overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.85)  # Move further right
            layout_zone = 'right'
        elif aspect_ratio < 0.8:
            # Very tall window - still avoid left side overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.8)   # Right side, not center
            layout_zone = 'upper'
        else:
            # Square-ish window - use far right positioning
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.82)  # Move further right
            layout_zone = 'right_center'
        
        # Ensure minimum margins
        min_margin = 5
        max_x = GameConfig.SCREEN_WIDTH - min_margin - 20  # 20 chars for longest menu option
        text_x_offset = min(text_x_offset, max_x)
        text_x_offset = max(text_x_offset, min_margin + 10)
        
        layout = {
            'title_x': text_x_offset - 10,
            'menu_x': text_x_offset,
            'use_background_layout': True,
            'layout_zone': layout_zone,
            'window_aspect': aspect_ratio,
            'window_size': (window_width, window_height)
        }
        
        return layout
    
    def _render_enhanced_menu(self, console: tcod.console.Console) -> None:
        """Render an enhanced menu with dynamic positioning based on background state."""
        # Calculate menu height based on content
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Full height for main menu
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, Colors.CYAN, y_offset=3)
        
        # Title with some ASCII art decoration
        title = "ROGUE SIGNAL PROTOCOL"
        subtitle = "Cyberpunk Stealth Exfiltration"
        
        if box['use_background_layout']:
            # Title content within narrow box - split into multiple lines to fit
            render_char_safe(console, box['center_x'] - 10, 6, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
            # Split title into two lines
            render_char_safe(console, box['center_x'] - 6, 8, "ROGUE SIGNAL", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 4, 9, "PROTOCOL", fg=Colors.CYAN, bg=Colors.BLACK)
            # Split subtitle into two lines
            render_char_safe(console, box['center_x'] - 8, 11, "Cyberpunk Stealth", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 6, 12, "Exfiltration", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 10, 13, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
        else:
            # ASCII mode - centered positioning
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 6, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 8, title, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2, 9, subtitle, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 10, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
        
        # Version and build info  
        if box['use_background_layout']:
            # Background mode - position within narrow box
            build_info = "Alpha Build"
            author_info = "by Adam Forster"
            render_char_safe(console, 
                box['center_x'] - len(build_info) // 2, 15,
                build_info, fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                box['center_x'] - len(author_info) // 2, 16,
                author_info, fg=(128, 128, 128), bg=Colors.BLACK
            )
        else:
            # ASCII mode - centered
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 13, 12,
                "Alpha Build by Adam Forster", fg=(128, 128, 128), bg=Colors.BLACK
            )
        
        # Menu options
        start_y = 21
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            prefix = "> " if i == self.selected_option else "  "
            
            if box['use_background_layout']:
                # Background mode - centered within narrow box
                x_pos = box['center_x'] - len(option) // 2 - 1
            else:
                # ASCII mode - centered
                x_pos = GameConfig.SCREEN_WIDTH // 2 - len(option) // 2 - 1
                
            render_char_safe(console, 
                x_pos, start_y + i * 2,
                f"{prefix}{option}", fg=color, bg=Colors.BLACK
            )
        
        # Save file info
        if SaveGameManager.save_exists():
            save_timestamp = SaveGameManager.get_save_timestamp()
            if save_timestamp:
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
                    # ASCII mode - centered
                    render_char_safe(console, 
                        GameConfig.SCREEN_WIDTH // 2 - 15, start_y + len(self.options) * 2 + 2,
                        "Save file found - Continue to resume", fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    render_char_safe(console, 
                        GameConfig.SCREEN_WIDTH // 2 - 12, start_y + len(self.options) * 2 + 3,
                        f"Last saved: {save_timestamp}", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
                    )
        
        # Controls - position based on layout mode
        if box['use_background_layout']:
            # Background mode - position within narrow box
            nav_text = "↕/W/S: Navigate"
            select_text = "Enter: Select"
            render_char_safe(console, 
                box['center_x'] - len(nav_text) // 2, GameConfig.SCREEN_HEIGHT - 6,
                nav_text, fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                box['center_x'] - len(select_text) // 2, GameConfig.SCREEN_HEIGHT - 5,
                select_text, fg=(128, 128, 128), bg=Colors.BLACK
            )
        else:
            # ASCII mode - centered
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 15, GameConfig.SCREEN_HEIGHT - 6,
                "UP/DOWN or W/S: Navigate", fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 10, GameConfig.SCREEN_HEIGHT - 5,
                "Enter: Select", fg=(128, 128, 128), bg=Colors.BLACK
            )
        
        # Story fragments info - position based on layout mode
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
                # ASCII mode - centered
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
                "will delete your save",
                "file permanently.",
                "",
                "This will erase:",
                "• Current level",
                "• Character state", 
                "• Inventory/upgrades",
                "• Story fragments",
                "  remain safe",
                "",
                "Are you sure you",
                "want to continue?"
            ]
        else:
            # ASCII mode - use original longer lines
            messages = [
                "Starting a new game will delete your",
                "current save file permanently.",
                "",
                "This will erase all progress including:",
                "• Current level and character state",
                "• Inventory and upgrades", 
                "• Story fragments remain safe",
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
                # ASCII mode - use full option text
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