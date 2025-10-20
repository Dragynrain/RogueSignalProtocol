#!/usr/bin/env python3
"""
Game Rendering Base
Base class for map renderers with common functionality.

COORDINATE SYSTEMS USED IN THIS CODEBASE:

1. CONSOLE COORDINATES (80x50 grid)
   - Used for: Text rendering, UI layout, menu positioning
   - Range: X: 0-79, Y: 0-49
   - Characters rendered at 10x16 pixels (tileset size)
   - Example: render_char_safe(console, 10, 5, "text")

2. GAME VIEWPORT COORDINATES (27x21 tiles in graphics mode)
   - Used for: Game map tile positions during gameplay
   - Calculated by: GameConfig.VIEWPORT_WIDTH/HEIGHT(graphics_mode)
   - Scaled to fit window using TileManager.tile_width/height
   - Example: viewport_x, viewport_y from camera position

3. SDL PIXEL COORDINATES (window resolution, e.g., 2560x1351)
   - Used for: Direct SDL sprite rendering
   - Full window pixel space
   - Example: SDL_Rect(pixel_x, pixel_y, sprite_w, sprite_h)

CONVERSION METHODS:
- _world_to_console(): World tile -> Console position
- _grid_to_pixel(): Game viewport -> SDL pixels (in-game)
- _console_to_pixel(): Console grid -> SDL pixels (menus)
- _is_in_viewport(): Check if world position is visible

CRITICAL RULES:
1. Menu rendering: Use console coords (80x50) + window scaling
2. Game rendering: Use viewport coords + TileManager dimensions
3. NEVER mix the two - they use different math!
"""

from typing import Tuple
from game_config import GameConfig
from game_entities import Position
from game_coordinate_helpers import CoordinateHelpers


