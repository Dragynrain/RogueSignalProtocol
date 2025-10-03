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
        'admin': EnemyTypeDefinition('A', 250, 8, EnemyMovement.TRACK, "Admin Avatar", 45)  # Boss-level but not impossible
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
    def get_player_stat(cls, stat_name: str, default_value=None):
        """Get player stat from balance config."""
        balance = cls.get_balance()
        return balance.get('player_stats', {}).get(stat_name, default_value)
    
    @classmethod
    def get_combat_value(cls, value_name: str, default_value=None):
        """Get combat value from balance config."""
        balance = cls.get_balance()
        return balance.get('combat', {}).get(value_name, default_value)
    
    @classmethod
    def get_code_patch_value(cls, value_name: str, default_value=None):
        """Get code patch value from balance config."""
        balance = cls.get_balance()
        return balance.get('code_patches', {}).get(value_name, default_value)
    
    @classmethod
    def get_temporary_effect_value(cls, value_name: str, default_value=None):
        """Get temporary effect value from balance config."""
        balance = cls.get_balance()
        return balance.get('temporary_effects', {}).get(value_name, default_value)
    
    # Legacy properties for backward compatibility
    @property
    def CPU_RESTORE_MIN(self):
        return self.get_code_patch_value('cpu_restore_min', 15)
    
    @property
    def CPU_RESTORE_MAX(self):
        return self.get_code_patch_value('cpu_restore_max', 35)
    
    @property
    def HEAT_REDUCTION_INSTANT(self):
        return self.get_code_patch_value('heat_reduction_instant', 30)
    
    @property
    def ENEMY_ELIMINATION_CPU_REWARD(self):
        return self.get_combat_value('enemy_elimination_cpu_reward', 5)
    
    @staticmethod
    def get_exploit_cpu_cost(exploit_name: str) -> int:
        """Get CPU cost for an exploit."""
        cpu_costs = {
            "shadow_step": 10,
            "buffer_overflow": 15,
            "code_injection": 20,
            "system_crash": 25,
            "threat_scan": 5,
            "log_wiper": 12,
            "antivirus": 18,
            "emp_burst": 30,
            "memory_leak": 8
        }
        return cpu_costs.get(exploit_name, 10)
    
    @staticmethod
    def get_enemy_difficulty_multiplier(difficulty: str) -> float:
        """Get difficulty multiplier for enemies."""
        multipliers = {
            "easy": 0.8,
            "normal": 1.0,
            "hard": 1.3,
            "nightmare": 1.6
        }
        return multipliers.get(difficulty, 1.0)