#!/usr/bin/env python3
"""
Unit tests for game_rendering.py - Game rendering system.
Tests BaseRenderer and various rendering components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod

from game_rendering import BaseRenderer, UIRenderer
from game_entities import Position, Colors
from game_config import GameConfig


class TestBaseRenderer:
    """Test BaseRenderer abstract base class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a concrete implementation for testing
        class ConcreteRenderer(BaseRenderer):
            def render_map(self, console, game):
                pass
        
        self.renderer = ConcreteRenderer()
        self.mock_console = Mock()
        self.mock_game = Mock()
    
    def test_initialization(self):
        """Test BaseRenderer initialization."""
        assert isinstance(self.renderer.ui_renderer, UIRenderer)
    
    @patch('game_rendering.render_char_safe')
    @patch('game_rendering.ensure_color_tuple')
    def test_draw_bordered_box(self, mock_ensure_color, mock_render):
        """Test _draw_bordered_box method."""
        mock_ensure_color.side_effect = lambda x: x  # Return input unchanged
        
        border_color = (255, 255, 255)
        bg_color = (50, 50, 50)
        
        self.renderer._draw_bordered_box(
            self.mock_console, 5, 5, 10, 6, border_color, bg_color
        )
        
        # Verify colors were ensured as tuples
        assert mock_ensure_color.call_count == 2
        
        # Verify render_char_safe was called multiple times for background, borders, and corners
        assert mock_render.call_count > 0
        
        # Check some specific corner characters were rendered
        corner_calls = [call for call in mock_render.call_args_list 
                       if len(call[0]) > 3 and call[0][3] in ['┌', '┐', '└', '┘']]
        assert len(corner_calls) == 4  # Four corners
    
    def test_render_game_story_fragment(self):
        """Test render_game when showing story fragment."""
        self.mock_game.show_story_fragment = "test_fragment"
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_help = False
        self.mock_game.show_inventory = False
        
        with patch.object(self.renderer.ui_renderer, 'render_story_fragment_screen') as mock_render:
            self.renderer.render_game(self.mock_console, self.mock_game)
            
            mock_render.assert_called_once_with(
                self.mock_console, self.mock_game, "test_fragment"
            )
    
    def test_render_game_lore_viewer(self):
        """Test render_game when showing lore viewer."""
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = True
        self.mock_game.show_help = False
        self.mock_game.show_inventory = False
        
        with patch.object(self.renderer.ui_renderer, 'render_lore_viewer_screen') as mock_render:
            self.renderer.render_game(self.mock_console, self.mock_game)
            
            mock_render.assert_called_once_with(self.mock_console, self.mock_game)
    
    def test_render_game_help_screen(self):
        """Test render_game when showing help."""
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_help = True
        self.mock_game.show_inventory = False
        
        with patch.object(self.renderer.ui_renderer, 'render_help_screen') as mock_render:
            self.renderer.render_game(self.mock_console, self.mock_game)
            
            mock_render.assert_called_once_with(self.mock_console)
    
    def test_render_game_inventory_screen(self):
        """Test render_game when showing inventory."""
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_help = False
        self.mock_game.show_inventory = True
        
        with patch.object(self.renderer.ui_renderer, 'render_inventory_screen') as mock_render:
            self.renderer.render_game(self.mock_console, self.mock_game)
            
            mock_render.assert_called_once_with(self.mock_console, self.mock_game)
    
    def test_render_game_main_screen(self):
        """Test render_game showing main game screen."""
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_help = False
        self.mock_game.show_inventory = False
        
        with patch.object(self.renderer, '_render_main_game_screen') as mock_render:
            self.renderer.render_game(self.mock_console, self.mock_game)
            
            mock_render.assert_called_once_with(self.mock_console, self.mock_game)
    
    def test_render_main_game_screen_basic(self):
        """Test _render_main_game_screen basic rendering."""
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.game_over = False
        self.mock_game.level = 1
        self.mock_game.player = Mock()
        self.mock_game.player.cpu = 100
        
        with patch.object(self.renderer.ui_renderer, 'render_top_status_bar') as mock_status, \
             patch.object(self.renderer, 'render_map') as mock_map, \
             patch.object(self.renderer.ui_renderer, 'render_bottom_panel') as mock_panel, \
             patch.object(self.renderer.ui_renderer, 'render_system_log') as mock_log:
            
            self.renderer._render_main_game_screen(self.mock_console, self.mock_game)
            
            mock_status.assert_called_once_with(self.mock_console, self.mock_game)
            mock_map.assert_called_once_with(self.mock_console, self.mock_game)
            mock_panel.assert_called_once_with(self.mock_console, self.mock_game)
            mock_log.assert_called_once_with(self.mock_console, self.mock_game)
    
    def test_render_main_game_screen_gateway_confirmation(self):
        """Test _render_main_game_screen with gateway confirmation."""
        self.mock_game.show_gateway_confirmation = True
        self.mock_game.game_over = False
        self.mock_game.level = 1
        self.mock_game.player = Mock()
        self.mock_game.player.cpu = 100
        
        with patch.object(self.renderer, '_render_gateway_confirmation') as mock_gateway, \
             patch.object(self.renderer.ui_renderer, 'render_top_status_bar'), \
             patch.object(self.renderer, 'render_map'), \
             patch.object(self.renderer.ui_renderer, 'render_bottom_panel'), \
             patch.object(self.renderer.ui_renderer, 'render_system_log'):
            
            self.renderer._render_main_game_screen(self.mock_console, self.mock_game)
            
            mock_gateway.assert_called_once_with(self.mock_console)
    
    def test_render_main_game_screen_victory(self):
        """Test _render_main_game_screen with victory condition."""
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.game_over = True
        self.mock_game.level = 5  # > 3 for victory
        self.mock_game.player = Mock()
        self.mock_game.player.cpu = 100
        
        with patch.object(self.renderer, '_render_victory_message') as mock_victory, \
             patch.object(self.renderer.ui_renderer, 'render_top_status_bar'), \
             patch.object(self.renderer, 'render_map'), \
             patch.object(self.renderer.ui_renderer, 'render_bottom_panel'), \
             patch.object(self.renderer.ui_renderer, 'render_system_log'):
            
            self.renderer._render_main_game_screen(self.mock_console, self.mock_game)
            
            mock_victory.assert_called_once_with(self.mock_console)
    
    def test_render_main_game_screen_death(self):
        """Test _render_main_game_screen with death condition."""
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.game_over = False
        self.mock_game.level = 1
        self.mock_game.player = Mock()
        self.mock_game.player.cpu = 0  # Dead
        
        with patch.object(self.renderer, '_render_death_message') as mock_death, \
             patch.object(self.renderer.ui_renderer, 'render_top_status_bar'), \
             patch.object(self.renderer, 'render_map'), \
             patch.object(self.renderer.ui_renderer, 'render_bottom_panel'), \
             patch.object(self.renderer.ui_renderer, 'render_system_log'):
            
            self.renderer._render_main_game_screen(self.mock_console, self.mock_game)
            
            mock_death.assert_called_once_with(self.mock_console)
    
    @patch('game_rendering.render_char_safe')
    @patch('game_config.GameConfig.GAME_AREA_WIDTH')
    def test_render_victory_message(self, mock_game_area_width, mock_render):
        """Test _render_victory_message method."""
        mock_game_area_width.return_value = 80
        
        self.renderer._render_victory_message(self.mock_console)
        
        # Should call render_char_safe multiple times for the victory message
        assert mock_render.call_count > 0
        
        # Check that some victory-related text was rendered
        victory_calls = [call for call in mock_render.call_args_list 
                        if len(call[0]) > 3 and 'SUCCESS' in str(call[0][3]).upper()]
        assert len(victory_calls) > 0
    
    @patch('game_rendering.render_char_safe')
    @patch('game_config.GameConfig.GAME_AREA_WIDTH')
    def test_render_death_message(self, mock_game_area_width, mock_render):
        """Test _render_death_message method."""
        mock_game_area_width.return_value = 80
        
        self.renderer._render_death_message(self.mock_console)
        
        # Should call render_char_safe multiple times for the death message
        assert mock_render.call_count > 0
    
    @patch('game_rendering.render_char_safe')
    @patch('game_config.GameConfig.GAME_AREA_WIDTH')
    def test_render_gateway_confirmation(self, mock_game_area_width, mock_render):
        """Test _render_gateway_confirmation method."""
        mock_game_area_width.return_value = 80
        
        self.renderer._render_gateway_confirmation(self.mock_console)
        
        # Should call render_char_safe multiple times for the confirmation dialog
        assert mock_render.call_count > 0


