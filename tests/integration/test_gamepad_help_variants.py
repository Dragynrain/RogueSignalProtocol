"""
Gamepad Help Menu Variants Tests.

Tests both HelpMenu (text mode) and GraphicalHelpMenu (graphics mode) classes
to ensure gamepad navigation works correctly for both variants.

Key differences to test:
- HelpMenu: uses _navigate_page(direction), navigate_right(), navigate_left()
- GraphicalHelpMenu: uses _next_page(), _previous_page(), navigate_right(), navigate_left()
- game_loop.py checks hasattr for _previous_page/_next_page (GraphicalHelpMenu only)

Coverage:
- Both menu classes respond to execute_action correctly
- Page navigation via InputAction (NAVIGATE_LEFT, NAVIGATE_RIGHT)
- Method existence verification (hasattr checks)
- Tab switching with gamepad
- Hybrid event+polling pattern verification
"""

from unittest.mock import MagicMock, Mock

import pytest
import tcod.console
import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameSettings
from rsp.input.actions import InputAction, InputContext
from rsp.ui.menu_help_lore import HelpMenu, create_help_menu

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis


@pytest.fixture
def help_menu():
    """Create text-mode help menu."""
    return HelpMenu()


@pytest.fixture
def graphical_help_menu():
    """Create graphics-mode help menu with mocked dependencies."""
    # Mock the context and tile_manager
    mock_context = MagicMock()
    mock_context.sdl_renderer = MagicMock()
    mock_context.sdl_window = MagicMock()
    mock_context.sdl_window.size = (1280, 800)

    mock_tile_manager = MagicMock()
    mock_tile_manager.get_tile = MagicMock(return_value=MagicMock())
    mock_tile_manager.tile_width = 64
    mock_tile_manager.tile_height = 64

    from rsp.ui.menu_help_graphics import GraphicalHelpMenu

    return GraphicalHelpMenu(mock_context, mock_tile_manager)


class TestHelpMenuMethodExistence:
    """Verify correct methods exist on each menu variant."""

    def test_help_menu_has_navigate_page(self, help_menu):
        """HelpMenu should have _navigate_page method."""
        assert hasattr(help_menu, "_navigate_page")
        assert callable(help_menu._navigate_page)

    def test_help_menu_has_navigate_right(self, help_menu):
        """HelpMenu should have navigate_right method."""
        assert hasattr(help_menu, "navigate_right")
        assert callable(help_menu.navigate_right)

    def test_help_menu_has_navigate_left(self, help_menu):
        """HelpMenu should have navigate_left method."""
        assert hasattr(help_menu, "navigate_left")
        assert callable(help_menu.navigate_left)

    def test_help_menu_does_not_have_next_page(self, help_menu):
        """HelpMenu should NOT have _next_page method."""
        assert not hasattr(help_menu, "_next_page")

    def test_help_menu_does_not_have_previous_page(self, help_menu):
        """HelpMenu should NOT have _previous_page method."""
        assert not hasattr(help_menu, "_previous_page")

    def test_graphical_help_has_next_page(self, graphical_help_menu):
        """GraphicalHelpMenu should have _next_page method."""
        assert hasattr(graphical_help_menu, "_next_page")
        assert callable(graphical_help_menu._next_page)

    def test_graphical_help_has_previous_page(self, graphical_help_menu):
        """GraphicalHelpMenu should have _previous_page method."""
        assert hasattr(graphical_help_menu, "_previous_page")
        assert callable(graphical_help_menu._previous_page)

    def test_graphical_help_has_navigate_right(self, graphical_help_menu):
        """GraphicalHelpMenu should have navigate_right method."""
        assert hasattr(graphical_help_menu, "navigate_right")
        assert callable(graphical_help_menu.navigate_right)

    def test_graphical_help_has_navigate_left(self, graphical_help_menu):
        """GraphicalHelpMenu should have navigate_left method."""
        assert hasattr(graphical_help_menu, "navigate_left")
        assert callable(graphical_help_menu.navigate_left)


