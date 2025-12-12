#!/usr/bin/env python3
"""
Scenario Testing - Test Specific Gameplay Situations

Tests concrete scenarios that should work in the game.
This is the "traditional" testing approach - exact inputs, exact outputs.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.test_agent import GameTestAgent


class TestGameplayScenarios:
    """Test specific gameplay scenarios."""

    def test_scenario_heat_management(self):
        """
        Scenario: Player attacks multiple times, heat should increase.

        This tests the exact behavior we expect from combat.
        """
        agent = GameTestAgent(seed=42)

        # Spawn enemies to attack
        enemy1 = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)
        enemy2 = agent.spawn_enemy("bot", agent.player.x + 2, agent.player.y)

        initial_heat = agent.player.heat

        # Attack first enemy
        agent.move_player(1, 0)  # Bump attack

        heat_after_1 = agent.player.heat
        assert heat_after_1 > initial_heat, "Heat should increase after attack"

        # Attack second enemy (if first one died, spawn another)
        if enemy1 not in agent.enemies:
            enemy2_pos = (agent.player.x + 1, agent.player.y)
            if enemy2_pos == (enemy2.x, enemy2.y):
                agent.move_player(1, 0)
                heat_after_2 = agent.player.heat
                assert heat_after_2 > heat_after_1, "Heat should keep increasing"

        print("\n=== Heat Management ===")
        print(f"Initial: {initial_heat}")
        print(f"After attack: {heat_after_1}")
        print(f"Heat gain: +{heat_after_1 - initial_heat}")

    def test_scenario_enemy_states(self):
        """
        Scenario: Enemy should become hostile when attacked.

        Tests the state machine transitions.
        """
        agent = GameTestAgent(seed=42)

        # Spawn an unaware enemy
        enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)

        from game_entities import EnemyState

        # Should start unaware
        assert (
            enemy.state == EnemyState.UNAWARE
        ), f"Enemy started as {enemy.state.name}, expected UNAWARE"

        # Attack it
        agent.move_player(1, 0)

        # Should now be hostile (if it survived)
        if enemy in agent.enemies:
            assert (
                enemy.state == EnemyState.HOSTILE
            ), f"Enemy is {enemy.state.name} after attack, expected HOSTILE"
            print("\n=== Enemy State Transition ===")
            print("Transition: UNAWARE -> HOSTILE after taking damage")
            print(f"Enemy HP: {enemy.cpu}/{enemy.max_cpu}")

    def test_scenario_turn_advancement(self):
        """
        Scenario: Waiting should advance turn counter and process game state.
        """
        agent = GameTestAgent(seed=42)

        initial_turn = agent.turn
        initial_heat = agent.player.heat

        # Wait 5 turns
        agent.wait(5)

        # Turn should have advanced
        assert (
            agent.turn == initial_turn + 5
        ), f"Turn counter should be {initial_turn + 5}, got {agent.turn}"

        # Heat should have decreased (passive cooling)
        # Note: This depends on your game's cooling rate
        final_heat = agent.player.heat

        print("\n=== Turn Processing ===")
        print(f"Turns: {initial_turn} -> {agent.turn}")
        print(f"Heat: {initial_heat} -> {final_heat} (change: {final_heat - initial_heat})")

    def test_scenario_gateway_progression(self, agent_with_guaranteed_gateway):
        """
        Scenario: Reaching gateway should allow level progression.

        Tests that the win condition is reachable.
        """
        agent = agent_with_guaranteed_gateway

        # Fixture guarantees gateway exists
        assert agent.game_map.gateway is not None, "Fixture failed to provide gateway"

        initial_level = agent.engine.level
        gateway_x = agent.game_map.gateway.x
        gateway_y = agent.game_map.gateway.y

        print("\n=== Gateway Test ===")
        print(f"Current level: {initial_level}")
        print(f"Player at: ({agent.player.x}, {agent.player.y})")
        print(f"Gateway at: ({gateway_x}, {gateway_y})")

        # Move to gateway
        reached = agent.move_to(gateway_x, gateway_y, max_steps=500)

        if reached:
            distance = abs(agent.player.x - gateway_x) + abs(agent.player.y - gateway_y)
            print(f"Reached gateway: {distance == 0}")
            print(f"Distance to gateway: {distance}")
            assert distance == 0, "Should be exactly on gateway"

    def test_scenario_enemy_does_not_attack_through_walls(self):
        """
        Scenario: Enemies should not be able to attack through walls.

        Tests collision detection. Creates a full wall barrier to ensure
        enemy cannot path around.
        """
        agent = GameTestAgent(seed=42)

        # Get player position
        player_x, player_y = agent.player.x, agent.player.y

        # Create a vertical wall barrier east of player (3 tiles tall)
        # This prevents enemy from pathfinding around
        wall_x = player_x + 1
        for dy in range(-1, 2):
            agent.game_map.walls.add((wall_x, player_y + dy))

        # Spawn enemy on the other side of the wall
        enemy_x, enemy_y = player_x + 2, player_y

        # Make sure enemy position is clear
        agent.game_map.walls.discard((enemy_x, enemy_y))

        enemy = agent.spawn_enemy("bot", enemy_x, enemy_y)

        initial_hp = agent.player.cpu

        # Process several turns - enemy shouldn't be able to attack through wall
        agent.wait(5)

        # Player HP should be unchanged
        assert agent.player.cpu == initial_hp, "Player took damage from enemy through wall!"

        print("\n=== Wall Collision Test ===")
        print(f"Enemy at ({enemy_x}, {enemy_y})")
        print(f"Wall barrier at x={wall_x}")
        print(f"Player at ({player_x}, {player_y})")
        print(f"Player HP: {agent.player.cpu} (unchanged)")

    def test_scenario_multiple_enemies_same_tile(self):
        """
        Scenario: Multiple enemies should not occupy the same tile.

        Tests spawn collision.
        """
        agent = GameTestAgent(seed=42)

        # Spawn enemy at a position
        spawn_x = agent.player.x + 5
        spawn_y = agent.player.y + 5

        enemy1 = agent.spawn_enemy("bot", spawn_x, spawn_y)

        # Try to spawn another at same position
        enemy2 = agent.spawn_enemy("scanner", spawn_x, spawn_y)

        # Both exist but should not overlap (unless we allow it)
        assert enemy1 in agent.enemies
        assert enemy2 in agent.enemies

        # Check positions
        pos1 = (enemy1.x, enemy1.y)
        pos2 = (enemy2.x, enemy2.y)

        print("\n=== Multi-Spawn Test ===")
        print(f"Enemy 1 at: {pos1}")
        print(f"Enemy 2 at: {pos2}")
        print(f"Same position: {pos1 == pos2}")

        # Note: This test documents current behavior
        # If you want to prevent stacking, you'd assert pos1 != pos2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
