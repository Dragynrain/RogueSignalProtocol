#!/usr/bin/env python3
"""
Unit tests for game_input.py - User input handling and key mapping.
Tests keyboard input processing, UI navigation, and game action triggering.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch
import tcod.event

# Import game modules
from game_input import InputHandler
from game_engine import GameEngine
from game_entities import Position
from game_characters import Player
from game_combat import ExploitSystem
from game_inventory import CodeHack, ExploitItem
from game_story import StoryFragmentManager


class TestInputHandlerInitialization(unittest.TestCase):
    """Test InputHandler initialization and basic setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.cpu = 100

    def test_input_handler_initialization(self):
        """Test InputHandler initializes correctly."""
        with patch('game_input.ExploitSystem') as mock_exploit_system:
            handler = InputHandler(self.mock_game)

            # Should store game reference and create exploit system
            self.assertEqual(handler.game, self.mock_game)
            mock_exploit_system.assert_called_once_with(self.mock_game)

    def test_input_handler_exploit_system_creation(self):
        """Test exploit system is properly created."""
        with patch('game_input.ExploitSystem') as mock_exploit_system_class:
            mock_exploit_system = Mock()
            mock_exploit_system_class.return_value = mock_exploit_system

            handler = InputHandler(self.mock_game)

            # Should have exploit system instance
            self.assertEqual(handler.exploit_system, mock_exploit_system)


class TestInputHandlerGameOverState(unittest.TestCase):
    """Test input handling when game is over or player is dead."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.game_over = False

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_dead_player_input_exits(self):
        """Test any input exits when player is dead."""
        self.mock_game.player.cpu = 0
        self.mock_game.game_over = False

        # Create mock key event
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SPACE

        # Should return False (exit)
        result = self.handler.handle_keydown(mock_event)
        self.assertFalse(result)

    def test_game_over_input_exits(self):
        """Test any input exits when game is over."""
        self.mock_game.player.cpu = 100
        self.mock_game.game_over = True

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        # Should return False (exit)
        result = self.handler.handle_keydown(mock_event)
        self.assertFalse(result)

    def test_normal_state_continues_processing(self):
        """Test normal state continues to other input handlers."""
        self.mock_game.player.cpu = 100
        self.mock_game.game_over = False
        self.mock_game.show_help = False
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.show_inventory = False
        self.mock_game.targeting_mode = False

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SPACE

        with patch.object(self.handler, '_handle_gameplay_input', return_value=True) as mock_gameplay:
            result = self.handler.handle_keydown(mock_event)

            # Should continue processing and call gameplay handler
            self.assertTrue(result)
            mock_gameplay.assert_called_once_with(mock_event)


class TestInputHandlerModalScreens(unittest.TestCase):
    """Test input handling for modal screens (help, story fragments, etc.)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.cpu = 100
        self.mock_game.game_over = False

        # Reset all modal states
        self.mock_game.show_help = False
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.show_inventory = False
        self.mock_game.targeting_mode = False

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_help_screen_any_key_closes(self):
        """Test any key closes help screen."""
        self.mock_game.show_help = True

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SPACE

        result = self.handler.handle_keydown(mock_event)

        # Should close help and continue
        self.assertFalse(self.mock_game.show_help)
        self.assertTrue(result)

    def test_story_fragment_any_key_closes(self):
        """Test any key closes story fragment display."""
        self.mock_game.show_story_fragment = 1

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        result = self.handler.handle_keydown(mock_event)

        # Should close story fragment and continue
        self.assertIsNone(self.mock_game.show_story_fragment)
        self.assertTrue(result)


