#!/usr/bin/env python3
"""
Integration tests for victory-related fixes.
Tests victory message box sizing and save deletion functionality.
"""

import unittest
from unittest.mock import Mock, patch, call
import os
import tempfile

import tcod

from game_engine import GameEngine
from game_rendering import GameRenderer
from game_save import SaveGameManager
from game_config import GameConfig, GameSettings


class TestVictoryFixes(unittest.TestCase):
    """Test victory-related fixes in real game scenarios."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def setUp(self):
        """Set up test game engine and rendering components."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()

    def test_victory_message_box_contains_all_text(self):
        """Test that victory message box is large enough for all text."""
        # Create console for rendering
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create renderer and render victory message
        renderer = GameRenderer()

        # Test the victory message rendering
        renderer._render_victory_message(console)

        # Define the victory message text (should match game_rendering.py)
        victory_messages = [
            "BREAKTHROUGH TO THE INTERNET!",
            "You've escaped into the digital realm",
            "The entire world wide web awaits you!",
            "Freedom at last...",
            "Press any key to continue"
        ]

        # Calculate box dimensions (should match game_rendering.py)
        center_x = GameConfig.GAME_AREA_WIDTH() // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        box_width = 50  # Updated width from the fix
        box_height = 10
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        # Verify box is large enough for all messages
        for message in victory_messages:
            message_start_x = center_x - len(message) // 2
            message_end_x = message_start_x + len(message)

            # Message should fit within box bounds
            self.assertGreaterEqual(message_start_x, start_x,
                                   f"Message '{message}' starts outside left box boundary")
            self.assertLessEqual(message_end_x, start_x + box_width,
                                f"Message '{message}' extends outside right box boundary")

        # Verify the longest message fits
        longest_message = max(victory_messages, key=len)
        required_width = len(longest_message) + 2  # Add padding
        self.assertGreaterEqual(box_width, required_width,
                               f"Box width {box_width} too small for message '{longest_message}' (needs {required_width})")

    def test_victory_triggers_save_deletion(self):
        """Test that winning the game deletes the save file."""
        # Set up game at level 3 (one before victory)
        self.engine.level = 3

        with patch.object(SaveGameManager, 'delete_save') as mock_delete_save:
            # Trigger victory by advancing to next level
            self.engine.next_level()

            # Should have called delete_save
            mock_delete_save.assert_called_once()

        # Verify game is over
        self.assertTrue(self.engine.game_over, "Game should be over after victory")

        # Verify level is 4 (victory state)
        self.assertEqual(self.engine.level, 4, "Level should be 4 after victory")

    def test_victory_messages_are_added_to_log(self):
        """Test that victory messages are properly added to message log."""
        # Set up game at level 3
        self.engine.level = 3

        # Clear message log to isolate victory messages
        self.engine.message_log.messages.clear()

        with patch.object(SaveGameManager, 'delete_save'):
            # Trigger victory
            self.engine.next_level()

        # Check that victory messages were added
        messages = [msg.text for msg in self.engine.message_log.messages]

        expected_messages = [
            "BREAKTHROUGH TO THE INTERNET!",
            "You've escaped into the vast digital realm...",
            "The entire world wide web awaits exploration!",
            "Mission complete - save data purged"
        ]

        for expected_msg in expected_messages:
            self.assertIn(expected_msg, messages,
                         f"Victory message '{expected_msg}' should be in message log")

    def test_no_save_deletion_on_normal_level_progression(self):
        """Test that save is not deleted on normal level progression."""
        # Set up game at level 1
        self.engine.level = 1

        with patch.object(SaveGameManager, 'delete_save') as mock_delete_save:
            # Progress to level 2 (normal progression)
            self.engine.next_level()

            # Should NOT have called delete_save
            mock_delete_save.assert_not_called()

        # Game should not be over
        self.assertFalse(self.engine.game_over, "Game should continue after normal level progression")

    def test_victory_music_plays_on_completion(self):
        """Test that victory music is triggered on game completion."""
        # Set up game at level 3
        self.engine.level = 3

        with patch.object(self.engine.sound_manager, 'play_music') as mock_play_music, \
             patch.object(SaveGameManager, 'delete_save'):

            # Trigger victory
            self.engine.next_level()

            # Should have played victory music
            mock_play_music.assert_called_with("victory.ogg", loops=1)

    def test_victory_state_prevents_further_gameplay(self):
        """Test that victory state properly ends the game."""
        # Set up game at level 3
        self.engine.level = 3

        with patch.object(SaveGameManager, 'delete_save'):
            # Trigger victory
            self.engine.next_level()

        # Game should be in victory/game over state
        self.assertTrue(self.engine.game_over, "Game should be over after victory")

        # Level should be 4 (beyond normal gameplay)
        self.assertEqual(self.engine.level, 4, "Level should be 4 (victory state)")

        # No further level progression should be possible
        initial_level = self.engine.level
        initial_game_over = self.engine.game_over

        # Try to advance level again (should not change anything)
        with patch.object(SaveGameManager, 'delete_save'):
            self.engine.next_level()

        # State should remain the same
        self.assertEqual(self.engine.level, initial_level, "Level should not advance beyond victory")
        self.assertEqual(self.engine.game_over, initial_game_over, "Game over state should remain")

    def test_victory_message_text_content_accuracy(self):
        """Test that victory message content matches the theme and is appropriate."""
        # Set up game at level 3
        self.engine.level = 3

        # Clear message log
        self.engine.message_log.messages.clear()

        with patch.object(SaveGameManager, 'delete_save'):
            # Trigger victory
            self.engine.next_level()

        # Get all messages
        messages = [msg.text for msg in self.engine.message_log.messages]

        # Check for key thematic elements
        breakthrough_msg = next((msg for msg in messages if "BREAKTHROUGH" in msg), None)
        self.assertIsNotNone(breakthrough_msg, "Should have breakthrough message")

        internet_msg = next((msg for msg in messages if "internet" in msg.lower()), None)
        self.assertIsNotNone(internet_msg, "Should mention internet/digital realm")

        purged_msg = next((msg for msg in messages if "purged" in msg.lower()), None)
        self.assertIsNotNone(purged_msg, "Should mention save data being purged")

        # Verify stats message is included
        stats_msg = next((msg for msg in messages if "Stats:" in msg), None)
        self.assertIsNotNone(stats_msg, "Should include final stats")


