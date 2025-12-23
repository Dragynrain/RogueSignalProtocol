#!/usr/bin/env python3
"""
Integration tests for game_loop.py critical systems.

Tests focus on:
- Game input event handling and ESC key behavior
- Auto-save on exit
- Menu navigation state transitions
- Error handling paths
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

import tcod

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game_config import GameSettings
from game_engine import GameEngine
from game_loop import handle_error_screen, handle_game_input_events, log_exception


class TestGameInputEventHandling(unittest.TestCase):
    """Test handle_game_input_events function with various scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.settings = GameSettings()
        self.game = Mock(spec=GameEngine)
        self.game.player = Mock()
        self.game.player.cpu = 100
        self.game.game_over = False
        self.game.dialogue_state = Mock()
        self.game.dialogue_state.is_active = Mock(return_value=False)
        self.game.show_lore_viewer = False
        self.game.show_help = False
        self.game.show_inventory = False
        self.game.show_achievements = False
        self.game.show_ascension = False
        self.game.look_mode = False
        self.game.targeting_mode = False
        self.game.auto_save = Mock()
        self.game.sound_manager = Mock()
        self.game.sound_manager.cleanup = Mock()

        self.input_handler = Mock()
        self.input_handler._handle_escape = Mock()
        self.input_handler._handle_dialogue_dismiss = Mock(return_value=True)
        self.input_handler.handle_keydown = Mock(return_value=True)
        self.input_handler.handle_mouse_motion = Mock()
        self.input_handler.handle_mouse_click = Mock()
        self.input_handler.handle_mouse_wheel = Mock()

    def test_quit_event_saves_and_exits(self):
        """Test that QUIT event triggers auto-save and exits."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.Quit()

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should call auto_save
        self.game.auto_save.assert_called_once()
        self.game.sound_manager.cleanup.assert_called_once()

        # Should exit (return False, None)
        self.assertFalse(should_continue)
        self.assertIsNone(result_game)

    def test_escape_with_active_dialogue_dismisses_dialogue(self):
        """Test ESC with active dialogue dismisses it first."""
        self.game.dialogue_state.is_active = Mock(return_value=True)

        # Use proper TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should call dialogue dismiss handler
        self.input_handler._handle_dialogue_dismiss.assert_called_once()

        # Should NOT auto-save
        self.game.auto_save.assert_not_called()

        # Should continue game
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_escape_with_death_dialogue_exits_to_menu(self):
        """Test ESC with death dialogue returns to menu."""
        self.game.dialogue_state.is_active = Mock(return_value=True)
        self.input_handler._handle_dialogue_dismiss = Mock(return_value=False)  # Death dialogue

        # Use proper TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should return to menu (True, None)
        self.assertTrue(should_continue)
        self.assertIsNone(result_game)

    def test_escape_with_inventory_open_closes_inventory(self):
        """Test ESC with inventory open closes it without saving."""
        self.game.show_inventory = True

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should call escape handler to close inventory
        self.input_handler._handle_escape.assert_called_once()

        # Should NOT auto-save
        self.game.auto_save.assert_not_called()

        # Should continue game
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_escape_with_look_mode_closes_look_mode(self):
        """Test ESC with look mode open closes it."""
        self.game.look_mode = True

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should call escape handler
        self.input_handler._handle_escape.assert_called_once()

        # Should NOT auto-save
        self.game.auto_save.assert_not_called()

    def test_escape_with_help_open_closes_help(self):
        """Test ESC with help screen open closes it."""
        self.game.show_help = True

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler._handle_escape.assert_called_once()
        self.game.auto_save.assert_not_called()

    def test_escape_with_lore_viewer_closes_it(self):
        """Test ESC with lore viewer open closes it."""
        self.game.show_lore_viewer = True
        self.game.lore_viewer_mode = "list"

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler._handle_escape.assert_called_once()
        self.game.auto_save.assert_not_called()

    def test_escape_with_targeting_mode_closes_targeting(self):
        """Test ESC with targeting mode open closes it without going to menu.

        Regression test: ESC during targeting should cancel targeting and
        continue gameplay, NOT exit to main menu.
        """
        self.game.targeting_mode = True

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler._handle_escape.assert_called_once()
        self.game.auto_save.assert_not_called()
        # Verify game continues (not going to menu)
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)  # Game continues, not None (menu)

    def test_escape_with_no_ui_open_saves_and_returns_to_menu(self):
        """Test ESC with no UI open triggers auto-save and menu."""
        # All UI states closed
        self.game.show_inventory = False
        self.game.look_mode = False
        self.game.show_help = False

        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should auto-save
        self.game.auto_save.assert_called_once()

        # Should NOT call escape handler (no UI to close)
        self.input_handler._handle_escape.assert_not_called()

        # Should return to menu (True, None)
        self.assertTrue(should_continue)
        self.assertIsNone(result_game)

    def test_escape_priority_dialogue_over_inventory(self):
        """Test ESC prioritizes dialogue dismissal over inventory close."""
        self.game.dialogue_state.is_active = Mock(return_value=True)
        self.game.show_inventory = True

        # Use proper TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should call dialogue dismiss, NOT escape handler
        self.input_handler._handle_dialogue_dismiss.assert_called_once()
        self.input_handler._handle_escape.assert_not_called()

    def test_mouse_motion_event_handled(self):
        """Test MOUSEMOTION event is forwarded to input handler."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        event = tcod.event.MouseMotion(position=(100, 100))

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler.handle_mouse_motion.assert_called_once_with(event)
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_mouse_click_event_handled(self):
        """Test MOUSEBUTTONDOWN event is forwarded to input handler."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        # MouseButtonDown: pixel, tile, button
        event = tcod.event.MouseButtonDown(
            pixel=(100, 100), tile=(10, 10), button=tcod.event.MouseButton.LEFT
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler.handle_mouse_click.assert_called_once_with(event)
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_mouse_wheel_event_handled(self):
        """Test MOUSEWHEEL event is forwarded to input handler."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        # MouseWheel: x, y, flipped
        event = tcod.event.MouseWheel(x=0, y=1, flipped=False)

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler.handle_mouse_wheel.assert_called_once_with(event)
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_keydown_other_than_escape_forwarded(self):
        """Test non-ESC keydown events are forwarded to handler."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        # Use KeySym(ord('w')) for cross-platform compatibility (KeySym.w doesn't exist on Linux)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.W,
            sym=tcod.event.KeySym(ord("w")),
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        self.input_handler.handle_keydown.assert_called_once_with(event)
        self.assertTrue(should_continue)
        self.assertEqual(result_game, self.game)

    def test_player_death_exits_to_menu(self):
        """Test that when player dies and presses a key, return to menu."""
        # Use real TCOD event (isinstance checks require real type, not mock)
        # Use KeySym(ord('w')) for cross-platform compatibility (KeySym.w doesn't exist on Linux)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.W,
            sym=tcod.event.KeySym(ord("w")),
            mod=tcod.event.Modifier.NONE,
        )

        # Input handler returns False (player dead, wants to exit)
        self.input_handler.handle_keydown = Mock(return_value=False)

        should_continue, result_game = handle_game_input_events(
            event, self.game, self.input_handler
        )

        # Should return to menu
        self.assertTrue(should_continue)
        self.assertIsNone(result_game)


class TestErrorHandling(unittest.TestCase):
    """Test error handling functions."""

    def test_log_exception_with_traceback(self):
        """Test log_exception extracts traceback info correctly."""
        with patch("logging.error") as mock_log_error:
            with patch("traceback.print_exc") as mock_print_exc:
                try:
                    raise ValueError("Test error")
                except Exception as e:
                    log_exception(e, "Test context", level="error")

                    # Should call logging.error
                    self.assertTrue(mock_log_error.called)

                    # Check that context was logged
                    error_calls = [str(call) for call in mock_log_error.call_args_list]
                    self.assertTrue(any("Test context" in str(call) for call in error_calls))

                    # Should print traceback
                    mock_print_exc.assert_called_once()

    def test_log_exception_with_warning_level(self):
        """Test log_exception with warning level."""
        with patch("logging.warning") as mock_log_warning:
            with patch("traceback.print_exc"):
                try:
                    raise RuntimeError("Test warning")
                except Exception as e:
                    log_exception(e, "Warning context", level="warning")

                    # Should call logging.warning
                    self.assertTrue(mock_log_warning.called)

    def test_log_exception_with_critical_level(self):
        """Test log_exception with critical level."""
        with patch("logging.critical") as mock_log_critical:
            with patch("traceback.print_exc"):
                try:
                    raise RuntimeError("Test critical")
                except Exception as e:
                    log_exception(e, "Critical context", level="critical")

                    # Should call logging.critical
                    self.assertTrue(mock_log_critical.called)

    @patch("game_loop.render_char_safe")
    def test_handle_error_screen_displays_message(self, mock_render):
        """Test handle_error_screen displays error correctly."""
        console = Mock()
        context = Mock()

        # Use real TCOD event (isinstance checks require real type, not mock)
        quit_event = tcod.event.Quit()

        with patch("tcod.event.wait", return_value=[quit_event]):
            result = handle_error_screen(console, context, "Test error", 42)

            # Should clear console
            console.clear.assert_called_once()

            # Should present console
            context.present.assert_called_once_with(console)

            # Should render error message
            self.assertTrue(mock_render.called)

            # Should return True (exit)
            self.assertTrue(result)

    @patch("game_loop.render_char_safe")
    def test_handle_error_screen_escape_exits(self, mock_render):
        """Test handle_error_screen accepts ESC to exit."""
        console = Mock()
        context = Mock()

        # Use real TCOD event (isinstance checks require real type, not mock)
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        with patch("tcod.event.wait", return_value=[esc_event]):
            result = handle_error_screen(console, context, "Test error", 42)

            self.assertTrue(result)


class TestAutoSaveBehavior(unittest.TestCase):
    """Test auto-save behavior in various scenarios."""

    def test_auto_save_called_on_quit(self):
        """Test auto-save is called when quitting."""
        game = Mock(spec=GameEngine)
        game.auto_save = Mock()
        game.sound_manager = Mock()
        game.sound_manager.cleanup = Mock()

        input_handler = Mock()

        # Use real TCOD event (isinstance checks require real type, not mock)
        quit_event = tcod.event.Quit()

        should_continue, result_game = handle_game_input_events(quit_event, game, input_handler)

        game.auto_save.assert_called_once()

    def test_auto_save_called_on_escape_to_menu(self):
        """Test auto-save is called when escaping to menu."""
        game = Mock(spec=GameEngine)
        game.auto_save = Mock()
        game.player = Mock()
        game.player.cpu = 100
        game.game_over = False
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.show_inventory = False
        game.show_help = False
        game.show_achievements = False
        game.show_ascension = False
        game.look_mode = False
        game.targeting_mode = False
        game.show_lore_viewer = False

        input_handler = Mock()

        # Use real TCOD event (isinstance checks require real type, not mock)
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        should_continue, result_game = handle_game_input_events(esc_event, game, input_handler)

        # Should auto-save when returning to menu
        game.auto_save.assert_called_once()

        # Should return to menu
        self.assertTrue(should_continue)
        self.assertIsNone(result_game)

    def test_no_auto_save_when_closing_inventory(self):
        """Test auto-save is NOT called when just closing inventory."""
        game = Mock(spec=GameEngine)
        game.auto_save = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.show_inventory = True  # Inventory is open
        game.show_lore_viewer = False
        game.show_help = False
        game.show_achievements = False
        game.show_ascension = False
        game.look_mode = False
        game.targeting_mode = False

        input_handler = Mock()
        input_handler._handle_escape = Mock()

        esc_event = Mock()
        esc_event.type = "KEYDOWN"
        esc_event.sym = tcod.event.KeySym.ESCAPE

        should_continue, result_game = handle_game_input_events(esc_event, game, input_handler)

        # Should NOT auto-save (just closing UI)
        game.auto_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
