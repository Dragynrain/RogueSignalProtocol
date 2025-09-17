#!/usr/bin/env python3
"""
Inventory and item management system.
Extracted from RogueSignalProtocol.py for better organization.
"""

import random
from typing import List
from game_entities import ExploitDefinition
from game_data import GameData, GameBalance


class InventoryItem:
    """Base class for all inventory items."""
    
    def __init__(self, name: str, item_type: str, description: str = ""):
        self.name = name
        self.item_type = item_type
        self.description = description
    
    def use(self, player, game) -> bool:
        """Use the item. Returns True if successful. Override in subclasses."""
        return False


class DataPatch(InventoryItem):
    """Randomized codes with unknown effects until used."""
    
    def __init__(self, color_name: str, effect: str, name: str, description: str = "", quantity: int = 1):
        super().__init__(name, "data_patch", description)
        self.color_name = color_name
        self.effect = effect
        self.quantity = quantity
        self.discovered = False
    
    def use(self, player, game) -> bool:
        """Apply the code effect to the player."""
        if self.color_name not in game.data_patch_effects:
            return False
        
        # Play code usage sound
        game.sound_manager.play_sound("item_use_code")
        
        # Use one from the stack
        self.quantity -= 1
        if self.quantity <= 0:
            player.inventory_manager.remove_item(self)
        
        effect_key, description = game.data_patch_effects[self.color_name]
        
        # Check if this color effect has been discovered in this game session
        is_known = self.color_name in game.discovered_code_effects
        
        if not is_known:
            # Mark this color effect as discovered for this game session
            game.discovered_code_effects[self.color_name] = effect_key
            
            # Update all data patches of this color in player's inventory to be discovered
            for item in player.inventory_manager.items:
                if isinstance(item, DataPatch) and item.color_name == self.color_name:
                    item.discovered = True
                    
            game.message_log.add_message(f"Used {self.name}: {description}")
        else:
            # Effect is known, show it was already identified
            self.discovered = True
            game.message_log.add_message(f"Used {self.name} ({description})")
        
        return self._apply_effect(effect_key, player, game)
    
    def _apply_effect(self, effect_key: str, player, game) -> bool:
        """Apply the specific effect."""
        if effect_key == 'restore_cpu':
            restore = random.randint(GameBalance.CPU_RESTORE_MIN, GameBalance.CPU_RESTORE_MAX)
            actual = min(restore, player.max_cpu - player.cpu)
            player.cpu += actual
            game.message_log.add_message(f"CPU restored: +{actual}")
        
        elif effect_key == 'reduce_heat':
            old_heat = player.heat
            player.heat = max(0, player.heat - GameBalance.HEAT_REDUCTION_INSTANT)
            actual_reduction = old_heat - player.heat
            game.message_log.add_message(f"Heat reduced: -{actual_reduction}°C")
        
        elif effect_key == 'reduce_detection':
            old_detection = player.detection
            player.detection = max(0, player.detection - 25)
            actual_reduction = old_detection - player.detection
            game.message_log.add_message(f"Detection: -{actual_reduction:.1f}%")
        
        elif effect_key == 'speed_boost':
            current_speed = player.temporary_effects.get('speed_boost_turns', 0)
            current_slow = player.temporary_effects.get('movement_slowed_turns', 0)
            
            if current_speed > 0:
                game.message_log.add_message("Speed boost already active")
            else:
                speed_to_add = 5
                
                if current_slow > 0:
                    # Offset against existing slow
                    if speed_to_add >= current_slow:
                        # Speed boost overcomes all slow
                        player.temporary_effects['movement_slowed_turns'] = 0
                        player.temporary_effects['speed_boost_turns'] = speed_to_add - current_slow
                        game.message_log.add_message(f"Speed boost active ({speed_to_add - current_slow} turns)")
                        if current_slow > 0:
                            game.message_log.add_message("Movement inhibition cancelled")
                    else:
                        # Slow overcomes all speed boost
                        player.temporary_effects['speed_boost_turns'] = 0
                        player.temporary_effects['movement_slowed_turns'] = current_slow - speed_to_add
                        game.message_log.add_message("Speed boost countered by inhibition")
                else:
                    # No slow, add speed normally
                    player.temporary_effects['speed_boost_turns'] = speed_to_add
                    game.message_log.add_message(f"Speed boost active ({speed_to_add} turns)")
        
        elif effect_key == 'enhanced_vision':
            current_turns = player.temporary_effects.get('enhanced_vision_turns', 0)
            new_turns = max(current_turns + 5, 5)  # Add 5 turns, minimum 5
            player.temporary_effects['enhanced_vision_turns'] = new_turns
            if current_turns > 0:
                game.message_log.add_message(f"Enhanced vision extended ({new_turns} turns)")
            else:
                game.message_log.add_message("Enhanced vision active (5 turns)")
        
        elif effect_key == 'exploit_efficiency':
            current_turns = player.temporary_effects.get('exploit_efficiency_turns', 0)
            new_turns = max(current_turns + 8, 8)  # Add 8 turns, minimum 8
            player.temporary_effects['exploit_efficiency_turns'] = new_turns
            if current_turns > 0:
                game.message_log.add_message(f"Exploit efficiency extended ({new_turns} turns)")
            else:
                game.message_log.add_message("Exploit efficiency active (8 turns)")
        
        return True


