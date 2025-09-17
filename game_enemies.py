#!/usr/bin/env python3
"""
Enemy management module for Rogue Signal Protocol.
Handles enemy spawning, AI coordination, and state updates.
"""

import random
from typing import List, Optional, TYPE_CHECKING

# Import necessary entities and configurations
from game_config import GameConfig
from game_entities import Position, EnemyMovement
from game_characters import Enemy, Player

# Forward references to avoid circular imports
if TYPE_CHECKING:
    from RogueSignalProtocol import MessageLog, GameStateManager, GameEngine, GameMap


class EnemyManager:
    """Manages enemy spawning, AI coordination, and state updates."""
    
    def __init__(self, game_map: 'GameMap', message_log: 'MessageLog'):
        self.enemies: List[Enemy] = []
        self.game_map = game_map
        self.message_log = message_log
    
    def spawn_enemy(self, position: Position, enemy_type: str) -> Enemy:
        """Spawn a new enemy at the specified position."""
        # Validate position is not on a wall
        if self.game_map.is_wall(position):
            raise ValueError(f"Cannot spawn enemy on wall at {position}")
        
        enemy = Enemy(position, enemy_type)
        
        # Set up patrol route for patrol enemies
        if enemy.type == 'patrol':
            enemy.patrol_points = self._generate_patrol_route(position)
        elif enemy.type == 'virus':
            # Give virus enemies random movement types for variety
            virus_movement_types = [EnemyMovement.STATIC, EnemyMovement.RANDOM, EnemyMovement.LINEAR, EnemyMovement.SEEK]
            virus_movement_weights = [2, 3, 2, 2]  # Equal chance for each movement type
            chosen_movement = random.choices(virus_movement_types, weights=virus_movement_weights)[0]
            enemy.type_data.movement = chosen_movement
            
            # Generate patrol route if virus got LINEAR movement
            if chosen_movement == EnemyMovement.LINEAR:
                enemy.patrol_points = self._generate_patrol_route(position)
            
        self.enemies.append(enemy)
        return enemy
    
    def update_all_enemies(self, player: Player, game_state: 'GameStateManager', game: 'GameEngine') -> None:
        """Update AI and movement for all enemies."""
        for enemy in self.enemies[:]:  # Use slice copy for safe iteration
            if enemy.disabled_turns > 0:
                continue
                
            # Enemy state is now handled by the main game's _process_enemies method
            
            # Move enemy
            enemy.move(self.game_map, player, game)
    
    def get_enemy_at_position(self, position: Position) -> Optional[Enemy]:
        """Get enemy at the specified position."""
        for enemy in self.enemies:
            if enemy.position.x == position.x and enemy.position.y == position.y:
                return enemy
        return None
    
    def remove_enemy(self, enemy: Enemy) -> None:
        """Remove an enemy from the game."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def _resume_patrol_route(self, enemy: Enemy) -> None:
        """Resume patrol route from the nearest patrol point."""
        if not enemy.patrol_points:
            return
        
        # Find the nearest patrol point to resume from
        min_distance = float('inf')
        nearest_index = 0
        
        for i, patrol_point in enumerate(enemy.patrol_points):
            distance = enemy.position.distance_to(patrol_point)
            if distance < min_distance:
                min_distance = distance
                nearest_index = i
        
        # If already at or very close to the nearest point, advance to next point
        nearest_point = enemy.patrol_points[nearest_index]
        if enemy.position.distance_to(nearest_point) <= GameConfig.ADJACENT_VISIBILITY_THRESHOLD:
            enemy.patrol_index = (nearest_index + 1) % len(enemy.patrol_points)
        else:
            # Set patrol index to the nearest point
            enemy.patrol_index = nearest_index
        
        # Reset stuck counter when resuming patrol route
        enemy.patrol_stuck_counter = 0
    
    def _generate_patrol_route(self, start: Position) -> List[Position]:
        """Generate simple geometric patrol routes with 2-4 points."""
        # Choose a simple pattern type
        pattern_type = random.choice(['line', 'triangle', 'rectangle'])
        step_size = random.randint(4, 8)  # Distance between patrol points
        
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
                return [start, end_point]
                
        elif pattern_type == 'triangle':
            # 3-point triangle pattern
            point2 = Position(start.x + step_size, start.y)
            point3 = Position(start.x + step_size//2, start.y + step_size)
            
            route = [start]
            if self._is_valid_patrol_point(point2):
                route.append(point2)
            if self._is_valid_patrol_point(point3):
                route.append(point3)
            
            if len(route) >= 3:
                return route
                
        elif pattern_type == 'rectangle':
            # 4-point rectangle pattern
            point2 = Position(start.x + step_size, start.y)
            point3 = Position(start.x + step_size, start.y + step_size)
            point4 = Position(start.x, start.y + step_size)
            
            route = [start]
            for point in [point2, point3, point4]:
                if self._is_valid_patrol_point(point):
                    route.append(point)
            
            if len(route) >= 4:
                return route
        
        # Fallback: simple 2-point horizontal line
        fallback_end = Position(start.x + 4, start.y)
        if self._is_valid_patrol_point(fallback_end):
            return [start, fallback_end]
        else:
            # Last resort: single point (static guard)
            return [start]
    
    def _is_valid_patrol_point(self, point: Position) -> bool:
        """Check if a position is valid for patrol."""
        return (point.is_valid(GameConfig.MAP_WIDTH - 3, GameConfig.MAP_HEIGHT - 3) and
                point.x >= 3 and point.y >= 3 and
                self.game_map.is_valid_position(point) and
                not self.game_map.is_wall(point))