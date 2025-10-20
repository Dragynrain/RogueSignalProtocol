"""
Corridor generation subsystem for procedural level generation.

This module handles all corridor-related generation:
- Room connection using MST (Minimum Spanning Tree) algorithm
- Extra path creation for multiple routes and loops
- Variable width corridors (narrow/medium/wide)
- Curved corridors using Bresenham's line algorithm
- Corridor alcoves for stealth hiding spots
- T-junctions and 4-way intersections for tactical complexity

Corridor types:
- L-shaped: Standard connection, either horizontal-then-vertical or vertical-then-horizontal
- Curved: Smooth Bresenham-based path between rooms
- Variable width: Narrow (1 tile), medium (2 tiles), or wide (3 tiles)
"""

import random
import logging
from typing import List, Tuple, Set

from game_config import GameConfig


class CorridorGenerator:
    """
    Corridor generation subsystem handling room connections and corridor features.

    Coordinates MST-based room connection, extra path creation, alcove placement,
    and intersection expansion into junctions.

    Attributes:
        game_map: GameMap instance to populate with corridors
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
    """

    def __init__(self, game_map, corridor_tiles: Set[Tuple[int, int]]):
        """
        Initialize corridor generator with game map and corridor tracking.

        Args:
            game_map: GameMap instance to modify during corridor generation
            corridor_tiles: Set to track corridor tile positions for alcove placement
        """
        self.game_map = game_map
        self.corridor_tiles = corridor_tiles

    def connect_rooms_mst(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Connect rooms using minimum spanning tree approach.

        Ensures all rooms are connected with minimum total corridor length.
        Creates base connectivity graph for the level.

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
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
                self.create_corridor_between_rooms(room1, room2)
                connected.append(room2)
                unconnected.pop(index)

    def add_extra_paths(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """
        Add extra corridors for multiple paths.

        Creates additional connections beyond the MST to provide:
        - Multiple routes between rooms
        - Loop opportunities for tactical gameplay
        - Fallback paths if one route is blocked

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        if len(rooms) < 3:
            return

        extra_connections = min(random.randint(2, 4), len(rooms) // 2)
        for _ in range(extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice(rooms)
            if room1 != room2:
                self.create_corridor_between_rooms(room1, room2)

    def create_corridor_between_rooms(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]) -> None:
        """
        Create corridor between two rooms - either L-shaped or curved.

        Randomly selects between:
        - L-shaped corridors (horizontal-then-vertical or vice versa)
        - Curved corridors (Bresenham line algorithm)

        Corridor width is determined by configured probabilities.

        Args:
            room1: First room tuple (x, y, width, height)
            room2: Second room tuple (x, y, width, height)
        """
        x1 = room1[0] + room1[2] // 2
        y1 = room1[1] + room1[3] // 2
        x2 = room2[0] + room2[2] // 2
        y2 = room2[1] + room2[3] // 2

        # Determine corridor width based on configured probabilities
        width = self.get_corridor_width()

        # 20% chance to use curved corridor instead of L-shaped
        curved_chance = GameConfig._get_required('room_generation.curved_corridor_chance')
        if random.random() < curved_chance:
            self.create_curved_corridor(x1, y1, x2, y2, width)
        else:
            # Create L-shaped corridor with specified width
            if random.choice([True, False]):
                # Horizontal then vertical
                self.carve_corridor_segment(min(x1, x2), max(x1, x2), y1, y1, width, horizontal=True)
                self.carve_corridor_segment(x2, x2, min(y1, y2), max(y1, y2), width, horizontal=False)
            else:
                # Vertical then horizontal
                self.carve_corridor_segment(x1, x1, min(y1, y2), max(y1, y2), width, horizontal=False)
                self.carve_corridor_segment(min(x1, x2), max(x1, x2), y2, y2, width, horizontal=True)

    def get_corridor_width(self) -> int:
        """
        Determine corridor width based on configured probabilities.

        Returns one of:
        - 1 tile (narrow corridors)
        - 2 tiles (medium corridors)
        - 3 tiles (wide corridors)

        Returns:
            Corridor width in tiles (1, 2, or 3)
        """
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

    def create_curved_corridor(self, x1: int, y1: int, x2: int, y2: int, width: int) -> None:
        """
        Create a curved corridor using Bresenham's line algorithm.

        Provides smoother, more organic-looking corridors compared to L-shaped ones.
        Good for creating variety in level layout.

        Args:
            x1: Starting x coordinate
            y1: Starting y coordinate
            x2: Ending x coordinate
            y2: Ending y coordinate
            width: Corridor width in tiles
        """
        # Use Bresenham's line algorithm to get line points
        line_points = self.bresenham_line(x1, y1, x2, y2)

        # Widen the line to the desired corridor width
        for x, y in line_points:
            # Carve a small area around each point based on width
            half_width = width // 2
            for dx in range(-half_width, (width + 1) // 2):
                for dy in range(-half_width, (width + 1) // 2):
                    px = x + dx
                    py = y + dy
                    if 0 <= px < GameConfig.MAP_WIDTH and 0 <= py < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((px, py))
                        self.corridor_tiles.add((px, py))

    def bresenham_line(self, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int]]:
        """
        Bresenham's line algorithm to get all points along a line.

        Classic line drawing algorithm for smooth diagonal lines.

        Args:
            x1: Starting x coordinate
            y1: Starting y coordinate
            x2: Ending x coordinate
            y2: Ending y coordinate

        Returns:
            List of (x, y) coordinates from (x1, y1) to (x2, y2)
        """
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            points.append((x, y))

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        return points

    def carve_corridor_segment(self, x_start: int, x_end: int, y_start: int, y_end: int,
                                width: int, horizontal: bool) -> None:
        """
        Carve a corridor segment with specified width and track corridor tiles.

        Args:
            x_start: Starting x coordinate
            x_end: Ending x coordinate
            y_start: Starting y coordinate
            y_end: Ending y coordinate
            width: Corridor width in tiles
            horizontal: True if corridor is horizontal, False if vertical
        """
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

    def add_corridor_alcoves(self) -> None:
        """
        Add alcoves to straight corridor segments for stealth hiding spots.

        Alcoves are small 1-tile indentations off the main corridor.
        They provide:
        - Stealth hiding spots (shadows automatically placed)
        - Tactical cover positions
        - Visual variety in corridor design
        """
        # Get alcove chance from config - FAIL if missing
        alcove_chance = GameConfig._get_required('room_generation.corridor_alcove_chance')
        min_segment_length = GameConfig._get_required('room_generation.corridor_alcove_min_length')

        # Find straight corridor segments
        horizontal_segments = self.find_straight_corridor_segments(horizontal=True)
        vertical_segments = self.find_straight_corridor_segments(horizontal=False)

        # Add alcoves to eligible segments
        for segment in horizontal_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self.create_alcoves_on_segment(segment, horizontal=True)

        for segment in vertical_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self.create_alcoves_on_segment(segment, horizontal=False)

    def find_straight_corridor_segments(self, horizontal: bool) -> List[List[Tuple[int, int]]]:
        """
        Find straight corridor segments (either horizontal or vertical).

        Args:
            horizontal: True to find horizontal segments, False for vertical

        Returns:
            List of corridor segments, where each segment is a list of (x, y) tiles
        """
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

    def create_alcoves_on_segment(self, segment: List[Tuple[int, int]], horizontal: bool) -> None:
        """
        Create 1-2 alcoves along a corridor segment.

        Alcoves are carved perpendicular to the corridor direction and
        automatically receive shadows for stealth gameplay.

        Args:
            segment: List of (x, y) corridor tiles in the segment
            horizontal: True if segment is horizontal, False if vertical
        """
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

    def create_corridor_intersections(self) -> None:
        """
        Create T-junctions and 4-way intersections where corridors meet.

        Expands intersection points into larger junction rooms with:
        - Increased tactical complexity
        - Corner shadows for stealth
        - Multiple approach angles
        """
        # Get configuration values
        intersection_chance = GameConfig._get_required('room_generation.corridor_intersection_chance')
        min_junction_size = GameConfig._get_required('room_generation.corridor_intersection_min_size')
        max_junction_size = GameConfig._get_required('room_generation.corridor_intersection_max_size')

        # Find corridor intersection points (tiles where 3+ corridors meet)
        intersections = self.find_corridor_intersections()

        for intersection_pos in intersections:
            if random.random() < intersection_chance:
                # Randomly choose junction size
                junction_size = random.choice([min_junction_size, max_junction_size])
                self.expand_intersection_into_junction(intersection_pos, junction_size)

    def find_corridor_intersections(self) -> List[Tuple[int, int]]:
        """
        Find points where 3 or more corridor segments meet.

        Identifies T-junctions (3 connections) and 4-way intersections (4 connections).

        Returns:
            List of (x, y) positions that are intersection points
        """
        intersections = []

        for tile in self.corridor_tiles:
            x, y = tile

            # Count corridor neighbors (orthogonal directions)
            corridor_neighbors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in self.corridor_tiles:
                    corridor_neighbors += 1

            # If 3 or 4 corridor neighbors, this is an intersection
            if corridor_neighbors >= 3:
                intersections.append(tile)

        return intersections

    def expand_intersection_into_junction(self, center: Tuple[int, int], size: int) -> None:
        """
        Expand an intersection point into a larger junction room.

        Creates a square room centered on the intersection with:
        - Corner shadows for stealth advantage
        - Wider maneuvering space
        - More tactical options during combat

        Args:
            center: Center position (x, y) of the intersection
            size: Size of the junction room (will be size x size tiles)
        """
        x, y = center
        half_size = size // 2

        # Carve out junction area (square around the intersection)
        for jx in range(x - half_size, x + half_size + 1):
            for jy in range(y - half_size, y + half_size + 1):
                if 0 <= jx < GameConfig.MAP_WIDTH and 0 <= jy < GameConfig.MAP_HEIGHT:
                    # Don't carve if it would break into another room
                    if (jx, jy) in self.game_map.walls:
                        self.game_map.walls.discard((jx, jy))
                        self.corridor_tiles.add((jx, jy))

        # Place shadows in corners of junction for stealth gameplay
        # Only place if the corner is actually carved (not a wall)
        corners = [
            (x - half_size, y - half_size),      # Top-left
            (x + half_size, y - half_size),      # Top-right
            (x - half_size, y + half_size),      # Bottom-left
            (x + half_size, y + half_size)       # Bottom-right
        ]

        for corner in corners:
            cx, cy = corner
            if (0 <= cx < GameConfig.MAP_WIDTH and
                0 <= cy < GameConfig.MAP_HEIGHT and
                (cx, cy) not in self.game_map.walls and
                (cx, cy) in self.corridor_tiles):  # Ensure it's actually a floor tile
                # Place shadow in corner
                self.game_map.shadows.add((cx, cy))
