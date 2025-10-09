"""
Game Level Generator Module

Handles procedural level generation and room placement algorithms.
Extracted from RogueSignalProtocol.py for better code organization.
"""

import random
import logging
from typing import List, Tuple, Optional, Dict, Set

# Import required classes and configs
from game_config import GameConfig, RoomGenerationConfig
from game_entities import Position
from game_inventory import CodeHack, ExploitItem, StoryFragment


class LevelGenerator:
    """Handles procedural level generation and room placement."""
    
    def __init__(self, game_map):
        self.game_map = game_map
    
    def generate_level(self, level: int, seed: int) -> None:
        """Generate a complete level with rooms, corridors, and special tiles."""
        random.seed(seed + level)
        
        # Clear existing level data
        self._clear_level_data()
        
        # Generate the level structure
        self._generate_procedural_level(level)
        
        # Place special tiles and items
        self._place_special_tiles(level)
        self._place_gateway()
        
        # Final invalidation to ensure FOV calculations use the correct wall layout
        self.game_map.invalidate_transparency_cache()
    
    def _clear_level_data(self) -> None:
        """Clear all existing level data."""
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.ghost_nodes.clear()
        self.game_map.code_hacks.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        self.game_map.explored_tiles.clear()
        self.game_map.last_known_enemy_positions.clear()
        # Invalidate transparency cache for FOV calculations
        self.game_map.invalidate_transparency_cache()
    
    def _generate_procedural_level(self, level: int) -> None:
        """Generate the basic level structure using improved algorithm from dungeon-gen-v3.py"""
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))
        
        # Create rooms with varied sizes (inspired by dungeon-gen-v3.py)
        rooms = self._create_varied_rooms(level)
        
        # Connect rooms using MST approach for better connectivity
        self._connect_rooms_mst(rooms)
        
        # Add extra paths for multiple routes (good for stealth)
        self._add_extra_paths(rooms)
        
        # Add strategic cover elements in open areas
        self._add_cover_elements_new()
        
        # Add shadow areas for stealth gameplay
        self._place_shadow_areas(level, rooms)
        
        # Ensure border walls are intact
        self._ensure_border_walls_new()
        
        # Store final room list
        self.last_generated_rooms = rooms
    
    def _create_varied_rooms(self, level: int) -> List[Tuple[int, int, int, int]]:
        """Create varied rooms including a guaranteed spawn room in top-left corner."""
        spawn_room = (2, 2, 8, 8)
        self._carve_room(spawn_room)
        rooms = [spawn_room]
        rooms.extend(self._generate_rooms_avoiding_existing(level, [spawn_room]))
        return rooms
    
    def _carve_room(self, room: Tuple[int, int, int, int]) -> None:
        """Carve out a room by removing walls in the specified area."""
        x, y, width, height = room
        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    self.game_map.walls.remove((rx, ry))
    
    def _generate_rooms_avoiding_existing(self, level: int, existing_rooms: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Generate room layouts for the level."""
        num_rooms = RoomGenerationConfig.MIN_ROOMS_BASE + level * RoomGenerationConfig.ROOM_LEVEL_MULTIPLIER
        max_rooms = min(num_rooms, RoomGenerationConfig.MAX_ROOMS)
        max_attempts = RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS
        
        new_rooms = []
        all_rooms = existing_rooms.copy()  # Include existing rooms for overlap checking
        
        for _ in range(max_attempts):
            if len(new_rooms) >= max_rooms:
                break
                
            # Generate random room, avoiding top-left spawn area
            room_width = random.randint(RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE)
            room_height = random.randint(RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE)
            room_x = random.randint(12, GameConfig.MAP_WIDTH - room_width - 2)  # Start at 12 to avoid spawn area
            room_y = random.randint(12, GameConfig.MAP_HEIGHT - room_height - 2)
            
            new_room = (room_x, room_y, room_width, room_height)
            
            # Check if room overlaps with any existing rooms
            if not self._room_overlaps(new_room, all_rooms):
                new_rooms.append(new_room)
                all_rooms.append(new_room)  # Add to tracking list
                self._carve_room(new_room)
        
        return new_rooms
    
    
    def _room_overlaps(self, new_room: Tuple[int, int, int, int], existing_rooms: List[Tuple[int, int, int, int]]) -> bool:
        """Check if a new room overlaps with existing rooms."""
        x1, y1, w1, h1 = new_room
        pad = RoomGenerationConfig.ROOM_PADDING

        for x2, y2, w2, h2 in existing_rooms:
            if (x1 < x2 + w2 + pad and x1 + w1 + pad > x2 and
                y1 < y2 + h2 + pad and y1 + h1 + pad > y2):
                return True
        return False
    

    
    def _place_shadow_areas(self, level: int, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Place shadow areas for stealth gameplay - NO FALLBACKS."""
        network_configs = GameConfig.NETWORK_CONFIGS()

        # FAIL if level config not found
        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            print(error_msg)
            logging.error(error_msg)
            print(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        # Ensure shadow_coverage exists
        if 'shadow_coverage' not in config:
            error_msg = f"CRITICAL CONFIG ERROR: 'shadow_coverage' missing for level {level} in game_data.json network_configs"
            print(error_msg)
            logging.error(error_msg)
            print(f"Available config keys for level {level}: {list(config.keys())}")
            raise KeyError(f"Required key 'shadow_coverage' missing from level {level} config")

        shadow_coverage = config['shadow_coverage']
        
        total_floor_tiles = sum(w * h for x, y, w, h in rooms)
        target_shadow_tiles = int(total_floor_tiles * shadow_coverage)
        
        placed_shadows = 0
        for room in rooms:
            if placed_shadows >= target_shadow_tiles:
                break
                
            x, y, width, height = room
            shadows_in_room = min(target_shadow_tiles - placed_shadows, width * height // 3)
            
            for _ in range(shadows_in_room):
                shadow_x = random.randint(x, x + width - 1)
                shadow_y = random.randint(y, y + height - 1)
                
                if (shadow_x, shadow_y) not in self.game_map.walls:
                    self.game_map.shadows.add((shadow_x, shadow_y))
                    placed_shadows += 1
    
    def _connect_rooms_mst(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Connect rooms using minimum spanning tree approach."""
        if len(rooms) < 2:
            return
            
        connected = [rooms[0]]  # Start with first room
        unconnected = rooms[1:]
        
        while unconnected:
            min_distance = float('inf')
            closest_pair = None
            
            for connected_room in connected:
                cx = connected_room[0] + connected_room[2] // 2
                cy = connected_room[1] + connected_room[3] // 2
                
                for i, unconnected_room in enumerate(unconnected):
                    ux = unconnected_room[0] + unconnected_room[2] // 2
                    uy = unconnected_room[1] + unconnected_room[3] // 2
                    
                    distance = abs(cx - ux) + abs(cy - uy)
                    if distance < min_distance:
                        min_distance = distance
                        closest_pair = (connected_room, unconnected_room, i)
            
            if closest_pair:
                room1, room2, index = closest_pair
                self._create_corridor_between_rooms(room1, room2)
                connected.append(room2)
                unconnected.pop(index)
    
    def _add_extra_paths(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Add extra corridors for multiple paths."""
        if len(rooms) < 3:
            return
        
        extra_connections = min(random.randint(2, 4), len(rooms) // 2)
        for _ in range(extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice(rooms)
            if room1 != room2:
                self._create_corridor_between_rooms(room1, room2)
    
    def _create_corridor_between_rooms(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]) -> None:
        """Create L-shaped corridor between two rooms."""
        x1 = room1[0] + room1[2] // 2
        y1 = room1[1] + room1[3] // 2
        x2 = room2[0] + room2[2] // 2
        y2 = room2[1] + room2[3] // 2
        
        # Create L-shaped corridor
        if random.choice([True, False]):
            # Horizontal then vertical
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y1 < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.discard((x, y1))
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x2 < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.discard((x2, y))
        else:
            # Vertical then horizontal
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if 0 <= x1 < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.discard((x1, y))
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y2 < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.discard((x, y2))
    
    def _add_cover_elements_new(self) -> None:
        """Add small cover elements in open areas."""
        # Add small wall segments for cover in larger open areas
        for y in range(5, GameConfig.MAP_HEIGHT - 5, 8):
            for x in range(5, GameConfig.MAP_WIDTH - 5, 8):
                if random.random() < 0.3:  # 30% chance
                    # Check if area is mostly open
                    open_tiles = 0
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            check_pos = (x + dx, y + dy)
                            if check_pos not in self.game_map.walls:
                                open_tiles += 1
                    
                    # If mostly open, add small cover element
                    if open_tiles > 15:
                        if random.choice([True, False]):
                            # Small horizontal wall
                            for dx in range(2):
                                if 0 <= x + dx < GameConfig.MAP_WIDTH:
                                    self.game_map.walls.add((x + dx, y))
                        else:
                            # Small vertical wall
                            for dy in range(2):
                                if 0 <= y + dy < GameConfig.MAP_HEIGHT:
                                    self.game_map.walls.add((x, y + dy))
    
    def _ensure_border_walls_new(self) -> None:
        """Ensure map has solid border walls."""
        # Top and bottom walls
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))
        
        # Left and right walls
        for y in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))
    
    def _place_special_tiles(self, level: int) -> None:
        """Place cooling nodes, CPU recovery nodes, and other special tiles - NO FALLBACKS."""
        floor_positions = self._get_all_floor_positions()

        if not floor_positions:
            logging.warning(f"No floor positions available for level {level} special node placement")
            return

        # Get level-specific counts from network config - FAIL if missing
        network_configs = GameConfig.get_network_configs()
        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            print(error_msg)
            logging.error(error_msg)
            print(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        # Helper function to get required config value
        def get_required_config(key: str) -> int:
            if key not in config:
                error_msg = f"CRITICAL CONFIG ERROR: '{key}' missing for level {level} in game_data.json network_configs"
                print(error_msg)
                logging.error(error_msg)
                print(f"Available config keys for level {level}: {list(config.keys())}")
                raise KeyError(f"Required key '{key}' missing from level {level} config")
            return config[key]

        # Place cooling nodes
        cooling_count = get_required_config('cooling_nodes')
        for i in range(cooling_count):
            if floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)
                if level == 3:
                    logging.info(f"Placed cooling node {i+1}/{cooling_count} at {pos}")

        # Place CPU recovery nodes
        cpu_count = get_required_config('cpu_nodes')
        for i in range(cpu_count):
            if floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes.add(pos)
                if level == 3:
                    logging.info(f"Placed CPU node {i+1}/{cpu_count} at {pos}")

        # Place ghost nodes (trace level reduction)
        ghost_count = get_required_config('ghost_nodes')
        for i in range(ghost_count):
            if floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.ghost_nodes.add(pos)
                if level == 3:
                    logging.info(f"Placed ghost node {i+1}/{ghost_count} at {pos}")
                    
        if level == 3:
            logging.info(f"Level 3 special nodes placed - Cooling: {len(self.game_map.cooling_nodes)}, CPU: {len(self.game_map.cpu_recovery_nodes)}, Ghost: {len(self.game_map.ghost_nodes)}")
    
    def _place_gateway(self) -> None:
        """Place the exit gateway far from spawn but with some randomness."""
        spawn_area = Position(5, 5)  # Center of spawn area
        floor_positions = self._get_all_floor_positions()
        
        if not floor_positions:
            return
            
        # Get positions far from spawn (bottom-right quadrant preferred)
        far_positions = []
        medium_positions = []
        
        for pos in floor_positions:
            position = Position(pos[0], pos[1])
            distance = spawn_area.distance_to(position)
            
            # Prefer positions that are far from spawn
            if distance > 30:  # Very far
                far_positions.append(pos)
            elif distance > 20:  # Medium distance
                medium_positions.append(pos)
        
        # Choose gateway position with preference for far positions
        if far_positions:
            gateway_pos = random.choice(far_positions)
        elif medium_positions:
            gateway_pos = random.choice(medium_positions)
        else:
            # Fallback: any position far enough
            valid_positions = [pos for pos in floor_positions 
                             if spawn_area.distance_to(Position(pos[0], pos[1])) > 15]
            gateway_pos = random.choice(valid_positions) if valid_positions else random.choice(floor_positions)
        
        self.game_map.gateway = Position(gateway_pos[0], gateway_pos[1])
    
    def _get_all_floor_positions(self) -> List[Tuple[int, int]]:
        """Get all valid floor positions (not walls)."""
        floor_positions = []
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_positions.append((x, y))
        return floor_positions