class TestInputHandlerEscapeHandling(unittest.TestCase):
    """Test escape key handling for various UI states."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.message_log = Mock()

        # Reset all modal states
        self.mock_game.show_help = False
        self.mock_game.show_story_fragment = None
        self.mock_game.show_lore_viewer = False
        self.mock_game.show_gateway_confirmation = False
        self.mock_game.show_inventory = False
        self.mock_game.targeting_mode = False
        self.mock_game.targeting_exploit = None
        self.mock_game.lore_viewer_mode = "list"
        self.mock_game.lore_viewer_selection = 0

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_escape_closes_story_fragment(self):
        """Test escape key closes story fragment."""
        self.mock_game.show_story_fragment = 5

        result = self.handler._handle_escape()

        self.assertIsNone(self.mock_game.show_story_fragment)
        self.assertTrue(result)

    def test_escape_cancels_targeting(self):
        """Test escape key cancels targeting mode."""
        self.mock_game.targeting_mode = True
        self.mock_game.targeting_exploit = "code_injection"

        result = self.handler._handle_escape()

        self.assertFalse(self.mock_game.targeting_mode)
        self.assertIsNone(self.mock_game.targeting_exploit)
        self.mock_game.message_log.add_message.assert_called_once_with("Targeting cancelled")
        self.assertTrue(result)


class TestInputHandlerGatewayConfirmation(unittest.TestCase):
    """Test gateway confirmation input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.message_log = Mock()
        self.mock_game.sound_manager = Mock()

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_confirm_key_triggers_next_level(self):
        """Test confirm key (Enter/Return) triggers level progression."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_confirm_key.return_value = True

            result = self.handler._handle_gateway_confirmation_input(mock_event)

            # Should close confirmation and trigger next level
            self.assertFalse(self.mock_game.show_gateway_confirmation)
            self.mock_game.sound_manager.play_sound.assert_called_once_with("level_complete")
            self.mock_game.message_log.add_message.assert_called_with("Gateway reached! Next network...")
            self.mock_game.next_level.assert_called_once()
            self.assertTrue(result)

    def test_y_key_triggers_next_level(self):
        """Test Y key triggers level progression."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.Y

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_confirm_key.return_value = False  # Not confirm key, but Y

            result = self.handler._handle_gateway_confirmation_input(mock_event)

            # Should still trigger next level
            self.assertFalse(self.mock_game.show_gateway_confirmation)
            self.mock_game.next_level.assert_called_once()
            self.assertTrue(result)

    def test_n_key_cancels_gateway(self):
        """Test N key cancels gateway transition."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.N

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_confirm_key.return_value = False
            mock_ui.is_escape_key.return_value = False

            result = self.handler._handle_gateway_confirmation_input(mock_event)

            # Should close confirmation without triggering next level
            self.assertFalse(self.mock_game.show_gateway_confirmation)
            self.mock_game.message_log.add_message.assert_called_with("Staying in current network")
            self.mock_game.next_level.assert_not_called()
            self.assertTrue(result)

    def test_escape_key_cancels_gateway(self):
        """Test Escape key cancels gateway transition."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.ESCAPE

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_confirm_key.return_value = False
            mock_ui.is_escape_key.return_value = True

            result = self.handler._handle_gateway_confirmation_input(mock_event)

            # Should close confirmation without triggering next level
            self.assertFalse(self.mock_game.show_gateway_confirmation)
            self.mock_game.message_log.add_message.assert_called_with("Staying in current network")
            self.mock_game.next_level.assert_not_called()
            self.assertTrue(result)


class TestInputHandlerInventoryInput(unittest.TestCase):
    """Test inventory input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.show_inventory = True

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_navigation_handled_by_universal_handler(self):
        """Test navigation is handled by UniversalInputHandler."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.UP

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = True

            result = self.handler._handle_inventory_input(mock_event)

            # Should delegate to universal handler and return early
            mock_ui.handle_list_navigation.assert_called_once()
            self.assertTrue(result)

    def test_confirm_key_uses_selected_item(self):
        """Test confirm key uses selected inventory item."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = False
            mock_ui.is_confirm_key.return_value = True

            with patch.object(self.handler, '_use_selected_inventory_item') as mock_use:
                result = self.handler._handle_inventory_input(mock_event)

                mock_use.assert_called_once()
                self.assertTrue(result)

    def test_u_key_unequips_exploit(self):
        """Test U key unequips selected exploit."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.U

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = False
            mock_ui.is_confirm_key.return_value = False

            with patch.object(self.handler, '_unequip_selected_exploit') as mock_unequip:
                result = self.handler._handle_inventory_input(mock_event)

                mock_unequip.assert_called_once()
                self.assertTrue(result)

    def test_x_key_examines_item(self):
        """Test X key examines selected item."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.X

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = False
            mock_ui.is_confirm_key.return_value = False

            with patch.object(self.handler, '_examine_selected_item') as mock_examine:
                result = self.handler._handle_inventory_input(mock_event)

                mock_examine.assert_called_once()
                self.assertTrue(result)

    def test_i_key_closes_inventory(self):
        """Test I key closes inventory."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.I

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = False
            mock_ui.is_confirm_key.return_value = False

            result = self.handler._handle_inventory_input(mock_event)

            self.assertFalse(self.mock_game.show_inventory)
            self.assertTrue(result)


