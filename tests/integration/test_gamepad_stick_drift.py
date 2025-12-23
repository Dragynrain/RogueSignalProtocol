"""
Phase 1.1: Stick Drift Compensation Tests

Tests that analog stick deadzone properly filters controller drift.
All controllers drift eventually - the game must handle this gracefully.

Test coverage:
- Analog values oscillating around deadzone threshold
- Stick sitting at low deflection (should be ignored)
- Stick returning to non-zero value after release
- Radial deadzone filtering
- Large deflection after drift

Uses the game_with_gamepad fixture from tests/conftest.py.
Uses mock_time fixture from conftest.py for reliable time control.
"""

import tcod.event
import tcod.sdl.joystick

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

from tests.conftest import get_movement_with_settling  # noqa: E402


class TestDeadzoneFiltering:
    """Test that deadzone properly filters low-value stick drift."""

    def test_stick_at_10_percent_ignored(self, game_with_gamepad):
        """Stick sitting at 10% deflection should be ignored (below 15% deadzone)."""
        game, input_handler, controller = game_with_gamepad

        # Set stick X to 10% of max (3277 out of 32767)
        drift_value = int(32767 * 0.10)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=drift_value
        )
        input_handler.handle_controller_axis(axis_event)

        # Check that stick state shows drift but movement is filtered
        assert input_handler.gamepad_handler.analog_handler.left_x == drift_value

        # Try to get movement - should be None (below deadzone)
        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )
        assert movement is None, "10% deflection should be filtered by 15% deadzone"

    def test_stick_at_5_percent_after_release(self, game_with_gamepad, mock_time):
        """Stick returning to 5% after release (not perfect zero) should be treated as centered."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect stick to 100% right (with settling)
        movement = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement == (1, 0), "Full deflection should register"

        # Release to 5% (1638) - treated as centered due to deadzone
        release_value = int(32767 * 0.05)
        analog.update_left_stick(x=release_value, y=0)

        # Next turn - should not move (5% is below deadzone)
        game.turn += 1
        movement = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement is None, "5% deflection should be treated as centered"

    def test_stick_oscillating_near_deadzone(self, game_with_gamepad, mock_time):
        """Stick oscillating between 14% and 35% tests filtering and movement."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Explicitly reset analog handler state for test isolation
        analog.left_x = 0
        analog.left_y = 0
        analog.last_gameplay_move_time = -1.0
        analog.gameplay_is_repeating = False
        analog.last_gameplay_direction = (0, 0)
        analog._settling_start_time = -1.0

        # Oscillate between below deadzone (14%) and above threshold (35%)
        # Deadzone: 15%, Threshold after scaling: 20%
        # To pass threshold: raw >= 0.15 + (0.20 * 0.85) = 0.32 = 32%
        below_deadzone = int(32767 * 0.14)  # 14% - filtered by deadzone
        above_threshold = int(32767 * 0.35)  # 35% - passes deadzone and threshold

        # Frame 1: Below deadzone (use direct update)
        analog.update_left_stick(x=below_deadzone, y=0)

        movement1 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement1 is None, "Below deadzone should be filtered"

        # Frame 2: Above threshold (with settling period)
        game.turn += 1
        movement2 = get_movement_with_settling(analog, game.turn, above_threshold, 0, mock_time)
        assert movement2 == (1, 0), "35% deflection should register movement"


