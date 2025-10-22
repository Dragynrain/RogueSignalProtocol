#!/usr/bin/env python3
"""
Enemy Management Module

Handles enemy spawning, patrol route generation, and high-level AI coordination.
The EnemyManager class:
- Spawns enemies with proper initialization
- Generates patrol routes (line, triangle, rectangle patterns)
- Updates all enemy AI each turn
- Provides queries for enemy positions

Individual enemy AI and movement logic is in game_characters.py.
"""

import random
import logging
from typing import List, Optional, TYPE_CHECKING

# Import necessary entities and configurations
from game_config import GameConfig
from game_entities import Position, EnemyMovement
from game_characters import Enemy, Player

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from RogueSignalProtocol import MessageLog, GameStateManager, GameEngine, GameMap


class EnemyManager:
    """
    Manages enemy spawning, AI coordination, and state updates.

    Centralizes enemy management to ensure consistent initialization and
    coordinate multi-enemy behaviors. Generates patrol routes automatically
    for PATROL enemies.
    """

    def __init__(self, game_map: 'GameMap', message_log: 'MessageLog'):
        """
        Initialize enemy manager.

        Args:
            game_map: GameMap instance for position validation
            message_log: MessageLog instance for AI messages
        """
        self.enemies: List[Enemy] = []
        self.game_map = game_map
        self.message_log = message_log

    def spawn_enemy(self, position: Position, enemy_type: str) -> Enemy:
        """
        Spawn a new enemy at the specified position.

        Automatically generates patrol routes for PATROL enemies.
        Virus enemies randomly select STATIC, RANDOM, or PATROL behavior.

        Args:
            position: Spawn position (must not be a wall)
            enemy_type: Enemy type identifier (e.g., 'daemon', 'worm', 'virus')

        Returns:
            Newly spawned Enemy instance

        Raises:
            ValueError: If position is on a wall
        """
        # Validate position is not on a wall
        if self.game_map.is_wall(position):
            raise ValueError(f"Cannot spawn enemy on wall at {position}")

        enemy = Enemy(position, enemy_type)

        # Set up patrol route for patrol enemies
        if enemy.type == 'patrol':
            enemy.patrol_points = self._generate_patrol_route(position)
            logging.debug(f"Spawned {enemy_type} at ({position.x},{position.y}), movement=PATROL, patrol_points={len(enemy.patrol_points)}")
        elif enemy.type == 'virus':
            # Virus enemies mimic other infected enemies - randomly pick base movement type
            virus_movement_types = [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.PATROL]
            chosen_movement = random.choice(virus_movement_types)
            # Store in instance variable, NOT in shared type_data!
            enemy.original_movement_type = chosen_movement

            # Generate patrol route if virus got PATROL movement
            if chosen_movement == EnemyMovement.PATROL:
                enemy.patrol_points = self._generate_patrol_route(position)
                logging.debug(f"Spawned {enemy_type} at ({position.x},{position.y}), movement={chosen_movement.name}, patrol_points={len(enemy.patrol_points)}")
            else:
                logging.debug(f"Spawned {enemy_type} at ({position.x},{position.y}), movement={chosen_movement.name}")
        else:
            movement_type = enemy.get_movement_type()
            logging.debug(f"Spawned {enemy_type} at ({position.x},{position.y}), movement={movement_type.name}")

        self.enemies.append(enemy)
        return enemy
    
    def update_all_enemies(self, player: Player, game_state: 'GameStateManager', game_engine: 'GameEngine') -> None:
        """
        Update AI and movement for all enemies.

        Skips disabled (stunned) enemies. Enemy state updates (awareness) are
        handled by GameTurnManager._update_enemy_awareness().

        Args:
            player: Player instance for AI targeting
            game_state: GameStateManager instance for game context
            game_engine: GameEngine instance for pathfinding and queries
        """
        for enemy in self.enemies[:]:  # Use slice copy for safe iteration
            if enemy.disabled_turns > 0:
                continue
                
            # Enemy state is now handled by the main game's _process_enemies method
            
            # Move enemy
            enemy.move(self.game_map, player, game_engine)
    
    def get_enemy_at_position(self, position: Position) -> Optional[Enemy]:
        """Get enemy at the specified position."""
        return next((e for e in self.enemies if e.position.x == position.x and e.position.y == position.y), None)
    
    def remove_enemy(self, enemy: Enemy) -> None:
        """Remove an enemy from the game."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def _resume_patrol_route(self, enemy: Enemy) -> None:
        """Resume patrol route from the nearest patrol point."""
        if not enemy.patrol_points:
            return

        # Find nearest patrol point
        distances = [(i, enemy.position.distance_to(p)) for i, p in enumerate(enemy.patrol_points)]
        nearest_index, min_distance = min(distances, key=lambda x: x[1])

        # Advance if already at nearest point
        enemy.patrol_index = (nearest_index + 1) % len(enemy.patrol_points) \
                           if min_distance <= GameConfig.ADJACENT_VISIBILITY_THRESHOLD else nearest_index
        # patrol_stuck_counter removed in simplified movement system
    
    def _generate_patrol_route(self, start: Position) -> List[Position]:
        """
        Generate simple geometric patrol routes with 2-4 points.

        Creates one of three patterns:
        - Line: 2 points (back and forth)
        - Triangle: 3 points (cyclic patrol)
        - Rectangle: 4 points (perimeter patrol)

        Validates that all points:
        1. Are within bounds and not on walls
        2. Can be reached from each other via TCOD pathfinding

        If no valid pattern can be created, falls back to single-point patrol
        (enemy stays in place when in patrol mode).

        Args:
            start: Starting patrol position

        Returns:
            List of Position objects forming the patrol route
        """
        # Choose a simple pattern type
        pattern_type = random.choice(['line', 'triangle', 'rectangle'])
        step_size = random.randint(4, 8)  # Distance between patrol points
        logging.debug(f"Patrol route: start=({start.x},{start.y}), pattern={pattern_type}, step_size={step_size}")

        if pattern_type == 'line':
            # 2-point line pattern (back and forth)
            direction = random.choice(['horizontal', 'vertical', 'diagonal'])
            if direction == 'horizontal':
                end_point = Position(start.x + step_size, start.y)
            elif direction == 'vertical':
                end_point = Position(start.x, start.y + step_size)
            else:  # diagonal
                end_point = Position(start.x + step_size, start.y + step_size)

            if self._is_valid_patrol_point(end_point):
                route = [start, end_point]
                if self._validate_patrol_connectivity(route):
                    return route

        elif pattern_type == 'triangle':
            # 3-point triangle pattern - try multiple orientations
            triangle_patterns = [
                # Standard triangle
                (Position(start.x + step_size, start.y), Position(start.x + step_size//2, start.y + step_size)),
                # Inverted triangle
                (Position(start.x + step_size, start.y), Position(start.x + step_size//2, start.y - step_size)),
                # Left-pointing triangle
                (Position(start.x, start.y + step_size), Position(start.x - step_size//2, start.y + step_size//2)),
                # Right-pointing triangle
                (Position(start.x, start.y + step_size), Position(start.x + step_size//2, start.y + step_size//2)),
            ]

            for point2, point3 in triangle_patterns:
                route = [start]
                if self._is_valid_patrol_point(point2):
                    route.append(point2)
                if self._is_valid_patrol_point(point3):
                    route.append(point3)

                if len(route) >= 3 and self._validate_patrol_connectivity(route):
                    return route

        elif pattern_type == 'rectangle':
            # 4-point rectangle pattern - try different sizes
            rectangle_sizes = [step_size, step_size // 2, step_size * 2 // 3]

            for size in rectangle_sizes:
                point2 = Position(start.x + size, start.y)
                point3 = Position(start.x + size, start.y + size)
                point4 = Position(start.x, start.y + size)

                route = [start]
                for point in [point2, point3, point4]:
                    if self._is_valid_patrol_point(point):
                        route.append(point)

                if len(route) >= 4 and self._validate_patrol_connectivity(route):
                    return route

                # Try smaller rectangle if full size failed
                if len(route) >= 3 and self._validate_patrol_connectivity(route):
                    return route

        # Fallback: try multiple simple 2-point patterns
        fallback_patterns = [
            Position(start.x + 4, start.y),      # Horizontal right
            Position(start.x - 4, start.y),      # Horizontal left
            Position(start.x, start.y + 4),      # Vertical down
            Position(start.x, start.y - 4),      # Vertical up
            Position(start.x + 3, start.y + 3),  # Diagonal down-right
            Position(start.x - 3, start.y - 3),  # Diagonal up-left
            Position(start.x + 2, start.y),      # Shorter horizontal
            Position(start.x, start.y + 2),      # Shorter vertical
        ]

        for fallback_end in fallback_patterns:
            if self._is_valid_patrol_point(fallback_end):
                route = [start, fallback_end]
                if self._validate_patrol_connectivity(route):
                    logging.debug(f"Patrol route: fallback pattern succeeded, points={len(route)}")
                    return route

        # Last resort: single point (static guard)
        logging.debug(f"Patrol route: all patterns failed, using single-point patrol at ({start.x},{start.y})")
        return [start]

    def _is_valid_patrol_point(self, point: Position) -> bool:
        """Check if a position is valid for patrol (within bounds, not a wall)."""
        return (point.is_valid(GameConfig.MAP_WIDTH - 3, GameConfig.MAP_HEIGHT - 3) and
                point.x >= 3 and point.y >= 3 and
                self.game_map.is_valid_position(point) and
                not self.game_map.is_wall(point))

    def _validate_patrol_connectivity(self, route: List[Position]) -> bool:
        """Verify all patrol points can reach each other via pathfinding."""
        if len(route) < 2:
            return True

        import tcod

        try:
            # Create a simple cost map (just walls vs walkable)
            cost_map = self.game_map.get_walkability_map().copy()

            # Check each consecutive pair of points
            for i in range(len(route)):
                start_point = route[i]
                end_point = route[(i + 1) % len(route)]  # Wrap around to check full loop

                # Quick pathfinding check
                # TCOD pathfinding uses (y, x) coordinate order for numpy arrays
                graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((start_point.y, start_point.x))
                path = pathfinder.path_to((end_point.y, end_point.x))

                # If no path exists, route is invalid
                if len(path) < 2:
                    return False

            return True
        except Exception:
            # If pathfinding fails for any reason, consider route invalid
            return False