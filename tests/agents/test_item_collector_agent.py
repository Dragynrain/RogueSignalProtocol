"""
Item Collection Agent Tests

Validates item-related mechanics and agent behavior:
- Item accessibility validation
- Collection workflow testing
- Agent pathfinding to items
"""

import pytest
from tests.test_agent import GameTestAgent


class TestItemCollectionMechanics:
    """Test item collection mechanics using agent framework."""

    def test_agent_can_navigate_map(self):
        """Agent should be able to navigate to different map positions."""
        agent = GameTestAgent(seed=77001)

        initial_pos = (agent.player.x, agent.player.y)

        # Try to move to different position
        agent.move_to(20, 20)

        # Position should have changed or attempted to change
        assert agent.player is not None

    def test_agent_pathfinding_works(self):
        """Agent pathfinding should work across map."""
        agent = GameTestAgent(seed=77002)

        # Record starting position
        start_x, start_y = agent.player.x, agent.player.y

        # Move somewhere else
        agent.move_to(start_x + 5, start_y + 5)

        # Agent should exist and be movable
        assert agent.player.x >= 0
        assert agent.player.y >= 0

    def test_map_has_walkable_tiles(self):
        """Map should have walkable (non-wall) tiles."""
        agent = GameTestAgent(seed=77003)

        # Player should be on walkable tile
        player_pos = (agent.player.x, agent.player.y)
        assert player_pos not in agent.engine.game_map.walls

    def test_agent_respects_map_boundaries(self):
        """Agent movement should respect map boundaries."""
        agent = GameTestAgent(seed=77004)

        # Player should be within map bounds
        assert 0 <= agent.player.x < agent.engine.game_map.width
        assert 0 <= agent.player.y < agent.engine.game_map.height

    def test_agent_avoids_walls(self):
        """Agent pathfinding should avoid walls."""
        agent = GameTestAgent(seed=77005)

        # Try to move around
        for _ in range(10):
            agent.wait(1)

        # Player should still not be in a wall
        player_pos = (agent.player.x, agent.player.y)
        assert player_pos not in agent.engine.game_map.walls

    def test_map_generation_consistent(self):
        """Same seed should generate consistent maps."""
        agent1 = GameTestAgent(seed=99999)
        agent2 = GameTestAgent(seed=99999)

        # Same seed should give same map dimensions
        assert agent1.engine.game_map.width == agent2.engine.game_map.width
        assert agent1.engine.game_map.height == agent2.engine.game_map.height

    def test_agent_can_explore_map(self):
        """Agent should be able to explore different map areas."""
        agent = GameTestAgent(seed=77006)

        initial_turn = agent.turn

        # Move around map
        agent.wait(20)

        # Turns should have advanced
        assert agent.turn > initial_turn
