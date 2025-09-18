#!/usr/bin/env python3
"""
Game data definitions and static data.
Extracted from RogueSignalProtocol.py for better organization.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition, EnemyMovement, TargetingMode


class GameData:
    """Static game data definitions."""
    
    ENEMY_TYPES = {
        # Rebalanced for challenging stealth gameplay
        'scanner': EnemyTypeDefinition('S', 35, 5, EnemyMovement.STATIC, "Scanner", 0),  # High vision, no attack - pure detection
        'patrol': EnemyTypeDefinition('P', 40, 4, EnemyMovement.PATROL, "Patrol", 15),  # Larger coverage, moderate damage
        'bot': EnemyTypeDefinition('B', 25, 3, EnemyMovement.RANDOM, "Bot", 8),  # More HP, better vision, light damage
        'firewall': EnemyTypeDefinition('F', 80, 6, EnemyMovement.STATIC, "Firewall", 5),  # Massive HP, huge vision, small attack
        'hunter': EnemyTypeDefinition('H', 50, 6, EnemyMovement.SEEK, "Hunter", 22),  # Elite threat - good vision, high damage
        'virus': EnemyTypeDefinition('V', 35, 4, EnemyMovement.SEEK, "Virus", 0),  # No direct damage - applies venom instead
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
                                     "Significantly reduces detection level (-50%)"),  # No damage, counter-detection
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
    """Game balance configuration and constants."""
    
    # CPU restoration from data patches
    CPU_RESTORE_MIN = 15
    CPU_RESTORE_MAX = 35
    
    # Heat reduction amounts
    HEAT_REDUCTION_INSTANT = 30
    
    # Detection system
    DETECTION_THRESHOLD_ALERT = 75
    DETECTION_THRESHOLD_HOSTILE = 100
    
    # Effect durations
    SPEED_BOOST_DURATION = 5
    ENHANCED_VISION_DURATION = 5
    EXPLOIT_EFFICIENCY_DURATION = 8
    
    # Virus system
    VIRUS_BASE_DURATION = 3
    VIRUS_MAX_DURATION = 10
    VIRUS_DAMAGE_PER_TURN = 2
    
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