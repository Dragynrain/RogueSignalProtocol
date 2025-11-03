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
    Centralized pathfinding using TCOD A* and Dijkstra maps.

    Single source of truth for all enemy pathfinding operations.
    Used by the movement queue system to calculate paths to targets.

    This helper ensures consistent pathfinding behavior across all enemies
    and movement types (PATROL, SEEK, HOSTILE). Includes enemy collision
    avoidance and reasonable path length validation.

    NEW: Dijkstra map support for advanced AI behaviors:
    - Flee: Move away from dangerous positions
    - Coordinate: Position relative to other enemies
    - Ambush: Find optimal attack positions
    """

    # Pathfinding constants
    SHORT_DISTANCE_THRESHOLD = 5  # Distance considered "short" for pathfinding
    MIN_PATH_LENGTH = 15  # Minimum reasonable path length
    SHORT_DISTANCE_MULTIPLIER = 5  # Path length multiplier for short distances

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
        if direct_distance <= PathfindingHelper.SHORT_DISTANCE_THRESHOLD:
            max_length = max(
                PathfindingHelper.MIN_PATH_LENGTH,
                int(direct_distance * PathfindingHelper.SHORT_DISTANCE_MULTIPLIER)
            )
        else:
            max_length = max(
                PathfindingHelper.MIN_PATH_LENGTH,
                int(direct_distance * max_length_multiplier)
            )

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
                logging.debug(f"Pathfinding: ({start.x},{start.y}) -> ({goal.x},{goal.y}), path_length={len(path)}, max={max_length}")
                return path
            elif len(path) > max_length:
                logging.debug(f"Pathfinding: ({start.x},{start.y}) -> ({goal.x},{goal.y}), path too long: {len(path)} > {max_length}")
            else:
                logging.debug(f"Pathfinding: ({start.x},{start.y}) -> ({goal.x},{goal.y}), no path found")
            return None

        except Exception as e:
            logging.warning(f"Pathfinding failed from {start} to {goal}: {e}")
            return None

    @staticmethod
    def create_dijkstra_map(
        goals: List[Position],
        game_map,
        game_engine,
        moving_enemy,
        max_distance: int = 100
    ) -> np.ndarray:
        """
        Create a Dijkstra map showing distance to nearest goal from any position.

        A Dijkstra map is a 2D array where each cell contains the cost to reach
        the nearest goal. This enables advanced AI behaviors:
        - Chase: Move to cells with LOWER values (closer to goals)
        - Flee: Move to cells with HIGHER values (further from goals)
        - Coordinate: Multiple enemies can use the same map

        Args:
            goals: List of goal positions (e.g., player position for chase,
                   enemy positions for flee)
            game_map: GameMap for walkability
            game_engine: GameEngine for enemy positions
            moving_enemy: Enemy using this map (for collision avoidance)
            max_distance: Maximum distance to compute (higher = more expensive)

        Returns:
            2D numpy array [y, x] with distance values (numpy.inf for unreachable)
        """
        # Create cost map with enemy collision
        cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

        # Create graph for pathfinding
        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        # Add all goals as roots
        for goal in goals:
            pathfinder.add_root((goal.y, goal.x))  # TCOD uses (y, x)

        # Return the distance map
        # pathfinder.distance is a 2D array with distances from roots
        return pathfinder.distance

    @staticmethod
    def get_flee_move(
        current_pos: Position,
        dijkstra_map: np.ndarray,
        game_map
    ) -> Optional[Tuple[int, int]]:
        """
        Get best move to FLEE from threats using Dijkstra map.

        Finds the adjacent cell with the HIGHEST distance value (furthest from threats).

        Args:
            current_pos: Current position of the fleeing enemy
            dijkstra_map: Dijkstra map with distances to threats
            game_map: GameMap for boundary checking

        Returns:
            Tuple (dx, dy) for the best flee direction, or None if no valid move
        """
        best_move = None
        best_distance = dijkstra_map[current_pos.y, current_pos.x]  # [y, x] indexing

        # Check all 8 adjacent cells
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
            new_pos = Position(current_pos.x + dx, current_pos.y + dy)

            # Validate position
            if not new_pos.is_valid(game_map.width, game_map.height):
                continue
            if game_map.is_wall(new_pos):
                continue

            # Get distance at this position
            distance = dijkstra_map[new_pos.y, new_pos.x]

            # We want HIGHER distance (flee) - skip unreachable cells
            if distance == np.inf:
                continue

            if distance > best_distance:
                best_distance = distance
                best_move = (dx, dy)

        return best_move

    @staticmethod
    def get_chase_move(
        current_pos: Position,
        dijkstra_map: np.ndarray,
        game_map
    ) -> Optional[Tuple[int, int]]:
        """
        Get best move to CHASE target using Dijkstra map.

        Finds the adjacent cell with the LOWEST distance value (closest to target).

        Args:
            current_pos: Current position of the chasing enemy
            dijkstra_map: Dijkstra map with distances to target
            game_map: GameMap for boundary checking

        Returns:
            Tuple (dx, dy) for the best chase direction, or None if no valid move
        """
        best_move = None
        best_distance = dijkstra_map[current_pos.y, current_pos.x]  # [y, x] indexing

        # Check all 8 adjacent cells
        for dx, dy in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
            new_pos = Position(current_pos.x + dx, current_pos.y + dy)

            # Validate position
            if not new_pos.is_valid(game_map.width, game_map.height):
                continue
            if game_map.is_wall(new_pos):
                continue

            # Get distance at this position
            distance = dijkstra_map[new_pos.y, new_pos.x]

            # We want LOWER distance (chase) - skip unreachable cells
            if distance == np.inf:
                continue

            if distance < best_distance:
                best_distance = distance
                best_move = (dx, dy)

        return best_move

    @staticmethod
    def path_exists(
        start: Position,
        goal: Position,
        cost_map: np.ndarray
    ) -> bool:
        """
        Check if a valid path exists between two points.

        Simpler than calculate_path - just returns boolean, doesn't validate length
        or apply enemy collision. Useful for connectivity validation.

        Args:
            start: Starting position
            goal: Goal position
            cost_map: Pre-computed cost map (0 = impassable, >0 = passable with cost)

        Returns:
            True if any path exists, False otherwise
        """
        try:
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))
            return len(path) >= 2  # Path includes start and goal
        except Exception as e:
            logging.debug(f"path_exists check failed: {e}")
            return False

    @staticmethod
    def calculate_simple_path(
        start: Position,
        goal: Position,
        cost_map: np.ndarray
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Calculate path using a custom cost map without enemy collision.

        Used for special pathfinding cases like:
        - Level generation (ensuring spawn-to-gateway connectivity)
        - Autowalk (player pathfinding without enemy avoidance)
        - Patrol route generation

        Args:
            start: Starting position
            goal: Goal position
            cost_map: Pre-computed cost map (0 = impassable, >0 = passable with cost)

        Returns:
            List of (y, x) tuples (TCOD format), or None if no path exists
        """
        try:
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
            path = pathfinder.path_to((goal.y, goal.x))

            if len(path) >= 2:
                return path
            return None
        except Exception as e:
            logging.warning(f"calculate_simple_path failed from {start} to {goal}: {e}")
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
            'traffic_masquerade_turns': 0,
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
            logging.debug(f"Player: moved from ({self.last_position.x},{self.last_position.y}) to ({new_position.x},{new_position.y})")
            self.position = new_position
            return True

        # Log boundary violations for debugging
        if not PositionValidator.is_within_bounds(new_position, game_map.width, game_map.height):
            logging.warning(f"Player movement out of bounds: intended=({intended_x}, {intended_y}), map_bounds=({game_map.width}, {game_map.height})")
        else:
            logging.debug(f"Player movement blocked: intended=({intended_x}, {intended_y})")

        return False
    
    def update_effects(self) -> None:
        """Update temporary effects each turn."""
        for effect in self.temporary_effects:
            self.temporary_effects[effect] = max(0, self.temporary_effects[effect] - 1)
    
    def is_invisible(self) -> bool:
        """Check if player is effectively invisible."""
        return self.temporary_effects['traffic_masquerade_turns'] > 0
    
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
        # Use Euclidean for vision range (TCOD FOV uses Euclidean)
        distance = self.position.distance_to(enemy_target.position)

        # Adjacent enemies always visible (use grid distance for gameplay)
        if self.position.grid_distance_to(enemy_target.position) <= 1:
            return True

        # Enhanced vision sees through walls
        vision_range = self.get_vision_range()
        if self.can_see_through_walls():
            return distance <= vision_range

        # Enemies in shadows only visible when adjacent (use grid distance for gameplay)
        if game_map.is_blind_spot(enemy_target.position) and self.position.grid_distance_to(enemy_target.position) > 1:
            # Don't log this - it gets called every frame during rendering
            return False

        # Shadows do NOT block vision going OUT - player standing in shadow has normal vision
        # (Shadows only block vision coming in, not vision going out)

        can_see = game_map.can_see_position(self.position, enemy_target.position, vision_range)
        return can_see
    
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
            old_ram = self.ram_total
            self.ram_total = min(max_ram, self.ram_total + upgrade.bonus_amount)
            logging.debug(f"Player upgrade '{upgrade_key}': RAM {old_ram} -> {self.ram_total} (cap={max_ram})")
        elif upgrade.stat_type == 'cpu':
            old_max_cpu = self.max_cpu
            old_cpu = self.cpu
            self.max_cpu = min(max_cpu, self.max_cpu + upgrade.bonus_amount)
            self.cpu = min(self.max_cpu, self.cpu + upgrade.bonus_amount)  # Boost current as well but cap at max
            logging.debug(f"Player upgrade '{upgrade_key}': max_CPU {old_max_cpu} -> {self.max_cpu}, CPU {old_cpu} -> {self.cpu} (cap={max_cpu})")
        elif upgrade.stat_type == 'heat':
            old_max_heat = self.max_heat
            max_cap = GameConfig.get('balance.max_heat_capacity', 200)
            self.max_heat = min(max_cap, self.max_heat + upgrade.bonus_amount)
            logging.debug(f"Player upgrade '{upgrade_key}': max_heat {old_max_heat} -> {self.max_heat} (cap={max_cap})")

        return True
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.cpu)
        old_cpu = self.cpu
        self.cpu -= actual_damage
        logging.debug(f"Player: took {actual_damage} damage, CPU {old_cpu} -> {self.cpu}/{self.max_cpu}")

        # Track metrics
        from game_metrics import track
        track("damage_taken", amount=actual_damage)

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
    - Pathfinding uses PathfindingHelper for all pathfinding operations
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
        self.blinded_turns = 0  # Memory Leak blindness - can't see player

        # Movement data
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Position] = None
        self.original_patrol_index = 0  # Store original patrol index when becoming hostile

        # Virus-specific: Store the original non-hostile movement type
        self.original_movement_type: Optional[EnemyMovement] = None

        # Movement queue system - stores next 3 planned moves
        self.move_queue: List[Position] = []
    
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
        """
        Get the color for rendering this enemy (glyph mode).

        Color indicates both AI state and health:
        - Alert state: Yellow (unaware), Orange (alert), Red (hostile), Blue (disabled)
        - HP damage: Blends in red tint as HP decreases
        """
        # Get base color from state
        if self.disabled_turns > 0:
            base_color = Colors.BLUE
        elif self.state == EnemyState.UNAWARE:
            base_color = Colors.ENEMY_UNAWARE
        elif self.state == EnemyState.ALERT:
            base_color = Colors.ENEMY_ALERT
        else:
            base_color = Colors.ENEMY_HOSTILE

        # Safety check to prevent division by zero
        if self.max_cpu <= 0:
            return base_color  # Return base color if invalid max_cpu

        # Apply HP-based tinting (blend with red)
        hp_percent = self.cpu / self.max_cpu

        if hp_percent >= 1.0:
            # Full HP - no tint
            return base_color
        elif hp_percent >= 0.5:
            # 50-99% HP - slight red tint (75% base, 25% red)
            red_tint = (255, 100, 100)
            return tuple(
                int(base_color[i] * 0.75 + red_tint[i] * 0.25)
                for i in range(3)
            )
        else:
            # <50% HP - heavy red tint (50% base, 50% red)
            red_tint = (255, 80, 80)
            return tuple(
                int(base_color[i] * 0.5 + red_tint[i] * 0.5)
                for i in range(3)
            )

    def get_graphics_tint(self) -> Tuple[int, int, int]:
        """
        Get subtle damage tint for graphics mode sprites.

        Uses multiplicative blending (texture.color_mod), so tint values close to
        (255, 255, 255) preserve original sprite colors.

        Returns:
            RGB tint: (255, 255, 255) = no tint, (255, 200, 200) = slight red wash
        """
        # Safety check to prevent division by zero
        if self.max_cpu <= 0:
            return (255, 255, 255)  # No tint if invalid max_cpu

        hp_percent = self.cpu / self.max_cpu

        if hp_percent >= 1.0:
            # Full HP - no tint
            return (255, 255, 255)
        elif hp_percent >= 0.5:
            # 50-99% HP - very subtle red tint (preserves ~86% of green/blue)
            return (255, 220, 220)
        else:
            # <50% HP - stronger red tint (preserves ~70% of green/blue)
            return (255, 180, 180)


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

        # Check basic range (use Euclidean - TCOD FOV uses Euclidean internally)
        distance = self.position.distance_to(player.position)
        if distance > self.type_data.vision:
            return False

        # Invisible players can't be seen
        if player.is_invisible():
            return False

        # Players in shadows only visible when adjacent (use grid distance for gameplay)
        if game_map.is_blind_spot(player.position) and self.position.grid_distance_to(player.position) > 1:
            return False

        # Final LOS check using TCOD FOV
        return game_map.can_see_position(self.position, player.position, self.type_data.vision)
    
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
            virus_increment = GameConfig.get('balance.virus_increment_turns', 3)
            virus_max = GameConfig.get('gameplay.virus_max_duration', 10)
            virus_turns = player.temporary_effects.get('virus_turns', 0) + virus_increment
            player.temporary_effects['virus_turns'] = min(virus_turns, virus_max)
            logging.debug(f"Enemy {self.type}@({self.x},{self.y}): infected player, virus_turns={player.temporary_effects['virus_turns']}")
            return 0

        if self.type == 'inhibitor':
            player.speed_moves_remaining = 0
            current_speed = player.temporary_effects['speed_boost_turns']
            net_effect = current_speed - 1

            if net_effect >= 0:
                # Still have speed boost remaining - just reduce it
                player.temporary_effects['speed_boost_turns'] = net_effect
            else:
                # No speed boost - apply slowdown by extending duration (stacking with cap)
                player.temporary_effects['speed_boost_turns'] = 0
                current_slow = player.temporary_effects.get('movement_slowed_turns', 0)
                # Add slowdown and cap at 5 turns to prevent infinite stacking
                player.temporary_effects['movement_slowed_turns'] = min(current_slow + (-net_effect), 5)
            logging.debug(f"Enemy {self.type}@({self.x},{self.y}): inhibited player, slowed_turns={player.temporary_effects['movement_slowed_turns']}")
            return 0

        damage = player.take_damage(self.type_data.damage)
        logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): attacked player for {damage} damage, player_cpu={player.cpu}/{player.max_cpu}")
        return damage
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        # Admin avatar has damage resistance
        original_damage = damage
        if self.type == 'admin':
            resist_percent = self.type_data.damage_resistance_percent if hasattr(self.type_data, 'damage_resistance_percent') else 50
            resist_min = self.type_data.damage_resistance_min if hasattr(self.type_data, 'damage_resistance_min') else 5
            damage = max(resist_min, damage * (100 - resist_percent) // 100)
            logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): damage reduced by resistance: {original_damage} -> {damage}")

        old_cpu = self.cpu
        self.cpu -= damage
        is_dead = self.cpu <= 0
        logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): took {damage} damage, cpu {old_cpu} -> {self.cpu}, destroyed={is_dead}")
        return is_dead
    
    def move(self, game_map, player, game_engine) -> bool:
        """
        Execute next queued move, maintaining fixed 3-length queue.

        Simplified flow:
        1. Check patrol waypoint advancement
        2. Check disabilities/cooldowns
        3. Ensure queue has moves (fill if needed)
        4. Pop and validate next move
        5. Execute move
        6. Ensure queue stays full (top up to 3)

        Returns:
            True if moved successfully, False otherwise
        """
        # 1. Patrol waypoint advancement
        if self._should_advance_patrol_waypoint():
            self._advance_patrol_waypoint()
            self.move_queue.clear()  # New waypoint = new plan

        # 2. Disability check
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False

        if self.move_cooldown > 0 and self.type != 'admin':
            self.move_cooldown -= 1
            return False

        # 3. Blindness decrement (blind enemies still move, just can't see)
        if self.blinded_turns > 0:
            self.blinded_turns -= 1

        # 3. Ensure queue has moves
        if not self.move_queue:
            self._ensure_queue_full(game_map, player, game_engine)

        # No moves available
        if not self.move_queue:
            return False

        # 4. Pop next move
        next_position = self.move_queue.pop(0)

        # 5. Validate move
        if not self._is_move_valid(next_position, game_map, player, game_engine):
            # Blocked - clear queue and replan next turn
            logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): move to ({next_position.x},{next_position.y}) BLOCKED, clearing queue")
            self.move_queue.clear()
            return False

        # 6. Execute move
        self.position = next_position

        # 7. Top up queue to maintain 3 moves
        self._ensure_queue_full(game_map, player, game_engine)

        # 8. Update cooldown
        if self.get_movement_type() == EnemyMovement.STATIC:
            self.move_cooldown = GameConfig.get('balance.static_enemy_cooldown', 999)
        else:
            self.move_cooldown = 0

        return True

    def _should_advance_patrol_waypoint(self) -> bool:
        """
        Check if enemy reached current patrol waypoint.

        Only advances for PATROL movement type enemies who are not hostile.
        Uses adjacency threshold to determine if waypoint reached.

        Returns:
            True if should advance to next waypoint, False otherwise
        """
        if self.get_movement_type() != EnemyMovement.PATROL:
            return False
        if not self.patrol_points:
            return False
        if self.state == EnemyState.HOSTILE:
            return False  # Hostile patrol enemies chase player

        # Check if arrived at current patrol waypoint (use grid distance for gameplay)
        current_target = self.patrol_points[self.patrol_index]
        return self.position.grid_distance_to(current_target) <= 1

    def _advance_patrol_waypoint(self):
        """Advance to next patrol waypoint (wraps around)."""
        self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)

    def _ensure_queue_full(self, game_map, player, game_engine):
        """
        Ensure move queue has 3 moves (or as many as possible).

        This is the ONLY method that fills the queue. Called after each move
        to maintain a fixed 3-length queue for player predictability.

        The 3-length queue is a core gameplay mechanic that allows players
        to predict enemy positions up to 3 turns ahead and plan tactically.

        Queue Invalidation: Queue is cleared (invalidated) in only 2 cases:
        1. Enemy state changes (UNAWARE <-> ALERT <-> HOSTILE)
        2. Next queued move is blocked (wall, enemy, etc.)

        Strategy:
        - If queue already has 3 moves, do nothing
        - Otherwise, calculate path from last queued position (or current position)
        - Add moves until queue has 3 (or path exhausted)

        Args:
            game_map: GameMap for pathfinding
            player: Player for targeting
            game_engine: GameEngine for enemy collision avoidance
        """
        # Already full
        if len(self.move_queue) >= 3:
            return

        movement_type = self.get_movement_type()

        # Static enemies don't move
        if movement_type == EnemyMovement.STATIC:
            return

        # PRIORITY 1: Flee behavior for low-health enemies (unless Admin)
        if self._should_flee(player, game_map) and self.type != 'admin':
            logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): FLEEING (cpu={self.cpu}/{self.type_data.max_cpu})")
            self._fill_flee_moves(game_map, player, game_engine)
            return

        # Random movement - fill with random moves (but only if not hostile/admin)
        # Hostile and admin enemies always use pathfinding, regardless of base movement type
        if movement_type == EnemyMovement.RANDOM and self.type != 'admin' and self.state != EnemyState.HOSTILE:
            self._fill_random_moves(game_map, player, game_engine)
            return

        # Pathfinding-based movement (PATROL, SEEK, or HOSTILE/ADMIN override)
        target = self._get_current_target(player, game_map)
        if not target:
            return

        # Start pathfinding from last queued position (or current if empty)
        start_pos = self.move_queue[-1] if self.move_queue else self.position

        # Calculate path
        path = PathfindingHelper.calculate_path(
            start=start_pos,
            goal=target,
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=self
        )

        # Fill queue from path
        if path is not None and len(path) > 1:
            # Add moves until queue has 3
            for i in range(1, len(path)):
                if len(self.move_queue) >= 3:
                    break
                # TCOD returns (y, x), convert to Position(x, y)
                self.move_queue.append(Position(path[i][1], path[i][0]))

        # Pathfinding failed - try greedy fallback (add at least 1 move)
        elif target and len(self.move_queue) == 0:
            greedy_move = self._calculate_greedy_move_toward_target(target, game_map, game_engine)
            if greedy_move:
                self.move_queue.append(greedy_move)

        # PATROL special case: If queue still not full, extend with next waypoint(s)
        if movement_type == EnemyMovement.PATROL and self.patrol_points and len(self.move_queue) < 3:
            self._extend_patrol_queue(game_map, game_engine)

    def _fill_random_moves(self, game_map, player, game_engine):
        """
        Fill queue with random moves for RANDOM movement type enemies.

        Chains random moves from last queued position to maintain
        3-length queue predictability. Used only for enemies with
        RANDOM base movement type who are not hostile.

        Args:
            game_map: GameMap for move validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance
        """
        # Start from last queued position (or current if empty)
        start_pos = self.move_queue[-1] if self.move_queue else self.position

        # Add random moves until queue has 3
        while len(self.move_queue) < 3:
            next_move = self._calculate_random_move_from(start_pos, game_map, player, game_engine)
            if next_move:
                self.move_queue.append(next_move)
                start_pos = next_move  # Chain for next random move
            else:
                break  # No valid random moves

    def _calculate_random_move_from(self, from_pos: Position, game_map, player, game_engine) -> Optional[Position]:
        """
        Calculate a random valid move from given position.

        Tries all 8 directions in random order until valid move found.

        Args:
            from_pos: Position to move from
            game_map: GameMap for boundary validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance

        Returns:
            Valid random Position, or None if no valid moves
        """
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)

        for dx, dy in directions:
            next_pos = Position(from_pos.x + dx, from_pos.y + dy)
            if self._is_move_valid_from(next_pos, from_pos, game_map, player, game_engine):
                return next_pos
        return None

    def _is_move_valid_from(self, position: Position, from_position: Position, game_map, player, game_engine) -> bool:
        """
        Check if move from from_position to position is valid.

        Validates: boundaries, player collision, enemy collision.

        Args:
            position: Target position
            from_position: Current position (unused but kept for consistency)
            game_map: GameMap for boundary validation
            player: Player to avoid colliding with
            game_engine: GameEngine for enemy collision avoidance

        Returns:
            True if move is valid, False otherwise
        """
        # Use centralized PositionValidator for consistency
        return PositionValidator.is_valid_for_enemy_movement(
            position, game_map, game_engine.enemies, player.position, self
        )

    def _extend_patrol_queue(self, game_map, game_engine):
        """
        Extend patrol queue with next waypoint(s) to reach 3 moves.

        When close to current waypoint, this chains pathfinding to subsequent
        waypoints to maintain the 3-move prediction guarantee.

        Args:
            game_map: GameMap for pathfinding
            game_engine: GameEngine for enemy collision avoidance
        """
        attempts = 0
        max_attempts = len(self.patrol_points)  # Avoid infinite loops

        while len(self.move_queue) < 3 and attempts < max_attempts:
            attempts += 1

            # Calculate next waypoint index (wraps around)
            next_index = (self.patrol_index + attempts) % len(self.patrol_points)
            next_waypoint = self.patrol_points[next_index]

            # Start from last queued position
            start_pos = self.move_queue[-1] if self.move_queue else self.position

            # Skip if already at/very close to this waypoint (use grid distance for gameplay)
            if start_pos.grid_distance_to(next_waypoint) <= 1:
                continue

            # Calculate path to next waypoint
            path = PathfindingHelper.calculate_path(
                start=start_pos,
                goal=next_waypoint,
                game_map=game_map,
                game_engine=game_engine,
                moving_enemy=self
            )

            # Add moves from path
            if path is not None and len(path) > 1:
                for i in range(1, len(path)):
                    if len(self.move_queue) >= 3:
                        return  # Queue full, done
                    self.move_queue.append(Position(path[i][1], path[i][0]))
            else:
                # Can't pathfind to next waypoint, stop trying
                break

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
            cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, self)
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

    def _should_flee(self, player, game_map) -> bool:
        """
        Determine if enemy should flee from player.

        Enemies flee when:
        1. Health is below 30% of maximum
        2. Player is visible OR hostile state (knows player is nearby)
        3. Not a static enemy (can't flee if can't move)

        Args:
            player: Player instance
            game_map: GameMap for visibility checks

        Returns:
            True if enemy should flee, False otherwise
        """
        # Don't flee if static
        if self.get_movement_type() == EnemyMovement.STATIC:
            return False

        # Check health threshold
        # Safety check for tests where max_cpu might be a mock
        try:
            max_cpu = int(self.type_data.max_cpu)
            if max_cpu <= 0:
                return False
            health_percent = self.cpu / max_cpu
            flee_threshold = GameConfig.get('balance.enemy_flee_health_threshold', 0.3)
            if health_percent > flee_threshold:
                return False
        except (TypeError, ValueError, AttributeError):
            # In tests or invalid state, don't flee
            return False

        # Only flee if we can see player or are hostile (know player is nearby)
        if self.can_see_player(player, game_map) or self.state == EnemyState.HOSTILE:
            return True

        return False

    def _fill_flee_moves(self, game_map, player, game_engine):
        """
        Fill move queue with flee moves using Dijkstra maps.

        Uses TCOD Dijkstra maps to find the best escape route away from player.
        Each move in the queue maximizes distance from player.

        Args:
            game_map: GameMap for pathfinding
            player: Player to flee from
            game_engine: GameEngine for enemy collision avoidance
        """
        # Create Dijkstra map with player as threat
        dijkstra_map = PathfindingHelper.create_dijkstra_map(
            goals=[player.position],
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=self
        )

        # Fill queue with up to 3 flee moves
        current_pos = self.move_queue[-1] if self.move_queue else self.position

        while len(self.move_queue) < 3:
            # Get best flee move from current position
            flee_direction = PathfindingHelper.get_flee_move(
                current_pos=current_pos,
                dijkstra_map=dijkstra_map,
                game_map=game_map
            )

            if flee_direction is None:
                # No valid flee move, stop filling
                logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): No valid flee move from ({current_pos.x},{current_pos.y})")
                break

            # Calculate next position
            dx, dy = flee_direction
            next_pos = Position(current_pos.x + dx, current_pos.y + dy)

            # Validate move
            if not self._is_move_valid_from(next_pos, current_pos, game_map, player, game_engine):
                logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): Flee move to ({next_pos.x},{next_pos.y}) invalid")
                break

            # Add to queue
            self.move_queue.append(next_pos)
            current_pos = next_pos
            logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): Added flee move to ({next_pos.x},{next_pos.y})")

        if len(self.move_queue) > 0:
            logging.debug(f"Enemy {self.type_data.name}@({self.x},{self.y}): Flee queue filled with {len(self.move_queue)} moves")

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
        # Use centralized PositionValidator for consistency
        return PositionValidator.is_valid_for_enemy_movement(
            position, game_map, game_engine.enemies, player.position, self
        )


# Pathfinding helper functions


