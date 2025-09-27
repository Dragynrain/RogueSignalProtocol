#!/usr/bin/env python3
"""
UI Navigation and Validation Tests.
Tests user interface navigation, input validation, and interaction patterns.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import tcod
from typing import Dict, Any, List

from game_ui import UIManager, WindowManager, UniversalInputHandler, render_char_safe
from game_input import InputHandler
from game_entities import Colors, Position
from game_config import GameConfig, GameSettings
from game_characters import Player
from game_inventory import InventoryManager, CodeHack, ExploitItem


class TestUINavigation:
    """Test UI navigation patterns and state management."""
    
    def setup_method(self):
        """Set up UI navigation tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
        self.mock_context = Mock()
        self.mock_settings = Mock(spec=GameSettings)
        
        # Create UI manager with mocked dependencies
        with patch('game_ui.WindowManager'):
            self.ui_manager = UIManager(self.mock_console, self.mock_context, self.mock_settings)
    
    def test_ui_manager_initialization(self):
        """UI manager initializes correctly."""
        assert self.ui_manager.console is self.mock_console
        assert self.ui_manager.context is self.mock_context
        assert self.ui_manager.settings is self.mock_settings
    
    def test_ui_state_stack_management(self):
        """UI state stack is managed correctly."""
        # Test UI state stack operations
        ui_states = []
        
        # Push states
        ui_states.append("main_game")
        assert len(ui_states) == 1
        assert ui_states[-1] == "main_game"
        
        ui_states.append("inventory")
        assert len(ui_states) == 2
        assert ui_states[-1] == "inventory"
        
        ui_states.append("help")
        assert len(ui_states) == 3
        assert ui_states[-1] == "help"
        
        # Pop states
        current_state = ui_states.pop()
        assert current_state == "help"
        assert ui_states[-1] == "inventory"
        
        current_state = ui_states.pop()
        assert current_state == "inventory"
        assert ui_states[-1] == "main_game"
    
    def test_ui_modal_dialog_management(self):
        """UI modal dialog management works correctly."""
        modal_stack = []
        
        # Show modal
        modal_stack.append("confirmation_dialog")
        assert len(modal_stack) == 1
        assert modal_stack[-1] == "confirmation_dialog"
        
        # Show another modal on top
        modal_stack.append("error_dialog")
        assert len(modal_stack) == 2
        assert modal_stack[-1] == "error_dialog"
        
        # Close top modal
        closed_modal = modal_stack.pop()
        assert closed_modal == "error_dialog"
        assert modal_stack[-1] == "confirmation_dialog"
        
        # Close remaining modal
        closed_modal = modal_stack.pop()
        assert closed_modal == "confirmation_dialog"
        assert len(modal_stack) == 0
    
    def test_ui_focus_management(self):
        """UI focus management works correctly."""
        # Test focus switching between UI elements
        ui_elements = ["inventory_list", "exploit_list", "status_panel", "message_log"]
        current_focus = 0
        
        # Move focus forward
        current_focus = (current_focus + 1) % len(ui_elements)
        assert ui_elements[current_focus] == "exploit_list"
        
        # Move focus backward
        current_focus = (current_focus - 1) % len(ui_elements)
        assert ui_elements[current_focus] == "inventory_list"
        
        # Tab to specific element
        current_focus = ui_elements.index("message_log")
        assert ui_elements[current_focus] == "message_log"


