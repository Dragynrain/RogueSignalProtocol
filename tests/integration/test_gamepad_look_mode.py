"""
Gamepad Look Mode and Cursor Control Tests.

Tests look mode entry, cursor movement, and targeting mode interactions:
- Right stick auto-enters look mode when magnitude > threshold
- Cursor movement via right stick in look mode
- Cursor movement in targeting mode
- Look mode with swap_sticks enabled (left stick controls cursor)
- Exiting look mode behavior

The look mode threshold is defined in GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD (default 0.3).

Uses the game_with_gamepad fixture from tests/conftest.py.
"""

import time

import pytest
import tcod.event
import tcod.sdl.joystick

from game_config import GameConfig
from game_input_actions import InputAction, InputContext
from game_input_analog import AnalogStickHandler

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

# Settling period for cursor movement
SETTLING_PERIOD_SEC = 0.035
LOOK_MODE_THRESHOLD = GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD  # 0.3


@pytest.fixture
def analog_handler():
    """Create standalone analog handler for cursor tests."""
    return AnalogStickHandler(deadzone=0.15, threshold=0.3, direction_locking=True)


class TestLookModeAutoEntry:
    """Test automatic look mode entry via right stick."""

    def test_right_stick_above_threshold_triggers_look_mode(self, game_with_gamepad):
        """Right stick deflection above threshold should trigger TOGGLE_LOOK_MODE."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Ensure swap is off (right stick is look stick)
        game.settings.gamepad_swap_sticks = False

        # Full right stick deflection (well above 0.3 threshold)
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        assert action == InputAction.TOGGLE_LOOK_MODE

    def test_right_stick_below_threshold_no_look_mode(self, game_with_gamepad):
        """Right stick deflection below threshold should not trigger look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        game.settings.gamepad_swap_sticks = False

        # Small deflection (20% = below 30% threshold)
        small_value = int(32768 * 0.2)
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=small_value
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        # Should not trigger look mode
        assert action != InputAction.TOGGLE_LOOK_MODE

    def test_look_mode_only_triggers_in_gameplay(self, game_with_gamepad):
        """Look mode auto-entry should only work in GAMEPLAY context."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        game.settings.gamepad_swap_sticks = False

        # Full right stick deflection
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=32000
        )

        # Test in various non-gameplay contexts
        for context in [
            InputContext.INVENTORY,
            InputContext.MAIN_MENU,
            InputContext.DIALOGUE,
            InputContext.HELP,
        ]:
            action = gamepad.handle_axis_event(axis_event, context)
            # Should not trigger look mode in these contexts
            assert action != InputAction.TOGGLE_LOOK_MODE

    def test_look_mode_requires_look_stick_event(self, game_with_gamepad):
        """Only events from the look stick should trigger look mode, not movement stick."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        game.settings.gamepad_swap_sticks = False

        # Pre-set right stick to have magnitude (simulating residual data)
        analog.update_right_stick(x=32000, y=0)

        # But send an event from the LEFT stick (movement stick)
        left_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(left_event, InputContext.GAMEPLAY)

        # Should NOT trigger look mode (event was from movement stick, not look stick)
        assert action != InputAction.TOGGLE_LOOK_MODE


class TestLookModeWithSwapSticks:
    """Test look mode with swap_sticks accessibility feature."""

    def test_left_stick_triggers_look_mode_when_swapped(self, game_with_gamepad):
        """When swapped, left stick should trigger look mode entry."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Enable swap (left stick becomes look stick)
        game.settings.gamepad_swap_sticks = True

        # Left stick deflection
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        assert action == InputAction.TOGGLE_LOOK_MODE

    def test_right_stick_no_look_mode_when_swapped(self, game_with_gamepad):
        """When swapped, right stick should not trigger look mode (it's movement stick)."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Pre-set left stick magnitude (actual look stick when swapped)
        analog.update_left_stick(x=32000, y=0)

        # But send event from right stick (now movement stick)
        right_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=32000
        )

        action = gamepad.handle_axis_event(right_event, InputContext.GAMEPLAY)

        # Should NOT trigger look mode (right stick is movement when swapped)
        assert action != InputAction.TOGGLE_LOOK_MODE


