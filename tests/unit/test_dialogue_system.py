#!/usr/bin/env python3
"""
Unit tests for the unified dialogue system.

Tests DialogueBox creation, DialogueState management, UnifiedRenderer,
DialogueInputHandler, and factory functions.
"""

from unittest.mock import Mock

import tcod.console
import tcod.event

from game_dialogue_system import (
    DialogueBox,
    DialogueInputHandler,
    DialogueState,
    UnifiedRenderer,
    create_death_dialogue,
    create_gateway_dialogue,
    create_intro_dialogue,
    create_inventory_attack_dialogue,
    create_overclock_warning_dialogue,
    create_victory_dialogue,
)
from game_entities import Colors


class TestDialogueBox:
    """Test DialogueBox dataclass."""

    def test_dialogue_box_creation(self):
        """DialogueBox can be created with all required fields."""
        dialogue = DialogueBox(
            title="Test Title",
            message="Test message",
            options=["[Y] Yes", "[N] No"],
            valid_keys=[tcod.event.KeySym.Y, tcod.event.KeySym.N],
            title_color=(255, 255, 0),
            message_color=(255, 255, 255),
            border_color=(0, 255, 255),
            bg_color=(0, 0, 0),
            format_data={"key": "value"},
            priority=5,
            user_pref_key="test_pref",
        )

        assert dialogue.title == "Test Title"
        assert dialogue.message == "Test message"
        assert len(dialogue.options) == 2
        assert len(dialogue.valid_keys) == 2
        assert dialogue.priority == 5
        assert dialogue.user_pref_key == "test_pref"

    def test_dialogue_box_default_priority(self):
        """DialogueBox uses default priority of 0 if not specified."""
        dialogue = DialogueBox(
            title="Test",
            message="Test",
            options=[],
            valid_keys=[],
            title_color=Colors.WHITE,
            message_color=Colors.WHITE,
            border_color=Colors.WHITE,
            bg_color=Colors.BLACK,
            format_data={},
        )

        assert dialogue.priority == 0

    def test_dialogue_box_no_user_pref(self):
        """DialogueBox can have no user preference key."""
        dialogue = DialogueBox(
            title="Test",
            message="Test",
            options=[],
            valid_keys=[],
            title_color=Colors.WHITE,
            message_color=Colors.WHITE,
            border_color=Colors.WHITE,
            bg_color=Colors.BLACK,
            format_data={},
            user_pref_key=None,
        )

        assert dialogue.user_pref_key is None


