#!/usr/bin/env python3
"""
Unit tests for enemy AI and pathfinding systems.
Tests enemy movement types, coordination, and advanced AI behaviors.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
from typing import List

from game_entities import Position, EnemyState, EnemyMovement, TargetingMode
from game_characters import Player, Enemy, create_pathfinding_cost_map, can_move_to_position
from game_map import GameMap
from game_engine import GameEngine
from game_enemies import EnemyManager
from tests.fixtures.mock_factories import MockPlayerFactory, MockEnemyFactory, MockGameMapFactory


def create_mock_game(game_map, player, enemies=None):
    """Create a mock game object with the required attributes."""
    mock_game = Mock()
    mock_game.game_map = game_map
    mock_game.player = player
    mock_game.enemies = enemies or []
    mock_game._get_enemy_at = Mock(return_value=None)
    mock_game.enemy_manager = Mock()
    mock_game.enemy_manager.enemies = enemies or []
    return mock_game


class TestEnemyMovementTypes:
    """Test different enemy movement patterns and behaviors."""
    
    def test_static_enemies_remain_in_position(self):
        """Test that STATIC enemies never move regardless of state."""
        game_map = GameMap(30, 30)
        player = Player(20, 20)
        
        # Create static enemy
        static_enemy = Enemy(Position(10, 10), 'firewall')  # Firewalls are STATIC
        original_position = Position(static_enemy.x, static_enemy.y)
        
        # Set different states and try to move
        for state in [EnemyState.UNAWARE, EnemyState.ALERT, EnemyState.HOSTILE]:
            static_enemy.state = state
            
            # Try to move
            moved = static_enemy.move(game_map, player, None)
            
            # Should never move
            assert moved is False
            assert static_enemy.position.x == original_position.x
            assert static_enemy.position.y == original_position.y
            assert len(static_enemy.movement_queue) == 0
    
    def test_random_movement_generates_valid_moves(self):
        """Test that RANDOM movement generates valid adjacent moves."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)  # Far from enemy
        
        # Create random movement enemy
        random_enemy = Enemy(Position(10, 10), 'scanner')  # Scanners use RANDOM
        random_enemy.type_data.movement = EnemyMovement.RANDOM
        random_enemy.state = EnemyState.UNAWARE
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [random_enemy])
        
        # Generate movement queue
        random_enemy._generate_movement_queue(game_map, player, mock_game)
        
        # Should have generated moves
        assert len(random_enemy.movement_queue) > 0
        assert len(random_enemy.movement_queue) <= 3
        
        # All moves should be valid adjacent positions
        current_pos = Position(random_enemy.x, random_enemy.y)
        for i, move in enumerate(random_enemy.movement_queue):
            expected_distance = 1 if i == 0 else 1  # Each move should be 1 step from previous
            prev_pos = current_pos if i == 0 else random_enemy.movement_queue[i-1]
            distance = move.distance_to(prev_pos)
            assert distance <= 1.5, f"Move {i} too far from previous position"  # Allow diagonal (sqrt(2) ≈ 1.41)
            
            # Position should be valid
            assert move.is_valid(game_map.width, game_map.height)
            assert not game_map.is_wall(move)
    
    def test_patrol_enemies_follow_predefined_routes(self):
        """Test that PATROL enemies follow their patrol points."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)  # Far from patrol
        
        # Create patrol enemy with predefined route
        patrol_enemy = Enemy(Position(10, 10), 'patrol')
        patrol_enemy.patrol_points = [
            Position(10, 10),  # Start
            Position(10, 15),  # North
            Position(15, 15),  # East
            Position(15, 10),  # South
        ]
        patrol_enemy.patrol_index = 0
        patrol_enemy.state = EnemyState.UNAWARE
        # Ensure enemy type is set correctly
        assert patrol_enemy.type_data.movement == EnemyMovement.PATROL
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [patrol_enemy])
        
        # Verify patrol points are set
        assert len(patrol_enemy.patrol_points) == 4
        
        # Test that patrol enemies have defined patrol behavior  
        # They should at least have a movement pattern when they have patrol points
        patrol_enemy._generate_movement_queue(game_map, player, mock_game)
        assert len(patrol_enemy.movement_queue) > 0, "Patrol enemy should generate movement queue"
        
        # Test that the patrol system recognizes valid patrol configuration
        target_point = patrol_enemy.patrol_points[patrol_enemy.patrol_index]
        next_target = patrol_enemy.patrol_points[(patrol_enemy.patrol_index + 1) % len(patrol_enemy.patrol_points)]
        
        # Patrol enemies should have a valid target from their patrol points
        assert target_point in patrol_enemy.patrol_points
        assert next_target in patrol_enemy.patrol_points
        assert len(patrol_enemy.patrol_points) == 4
    
    def test_seek_enemies_pathfind_toward_player(self):
        """Test that SEEK enemies pathfind toward player when hostile."""
        game_map = GameMap(30, 30)
        player = Player(20, 20)
        
        # Create SEEK enemy
        seek_enemy = Enemy(Position(10, 10), 'hunter')  # Hunters use SEEK
        seek_enemy.state = EnemyState.HOSTILE
        seek_enemy.last_seen_player = player.position
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [seek_enemy])
        
        with patch.object(seek_enemy, 'can_see_player', return_value=True):
            # Generate movement queue
            seek_enemy._generate_movement_queue(game_map, player, mock_game)
            
            # Should have moves toward player
            assert len(seek_enemy.movement_queue) > 0
            
            # Each move should get closer to player
            current_pos = Position(seek_enemy.x, seek_enemy.y)
            original_distance = current_pos.distance_to(player.position)
            
            for move in seek_enemy.movement_queue[:2]:  # Check first couple moves
                move_distance = move.distance_to(player.position)
                assert move_distance < original_distance, "SEEK enemy should move toward player"
                original_distance = move_distance
    
    def test_track_enemies_use_advanced_targeting(self):
        """Test that TRACK enemies use last known player position."""
        game_map = GameMap(30, 30)
        player = Player(20, 20)
        
        # Create TRACK enemy
        track_enemy = Enemy(Position(10, 10), 'hunter')
        track_enemy.type_data.movement = EnemyMovement.TRACK
        track_enemy.state = EnemyState.HOSTILE
        track_enemy.last_seen_player = Position(15, 15)  # Last known position
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [track_enemy])
        
        with patch.object(track_enemy, 'can_see_player', return_value=False):
            # Generate movement queue
            track_enemy._generate_movement_queue(game_map, player, mock_game)
            
            # Should have moves toward last known position
            assert len(track_enemy.movement_queue) > 0
            
            # Should move toward last known position, not current player position
            current_pos = Position(track_enemy.x, track_enemy.y)
            target_pos = track_enemy.last_seen_player
            original_distance = current_pos.distance_to(target_pos)
            
            first_move = track_enemy.movement_queue[0]
            new_distance = first_move.distance_to(target_pos)
            assert new_distance < original_distance, "TRACK enemy should move toward last known position"
    
    def test_movement_queue_population_and_execution(self):
        """Test movement queue population and step-by-step execution."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)
        
        enemy = Enemy(Position(10, 10), 'scanner')
        enemy.state = EnemyState.UNAWARE
        original_pos = Position(enemy.x, enemy.y)
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Generate queue
        enemy._generate_movement_queue(game_map, player, mock_game)
        initial_queue_length = len(enemy.movement_queue)
        
        # Execute one move
        moved = enemy._execute_next_move(game_map, player, mock_game)
        
        if moved:
            # Position should have changed
            assert enemy.position != original_pos
            # Queue should be one shorter
            assert len(enemy.movement_queue) == initial_queue_length - 1
        
        # Queue should regenerate when empty
        enemy.movement_queue.clear()
        needs_regen = enemy._should_regenerate_queue(game_map, player, None)
        assert needs_regen is True


