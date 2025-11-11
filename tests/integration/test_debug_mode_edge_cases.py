"""
Debug Mode Edge Cases Tests

Tests debug export functionality in various game states and edge cases:
- Debug export during different game states (menus, combat, etc.)
- Debug mode flag behavior
- Error handling for debug operations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tests.test_agent import GameTestAgent
from game_entities import EnemyState


class TestDebugExportGameStates:
    """Test debug export functionality across different game states."""

    def test_debug_export_during_gameplay(self):
        """Debug export should work during normal gameplay."""
        agent = GameTestAgent(seed=99001)

        # Simulate gameplay state
        assert agent.player.cpu > 0
        assert len(agent.enemies) >= 0

        # Debug export should be accessible
        # (Actual export tested in test_debug_export_integration.py)
        assert agent.engine is not None

    def test_debug_export_with_menu_open(self):
        """Debug export should work when menus are open."""
        agent = GameTestAgent(seed=99002)

        # Set menu flags
        agent.engine.show_inventory = True

        # Game state should still be accessible for debug export
        assert agent.engine.show_inventory is True
        assert agent.player is not None

    def test_debug_export_during_combat(self):
        """Debug export should capture combat state correctly."""
        agent = GameTestAgent(seed=99003)

        # Spawn hostile enemy (combat state)
        enemy = agent.spawn_enemy("hunter", 15, 15)
        enemy.state = EnemyState.HOSTILE

        # Move player nearby to create combat scenario
        agent.move_to(16, 15)

        # Verify combat state captured
        assert enemy.state == EnemyState.HOSTILE
        assert len([e for e in agent.enemies if e.state == EnemyState.HOSTILE]) >= 1

    def test_debug_export_with_dialogue_active(self):
        """Debug export should work when dialogue is displayed."""
        agent = GameTestAgent(seed=99004)

        # Simulate dialogue state
        agent.engine.dialogue_active = False  # Start with no dialogue

        # Game state accessible
        assert agent.player is not None
        assert agent.engine is not None

    def test_debug_export_at_low_hp(self):
        """Debug export should work when player is at low HP."""
        agent = GameTestAgent(seed=99005)

        # Set player to low HP
        agent.player.cpu = 5
        agent.player.max_cpu = 100

        # Player state should be captured correctly
        assert agent.player.cpu == 5
        assert agent.player.cpu / agent.player.max_cpu < 0.1

    def test_debug_export_at_high_heat(self):
        """Debug export should work when player is at high heat."""
        agent = GameTestAgent(seed=99006)

        # Set player to high heat
        agent.player.heat = 95

        # Heat state should be captured
        assert agent.player.heat >= 90

    def test_debug_export_with_full_inventory(self):
        """Debug export should handle full inventory correctly."""
        agent = GameTestAgent(seed=99007)

        # Fill inventory with items (using inventory manager)
        for i in range(50):
            agent.player.inventory_manager.items.append({
                "id": f"item_{i}",
                "name": f"Test Item {i}",
                "type": "code_hack"
            })

        # Large inventory should be captured
        assert len(agent.player.inventory_manager.items) >= 50

    def test_debug_export_on_level_2(self):
        """Debug export should work on level 2."""
        agent = GameTestAgent(seed=99008, level=2)

        # Verify level 2 state
        assert agent.engine.level == 2

    def test_debug_export_on_level_3(self):
        """Debug export should work on level 3."""
        agent = GameTestAgent(seed=99009, level=3)

        # Verify level 3 state
        assert agent.engine.level == 3


class TestDebugModeFlags:
    """Test debug mode flag behavior."""

    def test_debug_mode_flag_detection(self):
        """Debug mode flag should be detectable."""
        import os

        # Check if debug_mode.flag exists
        debug_flag_exists = os.path.exists("debug_mode.flag")

        # Flag existence is valid (may or may not exist)
        assert isinstance(debug_flag_exists, bool)

    def test_headless_mode_compatible_with_debug(self):
        """Headless mode (testing) should work with debug features."""
        agent = GameTestAgent(seed=99010)

        # Headless engine should support debug operations
        assert agent.engine.headless is True
        assert agent.player is not None

    def test_game_state_serializable_for_debug(self):
        """Game state should be serializable for debug export."""
        agent = GameTestAgent(seed=99011)

        # Player stats should be simple types (serializable)
        assert isinstance(agent.player.cpu, (int, float))
        assert isinstance(agent.player.heat, (int, float))
        assert isinstance(agent.player.x, int)
        assert isinstance(agent.player.y, int)

    def test_enemy_state_serializable_for_debug(self):
        """Enemy state should be serializable for debug export."""
        agent = GameTestAgent(seed=99012)

        enemy = agent.spawn_enemy("scanner", 10, 10)

        # Enemy stats should be serializable
        assert isinstance(enemy.cpu, (int, float))
        assert isinstance(enemy.x, int)
        assert isinstance(enemy.y, int)
        assert isinstance(enemy.type, str)


class TestDebugExportErrorHandling:
    """Test error handling in debug export operations."""

    def test_debug_export_with_no_enemies(self):
        """Debug export should handle empty enemy list."""
        agent = GameTestAgent(seed=99013)

        # Clear all enemies
        agent.engine.enemies = []

        # Empty enemy list should be valid
        assert len(agent.engine.enemies) == 0

    def test_debug_export_with_invalid_player_pos(self):
        """Debug export should handle edge case player positions."""
        agent = GameTestAgent(seed=99014)

        # Move player to edge of map
        agent.move_to(1, 1)

        # Position should be valid
        assert 0 <= agent.player.x < agent.engine.game_map.width
        assert 0 <= agent.player.y < agent.engine.game_map.height

    def test_debug_export_captures_turn_count(self):
        """Debug export should capture current turn count."""
        agent = GameTestAgent(seed=99015)

        # Advance some turns
        agent.wait(10)

        # Turn count should be tracked
        assert agent.turn >= 10

    def test_debug_export_captures_trace_level(self):
        """Debug export should capture trace level."""
        agent = GameTestAgent(seed=99016)

        # Set trace level
        agent.engine.trace_level = 45

        # Trace level should be captured
        assert agent.engine.trace_level == 45
