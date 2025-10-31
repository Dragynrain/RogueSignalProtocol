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
from game_entities import Position
from game_characters import PathfindingHelper

# Import specialized level generation subsystems
from game_level_structure import RoomGenerator, BSPRoomGenerator, CorridorGenerator
from game_level_tactical import TacticalGenerator
from game_level_layout import AdvancedLayoutGenerator
from game_level_placement import TilePlacementGenerator


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

    def __init__(self, game_map, use_bsp: bool = False):
        """
        Initialize level generator with game map and subsystems.

        Args:
            game_map: GameMap instance to populate with generated content
            use_bsp: If True, use BSP-based room generation instead of random placement
        """
        self.game_map = game_map
        self.corridor_tiles = set()  # Track corridor tiles for alcove placement
        self.use_bsp = use_bsp  # Toggle between BSP and traditional generation

        # Initialize specialized subsystems
        # Choose BSP or traditional room generator
        if use_bsp:
            self.room_generator = BSPRoomGenerator(game_map)
            logging.debug("Level Gen: Using BSP-based room generation")
        else:
            self.room_generator = RoomGenerator(game_map)
            logging.debug("Level Gen: Using traditional random room placement")

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

        # Seed both Python random (for legacy code) and TCOD random (for new code)
        random.seed(seed + level)
        from game_level_structure import seed_rng
        seed_rng(seed + level)

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

        # CRITICAL: Validate gateway is reachable from spawn
        spawn_pos = Position(6, 6)  # Spawn room center
        gateway_pos = self.game_map.gateway

        if not self._validate_gateway_reachability(spawn_pos, gateway_pos):
            logging.error(f"Level Gen: CRITICAL - Gateway at {gateway_pos} is NOT reachable from spawn {spawn_pos}!")
            self._fix_unreachable_gateway(level, seed, spawn_pos, gateway_pos)

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

        # PHASE 1: Create rooms with varied types (BSP or traditional)
        if self.use_bsp:
            logging.debug(f"Level Gen: Phase 1 - Creating BSP rooms for level {level}")
            rooms = self.room_generator.create_bsp_rooms(level)
            logging.debug(f"Level Gen: Phase 1 complete: {len(rooms)} BSP rooms created")
        else:
            logging.debug(f"Level Gen: Phase 1 - Creating varied rooms for level {level}")
            rooms = self.room_generator.create_varied_rooms(level)
            logging.debug(f"Level Gen: Phase 1 complete: {len(rooms)} rooms created")

        # PHASE 3: Identify hub rooms before connecting
        logging.debug(f"Level Gen: Phase 2 - Identifying hub rooms")
        hub_rooms = self.advanced_generator.identify_hub_rooms(rooms)
        logging.debug(f"Level Gen: Identified {len(hub_rooms)} hub rooms")

        # PHASE 2: Connect rooms (BSP tree-based or MST)
        if self.use_bsp:
            logging.debug(f"Level Gen: Phase 2 - Connecting rooms via BSP tree")
            self.room_generator.connect_bsp_rooms(self.corridor_generator)
            logging.debug(f"Level Gen: Phase 2 complete: {len(self.corridor_tiles)} corridor tiles created (BSP)")
        else:
            logging.debug(f"Level Gen: Phase 2 - Connecting rooms with MST")
            self.corridor_generator.connect_rooms_mst(rooms)
            logging.debug(f"Level Gen: Phase 2 complete: {len(self.corridor_tiles)} corridor tiles created (MST)")

        # Add extra paths for multiple routes (good for stealth) - works for both BSP and traditional
        self.corridor_generator.add_extra_paths(rooms)
        logging.debug(f"Level Gen: Added extra paths for routing options")

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

    def _validate_gateway_reachability(self, spawn_pos: Position, gateway_pos: Position) -> bool:
        """
        Validate that the gateway is reachable from spawn position using pathfinding.

        This is a critical validation to ensure the level is playable.
        Without this, players can spawn in sealed rooms with no way to reach the exit.

        Args:
            spawn_pos: Player spawn position
            gateway_pos: Gateway/exit position

        Returns:
            True if gateway is reachable, False otherwise
        """
        import numpy as np

        # Create cost map (1 for walkable, 0 for walls)
        cost_map = np.ones((GameConfig.MAP_HEIGHT, GameConfig.MAP_WIDTH), dtype=np.uint8, order="F")
        for y in range(GameConfig.MAP_HEIGHT):
            for x in range(GameConfig.MAP_WIDTH):
                pos = Position(x, y)
                if self.game_map.is_wall(pos):
                    cost_map[y, x] = 0  # Walls are impassable

        # Use PathfindingHelper for centralized pathfinding (fixes TCOD coordinate ordering)
        path = PathfindingHelper.calculate_simple_path(spawn_pos, gateway_pos, cost_map)

        if path is None or len(path) == 0:
            logging.error(f"Level Gen: Pathfinding returned empty path from {spawn_pos} to {gateway_pos}")
            return False

        path_length = len(path)
        logging.debug(f"Level Gen: Gateway reachability validated - path length={path_length} tiles")
        return True

    def _fix_unreachable_gateway(self, level: int, seed: int, spawn_pos: Position, gateway_pos: Position) -> None:
        """
        Fix an unreachable gateway by carving a deterministic emergency corridor.

        IMPORTANT: This uses corridor carving (not regeneration) to preserve seed determinism.
        The same seed will always produce the same map, even if gateway validation fails.

        This ensures the level is ALWAYS playable, even if generation has a bug.

        Args:
            level: Current level number
            seed: Original seed (for logging only)
            spawn_pos: Player spawn position
            gateway_pos: Gateway position to make reachable
        """
        import numpy as np

        # Carve emergency corridor (deterministic approach)
        logging.warning(f"Level Gen: Gateway at {gateway_pos} unreachable! Carving emergency corridor...")
        final_gateway = self.game_map.gateway

        # Use PathfindingHelper to get path treating walls as walkable
        # Create cost map where everything is walkable (we'll carve through walls)
        cost_map_all_walkable = np.ones((GameConfig.MAP_HEIGHT, GameConfig.MAP_WIDTH), dtype=np.uint8, order="F")

        emergency_path = PathfindingHelper.calculate_simple_path(spawn_pos, final_gateway, cost_map_all_walkable)

        if emergency_path is not None and len(emergency_path) > 0:
            # Carve corridor along path
            # IMPORTANT: TCOD returns path as list of (y, x) tuples
            for y, x in emergency_path:
                pos = Position(x, y)
                if self.game_map.is_wall(pos):
                    self.game_map.walls.discard((x, y))
                    # Add to corridor tiles for consistency
                    self.corridor_tiles.add((x, y))

            logging.warning(f"Level Gen: Emergency corridor carved ({len(emergency_path)} tiles) from {spawn_pos} to {final_gateway}")

            # Final validation
            if self._validate_gateway_reachability(spawn_pos, final_gateway):
                logging.info(f"Level Gen: Emergency corridor successful - gateway now reachable!")
            else:
                logging.critical(f"Level Gen: CRITICAL FAILURE - Emergency corridor failed to connect spawn to gateway!")
        else:
            logging.critical(f"Level Gen: CRITICAL FAILURE - Could not find path even ignoring walls!")
