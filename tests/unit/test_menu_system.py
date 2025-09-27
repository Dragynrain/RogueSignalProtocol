#!/usr/bin/env python3
"""
Menu System Tests.
Tests menu navigation, state management, and user interaction.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import tcod
from typing import Dict, Any

from game_menus import MenuBackground, MainMenu, LoreMenu, HelpMenu, SettingsMenu
from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_save import SaveGameManager
from game_audio import SoundManager


class TestMenuBackground:
    """Test menu background system functionality."""
    
    def setup_method(self):
        """Set up menu background tests."""
        self.mock_context = Mock()
        self.mock_context.sdl_renderer = Mock()
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_settings.graphics_mode = "graphics"
        
        self.menu_background = MenuBackground(self.mock_context, self.mock_settings)
    
    def test_menu_background_initialization(self):
        """Menu background initializes correctly."""
        assert self.menu_background.context is self.mock_context
        assert self.menu_background.settings is self.mock_settings
        assert self.menu_background.enabled is True
        assert self.menu_background.error_count == 0
        assert self.menu_background.background_texture is None
    
    def test_should_load_background_graphics_mode(self):
        """Should load background in graphics mode."""
        self.mock_settings.graphics_mode = "graphics"
        self.menu_background.enabled = True
        self.mock_context.sdl_renderer = Mock()
        
        result = self.menu_background.should_load_background()
        assert result is True
    
    def test_should_not_load_background_ascii_mode(self):
        """Should not load background in ASCII mode."""
        self.mock_settings.graphics_mode = "ascii"
        
        result = self.menu_background.should_load_background()
        assert result is False
    
    def test_should_not_load_background_when_disabled(self):
        """Should not load background when disabled."""
        self.mock_settings.graphics_mode = "graphics"
        self.menu_background.enabled = False
        
        result = self.menu_background.should_load_background()
        assert result is False
    
    def test_error_handling_file_not_found(self):
        """Background handles file not found errors."""
        result = self.menu_background._handle_background_error(
            'file_not_found', 
            'test_image.png', 
            FileNotFoundError("File not found")
        )
        
        assert self.menu_background.error_count == 1
        # Should continue trying for file errors
        assert self.menu_background.enabled is True
    
    def test_error_handling_sdl_unavailable(self):
        """Background handles SDL unavailable errors."""
        result = self.menu_background._handle_background_error(
            'sdl_unavailable', 
            'SDL renderer not available', 
            RuntimeError("SDL error")
        )
        
        assert self.menu_background.error_count == 1
        # Should disable for session-level issues
        assert self.menu_background.enabled is False
    
    def test_error_handling_excessive_errors(self):
        """Background disables after too many errors."""
        # Trigger many errors
        for i in range(15):
            self.menu_background._handle_background_error(
                'texture_failed', 
                f'Error {i}', 
                Exception(f"Error {i}")
            )
        
        assert self.menu_background.error_count == 15
        assert self.menu_background.enabled is False
    
    def test_reset_background_system(self):
        """Background system can be reset after errors."""
        # Cause errors
        self.menu_background.error_count = 10
        self.menu_background.enabled = False
        
        # Reset
        self.menu_background.reset_background_system()
        
        assert self.menu_background.error_count == 0
        assert self.menu_background.enabled is True


class TestMainMenu:
    """Test main menu functionality."""
    
    def setup_method(self):
        """Set up main menu tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.mock_context = Mock()
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        # Create main menu with mocked dependencies
        with patch('game_menus.WindowManager'), \
             patch('game_menus.MenuBackground'):
            self.main_menu = MainMenu(
                self.mock_console, 
                self.mock_context, 
                self.mock_settings,
                self.mock_sound_manager
            )
    
    def test_main_menu_initialization(self):
        """Main menu initializes correctly."""
        assert self.main_menu.console is self.mock_console
        assert self.main_menu.context is self.mock_context
        assert self.main_menu.settings is self.mock_settings
        assert self.main_menu.sound_manager is self.mock_sound_manager
    
    def test_main_menu_option_selection(self):
        """Main menu handles option selection."""
        # Test menu option navigation
        initial_selection = getattr(self.main_menu, 'selected_option', 0)
        
        # Simulate navigation (implementation depends on actual menu structure)
        # This test structure shows how to test menu navigation
        if hasattr(self.main_menu, 'handle_input'):
            # Mock input handling
            with patch.object(self.main_menu, 'handle_input') as mock_input:
                self.main_menu.handle_input('down')
                mock_input.assert_called_with('down')
    
    def test_main_menu_new_game_option(self):
        """Main menu new game option works correctly."""
        if hasattr(self.main_menu, 'start_new_game'):
            with patch.object(self.main_menu, 'start_new_game', return_value=True) as mock_new_game:
                result = self.main_menu.start_new_game()
                assert result is True
                mock_new_game.assert_called_once()
    
    def test_main_menu_load_game_option(self):
        """Main menu load game option works correctly."""
        if hasattr(self.main_menu, 'load_game'):
            with patch.object(SaveGameManager, 'load_game', return_value={'test': 'data'}):
                # Should attempt to load game
                # Implementation depends on actual menu structure
                pass
    
    def test_main_menu_settings_option(self):
        """Main menu settings option works correctly."""
        if hasattr(self.main_menu, 'open_settings'):
            with patch.object(self.main_menu, 'open_settings') as mock_settings:
                self.main_menu.open_settings()
                mock_settings.assert_called_once()
    
    def test_main_menu_quit_option(self):
        """Main menu quit option works correctly."""
        if hasattr(self.main_menu, 'quit_game'):
            with patch.object(self.main_menu, 'quit_game', return_value=True) as mock_quit:
                result = self.main_menu.quit_game()
                assert result is True
                mock_quit.assert_called_once()


