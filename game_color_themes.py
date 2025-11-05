#!/usr/bin/env python3
"""
Rogue Signal Protocol - Color Themes Handler

Provides easy access to user-selectable UI color themes and color variations.
All colors sourced from game_rules.json - no hardcoded values.
"""

from typing import Tuple
from game_color_manager import ColorManager


class ColorThemes:
    """
    Handler for user-selectable UI color themes.

    Provides access to the ui_themes category in game_rules.json.
    """

    @staticmethod
    def get_theme_color(theme_name: str) -> Tuple[int, int, int]:
        """
        Get RGB color for a UI theme.

        Args:
            theme_name: Theme name (cyan, purple, magenta, golden, crimson, azure, emerald, ivory)

        Returns:
            RGB tuple for the theme color

        Raises:
            KeyError: If theme not found in config
        """
        return ColorManager.get("ui_themes", theme_name)

    @staticmethod
    def get_available_themes() -> list:
        """
        Get list of all available theme names.

        Returns:
            List of theme name strings
        """
        return ["cyan", "purple", "magenta", "golden", "crimson", "azure", "emerald", "ivory"]


class ColorPalette:
    """
    Helper for accessing background colors and creating color variations.
    """

    @staticmethod
    def get_background(bg_type: str) -> Tuple[int, int, int]:
        """
        Get a background color.

        Args:
            bg_type: Background type (void, deep_space, ui_panel, ui_panel_log, popup, dialogue, menu_highlight)

        Returns:
            RGB tuple for the background color

        Raises:
            KeyError: If background type not found
        """
        return ColorManager.get("backgrounds", bg_type)

    @staticmethod
    def darken(color: Tuple[int, int, int], factor: float = 0.5) -> Tuple[int, int, int]:
        """
        Darken a color by a given factor.

        Args:
            color: RGB tuple to darken
            factor: Darkening factor (0.0 = black, 1.0 = original color)

        Returns:
            Darkened RGB tuple
        """
        factor = max(0.0, min(1.0, factor))
        return tuple(int(c * factor) for c in color)

    @staticmethod
    def lighten(color: Tuple[int, int, int], factor: float = 0.5) -> Tuple[int, int, int]:
        """
        Lighten a color by a given factor.

        Args:
            color: RGB tuple to lighten
            factor: Lightening factor (0.0 = original, 1.0 = white)

        Returns:
            Lightened RGB tuple
        """
        factor = max(0.0, min(1.0, factor))
        return tuple(int(c + (255 - c) * factor) for c in color)

    @staticmethod
    def blend(color1: Tuple[int, int, int], color2: Tuple[int, int, int],
              ratio: float = 0.5) -> Tuple[int, int, int]:
        """
        Blend two colors together.

        Args:
            color1: First RGB tuple
            color2: Second RGB tuple
            ratio: Blend ratio (0.0 = all color1, 1.0 = all color2)

        Returns:
            Blended RGB tuple
        """
        ratio = max(0.0, min(1.0, ratio))
        return tuple(
            int(color1[i] * (1 - ratio) + color2[i] * ratio)
            for i in range(3)
        )
