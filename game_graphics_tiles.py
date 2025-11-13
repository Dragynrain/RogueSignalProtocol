#!/usr/bin/env python3
"""
Graphics Tile Manager - Sprite Loading and Management System

Handles loading, caching, and serving PNG sprites for graphics mode rendering.
Supports transparency, dynamic scaling, and window resize handling.

Rendering Modes:
- GRAPHICS: High-res PNG sprites (512x512 scaled to tile size)
- GLYPH: CP437 characters via TCOD tileset (fallback in classic mode)

This module is only active when graphics_mode == "graphics" in settings.
"""

import json
import logging
import os
import sys

import tcod
import tcod.sdl

from game_errors import GameErrorHandler
from game_tile_dimension_calculator import TileDimensionCalculator


class TileManager:
    """
    Centralized system for loading, caching, and serving tile graphics.

    Responsibilities:
    - Load PNG sprites from disk with transparency
    - Scale sprites to calculated tile dimensions
    - Cache textures for performance
    - Track which sprites are tintable (color_mod) vs non-tintable (outline boxes)
    - Handle window resize events (reload textures at new scale)
    - Graceful fallback when sprites missing
    """

    def __init__(self, context, settings):
        """
        Initialize TileManager with SDL context and game settings.

        Args:
            context: TCOD context with SDL renderer access
            settings: GameSettings instance with graphics_mode setting
        """
        self.context = context
        self.settings = settings

        # Texture cache: entity_name (str) -> SDL texture
        self.texture_cache: dict[str, tcod.sdl.render.Texture] = {}

        # Tintable flags: entity_name (str) -> bool
        # True = white sprite, use color_mod tinting
        # False = colored sprite, use outline boxes for status
        self.tintable_flags: dict[str, bool] = {}

        # Tile mapping: entity_name -> sprite filename
        self.tile_mappings: dict[str, dict] = {}

        # Calculated tile dimensions in pixels
        self.tile_width = 0
        self.tile_height = 0

        # Window resize tracking
        self.last_window_size: tuple[int, int] | None = None

        # Graphics directory path
        self.graphics_dir = self._get_graphics_dir()

        # Load tile mappings from JSON
        self._load_tile_mappings()

        # Calculate initial tile dimensions
        self._calculate_tile_dimensions()

    def _get_graphics_dir(self) -> str:
        """Get absolute path to graphics directory."""
        if getattr(sys, "frozen", False):
            # Running as compiled executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, "graphics")

    def _load_tile_mappings(self):
        """Load tile mappings from JSON configuration file."""
        mapping_file = "graphics_tiles.json"

        try:
            if not os.path.exists(mapping_file):
                logging.warning(f"Tile mapping file not found: {mapping_file}")
                logging.warning("Graphics mode will use glyph fallbacks for all entities")
                return

            with open(mapping_file, encoding="utf-8") as f:
                data = json.load(f)

            # Parse mappings and tintable flags
            self.tile_mappings = data

            # Extract tintable flags for quick lookup
            self._extract_tintable_flags(data)

            logging.debug(
                f"Graphics: Loaded tile mappings - {len(self.tile_mappings)} categories, {len(self.tintable_flags)} tintable flags"
            )

        except json.JSONDecodeError as e:
            GameErrorHandler.handle_error(
                e, "tile_mapping_load", f"Failed to parse {mapping_file}, using glyph fallbacks"
            )
        except Exception as e:
            GameErrorHandler.handle_error(
                e, "tile_mapping_load", "Error loading tile mappings, using glyph fallbacks"
            )

    def _extract_tintable_flags(self, data: dict):
        """
        Extract tintable flags from tile mappings for quick lookup.

        Args:
            data: Tile mapping dictionary from JSON
        """
        # Process player
        if "player" in data and isinstance(data["player"], dict):
            player_data = data["player"]
            self.tintable_flags["player"] = player_data.get("tintable", False)

        # Process categories (enemies, terrain, items)
        for category in ["enemies", "terrain", "items"]:
            if category in data and isinstance(data[category], dict):
                for entity_name, entity_data in data[category].items():
                    if isinstance(entity_data, dict):
                        self.tintable_flags[entity_name] = entity_data.get("tintable", False)

    def _calculate_tile_dimensions(self):
        """
        Calculate tile pixel dimensions based on window size and grid layout.

        Delegates to TileDimensionCalculator for pure calculation logic.
        """
        try:
            window_size = self._get_window_size()
            self.tile_width, self.tile_height = TileDimensionCalculator.calculate_from_window(
                window_size, self.settings.graphics_mode
            )
            logging.debug(
                f"Graphics: Calculated tile dimensions {self.tile_width}x{self.tile_height} for window {window_size[0]}x{window_size[1]}"
            )

        except Exception as e:
            GameErrorHandler.handle_error(
                e, "tile_dimensions", "Failed to calculate tile dimensions, using fallbacks"
            )
            # Use fallback dimensions from config
            self.tile_width, self.tile_height = TileDimensionCalculator.get_fallback_dimensions()
            logging.warning(f"Using fallback tile dimensions: {self.tile_width}x{self.tile_height}")

    def _get_window_size(self) -> tuple[int, int]:
        """
        Get current window pixel dimensions from SDL.

        Returns:
            Tuple of (width, height) in pixels
        """
        if hasattr(self.context, "sdl_window") and self.context.sdl_window:
            return self.context.sdl_window.size

        # Fallback to reasonable default
        logging.warning("Could not get window size from context, using default 800x600")
        return (800, 600)

    def load_tile(self, entity_name: str) -> tcod.sdl.render.Texture | None:
        """
        Load a tile sprite from disk, scale it, and create SDL texture.

        This method:
        1. Looks up sprite filename from tile_mappings
        2. Loads PNG file with PIL (preserves alpha channel)
        3. Scales from 512x512 to calculated tile size
        4. Uploads to SDL as RGBA texture
        5. Sets blend mode for transparency

        Args:
            entity_name: Name of entity (e.g., "player", "Scanner", "floor")

        Returns:
            SDL texture if successful, None if failed
        """
        # Look up sprite filename
        sprite_file = self._get_sprite_filename(entity_name)
        if not sprite_file:
            logging.debug(f"No sprite mapping for entity: {entity_name}")
            return None

        # Build full file path
        filepath = os.path.join(self.graphics_dir, sprite_file)

        if not os.path.exists(filepath):
            logging.warning(f"Sprite file not found: {filepath}")
            return None

        try:
            import numpy as np
            from PIL import Image

            # Load image preserving alpha channel
            pil_image = Image.open(filepath)

            # Convert to RGBA if not already (ensure alpha channel exists)
            if pil_image.mode != "RGBA":
                pil_image = pil_image.convert("RGBA")

            # Scale to calculated tile size (512x512 -> tile_width x tile_height)
            pil_image = pil_image.resize(
                (self.tile_width, self.tile_height),
                Image.Resampling.LANCZOS,  # High-quality downscaling
            )

            # Convert to numpy array (height, width, 4) for RGBA
            pixels = np.array(pil_image, dtype=np.uint8)

            # Upload to SDL as texture
            renderer = self.context.sdl_renderer
            if not renderer:
                logging.error("SDL renderer not available")
                return None

            texture = renderer.upload_texture(pixels)

            # Set blend mode for proper transparency rendering
            texture.blend_mode = tcod.sdl.render.BlendMode.BLEND
            logging.debug(
                f"Graphics: Loaded sprite '{entity_name}' from {sprite_file} ({self.tile_width}x{self.tile_height}px)"
            )
            return texture

        except Exception as e:
            GameErrorHandler.handle_error(e, "sprite_load", f"Failed to load sprite {filepath}")
            return None

    def _get_sprite_filename(self, entity_name: str) -> str | None:
        """
        Look up sprite filename for an entity from tile mappings.

        Args:
            entity_name: Name of entity

        Returns:
            Sprite filename (e.g., "player01.png") or None if not found
        """
        # Check if it's the player
        if entity_name == "player" and "player" in self.tile_mappings:
            player_data = self.tile_mappings["player"]
            if isinstance(player_data, dict) and "file" in player_data:
                return player_data["file"]

        # Check each category (enemies, terrain, items, special)
        for category in ["enemies", "terrain", "items", "special"]:
            if category in self.tile_mappings:
                category_data = self.tile_mappings[category]
                if isinstance(category_data, dict):
                    # Try exact match first
                    if entity_name in category_data:
                        entity_data = category_data[entity_name]
                        if isinstance(entity_data, dict) and "file" in entity_data:
                            return entity_data["file"]

                    # Try case-insensitive match (for enemy types like "scanner" vs "Scanner")
                    for key in category_data.keys():
                        if key.lower() == entity_name.lower():
                            entity_data = category_data[key]
                            if isinstance(entity_data, dict) and "file" in entity_data:
                                logging.debug(
                                    f"Graphics: Found sprite via case-insensitive match: {entity_name} -> {key}"
                                )
                                return entity_data["file"]

                        # Special case for admin -> Admin Avatar
                        if entity_name.lower() == "admin" and key == "Admin Avatar":
                            entity_data = category_data[key]
                            if isinstance(entity_data, dict) and "file" in entity_data:
                                logging.debug("Graphics: Found sprite for admin -> Admin Avatar")
                                return entity_data["file"]

        return None

    def get_tile(
        self, entity_name: str, fail_silently: bool = False
    ) -> tcod.sdl.render.Texture | None:
        """
        Get tile texture for an entity (cached or load on-demand).

        Uses lazy loading: sprites are loaded on first access and cached.

        Args:
            entity_name: Name of entity
            fail_silently: If False, raise exception on missing textures (default)
                          If True, return None for backwards compatibility

        Returns:
            SDL texture if available, None if no sprite or load failed (only if fail_silently=True)

        Raises:
            RuntimeError: If texture cannot be loaded and fail_silently=False
        """
        # Check cache first
        if entity_name in self.texture_cache:
            cached = self.texture_cache[entity_name]
            if cached is None and not fail_silently:
                raise RuntimeError(f"Failed to load required texture: {entity_name}")
            return cached

        # Not in cache - try to load
        texture = self.load_tile(entity_name)

        # Cache result (even if None, to avoid repeated load attempts)
        self.texture_cache[entity_name] = texture

        # Fail fast on missing critical textures
        if texture is None and not fail_silently:
            raise RuntimeError(f"Failed to load required texture: {entity_name}")

        return texture

    def is_tintable(self, entity_name: str) -> bool:
        """
        Check if sprite should use color_mod tinting or outline boxes.

        Args:
            entity_name: Name of entity

        Returns:
            True if sprite should use color_mod (white base sprite)
            False if sprite should use outline boxes (colored base sprite)
        """
        return self.tintable_flags.get(entity_name, False)

    def has_sprite(self, entity_name: str) -> bool:
        """
        Check if entity has a sprite available.

        Args:
            entity_name: Name of entity

        Returns:
            True if sprite is mapped and available
        """
        return self._get_sprite_filename(entity_name) is not None

    def extract_sprite_colors(self, entity_name: str, num_colors: int = 5) -> list:
        """
        Extract representative colors from a sprite for particle effects.

        Samples colors from different regions of the sprite to create a
        varied color palette for particle explosions.

        Args:
            entity_name: Name of entity to extract colors from
            num_colors: Number of colors to sample (default: 5)

        Returns:
            List of RGB tuples [(r, g, b), ...], or fallback white if extraction fails
        """
        # Look up sprite filename
        sprite_file = self._get_sprite_filename(entity_name)
        if not sprite_file:
            logging.debug(f"No sprite for color extraction: {entity_name}")
            return [(255, 255, 255)]  # Fallback to white

        # Build full file path
        filepath = os.path.join(self.graphics_dir, sprite_file)

        if not os.path.exists(filepath):
            logging.warning(f"Sprite file not found for color extraction: {filepath}")
            return [(255, 255, 255)]

        try:
            import numpy as np
            from PIL import Image

            # Load sprite image
            pil_image = Image.open(filepath)

            # Convert to RGBA if not already
            if pil_image.mode != "RGBA":
                pil_image = pil_image.convert("RGBA")

            # Convert to numpy array
            pixels = np.array(pil_image, dtype=np.uint8)

            # Get dimensions
            height, width = pixels.shape[:2]

            # Sample colors from random points across the sprite
            colors = []
            attempts = 0
            max_attempts = 100  # Try lots of samples to find good colors

            # Sample random points until we get enough good colors
            while len(colors) < num_colors and attempts < max_attempts:
                attempts += 1

                # Random point, avoiding edges (10% margin)
                x = np.random.randint(int(width * 0.1), int(width * 0.9))
                y = np.random.randint(int(height * 0.1), int(height * 0.9))

                # Get pixel color (RGBA)
                pixel = pixels[y, x]
                r, g, b, a = pixel

                # Skip transparent/semi-transparent pixels
                if a < 200:
                    continue

                # Skip very dark pixels (likely background or shadows)
                brightness = r + g + b
                if brightness < 100:  # Skip near-black pixels
                    continue

                # Skip pure black pixels
                if r == 0 and g == 0 and b == 0:
                    continue

                # Skip very desaturated colors (grays)
                max_channel = max(r, g, b)
                min_channel = min(r, g, b)
                if max_channel > 0 and (max_channel - min_channel) < 30:
                    continue

                # Good color found!
                color = (int(r), int(g), int(b))
                if color not in colors:  # Avoid duplicates
                    colors.append(color)

            # If we didn't get enough colors from sampling points, calculate average
            if len(colors) < 3:
                # Calculate average color from all bright visible pixels
                alpha_channel = pixels[:, :, 3]
                visible_mask = alpha_channel > 200

                if np.any(visible_mask):
                    visible_pixels = pixels[visible_mask]
                    # Filter to only bright pixels
                    brightness = (
                        visible_pixels[:, 0].astype(int)
                        + visible_pixels[:, 1].astype(int)
                        + visible_pixels[:, 2].astype(int)
                    )
                    bright_mask = brightness > 150

                    if np.any(bright_mask):
                        bright_pixels = visible_pixels[bright_mask]
                        avg_r = int(np.mean(bright_pixels[:, 0]))
                        avg_g = int(np.mean(bright_pixels[:, 1]))
                        avg_b = int(np.mean(bright_pixels[:, 2]))
                        colors.append((avg_r, avg_g, avg_b))

            # Ensure we have at least one color
            if not colors:
                logging.debug(
                    f"[COLOR EXTRACT] No bright colors found for {entity_name}, using fallback bright color"
                )
                # Use a bright fallback color instead of white
                colors = [(200, 150, 255)]  # Light purple fallback
            else:
                logging.debug(
                    f"[COLOR EXTRACT] Got {len(colors)} colors for {entity_name}: {colors}"
                )

            return colors

        except Exception as e:
            GameErrorHandler.handle_error(
                e, "color_extract", f"Failed to extract colors from sprite {filepath}"
            )
            return [(255, 255, 255)]

    def check_and_handle_resize(self) -> bool:
        """
        Check if window was resized and reload textures if needed.

        Only reloads if window size changed by more than 10% (avoids
        constant reloading during resize drag).

        Returns:
            True if textures were reloaded, False otherwise
        """
        current_size = self._get_window_size()

        if self.last_window_size is None:
            self.last_window_size = current_size
            return False

        # Calculate percentage change
        width_change = abs(current_size[0] - self.last_window_size[0]) / self.last_window_size[0]
        height_change = abs(current_size[1] - self.last_window_size[1]) / self.last_window_size[1]

        # Reload if change > 10%
        if width_change > 0.1 or height_change > 0.1:
            self._reload_all_textures(current_size)
            self.last_window_size = current_size
            return True

        return False

    def _reload_all_textures(self, new_window_size: tuple[int, int]):
        """
        Recalculate tile size and reload all cached textures.

        Args:
            new_window_size: New window dimensions (width, height) in pixels
        """
        # Recalculate tile dimensions
        old_size = (self.tile_width, self.tile_height)
        self._calculate_tile_dimensions()
        new_size = (self.tile_width, self.tile_height)

        # Get list of entities that were loaded
        loaded_entities = [
            name for name, texture in self.texture_cache.items() if texture is not None
        ]

        logging.debug(
            f"Graphics: Window resize {new_window_size[0]}x{new_window_size[1]}px - reloading {len(loaded_entities)} textures (tile size {old_size[0]}x{old_size[1]} -> {new_size[0]}x{new_size[1]})"
        )

        # Clear cache (textures will be garbage collected)
        self.texture_cache.clear()

        # Lazy reload - textures will reload on next get_tile() call
        # We don't reload immediately to avoid hitching

    def preload_common_tiles(self):
        """
        Preload commonly used sprites to avoid first-access hitching.

        This is called after game initialization in graphics mode to
        load essential sprites (player, common enemies, terrain).
        """
        if self.settings.graphics_mode != "graphics":
            return

        # List of entities to preload
        common_entities = [
            "player",
            "floor",
            "wall",
            # Add common enemies once we have the mappings defined
        ]

        logging.debug(f"Graphics: Preloading {len(common_entities)} common tiles")
        loaded_count = 0
        for entity_name in common_entities:
            if self.get_tile(entity_name):
                loaded_count += 1

        logging.debug(
            f"Graphics: Preloaded {loaded_count}/{len(common_entities)} common tiles successfully"
        )

    def cleanup(self):
        """Free all cached textures and reset state."""
        self.texture_cache.clear()
        self.last_window_size = None

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about tile manager state (for debugging).

        Returns:
            Dictionary with stats (cached_textures, mappings, etc.)
        """
        cached_count = sum(1 for texture in self.texture_cache.values() if texture is not None)

        return {
            "cached_textures": cached_count,
            "total_cache_entries": len(self.texture_cache),
            "mappings_loaded": len(self.tile_mappings),
            "tintable_flags": len(self.tintable_flags),
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
        }
