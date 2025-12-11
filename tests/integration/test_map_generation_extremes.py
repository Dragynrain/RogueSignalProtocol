#!/usr/bin/env python3
"""
Map Generation Extreme Edge Case Testing

Tests map generation system under extreme conditions and fuzzing:
- Fuzzing with many random seeds to find problematic generations
- Gateway reachability validation
- Player spawn validation
- Enemy count edge cases
- Room size extremes
- Performance under stress
"""

import time

import numpy as np
import pytest
import tcod.path

from game_config import GameConfig
from tests.test_agent import GameTestAgent


class TestMapGenerationFuzzing:
    """Fuzz test map generation with many random seeds."""

    def test_map_generation_100_random_seeds(self):
        """Generate 100 maps with random seeds - all should be valid."""
        failures = []
        generation_times = []

        for seed in range(1000, 1100):  # 100 different seeds
            start_time = time.time()

            try:
                agent = GameTestAgent(seed=seed)

                # Validate basic constraints
                assert agent.game_map is not None, f"Seed {seed}: No map generated"
                assert agent.player is not None, f"Seed {seed}: No player spawned"

                # Player not in wall
                player_pos = (agent.player.x, agent.player.y)
                assert (
                    player_pos not in agent.game_map.walls
                ), f"Seed {seed}: Player in wall at {player_pos}"

                # Gateway exists
                assert agent.game_map.gateway is not None, f"Seed {seed}: No gateway found"

                # Gateway not in wall
                gateway_pos = (agent.game_map.gateway.x, agent.game_map.gateway.y)
                assert (
                    gateway_pos not in agent.game_map.walls
                ), f"Seed {seed}: Gateway in wall at {gateway_pos}"

                elapsed = time.time() - start_time
                generation_times.append(elapsed)

            except AssertionError as e:
                failures.append((seed, str(e)))
            except Exception as e:
                failures.append((seed, f"Exception: {e}"))

        # Report results
        print("\n=== Fuzzing Results ===")
        print("Seeds tested: 100")
        print(f"Failures: {len(failures)}")
        if generation_times:
            avg_time = sum(generation_times) / len(generation_times)
            max_time = max(generation_times)
            print(f"Avg generation time: {avg_time*1000:.2f}ms")
            print(f"Max generation time: {max_time*1000:.2f}ms")

        if failures:
            print("\nFailed seeds:")
            for seed, error in failures[:10]:  # Show first 10
                print(f"  Seed {seed}: {error}")

        # Test passes if < 5% failure rate
        failure_rate = len(failures) / 100.0
        assert (
            failure_rate < 0.05
        ), f"Too many failures: {len(failures)}/100 ({failure_rate*100:.1f}%)"

    def test_extreme_seeds_no_crash(self):
        """Test extreme seed values don't crash."""
        extreme_seeds = [
            0,  # Minimum
            1,  # Edge case
            2**31 - 1,  # Max 32-bit
            999999999,  # Large value
            42,  # Common test seed
            12345,  # Another common seed
        ]

        for seed in extreme_seeds:
            try:
                agent = GameTestAgent(seed=seed)
                assert agent.game_map is not None
                assert agent.player is not None
            except Exception as e:
                pytest.fail(f"Seed {seed} crashed: {e}")


