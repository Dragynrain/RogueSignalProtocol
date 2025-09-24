#!/usr/bin/env python3
"""
Unit tests for Message Log and UI functionality.
Tests message formatting, log capacity, color coding, and UI rendering integration.
"""

import pytest
from unittest.mock import patch, MagicMock
import tcod

from game_state import MessageLog
from game_ui import render_char_safe, WindowManager, UniversalInputHandler
from game_entities import Colors
from data_loading import DataLoader


class TestMessageLog:
    """Test the MessageLog class functionality."""
    
    def test_message_log_initialization(self):
        """Test MessageLog initializes with correct defaults."""
        log = MessageLog()
        assert log.messages == []
        assert log.max_messages == 100
        
        custom_log = MessageLog(max_messages=50)
        assert custom_log.max_messages == 50
    
    def test_add_basic_message(self):
        """Test adding a basic message without color."""
        log = MessageLog()
        log.add_message("Test message")
        
        assert len(log.messages) == 1
        assert log.messages[0][0] == "Test message"
        assert isinstance(log.messages[0][1], tuple)
        assert len(log.messages[0][1]) == 3  # RGB tuple
    
    def test_add_message_with_color(self):
        """Test adding a message with explicit color."""
        log = MessageLog()
        red_color = (255, 0, 0)
        log.add_message("Red message", color=red_color)
        
        assert len(log.messages) == 1
        assert log.messages[0][0] == "Red message"
        assert log.messages[0][1] == red_color
    
    def test_add_message_with_type(self):
        """Test adding a message with message type."""
        log = MessageLog()
        with patch.object(DataLoader, 'load_config') as mock_config:
            mock_config.return_value = {
                "colors": {
                    "message_log": {
                        "error": [255, 0, 0],
                        "default": [144, 238, 144]
                    }
                }
            }
            
            log.add_message("Error occurred", msg_type="error")
            
            assert len(log.messages) == 1
            assert log.messages[0][0] == "Error occurred"
            assert log.messages[0][1] == (255, 0, 0)
    
    def test_add_message_typed_helper(self):
        """Test the add_message_typed convenience method."""
        log = MessageLog()
        with patch.object(log, '_get_color_by_type', return_value=(0, 255, 0)) as mock_color:
            log.add_message_typed("Success message", "success")
            
            assert len(log.messages) == 1
            assert log.messages[0][0] == "Success message"
            mock_color.assert_called_once_with("success")
    
    def test_empty_message_ignored(self):
        """Test that empty messages are ignored."""
        log = MessageLog()
        log.add_message("")
        log.add_message(None)
        
        assert len(log.messages) == 0
    
    def test_log_capacity_overflow(self):
        """Test log capacity management when messages exceed max."""
        log = MessageLog(max_messages=3)
        
        # Add more messages than capacity
        for i in range(5):
            log.add_message(f"Message {i}")
        
        # Should only keep the last 3 messages
        assert len(log.messages) == 3
        assert log.messages[0][0] == "Message 2"
        assert log.messages[1][0] == "Message 3" 
        assert log.messages[2][0] == "Message 4"
    
    def test_get_recent_messages(self):
        """Test retrieving recent messages."""
        log = MessageLog()
        for i in range(5):
            log.add_message(f"Message {i}")
        
        # Get last 3 messages
        recent = log.get_recent_messages(3)
        assert len(recent) == 3
        assert recent[0][0] == "Message 2"
        assert recent[2][0] == "Message 4"
        
        # Request more than available
        all_messages = log.get_recent_messages(10)
        assert len(all_messages) == 5
        assert all_messages[0][0] == "Message 0"
    
    def test_color_determination_by_content(self):
        """Test automatic color determination based on message content."""
        log = MessageLog()
        with patch.object(DataLoader, 'load_config') as mock_config:
            mock_config.return_value = {
                "message_types": {
                    "patterns": {
                        "error": ["error", "failed", "critical"],
                        "success": ["success", "completed", "restored"]
                    }
                },
                "colors": {
                    "message_log": {
                        "error": [255, 0, 0],
                        "success": [0, 255, 0],
                        "default": [144, 238, 144]
                    }
                }
            }
            
            # Test error pattern matching
            log.add_message("Critical system failure")
            assert log.messages[0][1] == (255, 0, 0)
            
            # Test success pattern matching
            log.add_message("CPU restored successfully")
            assert log.messages[1][1] == (0, 255, 0)
            
            # Test default for unmatched content
            log.add_message("Random message")
            assert log.messages[2][1] == (144, 238, 144)
    
    def test_get_color_by_type(self):
        """Test getting color by explicit message type."""
        log = MessageLog()
        with patch.object(DataLoader, 'load_config') as mock_config:
            mock_config.return_value = {
                "colors": {
                    "message_log": {
                        "warning": [255, 255, 0],
                        "default": [144, 238, 144]
                    }
                }
            }
            
            # Test known type
            color = log._get_color_by_type("warning")
            assert color == (255, 255, 0)
            
            # Test unknown type falls back to default
            color = log._get_color_by_type("unknown")
            assert color == (144, 238, 144)


