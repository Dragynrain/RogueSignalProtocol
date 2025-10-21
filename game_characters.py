#!/usr/bin/env python3
"""
Player and Enemy character classes with AI behavior and movement systems.

This module handles all character logic including:
- Player stats (CPU, heat, RAM), abilities, and inventory management
- Enemy AI states (UNAWARE -> ALERT -> HOSTILE) and vision
- Movement queue system (FIFO 3-move rolling queue for all enemies)
- Pathfinding using TCOD's A* algorithm with enemy collision avoidance
- Status effects, damage calculation, and attack logic
"""

import logging
import random
import tcod
import numpy as np
from typing import List, Tuple, Optional
from game_entities import Position, Colors, EnemyState, EnemyMovement, PositionValidator
from game_config import GameConfig, GameBalance


class PathfindingHelper:
    """
    Centralized pathfinding using TCOD A*.
    Single implementation used for all queue operations.
    """

    @staticmethod
    def calculate_path(
        start: Position,
        goal: Position,
        game_map,
        game_engine,
        moving_enemy,
        max_length_multiplier: float = 3.0
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Calculate path from start to goal.

        Args:
            start: Starting position
            goal: Goal position
            game_map: GameMap for walkability
            game_engine: GameEngine for enemy positions
            moving_enemy: Enemy doing pathfinding (exclude from collision)
            max_length_multiplier: Max path length as multiple of direct distance

        Returns:
            List of (y, x) tuples (TCOD format), or None if no reasonable path
        """
        # Calculate reasonable path length
        direct_distance = start.distance_to(goal)
        if direct_distance <= 5:
            max_length = max(15, int(direct_distance * 5))
        else:
            max_length = max(15, int(direct_distance * max_length_multiplier))

        try:
            # Create cost map with enemy collision
            cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

            # TCOD pathfinding
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))

            # Validate path (TCOD returns numpy array)
            if len(path) > 1 and len(path) <= max_length:
                return path
            return None

        except Exception as e:
            logging.warning(f"Pathfinding failed from {start} to {goal}: {e}")
            return None

    @staticmethod
    def _create_cost_map(game_map, game_engine, moving_enemy):
        """Create cost map with enemy collision avoidance."""
        cost_map = game_map.get_walkability_map().copy()

        # Mark other enemies as impassable
        for enemy in game_engine.enemies:
            if enemy.id != moving_enemy.id:
                x, y = enemy.x, enemy.y
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    cost_map[y, x] = 0  # TCOD uses [y, x] indexing

        return cost_map


class Player:
    """
    Player character managing stats, position, abilities, and inventory.

    The Player class coordinates several systems:
    - Core stats (CPU health, heat, RAM capacity) with configurable maximums
    - Temporary status effects (invisibility, speed, vision enhancements, virus infection)
    - Vision system with shadow mechanics and enhanced vision upgrades
    - Inventory management (delegated to InventoryManager)
    - Permanent upgrades (RAM, CPU, heat capacity)

    Movement validation uses centralized PositionValidator to ensure consistency
    with enemy movement and other systems.
    """

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
        
        # Vision and abilities - load from config for easy balancing
        from game_config import GameConfig
        self.base_vision_range = GameConfig.get('gameplay.player_base_vision_range', 15)
        
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
        """
        Move player with boundary and collision checking.

        Uses centralized PositionValidator to ensure movement validation
        is consistent across player and enemy movement systems.

        Args:
            dx: Change in X coordinate (-1, 0, or 1)
            dy: Change in Y coordinate (-1, 0, or 1)
            game_map: GameMap instance for boundary/collision checking

        Returns:
            True if move was successful, False if blocked
        """
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
        """
        Check if player can see an enemy using vision range and shadow mechanics.

        Vision rules (checked in order):
        1. Adjacent enemies (distance <= 1.5) are always visible
        2. Enhanced vision ignores walls and sees within extended range
        3. Enemies in shadows are only visible when adjacent (shadows block incoming vision)
        4. Standard TCOD FOV check for line-of-sight within vision range

        Note: Shadows block vision TO targets in shadows, but do NOT block vision
        FROM the player if standing in a shadow. This creates tactical asymmetry.

        Args:
            enemy_target: Enemy to check visibility for
            game_map: GameMap instance for shadow/FOV checking

        Returns:
            True if player can see the enemy
        """
        distance = self.position.distance_to(enemy_target.position)

        # Adjacent enemies always visible
        if distance <= 1.5:
            return True

        # Enhanced vision sees through walls
        vision_range = self.get_vision_range()
        if self.can_see_through_walls():
            return distance <= vision_range

        # Enemies in shadows only visible when adjacent (shadows block vision coming IN)
        if game_map.is_shadow(enemy_target.position) and distance > 1:
            return False

        # Shadows do NOT block vision going OUT - player standing in shadow has normal vision
        # (Shadows only block vision coming in, not vision going out)

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
        """
        Apply a permanent stat upgrade with configurable caps.

        Each upgrade type has a maximum capacity to prevent unlimited scaling:
        - RAM: Capped at max_ram_capacity (default 32)
        - CPU: Capped at max_cpu_capacity (default 200), also boosts current CPU
        - Heat: Capped at 200 to balance heat-based abilities

        Args:
            upgrade_key: Key into GameUpgrades.UPGRADES dict

        Returns:
            True if upgrade was successfully applied, False if key not found
        """
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
    """
    Enemy character with state-based AI, pathfinding, and movement queue system.

    The Enemy class manages several interconnected systems:
    - AI state machine (UNAWARE -> ALERT -> HOSTILE) with vision checks
    - Movement queue system (FIFO 3-move rolling queue) for smooth pathfinding
    - TCOD A* pathfinding with enemy collision avoidance
    - Combat (melee attacks, status effects like virus/slow)
    - Special behaviors (virus mimicry, admin omniscience, patrol routes)

    Movement queue ensures enemies plan 3 moves ahead, providing smooth
    pathfinding that adapts when blocked. All enemies use the same queue
    system regardless of movement type (PATROL, RANDOM, SEEK, STATIC).

    Key delegation:
    - Type data loaded from GameData.ENEMY_TYPES (stats, vision, damage)
    - Pathfinding uses create_pathfinding_cost_map() helper
    - Position validation uses PositionValidator
    """

    _next_id = 1  # Class variable for unique IDs

    def __init__(self, position: Position, enemy_type: str):
        """
        Initialize enemy with type-specific stats and AI state.

        Args:
            position: Starting Position on the game map
            enemy_type: Key into GameData.ENEMY_TYPES (e.g., 'admin', 'virus', 'drone')

        Note:
            - Admin enemies start HOSTILE (can always see player)
            - Virus enemies store original_movement_type for mimicry behavior
            - Movement queue starts empty and is filled on first move
        """
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

        # Virus-specific: Store the original non-hostile movement type
        self.original_movement_type: Optional[EnemyMovement] = None

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

    def get_movement_type(self) -> EnemyMovement:
        """Get the effective movement type for this enemy.

        For virus enemies:
        - When HOSTILE: use SEEK movement (chase player)
        - When not HOSTILE (UNAWARE/ALERT): use their original mimicked movement type
        For all other enemies: returns type_data.movement
        """
        if self.type == 'virus':
            if self.state == EnemyState.HOSTILE:
                # Hostile viruses actively seek the player
                return EnemyMovement.SEEK
            elif self.original_movement_type is not None:
                # Non-hostile viruses use their mimicked movement type
                return self.original_movement_type
            # Fallback if original_movement_type wasn't set (shouldn't happen)
            return self.type_data.movement
        return self.type_data.movement

    def can_see_player(self, player: Player, game_map) -> bool:
        """
        Check if enemy can see player using layered vision rules.

        Vision checks are performed in order of efficiency:
        1. Disabled enemies cannot see anything
        2. Admin enemies always see player (omniscient)
        3. Range check using enemy's vision stat
        4. Invisibility check (data mimic blocks vision)
        5. Shadow check (players in shadows only visible when adjacent)
        6. TCOD FOV line-of-sight check

        Args:
            player: Player instance to check visibility for
            game_map: GameMap instance for shadow/FOV checking

        Returns:
            True if enemy can see player
        """
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

        # Final LOS check using TCOD FOV
        can_see = game_map.can_see_position(self.position, player.position, self.type_data.vision)
        return can_see
    
    def can_attack_player(self, player: Player) -> bool:
        """Check if enemy can attack player (adjacent including diagonally)."""
        # Can't attack if disabled
        if self.disabled_turns > 0:
            return False
            
        # Can't attack invisible players unless this is an admin
        if player.is_invisible() and self.type != 'admin':
            return False
            
        # Can't attack if no damage, unless it's a virus or inhibitor (which apply status effects)
        if self.type_data.damage <= 0 and self.type not in ('virus', 'inhibitor'):
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
        """
        Execute next move from FIFO queue, maintaining rolling 3-move queue.

        Movement queue flow:
        1. Check if at patrol waypoint (advance to next if reached)
        2. Skip if disabled/on cooldown
        3. Refresh queue if empty (calculate up to 3 moves ahead)
        4. Pop next position from front of queue (FIFO)
        5. Validate move (replan if blocked)
        6. Execute move
        7. For tracking enemies (admin/hostile): detect target changes, refresh if needed
        8. Replenish queue (add 1 move to back to maintain 3 moves)

        Why rolling queue?
        - Smooth pathfinding that shows 3 moves ahead for player prediction
        - Adapts to blockages by replanning when invalid
        - Efficient: only calculates new moves as needed

        Args:
            game_map: GameMap instance for pathfinding
            player: Player instance for target tracking
            game_engine: GameEngine instance for enemy collision checking

        Returns:
            True if move was executed, False if blocked/skipped
        """
        # Check patrol point advancement first
        movement_type = self.get_movement_type()
        if movement_type == EnemyMovement.PATROL and self.patrol_points and self.state != EnemyState.HOSTILE:
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
        elif movement_type == EnemyMovement.RANDOM:
            should_add_move = True
        elif current_target:
            should_add_move = True

        if should_add_move:
            self._add_next_move_to_queue(player, game_map, game_engine)

        # Handle patrol point advancement (non-hostile only)
        if movement_type == EnemyMovement.PATROL and self.patrol_points and self.state != EnemyState.HOSTILE:
            current_target = self.patrol_points[self.patrol_index]
            if self.position.distance_to(current_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                self.move_queue.clear()  # Will refresh on next turn

        # Reset cooldown
        if movement_type == EnemyMovement.STATIC:
            self.move_cooldown = 999
        else:
            self.move_cooldown = 0

        return True

    def _refresh_move_queue(self, player, game_map, game_engine):
        """
        Recalculate movement queue from scratch (up to 3 moves).

        Called when:
        - Queue is empty
        - Move is blocked and needs replanning
        - Target changes for tracking enemies (admin/hostile)
        - Patrol waypoint is reached

        Strategy:
        - Admin/hostile/patrol: Use TCOD A* pathfinding, add first 3 steps
        - Random movement: Generate 3 random valid moves
        - Validates adjacency between consecutive moves
        - Extends patrol queues to next waypoint if current route is short
        - Falls back to greedy movement if pathfinding fails
        """
        self.move_queue.clear()

        # Update tracking
        self._queue_state = self.state
        self._queue_target = self._get_current_target(player, game_map)

        # Static enemies don't move
        movement_type = self.get_movement_type()
        if movement_type == EnemyMovement.STATIC:
            return

        # Admin, hostile enemies, and patrol enemies use pathfinding
        if self.type == 'admin' or self.state == EnemyState.HOSTILE or movement_type == EnemyMovement.PATROL:
            path = self._calculate_path_to_target(self._queue_target, game_map, game_engine)

            # If pathfinding failed (blocked by enemies/walls), use greedy movement as fallback
            if (path is None or len(path) <= 1) and self._queue_target:
                fallback_move = self._calculate_greedy_move_toward_target(self._queue_target, game_map, game_engine)
                if fallback_move:
                    self.move_queue.append(fallback_move)
            elif path is not None and len(path) > 1:
                # Add positions to queue, validating adjacency between each step
                prev_pos = self.position  # Start from current position

                # Take up to 3 steps (skip current position at index 0)
                for i in range(1, min(len(path), 4)):
                    # TCOD path returns (y, x) tuples, convert to Position(x, y)
                    next_pos = Position(path[i][1], path[i][0])

                    # Ensure this position is adjacent to the previous position
                    if not prev_pos.is_adjacent_to(next_pos):
                        # Path has a gap - stop adding moves
                        break

                    self.move_queue.append(next_pos)
                    prev_pos = next_pos  # Update for next iteration

                    # Stop if adjacent to target (no need to add more moves)
                    if self._queue_target and next_pos.is_adjacent_to(self._queue_target):
                        break

                # For patrol enemies: if queue doesn't have 3 moves, try to extend toward next patrol point
                # This ensures short patrol routes still show movement predictions
                if (movement_type == EnemyMovement.PATROL and
                    self.state != EnemyState.HOSTILE and
                    self.patrol_points and
                    len(self.patrol_points) >= 2 and  # Only extend if there are multiple patrol points
                    len(self.move_queue) < 3):

                    try:
                        # Determine starting position for extension
                        if self.move_queue:
                            last_queued_pos = self.move_queue[-1]
                        else:
                            last_queued_pos = self.position

                        # Get next patrol point
                        next_patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                        next_patrol_target = self.patrol_points[next_patrol_index]

                        # Calculate path from last queued position to next patrol point
                        # TCOD pathfinding uses (y, x) coordinate order for numpy arrays
                        cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
                        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                        pathfinder = tcod.path.Pathfinder(graph)
                        pathfinder.add_root((last_queued_pos.y, last_queued_pos.x))
                        next_path = pathfinder.path_to((next_patrol_target.y, next_patrol_target.x))

                        # Add remaining moves to fill queue up to 3 total
                        if next_path is not None and len(next_path) > 1:
                            moves_to_add = 3 - len(self.move_queue)
                            for i in range(1, min(len(next_path), moves_to_add + 1)):
                                # TCOD path returns (y, x) tuples, convert to Position(x, y)
                                next_pos = Position(next_path[i][1], next_path[i][0])
                                if last_queued_pos.is_adjacent_to(next_pos):
                                    self.move_queue.append(next_pos)
                                    last_queued_pos = next_pos
                                else:
                                    break
                    except Exception as e:
                        logging.warning(f"Failed to extend patrol queue: {e}")
        # Random movement - add up to 3 random moves
        elif movement_type == EnemyMovement.RANDOM:
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

        # Random movement doesn't need a target (unless hostile or admin - they always pathfind)
        movement_type = self.get_movement_type()
        if movement_type == EnemyMovement.RANDOM and self.type != 'admin' and self.state != EnemyState.HOSTILE:
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
        if self.type == 'admin' or self.state == EnemyState.HOSTILE or movement_type == EnemyMovement.PATROL:
            try:
                # Check if path would be reasonable before adding to queue
                direct_distance = start_pos.distance_to(target)
                max_reasonable_path_length = max(6, int(direct_distance * 3))

                # TCOD pathfinding uses (y, x) coordinate order for numpy arrays
                cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
                graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((start_pos.y, start_pos.x))
                path = pathfinder.path_to((target.y, target.x))

                if len(path) > 1:
                    # Only add move if path length is reasonable
                    if len(path) <= max_reasonable_path_length:
                        # TCOD path returns (y, x) tuples, convert to Position(x, y)
                        next_pos = Position(path[1][1], path[1][0])

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

            # Set maximum reasonable path length - allow longer paths to route around obstacles
            # For short distances, be more generous to allow routing around other enemies
            if direct_distance <= 5:
                max_reasonable_path_length = max(15, int(direct_distance * 5))
            else:
                max_reasonable_path_length = max(15, int(direct_distance * 3))

            # TCOD pathfinding uses (y, x) coordinate order for numpy arrays
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.position.y, self.position.x))
            path = pathfinder.path_to((target.y, target.x))

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
            # TCOD pathfinding uses (y, x) coordinate order for numpy arrays
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.position.y, self.position.x))
            path = pathfinder.path_to((target.y, target.x))

            if len(path) > 1:
                # TCOD path returns (y, x) tuples, convert to Position(x, y)
                return Position(path[1][1], path[1][0])
        except Exception as e:
            logging.warning(f"Patrol pathfinding failed for {self.type_data.name}: {e}")

        return None

    def _calculate_greedy_move_toward_target(self, target: Position, game_map, game_engine) -> Optional[Position]:
        """
        Calculate best adjacent move toward target using greedy distance minimization.

        Used as fallback when pathfinding fails (e.g., blocked by other enemies).
        Tries all 8 adjacent directions and returns the valid position closest
        to the target. This ensures enemies can still make progress even when
        A* pathfinding cannot find a valid path.

        Args:
            target: Destination Position to move toward
            game_map: GameMap instance for wall checking
            game_engine: GameEngine instance for enemy collision checking

        Returns:
            Position closest to target that is valid, or None if no valid moves
        """
        if not target:
            return None

        best_move = None
        best_distance = float('inf')

        # Try all 8 adjacent directions
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

        for dx, dy in directions:
            next_pos = Position(self.position.x + dx, self.position.y + dy)

            # Check if move is valid (not blocked by walls)
            if not next_pos.is_valid(game_map.width, game_map.height):
                continue
            if game_map.is_wall(next_pos):
                continue

            # CRITICAL: Skip positions blocked by other enemies
            enemy_blocking = any(e.position.x == next_pos.x and e.position.y == next_pos.y
                               for e in game_engine.enemies if e.id != self.id)
            if enemy_blocking:
                continue

            # Calculate distance to target from this position
            distance = next_pos.distance_to(target)

            # Keep track of best VALID move (closest to target)
            if distance < best_distance:
                best_distance = distance
                best_move = next_pos

        return best_move

    def _calculate_random_move(self, game_map, player, game_engine) -> Optional[Position]:
        """Calculate a random valid adjacent move from the last queued position or current position."""
        # Calculate from the last position in queue (for rolling queue behavior)
        start_pos = self.move_queue[-1] if self.move_queue else self.position

        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            next_pos = Position(start_pos.x + dx, start_pos.y + dy)
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
        movement_type = self.get_movement_type()
        if movement_type == EnemyMovement.PATROL and self.patrol_points:
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
    """Create cost map for TCOD A* pathfinding with optimizations.

    Enemies are treated as impassable obstacles (like walls), forcing pathfinding
    to route around them or get as close as possible and wait.
    """
    # Start with base terrain map (cached in game_map)
    cost_map = game_map.get_walkability_map().copy()

    # Mark enemy positions as impassable (cost = 0)
    # Enemies block other enemies - pathfinding must route around them
    for enemy in game_engine.enemies:
        if enemy != moving_enemy:
            x, y = enemy.x, enemy.y
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                # Mark as impassable (0 cost means wall/blocked)
                # CRITICAL: TCOD uses [y, x] indexing for numpy arrays!
                cost_map[y, x] = 0

    return cost_map


