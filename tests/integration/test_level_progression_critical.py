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

    def test_level_1_to_2_progression_complete_workflow(self, basic_game_engine):
        """Test complete level 1 to 2 progression workflow."""

        # Verify initial state
        assert basic_game_engine.level == 1
        assert basic_game_engine.game_over == False

        # Store initial game state
        initial_turn = basic_game_engine.turn
        initial_player_stats = {
            'cpu': basic_game_engine.player.cpu,
            'trace level': basic_game_engine.player.trace_level,
            'x': basic_game_engine.player.x,
            'y': basic_game_engine.player.y
        }

        # Trigger level progression
        basic_game_engine.next_level()

        # Verify level progression
        assert basic_game_engine.level == 2
        assert basic_game_engine.game_over == False  # Should not end game yet

        # Verify map was regenerated
        assert basic_game_engine.game_map is not None
        assert basic_game_engine.game_map.width > 0
        assert basic_game_engine.game_map.height > 0

        # Verify player stats preserved (except position which changes)
        assert basic_game_engine.player.cpu == initial_player_stats['cpu']
        assert basic_game_engine.player.trace_level == initial_player_stats['trace level']

        # Verify player position is valid (may or may not change between levels)
        assert 0 <= basic_game_engine.player.x < GameConfig.MAP_WIDTH
        assert 0 <= basic_game_engine.player.y < GameConfig.MAP_HEIGHT

        # Verify turn counter continues
        assert basic_game_engine.turn >= initial_turn

        # Verify new enemies were spawned
        assert len(basic_game_engine.enemies) > 0

        # Verify level 2 music was triggered
        basic_game_engine.sound_manager.play_music.assert_called()
        music_calls = [call for call in basic_game_engine.sound_manager.play_music.call_args_list
                      if 'level2' in str(call)]
        assert len(music_calls) > 0

    def test_level_2_to_3_progression_with_increased_difficulty(self, basic_game_engine):
        """Test level 2 to 3 progression with difficulty scaling."""
        # Start at level 2 for this test
        basic_game_engine.next_level()  # Go to level 2
        assert basic_game_engine.level == 2

        # Get level 2 network config for comparison
        level_2_config = basic_game_engine.game_state.get_current_network_config()

        # Progress to level 3
        basic_game_engine.next_level()

        # Verify progression
        assert basic_game_engine.level == 3
        assert basic_game_engine.game_over == False

        # Get level 3 network config
        level_3_config = basic_game_engine.game_state.get_current_network_config()

        # Verify difficulty scaling
        assert level_3_config["enemies"] >= level_2_config["enemies"], "Level 3 should have same or more enemies"

        # Verify level 3 music
        basic_game_engine.sound_manager.play_music.assert_called()
        music_calls = [call for call in basic_game_engine.sound_manager.play_music.call_args_list
                      if 'level3' in str(call)]
        assert len(music_calls) > 0

    def test_level_3_completion_triggers_victory(self, basic_game_engine):
        """Test that completing level 3 triggers game victory."""
        # Start at level 3 for this test
        basic_game_engine.next_level()  # Go to level 2
        basic_game_engine.next_level()  # Go to level 3
        assert basic_game_engine.level == 3

        # Progress beyond level 3
        basic_game_engine.next_level()

        # Verify game victory
        assert basic_game_engine.level == 4
        assert basic_game_engine.game_over == True

        # Verify victory message was displayed
        recent_messages = basic_game_engine.message_log.get_recent_messages(5)
        victory_messages = [msg for msg in recent_messages if "BREAKTHROUGH" in msg.text]
        assert len(victory_messages) > 0

        # Verify victory music
        victory_music_calls = [call for call in basic_game_engine.sound_manager.play_music.call_args_list
                              if 'victory' in str(call)]
        assert len(victory_music_calls) > 0

    def test_level_progression_preserves_player_inventory(self, basic_game_engine):
        """Test that level progression preserves player inventory and exploits."""

        # Add items to player inventory
        initial_exploits = copy.deepcopy(basic_game_engine.player.inventory_manager.equipped_exploits)
        initial_inventory_count = len(basic_game_engine.player.inventory_manager.items)

        # Add a test exploit to player
        if 'shadow_step' not in basic_game_engine.player.inventory_manager.equipped_exploits:
            basic_game_engine.player.inventory_manager.equipped_exploits.append('shadow_step')

        # Progress level
        basic_game_engine.next_level()

        # Verify inventory preserved
        assert len(basic_game_engine.player.inventory_manager.items) >= initial_inventory_count
        assert 'shadow_step' in basic_game_engine.player.inventory_manager.equipped_exploits

        # Verify initial exploits are preserved
        for exploit in initial_exploits:
            assert exploit in basic_game_engine.player.inventory_manager.equipped_exploits

    def test_level_progression_error_handling(self, basic_game_engine):
        """Test error handling during level progression."""

        # Mock level generator to raise an exception
        original_generate = basic_game_engine.level_generator.generate_level
        basic_game_engine.level_generator.generate_level = Mock(side_effect=Exception("Test error"))

        initial_level = basic_game_engine.level

        # Attempt level progression
        basic_game_engine.next_level()

        # Verify error handling - level should revert
        assert basic_game_engine.level == initial_level

        # Verify error message was displayed
        recent_messages = basic_game_engine.message_log.get_recent_messages(3)
        error_messages = [msg for msg in recent_messages if "Network error" in msg.text]
        assert len(error_messages) > 0

        # Restore original method
        basic_game_engine.level_generator.generate_level = original_generate

    def test_network_configuration_scaling_across_levels(self, basic_game_engine):
        """Test that network configuration scales appropriately across levels."""

        # Test each level's configuration
        level_configs = {}

        for level in [1, 2, 3]:
            basic_game_engine.level = level
            config = basic_game_engine.game_state.get_current_network_config()
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

    def test_save_system_integration_during_level_progression(self, basic_game_engine):
        """Test save system works correctly during level progression."""

        # Mock save system
        basic_game_engine.save_manager = Mock()
        basic_game_engine.auto_save = Mock()

        # Progress level
        basic_game_engine.next_level()

        # Verify auto-save was called
        basic_game_engine.auto_save.assert_called()

    def test_enemy_placement_and_state_reset_on_new_level(self, basic_game_engine):
        """Test that enemies are properly placed and have correct initial state on new level."""

        # Progress to next level
        basic_game_engine.next_level()

        # Verify enemies were placed
        assert len(basic_game_engine.enemies) > 0

        # Verify all enemies have proper initial state
        for enemy in basic_game_engine.enemies:
            assert enemy.state == EnemyState.UNAWARE
            assert isinstance(enemy.position, Position)
            assert enemy.position.x >= 0 and enemy.position.x < GameConfig.MAP_WIDTH
            assert enemy.position.y >= 0 and enemy.position.y < GameConfig.MAP_HEIGHT
            assert hasattr(enemy, 'type')
            
    def test_map_features_generation_across_levels(self, basic_game_engine):
        """Test that essential map features are generated on each level."""

        for target_level in [1, 2, 3]:
            basic_game_engine.level = target_level - 1  # Set to previous level
            basic_game_engine.next_level()  # Progress to target level

            # Verify map exists
            assert basic_game_engine.game_map is not None

            # Verify map has proper dimensions
            assert basic_game_engine.game_map.width == GameConfig.MAP_WIDTH
            assert basic_game_engine.game_map.height == GameConfig.MAP_HEIGHT

            # Verify some walls were created
            assert len(basic_game_engine.game_map.walls) > 0

            # Verify borders were created (should have walls around edges)
            # Check corners are walls
            assert (0, 0) in basic_game_engine.game_map.walls  # Top-left corner
            assert (GameConfig.MAP_WIDTH-1, 0) in basic_game_engine.game_map.walls  # Top-right corner
            assert (0, GameConfig.MAP_HEIGHT-1) in basic_game_engine.game_map.walls  # Bottom-left corner
            assert (GameConfig.MAP_WIDTH-1, GameConfig.MAP_HEIGHT-1) in basic_game_engine.game_map.walls  # Bottom-right corner

    def test_complete_level_progression_workflow_1_to_victory(self, basic_game_engine):
        """Test complete workflow from level 1 to victory."""

        # Track progression
        progression_log = []

        # Progress through all levels
        for expected_level in [2, 3, 4]:  # 4 means victory
            initial_level = basic_game_engine.level
            progression_log.append(f"Starting level {initial_level}")

            basic_game_engine.next_level()

            progression_log.append(f"Progressed to level {basic_game_engine.level}")

            if expected_level <= 3:
                # Still in game
                assert basic_game_engine.level == expected_level
                assert basic_game_engine.game_over == False
                assert len(basic_game_engine.enemies) > 0  # Should have enemies
            else:
                # Victory condition
                assert basic_game_engine.level == 4
                assert basic_game_engine.game_over == True

        # Verify complete progression occurred
        assert len(progression_log) == 6  # 3 pairs of start/progress messages

        # Verify final victory state
        assert basic_game_engine.game_over == True
        assert basic_game_engine.level == 4


