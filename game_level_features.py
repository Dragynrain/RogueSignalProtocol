"""
Level feature generation: tactical elements, advanced layout, and special tile placement.

This module handles strategic feature placement for procedural levels:

TACTICAL GENERATION:
- Shadow placement (wall-adjacent and interior) for stealth gameplay
- Cover element clusters using Poisson disc sampling
- Defensive positions (corner cover, shadow bunkers, crossfire setups)
- Choke points by narrowing corridors in strategic locations
- Shadow cleanup to prevent invalid placements

ADVANCED LAYOUT:
- Hub-and-spoke patterns (central hub rooms with multiple connections)
- Looping paths for stealth and multiple routes
- Shadow zones (clusters of rooms with high shadow coverage)
- Landmark rooms (distinctive themed areas: server core, vault, junction, maze, arena)
- Map zones for different gameplay pacing (linear vs open sections)
- Loot room identification for item clustering

TILE PLACEMENT:
- Special tiles (cooling nodes, CPU recovery nodes, ghost nodes)
- Gateway placement using various strategies
- Border wall enforcement
- Objective-oriented placement based on level geography

Tactical elements provide:
- Stealth opportunities (shadows for hiding)
- Combat advantages (cover for protection)
- Strategic positioning (defensive setups)
- Bottleneck control (choke points)

Gateway strategies:
- Far Corner: Opposite corner from spawn, maximum distance
- Central Hub: Near map center, creates central objective
- Hidden Dead End: At end of longest branch, rewards exploration
- Gauntlet: Along edge, requires crossing the entire map
"""

import random
import logging
import math
from typing import List, Tuple, Dict, Set, Optional

from game_config import GameConfig
from game_entities import Position


# ============================================================================
# TACTICAL GENERATION
# ============================================================================

