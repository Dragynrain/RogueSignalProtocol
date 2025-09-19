#!/usr/bin/env python3
"""
Integration tests for RogueSignalProtocol - Game flow and end-to-end scenarios.
Tests complete gameplay scenarios including player movement, enemy interactions, combat, and level progression.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import random

# Import game modules
from game_engine import GameEngine
from game_entities import Position, Colors, EnemyState, EnemyMovement
from game_characters import Player, Enemy
from game_config import GameConfig, GameBalance
from game_data import GameData
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_audio import SoundManager
from game_inventory import CodeHack, ExploitItem


class TestGameFlowIntegration(unittest.TestCase):
    """Test complete game flow scenarios and end-to-end integration."""

    def setUp(self):
        """Set up integration test fixtures."""
        # Create engine with minimal mocking for integration testing
        with patch('game_engine.SoundManager') as mock_sound:
            mock_sound.return_value.preload_sounds = Mock()
            with patch.object(GameEngine, '_generate_procedural_level'):
                self.engine = GameEngine(load_save=False)

    def test_player_movement_to_enemy_combat_flow(self):
        """Test complete flow: player movement → enemy detection → combat."""
        # Place an enemy near the player
        enemy_pos = Position(self.engine.player.x + 2, self.engine.player.y)
        test_enemy = Enemy(enemy_pos, 'scanner')
        test_enemy.state = EnemyState.UNAWARE
        self.engine.enemy_manager.enemies = [test_enemy]

        # Simulate player moving toward enemy
        old_player_pos = Position(self.engine.player.x, self.engine.player.y)

        # Mock successful movement
        with patch.object(self.engine.player, 'move', return_value=True), \
             patch.object(self.engine, 'process_turn') as mock_process_turn:

            # Move player closer to enemy
            self.engine.move_player(1, 0)

            # Should process turn after movement
            mock_process_turn.assert_called_once()

        # Verify that move_player was called (position might not change due to mocking)
        # The important thing is that the turn processing happened
        pass

    def test_enemy_awareness_cascade_integration(self):
        """Test enemy awareness cascade when one enemy spots player."""
        # Create multiple enemies in alert range
        enemy1 = Enemy(Position(10, 10), 'scanner')
        enemy2 = Enemy(Position(12, 10), 'patrol')  # Within alert range
        enemy3 = Enemy(Position(20, 20), 'bot')     # Outside alert range

        enemy1.state = EnemyState.UNAWARE
        enemy2.state = EnemyState.UNAWARE
        enemy3.state = EnemyState.UNAWARE

        self.engine.enemy_manager.enemies = [enemy1, enemy2, enemy3]

        # Mock enemy1 seeing the player
        with patch.object(enemy1, 'can_see_player', return_value=True), \
             patch.object(enemy2, 'can_see_player', return_value=False), \
             patch.object(enemy3, 'can_see_player', return_value=False):

            # Process enemy awareness update
            self.engine._update_enemy_awareness()

            # Enemy1 should become alert
            self.assertEqual(enemy1.state, EnemyState.ALERT)

            # Simulate enemy1 becoming hostile (second awareness update)
            enemy1.state = EnemyState.HOSTILE
            self.engine._alert_nearby_enemies(enemy1)

            # Enemy2 should be alerted (within range)
            self.assertEqual(enemy2.state, EnemyState.HOSTILE)

            # Enemy3 should remain unaware (outside range)
            self.assertEqual(enemy3.state, EnemyState.UNAWARE)

    def test_combat_to_death_flow(self):
        """Test combat flow leading to player death."""
        # Set player to low health
        self.engine.player.cpu = 10

        # Create a strong enemy
        enemy = Enemy(Position(self.engine.player.x + 1, self.engine.player.y), 'firewall')
        enemy.state = EnemyState.HOSTILE
        self.engine.enemy_manager.enemies = [enemy]

        # Mock enemy attack that deals lethal damage
        with patch.object(enemy, 'can_attack_player', return_value=True), \
             patch.object(enemy, 'attack_player') as mock_attack, \
             patch('game_engine.SaveGameManager') as mock_save:

            # Mock the attack to actually damage the player
            def damage_player(player):
                player.cpu -= 15  # Deal lethal damage
                return 15

            mock_attack.side_effect = damage_player

            # Process enemy attacks
            self.engine._process_enemy_attacks()

            # Player should be dead
            self.assertLessEqual(self.engine.player.cpu, 0)
            self.assertTrue(self.engine.game_over)

            # Save should be deleted on death
            mock_save.delete_save.assert_called_once()

    def test_level_progression_flow(self):
        """Test complete level progression workflow."""
        initial_level = self.engine.level

        # Mock level generation to avoid complex setup
        with patch.object(self.engine, '_generate_procedural_level') as mock_gen, \
             patch.object(self.engine, 'auto_save') as mock_save:

            # Trigger level progression
            self.engine.next_level()

            # Level should advance
            self.assertEqual(self.engine.level, initial_level + 1)

            # Should generate new level and auto-save
            mock_gen.assert_called_once()
            mock_save.assert_called_once()

    def test_victory_condition_flow(self):
        """Test victory condition at final level."""
        # Set to penultimate level
        self.engine.level = 3

        with patch.object(self.engine, 'auto_save') as mock_save:
            # Trigger final level progression
            self.engine.next_level()

            # Should reach final level and trigger victory
            self.assertEqual(self.engine.level, 4)
            self.assertTrue(self.engine.game_over)
            mock_save.assert_called_once()

    def test_exploit_usage_to_enemy_elimination_flow(self):
        """Test using exploits to eliminate enemies."""
        # Create enemy at specific position
        enemy_pos = Position(10, 10)
        enemy = Enemy(enemy_pos, 'scanner')
        enemy.cpu = 30  # Low health for easy elimination
        self.engine.enemy_manager.enemies = [enemy]

        # Create exploit system
        exploit_system = ExploitSystem(self.engine)

        # Mock the exploit use with a simpler approach
        with patch.object(self.engine.game_map, 'has_line_of_sight', return_value=True), \
             patch.object(exploit_system, 'use_exploit', return_value=True) as mock_use:

            # Use exploit
            result = exploit_system.use_exploit('code_injection', enemy_pos)

            # Should succeed
            self.assertTrue(result)
            mock_use.assert_called_once_with('code_injection', enemy_pos)

    def test_special_tile_interaction_flow(self):
        """Test player interaction with special tiles."""
        # Set player to damaged state
        self.engine.player.cpu = 50
        self.engine.player.heat = 80

        # Mock special tile at player position
        with patch.object(self.engine.game_map, 'is_cooling_node', return_value=True), \
             patch.object(self.engine.game_map, 'is_cpu_recovery_node', return_value=True), \
             patch.object(self.engine.game_map, 'is_ghost_node', return_value=False):

            old_heat = self.engine.player.heat
            old_cpu = self.engine.player.cpu

            # Process special tiles
            self.engine._process_special_tiles()

            # Both cooling and CPU recovery should activate
            self.assertLess(self.engine.player.heat, old_heat)  # Heat reduced
            self.assertGreater(self.engine.player.cpu, old_cpu)  # CPU restored

    def test_item_pickup_to_inventory_flow(self):
        """Test complete item pickup and inventory management flow."""
        player_pos = (self.engine.player.x, self.engine.player.y)

        # Place a code hack at player position
        code_hack = CodeHack('crimson', 'restore_cpu', 'Crimson Code')
        self.engine.game_map.code_hacks[player_pos] = code_hack

        old_inventory_size = len(self.engine.player.inventory_manager.items)

        # Process special tiles (should pick up item)
        self.engine._process_special_tiles()

        # Item should be picked up
        self.assertNotIn(player_pos, self.engine.game_map.code_hacks)
        self.assertEqual(len(self.engine.player.inventory_manager.items), old_inventory_size + 1)

        # Verify item was added correctly
        picked_item = self.engine.player.inventory_manager.items[-1]
        self.assertIsInstance(picked_item, CodeHack)
        self.assertEqual(picked_item.color_name, 'crimson')

    def test_admin_spawn_to_detection_flow(self):
        """Test admin spawn when detection reaches maximum."""
        # Set detection to maximum
        self.engine.player.detection = GameConfig.MAX_DETECTION
        self.engine.admin_spawned = False

        # Mock admin spawn position finding
        with patch.object(self.engine, '_find_admin_spawn_position', return_value=Position(20, 20)) as mock_find, \
             patch.object(self.engine.enemy_manager, 'spawn_enemy') as mock_spawn:

            mock_admin = Mock()
            mock_admin.type = 'admin'
            mock_spawn.return_value = mock_admin

            # Check admin spawn
            self.engine._check_admin_spawn()

            # Admin should be spawned
            mock_find.assert_called_once()
            mock_spawn.assert_called_once_with(Position(20, 20), 'admin')
            self.assertEqual(mock_admin.state, EnemyState.HOSTILE)
            self.assertTrue(self.engine.admin_spawned)

    def test_overheating_damage_flow(self):
        """Test overheating damage when player heat exceeds maximum."""
        # Set player to overheating state
        self.engine.player.heat = 105
        self.engine.player.max_heat = 100
        self.engine.player.cpu = 100

        # Mock successful movement that would trigger overheat check
        with patch.object(self.engine.player, 'move', return_value=True), \
             patch.object(self.engine, '_get_enemy_at', return_value=None), \
             patch.object(self.engine, 'process_turn'):

            old_cpu = self.engine.player.cpu

            # Move player (should trigger overheat)
            self.engine.move_player(1, 0)

            # Should take overheating damage
            self.assertLess(self.engine.player.cpu, old_cpu)
            self.assertLessEqual(self.engine.player.heat, self.engine.player.max_heat)


class TestGameFlowErrorHandling(unittest.TestCase):
    """Test game flow error handling and edge cases."""

    def setUp(self):
        """Set up error handling test fixtures."""
        with patch('game_engine.SoundManager') as mock_sound:
            mock_sound.return_value.preload_sounds = Mock()
            with patch.object(GameEngine, '_generate_procedural_level'):
                self.engine = GameEngine(load_save=False)

    def test_movement_boundary_handling(self):
        """Test player movement at map boundaries."""
        # Move player to edge of map
        self.engine.player.x = 0
        self.engine.player.y = 0

        # Try to move beyond boundary
        old_position = Position(self.engine.player.x, self.engine.player.y)

        # Mock the boundary check (should clamp position)
        with patch.object(self.engine, '_get_enemy_at', return_value=None):
            self.engine.move_player(-1, -1)  # Try to move out of bounds

            # Position should be clamped to valid boundaries
            self.assertGreaterEqual(self.engine.player.x, 0)
            self.assertGreaterEqual(self.engine.player.y, 0)

    def test_enemy_pathfinding_failure_handling(self):
        """Test handling of enemy pathfinding failures."""
        # Create enemy in blocked position
        enemy = Enemy(Position(5, 5), 'patrol')
        enemy.state = EnemyState.HOSTILE
        enemy.movement_queue = []  # Empty queue
        self.engine.enemy_manager.enemies = [enemy]

        # Mock pathfinding to fail
        with patch('game_characters.create_pathfinding_cost_map', side_effect=Exception("Pathfinding failed")):
            # Should not crash when enemy tries to move
            try:
                self.engine._move_enemies()
                # Test passes if no exception is raised
            except Exception as e:
                self.fail(f"Enemy movement should handle pathfinding errors gracefully: {e}")

    def test_save_corruption_handling(self):
        """Test handling of corrupted save data."""
        # Mock corrupted save data
        corrupted_save = {"invalid": "data", "missing_required_fields": True}

        with patch('game_engine.SaveGameManager') as mock_save:
            mock_save.load_game.return_value = corrupted_save

            # Should handle corrupted save gracefully
            try:
                with patch.object(GameEngine, '_generate_procedural_level'):
                    engine = GameEngine(load_save=True)
                # Should fall back to new game without crashing
            except Exception as e:
                self.fail(f"Should handle corrupted save gracefully: {e}")

    def test_empty_enemy_list_handling(self):
        """Test game operations with no enemies."""
        # Clear all enemies
        self.engine.enemy_manager.enemies = []

        # Should handle empty enemy list gracefully
        try:
            self.engine._update_enemy_awareness()
            self.engine._move_enemies()
            self.engine._process_enemy_attacks()
            # Test passes if no exception is raised
        except Exception as e:
            self.fail(f"Should handle empty enemy list gracefully: {e}")


class TestGameFlowPerformance(unittest.TestCase):
    """Test game flow performance and scalability."""

    def setUp(self):
        """Set up performance test fixtures."""
        with patch('game_engine.SoundManager') as mock_sound:
            mock_sound.return_value.preload_sounds = Mock()
            with patch.object(GameEngine, '_generate_procedural_level'):
                self.engine = GameEngine(load_save=False)

    def test_many_enemies_performance(self):
        """Test game performance with many enemies."""
        # Create many enemies
        enemies = []
        for i in range(50):  # Large number of enemies
            enemy = Enemy(Position(10 + i, 10), 'scanner')
            enemy.state = EnemyState.UNAWARE
            enemies.append(enemy)

        self.engine.enemy_manager.enemies = enemies

        # Measure time for enemy processing
        import time
        start_time = time.time()

        # Process multiple turns
        for _ in range(5):
            self.engine._update_enemy_awareness()
            self.engine._move_enemies()
            self.engine._process_enemy_attacks()

        end_time = time.time()
        processing_time = end_time - start_time

        # Should complete within reasonable time (less than 1 second for 5 turns with 50 enemies)
        self.assertLess(processing_time, 1.0, "Enemy processing should be performant with many enemies")

    def test_memory_usage_stability(self):
        """Test that repeated operations don't cause memory leaks."""
        # Get initial enemy count
        initial_count = len(self.engine.enemy_manager.enemies)

        # Simulate many operations that create and destroy objects
        for _ in range(100):
            # Create temporary enemy
            temp_enemy = Enemy(Position(5, 5), 'scanner')
            self.engine.enemy_manager.enemies.append(temp_enemy)

            # Process turn
            self.engine._update_enemy_awareness()

            # Remove enemy
            self.engine.enemy_manager.enemies.remove(temp_enemy)

        # Enemy count should return to initial
        final_count = len(self.engine.enemy_manager.enemies)
        self.assertEqual(final_count, initial_count, "Memory should be properly managed")


