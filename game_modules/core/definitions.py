"""
Game definition classes for enemies, exploits, and upgrades.
"""

from dataclasses import dataclass
from typing import Tuple

from .data_structures import EnemyMovement, TargetingMode


@dataclass
class EnemyTypeDefinition:
    """Definition of an enemy type with all its properties."""
    symbol: str
    cpu: int
    vision: int
    movement: EnemyMovement
    name: str
    damage: int


@dataclass
class ExploitDefinition:
    """Definition of an exploit with its properties."""
    name: str
    ram: int
    heat: int
    range: int
    exploit_class: str  # Category: 'stealth', 'combat', 'utility', 'emergency'
    damage: int = 0  # Damage dealt (0 for non-combat exploits)
    targeting: TargetingMode = TargetingMode.SINGLE
    description: str = ""


@dataclass
class UpgradeDefinition:
    """Definition of a permanent upgrade with its properties."""
    name: str
    symbol: str
    color: Tuple[int, int, int]  # RGB color tuple
    stat_type: str  # 'ram', 'cpu', 'heat'
    bonus_amount: int


class GameData:
    """Static game data definitions for enemies and exploits."""
    
    ENEMY_TYPES = {
        # Balanced for challenging stealth gameplay
        'scanner': EnemyTypeDefinition('S', 35, 5, EnemyMovement.STATIC, "Scanner", 0),
        'patrol': EnemyTypeDefinition('P', 40, 4, EnemyMovement.PATROL, "Patrol", 15),
        'bot': EnemyTypeDefinition('B', 25, 3, EnemyMovement.RANDOM, "Bot", 8),
        'firewall': EnemyTypeDefinition('F', 80, 6, EnemyMovement.STATIC, "Firewall", 0),
        'hunter': EnemyTypeDefinition('H', 50, 6, EnemyMovement.RANDOM, "Hunter", 22),
        'virus': EnemyTypeDefinition('V', 35, 4, EnemyMovement.RANDOM, "Virus", 0),
        'inhibitor': EnemyTypeDefinition('I', 30, 4, EnemyMovement.RANDOM, "Inhibitor", 5),
        'admin': EnemyTypeDefinition('A', 250, 8, EnemyMovement.RANDOM, "Admin Avatar", 45)
    }
    
    EXPLOITS = {
        # Balanced for strategic resource management
        'shadow_step': ExploitDefinition(
            "Shadow Step", 3, 30, 6, "stealth", 0, TargetingMode.SINGLE,
            "Teleport to any shadow zone within range (6 tiles)"
        ),
        'data_mimic': ExploitDefinition(
            "Data Mimic", 2, 25, 0, "stealth", 0, TargetingMode.SINGLE,
            "Become invisible to enemies for 5 turns"
        ),
        'noise_maker': ExploitDefinition(
            "Noise Maker", 1, 15, 8, "stealth", 0, TargetingMode.SINGLE,
            "Create distraction that lasts 8 turns at target location"
        ),
        'buffer_overflow': ExploitDefinition(
            "Buffer Overflow", 2, 30, 1, "combat", 40, TargetingMode.SINGLE,
            "Devastating melee attack (40 damage, 1 tile range)"
        ),
        'code_injection': ExploitDefinition(
            "Code Injection", 2, 20, 5, "combat", 25, TargetingMode.SINGLE,
            "Ranged attack (25 damage, 5 tile range)"
        ),
        'system_crash': ExploitDefinition(
            "System Crash", 4, 45, 3, "combat", 30, TargetingMode.AREA,
            "Area attack (30 damage) that disables enemies for 4 turns"
        ),
        'threat_scan': ExploitDefinition(
            "Threat Scan", 3, 20, 0, "utility", 0, TargetingMode.SINGLE,
            "Reveals ALL enemies, vision ranges, & movement paths (5 turns)"
        ),
        'log_wiper': ExploitDefinition(
            "Log Wiper", 2, 20, 0, "utility", 0, TargetingMode.SINGLE,
            "Significantly reduces detection level (-50%)"
        ),
        'antivirus': ExploitDefinition(
            "Antivirus", 2, 25, 0, "utility", 0, TargetingMode.SINGLE,
            "Purges all negative status effects (virus, etc.)"
        ),
        'emp_burst': ExploitDefinition(
            "EMP Burst", 4, 50, 3, "emergency", 20, TargetingMode.AREA,
            "Area attack (20 damage) that disables all nearby enemies"
        ),
        'memory_leak': ExploitDefinition(
            "Memory Leak", 2, 30, 1, "combat", 0, TargetingMode.AREA,
            "Target enemies forget they saw you (3x3 area)"
        ),
        'network_scan': ExploitDefinition(
            "Network Scan", 1, 15, 0, "utility", 0, TargetingMode.SINGLE,
            "Reveals all cooling nodes, CPU nodes, and ghost nodes on the level"
        )
    }

    UPGRADES = {
        'ram_boost': UpgradeDefinition(
            "Memory Expansion", "[", (100, 149, 237), "ram", 4
        ),
        'cpu_boost': UpgradeDefinition(
            "Processor Upgrade", "]", (255, 215, 0), "cpu", 4
        ),
        'heat_sink': UpgradeDefinition(
            "Advanced Cooling", "°", (0, 191, 255), "heat", 4
        )
    }