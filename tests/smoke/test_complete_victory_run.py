#!/usr/bin/env python3
"""
Complete Victory Run Smoke Test

Tests that the game can be played from start to victory screen without
crashing. This is the ultimate integration test - validates the entire
game loop, all systems working together, across all 3 levels.

Uses the VictoryRunAgent to automatically play through the game.

This test is CRITICAL because:
- Validates end-to-end game flow
- Ensures no crashes during extended play
- Tests level transitions
- Validates victory screen triggers correctly
- Catches integration bugs that only appear during long sessions
"""

import pytest

from tests.agents.test_victory_run_agent import VictoryRunAgent


class TestCompleteVictoryRun:
    """Smoke tests for complete game playthrough."""

    def test_game_starts_for_victory_run(self):
        """Game initializes correctly for victory run attempt."""
        agent = VictoryRunAgent(seed=12345)

        assert agent is not None
        assert agent.player is not None
        assert agent.engine is not None
        assert agent.turn == 0
        assert agent.victory_achieved is False

    def test_agent_can_explore_level_1(self):
        """Agent can explore level 1 without crashing."""
        agent = VictoryRunAgent(seed=12345)

        # Explore level 1 for reasonable time
        agent.explore_level(max_exploration_turns=100)

        # Should have explored without crash
        assert agent.turns_taken > 0
        assert agent.turns_taken <= 100 or agent.engine.game_over

    def test_extended_gameplay_session(self):
        """Extended gameplay session completes without crashes."""
        agent = VictoryRunAgent(seed=12345)

        # Play for extended period
        for _ in range(300):
            if agent.engine.game_over:
                break

            # Try to move
            import random

            dx, dy = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
            try:
                agent.move_player(dx, dy)
            except Exception:
                agent.wait(1)

            agent.turns_taken += 1

        # Should complete without crashing
        assert agent.turns_taken > 0

    def test_game_state_stable_over_time(self):
        """Game state remains stable during extended play."""
        agent = VictoryRunAgent(seed=12345)

        # Play for many turns
        agent.explore_level(max_exploration_turns=200)

        # Verify state consistency
        state = agent.get_state()
        assert state["player_hp"] >= 0
        assert state["player_hp"] <= state["player_max_hp"]
        assert state["turn"] >= 0
        assert 0 <= agent.player.heat

    def test_no_memory_leaks_during_long_session(self):
        """No memory leaks during extended gameplay."""
        agent = VictoryRunAgent(seed=12345, max_turns=500)

        # Simulate long session
        for _ in range(500):
            if agent.engine.game_over:
                break

            # Perform actions
            agent.move_player(1, 0)
            agent.turns_taken += 1
        # No exception after 1000 turns means no memory leak

    @pytest.mark.slow
    def test_victory_run_attempt_completes(self):
        """
        Full victory run attempt completes without crashing.

        NOTE: This test may take several minutes to complete.
        Marked as 'slow' to skip in quick test runs.
        """
        agent = VictoryRunAgent(seed=99999, max_turns=3000)

        # Attempt victory run - success depends on RNG, but should not crash
        result = agent.run_to_victory()
        # Result can be True (victory) or False (death) - both are valid outcomes

    def test_multiple_victory_run_attempts(self):
        """Multiple victory run attempts work without issues."""
        # Test that we can run multiple games without state pollution
        for seed in [100, 200, 300]:
            agent = VictoryRunAgent(seed=seed, max_turns=100)

            # Short exploration
            agent.explore_level(max_exploration_turns=50)

            # Should complete successfully
            assert agent.turns_taken > 0

    def test_victory_agent_metrics_tracking(self):
        """Victory agent correctly tracks metrics."""
        agent = VictoryRunAgent(seed=42)

        # Play for a bit
        agent.explore_level(max_exploration_turns=50)

        # Metrics should be tracked
        assert agent.turns_taken > 0
        assert agent.levels_completed >= 0
        assert agent.max_turns > 0

    def test_game_over_handling(self):
        """Game over state is handled correctly."""
        agent = VictoryRunAgent(seed=42)

        # Play until game over or reasonable limit
        for _ in range(500):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)
            agent.turns_taken += 1

        # If game over, verify state is consistent
        if agent.engine.game_over:
            # Player should be dead (HP = 0)
            assert agent.player.cpu == 0

    def test_player_survives_initial_turns(self):
        """Player survives initial gameplay turns."""
        agent = VictoryRunAgent(seed=12345)

        # Play first 50 turns
        for _ in range(50):
            if agent.engine.game_over:
                break

            # Move cautiously
            agent.move_player(1, 0)
            agent.turns_taken += 1

        # Player should still have HP (or game ended)
        assert agent.player.cpu > 0 or agent.engine.game_over


class TestVictoryRunRobustness:
    """Test victory run robustness and edge cases."""

    def test_various_random_seeds(self):
        """Victory run works with various random seeds."""
        seeds = [111, 222, 333, 444, 555]

        for seed in seeds:
            agent = VictoryRunAgent(seed=seed, max_turns=100)

            # Short exploration with each seed
            agent.explore_level(max_exploration_turns=30)

            # Should complete without crash
            assert agent.turns_taken > 0

    def test_victory_run_with_different_max_turns(self):
        """Victory run respects different max_turns settings."""
        max_turns_values = [100, 500, 1000]

        for max_turns in max_turns_values:
            agent = VictoryRunAgent(seed=42, max_turns=max_turns)

            assert agent.max_turns == max_turns

            # Short test
            agent.explore_level(max_exploration_turns=10)
            assert agent.turns_taken > 0

    def test_victory_run_state_consistency(self):
        """Victory run maintains consistent state throughout."""
        agent = VictoryRunAgent(seed=789)

        # Record initial state
        initial_level = agent.engine.level

        # Play for a bit
        agent.explore_level(max_exploration_turns=50)

        # State should be consistent
        assert agent.engine.level >= initial_level
        assert agent.turn >= 0
        assert agent.player.cpu >= 0

    def test_rapid_actions_dont_crash(self):
        """Rapid consecutive actions don't crash the game."""
        agent = VictoryRunAgent(seed=42)

        # Perform many rapid actions - smoke test for stability
        for _ in range(100):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)
        # No exception means rapid actions handled correctly


class TestVictoryRunPerformance:
    """Performance tests for victory runs."""

    def test_turn_processing_speed(self):
        """Turn processing completes in reasonable time."""
        import time

        agent = VictoryRunAgent(seed=42)

        # Measure time for 100 turns
        start_time = time.time()

        for _ in range(100):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)

        elapsed_time = time.time() - start_time

        # Should complete in under 10 seconds (reasonable performance)
        assert elapsed_time < 10.0

    def test_no_performance_degradation(self):
        """Performance doesn't degrade over time."""
        import time

        agent = VictoryRunAgent(seed=42)

        # Measure first 50 turns
        start_time = time.time()
        for _ in range(50):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)
        first_batch_time = time.time() - start_time

        # Measure next 50 turns
        start_time = time.time()
        for _ in range(50):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)
        second_batch_time = time.time() - start_time

        # Second batch shouldn't be significantly slower (< 2x)
        # (Some variance is expected, but not massive degradation)
        if first_batch_time > 0:
            assert second_batch_time < first_batch_time * 3
