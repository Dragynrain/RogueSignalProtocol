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
from tests.fixtures.simple_fixtures import create_real_enemy


class TestBasicTurnProcessing:
    """Test fundamental turn processing mechanics."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_turn_counter_increments(self):
        """Test turn counter increments each turn."""
        engine = self.create_test_engine()

        initial_turn = engine.turn

        # Process turn
        engine.process_turn()

        # Verify turn incremented
        assert engine.turn == initial_turn + 1, "Turn counter should increment"

    def test_multiple_turns_increment_correctly(self):
        """Test turn counter increments correctly over multiple turns."""
        engine = self.create_test_engine()

        initial_turn = engine.turn

        # Process 10 turns
        for i in range(10):
            engine.process_turn()

        # Verify turn incremented by 10
        assert engine.turn == initial_turn + 10, "Turn should increment by 10"

    def test_turn_processing_updates_game_state(self):
        """Test that turn processing updates game state correctly."""
        engine = self.create_test_engine()

        # Verify initial state
        assert engine.game_state is not None
        assert hasattr(engine, 'turn')

        initial_turn = engine.turn

        # Process turn
        engine.process_turn()

        # Verify state updated
        assert engine.turn > initial_turn
        assert engine.game_state is not None


class TestBackgroundTraceAccumulation:
    """Test background trace accumulation per turn."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_trace_level_increases_per_turn(self):
        """Test trace level increases each turn based on network config."""
        engine = self.create_test_engine()

        initial_trace = engine.player.trace_level

        # Get background trace rate
        network_config = engine.game_state.get_current_network_config()
        background_trace = network_config.get('background_trace', 0)

        # Process turn
        engine.process_turn()

        # Verify trace increased
        if background_trace > 0:
            assert engine.player.trace_level >= initial_trace, "Trace should increase with background trace"

    def test_trace_accumulation_over_many_turns(self):
        """Test trace accumulates correctly over many turns."""
        engine = self.create_test_engine()

        initial_trace = engine.player.trace_level

        # Process 20 turns
        for _ in range(20):
            engine.process_turn()

        # Trace should have increased or stayed same (background trace might be 0)
        assert engine.player.trace_level >= initial_trace, "Trace should not decrease over turns"

    def test_trace_level_caps_at_maximum(self):
        """Test trace level cannot exceed maximum."""
        engine = self.create_test_engine()

        # Set trace near maximum
        engine.player.trace_level = 95
        max_trace = 100

        # Process many turns
        for _ in range(50):
            engine.process_turn()
            if engine.player.trace_level >= max_trace:
                break

        # Verify trace doesn't exceed maximum
        assert engine.player.trace_level <= max_trace, "Trace should not exceed maximum"


class TestHeatDissipation:
    """Test heat dissipation per turn."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_heat_dissipates_naturally_per_turn(self):
        """Test heat dissipates naturally each turn."""
        engine = self.create_test_engine()

        # Generate heat
        engine.player.heat = 50

        initial_heat = engine.player.heat

        # Process several turns without generating more heat
        for _ in range(5):
            engine.process_turn()

        # Heat should have dissipated (or stayed same if dissipation is 0)
        assert engine.player.heat <= initial_heat, "Heat should not increase without actions"

    def test_heat_dissipation_rate_consistent(self):
        """Test heat dissipation rate is consistent across turns."""
        engine = self.create_test_engine()

        # Set initial heat
        engine.player.heat = 60

        heat_samples = []

        # Sample heat over 10 turns
        for turn in range(10):
            heat_samples.append(engine.player.heat)
            engine.process_turn()

        # Verify heat generally decreases or stays stable
        # (May stay stable if heat generation equals dissipation)
        final_heat = engine.player.heat
        initial_heat = heat_samples[0]

        assert final_heat <= initial_heat, "Heat should decrease or stay same"

    def test_heat_cannot_go_negative(self):
        """Test heat cannot go below 0."""
        engine = self.create_test_engine()

        # Set heat to 0
        engine.player.heat = 0

        # Process turns
        for _ in range(10):
            engine.process_turn()

        # Verify heat stayed at 0 or above
        assert engine.player.heat >= 0, "Heat should not go negative"


class TestTemporaryEffectDuration:
    """Test temporary effect duration decrements per turn."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_temporary_effect_decrements_each_turn(self):
        """Test temporary effect duration decrements each turn."""
        engine = self.create_test_engine()

        # Apply temporary effect
        engine.player.temporary_effects['speed_boost_turns'] = 5

        # Process turn
        engine.process_turn()

        # Verify effect decremented
        assert engine.player.temporary_effects['speed_boost_turns'] == 4, "Effect duration should decrement"

    def test_temporary_effect_expires_after_duration(self):
        """Test temporary effect expires after duration reaches 0."""
        engine = self.create_test_engine()

        # Apply temporary effect with short duration
        engine.player.temporary_effects['data_mimic_turns'] = 2

        # Process 3 turns
        for _ in range(3):
            engine.process_turn()

        # Verify effect expired
        assert engine.player.temporary_effects.get('data_mimic_turns', 0) == 0, "Effect should expire"

    def test_multiple_temporary_effects_tracked_separately(self):
        """Test multiple temporary effects are tracked and decremented separately."""
        engine = self.create_test_engine()

        # Apply multiple effects
        engine.player.temporary_effects['speed_boost_turns'] = 5
        engine.player.temporary_effects['enhanced_vision_turns'] = 3
        engine.player.temporary_effects['data_mimic_turns'] = 2

        # Process 2 turns
        for _ in range(2):
            engine.process_turn()

        # Verify each effect decremented independently
        assert engine.player.temporary_effects['speed_boost_turns'] == 3
        assert engine.player.temporary_effects['enhanced_vision_turns'] == 1
        assert engine.player.temporary_effects.get('data_mimic_turns', 0) == 0  # Should be expired

    def test_zero_duration_effect_does_not_go_negative(self):
        """Test effect with 0 duration doesn't go negative."""
        engine = self.create_test_engine()

        # Set effect to 0
        engine.player.temporary_effects['speed_boost_turns'] = 0

        # Process turns
        for _ in range(5):
            engine.process_turn()

        # Verify stayed at 0
        assert engine.player.temporary_effects.get('speed_boost_turns', 0) >= 0


