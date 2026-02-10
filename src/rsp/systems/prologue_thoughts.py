"""
Reactive internal voice system for prologue tutorial.

Tutorial guidance delivered as the protagonist's internal thoughts -
reactive to player actions, not pre-emptive instructions. The character
reflects on what just happened, teaching through experience.

Design principles:
- Reactive: Responds to outcomes (success/failure), not pre-emptive hints
- Reflective: Character thinks about what just happened and why
- One-shot: Each thought triggers ONCE per session
"""

from rsp.entities.base import Colors

# Track shown thoughts - reset on prologue restart
_shown_thoughts: set[str] = set()


# =============================================================================
# THOUGHT TRIGGER REGISTRY
# =============================================================================
# Central documentation of where each thought is triggered.
# Format: "thought_key": ("file:function", "trigger condition")
#
# This registry exists for MAINTENANCE purposes - to audit that all thoughts
# have triggers and to locate where triggers are implemented.
# =============================================================================

THOUGHT_TRIGGER_REGISTRY: dict[str, tuple[str, str]] = {
    # Movement & Combat
    "diagonal_discover": (
        "engine.py:move_player",
        "Player moves diagonally (dx != 0 and dy != 0)",
    ),
    "melee_success": (
        "engine.py:_perform_bump_attack",
        "Player kills enemy with bump attack",
    ),
    # Turn-based awareness
    "turn_based_observe": (
        "turn_manager.py:_update_enemy_positions",
        "First time player sees enemy move",
    ),
    "wait_fail": (
        "engine.py:move_player",
        "Player waits (dx=0,dy=0) but takes damage after",
    ),
    "wait_success": (
        "engine.py:move_player",
        "Player waits with nearby enemy and survives",
    ),
    # FOV & Blind Spots
    "fov_bidirectional": (
        "turn_manager.py:_enemy_attacks_player",
        "Enemy spots player (bidirectional visibility)",
    ),
    "blindspot_observe": (
        "turn_manager.py:_check_blindspot_thoughts",
        "Player enters a blind spot tile",
    ),
    "blindspot_adjacent_fail": (
        "turn_manager.py:_enemy_attacks_player",
        "Player in blind spot but adjacent enemy sees through",
    ),
    "blindspot_range_success": (
        "turn_manager.py:_update_enemy_states",
        "Enemy doesn't see player in blind spot at range > 1",
    ),
    # Alert & Escape
    "alert_to_hostile_fail": (
        "turn_manager.py:_enemy_attacks_player",
        "Player hit after failing to escape alert",
    ),
    "alert_escape_success": (
        "turn_manager.py:_update_enemy_states",
        "Enemy loses sight during alert, doesn't go hostile",
    ),
    # Exploits
    "exploit_equip_hint": (
        "turn_manager.py:_handle_pickups",
        "Player picks up Code Injection exploit in prologue",
    ),
    "exploit_observe": (
        "turn_manager.py:_check_blindspot_thoughts",
        "Player in blind spot sees enemy at range 2-5",
    ),
    "exploit_success": (
        "combat.py:use_exploit",
        "Player kills enemy with exploit",
    ),
    "exploit_ranged_practice": (
        "combat.py:use_exploit",
        "Player hits enemy at range with exploit",
    ),
    "utility_pickup": (
        "turn_manager.py:_handle_item_pickup",
        "Player picks up Threat Scan (utility exploit)",
    ),
    # Code Hacks
    "code_hack_discovery": (
        "turn_manager.py:_handle_code_hack_pickup",
        "Player uses code hack, sees effect matches color",
    ),
    # Enemy Intent
    "intent_observe": (
        "info_panel.py:_render_enemy_info",
        "Player views enemy info showing movement queue",
    ),
    # Heat & Nodes
    "heat_high": (
        "combat.py:_apply_heat_damage",
        "Player heat exceeds 60",
    ),
    "cooling_node_use": (
        "turn_manager.py:_handle_node_effects",
        "Player enters cooling node",
    ),
    "cpu_node_use": (
        "turn_manager.py:_handle_node_effects",
        "Player enters CPU recovery node",
    ),
    "ghost_node_use": (
        "turn_manager.py:_handle_node_effects",
        "Player enters ghost node",
    ),
    # Navigation
    "stealth_choice": (
        "engine.py:move_player",
        "Player enters stepping blind spot alcove (x=11-14, y=19)",
    ),
    "gateway_spotted": (
        "engine.py:move_player",
        "Player has LOS to gateway",
    ),
}


