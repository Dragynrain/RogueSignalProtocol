#!/usr/bin/env python3
"""
Game entity enums for state management.

Defines enumeration types for:
- EnemyState: Enemy awareness levels (UNAWARE, ALERT, HOSTILE)
- EnemyMovement: AI movement patterns (STATIC, PATROL, RANDOM, SEEK, etc.)
- TargetingMode: Exploit targeting behavior (NONE, SINGLE, AREA, DIRECTION)

Extracted from game_entities.py to improve modularity.
"""

from enum import Enum


class EnemyState(Enum):
    """
    Enemy awareness states.

    UNAWARE: Enemy has not detected player (green)
    ALERT: Enemy suspects player presence, searching (yellow) - lasts 1 turn
    HOSTILE: Enemy actively pursuing player (red)
    """

    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"


class EnemyMovement(Enum):
    """
    Enemy movement patterns defining AI behavior.

    STATIC: Does not move unless alerted
    PATROL: Follows predefined patrol points in sequence
    RANDOM: Wanders randomly
    SEEK: Actively seeks player (used for hostile behavior)
    ADMIN: Perfect vision and constant seeking (boss-type enemy)
    TRACK: Legacy tracking behavior
    VIRUS: Randomly selects STATIC, PATROL, or RANDOM on spawn (unpredictable)
    """

    STATIC = "static"
    PATROL = "patrol"
    RANDOM = "random"
    SEEK = "seek"
    ADMIN = "admin"
    TRACK = "track"
    VIRUS = "virus"


class TargetingMode(Enum):
    """
    Exploit targeting modes.

    NONE: No targeting required (instant self-buff/debuff)
    SINGLE: Single target selection
    AREA: Area of effect around target point
    DIRECTION: Directional targeting (not currently used)
    """

    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"