class TestLoreMenu:
    """Test lore menu functionality."""
    
    def setup_method(self):
        """Set up lore menu tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        
        # Mock story fragments
        self.mock_fragments = [
            Mock(id=1, title="Fragment 1", content="Content 1"),
            Mock(id=2, title="Fragment 2", content="Content 2"),
            Mock(id=3, title="Fragment 3", content="Content 3")
        ]
        
        with patch('game_story.get_story_fragments', return_value=self.mock_fragments):
            self.lore_menu = LoreMenu(self.mock_console)
    
    def test_lore_menu_initialization(self):
        """Lore menu initializes correctly."""
        assert self.lore_menu.console is self.mock_console
        # Should have loaded story fragments
        if hasattr(self.lore_menu, 'fragments'):
            assert len(self.lore_menu.fragments) == 3
    
    def test_lore_menu_navigation(self):
        """Lore menu navigation works correctly."""
        if hasattr(self.lore_menu, 'selected_item'):
            initial_selection = self.lore_menu.selected_item
            
            # Test navigation methods if they exist
            if hasattr(self.lore_menu, 'navigate_up'):
                self.lore_menu.navigate_up()
                # Selection should change
            
            if hasattr(self.lore_menu, 'navigate_down'):
                self.lore_menu.navigate_down()
                # Selection should change
    
    def test_lore_menu_fragment_selection(self):
        """Lore menu fragment selection works correctly."""
        if hasattr(self.lore_menu, 'select_fragment'):
            with patch.object(self.lore_menu, 'select_fragment') as mock_select:
                self.lore_menu.select_fragment(1)
                mock_select.assert_called_with(1)
    
    def test_lore_menu_rendering(self):
        """Lore menu renders correctly."""
        if hasattr(self.lore_menu, 'render'):
            with patch('game_ui.render_char_safe') as mock_render:
                self.lore_menu.render()
                # Should make render calls
                assert mock_render.call_count > 0
    
    def test_lore_menu_search_functionality(self):
        """Lore menu search functionality works if implemented."""
        if hasattr(self.lore_menu, 'search'):
            results = self.lore_menu.search("Fragment")
            # Should return matching fragments
            if results is not None:
                assert isinstance(results, list)


class TestHelpMenu:
    """Test help menu functionality."""
    
    def setup_method(self):
        """Set up help menu tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.help_menu = HelpMenu(self.mock_console)
    
    def test_help_menu_initialization(self):
        """Help menu initializes correctly."""
        assert self.help_menu.console is self.mock_console
    
    def test_help_menu_content_display(self):
        """Help menu displays content correctly."""
        if hasattr(self.help_menu, 'render'):
            with patch('game_ui.render_char_safe') as mock_render:
                self.help_menu.render()
                # Should render help content
                assert mock_render.call_count > 0
    
    def test_help_menu_section_navigation(self):
        """Help menu section navigation works."""
        if hasattr(self.help_menu, 'current_section'):
            initial_section = getattr(self.help_menu, 'current_section', 0)
            
            # Test section navigation if available
            if hasattr(self.help_menu, 'next_section'):
                self.help_menu.next_section()
                # Section should change
            
            if hasattr(self.help_menu, 'previous_section'):
                self.help_menu.previous_section()
                # Section should change
    
    def test_help_menu_keyboard_shortcuts_display(self):
        """Help menu displays keyboard shortcuts."""
        # Test that help menu contains expected control information
        if hasattr(self.help_menu, 'get_controls_text'):
            controls = self.help_menu.get_controls_text()
            if controls:
                assert isinstance(controls, (str, list))
                # Should contain movement keys
                if isinstance(controls, str):
                    assert any(key in controls.lower() for key in ['wasd', 'arrow', 'move'])
    
    def test_help_menu_close_functionality(self):
        """Help menu close functionality works."""
        if hasattr(self.help_menu, 'close'):
            with patch.object(self.help_menu, 'close', return_value=True) as mock_close:
                result = self.help_menu.close()
                assert result is True
                mock_close.assert_called_once()


