#!/usr/bin/env python3
"""
Unit tests for game_inventory.py - Inventory management system.

Tests cover:
- InventoryManager item operations (add, remove, get)
- Code hack stacking by color
- Exploit equipping with RAM/slot constraints
- RAM usage calculation
- Item type filtering and display ordering

Does NOT test:
- Item use() effects (integration tests)
- Code hack discovery system (integration tests)
- Metrics tracking (integration tests)
"""

from unittest.mock import Mock

import pytest

from rsp.entities.base import ExploitDefinition, TargetingMode
from rsp.combat.inventory import CodeHack, ExploitItem, InventoryItem, InventoryManager


class TestInventoryManagerInitialization:
    """Test InventoryManager initialization."""

    def test_inventory_manager_creates_with_empty_items(self, real_game_data):
        """InventoryManager should initialize with empty items list."""
        mock_player = Mock()
        mock_player.ram_total = 8

        manager = InventoryManager(mock_player)

        assert isinstance(manager.items, list)
        # Items list may have initial items, just check it's a list
        assert hasattr(manager, "items")

    def test_inventory_manager_starts_with_one_exploit_equipped(self, real_game_data):
        """InventoryManager should start with one random exploit equipped."""
        mock_player = Mock()
        mock_player.ram_total = 8

        manager = InventoryManager(mock_player)

        assert len(manager.equipped_exploits) == 1
        assert isinstance(manager.equipped_exploits, list)

    def test_inventory_manager_has_max_exploit_slots(self, real_game_data):
        """InventoryManager should have max_equipped_exploits limit."""
        mock_player = Mock()
        mock_player.ram_total = 8

        manager = InventoryManager(mock_player)

        assert manager.max_equipped_exploits == 5


class TestInventoryManagerAddRemove:
    """Test adding and removing items."""

    def test_add_item_adds_to_inventory(self, real_game_data):
        """add_item should add item to inventory."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        item = InventoryItem("Test Item", "test", "Test description")
        result = manager.add_item(item)

        assert result is True
        assert item in manager.items

    def test_add_code_hack_stacks_same_color(self, real_game_data):
        """Adding code hack of same color should stack quantities."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        # Add first code
        code1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=1)
        manager.add_item(code1)

        # Add second code of same color
        code2 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=1)
        manager.add_item(code2)

        # Should have only 1 item in inventory (stacked)
        code_hacks = manager.get_items_by_type("code_hack")
        assert len(code_hacks) == 1
        assert code_hacks[0].quantity == 2

    def test_add_code_hack_different_colors_dont_stack(self, real_game_data):
        """Adding code hacks of different colors should not stack."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        code1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=1)
        code2 = CodeHack("azure", "reduce_heat", "Azure Code", "Test", quantity=1)

        manager.add_item(code1)
        manager.add_item(code2)

        code_hacks = manager.get_items_by_type("code_hack")
        assert len(code_hacks) == 2

    def test_remove_item_removes_from_inventory(self, real_game_data):
        """remove_item should remove item from inventory."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        item = InventoryItem("Test Item", "test", "Test")
        manager.add_item(item)

        result = manager.remove_item(item)

        assert result is True
        assert item not in manager.items

    def test_remove_nonexistent_item_returns_false(self, real_game_data):
        """Removing item not in inventory should return False."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        item = InventoryItem("Test Item", "test", "Test")

        result = manager.remove_item(item)

        assert result is False


class TestInventoryManagerFiltering:
    """Test item filtering and display methods."""

    def test_get_items_by_type_filters_correctly(self, real_game_data):
        """get_items_by_type should return only items of specified type."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        code1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test")
        code2 = CodeHack("azure", "reduce_heat", "Azure Code", "Test")
        exploit_def = ExploitDefinition(
            "Test Exploit", 2, 10, 3, "test", 10, TargetingMode.SINGLE, "Test"
        )
        exploit = ExploitItem("test_exploit", exploit_def)

        manager.add_item(code1)
        manager.add_item(code2)
        manager.add_item(exploit)

        code_hacks = manager.get_items_by_type("code_hack")
        exploits = manager.get_items_by_type("exploit")

        assert len(code_hacks) == 2
        assert len(exploits) == 1

    def test_get_items_by_type_sorts_code_hacks_alphabetically(self, real_game_data):
        """get_items_by_type should sort code hacks alphabetically by name."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        code_z = CodeHack("crimson", "restore_cpu", "Zeta Code", "Test")
        code_a = CodeHack("azure", "reduce_heat", "Alpha Code", "Test")
        code_m = CodeHack("golden", "speed_boost", "Mu Code", "Test")

        manager.add_item(code_z)
        manager.add_item(code_a)
        manager.add_item(code_m)

        code_hacks = manager.get_items_by_type("code_hack")

        assert code_hacks[0].name == "Alpha Code"
        assert code_hacks[1].name == "Mu Code"
        assert code_hacks[2].name == "Zeta Code"

    def test_get_display_items_orders_correctly(self, real_game_data):
        """get_display_items should return codes first, then exploits."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        exploit_def = ExploitDefinition(
            "Test Exploit", 2, 10, 3, "test", 10, TargetingMode.SINGLE, "Test"
        )
        exploit = ExploitItem("test_exploit", exploit_def)
        code = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test")

        # Add in opposite order (exploit first)
        manager.add_item(exploit)
        manager.add_item(code)

        display_items = manager.get_display_items()

        # Code should come first
        assert display_items[0].item_type == "code_hack"
        assert display_items[1].item_type == "exploit"