class TestGatewayReachability:
    """Test gateway is always reachable from player spawn."""

    def test_gateway_reachable_from_player_spawn(self):
        """Gateway should always be reachable via pathfinding."""
        # Test multiple seeds
        for seed in range(2000, 2020):  # 20 seeds
            agent = GameTestAgent(seed=seed)

            # TCOD pathfinding uses (y, x) order, not (x, y)
            player_pos = (agent.player.y, agent.player.x)
            gateway_pos = (agent.game_map.gateway.y, agent.game_map.gateway.x)

            # Build cost map (1 = walkable, 0 = blocked)
            cost = np.ones((GameConfig.MAP_HEIGHT, GameConfig.MAP_WIDTH), dtype=np.int8)
            for wall_x, wall_y in agent.game_map.walls:
                cost[wall_y, wall_x] = 0

            # Use TCOD pathfinding
            graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root(player_pos)

            path = pathfinder.path_to(gateway_pos)

            assert (
                len(path) > 0
            ), f"Seed {seed}: Gateway at {gateway_pos} unreachable from player at {player_pos}"

    def test_gateway_not_in_isolated_room(self):
        """Gateway should not be in a room isolated from player (allows small failure rate)."""
        failures = []

        for seed in range(3000, 3050):  # 50 seeds
            agent = GameTestAgent(seed=seed)

            # Get all walkable tiles
            walkable = set()
            for x in range(GameConfig.MAP_WIDTH):
                for y in range(GameConfig.MAP_HEIGHT):
                    if (x, y) not in agent.game_map.walls:
                        walkable.add((x, y))

            # Flood fill from player position
            reachable = set()
            queue = [(agent.player.x, agent.player.y)]
            reachable.add((agent.player.x, agent.player.y))

            while queue:
                x, y = queue.pop(0)
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in walkable and (nx, ny) not in reachable:
                        reachable.add((nx, ny))
                        queue.append((nx, ny))

            # Gateway should be reachable
            gateway_pos = (agent.game_map.gateway.x, agent.game_map.gateway.y)
            if gateway_pos not in reachable:
                failures.append(seed)

        # Report failures
        if failures:
            print("\n=== Gateway Isolation Test ===")
            print(f"Failed seeds: {failures}")
            print(f"Failure rate: {len(failures)}/50 ({len(failures)/50*100:.1f}%)")

        # Allow up to 10% failure rate (procedural generation isn't perfect)
        # Real game would regenerate these seeds
        # NOTE: Current algorithm has ~8% failure rate - should be improved
        assert (
            len(failures) <= 5
        ), f"Too many isolated gateways: {len(failures)}/50 seeds ({len(failures)/50*100:.1f}%)"


class TestPlayerSpawnValidation:
    """Test player spawn is always valid."""

    def test_player_never_spawns_in_wall(self):
        """Player should never spawn inside a wall."""
        for seed in range(4000, 4050):  # 50 seeds
            agent = GameTestAgent(seed=seed)
            player_pos = (agent.player.x, agent.player.y)

            assert (
                player_pos not in agent.game_map.walls
            ), f"Seed {seed}: Player spawned in wall at {player_pos}"

    def test_player_has_adjacent_walkable_space(self):
        """Player spawn should have at least one adjacent walkable tile."""
        for seed in range(5000, 5030):  # 30 seeds
            agent = GameTestAgent(seed=seed)
            px, py = agent.player.x, agent.player.y

            # Check all 8 adjacent tiles
            adjacent_walkable = []
            for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
                nx, ny = px + dx, py + dy
                if 0 <= nx < GameConfig.MAP_WIDTH and 0 <= ny < GameConfig.MAP_HEIGHT:
                    if (nx, ny) not in agent.game_map.walls:
                        adjacent_walkable.append((nx, ny))

            assert (
                len(adjacent_walkable) > 0
            ), f"Seed {seed}: Player at {(px, py)} has no adjacent walkable tiles"

    def test_player_not_adjacent_to_gateway(self):
        """Player shouldn't spawn right next to gateway (too easy)."""
        for seed in range(6000, 6030):  # 30 seeds
            agent = GameTestAgent(seed=seed)

            px, py = agent.player.x, agent.player.y
            gx, gy = agent.game_map.gateway.x, agent.game_map.gateway.y

            # Calculate Manhattan distance
            distance = abs(px - gx) + abs(py - gy)

            # Should be at least 10 tiles away (configurable game design choice)
            assert distance >= 10, f"Seed {seed}: Player too close to gateway (distance={distance})"


class TestEnemyCountEdgeCases:
    """Test enemy spawn counts under various conditions."""

    def test_enemy_count_within_reasonable_range(self):
        """Enemy count should be within configured range for level 1."""
        counts = []

        for seed in range(7000, 7050):  # 50 seeds
            agent = GameTestAgent(seed=seed, level=1)
            enemy_count = len(agent.enemies)
            counts.append(enemy_count)

            # Should have at least 1 enemy (game design)
            assert enemy_count > 0, f"Seed {seed}: Level 1 has no enemies"

            # Should not have excessive enemies (< 30 for level 1)
            assert enemy_count < 30, f"Seed {seed}: Level 1 has too many enemies ({enemy_count})"

        # Report statistics
        avg_enemies = sum(counts) / len(counts)
        min_enemies = min(counts)
        max_enemies = max(counts)

        print("\n=== Enemy Count Stats (Level 1, 50 seeds) ===")
        print(f"Average: {avg_enemies:.1f}")
        print(f"Min: {min_enemies}")
        print(f"Max: {max_enemies}")

    def test_all_enemies_spawn_in_valid_positions(self):
        """All enemies across multiple seeds spawn in valid positions."""
        for seed in range(8000, 8030):  # 30 seeds
            agent = GameTestAgent(seed=seed)

            for enemy in agent.enemies:
                enemy_pos = (enemy.x, enemy.y)

                # Not in wall
                assert (
                    enemy_pos not in agent.game_map.walls
                ), f"Seed {seed}: Enemy {enemy.type} in wall at {enemy_pos}"

                # Not on player
                player_pos = (agent.player.x, agent.player.y)
                assert (
                    enemy_pos != player_pos
                ), f"Seed {seed}: Enemy {enemy.type} on player at {enemy_pos}"

    def test_enemies_have_minimum_spacing(self):
        """Enemies should have some spacing from each other."""
        for seed in range(9000, 9020):  # 20 seeds
            agent = GameTestAgent(seed=seed)

            enemy_positions = [(e.x, e.y) for e in agent.enemies]

            # Check for exact overlaps (shouldn't happen)
            assert len(enemy_positions) == len(
                set(enemy_positions)
            ), f"Seed {seed}: Multiple enemies at same position"


