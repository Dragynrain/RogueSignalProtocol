"""
Keyboard Binding Modifier Key Integration Tests

Tests that the keyboard binding capture mode correctly handles modifier keys:
- Modifier-only keys (Shift, Ctrl, Alt) are ignored
- Modifier+key combinations are captured correctly
- The binding flow works end-to-end through the menu system

Note: These tests verify the full input pipeline from event creation
through menu handling to binding storage.
"""

import pytest
import tcod
import tcod.event

from game_config import GameSettings
from game_input_actions import InputAction
from game_input_mappings import MODIFIER_ONLY_KEYS, InputMapper
from game_menu_controls import KeyboardBindingsMenu
from tests.integration.input_test_utils import InputTestHelper


class TestKeyboardBindingModifierIntegration:
    """
    Integration tests for modifier key handling in keyboard binding mode.

    These tests verify the complete flow:
    1. Enter binding mode
    2. Press modifier key (should be ignored)
    3. Press modifier+key combination (should create binding)
    4. Verify binding is stored correctly
    """

    @pytest.fixture
    def binding_menu(self):
        """Create a keyboard bindings menu ready for testing."""
        settings = GameSettings()
        input_mapper = InputMapper()
        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        return menu

    @pytest.fixture
    def binding_menu_in_binding_mode(self, binding_menu):
        """Create a menu already in binding mode for an action."""
        # Enter binding mode for TOGGLE_HELP (an action with few default bindings)
        binding_menu.binding_mode = True
        binding_menu.binding_action = InputAction.TOGGLE_HELP
        return binding_menu

    # --------------------------------------------------------------------------
    # Modifier-Only Key Rejection Tests
    # --------------------------------------------------------------------------

    def test_left_shift_alone_stays_in_binding_mode(self, binding_menu_in_binding_mode):
        """Integration: Pressing only left Shift should not exit binding mode."""
        menu = binding_menu_in_binding_mode

        # Create Shift key event
        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.LSHIFT, mod=tcod.event.Modifier.SHIFT
        )

        # Process through full input pipeline
        menu.handle_input(event)

        # Should still be in binding mode
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

    def test_right_shift_alone_stays_in_binding_mode(self, binding_menu_in_binding_mode):
        """Integration: Pressing only right Shift should not exit binding mode."""
        menu = binding_menu_in_binding_mode

        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.RSHIFT, mod=tcod.event.Modifier.SHIFT
        )

        menu.handle_input(event)

        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

    def test_ctrl_alone_stays_in_binding_mode(self, binding_menu_in_binding_mode):
        """Integration: Pressing only Ctrl should not exit binding mode."""
        menu = binding_menu_in_binding_mode

        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.LCTRL, mod=tcod.event.Modifier.CTRL
        )

        menu.handle_input(event)

        assert menu.binding_mode is True

    def test_alt_alone_stays_in_binding_mode(self, binding_menu_in_binding_mode):
        """Integration: Pressing only Alt should not exit binding mode."""
        menu = binding_menu_in_binding_mode

        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.LALT, mod=tcod.event.Modifier.ALT
        )

        menu.handle_input(event)

        assert menu.binding_mode is True

    # --------------------------------------------------------------------------
    # Modifier+Key Combination Tests
    # --------------------------------------------------------------------------

    def test_shift_plus_slash_creates_binding(self, binding_menu_in_binding_mode):
        """Integration: Shift+/ should create a binding (for '?' key)."""
        menu = binding_menu_in_binding_mode

        # Create Shift+/ event (which produces '?' on US keyboard)
        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.SLASH, mod=tcod.event.Modifier.SHIFT
        )

        menu.handle_input(event)

        # Should exit binding mode
        assert menu.binding_mode is False
        assert menu.binding_action is None

        # Binding should be stored
        assert menu.input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_shift_plus_unbound_key_creates_binding(self, binding_menu_in_binding_mode):
        """Integration: Shift+unbound key should create a binding."""
        menu = binding_menu_in_binding_mode

        # Create Shift+Semicolon event (typically unbound)
        event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.SEMICOLON, mod=tcod.event.Modifier.SHIFT
        )

        menu.handle_input(event)

        assert menu.binding_mode is False
        assert menu.input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    # --------------------------------------------------------------------------
    # Full Binding Flow Tests
    # --------------------------------------------------------------------------

    def test_full_binding_flow_with_modifier_rejection(self, binding_menu):
        """Integration: Complete flow - enter binding, press shift, press shift+key."""
        menu = binding_menu

        # Step 1: Navigate to TOGGLE_HELP and enter binding mode
        # Find the TOGGLE_HELP action in the selectable items
        for i, idx in enumerate(menu.selectable_indices):
            item = menu.display_items[idx]
            if item.get("action") == InputAction.TOGGLE_HELP:
                menu.selected_index = i
                break

        # Press Enter to enter binding mode
        menu.execute_action(InputAction.CONFIRM)
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

        # Step 2: Press Shift alone (should be ignored)
        shift_event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.LSHIFT, mod=tcod.event.Modifier.SHIFT
        )
        menu.handle_input(shift_event)
        assert menu.binding_mode is True, "Shift alone should not create binding"

        # Step 3: Press Shift+/ to create the binding
        slash_event = InputTestHelper.create_keyboard_event(
            tcod.event.KeySym.SLASH, mod=tcod.event.Modifier.SHIFT
        )
        menu.handle_input(slash_event)

        # Step 4: Verify binding was created
        assert menu.binding_mode is False
        assert menu.input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_multiple_modifier_attempts_before_binding(self, binding_menu_in_binding_mode):
        """Integration: Multiple modifier presses should all be ignored until real key."""
        menu = binding_menu_in_binding_mode

        # Press various modifiers
        modifiers = [
            (tcod.event.KeySym.LSHIFT, tcod.event.Modifier.SHIFT),
            (tcod.event.KeySym.LCTRL, tcod.event.Modifier.CTRL),
            (tcod.event.KeySym.LALT, tcod.event.Modifier.ALT),
            (tcod.event.KeySym.RSHIFT, tcod.event.Modifier.SHIFT),
        ]

        for key_sym, mod in modifiers:
            event = InputTestHelper.create_keyboard_event(key_sym, mod=mod)
            menu.handle_input(event)
            assert menu.binding_mode is True, f"Modifier {key_sym} should not create binding"

        # Finally press a real key
        event = InputTestHelper.create_keyboard_event(tcod.event.KeySym.T)
        menu.handle_input(event)

        assert menu.binding_mode is False
        assert menu.input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)


