"""
Level structure generation: rooms and corridors.

This module handles the fundamental topology of procedural levels:

ROOM GENERATION:
- Room type selection with configurable weights (rectangular, L-shaped, irregular, cross, circular)
- Room carving with varied shapes and patterns
- Pillar pattern application for server hall aesthetics
- Room placement with overlap detection and zone-based strategies
- BSP (Binary Space Partitioning) for organic spatial distribution

CORRIDOR GENERATION:
- Room connection using MST (Minimum Spanning Tree) algorithm
- Extra path creation for multiple routes and loops
- Variable width corridors (narrow/medium/wide)
- Curved corridors using Bresenham's line algorithm
- Corridor alcoves for stealth hiding spots
- T-junctions and 4-way intersections for tactical complexity

Room types:
- Rectangular: Standard room, reliable for navigation
- L-shaped: Creates ambush corners and multiple approach angles
- Irregular: Damaged infrastructure look with unpredictable cover
- Cross: Forces checking multiple directions with cardinal exits
- Circular: No corners, different tactical approach, good for server cores

Corridor types:
- L-shaped: Standard connection, either horizontal-then-vertical or vertical-then-horizontal
- Curved: Smooth Bresenham-based path between rooms
- Variable width: Narrow (1 tile), medium (2 tiles), or wide (3 tiles)
"""

import logging
import random

import tcod.bsp
import tcod.noise
import tcod.random

from game_config import GameConfig, RoomGenerationConfig

# Module-level RNG instance - will be seeded by LevelGenerator
_rng: tcod.random.Random | None = None


def get_rng() -> tcod.random.Random:
    """Get the current RNG instance, creating one if needed."""
    global _rng
    if _rng is None:
        _rng = tcod.random.Random(tcod.random.MERSENNE_TWISTER)
    return _rng


def seed_rng(seed: int) -> None:
    """Seed the RNG for reproducible level generation."""
    global _rng
    _rng = tcod.random.Random(tcod.random.MERSENNE_TWISTER, seed=seed)
    logging.debug(f"RNG: Seeded TCOD RNG with seed={seed}")


def create_noise_map(
    width: int, height: int, seed: int, octaves: int = 4, scale: float = 0.1
) -> tcod.noise.Noise:
    """
    Create a Perlin noise generator for organic pattern generation.

    Perlin noise creates smooth, natural-looking random values useful for:
    - Shadow zone placement (organic darkness)
    - Terrain variation
    - Special node distribution

    Args:
        width: Map width
        height: Map height
        seed: Seed for reproducible noise
        octaves: Number of octaves (more = more detail), default 4
        scale: Noise scale (lower = larger features), default 0.1

    Returns:
        TCOD Noise instance configured for 2D generation
    """
    # Create 2D Perlin noise generator
    noise = tcod.noise.Noise(
        dimensions=2,
        algorithm=tcod.noise.Algorithm.PERLIN,
        implementation=tcod.noise.Implementation.SIMPLE,
        hurst=0.5,
        lacunarity=2.0,
        octaves=octaves,
        seed=seed,
    )
    return noise


def get_noise_value(noise: tcod.noise.Noise, x: int, y: int, scale: float = 0.1) -> float:
    """
    Get noise value at a position.

    Args:
        noise: TCOD Noise instance
        x: X coordinate
        y: Y coordinate
        scale: Scale factor for noise coordinates

    Returns:
        Noise value between -1.0 and 1.0
    """
    return noise.get_point(x * scale, y * scale)


