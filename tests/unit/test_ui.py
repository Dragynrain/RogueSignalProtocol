#!/usr/bin/env python3
"""
Unit tests for game_ui.py - UI rendering utilities and window management.
Tests UI helper functions, window management, and input handling utilities.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import time
import tcod.event

# Import game modules
from game_ui import render_char_safe, WindowManager, UniversalInputHandler
from game_entities import Colors


class TestRenderCharSafe(unittest.TestCase):
    """Test render_char_safe function for safe console rendering."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_console = Mock()

    def test_render_char_safe_with_valid_colors(self):
        """Test render_char_safe with valid RGB tuple colors."""
        fg_color = (255, 255, 255)
        bg_color = (0, 0, 0)

        render_char_safe(self.mock_console, 10, 5, '@', fg_color, bg_color)

        # Should call console.print with validated colors as keyword args
        self.mock_console.print.assert_called_once_with(10, 5, '@', fg=fg_color, bg=bg_color)

    def test_render_char_safe_with_none_colors(self):
        """Test render_char_safe with None colors (should pass through)."""
        render_char_safe(self.mock_console, 10, 5, '@', None, None)

        # Should call console.print without color args when both are None
        self.mock_console.print.assert_called_once_with(10, 5, '@')

    def test_render_char_safe_with_string_colors_logs_error(self):
        """Test render_char_safe logs error for string colors."""
        with patch('game_ui.logging') as mock_logging:
            # This should trigger error logging but still render
            render_char_safe(self.mock_console, 10, 5, '@', "white", (0, 0, 0))

            # Should log error about invalid color
            mock_logging.error.assert_called()
            # Should still attempt to render
            self.mock_console.print.assert_called()

    def test_render_char_safe_with_invalid_tuple_colors(self):
        """Test render_char_safe with invalid tuple colors."""
        invalid_color = (300, -10, "blue")  # Invalid RGB values

        with patch('game_ui.logging') as mock_logging:
            render_char_safe(self.mock_console, 10, 5, '@', invalid_color, None)

            # Should log error and attempt fallback
            mock_logging.error.assert_called()
            self.mock_console.print.assert_called()

    def test_render_char_safe_error_handling(self):
        """Test render_char_safe handles console print errors gracefully."""
        self.mock_console.print.side_effect = Exception("Console error")

        with patch('game_ui.logging') as mock_logging:
            # Should not raise exception
            render_char_safe(self.mock_console, 10, 5, '@', (255, 255, 255), None)

            # Should log the error
            mock_logging.error.assert_called()

    def test_render_char_safe_with_colors_object(self):
        """Test render_char_safe with Colors class attributes."""
        # Test with actual Colors class values
        fg_color = Colors.WHITE
        bg_color = Colors.BLACK

        render_char_safe(self.mock_console, 10, 5, '@', fg_color, bg_color)

        # Should call console.print with the color values as keyword args
        self.mock_console.print.assert_called_once_with(10, 5, '@', fg=fg_color, bg=bg_color)


