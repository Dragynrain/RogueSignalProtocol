"""
Test: Swap Sticks - Gameplay Movement and Look Mode Cursor

When swap_sticks=True:
- RIGHT stick moves the character
- LEFT stick triggers look mode, then moves the cursor

Tests use the FULL input handler path (not just gamepad handler) to verify integration.
"""
import pytest
import time
from unittest.mock import Mock
import tcod.event
import tcod.sdl.joystick

from game_engine import GameEngine
from game_config import GameSettings, GameConfig
from game_audio import NullSoundManager
from game_input_actions import InputAction, InputContext

CA = tcod.sdl.joystick.ControllerAxis


@pytest.fixture
def game_with_swap_sticks():
    """Create game with swap_sticks enabled."""
    settings = GameSettings()
    settings.graphics_mode = "text"
    settings.gamepad_swap_sticks = True  # KEY: swap is ON

    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)
    game.dialogue_state.active_dialogue = None

    return game


class TestSwapSticksGameplayMovement:
    """Test that RIGHT stick moves the character when swap_sticks=True."""

    def test_right_stick_moves_character_full_path(self, game_with_swap_sticks):
        """
        Test RIGHT stick movement through FULL InputHandler path.

        This tests the real game flow, not just the gamepad handler.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler

        # Reset gameplay movement state completely
        analog = input_handler.gamepad_handler.analog_handler
        analog.last_gameplay_move_time = -1.0
        analog.gameplay_is_repeating = False
        analog.last_gameplay_direction = (0, 0)
        analog._settling_start_time = -1.0
        analog.right_x = 0
        analog.right_y = 0

        # Create proper ControllerAxis event (not Mock)
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            axis=CA.RIGHTY,
            value=25000,
            which=0
        )

        # First call starts settling period
        result1 = input_handler.handle_controller_axis(event)

        # Bypass settling period
        analog._settling_start_time = time.time() - 0.1

        # Second call should produce action
        result2 = input_handler.handle_controller_axis(event)

        # Should be handled (True) and have triggered movement action
        assert result2 is True, \
            f"RIGHT stick should be handled in gameplay with swap=True, got {result2}"

    def test_left_stick_triggers_look_mode_full_path(self, game_with_swap_sticks):
        """
        Test LEFT stick triggers look mode through full path when swap=True.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler

        # Ensure we're in gameplay, not look mode
        game.look_mode = False

        # Reset state
        analog = input_handler.gamepad_handler.analog_handler
        analog.last_gameplay_move_time = -1.0
        analog._settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0

        # Push LEFT stick down
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            axis=CA.LEFTY,
            value=25000,
            which=0
        )

        result = input_handler.handle_controller_axis(event)

        # Should trigger look mode
        assert game.look_mode is True, \
            "LEFT stick should trigger look mode when swap=True in gameplay"


class TestSwapSticksLookModeCursor:
    """Test that LEFT stick moves cursor in look mode when swap_sticks=True."""

    def test_left_stick_moves_cursor_in_look_mode_full_path(self, game_with_swap_sticks):
        """
        Test LEFT stick cursor movement in look mode through full path.

        This is the reported bug: look mode triggers but cursor won't move.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler

        # Enter look mode first
        game.look_mode = True
        from game_entities import Position
        game.look_cursor_position = Position(game.player.position.x, game.player.position.y)
        initial_cursor_y = game.look_cursor_position.y

        # Reset cursor movement state
        analog = input_handler.gamepad_handler.analog_handler
        analog.last_cursor_move_time = -1.0
        analog.cursor_is_repeating = False
        analog.last_cursor_direction = (0, 0)
        analog._cursor_settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0

        # Push LEFT stick down
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            axis=CA.LEFTY,
            value=25000,  # Down
            which=0
        )

        # First call starts settling
        result1 = input_handler.handle_controller_axis(event)

        # Bypass settling
        analog._cursor_settling_start_time = time.time() - 0.1

        # Second call should move cursor
        result2 = input_handler.handle_controller_axis(event)

        # Cursor should have moved down (Y increased)
        assert game.look_cursor_position.y > initial_cursor_y, \
            f"LEFT stick should move cursor down in look mode with swap=True, " \
            f"cursor_y was {initial_cursor_y}, now {game.look_cursor_position.y}"

    def test_right_stick_does_nothing_in_look_mode_full_path(self, game_with_swap_sticks):
        """
        Test RIGHT stick is ignored in look mode when swap=True.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler

        # Enter look mode
        game.look_mode = True
        from game_entities import Position
        game.look_cursor_position = Position(game.player.position.x, game.player.position.y)
        initial_cursor_y = game.look_cursor_position.y

        # Reset state
        analog = input_handler.gamepad_handler.analog_handler
        analog.last_cursor_move_time = -1.0
        analog._cursor_settling_start_time = -1.0

        # Push RIGHT stick down
        event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            axis=CA.RIGHTY,
            value=25000,
            which=0
        )

        result = input_handler.handle_controller_axis(event)

        # Cursor should NOT have moved
        assert game.look_cursor_position.y == initial_cursor_y, \
            f"RIGHT stick should NOT move cursor in look mode with swap=True, " \
            f"cursor_y was {initial_cursor_y}, now {game.look_cursor_position.y}"
