"""
Special tile and gateway placement for procedural levels.

This module handles strategic placement of special nodes and level objectives:

TILE PLACEMENT:
- Special tiles (cooling nodes, CPU recovery nodes, ghost nodes)
- Gateway placement using various strategies
- Border wall enforcement
- Objective-oriented placement based on level geography

Gateway strategies:
- Far Corner: Opposite corner from spawn, maximum distance
- Central Hub: Near map center, creates central objective
- Hidden Dead End: At end of longest branch, rewards exploration
- Gauntlet: Along edge, requires crossing the entire map

Node placement strategies:
- Cooling nodes: High-traffic areas (central corridors, hub rooms)
- CPU recovery nodes: Peripheral/safer areas (edge rooms, dead ends)
- Ghost nodes: Shadow-adjacent positions (stealth paths)
"""

import logging
import random

from rsp.systems.ascension import AscensionModifiers
from rsp.core.config import GameConfig
from rsp.entities.base import Position
from rsp.level.map import RestoreNode


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

        # Invalidate transparency cache after walls are modified
        self.game_map.invalidate_transparency_cache()

    def place_special_tiles(
        self,
        level: int,
        landmark_rooms: list[dict] = None,
        ascension_modifiers: AscensionModifiers | None = None,
    ) -> None:
        """
        Place cooling nodes, CPU recovery nodes, and other special tiles.

        Uses objective-oriented placement strategies:
        - Cooling nodes: High-traffic areas (central corridors, hub rooms)
        - CPU recovery nodes: Peripheral/safer areas (edge rooms, dead ends)
        - Ghost nodes: Shadow-adjacent positions (stealth paths)

        Args:
            level: Current level number (affects node counts)
            landmark_rooms: List of landmark room definitions for objective placement
            ascension_modifiers: Optional AscensionModifiers for A13+ node capacity
        """
        logging.debug(f"Tile Placement: Placing special tiles for level {level}")
        if ascension_modifiers is None:
            ascension_modifiers = AscensionModifiers()
        if landmark_rooms is None:
            landmark_rooms = []

        floor_positions = self.get_all_floor_positions()

        if not floor_positions:
            logging.warning(
                f"No floor positions available for level {level} special node placement"
            )
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

        def get_node_capacity() -> int:
            """Get random node capacity for A13+ or -1 (unlimited) otherwise."""
            if ascension_modifiers.node_capacity_ranges is None:
                return -1  # Unlimited
            floor_key = f"floor_{level}"
            if floor_key not in ascension_modifiers.node_capacity_ranges:
                return -1  # Unlimited for unlisted floors
            min_cap, max_cap = ascension_modifiers.node_capacity_ranges[floor_key]
            return random.randint(min_cap, max_cap)

        cooling_count = get_required_config("cooling_nodes")
        # A19+: Apply node reduction per floor (min 0 nodes)
        if ascension_modifiers.node_reduction_per_floor > 0:
            cooling_count = max(0, cooling_count - ascension_modifiers.node_reduction_per_floor)
        cooling_positions = self.get_high_traffic_positions(floor_positions)
        logging.debug(
            f"Tile Placement: Placing {cooling_count} cooling nodes (high-traffic candidates={len(cooling_positions)})"
        )
        for i in range(cooling_count):
            capacity = get_node_capacity()
            if cooling_positions:
                pos = random.choice(cooling_positions)
                cooling_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes[pos] = RestoreNode(
                    node_type="cooling", total_capacity=capacity
                )
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes[pos] = RestoreNode(
                    node_type="cooling", total_capacity=capacity
                )
        actual_cooling = len(self.game_map.cooling_nodes)
        match_status = "MATCH" if actual_cooling == cooling_count else "MISMATCH"
        logging.info(
            f"Tile Placement: COOLING NODES - Expected: {cooling_count}, Actual: {actual_cooling} [{match_status}]"
        )

        cpu_count = get_required_config("cpu_nodes")
        # A19+: Apply node reduction per floor (min 0 nodes)
        if ascension_modifiers.node_reduction_per_floor > 0:
            cpu_count = max(0, cpu_count - ascension_modifiers.node_reduction_per_floor)
        cpu_positions = self.get_peripheral_positions(floor_positions)
        logging.debug(
            f"Tile Placement: Placing {cpu_count} CPU nodes (peripheral candidates={len(cpu_positions)})"
        )
        for i in range(cpu_count):
            capacity = get_node_capacity()
            if cpu_positions:
                pos = random.choice(cpu_positions)
                cpu_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes[pos] = RestoreNode(
                    node_type="cpu", total_capacity=capacity
                )
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes[pos] = RestoreNode(
                    node_type="cpu", total_capacity=capacity
                )
        actual_cpu = len(self.game_map.cpu_recovery_nodes)
        match_status = "MATCH" if actual_cpu == cpu_count else "MISMATCH"
        logging.info(
            f"Tile Placement: CPU NODES - Expected: {cpu_count}, Actual: {actual_cpu} [{match_status}]"
        )

        ghost_count = get_required_config("ghost_nodes")
        # A19+: Apply node reduction per floor (min 0 nodes)
        if ascension_modifiers.node_reduction_per_floor > 0:
            ghost_count = max(0, ghost_count - ascension_modifiers.node_reduction_per_floor)
        ghost_positions = self.get_shadow_adjacent_positions(floor_positions)
        logging.debug(
            f"Tile Placement: Placing {ghost_count} ghost nodes (shadow-adjacent candidates={len(ghost_positions)})"
        )
        for i in range(ghost_count):
            capacity = get_node_capacity()
            if ghost_positions:
                pos = random.choice(ghost_positions)
                ghost_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.ghost_nodes[pos] = RestoreNode(
                    node_type="ghost", total_capacity=capacity
                )
            elif floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.ghost_nodes[pos] = RestoreNode(
                    node_type="ghost", total_capacity=capacity
                )
        actual_ghost = len(self.game_map.ghost_nodes)
        match_status = "MATCH" if actual_ghost == ghost_count else "MISMATCH"
        logging.info(
            f"Tile Placement: GHOST NODES - Expected: {ghost_count}, Actual: {actual_ghost} [{match_status}]"
        )

    def get_high_traffic_positions(
        self, floor_positions: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
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
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in self.game_map.walls:
                    floor_neighbors += 1

            if 3 <= floor_neighbors <= 6:
                high_traffic.append(pos)

        return high_traffic

    def get_peripheral_positions(
        self, floor_positions: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
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

            near_edge = (
                x < 15 or x > GameConfig.MAP_WIDTH - 15 or y < 15 or y > GameConfig.MAP_HEIGHT - 15
            )

            if near_edge:
                floor_neighbors = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (x + dx, y + dy)
                    if neighbor not in self.game_map.walls:
                        floor_neighbors += 1

                if floor_neighbors >= 3:
                    peripheral.append(pos)

        return peripheral

    def get_shadow_adjacent_positions(
        self, floor_positions: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
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

            if pos in self.game_map.blind_spots:
                shadow_adjacent.append(pos)
                continue

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in self.game_map.blind_spots:
                    shadow_adjacent.append(pos)
                    break

        return shadow_adjacent

    def get_all_floor_positions(self) -> list[tuple[int, int]]:
        """
        Get all valid floor positions (not walls, not blind spots).

        Excludes blind spots to prevent special nodes (cooling/CPU) from getting
        stealth bonuses. Ghost nodes are placed separately and intentionally
        can overlap with blind spots.

        Returns:
            List of all floor tile positions excluding blind spots
        """
        floor_positions = []
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls and (x, y) not in self.game_map.blind_spots:
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
        logging.debug(f"Gateway: Selected strategy '{strategy}' for level {level}")

        spawn_area = Position(5, 5)
        floor_positions = self.get_all_floor_positions()

        # Exclude positions with special nodes (cooling, CPU, ghost)
        occupied_positions = (
            self.game_map.cooling_nodes
            | self.game_map.cpu_recovery_nodes
            | self.game_map.ghost_nodes
        )
        floor_positions = [pos for pos in floor_positions if pos not in occupied_positions]

        if not floor_positions:
            logging.warning(f"Gateway: No floor positions available for level {level}")
            return

        if strategy == "far_corner":
            gateway_pos = self.gateway_far_corner(spawn_area, floor_positions)
        elif strategy == "central_hub":
            gateway_pos = self.gateway_central_hub(floor_positions)
        elif strategy == "hidden_dead_end":
            gateway_pos = self.gateway_hidden_dead_end(floor_positions)
        elif strategy == "gauntlet":
            gateway_pos = self.gateway_gauntlet(spawn_area, floor_positions)
        else:
            gateway_pos = self.gateway_far_corner(spawn_area, floor_positions)

        self.game_map.gateway = Position(gateway_pos[0], gateway_pos[1])
        distance_from_spawn = spawn_area.distance_to(self.game_map.gateway)
        logging.debug(
            f"Gateway: Placed at {gateway_pos}, distance_from_spawn={distance_from_spawn:.1f}"
        )

    def select_gateway_strategy(self) -> str:
        """
        Select a gateway placement strategy based on configured weights.

        Returns:
            Strategy name string
        """
        weights = GameConfig._get_required("room_generation.gateway_strategy_weights")

        strategies = ["far_corner", "central_hub", "hidden_dead_end", "gauntlet"]
        strategy_weights = [
            weights["far_corner"],
            weights["central_hub"],
            weights["hidden_dead_end"],
            weights["gauntlet"],
        ]

        total = sum(strategy_weights)
        if total == 0:
            return strategies[0]  # Default to far_corner if all weights are 0
        normalized = [w / total for w in strategy_weights]

        rand = random.random()
        cumulative = 0
        for strategy, weight in zip(strategies, normalized):
            cumulative += weight
            if rand < cumulative:
                return strategy

        return strategies[0]

    def gateway_far_corner(
        self, spawn: Position, floor_positions: list[tuple[int, int]]
    ) -> tuple[int, int]:
        """
        Gateway in opposite corner from spawn - minimum 45 tiles.

        Creates maximum distance objective.

        Args:
            spawn: Spawn position
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required("room_generation.gateway_minimum_distances")[
            "far_corner"
        ]

        far_positions = [
            pos
            for pos in floor_positions
            if spawn.distance_to(Position(pos[0], pos[1])) > min_distance
        ]

        if far_positions:
            return random.choice(far_positions)

        furthest = max(floor_positions, key=lambda pos: spawn.distance_to(Position(pos[0], pos[1])))
        logging.warning(
            f"Far corner gateway: No positions >{min_distance} tiles from spawn, using furthest available"
        )
        return furthest

    def gateway_central_hub(self, floor_positions: list[tuple[int, int]]) -> tuple[int, int]:
        """
        Gateway in or near central area of map - minimum 35 tiles from spawn.

        Creates central objective, encourages exploration of center.

        Args:
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required("room_generation.gateway_minimum_distances")[
            "central_hub"
        ]
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

        valid_by_distance = [
            pos
            for pos in floor_positions
            if spawn.distance_to(Position(pos[0], pos[1])) > min_distance
        ]
        if valid_by_distance:
            return min(
                valid_by_distance,
                key=lambda pos: abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y),
            )

        logging.warning(f"Central hub gateway: No positions >{min_distance} tiles from spawn!")
        return min(
            floor_positions, key=lambda pos: abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y)
        )

    def gateway_hidden_dead_end(self, floor_positions: list[tuple[int, int]]) -> tuple[int, int]:
        """
        Gateway at end of longest branch - minimum 38 tiles from spawn.

        Rewards exploration, creates hidden objective.

        Args:
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required("room_generation.gateway_minimum_distances")[
            "hidden_dead_end"
        ]
        spawn = Position(5, 5)

        dead_end_positions = []

        for pos in floor_positions:
            x, y = pos

            neighbor_count = sum(
                1
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if (x + dx, y + dy) in floor_positions
            )

            if neighbor_count <= 2:
                distance_from_spawn = spawn.distance_to(Position(x, y))
                if distance_from_spawn > min_distance:
                    dead_end_positions.append(pos)

        if dead_end_positions:
            return random.choice(dead_end_positions)

        any_dead_end = [
            pos
            for pos in floor_positions
            if sum(
                1
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if (pos[0] + dx, pos[1] + dy) in floor_positions
            )
            <= 2
        ]

        if any_dead_end:
            logging.warning(
                f"Hidden dead end gateway: No dead ends >{min_distance} tiles from spawn"
            )
            return random.choice(any_dead_end)

        return random.choice(floor_positions)

    def gateway_gauntlet(
        self, spawn: Position, floor_positions: list[tuple[int, int]]
    ) -> tuple[int, int]:
        """
        Gateway along edge - minimum 40 tiles from spawn, requires crossing map.

        Forces traversal across the level.

        Args:
            spawn: Spawn position
            floor_positions: List of available floor positions

        Returns:
            Selected gateway position (x, y)
        """
        min_distance = GameConfig._get_required("room_generation.gateway_minimum_distances")[
            "gauntlet"
        ]

        edge_positions = []
        for pos in floor_positions:
            x, y = pos

            near_edge = (
                x < 10 or x > GameConfig.MAP_WIDTH - 10 or y < 10 or y > GameConfig.MAP_HEIGHT - 10
            )

            distance_from_spawn = spawn.distance_to(Position(x, y))

            if near_edge and distance_from_spawn > min_distance:
                edge_positions.append(pos)

        if edge_positions:
            return random.choice(edge_positions)

        logging.warning(
            f"Gauntlet gateway: No edge positions >{min_distance} tiles from spawn, using far corner"
        )
        return self.gateway_far_corner(spawn, floor_positions)
