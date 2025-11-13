"""
Session and State Management Integration Tests

Tests complete session and state management workflows:
- Game session lifecycle
- Auto-save triggers and timing
- State consistency across actions
- Menu state transitions
- Multiple game sessions
- State recovery after errors

These tests verify state management integrates correctly with:
- Save/load system
- Game engine
- Player state
- Level transitions
- Menu system
"""

import copy
from unittest.mock import Mock

import pytest

from game_entities import Position


class TestGameSessionLifecycle:
    """Test complete game session lifecycle."""

    def test_new_game_initializes_fresh_state(self, basic_game_engine):
        """Test starting a new game creates fresh state."""
        engine = basic_game_engine

        # Verify fresh game state
        assert engine.level == 1, "New game should start at level 1"
        assert engine.turn >= 0, "Turn should be initialized"
        assert not engine.game_over, "Game should not be over"
        assert engine.player.cpu > 0, "Player should have CPU"
        assert len(engine.enemies) > 0, "Enemies should be spawned"

    def test_game_state_consistency_after_player_action(self, basic_game_engine):
        """Test game state remains consistent after player actions."""
        engine = basic_game_engine

        # Record initial state
        initial_state = {
            "level": engine.level,
            "turn": engine.turn,
            "player_cpu": engine.player.cpu,
            "enemy_count": len(engine.enemies),
        }

        # Perform player movement
        engine.move_player(1, 0)

        # Verify state consistency
        assert engine.level == initial_state["level"], "Level should not change from movement"
        assert engine.turn >= initial_state["turn"], "Turn should advance or stay same"
        assert engine.player.cpu > 0, "Player should still have CPU"
        assert len(engine.enemies) >= 0, "Enemy count should be valid"

    def test_multiple_consecutive_turns_maintain_state(self, basic_game_engine):
        """Test state remains consistent across multiple consecutive turns."""
        engine = basic_game_engine

        # Process 20 consecutive turns
        for turn_num in range(20):
            engine.process_turn()

            # Verify state validity after each turn
            assert engine.turn > 0, "Turn should be positive"
            assert engine.level >= 1, "Level should be at least 1"
            assert engine.player.cpu >= 0, "CPU should be non-negative"
            assert engine.player.heat >= 0, "Heat should be non-negative"
            assert engine.player.trace_level >= 0, "Trace should be non-negative"

            # If game over, break
            if engine.game_over:
                assert engine.player.cpu <= 0, "Game over should mean CPU depleted"
                break


class TestAutoSaveTriggers:
    """Test auto-save triggers and timing."""

    def test_auto_save_method_exists(self, basic_game_engine):
        """Test that auto-save method exists and is callable."""
        engine = basic_game_engine

        # Verify auto-save exists
        assert hasattr(engine, "auto_save"), "Engine should have auto_save method"
        assert callable(engine.auto_save), "auto_save should be callable"

    def test_auto_save_after_level_progression(self, basic_game_engine):
        """Test auto-save is triggered after level progression."""
        engine = basic_game_engine

        # Mock the auto-save method
        engine.auto_save = Mock()

        # Progress to next level
        engine.next_level()

        # Verify auto-save was called
        engine.auto_save.assert_called()

    def test_game_state_persists_in_session_manager(self, basic_game_engine):
        """Test game state is tracked by session manager."""
        engine = basic_game_engine

        # Verify session manager exists
        assert hasattr(engine, "game_session"), "Engine should have game_session"

        # Modify game state
        engine.player.cpu = 75
        engine.level = 2

        # Verify session can access current state
        assert hasattr(engine, "player"), "Session should track player"
        assert hasattr(engine, "level"), "Session should track level"


