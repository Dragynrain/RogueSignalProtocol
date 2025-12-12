"""
TDD tests for Graphical Help screen navigation fixes.

Bug Reports:
------------
1. Mouse instruction text says "←→: Change Page" but:
   - These are keyboard/gamepad arrows, not mouse
   - Mouse uses wheel for page navigation
   - Text should clarify "Keyboard/Gamepad" vs "Mouse"

2. Vertical navigation (up/down) should be DISABLED:
   - Currently both D-pad UP/DOWN and stick vertical work
   - Easy to accidentally trigger diagonals on analog stick
   - Should be horizontal-only (left/right) for page navigation
   - Prevents accidental double-moves from diagonal stick input

Expected behavior:
- Clear instruction text distinguishing keyboard/gamepad vs mouse
- D-pad LEFT/RIGHT and stick horizontal: change pages
- D-pad UP/DOWN and stick vertical: do nothing (disabled)
- Mouse wheel: change pages
"""

from unittest.mock import Mock

import pytest
import tcod.event
import tcod.sdl.joystick

from game_config import GameSettings
from game_input_actions import InputAction
from game_menu_help_graphics import GraphicalHelpMenu


class TestGraphicalHelpHorizontalOnly:
    """Test that Graphical Help menu only accepts horizontal navigation."""

    @pytest.fixture
    def help_menu(self):
        """Create graphical help menu for testing."""
        settings = GameSettings()
        settings.master_volume = 0.0
        settings.graphics_mode = "graphics"

        mock_context = Mock()
        mock_context.sdl_renderer = Mock()
        mock_context.recommended_console_size = Mock(return_value=(1280, 800))
        mock_context.sdl_window.size = (1280, 800)

        mock_tile_manager = Mock()
        mock_tile_manager.tile_width = 20
        mock_tile_manager.tile_height = 32

        menu = GraphicalHelpMenu(mock_context, mock_tile_manager)
        return menu

    def test_navigate_left_right_changes_pages(self, help_menu):
        """
        SHOULD PASS: Left/right navigation should change pages.

        This is the correct behavior we want to keep.
        """
        initial_page = help_menu.current_page

        # Navigate RIGHT (next page)
        result = help_menu.execute_action(InputAction.NAVIGATE_RIGHT)
        assert result == "", "execute_action should return empty string"

        # Should have changed page
        if help_menu.current_page < len(help_menu.pages) - 1:
            # Not at last page, should have moved forward
            assert (
                help_menu.current_page == initial_page + 1
            ), "NAVIGATE_RIGHT should move to next page"
        else:
            # At last page, should wrap to first
            assert help_menu.current_page == 0, "NAVIGATE_RIGHT at last page should wrap to first"

    def test_navigate_up_down_should_do_nothing(self, help_menu):
        """
        Up/down navigation should be DISABLED (do nothing).

        Prevents accidental diagonal movements on analog stick causing
        unwanted double-moves (both horizontal and vertical).

        Fixed in game_menu_help_graphics.py lines 577-579.
        """
        initial_page = help_menu.current_page

        # Try to navigate UP (should do nothing)
        result = help_menu.execute_action(InputAction.NAVIGATE_UP)
        assert result == "", "execute_action should return empty string"

        # Page should NOT have changed
        assert (
            help_menu.current_page == initial_page
        ), "BUG: NAVIGATE_UP should do nothing in Graphical Help (horizontal-only navigation)"

        # Try to navigate DOWN (should do nothing)
        result = help_menu.execute_action(InputAction.NAVIGATE_DOWN)

        # Page should STILL not have changed
        assert (
            help_menu.current_page == initial_page
        ), "BUG: NAVIGATE_DOWN should do nothing in Graphical Help (horizontal-only navigation)"

    def test_move_north_south_should_do_nothing(self, help_menu):
        """
        Cardinal movement actions (MOVE_NORTH/SOUTH) should be disabled.

        These are alternate actions for the same inputs and are now ignored.
        Fixed in game_menu_help_graphics.py lines 577-579.
        """
        initial_page = help_menu.current_page

        # Try MOVE_NORTH (keyboard W or up arrow)
        result = help_menu.execute_action(InputAction.MOVE_NORTH)
        assert (
            help_menu.current_page == initial_page
        ), "BUG: MOVE_NORTH should do nothing in Graphical Help"

        # Try MOVE_SOUTH (keyboard S or down arrow)
        result = help_menu.execute_action(InputAction.MOVE_SOUTH)
        assert (
            help_menu.current_page == initial_page
        ), "BUG: MOVE_SOUTH should do nothing in Graphical Help"

    def test_dpad_up_down_does_nothing_end_to_end(self, help_menu):
        """
        D-pad UP/DOWN should not navigate pages (end-to-end test).

        Tests the complete path from button press to menu behavior.
        """
        initial_page = help_menu.current_page

        # Create D-pad DOWN press event
        dpad_down = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )

        # Process the event
        result = help_menu.handle_input(dpad_down)

        # Page should NOT have changed
        assert (
            help_menu.current_page == initial_page
        ), "BUG: D-pad DOWN should not change pages in Graphical Help"

        # Try D-pad UP
        dpad_up = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_UP,
            pressed=True,
        )

        result = help_menu.handle_input(dpad_up)

        # Page should STILL not have changed
        assert (
            help_menu.current_page == initial_page
        ), "BUG: D-pad UP should not change pages in Graphical Help"

    def test_dpad_left_right_still_works(self, help_menu):
        """
        SHOULD PASS: D-pad LEFT/RIGHT should still work for page navigation.

        This ensures we don't accidentally break horizontal navigation.
        """
        # Build pages so navigation has something to work with
        help_menu._build_pages()

        initial_page = help_menu.current_page

        # Create D-pad RIGHT press event
        dpad_right = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
            pressed=True,
        )

        # Process the event
        result = help_menu.handle_input(dpad_right)

        # Page SHOULD have changed
        assert (
            help_menu.current_page != initial_page
        ), "D-pad RIGHT should change pages in Graphical Help"


class TestGraphicalHelpMouseWheel:
    """Test that mouse wheel navigation still works."""

    @pytest.fixture
    def help_menu(self):
        """Create graphical help menu for testing."""
        settings = GameSettings()
        settings.master_volume = 0.0
        settings.graphics_mode = "graphics"

        mock_context = Mock()
        mock_context.sdl_renderer = Mock()
        mock_context.recommended_console_size = Mock(return_value=(1280, 800))
        mock_context.sdl_window.size = (1280, 800)

        mock_tile_manager = Mock()
        mock_tile_manager.tile_width = 20
        mock_tile_manager.tile_height = 32

        menu = GraphicalHelpMenu(mock_context, mock_tile_manager)
        return menu

    def test_mouse_wheel_changes_pages(self, help_menu):
        """
        SHOULD PASS: Mouse wheel should navigate pages (the actual mouse input).

        This verifies that mouse wheel (the REAL mouse navigation) still works.
        """
        # Build pages so navigation has something to work with
        help_menu._build_pages()

        initial_page = help_menu.current_page

        # Create mouse wheel event (scroll down = next page)
        wheel_event = Mock()
        wheel_event.y = -1  # Negative Y = scroll down/away from user

        result = help_menu.handle_mouse_wheel(wheel_event)

        # Should have changed page
        assert (
            help_menu.current_page != initial_page
        ), "Mouse wheel down should navigate to next page"
