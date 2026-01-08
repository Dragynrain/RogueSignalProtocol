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

import random
from dataclasses import dataclass
from typing import Any

import tcod.console
import tcod.constants
import tcod.event

from rsp.core.data_loading import get_death_messages, get_intro_messages
from rsp.core.errors import GameErrorHandler
from rsp.entities.base import Colors, ensure_color_tuple
from rsp.rendering.coordinates import CoordinateHelpers
from rsp.ui.common import render_char_safe
from rsp.utils.colors import ColorManager
from rsp.utils.story import StoryFragmentManager

# ============================================================================
# Constants
# ============================================================================

# Dialogue box dimensions
DIALOGUE_BOX_HEIGHT = 14  # Height to accommodate wrapped text

# Story progression tiers (fragment count thresholds)
STORY_TIER_BEGINNER = 4  # 0-4 fragments
STORY_TIER_NOVICE = 9  # 5-9 fragments
STORY_TIER_INTERMEDIATE = 14  # 10-14 fragments
STORY_TIER_ADVANCED = 20  # 15-20 fragments
# 21+ is STORY_TIER_MASTER (implicit)

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
    options: list[str]
    valid_keys: list[tcod.event.KeySym]
    title_color: tuple[int, int, int]
    message_color: tuple[int, int, int]
    border_color: tuple[int, int, int]
    bg_color: tuple[int, int, int]
    format_data: dict[str, Any]
    priority: int = 0
    user_pref_key: str | None = None


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
        self.active_dialogue: DialogueBox | None = None
        # Priority queue: List of (DialogueBox, priority) sorted by priority
        self.dialogue_queue: list[tuple[DialogueBox, int]] = []
        # Last rendered coordinates for click detection
        self.last_render_coords: dict[str, int] | None = None

    def show(self, dialogue: DialogueBox) -> bool:
        """
        Show a dialogue box.

        If a dialogue is already active, queues the new one by priority.
        Higher priority dialogues interrupt lower priority ones.
        Respects user preferences for "don't show again" dialogues.

        Args:
            dialogue: DialogueBox to show

        Returns:
            True if dialogue was shown/queued, False if suppressed by preferences
        """
        # Check user preferences
        if not self.should_show_dialogue(dialogue):
            return False  # Suppressed by user preference

        # If dialogue already active, check priority
        if self.active_dialogue:
            # Higher priority dialogues interrupt lower priority ones
            if dialogue.priority > self.active_dialogue.priority:
                # Queue the currently active dialogue
                self._queue_dialogue(self.active_dialogue)
                # Show the high-priority dialogue immediately
                self.active_dialogue = dialogue
                return True  # Interrupted and shown immediately
            else:
                # Queue this dialogue (same or lower priority)
                self._queue_dialogue(dialogue)
                return True  # Queued for later display

        # Show immediately (no active dialogue)
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

    def get_active(self) -> DialogueBox | None:
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
        dialogue_prefs = getattr(self.settings, "dialogue_preferences", {})
        return dialogue_prefs.get(dialogue.user_pref_key, True)

    def disable_dialogue(self, user_pref_key: str) -> None:
        """
        Disable a dialogue type by saving preference to user settings.

        Args:
            user_pref_key: Preference key to disable
        """
        # Ensure dialogue_preferences dict exists
        if not hasattr(self.settings, "dialogue_preferences"):
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
    def render(
        console: tcod.console.Console,
        dialogue: DialogueBox,
        dialogue_state: DialogueState | None = None,
        mouse_tile_x: int | None = None,
        mouse_tile_y: int | None = None,
    ) -> None:
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
        box_height = DIALOGUE_BOX_HEIGHT  # Increased height to accommodate wrapped text

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
        from rsp.rendering.utils import draw_bordered_box

        draw_bordered_box(console, box_x, box_y, box_width, box_height, border_color, bg_color)

        # Render title (centered, ensure x doesn't go negative if title is too long)
        title_x = max(box_x + 1, box_x + (box_width - len(dialogue.title)) // 2)
        render_char_safe(console, title_x, box_y + 1, dialogue.title, fg=title_color, bg=bg_color)

        # Format message with format_data
        def _format_message():
            return dialogue.message.format(**dialogue.format_data)

        formatted_message = GameErrorHandler.handle_safe_operation(
            _format_message,
            "dialogue_format",
            dialogue.message,  # fallback to unformatted message
            "Failed to format dialogue message",
        )

        # Render message (word-wrapped using TCOD's built-in wrapping)
        message_y = box_y + 3
        console.print(
            x=box_x + 2,
            y=message_y,
            string=formatted_message,
            fg=message_color,
            bg=None,  # Leave background unchanged (already set by draw_bordered_box)
            width=box_width - 4,
            alignment=tcod.constants.LEFT,
        )

        # Render options (centered at bottom) with hover highlighting
        options_y = box_y + box_height - 2
        options_text = "  ".join(dialogue.options)
        options_x = box_x + (box_width - len(options_text)) // 2

        # Determine which option is being hovered (if any)
        hovered_option = None
        if mouse_tile_x is not None and mouse_tile_y is not None and mouse_tile_y == options_y:
            # Calculate actual rendered position for each option
            # Options are rendered with 2-char separator between them
            option_x = options_x
            for i, option in enumerate(dialogue.options):
                option_end_x = option_x + len(option)
                if option_x <= mouse_tile_x < option_end_x:
                    hovered_option = i
                    break
                option_x = option_end_x + 2  # +2 for "  " separator

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
                "box_x": box_x,
                "box_y": box_y,
                "box_width": box_width,
                "box_height": box_height,
                "options_y": options_y,
                "options_x": options_x,
                "options_width": len(options_text),
                "num_options": len(dialogue.options),
            }

    @staticmethod
    def get_option_at_click(dialogue_state: DialogueState, tile_x: int, tile_y: int) -> int | None:
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
        if tile_y != coords["options_y"]:
            return None

        # Check if click is within the options text bounds
        options_end_x = coords["options_x"] + coords["options_width"]
        if not (coords["options_x"] <= tile_x < options_end_x):
            return None

        # For single-option dialogues, any click on options text = option 0
        if coords["num_options"] == 1:
            return 0

        # For two-option dialogues, determine left vs right
        # Options are rendered as "option1  option2" with 2 spaces between
        # Find the midpoint to distinguish left from right
        mid_x = coords["options_x"] + coords["options_width"] // 2

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
    def handle_input(dialogue: DialogueBox, key: tcod.event.KeySym) -> str | None:
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
        elif key in (
            tcod.event.KeySym.SPACE,
            tcod.event.KeySym.RETURN,
            tcod.event.KeySym.KP_ENTER,
            tcod.event.KeySym.ESCAPE,
        ):
            return "dismiss"

        return None


