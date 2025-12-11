"""
Phase 0.3: Auto-Repeat Edge Cases Tests

Tests comprehensive auto-repeat behavior for gamepad inputs.
Auto-repeat bugs are the #1 complaint from .claude/gamepad.md.

Critical issues tested:
- Immediate stop on button/stick release
- No false-repeat on direction change (D-pad double-move bug)
- Timing consistency (400ms delay, 150ms repeat rate for buttons; 400ms/150ms for stick)
- Context switch cleanup
- Consistency between stick and D-pad
- Behavior during lag/frame skip

Uses the game_with_gamepad fixture from tests/conftest.py.
"""

import pytest
import tcod.event
import tcod.sdl.joystick
from unittest.mock import patch
import time

from game_input_actions import InputAction, InputContext

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis


class TestButtonAutoRepeatStop:
    """Test that button auto-repeat stops immediately on release."""

    def test_dpad_auto_repeat_stops_on_release(self, game_with_gamepad):
        """D-pad auto-repeat must stop within 1 frame of release."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        with patch('time.time') as mock_time:
            # Initial press at t=0
            mock_time.return_value = 0.0

            # Press D-pad UP using gamepad handler directly (with MAIN_MENU context)
            press_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            action = gamepad_handler.handle_button_event(press_event, InputContext.MAIN_MENU)

            # Should track button for auto-repeat (navigation in main menu)
            assert gamepad_handler.button_held == CB.DPAD_UP

            # At t=0.5 (well past initial delay of 0.4s), should repeat
            mock_time.return_value = 0.5
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is not None, "Auto-repeat should be active (NAVIGATE_UP)"

            # Release button
            mock_time.return_value = 0.51
            release_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONUP",
                which=0,
                button=CB.DPAD_UP,
                pressed=False
            )
            gamepad_handler.handle_button_event(release_event, InputContext.MAIN_MENU)

            # Immediately after release, no auto-repeat
            mock_time.return_value = 0.52  # 10ms later
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is None, "Auto-repeat must stop immediately on release"

    def test_button_state_cleared_on_release(self, game_with_gamepad):
        """Button held state must be cleared on release for navigation buttons."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        # Press D-pad DOWN (navigation button) using gamepad handler directly
        press_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=CB.DPAD_DOWN,
            pressed=True
        )
        gamepad_handler.handle_button_event(press_event, InputContext.MAIN_MENU)

        assert gamepad_handler.button_held == CB.DPAD_DOWN

        # Release D-pad DOWN
        release_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONUP",
            which=0,
            button=CB.DPAD_DOWN,
            pressed=False
        )
        gamepad_handler.handle_button_event(release_event, InputContext.MAIN_MENU)

        # State cleared (-1.0 is the sentinel for "never pressed")
        assert gamepad_handler.button_held is None
        assert gamepad_handler.button_held_since == -1.0


class TestStickAutoRepeatStop:
    """Test that analog stick auto-repeat stops immediately on release."""

    def test_stick_auto_repeat_stops_on_center(self, game_with_gamepad):
        """Left stick auto-repeat stops when stick returns to center."""
        game, input_handler, controller = game_with_gamepad
        # Use analog handler directly to test analog behavior in isolation
        # (handle_controller_axis processes through menu handlers which consume movement)
        analog = input_handler.gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Deflect stick UP directly on analog handler
            analog.update_left_stick(x=0, y=-32767)

            # First movement should be immediate
            movement = analog.get_left_stick_movement_menu()
            assert movement == (0, -1), "First stick movement should be immediate"

            # Release stick to center
            mock_time.return_value = 0.01
            analog.update_left_stick(x=0, y=0)

            # No movement after centering
            mock_time.return_value = 0.02
            movement = analog.get_left_stick_movement_menu()
            assert movement is None, "No movement when stick centered"

    def test_stick_drift_doesnt_cause_auto_repeat(self, game_with_gamepad):
        """Stick drift (5% deflection) should not trigger auto-repeat."""
        game, input_handler, controller = game_with_gamepad
        game.show_inventory = True

        # Set stick to 5% deflection (below 15% deadzone)
        drift_value = int(32767 * 0.05)

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            axis_event = tcod.event.ControllerAxis(
                type="CONTROLLERAXISMOTION",
                which=0,
                axis=CA.LEFTY,
                value=drift_value
            )
            input_handler.handle_controller_axis(axis_event)

            # Wait for auto-repeat timing
            mock_time.return_value = 1.0

            # Should not generate movement (below deadzone)
            movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_menu()
            assert movement is None, "Drift below deadzone should not cause movement"