class TacticalGenerator:
    """
    Tactical features subsystem handling shadows, cover, and defensive elements.

    Coordinates placement of stealth and combat-related features throughout
    the level to support various playstyles.

    Attributes:
        game_map: GameMap instance to populate with tactical features
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
    """

    def __init__(self, game_map, corridor_tiles: Set[Tuple[int, int]]):
        """
        Initialize tactical generator with game map and corridor tracking.

        Args:
            game_map: GameMap instance to modify during tactical feature generation
            corridor_tiles: Set of corridor tile positions (used for cover validation)
        """
        self.game_map = game_map
        self.corridor_tiles = corridor_tiles

    def place_shadow_areas(self, level: int, rooms: List[Tuple[int, int, int, int]],
                          shadow_zone_rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Place shadow areas for stealth gameplay with wall-adjacent preference and shadow zones.

        Shadows are placed using weighted distribution:
        - Wall-adjacent positions (preferred for realistic lighting)
        - Interior positions (for larger shadow areas)

        Shadow zones have higher coverage for stealth-focused areas.

        Args:
            level: Current level number (affects shadow coverage)
            rooms: List of room tuples (x, y, width, height)
            shadow_zone_rooms: List of rooms designated as shadow zones
        """
        network_configs = GameConfig.NETWORK_CONFIGS()

        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        if 'shadow_coverage' not in config:
            error_msg = f"CRITICAL CONFIG ERROR: 'shadow_coverage' missing for level {level} in game_data.json network_configs"
            logging.error(error_msg)
            logging.error(f"Available config keys for level {level}: {list(config.keys())}")
            raise KeyError(f"Required key 'shadow_coverage' missing from level {level} config")

        shadow_coverage = config['shadow_coverage']

        wall_adjacent_weight = GameConfig._get_required('room_generation.shadow_placement_weights.wall_adjacent')
        interior_weight = GameConfig._get_required('room_generation.shadow_placement_weights.interior')

        total_floor_tiles = sum(w * h for x, y, w, h in rooms)
        target_shadow_tiles = int(total_floor_tiles * shadow_coverage)

        placed_shadows = 0
        for room in rooms:
            if placed_shadows >= target_shadow_tiles:
                break

            x, y, width, height = room

            if room in shadow_zone_rooms:
                zone_coverage = GameConfig._get_required('room_generation.shadow_zone_coverage')
                shadows_in_room = int(width * height * zone_coverage)
            else:
                shadows_in_room = min(target_shadow_tiles - placed_shadows, width * height // 3)

            wall_adjacent_positions = self.get_wall_adjacent_positions(room)
            interior_positions = self.get_interior_positions(room)

            for _ in range(shadows_in_room):
                if random.random() < wall_adjacent_weight:
                    if wall_adjacent_positions:
                        shadow_pos = random.choice(wall_adjacent_positions)
                        wall_adjacent_positions.remove(shadow_pos)
                    elif interior_positions:
                        shadow_pos = random.choice(interior_positions)
                        interior_positions.remove(shadow_pos)
                    else:
                        continue
                else:
                    if interior_positions:
                        shadow_pos = random.choice(interior_positions)
                        interior_positions.remove(shadow_pos)
                    elif wall_adjacent_positions:
                        shadow_pos = random.choice(wall_adjacent_positions)
                        wall_adjacent_positions.remove(shadow_pos)
                    else:
                        continue

                if shadow_pos not in self.game_map.walls:
                    self.game_map.shadows.add(shadow_pos)
                    placed_shadows += 1

    def get_wall_adjacent_positions(self, room: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
        """
        Get floor positions that are adjacent to walls (1 tile from wall).

        Wall-adjacent positions are preferred for shadow placement as they
        represent realistic lighting/shadow behavior.

        Args:
            room: Room tuple (x, y, width, height)

        Returns:
            List of (x, y) positions adjacent to walls
        """
        x, y, width, height = room
        wall_adjacent = []

        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    continue

                adjacent_to_wall = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (rx + dx, ry + dy)
                    if neighbor in self.game_map.walls:
                        adjacent_to_wall = True
                        break

                if adjacent_to_wall:
                    wall_adjacent.append((rx, ry))

        return wall_adjacent

    def get_interior_positions(self, room: Tuple[int, int, int, int]) -> List[Tuple[int, int]]:
        """
        Get floor positions that are NOT adjacent to walls (interior tiles).

        Interior positions are used for larger shadow areas in open spaces.

        Args:
            room: Room tuple (x, y, width, height)

        Returns:
            List of (x, y) interior positions
        """
        x, y, width, height = room
        interior = []

        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    continue

                adjacent_to_wall = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (rx + dx, ry + dy)
                    if neighbor in self.game_map.walls:
                        adjacent_to_wall = True
                        break

                if not adjacent_to_wall:
                    interior.append((rx, ry))

        return interior

    def cleanup_invalid_shadows(self) -> None:
        """
        Remove any shadows that ended up on walls.

        Can happen when cover is placed after shadows. Ensures shadows
        never overlap with walls for proper rendering and gameplay.
        """
        invalid_shadows = []
        for shadow_pos in self.game_map.shadows:
            if shadow_pos in self.game_map.walls:
                invalid_shadows.append(shadow_pos)

        for shadow_pos in invalid_shadows:
            self.game_map.shadows.remove(shadow_pos)

    def add_cover_elements_new(self) -> None:
        """
        Add strategic cover clusters in open areas using Poisson disc sampling.

        Cover provides:
        - Tactical positioning during combat
        - Line-of-sight breaking
        - Strategic gameplay options

        Uses Poisson disc sampling for natural, evenly-distributed placement.
        """
        min_open_area_size = GameConfig._get_required('room_generation.cover_min_open_area_size')
        cluster_chance = GameConfig._get_required('room_generation.cover_cluster_chance')
        poisson_radius = GameConfig._get_required('room_generation.cover_poisson_radius')

        open_areas = self.find_large_open_areas(min_open_area_size)

        for area in open_areas:
            if random.random() < cluster_chance:
                cluster_positions = self.poisson_disc_sampling(area, poisson_radius)

                for pos in cluster_positions:
                    self.create_cover_cluster(pos)

    def find_large_open_areas(self, min_size: int) -> List[Tuple[int, int, int, int]]:
        """
        Find large contiguous open floor areas.

        Identifies open rectangles suitable for cover placement.

        Args:
            min_size: Minimum size (width and height) for an area to be considered

        Returns:
            List of area tuples (x, y, width, height)
        """
        open_areas = []

        for y in range(5, GameConfig.MAP_HEIGHT - min_size - 5, min_size):
            for x in range(5, GameConfig.MAP_WIDTH - min_size - 5, min_size):
                max_width = 0
                max_height = 0

                for w in range(min_size, GameConfig.MAP_WIDTH - x):
                    if (x + w, y) in self.game_map.walls:
                        break
                    max_width = w + 1

                for h in range(min_size, GameConfig.MAP_HEIGHT - y):
                    if (x, y + h) in self.game_map.walls:
                        break
                    max_height = h + 1

                if max_width >= min_size and max_height >= min_size:
                    open_tiles = 0
                    total_tiles = max_width * max_height
                    for dy in range(max_height):
                        for dx in range(max_width):
                            if (x + dx, y + dy) not in self.game_map.walls:
                                open_tiles += 1

                    if open_tiles >= total_tiles * 0.7:
                        open_areas.append((x, y, max_width, max_height))

        return open_areas

    def poisson_disc_sampling(self, area: Tuple[int, int, int, int], radius: float) -> List[Tuple[int, int]]:
        """
        Generate points using Poisson disc sampling for natural distribution.

        Points are guaranteed to be at least 'radius' distance apart,
        creating a natural, evenly-spaced distribution.

        Args:
            area: Area tuple (x, y, width, height) to sample within
            radius: Minimum distance between points

        Returns:
            List of (x, y) sampled positions
        """
        x_start, y_start, width, height = area
        points = []

        if width < 5 or height < 5:
            return points

        max_attempts = 30
        k_attempts = 0

        num_points = min(4, max(2, (width * height) // 100))

        for _ in range(num_points):
            for attempt in range(max_attempts):
                max_x = x_start + width - 3
                max_y = y_start + height - 3
                if max_x <= x_start + 2 or max_y <= y_start + 2:
                    break

                px = random.randint(x_start + 2, max_x)
                py = random.randint(y_start + 2, max_y)

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

    def create_cover_cluster(self, center: Tuple[int, int]) -> None:
        """
        Create a cluster of cover walls at the specified position.

        Cover clusters come in three patterns:
        - Small: 2x2 compact cluster
        - L-shaped: L-shaped cover for corner protection
        - Scattered: 5-6 tile spread-out cluster

        Args:
            center: Center position (x, y) for the cluster
        """
        x, y = center

        cluster_type = random.choice(['small', 'l_shaped', 'scattered'])

        if cluster_type == 'small':
            for dx in range(2):
                for dy in range(2):
                    pos = (x + dx, y + dy)
                    if self.is_valid_cover_position(pos):
                        self.game_map.walls.add(pos)

        elif cluster_type == 'l_shaped':
            positions = [(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x, y + 2)]
            for pos in positions:
                if self.is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

        elif cluster_type == 'scattered':
            positions = [
                (x, y), (x + 2, y), (x + 1, y + 1),
                (x, y + 2), (x + 2, y + 2)
            ]
            for pos in positions:
                if self.is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

    def is_valid_cover_position(self, pos: Tuple[int, int]) -> bool:
        """
        Check if a position is valid for placing cover.

        Cover must:
        - Be within bounds
        - Be on floor (not wall)
        - Not be in corridor (keep corridors clear)
        - Not overlap special nodes

        Args:
            pos: Position (x, y) to check

        Returns:
            True if position is valid for cover placement
        """
        x, y = pos

        if not (0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT):
            return False

        if pos in self.game_map.walls:
            return False

        if pos in self.corridor_tiles:
            return False

        if (pos in self.game_map.cooling_nodes or
            pos in self.game_map.cpu_recovery_nodes or
            pos in self.game_map.ghost_nodes):
            return False

        return True

    def place_defensive_positions(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Place defensive positions (cover + shadow combinations) in strategic locations.

        Defensive positions provide:
        - Pre-positioned tactical advantages
        - Combined cover and stealth
        - Strategic holdout locations

        Placed in:
        - Large rooms
        - Near strategic objectives
        - High-traffic areas

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        defensive_chance = GameConfig._get_required('room_generation.defensive_position_chance')
        position_types = GameConfig._get_required('room_generation.defensive_position_types')

        strategic_rooms = []

        for room in rooms:
            x, y, w, h = room
            area = w * h
            if area >= 50:
                strategic_rooms.append(room)

        num_positions = min(random.randint(1, 3), len(strategic_rooms))

        for _ in range(num_positions):
            if not strategic_rooms:
                break

            room = random.choice(strategic_rooms)
            strategic_rooms.remove(room)

            position_type = random.choice(position_types)

            self.create_defensive_position(room, position_type)

    def create_defensive_position(self, room: Tuple[int, int, int, int], position_type: str) -> None:
        """
        Create a specific type of defensive position within a room.

        Combines cover walls and shadow placement for tactical advantage.

        Args:
            room: Room tuple (x, y, width, height)
            position_type: Type of defensive position ('corner_cover', 'shadow_bunker', 'crossfire')
        """
        x, y, w, h = room

        if w < 6 or h < 6:
            return

        center_x = x + w // 2
        center_y = y + h // 2

        offset_x = random.randint(-2, 2)
        offset_y = random.randint(-2, 2)
        pos_x = max(x + 2, min(x + w - 3, center_x + offset_x))
        pos_y = max(y + 2, min(y + h - 3, center_y + offset_y))

        if position_type == 'corner_cover':
            self.create_corner_cover_position(pos_x, pos_y)
        elif position_type == 'shadow_bunker':
            self.create_shadow_bunker_position(pos_x, pos_y)
        elif position_type == 'crossfire':
            self.create_crossfire_position(pos_x, pos_y)

    def create_corner_cover_position(self, x: int, y: int) -> None:
        """
        Corner Cover: L-shaped cover with shadow in the corner.

        Pattern:
        ##S
        #..

        Args:
            x: X position for the corner
            y: Y position for the corner
        """
        cover_positions = [(x, y), (x + 1, y), (x, y + 1)]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        shadow_pos = (x + 1, y + 1)
        if shadow_pos not in self.game_map.walls:
            self.game_map.shadows.add(shadow_pos)

    def create_shadow_bunker_position(self, x: int, y: int) -> None:
        """
        Shadow Bunker: 3-sided cover with shadow inside.

        Pattern:
        ###
        #S#
        .#.

        Args:
            x: X position for the bunker
            y: Y position for the bunker
        """
        cover_positions = [
            (x, y), (x + 1, y), (x + 2, y),
            (x, y + 1), (x + 2, y + 1),
            (x + 1, y + 2)
        ]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        shadow_pos = (x + 1, y + 1)
        if shadow_pos not in self.game_map.walls:
            self.game_map.shadows.add(shadow_pos)

    def create_crossfire_position(self, x: int, y: int) -> None:
        """
        Crossfire: Two separated cover pieces with shadows, creates crossfire opportunity.

        Pattern:
        #S...S#

        Args:
            x: X position for the crossfire setup
            y: Y position for the crossfire setup
        """
        cover_positions = [(x, y), (x + 4, y)]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        shadow_positions = [(x + 1, y), (x + 3, y)]
        for pos in shadow_positions:
            if pos not in self.game_map.walls:
                self.game_map.shadows.add(pos)

    def create_choke_points(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Create choke points by narrowing corridors near strategic rooms.

        Choke points are bottleneck areas that force tension in gameplay by:
        - Limiting movement options
        - Creating predictable enemy paths
        - Forcing tactical decisions

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        choke_point_count = GameConfig._get_required('room_generation.choke_point_count')
        max_exits = GameConfig._get_required('room_generation.choke_point_max_exits')

        if not self.corridor_tiles:
            return

        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        central_corridors = []
        for tile in self.corridor_tiles:
            x, y = tile
            distance_to_center = abs(x - map_center_x) + abs(y - map_center_y)
            if distance_to_center < 20:
                central_corridors.append(tile)

        if not central_corridors:
            return

        num_chokes = min(choke_point_count, len(central_corridors) // 10)
        choke_positions = random.sample(central_corridors, min(num_chokes, len(central_corridors)))

        for choke_pos in choke_positions:
            self.narrow_corridor_at_position(choke_pos)

    def narrow_corridor_at_position(self, position: Tuple[int, int]) -> None:
        """
        Narrow a corridor at the given position by adding walls on sides.

        Creates a bottleneck effect by reducing corridor width.

        Args:
            position: Position (x, y) to narrow
        """
        x, y = position

        has_horizontal_flow = ((x - 1, y) in self.corridor_tiles or (x + 1, y) in self.corridor_tiles)
        has_vertical_flow = ((x, y - 1) in self.corridor_tiles or (x, y + 1) in self.corridor_tiles)

        if has_horizontal_flow and not has_vertical_flow:
            if (x, y + 1) not in self.game_map.walls and (x, y + 1) in self.corridor_tiles:
                self.game_map.walls.add((x, y + 1))
                self.corridor_tiles.discard((x, y + 1))
            if (x, y - 1) not in self.game_map.walls and (x, y - 1) in self.corridor_tiles:
                self.game_map.walls.add((x, y - 1))
                self.corridor_tiles.discard((x, y - 1))

        elif has_vertical_flow and not has_horizontal_flow:
            if (x + 1, y) not in self.game_map.walls and (x + 1, y) in self.corridor_tiles:
                self.game_map.walls.add((x + 1, y))
                self.corridor_tiles.discard((x + 1, y))
            if (x - 1, y) not in self.game_map.walls and (x - 1, y) in self.corridor_tiles:
                self.game_map.walls.add((x - 1, y))
                self.corridor_tiles.discard((x - 1, y))


# ============================================================================
# ADVANCED LAYOUT GENERATION
# ============================================================================

class AdvancedLayoutGenerator:
    """
    Advanced layout subsystem handling complex architectural features.

    Coordinates hub rooms, looping paths, shadow zones, landmark rooms,
    and zone-based map division.

    Attributes:
        game_map: GameMap instance to populate with advanced features
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
        room_generator: Reference to RoomGenerator for room carving
        corridor_generator: Reference to CorridorGenerator for connections
        tactical_generator: Reference to TacticalGenerator for cover/shadows
    """

    def __init__(self, game_map, corridor_tiles, room_generator, corridor_generator, tactical_generator):
        """
        Initialize advanced layout generator with references to other subsystems.

        Args:
            game_map: GameMap instance to modify
            corridor_tiles: Set of corridor tile positions
            room_generator: RoomGenerator instance for room carving
            corridor_generator: CorridorGenerator instance for connections
            tactical_generator: TacticalGenerator instance for cover/shadows
        """
        self.game_map = game_map
        self.corridor_tiles = corridor_tiles
        self.room_generator = room_generator
        self.corridor_generator = corridor_generator
        self.tactical_generator = tactical_generator

    def identify_hub_rooms(self, rooms: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Identify 1-2 central rooms to become hub rooms.

        Hub rooms will be expanded and have more connections, creating
        a hub-and-spoke navigation pattern.

        Args:
            rooms: List of room tuples (x, y, width, height)

        Returns:
            List of expanded hub room tuples
        """
        if len(rooms) < 5:
            return []

        hub_count = GameConfig._get_required('room_generation.hub_room_count')

        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        room_centrality = []
        for room in rooms:
            x, y, w, h = room
            room_center_x = x + w // 2
            room_center_y = y + h // 2
            distance_to_center = abs(room_center_x - map_center_x) + abs(room_center_y - map_center_y)
            room_centrality.append((distance_to_center, room))

        room_centrality.sort(key=lambda item: item[0])
        hub_rooms = [room for _, room in room_centrality[:hub_count]]

        expanded_hubs = []
        for room in hub_rooms:
            expanded_room = self.expand_hub_room(room)
            expanded_hubs.append(expanded_room)

        return expanded_hubs

    def expand_hub_room(self, room: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """
        Expand a hub room to make it larger and more prominent.

        Args:
            room: Room tuple (x, y, width, height) to expand

        Returns:
            Expanded room tuple (x, y, width, height)
        """
        x, y, w, h = room
        multiplier = GameConfig._get_required('room_generation.hub_room_size_multiplier')

        new_w = int(w * multiplier)
        new_h = int(h * multiplier)

        new_x = max(1, x - (new_w - w) // 2)
        new_y = max(1, y - (new_h - h) // 2)

        if new_x + new_w >= GameConfig.MAP_WIDTH - 1:
            new_x = GameConfig.MAP_WIDTH - new_w - 1
        if new_y + new_h >= GameConfig.MAP_HEIGHT - 1:
            new_y = GameConfig.MAP_HEIGHT - new_h - 1

        expanded_room = (new_x, new_y, new_w, new_h)
        self.room_generator.carve_rectangular_room(expanded_room)

        return expanded_room

    def connect_hub_rooms(self, hub_rooms: List[Tuple[int, int, int, int]],
                         all_rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Create hub-and-spoke pattern by connecting hub rooms to multiple other rooms.

        Each hub gets connected to several nearby rooms, creating a central
        navigation node.

        Args:
            hub_rooms: List of hub room tuples
            all_rooms: List of all room tuples in the level
        """
        if not hub_rooms:
            return

        min_connections = GameConfig._get_required('room_generation.hub_min_connections')
        max_connections = GameConfig._get_required('room_generation.hub_max_connections')

        for hub in hub_rooms:
            hub_center_x = hub[0] + hub[2] // 2
            hub_center_y = hub[1] + hub[3] // 2

            room_distances = []
            for room in all_rooms:
                if room == hub or room in hub_rooms:
                    continue
                room_center_x = room[0] + room[2] // 2
                room_center_y = room[1] + room[3] // 2
                distance = abs(hub_center_x - room_center_x) + abs(hub_center_y - room_center_y)
                room_distances.append((distance, room))

            room_distances.sort(key=lambda item: item[0])
            num_connections = random.randint(min_connections, max_connections)

            for i in range(min(num_connections, len(room_distances))):
                _, target_room = room_distances[i]
                self.corridor_generator.create_corridor_between_rooms(hub, target_room)

    def create_looping_paths(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Create looping paths by identifying leaf nodes and adding connections to create cycles.

        Loops provide:
        - Multiple approach routes
        - Stealth escape options
        - Tactical flanking opportunities

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        if len(rooms) < 4:
            return

        connectivity = self.build_room_connectivity_graph(rooms)

        leaf_rooms = [room for room in rooms if connectivity.get(room, 0) <= 1]

        min_loops = GameConfig._get_required('room_generation.looping_paths_min_loops')
        max_loops = GameConfig._get_required('room_generation.looping_paths_max_loops')
        target_loops = random.randint(min_loops, max_loops)

        loops_created = 0
        extra_connections = GameConfig._get_required('room_generation.looping_paths_extra_connections')

        for _ in range(extra_connections):
            if loops_created >= target_loops:
                break

            candidates = [room for room in rooms if connectivity.get(room, 0) < 4]
            if len(candidates) < 2:
                break

            room1 = random.choice(candidates)
            room2 = random.choice([r for r in candidates if r != room1])

            self.corridor_generator.create_corridor_between_rooms(room1, room2)
            connectivity[room1] = connectivity.get(room1, 0) + 1
            connectivity[room2] = connectivity.get(room2, 0) + 1
            loops_created += 1

    def build_room_connectivity_graph(self, rooms: List[Tuple[int, int, int, int]]) -> Dict[Tuple[int, int, int, int], int]:
        """
        Build a simple connectivity graph showing how many connections each room has.

        This is an approximation based on proximity and corridor tiles.

        Args:
            rooms: List of room tuples (x, y, width, height)

        Returns:
            Dictionary mapping room tuples to connection counts
        """
        connectivity = {}

        for room in rooms:
            x, y, w, h = room
            adjacent_corridors = 0

            for rx in range(x - 1, x + w + 1):
                if (rx, y - 1) in self.corridor_tiles or (rx, y + h) in self.corridor_tiles:
                    adjacent_corridors += 1
            for ry in range(y - 1, y + h + 1):
                if (x - 1, ry) in self.corridor_tiles or (x + w, ry) in self.corridor_tiles:
                    adjacent_corridors += 1

            estimated_connections = max(1, adjacent_corridors // 3)
            connectivity[room] = estimated_connections

        return connectivity

    def create_shadow_zones(self, rooms: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Identify room clusters and designate some as shadow zones.

        Shadow zones have higher shadow coverage, creating stealth-focused areas.

        Args:
            rooms: List of room tuples (x, y, width, height)

        Returns:
            List of room tuples designated as shadow zones
        """
        shadow_zone_chance = GameConfig._get_required('room_generation.shadow_zone_chance')
        min_cluster_size = GameConfig._get_required('room_generation.shadow_zone_room_cluster_min')

        clusters = self.find_room_clusters(rooms, min_cluster_size)

        shadow_zone_rooms = []
        for cluster in clusters:
            if random.random() < shadow_zone_chance:
                shadow_zone_rooms.extend(cluster)

        return shadow_zone_rooms

    def find_room_clusters(self, rooms: List[Tuple[int, int, int, int]], min_size: int) -> List[List[Tuple[int, int, int, int]]]:
        """
        Find clusters of nearby rooms using simple proximity-based clustering.

        Args:
            rooms: List of room tuples (x, y, width, height)
            min_size: Minimum number of rooms to form a cluster

        Returns:
            List of clusters, where each cluster is a list of room tuples
        """
        clusters = []
        unclustered = set(rooms)
        proximity_threshold = 15

        while unclustered:
            seed = unclustered.pop()
            cluster = [seed]

            changed = True
            while changed:
                changed = False
                to_add = []

                for room in unclustered:
                    for cluster_room in cluster:
                        if self.room_distance(room, cluster_room) < proximity_threshold:
                            to_add.append(room)
                            changed = True
                            break

                for room in to_add:
                    unclustered.discard(room)
                    cluster.append(room)

            if len(cluster) >= min_size:
                clusters.append(cluster)

        return clusters

    def room_distance(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]) -> int:
        """
        Calculate Manhattan distance between room centers.

        Args:
            room1: First room tuple (x, y, width, height)
            room2: Second room tuple (x, y, width, height)

        Returns:
            Manhattan distance between room centers
        """
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2
        center1_x = x1 + w1 // 2
        center1_y = y1 + h1 // 2
        center2_x = x2 + w2 // 2
        center2_y = y2 + h2 // 2
        return abs(center1_x - center2_x) + abs(center1_y - center2_y)

    def create_landmark_rooms(self, level: int, rooms: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        Create 1-2 distinctive landmark rooms per level.

        Landmark types:
        - Server Core: Large circular room with pillars
        - Vault: Small secured room at corridor end
        - Junction: Massive cross-shaped hub
        - Maze: Dense cluster of small rooms
        - Arena: Large open combat area

        Args:
            level: Current level number
            rooms: List of existing room tuples

        Returns:
            List of landmark room definitions with positions for special item placement
        """
        if not GameConfig._get_required('room_generation.enable_landmarks'):
            return []

        if len(rooms) < 5:
            return []

        num_landmarks = random.randint(1, 2)
        landmark_types = random.sample(['server_core', 'vault', 'junction', 'maze', 'arena'], num_landmarks)

        landmark_rooms = []
        for landmark_type in landmark_types:
            landmark_data = self.create_landmark_room(landmark_type, rooms, level)
            if landmark_data:
                landmark_rooms.append(landmark_data)

        return landmark_rooms

    def create_landmark_room(self, landmark_type: str, existing_rooms: List[Tuple[int, int, int, int]],
                            level: int) -> Optional[Dict]:
        """
        Create a specific landmark room type.

        Args:
            landmark_type: Type of landmark ('server_core', 'vault', 'junction', 'maze', 'arena')
            existing_rooms: List of existing room tuples
            level: Current level number

        Returns:
            Dictionary with 'type', 'position', 'room', and 'description', or None if placement failed
        """
        if landmark_type == 'server_core':
            return self.create_server_core_landmark(existing_rooms, level)
        elif landmark_type == 'vault':
            return self.create_vault_landmark(existing_rooms)
        elif landmark_type == 'junction':
            return self.create_junction_landmark(existing_rooms)
        elif landmark_type == 'maze':
            return self.create_maze_landmark(existing_rooms)
        elif landmark_type == 'arena':
            return self.create_arena_landmark(existing_rooms)

        return None

    def create_server_core_landmark(self, existing_rooms: List[Tuple[int, int, int, int]],
                                   level: int) -> Optional[Dict]:
        """
        The Server Core: Large circular room with pillar pattern, gateway often inside.

        Args:
            existing_rooms: List of existing room tuples
            level: Current level number

        Returns:
            Landmark definition dictionary or None
        """
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        size = 10
        x = map_center_x - size // 2
        y = map_center_y - size // 2

        room = (x, y, size, size)

        if self.room_generator.room_overlaps(room, existing_rooms):
            return None

        self.room_generator.carve_circular_room(room)

        self.room_generator.apply_pillar_pattern(room, level)

        return {
            'type': 'server_core',
            'room': room,
            'position': (x + size // 2, y + size // 2),
            'description': 'Server Core - Large circular room with server pillars'
        }

    def create_vault_landmark(self, existing_rooms: List[Tuple[int, int, int, int]]) -> Optional[Dict]:
        """
        The Vault: Small room at the end of a narrow corridor with upgrade.

        Args:
            existing_rooms: List of existing room tuples

        Returns:
            Landmark definition dictionary or None
        """
        edge_rooms = [r for r in existing_rooms
                     if r[0] < 15 or r[0] > GameConfig.MAP_WIDTH - 15 or
                        r[1] < 15 or r[1] > GameConfig.MAP_HEIGHT - 15]

        if not edge_rooms:
            return None

        vault_base = random.choice(edge_rooms)
        x, y, w, h = vault_base

        vault_size = 4
        vault_x = x + w + 5
        vault_y = y

        vault_room = (vault_x, vault_y, vault_size, vault_size)

        if self.room_generator.room_overlaps(vault_room, existing_rooms):
            return None

        self.room_generator.carve_rectangular_room(vault_room)

        self.corridor_generator.create_corridor_between_rooms(vault_base, vault_room)

        return {
            'type': 'vault',
            'room': vault_room,
            'position': (vault_x + vault_size // 2, vault_y + vault_size // 2),
            'description': 'Vault - Small secured room with valuable items'
        }

    def create_junction_landmark(self, existing_rooms: List[Tuple[int, int, int, int]]) -> Optional[Dict]:
        """
        The Junction: Massive cross-shaped room connecting 6+ other rooms.

        Args:
            existing_rooms: List of existing room tuples

        Returns:
            Landmark definition dictionary or None
        """
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        size = 12
        x = map_center_x - size // 2
        y = map_center_y - size // 2

        room = (x, y, size, size)

        if self.room_generator.room_overlaps(room, existing_rooms):
            return None

        self.room_generator.carve_cross_room(room)

        nearby_rooms = sorted(existing_rooms,
                            key=lambda r: abs((r[0] + r[2]//2) - map_center_x) +
                                        abs((r[1] + r[3]//2) - map_center_y))[:6]

        for nearby_room in nearby_rooms:
            self.corridor_generator.create_corridor_between_rooms(room, nearby_room)

        return {
            'type': 'junction',
            'room': room,
            'position': (x + size // 2, y + size // 2),
            'description': 'Junction - Major cross-shaped hub connecting multiple areas'
        }

    def create_maze_landmark(self, existing_rooms: List[Tuple[int, int, int, int]]) -> Optional[Dict]:
        """
        The Maze: Dense cluster of small rooms with many connections.

        Args:
            existing_rooms: List of existing room tuples

        Returns:
            Landmark definition dictionary or None
        """
        corner_x = random.choice([10, GameConfig.MAP_WIDTH - 20])
        corner_y = random.choice([10, GameConfig.MAP_HEIGHT - 20])

        maze_rooms = []
        for i in range(random.randint(4, 6)):
            offset_x = (i % 3) * 5
            offset_y = (i // 3) * 5
            small_room = (corner_x + offset_x, corner_y + offset_y, 4, 4)

            if not self.room_generator.room_overlaps(small_room, existing_rooms + maze_rooms):
                self.room_generator.carve_rectangular_room(small_room)
                maze_rooms.append(small_room)

        for i, room1 in enumerate(maze_rooms):
            for room2 in maze_rooms[i+1:]:
                if random.random() < 0.7:
                    self.corridor_generator.create_corridor_between_rooms(room1, room2)

        if not maze_rooms:
            return None

        center_room = maze_rooms[len(maze_rooms) // 2]

        return {
            'type': 'maze',
            'room': center_room,
            'position': (center_room[0] + center_room[2] // 2, center_room[1] + center_room[3] // 2),
            'description': 'Maze - Dense cluster of interconnected small rooms'
        }

    def create_arena_landmark(self, existing_rooms: List[Tuple[int, int, int, int]]) -> Optional[Dict]:
        """
        The Arena: Large open room with scattered cover, good for major fights.

        Args:
            existing_rooms: List of existing room tuples

        Returns:
            Landmark definition dictionary or None
        """
        arena_size = 14
        x = random.randint(15, GameConfig.MAP_WIDTH - arena_size - 15)
        y = random.randint(15, GameConfig.MAP_HEIGHT - arena_size - 15)

        room = (x, y, arena_size, arena_size)

        if self.room_generator.room_overlaps(room, existing_rooms):
            return None

        self.room_generator.carve_rectangular_room(room)

        cover_positions = self.tactical_generator.poisson_disc_sampling(room, 6.0)
        for pos in cover_positions:
            self.tactical_generator.create_cover_cluster(pos)

        return {
            'type': 'arena',
            'room': room,
            'position': (x + arena_size // 2, y + arena_size // 2),
            'description': 'Arena - Large open combat area with scattered cover'
        }

    def create_map_zones(self) -> List[Dict]:
        """
        Divide the map into zones with different connectivity characteristics.

        Zones can be:
        - Linear: Limited connections, forced progression
        - Open: Many connections, exploration encouraged

        Returns:
            List of zone definitions with their types and bounds
        """
        zone_count = GameConfig._get_required('room_generation.zone_count')
        zone_types = GameConfig._get_required('room_generation.zone_types')

        zones = []

        zone_height = GameConfig.MAP_HEIGHT // zone_count

        for i in range(zone_count):
            y_start = i * zone_height
            y_end = (i + 1) * zone_height if i < zone_count - 1 else GameConfig.MAP_HEIGHT

            zone_type = random.choice(zone_types)
            zones.append({
                'type': zone_type,
                'bounds': (0, y_start, GameConfig.MAP_WIDTH, y_end),
                'index': i
            })

        return zones

    def get_zone_for_room(self, room: Tuple[int, int, int, int], zones: List[Dict]) -> str:
        """
        Determine which zone a room belongs to based on its center point.

        Args:
            room: Room tuple (x, y, width, height)
            zones: List of zone definitions

        Returns:
            Zone type string ('linear', 'open', etc.)
        """
        x, y, w, h = room
        center_y = y + h // 2

        for zone in zones:
            _, y_start, _, y_end = zone['bounds']
            if y_start <= center_y < y_end:
                return zone['type']

        return zones[0]['type'] if zones else 'open'

    def identify_loot_rooms(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Identify which rooms should be 'loot rooms' with higher item density.

        Stores loot room positions directly in game_map for use during item placement.

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        loot_room_percentage = GameConfig._get_required('room_generation.loot_room_percentage')
        num_loot_rooms = max(1, int(len(rooms) * loot_room_percentage))

        loot_rooms = random.sample(rooms, num_loot_rooms)

        loot_room_positions = set()
        for room in loot_rooms:
            x, y, w, h = room
            for rx in range(x, x + w):
                for ry in range(y, y + h):
                    if (rx, ry) not in self.game_map.walls:
                        loot_room_positions.add((rx, ry))

        self.game_map.loot_room_positions = loot_room_positions


# ============================================================================
# TILE PLACEMENT
# ============================================================================

class TilePlacementGenerator:
    """
    Special tile and gateway placement subsystem.

    Coordinates strategic placement of nodes and gateway based on
    level topology and gameplay objectives.

    Attributes:
        game_map: GameMap instance to populate with special tiles
    """

    def __init__(self, game_map):
        """
        Initialize tile placement generator with game map reference.

        Args:
            game_map: GameMap instance to modify during placement
        """
        self.game_map = game_map

    def ensure_border_walls_new(self) -> None:
        """
        Ensure map has solid border walls.

        Creates a complete perimeter of walls around the map edges.
        """
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))

        for y in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))

    def place_special_tiles(self, level: int, landmark_rooms: List[Dict] = None) -> None:
        """
        Place cooling nodes, CPU recovery nodes, and other special tiles.

        Uses objective-oriented placement strategies:
        - Cooling nodes: High-traffic areas (central corridors, hub rooms)
        - CPU recovery nodes: Peripheral/safer areas (edge rooms, dead ends)
        - Ghost nodes: Shadow-adjacent positions (stealth paths)

        Args:
            level: Current level number (affects node counts)
            landmark_rooms: List of landmark room definitions for objective placement
        """
        if landmark_rooms is None:
            landmark_rooms = []

        floor_positions = self.get_all_floor_positions()

        if not floor_positions:
            logging.warning(f"No floor positions available for level {level} special node placement")
            return

        network_configs = GameConfig.get_network_configs()
        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        def get_required_config(key: str) -> int:
            if key not in config:
                error_msg = f"CRITICAL CONFIG ERROR: '{key}' missing for level {level} in game_data.json network_configs"
                logging.error(error_msg)
                logging.error(f"Available config keys for level {level}: {list(config.keys())}")
                raise KeyError(f"Required key '{key}' missing from level {level} config")
            return config[key]

        cooling_count = get_required_config('cooling_nodes')
        cooling_positions = self.get_high_traffic_positions(floor_positions)
        for i in range(cooling_count):
            if cooling_positions:
                pos = random.choice(cooling_positions)
                cooling_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)

        cpu_count = get_required_config('cpu_nodes')
        cpu_positions = self.get_peripheral_positions(floor_positions)
        for i in range(cpu_count):
            if cpu_positions:
                pos = random.choice(cpu_positions)
                cpu_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes.add(pos)
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes.add(pos)

        ghost_count = get_required_config('ghost_nodes')
        ghost_positions = self.get_shadow_adjacent_positions(floor_positions)
        for i in range(ghost_count):
            if ghost_positions:
                pos = random.choice(ghost_positions)
                ghost_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.ghost_nodes.add(pos)
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.ghost_nodes.add(pos)

    def get_high_traffic_positions(self, floor_positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Get positions in high-traffic areas (central corridors, hub rooms).

        High-traffic areas are:
        - Near map center
        - In corridors (limited floor neighbors)

        Args:
            floor_positions: List of all available floor positions

        Returns:
            List of high-traffic floor positions
        """
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        high_traffic = []
        for pos in floor_positions:
            x, y = pos

            dist_to_center = abs(x - map_center_x) + abs(y - map_center_y)
            if dist_to_center < 15:
                high_traffic.append(pos)
                continue

            floor_neighbors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in self.game_map.walls:
                    floor_neighbors += 1

            if 3 <= floor_neighbors <= 6:
                high_traffic.append(pos)

        return high_traffic

    def get_peripheral_positions(self, floor_positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Get positions in peripheral/safer areas (edge rooms, dead ends).

        Peripheral positions are:
        - Near map edges
        - In rooms (not corridors)

        Args:
            floor_positions: List of all available floor positions

        Returns:
            List of peripheral floor positions
        """
        peripheral = []

        for pos in floor_positions:
            x, y = pos

            near_edge = (x < 15 or x > GameConfig.MAP_WIDTH - 15 or
                        y < 15 or y > GameConfig.MAP_HEIGHT - 15)

            if near_edge:
                floor_neighbors = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (x + dx, y + dy)
                    if neighbor not in self.game_map.walls:
                        floor_neighbors += 1

                if floor_neighbors >= 3:
                    peripheral.append(pos)

        return peripheral

    def get_shadow_adjacent_positions(self, floor_positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Get positions adjacent to or within shadow areas.

        Shadow-adjacent positions are good for ghost nodes,
        rewarding stealth gameplay.

        Args:
            floor_positions: List of all available floor positions

        Returns:
            List of shadow-adjacent floor positions
        """
        shadow_adjacent = []

        for pos in floor_positions:
            x, y = pos

            if pos in self.game_map.shadows:
                shadow_adjacent.append(pos)
                continue

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in self.game_map.shadows:
                    shadow_adjacent.append(pos)
                    break

        return shadow_adjacent

    def get_all_floor_positions(self) -> List[Tuple[int, int]]:
        """
        Get all valid floor positions (not walls).

        Returns:
            List of all floor tile positions
        """
        floor_positions = []
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_positions.append((x, y))
        return floor_positions

    def place_gateway_strategic(self, level: int) -> None:
        """
        Place gateway using strategic placement strategies.

        Selects from multiple strategies:
        - Far Corner: Opposite corner from spawn
        - Central Hub: Near map center
        - Hidden Dead End: At end of longest branch
        - Gauntlet: Along edge, requires crossing map

        Args:
            level: Current level number (not currently used, but available for future per-level strategies)
        """
        strategy = self.select_gateway_strategy()

        spawn_area = Position(5, 5)
        floor_positions = self.get_all_floor_positions()

        if not floor_positions:
            return

        if strategy == 'far_corner':
            gateway_pos = self.gateway_far_corner(spawn_area, floor_positions)
        elif strategy == 'central_hub':
            gateway_pos = self.gateway_central_hub(floor_positions)
        elif strategy == 'hidden_dead_end':
            gateway_pos = self.gateway_hidden_dead_end(floor_positions)
        elif strategy == 'gauntlet':
            gateway_pos = self.gateway_gauntlet(spawn_area, floor_positions)
        else:
            gateway_pos = self.gateway_far_corner(spawn_area, floor_positions)

        self.game_map.gateway = Position(gateway_pos[0], gateway_pos[1])

    def select_gateway_strategy(self) -> str:
        """
        Select a gateway placement strategy based on configured weights.

        Returns:
            Strategy name string
        """
        weights = GameConfig._get_required('room_generation.gateway_strategy_weights')

        strategies = ['far_corner', 'central_hub', 'hidden_dead_end', 'gauntlet']
        strategy_weights = [
            weights.get('far_corner', 0.4),
            weights.get('central_hub', 0.3),
            weights.get('hidden_dead_end', 0.2),
            weights.get('gauntlet', 0.1)
        ]

        total = sum(strategy_weights)
        normalized = [w / total for w in strategy_weights]

        rand = random.random()
        cumulative = 0
        for strategy, weight in zip(strategies, normalized):
            cumulative += weight
            if rand < cumulative:
                return strategy

        return strategies[0]

    def gateway_far_corner(self, spawn: Position, floor_positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Gateway in opposite corner from spawn - minimum 30 tiles.

        Creates maximum distance objective.

        Args:
            spawn: Spawn position
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required('room_generation.gateway_minimum_distances')['far_corner']

        far_positions = [pos for pos in floor_positions
                        if spawn.distance_to(Position(pos[0], pos[1])) > min_distance]

        if far_positions:
            return random.choice(far_positions)

        furthest = max(floor_positions, key=lambda pos: spawn.distance_to(Position(pos[0], pos[1])))
        logging.warning(f"Far corner gateway: No positions >{min_distance} tiles from spawn, using furthest available")
        return furthest

    def gateway_central_hub(self, floor_positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Gateway in or near central area of map - minimum 20 tiles from spawn.

        Creates central objective, encourages exploration of center.

        Args:
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required('room_generation.gateway_minimum_distances')['central_hub']
        spawn = Position(5, 5)
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        central_positions = []
        for pos in floor_positions:
            distance_to_center = abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y)
            distance_from_spawn = spawn.distance_to(Position(pos[0], pos[1]))

            if distance_to_center < 15 and distance_from_spawn > min_distance:
                central_positions.append(pos)

        if central_positions:
            return random.choice(central_positions)

        valid_by_distance = [pos for pos in floor_positions
                            if spawn.distance_to(Position(pos[0], pos[1])) > min_distance]
        if valid_by_distance:
            return min(valid_by_distance, key=lambda pos: abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y))

        logging.warning(f"Central hub gateway: No positions >{min_distance} tiles from spawn!")
        return min(floor_positions, key=lambda pos: abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y))

    def gateway_hidden_dead_end(self, floor_positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Gateway at end of longest branch - minimum 25 tiles from spawn.

        Rewards exploration, creates hidden objective.

        Args:
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required('room_generation.gateway_minimum_distances')['hidden_dead_end']
        spawn = Position(5, 5)

        dead_end_positions = []

        for pos in floor_positions:
            x, y = pos

            neighbor_count = sum(1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                if (x + dx, y + dy) in floor_positions)

            if neighbor_count <= 2:
                distance_from_spawn = spawn.distance_to(Position(x, y))
                if distance_from_spawn > min_distance:
                    dead_end_positions.append(pos)

        if dead_end_positions:
            return random.choice(dead_end_positions)

        any_dead_end = [pos for pos in floor_positions
                       if sum(1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                             if (pos[0] + dx, pos[1] + dy) in floor_positions) <= 2]

        if any_dead_end:
            logging.warning(f"Hidden dead end gateway: No dead ends >{min_distance} tiles from spawn")
            return random.choice(any_dead_end)

        return random.choice(floor_positions)

    def gateway_gauntlet(self, spawn: Position, floor_positions: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Gateway along edge - minimum 25 tiles from spawn, requires crossing map.

        Forces traversal across the level.

        Args:
            spawn: Spawn position
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required('room_generation.gateway_minimum_distances')['gauntlet']

        edge_positions = []
        for pos in floor_positions:
            x, y = pos

            near_edge = (x < 10 or x > GameConfig.MAP_WIDTH - 10 or
                        y < 10 or y > GameConfig.MAP_HEIGHT - 10)

            distance_from_spawn = spawn.distance_to(Position(x, y))

            if near_edge and distance_from_spawn > min_distance:
                edge_positions.append(pos)

        if edge_positions:
            return random.choice(edge_positions)

        logging.warning(f"Gauntlet gateway: No edge positions >{min_distance} tiles from spawn, using far corner")
        return self.gateway_far_corner(spawn, floor_positions)
