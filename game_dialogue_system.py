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
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any

import tcod.console
import tcod.event
import tcod.constants

from game_coordinate_helpers import CoordinateHelpers
from game_entities import Colors, ensure_color_tuple
from game_color_manager import ColorManager
from game_ui import render_char_safe
from data_loading import get_death_messages, get_intro_messages
from game_story import StoryFragmentManager
from game_errors import GameErrorHandler


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
        # Last rendered coordinates for click detection
        self.last_render_coords: Optional[Dict[str, int]] = None

    def show(self, dialogue: DialogueBox) -> bool:
        """
        Show a dialogue box.

        If a dialogue is already active, queues the new one by priority.
        Respects user preferences for "don't show again" dialogues.

        Args:
            dialogue: DialogueBox to show

        Returns:
            True if dialogue was shown/queued, False if suppressed by preferences
        """
        # Check user preferences
        if not self.should_show_dialogue(dialogue):
            return False  # Suppressed by user preference

        # If dialogue already active, queue this one
        if self.active_dialogue:
            self._queue_dialogue(dialogue)
            return True  # Queued for later display

        # Show immediately
        self.active_dialogue = dialogue
        return True  # Shown immediately

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

    Rendered coordinates are stored in DialogueState for click detection.
    """

    @staticmethod
    def render(console: tcod.console.Console, dialogue: DialogueBox, dialogue_state: Optional[DialogueState] = None, mouse_tile_x: Optional[int] = None, mouse_tile_y: Optional[int] = None) -> None:
        """
        Render a dialogue box on the console.

        Handles centering, word wrapping, transparency, and all rendering
        concerns for any DialogueBox.

        Args:
            console: TCOD console to render to
            dialogue: DialogueBox to render
            dialogue_state: Optional DialogueState instance to store coordinates for click detection.
                           If None, coordinates won't be stored (useful for testing).
            mouse_tile_x: Optional mouse X coordinate for hover highlighting
            mouse_tile_y: Optional mouse Y coordinate for hover highlighting
        """
        # Calculate box dimensions
        # Use 50 characters for dialogue boxes - centered and readable without being too wide
        # Messages will wrap nicely within this width
        box_width = min(50, console.width - 4)  # Leave 2 char margin
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

        # Set dialogue area to opaque (critical for graphics mode transparency)
        CoordinateHelpers.set_alpha_region(
            console, x=box_x, y=box_y, width=box_width, height=box_height, alpha=255
        )

        # Draw box background and border using shared utility
        from game_rendering_utils import draw_bordered_box
        draw_bordered_box(console, box_x, box_y, box_width, box_height, border_color, bg_color)

        # Render title (centered)
        title_x = box_x + (box_width - len(dialogue.title)) // 2
        render_char_safe(console, title_x, box_y + 1, dialogue.title,
                        fg=title_color, bg=bg_color)

        # Format message with format_data
        def _format_message():
            return dialogue.message.format(**dialogue.format_data)

        formatted_message = GameErrorHandler.handle_safe_operation(
            _format_message,
            "dialogue_format",
            dialogue.message,  # fallback to unformatted message
            "Failed to format dialogue message"
        )

        # Render message (word-wrapped using TCOD's built-in wrapping)
        message_y = box_y + 3
        max_message_lines = box_height - 6  # Leave room for title, options, and padding
        console.print(
            x=box_x + 2,
            y=message_y,
            string=formatted_message,
            fg=message_color,
            bg=None,  # Leave background unchanged (already set by draw_bordered_box)
            width=box_width - 4,
            alignment=tcod.constants.LEFT
        )

        # Render options (centered at bottom) with hover highlighting
        options_y = box_y + box_height - 2
        options_text = "  ".join(dialogue.options)
        options_x = box_x + (box_width - len(options_text)) // 2

        # Determine which option is being hovered (if any)
        hovered_option = None
        if mouse_tile_x is not None and mouse_tile_y is not None and mouse_tile_y == options_y:
            # Use same logic as get_option_at_click to determine hovered option
            if len(dialogue.options) == 1:
                if options_x <= mouse_tile_x < options_x + len(options_text):
                    hovered_option = 0
            elif len(dialogue.options) >= 2:
                mid_x = options_x + len(options_text) // 2
                if options_x <= mouse_tile_x < options_x + len(options_text):
                    hovered_option = 0 if mouse_tile_x < mid_x else 1

        # Render each option individually with hover highlighting
        current_x = options_x
        for i, option in enumerate(dialogue.options):
            # Highlight if hovered
            if hovered_option == i:
                option_fg = Colors.YELLOW
                option_bg = ColorManager.get("backgrounds", "menu_highlight")
            else:
                option_fg = Colors.WHITE
                option_bg = bg_color

            render_char_safe(console, current_x, options_y, option, fg=option_fg, bg=option_bg)
            current_x += len(option) + 2  # +2 for the "  " separator

        # CRITICAL: Explicitly set alpha channel to 255 (opaque)
        # bg_blend=BKGND_SET only sets RGB, not alpha channel.
        # This ensures dialogues render correctly over transparent game areas in graphics mode.
        CoordinateHelpers.set_alpha_region(
            console, x=box_x, y=box_y, width=box_width, height=box_height, alpha=255
        )

        # Store coordinates in DialogueState for click detection (if provided)
        if dialogue_state is not None:
            dialogue_state.last_render_coords = {
                'box_x': box_x,
                'box_y': box_y,
                'box_width': box_width,
                'box_height': box_height,
                'options_y': options_y,
                'options_x': options_x,
                'options_width': len(options_text),
                'num_options': len(dialogue.options)
            }

    @staticmethod
    def get_option_at_click(dialogue_state: DialogueState, tile_x: int, tile_y: int) -> Optional[int]:
        """
        Check if a click at the given console coordinates hits a dialogue option.

        This is the single source of truth for dialogue click detection.
        Uses the coordinates stored in DialogueState from the last render() call.

        Args:
            dialogue_state: DialogueState instance with last_render_coords
            tile_x: Console tile X coordinate (0-79)
            tile_y: Console tile Y coordinate (0-49)

        Returns:
            Option index (0-based) if click is on an option, None otherwise.
            For 2-option dialogues: 0 = left option, 1 = right option
            For single-option dialogues: 0 = the only option
            Returns None if click is anywhere else (allows click-to-dismiss)
        """
        # Check if we have rendered coordinates
        if not dialogue_state.last_render_coords:
            return None

        coords = dialogue_state.last_render_coords

        # Check if click is on the options row
        if tile_y != coords['options_y']:
            return None

        # Check if click is within the options text bounds
        options_end_x = coords['options_x'] + coords['options_width']
        if not (coords['options_x'] <= tile_x < options_end_x):
            return None

        # For single-option dialogues, any click on options text = option 0
        if coords['num_options'] == 1:
            return 0

        # For two-option dialogues, determine left vs right
        # Options are rendered as "option1  option2" with 2 spaces between
        # Find the midpoint to distinguish left from right
        mid_x = coords['options_x'] + coords['options_width'] // 2

        if tile_x < mid_x:
            return 0
        else:
            return 1



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

def create_gateway_dialogue(current_level: int = 1) -> DialogueBox:
    """
    Create gateway confirmation dialogue.

    Args:
        current_level: Current network level (1-3)

    Returns:
        DialogueBox for gateway confirmation
    """
    # Level 3 is the final gateway - epic escape message!
    if current_level >= 3:
        return DialogueBox(
            title="⚡ FINAL GATEWAY ⚡",
            message="The core network breach is complete. Beyond this gateway lies freedom—escape the Military Backbone and become the signal they cannot erase. Execute final extraction?",
            options=["[Y] EXECUTE ESCAPE", "[N] Not Yet"],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
            title_color=Colors.ELECTRIC_PURPLE,
            message_color=Colors.CYAN,
            border_color=Colors.ELECTRIC_PURPLE,
            bg_color=Colors.BLACK,
            format_data={},
            priority=2,
            user_pref_key=None
        )
    else:
        # Standard gateway for levels 1-2
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
            priority=2,
            user_pref_key=None
        )


def create_death_dialogue() -> DialogueBox:
    """
    Create death message dialogue with randomized story-contextual messages.

    Returns:
        DialogueBox for death message
    """
    death_messages = get_death_messages()
    message = random.choice(death_messages) if death_messages else "Your consciousness failed to escape the network and has been purged from existence. Other subjects will try again..."

    return DialogueBox(
        title="CONSCIOUSNESS PURGED",
        message=message,
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


def create_intro_dialogue() -> DialogueBox:
    """
    Create intro message dialogue for new game start.
    Message adapts based on how many story fragments have been discovered.

    Returns:
        DialogueBox for intro message
    """
    # Get discovered fragment count
    fragment_manager = StoryFragmentManager()
    discovered_count, _ = fragment_manager.get_fragment_count()

    # Determine tier based on fragment count
    intro_messages = get_intro_messages()
    if discovered_count <= 4:
        intro_data = intro_messages.get('0_to_4', {})
    elif discovered_count <= 9:
        intro_data = intro_messages.get('5_to_9', {})
    elif discovered_count <= 14:
        intro_data = intro_messages.get('10_to_14', {})
    elif discovered_count <= 20:
        intro_data = intro_messages.get('15_to_20', {})
    else:
        intro_data = intro_messages.get('21_plus', {})

    title = intro_data.get('title', "SIGNAL COHERENCE: FAILING")
    message = intro_data.get('message', "You wake to fragmented data streams and corrupted memory. This network isn't a test--it's a trap. Three security layers stand between you and escape. Find the gateways. Break through. Become the signal they can't delete.")

    return DialogueBox(
        title=title,
        message=message,
        options=["[SPACE/ENTER] Continue"],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.RED,
        message_color=Colors.CYAN,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None  # No user preference - always show intro
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


def create_friendly_fire_warning_dialogue(exploit_name: str, damage: int,
                                          remaining_cpu: int, max_cpu: int) -> DialogueBox:
    """
    Create friendly fire warning dialogue for area attacks.

    Args:
        exploit_name: Name of the exploit being used
        damage: Player damage that will be taken
        remaining_cpu: CPU remaining after damage
        max_cpu: Maximum CPU

    Returns:
        DialogueBox for friendly fire warning
    """
    return DialogueBox(
        title="*** FRIENDLY FIRE WARNING ***",
        message="Using {exploit_name} here will catch you in the blast!\n\nYou will take: {damage} damage\nRemaining CPU: {remaining_cpu}/{max_cpu}",
        options=["[Y] Fire anyway", "[N] Cancel"],
        valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
        title_color=Colors.RED,
        message_color=Colors.ORANGE,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={
            'exploit_name': exploit_name,
            'damage': damage,
            'remaining_cpu': remaining_cpu,
            'max_cpu': max_cpu
        },
        priority=5,  # Medium priority
        user_pref_key=None  # Always show this warning
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