class ExploitItem(InventoryItem):
    """Exploit items that can be equipped."""
    
    def __init__(self, exploit_key: str, exploit_def: ExploitDefinition):
        super().__init__(exploit_def.name, "exploit", exploit_def.description)
        self.exploit_key = exploit_key
        self.ram_cost = exploit_def.ram
    
    def use(self, player, game) -> bool:
        """Equip the exploit."""
        success = player.inventory_manager.equip_exploit(self)
        if success:
            game.message_log.add_message(f"Equipped {self.name}")
        else:
            # Check specific failure reasons
            if self.exploit_key in player.inventory_manager.equipped_exploits:
                game.message_log.add_message(f"{self.name} already equipped")
            elif len(player.inventory_manager.equipped_exploits) >= player.inventory_manager.max_equipped_exploits:
                game.message_log.add_message(f"No exploit slots available ({player.inventory_manager.max_equipped_exploits} max)")
            else:
                # Must be RAM issue
                current_ram = player.inventory_manager.get_ram_usage()
                needed_ram = GameData.EXPLOITS[self.exploit_key].ram if self.exploit_key in GameData.EXPLOITS else 0
                game.message_log.add_message(f"Not enough RAM: {current_ram + needed_ram}/{player.ram_total}")
        return success


class StoryFragment(InventoryItem):
    """Story fragment items that reveal narrative pieces."""
    
    def __init__(self, fragment_index: int):
        super().__init__("Story Fragment", "story_fragment", "A fragment of the truth...")
        self.fragment_index = fragment_index
    
    def use(self, player, game) -> bool:
        """Use story fragment - automatically triggers discovery screen."""
        # The story fragment discovery and display is handled elsewhere
        # This use method just removes it from inventory since it's consumed
        player.inventory_manager.remove_item(self)
        return True


class InventoryManager:
    """Manages player inventory and equipped items."""
    
    def __init__(self, player):
        self.player = player
        self.items: List[InventoryItem] = []
        # Start with one random exploit
        all_exploits = list(GameData.EXPLOITS.keys())
        self.equipped_exploits: List[str] = [random.choice(all_exploits)]
        self.max_equipped_exploits = 5
    
    def add_item(self, item: InventoryItem) -> bool:
        """Add an item to inventory."""
        if isinstance(item, DataPatch):
            # Look for existing code of the same color
            for existing_item in self.items:
                if (isinstance(existing_item, DataPatch) and 
                    existing_item.color_name == item.color_name):
                        # Found matching color, add to existing stack
                        existing_item.quantity += item.quantity
                        # If the new patch is discovered, mark the stack as discovered
                        if item.discovered:
                            existing_item.discovered = True
                        return True
            # No existing stack found, add as new item
        
        # Add non-code items or new code colors
        self.items.append(item)
        return True
    
    def remove_item(self, item: InventoryItem) -> bool:
        """Remove an item from inventory."""
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def get_items_by_type(self, item_type: str) -> List[InventoryItem]:
        """Get all items of a specific type."""
        items = [item for item in self.items if item.item_type == item_type]
        if item_type == "data_patch":
            items.sort(key=lambda x: x.name.lower())
        return items
    
    def get_display_items(self) -> List[InventoryItem]:
        """Get all items in display order (codes first, then exploits)."""
        display_items = []
        # Add codes first (sorted alphabetically)
        display_items.extend(self.get_items_by_type("data_patch"))
        # Add other items (exploits, etc.)
        display_items.extend(self.get_items_by_type("exploit"))
        # Add any other item types
        display_items.extend([item for item in self.items if item.item_type not in ["data_patch", "exploit"]])
        return display_items
    
    def equip_exploit(self, exploit_item: ExploitItem) -> bool:
        """Equip an exploit from inventory."""
        # Check if already equipped
        if exploit_item.exploit_key in self.equipped_exploits:
            return False
        
        # Check if we have room for more exploits
        if len(self.equipped_exploits) >= self.max_equipped_exploits:
            return False
        
        # Check if we have enough RAM
        current_ram_usage = self.get_ram_usage()
        exploit_ram_cost = GameData.EXPLOITS[exploit_item.exploit_key].ram
        
        if current_ram_usage + exploit_ram_cost > self.player.ram_total:
            return False
        
        # Equip the exploit
        self.equipped_exploits.append(exploit_item.exploit_key)
        self.remove_item(exploit_item)
        return True
    
    def unequip_exploit(self, exploit_key: str) -> bool:
        """Unequip an exploit and return it to inventory."""
        if exploit_key not in self.equipped_exploits:
            return False
        
        # Remove from equipped list
        self.equipped_exploits.remove(exploit_key)
        
        # Add back to inventory
        exploit_def = GameData.EXPLOITS[exploit_key]
        exploit_item = ExploitItem(exploit_key, exploit_def)
        self.add_item(exploit_item)
        
        return True
    
    def get_ram_usage(self) -> int:
        """Calculate current RAM usage from equipped exploits."""
        total_ram = 0
        for exploit_key in self.equipped_exploits:
            if exploit_key in GameData.EXPLOITS:
                total_ram += GameData.EXPLOITS[exploit_key].ram
        return total_ram
    
    def can_equip_exploit(self, exploit_key: str) -> bool:
        """Check if an exploit can be equipped."""
        # Check if already equipped
        if exploit_key in self.equipped_exploits:
            return False
        
        # Check if we have room for more exploits
        if len(self.equipped_exploits) >= self.max_equipped_exploits:
            return False
        
        # Check if we have enough RAM
        current_ram_usage = self.get_ram_usage()
        exploit_ram_cost = GameData.EXPLOITS[exploit_key].ram
        
        return current_ram_usage + exploit_ram_cost <= self.player.ram_total
    
    def get_equipped_exploit_names(self) -> List[str]:
        """Get the names of all equipped exploits."""
        names = []
        for exploit_key in self.equipped_exploits:
            if exploit_key in GameData.EXPLOITS:
                names.append(GameData.EXPLOITS[exploit_key].name)
        return names