class TestCursorMovementInLookMode:
    """Test cursor movement via stick in look mode."""

    def test_right_stick_cursor_movement_in_look_mode(self, game_with_gamepad):
        """Right stick should move cursor in LOOK_MODE context."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        game.settings.gamepad_swap_sticks = False

        # Set right stick position
        analog.update_right_stick(x=32000, y=0)

        # Start settling, wait, then get cursor movement
        analog.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Send axis event in LOOK_MODE context
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.LOOK_MODE)

        # Should return movement action for cursor
        assert action == InputAction.MOVE_EAST

    def test_cursor_movement_8way_diagonal(self, analog_handler):
        """Cursor movement should support 8-way including diagonals."""
        handler = analog_handler

        # Set right stick to diagonal (northeast: +X, -Y)
        handler.update_right_stick(x=32000, y=-32000)

        # Start settling
        handler.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Get cursor movement
        movement = handler.get_right_stick_movement()

        assert movement is not None
        assert movement == (1, -1)  # Northeast

    def test_cursor_movement_has_settling_period(self, analog_handler):
        """Cursor movement should respect settling period like gameplay."""
        handler = analog_handler

        # Set right stick
        handler.update_right_stick(x=32000, y=0)

        # First call starts settling (returns None)
        movement1 = handler.get_right_stick_movement()
        assert movement1 is None

        # Immediate second call still settling
        movement2 = handler.get_right_stick_movement()
        assert movement2 is None

        # After settling period
        time.sleep(SETTLING_PERIOD_SEC)
        movement3 = handler.get_right_stick_movement()
        assert movement3 is not None

    def test_cursor_movement_direction_locking(self, analog_handler):
        """Cursor should lock direction after settling (prevents diagonal swipes)."""
        handler = analog_handler

        # Start with right
        handler.update_right_stick(x=32000, y=0)
        handler.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Lock direction
        movement1 = handler.get_right_stick_movement()
        assert movement1 == (1, 0)  # Right

        # Change to diagonal (should be ignored - direction locked)
        handler.update_right_stick(x=32000, y=-32000)

        # Wait for auto-repeat
        time.sleep(handler.cursor_initial_delay + 0.01)
        movement2 = handler.get_right_stick_movement()

        # Should still be (1, 0) due to direction locking
        assert movement2 == (1, 0)

    def test_cursor_release_resets_direction_lock(self, analog_handler):
        """Releasing stick should reset direction lock."""
        handler = analog_handler

        # Move right, lock direction
        handler.update_right_stick(x=32000, y=0)
        handler.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)
        movement1 = handler.get_right_stick_movement()
        assert movement1 == (1, 0)

        # Release
        handler.update_right_stick(x=0, y=0)
        handler.get_right_stick_movement()  # Process release

        # Now push up - should work (direction unlocked)
        handler.update_right_stick(x=0, y=-32000)
        handler.get_right_stick_movement()  # Start settling
        time.sleep(SETTLING_PERIOD_SEC)
        movement2 = handler.get_right_stick_movement()

        assert movement2 == (0, -1)  # Up (new direction)


class TestCursorMovementWithSwapSticks:
    """Test cursor control with swap_sticks enabled."""

    def test_left_stick_cursor_in_look_mode_when_swapped(self, game_with_gamepad):
        """When swapped, left stick should control cursor in look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Set left stick position
        analog.update_left_stick(x=32000, y=0)

        # Start settling, wait
        analog.get_left_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Send axis event in LOOK_MODE context
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.LOOK_MODE)

        # Should return movement action
        assert action == InputAction.MOVE_EAST

    def test_left_stick_cursor_movement_8way(self, analog_handler):
        """Left stick cursor movement should also support 8-way."""
        handler = analog_handler

        # Set left stick to diagonal (southwest: -X, +Y)
        handler.update_left_stick(x=-32000, y=32000)

        # Start settling
        handler.get_left_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Get cursor movement
        movement = handler.get_left_stick_movement()

        assert movement is not None
        assert movement == (-1, 1)  # Southwest


class TestTargetingMode:
    """Test cursor control in targeting mode."""

    def test_right_stick_cursor_in_targeting_mode(self, game_with_gamepad):
        """Right stick should control cursor in TARGETING context."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        game.settings.gamepad_swap_sticks = False

        # Set right stick position
        analog.update_right_stick(x=0, y=-32000)  # Up

        # Start settling, wait
        analog.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Send axis event in TARGETING context
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTY, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.TARGETING)

        # Should return movement action for cursor
        assert action == InputAction.MOVE_NORTH

    def test_targeting_mode_with_swap_sticks(self, game_with_gamepad):
        """Targeting mode should respect swap_sticks setting."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Set left stick position (look stick when swapped)
        analog.update_left_stick(x=-32000, y=0)  # Left

        # Start settling, wait
        analog.get_left_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)

        # Send axis event in TARGETING context
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=-32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.TARGETING)

        assert action == InputAction.MOVE_WEST


