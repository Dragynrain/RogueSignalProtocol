"""
Enemy entity class with AI behavior and movement patterns.
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

from ...core.data_structures import Position, EnemyState, EnemyMovement
from ...core.definitions import GameData
from ...core.colors import Colors
from ...core.exceptions import InvalidPositionError

if TYPE_CHECKING:
    from .player import Player
    from .game_map import GameMap


class EnemyConfig:
    """Configuration constants for enemy behavior."""
    ADJACENT_THRESHOLD = 1.5
    MAX_MOVEMENT_ATTEMPTS = 5
    PATROL_STUCK_THRESHOLD = 3
    DEFAULT_ALERT_DURATION = 10
    PATHFINDING_MAX_ATTEMPTS = 100


class Enemy:
    """
    Enemy character with AI behavior and movement patterns.
    
    Handles enemy state management, AI decision making, pathfinding,
    and interactions with the player and game world.
    """
    
    _next_id = 1  # Class variable for unique IDs
    
    def __init__(self, position: Position, enemy_type: str):
        """
        Initialize enemy at given position with specified type.
        
        Args:
            position: Starting position for the enemy
            enemy_type: Type key from GameData.ENEMY_TYPES
            
        Raises:
            KeyError: If enemy_type is not found in GameData.ENEMY_TYPES
        """
        if enemy_type not in GameData.ENEMY_TYPES:
            raise KeyError(f"Unknown enemy type: {enemy_type}")
            
        # Identity
        self.id = Enemy._next_id
        Enemy._next_id += 1
        
        # Position and type
        self.position = position
        self.type = enemy_type
        self.type_data = GameData.ENEMY_TYPES[enemy_type]
        
        # Stats from type definition
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu
        
        # AI state management
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0
        
        # Movement and pathfinding
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.patrol_stuck_counter = 0
        self.last_seen_player: Optional[Position] = None
        self.movement_queue: List[Position] = []
        self.last_queue_state: Optional[EnemyState] = None
        self.last_queue_target: Optional[Position] = None
        self.last_target: Optional[Position] = None
        self.original_patrol_index = 0
    
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
    
    def get_display_color(self) -> Tuple[int, int, int]:
        """
        Get the color for rendering this enemy based on current state.
        
        Returns:
            RGB color tuple for rendering
        """
        if self.disabled_turns > 0:
            return Colors.ELECTRIC_BLUE  # Disabled state
        elif self.state == EnemyState.UNAWARE:
            return Colors.GRAY  # Unaware/patrol state
        elif self.state == EnemyState.ALERT:
            return Colors.WARNING  # Alert state
        elif self.state == EnemyState.HUNT:
            return Colors.DANGER  # Hostile/hunting state
        else:
            return Colors.ENEMY  # Default enemy color
    
    def can_see_player(self, player: 'Player', game_map: 'GameMap') -> bool:
        """
        Check if enemy can see player based on vision mechanics.
        
        Args:
            player: Player to check visibility for
            game_map: Game map for line of sight calculations
            
        Returns:
            True if player is visible, False otherwise
        """
        # Disabled enemies can't see anything
        if self.disabled_turns > 0:
            return False
        
        # Admin avatars have perfect tracking abilities
        if self.type == 'admin':
            return True
        
        # Check basic vision range
        distance_to_player = self.position.distance_to(player.position)
        if distance_to_player > self.type_data.vision:
            return False

        # Check if player is invisible (stealth effects)
        if player.is_invisible():
            return False
        
        # Apply stealth mechanics with shadows
        is_player_in_shadow = game_map.is_shadow(player.position)
        
        # Player in shadow: only visible if enemy is directly adjacent
        if is_player_in_shadow and distance_to_player > EnemyConfig.ADJACENT_THRESHOLD:
            return False

        # Use line of sight calculation from game map
        return game_map.has_line_of_sight(self.position, player.position)
    
    def can_attack_player(self, player: 'Player') -> bool:
        """
        Check if enemy can attack player (must be adjacent).
        
        Args:
            player: Player to check attack possibility for
            
        Returns:
            True if attack is possible, False otherwise
        """
        # Can't attack if disabled
        if self.disabled_turns > 0:
            return False
            
        # Can't attack invisible players (except admin avatars)
        if player.is_invisible() and self.type != 'admin':
            return False
            
        # Must be adjacent (including diagonally)
        distance = self.position.distance_to(player.position)
        is_adjacent = distance <= EnemyConfig.ADJACENT_THRESHOLD
        
        # Must have damage capability
        has_damage = self.type_data.damage > 0
        
        return is_adjacent and has_damage
    
    def take_damage(self, damage: int) -> int:
        """
        Take damage and return actual damage taken.
        
        Args:
            damage: Amount of damage to take
            
        Returns:
            Actual damage taken
        """
        actual_damage = min(damage, self.cpu)
        self.cpu = max(0, self.cpu - actual_damage)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """
        Heal the enemy up to maximum CPU.
        
        Args:
            amount: Amount to heal
            
        Returns:
            Actual amount healed
        """
        old_cpu = self.cpu
        self.cpu = min(self.max_cpu, self.cpu + amount)
        return self.cpu - old_cpu
    
    def is_alive(self) -> bool:
        """Check if enemy is still alive (has CPU remaining)."""
        return self.cpu > 0
    
    def is_disabled(self) -> bool:
        """Check if enemy is currently disabled."""
        return self.disabled_turns > 0
    
    def disable(self, turns: int) -> None:
        """
        Disable enemy for specified number of turns.
        
        Args:
            turns: Number of turns to disable
        """
        self.disabled_turns = max(self.disabled_turns, turns)
        # Clear movement queue when disabled
        self.movement_queue.clear()
    
    def update_state(self) -> None:
        """Update enemy state counters each turn."""
        # Reduce disabled turns
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
        
        # Reduce alert timer
        if self.alert_timer > 0:
            self.alert_timer -= 1
            
        # Reduce movement cooldown
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
    
    def set_alert_state(self, duration: int = None) -> None:
        """
        Set enemy to alert state for specified duration.
        
        Args:
            duration: Alert duration in turns (uses default if None)
        """
        if duration is None:
            duration = EnemyConfig.DEFAULT_ALERT_DURATION
            
        self.state = EnemyState.ALERT
        self.alert_timer = duration
    
    def set_hunt_state(self, player_position: Position) -> None:
        """
        Set enemy to hunt state targeting player position.
        
        Args:
            player_position: Last known player position
        """
        self.state = EnemyState.HUNT
        self.last_seen_player = Position(player_position.x, player_position.y)
        self.alert_timer = EnemyConfig.DEFAULT_ALERT_DURATION
    
    def reset_to_patrol(self) -> None:
        """Reset enemy to patrol/unaware state."""
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.last_seen_player = None
        self.movement_queue.clear()
    
    def add_patrol_point(self, position: Position) -> None:
        """
        Add a patrol point for this enemy.
        
        Args:
            position: Position to add to patrol route
        """
        self.patrol_points.append(Position(position.x, position.y))
    
    def get_current_patrol_target(self) -> Optional[Position]:
        """
        Get the current patrol target position.
        
        Returns:
            Current patrol target or None if no patrol points
        """
        if not self.patrol_points:
            return None
        return self.patrol_points[self.patrol_index % len(self.patrol_points)]
    
    def advance_patrol(self) -> None:
        """Advance to the next patrol point."""
        if self.patrol_points:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            self.patrol_stuck_counter = 0
    
    def get_movement_type(self) -> EnemyMovement:
        """Get the movement type for this enemy."""
        return self.type_data.movement
    
    def get_damage(self) -> int:
        """Get the damage this enemy deals."""
        return self.type_data.damage
    
    def get_vision_range(self) -> int:
        """Get the vision range for this enemy."""
        return self.type_data.vision
    
    def get_symbol(self) -> str:
        """Get the display symbol for this enemy."""
        return self.type_data.symbol
    
    def get_name(self) -> str:
        """Get the display name for this enemy."""
        return self.type_data.name
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.get_name()}({self.id}) at {self.position} - {self.state.value}"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"Enemy(id={self.id}, type='{self.type}', "
                f"pos={self.position}, state={self.state.value}, "
                f"cpu={self.cpu}/{self.max_cpu})")