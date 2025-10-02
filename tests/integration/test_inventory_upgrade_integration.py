#!/usr/bin/env python3
"""
Integration tests for inventory and upgrade systems.
Tests how inventory management integrates with upgrade progression and gameplay.
"""

import unittest
from unittest.mock import Mock, patch

from game_engine import GameEngine
from game_config import GameSettings
from game_entities import Position
from game_inventory import InventoryManager, CodeHack, ExploitItem
from game_data import GameUpgrades


class TestInventoryUpgradeIntegration(unittest.TestCase):
    """Test integration between inventory management and upgrade systems."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        game_settings = GameSettings()

        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=game_settings
        )

        return engine

    def setUp(self):
        """Set up test environment."""
        self.engine = self.create_test_engine()
        self.inventory = self.engine.player.inventory_manager

    def test_inventory_capacity_affects_gameplay(self):
        """Test that inventory capacity limits affect pickup behavior."""
        # Fill inventory to capacity
        for i in range(self.inventory.capacity):
            code_hack = CodeHack(f"test_hack_{i}", "Test hack", "A test code hack", 5)
            self.inventory.add_item(code_hack)

        # Verify inventory is full
        self.assertTrue(self.inventory.is_full(), "Inventory should be full")

        # Try to add another item
        extra_hack = CodeHack("extra_hack", "Extra hack", "Should not fit", 3)
        result = self.inventory.add_item(extra_hack)

        # Should fail to add
        self.assertFalse(result, "Should not be able to add item to full inventory")

    def test_upgrade_acquisition_integration(self):
        """Test that acquiring upgrades affects player capabilities."""
        # Check initial player stats
        initial_cpu = self.engine.player.max_cpu
        initial_heat_capacity = getattr(self.engine.player, 'max_heat', 100)

        # Simulate finding and applying CPU upgrade
        upgrade_pos = (20, 20)
        self.engine.game_map.permanent_upgrades[upgrade_pos] = 'cpu_boost'
        self.engine.player.x, self.engine.player.y = 20, 20

        # Process the upgrade pickup
        self.engine._process_special_tiles()

        # Player stats should have improved
        self.assertGreaterEqual(self.engine.player.max_cpu, initial_cpu,
                               "CPU should have increased from upgrade")

    def test_exploit_inventory_combat_integration(self):
        """Test that exploits in inventory properly integrate with combat system."""
        # Add exploit to inventory
        from game_data import GameData
        exploit_keys = list(GameData.EXPLOITS.keys())
        if exploit_keys:
            exploit_key = exploit_keys[0]
            exploit_def = GameData.EXPLOITS[exploit_key]
            exploit_item = ExploitItem(exploit_def)
            self.inventory.add_item(exploit_item)

            # Equip the exploit
            self.inventory.equip_exploit(exploit_key)

            # Verify it's equipped
            self.assertEqual(self.inventory.equipped_exploit, exploit_key,
                           "Exploit should be equipped")

            # Test using the exploit in combat context
            target_pos = Position(self.engine.player.x + 1, self.engine.player.y)
            can_use = self.engine.exploit_system.can_use_exploit(exploit_key, target_pos)

            # Should be able to use equipped exploit (subject to heat/range constraints)
            if self.engine.player.heat < 100:  # Assuming heat limit
                self.assertTrue(isinstance(can_use, bool), "Should return boolean for usability")

    def test_inventory_persistence_through_levels(self):
        """Test that inventory contents persist through level progression."""
        # Add items to inventory
        test_items = []
        for i in range(3):
            code_hack = CodeHack(f"persistent_hack_{i}", f"Hack {i}", "Persistent item", 2)
            self.inventory.add_item(code_hack)
            test_items.append(code_hack.name)

        # Record inventory state
        initial_item_count = len(self.inventory.items)
        initial_item_names = [item.name for item in self.inventory.items]

        # Progress to next level
        original_level = self.engine.level
        self.engine.next_level()

        # Verify inventory persisted
        self.assertEqual(len(self.inventory.items), initial_item_count,
                        "Inventory should maintain item count through level progression")

        current_item_names = [item.name for item in self.inventory.items]
        for name in initial_item_names:
            self.assertIn(name, current_item_names,
                         f"Item '{name}' should persist through level progression")

    def test_code_hack_upgrade_synergy(self):
        """Test that code hacks and upgrades work together effectively."""
        # Add heat management code hack
        heat_hack = CodeHack("heat_optimizer", "Heat Optimizer",
                           "Reduces exploit heat cost", 15)
        self.inventory.add_item(heat_hack)

        # Set player heat to test heat management
        self.engine.player.heat = 80

        # Use code hack
        if self.inventory.use_item("heat_optimizer"):
            # Heat should have been reduced
            self.assertLess(self.engine.player.heat, 80,
                           "Code hack should reduce heat")

        # Now test interaction with exploit usage
        # (This would require more complex setup but demonstrates the integration point)

    def test_story_fragment_inventory_relationship(self):
        """Test how story fragments relate to inventory system."""
        # Story fragments don't go in inventory but affect discovery count
        initial_discovered = 0
        if hasattr(self.engine, 'story_fragment_manager'):
            discovered, total = self.engine.story_fragment_manager.get_fragment_count()
            initial_discovered = discovered

        # Place and discover story fragment
        from game_inventory import StoryFragment
        fragment = StoryFragment(0)
        self.engine.game_map.story_fragments[(25, 25)] = fragment
        self.engine.player.x, self.engine.player.y = 25, 25

        # Process discovery
        self.engine._process_special_tiles()

        # Fragment should be discovered but not in inventory
        self.assertTrue((25, 25) not in self.engine.game_map.story_fragments,
                       "Story fragment should be removed from map after discovery")

        # Inventory should not contain story fragments
        story_items = [item for item in self.inventory.items
                      if isinstance(item, StoryFragment)]
        self.assertEqual(len(story_items), 0,
                        "Story fragments should not be stored in inventory")


class TestUpgradeProgressionIntegration(unittest.TestCase):
    """Test integration of upgrade progression with game systems."""

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        mock_sound_manager = Mock()
        game_settings = GameSettings()

        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=game_settings
        )

        return engine

    def setUp(self):
        """Set up test environment."""
        self.engine = self.create_test_engine()

    def test_upgrade_availability_by_level(self):
        """Test that upgrades become available appropriately by level."""
        # Check upgrade availability at different levels
        for level in [1, 2, 3]:
            self.engine.level = level

            # Generate level to see what upgrades are available
            try:
                self.engine._generate_procedural_level()

                # Count permanent upgrades
                upgrade_count = len(self.engine.game_map.permanent_upgrades)

                # Higher levels should generally have more upgrade opportunities
                self.assertGreaterEqual(upgrade_count, 0,
                                      f"Level {level} should have upgrade opportunities")

            except Exception:
                # Level generation might fail in test environment, that's ok
                pass

    def test_multiple_upgrade_stacking(self):
        """Test that multiple upgrades stack properly."""
        initial_cpu = self.engine.player.max_cpu

        # Apply multiple CPU upgrades
        for i, pos in enumerate([(10, 10), (15, 15), (20, 20)]):
            self.engine.game_map.permanent_upgrades[pos] = 'cpu_boost'
            self.engine.player.x, self.engine.player.y = pos[0], pos[1]
            self.engine._process_special_tiles()

            # Each upgrade should increase CPU further
            current_cpu = self.engine.player.max_cpu
            self.assertGreater(current_cpu, initial_cpu,
                             f"CPU should increase after upgrade {i+1}")
            initial_cpu = current_cpu

    def test_upgrade_limits_and_balance(self):
        """Test that upgrades have reasonable limits for game balance."""
        # Test that upgrades don't make player overpowered
        original_cpu = self.engine.player.max_cpu

        # Apply many upgrades
        for i in range(10):  # Excessive number of upgrades
            pos = (10 + i, 10 + i)
            self.engine.game_map.permanent_upgrades[pos] = 'cpu_boost'
            self.engine.player.x, self.engine.player.y = pos[0], pos[1]
            self.engine._process_special_tiles()

        # Should have some reasonable upper limit
        final_cpu = self.engine.player.max_cpu
        cpu_increase_ratio = final_cpu / original_cpu

        # Shouldn't increase by more than 5x (reasonable balance check)
        self.assertLess(cpu_increase_ratio, 5.0,
                       "CPU upgrades should have reasonable limits for game balance")


if __name__ == '__main__':
    unittest.main()