class TestModifierBindingSaveLoad:
    """Tests for saving and loading custom bindings with modifiers."""

    def test_save_load_roundtrip_preserves_modifier(self):
        """Custom binding with modifier survives save/load cycle."""
        mapper = InputMapper()

        # Add a custom binding with Shift modifier
        mapper.add_keyboard_binding(
            InputAction.TOGGLE_HELP, tcod.event.KeySym.SLASH, modifier=tcod.event.Modifier.SHIFT
        )

        # Save bindings
        keyboard_bindings, gamepad_bindings = mapper.save_custom_bindings()

        # Verify saved format - Shift+/ should be saved as "?"
        assert "GAMEPLAY" in keyboard_bindings
        assert "TOGGLE_HELP" in keyboard_bindings["GAMEPLAY"]
        binding_names = keyboard_bindings["GAMEPLAY"]["TOGGLE_HELP"]
        assert "?" in binding_names, f"Expected '?' in {binding_names}"

        # Create new mapper and load saved bindings
        new_mapper = InputMapper()
        new_mapper.load_custom_bindings(keyboard_bindings, gamepad_bindings)

        # Verify the binding works - Shift+/ should trigger TOGGLE_HELP
        action = new_mapper.get_action_for_key(
            tcod.event.KeySym.SLASH, modifier=tcod.event.Modifier.SHIFT
        )
        assert action == InputAction.TOGGLE_HELP

        # Verify plain / does NOT trigger TOGGLE_HELP
        action_plain = new_mapper.get_action_for_key(tcod.event.KeySym.SLASH, modifier=0)
        assert action_plain != InputAction.TOGGLE_HELP

    def test_save_load_multiple_modifiers(self):
        """Custom binding with Ctrl+Shift survives save/load."""
        mapper = InputMapper()

        # Add Ctrl+Shift+S binding
        ctrl_shift = tcod.event.Modifier.CTRL | tcod.event.Modifier.SHIFT
        mapper.add_keyboard_binding(InputAction.WAIT, tcod.event.KeySym.S, modifier=ctrl_shift)

        # Save and reload
        keyboard_bindings, gamepad_bindings = mapper.save_custom_bindings()
        new_mapper = InputMapper()
        new_mapper.load_custom_bindings(keyboard_bindings, gamepad_bindings)

        # Verify Ctrl+Shift+S triggers WAIT
        action = new_mapper.get_action_for_key(tcod.event.KeySym.S, modifier=ctrl_shift)
        assert action == InputAction.WAIT

        # Plain S should still be MOVE_SOUTH (default)
        action_plain = new_mapper.get_action_for_key(tcod.event.KeySym.S, modifier=0)
        assert action_plain == InputAction.MOVE_SOUTH

    def test_save_load_mixed_bindings(self):
        """Mix of plain and modifier bindings survives save/load."""
        mapper = InputMapper()

        # Add plain binding
        mapper.add_keyboard_binding(InputAction.WAIT, tcod.event.KeySym.T)
        # Add modifier binding
        mapper.add_keyboard_binding(
            InputAction.TOGGLE_HELP, tcod.event.KeySym.H, modifier=tcod.event.Modifier.SHIFT
        )

        # Save and reload
        keyboard_bindings, gamepad_bindings = mapper.save_custom_bindings()
        new_mapper = InputMapper()
        new_mapper.load_custom_bindings(keyboard_bindings, gamepad_bindings)

        # Verify plain T triggers WAIT
        assert new_mapper.get_action_for_key(tcod.event.KeySym.T) == InputAction.WAIT

        # Verify Shift+H triggers TOGGLE_HELP
        action = new_mapper.get_action_for_key(
            tcod.event.KeySym.H, modifier=tcod.event.Modifier.SHIFT
        )
        assert action == InputAction.TOGGLE_HELP


