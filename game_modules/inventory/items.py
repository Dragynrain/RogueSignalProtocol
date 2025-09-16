"""
Inventory item classes for the game.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from ..core.data_structures import Position
from ..core.colors import Colors


class InventoryItem(ABC):
    """
    Abstract base class for all inventory items.
    
    Defines the interface that all items must implement.
    """
    
    def __init__(self, name: str):
        """
        Initialize inventory item.
        
        Args:
            name: Display name of the item
        """
        self.name = name
    
    @abstractmethod
    def get_display_symbol(self) -> str:
        """Get the symbol used to display this item on the map."""
        pass
    
    @abstractmethod
    def get_display_color(self) -> tuple[int, int, int]:
        """Get the color used to display this item on the map."""
        pass
    
    @abstractmethod
    def get_ram_cost(self) -> int:
        """Get the RAM cost of this item."""
        pass
    
    def get_description(self) -> str:
        """Get a description of this item."""
        return f"{self.name}"
    
    def __str__(self) -> str:
        """String representation."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"{self.__class__.__name__}(name='{self.name}')"


class DataPatch(InventoryItem):
    """
    Data patch item that provides various stat bonuses.
    
    Can boost CPU, reduce heat, or provide other temporary benefits.
    """
    
    def __init__(self, name: str, cpu_boost: int = 0, heat_reduction: int = 0, 
                 ram_cost: int = 1, description: str = ""):
        """
        Initialize data patch.
        
        Args:
            name: Display name
            cpu_boost: Amount of CPU this patch restores
            heat_reduction: Amount of heat this patch reduces
            ram_cost: RAM required to carry this patch
            description: Detailed description
        """
        super().__init__(name)
        self.cpu_boost = cpu_boost
        self.heat_reduction = heat_reduction
        self.ram_cost = ram_cost
        self.description = description or f"Restores {cpu_boost} CPU, reduces {heat_reduction} heat"
    
    def get_display_symbol(self) -> str:
        """Data patches are displayed as 'd'."""
        return 'd'
    
    def get_display_color(self) -> tuple[int, int, int]:
        """Data patches are displayed in cyan."""
        return Colors.NEON_BLUE
    
    def get_ram_cost(self) -> int:
        """Get RAM cost of this data patch."""
        return self.ram_cost
    
    def get_description(self) -> str:
        """Get detailed description."""
        return self.description
    
    def use(self, player) -> str:
        """
        Use this data patch on the player.
        
        Args:
            player: Player to apply effects to
            
        Returns:
            Description of what happened
        """
        effects = []
        
        if self.cpu_boost > 0:
            healed = player.heal(self.cpu_boost)
            if healed > 0:
                effects.append(f"restored {healed} CPU")
        
        if self.heat_reduction > 0:
            reduced = player.reduce_heat(self.heat_reduction)
            if reduced > 0:
                effects.append(f"reduced heat by {reduced}")
        
        if effects:
            return f"Data patch {', '.join(effects)}"
        else:
            return "Data patch had no effect"


class ExploitItem(InventoryItem):
    """
    Exploit item that can be used for various abilities.
    
    Contains references to exploit definitions and usage tracking.
    """
    
    def __init__(self, exploit_key: str, name: str, ram_cost: int = 2):
        """
        Initialize exploit item.
        
        Args:
            exploit_key: Key identifying the exploit type
            name: Display name
            ram_cost: RAM required to carry this exploit
        """
        super().__init__(name)
        self.exploit_key = exploit_key
        self.ram_cost = ram_cost
        self._exploit_data = None
    
    def get_display_symbol(self) -> str:
        """Exploits are displayed as 'e'."""
        return 'e'
    
    def get_display_color(self) -> tuple[int, int, int]:
        """Exploits are displayed in electric blue."""
        return Colors.ELECTRIC_BLUE
    
    def get_ram_cost(self) -> int:
        """Get RAM cost of this exploit."""
        return self.ram_cost
    
    def get_exploit_data(self):
        """Get the exploit definition data (lazy loaded)."""
        if self._exploit_data is None:
            try:
                from ..core.definitions import GameData
                self._exploit_data = GameData.EXPLOITS.get(self.exploit_key)
            except ImportError:
                pass
        return self._exploit_data
    
    def get_description(self) -> str:
        """Get detailed description of the exploit."""
        exploit_data = self.get_exploit_data()
        if exploit_data:
            return f"{exploit_data.name}: {exploit_data.description}"
        return f"Exploit: {self.name}"
    
    def get_heat_cost(self) -> int:
        """Get heat cost to use this exploit."""
        exploit_data = self.get_exploit_data()
        return exploit_data.heat if exploit_data else 0
    
    def get_range(self) -> int:
        """Get range of this exploit."""
        exploit_data = self.get_exploit_data()
        return exploit_data.range if exploit_data else 0
    
    def get_damage(self) -> int:
        """Get damage dealt by this exploit."""
        exploit_data = self.get_exploit_data()
        return exploit_data.damage if exploit_data else 0