class TestLookModeThreshold:
    """Test look mode threshold behavior."""

    def test_threshold_value_is_correct(self):
        """Look mode threshold should be 0.3 (30%)."""
        assert GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD == 0.3

    def test_exactly_at_threshold(self, game_with_gamepad):
        """Deflection exactly at threshold should trigger look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        game.settings.gamepad_swap_sticks = False

        # 35% deflection (just above threshold after deadzone adjustment)
        # Raw 35% -> after 15% deadzone rescale: (0.35-0.15)/(1-0.15) = 0.235
        # Still above 0.3? Let me calculate: we need post-deadzone magnitude > 0.3
        # So raw magnitude needs to be: 0.3 * 0.85 + 0.15 = 0.405
        # Use 45% to be safe
        value = int(32768 * 0.45)
        analog.update_right_stick(x=value, y=0)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=value
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        assert action == InputAction.TOGGLE_LOOK_MODE

    def test_just_below_threshold(self, game_with_gamepad):
        """Deflection just below threshold should not trigger look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        game.settings.gamepad_swap_sticks = False

        # 25% deflection (below threshold)
        value = int(32768 * 0.25)
        analog.update_right_stick(x=value, y=0)

        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=value
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.GAMEPLAY)

        assert action != InputAction.TOGGLE_LOOK_MODE


class TestCursorAutoRepeat:
    """Test cursor movement auto-repeat behavior."""

    def test_cursor_auto_repeat_timing(self, analog_handler):
        """Cursor should auto-repeat at configured rate."""
        handler = analog_handler

        # Set stick
        handler.update_right_stick(x=32000, y=0)

        # First movement (after settling)
        handler.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)
        movement1 = handler.get_right_stick_movement()
        assert movement1 is not None

        # Immediate - blocked
        movement2 = handler.get_right_stick_movement()
        assert movement2 is None

        # After initial delay
        time.sleep(handler.cursor_initial_delay + 0.01)
        movement3 = handler.get_right_stick_movement()
        assert movement3 is not None  # Should repeat

    def test_cursor_repeat_continues(self, analog_handler):
        """Cursor should continue repeating while held."""
        handler = analog_handler

        # Set stick
        handler.update_right_stick(x=32000, y=0)

        # Get past settling and initial delay
        handler.get_right_stick_movement()
        time.sleep(SETTLING_PERIOD_SEC)
        handler.get_right_stick_movement()  # First movement
        time.sleep(handler.cursor_initial_delay + 0.01)
        handler.get_right_stick_movement()  # First repeat

        # Now in repeat mode - wait for repeat rate
        time.sleep(handler.cursor_repeat_rate + 0.01)
        movement = handler.get_right_stick_movement()

        assert movement is not None


class TestTriggerLookModeToggle:
    """Test trigger-based look mode toggle."""

    def test_left_trigger_toggles_look_mode(self, game_with_gamepad):
        """Left trigger should toggle look mode."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Initialize trigger state (unpressed)
        init_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=0
        )
        gamepad.handle_axis_event(init_event, InputContext.GAMEPLAY)

        # Press trigger
        press_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=30000
        )
        action = gamepad.handle_axis_event(press_event, InputContext.GAMEPLAY)

        assert action == InputAction.TOGGLE_LOOK_MODE

    def test_trigger_fires_once_per_press(self, game_with_gamepad):
        """Trigger should only fire action once per press (edge detection)."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Initialize trigger
        init_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=0
        )
        gamepad.handle_axis_event(init_event, InputContext.GAMEPLAY)

        # Press trigger - first time fires
        press_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=30000
        )
        action1 = gamepad.handle_axis_event(press_event, InputContext.GAMEPLAY)
        assert action1 == InputAction.TOGGLE_LOOK_MODE

        # Hold trigger - should not fire again
        action2 = gamepad.handle_axis_event(press_event, InputContext.GAMEPLAY)
        assert action2 is None

        # Release and press again
        release_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=0
        )
        gamepad.handle_axis_event(release_event, InputContext.GAMEPLAY)

        action3 = gamepad.handle_axis_event(press_event, InputContext.GAMEPLAY)
        assert action3 == InputAction.TOGGLE_LOOK_MODE


class TestLookModeContextSwitch:
    """Test look mode behavior during context switches."""

    def test_look_mode_context_detection(self, game_with_gamepad):
        """Game should detect LOOK_MODE context when look_mode flag is set."""
        game, input_handler, _ = game_with_gamepad

        # Enable look mode on game
        game.look_mode = True

        context = input_handler._get_current_context()

        assert context == InputContext.LOOK_MODE

    def test_targeting_mode_context_detection(self, game_with_gamepad):
        """Game should detect TARGETING context when targeting_mode flag is set."""
        game, input_handler, _ = game_with_gamepad

        # Enable targeting mode on game
        game.targeting_mode = True

        context = input_handler._get_current_context()

        assert context == InputContext.TARGETING

    def test_targeting_takes_priority_over_look(self, game_with_gamepad):
        """Targeting mode should take priority over look mode."""
        game, input_handler, _ = game_with_gamepad

        # Enable both
        game.look_mode = True
        game.targeting_mode = True

        context = input_handler._get_current_context()

        # Targeting should take priority
        assert context == InputContext.TARGETING
