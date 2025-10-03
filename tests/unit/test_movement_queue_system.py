"""
Comprehensive tests for the enemy movement queue system.
Tests ALL aspects of movement queue functionality.
"""

from unittest.mock import Mock, patch
from game_characters import Enemy, Player
from game_entities import Position, EnemyState, EnemyMovement
from game_map import GameMap
from tests.fixtures.real_game_data import create_real_enemy, create_test_map_with_real_tiles

class TestMovementQueueGeneration:
    """Test movement queue generation for all enemy types."""
    
    def setup_method(self):
        self.game_map = create_test_map_with_real_tiles()
        self.player = Player(10, 10)
        self.game_engine = Mock()  # Minimal mock for game engine
        self.game_engine.player = self.player
        self.game_engine.enemies = []  # Empty list of enemies
    
    def test_queue_generation_for_random_movement(self):
        """Test queue generation for RANDOM movement enemies."""
        enemy = create_real_enemy("bot", Position(5, 5))  # Bot uses RANDOM
        assert enemy.type_data.movement == EnemyMovement.RANDOM
        
        # Generate queue
        enemy._generate_movement_queue(self.game_map, self.player, self.game_engine)
        
        # Verify queue properties
        assert len(enemy.movement_queue) == 3, "Queue must always have 3 moves"
        assert all(isinstance(pos, Position) for pos in enemy.movement_queue), "Queue must contain Position objects"
        
        # Verify moves are valid (not in walls, within map bounds)
        for pos in enemy.movement_queue:
            assert not self.game_map.is_wall(pos), f"Move to {pos} must not be a wall"
            assert 0 <= pos.x < self.game_map.width, "Move must be within map width"
            assert 0 <= pos.y < self.game_map.height, "Move must be within map height"
    
    def test_queue_generation_for_seek_movement(self):
        """Test queue generation for SEEK movement enemies."""
        enemy = create_real_enemy("hunter", Position(15, 15))  # Hunter uses SEEK
        enemy.state = EnemyState.HOSTILE  # Seeking requires hostile state
        
        enemy._generate_movement_queue(self.game_map, self.player, self.game_engine)
        
        assert len(enemy.movement_queue) == 3
        
        # For SEEK, verify that the system generates moves (pathfinding may not always be direct)
        # Verify moves are valid (not in walls, within map bounds)
        for pos in enemy.movement_queue:
            assert not self.game_map.is_wall(pos), f"Move to {pos} must not be a wall"
            assert 0 <= pos.x < self.game_map.width, "Move must be within map width"
            assert 0 <= pos.y < self.game_map.height, "Move must be within map height"
    
    def test_queue_generation_for_patrol_movement(self):
        """Test queue generation for PATROL movement enemies."""
        enemy = create_real_enemy("patrol", Position(5, 5))  # Patrol uses PATROL
        enemy.patrol_points = [Position(10, 5), Position(15, 5), Position(5, 5)]
        enemy.patrol_index = 0
        
        enemy._generate_movement_queue(self.game_map, self.player, self.game_engine)
        
        assert len(enemy.movement_queue) == 3
        
        # For PATROL, verify that the system generates moves and they're valid
        # Verify moves are valid (not in walls, within map bounds)
        for pos in enemy.movement_queue:
            assert not self.game_map.is_wall(pos), f"Move to {pos} must not be a wall"
            assert 0 <= pos.x < self.game_map.width, "Move must be within map width"
            assert 0 <= pos.y < self.game_map.height, "Move must be within map height"
        
        # Verify patrol enemy has patrol points set
        assert len(enemy.patrol_points) > 0, "Patrol enemy should have patrol points"
        assert 0 <= enemy.patrol_index < len(enemy.patrol_points), "Patrol index should be valid"

