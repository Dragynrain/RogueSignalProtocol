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
from game_dialogue_renderer import DialogueRenderer


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
        self.ui_renderer = UIRenderer(settings=settings, context=context, tile_manager=tile_manager)
        self.dialogue_renderer = DialogueRenderer()

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
            from game_dialogue import DialogueType
            dialogue_type = game.dialogue_manager.active_dialogue

            # Route to specific renderer based on dialogue type
            if dialogue_type == DialogueType.DEATH_MESSAGE:
                self.dialogue_renderer.render_death_message(console)
            elif dialogue_type == DialogueType.VICTORY_MESSAGE:
                self.dialogue_renderer.render_victory_message(console)
            elif dialogue_type == DialogueType.GATEWAY_CONFIRM:
                self.dialogue_renderer.render_gateway_confirmation(console)
            else:
                # Generic dialogue renderer (overclock warning, inventory attack, etc.)
                self.dialogue_renderer.render_dialogue(console, game)

        # For overlay screens (inventory, help, lore), we need to present in graphics mode too
        if should_use_graphics:
            self.context.sdl_renderer.clear()

            # Render sprites if the screen supports them (e.g., GraphicalHelpMenu)
            if game.show_help:
                self.ui_renderer.render_help_sprites()

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
            self.ui_renderer.render_inspection_panel(console, game)

            # Set game area background alpha to 0 for transparency BEFORE rendering dialogues
            # This allows sprites rendered below to show through the console texture
            # CRITICAL: Use ACTUAL array dimensions for bounds, not GameConfig
            actual_height, actual_width = console.rgba["bg"].shape[:2]

            # Clamp to actual array bounds to prevent index errors
            max_y = min(actual_height, GameConfig.PANEL_Y())
            max_x = min(actual_width, GameConfig.GAME_AREA_WIDTH())

            # Loop: y outer, x inner → indexing: [y, x]
            for y in range(1, max_y):
                for x in range(max_x):
                    console.rgba["bg"][y, x, 3] = 0  # Alpha = 0 (fully transparent)

            # Render dialogue system on console AFTER transparency pass (highest priority, opaque backgrounds)
            if game.dialogue_manager.is_active():
                from game_dialogue import DialogueType
                dialogue_type = game.dialogue_manager.active_dialogue

                # Route to specific renderer based on dialogue type
                if dialogue_type == DialogueType.DEATH_MESSAGE:
                    self.dialogue_renderer.render_death_message(console)
                elif dialogue_type == DialogueType.VICTORY_MESSAGE:
                    self.dialogue_renderer.render_victory_message(console)
                elif dialogue_type == DialogueType.GATEWAY_CONFIRM:
                    self.dialogue_renderer.render_gateway_confirmation(console)
                else:
                    # Generic dialogue renderer (overclock warning, inventory attack, etc.)
                    self.dialogue_renderer.render_dialogue(console, game)

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
            self.ui_renderer.render_inspection_panel(console, game)

            # Render dialogue system (highest priority overlay) - handles gateway, death, victory
            if game.dialogue_manager.is_active():
                from game_dialogue import DialogueType
                dialogue_type = game.dialogue_manager.active_dialogue

                # Route to specific renderer based on dialogue type
                if dialogue_type == DialogueType.DEATH_MESSAGE:
                    self.dialogue_renderer.render_death_message(console)
                elif dialogue_type == DialogueType.VICTORY_MESSAGE:
                    self.dialogue_renderer.render_victory_message(console)
                elif dialogue_type == DialogueType.GATEWAY_CONFIRM:
                    self.dialogue_renderer.render_gateway_confirmation(console)
                else:
                    # Generic dialogue renderer (overclock warning, inventory attack, etc.)
                    self.dialogue_renderer.render_dialogue(console, game)


# Legacy alias for backward compatibility
Renderer = GameRenderer
