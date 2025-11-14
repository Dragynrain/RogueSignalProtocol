#!/usr/bin/env python3
"""
Game Configuration and Settings Management

Contains:
- GameSettings: User preferences (audio, graphics mode, dialogue preferences)
- GameConfig: Core game constants (map size, FOV, balance values)
- GameBalance: Balance values loaded from JSON
- RoomGenerationConfig: Procedural generation parameters

GameSettings persists to user_settings.json (can use defaults if missing).
GameConfig and GameBalance load from game_rules.json (fail-fast if missing).
"""

import json
import logging
import os
from typing import Any

from data_loading import DataLoader


class GameSettings:
    """
    Manages user preferences with persistent storage.

    Settings are saved to user_settings.json and loaded on startup.
    If the file is missing or corrupted, creates a new one with defaults.
    This is the ONLY configuration file that can be missing without error.

    Settings include:
    - Audio volumes (master, SFX, music)
    - Graphics mode (glyph vs graphics sprites)
    - Dialogue preferences (which dialogues to show/hide)
    """

    SETTINGS_FILE = "saves/user_settings.json"

    # Single source of truth for default settings
    DEFAULTS = {
        "master_volume": 0.7,
        "sfx_volume": 0.75,
        "music_volume": 0.6,
        "graphics_mode": "graphics",  # "glyph" (CP437 characters) or "graphics" (PNG sprites)
        "show_achievement_popups": True,  # Show achievement unlock popups
        "show_particle_effects": True,  # Show particle effects (explosions) in graphics mode
        "ui_color": "cyan",  # UI theme color for borders/headers (cyan, purple, magenta, golden, crimson, azure, emerald)
        "dialogue_preferences": {},  # Stores user preferences for dialogue visibility
        "custom_keyboard_bindings": {},  # Custom key bindings for remapping (Phase 1: Gamepad Support)
        "custom_gamepad_bindings": {},  # Custom gamepad button bindings
        "gamepad_deadzone": 0.15,  # Analog stick deadzone (15% default)
        "gamepad_enabled": True,  # Enable/disable gamepad input
    }

    def __init__(self):
        # Initialize all settings from DEFAULTS dictionary
        self._apply_settings_from_dict(self.DEFAULTS)
        self.load_settings()

    def _apply_settings_from_dict(self, settings_dict: dict) -> None:
        """
        Apply settings from a dictionary to instance attributes.

        Handles deep copying for mutable defaults (dicts) to prevent
        shared reference issues.

        Args:
            settings_dict: Dictionary containing setting key-value pairs
        """
        for key, default_value in self.DEFAULTS.items():
            value = settings_dict.get(key, default_value)

            # Deep copy mutable types to avoid shared references
            if isinstance(value, dict):
                setattr(self, key, value.copy())
            else:
                setattr(self, key, value)

    def _get_settings_as_dict(self) -> dict:
        """
        Get current settings as a dictionary for saving.

        Returns:
            Dictionary mapping setting names to current values
        """
        return {key: getattr(self, key) for key in self.DEFAULTS.keys()}

    def load_settings(self) -> None:
        """
        Load settings from user_settings.json.

        Handles:
        - Missing file (uses in-memory defaults, doesn't create file)
        - Empty/corrupted file (recreates default)
        - Migration from old setting names (e.g., "ascii" -> "glyph")

        Never crashes - always falls back to defaults if needed.
        File is only created when user changes a setting (via save_settings()).
        """
        try:
            if os.path.exists(self.SETTINGS_FILE):
                # Read file content first to check for corruption
                try:
                    with open(self.SETTINGS_FILE) as f:
                        content = f.read().strip()
                except (PermissionError, OSError) as e:
                    logging.error(f"Cannot read settings file: {e}")
                    self._create_default_settings_file()
                    return

                # Check if file is empty or contains only whitespace
                if not content:
                    logging.warning("Settings file is empty, using defaults")
                    self._create_default_settings_file()
                    return

                # Try to parse JSON
                try:
                    settings_data = json.loads(content)
                except json.JSONDecodeError as e:
                    logging.warning(
                        f"Settings file corrupted (JSON decode error: {e}), recreating with defaults"
                    )
                    self._create_default_settings_file()
                    return

                # Load settings with defaults from single source of truth
                self._apply_settings_from_dict(settings_data)

                # Migrate old "ascii" setting to "glyph"
                if self.graphics_mode == "ascii":
                    self.graphics_mode = "glyph"
                    try:
                        self.save_settings()
                        logging.info("Migrated graphics_mode from 'ascii' to 'glyph'")
                    except (PermissionError, OSError) as e:
                        logging.error(f"Failed to save migrated settings: {e}")
                        # Game can still run, just won't persist migration

                logging.debug(
                    f"Settings: Loaded from {self.SETTINGS_FILE} - graphics={self.graphics_mode}, master_vol={self.master_volume:.2f}, dialogues={len(self.dialogue_preferences)}"
                )
        except (PermissionError, OSError) as e:
            logging.error(f"File I/O error loading settings: {e}")
            self._create_default_settings_file()

    def _create_default_settings_file(self) -> None:
        """Create a default settings file."""
        try:
            # Use DEFAULTS as single source of truth
            default_settings = self.DEFAULTS.copy()
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(default_settings, f, indent=2)
            logging.info("Created default settings file")
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to create default settings file: {e}")
            # Game will use in-memory defaults

    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = self._get_settings_as_dict()
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(settings_data, f, indent=2)
            logging.debug(f"Settings: Saved to {self.SETTINGS_FILE}")
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to save settings: {e}")
            # Settings won't persist, but game continues with current values

    def _set_volume_attribute(self, volume_type: str, volume: float):
        """Generic volume setter for any volume type."""
        from game_entities import clamp

        old_value = getattr(self, f"{volume_type}_volume", 0.0)
        new_value = clamp(volume, 0.0, 1.0)
        setattr(self, f"{volume_type}_volume", new_value)
        logging.debug(f"Settings: {volume_type}_volume changed {old_value:.2f} -> {new_value:.2f}")
        self.save_settings()

    def set_master_volume(self, volume: float):
        self._set_volume_attribute("master", volume)

    def set_sfx_volume(self, volume: float):
        self._set_volume_attribute("sfx", volume)

    def set_music_volume(self, volume: float):
        self._set_volume_attribute("music", volume)

    def set_graphics_mode(self, mode: str):
        """Set graphics mode ('glyph' for CP437 characters or 'graphics' for PNG sprites)"""
        if mode in ["glyph", "graphics", "ascii"]:  # Accept "ascii" for backwards compatibility
            # Migrate "ascii" to "glyph" if provided
            if mode == "ascii":
                mode = "glyph"
                logging.info("Migrated graphics_mode from 'ascii' to 'glyph'")
            old_mode = self.graphics_mode
            self.graphics_mode = mode
            logging.debug(f"Settings: graphics_mode changed {old_mode} -> {mode}")
            self.save_settings()

    def set_ui_color(self, color: str):
        """Set UI theme color for borders/headers."""
        valid_colors = [
            "cyan",
            "purple",
            "magenta",
            "golden",
            "crimson",
            "azure",
            "emerald",
            "ivory",
        ]
        if color in valid_colors:
            old_color = self.ui_color
            self.ui_color = color
            logging.debug(f"Settings: ui_color changed {old_color} -> {color}")
            self.save_settings()

    def get_ui_color_rgb(self) -> tuple:
        """Get RGB values for current UI color from ui_themes in game_rules.json."""
        from game_color_manager import ColorManager

        try:
            return ColorManager.get("ui_themes", self.ui_color)
        except KeyError:
            # Fallback to neon_cyan if theme not found
            return ColorManager.get("basic", "neon_cyan")

    def get_volume_percent(self, volume_type: str) -> int:
        """Get volume as percentage (0-100)"""
        volume_map = {
            "master": self.master_volume,
            "sfx": self.sfx_volume,
            "music": self.music_volume,
        }
        return int(volume_map.get(volume_type, 0) * 100)

    def set_volume_percent(self, volume_type: str, percent: int):
        """Set volume from percentage (0-100)"""
        setter_map = {
            "master": self.set_master_volume,
            "sfx": self.set_sfx_volume,
            "music": self.set_music_volume,
        }
        if volume_type in setter_map:
            setter_map[volume_type](percent / 100.0)

    @property
    def audio_enabled(self) -> bool:
        """Check if audio is enabled (master volume > 0)."""
        return self.master_volume > 0

    @property
    def music_enabled(self) -> bool:
        """Check if music is enabled (music volume > 0 and master volume > 0)."""
        return self.music_volume > 0 and self.master_volume > 0


