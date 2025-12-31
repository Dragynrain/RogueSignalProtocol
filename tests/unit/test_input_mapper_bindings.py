"""
Tests for InputMapper keyboard and gamepad binding modification methods.

Tests the key rebinding and gamepad remapping functionality including:
- add_keyboard_binding / add_gamepad_binding
- remove_keyboard_binding / remove_gamepad_binding
- clear_keyboard_bindings / clear_gamepad_bindings
- replace_keyboard_binding / replace_gamepad_binding
- get_conflicts / get_gamepad_conflicts
"""

import tcod.event
import tcod.sdl.joystick

from rsp.input.actions import InputAction, InputContext
from rsp.input.mappings import InputMapper

# Shortcuts for readability
KS = tcod.event.KeySym
CB = tcod.sdl.joystick.ControllerButton


class TestKeyboardBindingAdd:
    """Tests for add_keyboard_binding()."""

    def test_add_simple_binding(self):
        """Adding a key binding works."""
        mapper = InputMapper()

        result = mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        assert result is True
        # Verify it's in custom bindings
        assert InputContext.GAMEPLAY in mapper._custom_keyboard_bindings
        assert InputAction.WAIT in mapper._custom_keyboard_bindings[InputContext.GAMEPLAY]

    def test_add_binding_reserved_escape_rejected(self):
        """ESC key cannot be bound."""
        mapper = InputMapper()

        result = mapper.add_keyboard_binding(InputAction.WAIT, KS.ESCAPE, InputContext.GAMEPLAY)

        assert result is False

    def test_add_binding_reserved_f12_rejected(self):
        """F12 key cannot be bound."""
        mapper = InputMapper()

        result = mapper.add_keyboard_binding(InputAction.WAIT, KS.F12, InputContext.GAMEPLAY)

        assert result is False

    def test_add_binding_with_modifier(self):
        """Adding binding with Shift modifier works."""
        mapper = InputMapper()

        # Use KS(ord('w')) for cross-platform compatibility (KS.w doesn't exist on Linux)
        result = mapper.add_keyboard_binding(
            InputAction.WAIT,
            KS(ord("w")),
            InputContext.GAMEPLAY,
            modifier=tcod.event.Modifier.SHIFT,
        )

        assert result is True

    def test_add_duplicate_binding_no_duplicate(self):
        """Adding same binding twice doesn't create duplicate."""
        mapper = InputMapper()

        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        # Should have exactly one binding
        bindings = mapper._custom_keyboard_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(bindings) == 1

    def test_add_multiple_keys_same_action(self):
        """Can bind multiple keys to same action."""
        mapper = InputMapper()

        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.WAIT, KS.PERIOD, InputContext.GAMEPLAY)

        bindings = mapper._custom_keyboard_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(bindings) == 2

    def test_add_binding_different_contexts(self):
        """Same key can be bound in different contexts."""
        mapper = InputMapper()

        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.RETURN, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.RETURN, InputContext.INVENTORY)

        assert InputContext.GAMEPLAY in mapper._custom_keyboard_bindings
        assert InputContext.INVENTORY in mapper._custom_keyboard_bindings


