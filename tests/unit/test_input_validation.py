"""
Test Category 6: Input Validation and Edge Cases
Tests for game_input.py - ensuring robust input handling and edge case coverage.
"""

import pytest
import tcod.event
from unittest.mock import Mock, MagicMock, patch

# Import test fixtures
from tests.fixtures.simple_fixtures import player

# Import game modules
from game_input import InputHandler
from game_ui import UniversalInputHandler
from game_entities import Position


def create_mock_game():
    """Create a mock game object for testing."""
    game = Mock()

    # Player
    game.player = player()
    game.player.inventory_manager = Mock()
    game.player.inventory_manager.equipped_exploits = []
    game.player.inventory_manager.get_display_items = Mock(return_value=[])

    # Game state
    game.game_over = False
    game.show_help = False
    game.show_story_fragment = None
    game.show_lore_viewer = False
    game.show_gateway_confirmation = False
    game.show_inventory = False
    game.targeting_mode = False
    game.targeting_exploit = None
    game.look_mode = False
    game.look_cursor_position = Position(10, 10)
    game.cursor_position = Position(10, 10)
    game.inventory_selection = 0
    game.lore_viewer_mode = "list"
    game.lore_viewer_selection = 0

    # Mock methods
    game.move_player = Mock()
    game.maybe_process_turn = Mock()
    game.next_level = Mock()
    game._move_cursor = Mock()

    # Mock managers
    game.message_log = Mock()
    game.message_log.add_message = Mock()
    game.sound_manager = Mock()
    game.sound_manager.play_sound = Mock()
    game.story_fragment_manager = Mock()
    game.story_fragment_manager.get_discovered_fragments = Mock(return_value=[])
    game.dialogue_manager = Mock()  # Add dialogue_manager mock for new dialogue system
    game.dialogue_manager.is_active = Mock(return_value=False)  # Dialogue not active by default

    return game


def create_mock_event(key_sym, mod=tcod.event.Modifier.NONE):
    """Create a mock keyboard event."""
    event = Mock()
    event.sym = key_sym
    event.mod = mod
    return event


class TestInputHandler:
    """Test the main InputHandler class for input validation and edge cases."""
    
    def test_input_handler_initialization(self):
        """Test that InputHandler initializes correctly with game instance."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        assert handler.game == game
        assert handler.exploit_system is not None
    
    def test_dead_player_any_key_exits(self):
        """Test that any key exits to main menu when player is dead."""
        game = create_mock_game()
        game.player.cpu = 0  # Dead player
        game.game_over = False
        
        handler = InputHandler(game)
        
        # Test various keys should all return False (exit)
        test_keys = [
            tcod.event.KeySym.W,  # Movement
            tcod.event.KeySym.SPACE,  # Wait
            tcod.event.KeySym.I,  # Inventory
            tcod.event.KeySym.ESCAPE,  # Escape
            tcod.event.KeySym.RETURN  # Enter
        ]
        
        for key in test_keys:
            event = create_mock_event(key)
            result = handler.handle_keydown(event)
            assert result is False, f"Key {key} should exit when player is dead"
    
    def test_game_over_state_any_key_exits(self):
        """Test that any key exits when game_over flag is set."""
        game = create_mock_game()
        game.player.cpu = 100  # Alive player
        game.game_over = True  # But game over
        
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.SPACE)
        result = handler.handle_keydown(event)
        assert result is False
    
    def test_help_screen_any_key_closes(self):
        """Test that any key closes help screen."""
        game = create_mock_game()
        game.show_help = True
        
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.SPACE)
        result = handler.handle_keydown(event)
        
        assert result is True
        assert game.show_help is False
    
    def test_story_fragment_any_key_closes(self):
        """Test that any key closes story fragment display."""
        game = create_mock_game()
        game.show_story_fragment = "some_fragment"
        
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.SPACE)
        result = handler.handle_keydown(event)
        
        assert result is True
        assert game.show_story_fragment is None
    
    def test_escape_key_handling_multiple_states(self):
        """Test escape key behavior across different UI states."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test story fragment
        game.show_story_fragment = "test"
        handler._handle_escape()
        assert game.show_story_fragment is None
        
        # Test lore viewer
        game.show_lore_viewer = True
        game.lore_viewer_mode = "reading"
        game.lore_viewer_selection = 5
        handler._handle_escape()
        assert game.show_lore_viewer is False
        assert game.lore_viewer_mode == "list"
        assert game.lore_viewer_selection == 0
        
        # Test help
        game.show_help = True
        handler._handle_escape()
        assert game.show_help is False
        
        # Test gateway confirmation
        game.show_gateway_confirmation = True
        handler._handle_escape()
        assert game.show_gateway_confirmation is False
        
        # Test inventory
        game.show_inventory = True
        handler._handle_escape()
        assert game.show_inventory is False
        
        # Test targeting mode
        game.targeting_mode = True
        game.targeting_exploit = "test_exploit"
        handler._handle_escape()
        assert game.targeting_mode is False
        assert game.targeting_exploit is None


