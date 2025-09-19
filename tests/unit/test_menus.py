#!/usr/bin/env python3
"""
Unit tests for game menu files - covering menu functionality.
Tests game_menu_main.py, game_menu_background.py, and game_menu_help_lore.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod

from game_menu_main import MainMenu
from game_menu_background import MenuBackground
from game_menu_help_lore import HelpMenu, LoreMenu
from game_config import GameSettings


class TestMainMenu:
    """Test MainMenu functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_background = Mock()
        self.main_menu = MainMenu(background=self.mock_background)
    
    def test_initialization(self):
        """Test MainMenu initialization."""
        assert self.main_menu.selected_option == 0
        assert self.main_menu.show_warning is False
        assert self.main_menu.warning_selection == 0
        assert self.main_menu.mid_game_mode is False
        assert self.main_menu.background == self.mock_background
    
    def test_initialization_no_background(self):
        """Test MainMenu initialization without background."""
        menu = MainMenu()
        assert menu.background is None
    
    @patch('game_menu_main.SaveGameManager.save_exists')
    def test_refresh_options_with_save(self, mock_save_exists):
        """Test refresh_options when save exists."""
        mock_save_exists.return_value = True
        
        self.main_menu.refresh_options(show_continue=True)
        
        expected_options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"]
        assert self.main_menu.options == expected_options
        assert self.main_menu.mid_game_mode is False
        assert self.main_menu.selected_option == 0
        assert self.main_menu.show_warning is False
    
    @patch('game_menu_main.SaveGameManager.save_exists')
    def test_refresh_options_no_save(self, mock_save_exists):
        """Test refresh_options when no save exists."""
        mock_save_exists.return_value = False
        
        self.main_menu.refresh_options(show_continue=True)
        
        expected_options = ["New Game", "Settings", "Help", "Lore", "Exit"]
        assert self.main_menu.options == expected_options
    
    def test_refresh_options_mid_game_mode(self):
        """Test refresh_options in mid-game mode."""
        self.main_menu.refresh_options(show_continue=False)
        
        expected_options = ["New Game", "Settings", "Help", "Lore", "Exit"]
        assert self.main_menu.options == expected_options
        assert self.main_menu.mid_game_mode is True
    
    def test_has_background_true(self):
        """Test _has_background when background is available."""
        self.mock_background.should_load_background.return_value = True
        self.mock_background.background_texture = "some_texture"  # Truthy non-Mock value
        
        result = self.main_menu._has_background()
        
        assert result == "some_texture"  # Returns the last truthy value
    
    def test_has_background_false_no_background(self):
        """Test _has_background when no background object."""
        menu = MainMenu(background=None)
        
        result = menu._has_background()
        
        assert not result  # Should be falsy (None or False)
    
    def test_has_background_false_should_not_load(self):
        """Test _has_background when should_load_background is False."""
        self.mock_background.should_load_background.return_value = False
        
        result = self.main_menu._has_background()
        
        assert not result  # Should be falsy (None or False)
    
    def test_has_background_false_no_texture(self):
        """Test _has_background when no background texture."""
        self.mock_background.should_load_background.return_value = True
        self.mock_background.background_texture = None
        
        result = self.main_menu._has_background()
        
        assert not result  # Should be falsy (None or False)
    
    @patch.object(MainMenu, '_has_background')
    @patch.object(MainMenu, '_clear_text_areas_only')
    @patch.object(MainMenu, '_render_full_screen')
    def test_render_with_background(self, mock_render_full, mock_clear_text, mock_has_bg):
        """Test render method with background."""
        mock_has_bg.return_value = True
        mock_console = Mock()
        
        self.main_menu.render(mock_console)
        
        mock_clear_text.assert_called_once_with(mock_console)
        mock_render_full.assert_not_called()
    
    @patch.object(MainMenu, '_has_background')
    @patch.object(MainMenu, '_render_full_screen')
    def test_render_without_background(self, mock_render_full, mock_has_bg):
        """Test render method without background."""
        mock_has_bg.return_value = False
        mock_console = Mock()
        
        self.main_menu.render(mock_console)
        
        mock_render_full.assert_called_once_with(mock_console)
    
    def test_handle_input_navigation(self):
        """Test input handling for navigation."""
        # Mock key events
        up_event = Mock()
        up_event.sym = tcod.event.KeySym.UP
        down_event = Mock() 
        down_event.sym = tcod.event.KeySym.DOWN
        
        # Test down navigation
        initial_selection = self.main_menu.selected_option
        result = self.main_menu.handle_input(down_event)
        
        assert result is None  # No action
        assert self.main_menu.selected_option == (initial_selection + 1) % len(self.main_menu.options)
        
        # Test up navigation
        result = self.main_menu.handle_input(up_event)
        
        assert result is None  # No action
        assert self.main_menu.selected_option == initial_selection  # Should wrap around
    
    def test_handle_input_enter_actions(self):
        """Test input handling for enter key actions."""
        enter_event = Mock()
        enter_event.sym = tcod.event.KeySym.RETURN
        
        # Test different menu selections
        test_cases = [
            (0, "continue"),  # Assuming first option is Continue
            (1, "new_game"),  # New Game
            (2, "settings"),  # Settings
            (3, "help"),      # Help
            (4, "lore"),      # Lore
            (5, "exit")       # Exit
        ]
        
        for selection, expected_action in test_cases:
            self.main_menu.selected_option = selection
            
            # Skip if selection is out of range for current options
            if selection >= len(self.main_menu.options):
                continue
                
            result = self.main_menu.handle_input(enter_event)
            assert result == expected_action
    
    def test_handle_input_escape_key(self):
        """Test input handling for escape key."""
        escape_event = Mock()
        escape_event.sym = tcod.event.KeySym.ESCAPE
        
        result = self.main_menu.handle_input(escape_event)
        
        assert result == "exit"


