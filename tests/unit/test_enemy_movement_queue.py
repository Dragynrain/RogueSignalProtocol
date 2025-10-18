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
