"""
Room generation subsystem for procedural level generation.

This module handles all room-related generation:
- Room type selection with configurable weights (rectangular, L-shaped, irregular, cross, circular)
- Room carving with varied shapes and patterns
- Pillar pattern application for server hall aesthetics
- Room placement with overlap detection and zone-based strategies

Room types:
- Rectangular: Standard room, reliable for navigation
- L-shaped: Creates ambush corners and multiple approach angles
- Irregular: Damaged infrastructure look with unpredictable cover
- Cross: Forces checking multiple directions with cardinal exits
- Circular: No corners, different tactical approach, good for server cores
"""

import random
import logging
from typing import List, Tuple, Dict

from game_config import GameConfig, RoomGenerationConfig


class RoomGenerator:
    """
    Room generation subsystem handling room creation and carving.

    Coordinates room type selection, room carving with varied shapes,
    and pillar pattern application for large rooms.

    Attributes:
        game_map: GameMap instance to populate with rooms
    """

    def __init__(self, game_map):
        """
        Initialize room generator with game map reference.

        Args:
            game_map: GameMap instance to modify during room generation
        """
        self.game_map = game_map

    def create_varied_rooms(self, level: int) -> List[Tuple[int, int, int, int]]:
        """
        Create varied rooms including a guaranteed spawn room in top-left corner.

        Args:
            level: Current level number (affects room type weights)

        Returns:
            List of room tuples (x, y, width, height) including spawn room
        """
        spawn_room = (2, 2, 8, 8)
        # Always make spawn room rectangular for predictability
        self.carve_room(spawn_room, room_type='rectangular', level=level)
        rooms = [spawn_room]
        rooms.extend(self.generate_rooms_avoiding_existing(level, [spawn_room]))
        return rooms

    def get_room_type_weights(self, level: int) -> Dict[str, float]:
        """
        Get room type weights for the given level, with per-level overrides.

        Args:
            level: Current level number

        Returns:
            Dictionary mapping room type names to their selection weights
        """
        # Get default weights from config
        default_weights = {
            'rectangular': GameConfig._get_required('room_generation.room_type_weights.rectangular'),
            'l_shaped': GameConfig._get_required('room_generation.room_type_weights.l_shaped'),
            'irregular': GameConfig._get_required('room_generation.room_type_weights.irregular'),
            'cross': GameConfig._get_required('room_generation.room_type_weights.cross'),
            'circular': GameConfig._get_required('room_generation.room_type_weights.circular')
        }

        # Check for per-level overrides
        network_configs = GameConfig.NETWORK_CONFIGS()
        if level in network_configs:
            level_config = network_configs[level]
            if 'level_generation' in level_config and 'room_type_weights' in level_config['level_generation']:
                # Override with level-specific weights
                level_weights = level_config['level_generation']['room_type_weights']
                for room_type in default_weights:
                    if room_type in level_weights:
                        default_weights[room_type] = level_weights[room_type]

        return default_weights

    def select_room_type(self, level: int, width: int, height: int) -> str:
        """
        Select a room type based on configured weights and room size.

        Different room types require minimum dimensions:
        - Rectangular: Any size
        - L-shaped: 5x5 minimum
        - Irregular: 4x4 minimum
        - Cross: 7x7 minimum
        - Circular: 7x7 minimum

        Args:
            level: Current level number (affects weights)
            width: Room width in tiles
            height: Room height in tiles

        Returns:
            Selected room type name ('rectangular', 'l_shaped', etc.)
        """
        weights = self.get_room_type_weights(level)

        # Some room types require minimum sizes
        available_types = []
        available_weights = []

        # Rectangular always available
        available_types.append('rectangular')
        available_weights.append(weights['rectangular'])

        # L-shaped needs at least 5x5
        if width >= 5 and height >= 5:
            available_types.append('l_shaped')
            available_weights.append(weights['l_shaped'])

        # Irregular needs at least 4x4
        if width >= 4 and height >= 4:
            available_types.append('irregular')
            available_weights.append(weights['irregular'])

        # Cross needs at least 7x7
        if width >= 7 and height >= 7:
            available_types.append('cross')
            available_weights.append(weights['cross'])

        # Circular needs at least 7x7
        if width >= 7 and height >= 7:
            available_types.append('circular')
            available_weights.append(weights['circular'])

        # Normalize weights
        total_weight = sum(available_weights)
        if total_weight == 0:
            return 'rectangular'

        normalized_weights = [w / total_weight for w in available_weights]

        # Select room type based on weights
        rand = random.random()
        cumulative = 0
        for room_type, weight in zip(available_types, normalized_weights):
            cumulative += weight
            if rand < cumulative:
                return room_type

        return available_types[-1]  # Fallback to last type

    def carve_room(self, room: Tuple[int, int, int, int], room_type: str = 'rectangular', level: int = 1) -> None:
        """
        Carve out a room by removing walls based on the room type.

        Args:
            room: Room tuple (x, y, width, height)
            room_type: Type of room to carve ('rectangular', 'l_shaped', etc.)
            level: Current level number (affects pillar placement)
        """
        if room_type == 'rectangular':
            self.carve_rectangular_room(room)
        elif room_type == 'l_shaped':
            self.carve_l_shaped_room(room)
        elif room_type == 'irregular':
            self.carve_irregular_room(room)
        elif room_type == 'cross':
            self.carve_cross_room(room)
        elif room_type == 'circular':
            self.carve_circular_room(room)
        else:
            # Fallback to rectangular
            self.carve_rectangular_room(room)

        # Apply pillars to large rectangular rooms if configured
        x, y, width, height = room
        if room_type == 'rectangular' and width >= 7 and height >= 7:
            self.apply_pillar_pattern(room, level)

    def carve_rectangular_room(self, room: Tuple[int, int, int, int]) -> None:
        """
        Carve out a standard rectangular room.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room
        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    self.game_map.walls.remove((rx, ry))

    def carve_l_shaped_room(self, room: Tuple[int, int, int, int]) -> None:
        """
        Carve out an L-shaped room by creating two overlapping rectangles.
        Creates natural ambush corners and multiple approach angles.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        # Determine L orientation (4 possible orientations)
        orientation = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right'])

        # Create two rectangles that form an L shape
        if orientation == 'top_left':
            # Large rectangle on top, small on left bottom
            rect1_width = width
            rect1_height = height // 2 + 1
            rect2_width = width // 2 + 1
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)
        elif orientation == 'top_right':
            # Large rectangle on top, small on right bottom
            rect1_width = width
            rect1_height = height // 2 + 1
            rect2_width = width // 2 + 1
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x + width - rect2_width, y + rect1_height - 1, rect2_width, rect2_height)
        elif orientation == 'bottom_left':
            # Small rectangle on top left, large on bottom
            rect1_width = width // 2 + 1
            rect1_height = height // 2 + 1
            rect2_width = width
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)
        else:  # bottom_right
            # Small rectangle on top right, large on bottom
            rect1_width = width // 2 + 1
            rect1_height = height // 2 + 1
            rect2_width = width
            rect2_height = height - rect1_height + 1
            rect1 = (x + width - rect1_width, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)

        # Carve both rectangles
        self.carve_rectangular_room(rect1)
        self.carve_rectangular_room(rect2)

    def carve_irregular_room(self, room: Tuple[int, int, int, int]) -> None:
        """
        Carve out an irregular/damaged room by starting with a rectangle
        and randomly removing corner sections.
        Creates unpredictable cover positions and looks like damaged infrastructure.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        # First carve the base rectangular room
        self.carve_rectangular_room(room)

        # Randomly remove 2-5 corner sections
        num_removals = random.randint(2, 5)
        total_area = width * height
        removed_area = 0

        for _ in range(num_removals):
            # Don't remove more than 30% of total area
            if removed_area >= total_area * 0.3:
                break

            # Select a corner to remove from
            corner = random.choice(['top_left', 'top_right', 'bottom_left', 'bottom_right'])

            # Size of section to remove (1-3 tiles in each dimension)
            remove_width = random.randint(1, min(3, width // 2))
            remove_height = random.randint(1, min(3, height // 2))

            # Determine removal area based on corner
            if corner == 'top_left':
                remove_x = x
                remove_y = y
            elif corner == 'top_right':
                remove_x = x + width - remove_width
                remove_y = y
            elif corner == 'bottom_left':
                remove_x = x
                remove_y = y + height - remove_height
            else:  # bottom_right
                remove_x = x + width - remove_width
                remove_y = y + height - remove_height

            # Add walls back in the removal area
            for rx in range(remove_x, remove_x + remove_width):
                for ry in range(remove_y, remove_y + remove_height):
                    if 0 <= rx < GameConfig.MAP_WIDTH and 0 <= ry < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.add((rx, ry))
                        removed_area += 1

    def carve_cross_room(self, room: Tuple[int, int, int, int]) -> None:
        """
        Carve out a cross/plus-shaped room with 4 cardinal exit points.
        Creates interesting sightlines and forces checking multiple directions.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        # Create vertical bar (center)
        vert_width = max(3, width // 3)
        vert_x = x + (width - vert_width) // 2
        vert_rect = (vert_x, y, vert_width, height)

        # Create horizontal bar (center)
        horiz_height = max(3, height // 3)
        horiz_y = y + (height - horiz_height) // 2
        horiz_rect = (x, horiz_y, width, horiz_height)

        # Carve both bars
        self.carve_rectangular_room(vert_rect)
        self.carve_rectangular_room(horiz_rect)

    def carve_circular_room(self, room: Tuple[int, int, int, int]) -> None:
        """
        Carve out a circular/oval room using midpoint circle algorithm.
        No corners to hide in - forces different tactical approach.
        Good for server core themed rooms.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        # Calculate center and radii
        center_x = x + width // 2
        center_y = y + height // 2
        radius_x = width // 2
        radius_y = height // 2

        # Use ellipse equation to determine which tiles to carve
        for rx in range(x, x + width):
            for ry in range(y, y + height):
                # Check if point is inside ellipse
                dx = (rx - center_x) / radius_x
                dy = (ry - center_y) / radius_y
                if dx * dx + dy * dy <= 1.0:
                    if (rx, ry) in self.game_map.walls:
                        self.game_map.walls.remove((rx, ry))

    def apply_pillar_pattern(self, room: Tuple[int, int, int, int], level: int) -> None:
        """
        Apply pillar pattern to a large room, creating server hall aesthetics.
        Excellent for stealth gameplay - many breaking points for line of sight.

        Args:
            room: Room tuple (x, y, width, height)
            level: Current level number (affects pillar chance)
        """
        # Get pillar chance from config with per-level override
        network_configs = GameConfig.NETWORK_CONFIGS()
        if level in network_configs:
            level_config = network_configs[level]
            if 'level_generation' in level_config and 'pillar_room_chance' in level_config['level_generation']:
                pillar_chance = level_config['level_generation']['pillar_room_chance']
            else:
                pillar_chance = GameConfig._get_required('room_generation.pillar_room_chance')
        else:
            pillar_chance = GameConfig._get_required('room_generation.pillar_room_chance')

        # Check if we should apply pillars
        if random.random() > pillar_chance:
            return

        x, y, width, height = room
        pillar_spacing = GameConfig._get_required('room_generation.pillar_grid_spacing')

        # Place pillars in a grid pattern (skip edges to allow entry)
        for rx in range(x + pillar_spacing, x + width - 1, pillar_spacing + 1):
            for ry in range(y + pillar_spacing, y + height - 1, pillar_spacing + 1):
                if (rx, ry) not in self.game_map.walls:
                    # Add a single-tile pillar (wall)
                    self.game_map.walls.add((rx, ry))

    def generate_rooms_avoiding_existing(self, level: int, existing_rooms: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Generate room layouts for the level with zone-based placement.

        Args:
            level: Current level number (affects room count)
            existing_rooms: List of already placed rooms to avoid

        Returns:
            List of newly generated room tuples (x, y, width, height)
        """
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
            if not self.room_overlaps(new_room, all_rooms):
                # Select room type based on configured weights and size
                room_type = self.select_room_type(level, room_width, room_height)

                new_rooms.append(new_room)
                all_rooms.append(new_room)  # Add to tracking list

                # Carve room with selected type
                self.carve_room(new_room, room_type, level)

        return new_rooms

    def room_overlaps(self, new_room: Tuple[int, int, int, int], existing_rooms: List[Tuple[int, int, int, int]]) -> bool:
        """
        Check if a new room overlaps with existing rooms.

        Args:
            new_room: Room tuple to check (x, y, width, height)
            existing_rooms: List of existing room tuples

        Returns:
            True if room overlaps with any existing room, False otherwise
        """
        x1, y1, w1, h1 = new_room
        pad = RoomGenerationConfig.ROOM_PADDING

        for x2, y2, w2, h2 in existing_rooms:
            if (x1 < x2 + w2 + pad and x1 + w1 + pad > x2 and
                y1 < y2 + h2 + pad and y1 + h1 + pad > y2):
                return True
        return False
