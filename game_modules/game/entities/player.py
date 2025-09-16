"""
Player entity class with stats, position, and abilities.
"""

from typing import TYPE_CHECKING, Dict

from ...core.data_structures import Position
from ...core.exceptions import InvalidPositionError

if TYPE_CHECKING:
    from .enemy import Enemy
    from .game_map import GameMap
    from ...inventory import InventoryManager


class PlayerConfig:
    """Configuration constants for player."""
    DEFAULT_CPU = 100
    DEFAULT_MAX_CPU = 100
    DEFAULT_HEAT = 0
    DEFAULT_MAX_HEAT = 100
    DEFAULT_DETECTION = 0
    DEFAULT_RAM_TOTAL = 8
    DEFAULT_VISION_RANGE = 15
    
    # Vision and mechanics
    ADJACENT_VISIBILITY_THRESHOLD = 1.5
    SHADOW_VISION_REDUCTION_FACTOR = 3
    
    # Stat caps
    MAX_RAM_CAPACITY = 32
    MAX_CPU_CAPACITY = 300
    MAX_HEAT_CAPACITY = 200


class Player:
    """
    Player character with stats, position, and abilities.
    
    Manages player state including position, stats, temporary effects,
    and interactions with the game world.
    """
    
    def __init__(self, x: int, y: int):
        """
        Initialize player at given position.
        
        Args:
            x: Initial x coordinate
            y: Initial y coordinate
        """
        # Position and movement
        self.position = Position(x, y)
        self.last_position = Position(x, y)
        
        # Core stats
        self.cpu = PlayerConfig.DEFAULT_CPU
        self.max_cpu = PlayerConfig.DEFAULT_MAX_CPU
        self.heat = PlayerConfig.DEFAULT_HEAT
        self._max_heat = PlayerConfig.DEFAULT_MAX_HEAT
        self.detection = PlayerConfig.DEFAULT_DETECTION
        self.ram_total = PlayerConfig.DEFAULT_RAM_TOTAL
        
        # Vision and abilities
        self.base_vision_range = PlayerConfig.DEFAULT_VISION_RANGE
        
        # Temporary effects tracking
        self.temporary_effects: Dict[str, int] = {
            'data_mimic_turns': 0,
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'virus_turns': 0,
            'ghost_node_turns': 0
        }
        self.speed_moves_remaining = 0
        
        # Inventory system (imported dynamically to avoid circular imports)
        self.inventory_manager = None
        self._initialize_inventory()
    
    def _initialize_inventory(self) -> None:
        """Initialize inventory manager (avoiding circular imports)."""
        try:
            from ...inventory import InventoryManager
            self.inventory_manager = InventoryManager(self)
        except ImportError:
            # Fallback for testing or when inventory system isn't available
            self.inventory_manager = None
    
    @property
    def x(self) -> int:
        """Get x coordinate."""
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        """Set x coordinate."""
        self.position.x = value
    
    @property
    def y(self) -> int:
        """Get y coordinate."""
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        """Set y coordinate."""
        self.position.y = value
    
    @property
    def ram_used(self) -> int:
        """Get current RAM usage from inventory."""
        if self.inventory_manager:
            return self.inventory_manager.get_ram_usage()
        return 0
    
    @property
    def max_heat(self) -> int:
        """Get maximum heat capacity."""
        return self._max_heat
    
    @max_heat.setter  
    def max_heat(self, value: int):
        """Set maximum heat capacity."""
        self._max_heat = max(0, min(PlayerConfig.MAX_HEAT_CAPACITY, value))
    
    def move(self, dx: int, dy: int, game_map: 'GameMap') -> bool:
        """
        Move player with boundary and collision checking.
        
        Args:
            dx: Change in x coordinate
            dy: Change in y coordinate
            game_map: Game map for collision checking
            
        Returns:
            True if move was successful, False otherwise
        """
        # Store last position for potential rollback
        self.last_position = Position(self.x, self.y)
        
        # Calculate new position with boundary constraints
        new_x = max(0, min(game_map.width - 1, self.x + dx))
        new_y = max(0, min(game_map.height - 1, self.y + dy))
        new_position = Position(new_x, new_y)
        
        # Check if position is valid (not a wall, etc.)
        if game_map.is_valid_position(new_position):
            self.position = new_position
            return True
        return False
    
    def update_effects(self) -> None:
        """Update temporary effects each turn."""
        for effect_name in self.temporary_effects:
            if self.temporary_effects[effect_name] > 0:
                self.temporary_effects[effect_name] -= 1
    
    def is_invisible(self) -> bool:
        """Check if player is effectively invisible to enemies."""
        return self.temporary_effects['data_mimic_turns'] > 0
    
    def get_vision_range(self) -> int:
        """Get current vision range including temporary bonuses."""
        base_range = self.base_vision_range
        if self.temporary_effects['enhanced_vision_turns'] > 0:
            base_range += 2
        return base_range
    
    def can_see_through_walls(self) -> bool:
        """Check if player can see through walls (enhanced vision effect)."""
        return self.temporary_effects['enhanced_vision_turns'] > 0
    
    def can_see_enemy(self, enemy: 'Enemy', game_map: 'GameMap') -> bool:
        """
        Check if player can see enemy using stealth and vision mechanics.
        
        Args:
            enemy: Enemy to check visibility for
            game_map: Game map for line of sight calculations
            
        Returns:
            True if enemy is visible, False otherwise
        """
        distance = self.position.distance_to(enemy.position)
        
        # Adjacent enemies should ALWAYS be visible (critical for gameplay)
        if distance <= PlayerConfig.ADJACENT_VISIBILITY_THRESHOLD:
            return True
        
        # Enhanced vision can see through walls
        if self.can_see_through_walls():
            return distance <= self.get_vision_range()
        
        # Check stealth mechanics
        player_in_shadow = game_map.is_shadow(self.position)
        enemy_in_shadow = game_map.is_shadow(enemy.position)
        
        # If enemy is in shadow, only visible if player is directly adjacent
        if enemy_in_shadow and distance > 1:
            return False
        
        # Calculate effective vision range considering shadows
        base_vision_range = self.get_vision_range()
        if player_in_shadow and distance > 1:
            # Reduce vision range when in shadows
            effective_vision_range = max(1, 
                base_vision_range // PlayerConfig.SHADOW_VISION_REDUCTION_FACTOR)
        else:
            effective_vision_range = base_vision_range
        
        # Use game map's line of sight calculation
        return game_map.can_see_position(self.position, enemy.position, effective_vision_range)
    
    def apply_permanent_upgrade(self, upgrade_key: str) -> bool:
        """
        Apply a permanent upgrade to the player.
        
        Args:
            upgrade_key: Key identifying the upgrade type
            
        Returns:
            True if upgrade was applied successfully, False otherwise
        """
        # Import here to avoid circular dependencies
        try:
            from ...core.definitions import GameData
            
            if upgrade_key not in GameData.UPGRADES:
                return False
                
            upgrade = GameData.UPGRADES[upgrade_key]
            
            if upgrade.stat_type == 'ram':
                self.ram_total = min(PlayerConfig.MAX_RAM_CAPACITY, 
                                   self.ram_total + upgrade.bonus_amount)
            elif upgrade.stat_type == 'cpu':
                self.max_cpu = min(PlayerConfig.MAX_CPU_CAPACITY, 
                                 self.max_cpu + upgrade.bonus_amount)
                # Boost current CPU as well but cap at max
                self.cpu = min(self.max_cpu, self.cpu + upgrade.bonus_amount)
            elif upgrade.stat_type == 'heat':
                self.max_heat = min(PlayerConfig.MAX_HEAT_CAPACITY, 
                                  self.max_heat + upgrade.bonus_amount)
                
            return True
            
        except ImportError:
            return False
    
    def take_damage(self, damage: int) -> int:
        """
        Take damage and return actual damage taken.
        
        Args:
            damage: Amount of damage to take
            
        Returns:
            Actual damage taken (may be less if CPU is lower than damage)
        """
        actual_damage = min(damage, self.cpu)
        self.cpu = max(0, self.cpu - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the player up to maximum CPU.
        
        Args:
            amount: Amount to heal
            
        Returns:
            Actual amount healed
        """
        old_cpu = self.cpu
        self.cpu = min(self.max_cpu, self.cpu + amount)
        return self.cpu - old_cpu
    
    def reduce_heat(self, amount: int) -> int:
        """
        Reduce player heat.
        
        Args:
            amount: Amount to reduce heat by
            
        Returns:
            Actual amount reduced
        """
        old_heat = self.heat
        self.heat = max(0, self.heat - amount)
        return old_heat - self.heat
    
    def add_heat(self, amount: int) -> int:
        """
        Add heat to the player.
        
        Args:
            amount: Amount of heat to add
            
        Returns:
            Actual amount added (may be capped by max heat)
        """
        old_heat = self.heat
        self.heat = min(self.max_heat, self.heat + amount)
        return self.heat - old_heat
    
    def is_overheated(self) -> bool:
        """Check if player is at maximum heat capacity."""
        return self.heat >= self.max_heat
    
    def is_alive(self) -> bool:
        """Check if player is still alive (has CPU remaining)."""
        return self.cpu > 0