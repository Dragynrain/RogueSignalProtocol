"""
Test: Swap Sticks - Menu Navigation

Verifies swap_sticks setting works in menus:
- When swap_sticks=True, RIGHT stick navigates menus
- LEFT stick is ignored when swap is enabled

FIX APPLIED: GamepadInputHandler uses GameSettings.get_instance() singleton
to read swap_sticks, so menus can access the setting even with game=None.
"""

import pytest
from unittest.mock import Mock
import tcod.event
import tcod.sdl.joystick

from game_config import GameSettings
from game_input_actions import InputAction, InputContext
from game_menu_main import MainMenu

CA = tcod.sdl.joystick.ControllerAxis


@pytest.fixture
def settings_with_swap():
    """Create settings with swap_sticks enabled."""
    settings = GameSettings()
    settings.graphics_mode = "text"
    settings.gamepad_swap_sticks = True  # KEY: swap is ON
    return settings


class TestSwapSticksMenuNavigation:
    """
    Test that RIGHT stick navigates menus when swap_sticks=True.

    This tests the ACTUAL menu path - MainMenu with its own BaseInputHandler,
    NOT the GameEngine's input handler.
    """

    def test_menu_gamepad_handler_reads_swap_sticks(self, settings_with_swap):
        """
        Menu's GamepadInputHandler must be able to read swap_sticks setting.

        FIX: GamepadInputHandler now uses GameSettings.get_instance() singleton.
        """
        # settings_with_swap fixture creates GameSettings which registers as singleton
        # Menu's GamepadInputHandler will pick it up via GameSettings.get_instance()
        menu = MainMenu(background=None)

        # Push RIGHT stick down
        event = Mock()
        event.axis = CA.RIGHTY
        event.value = 25000

        # Reset menu navigation state
        menu.gamepad_handler.analog_handler.last_menu_move_time = -1.0
        menu.gamepad_handler.analog_handler.menu_is_repeating = False
        menu.gamepad_handler.analog_handler.last_menu_direction = (0, 0)

        # Get action from the menu's gamepad handler
        result = menu.gamepad_handler.handle_axis_event(event, InputContext.MAIN_MENU)

        # This SHOULD navigate, but currently swap_sticks is always False
        # because the menu has no access to settings
        assert result == InputAction.NAVIGATE_DOWN, \
            f"Menu's RIGHT stick should navigate down when swap=True, got {result}. " \
            f"BUG: Menu's GamepadInputHandler has game=None, can't read swap_sticks!"

    def test_menu_left_stick_ignored_when_swap_enabled(self, settings_with_swap):
        """
        LEFT stick should NOT navigate menus when swap_sticks=True.

        FIX: GamepadInputHandler now uses GameSettings.get_instance() singleton.
        """
        # settings_with_swap fixture creates GameSettings which registers as singleton
        menu = MainMenu(background=None)

        # Reset state
        menu.gamepad_handler.analog_handler.last_menu_move_time = -1.0

        # Push LEFT stick down
        event = Mock()
        event.axis = CA.LEFTY
        event.value = 25000

        result = menu.gamepad_handler.handle_axis_event(event, InputContext.MAIN_MENU)

        # When swap is ON, left stick should NOT navigate
        assert result != InputAction.NAVIGATE_DOWN, \
            f"LEFT stick should NOT navigate when swap=True, got {result}"