class TestWindowManager(unittest.TestCase):
    """Test WindowManager class for window dimension management."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_context = Mock()
        self.mock_window = Mock()
        self.mock_context.sdl_window = self.mock_window

    def test_window_manager_initialization(self):
        """Test WindowManager initializes correctly."""
        manager = WindowManager(self.mock_context)

        self.assertEqual(manager.context, self.mock_context)
        self.assertIsNone(manager._cached_dimensions)
        self.assertEqual(manager._last_check_time, 0)

    def test_get_window_pixel_dimensions_first_call(self):
        """Test first call to get_window_pixel_dimensions gets actual dimensions."""
        self.mock_window.size = (1024, 768)
        manager = WindowManager(self.mock_context)

        dimensions = manager.get_window_pixel_dimensions()

        self.assertEqual(dimensions, (1024, 768))
        self.assertEqual(manager._cached_dimensions, (1024, 768))
        self.assertGreater(manager._last_check_time, 0)

    def test_get_window_pixel_dimensions_caching(self):
        """Test dimensions are cached and not recalculated immediately."""
        self.mock_window.size = (1024, 768)
        manager = WindowManager(self.mock_context)

        # First call
        dimensions1 = manager.get_window_pixel_dimensions()

        # Change window size
        self.mock_window.size = (1280, 720)

        # Second call immediately should return cached value
        dimensions2 = manager.get_window_pixel_dimensions()

        self.assertEqual(dimensions1, (1024, 768))
        self.assertEqual(dimensions2, (1024, 768))  # Should be cached

    def test_get_window_pixel_dimensions_cache_expiry(self):
        """Test cache expires and gets fresh dimensions."""
        self.mock_window.size = (1024, 768)
        manager = WindowManager(self.mock_context)

        # First call
        dimensions1 = manager.get_window_pixel_dimensions()

        # Change window size and simulate time passing
        self.mock_window.size = (1280, 720)
        manager._last_check_time = time.time() - 0.2  # Simulate 0.2s ago

        # Should get fresh dimensions
        dimensions2 = manager.get_window_pixel_dimensions()

        self.assertEqual(dimensions1, (1024, 768))
        self.assertEqual(dimensions2, (1280, 720))

    def test_get_window_pixel_dimensions_no_window_fallback(self):
        """Test fallback when SDL window is not available."""
        self.mock_context.sdl_window = None
        manager = WindowManager(self.mock_context)

        dimensions = manager.get_window_pixel_dimensions()

        # Should return fallback dimensions
        self.assertEqual(dimensions, (800, 600))

    def test_calculate_background_rect_basic(self):
        """Test basic background rectangle calculation."""
        self.mock_window.size = (1000, 600)
        manager = WindowManager(self.mock_context)

        # Test with image that fits exactly in left 60%
        image_size = (600, 600)  # Square image
        rect = manager.calculate_background_rect(image_size)

        # Should scale to fit in left 60% (600px width)
        x, y, width, height = rect
        self.assertEqual(x, 0)  # Left-aligned
        self.assertEqual(width, 600)  # Scaled to fit width
        self.assertEqual(height, 600)  # Maintains aspect ratio
        self.assertEqual(y, 0)  # Centered vertically

    def test_calculate_background_rect_aspect_ratio_preservation(self):
        """Test background rect calculation preserves aspect ratio."""
        self.mock_window.size = (1200, 800)
        manager = WindowManager(self.mock_context)

        # Test with wide image
        image_size = (1000, 500)  # 2:1 aspect ratio
        rect = manager.calculate_background_rect(image_size)

        x, y, width, height = rect
        # Should scale to fit in left 60% (720px width available)
        self.assertEqual(width, 720)  # Scaled to fit available width
        self.assertEqual(height, 360)  # Maintains 2:1 aspect ratio
        self.assertEqual(x, 0)  # Left-aligned
        self.assertGreaterEqual(y, 0)  # Centered vertically

    def test_calculate_background_rect_tall_image(self):
        """Test background rect calculation with tall image."""
        self.mock_window.size = (1200, 600)
        manager = WindowManager(self.mock_context)

        # Test with tall image that's constrained by height
        image_size = (400, 800)  # 1:2 aspect ratio, taller than window
        rect = manager.calculate_background_rect(image_size)

        x, y, width, height = rect
        # Should be constrained by window height
        self.assertEqual(height, 600)  # Scaled to fit height
        self.assertEqual(width, 300)  # Maintains 1:2 aspect ratio
        self.assertEqual(x, 0)  # Left-aligned
        self.assertEqual(y, 0)  # Top-aligned when height-constrained


class TestUniversalInputHandler(unittest.TestCase):
    """Test UniversalInputHandler class for common input operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_screen = Mock()
        self.mock_screen.selected_option = 2
        self.mock_event = Mock()

    def test_navigation_up_with_wrap_around(self):
        """Test up navigation with wrap around enabled."""
        self.mock_event.sym = tcod.event.KeySym.UP
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=True
        )

        self.assertTrue(result)
        # Should wrap from 2 to 1
        self.assertEqual(self.mock_screen.selected_option, 1)

    def test_navigation_up_at_boundary_with_wrap(self):
        """Test up navigation at boundary with wrap around."""
        self.mock_screen.selected_option = 0
        self.mock_event.sym = tcod.event.KeySym.W  # Alternative up key
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=True
        )

        self.assertTrue(result)
        # Should wrap from 0 to 4 (last option)
        self.assertEqual(self.mock_screen.selected_option, 4)

    def test_navigation_up_without_wrap_around(self):
        """Test up navigation without wrap around."""
        self.mock_screen.selected_option = 0
        self.mock_event.sym = tcod.event.KeySym.UP
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=False
        )

        self.assertTrue(result)
        # Should stay at 0 (no wrap)
        self.assertEqual(self.mock_screen.selected_option, 0)

    def test_navigation_down_with_wrap_around(self):
        """Test down navigation with wrap around enabled."""
        self.mock_event.sym = tcod.event.KeySym.DOWN
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=True
        )

        self.assertTrue(result)
        # Should move from 2 to 3
        self.assertEqual(self.mock_screen.selected_option, 3)

    def test_navigation_down_at_boundary_with_wrap(self):
        """Test down navigation at boundary with wrap around."""
        self.mock_screen.selected_option = 4  # Last option
        self.mock_event.sym = tcod.event.KeySym.S  # Alternative down key
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=True
        )

        self.assertTrue(result)
        # Should wrap from 4 to 0 (first option)
        self.assertEqual(self.mock_screen.selected_option, 0)

    def test_navigation_down_without_wrap_around(self):
        """Test down navigation without wrap around."""
        self.mock_screen.selected_option = 4  # Last option
        self.mock_event.sym = tcod.event.KeySym.DOWN
        option_count = 5

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, option_count, wrap_around=False
        )

        self.assertTrue(result)
        # Should stay at 4 (no wrap)
        self.assertEqual(self.mock_screen.selected_option, 4)

    def test_navigation_with_callback(self):
        """Test navigation with callback function."""
        self.mock_event.sym = tcod.event.KeySym.UP
        mock_callback = Mock()

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, 5, callback=mock_callback
        )

        self.assertTrue(result)
        # Should call callback with -1 for up direction
        mock_callback.assert_called_once_with(-1)
        # Screen selection should not be modified when using callback
        self.assertEqual(self.mock_screen.selected_option, 2)  # Unchanged

    def test_navigation_unhandled_key(self):
        """Test navigation with unhandled key returns False."""
        self.mock_event.sym = tcod.event.KeySym.SPACE  # Not a navigation key

        result = UniversalInputHandler.handle_list_navigation(
            self.mock_screen, self.mock_event, 5
        )

        self.assertFalse(result)
        # Selection should be unchanged
        self.assertEqual(self.mock_screen.selected_option, 2)

    def test_dialog_navigation_basic(self):
        """Test basic dialog navigation (2 options)."""
        # Create a simple object instead of Mock to avoid arithmetic issues
        class SimpleScreen:
            def __init__(self):
                self.selected_option = 0

        screen = SimpleScreen()
        self.mock_event.sym = tcod.event.KeySym.DOWN

        result = UniversalInputHandler.handle_dialog_navigation(
            screen, self.mock_event
        )

        self.assertTrue(result)
        self.assertEqual(screen.selected_option, 1)

    def test_dialog_navigation_wrapping(self):
        """Test dialog navigation toggles between options."""
        # Create a simple object instead of Mock to avoid arithmetic issues
        class SimpleScreen:
            def __init__(self):
                self.selected_option = 1

        screen = SimpleScreen()
        self.mock_event.sym = tcod.event.KeySym.DOWN

        result = UniversalInputHandler.handle_dialog_navigation(
            screen, self.mock_event, option_count=2
        )

        self.assertTrue(result)
        self.assertEqual(screen.selected_option, 0)  # Should toggle to other option

    def test_key_classification_methods(self):
        """Test static methods for key classification."""
        # Test confirm keys
        confirm_event = Mock()
        confirm_event.sym = tcod.event.KeySym.RETURN
        self.assertTrue(UniversalInputHandler.is_confirm_key(confirm_event))

        enter_event = Mock()
        enter_event.sym = tcod.event.KeySym.KP_ENTER
        self.assertTrue(UniversalInputHandler.is_confirm_key(enter_event))

        # Test escape keys
        escape_event = Mock()
        escape_event.sym = tcod.event.KeySym.ESCAPE
        self.assertTrue(UniversalInputHandler.is_escape_key(escape_event))

        # Test non-matching keys
        other_event = Mock()
        other_event.sym = tcod.event.KeySym.SPACE
        self.assertFalse(UniversalInputHandler.is_confirm_key(other_event))
        self.assertFalse(UniversalInputHandler.is_escape_key(other_event))


