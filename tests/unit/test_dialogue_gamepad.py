"""
Tests for dialogue gamepad support.

Verifies that:
- Dialogue options show correct hints for current input device
- Gamepad input is handled via InputMapper
- Button remapping affects dialogue help text
"""

import pytest
import tcod.event
import tcod.sdl.joystick

from game_input_actions import InputAction, InputContext
from game_input_mappings import InputMapper
from game_input_device_tracker import InputDeviceType, set_last_device


class TestDialogueOptionText:
    """Test dynamic dialogue option text generation."""

    def test_confirm_option_shows_y_for_keyboard(self):
        """Verify confirm option shows [Y] when using keyboard."""
        from game_help_hints import get_dialogue_confirm_option

        set_last_device(InputDeviceType.KEYBOARD)
        result = get_dialogue_confirm_option("Yes")
        assert "[Y]" in result
        assert "Yes" in result

    def test_confirm_option_shows_a_for_gamepad(self):
        """Verify confirm option shows [A] when using gamepad."""
        from game_help_hints import get_dialogue_confirm_option

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_confirm_option("Yes")
        assert "[A]" in result
        assert "Yes" in result

    def test_cancel_option_shows_n_for_keyboard(self):
        """Verify cancel option shows [N] when using keyboard."""
        from game_help_hints import get_dialogue_cancel_option

        set_last_device(InputDeviceType.KEYBOARD)
        result = get_dialogue_cancel_option("No")
        assert "[N]" in result
        assert "No" in result

    def test_cancel_option_shows_b_for_gamepad(self):
        """Verify cancel option shows [B] when using gamepad."""
        from game_help_hints import get_dialogue_cancel_option

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_cancel_option("No")
        assert "[B]" in result
        assert "No" in result

    def test_skip_option_shows_d_for_keyboard(self):
        """Verify skip warning option shows [D] when using keyboard."""
        from game_help_hints import get_dialogue_skip_option

        set_last_device(InputDeviceType.KEYBOARD)
        result = get_dialogue_skip_option("Don't ask again")
        assert "[D]" in result
        assert "Don't ask again" in result

    def test_skip_option_shows_x_for_gamepad(self):
        """Verify skip warning option shows [X] when using gamepad."""
        from game_help_hints import get_dialogue_skip_option

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_skip_option("Don't ask again")
        assert "[X]" in result
        assert "Don't ask again" in result

    def test_dismiss_option_shows_keys_for_keyboard(self):
        """Verify dismiss option shows Space/Enter when using keyboard."""
        from game_help_hints import get_dialogue_dismiss_option

        set_last_device(InputDeviceType.KEYBOARD)
        result = get_dialogue_dismiss_option("Continue")
        assert "Space" in result or "Enter" in result
        assert "Continue" in result

    def test_dismiss_option_shows_a_for_gamepad(self):
        """Verify dismiss option shows [A] when using gamepad."""
        from game_help_hints import get_dialogue_dismiss_option

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_dismiss_option("Continue")
        assert "[A]" in result
        assert "Continue" in result

    def test_remapped_confirm_shows_custom_button(self):
        """Verify remapped CONFIRM shows new button on gamepad."""
        from game_help_hints import get_dialogue_confirm_option

        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton

        # Remap CONFIRM to Y button in DIALOGUE context
        mapper.add_gamepad_binding(InputAction.CONFIRM, CB.Y, InputContext.DIALOGUE)

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_confirm_option("Yes", mapper)
        assert "[Y]" in result  # Gamepad Y button

    def test_remapped_cancel_shows_custom_button(self):
        """Verify remapped CANCEL shows new button on gamepad."""
        from game_help_hints import get_dialogue_cancel_option

        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton

        # Remap CANCEL to X button in DIALOGUE context
        mapper.add_gamepad_binding(InputAction.CANCEL, CB.X, InputContext.DIALOGUE)

        set_last_device(InputDeviceType.GAMEPAD)
        result = get_dialogue_cancel_option("No", mapper)
        assert "[X]" in result


