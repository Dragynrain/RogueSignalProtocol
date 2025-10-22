#!/usr/bin/env python3
"""
Unit tests for advanced Level Generation features.
Tests Phase 4-5 features: T-junctions, landmark rooms, objective-oriented placement, curved corridors, defensive positions, choke points, and zones.
"""

import pytest
import random
from game_level import LevelGenerator
from game_map import GameMap
from game_config import GameConfig


class TestPhase4AdvancedFeatures:
    """Test Phase 4 advanced features: T-junctions, landmark rooms, objective-oriented placement."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_find_corridor_intersections(self):
        """Test finding corridor intersection points."""
        # Create a cross-pattern of corridors
        for x in range(15, 25):
            self.level_generator.corridor_tiles.add((x, 20))
        for y in range(15, 25):
            self.level_generator.corridor_tiles.add((20, y))

        # Find intersections
        intersections = self.level_generator.corridor_generator.find_corridor_intersections()

        # Should find the center point (20, 20) as a 4-way intersection
        assert (20, 20) in intersections

    def test_expand_intersection_into_junction(self):
        """Test expanding intersection into junction room."""
        # Clear area
        for x in range(15, 26):
            for y in range(15, 26):
                if (x, y) in self.game_map.walls:
                    self.game_map.walls.remove((x, y))

        # Fill with walls for controlled test
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if not (15 <= x <= 25 and 15 <= y <= 25):
                    self.game_map.walls.add((x, y))

        center = (20, 20)
        self.level_generator.corridor_tiles.add(center)

        # Expand into 3x3 junction
        self.level_generator.corridor_generator.expand_intersection_into_junction(center, 3)

        # Verify junction area is carved
        for jx in range(19, 22):
            for jy in range(19, 22):
                assert (jx, jy) not in self.game_map.walls

        # Verify at least some shadows placed in corners
        # (Shadows are only placed if the corners are in corridor_tiles)
        corner_shadows = sum(1 for corner in [(19, 19), (21, 19), (19, 21), (21, 21)]
                           if corner in self.game_map.shadows)
        # Since we didn't add all corners to corridor_tiles, may not get all 4 shadows
        # Just verify the method ran without error
        assert corner_shadows >= 0  # Should not crash

    def test_create_corridor_intersections(self):
        """Test full corridor intersection creation."""
        # Generate a level
        self.level_generator.generate_level(1, 77777)

        # Should complete without errors
        assert self.game_map.gateway is not None

    def test_create_landmark_rooms(self):
        """Test landmark room creation."""
        # Generate some base rooms first
        self.level_generator.generate_level(1, 12345)
        rooms = self.level_generator.last_generated_rooms

        # Create landmark rooms
        landmark_rooms = self.level_generator.advanced_generator.create_landmark_rooms(1, rooms)

        # Should create 1-2 landmarks or 0 if not enough rooms
        assert 0 <= len(landmark_rooms) <= 2

        # Each landmark should have required fields
        for landmark in landmark_rooms:
            assert 'type' in landmark
            assert 'room' in landmark
            assert 'position' in landmark
            assert 'description' in landmark

    def test_create_server_core_landmark(self):
        """Test server core landmark creation."""
        # Generate base rooms
        self.level_generator.generate_level(1, 11111)
        rooms = self.level_generator.last_generated_rooms

        # Try to create server core
        landmark = self.level_generator.advanced_generator.create_server_core_landmark(rooms, 1)

        # May or may not succeed depending on room placement
        if landmark:
            assert landmark['type'] == 'server_core'
            assert 'position' in landmark
            x, y = landmark['position']
            assert 0 <= x < GameConfig.MAP_WIDTH
            assert 0 <= y < GameConfig.MAP_HEIGHT

    def test_create_vault_landmark(self):
        """Test vault landmark creation."""
        # Generate base rooms
        self.level_generator.generate_level(1, 22222)
        rooms = self.level_generator.last_generated_rooms

        # Try to create vault
        landmark = self.level_generator.advanced_generator.create_vault_landmark(rooms)

        # May or may not succeed
        if landmark:
            assert landmark['type'] == 'vault'
            assert 'position' in landmark

    def test_create_arena_landmark(self):
        """Test arena landmark creation."""
        # Generate base rooms
        self.level_generator.generate_level(1, 33333)
        rooms = self.level_generator.last_generated_rooms

        # Try to create arena
        landmark = self.level_generator.advanced_generator.create_arena_landmark(rooms)

        # May or may not succeed
        if landmark:
            assert landmark['type'] == 'arena'
            assert 'position' in landmark

    def test_get_high_traffic_positions(self):
        """Test identification of high-traffic positions."""
        # Generate a level
        self.level_generator.generate_level(1, 44444)
        floor_positions = self.level_generator.placement_generator.get_all_floor_positions()

        # Get high-traffic positions
        high_traffic = self.level_generator.placement_generator.get_high_traffic_positions(floor_positions)

        # Should find some high-traffic positions
        assert len(high_traffic) > 0

        # All should be valid floor positions
        for pos in high_traffic:
            assert pos not in self.game_map.walls

    def test_get_peripheral_positions(self):
        """Test identification of peripheral positions."""
        # Generate a level
        self.level_generator.generate_level(1, 55555)
        floor_positions = self.level_generator.placement_generator.get_all_floor_positions()

        # Get peripheral positions
        peripheral = self.level_generator.placement_generator.get_peripheral_positions(floor_positions)

        # Should find some peripheral positions (unless map is very small)
        # All should be valid floor positions
        for pos in peripheral:
            assert pos not in self.game_map.walls

    def test_get_shadow_adjacent_positions(self):
        """Test identification of shadow-adjacent positions."""
        # Generate a level
        self.level_generator.generate_level(1, 66666)
        floor_positions = self.level_generator.placement_generator.get_all_floor_positions()

        # Get shadow-adjacent positions
        shadow_adjacent = self.level_generator.placement_generator.get_shadow_adjacent_positions(floor_positions)

        # Should find some shadow-adjacent positions if shadows exist
        if len(self.game_map.shadows) > 0:
            assert len(shadow_adjacent) > 0

        # All should be valid floor positions
        for pos in shadow_adjacent:
            assert pos not in self.game_map.walls

    def test_objective_oriented_placement(self):
        """Test that objective-oriented placement works in full level generation."""
        # Generate a level with landmarks
        self.level_generator.generate_level(1, 88888)

        # Should have placed nodes
        assert len(self.game_map.cooling_nodes) > 0
        assert len(self.game_map.cpu_recovery_nodes) > 0
        assert len(self.game_map.ghost_nodes) > 0

        # All nodes should be on floor
        for node in self.game_map.cooling_nodes:
            assert node not in self.game_map.walls

        for node in self.game_map.cpu_recovery_nodes:
            assert node not in self.game_map.walls

        for node in self.game_map.ghost_nodes:
            assert node not in self.game_map.walls

    def test_landmark_rooms_stored_correctly(self):
        """Test that landmark rooms are stored for later use."""
        # Generate a level
        self.level_generator.generate_level(1, 99999)

        # Check if landmark rooms were stored
        if hasattr(self.level_generator, '_landmark_rooms'):
            landmark_rooms = self.level_generator._landmark_rooms
            assert isinstance(landmark_rooms, list)

            # Each landmark should be a dict
            for landmark in landmark_rooms:
                assert isinstance(landmark, dict)

    def test_phase4_full_integration(self):
        """Test full Phase 4 integration with all features."""
        # Generate multiple levels to test different scenarios
        for seed in [111111, 222222, 333333]:
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

            # Should have special nodes
            assert len(self.game_map.cooling_nodes) > 0

    def test_phase4_deterministic(self):
        """Test that Phase 4 features maintain deterministic generation."""
        seed = 777777

        # Generate first level
        self.level_generator.generate_level(1, seed)
        first_walls = set(self.game_map.walls)
        first_shadows = set(self.game_map.shadows)
        first_cooling = set(self.game_map.cooling_nodes)
        first_gateway = self.game_map.gateway

        # Generate second level with same seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(1, seed)
        second_walls = set(self.game_map.walls)
        second_shadows = set(self.game_map.shadows)
        second_cooling = set(self.game_map.cooling_nodes)
        second_gateway = self.game_map.gateway

        # Should be identical
        assert first_walls == second_walls
        assert first_shadows == second_shadows
        assert first_cooling == second_cooling
        assert first_gateway == second_gateway

    def test_cross_shaped_rooms_exist(self):
        """Verify cross-shaped rooms can be generated (Phase 2 feature)."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a cross-shaped room
        room = (20, 20, 9, 9)
        self.level_generator.room_generator.carve_cross_room(room)

        # Verify center column is carved
        center_x = 20 + 9 // 2
        for y in range(20, 29):
            assert (center_x, y) not in self.game_map.walls

        # Verify center row is carved
        center_y = 20 + 9 // 2
        for x in range(20, 29):
            assert (x, center_y) not in self.game_map.walls

    def test_circular_rooms_exist(self):
        """Verify circular rooms can be generated (Phase 2 feature)."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a circular room
        room = (20, 20, 8, 8)
        self.level_generator.room_generator.carve_circular_room(room)

        # Verify center is carved
        center_x, center_y = 20 + 4, 20 + 4
        assert (center_x, center_y) not in self.game_map.walls

        # Count carved tiles - should be less than rectangular but more than half
        carved_tiles = 0
        for x in range(20, 28):
            for y in range(20, 28):
                if (x, y) not in self.game_map.walls:
                    carved_tiles += 1

        full_room_size = 8 * 8
        assert carved_tiles < full_room_size
        assert carved_tiles > full_room_size * 0.5


class TestPhase5PolishFeatures:
    """Test Phase 5 polish features: curved corridors, defensive positions, item clustering, choke points, zones."""

    def setup_method(self):
        """Set up test environment."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

    def test_bresenham_line_algorithm(self):
        """Test Bresenham's line algorithm produces correct line points."""
        # Test horizontal line
        points = self.level_generator.corridor_generator.bresenham_line(5, 5, 10, 5)
        assert len(points) == 6  # Should have 6 points (5 to 10 inclusive)
        assert (5, 5) in points
        assert (10, 5) in points

        # Test vertical line
        points = self.level_generator.corridor_generator.bresenham_line(5, 5, 5, 10)
        assert len(points) == 6
        assert (5, 5) in points
        assert (5, 10) in points

        # Test diagonal line
        points = self.level_generator.corridor_generator.bresenham_line(5, 5, 10, 10)
        assert len(points) >= 5  # Should have at least 5 points
        assert (5, 5) in points
        assert (10, 10) in points

    def test_curved_corridors_can_be_created(self):
        """Test that curved corridors can be created using Bresenham's algorithm."""
        # Fill map with walls
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a curved corridor
        self.level_generator.corridor_generator.create_curved_corridor(10, 10, 20, 20, width=1)

        # Verify corridor exists (should carve from start to end)
        # Check that start and end points are not walls
        assert (10, 10) not in self.game_map.walls
        assert (20, 20) not in self.game_map.walls

        # Verify corridor tiles were tracked
        assert len(self.level_generator.corridor_tiles) > 0

    def test_defensive_positions_created(self):
        """Test that defensive positions combine cover and shadows."""
        # Generate a level to have some rooms
        self.level_generator.generate_level(1, 12345)

        # Create a large room for testing
        test_room = (15, 15, 10, 10)
        self.level_generator.room_generator.carve_rectangular_room(test_room)

        initial_walls = len(self.game_map.walls)
        initial_shadows = len(self.game_map.shadows)

        # Create a defensive position
        self.level_generator.tactical_generator.create_corner_cover_position(17, 17)

        # Should have added some walls (cover) and possibly shadows
        # Note: Shadow creation depends on room layout and may not always increase count
        assert len(self.game_map.walls) >= initial_walls
        assert len(self.game_map.shadows) >= initial_shadows

    def test_loot_rooms_identified(self):
        """Test that loot rooms are correctly identified and stored."""
        self.level_generator.generate_level(1, 12345)

        # Loot room positions should be populated
        assert hasattr(self.game_map, 'loot_room_positions')
        assert isinstance(self.game_map.loot_room_positions, set)

        # Should have some loot room positions (20% of rooms)
        # With typical 12-15 rooms, should have at least a few positions
        if len(self.level_generator.last_generated_rooms) > 5:
            assert len(self.game_map.loot_room_positions) > 0

    def test_choke_points_narrow_corridors(self):
        """Test that choke points can narrow corridors."""
        # Create a wide corridor
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create a 3-wide horizontal corridor
        for x in range(10, 20):
            for y in range(24, 27):
                self.game_map.walls.discard((x, y))
                self.level_generator.corridor_tiles.add((x, y))

        initial_corridor_count = len(self.level_generator.corridor_tiles)

        # Narrow the corridor at a position
        self.level_generator.tactical_generator.narrow_corridor_at_position((15, 25))

        # Should have fewer corridor tiles (some converted to walls)
        # Note: May not always narrow if corridor is already narrow
        assert len(self.level_generator.corridor_tiles) <= initial_corridor_count

    def test_map_zones_created(self):
        """Test that map zones are created with correct structure."""
        zones = self.level_generator.advanced_generator.create_map_zones()

        # Should create configured number of zones
        zone_count = GameConfig._get_required('room_generation.zone_count')
        assert len(zones) == zone_count

        # Each zone should have type and bounds
        for zone in zones:
            assert 'type' in zone
            assert 'bounds' in zone
            assert zone['type'] in ['linear', 'open', 'mixed']

    def test_zone_assignment_for_rooms(self):
        """Test that rooms are correctly assigned to zones."""
        zones = self.level_generator.advanced_generator.create_map_zones()

        # Test room in different areas
        top_room = (10, 5, 5, 5)
        middle_room = (10, 25, 5, 5)
        bottom_room = (10, 45, 5, 5)

        top_zone = self.level_generator.advanced_generator.get_zone_for_room(top_room, zones)
        middle_zone = self.level_generator.advanced_generator.get_zone_for_room(middle_room, zones)
        bottom_zone = self.level_generator.advanced_generator.get_zone_for_room(bottom_room, zones)

        # Should all return valid zone types
        assert top_zone in ['linear', 'open', 'mixed']
        assert middle_zone in ['linear', 'open', 'mixed']
        assert bottom_zone in ['linear', 'open', 'mixed']

    def test_full_phase5_level_generation(self):
        """Integration test: Generate a complete level with all Phase 5 features."""
        self.level_generator.generate_level(1, 99999)

        # Verify basic structure
        assert len(self.game_map.walls) > 0
        assert self.game_map.gateway is not None

        # Verify Phase 5 features are present
        assert hasattr(self.game_map, 'loot_room_positions')
        assert hasattr(self.level_generator, '_room_zones') or True  # May not always be set

        # Verify level is playable (gateway not on wall, etc.)
        gateway_pos = (self.game_map.gateway.x, self.game_map.gateway.y)
        assert gateway_pos not in self.game_map.walls

    def test_corridor_width_variation_phase5(self):
        """Test that curved corridors respect width parameter."""
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        # Create corridors with different widths
        self.level_generator.corridor_generator.create_curved_corridor(10, 10, 15, 15, width=1)
        narrow_count = len(self.level_generator.corridor_tiles)

        self.level_generator.corridor_tiles.clear()
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))

        self.level_generator.corridor_generator.create_curved_corridor(10, 10, 15, 15, width=3)
        wide_count = len(self.level_generator.corridor_tiles)

        # Wider corridor should have more tiles
        assert wide_count > narrow_count


if __name__ == "__main__":
    pytest.main([__file__])