class TestDialogueState:
    """Test DialogueState manager."""

    def test_dialogue_state_initialization(self):
        """DialogueState initializes with no active dialogue."""
        settings = Mock()
        state = DialogueState(settings)

        assert state.active_dialogue is None
        assert len(state.dialogue_queue) == 0
        assert not state.is_active()

    def test_show_dialogue_immediately(self):
        """show() displays dialogue immediately if none active."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        dialogue = create_gateway_dialogue()
        state.show(dialogue)

        assert state.is_active()
        assert state.get_active() == dialogue

    def test_show_dialogue_queues_if_active(self):
        """show() interrupts with higher priority dialogue."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        dialogue1 = create_gateway_dialogue()  # Priority 2
        dialogue2 = create_death_dialogue()  # Priority 10 (higher)

        state.show(dialogue1)  # Shows immediately
        state.show(dialogue2)  # Interrupts dialogue1 (higher priority)

        # Higher priority dialogue interrupts and shows immediately
        assert state.get_active() == dialogue2
        assert len(state.dialogue_queue) == 1  # dialogue1 queued

    def test_close_dialogue_shows_next_queued(self):
        """close() shows next queued dialogue if available with priority interruption."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        dialogue1 = create_gateway_dialogue()  # Priority 2
        dialogue2 = create_death_dialogue()  # Priority 10 (higher)

        state.show(dialogue1)  # Shows immediately
        state.show(dialogue2)  # Interrupts dialogue1 (higher priority)

        # dialogue2 is active, dialogue1 is queued
        assert state.get_active() == dialogue2

        state.close()  # Close dialogue2

        # Should now show dialogue1 from queue
        assert state.get_active() == dialogue1
        assert len(state.dialogue_queue) == 0

    def test_close_dialogue_with_empty_queue(self):
        """close() clears active dialogue if queue is empty."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        dialogue = create_gateway_dialogue()
        state.show(dialogue)
        state.close()

        assert not state.is_active()
        assert state.get_active() is None

    def test_priority_queue_ordering(self):
        """Dialogues interrupt by priority and queue is ordered (higher = first)."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Create dialogues with different priorities
        low_priority = create_gateway_dialogue()  # priority = 2
        high_priority = create_death_dialogue()  # priority = 10
        med_priority = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)  # priority = 5

        # Show in random order
        state.show(low_priority)  # Shows immediately (priority 2)
        state.show(high_priority)  # Interrupts low_priority (priority 10 > 2)
        state.show(med_priority)  # Queues (priority 5 < 10)

        # Highest priority dialogue interrupts and shows immediately
        assert state.get_active() == high_priority  # Priority 10

        # Close and check queue order: med_priority (5) should come before low_priority (2)
        state.close()
        assert state.get_active() == med_priority  # Priority 5

        state.close()
        assert state.get_active() == low_priority  # Priority 2

        state.close()
        assert not state.is_active()

    def test_should_show_dialogue_respects_preferences(self):
        """should_show_dialogue() respects user preferences."""
        settings = Mock()
        settings.dialogue_preferences = {"show_overclock_warning": False}  # User disabled this
        state = DialogueState(settings)

        # Dialogue with preference key set to False should not show
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        assert not state.should_show_dialogue(dialogue)

        # Dialogue without preference key should always show
        dialogue2 = create_gateway_dialogue()
        assert state.should_show_dialogue(dialogue2)

    def test_show_respects_user_preferences(self):
        """show() respects user preferences and doesn't show disabled dialogues."""
        settings = Mock()
        settings.dialogue_preferences = {"show_overclock_warning": False}
        state = DialogueState(settings)

        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        state.show(dialogue)

        # Should not show or queue
        assert not state.is_active()
        assert len(state.dialogue_queue) == 0

    def test_disable_dialogue(self):
        """disable_dialogue() saves preference to settings."""
        settings = Mock()
        settings.dialogue_preferences = {}
        settings.save_settings = Mock()
        state = DialogueState(settings)

        state.disable_dialogue("show_overclock_warning")

        assert settings.dialogue_preferences["show_overclock_warning"] is False
        settings.save_settings.assert_called_once()

    def test_disable_dialogue_creates_dict_if_missing(self):
        """disable_dialogue() creates dialogue_preferences dict if missing."""
        settings = Mock(spec=[])  # Mock with no attributes
        settings.save_settings = Mock()
        state = DialogueState(settings)

        state.disable_dialogue("test_key")

        assert hasattr(settings, "dialogue_preferences")
        assert settings.dialogue_preferences["test_key"] is False


class TestUnifiedRenderer:
    """Test UnifiedRenderer."""

    def test_render_dialogue_basic(self):
        """render() creates dialogue box without crashing."""
        console = tcod.console.Console(width=80, height=50)
        dialogue = create_gateway_dialogue()

        # Should not crash
        UnifiedRenderer.render(console, dialogue)

    def test_render_sets_alpha_opaque(self):
        """render() sets dialogue area alpha to 255 (opaque)."""
        console = tcod.console.Console(width=80, height=50)

        # Make entire console transparent first
        console.rgba["bg"][:, :, 3] = 0

        dialogue = create_gateway_dialogue()
        UnifiedRenderer.render(console, dialogue)

        # Check that some area in center is now opaque (dialogue box)
        # Center of 80x50 console should have opaque dialogue
        center_y, center_x = 25, 40
        assert console.rgba["bg"][center_y, center_x, 3] == 255

    def test_render_formats_message(self):
        """render() formats message with format_data."""
        console = tcod.console.Console(width=80, height=50)

        dialogue = create_overclock_warning_dialogue(
            exploit_name="Buffer Overflow",
            overheat_amount=15,
            damage=5,
            remaining_cpu=10,
            max_cpu=20,
        )

        # Should not crash when formatting
        UnifiedRenderer.render(console, dialogue)

    # NOTE: Text wrapping tests removed - we now use TCOD's built-in console.print()
    # with width parameter for word wrapping, which is well-tested in TCOD itself.