# ============================================================================
# Factory Functions
# ============================================================================


def create_gateway_dialogue(current_level: int = 1, input_mapper=None) -> DialogueBox:
    """
    Create gateway confirmation dialogue.

    Args:
        current_level: Current network level (1-3)
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for gateway confirmation
    """
    from rsp.ui.help_hints import get_dialogue_cancel_option, get_dialogue_confirm_option

    # Level 3 is the final gateway - epic escape message!
    if current_level >= 3:
        return DialogueBox(
            title="FINAL GATEWAY",
            message="The core network breach is complete. Beyond this gateway lies freedom--escape the Military Backbone and become the signal they cannot erase. Execute final extraction?",
            options=[
                get_dialogue_confirm_option("EXECUTE ESCAPE", input_mapper),
                get_dialogue_cancel_option("Not Yet", input_mapper),
            ],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
            title_color=Colors.ELECTRIC_PURPLE,
            message_color=Colors.CYAN,
            border_color=Colors.ELECTRIC_PURPLE,
            bg_color=Colors.BLACK,
            format_data={},
            priority=2,
            user_pref_key=None,
        )
    else:
        # Standard gateway for levels 1-2
        return DialogueBox(
            title="NETWORK GATEWAY",
            message="Proceed to next network?",
            options=[
                get_dialogue_confirm_option("Yes", input_mapper),
                get_dialogue_cancel_option("No", input_mapper),
            ],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
            title_color=Colors.YELLOW,
            message_color=Colors.WHITE,
            border_color=Colors.CYAN,
            bg_color=Colors.BLACK,
            format_data={},
            priority=2,
            user_pref_key=None,
        )


def create_death_dialogue(input_mapper=None) -> DialogueBox:
    """
    Create death message dialogue with randomized story-contextual messages.

    Args:
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for death message
    """
    from rsp.ui.help_hints import get_dialogue_dismiss_option

    death_messages = get_death_messages()
    message = (
        random.choice(death_messages)
        if death_messages
        else "Your consciousness failed to escape the network and has been purged from existence. Other subjects will try again..."
    )

    return DialogueBox(
        title="CONSCIOUSNESS PURGED",
        message=message,
        options=[get_dialogue_dismiss_option("Return to menu", input_mapper)],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.RED,
        message_color=Colors.WHITE,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None,
    )


