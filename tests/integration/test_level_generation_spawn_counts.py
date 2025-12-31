#!/usr/bin/env python3
"""
Integration test for level generation spawn counts.

Verifies that procedurally generated levels spawn the correct number of
special nodes and items as defined in game_content.json network_configs.

Tests all 3 levels with multiple random seeds to ensure consistency.
"""

import logging
import random

import pytest

from rsp.core.config import GameConfig
from rsp.core.session import GameSession
from tests.fixtures.quick_fixtures import quick_engine


@pytest.mark.parametrize("level", [1, 2, 3])
def test_level_spawn_counts(level):
    """Verify each level spawns correct counts across multiple seeds."""
    _verify_level_spawn_counts(level=level, seeds=[42, 123, 999])


def _verify_level_spawn_counts(level: int, seeds: list):
    """
    Verify spawn counts for a specific level across multiple seeds.

    Args:
        level: Level number (1, 2, or 3)
        seeds: List of random seeds to test with
    """
    # Get expected counts from config
    network_configs = GameConfig.get_network_configs()
    assert level in network_configs, f"Level {level} not found in network_configs"

    config = network_configs[level]
    expected = {
        "cooling_nodes": config["cooling_nodes"],
        "cpu_nodes": config["cpu_nodes"],
        "ghost_nodes": config["ghost_nodes"],
        "code_hacks": config["code_hacks"],
        "exploit_pickups": config["exploit_pickups"],
        "permanent_upgrades": config["permanent_upgrades"],
    }

    # Test with multiple seeds
    for seed in seeds:
        random.seed(seed)

        # Create game engine and session, then generate level
        engine = quick_engine(load_save=False)
        engine.level = level  # Set engine level for generation
        session = GameSession(engine)
        session.level = level  # Set session level for consistency
        session.generate_procedural_level()

        game_map = engine.game_map

        # Count actual spawned items
        actual = {
            "cooling_nodes": len(game_map.cooling_nodes),
            "cpu_nodes": len(game_map.cpu_recovery_nodes),
            "ghost_nodes": len(game_map.ghost_nodes),
            "code_hacks": len(game_map.code_hacks),
            "exploit_pickups": len(game_map.exploit_pickups),
            "permanent_upgrades": len(game_map.permanent_upgrades),
        }

        # Verify each count matches
        for item_type, expected_count in expected.items():
            actual_count = actual[item_type]
            assert actual_count == expected_count, (
                f"Level {level} seed {seed}: {item_type} mismatch - "
                f"Expected: {expected_count}, Actual: {actual_count}"
            )

        # Verify gateway doesn't overlap with special nodes
        gateway_pos = (game_map.gateway.x, game_map.gateway.y)
        overlapping_nodes = []
        if gateway_pos in game_map.cooling_nodes:
            overlapping_nodes.append("cooling_node")
        if gateway_pos in game_map.cpu_recovery_nodes:
            overlapping_nodes.append("cpu_recovery_node")
        if gateway_pos in game_map.ghost_nodes:
            overlapping_nodes.append("ghost_node")

        assert not overlapping_nodes, (
            f"Level {level} seed {seed}: Gateway at {gateway_pos} overlaps with: "
            f"{', '.join(overlapping_nodes)}"
        )

        logging.info(f"Level {level} seed {seed}: All spawn counts match [OK]")


if __name__ == "__main__":
    # Run tests manually
    logging.basicConfig(level=logging.INFO)

    for level in [1, 2, 3]:
        print(f"Testing Level {level} spawn counts...")
        test_level_spawn_counts(level)
        print(f"[OK] Level {level}\n")

    print("All level generation spawn count tests passed!")
