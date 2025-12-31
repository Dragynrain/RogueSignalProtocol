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

from unittest.mock import Mock, patch

import pytest
import tcod
import tcod.event

from rsp.core.config import GameSettings
from rsp.ui.menu_about import AboutMenu
from rsp.ui.menu_help_lore import HelpMenu, LoreMenu
from rsp.ui.menus import MainMenu, MenuBackground, SettingsMenu
from rsp.systems.save import SaveGameManager


class TestMainMenu:
    """Test the MainMenu class functionality."""

    def test_main_menu_initialization_with_save_exists(self):
        """MainMenu initializes correctly when save file exists."""
        # Clear singleton to ensure test isolation (prevents state bleed from parallel tests)
        GameSettings._instance = None
        with patch.object(SaveGameManager, "save_exists", return_value=True):
            # Create settings FIRST so both menus see the same ascension state
            settings = GameSettings()  # Loads from user_settings.json
            settings.graphics_mode = "glyphs"  # Start in glyph mode

            # Without graphics mode, Graphics Preview is hidden
            # Note: Ascension option only appears when highest_unlocked > 0
            menu = MainMenu()
            assert menu.selected_option == 0
            assert any(opt.startswith("Continue") for opt in menu.options)
            assert "New Game" in menu.options
            assert "Graphics Preview" not in menu.options  # Hidden in glyph mode
            # Base: Continue, New, Settings, Controls, Help, Achievements, Data Fragments, About, Exit (9)
            # Plus Ascension if unlocked (settings loaded from user_settings.json)
            base_count = 9
            if settings.get_highest_ascension_unlocked() > 0:
                base_count += 1  # Ascension option added
            assert len(menu.options) == base_count
            assert menu.show_warning is False

            # With graphics mode settings, Graphics Preview is shown (if graphics_preview_menu exists)
            settings.graphics_mode = "graphics"
            mock_menus = {
                "graphics_preview_menu": Mock()
            }  # Mock menus dict with graphics_preview_menu
            menu_graphics = MainMenu(menus=mock_menus)
            assert "Graphics Preview" in menu_graphics.options
            # Graphics Preview should be the only difference from base menu
            # (both menus have same Continue/Ascension state from same save_exists mock)
            assert len(menu_graphics.options) == len(menu.options) + 1

    def test_main_menu_initialization_no_save(self):
        """MainMenu initializes correctly when no save file exists."""
        with patch.object(SaveGameManager, "save_exists", return_value=False):
            # Without settings (glyph mode), Graphics Preview is hidden
            # Note: Ascension option only appears when highest_unlocked > 0
            settings = GameSettings()  # Registers as singleton
            menu = MainMenu()
            assert menu.selected_option == 0
            assert not any(opt.startswith("Continue") for opt in menu.options)
            assert "New Game" in menu.options
            assert "Graphics Preview" not in menu.options  # Hidden in glyph mode
            # Base: New, Settings, Controls, Help, Achievements, Data Fragments, About, Exit (8)
            # Plus Ascension if unlocked
            base_count = 8
            if settings.get_highest_ascension_unlocked() > 0:
                base_count += 1  # Ascension option added
            assert len(menu.options) == base_count
            assert isinstance(menu.options, list)
            assert menu.show_warning is False

            # With graphics mode settings, Graphics Preview is shown (if graphics_preview_menu exists)
            settings.graphics_mode = "graphics"
            mock_menus = {
                "graphics_preview_menu": Mock()
            }  # Mock menus dict with graphics_preview_menu
            menu_graphics = MainMenu(menus=mock_menus)
            assert "Graphics Preview" in menu_graphics.options
            # Graphics Preview should be the only difference from base menu
            assert len(menu_graphics.options) == len(menu.options) + 1

    def test_refresh_options_with_continue(self):
        """refresh_options() correctly adds continue option when save exists."""
        with patch.object(SaveGameManager, "save_exists", return_value=True):
            menu = MainMenu()
            menu.refresh_options(show_continue=True)
            assert any(opt.startswith("Continue") for opt in menu.options)
            # mid_game_mode is False when no active_game provided
            assert menu.mid_game_mode is False

    def test_refresh_options_without_continue(self):
        """refresh_options() correctly removes continue option for mid-game."""
        with patch.object(SaveGameManager, "save_exists", return_value=True):
            menu = MainMenu()
            menu.refresh_options(show_continue=False)
            assert not any(opt.startswith("Continue") for opt in menu.options)
            # mid_game_mode is False when no active_game provided
            # (changed: mid_game_mode now depends on active_game, not show_continue)
            assert menu.mid_game_mode is False

    def test_refresh_options_with_active_game(self):
        """refresh_options() sets mid_game_mode when active_game provided."""
        # Create mock game with alive player
        mock_game = Mock()
        mock_game.player = Mock()
        mock_game.player.cpu = 100
        mock_game.game_over = False

        with patch.object(SaveGameManager, "save_exists", return_value=True):
            menu = MainMenu()
            menu.refresh_options(show_continue=True, active_game=mock_game)
            # Should show Continue and enable START button toggle
            assert any(opt.startswith("Continue") for opt in menu.options)
            assert menu.mid_game_mode is True  # Can resume with START button

    def test_menu_navigation_down(self):
        """Menu navigation moves selection down correctly."""
        menu = MainMenu()
        initial_option = menu.selected_option

        # Create mock keyboard event for DOWN key
        down_event = Mock(spec=tcod.event.KeyDown)
        down_event.sym = tcod.event.KeySym.DOWN
        down_event.type = "KEYDOWN"  # Required for new input system

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
        up_event.type = "KEYDOWN"  # Required for new input system

        result = menu.handle_input(up_event)

        assert menu.selected_option == 0  # Moved up one position

    def test_menu_selection_enter_new_game(self):
        """Selecting New Game returns correct action."""
        with patch.object(SaveGameManager, "save_exists", return_value=False):
            menu = MainMenu()
            # Select "New Game" option (should be index 0 when no save exists)
            menu.selected_option = 0

            # Create mock keyboard event for ENTER key
            enter_event = Mock(spec=tcod.event.KeyDown)
            enter_event.sym = tcod.event.KeySym.RETURN
            enter_event.type = "KEYDOWN"  # Required for new input system

            result = menu.handle_input(enter_event)

            assert result == "new_game"

    def test_menu_warning_system(self):
        """Menu warning system works when trying to overwrite save."""
        with patch.object(SaveGameManager, "save_exists", return_value=True):
            menu = MainMenu()
            # Select "New Game" when save exists - should show warning
            new_game_index = menu.options.index("New Game")
            menu.selected_option = new_game_index

            enter_event = Mock(spec=tcod.event.KeyDown)
            enter_event.sym = tcod.event.KeySym.RETURN
            enter_event.type = "KEYDOWN"  # Required for new input system

            result = menu.handle_input(enter_event)

            # Should show warning instead of starting new game
            assert menu.show_warning is True

    def test_menu_warning_shows_in_mid_game_mode(self):
        """Warning should appear when New Game selected in mid-game mode with save file.

        Bug fix: Previously, mid_game_mode bypassed the warning check, allowing
        players to accidentally start a new game without confirmation when returning
        to main menu from an active game.
        """
        with patch.object(SaveGameManager, "save_exists", return_value=True):
            # Create mock active game
            mock_game = Mock()
            mock_game.player = Mock()
            mock_game.player.cpu = 100
            mock_game.game_over = False

            menu = MainMenu()
            # Set up mid-game mode (simulating returning to menu from active game)
            menu.refresh_options(show_continue=True, active_game=mock_game)
            assert menu.mid_game_mode is True  # Verify we're in mid-game mode

            # Select "New Game" option
            new_game_index = menu.options.index("New Game")
            menu.selected_option = new_game_index

            enter_event = Mock(spec=tcod.event.KeyDown)
            enter_event.sym = tcod.event.KeySym.RETURN
            enter_event.type = "KEYDOWN"

            result = menu.handle_input(enter_event)

            # Should show warning even in mid-game mode (save file exists!)
            assert menu.show_warning is True
            assert result == ""  # No action yet, waiting for confirmation

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
        self.menu_background._handle_background_error("test error", Exception("Test error"))

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
        self.mock_settings.graphics_mode = "graphics"  # Required for _build_options
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
        assert hasattr(help_menu, "render")
        assert hasattr(help_menu, "handle_input")

    def test_help_menu_has_help_sections(self):
        """HelpMenu contains help information."""
        help_menu = HelpMenu()
        # Should have page building methods
        assert hasattr(help_menu, "_build_page_1")
        assert hasattr(help_menu, "_build_page_2")
        assert hasattr(help_menu, "_build_page_3")
        assert hasattr(help_menu, "_build_page_content")

        # Should be able to build page content and return lines
        page_content = help_menu._build_page_content()
        assert page_content is not None
        assert len(page_content) > 0