class GameConfig:
    """Game configuration constants and settings."""

    _config_data = None

    # Initialize class attributes with defaults first
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 50
    MAP_HEIGHT = 50
    UI_HEIGHT = 10
    SIDEBAR_WIDTH = 25
    LOG_WIDTH = 25
    INFO_PANEL_HEIGHT = 11
    PANEL_HEIGHT = 5
    DEFAULT_PLAYER_RAM = 8
    DEFAULT_PLAYER_CPU = 100
    MAX_HEAT = 100
    MAX_TRACE_LEVEL = 100
    DETECTION_REDUCTION_ON_LEVEL = 50
    DUNGEON_SEED_RANGE = 1000000
    DEFAULT_VISION_RANGE = 10
    MAX_SAVE_ATTEMPTS = 3
    NEARBY_ENEMY_ALERT_RADIUS = 8
    VIRUS_DAMAGE_PER_TURN = 3
    # Level generation layout constants
    EDGE_ROOM_BUFFER = 15  # Minimum distance from map edge for room placement
    LANDMARK_CORNER_OFFSET = 10  # Offset from corner for landmark placement
    LANDMARK_CORNER_SIZE_ADJUST = 20  # Size adjustment for landmark corner calculation
    ARENA_EDGE_BUFFER = 15  # Minimum distance from map edge for arena placement
    ENEMY_PLACEMENT_ATTEMPTS_MULTIPLIER = 25  # Max placement attempts = enemy_count * this value
    DEFAULT_FADE_TIME = 2000
    MESSAGE_CENTER_OFFSET_LARGE = 15
    MESSAGE_CENTER_OFFSET_MEDIUM = 12
    MESSAGE_CENTER_OFFSET_SMALL = 8
    MESSAGE_CENTER_OFFSET_TINY = 10
    MESSAGE_LINE_SPACING = 1
    MESSAGE_BUTTON_SPACING = 3

    @classmethod
    def load_from_json(cls):
        """Load configuration from JSON file - FAILS if required values missing."""
        try:
            with open("game_rules.json", encoding="utf-8") as f:
                cls._config_data = json.load(f)

            # Update class attributes - NO FALLBACKS, fail if missing
            cls.SCREEN_WIDTH = cls._get_required("display.screen_width")
            cls.SCREEN_HEIGHT = cls._get_required("display.screen_height")
            cls.MAP_WIDTH = cls._get_required("display.map_width")
            cls.MAP_HEIGHT = cls._get_required("display.map_height")
            cls.UI_HEIGHT = cls._get_required("display.ui_height")
            cls.SIDEBAR_WIDTH = cls._get_required("display.sidebar_width")
            cls.LOG_WIDTH = cls._get_required("display.log_width")
            cls.PANEL_HEIGHT = cls._get_required("display.panel_height")
            cls.DEFAULT_PLAYER_RAM = cls._get_required("gameplay.default_player_ram")
            cls.DEFAULT_PLAYER_CPU = cls._get_required("gameplay.default_player_cpu")
            cls.MAX_HEAT = cls._get_required("gameplay.max_heat")
            cls.MAX_TRACE_LEVEL = cls._get_required("gameplay.max_trace_level")
            cls.DETECTION_REDUCTION_ON_LEVEL = cls._get_required(
                "gameplay.trace_reduction_on_level"
            )
            cls.DUNGEON_SEED_RANGE = cls._get_required("gameplay.dungeon_seed_range")
            cls.DEFAULT_VISION_RANGE = cls._get_required("gameplay.default_vision_range")
            cls.MAX_SAVE_ATTEMPTS = cls._get_required("gameplay.max_save_attempts")
            cls.NEARBY_ENEMY_ALERT_RADIUS = cls._get_required("gameplay.nearby_enemy_alert_radius")
            cls.VIRUS_DAMAGE_PER_TURN = cls._get_required("gameplay.virus_damage_per_turn")
            cls.DEFAULT_FADE_TIME = cls._get_required("audio.default_fade_time")
            cls.MESSAGE_CENTER_OFFSET_LARGE = cls._get_required("ui.message_center_offset_large")
            cls.MESSAGE_CENTER_OFFSET_MEDIUM = cls._get_required("ui.message_center_offset_medium")
            cls.MESSAGE_CENTER_OFFSET_SMALL = cls._get_required("ui.message_center_offset_small")
            cls.MESSAGE_CENTER_OFFSET_TINY = cls._get_required("ui.message_center_offset_tiny")
            cls.MESSAGE_LINE_SPACING = cls._get_required("ui.message_line_spacing")
            cls.MESSAGE_BUTTON_SPACING = cls._get_required("ui.message_button_spacing")

        except FileNotFoundError as e:
            error_msg = "CRITICAL CONFIG ERROR: game_rules.json not found"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise FileNotFoundError("Required file game_rules.json is missing") from e
        except json.JSONDecodeError as e:
            error_msg = "CRITICAL CONFIG ERROR: Invalid JSON in game_rules.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            raise json.JSONDecodeError(
                "game_rules.json contains invalid JSON", e.doc, e.pos
            ) from e
        except KeyError as e:
            error_msg = "CRITICAL CONFIG ERROR: Missing required config value in game_rules.json"
            logging.error(error_msg)
            logging.error(f"Exception: {str(e)}")
            if cls._config_data:
                logging.error(f"Available top-level sections: {list(cls._config_data.keys())}")
            raise KeyError(f"Required configuration value missing from game_rules.json: {e}") from e

    @classmethod
    def _ensure_loaded(cls):
        """Ensure config data is loaded."""
        if cls._config_data is None:
            cls.load_from_json()

    # Calculated layout properties
    @classmethod
    def GAME_AREA_WIDTH(cls):
        """Calculate game area width (screen width minus log width)."""
        cls._ensure_loaded()
        return cls.SCREEN_WIDTH - cls.LOG_WIDTH

    @classmethod
    def PANEL_Y(cls):
        """Calculate panel Y position (screen height minus panel height)."""
        cls._ensure_loaded()
        return cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT

    @classmethod
    def LOG_START_Y(cls):
        """Calculate system log start Y position (after info panel header)."""
        cls._ensure_loaded()
        return cls.INFO_PANEL_HEIGHT

    @classmethod
    def VIEWPORT_WIDTH(
        cls, graphics_mode: str = "glyph", tile_width: int = None, window_width: int = None
    ):
        """
        Calculate viewport width (visible tiles) based on rendering mode.

        In glyph mode: Returns console character count (55 chars)
        In graphics mode: Returns number of pixel-tiles that fit in game area
            - Requires tile_width and window_width for accurate calculation
            - Falls back to console width if parameters not provided

        Args:
            graphics_mode: "graphics" or "glyph"
            tile_width: Width of one tile in pixels
            window_width: Actual window width in pixels (dynamic, resolution-dependent)

        Returns:
            Number of tiles visible horizontally
        """
        cls._ensure_loaded()
        game_area_width_chars = cls.SCREEN_WIDTH - cls.LOG_WIDTH

        if graphics_mode == "glyph" or tile_width is None or window_width is None:
            # Glyph mode or missing info: return console character count
            return game_area_width_chars
        else:
            # Graphics mode: calculate how many pixel-tiles fit in the game area
            # Game area is 55/80 of the total window width
            game_area_pixel_width = int(window_width * (game_area_width_chars / cls.SCREEN_WIDTH))
            return game_area_pixel_width // tile_width

    @classmethod
    def VIEWPORT_HEIGHT(
        cls, graphics_mode: str = "glyph", tile_height: int = None, window_height: int = None
    ):
        """
        Calculate viewport height (visible tiles) based on rendering mode.

        In glyph mode: Returns console character count (44 chars)
        In graphics mode: Returns number of pixel-tiles that fit in game area
            - Requires tile_height and window_height for accurate calculation
            - Falls back to console height if parameters not provided

        Args:
            graphics_mode: "graphics" or "glyph"
            tile_height: Height of one tile in pixels
            window_height: Actual window height in pixels (dynamic, resolution-dependent)

        Returns:
            Number of tiles visible vertically (excluding top status bar and panel)
        """
        cls._ensure_loaded()
        viewable_height_chars = cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT - 1

        if graphics_mode == "glyph" or tile_height is None or window_height is None:
            # Glyph mode or missing info: return console character count
            return viewable_height_chars
        else:
            # Graphics mode: calculate how many pixel-tiles fit in the game area
            # Game area height excludes panel and status bar
            game_area_pixel_height = int(
                window_height * (viewable_height_chars / cls.SCREEN_HEIGHT)
            )
            return game_area_pixel_height // tile_height

    @classmethod
    def STATUS_BAR_HEIGHT(cls):
        """Get status bar height from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.status_bar_height")

    @classmethod
    def VISION_BRACKET_SIZE(cls):
        """Get vision bracket size from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.vision_bracket_size")

    @classmethod
    def STATUS_OUTLINE_THICKNESS(cls):
        """Get status outline thickness from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.status_outline_thickness")

    @classmethod
    def ENEMY_OUTLINE_THICKNESS(cls):
        """Get enemy outline thickness from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.enemy_outline_thickness")

    @classmethod
    def MIN_TILE_WIDTH(cls):
        """Get minimum tile width from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.min_tile_width")

    @classmethod
    def MIN_TILE_HEIGHT(cls):
        """Get minimum tile height from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.min_tile_height")

    @classmethod
    def FALLBACK_TILE_WIDTH(cls):
        """Get fallback tile width from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.fallback_tile_width")

    @classmethod
    def FALLBACK_TILE_HEIGHT(cls):
        """Get fallback tile height from config."""
        cls._ensure_loaded()
        return cls._get_required("rendering.fallback_tile_height")

    # Particle system configuration
    @classmethod
    def PARTICLE_GRAVITY(cls):
        """Get particle gravity from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.gravity")

    @classmethod
    def PARTICLE_COUNT_DEFAULT(cls):
        """Get default particle count from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.default_particle_count")

    @classmethod
    def PARTICLE_VELOCITY_MIN(cls):
        """Get minimum particle velocity from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.velocity_min")

    @classmethod
    def PARTICLE_VELOCITY_MAX(cls):
        """Get maximum particle velocity from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.velocity_max")

    @classmethod
    def PARTICLE_UPWARD_BIAS(cls):
        """Get particle upward bias from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.upward_bias")

    @classmethod
    def PARTICLE_SIZE_MIN(cls):
        """Get minimum particle size from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.size_min")

    @classmethod
    def PARTICLE_SIZE_MAX(cls):
        """Get maximum particle size from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.size_max")

    @classmethod
    def PARTICLE_LIFETIME_MIN(cls):
        """Get minimum particle lifetime from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.lifetime_min")

    @classmethod
    def PARTICLE_LIFETIME_MAX(cls):
        """Get maximum particle lifetime from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.lifetime_max")

    @classmethod
    def PARTICLE_COLOR_VARIATION(cls):
        """Get particle color variation from config."""
        cls._ensure_loaded()
        return cls._get_required("particles.color_variation")

    @classmethod
    def PARTICLE_SPRITE_COLOR_COUNT(cls):
        """Get number of colors to extract from sprite for particles."""
        cls._ensure_loaded()
        return cls._get_required("particles.sprite_color_count")

    @classmethod
    def _get_required(cls, key: str):
        """Get required configuration value - raises KeyError if missing."""
        if cls._config_data is None:
            raise RuntimeError("Config data not loaded - call load_from_json first")

        keys = key.split(".")
        value = cls._config_data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError) as e:
            error_msg = f"CRITICAL CONFIG ERROR: Required key '{key}' not found in game_rules.json"
            logging.error(error_msg)

            # Provide helpful debug info
            partial_keys = []
            partial_value = cls._config_data
            for k in keys:
                partial_keys.append(k)
                try:
                    partial_value = partial_value[k]
                except (KeyError, TypeError):
                    break

            if partial_keys:
                path_str = ".".join(partial_keys[:-1]) if len(partial_keys) > 1 else "root"
                if isinstance(partial_value, dict):
                    logging.error(f"Available keys at '{path_str}': {list(partial_value.keys())}")
                else:
                    logging.error(
                        f"Value at '{path_str}' is {type(partial_value).__name__}, not a dict"
                    )

            raise KeyError(f"Required config key missing: {key}") from e

    @classmethod
    def get(cls, key: str, default=None):
        """Get configuration value by key with optional default (use sparingly)."""
        if cls._config_data is None:
            cls.load_from_json()

        if cls._config_data:
            keys = key.split(".")
            value = cls._config_data
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                pass

        return default

    @classmethod
    def get_network_configs(cls) -> dict[int, dict[str, Any]]:
        """Get network configurations from game data."""
        game_data = DataLoader.load_game_data()
        configs = game_data["network_configs"]
        return {int(k): v for k, v in configs.items()}

    @classmethod
    def NETWORK_CONFIGS(cls) -> dict[int, dict[str, Any]]:
        """Get network configurations from game data."""
        return cls.get_network_configs()


