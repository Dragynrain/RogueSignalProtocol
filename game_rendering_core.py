#!/usr/bin/env python3
"""
Game Rendering Core
Main renderer orchestrator and shared utilities.
"""

import tcod
import os
import logging
from typing import List

from game_config import GameConfig
from game_entities import Position, Colors, ensure_color_tuple
from game_ui import render_char_safe

# Import specialized renderers
from game_rendering_ui import UIRenderer
from game_rendering_glyphs import GlyphsMapRenderer
from game_rendering_graphics import GraphicsMapRenderer


def draw_bordered_box(console: tcod.console.Console, start_x: int, start_y: int,
                     width: int, height: int, border_color: tuple, bg_color: tuple):
    """Draw a bordered box with background fill - extracted utility function."""
    # Ensure colors are tuples to prevent TCOD ColorRGB errors
    border_color = ensure_color_tuple(border_color)
    bg_color = ensure_color_tuple(bg_color)

    # Use TCOD's built-in box drawing for efficiency
    console.draw_rect(start_x, start_y, width, height, ord(' '), fg=Colors.WHITE, bg=bg_color)

    # Draw border using TCOD's box drawing
    console.draw_frame(start_x, start_y, width, height,
                      fg=border_color, bg=bg_color, clear=False)


class GameRenderer:
    """Unified game renderer - consolidates all rendering functionality."""

    def __init__(self, settings=None, tile_manager=None, context=None):
        self.settings = settings
        self.tile_manager = tile_manager
        self.context = context
        self.ui_renderer = UIRenderer()

        # Initialize both map renderers
        self.glyphs_renderer = GlyphsMapRenderer(settings=settings)
        self.graphics_renderer = GraphicsMapRenderer(tile_manager=tile_manager, context=context, settings=settings)

    def render_game(self, console: tcod.console.Console, game, context=None):
        """Render the complete game state."""
        # Check if we should use graphics mode rendering
        should_use_graphics = (self.settings and
                               self.settings.graphics_mode == "graphics" and
                               self.tile_manager is not None and
                               self.context is not None and
                               hasattr(self.context, 'sdl_renderer') and
                               self.context.sdl_renderer is not None and
                               hasattr(self.context, 'console_render') and
                               self.context.console_render is not None)

        # Only clear console for overlay screens that need full console rendering
        # Main game screen handles clearing differently for graphics vs glyph mode
        if game.show_story_fragment is not None:
            console.clear()
            self.ui_renderer.render_story_fragment_screen(console, game, game.show_story_fragment)
        elif game.show_lore_viewer:
            console.clear()
            self.ui_renderer.render_lore_viewer_screen(console, game)
        elif game.show_help:
            console.clear()
            self.ui_renderer.render_help_screen(console)
        elif game.show_inventory:
            console.clear()
            self.ui_renderer.render_inventory_screen(console, game)
        else:
            # Main game screen uses special graphics rendering
            self._render_main_game_screen(console, game)
            return  # Main game screen handles its own present() in graphics mode

        # Render dialogue system on top of EVERYTHING (highest priority overlay)
        if game.dialogue_manager.is_active():
            self._render_dialogue(console, game)

        # For overlay screens (inventory, help, lore), we need to present in graphics mode too
        if should_use_graphics:
            self.context.sdl_renderer.clear()
            console_texture = self.context.console_render.render(console)
            self.context.sdl_renderer.copy(console_texture)
            self.context.sdl_renderer.present()

    def _render_main_game_screen(self, console: tcod.console.Console, game):
        """
        Render the main game screen.
        Uses layered SDL rendering in graphics mode, traditional console in glyph mode.
        """
        # Check if we should use graphics mode rendering
        should_use_graphics = (self.settings and
                               self.settings.graphics_mode == "graphics" and
                               self.tile_manager is not None and
                               self.context is not None and
                               hasattr(self.context, 'sdl_renderer') and
                               self.context.sdl_renderer is not None and
                               hasattr(self.context, 'console_render') and
                               self.context.console_render is not None)

        if should_use_graphics:
            # === GRAPHICS MODE: Sprites + Console UI ===
            logging.info("Using graphics mode rendering")

            # Set SDL clear color to black (for unexplored areas)
            self.context.sdl_renderer.draw_color = (0, 0, 0, 255)
            self.context.sdl_renderer.clear()

            # LAYER 1: Render sprites (terrain + entities) directly to SDL
            self.graphics_renderer.render_sprites_layer(game)

            # LAYER 2: Render status effect boxes over sprites
            self.graphics_renderer.render_status_effects_layer(game)

            # LAYER 2.5: Render overlay elements (vision, movement prediction, targeting) to SDL
            self.graphics_renderer.render_overlay_layer(game)

            # LAYER 3: Render console UI as texture overlay
            # Clear console and render ONLY UI panels (not game area)
            console.clear()
            self.ui_renderer.render_top_status_bar(console, game)
            self.ui_renderer.render_bottom_panel(console, game)
            self.ui_renderer.render_system_log(console, game)

            # Render dialogue system on console if active (covers everything)
            if game.dialogue_manager.is_active():
                self._render_dialogue(console, game)

            # Set game area background alpha to 0 for transparency
            # This allows sprites rendered below to show through the console texture
            # Game area: x=0-54, y=1-44 (excluding top bar, bottom panel, and system log)
            for x in range(GameConfig.GAME_AREA_WIDTH()):
                for y in range(1, GameConfig.PANEL_Y()):
                    console.rgba["bg"][x, y, 3] = 0  # Alpha = 0 (fully transparent)

            # Convert console to texture and overlay on top of sprites
            console_texture = self.context.console_render.render(console)
            self.context.sdl_renderer.copy(console_texture)

            # Present final frame
            self.context.sdl_renderer.present()

        else:
            # === GLYPH MODE: Traditional Console Rendering ===
            # Clear console for glyph mode - map rendering will overwrite everything
            console.clear()

            self.ui_renderer.render_top_status_bar(console, game)
            self.glyphs_renderer.render_map(console, game)
            self.ui_renderer.render_bottom_panel(console, game)
            self.ui_renderer.render_system_log(console, game)

            # Render dialogue system (highest priority overlay) - handles gateway, death, victory
            if game.dialogue_manager.is_active():
                self._render_dialogue(console, game)

    def _render_victory_message(self, console: tcod.console.Console):
        """Render victory message."""
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2

        box_width = 50  # Increased from 38 to fit longer messages
        box_height = 10
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        draw_bordered_box(console, start_x, start_y, box_width, box_height,
                         Colors.GREEN, Colors.UI_BG)

        # Victory message - centered properly within the larger box
        title = "BREAKTHROUGH TO THE INTERNET!"
        line1 = "You've escaped into the digital realm"
        line2 = "The entire world wide web awaits you!"
        line3 = "Freedom at last..."
        instruction = "Press any key to continue"

        render_char_safe(console, center_x - len(title) // 2, start_y + 2, title, fg=Colors.GREEN, bg=Colors.UI_BG)
        render_char_safe(console, center_x - len(line1) // 2, start_y + 3, line1, fg=Colors.WHITE, bg=Colors.UI_BG)
        render_char_safe(console, center_x - len(line2) // 2, start_y + 4, line2, fg=Colors.CYAN, bg=Colors.UI_BG)
        render_char_safe(console, center_x - len(line3) // 2, start_y + 5, line3, fg=Colors.ELECTRIC_BLUE, bg=Colors.UI_BG)
        render_char_safe(console, center_x - len(instruction) // 2, start_y + 7, instruction, fg=Colors.YELLOW, bg=Colors.UI_BG)

    def _render_gateway_confirmation(self, console: tcod.console.Console):
        """Render gateway confirmation dialog."""
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2

        box_width = 30
        box_height = 6
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        draw_bordered_box(console, start_x, start_y, box_width, box_height,
                         Colors.CYAN, Colors.UI_BG)

        # Title and message
        render_char_safe(console, center_x - 7, start_y + 1, "NETWORK GATEWAY", fg=Colors.YELLOW, bg=Colors.UI_BG)
        render_char_safe(console, center_x - 12, start_y + 2, "Proceed to next network?", fg=Colors.WHITE, bg=Colors.UI_BG)

        # Options
        render_char_safe(console, center_x - 5, start_y + 4, "Y: Yes  N: No", fg=Colors.CYAN, bg=Colors.UI_BG)

    def _render_dialogue(self, console: tcod.console.Console, game):
        """Render active dialogue popup."""
        config = game.dialogue_manager.get_active_config()
        if not config:
            return

        # Calculate dialogue box dimensions - use SCREEN_WIDTH for proper centering
        box_width = 60
        box_height = 12
        center_x = GameConfig.SCREEN_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        box_x = center_x - box_width // 2
        box_y = center_y - box_height // 2

        # Ensure colors are tuples
        from game_entities import ensure_color_tuple
        border_color = ensure_color_tuple(config.color_scheme["border"])
        bg_color = ensure_color_tuple(config.color_scheme["background"])

        # Draw dialogue box using TCOD's built-in box drawing
        console.draw_rect(box_x, box_y, box_width, box_height, ord(' '), fg=Colors.WHITE, bg=bg_color)
        console.draw_frame(box_x, box_y, box_width, box_height, fg=border_color, bg=bg_color, clear=False)

        # Render title (centered)
        title_x = box_x + (box_width - len(config.title)) // 2
        render_char_safe(console, title_x, box_y + 1, config.title,
                        fg=config.color_scheme["title"], bg=bg_color)

        # Format message with context data
        try:
            formatted_message = config.message.format(**game.dialogue_manager.dialogue_data)
        except KeyError as e:
            logging.warning(f"Missing dialogue context data key: {e}")
            formatted_message = config.message

        # Render message (word-wrapped)
        message_lines = self._wrap_dialogue_text(formatted_message, box_width - 4)
        message_y = box_y + 3
        for i, line in enumerate(message_lines):
            if message_y + i < box_y + box_height - 3:  # Leave room for options
                render_char_safe(console, box_x + 2, message_y + i, line,
                               fg=config.color_scheme["message"], bg=bg_color)

        # Render options (centered at bottom)
        options_y = box_y + box_height - 2
        options_text = "  ".join(config.options)
        options_x = box_x + (box_width - len(options_text)) // 2
        render_char_safe(console, options_x, options_y, options_text,
                        fg=Colors.WHITE, bg=bg_color)

    def _wrap_dialogue_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width characters.
        Handles edge cases like words longer than max_width by breaking them.
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # If word itself is longer than max_width, break it into chunks
            if word_length > max_width:
                # First, flush current line if any
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_length = 0

                # Break the long word into chunks
                for i in range(0, word_length, max_width):
                    chunk = word[i:i + max_width]
                    lines.append(chunk)
                continue

            # Check if adding this word would exceed max_width
            space_needed = 1 if current_line else 0  # Space before word
            if current_length + space_needed + word_length <= max_width:
                current_line.append(word)
                current_length += space_needed + word_length
            else:
                # Start new line
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _render_death_message(self, console: tcod.console.Console):
        """Render death message with frame and black backgrounds."""
        # Ensure save is deleted on death (permadeath)
        save_path = "save_game.json"
        if os.path.exists(save_path):
            os.remove(save_path)

        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2

        # Background box with border
        box_width = 40
        box_height = 12
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        # Use TCOD's efficient drawing
        console.draw_rect(start_x, start_y, box_width, box_height, ord(' '), fg=Colors.WHITE, bg=Colors.BLACK)
        console.draw_frame(start_x, start_y, box_width, box_height, fg=Colors.RED, bg=Colors.BLACK, clear=False)

        # Death message
        render_char_safe(console, center_x - 10, start_y + 2, "CONSCIOUSNESS PURGED", fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, center_x - 17, start_y + 4, "Your consciousness failed to escape", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 14, start_y + 5, "the network and has been purged", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 10, start_y + 6, "from existence.", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 13, start_y + 7, "Other subjects will try again...", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)
        render_char_safe(console, center_x - 10, start_y + 9, "Press any key to restart", fg=Colors.CYAN, bg=Colors.BLACK)


# Legacy alias for backward compatibility
Renderer = GameRenderer
