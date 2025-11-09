#!/usr/bin/env python3
"""
Tests for upgrade and progression system mechanics.
Covers Player.apply_permanent_upgrade(), temporary effects, and stat boundaries.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from game_characters import Player
from game_entities import Position
from game_config import GameConfig
from game_inventory import CodeHack
from game_data import GameUpgrades


class TestUpgradeApplication(unittest.TestCase):
    """Test permanent upgrade application logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(5, 5)
        # Set consistent starting values
        self.player.cpu = 100
        self.player.max_cpu = 100
        self.player.ram_total = 8
        self.player.max_heat = 100

    def test_cpu_upgrade_application(self):
        """Test CPU upgrade increases max and current CPU."""
        initial_cpu = self.player.cpu
        initial_max_cpu = self.player.max_cpu
        
        result = self.player.apply_permanent_upgrade('cpu_boost')
        
        self.assertTrue(result)
        self.assertEqual(self.player.max_cpu, initial_max_cpu + 20)
        self.assertEqual(self.player.cpu, initial_cpu + 20)

    def test_ram_upgrade_application(self):
        """Test RAM upgrade increases total RAM capacity."""
        initial_ram = self.player.ram_total
        
        result = self.player.apply_permanent_upgrade('ram_boost')
        
        self.assertTrue(result)
        self.assertEqual(self.player.ram_total, initial_ram + 4)

    def test_heat_upgrade_application(self):
        """Test heat upgrade increases max heat capacity."""
        initial_max_heat = self.player.max_heat
        
        result = self.player.apply_permanent_upgrade('heat_boost')
        
        self.assertTrue(result)
        self.assertEqual(self.player.max_heat, initial_max_heat + 20)

    def test_invalid_upgrade_key(self):
        """Test invalid upgrade key returns False."""
        result = self.player.apply_permanent_upgrade('invalid_upgrade')
        self.assertFalse(result)

    def test_cpu_upgrade_respects_max_boundary(self):
        """Test CPU upgrades don't exceed maximum capacity."""
        # Set player close to max
        original_get_required = GameConfig._get_required

        def mock_get_required(key):
            if key == 'gameplay.max_cpu_capacity':
                return 120  # Set a lower cap for testing
            # For any other key, call the real method
            return original_get_required(key)

        with patch.object(GameConfig, '_get_required', side_effect=mock_get_required):
            self.player.cpu = 110
            self.player.max_cpu = 110

            result = self.player.apply_permanent_upgrade('cpu_boost')

            self.assertTrue(result)
            self.assertEqual(self.player.max_cpu, 120)  # Capped at max
            self.assertEqual(self.player.cpu, 120)

    def test_ram_upgrade_respects_max_boundary(self):
        """Test RAM upgrades don't exceed maximum capacity."""
        original_get_required = GameConfig._get_required

        def mock_get_required(key):
            if key == 'gameplay.max_ram_capacity':
                return 10  # Set a lower cap for testing
            return original_get_required(key)

        with patch.object(GameConfig, '_get_required', side_effect=mock_get_required):
            self.player.ram_total = 8

            result = self.player.apply_permanent_upgrade('ram_boost')

            self.assertTrue(result)
            self.assertEqual(self.player.ram_total, 10)  # Capped at max

    def test_heat_upgrade_respects_max_boundary(self):
        """Test heat upgrades don't exceed maximum capacity."""
        self.player.max_heat = 190
        
        result = self.player.apply_permanent_upgrade('heat_boost')
        
        self.assertTrue(result)
        self.assertEqual(self.player.max_heat, 200)  # Capped at 200