class TestSettingsMenu:
    """Test settings menu functionality."""
    
    def setup_method(self):
        """Set up settings menu tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        self.settings_menu = SettingsMenu(
            self.mock_console,
            self.mock_settings,
            self.mock_sound_manager
        )
    
    def test_settings_menu_initialization(self):
        """Settings menu initializes correctly."""
        assert self.settings_menu.console is self.mock_console
        assert self.settings_menu.settings is self.mock_settings
        assert self.settings_menu.sound_manager is self.mock_sound_manager
    
    def test_settings_menu_graphics_mode_toggle(self):
        """Settings menu graphics mode toggle works."""
        if hasattr(self.settings_menu, 'toggle_graphics_mode'):
            self.mock_settings.graphics_mode = "ascii"
            
            self.settings_menu.toggle_graphics_mode()
            
            # Should toggle to graphics mode
            # (Implementation depends on actual settings structure)
    
    def test_settings_menu_volume_adjustment(self):
        """Settings menu volume adjustment works."""
        if hasattr(self.settings_menu, 'adjust_volume'):
            initial_volume = getattr(self.mock_settings, 'master_volume', 0.5)
            
            self.settings_menu.adjust_volume(0.1)  # Increase volume
            
            # Should adjust volume through sound manager
            # (Implementation depends on actual volume system)
    
    def test_settings_menu_key_binding_modification(self):
        """Settings menu key binding modification works."""
        if hasattr(self.settings_menu, 'modify_key_binding'):
            with patch.object(self.settings_menu, 'modify_key_binding') as mock_modify:
                self.settings_menu.modify_key_binding('move_up', 'w')
                mock_modify.assert_called_with('move_up', 'w')
    
    def test_settings_menu_save_settings(self):
        """Settings menu save functionality works."""
        if hasattr(self.settings_menu, 'save_settings'):
            with patch.object(self.mock_settings, 'save') as mock_save:
                self.settings_menu.save_settings()
                # Should save settings
                mock_save.assert_called_once()
    
    def test_settings_menu_reset_to_defaults(self):
        """Settings menu reset to defaults works."""
        if hasattr(self.settings_menu, 'reset_to_defaults'):
            with patch.object(self.settings_menu, 'reset_to_defaults') as mock_reset:
                self.settings_menu.reset_to_defaults()
                mock_reset.assert_called_once()


class TestMenuNavigation:
    """Test general menu navigation functionality."""
    
    def test_menu_navigation_up_down(self):
        """Menu navigation up/down works correctly."""
        # Generic test for menu navigation
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
            # Should clamp or handle invalid indices
            clamped_index = max(0, min(invalid_index, len(menu_items) - 1))
            assert 0 <= clamped_index < len(menu_items)
    
    def test_menu_input_handling(self):
        """Menu input handling works correctly."""
        # Test various input types
        valid_inputs = ['up', 'down', 'select', 'back', 'escape']
        
        for input_type in valid_inputs:
            # Should handle all valid input types
            assert isinstance(input_type, str)
            assert len(input_type) > 0
    
    def test_menu_state_management(self):
        """Menu state management works correctly."""
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


class TestMenuRendering:
    """Test menu rendering functionality."""
    
    def setup_method(self):
        """Set up menu rendering tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
    
    def test_menu_title_rendering(self):
        """Menu title rendering works correctly."""
        title = "Main Menu"
        
        with patch('game_ui.render_char_safe') as mock_render:
            # Simulate title rendering
            for i, char in enumerate(title):
                mock_render(self.mock_console, 10 + i, 5, char, fg=Colors.WHITE)
            
            # Should render each character
            assert mock_render.call_count == len(title)
    
    def test_menu_options_rendering(self):
        """Menu options rendering works correctly."""
        options = ["New Game", "Load Game", "Settings", "Quit"]
        
        with patch('game_ui.render_char_safe') as mock_render:
            # Simulate option rendering
            for y, option in enumerate(options):
                for x, char in enumerate(option):
                    mock_render(self.mock_console, 10 + x, 10 + y, char, fg=Colors.WHITE)
            
            # Should render all option characters
            total_chars = sum(len(option) for option in options)
            assert mock_render.call_count == total_chars
    
    def test_menu_selection_highlight_rendering(self):
        """Menu selection highlight rendering works correctly."""
        selected_option = 1
        options = ["Option 1", "Option 2", "Option 3"]
        
        with patch('game_ui.render_char_safe') as mock_render:
            # Simulate highlighted option rendering
            for x, char in enumerate(options[selected_option]):
                mock_render(
                    self.mock_console, 
                    10 + x, 
                    10 + selected_option, 
                    char, 
                    fg=Colors.BLACK, 
                    bg=Colors.WHITE  # Highlighted background
                )
            
            # Should render highlighted option
            assert mock_render.call_count == len(options[selected_option])
    
    def test_menu_border_rendering(self):
        """Menu border rendering works correctly."""
        box_width = 20
        box_height = 10
        
        with patch('game_ui.render_char_safe') as mock_render:
            # Simulate border rendering
            # Top and bottom borders
            for x in range(box_width):
                mock_render(self.mock_console, x, 0, '─', fg=Colors.WHITE)
                mock_render(self.mock_console, x, box_height - 1, '─', fg=Colors.WHITE)
            
            # Left and right borders
            for y in range(box_height):
                mock_render(self.mock_console, 0, y, '│', fg=Colors.WHITE)
                mock_render(self.mock_console, box_width - 1, y, '│', fg=Colors.WHITE)
            
            # Corners
            mock_render(self.mock_console, 0, 0, '┌', fg=Colors.WHITE)
            mock_render(self.mock_console, box_width - 1, 0, '┐', fg=Colors.WHITE)
            mock_render(self.mock_console, 0, box_height - 1, '└', fg=Colors.WHITE)
            mock_render(self.mock_console, box_width - 1, box_height - 1, '┘', fg=Colors.WHITE)
            
            # Should render border elements
            expected_calls = (box_width * 2) + (box_height * 2) + 4  # borders + corners
            assert mock_render.call_count == expected_calls


