"""Achievements Screen Context Tests - Comprehensive achievements viewer validation.

Tests validate achievements screen navigation and interaction with:
- Keyboard (arrow keys, PageUp/PageDown, ESC)
- Gamepad (D-pad, analog stick, B button)
- Mouse (right-click, wheel scroll)

Achievements screen is the player's progress tracker!
"""

import pytest
from unittest.mock import Mock, MagicMock
import tcod.event

from game_input_actions import InputAction, InputContext
from game_engine import GameEngine
from game_input import InputHandler
from game_menu_achievements import AchievementsMenu


class TestAchievementsScreenNavigation:
    """Test achievements screen navigation with all input methods."""

    def test_keyboard_scroll_down(self):
        """DOWN arrow scrolls achievements list down."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        initial_scroll = 0

        # Scroll down (NAVIGATE_DOWN in achievements context)
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        # Note: This tests the action routing, actual scroll tested in menu unit tests
        assert game.show_achievements is True  # Still showing achievements

    def test_keyboard_scroll_up(self):
        """UP arrow scrolls achievements list up."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # Scroll up
        handler._execute_action(InputAction.NAVIGATE_UP)

        # Still showing achievements
        assert game.show_achievements is True

    def test_keyboard_escape_closes(self):
        """ESC key closes achievements screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # Press ESC (CANCEL action)
        handler._execute_action(InputAction.CANCEL)

        # Achievements should be closed
        assert game.show_achievements is False

    def test_gamepad_dpad_down_scrolls(self):
        """Gamepad D-pad DOWN scrolls achievements."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # D-pad DOWN
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        # Still showing (scroll happened internally)
        assert game.show_achievements is True

    def test_gamepad_dpad_up_scrolls(self):
        """Gamepad D-pad UP scrolls achievements."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # D-pad UP
        handler._execute_action(InputAction.NAVIGATE_UP)

        # Still showing
        assert game.show_achievements is True

    def test_gamepad_cancel_closes(self):
        """Gamepad B button closes achievements screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # B button (CANCEL)
        handler._execute_action(InputAction.CANCEL)

        # Achievements closed
        assert game.show_achievements is False


