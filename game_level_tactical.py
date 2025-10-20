"""
Tactical features subsystem for procedural level generation.

This module handles all tactical gameplay features:
- Shadow placement (wall-adjacent and interior) for stealth gameplay
- Cover element clusters using Poisson disc sampling
- Defensive positions (corner cover, shadow bunkers, crossfire setups)
- Choke points by narrowing corridors in strategic locations
- Shadow cleanup to prevent invalid placements

Tactical elements provide:
- Stealth opportunities (shadows for hiding)
- Combat advantages (cover for protection)
- Strategic positioning (defensive setups)
- Bottleneck control (choke points)
"""

import random
import logging
import math
from typing import List, Tuple, Set

from game_config import GameConfig


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

            # If this room is in a shadow zone, use higher coverage
            if room in shadow_zone_rooms:
                zone_coverage = GameConfig._get_required('room_generation.shadow_zone_coverage')
                shadows_in_room = int(width * height * zone_coverage)
            else:
                shadows_in_room = min(target_shadow_tiles - placed_shadows, width * height // 3)

            # Get wall-adjacent and interior positions for this room
            wall_adjacent_positions = self.get_wall_adjacent_positions(room)
            interior_positions = self.get_interior_positions(room)

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
        # Get config values
        min_open_area_size = GameConfig._get_required('room_generation.cover_min_open_area_size')
        cluster_chance = GameConfig._get_required('room_generation.cover_cluster_chance')
        poisson_radius = GameConfig._get_required('room_generation.cover_poisson_radius')

        # Find large open areas (10x10+ contiguous floor space)
        open_areas = self.find_large_open_areas(min_open_area_size)

        # Place cover clusters in some open areas
        for area in open_areas:
            if random.random() < cluster_chance:
                # Use Poisson disc sampling for natural distribution
                cluster_positions = self.poisson_disc_sampling(area, poisson_radius)

                # Create cover clusters at sampled positions
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

        # Randomly select cluster pattern
        cluster_type = random.choice(['small', 'l_shaped', 'scattered'])

        if cluster_type == 'small':
            # Small 2x2 cluster
            for dx in range(2):
                for dy in range(2):
                    pos = (x + dx, y + dy)
                    if self.is_valid_cover_position(pos):
                        self.game_map.walls.add(pos)

        elif cluster_type == 'l_shaped':
            # L-shaped cover
            positions = [(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x, y + 2)]
            for pos in positions:
                if self.is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

        elif cluster_type == 'scattered':
            # Scattered 5-6 tile cluster
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

        # Identify strategic locations:
        # 1. Near gateway (if it exists)
        # 2. In large rooms
        # 3. Near landmark rooms if they exist

        strategic_rooms = []

        # Add large rooms (good for defensive positions)
        for room in rooms:
            x, y, w, h = room
            area = w * h
            if area >= 50:  # Large room
                strategic_rooms.append(room)

        # Limit to placing 1-3 defensive positions
        num_positions = min(random.randint(1, 3), len(strategic_rooms))

        for _ in range(num_positions):
            if not strategic_rooms:
                break

            # Select random strategic room
            room = random.choice(strategic_rooms)
            strategic_rooms.remove(room)

            # Choose position type
            position_type = random.choice(position_types)

            # Create defensive position
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

        # Find a good central position in the room (avoid edges)
        if w < 6 or h < 6:
            return  # Room too small for defensive position

        # Select position near room center
        center_x = x + w // 2
        center_y = y + h // 2

        # Add some randomness to avoid always being exactly centered
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
        # Place L-shaped cover
        cover_positions = [(x, y), (x + 1, y), (x, y + 1)]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        # Place shadow in the corner (protected spot)
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
        # Place 3-sided cover
        cover_positions = [
            (x, y), (x + 1, y), (x + 2, y),      # Top wall
            (x, y + 1), (x + 2, y + 1),          # Side walls
            (x + 1, y + 2)                       # Bottom center
        ]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        # Place shadow in the protected center
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
        # Place two cover walls with gap
        cover_positions = [(x, y), (x + 4, y)]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        # Place shadows behind each cover
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

        # We can't create true "choke point rooms" post-generation, but we can:
        # 1. Narrow existing corridors in strategic locations
        # 2. Add walls to reduce corridor width in key areas

        # Find central/strategic corridor positions
        if not self.corridor_tiles:
            return

        # Find corridor tiles near the map center (high traffic)
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2

        central_corridors = []
        for tile in self.corridor_tiles:
            x, y = tile
            distance_to_center = abs(x - map_center_x) + abs(y - map_center_y)
            if distance_to_center < 20:  # Within central area
                central_corridors.append(tile)

        if not central_corridors:
            return

        # Select random positions to narrow
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

        # Check corridor orientation (horizontal or vertical)
        has_horizontal_flow = ((x - 1, y) in self.corridor_tiles or (x + 1, y) in self.corridor_tiles)
        has_vertical_flow = ((x, y - 1) in self.corridor_tiles or (x, y + 1) in self.corridor_tiles)

        if has_horizontal_flow and not has_vertical_flow:
            # Horizontal corridor - add walls above/below
            # Only narrow if corridor is wide enough
            if (x, y + 1) not in self.game_map.walls and (x, y + 1) in self.corridor_tiles:
                self.game_map.walls.add((x, y + 1))
                self.corridor_tiles.discard((x, y + 1))
            if (x, y - 1) not in self.game_map.walls and (x, y - 1) in self.corridor_tiles:
                self.game_map.walls.add((x, y - 1))
                self.corridor_tiles.discard((x, y - 1))

        elif has_vertical_flow and not has_horizontal_flow:
            # Vertical corridor - add walls left/right
            if (x + 1, y) not in self.game_map.walls and (x + 1, y) in self.corridor_tiles:
                self.game_map.walls.add((x + 1, y))
                self.corridor_tiles.discard((x + 1, y))
            if (x - 1, y) not in self.game_map.walls and (x - 1, y) in self.corridor_tiles:
                self.game_map.walls.add((x - 1, y))
                self.corridor_tiles.discard((x - 1, y))
