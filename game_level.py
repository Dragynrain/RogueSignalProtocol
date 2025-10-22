"""
Procedural level generation with room types, corridors, and tactical features.

This module handles multi-phase level generation:
- Phase 1: Room creation with varied types (rectangular, L-shaped, irregular, cross, circular)
- Phase 2: Room connection using MST + extra paths for multiple routes
- Phase 3: Hub-and-spoke patterns, looping paths for stealth options
- Phase 4: Landmark rooms (central plazas, long halls), T-junctions, intersections
- Phase 5: Tactical features (choke points, defensive positions, loot clustering)
- Item/node placement: Strategic positioning based on room types and corridors

Key algorithms:
- Minimum Spanning Tree (MST) for base connectivity
- Alcove generation in corridors for hiding spots
- Shadow placement for stealth gameplay
- Cover elements in open areas
- Gateway placement with minimum distance from spawn

Architecture:
The LevelGenerator now coordinates specialized subsystems:
- RoomGenerator: Room creation and carving
- CorridorGenerator: MST connectivity and corridor features
- TacticalGenerator: Shadows, cover, defensive positions, choke points
- AdvancedLayoutGenerator: Hubs, loops, shadow zones, landmarks, zones
- TilePlacementGenerator: Special tiles and gateway placement
"""

import random
import logging
from typing import List, Tuple

# Import required classes and configs
from game_config import GameConfig

# Import specialized level generation subsystems
from game_level_structure import RoomGenerator, CorridorGenerator
from game_level_features import TacticalGenerator, AdvancedLayoutGenerator, TilePlacementGenerator


