#!/usr/bin/env python3
"""
Comprehensive Menu System Tests

Tests all menu functionality including:
- MainMenu (initialization, navigation, selection, warnings)
- HelpMenu and LoreMenu
- MenuBackground (graphics mode handling)
- SettingsMenu
- Menu navigation logic and state management
- Menu integration and error handling

Consolidated from test_menus.py and test_menu_system.py
"""

import pytest
from unittest.mock import Mock, patch
import tcod
import tcod.event

from game_menus import MenuBackground, MainMenu, SettingsMenu
from game_menu_help_lore import LoreMenu, HelpMenu
from game_save import SaveGameManager
from game_config import GameSettings


class TestMainMenu:
    """Test the MainMenu class functionality."""

    def test_main_menu_initialization_with_save_exists(self):
        """MainMenu initializes correctly when save file exists."""
        with patch.object(SaveGameManager, 'save_exists', return_value=True):
            menu = MainMenu()
            assert menu.selected_option == 0
            assert "Continue Game" in menu.options
            assert "New Game" in menu.options
            assert len(menu.options) == 8  # Continue, New, Settings, Help, Achievements, Lore, Graphics Preview, Exit
            assert menu.show_warning is False

    def test_main_menu_initialization_no_save(self):
        """MainMenu initializes correctly when no save file exists."""
        with patch.object(SaveGameManager, 'save_exists', return_value=False):
            menu = MainMenu()
            assert menu.selected_option == 0
            assert "Continue Game" not in menu.options
            assert "New Game" in menu.options
            assert len(menu.options) == 7  # New, Settings, Help, Achievements, Lore, Graphics Preview, Exit
            assert isinstance(menu.options, list)
            assert menu.show_warning is False

    def test_refresh_options_with_continue(self):
        """refresh_options() correctly adds continue option when save exists."""
        with patch.object(SaveGameManager, 'save_exists', return_value=True):
            menu = MainMenu()
            menu.refresh_options(show_continue=True)
            assert "Continue Game" in menu.options
            assert menu.mid_game_mode is False

    def test_refresh_options_without_continue(self):
        """refresh_options() correctly removes continue option for mid-game."""
        with patch.object(SaveGameManager, 'save_exists', return_value=True):
            menu = MainMenu()
            menu.refresh_options(show_continue=False)
            assert "Continue Game" not in menu.options
            assert menu.mid_game_mode is True

    def test_menu_navigation_down(self):
        """Menu navigation moves selection down correctly."""
        menu = MainMenu()
        initial_option = menu.selected_option

        # Create mock keyboard event for DOWN key
        down_event = Mock(spec=tcod.event.KeyDown)
        down_event.sym = tcod.event.KeySym.DOWN

        result = menu.handle_input(down_event)

        # Should move selection down (wrapping at end)
        if initial_option < len(menu.options) - 1:
            assert menu.selected_option == initial_option + 1
        else:
            assert menu.selected_option == 0  # Wrapped to beginning

    def test_menu_navigation_up(self):
        """Menu navigation moves selection up correctly."""
        menu = MainMenu()
        menu.selected_option = 1  # Start at second option

        # Create mock keyboard event for UP key
        up_event = Mock(spec=tcod.event.KeyDown)
        up_event.sym = tcod.event.KeySym.UP

        result = menu.handle_input(up_event)

        assert menu.selected_option == 0  # Moved up one position

    def test_menu_selection_enter_new_game(self):
        """Selecting New Game returns correct action."""
        with patch.object(SaveGameManager, 'save_exists', return_value=False):
            menu = MainMenu()
            # Select "New Game" option (should be index 0 when no save exists)
            menu.selected_option = 0

            # Create mock keyboard event for ENTER key
            enter_event = Mock(spec=tcod.event.KeyDown)
            enter_event.sym = tcod.event.KeySym.RETURN

            result = menu.handle_input(enter_event)

            assert result == "new_game"

    def test_menu_warning_system(self):
        """Menu warning system works when trying to overwrite save."""
        with patch.object(SaveGameManager, 'save_exists', return_value=True):
            menu = MainMenu()
            # Select "New Game" when save exists - should show warning
            new_game_index = menu.options.index("New Game")
            menu.selected_option = new_game_index

            enter_event = Mock(spec=tcod.event.KeyDown)
            enter_event.sym = tcod.event.KeySym.RETURN

            result = menu.handle_input(enter_event)

            # Should show warning instead of starting new game
            assert menu.show_warning is True

    def test_background_trace(self):
        """Menu correctly detects if background is available."""
        # Test without background
        menu = MainMenu()
        has_bg = menu._has_background()
        # Should be falsy (False, None, or empty)
        assert not has_bg

        # Test with mock background
        mock_background = Mock()
        mock_background.should_load_background.return_value = True
        mock_background.background_texture = Mock()  # Not None

        menu_with_bg = MainMenu(background=mock_background)
        result = menu_with_bg._has_background()
        # Should be truthy (the actual texture object or True)
        assert result


