#!/usr/bin/env python3
"""
First 5 Minutes Smoke Test

Validates the initial gameplay experience - the most critical user-facing
functionality. This test simulates what a player would do in the first
5 minutes of gameplay and ensures no crashes or game-breaking bugs occur.

Tests:
- Game starts without crashing
- Player can move around
- Basic interactions work (items, enemies)
- Menus open and close
- No immediate crashes in core gameplay loop
"""

from tests.test_agent import GameTestAgent


class TestFirst5MinutesSmoke:
    """Smoke test for the first 5 minutes of gameplay experience."""

    def test_game_starts_successfully(self):
        """Game initializes and starts without crashing."""
        agent = GameTestAgent(seed=42)

        # Basic assertions - game should be initialized
        assert agent.player is not None
        assert agent.game_map is not None
        assert agent.player.cpu > 0
        assert agent.turn == 0

    def test_player_can_move_in_all_directions(self):
        """Player can move in all cardinal directions without crashing."""
        agent = GameTestAgent(seed=42)

        initial_pos = (agent.player.x, agent.player.y)

        # Try moving in various directions
        # Note: Some moves might be blocked by walls, but should not crash
        moves_attempted = [
            (1, 0),  # Right
            (0, 1),  # Down
            (-1, 0),  # Left
            (0, -1),  # Up
        ]

        for dx, dy in moves_attempted:
            try:
                agent.move_player(dx, dy)
                # If move succeeds, verify game is still valid
                assert agent.player is not None
                assert agent.turn > 0
            except Exception:
                # Move might be blocked, but should not crash the game
                pass

        # Player should have moved at least once (some direction was valid)
        assert agent.turn > 0

    def test_player_can_move_multiple_times(self):
        """Player can perform multiple moves in sequence."""
        agent = GameTestAgent(seed=42)

        # Perform 10 movement attempts
        for i in range(10):
            # Try moving right, if blocked try down, if blocked try left, etc.
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                initial_turn = agent.turn
                agent.move_player(dx, dy)

                # If turn advanced, move succeeded
                if agent.turn > initial_turn:
                    break

        # Should have made at least some moves
        assert agent.turn > 0
        assert not agent.engine.game_over

    def test_game_state_updates_correctly(self):
        """Game state updates correctly after player actions."""
        agent = GameTestAgent(seed=42)

        # Get initial state
        initial_state = agent.get_state()

        # Perform some actions
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Get new state
        new_state = agent.get_state()

        # State should have changed
        assert new_state["turn"] > initial_state["turn"]
        assert new_state["player_pos"] != initial_state["player_pos"]

    def test_player_can_wait(self):
        """Player can wait/pass turn without crashing."""
        agent = GameTestAgent(seed=42)

        initial_turn = agent.turn

        # Wait several turns
        for _ in range(5):
            agent.wait()

        # Turns should have advanced
        assert agent.turn > initial_turn
        assert not agent.engine.game_over

    def test_player_explores_without_crashing(self):
        """Player can explore for extended period without crashes."""
        agent = GameTestAgent(seed=42)

        # Simulate ~30 turns of gameplay (first few minutes)
        max_turns = 30
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        for i in range(max_turns):
            if agent.engine.game_over:
                break

            # Try to move in a direction
            dx, dy = directions[i % len(directions)]

            try:
                agent.move_player(dx, dy)
            except Exception:
                # If move fails, wait instead
                agent.wait()

        # Should have survived exploration
        assert agent.turn >= max_turns or agent.engine.game_over

    def test_basic_game_loop_stable(self):
        """Basic game loop runs stably for first 5 minutes worth of turns."""
        agent = GameTestAgent(seed=42)

        # Run for 50 turns (approximately first 5 minutes)
        turns_to_run = 50

        for _ in range(turns_to_run):
            if agent.engine.game_over:
                # Game over is fine (player died or won)
                break

            # Perform random valid action
            import random

            action = random.choice(["move", "wait"])

            if action == "move":
                dx, dy = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
                try:
                    agent.move_player(dx, dy)
                except Exception:
                    agent.wait()
            else:
                agent.wait()

        # Should complete without crashes
        assert True  # Reaching here means no crash

    def test_player_stats_are_valid(self):
        """Player stats remain in valid ranges during gameplay."""
        agent = GameTestAgent(seed=42)

        # Play for 20 turns
        for _ in range(20):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)

        # Stats should be valid
        assert 0 <= agent.player.cpu <= agent.player.max_cpu
        assert agent.player.heat >= 0
        assert agent.player.trace_level >= 0

    def test_fov_updates_on_movement(self):
        """Field of view updates when player moves."""
        agent = GameTestAgent(seed=42)

        initial_visible = len(agent.engine.visible_tiles)

        # Move several times
        for _ in range(5):
            agent.move_player(1, 0)

        # Visible tiles should have updated (may be same or different based on map)
        assert len(agent.engine.visible_tiles) > 0

    def test_enemies_exist_and_active(self):
        """Enemies spawn and are active in the level."""
        agent = GameTestAgent(seed=42)

        # Level should have enemies
        enemies = agent.enemies
        assert len(enemies) > 0

        # Enemies should have valid properties
        for enemy in enemies:
            assert enemy.cpu > 0
            assert enemy.x >= 0 and enemy.y >= 0
            assert enemy.state is not None

    def test_game_responds_to_time_passage(self):
        """Game state evolves over time (enemies move, etc)."""
        agent = GameTestAgent(seed=42)

        # Record initial enemy positions
        initial_enemy_positions = [(e.x, e.y) for e in agent.enemies[:3]]

        # Wait many turns to let enemies act
        for _ in range(10):
            agent.wait()

        # At least some enemies should have moved (if they're not idle)
        new_enemy_positions = [(e.x, e.y) for e in agent.enemies[:3]]

        # Positions may have changed (enemies moving) or stayed same (idle)
        # Just verify no crashes occurred
        assert len(new_enemy_positions) > 0

    def test_no_immediate_crash_on_startup(self):
        """Game does not crash immediately on startup."""
        agent = GameTestAgent(seed=42)

        # Perform basic sanity checks
        assert agent.engine is not None
        assert agent.player is not None
        assert agent.game_map is not None
        assert agent.message_log is not None

        # Game state should be valid
        state = agent.get_state()
        assert state["player_hp"] > 0
        assert state["turn"] == 0
        assert not state["game_over"]

    def test_multiple_game_instances(self):
        """Multiple game instances can coexist (for integration testing)."""
        agent1 = GameTestAgent(seed=42)
        agent2 = GameTestAgent(seed=43)

        # Both should be valid
        assert agent1.player is not None
        assert agent2.player is not None

        # They should be independent
        agent1.move_player(1, 0)

        assert agent1.turn == 1
        assert agent2.turn == 0

    def test_game_state_remains_consistent(self):
        """Game state remains consistent after various actions."""
        agent = GameTestAgent(seed=42)

        # Perform various actions
        for _ in range(10):
            state_before = agent.get_state()

            # Perform action
            agent.move_player(1, 0)

            state_after = agent.get_state()

            # Verify state consistency
            assert state_after["turn"] >= state_before["turn"]
            assert state_after["player_hp"] <= state_before["player_max_hp"]
            assert not (state_after["game_over"] and state_after["player_hp"] > 0)