class TestInputHandlerLoreViewer(unittest.TestCase):
    """Test lore viewer input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.story_fragment_manager = Mock(spec=StoryFragmentManager)
        self.mock_game.lore_viewer_mode = "list"
        self.mock_game.lore_viewer_selection = 0

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_no_fragments_only_escape_works(self):
        """Test when no fragments discovered, only escape should work."""
        self.mock_game.story_fragment_manager.get_discovered_fragments.return_value = []

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SPACE

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_escape_key.return_value = False

            result = self.handler._handle_lore_viewer_input(mock_event)
            self.assertFalse(result)

    def test_fragments_available_navigation_in_list_mode(self):
        """Test navigation works when fragments are available in list mode."""
        self.mock_game.story_fragment_manager.get_discovered_fragments.return_value = [1, 2, 3]
        self.mock_game.lore_viewer_mode = "list"

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.UP

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = True

            result = self.handler._handle_lore_viewer_input(mock_event)

            mock_ui.handle_list_navigation.assert_called_once()
            self.assertTrue(result)

    def test_confirm_key_enters_reading_mode(self):
        """Test confirm key enters reading mode for selected fragment."""
        self.mock_game.story_fragment_manager.get_discovered_fragments.return_value = [1, 2, 3]
        self.mock_game.lore_viewer_mode = "list"

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.handle_list_navigation.return_value = False
            mock_ui.is_confirm_key.return_value = True

            result = self.handler._handle_lore_viewer_input(mock_event)

            self.assertEqual(self.mock_game.lore_viewer_mode, "reading")
            self.assertTrue(result)

    def test_reading_mode_any_key_returns_to_list(self):
        """Test in reading mode, any key returns to list mode."""
        self.mock_game.story_fragment_manager.get_discovered_fragments.return_value = [1, 2, 3]
        self.mock_game.lore_viewer_mode = "reading"

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SPACE

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_escape_key.return_value = False

            result = self.handler._handle_lore_viewer_input(mock_event)

            self.assertEqual(self.mock_game.lore_viewer_mode, "list")
            self.assertTrue(result)

    def test_escape_in_reading_mode_delegates_to_main_loop(self):
        """Test escape in reading mode is handled by main loop."""
        self.mock_game.story_fragment_manager.get_discovered_fragments.return_value = [1, 2, 3]
        self.mock_game.lore_viewer_mode = "reading"

        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.ESCAPE

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_escape_key.return_value = True

            result = self.handler._handle_lore_viewer_input(mock_event)

            # Should return False to let main loop handle escape
            self.assertFalse(result)


class TestInputHandlerTargetingMode(unittest.TestCase):
    """Test targeting mode input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.targeting_mode = True
        self.mock_game.targeting_exploit = "code_injection"
        self.mock_game.cursor_position = Position(10, 10)
        self.mock_game.message_log = Mock()

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_movement_keys_move_cursor(self):
        """Test movement keys move the targeting cursor."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.UP

        with patch.object(self.mock_game, '_move_cursor') as mock_move_cursor:
            result = self.handler._handle_targeting_input(mock_event)

            # Should move cursor using _move_cursor
            mock_move_cursor.assert_called_once_with(0, -1)
            self.assertTrue(result)

    def test_confirm_key_uses_exploit_at_cursor(self):
        """Test confirm key uses exploit at cursor position."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        with patch.object(self.handler.exploit_system, 'execute_exploit') as mock_execute:
            result = self.handler._handle_targeting_input(mock_event)

            # Should execute exploit at cursor position
            mock_execute.assert_called_once_with("code_injection", self.mock_game.cursor_position)
            self.assertTrue(result)

    def test_failed_exploit_use_stays_in_targeting(self):
        """Test failed exploit use keeps targeting mode active."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.RETURN

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_movement_key.return_value = False
            mock_ui.is_confirm_key.return_value = True

            with patch.object(self.handler.exploit_system, 'use_exploit', return_value=False):
                result = self.handler._handle_targeting_input(mock_event)

                # Should stay in targeting mode
                self.assertTrue(self.mock_game.targeting_mode)
                self.assertEqual(self.mock_game.targeting_exploit, "code_injection")
                self.assertTrue(result)


class TestInputHandlerGameplayInput(unittest.TestCase):
    """Test normal gameplay input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.cpu = 100
        self.mock_game.game_over = False
        self.mock_game.show_help = False
        self.mock_game.show_inventory = False
        self.mock_game.sound_manager = Mock()

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_movement_keys_trigger_player_movement(self):
        """Test movement keys trigger player movement."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.UP

        with patch.object(self.mock_game, 'move_player') as mock_move:
            result = self.handler._handle_gameplay_input(mock_event)

            mock_move.assert_called_once_with(0, -1)
            self.assertTrue(result)

    def test_shift_slash_shows_help(self):
        """Test Shift+/ shows help screen."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.SLASH
        mock_event.mod = tcod.event.Modifier.LSHIFT

        result = self.handler._handle_gameplay_input(mock_event)

        self.assertTrue(self.mock_game.show_help)
        self.assertTrue(result)

    def test_i_key_shows_inventory(self):
        """Test I key shows inventory."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.I

        with patch.object(self.handler, '_open_inventory') as mock_open:
            result = self.handler._handle_gameplay_input(mock_event)

            mock_open.assert_called_once()
            self.assertTrue(result)

    def test_l_key_shows_lore_viewer(self):
        """Test L key shows lore viewer."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.L

        result = self.handler._handle_gameplay_input(mock_event)

        self.assertTrue(self.mock_game.show_lore_viewer)
        self.assertTrue(result)

    def test_unhandled_key_returns_true(self):
        """Test unhandled keys return True to continue game."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.F1  # Random unhandled key

        result = self.handler._handle_gameplay_input(mock_event)

        # Should return True even for unhandled keys
        self.assertTrue(result)


class TestInputHandlerExploitActivation(unittest.TestCase):
    """Test exploit activation through number keys."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_game = Mock(spec=GameEngine)
        self.mock_game.player = Mock(spec=Player)
        self.mock_game.player.inventory_manager = Mock()
        self.mock_game.player.inventory_manager.equipped_exploits = ["shadow_step", "code_injection"]

        with patch('game_input.ExploitSystem'):
            self.handler = InputHandler(self.mock_game)

    def test_number_key_activates_equipped_exploit(self):
        """Test number keys activate corresponding equipped exploits."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.N1  # Key '1'

        with patch.object(self.handler, '_use_exploit_slot') as mock_use_slot:
            result = self.handler._handle_gameplay_input(mock_event)

            # Should use exploit slot 0 (first equipped exploit)
            mock_use_slot.assert_called_once_with(0)
            self.assertTrue(result)

    def test_number_key_beyond_equipped_range_ignored(self):
        """Test number keys beyond equipped exploit range are ignored."""
        mock_event = Mock(spec=tcod.event.KeyDown)
        mock_event.sym = tcod.event.KeySym.N5  # Key '5' - beyond range

        with patch('game_input.UniversalInputHandler') as mock_ui:
            mock_ui.is_movement_key.return_value = False
            mock_ui.is_escape_key.return_value = False

        with patch.object(self.handler.exploit_system, 'activate_exploit') as mock_activate:
            result = self.handler._handle_gameplay_input(mock_event)

            # Should not activate any exploit
            mock_activate.assert_not_called()
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()