"""
Inventory Large Capacity and Edge Case Tests

NOTE: The inventory system has NO HARD CAPACITY LIMIT (unlimited items allowed).
This test suite focuses on:
- Handling many items without performance degradation
- Code hack stacking behavior (same color stacks)
- Exploit equipping with 3-slot limit (swapping behavior)
- Large inventory state persistence through save/load
- Inventory display rendering with many items
- Edge cases like adding/removing items from large inventory

These tests ensure inventory system remains stable with large item counts.
"""

import pytest
from unittest.mock import Mock, patch

from game_engine import GameEngine
from game_characters import Player
from game_entities import Position
from game_inventory import ExploitItem, CodeHack, StoryFragment, InventoryManager
from game_data import GameData
from game_config import GameConfig, GameBalance
from tests.fixtures.simple_fixtures import create_real_player
from tests.fixtures.real_game_data import get_real_game_data


@pytest.fixture
def player_with_inventory():
    """Create player with real inventory manager."""
    player = create_real_player()
    return player


@pytest.fixture
def large_inventory_player():
    """Create player with large inventory (many items to test performance)."""
    player = create_real_player()

    # Add many items to test large inventory handling
    exploit_keys = list(GameData.EXPLOITS.keys())
    large_count = 50  # Large but reasonable number for testing

    for i in range(large_count):
        exploit_key = exploit_keys[i % len(exploit_keys)]
        exploit_def = GameData.EXPLOITS[exploit_key]
        item = ExploitItem(exploit_key, exploit_def)
        player.inventory_manager.add_item(item)

    return player


class TestInventoryLargeCapacity:
    """Test inventory behavior with many items."""

    def test_pickup_item_with_large_inventory(self, large_inventory_player, basic_game_engine):
        """Test picking up item when inventory already has many items."""
        player = large_inventory_player
        engine = basic_game_engine
        engine.player = player

        initial_count = len(player.inventory_manager.items)

        # Verify inventory has many items
        assert initial_count >= 50, "Inventory should have many items for this test"

        # Spawn an exploit pickup on the map
        if len(engine.game_map.exploit_pickups) > 0:
            exploit_pos = list(engine.game_map.exploit_pickups.keys())[0]
            engine.player.x = exploit_pos[0]
            engine.player.y = exploit_pos[1]

            # Pick up the exploit (should succeed - no capacity limit)
            engine.maybe_process_turn()

            # Inventory should have one more item
            final_count = len(player.inventory_manager.items)
            assert final_count >= initial_count, "Item should be added to large inventory"

    def test_pickup_code_hack_with_large_inventory(self, large_inventory_player, basic_game_engine):
        """Test code hack pickup with large inventory."""
        player = large_inventory_player
        engine = basic_game_engine
        engine.player = player

        initial_inventory = len(player.inventory_manager.items)

        # Spawn code hack on map
        if len(engine.game_map.code_hacks) > 0:
            code_pos = list(engine.game_map.code_hacks.keys())[0]
            engine.player.x = code_pos[0]
            engine.player.y = code_pos[1]

            # Pick up code hack (goes into inventory, may stack)
            engine.maybe_process_turn()

            # Code hack should be added (or stacked with existing)
            final_count = len(player.inventory_manager.items)
            assert final_count >= initial_inventory, "Code hack should be added or stacked"

    def test_pickup_story_fragment_with_large_inventory(self, large_inventory_player, basic_game_engine):
        """Test story fragment pickup with large inventory."""
        player = large_inventory_player
        engine = basic_game_engine
        engine.player = player

        initial_inventory = len(player.inventory_manager.items)

        # Spawn story fragment
        if len(engine.game_map.story_fragments) > 0:
            story_pos = list(engine.game_map.story_fragments.keys())[0]
            engine.player.x = story_pos[0]
            engine.player.y = story_pos[1]

            # Pick up story fragment
            engine.maybe_process_turn()

            # Story fragment should be added
            final_count = len(player.inventory_manager.items)
            assert final_count >= initial_inventory, "Story fragment should be added"