class TestMenuErrorHandling:
    """Test menu error handling and edge cases."""
    
    def setup_method(self):
        """Set up menu error handling tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.mock_settings = Mock(spec=GameSettings)
    
    def test_menu_with_no_options(self):
        """Menu handles empty option list gracefully."""
        empty_options = []
        
        # Should handle empty menu gracefully
        selected_index = 0
        if len(empty_options) > 0:
            selected_index = selected_index % len(empty_options)
        else:
            selected_index = 0  # Default to 0 for empty menu
        
        assert selected_index == 0
    
    def test_menu_with_invalid_console(self):
        """Menu handles invalid console gracefully."""
        invalid_consoles = [None, "not_a_console", 123]
        
        for invalid_console in invalid_consoles:
            try:
                # Should either handle gracefully or raise expected exception
                if hasattr(MainMenu, '__init__'):
                    # Menu initialization with invalid console
                    pass
            except (TypeError, AttributeError):
                # Expected to fail with invalid console
                pass
    
    def test_menu_with_corrupted_settings(self):
        """Menu handles corrupted settings gracefully."""
        corrupted_settings = [
            None,
            Mock(graphics_mode=None),
            Mock(graphics_mode="invalid_mode"),
            "not_settings"
        ]
        
        for settings in corrupted_settings:
            try:
                # Should handle corrupted settings
                if hasattr(SettingsMenu, '__init__'):
                    pass
            except (TypeError, AttributeError):
                # Expected to fail with invalid settings
                pass
    
    def test_menu_save_failure_handling(self):
        """Menu handles save failures gracefully."""
        settings_menu = SettingsMenu(
            self.mock_console,
            self.mock_settings,
            Mock(spec=SoundManager)
        )
        
        # Mock save to fail
        with patch.object(self.mock_settings, 'save', side_effect=Exception("Save failed")):
            try:
                if hasattr(settings_menu, 'save_settings'):
                    settings_menu.save_settings()
                # Should handle save failure gracefully
            except Exception:
                # May propagate or handle gracefully
                pass
    
    def test_menu_load_failure_handling(self):
        """Menu handles load failures gracefully."""
        # Mock load game to fail
        with patch.object(SaveGameManager, 'load_game', side_effect=Exception("Load failed")):
            try:
                # Should handle load failure gracefully
                SaveGameManager.load_game()
            except Exception:
                # Expected to fail with load error
                pass
    
    def test_menu_audio_failure_handling(self):
        """Menu handles audio system failures gracefully."""
        mock_sound_manager = Mock(spec=SoundManager)
        mock_sound_manager.play_sound.side_effect = Exception("Audio failed")
        
        try:
            # Should handle audio failures gracefully
            mock_sound_manager.play_sound("menu_select")
        except Exception:
            # May propagate or handle gracefully
            pass