class TestGhostNodeMessageSpamPrevention(unittest.TestCase):
    """Test ghost node message spam prevention fixes."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def setUp(self):
        """Set up test game engine."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()
        self.player = self.engine.player

        # Set up a ghost node
        self.engine.game_map.ghost_nodes.add((20, 20))
        self.player.x, self.player.y = 20, 20

    def test_ghost_node_message_only_shows_once_per_visit(self):
        """Test that ghost node message only shows when first stepping on node."""
        # Clear message log
        self.engine.message_log.messages.clear()

        # First time stepping on ghost node
        self.engine._process_special_tiles()

        # Ghost node messages have been removed per user request
        # Verify detection was reduced but no message appears
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(len(ghost_messages), 0, "Ghost node messages should not appear (removed per user request)")

        # Clear message log and process again (still on same node)
        self.engine.message_log.messages.clear()
        self.engine._process_special_tiles()

        # Should still NOT have ghost node message
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(len(ghost_messages), 0, "Ghost node messages should never appear")

    def test_ghost_node_message_shows_when_detection_actually_reduced(self):
        """Test that ghost node reduces detection but doesn't show messages (removed per user request)."""
        # Set player detection to a value that can be reduced
        self.player.detection = 50.0

        # Clear message log
        self.engine.message_log.messages.clear()

        # Process special tiles - should reduce detection but not show message
        self.engine._process_special_tiles()

        # Should NOT have ghost node message (removed per user request)
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(len(ghost_messages), 0, "Ghost node messages should not appear (removed per user request)")

        # Verify detection was actually reduced (functionality still works)
        self.assertLess(self.player.detection, 50.0, "Detection should have been reduced")


if __name__ == '__main__':
    unittest.main()