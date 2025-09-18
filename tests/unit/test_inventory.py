#!/usr/bin/env python3
"""
Unit tests for inventory and item management system.
Tests InventoryItem, CodeHack, ExploitItem, StoryFragment, and InventoryManager.
"""

import pytest
from unittest.mock import Mock, MagicMock
import random

from game_inventory import (
    InventoryItem, CodeHack, ExploitItem, StoryFragment, InventoryManager
)
from game_entities import ExploitDefinition
from game_data import GameData, GameBalance


class TestInventoryItem:
    """Test the base InventoryItem class."""
    
    def test_inventory_item_creation(self):
        """Test basic inventory item creation."""
        item = InventoryItem("Test Item", "test_type", "Test description")
        assert item.name == "Test Item"
        assert item.item_type == "test_type"
        assert item.description == "Test description"
    
    def test_inventory_item_creation_no_description(self):
        """Test inventory item creation without description."""
        item = InventoryItem("Simple Item", "simple")
        assert item.name == "Simple Item"
        assert item.item_type == "simple"
        assert item.description == ""
    
    def test_inventory_item_use_default(self):
        """Test default use method returns False."""
        item = InventoryItem("Unusable", "test")
        mock_player = Mock()
        mock_game = Mock()
        assert item.use(mock_player, mock_game) is False