class TestDialogueInputHandler:
    """Test DialogueInputHandler."""

    def test_handle_input_confirm(self):
        """handle_input() returns 'confirm' for Y key."""
        dialogue = create_gateway_dialogue()
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.Y)

        assert action == "confirm"

    def test_handle_input_cancel(self):
        """handle_input() returns 'cancel' for N key."""
        dialogue = create_gateway_dialogue()
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.N)

        assert action == "cancel"

    def test_handle_input_dont_show_again(self):
        """handle_input() returns 'dont_show_again' for D key."""
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.D)

        assert action == "dont_show_again"

    def test_handle_input_dismiss_space(self):
        """handle_input() returns 'dismiss' for SPACE key."""
        dialogue = create_death_dialogue()
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.SPACE)

        assert action == "dismiss"

    def test_handle_input_dismiss_enter(self):
        """handle_input() returns 'dismiss' for ENTER key."""
        dialogue = create_death_dialogue()
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.RETURN)

        assert action == "dismiss"

    def test_handle_input_invalid_key(self):
        """handle_input() returns None for invalid keys."""
        dialogue = create_gateway_dialogue()
        # Gateway dialogue doesn't accept SPACE as valid
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.SPACE)

        assert action is None

    def test_handle_input_escape(self):
        """handle_input() returns 'dismiss' for ESC key."""
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        action = DialogueInputHandler.handle_input(dialogue, tcod.event.KeySym.ESCAPE)

        assert action == "dismiss"


