#!/usr/bin/env python3
"""
Inventory and item management system with item types and exploit equipping.

This module handles:
- Item types (CodeHack, ExploitItem, StoryFragment) with use() methods
- Code hack discovery system (effects randomized per session, revealed on first use)
- Exploit equipping with RAM constraints and slot limits
- Inventory operations (add, remove, stack management for code hacks)
- RAM usage calculation from equipped exploits

Key pattern:
All items inherit from InventoryItem and override use() for their specific behavior.
InventoryManager delegates to items for usage logic.
"""

import random
from typing import List
from game_entities import ExploitDefinition
from game_data import GameData
from game_config import GameBalance


class InventoryItem:
    """
    Base class for all inventory items using template method pattern.

    Subclasses override use() to implement specific item behavior (heal,
    equip exploit, reveal story, etc.). The base implementation returns
    False to indicate no effect.

    Attributes:
        name: Display name for UI
        item_type: Category string (code_hack, exploit, story_fragment)
        description: Descriptive text shown in menus
    """

    def __init__(self, name: str, item_type: str, description: str = ""):
        self.name = name
        self.item_type = item_type
        self.description = description

    def use(self, player, game) -> bool:
        """
        Use the item with side effects on player/game state.

        Args:
            player: Player instance to modify
            game: GameEngine instance for message log and game state

        Returns:
            True if item was successfully used
        """
        return False


class CodeHack(InventoryItem):
    """
    Randomized code hacks with discovery system and stack management.

    Code hacks have randomized effects per game session (e.g., "Crimson Code"
    might restore CPU in one run, reduce heat in another). Effects are unknown
    until first use, then revealed for all codes of that color.

    Features:
    - Color-based effect randomization (same color = same effect per session)
    - Discovery tracking (first use reveals effect for that color)
    - Stacking (multiple codes of same color stack in inventory)
    - Various effects (restore CPU, reduce heat/trace, speed boost, enhanced vision)

    Attributes:
        color_name: Color identifier used for effect lookup and stacking
        effect: Effect type key (restore_cpu, reduce_heat, etc.)
        quantity: Number of uses in this stack
        discovered: Whether this color's effect has been revealed
    """

    def __init__(self, color_name: str, effect: str, name: str, description: str = "", quantity: int = 1):
        super().__init__(name, "code_hack", description)
        self.color_name = color_name
        self.effect = effect
        self.quantity = quantity
        self.discovered = False
    
    def use(self, player, game) -> bool:
        """
        Apply code effect and trigger discovery if first use of this color.

        Discovery flow:
        1. Decrement quantity (remove if depleted)
        2. Check if this color has been discovered in this session
        3. If not discovered: mark as discovered, update all matching codes in inventory
        4. Show message (with or without discovery notification)
        5. Apply the specific effect

        Args:
            player: Player instance to apply effect to
            game: GameEngine instance for discovery tracking and messages

        Returns:
            True if effect was successfully applied
        """
        if self.color_name not in game.code_hack_effects:
            return False
        
        # Play code usage sound
        game.sound_manager.play_sound("item_use_code")
        
        # Use one from the stack
        self.quantity -= 1
        if self.quantity <= 0:
            player.inventory_manager.remove_item(self)
        
        effect_key, description = game.code_hack_effects[self.color_name]
        
        # Check if this color effect has been discovered in this game session
        is_known = self.color_name in game.discovered_code_effects

        if not is_known:
            # Mark this color effect as discovered for this game session
            game.discovered_code_effects[self.color_name] = effect_key
            self.discovered = True
            self.description = description
            game.message_log.add_message(f"Used {self.name}: {description}")
        else:
            # Effect is known, show it was already identified
            self.discovered = True
            self.description = description
            game.message_log.add_message(f"Used {self.name} ({description})")

        # Track metrics
        from game_metrics import track
        track("code_hacks_used", category=self.name)

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
        
        elif effect_key == 'reduce_trace_level':
            from game_config import GameConfig
            reduction = GameConfig.get('balance.trace_reduction_code_hack', 25)
            old_trace = player.trace_level
            player.trace_level = max(0, player.trace_level - reduction)
            actual_reduction = old_trace - player.trace_level
            game.message_log.add_message(f"Trace Level: -{actual_reduction:.1f}%")
        
        elif effect_key == 'speed_boost':
            from game_config import GameConfig
            speed_to_add = GameConfig.get('balance.speed_boost_turns', 3)

            if player.temporary_effects.get('speed_boost_turns', 0) > 0:
                game.message_log.add_message("Speed boost already active")
                return True

            current_slow = player.temporary_effects.get('movement_slowed_turns', 0)

            if current_slow > 0:
                net_speed = speed_to_add - current_slow
                if net_speed > 0:
                    player.temporary_effects['movement_slowed_turns'] = 0
                    player.temporary_effects['speed_boost_turns'] = net_speed
                    game.message_log.add_message(f"Speed boost active ({net_speed} enemy turns)")
                    game.message_log.add_message("Movement inhibition cancelled")
                else:
                    player.temporary_effects['speed_boost_turns'] = 0
                    player.temporary_effects['movement_slowed_turns'] = -net_speed
                    game.message_log.add_message("Speed boost countered by inhibition")
            else:
                player.temporary_effects['speed_boost_turns'] = speed_to_add
                game.message_log.add_message(f"Speed boost active ({speed_to_add} enemy turns)")
        
        elif effect_key == 'enhanced_vision':
            from game_config import GameConfig
            turns_to_add = GameConfig.get('balance.enhanced_vision_turns', 5)
            current = player.temporary_effects.get('enhanced_vision_turns', 0)
            new_turns = max(current + turns_to_add, turns_to_add)
            player.temporary_effects['enhanced_vision_turns'] = new_turns
            msg = f"Enhanced vision extended ({new_turns} turns)" if current > 0 else f"Enhanced vision active ({turns_to_add} turns)"
            game.message_log.add_message(msg)

        elif effect_key == 'exploit_efficiency':
            from game_config import GameConfig
            turns_to_add = GameConfig.get('balance.exploit_efficiency_turns', 8)
            current = player.temporary_effects.get('exploit_efficiency_turns', 0)
            new_turns = max(current + turns_to_add, turns_to_add)
            player.temporary_effects['exploit_efficiency_turns'] = new_turns
            msg = f"Exploit efficiency extended ({new_turns} turns)" if current > 0 else f"Exploit efficiency active ({turns_to_add} turns)"
            game.message_log.add_message(msg)
        
        return True