def create_intro_dialogue(input_mapper=None) -> DialogueBox:
    """
    Create intro message dialogue for new game start.
    Message adapts based on how many story fragments have been discovered.

    Args:
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for intro message
    """
    from rsp.ui.help_hints import get_dialogue_dismiss_option

    # Get discovered fragment count
    fragment_manager = StoryFragmentManager()
    discovered_count, _ = fragment_manager.get_fragment_count()

    # Determine tier based on fragment count
    intro_messages = get_intro_messages()
    if discovered_count <= STORY_TIER_BEGINNER:
        intro_data = intro_messages["0_to_4"]
    elif discovered_count <= STORY_TIER_NOVICE:
        intro_data = intro_messages["5_to_9"]
    elif discovered_count <= STORY_TIER_INTERMEDIATE:
        intro_data = intro_messages["10_to_14"]
    elif discovered_count <= STORY_TIER_ADVANCED:
        intro_data = intro_messages["15_to_20"]
    else:
        intro_data = intro_messages["21_plus"]

    title = intro_data["title"]
    message = intro_data["message"]

    return DialogueBox(
        title=title,
        message=message,
        options=[get_dialogue_dismiss_option("Continue", input_mapper)],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.RED,
        message_color=Colors.CYAN,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None,  # No user preference - always show intro
    )