class StoryFragment(InventoryItem):
    """
    Story fragment item that contains narrative content.
    
    These provide lore and story elements for the player to discover.
    """
    
    def __init__(self, title: str, content: str, ram_cost: int = 0):
        """
        Initialize story fragment.
        
        Args:
            title: Title/name of the fragment
            content: Story content text
            ram_cost: RAM required to carry (usually 0)
        """
        super().__init__(title)
        self.content = content
        self.ram_cost = ram_cost
        self.is_read = False
    
    def get_display_symbol(self) -> str:
        """Story fragments are displayed as 's'."""
        return 's'
    
    def get_display_color(self) -> tuple[int, int, int]:
        """Story fragments are displayed in purple."""
        return Colors.PURPLE
    
    def get_ram_cost(self) -> int:
        """Story fragments typically don't use RAM."""
        return self.ram_cost
    
    def get_description(self) -> str:
        """Get description of the story fragment."""
        status = "(read)" if self.is_read else "(unread)"
        return f"Story Fragment: {self.name} {status}"
    
    def read(self) -> str:
        """
        Read the story fragment.
        
        Returns:
            The story content
        """
        self.is_read = True
        return self.content
    
    def get_preview(self, max_length: int = 50) -> str:
        """
        Get a preview of the story content.
        
        Args:
            max_length: Maximum length of preview
            
        Returns:
            Truncated story content
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length - 3] + "..."


class UpgradeItem(InventoryItem):
    """
    Permanent upgrade item that enhances player capabilities.
    
    These are consumed when used and provide permanent stat boosts.
    """
    
    def __init__(self, upgrade_key: str, name: str):
        """
        Initialize upgrade item.
        
        Args:
            upgrade_key: Key identifying the upgrade type
            name: Display name
        """
        super().__init__(name)
        self.upgrade_key = upgrade_key
        self._upgrade_data = None
    
    def get_display_symbol(self) -> str:
        """Get symbol from upgrade definition."""
        upgrade_data = self.get_upgrade_data()
        return upgrade_data.symbol if upgrade_data else 'U'
    
    def get_display_color(self) -> tuple[int, int, int]:
        """Get color from upgrade definition."""
        upgrade_data = self.get_upgrade_data()
        return upgrade_data.color if upgrade_data else Colors.WARNING
    
    def get_ram_cost(self) -> int:
        """Upgrades don't use RAM in inventory."""
        return 0
    
    def get_upgrade_data(self):
        """Get the upgrade definition data (lazy loaded)."""
        if self._upgrade_data is None:
            try:
                from ..core.definitions import GameData
                self._upgrade_data = GameData.UPGRADES.get(self.upgrade_key)
            except ImportError:
                pass
        return self._upgrade_data
    
    def get_description(self) -> str:
        """Get detailed description of the upgrade."""
        upgrade_data = self.get_upgrade_data()
        if upgrade_data:
            return f"{upgrade_data.name}: +{upgrade_data.bonus_amount} {upgrade_data.stat_type}"
        return f"Permanent Upgrade: {self.name}"