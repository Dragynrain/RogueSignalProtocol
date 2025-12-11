"""
Gameplay Movement Time-Based Gating Tests

Tests for the time-based gating system that controls gamepad left stick
movement during gameplay. This replaced the old turn-based gating which
didn't work correctly (turns increment after each move, causing instant
continuous movement).

Behavior:
- First tap: immediate movement
- Hold: wait for initial delay (0.35s), then repeat at rate (0.18s)
- Direction change: immediate movement (resets timing)
- Stick release: resets all timing state

Uses the game_with_gamepad fixture from tests/conftest.py.
Uses mock_time fixture from conftest.py for reliable time control.
"""

import pytest
import tcod.event
import tcod.sdl.joystick

from game_config import GameConfig

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

from tests.conftest import get_movement_with_settling, SETTLING_PERIOD_SEC


class TestFirstInputImmediate:
    """Test that first input (or after release) is immediate (after settling period)."""

    def test_first_tap_immediate(self, game_with_gamepad, mock_time):
        """First stick deflection should give movement after settling period."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # First tap (with settling period)
        movement = get_movement_with_settling(analog, game.turn, 0, -32767, mock_time)
        assert movement == (0, -1), "First tap should give immediate movement"

    def test_release_and_retap_immediate(self, game_with_gamepad, mock_time):
        """After releasing and re-deflecting, movement should be immediate (after settling)."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # First tap (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement1 == (1, 0)

        # Release stick
        analog.update_left_stick(x=0, y=0)
        analog.get_left_stick_movement_gameplay(game.turn)  # Process release

        # Re-tap (with settling)
        movement2 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement2 == (1, 0), "Re-tap after release should be immediate"


class TestHoldBehavior:
    """Test hold-to-repeat behavior with timing."""

    def test_hold_blocks_until_initial_delay(self, game_with_gamepad, mock_time):
        """Holding stick should block movement until initial delay passes (after settling)."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect stick (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement1 == (1, 0)

        # Immediate second call - should be blocked
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 is None, "Should be blocked before initial delay"

    def test_hold_allows_after_initial_delay(self, game_with_gamepad, mock_time):
        """After initial delay, holding stick should allow movement."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect stick (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement1 == (1, 0)

        # Wait for initial delay
        mock_time.advance(GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY + 0.05)

        # Should now allow movement
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 == (1, 0), "Should allow movement after initial delay"

    def test_repeat_rate_after_initial_delay(self, game_with_gamepad, mock_time):
        """After initial delay, should repeat at configured rate."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect stick (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)
        assert movement1 == (1, 0)

        # Wait for initial delay
        mock_time.advance(GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY + 0.05)

        # Should allow movement (enters repeat mode)
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 == (1, 0)

        # Immediately after - should be blocked (repeat rate not elapsed)
        movement3 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement3 is None, "Should block before repeat rate elapsed"

        # Wait for repeat rate
        mock_time.advance(GameConfig.GAMEPLAY_MOVEMENT_REPEAT_RATE + 0.02)

        # Should allow again
        movement4 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement4 == (1, 0), "Should allow after repeat rate"


class TestDirectionLocking:
    """Test that direction is locked on first deflection (prevents multi-move diagonal bug)."""

    def test_direction_locked_on_first_deflection(self, game_with_gamepad, mock_time):
        """Direction should be locked until stick is released."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Move north (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 0, -32767, mock_time)
        assert movement1 == (0, -1)

        # Try to change to south - should be IGNORED (direction locked)
        analog.update_left_stick(x=0, y=32767)
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 is None, "Direction change should be ignored while stick held"

    def test_direction_unlocked_on_release(self, game_with_gamepad, mock_time):
        """Direction should unlock when stick returns to center."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Move north (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, 0, -32767, mock_time)
        assert movement1 == (0, -1)

        # Release stick
        analog.update_left_stick(x=0, y=0)
        analog.get_left_stick_movement_gameplay(game.turn)

        # Now deflect south (with settling)
        movement2 = get_movement_with_settling(analog, game.turn, 0, 32767, mock_time)
        assert movement2 == (0, 1), "New direction after release should work"

    def test_direction_lock_prevents_diagonal_multi_move(self, game_with_gamepad, mock_time):
        """Rapidly changing directions while held should not cause multiple moves."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Simulate diagonal tap: left -> up-left -> up (common when pushing to diagonal)
        # First: left is detected (with settling)
        movement1 = get_movement_with_settling(analog, game.turn, -32767, 0, mock_time)
        assert movement1 == (-1, 0), "First direction should register"

        # Stick moves through up-left zone - should be ignored
        analog.update_left_stick(x=-23170, y=-23170)
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 is None, "Direction change to diagonal should be ignored"

        # Stick settles on up - should be ignored
        analog.update_left_stick(x=0, y=-32767)
        movement3 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement3 is None, "Direction change to up should be ignored"