class LevelGenerator:
    """
    Procedural level generator coordinating multi-phase map creation.

    The generator orchestrates several subsystems via delegation:
    - Room generation with varied shapes and sizes (configurable per level)
    - Corridor creation using MST algorithm + extra paths
    - Tactical feature placement (cover, shadows, alcoves, intersections)
    - Advanced layout features (hubs, loops, landmarks, zones)
    - Item/node distribution (strategic positioning in rooms and corridors)
    - Gateway placement with spawn distance constraints

    Generation flow:
    1. Clear existing level data
    2. Fill map with walls
    3. Generate rooms with varied types (RoomGenerator)
    4. Connect rooms (CorridorGenerator: MST + extra paths + loops + hubs)
    5. Add tactical features (TacticalGenerator: alcoves, intersections, cover, shadows)
    6. Add advanced features (AdvancedLayoutGenerator: landmarks, hubs, zones)
    7. Place special tiles (TilePlacementGenerator: items, nodes, gateway)
    8. Invalidate FOV cache for new layout

    Attributes:
        game_map: GameMap instance to populate with generated content
        corridor_tiles: Set of (x, y) tuples tracking corridor positions
        last_generated_rooms: List of room bounds (x, y, w, h) from last generation
        room_generator: Subsystem for room creation
        corridor_generator: Subsystem for corridor creation
        tactical_generator: Subsystem for tactical features
        advanced_generator: Subsystem for advanced layout features
        placement_generator: Subsystem for special tile placement
    """

    def __init__(self, game_map):
        """
        Initialize level generator with game map and subsystems.

        Args:
            game_map: GameMap instance to populate with generated content
        """
        self.game_map = game_map
        self.corridor_tiles = set()  # Track corridor tiles for alcove placement

        # Initialize specialized subsystems
        self.room_generator = RoomGenerator(game_map)
        self.corridor_generator = CorridorGenerator(game_map, self.corridor_tiles)
        self.tactical_generator = TacticalGenerator(game_map, self.corridor_tiles)
        self.placement_generator = TilePlacementGenerator(game_map)

        # Advanced generator needs references to other subsystems for cross-system operations
        self.advanced_generator = AdvancedLayoutGenerator(
            game_map,
            self.corridor_tiles,
            self.room_generator,
            self.corridor_generator,
            self.tactical_generator
        )

    def generate_level(self, level: int, seed: int) -> None:
        """
        Generate a complete level from scratch using seeded RNG.

        Coordinates the entire generation pipeline:
        1. Set RNG seed for reproducibility (seed + level)
        2. Clear previous level data
        3. Generate rooms, corridors, and tactical features
        4. Place special tiles (items, nodes, gateway)
        5. Invalidate FOV cache to reflect new walls

        Args:
            level: Current level number (affects difficulty, room counts, items)
            seed: Base RNG seed (combined with level for reproducibility)
        """
        logging.debug(f"Level Gen: === Level {level} Generation START (seed={seed}) ===")
        import time
        start_time = time.time()

        random.seed(seed + level)

        # Clear existing level data
        self._clear_level_data()

        # Generate the level structure
        self._generate_procedural_level(level)

        # Place special tiles and items
        # Pass landmark rooms for objective-oriented placement
        landmark_rooms = getattr(self, '_landmark_rooms', [])
        self.placement_generator.place_special_tiles(level, landmark_rooms=landmark_rooms)

        # Use strategic gateway placement
        self.placement_generator.place_gateway_strategic(level)

        # Final invalidation to ensure FOV calculations use the correct wall layout
        self.game_map.invalidate_transparency_cache()

        generation_time = time.time() - start_time
        rooms_count = len(getattr(self, 'last_generated_rooms', []))
        corridor_count = len(self.corridor_tiles)

        logging.debug(f"Level Gen: Level {level} complete in {generation_time:.3f}s: rooms={rooms_count}, corridor_tiles={corridor_count}")

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
        """
        Generate the core level structure with multi-phase room/corridor creation.

        This is the main generation orchestrator that executes all phases:
        - Room creation with varied types and guaranteed spawn room
        - MST-based connectivity + extra paths for routing options
        - Hub-and-spoke patterns and looping paths for stealth
        - Landmark rooms, corridor intersections, and alcoves
        - Tactical features (choke points, cover, shadows, defensive positions)
        - Loot room identification for item clustering

        The algorithm prioritizes gameplay variety (multiple paths, hiding spots,
        tactical positions) over pure dungeon aesthetics.

        Args:
            level: Current level number for difficulty scaling
        """
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # PHASE 1: Create rooms with varied types
        logging.debug(f"Level Gen: Phase 1 - Creating varied rooms for level {level}")
        rooms = self.room_generator.create_varied_rooms(level)
        logging.debug(f"Level Gen: Phase 1 complete: {len(rooms)} rooms created")

        # PHASE 3: Identify hub rooms before connecting
        logging.debug(f"Level Gen: Phase 2 - Identifying hub rooms")
        hub_rooms = self.advanced_generator.identify_hub_rooms(rooms)
        logging.debug(f"Level Gen: Identified {len(hub_rooms)} hub rooms")

        # PHASE 2: Connect rooms using MST approach for better connectivity
        logging.debug(f"Level Gen: Phase 2 - Connecting rooms with MST")
        self.corridor_generator.connect_rooms_mst(rooms)

        # Add extra paths for multiple routes (good for stealth)
        self.corridor_generator.add_extra_paths(rooms)
        logging.debug(f"Level Gen: Phase 2 complete: {len(self.corridor_tiles)} corridor tiles created")

        # PHASE 3: Create looping paths for better stealth options
        logging.debug(f"Level Gen: Phase 3 - Creating looping paths")
        self.advanced_generator.create_looping_paths(rooms)

        # PHASE 3: Connect hub rooms to create hub-and-spoke pattern
        self.advanced_generator.connect_hub_rooms(hub_rooms, rooms)

        # PHASE 5: Create choke points along critical path
        logging.debug(f"Level Gen: Phase 3 - Creating choke points")
        self.tactical_generator.create_choke_points(rooms)

        # PHASE 4: Create landmark rooms
        logging.debug(f"Level Gen: Phase 4 - Creating landmark rooms")
        landmark_rooms = self.advanced_generator.create_landmark_rooms(level, rooms)
        # Store for later use in special tile placement
        self._landmark_rooms = landmark_rooms
        logging.debug(f"Level Gen: Created {len(landmark_rooms)} landmark rooms: {[lm['type'] for lm in landmark_rooms]}")

        # Add alcoves to corridors for stealth hiding spots
        logging.debug(f"Level Gen: Phase 4 - Adding corridor alcoves")
        self.corridor_generator.add_corridor_alcoves()

        # PHASE 4: Create T-junctions and 4-way intersections
        self.corridor_generator.create_corridor_intersections()

        # Add strategic cover elements in open areas
        logging.debug(f"Level Gen: Phase 4 - Adding cover elements")
        self.tactical_generator.add_cover_elements_new()

        # PHASE 3: Create shadow zones first
        logging.debug(f"Level Gen: Phase 5 - Creating shadow zones")
        shadow_zone_rooms = self.advanced_generator.create_shadow_zones(rooms)
        logging.debug(f"Level Gen: Created {len(shadow_zone_rooms)} shadow zone rooms")

        # Add shadow areas for stealth gameplay (with shadow zones)
        logging.debug(f"Level Gen: Phase 5 - Placing shadow areas")
        self.tactical_generator.place_shadow_areas(level, rooms, shadow_zone_rooms)
        logging.debug(f"Level Gen: Placed {len(self.game_map.shadows)} shadow tiles")

        # PHASE 5: Add defensive positions (cover + shadow combinations)
        self.tactical_generator.place_defensive_positions(rooms)

        # PHASE 5: Identify loot rooms for item clustering
        self.advanced_generator.identify_loot_rooms(rooms)

        # PHASE 4: Clean up any shadows that ended up on walls (from cover placement)
        before_cleanup = len(self.game_map.shadows)
        self.tactical_generator.cleanup_invalid_shadows()
        after_cleanup = len(self.game_map.shadows)
        if before_cleanup != after_cleanup:
            logging.debug(f"Level Gen: Shadow cleanup removed {before_cleanup - after_cleanup} invalid shadows")

        # Ensure border walls are intact
        self.placement_generator.ensure_border_walls_new()

        # Store final room list
        self.last_generated_rooms = rooms

    # ========================================================================
    # Backward Compatibility: Pass-through methods for testing
    # These delegate to the appropriate subsystem for backward compatibility
    # ========================================================================

    # Room generation pass-throughs
    def _select_room_type(self, level, width, height):
        return self.room_generator.select_room_type(level, width, height)

    def _get_room_type_weights(self, level):
        return self.room_generator.get_room_type_weights(level)

    def _carve_rectangular_room(self, room):
        return self.room_generator.carve_rectangular_room(room)

    def _carve_l_shaped_room(self, room):
        return self.room_generator.carve_l_shaped_room(room)

    def _carve_irregular_room(self, room):
        return self.room_generator.carve_irregular_room(room)

    def _carve_cross_room(self, room):
        return self.room_generator.carve_cross_room(room)

    def _carve_circular_room(self, room):
        return self.room_generator.carve_circular_room(room)

    def _apply_pillar_pattern(self, room, level):
        return self.room_generator.apply_pillar_pattern(room, level)

    def _room_overlaps(self, new_room, existing_rooms):
        return self.room_generator.room_overlaps(new_room, existing_rooms)

    def _carve_room(self, room, room_type='rectangular', level=1):
        return self.room_generator.carve_room(room, room_type, level)

    # Corridor generation pass-throughs
    def _get_corridor_width(self):
        return self.corridor_generator.get_corridor_width()

    def _carve_corridor_segment(self, x_start, x_end, y_start, y_end, width, horizontal):
        return self.corridor_generator.carve_corridor_segment(x_start, x_end, y_start, y_end, width, horizontal)

    def _find_straight_corridor_segments(self, horizontal):
        return self.corridor_generator.find_straight_corridor_segments(horizontal)

    def _create_alcoves_on_segment(self, segment, horizontal):
        return self.corridor_generator.create_alcoves_on_segment(segment, horizontal)

    def _find_corridor_intersections(self):
        return self.corridor_generator.find_corridor_intersections()

    def _expand_intersection_into_junction(self, center, size):
        return self.corridor_generator.expand_intersection_into_junction(center, size)

    def _bresenham_line(self, x1, y1, x2, y2):
        return self.corridor_generator.bresenham_line(x1, y1, x2, y2)

    def _create_curved_corridor(self, x1, y1, x2, y2, width):
        return self.corridor_generator.create_curved_corridor(x1, y1, x2, y2, width)

    def _create_corridor_between_rooms(self, room1, room2):
        return self.corridor_generator.create_corridor_between_rooms(room1, room2)

    # Tactical generation pass-throughs
    def _get_wall_adjacent_positions(self, room):
        return self.tactical_generator.get_wall_adjacent_positions(room)

    def _get_interior_positions(self, room):
        return self.tactical_generator.get_interior_positions(room)

    def _poisson_disc_sampling(self, area, radius):
        return self.tactical_generator.poisson_disc_sampling(area, radius)

    def _find_large_open_areas(self, min_size):
        return self.tactical_generator.find_large_open_areas(min_size)

    def _is_valid_cover_position(self, pos):
        return self.tactical_generator.is_valid_cover_position(pos)

    def _create_cover_cluster(self, center):
        return self.tactical_generator.create_cover_cluster(center)

    def _narrow_corridor_at_position(self, position):
        return self.tactical_generator.narrow_corridor_at_position(position)

    def _create_corner_cover_position(self, x, y):
        return self.tactical_generator.create_corner_cover_position(x, y)

    def _create_shadow_bunker_position(self, x, y):
        return self.tactical_generator.create_shadow_bunker_position(x, y)

    def _create_crossfire_position(self, x, y):
        return self.tactical_generator.create_crossfire_position(x, y)

    # Advanced layout pass-throughs
    def _identify_hub_rooms(self, rooms):
        return self.advanced_generator.identify_hub_rooms(rooms)

    def _expand_hub_room(self, room):
        return self.advanced_generator.expand_hub_room(room)

    def _build_room_connectivity_graph(self, rooms):
        return self.advanced_generator.build_room_connectivity_graph(rooms)

    def _create_shadow_zones(self, rooms):
        return self.advanced_generator.create_shadow_zones(rooms)

    def _find_room_clusters(self, rooms, min_size):
        return self.advanced_generator.find_room_clusters(rooms, min_size)

    def _room_distance(self, room1, room2):
        return self.advanced_generator.room_distance(room1, room2)

    def _create_landmark_rooms(self, level, rooms):
        return self.advanced_generator.create_landmark_rooms(level, rooms)

    def _create_server_core_landmark(self, existing_rooms, level):
        return self.advanced_generator.create_server_core_landmark(existing_rooms, level)

    def _create_vault_landmark(self, existing_rooms):
        return self.advanced_generator.create_vault_landmark(existing_rooms)

    def _create_arena_landmark(self, existing_rooms):
        return self.advanced_generator.create_arena_landmark(existing_rooms)

    def _create_map_zones(self):
        return self.advanced_generator.create_map_zones()

    def _get_zone_for_room(self, room, zones):
        return self.advanced_generator.get_zone_for_room(room, zones)

    # Placement pass-throughs
    def _select_gateway_strategy(self):
        return self.placement_generator.select_gateway_strategy()

    def _gateway_far_corner(self, spawn, floor_positions):
        return self.placement_generator.gateway_far_corner(spawn, floor_positions)

    def _gateway_central_hub(self, floor_positions):
        return self.placement_generator.gateway_central_hub(floor_positions)

    def _gateway_hidden_dead_end(self, floor_positions):
        return self.placement_generator.gateway_hidden_dead_end(floor_positions)

    def _gateway_gauntlet(self, spawn, floor_positions):
        return self.placement_generator.gateway_gauntlet(spawn, floor_positions)

    def _get_high_traffic_positions(self, floor_positions):
        return self.placement_generator.get_high_traffic_positions(floor_positions)

    def _get_peripheral_positions(self, floor_positions):
        return self.placement_generator.get_peripheral_positions(floor_positions)

    def _get_shadow_adjacent_positions(self, floor_positions):
        return self.placement_generator.get_shadow_adjacent_positions(floor_positions)

    def _get_all_floor_positions(self):
        return self.placement_generator.get_all_floor_positions()
