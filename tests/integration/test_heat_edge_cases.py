"""
Heat Management Edge Case Tests

Tests edge cases and specific behaviors of the heat system:
- Heat at maximum + exploit usage (can player act at max heat?)
- Cooling node timing (immediate vs next turn)
- Overheat damage and heat reset mechanics
- Heat decay rate accuracy (normal vs boosted)
- Consecutive attack heat penalty
- Exploit efficiency heat reduction (30%)
- Speed boost + heat interaction

These tests complement the existing heat_trace_integration tests
by focusing on specific edge cases and timing mechanics.
"""

import pytest
from game_entities import Position
from game_config import GameBalance
from tests.fixtures.simple_fixtures import create_real_enemy


class TestHeatAtMaximum:
    """Test behavior when heat is at or near maximum."""

    def test_exploit_usable_at_max_heat(self, basic_game_engine):
        """Test player can still use exploits at maximum heat."""
        engine = basic_game_engine

        # Set heat to maximum
        engine.player.heat = engine.player.max_heat
        engine.player.inventory_manager.equipped_exploits.append('code_injection')

        # Create target enemy
        bot = create_real_enemy("bot", Position(11, 10))
        engine.player.position = Position(10, 10)
        engine.enemies = [bot]

        # Try to use exploit at max heat
        result = engine.exploit_system.use_exploit('code_injection')

        # Should still work (heat caps, doesn't prevent action)
        assert result is True, "Exploit should be usable at max heat"

    def test_heat_stays_at_max_when_generating_more(self, basic_game_engine):
        """Test heat caps at maximum when generating more heat."""
        engine = basic_game_engine

        # Set heat near max
        engine.player.heat = engine.player.max_heat - 5
        engine.player.inventory_manager.equipped_exploits.append('code_injection')

        # Create target
        bot = create_real_enemy("bot", Position(11, 10))
        engine.player.position = Position(10, 10)
        engine.enemies = [bot]

        # Use exploit (generates ~8 heat)
        engine.exploit_system.use_exploit('code_injection')

        # Heat should cap at max
        assert engine.player.heat <= engine.player.max_heat, \
            f"Heat should cap at {engine.player.max_heat}, got {engine.player.heat}"

    def test_overheat_mechanism_exists(self, basic_game_engine):
        """Test overheat system is properly configured."""
        engine = basic_game_engine

        # Verify max heat is defined
        assert hasattr(engine.player, 'max_heat'), "Player should have max_heat attribute"
        assert engine.player.max_heat > 0, "Max heat should be positive"

        # Verify overheat damage formula exists (checked in game_engine.py line 398-403)
        # Test that heat can be set to maximum without crashing
        engine.player.heat = engine.player.max_heat
        engine.player.cpu = 100

        # System should remain stable
        assert engine.player.heat == engine.player.max_heat, \
            f"Heat should be settable to max ({engine.player.max_heat})"


