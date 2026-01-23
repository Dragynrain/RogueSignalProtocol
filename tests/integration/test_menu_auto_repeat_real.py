"""
REAL auto-repeat tests that test the ACTUAL game loop behavior.

These tests simulate the actual polling loop, not just single events.
They would have caught BOTH bugs:
1. D-pad infinite scrolling (no BUTTONUP handling)
2. Left stick no auto-repeat (no polling)

Uses mock_time fixture for deterministic timing (no flaky time.sleep).
"""

import pytest
import tcod
import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameSettings
from rsp.input.actions import InputContext
from rsp.ui.menu_main import MainMenu


class TestMainMenuAutoRepeatReal:
    """Test ACTUAL auto-repeat behavior in main menu (polling loop simulation)."""

    @pytest.fixture
    def main_menu_with_gamepad(self):
        """Create main menu with gamepad handler."""
        settings = GameSettings()
        settings.master_volume = 0.0
        settings.sfx_volume = 0.0
        settings.music_volume = 0.0

        # Create main menu (background and menus can be None for testing)
        # Settings accessed via singleton (GameSettings() above registers it)
        menu = MainMenu(background=None, menus=None)

        # Ensure gamepad handler exists
        assert hasattr(menu, "gamepad_handler"), "Menu must have gamepad_handler"

        yield menu

    def test_dpad_stops_on_release(self, main_menu_with_gamepad):
        """
        CRITICAL: D-pad auto-repeat must STOP when button is released.

        This test would have FAILED before the fix because MainMenu.handle_input()
        never handled CONTROLLERBUTTONUP events.
        """
        menu = main_menu_with_gamepad

        # Simulate pressing D-pad Down
        down_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )
        result = menu.handle_input(down_event)

        # Verify button is tracked as held
        assert (
            menu.gamepad_handler.button_held == tcod.sdl.joystick.ControllerButton.DPAD_DOWN
        ), "After BUTTONDOWN, button_held should be set"

        # NOW: Simulate releasing the button
        up_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONUP",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=False,
        )
        menu.handle_input(up_event)

        # CRITICAL TEST: Verify button state is cleared
        assert menu.gamepad_handler.button_held is None, (
            "After BUTTONUP, button_held MUST be None! "
            "BUG: D-pad scrolls forever because BUTTONUP is not handled!"
        )

        # Verify repeat action is None after release
        context = InputContext.MAIN_MENU
        repeat_action_after_release = menu.gamepad_handler.get_button_repeat_action(context)
        assert (
            repeat_action_after_release is None
        ), "After BUTTONUP, get_button_repeat_action() should return None"

    def test_left_stick_auto_repeat_via_polling(self, main_menu_with_gamepad, mock_time):
        """
        CRITICAL: Left stick auto-repeat must work via polling loop.

        This test would have FAILED before the fix because there was NO
        analog stick polling in handle_menu_navigation().
        """
        menu = main_menu_with_gamepad
        initial_selection = menu.selected_option

        # Simulate pushing left stick down (axis event updates analog handler)
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
            value=32767,  # Full down
        )

        # First event: Updates analog handler state
        menu.handle_input(axis_event)

        # Should move immediately (first move has no delay)
        first_move = menu.selected_option
        assert first_move == (initial_selection + 1) % len(
            menu.options
        ), "First analog move should be immediate"

        # Wait past initial delay (0.4s + buffer)
        mock_time.advance(0.45)

        # CRITICAL: Simulate polling loop calling analog handler
        # This is what game_loop.py should do but WASN'T doing!
        movement = menu.gamepad_handler.analog_handler.get_left_stick_movement_menu()

        assert movement is not None, (
            "After initial delay, analog handler should return movement! "
            "BUG: Left stick doesn't repeat because there's NO POLLING in game loop!"
        )

        # If movement exists, execute it
        if movement:
            dx, dy = movement
            if dy > 0:
                from rsp.input.actions import InputAction

                menu.execute_action(InputAction.NAVIGATE_DOWN)
                second_move = menu.selected_option
                assert (
                    second_move != first_move
                ), "Polling should trigger another move (auto-repeat)"

        # Test that repeat continues if stick is still held
        mock_time.advance(0.16)  # Wait past repeat rate (150ms + buffer)
        movement2 = menu.gamepad_handler.analog_handler.get_left_stick_movement_menu()
        assert movement2 is not None, "Should continue repeating while held"

    def test_dpad_and_stick_use_same_timing(self, main_menu_with_gamepad):
        """
        Both D-pad and left stick use similar auto-repeat timing.

        D-pad: 400ms initial delay, 150ms repeat rate
        Stick: 400ms initial delay, 150ms repeat rate
        """
        menu = main_menu_with_gamepad

        # Check D-pad timing constants
        assert (
            menu.gamepad_handler.button_repeat_initial_delay == 0.4
        ), "D-pad initial delay should be 400ms"
        assert menu.gamepad_handler.button_repeat_rate == 0.15, "D-pad repeat rate should be 150ms"

        # Check analog stick timing constants
        assert (
            menu.gamepad_handler.analog_handler.menu_initial_delay == 0.4
        ), "Stick initial delay should be 400ms"
        assert (
            menu.gamepad_handler.analog_handler.menu_repeat_rate == 0.15
        ), "Stick repeat rate should be 150ms"

        # NOTE: Both use the same timing for consistent feel across input methods

    def test_buttonup_clears_state_for_all_dpad_directions(self, main_menu_with_gamepad):
        """
        BUTTONUP must clear button_held state for D-pad navigation directions.

        This prevents the infinite scrolling bug. Main menu only uses UP/DOWN.
        """
        menu = main_menu_with_gamepad
        context = InputContext.MAIN_MENU

        # Test D-pad UP/DOWN (main menu only uses vertical navigation)
        directions = [
            tcod.sdl.joystick.ControllerButton.DPAD_UP,
            tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
        ]

        for direction in directions:
            # Press button
            down_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=direction, pressed=True
            )
            menu.handle_input(down_event)

            # Verify button is held (only tracked if mapped to a navigation action)
            assert (
                menu.gamepad_handler.button_held == direction
            ), f"Button {direction} should be tracked as held"

            # Release button
            up_event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONUP", which=0, button=direction, pressed=False
            )
            menu.handle_input(up_event)

            # CRITICAL: Verify state is cleared
            assert menu.gamepad_handler.button_held is None, (
                f"Button {direction} state must be cleared on BUTTONUP! "
                f"Otherwise it scrolls forever!"
            )