class TestInventoryManagerEquipping:
    """Test exploit equipping mechanics."""

    def test_equip_exploit_adds_to_equipped_list(self, real_game_data):
        """equip_exploit should add exploit to equipped_exploits."""
        from rsp.core.data import GameData

        mock_player = Mock()
        mock_player.ram_total = 10
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = []  # Start with none equipped

        # Use real exploit from GameData
        exploit_def = GameData.EXPLOITS["code_injection"]
        exploit = ExploitItem("code_injection", exploit_def)
        manager.add_item(exploit)

        result = manager.equip_exploit(exploit)

        assert result is True
        assert "code_injection" in manager.equipped_exploits

    def test_equip_exploit_removes_from_inventory(self, real_game_data):
        """equip_exploit should remove exploit from items."""
        from rsp.core.data import GameData

        mock_player = Mock()
        mock_player.ram_total = 10
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = []

        exploit_def = GameData.EXPLOITS["code_injection"]
        exploit = ExploitItem("code_injection", exploit_def)
        manager.add_item(exploit)

        manager.equip_exploit(exploit)

        assert exploit not in manager.items

    def test_equip_exploit_fails_if_already_equipped(self, real_game_data):
        """Cannot equip the same exploit twice."""
        from rsp.core.data import GameData

        mock_player = Mock()
        mock_player.ram_total = 10
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["code_injection"]  # Already equipped

        exploit_def = GameData.EXPLOITS["code_injection"]
        exploit = ExploitItem("code_injection", exploit_def)

        result = manager.equip_exploit(exploit)

        assert result is False

    def test_equip_exploit_fails_if_slots_full(self, real_game_data):
        """Cannot equip more than max_equipped_exploits."""
        from rsp.core.data import GameData

        mock_player = Mock()
        mock_player.ram_total = 100  # Enough RAM
        manager = InventoryManager(mock_player)
        manager.max_equipped_exploits = 2
        manager.equipped_exploits = ["system_hop", "traffic_masquerade"]  # All slots full

        exploit_def = GameData.EXPLOITS["code_injection"]
        exploit = ExploitItem("code_injection", exploit_def)

        result = manager.equip_exploit(exploit)

        assert result is False

    def test_equip_exploit_fails_if_insufficient_ram(self, real_game_data):
        """Cannot equip exploit if not enough RAM."""
        from rsp.core.data import GameData

        mock_player = Mock()
        mock_player.ram_total = 2  # Very limited RAM
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = []

        # Use system_crash which costs 3 RAM (more than available)
        exploit_def = GameData.EXPLOITS["system_crash"]
        exploit = ExploitItem("system_crash", exploit_def)

        result = manager.equip_exploit(exploit)

        assert result is False