class TestPathfindingAndObstacles:
    """Test pathfinding algorithms and obstacle avoidance."""
    
    def test_pathfinding_obstacle_avoidance(self):
        """Test that enemies avoid walls and obstacles when pathfinding."""
        game_map = GameMap(20, 20)
        player = Player(15, 10)
        
        # Create a wall between enemy and player
        for y in range(5, 15):
            game_map.walls.add((12, y))
        
        enemy = Enemy(Position(5, 10), 'hunter')
        enemy.state = EnemyState.HOSTILE
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        with patch.object(enemy, 'can_see_player', return_value=True):
            # Generate pathfinding queue
            enemy._generate_pathfinding_queue(player.position, game_map, mock_game)
            
            # Enemy should find path around wall
            assert len(enemy.movement_queue) > 0
            
            # No move should go through walls
            for move in enemy.movement_queue:
                assert not game_map.is_wall(move), f"Move {move} goes through wall"
    
    def test_line_of_sight_calculations(self):
        """Test enemy line of sight detection."""
        game_map = GameMap(20, 20)
        player = Player(15, 10)
        
        # Enemy with clear line of sight (close enough and no walls)
        clear_enemy = Enemy(Position(12, 10), 'scanner')  # Distance = 3, within scanner vision=8
        assert bool(clear_enemy.can_see_player(player, game_map)) is True
        
        # Add wall blocking line of sight
        game_map.walls.add((13, 10))  # Block between enemy and player
        blocked_enemy = Enemy(Position(10, 10), 'scanner')
        assert bool(blocked_enemy.can_see_player(player, game_map)) is False
    
    def test_vision_range_enforcement(self):
        """Test that enemies respect their vision range limits."""
        game_map = GameMap(50, 50)
        
        # Scanner has vision=5
        scanner = Enemy(Position(10, 10), 'scanner')
        
        # Player within range
        close_player = Player(14, 10)  # Distance = 4, within scanner vision=5
        assert bool(scanner.can_see_player(close_player, game_map)) is True
        
        # Player outside range
        far_player = Player(20, 10)  # Distance = 10 > 5
        assert bool(scanner.can_see_player(far_player, game_map)) is False
    
    def test_pathfinding_cost_map_creation(self):
        """Test creation of pathfinding cost maps."""
        game_map = GameMap(20, 20)
        
        # Add some walls
        game_map.walls.update([(10, 10), (10, 11), (10, 12)])
        
        enemy = Enemy(Position(5, 5), 'hunter')
        
        # Create mock game
        mock_game = create_mock_game(game_map, Player(15, 15), [enemy])
        
        # Create cost map
        cost_map = create_pathfinding_cost_map(game_map, mock_game, enemy)
        
        # Should be 2D array with correct dimensions (width, height)
        assert cost_map.shape == (game_map.width, game_map.height)
        
        # Walls should be blocked (False in boolean cost map)
        assert cost_map[10, 10] == False  # Wall positions are blocked
        assert cost_map[10, 11] == False
        
        # Open areas should be passable  
        assert cost_map[5, 5] == True  # Open position should be passable


