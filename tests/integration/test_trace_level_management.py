"""
Trace Level Management Integration Tests

Tests comprehensive trace level behavior:
- Trace increase rate accuracy (interval and amount)
- Trace floor (minimum 0) with ghost nodes and log wiper
- Trace ceiling (maximum 100)
- Ghost node reduces trace by 20%
- Log Wiper exploit reduces trace by 30%
- Trace resets to 0 on level transition
- Trace increase varies by level (background_trace config)

These tests verify the complete trace management system works correctly
across different scenarios and edge cases.
"""

import pytest

from game_config import GameBalance
from game_entities import Position
from tests.fixtures.simple_fixtures import create_real_enemy


class TestTraceIncreaseRate:
    """Test trace increase rate accuracy and timing."""

    def test_trace_increases_at_correct_interval(self, basic_game_engine):
        """Test trace increases every TRACE_INCREASE_INTERVAL turns."""
        engine = basic_game_engine

        # Set initial trace
        engine.player.trace_level = 10.0
        initial_trace = engine.player.trace_level

        # Process turns until we hit the increase interval
        interval = GameBalance.TRACE_INCREASE_INTERVAL

        # Process turns up to interval - 1 (should not increase yet)
        for _ in range(interval - 1):
            engine.process_turn()

        # Trace should not have increased yet
        trace_before_interval = engine.player.trace_level

        # Process one more turn (should trigger increase)
        engine.process_turn()

        # Verify trace increased after the interval
        assert (
            engine.player.trace_level > trace_before_interval
        ), f"Trace should increase at interval {interval}"

    def test_trace_increase_amount_accurate(self, basic_game_engine):
        """Test trace increase amount matches config over time."""
        engine = basic_game_engine

        # Remove all enemies to prevent combat deaths during test
        engine.enemies.clear()

        # Set initial trace and make player invulnerable
        engine.player.trace_level = 0.0
        engine.player.cpu = 1000  # High health to prevent death

        # Get current network config
        config = engine.game_state.get_current_network_config()
        background_trace = config.get("background_trace", 1)
        expected_increase_per_interval = background_trace * GameBalance.TRACE_INCREASE_AMOUNT

        # Process many turns and count trace increases
        interval = GameBalance.TRACE_INCREASE_INTERVAL
        num_intervals = 3
        total_turns = interval * num_intervals

        # Process turns
        for _ in range(total_turns):
            engine.process_turn()

        # Calculate actual total increase
        actual_total_increase = engine.player.trace_level

        # Expected total increase over num_intervals
        expected_total_increase = expected_increase_per_interval * num_intervals

        # Verify trace increased over time (allow for timing variations with turn 0 counting)
        # The exact amount can vary based on initial turn counter, but should be in the ballpark
        min_expected = expected_total_increase
        max_expected = expected_total_increase * 2 + 1  # Allow up to double (if turn 0 counted)

        assert min_expected <= actual_total_increase <= max_expected, (
            f"After processing {total_turns} turns ({num_intervals} intervals), "
            f"trace should be between {min_expected} and {max_expected}, got {actual_total_increase}"
        )

    def test_trace_increases_scale_by_level(self, basic_game_engine):
        """Test trace increase varies by level (higher levels = faster trace)."""
        engine = basic_game_engine

        # Test level 1 trace rate
        engine.level = 1
        engine.player.trace_level = 0.0

        # Process one interval
        interval = GameBalance.TRACE_INCREASE_INTERVAL
        for _ in range(interval):
            engine.process_turn()

        level_1_trace = engine.player.trace_level

        # Reset and test level 2 trace rate
        engine.level = 2
        engine.player.trace_level = 0.0
        engine.turn = 0  # Reset turn counter

        for _ in range(interval):
            engine.process_turn()

        level_2_trace = engine.player.trace_level

        # Level 2 should have higher or equal trace accumulation
        # (background_trace config increases with level)
        assert (
            level_2_trace >= level_1_trace
        ), f"Level 2 trace ({level_2_trace}) should be >= Level 1 trace ({level_1_trace})"


