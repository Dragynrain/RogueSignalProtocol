"""
Special tile and gateway placement subsystem for procedural level generation.

This module handles strategic placement of:
- Special tiles (cooling nodes, CPU recovery nodes, ghost nodes)
- Gateway placement using various strategies
- Border wall enforcement
- Objective-oriented placement based on level geography

Placement strategies:
- High-traffic positions: Central corridors, hub rooms (for cooling nodes)
- Peripheral positions: Edge rooms, dead ends (for CPU recovery nodes)
- Shadow-adjacent positions: Near shadows and stealth paths (for ghost nodes)

Gateway strategies:
- Far Corner: Opposite corner from spawn, maximum distance
- Central Hub: Near map center, creates central objective
- Hidden Dead End: At end of longest branch, rewards exploration
- Gauntlet: Along edge, requires crossing the entire map
"""

import random
import logging
from typing import List, Tuple, Dict

from game_config import GameConfig
from game_entities import Position


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
        # Top and bottom walls
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))

        # Left and right walls
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

        # Get level-specific counts from network config - FAIL if missing
        network_configs = GameConfig.get_network_configs()
        if level not in network_configs:
            error_msg = f"CRITICAL CONFIG ERROR: Level {level} not found in network_configs"
            logging.error(error_msg)
            logging.error(f"Available levels: {list(network_configs.keys())}")
            raise KeyError(f"Network config missing for level: {level}")

        config = network_configs[level]

        # Helper function to get required config value
        def get_required_config(key: str) -> int:
            if key not in config:
                error_msg = f"CRITICAL CONFIG ERROR: '{key}' missing for level {level} in game_data.json network_configs"
                logging.error(error_msg)
                logging.error(f"Available config keys for level {level}: {list(config.keys())}")
                raise KeyError(f"Required key '{key}' missing from level {level} config")
            return config[key]

        # Place cooling nodes in high-traffic areas (central corridors)
        cooling_count = get_required_config('cooling_nodes')
        cooling_positions = self.get_high_traffic_positions(floor_positions)
        for i in range(cooling_count):
            if cooling_positions:
                pos = random.choice(cooling_positions)
                cooling_positions.remove(pos)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)
            elif floor_positions:
                # Fallback to random if no high-traffic positions
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)

        # Place CPU recovery nodes in safer peripheral rooms
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

        # Place ghost nodes along stealth paths (shadow zones)
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

            # Check if in central area of map
            dist_to_center = abs(x - map_center_x) + abs(y - map_center_y)
            if dist_to_center < 15:
                high_traffic.append(pos)
                continue

            # Check if in a corridor (has limited floor neighbors)
            floor_neighbors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor not in self.game_map.walls:
                    floor_neighbors += 1

            # Corridors typically have 3-6 floor neighbors
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

            # Check if near map edges
            near_edge = (x < 15 or x > GameConfig.MAP_WIDTH - 15 or
                        y < 15 or y > GameConfig.MAP_HEIGHT - 15)

            if near_edge:
                # Also check it's in a room (not a corridor)
                floor_neighbors = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (x + dx, y + dy)
                    if neighbor not in self.game_map.walls:
                        floor_neighbors += 1

                # Rooms typically have 4 floor neighbors
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

            # Check if position itself is a shadow
            if pos in self.game_map.shadows:
                shadow_adjacent.append(pos)
                continue

            # Check if adjacent to shadows
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
        # Select strategy based on configured weights
        strategy = self.select_gateway_strategy()

        spawn_area = Position(5, 5)  # Center of spawn area
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
            # Fallback to far corner
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

        # Normalize weights
        total = sum(strategy_weights)
        normalized = [w / total for w in strategy_weights]

        # Select based on cumulative probability
        rand = random.random()
        cumulative = 0
        for strategy, weight in zip(strategies, normalized):
            cumulative += weight
            if rand < cumulative:
                return strategy

        return strategies[0]  # Fallback

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

        # Fallback to furthest available (but log warning)
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

        # Find positions near center AND far enough from spawn
        central_positions = []
        for pos in floor_positions:
            distance_to_center = abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y)
            distance_from_spawn = spawn.distance_to(Position(pos[0], pos[1]))

            if distance_to_center < 15 and distance_from_spawn > min_distance:
                central_positions.append(pos)

        if central_positions:
            return random.choice(central_positions)

        # Fallback: prioritize distance over centrality
        valid_by_distance = [pos for pos in floor_positions
                            if spawn.distance_to(Position(pos[0], pos[1])) > min_distance]
        if valid_by_distance:
            # From valid positions, choose closest to center
            return min(valid_by_distance, key=lambda pos: abs(pos[0] - map_center_x) + abs(pos[1] - map_center_y))

        # Absolute fallback (shouldn't happen on normal maps)
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

        # Find dead ends (≤2 neighbors) that are far enough from spawn
        dead_end_positions = []

        for pos in floor_positions:
            x, y = pos

            # Count floor neighbors
            neighbor_count = sum(1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                                if (x + dx, y + dy) in floor_positions)

            # Is it a dead end?
            if neighbor_count <= 2:
                distance_from_spawn = spawn.distance_to(Position(x, y))
                if distance_from_spawn > min_distance:
                    dead_end_positions.append(pos)

        if dead_end_positions:
            return random.choice(dead_end_positions)

        # Fallback: Any dead end (ignore distance requirement)
        any_dead_end = [pos for pos in floor_positions
                       if sum(1 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                             if (pos[0] + dx, pos[1] + dy) in floor_positions) <= 2]

        if any_dead_end:
            logging.warning(f"Hidden dead end gateway: No dead ends >{min_distance} tiles from spawn")
            return random.choice(any_dead_end)

        # Ultimate fallback
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

            # Check if near any edge
            near_edge = (x < 10 or x > GameConfig.MAP_WIDTH - 10 or
                        y < 10 or y > GameConfig.MAP_HEIGHT - 10)

            distance_from_spawn = spawn.distance_to(Position(x, y))

            if near_edge and distance_from_spawn > min_distance:
                edge_positions.append(pos)

        if edge_positions:
            return random.choice(edge_positions)

        # Fallback to far corner strategy
        logging.warning(f"Gauntlet gateway: No edge positions >{min_distance} tiles from spawn, using far corner")
        return self.gateway_far_corner(spawn, floor_positions)
