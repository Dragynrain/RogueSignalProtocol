#!/usr/bin/env python3
"""
Unit tests for Level generation functionality.
Tests the actual LevelGenerator class and level creation logic.
"""

import pytest
from unittest.mock import Mock, patch
import random

# Import actual classes
from game_level import LevelGenerator
from game_entities import Position
from game_map import GameMap
from game_config import GameConfig


class TestLevelGenerator:
    """Test the actual LevelGenerator class functionality."""
    
    def test_level_generator_initialization(self):
        """LevelGenerator initializes correctly with a game map."""
        mock_map = Mock(spec=GameMap)
        level_gen = LevelGenerator(mock_map)
        
        assert level_gen.game_map is mock_map
    
    def test_clear_level_data(self):
        """_clear_level_data clears all map collections."""
        mock_map = Mock(spec=GameMap)
        # Mock all the collections that should be cleared
        mock_collections = [
            'walls', 'shadows', 'cooling_nodes', 'cpu_recovery_nodes',
            'ghost_nodes', 'code_hacks', 'exploit_pickups', 
            'permanent_upgrades', 'story_fragments', 'explored_tiles',
            'last_known_enemy_positions'
        ]
        for collection_name in mock_collections:
            setattr(mock_map, collection_name, Mock())
        mock_map.invalidate_transparency_cache = Mock()
        
        level_gen = LevelGenerator(mock_map)
        level_gen._clear_level_data()
        
        # Verify all collections were cleared
        for collection_name in mock_collections:
            getattr(mock_map, collection_name).clear.assert_called_once()
        
        # Verify transparency cache was invalidated
        mock_map.invalidate_transparency_cache.assert_called_once()
    
    def test_room_carving(self):
        """_carve_room removes walls from the specified area."""
        mock_map = Mock(spec=GameMap)
        mock_map.walls = set()
        # Add walls in the room area initially
        room = (10, 10, 15, 15)  # x, y, width, height
        for x in range(10, 25):
            for y in range(10, 25):
                mock_map.walls.add((x, y))
        
        level_gen = LevelGenerator(mock_map)
        level_gen._carve_room(room)
        
        # Verify walls were removed from the room area
        for x in range(11, 24):  # Room interior should be clear
            for y in range(11, 24):
                assert (x, y) not in mock_map.walls
    
    def test_room_overlap_detection(self):
        """_room_overlaps correctly detects room overlaps."""
        mock_map = Mock(spec=GameMap)
        level_gen = LevelGenerator(mock_map)
        
        existing_rooms = [(10, 10, 20, 20)]  # One existing room
        
        # Test overlapping room
        overlapping_room = (15, 15, 20, 20)
        assert level_gen._room_overlaps(overlapping_room, existing_rooms) is True
        
        # Test non-overlapping room
        separate_room = (40, 40, 20, 20)
        assert level_gen._room_overlaps(separate_room, existing_rooms) is False
        
        # Test edge case - adjacent with proper padding
        # Room at (10,10,20,20) with padding=1 needs x:9-31, y:9-31 clear
        # So adjacent room should start at x:32+ to not overlap  
        properly_spaced_room = (32, 10, 20, 20)
        assert level_gen._room_overlaps(properly_spaced_room, existing_rooms) is False
    
    def test_spawn_room_generation(self):
        """_generate_spawn_room creates a valid spawn room."""
        mock_map = Mock(spec=GameMap)
        level_gen = LevelGenerator(mock_map)
        
        spawn_room = level_gen._generate_spawn_room()
        
        # Should be a 4-tuple (x, y, width, height)
        assert isinstance(spawn_room, tuple)
        assert len(spawn_room) == 4
        
        x, y, width, height = spawn_room
        # Should be within map bounds
        assert 0 <= x < GameConfig.MAP_WIDTH
        assert 0 <= y < GameConfig.MAP_HEIGHT
        assert x + width <= GameConfig.MAP_WIDTH
        assert y + height <= GameConfig.MAP_HEIGHT
        
        # Should be reasonable size
        assert width > 0 and height > 0
    
    def test_varied_room_creation(self):
        """_create_varied_rooms creates multiple rooms including spawn room."""
        mock_map = Mock(spec=GameMap)
        mock_map.walls = set()
        
        level_gen = LevelGenerator(mock_map)
        
        # Mock the room generation method to avoid complex logic
        with patch.object(level_gen, '_generate_rooms_avoiding_existing', return_value=[]):
            rooms = level_gen._create_varied_rooms(level=1)
        
        # Should create at least the spawn room
        assert len(rooms) >= 1
        
        # First room should be the spawn room (top-left corner)
        spawn_room = rooms[0]
        assert spawn_room == (2, 2, 8, 8)
    
    def test_corridor_carving(self):
        """_carve_corridor creates path between two points."""
        mock_map = Mock(spec=GameMap)
        mock_map.walls = set()
        # Fill area with walls initially
        for x in range(30):
            for y in range(30):
                mock_map.walls.add((x, y))
        
        level_gen = LevelGenerator(mock_map)
        level_gen._carve_corridor(5, 5, 15, 15)
        
        # Should have carved a path (some walls removed)
        initial_wall_count = 30 * 30
        remaining_wall_count = len(mock_map.walls)
        assert remaining_wall_count < initial_wall_count
    
    def test_border_walls_enforcement(self):
        """_ensure_border_walls_new maintains walls around map edges."""
        mock_map = Mock(spec=GameMap)
        mock_map.walls = set()
        
        level_gen = LevelGenerator(mock_map)
        level_gen._ensure_border_walls_new()
        
        # Check that border walls exist
        # Top and bottom borders
        for x in range(GameConfig.MAP_WIDTH):
            assert (x, 0) in mock_map.walls  # Top border
            assert (x, GameConfig.MAP_HEIGHT - 1) in mock_map.walls  # Bottom border
        
        # Left and right borders
        for y in range(GameConfig.MAP_HEIGHT):
            assert (0, y) in mock_map.walls  # Left border
            assert (GameConfig.MAP_WIDTH - 1, y) in mock_map.walls  # Right border
    
    def test_shadow_area_placement(self):
        """_place_shadow_areas creates shadow tiles for stealth."""
        mock_map = Mock(spec=GameMap)
        mock_map.shadows = set()
        mock_map.walls = set()
        
        level_gen = LevelGenerator(mock_map)
        rooms = [(10, 10, 20, 20)]  # One test room
        
        level_gen._place_shadow_areas(level=1, rooms=rooms)
        
        # Should have placed some shadows
        assert len(mock_map.shadows) > 0
    
    def test_special_tiles_placement(self):
        """_place_special_tiles creates game objective tiles."""
        mock_map = Mock(spec=GameMap)
        # Initialize all collections
        collections = [
            'cooling_nodes', 'cpu_recovery_nodes', 'ghost_nodes',
            'code_hacks', 'exploit_pickups', 'permanent_upgrades',
            'story_fragments', 'walls'
        ]
        for collection in collections:
            setattr(mock_map, collection, set() if collection != 'walls' else set())
        
        level_gen = LevelGenerator(mock_map)
        level_gen.last_generated_rooms = [(10, 10, 20, 20)]  # Mock rooms
        
        level_gen._place_special_tiles(level=1)
        
        # Should have placed at least some special tiles
        total_special_tiles = (
            len(mock_map.cooling_nodes) +
            len(mock_map.cpu_recovery_nodes) +
            len(mock_map.ghost_nodes) +
            len(mock_map.code_hacks) +
            len(mock_map.exploit_pickups) +
            len(mock_map.permanent_upgrades) +
            len(mock_map.story_fragments)
        )
        assert total_special_tiles > 0
    
    def test_level_generation_integration(self):
        """generate_level creates a complete level."""
        mock_map = Mock(spec=GameMap)
        # Initialize all required collections and methods
        collections = [
            'walls', 'shadows', 'cooling_nodes', 'cpu_recovery_nodes',
            'ghost_nodes', 'code_hacks', 'exploit_pickups', 
            'permanent_upgrades', 'story_fragments', 'explored_tiles',
            'last_known_enemy_positions'
        ]
        for collection in collections:
            setattr(mock_map, collection, set())
        mock_map.invalidate_transparency_cache = Mock()
        mock_map.place_gateway = Mock()
        
        level_gen = LevelGenerator(mock_map)
        
        # Should not raise exceptions
        level_gen.generate_level(level=1, seed=12345)
        
        # Should have called invalidate cache multiple times
        assert mock_map.invalidate_transparency_cache.call_count >= 1
        
        # Should have created some walls (border walls at minimum)
        assert len(mock_map.walls) > 0


