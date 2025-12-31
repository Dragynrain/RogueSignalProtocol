#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Data Definitions

Static game data and definitions loaded from JSON configuration.
Provides GameData class with enemy types, exploits, upgrades, and code hacks.
Uses DataLoader for configuration loading with no hardcoded fallbacks.
GameUpgrades class handles upgrade discovery and management.
"""

from rsp.core.data_loading import DataLoader
from rsp.entities.base import (
    EnemyMovement,
    EnemyTypeDefinition,
    ExploitDefinition,
    TargetingMode,
    UpgradeDefinition,
)


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

    # Will be populated at module level after class definition
    ENEMY_TYPES = None

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


# Load enemy types on module initialization (after class is defined)
GameData.ENEMY_TYPES = GameData._load_enemy_types()


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
        from rsp.core.data_loading import DataLoader
        from rsp.entities.base import ensure_color_tuple

        content = DataLoader.load_game_data()
        upgrades_data = content["upgrades"]

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