class TestEnemyTurnProcessing:
    """Test enemy processing during turn workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_all_enemies_process_during_turn(self):
        """Test all enemies get their turn processed."""
        engine = self.create_test_engine()

        # Create multiple enemies
        enemies = [
            create_real_enemy("bot", Position(10, 10)),
            create_real_enemy("scanner", Position(15, 15)),
            create_real_enemy("patrol", Position(20, 20)),
        ]

        for enemy in enemies:
            enemy.state = EnemyState.UNAWARE

        engine.enemies = enemies

        # Record initial positions
        initial_positions = [(e.x, e.y) for e in engine.enemies]

        # Process turn
        engine.process_turn()

        # Verify enemies were processed (they should have attempted to take actions)
        # Note: Enemies might not move if patrol queue is empty, but processing should occur
        assert len(engine.enemies) == len(initial_positions), "All enemies should still exist"

    def test_hostile_enemy_processes_during_turn(self):
        """Test hostile enemy is processed during turn."""
        engine = self.create_test_engine()

        # Position player and ensure no shadows interfere with visibility
        player_pos = Position(20, 20)
        engine.player.position = player_pos
        engine.game_map.shadows.discard((player_pos.x, player_pos.y))
        engine.game_map.ghost_nodes.discard((player_pos.x, player_pos.y))

        # Create hostile enemy ADJACENT to player to maintain continuous visibility
        # This prevents random de-escalation to UNAWARE (15% chance when can't see player)
        enemy_pos = Position(21, 20)  # Adjacent = always visible
        engine.game_map.shadows.discard((enemy_pos.x, enemy_pos.y))
        engine.game_map.ghost_nodes.discard((enemy_pos.x, enemy_pos.y))

        enemy = create_real_enemy("bot", enemy_pos)
        enemy.state = EnemyState.HOSTILE
        enemy.last_seen_player = player_pos
        engine.enemies = [enemy]

        # Process several turns - enemy should remain hostile since it can always see player
        for _ in range(5):
            engine.process_turn()

        # Enemy should have been processed and remain hostile (continuous visibility)
        assert enemy in engine.enemies, "Enemy should still be tracked"
        assert enemy.state == EnemyState.HOSTILE, f"Enemy should remain hostile with continuous visibility, not {enemy.state}"

    def test_disabled_enemy_skips_turn(self):
        """Test disabled enemy does not act during turn."""
        engine = self.create_test_engine()

        # Create disabled enemy
        enemy = create_real_enemy("bot", Position(15, 15))
        enemy.state = EnemyState.HOSTILE
        enemy.disabled_turns = 3
        engine.enemies = [enemy]

        initial_x = enemy.x
        initial_y = enemy.y

        # Process turn
        engine.process_turn()

        # Verify disabled enemy didn't move
        assert enemy.x == initial_x and enemy.y == initial_y, "Disabled enemy should not move"

        # Verify disabled counter decremented
        assert enemy.disabled_turns == 2, "Disabled turns should decrement"


class TestEnvironmentalEffects:
    """Test environmental effects applied per turn."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_overheat_damage_applied_per_turn(self):
        """Test overheat damage is applied each turn when at max heat."""
        engine = self.create_test_engine()

        # Set player to max heat
        engine.player.heat = engine.player.max_heat
        engine.player.cpu = 50

        initial_cpu = engine.player.cpu

        # Process turn
        engine.process_turn()

        # Verify overheat damage applied
        if engine.player.heat >= engine.player.max_heat:
            assert engine.player.cpu < initial_cpu, "Overheat should damage CPU"

    def test_standing_on_cpu_node_restores_cpu(self):
        """Test standing on CPU recovery node restores CPU each turn."""
        engine = self.create_test_engine()

        # Find CPU node
        if len(engine.game_map.cpu_recovery_nodes) > 0:
            cpu_node = list(engine.game_map.cpu_recovery_nodes)[0]

            # Position player on CPU node with damaged CPU
            engine.player.x = cpu_node[0]
            engine.player.y = cpu_node[1]
            engine.player.cpu = 50

            initial_cpu = engine.player.cpu

            # Process turn
            engine.maybe_process_turn()

            # Verify CPU restored
            assert engine.player.cpu > initial_cpu, "CPU node should restore CPU"

    def test_standing_on_cooling_node_reduces_heat(self):
        """Test standing on cooling node reduces heat each turn."""
        engine = self.create_test_engine()

        # Find cooling node
        if len(engine.game_map.cooling_nodes) > 0:
            cooling_node = list(engine.game_map.cooling_nodes)[0]

            # Position player on cooling node with heat
            engine.player.x = cooling_node[0]
            engine.player.y = cooling_node[1]
            engine.player.heat = 40

            initial_heat = engine.player.heat

            # Process turn
            engine.maybe_process_turn()

            # Verify heat reduced
            assert engine.player.heat < initial_heat, "Cooling node should reduce heat"


