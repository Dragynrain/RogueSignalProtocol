"""
Ascension System - Progressive difficulty modifiers.

Core components:
- AscensionModifiers: Dataclass storing modifier values for a run
- calculate_ascension_modifiers(): Cumulative calculation from level
- is_ascension_unlocked(): Check if level is available
- unlock_next_ascension(): Progression after victory
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AscensionModifiers:
    """
    Stores modifier values for a single ascension level.

    All values are DELTAS from base game, not absolute values.
    Neutral defaults (0, 1.0, None, False) mean no modification.
    """

    # A1: Scanner vision bonus
    scanner_vision_bonus: int = 0

    # A2: Enemy HP bonus (flat add to all enemies)
    enemy_hp_bonus: int = 0

    # A3: Background trace gain multiplier
    trace_gain_multiplier: float = 1.0

    # A4: Enemy damage multiplier
    enemy_damage_multiplier: float = 1.0

    # A5: All enemy vision bonus
    enemy_vision_bonus: int = 0

    # A6: Blind spot coverage reduction per floor
    blind_spot_reduction_per_floor: int = 0

    # A7: Hostile trace bonus (flat add when spotted)
    hostile_trace_bonus: float = 0.0

    # A8: Heat reduction override (None = use default)
    heat_reduction_override: int | None = None

    # A9: Enemy count bonus per floor
    enemy_count_bonus: int = 0

    # A10: Player vision override (None = use default 15)
    player_vision_override: int | None = None

    # A11: Code reduction per floor
    code_reduction_per_floor: int = 0
    code_minimum: int = 3  # Hard floor for codes

    # A12: Spawn weight overrides (None = use default)
    spawn_weights: dict[str, int] | None = None

    # A13: Node capacity ranges by floor (None = unlimited)
    node_capacity_ranges: dict[str, list[int]] | None = None

    # A14: Starting RAM override (None = use default 8)
    starting_ram_override: int | None = None

    # A15: Alert range override (None = use default 6)
    alert_range_override: int | None = None

    # A16: Room generation overrides
    room_generation_overrides: dict | None = None

    # A17: Melee heat bonus
    melee_heat_bonus: int = 0

    # A18: Upgrade reduction per floor
    upgrade_reduction_per_floor: int = 0

    # A19: Node reduction per floor
    node_reduction_per_floor: int = 0

    # A20: Blind spots consumable (disappear when used)
    blind_spots_consumable: bool = False


def _load_ascension_config() -> dict:
    """Load ascension config from game_rules.json."""
    game_rules_path = Path(__file__).parent / "game_rules.json"
    with open(game_rules_path, encoding="utf-8") as f:
        rules = json.load(f)
    return rules.get("ascension", {})


def calculate_ascension_modifiers(level: int) -> AscensionModifiers:
    """
    Calculate cumulative modifiers for a given ascension level.

    Modifiers are CUMULATIVE - level N includes all modifiers from 1 to N.
    Level 0 returns neutral/default modifiers (base game).

    Args:
        level: Ascension level (0-20)

    Returns:
        AscensionModifiers with all applicable modifiers set
    """
    mods = AscensionModifiers()

    if level <= 0:
        return mods

    config = _load_ascension_config()
    modifiers_config = config.get("modifiers", {})

    # Apply modifiers cumulatively from 1 to level
    for lvl in range(1, level + 1):
        lvl_config = modifiers_config.get(str(lvl), {})

        # A1: Scanner vision
        if "scanner_vision_bonus" in lvl_config:
            mods.scanner_vision_bonus += lvl_config["scanner_vision_bonus"]

        # A2: Enemy HP
        if "enemy_hp_bonus" in lvl_config:
            mods.enemy_hp_bonus += lvl_config["enemy_hp_bonus"]

        # A3: Trace gain multiplier (replaces, not additive)
        if "trace_gain_multiplier" in lvl_config:
            mods.trace_gain_multiplier = lvl_config["trace_gain_multiplier"]

        # A4: Enemy damage multiplier (replaces)
        if "enemy_damage_multiplier" in lvl_config:
            mods.enemy_damage_multiplier = lvl_config["enemy_damage_multiplier"]

        # A5: All enemy vision bonus
        if "enemy_vision_bonus" in lvl_config:
            mods.enemy_vision_bonus += lvl_config["enemy_vision_bonus"]

        # A6: Blind spot reduction
        if "blind_spot_reduction_per_floor" in lvl_config:
            mods.blind_spot_reduction_per_floor += lvl_config["blind_spot_reduction_per_floor"]

        # A7: Hostile trace bonus
        if "hostile_trace_bonus" in lvl_config:
            mods.hostile_trace_bonus += lvl_config["hostile_trace_bonus"]

        # A8: Heat reduction override (replaces)
        if "heat_reduction_override" in lvl_config:
            mods.heat_reduction_override = lvl_config["heat_reduction_override"]

        # A9: Enemy count bonus
        if "enemy_count_bonus" in lvl_config:
            mods.enemy_count_bonus += lvl_config["enemy_count_bonus"]

        # A10: Player vision override (replaces)
        if "player_vision_override" in lvl_config:
            mods.player_vision_override = lvl_config["player_vision_override"]

        # A11: Code reduction
        if "code_reduction_per_floor" in lvl_config:
            mods.code_reduction_per_floor += lvl_config["code_reduction_per_floor"]
        if "code_minimum" in lvl_config:
            mods.code_minimum = lvl_config["code_minimum"]

        # A12: Spawn weights (replaces)
        if "spawn_weights" in lvl_config:
            mods.spawn_weights = lvl_config["spawn_weights"]

        # A13: Node capacity ranges (replaces)
        if "node_capacity_ranges" in lvl_config:
            mods.node_capacity_ranges = lvl_config["node_capacity_ranges"]

        # A14: Starting RAM override
        if "starting_ram_override" in lvl_config:
            mods.starting_ram_override = lvl_config["starting_ram_override"]

        # A15: Alert range override
        if "alert_range_override" in lvl_config:
            mods.alert_range_override = lvl_config["alert_range_override"]

        # A16: Room generation overrides (replaces)
        if "room_generation" in lvl_config:
            mods.room_generation_overrides = lvl_config["room_generation"]

        # A17: Melee heat bonus
        if "melee_heat_bonus" in lvl_config:
            mods.melee_heat_bonus += lvl_config["melee_heat_bonus"]

        # A18: Upgrade reduction
        if "upgrade_reduction_per_floor" in lvl_config:
            mods.upgrade_reduction_per_floor += lvl_config["upgrade_reduction_per_floor"]

        # A19: Node reduction
        if "node_reduction_per_floor" in lvl_config:
            mods.node_reduction_per_floor += lvl_config["node_reduction_per_floor"]

        # A20: Consumable blind spots
        if "blind_spots_consumable" in lvl_config:
            mods.blind_spots_consumable = lvl_config["blind_spots_consumable"]

    return mods


def is_ascension_unlocked(level: int, highest_unlocked: int) -> bool:
    """
    Check if an ascension level is unlocked.

    Args:
        level: Level to check (0-20)
        highest_unlocked: Highest level player has unlocked

    Returns:
        True if level is playable
    """
    return level <= highest_unlocked


def unlock_next_ascension(current_level: int, highest_unlocked: int) -> int:
    """
    Attempt to unlock the next ascension level after a victory.

    Only unlocks if current_level equals highest_unlocked (playing at frontier).
    Cannot exceed max level (20).

    Args:
        current_level: Level that was just beaten
        highest_unlocked: Current highest unlocked level

    Returns:
        New highest_unlocked value
    """
    config = _load_ascension_config()
    max_level = config.get("max_level", 20)

    if current_level >= highest_unlocked and highest_unlocked < max_level:
        return highest_unlocked + 1

    return highest_unlocked


def get_max_ascension_level() -> int:
    """Get the maximum ascension level from config."""
    config = _load_ascension_config()
    return config.get("max_level", 20)
