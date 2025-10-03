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
        """Check if player can see enemy using TCOD FOV system with shadow mechanics."""
        distance = self.position.distance_to(enemy_target.position)
        
        # Adjacent enemies should ALWAYS be visible (critical for combat feedback)
        if distance <= getattr(GameConfig, 'adjacent_visibility_threshold', 1.5):
            return True
        
        # Use enhanced vision system that can see through walls
        if self.can_see_through_walls():
            return distance <= self.get_vision_range()

        # Check stealth mechanics first
        player_in_shadow = game_map.is_shadow(self.position)
        enemy_in_shadow = game_map.is_shadow(enemy_target.position)
        
        # If enemy is in shadow, only visible if player is directly adjacent
        if enemy_in_shadow and distance > 1:
            return False
        
        # Calculate effective vision range considering shadows
        base_vision_range = self.get_vision_range()
        if player_in_shadow and distance > 1:
            # Reduce vision range when in shadows
            reduction_factor = getattr(GameConfig, 'shadow_vision_reduction_factor', 3)
            effective_vision_range = max(1, base_vision_range // reduction_factor)
        else:
            effective_vision_range = base_vision_range
        
        # Use TCOD FOV for line of sight calculation
        return game_map.can_see_position(self.position, enemy_target.position, effective_vision_range)
    
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
        self.patrol_stuck_counter = 0  # Prevents getting stuck on patrol points
        self.last_seen_player: Optional[Position] = None
        self.movement_queue: List[Position] = []  # Queue of planned moves for ALL movement types
        self.last_queue_state = None  # Track state when queue was last generated
        self.last_queue_target = None  # Track target when queue was last generated
        self.last_target: Optional[Position] = None  # Last target we pathfinded to
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
        
        # Admin Avatar has perfect tracking - can always see player regardless of conditions
        if self.type == 'admin':
            return True
        
        distance_to_player = self.position.distance_to(player.position)
        max_vision_range = self.type_data.vision
        
        if distance_to_player > max_vision_range:
            return False

        # Check if player is invisible (data mimic effect)
        if player.is_invisible():
            return False
        
        # Check for stealth mechanics with shadows
        is_player_in_shadow = game_map.is_shadow(player.position)
        
        # Player in shadow: only visible if enemy is directly adjacent
        adjacent_threshold = GameBalance.ADJACENT_DISTANCE_THRESHOLD
        if is_player_in_shadow and distance_to_player > adjacent_threshold:
            return False

        return game_map.can_see_position(self.position, player.position, max_vision_range)
    
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
            # Virus applies virus damage instead of direct damage
            virus_duration = getattr(GameConfig, 'virus_base_duration', 3)
            current_virus = player.temporary_effects.get('virus_turns', 0)
            
            # Each attack adds to the duration (stacks)
            player.temporary_effects['virus_turns'] = current_virus + virus_duration
            
            # Cap maximum virus duration to prevent infinite stacking
            max_virus_duration = getattr(GameConfig, 'virus_max_duration', 10)
            player.temporary_effects['virus_turns'] = min(
                player.temporary_effects['virus_turns'], 
                max_virus_duration
            )
            
            return 0  # No immediate damage
        elif self.type == 'inhibitor':
            # Inhibitor adds 1 slow turn - offset against any speed boost
            slow_to_add = 1
            current_speed = player.temporary_effects['speed_boost_turns']
            
            if current_speed > 0:
                # Cancel speed moves immediately
                player.speed_moves_remaining = 0
                
                if current_speed >= slow_to_add:
                    # Speed boost absorbs all slow
                    player.temporary_effects['speed_boost_turns'] = current_speed - slow_to_add
                else:
                    # Some slow remains after canceling speed
                    player.temporary_effects['speed_boost_turns'] = 0
                    player.temporary_effects['movement_slowed_turns'] = slow_to_add - current_speed
            else:
                # No speed boost, add slow normally
                player.temporary_effects['movement_slowed_turns'] += slow_to_add
            
            # Inhibitor only slows, doesn't deal damage
            return 0
        else:
            return player.take_damage(self.type_data.damage)
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        # Admin avatar has 50% damage resistance
        if self.type == 'admin':
            damage = max(5, damage // 2)  # Minimum 5 damage to prevent immunity
        
        self.cpu -= damage
        return self.cpu <= 0
    
    def move(self, game_map, player: Player, game_engine=None) -> bool:
        """Simple queue-based movement system."""
        # Skip movement if disabled or on cooldown
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False
        
        if self.move_cooldown > 0 and self.type != 'admin':
            self.move_cooldown -= 1
            return False
        
        # Generate new queue if needed (empty queue or state/target changed)
        if self._should_regenerate_queue(game_map, player, game_engine):
            self._generate_movement_queue(game_map, player, game_engine)
        else:
            # If queue is getting short but state/target unchanged, extend it
            self._extend_queue_if_needed(game_map, player, game_engine)

        # Execute next move from queue
        moved = self._execute_next_move(game_map, player, game_engine)
        
        # Reset cooldown after successful movement
        if moved:
            self._reset_movement_cooldown()
        
        return moved
    
    def _should_regenerate_queue(self, game_map, player: Player, game_engine) -> bool:
        """Determine if the movement queue should be regenerated."""
        # Always regenerate if queue is empty
        if not self.movement_queue:
            return True
        
        # Check if enemy state has changed
        if self.last_queue_state != self.state:
            return True
        
        # For hostile enemies, check if target has changed
        if self.state == EnemyState.HOSTILE:
            current_target = None
            if self.can_see_player(player, game_map):
                current_target = player.position
            elif self.last_seen_player:
                current_target = self.last_seen_player
            
            if current_target != self.last_queue_target:
                return True
        
        # For SEEK/TRACK enemies, check if they've acquired or lost a target
        elif self.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.TRACK]:
            current_target = None
            if self.can_see_player(player, game_map):
                current_target = player.position
            elif self.last_seen_player and self.type_data.movement == EnemyMovement.TRACK:
                current_target = self.last_seen_player
            
            if current_target != self.last_queue_target:
                return True
        
        return False

    def _extend_queue_if_needed(self, game_map, player: Player, game_engine):
        """Extend movement queue if it's getting short, maintaining the same movement pattern."""
        # Only extend if queue has fewer than 3 moves
        if len(self.movement_queue) >= GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
            return

        # Don't extend if enemy is static
        if self.type_data.movement == EnemyMovement.STATIC:
            return

        # Determine current target and movement pattern
        target = None
        use_pathfinding = False

        if self.state == EnemyState.HOSTILE:
            if self.can_see_player(player, game_map):
                target = player.position
                use_pathfinding = True
            elif self.last_seen_player:
                target = self.last_seen_player
                use_pathfinding = True
            elif self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
                target = self.patrol_points[self.patrol_index]
                use_pathfinding = True
        elif self.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.TRACK]:
            if self.can_see_player(player, game_map):
                target = player.position
                use_pathfinding = True
            elif self.last_seen_player and self.type_data.movement == EnemyMovement.TRACK:
                target = self.last_seen_player
                use_pathfinding = True
        elif self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
            # Use intelligent patrol queue extension
            current_target = self.patrol_points[self.patrol_index]
            next_target = self.patrol_points[(self.patrol_index + 1) % len(self.patrol_points)]
            self._extend_patrol_queue(current_target, next_target, game_map, game_engine)
            return

        # Extend the queue using the same logic as before
        self._extend_movement_queue(target, use_pathfinding, game_map, game_engine)

    def _reset_movement_cooldown(self):
        """Reset movement cooldown based on enemy type."""
        if self.type_data.movement == EnemyMovement.STATIC:
            self.move_cooldown = 999  # Static enemies never move
        elif self.type == 'admin':
            self.move_cooldown = 0  # Admin Avatar always moves every turn
        else:
            self.move_cooldown = 0  # All moving enemies can move next turn
    
    def _needs_full_queue_regeneration(self, player: Player, game_map) -> bool:
        """
        Determine if the movement queue needs full regeneration or just extension.
        
        Full regeneration is needed when:
        - Queue is empty
        - Enemy state changed (e.g., unaware -> alert -> hostile)
        - Target changed (e.g., different player position, different patrol point)
        - Patrol enemy reached their current destination
        """
        # Empty queue always needs full regeneration
        if not self.movement_queue:
            return True
        
        # State change requires full regeneration (behavior might change)
        if self.last_queue_state != self.state:
            return True
        
        # Determine current target based on enemy state and movement type
        current_target = None
        if self.state == EnemyState.HOSTILE:
            if self.can_see_player(player, game_map):
                current_target = player.position
            elif self.last_seen_player:
                current_target = self.last_seen_player
        elif self.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.TRACK]:
            if self.can_see_player(player, game_map):
                current_target = player.position
            elif self.last_seen_player and self.type_data.movement == EnemyMovement.TRACK:
                current_target = self.last_seen_player
        elif self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
            current_target = self.patrol_points[self.patrol_index]
        
        # Only regenerate if target actually changed (not just None -> None)
        if current_target != self.last_queue_target and not (current_target is None and self.last_queue_target is None):
            return True
        
        # For patrol enemies, check if they reached their destination
        if (self.type_data.movement == EnemyMovement.PATROL and 
            self.patrol_points and 
            self.state != EnemyState.HOSTILE):
            current_patrol_target = self.patrol_points[self.patrol_index]
            adjacent_threshold = GameBalance.ADJACENT_DISTANCE_THRESHOLD
            if self.position.distance_to(current_patrol_target) <= adjacent_threshold:
                return True
        
        return False
    
    def _extend_movement_queue(self, target: Optional[Position], use_pathfinding: bool, game_map, game_engine):
        """Extend the existing movement queue to maintain 3 moves."""
        # Calculate how many moves we need to add
        desired_queue_length = 3
        moves_needed = desired_queue_length - len(self.movement_queue)
        
        if moves_needed <= 0:
            return  # Queue is already full
        
        # Generate additional moves based on the same logic
        temp_queue = []
        if use_pathfinding and target:
            # Use pathfinding to generate additional moves
            try:
                cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
                graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                
                # Start from the last position in the current queue, or current position
                start_pos = self.movement_queue[-1] if self.movement_queue else self.position
                pathfinder.add_root((start_pos.x, start_pos.y))
                path = pathfinder.path_to((target.x, target.y))
                
                if len(path) > 1:
                    # Add the next moves from the path (skip current position)
                    for i in range(1, min(len(path), moves_needed + 1)):
                        x, y = path[i]
                        temp_queue.append(Position(x, y))
            except (AttributeError, IndexError, ValueError, TypeError):
                # If pathfinding fails due to invalid data, continue to random moves below
                pass
        
        # Fill remaining slots with random moves if needed
        while len(temp_queue) < moves_needed:
            # Use the last position in the temp queue, or the last position in movement queue, or current position
            if temp_queue:
                current_pos = temp_queue[-1]
            elif self.movement_queue:
                current_pos = self.movement_queue[-1]
            else:
                current_pos = self.position
            
            random_move = self._get_random_adjacent_position(current_pos, game_map, game_engine)
            if random_move and random_move not in temp_queue and random_move not in self.movement_queue:
                temp_queue.append(random_move)

                # If this move gets us adjacent to the player, stop adding moves
                if (target and random_move.is_adjacent_to(target) and
                    target == game_engine.player.position):
                    break
            else:
                break  # Can't find more valid moves
        
        # Add the new moves to the queue
        self.movement_queue.extend(temp_queue)
    
    def _get_random_adjacent_position(self, from_pos: Position, game_map, game_engine) -> Optional[Position]:
        """Get a random valid adjacent position from the given position."""
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            next_pos = Position(from_pos.x + dx, from_pos.y + dy)
            if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                return next_pos
        
        return None  # No valid adjacent positions found
    
    def _generate_movement_queue(self, game_map, player: Player, game_engine):
        """Generate movement queue based on enemy state and type."""
        # Only clear queue if state/target changed significantly, otherwise maintain it
        needs_full_regeneration = self._needs_full_queue_regeneration(player, game_map)
        
        if needs_full_regeneration:
            self.movement_queue.clear()
        
        # Static enemies never move, regardless of state
        if self.type_data.movement == EnemyMovement.STATIC:
            return
        
        # Determine target based on state and movement type
        target = None
        use_pathfinding = False
        
        if self.state == EnemyState.HOSTILE:
            # HOSTILE enemies seek the player
            if self.can_see_player(player, game_map):
                self.last_seen_player = player.position
                target = player.position
                use_pathfinding = True
            elif self.last_seen_player:
                target = self.last_seen_player
                use_pathfinding = True
            elif self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
                # HOSTILE patrol enemies return to patrol when they lose the player
                self._generate_intelligent_patrol_queue(game_map, game_engine)
                return  # Skip normal pathfinding
        elif self.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.TRACK]:
            # SEEK/TRACK movement types target player when they can see them
            if self.can_see_player(player, game_map):
                self.last_seen_player = player.position
                target = player.position
                use_pathfinding = True
            elif self.last_seen_player and self.type_data.movement == EnemyMovement.TRACK:
                # TRACK is more persistent than SEEK
                target = self.last_seen_player
                use_pathfinding = True
        elif self.type_data.movement == EnemyMovement.PATROL and self.patrol_points:
            # PATROL movement with intelligent route planning
            self._generate_intelligent_patrol_queue(game_map, game_engine)
            return  # Skip normal pathfinding - patrol uses custom logic
        
        # Generate or extend the movement queue
        if needs_full_regeneration:
            # Full regeneration - build entire queue from scratch
            if use_pathfinding and target:
                self._generate_pathfinding_queue(target, game_map, game_engine)
            else:
                self._generate_random_queue(game_map, game_engine)
            
            # Ensure we always have up to 3 moves (but stop if adjacent to target)
            self._ensure_queue_length(game_map, game_engine, target)
        else:
            # Extend existing queue - just add moves to reach 3 total
            self._extend_movement_queue(target, use_pathfinding, game_map, game_engine)
        
        # Track state and target for future queue regeneration decisions
        self.last_queue_state = self.state
        self.last_queue_target = target

    def _generate_intelligent_patrol_queue(self, game_map, game_engine):
        """Generate intelligent patrol movement queue that considers the full patrol route."""
        if not self.patrol_points:
            return

        current_target = self.patrol_points[self.patrol_index]
        next_target = self.patrol_points[(self.patrol_index + 1) % len(self.patrol_points)]

        # Determine if we need full regeneration or just extension
        needs_full_regeneration = self._needs_full_queue_regeneration(None, game_map)

        if needs_full_regeneration:
            self.movement_queue.clear()

            # Calculate distance to current patrol point
            distance_to_current = self.position.distance_to(current_target)

            # If we're very close to current target, plan route to next target
            if distance_to_current <= 2.0:
                self._generate_patrol_route_to_next_point(current_target, next_target, game_map, game_engine)
            else:
                # Plan route to current target, but consider next target for final moves
                self._generate_patrol_route_to_current_point(current_target, next_target, game_map, game_engine)
        else:
            # Extend existing queue
            self._extend_patrol_queue(current_target, next_target, game_map, game_engine)

        # Track target for regeneration decisions
        self.last_queue_target = current_target

    def _generate_patrol_route_to_current_point(self, current_target: Position, next_target: Position, game_map, game_engine):
        """Generate route to current patrol point, but position for efficient transition to next point."""
        try:
            # Create cost map
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.x, self.y))

            # Calculate path to current target
            path = pathfinder.path_to((current_target.x, current_target.y))

            if len(path) <= 1:
                # Already at target, plan for next target
                self._generate_patrol_route_to_next_point(current_target, next_target, game_map, game_engine)
                return

            # Add most of the path to current target
            moves_to_add = min(len(path) - 1, 2)  # Save room for strategic positioning
            for i in range(1, moves_to_add + 1):
                x, y = path[i]
                next_pos = Position(x, y)
                if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                    self.movement_queue.append(next_pos)

            # For the final move(s), position strategically for next target
            if len(self.movement_queue) < GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
                self._add_strategic_positioning_moves(current_target, next_target, game_map, game_engine)

        except Exception as e:
            logging.error(f"Patrol pathfinding failed: {e}")
            # Fallback to simple movement
            self._generate_random_queue(game_map, game_engine)

    def _generate_patrol_route_to_next_point(self, current_target: Position, next_target: Position, game_map, game_engine):
        """Generate route directly to next patrol point since we're close to current."""
        try:
            # Create cost map
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.x, self.y))

            # Calculate path to next target
            path = pathfinder.path_to((next_target.x, next_target.y))

            if len(path) > 1:
                # Add up to 3 moves toward next target
                for i in range(1, min(len(path), 4)):
                    x, y = path[i]
                    next_pos = Position(x, y)
                    if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                        self.movement_queue.append(next_pos)

            # Fill remaining slots with random moves if needed
            while len(self.movement_queue) < GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
                if self.movement_queue:
                    last_pos = self.movement_queue[-1]
                else:
                    last_pos = self.position

                random_move = self._get_random_adjacent_position(last_pos, game_map, game_engine)
                if random_move and random_move not in self.movement_queue:
                    self.movement_queue.append(random_move)
                else:
                    break

        except Exception as e:
            logging.error(f"Patrol next-point pathfinding failed: {e}")
            self._generate_random_queue(game_map, game_engine)

    def _add_strategic_positioning_moves(self, current_target: Position, next_target: Position, game_map, game_engine):
        """Add moves that position the enemy strategically for transition to next patrol point."""
        # Calculate direction from current to next target
        dx = next_target.x - current_target.x
        dy = next_target.y - current_target.y

        # Normalize direction
        if dx != 0:
            dx = dx // abs(dx)
        if dy != 0:
            dy = dy // abs(dy)

        # Try to position on the side of current target that's toward next target
        strategic_positions = [
            Position(current_target.x + dx, current_target.y + dy),  # Diagonal toward next
            Position(current_target.x + dx, current_target.y),       # Horizontal toward next
            Position(current_target.x, current_target.y + dy),       # Vertical toward next
            Position(current_target.x - dx, current_target.y - dy),  # Opposite direction
        ]

        for strategic_pos in strategic_positions:
            if len(self.movement_queue) >= GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
                break

            if (self._is_valid_enemy_move(strategic_pos, game_map, game_engine) and
                strategic_pos not in self.movement_queue and
                strategic_pos != self.position):
                self.movement_queue.append(strategic_pos)

    def _extend_patrol_queue(self, current_target: Position, next_target: Position, game_map, game_engine):
        """Extend existing patrol queue intelligently."""
        while len(self.movement_queue) < GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
            # If queue is short, add moves toward current target or next target as appropriate
            if self.movement_queue:
                last_planned_pos = self.movement_queue[-1]
                distance_to_current = last_planned_pos.distance_to(current_target)

                # If close to current target, start planning for next
                if distance_to_current <= 2.0:
                    target_for_extension = next_target
                else:
                    target_for_extension = current_target
            else:
                target_for_extension = current_target

            # Add one move toward the target
            self._extend_movement_queue(target_for_extension, True, game_map, game_engine)

            # Safety break to avoid infinite loop
            if len(self.movement_queue) >= GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
                break

    def _generate_pathfinding_queue(self, target: Position, game_map, game_engine):
        """Generate movement queue using pathfinding to target, ensuring 3 valid moves."""
        try:
            # Create cost map
            cost_map = create_pathfinding_cost_map(game_map, game_engine, self)

            # Set up pathfinder
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((self.x, self.y))

            # Calculate path
            path = pathfinder.path_to((target.x, target.y))

            # If we can't reach the target directly, find the closest accessible position
            if len(path) == 0:
                closest_position = self._find_closest_accessible_position(target, pathfinder, game_map, game_engine)
                if closest_position:
                    path = pathfinder.path_to((closest_position.x, closest_position.y))
                    logging.debug(f"Enemy {self.type_data.name} path blocked, moving to closest position instead")

                if len(path) == 0:
                    logging.warning(f"Enemy {self.type_data.name} could not find any path to target area")

            # Add up to 3 moves from the path, but stop if we'd be adjacent to target
            for i in range(1, min(len(path), 4)):  # Skip current position, take next 3
                x, y = path[i]
                next_pos = Position(x, y)
                if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                    self.movement_queue.append(next_pos)

                    # If this move gets us adjacent to the player, stop adding moves
                    # (enemy will attack instead of moving further)
                    if (target and next_pos.is_adjacent_to(target) and
                        target == game_engine.player.position):
                        break

                    # Also stop if the next position in the path would be the player position
                    # This prevents queueing moves that attempt to go "through" the player
                    if (i + 1 < len(path) and target == game_engine.player.position and
                        path[i + 1][0] == target.x and path[i + 1][1] == target.y):
                        break

        except Exception as e:
            # If pathfinding fails, fall back to random movement
            logging.error(f"Enemy {self.type_data.name} pathfinding failed: {e}")
            self._generate_random_queue(game_map, game_engine)
    
    def _find_closest_accessible_position(self, target: Position, pathfinder, game_map, game_engine) -> Optional[Position]:
        """Find the closest position to target that is accessible via pathfinding."""
        # Search in expanding rings around the target
        for radius in range(1, 8):  # Search up to 8 tiles away
            # Check all positions at this radius from the target
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    # Only check positions on the perimeter of this radius
                    if abs(dx) != radius and abs(dy) != radius:
                        continue

                    candidate_pos = Position(target.x + dx, target.y + dy)

                    # Check if this position is valid and accessible
                    if (self._is_valid_enemy_move(candidate_pos, game_map, game_engine) and
                        len(pathfinder.path_to((candidate_pos.x, candidate_pos.y))) > 0):
                        return candidate_pos

        return None

    def _generate_random_queue(self, game_map, game_engine):
        """Generate 3 random valid moves."""
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        current_pos = Position(self.x, self.y)
        attempts = 0
        max_attempts = 24  # 8 directions * 3 moves
        
        while len(self.movement_queue) < GameBalance.MAX_MOVEMENT_QUEUE_SIZE and attempts < max_attempts:
            # Shuffle directions for better randomness
            random.shuffle(directions)
            
            for dx, dy in directions:
                if len(self.movement_queue) >= GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
                    break
                    
                next_pos = Position(current_pos.x + dx, current_pos.y + dy)
                if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                    self.movement_queue.append(next_pos)
                    current_pos = next_pos
                    break
            attempts += 1
    
    def _ensure_queue_length(self, game_map, game_engine, target: Optional[Position] = None):
        """Ensure the movement queue has up to 3 moves, but stop if adjacent to target."""
        # If the last move in the queue is already adjacent to the player, don't add more moves
        if (self.movement_queue and target and
            target == game_engine.player.position and
            self.movement_queue[-1].is_adjacent_to(target)):
            return

        while len(self.movement_queue) < GameBalance.MAX_MOVEMENT_QUEUE_SIZE:
            # Try to add more random moves from the last position in queue
            if self.movement_queue:
                last_pos = self.movement_queue[-1]
            else:
                last_pos = Position(self.x, self.y)
            
            # Try all directions to find a valid move
            directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
            random.shuffle(directions)
            
            move_added = False
            for dx, dy in directions:
                next_pos = Position(last_pos.x + dx, last_pos.y + dy)
                if self._is_valid_enemy_move(next_pos, game_map, game_engine):
                    # Check if this position is already in the queue to avoid cycles
                    if next_pos not in [Position(self.x, self.y)] + self.movement_queue:
                        self.movement_queue.append(next_pos)
                        move_added = True

                        # If this move gets us adjacent to the player, stop adding moves
                        if (target and next_pos.is_adjacent_to(target) and
                            target == game_engine.player.position):
                            return
                        break
            
            # If we can't find any valid moves, break to avoid infinite loop
            if not move_added:
                break
    
    def _is_valid_enemy_move(self, position: Position, game_map, game_engine) -> bool:
        """Check if a position is valid for enemy movement."""
        return PositionValidator.is_valid_for_enemy_movement(
            position, game_map, game_engine.enemies, game_engine.player.position, self
        )
    
    def _execute_next_move(self, game_map, player: Player, game_engine) -> bool:
        """Execute the next move from the movement queue."""
        if not self.movement_queue:
            return False

        next_position = self.movement_queue[0]

        # If next position is the player position, we can't move there
        if next_position.distance_to(player.position) == 0:
            # Clear queue since we've reached our goal (adjacent to player)
            self.movement_queue.clear()
            return False  # No movement, but this is expected behavior

        # Check if we can move to this position
        if can_move_to_position(self, next_position, game_map, player, game_engine):
            self.position = next_position
            self.movement_queue.pop(0)  # Remove completed move

            # Check if patrol enemy reached their patrol point
            if (self.type_data.movement == EnemyMovement.PATROL and
                self.patrol_points and
                self.state != EnemyState.HOSTILE):  # Only patrol when not hostile

                current_target = self.patrol_points[self.patrol_index]
                adjacent_threshold = GameBalance.ADJACENT_DISTANCE_THRESHOLD
                if self.position.distance_to(current_target) <= adjacent_threshold:
                    # Reached patrol point, advance to next one
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                    # Clear movement queue to force pathfinding to new target
                    self.movement_queue.clear()

            return True
        else:
            # Move is blocked - only remove the blocked move, don't clear entire queue
            # The queue will be regenerated next turn if needed via _should_regenerate_queue
            self.movement_queue.pop(0)  # Remove just the blocked move

            # Handle patrol stuck situations
            if (self.type_data.movement == EnemyMovement.PATROL and self.patrol_points):
                self.patrol_stuck_counter += 1
                if self.patrol_stuck_counter >= GameBalance.PATROL_STUCK_THRESHOLD:
                    # Skip to next patrol point if stuck for too many turns
                    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                    self.patrol_stuck_counter = 0
                    # Now clear queue to force pathfinding to new patrol point
                    self.movement_queue.clear()

            return False


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