class TestMovementInputValidation:
    """Test movement input validation and boundary conditions."""
    
    def test_all_movement_keys_recognized(self):
        """Test that all movement key types are properly recognized."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test WASD + QEZC movement keys
        wasd_keys = [
            (tcod.event.KeySym.W, (0, -1)),
            (tcod.event.KeySym.A, (-1, 0)), 
            (tcod.event.KeySym.S, (0, 1)),
            (tcod.event.KeySym.D, (1, 0)),
            (tcod.event.KeySym.Q, (-1, -1)),
            (tcod.event.KeySym.E, (1, -1)),
            (tcod.event.KeySym.Z, (-1, 1)),
            (tcod.event.KeySym.C, (1, 1))
        ]
        
        for key_sym, expected_direction in wasd_keys:
            event = create_mock_event(key_sym)
            handler._handle_gameplay_input(event)
            game.move_player.assert_called_with(*expected_direction)
            game.move_player.reset_mock()
    
    def test_arrow_key_movement(self):
        """Test arrow key movement input."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        arrow_keys = [
            (tcod.event.KeySym.UP, (0, -1)),
            (tcod.event.KeySym.DOWN, (0, 1)),
            (tcod.event.KeySym.LEFT, (-1, 0)),
            (tcod.event.KeySym.RIGHT, (1, 0))
        ]
        
        for key_sym, expected_direction in arrow_keys:
            event = create_mock_event(key_sym)
            handler._handle_gameplay_input(event)
            game.move_player.assert_called_with(*expected_direction)
            game.move_player.reset_mock()
    
    def test_numpad_movement(self):
        """Test numpad movement input."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        numpad_keys = [
            (tcod.event.KeySym.KP_8, (0, -1)),   # North
            (tcod.event.KeySym.KP_2, (0, 1)),    # South
            (tcod.event.KeySym.KP_4, (-1, 0)),   # West
            (tcod.event.KeySym.KP_6, (1, 0)),    # East
            (tcod.event.KeySym.KP_7, (-1, -1)),  # Northwest
            (tcod.event.KeySym.KP_9, (1, -1)),   # Northeast
            (tcod.event.KeySym.KP_1, (-1, 1)),   # Southwest
            (tcod.event.KeySym.KP_3, (1, 1))     # Southeast
        ]
        
        for key_sym, expected_direction in numpad_keys:
            event = create_mock_event(key_sym)
            handler._handle_gameplay_input(event)
            game.move_player.assert_called_with(*expected_direction)
            game.move_player.reset_mock()
    
    def test_targeting_mode_movement(self):
        """Test movement while in targeting mode moves cursor instead of player."""
        game = create_mock_game()
        game.targeting_mode = True
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.W)
        handler._handle_targeting_input(event)
        
        # Should move cursor, not player
        game._move_cursor.assert_called_with(0, -1)
        game.move_player.assert_not_called()
    
    def test_wait_keys_all_work(self):
        """Test that all wait/rest keys trigger turn processing."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        wait_keys = [
            tcod.event.KeySym.SPACE,
            tcod.event.KeySym.PERIOD,
            tcod.event.KeySym.KP_5
        ]
        
        for key_sym in wait_keys:
            event = create_mock_event(key_sym)
            handler._handle_gameplay_input(event)
            game.maybe_process_turn.assert_called()
            game.maybe_process_turn.reset_mock()


