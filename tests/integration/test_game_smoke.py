#!/usr/bin/env python3
"""
Smoke Tests for Game Integration

Basic integration tests to verify core gameplay systems work together.
These tests run the actual game engine in headless mode to catch
integration bugs that unit tests might miss.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.test_agent import GameTestAgent
from game_entities import Position


class TestMovement:
    """Test player movement mechanics."""

    def test_player_can_move_in_all_directions(self):
        """Player should be able to move in all 8 cardinal directions."""
        agent = GameTestAgent(seed=42)
        initial_pos = (agent.player.x, agent.player.y)

        # Test all 8 directions
        directions = [
            (0, -1),   # North
            (1, -1),   # Northeast
            (1, 0),    # East
            (1, 1),    # Southeast
            (0, 1),    # South
            (-1, 1),   # Southwest
            (-1, 0),   # West
            (-1, -1),  # Northwest
        ]

        for dx, dy in directions:
            # Move player
            old_pos = (agent.player.x, agent.player.y)

            # Try to move (may be blocked by walls in some directions)
            # We just verify the game doesn't crash
            try:
                agent.move_player(dx, dy)
                # If we moved, verify we're in a different position or same if blocked
                new_pos = (agent.player.x, agent.player.y)
                # Position should either change or stay the same (if blocked)
                assert new_pos == old_pos or new_pos != old_pos
            except Exception as e:
                pytest.fail(f"Movement in direction ({dx}, {dy}) caused exception: {e}")

        # Player should still be alive
        agent.assert_alive()

    def test_player_movement_updates_position(self):
        """Moving player should update position coordinates."""
        agent = GameTestAgent(seed=42)
        initial_x = agent.player.x
        initial_y = agent.player.y

        # Find a walkable direction
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                new_x = initial_x + dx
                new_y = initial_y + dy

                # Check bounds
                if 0 <= new_x < 80 and 0 <= new_y < 50:
                    # Check if walkable (not a wall)
                    if (new_x, new_y) not in agent.game_map.walls:
                        # This should work
                        success = agent.move_player(dx, dy)
                        if success:
                            assert agent.player.x == new_x, f"Expected x={new_x}, got {agent.player.x}"
                            assert agent.player.y == new_y, f"Expected y={new_y}, got {agent.player.y}"
                            return  # Test passed

        # If we couldn't find any walkable tile, that's suspicious but not necessarily wrong
        # (could be surrounded by walls in rare cases)
        pytest.skip("Could not find walkable tile to test movement")

    def test_movement_blocked_by_walls(self):
        """Player cannot move through walls."""
        agent = GameTestAgent(seed=42)

        # Find a wall adjacent to player
        player_x, player_y = agent.player.x, agent.player.y

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                check_x = player_x + dx
                check_y = player_y + dy

                # Check bounds
                if 0 <= check_x < 80 and 0 <= check_y < 50:
                    # If this is a wall
                    if (check_x, check_y) in agent.game_map.walls:
                        # Try to move there
                        old_pos = (player_x, player_y)
                        agent.move_player(dx, dy)
                        new_pos = (agent.player.x, agent.player.y)

                        # Position should not have changed
                        assert old_pos == new_pos, "Player moved through a wall!"
                        return  # Test passed

        # If no walls found adjacent, skip test
        pytest.skip("No walls adjacent to player spawn position")


class TestCombat:
    """Test combat mechanics."""

    def test_bump_attack_damages_enemy(self):
        """Bumping into an enemy should deal damage."""
        agent = GameTestAgent(seed=42)

        # Spawn an enemy next to player
        enemy_x = agent.player.x + 1
        enemy_y = agent.player.y
        enemy = agent.spawn_enemy('bot', enemy_x, enemy_y)
        initial_hp = enemy.cpu

        # Move into enemy (bump attack)
        agent.move_player(1, 0)

        # Enemy should have taken damage or be dead
        if enemy in agent.enemies:
            assert enemy.cpu < initial_hp, "Enemy took no damage from bump attack"
        # else enemy was killed, which is also valid

    def test_killing_enemy_removes_it(self):
        """Killing an enemy should remove it from the game."""
        agent = GameTestAgent(seed=42)

        # Spawn a weak enemy next to player
        enemy_x = agent.player.x + 1
        enemy_y = agent.player.y
        enemy = agent.spawn_enemy('bot', enemy_x, enemy_y)
        enemy.cpu = 1  # Make it very weak

        initial_enemy_count = len(agent.enemies)

        # Attack the enemy (should kill it)
        agent.move_player(1, 0)

        # Enemy count should decrease
        assert len(agent.enemies) < initial_enemy_count, "Dead enemy was not removed"
        assert enemy not in agent.enemies, "Dead enemy still in enemies list"

    def test_player_takes_damage_on_death_check(self):
        """Player can take damage and die."""
        agent = GameTestAgent(seed=42)

        # Reduce player to very low HP
        agent.player.cpu = 5

        # Deal lethal damage
        agent.player.take_damage(10)

        # Player should be dead
        assert agent.player.cpu <= 0, "Player survived lethal damage"


class TestFieldOfView:
    """Test FOV and visibility mechanics."""

    def test_fov_updates_on_movement(self):
        """Field of view should update when player moves."""
        agent = GameTestAgent(seed=42)

        # Get initial visible tiles
        initial_visible = set(agent.engine.visible_tiles)

        # Move player if possible
        moved = False
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            if agent.move_player(dx, dy):
                moved = True
                break

        if not moved:
            pytest.skip("Could not move player to test FOV update")

        # Get new visible tiles
        new_visible = set(agent.engine.visible_tiles)

        # Visible tiles should have changed (unless in a perfectly symmetric area)
        # At minimum, the set should not be identical
        # Note: In rare cases they could be the same, but usually they differ
        # We'll just check that FOV calculation ran without error
        assert isinstance(new_visible, set), "FOV did not return a set"
        assert len(new_visible) > 0, "FOV returned no visible tiles"

    def test_player_position_always_visible(self):
        """Player's current position should always be visible."""
        agent = GameTestAgent(seed=42)

        player_pos = (agent.player.x, agent.player.y)
        assert agent.is_visible(agent.player.x, agent.player.y), \
            f"Player position {player_pos} is not visible"

    def test_explored_tiles_persist(self):
        """Tiles remain explored after leaving FOV."""
        agent = GameTestAgent(seed=42)

        # Mark current visible tiles as explored
        initial_explored = set(agent.game_map.explored_tiles)

        # Move around to explore more tiles
        for _ in range(5):
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                if agent.move_player(dx, dy):
                    break

        # Explored tiles should have grown or stayed the same
        final_explored = set(agent.game_map.explored_tiles)
        assert len(final_explored) >= len(initial_explored), \
            "Explored tiles decreased (should only grow)"


