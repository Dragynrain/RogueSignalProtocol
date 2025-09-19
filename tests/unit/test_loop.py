#!/usr/bin/env python3
"""
Unit tests for game_loop.py - Game loop and initialization functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod
import time

from game_loop import (
    load_tileset, initialize_tcod_context, WindowManager, 
    initialize_game_systems, handle_error_screen
)
from game_config import GameConfig, GameSettings


class TestLoadTileset:
    """Test tileset loading functionality."""
    
    @patch('tcod.tileset.load_tilesheet')
    def test_load_tileset_success(self, mock_load_tilesheet):
        """Test successful tileset loading."""
        mock_tileset = Mock()
        mock_load_tilesheet.return_value = mock_tileset
        
        result = load_tileset()
        
        mock_load_tilesheet.assert_called_once_with(
            "terminal10x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437
        )
        assert result == mock_tileset
    
    @patch('tcod.tileset.load_tilesheet')
    def test_load_tileset_logs_success(self, mock_load_tilesheet):
        """Test that successful loading is logged."""
        mock_tileset = Mock()
        mock_load_tilesheet.return_value = mock_tileset
        
        with patch('logging.info') as mock_log:
            load_tileset()
            mock_log.assert_called_with("Loaded terminal tileset successfully")


class TestInitializeTcodContext:
    """Test TCOD context initialization."""
    
    @patch('game_loop.load_tileset')
    @patch('tcod.context.new')
    def test_initialize_tcod_context_basic(self, mock_context_new, mock_load_tileset):
        """Test basic context initialization."""
        mock_tileset = Mock()
        mock_load_tileset.return_value = mock_tileset
        mock_context = Mock()
        mock_context_new.return_value = mock_context
        
        result = initialize_tcod_context()
        
        # Verify context creation with correct arguments
        expected_args = {
            "columns": GameConfig.SCREEN_WIDTH,
            "rows": GameConfig.SCREEN_HEIGHT,
            "title": "Rogue Signal Protocol",
            "vsync": True,
            "sdl_window_flags": 160,
            "tileset": mock_tileset
        }
        mock_context_new.assert_called_once_with(**expected_args)
        assert result == mock_context
    
    @patch('game_loop.load_tileset')
    @patch('tcod.context.new')
    def test_initialize_tcod_context_no_tileset(self, mock_context_new, mock_load_tileset):
        """Test context initialization when tileset is None."""
        mock_load_tileset.return_value = None
        mock_context = Mock()
        mock_context_new.return_value = mock_context
        
        result = initialize_tcod_context()
        
        # Should not include tileset in arguments
        call_args = mock_context_new.call_args[1]
        assert "tileset" not in call_args
        assert result == mock_context
    
    @patch('game_loop.load_tileset')
    @patch('tcod.context.new')
    @patch('tcod.render.SDLTilesetAtlas')
    @patch('tcod.render.SDLConsoleRender')
    def test_initialize_tcod_context_with_sdl_renderer(self, mock_console_render_class, 
                                                      mock_atlas_class, mock_context_new, 
                                                      mock_load_tileset):
        """Test context initialization with SDL renderer available."""
        mock_tileset = Mock()
        mock_load_tileset.return_value = mock_tileset
        
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()  # SDL renderer available
        mock_context_new.return_value = mock_context
        
        mock_atlas = Mock()
        mock_atlas_class.return_value = mock_atlas
        mock_console_render = Mock()
        mock_console_render_class.return_value = mock_console_render
        
        with patch('logging.info') as mock_log:
            result = initialize_tcod_context()
            
            # Verify SDL components were created
            mock_atlas_class.assert_called_once_with(mock_context.sdl_renderer, mock_tileset)
            mock_console_render_class.assert_called_once_with(mock_atlas)
            
            # Verify console render was attached
            assert result.console_render == mock_console_render
            
            # Verify logging
            mock_log.assert_any_call("SDL renderer available for graphics mode")
            mock_log.assert_any_call("Console texture rendering initialized successfully")
    
    @patch('game_loop.load_tileset')
    @patch('tcod.context.new')
    def test_initialize_tcod_context_no_sdl_renderer(self, mock_context_new, mock_load_tileset):
        """Test context initialization without SDL renderer."""
        mock_load_tileset.return_value = Mock()
        
        mock_context = Mock()
        mock_context.sdl_renderer = None  # No SDL renderer
        mock_context_new.return_value = mock_context
        
        with patch('logging.warning') as mock_log:
            result = initialize_tcod_context()
            
            assert result.console_render is None
            mock_log.assert_called_with("SDL renderer unavailable - graphics mode will be disabled")
    
    @patch('game_loop.load_tileset')
    @patch('tcod.context.new')
    @patch('tcod.render.SDLTilesetAtlas')
    def test_initialize_tcod_context_render_failure(self, mock_atlas_class, mock_context_new, mock_load_tileset):
        """Test context initialization when console rendering fails."""
        mock_load_tileset.return_value = Mock()
        
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()
        mock_context_new.return_value = mock_context
        
        # Make atlas creation fail
        mock_atlas_class.side_effect = Exception("Atlas creation failed")
        
        with patch('logging.warning') as mock_log:
            result = initialize_tcod_context()
            
            assert result.console_render is None
            mock_log.assert_called_with("Failed to initialize console rendering: Atlas creation failed")


class TestWindowManager:
    """Test WindowManager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.window_manager = WindowManager(self.mock_context)
    
    def test_initialization(self):
        """Test WindowManager initialization."""
        assert self.window_manager.context == self.mock_context
        assert self.window_manager._cached_dimensions is None
        assert self.window_manager._last_check_time == 0
    
    @patch('time.time')
    def test_get_window_pixel_dimensions_with_window(self, mock_time):
        """Test getting window dimensions when SDL window is available."""
        mock_time.return_value = 100.0
        
        mock_window = Mock()
        mock_window.size = (1024, 768)
        self.mock_context.sdl_window = mock_window
        
        dimensions = self.window_manager.get_window_pixel_dimensions()
        
        assert dimensions == (1024, 768)
        assert self.window_manager._cached_dimensions == (1024, 768)
        assert self.window_manager._last_check_time == 100.0
    
    @patch('time.time')
    def test_get_window_pixel_dimensions_no_window(self, mock_time):
        """Test getting window dimensions when SDL window is not available."""
        mock_time.return_value = 100.0
        self.mock_context.sdl_window = None
        
        dimensions = self.window_manager.get_window_pixel_dimensions()
        
        assert dimensions == (800, 600)  # Fallback dimensions
        assert self.window_manager._cached_dimensions == (800, 600)
    
    @patch('time.time')
    def test_get_window_pixel_dimensions_caching(self, mock_time):
        """Test dimension caching behavior."""
        # First call
        mock_time.return_value = 100.0
        mock_window = Mock()
        mock_window.size = (1024, 768)
        self.mock_context.sdl_window = mock_window
        
        dimensions1 = self.window_manager.get_window_pixel_dimensions()
        
        # Second call within cache time
        mock_time.return_value = 100.05  # 0.05 seconds later
        mock_window.size = (1200, 800)  # Change size
        
        dimensions2 = self.window_manager.get_window_pixel_dimensions()
        
        # Should return cached value
        assert dimensions1 == dimensions2 == (1024, 768)
        
        # Third call after cache expires
        mock_time.return_value = 100.2  # 0.2 seconds later
        dimensions3 = self.window_manager.get_window_pixel_dimensions()
        
        # Should return new value
        assert dimensions3 == (1200, 800)
    
    def test_calculate_background_rect_basic(self):
        """Test basic background rectangle calculation."""
        # Mock window dimensions
        self.window_manager._cached_dimensions = (1000, 600)
        self.window_manager._last_check_time = time.time()
        
        image_size = (400, 300)
        rect = self.window_manager.calculate_background_rect(image_size)
        
        x, y, width, height = rect
        
        # Should be positioned at left edge
        assert x == 0
        
        # Should be vertically centered
        assert y == (600 - height) // 2
        
        # Should fit within 60% of window width
        graphics_area_width = int(1000 * 0.6)  # 600
        assert width <= graphics_area_width
    
    def test_calculate_background_rect_scale_by_width(self):
        """Test background rect when image is limited by width."""
        self.window_manager._cached_dimensions = (1000, 1000)
        self.window_manager._last_check_time = time.time()
        
        # Wide image that will be limited by graphics area width (600px)
        image_size = (800, 400)
        rect = self.window_manager.calculate_background_rect(image_size)
        
        x, y, width, height = rect
        
        # Should scale to fit in 60% width area
        graphics_area_width = int(1000 * 0.6)  # 600
        expected_scale = graphics_area_width / 800  # 0.75
        expected_width = int(800 * expected_scale)  # 600
        expected_height = int(400 * expected_scale)  # 300
        
        assert width == expected_width
        assert height == expected_height
        assert x == 0
        assert y == (1000 - expected_height) // 2
    
    def test_calculate_background_rect_scale_by_height(self):
        """Test background rect when image is limited by height."""
        self.window_manager._cached_dimensions = (1000, 400)
        self.window_manager._last_check_time = time.time()
        
        # Tall image that will be limited by window height
        image_size = (200, 800)
        rect = self.window_manager.calculate_background_rect(image_size)
        
        x, y, width, height = rect
        
        # Should scale to fit window height
        expected_scale = 400 / 800  # 0.5
        expected_width = int(200 * expected_scale)  # 100
        expected_height = int(800 * expected_scale)  # 400
        
        assert width == expected_width
        assert height == expected_height
        assert x == 0
        assert y == 0  # Should be at top since it fills height


