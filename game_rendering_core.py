#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Rendering Core

Main rendering orchestrator that coordinates all visual output.
Manages dual rendering modes (ASCII glyphs and graphical tiles) and delegates
specialized rendering tasks to dedicated subsystems (UI, map, dialogue).
Uses layered SDL rendering in graphics mode for sprite-over-UI composition.
"""

import tcod
import os
import logging
from typing import List

from game_config import GameConfig
from game_entities import Position, Colors, ensure_color_tuple
from game_ui import render_char_safe
from game_coordinate_helpers import CoordinateHelpers
from game_unicode_chars import GameGlyphs

# Import specialized renderers
from game_rendering_ui import UIRenderer
from game_rendering_glyphs import GlyphsMapRenderer
from game_rendering_graphics import GraphicsMapRenderer
from game_dialogue_system import UnifiedRenderer


def draw_bordered_box(console: tcod.console.Console, start_x: int, start_y: int,
                     width: int, height: int, border_color: tuple, bg_color: tuple):
    """
    Draw a bordered box with background fill using TCOD primitives.

    Uses TCOD's built-in draw_rect and draw_frame for efficiency.
    Ensures color values are tuples to prevent TCOD ColorRGB errors.

    Args:
        console: TCOD console to draw on
        start_x: Left edge of box
        start_y: Top edge of box
        width: Box width in characters
        height: Box height in characters
        border_color: RGB tuple for border color
        bg_color: RGB tuple for background fill
    """
    # Ensure colors are tuples to prevent TCOD ColorRGB errors
    border_color = ensure_color_tuple(border_color)
    bg_color = ensure_color_tuple(bg_color)

    # Draw background
    console.draw_rect(start_x, start_y, width, height, ord(' '), fg=Colors.WHITE, bg=bg_color)

    # Draw double-line border manually (using GameGlyphs constants)
    # Top border
    render_char_safe(console, start_x, start_y, GameGlyphs.WALL_TOP_LEFT, fg=border_color, bg=bg_color)
    for x in range(start_x + 1, start_x + width - 1):
        render_char_safe(console, x, start_y, GameGlyphs.WALL_HORIZONTAL, fg=border_color, bg=bg_color)
    render_char_safe(console, start_x + width - 1, start_y, GameGlyphs.WALL_TOP_RIGHT, fg=border_color, bg=bg_color)

    # Side borders
    for y in range(start_y + 1, start_y + height - 1):
        render_char_safe(console, start_x, y, GameGlyphs.WALL_VERTICAL, fg=border_color, bg=bg_color)
        render_char_safe(console, start_x + width - 1, y, GameGlyphs.WALL_VERTICAL, fg=border_color, bg=bg_color)

    # Bottom border
    render_char_safe(console, start_x, start_y + height - 1, GameGlyphs.WALL_BOTTOM_LEFT, fg=border_color, bg=bg_color)
    for x in range(start_x + 1, start_x + width - 1):
        render_char_safe(console, x, start_y + height - 1, GameGlyphs.WALL_HORIZONTAL, fg=border_color, bg=bg_color)
    render_char_safe(console, start_x + width - 1, start_y + height - 1, GameGlyphs.WALL_BOTTOM_RIGHT, fg=border_color, bg=bg_color)


class GameRenderer:
    """
    Main rendering orchestrator that coordinates all visual output.

    Manages dual rendering modes (ASCII glyphs vs graphical tiles) and delegates
    specialized rendering to subsystems:
    - UIRenderer: Status bars, panels, screens
    - GlyphsMapRenderer: ASCII map rendering
    - GraphicsMapRenderer: Sprite-based map rendering with SDL
    - UnifiedRenderer: Dialogue system overlays

    In graphics mode, uses layered SDL rendering:
    1. Sprites (terrain + entities) rendered to SDL
    2. Status effects rendered as sprite overlays
    3. Vision/targeting overlays rendered to SDL
    4. Console UI rendered as transparent texture overlay

    Key attributes:
        ui_renderer: Handles all UI panels and screens
        glyphs_renderer: ASCII map rendering for glyph mode
        graphics_renderer: Sprite rendering for graphics mode
        tile_manager: Manages sprite tiles and dimensions
        context: TCOD context with SDL renderer access
    """

    def __init__(self, settings=None, tile_manager=None, context=None):
        """
        Initialize the renderer with dependency injection.

        Creates both glyph and graphics renderers to support runtime mode switching.
        Graphics renderer requires tile_manager and context with SDL support.

        Args:
            settings: Game settings for graphics mode detection
            tile_manager: Manages sprite tiles (required for graphics mode)
            context: TCOD context with SDL renderer (required for graphics mode)
        """
        self.settings = settings
        self.tile_manager = tile_manager
        self.context = context
        self.ui_renderer = UIRenderer(settings=settings, context=context, tile_manager=tile_manager)
        # UnifiedRenderer is stateless, no need to initialize

        # Initialize both map renderers
        self.glyphs_renderer = GlyphsMapRenderer(settings=settings)
        self.graphics_renderer = GraphicsMapRenderer(tile_manager=tile_manager, context=context, settings=settings)

    def _is_graphics_mode_available(self) -> bool:
        """
        Check if graphics rendering is available and enabled.

        Returns True if all requirements are met:
        - Settings exist with graphics_mode == "graphics"
        - tile_manager is available
        - context exists with SDL renderer support
        - console_render exists in context

        Returns:
            bool: True if graphics mode can be used, False otherwise
        """
        return (self.settings and
                self.settings.graphics_mode == "graphics" and
                self.tile_manager is not None and
                self.context is not None and
                hasattr(self.context, 'sdl_renderer') and
                self.context.sdl_renderer is not None and
                hasattr(self.context, 'console_render') and
                self.context.console_render is not None)

    def render_game(self, console: tcod.console.Console, game, context=None):
        """
        Render the complete game state based on current screen mode.

        Delegates to specialized renderers based on active screen:
        - Story fragments, lore viewer, help, inventory: Full console overlays
        - Main game: Layered rendering (graphics mode) or console (glyph mode)

        Always renders dialogue system last as highest-priority overlay.
        Graphics mode handles SDL present() internally for overlay screens.

        Args:
            console: TCOD console to render to
            game: GameEngine instance with complete game state
            context: Optional TCOD context (unused, kept for compatibility)
        """
        # Check if we should use graphics mode rendering
        should_use_graphics = self._is_graphics_mode_available()

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
        elif game.show_achievements:
            console.clear()
            self.ui_renderer.render_achievements_screen(console, game)
        elif game.show_inventory:
            console.clear()
            self.ui_renderer.render_inventory_screen(console, game)
        else:
            # Main game screen uses special graphics rendering
            self._render_main_game_screen(console, game)
            return  # Main game screen handles its own present() in graphics mode

        # Render dialogue system on top of EVERYTHING (highest priority overlay)
        if game.dialogue_state.is_active():
            # Use UnifiedRenderer for all dialogue types
            dialogue = game.dialogue_state.get_active()
            if dialogue:
                UnifiedRenderer.render(console, dialogue, game.dialogue_state,
                                     game.last_mouse_tile_x, game.last_mouse_tile_y)

        # Render achievement popups (high priority, after dialogue or at same level)
        # Only show if enabled in settings (default: True)
        if (hasattr(game, 'achievement_popup_manager') and
            hasattr(game, 'settings') and
            game.settings.show_achievement_popups):
            game.achievement_popup_manager.update()
            game.achievement_popup_manager.render(console)

        # For overlay screens (inventory, help, lore), we need to present in graphics mode too
        if should_use_graphics:
            # Set background to black before clearing
            self.context.sdl_renderer.draw_color = (0, 0, 0, 255)
            self.context.sdl_renderer.clear()

            # Render sprites if the screen supports them (e.g., GraphicalHelpMenu)
            if game.show_help:
                self.ui_renderer.render_help_sprites()

            console_texture = self.context.console_render.render(console)
            self.context.sdl_renderer.copy(console_texture)
            self.context.sdl_renderer.present()

    def _render_main_game_screen(self, console: tcod.console.Console, game):
        """
        Render the main game screen with mode-specific layering.

        Graphics mode (SDL layered rendering):
        1. Sprites layer: Terrain + entities rendered to SDL
        2. Status effects layer: Visual status indicators over sprites
        3. Overlay layer: Vision cones, movement prediction, targeting
        4. Console UI layer: Transparent texture with opaque UI panels

        Glyph mode (traditional console):
        - Single-pass console rendering with all elements

        Uses transparency masking in graphics mode to allow sprites to show
        through the game viewport area while keeping UI panels opaque.

        Args:
            console: TCOD console to render to
            game: GameEngine instance with complete game state
        """
        # Check if we should use graphics mode rendering
        should_use_graphics = self._is_graphics_mode_available()

        if should_use_graphics:
            # === GRAPHICS MODE: Sprites + Console UI ===
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
            # Clear console (alpha=255 by default)
            console.clear()

            # Make ENTIRE console transparent FIRST using CoordinateHelpers
            CoordinateHelpers.set_alpha_region(
                console, x=0, y=0, width=console.width, height=console.height, alpha=0
            )

            # Render UI panels - we'll set their alpha explicitly after
            self.ui_renderer.render_top_status_bar(console, game)
            self.ui_renderer.render_info_panel(console, game)
            self.ui_renderer.render_bottom_panel(console, game)
            self.ui_renderer.render_system_log(console, game)
            self.ui_renderer.render_inspection_panel(console, game)

            # Set UI panel areas back to opaque using CoordinateHelpers
            panel_y = GameConfig.PANEL_Y()
            log_x = GameConfig.GAME_AREA_WIDTH()
            log_start_y = GameConfig.LOG_START_Y()

            # Top status bar (full width, height 1)
            CoordinateHelpers.set_alpha_region(
                console, x=0, y=0, width=console.width, height=1, alpha=255
            )
            # Bottom panel (full width, from PANEL_Y to bottom)
            CoordinateHelpers.set_alpha_region(
                console, x=0, y=panel_y, width=console.width, height=console.height - panel_y, alpha=255
            )
            # Info panel and system log (from GAME_AREA_WIDTH to right edge, from top to panel start)
            CoordinateHelpers.set_alpha_region(
                console, x=log_x, y=0, width=console.width - log_x, height=panel_y, alpha=255
            )

            # Render dialogue system on console AFTER transparency pass (highest priority, opaque backgrounds)
            if game.dialogue_state.is_active():
                # Use UnifiedRenderer for all dialogue types
                dialogue = game.dialogue_state.get_active()
                if dialogue:
                    UnifiedRenderer.render(console, dialogue, game.dialogue_state,
                                         game.last_mouse_tile_x, game.last_mouse_tile_y)

            # Render achievement popups (high priority, after dialogue or at same level)
            if hasattr(game, 'achievement_popup_manager'):
                game.achievement_popup_manager.update()
                game.achievement_popup_manager.render(console)

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
            self.ui_renderer.render_info_panel(console, game)
            self.ui_renderer.render_bottom_panel(console, game)
            self.ui_renderer.render_system_log(console, game)
            self.ui_renderer.render_inspection_panel(console, game)

            # Render dialogue system (highest priority overlay) - handles gateway, death, victory
            if game.dialogue_state.is_active():
                # Use UnifiedRenderer for all dialogue types
                dialogue = game.dialogue_state.get_active()
                if dialogue:
                    UnifiedRenderer.render(console, dialogue, game.dialogue_state,
                                         game.last_mouse_tile_x, game.last_mouse_tile_y)

            # Render achievement popups (high priority, after dialogue or at same level)
            if hasattr(game, 'achievement_popup_manager'):
                game.achievement_popup_manager.update()
                game.achievement_popup_manager.render(console)


# Legacy alias for backward compatibility
Renderer = GameRenderer