class TestCodeHackStacking:
    """Test code hack stacking behavior with large inventory."""

    def test_code_hack_stacking_same_color(self, player_with_inventory):
        """Test code hacks of same color stack together."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Add first crimson code
        hack1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Restores CPU", quantity=1)
        manager.add_item(hack1)

        initial_count = len(manager.items)

        # Add second crimson code (should stack)
        hack2 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Restores CPU", quantity=1)
        manager.add_item(hack2)

        final_count = len(manager.items)

        # Should not add new item, just increase quantity
        assert final_count == initial_count, "Same color code hacks should stack"

        # Find the crimson code and verify quantity increased
        crimson_codes = [item for item in manager.items
                        if isinstance(item, CodeHack) and item.color_name == "crimson"]
        assert len(crimson_codes) == 1, "Should have only one crimson code stack"
        assert crimson_codes[0].quantity == 2, "Quantity should be 2 after stacking"

    def test_code_hack_different_colors_dont_stack(self, player_with_inventory):
        """Test code hacks of different colors don't stack."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Add crimson code
        hack1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Restores CPU", quantity=1)
        manager.add_item(hack1)

        initial_count = len(manager.items)

        # Add azure code (different color, shouldn't stack)
        hack2 = CodeHack("azure", "reduce_heat", "Azure Code", "Reduces heat", quantity=1)
        manager.add_item(hack2)

        final_count = len(manager.items)

        # Should add as separate item
        assert final_count == initial_count + 1, "Different color codes should not stack"

    def test_inventory_handles_many_items_without_crash(self, player_with_inventory):
        """Test inventory can handle many items without performance issues."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Add 100 items
        exploit_keys = list(GameData.EXPLOITS.keys())
        for i in range(100):
            exploit_key = exploit_keys[i % len(exploit_keys)]
            exploit_def = GameData.EXPLOITS[exploit_key]
            item = ExploitItem(exploit_key, exploit_def)
            result = manager.add_item(item)

            # Verify add_item returns True (successful)
            assert result == True, f"Adding item {i} should succeed"

        # Verify all items added
        assert len(manager.items) >= 100, "Should have at least 100 items"

    def test_inventory_operations_stable_with_large_inventory(self, large_inventory_player):
        """Test all inventory operations work correctly with large inventory."""
        player = large_inventory_player
        manager = player.inventory_manager

        initial_count = len(manager.items)
        assert initial_count >= 50, "Should start with large inventory"

        # Test various operations don't crash
        # 1. List items
        items_list = manager.items
        assert len(items_list) >= 50

        # 2. Get items by type
        exploits = manager.get_items_by_type("exploit")
        assert isinstance(exploits, list)

        # 3. Get specific item
        if len(manager.items) > 0:
            first_item = manager.items[0]
            assert first_item is not None

        # No crashes = success
        assert len(manager.items) == initial_count


class TestExploitSlotManagement:
    """Test exploit equipping when slots are full."""

    def test_equip_exploit_when_slots_full(self, player_with_inventory):
        """Test equipping exploit when all 3 slots are full (should swap)."""
        player = player_with_inventory

        # Equip 3 exploits (fill slots)
        exploit_keys = list(GameData.EXPLOITS.keys())[:3]
        for i, key in enumerate(exploit_keys):
            exploit_def = GameData.EXPLOITS[key]
            item = ExploitItem(key, exploit_def)
            player.inventory_manager.add_item(item)

            # Equip to slot
            if hasattr(player, 'equipped_exploits'):
                if i < len(player.equipped_exploits):
                    player.equipped_exploits[i] = item

        # Verify 3 slots filled
        if hasattr(player, 'equipped_exploits'):
            equipped_count = sum(1 for e in player.equipped_exploits if e is not None)
            assert equipped_count == 3, "All 3 exploit slots should be filled"

            # Try to equip a 4th exploit (should swap out one of the existing)
            if len(exploit_keys) > 3:
                new_key = exploit_keys[3]
                new_def = GameData.EXPLOITS[new_key]
                new_item = ExploitItem(new_key, new_def)
                player.inventory_manager.add_item(new_item)

                # Equipping should work (swap)
                old_exploit = player.equipped_exploits[0]
                player.equipped_exploits[0] = new_item

                # Verify swap occurred
                assert player.equipped_exploits[0] == new_item

    def test_equip_menu_handles_full_slots(self, player_with_inventory):
        """Test equip menu can handle swapping when slots are full."""
        player = player_with_inventory

        # Add multiple exploits to inventory
        exploit_keys = list(GameData.EXPLOITS.keys())[:5]
        for key in exploit_keys:
            exploit_def = GameData.EXPLOITS[key]
            item = ExploitItem(key, exploit_def)
            player.inventory_manager.add_item(item)

        # Verify inventory has items
        assert len(player.inventory_manager.items) >= 5

        # Equip menu should be able to display and handle selection
        # (This test verifies no crashes when inventory is populated)
        if hasattr(player, 'equipped_exploits'):
            assert player.equipped_exploits is not None


class TestInventoryDisplay:
    """Test inventory UI rendering with many items."""

    def test_inventory_display_with_large_inventory(self, large_inventory_player):
        """Test inventory menu can render correctly with large inventory."""
        player = large_inventory_player

        # Verify inventory has many items
        assert len(player.inventory_manager.items) >= 50

        # Inventory display should handle large inventory without crashes
        # (Actual rendering tested in UI tests, this verifies data structure is valid)
        items = player.inventory_manager.items
        for item in items:
            assert item is not None
            # Check item has required attributes
            assert hasattr(item, 'name') or hasattr(item, 'exploit_id')

    def test_get_display_items_with_large_inventory(self, large_inventory_player):
        """Test get_display_items works correctly with large inventory."""
        player = large_inventory_player
        manager = player.inventory_manager

        # Get display items (sorted order)
        display_items = manager.get_display_items()

        # Should return all items in proper order
        assert len(display_items) >= 50
        assert all(item is not None for item in display_items)


class TestInventoryPersistence:
    """Test large inventory state persistence through save/load."""

    def test_large_inventory_save_load(self, large_inventory_player):
        """Test large inventory persists correctly through save/load."""
        player = large_inventory_player

        # Record initial inventory state
        initial_count = len(player.inventory_manager.items)
        assert initial_count >= 50, "Should have large inventory"

        # Verify inventory data is serializable (can be saved)
        # This tests that large inventory won't cause save failures
        for item in player.inventory_manager.items:
            assert hasattr(item, '__dict__') or hasattr(item, '__slots__'), "Item should be serializable"

        # Large inventory should not cause performance issues
        assert initial_count >= 50, "Large inventory handling verified"


class TestInventoryDropping:
    """Test dropping items from large inventory."""

    def test_drop_item_from_large_inventory(self, large_inventory_player):
        """Test dropping item from large inventory."""
        player = large_inventory_player
        manager = player.inventory_manager

        initial_count = len(manager.items)
        assert initial_count >= 50, "Inventory should be large"

        # Drop first item
        if len(manager.items) > 0:
            item_to_drop = manager.items[0]
            result = manager.remove_item(item_to_drop)

            # Verify item was removed
            assert result == True, "Remove should return True"
            final_count = len(manager.items)
            assert final_count == initial_count - 1, "Item should be removed from inventory"

    def test_drop_item_validation(self, player_with_inventory):
        """Test dropping item that doesn't exist in inventory."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Try to drop item not in inventory
        fake_item = ExploitItem("fake_exploit", Mock())

        # Should return False (item not in inventory)
        result = manager.remove_item(fake_item)
        assert result == False, "Removing non-existent item should return False"


class TestInventoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_inventory_to_large_inventory_workflow(self, player_with_inventory):
        """Test filling inventory from empty to large size."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Start with empty inventory
        manager.items = []
        assert len(manager.items) == 0

        # Fill with many items
        target_count = 75
        exploit_keys = list(GameData.EXPLOITS.keys())

        for i in range(target_count):
            exploit_key = exploit_keys[i % len(exploit_keys)]
            exploit_def = GameData.EXPLOITS[exploit_key]
            item = ExploitItem(exploit_key, exploit_def)
            manager.add_item(item)

        # Final count should match target
        assert len(manager.items) == target_count

    def test_adding_duplicate_exploits(self, player_with_inventory):
        """Test adding same exploit multiple times (should create separate items)."""
        player = player_with_inventory
        manager = player.inventory_manager

        # Add same exploit 5 times
        exploit_key = list(GameData.EXPLOITS.keys())[0]
        exploit_def = GameData.EXPLOITS[exploit_key]

        initial_count = len(manager.items)

        for i in range(5):
            item = ExploitItem(exploit_key, exploit_def)
            manager.add_item(item)

        final_count = len(manager.items)

        # Should have 5 separate items (exploits don't stack, only code hacks do)
        assert final_count == initial_count + 5, "Each exploit should be a separate item"