class TestCodeHack:
    """Test the CodeHack item class."""
    
    def test_code_hack_creation(self):
        """Test code hack creation with all parameters."""
        code = CodeHack("red", "restore_cpu", "Red Code", "Restores CPU", 3)
        assert code.name == "Red Code"
        assert code.item_type == "code_hack"
        assert code.color_name == "red"
        assert code.effect == "restore_cpu"
        assert code.quantity == 3
        assert code.discovered is False
    
    def test_code_hack_creation_defaults(self):
        """Test code hack creation with default values."""
        code = CodeHack("blue", "reduce_heat", "Blue Code")
        assert code.quantity == 1
        assert code.description == ""
        assert code.discovered is False
    
    def test_code_hack_use_invalid_effect(self):
        """Test using a code hack with invalid effect."""
        code = CodeHack("invalid", "nonexistent", "Invalid Code")
        mock_player = Mock()
        mock_game = Mock()
        mock_game.data_patch_effects = {"red": ("restore_cpu", "Restores CPU")}
        
        result = code.use(mock_player, mock_game)
        assert result is False
    
    def test_code_hack_use_valid_unknown_effect(self):
        """Test using a code hack with valid but unknown effect."""
        code = CodeHack("green", "reduce_heat", "Green Code", quantity=2)
        
        # Mock game components
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.items = [code]
        
        mock_game = Mock()
        mock_game.data_patch_effects = {"green": ("reduce_heat", "Reduces heat")}
        mock_game.discovered_code_effects = {}
        mock_game.sound_manager = Mock()
        mock_game.message_log = Mock()
        
        # Mock the apply effect method
        code._apply_effect = Mock(return_value=True)
        
        result = code.use(mock_player, mock_game)
        
        assert result is True
        assert code.quantity == 1  # Should decrease by 1
        assert "green" in mock_game.discovered_code_effects
        assert code.discovered is True
        mock_game.sound_manager.play_sound.assert_called_once_with("item_use_code")
    
    def test_code_hack_use_known_effect(self):
        """Test using a code hack with known effect."""
        code = CodeHack("blue", "speed_boost", "Blue Code", quantity=1)
        
        # Mock game components
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.remove_item = Mock()
        
        mock_game = Mock()
        mock_game.data_patch_effects = {"blue": ("speed_boost", "Speed boost")}
        mock_game.discovered_code_effects = {"blue": "speed_boost"}
        mock_game.sound_manager = Mock()
        mock_game.message_log = Mock()
        
        # Mock the apply effect method
        code._apply_effect = Mock(return_value=True)
        
        result = code.use(mock_player, mock_game)
        
        assert result is True
        assert code.discovered is True
        mock_player.inventory_manager.remove_item.assert_called_once_with(code)
    
    def test_code_hack_apply_restore_cpu(self):
        """Test CPU restoration effect."""
        code = CodeHack("red", "restore_cpu", "Red Code")
        
        mock_player = Mock()
        mock_player.cpu = 50
        mock_player.max_cpu = 100
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        # Mock random to return predictable value
        with pytest.MonkeyPatch().context() as m:
            m.setattr(random, 'randint', lambda min_val, max_val: 30)
            
            result = code._apply_effect("restore_cpu", mock_player, mock_game)
            
            assert result is True
            assert mock_player.cpu == 80  # 50 + 30
            mock_game.message_log.add_message.assert_called_with("CPU restored: +30")
    
    def test_code_hack_apply_restore_cpu_overflow(self):
        """Test CPU restoration when near max."""
        code = CodeHack("red", "restore_cpu", "Red Code")
        
        mock_player = Mock()
        mock_player.cpu = 95
        mock_player.max_cpu = 100
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        # Mock random to return large value
        with pytest.MonkeyPatch().context() as m:
            m.setattr(random, 'randint', lambda min_val, max_val: 20)
            
            result = code._apply_effect("restore_cpu", mock_player, mock_game)
            
            assert result is True
            assert mock_player.cpu == 100  # Capped at max
            mock_game.message_log.add_message.assert_called_with("CPU restored: +5")
    
    def test_code_hack_apply_reduce_heat(self):
        """Test heat reduction effect."""
        code = CodeHack("blue", "reduce_heat", "Blue Code")
        
        mock_player = Mock()
        mock_player.heat = 80
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        # Mock GameBalance constant
        with pytest.MonkeyPatch().context() as m:
            m.setattr(GameBalance, 'HEAT_REDUCTION_INSTANT', 25)
            
            result = code._apply_effect("reduce_heat", mock_player, mock_game)
            
            assert result is True
            assert mock_player.heat == 55  # 80 - 25
            mock_game.message_log.add_message.assert_called_with("Heat reduced: -25°C")
    
    def test_code_hack_apply_reduce_heat_minimum(self):
        """Test heat reduction doesn't go below zero."""
        code = CodeHack("blue", "reduce_heat", "Blue Code")
        
        mock_player = Mock()
        mock_player.heat = 10
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        # Mock GameBalance constant
        with pytest.MonkeyPatch().context() as m:
            m.setattr(GameBalance, 'HEAT_REDUCTION_INSTANT', 25)
            
            result = code._apply_effect("reduce_heat", mock_player, mock_game)
            
            assert result is True
            assert mock_player.heat == 0  # Minimum
            mock_game.message_log.add_message.assert_called_with("Heat reduced: -10°C")
    
    def test_code_hack_apply_reduce_detection(self):
        """Test detection reduction effect."""
        code = CodeHack("green", "reduce_detection", "Green Code")
        
        mock_player = Mock()
        mock_player.detection = 75.5
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = code._apply_effect("reduce_detection", mock_player, mock_game)
        
        assert result is True
        assert mock_player.detection == 50.5  # 75.5 - 25
        mock_game.message_log.add_message.assert_called_with("Detection: -25.0%")
    
    def test_code_hack_apply_speed_boost_new(self):
        """Test speed boost effect when not active."""
        code = CodeHack("yellow", "speed_boost", "Yellow Code")
        
        mock_player = Mock()
        mock_player.temporary_effects = {}
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = code._apply_effect("speed_boost", mock_player, mock_game)
        
        assert result is True
        assert mock_player.temporary_effects['speed_boost_turns'] == 5
        mock_game.message_log.add_message.assert_called_with("Speed boost active (5 turns)")
    
    def test_code_hack_apply_speed_boost_existing(self):
        """Test speed boost effect when already active."""
        code = CodeHack("yellow", "speed_boost", "Yellow Code")
        
        mock_player = Mock()
        mock_player.temporary_effects = {'speed_boost_turns': 3}
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = code._apply_effect("speed_boost", mock_player, mock_game)
        
        assert result is True
        # Should not change existing boost
        assert mock_player.temporary_effects['speed_boost_turns'] == 3
        mock_game.message_log.add_message.assert_called_with("Speed boost already active")
    
    def test_code_hack_apply_enhanced_vision_new(self):
        """Test enhanced vision effect when not active."""
        code = CodeHack("purple", "enhanced_vision", "Purple Code")
        
        mock_player = Mock()
        mock_player.temporary_effects = {}
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = code._apply_effect("enhanced_vision", mock_player, mock_game)
        
        assert result is True
        assert mock_player.temporary_effects['enhanced_vision_turns'] == 5
        mock_game.message_log.add_message.assert_called_with("Enhanced vision active (5 turns)")
    
    def test_code_hack_apply_enhanced_vision_extend(self):
        """Test enhanced vision effect extension."""
        code = CodeHack("purple", "enhanced_vision", "Purple Code")
        
        mock_player = Mock()
        mock_player.temporary_effects = {'enhanced_vision_turns': 2}
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = code._apply_effect("enhanced_vision", mock_player, mock_game)
        
        assert result is True
        assert mock_player.temporary_effects['enhanced_vision_turns'] == 7  # 2 + 5
        mock_game.message_log.add_message.assert_called_with("Enhanced vision extended (7 turns)")