class TestDialogueFactoryOptions:
    """Test that dialogue factory functions create correct options."""

    def test_gateway_dialogue_has_keyboard_options(self):
        """Verify gateway dialogue has [Y] and [N] when using keyboard."""
        from game_dialogue_system import create_gateway_dialogue

        set_last_device(InputDeviceType.KEYBOARD)
        dialogue = create_gateway_dialogue(1)
        options_str = " ".join(dialogue.options)

        assert "[Y]" in options_str
        assert "[N]" in options_str

    def test_gateway_dialogue_has_gamepad_options(self):
        """Verify gateway dialogue has [A] and [B] when using gamepad."""
        from game_dialogue_system import create_gateway_dialogue

        set_last_device(InputDeviceType.GAMEPAD)
        dialogue = create_gateway_dialogue(1)
        options_str = " ".join(dialogue.options)

        assert "[A]" in options_str
        assert "[B]" in options_str

    def test_overclock_dialogue_has_skip_option_keyboard(self):
        """Verify overclock warning has [D] skip option when using keyboard."""
        from game_dialogue_system import create_overclock_warning_dialogue

        set_last_device(InputDeviceType.KEYBOARD)
        dialogue = create_overclock_warning_dialogue(
            exploit_name="Test",
            overheat_amount=5,
            damage=10,
            remaining_cpu=50,
            max_cpu=100,
        )
        options_str = " ".join(dialogue.options)

        assert "[D]" in options_str
        assert "Don't ask again" in options_str

    def test_overclock_dialogue_has_skip_option_gamepad(self):
        """Verify overclock warning has [X] skip option when using gamepad."""
        from game_dialogue_system import create_overclock_warning_dialogue

        set_last_device(InputDeviceType.GAMEPAD)
        dialogue = create_overclock_warning_dialogue(
            exploit_name="Test",
            overheat_amount=5,
            damage=10,
            remaining_cpu=50,
            max_cpu=100,
        )
        options_str = " ".join(dialogue.options)

        assert "[X]" in options_str
        assert "Don't ask again" in options_str

    def test_death_dialogue_has_dismiss_option_keyboard(self):
        """Verify death dialogue has Space/Enter dismiss for keyboard."""
        from game_dialogue_system import create_death_dialogue

        set_last_device(InputDeviceType.KEYBOARD)
        dialogue = create_death_dialogue()
        options_str = " ".join(dialogue.options)

        assert "Space" in options_str or "Enter" in options_str

    def test_death_dialogue_has_dismiss_option_gamepad(self):
        """Verify death dialogue has [A] dismiss for gamepad."""
        from game_dialogue_system import create_death_dialogue

        set_last_device(InputDeviceType.GAMEPAD)
        dialogue = create_death_dialogue()
        options_str = " ".join(dialogue.options)

        assert "[A]" in options_str

    def test_friendly_fire_dialogue_has_confirm_cancel_keyboard(self):
        """Verify friendly fire warning has [Y] and [N] for keyboard."""
        from game_dialogue_system import create_friendly_fire_warning_dialogue

        set_last_device(InputDeviceType.KEYBOARD)
        dialogue = create_friendly_fire_warning_dialogue(
            exploit_name="Test",
            damage=20,
            remaining_cpu=30,
            max_cpu=100,
        )
        options_str = " ".join(dialogue.options)

        assert "[Y]" in options_str
        assert "[N]" in options_str

    def test_friendly_fire_dialogue_has_confirm_cancel_gamepad(self):
        """Verify friendly fire warning has [A] and [B] for gamepad."""
        from game_dialogue_system import create_friendly_fire_warning_dialogue

        set_last_device(InputDeviceType.GAMEPAD)
        dialogue = create_friendly_fire_warning_dialogue(
            exploit_name="Test",
            damage=20,
            remaining_cpu=30,
            max_cpu=100,
        )
        options_str = " ".join(dialogue.options)

        assert "[A]" in options_str
        assert "[B]" in options_str


class TestInputMapperDialogueBindings:
    """Test InputMapper dialogue context bindings."""

    def test_default_dialogue_confirm_is_a(self):
        """Verify default CONFIRM in DIALOGUE context is A button."""
        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton

        action = mapper.get_action_for_gamepad_button(CB.A, InputContext.DIALOGUE)
        assert action == InputAction.CONFIRM

    def test_default_dialogue_cancel_is_b(self):
        """Verify default CANCEL in DIALOGUE context is B button."""
        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton

        action = mapper.get_action_for_gamepad_button(CB.B, InputContext.DIALOGUE)
        assert action == InputAction.CANCEL

    def test_default_dialogue_skip_is_x(self):
        """Verify default DIALOGUE_SKIP_WARNING in DIALOGUE context is X button."""
        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton

        action = mapper.get_action_for_gamepad_button(CB.X, InputContext.DIALOGUE)
        assert action == InputAction.DIALOGUE_SKIP_WARNING

    def test_button_hint_for_dialogue_confirm(self):
        """Verify button hint returns 'A' for CONFIRM."""
        mapper = InputMapper()
        hint = mapper.get_button_hint(InputAction.CONFIRM, InputContext.DIALOGUE)
        assert hint == "A"

    def test_button_hint_for_dialogue_cancel(self):
        """Verify button hint returns 'B' for CANCEL."""
        mapper = InputMapper()
        hint = mapper.get_button_hint(InputAction.CANCEL, InputContext.DIALOGUE)
        assert hint == "B"

    def test_button_hint_for_dialogue_skip(self):
        """Verify button hint returns 'X' for DIALOGUE_SKIP_WARNING."""
        mapper = InputMapper()
        hint = mapper.get_button_hint(InputAction.DIALOGUE_SKIP_WARNING, InputContext.DIALOGUE)
        assert hint == "X"


class TestDialogueSkipWarningAction:
    """Test DIALOGUE_SKIP_WARNING action exists and is configured."""

    def test_action_exists(self):
        """Verify DIALOGUE_SKIP_WARNING is defined."""
        assert hasattr(InputAction, "DIALOGUE_SKIP_WARNING")

    def test_action_has_display_name(self):
        """Verify action has a display name in ACTION_DISPLAY_NAMES."""
        from game_menu_controls import ACTION_DISPLAY_NAMES

        assert InputAction.DIALOGUE_SKIP_WARNING in ACTION_DISPLAY_NAMES
        assert ACTION_DISPLAY_NAMES[InputAction.DIALOGUE_SKIP_WARNING] == "Don't Warn Again"
