#!/usr/bin/env python3
"""
Exploration Agent - Goal-Oriented Testing

Smart agent that tries to explore the entire map.
Tests pathfinding, FOV, and map generation.
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_agent import GameTestAgent
from game_entities import Position
from game_characters import PathfindingHelper


class ExplorationAgent:
    """
    Agent that systematically explores the map.

    This tests:
    - Pathfinding doesn't get stuck
    - Map generation creates reachable areas
    - FOV updates correctly
    - No infinite loops in movement
    """

    def __init__(self, agent: GameTestAgent):
        self.agent = agent
        self.visited_tiles = set()
        self.stuck_count = 0
        self.max_stuck = 10

    def find_nearest_unexplored(self):
        """Find nearest unexplored visible tile."""
        visible = self.agent.engine.visible_tiles
        player_pos = (self.agent.player.x, self.agent.player.y)

        unexplored_visible = [
            tile for tile in visible
            if tile not in self.visited_tiles
            and tile not in self.agent.game_map.walls
        ]

        if not unexplored_visible:
            return None

        # Find closest by Manhattan distance
        def distance(tile):
            return abs(tile[0] - player_pos[0]) + abs(tile[1] - player_pos[1])

        return min(unexplored_visible, key=distance)

    def explore_map(self, max_turns: int = 500):
        """
        Try to explore as much of the map as possible.

        Returns:
            Statistics about exploration
        """
        stats = {
            'turns_taken': 0,
            'tiles_explored': 0,
            'tiles_visible': 0,
            'got_stuck': False,
            'exploration_percentage': 0.0,
            'path_found': True
        }

        last_position = None
        stuck_counter = 0

        for turn in range(max_turns):
            stats['turns_taken'] = turn + 1

            # Stop if player died
            if self.agent.engine.game_over:
                break

            # Mark current position as visited
            current = (self.agent.player.x, self.agent.player.y)
            self.visited_tiles.add(current)

            # Check if stuck in same position
            if current == last_position:
                stuck_counter += 1
                if stuck_counter > self.max_stuck:
                    stats['got_stuck'] = True
                    break
            else:
                stuck_counter = 0

            last_position = current

            # Find unexplored area
            target = self.find_nearest_unexplored()

            if target is None:
                # No more unexplored visible tiles - try to find any unexplored tile
                # This would require more sophisticated pathfinding
                break

            # Use proper TCOD pathfinding to reach target
            target_pos = Position(target[0], target[1])
            player_pos = Position(self.agent.player.x, self.agent.player.y)

            # Create cost map for pathfinding
            walkability = self.agent.game_map.get_walkability_map()
            cost_map = np.where(walkability, 10, 0).astype(np.int32)

            # Calculate path using PathfindingHelper
            path = PathfindingHelper.calculate_simple_path(player_pos, target_pos, cost_map)

            if path is None or len(path) < 2:
                # No path found - wait a turn
                self.agent.wait(1)
                continue

            # Get next step in path (skip current position)
            next_step = path[1]  # path[0] is current position
            next_x, next_y = next_step[1], next_step[0]  # Convert from (y, x) to (x, y)

            # Calculate movement delta
            dx = next_x - self.agent.player.x
            dy = next_y - self.agent.player.y

            # Try to move
            if not self.agent.move_player(dx, dy):
                # Path is blocked (shouldn't happen with proper pathfinding)
                # Wait a turn
                self.agent.wait(1)

        # Calculate stats
        stats['tiles_explored'] = len(self.visited_tiles)
        stats['tiles_visible'] = len(self.agent.engine.visible_tiles)

        # Estimate total walkable tiles (rough approximation)
        # In a typical roguelike, about 30-40% of tiles are walkable
        total_tiles = 80 * 50
        estimated_walkable = total_tiles * 0.35
        stats['exploration_percentage'] = (len(self.visited_tiles) / estimated_walkable) * 100

        return stats


class TestExplorationAgent:
    """Tests using goal-oriented exploration agents."""

    def test_explore_level_1(self):
        """Agent should be able to explore a significant portion of level 1."""
        agent = GameTestAgent(seed=42)
        explorer = ExplorationAgent(agent)

        stats = explorer.explore_map(max_turns=300)

        print(f"\n=== Exploration Stats ===")
        print(f"Turns taken: {stats['turns_taken']}")
        print(f"Tiles explored: {stats['tiles_explored']}")
        print(f"Estimated coverage: {stats['exploration_percentage']:.1f}%")
        print(f"Got stuck: {stats['got_stuck']}")

        # Agent should explore at least 50 tiles without getting stuck
        assert stats['tiles_explored'] >= 50, \
            f"Only explored {stats['tiles_explored']} tiles - pathfinding issue?"
        assert not stats['got_stuck'], "Agent got stuck - pathfinding failure"

    def test_exploration_across_seeds(self):
        """Test exploration on different random seeds."""
        results = []

        for seed in [1, 42, 100, 200, 300]:
            agent = GameTestAgent(seed=seed)
            explorer = ExplorationAgent(agent)
            stats = explorer.explore_map(max_turns=200)

            results.append({
                'seed': seed,
                'explored': stats['tiles_explored'],
                'stuck': stats['got_stuck']
            })

        print(f"\n=== Multi-Seed Exploration ===")
        for result in results:
            print(f"Seed {result['seed']}: {result['explored']} tiles explored "
                  f"(Stuck: {result['stuck']})")

        # No seed should get the agent stuck
        stuck_seeds = [r['seed'] for r in results if r['stuck']]
        assert len(stuck_seeds) == 0, f"Agent got stuck on seeds: {stuck_seeds}"

        # All seeds should allow some exploration
        min_explored = min(r['explored'] for r in results)
        assert min_explored >= 30, \
            f"Minimum exploration was only {min_explored} tiles - possible map generation issue"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