# Thought definitions - message text loaded from narrative_content.json
# These keys match the prologue_thoughts section in narrative_content.json
THOUGHT_KEYS = {
    "diagonal_discover",
    "melee_success",
    "turn_based_observe",
    "wait_fail",
    "wait_success",
    "fov_bidirectional",
    "blindspot_observe",
    "blindspot_adjacent_fail",
    "blindspot_range_success",
    "alert_to_hostile_fail",
    "alert_escape_success",
    "exploit_equip_hint",
    "exploit_observe",
    "exploit_success",
    "exploit_ranged_practice",
    "utility_pickup",
    "code_hack_discovery",
    "intent_observe",
    "heat_high",
    "cooling_node_use",
    "cpu_node_use",
    "ghost_node_use",
    "stealth_choice",
    "gateway_spotted",
}


def show_prologue_thought(thought_key: str, game) -> bool:
    """
    Show internal thought if in prologue mode and not already shown.

    Args:
        thought_key: Key from THOUGHT_KEYS (matches narrative_content.json)
        game: GameEngine instance

    Returns:
        True if thought was shown, False otherwise
    """
    # Only show thoughts in prologue mode
    if not getattr(game, "prologue_mode", False):
        return False

    # Don't repeat thoughts
    if thought_key in _shown_thoughts:
        return False

    # Validate key
    if thought_key not in THOUGHT_KEYS:
        return False

    # Get message from narrative content
    from rsp.core.data_loading import get_prologue_thoughts

    prologue_thoughts = get_prologue_thoughts()
    message = prologue_thoughts.get(thought_key)
    if not message:
        return False

    # Show the thought (using DIMMED for subtle tutorial feedback)
    game.message_log.add_message(message, Colors.DIMMED)
    _shown_thoughts.add(thought_key)
    return True


def reset_prologue_thoughts():
    """Reset on prologue restart - lets player learn again."""
    _shown_thoughts.clear()


def validate_thought_keys() -> list[str]:
    """Validate that all THOUGHT_KEYS have corresponding entries in narrative_content.json.

    Call this at game startup to catch configuration errors early.

    Returns:
        List of missing keys (empty if all keys are valid)
    """
    from rsp.core.data_loading import get_prologue_thoughts

    prologue_thoughts = get_prologue_thoughts()
    missing = []
    for key in THOUGHT_KEYS:
        if key not in prologue_thoughts:
            missing.append(key)
    return missing


def validate_trigger_registry() -> dict[str, list[str]]:
    """Validate the thought trigger registry for completeness.

    Returns:
        Dict with 'missing_registry' (keys in THOUGHT_KEYS but not in registry)
        and 'missing_keys' (keys in registry but not in THOUGHT_KEYS).
        Empty lists mean the registry is complete and consistent.
    """
    registry_keys = set(THOUGHT_TRIGGER_REGISTRY.keys())
    missing_registry = [k for k in THOUGHT_KEYS if k not in registry_keys]
    missing_keys = [k for k in registry_keys if k not in THOUGHT_KEYS]

    return {
        "missing_registry": missing_registry,
        "missing_keys": missing_keys,
    }


def get_trigger_location(thought_key: str) -> tuple[str, str] | None:
    """Get the file/function and condition where a thought is triggered.

    Useful for debugging and maintenance.

    Args:
        thought_key: The thought key to look up

    Returns:
        Tuple of (file:function, trigger_condition) or None if not found
    """
    return THOUGHT_TRIGGER_REGISTRY.get(thought_key)


def has_shown_thought(thought_key: str) -> bool:
    """Check if a thought has already been shown."""
    return thought_key in _shown_thoughts