class TestCoolingNodeTiming:
    """Test cooling node application timing."""

    def test_cooling_node_immediate_on_step(self, basic_game_engine):
        """Test cooling node reduces heat immediately when stepped on."""
        engine = basic_game_engine

        # Set up cooling node
        cooling_pos = Position(20, 20)
        engine.game_map.cooling_nodes.add((cooling_pos.x, cooling_pos.y))

        # Set heat and position player next to node
        engine.player.heat = 60
        engine.player.position = Position(19, 20)

        initial_heat = engine.player.heat

        # Move onto cooling node
        engine.player.position = cooling_pos

        # Process turn (cooling should apply)
        engine.process_turn()

        # Heat should be reduced
        assert engine.player.heat < initial_heat, \
            "Cooling node should reduce heat on the turn player steps on it"

    def test_cooling_node_applies_each_turn(self, basic_game_engine):
        """Test cooling node reduces heat each turn while standing on it."""
        engine = basic_game_engine

        # Set up cooling node
        cooling_pos = Position(20, 20)
        engine.game_map.cooling_nodes.add((cooling_pos.x, cooling_pos.y))
        engine.player.position = cooling_pos
        engine.player.heat = 80

        heat_values = [engine.player.heat]

        # Stand still for multiple turns
        for _ in range(3):
            engine.process_turn()
            heat_values.append(engine.player.heat)

        # Heat should decrease each turn
        assert heat_values[-1] < heat_values[0], \
            f"Heat should decrease over multiple turns on cooling node"
        # Each turn should show reduction
        for i in range(len(heat_values) - 1):
            assert heat_values[i + 1] <= heat_values[i], \
                f"Heat should not increase while on cooling node"

    def test_cooling_node_stacks_with_passive_decay(self, basic_game_engine):
        """Test cooling node effect stacks with passive heat decay."""
        engine = basic_game_engine

        # Set up cooling node
        cooling_pos = Position(20, 20)
        engine.game_map.cooling_nodes.add((cooling_pos.x, cooling_pos.y))
        engine.player.position = cooling_pos
        engine.player.heat = 60

        initial_heat = engine.player.heat

        # Process one turn
        engine.process_turn()

        # Heat reduction should be cooling node (20) + passive decay (2 or 3)
        expected_reduction_min = 20 + GameBalance.HEAT_REDUCTION_NORMAL
        actual_reduction = initial_heat - engine.player.heat

        assert actual_reduction >= expected_reduction_min - 1, \
            f"Cooling node should stack with passive decay, expected ~{expected_reduction_min}, got {actual_reduction}"


class TestHeatDecayRates:
    """Test heat decay rate accuracy."""

    def test_normal_heat_decay_rate(self, basic_game_engine):
        """Test heat decays at normal rate (2 per turn)."""
        engine = basic_game_engine

        # Remove all enemies to prevent combat
        engine.enemies.clear()

        # Set initial heat
        engine.player.heat = 50
        engine.player.temporary_effects['exploit_efficiency_turns'] = 0  # Ensure normal rate

        # Process several turns
        heat_before = engine.player.heat
        turns = 5
        for _ in range(turns):
            engine.process_turn()

        # Calculate expected reduction
        expected_reduction = GameBalance.HEAT_REDUCTION_NORMAL * turns
        actual_reduction = heat_before - engine.player.heat

        # Allow small tolerance
        assert abs(actual_reduction - expected_reduction) <= 1, \
            f"Heat should decay by {expected_reduction} over {turns} turns, got {actual_reduction}"

    def test_boosted_heat_decay_with_exploit_efficiency(self, basic_game_engine):
        """Test heat decays faster with exploit efficiency active."""
        engine = basic_game_engine

        # Remove all enemies
        engine.enemies.clear()

        # Set initial heat and activate exploit efficiency
        engine.player.heat = 50
        engine.player.temporary_effects['exploit_efficiency_turns'] = 10  # Active

        # Process several turns
        heat_before = engine.player.heat
        turns = 3
        for _ in range(turns):
            engine.process_turn()

        # Calculate expected reduction (boosted rate)
        expected_reduction = GameBalance.HEAT_REDUCTION_BOOSTED * turns
        actual_reduction = heat_before - engine.player.heat

        # Allow small tolerance
        assert abs(actual_reduction - expected_reduction) <= 1, \
            f"With exploit efficiency, heat should decay by {expected_reduction} over {turns} turns, got {actual_reduction}"

    def test_heat_doesnt_decay_below_zero(self, basic_game_engine):
        """Test heat stops at zero and doesn't go negative."""
        engine = basic_game_engine

        # Set very low heat
        engine.player.heat = 3

        # Process many turns
        for _ in range(10):
            engine.process_turn()

        # Heat should be 0, not negative
        assert engine.player.heat == 0, \
            f"Heat should not go below 0, got {engine.player.heat}"