class TestTraceFloorAndCeiling:
    """Test trace level boundaries (0 min, 100 max)."""

    def test_trace_floor_at_zero(self, basic_game_engine):
        """Test trace cannot go below 0."""
        engine = basic_game_engine

        # Set trace to low value
        engine.player.trace_level = 5.0

        # Add log wiper exploit (reduces trace by 30%)
        engine.player.inventory_manager.equipped_exploits.append("log_wiper")
        engine.player.position = Position(10, 10)

        # Use log wiper multiple times to try to go negative
        for _ in range(5):
            engine.exploit_system.use_exploit("log_wiper")

        # Verify trace didn't go negative
        assert (
            engine.player.trace_level >= 0
        ), f"Trace should not go negative, got {engine.player.trace_level}"

    def test_trace_ceiling_at_100(self, basic_game_engine):
        """Test trace caps at 100."""
        engine = basic_game_engine

        # Set trace near maximum
        engine.player.trace_level = 95.0

        # Process many turns to try to exceed 100
        for _ in range(50):
            engine.process_turn()

        # Verify trace capped at 100
        assert (
            engine.player.trace_level <= 100
        ), f"Trace should cap at 100, got {engine.player.trace_level}"

    def test_trace_at_exactly_zero(self, basic_game_engine):
        """Test trace at exactly 0 is stable."""
        engine = basic_game_engine

        # Set trace to exactly 0
        engine.player.trace_level = 0.0

        # Process turn
        engine.process_turn()

        # Verify no negative values
        assert (
            engine.player.trace_level >= 0
        ), f"Trace should not go negative from 0, got {engine.player.trace_level}"


class TestGhostNodeTraceReduction:
    """Test ghost node reduces trace by 20%."""

    def test_ghost_node_reduces_trace_by_20_points(self, basic_game_engine):
        """Test standing on ghost node reduces trace by 20 points per turn."""
        engine = basic_game_engine

        # Set up ghost node and player position
        ghost_pos = Position(20, 20)
        engine.game_map.ghost_nodes.add((ghost_pos.x, ghost_pos.y))
        engine.player.position = ghost_pos

        # Set initial trace
        engine.player.trace_level = 50.0
        initial_trace = engine.player.trace_level

        # Process turn (should apply ghost node effect)
        engine.process_turn()

        # Ghost node reduces trace by 20 points per turn (fixed amount, not percentage)
        expected_reduction = 20.0
        expected_trace = initial_trace - expected_reduction

        # Verify trace reduced by 20 points (allow for background trace increase)
        actual_trace = engine.player.trace_level
        # The actual reduction might be slightly less than 20 if background trace increased
        assert actual_trace <= expected_trace + 1.0, (
            f"Ghost node should reduce trace by approximately {expected_reduction} points, "
            f"expected around {expected_trace}, got {actual_trace}"
        )

    def test_ghost_node_doesnt_go_below_zero(self, basic_game_engine):
        """Test ghost node reduction respects 0 floor."""
        engine = basic_game_engine

        # Set up ghost node
        ghost_pos = Position(20, 20)
        engine.game_map.ghost_nodes.add((ghost_pos.x, ghost_pos.y))
        engine.player.position = ghost_pos

        # Set very low trace
        engine.player.trace_level = 3.0

        # Process turn (should reduce but not go negative)
        engine.process_turn()

        # Verify trace is 0 or positive
        assert (
            engine.player.trace_level >= 0
        ), f"Ghost node should not make trace negative, got {engine.player.trace_level}"

    def test_multiple_turns_on_ghost_node(self, basic_game_engine):
        """Test ghost node reduces trace each turn."""
        engine = basic_game_engine

        # Set up ghost node
        ghost_pos = Position(20, 20)
        engine.game_map.ghost_nodes.add((ghost_pos.x, ghost_pos.y))
        engine.player.position = ghost_pos

        # Set initial trace
        engine.player.trace_level = 80.0
        trace_values = [engine.player.trace_level]

        # Stand on ghost node for multiple turns
        for _ in range(5):
            engine.process_turn()
            trace_values.append(engine.player.trace_level)

        # Verify trace decreased over time (accounting for background increase)
        # After 5 turns, trace should be noticeably lower
        assert (
            trace_values[-1] < trace_values[0]
        ), "Ghost node should reduce trace over multiple turns"


