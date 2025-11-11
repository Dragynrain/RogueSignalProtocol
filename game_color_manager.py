#!/usr/bin/env python3
"""
Rogue Signal Protocol - Color Manager

Centralized color management with lazy loading from JSON configuration.
Provides ColorManager class with no fallback colors - fails fast on missing config.
Ensures all colors are loaded from game_rules.json for consistency.
"""

from typing import Tuple
from game_entities import ensure_color_tuple


class ColorManager:
    """Centralized color management with lazy loading.

    CRITICAL: No fallback colors! If a color is missing from config, raises KeyError.
    This ensures config errors are caught immediately rather than hidden.
    """
    _config = None
    _colors = None

    @classmethod
    def _ensure_loaded(cls):
        """Load colors from config once."""
        if cls._colors is None:
            from data_loading import DataLoader
            cls._config = DataLoader.load_config()

            # Fail fast if colors section missing
            if "colors" not in cls._config:
                raise KeyError("CRITICAL CONFIG ERROR: Missing 'colors' section in game_rules.json")

            cls._colors = cls._config["colors"]

    @classmethod
    def get(cls, category: str, key: str) -> Tuple[int, int, int]:
        """
        Get color from config. NO FALLBACKS - raises KeyError if missing.

        Args:
            category: Color category (e.g., "exploits", "graphics_tint", "enemy_states")
            key: Specific color key within category

        Returns:
            tuple: RGB color tuple (r, g, b)

        Raises:
            KeyError: If category or key not found in config (by design - no silent failures)
        """
        cls._ensure_loaded()

        if category not in cls._colors:
            raise KeyError(
                f"CRITICAL CONFIG ERROR: Missing color category '{category}' in game_rules.json. "
                f"Available categories: {list(cls._colors.keys())}"
            )

        category_colors = cls._colors[category]
        if key not in category_colors:
            raise KeyError(
                f"CRITICAL CONFIG ERROR: Missing color '{key}' in category '{category}'. "
                f"Available keys: {list(category_colors.keys())}"
            )

        return ensure_color_tuple(category_colors[key])

    @classmethod
    def get_exploit_color(cls, exploit_type: str) -> Tuple[int, int, int]:
        """Get exploit-specific color. Raises KeyError if not in config."""
        return cls.get("exploits", exploit_type)

    @classmethod
    def get_tint_color(cls, tint_type: str) -> Tuple[int, int, int]:
        """Get graphics tint color. Raises KeyError if not in config."""
        return cls.get("graphics_tint", tint_type)

    @classmethod
    def get_enemy_state_color(cls, state: str) -> Tuple[int, int, int]:
        """Get enemy state color. Raises KeyError if not in config."""
        return cls.get("enemies", state)

    @classmethod
    def get_terrain_variant_color(cls, variant: str) -> Tuple[int, int, int]:
        """Get terrain variant color. Raises KeyError if not in config."""
        return cls.get("terrain_variants", variant)

    @classmethod
    def get_targeting_color(cls, element: str) -> Tuple[int, int, int]:
        """Get targeting overlay color. Raises KeyError if not in config."""
        return cls.get("targeting", element)