class TestExploitItem:
    """Test the ExploitItem class."""
    
    def test_exploit_item_creation(self):
        """Test exploit item creation."""
        exploit_def = ExploitDefinition(
            name="Test Exploit",
            description="Test description",
            category="stealth",
            targeting="self",
            ram=10,
            heat=5,
            range=1,
            damage=0
        )
        
        exploit = ExploitItem("test_exploit", exploit_def)
        
        assert exploit.name == "Test Exploit"
        assert exploit.item_type == "exploit"
        assert exploit.description == "Test description"
        assert exploit.exploit_key == "test_exploit"
        assert exploit.ram_cost == 10
    
    def test_exploit_item_use_success(self):
        """Test successful exploit equipping."""
        exploit_def = ExploitDefinition(
            name="Stealth Exploit",
            description="Stealth description",
            category="stealth",
            targeting="self",
            ram=5,
            heat=0,
            range=1,
            damage=0
        )
        
        exploit = ExploitItem("stealth_exploit", exploit_def)
        
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equip_exploit = Mock(return_value=True)
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = exploit.use(mock_player, mock_game)
        
        assert result is True
        mock_player.inventory_manager.equip_exploit.assert_called_once_with(exploit)
        mock_game.message_log.add_message.assert_called_with("Equipped Stealth Exploit")
    
    def test_exploit_item_use_already_equipped(self):
        """Test exploit equipping when already equipped."""
        exploit_def = ExploitDefinition(
            name="Duplicate Exploit",
            description="Duplicate description",
            category="combat",
            targeting="target",
            ram=8,
            heat=3,
            range=2,
            damage=5
        )
        
        exploit = ExploitItem("duplicate_exploit", exploit_def)
        
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equip_exploit = Mock(return_value=False)
        mock_player.inventory_manager.equipped_exploits = ["duplicate_exploit"]
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = exploit.use(mock_player, mock_game)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Duplicate Exploit already equipped")
    
    def test_exploit_item_use_no_slots(self):
        """Test exploit equipping when no slots available."""
        exploit_def = ExploitDefinition(
            name="Full Exploit",
            description="Full description",
            category="utility",
            targeting="self",
            ram=6,
            heat=2,
            range=1,
            damage=0
        )
        
        exploit = ExploitItem("full_exploit", exploit_def)
        
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equip_exploit = Mock(return_value=False)
        mock_player.inventory_manager.equipped_exploits = ["other1", "other2", "other3"]
        mock_player.inventory_manager.max_equipped_exploits = 3
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        result = exploit.use(mock_player, mock_game)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("No exploit slots available (3 max)")
    
    def test_exploit_item_use_insufficient_ram(self):
        """Test exploit equipping with insufficient RAM."""
        exploit_def = ExploitDefinition(
            name="Heavy Exploit",
            description="Heavy description",
            category="combat",
            targeting="target",
            ram=20,
            heat=5,
            range=3,
            damage=8
        )
        
        exploit = ExploitItem("heavy_exploit", exploit_def)
        
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.equip_exploit = Mock(return_value=False)
        mock_player.inventory_manager.equipped_exploits = []
        mock_player.inventory_manager.max_equipped_exploits = 5
        mock_player.inventory_manager.get_ram_usage = Mock(return_value=15)
        mock_player.ram_total = 30
        
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {"heavy_exploit": exploit_def}
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            result = exploit.use(mock_player, mock_game)
            
            assert result is False
            mock_game.message_log.add_message.assert_called_with("Not enough RAM: 35/30")


class TestStoryFragment:
    """Test the StoryFragment class."""
    
    def test_story_fragment_creation(self):
        """Test story fragment creation."""
        fragment = StoryFragment(5)
        
        assert fragment.name == "Story Fragment"
        assert fragment.item_type == "story_fragment"
        assert fragment.description == "A fragment of the truth..."
        assert fragment.fragment_index == 5
    
    def test_story_fragment_use(self):
        """Test story fragment usage."""
        fragment = StoryFragment(3)
        
        mock_player = Mock()
        mock_player.inventory_manager = Mock()
        mock_player.inventory_manager.remove_item = Mock()
        
        mock_game = Mock()
        
        result = fragment.use(mock_player, mock_game)
        
        assert result is True
        mock_player.inventory_manager.remove_item.assert_called_once_with(fragment)