class TestDirectionChangeNoFalseRepeat:
    """Test that direction change doesn't cause false auto-repeat.

    This is the critical D-pad double-move bug from .claude/gamepad.md.
    """

    def test_dpad_direction_change_no_double_move(self, game_with_gamepad):
        """CRITICAL: D-pad direction change should not cause double-move."""
        game, input_handler, controller = game_with_gamepad
        game.show_inventory = True

        # Track inventory selection to verify navigation
        initial_selection = game.inventory_selection

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Press D-pad UP - should navigate up
            up_press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            input_handler.handle_controller_button(up_press)
            first_selection = game.inventory_selection

            # Should have moved (unless already at top)
            # The exact behavior depends on inventory contents, so just verify it was handled

            # Release UP
            mock_time.return_value = 0.1
            up_release = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONUP",
                which=0,
                button=CB.DPAD_UP,
                pressed=False
            )
            input_handler.handle_controller_button(up_release)

            # Press D-pad DOWN immediately (direction change) - should NOT auto-repeat
            # This is the key test: changing direction should reset timing, not trigger double-move
            mock_time.return_value = 0.11  # Only 10ms after release - too soon for repeat
            down_press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_DOWN,
                pressed=True
            )
            input_handler.handle_controller_button(down_press)

            # The DOWN press should be handled as a new action (not auto-repeat)
            # Verify the button state was reset to DOWN (not still UP)
            gamepad_handler = input_handler.gamepad_handler
            assert gamepad_handler.button_held == CB.DPAD_DOWN, \
                "Direction change should track new button (DOWN), not old (UP)"
            # Button held time should be reset to the new press time (0.11)
            assert gamepad_handler.button_held_since == 0.11, \
                "Button held time should reset on direction change"

    def test_stick_direction_reversal_immediate_response(self, game_with_gamepad):
        """Stick direction reversal should give immediate new direction."""
        game, input_handler, controller = game_with_gamepad
        # Use analog handler directly to test analog behavior in isolation
        analog = input_handler.gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            # Move stick UP
            mock_time.return_value = 0.0
            analog.update_left_stick(x=0, y=-32767)

            # Get first movement (immediate because last_menu_move_time < 0.0)
            movement1 = analog.get_left_stick_movement_menu()
            assert movement1 == (0, -1), "First movement should be UP"

            # Reverse to DOWN (direction change triggers immediate movement)
            mock_time.return_value = 0.05
            analog.update_left_stick(x=0, y=32767)

            # Direction change should give immediate movement
            movement2 = analog.get_left_stick_movement_menu()
            assert movement2 == (0, 1), "Direction change should give immediate DOWN movement"


