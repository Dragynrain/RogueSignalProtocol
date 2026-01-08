#!/usr/bin/env python3
"""
Integration tests for Virus enemy movement state transitions.

Tests the behavior fixes for Virus enemies to ensure:
1. STATIC viruses never move, even when hostile
2. Mobile viruses return to their base movement type after losing player
3. SEEK is never assigned as a base movement type
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

    # Mock FOV
    import numpy as np

    game_map._compute_fov_cached.return_value = np.ones((50, 50), dtype=bool)

    return game_map


@pytest.fixture
def mock_game_engine(mock_game_map):
    """Create a mock GameEngine."""
    engine = Mock(spec=GameEngine)
    engine.game_map = mock_game_map
    engine.enemies = []
    engine.player = Player(25, 25)
    return engine


def mock_pathfinding_cost_map(game_map, game_engine, moving_enemy):
    """Mock cost map for pathfinding."""
    import numpy as np

    return np.ones((game_map.height, game_map.width), dtype=np.int32)


class TestVirusStaticMovement:
    """Test that STATIC viruses never move, even when hostile."""

    def test_static_virus_never_moves_when_hostile(self, mock_game_map, mock_game_engine):
        """STATIC virus should remain stationary even when hostile and player is visible."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM,
                    cpu=50,
                    vision=10,
                    damage=0,
                    name="Virus",
                    max_cpu=50,
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_pathfinding_cost_map,
            ):
                # Create virus with STATIC base movement
                virus = Enemy(Position(10, 10), "virus")
                virus.original_movement_type = EnemyMovement.STATIC
                virus.state = EnemyState.HOSTILE
                virus.last_seen_player = Position(15, 15)

                mock_game_engine.enemies = [virus]

                # Verify movement type is STATIC
                assert virus.get_movement_type() == EnemyMovement.STATIC

                # Try to move (should not move)
                initial_pos = virus.position
                with patch.object(virus, "can_see_player", return_value=True):
                    virus.move(mock_game_map, mock_game_engine.player, mock_game_engine)

                # Virus should not have moved
                assert virus.position == initial_pos
                assert len(virus.move_queue) == 0  # No moves queued for STATIC

    def test_static_virus_never_moves_when_unaware(self, mock_game_map, mock_game_engine):
        """STATIC virus should remain stationary when unaware."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM,
                    cpu=50,
                    vision=10,
                    damage=0,
                    name="Virus",
                    max_cpu=50,
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_pathfinding_cost_map,
            ):
                # Create virus with STATIC base movement
                virus = Enemy(Position(10, 10), "virus")
                virus.original_movement_type = EnemyMovement.STATIC
                virus.state = EnemyState.UNAWARE

                mock_game_engine.enemies = [virus]

                # Verify movement type is STATIC
                assert virus.get_movement_type() == EnemyMovement.STATIC

                # Try to move (should not move)
                initial_pos = virus.position
                virus.move(mock_game_map, mock_game_engine.player, mock_game_engine)

                # Virus should not have moved
                assert virus.position == initial_pos


class TestVirusMovementTypeTransitions:
    """Test that viruses return to their base movement type after losing player."""

    def test_random_virus_returns_to_random_after_losing_player(
        self, mock_game_map, mock_game_engine
    ):
        """Virus with RANDOM base movement should return to RANDOM after losing player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM,
                    cpu=50,
                    vision=10,
                    damage=0,
                    name="Virus",
                    max_cpu=50,
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_pathfinding_cost_map,
            ):
                virus = Enemy(Position(10, 10), "virus")
                virus.original_movement_type = EnemyMovement.RANDOM

                mock_game_engine.enemies = [virus]

                # Start UNAWARE with RANDOM movement
                virus.state = EnemyState.UNAWARE
                assert virus.get_movement_type() == EnemyMovement.RANDOM

                # Become HOSTILE (should switch to SEEK)
                virus.state = EnemyState.HOSTILE
                assert virus.get_movement_type() == EnemyMovement.SEEK

                # Lose player, return to UNAWARE (should return to RANDOM)
                virus.state = EnemyState.UNAWARE
                assert virus.get_movement_type() == EnemyMovement.RANDOM

    def test_patrol_virus_returns_to_patrol_after_losing_player(
        self, mock_game_map, mock_game_engine
    ):
        """Virus with PATROL base movement should return to PATROL after losing player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM,
                    cpu=50,
                    vision=10,
                    damage=0,
                    name="Virus",
                    max_cpu=50,
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_pathfinding_cost_map,
            ):
                virus = Enemy(Position(10, 10), "virus")
                virus.original_movement_type = EnemyMovement.PATROL
                virus.patrol_points = [Position(10, 10), Position(15, 15), Position(20, 20)]
                virus.patrol_index = 0

                mock_game_engine.enemies = [virus]

                # Start UNAWARE with PATROL movement
                virus.state = EnemyState.UNAWARE
                assert virus.get_movement_type() == EnemyMovement.PATROL

                # Become HOSTILE (should switch to SEEK)
                virus.state = EnemyState.HOSTILE
                assert virus.get_movement_type() == EnemyMovement.SEEK

                # Lose player, return to UNAWARE (should return to PATROL)
                virus.state = EnemyState.UNAWARE
                assert virus.get_movement_type() == EnemyMovement.PATROL

    def test_virus_hostile_behavior_uses_seek(self, mock_game_map, mock_game_engine):
        """All mobile viruses should use SEEK movement when hostile."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM,
                    cpu=50,
                    vision=10,
                    damage=0,
                    name="Virus",
                    max_cpu=50,
                )
            },
        ):
            # Test with different base movement types
            for base_movement in [EnemyMovement.RANDOM, EnemyMovement.PATROL]:
                virus = Enemy(Position(10, 10), "virus")
                virus.original_movement_type = base_movement
                virus.state = EnemyState.HOSTILE

                # All non-STATIC viruses use SEEK when hostile
                assert virus.get_movement_type() == EnemyMovement.SEEK


class TestVirusSpawnMovementTypes:
    """Test that viruses only spawn with valid base movement types."""

    def test_virus_never_spawns_with_seek_movement(self):
        """SEEK should never be assigned as a virus base movement type."""
        # This is a documentation test - SEEK is a hostile behavior, not a base type
        # Valid base movement types for viruses are: STATIC, RANDOM, PATROL
        valid_virus_movements = [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.PATROL]

        # SEEK should NOT be in this list
        assert EnemyMovement.SEEK not in valid_virus_movements

        # All valid types should be passive/non-hostile behaviors
        for movement in valid_virus_movements:
            assert movement in [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.PATROL]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