class MapRendererBase:
    """Base class for map renderers with common functionality."""

    def __init__(self, tile_manager=None, context=None, settings=None):
        """
        Initialize MapRenderer with optional graphics support.

        Args:
            tile_manager: TileManager instance for sprite loading (None for glyph mode)
            context: TCOD context with SDL renderer (None for glyph mode)
            settings: GameSettings instance for accessing graphics_mode
        """
        self.tile_manager = tile_manager
        self.context = context
        self.settings = settings

    def _should_use_graphics(self):
        """Check if graphics mode is available and should be used."""
        return (self.tile_manager is not None and
                self.context is not None and
                hasattr(self.context, 'sdl_renderer') and
                self.context.sdl_renderer is not None)

    def _get_graphics_mode(self):
        """Get current graphics mode from settings."""
        if self.settings:
            return self.settings.graphics_mode
        return "glyph"

    def _world_to_console(self, world_x: int, world_y: int, camera_offset: Position) -> Tuple[int, int]:
        """
        Convert world coordinates to console coordinates based on viewport.

        COORDINATE SYSTEM: World (50x50 map) -> Console (80x50 grid)
        This is the fundamental conversion for all text rendering.

        Args:
            world_x: World X coordinate (0-49 in a 50x50 map)
            world_y: World Y coordinate (0-49 in a 50x50 map)
            camera_offset: Camera offset position (top-left of viewport)

        Returns:
            Tuple of (console_x, console_y) where:
            - console_x: Console X position (0-79)
            - console_y: Console Y position (1-49, accounting for status bar at row 0)
        """
        # Calculate viewport position (relative to camera)
        viewport_x = world_x - camera_offset.x
        viewport_y = world_y - camera_offset.y

        # Console position accounts for status bar at row 0
        console_x = viewport_x
        console_y = viewport_y + GameConfig.STATUS_BAR_HEIGHT()

        return (console_x, console_y)

    def _is_in_viewport(self, world_x: int, world_y: int, camera_offset: Position) -> bool:
        """
        Check if world coordinates are within the current viewport.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            camera_offset: Camera offset position

        Returns:
            True if position is in viewport
        """
        graphics_mode = self._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        viewport_x = world_x - camera_offset.x
        viewport_y = world_y - camera_offset.y

        return (0 <= viewport_x < viewport_width and
                0 <= viewport_y < viewport_height)

    def _calculate_camera_offset(self, player, game=None) -> Position:
        """
        Calculate camera offset to center on player or look cursor.

        Uses viewport dimensions based on graphics mode - smaller viewport
        in graphics mode for larger sprite appearance.

        Args:
            player: Player entity
            game: Game engine (optional, for look mode support)
        """
        graphics_mode = self._get_graphics_mode()

        # Get viewport dimensions (tiles visible, not console grid size)
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        # In look mode, center camera on cursor instead of player
        if game and game.look_mode and hasattr(game, 'look_cursor_position'):
            center_x = game.look_cursor_position.x
            center_y = game.look_cursor_position.y
        else:
            center_x = player.x
            center_y = player.y

        # Center camera on target position within the viewport
        camera_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                             center_x - viewport_width // 2))
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                             center_y - viewport_height // 2))

        return Position(camera_x, camera_y)

    def _grid_to_pixel(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """
        Convert grid coordinates to pixel coordinates for IN-GAME rendering.

        COORDINATE SYSTEM: Game viewport grid -> SDL pixels
        This is used for positioning sprites during gameplay.

        IMPORTANT: This uses TileManager dimensions which are viewport-scaled
        (e.g., 65x54 pixels per tile in 2x zoom mode). This is DIFFERENT from
        menu sprite positioning which uses window scaling.

        Args:
            screen_x: Grid x coordinate (0 to GAME_AREA_WIDTH)
            screen_y: Grid y coordinate (0 to SCREEN_HEIGHT)

        Returns:
            Tuple of (pixel_x, pixel_y) in SDL window space
        """
        if not self.tile_manager:
            return (0, 0)

        # Use viewport-scaled tile dimensions
        pixel_x = screen_x * self.tile_manager.tile_width
        pixel_y = screen_y * self.tile_manager.tile_height
        return (pixel_x, pixel_y)

    def _get_tile_rect(self, screen_x: int, screen_y: int) -> Tuple[int, int, int, int]:
        """
        Get pixel rectangle for a tile at grid coordinates.

        Args:
            screen_x: Grid x coordinate
            screen_y: Grid y coordinate

        Returns:
            Tuple of (x, y, width, height) in pixels for SDL rendering
        """
        if not self.tile_manager:
            return (0, 0, 0, 0)

        px, py = self._grid_to_pixel(screen_x, screen_y)
        return (px, py, self.tile_manager.tile_width, self.tile_manager.tile_height)

    def _console_to_pixels(self, console_x: int, console_y: int) -> Tuple[int, int]:
        """
        Convert console coordinates to pixel coordinates for MENU rendering.

        COORDINATE SYSTEM: Console grid (80x50) -> SDL pixels
        This is used for positioning sprites in menus to align with text.

        IMPORTANT: This uses window scaling (pixels per character) which is
        DIFFERENT from in-game rendering that uses TileManager dimensions.
        Both methods use the same sprite SIZE (TileManager dimensions) but
        different positioning math.

        Args:
            console_x: Console X coordinate (0-79)
            console_y: Console Y coordinate (0-49)

        Returns:
            Tuple of (pixel_x, pixel_y) in SDL window space
        """
        window_width, window_height = self._get_window_size()

        # Use CoordinateHelpers for consistent coordinate conversion
        return CoordinateHelpers.char_to_pixel_coords(
            console_x, console_y, window_width, window_height
        )

    def _get_window_size(self) -> Tuple[int, int]:
        """
        Get current window dimensions with fallback.

        Returns:
            Tuple of (width, height) in pixels
        """
        try:
            if hasattr(self.context, 'sdl_window') and self.context.sdl_window:
                return self.context.sdl_window.size
        except (AttributeError, TypeError):
            pass
        # Fallback to default resolution
        return (800, 600)