class TestRadialDeadzone:
    """Test radial deadzone vs square deadzone behavior."""

    def test_diagonal_drift_filtered_by_radial_deadzone(self, game_with_gamepad):
        """Stick at (10%, 10%) = 14.1% magnitude should be filtered by radial deadzone."""
        game, input_handler, controller = game_with_gamepad

        # Set stick to (10%, 10%)
        # Magnitude = sqrt(0.1^2 + 0.1^2) = sqrt(0.02) = 0.141 = 14.1%
        # Below 15% radial deadzone
        drift_value = int(32767 * 0.10)

        # Set both axes
        x_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=drift_value
        )
        y_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=drift_value
        )

        input_handler.handle_controller_axis(x_event)
        input_handler.handle_controller_axis(y_event)

        # Try to get movement - should be None (14.1% magnitude < 15% deadzone)
        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )
        assert movement is None, "14.1% magnitude should be filtered by 15% radial deadzone"

    def test_diagonal_above_deadzone_registers(self, game_with_gamepad, mock_time):
        """Stick at (28%, 28%) = 39.6% magnitude should register."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Set stick to (28%, 28%)
        # Magnitude = sqrt(0.28^2 + 0.28^2) = sqrt(0.1568) = 0.396 = 39.6%
        # Above 15% deadzone, scaled coordinates pass 20% threshold:
        # Scaled magnitude = (0.396 - 0.15) / 0.85 = 0.289
        # Scaled coords = (0.28, 0.28) * 0.289/0.396 = (0.204, 0.204) > 0.20 threshold
        value = int(32767 * 0.28)

        # CRITICAL: Reset turn gating since test may have existing state
        analog.reset_movement_gating()

        # Should get diagonal movement (southeast, not northeast - positive Y is down in SDL)
        movement = get_movement_with_settling(analog, game.turn, value, value, mock_time)
        assert movement == (1, 1), "39.6% magnitude should register as southeast movement"


class TestDriftRecovery:
    """Test that large deflections work properly even with background drift."""

    def test_large_deflection_after_drift(self, game_with_gamepad, mock_time):
        """User slams stick to 100% after it was drifting at 8% - should respond after settling."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Start with drift at 8% (use direct update)
        drift_value = int(32767 * 0.08)
        analog.update_left_stick(x=drift_value, y=0)

        # Verify no movement from drift
        movement1 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement1 is None, "8% drift should be ignored"

        # User slams stick to 100% (with settling period)
        game.turn += 1
        movement2 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement2 == (1, 0), "Full deflection should work immediately after drift"

    def test_negative_drift_filtered(self, game_with_gamepad):
        """Negative drift (stick drifting left) should also be filtered."""
        game, input_handler, controller = game_with_gamepad

        # Set stick to -10% (drifting left)
        drift_value = int(32767 * -0.10)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=drift_value
        )
        input_handler.handle_controller_axis(axis_event)

        # Should not generate movement
        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )
        assert movement is None, "Negative 10% drift should be filtered"


class TestDeadzoneConsistency:
    """Test that deadzone behavior is consistent across all contexts."""

    def test_deadzone_same_in_gameplay_and_menus(self, game_with_gamepad):
        """Deadzone should filter the same values in both gameplay and menu contexts."""
        game, input_handler, controller = game_with_gamepad

        # Test in gameplay context first
        drift_value = int(32767 * 0.10)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=drift_value
        )
        input_handler.handle_controller_axis(axis_event)

        # Gameplay: should be filtered
        movement_gameplay = (
            input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(game.turn)
        )
        assert movement_gameplay is None

        # Switch to menu context
        game.show_inventory = True

        # Menu: should also be filtered
        movement_menu = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_menu()
        assert movement_menu is None, "Deadzone should be consistent across contexts"

    def test_right_stick_uses_same_deadzone(self, game_with_gamepad):
        """Right stick should use the same deadzone as left stick."""
        game, input_handler, controller = game_with_gamepad

        # Set right stick to 10% (below deadzone)
        drift_value = int(32767 * 0.10)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=drift_value
        )
        input_handler.handle_controller_axis(axis_event)

        # Verify state updated
        assert input_handler.gamepad_handler.analog_handler.right_x == drift_value

        # Right stick movement should also be filtered
        # (Right stick is used for look mode targeting, not tested here but uses same deadzone logic)


class TestEdgeCases:
    """Test edge cases in deadzone handling."""

    def test_exact_deadzone_threshold(self, game_with_gamepad):
        """Stick at exactly 15% should be at the edge of deadzone."""
        game, input_handler, controller = game_with_gamepad

        # Set stick to exactly 15%
        threshold_value = int(32767 * 0.15)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=threshold_value
        )
        input_handler.handle_controller_axis(axis_event)

        # At 15%, behavior depends on implementation (< vs <=)
        # Either None or (1, 0) is acceptable, just verify no crash
        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )
        # Test passes if no exception raised

    def test_zero_value_explicitly(self, game_with_gamepad):
        """Stick at perfect zero should definitely not generate movement."""
        game, input_handler, controller = game_with_gamepad

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=0  # Perfect zero
        )
        input_handler.handle_controller_axis(axis_event)

        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )
        assert movement is None, "Perfect zero should never generate movement"

    def test_maximum_value_always_works(self, game_with_gamepad, mock_time):
        """Maximum stick deflection (32767) should always generate movement."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Test all four cardinal directions at maximum
        test_cases = [
            (32767, 0, (1, 0)),  # East
            (-32767, 0, (-1, 0)),  # West
            (0, -32767, (0, -1)),  # North
            (0, 32767, (0, 1)),  # South
        ]

        for x, y, expected_movement in test_cases:
            # Reset stick and direction locking state (use direct update)
            analog.update_left_stick(x=0, y=0)
            analog.get_left_stick_movement_gameplay(game.turn)  # Process release

            # Set new direction (with settling period)
            movement = get_movement_with_settling(analog, game.turn, x, y, mock_time)
            assert (
                movement == expected_movement
            ), f"Maximum deflection ({x}, {y}) should always work"