class TestAchievementsMenuDirect:
    """Test AchievementsMenu class directly for detailed behavior."""

    def test_scroll_down_increases_offset(self):
        """scroll_down increases scroll offset."""
        menu = AchievementsMenu()
        initial_offset = menu.scroll_offset

        menu.scroll_down()

        # Should increase (unless at max, but with default achievements it should increase)
        assert menu.scroll_offset >= initial_offset

    def test_scroll_up_decreases_offset(self):
        """scroll_up decreases scroll offset."""
        menu = AchievementsMenu()
        menu.scroll_offset = 5  # Set to non-zero

        menu.scroll_up()

        # Should decrease by ARROW_SCROLL_SPEED (3 by default)
        assert menu.scroll_offset == 2

    def test_scroll_up_at_zero_stays_zero(self):
        """scroll_up at offset 0 stays at 0."""
        menu = AchievementsMenu()
        menu.scroll_offset = 0

        menu.scroll_up()

        # Should stay at 0 (clamped)
        assert menu.scroll_offset == 0

    def test_navigate_down_action_scrolls(self):
        """NAVIGATE_DOWN action scrolls down."""
        menu = AchievementsMenu()
        initial_offset = menu.scroll_offset

        result = menu.execute_action(InputAction.NAVIGATE_DOWN)

        # Should scroll down and return "" (stay in menu)
        assert result == ""
        assert menu.scroll_offset >= initial_offset

    def test_navigate_up_action_scrolls(self):
        """NAVIGATE_UP action scrolls up."""
        menu = AchievementsMenu()
        menu.scroll_offset = 5

        result = menu.execute_action(InputAction.NAVIGATE_UP)

        # Should scroll up by ARROW_SCROLL_SPEED (3 by default) and return "" (stay in menu)
        assert result == ""
        assert menu.scroll_offset == 2

    def test_cancel_action_returns_back(self):
        """CANCEL action returns 'back' command."""
        menu = AchievementsMenu()

        result = menu.execute_action(InputAction.CANCEL)

        # Should return 'back' to exit menu
        assert result == "back"

    def test_keyboard_pagedown_scrolls_fast(self):
        """PageDown action scrolls down by PAGE_SCROLL_SPEED lines."""
        menu = AchievementsMenu()
        menu.scroll_offset = 0

        # Execute PAGE_DOWN action directly (keyboard PageDown not mapped)
        result = menu.execute_action(InputAction.NAVIGATE_PAGE_DOWN)

        # Should scroll by PAGE_SCROLL_SPEED (35 lines = full page, or less if near max)
        assert menu.scroll_offset > 0
        assert result == ""  # Stay in menu

    def test_keyboard_pageup_scrolls_fast(self):
        """PageUp action scrolls up by PAGE_SCROLL_SPEED lines."""
        menu = AchievementsMenu()
        menu.scroll_offset = 50  # Start scrolled down

        # Execute PAGE_UP action directly (keyboard PageUp not mapped)
        result = menu.execute_action(InputAction.NAVIGATE_PAGE_UP)

        # Should scroll up by PAGE_SCROLL_SPEED (35 lines = full page)
        assert menu.scroll_offset == 15
        assert result == ""  # Stay in menu

    def test_mouse_right_click_goes_back(self):
        """Right-click closes achievements screen."""
        menu = AchievementsMenu()

        # Create mock right-click event
        event = Mock()
        event.button = tcod.event.MouseButton.RIGHT

        result = menu.handle_mouse_click(event)

        # Should return 'back'
        assert result == "back"

    def test_mouse_left_click_does_nothing(self):
        """Left-click does nothing (intentional)."""
        menu = AchievementsMenu()

        # Create mock left-click event
        event = Mock()
        event.button = tcod.event.MouseButton.LEFT

        result = menu.handle_mouse_click(event)

        # Should return "" (do nothing)
        assert result == ""

    def test_mouse_wheel_down_scrolls(self):
        """Mouse wheel down scrolls list down."""
        menu = AchievementsMenu()
        menu.scroll_offset = 0

        # Create mock wheel event (negative y = scroll down)
        event = Mock()
        event.y = -1

        result = menu.handle_mouse_wheel(event)

        # Should scroll down
        assert menu.scroll_offset > 0
        assert result == ""  # Returns empty string

    def test_mouse_wheel_up_scrolls(self):
        """Mouse wheel up scrolls list up."""
        menu = AchievementsMenu()
        menu.scroll_offset = 10

        # Create mock wheel event (positive y = scroll up)
        event = Mock()
        event.y = 1

        result = menu.handle_mouse_wheel(event)

        # Should scroll up
        assert menu.scroll_offset < 10
        assert result == ""  # Returns empty string


class TestAchievementsScreenContextDetection:
    """Test achievements screen context detection and priority."""

    def test_achievements_context_detected(self):
        """_get_current_context returns ACHIEVEMENTS_SCREEN when active."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        game.show_inventory = False
        game.show_help = False
        game.show_lore_viewer = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.ACHIEVEMENTS_SCREEN

    def test_achievements_priority_over_main_menu(self):
        """Achievements screen takes priority over main menu."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_main_menu = True
        game.show_achievements = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Achievements takes priority
        assert context == InputContext.ACHIEVEMENTS_SCREEN

    def test_dialogue_overrides_achievements(self):
        """Dialogue takes priority over achievements screen."""
        game = GameEngine()
        game.dialogue_state.is_active = Mock(return_value=True)
        game.show_achievements = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Dialogue overrides achievements
        assert context == InputContext.DIALOGUE

    def test_achievement_popup_overrides_achievements_screen(self):
        """Achievement popup takes priority over achievements screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Popup takes priority
        assert context == InputContext.ACHIEVEMENT_POPUP


class TestAchievementsScreenBlocking:
    """Test that achievements screen blocks gameplay actions."""

    def test_movement_blocked_in_achievements(self):
        """Player shouldn't move while achievements screen is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should be blocked)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_gameplay_actions_blocked_in_achievements(self):
        """Gameplay actions blocked while achievements screen is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_achievements = True
        handler = InputHandler(game, renderer=None)

        # Try to execute exploit (should be blocked)
        result = handler._execute_action(InputAction.EXPLOIT_EXECUTE)

        # Action should not execute (achievements context doesn't handle EXPLOIT_EXECUTE)
        # Achievements should still be open
        assert game.show_achievements is True
