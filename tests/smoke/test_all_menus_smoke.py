#!/usr/bin/env python3
"""
All Menus Smoke Test

Validates that all menu classes can be instantiated and have basic properties.
Quick sanity check that menu definitions are not broken.
"""

from unittest.mock import Mock, patch

import pytest
import tcod

from game_config import GameSettings
from game_menu_about import AboutMenu
from game_menu_achievements import AchievementsMenu
from game_menu_graphics_preview import GraphicsPreviewMenu
from game_menu_help_graphics import GraphicalHelpMenu
from game_menu_help_lore import HelpMenu, LoreMenu
from game_menus import MainMenu, SettingsMenu


class TestAllMenusSmoke:
    """Smoke test for all menu classes."""

    def test_main_menu_instantiation(self):
        """MainMenu can be instantiated without errors."""
        with patch("game_menu_main.SaveGameManager.save_exists", return_value=False):
            menu = MainMenu()
            assert menu is not None
            assert hasattr(menu, "options")
            assert len(menu.options) > 0

    def test_settings_menu_instantiation(self):
        """SettingsMenu can be instantiated without errors."""
        mock_settings = Mock(spec=GameSettings)
        mock_settings.graphics_mode = "glyph"
        mock_settings.audio_enabled = True
        mock_settings.music_volume = 0.5
        mock_settings.sfx_volume = 0.5
        mock_settings.dialogue_skip = False

        menu = SettingsMenu(mock_settings)
        assert menu is not None
        assert hasattr(menu, "options")
        assert len(menu.options) > 0

    def test_about_menu_instantiation(self):
        """AboutMenu can be instantiated without errors."""
        menu = AboutMenu()
        assert menu is not None
        # About menu may not have selectable options (just display)
        assert hasattr(menu, "options")

    def test_achievements_menu_instantiation(self):
        """AchievementsMenu can be instantiated without errors."""
        menu = AchievementsMenu()
        assert menu is not None

    def test_help_menu_instantiation(self):
        """HelpMenu can be instantiated without errors."""
        menu = HelpMenu()
        assert menu is not None

    def test_lore_menu_instantiation(self):
        """LoreMenu can be instantiated without errors."""
        menu = LoreMenu()
        assert menu is not None

    @pytest.mark.skip(
        reason="GraphicsPreviewMenu requires full graphics stack (SDL, tile files, etc.). "
        "Cannot be tested in headless environment. Tested in manual QA."
    )
    def test_graphics_preview_menu_instantiation(self):
        """GraphicsPreviewMenu requires full graphics environment - tested manually."""
        pass  # Tested during manual QA with full graphics stack

    @pytest.mark.skip(
        reason="GraphicalHelpMenu requires full graphics stack (SDL, tile files, etc.). "
        "Cannot be tested in headless environment. Tested in manual QA."
    )
    def test_graphical_help_menu_instantiation(self):
        """GraphicalHelpMenu requires full graphics environment - tested manually."""
        pass  # Tested during manual QA with full graphics stack

    def test_all_menus_have_render_method(self):
        """All menu classes have a render method."""
        menu_classes = [
            (MainMenu, {}),
            (SettingsMenu, {"settings": Mock(spec=GameSettings)}),
            (AboutMenu, {}),
            (HelpMenu, {}),
            (LoreMenu, {}),
        ]

        for menu_class, kwargs in menu_classes:
            # Add defaults for SettingsMenu
            if menu_class == SettingsMenu:
                mock_settings = Mock(spec=GameSettings)
                mock_settings.graphics_mode = "glyph"
                mock_settings.audio_enabled = True
                mock_settings.music_volume = 0.5
                mock_settings.sfx_volume = 0.5
                mock_settings.dialogue_skip = False
                kwargs["settings"] = mock_settings

            # Instantiate menu
            if menu_class == MainMenu:
                with patch("game_menu_main.SaveGameManager.save_exists", return_value=False):
                    menu = menu_class(**kwargs)
            else:
                menu = menu_class(**kwargs)

            # Check render method exists
            assert hasattr(menu, "render"), f"{menu_class.__name__} missing render method"
            assert callable(menu.render), f"{menu_class.__name__}.render is not callable"

    def test_all_menus_have_handle_input_method(self):
        """All menu classes have a handle_input method."""
        menu_classes = [
            (MainMenu, {}),
            (SettingsMenu, {"settings": Mock(spec=GameSettings)}),
            (AboutMenu, {}),
            (HelpMenu, {}),
            (LoreMenu, {}),
        ]

        for menu_class, kwargs in menu_classes:
            # Add defaults for SettingsMenu
            if menu_class == SettingsMenu:
                mock_settings = Mock(spec=GameSettings)
                mock_settings.graphics_mode = "glyph"
                mock_settings.audio_enabled = True
                mock_settings.music_volume = 0.5
                mock_settings.sfx_volume = 0.5
                mock_settings.dialogue_skip = False
                kwargs["settings"] = mock_settings

            # Instantiate menu
            if menu_class == MainMenu:
                with patch("game_menu_main.SaveGameManager.save_exists", return_value=False):
                    menu = menu_class(**kwargs)
            else:
                menu = menu_class(**kwargs)

            # Check handle_input method exists
            assert hasattr(
                menu, "handle_input"
            ), f"{menu_class.__name__} missing handle_input method"
            assert callable(
                menu.handle_input
            ), f"{menu_class.__name__}.handle_input is not callable"

    def test_main_menu_has_expected_options(self):
        """MainMenu has expected options."""
        with patch("game_menu_main.SaveGameManager.save_exists", return_value=False):
            menu = MainMenu()

            # Should have at least these core options
            assert any("New Game" in opt for opt in menu.options)
            assert any("Settings" in opt for opt in menu.options)
            assert any("Exit" in opt for opt in menu.options)

    def test_settings_menu_has_expected_options(self):
        """SettingsMenu has expected options."""
        mock_settings = Mock(spec=GameSettings)
        mock_settings.graphics_mode = "glyph"
        mock_settings.audio_enabled = True
        mock_settings.music_volume = 0.5
        mock_settings.sfx_volume = 0.5
        mock_settings.dialogue_skip = False

        menu = SettingsMenu(mock_settings)

        # Should have settings-related options
        assert len(menu.options) > 0

    def test_help_menu_can_render(self):
        """HelpMenu can render without crashing."""
        menu = HelpMenu()
        test_console = tcod.console.Console(width=80, height=50)

        try:
            menu.render(test_console)
            assert True
        except Exception as e:
            pytest.fail(f"HelpMenu.render() crashed: {e}")

    def test_menus_can_render_to_console(self):
        """Menus can render to a test console without crashing."""
        test_console = tcod.console.Console(width=80, height=50)

        # Test a simple menu
        with patch("game_menu_main.SaveGameManager.save_exists", return_value=False):
            menu = MainMenu()
            try:
                menu.render(test_console)
                # If render completes without exception, that's success
                assert True
            except Exception as e:
                pytest.fail(f"MainMenu.render() crashed: {e}")