class TestMenuBackground:
    """Test MenuBackground functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_settings = Mock()
        self.mock_settings.graphics_mode = "graphics"
        self.menu_background = MenuBackground(self.mock_context, self.mock_settings)
    
    def test_initialization(self):
        """Test MenuBackground initialization."""
        assert self.menu_background.context == self.mock_context
        assert self.menu_background.settings == self.mock_settings
        assert self.menu_background.background_texture is None
        assert self.menu_background.current_image_path is None
    
    def test_should_load_background_graphics_mode(self):
        """Test should_load_background in graphics mode."""
        self.mock_settings.graphics_mode = "graphics"
        
        result = self.menu_background.should_load_background()
        
        assert result is True
    
    def test_should_load_background_ascii_mode(self):
        """Test should_load_background in ASCII mode."""
        self.mock_settings.graphics_mode = "ascii"
        
        result = self.menu_background.should_load_background()
        
        assert result is False
    
    @patch('random.choice')
    @patch('os.path.exists')
    @patch('glob.glob')
    def test_load_random_background_success(self, mock_glob, mock_exists, mock_choice):
        """Test successful random background loading."""
        mock_glob.return_value = ["bg1.jpg", "bg2.png", "bg3.jpg"]
        mock_choice.return_value = "bg2.png"
        mock_exists.return_value = True
        
        with patch.object(self.menu_background, '_load_background_image') as mock_load:
            mock_load.return_value = True
            
            result = self.menu_background.load_random_background()
            
            assert result is True
            mock_load.assert_called_once_with("bg2.png")
    
    @patch('glob.glob')
    def test_load_random_background_no_images(self, mock_glob):
        """Test load_random_background when no images found."""
        mock_glob.return_value = []
        
        with patch('logging.warning') as mock_log:
            result = self.menu_background.load_random_background()
            
            assert result is False
            mock_log.assert_called()
    
    def test_cleanup(self):
        """Test cleanup method."""
        # Set up some state to clean
        self.menu_background.background_texture = Mock()
        self.menu_background.current_image_path = "test.jpg"
        
        self.menu_background.cleanup()
        
        assert self.menu_background.background_texture is None
        assert self.menu_background.current_image_path is None
    
    def test_reset_background_system(self):
        """Test reset_background_system method."""
        # This method exists to reset error states
        # Test that it can be called without error
        self.menu_background.reset_background_system()
        
        # Method should complete without raising exceptions
        assert True
    
    def test_reload_if_mode_changed_graphics_to_ascii(self):
        """Test reload when switching from graphics to ASCII mode."""
        self.menu_background.background_texture = Mock()
        self.mock_settings.graphics_mode = "ascii"  # Changed to ASCII
        
        self.menu_background.reload_if_mode_changed()
        
        # Background should be cleaned up
        assert self.menu_background.background_texture is None
    
    def test_reload_if_mode_changed_ascii_to_graphics(self):
        """Test reload when switching from ASCII to graphics mode."""
        self.menu_background.background_texture = None
        self.mock_settings.graphics_mode = "graphics"  # Changed to graphics
        
        with patch.object(self.menu_background, 'load_random_background') as mock_load:
            self.menu_background.reload_if_mode_changed()
            
            mock_load.assert_called_once()


class TestHelpMenu:
    """Test HelpMenu functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.help_menu = HelpMenu()
    
    def test_initialization(self):
        """Test HelpMenu initialization."""
        assert self.help_menu.selected_section == 0
        assert isinstance(self.help_menu.sections, list)
        assert len(self.help_menu.sections) > 0
    
    def test_render(self):
        """Test HelpMenu render method."""
        mock_console = Mock()
        
        # Should not raise an exception
        self.help_menu.render(mock_console)
        
        # Console should have been used for rendering
        assert mock_console.method_calls  # Some methods should have been called
    
    def test_handle_input_navigation(self):
        """Test HelpMenu input handling for navigation."""
        up_event = Mock()
        up_event.sym = tcod.event.KeySym.UP
        down_event = Mock()
        down_event.sym = tcod.event.KeySym.DOWN
        
        initial_section = self.help_menu.selected_section
        
        # Test navigation
        result_down = self.help_menu.handle_input(down_event)
        assert result_down is None
        
        result_up = self.help_menu.handle_input(up_event)
        assert result_up is None
    
    def test_handle_input_escape(self):
        """Test HelpMenu escape key handling."""
        escape_event = Mock()
        escape_event.sym = tcod.event.KeySym.ESCAPE
        
        result = self.help_menu.handle_input(escape_event)
        
        assert result == "back"