class RoomGenerationConfig:
    """Configuration for procedural room generation."""

    # Set class attributes with defaults
    MIN_ROOMS_BASE = 12
    ROOM_LEVEL_MULTIPLIER = 3
    MAX_ROOMS = 20
    MAX_PLACEMENT_ATTEMPTS = 400
    MIN_ROOM_SIZE = 3
    MAX_ROOM_SIZE = 8
    ROOM_PADDING = 1

    # NOTE: Special node counts (cooling_nodes, cpu_nodes, ghost_nodes, code_hacks,
    # exploit_pickups, permanent_upgrades) are defined per-level in game_content.json
    # network_configs, NOT here. Those values vary by level (1, 2, 3).

    @classmethod
    def load_from_json(cls):
        """Load room generation config from JSON - NO FALLBACKS."""
        cls.MIN_ROOMS_BASE = GameConfig._get_required("room_generation.min_rooms_base")
        cls.ROOM_LEVEL_MULTIPLIER = GameConfig._get_required(
            "room_generation.room_level_multiplier"
        )
        cls.MAX_ROOMS = GameConfig._get_required("room_generation.max_rooms")
        cls.MAX_PLACEMENT_ATTEMPTS = GameConfig._get_required(
            "room_generation.max_placement_attempts"
        )
        cls.MIN_ROOM_SIZE = GameConfig._get_required("room_generation.min_room_size")
        cls.MAX_ROOM_SIZE = GameConfig._get_required("room_generation.max_room_size")
        cls.ROOM_PADDING = GameConfig._get_required("room_generation.room_padding")

        # NOTE: Node/item counts removed - use game_content.json network_configs instead
        # (values vary per level, not a single "per_level" value)

    def __init__(self):
        self.min_room_size = self.MIN_ROOM_SIZE
        self.max_room_size = self.MAX_ROOM_SIZE
        self.max_rooms = self.MAX_ROOMS
        self.room_attempts = self.MAX_PLACEMENT_ATTEMPTS


