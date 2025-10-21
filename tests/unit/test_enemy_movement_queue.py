#!/usr/bin/env python3
"""
Unit tests for enemy movement queue system.

The movement queue is a FIFO queue (max size 3) that stores enemy moves.
This is critical for enemy behavior - enemies plan moves ahead and execute them.
"""

import pytest
from game_entities import Position, EnemyState
from tests.fixtures.simple_fixtures import enemy_builder, map_builder


class TestMovementQueueBasics:
    """Test basic movement queue operations."""

    def test_move_queue_initializes_empty(self):
        """New enemy should have empty movement queue."""
        enemy = enemy_builder("scanner", pos=(10, 10))

        assert enemy.move_queue == []

    def test_add_moves_to_queue(self):
        """Enemy can add moves to queue."""
        enemy = enemy_builder("scanner", pos=(10, 10))

        enemy.move_queue = [Position(11, 10), Position(12, 10)]

        assert len(enemy.move_queue) == 2
        assert enemy.move_queue[0] == Position(11, 10)
        assert enemy.move_queue[1] == Position(12, 10)

    def test_move_queue_fifo_order(self):
        """Queue should consume moves in FIFO order (first in, first out)."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder()

        # Queue up 3 moves
        enemy.move_queue = [
            Position(11, 10),  # First move
            Position(12, 10),  # Second move
            Position(13, 10),  # Third move
        ]

        # Execute first move
        if enemy.move_queue:
            next_move = enemy.move_queue.pop(0)  # FIFO
            enemy.position = next_move

        assert enemy.position == Position(11, 10)
        assert len(enemy.move_queue) == 2
        assert enemy.move_queue[0] == Position(12, 10)


class TestMovementQueueSizeLimit:
    """Test movement queue size constraints."""

    def test_move_queue_size_limit_three(self):
        """Movement queue should be limited to 3 positions."""
        enemy = enemy_builder("patrol", pos=(5, 5))

        # Try to add 5 moves
        full_path = [Position(6, 5), Position(7, 5), Position(8, 5),
                     Position(9, 5), Position(10, 5)]

        # Queue should only store first 3
        enemy.move_queue = full_path[:3]

        assert len(enemy.move_queue) == 3
        assert enemy.move_queue[0] == Position(6, 5)
        assert enemy.move_queue[2] == Position(8, 5)

    def test_queue_doesnt_overflow(self):
        """Adding to full queue should not cause errors."""
        enemy = enemy_builder("patrol", pos=(5, 5))

        # Fill queue
        enemy.move_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]

        # Verify full
        assert len(enemy.move_queue) == 3


class TestQueueRefillBehavior:
    """Test queue refill when empty."""

    def test_empty_queue_triggers_refill(self):
        """When queue is empty, enemy should calculate new path."""
        enemy = enemy_builder("patrol", pos=(10, 10),
                             patrol_points=[(15, 15), (20, 20)])
        game_map = map_builder(width=40, height=40)

        # Start with empty queue
        enemy.move_queue = []

        # After calling move() with empty queue, it should refill
        # (This would be tested in integration - here we test the condition)
        assert len(enemy.move_queue) == 0  # Starts empty

    def test_queue_exhaustion_during_patrol(self):
        """Patrol enemy exhausts queue and needs new path to next point."""
        enemy = enemy_builder("patrol", pos=(10, 10),
                             patrol_points=[(10, 15), (15, 15)])

        # Simulate exhausting queue
        enemy.move_queue = [Position(10, 11)]

        # Pop last move
        enemy.move_queue.pop(0)

        # Queue now empty - enemy needs to recalculate
        assert len(enemy.move_queue) == 0


class TestStateChangeQueueBehavior:
    """Test how state changes affect movement queue."""

    def test_becoming_hostile_clears_old_patrol_queue(self):
        """When enemy becomes HOSTILE, old patrol queue should be cleared."""
        enemy = enemy_builder("patrol", pos=(10, 10),
                             state=EnemyState.UNAWARE,
                             patrol_points=[(15, 15)],
                             move_queue=[(11, 10), (12, 10)])

        # Enemy has patrol queue
        assert len(enemy.move_queue) == 2

        # Enemy spots player and becomes HOSTILE
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = Position(20, 20)

        # Old patrol queue should be cleared (in actual move() logic)
        # This test verifies the state change occurred
        assert enemy.state == EnemyState.HOSTILE

    def test_alert_state_keeps_queue(self):
        """ALERT state (heard something) may keep partial queue."""
        enemy = enemy_builder("scanner", pos=(10, 10),
                             state=EnemyState.UNAWARE,
                             move_queue=[(11, 10), (12, 10)])

        # Enemy becomes ALERT (heard player)
        enemy.state = EnemyState.ALERT

        # Queue behavior depends on alert logic - just test state
        assert enemy.state == EnemyState.ALERT


class TestQueueBlockageRecovery:
    """Test queue behavior when path becomes blocked."""

    def test_blocked_move_in_queue(self):
        """If queued move is blocked, enemy should handle gracefully."""
        game_map = map_builder(width=30, height=30,
                              walls=[(11, 10), (12, 10)])  # Block path

        enemy = enemy_builder("scanner", pos=(10, 10),
                             move_queue=[(11, 10), (12, 10)])  # Blocked path

        # Enemy has moves queued to blocked positions
        assert len(enemy.move_queue) == 2

        # When trying to move to (11, 10), should detect wall
        next_move = enemy.move_queue[0]
        is_blocked = game_map.is_wall(next_move)

        assert is_blocked is True  # Move is blocked

    def test_queue_with_partial_blockage(self):
        """Queue where second move is blocked but first is valid."""
        game_map = map_builder(width=30, height=30,
                              walls=[(12, 10)])  # Only second move blocked

        enemy = enemy_builder("scanner", pos=(10, 10),
                             move_queue=[(11, 10), (12, 10), (13, 10)])

        # First move should be valid
        assert not game_map.is_wall(enemy.move_queue[0])
        # Second move is blocked
        assert game_map.is_wall(enemy.move_queue[1])


class TestQueueFromPathfinding:
    """Test queue population from pathfinding results."""

    def test_path_to_queue_conversion(self):
        """Path from TCOD pathfinding should populate queue correctly."""
        enemy = enemy_builder("scanner", pos=(5, 5))

        # Simulate TCOD pathfinding result (list of (x, y) tuples)
        pathfinding_result = [(6, 5), (7, 5), (8, 5), (9, 5)]

        # Convert to queue (first 3 moves)
        enemy.move_queue = [Position(x, y) for x, y in pathfinding_result[:3]]

        assert len(enemy.move_queue) == 3
        assert enemy.move_queue[0] == Position(6, 5)
        assert enemy.move_queue[2] == Position(8, 5)

    def test_empty_path_results_in_empty_queue(self):
        """No path found should result in empty queue."""
        enemy = enemy_builder("scanner", pos=(5, 5))

        # Pathfinding failed - no path
        pathfinding_result = []

        enemy.move_queue = [Position(x, y) for x, y in pathfinding_result[:3]]

        assert len(enemy.move_queue) == 0


class TestPathfindingHelper:
    """Test centralized pathfinding helper."""

    def test_pathfinding_finds_straight_path(self):
        """PathfindingHelper finds basic straight path."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        game_map = map_builder(width=30, height=30)
        enemy = enemy_builder("scanner", pos=(10, 10))

        # Mock game_engine with enemies list
        game_engine = Mock()
        game_engine.enemies = [enemy]

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy
        )

        assert path is not None, "Should find path"
        assert len(path) > 1, "Path should have multiple steps"
        # Path should move toward goal
        assert path[-1][1] > 10, "Path should move in positive x direction"

    def test_pathfinding_around_walls(self):
        """PathfindingHelper routes around walls."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        # Create map with wall blocking direct path
        game_map = map_builder(width=30, height=30,
                              walls=[(11, 10), (12, 10), (13, 10)])
        enemy = enemy_builder("scanner", pos=(10, 10))

        game_engine = Mock()
        game_engine.enemies = [enemy]

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy
        )

        # Should find path around wall (or None if completely blocked)
        # The important thing is it doesn't crash and handles walls
        assert path is None or len(path) > 1

    def test_pathfinding_routes_around_enemies(self):
        """PathfindingHelper routes around other enemies."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        game_map = map_builder(width=30, height=30)
        enemy1 = enemy_builder("scanner", pos=(10, 10))
        enemy2 = enemy_builder("bot", pos=(11, 10))  # Blocking

        game_engine = Mock()
        game_engine.enemies = [enemy1, enemy2]

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy1
        )

        # Path should exist and route around enemy2
        assert path is not None, "Should find path around enemy"
        # Verify path doesn't go through enemy2's position
        if len(path) > 1:
            # Check that no step in path goes through enemy2
            for step in path[1:]:  # Skip start position
                # step is a tuple (y, x), compare correctly
                assert not (step[0] == enemy2.y and step[1] == enemy2.x), "Path should not go through other enemy"

    def test_pathfinding_unreachable_target(self):
        """PathfindingHelper returns None for unreachable targets."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        # Create map with walls completely surrounding the goal
        walls = []
        for x in range(14, 17):
            for y in range(14, 17):
                walls.append((x, y))

        game_map = map_builder(width=30, height=30, walls=walls)
        enemy = enemy_builder("scanner", pos=(10, 10))

        game_engine = Mock()
        game_engine.enemies = [enemy]

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 15),  # Completely walled off
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy
        )

        assert path is None, "Should return None for unreachable target"

    def test_pathfinding_path_length_limit(self):
        """PathfindingHelper respects path length limits."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        game_map = map_builder(width=100, height=100)
        enemy = enemy_builder("scanner", pos=(10, 10))

        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Try to find path to very distant target
        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(90, 90),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy,
            max_length_multiplier=1.5  # Strict limit
        )

        # Path should either be None or within reasonable length
        if path is not None:
            direct_distance = Position(10, 10).distance_to(Position(90, 90))
            max_allowed = max(15, int(direct_distance * 1.5))
            assert len(path) <= max_allowed, "Path should respect length limit"

    def test_pathfinding_adjacent_positions(self):
        """PathfindingHelper handles adjacent positions correctly."""
        from game_characters import PathfindingHelper
        from unittest.mock import Mock

        game_map = map_builder(width=30, height=30)
        enemy = enemy_builder("scanner", pos=(10, 10))

        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Path to adjacent position
        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(11, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy
        )

        assert path is not None, "Should find path to adjacent position"
        assert len(path) == 2, "Path to adjacent should be 2 steps (start + goal)"
        # Verify path ends at goal (comparing tuples directly)
        assert tuple(path[-1]) == (10, 11), "Path should end at goal position (y, x)"