class TestHelpMenuPageNavigation:
    """Test page navigation for HelpMenu (text mode)."""

    def test_initial_page_is_zero(self, help_menu):
        """Help menu should start on page 0."""
        assert help_menu.current_page == 0

    def test_navigate_right_advances_page(self, help_menu):
        """navigate_right should advance to next page."""
        initial_page = help_menu.current_page
        help_menu.navigate_right()
        assert help_menu.current_page == initial_page + 1

    def test_navigate_left_goes_back(self, help_menu):
        """navigate_left should go to previous page."""
        help_menu.current_page = 2
        help_menu.navigate_left()
        assert help_menu.current_page == 1

    def test_navigate_wraps_around(self, help_menu):
        """Page navigation should wrap around."""
        # Navigate past the end
        help_menu.current_page = help_menu.total_pages - 1
        help_menu.navigate_right()
        assert help_menu.current_page == 0  # Wrapped to first page

        # Navigate before the beginning
        help_menu.navigate_left()
        assert help_menu.current_page == help_menu.total_pages - 1  # Wrapped to last page

    def test_execute_action_navigate_right(self, help_menu):
        """execute_action with NAVIGATE_RIGHT should advance page."""
        initial_page = help_menu.current_page
        result = help_menu.execute_action(InputAction.NAVIGATE_RIGHT)
        assert result == ""  # Empty string means handled
        assert help_menu.current_page == initial_page + 1

    def test_execute_action_navigate_left(self, help_menu):
        """execute_action with NAVIGATE_LEFT should go back."""
        help_menu.current_page = 2
        result = help_menu.execute_action(InputAction.NAVIGATE_LEFT)
        assert result == ""
        assert help_menu.current_page == 1

    def test_execute_action_move_east_navigates_right(self, help_menu):
        """MOVE_EAST should also navigate right."""
        initial_page = help_menu.current_page
        result = help_menu.execute_action(InputAction.MOVE_EAST)
        assert result == ""
        assert help_menu.current_page == initial_page + 1

    def test_execute_action_move_west_navigates_left(self, help_menu):
        """MOVE_WEST should also navigate left."""
        help_menu.current_page = 2
        result = help_menu.execute_action(InputAction.MOVE_WEST)
        assert result == ""
        assert help_menu.current_page == 1

    def test_execute_action_cancel_returns_back(self, help_menu):
        """CANCEL should return 'back'."""
        result = help_menu.execute_action(InputAction.CANCEL)
        assert result == "back"


class TestGraphicalHelpMenuPageNavigation:
    """Test page navigation for GraphicalHelpMenu."""

    def test_initial_page_is_zero(self, graphical_help_menu):
        """Graphical help menu should start on page 0."""
        assert graphical_help_menu.current_page == 0

    def test_next_page_advances(self, graphical_help_menu):
        """_next_page should advance to next page."""
        graphical_help_menu._build_pages()  # Build pages first
        initial_page = graphical_help_menu.current_page
        graphical_help_menu._next_page()
        assert graphical_help_menu.current_page == initial_page + 1

    def test_previous_page_goes_back(self, graphical_help_menu):
        """_previous_page should go to previous page."""
        graphical_help_menu._build_pages()
        graphical_help_menu.current_page = 2
        graphical_help_menu._previous_page()
        assert graphical_help_menu.current_page == 1

    def test_next_page_stops_at_end(self, graphical_help_menu):
        """_next_page should stop at last page (no wrap)."""
        graphical_help_menu._build_pages()
        last_page = len(graphical_help_menu.pages) - 1
        graphical_help_menu.current_page = last_page
        graphical_help_menu._next_page()
        assert graphical_help_menu.current_page == last_page  # Didn't change

    def test_previous_page_stops_at_start(self, graphical_help_menu):
        """_previous_page should stop at first page (no wrap)."""
        graphical_help_menu._build_pages()
        graphical_help_menu.current_page = 0
        graphical_help_menu._previous_page()
        assert graphical_help_menu.current_page == 0  # Didn't change

    def test_navigate_right_calls_next_page(self, graphical_help_menu):
        """navigate_right should call _next_page."""
        graphical_help_menu._build_pages()
        initial_page = graphical_help_menu.current_page
        graphical_help_menu.navigate_right()
        assert graphical_help_menu.current_page == initial_page + 1

    def test_navigate_left_calls_previous_page(self, graphical_help_menu):
        """navigate_left should call _previous_page."""
        graphical_help_menu._build_pages()
        graphical_help_menu.current_page = 2
        graphical_help_menu.navigate_left()
        assert graphical_help_menu.current_page == 1

    def test_execute_action_navigate_right(self, graphical_help_menu):
        """execute_action with NAVIGATE_RIGHT should advance page."""
        graphical_help_menu._build_pages()
        initial_page = graphical_help_menu.current_page
        result = graphical_help_menu.execute_action(InputAction.NAVIGATE_RIGHT)
        assert result == ""
        assert graphical_help_menu.current_page == initial_page + 1

    def test_execute_action_navigate_left(self, graphical_help_menu):
        """execute_action with NAVIGATE_LEFT should go back."""
        graphical_help_menu._build_pages()
        graphical_help_menu.current_page = 2
        result = graphical_help_menu.execute_action(InputAction.NAVIGATE_LEFT)
        assert result == ""
        assert graphical_help_menu.current_page == 1

    def test_execute_action_cancel_returns_back(self, graphical_help_menu):
        """CANCEL should return 'back'."""
        result = graphical_help_menu.execute_action(InputAction.CANCEL)
        assert result == "back"

    def test_vertical_navigation_ignored(self, graphical_help_menu):
        """Vertical navigation should be ignored (prevents diagonal swipe issues)."""
        graphical_help_menu._build_pages()
        initial_page = graphical_help_menu.current_page

        # Try vertical navigation - should do nothing
        result_up = graphical_help_menu.execute_action(InputAction.NAVIGATE_UP)
        assert result_up == ""
        assert graphical_help_menu.current_page == initial_page

        result_down = graphical_help_menu.execute_action(InputAction.NAVIGATE_DOWN)
        assert result_down == ""
        assert graphical_help_menu.current_page == initial_page