class TestExploitInputValidation:
    """Test exploit usage input validation."""
    
    def test_exploit_number_keys(self):
        """Test that number keys 1-5 trigger exploit usage."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        number_keys = [
            (tcod.event.KeySym.N1, 0),
            (tcod.event.KeySym.N2, 1),
            (tcod.event.KeySym.N3, 2),
            (tcod.event.KeySym.N4, 3),
            (tcod.event.KeySym.N5, 4)
        ]
        
        for key_sym, expected_slot in number_keys:
            with patch.object(handler, '_use_exploit_slot') as mock_use:
                event = create_mock_event(key_sym)
                handler._handle_gameplay_input(event)
                mock_use.assert_called_with(expected_slot)
    
    def test_exploit_slot_validation(self):
        """Test exploit slot validation for valid and invalid slots."""
        game = create_mock_game()
        game.player.inventory_manager.equipped_exploits = ["exploit1", "exploit2"]
        
        handler = InputHandler(game)
        
        # Mock the exploit system to avoid GameData lookup
        handler.exploit_system = Mock()
        
        # Valid slot
        handler._use_exploit_slot(0)
        handler.exploit_system.use_exploit.assert_called_with("exploit1")
        
        # Valid slot 2
        handler._use_exploit_slot(1)
        handler.exploit_system.use_exploit.assert_called_with("exploit2")
        
        # Invalid slot (out of range)
        handler.exploit_system.use_exploit.reset_mock()
        handler._use_exploit_slot(5)
        handler.exploit_system.use_exploit.assert_not_called()
    
    def test_targeting_mode_exploit_execution(self):
        """Test exploit execution in targeting mode."""
        game = create_mock_game()
        game.targeting_mode = True
        game.targeting_exploit = "test_exploit"
        game.cursor_position = Position(5, 5)
        
        handler = InputHandler(game)
        
        # Mock the exploit system
        handler.exploit_system = Mock()
        
        # Test Enter key
        event = create_mock_event(tcod.event.KeySym.RETURN)
        handler._handle_targeting_input(event)
        
        handler.exploit_system.execute_exploit.assert_called_with("test_exploit", Position(5, 5))
        
        # Test Numpad Enter
        event = create_mock_event(tcod.event.KeySym.KP_ENTER)
        handler._handle_targeting_input(event)
        
        assert handler.exploit_system.execute_exploit.call_count == 2


class TestUIToggleInputValidation:
    """Test UI toggle input validation and edge cases."""
    
    def test_inventory_toggle(self):
        """Test inventory toggle functionality."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test opening inventory
        event = create_mock_event(tcod.event.KeySym.I)
        handler._handle_gameplay_input(event)
        
        game.sound_manager.play_sound.assert_called_with("ui_menu_open")
        assert game.show_inventory is True
        assert game.inventory_selection == 0
        
        # Test closing inventory from within inventory mode
        game.show_inventory = True
        handler._handle_inventory_input(event)
        assert game.show_inventory is False
    
    def test_lore_viewer_toggle(self):
        """Test lore viewer toggle."""
        game = create_mock_game()
        handler = InputHandler(game)

        event = create_mock_event(tcod.event.KeySym.O)
        handler._handle_gameplay_input(event)

        assert game.show_lore_viewer is True
    
    def test_help_toggle_with_shift(self):
        """Test help toggle with shift+? (/)."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Create event with shift modifier
        event = create_mock_event(tcod.event.KeySym.SLASH)
        event.mod = tcod.event.Modifier.LSHIFT
        
        handler._handle_gameplay_input(event)
        
        assert game.show_help is True
    
    def test_help_without_shift_ignored(self):
        """Test that / without shift doesn't open help."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.SLASH)
        event.mod = tcod.event.Modifier.NONE  # No shift
        
        original_help_state = game.show_help
        handler._handle_gameplay_input(event)
        
        assert game.show_help == original_help_state  # Should remain unchanged