class TestRenderCharSafe:
    """Test the render_char_safe function for UI rendering."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_console = MagicMock()
    
    def test_render_basic_character(self):
        """Test rendering a basic character with no colors."""
        render_char_safe(self.mock_console, 5, 10, '@')
        self.mock_console.print.assert_called_once_with(5, 10, '@')
    
    def test_render_with_foreground_color(self):
        """Test rendering with foreground color."""
        color = (255, 0, 0)
        render_char_safe(self.mock_console, 5, 10, '@', fg=color)
        self.mock_console.print.assert_called_once_with(5, 10, '@', fg=color)
    
    def test_render_with_both_colors(self):
        """Test rendering with both foreground and background colors."""
        fg_color = (255, 0, 0)
        bg_color = (0, 0, 255)
        render_char_safe(self.mock_console, 5, 10, '@', fg=fg_color, bg=bg_color)
        self.mock_console.print.assert_called_once_with(5, 10, '@', fg=fg_color, bg=bg_color)
    
    def test_invalid_string_color_logs_error_and_uses_fallback(self):
        """Test that string colors log errors and use fallback rendering."""
        # String colors should not raise exception but should use fallback rendering
        render_char_safe(self.mock_console, 5, 10, '@', fg="red")
        
        # Should have attempted fallback rendering
        self.mock_console.print.assert_called_once_with(5, 10, '@', fg=Colors.WHITE, bg=Colors.BLACK)
    
    def test_invalid_color_format_uses_fallback(self):
        """Test that invalid color formats use white fallback."""
        # Test with invalid color format
        render_char_safe(self.mock_console, 5, 10, '@', fg=123)
        self.mock_console.print.assert_called_once_with(5, 10, '@', fg=Colors.WHITE)
    
    def test_color_values_out_of_range_uses_fallback(self):
        """Test that out-of-range color values use fallback."""
        bad_color = (300, -50, 256)  # Out of 0-255 range
        render_char_safe(self.mock_console, 5, 10, '@', fg=bad_color)
        self.mock_console.print.assert_called_once_with(5, 10, '@', fg=Colors.WHITE)
    
    def test_console_error_uses_fallback(self):
        """Test that console errors use fallback rendering."""
        self.mock_console.print.side_effect = Exception("TCOD Error")
        
        # Should not raise exception and should try fallback
        render_char_safe(self.mock_console, 5, 10, '@', fg=(255, 0, 0))
        
        # Should have attempted both original and fallback calls
        assert self.mock_console.print.call_count == 2
        # Last call should be fallback
        final_call = self.mock_console.print.call_args_list[-1]
        assert final_call[0] == (5, 10, '@')
        assert final_call[1] == {'fg': Colors.WHITE, 'bg': Colors.BLACK}


class TestWindowManager:
    """Test the WindowManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_window = MagicMock()
        self.mock_context.sdl_window = self.mock_window
        self.window_manager = WindowManager(self.mock_context)
    
    def test_window_dimensions_caching(self):
        """Test that window dimensions are cached properly."""
        self.mock_window.size = (1920, 1080)
        
        # First call should query SDL
        dims1 = self.window_manager.get_window_pixel_dimensions()
        assert dims1 == (1920, 1080)
        
        # Second immediate call should use cache
        dims2 = self.window_manager.get_window_pixel_dimensions()
        assert dims2 == (1920, 1080)
        
        # Should only have accessed window.size once due to caching
        assert self.mock_window.size == (1920, 1080)  # Verify it was accessed
    
    def test_window_dimensions_fallback(self):
        """Test fallback when SDL window is not available."""
        self.mock_context.sdl_window = None
        
        dims = self.window_manager.get_window_pixel_dimensions()
        assert dims == (800, 600)  # Fallback dimensions
    
    def test_background_rect_calculation(self):
        """Test background image rectangle calculation."""
        self.mock_window.size = (1200, 800)
        
        # Test image that fits within left 60% area
        image_size = (400, 300)
        rect = self.window_manager.calculate_background_rect(image_size)
        
        # Should be positioned at left side
        x, y, width, height = rect
        assert x == 0  # Left-aligned
        assert width <= 720  # Within 60% of 1200px width
        assert height <= 800  # Within window height
        
        # Y should center vertically
        assert y == (800 - height) // 2