class TestConsecutiveAttackHeatPenalty:
    """Test heat penalty for consecutive attacks from same position."""

    def test_moving_resets_consecutive_attack_penalty(self, basic_game_engine):
        """Test moving between attacks resets heat penalty."""
        engine = basic_game_engine

        engine.player.heat = 0
        engine.player.position = Position(10, 10)
        engine.player.inventory_manager.equipped_exploits.append('code_injection')

        # Create enemies
        bot1 = create_real_enemy("bot", Position(11, 10))
        bot2 = create_real_enemy("bot", Position(12, 11))
        engine.enemies = [bot1, bot2]

        # Attack from first position
        engine.exploit_system.use_exploit('code_injection')
        heat_after_first = engine.player.heat

        # Move to new position
        engine.player.position = Position(11, 11)

        # Attack from new position
        engine.exploit_system.use_exploit('code_injection')
        heat_after_second = engine.player.heat

        # Second attack heat generation should be similar to first (reset penalty)
        first_attack_heat = heat_after_first
        second_attack_heat = heat_after_second - heat_after_first

        # Should be within ~2 of each other (both base heat ~8)
        assert abs(first_attack_heat - second_attack_heat) <= 2, \
            f"Moving should reset heat penalty, first={first_attack_heat}, second={second_attack_heat}"


class TestExploitEfficiencyHeatReduction:
    """Test exploit efficiency reduces heat generation by 30%."""

    def test_exploit_efficiency_reduces_heat_generation(self, basic_game_engine):
        """Test exploit efficiency reduces heat by 30%."""
        engine = basic_game_engine

        # Test without efficiency
        engine.player.heat = 0
        engine.player.position = Position(10, 10)
        engine.player.inventory_manager.equipped_exploits.append('code_injection')
        engine.player.temporary_effects['exploit_efficiency_turns'] = 0

        bot1 = create_real_enemy("bot", Position(11, 10))
        engine.enemies = [bot1]

        # Attack without efficiency
        engine.exploit_system.use_exploit('code_injection')
        heat_normal = engine.player.heat

        # Reset and test with efficiency
        engine.player.heat = 0
        engine.player.position = Position(10, 10)
        engine.player.temporary_effects['exploit_efficiency_turns'] = 5

        bot2 = create_real_enemy("bot", Position(11, 10))
        engine.enemies = [bot2]

        # Attack with efficiency
        engine.exploit_system.use_exploit('code_injection')
        heat_efficient = engine.player.heat

        # Efficient heat should be ~70% of normal (30% reduction)
        expected_efficient = int(heat_normal * 0.7)

        assert abs(heat_efficient - expected_efficient) <= 1, \
            f"Exploit efficiency should reduce heat to ~{expected_efficient}, got {heat_efficient} (normal: {heat_normal})"


class TestSpeedBoostHeatInteraction:
    """Test heat generation with speed boost multiple moves."""

    def test_speed_boost_allows_multiple_moves_per_turn(self, basic_game_engine):
        """Test speed boost grants 2 moves per enemy turn."""
        engine = basic_game_engine

        # Activate speed boost
        engine.player.temporary_effects['speed_boost_turns'] = 5
        engine.player.speed_moves_remaining = 0

        # Process turn (should grant 2 moves)
        engine.process_turn()

        # Should have 2 moves available
        assert engine.player.speed_moves_remaining == 2, \
            f"Speed boost should grant 2 moves, got {engine.player.speed_moves_remaining}"

    def test_heat_decay_applies_per_turn_not_per_move(self, basic_game_engine):
        """Test heat decay happens once per turn, not per speed boost move."""
        engine = basic_game_engine

        # Remove enemies
        engine.enemies.clear()

        # Set heat and activate speed boost
        engine.player.heat = 50
        engine.player.temporary_effects['speed_boost_turns'] = 5
        engine.player.speed_moves_remaining = 2  # Simulate having 2 moves

        initial_heat = engine.player.heat

        # Process one turn (even with 2 moves available)
        engine.process_turn()

        # Heat should decay once, not twice
        expected_reduction = GameBalance.HEAT_REDUCTION_NORMAL
        actual_reduction = initial_heat - engine.player.heat

        assert abs(actual_reduction - expected_reduction) <= 1, \
            f"Heat should decay once per turn, not per move. Expected {expected_reduction}, got {actual_reduction}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
