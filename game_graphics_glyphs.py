#!/usr/bin/env python3
"""
Graphics Glyph Manager
Manages rendering of console glyphs as SDL textures for graphics mode.
This is a temporary hacky solution to overlay text glyphs on sprites until proper sprite assets are created.
"""

import tcod
import numpy as np
import logging
from typing import Dict, Tuple, Optional


class GlyphManager:
    """
    Manages console glyphs rendered as SDL textures for graphics mode overlay.

    This allows transparent glyph rendering over sprites by converting console characters
    to individual SDL textures with proper alpha channels.
    """

    def __init__(self, renderer, tileset: tcod.tileset.Tileset):
        """
        Initialize the glyph manager.

        Args:
            renderer: SDL renderer from context.sdl_renderer
            tileset: TCOD tileset to extract glyph pixel data from
        """
        self.renderer = renderer
        self.tileset = tileset
        self.glyph_cache: Dict[Tuple[int, Tuple[int, int, int]], object] = {}

        # Get tile dimensions from tileset
        self.glyph_width = tileset.tile_width
        self.glyph_height = tileset.tile_height

        logging.info(f"GlyphManager initialized with glyph size {self.glyph_width}x{self.glyph_height}")

    def get_glyph_texture(self, codepoint: int, color: Tuple[int, int, int]):
        """
        Get or create a cached glyph texture with the specified color.

        Args:
            codepoint: Character code to render
            color: RGB tuple for foreground color

        Returns:
            SDL texture of the glyph, or None if failed
        """
        cache_key = (codepoint, color)

        # Return cached texture if available
        if cache_key in self.glyph_cache:
            return self.glyph_cache[cache_key]

        # Extract glyph pixel data from tileset
        try:
            glyph_pixels = self.tileset.get_tile(codepoint)

            if glyph_pixels is None or glyph_pixels.size == 0:
                logging.warning(f"Failed to get tile for codepoint {codepoint}")
                return None

            # Glyph pixels are RGBA array with shape (height, width, 4)
            # Apply color tinting: replace white pixels with the desired color, preserve alpha
            colored_glyph = self._apply_color_tint(glyph_pixels, color)

            # Upload to SDL as texture
            texture = self.renderer.upload_texture(colored_glyph)

            # Enable alpha blending for transparency
            from tcod.sdl.render import BlendMode
            texture.blend_mode = BlendMode.BLEND

            # Cache the texture
            self.glyph_cache[cache_key] = texture

            return texture

        except Exception as e:
            logging.error(f"Failed to create glyph texture for codepoint {codepoint}: {e}")
            return None

    def _apply_color_tint(self, glyph_pixels: np.ndarray, color: Tuple[int, int, int]) -> np.ndarray:
        """
        Apply color tinting to glyph pixels.

        Replaces the RGB channels with the desired color while preserving alpha.

        Args:
            glyph_pixels: RGBA pixel array (height, width, 4)
            color: RGB tuple for tinting

        Returns:
            Tinted RGBA pixel array
        """
        # Make a copy to avoid modifying cached data
        tinted = glyph_pixels.copy()

        # For each pixel, if it has alpha > 0, replace RGB with the desired color
        # This effectively colorizes the glyph while preserving its shape via alpha
        alpha_mask = tinted[:, :, 3] > 0
        tinted[alpha_mask, 0] = color[0]  # R
        tinted[alpha_mask, 1] = color[1]  # G
        tinted[alpha_mask, 2] = color[2]  # B

        return tinted

    def render_glyph(self, codepoint: int, color: Tuple[int, int, int],
                     screen_x: int, screen_y: int, tile_width: int, tile_height: int):
        """
        Render a single glyph to the SDL renderer at the specified position.

        Args:
            codepoint: Character code to render
            color: RGB foreground color
            screen_x: Screen X position in console grid coordinates
            screen_y: Screen Y position in console grid coordinates
            tile_width: Width of each tile in pixels
            tile_height: Height of each tile in pixels
        """
        texture = self.get_glyph_texture(codepoint, color)

        if texture is None:
            return

        # Calculate pixel position
        pixel_x = screen_x * tile_width
        pixel_y = screen_y * tile_height

        # Render the glyph texture
        dest_rect = (pixel_x, pixel_y, tile_width, tile_height)
        self.renderer.copy(texture, dest=dest_rect)

    def cleanup(self):
        """Clean up cached textures."""
        self.glyph_cache.clear()
        logging.info("GlyphManager cache cleared")