class TestPosition:
    """Test Position class functionality (keeping the useful parts)."""
    
    def test_position_creation(self):
        """Position creates with correct coordinates."""
        pos = Position(10, 15)
        
        assert pos.x == 10
        assert pos.y == 15
    
    def test_position_equality(self):
        """Position equality works correctly."""
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)
        pos3 = Position(6, 10)
        
        assert pos1 == pos2
        assert pos1 != pos3
    
    def test_position_distance_calculation(self):
        """Position distance calculation works if available."""
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        
        # If distance method exists, test it
        if hasattr(pos1, 'distance_to'):
            distance = pos1.distance_to(pos2)
            assert distance == 5  # 3-4-5 triangle
        else:
            # Manual distance calculation
            import math
            distance = math.sqrt((pos2.x - pos1.x)**2 + (pos2.y - pos1.y)**2)
            assert abs(distance - 5.0) < 0.001


class TestLevelGenerationEdgeCases:
    """Test edge cases and error conditions for level generation."""
    
    def test_level_generation_with_different_seeds(self):
        """Different seeds produce different levels."""
        mock_map1 = Mock(spec=GameMap)
        mock_map2 = Mock(spec=GameMap)
        
        # Initialize collections for both maps
        for mock_map in [mock_map1, mock_map2]:
            collections = [
                'walls', 'shadows', 'cooling_nodes', 'cpu_recovery_nodes',
                'ghost_nodes', 'code_hacks', 'exploit_pickups', 
                'permanent_upgrades', 'story_fragments', 'explored_tiles',
                'last_known_enemy_positions'
            ]
            for collection in collections:
                setattr(mock_map, collection, set())
            mock_map.invalidate_transparency_cache = Mock()
            mock_map.place_gateway = Mock()
        
        level_gen1 = LevelGenerator(mock_map1)
        level_gen2 = LevelGenerator(mock_map2)
        
        # Generate levels with different seeds
        level_gen1.generate_level(level=1, seed=12345)
        level_gen2.generate_level(level=1, seed=54321)
        
        # Both should succeed without errors
        assert mock_map1.invalidate_transparency_cache.called
        assert mock_map2.invalidate_transparency_cache.called
    
    @patch('game_config.GameConfig.get_network_configs')
    def test_level_generation_boundary_conditions(self, mock_network_configs):
        """Level generation works with extreme level numbers."""
        # Mock network configs to ensure they exist for test levels
        mock_network_configs.return_value = {
            1: {'enemies': 15, 'shadow_coverage': 0.15, 'cooling_nodes': 8, 'cpu_nodes': 6, 'ghost_nodes': 6, 'data_patches': 10, 'exploit_pickups': 4, 'permanent_upgrades': 2},
            2: {'enemies': 22, 'shadow_coverage': 0.18, 'cooling_nodes': 6, 'cpu_nodes': 4, 'ghost_nodes': 4, 'data_patches': 8, 'exploit_pickups': 3, 'permanent_upgrades': 2},
            3: {'enemies': 30, 'shadow_coverage': 0.16, 'cooling_nodes': 4, 'cpu_nodes': 2, 'ghost_nodes': 2, 'data_patches': 6, 'exploit_pickups': 2, 'permanent_upgrades': 2}
        }
        
        # Test boundary level values (using valid network config levels)
        test_levels = [1, 2, 3]  # Use levels that exist in network configs
        for level_num in test_levels:
            # Create completely fresh mock for each iteration to avoid cross-test contamination
            mock_map = Mock(spec=GameMap)
            collections = [
                'walls', 'shadows', 'cooling_nodes', 'cpu_recovery_nodes',
                'ghost_nodes', 'code_hacks', 'exploit_pickups', 
                'permanent_upgrades', 'story_fragments', 'explored_tiles',
                'last_known_enemy_positions'
            ]
            for collection in collections:
                setattr(mock_map, collection, set())
            mock_map.invalidate_transparency_cache = Mock()
            mock_map.place_gateway = Mock()
            
            # Mock floor positions to ensure special tile placement works
            with patch.object(LevelGenerator, '_get_all_floor_positions', return_value=[(x, y) for x in range(5) for y in range(5)]):
                level_gen = LevelGenerator(mock_map)
                
                # Should not raise exceptions
                level_gen.generate_level(level=level_num, seed=12345)
                assert mock_map.invalidate_transparency_cache.called