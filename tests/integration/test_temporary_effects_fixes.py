#!/usr/bin/env python3
"""
Integration tests for temporary effects decay rate fixes.
Tests real game scenarios to prevent double-decrementing bugs.
"""

import unittest
from unittest.mock import Mock, patch

from game_engine import GameEngine
from game_characters import Player
from game_state import GameStateManager, TurnProcessor, MessageLog
from game_config import GameSettings
from game_entities import Position


class TestTemporaryEffectsDecayFixes(unittest.TestCase):
    """Test temporary effects decay at correct rates in real game scenarios."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def setUp(self):
        """Set up test game engine with real components."""
        self.game_settings = GameSettings()
        self.engine = self.create_test_engine()
        self.player = self.engine.player

    def test_data_mimic_decays_once_per_turn(self):
        """Test that data mimic effect decays exactly 1 per turn, not 2."""
        # Set data mimic effect to 5 turns
        self.player.temporary_effects['data_mimic_turns'] = 5

        # Process one complete turn
        initial_value = self.player.temporary_effects['data_mimic_turns']
        self.engine.process_turn()
        after_one_turn = self.player.temporary_effects['data_mimic_turns']

        # Should decrease by exactly 1
        self.assertEqual(after_one_turn, initial_value - 1,
                        f"Data mimic should decay by 1 per turn, was {initial_value} -> {after_one_turn}")

        # Test multiple turns to ensure consistent decay
        for expected_value in [3, 2, 1, 0]:
            self.engine.process_turn()
            actual_value = self.player.temporary_effects['data_mimic_turns']
            self.assertEqual(actual_value, expected_value,
                           f"Data mimic should be {expected_value} after turn, got {actual_value}")

    def test_all_temporary_effects_decay_consistently(self):
        """Test that all temporary effects decay at 1 per turn."""
        # Set all effects to initial values
        initial_effects = {
            'data_mimic_turns': 4,
            'speed_boost_turns': 3,
            'movement_slowed_turns': 2,
            'enhanced_vision_turns': 5,
            'exploit_efficiency_turns': 6,
            'virus_turns': 1
        }

        for effect, value in initial_effects.items():
            self.player.temporary_effects[effect] = value

        # Process turn and check all effects decreased by exactly 1
        self.engine.process_turn()

        for effect, initial_value in initial_effects.items():
            expected_value = max(0, initial_value - 1)  # Can't go below 0
            actual_value = self.player.temporary_effects[effect]
            self.assertEqual(actual_value, expected_value,
                           f"{effect} should decay from {initial_value} to {expected_value}, got {actual_value}")

    def test_system_crash_disables_enemies_for_four_turns(self):
        """Test that system crash properly disables enemies for 4 turns."""
        # Create an enemy and disable it with system crash
        from game_characters import Enemy
        enemy = Enemy(Position(10, 10), 'virus')
        enemy.disabled_turns = 4
        self.engine.enemies = [enemy]

        # Enemy should be disabled and not move for 4 turns
        for turn in range(4):
            initial_pos = (enemy.x, enemy.y)
            result = enemy.move(self.engine.game_map, self.player, self.engine)

            # Should return False (didn't move) and disabled_turns should decrease
            self.assertFalse(result, f"Enemy should not move on turn {turn + 1}")
            self.assertEqual((enemy.x, enemy.y), initial_pos, f"Enemy should not change position on turn {turn + 1}")

            expected_disabled = 4 - (turn + 1)
            self.assertEqual(enemy.disabled_turns, expected_disabled,
                           f"disabled_turns should be {expected_disabled} after turn {turn + 1}")

        # On 5th turn, enemy should be able to move again
        enemy.disabled_turns = 0  # Should be 0 after 4 turns
        # Reset position and try to move
        enemy.x, enemy.y = 10, 10
        self.engine.game_map.walls.clear()  # Clear walls for movement
        result = enemy.move(self.engine.game_map, self.player, self.engine)
        # This should succeed (return True) if enemy has valid moves in queue
        # Or False if no valid moves, but disabled_turns should be 0
        self.assertEqual(enemy.disabled_turns, 0, "Enemy should not be disabled after 4 turns")

    def test_temporary_effects_dont_go_negative(self):
        """Test that temporary effects don't go below 0."""
        # Set effects to 1 and process multiple turns
        self.player.temporary_effects['data_mimic_turns'] = 1

        # Process several turns
        for _ in range(5):
            self.engine.process_turn()

        # Effect should be 0, not negative
        self.assertEqual(self.player.temporary_effects['data_mimic_turns'], 0,
                        "Temporary effects should not go below 0")

    def test_virus_effect_applies_damage_then_decrements(self):
        """Test that virus effect applies damage before decrementing counter."""
        # Ensure player is not on a CPU recovery node (which would heal +20 and mask virus damage of -3)
        player_pos = (self.player.x, self.player.y)
        if self.engine.game_map.is_cpu_recovery_node(self.player.position):
            # Move player off the CPU node
            for x in range(15, 30):
                for y in range(15, 30):
                    test_pos = Position(x, y)
                    if (not self.engine.game_map.is_wall(test_pos) and
                        not self.engine.game_map.is_cpu_recovery_node(test_pos)):
                        self.player.x = x
                        self.player.y = y
                        break

        # Set virus effect and track initial CPU
        self.player.temporary_effects['virus_turns'] = 3
        initial_cpu = self.player.cpu

        # Process one turn
        self.engine.process_turn()

        # CPU should have decreased (virus damage applied)
        self.assertLess(self.player.cpu, initial_cpu, "Virus should deal damage (player not on CPU recovery node)")

        # Virus turns should have decremented by 1
        self.assertEqual(self.player.temporary_effects['virus_turns'], 2,
                        "Virus turns should decrement by 1 after damage applied")

    def test_multiple_turn_processing_accumulates_correctly(self):
        """Test that processing multiple turns accumulates effects correctly."""
        # Set multiple effects with different durations
        self.player.temporary_effects['data_mimic_turns'] = 5
        self.player.temporary_effects['speed_boost_turns'] = 3
        self.player.temporary_effects['virus_turns'] = 2

        initial_cpu = self.player.cpu

        # Process 3 turns
        for turn in range(3):
            self.engine.process_turn()

            # Check effects after each turn
            expected_mimic = max(0, 5 - (turn + 1))
            expected_speed = max(0, 3 - (turn + 1))
            expected_virus = max(0, 2 - (turn + 1))

            self.assertEqual(self.player.temporary_effects['data_mimic_turns'], expected_mimic)
            self.assertEqual(self.player.temporary_effects['speed_boost_turns'], expected_speed)
            self.assertEqual(self.player.temporary_effects['virus_turns'], expected_virus)

    def test_no_double_processing_of_effects(self):
        """Test that effects are only processed once per turn through the unified system."""
        # This test ensures the fix for double-decrementing is working
        self.player.temporary_effects['data_mimic_turns'] = 10

        # Manually check that only GameStateManager processes effects, not Player.update_effects
        with patch.object(self.player, 'update_effects') as mock_update:
            self.engine.process_turn()

            # Player.update_effects should NOT be called during turn processing
            # (it was the source of double-decrementing)
            mock_update.assert_not_called()

        # Effect should have decreased by exactly 1
        self.assertEqual(self.player.temporary_effects['data_mimic_turns'], 9,
                        "Effect should decrease by exactly 1, indicating no double processing")


if __name__ == '__main__':
    unittest.main()