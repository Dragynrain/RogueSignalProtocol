#!/usr/bin/env python3
"""
Unit tests for enemy spawning and management system.
Tests EnemyManager class and enemy coordination logic.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import random

from game_enemies import EnemyManager
from game_entities import Position, EnemyMovement
from game_characters import Enemy, Player
from game_config import GameConfig


class TestEnemyManager:
    """Test the EnemyManager class."""
    
    def test_enemy_manager_creation(self):
        """Test enemy manager creation."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        assert manager.enemies == []
        assert manager.game_map == mock_game_map
        assert manager.message_log == mock_message_log
    
    def test_spawn_enemy_basic(self):
        """Test basic enemy spawning."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        position = Position(5, 5)
        
        enemy = manager.spawn_enemy(position, "scanner")
        
        assert len(manager.enemies) == 1
        assert enemy in manager.enemies
        assert enemy.position == position
        assert enemy.type == "scanner"
        mock_game_map.is_wall.assert_called_once_with(position)
    
    def test_spawn_enemy_on_wall_raises_error(self):
        """Test spawning enemy on wall raises ValueError."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=True)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        position = Position(3, 3)
        
        with pytest.raises(ValueError, match="Cannot spawn enemy on wall"):
            manager.spawn_enemy(position, "scanner")
        
        assert len(manager.enemies) == 0
    
    def test_spawn_patrol_enemy(self):
        """Test spawning a patrol enemy with patrol route generation."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=False)
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        manager._generate_patrol_route = Mock(return_value=[Position(5, 5), Position(10, 5)])
        
        position = Position(5, 5)
        enemy = manager.spawn_enemy(position, "patrol")
        
        assert enemy.type == "patrol"
        assert enemy.patrol_points == [Position(5, 5), Position(10, 5)]
        manager._generate_patrol_route.assert_called_once_with(position)
    
    def test_spawn_virus_enemy_random_movement(self):
        """Test spawning virus enemy with random movement assignment."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=False)
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        manager._generate_patrol_route = Mock(return_value=[Position(7, 7), Position(12, 7)])
        
        # Mock random.choices to return PATROL movement
        with patch('random.choices', return_value=[EnemyMovement.PATROL]):
            position = Position(7, 7)
            enemy = manager.spawn_enemy(position, "virus")
            
            assert enemy.type == "virus"
            assert enemy.type_data.movement == EnemyMovement.PATROL
            assert enemy.patrol_points == [Position(7, 7), Position(12, 7)]
    
    def test_spawn_virus_enemy_non_patrol_movement(self):
        """Test spawning virus enemy with non-patrol movement."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random.choices to return RANDOM movement
        with patch('random.choices', return_value=[EnemyMovement.RANDOM]):
            position = Position(8, 8)
            enemy = manager.spawn_enemy(position, "virus")
            
            assert enemy.type == "virus"
            assert enemy.type_data.movement == EnemyMovement.RANDOM
            # No patrol route should be generated for non-patrol movement
            assert enemy.patrol_points is None or enemy.patrol_points == []
    
    def test_update_all_enemies(self):
        """Test updating all enemies."""
        mock_game_map = Mock()
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Create mock enemies
        enemy1 = Mock()
        enemy1.disabled_turns = 0
        enemy1.move = Mock()
        
        enemy2 = Mock()
        enemy2.disabled_turns = 2  # Disabled enemy
        enemy2.move = Mock()
        
        enemy3 = Mock()
        enemy3.disabled_turns = 0
        enemy3.move = Mock()
        
        manager.enemies = [enemy1, enemy2, enemy3]
        
        mock_player = Mock()
        mock_game_state = Mock()
        mock_game = Mock()
        
        manager.update_all_enemies(mock_player, mock_game_state, mock_game)
        
        # Only non-disabled enemies should move
        enemy1.move.assert_called_once_with(mock_game_map, mock_player, mock_game)
        enemy2.move.assert_not_called()  # Disabled
        enemy3.move.assert_called_once_with(mock_game_map, mock_player, mock_game)
    
    def test_get_enemy_at_position_found(self):
        """Test getting enemy at specific position when enemy exists."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Create mock enemies at different positions
        enemy1 = Mock()
        enemy1.position = Position(5, 5)
        
        enemy2 = Mock()
        enemy2.position = Position(8, 3)
        
        manager.enemies = [enemy1, enemy2]
        
        result = manager.get_enemy_at_position(Position(8, 3))
        
        assert result == enemy2
    
    def test_get_enemy_at_position_not_found(self):
        """Test getting enemy at position when no enemy exists."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Create mock enemy at different position
        enemy1 = Mock()
        enemy1.position = Position(5, 5)
        
        manager.enemies = [enemy1]
        
        result = manager.get_enemy_at_position(Position(10, 10))
        
        assert result is None
    
    def test_get_enemy_at_position_empty_list(self):
        """Test getting enemy when enemy list is empty."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        result = manager.get_enemy_at_position(Position(5, 5))
        
        assert result is None
    
    def test_remove_enemy_exists(self):
        """Test removing an existing enemy."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        enemy1 = Mock()
        enemy2 = Mock()
        enemy3 = Mock()
        
        manager.enemies = [enemy1, enemy2, enemy3]
        
        manager.remove_enemy(enemy2)
        
        assert enemy2 not in manager.enemies
        assert len(manager.enemies) == 2
        assert enemy1 in manager.enemies
        assert enemy3 in manager.enemies
    
    def test_remove_enemy_not_exists(self):
        """Test removing a non-existing enemy."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        enemy1 = Mock()
        enemy2 = Mock()
        different_enemy = Mock()
        
        manager.enemies = [enemy1, enemy2]
        
        manager.remove_enemy(different_enemy)
        
        # List should remain unchanged
        assert len(manager.enemies) == 2
        assert enemy1 in manager.enemies
        assert enemy2 in manager.enemies
    
    def test_resume_patrol_route_no_patrol_points(self):
        """Test resuming patrol route when enemy has no patrol points."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        enemy = Mock()
        enemy.patrol_points = []
        
        manager._resume_patrol_route(enemy)
        
        # Should do nothing (no assertions needed, just ensure no error)
    
    def test_resume_patrol_route_near_point(self):
        """Test resuming patrol route when near a patrol point."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        enemy = Mock()
        enemy.position = Position(5, 5)
        enemy.patrol_points = [Position(5, 5), Position(10, 5), Position(10, 10)]
        enemy.patrol_index = 0
        enemy.patrol_stuck_counter = 5
        
        # Mock the distance calculation
        enemy.position.distance_to = Mock(side_effect=lambda pos: 0.5 if pos == Position(5, 5) else 10.0)
        
        # Mock the constant directly where it's used
        with patch('game_enemies.GameConfig') as mock_config:
            mock_config.ADJACENT_VISIBILITY_THRESHOLD = 1.0
            manager._resume_patrol_route(enemy)
        
        # Should advance to next point since very close to current point
        assert enemy.patrol_index == 1
        assert enemy.patrol_stuck_counter == 0
    
    def test_resume_patrol_route_far_from_point(self):
        """Test resuming patrol route when far from nearest point."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        enemy = Mock()
        enemy.position = Position(7, 7)
        enemy.patrol_points = [Position(5, 5), Position(10, 5), Position(10, 10)]
        enemy.patrol_stuck_counter = 3
        
        # Mock distance calculations - closest to point at index 1
        def mock_distance(pos):
            distances = {
                Position(5, 5): 5.0,   # Index 0
                Position(10, 5): 3.0,  # Index 1 - closest
                Position(10, 10): 4.0  # Index 2
            }
            return distances.get(pos, 10.0)
        
        enemy.position.distance_to = Mock(side_effect=mock_distance)
        
        # Mock the constant directly where it's used
        with patch('game_enemies.GameConfig') as mock_config:
            mock_config.ADJACENT_VISIBILITY_THRESHOLD = 1.0
            manager._resume_patrol_route(enemy)
        
        # Should set patrol index to nearest point (index 1)
        assert enemy.patrol_index == 1
        assert enemy.patrol_stuck_counter == 0


class TestPatrolRouteGeneration:
    """Test patrol route generation methods."""
    
    def test_generate_patrol_route_line_horizontal(self):
        """Test generating horizontal line patrol route."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random choices
        with patch('random.choice', side_effect=['line', 'horizontal']):
            with patch('random.randint', return_value=6):
                start = Position(5, 5)
                route = manager._generate_patrol_route(start)
                
                assert len(route) == 2
                assert route[0] == start
                assert route[1] == Position(11, 5)  # 5 + 6
    
    def test_generate_patrol_route_line_vertical(self):
        """Test generating vertical line patrol route."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random choices
        with patch('random.choice', side_effect=['line', 'vertical']):
            with patch('random.randint', return_value=4):
                start = Position(8, 8)
                route = manager._generate_patrol_route(start)
                
                assert len(route) == 2
                assert route[0] == start
                assert route[1] == Position(8, 12)  # 8 + 4
    
    def test_generate_patrol_route_line_diagonal(self):
        """Test generating diagonal line patrol route."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random choices
        with patch('random.choice', side_effect=['line', 'diagonal']):
            with patch('random.randint', return_value=5):
                start = Position(10, 10)
                route = manager._generate_patrol_route(start)
                
                assert len(route) == 2
                assert route[0] == start
                assert route[1] == Position(15, 15)  # 10 + 5, 10 + 5
    
    def test_generate_patrol_route_triangle(self):
        """Test generating triangle patrol route."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random choices
        with patch('random.choice', return_value='triangle'):
            with patch('random.randint', return_value=6):
                start = Position(5, 5)
                route = manager._generate_patrol_route(start)
                
                assert len(route) == 3
                assert route[0] == start
                assert route[1] == Position(11, 5)  # 5 + 6
                assert route[2] == Position(8, 11)  # 5 + 6//2, 5 + 6
    
    def test_generate_patrol_route_rectangle(self):
        """Test generating rectangle patrol route."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock random choices
        with patch('random.choice', return_value='rectangle'):
            with patch('random.randint', return_value=4):
                start = Position(6, 6)
                route = manager._generate_patrol_route(start)
                
                assert len(route) == 4
                assert route[0] == start
                assert route[1] == Position(10, 6)   # 6 + 4
                assert route[2] == Position(10, 10)  # 6 + 4, 6 + 4
                assert route[3] == Position(6, 10)   # 6, 6 + 4
    
    def test_generate_patrol_route_invalid_points_fallback(self):
        """Test fallback when pattern generation fails."""
        mock_game_map = Mock()
        # First call (for pattern) returns False, second call (for fallback) returns True
        mock_game_map.is_valid_position = Mock(side_effect=[False, True])
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        manager._is_valid_patrol_point = Mock(side_effect=[False, False, True])  # Pattern fails twice, fallback succeeds
        
        # Mock random choices
        with patch('random.choice', return_value='triangle'):
            with patch('random.randint', return_value=6):
                start = Position(5, 5)
                route = manager._generate_patrol_route(start)
                
                # Should fallback to 2-point horizontal line
                assert len(route) == 2
                assert route[0] == start
                assert route[1] == Position(9, 5)  # 5 + 4 (fallback step size)
    
    def test_generate_patrol_route_complete_fallback(self):
        """Test complete fallback when all generation fails."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        manager._is_valid_patrol_point = Mock(return_value=False)  # All points invalid
        
        # Mock random choices
        with patch('random.choice', return_value='line'):
            start = Position(5, 5)
            route = manager._generate_patrol_route(start)
            
            # Should return single point (static guard)
            assert len(route) == 1
            assert route[0] == start
    
    def test_is_valid_patrol_point_valid(self):
        """Test valid patrol point check."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock GameConfig
        with patch.object(GameConfig, 'MAP_WIDTH', 50):
            with patch.object(GameConfig, 'MAP_HEIGHT', 50):
                point = Position(10, 10)
                result = manager._is_valid_patrol_point(point)
                
                assert result is True
                mock_game_map.is_valid_position.assert_called_once_with(point)
                mock_game_map.is_wall.assert_called_once_with(point)
    
    def test_is_valid_patrol_point_too_close_to_edge(self):
        """Test patrol point too close to map edge."""
        mock_game_map = Mock()
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock GameConfig
        with patch.object(GameConfig, 'MAP_WIDTH', 50):
            with patch.object(GameConfig, 'MAP_HEIGHT', 50):
                point = Position(2, 10)  # x < 3, too close to edge
                result = manager._is_valid_patrol_point(point)
                
                assert result is False
    
    def test_is_valid_patrol_point_on_wall(self):
        """Test patrol point on wall."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=True)
        mock_game_map.is_wall = Mock(return_value=True)  # Point is on wall
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock GameConfig
        with patch.object(GameConfig, 'MAP_WIDTH', 50):
            with patch.object(GameConfig, 'MAP_HEIGHT', 50):
                point = Position(10, 10)
                result = manager._is_valid_patrol_point(point)
                
                assert result is False
    
    def test_is_valid_patrol_point_invalid_position(self):
        """Test patrol point with invalid map position."""
        mock_game_map = Mock()
        mock_game_map.is_valid_position = Mock(return_value=False)  # Invalid position
        mock_game_map.is_wall = Mock(return_value=False)
        mock_message_log = Mock()
        
        manager = EnemyManager(mock_game_map, mock_message_log)
        
        # Mock GameConfig
        with patch.object(GameConfig, 'MAP_WIDTH', 50):
            with patch.object(GameConfig, 'MAP_HEIGHT', 50):
                point = Position(10, 10)
                result = manager._is_valid_patrol_point(point)
                
                assert result is False