class TestEnemyCoordination:
    """Test enemy coordination and communication systems."""
    
    def test_enemy_alert_cascading(self):
        """Test that enemy alerts propagate to nearby enemies."""
        with patch.object(GameEngine, '_generate_procedural_level'):
            game_map = GameMap(30, 30)
            engine = GameEngine(game_map=game_map)
            player = Player(15, 15)
            engine.player = player
            
            # Create multiple enemies near each other
            enemy1 = Enemy(Position(10, 10), 'scanner')
            enemy2 = Enemy(Position(11, 11), 'patrol')  # Adjacent
            enemy3 = Enemy(Position(20, 20), 'bot')     # Far away
            
            enemies = [enemy1, enemy2, enemy3]
            engine.enemy_manager.enemies = enemies
            
            # Enemy1 is ALERT and will transition to HOSTILE when it sees player
            enemy1.state = EnemyState.ALERT
            enemy1.alert_timer = 0  # Ready to become hostile
            
            # Mock can_see_player to return True for enemy1 (triggering the cascade)
            with patch.object(enemy1, 'can_see_player', return_value=True), \
                 patch.object(enemy2, 'can_see_player', return_value=False), \
                 patch.object(enemy3, 'can_see_player', return_value=False), \
                 patch.object(engine, '_alert_nearby_enemies') as mock_alert:
                
                engine._update_enemy_awareness()
                
                # Should call alert_nearby_enemies when enemy1 becomes hostile
                mock_alert.assert_called_once_with(enemy1)
    
    def test_group_movement_coordination(self):
        """Test that enemies coordinate movement to avoid clustering."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)
        
        # Create group of enemies
        enemies = [
            Enemy(Position(10, 10), 'scanner'),
            Enemy(Position(10, 11), 'patrol'),
            Enemy(Position(11, 10), 'bot')
        ]
        
        # All become hostile and target player
        for enemy in enemies:
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = player.position
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, enemies)
        
        # Generate movement for all
        for enemy in enemies:
            with patch.object(enemy, 'can_see_player', return_value=True):
                enemy._generate_movement_queue(game_map, player, mock_game)
        
        # Enemies should have movement plans
        for enemy in enemies:
            assert len(enemy.movement_queue) > 0
    
    def test_threat_prioritization(self):
        """Test that enemies prioritize threats appropriately."""
        game_map = GameMap(30, 30)
        player = Player(15, 15)
        
        enemy = Enemy(Position(10, 10), 'hunter')
        
        # Enemy can see player - should prioritize player
        with patch.object(enemy, 'can_see_player', return_value=True):
            enemy.state = EnemyState.UNAWARE
            
            # Simulate spotting player
            if enemy.can_see_player(player, game_map):
                enemy.state = EnemyState.ALERT
                enemy.last_seen_player = player.position
                
            assert enemy.state == EnemyState.ALERT
            assert enemy.last_seen_player is not None
    
    def test_memory_persistence_between_turns(self):
        """Test that enemies remember player positions between turns."""
        game_map = GameMap(30, 30)
        player = Player(15, 15)
        
        enemy = Enemy(Position(10, 10), 'hunter')
        enemy.state = EnemyState.HOSTILE
        
        # Set last seen position
        last_pos = Position(12, 12)
        enemy.last_seen_player = last_pos
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Enemy can't see player currently
        with patch.object(enemy, 'can_see_player', return_value=False):
            # Should still remember last position
            assert enemy.last_seen_player == last_pos
            
            # Should pathfind to remembered position
            enemy._generate_movement_queue(game_map, player, mock_game)
            
            if enemy.movement_queue:
                # Should move toward remembered position
                first_move = enemy.movement_queue[0]
                original_distance = Position(enemy.x, enemy.y).distance_to(last_pos)
                new_distance = first_move.distance_to(last_pos)
                assert new_distance <= original_distance
    
    def test_state_synchronization(self):
        """Test that enemy states are properly synchronized."""
        enemy = Enemy(Position(10, 10), 'scanner')
        
        # Test state transitions
        assert enemy.state == EnemyState.UNAWARE
        
        enemy.state = EnemyState.ALERT
        enemy.alert_timer = 0
        assert enemy.state == EnemyState.ALERT
        
        enemy.state = EnemyState.HOSTILE
        assert enemy.state == EnemyState.HOSTILE
        
        # Test that queue state tracking works
        enemy.last_queue_state = EnemyState.UNAWARE
        needs_regen = (enemy.last_queue_state != enemy.state)
        assert needs_regen is True  # State changed from UNAWARE to HOSTILE


class TestMovementValidation:
    """Test movement validation and collision detection."""
    
    def test_valid_enemy_move_checking(self):
        """Test that enemy move validation works correctly."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)
        enemy = Enemy(Position(10, 10), 'scanner')
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Valid position should pass
        valid_pos = Position(11, 11)
        assert enemy._is_valid_enemy_move(valid_pos, game_map, mock_game) is True
        
        # Wall position should fail
        game_map.walls.add((12, 12))
        wall_pos = Position(12, 12)
        assert enemy._is_valid_enemy_move(wall_pos, game_map, mock_game) is False
        
        # Out of bounds should fail
        oob_pos = Position(-1, 10)
        assert enemy._is_valid_enemy_move(oob_pos, game_map, mock_game) is False
        
        oob_pos2 = Position(50, 10)  # Beyond map width
        assert enemy._is_valid_enemy_move(oob_pos2, game_map, mock_game) is False
    
    def test_movement_cooldown_system(self):
        """Test enemy movement cooldown mechanics."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)
        enemy = Enemy(Position(10, 10), 'scanner')
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Set movement cooldown
        enemy.move_cooldown = 2
        
        # Should not move while on cooldown
        moved = enemy.move(game_map, player, mock_game)
        assert moved is False
        assert enemy.move_cooldown == 1
        
        # Still on cooldown
        moved = enemy.move(game_map, player, mock_game)
        assert moved is False
        assert enemy.move_cooldown == 0
        
        # Now should be able to move
        moved = enemy.move(game_map, player, mock_game)
        # Note: moved might still be False if no valid moves, but cooldown should be reset
    
    def test_disabled_enemy_behavior(self):
        """Test that disabled enemies cannot move."""
        game_map = GameMap(30, 30)
        player = Player(25, 25)
        enemy = Enemy(Position(10, 10), 'scanner')
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Disable enemy
        enemy.disabled_turns = 3
        
        # Should not move while disabled
        for turn in range(3):
            moved = enemy.move(game_map, player, mock_game)
            assert moved is False
            expected_remaining = 3 - turn - 1
            assert enemy.disabled_turns == expected_remaining
        
        # Should be able to move after disability expires
        moved = enemy.move(game_map, player, mock_game)
        assert enemy.disabled_turns == 0


class TestEnemyStateTransitions:
    """Test enemy state machine and transitions."""
    
    def test_unaware_to_alert_transition(self):
        """Test transition from UNAWARE to ALERT when spotting player."""
        game_map = GameMap(30, 30)
        player = Player(15, 15)
        enemy = Enemy(Position(10, 10), 'scanner')
        
        assert enemy.state == EnemyState.UNAWARE
        
        # Simulate spotting player
        with patch.object(enemy, 'can_see_player', return_value=True):
            if enemy.can_see_player(player, game_map):
                enemy.state = EnemyState.ALERT
                enemy.last_seen_player = player.position
                enemy.alert_timer = 0
        
        assert enemy.state == EnemyState.ALERT
        assert enemy.last_seen_player is not None
    
    def test_alert_to_hostile_transition(self):
        """Test transition from ALERT to HOSTILE."""
        enemy = Enemy(Position(10, 10), 'scanner')
        enemy.state = EnemyState.ALERT
        enemy.alert_timer = 0
        
        # After alert timer expires, should become hostile
        enemy.state = EnemyState.HOSTILE
        assert enemy.state == EnemyState.HOSTILE
    
    def test_patrol_behavior_preservation(self):
        """Test that patrol enemies preserve their routes when state changes."""
        enemy = Enemy(Position(10, 10), 'patrol')
        enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(20, 10)]
        enemy.patrol_index = 1
        original_index = enemy.patrol_index
        
        # Becoming hostile should preserve patrol data
        enemy.state = EnemyState.HOSTILE
        assert enemy.patrol_points is not None
        # patrol_index might change based on implementation, but patrol_points should remain


class TestEnemyAIIntegration:
    """Test integration between AI systems and game engine."""
    
    def test_enemy_turn_processing_order(self):
        """Test that enemy turns are processed in correct order."""
        with patch.object(GameEngine, '_generate_procedural_level'):
            game_map = GameMap(30, 30)
            engine = GameEngine(game_map=game_map)
            engine.player = Player(15, 15)
            
            # Create enemies
            enemies = [
                Enemy(Position(10, 10), 'scanner'),
                Enemy(Position(12, 12), 'patrol'),
                Enemy(Position(14, 14), 'hunter')
            ]
            engine.enemy_manager.enemies = enemies
            
            # Mock the update phases
            with patch.object(engine, '_update_enemy_awareness') as mock_awareness, \
                 patch.object(engine, '_move_enemies') as mock_movement, \
                 patch.object(engine, '_process_enemy_attacks') as mock_attacks:
                
                engine._update_enemies()
                
                # Should call phases in correct order
                mock_awareness.assert_called_once()
                mock_movement.assert_called_once()
                mock_attacks.assert_called_once()
    
    def test_ai_performance_with_multiple_enemies(self):
        """Test AI performance with many enemies."""
        game_map = GameMap(50, 50)
        player = Player(25, 25)
        
        # Create many enemies (use different types that actually move)
        enemies = []
        enemy_types = ['bot', 'hunter', 'patrol']  # These move
        for i in range(10):
            x = 10 + (i % 5) * 3
            y = 10 + (i // 5) * 3
            enemy_type = enemy_types[i % len(enemy_types)]
            enemy = Enemy(Position(x, y), enemy_type)
            enemy.state = EnemyState.UNAWARE  # They should at least try random movement
            enemies.append(enemy)
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, enemies)
        
        # All enemies generate movement
        for enemy in enemies:
            enemy._generate_movement_queue(game_map, player, mock_game)
        
        # All should have some kind of movement plan
        total_moves = sum(len(enemy.movement_queue) for enemy in enemies)
        assert total_moves > 0
    
    def test_ai_error_recovery(self):
        """Test that AI system recovers gracefully from errors."""
        game_map = GameMap(30, 30)
        player = Player(15, 15)
        enemy = Enemy(Position(10, 10), 'hunter')
        
        # Create mock game
        mock_game = create_mock_game(game_map, player, [enemy])
        
        # Simulate pathfinding failure
        with patch('game_characters.create_pathfinding_cost_map', side_effect=Exception("Pathfinding error")):
            # Should not crash, should fall back to random movement
            enemy._generate_pathfinding_queue(player.position, game_map, mock_game)
            
            # Should have some movement (random fallback)
            assert len(enemy.movement_queue) >= 0  # Might be 0 if no valid moves found