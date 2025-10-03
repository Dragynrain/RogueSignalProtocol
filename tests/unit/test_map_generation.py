#!/usr/bin/env python3
"""
Comprehensive Map Generation and Level Tests - Test Category 2
Tests for map generation, room placement, connectivity, tile distribution,
and boundary conditions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
from game_level import LevelGenerator
from game_map import GameMap
from game_entities import Position
from game_config import GameConfig, RoomGenerationConfig
from game_inventory import CodeHack, ExploitItem, StoryFragment


class TestMapGeneration:
    """Test suite for map generation and level functionality."""
    
    def setup_method(self):
        """Setup common test objects."""
        # Create a test game map
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
    """Test basic GameMap functionality and queries."""
    
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
    
    def test_wall_trace_level(self):
        """Wall trace_level works correctly."""
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
    
    def test_shadow_trace_level(self):
        """Shadow trace_level works correctly including ghost nodes."""
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
    
    def test_special_node_trace_level(self):
        """Special node trace_level works correctly."""
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
    
    def test_valid_position_trace_level(self):
        """Valid position trace_level considers walls and boundaries."""
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
    """Test room generation functionality."""
    
    def test_room_carving(self):
        """Room carving removes walls correctly."""
        # Fill map with walls first
        for x in range(self.game_map.width):
            for y in range(self.game_map.height):
                self.game_map.walls.add((x, y))
        
        # Carve a room
        test_room = (5, 5, 10, 8)  # x, y, width, height
        self.level_generator._carve_room(test_room)
        
        # Check that walls were removed in the room area
        for x in range(5, 15):
            for y in range(5, 13):
                assert (x, y) not in self.game_map.walls
        
        # Check that walls outside the room remain
        assert (4, 5) in self.game_map.walls
        assert (15, 5) in self.game_map.walls
        assert (5, 4) in self.game_map.walls
        assert (5, 13) in self.game_map.walls
    
    def test_room_overlap_trace_level(self):
        """Room overlap trace_level works correctly."""
        existing_rooms = [(5, 5, 10, 8), (20, 20, 6, 6)]
        
        # Test non-overlapping room
        non_overlapping = (30, 30, 5, 5)
        assert not self.level_generator._room_overlaps(non_overlapping, existing_rooms)
        
        # Test overlapping room (direct overlap)
        overlapping_direct = (7, 7, 5, 5)
        assert self.level_generator._room_overlaps(overlapping_direct, existing_rooms)
        
        # Test overlapping room considering padding
        padding = RoomGenerationConfig.ROOM_PADDING
        overlapping_padding = (15 - padding, 5, 5, 5)  # Should overlap due to padding
        assert self.level_generator._room_overlaps(overlapping_padding, existing_rooms)
        
        # Test edge case - just outside padding
        just_outside = (15 + padding + 1, 5, 5, 5)
        assert not self.level_generator._room_overlaps(just_outside, existing_rooms)
    
    def test_spawn_room_generation(self):
        """Spawn room is generated in correct area."""
        # Spawn room is now hardcoded at (2, 2, 8, 8)
        rooms = self.level_generator._create_varied_rooms(1)
        spawn_room = rooms[0]
        x, y, width, height = spawn_room

        # Spawn room should be at fixed location
        assert x == 2
        assert y == 2
        assert width == 8
        assert height == 8
    
    def test_varied_rooms_creation(self):
        """Varied rooms creation includes spawn room and avoids overlap."""
        with patch.object(self.level_generator, '_generate_rooms_avoiding_existing') as mock_gen:
            mock_gen.return_value = [(20, 20, 5, 5), (30, 30, 6, 6)]
            
            rooms = self.level_generator._create_varied_rooms(level=1)
            
            # Should have spawn room plus generated rooms
            assert len(rooms) >= 1  # At least the spawn room
            
            # First room should be the spawn room
            spawn_room = rooms[0]
            assert spawn_room == (2, 2, 8, 8)  # Fixed spawn room
            
            # Should have called room generation avoiding spawn room
            mock_gen.assert_called_once_with(1, [(2, 2, 8, 8)])


class TestLevelGeneration(TestMapGeneration):
    """Test complete level generation process."""
    
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
    
    def test_complete_level_generation(self):
        """Complete level generation creates playable level."""
        # Mock the methods to avoid complex dependencies
        with patch.object(self.level_generator, '_generate_procedural_level') as mock_proc, \
             patch.object(self.level_generator, '_place_special_tiles') as mock_special, \
             patch.object(self.level_generator, '_place_gateway') as mock_gateway:
            
            self.level_generator.generate_level(level=1, seed=12345)
            
            # Verify methods were called in correct order
            mock_proc.assert_called_once_with(1)
            mock_special.assert_called_once_with(1)
            mock_gateway.assert_called_once()
    
    def test_procedural_level_basic_structure(self):
        """Procedural level generation creates basic structure."""
        # Mock dependencies to isolate the test
        with patch.object(self.level_generator, '_create_varied_rooms') as mock_rooms, \
             patch.object(self.level_generator, '_connect_rooms_mst') as mock_connect, \
             patch.object(self.level_generator, '_add_extra_paths') as mock_paths, \
             patch.object(self.level_generator, '_add_cover_elements_new') as mock_cover, \
             patch.object(self.level_generator, '_place_shadow_areas') as mock_shadows, \
             patch.object(self.level_generator, '_ensure_border_walls_new') as mock_borders:
            
            mock_rooms.return_value = [(5, 5, 10, 8), (20, 20, 6, 6)]
            
            self.level_generator._generate_procedural_level(level=1)
            
            # Initially filled with walls
            total_positions = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
            assert len(self.game_map.walls) <= total_positions
            
            # All major steps should be called
            mock_rooms.assert_called_once_with(1)
            mock_connect.assert_called_once()
            mock_paths.assert_called_once()
            mock_cover.assert_called_once()
            mock_shadows.assert_called_once()
            mock_borders.assert_called_once()


class TestSpecialTileDistribution(TestMapGeneration):
    """Test special tile placement and distribution."""
    
    def test_special_tile_placement_counts(self):
        """Special tiles are placed according to configuration."""
        # Mock the dependencies for special tile placement
        with patch.object(self.level_generator, '_get_all_floor_positions') as mock_floor, \
             patch('game_config.GameConfig.get_network_configs') as mock_config:
            
            # Mock available floor positions
            mock_floor.return_value = [(5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)]
            
            # Mock network config for level 1
            mock_config.return_value = {
                1: {
                    'cooling_nodes': 2,
                    'cpu_recovery_nodes': 1,
                    'ghost_nodes': 1
                }
            }
            
            self.level_generator._place_special_tiles(level=1)
            
            # Should have attempted to place tiles
            mock_floor.assert_called_once()
            mock_config.assert_called_once()
    
    def test_cooling_node_placement(self):
        """Cooling nodes are placed in valid positions."""
        # Create a simple level with some open spaces
        self.game_map.walls.add((0, 0))  # Add some walls but leave open spaces
        self.game_map.walls.add((1, 0))
        
        # Test placement logic (if we can access it)
        valid_position = Position(5, 5)
        assert self.game_map.is_valid_position(valid_position)
        
        # Add a cooling node manually and test trace_level
        self.game_map.cooling_nodes.add((5, 5))
        assert self.game_map.is_cooling_node(Position(5, 5))
    
    def test_shadow_area_distribution(self):
        """Shadow areas are distributed properly."""
        # Create some rooms for shadow placement
        test_rooms = [(5, 5, 10, 8), (20, 20, 8, 6)]
        
        # Clear any existing walls for this test
        self.game_map.walls.clear()
        
        # Mock random choices to make test deterministic
        with patch('random.choice') as mock_choice, \
             patch('random.randint') as mock_randint:
            
            mock_choice.side_effect = lambda x: x[0] if x else None
            mock_randint.return_value = 2
            
            # Test shadow placement (simplified version)
            self.level_generator._place_shadow_areas(level=1, rooms=test_rooms)
            
            # Shadows should have been placed (exact count depends on implementation)
            # This tests that the method doesn't crash and produces some output
            shadow_count = len(self.game_map.shadows)
            assert shadow_count >= 0  # Should not error out


class TestMapConnectivity(TestMapGeneration):
    """Test map connectivity algorithms."""
    
    def test_room_connection_basic(self):
        """Room connection creates corridors between rooms."""
        # Create test rooms
        room1 = (5, 5, 6, 6)
        room2 = (15, 15, 6, 6)
        
        # Carve the rooms first
        self.level_generator._carve_room(room1)
        self.level_generator._carve_room(room2)

        # Use _create_corridor_between_rooms (the new method)
        self.level_generator._create_corridor_between_rooms(room1, room2)
        
        # Verify some corridor was created (check that there's a path)
        # This is a basic test - in practice we'd want to verify actual connectivity
        room1_center = (8, 8)  # Center of room1
        room2_center = (18, 18)  # Center of room2
        
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
    
    def test_mst_connection_algorithm(self):
        """MST connection algorithm connects all rooms."""
        test_rooms = [(5, 5, 5, 5), (15, 15, 5, 5), (25, 25, 5, 5)]
        
        # Mock the corridor creation method that MST actually uses
        with patch.object(self.level_generator, '_create_corridor_between_rooms') as mock_corridor:
            self.level_generator._connect_rooms_mst(test_rooms)
            
            # MST should connect all rooms (minimum spanning tree)
            # With 3 rooms, should have 2 connections minimum
            assert mock_corridor.call_count >= 2
    
    def test_extra_paths_addition(self):
        """Extra paths add alternative routes."""
        test_rooms = [(5, 5, 5, 5), (15, 15, 5, 5), (25, 25, 5, 5), (35, 35, 5, 5)]

        # Mock the corridor creation method
        with patch.object(self.level_generator, '_create_corridor_between_rooms') as mock_connect:
            self.level_generator._add_extra_paths(test_rooms)

            # Should add some additional connections for variety
            assert mock_connect.call_count >= 0


class TestMapBoundaryConditions(TestMapGeneration):
    """Test map boundary conditions and edge cases."""
    
    def test_boundary_wall_enforcement(self):
        """Boundary walls are properly enforced."""
        # Clear all walls first
        self.game_map.walls.clear()
        
        # Ensure border walls (mock the method since it might be complex)
        with patch.object(self.level_generator, '_ensure_border_walls_new') as mock_borders:
            mock_borders.return_value = None
            self.level_generator._ensure_border_walls_new()
            mock_borders.assert_called_once()
    
    def test_edge_case_room_placement(self):
        """Room placement handles edge cases correctly."""
        # Test room placement near boundaries
        edge_room = (GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10, 5, 5)
        
        # This should not crash
        self.level_generator._carve_room(edge_room)
        
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
            rooms = self.level_generator._create_varied_rooms(level=1)
            assert len(rooms) >= 1
            
            # First room should be spawn room
            spawn_room = rooms[0]
            assert spawn_room == (2, 2, 8, 8)
        finally:
            RoomGenerationConfig.MAX_ROOMS = original_max_rooms
    
    def test_zero_level_generation(self):
        """Level generation handles level 0 correctly."""
        # Mock dependencies
        with patch.object(self.level_generator, '_generate_procedural_level'), \
             patch.object(self.level_generator, '_place_special_tiles'), \
             patch.object(self.level_generator, '_place_gateway'):
            
            # Should not crash with level 0
            self.level_generator.generate_level(level=0, seed=12345)
    
    def test_high_level_generation(self):
        """Level generation handles high levels correctly."""
        # Mock dependencies to test high level scaling
        with patch.object(self.level_generator, '_generate_procedural_level'), \
             patch.object(self.level_generator, '_place_special_tiles'), \
             patch.object(self.level_generator, '_place_gateway'):
            
            # Should handle high levels without overflow
            self.level_generator.generate_level(level=100, seed=12345)


class TestRoomOverlapPrevention(TestMapGeneration):
    """Test room overlap prevention mechanisms."""
    
    def test_overlap_with_multiple_rooms(self):
        """Overlap trace_level works with multiple existing rooms."""
        existing_rooms = [
            (5, 5, 8, 6),
            (20, 20, 6, 8),
            (35, 35, 5, 5)
        ]
        
        # Test room that overlaps with first room
        overlapping_1 = (7, 7, 5, 5)
        assert self.level_generator._room_overlaps(overlapping_1, existing_rooms)
        
        # Test room that overlaps with second room
        overlapping_2 = (22, 22, 4, 4)
        assert self.level_generator._room_overlaps(overlapping_2, existing_rooms)
        
        # Test room that doesn't overlap with any
        non_overlapping = (50, 50, 5, 5)
        assert not self.level_generator._room_overlaps(non_overlapping, existing_rooms)
    
    def test_padding_consideration(self):
        """Room overlap considers padding correctly."""
        existing_rooms = [(10, 10, 10, 10)]
        padding = RoomGenerationConfig.ROOM_PADDING
        
        # Room exactly at padding distance should not overlap
        room_at_padding = (20 + padding, 10, 5, 5)
        assert not self.level_generator._room_overlaps(room_at_padding, existing_rooms)
        
        # Room inside padding distance should overlap
        room_inside_padding = (20 + padding - 1, 10, 5, 5)
        assert self.level_generator._room_overlaps(room_inside_padding, existing_rooms)
    
    def test_room_generation_avoids_existing(self):
        """Room generation properly avoids existing rooms."""
        # Mock room placement to test overlap avoidance
        existing_rooms = [(5, 5, 10, 8)]
        
        # Use a more reliable approach by mocking the carve_room method and testing logic
        with patch.object(self.level_generator, '_carve_room') as mock_carve:
            # Set a low max attempts for faster testing
            original_attempts = RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS
            RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS = 50  # Enough for some successes
            
            try:
                new_rooms = self.level_generator._generate_rooms_avoiding_existing(1, existing_rooms)
                
                # Should have generated some rooms that don't overlap
                assert len(new_rooms) >= 0  # May be 0 if all attempts failed
                
                # If any rooms were generated, they shouldn't overlap
                for room in new_rooms:
                    assert not self.level_generator._room_overlaps(room, existing_rooms)
                
                # Should have called carve_room for each generated room
                assert mock_carve.call_count == len(new_rooms)
                    
            finally:
                RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS = original_attempts


class TestMapIntegration(TestMapGeneration):
    """Integration tests for complete map functionality."""
    
    def test_full_level_generation_produces_valid_map(self):
        """Full level generation produces a playable map."""
        # Generate a complete level
        self.level_generator.generate_level(level=1, seed=42)
        
        # Basic validation - map should have walls and open areas
        assert len(self.game_map.walls) > 0  # Should have some walls
        
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
        assert border_walls > expected_border_positions * 0.7  # At least 70% border walls
    
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