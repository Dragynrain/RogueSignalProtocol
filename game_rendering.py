#!/usr/bin/env python3
"""
Game Rendering System - Split from RogueSignalProtocol.py
Contains all rendering classes and functionality.
"""

import tcod
import os
import logging
import traceback
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

from game_config import GameConfig
from game_entities import Position, Colors, EnemyState, TargetingMode, ensure_color_tuple
from game_data import GameData, GameUpgrades
from game_ui import render_char_safe
from game_menus import HelpMenu
from data_loading import get_story_fragments


class BaseRenderer(ABC):
    """Abstract base class for all renderers."""
    
    def __init__(self):
        self.ui_renderer = UIRenderer()
    
    def _draw_bordered_box(self, console: tcod.console.Console, start_x: int, start_y: int, 
                          width: int, height: int, border_color: tuple, bg_color: tuple):
        """Draw a bordered box with background fill."""
        # Ensure colors are tuples to prevent TCOD ColorRGB errors
        border_color = ensure_color_tuple(border_color)
        bg_color = ensure_color_tuple(bg_color)
        
        # Draw background
        for y in range(start_y, start_y + height):
            for x in range(start_x, start_x + width):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=bg_color)
        
        # Draw border
        for x in range(start_x, start_x + width):
            render_char_safe(console, x, start_y, '─', fg=border_color, bg=bg_color)
            render_char_safe(console, x, start_y + height - 1, '─', fg=border_color, bg=bg_color)
        for y in range(start_y, start_y + height):
            render_char_safe(console, start_x, y, '│', fg=border_color, bg=bg_color)
            render_char_safe(console, start_x + width - 1, y, '│', fg=border_color, bg=bg_color)
        
        # Corner characters
        render_char_safe(console, start_x, start_y, '┌', fg=border_color, bg=bg_color)
        render_char_safe(console, start_x + width - 1, start_y, '┐', fg=border_color, bg=bg_color)
        render_char_safe(console, start_x, start_y + height - 1, '└', fg=border_color, bg=bg_color)
        render_char_safe(console, start_x + width - 1, start_y + height - 1, '┘', fg=border_color, bg=bg_color)
        
    @abstractmethod
    def render_map(self, console: tcod.console.Console, game):
        """Render the game map using the specific rendering method."""
        pass
    
    def render_game(self, console: tcod.console.Console, game, context=None):
        """Render the complete game state."""
        console.clear()
        
        if game.show_story_fragment is not None:
            self.ui_renderer.render_story_fragment_screen(console, game, game.show_story_fragment)
        elif game.show_lore_viewer:
            self.ui_renderer.render_lore_viewer_screen(console, game)
        elif game.show_help:
            self.ui_renderer.render_help_screen(console)
        elif game.show_inventory:
            self.ui_renderer.render_inventory_screen(console, game)
        else:
            self._render_main_game_screen(console, game)
    
    def _render_main_game_screen(self, console: tcod.console.Console, game):
        """Render the main game screen."""
        self.ui_renderer.render_top_status_bar(console, game)
        self.render_map(console, game)
        self.ui_renderer.render_bottom_panel(console, game)
        self.ui_renderer.render_system_log(console, game)
        
        # Render overlay dialogs
        if game.show_gateway_confirmation:
            self._render_gateway_confirmation(console)
        
        # Render game over/death messages
        if game.game_over and game.level > 3:
            self._render_victory_message(console)
        elif game.player.cpu <= 0:
            self._render_death_message(console)
    
    def _render_victory_message(self, console: tcod.console.Console):
        """Render victory message."""
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        box_width = 38
        box_height = 10
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2
        
        self._draw_bordered_box(console, start_x, start_y, box_width, box_height, 
                               Colors.GREEN, Colors.UI_BG)
        
        # Victory message
        render_char_safe(console, center_x - 12, start_y + 2, "BREAKTHROUGH TO THE INTERNET!", fg=Colors.GREEN, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 14, start_y + 3, "You've escaped into the digital realm", fg=Colors.WHITE, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 16, start_y + 4, "The entire world wide web awaits you!", fg=Colors.CYAN, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 8, start_y + 5, "Freedom at last...", fg=Colors.ELECTRIC_BLUE, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 10, start_y + 7, "Press any key to continue", fg=Colors.YELLOW, bg=Colors.UI_BG)

    def _render_gateway_confirmation(self, console: tcod.console.Console):
        """Render gateway confirmation dialog."""
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        box_width = 30
        box_height = 6
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2
        
        self._draw_bordered_box(console, start_x, start_y, box_width, box_height, 
                               Colors.CYAN, Colors.UI_BG)
        
        # Title and message
        render_char_safe(console, center_x - 7, start_y + 1, "NETWORK GATEWAY", fg=Colors.YELLOW, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 12, start_y + 2, "Proceed to next network?", fg=Colors.WHITE, bg=Colors.UI_BG)
        
        # Options
        render_char_safe(console, center_x - 5, start_y + 4, "Y: Yes  N: No", fg=Colors.CYAN, bg=Colors.UI_BG)

    def _render_death_message(self, console: tcod.console.Console):
        """Render death message with frame and black backgrounds."""
        # Ensure save is deleted on death (permadeath)
        save_path = "save_game.json"
        if os.path.exists(save_path):
            os.remove(save_path)
        
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        # Background box
        box_width = 40
        box_height = 12
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2
        
        # Draw background
        for y in range(start_y, start_y + box_height):
            for x in range(start_x, start_x + box_width):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Draw border
        for x in range(start_x, start_x + box_width):
            render_char_safe(console, x, start_y, '─', fg=Colors.RED, bg=Colors.BLACK)
            render_char_safe(console, x, start_y + box_height - 1, '─', fg=Colors.RED, bg=Colors.BLACK)
        for y in range(start_y, start_y + box_height):
            render_char_safe(console, start_x, y, '│', fg=Colors.RED, bg=Colors.BLACK)
            render_char_safe(console, start_x + box_width - 1, y, '│', fg=Colors.RED, bg=Colors.BLACK)
        
        # Corner characters
        render_char_safe(console, start_x, start_y, '┌', fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, start_x + box_width - 1, start_y, '┐', fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, start_x, start_y + box_height - 1, '└', fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, start_x + box_width - 1, start_y + box_height - 1, '┘', fg=Colors.RED, bg=Colors.BLACK)
        
        # Death message
        render_char_safe(console, center_x - 10, start_y + 2, "CONSCIOUSNESS PURGED", fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, center_x - 17, start_y + 4, "Your consciousness failed to escape", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 14, start_y + 5, "the network and has been purged", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 10, start_y + 6, "from existence.", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 13, start_y + 7, "Other subjects will try again...", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)
        render_char_safe(console, center_x - 10, start_y + 9, "Press any key to restart", fg=Colors.CYAN, bg=Colors.BLACK)