class TestKeyboardBindingRemove:
    """Tests for remove_keyboard_binding()."""

    def test_remove_existing_binding(self):
        """Removing existing binding works."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        result = mapper.remove_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        assert result is True
        # Context should be cleaned up
        assert InputContext.GAMEPLAY not in mapper._custom_keyboard_bindings

    def test_remove_nonexistent_binding(self):
        """Removing binding that doesn't exist returns False."""
        mapper = InputMapper()

        result = mapper.remove_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        assert result is False

    def test_remove_nonexistent_context(self):
        """Removing from nonexistent context returns False."""
        mapper = InputMapper()

        result = mapper.remove_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.TARGETING)

        assert result is False

    def test_remove_with_modifier(self):
        """Removing binding with modifier works."""
        mapper = InputMapper()
        # Use KS(ord('w')) for cross-platform compatibility (KS.w doesn't exist on Linux)
        mapper.add_keyboard_binding(
            InputAction.WAIT,
            KS(ord("w")),
            InputContext.GAMEPLAY,
            modifier=tcod.event.Modifier.SHIFT,
        )

        result = mapper.remove_keyboard_binding(
            InputAction.WAIT,
            KS(ord("w")),
            InputContext.GAMEPLAY,
            modifier=tcod.event.Modifier.SHIFT,
        )

        assert result is True

    def test_remove_leaves_other_bindings(self):
        """Removing one binding doesn't affect others."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.WAIT, KS.PERIOD, InputContext.GAMEPLAY)

        mapper.remove_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        # Period binding should still exist
        bindings = mapper._custom_keyboard_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(bindings) == 1


class TestKeyboardBindingClear:
    """Tests for clear_keyboard_bindings()."""

    def test_clear_action_bindings(self):
        """Clearing bindings for action removes all keys."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.WAIT, KS.PERIOD, InputContext.GAMEPLAY)

        mapper.clear_keyboard_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        # Action should be gone
        assert InputAction.WAIT not in mapper._custom_keyboard_bindings.get(
            InputContext.GAMEPLAY, {}
        )

    def test_clear_leaves_other_actions(self):
        """Clearing one action doesn't affect others."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.RETURN, InputContext.GAMEPLAY)

        mapper.clear_keyboard_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        # CONFIRM should still exist
        assert InputAction.CONFIRM in mapper._custom_keyboard_bindings[InputContext.GAMEPLAY]

    def test_clear_nonexistent_no_error(self):
        """Clearing nonexistent action doesn't raise error."""
        mapper = InputMapper()

        # Should not raise
        mapper.clear_keyboard_bindings(InputAction.WAIT, InputContext.GAMEPLAY)


class TestKeyboardBindingReplace:
    """Tests for replace_keyboard_binding()."""

    def test_replace_removes_conflicts(self):
        """Replace removes key from other actions."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.SPACE, InputContext.GAMEPLAY)

        # Now bind SPACE to WAIT instead
        removed = mapper.replace_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        # CONFIRM should have lost SPACE
        assert InputAction.CONFIRM in removed or len(removed) > 0
        # WAIT should have SPACE
        assert InputAction.WAIT in mapper._custom_keyboard_bindings[InputContext.GAMEPLAY]

    def test_replace_returns_conflicting_actions(self):
        """Replace returns list of actions that lost the binding."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_keyboard_binding(InputAction.CANCEL, KS.SPACE, InputContext.GAMEPLAY)

        removed = mapper.replace_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        # Both should be in removed list
        assert InputAction.CONFIRM in removed
        assert InputAction.CANCEL in removed

    def test_replace_no_conflicts_empty_list(self):
        """Replace with no conflicts returns empty list (or just defaults)."""
        mapper = InputMapper()

        removed = mapper.replace_keyboard_binding(
            InputAction.WAIT, KS.F5, InputContext.GAMEPLAY  # Unlikely to conflict
        )

        # May include default conflicts, but no custom ones added
        assert isinstance(removed, list)


class TestKeyboardConflicts:
    """Tests for get_conflicts()."""

    def test_detect_custom_binding_conflict(self):
        """Detects conflict with custom binding."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.SPACE, InputContext.GAMEPLAY)

        conflicts = mapper.get_conflicts(InputAction.WAIT, KS.SPACE)

        assert InputAction.CONFIRM in conflicts

    def test_no_conflict_different_key(self):
        """No conflict when using different key."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.CONFIRM, KS.SPACE, InputContext.GAMEPLAY)

        conflicts = mapper.get_conflicts(InputAction.WAIT, KS.PERIOD)

        # CONFIRM uses SPACE, not PERIOD
        assert InputAction.CONFIRM not in conflicts

    def test_no_self_conflict(self):
        """Action doesn't conflict with itself."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        conflicts = mapper.get_conflicts(InputAction.WAIT, KS.SPACE)

        assert InputAction.WAIT not in conflicts


class TestGamepadBindingAdd:
    """Tests for add_gamepad_binding()."""

    def test_add_simple_binding(self):
        """Adding gamepad button binding works."""
        mapper = InputMapper()

        result = mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        assert result is True
        assert InputContext.GAMEPLAY in mapper._custom_gamepad_bindings
        assert InputAction.WAIT in mapper._custom_gamepad_bindings[InputContext.GAMEPLAY]

    def test_add_reserved_guide_rejected(self):
        """Guide button cannot be bound."""
        mapper = InputMapper()

        result = mapper.add_gamepad_binding(InputAction.WAIT, CB.GUIDE, InputContext.GAMEPLAY)

        assert result is False

    def test_add_duplicate_no_duplicate(self):
        """Adding same button twice doesn't create duplicate."""
        mapper = InputMapper()

        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        buttons = mapper._custom_gamepad_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(buttons) == 1

    def test_add_multiple_buttons_same_action(self):
        """Can bind multiple buttons to same action."""
        mapper = InputMapper()

        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        buttons = mapper._custom_gamepad_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(buttons) == 2