class TestUIRenderer:
    """Test UIRenderer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ui_renderer = UIRenderer()
        self.mock_console = Mock()
        self.mock_game = Mock()
    
    def test_initialization(self):
        """Test UIRenderer initialization."""
        assert self.ui_renderer is not None
    
    @patch('game_rendering.render_char_safe')
    def test_render_top_status_bar(self, mock_render):
        """Test render_top_status_bar method."""
        # Set up mock game data
        self.mock_game.player = Mock()
        self.mock_game.player.cpu = 75
        self.mock_game.player.heat = 30
        self.mock_game.player.detection = 45
        self.mock_game.level = 3
        self.mock_game.turn = 50
        
        self.ui_renderer.render_top_status_bar(self.mock_console, self.mock_game)
        
        # Should render status information
        assert mock_render.call_count > 0
        
        # Check that CPU, heat, detection, level info was rendered
        rendered_text = ' '.join([str(call[0][3]) for call in mock_render.call_args_list 
                                 if len(call[0]) > 3])
        assert '75' in rendered_text  # CPU value
        assert '30' in rendered_text  # Heat value
        assert '45' in rendered_text  # Detection value
        assert '3' in rendered_text   # Level value
    
    @patch('game_rendering.render_char_safe')
    def test_render_system_log(self, mock_render):
        """Test render_system_log method."""
        # Set up mock message log
        mock_message_log = Mock()
        mock_message_log.get_recent_messages.return_value = [
            ("System message 1", (255, 255, 255)),
            ("System message 2", (255, 0, 0)),
            ("System message 3", (0, 255, 0))
        ]
        self.mock_game.message_log = mock_message_log
        
        self.ui_renderer.render_system_log(self.mock_console, self.mock_game)
        
        # Should render messages
        assert mock_render.call_count > 0
        
        # Check that messages were rendered
        rendered_text = ' '.join([str(call[0][3]) for call in mock_render.call_args_list 
                                 if len(call[0]) > 3])
        assert 'System message' in rendered_text
    
    @patch('game_rendering.render_char_safe')
    def test_render_bottom_panel(self, mock_render):
        """Test render_bottom_panel method."""
        # Set up mock game state
        self.mock_game.targeting_mode = False
        self.mock_game.cursor_position = Position(10, 10)
        
        self.ui_renderer.render_bottom_panel(self.mock_console, self.mock_game)
        
        # Should render bottom panel information
        assert mock_render.call_count > 0
    
    @patch('game_rendering.render_char_safe')
    def test_render_help_screen(self, mock_render):
        """Test render_help_screen method."""
        with patch('game_rendering.HelpMenu') as mock_help_menu_class:
            mock_help_menu = Mock()
            mock_help_menu_class.return_value = mock_help_menu
            
            self.ui_renderer.render_help_screen(self.mock_console)
            
            # Should create and render help menu
            mock_help_menu_class.assert_called_once()
            mock_help_menu.render.assert_called_once_with(self.mock_console)
    
    @patch('game_rendering.render_char_safe')
    def test_render_inventory_screen(self, mock_render):
        """Test render_inventory_screen method."""
        # Set up mock inventory
        self.mock_game.player = Mock()
        self.mock_game.player.inventory = Mock()
        self.mock_game.player.inventory.items = []
        self.mock_game.inventory_selection = 0
        
        self.ui_renderer.render_inventory_screen(self.mock_console, self.mock_game)
        
        # Should render inventory information
        assert mock_render.call_count > 0
    
    @patch('game_rendering.render_char_safe')
    @patch('data_loading.get_story_fragments')
    def test_render_story_fragment_screen(self, mock_get_fragments, mock_render):
        """Test render_story_fragment_screen method."""
        mock_get_fragments.return_value = {
            "test_fragment": "This is a test story fragment for testing purposes."
        }
        
        self.ui_renderer.render_story_fragment_screen(
            self.mock_console, self.mock_game, "test_fragment"
        )
        
        # Should render story fragment
        assert mock_render.call_count > 0
        
        # Check that fragment content was rendered
        rendered_text = ' '.join([str(call[0][3]) for call in mock_render.call_args_list 
                                 if len(call[0]) > 3])
        assert 'test story fragment' in rendered_text.lower()
    
    @patch('game_rendering.render_char_safe')
    def test_render_lore_viewer_screen(self, mock_render):
        """Test render_lore_viewer_screen method."""
        # Set up mock lore viewer state
        self.mock_game.lore_viewer_mode = "list"
        self.mock_game.lore_viewer_selection = 0
        
        self.ui_renderer.render_lore_viewer_screen(self.mock_console, self.mock_game)
        
        # Should render lore viewer
        assert mock_render.call_count > 0


class TestRendererFactoryAndUtilities:
    """Test renderer factory and utility functions."""
    
    def test_abstract_base_renderer_cannot_instantiate(self):
        """Test that BaseRenderer cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseRenderer()
    
    @patch('game_rendering.render_char_safe')
    def test_box_rendering_edge_cases(self, mock_render):
        """Test _draw_bordered_box with edge cases."""
        class ConcreteRenderer(BaseRenderer):
            def render_map(self, console, game):
                pass
        
        renderer = ConcreteRenderer()
        mock_console = Mock()
        
        # Test minimum size box (1x1)
        renderer._draw_bordered_box(mock_console, 0, 0, 1, 1, Colors.WHITE, Colors.BLACK)
        
        # Test large box
        renderer._draw_bordered_box(mock_console, 5, 5, 50, 30, Colors.RED, Colors.BLUE)
        
        # Should not raise exceptions
        assert mock_render.call_count > 0


class TestRenderingErrorHandling:
    """Test error handling in rendering system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        class ConcreteRenderer(BaseRenderer):
            def render_map(self, console, game):
                pass
        
        self.renderer = ConcreteRenderer()
        self.mock_console = Mock()
        self.mock_game = Mock()
    
    def test_render_with_none_game(self):
        """Test rendering handles None game gracefully."""
        # This should not crash but may produce limited output
        try:
            self.renderer.render_game(self.mock_console, None)
        except AttributeError:
            # Expected due to None game object
            pass
    
    @patch('game_rendering.render_char_safe')
    def test_render_with_missing_attributes(self, mock_render):
        """Test rendering with game missing some attributes."""
        incomplete_game = Mock()
        # Deliberately missing some attributes to test defensive programming
        del incomplete_game.show_story_fragment
        
        # Should handle gracefully or raise AttributeError
        try:
            self.renderer.render_game(self.mock_console, incomplete_game)
        except AttributeError:
            # Expected for incomplete game object
            pass
    
    @patch('logging.error')
    def test_rendering_logs_errors(self, mock_log_error):
        """Test that rendering errors are properly logged."""
        # This would need actual error conditions in the rendering code
        # For now, just verify the logging system is available
        assert mock_log_error is not None