class TestLoreMenu:
    """Test LoreMenu functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lore_menu = LoreMenu()
    
    def test_initialization(self):
        """Test LoreMenu initialization."""
        assert self.lore_menu.selected_entry == 0
        assert hasattr(self.lore_menu, 'lore_entries')
    
    def test_render(self):
        """Test LoreMenu render method."""
        mock_console = Mock()
        
        # Should not raise an exception
        self.lore_menu.render(mock_console)
        
        # Console should have been used for rendering
        assert mock_console.method_calls  # Some methods should have been called
    
    def test_handle_input_navigation(self):
        """Test LoreMenu input handling for navigation."""
        up_event = Mock()
        up_event.sym = tcod.event.KeySym.UP
        down_event = Mock()
        down_event.sym = tcod.event.KeySym.DOWN
        
        # Test navigation
        result_down = self.lore_menu.handle_input(down_event)
        assert result_down is None
        
        result_up = self.lore_menu.handle_input(up_event)
        assert result_up is None
    
    def test_handle_input_escape(self):
        """Test LoreMenu escape key handling."""
        escape_event = Mock()
        escape_event.sym = tcod.event.KeySym.ESCAPE
        
        result = self.lore_menu.handle_input(escape_event)
        
        assert result == "back"


class TestMenuIntegration:
    """Integration tests for menu system."""
    
    @patch('game_menu_main.SaveGameManager.save_exists')
    def test_menu_workflow_with_save(self, mock_save_exists):
        """Test complete menu workflow when save exists."""
        mock_save_exists.return_value = True
        
        menu = MainMenu()
        menu.refresh_options()
        
        # Should include Continue Game option
        assert "Continue Game" in menu.options
        
        # Test selecting continue game
        enter_event = Mock()
        enter_event.sym = tcod.event.KeySym.RETURN
        menu.selected_option = 0  # Continue Game
        
        result = menu.handle_input(enter_event)
        assert result == "continue"
    
    @patch('game_menu_main.SaveGameManager.save_exists')
    def test_menu_workflow_no_save(self, mock_save_exists):
        """Test complete menu workflow when no save exists."""
        mock_save_exists.return_value = False
        
        menu = MainMenu()
        menu.refresh_options()
        
        # Should not include Continue Game option
        assert "Continue Game" not in menu.options
        assert "New Game" in menu.options
        
        # Test selecting new game
        enter_event = Mock()
        enter_event.sym = tcod.event.KeySym.RETURN
        menu.selected_option = 0  # New Game (first option when no save)
        
        result = menu.handle_input(enter_event)
        assert result == "new_game"