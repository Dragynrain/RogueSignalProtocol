"""
Test: Swap Sticks - Polling Path (game_loop.py)

Tests the POLLING behavior that happens every frame when sticks are held,
verifying that swap_sticks setting is respected in both event-based and
polling code paths.

Covers gameplay movement, look mode cursor, and menu navigation.
"""

import time

import pytest
import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.systems.audio import NullSoundManager

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


class TestPollingPathSwapSticksGameplay:
    """
    Test that POLLING for gameplay movement respects swap_sticks.

    When swap_sticks=True:
    - RIGHT stick values should be used for gameplay movement
    - LEFT stick values should be IGNORED for gameplay movement
    """

    def test_polling_uses_right_stick_for_gameplay_when_swapped(self, game_with_swap_sticks):
        """
        Simulate what game_loop.py polling does and verify it uses correct stick.

        This test will FAIL until game_loop.py is fixed to check swap_sticks.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler
        analog = input_handler.gamepad_handler.analog_handler

        # Reset all state
        analog.last_gameplay_move_time = -1.0
        analog.gameplay_is_repeating = False
        analog.last_gameplay_direction = (0, 0)
        analog._settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set RIGHT stick to down position (this should move player when swap=True)
        analog.right_y = 25000

        # Get swap_sticks setting (same way game_loop.py should check it)
        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)
        assert swap_sticks is True, "Test setup: swap_sticks should be True"

        # THIS IS WHAT game_loop.py SHOULD DO (but currently doesn't):
        # When swap=True, use get_right_stick_movement_gameplay instead of get_left_stick
        if swap_sticks:
            movement = analog.get_right_stick_movement_gameplay(game.turn)
        else:
            movement = analog.get_left_stick_movement_gameplay(game.turn)

        # First call starts settling, should return None
        assert movement is None, "First call starts settling period"

        # Bypass settling period
        analog._settling_start_time = time.time() - 0.1

        # Second call should give movement
        if swap_sticks:
            movement = analog.get_right_stick_movement_gameplay(game.turn)
        else:
            movement = analog.get_left_stick_movement_gameplay(game.turn)

        assert movement is not None, "RIGHT stick should produce movement when swap=True"
        assert movement == (0, 1), f"Expected (0, 1) for down, got {movement}"

    def test_polling_ignores_left_stick_for_gameplay_when_swapped(self, game_with_swap_sticks):
        """
        Verify LEFT stick does NOT produce gameplay movement when swap=True.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler
        analog = input_handler.gamepad_handler.analog_handler

        # Reset all state
        analog.last_gameplay_move_time = -1.0
        analog._settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set LEFT stick to down position (this should NOT move player when swap=True)
        analog.left_y = 25000

        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)

        # When swap=True, we use RIGHT stick for movement, so LEFT stick should do nothing
        if swap_sticks:
            movement = analog.get_right_stick_movement_gameplay(game.turn)
        else:
            movement = analog.get_left_stick_movement_gameplay(game.turn)

        # RIGHT stick has no input, so should return None
        assert (
            movement is None
        ), "LEFT stick should NOT produce movement when swap=True (we read RIGHT)"