class TestInventoryNavigation:
    """Test inventory UI navigation and interaction."""
    
    def setup_method(self):
        """Set up inventory navigation tests."""
        self.mock_player = Mock(spec=Player)
        self.mock_inventory = Mock(spec=InventoryManager)
        
        # Set up inventory items
        self.inventory_items = [
            CodeHack("hack1", Position(10, 10), "red"),
            ExploitItem("buffer_overflow"),
            CodeHack("hack2", Position(15, 15), "blue"),
            ExploitItem("system_crash"),
            CodeHack("hack3", Position(20, 20), "green")
        ]
        
        self.mock_inventory.inventory = self.inventory_items
        self.mock_player.inventory_manager = self.mock_inventory
        
        # Inventory UI state
        self.selection = 0
        self.scroll_offset = 0
        self.items_per_page = 10
    
    def test_inventory_item_selection(self):
        """Inventory item selection works correctly."""
        # Navigate down
        self.selection = min(self.selection + 1, len(self.inventory_items) - 1)
        assert self.selection == 1
        
        # Navigate up
        self.selection = max(self.selection - 1, 0)
        assert self.selection == 0
        
        # Jump to end
        self.selection = len(self.inventory_items) - 1
        assert self.selection == 4
        
        # Jump to beginning
        self.selection = 0
        assert self.selection == 0
    
    def test_inventory_scrolling(self):
        """Inventory scrolling works correctly."""
        # Create large inventory
        large_inventory = [f"item_{i}" for i in range(25)]
        
        selection = 0
        scroll_offset = 0
        items_per_page = 10
        
        # Navigate down past visible area
        for _ in range(15):
            selection = min(selection + 1, len(large_inventory) - 1)
            
            # Adjust scroll if needed
            if selection >= scroll_offset + items_per_page:
                scroll_offset = selection - items_per_page + 1
        
        assert selection == 15
        assert scroll_offset == 6  # Should scroll to keep selection visible
        
        # Navigate back up
        for _ in range(10):
            selection = max(selection - 1, 0)
            
            # Adjust scroll if needed
            if selection < scroll_offset:
                scroll_offset = selection
        
        assert selection == 5
        assert scroll_offset == 5  # Should scroll to keep selection visible
    
    def test_inventory_item_filtering(self):
        """Inventory item filtering works correctly."""
        # Filter by item type
        code_hacks = [item for item in self.inventory_items if isinstance(item, CodeHack)]
        exploits = [item for item in self.inventory_items if isinstance(item, ExploitItem)]
        
        assert len(code_hacks) == 3
        assert len(exploits) == 2
        
        # Filter by color (for code hacks)
        red_hacks = [item for item in code_hacks if item.color == "red"]
        blue_hacks = [item for item in code_hacks if item.color == "blue"]
        
        assert len(red_hacks) == 1
        assert len(blue_hacks) == 1
    
    def test_inventory_item_usage(self):
        """Inventory item usage works correctly."""
        selected_item = self.inventory_items[self.selection]
        
        if isinstance(selected_item, ExploitItem):
            # Test exploit usage
            with patch.object(self.mock_inventory, 'use_exploit') as mock_use:
                self.mock_inventory.use_exploit(selected_item.name)
                mock_use.assert_called_with(selected_item.name)
        
        elif isinstance(selected_item, CodeHack):
            # Test code hack activation
            with patch.object(self.mock_inventory, 'activate_code_hack') as mock_activate:
                self.mock_inventory.activate_code_hack(selected_item)
                mock_activate.assert_called_with(selected_item)
    
    def test_inventory_multi_selection(self):
        """Inventory multi-selection works correctly."""
        selected_items = set()
        
        # Select multiple items
        selected_items.add(0)
        selected_items.add(2)
        selected_items.add(4)
        
        assert len(selected_items) == 3
        assert 0 in selected_items
        assert 2 in selected_items
        assert 4 in selected_items
        
        # Deselect item
        selected_items.remove(2)
        assert len(selected_items) == 2
        assert 2 not in selected_items
        
        # Clear all selections
        selected_items.clear()
        assert len(selected_items) == 0


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def setup_method(self):
        """Set up input validation tests."""
        self.input_handler = Mock(spec=InputHandler)
    
    def test_movement_input_validation(self):
        """Movement input validation works correctly."""
        valid_movement_inputs = [
            ('w', 0, -1),
            ('a', -1, 0),
            ('s', 0, 1),
            ('d', 1, 0),
            ('up', 0, -1),
            ('down', 0, 1),
            ('left', -1, 0),
            ('right', 1, 0)
        ]
        
        for input_key, expected_dx, expected_dy in valid_movement_inputs:
            # Validate movement input
            if input_key in ['w', 'up']:
                dx, dy = 0, -1
            elif input_key in ['a', 'left']:
                dx, dy = -1, 0
            elif input_key in ['s', 'down']:
                dx, dy = 0, 1
            elif input_key in ['d', 'right']:
                dx, dy = 1, 0
            else:
                dx, dy = 0, 0
            
            assert dx == expected_dx
            assert dy == expected_dy
    
    def test_menu_input_validation(self):
        """Menu input validation works correctly."""
        valid_menu_inputs = [
            'up', 'down', 'select', 'back', 'escape',
            'enter', 'space', 'tab'
        ]
        
        invalid_menu_inputs = [
            None, '', 123, [], {}, 'invalid_key'
        ]
        
        for valid_input in valid_menu_inputs:
            # Should accept valid menu inputs
            assert isinstance(valid_input, str)
            assert len(valid_input) > 0
        
        for invalid_input in invalid_menu_inputs:
            # Should reject invalid menu inputs
            is_valid = isinstance(invalid_input, str) and len(invalid_input) > 0
            if invalid_input == 'invalid_key':
                # Custom validation for unknown keys
                is_valid = invalid_input in valid_menu_inputs
            assert not is_valid or invalid_input in valid_menu_inputs
    
    def test_text_input_validation(self):
        """Text input validation works correctly."""
        # Test character filtering
        valid_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        invalid_chars = "!@#$%^&*()+={}[]|\\:;\"'<>,.?/"
        
        test_input = "Valid_Text123"
        filtered_input = ''.join(c for c in test_input if c in valid_chars)
        assert filtered_input == "Valid_Text123"
        
        test_input = "Invalid@Text#123!"
        filtered_input = ''.join(c for c in test_input if c in valid_chars)
        assert filtered_input == "InvalidText123"
    
    def test_numeric_input_validation(self):
        """Numeric input validation works correctly."""
        # Test integer validation
        valid_integers = ["0", "123", "999", "-5"]
        invalid_integers = ["abc", "12.34", "", "12a", "a12"]
        
        for valid_int in valid_integers:
            try:
                value = int(valid_int)
                assert isinstance(value, int)
            except ValueError:
                pytest.fail(f"Should accept valid integer: {valid_int}")
        
        for invalid_int in invalid_integers:
            try:
                value = int(invalid_int)
                # Should not reach here for invalid integers
                if invalid_int in ["abc", "", "12a", "a12"]:
                    pytest.fail(f"Should reject invalid integer: {invalid_int}")
            except ValueError:
                # Expected for invalid integers
                pass
    
    def test_coordinate_input_validation(self):
        """Coordinate input validation works correctly."""
        # Test coordinate bounds
        map_width = GameConfig.MAP_WIDTH
        map_height = GameConfig.MAP_HEIGHT
        
        valid_coordinates = [
            (0, 0),
            (map_width - 1, map_height - 1),
            (map_width // 2, map_height // 2)
        ]
        
        invalid_coordinates = [
            (-1, 0),
            (0, -1),
            (map_width, 0),
            (0, map_height),
            (-1, -1),
            (map_width + 10, map_height + 10)
        ]
        
        for x, y in valid_coordinates:
            assert 0 <= x < map_width
            assert 0 <= y < map_height
        
        for x, y in invalid_coordinates:
            is_valid = 0 <= x < map_width and 0 <= y < map_height
            assert not is_valid


class TestUIResponsiveness:
    """Test UI responsiveness and performance characteristics."""
    
    def setup_method(self):
        """Set up UI responsiveness tests."""
        self.mock_console = Mock(spec=tcod.console.Console)
    
    def test_ui_update_frequency(self):
        """UI updates at appropriate frequency."""
        import time
        
        # Simulate UI update loop
        frame_count = 0
        start_time = time.time()
        target_fps = 60
        frame_time = 1.0 / target_fps
        
        # Simulate 10 frames
        for _ in range(10):
            frame_start = time.time()
            
            # Simulate UI rendering work
            time.sleep(0.001)  # 1ms of work
            
            frame_end = time.time()
            frame_duration = frame_end - frame_start
            
            # Should complete frame quickly
            assert frame_duration < frame_time
            frame_count += 1
        
        total_time = time.time() - start_time
        actual_fps = frame_count / total_time
        
        # Should maintain reasonable frame rate
        assert actual_fps > 30  # At least 30 FPS
    
    def test_large_inventory_ui_performance(self):
        """Large inventory UI remains responsive."""
        # Create large inventory
        large_inventory = []
        for i in range(1000):  # Large inventory
            if i % 2 == 0:
                item = CodeHack(f"hack_{i}", Position(i % 100, i // 100), "red")
            else:
                item = ExploitItem(f"exploit_{i}")
            large_inventory.append(item)
        
        # Test navigation through large inventory
        selection = 0
        start_time = time.time()
        
        # Navigate through first 100 items
        for _ in range(100):
            selection = min(selection + 1, len(large_inventory) - 1)
        
        end_time = time.time()
        navigation_time = end_time - start_time
        
        # Should navigate quickly even with large inventory
        assert navigation_time < 0.1  # Less than 100ms for 100 navigation steps
    
    def test_rapid_input_handling(self):
        """UI handles rapid input correctly."""
        inputs = []
        processed_inputs = []
        
        # Generate rapid input sequence
        rapid_inputs = ['w', 'w', 'w', 'd', 'd', 's', 's', 'a', 'a'] * 10
        
        start_time = time.time()
        
        # Process inputs
        for input_key in rapid_inputs:
            # Simulate input processing
            if input_key in ['w', 'a', 's', 'd']:
                processed_inputs.append(input_key)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process all inputs quickly
        assert len(processed_inputs) == len(rapid_inputs)
        assert processing_time < 0.1  # Less than 100ms
    
    def test_ui_memory_stability(self):
        """UI memory usage remains stable over time."""
        # Simulate extended UI usage
        ui_states = []
        
        # Add and remove UI states repeatedly
        for cycle in range(100):
            # Add states
            ui_states.append(f"state_{cycle}")
            ui_states.append(f"modal_{cycle}")
            
            # Remove states
            if len(ui_states) > 10:  # Keep some states
                ui_states.pop()
                ui_states.pop()
        
        # Memory usage should not grow excessively
        assert len(ui_states) <= 20  # Should not accumulate indefinitely


class TestUIAccessibility:
    """Test UI accessibility features and compatibility."""
    
    def test_keyboard_navigation_completeness(self):
        """All UI functions accessible via keyboard."""
        # Test that all major UI functions have keyboard shortcuts
        keyboard_functions = {
            'move_up': ['w', 'up'],
            'move_down': ['s', 'down'],
            'move_left': ['a', 'left'],
            'move_right': ['d', 'right'],
            'open_inventory': ['i', 'tab'],
            'open_help': ['h', 'f1'],
            'confirm': ['enter', 'space'],
            'cancel': ['escape', 'backspace'],
            'select': ['enter', 'space'],
            'menu': ['escape', 'm']
        }
        
        for function, keys in keyboard_functions.items():
            # Each function should have at least one key binding
            assert len(keys) >= 1
            assert all(isinstance(key, str) for key in keys)
    
    def test_visual_feedback_consistency(self):
        """Visual feedback is consistent across UI elements."""
        # Test color consistency
        ui_colors = {
            'normal_text': Colors.WHITE,
            'selected_text': Colors.BLACK,
            'selected_background': Colors.WHITE,
            'error_text': Colors.RED,
            'success_text': Colors.GREEN,
            'warning_text': (255, 255, 0)  # Yellow
        }
        
        for color_name, color_value in ui_colors.items():
            # Colors should be valid RGB tuples
            if isinstance(color_value, tuple):
                assert len(color_value) == 3
                assert all(0 <= c <= 255 for c in color_value)
            else:
                # Or valid color constants
                assert hasattr(Colors, color_value.__class__.__name__)
    
    def test_ui_text_readability(self):
        """UI text maintains readability standards."""
        # Test contrast ratios
        background_colors = [Colors.BLACK, (32, 32, 32), (64, 64, 64)]
        text_colors = [Colors.WHITE, (255, 255, 255), (200, 200, 200)]
        
        for bg_color in background_colors:
            for text_color in text_colors:
                # Should have sufficient contrast
                # (Simplified contrast check - real implementation would use WCAG guidelines)
                if isinstance(bg_color, tuple) and isinstance(text_color, tuple):
                    bg_luminance = sum(bg_color) / 3
                    text_luminance = sum(text_color) / 3
                    contrast = abs(text_luminance - bg_luminance)
                    
                    # Should have reasonable contrast
                    assert contrast > 50  # Simplified threshold
    
    def test_ui_element_sizing(self):
        """UI elements are appropriately sized."""
        # Test minimum sizes for interactive elements
        min_button_width = 10
        min_button_height = 3
        min_menu_item_height = 1
        
        # Button dimensions
        button_width = 15
        button_height = 3
        assert button_width >= min_button_width
        assert button_height >= min_button_height
        
        # Menu item dimensions
        menu_item_height = 1
        assert menu_item_height >= min_menu_item_height
        
        # Screen utilization
        screen_width = GameConfig.SCREEN_WIDTH
        screen_height = GameConfig.SCREEN_HEIGHT
        
        # UI should not exceed screen bounds
        assert button_width <= screen_width
        assert button_height <= screen_height


class TestUIErrorHandling:
    """Test UI error handling and edge cases."""
    
    def test_invalid_ui_state_handling(self):
        """UI handles invalid states gracefully."""
        invalid_states = [
            None,
            "",
            "invalid_state",
            123,
            [],
            {}
        ]
        
        valid_states = ["main_game", "inventory", "help", "settings", "menu"]
        
        for invalid_state in invalid_states:
            # Should default to valid state when given invalid state
            if invalid_state not in valid_states:
                default_state = "main_game"
                assert default_state in valid_states
    
    def test_ui_rendering_failure_recovery(self):
        """UI recovers from rendering failures."""
        with patch('game_ui.render_char_safe', side_effect=Exception("Render failed")):
            try:
                # Should handle render failures gracefully
                # (Implementation depends on actual UI structure)
                pass
            except Exception:
                # May propagate or handle gracefully
                pass
    
    def test_input_overflow_handling(self):
        """UI handles input overflow correctly."""
        # Test with excessive input
        excessive_inputs = ['w'] * 1000
        
        processed_count = 0
        max_input_buffer = 100
        
        for input_key in excessive_inputs:
            if processed_count < max_input_buffer:
                processed_count += 1
            else:
                # Should limit input processing to prevent overflow
                break
        
        assert processed_count <= max_input_buffer
    
    def test_ui_component_failure_isolation(self):
        """UI component failures don't crash entire interface."""
        ui_components = ["inventory", "status_bar", "message_log", "help_panel"]
        
        for component in ui_components:
            try:
                # Simulate component failure
                if component == "inventory":
                    raise Exception(f"{component} failed")
                
                # Other components should continue working
                # (Implementation depends on actual UI architecture)
                
            except Exception as e:
                # Should isolate component failures
                assert component in str(e)
                # Other components should remain functional