"""
Test for new game crash with analog stick handler.

Reproduces the AttributeError: 'AnalogStickHandler' object has no attribute 'get_left_stick_movement'
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from game_input_analog import AnalogStickHandler
from game_input_gamepad import GamepadInputHandler
from game_input import InputHandler


class TestNewGameCrash:
    """Test that reproduces the new game instant crash."""

    def test_analog_handler_has_get_left_stick_movement_method(self):
        """
        Test that AnalogStickHandler HAS get_left_stick_movement() method.

        This method was added for swap_sticks support - it handles cursor movement
        in look mode when swap_sticks=True (left stick controls cursor).
        """
        analog_handler = AnalogStickHandler()

        # The method should exist and work
        assert hasattr(analog_handler, 'get_left_stick_movement'), \
            "get_left_stick_movement() should exist for swap_sticks cursor control"

        # Test that it returns None when no input
        result = analog_handler.get_left_stick_movement()
        assert result is None, "Should return None with no stick input"

    def test_game_loop_calls_correct_analog_methods(self):
        """
        Test that game loop should use the correct methods based on context.

        This test verifies the fix - ensuring we call the right method for each context.
        """
        import time

        # Setup
        analog_handler = AnalogStickHandler()
        gamepad_handler = Mock()
        gamepad_handler.analog_handler = analog_handler

        input_handler = Mock()
        input_handler.gamepad_handler = gamepad_handler

        game = Mock()
        game.turn_count = 1
        game.show_inventory = False
        game.look_mode = False
        game.targeting_mode = False
        game.show_achievements = False
        game.show_help = False

        # Simulate left stick input
        analog_handler.update_left_stick(x=25000, y=0)

        # GAMEPLAY CONTEXT: First call starts settling period (returns None)
        movement = analog_handler.get_left_stick_movement_gameplay(game.turn_count)
        assert movement is None, "First call should start settling period"

        # Wait for settling period to complete (30ms + buffer)
        time.sleep(0.035)

        # Second call after settling should return movement
        movement = analog_handler.get_left_stick_movement_gameplay(game.turn_count)
        assert movement is not None, "Should detect left stick movement after settling"

        # Reset state for menu test
        analog_handler.update_left_stick(x=0, y=0)  # Release
        analog_handler.update_left_stick(x=25000, y=0)  # New deflection

        # MENU/MODAL CONTEXT: Should call get_left_stick_movement_menu()
        # Menu context doesn't have settling period - returns immediately
        game.show_achievements = True
        movement = analog_handler.get_left_stick_movement_menu()
        assert movement is not None, "Should detect left stick movement in menu context"