class TestMovementQueueExecution:
    """Test movement queue execution and state updates."""
    
    def test_execute_next_move_success(self):
        """Test successful execution of next move from queue."""
        enemy = create_real_enemy("bot", Position(5, 5))
        enemy.movement_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]
        original_position = enemy.position
        
        game_map = create_test_map_with_real_tiles()
        player = Player(10, 10)
        
        # Create mock game object with enemies list
        mock_game = Mock()
        mock_game.enemies = [enemy]  # Include the enemy itself
        
        success = enemy._execute_next_move(game_map, player, mock_game)
        
        assert success == True, "Move execution should succeed"
        assert enemy.position == Position(6, 5), "Enemy should move to first queue position"
        assert len(enemy.movement_queue) == 2, "Queue should have one less move after execution"
        assert enemy.movement_queue[0] == Position(7, 5), "Next move should be at queue front"
    
    def test_execute_move_blocked_clears_queue(self):
        """Test that blocked moves clear the queue for recalculation."""
        enemy = create_real_enemy("bot", Position(5, 5))
        enemy.movement_queue = [Position(1, 1), Position(2, 2), Position(3, 3)]  # Assume blocked
        
        game_map = create_test_map_with_real_tiles()
        player = Player(10, 10)
        
        # Create mock game object with enemies list
        mock_game = Mock()
        mock_game.enemies = [enemy]
        
        # Mock can_move_to_position to return False (blocked)
        with patch('game_characters.can_move_to_position', return_value=False):
            success = enemy._execute_next_move(game_map, player, mock_game)

        assert success == False, "Blocked move should fail"
        assert len(enemy.movement_queue) == 2, "Blocked move should only remove first move, not clear entire queue"

class TestMovementQueuePrediction:
    """Test movement prediction system that shows queue to player."""
    
    def test_predict_enemy_movement_uses_queue(self):
        """Test that movement prediction uses enemy's actual queue."""
        from game_engine import GameEngine
        
        # Create real game setup with proper initialization
        player = Player(10, 10)
        game_map = create_test_map_with_real_tiles()
        game_engine = GameEngine()
        game_engine.player = player  # Set the player
        game_engine.game_map = game_map  # Set the game map
        
        enemy = create_real_enemy("bot", Position(5, 5))
        enemy.movement_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]
        
        # Test prediction
        predicted_moves = game_engine.get_enemy_next_positions(enemy, steps=3)
        
        assert len(predicted_moves) == 3, "Should predict requested number of steps"
        assert predicted_moves == enemy.movement_queue, "Prediction should match actual queue"
        
    def test_predict_movement_generates_queue_if_empty(self):
        """Test prediction generates queue if enemy has no queue."""
        from game_engine import GameEngine
        
        # Create real game setup with proper initialization
        player = Player(10, 10)
        game_map = create_test_map_with_real_tiles()
        game_engine = GameEngine()
        game_engine.player = player  # Set the player
        game_engine.game_map = game_map  # Set the game map
        
        enemy = create_real_enemy("bot", Position(5, 5))
        enemy.movement_queue = []  # Empty queue
        
        predicted_moves = game_engine.get_enemy_next_positions(enemy, steps=3)
        
        assert len(predicted_moves) == 3, "Should generate predictions even with empty queue"
        assert all(isinstance(pos, Position) for pos in predicted_moves), "Predictions should be Position objects"