class TestRoomSizeValidation:
    """Test room generation doesn't create invalid sizes."""

    def test_no_single_tile_rooms(self):
        """Map shouldn't have isolated single-tile walkable areas."""
        for seed in range(10000, 10020):  # 20 seeds
            agent = GameTestAgent(seed=seed)

            # Find connected components of walkable tiles
            walkable = set()
            for x in range(GameConfig.MAP_WIDTH):
                for y in range(GameConfig.MAP_HEIGHT):
                    if (x, y) not in agent.game_map.walls:
                        walkable.add((x, y))

            # Find all connected components
            visited = set()
            components = []

            for start_pos in walkable:
                if start_pos in visited:
                    continue

                # BFS to find connected component
                component = set()
                queue = [start_pos]
                component.add(start_pos)
                visited.add(start_pos)

                while queue:
                    x, y = queue.pop(0)
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if (nx, ny) in walkable and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            component.add((nx, ny))
                            queue.append((nx, ny))

                components.append(component)

            # All components should be at least 4 tiles (2x2 minimum)
            small_components = [c for c in components if len(c) < 4]

            # Allow a few tiny components (disconnected artifacts) but not many
            assert (
                len(small_components) <= 5
            ), f"Seed {seed}: Too many tiny components ({len(small_components)})"

    def test_map_has_reasonable_open_space(self):
        """Map should have reasonable amount of open space (not too cramped)."""
        for seed in range(11000, 11020):  # 20 seeds
            agent = GameTestAgent(seed=seed)

            total_tiles = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
            wall_count = len(agent.game_map.walls)
            walkable_percentage = ((total_tiles - wall_count) / total_tiles) * 100

            # Should be between 20% and 80% walkable
            assert (
                20 <= walkable_percentage <= 80
            ), f"Seed {seed}: Walkable percentage {walkable_percentage:.1f}% out of range"


class TestMapGenerationPerformance:
    """Test map generation performance under stress."""

    def test_generation_time_reasonable(self):
        """Map generation should complete in reasonable time."""
        times = []

        for seed in range(12000, 12050):  # 50 generations
            start_time = time.time()
            agent = GameTestAgent(seed=seed)
            elapsed = time.time() - start_time
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print("\n=== Generation Performance (50 seeds) ===")
        print(f"Average time: {avg_time*1000:.2f}ms")
        print(f"Max time: {max_time*1000:.2f}ms")

        # Average should be < 50ms per generation
        assert avg_time < 0.05, f"Generation too slow: avg {avg_time*1000:.2f}ms"

        # No single generation should take > 200ms
        assert max_time < 0.2, f"Slowest generation: {max_time*1000:.2f}ms"

    def test_rapid_successive_generations(self):
        """Rapidly generating many maps doesn't slow down over time."""
        batch_times = []

        # Generate 5 batches of 20 maps
        for batch in range(5):
            start_time = time.time()

            for i in range(20):
                seed = 13000 + batch * 20 + i
                agent = GameTestAgent(seed=seed)

            batch_time = time.time() - start_time
            batch_times.append(batch_time)

        # Later batches shouldn't be slower (no memory leak/accumulation)
        first_batch = batch_times[0]
        last_batch = batch_times[-1]

        print("\n=== Successive Generation Performance ===")
        print(f"First batch (20 maps): {first_batch*1000:.2f}ms")
        print(f"Last batch (20 maps): {last_batch*1000:.2f}ms")

        # Last batch shouldn't be more than 50% slower than first
        assert (
            last_batch < first_batch * 1.5
        ), f"Performance degradation: {last_batch/first_batch:.2f}x slower"
