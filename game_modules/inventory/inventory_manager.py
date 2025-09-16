"""
Inventory management system for the player.
"""

from typing import List, Dict, Optional, TYPE_CHECKING

from .items import InventoryItem, DataPatch, ExploitItem, StoryFragment
from ..core.exceptions import GameLogicError

if TYPE_CHECKING:
    from ..game.entities import Player


class InventoryConfig:
    """Configuration constants for inventory system."""
    MAX_ITEMS = 50  # Maximum total items
    CATEGORY_LIMITS = {
        'data_patches': 20,
        'exploits': 15,
        'story_fragments': 20
    }


class InventoryManager:
    """
    Manages player inventory including items, RAM usage, and organization.
    
    Provides methods for adding, removing, and organizing inventory items
    while respecting RAM constraints and item limits.
    """
    
    def __init__(self, player: 'Player'):
        """
        Initialize inventory manager.
        
        Args:
            player: Player that owns this inventory
        """
        self.player = player
        
        # Item collections
        self.data_patches: List[DataPatch] = []
        self.exploits: List[ExploitItem] = []
        self.story_fragments: List[StoryFragment] = []
        
        # Quick access maps
        self._exploit_map: Dict[str, ExploitItem] = {}
    
    def get_ram_usage(self) -> int:
        """
        Calculate total RAM usage of all items.
        
        Returns:
            Total RAM used by inventory items
        """
        total_ram = 0
        
        for patch in self.data_patches:
            total_ram += patch.get_ram_cost()
        
        for exploit in self.exploits:
            total_ram += exploit.get_ram_cost()
        
        for fragment in self.story_fragments:
            total_ram += fragment.get_ram_cost()
        
        return total_ram
    
    def get_available_ram(self) -> int:
        """
        Get remaining RAM capacity.
        
        Returns:
            Available RAM space
        """
        return max(0, self.player.ram_total - self.get_ram_usage())
    
    def can_add_item(self, item: InventoryItem) -> bool:
        """
        Check if an item can be added to inventory.
        
        Args:
            item: Item to check
            
        Returns:
            True if item can be added, False otherwise
        """
        # Check RAM capacity
        if item.get_ram_cost() > self.get_available_ram():
            return False
        
        # Check total item limit
        total_items = len(self.data_patches) + len(self.exploits) + len(self.story_fragments)
        if total_items >= InventoryConfig.MAX_ITEMS:
            return False
        
        # Check category-specific limits
        if isinstance(item, DataPatch):
            return len(self.data_patches) < InventoryConfig.CATEGORY_LIMITS['data_patches']
        elif isinstance(item, ExploitItem):
            return len(self.exploits) < InventoryConfig.CATEGORY_LIMITS['exploits']
        elif isinstance(item, StoryFragment):
            return len(self.story_fragments) < InventoryConfig.CATEGORY_LIMITS['story_fragments']
        
        return True
    
    def add_item(self, item: InventoryItem) -> bool:
        """
        Add an item to the inventory.
        
        Args:
            item: Item to add
            
        Returns:
            True if successfully added, False otherwise
            
        Raises:
            GameLogicError: If item type is not supported
        """
        if not self.can_add_item(item):
            return False
        
        try:
            if isinstance(item, DataPatch):
                self.data_patches.append(item)
            elif isinstance(item, ExploitItem):
                self.exploits.append(item)
                self._exploit_map[item.exploit_key] = item
            elif isinstance(item, StoryFragment):
                self.story_fragments.append(item)
            else:
                raise GameLogicError(f"Unsupported item type: {type(item)}")
            
            return True
            
        except Exception as e:
            raise GameLogicError(f"Failed to add item to inventory: {e}")
    
    def remove_item(self, item: InventoryItem) -> bool:
        """
        Remove an item from the inventory.
        
        Args:
            item: Item to remove
            
        Returns:
            True if successfully removed, False if not found
        """
        try:
            if isinstance(item, DataPatch):
                if item in self.data_patches:
                    self.data_patches.remove(item)
                    return True
            elif isinstance(item, ExploitItem):
                if item in self.exploits:
                    self.exploits.remove(item)
                    self._exploit_map.pop(item.exploit_key, None)
                    return True
            elif isinstance(item, StoryFragment):
                if item in self.story_fragments:
                    self.story_fragments.remove(item)
                    return True
            
            return False
            
        except Exception:
            return False
    
    def use_data_patch(self, patch_index: int) -> Optional[str]:
        """
        Use a data patch by index.
        
        Args:
            patch_index: Index of patch to use
            
        Returns:
            Description of effect, or None if invalid index
        """
        if 0 <= patch_index < len(self.data_patches):
            patch = self.data_patches[patch_index]
            result = patch.use(self.player)
            self.remove_item(patch)
            return result
        return None
    
    def has_exploit(self, exploit_key: str) -> bool:
        """
        Check if player has a specific exploit.
        
        Args:
            exploit_key: Exploit identifier
            
        Returns:
            True if exploit is available
        """
        return exploit_key in self._exploit_map
    
    def get_exploit(self, exploit_key: str) -> Optional[ExploitItem]:
        """
        Get exploit item by key.
        
        Args:
            exploit_key: Exploit identifier
            
        Returns:
            ExploitItem if found, None otherwise
        """
        return self._exploit_map.get(exploit_key)
    
    def get_all_items(self) -> List[InventoryItem]:
        """Get all items in inventory as a single list."""
        all_items = []
        all_items.extend(self.data_patches)
        all_items.extend(self.exploits)
        all_items.extend(self.story_fragments)
        return all_items
    
    def get_item_counts(self) -> Dict[str, int]:
        """
        Get count of items by category.
        
        Returns:
            Dictionary with category counts
        """
        return {
            'data_patches': len(self.data_patches),
            'exploits': len(self.exploits),
            'story_fragments': len(self.story_fragments),
            'total': len(self.get_all_items())
        }
    
    def organize_by_type(self) -> Dict[str, List[InventoryItem]]:
        """
        Organize items by type for display.
        
        Returns:
            Dictionary with items organized by type
        """
        return {
            'Data Patches': list(self.data_patches),
            'Exploits': list(self.exploits),
            'Story Fragments': list(self.story_fragments)
        }
    
    def sort_data_patches(self, key_func=None) -> None:
        """
        Sort data patches in inventory.
        
        Args:
            key_func: Function to determine sort order (default: by name)
        """
        if key_func is None:
            key_func = lambda patch: patch.name
        self.data_patches.sort(key=key_func)
    
    def sort_exploits(self, key_func=None) -> None:
        """
        Sort exploits in inventory.
        
        Args:
            key_func: Function to determine sort order (default: by name)
        """
        if key_func is None:
            key_func = lambda exploit: exploit.name
        self.exploits.sort(key=key_func)
    
    def clear_all(self) -> None:
        """Clear all items from inventory."""
        self.data_patches.clear()
        self.exploits.clear()
        self.story_fragments.clear()
        self._exploit_map.clear()
    
    def get_ram_breakdown(self) -> Dict[str, int]:
        """
        Get RAM usage breakdown by category.
        
        Returns:
            Dictionary with RAM usage by category
        """
        breakdown = {
            'data_patches': sum(patch.get_ram_cost() for patch in self.data_patches),
            'exploits': sum(exploit.get_ram_cost() for exploit in self.exploits),
            'story_fragments': sum(fragment.get_ram_cost() for fragment in self.story_fragments)
        }
        breakdown['total'] = sum(breakdown.values())
        return breakdown
    
    def find_items_by_name(self, name: str) -> List[InventoryItem]:
        """
        Find items by partial name match.
        
        Args:
            name: Name to search for (case-insensitive)
            
        Returns:
            List of matching items
        """
        name_lower = name.lower()
        matches = []
        
        for item in self.get_all_items():
            if name_lower in item.name.lower():
                matches.append(item)
        
        return matches
    
    def __str__(self) -> str:
        """String representation for debugging."""
        counts = self.get_item_counts()
        ram_info = f"{self.get_ram_usage()}/{self.player.ram_total}"
        return f"Inventory({counts['total']} items, {ram_info} RAM)"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"InventoryManager(patches={len(self.data_patches)}, "
                f"exploits={len(self.exploits)}, "
                f"fragments={len(self.story_fragments)})")