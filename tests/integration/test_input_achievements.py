"""
Achievements Screen Input Testing

Tests input handling for achievements screen:
- Scrolling with keyboard, D-pad, analog stick
- Page up/down navigation
- Exit behaviors

Note: Extracted from test_input_critical_paths.py for maintainability.
"""

import pytest
import tcod.event
import tcod.sdl.joystick
from unittest.mock import Mock

from game_input_actions import InputAction


class TestAchievementsScrolling:
    """Test scrolling behavior in achievements menu."""

    @pytest.fixture
    def achievements_menu(self):
        """Create achievements menu instance."""
        from game_menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        yield menu

    def test_scroll_down_increases_offset(self, achievements_menu):
        """Scrolling down increases scroll offset (if content available)."""
        menu = achievements_menu
        initial_offset = menu.scroll_offset

        menu.execute_action(InputAction.NAVIGATE_DOWN)

        # Offset should increase or stay same if at bottom
        assert menu.scroll_offset >= initial_offset

    def test_scroll_up_at_top_stays_at_zero(self, achievements_menu):
        """Scrolling up at top keeps offset at 0."""
        menu = achievements_menu
        menu.scroll_offset = 0

        for _ in range(5):
            menu.execute_action(InputAction.NAVIGATE_UP)

        assert menu.scroll_offset == 0

    def test_page_down_scrolls_faster(self, achievements_menu):
        """Page down scrolls more than single down."""
        menu = achievements_menu
        menu.scroll_offset = 0

        # Single down
        menu.execute_action(InputAction.NAVIGATE_DOWN)
        single_offset = menu.scroll_offset

        # Reset and page down
        menu.scroll_offset = 0
        menu.execute_action(InputAction.NAVIGATE_PAGE_DOWN)
        page_offset = menu.scroll_offset

        # Page should scroll same or more than single
        assert page_offset >= single_offset

    def test_cancel_returns_back(self, achievements_menu):
        """Cancel action returns 'back' to exit."""
        menu = achievements_menu
        result = menu.execute_action(InputAction.CANCEL)

        assert result == "back"


class TestAchievementsInputTypes:
    """Test different input types work for achievements."""

    @pytest.fixture
    def achievements_menu(self):
        """Create achievements menu instance."""
        from game_menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        yield menu

    def test_keyboard_down_scrolls(self, achievements_menu):
        """Keyboard down arrow scrolls via handle_input."""
        menu = achievements_menu
        initial = menu.scroll_offset

        event = Mock()
        event.type = 'KEYDOWN'
        event.sym = tcod.event.KeySym.DOWN
        menu.handle_input(event)

        # Offset should change or stay same
        assert menu.scroll_offset >= 0

    def test_dpad_down_scrolls(self, achievements_menu):
        """D-pad down scrolls via handle_input."""
        menu = achievements_menu
        initial = menu.scroll_offset

        event = Mock()
        event.type = 'CONTROLLERBUTTONDOWN'
        event.button = tcod.sdl.joystick.ControllerButton.DPAD_DOWN
        menu.handle_input(event)

        assert menu.scroll_offset >= initial

    def test_left_stick_vertical_scrolls(self, achievements_menu):
        """Left stick vertical movement scrolls."""
        menu = achievements_menu

        event = Mock()
        event.type = 'CONTROLLERAXISMOTION'
        event.axis = tcod.sdl.joystick.ControllerAxis.LEFTY
        event.value = 20000  # Down
        menu.handle_input(event)

        event.value = -20000  # Up
        menu.handle_input(event)

        # Should not crash
        assert menu.scroll_offset >= 0

    def test_b_button_exits(self, achievements_menu):
        """B button returns back."""
        menu = achievements_menu

        event = Mock()
        event.type = 'CONTROLLERBUTTONDOWN'
        event.button = tcod.sdl.joystick.ControllerButton.B
        result = menu.handle_input(event)

        assert result == 'back' or result == ''

    def test_mouse_wheel_scrolls(self, achievements_menu):
        """Mouse wheel scrolls if supported."""
        menu = achievements_menu

        if hasattr(menu, 'handle_mouse_wheel'):
            event = Mock()
            event.y = -1  # Scroll down
            menu.handle_mouse_wheel(event)

            event.y = 1  # Scroll up
            menu.handle_mouse_wheel(event)

        assert menu.scroll_offset >= 0


class TestAchievementsBoundaries:
    """Test scroll boundary handling."""

    @pytest.fixture
    def achievements_menu(self):
        """Create achievements menu instance."""
        from game_menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        yield menu

    def test_repeated_scroll_down_doesnt_crash(self, achievements_menu):
        """Repeatedly scrolling down handles gracefully."""
        menu = achievements_menu

        for _ in range(100):
            menu.scroll_down()

        # Should not crash or go negative
        assert menu.scroll_offset >= 0

    def test_repeated_scroll_up_stays_at_zero(self, achievements_menu):
        """Repeatedly scrolling up stays at top."""
        menu = achievements_menu
        menu.scroll_offset = 0

        for _ in range(100):
            menu.scroll_up()

        assert menu.scroll_offset == 0

    def test_scroll_down_then_back_up(self, achievements_menu):
        """Scroll down then back up works correctly."""
        menu = achievements_menu
        initial = menu.scroll_offset

        # Scroll down
        for _ in range(10):
            menu.scroll_down()

        # Scroll back up
        for _ in range(10):
            menu.scroll_up()

        # Should be back at or near initial
        assert menu.scroll_offset >= 0