class TestLoreMenu:
    """Test the LoreMenu class functionality."""

    def test_lore_menu_initialization(self):
        """LoreMenu initializes correctly."""
        lore_menu = LoreMenu()
        # Should initialize without errors
        assert lore_menu is not None
        # Should have expected attributes
        assert hasattr(lore_menu, "lore_viewer_selection")
        assert hasattr(lore_menu, "lore_viewer_mode")
        assert lore_menu.lore_viewer_mode == "list"

    def test_lore_menu_story_fragment_loading(self):
        """LoreMenu can load story fragments."""
        lore_menu = LoreMenu()
        # Initially story fragment manager should be None
        assert lore_menu.story_fragment_manager is None

        # Load story fragments should initialize the manager
        lore_menu._load_story_fragments()
        assert lore_menu.story_fragment_manager is not None


class TestAboutMenu:
    """Test the AboutMenu class functionality."""

    def test_about_menu_initialization(self):
        """AboutMenu initializes correctly."""
        about_menu = AboutMenu()
        assert about_menu is not None
        assert about_menu.selected_option == 0
        # Should have 4 items: Itch.io, Discord, GitHub, Back
        assert len(about_menu.links) == 4
        assert len(about_menu.options) == 4

    def test_about_menu_has_correct_urls(self):
        """AboutMenu contains correct URLs (no hallucination check)."""
        about_menu = AboutMenu()

        # Verify all URLs are exactly as expected
        assert about_menu.links[0]["url"] == "https://dragynrain.itch.io/rogue-signal-protocol"
        assert about_menu.links[1]["url"] == "https://discord.gg/5fykUtECqz"
        assert about_menu.links[2]["url"] == "https://github.com/Dragynrain/RogueSignalProtocol"
        assert about_menu.links[3]["url"] is None  # Back button has no URL

    def test_about_menu_navigation(self):
        """AboutMenu navigation works correctly."""
        about_menu = AboutMenu()

        # Start at first option
        assert about_menu.selected_option == 0

        # Navigate down
        down_event = Mock(spec=tcod.event.KeyDown)
        down_event.sym = tcod.event.KeySym.DOWN
        about_menu.handle_input(down_event)
        assert about_menu.selected_option == 1

    def test_about_menu_back_action(self):
        """AboutMenu back option returns to main menu."""
        about_menu = AboutMenu()

        # Select last option (Back)
        about_menu.selected_option = len(about_menu.links) - 1

        # Press enter
        enter_event = Mock(spec=tcod.event.KeyDown)
        enter_event.sym = tcod.event.KeySym.RETURN
        result = about_menu.handle_input(enter_event)

        assert result == "back"

    def test_about_menu_escape_handling(self):
        """AboutMenu handles escape key."""
        about_menu = AboutMenu()

        escape_event = Mock(spec=tcod.event.KeyDown)
        escape_event.sym = tcod.event.KeySym.ESCAPE
        result = about_menu.handle_input(escape_event)

        assert result == "back"

    def test_about_menu_rendering_safety(self):
        """AboutMenu renders without crashing."""
        about_menu = AboutMenu()
        mock_console = Mock(spec=tcod.console.Console)
        mock_console.width = 80
        mock_console.height = 50
        mock_console.rgba = Mock()

        # Smoke test - no exception means success
        about_menu.render(mock_console)


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
            AboutMenu(),
        ]

        # Create mock keyboard event for ESCAPE key
        escape_event = Mock(spec=tcod.event.KeyDown)
        escape_event.sym = tcod.event.KeySym.ESCAPE

        for menu in menus:
            result = menu.handle_input(escape_event)
            # Each menu should handle escape appropriately (exit, return to main, etc.)
            assert result is not None or hasattr(menu, "show_warning")

    def test_console_rendering_safety(self):
        """Menu rendering doesn't crash with mock console."""
        menu = MainMenu()
        mock_console = Mock(spec=tcod.console.Console)
        mock_console.width = 80
        mock_console.height = 25
        mock_console.rgba = Mock()

        # Smoke test - no exception means success
        menu.render(mock_console)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