class TestMenuBackground:
    """Test menu background behavior for graphics mode."""

    def setup_method(self):
        """Set up menu background tests."""
        self.mock_context = Mock()
        self.mock_context.sdl_renderer = Mock()
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_settings.graphics_mode = "graphics"

        self.menu_background = MenuBackground(self.mock_context, self.mock_settings)

    def test_should_load_background_graphics_mode(self):
        """Should load background in graphics mode."""
        self.mock_settings.graphics_mode = "graphics"
        self.menu_background.enabled = True
        self.mock_context.sdl_renderer = Mock()

        result = self.menu_background.should_load_background()
        assert result is True

    def test_should_not_load_background_ascii_mode(self):
        """Should not load background in glyph mode."""
        self.mock_settings.graphics_mode = "glyph"

        result = self.menu_background.should_load_background()
        assert result is False

    def test_should_not_load_background_when_disabled(self):
        """Should not load background when disabled."""
        self.mock_settings.graphics_mode = "graphics"
        self.menu_background.enabled = False

        result = self.menu_background.should_load_background()
        assert result is False

    def test_error_handling_disables_background(self):
        """Background handles errors by disabling."""
        self.menu_background._handle_background_error(
            'test error',
            Exception("Test error")
        )

        assert self.menu_background.enabled is False

    def test_reset_background_system(self):
        """Background system can be reset after errors."""
        self.menu_background.enabled = False
        self.menu_background.reset_background_system()

        assert self.menu_background.enabled is True


class TestSettingsMenu:
    """Test settings menu behavior."""

    def setup_method(self):
        """Set up settings menu tests."""
        self.mock_settings = Mock(spec=GameSettings)
        self.settings_menu = SettingsMenu(self.mock_settings)

    def test_settings_menu_initialization(self):
        """Settings menu initializes correctly."""
        assert self.settings_menu is not None


class TestHelpMenu:
    """Test the HelpMenu class functionality."""

    def test_help_menu_initialization(self):
        """HelpMenu initializes correctly."""
        help_menu = HelpMenu()
        # Should initialize without errors
        assert help_menu is not None
        # Should have render method
        assert hasattr(help_menu, 'render')
        assert hasattr(help_menu, 'handle_input')

    def test_help_menu_has_help_sections(self):
        """HelpMenu contains help information."""
        help_menu = HelpMenu()
        # Should have help sections method
        assert hasattr(help_menu, '_get_help_sections')

        # Get help sections should return content
        help_sections = help_menu._get_help_sections()
        assert help_sections is not None
        assert len(help_sections) > 0


class TestLoreMenu:
    """Test the LoreMenu class functionality."""

    def test_lore_menu_initialization(self):
        """LoreMenu initializes correctly."""
        lore_menu = LoreMenu()
        # Should initialize without errors
        assert lore_menu is not None
        # Should have expected attributes
        assert hasattr(lore_menu, 'lore_viewer_selection')
        assert hasattr(lore_menu, 'lore_viewer_mode')
        assert lore_menu.lore_viewer_mode == "list"

    def test_lore_menu_story_fragment_loading(self):
        """LoreMenu can load story fragments."""
        lore_menu = LoreMenu()
        # Initially story fragment manager should be None
        assert lore_menu.story_fragment_manager is None

        # Load story fragments should initialize the manager
        lore_menu._load_story_fragments()
        assert lore_menu.story_fragment_manager is not None


class TestMenuNavigation:
    """Test menu navigation logic (pure algorithmic tests)."""

    def test_menu_navigation_up_down(self):
        """Menu navigation wraps correctly."""
        menu_items = ["Option 1", "Option 2", "Option 3", "Option 4"]
        selected_index = 0

        # Navigate down
        selected_index = (selected_index + 1) % len(menu_items)
        assert selected_index == 1

        # Navigate up
        selected_index = (selected_index - 1) % len(menu_items)
        assert selected_index == 0

        # Navigate up from first item (should wrap to last)
        selected_index = (selected_index - 1) % len(menu_items)
        assert selected_index == 3

    def test_menu_selection_validation(self):
        """Menu selection validation works correctly."""
        menu_items = ["New Game", "Load Game", "Settings", "Quit"]

        # Valid selections
        for i in range(len(menu_items)):
            assert 0 <= i < len(menu_items)

        # Invalid selections should be handled
        invalid_indices = [-1, len(menu_items), 100]
        for invalid_index in invalid_indices:
            # Should clamp to valid range
            clamped_index = max(0, min(invalid_index, len(menu_items) - 1))
            assert 0 <= clamped_index < len(menu_items)

    def test_menu_state_management(self):
        """Menu state stack management works correctly."""
        menu_stack = []

        # Push menu states
        menu_stack.append("main_menu")
        assert len(menu_stack) == 1
        assert menu_stack[-1] == "main_menu"

        menu_stack.append("settings_menu")
        assert len(menu_stack) == 2
        assert menu_stack[-1] == "settings_menu"

        # Pop menu states
        current_menu = menu_stack.pop()
        assert current_menu == "settings_menu"
        assert len(menu_stack) == 1
        assert menu_stack[-1] == "main_menu"


class TestMenuIntegration:
    """Test menu system integration and transitions."""

    def test_menu_escape_handling(self):
        """All menus handle escape key appropriately."""
        menus = [
            MainMenu(),
            HelpMenu(),
        ]

        # Create mock keyboard event for ESCAPE key
        escape_event = Mock(spec=tcod.event.KeyDown)
        escape_event.sym = tcod.event.KeySym.ESCAPE

        for menu in menus:
            result = menu.handle_input(escape_event)
            # Each menu should handle escape appropriately (exit, return to main, etc.)
            assert result is not None or hasattr(menu, 'show_warning')

    def test_console_rendering_safety(self):
        """Menu rendering doesn't crash with mock console."""
        menu = MainMenu()
        mock_console = Mock(spec=tcod.console.Console)
        mock_console.width = 80
        mock_console.height = 25
        mock_console.rgba = Mock()

        # Should not raise exceptions
        try:
            menu.render(mock_console)
            assert True
        except Exception as e:
            pytest.fail(f"Menu rendering failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
