"""
Tactical feature generation for procedural levels.

This module handles tactical element placement including shadows, cover, and defensive positions:

TACTICAL GENERATION:
- Shadow placement (wall-adjacent and interior) for stealth gameplay using Perlin noise
- Cover element clusters using Poisson disc sampling for natural distribution
- Defensive positions (corner cover, shadow bunkers, crossfire setups)
- Choke points by narrowing corridors in strategic locations
- Shadow cleanup to prevent invalid placements

Tactical elements provide:
- Stealth opportunities (shadows for hiding)
- Combat advantages (cover for protection)
- Strategic positioning (defensive setups)
- Bottleneck control (choke points)

All shadow placement uses organic Perlin noise patterns for natural-looking darkness zones.
"""

from __future__ import annotations

import logging
import math
import random
from typing import TYPE_CHECKING

from rsp.core.config import GameConfig
from rsp.entities.base import Position
from rsp.level.structure import create_noise_map, get_noise_value

if TYPE_CHECKING:
    from rsp.systems.ascension import AscensionModifiers


class TacticalGenerator:
    """
    Tactical features subsystem handling shadows, cover, and defensive elements.

    Coordinates placement of stealth and combat-related features throughout
    the level to support various playstyles.

    Attributes:
        game_map: GameMap instance to populate with tactical features
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
    """

    def __init__(self, game_map, corridor_tiles: set[tuple[int, int]]):
        """
        Initialize tactical generator with game map and corridor tracking.

        Args:
            game_map: GameMap instance to modify during tactical feature generation
            corridor_tiles: Set of corridor tile positions (used for cover validation)
        """
        self.game_map = game_map
        self.corridor_tiles = corridor_tiles

    def place_blind_spot_areas(
        self,
        level: int,
        rooms: list[tuple[int, int, int, int]],
        blind_spot_zone_rooms: list[tuple[int, int, int, int]],
        ascension_modifiers: AscensionModifiers | None = None,
    ) -> None:
        """
        Place blind spot areas for stealth gameplay using Perlin noise for organic patterns.

        NEW: Uses Perlin noise to create natural-looking darkness zones!
        Blind spots are influenced by:
        - Noise-based probability (organic blind spot clusters)
        - Wall-adjacent positions (preferred for realistic lighting)
        - Interior positions (for larger blind spot areas)

        Blind spot zones have higher coverage for stealth-focused areas.

        Args:
            level: Current level number (affects blind spot coverage)
            rooms: List of room tuples (x, y, width, height)
            blind_spot_zone_rooms: List of rooms designated as blind spot zones
            ascension_modifiers: Optional AscensionModifiers for A6 blind spot reduction
        """
        network_configs = GameConfig.NETWORK_CONFIGS()

        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        if "blind_spot_coverage" not in config:
            error_msg = f"CRITICAL CONFIG ERROR: 'blind_spot_coverage' missing for level {level} in game_data.json network_configs"
            logging.error(error_msg)
            logging.error(f"Available config keys for level {level}: {list(config.keys())}")
            raise KeyError(f"Required key 'blind_spot_coverage' missing from level {level} config")

        blind_spot_coverage = config["blind_spot_coverage"]

        # A6: Apply blind spot reduction per floor from ascension modifiers
        if (
            ascension_modifiers is not None
            and ascension_modifiers.blind_spot_reduction_per_floor > 0
        ):
            reduction = (
                ascension_modifiers.blind_spot_reduction_per_floor / 100.0
            )  # Convert 1% to 0.01
            blind_spot_coverage = max(0.01, blind_spot_coverage - reduction)  # Min 1% coverage
            logging.debug(
                f"Shadow Gen: A6 blind spot reduction applied: -{ascension_modifiers.blind_spot_reduction_per_floor}% -> coverage now {blind_spot_coverage:.2%}"
            )

        # Create Perlin noise map for organic blind spot distribution
        noise_seed = level * 12345 + random.randint(0, 10000)
        noise_map = create_noise_map(
            width=GameConfig.MAP_WIDTH,
            height=GameConfig.MAP_HEIGHT,
            seed=noise_seed,
            octaves=3,
            scale=0.15,  # Larger scale = bigger shadow clusters
        )
        logging.debug(
            f"Shadow Gen: Created Perlin noise map for organic shadow placement (seed={noise_seed})"
        )

        wall_adjacent_weight = GameConfig._get_required(
            "room_generation.blind_spot_placement_weights.wall_adjacent"
        )

        total_floor_tiles = sum(w * h for x, y, w, h in rooms)
        target_blind_spot_tiles = int(total_floor_tiles * blind_spot_coverage)

        placed_blind_spots = 0
        for room in rooms:
            if placed_blind_spots >= target_blind_spot_tiles:
                break

            x, y, width, height = room

            if room in blind_spot_zone_rooms:
                zone_coverage = GameConfig._get_required("room_generation.blind_spot_zone_coverage")
                blind_spots_in_room = int(width * height * zone_coverage)
            else:
                blind_spots_in_room = min(
                    target_blind_spot_tiles - placed_blind_spots, width * height // 3
                )

            # Get candidate positions with noise values
            wall_adjacent_positions = self._get_noise_weighted_positions(
                self.get_wall_adjacent_positions(room), noise_map
            )
            interior_positions = self._get_noise_weighted_positions(
                self.get_interior_positions(room), noise_map
            )

            for _ in range(blind_spots_in_room):
                # Use noise to bias selection toward "darker" areas
                if random.random() < wall_adjacent_weight:
                    if wall_adjacent_positions:
                        shadow_pos = self._select_by_noise_weight(wall_adjacent_positions)
                        wall_adjacent_positions = [
                            (pos, noise)
                            for pos, noise in wall_adjacent_positions
                            if pos != shadow_pos
                        ]
                    elif interior_positions:
                        shadow_pos = self._select_by_noise_weight(interior_positions)
                        interior_positions = [
                            (pos, noise) for pos, noise in interior_positions if pos != shadow_pos
                        ]
                    else:
                        continue
                else:
                    if interior_positions:
                        shadow_pos = self._select_by_noise_weight(interior_positions)
                        interior_positions = [
                            (pos, noise) for pos, noise in interior_positions if pos != shadow_pos
                        ]
                    elif wall_adjacent_positions:
                        shadow_pos = self._select_by_noise_weight(wall_adjacent_positions)
                        wall_adjacent_positions = [
                            (pos, noise)
                            for pos, noise in wall_adjacent_positions
                            if pos != shadow_pos
                        ]
                    else:
                        continue

                if shadow_pos not in self.game_map.walls:
                    self.game_map.blind_spots.add(shadow_pos)
                    placed_blind_spots += 1

        logging.debug(
            f"Shadow Gen: Placed {placed_blind_spots} shadows using noise-based organic distribution"
        )

    def _get_noise_weighted_positions(
        self, positions: list[tuple[int, int]], noise_map
    ) -> list[tuple[tuple[int, int], float]]:
        """
        Add noise values to positions for weighted selection.

        Args:
            positions: List of (x, y) positions
            noise_map: TCOD Noise instance

        Returns:
            List of ((x, y), noise_value) tuples
        """
        weighted = []
        for pos in positions:
            x, y = pos
            noise_value = get_noise_value(noise_map, x, y, scale=0.15)
            weighted.append((pos, noise_value))
        return weighted

    def _select_by_noise_weight(
        self, weighted_positions: list[tuple[tuple[int, int], float]]
    ) -> tuple[int, int]:
        """
        Select position biased by noise value (higher noise = more likely).

        Converts noise from [-1, 1] to [0, 1] probability range.

        Args:
            weighted_positions: List of ((x, y), noise_value) tuples

        Returns:
            Selected (x, y) position
        """
        if not weighted_positions:
            return None

        # Normalize noise values to [0, 1] range and use as weights
        normalized_weights = [(pos, (noise + 1.0) / 2.0) for pos, noise in weighted_positions]

        # Weighted random selection
        total_weight = sum(weight for _, weight in normalized_weights)
        if total_weight <= 0:
            # Fallback to uniform random if all weights are 0
            return random.choice([pos for pos, _ in weighted_positions])

        rand = random.random() * total_weight
        cumulative = 0.0
        for pos, weight in normalized_weights:
            cumulative += weight
            if rand <= cumulative:
                return pos

        # Fallback to last position
        return normalized_weights[-1][0]

    def get_wall_adjacent_positions(self, room: tuple[int, int, int, int]) -> list[tuple[int, int]]:
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

    def get_interior_positions(self, room: tuple[int, int, int, int]) -> list[tuple[int, int]]:
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
        for shadow_pos in self.game_map.blind_spots:
            if shadow_pos in self.game_map.walls:
                invalid_shadows.append(shadow_pos)

        for shadow_pos in invalid_shadows:
            self.game_map.blind_spots.remove(shadow_pos)

    def add_cover_elements_new(self) -> None:
        """
        Add strategic cover clusters in open areas using Poisson disc sampling.

        Cover provides:
        - Tactical positioning during combat
        - Line-of-sight breaking
        - Strategic gameplay options

        Uses Poisson disc sampling for natural, evenly-distributed placement.
        """
        min_open_area_size = GameConfig._get_required("room_generation.cover_min_open_area_size")
        cluster_chance = GameConfig._get_required("room_generation.cover_cluster_chance")
        poisson_radius = GameConfig._get_required("room_generation.cover_poisson_radius")

        open_areas = self.find_large_open_areas(min_open_area_size)
        logging.debug(f"Tactical Gen: Found {len(open_areas)} open areas for cover placement")

        clusters_placed = 0
        for area in open_areas:
            if random.random() < cluster_chance:
                cluster_positions = self.poisson_disc_sampling(area, poisson_radius)

                for pos in cluster_positions:
                    self.create_cover_cluster(pos)
                    clusters_placed += 1

        logging.debug(f"Tactical Gen: Placed {clusters_placed} cover clusters")

    def find_large_open_areas(self, min_size: int) -> list[tuple[int, int, int, int]]:
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

    def poisson_disc_sampling(
        self, area: tuple[int, int, int, int], radius: float
    ) -> list[tuple[int, int]]:
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

    def create_cover_cluster(self, center: tuple[int, int]) -> None:
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

        cluster_type = random.choice(["small", "l_shaped", "scattered"])

        if cluster_type == "small":
            for dx in range(2):
                for dy in range(2):
                    pos = (x + dx, y + dy)
                    if self.is_valid_cover_position(pos):
                        self.game_map.walls.add(pos)

        elif cluster_type == "l_shaped":
            positions = [(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x, y + 2)]
            for pos in positions:
                if self.is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

        elif cluster_type == "scattered":
            positions = [(x, y), (x + 2, y), (x + 1, y + 1), (x, y + 2), (x + 2, y + 2)]
            for pos in positions:
                if self.is_valid_cover_position(pos):
                    self.game_map.walls.add(pos)

    def is_valid_cover_position(self, pos: tuple[int, int]) -> bool:
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
        pos_obj = Position(x, y)

        if not pos_obj.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            return False

        if pos in self.game_map.walls:
            return False

        if pos in self.corridor_tiles:
            return False

        if (
            pos in self.game_map.cooling_nodes
            or pos in self.game_map.cpu_recovery_nodes
            or pos in self.game_map.ghost_nodes
        ):
            return False

        return True

    def place_defensive_positions(self, rooms: list[tuple[int, int, int, int]]) -> None:
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
        position_types = GameConfig._get_required("room_generation.defensive_position_types")

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

    def create_defensive_position(
        self, room: tuple[int, int, int, int], position_type: str
    ) -> None:
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

        if position_type == "corner_cover":
            self.create_corner_cover_position(pos_x, pos_y)
        elif position_type == "shadow_bunker":
            self.create_shadow_bunker_position(pos_x, pos_y)
        elif position_type == "crossfire":
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
            self.game_map.blind_spots.add(shadow_pos)

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
            (x, y),
            (x + 1, y),
            (x + 2, y),
            (x, y + 1),
            (x + 2, y + 1),
            (x + 1, y + 2),
        ]
        for pos in cover_positions:
            if self.is_valid_cover_position(pos):
                self.game_map.walls.add(pos)

        shadow_pos = (x + 1, y + 1)
        if shadow_pos not in self.game_map.walls:
            self.game_map.blind_spots.add(shadow_pos)

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
                self.game_map.blind_spots.add(pos)

    def create_choke_points(self, rooms: list[tuple[int, int, int, int]]) -> None:
        """
        Create choke points by narrowing corridors near strategic rooms.

        Choke points are bottleneck areas that force tension in gameplay by:
        - Limiting movement options
        - Creating predictable enemy paths
        - Forcing tactical decisions

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        choke_point_count = GameConfig._get_required("room_generation.choke_point_count")

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

    def narrow_corridor_at_position(self, position: tuple[int, int]) -> None:
        """
        Narrow a corridor at the given position by adding walls on sides.

        Creates a bottleneck effect by reducing corridor width.

        Args:
            position: Position (x, y) to narrow
        """
        x, y = position

        has_horizontal_flow = (x - 1, y) in self.corridor_tiles or (x + 1, y) in self.corridor_tiles
        has_vertical_flow = (x, y - 1) in self.corridor_tiles or (x, y + 1) in self.corridor_tiles

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