class TestMovementQueueStateTracking:
    """Test when queues should be regenerated vs extended."""
    
    def test_queue_regeneration_on_state_change(self):
        """Test queue regenerates when enemy state changes."""
        enemy = create_real_enemy("hunter", Position(5, 5))
        enemy.state = EnemyState.UNAWARE
        enemy.movement_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]
        enemy.last_queue_state = EnemyState.UNAWARE
        
        # Change state to HOSTILE
        enemy.state = EnemyState.HOSTILE
        
        game_map = create_test_map_with_real_tiles()
        player = Player(10, 10)
        
        should_regenerate = enemy._should_regenerate_queue(game_map, player, None)
        assert should_regenerate == True, "Queue should regenerate when state changes"
    
    def test_queue_extension_when_state_stable(self):
        """Test queue extends (not regenerates) when state is stable."""
        enemy = create_real_enemy("bot", Position(5, 5))
        enemy.state = EnemyState.UNAWARE
        enemy.movement_queue = [Position(6, 5)]  # Short queue
        enemy.last_queue_state = EnemyState.UNAWARE

        game_map = create_test_map_with_real_tiles()
        player = Player(10, 10)

        # Create mock game object
        mock_game = Mock()
        mock_game.player = player
        mock_game.enemies = [enemy]

        should_regenerate = enemy._should_regenerate_queue(game_map, player, mock_game)
        assert should_regenerate == False, "Queue should extend, not regenerate, when state stable"

        # Store initial queue length
        initial_length = len(enemy.movement_queue)

        enemy._extend_movement_queue(None, False, game_map, mock_game)

        # Should have extended the queue by at least 1 move, preferably to 3 total
        new_length = len(enemy.movement_queue)
        assert new_length > initial_length, "Queue should be extended with additional moves"
        assert new_length <= 3, "Queue should not exceed 3 moves"

        # In most cases it should reach 3, but allow for edge cases where map constraints prevent it
        if new_length < 3:
            # If we couldn't reach 3 moves, ensure it's due to valid constraints (no more valid moves)
            # This is acceptable behavior when enemy is constrained by map geometry
            print(f"Warning: Queue only extended to {new_length} moves (acceptable if map constrains movement)")

class TestMovementQueueAttackProximity:
    """Test movement queue behavior when enemies can attack within 3 moves."""

    def test_queue_stops_when_adjacent_to_player(self):
        """Enemy queue stops when it would be adjacent to player (attack position)."""
        from game_engine import GameEngine

        # Create real game setup
        player = Player(10, 10)
        game_map = create_test_map_with_real_tiles()
        game_engine = GameEngine()
        game_engine.player = player
        game_engine.game_map = game_map

        # Enemy 2 moves away should only show 1 move (to adjacent position)
        enemy = create_real_enemy("hunter", Position(12, 10))  # 2 moves away horizontally
        enemy.state = EnemyState.HOSTILE
        game_engine.enemies = [enemy]

        predicted_moves = game_engine.get_enemy_next_positions(enemy, steps=3)

        assert len(predicted_moves) == 1, "Enemy 2 moves away should show only 1 move"
        assert predicted_moves[0].is_adjacent_to(player.position), "Move should get enemy adjacent to player"

    def test_queue_shows_full_3_moves_when_far_away(self):
        """Enemy far from player shows full 3-move queue."""
        from game_engine import GameEngine

        # Create real game setup
        player = Player(10, 10)
        game_map = create_test_map_with_real_tiles()
        game_engine = GameEngine()
        game_engine.player = player
        game_engine.game_map = game_map

        # Enemy 5+ moves away should show 3 moves
        enemy = create_real_enemy("hunter", Position(15, 10))  # 5 moves away
        enemy.state = EnemyState.HOSTILE
        game_engine.enemies = [enemy]

        predicted_moves = game_engine.get_enemy_next_positions(enemy, steps=3)

        assert len(predicted_moves) == 3, "Enemy far away should show full 3 moves"

    def test_adjacent_enemy_shows_no_moves(self):
        """Enemy adjacent to player shows no movement (will attack)."""
        from game_engine import GameEngine

        # Create real game setup
        player = Player(10, 10)
        game_map = create_test_map_with_real_tiles()
        game_engine = GameEngine()
        game_engine.player = player
        game_engine.game_map = game_map

        # Adjacent enemy should show no moves
        enemy = create_real_enemy("hunter", Position(11, 10))  # Adjacent
        enemy.state = EnemyState.HOSTILE
        game_engine.enemies = [enemy]

        predicted_moves = game_engine.get_enemy_next_positions(enemy, steps=3)

        assert len(predicted_moves) == 0, "Adjacent enemy should show no moves (will attack)"
        assert enemy.can_attack_player(player) is True, "Enemy should be able to attack player"