class TestUIIntegration(unittest.TestCase):
    """Test integration between UI components."""

    def test_window_manager_and_input_handler_integration(self):
        """Test WindowManager and UniversalInputHandler work together."""
        mock_context = Mock()
        mock_window = Mock()
        mock_context.sdl_window = mock_window
        mock_window.size = (1920, 1080)

        manager = WindowManager(mock_context)
        dimensions = manager.get_window_pixel_dimensions()

        # Test that window dimensions are reasonable for UI calculations
        self.assertGreater(dimensions[0], 0)
        self.assertGreater(dimensions[1], 0)
        self.assertEqual(dimensions, (1920, 1080))

        # Test background rect calculation with these dimensions
        image_size = (800, 600)
        rect = manager.calculate_background_rect(image_size)
        x, y, width, height = rect

        # Should constrain to left 60% of screen
        max_width = int(1920 * 0.6)  # 1152px
        self.assertLessEqual(width, max_width)
        self.assertEqual(x, 0)  # Left-aligned

    def test_render_char_safe_with_window_coordinates(self):
        """Test render_char_safe with coordinates from window calculations."""
        mock_console = Mock()
        mock_context = Mock()
        mock_window = Mock()
        mock_context.sdl_window = mock_window
        mock_window.size = (800, 600)

        manager = WindowManager(mock_context)
        width, height = manager.get_window_pixel_dimensions()

        # Test rendering at various positions within window bounds
        test_positions = [
            (0, 0),  # Top-left
            (width // 2, height // 2),  # Center
            (width - 1, height - 1),  # Bottom-right (within bounds)
        ]

        for x, y in test_positions:
            # Should not raise exceptions for valid positions
            render_char_safe(mock_console, x, y, '@', (255, 255, 255), (0, 0, 0))
            mock_console.print.assert_called()

    def test_input_handler_navigation_bounds_checking(self):
        """Test input handler properly handles navigation bounds."""
        mock_screen = Mock()
        mock_screen.selected_option = 0

        # Test with various option counts
        for option_count in [1, 5, 10, 100]:
            # Reset selection
            mock_screen.selected_option = 0

            # Test up navigation at boundary
            up_event = Mock()
            up_event.sym = tcod.event.KeySym.UP
            UniversalInputHandler.handle_list_navigation(
                mock_screen, up_event, option_count, wrap_around=False
            )
            # Should not go below 0
            self.assertGreaterEqual(mock_screen.selected_option, 0)

            # Test down navigation at boundary
            mock_screen.selected_option = option_count - 1
            down_event = Mock()
            down_event.sym = tcod.event.KeySym.DOWN
            UniversalInputHandler.handle_list_navigation(
                mock_screen, down_event, option_count, wrap_around=False
            )
            # Should not exceed max
            self.assertLess(mock_screen.selected_option, option_count)


class TestUIErrorHandling(unittest.TestCase):
    """Test UI error handling and edge cases."""

    def test_window_manager_error_recovery(self):
        """Test WindowManager handles SDL errors gracefully."""
        mock_context = Mock()
        mock_context.sdl_window = None  # Simulate missing window

        manager = WindowManager(mock_context)
        dimensions = manager.get_window_pixel_dimensions()

        # Should return fallback dimensions
        self.assertEqual(dimensions, (800, 600))

    def test_render_char_safe_exception_handling(self):
        """Test render_char_safe handles console exceptions."""
        mock_console = Mock()
        mock_console.print.side_effect = Exception("Console rendering failed")

        with patch('game_ui.logging') as mock_logging:
            # Should not raise exception
            try:
                render_char_safe(mock_console, 10, 5, '@', (255, 255, 255), None)
            except Exception:
                self.fail("render_char_safe should handle console exceptions gracefully")

            # Should log the error
            mock_logging.error.assert_called()

    def test_input_handler_edge_cases(self):
        """Test UniversalInputHandler handles edge cases."""
        mock_screen = Mock()
        mock_screen.selected_option = 0

        # Test with one option (no navigation possible)
        mock_event = Mock()
        mock_event.sym = tcod.event.KeySym.DOWN

        result = UniversalInputHandler.handle_list_navigation(
            mock_screen, mock_event, 1, wrap_around=True
        )

        # Should handle gracefully - wrapping with 1 option keeps it at 0
        self.assertTrue(result)
        self.assertEqual(mock_screen.selected_option, 0)

        # Test without wrap around
        result = UniversalInputHandler.handle_list_navigation(
            mock_screen, mock_event, 1, wrap_around=False
        )

        # Should handle gracefully - clamping keeps it at 0
        self.assertTrue(result)
        self.assertEqual(mock_screen.selected_option, 0)


if __name__ == '__main__':
    unittest.main()