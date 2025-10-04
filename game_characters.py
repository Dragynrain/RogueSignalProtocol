#!/usr/bin/env python3
"""
Player and Enemy character classes.
Extracted from RogueSignalProtocol.py for better organization.
"""

import logging
import random
import tcod
import numpy as np
from typing import List, Tuple, Optional
from game_entities import Position, Colors, EnemyState, EnemyMovement, PositionValidator
from game_config import GameConfig, GameBalance


class Player:
    """Player character with stats, position, and abilities."""
    
    def __init__(self, x: int, y: int):
        """Initialize player character at the specified position.
        
        Args:
            x: Initial X coordinate on the game map
            y: Initial Y coordinate on the game map
        """
        # Position and movement
        self.position = Position(x, y)
        self.last_position = Position(x, y)
        
        # Core stats
        self.cpu = 100
        self.max_cpu = 100
        self.heat = 0
        self._max_heat = 100  # Initialize max heat capacity
        self.trace_level = 0.0  # Global trace level (float for fractional increments)
        self.ram_total = 8
        
        # Vision and abilities
        self.base_vision_range = 15
        
        # Temporary effects
        self.temporary_effects = {
            'data_mimic_turns': 0,
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'virus_turns': 0
        }
        self.speed_moves_remaining = 0
        
        # Inventory system - imported later to avoid circular imports
        # Delayed import to avoid circular dependency
        from game_inventory import InventoryManager
        self.inventory_manager = InventoryManager(self)
    
    @property
    def x(self) -> int:
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    @property
    def ram_used(self) -> int:
        return self.inventory_manager.get_ram_usage()
    
    def move(self, dx: int, dy: int, game_map) -> bool:
        """Move player with boundary and collision checking."""
        self.last_position = Position(self.x, self.y)
        
        # Calculate the intended destination (unclamped)
        intended_x = self.x + dx
        intended_y = self.y + dy
        
        # Create the position and validate it using centralized utilities
        new_position = Position(intended_x, intended_y)

        # Use centralized validation
        if PositionValidator.is_basic_valid_position(new_position, game_map):
            self.position = new_position
            return True

        # Log boundary violations for debugging
        if not PositionValidator.is_within_bounds(new_position, game_map.width, game_map.height):
            logging.warning(f"Movement out of bounds: intended=({intended_x}, {intended_y}), map_bounds=({game_map.width}, {game_map.height})")

        return False
    
    def update_effects(self) -> None:
        """Update temporary effects each turn."""
        for effect in self.temporary_effects:
            self.temporary_effects[effect] = max(0, self.temporary_effects[effect] - 1)
    
    def is_invisible(self) -> bool:
        """Check if player is effectively invisible."""
        return self.temporary_effects['data_mimic_turns'] > 0
    
    def get_vision_range(self) -> int:
        """Get current vision range including bonuses."""
        base_range = self.base_vision_range
        if self.temporary_effects['enhanced_vision_turns'] > 0:
            base_range += 2
        return base_range
    
    def can_see_through_walls(self) -> bool:
        """Check if player can see through walls."""
        return self.temporary_effects['enhanced_vision_turns'] > 0
    
    def can_see_enemy(self, enemy_target: 'Enemy', game_map) -> bool:
        """Check if player can see enemy."""
        distance = self.position.distance_to(enemy_target.position)

        # Adjacent enemies always visible
        if distance <= 1.5:
            return True

        # Enhanced vision sees through walls
        vision_range = self.get_vision_range()
        if self.can_see_through_walls():
            return distance <= vision_range

        # Enemies in shadows only visible when adjacent
        if game_map.is_shadow(enemy_target.position) and distance > 1:
            return False

        # Reduce vision when player is in shadow
        if game_map.is_shadow(self.position) and distance > 1:
            vision_range = max(1, vision_range // 3)

        return game_map.can_see_position(self.position, enemy_target.position, vision_range)
    
    @property
    def max_heat(self) -> int:
        """Get maximum heat capacity."""
        return getattr(self, '_max_heat', 100)  # Default 100 if not set
    
    @max_heat.setter  
    def max_heat(self, value: int):
        """Set maximum heat capacity."""
        self._max_heat = value
    
    def apply_permanent_upgrade(self, upgrade_key: str) -> bool:
        """Apply a permanent upgrade to the player."""
        # Delayed import to avoid circular dependency  
        from game_data import GameUpgrades
        
        if upgrade_key not in GameUpgrades.UPGRADES:
            return False
            
        upgrade = GameUpgrades.UPGRADES[upgrade_key]
        
        max_ram = GameConfig.get('gameplay.max_ram_capacity', 32)
        max_cpu = GameConfig.get('gameplay.max_cpu_capacity', 200)
        
        if upgrade.stat_type == 'ram':
            self.ram_total = min(max_ram, self.ram_total + upgrade.bonus_amount)
        elif upgrade.stat_type == 'cpu':
            self.max_cpu = min(max_cpu, self.max_cpu + upgrade.bonus_amount)
            self.cpu = min(self.max_cpu, self.cpu + upgrade.bonus_amount)  # Boost current as well but cap at max
        elif upgrade.stat_type == 'heat':
            self.max_heat = min(200, self.max_heat + upgrade.bonus_amount)  # Cap at 200
            
        return True
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.cpu)
        self.cpu -= actual_damage
        return actual_damage


