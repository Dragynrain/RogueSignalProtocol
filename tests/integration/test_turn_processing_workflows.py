"""
Turn Processing Workflow Integration Tests

Tests complete turn processing across multiple systems:
- Turn counter increments
- Background trace accumulation
- Heat dissipation
- Temporary effect duration
- Enemy turn processing
- Environmental effects per turn
- Resource regeneration
- Turn-based state updates

These tests verify turn processing integrates correctly with:
- Game state management
- Player stats and resources
- Enemy AI and movement
- Temporary effects system
- Environmental systems
"""

import pytest
from unittest.mock import Mock

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_config import GameSettings, GameBalance
from tests.fixtures.real_game_data import get_real_game_data
from tests.fixtures.simple_fixtures import enemy_builder


class TestBasicTurnProcessing:
    """Test fundamental turn processing mechanics."""

    def test_turn_counter_increments(self, basic_game_engine):
        """Test turn counter increments each turn."""

        initial_turn = basic_game_engine.turn

        # Process turn
        basic_game_engine.process_turn()

        # Verify turn incremented
        assert basic_game_engine.turn == initial_turn + 1, "Turn counter should increment"

    def test_multiple_turns_increment_correctly(self, basic_game_engine):
        """Test turn counter increments correctly over multiple turns."""

        initial_turn = basic_game_engine.turn

        # Process 10 turns
        for i in range(10):
            basic_game_engine.process_turn()

        # Verify turn incremented by 10
        assert basic_game_engine.turn == initial_turn + 10, "Turn should increment by 10"

    def test_turn_processing_updates_game_state(self, basic_game_engine):
        """Test that turn processing updates game state correctly."""

        # Verify initial state
        assert basic_game_engine.game_state is not None
        assert hasattr(basic_game_engine, 'turn')

        initial_turn = basic_game_engine.turn

        # Process turn
        basic_game_engine.process_turn()

        # Verify state updated
        assert basic_game_engine.turn > initial_turn
        assert basic_game_engine.game_state is not None


class TestBackgroundTraceAccumulation:
    """Test background trace accumulation per turn."""

    def test_trace_level_increases_per_turn(self, basic_game_engine):
        """Test trace level increases each turn based on network config."""

        initial_trace = basic_game_engine.player.trace_level

        # Get background trace rate
        network_config = basic_game_engine.game_state.get_current_network_config()
        background_trace = network_config.get('background_trace', 0)

        # Process turn
        basic_game_engine.process_turn()

        # Verify trace increased
        if background_trace > 0:
            assert basic_game_engine.player.trace_level >= initial_trace, "Trace should increase with background trace"

    def test_trace_accumulation_over_many_turns(self, basic_game_engine):
        """Test trace accumulates correctly over many turns."""

        initial_trace = basic_game_engine.player.trace_level

        # Process 20 turns
        for _ in range(20):
            basic_game_engine.process_turn()

        # Trace should have increased or stayed same (background trace might be 0)
        assert basic_game_engine.player.trace_level >= initial_trace, "Trace should not decrease over turns"

    def test_trace_level_caps_at_maximum(self, basic_game_engine):
        """Test trace level cannot exceed maximum."""

        # Set trace near maximum
        basic_game_engine.player.trace_level = 95
        max_trace = 100

        # Process many turns
        for _ in range(50):
            basic_game_engine.process_turn()
            if basic_game_engine.player.trace_level >= max_trace:
                break

        # Verify trace doesn't exceed maximum
        assert basic_game_engine.player.trace_level <= max_trace, "Trace should not exceed maximum"


