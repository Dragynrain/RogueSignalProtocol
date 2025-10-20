"""
Game Level Generator Module

Handles procedural level generation and room placement algorithms.
Extracted from RogueSignalProtocol.py for better code organization.
"""

import random
import logging
import math
from typing import List, Tuple, Optional, Dict, Set

# Import required classes and configs
from game_config import GameConfig, RoomGenerationConfig
from game_entities import Position
from game_inventory import CodeHack, ExploitItem, StoryFragment


class LevelGenerator:
    """Handles procedural level generation and room placement."""
    
    def __init__(self, game_map):
        self.game_map = game_map
        self.corridor_tiles = set()  # Track corridor tiles for alcove placement
    
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
        self.corridor_tiles.clear()  # Clear corridor tracking
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

        # Add alcoves to corridors for stealth hiding spots
        self._add_corridor_alcoves()

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
        """Place shadow areas for stealth gameplay with wall-adjacent preference - NO FALLBACKS."""
        network_configs = GameConfig.NETWORK_CONFIGS()

        # FAIL if level config not found
        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        # Ensure shadow_coverage exists
        if 'shadow_coverage' not in config:
            error_msg = f"CRITICAL CONFIG ERROR: 'shadow_coverage' missing for level {level} in game_data.json network_configs"
            logging.error(error_msg)
            logging.error(f"Available config keys for level {level}: {list(config.keys())}")
            raise KeyError(f"Required key 'shadow_coverage' missing from level {level} config")

        shadow_coverage = config['shadow_coverage']

        # Get shadow placement weights from config - FAIL if missing
        wall_adjacent_weight = GameConfig._get_required('room_generation.shadow_placement_weights.wall_adjacent')
        interior_weight = GameConfig._get_required('room_generation.shadow_placement_weights.interior')

        total_floor_tiles = sum(w * h for x, y, w, h in rooms)
        target_shadow_tiles = int(total_floor_tiles * shadow_coverage)

        placed_shadows = 0
        for room in rooms:
            if placed_shadows >= target_shadow_tiles:
                break

            x, y, width, height = room
            shadows_in_room = min(target_shadow_tiles - placed_shadows, width * height // 3)

            # Get wall-adjacent and interior positions for this room
            wall_adjacent_positions = self._get_wall_adjacent_positions(room)
            interior_positions = self._get_interior_positions(room)

            for _ in range(shadows_in_room):
                # Determine if this shadow should be wall-adjacent or interior
                if random.random() < wall_adjacent_weight:
                    # Try wall-adjacent placement
                    if wall_adjacent_positions:
                        shadow_pos = random.choice(wall_adjacent_positions)
                        wall_adjacent_positions.remove(shadow_pos)
                    elif interior_positions:
                        # Fallback to interior if no wall-adjacent positions left
                        shadow_pos = random.choice(interior_positions)
                        interior_positions.remove(shadow_pos)
                    else:
                        continue  # No positions left
                else:
                    # Try interior placement
                    if interior_positions:
                        shadow_pos = random.choice(interior_positions)
                        interior_positions.remove(shadow_pos)
                    elif wall_adjacent_positions:
                        # Fallback to wall-adjacent if no interior positions left
                        shadow_pos = random.choice(wall_adjacent_positions)
                        wall_adjacent_positions.remove(shadow_pos)
                    else:
                        continue  # No positions left

                if shadow_pos not in self.game_map.walls:
                    self.game_map.shadows.add(shadow_pos)
                    placed_shadows += 1

    def _get_wall_adjacent_positions(self, room: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
        """Get floor positions that are adjacent to walls (1 tile from wall)."""
        x, y, width, height = room
        wall_adjacent = []

        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    continue

                # Check if adjacent to any wall
                adjacent_to_wall = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (rx + dx, ry + dy)
                    if neighbor in self.game_map.walls:
                        adjacent_to_wall = True
                        break

                if adjacent_to_wall:
                    wall_adjacent.append((rx, ry))

        return wall_adjacent

    def _get_interior_positions(self, room: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
        """Get floor positions that are NOT adjacent to walls (interior tiles)."""
        x, y, width, height = room
        interior = []

        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    continue

                # Check if NOT adjacent to any wall
                adjacent_to_wall = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (rx + dx, ry + dy)
                    if neighbor in self.game_map.walls:
                        adjacent_to_wall = True
                        break

                if not adjacent_to_wall:
                    interior.append((rx, ry))

        return interior
    
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
        """Create L-shaped corridor between two rooms with variable width."""
        x1 = room1[0] + room1[2] // 2
        y1 = room1[1] + room1[3] // 2
        x2 = room2[0] + room2[2] // 2
        y2 = room2[1] + room2[3] // 2

        # Determine corridor width based on configured probabilities
        width = self._get_corridor_width()

        # Create L-shaped corridor with specified width
        if random.choice([True, False]):
            # Horizontal then vertical
            self._carve_corridor_segment(min(x1, x2), max(x1, x2), y1, y1, width, horizontal=True)
            self._carve_corridor_segment(x2, x2, min(y1, y2), max(y1, y2), width, horizontal=False)
        else:
            # Vertical then horizontal
            self._carve_corridor_segment(x1, x1, min(y1, y2), max(y1, y2), width, horizontal=False)
            self._carve_corridor_segment(min(x1, x2), max(x1, x2), y2, y2, width, horizontal=True)

    def _get_corridor_width(self) -> int:
        """Determine corridor width based on configured probabilities."""
        rand = random.random()

        # Get weights from config - FAIL if missing
        narrow_weight = GameConfig._get_required('room_generation.corridor_width_weights.narrow')
        medium_weight = GameConfig._get_required('room_generation.corridor_width_weights.medium')
        wide_weight = GameConfig._get_required('room_generation.corridor_width_weights.wide')

        # Select width based on cumulative probabilities
        if rand < narrow_weight:
            return 1
        elif rand < narrow_weight + medium_weight:
            return 2
        else:
            return 3

    def _carve_corridor_segment(self, x_start: int, x_end: int, y_start: int, y_end: int,
                                width: int, horizontal: bool) -> None:
        """Carve a corridor segment with specified width and track corridor tiles."""
        if horizontal:
            # Horizontal corridor - expand vertically
            for x in range(x_start, x_end + 1):
                for offset in range(-(width // 2), (width + 1) // 2):
                    y = y_start + offset
                    if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((x, y))
                        self.corridor_tiles.add((x, y))  # Track corridor tile
        else:
            # Vertical corridor - expand horizontally
            for y in range(y_start, y_end + 1):
                for offset in range(-(width // 2), (width + 1) // 2):
                    x = x_start + offset
                    if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((x, y))
                        self.corridor_tiles.add((x, y))  # Track corridor tile

    def _add_corridor_alcoves(self) -> None:
        """Add alcoves to straight corridor segments for stealth hiding spots."""
        # Get alcove chance from config - FAIL if missing
        alcove_chance = GameConfig._get_required('room_generation.corridor_alcove_chance')
        min_segment_length = GameConfig._get_required('room_generation.corridor_alcove_min_length')

        # Find straight corridor segments
        horizontal_segments = self._find_straight_corridor_segments(horizontal=True)
        vertical_segments = self._find_straight_corridor_segments(horizontal=False)

        # Add alcoves to eligible segments
        for segment in horizontal_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self._create_alcoves_on_segment(segment, horizontal=True)

        for segment in vertical_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self._create_alcoves_on_segment(segment, horizontal=False)

    def _find_straight_corridor_segments(self, horizontal: bool) -> List[List[Tuple[int, int]]]:
        """Find straight corridor segments (either horizontal or vertical)."""
        segments = []
        processed = set()

        for tile in self.corridor_tiles:
            if tile in processed:
                continue

            x, y = tile

            if horizontal:
                # Find horizontal segment starting from this tile
                segment = []
                # Scan left to find start
                start_x = x
                while (start_x - 1, y) in self.corridor_tiles:
                    start_x -= 1

                # Scan right to build segment
                curr_x = start_x
                while (curr_x, y) in self.corridor_tiles:
                    if (curr_x, y) not in processed:
                        segment.append((curr_x, y))
                        processed.add((curr_x, y))
                    curr_x += 1

                if len(segment) > 0:
                    segments.append(segment)
            else:
                # Find vertical segment starting from this tile
                segment = []
                # Scan up to find start
                start_y = y
                while (x, start_y - 1) in self.corridor_tiles:
                    start_y -= 1

                # Scan down to build segment
                curr_y = start_y
                while (x, curr_y) in self.corridor_tiles:
                    if (x, curr_y) not in processed:
                        segment.append((x, curr_y))
                        processed.add((x, curr_y))
                    curr_y += 1

                if len(segment) > 0:
                    segments.append(segment)

        return segments

    def _create_alcoves_on_segment(self, segment: List[Tuple[int, int]], horizontal: bool) -> None:
        """Create 1-2 alcoves along a corridor segment."""
        if len(segment) < 4:
            return

        # Determine how many alcoves to place (1-2)
        num_alcoves = random.randint(1, min(2, len(segment) // 4))

        # Select random positions along the segment (avoid first and last tiles)
        valid_positions = segment[1:-1]  # Exclude endpoints
        if len(valid_positions) < num_alcoves:
            return

        alcove_positions = random.sample(valid_positions, num_alcoves)

        for pos in alcove_positions:
            x, y = pos

            if horizontal:
                # Horizontal corridor - add alcove above or below
                direction = random.choice([-1, 1])
                alcove_pos = (x, y + direction)
            else:
                # Vertical corridor - add alcove left or right
                direction = random.choice([-1, 1])
                alcove_pos = (x + direction, y)

            # Check if alcove position is valid (is currently a wall, not out of bounds)
            if (0 <= alcove_pos[0] < GameConfig.MAP_WIDTH and
                0 <= alcove_pos[1] < GameConfig.MAP_HEIGHT and
                alcove_pos in self.game_map.walls):

                # Carve the alcove
                self.game_map.walls.discard(alcove_pos)

                # Place a shadow in the alcove for stealth gameplay
                self.game_map.shadows.add(alcove_pos)

    def _add_cover_elements_new(self) -> None:
        """Add strategic cover clusters in open areas using Poisson disc sampling."""
        # Get config values
        min_open_area_size = GameConfig._get_required('room_generation.cover_min_open_area_size')
        cluster_chance = GameConfig._get_required('room_generation.cover_cluster_chance')
        poisson_radius = GameConfig._get_required('room_generation.cover_poisson_radius')

        # Find large open areas (10x10+ contiguous floor space)
        open_areas = self._find_large_open_areas(min_open_area_size)

        # Place cover clusters in some open areas
        for area in open_areas:
            if random.random() < cluster_chance:
                # Use Poisson disc sampling for natural distribution
                cluster_positions = self._poisson_disc_sampling(area, poisson_radius)

                # Create cover clusters at sampled positions
                for pos in cluster_positions:
                    self._create_cover_cluster(pos)

    def _find_large_open_areas(self, min_size: int) -> List[Tuple[int, int, int, int]]:
        """Find large contiguous open floor areas (x, y, width, height)."""
        open_areas = []

        # Simple grid-based search for open rectangles
        for y in range(5, GameConfig.MAP_HEIGHT - min_size - 5, min_size):
            for x in range(5, GameConfig.MAP_WIDTH - min_size - 5, min_size):
                # Check if this position starts a large open area
                max_width = 0
                max_height = 0

                # Find maximum width at this y
                for w in range(min_size, GameConfig.MAP_WIDTH - x):
                    if (x + w, y) in self.game_map.walls:
                        break
                    max_width = w + 1

                # Find maximum height at this x
                for h in range(min_size, GameConfig.MAP_HEIGHT - y):
                    if (x, y + h) in self.game_map.walls:
                        break
                    max_height = h + 1

                # Check if we have a large enough rectangular area
                if max_width >= min_size and max_height >= min_size:
                    # Verify the rectangle is mostly open
                    open_tiles = 0
                    total_tiles = max_width * max_height
                    for dy in range(max_height):
                        for dx in range(max_width):
                            if (x + dx, y + dy) not in self.game_map.walls:
                                open_tiles += 1

                    # If at least 70% open, consider it an open area
                    if open_tiles >= total_tiles * 0.7:
                        open_areas.append((x, y, max_width, max_height))

        return open_areas

    def _poisson_disc_sampling(self, area: Tuple[int, int, int, int], radius: float) -> List[Tuple[int, int]]:
        """
        Generate points using Poisson disc sampling for natural distribution.
        Points are guaranteed to be at least 'radius' distance apart.
        """
        x_start, y_start, width, height = area
        points = []

        # Check if area is too small for sampling
        if width < 5 or height < 5:
            return points

        # Simplified Poisson disc sampling using rejection method
        max_attempts = 30
        k_attempts = 0

        # Try to place 2-4 points depending on area size
        num_points = min(4, max(2, (width * height) // 100))

        for _ in range(num_points):
            for attempt in range(max_attempts):
                # Random point in area (with bounds checking)
                max_x = x_start + width - 3
                max_y = y_start + height - 3
                if max_x <= x_start + 2 or max_y <= y_start + 2:
                    break  # Area too small

                px = random.randint(x_start + 2, max_x)
                py = random.randint(y_start + 2, max_y)

                # Check distance to existing points
                valid = True
                for ex_x, ex_y in points:
                    dist = math.sqrt((px - ex_x) ** 2 + (py - ex_y) ** 2)
                    if dist < radius:
                        valid = False
                        break

                if valid and (px, py) not in self.game_map.walls:
                    points.append((px, py))
                    break

        return points

    def _create_cover_cluster(self, center: Tuple[int, int]) -> None:
        """Create a cluster of cover walls at the specified position."""
        x, y = center

        # Randomly select cluster pattern
        cluster_type = random.choice(['small', 'l_shaped', 'scattered'])

        if cluster_type == 'small':
            # Small 2x2 cluster
            for dx in range(2):
                for dy in range(2):
                    pos = (x + dx, y + dy)
                    if self._is_valid_cover_position(pos):
                        self.game_map.walls.add(pos)

        elif cluster_type == 'l_shaped':
            # L-shaped cover
            positions = [(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x, y + 2)]
            for pos in positions:
                if self._is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

        elif cluster_type == 'scattered':
            # Scattered 5-6 tile cluster
            positions = [
                (x, y), (x + 2, y), (x + 1, y + 1),
                (x, y + 2), (x + 2, y + 2)
            ]
            for pos in positions:
                if self._is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

    def _is_valid_cover_position(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is valid for placing cover."""
        x, y = pos

        # Must be within bounds
        if not (0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT):
            return False

        # Must currently be floor
        if pos in self.game_map.walls:
            return False

        # Must not be in a corridor (corridors need to stay clear)
        if pos in self.corridor_tiles:
            return False

        # Must not be too close to existing special nodes
        if (pos in self.game_map.cooling_nodes or
            pos in self.game_map.cpu_recovery_nodes or
            pos in self.game_map.ghost_nodes):
            return False

        return True
    
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
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        # Helper function to get required config value
        def get_required_config(key: str) -> int:
            if key not in config:
                error_msg = f"CRITICAL CONFIG ERROR: '{key}' missing for level {level} in game_data.json network_configs"
                logging.error(error_msg)
                logging.error(f"Available config keys for level {level}: {list(config.keys())}")
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