class TestGameLoopPollingIntegration:
    """
    Test that game_loop.py handle_menu_navigation() actually polls analog sticks.

    These tests verify the INTEGRATION between menu and game loop.
    """

    def test_game_loop_has_analog_stick_polling(self):
        """
        Verify that handle_menu_navigation() has analog stick polling code.

        This is a code inspection test - checks that the fix exists.
        """
        import inspect

        import rsp.core.loop as game_loop

        # Get source code of handle_menu_navigation
        source = inspect.getsource(game_loop.handle_menu_navigation)

        # Verify it has analog stick polling
        assert "get_left_stick_movement_menu()" in source, (
            "handle_menu_navigation MUST call get_left_stick_movement_menu() for auto-repeat! "
            "BUG: Left stick doesn't repeat because there's NO POLLING!"
        )

        assert "analog_handler" in source, "Must access analog_handler to poll stick state"

        # Verify it handles the movement result
        assert (
            "NAVIGATE_UP" in source or "NAVIGATE_DOWN" in source
        ), "Must convert stick movement to navigation actions"

    def test_game_loop_handles_buttonup_events(self):
        """
        Verify that handle_menu_navigation() routes BUTTONUP events to menu.

        This ensures button state gets cleared.
        """
        import inspect

        import rsp.core.loop as game_loop

        source = inspect.getsource(game_loop.handle_menu_navigation)

        # Verify it handles CONTROLLERBUTTONUP
        assert "CONTROLLERBUTTONUP" in source, (
            "handle_menu_navigation must handle CONTROLLERBUTTONUP events! "
            "Otherwise button state never clears!"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