class TestDiagonalMovement:
    """Test diagonal (8-way) movement works correctly."""

    def test_northeast_movement(self, game_with_gamepad, mock_time):
        """Test northeast diagonal movement."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect both axes (with settling)
        movement = get_movement_with_settling(analog, game.turn, 32767, -32767, mock_time)
        assert movement == (1, -1), "Should get northeast diagonal"

    def test_southwest_movement(self, game_with_gamepad, mock_time):
        """Test southwest diagonal movement."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect both axes (with settling)
        movement = get_movement_with_settling(analog, game.turn, -32767, 32767, mock_time)
        assert movement == (-1, 1), "Should get southwest diagonal"


class TestStickRelease:
    """Test that releasing the stick resets state properly."""

    def test_release_returns_none(self, game_with_gamepad, mock_time):
        """Stick in center should return None."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect (with settling) then release
        get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)

        # Release
        analog.update_left_stick(x=0, y=0)

        movement = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement is None, "Centered stick should return None"

    def test_release_resets_state(self, game_with_gamepad, mock_time):
        """Releasing stick should reset all timing state."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect (with settling) and enter repeat mode
        get_movement_with_settling(analog, game.turn, 32767, 0, mock_time)

        mock_time.advance(GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY + 0.05)
        analog.get_left_stick_movement_gameplay(game.turn)  # Enter repeat mode
        assert analog.gameplay_is_repeating, "Should be in repeat mode"

        # Release
        analog.update_left_stick(x=0, y=0)
        analog.get_left_stick_movement_gameplay(game.turn)

        # State should be reset
        assert analog.last_gameplay_move_time == -1.0, "Time should be reset"
        assert not analog.gameplay_is_repeating, "Should not be repeating"
        assert analog.last_gameplay_direction == (0, 0), "Direction should be reset"


class TestResetMethod:
    """Test the reset_movement_gating() method."""

    def test_reset_clears_state(self, game_with_gamepad):
        """reset_movement_gating() should clear all state."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Set up some state
        analog.last_gameplay_move_time = 12345.0
        analog.gameplay_is_repeating = True
        analog.last_gameplay_direction = (1, -1)

        # Reset
        analog.reset_movement_gating()

        # Check state cleared
        assert analog.last_gameplay_move_time == -1.0
        assert not analog.gameplay_is_repeating
        assert analog.last_gameplay_direction == (0, 0)


class TestTurnParameterIgnored:
    """Test that the turn parameter is ignored (kept for API compat)."""

    def test_turn_value_irrelevant(self, game_with_gamepad, mock_time):
        """Turn value should not affect behavior (time-based now)."""
        game, input_handler, controller = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect stick (with settling)
        movement1 = get_movement_with_settling(analog, 0, 32767, 0, mock_time)
        assert movement1 == (1, 0)

        # Second call with turn 1000 - should still be blocked (time-based)
        movement2 = analog.get_left_stick_movement_gameplay(1000)
        assert movement2 is None, "Turn value should not bypass time gating"

        # Wait for initial delay
        mock_time.advance(GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY + 0.05)

        # Now should work regardless of turn value
        movement3 = analog.get_left_stick_movement_gameplay(0)
        assert movement3 == (1, 0)