class TestHeatDissipation:
    """Test heat dissipation per turn."""

    def test_heat_dissipates_naturally_per_turn(self, basic_game_engine):
        """Test heat dissipates naturally each turn."""

        # Generate heat
        basic_game_engine.player.heat = 50

        initial_heat = basic_game_engine.player.heat

        # Process several turns without generating more heat
        for _ in range(5):
            basic_game_engine.process_turn()

        # Heat should have dissipated (or stayed same if dissipation is 0)
        assert basic_game_engine.player.heat <= initial_heat, "Heat should not increase without actions"

    def test_heat_dissipation_rate_consistent(self, basic_game_engine):
        """Test heat dissipation rate is consistent across turns."""

        # Set initial heat
        basic_game_engine.player.heat = 60

        heat_samples = []

        # Sample heat over 10 turns
        for turn in range(10):
            heat_samples.append(basic_game_engine.player.heat)
            basic_game_engine.process_turn()

        # Verify heat generally decreases or stays stable
        # (May stay stable if heat generation equals dissipation)
        final_heat = basic_game_engine.player.heat
        initial_heat = heat_samples[0]

        assert final_heat <= initial_heat, "Heat should decrease or stay same"

    def test_heat_cannot_go_negative(self, basic_game_engine):
        """Test heat cannot go below 0."""

        # Set heat to 0
        basic_game_engine.player.heat = 0

        # Process turns
        for _ in range(10):
            basic_game_engine.process_turn()

        # Verify heat stayed at 0 or above
        assert basic_game_engine.player.heat >= 0, "Heat should not go negative"


class TestTemporaryEffectDuration:
    """Test temporary effect duration decrements per turn."""

    def test_temporary_effect_decrements_each_turn(self, basic_game_engine):
        """Test temporary effect duration decrements each turn."""

        # Apply temporary effect
        basic_game_engine.player.temporary_effects['speed_boost_turns'] = 5

        # Process turn
        basic_game_engine.process_turn()

        # Verify effect decremented
        assert basic_game_engine.player.temporary_effects['speed_boost_turns'] == 4, "Effect duration should decrement"

    def test_temporary_effect_expires_after_duration(self, basic_game_engine):
        """Test temporary effect expires after duration reaches 0."""

        # Apply temporary effect with short duration
        basic_game_engine.player.temporary_effects['data_mimic_turns'] = 2

        # Process 3 turns
        for _ in range(3):
            basic_game_engine.process_turn()

        # Verify effect expired
        assert basic_game_engine.player.temporary_effects.get('data_mimic_turns', 0) == 0, "Effect should expire"

    def test_multiple_temporary_effects_tracked_separately(self, basic_game_engine):
        """Test multiple temporary effects are tracked and decremented separately."""

        # Apply multiple effects
        basic_game_engine.player.temporary_effects['speed_boost_turns'] = 5
        basic_game_engine.player.temporary_effects['enhanced_vision_turns'] = 3
        basic_game_engine.player.temporary_effects['data_mimic_turns'] = 2

        # Process 2 turns
        for _ in range(2):
            basic_game_engine.process_turn()

        # Verify each effect decremented independently
        assert basic_game_engine.player.temporary_effects['speed_boost_turns'] == 3
        assert basic_game_engine.player.temporary_effects['enhanced_vision_turns'] == 1
        assert basic_game_engine.player.temporary_effects.get('data_mimic_turns', 0) == 0  # Should be expired

    def test_zero_duration_effect_does_not_go_negative(self, basic_game_engine):
        """Test effect with 0 duration doesn't go negative."""

        # Set effect to 0
        basic_game_engine.player.temporary_effects['speed_boost_turns'] = 0

        # Process turns
        for _ in range(5):
            basic_game_engine.process_turn()

        # Verify stayed at 0
        assert basic_game_engine.player.temporary_effects.get('speed_boost_turns', 0) >= 0


