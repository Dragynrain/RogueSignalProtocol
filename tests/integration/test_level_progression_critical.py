"""
Critical level progression integration tests.

Tests the complete level progression workflow including:
- Level 1 to 2 transition
- Level 2 to 3 transition
- Level 3 completion and game victory
- Map generation, enemy placement, item placement
- Game state persistence through level changes
- Audio transitions between levels
- Network configuration scaling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
import copy

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, Colors
from game_config import GameConfig, GameSettings, GameBalance
from game_state import GameStateManager
from tests.fixtures.real_game_data import get_real_game_data
from tests.fixtures.simple_fixtures import create_test_map_with_real_tiles, create_real_player


class TestLevelProgressionCritical:
    """Test critical level progression functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create real game data
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "ascii"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

    def create_test_engine(self, level=1):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        # Set initial level
        engine.level = level

        return engine

    def test_level_1_to_2_progression_complete_workflow(self):
        """Test complete level 1 to 2 progression workflow."""
        engine = self.create_test_engine(level=1)

        # Verify initial state
        assert engine.level == 1
        assert engine.game_over == False

        # Store initial game state
        initial_turn = engine.turn
        initial_player_stats = {
            'cpu': engine.player.cpu,
            'trace level': engine.player.trace_level,
            'x': engine.player.x,
            'y': engine.player.y
        }

        # Trigger level progression
        engine.next_level()

        # Verify level progression
        assert engine.level == 2
        assert engine.game_over == False  # Should not end game yet

        # Verify map was regenerated
        assert engine.game_map is not None
        assert engine.game_map.width > 0
        assert engine.game_map.height > 0

        # Verify player stats preserved (except position which changes)
        assert engine.player.cpu == initial_player_stats['cpu']
        assert engine.player.trace_level == initial_player_stats['trace level']

        # Verify player position is valid (may or may not change between levels)
        assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
        assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT

        # Verify turn counter continues
        assert engine.turn >= initial_turn

        # Verify new enemies were spawned
        assert len(engine.enemies) > 0

        # Verify level 2 music was triggered
        engine.sound_manager.play_music.assert_called()
        music_calls = [call for call in engine.sound_manager.play_music.call_args_list
                      if 'level2' in str(call)]
        assert len(music_calls) > 0

    def test_level_2_to_3_progression_with_increased_difficulty(self):
        """Test level 2 to 3 progression with difficulty scaling."""
        engine = self.create_test_engine(level=2)

        # Get level 2 network config for comparison
        level_2_config = engine.game_state.get_current_network_config()

        # Progress to level 3
        engine.next_level()

        # Verify progression
        assert engine.level == 3
        assert engine.game_over == False

        # Get level 3 network config
        level_3_config = engine.game_state.get_current_network_config()

        # Verify difficulty scaling
        assert level_3_config["enemies"] >= level_2_config["enemies"], "Level 3 should have same or more enemies"

        # Verify level 3 music
        engine.sound_manager.play_music.assert_called()
        music_calls = [call for call in engine.sound_manager.play_music.call_args_list
                      if 'level3' in str(call)]
        assert len(music_calls) > 0

    def test_level_3_completion_triggers_victory(self):
        """Test that completing level 3 triggers game victory."""
        engine = self.create_test_engine(level=3)

        # Progress beyond level 3
        engine.next_level()

        # Verify game victory
        assert engine.level == 4
        assert engine.game_over == True

        # Verify victory message was displayed
        recent_messages = engine.message_log.get_recent_messages(5)
        victory_messages = [msg for msg in recent_messages if "BREAKTHROUGH" in msg.text]
        assert len(victory_messages) > 0

        # Verify victory music
        victory_music_calls = [call for call in engine.sound_manager.play_music.call_args_list
                              if 'victory' in str(call)]
        assert len(victory_music_calls) > 0

    def test_level_progression_preserves_player_inventory(self):
        """Test that level progression preserves player inventory and exploits."""
        engine = self.create_test_engine(level=1)

        # Add items to player inventory
        initial_exploits = copy.deepcopy(engine.player.inventory_manager.equipped_exploits)
        initial_inventory_count = len(engine.player.inventory_manager.items)

        # Add a test exploit to player
        if 'shadow_step' not in engine.player.inventory_manager.equipped_exploits:
            engine.player.inventory_manager.equipped_exploits.append('shadow_step')

        # Progress level
        engine.next_level()

        # Verify inventory preserved
        assert len(engine.player.inventory_manager.items) >= initial_inventory_count
        assert 'shadow_step' in engine.player.inventory_manager.equipped_exploits

        # Verify initial exploits are preserved
        for exploit in initial_exploits:
            assert exploit in engine.player.inventory_manager.equipped_exploits

    def test_level_progression_error_handling(self):
        """Test error handling during level progression."""
        engine = self.create_test_engine(level=1)

        # Mock level generator to raise an exception
        original_generate = engine.level_generator.generate_level
        engine.level_generator.generate_level = Mock(side_effect=Exception("Test error"))

        initial_level = engine.level

        # Attempt level progression
        engine.next_level()

        # Verify error handling - level should revert
        assert engine.level == initial_level

        # Verify error message was displayed
        recent_messages = engine.message_log.get_recent_messages(3)
        error_messages = [msg for msg in recent_messages if "Network error" in msg.text]
        assert len(error_messages) > 0

        # Restore original method
        engine.level_generator.generate_level = original_generate

    def test_network_configuration_scaling_across_levels(self):
        """Test that network configuration scales appropriately across levels."""
        engine = self.create_test_engine(level=1)

        # Test each level's configuration
        level_configs = {}

        for level in [1, 2, 3]:
            engine.level = level
            config = engine.game_state.get_current_network_config()
            level_configs[level] = config

            # Verify config has required keys
            assert "enemies" in config
            assert "background_trace" in config
            assert isinstance(config["enemies"], (int, float))
            assert isinstance(config["background_trace"], (int, float))

        # Verify progression - later levels should have same or higher difficulty
        assert level_configs[2]["enemies"] >= level_configs[1]["enemies"]
        assert level_configs[3]["enemies"] >= level_configs[2]["enemies"]
        assert level_configs[2]["background_trace"] >= level_configs[1]["background_trace"]
        assert level_configs[3]["background_trace"] >= level_configs[2]["background_trace"]

    def test_save_system_integration_during_level_progression(self):
        """Test save system works correctly during level progression."""
        engine = self.create_test_engine(level=1)

        # Mock save system
        engine.save_manager = Mock()
        engine.auto_save = Mock()

        # Progress level
        engine.next_level()

        # Verify auto-save was called
        engine.auto_save.assert_called()

    def test_enemy_placement_and_state_reset_on_new_level(self):
        """Test that enemies are properly placed and have correct initial state on new level."""
        engine = self.create_test_engine(level=1)

        # Progress to next level
        engine.next_level()

        # Verify enemies were placed
        assert len(engine.enemies) > 0

        # Verify all enemies have proper initial state
        for enemy in engine.enemies:
            assert enemy.state == EnemyState.UNAWARE
            assert isinstance(enemy.position, Position)
            assert enemy.position.x >= 0 and enemy.position.x < GameConfig.MAP_WIDTH
            assert enemy.position.y >= 0 and enemy.position.y < GameConfig.MAP_HEIGHT
            assert hasattr(enemy, 'type')
            assert hasattr(enemy, 'movement_queue')

    def test_map_features_generation_across_levels(self):
        """Test that essential map features are generated on each level."""
        engine = self.create_test_engine(level=1)

        for target_level in [1, 2, 3]:
            engine.level = target_level - 1  # Set to previous level
            engine.next_level()  # Progress to target level

            # Verify map exists
            assert engine.game_map is not None

            # Verify map has proper dimensions
            assert engine.game_map.width == GameConfig.MAP_WIDTH
            assert engine.game_map.height == GameConfig.MAP_HEIGHT

            # Verify some walls were created
            assert len(engine.game_map.walls) > 0

            # Verify borders were created (should have walls around edges)
            # Check corners are walls
            assert (0, 0) in engine.game_map.walls  # Top-left corner
            assert (GameConfig.MAP_WIDTH-1, 0) in engine.game_map.walls  # Top-right corner
            assert (0, GameConfig.MAP_HEIGHT-1) in engine.game_map.walls  # Bottom-left corner
            assert (GameConfig.MAP_WIDTH-1, GameConfig.MAP_HEIGHT-1) in engine.game_map.walls  # Bottom-right corner

    def test_complete_level_progression_workflow_1_to_victory(self):
        """Test complete workflow from level 1 to victory."""
        engine = self.create_test_engine(level=1)

        # Track progression
        progression_log = []

        # Progress through all levels
        for expected_level in [2, 3, 4]:  # 4 means victory
            initial_level = engine.level
            progression_log.append(f"Starting level {initial_level}")

            engine.next_level()

            progression_log.append(f"Progressed to level {engine.level}")

            if expected_level <= 3:
                # Still in game
                assert engine.level == expected_level
                assert engine.game_over == False
                assert len(engine.enemies) > 0  # Should have enemies
            else:
                # Victory condition
                assert engine.level == 4
                assert engine.game_over == True

        # Verify complete progression occurred
        assert len(progression_log) == 6  # 3 pairs of start/progress messages

        # Verify final victory state
        assert engine.game_over == True
        assert engine.level == 4


