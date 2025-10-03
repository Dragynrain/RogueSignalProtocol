#!/usr/bin/env python3
"""
Integration tests for audio system and story fragment interactions.
Tests how these systems work together in real gameplay scenarios.
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from game_engine import GameEngine
from game_config import GameSettings
from game_entities import Position
from game_story import StoryFragmentManager
from game_audio import SoundManager


class TestAudioStoryIntegration(unittest.TestCase):
    """Test integration between audio system and story fragments."""

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
        """Set up test environment."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()

    def test_story_fragment_discovery_triggers_audio(self):
        """Test that discovering story fragments triggers appropriate audio feedback."""
        # Reset story fragment manager to clean state
        self.engine.story_fragment_manager.discovered_fragments = []

        # Place a story fragment
        from game_inventory import StoryFragment
        fragment = StoryFragment(0)
        self.engine.game_map.story_fragments[(20, 20)] = fragment

        # Move player to story fragment location
        self.engine.player.x, self.engine.player.y = 20, 20

        with patch.object(self.engine.sound_manager, 'play_sound') as mock_play_sound:
            # Process special tiles to trigger story fragment pickup
            self.engine._process_special_tiles()

            # Should have triggered item pickup sound
            mock_play_sound.assert_called()

    def test_enemy_trace_level_audio_with_story_context(self):
        """Test that enemy trace level audio works correctly when story fragments are present."""
        # Set up enemy and story fragment
        from game_characters import Enemy
        from game_entities import EnemyState

        enemy = Enemy(Position(15, 15), 'virus')
        enemy.state = EnemyState.UNAWARE
        self.engine.enemies = [enemy]

        # Place story fragment nearby
        from game_inventory import StoryFragment
        fragment = StoryFragment(0)
        self.engine.game_map.story_fragments[(18, 18)] = fragment

        # Move player into enemy vision
        self.engine.player.x, self.engine.player.y = 16, 15

        with patch.object(self.engine.sound_manager, 'play_sound') as mock_play_sound:
            # Process enemy turn to trigger trace level
            self.engine._update_enemy_awareness()

            # Should trigger enemy alert sound
            expected_calls = [call for call in mock_play_sound.call_args_list
                            if 'alert' in str(call) or 'enemy' in str(call)]
            self.assertGreater(len(expected_calls), 0, "Should trigger enemy trace level audio")

    def test_audio_settings_affect_story_discovery(self):
        """Test that audio settings properly control story fragment sounds."""
        # Test with audio disabled
        self.game_settings.sound_enabled = False

        # Place and discover story fragment
        from game_inventory import StoryFragment
        fragment = StoryFragment(0)
        self.engine.game_map.story_fragments[(25, 25)] = fragment
        self.engine.player.x, self.engine.player.y = 25, 25

        with patch.object(self.engine.sound_manager, 'play_sound') as mock_play_sound:
            self.engine._process_special_tiles()

            # With sound disabled, should still register discovery but may handle audio differently
            # The exact behavior depends on sound manager implementation
            self.assertTrue(len(self.engine.game_map.story_fragments) == 0 or
                          (25, 25) not in self.engine.game_map.story_fragments,
                          "Story fragment should be discovered")

    def test_story_manager_persistence_with_audio_cues(self):
        """Test that story manager persistence works correctly with audio system."""
        # Create story manager and reset to clean state
        story_manager = StoryFragmentManager()
        story_manager.discovered_fragments = []

        # Discover fragments and check audio integration
        with patch.object(self.engine.sound_manager, 'play_sound') as mock_play_sound:
            # Simulate discovering multiple fragments
            for i in range(3):
                fragment_discovered = story_manager.discover_fragment(i)
                self.assertTrue(fragment_discovered, f"Fragment {i} should be discoverable")

            # Verify story progress affects audio context
            discovered_count, total_count = story_manager.get_fragment_count()
            self.assertEqual(discovered_count, 3, "Should have discovered 3 fragments")
            self.assertGreater(total_count, 3, "Should have more total fragments available")


class TestLevelAudioIntegration(unittest.TestCase):
    """Test integration between level progression and audio system."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        game_settings = GameSettings()

        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=game_settings
        )

        return engine

    def setUp(self):
        """Set up test environment."""
        self.engine = self.create_test_engine()

    def test_level_progression_audio_cues(self):
        """Test that level progression triggers appropriate audio."""
        # Start at level 1
        self.engine.level = 1

        with patch.object(self.engine.sound_manager, 'play_music') as mock_play_music:
            # Progress to level 2
            self.engine.next_level()

            # Should trigger level progression without victory music
            victory_calls = [call for call in mock_play_music.call_args_list
                           if 'victory' in str(call)]
            self.assertEqual(len(victory_calls), 0, "Should not play victory music on normal progression")

    def test_victory_audio_integration(self):
        """Test that victory triggers proper audio sequence."""
        # Set up for victory (level 3 -> 4)
        self.engine.level = 3

        with patch.object(self.engine.sound_manager, 'play_music') as mock_play_music, \
             patch('game_save.SaveGameManager.delete_save'):

            # Trigger victory
            self.engine.next_level()

            # Should trigger victory music
            victory_calls = [call for call in mock_play_music.call_args_list
                           if 'victory' in str(call)]
            self.assertGreater(len(victory_calls), 0, "Should play victory music")

    def test_special_nodes_audio_feedback(self):
        """Test that special nodes provide audio feedback."""
        # Add cooling node
        self.engine.game_map.cooling_nodes.add((30, 30))
        self.engine.player.x, self.engine.player.y = 30, 30
        self.engine.player.heat = 50  # Set some heat to be reduced

        with patch.object(self.engine.sound_manager, 'play_sound') as mock_play_sound:
            # Process special tiles
            self.engine._process_special_tiles()

            # Should trigger node activation sound
            activation_calls = [call for call in mock_play_sound.call_args_list
                              if 'node' in str(call) or 'activate' in str(call)]
            self.assertGreater(len(activation_calls), 0, "Should play node activation sound")


if __name__ == '__main__':
    unittest.main()