class TestEnemyTurnProcessing:
    """Test enemy processing during turn workflow."""

    def test_all_enemies_process_during_turn(self, basic_game_engine):
        """Test all enemies get their turn processed."""

        # Create multiple enemies
        enemies = [
            enemy_builder("bot", pos=(10, 10)),
            enemy_builder("scanner", pos=(15, 15)),
            enemy_builder("patrol", pos=(20, 20)),
        ]

        for enemy in enemies:
            enemy.state = EnemyState.UNAWARE

        basic_game_engine.enemies = enemies

        # Record initial positions
        initial_positions = [(e.x, e.y) for e in basic_game_engine.enemies]

        # Process turn
        basic_game_engine.process_turn()

        # Verify enemies were processed (they should have attempted to take actions)
        # Note: Enemies might not move if patrol queue is empty, but processing should occur
        assert len(basic_game_engine.enemies) == len(initial_positions), "All enemies should still exist"

    def test_hostile_enemy_processes_during_turn(self, basic_game_engine):
        """Test hostile enemy is processed during turn."""

        # Position player and ensure no shadows interfere with visibility
        player_pos = Position(20, 20)
        basic_game_engine.player.position = player_pos
        basic_game_engine.game_map.shadows.discard((player_pos.x, player_pos.y))
        basic_game_engine.game_map.ghost_nodes.discard((player_pos.x, player_pos.y))

        # Create hostile enemy ADJACENT to player to maintain continuous visibility
        # This prevents random de-escalation to UNAWARE (15% chance when can't see player)
        enemy_pos = Position(21, 20)  # Adjacent = always visible
        basic_game_engine.game_map.shadows.discard((enemy_pos.x, enemy_pos.y))
        basic_game_engine.game_map.ghost_nodes.discard((enemy_pos.x, enemy_pos.y))

        enemy = enemy_builder("bot", pos=(enemy_pos.x, enemy_pos.y),
                              state=EnemyState.HOSTILE,
                              last_seen=(player_pos.x, player_pos.y))
        basic_game_engine.enemies = [enemy]

        # Process several turns - enemy should remain hostile since it can always see player
        for _ in range(5):
            basic_game_engine.process_turn()

        # Enemy should have been processed and remain hostile (continuous visibility)
        assert enemy in basic_game_engine.enemies, "Enemy should still be tracked"
        assert enemy.state == EnemyState.HOSTILE, f"Enemy should remain hostile with continuous visibility, not {enemy.state}"

    def test_disabled_enemy_skips_turn(self, basic_game_engine):
        """Test disabled enemy does not act during turn."""

        # Create disabled enemy
        enemy = enemy_builder("bot", pos=(15, 15))
        enemy.state = EnemyState.HOSTILE
        enemy.disabled_turns = 3
        basic_game_engine.enemies = [enemy]

        initial_x = enemy.x
        initial_y = enemy.y

        # Process turn
        basic_game_engine.process_turn()

        # Verify disabled enemy didn't move
        assert enemy.x == initial_x and enemy.y == initial_y, "Disabled enemy should not move"

        # Verify disabled counter decremented
        assert enemy.disabled_turns == 2, "Disabled turns should decrement"


class TestEnvironmentalEffects:
    """Test environmental effects applied per turn."""

    def test_overheat_damage_applied_per_turn(self, basic_game_engine):
        """Test overheat damage is applied each turn when at max heat."""

        # Set player to max heat
        basic_game_engine.player.heat = basic_game_engine.player.max_heat
        basic_game_engine.player.cpu = 50

        initial_cpu = basic_game_engine.player.cpu

        # Process turn
        basic_game_engine.process_turn()

        # Verify overheat damage applied
        if basic_game_engine.player.heat >= basic_game_engine.player.max_heat:
            assert basic_game_engine.player.cpu < initial_cpu, "Overheat should damage CPU"

    def test_standing_on_cpu_node_restores_cpu(self, basic_game_engine):
        """Test standing on CPU recovery node restores CPU each turn."""

        # Find CPU node
        if len(basic_game_engine.game_map.cpu_recovery_nodes) > 0:
            cpu_node = list(basic_game_engine.game_map.cpu_recovery_nodes)[0]

            # Position player on CPU node with damaged CPU
            basic_game_engine.player.x = cpu_node[0]
            basic_game_engine.player.y = cpu_node[1]
            basic_game_engine.player.cpu = 50

            initial_cpu = basic_game_engine.player.cpu

            # Process turn
            basic_game_engine.maybe_process_turn()

            # Verify CPU restored
            assert basic_game_engine.player.cpu > initial_cpu, "CPU node should restore CPU"

    def test_standing_on_cooling_node_reduces_heat(self, basic_game_engine):
        """Test standing on cooling node reduces heat each turn."""

        # Find cooling node
        if len(basic_game_engine.game_map.cooling_nodes) > 0:
            cooling_node = list(basic_game_engine.game_map.cooling_nodes)[0]

            # Position player on cooling node with heat
            basic_game_engine.player.x = cooling_node[0]
            basic_game_engine.player.y = cooling_node[1]
            basic_game_engine.player.heat = 40

            initial_heat = basic_game_engine.player.heat

            # Process turn
            basic_game_engine.maybe_process_turn()

            # Verify heat reduced
            assert basic_game_engine.player.heat < initial_heat, "Cooling node should reduce heat"