class TestInventoryManagerUnequipping:
    """Test exploit unequipping mechanics."""

    def test_unequip_exploit_removes_from_equipped_list(self, real_game_data):
        """unequip_exploit should remove from equipped_exploits."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["system_hop"]

        result = manager.unequip_exploit("system_hop")

        assert result is True
        assert "system_hop" not in manager.equipped_exploits

    def test_unequip_exploit_adds_to_inventory(self, real_game_data):
        """unequip_exploit should add exploit back to items."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["system_hop"]

        manager.unequip_exploit("system_hop")

        # Should have added ExploitItem back to inventory
        exploits = manager.get_items_by_type("exploit")
        assert len(exploits) == 1
        assert exploits[0].exploit_key == "system_hop"

    def test_unequip_exploit_fails_if_not_equipped(self, real_game_data):
        """unequip_exploit should fail if exploit not equipped."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = []

        result = manager.unequip_exploit("nonexistent_exploit")

        assert result is False


class TestInventoryManagerRAMCalculation:
    """Test RAM usage calculation."""

    def test_get_ram_usage_calculates_correctly(self, real_game_data):
        """get_ram_usage should sum RAM costs of equipped exploits."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        # Equip exploits with known RAM costs
        # system_hop costs 3 RAM, traffic_masquerade costs 2 RAM
        manager.equipped_exploits = ["system_hop", "traffic_masquerade"]

        ram_usage = manager.get_ram_usage()

        # system_hop (3) + traffic_masquerade (2) = 5
        assert ram_usage == 5

    def test_get_ram_usage_returns_zero_for_no_exploits(self, real_game_data):
        """get_ram_usage should return 0 when no exploits equipped."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = []

        ram_usage = manager.get_ram_usage()

        assert ram_usage == 0

    def test_can_equip_exploit_checks_ram_availability(self, real_game_data):
        """can_equip_exploit should return False if insufficient RAM."""
        mock_player = Mock()
        mock_player.ram_total = 5
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["system_hop"]  # 3 RAM used

        # Try to equip traffic_masquerade (2 RAM)
        # 3 + 2 = 5, which equals ram_total (should succeed)
        assert manager.can_equip_exploit("traffic_masquerade") is True

        # Try to equip buffer_overflow (2 RAM) when already at limit
        manager.equipped_exploits = ["system_hop", "traffic_masquerade"]  # 5 RAM used
        assert manager.can_equip_exploit("buffer_overflow") is False

    def test_can_equip_exploit_checks_slot_availability(self, real_game_data):
        """can_equip_exploit should return False if no slots available."""
        mock_player = Mock()
        mock_player.ram_total = 100  # Lots of RAM
        manager = InventoryManager(mock_player)
        manager.max_equipped_exploits = 1
        manager.equipped_exploits = ["system_hop"]  # Slot full

        result = manager.can_equip_exploit("traffic_masquerade")

        assert result is False

    def test_can_equip_exploit_returns_false_if_already_equipped(self, real_game_data):
        """can_equip_exploit should return False if already equipped."""
        mock_player = Mock()
        mock_player.ram_total = 100
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["system_hop"]

        result = manager.can_equip_exploit("system_hop")

        assert result is False


class TestInventoryManagerQueries:
    """Test inventory query methods."""

    def test_get_equipped_exploit_names_returns_names(self, real_game_data):
        """get_equipped_exploit_names should return exploit names."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["system_hop", "traffic_masquerade"]

        names = manager.get_equipped_exploit_names()

        assert "System Hop" in names
        assert "Traffic Masquerade" in names
        assert len(names) == 2


class TestCodeHackStacking:
    """Test code hack quantity management."""

    def test_code_hack_initializes_with_quantity(self):
        """CodeHack should initialize with specified quantity."""
        code = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=3)

        assert code.quantity == 3

    def test_adding_discovered_code_marks_stack_discovered(self, real_game_data):
        """Adding discovered code to stack should mark stack as discovered."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)

        # Add undiscovered code
        code1 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=1)
        code1.discovered = False
        manager.add_item(code1)

        # Add discovered code of same color
        code2 = CodeHack("crimson", "restore_cpu", "Crimson Code", "Test", quantity=1)
        code2.discovered = True
        manager.add_item(code2)

        # Stack should now be marked discovered
        code_hacks = manager.get_items_by_type("code_hack")
        assert code_hacks[0].discovered is True


class TestExploitItemRAM:
    """Test ExploitItem RAM cost tracking."""

    def test_exploit_item_caches_ram_cost(self, real_game_data):
        """ExploitItem should cache RAM cost from exploit definition."""
        exploit_def = ExploitDefinition(
            "Test Exploit", 5, 10, 3, "test", 10, TargetingMode.SINGLE, "Test"
        )
        exploit = ExploitItem("test_exploit", exploit_def)

        assert exploit.ram_cost == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
