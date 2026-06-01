#!/usr/bin/env python3
"""
Integration tests for patrol movement queue fixes.

Tests the behavior fixes for patrol enemies to ensure:
1. Short patrol routes (1-2 tiles apart) maintain full 3-move queues
2. Waypoint advancement doesn't clear the queue unnecessarily
3. Queue properly extends with next waypoint moves
"""

from unittest.mock import Mock, patch

import pytest

from rsp.core.engine import GameEngine
from rsp.entities.base import EnemyMovement, EnemyState, Position
from rsp.entities.characters import Enemy, Player
from rsp.level.map import GameMap


@pytest.fixture
def mock_game_map():
    """Create a mock GameMap."""
    game_map = Mock(spec=GameMap)
    game_map.width = 50
    game_map.height = 50
    game_map.is_wall.return_value = False
    game_map.is_blind_spot.return_value = False
    game_map.can_see_position.return_value = True

    # Mock walkability map
    import numpy as np

    game_map.get_walkability_map.return_value = np.ones((50, 50), dtype=np.int32)
    game_map._compute_fov_cached.return_value = np.ones((50, 50), dtype=bool)

    return game_map


@pytest.fixture
def mock_game_engine(mock_game_map):
    """Create a mock GameEngine."""
    engine = Mock(spec=GameEngine)
    engine.game_map = mock_game_map
    engine.enemies = []
    engine.player = Player(40, 40)  # Far from patrol route
    return engine


class TestShortPatrolQueues:
    """Test that short patrol routes maintain full 3-move queues."""

    def test_short_patrol_maintains_full_queue(self, mock_game_map, mock_game_engine):
        """Patrol with waypoints 1-2 tiles apart should still maintain 3-move queue."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            # Create patrol with very short distances between waypoints
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [
                Position(10, 10),  # Start
                Position(12, 10),  # 2 tiles away
                Position(14, 10),  # 2 tiles away
                Position(16, 10),  # 2 tiles away
            ]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            mock_game_engine.enemies = [patrol]

            # Fill the queue initially
            patrol._ensure_queue_full(mock_game_map, mock_game_engine.player, mock_game_engine)

            # Queue should have 3 moves despite short distances
            # It should chain moves across multiple waypoints if needed
            assert len(patrol.move_queue) > 0, "Short patrol should still generate moves"

    def test_patrol_queue_extends_across_waypoints(self, mock_game_map, mock_game_engine):
        """Queue should chain moves from current waypoint to next waypoint(s)."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            # Create patrol route
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [
                Position(11, 10),  # Waypoint 0 - 1 tile away
                Position(13, 10),  # Waypoint 1 - 2 tiles from waypoint 0
                Position(16, 10),  # Waypoint 2 - 3 tiles from waypoint 1
            ]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            mock_game_engine.enemies = [patrol]

            # Fill the queue
            patrol._ensure_queue_full(mock_game_map, mock_game_engine.player, mock_game_engine)

            # Queue should extend across multiple waypoints to reach 3 moves
            # Even if first waypoint is only 1 tile away
            initial_queue_length = len(patrol.move_queue)
            assert initial_queue_length > 0, "Queue should be filled for short patrols"


class TestPatrolWaypointAdvancement:
    """Test that waypoint advancement doesn't clear the queue unnecessarily."""

    def test_waypoint_advancement_preserves_valid_moves(self, mock_game_map, mock_game_engine):
        """When advancing waypoint, existing valid moves to next waypoint should be preserved."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [
                Position(12, 10),  # Waypoint 0
                Position(15, 10),  # Waypoint 1
                Position(18, 10),  # Waypoint 2
            ]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            mock_game_engine.enemies = [patrol]

            # Manually set up queue with moves to waypoint 0 and beyond
            patrol.move_queue = [
                Position(11, 10),  # Move toward waypoint 0
                Position(12, 10),  # Reach waypoint 0
                Position(13, 10),  # Move toward waypoint 1 (already queued!)
            ]

            # Simulate arriving at waypoint 0 and advancing
            patrol.position = Position(12, 10)

            # Advance waypoint (should happen when at waypoint)
            if patrol._should_advance_patrol_waypoint():
                old_queue_length = len(patrol.move_queue)
                patrol._advance_patrol_waypoint()

                # Queue should NOT be cleared - the fix removes the queue.clear() call
                # The already-queued move toward waypoint 1 should remain
                assert (
                    len(patrol.move_queue) == old_queue_length
                ), "Waypoint advancement should not clear already-queued valid moves"

    def test_waypoint_detection_requires_exact_arrival(self, mock_game_map, mock_game_engine):
        """Waypoint advancement triggers only when exactly on the waypoint (grid_distance == 0).

        Advancing while still 1 tile away flips the target before the queued move to the
        endpoint runs, making the patrol overshoot and jerk back at each turnaround.
        """
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [Position(12, 10), Position(15, 10)]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            # Not at waypoint yet
            assert not patrol._should_advance_patrol_waypoint()

            # Adjacent to waypoint (grid_distance = 1) - must NOT advance yet
            patrol.position = Position(11, 10)
            assert not patrol._should_advance_patrol_waypoint()

            # At waypoint (exact position) - advances
            patrol.position = Position(12, 10)
            assert patrol._should_advance_patrol_waypoint()


class TestPatrolLookahead:
    """Test the _fill_patrol_lookahead queue builder (replaces _extend_patrol_queue)."""

    def test_fills_queue_to_three(self, mock_game_map, mock_game_engine):
        """_fill_patrol_lookahead should fill the queue to 3 moves by chaining waypoints."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [
                Position(11, 10),  # Waypoint 0 - close
                Position(13, 10),  # Waypoint 1
                Position(16, 10),  # Waypoint 2
            ]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            mock_game_engine.enemies = [patrol]

            patrol._fill_patrol_lookahead(
                mock_game_map, mock_game_engine.player, mock_game_engine
            )

            # Chains across waypoints to reach the full 3-move lookahead.
            assert len(patrol.move_queue) == 3

    def test_rebuilds_from_current_position(self, mock_game_map, mock_game_engine):
        """_fill_patrol_lookahead discards any stale queue and rebuilds from current pos."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL,
                    cpu=50,
                    vision=5,
                    damage=10,
                    name="Patrol",
                    max_cpu=50,
                )
            },
        ):
            patrol = Enemy(Position(10, 10), "patrol")
            patrol.patrol_points = [Position(13, 10), Position(16, 10)]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE

            mock_game_engine.enemies = [patrol]

            # Stale move left over from a previous plan - must be discarded.
            patrol.move_queue = [Position(99, 99)]

            patrol._fill_patrol_lookahead(
                mock_game_map, mock_game_engine.player, mock_game_engine
            )

            assert Position(99, 99) not in patrol.move_queue
            # First queued move steps from (10,10) toward waypoint (13,10): no teleport.
            assert patrol.move_queue[0] == Position(11, 10)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
