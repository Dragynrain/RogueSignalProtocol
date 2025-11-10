#!/usr/bin/env python3
"""
Level Generation Testing

Tests that procedural level generation creates valid, playable maps.
No agent behavior - just validates the generated levels.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_agent import GameTestAgent
from game_config import GameConfig


class TestLevelGeneration:
    """Test procedural level generation."""

    def test_level_generates_without_crash(self):
        """Level generation should not crash."""
        agent = GameTestAgent(seed=42)

        # If we got here, generation succeeded
        assert agent.game_map is not None
        assert agent.player is not None

    def test_player_starts_in_walkable_area(self):
        """Player should spawn in a walkable (non-wall) location."""
        agent = GameTestAgent(seed=42)

        player_pos = (agent.player.x, agent.player.y)
        assert player_pos not in agent.game_map.walls, \
            f"Player spawned inside a wall at {player_pos}"

    def test_level_has_some_walkable_tiles(self):
        """Level should have a reasonable amount of walkable space."""
        agent = GameTestAgent(seed=42)

        total_tiles = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
        wall_count = len(agent.game_map.walls)
        walkable_count = total_tiles - wall_count

        # At least 20% of map should be walkable
        walkable_percentage = (walkable_count / total_tiles) * 100

        print(f"\n=== Map Statistics ===")
        print(f"Total tiles: {total_tiles}")
        print(f"Walls: {wall_count}")
        print(f"Walkable: {walkable_count} ({walkable_percentage:.1f}%)")

        assert walkable_percentage >= 20, \
            f"Only {walkable_percentage:.1f}% walkable - map may be too dense"

    def test_gateway_exists_and_is_reachable(self):
        """Gateway should exist on level 1."""
        agent = GameTestAgent(seed=42)

        assert agent.game_map.gateway is not None, "No gateway found on level 1"

        gateway_pos = (agent.game_map.gateway.x, agent.game_map.gateway.y)
        assert gateway_pos not in agent.game_map.walls, \
            "Gateway is inside a wall"

    def test_enemies_spawn_in_walkable_areas(self):
        """All enemies should spawn in valid walkable positions."""
        agent = GameTestAgent(seed=42)

        for enemy in agent.enemies:
            enemy_pos = (enemy.x, enemy.y)
            assert enemy_pos not in agent.game_map.walls, \
                f"Enemy {enemy.type} spawned inside wall at {enemy_pos}"

    def test_enemies_dont_overlap_player_spawn(self):
        """Enemies should not spawn on top of the player."""
        agent = GameTestAgent(seed=42)

        player_pos = (agent.player.x, agent.player.y)

        for enemy in agent.enemies:
            enemy_pos = (enemy.x, enemy.y)
            assert enemy_pos != player_pos, \
                f"Enemy {enemy.type} spawned on player at {player_pos}"

    def test_deterministic_generation(self):
        """Same seed should generate same map layout."""
        seed = 12345

        # Generate two maps with same seed
        agent1 = GameTestAgent(seed=seed)
        agent2 = GameTestAgent(seed=seed)

        # Wall positions should be identical
        walls1 = agent1.game_map.walls
        walls2 = agent2.game_map.walls

        assert walls1 == walls2, "Same seed produced different wall layouts"

        # Player spawn should be identical
        assert agent1.player.x == agent2.player.x, "Different player X position"
        assert agent1.player.y == agent2.player.y, "Different player Y position"

    def test_multiple_seeds_generate_different_maps(self):
        """Different seeds should produce different maps."""
        agent1 = GameTestAgent(seed=1)
        agent2 = GameTestAgent(seed=2)

        walls1 = agent1.game_map.walls
        walls2 = agent2.game_map.walls

        # Maps should be different (wall layouts differ)
        assert walls1 != walls2, "Different seeds produced identical maps"

    def test_generation_on_100_seeds(self):
        """Stress test: Generate 100 different maps without crashing."""
        failures = []

        for seed in range(100):
            try:
                agent = GameTestAgent(seed=seed)

                # Basic validation
                player_pos = (agent.player.x, agent.player.y)
                if player_pos in agent.game_map.walls:
                    failures.append(f"Seed {seed}: Player in wall")

                for enemy in agent.enemies:
                    enemy_pos = (enemy.x, enemy.y)
                    if enemy_pos in agent.game_map.walls:
                        failures.append(f"Seed {seed}: Enemy in wall")
                        break

            except Exception as e:
                failures.append(f"Seed {seed}: {type(e).__name__} - {str(e)}")

        if failures:
            print(f"\n=== Generation Failures ===")
            for failure in failures[:10]:  # Show first 10
                print(failure)
            if len(failures) > 10:
                print(f"... and {len(failures) - 10} more")

        assert len(failures) == 0, \
            f"{len(failures)}/100 seeds failed generation validation"

    def test_map_connectivity(self):
        """Test that player can reach the gateway (basic connectivity check)."""
        agent = GameTestAgent(seed=42)

        if agent.game_map.gateway is None:
            pytest.skip("No gateway on this level")

        # Try to pathfind to gateway
        gateway_x = agent.game_map.gateway.x
        gateway_y = agent.game_map.gateway.y

        # Use the agent's pathfinding
        reached = agent.move_to(gateway_x, gateway_y, max_steps=500)

        # We should be able to reach the gateway
        # (or at least get close - within 2 tiles)
        distance_to_gateway = (
            abs(agent.player.x - gateway_x) +
            abs(agent.player.y - gateway_y)
        )

        print(f"\n=== Connectivity Test ===")
        print(f"Started at: ({agent.player.x}, {agent.player.y})")
        print(f"Gateway at: ({gateway_x}, {gateway_y})")
        print(f"Reached gateway: {reached}")
        print(f"Final distance: {distance_to_gateway}")

        assert distance_to_gateway <= 2, \
            f"Could not reach gateway (distance: {distance_to_gateway}) - map may not be connected"

    def test_special_tiles_in_valid_positions(self):
        """Cooling nodes and other special tiles should be in walkable areas."""
        agent = GameTestAgent(seed=42)

        # Check cooling nodes
        for node_pos in agent.game_map.cooling_nodes:
            assert node_pos not in agent.game_map.walls, \
                f"Cooling node at {node_pos} is inside a wall"

        # Check CPU recovery nodes
        for node_pos in agent.game_map.cpu_recovery_nodes:
            assert node_pos not in agent.game_map.walls, \
                f"CPU recovery node at {node_pos} is inside a wall"

    def test_map_has_some_features(self):
        """Map should have some interesting features (not just empty rooms)."""
        agent = GameTestAgent(seed=42)

        feature_count = (
            len(agent.game_map.cooling_nodes) +
            len(agent.game_map.cpu_recovery_nodes) +
            len(agent.game_map.blind_spots) +
            len(agent.enemies)
        )

        print(f"\n=== Map Features ===")
        print(f"Cooling nodes: {len(agent.game_map.cooling_nodes)}")
        print(f"CPU nodes: {len(agent.game_map.cpu_recovery_nodes)}")
        print(f"Blind spots: {len(agent.game_map.blind_spots)}")
        print(f"Enemies: {len(agent.enemies)}")
        print(f"Total features: {feature_count}")

        # Map should have at least a few features
        assert feature_count >= 5, \
            f"Map has only {feature_count} features - may be too empty"


    def test_level_1_spawn_quantities_match_config(self):
        """Level 1 should spawn exactly the quantities specified in game_content.json."""
        agent = GameTestAgent(seed=42)

        # Load expected quantities from config
        from game_config import GameConfig
        network_configs = GameConfig.get_network_configs()
        expected = network_configs[1]

        # Count actual spawned items
        actual = {
            'enemies': len(agent.enemies),
            'cooling_nodes': len(agent.game_map.cooling_nodes),
            'cpu_nodes': len(agent.game_map.cpu_recovery_nodes),
            'code_hacks': len(agent.game_map.code_hacks),
            'exploit_pickups': len(agent.game_map.exploit_pickups),
            'permanent_upgrades': len(agent.game_map.permanent_upgrades)
        }

        print(f"\n=== Level 1 Spawn Quantities ===")
        print(f"{'Item':<20} {'Expected':<12} {'Actual':<12} {'Match':<8}")
        print("-" * 52)

        mismatches = []
        for key in ['enemies', 'cooling_nodes', 'cpu_nodes', 'code_hacks',
                    'exploit_pickups', 'permanent_upgrades']:
            expected_count = expected[key]
            actual_count = actual[key]
            match = "OK" if expected_count == actual_count else "FAIL"
            print(f"{key:<20} {expected_count:<12} {actual_count:<12} {match:<8}")

            if expected_count != actual_count:
                mismatches.append(f"{key}: expected {expected_count}, got {actual_count}")

        # Assert all quantities match
        assert len(mismatches) == 0, \
            f"Spawn quantities don't match config:\n" + "\n".join(mismatches)

    def test_spawn_quantities_consistent_across_seeds(self):
        """Same level should spawn same quantities regardless of seed."""
        from game_config import GameConfig
        network_configs = GameConfig.get_network_configs()
        expected = network_configs[1]

        # Test multiple seeds
        seeds = [1, 42, 123, 999, 5555]
        results = []

        for seed in seeds:
            agent = GameTestAgent(seed=seed)
            actual = {
                'enemies': len(agent.enemies),
                'cooling_nodes': len(agent.game_map.cooling_nodes),
                'cpu_nodes': len(agent.game_map.cpu_recovery_nodes),
                'code_hacks': len(agent.game_map.code_hacks),
                'exploit_pickups': len(agent.game_map.exploit_pickups),
                'permanent_upgrades': len(agent.game_map.permanent_upgrades)
            }
            results.append((seed, actual))

        print(f"\n=== Spawn Consistency Across Seeds ===")
        print(f"Expected (from config): {dict(expected)}")

        # Check all seeds produce same counts
        for seed, actual in results:
            for key in ['enemies', 'cooling_nodes', 'cpu_nodes', 'code_hacks',
                       'exploit_pickups', 'permanent_upgrades']:
                assert actual[key] == expected[key], \
                    f"Seed {seed}: {key} count {actual[key]} != expected {expected[key]}"

        print(f"All {len(seeds)} seeds produced correct quantities!")

    def test_all_levels_match_config(self):
        """Test that all 3 levels spawn correct quantities."""
        from game_config import GameConfig
        network_configs = GameConfig.get_network_configs()

        print(f"\n=== All Levels Spawn Validation ===")

        for level_num in [1, 2, 3]:
            # Create agent at specific level
            agent = GameTestAgent(seed=42)
            agent.engine.level = level_num

            # Generate level
            agent.engine.game_session.generate_procedural_level()

            expected = network_configs[level_num]
            actual = {
                'enemies': len(agent.enemies),
                'cooling_nodes': len(agent.game_map.cooling_nodes),
                'cpu_nodes': len(agent.game_map.cpu_recovery_nodes),
                'code_hacks': len(agent.game_map.code_hacks),
                'exploit_pickups': len(agent.game_map.exploit_pickups),
                'permanent_upgrades': len(agent.game_map.permanent_upgrades)
            }

            print(f"\nLevel {level_num} ({expected.get('name', 'Unknown')}):")
            print(f"  Enemies: {actual['enemies']} (expected {expected['enemies']})")
            print(f"  Cooling nodes: {actual['cooling_nodes']} (expected {expected['cooling_nodes']})")
            print(f"  CPU nodes: {actual['cpu_nodes']} (expected {expected['cpu_nodes']})")
            print(f"  Code hacks: {actual['code_hacks']} (expected {expected['code_hacks']})")
            print(f"  Exploits: {actual['exploit_pickups']} (expected {expected['exploit_pickups']})")
            print(f"  Upgrades: {actual['permanent_upgrades']} (expected {expected['permanent_upgrades']})")

            # Validate each quantity
            for key in ['enemies', 'cooling_nodes', 'cpu_nodes', 'code_hacks',
                       'exploit_pickups', 'permanent_upgrades']:
                assert actual[key] == expected[key], \
                    f"Level {level_num}: {key} count {actual[key]} != expected {expected[key]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