class TestInventoryManager:
    """Test the InventoryManager class."""
    
    def test_inventory_manager_creation(self):
        """Test inventory manager creation."""
        mock_player = Mock()
        
        # Mock GameData.EXPLOITS
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "exploit1": Mock(),
                "exploit2": Mock(),
                "exploit3": Mock()
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            m.setattr(random, 'choice', lambda x: "exploit2")
            
            manager = InventoryManager(mock_player)
            
            assert manager.player == mock_player
            assert manager.items == []
            assert manager.equipped_exploits == ["exploit2"]
            assert manager.max_equipped_exploits == 5
    
    def test_add_code_hack_new_color(self):
        """Test adding a code hack with new color."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        code = CodeHack("red", "restore_cpu", "Red Code", quantity=2)
        result = manager.add_item(code)
        
        assert result is True
        assert len(manager.items) == 1
        assert manager.items[0] == code
    
    def test_add_code_hack_existing_color(self):
        """Test adding a code hack with existing color."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        # Add initial code
        existing_code = CodeHack("blue", "reduce_heat", "Blue Code", quantity=1)
        manager.items.append(existing_code)
        
        # Add new code of same color
        new_code = CodeHack("blue", "reduce_heat", "Blue Code", quantity=3)
        result = manager.add_item(new_code)
        
        assert result is True
        assert len(manager.items) == 1  # Should not add new item
        assert existing_code.quantity == 4  # 1 + 3
    
    def test_add_code_hack_discovered_flag(self):
        """Test adding discovered code hack to existing stack."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        # Add initial undiscovered code
        existing_code = CodeHack("green", "speed_boost", "Green Code", quantity=1)
        existing_code.discovered = False
        manager.items.append(existing_code)
        
        # Add discovered code of same color
        new_code = CodeHack("green", "speed_boost", "Green Code", quantity=2)
        new_code.discovered = True
        result = manager.add_item(new_code)
        
        assert result is True
        assert existing_code.discovered is True
        assert existing_code.quantity == 3
    
    def test_add_non_code_item(self):
        """Test adding non-code items."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        fragment = StoryFragment(1)
        result = manager.add_item(fragment)
        
        assert result is True
        assert len(manager.items) == 1
        assert manager.items[0] == fragment
    
    def test_remove_item_exists(self):
        """Test removing an existing item."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        item = StoryFragment(2)
        manager.items.append(item)
        
        result = manager.remove_item(item)
        
        assert result is True
        assert len(manager.items) == 0
    
    def test_remove_item_not_exists(self):
        """Test removing a non-existing item."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        item = StoryFragment(3)
        result = manager.remove_item(item)
        
        assert result is False
        assert len(manager.items) == 0
    
    def test_get_items_by_type(self):
        """Test getting items by type."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        
        code1 = CodeHack("red", "restore_cpu", "Red Code")
        code2 = CodeHack("blue", "reduce_heat", "Blue Code")
        fragment = StoryFragment(1)
        
        manager.items.extend([code1, fragment, code2])
        
        codes = manager.get_items_by_type("data_patch")
        fragments = manager.get_items_by_type("story_fragment")
        
        assert len(codes) == 0  # Code hacks have type "code_hack", not "data_patch"
        assert len(fragments) == 1
        assert fragments[0] == fragment
    
    def test_equip_exploit_success(self):
        """Test successful exploit equipping."""
        mock_player = Mock()
        mock_player.ram_total = 50
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["existing_exploit"]
        
        # Mock GameData
        exploit_def = ExploitDefinition(
            name="New Exploit",
            description="New description",
            category="stealth",
            targeting="self",
            ram=10,
            heat=0,
            range=1,
            damage=0
        )
        
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "existing_exploit": Mock(ram=5),
                "new_exploit": exploit_def
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            exploit_item = ExploitItem("new_exploit", exploit_def)
            manager.items.append(exploit_item)
            
            result = manager.equip_exploit(exploit_item)
            
            assert result is True
            assert "new_exploit" in manager.equipped_exploits
            assert exploit_item not in manager.items
    
    def test_equip_exploit_already_equipped(self):
        """Test equipping already equipped exploit."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["duplicate_exploit"]
        
        exploit_def = ExploitDefinition(
            name="Duplicate",
            description="Duplicate",
            category="combat",
            targeting="target",
            ram=8,
            heat=0,
            range=2,
            damage=4
        )
        
        exploit_item = ExploitItem("duplicate_exploit", exploit_def)
        
        result = manager.equip_exploit(exploit_item)
        
        assert result is False
        assert len(manager.equipped_exploits) == 1
    
    def test_equip_exploit_no_slots(self):
        """Test equipping when no slots available."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["e1", "e2", "e3", "e4", "e5"]  # Max slots
        manager.max_equipped_exploits = 5
        
        exploit_def = ExploitDefinition(
            name="Sixth",
            description="Sixth",
            category="utility",
            targeting="self",
            ram=5,
            heat=0,
            range=1,
            damage=0
        )
        
        exploit_item = ExploitItem("sixth_exploit", exploit_def)
        
        result = manager.equip_exploit(exploit_item)
        
        assert result is False
        assert len(manager.equipped_exploits) == 5
    
    def test_equip_exploit_insufficient_ram(self):
        """Test equipping with insufficient RAM."""
        mock_player = Mock()
        mock_player.ram_total = 20
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["heavy_exploit"]
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "heavy_exploit": Mock(ram=15),
                "another_exploit": Mock(ram=10)
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            exploit_def = ExploitDefinition(
                name="Another",
                description="Another",
                category="combat",
                targeting="target",
                ram=10,
                heat=0,
                range=2,
                damage=5
            )
            
            exploit_item = ExploitItem("another_exploit", exploit_def)
            
            result = manager.equip_exploit(exploit_item)
            
            assert result is False  # 15 + 10 = 25 > 20
            assert len(manager.equipped_exploits) == 1
    
    def test_unequip_exploit_success(self):
        """Test successful exploit unequipping."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["target_exploit", "other_exploit"]
        
        # Mock GameData
        exploit_def = ExploitDefinition(
            name="Target Exploit",
            description="Target description",
            category="stealth",
            targeting="self",
            ram=8,
            heat=0,
            range=1,
            damage=0
        )
        
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {"target_exploit": exploit_def}
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            result = manager.unequip_exploit("target_exploit")
            
            assert result is True
            assert "target_exploit" not in manager.equipped_exploits
            assert len(manager.items) == 1
            assert isinstance(manager.items[0], ExploitItem)
            assert manager.items[0].exploit_key == "target_exploit"
    
    def test_unequip_exploit_not_equipped(self):
        """Test unequipping non-equipped exploit."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["other_exploit"]
        
        result = manager.unequip_exploit("nonexistent_exploit")
        
        assert result is False
        assert manager.equipped_exploits == ["other_exploit"]
        assert len(manager.items) == 0
    
    def test_get_ram_usage(self):
        """Test RAM usage calculation."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["exploit1", "exploit2", "nonexistent"]
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "exploit1": Mock(ram=8),
                "exploit2": Mock(ram=12)
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            total_ram = manager.get_ram_usage()
            
            assert total_ram == 20  # 8 + 12, nonexistent ignored
    
    def test_can_equip_exploit_success(self):
        """Test exploit equipping check - success case."""
        mock_player = Mock()
        mock_player.ram_total = 30
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["existing"]
        manager.max_equipped_exploits = 5
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "existing": Mock(ram=10),
                "new_exploit": Mock(ram=15)
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            result = manager.can_equip_exploit("new_exploit")
            
            assert result is True  # 10 + 15 = 25 <= 30
    
    def test_can_equip_exploit_already_equipped(self):
        """Test exploit equipping check - already equipped."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["duplicate"]
        
        result = manager.can_equip_exploit("duplicate")
        
        assert result is False
    
    def test_can_equip_exploit_no_slots(self):
        """Test exploit equipping check - no slots."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["e1", "e2", "e3"]
        manager.max_equipped_exploits = 3
        
        result = manager.can_equip_exploit("new_exploit")
        
        assert result is False
    
    def test_can_equip_exploit_insufficient_ram(self):
        """Test exploit equipping check - insufficient RAM."""
        mock_player = Mock()
        mock_player.ram_total = 20
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["heavy"]
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploits = {
                "heavy": Mock(ram=15),
                "expensive": Mock(ram=10)
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            result = manager.can_equip_exploit("expensive")
            
            assert result is False  # 15 + 10 = 25 > 20
    
    def test_get_equipped_exploit_names(self):
        """Test getting equipped exploit names."""
        mock_player = Mock()
        manager = InventoryManager(mock_player)
        manager.equipped_exploits = ["exploit1", "exploit2", "nonexistent"]
        
        # Mock GameData
        with pytest.MonkeyPatch().context() as m:
            mock_exploit1 = Mock()
            mock_exploit1.name = "First Exploit"
            mock_exploit2 = Mock()
            mock_exploit2.name = "Second Exploit"
            
            mock_exploits = {
                "exploit1": mock_exploit1,
                "exploit2": mock_exploit2
            }
            m.setattr(GameData, 'EXPLOITS', mock_exploits)
            
            names = manager.get_equipped_exploit_names()
            
            assert names == ["First Exploit", "Second Exploit"]
            # nonexistent exploit should be ignored