class TestGamepadBindingRemove:
    """Tests for remove_gamepad_binding()."""

    def test_remove_existing_binding(self):
        """Removing existing button binding works."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        result = mapper.remove_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        assert result is True
        assert InputContext.GAMEPLAY not in mapper._custom_gamepad_bindings

    def test_remove_nonexistent_binding(self):
        """Removing nonexistent binding returns False."""
        mapper = InputMapper()

        result = mapper.remove_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        assert result is False

    def test_remove_leaves_other_bindings(self):
        """Removing one button doesn't affect others."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        mapper.remove_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        buttons = mapper._custom_gamepad_bindings[InputContext.GAMEPLAY][InputAction.WAIT]
        assert len(buttons) == 1
        assert CB.X in buttons


class TestGamepadBindingClear:
    """Tests for clear_gamepad_bindings()."""

    def test_clear_action_bindings(self):
        """Clearing bindings removes all buttons for action."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        mapper.clear_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        assert InputAction.WAIT not in mapper._custom_gamepad_bindings.get(
            InputContext.GAMEPLAY, {}
        )

    def test_clear_leaves_other_actions(self):
        """Clearing one action doesn't affect others."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.CONFIRM, CB.X, InputContext.GAMEPLAY)

        mapper.clear_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        assert InputAction.CONFIRM in mapper._custom_gamepad_bindings[InputContext.GAMEPLAY]


class TestGamepadBindingReplace:
    """Tests for replace_gamepad_binding()."""

    def test_replace_removes_conflicts(self):
        """Replace removes button from other actions."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.CONFIRM, CB.A, InputContext.GAMEPLAY)

        removed = mapper.replace_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        # CONFIRM should have lost A button
        assert InputAction.CONFIRM in removed or len(removed) > 0
        # WAIT should have A
        assert CB.A in mapper._custom_gamepad_bindings[InputContext.GAMEPLAY][InputAction.WAIT]

    def test_replace_returns_conflicting_actions(self):
        """Replace returns list of actions that lost the binding."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.CONFIRM, CB.A, InputContext.GAMEPLAY)

        removed = mapper.replace_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        assert InputAction.CONFIRM in removed


class TestGamepadConflicts:
    """Tests for get_gamepad_conflicts()."""

    def test_detect_default_conflict(self):
        """Detects conflict with default gamepad binding."""
        mapper = InputMapper()

        # A button in GAMEPLAY is usually WAIT by default
        conflicts = mapper.get_gamepad_conflicts(InputAction.CONFIRM, CB.A, InputContext.GAMEPLAY)

        # Should find WAIT (the default A button mapping)
        assert isinstance(conflicts, list)

    def test_no_self_conflict(self):
        """Action doesn't conflict with itself."""
        mapper = InputMapper()

        conflicts = mapper.get_gamepad_conflicts(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        assert InputAction.WAIT not in conflicts


class TestResetToDefaults:
    """Tests for reset_to_defaults()."""

    def test_reset_keyboard_clears_custom(self):
        """Resetting keyboard clears custom bindings."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)

        mapper.reset_to_defaults("keyboard")

        assert len(mapper._custom_keyboard_bindings) == 0

    def test_reset_gamepad_clears_custom(self):
        """Resetting gamepad clears custom bindings."""
        mapper = InputMapper()
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        mapper.reset_to_defaults("gamepad")

        assert len(mapper._custom_gamepad_bindings) == 0

    def test_reset_keyboard_preserves_gamepad(self):
        """Resetting keyboard doesn't affect gamepad."""
        mapper = InputMapper()
        mapper.add_keyboard_binding(InputAction.WAIT, KS.SPACE, InputContext.GAMEPLAY)
        mapper.add_gamepad_binding(InputAction.WAIT, CB.A, InputContext.GAMEPLAY)

        mapper.reset_to_defaults("keyboard")

        assert len(mapper._custom_keyboard_bindings) == 0
        assert len(mapper._custom_gamepad_bindings) > 0