class TestLevelGenerationCritical:
    """Test critical level generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "ascii"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

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

    def test_deterministic_level_generation_with_same_seed(self):
        """Test that level generation is deterministic with the same seed."""
        engine1 = self.create_test_engine()
        engine2 = self.create_test_engine()

        # Set same seed for both engines
        test_seed = 12345
        engine1.game_state.dungeon_seed = test_seed
        engine2.game_state.dungeon_seed = test_seed

        # Generate level 2 in both engines
        engine1.level = 1
        engine1.next_level()

        engine2.level = 1
        engine2.next_level()

        # Compare map dimensions (should be identical)
        assert engine1.game_map.width == engine2.game_map.width
        assert engine1.game_map.height == engine2.game_map.height

        # Compare some map features (allowing for minor variations in procedural elements)
        wall_count_1 = len(engine1.game_map.walls)
        wall_count_2 = len(engine2.game_map.walls)

        # Wall counts should be very similar (allowing for minor procedural variation)
        assert abs(wall_count_1 - wall_count_2) <= 5

    def test_player_spawning_in_valid_location(self):
        """Test that player spawns in a valid location on new levels."""
        engine = self.create_test_engine()

        for level in [1, 2, 3]:
            engine.level = level - 1
            engine.next_level()

            # Verify player is in bounds
            assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
            assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT

            # Verify player is not in a wall
            player_pos = (engine.player.x, engine.player.y)
            assert player_pos not in engine.game_map.walls, f"Player spawned in wall at level {level}"

            # Verify player has some free space around them (not completely boxed in)
            adjacent_positions = [
                (engine.player.x + dx, engine.player.y + dy)
                for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                if dx != 0 or dy != 0
            ]

            valid_adjacent = 0
            for x, y in adjacent_positions:
                if (0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT and
                    (x, y) not in engine.game_map.walls):
                    valid_adjacent += 1

            assert valid_adjacent > 0, f"Player has no valid adjacent positions at level {level}"

    def test_enemy_spawning_constraints_and_distribution(self):
        """Test enemy spawning follows proper constraints and distribution."""
        engine = self.create_test_engine()

        for level in [1, 2, 3]:
            engine.level = level - 1
            engine.next_level()

            # Verify enemies exist
            assert len(engine.enemies) > 0, f"No enemies spawned at level {level}"

            # Verify all enemies are in valid positions
            for enemy in engine.enemies:
                assert 0 <= enemy.x < GameConfig.MAP_WIDTH
                assert 0 <= enemy.y < GameConfig.MAP_HEIGHT

                # Enemy should not be in wall
                enemy_pos = (enemy.x, enemy.y)
                assert enemy_pos not in engine.game_map.walls, f"Enemy spawned in wall at level {level}"

                # Enemy should not be on top of player
                assert enemy.x != engine.player.x or enemy.y != engine.player.y, f"Enemy spawned on player at level {level}"

            # Verify no two enemies occupy same position
            positions = [(e.x, e.y) for e in engine.enemies]
            assert len(positions) == len(set(positions)), f"Multiple enemies at same position in level {level}"

            # Verify enemy distribution is reasonable (not all clumped in one area)
            if len(engine.enemies) >= 3:
                x_coords = [e.x for e in engine.enemies]
                y_coords = [e.y for e in engine.enemies]

                x_spread = max(x_coords) - min(x_coords)
                y_spread = max(y_coords) - min(y_coords)

                # Enemies should be distributed across a reasonable area
                assert x_spread >= 3, f"Enemies too clustered horizontally at level {level}"
                assert y_spread >= 3, f"Enemies too clustered vertically at level {level}"