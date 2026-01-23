"""
Gamepad Settings Synchronization Tests.

Tests that gamepad settings changes are applied in real-time during gameplay:
- gamepad_enabled toggle
- gamepad_deadzone changes
- gamepad_threshold changes
- gamepad_direction_locking toggle
- gamepad_swap_sticks toggle

The sync_settings_to_analog_handler() method should apply these changes
without recreating the handler.

Uses the game_with_gamepad fixture from tests/conftest.py.
Uses mock_time fixture for deterministic timing (no flaky time.sleep).
"""

import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameConfig
from rsp.input.actions import InputAction, InputContext

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

SETTLING_PERIOD_SEC = 0.035


class TestGamepadEnabledSetting:
    """Test toggling gamepad_enabled during gameplay."""

    def test_gamepad_enabled_by_default(self, game_with_gamepad):
        """Gamepad should be enabled by default."""
        game, input_handler, _ = game_with_gamepad

        assert game.settings.gamepad_enabled is True

    def test_disable_gamepad_ignores_button_input(self, game_with_gamepad):
        """When gamepad_enabled=False, button input should be ignored."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Disable gamepad
        game.settings.gamepad_enabled = False

        # Try to press A button
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        action = gamepad.handle_button_event(button_event, InputContext.GAMEPLAY)

        # Should return None (ignored)
        assert action is None

    def test_disable_gamepad_ignores_axis_input(self, game_with_gamepad):
        """When gamepad_enabled=False, stick input should be ignored."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Disable gamepad
        game.settings.gamepad_enabled = False

        # Try to move left stick
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.MAIN_MENU)

        # Should return None (ignored)
        assert action is None

    def test_reenable_gamepad_restores_input(self, game_with_gamepad):
        """Re-enabling gamepad should restore input handling."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Disable then re-enable
        game.settings.gamepad_enabled = False
        game.settings.gamepad_enabled = True

        # Try button press
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        action = gamepad.handle_button_event(button_event, InputContext.GAMEPLAY)

        # Should work now
        assert action == InputAction.WAIT


class TestDeadzoneSetting:
    """Test changing gamepad_deadzone during gameplay."""

    def test_default_deadzone_filters_small_input(self, game_with_gamepad):
        """Default deadzone (15%) should filter small stick input."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # 10% deflection (below 15% deadzone)
        small_value = int(32768 * 0.1)
        analog.update_left_stick(x=small_value, y=0)

        # Should be filtered to zero
        norm_x, norm_y = analog.apply_scaled_radial_deadzone(small_value, 0)
        assert norm_x == 0.0
        assert norm_y == 0.0

    def test_increase_deadzone_filters_more(self, game_with_gamepad):
        """Increasing deadzone should filter larger inputs."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Change deadzone to 30%
        game.settings.gamepad_deadzone = 0.30
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify setting was applied
        assert analog.deadzone == 0.30

        # 25% deflection (below new 30% deadzone)
        medium_value = int(32768 * 0.25)
        norm_x, norm_y = analog.apply_scaled_radial_deadzone(medium_value, 0)

        # Should be filtered to zero
        assert norm_x == 0.0

    def test_decrease_deadzone_allows_more(self, game_with_gamepad):
        """Decreasing deadzone should allow smaller inputs."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Change deadzone to 5%
        game.settings.gamepad_deadzone = 0.05
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify setting was applied
        assert analog.deadzone == 0.05

        # 10% deflection (above new 5% deadzone)
        small_value = int(32768 * 0.1)
        norm_x, norm_y = analog.apply_scaled_radial_deadzone(small_value, 0)

        # Should NOT be filtered to zero
        assert norm_x > 0.0


class TestThresholdSetting:
    """Test changing gamepad_threshold during gameplay."""

    def test_default_threshold_requires_movement(self, game_with_gamepad):
        """Default threshold (30%) should require significant deflection for movement."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # 25% deflection (below 30% threshold)
        medium_value = int(32768 * 0.25)
        dx, dy = analog.analog_to_8way(medium_value, 0)

        # Should return no movement
        assert dx == 0
        assert dy == 0

    def test_increase_threshold_requires_more(self, game_with_gamepad):
        """Increasing threshold should require larger deflection."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Change threshold to 50%
        game.settings.gamepad_threshold = 0.50
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify setting was applied
        assert analog.threshold == 0.50

        # 40% deflection (below new 50% threshold)
        large_value = int(32768 * 0.4)
        dx, dy = analog.analog_to_8way(large_value, 0)

        # Should return no movement
        assert dx == 0

    def test_decrease_threshold_allows_less(self, game_with_gamepad):
        """Decreasing threshold should allow smaller deflection to trigger movement."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Change threshold to 10% (very low)
        game.settings.gamepad_threshold = 0.10
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify setting was applied
        assert analog.threshold == 0.10

        # 30% deflection (above 15% deadzone)
        # After deadzone rescaling: (0.30 - 0.15) / (1 - 0.15) = 0.15 / 0.85 = 0.176
        # This is above the 10% threshold
        medium_value = int(32768 * 0.30)
        dx, dy = analog.analog_to_8way(medium_value, 0)

        # Should return movement
        assert dx == 1  # Right


class TestDirectionLockingSetting:
    """Test changing gamepad_direction_locking during gameplay."""

    def test_direction_locking_enabled_by_default(self, game_with_gamepad):
        """Direction locking should be enabled by default."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        assert analog.direction_locking is True

    def test_disable_direction_locking(self, game_with_gamepad):
        """Disabling direction locking should allow direction changes while held."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Disable direction locking
        game.settings.gamepad_direction_locking = False
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify setting was applied
        assert analog.direction_locking is False

    def test_reenable_direction_locking(self, game_with_gamepad):
        """Re-enabling direction locking should restore the feature."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Disable then re-enable
        game.settings.gamepad_direction_locking = False
        input_handler.gamepad_handler.sync_settings_to_analog_handler()
        assert analog.direction_locking is False

        game.settings.gamepad_direction_locking = True
        input_handler.gamepad_handler.sync_settings_to_analog_handler()
        assert analog.direction_locking is True