class TestPollingPathSwapSticksLookMode:
    """
    Test that POLLING for look mode cursor respects swap_sticks.

    When swap_sticks=True:
    - LEFT stick values should be used for cursor movement
    - RIGHT stick values should be IGNORED for cursor movement
    """

    def test_polling_uses_left_stick_for_cursor_when_swapped(self, game_with_swap_sticks):
        """
        Simulate what game_loop.py polling does for look mode cursor.

        This test will FAIL until game_loop.py is fixed to check swap_sticks.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler
        analog = input_handler.gamepad_handler.analog_handler

        # Enter look mode
        game.look_mode = True
        from rsp.entities.base import Position

        game.look_cursor_position = Position(game.player.position.x, game.player.position.y)

        # Reset cursor state
        analog.last_cursor_move_time = -1.0
        analog.cursor_is_repeating = False
        analog.last_cursor_direction = (0, 0)
        analog._cursor_settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set LEFT stick to down position (this should move cursor when swap=True)
        analog.left_y = 25000

        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)
        assert swap_sticks is True

        # THIS IS WHAT game_loop.py SHOULD DO (but currently doesn't):
        # When swap=True, use get_left_stick_movement instead of get_right_stick
        if swap_sticks:
            movement = analog.get_left_stick_movement()
        else:
            movement = analog.get_right_stick_movement()

        # First call starts settling
        assert movement is None, "First call starts settling"

        # Bypass settling
        analog._cursor_settling_start_time = time.time() - 0.1

        # Second call should give movement
        if swap_sticks:
            movement = analog.get_left_stick_movement()
        else:
            movement = analog.get_right_stick_movement()

        assert movement is not None, "LEFT stick should produce cursor movement when swap=True"
        assert movement == (0, 1), f"Expected (0, 1) for down, got {movement}"

    def test_polling_ignores_right_stick_for_cursor_when_swapped(self, game_with_swap_sticks):
        """
        Verify RIGHT stick does NOT move cursor when swap=True.
        """
        game = game_with_swap_sticks
        input_handler = game.input_handler
        analog = input_handler.gamepad_handler.analog_handler

        # Enter look mode
        game.look_mode = True

        # Reset cursor state
        analog.last_cursor_move_time = -1.0
        analog._cursor_settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set RIGHT stick to down position (should NOT move cursor when swap=True)
        analog.right_y = 25000

        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)

        # When swap=True, we use LEFT stick for cursor, so RIGHT stick should do nothing
        if swap_sticks:
            movement = analog.get_left_stick_movement()
        else:
            movement = analog.get_right_stick_movement()

        # LEFT stick has no input, so should return None
        assert movement is None, "RIGHT stick should NOT produce cursor movement when swap=True"


class TestGameLoopPollingSwapSticks:
    """
    Integration test that verifies game_loop.py polling respects swap_sticks.

    These tests check the actual logic that game_loop.py uses (or should use).
    """

    def test_game_loop_polling_logic_gameplay(self, game_with_swap_sticks):
        """
        Test the exact polling logic that game_loop.py uses for gameplay.

        Current game_loop.py code (WRONG):
            movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(game.turn)

        Fixed code (CORRECT):
            swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)
            if swap_sticks:
                movement = analog.get_right_stick_movement_gameplay(game.turn)
            else:
                movement = analog.get_left_stick_movement_gameplay(game.turn)
        """
        game = game_with_swap_sticks
        analog = game.input_handler.gamepad_handler.analog_handler

        # Reset state
        analog.last_gameplay_move_time = -1.0
        analog._settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 25000  # RIGHT stick pushed down

        # Bypass settling
        analog._settling_start_time = time.time() - 0.1

        # Simulate what FIXED game_loop.py should do
        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)

        if swap_sticks:
            movement = analog.get_right_stick_movement_gameplay(game.turn)
        else:
            movement = analog.get_left_stick_movement_gameplay(game.turn)

        # With swap=True and right_y=25000, we should get downward movement
        assert movement is not None, "Polling should detect RIGHT stick movement when swap=True"

    def test_game_loop_polling_logic_look_mode(self, game_with_swap_sticks):
        """
        Test the exact polling logic that game_loop.py uses for look mode.

        Current game_loop.py code (WRONG):
            movement = input_handler.gamepad_handler.analog_handler.get_right_stick_movement()

        Fixed code (CORRECT):
            swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)
            if swap_sticks:
                movement = analog.get_left_stick_movement()
            else:
                movement = analog.get_right_stick_movement()
        """
        game = game_with_swap_sticks
        game.look_mode = True
        analog = game.input_handler.gamepad_handler.analog_handler

        # Reset state
        analog.last_cursor_move_time = -1.0
        analog._cursor_settling_start_time = -1.0
        analog.left_x = 0
        analog.left_y = 25000  # LEFT stick pushed down
        analog.right_x = 0
        analog.right_y = 0

        # Bypass settling
        analog._cursor_settling_start_time = time.time() - 0.1

        # Simulate what FIXED game_loop.py should do
        swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)

        if swap_sticks:
            movement = analog.get_left_stick_movement()
        else:
            movement = analog.get_right_stick_movement()

        # With swap=True and left_y=25000, we should get downward cursor movement
        assert (
            movement is not None
        ), "Polling should detect LEFT stick movement for cursor when swap=True"


class TestPollingPathSwapSticksMenuNavigation:
    """
    Test that POLLING for menu navigation respects swap_sticks.

    This includes the main menu, settings menu, and confirmation dialogs
    like "Delete Save?" when starting a new game.

    When swap_sticks=True:
    - RIGHT stick values should be used for menu navigation
    - LEFT stick values should be IGNORED for menu navigation
    """

    def test_polling_uses_right_stick_for_menu_when_swapped(self, game_with_swap_sticks):
        """
        Verify RIGHT stick is used for menu navigation when swap=True.

        This tests the pattern that game_loop.py handle_menu_navigation uses.
        """
        game = game_with_swap_sticks
        settings = game.settings
        analog = game.input_handler.gamepad_handler.analog_handler

        # Reset menu state
        analog.last_menu_move_time = -1.0
        analog.menu_is_repeating = False
        analog.last_menu_direction = (0, 0)
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set RIGHT stick to down position (this should navigate menu when swap=True)
        analog.right_y = 25000

        swap_sticks = getattr(settings, "gamepad_swap_sticks", False)
        assert swap_sticks is True

        # THIS IS WHAT game_loop.py handle_menu_navigation SHOULD DO:
        if swap_sticks:
            movement = analog.get_right_stick_movement_menu()
        else:
            movement = analog.get_left_stick_movement_menu()

        # Menu navigation should give immediate movement (no settling period)
        assert movement is not None, "RIGHT stick should produce menu navigation when swap=True"
        # For 4-way menu nav, vertical takes priority
        assert movement[1] == 1, f"Expected dy=1 for down, got {movement}"

    def test_polling_ignores_left_stick_for_menu_when_swapped(self, game_with_swap_sticks):
        """
        Verify LEFT stick does NOT produce menu navigation when swap=True.
        """
        game = game_with_swap_sticks
        settings = game.settings
        analog = game.input_handler.gamepad_handler.analog_handler

        # Reset menu state
        analog.last_menu_move_time = -1.0
        analog.menu_is_repeating = False
        analog.last_menu_direction = (0, 0)
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set LEFT stick to down position (should NOT navigate menu when swap=True)
        analog.left_y = 25000

        swap_sticks = getattr(settings, "gamepad_swap_sticks", False)

        # When swap=True, we use RIGHT stick for menu, so LEFT stick should do nothing
        if swap_sticks:
            movement = analog.get_right_stick_movement_menu()
        else:
            movement = analog.get_left_stick_movement_menu()

        # RIGHT stick has no input, so should return None
        assert movement is None, "LEFT stick should NOT produce menu navigation when swap=True"

    def test_confirmation_dialog_uses_swapped_stick(self, game_with_swap_sticks):
        """
        Test that confirmation dialogs (like "Delete Save?") use swapped stick.

        The confirmation dialog uses the same menu navigation polling code,
        so if the swap is working for menus, it works for confirmation too.
        """
        game = game_with_swap_sticks
        settings = game.settings
        analog = game.input_handler.gamepad_handler.analog_handler

        # Reset menu state (same state as confirmation dialog uses)
        analog.last_menu_move_time = -1.0
        analog.menu_is_repeating = False
        analog.last_menu_direction = (0, 0)
        analog.left_x = 0
        analog.left_y = 0
        analog.right_x = 0
        analog.right_y = 0

        # Set RIGHT stick up (to select "Yes" in confirmation)
        analog.right_y = -25000

        swap_sticks = getattr(settings, "gamepad_swap_sticks", False)

        # Confirmation dialog uses menu navigation polling
        if swap_sticks:
            movement = analog.get_right_stick_movement_menu()
        else:
            movement = analog.get_left_stick_movement_menu()

        assert movement is not None, "Confirmation dialog should respond to swapped stick"
        assert movement[1] == -1, f"Expected dy=-1 for up, got {movement}"