class TestHelpMenuContext:
    """Test input context detection for help menus."""

    def test_help_menu_context(self, help_menu):
        """HelpMenu should report HELP context."""
        assert help_menu.get_context() == InputContext.HELP

    def test_graphical_help_menu_context(self, graphical_help_menu):
        """GraphicalHelpMenu should report HELP context."""
        assert graphical_help_menu.get_context() == InputContext.HELP


class TestHelpMenuFactory:
    """Test the create_help_menu factory function."""

    def test_factory_creates_help_menu_for_text_mode(self):
        """Factory should create HelpMenu for text graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "text"

        menu = create_help_menu(settings)

        assert isinstance(menu, HelpMenu)

    def test_factory_creates_graphical_for_graphics_mode(self):
        """Factory should create GraphicalHelpMenu for graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_context = MagicMock()
        mock_tile_manager = MagicMock()

        from rsp.ui.menu_help_graphics import GraphicalHelpMenu

        menu = create_help_menu(settings, context=mock_context, tile_manager=mock_tile_manager)

        assert isinstance(menu, GraphicalHelpMenu)

    def test_factory_fails_without_tile_manager_in_graphics_mode(self):
        """Factory should raise error if tile_manager is missing in graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_context = MagicMock()

        with pytest.raises(RuntimeError) as exc_info:
            create_help_menu(settings, context=mock_context, tile_manager=None)

        assert "TileManager" in str(exc_info.value)

    def test_factory_fails_without_context_in_graphics_mode(self):
        """Factory should raise error if context is missing in graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_tile_manager = MagicMock()

        with pytest.raises(RuntimeError) as exc_info:
            create_help_menu(settings, context=None, tile_manager=mock_tile_manager)

        assert "context" in str(exc_info.value)


