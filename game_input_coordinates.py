"""
game_input_coordinates.py - Coordinate Conversion

Handles pixel-to-world coordinate conversion for input events.
Supports both glyph mode (console tiles) and graphics mode (sprite grid).

This module was extracted from game_input.py to provide focused,
testable coordinate conversion logic separate from input handling.
"""

import logging
from typing import Optional, Tuple
from game_config import GameConfig
from game_entities import Position
from game_coordinate_helpers import CoordinateHelpers
from game_errors import GameErrorHandler


class InputCoordinateConverter:
    """Handles pixel-to-world coordinate conversion for input system."""

    @staticmethod
    def get_window_dimensions(renderer, game) -> Tuple[int, int]:
        """
        Get window dimensions from context.

        Tries renderer.context first, then game.context, then fallback.

        Args:
            renderer: GameRenderer instance (may be None)
            game: Game instance

        Returns:
            Tuple of (window_width, window_height) in pixels
        """
        context = None
        if renderer and hasattr(renderer, 'context'):
            context = renderer.context
        elif hasattr(game, 'context'):
            context = game.context

        if context and hasattr(context, 'sdl_window'):
            return context.sdl_window.size
        return (800, 600)  # Fallback

    @staticmethod
    def pixel_to_world_position(
        pixel_x: float,
        pixel_y: float,
        renderer,
        game,
        graphics_mode: str,
        camera_offset: Optional[Position] = None
    ) -> Optional[Position]:
        """Convert mouse pixel coords to world coords.

        Conversion flow:
        1. Convert pixels to sprite grid coordinates (in graphics mode) or console chars (in glyph mode)
        2. Subtract status bar height to get viewport coords
        3. Add camera offset to get world coords
        4. Validate against map bounds

        Args:
            pixel_x: SDL pixel X coordinate
            pixel_y: SDL pixel Y coordinate
            renderer: GameRenderer instance (may be None)
            game: Game instance
            graphics_mode: Current graphics mode ("graphics" or "glyph")
            camera_offset: Optional camera offset Position. If None, will calculate from game state.

        Returns:
            Position in world coordinates, or None if outside valid game area
        """
        # Convert pixels to grid coordinates
        if graphics_mode == "graphics":
            # In graphics mode, sprites are rendered at pixel = grid * tile_dimension
            if renderer and hasattr(renderer, 'tile_manager') and renderer.tile_manager:
                tile_x, tile_y = CoordinateHelpers.pixel_to_sprite_grid(
                    pixel_x, pixel_y,
                    renderer.tile_manager.tile_width,
                    renderer.tile_manager.tile_height
                )
            else:
                logging.error(f"Graphics mode but renderer not available: renderer={renderer}, has_tile_mgr={hasattr(renderer, 'tile_manager') if renderer else False}")
                return None
        else:
            # In glyph mode, use console character conversion
            try:
                window_w, window_h = InputCoordinateConverter.get_window_dimensions(renderer, game)
                tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
                    pixel_x, pixel_y, window_w, window_h
                )
            except Exception as e:
                GameErrorHandler.handle_error(e, "pixel_conversion", "Failed to convert pixels in glyph mode", fatal=False)
                return None

        # Use graphics_mode to handle coordinate conversion
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)
        status_bar_height = GameConfig.STATUS_BAR_HEIGHT()

        # In GRAPHICS mode, grid coords from pixel_to_sprite_grid are RENDERING positions
        # Sprites render at: pixel = (viewport_x, viewport_y + status_bar) * tile_dimensions
        # So grid coords INCLUDE status bar offset - we need to subtract it
        # In GLYPH mode, tile coords from pixel_to_char_coords are CONSOLE positions
        # Console tiles map directly: viewport = console_tile - status_bar

        if graphics_mode == "graphics":
            # Grid coordinates include status bar offset, subtract to get viewport
            viewport_x = tile_x
            viewport_y = tile_y - status_bar_height
        else:
            # Console coordinates, subtract status bar to get viewport
            viewport_x = tile_x
            viewport_y = tile_y - status_bar_height

        # Validate viewport coordinates
        if viewport_y < 0 or viewport_y >= viewport_height:
            return None
        if viewport_x < 0 or viewport_x >= viewport_width:
            return None

        # Use the camera offset from the last render for consistency
        # This ensures input conversion matches what's actually displayed on screen
        if camera_offset is None:
            # Try to use last_camera_offset from game
            if hasattr(game, 'last_camera_offset') and game.last_camera_offset:
                camera_x = game.last_camera_offset.x
                camera_y = game.last_camera_offset.y
            else:
                # Fallback: calculate fresh (shouldn't happen after first render)
                center_x = game.player.x
                center_y = game.player.y
                camera_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                                     center_x - viewport_width // 2))
                camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                                     center_y - viewport_height // 2))
        else:
            camera_x = camera_offset.x
            camera_y = camera_offset.y

        # Convert to world coordinates
        world_x = viewport_x + camera_x
        world_y = viewport_y + camera_y

        # Validate against map bounds
        if not (0 <= world_x < GameConfig.MAP_WIDTH and
                0 <= world_y < GameConfig.MAP_HEIGHT):
            return None

        return Position(world_x, world_y)