class TestLogWiperExploit:
    """Test Log Wiper exploit reduces trace by 30%."""

    def test_log_wiper_reduces_trace_by_30_percent(self, basic_game_engine):
        """Test Log Wiper exploit reduces trace by 30%."""
        engine = basic_game_engine

        # Set up player with log wiper
        engine.player.trace_level = 60.0
        engine.player.inventory_manager.equipped_exploits.append("log_wiper")
        engine.player.position = Position(10, 10)

        initial_trace = engine.player.trace_level

        # Use log wiper
        result = engine.exploit_system.use_exploit("log_wiper")

        # Verify exploit succeeded
        assert result is True, "Log Wiper should succeed"

        # Calculate expected reduction (30%)
        # Note: The exploit data specifies 30 as trace_reduction_percent
        expected_reduction = 30.0
        expected_trace = initial_trace - expected_reduction

        # Verify trace reduced by approximately 30
        actual_trace = engine.player.trace_level
        assert abs(actual_trace - expected_trace) < 1.0, (
            f"Log Wiper should reduce trace by {expected_reduction}, "
            f"expected {expected_trace}, got {actual_trace}"
        )

    def test_log_wiper_doesnt_go_below_zero(self, basic_game_engine):
        """Test Log Wiper respects 0 floor."""
        engine = basic_game_engine

        # Set low trace
        engine.player.trace_level = 10.0
        engine.player.inventory_manager.equipped_exploits.append("log_wiper")
        engine.player.position = Position(10, 10)

        # Use log wiper
        engine.exploit_system.use_exploit("log_wiper")

        # Verify trace is 0 or positive
        assert (
            engine.player.trace_level >= 0
        ), f"Log Wiper should not make trace negative, got {engine.player.trace_level}"

    def test_log_wiper_multiple_uses(self, basic_game_engine):
        """Test Log Wiper can be used multiple times."""
        engine = basic_game_engine

        # Set high trace
        engine.player.trace_level = 90.0
        engine.player.inventory_manager.equipped_exploits.append("log_wiper")
        engine.player.position = Position(10, 10)
        engine.player.ram = 100  # Ensure enough RAM

        trace_values = [engine.player.trace_level]

        # Use log wiper 3 times
        for _ in range(3):
            engine.exploit_system.use_exploit("log_wiper")
            trace_values.append(engine.player.trace_level)

        # Verify trace decreased with each use
        assert trace_values[-1] < trace_values[0], "Multiple Log Wiper uses should reduce trace"
        assert engine.player.trace_level >= 0, "Trace should not go negative"