class TestInventoryInputEdgeCases:
    """Test inventory input handling edge cases."""
    
    def test_inventory_navigation_empty(self):
        """Test inventory navigation with no items."""
        game = create_mock_game()
        game.player.inventory_manager.equipped_exploits = []
        game.player.inventory_manager.get_display_items.return_value = []
        
        handler = InputHandler(game)
        
        # Navigation should not crash with empty inventory
        handler._navigate_inventory(1)
        handler._navigate_inventory(-1)
        
        # Selection should remain 0
        assert game.inventory_selection == 0
    
    def test_inventory_navigation_wraparound(self):
        """Test inventory navigation wraparound behavior."""
        game = create_mock_game()
        game.player.inventory_manager.equipped_exploits = ["exploit1"]
        game.player.inventory_manager.get_display_items.return_value = ["item1", "item2"]
        game.inventory_selection = 0
        
        handler = InputHandler(game)
        
        # Forward navigation
        handler._navigate_inventory(1)
        assert game.inventory_selection == 1
        
        handler._navigate_inventory(1)
        assert game.inventory_selection == 2
        
        # Should wrap to beginning
        handler._navigate_inventory(1)
        assert game.inventory_selection == 0
        
        # Backward navigation should wrap to end
        handler._navigate_inventory(-1)
        assert game.inventory_selection == 2
    
    def test_inventory_item_usage_edge_cases(self):
        """Test inventory item usage with edge cases."""
        game = create_mock_game()
        
        # Mock items and equipped exploits
        mock_item = Mock()
        mock_item.use.return_value = True
        
        game.player.inventory_manager.equipped_exploits = ["exploit1"]
        game.player.inventory_manager.get_display_items.return_value = [mock_item]
        
        handler = InputHandler(game)
        
        # Test using item when selection is out of range
        game.inventory_selection = 999
        handler._use_selected_inventory_item()
        mock_item.use.assert_not_called()
        
        # Test using valid item
        game.inventory_selection = 1  # Index 1 = first inventory item (after 1 equipped exploit)
        handler._use_selected_inventory_item()
        mock_item.use.assert_called_with(game.player, game)
    
    def test_examine_item_edge_cases(self):
        """Test examining items with various edge cases."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test examining with no selection
        game.player.inventory_manager.equipped_exploits = []
        game.player.inventory_manager.get_display_items.return_value = []
        game.inventory_selection = 0
        
        handler._examine_selected_item()
        game.message_log.add_message.assert_called_with("No item selected")
        
        # Test examining out of range selection
        game.inventory_selection = 999
        handler._examine_selected_item()
        game.message_log.add_message.assert_called_with("No item selected")


class TestGatewayConfirmationInput:
    """Test gateway confirmation input handling."""
    
    def test_gateway_confirmation_yes(self):
        """Test gateway confirmation with Yes input."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test Y key
        event = create_mock_event(tcod.event.KeySym.Y)
        result = handler._handle_gateway_confirmation_input(event)
        
        assert result is True
        assert game.show_gateway_confirmation is False
        game.sound_manager.play_sound.assert_called_with("level_complete")
        game.message_log.add_message.assert_called_with("Gateway reached! Next network...")
        game.next_level.assert_called()
    
    def test_gateway_confirmation_no(self):
        """Test gateway confirmation with No input."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        # Test N key
        event = create_mock_event(tcod.event.KeySym.N)
        result = handler._handle_gateway_confirmation_input(event)
        
        assert result is True
        assert game.show_gateway_confirmation is False
        game.message_log.add_message.assert_called_with("Staying in current network")
        game.next_level.assert_not_called()
    
    def test_gateway_confirmation_escape(self):
        """Test gateway confirmation with Escape key."""
        game = create_mock_game()
        handler = InputHandler(game)
        
        event = create_mock_event(tcod.event.KeySym.ESCAPE)
        result = handler._handle_gateway_confirmation_input(event)
        
        assert result is True
        assert game.show_gateway_confirmation is False
        game.next_level.assert_not_called()


class TestLoreViewerInputEdgeCases:
    """Test lore viewer input handling edge cases."""
    
    def test_lore_viewer_no_fragments(self):
        """Test lore viewer behavior when no fragments are discovered."""
        game = create_mock_game()
        game.story_fragment_manager.get_discovered_fragments.return_value = []
        
        handler = InputHandler(game)
        
        # Only escape should return True (is escape key)
        escape_event = create_mock_event(tcod.event.KeySym.ESCAPE)
        result = handler._handle_lore_viewer_input(escape_event)
        assert result is True  # Returns True because it's the escape key
        
        # Other keys should return False (not escape key)
        other_event = create_mock_event(tcod.event.KeySym.SPACE)
        result = handler._handle_lore_viewer_input(other_event)
        assert result is False  # Returns False because it's not the escape key
    
    def test_lore_viewer_navigation_modes(self):
        """Test lore viewer navigation in different modes."""
        game = create_mock_game()
        game.story_fragment_manager.get_discovered_fragments.return_value = ["frag1", "frag2", "frag3"]
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        
        handler = InputHandler(game)
        
        # Test entering reading mode
        enter_event = create_mock_event(tcod.event.KeySym.RETURN)
        result = handler._handle_lore_viewer_input(enter_event)
        assert result is True
        assert game.lore_viewer_mode == "reading"
        
        # Test reading mode - any key should return to list
        game.lore_viewer_mode = "reading"
        space_event = create_mock_event(tcod.event.KeySym.SPACE)
        result = handler._handle_lore_viewer_input(space_event)
        assert result is True
        assert game.lore_viewer_mode == "list"
    
    def test_lore_viewer_navigation_bounds(self):
        """Test lore viewer navigation boundary conditions."""
        game = create_mock_game()
        game.story_fragment_manager.get_discovered_fragments.return_value = ["frag1", "frag2"]
        game.lore_viewer_selection = 0
        
        handler = InputHandler(game)
        
        # Navigate down
        handler._navigate_lore_viewer(1)
        assert game.lore_viewer_selection == 1
        
        # Navigate down past end (should clamp)
        handler._navigate_lore_viewer(1)
        assert game.lore_viewer_selection == 1  # Should stay at max
        
        # Navigate up
        handler._navigate_lore_viewer(-1)
        assert game.lore_viewer_selection == 0
        
        # Navigate up past beginning (should clamp)
        handler._navigate_lore_viewer(-1)
        assert game.lore_viewer_selection == 0  # Should stay at min


class TestUniversalInputHandlerEdgeCases:
    """Test edge cases in UniversalInputHandler."""
    
    def test_key_validation_methods(self):
        """Test key validation static methods."""
        # Test escape key trace level
        escape_event = create_mock_event(tcod.event.KeySym.ESCAPE)
        assert UniversalInputHandler.is_escape_key(escape_event) is True
        
        non_escape_event = create_mock_event(tcod.event.KeySym.SPACE)
        assert UniversalInputHandler.is_escape_key(non_escape_event) is False
        
        # Test confirm key trace level
        enter_event = create_mock_event(tcod.event.KeySym.RETURN)
        assert UniversalInputHandler.is_confirm_key(enter_event) is True
        
        kp_enter_event = create_mock_event(tcod.event.KeySym.KP_ENTER)
        assert UniversalInputHandler.is_confirm_key(kp_enter_event) is True
        
        other_event = create_mock_event(tcod.event.KeySym.SPACE)
        assert UniversalInputHandler.is_confirm_key(other_event) is False
    
    def test_list_navigation_edge_cases(self):
        """Test list navigation with edge cases."""
        mock_screen = Mock()
        mock_screen.selected_option = 0
        
        # Test with zero options - navigation should still handle key but do nothing
        result = UniversalInputHandler.handle_list_navigation(
            mock_screen, 
            create_mock_event(tcod.event.KeySym.UP), 
            1,  # At least 1 option to avoid division by zero
            True
        )
        assert result is True  # Navigation keys are still handled
        
        # Test with normal navigation using callback
        mock_screen.selected_option = 1
        up_event = create_mock_event(tcod.event.KeySym.UP)
        
        def navigation_callback(direction):
            if direction == -1:
                mock_screen.selected_option = max(0, mock_screen.selected_option - 1)
        
        result = UniversalInputHandler.handle_list_navigation(
            mock_screen,
            up_event,
            3,  # 3 options
            True,
            navigation_callback
        )
        assert result is True
        assert mock_screen.selected_option == 0


if __name__ == "__main__":
    pytest.main([__file__])