class TestFactoryFunctions:
    """Test factory functions for creating dialogues."""

    def test_create_gateway_dialogue(self):
        """create_gateway_dialogue() creates valid DialogueBox."""
        dialogue = create_gateway_dialogue()

        assert dialogue.title == "NETWORK GATEWAY"
        assert "Proceed" in dialogue.message
        assert len(dialogue.options) == 2
        assert tcod.event.KeySym.Y in dialogue.valid_keys
        assert tcod.event.KeySym.N in dialogue.valid_keys
        assert dialogue.priority == 2
        assert dialogue.user_pref_key is None

    def test_create_death_dialogue(self):
        """create_death_dialogue() creates valid DialogueBox."""
        dialogue = create_death_dialogue()

        assert dialogue.title == "CONSCIOUSNESS PURGED"
        # Message is randomized from narrative content - just verify it exists and has content
        assert len(dialogue.message) > 0
        assert dialogue.message  # Non-empty string
        assert len(dialogue.options) == 1
        assert tcod.event.KeySym.SPACE in dialogue.valid_keys
        assert dialogue.priority == 10  # Critical
        assert dialogue.user_pref_key is None

    def test_create_intro_dialogue(self):
        """create_intro_dialogue() creates valid DialogueBox."""
        dialogue = create_intro_dialogue()

        assert dialogue.title == "SIGNAL COHERENCE: FAILING"
        assert "trap" in dialogue.message.lower()
        assert len(dialogue.options) == 1
        assert tcod.event.KeySym.SPACE in dialogue.valid_keys
        assert dialogue.priority == 10  # Critical
        assert dialogue.user_pref_key is None  # Always show intro

    def test_create_victory_dialogue(self):
        """create_victory_dialogue() creates valid DialogueBox."""
        dialogue = create_victory_dialogue()

        assert dialogue.title == "ROGUE SIGNAL ESTABLISHED"
        assert "breached" in dialogue.message.lower()
        assert len(dialogue.options) == 1
        assert tcod.event.KeySym.SPACE in dialogue.valid_keys
        assert dialogue.priority == 10  # Critical
        assert dialogue.user_pref_key is None

    def test_create_overclock_warning_dialogue(self):
        """create_overclock_warning_dialogue() creates valid DialogueBox with format data."""
        dialogue = create_overclock_warning_dialogue(
            exploit_name="Buffer Overflow",
            overheat_amount=15,
            damage=5,
            remaining_cpu=10,
            max_cpu=20,
        )

        assert dialogue.title == "*** OVERCLOCK WARNING ***"
        assert "{exploit_name}" in dialogue.message
        assert len(dialogue.options) == 3  # Y, N, D
        assert tcod.event.KeySym.Y in dialogue.valid_keys
        assert tcod.event.KeySym.N in dialogue.valid_keys
        assert tcod.event.KeySym.D in dialogue.valid_keys
        assert dialogue.priority == 5  # Medium
        assert dialogue.user_pref_key == "show_overclock_warning"

        # Check format data
        assert dialogue.format_data["exploit_name"] == "Buffer Overflow"
        assert dialogue.format_data["damage"] == 5
        assert dialogue.format_data["remaining_cpu"] == 10

    def test_create_inventory_attack_dialogue(self):
        """create_inventory_attack_dialogue() creates valid DialogueBox."""
        dialogue = create_inventory_attack_dialogue()

        assert dialogue.title == "*** UNDER ATTACK ***"
        assert "attacking" in dialogue.message.lower()
        assert len(dialogue.options) == 1
        assert tcod.event.KeySym.ESCAPE in dialogue.valid_keys
        assert dialogue.priority == 8  # High
        assert dialogue.user_pref_key is None


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_dialogue_lifecycle(self):
        """Test complete dialogue lifecycle: show, render, input, close."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)
        console = tcod.console.Console(width=80, height=50)

        # Show dialogue
        dialogue = create_gateway_dialogue()
        state.show(dialogue)
        assert state.is_active()

        # Render dialogue
        UnifiedRenderer.render(console, state.get_active())

        # Handle input
        action = DialogueInputHandler.handle_input(state.get_active(), tcod.event.KeySym.Y)
        assert action == "confirm"

        # Close dialogue
        state.close()
        assert not state.is_active()

    def test_multiple_dialogues_with_priority(self):
        """Test multiple dialogues with priority interruption."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Queue three dialogues
        state.show(create_gateway_dialogue())  # priority 2 - shows immediately
        state.show(create_death_dialogue())  # priority 10 - interrupts priority 2
        state.show(
            create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        )  # priority 5 - queues (5 < 10)

        # Highest priority interrupts and shows immediately
        assert state.get_active().priority == 10

        # Close and verify queue is ordered by priority
        state.close()
        assert state.get_active().priority == 5  # Medium priority from queue

        state.close()
        assert state.get_active().priority == 2  # Lowest priority from queue

        state.close()
        assert not state.is_active()

    def test_disabled_dialogue_not_shown(self):
        """Test that disabled dialogues are not shown."""
        settings = Mock()
        settings.dialogue_preferences = {"show_overclock_warning": False}
        state = DialogueState(settings)

        # Try to show disabled dialogue
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        state.show(dialogue)

        # Should not show
        assert not state.is_active()

    def test_render_all_dialogue_types(self):
        """Test rendering all dialogue types without crashes."""
        console = tcod.console.Console(width=80, height=50)

        dialogues = [
            create_gateway_dialogue(),
            create_death_dialogue(),
            create_intro_dialogue(),
            create_victory_dialogue(),
            create_overclock_warning_dialogue("Test", 10, 5, 15, 20),
            create_inventory_attack_dialogue(),
        ]

        for dialogue in dialogues:
            console.clear()
            UnifiedRenderer.render(console, dialogue)
            # If we get here without exception, rendering succeeded