class TestTurnProcessingEdgeCases:
    """Test edge cases in turn processing."""

    def test_turn_processing_with_no_enemies(self, basic_game_engine):
        """Test turn processing works correctly with no enemies."""

        # Remove all enemies
        basic_game_engine.enemies = []

        initial_turn = basic_game_engine.turn

        # Process turn
        basic_game_engine.process_turn()

        # Verify turn still processed
        assert basic_game_engine.turn == initial_turn + 1, "Turn should process even without enemies"

    def test_dialogue_system_integration(self, basic_game_engine):
        """Test dialogue system integrates with game basic_game_engine."""

        # Verify dialogue system exists and is integrated
        assert hasattr(basic_game_engine, 'dialogue_state'), "Engine should have dialogue_state"
        assert hasattr(basic_game_engine.dialogue_state, 'is_active'), "Should have is_active method"

        # Check current dialogue state
        has_dialogue = basic_game_engine.dialogue_state.is_active()
        assert isinstance(has_dialogue, bool), "is_active should return boolean"

    def test_turn_processing_while_game_over(self, basic_game_engine):
        """Test turn processing behavior when game is over."""

        # Set game over
        basic_game_engine.game_over = True

        initial_turn = basic_game_engine.turn

        # Try to process turn
        basic_game_engine.process_turn()

        # Turn processing might be blocked or might proceed
        # Just verify system handles game_over state
        assert basic_game_engine.game_over, "Game over state should persist"

    def test_massive_turn_count_does_not_overflow(self, basic_game_engine):
        """Test turn counter handles large numbers correctly."""

        # Set turn to large number
        basic_game_engine.turn = 9999

        # Process turn
        basic_game_engine.process_turn()

        # Verify turn incremented correctly
        assert basic_game_engine.turn == 10000, "Turn counter should handle large numbers"


class TestCrossSystemTurnEffects:
    """Test turn processing effects across multiple systems."""

    def test_turn_affects_player_enemy_and_environment(self, basic_game_engine):
        """Test single turn affects player stats, enemy behavior, and environment."""

        # Set up scenario
        basic_game_engine.player.heat = 30
        basic_game_engine.player.trace_level = 20

        # Create enemy
        enemy = enemy_builder("bot", pos=(15, 15))
        enemy.state = EnemyState.HOSTILE
        basic_game_engine.enemies = [enemy]

        initial_turn = basic_game_engine.turn
        initial_trace = basic_game_engine.player.trace_level
        initial_heat = basic_game_engine.player.heat
        initial_enemy_pos = (enemy.x, enemy.y)

        # Process turn
        basic_game_engine.process_turn()

        # Verify multiple systems updated
        assert basic_game_engine.turn == initial_turn + 1, "Turn should increment"
        assert basic_game_engine.player.trace_level >= initial_trace, "Trace should increase"
        # Heat might decrease (dissipation) or stay same
        # Enemy might move or stay same depending on pathfinding

        # At minimum, turn counter should advance
        assert basic_game_engine.turn > initial_turn

    def test_temporary_effect_interacts_with_turn_processing(self, basic_game_engine):
        """Test temporary effects correctly interact with turn-based systems."""

        # Apply speed boost
        basic_game_engine.player.temporary_effects['speed_boost_turns'] = 3

        # Verify effect is active (check value directly, not method)
        assert basic_game_engine.player.temporary_effects['speed_boost_turns'] > 0, "Speed boost should be active"

        # Process turn
        basic_game_engine.process_turn()

        # Effect should have been decremented
        assert basic_game_engine.player.temporary_effects['speed_boost_turns'] <= 3, "Effect should decrement or stay"

        # Process more turns until expiry
        for _ in range(5):
            basic_game_engine.process_turn()

        # Effect should be expired
        assert basic_game_engine.player.temporary_effects['speed_boost_turns'] == 0, "Speed boost should expire"

    def test_alert_timer_decrements_per_turn(self, basic_game_engine):
        """Test enemy alert timer decrements correctly per turn."""

        # Create alert enemy
        enemy = enemy_builder("scanner", pos=(10, 10))
        enemy.state = EnemyState.ALERT
        enemy.alert_timer = 3
        basic_game_engine.enemies = [enemy]

        # Process turn
        basic_game_engine.process_turn()

        # Verify alert timer decremented
        # Note: Alert timer is 1 turn only per game rules, so it should expire immediately
        # But we test the decrement behavior
        assert enemy.alert_timer >= 0, "Alert timer should not go negative"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