# ============================================================================
# ROOM GENERATION
# ============================================================================


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

    def create_varied_rooms(self, level: int) -> list[tuple[int, int, int, int]]:
        """
        Create varied rooms including a guaranteed spawn room in top-left corner.

        Args:
            level: Current level number (affects room type weights)

        Returns:
            List of room tuples (x, y, width, height) including spawn room
        """
        spawn_room = (2, 2, 8, 8)
        logging.debug(
            f"Room Gen: Creating spawn room at {spawn_room[:2]}, size={spawn_room[2]}x{spawn_room[3]}"
        )
        self.carve_room(spawn_room, room_type="rectangular", level=level)
        rooms = [spawn_room]
        rooms.extend(self.generate_rooms_avoiding_existing(level, [spawn_room]))
        logging.debug(f"Room Gen: Total rooms created: {len(rooms)}")
        return rooms

    def get_room_type_weights(self, level: int) -> dict[str, float]:
        """
        Get room type weights for the given level, with per-level overrides.

        Args:
            level: Current level number

        Returns:
            Dictionary mapping room type names to their selection weights
        """
        default_weights = {
            "rectangular": GameConfig._get_required(
                "room_generation.room_type_weights.rectangular"
            ),
            "l_shaped": GameConfig._get_required("room_generation.room_type_weights.l_shaped"),
            "irregular": GameConfig._get_required("room_generation.room_type_weights.irregular"),
            "cross": GameConfig._get_required("room_generation.room_type_weights.cross"),
            "circular": GameConfig._get_required("room_generation.room_type_weights.circular"),
        }

        network_configs = GameConfig.NETWORK_CONFIGS()
        if level in network_configs:
            level_config = network_configs[level]
            if (
                "level_generation" in level_config
                and "room_type_weights" in level_config["level_generation"]
            ):
                level_weights = level_config["level_generation"]["room_type_weights"]
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

        available_types = []
        available_weights = []

        available_types.append("rectangular")
        available_weights.append(weights["rectangular"])

        if width >= 5 and height >= 5:
            available_types.append("l_shaped")
            available_weights.append(weights["l_shaped"])

        if width >= 4 and height >= 4:
            available_types.append("irregular")
            available_weights.append(weights["irregular"])

        if width >= 7 and height >= 7:
            available_types.append("cross")
            available_weights.append(weights["cross"])

        if width >= 7 and height >= 7:
            available_types.append("circular")
            available_weights.append(weights["circular"])

        total_weight = sum(available_weights)
        if total_weight == 0:
            return "rectangular"

        normalized_weights = [w / total_weight for w in available_weights]

        # Use TCOD RNG for reproducible room type selection
        rng = get_rng()
        rand = rng.uniform(0.0, 1.0)
        cumulative = 0
        for room_type, weight in zip(available_types, normalized_weights):
            cumulative += weight
            if rand < cumulative:
                return room_type

        return available_types[-1]

    def carve_room(
        self, room: tuple[int, int, int, int], room_type: str = "rectangular", level: int = 1
    ) -> None:
        """
        Carve out a room by removing walls based on the room type.

        Args:
            room: Room tuple (x, y, width, height)
            room_type: Type of room to carve ('rectangular', 'l_shaped', etc.)
            level: Current level number (affects pillar placement)
        """
        if room_type == "rectangular":
            self.carve_rectangular_room(room)
        elif room_type == "l_shaped":
            self.carve_l_shaped_room(room)
        elif room_type == "irregular":
            self.carve_irregular_room(room)
        elif room_type == "cross":
            self.carve_cross_room(room)
        elif room_type == "circular":
            self.carve_circular_room(room)
        else:
            self.carve_rectangular_room(room)

        x, y, width, height = room
        if room_type == "rectangular" and width >= 7 and height >= 7:
            self.apply_pillar_pattern(room, level)

    def carve_rectangular_room(self, room: tuple[int, int, int, int]) -> None:
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

    def carve_l_shaped_room(self, room: tuple[int, int, int, int]) -> None:
        """
        Carve out an L-shaped room by creating two overlapping rectangles.
        Creates natural ambush corners and multiple approach angles.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        orientation = random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])

        if orientation == "top_left":
            rect1_width = width
            rect1_height = height // 2 + 1
            rect2_width = width // 2 + 1
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)
        elif orientation == "top_right":
            rect1_width = width
            rect1_height = height // 2 + 1
            rect2_width = width // 2 + 1
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x + width - rect2_width, y + rect1_height - 1, rect2_width, rect2_height)
        elif orientation == "bottom_left":
            rect1_width = width // 2 + 1
            rect1_height = height // 2 + 1
            rect2_width = width
            rect2_height = height - rect1_height + 1
            rect1 = (x, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)
        else:
            rect1_width = width // 2 + 1
            rect1_height = height // 2 + 1
            rect2_width = width
            rect2_height = height - rect1_height + 1
            rect1 = (x + width - rect1_width, y, rect1_width, rect1_height)
            rect2 = (x, y + rect1_height - 1, rect2_width, rect2_height)

        self.carve_rectangular_room(rect1)
        self.carve_rectangular_room(rect2)

    def carve_irregular_room(self, room: tuple[int, int, int, int]) -> None:
        """
        Carve out an irregular/damaged room by starting with a rectangle
        and randomly removing corner sections.
        Creates unpredictable cover positions and looks like damaged infrastructure.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        self.carve_rectangular_room(room)

        num_removals = random.randint(2, 5)
        total_area = width * height
        removed_area = 0

        for _ in range(num_removals):
            if removed_area >= total_area * 0.3:
                break

            corner = random.choice(["top_left", "top_right", "bottom_left", "bottom_right"])

            remove_width = random.randint(1, min(3, width // 2))
            remove_height = random.randint(1, min(3, height // 2))

            if corner == "top_left":
                remove_x = x
                remove_y = y
            elif corner == "top_right":
                remove_x = x + width - remove_width
                remove_y = y
            elif corner == "bottom_left":
                remove_x = x
                remove_y = y + height - remove_height
            else:
                remove_x = x + width - remove_width
                remove_y = y + height - remove_height

            for rx in range(remove_x, remove_x + remove_width):
                for ry in range(remove_y, remove_y + remove_height):
                    if 0 <= rx < GameConfig.MAP_WIDTH and 0 <= ry < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.add((rx, ry))
                        removed_area += 1

    def carve_cross_room(self, room: tuple[int, int, int, int]) -> None:
        """
        Carve out a cross/plus-shaped room with 4 cardinal exit points.
        Creates interesting sightlines and forces checking multiple directions.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        vert_width = max(3, width // 3)
        vert_x = x + (width - vert_width) // 2
        vert_rect = (vert_x, y, vert_width, height)

        horiz_height = max(3, height // 3)
        horiz_y = y + (height - horiz_height) // 2
        horiz_rect = (x, horiz_y, width, horiz_height)

        self.carve_rectangular_room(vert_rect)
        self.carve_rectangular_room(horiz_rect)

    def carve_circular_room(self, room: tuple[int, int, int, int]) -> None:
        """
        Carve out a circular/oval room using midpoint circle algorithm.
        No corners to hide in - forces different tactical approach.
        Good for server core themed rooms.

        Args:
            room: Room tuple (x, y, width, height)
        """
        x, y, width, height = room

        center_x = x + width // 2
        center_y = y + height // 2
        radius_x = width // 2
        radius_y = height // 2

        for rx in range(x, x + width):
            for ry in range(y, y + height):
                dx = (rx - center_x) / radius_x
                dy = (ry - center_y) / radius_y
                if dx * dx + dy * dy <= 1.0:
                    if (rx, ry) in self.game_map.walls:
                        self.game_map.walls.remove((rx, ry))

    def apply_pillar_pattern(self, room: tuple[int, int, int, int], level: int) -> None:
        """
        Apply pillar pattern to a large room, creating server hall aesthetics.
        Excellent for stealth gameplay - many breaking points for line of sight.

        Args:
            room: Room tuple (x, y, width, height)
            level: Current level number (affects pillar chance)
        """
        network_configs = GameConfig.NETWORK_CONFIGS()
        if level in network_configs:
            level_config = network_configs[level]
            if (
                "level_generation" in level_config
                and "pillar_room_chance" in level_config["level_generation"]
            ):
                pillar_chance = level_config["level_generation"]["pillar_room_chance"]
            else:
                pillar_chance = GameConfig._get_required("room_generation.pillar_room_chance")
        else:
            pillar_chance = GameConfig._get_required("room_generation.pillar_room_chance")

        if random.random() > pillar_chance:
            return

        x, y, width, height = room
        pillar_spacing = GameConfig._get_required("room_generation.pillar_grid_spacing")

        for rx in range(x + pillar_spacing, x + width - 1, pillar_spacing + 1):
            for ry in range(y + pillar_spacing, y + height - 1, pillar_spacing + 1):
                if (rx, ry) not in self.game_map.walls:
                    self.game_map.walls.add((rx, ry))

    def generate_rooms_avoiding_existing(
        self, level: int, existing_rooms: list[tuple[int, int, int, int]]
    ) -> list[tuple[int, int, int, int]]:
        """
        Generate room layouts for the level with zone-based placement.

        Args:
            level: Current level number (affects room count)
            existing_rooms: List of already placed rooms to avoid

        Returns:
            List of newly generated room tuples (x, y, width, height)
        """
        num_rooms = (
            RoomGenerationConfig.MIN_ROOMS_BASE + level * RoomGenerationConfig.ROOM_LEVEL_MULTIPLIER
        )
        max_rooms = min(num_rooms, RoomGenerationConfig.MAX_ROOMS)
        max_attempts = RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS

        logging.debug(
            f"Room Gen: Attempting to generate {max_rooms} rooms (max_attempts={max_attempts})"
        )

        new_rooms = []
        all_rooms = existing_rooms.copy()
        room_type_counts = {}

        for _ in range(max_attempts):
            if len(new_rooms) >= max_rooms:
                break

            room_width = random.randint(
                RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE
            )
            room_height = random.randint(
                RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE
            )
            room_x = random.randint(12, GameConfig.MAP_WIDTH - room_width - 2)
            room_y = random.randint(12, GameConfig.MAP_HEIGHT - room_height - 2)

            new_room = (room_x, room_y, room_width, room_height)

            if not self.room_overlaps(new_room, all_rooms):
                room_type = self.select_room_type(level, room_width, room_height)
                room_type_counts[room_type] = room_type_counts.get(room_type, 0) + 1

                new_rooms.append(new_room)
                all_rooms.append(new_room)

                self.carve_room(new_room, room_type, level)
                logging.debug(
                    f"Room Gen: Room {len(new_rooms)}: type={room_type}, pos=({room_x},{room_y}), size={room_width}x{room_height}"
                )

        logging.debug(
            f"Room Gen: Successfully placed {len(new_rooms)} rooms, types={room_type_counts}"
        )
        return new_rooms

    def room_overlaps(
        self, new_room: tuple[int, int, int, int], existing_rooms: list[tuple[int, int, int, int]]
    ) -> bool:
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
            if (
                x1 < x2 + w2 + pad
                and x1 + w1 + pad > x2
                and y1 < y2 + h2 + pad
                and y1 + h1 + pad > y2
            ):
                return True
        return False


# ============================================================================
# BSP-BASED ROOM GENERATION
# ============================================================================


class BSPRoomGenerator(RoomGenerator):
    """
    BSP-based room generator using TCOD's Binary Space Partitioning.

    Uses BSP to partition the map space into organic regions, then applies
    the existing room types (rectangular, L-shaped, etc.) to each leaf node.

    Benefits over random placement:
    - Better spatial distribution (no clustering)
    - More organic layouts
    - Automatic hierarchy for corridor planning
    - Guaranteed room connectivity via BSP tree structure

    Attributes:
        game_map: GameMap instance to populate
        bsp_tree: Root BSP node for the current level
        leaf_rooms: List of rooms created in BSP leaf nodes
    """

    def __init__(self, game_map):
        """
        Initialize BSP room generator.

        Args:
            game_map: GameMap instance to modify
        """
        super().__init__(game_map)
        self.bsp_tree: tcod.bsp.BSP | None = None
        self.leaf_rooms: list[tuple[int, int, int, int]] = []

    def create_bsp_rooms(self, level: int) -> list[tuple[int, int, int, int]]:
        """
        Create rooms using BSP space partitioning.

        Uses TCOD's BSP algorithm to partition the map into regions,
        then creates a room in each leaf node using existing room types.

        Args:
            level: Current level number (affects BSP depth and room types)

        Returns:
            List of room tuples (x, y, width, height)
        """
        logging.debug(f"BSP Gen: Starting BSP-based room generation for level {level}")

        # Create BSP tree - partition the entire map
        # Leave border space for walls
        margin = 2
        self.bsp_tree = tcod.bsp.BSP(
            x=margin,
            y=margin,
            width=GameConfig.MAP_WIDTH - margin * 2,
            height=GameConfig.MAP_HEIGHT - margin * 2,
        )

        # Configure BSP splitting
        # Higher levels = deeper splits = more rooms
        depth = min(7, 5 + (level // 2))  # 5-7 depth based on level
        min_room_size = RoomGenerationConfig.MIN_ROOM_SIZE + 2  # Add padding

        logging.debug(
            f"BSP Gen: Partitioning with depth={depth}, min_size={min_room_size}x{min_room_size}"
        )

        # Recursively split the space
        self.bsp_tree.split_recursive(
            depth=depth,
            min_width=min_room_size,
            min_height=min_room_size,
            max_horizontal_ratio=1.5,  # Prefer more square-ish partitions
            max_vertical_ratio=1.5,
        )

        # Create rooms in leaf nodes
        self.leaf_rooms = []
        self._create_rooms_in_leaves(self.bsp_tree, level)

        logging.debug(f"BSP Gen: Created {len(self.leaf_rooms)} BSP rooms")
        return self.leaf_rooms

    def _create_rooms_in_leaves(self, node: tcod.bsp.BSP, level: int) -> None:
        """
        Recursively traverse BSP tree and create rooms in leaf nodes.

        Args:
            node: Current BSP node
            level: Current level number for room type selection
        """
        # If this node has children, recurse into them
        if node.children:
            for child in node.children:
                self._create_rooms_in_leaves(child, level)
            return

        # Leaf node - create a room within this partition
        # Leave some space between room and partition boundary for walls
        padding = random.randint(1, 3)

        room_width = node.width - padding * 2
        room_height = node.height - padding * 2

        # Ensure minimum room size
        if (
            room_width < RoomGenerationConfig.MIN_ROOM_SIZE
            or room_height < RoomGenerationConfig.MIN_ROOM_SIZE
        ):
            logging.debug(f"BSP Gen: Skipping too-small partition: {room_width}x{room_height}")
            return

        # Randomly position room within partition (creates irregular spacing)
        max_offset_x = padding
        max_offset_y = padding
        offset_x = random.randint(0, max_offset_x)
        offset_y = random.randint(0, max_offset_y)

        room_x = node.x + offset_x
        room_y = node.y + offset_y

        # Clamp to max room size if needed
        room_width = min(room_width, RoomGenerationConfig.MAX_ROOM_SIZE)
        room_height = min(room_height, RoomGenerationConfig.MAX_ROOM_SIZE)

        room = (room_x, room_y, room_width, room_height)

        # Select room type based on size and level
        room_type = self.select_room_type(level, room_width, room_height)

        # Carve the room
        self.carve_room(room, room_type, level)
        self.leaf_rooms.append(room)

        logging.debug(
            f"BSP Gen: Leaf room created: type={room_type}, pos=({room_x},{room_y}), size={room_width}x{room_height}"
        )

    def connect_bsp_rooms(self, corridor_generator) -> None:
        """
        Connect BSP rooms using the tree hierarchy.

        Traverses the BSP tree and creates corridors connecting sibling nodes.
        This ensures all rooms are connected while creating organic pathways.

        Args:
            corridor_generator: CorridorGenerator instance for creating corridors
        """
        if not self.bsp_tree:
            logging.warning("BSP Gen: No BSP tree available for room connection")
            return

        logging.debug(f"BSP Gen: Connecting {len(self.leaf_rooms)} BSP rooms via tree structure")
        self._connect_nodes(self.bsp_tree, corridor_generator)

    def _connect_nodes(self, node: tcod.bsp.BSP, corridor_generator) -> tuple[int, int]:
        """
        Recursively connect BSP nodes.

        For each node, get connection points from children and create corridor
        between them. This creates organic pathways following BSP structure.

        Args:
            node: Current BSP node
            corridor_generator: CorridorGenerator for corridor creation

        Returns:
            Tuple (x, y) representing connection point for this subtree
        """
        # Calculate center point (BSP nodes don't have a .center attribute)
        center_x = node.x + node.width // 2
        center_y = node.y + node.height // 2

        # Leaf node - return center point
        if not node.children:
            return (center_x, center_y)

        # Internal node - connect children and return our connection point
        child1, child2 = node.children
        point1 = self._connect_nodes(child1, corridor_generator)
        point2 = self._connect_nodes(child2, corridor_generator)

        # Create corridor between the two child connection points
        x1, y1 = point1
        x2, y2 = point2

        # Use existing corridor generation with random width
        corridor_width = corridor_generator.get_corridor_width()
        corridor_generator.create_curved_corridor(x1, y1, x2, y2, corridor_width)

        logging.debug(f"BSP Gen: Connected ({x1},{y1}) <-> ({x2},{y2}), width={corridor_width}")

        # Return our center as connection point for parent
        return (center_x, center_y)


# ============================================================================
# CORRIDOR GENERATION
# ============================================================================


class CorridorGenerator:
    """
    Corridor generation subsystem handling room connections and corridor features.

    Coordinates MST-based room connection, extra path creation, alcove placement,
    and intersection expansion into junctions.

    Attributes:
        game_map: GameMap instance to populate with corridors
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
    """

    def __init__(self, game_map, corridor_tiles: set[tuple[int, int]]):
        """
        Initialize corridor generator with game map and corridor tracking.

        Args:
            game_map: GameMap instance to modify during corridor generation
            corridor_tiles: Set to track corridor tile positions for alcove placement
        """
        self.game_map = game_map
        self.corridor_tiles = corridor_tiles

    def connect_rooms_mst(self, rooms: list[tuple[int, int, int, int]]) -> None:
        """
        Connect rooms using minimum spanning tree approach.

        Ensures all rooms are connected with minimum total corridor length.
        Creates base connectivity graph for the level.

        Args:
            rooms: List of room tuples (x, y, width, height)
        """
        if len(rooms) < 2:
            logging.debug(f"Corridor Gen: Skipping MST (only {len(rooms)} room)")
            return

        logging.debug(f"Corridor Gen: Building MST for {len(rooms)} rooms")
        connected = [rooms[0]]
        unconnected = rooms[1:]
        edges_created = 0

        while unconnected:
            min_distance = float("inf")
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
                edges_created += 1

        logging.debug(f"Corridor Gen: MST complete, created {edges_created} corridor connections")

    def add_extra_paths(self, rooms: list[tuple[int, int, int, int]]) -> None:
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
            logging.debug(f"Corridor Gen: Skipping extra paths (only {len(rooms)} rooms)")
            return

        extra_connections = min(random.randint(2, 4), len(rooms) // 2)
        logging.debug(f"Corridor Gen: Adding {extra_connections} extra paths for loops")
        for _ in range(extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice(rooms)
            if room1 != room2:
                self.create_corridor_between_rooms(room1, room2)

    def create_corridor_between_rooms(
        self, room1: tuple[int, int, int, int], room2: tuple[int, int, int, int]
    ) -> None:
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

        width = self.get_corridor_width()

        curved_chance = GameConfig._get_required("room_generation.curved_corridor_chance")
        if random.random() < curved_chance:
            self.create_curved_corridor(x1, y1, x2, y2, width)
        else:
            if random.choice([True, False]):
                self.carve_corridor_segment(
                    min(x1, x2), max(x1, x2), y1, y1, width, horizontal=True
                )
                self.carve_corridor_segment(
                    x2, x2, min(y1, y2), max(y1, y2), width, horizontal=False
                )
            else:
                self.carve_corridor_segment(
                    x1, x1, min(y1, y2), max(y1, y2), width, horizontal=False
                )
                self.carve_corridor_segment(
                    min(x1, x2), max(x1, x2), y2, y2, width, horizontal=True
                )

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

        narrow_weight = GameConfig._get_required("room_generation.corridor_width_weights.narrow")
        medium_weight = GameConfig._get_required("room_generation.corridor_width_weights.medium")
        wide_weight = GameConfig._get_required("room_generation.corridor_width_weights.wide")

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
        line_points = self.bresenham_line(x1, y1, x2, y2)

        for x, y in line_points:
            half_width = width // 2
            for dx in range(-half_width, (width + 1) // 2):
                for dy in range(-half_width, (width + 1) // 2):
                    px = x + dx
                    py = y + dy
                    if 0 <= px < GameConfig.MAP_WIDTH and 0 <= py < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((px, py))
                        self.corridor_tiles.add((px, py))

    def bresenham_line(self, x1: int, y1: int, x2: int, y2: int) -> list[tuple[int, int]]:
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

    def carve_corridor_segment(
        self, x_start: int, x_end: int, y_start: int, y_end: int, width: int, horizontal: bool
    ) -> None:
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
            for x in range(x_start, x_end + 1):
                for offset in range(-(width // 2), (width + 1) // 2):
                    y = y_start + offset
                    if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((x, y))
                        self.corridor_tiles.add((x, y))
        else:
            for y in range(y_start, y_end + 1):
                for offset in range(-(width // 2), (width + 1) // 2):
                    x = x_start + offset
                    if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                        self.game_map.walls.discard((x, y))
                        self.corridor_tiles.add((x, y))

    def add_corridor_alcoves(self) -> None:
        """
        Add alcoves to straight corridor segments for stealth hiding spots.

        Alcoves are small 1-tile indentations off the main corridor.
        They provide:
        - Stealth hiding spots (shadows automatically placed)
        - Tactical cover positions
        - Visual variety in corridor design
        """
        alcove_chance = GameConfig._get_required("room_generation.corridor_alcove_chance")
        min_segment_length = GameConfig._get_required("room_generation.corridor_alcove_min_length")

        horizontal_segments = self.find_straight_corridor_segments(horizontal=True)
        vertical_segments = self.find_straight_corridor_segments(horizontal=False)

        alcoves_created = 0
        for segment in horizontal_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self.create_alcoves_on_segment(segment, horizontal=True)
                alcoves_created += 1

        for segment in vertical_segments:
            if len(segment) >= min_segment_length and random.random() < alcove_chance:
                self.create_alcoves_on_segment(segment, horizontal=False)
                alcoves_created += 1

        logging.debug(
            f"Corridor Gen: Created {alcoves_created} alcoves from {len(horizontal_segments)} H + {len(vertical_segments)} V segments"
        )

    def find_straight_corridor_segments(self, horizontal: bool) -> list[list[tuple[int, int]]]:
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
                segment = []
                start_x = x
                while (start_x - 1, y) in self.corridor_tiles:
                    start_x -= 1

                curr_x = start_x
                while (curr_x, y) in self.corridor_tiles:
                    if (curr_x, y) not in processed:
                        segment.append((curr_x, y))
                        processed.add((curr_x, y))
                    curr_x += 1

                if len(segment) > 0:
                    segments.append(segment)
            else:
                segment = []
                start_y = y
                while (x, start_y - 1) in self.corridor_tiles:
                    start_y -= 1

                curr_y = start_y
                while (x, curr_y) in self.corridor_tiles:
                    if (x, curr_y) not in processed:
                        segment.append((x, curr_y))
                        processed.add((x, curr_y))
                    curr_y += 1

                if len(segment) > 0:
                    segments.append(segment)

        return segments

    def create_alcoves_on_segment(self, segment: list[tuple[int, int]], horizontal: bool) -> None:
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

        num_alcoves = random.randint(1, min(2, len(segment) // 4))

        valid_positions = segment[1:-1]
        if len(valid_positions) < num_alcoves:
            return

        alcove_positions = random.sample(valid_positions, num_alcoves)

        for pos in alcove_positions:
            x, y = pos

            if horizontal:
                direction = random.choice([-1, 1])
                alcove_pos = (x, y + direction)
            else:
                direction = random.choice([-1, 1])
                alcove_pos = (x + direction, y)

            if (
                0 <= alcove_pos[0] < GameConfig.MAP_WIDTH
                and 0 <= alcove_pos[1] < GameConfig.MAP_HEIGHT
                and alcove_pos in self.game_map.walls
            ):

                self.game_map.walls.discard(alcove_pos)

                self.game_map.blind_spots.add(alcove_pos)

    def create_corridor_intersections(self) -> None:
        """
        Create T-junctions and 4-way intersections where corridors meet.

        Expands intersection points into larger junction rooms with:
        - Increased tactical complexity
        - Corner shadows for stealth
        - Multiple approach angles
        """
        intersection_chance = GameConfig._get_required(
            "room_generation.corridor_intersection_chance"
        )
        min_junction_size = GameConfig._get_required(
            "room_generation.corridor_intersection_min_size"
        )
        max_junction_size = GameConfig._get_required(
            "room_generation.corridor_intersection_max_size"
        )

        intersections = self.find_corridor_intersections()
        logging.debug(f"Corridor Gen: Found {len(intersections)} corridor intersections")

        junctions_created = 0
        for intersection_pos in intersections:
            if random.random() < intersection_chance:
                junction_size = random.choice([min_junction_size, max_junction_size])
                self.expand_intersection_into_junction(intersection_pos, junction_size)
                junctions_created += 1

        logging.debug(f"Corridor Gen: Created {junctions_created} T-junction/4-way rooms")

    def find_corridor_intersections(self) -> list[tuple[int, int]]:
        """
        Find points where 3 or more corridor segments meet.

        Identifies T-junctions (3 connections) and 4-way intersections (4 connections).

        Returns:
            List of (x, y) positions that are intersection points
        """
        intersections = []

        for tile in self.corridor_tiles:
            x, y = tile

            corridor_neighbors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in self.corridor_tiles:
                    corridor_neighbors += 1

            if corridor_neighbors >= 3:
                intersections.append(tile)

        return intersections

    def expand_intersection_into_junction(self, center: tuple[int, int], size: int) -> None:
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

        for jx in range(x - half_size, x + half_size + 1):
            for jy in range(y - half_size, y + half_size + 1):
                if 0 <= jx < GameConfig.MAP_WIDTH and 0 <= jy < GameConfig.MAP_HEIGHT:
                    if (jx, jy) in self.game_map.walls:
                        self.game_map.walls.discard((jx, jy))
                        self.corridor_tiles.add((jx, jy))

        corners = [
            (x - half_size, y - half_size),
            (x + half_size, y - half_size),
            (x - half_size, y + half_size),
            (x + half_size, y + half_size),
        ]

        for corner in corners:
            cx, cy = corner
            if (
                0 <= cx < GameConfig.MAP_WIDTH
                and 0 <= cy < GameConfig.MAP_HEIGHT
                and (cx, cy) not in self.game_map.walls
                and (cx, cy) in self.corridor_tiles
            ):
                self.game_map.blind_spots.add((cx, cy))
