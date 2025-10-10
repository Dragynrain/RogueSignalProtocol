#!/usr/bin/env python3
"""
Game data definitions and static data.
Extracted from RogueSignalProtocol.py for better organization.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition, EnemyMovement, TargetingMode
from data_loading import DataLoader


class GameData:
    """Static game data definitions."""
    
    ENEMY_TYPES = {
        # Rebalanced for challenging stealth gameplay
        'scanner': EnemyTypeDefinition('S', 35, 5, EnemyMovement.STATIC, "Scanner", 0),  # High vision, no attack - pure trace level
        'patrol': EnemyTypeDefinition('P', 40, 4, EnemyMovement.PATROL, "Patrol", 15),  # Larger coverage, moderate damage
        'bot': EnemyTypeDefinition('B', 25, 3, EnemyMovement.RANDOM, "Bot", 8),  # More HP, better vision, light damage
        'firewall': EnemyTypeDefinition('F', 80, 6, EnemyMovement.STATIC, "Firewall", 5),  # Massive HP, huge vision, small attack
        'hunter': EnemyTypeDefinition('H', 50, 6, EnemyMovement.RANDOM, "Hunter", 22),  # Elite threat - good vision, high damage
        'virus': EnemyTypeDefinition('V', 35, 4, EnemyMovement.RANDOM, "Virus", 0),  # Base movement (overridden on spawn) - applies virus instead of damage
        'inhibitor': EnemyTypeDefinition('I', 30, 4, EnemyMovement.RANDOM, "Inhibitor", 5),  # Low damage, slows player movement
        'admin': EnemyTypeDefinition('A', 250, 8, EnemyMovement.ADMIN, "Admin Avatar", 45)  # Boss-level - constant seeking with perfect vision
    }
    
    EXPLOITS = {
        # Rebalanced for strategic resource management with damage values
        'shadow_step': ExploitDefinition("Shadow Step", 3, 30, 6, "stealth", 0, TargetingMode.SINGLE,
                                       "Teleport to any shadow zone within range (6 tiles)"),  # No damage, pure mobility
        'data_mimic': ExploitDefinition("Data Mimic", 2, 25, 0, "stealth", 0, TargetingMode.NONE,
                                      "Become invisible to enemies for 5 turns"),  # No damage, pure stealth
        'noise_maker': ExploitDefinition("Noise Maker", 1, 15, 8, "stealth", 0, TargetingMode.SINGLE,
                                       "Create distraction that lasts 8 turns at target location"),  # No damage, distraction
        'buffer_overflow': ExploitDefinition("Buffer Overflow", 2, 30, 1, "combat", 40, TargetingMode.SINGLE,
                                           "Devastating melee attack (40 damage, 1 tile range)"),  # High single-target damage
        'code_injection': ExploitDefinition("Code Injection", 2, 20, 5, "combat", 25, TargetingMode.SINGLE,
                                          "Ranged attack (25 damage, 5 tile range)"),  # Moderate ranged damage
        'system_crash': ExploitDefinition("System Crash", 4, 45, 3, "combat", 30, TargetingMode.AREA,
                                        "Area attack (30 damage) that disables enemies for 4 turns"),  # Area damage
        'threat_scan': ExploitDefinition("Threat Scan", 3, 20, 0, "utility", 0, TargetingMode.NONE,
                                        "Reveals ALL enemies, vision ranges, & movement paths (5 turns)"),  # No damage, intel
        'log_wiper': ExploitDefinition("Log Wiper", 2, 20, 0, "utility", 0, TargetingMode.NONE,
                                     "Significantly reduces trace level (-50%)"),  # No damage, counter-trace level
        'antivirus': ExploitDefinition("Antivirus", 2, 25, 0, "utility", 0, TargetingMode.NONE,
                                     "Purges all negative status effects (virus, etc.)"),  # Status cleansing
        'emp_burst': ExploitDefinition("EMP Burst", 4, 50, 3, "emergency", 20, TargetingMode.AREA,
                                     "Area attack (20 damage) that disables all nearby enemies"),  # Moderate area damage + disable
        'memory_leak': ExploitDefinition("Memory Leak", 2, 30, 1, "combat", 0, TargetingMode.AREA,
                                        "Target enemies forget they saw you (3x3 area)"),  # Non-lethal area crowd control
        'network_scan': ExploitDefinition("Network Scan", 1, 15, 0, "utility", 0, TargetingMode.NONE,
                                     "Reveals all cooling nodes, CPU nodes, and ghost nodes on the level")  # Cheap utility
    }


class GameUpgrades:
    """Static upgrade definitions."""
    
    UPGRADES = {
        'ram_boost': UpgradeDefinition(
            "Memory Expansion", "[", (100, 149, 237), "ram", 4
        ),
        'cpu_boost': UpgradeDefinition(
            "Processing Core", "]", (50, 205, 50), "cpu", 20
        ),
        'heat_boost': UpgradeDefinition(
            "Cooling Matrix", "=", (20, 255, 200), "heat", 20
        )
    }


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
            return balance['player_stats'][stat_name]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Player stat '{stat_name}' not found in game_content.json balance.player_stats"
            print(error_msg)
            import logging
            logging.error(error_msg)
            if 'player_stats' in balance:
                print(f"Available player stats: {list(balance['player_stats'].keys())}")
            else:
                print(f"'player_stats' section missing from balance config")
                print(f"Available balance sections: {list(balance.keys())}")
            raise KeyError(f"Player stat not found: {stat_name}") from e

    @classmethod
    def get_combat_value(cls, value_name: str):
        """Get combat value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance['combat'][value_name]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Combat value '{value_name}' not found in game_content.json balance.combat"
            print(error_msg)
            import logging
            logging.error(error_msg)
            if 'combat' in balance:
                print(f"Available combat values: {list(balance['combat'].keys())}")
            else:
                print(f"'combat' section missing from balance config")
                print(f"Available balance sections: {list(balance.keys())}")
            raise KeyError(f"Combat value not found: {value_name}") from e

    @classmethod
    def get_code_hack_value(cls, value_name: str):
        """Get code hack value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance['code_hacks'][value_name]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Code hack value '{value_name}' not found in game_content.json balance.code_hacks"
            print(error_msg)
            import logging
            logging.error(error_msg)
            if 'code_hacks' in balance:
                print(f"Available code hack values: {list(balance['code_hacks'].keys())}")
            else:
                print(f"'code_hacks' section missing from balance config")
                print(f"Available balance sections: {list(balance.keys())}")
            raise KeyError(f"Code hack value not found: {value_name}") from e

    @classmethod
    def get_temporary_effect_value(cls, value_name: str):
        """Get temporary effect value from balance config - FAILS if not found."""
        balance = cls.get_balance()
        try:
            return balance['temporary_effects'][value_name]
        except KeyError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Temporary effect '{value_name}' not found in game_content.json balance.temporary_effects"
            print(error_msg)
            import logging
            logging.error(error_msg)
            if 'temporary_effects' in balance:
                print(f"Available temporary effects: {list(balance['temporary_effects'].keys())}")
            else:
                print(f"'temporary_effects' section missing from balance config")
                print(f"Available balance sections: {list(balance.keys())}")
            raise KeyError(f"Temporary effect value not found: {value_name}") from e
    
    # NO FALLBACK VALUES - All values must come from JSON
    # These properties dynamically fetch from JSON and will raise KeyError if missing

    @classmethod
    def __getattr__(cls, name):
        """Dynamic attribute access for balance values - NO FALLBACKS."""
        if name == 'CPU_RESTORE_MIN':
            return cls.get_balance()['cpu_restore_min']
        elif name == 'CPU_RESTORE_MAX':
            return cls.get_balance()['cpu_restore_max']
        elif name == 'HEAT_REDUCTION_INSTANT':
            return cls.get_code_hack_value('heat_reduction_instant')
        elif name == 'ENEMY_ELIMINATION_CPU_REWARD':
            return cls.get_combat_value('enemy_elimination_cpu_reward')
        raise AttributeError(f"'{cls.__name__}' has no attribute '{name}'")

    @staticmethod
    def get_exploit_cpu_cost(exploit_name: str) -> int:
        """Get CPU cost for an exploit - uses game_content.json."""
        # Delegate to GameBalance which loads from JSON
        from game_config import GameBalance
        return GameBalance.get_exploit_cpu_cost(exploit_name)

    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies - uses game_content.json."""
        # Delegate to GameBalance which loads from JSON
        from game_config import GameBalance
        return GameBalance.get_enemy_difficulty_multiplier(difficulty)