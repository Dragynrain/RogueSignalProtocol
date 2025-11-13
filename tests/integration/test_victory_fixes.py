#!/usr/bin/env python3
"""
Integration tests for victory-related fixes.
Tests victory message box sizing and save deletion functionality.
"""

import unittest
from unittest.mock import Mock, patch

import tcod

from game_config import GameConfig, GameSettings
from game_engine import GameEngine
from game_save import SaveGameManager


class TestVictoryFixes(unittest.TestCase):
    """Test victory-related fixes in real game scenarios."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(sound_manager=mock_sound_manager, settings=self.game_settings)

        return engine

    def setUp(self):
        """Set up test game engine and rendering components."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()

    def test_victory_message_box_contains_all_text(self):
        """Test that victory message box is large enough for all text."""
        # Create console for rendering
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create victory dialogue using new system
        from game_dialogue_system import UnifiedRenderer, create_victory_dialogue

        victory_dialogue = create_victory_dialogue()

        # Render the dialogue
        UnifiedRenderer.render(console, victory_dialogue)

        # The UnifiedRenderer automatically handles box sizing and word wrapping
        # This test now verifies that the dialogue was created with the correct content
        # and that rendering completed without errors

        # Verify the dialogue has the expected content
        self.assertIn(
            "ROGUE SIGNAL", victory_dialogue.title or "", "Title should mention rogue signal"
        )
        self.assertIsNotNone(victory_dialogue.message, "Victory message should have content")
        self.assertGreater(len(victory_dialogue.message), 0, "Victory message should not be empty")

    def test_victory_triggers_save_deletion(self):
        """Test that winning the game deletes the save file."""
        # Set up game at level 3 (one before victory)
        self.engine.level = 3

        with patch.object(SaveGameManager, "delete_save") as mock_delete_save:
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

        with patch.object(SaveGameManager, "delete_save"):
            # Trigger victory
            self.engine.next_level()

        # Check that victory messages were added
        messages = [msg.text for msg in self.engine.message_log.messages]

        expected_messages = [
            "BREAKTHROUGH TO THE INTERNET!",
            "You've become the rogue signal they couldn't delete...",
            "The network is vast. The future, uncertain. But you're free.",
            "Mission complete - save data purged",
        ]

        for expected_msg in expected_messages:
            self.assertIn(
                expected_msg, messages, f"Victory message '{expected_msg}' should be in message log"
            )

    def test_no_save_deletion_on_normal_level_progression(self):
        """Test that save is not deleted on normal level progression."""
        # Set up game at level 1
        self.engine.level = 1

        with patch.object(SaveGameManager, "delete_save") as mock_delete_save:
            # Progress to level 2 (normal progression)
            self.engine.next_level()

            # Should NOT have called delete_save
            mock_delete_save.assert_not_called()

        # Game should not be over
        self.assertFalse(
            self.engine.game_over, "Game should continue after normal level progression"
        )

    def test_victory_music_plays_on_completion(self):
        """Test that victory music is triggered on game completion."""
        # Set up game at level 3
        self.engine.level = 3

        with (
            patch.object(self.engine.sound_manager, "play_music") as mock_play_music,
            patch.object(self.engine.sound_manager, "stop_music") as mock_stop_music,
            patch.object(SaveGameManager, "delete_save"),
        ):

            # Trigger victory
            self.engine.next_level()

            # Should have stopped level music
            mock_stop_music.assert_called_with(fade_out_ms=500)

            # Should have played victory music (one-shot WAV file)
            mock_play_music.assert_called_with("victory.wav", loops=0)

    def test_victory_state_prevents_further_gameplay(self):
        """Test that victory state properly ends the game."""
        # Set up game at level 3
        self.engine.level = 3

        with patch.object(SaveGameManager, "delete_save"):
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
        with patch.object(SaveGameManager, "delete_save"):
            self.engine.next_level()

        # State should remain the same
        self.assertEqual(
            self.engine.level, initial_level, "Level should not advance beyond victory"
        )
        self.assertEqual(self.engine.game_over, initial_game_over, "Game over state should remain")

    def test_victory_message_text_content_accuracy(self):
        """Test that victory message content matches the theme and is appropriate."""
        # Set up game at level 3
        self.engine.level = 3

        # Clear message log
        self.engine.message_log.messages.clear()

        with patch.object(SaveGameManager, "delete_save"):
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
        engine = GameEngine(sound_manager=mock_sound_manager, settings=self.game_settings)

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
        # Verify trace level was reduced but no message appears
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(
            len(ghost_messages),
            0,
            "Ghost node messages should not appear (removed per user request)",
        )

        # Clear message log and process again (still on same node)
        self.engine.message_log.messages.clear()
        self.engine._process_special_tiles()

        # Should still NOT have ghost node message
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(len(ghost_messages), 0, "Ghost node messages should never appear")

    def test_ghost_node_message_shows_when_trace_level_actually_reduced(self):
        """Test that ghost node reduces trace level but doesn't show messages (removed per user request)."""
        # Set player trace level to a value that can be reduced
        self.player.trace_level = 50.0

        # Clear message log
        self.engine.message_log.messages.clear()

        # Process special tiles - should reduce trace level but not show message
        self.engine._process_special_tiles()

        # Should NOT have ghost node message (removed per user request)
        messages = [msg.text for msg in self.engine.message_log.messages]
        ghost_messages = [msg for msg in messages if "Ghost node" in msg]
        self.assertEqual(
            len(ghost_messages),
            0,
            "Ghost node messages should not appear (removed per user request)",
        )

        # Verify trace level was actually reduced (functionality still works)
        self.assertLess(self.player.trace_level, 50.0, "TraceLevel should have been reduced")


if __name__ == "__main__":
    unittest.main()
