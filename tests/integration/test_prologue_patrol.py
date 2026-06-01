#!/usr/bin/env python3
"""
Regression test for prologue patrol motion.

The first prologue patrol (Section 2) oscillates between two waypoints,
(7,6) and (10,6). A bug in waypoint advancement + move-queue management made
it overshoot and jerk back at each endpoint (a visible "double-tap" turnaround),
so it read like the patrol had a phantom third waypoint. This test pins clean
back-and-forth motion: the patrol only ever reverses direction AT an endpoint.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from rsp.core.engine import GameEngine
from rsp.entities.base import EnemyMovement, EnemyState, Position
from rsp.entities.characters import Enemy, Player
from rsp.level.map import GameMap


@pytest.fixture
def open_map():
    """Open, fully walkable map matching the prologue dimensions."""
    game_map = Mock(spec=GameMap)
    game_map.width = 28
    game_map.height = 24
    game_map.is_wall.return_value = False
    game_map.is_blind_spot.return_value = False
    game_map.can_see_position.return_value = True
    game_map.get_walkability_map.return_value = np.ones((24, 28), dtype=np.int32)
    game_map._compute_fov_cached.return_value = np.ones((24, 28), dtype=bool)
    return game_map


def _run_patrol(open_map, waypoints, spawn, turns=16):
    """Spawn a UNAWARE patrol on the given route and return the x-position sequence."""
    with patch(
        "rsp.core.data.GameData.ENEMY_TYPES",
        {
            "patrol": Mock(
                movement=EnemyMovement.PATROL,
                cpu=50,
                vision=4,
                damage=10,
                name="Patrol",
                max_cpu=50,
            )
        },
    ):
        engine = Mock(spec=GameEngine)
        engine.game_map = open_map
        # Player parked far away so the patrol never goes HOSTILE.
        player = Player(1, 1)
        engine.player = player

        patrol = Enemy(Position(*spawn), "patrol")
        patrol.patrol_points = [Position(x, y) for x, y in waypoints]
        patrol.patrol_index = 0
        patrol.state = EnemyState.UNAWARE
        engine.enemies = [patrol]

        seq = [int(patrol.x)]
        for _ in range(turns):
            patrol.move(open_map, player, engine)
            seq.append(int(patrol.x))
        return seq


def _assert_no_phantom_turnaround(seq, lo, hi):
    """Every direction reversal must occur exactly at an endpoint (lo or hi)."""
    for i in range(1, len(seq) - 1):
        prev, cur, nxt = seq[i - 1], seq[i], seq[i + 1]
        reversed_dir = (cur - prev) * (nxt - cur) < 0
        if reversed_dir:
            assert cur in (lo, hi), (
                f"patrol reversed direction at x={cur} (not an endpoint); "
                f"sequence={seq}"
            )


class TestPrologueFirstPatrol:
    """Section 2 patrol: sweeps between waypoints (3,6) and (10,6)."""

    def test_clean_oscillation_between_endpoints(self, open_map):
        seq = _run_patrol(open_map, waypoints=[(3, 6), (10, 6)], spawn=(3, 6), turns=24)

        # Reaches both endpoints (full intended range).
        assert 3 in seq, f"patrol never reached left endpoint x=3; sequence={seq}"
        assert 10 in seq, f"patrol never reached right endpoint x=10; sequence={seq}"

        # Stays within the route.
        assert all(3 <= x <= 10 for x in seq), f"patrol left its route; sequence={seq}"

        # No phantom turnaround / double-tap mid-route.
        _assert_no_phantom_turnaround(seq, lo=3, hi=10)

    def test_no_immediate_endpoint_double_tap(self, open_map):
        """The specific bug: stutter (e.g. x=10,9,10 or x=3,4,3) at the turnaround."""
        seq = _run_patrol(open_map, waypoints=[(3, 6), (10, 6)], spawn=(3, 6), turns=24)
        for i in range(len(seq) - 2):
            assert not (seq[i] == seq[i + 2] and seq[i] in (3, 10)), (
                f"endpoint double-tap at index {i} (x={seq[i]}); sequence={seq}"
            )

    def test_prediction_matches_actual_motion(self, open_map):
        """The 3-move prediction (move_queue) must equal where the patrol actually goes.

        The player reads move_queue[:3] to plan. If the predicted moves diverge from
        actual motion (e.g. near a turnaround), the prediction is misleading.
        """
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"patrol": Mock(movement=EnemyMovement.PATROL, cpu=50, vision=4, damage=10,
                            name="Patrol", max_cpu=50)},
        ):
            engine = Mock(spec=GameEngine)
            engine.game_map = open_map
            player = Player(1, 1)
            engine.player = player
            patrol = Enemy(Position(3, 6), "patrol")
            patrol.patrol_points = [Position(3, 6), Position(10, 6)]
            patrol.patrol_index = 0
            patrol.state = EnemyState.UNAWARE
            engine.enemies = [patrol]

            positions = [(patrol.x, patrol.y)]
            predictions = []
            for _ in range(24):
                predictions.append([(p.x, p.y) for p in patrol.move_queue[:3]])
                patrol.move(open_map, player, engine)
                positions.append((patrol.x, patrol.y))

            for t, pred in enumerate(predictions):
                if not pred:
                    continue  # queue not yet warmed up
                actual_next = positions[t + 1 : t + 1 + len(pred)]
                if len(actual_next) < len(pred):
                    continue  # prediction window runs past the end of the recording
                assert pred == actual_next, (
                    f"prediction at turn {t} = {pred} but actual motion = {actual_next}; "
                    f"positions={positions}"
                )
