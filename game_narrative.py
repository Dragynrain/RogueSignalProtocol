#!/usr/bin/env python3
"""
Environmental Narrative System

Manages atmospheric flavor messages that enhance storytelling during gameplay.
Messages are triggered by specific game events and displayed in the MessageLog.

Key features:
- Environmental messages for level start, combat, trace, etc.
- Context-aware message selection (don't repeat same message)
- Lightweight integration with existing MessageLog system
- No UI changes needed - uses existing message system

Event types:
- level_start: Entering a new network level
- first_blind_spot: First time entering blind spots on a level
- high_trace: When trace level is dangerously high (>70%)
- low_cpu: When CPU is critical (<30)
- first_combat: First enemy killed on a level
- admin_spawn: When Admin Avatar spawns
- admin_defeated: When Admin Avatar is defeated
- overheating: When player is overheating
- gateway_approach: When near gateway
- random_atmospheric: Occasional ambient messages
"""

import random

from data_loading import get_environmental_messages


class NarrativeManager:
    """
    Manages environmental narrative messages during gameplay.

    Tracks which messages have been shown to avoid repetition within a session,
    and provides methods to trigger appropriate messages for game events.
    """

    def __init__(self):
        """Initialize narrative manager with message pools."""
        self.messages = get_environmental_messages()

        # Track shown messages to avoid repeats (reset per level or session as needed)
        self.shown_messages: dict[str, set[str]] = {
            category: set() for category in self.messages.keys()
        }

        # Per-level flags to ensure certain messages only show once per level
        self.level_flags = {"first_blind_spot": False, "first_combat": False}

    def reset_level_flags(self):
        """Reset per-level flags when starting a new level."""
        self.level_flags = {"first_blind_spot": False, "first_combat": False}

    def get_message(self, category: str, force: bool = False) -> str:
        """
        Get a random message from a category, avoiding recent repeats.

        Args:
            category: Message category (e.g., 'level_start', 'high_trace')
            force: If True, ignore shown message tracking (for one-time events)

        Returns:
            Message string, or empty string if category not found
        """
        if category not in self.messages:
            return ""

        available_messages = self.messages[category]

        if not available_messages:
            return ""

        # Filter out recently shown messages (if not forcing)
        if not force and category in self.shown_messages:
            unshown = [
                msg for msg in available_messages if msg not in self.shown_messages[category]
            ]

            # If we've shown all messages, reset the tracking for this category
            if not unshown:
                self.shown_messages[category].clear()
                unshown = available_messages

            available_messages = unshown

        # Pick random message
        message = random.choice(available_messages)

        # Track it
        if category in self.shown_messages:
            self.shown_messages[category].add(message)

        return message

    def trigger_level_start(self) -> str:
        """Trigger level start message."""
        return self.get_message("level_start")

    def trigger_first_blind_spot(self) -> str:
        """Trigger first blind spot entry message (once per level)."""
        if not self.level_flags["first_blind_spot"]:
            self.level_flags["first_blind_spot"] = True
            return self.get_message("first_blind_spot")
        return ""

    def trigger_high_trace(self) -> str:
        """Trigger high trace warning message."""
        return self.get_message("high_trace")

    def trigger_low_cpu(self) -> str:
        """Trigger low CPU warning message."""
        return self.get_message("low_cpu")

    def trigger_first_combat(self) -> str:
        """Trigger first combat message (once per level)."""
        if not self.level_flags["first_combat"]:
            self.level_flags["first_combat"] = True
            return self.get_message("first_combat")
        return ""

    def trigger_admin_spawn(self) -> str:
        """Trigger admin spawn message."""
        return self.get_message("admin_spawn")

    def trigger_admin_defeated(self) -> str:
        """Trigger admin defeated message."""
        return self.get_message("admin_defeated")

    def trigger_overheating(self) -> str:
        """Trigger overheating message."""
        return self.get_message("overheating")

    def trigger_gateway_approach(self) -> str:
        """Trigger gateway approach message."""
        return self.get_message("gateway_approach")

    def trigger_random_atmospheric(self, chance: float = 0.15) -> str:
        """
        Trigger random atmospheric message with probability.

        Args:
            chance: Probability of triggering (0.0 to 1.0)

        Returns:
            Message string, or empty if roll failed
        """
        if random.random() < chance:
            return self.get_message("random_atmospheric")
        return ""