class TestSwapSticksSetting:
    """Test changing gamepad_swap_sticks during gameplay."""

    def test_swap_sticks_disabled_by_default(self, game_with_gamepad):
        """Swap sticks should be disabled by default."""
        game, input_handler, _ = game_with_gamepad

        assert game.settings.gamepad_swap_sticks is False

    def test_left_stick_moves_player_normally(self, game_with_gamepad, mock_time):
        """With swap disabled, left stick should move player."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Ensure swap is off
        game.settings.gamepad_swap_sticks = False

        # Move left stick right
        analog.update_left_stick(x=32000, y=0)

        # Start settling period (first call)
        analog.get_left_stick_movement_gameplay(game.turn)
        mock_time.advance(SETTLING_PERIOD_SEC)

        # Get gameplay movement after settling
        movement = analog.get_left_stick_movement_gameplay(game.turn)

        assert movement is not None
        assert movement == (1, 0)  # Right

    def test_right_stick_moves_player_when_swapped(self, game_with_gamepad, mock_time):
        """With swap enabled, right stick should move player."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Move right stick right
        analog.update_right_stick(x=32000, y=0)

        # Start settling period (first call)
        analog.get_right_stick_movement_gameplay(game.turn)
        mock_time.advance(SETTLING_PERIOD_SEC)

        # Get gameplay movement from RIGHT stick (which is now movement)
        movement = analog.get_right_stick_movement_gameplay(game.turn)

        assert movement is not None
        assert movement == (1, 0)  # Right

    def test_swap_sticks_affects_menu_navigation(self, game_with_gamepad):
        """Swap sticks should affect which stick navigates menus."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Right stick should now navigate menus
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTY, value=-32000  # Up
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.MAIN_MENU)

        assert action == InputAction.NAVIGATE_UP

    def test_swap_sticks_affects_look_mode_trigger(self, game_with_gamepad):
        """Swap sticks should affect which stick triggers look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # When swapped, LEFT stick triggers look mode
        # Move left stick to trigger look mode (normally right stick does this)
        analog.update_left_stick(x=32000, y=0)

        # Check magnitude (left stick should now be "look" stick)
        look_magnitude = analog.get_left_stick_magnitude()
        assert look_magnitude > GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD


class TestSettingsSyncMethod:
    """Test the sync_settings_to_analog_handler method directly."""

    def test_sync_updates_deadzone(self, game_with_gamepad):
        """sync_settings_to_analog_handler should update deadzone."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        original = analog.deadzone
        game.settings.gamepad_deadzone = 0.25
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        assert analog.deadzone == 0.25
        assert analog.deadzone != original

    def test_sync_updates_threshold(self, game_with_gamepad):
        """sync_settings_to_analog_handler should update threshold."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        original = analog.threshold
        game.settings.gamepad_threshold = 0.4
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        assert analog.threshold == 0.4
        assert analog.threshold != original

    def test_sync_updates_direction_locking(self, game_with_gamepad):
        """sync_settings_to_analog_handler should update direction_locking."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        assert analog.direction_locking is True
        game.settings.gamepad_direction_locking = False
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        assert analog.direction_locking is False

    def test_sync_ignores_invalid_values(self, game_with_gamepad):
        """sync_settings_to_analog_handler should ignore invalid/mock values."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        original_deadzone = analog.deadzone

        # Set invalid value (string instead of float)
        game.settings.gamepad_deadzone = "invalid"
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Should keep original value
        assert analog.deadzone == original_deadzone

    def test_sync_is_called_on_axis_event(self, game_with_gamepad):
        """Axis events should trigger settings sync automatically."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler
        gamepad = input_handler.gamepad_handler

        # Change setting
        game.settings.gamepad_deadzone = 0.35

        # Axis event should trigger sync
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=100
        )
        gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        # Setting should now be synced
        assert analog.deadzone == 0.35


class TestSettingsPersistenceAcrossContexts:
    """Test that settings remain applied across context switches."""

    def test_deadzone_persists_gameplay_to_menu(self, game_with_gamepad):
        """Deadzone setting should persist from gameplay to menu context."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Change deadzone in gameplay context
        game.settings.gamepad_deadzone = 0.25
        input_handler.gamepad_handler.sync_settings_to_analog_handler()

        # Verify in gameplay
        assert analog.deadzone == 0.25

        # Open inventory (switch context)
        game.show_inventory = True

        # Deadzone should still be 0.25
        assert analog.deadzone == 0.25

    def test_swap_sticks_persists_across_contexts(self, game_with_gamepad):
        """Swap sticks setting should work consistently across menu contexts."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Test in MAIN_MENU context - right stick should navigate when swapped
        axis_event_up = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTY, value=-32000
        )
        action1 = gamepad.handle_axis_event(axis_event_up, InputContext.MAIN_MENU)
        assert action1 == InputAction.NAVIGATE_UP

        # Test in SETTINGS_MENU context - same setting should apply
        axis_event_down = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTY, value=32000
        )
        action2 = gamepad.handle_axis_event(axis_event_down, InputContext.SETTINGS_MENU)
        assert action2 == InputAction.NAVIGATE_DOWN
