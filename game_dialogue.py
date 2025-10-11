#!/usr/bin/env python3
"""
Dialogue system for popup warnings and confirmations.
Provides a unified, reusable system for all game dialogues including overclock warnings,
inventory attack warnings, and future confirmations.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple


class DialoguePriority(Enum):
    """Priority levels for dialogue queuing and display."""
    LOW = 0      # Informational messages
    MEDIUM = 1   # Warnings (overclock)
    HIGH = 2     # Urgent warnings (under attack)
    CRITICAL = 3 # Game-ending confirmations


class DialogueType(Enum):
    """Types of dialogues that can be displayed."""
    OVERCLOCK_WARNING = "overclock"          # Exploit use over heat capacity
    INVENTORY_ATTACK = "inventory_attack"    # Attacked while in inventory
    # Future types can be added here:
    # GATEWAY_CONFIRM = "gateway"
    # SAVE_OVERWRITE = "save_overwrite"
    # QUIT_CONFIRM = "quit_confirm"


@dataclass
class DialogueConfig:
    """Configuration for a specific dialogue type."""
    title: str                                      # e.g., "OVERCLOCK WARNING"
    message: str                                    # Main message text (supports .format() with context data)
    options: List[str]                              # e.g., ["[Y] Confirm", "[N] Cancel"]
    default_action: str                             # Which option is selected by default
    color_scheme: Dict[str, Tuple[int, int, int]]  # Colors for different parts
    requires_confirmation: bool                     # If False, just shows info (press any key)
    can_dismiss: bool                               # Can player press ESC to dismiss?
    priority: DialoguePriority                      # Priority level for queuing
    blocks_movement: bool                           # If True, movement keys are ignored while dialogue active
    has_dont_show_option: bool                      # If True, includes "Don't show this again" checkbox
    user_pref_key: Optional[str]                    # Key in user_settings.json for "don't show" preference


class DialogueManager:
    """
    Manages all game dialogues and warnings.

    Handles dialogue display, queuing, priority management, and user preferences.
    Dialogues are shown one at a time, with higher priority dialogues taking precedence.
    """

    def __init__(self, settings):
        """
        Initialize the dialogue manager.

        Args:
            settings: GameSettings instance for accessing and saving user preferences
        """
        self.active_dialogue: Optional[DialogueType] = None
        self.dialogue_data: Dict[str, Any] = {}  # Context data for current dialogue
        self.dialogue_configs: Dict[DialogueType, DialogueConfig] = {}
        self.dialogue_queue: List[Tuple[DialogueType, Dict[str, Any]]] = []  # Priority-sorted queue
        self.settings = settings  # Reference to GameSettings for "don't show" preferences
        self._register_default_dialogues()

    def _register_default_dialogues(self):
        """Register all default dialogue configurations."""
        # Import Colors here to avoid circular imports
        from game_entities import Colors

        # Overclock warning dialogue
        # Shows exact damage calculation to help player make informed decision
        self.dialogue_configs[DialogueType.OVERCLOCK_WARNING] = DialogueConfig(
            title="*** OVERCLOCK WARNING ***",
            message="Using {exploit_name} will exceed heat capacity by {overheat_amount}. You will take {damage} CPU damage. Remaining CPU: {remaining_cpu}/{max_cpu}",
            options=["[Y] Use exploit anyway", "[N] Cancel", "[D] Don't show again"],
            default_action="N",
            color_scheme={
                "title": Colors.RED,
                "message": Colors.YELLOW,
                "border": Colors.RED,
                "background": (30, 0, 0),
            },
            requires_confirmation=True,
            can_dismiss=True,
            priority=DialoguePriority.MEDIUM,
            blocks_movement=True,
            has_dont_show_option=True,
            user_pref_key="show_overclock_warning"
        )

        # Inventory attack warning dialogue
        # Critical warning shown when player takes damage while in inventory
        self.dialogue_configs[DialogueType.INVENTORY_ATTACK] = DialogueConfig(
            title="*** UNDER ATTACK ***",
            message="Enemies are attacking! Close inventory immediately!",
            options=["[ESC] Close Inventory"],
            default_action="ESC",
            color_scheme={
                "title": Colors.RED,
                "message": Colors.BRIGHT_RED,
                "border": Colors.RED,
                "background": (30, 0, 0),
            },
            requires_confirmation=False,
            can_dismiss=True,
            priority=DialoguePriority.HIGH,
            blocks_movement=True,
            has_dont_show_option=False,
            user_pref_key=None
        )

    def show_dialogue(self, dialogue_type: DialogueType, **context_data):
        """
        Show a dialogue to the player.

        Checks user preferences and handles queuing based on priority.
        If a dialogue is already active, the new dialogue is added to the priority queue.

        Args:
            dialogue_type: Type of dialogue to show
            **context_data: Context data for formatting the dialogue message
        """
        config = self.dialogue_configs.get(dialogue_type)
        if not config:
            logging.warning(f"Attempted to show unregistered dialogue type: {dialogue_type}")
            return

        # Check if user has disabled this dialogue type
        if config.user_pref_key:
            dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
            if not dialogue_prefs.get(config.user_pref_key, True):
                # User has disabled this dialogue, don't show it
                return

        # If a dialogue is already active, add to queue based on priority
        if self.active_dialogue:
            self._queue_dialogue(dialogue_type, context_data)
            return

        # Show dialogue immediately
        self.active_dialogue = dialogue_type
        self.dialogue_data = context_data

    def _queue_dialogue(self, dialogue_type: DialogueType, context_data: Dict[str, Any]):
        """
        Add dialogue to priority queue.

        Dialogues are inserted based on priority, with higher priority dialogues
        appearing earlier in the queue.

        Args:
            dialogue_type: Type of dialogue to queue
            context_data: Context data for the dialogue
        """
        new_priority = self.dialogue_configs[dialogue_type].priority

        # Insert into queue based on priority (higher priority = closer to front)
        inserted = False
        for i, (queued_type, _) in enumerate(self.dialogue_queue):
            queued_priority = self.dialogue_configs[queued_type].priority
            if new_priority.value > queued_priority.value:
                self.dialogue_queue.insert(i, (dialogue_type, context_data))
                inserted = True
                break

        # If not inserted yet, append to end
        if not inserted:
            self.dialogue_queue.append((dialogue_type, context_data))

    def _show_next_queued_dialogue(self):
        """
        Show the next dialogue from the queue if available.

        Called automatically when the current dialogue is closed.
        """
        if self.dialogue_queue:
            next_type, next_data = self.dialogue_queue.pop(0)
            self.active_dialogue = next_type
            self.dialogue_data = next_data

    def handle_input(self, key) -> Optional[str]:
        """
        Handle player input for active dialogue.

        Args:
            key: Key code from tcod.event

        Returns:
            Action to take: "confirm", "cancel", "dismiss", "dont_show_again", or None
        """
        if not self.active_dialogue:
            return None

        # Import tcod here to avoid circular imports
        import tcod.event

        config = self.dialogue_configs[self.active_dialogue]

        # Handle ESC key
        if key == tcod.event.K_ESCAPE and config.can_dismiss:
            return "dismiss"

        # Handle confirmation dialogues
        if config.requires_confirmation:
            if key == tcod.event.K_y:
                return "confirm"
            elif key == tcod.event.K_n:
                return "cancel"
            elif key == tcod.event.K_d and config.has_dont_show_option:
                return "dont_show_again"
        else:
            # Info-only dialogue - any key closes it
            if key == tcod.event.K_ESCAPE:
                return "dismiss"

        return None

    def close_dialogue(self):
        """
        Close the current dialogue and show next queued dialogue if any.

        Clears the active dialogue state and automatically shows the next
        queued dialogue if one exists.
        """
        self.active_dialogue = None
        self.dialogue_data = {}

        # Show next queued dialogue if available
        self._show_next_queued_dialogue()

    def disable_dialogue(self, dialogue_type: DialogueType):
        """
        Disable a dialogue type by saving preference to user settings.

        Updates the user settings immediately and persists to disk.

        Args:
            dialogue_type: Type of dialogue to disable
        """
        config = self.dialogue_configs.get(dialogue_type)
        if config and config.user_pref_key:
            # Ensure dialogue_preferences dict exists
            if not hasattr(self.settings, 'dialogue_preferences'):
                self.settings.dialogue_preferences = {}

            # Set preference to False (disabled)
            self.settings.dialogue_preferences[config.user_pref_key] = False

            # Save settings immediately to persist the change
            self.settings.save_settings()

            logging.info(f"Disabled dialogue type: {dialogue_type.value}")

    def is_active(self) -> bool:
        """
        Check if a dialogue is currently active.

        Returns:
            True if a dialogue is currently being displayed
        """
        return self.active_dialogue is not None

    def get_active_config(self) -> Optional[DialogueConfig]:
        """
        Get configuration for currently active dialogue.

        Returns:
            DialogueConfig for active dialogue, or None if no dialogue is active
        """
        if self.active_dialogue:
            return self.dialogue_configs[self.active_dialogue]
        return None