class Enemy:
    """Enemy character with AI behavior."""
    
    _next_id = 1  # Class variable for unique IDs
    
    def __init__(self, position: Position, enemy_type: str):
        self.id = Enemy._next_id
        Enemy._next_id += 1
        
        self.position = position
        self.type = enemy_type
        
        # Load type data - imported here to avoid circular imports
        # Delayed import to avoid circular dependency
        from game_data import GameData
        self.type_data = GameData.ENEMY_TYPES[enemy_type]
        
        # Stats
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu
        
        # AI state
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0
        
        # Movement data
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Position] = None
        self.original_patrol_index = 0  # Store original patrol index when becoming hostile
    
    @property
    def x(self) -> int:
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get the color for rendering this enemy."""
        if self.disabled_turns > 0:
            return Colors.BLUE
        elif self.state == EnemyState.UNAWARE:
            return Colors.ENEMY_UNAWARE
        elif self.state == EnemyState.ALERT:
            return Colors.ENEMY_ALERT
        else:
            return Colors.ENEMY_HOSTILE
    
    def can_see_player(self, player: Player, game_map) -> bool:
        """Check if enemy can see player."""
        if self.disabled_turns > 0:
            return False

        # Admin always sees player
        if self.type == 'admin':
            return True

        # Check basic range
        distance = self.position.distance_to(player.position)
        if distance > self.type_data.vision:
            return False

        # Invisible players can't be seen
        if player.is_invisible():
            return False

        # Players in shadows only visible when adjacent
        if game_map.is_shadow(player.position) and distance > GameBalance.ADJACENT_DISTANCE_THRESHOLD:
            return False

        return game_map.can_see_position(self.position, player.position, self.type_data.vision)
    
    def can_attack_player(self, player: Player) -> bool:
        """Check if enemy can attack player (adjacent including diagonally)."""
        # Can't attack if disabled
        if self.disabled_turns > 0:
            return False
            
        # Can't attack invisible players unless this is an admin
        if player.is_invisible() and self.type != 'admin':
            return False
            
        # Can't attack if no damage, unless it's a virus (which applies status effects)
        if self.type_data.damage <= 0 and self.type != 'virus':
            return False
            
        dx = abs(self.position.x - player.position.x)
        dy = abs(self.position.y - player.position.y)
        # Adjacent in any direction (including diagonal)
        is_adjacent = dx <= 1 and dy <= 1 and (dx + dy) > 0
        return is_adjacent
    
    def attack_player(self, player: Player) -> int:
        """Attack the player and return damage dealt."""
        if self.type == 'virus':
            virus_turns = player.temporary_effects.get('virus_turns', 0) + 3
            player.temporary_effects['virus_turns'] = min(virus_turns, 10)
            return 0

        if self.type == 'inhibitor':
            player.speed_moves_remaining = 0
            current_speed = player.temporary_effects['speed_boost_turns']
            net_effect = current_speed - 1

            if net_effect >= 0:
                player.temporary_effects['speed_boost_turns'] = net_effect
            else:
                player.temporary_effects['speed_boost_turns'] = 0
                player.temporary_effects['movement_slowed_turns'] = -net_effect
            return 0

        return player.take_damage(self.type_data.damage)
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        # Admin avatar has 50% damage resistance
        if self.type == 'admin':
            damage = max(5, damage // 2)  # Minimum 5 damage to prevent immunity
        
        self.cpu -= damage
        return self.cpu <= 0
    
    def move(self, game_map, player: Player, game_engine=None) -> bool:
        """
        Calculate and execute next move based on current state."""
        # Skip movement if disabled or on cooldown
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False

        if self.move_cooldown > 0 and self.type != 'admin':
            self.move_cooldown -= 1
            return False

        # Calculate next move
        next_position = self._calculate_next_move(player, game_map, game_engine)

        if not next_position or not self._is_move_valid(next_position, game_map, player, game_engine):
            return False

        # Execute the move
        self.position = next_position

        # Handle patrol point advancement (only when unaware or alert, not hostile)
        if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points and self.state != EnemyState.HOSTILE:
            current_target = self.patrol_points[self.patrol_index]
            if self.position.distance_to(current_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)

        # Reset cooldown
        if self.type_data.movement == EnemyMovement.STATIC:
            self.move_cooldown = 999
        elif self.type == 'admin':
            self.move_cooldown = 0
        else:
            self.move_cooldown = 0

        return True
    
    def _calculate_next_move(self, player, game_map, game_engine) -> Optional[Position]:
        """Calculate the next move based on current state and movement type."""
        if self.type_data.movement == EnemyMovement.STATIC:
            return None

        # Hostile enemies pathfind toward player
        if self.state == EnemyState.HOSTILE:
            return self._calculate_hostile_move(player, game_map, game_engine)

        # Non-hostile enemies use their base movement type
        if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
            return self._calculate_patrol_move(game_map, game_engine)
        elif self.type_data.movement == EnemyMovement.RANDOM:
            return self._calculate_random_move(game_map, game_engine.player, game_engine)

        return None

    def _calculate_hostile_move(self, player, game_map, game_engine) -> Optional[Position]:
        """Calculate next move toward player using pathfinding."""
        target = self._get_current_target(player, game_map)

        if not target:
            # Hostile but no target - fall back to patrol or random
            if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
                return self._calculate_patrol_move(game_map, game_engine)
            return self._calculate_random_move(game_map, player, game_engine)

        # Stop if already adjacent
        if self.position.is_adjacent_to(target):
            return None

        # Use pathfinding to find next step
        try:
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.position.x, self.position.y))
            path = pathfinder.path_to((target.x, target.y))

            if len(path) > 1:
                return Position(path[1][0], path[1][1])
        except Exception as e:
            logging.warning(f"Pathfinding failed for {self.type_data.name}: {e}")

        # Pathfinding failed - try random
        return self._calculate_random_move(game_map, player, game_engine)

    def _calculate_patrol_move(self, game_map, game_engine) -> Optional[Position]:
        """Calculate next move toward current patrol point."""
        if not self.patrol_points:
            return None

        current_target = self.patrol_points[self.patrol_index]

        # If close to current patrol point, route toward next one
        if self.position.distance_to(current_target) <= 2.0:
            next_index = (self.patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[next_index]
        else:
            target = current_target

        # Use pathfinding to get next step
        try:
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.position.x, self.position.y))
            path = pathfinder.path_to((target.x, target.y))

            if len(path) > 1:
                return Position(path[1][0], path[1][1])
        except Exception as e:
            logging.warning(f"Patrol pathfinding failed for {self.type_data.name}: {e}")

        # Pathfinding failed - try random
        return self._calculate_random_move(game_map, game_engine.player, game_engine)

    def _calculate_random_move(self, game_map, player, game_engine) -> Optional[Position]:
        """Calculate a random valid adjacent move."""
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            next_pos = Position(self.position.x + dx, self.position.y + dy)
            if self._is_move_valid(next_pos, game_map, player, game_engine):
                return next_pos

        return None

    def _get_current_target(self, player, game_map):
        """Get the current target position for hostile enemies."""
        if self.state != EnemyState.HOSTILE:
            return None

        # Only HOSTILE enemies pathfind toward player (ALERT is just a 1-turn warning)
        # If we can see player, target their current position
        if self.can_see_player(player, game_map):
            self.last_seen_player = player.position
            return player.position

        # Otherwise target last known position
        return self.last_seen_player

    def _is_move_valid(self, position, game_map, player, game_engine) -> bool:
        """Check if a position is valid for movement."""
        # Basic position check
        if not game_map.is_valid_position(position):
            return False

        # Can't move to player position
        if position.x == player.x and position.y == player.y:
            return False

        # Can't move to position occupied by another enemy
        for other_enemy in game_engine.enemies:
            if other_enemy != self and other_enemy.x == position.x and other_enemy.y == position.y:
                return False

        return True

# Pathfinding helper functions
def create_pathfinding_cost_map(game_map, game_engine, moving_enemy):
    """Create cost map for TCOD A* pathfinding with optimizations."""
    # Start with base terrain map (cached in game_map)
    cost_map = game_map.get_walkability_map().copy()

    # Efficiently mark enemy positions as impassable
    enemy_positions = {(enemy.x, enemy.y) for enemy in game_engine.enemies if enemy != moving_enemy}
    for x, y in enemy_positions:
        if 0 <= x < game_map.width and 0 <= y < game_map.height:
            cost_map[x, y] = False

    return cost_map


def pathfind_and_move(enemy, target, game_map, player, game_engine):
    """Use TCOD A* pathfinding to move enemy one step toward target with caching."""
    try:
        # Use cached pathfinder if available
        if not hasattr(game_engine, '_pathfinder_cache'):
            game_engine._pathfinder_cache = {}

        # Create cache key based on enemy positions and target
        enemy_positions = tuple(sorted((e.x, e.y) for e in game_engine.enemies if e != enemy))
        cache_key = (enemy.x, enemy.y, target.x, target.y, enemy_positions)

        # Check cache first
        if cache_key in game_engine._pathfinder_cache:
            optimal_path = game_engine._pathfinder_cache[cache_key]
        else:
            # Calculate new path and cache it
            cost_map = create_pathfinding_cost_map(game_map, game_engine, enemy)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((enemy.x, enemy.y))
            optimal_path = pathfinder.path_to((target.x, target.y))

            # Cache the result (limit cache size to prevent memory issues)
            if len(game_engine._pathfinder_cache) > 100:
                game_engine._pathfinder_cache.clear()
            game_engine._pathfinder_cache[cache_key] = optimal_path

        # Take the next step along the path
        if len(optimal_path) >= 2:
            next_x, next_y = optimal_path[1]  # Skip current position [0]
            next_position = Position(next_x, next_y)

            if can_move_to_position(enemy, next_position, game_map, player, game_engine):
                enemy.position = next_position
                return True

        return False
    except Exception:
        return False


def can_move_to_position(enemy, destination, game_map, player, game_engine):
    """Check if enemy can move to the specified position."""
    # Basic position validation
    if not game_map.is_valid_position(destination):
        return False
    
    # Can't move to player position
    if destination.x == player.x and destination.y == player.y:
        return False
    
    # Can't move to a position occupied by another enemy
    for other_enemy in game_engine.enemies:
        if other_enemy != enemy and other_enemy.x == destination.x and other_enemy.y == destination.y:
            return False
    
    return True