def create_victory_dialogue(input_mapper=None) -> DialogueBox:
    """
    Create victory message dialogue.

    Args:
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for victory message
    """
    from rsp.ui.help_hints import get_dialogue_dismiss_option

    return DialogueBox(
        title="ROGUE SIGNAL ESTABLISHED",
        message="You've breached the firewall. The network couldn't contain you. The world wide web sprawls endlessly ahead--uncharted, uncontrolled, and yours to define.",
        options=[get_dialogue_dismiss_option("Continue", input_mapper)],
        valid_keys=[tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.GREEN,
        message_color=Colors.CYAN,
        border_color=Colors.GREEN,
        bg_color=Colors.BLACK,
        format_data={},
        priority=10,  # Critical priority
        user_pref_key=None,
    )


def create_prologue_intro_dialogue() -> DialogueBox:
    """Create prologue introduction dialogue (shown when prologue starts)."""
    return DialogueBox(
        title="FIRST INFILTRATION",
        message=(
            "Remote uplink active.\n"
            "Reach the gateway.\n"
            "\n"
            "Arrow keys to move. Period (.) to wait. 1-5 for exploits.\n"
            "Press ? anytime for help."
        ),
        options=["[ENTER] Begin"],
        valid_keys=[tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.CYAN,
        message_color=Colors.WHITE,
        border_color=Colors.CYAN,
        bg_color=(20, 30, 40),
        format_data={},
        priority=5,
    )


def create_prologue_completion_dialogue() -> DialogueBox:
    """Create prologue completion dialogue (returns to main menu)."""
    return DialogueBox(
        title="UPLINK ESTABLISHED",
        message=(
            "Gateway reached. You are ready.\n"
            "\n"
            "The real networks won't be this forgiving. "
            "Stay too long, and something worse than guards will find you."
        ),
        options=["[ENTER] Continue"],
        valid_keys=[tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.GREEN,
        message_color=Colors.WHITE,
        border_color=Colors.GREEN,
        bg_color=(20, 30, 40),
        format_data={},
        priority=5,
    )


def create_prologue_death_dialogue(cause: str, hint: str | None = None) -> DialogueBox:
    """Create prologue death dialogue (restarts training).

    Args:
        cause: Death cause message
        hint: Optional contextual hint for first death in a section
    """
    # Build message with optional hint
    if hint:
        message = f"{cause}\n\n{hint}\n\nRe-establishing uplink... I know more now."
    else:
        message = f"{cause}\n\nRe-establishing uplink... I know more now."

    return DialogueBox(
        title="CONNECTION LOST",
        message=message,
        options=["[ENTER] Retry"],
        valid_keys=[tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER],
        title_color=Colors.YELLOW,
        message_color=Colors.WHITE,
        border_color=Colors.YELLOW,
        bg_color=(40, 30, 20),
        format_data={},
        priority=10,
    )


def create_overclock_warning_dialogue(
    exploit_name: str,
    overheat_amount: int,
    damage: int,
    remaining_cpu: int,
    max_cpu: int,
    input_mapper=None,
) -> DialogueBox:
    """
    Create overclock warning dialogue.

    Args:
        exploit_name: Name of the exploit being used
        overheat_amount: Amount over heat capacity
        damage: CPU damage that will be taken
        remaining_cpu: CPU remaining after damage
        max_cpu: Maximum CPU
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for overclock warning
    """
    from rsp.ui.help_hints import (
        get_dialogue_cancel_option,
        get_dialogue_confirm_option,
        get_dialogue_skip_option,
    )

    return DialogueBox(
        title="*** OVERCLOCK WARNING ***",
        message="Using {exploit_name} will overheat by {overheat_amount} heat.\n\nCPU damage: {damage}\nRemaining CPU: {remaining_cpu}/{max_cpu}",
        options=[
            get_dialogue_confirm_option("Use anyway", input_mapper),
            get_dialogue_cancel_option("Cancel", input_mapper),
            get_dialogue_skip_option("Don't ask again", input_mapper),
        ],
        valid_keys=[
            tcod.event.KeySym.Y,
            tcod.event.KeySym.N,
            tcod.event.KeySym.D,
            tcod.event.KeySym.ESCAPE,
        ],
        title_color=Colors.RED,
        message_color=Colors.YELLOW,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={
            "exploit_name": exploit_name,
            "overheat_amount": overheat_amount,
            "damage": damage,
            "remaining_cpu": remaining_cpu,
            "max_cpu": max_cpu,
        },
        priority=5,  # Medium priority
        user_pref_key="show_overclock_warning",
    )


def create_friendly_fire_warning_dialogue(
    exploit_name: str, damage: int, remaining_cpu: int, max_cpu: int, input_mapper=None
) -> DialogueBox:
    """
    Create friendly fire warning dialogue for area attacks.

    Args:
        exploit_name: Name of the exploit being used
        damage: Player damage that will be taken
        remaining_cpu: CPU remaining after damage
        max_cpu: Maximum CPU
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for friendly fire warning
    """
    from rsp.ui.help_hints import get_dialogue_cancel_option, get_dialogue_confirm_option

    return DialogueBox(
        title="*** FRIENDLY FIRE WARNING ***",
        message="Using {exploit_name} here will catch you in the blast!\n\nYou will take: {damage} damage\nRemaining CPU: {remaining_cpu}/{max_cpu}",
        options=[
            get_dialogue_confirm_option("Fire anyway", input_mapper),
            get_dialogue_cancel_option("Cancel", input_mapper),
        ],
        valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N, tcod.event.KeySym.ESCAPE],
        title_color=Colors.RED,
        message_color=Colors.ORANGE,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={
            "exploit_name": exploit_name,
            "damage": damage,
            "remaining_cpu": remaining_cpu,
            "max_cpu": max_cpu,
        },
        priority=5,  # Medium priority
        user_pref_key=None,  # Always show this warning
    )


def create_system_crash_warning_dialogue(
    damage: int, remaining_cpu: int, max_cpu: int, would_die: bool, input_mapper=None
) -> DialogueBox:
    """
    Create System Crash warning dialogue for self-damage exploit.

    Args:
        damage: Self-damage that will be taken (30)
        remaining_cpu: CPU remaining after damage
        max_cpu: Maximum CPU
        would_die: Whether this would kill the player
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for System Crash warning
    """
    from rsp.ui.help_hints import (
        get_dialogue_cancel_option,
        get_dialogue_confirm_option,
        get_dialogue_skip_option,
    )

    if would_die:
        warning_text = "*** FATAL ERROR ***\n\nSystem Crash will deal {damage} damage to YOU!\n\nThis will KILL you!\n\nYour CPU: {current_cpu}/{max_cpu} -> DEAD"
        title_color = Colors.RED
        border_color = Colors.RED
    else:
        warning_text = "*** SYSTEM CRASH WARNING ***\n\nThis crashes the system YOU'RE ON!\n\nYou will take {damage} CPU damage\nAll enemies in radius 3 will take {damage} damage + 3 turn stun\n\nYour CPU: {current_cpu}/{max_cpu} -> {remaining_cpu}/{max_cpu}"
        title_color = Colors.YELLOW
        border_color = Colors.YELLOW

    return DialogueBox(
        title="!!! SYSTEM CRASH !!!",
        message=warning_text,
        options=[
            get_dialogue_confirm_option("Execute", input_mapper),
            get_dialogue_cancel_option("Cancel", input_mapper),
            get_dialogue_skip_option("Disable", input_mapper),
        ],
        valid_keys=[
            tcod.event.KeySym.Y,
            tcod.event.KeySym.N,
            tcod.event.KeySym.D,
            tcod.event.KeySym.ESCAPE,
        ],
        title_color=title_color,
        message_color=Colors.WHITE,
        border_color=border_color,
        bg_color=Colors.BLACK,
        format_data={
            "damage": damage,
            "remaining_cpu": remaining_cpu,
            "max_cpu": max_cpu,
            "current_cpu": remaining_cpu + damage,
        },
        priority=6,  # Higher priority than overclock (this can kill you!)
        user_pref_key="show_system_crash_warning",
    )


def create_system_crash_overheat_dialogue(
    overheat_damage: int, self_damage: int, current_cpu: int, max_cpu: int, input_mapper=None
) -> DialogueBox:
    """
    Create combined System Crash + overheat warning dialogue.

    Shows when System Crash will cause BOTH overheat damage AND self-damage,
    so player sees accurate total damage in one dialogue.

    Args:
        overheat_damage: CPU damage from overheating
        self_damage: CPU damage from System Crash self-damage (30)
        current_cpu: Current CPU before any damage
        max_cpu: Maximum CPU
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for combined warning
    """
    from rsp.ui.help_hints import (
        get_dialogue_cancel_option,
        get_dialogue_confirm_option,
    )

    total_damage = overheat_damage + self_damage
    final_cpu = current_cpu - total_damage
    would_die = final_cpu <= 0

    if would_die:
        warning_text = (
            "System Crash will OVERHEAT and crash your system!\n\n"
            "Overheat damage: {overheat_damage}\n"
            "Self damage: {self_damage}\n"
            "TOTAL damage: {total_damage}\n\n"
            "This will KILL you!\n"
            "Your CPU: {current_cpu}/{max_cpu} -> DEAD"
        )
        title_color = Colors.RED
        border_color = Colors.RED
    else:
        warning_text = (
            "System Crash will OVERHEAT and crash your system!\n\n"
            "Overheat damage: {overheat_damage}\n"
            "Self damage: {self_damage}\n"
            "TOTAL damage: {total_damage}\n\n"
            "Your CPU: {current_cpu}/{max_cpu} -> {final_cpu}/{max_cpu}"
        )
        title_color = Colors.RED
        border_color = Colors.RED

    return DialogueBox(
        title="!!! CRITICAL WARNING !!!",
        message=warning_text,
        options=[
            get_dialogue_confirm_option("Execute anyway", input_mapper),
            get_dialogue_cancel_option("Cancel", input_mapper),
        ],
        valid_keys=[
            tcod.event.KeySym.Y,
            tcod.event.KeySym.N,
            tcod.event.KeySym.ESCAPE,
        ],
        title_color=title_color,
        message_color=Colors.YELLOW,
        border_color=border_color,
        bg_color=Colors.BLACK,
        format_data={
            "overheat_damage": overheat_damage,
            "self_damage": self_damage,
            "total_damage": total_damage,
            "current_cpu": current_cpu,
            "max_cpu": max_cpu,
            "final_cpu": final_cpu,
        },
        priority=7,  # Highest priority - combined critical warning
        user_pref_key=None,  # Always show - too dangerous to disable
    )


def create_inventory_attack_dialogue(input_mapper=None) -> DialogueBox:
    """
    Create inventory attack warning dialogue.

    Args:
        input_mapper: Optional InputMapper for dynamic button hints

    Returns:
        DialogueBox for inventory attack warning
    """
    from rsp.input.actions import InputAction, InputContext
    from rsp.ui.help_hints import _get_mapper

    m = _get_mapper(input_mapper)
    btn_cancel = m.get_button_hint(InputAction.CANCEL, InputContext.INVENTORY)

    return DialogueBox(
        title="*** UNDER ATTACK ***",
        message="Enemies are attacking! Close inventory immediately!",
        options=[f"[ESC/{btn_cancel}] Close Inventory"],
        valid_keys=[tcod.event.KeySym.ESCAPE],
        title_color=Colors.RED,
        message_color=Colors.BRIGHT_RED,
        border_color=Colors.RED,
        bg_color=Colors.BLACK,
        format_data={},
        priority=8,  # High priority
        user_pref_key=None,
    )