class TestGameLoopPollingCompatibility:
    """Test that menus work with game_loop.py polling logic."""

    def test_hasattr_check_for_graphical_menu(self, graphical_help_menu):
        """game_loop.py checks hasattr for _previous_page - should pass for GraphicalHelpMenu."""
        # Simulating game_loop.py logic:
        if hasattr(graphical_help_menu, "_previous_page"):
            # This branch should be taken for GraphicalHelpMenu
            result = graphical_help_menu._previous_page
            assert callable(result)
        else:
            pytest.fail("GraphicalHelpMenu should have _previous_page method")

    def test_hasattr_check_for_text_menu(self, help_menu):
        """game_loop.py checks hasattr for _previous_page - should fail for HelpMenu."""
        # Simulating game_loop.py logic:
        if hasattr(help_menu, "_previous_page"):
            pytest.fail("HelpMenu should NOT have _previous_page method")
        else:
            # This branch should be taken for HelpMenu
            # For HelpMenu, polling path should use navigate_left/navigate_right
            assert hasattr(help_menu, "navigate_left")
            assert hasattr(help_menu, "navigate_right")

    def test_common_interface_navigate_right(self, help_menu, graphical_help_menu):
        """Both menus should support navigate_right for common interface."""
        # This allows polling code to use a common interface
        graphical_help_menu._build_pages()

        help_menu.navigate_right()
        graphical_help_menu.navigate_right()

        assert help_menu.current_page == 1
        assert graphical_help_menu.current_page == 1

    def test_common_interface_navigate_left(self, help_menu, graphical_help_menu):
        """Both menus should support navigate_left for common interface."""
        graphical_help_menu._build_pages()

        help_menu.current_page = 2
        graphical_help_menu.current_page = 2

        help_menu.navigate_left()
        graphical_help_menu.navigate_left()

        assert help_menu.current_page == 1
        assert graphical_help_menu.current_page == 1


class TestHelpMenuGamepadButtons:
    """Test gamepad button handling in help menus."""

    def test_help_menu_has_gamepad_handler(self, help_menu):
        """HelpMenu should have a gamepad handler via BaseInputHandler."""
        assert hasattr(help_menu, "gamepad_handler")
        assert help_menu.gamepad_handler is not None

    def test_graphical_help_has_gamepad_handler(self, graphical_help_menu):
        """GraphicalHelpMenu should have a gamepad handler via BaseInputHandler."""
        assert hasattr(graphical_help_menu, "gamepad_handler")
        assert graphical_help_menu.gamepad_handler is not None

    def test_shoulder_buttons_change_pages(self, help_menu):
        """Shoulder buttons (LB/RB) should change pages."""
        # LB/RB are typically mapped to NAVIGATE_LEFT/RIGHT or page navigation
        # Test through execute_action since that's what input handler calls
        initial = help_menu.current_page
        help_menu.execute_action(InputAction.NAVIGATE_RIGHT)
        assert help_menu.current_page == initial + 1


class TestMouseWheelNavigation:
    """Test mouse wheel navigation in help menus."""

    def test_help_menu_wheel_up_previous_page(self, help_menu):
        """Mouse wheel up should go to previous page."""
        help_menu.current_page = 2
        mock_event = Mock()
        mock_event.y = 1  # Wheel up

        result = help_menu.handle_mouse_wheel(mock_event)

        assert result == ""
        assert help_menu.current_page == 1

    def test_help_menu_wheel_down_next_page(self, help_menu):
        """Mouse wheel down should go to next page."""
        initial = help_menu.current_page
        mock_event = Mock()
        mock_event.y = -1  # Wheel down

        result = help_menu.handle_mouse_wheel(mock_event)

        assert result == ""
        assert help_menu.current_page == initial + 1

    def test_graphical_help_wheel_up(self, graphical_help_menu):
        """GraphicalHelpMenu mouse wheel up should go to previous page."""
        graphical_help_menu._build_pages()
        graphical_help_menu.current_page = 2
        mock_event = Mock()
        mock_event.y = 1  # Wheel up

        result = graphical_help_menu.handle_mouse_wheel(mock_event)

        assert result == ""
        assert graphical_help_menu.current_page == 1

    def test_graphical_help_wheel_down(self, graphical_help_menu):
        """GraphicalHelpMenu mouse wheel down should go to next page."""
        graphical_help_menu._build_pages()
        initial = graphical_help_menu.current_page
        mock_event = Mock()
        mock_event.y = -1  # Wheel down

        result = graphical_help_menu.handle_mouse_wheel(mock_event)

        assert result == ""
        assert graphical_help_menu.current_page == initial + 1


class TestRightClickNavigation:
    """Test right-click returns to previous menu."""

    def test_help_menu_right_click_returns_back(self, help_menu):
        """Right-click in HelpMenu should return 'back'."""
        mock_event = Mock()
        result = help_menu.handle_right_click(mock_event)
        assert result == "back"

    def test_graphical_help_right_click_returns_back(self, graphical_help_menu):
        """Right-click in GraphicalHelpMenu should return 'back'."""
        mock_event = Mock()
        result = graphical_help_menu.handle_right_click(mock_event)
        assert result == "back"