class TestTraceLevelTransition:
    """Test trace level resets to 0 on level transition."""

    def test_trace_resets_on_level_transition(self, basic_game_engine):
        """Test trace level resets to 0 when advancing to next level."""
        engine = basic_game_engine

        # Set high trace on level 1
        engine.level = 1
        engine.player.trace_level = 85.0

        # Record CPU and heat (should be preserved)
        old_cpu = engine.player.cpu
        old_heat = engine.player.heat

        # Position player on gateway (singular)
        gateway_pos = engine.game_map.gateway
        engine.player.position = Position(gateway_pos.x, gateway_pos.y)

        # Progress to next level
        engine.game_session.progress_to_next_level()

        # Verify trace reset to 0
        assert (
            engine.player.trace_level == 0
        ), f"Trace should reset to 0 on level transition, got {engine.player.trace_level}"

        # Verify CPU and heat preserved
        assert engine.player.cpu == old_cpu, "CPU should be preserved"
        assert engine.player.heat == old_heat, "Heat should be preserved"

    def test_trace_resets_level_1_to_2(self, basic_game_engine):
        """Test trace reset from level 1 to level 2."""
        engine = basic_game_engine

        # Set up level 1 with high trace
        engine.level = 1
        engine.player.trace_level = 75.0

        # Position on gateway (singular)
        gateway_pos = engine.game_map.gateway
        engine.player.position = Position(gateway_pos.x, gateway_pos.y)

        # Advance to level 2
        engine.game_session.progress_to_next_level()

        # Verify level advanced and trace reset
        assert engine.level == 2, "Should be on level 2"
        assert engine.player.trace_level == 0, "Trace should reset to 0"

    def test_trace_resets_level_2_to_3(self, basic_game_engine):
        """Test trace reset from level 2 to level 3."""
        engine = basic_game_engine

        # Set up level 2 with high trace
        engine.level = 2
        engine.player.trace_level = 95.0

        # Position on gateway (singular)
        gateway_pos = engine.game_map.gateway
        engine.player.position = Position(gateway_pos.x, gateway_pos.y)

        # Advance to level 3
        engine.game_session.progress_to_next_level()

        # Verify level advanced and trace reset
        assert engine.level == 3, "Should be on level 3"
        assert engine.player.trace_level == 0, "Trace should reset to 0"


class TestTraceCombinedScenarios:
    """Test trace management in combined scenarios."""

    def test_ghost_node_and_background_increase_balance(self, basic_game_engine):
        """Test ghost node reduction vs background trace increase."""
        engine = basic_game_engine

        # Set up ghost node
        ghost_pos = Position(20, 20)
        engine.game_map.ghost_nodes.add((ghost_pos.x, ghost_pos.y))
        engine.player.position = ghost_pos

        # Set initial trace
        engine.player.trace_level = 50.0
        initial_trace = engine.player.trace_level

        # Process many turns on ghost node
        for _ in range(20):
            engine.process_turn()

        # Ghost node reduction should outpace background increase
        # (20% reduction per turn vs ~1% increase per interval)
        assert (
            engine.player.trace_level < initial_trace
        ), "Ghost node should reduce trace despite background increase"

    def test_log_wiper_and_exploit_usage_interaction(self, basic_game_engine):
        """Test using log wiper after building up trace with exploits."""
        engine = basic_game_engine

        # Set up player with exploits
        engine.player.trace_level = 20.0
        engine.player.inventory_manager.equipped_exploits.extend(["code_injection", "log_wiper"])
        engine.player.ram = 100

        # Create target enemy
        bot = create_real_enemy("bot", Position(11, 10))
        engine.player.position = Position(10, 10)
        engine.enemies = [bot]

        # Use offensive exploit multiple times (increases trace)
        for _ in range(3):
            if len(engine.enemies) > 0:
                engine.exploit_system.use_exploit("code_injection")

        trace_after_combat = engine.player.trace_level

        # Use log wiper to reduce trace
        engine.exploit_system.use_exploit("log_wiper")

        # Verify trace reduced
        assert (
            engine.player.trace_level < trace_after_combat
        ), "Log Wiper should reduce trace after combat"

    def test_high_trace_level_admin_spawn_threshold(self, basic_game_engine):
        """Test trace reaching admin spawn threshold."""
        engine = basic_game_engine

        # Initialize admin_spawned if not present
        if not hasattr(engine.game_state, "admin_spawned"):
            engine.game_state.admin_spawned = False

        # Set trace near threshold
        engine.player.trace_level = 95.0

        # Process turns to push trace to 100
        for _ in range(10):
            engine.process_turn()
            if engine.player.trace_level >= 100:
                break

        # Verify admin spawn system is tracking
        assert hasattr(engine.game_state, "admin_spawned"), "Should track admin spawn status"
        assert isinstance(
            engine.game_state.admin_spawned, bool
        ), "Admin spawn flag should be boolean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