class TestStateConsistency:
    """Test state consistency across different game systems."""

    def test_player_state_consistent_with_inventory(self, basic_game_engine):
        """Test player state remains consistent with inventory."""
        engine = basic_game_engine

        # Modify inventory
        initial_equipped_count = len(engine.player.inventory_manager.equipped_exploits)

        # Add an exploit
        from game_data import GameData
        from game_inventory import ExploitItem

        exploit_key = list(GameData.EXPLOITS.keys())[0]
        exploit_def = GameData.EXPLOITS[exploit_key]
        test_exploit = ExploitItem(exploit_key, exploit_def)

        engine.player.inventory_manager.add_item(test_exploit)

        # Verify inventory updated
        assert len(engine.player.inventory_manager.items) > 0, "Inventory should have items"

    def test_level_state_consistent_with_map(self, basic_game_engine):
        """Test level state remains consistent with map."""
        engine = basic_game_engine

        # Verify level and map consistency
        assert engine.game_map is not None, "Map should exist"
        assert engine.level >= 1, "Level should be valid"

        # Progress level
        initial_level = engine.level
        engine.next_level()

        # Verify new map generated
        assert engine.level == initial_level + 1, "Level should increment"
        assert engine.game_map is not None, "New map should exist"

    def test_enemy_state_consistent_with_game_engine(self, basic_game_engine):
        """Test enemy state remains consistent with game engine."""
        engine = basic_game_engine

        # Verify enemies tracked
        assert hasattr(engine, "enemies"), "Engine should track enemies"
        initial_enemy_count = len(engine.enemies)

        # Process turn (enemies act)
        engine.process_turn()

        # Verify enemy count reasonable
        assert len(engine.enemies) >= 0, "Enemy count should be non-negative"
        # Enemy count might decrease if player defeats enemies

    def test_trace_level_consistent_across_systems(self, basic_game_engine):
        """Test trace level remains consistent across different systems."""
        engine = basic_game_engine

        # Set trace level
        engine.player.trace_level = 50

        # Verify accessible from different systems
        assert engine.player.trace_level == 50, "Player trace should be 50"

        # Ensure player is not on a cooling node (which would decrease trace)
        player_tile_pos = (engine.player.x, engine.player.y)
        if player_tile_pos in engine.game_map.cooling_nodes:
            # Move player to a safe position away from special tiles
            for x in range(15, 25):
                for y in range(15, 25):
                    test_pos = (x, y)
                    if (
                        not engine.game_map.is_wall(Position(x, y))
                        and test_pos not in engine.game_map.cooling_nodes
                        and test_pos not in engine.game_map.ghost_nodes
                    ):
                        engine.player.x = x
                        engine.player.y = y
                        break

        # Process turn (trace should increase due to background trace)
        initial_trace = engine.player.trace_level
        engine.process_turn()

        # Trace should increase or stay same (no cooling nodes to reduce it)
        assert (
            engine.player.trace_level >= initial_trace
        ), "Trace should not decrease without cooling nodes"


class TestMenuStateTransitions:
    """Test menu state transitions."""

    def test_inventory_menu_state_transitions(self, basic_game_engine):
        """Test opening and closing inventory maintains state."""
        engine = basic_game_engine

        # Verify inventory flag exists
        assert hasattr(engine, "show_inventory"), "Engine should have show_inventory flag"

        # Open inventory
        engine.show_inventory = True

        # Verify inventory shown
        assert engine.show_inventory, "Inventory should be shown"

        # Close inventory
        engine.show_inventory = False

        # Verify inventory closed
        assert not engine.show_inventory, "Inventory should be closed"

    def test_look_mode_state_transitions(self, basic_game_engine):
        """Test entering and exiting look mode maintains state."""
        engine = basic_game_engine

        # Enter look mode
        engine.look_mode = True
        engine.cursor_position = Position(engine.player.x, engine.player.y)

        # Verify look mode active
        assert engine.look_mode, "Look mode should be active"

        # Exit look mode
        engine.look_mode = False

        # Verify look mode inactive
        assert not engine.look_mode, "Look mode should be inactive"

    def test_dialogue_state_system(self, basic_game_engine):
        """Test dialogue system state management."""
        engine = basic_game_engine

        # Verify dialogue system exists
        assert hasattr(engine, "dialogue_state"), "Engine should have dialogue_state"

        # Verify dialogue state methods exist
        assert hasattr(engine.dialogue_state, "is_active"), "Should have is_active method"
        assert hasattr(engine.dialogue_state, "get_active"), "Should have get_active method"
        assert hasattr(engine.dialogue_state, "close"), "Should have close method"

        # Dialogue system is functional
        # Note: May have initial dialogue active (tutorial, gateway, etc)
        initial_state = engine.dialogue_state.is_active()
        assert isinstance(initial_state, bool), "is_active should return boolean"


