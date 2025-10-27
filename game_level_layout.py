"""
Advanced layout generation for procedural levels.

This module handles complex architectural features including:

ADVANCED LAYOUT:
- Hub-and-spoke patterns (central hub rooms with multiple connections)
- Looping paths for stealth and multiple approach routes
- Shadow zones (clusters of rooms with high shadow coverage)
- Landmark rooms (distinctive themed areas: server core, vault, junction, maze, arena)
- Map zones for different gameplay pacing (linear vs open sections)
- Loot room identification for item clustering

Hub rooms create central navigation nodes with multiple connections.
Looping paths provide tactical flanking and stealth escape opportunities.
Shadow zones offer stealth-focused areas with high darkness coverage.
Landmark rooms provide memorable, distinctive locations with special rewards.
Map zones create varied gameplay pacing through connectivity patterns.
"""

import random
import logging
from typing import List, Tuple, Dict, Optional

from game_config import GameConfig


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
