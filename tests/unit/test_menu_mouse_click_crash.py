"""
Test for mouse click crash in menu system.

Regression test for AttributeError: 'AchievementsMenu' object has no attribute 'handle_mouse_click'
"""

from unittest.mock import Mock

import tcod.event

from rsp.core.config import GameSettings
from rsp.ui.menu_achievements import AchievementsMenu
from rsp.ui.menu_main import MainMenu
from rsp.ui.menu_settings import SettingsMenu


class TestMenuMouseClickCrash:
    """Test that all menus handle mouse clicks without crashing."""

    def test_achievements_menu_handle_mouse_click_exists(self):
        """AchievementsMenu should have handle_mouse_click method."""
        menu = AchievementsMenu()
        assert hasattr(
            menu, "handle_mouse_click"
        ), "AchievementsMenu missing handle_mouse_click method"

    def test_achievements_menu_left_click_does_not_crash(self):
        """AchievementsMenu should handle left click without crashing."""
        menu = AchievementsMenu()

        # Create a mock left click event
        event = Mock(spec=tcod.event.MouseButtonDown)
        event.position = Mock()
        event.position.x = 40
        event.position.y = 25
        event.button = tcod.event.MouseButton.LEFT

        # This should not raise AttributeError
        result = menu.handle_mouse_click(event)
        # Menu click handlers return "" (no action) or "back" (exit menu)
        assert result in (
            "",
            "back",
        ), f"handle_mouse_click should return '' or 'back', got {result!r}"

    def test_achievements_menu_right_click_returns_back(self):
        """AchievementsMenu should return 'back' on right click."""
        menu = AchievementsMenu()

        # Create a mock right click event
        event = Mock(spec=tcod.event.MouseButtonDown)
        event.position = Mock()
        event.position.x = 40
        event.position.y = 25
        event.button = tcod.event.MouseButton.RIGHT

        result = menu.handle_mouse_click(event)
        assert result == "back", "Right click should return 'back'"

    def test_main_menu_handle_mouse_click_exists(self):
        """MainMenu should have handle_mouse_click method."""
        menu = MainMenu()
        assert hasattr(menu, "handle_mouse_click"), "MainMenu missing handle_mouse_click method"

    def test_settings_menu_handle_mouse_click_exists(self):
        """SettingsMenu should have handle_mouse_click method."""
        mock_settings = Mock(spec=GameSettings)
        mock_settings.graphics_mode = "graphics"  # Required for _build_options
        menu = SettingsMenu(mock_settings)
        assert hasattr(menu, "handle_mouse_click"), "SettingsMenu missing handle_mouse_click method"