class TestInitializeGameSystems:
    """Test game systems initialization."""
    
    @patch('game_loop.MainMenu')
    @patch('game_loop.SettingsMenu')
    @patch('game_loop.HelpMenu')
    @patch('game_loop.LoreMenu')
    def test_initialize_game_systems_without_background(self, mock_lore, mock_help, 
                                                       mock_settings, mock_main):
        """Test system initialization without background."""
        mock_settings_obj = Mock()
        mock_background = None
        
        result = initialize_game_systems(mock_settings_obj, mock_background)
        
        # Verify all menu classes were instantiated
        mock_main.assert_called_once_with(background=None)
        mock_settings.assert_called_once_with(mock_settings_obj, None)
        mock_help.assert_called_once()
        mock_lore.assert_called_once()
        
        # Verify return structure
        assert 'main_menu' in result
        assert 'settings_menu' in result
        assert 'help_menu' in result
        assert 'lore_menu' in result
    
    @patch('game_loop.MainMenu')
    @patch('game_loop.SettingsMenu')
    @patch('game_loop.HelpMenu')
    @patch('game_loop.LoreMenu')
    def test_initialize_game_systems_with_background(self, mock_lore, mock_help, 
                                                    mock_settings, mock_main):
        """Test system initialization with background."""
        mock_settings_obj = Mock()
        mock_background = Mock()
        
        result = initialize_game_systems(mock_settings_obj, mock_background)
        
        # Verify background was passed to menus
        mock_main.assert_called_once_with(background=mock_background)
        mock_settings.assert_called_once_with(mock_settings_obj, mock_background)


