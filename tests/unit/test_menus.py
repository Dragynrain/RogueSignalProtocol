#!/usr/bin/env python3
"""
Unit tests for Menu functionality testing real menu behavior.
Focus on actual menu classes and their methods.
"""

import pytest
from unittest.mock import Mock, patch
import tcod
import tcod.event

# Import actual menu classes
from game_menus import MainMenu
from game_menu_help_lore import LoreMenu, HelpMenu
from game_save import SaveGameManager


class TestMainMenu:
    """Test the actual MainMenu class functionality."""
    
    def test_main_menu_initialization_with_save_exists(self):
        """MainMenu initializes correctly when save file exists."""
        with patch.object(SaveGameManager, 'save_exists', return_value=True):
            menu = MainMenu()
            assert menu.selected_option == 0
            assert "Continue Game" in menu.options
            assert "New Game" in menu.options
            assert len(menu.options) == 7  # Continue, New, Settings, Help, Lore, Graphics Preview, Exit
    
    def test_main_menu_initialization_no_save(self):
        """MainMenu initializes correctly when no save file exists."""
        with patch.object(SaveGameManager, 'save_exists', return_value=False):
            menu = MainMenu()
            assert menu.selected_option == 0
            assert "Continue Game" not in menu.options
            assert "New Game" in menu.options
            assert len(menu.options) == 6  # New, Settings, Help, Lore, Graphics Preview, Exit
    
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