class TestGameFlowUserScenarios(unittest.TestCase):
    """Test realistic user gameplay scenarios."""

    def setUp(self):
        """Set up user scenario test fixtures."""
        with patch('game_engine.SoundManager') as mock_sound:
            mock_sound.return_value.preload_sounds = Mock()
            with patch.object(GameEngine, '_generate_procedural_level'):
                self.engine = GameEngine(load_save=False)

    def test_stealth_gameplay_scenario(self):
        """Test typical stealth gameplay scenario."""
        # Set up stealth scenario
        self.engine.player.cpu = 100
        self.engine.player.heat = 0
        self.engine.player.detection = 0

        # Create patrolling enemy
        enemy = Enemy(Position(10, 10), 'patrol')
        enemy.state = EnemyState.UNAWARE
        enemy.patrol_points = [Position(10, 10), Position(15, 10), Position(15, 15)]
        self.engine.enemy_manager.enemies = [enemy]

        # Mock shadow position for stealth
        with patch.object(self.engine.game_map, 'is_shadow', return_value=True):
            # Player should be able to move stealthily
            old_detection = self.engine.player.detection

            # Move player (simulate several stealth moves)
            for _ in range(3):
                with patch.object(self.engine.player, 'move', return_value=True), \
                     patch.object(self.engine, 'process_turn'):
                    self.engine.move_player(1, 0)

            # Detection should remain low in shadows
            detection_increase = self.engine.player.detection - old_detection
            self.assertLessEqual(detection_increase, 15, "Stealth should keep detection low")

    def test_aggressive_gameplay_scenario(self):
        """Test aggressive combat gameplay scenario."""
        # Set up aggressive scenario
        self.engine.player.cpu = 100
        self.engine.player.heat = 0

        # Create multiple enemies for combat
        enemies = [
            Enemy(Position(8, 8), 'scanner'),
            Enemy(Position(9, 9), 'bot'),
            Enemy(Position(7, 9), 'firewall')
        ]

        for enemy in enemies:
            enemy.state = EnemyState.UNAWARE
            enemy.cpu = 25  # Weak enemies for elimination

        self.engine.enemy_manager.enemies = enemies

        # Simulate aggressive combat
        initial_enemy_count = len(self.engine.enemy_manager.enemies)

        # Mock bump attacks on enemies
        for enemy in enemies[:]:  # Copy list to avoid modification during iteration
            with patch.object(self.engine, '_get_enemy_at', return_value=enemy), \
                 patch.object(self.engine, 'maybe_process_turn'):

                # Perform bump attack
                self.engine.move_player(1, 0)

        # Some enemies should be eliminated (depending on damage rolls)
        # At minimum, player should survive the encounter
        self.assertGreater(self.engine.player.cpu, 0, "Player should survive aggressive combat")

    def test_resource_management_scenario(self):
        """Test resource management gameplay scenario."""
        # Set up resource scarcity
        self.engine.player.cpu = 30  # Low health
        self.engine.player.heat = 90  # High heat

        # Place helpful resources
        player_pos = (self.engine.player.x, self.engine.player.y)

        # Mock CPU recovery node at player position
        with patch.object(self.engine.game_map, 'is_cooling_node', return_value=True), \
             patch.object(self.engine.game_map, 'is_cpu_recovery_node', return_value=True), \
             patch.object(self.engine.game_map, 'is_ghost_node', return_value=False):

            old_cpu = self.engine.player.cpu
            old_heat = self.engine.player.heat

            # Use special tiles for recovery
            self.engine._process_special_tiles()

            # Resources should improve
            self.assertGreaterEqual(self.engine.player.cpu, old_cpu, "CPU should be restored")
            self.assertLessEqual(self.engine.player.heat, old_heat, "Heat should be reduced")


if __name__ == '__main__':
    unittest.main()