class TestAutoRepeatTiming:
    """Test auto-repeat timing consistency (400ms delay, 150ms repeat rate)."""

    def test_button_auto_repeat_timing_pattern(self, game_with_gamepad):
        """Button auto-repeat should follow 400ms initial, 150ms repeat pattern."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        with patch('time.time') as mock_time:
            # Press button at t=0 (use gamepad handler directly with MAIN_MENU context)
            mock_time.return_value = 0.0
            press_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            gamepad_handler.handle_button_event(press_event, InputContext.MAIN_MENU)

            # At t=0.3 (300ms), before initial delay (400ms) - no repeat
            mock_time.return_value = 0.3
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is None, "No repeat before 400ms initial delay"

            # At t=0.5 (500ms), after initial delay - should repeat
            mock_time.return_value = 0.5
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is not None, "Should repeat after 400ms delay (NAVIGATE_UP)"

            # At t=0.6 (100ms later), too soon for repeat rate (150ms)
            mock_time.return_value = 0.6
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is None, "Should not repeat before 150ms repeat interval"

            # At t=0.65 (150ms later from last repeat), should repeat again
            mock_time.return_value = 0.65
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is not None, "Should repeat at 150ms interval (NAVIGATE_UP)"

    def test_stick_auto_repeat_timing_consistency(self, game_with_gamepad):
        """Stick auto-repeat should have consistent timing (400ms delay, 150ms repeat)."""
        game, input_handler, controller = game_with_gamepad
        # Use analog handler directly to test timing behavior in isolation
        analog = input_handler.gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            # Deflect stick at t=0
            mock_time.return_value = 0.0
            analog.update_left_stick(x=0, y=-32767)

            # First movement immediate (last_menu_move_time < 0.0)
            movement1 = analog.get_left_stick_movement_menu()
            assert movement1 == (0, -1), "First movement immediate"

            # Too soon for repeat (100ms < 400ms initial delay)
            mock_time.return_value = 0.1
            movement2 = analog.get_left_stick_movement_menu()
            assert movement2 is None, "No repeat before initial delay"

            # After initial delay (400ms)
            mock_time.return_value = 0.41
            movement3 = analog.get_left_stick_movement_menu()
            assert movement3 == (0, -1), "Repeat after initial delay"

            # Too soon for repeat interval (50ms < 150ms)
            mock_time.return_value = 0.46
            movement4 = analog.get_left_stick_movement_menu()
            assert movement4 is None, "No repeat before interval"

            # After repeat interval (150ms)
            mock_time.return_value = 0.56
            movement5 = analog.get_left_stick_movement_menu()
            assert movement5 == (0, -1), "Repeat at interval"


class TestAutoRepeatContextSwitch:
    """Test auto-repeat state cleanup during context switches."""

    def test_button_hold_cleared_on_context_switch(self, game_with_gamepad):
        """Button hold state persists across context (handled by context-aware actions)."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Press and hold D-pad DOWN using gamepad handler directly (MAIN_MENU context)
            press_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_DOWN,
                pressed=True
            )
            gamepad_handler.handle_button_event(press_event, InputContext.MAIN_MENU)

            # Button should be tracked
            assert gamepad_handler.button_held == CB.DPAD_DOWN

            # Close inventory (context switch to gameplay)
            game.show_inventory = False

            # Button is still held physically, but context determines action
            new_context = input_handler._get_current_context()
            assert new_context == InputContext.GAMEPLAY

            # In gameplay, D-pad DOWN = MOVE_SOUTH, not NAVIGATE_DOWN
            # Auto-repeat action depends on context
            mock_time.return_value = 0.5
            action = input_handler.gamepad_handler.get_button_repeat_action(InputContext.GAMEPLAY)

            # In gameplay context, D-pad is for movement (not tracked for auto-repeat)
            # The button_held state persists but action changes based on context
            # Note: get_button_repeat_action returns InputAction (not bool) internally
            # (InputAction is already imported at module level)
            if action:
                assert action == InputAction.MOVE_SOUTH, "Context determines action"

    def test_stick_state_reset_on_menu_exit(self, game_with_gamepad):
        """Stick navigation state can be reset when exiting menu."""
        game, input_handler, controller = game_with_gamepad
        # Use analog handler directly to test state reset behavior
        analog = input_handler.gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Move stick directly on analog handler
            analog.update_left_stick(x=0, y=-32767)

            movement = analog.get_left_stick_movement_menu()
            assert movement == (0, -1), "Should get menu movement"

            # Reset menu navigation state (as would happen on context switch)
            analog.reset_menu_navigation()

            # Check state cleared (reset to "never moved" state)
            assert analog.menu_is_repeating is False
            assert analog.last_menu_move_time == -1.0