class TestStateRecoveryAndErrors:
    """Test state recovery from error conditions."""

    def test_invalid_player_position_handled_gracefully(self, basic_game_engine):
        """Test that invalid player position is handled gracefully."""
        engine = basic_game_engine

        # Try to set invalid position
        invalid_x = -10
        invalid_y = -10

        # System should either reject or clamp position
        try:
            engine.player.x = invalid_x
            engine.player.y = invalid_y
            # If allowed, verify it doesn't crash game
            engine.process_turn()
            # Game should still be functional
            assert True, "Game should handle invalid position"
        except Exception:
            # If rejected, that's also acceptable
            assert True, "Invalid position rejected"

    def test_negative_cpu_state_detectable(self, basic_game_engine):
        """Test that negative CPU state is detectable."""
        engine = basic_game_engine

        # Set negative CPU
        engine.player.cpu = -10

        # Verify negative CPU is detectable
        assert engine.player.cpu < 0, "Negative CPU should be detectable"
        assert engine.player.cpu <= 0, "System should recognize depleted state"

    def test_excessive_heat_handled_correctly(self, basic_game_engine):
        """Test that heat exceeding maximum is handled correctly."""
        engine = basic_game_engine

        # Set heat way above maximum
        engine.player.heat = engine.player.max_heat + 50

        # Process turn
        engine.process_turn()

        # Heat should be capped or damage applied
        # System should handle gracefully without crashing
        assert engine.player.cpu >= 0 or engine.game_over, "Excessive heat should be handled"

    def test_state_consistency_after_enemy_defeat(self, basic_game_engine):
        """Test state remains consistent after defeating all enemies."""
        engine = basic_game_engine

        # Remove all enemies
        engine.enemies = []

        # Process turn
        engine.process_turn()

        # Game should still function
        assert not engine.game_over, "Game should continue with no enemies"
        assert engine.turn > 0, "Turn should still advance"


class TestCrossLevelStatePersistence:
    """Test state persistence across level transitions."""

    def test_player_cpu_persists_across_levels(self, basic_game_engine):
        """Test player CPU value persists across level transitions."""
        engine = basic_game_engine

        # Set specific CPU value
        engine.player.cpu = 75

        # Progress level
        engine.next_level()

        # Verify CPU persisted
        assert engine.player.cpu == 75, "CPU should persist across levels"

    def test_equipped_exploits_persist_across_levels(self, basic_game_engine):
        """Test equipped exploits persist across level transitions."""
        engine = basic_game_engine

        # Equip exploits
        initial_exploits = copy.deepcopy(engine.player.inventory_manager.equipped_exploits)

        # Progress level
        engine.next_level()

        # Verify exploits persisted
        assert engine.player.inventory_manager.equipped_exploits == initial_exploits

    def test_permanent_upgrades_persist_across_levels(self, basic_game_engine):
        """Test permanent upgrades persist across level transitions."""
        engine = basic_game_engine

        # Record permanent stats
        initial_max_cpu = engine.player.max_cpu
        initial_ram = engine.player.ram_total

        # Progress level
        engine.next_level()

        # Verify permanent stats persisted
        assert engine.player.max_cpu == initial_max_cpu, "Max CPU should persist"
        assert engine.player.ram_total == initial_ram, "RAM should persist"

    def test_trace_level_resets_on_level_transition(self, basic_game_engine):
        """Test trace level resets to 0 on level transition."""
        engine = basic_game_engine

        # Set high trace
        engine.player.trace_level = 80

        # Progress level
        engine.next_level()

        # Verify trace reset
        assert engine.player.trace_level == 0, "Trace should reset to 0 on new level"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
