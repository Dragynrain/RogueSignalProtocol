#!/usr/bin/env python3
"""
Tile Dimension Calculator
Pure functions for calculating tile/sprite dimensions based on window size and mode.
"""

from typing import Tuple
import logging

from game_config import GameConfig


class TileDimensionCalculator:
    """
    Pure functions for tile dimension calculations.

    Separates calculation logic from TileManager for better testability
    and clearer separation of concerns.
    """

    @staticmethod
    def calculate_from_window(window_size: Tuple[int, int], graphics_mode: str) -> Tuple[int, int]:
        """
        Calculate tile dimensions based on window size and graphics mode.

        Args:
            window_size: (width, height) in pixels
            graphics_mode: "graphics" or "glyph"

        Returns:
            Tuple of (tile_width, tile_height) in pixels
        """
        width, height = window_size

        if graphics_mode == "graphics":
            return TileDimensionCalculator._calc_graphics_mode(width, height)
        else:
            return TileDimensionCalculator._calc_glyph_mode(width, height)

    @staticmethod
    def _calc_graphics_mode(window_width: int, window_height: int) -> Tuple[int, int]:
        """
        Calculate tile dimensions for graphics mode with viewport scaling.

        In graphics mode, the viewport is smaller (half the size) which makes
        each sprite appear larger (2x zoom effect).

        Args:
            window_width: Window width in pixels
            window_height: Window height in pixels

        Returns:
            Tuple of (tile_width, tile_height) in pixels
        """
        # Get console grid dimensions for base calculation
        console_width = GameConfig.SCREEN_WIDTH
        console_height = GameConfig.SCREEN_HEIGHT

        # Calculate base tile size
        base_tile_width = window_width // console_width
        base_tile_height = window_height // console_height

        # Get viewport dimensions (smaller in graphics mode)
        viewport_width = GameConfig.VIEWPORT_WIDTH("graphics")
        viewport_height = GameConfig.VIEWPORT_HEIGHT("graphics")

        # Calculate game area dimensions
        game_area_width = GameConfig.GAME_AREA_WIDTH()
        viewable_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - GameConfig.STATUS_BAR_HEIGHT()

        # Scale up tiles to fill game area with smaller viewport
        tile_width = (base_tile_width * game_area_width) // viewport_width
        tile_height = (base_tile_height * viewable_height) // viewport_height

        return TileDimensionCalculator.validate_and_clamp(tile_width, tile_height)

    @staticmethod
    def _calc_glyph_mode(window_width: int, window_height: int) -> Tuple[int, int]:
        """
        Calculate tile dimensions for glyph/ASCII mode.

        In glyph mode, tiles match the console grid size.

        Args:
            window_width: Window width in pixels
            window_height: Window height in pixels

        Returns:
            Tuple of (tile_width, tile_height) in pixels
        """
        console_width = GameConfig.SCREEN_WIDTH
        console_height = GameConfig.SCREEN_HEIGHT

        tile_width = window_width // console_width
        tile_height = window_height // console_height

        return TileDimensionCalculator.validate_and_clamp(tile_width, tile_height)

    @staticmethod
    def validate_and_clamp(width: int, height: int) -> Tuple[int, int]:
        """
        Ensure tile dimensions meet minimum requirements for readability.

        Args:
            width: Proposed tile width
            height: Proposed tile height

        Returns:
            Tuple of (width, height) clamped to minimums
        """
        min_w = GameConfig.MIN_TILE_WIDTH()
        min_h = GameConfig.MIN_TILE_HEIGHT()

        clamped_width = max(min_w, width)
        clamped_height = max(min_h, height)

        if clamped_width != width:
            logging.warning(f"Tile width clamped to minimum: {clamped_width}px (was {width}px)")
        if clamped_height != height:
            logging.warning(f"Tile height clamped to minimum: {clamped_height}px (was {height}px)")

        return (clamped_width, clamped_height)

    @staticmethod
    def get_fallback_dimensions() -> Tuple[int, int]:
        """
        Get fallback tile dimensions when calculation fails.

        Returns:
            Tuple of (width, height) from config
        """
        return (GameConfig.FALLBACK_TILE_WIDTH(), GameConfig.FALLBACK_TILE_HEIGHT())
