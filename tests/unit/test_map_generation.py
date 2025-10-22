#!/usr/bin/env python3
"""
Map Generation Tests - Focus on Real Behavior
Tests for map generation using real objects and integration testing.
Removed over-mocked unit tests that test implementation details.
"""

import pytest
from unittest.mock import Mock, patch
from game_level import LevelGenerator
from game_map import GameMap
from game_entities import Position
from game_config import GameConfig, RoomGenerationConfig


class TestMapGeneration:
    """Test suite for map generation and level functionality."""

    def setup_method(self):
        """Setup common test objects."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.level_generator = LevelGenerator(self.game_map)

        # Store original config values for restoration
        self.original_config = {
            'MIN_ROOMS_BASE': RoomGenerationConfig.MIN_ROOMS_BASE,
            'MAX_ROOMS': RoomGenerationConfig.MAX_ROOMS,
            'MIN_ROOM_SIZE': RoomGenerationConfig.MIN_ROOM_SIZE,
            'MAX_ROOM_SIZE': RoomGenerationConfig.MAX_ROOM_SIZE,
            'ROOM_PADDING': RoomGenerationConfig.ROOM_PADDING
        }

    def teardown_method(self):
        """Restore original configuration values."""
        for key, value in self.original_config.items():
            setattr(RoomGenerationConfig, key, value)


class TestGameMapBasics(TestMapGeneration):
    """Test basic GameMap functionality with real objects."""

    def test_game_map_creation(self):
        """GameMap creates with correct dimensions and empty state."""
        game_map = GameMap(80, 40)

        assert game_map.width == 80
        assert game_map.height == 40
        assert len(game_map.walls) == 0
        assert len(game_map.shadows) == 0
        assert len(game_map.cooling_nodes) == 0
        assert len(game_map.cpu_recovery_nodes) == 0
        assert len(game_map.ghost_nodes) == 0
        assert len(game_map.code_hacks) == 0
        assert len(game_map.exploit_pickups) == 0
        assert game_map.gateway is None

    def test_wall_detection(self):
        """Wall detection works correctly including boundaries."""
        game_map = GameMap(10, 10)

        # No walls initially
        assert not game_map.is_wall(Position(5, 5))

        # Add a wall
        game_map.walls.add((5, 5))
        assert game_map.is_wall(Position(5, 5))

        # Out of bounds positions are considered walls
        assert game_map.is_wall(Position(-1, 5))
        assert game_map.is_wall(Position(5, -1))
        assert game_map.is_wall(Position(10, 5))
        assert game_map.is_wall(Position(5, 10))

    def test_shadow_detection(self):
        """Shadow detection works correctly including ghost nodes."""
        game_map = GameMap(10, 10)

        # No shadows initially
        assert not game_map.is_shadow(Position(5, 5))

        # Add a shadow
        game_map.shadows.add((5, 5))
        assert game_map.is_shadow(Position(5, 5))

        # Ghost nodes also count as shadows
        game_map.ghost_nodes.add((3, 3))
        assert game_map.is_shadow(Position(3, 3))

        # Out of bounds positions are not shadows
        assert not game_map.is_shadow(Position(-1, 5))
        assert not game_map.is_shadow(Position(10, 5))

    def test_special_node_detection(self):
        """Special node detection works correctly."""
        game_map = GameMap(10, 10)

        # Add different types of nodes
        game_map.cooling_nodes.add((2, 2))
        game_map.cpu_recovery_nodes.add((3, 3))
        game_map.ghost_nodes.add((4, 4))

        assert game_map.is_cooling_node(Position(2, 2))
        assert not game_map.is_cooling_node(Position(3, 3))

        assert game_map.is_cpu_recovery_node(Position(3, 3))
        assert not game_map.is_cpu_recovery_node(Position(2, 2))

        assert game_map.is_ghost_node(Position(4, 4))
        assert not game_map.is_ghost_node(Position(2, 2))

    def test_valid_position_detection(self):
        """Valid position detection considers walls and boundaries."""
        game_map = GameMap(10, 10)

        # Valid empty position
        assert game_map.is_valid_position(Position(5, 5))

        # Invalid due to wall
        game_map.walls.add((5, 5))
        assert not game_map.is_valid_position(Position(5, 5))

        # Invalid due to boundaries
        assert not game_map.is_valid_position(Position(-1, 5))
        assert not game_map.is_valid_position(Position(10, 5))
        assert not game_map.is_valid_position(Position(5, -1))
        assert not game_map.is_valid_position(Position(5, 10))


class TestRoomGeneration(TestMapGeneration):
    """Test room generation with real LevelGenerator."""

    def test_room_carving(self):
        """Room carving removes walls correctly."""
        # Fill map with walls first
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                self.game_map.walls.add((x, y))

        # Carve a room
        test_room = (5, 5, 10, 8)  # x, y, width, height
        self.level_generator.room_generator.carve_room(test_room)

        # Check that walls were removed in the room area
        for x in range(5, 15):
            for y in range(5, 13):
                assert (x, y) not in self.game_map.walls

        # Check that walls outside the room remain
        assert (4, 5) in self.game_map.walls
        assert (15, 5) in self.game_map.walls
        assert (5, 4) in self.game_map.walls
        assert (5, 13) in self.game_map.walls

    def test_room_overlap_detection(self):
        """Room overlap detection works correctly."""
        existing_rooms = [(5, 5, 10, 8), (20, 20, 6, 6)]

        # Test non-overlapping room
        non_overlapping = (30, 30, 5, 5)
        assert not self.level_generator.room_generator.room_overlaps(non_overlapping, existing_rooms)

        # Test overlapping room (direct overlap)
        overlapping_direct = (7, 7, 5, 5)
        assert self.level_generator.room_generator.room_overlaps(overlapping_direct, existing_rooms)

        # Test overlapping room considering padding
        padding = RoomGenerationConfig.ROOM_PADDING
        overlapping_padding = (15 - padding, 5, 5, 5)
        assert self.level_generator.room_generator.room_overlaps(overlapping_padding, existing_rooms)

        # Test edge case - just outside padding
        just_outside = (15 + padding + 1, 5, 5, 5)
        assert not self.level_generator.room_generator.room_overlaps(just_outside, existing_rooms)

    def test_spawn_room_generation(self):
        """Spawn room is generated at fixed location."""
        rooms = self.level_generator.room_generator.create_varied_rooms(1)
        spawn_room = rooms[0]
        x, y, width, height = spawn_room

        # Spawn room should be at fixed location
        assert x == 2
        assert y == 2
        assert width == 8
        assert height == 8


class TestRoomOverlapPrevention(TestMapGeneration):
    """Test room overlap prevention with real logic."""

    def test_overlap_with_multiple_rooms(self):
        """Overlap detection works with multiple existing rooms."""
        existing_rooms = [
            (5, 5, 8, 6),
            (20, 20, 6, 8),
            (35, 35, 5, 5)
        ]

        # Test room that overlaps with first room
        overlapping_1 = (7, 7, 5, 5)
        assert self.level_generator.room_generator.room_overlaps(overlapping_1, existing_rooms)

        # Test room that overlaps with second room
        overlapping_2 = (22, 22, 4, 4)
        assert self.level_generator.room_generator.room_overlaps(overlapping_2, existing_rooms)

        # Test room that doesn't overlap with any
        non_overlapping = (50, 50, 5, 5)
        assert not self.level_generator.room_generator.room_overlaps(non_overlapping, existing_rooms)

    def test_padding_consideration(self):
        """Room overlap considers padding correctly."""
        existing_rooms = [(10, 10, 10, 10)]
        padding = RoomGenerationConfig.ROOM_PADDING

        # Room exactly at padding distance should not overlap
        room_at_padding = (20 + padding, 10, 5, 5)
        assert not self.level_generator.room_generator.room_overlaps(room_at_padding, existing_rooms)

        # Room inside padding distance should overlap
        room_inside_padding = (20 + padding - 1, 10, 5, 5)
        assert self.level_generator.room_generator.room_overlaps(room_inside_padding, existing_rooms)


class TestMapConnectivity(TestMapGeneration):
    """Test map connectivity with real objects."""

    def test_room_connection_creates_corridors(self):
        """Room connection creates corridors between rooms."""
        # Create test rooms
        room1 = (5, 5, 6, 6)
        room2 = (15, 15, 6, 6)

        # Carve the rooms first
        self.level_generator.room_generator.carve_room(room1)
        self.level_generator.room_generator.carve_room(room2)

        # Create corridor between rooms
        self.level_generator.corridor_generator.create_corridor_between_rooms(room1, room2)

        # Verify corridor was created (some non-wall positions between rooms)
        room1_center = (8, 8)
        room2_center = (18, 18)

        # There should be some non-wall positions between the rooms
        path_positions = []
        for x in range(8, 19):
            if (x, 8) not in self.game_map.walls:
                path_positions.append((x, 8))
        for y in range(8, 19):
            if (18, y) not in self.game_map.walls:
                path_positions.append((18, y))

        # Should have created some corridor positions
        assert len(path_positions) > 0


class TestLevelDataManagement(TestMapGeneration):
    """Test level data clearing and management."""

    def test_level_data_clearing(self):
        """Level data clearing removes all existing data."""
        # Add some test data
        self.game_map.walls.add((5, 5))
        self.game_map.shadows.add((6, 6))
        self.game_map.cooling_nodes.add((7, 7))
        self.game_map.cpu_recovery_nodes.add((8, 8))
        self.game_map.ghost_nodes.add((9, 9))
        self.game_map.code_hacks[(10, 10)] = Mock()
        self.game_map.exploit_pickups[(11, 11)] = Mock()
        self.game_map.permanent_upgrades[(12, 12)] = "test_upgrade"
        self.game_map.story_fragments[(13, 13)] = Mock()
        self.game_map.explored_tiles.add((14, 14))
        self.game_map.last_known_enemy_positions[1] = (Position(15, 15), 10)

        # Clear level data
        self.level_generator._clear_level_data()

        # Verify everything is cleared
        assert len(self.game_map.walls) == 0
        assert len(self.game_map.shadows) == 0
        assert len(self.game_map.cooling_nodes) == 0
        assert len(self.game_map.cpu_recovery_nodes) == 0
        assert len(self.game_map.ghost_nodes) == 0
        assert len(self.game_map.code_hacks) == 0
        assert len(self.game_map.exploit_pickups) == 0
        assert len(self.game_map.permanent_upgrades) == 0
        assert len(self.game_map.story_fragments) == 0
        assert len(self.game_map.explored_tiles) == 0
        assert len(self.game_map.last_known_enemy_positions) == 0


class TestMapBoundaryConditions(TestMapGeneration):
    """Test map boundary conditions and edge cases."""

    def test_edge_case_room_placement(self):
        """Room placement near boundaries works correctly."""
        # Test room placement near boundaries
        edge_room = (GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10, 5, 5)

        # This should not crash
        self.level_generator.room_generator.carve_room(edge_room)

        # Room should be carved properly within bounds
        for x in range(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_WIDTH - 5):
            for y in range(GameConfig.MAP_HEIGHT - 10, GameConfig.MAP_HEIGHT - 5):
                if x < GameConfig.MAP_WIDTH and y < GameConfig.MAP_HEIGHT:
                    assert (x, y) not in self.game_map.walls

    def test_minimum_room_requirements(self):
        """Level generation handles minimum room requirements."""
        # Test with very restrictive room generation
        original_max_rooms = RoomGenerationConfig.MAX_ROOMS
        RoomGenerationConfig.MAX_ROOMS = 1

        try:
            # Should still generate at least the spawn room
            rooms = self.level_generator.room_generator.create_varied_rooms(level=1)
            assert len(rooms) >= 1

            # First room should be spawn room
            spawn_room = rooms[0]
            assert spawn_room == (2, 2, 8, 8)
        finally:
            RoomGenerationConfig.MAX_ROOMS = original_max_rooms


class TestMapIntegration(TestMapGeneration):
    """Integration tests for complete map generation."""

    def test_full_level_generation_produces_valid_map(self):
        """Full level generation produces a playable map."""
        # Generate a complete level
        self.level_generator.generate_level(level=1, seed=42)

        # Basic validation - map should have walls and open areas
        assert len(self.game_map.walls) > 0

        # Should have some open areas (not everything is walls)
        open_positions = 0
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    open_positions += 1
        assert open_positions > 0

        # Border should be mostly walls for containment
        border_walls = 0
        for x in range(GameConfig.MAP_WIDTH):
            if (x, 0) in self.game_map.walls:
                border_walls += 1
            if (x, GameConfig.MAP_HEIGHT - 1) in self.game_map.walls:
                border_walls += 1
        for y in range(GameConfig.MAP_HEIGHT):
            if (0, y) in self.game_map.walls:
                border_walls += 1
            if (GameConfig.MAP_WIDTH - 1, y) in self.game_map.walls:
                border_walls += 1

        # Most border positions should be walls
        expected_border_positions = 2 * (GameConfig.MAP_WIDTH + GameConfig.MAP_HEIGHT - 2)
        assert border_walls > expected_border_positions * 0.7

    def test_deterministic_generation(self):
        """Same seed produces same map."""
        # Generate first map
        self.level_generator.generate_level(level=1, seed=12345)
        walls_1 = self.game_map.walls.copy()
        shadows_1 = self.game_map.shadows.copy()

        # Clear and generate second map with same seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(level=1, seed=12345)
        walls_2 = self.game_map.walls.copy()
        shadows_2 = self.game_map.shadows.copy()

        # Should be identical
        assert walls_1 == walls_2
        assert shadows_1 == shadows_2

    def test_different_seeds_produce_different_maps(self):
        """Different seeds produce different maps."""
        # Generate first map
        self.level_generator.generate_level(level=1, seed=12345)
        walls_1 = self.game_map.walls.copy()

        # Clear and generate second map with different seed
        self.level_generator._clear_level_data()
        self.level_generator.generate_level(level=1, seed=54321)
        walls_2 = self.game_map.walls.copy()

        # Should be different (very high probability)
        assert walls_1 != walls_2


if __name__ == "__main__":
    pytest.main([__file__])
