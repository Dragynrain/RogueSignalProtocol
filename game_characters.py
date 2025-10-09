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
        from game_data import GameData
        self.type_data = GameData.ENEMY_TYPES[enemy_type]

        # Stats
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu

        # AI state - admin starts hostile since it can always see player
        self.state = EnemyState.HOSTILE if enemy_type == 'admin' else EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0

        # Movement data
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Position] = None
        self.original_patrol_index = 0  # Store original patrol index when becoming hostile

        # Movement queue system - stores next 3 planned moves
        self.move_queue: List[Position] = []
        self._queue_target: Optional[Position] = None  # Target when queue was calculated
        self._queue_state: EnemyState = self.state  # State when queue was calculated
    
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
    
    def move(self, game_map, player: Player, game_engine) -> bool:
        """Execute next move from queue, maintaining rolling 3-move queue."""
        # Check patrol point advancement first
        if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points and self.state != EnemyState.HOSTILE:
            current_patrol_target = self.patrol_points[self.patrol_index]
            if self.position.distance_to(current_patrol_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                self.move_queue.clear()  # Triggers refresh below

        # Skip movement if disabled or on cooldown
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False

        if self.move_cooldown > 0 and self.type != 'admin':
            self.move_cooldown -= 1
            return False

        # Refresh queue if empty
        if not self.move_queue:
            self._refresh_move_queue(player, game_map, game_engine)

        # No moves available
        if not self.move_queue:
            return False

        # Pop and validate next move
        next_position = self.move_queue.pop(0)
        if not self._is_move_valid(next_position, game_map, player, game_engine):
            # Move blocked - clear queue and refresh
            self.move_queue.clear()
            self._refresh_move_queue(player, game_map, game_engine)
            # Try again with fresh queue
            if not self.move_queue:
                return False
            next_position = self.move_queue.pop(0)
            if not self._is_move_valid(next_position, game_map, player, game_engine):
                self.move_queue.clear()
                return False

        # Execute move
        self.position = next_position

        # Check if we need to refresh queue due to target change (for tracking enemies)
        if self.type == 'admin' or self.state == EnemyState.HOSTILE:
            current_target = self._get_current_target(player, game_map)
            # If target changed (player moved), refresh entire queue
            if current_target != self._queue_target:
                self.move_queue.clear()
                self._refresh_move_queue(player, game_map, game_engine)
                return True  # Move successful, queue refreshed

        # Replenish queue (rolling queue - add one move to maintain 3 moves)
        current_target = self._get_current_target(player, game_map)
        should_add_move = False

        if self.type == 'admin' or self.state == EnemyState.HOSTILE:
            should_add_move = current_target and not self.position.is_adjacent_to(player.position)
        elif self.type_data.movement == EnemyMovement.RANDOM:
            should_add_move = True
        elif current_target:
            should_add_move = True

        if should_add_move:
            self._add_next_move_to_queue(player, game_map, game_engine)

        # Handle patrol point advancement (non-hostile only)
        if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points and self.state != EnemyState.HOSTILE:
            current_target = self.patrol_points[self.patrol_index]
            if self.position.distance_to(current_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                self.move_queue.clear()  # Will refresh on next turn

        # Reset cooldown
        if self.type_data.movement == EnemyMovement.STATIC:
            self.move_cooldown = 999
        else:
            self.move_cooldown = 0

        return True

    def _refresh_move_queue(self, player, game_map, game_engine):
        """Recalculate movement queue (up to 3 moves)."""
        self.move_queue.clear()

        # Update tracking
        self._queue_state = self.state
        self._queue_target = self._get_current_target(player, game_map)

        # Static enemies don't move
        if self.type_data.movement == EnemyMovement.STATIC:
            return

        # Admin, hostile enemies, and patrol enemies use pathfinding
        if self.type == 'admin' or self.state == EnemyState.HOSTILE or self.type_data.movement == EnemyMovement.PATROL:
            path = self._calculate_path_to_target(self._queue_target, game_map, game_engine)
            if path is not None and len(path) > 1:
                # Add positions to queue, validating adjacency between each step
                prev_pos = self.position  # Start from current position

                # Take up to 3 steps (skip current position at index 0)
                for i in range(1, min(len(path), 4)):
                    next_pos = Position(path[i][0], path[i][1])

                    # Ensure this position is adjacent to the previous position
                    if not prev_pos.is_adjacent_to(next_pos):
                        # Path has a gap - stop adding moves
                        break

                    self.move_queue.append(next_pos)
                    prev_pos = next_pos  # Update for next iteration

                    # Stop if adjacent to target (no need to add more moves)
                    if self._queue_target and next_pos.is_adjacent_to(self._queue_target):
                        break

                # For patrol enemies: if queue reaches the target and there's room for more moves,
                # add moves toward the next patrol point to maintain smooth movement
                if (self.type_data.movement == EnemyMovement.PATROL and
                    self.state != EnemyState.HOSTILE and
                    self.patrol_points and
                    len(self.move_queue) < 3):
                    # Get next patrol point
                    next_patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                    next_patrol_target = self.patrol_points[next_patrol_index]

                    # If we're close to current target, start pathing to next
                    if self.move_queue:
                        last_queued_pos = self.move_queue[-1]
                        if last_queued_pos.distance_to(self._queue_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
                            # Calculate path from last queued position to next patrol point
                            try:
                                cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
                                graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                                pathfinder = tcod.path.Pathfinder(graph)
                                pathfinder.add_root((last_queued_pos.x, last_queued_pos.y))
                                next_path = pathfinder.path_to((next_patrol_target.x, next_patrol_target.y))

                                # Add remaining moves to fill queue
                                if next_path is not None and len(next_path) > 1:
                                    for i in range(1, min(len(next_path), 3 - len(self.move_queue) + 1)):
                                        next_pos = Position(next_path[i][0], next_path[i][1])
                                        if last_queued_pos.is_adjacent_to(next_pos):
                                            self.move_queue.append(next_pos)
                                            last_queued_pos = next_pos
                                        else:
                                            break
                            except Exception as e:
                                logging.warning(f"Failed to extend patrol queue: {e}")
        # Random movement - add up to 3 random moves
        elif self.type_data.movement == EnemyMovement.RANDOM:
            for i in range(3):
                next_move = self._calculate_random_move(game_map, player, game_engine)
                if next_move:
                    self.move_queue.append(next_move)
                else:
                    break

    def invalidate_move_queue(self):
        """Mark queue as invalid (called externally when state changes)."""
        self.move_queue.clear()

    def _add_next_move_to_queue(self, player, game_map, game_engine):
        """Add one move to the back of queue to maintain 3 moves (rolling queue)."""
        # Don't add more if already at 3
        if len(self.move_queue) >= 3:
            return

        # Random movement doesn't need a target
        if self.type_data.movement == EnemyMovement.RANDOM and self.type != 'admin':
            next_move = self._calculate_random_move(game_map, player, game_engine)
            if next_move:
                self.move_queue.append(next_move)
            return

        # Calculate from last position in queue
        start_pos = self.move_queue[-1] if self.move_queue else self.position
        target = self._get_current_target(player, game_map)

        if not target:
            return

        # Don't add more moves if queue already reaches adjacent to target
        if start_pos.is_adjacent_to(target):
            return

        # For pathfinding enemies (admin, hostile, or patrol), calculate next step along path
        if self.type == 'admin' or self.state == EnemyState.HOSTILE or self.type_data.movement == EnemyMovement.PATROL:
            try:
                # Check if path would be reasonable before adding to queue
                direct_distance = start_pos.distance_to(target)
                max_reasonable_path_length = max(6, int(direct_distance * 3))

                cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
                graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((start_pos.x, start_pos.y))
                path = pathfinder.path_to((target.x, target.y))

                if len(path) > 1:
                    # Only add move if path length is reasonable
                    if len(path) <= max_reasonable_path_length:
                        next_pos = Position(path[1][0], path[1][1])

                        # Validate adjacency before adding
                        if start_pos.is_adjacent_to(next_pos):
                            self.move_queue.append(next_pos)
                    else:
                        # Path too long - skip this move
                        pass
            except Exception as e:
                logging.warning(f"Failed to add move to queue for {self.type_data.name}: {e}")

    def _calculate_path_to_target(self, target: Optional[Position], game_map, game_engine):
        """Calculate full path to target using A* pathfinding with reasonable distance limits."""
        if not target:
            return None

        try:
            # Calculate direct distance to target
            direct_distance = self.position.distance_to(target)

            # Set maximum reasonable path length - if path is more than 3x direct distance,
            # enemy should stop rather than take long detours
            max_reasonable_path_length = max(6, int(direct_distance * 3))

            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.position.x, self.position.y))
            path = pathfinder.path_to((target.x, target.y))

            # Check if path exists and is reasonable
            if len(path) > 1:
                # If path is too long compared to direct distance, enemy should wait instead
                if len(path) > max_reasonable_path_length:
                    return None
                return path
            return None
        except Exception as e:
            logging.warning(f"Pathfinding failed for {self.type_data.name}: {e}")
            return None



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

        return None

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
        """Get the current target position based on enemy state and movement type."""
        # Admin always targets player (can always see them)
        if self.type == 'admin':
            self.last_seen_player = player.position
            return player.position

        # HOSTILE enemies target player
        if self.state == EnemyState.HOSTILE:
            if self.can_see_player(player, game_map):
                self.last_seen_player = player.position
                return player.position
            # Target last known position
            return self.last_seen_player

        # PATROL enemies target current patrol point
        if self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
            return self.patrol_points[self.patrol_index]

        # RANDOM enemies have no fixed target
        return None

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


