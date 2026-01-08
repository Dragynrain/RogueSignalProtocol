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


def has_shown_thought(thought_key: str) -> bool:
    """Check if a thought has already been shown."""
    return thought_key in _shown_thoughts
