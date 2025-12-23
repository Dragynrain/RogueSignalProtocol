#!/usr/bin/env python3
"""
Core game entities and data structures.

Now streamlined with extracted modules:
- Enums extracted to game_entity_enums.py
- Position extracted to game_position.py
- ColorManager: JSON-driven color configuration (singleton)
- Enemy/Exploit/Upgrade definitions
- PositionValidator: Centralized position validation logic
"""

from dataclasses import dataclass

from data_loading import DataLoader

# Import extracted modules (and re-export for backward compatibility)
from game_entity_enums import EnemyMovement, EnemyState, TargetingMode
from game_position import Position, parse_coordinate_string

# Explicit exports (prevents ruff from removing "unused" imports)
__all__ = [
    # Re-exports from other modules
    "Position",
    "parse_coordinate_string",
    "EnemyState",
    "EnemyMovement",
    "TargetingMode",
    # Classes defined in this file
    "ColorManager",
    "ExploitDefinition",
    "EnemyTypeDefinition",
    "UpgradeDefinition",
    "PositionValidator",
    # Utility functions
    "clamp",
    "ensure_color_tuple",
]


class ColorManager:
    """
    JSON-driven color management for the game (singleton pattern).

    Loads all colors from game_config.json on first access and caches them.
    Ensures consistent color scheme across the entire game and fails fast
    if required colors are missing from configuration. No hardcoded fallbacks.

    The singleton pattern ensures only one instance loads the JSON once.
    """

    _instance = None
    _colors = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_colors()
        return cls._instance

    def _load_colors(self):
        """
        Load consolidated cyberspace color palette from JSON configuration.

        Loads all color categories and creates backward-compatible aliases
        for legacy color names (e.g., RED -> CRIMSON_RED, WHITE -> PURE_WHITE).

        Fails fast if colors section is missing.
        """
        import logging

        try:
            config = DataLoader.load_config()
            self._colors = {}

            # Load color effects settings
            color_effects = config["color_effects"]
            self._enemy_vision_alpha = color_effects["enemy_vision_alpha"]
            self._enemy_vision_darken = color_effects["enemy_vision_darken_factor"]
            logging.info(
                f"Loaded color effects: enemy_vision_alpha={self._enemy_vision_alpha}, enemy_vision_darken={self._enemy_vision_darken}"
            )

            # Ensure colors section exists
            if "colors" not in config:
                error_msg = "CRITICAL CONFIG ERROR: 'colors' section missing from game_rules.json"
                logging.error(error_msg)
                logging.error(f"Available sections: {list(config.keys())}")
                raise KeyError("Required 'colors' section missing from game_rules.json")

            color_config = config["colors"]

            # Load ALL color categories dynamically
            for category, items in color_config.items():
                if category.startswith("_"):  # Skip comment fields
                    continue
                if isinstance(items, dict):
                    for name, rgb in items.items():
                        if name.startswith("_"):  # Skip comment fields
                            continue
                        if isinstance(rgb, list) and len(rgb) == 3:
                            self._colors[name.upper()] = tuple(rgb)

            # Backward compatibility aliases (old name -> new name)
            self._create_aliases(
                {
                    # Basic colors
                    "WHITE": "PURE_WHITE",
                    "BLACK": "VOID_BLACK",
                    "RED": "CRIMSON_RED",
                    "GREEN": "MATRIX_GREEN",
                    "BLUE": "ELECTRIC_BLUE",
                    "YELLOW": "NEON_GOLD",
                    "MAGENTA": "HOT_MAGENTA",
                    "CYAN": "NEON_CYAN",
                    "LIGHT_GRAY": "STEEL_GRAY",
                    "DARK_GRAY": "SHADOW_GRAY",
                    "ORANGE": "SUNSET_ORANGE",
                    "BRIGHT_RED": "BLOOD_RED",
                    "BRIGHT_GREEN": "MATRIX_GREEN",
                    "BRIGHT_BLUE": "ELECTRIC_BLUE",
                    "BRIGHT_YELLOW": "NEON_GOLD",
                    "BRIGHT_MAGENTA": "HOT_MAGENTA",
                    "BRIGHT_CYAN": "NEON_CYAN",
                    "DARK_GREEN": "DEEP_GREEN",
                    # Game elements (consolidated)
                    "PLAYER": "MATRIX_GREEN",
                    "ENEMY": "CRIMSON_RED",
                    "BLIND_SPOT_VISIBLE": "GHOST_PURPLE",
                    "BLIND_SPOT_REMEMBERED": "VOID_PURPLE",
                    "FLOOR": "DIGITAL_FLOOR",
                    "GATEWAY": "NEON_GOLD",
                    "CPU_RECOVERY": "CRIMSON_RED",
                    "HEAT_RECOVERY": "NEON_CYAN",
                    "DATA_PATCH": "NEON_GOLD",
                    "EXPLOIT_PICKUP": "ALERT_AMBER",
                    "UPGRADE": "HOT_MAGENTA",
                    "STORY_FRAGMENT": "NEON_CYAN",
                    # Data codes (renamed)
                    "CRIMSON": "COMBAT_RED",
                    "AZURE": "ELECTRIC_BLUE",  # AZURE_BLUE removed, use ELECTRIC_BLUE
                    "AZURE_BLUE": "ELECTRIC_BLUE",  # Removed duplicate
                    "EMERALD": "EMERALD_GREEN",
                    "GOLDEN": "UTILITY_GOLD",
                    "VIOLET": "PLASMA_VIOLET",
                    "SILVER": "SILVER_MIST",
                    # Message log (consolidated)
                    "CRITICAL": "CRIMSON_RED",
                    "ERROR": "ALERT_AMBER",
                    "WARNING": "NEON_GOLD",
                    "ALERT": "ALERT_AMBER",
                    "SUCCESS": "MATRIX_GREEN",
                    "INFO": "NEON_CYAN",
                    "SYSTEM": "SYSTEM_PURPLE",
                    "COMBAT": "NEON_PINK",
                    "STEALTH": "STEALTH_BLUE",
                    "DEFAULT": "STEEL_GRAY",  # SILVER_WHITE removed, use STEEL_GRAY
                    "SILVER_WHITE": "STEEL_GRAY",  # Removed duplicate
                    # Enemy states
                    "ENEMY_UNAWARE": "UNAWARE",
                    "ENEMY_ALERT": "ALERT",
                    "ENEMY_HOSTILE": "HOSTILE",
                    "ENEMY_DISABLED": "DISABLED",
                    "UNAWARE_DARK": "UNAWARE",  # Removed _dark variants (created programmatically)
                    "ALERT_DARK": "ALERT",
                    "HOSTILE_DARK": "HOSTILE",
                    # Status effects (consolidated)
                    "VIRUS": "VIRUS",
                    "SLOW": "UNAWARE",  # Removed status_effects.slow, use enemies.unaware (same yellow)
                    "INVISIBLE": "INVISIBLE",
                    "DISABLED": "DISABLED",  # enemies.disabled still exists
                    # UI (consolidated)
                    "UI_BG": "UI_PANEL",  # from backgrounds
                    "UI_TEXT": "NEON_CYAN",
                    "UI_ACCENT": "DEEP_PURPLE",
                    "UI_HIGHLIGHT": "HOT_MAGENTA",
                    "ELECTRIC_PURPLE": "DEEP_PURPLE",
                    "HELP_TEXT": "SHADOW_GRAY",
                    "DIALOGUE_BACKGROUND": "UI_PANEL",  # backgrounds.dialogue removed, use UI_PANEL
                    "LOG_BG": "UI_PANEL",  # backgrounds.ui_panel_log removed, use UI_PANEL
                    # Removed dark UI backgrounds (consolidated)
                    "VOID": "VOID_BLACK",  # backgrounds.void removed, use basic.void_black
                    "DEEP_SPACE": "VOID_BLACK",  # backgrounds.deep_space removed, use VOID_BLACK
                    "UI_PANEL_LOG": "UI_PANEL",  # backgrounds.ui_panel_log removed, use UI_PANEL
                    "DIALOGUE": "UI_PANEL",  # backgrounds.dialogue removed, use UI_PANEL
                    "BLIND_SPOT": "VOID_PURPLE",  # game_elements.blind_spot removed, use VOID_PURPLE
                    # Removed terrain_variants duplicates
                    "FLOOR_TERRAIN": "DIGITAL_FLOOR",  # terrain_variants.floor removed, use game_elements.digital_floor
                    "BLIND_SPOT_TERRAIN": "VOID_PURPLE",  # terrain_variants.blind_spot removed, use game_elements.void_purple
                    # Removed achievement_popup duplicates
                    "ACHIEVEMENT_BACKGROUND": "POPUP",  # achievement_popup.background removed, use backgrounds.popup
                    "ACHIEVEMENT_NAME": "PURE_WHITE",  # achievement_popup.name removed, use basic.pure_white
                    "ACHIEVEMENT_BORDER": "NEON_GOLD",  # achievement_popup.border removed, use basic.neon_gold
                    "ACHIEVEMENT_TITLE": "NEON_GOLD",  # achievement_popup.title removed, use basic.neon_gold
                    # Removed graphics_tint duplicates
                    "NORMAL_TINT": "PURE_WHITE",  # graphics_tint.normal removed, use basic.pure_white
                    # Removed ui_themes duplicates
                    "THEME_CYAN": "NEON_CYAN",  # ui_themes.cyan removed, use basic.neon_cyan
                    "THEME_AZURE": "ELECTRIC_BLUE",  # ui_themes.azure removed, use basic.electric_blue
                    "THEME_EMERALD": "MATRIX_GREEN",  # ui_themes.emerald removed, use basic.matrix_green
                    "THEME_MAGENTA": "HOT_MAGENTA",  # ui_themes.magenta removed, use basic.hot_magenta
                }
            )

            # Load backgrounds into main color dict
            if "backgrounds" in color_config:
                for name, rgb in color_config["backgrounds"].items():
                    if not name.startswith("_") and isinstance(rgb, list):
                        self._colors[name.upper()] = tuple(rgb)

            # Derived colors for enemy vision ranges (darkened versions for glyph mode)
            if "UNAWARE" in self._colors:
                self._colors["VISION_UNAWARE"] = self._darken_color(
                    self._colors["UNAWARE"], self._enemy_vision_darken
                )
            if "ALERT" in self._colors:
                self._colors["VISION_ALERT"] = self._darken_color(
                    self._colors["ALERT"], self._enemy_vision_darken
                )
            if "HOSTILE" in self._colors:
                self._colors["VISION_HOSTILE"] = self._darken_color(
                    self._colors["HOSTILE"], self._enemy_vision_darken
                )

            # LOG_BORDER uses UI text color
            if "NEON_CYAN" in self._colors:
                self._colors["LOG_BORDER"] = self._colors["NEON_CYAN"]

        except KeyError:
            # Re-raise KeyError to fail immediately
            raise
        except Exception as e:
            error_msg = "CRITICAL CONFIG ERROR: Failed to load colors from game_rules.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise RuntimeError(f"Failed to load colors: {e}") from e

    def _create_aliases(self, alias_map: dict):
        """
        Create backward-compatible color aliases.

        Args:
            alias_map: Dict mapping old names to new names
        """
        for old_name, new_name in alias_map.items():
            if new_name in self._colors:
                self._colors[old_name] = self._colors[new_name]

    def _darken_color(self, color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        """
        Darken a color by multiplying each RGB component by the factor.

        Args:
            color: RGB tuple (0-255 for each component)
            factor: Darkening factor (0.0 = black, 1.0 = original color)

        Returns:
            Darkened RGB tuple
        """
        return tuple(int(c * factor) for c in color)

    def get_color(self, name: str) -> tuple[int, int, int]:
        """
        Get color by name (case-insensitive).

        Args:
            name: Color name (e.g., 'white', 'ENEMY_HOSTILE')

        Returns:
            RGB tuple

        Raises:
            KeyError: If color name not found in configuration
        """
        name_upper = name.upper()
        if name_upper not in self._colors:
            import logging

            logging.error(f"CRITICAL CONFIG ERROR: Color '{name}' not found in game configuration")
            logging.error(f"Available colors: {sorted(self._colors.keys())}")
            raise KeyError(
                f"Color '{name}' not found in configuration. Check game_rules.json colors section."
            )
        return self._colors[name_upper]

    @property
    def vision_alpha(self) -> float:
        """Get the alpha transparency value for enemy vision overlays (0.0-1.0)."""
        return self._enemy_vision_alpha

    @staticmethod
    def interpolate_color(
        color1: tuple[int, int, int], color2: tuple[int, int, int], factor: float
    ) -> tuple[int, int, int]:
        """
        Interpolate between two colors.

        Useful for creating smooth color transitions (e.g., heat meters, health bars).

        Args:
            color1: Starting RGB color
            color2: Ending RGB color
            factor: Interpolation factor (0.0 = color1, 1.0 = color2)

        Returns:
            Interpolated RGB tuple
        """
        factor = max(0.0, min(1.0, factor))
        r = int(color1[0] + (color2[0] - color1[0]) * factor)
        g = int(color1[1] + (color2[1] - color1[1]) * factor)
        b = int(color1[2] + (color2[2] - color1[2]) * factor)
        return (r, g, b)


class Colors:
    """
    Backward-compatible color access wrapper for ColorManager.

    Provides attribute-style access to colors (e.g., Colors.WHITE, Colors.ENEMY_HOSTILE).
    Delegates to the singleton ColorManager instance under the hood.
    """

    _manager = None

    def __init__(self):
        if Colors._manager is None:
            Colors._manager = ColorManager()

    def __getattr__(self, name: str):
        if Colors._manager is None:
            Colors._manager = ColorManager()
        return Colors._manager.get_color(name)

    @classmethod
    def get_color(cls, name: str) -> tuple[int, int, int]:
        """Get color by name."""
        if cls._manager is None:
            cls._manager = ColorManager()
        return cls._manager.get_color(name)

    @staticmethod
    def interpolate_color(
        color1: tuple[int, int, int], color2: tuple[int, int, int], factor: float
    ) -> tuple[int, int, int]:
        """Interpolate between two colors by the given factor (0.0 to 1.0)."""
        return ColorManager.interpolate_color(color1, color2, factor)


# Create a singleton instance for backward compatibility
Colors = Colors()

# Enums and Position are now imported from extracted modules
# (EnemyState, EnemyMovement, TargetingMode from game_entity_enums.py)
# (Position, parse_coordinate_string from game_position.py)


def ensure_color_tuple(color) -> tuple[int, int, int]:
    """Ensure color is a valid RGB tuple."""
    if isinstance(color, str):
        # Handle string color names - convert to Colors class attributes
        color_name = color.upper()
        if hasattr(Colors, color_name):
            return getattr(Colors, color_name)
        else:
            return Colors.WHITE
    elif isinstance(color, (list, tuple)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    else:
        return Colors.WHITE  # Default fallback


@dataclass
class EnemyTypeDefinition:
    """Definition of an enemy type with all its properties."""

    symbol: str
    cpu: int
    vision: int
    movement: str
    name: str
    damage: int
    description: str = ""


@dataclass
class ExploitDefinition:
    """Definition of an exploit with all its properties."""

    name: str
    ram: int
    heat: int
    range: int
    category: str
    damage: int
    targeting: str
    description: str = ""
    effect_duration: int = 0  # Duration in turns for effects (stun, invisibility, scan, etc.)
    effect_radius: int = 0  # Radius of effect for area exploits (0 for single-target/no effect)
    alert_duration_patrol: int = 0  # Alert duration for patrol enemies (decoy_swarm)
    alert_duration_normal: int = 0  # Alert duration for normal enemies (decoy_swarm)
    trace_reduction_percent: int = 0  # Trace reduction percentage (log_wiper)
    self_damage: int = 0  # Damage dealt to player when using exploit (system_crash)
    help_summary: str = ""  # Short help text shown in UI


@dataclass
class UpgradeDefinition:
    """Definition of an upgrade item."""

    name: str
    symbol: str
    color: tuple[int, int, int]
    stat_type: str
    bonus_amount: int
    description: str = ""  # Add missing description field


# Utility functions for position handling
def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max bounds.

    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Value constrained to [min_val, max_val]
    """
    return max(min_val, min(value, max_val))


class PositionValidator:
    """
    Centralized position validation utilities to avoid code duplication.

    Provides static methods for common validation patterns:
    - Boundary checks
    - Wall collision detection
    - Item/enemy placement validation
    - Movement validation

    All methods are static as they don't maintain state.
    """

    @staticmethod
    def is_within_bounds(position: Position, width: int, height: int) -> bool:
        """Check if position is within map bounds."""
        return 0 <= position.x < width and 0 <= position.y < height

    @staticmethod
    def is_basic_valid_position(position: Position, game_map) -> bool:
        """Basic position validation - within bounds and not a wall."""
        return PositionValidator.is_within_bounds(
            position, game_map.width, game_map.height
        ) and game_map.is_valid_position(position)

    @staticmethod
    def is_valid_for_placement(
        position: Position,
        game_map,
        min_distance_from_spawn: float = 5.0,
        check_existing_items: bool = False,
    ) -> bool:
        """Check if position is valid for item/node placement.

        Ensures items don't spawn on gateway or other critical locations.
        """
        from game_config import GameConfig

        # Boundary and wall check
        if not (
            0 < position.x < GameConfig.MAP_WIDTH - 1
            and 0 < position.y < GameConfig.MAP_HEIGHT - 1
            and game_map.is_valid_position(position)
        ):
            return False

        # Gateway check - never place items on gateway
        if (
            game_map.gateway
            and position.x == game_map.gateway.x
            and position.y == game_map.gateway.y
        ):
            return False

        # Spawn distance check
        dx, dy = position.x - 5, position.y - 5
        if dx * dx + dy * dy <= min_distance_from_spawn * min_distance_from_spawn:
            return False

        # Check existing items
        if check_existing_items:
            pos_tuple = (position.x, position.y)
            if any(
                pos_tuple in items
                for items in [
                    game_map.code_hacks,
                    game_map.cooling_nodes,
                    game_map.cpu_recovery_nodes,
                    game_map.ghost_nodes,
                    game_map.exploit_pickups,
                ]
            ):
                return False

        return True

    @staticmethod
    def is_valid_for_enemy_placement(
        position: Position,
        game_map,
        enemies_list,
        player_position: Position,
        check_existing_items: bool = True,
    ) -> bool:
        """Check if position is valid for enemy placement."""
        return (
            position != player_position
            and PositionValidator.is_valid_for_placement(
                position, game_map, 12.0, check_existing_items
            )
            and position not in {e.position for e in enemies_list}
        )

    @staticmethod
    def is_valid_for_enemy_movement(
        position: Position, game_map, enemies_list, player_position: Position, current_enemy
    ) -> bool:
        """Check if position is valid for enemy movement."""
        # Basic position validation
        if not PositionValidator.is_basic_valid_position(position, game_map):
            return False

        # Can't move to player position
        if position == player_position:
            return False

        # Can't move to a position occupied by another enemy
        for other_enemy in enemies_list:
            if other_enemy != current_enemy and other_enemy.position == position:
                return False

        return True

    @staticmethod
    def is_valid_for_patrol(position: Position, game_map, margin: int = 3) -> bool:
        """
        Check if position is valid for patrol point placement.

        Patrol points need extra margin from map edges to ensure the enemy
        can path around them safely without getting stuck at borders.

        Args:
            position: Position to validate
            game_map: GameMap for boundary and wall checking
            margin: Minimum distance from map edges (default 3 tiles)

        Returns:
            True if valid for patrol, False otherwise
        """
        from game_config import GameConfig

        # Check bounds with margin
        if not (
            margin <= position.x < GameConfig.MAP_WIDTH - margin
            and margin <= position.y < GameConfig.MAP_HEIGHT - margin
        ):
            return False

        # Must be walkable (not a wall)
        return game_map.is_valid_position(position) and not game_map.is_wall(position)