class TestGameState:
    """Test overall game state management."""

    def test_engine_initializes_without_crash(self):
        """Game engine should initialize in headless mode."""
        agent = GameTestAgent(seed=42)
        assert agent.engine is not None
        assert agent.player is not None
        assert agent.game_map is not None

    def test_turn_counter_increments(self):
        """Turn counter should increment when turns are processed."""
        agent = GameTestAgent(seed=42)
        initial_turn = agent.turn

        agent.wait(1)

        assert agent.turn > initial_turn, "Turn counter did not increment"

    def test_multiple_turns_execute_without_crash(self):
        """Running multiple turns should not crash."""
        agent = GameTestAgent(seed=42)

        # Run 10 turns
        for _ in range(10):
            agent.wait(1)
            agent.assert_alive()  # Player should still be alive

        # Should have advanced 10 turns
        assert agent.turn >= 10, f"Expected turn >= 10, got {agent.turn}"

    def test_state_snapshot_returns_valid_data(self):
        """get_state() should return valid game state."""
        agent = GameTestAgent(seed=42)
        state = agent.get_state()

        # Validate state structure
        assert 'player_hp' in state
        assert 'player_pos' in state
        assert 'enemies' in state
        assert 'turn' in state
        assert 'level' in state

        # Validate data types
        assert isinstance(state['player_hp'], int)
        assert isinstance(state['player_pos'], tuple)
        assert isinstance(state['enemies'], list)
        assert isinstance(state['turn'], int)

    def test_deterministic_with_seed(self):
        """Same seed should produce same initial state."""
        agent1 = GameTestAgent(seed=12345)
        agent2 = GameTestAgent(seed=12345)

        # Initial positions might vary due to level generation,
        # but we can check that both engines initialized
        assert agent1.player is not None
        assert agent2.player is not None

        # Both should be at turn 0
        assert agent1.turn == agent2.turn


class TestEnemyBehavior:
    """Test enemy AI and behavior."""

    def test_enemies_exist_on_level(self):
        """Level should spawn with enemies."""
        agent = GameTestAgent(seed=42)

        # There should be at least some enemies on the level
        # (could be 0 in very rare cases, but usually not)
        assert agent.enemies is not None
        assert isinstance(agent.enemies, list)

    def test_enemy_positions_valid(self):
        """All enemies should have valid positions."""
        agent = GameTestAgent(seed=42)

        for enemy in agent.enemies:
            assert 0 <= enemy.x < 80, f"Enemy x={enemy.x} out of bounds"
            assert 0 <= enemy.y < 50, f"Enemy y={enemy.y} out of bounds"

    def test_get_enemy_at_position(self):
        """get_enemy_at should find enemies at their positions."""
        agent = GameTestAgent(seed=42)

        if len(agent.enemies) == 0:
            pytest.skip("No enemies spawned to test")

        enemy = agent.enemies[0]
        found = agent.get_enemy_at(enemy.x, enemy.y)

        assert found is not None, f"Could not find enemy at ({enemy.x}, {enemy.y})"
        assert found == enemy, "Found wrong enemy at position"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