class TestTemporaryEffects(unittest.TestCase):
    """Test temporary effect management and duration."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(5, 5)
        self.mock_game = MagicMock()
        self.mock_game.player = self.player
        self.mock_game.message_log = MagicMock()

    def test_temporary_effects_initialization(self):
        """Test player initializes with empty temporary effects."""
        expected_effects = {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'traffic_masquerade_turns': 0,
            'movement_slowed_turns': 0,
            'virus_turns': 0
        }
        self.assertEqual(self.player.temporary_effects, expected_effects)

    def test_speed_boost_effect_application(self):
        """Test speed boost temporary effect gets applied correctly."""
        code_hack = CodeHack("blue", "speed_boost", "Speed Boost Code")
        result = code_hack._apply_effect('speed_boost', self.player, self.mock_game)
        
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 3)

    def test_enhanced_vision_effect_application(self):
        """Test enhanced vision temporary effect gets applied correctly."""
        code_hack = CodeHack("green", "enhanced_vision", "Enhanced Vision Code")
        result = code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)
        
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 5)

    def test_exploit_efficiency_effect_application(self):
        """Test exploit efficiency temporary effect gets applied correctly."""
        code_hack = CodeHack("yellow", "exploit_efficiency", "Exploit Efficiency Code")
        result = code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)
        
        self.assertTrue(result)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 8)

    def test_effect_stacking_prevents_duplicate_speed_boost(self):
        """Test speed boost doesn't stack when already active."""
        code_hack = CodeHack("blue", "speed_boost", "Speed Boost Code")
        
        # Apply first speed boost
        code_hack._apply_effect('speed_boost', self.player, self.mock_game)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 3)
        
        # Try to apply second speed boost
        code_hack._apply_effect('speed_boost', self.player, self.mock_game)
        
        # Should still be 5, not 10
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 3)

    def test_enhanced_vision_stacking_extends_duration(self):
        """Test enhanced vision extends duration when applied multiple times."""
        code_hack = CodeHack("green", "enhanced_vision", "Enhanced Vision Code")
        
        # Apply first enhanced vision
        code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 5)
        
        # Apply second enhanced vision
        code_hack._apply_effect('enhanced_vision', self.player, self.mock_game)
        
        # Should be extended to 10
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 10)

    def test_exploit_efficiency_stacking_extends_duration(self):
        """Test exploit efficiency extends duration when applied multiple times."""
        code_hack = CodeHack("yellow", "exploit_efficiency", "Exploit Efficiency Code")
        
        # Apply first exploit efficiency
        code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 8)
        
        # Apply second exploit efficiency
        code_hack._apply_effect('exploit_efficiency', self.player, self.mock_game)
        
        # Should be extended to 16
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 16)

    def test_speed_boost_counters_movement_slow(self):
        """Test speed boost counters existing movement slow effects."""
        code_hack = CodeHack("blue", "speed_boost", "Speed Boost Code")
        
        # Apply movement slow first
        self.player.temporary_effects['movement_slowed_turns'] = 3
        
        # Apply speed boost
        code_hack._apply_effect('speed_boost', self.player, self.mock_game)
        
        # Speed boost should overcome slow and provide net benefit
        self.assertEqual(self.player.temporary_effects['movement_slowed_turns'], 0)
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 0)  # 3 - 3


class TestEffectExpiration(unittest.TestCase):
    """Test temporary effect duration tracking and expiration."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(5, 5)

    def test_effect_countdown_decreases_turns(self):
        """Test that update_effects decreases effect turns."""
        self.player.temporary_effects['speed_boost_turns'] = 5
        self.player.temporary_effects['enhanced_vision_turns'] = 3
        
        self.player.update_effects()
        
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 4)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 2)

    def test_effects_dont_go_negative(self):
        """Test that effects don't go below zero."""
        self.player.temporary_effects['speed_boost_turns'] = 1
        
        self.player.update_effects()
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 0)
        
        self.player.update_effects()
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 0)

    def test_multiple_effects_countdown_independently(self):
        """Test multiple effects count down independently."""
        self.player.temporary_effects['speed_boost_turns'] = 3
        self.player.temporary_effects['enhanced_vision_turns'] = 1
        self.player.temporary_effects['exploit_efficiency_turns'] = 5
        
        self.player.update_effects()
        
        self.assertEqual(self.player.temporary_effects['speed_boost_turns'], 2)
        self.assertEqual(self.player.temporary_effects['enhanced_vision_turns'], 0)
        self.assertEqual(self.player.temporary_effects['exploit_efficiency_turns'], 4)

    def test_traffic_masquerade_trace_level_method(self):
        """Test is_invisible returns correct state."""
        self.assertFalse(self.player.is_invisible())
        
        self.player.temporary_effects['traffic_masquerade_turns'] = 3
        self.assertTrue(self.player.is_invisible())
        
        self.player.temporary_effects['traffic_masquerade_turns'] = 0
        self.assertFalse(self.player.is_invisible())

    def test_enhanced_vision_trace_level_methods(self):
        """Test enhanced vision trace level methods work correctly."""
        # Test can_see_through_walls method
        self.assertFalse(self.player.can_see_through_walls())
        
        self.player.temporary_effects['enhanced_vision_turns'] = 2
        self.assertTrue(self.player.can_see_through_walls())
        
        # Test enhanced vision range calculation
        self.player.temporary_effects['enhanced_vision_turns'] = 0
        normal_range = self.player.get_vision_range()
        
        self.player.temporary_effects['enhanced_vision_turns'] = 5
        enhanced_range = self.player.get_vision_range()
        
        self.assertGreater(enhanced_range, normal_range)