class TestHandleErrorScreen:
    """Test error screen handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_console = Mock()
        self.mock_context = Mock()
    
    @patch('game_loop.render_char_safe')
    @patch('tcod.event.wait')
    def test_handle_error_screen_escape_key(self, mock_wait, mock_render):
        """Test error screen handling with ESC key."""
        # Mock ESC key event
        mock_event = Mock()
        mock_event.type = "KEYDOWN"
        mock_event.sym = tcod.event.KeySym.ESCAPE
        mock_wait.return_value = [mock_event]
        
        result = handle_error_screen(self.mock_console, self.mock_context, 
                                   "Test error", 42)
        
        # Verify console was cleared and error displayed
        self.mock_console.clear.assert_called_once()
        # Check that render was called twice (error message and instruction)
        assert mock_render.call_count == 2
        self.mock_context.present.assert_called_once_with(self.mock_console)
        
        assert result is True
    
    @patch('game_loop.render_char_safe')
    @patch('tcod.event.wait')
    def test_handle_error_screen_quit_event(self, mock_wait, mock_render):
        """Test error screen handling with QUIT event."""
        mock_event = Mock()
        mock_event.type = "QUIT"
        mock_wait.return_value = [mock_event]
        
        result = handle_error_screen(self.mock_console, self.mock_context, 
                                   "Test error", 42)
        
        assert result is True
    
    @patch('game_loop.render_char_safe')
    @patch('tcod.event.wait')
    def test_handle_error_screen_other_key(self, mock_wait, mock_render):
        """Test error screen handling with other keys."""
        mock_event = Mock()
        mock_event.type = "KEYDOWN"
        mock_event.sym = tcod.event.KeySym.SPACE
        mock_wait.return_value = [mock_event]
        
        result = handle_error_screen(self.mock_console, self.mock_context, 
                                   "Test error", 42)
        
        assert result is False
    
    @patch('game_loop.render_char_safe')
    @patch('tcod.event.wait')
    def test_handle_error_screen_long_message(self, mock_wait, mock_render):
        """Test error screen with long error message."""
        mock_event = Mock()
        mock_event.type = "QUIT"
        mock_wait.return_value = [mock_event]
        
        long_message = "This is a very long error message that should be truncated"
        result = handle_error_screen(self.mock_console, self.mock_context, 
                                   long_message, 100)
        
        # Verify error message call (should be first call)
        error_call = mock_render.call_args_list[0]
        assert "Error:" in error_call[0][3]  # Check message contains "Error:"
        assert error_call[1]['fg'] == (255, 0, 0)  # Check red color
        assert result is True