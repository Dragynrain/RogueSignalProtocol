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

import tcod
import tcod.sdl
import logging
import os
import sys
import json
from typing import Dict, Optional, Tuple


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
        self.texture_cache: Dict[str, tcod.sdl.render.Texture] = {}

        # Tintable flags: entity_name (str) -> bool
        # True = white sprite, use color_mod tinting
        # False = colored sprite, use outline boxes for status
        self.tintable_flags: Dict[str, bool] = {}

        # Tile mapping: entity_name -> sprite filename
        self.tile_mappings: Dict[str, Dict] = {}

        # Calculated tile dimensions in pixels
        self.tile_width = 0
        self.tile_height = 0

        # Window resize tracking
        self.last_window_size: Optional[Tuple[int, int]] = None

        # Graphics directory path
        self.graphics_dir = self._get_graphics_dir()

        # Load tile mappings from JSON
        self._load_tile_mappings()

        # Calculate initial tile dimensions
        self._calculate_tile_dimensions()

        logging.info(f"TileManager initialized: tile_size={self.tile_width}x{self.tile_height}")

    def _get_graphics_dir(self) -> str:
        """Get absolute path to graphics directory."""
        if getattr(sys, 'frozen', False):
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

            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse mappings and tintable flags
            self.tile_mappings = data

            # Extract tintable flags for quick lookup
            self._extract_tintable_flags(data)

            logging.info(f"Loaded {len(self.tile_mappings)} tile mapping categories")

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse {mapping_file}: {e}")
            logging.error("Graphics mode will use glyph fallbacks")
        except Exception as e:
            logging.error(f"Error loading tile mappings: {e}")
            logging.error("Graphics mode will use glyph fallbacks")

    def _extract_tintable_flags(self, data: Dict):
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

        In graphics mode, tiles are calculated based on the smaller viewport size,
        making each sprite appear larger (2x scale factor).
        """
        try:
            from game_config import GameConfig

            # Get window pixel dimensions
            window_size = self._get_window_size()
            window_width, window_height = window_size

            # Get console grid dimensions (full console for UI)
            console_width = GameConfig.SCREEN_WIDTH
            console_height = GameConfig.SCREEN_HEIGHT

            # Calculate base tile size for UI rendering
            base_tile_width = window_width // console_width
            base_tile_height = window_height // console_height

            # In graphics mode, use viewport dimensions to calculate larger sprite tiles
            if self.settings.graphics_mode == "graphics":
                # Get viewport dimensions (half of game area)
                viewport_width = GameConfig.VIEWPORT_WIDTH("graphics")
                viewport_height = GameConfig.VIEWPORT_HEIGHT("graphics")

                # Calculate game area pixel dimensions
                game_area_width = GameConfig.GAME_AREA_WIDTH()
                viewable_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1

                # Calculate sprite tile size to fill game area with smaller viewport
                self.tile_width = (base_tile_width * game_area_width) // viewport_width
                self.tile_height = (base_tile_height * viewable_height) // viewport_height
            else:
                # Glyph mode: tiles match console grid
                self.tile_width = base_tile_width
                self.tile_height = base_tile_height

            # Ensure minimum tile size (readability threshold)
            if self.tile_width < 8:
                self.tile_width = 8
                logging.warning(f"Tile width clamped to minimum: {self.tile_width}px")
            if self.tile_height < 8:
                self.tile_height = 8
                logging.warning(f"Tile height clamped to minimum: {self.tile_height}px")

            logging.debug(f"Tile dimensions calculated: {self.tile_width}x{self.tile_height} "
                         f"(window={window_width}x{window_height}, "
                         f"mode={self.settings.graphics_mode})")

        except Exception as e:
            logging.error(f"Failed to calculate tile dimensions: {e}")
            # Fallback to reasonable defaults
            self.tile_width = 10
            self.tile_height = 16
            logging.warning(f"Using fallback tile dimensions: {self.tile_width}x{self.tile_height}")

    def _get_window_size(self) -> Tuple[int, int]:
        """
        Get current window pixel dimensions from SDL.

        Returns:
            Tuple of (width, height) in pixels
        """
        if hasattr(self.context, 'sdl_window') and self.context.sdl_window:
            return self.context.sdl_window.size

        # Fallback to reasonable default
        logging.warning("Could not get window size from context, using default 800x600")
        return (800, 600)

    def load_tile(self, entity_name: str) -> Optional[tcod.sdl.render.Texture]:
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
            from PIL import Image
            import numpy as np

            # Load image preserving alpha channel
            pil_image = Image.open(filepath)

            # Convert to RGBA if not already (ensure alpha channel exists)
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Scale to calculated tile size (512x512 -> tile_width x tile_height)
            pil_image = pil_image.resize(
                (self.tile_width, self.tile_height),
                Image.Resampling.LANCZOS  # High-quality downscaling
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

            logging.debug(f"Loaded sprite: {entity_name} from {sprite_file}")
            return texture

        except Exception as e:
            logging.warning(f"Failed to load sprite {filepath}: {e}")
            return None

    def _get_sprite_filename(self, entity_name: str) -> Optional[str]:
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
                if isinstance(category_data, dict) and entity_name in category_data:
                    entity_data = category_data[entity_name]
                    if isinstance(entity_data, dict) and "file" in entity_data:
                        return entity_data["file"]

        return None

    def get_tile(self, entity_name: str) -> Optional[tcod.sdl.render.Texture]:
        """
        Get tile texture for an entity (cached or load on-demand).

        Uses lazy loading: sprites are loaded on first access and cached.

        Args:
            entity_name: Name of entity

        Returns:
            SDL texture if available, None if no sprite or load failed
        """
        # Check cache first
        if entity_name in self.texture_cache:
            return self.texture_cache[entity_name]

        # Not in cache - try to load
        texture = self.load_tile(entity_name)

        # Cache result (even if None, to avoid repeated load attempts)
        self.texture_cache[entity_name] = texture

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
            logging.info(f"Window resized: {self.last_window_size} -> {current_size}")
            self._reload_all_textures(current_size)
            self.last_window_size = current_size
            return True

        return False

    def _reload_all_textures(self, new_window_size: Tuple[int, int]):
        """
        Recalculate tile size and reload all cached textures.

        Args:
            new_window_size: New window dimensions (width, height) in pixels
        """
        # Recalculate tile dimensions
        self._calculate_tile_dimensions()

        # Get list of entities that were loaded
        loaded_entities = [name for name, texture in self.texture_cache.items()
                          if texture is not None]

        # Clear cache (textures will be garbage collected)
        self.texture_cache.clear()

        # Lazy reload - textures will reload on next get_tile() call
        # We don't reload immediately to avoid hitching

        logging.info(f"Prepared {len(loaded_entities)} textures for reload at "
                    f"new size: {self.tile_width}x{self.tile_height}")

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

        logging.info("Preloading common tiles...")
        preloaded = 0

        for entity_name in common_entities:
            texture = self.get_tile(entity_name)
            if texture is not None:
                preloaded += 1

        logging.info(f"Preloaded {preloaded}/{len(common_entities)} common tiles")

    def cleanup(self):
        """Free all cached textures and reset state."""
        self.texture_cache.clear()
        self.last_window_size = None
        logging.info("TileManager cleanup complete")

    def get_stats(self) -> Dict[str, int]:
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
