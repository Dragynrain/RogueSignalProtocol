#!/usr/bin/env python3
"""
Unit tests for menu navigation and settings functionality.

Tests for:
- Menu back navigation (should return to parent, not main menu)
- Gamepad enabled/disabled setting
- Deadzone setting updates applying at runtime
- Left stick horizontal movement in menus
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestMenuBackNavigation:
    """Tests for proper back navigation hierarchy."""

    def test_controls_hub_back_returns_to_settings(self):
        """Controls hub 'back' should return to settings menu, not main menu."""
        # This tests the menu hierarchy:
        # Main Menu -> Settings -> Controls Hub -> Keyboard/Gamepad Bindings
        # "back" from Controls Hub should go to Settings, not Main Menu

        from game_menu_controls import ControlsMenuHub
        from game_config import GameSettings

        settings = GameSettings()
        hub = ControlsMenuHub(settings, None)

        # When user presses back in controls hub
        from game_input_actions import InputAction
        result = hub.execute_action(InputAction.CANCEL)

        # It should return "back" (menu loop handles the actual navigation)
        assert result == "back"
        # The test verifies the menu returns "back", but the game loop
        # needs to track parent menus to know WHERE to go back to

    def test_keyboard_bindings_back_returns_to_controls_hub(self):
        """Keyboard bindings 'back' should return to controls hub."""
        from game_menu_controls import KeyboardBindingsMenu
        from game_input_mappings import InputMapper
        from game_config import GameSettings
        from game_input_actions import InputAction

        settings = GameSettings()
        mapper = InputMapper()
        menu = KeyboardBindingsMenu(settings, mapper, None)

        result = menu.execute_action(InputAction.CANCEL)
        assert result == "back"


class TestGamepadEnabledSetting:
    """Tests for gamepad enabled/disabled functionality."""

    def test_gamepad_disabled_blocks_controller_button(self):
        """When gamepad_enabled is False, controller buttons should be ignored."""
        # This is a failing test - the setting isn't checked yet
        from game_input_gamepad import GamepadInputHandler
        from game_input_mappings import InputMapper
        from game_input_actions import InputContext

        mapper = InputMapper()

        # Create mock game with settings
        mock_game = Mock()
        mock_game.settings = Mock()
        mock_game.settings.gamepad_enabled = False
        mock_game.settings.gamepad_deadzone = 0.15
        mock_game.settings.gamepad_direction_locking = True

        handler = GamepadInputHandler(mapper, mock_game)

        # Create mock button event (A button press)
        import tcod.event
        import tcod.sdl.joystick
        mock_event = Mock(spec=tcod.event.ControllerButton)
        mock_event.pressed = True
        mock_event.button = tcod.sdl.joystick.ControllerButton.A

        # When gamepad is disabled, button should return None (ignored)
        result = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert result is None, "Gamepad button should be ignored when gamepad_enabled=False"

    def test_gamepad_enabled_processes_controller_button(self):
        """When gamepad_enabled is True, controller buttons should be processed."""
        from game_input_gamepad import GamepadInputHandler
        from game_input_mappings import InputMapper
        from game_input_actions import InputContext, InputAction

        mapper = InputMapper()

        # Create mock game with settings
        mock_game = Mock()
        mock_game.settings = Mock()
        mock_game.settings.gamepad_enabled = True
        mock_game.settings.gamepad_deadzone = 0.15
        mock_game.settings.gamepad_direction_locking = True

        handler = GamepadInputHandler(mapper, mock_game)

        # Create mock button event (A button press)
        import tcod.event
        import tcod.sdl.joystick
        mock_event = Mock(spec=tcod.event.ControllerButton)
        mock_event.pressed = True
        mock_event.button = tcod.sdl.joystick.ControllerButton.A

        # When gamepad is enabled, button should return an action
        result = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert result == InputAction.WAIT, "A button in GAMEPLAY should map to WAIT"


class TestDeadzoneSetting:
    """Tests for deadzone setting updates."""

    def test_deadzone_change_applies_at_runtime(self):
        """Changing deadzone setting should affect analog stick immediately."""
        from game_input_analog import AnalogStickHandler

        handler = AnalogStickHandler(deadzone=0.15)
        assert handler.deadzone == 0.15

        # Change deadzone
        handler.deadzone = 0.30

        # A stick value of 0.2 (which is above 0.15 but below 0.30)
        # should now register as zero with the new deadzone
        raw_value = int(0.2 * 32767)  # 20% deflection
        result = handler.apply_scaled_radial_deadzone(raw_value, 0)
        assert result == (0.0, 0.0), "20% deflection should be inside 30% deadzone"

    def test_gamepad_handler_reads_deadzone_dynamically(self):
        """GamepadInputHandler should read deadzone from settings on each use.

        The sync_settings_to_analog_handler() method syncs settings to the analog handler.
        It's also called automatically on every axis event (line 268-269 in game_input_gamepad.py).
        """
        from game_input_gamepad import GamepadInputHandler
        from game_input_mappings import InputMapper

        mapper = InputMapper()

        # Create mock game with settings
        mock_game = Mock()
        mock_game.settings = Mock()
        mock_game.settings.gamepad_enabled = True
        mock_game.settings.gamepad_deadzone = 0.15
        mock_game.settings.gamepad_direction_locking = True
        mock_game.settings.gamepad_threshold = 0.30

        handler = GamepadInputHandler(mapper, mock_game)

        # Initial deadzone should be 0.15
        assert handler.analog_handler.deadzone == 0.15

        # User changes deadzone setting to 0.30
        mock_game.settings.gamepad_deadzone = 0.30

        # Sync applies the new value (also called automatically on axis events)
        handler.sync_settings_to_analog_handler()
        assert handler.analog_handler.deadzone == 0.30, \
            "Handler should update deadzone when settings change"


class TestLeftStickHorizontalInMenus:
    """Tests for left stick horizontal movement in menus."""

    def test_left_stick_horizontal_adjusts_sliders(self):
        """Left stick horizontal movement should adjust slider values in menus."""
        # This is testing the game loop behavior - it currently only handles vertical
        from game_input_analog import AnalogStickHandler

        handler = AnalogStickHandler()

        # Move stick fully right
        handler.update_left_stick(x=32767, y=0)

        # Get menu movement - should return (1, 0) for right
        movement = handler.get_left_stick_movement_menu()
        assert movement is not None, "Horizontal stick should produce movement"
        dx, dy = movement
        assert dx == 1 and dy == 0, "Full right stick should give (1, 0)"

    def test_horizontal_stick_returns_correct_direction(self):
        """Horizontal stick movement should return correct dx values."""
        from game_input_analog import AnalogStickHandler

        handler = AnalogStickHandler()

        # Test left direction
        handler.update_left_stick(x=-32767, y=0)
        movement = handler.get_left_stick_movement_menu()
        assert movement is not None, "Left stick should produce movement"
        dx, dy = movement
        assert dx == -1 and dy == 0, "Full left stick should give (-1, 0)"

        # Reset and test right direction
        handler.update_left_stick(x=32767, y=0)
        movement = handler.get_left_stick_movement_menu()
        assert movement is not None, "Right stick should produce movement"
        dx, dy = movement
        assert dx == 1 and dy == 0, "Full right stick should give (1, 0)"


class TestKeyboardContextAwareness:
    """Tests for keyboard input context handling."""

    def test_keyboard_uses_context_for_action_lookup(self):
        """BaseInputHandler should pass context to get_action_for_key.

        Bug: Line 112 in game_input_base.py calls get_action_for_key without context.
        This breaks custom keyboard bindings which are context-specific.
        """
        from game_input_base import BaseInputHandler
        from game_input_actions import InputAction, InputContext
        from unittest.mock import Mock, patch
        import tcod.event

        # Create a concrete subclass for testing
        class TestMenu(BaseInputHandler):
            def get_context(self):
                return InputContext.SETTINGS_MENU

            def execute_action(self, action):
                return action

            def get_default_return(self):
                return None

        handler = TestMenu()

        # Mock the input_mapper to verify context is passed
        with patch.object(handler.input_mapper, 'get_action_for_key') as mock_get_action:
            mock_get_action.return_value = InputAction.NAVIGATE_DOWN

            # Create a key event
            event = Mock(spec=tcod.event.KeyDown)
            event.sym = tcod.event.KeySym.DOWN

            handler.handle_input(event)

            # Verify get_action_for_key was called WITH the context and modifier
            mock_get_action.assert_called_once_with(
                tcod.event.KeySym.DOWN,
                InputContext.SETTINGS_MENU,  # Context should be passed!
                0  # Default modifier (no modifier pressed)
            )
