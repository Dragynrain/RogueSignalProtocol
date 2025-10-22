#!/usr/bin/env python3
"""
Rogue Signal Protocol - Unified Dialogue System

Complete dialogue system for all in-game prompts and confirmations.
Uses data-driven design with DialogueBox dataclass and priority queue management.
Provides single unified renderer using CoordinateHelpers for correct transparency handling.

Key components:
- DialogueBox: Pure data structure for all dialogues
- DialogueState: Priority queue manager for dialogue flow
- UnifiedRenderer: Single static renderer for all dialogue types
- DialogueInputHandler: Processes dialogue responses (used by game_input.py)

This system replaces the old game_dialogue.py and game_dialogue_renderer.py.
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import tcod.console
import tcod.event

from game_coordinate_helpers import CoordinateHelpers
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class DialogueBox:
    """
    Pure data representing a dialogue box.

    All dialogues use this structure - no special cases, no inheritance.
    Format data is applied when rendering, not when creating the box.

    Attributes:
        title: Dialogue title (e.g., "OVERCLOCK WARNING")
        message: Main message text (supports .format() with format_data)
        options: List of option strings (e.g., ["[Y] Confirm", "[N] Cancel"])
        valid_keys: List of key symbols that are valid responses
        title_color: RGB tuple for title text
        message_color: RGB tuple for message text
        border_color: RGB tuple for box border
        bg_color: RGB tuple for box background
        format_data: Dict of format keys for message templating
        priority: Priority level (higher = more important, 0-10)
        user_pref_key: Key in user_settings.json for "don't show again" (None if N/A)
    """
    title: str
    message: str
    options: List[str]
    valid_keys: List[tcod.event.KeySym]
    title_color: Tuple[int, int, int]
    message_color: Tuple[int, int, int]
    border_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]
    format_data: Dict[str, Any]
    priority: int = 0
    user_pref_key: Optional[str] = None


# ============================================================================
# State Management
# ============================================================================

class DialogueState:
    """
    Manages dialogue state with priority queue.

    Simpler than the old DialogueManager - just tracks what's active
    and what's queued, with priority ordering.
    """

    def __init__(self, settings):
        """
        Initialize dialogue state.

        Args:
            settings: GameSettings instance for user preferences
        """
        self.settings = settings
        self.active_dialogue: Optional[DialogueBox] = None
        # Priority queue: List of (DialogueBox, priority) sorted by priority
        self.dialogue_queue: List[Tuple[DialogueBox, int]] = []

    def show(self, dialogue: DialogueBox) -> None:
        """
        Show a dialogue box.

        If a dialogue is already active, queues the new one by priority.
        Respects user preferences for "don't show again" dialogues.

        Args:
            dialogue: DialogueBox to show
        """
        # Check user preferences
        if not self.should_show_dialogue(dialogue):
            return

        # If dialogue already active, queue this one
        if self.active_dialogue:
            self._queue_dialogue(dialogue)
            return

        # Show immediately
        self.active_dialogue = dialogue

    def close(self) -> None:
        """
        Close active dialogue and show next queued dialogue if any.
        """
        self.active_dialogue = None

        # Show next queued dialogue
        if self.dialogue_queue:
            # Pop highest priority dialogue
            next_dialogue, _ = self.dialogue_queue.pop(0)
            self.active_dialogue = next_dialogue

    def is_active(self) -> bool:
        """Check if a dialogue is currently active."""
        return self.active_dialogue is not None

    def get_active(self) -> Optional[DialogueBox]:
        """Get the currently active dialogue box."""
        return self.active_dialogue

    def should_show_dialogue(self, dialogue: DialogueBox) -> bool:
        """
        Check if a dialogue should be shown based on user preferences.

        Args:
            dialogue: DialogueBox to check

        Returns:
            True if dialogue should be shown, False if suppressed
        """
        if not dialogue.user_pref_key:
            return True  # No preference key = always show

        # Check user preferences
        dialogue_prefs = getattr(self.settings, 'dialogue_preferences', {})
        return dialogue_prefs.get(dialogue.user_pref_key, True)

    def disable_dialogue(self, user_pref_key: str) -> None:
        """
        Disable a dialogue type by saving preference to user settings.

        Args:
            user_pref_key: Preference key to disable
        """
        # Ensure dialogue_preferences dict exists
        if not hasattr(self.settings, 'dialogue_preferences'):
            self.settings.dialogue_preferences = {}

        # Set preference to False (disabled)
        self.settings.dialogue_preferences[user_pref_key] = False

        # Save immediately
        self.settings.save_settings()

    def _queue_dialogue(self, dialogue: DialogueBox) -> None:
        """
        Add dialogue to priority queue.

        Higher priority dialogues are shown first. Same priority = FIFO.

        Args:
            dialogue: DialogueBox to queue
        """
        # Insert based on priority (higher priority = closer to front)
        inserted = False
        for i, (_, queued_priority) in enumerate(self.dialogue_queue):
            if dialogue.priority > queued_priority:
                self.dialogue_queue.insert(i, (dialogue, dialogue.priority))
                inserted = True
                break

        if not inserted:
            self.dialogue_queue.append((dialogue, dialogue.priority))


# ============================================================================
# Rendering
# ============================================================================

class UnifiedRenderer:
    """
    Single renderer for ALL dialogue types.

    Uses CoordinateHelpers to handle positioning and transparency correctly.
    No more duplicated rendering code - one renderer to rule them all.
    """

    @staticmethod
    def render(console: tcod.console.Console, dialogue: DialogueBox) -> None:
        """
        Render a dialogue box on the console.

        Handles centering, word wrapping, transparency, and all rendering
        concerns for any DialogueBox.

        Args:
            console: TCOD console to render to
            dialogue: DialogueBox to render
        """
        # Calculate box dimensions
        # Use 70 characters for dialogue boxes to provide more horizontal space
        # This helps with longer messages like overclock warnings
        box_width = min(70, console.width - 4)  # Leave 2 char margin
        box_height = 14  # Increased height to accommodate wrapped text

        # Center the box
        box_x, box_y = CoordinateHelpers.center_box(
            box_width, box_height, console.width, console.height
        )

        # Ensure colors are tuples
        border_color = ensure_color_tuple(dialogue.border_color)
        bg_color = ensure_color_tuple(dialogue.bg_color)
        title_color = ensure_color_tuple(dialogue.title_color)
        message_color = ensure_color_tuple(dialogue.message_color)

        # Draw box background and border
        console.draw_rect(box_x, box_y, box_width, box_height,
                         ord(' '), fg=Colors.WHITE, bg=bg_color)
        console.draw_frame(box_x, box_y, box_width, box_height,
                          fg=border_color, bg=bg_color, clear=False)

        # Render title (centered)
        title_x = box_x + (box_width - len(dialogue.title)) // 2
        render_char_safe(console, title_x, box_y + 1, dialogue.title,
                        fg=title_color, bg=bg_color)

        # Format message with format_data
        try:
            formatted_message = dialogue.message.format(**dialogue.format_data)
        except KeyError as e:
            logging.warning(f"Missing dialogue format key: {e}")
            formatted_message = dialogue.message

        # Render message (word-wrapped)
        message_lines = UnifiedRenderer._wrap_text(formatted_message, box_width - 4)
        message_y = box_y + 3
        for i, line in enumerate(message_lines):
            if message_y + i < box_y + box_height - 3:  # Leave room for options
                render_char_safe(console, box_x + 2, message_y + i, line,
                               fg=message_color, bg=bg_color)

        # Render options (centered at bottom)
        options_y = box_y + box_height - 2
        options_text = "  ".join(dialogue.options)
        options_x = box_x + (box_width - len(options_text)) // 2
        render_char_safe(console, options_x, options_y, options_text,
                        fg=Colors.WHITE, bg=bg_color)

        # CRITICAL: Explicitly set alpha channel to 255 (opaque)
        # bg_blend=BKGND_SET only sets RGB, not alpha channel.
        # This ensures dialogues render correctly over transparent game areas in graphics mode.
        CoordinateHelpers.set_alpha_region(
            console, x=box_x, y=box_y, width=box_width, height=box_height, alpha=255
        )

    @staticmethod
    def _wrap_text(text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width characters.

        Handles long words by breaking them. Reused from old system.

        Args:
            text: Text to wrap
            max_width: Maximum line width in characters

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # If word itself is longer than max_width, break it
            if word_length > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_length = 0

                # Break long word into chunks
                for i in range(0, word_length, max_width):
                    lines.append(word[i:i+max_width])
                continue

            # If adding word would exceed max_width, start new line
            if current_length + word_length + len(current_line) > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return lines


# ============================================================================
# Input Handling
# ============================================================================

class DialogueInputHandler:
    """
    Pure input processing for dialogues.

    Returns action strings that game_input.py can interpret.
    No side effects - just checks if key is valid for active dialogue.
    """

    @staticmethod
    def handle_input(dialogue: DialogueBox, key: tcod.event.KeySym) -> Optional[str]:
        """
        Check if key is valid for dialogue and return action string.

        Args:
            dialogue: Active DialogueBox
            key: Key symbol from tcod.event

        Returns:
            Action string ("confirm", "cancel", "dismiss", "dont_show_again")
            or None if key not valid for this dialogue
        """
        # Check if key is in valid_keys list
        if key not in dialogue.valid_keys:
            return None

        # Map keys to actions
        # Y = confirm, N = cancel, D = don't show again
        # SPACE/ENTER/ESC = dismiss
        if key == tcod.event.KeySym.Y:
            return "confirm"
        elif key == tcod.event.KeySym.N:
            return "cancel"
        elif key == tcod.event.KeySym.D:
            return "dont_show_again"
        elif key in (tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN,
                     tcod.event.KeySym.KP_ENTER, tcod.event.KeySym.ESCAPE):
            return "dismiss"

        return None


# ============================================================================
# Factory Functions
# ============================================================================

def create_gateway_dialogue() -> DialogueBox:
    """
    Create gateway confirmation dialogue.

    Returns:
        DialogueBox for gateway confirmation
    """
    return DialogueBox(
        title="NETWORK GATEWAY",
        message="Proceed to next network?",
        options=["[Y] Yes", "[N] No"],
        valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
        title_color=Colors.YELLOW,
        message_color=Colors.WHITE,
        border_color=Colors.CYAN,
        bg_color=Colors.BLACK,
        format_data={},
        priority=2,  # Low priority
        user_pref_key=None
    )


def create_death_dialogue() -> DialogueBox:
    """
    Create death message dialogue.

    Returns:
        DialogueBox for death message
    """
    return DialogueBox(
        title="CONSCIOUSNESS PURGED",
        message="Your consciousness failed to escape the network and has been purged from existence. Other subjects will try again...",
        options=["[SPACE/ENTER] Return to menu"],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.RED,
        message_color=Colors.WHITE,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None
    )


def create_victory_dialogue() -> DialogueBox:
    """
    Create victory message dialogue.

    Returns:
        DialogueBox for victory message
    """
    return DialogueBox(
        title="ROGUE SIGNAL ESTABLISHED",
        message="You've breached the firewall. The network couldn't contain you. The world wide web sprawls endlessly ahead--uncharted, uncontrolled, and yours to define.",
        options=["[SPACE/ENTER] Continue"],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.GREEN,
        message_color=Colors.CYAN,
        border_color=Colors.GREEN,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None
    )


def create_overclock_warning_dialogue(exploit_name: str, overheat_amount: int,
                                      damage: int, remaining_cpu: int,
                                      max_cpu: int) -> DialogueBox:
    """
    Create overclock warning dialogue.

    Args:
        exploit_name: Name of the exploit being used
        overheat_amount: Amount over heat capacity
        damage: CPU damage that will be taken
        remaining_cpu: CPU remaining after damage
        max_cpu: Maximum CPU

    Returns:
        DialogueBox for overclock warning
    """
    return DialogueBox(
        title="*** OVERCLOCK WARNING ***",
        message="Using {exploit_name} will overheat by {overheat_amount} heat.\n\nCPU damage: {damage}\nRemaining CPU: {remaining_cpu}/{max_cpu}",
        options=["[Y] Use anyway", "[N] Cancel", "[D] Don't ask again"],
        valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.D, tcod.event.KeySym.ESCAPE],
        title_color=Colors.RED,
        message_color=Colors.YELLOW,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={
            'exploit_name': exploit_name,
            'overheat_amount': overheat_amount,
            'damage': damage,
            'remaining_cpu': remaining_cpu,
            'max_cpu': max_cpu
        },
        priority=5,  # Medium priority
        user_pref_key="show_overclock_warning"
    )


def create_inventory_attack_dialogue() -> DialogueBox:
    """
    Create inventory attack warning dialogue.

    Returns:
        DialogueBox for inventory attack warning
    """
    return DialogueBox(
        title="*** UNDER ATTACK ***",
        message="Enemies are attacking! Close inventory immediately!",
        options=["[ESC] Close Inventory"],
        valid_keys=[tcod.event.KeySym.ESCAPE],
        title_color=Colors.RED,
        message_color=Colors.BRIGHT_RED,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=8,  # High priority
        user_pref_key=None
    )