class ExploitItem(InventoryItem):
    """
    Exploit items that can be equipped with RAM cost constraints.

    Exploits are abilities that consume RAM when equipped (e.g., firewall breach,
    data corruption, stealth protocols). Players can equip up to max_equipped_exploits
    (default 5) as long as total RAM cost doesn't exceed ram_total.

    Attributes:
        exploit_key: Key into GameData.EXPLOITS for stats and behavior
        ram_cost: RAM consumed when equipped (cached from exploit_def)
    """

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
    """
    Manages player inventory, item operations, and exploit equipping.

    Responsibilities:
    - Item storage (list of InventoryItem instances)
    - Stack management for code hacks (same color stacks together)
    - Exploit equipping with RAM/slot validation
    - RAM usage calculation from equipped exploits
    - Item queries by type and display ordering

    Key constraints:
    - Max 5 equipped exploits (configurable)
    - Total RAM usage cannot exceed player.ram_total
    - Code hacks of same color automatically stack

    Delegation:
    - Items handle their own use() logic
    - GameData.EXPLOITS provides exploit stats
    """

    def __init__(self, player):
        self.player = player
        self.items: List[InventoryItem] = []
        # Start with one random exploit
        all_exploits = list(GameData.EXPLOITS.keys())
        self.equipped_exploits: List[str] = [random.choice(all_exploits)]
        self.max_equipped_exploits = 5
    
    def add_item(self, item: InventoryItem) -> bool:
        """
        Add item to inventory with automatic stacking for code hacks.

        Code hacks of the same color automatically stack together (quantity
        is incremented on existing stack). Other item types are added as
        separate entries.

        Args:
            item: InventoryItem to add (CodeHack, ExploitItem, etc.)

        Returns:
            True if successfully added
        """
        if isinstance(item, CodeHack):
            # Look for existing code of the same color
            for existing_item in self.items:
                if (isinstance(existing_item, CodeHack) and
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
        if item_type == "code_hack":
            items.sort(key=lambda x: x.name.lower())
        return items
    
    def get_display_items(self) -> List[InventoryItem]:
        """Get all items in display order (codes first, then exploits)."""
        display_items = []
        # Add codes first (sorted alphabetically)
        display_items.extend(self.get_items_by_type("code_hack"))
        # Add other items (exploits, etc.)
        display_items.extend(self.get_items_by_type("exploit"))
        # Add any other item types
        display_items.extend([item for item in self.items if item.item_type not in ["code_hack", "exploit"]])
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

        # Track metrics
        from game_metrics import track
        track("exploits_equipped", category=exploit_item.exploit_key)

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

        # Track metrics
        from game_metrics import track
        track("exploits_unequipped", category=exploit_key)

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