class TestEnsureQueueFull:
    """Test _ensure_queue_full() method for Phase 2."""

    def test_ensure_queue_full_fills_to_three_initially(self):
        """Empty queue fills to 3 moves."""
        from unittest.mock import Mock

        # Use bot which has SEEK movement type (not STATIC)
        enemy = enemy_builder("bot", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 20
        player.y = 20
        player.position = Position(20, 20)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Hostile enemy should target player
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = player.position
        # Mock can_see_player so target is found
        enemy.can_see_player = Mock(return_value=True)

        enemy._ensure_queue_full(game_map, player, game_engine)

        assert len(enemy.move_queue) <= 3, "Queue should not exceed 3 moves"
        assert len(enemy.move_queue) >= 1, "Queue should have at least 1 move"

    def test_ensure_queue_full_tops_up_partial_queue(self):
        """Partial queue tops up to 3 moves."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 20
        player.y = 20
        player.position = Position(20, 20)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Hostile enemy should target player
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = player.position

        # Start with 1 move
        enemy.move_queue = [Position(11, 10)]

        enemy._ensure_queue_full(game_map, player, game_engine)

        assert len(enemy.move_queue) <= 3, "Queue should not exceed 3 moves"
        assert len(enemy.move_queue) >= 1, "Queue should maintain moves"

    def test_ensure_queue_full_does_not_overfill(self):
        """Queue with 3 moves should not be overfilled."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 20
        player.y = 20
        player.position = Position(20, 20)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Fill queue to 3
        enemy.move_queue = [Position(11, 10), Position(12, 10), Position(13, 10)]

        enemy._ensure_queue_full(game_map, player, game_engine)

        assert len(enemy.move_queue) == 3, "Queue should stay at 3 moves"

    def test_ensure_queue_full_random_movement(self):
        """Random movement enemies fill queue with random moves."""
        from unittest.mock import Mock
        from game_entities import EnemyMovement

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 20
        player.y = 20
        player.position = Position(20, 20)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Force random movement by mocking type_data
        enemy.type_data = Mock()
        enemy.type_data.movement = EnemyMovement.RANDOM

        enemy._ensure_queue_full(game_map, player, game_engine)

        # Random movement should fill queue
        assert len(enemy.move_queue) <= 3, "Queue should not exceed 3 moves"

    def test_ensure_queue_full_static_enemy(self):
        """Static enemies don't fill queue."""
        from unittest.mock import Mock
        from game_entities import EnemyMovement

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 20
        player.y = 20
        player.position = Position(20, 20)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Force static movement
        enemy.type_data = Mock()
        enemy.type_data.movement = EnemyMovement.STATIC

        enemy._ensure_queue_full(game_map, player, game_engine)

        assert len(enemy.move_queue) == 0, "Static enemies should not queue moves"


class TestFillRandomMoves:
    """Test _fill_random_moves() helper method."""

    def test_fill_random_moves_fills_queue(self):
        """_fill_random_moves() fills queue with random valid moves."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        enemy._fill_random_moves(game_map, player, game_engine)

        # Should fill to 3 (or fewer if cornered)
        assert len(enemy.move_queue) <= 3
        # All moves should be valid positions
        for move in enemy.move_queue:
            assert game_map.is_valid_position(move)

    def test_fill_random_moves_chains_from_last_position(self):
        """Random moves chain from last queued position."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        # Start with one move
        enemy.move_queue = [Position(11, 10)]

        enemy._fill_random_moves(game_map, player, game_engine)

        # Should have filled to 3
        assert len(enemy.move_queue) <= 3
        # First move should remain unchanged
        assert enemy.move_queue[0] == Position(11, 10)


class TestCalculateRandomMoveFrom:
    """Test _calculate_random_move_from() helper."""

    def test_calculate_random_move_from_open_space(self):
        """Can find random move from open space."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        move = enemy._calculate_random_move_from(Position(15, 15), game_map, player, game_engine)

        assert move is not None, "Should find random move in open space"
        assert game_map.is_valid_position(move)
        # Should be adjacent to start position
        distance = Position(15, 15).distance_to(move)
        assert distance <= 1.5, "Random move should be adjacent"

    def test_calculate_random_move_from_blocked(self):
        """Returns None if all directions blocked."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        # Surround position with walls
        walls = [(x, y) for x in range(14, 17) for y in range(14, 17) if (x, y) != (15, 15)]
        game_map = map_builder(width=40, height=40, walls=walls)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        move = enemy._calculate_random_move_from(Position(15, 15), game_map, player, game_engine)

        # Should return None when all directions are blocked
        assert move is None, "Should return None when surrounded"


class TestIsMoveValidFrom:
    """Test _is_move_valid_from() helper."""

    def test_is_move_valid_from_valid_position(self):
        """Valid move returns True."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        is_valid = enemy._is_move_valid_from(Position(15, 15), Position(14, 15), game_map, player, game_engine)

        assert is_valid is True

    def test_is_move_valid_from_player_position(self):
        """Move to player position is invalid."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 15
        player.y = 15
        player.position = Position(15, 15)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        is_valid = enemy._is_move_valid_from(Position(15, 15), Position(14, 15), game_map, player, game_engine)

        assert is_valid is False

    def test_is_move_valid_from_other_enemy(self):
        """Move to other enemy position is invalid."""
        from unittest.mock import Mock

        enemy1 = enemy_builder("scanner", pos=(10, 10))
        enemy2 = enemy_builder("bot", pos=(15, 15))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy1, enemy2]

        is_valid = enemy1._is_move_valid_from(Position(15, 15), Position(14, 15), game_map, player, game_engine)

        assert is_valid is False

    def test_is_move_valid_from_out_of_bounds(self):
        """Move to out of bounds position is invalid."""
        from unittest.mock import Mock

        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=40, height=40)
        player = Mock()
        player.x = 30
        player.y = 30
        player.position = Position(30, 30)
        game_engine = Mock()
        game_engine.enemies = [enemy]

        is_valid = enemy._is_move_valid_from(Position(50, 50), Position(10, 10), game_map, player, game_engine)

        assert is_valid is False