class TestUniversalInputHandler:
    """Test the UniversalInputHandler utility class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_screen = MagicMock()
        self.mock_screen.selected_option = 0
        self.mock_event = MagicMock()
    
    def test_list_navigation_up(self):
        """Test upward navigation in lists."""
        self.mock_event.sym = tcod.event.KeySym.UP
        
        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count=3, wrap_around=True
        )
        
        assert result is True
        assert self.mock_screen.selected_option == 2  # Wrapped from 0 to 2
    
    def test_list_navigation_down(self):
        """Test downward navigation in lists."""
        self.mock_event.sym = tcod.event.KeySym.DOWN
        
        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count=3, wrap_around=True
        )
        
        assert result is True
        assert self.mock_screen.selected_option == 1  # Moved from 0 to 1
    
    def test_list_navigation_no_wrap(self):
        """Test navigation without wrap-around."""
        self.mock_screen.selected_option = 0
        self.mock_event.sym = tcod.event.KeySym.UP
        
        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count=3, wrap_around=False
        )
        
        assert result is True
        assert self.mock_screen.selected_option == 0  # Stayed at 0 (clamped)
    
    def test_dialog_navigation_toggle(self):
        """Test dialog navigation toggles between options."""
        self.mock_screen.warning_selection = 0
        self.mock_event.sym = tcod.event.KeySym.UP
        
        result = UniversalInputHandler.handle_dialog_navigation(
            self.mock_screen, self.mock_event, option_count=2
        )
        
        assert result is True
        assert self.mock_screen.warning_selection == 1  # Toggled from 0 to 1
    
    def test_value_adjustment_left_right(self):
        """Test value adjustment with left/right keys."""
        adjustment_values = []
        def adjust_callback(direction):
            adjustment_values.append(direction)
        
        # Test left adjustment
        self.mock_event.sym = tcod.event.KeySym.LEFT
        result = UniversalInputHandler.handle_value_adjustment(
            self.mock_screen, self.mock_event, adjust_callback
        )
        
        assert result is True
        assert adjustment_values == [-1]
        
        # Test right adjustment
        self.mock_event.sym = tcod.event.KeySym.RIGHT
        result = UniversalInputHandler.handle_value_adjustment(
            self.mock_screen, self.mock_event, adjust_callback
        )
        
        assert result is True
        assert adjustment_values == [-1, 1]
    
    def test_confirm_key_detection(self):
        """Test confirm key detection."""
        self.mock_event.sym = tcod.event.KeySym.RETURN
        assert UniversalInputHandler.is_confirm_key(self.mock_event) is True
        
        self.mock_event.sym = tcod.event.KeySym.KP_ENTER
        assert UniversalInputHandler.is_confirm_key(self.mock_event) is True
        
        self.mock_event.sym = tcod.event.KeySym.SPACE
        assert UniversalInputHandler.is_confirm_key(self.mock_event) is False
    
    def test_escape_key_detection(self):
        """Test escape key detection."""
        self.mock_event.sym = tcod.event.KeySym.ESCAPE
        assert UniversalInputHandler.is_escape_key(self.mock_event) is True
        
        self.mock_event.sym = tcod.event.KeySym.RETURN
        assert UniversalInputHandler.is_escape_key(self.mock_event) is False
    
    def test_any_key_screen_handler(self):
        """Test any key screen handler always returns True."""
        result = UniversalInputHandler.handle_any_key_screen(self.mock_event)
        assert result is True


class TestMessageLogIntegration:
    """Test integration between MessageLog and UI systems."""
    
    def test_message_color_consistency(self):
        """Test that message colors are consistent with UI expectations."""
        log = MessageLog()
        with patch.object(DataLoader, 'load_config') as mock_config:
            mock_config.return_value = {
                "message_types": {
                    "patterns": {
                        "error": ["error", "failure"],
                        "success": ["success", "complete"]
                    }
                },
                "colors": {
                    "message_log": {
                        "error": [255, 0, 0],
                        "success": [0, 255, 0],
                        "default": [144, 238, 144]
                    }
                }
            }
            
            log.add_message("System error detected")
            log.add_message("Operation completed successfully")
            
            # Colors should be valid RGB tuples that render_char_safe can use
            for message, color in log.messages:
                assert isinstance(color, tuple)
                assert len(color) == 3
                assert all(0 <= c <= 255 for c in color)
    
    def test_message_log_ui_rendering_compatibility(self):
        """Test that MessageLog output is compatible with UI rendering."""
        log = MessageLog()
        mock_console = MagicMock()
        
        # Add various message types
        log.add_message("Normal message")
        log.add_message("Warning message", color=(255, 255, 0))
        
        # Test that all messages can be rendered without errors
        for i, (text, color) in enumerate(log.get_recent_messages(10)):
            # This should not raise any exceptions
            render_char_safe(mock_console, 0, i, text[0] if text else ' ', fg=color)
            
        # Verify render_char_safe was called for each message
        assert mock_console.print.call_count == len(log.messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])