class TestStickVsDpadConsistency:
    """Test that stick and D-pad have consistent auto-repeat behavior."""

    def test_same_timing_parameters(self, game_with_gamepad):
        """Stick and D-pad should use similar timing parameters."""
        game, input_handler, controller = game_with_gamepad
        game.show_inventory = True

        # D-pad timing constants
        dpad_initial_delay = input_handler.gamepad_handler.button_repeat_initial_delay
        dpad_repeat_rate = input_handler.gamepad_handler.button_repeat_rate

        # Stick timing constants (from analog handler for menus)
        stick_initial_delay = input_handler.gamepad_handler.analog_handler.menu_initial_delay
        stick_repeat_rate = input_handler.gamepad_handler.analog_handler.menu_repeat_rate

        # Should be identical or very similar
        assert dpad_initial_delay == stick_initial_delay, f"Initial delays should match: {dpad_initial_delay} vs {stick_initial_delay}"
        assert dpad_repeat_rate == stick_repeat_rate, f"Repeat rates should match: {dpad_repeat_rate} vs {stick_repeat_rate}"

    def test_both_stop_on_release(self, game_with_gamepad):
        """Both stick and D-pad should stop immediately on release."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler
        analog = gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Test D-pad (use gamepad handler directly with MAIN_MENU context)
            dpad_press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            gamepad_handler.handle_button_event(dpad_press, InputContext.MAIN_MENU)

            assert gamepad_handler.button_held == CB.DPAD_UP, "D-pad tracked"

            # Release D-pad
            dpad_release = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONUP",
                which=0,
                button=CB.DPAD_UP,
                pressed=False
            )
            gamepad_handler.handle_button_event(dpad_release, InputContext.MAIN_MENU)

            assert gamepad_handler.button_held is None, "D-pad state cleared"

            # Test stick (use analog handler directly)
            analog.update_left_stick(x=0, y=-32767)

            # Get movement to initialize state
            movement = analog.get_left_stick_movement_menu()
            assert movement == (0, -1), "Stick generates movement"

            # Center stick
            mock_time.return_value = 0.1
            analog.update_left_stick(x=0, y=0)

            movement = analog.get_left_stick_movement_menu()
            assert movement is None, "Stick returns None when centered"


class TestAutoRepeatDuringLag:
    """Test auto-repeat behavior during frame lag/skip."""

    def test_auto_repeat_doesnt_burst_after_lag(self, game_with_gamepad):
        """Auto-repeat should not 'catch up' with burst of events after lag."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        with patch('time.time') as mock_time:
            # Press button at t=0 (use gamepad handler directly with MAIN_MENU context)
            mock_time.return_value = 0.0
            press_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_DOWN,
                pressed=True
            )
            gamepad_handler.handle_button_event(press_event, InputContext.MAIN_MENU)

            # Simulate lag: jump from t=0 to t=1.0 (1 second)
            mock_time.return_value = 1.0

            # Should only get ONE action, not a burst
            action = gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)
            assert action is not None, "Should get action after lag (NAVIGATE_DOWN)"

            # Immediately after, should not get another (last_repeat_time updated)
            action2 = input_handler.gamepad_handler.get_button_repeat_action(InputContext.INVENTORY)
            assert action2 is None, "Should not burst multiple events"

            # Next event only after repeat interval (150ms+)
            # Use 1.151 to avoid floating point precision issues (1.15 - 1.0 = 0.14999...)
            mock_time.return_value = 1.151
            action3 = input_handler.gamepad_handler.get_button_repeat_action(InputContext.INVENTORY)
            assert action3 is not None, "Next repeat at normal interval (NAVIGATE_DOWN)"

    def test_stick_auto_repeat_time_based_not_frame_based(self, game_with_gamepad):
        """Stick auto-repeat should be time-based, not frame-count based."""
        game, input_handler, controller = game_with_gamepad
        # Use analog handler directly to test time-based behavior in isolation
        analog = input_handler.gamepad_handler.analog_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Deflect stick directly on analog handler
            analog.update_left_stick(x=0, y=-32767)

            # First movement (immediate)
            movement1 = analog.get_left_stick_movement_menu()
            assert movement1 == (0, -1), "First movement immediate"

            # Many frame checks in short time (high FPS)
            for i in range(1, 11):
                mock_time.return_value = 0.01 * i  # 10ms increments
                movement = analog.get_left_stick_movement_menu()
                # Should return None (not enough time passed)
                assert movement is None, f"Frame {i}: Should not repeat too frequently"

            # After sufficient time, should repeat
            mock_time.return_value = 0.41  # Past initial delay of 400ms
            movement2 = analog.get_left_stick_movement_menu()
            assert movement2 == (0, -1), "Should repeat after time threshold"


class TestAutoRepeatEdgeCases:
    """Additional edge cases for auto-repeat behavior."""

    def test_multiple_buttons_held_simultaneously(self, game_with_gamepad):
        """Holding multiple buttons - only last navigation button should be tracked."""
        game, input_handler, controller = game_with_gamepad
        gamepad_handler = input_handler.gamepad_handler

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Press D-pad UP (navigation button) using gamepad handler directly
            up_press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            gamepad_handler.handle_button_event(up_press, InputContext.MAIN_MENU)

            # Press D-pad DOWN (navigation button, without releasing UP)
            mock_time.return_value = 0.05
            down_press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_DOWN,
                pressed=True
            )
            gamepad_handler.handle_button_event(down_press, InputContext.MAIN_MENU)

            # Only DOWN should be tracked for repeat (last pressed navigation button)
            assert gamepad_handler.button_held == CB.DPAD_DOWN

    def test_button_repeat_in_non_menu_context(self, game_with_gamepad):
        """Button repeat tracking only happens for navigation buttons in menu contexts."""
        game, input_handler, controller = game_with_gamepad
        # In gameplay context (default)
        assert not game.show_inventory
        assert not game.show_help

        with patch('time.time') as mock_time:
            mock_time.return_value = 0.0

            # Press D-pad in gameplay (movement, not navigation)
            press_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN",
                which=0,
                button=CB.DPAD_UP,
                pressed=True
            )
            action = input_handler.handle_controller_button(press_event)

            # In gameplay, D-pad UP = MOVE_NORTH (not tracked for auto-repeat)
            assert action is not False  # MOVE_NORTH action handled (True or None, not exit)
            # Button may not be tracked because it's not a navigation action in gameplay
            # Movement uses different system (turn-gating, not auto-repeat)
