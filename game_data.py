#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Data Definitions

Static game data and definitions loaded from JSON configuration.
Provides GameData class with enemy types, exploits, upgrades, and code hacks.
Uses DataLoader for configuration loading with no hardcoded fallbacks.
GameUpgrades class handles upgrade discovery and management.
"""

from data_loading import DataLoader
from game_entities import (
    EnemyMovement,
    EnemyTypeDefinition,
    ExploitDefinition,
    TargetingMode,
    UpgradeDefinition,
)
from game_errors import GameErrorHandler


class GameData:
    """Static game data definitions loaded from JSON."""

    @staticmethod
    def _load_enemy_types():
        """Load enemy types from JSON - NO FALLBACKS."""
        game_data = DataLoader.load_game_data()
        if "enemy_types" not in game_data:
            raise KeyError("CRITICAL: 'enemy_types' section missing from game_content.json")

        enemy_types = {}
        for enemy_id, data in game_data["enemy_types"].items():
            # Map movement string to enum
            movement_str = data["movement"].upper()
            try:
                movement = EnemyMovement[movement_str]
            except KeyError:
                raise ValueError(
                    f"Unknown movement type '{data['movement']}' for enemy '{enemy_id}'"
                )

            enemy_types[enemy_id] = EnemyTypeDefinition(
                symbol=data["symbol"],
                cpu=data["cpu"],
                vision=data["vision"],
                movement=movement,
                name=data["name"],
                damage=data["damage"],
            )

        return enemy_types

    # Load enemy types on module initialization
    ENEMY_TYPES = _load_enemy_types.__func__()

    EXPLOITS = {
        # Rebalanced for strategic resource management with damage values
        "system_hop": ExploitDefinition(
            "System Hop",
            3,
            30,
            6,
            "stealth",
            0,
            TargetingMode.SINGLE,
            "Pivot to any blind spot within range (6 tiles)",
            0,
            0,
        ),  # No damage, pure mobility, no duration
        "traffic_masquerade": ExploitDefinition(
            "Traffic Masquerade",
            2,
            25,
            0,
            "stealth",
            0,
            TargetingMode.NONE,
            "Masquerade as legitimate traffic for 5 turns",
            5,
            0,
        ),  # No damage, 5 turn duration, pure stealth
        "decoy_swarm": ExploitDefinition(
            "Decoy Swarm",
            1,
            15,
            8,
            "stealth",
            0,
            TargetingMode.SINGLE,
            "Spawn decoys that last 8 turns at target location",
            8,
            10,
            3,
            2,
        ),  # No damage, 8 turn duration, distraction with radius 10, alert durations: 3 for patrol, 2 for normal
        "buffer_overflow": ExploitDefinition(
            "Buffer Overflow",
            2,
            30,
            1,
            "combat",
            40,
            TargetingMode.SINGLE,
            "Devastating melee attack (40 damage, 1 tile range)",
            0,
            0,
        ),  # High single-target damage
        "code_injection": ExploitDefinition(
            "Code Injection",
            2,
            20,
            5,
            "combat",
            25,
            TargetingMode.SINGLE,
            "Ranged attack (25 damage, 5 tile range)",
            0,
            0,
        ),  # Moderate ranged damage
        "system_crash": ExploitDefinition(
            "System Crash",
            3,
            35,
            0,
            "emergency",
            30,
            TargetingMode.NONE,
            "CRASHES THE SYSTEM YOU'RE ON! Self-damage + AoE stun (30 self-dmg, 30 dmg to enemies, 3t stun, radius 3)",
            3,
            3,
            0,
            0,
            0,
            30,
            "30dmg AoE + stun (SELF-DAMAGE!)",
        ),  # Emergency with self-damage
        "threat_scan": ExploitDefinition(
            "Threat Scan",
            3,
            20,
            0,
            "utility",
            0,
            TargetingMode.NONE,
            "Reveals ALL enemies, vision ranges, & movement paths (5 turns)",
            5,
            0,
        ),  # No damage, 5 turn duration, intel
        "log_wiper": ExploitDefinition(
            "Log Wiper",
            2,
            20,
            0,
            "utility",
            0,
            TargetingMode.NONE,
            "Significantly reduces trace level (-30%)",
            0,
            0,
            0,
            0,
            30,
        ),  # No damage, counter-trace level, 30% reduction
        "antivirus": ExploitDefinition(
            "Antivirus",
            2,
            25,
            0,
            "utility",
            0,
            TargetingMode.NONE,
            "Purges all negative status effects (virus, slow, etc.)",
            0,
            0,
        ),  # Status cleansing
        "denial_of_service": ExploitDefinition(
            "Denial of Service",
            3,
            40,
            4,
            "combat",
            0,
            TargetingMode.AREA,
            "Targeted area denial (radius 1) that disables enemies for 5 turns",
            5,
            1,
        ),  # No damage, 5-turn disable duration, radius 1
        "memory_leak": ExploitDefinition(
            "Memory Leak",
            2,
            30,
            1,
            "combat",
            0,
            TargetingMode.AREA,
            "Target enemies forget they saw you (3x3 area, blinds for 3 turns)",
            3,
            1,
        ),  # Non-lethal area crowd control, 3-turn blindness, radius 1
        "network_scan": ExploitDefinition(
            "Network Scan",
            1,
            15,
            0,
            "utility",
            0,
            TargetingMode.NONE,
            "Reveals all cooling nodes, CPU nodes, and ghost nodes on the level",
            0,
            0,
        ),  # Cheap utility
        "logic_bomb": ExploitDefinition(
            "Logic Bomb",
            2,
            35,
            4,
            "combat",
            15,
            TargetingMode.AREA,
            "Deploy explosive that detonates in radius (15 damage, 2 tile radius) WARNING: Friendly fire!",
            0,
            2,
        ),  # AoE damage with friendly fire, radius 2
    }


class GameUpgrades:
    """Static upgrade definitions - loads colors from JSON."""

    _loaded = False
    UPGRADES = {}

    @classmethod
    def _ensure_loaded(cls):
        """Lazy load upgrades from JSON on first access."""
        if not cls._loaded:
            cls._load_upgrades()
            cls._loaded = True

    @classmethod
    def _load_upgrades(cls):
        """Load upgrade definitions from game_content.json."""
        from data_loading import DataLoader
        from game_entities import ensure_color_tuple

        content = DataLoader.load_game_data()
        upgrades_data = content.get("upgrades", {})

        for key, data in upgrades_data.items():
            cls.UPGRADES[key] = UpgradeDefinition(
                name=data["name"],
                symbol=data["symbol"],
                color=ensure_color_tuple(data["color"]),
                stat_type=data["stat_type"],
                bonus_amount=data["bonus_amount"],
            )


# Load upgrades on module import
GameUpgrades._ensure_loaded()


class GameBalance:
    """Game balance configuration loaded from JSON data."""

    @classmethod
    def get_balance(cls):
        """Get balance configuration from JSON data."""
        return DataLoader.get_balance_config()

    @classmethod
    def get_player_stat(cls, stat_name: str):
        """Get player stat from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance["player_stats"][stat_name]
        except KeyError as e:
            GameErrorHandler.handle_config_error(
                f"Player stat '{stat_name}' not found in game_content.json balance.player_stats", e
            )

    @classmethod
    def get_combat_value(cls, value_name: str):
        """Get combat value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance["combat"][value_name]
        except KeyError as e:
            GameErrorHandler.handle_config_error(
                f"Combat value '{value_name}' not found in game_content.json balance.combat", e
            )

    @classmethod
    def get_code_hack_value(cls, value_name: str):
        """Get code hack value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance["code_hacks"][value_name]
        except KeyError as e:
            GameErrorHandler.handle_config_error(
                f"Code hack value '{value_name}' not found in game_content.json balance.code_hacks",
                e,
            )

    @classmethod
    def get_temporary_effect_value(cls, value_name: str):
        """Get temporary effect value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance["temporary_effects"][value_name]
        except KeyError as e:
            GameErrorHandler.handle_config_error(
                f"Temporary effect '{value_name}' not found in game_content.json balance.temporary_effects",
                e,
            )

    # NO FALLBACK VALUES - All values must come from JSON
    # These properties dynamically fetch from JSON and will raise KeyError if missing

    @classmethod
    def __getattr__(cls, name):
        """Dynamic attribute access for balance values - NO FALLBACKS."""
        if name == "CPU_RESTORE_MIN":
            return cls.get_balance()["cpu_restore_min"]
        elif name == "CPU_RESTORE_MAX":
            return cls.get_balance()["cpu_restore_max"]
        elif name == "HEAT_REDUCTION_INSTANT":
            return cls.get_code_hack_value("heat_reduction_instant")
        elif name == "ENEMY_ELIMINATION_CPU_REWARD":
            return cls.get_combat_value("enemy_elimination_cpu_reward")
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies - uses game_content.json."""
        # Delegate to GameBalance which loads from JSON
        from game_config import GameBalance

        return GameBalance.get_enemy_difficulty_multiplier(difficulty)