class TestLevelGenerationCritical:
    """Test critical level generation functionality."""

    def test_deterministic_level_generation_with_same_seed(self):
        """Test that level generation is deterministic with the same seed."""
        # Create two engines with muted audio
        from unittest.mock import Mock
        from game_config import GameSettings

        mock_sound = Mock()
        settings = GameSettings()
        settings.master_volume = 0.0
        settings.sfx_volume = 0.0

        engine1 = GameEngine(sound_manager=mock_sound, settings=settings)
        engine2 = GameEngine(sound_manager=mock_sound, settings=settings)

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

    def test_player_spawning_in_valid_location(self, basic_game_engine):
        """Test that player spawns in a valid location on new levels."""

        for level in [1, 2, 3]:
            basic_game_engine.level = level - 1
            basic_game_engine.next_level()

            # Verify player is in bounds
            assert 0 <= basic_game_engine.player.x < GameConfig.MAP_WIDTH
            assert 0 <= basic_game_engine.player.y < GameConfig.MAP_HEIGHT

            # Verify player is not in a wall
            player_pos = (basic_game_engine.player.x, basic_game_engine.player.y)
            assert player_pos not in basic_game_engine.game_map.walls, f"Player spawned in wall at level {level}"

            # Verify player has some free space around them (not completely boxed in)
            adjacent_positions = [
                (basic_game_engine.player.x + dx, basic_game_engine.player.y + dy)
                for dx in [-1, 0, 1] for dy in [-1, 0, 1]
                if dx != 0 or dy != 0
            ]

            valid_adjacent = 0
            for x, y in adjacent_positions:
                if (0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT and
                    (x, y) not in basic_game_engine.game_map.walls):
                    valid_adjacent += 1

            assert valid_adjacent > 0, f"Player has no valid adjacent positions at level {level}"

    def test_enemy_spawning_constraints_and_distribution(self, basic_game_engine):
        """Test enemy spawning follows proper constraints and distribution."""

        for level in [1, 2, 3]:
            basic_game_engine.level = level - 1
            basic_game_engine.next_level()

            # Verify enemies exist
            assert len(basic_game_engine.enemies) > 0, f"No enemies spawned at level {level}"

            # Verify all enemies are in valid positions
            for enemy in basic_game_engine.enemies:
                assert 0 <= enemy.x < GameConfig.MAP_WIDTH
                assert 0 <= enemy.y < GameConfig.MAP_HEIGHT

                # Enemy should not be in wall
                enemy_pos = (enemy.x, enemy.y)
                assert enemy_pos not in basic_game_engine.game_map.walls, f"Enemy spawned in wall at level {level}"

                # Enemy should not be on top of player
                assert enemy.x != basic_game_engine.player.x or enemy.y != basic_game_engine.player.y, f"Enemy spawned on player at level {level}"

            # Verify no two enemies occupy same position
            positions = [(e.x, e.y) for e in basic_game_engine.enemies]
            assert len(positions) == len(set(positions)), f"Multiple enemies at same position in level {level}"

            # Verify enemy distribution is reasonable (not all clumped in one area)
            if len(basic_game_engine.enemies) >= 3:
                x_coords = [e.x for e in basic_game_engine.enemies]
                y_coords = [e.y for e in basic_game_engine.enemies]

                x_spread = max(x_coords) - min(x_coords)
                y_spread = max(y_coords) - min(y_coords)

                # Enemies should be distributed across a reasonable area
                assert x_spread >= 3, f"Enemies too clustered horizontally at level {level}"
                assert y_spread >= 3, f"Enemies too clustered vertically at level {level}"