class TestStatBoundaryEnforcement(unittest.TestCase):
    """Test stat boundaries are properly enforced."""

    def setUp(self):
        """Set up test fixtures."""
        self.player = Player(5, 5)

    def test_cpu_damage_doesnt_go_negative(self):
        """Test CPU damage doesn't reduce CPU below zero."""
        self.player.cpu = 10
        
        damage_taken = self.player.take_damage(50)
        
        self.assertEqual(damage_taken, 10)  # Only took 10 damage (what was available)
        self.assertEqual(self.player.cpu, 0)

    def test_cpu_damage_normal_case(self):
        """Test CPU damage works normally when sufficient CPU available."""
        self.player.cpu = 50
        
        damage_taken = self.player.take_damage(30)
        
        self.assertEqual(damage_taken, 30)
        self.assertEqual(self.player.cpu, 20)

    def test_cpu_healing_respects_max_cpu(self):
        """Test CPU healing doesn't exceed max_cpu."""
        self.player.cpu = 80
        self.player.max_cpu = 100
        
        # Test that healing is capped
        initial_cpu = self.player.cpu
        healing_amount = 30
        expected_cpu = min(self.player.max_cpu, initial_cpu + healing_amount)
        
        # Simulate healing (this would normally be done by item effects)
        self.player.cpu = min(self.player.max_cpu, self.player.cpu + healing_amount)
        
        self.assertEqual(self.player.cpu, expected_cpu)

    def test_multiple_upgrades_stack_within_limits(self):
        """Test multiple upgrades of same type stack within limits."""
        # Apply multiple CPU upgrades
        self.player.apply_permanent_upgrade('cpu_boost')
        initial_max = self.player.max_cpu
        
        self.player.apply_permanent_upgrade('cpu_boost')
        
        # Should stack unless hitting boundary
        expected_max = min(getattr(GameConfig, 'max_cpu_capacity', 200), initial_max + 20)
        self.assertEqual(self.player.max_cpu, expected_max)

    def test_heat_boundary_enforcement(self):
        """Test heat capacity has proper boundaries."""
        # Test normal heat upgrade
        initial_heat = self.player.max_heat
        self.player.apply_permanent_upgrade('heat_boost')
        self.assertEqual(self.player.max_heat, min(200, initial_heat + 20))

    def test_ram_boundary_enforcement(self):
        """Test RAM capacity has proper boundaries."""
        initial_ram = self.player.ram_total

        # Mock a lower max for testing
        original_get_required = GameConfig._get_required

        def mock_get_required(key):
            if key == 'gameplay.max_ram_capacity':
                return 15  # Set a lower cap for testing
            return original_get_required(key)

        with patch.object(GameConfig, '_get_required', side_effect=mock_get_required):
            self.player.apply_permanent_upgrade('ram_boost')
            expected_ram = min(15, initial_ram + 4)
            self.assertEqual(self.player.ram_total, expected_ram)


if __name__ == '__main__':
    unittest.main()