class TestHelpTextDisplaysModifierKey:
    """Tests that help text shows the help key symbol correctly."""

    def test_info_panel_shows_question_mark_for_help(self):
        """Info panel should display 'Press ?' for help (shows symbol, not Shift+/)."""
        from game_info_panel import InfoProvider

        # Create a minimal mock game for testing
        class MockGame:
            def __init__(self):
                self.player = None
                self.show_inventory = False
                self.look_mode_active = False
                self.mouse_hover_world_pos = None

        game = MockGame()
        # get_default_info is called when get_info_for_hover returns None
        info = InfoProvider.get_default_info(game)

        # Find the help text line
        help_line = None
        for line in info["lines"]:
            if "help" in line["text"].lower():
                help_line = line["text"]
                break

        assert help_line is not None, "Help text not found in info panel"
        # Should show "?" symbol, not "Shift+/"
        assert "?" in help_line, f"Expected '?' in help text, got: {help_line}"
        assert "Press ? for help" == help_line, f"Expected 'Press ? for help', got: {help_line}"


class TestModifierOnlyKeysConstant:
    """Tests for the MODIFIER_ONLY_KEYS constant in game_input_mappings."""

    def test_modifier_only_keys_contains_expected_keys(self):
        """MODIFIER_ONLY_KEYS should contain all standard modifier keys."""
        expected_keys = {
            tcod.event.KeySym.LSHIFT,
            tcod.event.KeySym.RSHIFT,
            tcod.event.KeySym.LCTRL,
            tcod.event.KeySym.RCTRL,
            tcod.event.KeySym.LALT,
            tcod.event.KeySym.RALT,
            tcod.event.KeySym.LGUI,
            tcod.event.KeySym.RGUI,
        }

        assert MODIFIER_ONLY_KEYS == expected_keys

    def test_modifier_only_keys_does_not_contain_escape(self):
        """MODIFIER_ONLY_KEYS should not contain ESC (used for cancel)."""
        assert tcod.event.KeySym.ESCAPE not in MODIFIER_ONLY_KEYS

    def test_modifier_only_keys_does_not_contain_regular_keys(self):
        """MODIFIER_ONLY_KEYS should not contain regular letter/number keys."""
        regular_keys = [
            tcod.event.KeySym.A,
            tcod.event.KeySym.Z,
            tcod.event.KeySym.N1,
            tcod.event.KeySym.SPACE,
            tcod.event.KeySym.RETURN,
        ]

        for key in regular_keys:
            assert key not in MODIFIER_ONLY_KEYS
