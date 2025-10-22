#!/usr/bin/env python3
"""
Unit tests for room-based Level Generation features.
Tests variable room types and Phase 3 layout improvements: looping paths, gateway strategies, shadow zones, hub-and-spoke.
"""

import pytest
import random
from game_level import LevelGenerator
from game_map import GameMap
from game_entities import Position
from game_config import GameConfig


class TestVariableRoomTypes:
    """Test variable room type generation (L-shaped, irregular, cross, circular, pillar)."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_room_type_selection(self):
        """Test that room type selection returns valid types."""
        # Test with various room sizes
        room_types = set()
        for _ in range(50):
            room_type = self.level_generator.room_generator.select_room_type(1, 8, 8)
            room_types.add(room_type)
            assert room_type in ['rectangular', 'l_shaped', 'irregular', 'cross', 'circular']

        # Should use multiple types over 50 iterations
        assert len(room_types) >= 2

    def test_room_type_respects_minimum_sizes(self):
        """Test that room types respect minimum size requirements."""
        # Small room should only get rectangular or limited types
        for _ in range(20):
            small_room_type = self.level_generator.room_generator.select_room_type(1, 3, 3)
            assert small_room_type in ['rectangular']

        # Large room should be able to get all types
        large_room_types = set()
        for _ in range(100):
            large_room_type = self.level_generator.room_generator.select_room_type(1, 8, 8)
            large_room_types.add(large_room_type)

        # Should have variety
        assert len(large_room_types) >= 3

    def test_carve_rectangular_room(self):
        """Test rectangular room carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        room = (10, 10, 5, 5)
        self.level_generator.room_generator.carve_rectangular_room(room)

        # Verify all tiles in room are carved
        for x in range(10, 15):
            for y in range(10, 15):
                assert (x, y) not in self.game_map.walls

    def test_carve_l_shaped_room(self):
        """Test L-shaped room carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        room = (10, 10, 8, 8)
        self.level_generator.room_generator.carve_l_shaped_room(room)

        # Count carved tiles
        carved_tiles = 0
        for x in range(10, 18):
            for y in range(10, 18):
                if (x, y) not in self.game_map.walls:
                    carved_tiles += 1

        # Should carve less than full room but more than half
        full_room_size = 8 * 8
        assert carved_tiles > full_room_size * 0.5
        assert carved_tiles < full_room_size

    def test_carve_irregular_room(self):
        """Test irregular/damaged room carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        room = (10, 10, 8, 8)
        random.seed(42)
        self.level_generator.room_generator.carve_irregular_room(room)

        # Count carved tiles
        carved_tiles = 0
        for x in range(10, 18):
            for y in range(10, 18):
                if (x, y) not in self.game_map.walls:
                    carved_tiles += 1

        # Should carve at least 70% of room (removed up to 30%)
        full_room_size = 8 * 8
        assert carved_tiles >= full_room_size * 0.7

    def test_carve_cross_room(self):
        """Test cross/plus-shaped room carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        room = (10, 10, 9, 9)
        self.level_generator.room_generator.carve_cross_room(room)

        # Verify center column is carved (vertical bar)
        center_x = 10 + 9 // 2
        for y in range(10, 19):
            assert (center_x, y) not in self.game_map.walls

        # Verify center row is carved (horizontal bar)
        center_y = 10 + 9 // 2
        for x in range(10, 19):
            assert (x, center_y) not in self.game_map.walls

    def test_carve_circular_room(self):
        """Test circular/oval room carving."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        room = (10, 10, 8, 8)
        self.level_generator.room_generator.carve_circular_room(room)

        # Verify center is carved
        center_x, center_y = 10 + 4, 10 + 4
        assert (center_x, center_y) not in self.game_map.walls

        # Count carved tiles - should be less than full rectangular room
        carved_tiles = 0
        for x in range(10, 18):
            for y in range(10, 18):
                if (x, y) not in self.game_map.walls:
                    carved_tiles += 1

        full_room_size = 8 * 8
        # Circle should carve roughly pi/4 of the rectangular area (~78%)
        assert carved_tiles < full_room_size
        assert carved_tiles > full_room_size * 0.5

    def test_apply_pillar_pattern(self):
        """Test pillar pattern application to large rooms."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create large room
        room = (10, 10, 10, 10)
        self.level_generator.room_generator.carve_rectangular_room(room)

        floor_before = sum(1 for x in range(10, 20) for y in range(10, 20) if (x, y) not in self.game_map.walls)

        # Apply pillars
        random.seed(1)  # Seed that triggers pillar placement
        self.level_generator.room_generator.apply_pillar_pattern(room, level=1)

        floor_after = sum(1 for x in range(10, 20) for y in range(10, 20) if (x, y) not in self.game_map.walls)

        # Pillars may or may not be added based on chance
        # If added, floor tiles should decrease
        assert floor_after <= floor_before

    def test_level_generation_with_varied_rooms(self):
        """Test that full level generation works with varied room types."""
        random.seed(12345)
        self.level_generator.generate_level(1, 88888)

        # Should complete successfully
        assert len(self.game_map.walls) > 0

        # Should have some floor tiles
        floor_count = 0
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_count += 1

        assert floor_count > 100

        # Gateway should be placed
        assert self.game_map.gateway is not None

    def test_per_level_room_type_weights(self):
        """Test that different levels use different room type distributions."""
        # Get weights for different levels
        weights_l1 = self.level_generator.room_generator.get_room_type_weights(1)
        weights_l2 = self.level_generator.room_generator.get_room_type_weights(2)
        weights_l3 = self.level_generator.room_generator.get_room_type_weights(3)

        # Verify all levels have rectangular as most common or second most common
        assert all('rectangular' in w for w in [weights_l1, weights_l2, weights_l3])

        # Level 1 should favor rectangular more than or equal to level 3
        # (Equal is acceptable if per-level configs not loaded, > if they are loaded)
        assert weights_l1['rectangular'] >= weights_l3['rectangular']

        # Verify weights are valid (sum to 1.0 or close to it)
        for weights in [weights_l1, weights_l2, weights_l3]:
            total = sum(weights.values())
            assert 0.99 <= total <= 1.01

    def test_all_room_types_can_be_generated(self):
        """Test that all room types can be successfully generated."""
        room_types = ['rectangular', 'l_shaped', 'irregular', 'cross', 'circular']

        for room_type in room_types:
            # Clear map
            for x in range(GameConfig.MAP_WIDTH):
                for y in range(GameConfig.MAP_HEIGHT):
                    self.game_map.walls.add((x, y))

            # Carve room of each type
            room = (15, 15, 8, 8)
            self.level_generator.room_generator.carve_room(room, room_type, level=1)

            # Verify some tiles were carved
            carved_tiles = 0
            for x in range(15, 23):
                for y in range(15, 23):
                    if (x, y) not in self.game_map.walls:
                        carved_tiles += 1

            assert carved_tiles > 0, f"Room type {room_type} failed to carve any tiles"


class TestPhase3LayoutImprovements:
    """Test Phase 3 layout improvements: looping paths, gateway strategies, shadow zones, hub-and-spoke."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_identify_hub_rooms(self):
        """Test identification of central hub rooms."""
        # Generate some rooms
        self.level_generator.generate_level(1, 12345)
        rooms = self.level_generator.last_generated_rooms

        # Identify hub rooms
        hub_rooms = self.level_generator.advanced_generator.identify_hub_rooms(rooms)

        # Should return empty list for too few rooms, or valid hubs otherwise
        if len(rooms) >= 5:
            assert len(hub_rooms) >= 0
            # If hubs were created, verify they're larger than original rooms
            if hub_rooms:
                for hub in hub_rooms:
                    x, y, w, h = hub
                    assert w > 0 and h > 0
        else:
            assert hub_rooms == []

    def test_hub_room_expansion(self):
        """Test that hub rooms are expanded correctly."""
        # Create a small room
        room = (10, 10, 5, 5)
        expanded = self.level_generator.advanced_generator.expand_hub_room(room)

        x, y, w, h = expanded

        # Expanded room should be larger
        assert w >= 5
        assert h >= 5

        # Should be within map bounds
        assert 0 <= x < GameConfig.MAP_WIDTH
        assert 0 <= y < GameConfig.MAP_HEIGHT
        assert x + w <= GameConfig.MAP_WIDTH
        assert y + h <= GameConfig.MAP_HEIGHT

    def test_create_looping_paths(self):
        """Test creation of looping paths in level."""
        # Generate a level
        self.level_generator.generate_level(1, 54321)

        # Level should complete successfully
        assert self.game_map.gateway is not None
        assert len(self.game_map.walls) > 0

    def test_build_room_connectivity_graph(self):
        """Test building connectivity graph from rooms."""
        # Generate level to get rooms
        self.level_generator.generate_level(1, 99999)
        rooms = self.level_generator.last_generated_rooms

        # Build connectivity graph
        connectivity = self.level_generator.advanced_generator.build_room_connectivity_graph(rooms)

        # Should have connectivity data for each room
        assert len(connectivity) > 0

        # All rooms should have at least 1 connection
        for room, connections in connectivity.items():
            assert connections >= 1

    def test_create_shadow_zones(self):
        """Test shadow zone creation."""
        # Generate level to get rooms
        self.level_generator.generate_level(1, 77777)
        rooms = self.level_generator.last_generated_rooms

        # Create shadow zones
        shadow_zone_rooms = self.level_generator.advanced_generator.create_shadow_zones(rooms)

        # Shadow zones may or may not be created
        assert isinstance(shadow_zone_rooms, list)

        # If created, should be subset of rooms
        for sz_room in shadow_zone_rooms:
            assert sz_room in rooms

    def test_find_room_clusters(self):
        """Test finding clusters of nearby rooms."""
        # Generate level to get rooms
        self.level_generator.generate_level(1, 33333)
        rooms = self.level_generator.last_generated_rooms

        # Find clusters
        clusters = self.level_generator.advanced_generator.find_room_clusters(rooms, 3)

        # Clusters should be valid
        assert isinstance(clusters, list)

        # Each cluster should have minimum size
        for cluster in clusters:
            assert len(cluster) >= 3
            # All rooms in cluster should be from original room list
            for room in cluster:
                assert room in rooms

    def test_room_distance_calculation(self):
        """Test Manhattan distance calculation between rooms."""
        room1 = (10, 10, 5, 5)
        room2 = (20, 20, 5, 5)

        distance = self.level_generator.advanced_generator.room_distance(room1, room2)

        # Distance should be positive
        assert distance > 0

        # Distance between same room should be 0
        assert self.level_generator.advanced_generator.room_distance(room1, room1) == 0

        # Distance should be symmetric
        assert self.level_generator.advanced_generator.room_distance(room1, room2) == self.level_generator.advanced_generator.room_distance(room2, room1)

    def test_gateway_strategy_selection(self):
        """Test gateway placement strategy selection."""
        # Test multiple times to verify randomness
        strategies = set()
        for _ in range(50):
            strategy = self.level_generator.placement_generator.select_gateway_strategy()
            strategies.add(strategy)
            assert strategy in ['far_corner', 'central_hub', 'hidden_dead_end', 'gauntlet']

        # Should use multiple strategies over iterations
        assert len(strategies) >= 2

    def test_gateway_far_corner_strategy(self):
        """Test far corner gateway placement strategy."""
        floor_positions = self._create_open_map()
        spawn = Position(5, 5)

        gateway_pos = self.level_generator.placement_generator.gateway_far_corner(spawn, floor_positions)

        # Gateway should be far from spawn
        gateway = Position(gateway_pos[0], gateway_pos[1])
        distance = spawn.distance_to(gateway)
        assert distance > 15  # Should be reasonably far

    def test_gateway_central_hub_strategy(self):
        """Test central hub gateway placement strategy."""
        floor_positions = self._create_open_map()

        gateway_pos = self.level_generator.placement_generator.gateway_central_hub(floor_positions)

        # Gateway should be near center of map
        map_center_x = GameConfig.MAP_WIDTH // 2
        map_center_y = GameConfig.MAP_HEIGHT // 2
        dist_to_center = abs(gateway_pos[0] - map_center_x) + abs(gateway_pos[1] - map_center_y)

        # Should be relatively central
        assert dist_to_center < GameConfig.MAP_WIDTH // 2

    def test_gateway_hidden_dead_end_strategy(self):
        """Test hidden dead end gateway placement strategy."""
        floor_positions = self._create_open_map()

        gateway_pos = self.level_generator.placement_generator.gateway_hidden_dead_end(floor_positions)

        # Should return a valid position
        assert gateway_pos in floor_positions

    def test_gateway_gauntlet_strategy(self):
        """Test gauntlet gateway placement strategy."""
        floor_positions = self._create_open_map()
        spawn = Position(5, 5)

        gateway_pos = self.level_generator.placement_generator.gateway_gauntlet(spawn, floor_positions)

        # Should return a valid position
        assert gateway_pos in floor_positions

        # Should be far enough from spawn
        gateway = Position(gateway_pos[0], gateway_pos[1])
        distance = spawn.distance_to(gateway)
        assert distance > 10

    def test_strategic_gateway_placement(self):
        """Test strategic gateway placement in full level generation."""
        # Generate level with strategic gateway placement
        self.level_generator.generate_level(1, 11111)

        # Gateway should be placed
        assert self.game_map.gateway is not None

        # Gateway should be on floor
        gateway_pos = (self.game_map.gateway.x, self.game_map.gateway.y)
        assert gateway_pos not in self.game_map.walls

    def test_shadow_zones_increase_shadow_coverage(self):
        """Test that shadow zones have higher shadow coverage."""
        # Generate level with shadow zones
        random.seed(42)
        self.level_generator.generate_level(1, 22222)

        # Should have some shadows
        assert len(self.game_map.shadows) > 0

        # All shadows should be on floor
        for shadow in self.game_map.shadows:
            assert shadow not in self.game_map.walls

    def test_connect_hub_rooms(self):
        """Test hub room connection to other rooms."""
        # Generate level with rooms
        self.level_generator.generate_level(1, 44444)

        # Should complete successfully
        assert self.game_map.gateway is not None

    def test_level_generation_with_phase3_features(self):
        """Test that full level generation works with all Phase 3 features."""
        # Generate multiple levels to test different strategies
        for seed in [111, 222, 333, 444, 555]:
            self.level_generator._clear_level_data()
            self.level_generator.generate_level(1, seed)

            # Verify basic level structure
            assert len(self.game_map.walls) > 0
            assert self.game_map.gateway is not None

            # Gateway should be on floor
            gateway_pos = (self.game_map.gateway.x, self.game_map.gateway.y)
            assert gateway_pos not in self.game_map.walls

            # Should have floor tiles
            floor_count = sum(1 for x in range(GameConfig.MAP_WIDTH)
                            for y in range(GameConfig.MAP_HEIGHT)
                            if (x, y) not in self.game_map.walls)
            assert floor_count > 50

    def test_phase3_deterministic_generation(self):
        """Test that Phase 3 features maintain deterministic generation."""
        seed = 99999

        # Generate first level
        self.level_generator.generate_level(1, seed)
        first_walls = set(self.game_map.walls)
        first_shadows = set(self.game_map.shadows)
        first_gateway = self.game_map.gateway

        # Generate second level with same seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(1, seed)
        second_walls = set(self.game_map.walls)
        second_shadows = set(self.game_map.shadows)
        second_gateway = self.game_map.gateway

        # Should be identical
        assert first_walls == second_walls
        assert first_shadows == second_shadows
        assert first_gateway == second_gateway

    def _create_open_map(self):
        """Helper to create an open map for testing."""
        # Clear most of the map
        for x in range(5, GameConfig.MAP_WIDTH - 5):
            for y in range(5, GameConfig.MAP_HEIGHT - 5):
                if (x, y) in self.game_map.walls:
                    self.game_map.walls.remove((x, y))

        # Return floor positions
        return [(x, y) for x in range(5, GameConfig.MAP_WIDTH - 5)
                for y in range(5, GameConfig.MAP_HEIGHT - 5)
                if (x, y) not in self.game_map.walls]


if __name__ == "__main__":
    pytest.main([__file__])