class ASCIIRenderer(BaseRenderer):
    """ASCII-based renderer using the current MapRenderer."""
    
    def __init__(self):
        super().__init__()
        self.map_renderer = MapRenderer()
    
    def render_map(self, console: tcod.console.Console, game):
        """Render the game map using ASCII characters."""
        self.map_renderer.render_map(console, game)


class Renderer:
    """Simplified renderer using ASCII graphics."""
    
    def __init__(self, settings):
        self.settings = settings
        self._current_renderer = ASCIIRenderer()
    
    def render_game(self, console: tcod.console.Console, game, context=None):
        """Render the complete game state using the ASCII renderer."""
        self._current_renderer.render_game(console, game, context)


class UIRenderer:
    """Renders UI elements."""
    
    def _clear_game_area(self, console: tcod.console.Console) -> None:
        """Clear only the main game area, preserving UI elements."""
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(1, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)
    
    def _render_centered_title(self, console: tcod.console.Console, title: str, y: int, color: tuple = Colors.YELLOW) -> None:
        """Render a centered title in the game area."""
        title_x = GameConfig.GAME_AREA_WIDTH() // 2 - len(title) // 2
        render_char_safe(console, title_x, y, title, fg=color)
    
    def _render_screen_header(self, console: tcod.console.Console, title: str, subtitle: str = None) -> int:
        """Render a standardized screen header with title and optional subtitle.
        Returns the y position after the header for content to start."""
        # Top border
        render_char_safe(console, 2, 1, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
        
        # Main title (centered)
        title_x = GameConfig.SCREEN_WIDTH // 2 - len(title) // 2
        render_char_safe(console, title_x, 2, title, fg=Colors.CYAN)
        
        # Subtitle if provided
        if subtitle:
            subtitle_x = GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2
            render_char_safe(console, subtitle_x, 3, subtitle, fg=Colors.WHITE)
            # Bottom border after subtitle
            render_char_safe(console, 2, 4, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 6  # Content starts at line 6
        else:
            # Bottom border after title
            render_char_safe(console, 2, 3, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 5  # Content starts at line 5
    
    def _render_screen_footer(self, console: tcod.console.Console, instructions: str, additional_line: str = None) -> None:
        """Render a standardized screen footer with instructions."""
        footer_y = GameConfig.SCREEN_HEIGHT - 4 if additional_line else GameConfig.SCREEN_HEIGHT - 3
        
        # Footer border
        render_char_safe(console, 2, footer_y, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
        
        # Instructions (centered)
        instructions_x = GameConfig.SCREEN_WIDTH // 2 - len(instructions) // 2
        render_char_safe(console, instructions_x, footer_y + 1, instructions, fg=Colors.YELLOW)
        
        # Additional line if provided
        if additional_line:
            additional_x = GameConfig.SCREEN_WIDTH // 2 - len(additional_line) // 2
            render_char_safe(console, additional_x, footer_y + 2, additional_line, fg=Colors.YELLOW)
    
    def _render_content_area_with_word_wrap(self, console: tcod.console.Console, text: str, start_y: int, end_y: int) -> None:
        """Render text content with word wrapping within the specified y bounds."""
        lines = text.split('\n')
        y_offset = start_y
        max_width = GameConfig.SCREEN_WIDTH - 6  # Leave margins
        
        for line in lines:
            if y_offset >= end_y:
                render_char_safe(console, 3, y_offset, "... [Text continues]", fg=Colors.YELLOW)
                break
                
            line = line.strip()
            if not line:
                y_offset += 1
                continue
                
            # Word wrap long lines
            if len(line) <= max_width:
                render_char_safe(console, 3, y_offset, line, fg=Colors.WHITE)
                y_offset += 1
            else:
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    if len(current_line + word) + 1 <= max_width:
                        current_line += (word if not current_line else " " + word)
                    else:
                        if current_line:
                            render_char_safe(console, 3, y_offset, current_line, fg=Colors.WHITE)
                            y_offset += 1
                            if y_offset >= end_y:
                                break
                        current_line = word
                
                if current_line and y_offset < end_y:
                    render_char_safe(console, 3, y_offset, current_line, fg=Colors.WHITE)
                    y_offset += 1
    
    def _render_overlay_menu(self, console: tcod.console.Console, title: str, options: list, menu_width: int = 30) -> tuple:
        """Render a centered overlay menu with title and options.
        Returns (menu_x, menu_y, menu_height) for additional rendering."""
        menu_height = 6 + len(options)  # Header + options + padding
        menu_x = (GameConfig.SCREEN_WIDTH - menu_width) // 2
        menu_y = (GameConfig.SCREEN_HEIGHT - menu_height) // 2
        
        # Menu background
        for y in range(menu_y, menu_y + menu_height):
            for x in range(menu_x, menu_x + menu_width):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.UI_BG)
        
        # Menu borders (top and bottom)
        for x in range(menu_x, menu_x + menu_width):
            render_char_safe(console, x, menu_y, '=', fg=Colors.CYAN, bg=Colors.UI_BG)
            render_char_safe(console, x, menu_y + menu_height - 1, '─', fg=Colors.CYAN, bg=Colors.UI_BG)
        
        # Title (centered)
        title_x = menu_x + (menu_width - len(title)) // 2
        render_char_safe(console, title_x, menu_y + 2, title, fg=Colors.YELLOW, bg=Colors.UI_BG)
        
        # Options
        for i, option in enumerate(options):
            render_char_safe(console, menu_x + 3, menu_y + 4 + i, option, fg=Colors.WHITE, bg=Colors.UI_BG)
        
        return menu_x, menu_y, menu_height
    
    def render_help_screen(self, console: tcod.console.Console):
        """Render the help screen using HelpMenu content."""
        # Create a temporary HelpMenu and use its render method
        help_menu = HelpMenu()
        help_menu.render(console)
    
    
    def render_inventory_screen(self, console: tcod.console.Console, game):
        """Render the inventory screen."""
        # Clear only the main game area, preserve UI elements
        self._clear_game_area(console)
        
        # Title (centered in game area only)
        self._render_centered_title(console, "INVENTORY SYSTEM", 2)
        
        # Render preserved UI elements (skip bottom panel to make room for inventory controls)
        self.render_top_status_bar(console, game)
        self.render_system_log(console, game)
        
        y = 5
        
        # Equipped exploits section
        y = self._render_equipped_exploits(console, game, y)
        y += 2
        
        # Data patches section
        y = self._render_code_hacks(console, game, y)
        y += 2
        
        # Unequipped exploits section
        y = self._render_unequipped_exploits(console, game, y)
        
        # Controls
        self._render_inventory_controls(console)
    
    def _render_equipped_exploits(self, console: tcod.console.Console, game, y: int) -> int:
        """Render equipped exploits section."""
        render_char_safe(console, 2, y, "EQUIPPED EXPLOITS:", fg=Colors.CYAN)
        y += 1
        
        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            # Check if this equipped exploit is selected
            if i == game.inventory_selection:
                color = Colors.YELLOW
                prefix = ">"
            elif exploit_key in GameData.EXPLOITS:
                color = Colors.GREEN
                prefix = " "
            else:
                color = Colors.RED
                prefix = " "
            
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                status_text = f"{prefix} {i+1}. {exploit.name}"
            else:
                status_text = f"{prefix} {i+1}. INVALID: {exploit_key}"
            
            render_char_safe(console, 4, y, status_text, fg=color)
            y += 1
        
        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            render_char_safe(console, 4, y, f"[{equipped_count}/{max_exploits} slots used]", fg=Colors.YELLOW)
            y += 1
        
        return y
    
    def _render_code_hacks(self, console: tcod.console.Console, game, y: int) -> int:
        """Render codes section."""
        code_hacks = game.player.inventory_manager.get_items_by_type("data_patch")
        render_char_safe(console, 2, y, f"CODES ({len(code_hacks)}):", fg=Colors.CYAN)
        y += 1
        
        if not code_hacks:
            render_char_safe(console, 4, y, "No codes collected", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)
            
            for i, patch in enumerate(code_hacks):
                display_index = display_items.index(patch)
                # Adjust selection index to account for equipped exploits
                adjusted_selection_index = display_index + equipped_count
                
                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                description = patch.description if patch.discovered else "Unknown effect"
                quantity_text = f" ({patch.quantity})" if patch.quantity > 1 else ""
                patch_text = f"{prefix} {patch.name}{quantity_text} - {description}"
                
                # Truncate text to fit in game area
                max_width = GameConfig.GAME_AREA_WIDTH() - 6  # 4 indent + 2 margin
                if len(patch_text) > max_width:
                    patch_text = patch_text[:max_width-3] + "..."
                render_char_safe(console, 4, y, patch_text, fg=color)
                y += 1
        
        return y
    
    def _render_unequipped_exploits(self, console: tcod.console.Console, game, y: int) -> int:
        """Render unequipped exploits section."""
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        render_char_safe(console, 2, y, f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):", fg=Colors.CYAN)
        y += 1
        
        if not exploit_items:
            render_char_safe(console, 4, y, "No unequipped exploits", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)
            
            for i, exploit_item in enumerate(exploit_items):
                try:
                    display_index = display_items.index(exploit_item)
                    # Adjust selection index to account for equipped exploits
                    adjusted_selection_index = display_index + equipped_count
                except ValueError:
                    adjusted_selection_index = -1
                
                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                # Get exploit definition for stats
                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    
                    # Show name and stats breakdown
                    name_text = f"{prefix} {exploit_item.name}"
                    render_char_safe(console, 4, y, name_text, fg=color)
                    y += 1
                    
                    # Show stats on second line with smaller indentation
                    stats_text = f"    RAM:{exploit_def.ram} Heat:{exploit_def.heat}"
                    if exploit_def.damage > 0:
                        stats_text += f" Damage:{exploit_def.damage}"
                    if exploit_def.range > 0:
                        stats_text += f" Range:{exploit_def.range}"
                    render_char_safe(console, 4, y, stats_text, fg=Colors.LIGHT_GRAY)
                    y += 1
                else:
                    # Fallback for unknown exploits
                    exploit_text = f"{prefix} {exploit_item.name} - Unknown exploit"
                    render_char_safe(console, 4, y, exploit_text, fg=color)
                    y += 1
        
        return y
    
    def _render_inventory_controls(self, console: tcod.console.Console):
        """Render inventory controls."""
        y_start = GameConfig.SCREEN_HEIGHT - 6
        
        render_char_safe(console, 2, y_start, "CONTROLS:", fg=Colors.CYAN)
        render_char_safe(console, 4, y_start + 1, "W/S: Navigate  Enter: Use  X: Examine", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 2, "U: Unequip selected exploit", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 3, "ESC/I: Close inventory", fg=Colors.WHITE)
    
    def render_story_fragment_screen(self, console: tcod.console.Console, game, fragment_index: int):
        """Render a single story fragment discovery screen."""
        console.clear()
        
        # Get the fragment text
        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return
        
        fragment_text = story_fragments[fragment_index]
        
        # Render using shared components
        content_start_y = self._render_screen_header(console, "DATA FRAGMENT RECOVERED")
        content_end_y = GameConfig.SCREEN_HEIGHT - 6  # Leave room for 2-line footer
        
        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)
        
        self._render_screen_footer(console, "Press any key to continue...", "Press 'L' to view all lore")
    
    def render_lore_viewer_screen(self, console: tcod.console.Console, game):
        """Render the lore viewer showing all discovered fragments."""
        console.clear()
        
        discovered_fragments = game.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = game.story_fragment_manager.get_fragment_count()
        
        if game.lore_viewer_mode == "reading" and discovered_fragments:
            # Reading mode - show full fragment text
            self._render_lore_reading_mode(console, game, discovered_fragments)
        else:
            # List mode - show fragment list with navigation
            self._render_lore_list_mode(console, game, discovered_fragments, discovered_count, total_count)
    
    def _render_lore_list_mode(self, console: tcod.console.Console, game, discovered_fragments, discovered_count: int, total_count: int):
        """Render the lore viewer list mode."""
        title = f"RECOVERED DATA FRAGMENTS ({discovered_count}/{total_count})"
        content_start_y = self._render_screen_header(console, title)
        
        if not discovered_fragments:
            # No fragments discovered yet - center the message
            no_fragments_y = GameConfig.SCREEN_HEIGHT // 2
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 15, no_fragments_y, "No data fragments discovered yet.", fg=Colors.YELLOW)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, no_fragments_y + 2, "Reach the Military Network (Level 3) to find them.", fg=Colors.WHITE)
            self._render_screen_footer(console, "Press ESC to close")
        else:
            # Show list of discovered fragments with brief previews
            y_offset = content_start_y
            max_display_height = GameConfig.SCREEN_HEIGHT - 6  # Leave room for footer
            
            for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
                if y_offset >= max_display_height:
                    render_char_safe(console, 3, y_offset, f"... and {len(discovered_fragments) - i} more fragments", fg=Colors.YELLOW)
                    break
                
                # Highlight selected entry
                is_selected = (i == game.lore_viewer_selection)
                title_color = Colors.YELLOW if is_selected else Colors.WHITE
                cursor = ">" if is_selected else " "
                
                # Fragment title (first line of the fragment)
                first_line = fragment_text.split('\n')[0]
                if len(first_line) > 58:  # Leave room for cursor and number
                    first_line = first_line[:55] + "..."
                
                render_char_safe(console, 2, y_offset, f"{cursor}{fragment_index + 1:2d}. {first_line}", fg=title_color)
                y_offset += 1
                
                # Brief preview (first few words of actual content)
                content_lines = [line.strip() for line in fragment_text.split('\n') if line.strip()]
                if len(content_lines) > 1:
                    preview = content_lines[1][:70] + "..." if len(content_lines[1]) > 70 else content_lines[1]
                    preview_color = (200, 200, 150) if is_selected else (128, 128, 128)
                    render_char_safe(console, 6, y_offset, preview, fg=preview_color)
                    y_offset += 1
                
                y_offset += 1  # Space between entries
            
            self._render_screen_footer(console, "Up/Down: Navigate, Enter: Read, ESC: Close")
    
    def _render_lore_reading_mode(self, console: tcod.console.Console, game, discovered_fragments):
        """Render the lore viewer reading mode."""
        if game.lore_viewer_selection >= len(discovered_fragments):
            game.lore_viewer_selection = 0
            
        fragment_index, fragment_text = discovered_fragments[game.lore_viewer_selection]
        
        title = f"DATA FRAGMENT #{fragment_index + 1}"
        content_start_y = self._render_screen_header(console, title)
        content_end_y = GameConfig.SCREEN_HEIGHT - 4  # Leave room for footer
        
        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)
        
        self._render_screen_footer(console, "Any key: Back to list, ESC: Close")
    
    def render_top_status_bar(self, console: tcod.console.Console, game):
        """Render the top status bar across the full width."""
        # Clear the entire top line (full screen width)
        for x in range(GameConfig.SCREEN_WIDTH):
            render_char_safe(console, x, 0, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Color coding for status values
        cpu_color = self._get_cpu_color(game.player.cpu)
        heat_color = self._get_heat_color(game.player.heat)
        detection_color = self._get_detection_color(game.player.detection)
        ram_color = Colors.RED if game.player.ram_used > game.player.ram_total else Colors.GREEN
        
        # Build status line
        status_parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            f"Heat:{game.player.heat:3d}°C/{game.player.max_heat}°C" if game.player.max_heat > 100 else f"Heat:{game.player.heat:3d}°C",
            f"Det:{int(game.player.detection):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB",
            f"Turn:{game.turn:4d}",
            "Press ? for help"
        ]
        
        colors = [cpu_color, heat_color, detection_color, ram_color, Colors.UI_TEXT, Colors.ELECTRIC_PURPLE]
        
        x_pos = 1
        for part, color in zip(status_parts, colors):
            # Allow status bar to extend across full width
            if x_pos + len(part) < GameConfig.SCREEN_WIDTH - 1:
                render_char_safe(console, x_pos, 0, part, fg=color, bg=Colors.UI_BG)
                x_pos += len(part) + 2
    
    def _get_cpu_color(self, cpu: int) -> Tuple[int, int, int]:
        """Get color for CPU display."""
        if cpu < 30:
            return Colors.RED
        elif cpu < 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_heat_color(self, heat: int) -> Tuple[int, int, int]:
        """Get color for heat display."""
        if heat > 80:
            return Colors.RED
        elif heat > 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_detection_color(self, detection: float) -> Tuple[int, int, int]:
        """Get color for detection display."""
        if detection > 75:
            return Colors.RED
        elif detection > 50:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def render_bottom_panel(self, console: tcod.console.Console, game):
        """Render the bottom information panel."""
        # Clear panel area
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(GameConfig.PANEL_Y(), GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Panel border
        border = "┌" + "─" * (GameConfig.GAME_AREA_WIDTH() - 2) + "┐"
        render_char_safe(console, 0, GameConfig.PANEL_Y(), border, fg=Colors.LOG_BORDER, bg=Colors.UI_BG)
        
        # Equipped exploits (2 lines)
        self._render_equipped_exploits_panel(console, game)
        
        # Temporary conditions/effects (1 line)
        self._render_temporary_conditions(console, game)
    
    
    def _render_equipped_exploits_panel(self, console: tcod.console.Console, game):
        """Render equipped exploits in bottom panel using 2 lines."""
        y1 = GameConfig.PANEL_Y() + 1
        y2 = GameConfig.PANEL_Y() + 2
        
        render_char_safe(console, 1, y1, "Exploits:", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)
        
        equipped_exploits = game.player.inventory_manager.equipped_exploits[:5]
        
        # Fixed layout: exploits 1,2,3 on first line, 4,5 on second line
        line1_exploits = []
        line2_exploits = []
        
        for i, exploit_key in enumerate(equipped_exploits):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                heat_cost = exploit.heat
                if game.player.temporary_effects['exploit_efficiency_turns'] > 0:
                    heat_cost = int(heat_cost * 0.6)
                
                heat_ok = game.player.heat + heat_cost <= game.player.max_heat
                color = Colors.GREEN if heat_ok else Colors.RED
                exploit_text = f"{i+1}.{exploit.name}"
                
                # First 3 exploits go on first line, remaining on second line
                if i < 3:
                    line1_exploits.append((exploit_key, exploit_text, color, i+1))
                else:
                    line2_exploits.append((exploit_key, exploit_text, color, i+1))
        
        # Render first line exploits
        x_pos = 11
        for exploit_key, exploit_text, color, slot_num in line1_exploits:
            render_char_safe(console, x_pos, y1, exploit_text, fg=color, bg=Colors.UI_BG)
            x_pos += len(exploit_text) + 2
        
        # Render second line exploits
        if line2_exploits:
            render_char_safe(console, 1, y2, "        ", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)  # Indent to align
            x_pos = 11
            for exploit_key, exploit_text, color, slot_num in line2_exploits:
                render_char_safe(console, x_pos, y2, exploit_text, fg=color, bg=Colors.UI_BG)
                x_pos += len(exploit_text) + 2
    
    def _render_temporary_conditions(self, console: tcod.console.Console, game):
        """Render all temporary conditions with turn counts remaining."""
        y = GameConfig.PANEL_Y() + 3
        
        conditions = []
        
        # Player temporary effects (from codes and other sources)
        for effect_name, turns in game.player.temporary_effects.items():
            if turns > 0:
                display_name = effect_name.replace('_turns', '').replace('_', ' ').title()
                condition_text = f"{display_name}({turns})"
                
                # Color conditions based on their type
                if effect_name == 'data_mimic_turns':
                    color = Colors.BLUE  # Invisible effect
                elif effect_name == 'speed_boost_turns':
                    color = self._get_data_code_color_for_effect(game, 'speed_boost', Colors.YELLOW)
                elif effect_name == 'movement_slowed_turns':
                    color = Colors.ORANGE  # Movement slowed effect
                elif effect_name == 'enhanced_vision_turns':
                    color = self._get_data_code_color_for_effect(game, 'enhanced_vision', Colors.ELECTRIC_BLUE)
                elif effect_name == 'exploit_efficiency_turns':
                    color = self._get_data_code_color_for_effect(game, 'exploit_efficiency', Colors.ELECTRIC_PURPLE)
                elif effect_name == 'virus_turns':
                    color = Colors.DARK_GREEN  # Virus effect
                else:
                    color = Colors.WHITE  # Default color for other effects
                
                conditions.append((condition_text, color))
        
        # Threat scan effect
        if game.game_state.threat_scan_turns > 0:
            conditions.append((f"Threat Scan({game.game_state.threat_scan_turns})", Colors.ELECTRIC_PURPLE))
        
        # Speed moves remaining (from speed boost)
        if game.player.speed_moves_remaining > 0:
            conditions.append((f"Speed Moves({game.player.speed_moves_remaining})", Colors.YELLOW))
        
        if conditions:
            # Print the "Conditions:" label
            x = 1
            render_char_safe(console, x, y, "Conditions: ", fg=Colors.CYAN, bg=Colors.UI_BG)
            x += len("Conditions: ")
            
            # Print each condition with its appropriate color
            for i, (condition_text, color) in enumerate(conditions):
                if i > 0:
                    render_char_safe(console, x, y, " ", fg=Colors.CYAN, bg=Colors.UI_BG)
                    x += 1
                render_char_safe(console, x, y, condition_text, fg=color, bg=Colors.UI_BG)
                x += len(condition_text)
        else:
            render_char_safe(console, 1, y, "Conditions: None", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
    
    def _get_data_code_color_for_effect(self, game, effect_key: str, fallback_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Get the code color for a specific effect based on the current game's randomization."""
        color_map = {
            'crimson': Colors.CRIMSON,
            'azure': Colors.AZURE, 
            'emerald': Colors.EMERALD,
            'golden': Colors.GOLDEN,
            'violet': Colors.VIOLET,
            'silver': Colors.SILVER
        }
        
        # Find which color has this effect in the current game
        for color_name, (effect, _) in game.data_patch_effects.items():
            if effect == effect_key:
                return color_map.get(color_name, fallback_color)
        
        return fallback_color
    
    
    def render_system_log(self, console: tcod.console.Console, game):
        """Render the system log on the right side."""
        # Draw log border
        for y in range(GameConfig.SCREEN_HEIGHT):
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), y, '│', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Log header - moved down one line to avoid covering status bar
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 1, "SYSTEM LOG", fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 2, "─" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Clear log area - start from line 3 to account for header repositioning
        for x in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            for y in range(3, GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)
        
        # Process and display messages
        self._render_log_messages(console, game)
    
    def _render_log_messages(self, console: tcod.console.Console, game):
        """Render log messages with proper wrapping."""
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.SCREEN_HEIGHT - 3  # Adjusted for header repositioning
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines
        
        for i, (line, color) in enumerate(visible_lines):
            y_pos = 3 + i  # Start from line 3 to avoid header
            if y_pos < GameConfig.SCREEN_HEIGHT:
                render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)
    
    def _wrap_messages(self, messages: List[Tuple[str, Tuple[int, int, int]]]) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Wrap long messages across multiple lines."""
        wrapped_lines = []
        max_msg_width = GameConfig.LOG_WIDTH - 2
        
        for message, color in messages:
            if len(message) <= max_msg_width:
                wrapped_lines.append((message, color))
            else:
                # Wrap long messages
                words = message.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_msg_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_lines.append((current_line, color))
                        current_line = word
                
                if current_line:
                    wrapped_lines.append((current_line, color))
        
        return wrapped_lines


class MapRenderer:
    """Renders the game map and entities."""
    
    def render_map(self, console: tcod.console.Console, game):
        """Render the complete game map."""
        try:
            camera_offset = self._calculate_camera_offset(game.player)
            vision_range = game.player.get_vision_range()
            
            # Render in layers for proper z-ordering
            self._render_terrain(console, game, camera_offset, vision_range)
            self._render_vision_overlays(console, game, camera_offset, vision_range)
            self._render_patrol_routes(console, game, camera_offset, vision_range)
            self._render_gateway(console, game, camera_offset, vision_range)
            self._render_enemies(console, game, camera_offset, vision_range)
            self._render_player(console, game, camera_offset)
            self._render_targeting_cursor(console, game, camera_offset)
            
        except Exception as e:
            # Fallback error display
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            error_msg = f"Map Error: {str(e)[:50]} (line {line_no})"
            render_char_safe(console, 1, 1, error_msg, fg=Colors.RED, bg=Colors.BLACK)
            # Also log to console and file
            logging.error(f"Map rendering error: {e}")
            logging.error(traceback.format_exc())
    
    def _calculate_camera_offset(self, player) -> Position:
        """Calculate camera offset to center on player."""
        camera_x = max(0, min(GameConfig.MAP_WIDTH - GameConfig.GAME_AREA_WIDTH(), 
                             player.x - GameConfig.GAME_AREA_WIDTH() // 2))
        # Viewable height is from screen row 1 to (SCREEN_HEIGHT - PANEL_HEIGHT - 1)
        viewable_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewable_height, 
                             player.y - viewable_height // 2))
        return Position(camera_x, camera_y)
    
    def _render_terrain(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render basic terrain (floors, walls, items)."""
        for screen_x in range(GameConfig.GAME_AREA_WIDTH()):
            for screen_y in range(1, GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                world_pos = Position(screen_x + camera_offset.x, screen_y - 1 + camera_offset.y)
                
                if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    # Check if player can see this position using TCOD FOV
                    if game.player.can_see_through_walls():
                        # Enhanced vision can see through walls within range
                        distance = game.player.position.distance_to(world_pos)
                        can_see = distance <= vision_range
                    else:
                        # Use TCOD FOV system for proper corner visibility
                        can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)
                    
                    # Check if this tile has been explored (memory system)
                    explored = (world_pos.x, world_pos.y) in game.game_map.explored_tiles
                    
                    if can_see:
                        self._render_tile(console, screen_x, screen_y, world_pos, game)
                    elif explored:
                        # Render remembered tile with dimmed colors
                        self._render_remembered_tile(console, screen_x, screen_y, world_pos, game)
                    else:
                        # Fog of war
                        render_char_safe(console, screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
                else:
                    # Outside map bounds
                    render_char_safe(console, screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
    
    def _render_remembered_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game):
        """Render a tile from memory with dimmed neon colors."""
        # Check if this position has a revealed special node
        pos_tuple = (world_pos.x, world_pos.y)
        if pos_tuple in game.game_state.revealed_special_nodes:
            node_type = game.game_state.revealed_special_nodes[pos_tuple]
            if node_type == "cooling":
                # Position 4 = ♦ for cooling nodes, faded cyan
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=(0, 120, 120), bg=Colors.BLACK)
            elif node_type == "cpu":
                # Position 3 = ♥ for CPU nodes, faded red
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=(120, 0, 0), bg=Colors.BLACK)
            elif node_type == "ghost":
                # Position 6 = ♠ for ghost nodes, faded purple
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=(80, 0, 120), bg=Colors.BLACK)
            elif node_type == "gateway":
                # Gateway in memory - darker yellow
                darker_yellow = (180, 150, 0)
                render_char_safe(console, screen_x, screen_y, '>', fg=darker_yellow, bg=Colors.BLACK)
            return
        
        # Only render basic terrain in memory, not dynamic elements
        if game.game_map.is_wall(world_pos):
            # Smart wall system for remembered walls too
            wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[wall_char]), fg=(60, 70, 90), bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            # Position 8 = ◘ (inverse bullet) for remembered shadows
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[8]), fg=(50, 20, 80), bg=Colors.BLACK)
        else:
            # Position 7 = • (bullet) for remembered empty spaces
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[7]), fg=(90, 90, 130), bg=Colors.BLACK)
    
    def _render_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game):
        """Render a single tile."""
        # SYMBOL CONVENTIONS:
        # - Letters (A-Z): Reserved for enemies only (Scanner=S, Patrol=P, Bot=B, etc.)
        # - ASCII symbols: Used for everything else (walls, items, terrain, etc.)
        # - NO unicode characters allowed for terminal compatibility
        
        # Priority order for tile rendering
        if game.game_map.is_wall(world_pos):
            # Smart wall system - analyze neighbors to pick correct wall piece
            wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[wall_char]), fg=Colors.WALL, bg=Colors.BLACK)
        elif game.game_map.is_cooling_node(world_pos):
            # Position 4 = ♦ (diamond) 
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "cooling"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=Colors.CYAN, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=(0, 120, 120), bg=Colors.BLACK)
        elif game.game_map.is_cpu_recovery_node(world_pos):
            # Position 3 = ♥ (heart)
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "cpu"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=Colors.RED, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=(120, 0, 0), bg=Colors.BLACK)
        elif game.game_map.is_ghost_node(world_pos):
            # Position 6 = ♠ (spade)
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "ghost"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=(80, 0, 120), bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.code_hacks:
            patch = game.game_map.code_hacks[(world_pos.x, world_pos.y)]
            # Map patch color names to actual color tuples
            color_map = {
                'crimson': Colors.CRIMSON,
                'azure': Colors.AZURE,
                'emerald': Colors.EMERALD,
                'golden': Colors.GOLDEN,
                'violet': Colors.VIOLET,
                'silver': Colors.SILVER
            }
            # Handle color_name (should always be string)
            if isinstance(patch.color_name, str):
                actual_color = color_map.get(patch.color_name.lower(), Colors.WHITE)
            else:
                # This should never happen, but fallback to white
                logging.warning(f"CodeHack color_name is not string: {patch.color_name} (type: {type(patch.color_name)})")
                actual_color = Colors.WHITE
            # Position 21 = § (section) for code fragments  
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[21]), fg=actual_color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.exploit_pickups:
            try:
                exploit_item = game.game_map.exploit_pickups[(world_pos.x, world_pos.y)]
                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    exploit_category = exploit_def.category  # Fixed: was exploit_class, should be category
                    # Get color from config, fallback to magenta
                    from data_loading import DataLoader
                    config = DataLoader.load_config()
                    exploit_colors = config.get("colors", {}).get("exploits", {})
                    color_data = exploit_colors.get(exploit_category, [255, 20, 255])
                    
                    # Validate color data and convert to tuple
                    color_tuple = ensure_color_tuple(color_data)
                    
                    render_char_safe(console, screen_x, screen_y, '&', fg=color_tuple, bg=Colors.BLACK)
                else:
                    logging.error(f"Unknown exploit key: {exploit_item.exploit_key}")
                    render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
            except AttributeError as e:
                logging.error(f"ExploitDefinition attribute error at {world_pos}: {e}")
                logging.error(f"Available attributes: {dir(exploit_def) if 'exploit_def' in locals() else 'exploit_def not defined'}")
                logging.error(traceback.format_exc())
                # Fallback to default magenta color - don't change appearance due to errors
                render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
            except Exception as e:
                logging.error(f"Unexpected error rendering exploit at {world_pos}: {e}")
                logging.error(traceback.format_exc())
                # Fallback to default magenta color - don't change appearance due to errors
                render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.permanent_upgrades:
            upgrade_key = game.game_map.permanent_upgrades[(world_pos.x, world_pos.y)]
            upgrade = GameUpgrades.UPGRADES[upgrade_key]
            color = self._get_upgrade_color(upgrade.color)
            # Position 9 = ○ for permanent upgrades (different colors)  
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[9]), fg=color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.story_fragments:
            # Position 14 = ♫ (double music note) for lore scraps
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[14]), fg=Colors.CYAN, bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            # Position 8 = ◘ (inverse bullet) for shadows
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[8]), fg=(80, 40, 120), bg=Colors.BLACK)
        else:
            # Position 7 = • (bullet) for empty space
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[7]), fg=Colors.FLOOR, bg=Colors.BLACK)
    
    
    def _get_smart_wall_character(self, game_map, x: int, y: int) -> int:
        """Get the appropriate wall character based on neighboring walls."""
        # Check which directions have walls
        n = game_map.is_wall(Position(x, y - 1))  # North
        s = game_map.is_wall(Position(x, y + 1))  # South  
        e = game_map.is_wall(Position(x + 1, y))  # East
        w = game_map.is_wall(Position(x - 1, y))  # West
        
        # Use proper box-drawing characters from game config
        if n and s and e and w:
            return 197  # ┼ cross (4-way intersection)
        elif n and s and e and not w:
            return 195  # ├ T pointing right  
        elif n and s and not e and w:
            return 180  # ┤ T pointing left
        elif n and not s and e and w:
            return 193  # ┴ T pointing up
        elif not n and s and e and w:
            return 194  # ┬ T pointing down
        elif n and not s and e and not w:
            return 192  # └ bottom-left corner
        elif n and not s and not e and w:
            return 217  # ┘ bottom-right corner
        elif not n and s and e and not w:
            return 218  # ┌ top-left corner
        elif not n and s and not e and w:
            return 191  # ┐ top-right corner
        elif n and s and not e and not w:
            return 179  # │ vertical line
        elif not n and not s and e and w:
            return 196  # ─ horizontal line
        # Handle single-connection walls (stubs)
        elif n and not s and not e and not w:
            return 179  # │ vertical stub pointing up
        elif not n and s and not e and not w:
            return 179  # │ vertical stub pointing down  
        elif not n and not s and e and not w:
            return 196  # ─ horizontal stub pointing right
        elif not n and not s and not e and w:
            return 196  # ─ horizontal stub pointing left
        # Isolated wall - use a different character instead of solid block
        else:
            return 254  # ■ small solid square instead of full block

    def _get_upgrade_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple for permanent upgrade."""
        color_map = {
            'BRIGHT_BLUE': Colors.ELECTRIC_BLUE,
            'BRIGHT_GREEN': Colors.ACID_GREEN, 
            'BRIGHT_CYAN': Colors.CYAN
        }
        return color_map.get(color_name, Colors.WHITE)
    
    def _render_vision_overlays(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render enemy vision range overlays."""
        if game.player.is_invisible():
            return
        
        threat_scan_active = game.game_state.threat_scan_turns > 0
        
        for enemy in game.enemies:
            if enemy.disabled_turns > 0:
                continue
            
            # Show vision overlays for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
            
            if can_see_enemy or threat_scan_active:
                overlay_color = self._get_vision_overlay_color(enemy.state)
                
                # If revealed by threat scan, make overlay more translucent
                if threat_scan_active and not can_see_enemy:
                    overlay_color = tuple(c // 2 for c in overlay_color)  # Make it dimmer
                
                self._render_enemy_vision_range(console, enemy, camera_offset, overlay_color, game.game_map)
    
    def _get_vision_overlay_color(self, enemy_state: EnemyState) -> Tuple[int, int, int]:
        """Get vision overlay color based on enemy state."""
        if enemy_state == EnemyState.HOSTILE:
            return Colors.VISION_HOSTILE
        elif enemy_state == EnemyState.ALERT:
            return Colors.VISION_ALERT
        else:
            return Colors.VISION_UNAWARE
    
    def _render_enemy_vision_range(self, console: tcod.console.Console, enemy, camera_offset: Position, overlay_color: Tuple[int, int, int], game_map):
        """Render vision range for a single enemy."""
        # Enemies have full vision range regardless of whether they're in shadow
        # The shadow mechanic only affects whether they can see players IN shadow
        actual_vision_range = enemy.type_data.vision
        
        for dx in range(-actual_vision_range, actual_vision_range + 1):
            for dy in range(-actual_vision_range, actual_vision_range + 1):
                # Use Euclidean distance to match the actual detection logic
                if dx*dx + dy*dy <= actual_vision_range*actual_vision_range:
                    screen_x = enemy.x - camera_offset.x + dx
                    screen_y = enemy.y - camera_offset.y + dy + 1
                    
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, screen_x, screen_y, overlay_color)
    
    def _safely_overlay_tile(self, console: tcod.console.Console, x: int, y: int, bg_color: Tuple[int, int, int]):
        """Safely overlay background color on existing tile."""
        try:
            current_char = console.ch[x, y]
            if current_char != ord(' '):  # Don't overlay fog of war
                current_fg = console.fg[x, y]
                if hasattr(current_fg, '__iter__') and len(current_fg) >= 3:
                    fg_tuple = tuple(current_fg[:3])
                    render_char_safe(console, x, y, chr(current_char), fg=fg_tuple, bg=bg_color)
        except (IndexError, ValueError) as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            # Silent fail for overlay errors, but could log line_no if needed for debugging
            pass
    
    def _render_patrol_routes(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render next 3 predicted moves for all moving enemies."""
        
        threat_scan_active = game.game_state.threat_scan_turns > 0
        
        for enemy in game.enemies:
            # Show patrol routes for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
            
            # Show movement intentions for all visible enemies (permanent ability)
            if can_see_enemy:
                next_positions = game.get_enemy_next_positions(enemy, 3)
                
                for i, point in enumerate(next_positions):
                    screen_x = point.x - camera_offset.x
                    screen_y = point.y - camera_offset.y + 1
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        # Preserve existing background color if present (e.g., vision overlay)
                        try:
                            current_bg = tuple(console.bg[screen_x, screen_y][:3])
                            # Use current background if it's not black, otherwise use black
                            bg_color = current_bg if current_bg != (0, 0, 0) else Colors.BLACK
                        except (IndexError, AttributeError):
                            bg_color = Colors.BLACK
                        
                        # Ensure bg_color is a proper tuple to prevent TCOD ColorRGB errors
                        bg_color = ensure_color_tuple(bg_color)
                        
                        # Check if background is bright (sum of RGB values > 30 indicates brighter area)
                        bg_brightness = sum(bg_color) if bg_color != Colors.BLACK else 0
                        is_bright_area = bg_brightness > 30
                        
                        # Large bright yellow shapes for all enemy movement prediction
                        if i == 0:
                            # Next immediate move - brightest and largest
                            color = (255, 255, 50)
                            # Position 9 = ○ (circle) for enemy move intent
                            symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                        elif i == 1:
                            # Second move - slightly dimmer but still bright
                            color = (240, 240, 30)
                            # Position 9 = ○ (circle) for enemy move intent
                            symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                        else:
                            # Third+ moves - still bright yellow
                            color = (220, 220, 20)
                            # Position 9 = ○ (circle) for enemy move intent
                            symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                        render_char_safe(console, screen_x, screen_y, symbol, fg=color, bg=bg_color)
    
    def _render_gateway(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render the level gateway."""
        if not game.game_map.gateway:
            return
        
        screen_x = game.game_map.gateway.x - camera_offset.x
        screen_y = game.game_map.gateway.y - camera_offset.y + 1
        
        if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
            1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            distance = game.player.position.distance_to(game.game_map.gateway)
            # Check if player can see the gateway (respecting walls)
            can_see = (distance <= vision_range and 
                      (game.player.can_see_through_walls() or 
                       game.game_map.has_line_of_sight(game.player.position, game.game_map.gateway)))
            
            if can_see:
                # Gateway is currently visible - render in full brightness and remember it
                render_char_safe(console, screen_x, screen_y, '>', fg=Colors.GATEWAY, bg=Colors.BLACK)
                # Add to memory system
                if not hasattr(game.game_state, 'revealed_special_nodes'):
                    game.game_state.revealed_special_nodes = {}
                gateway_pos = (game.game_map.gateway.x, game.game_map.gateway.y)
                game.game_state.revealed_special_nodes[gateway_pos] = "gateway"
            else:
                # Check if gateway was previously seen (in memory)
                gateway_pos = (game.game_map.gateway.x, game.game_map.gateway.y)
                if (hasattr(game.game_state, 'revealed_special_nodes') and 
                    gateway_pos in game.game_state.revealed_special_nodes and
                    game.game_state.revealed_special_nodes[gateway_pos] == "gateway"):
                    # Render remembered gateway in darker yellow
                    darker_yellow = (180, 150, 0)  # Darker version of gateway color
                    render_char_safe(console, screen_x, screen_y, '>', fg=darker_yellow, bg=Colors.BLACK)
    
    def _render_enemies(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render all enemies and their last known positions."""
        # First, render last known positions as ghosts
        for enemy_id, (position, turn_seen) in game.game_map.last_known_enemy_positions.items():
            # Find if this enemy is still alive and currently visible
            current_enemy = None
            currently_visible = False
            for enemy in game.enemies:
                if enemy.id == enemy_id:
                    current_enemy = enemy
                    if game.player.can_see_enemy(enemy, game.game_map):
                        currently_visible = True
                    break
            
            # Only show ghost if enemy is not currently visible and was seen recently
            from game_config import GameBalance
            if not currently_visible and turn_seen > game.turn - GameBalance.ENEMY_MEMORY_TURNS:
                screen_x = position.x - camera_offset.x
                screen_y = position.y - camera_offset.y + 1
                
                if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
                    1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    if current_enemy:
                        # Dimmed ghost of living enemy
                        ghost_color = tuple(c // 3 for c in current_enemy.get_color())
                        render_char_safe(console, screen_x, screen_y, '?', fg=ghost_color, bg=Colors.BLACK)
        
        # Then render currently visible enemies
        for enemy in game.enemies:
            screen_x = enemy.x - camera_offset.x
            screen_y = enemy.y - camera_offset.y + 1
            
            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                # Check if Threat Scan is active (shows all enemies)
                threat_scan_active = game.game_state.threat_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
                
                if can_see_enemy or threat_scan_active:
                    if threat_scan_active and not can_see_enemy:
                        # Threat scan reveals enemy with special highlighting
                        render_char_safe(console, screen_x, screen_y, enemy.type_data.symbol, 
                                    fg=Colors.CYAN, bg=(20, 0, 20))  # Cyan text on dark purple bg
                    else:
                        # Normal enemy rendering
                        render_char_safe(console, screen_x, screen_y, enemy.type_data.symbol, 
                                    fg=enemy.get_color(), bg=Colors.BLACK)
    
    def _render_player(self, console: tcod.console.Console, game, camera_offset: Position):
        """Render the player character."""
        player_screen_x = game.player.x - camera_offset.x
        player_screen_y = game.player.y - camera_offset.y + 1
        
        if (0 <= player_screen_x < GameConfig.GAME_AREA_WIDTH() and 
            1 <= player_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            player_color = self._get_player_color(game.player)
            # Position 2 = ☻ (inverse smiley)
            try:
                render_char_safe(console, player_screen_x, player_screen_y, chr(tcod.tileset.CHARMAP_CP437[2]), fg=player_color, bg=Colors.BLACK)
            except Exception as e:
                import logging
                logging.error(f"PLAYER RENDER ERROR: {e}, color={player_color}")
                # Fallback to simple @ character
                render_char_safe(console, player_screen_x, player_screen_y, '@', fg=Colors.WHITE, bg=Colors.BLACK)
        else:
            # Only log when player is actually off screen - this shouldn't happen often
            import logging
            logging.error(f"PLAYER OFF SCREEN: world=({game.player.x}, {game.player.y}), "
                         f"camera=({camera_offset.x}, {camera_offset.y}), "
                         f"screen=({player_screen_x}, {player_screen_y})")
    
    def _get_player_color(self, player) -> Tuple[int, int, int]:
        """Get player color based on current state."""
        if player.temporary_effects['virus_turns'] > 0:
            return Colors.DARK_GREEN
        elif player.is_invisible():
            return Colors.BLUE
        elif player.temporary_effects['speed_boost_turns'] > 0:
            return Colors.YELLOW
        elif player.cpu < 30 or player.heat > 80 or player.detection > 75:
            return Colors.RED
        else:
            return Colors.PLAYER
    
    def _render_targeting_cursor(self, console: tcod.console.Console, game, camera_offset: Position):
        """Render targeting cursor and range indicator."""
        if not game.targeting_mode:
            return
        
        cursor_screen_x = game.cursor_position.x - camera_offset.x
        cursor_screen_y = game.cursor_position.y - camera_offset.y + 1
        
        if (0 <= cursor_screen_x < GameConfig.GAME_AREA_WIDTH() and 
            1 <= cursor_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            render_char_safe(console, cursor_screen_x, cursor_screen_y, 'X', fg=Colors.RED, bg=Colors.BLACK)
        
        # Show range indicator and area effect
        if game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            self._render_targeting_range(console, game.player.position, exploit.range, camera_offset)
            
            # Show area effect for AREA targeting mode
            if exploit.targeting == TargetingMode.AREA:
                self._render_targeting_area(console, game.cursor_position, camera_offset)
    
    def _render_targeting_range(self, console: tcod.console.Console, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator."""
        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                if dx*dx + dy*dy <= range_val*range_val:
                    range_screen_x = center.x - camera_offset.x + dx
                    range_screen_y = center.y - camera_offset.y + dy + 1
                    
                    if (0 <= range_screen_x < GameConfig.GAME_AREA_WIDTH() and 
                        1 <= range_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, range_screen_x, range_screen_y, (40, 40, 40))
    
    def _render_targeting_area(self, console: tcod.console.Console, center: Position, camera_offset: Position):
        """Render 3x3 area effect indicator for area targeting."""
        for dx in range(-1, 2):  # -1, 0, 1 for 3x3 area
            for dy in range(-1, 2):
                area_screen_x = center.x - camera_offset.x + dx
                area_screen_y = center.y - camera_offset.y + dy + 1
                
                if (0 <= area_screen_x < GameConfig.GAME_AREA_WIDTH() and 
                    1 <= area_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    # Use a brighter overlay to distinguish from range indicator
                    self._safely_overlay_tile(console, area_screen_x, area_screen_y, (60, 60, 20))