class GameBalance:
    """Game balance configuration."""

    # Set class attributes with defaults
    HEAT_REDUCTION_NORMAL = 2
    HEAT_REDUCTION_BOOSTED = 3
    TRACE_INCREASE_INTERVAL = 25
    TRACE_INCREASE_AMOUNT = 1
    COOLING_NODE_EFFECT = 20
    GHOST_NODE_DETECTION_REDUCTION_PERCENT = 20.0
    CPU_RECOVERY_AMOUNT = 20
    ENEMY_ELIMINATION_CPU_REWARD = 5
    CPU_RESTORE_MIN = 30
    CPU_RESTORE_MAX = 40
    HEAT_REDUCTION_INSTANT = 40
    ADJACENT_DISTANCE_THRESHOLD = 1.5
    PATROL_STUCK_THRESHOLD = 3
    PATHFINDING_TIMEOUT_ATTEMPTS = 100
    ENHANCED_VISION_BONUS = 2
    BLIND_SPOT_VISION_REDUCTION_FACTOR = 3
    ENEMY_TRACE_ALERT_TO_HOSTILE = 3
    ENEMY_TRACE_CONTINUOUS_HOSTILE = 0.3
    ENEMY_MEMORY_TURNS = 20
    OVERHEAT_COOLDOWN_AMOUNT = 15  # Heat reduction on overheat
    OVERHEAT_MINIMUM_HEAT = 85  # Minimum heat level after overheat cooldown

    @classmethod
    def load_from_json(cls):
        """Load balance config from JSON - NO FALLBACKS."""
        cls.HEAT_REDUCTION_NORMAL = GameConfig._get_required("balance.heat_reduction_normal")
        cls.HEAT_REDUCTION_BOOSTED = GameConfig._get_required("balance.heat_reduction_boosted")
        cls.TRACE_INCREASE_INTERVAL = GameConfig._get_required("balance.trace_increase_interval")
        cls.TRACE_INCREASE_AMOUNT = GameConfig._get_required("balance.trace_increase_amount")
        cls.COOLING_NODE_EFFECT = GameConfig._get_required("balance.cooling_node_effect")
        cls.GHOST_NODE_DETECTION_REDUCTION_PERCENT = GameConfig._get_required(
            "balance.ghost_node_trace_reduction_percent"
        )
        cls.CPU_RECOVERY_AMOUNT = GameConfig._get_required("balance.cpu_recovery_amount")
        cls.ENEMY_ELIMINATION_CPU_REWARD = GameConfig._get_required(
            "balance.enemy_elimination_cpu_reward"
        )
        cls.CPU_RESTORE_MIN = GameConfig._get_required("balance.cpu_restore_min")
        cls.CPU_RESTORE_MAX = GameConfig._get_required("balance.cpu_restore_max")
        cls.HEAT_REDUCTION_INSTANT = GameConfig._get_required("balance.heat_reduction_instant")
        cls.ADJACENT_DISTANCE_THRESHOLD = GameConfig._get_required(
            "balance.adjacent_distance_threshold"
        )
        cls.PATROL_STUCK_THRESHOLD = GameConfig._get_required("balance.patrol_stuck_threshold")
        cls.PATHFINDING_TIMEOUT_ATTEMPTS = GameConfig._get_required(
            "balance.pathfinding_timeout_attempts"
        )
        cls.ENHANCED_VISION_BONUS = GameConfig._get_required("balance.enhanced_vision_bonus")
        cls.BLIND_SPOT_VISION_REDUCTION_FACTOR = GameConfig._get_required(
            "balance.blind_spot_vision_reduction_factor"
        )
        cls.ENEMY_TRACE_ALERT_TO_HOSTILE = GameConfig._get_required(
            "balance.ai_behavior.enemy_trace_alert_to_hostile"
        )
        cls.ENEMY_TRACE_CONTINUOUS_HOSTILE = GameConfig._get_required(
            "balance.ai_behavior.enemy_trace_continuous_hostile"
        )
        cls.ENEMY_MEMORY_TURNS = GameConfig._get_required("balance.enemy_memory_turns")
        cls.OVERHEAT_COOLDOWN_AMOUNT = GameConfig._get_required("balance.overheat_cooldown_amount")
        cls.OVERHEAT_MINIMUM_HEAT = GameConfig._get_required("balance.overheat_minimum_heat")

    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies - FAILS if not found."""
        game_data = DataLoader.load_game_data()
        try:
            multipliers = game_data["difficulty_multipliers"]
            return multipliers[difficulty]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Difficulty '{difficulty}' not found in game_content.json difficulty_multipliers"
            logging.error(error_msg)
            if "difficulty_multipliers" in game_data:
                logging.error(
                    f"Available difficulties: {list(game_data['difficulty_multipliers'].keys())}"
                )
            else:
                logging.error("'difficulty_multipliers' section missing from game_content.json")
                logging.error(f"Available sections: {list(game_data.keys())}")
            raise KeyError(f"Difficulty multiplier not found for: {difficulty}") from e


# Load configurations when module is imported
GameConfig.load_from_json()
RoomGenerationConfig.load_from_json()
GameBalance.load_from_json()