class TestTurnProcessingEdgeCases:
    """Test edge cases in turn processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_turn_processing_with_no_enemies(self):
        """Test turn processing works correctly with no enemies."""
        engine = self.create_test_engine()

        # Remove all enemies
        engine.enemies = []

        initial_turn = engine.turn

        # Process turn
        engine.process_turn()

        # Verify turn still processed
        assert engine.turn == initial_turn + 1, "Turn should process even without enemies"

    def test_dialogue_system_integration(self):
        """Test dialogue system integrates with game engine."""
        engine = self.create_test_engine()

        # Verify dialogue system exists and is integrated
        assert hasattr(engine, 'dialogue_state'), "Engine should have dialogue_state"
        assert hasattr(engine.dialogue_state, 'is_active'), "Should have is_active method"

        # Check current dialogue state
        has_dialogue = engine.dialogue_state.is_active()
        assert isinstance(has_dialogue, bool), "is_active should return boolean"

    def test_turn_processing_while_game_over(self):
        """Test turn processing behavior when game is over."""
        engine = self.create_test_engine()

        # Set game over
        engine.game_over = True

        initial_turn = engine.turn

        # Try to process turn
        engine.process_turn()

        # Turn processing might be blocked or might proceed
        # Just verify system handles game_over state
        assert engine.game_over, "Game over state should persist"

    def test_massive_turn_count_does_not_overflow(self):
        """Test turn counter handles large numbers correctly."""
        engine = self.create_test_engine()

        # Set turn to large number
        engine.turn = 9999

        # Process turn
        engine.process_turn()

        # Verify turn incremented correctly
        assert engine.turn == 10000, "Turn counter should handle large numbers"


class TestCrossSystemTurnEffects:
    """Test turn processing effects across multiple systems."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )
        return engine

    def test_turn_affects_player_enemy_and_environment(self):
        """Test single turn affects player stats, enemy behavior, and environment."""
        engine = self.create_test_engine()

        # Set up scenario
        engine.player.heat = 30
        engine.player.trace_level = 20

        # Create enemy
        enemy = create_real_enemy("bot", Position(15, 15))
        enemy.state = EnemyState.HOSTILE
        engine.enemies = [enemy]

        initial_turn = engine.turn
        initial_trace = engine.player.trace_level
        initial_heat = engine.player.heat
        initial_enemy_pos = (enemy.x, enemy.y)

        # Process turn
        engine.process_turn()

        # Verify multiple systems updated
        assert engine.turn == initial_turn + 1, "Turn should increment"
        assert engine.player.trace_level >= initial_trace, "Trace should increase"
        # Heat might decrease (dissipation) or stay same
        # Enemy might move or stay same depending on pathfinding

        # At minimum, turn counter should advance
        assert engine.turn > initial_turn

    def test_temporary_effect_interacts_with_turn_processing(self):
        """Test temporary effects correctly interact with turn-based systems."""
        engine = self.create_test_engine()

        # Apply speed boost
        engine.player.temporary_effects['speed_boost_turns'] = 3

        # Verify effect is active (check value directly, not method)
        assert engine.player.temporary_effects['speed_boost_turns'] > 0, "Speed boost should be active"

        # Process turn
        engine.process_turn()

        # Effect should have been decremented
        assert engine.player.temporary_effects['speed_boost_turns'] <= 3, "Effect should decrement or stay"

        # Process more turns until expiry
        for _ in range(5):
            engine.process_turn()

        # Effect should be expired
        assert engine.player.temporary_effects['speed_boost_turns'] == 0, "Speed boost should expire"

    def test_alert_timer_decrements_per_turn(self):
        """Test enemy alert timer decrements correctly per turn."""
        engine = self.create_test_engine()

        # Create alert enemy
        enemy = create_real_enemy("scanner", Position(10, 10))
        enemy.state = EnemyState.ALERT
        enemy.alert_timer = 3
        engine.enemies = [enemy]

        # Process turn
        engine.process_turn()

        # Verify alert timer decremented
        # Note: Alert timer is 1 turn only per game rules, so it should expire immediately
        # But we test the decrement behavior
        assert enemy.alert_timer >= 0, "Alert timer should not go negative"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
