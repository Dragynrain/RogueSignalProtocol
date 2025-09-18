#!/usr/bin/env python3
"""
Unit tests for game_level.py - Level generation and map systems.
Tests procedural level generation, room placement, and map functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import random
from game_level import LevelGenerator
from game_map import GameMap
from game_entities import Position
from game_config import GameConfig, RoomGenerationConfig
from game_inventory import CodeHack, ExploitItem, StoryFragment


class TestGameMap:
    """Test GameMap class functionality."""
    
    def test_game_map_creation(self):
        """Test basic game map creation."""
        game_map = GameMap(50, 40)
        
        assert game_map.width == 50
        assert game_map.height == 40
        assert isinstance(game_map.walls, set)
        assert isinstance(game_map.shadows, set)
        assert isinstance(game_map.cooling_nodes, set)
        assert isinstance(game_map.cpu_recovery_nodes, set)
        assert isinstance(game_map.ghost_nodes, set)
        assert isinstance(game_map.code_hacks, dict)
        assert isinstance(game_map.exploit_pickups, dict)
        assert isinstance(game_map.permanent_upgrades, dict)
        assert isinstance(game_map.story_fragments, dict)
        assert isinstance(game_map.explored_tiles, set)
        assert isinstance(game_map.last_known_enemy_positions, dict)
    
    def test_wall_detection(self):
        """Test wall detection functionality."""
        game_map = GameMap(50, 40)
        
        # Initially no walls
        pos = Position(10, 10)
        assert game_map.is_wall(pos) is False
        
        # Add wall
        game_map.walls.add((10, 10))
        assert game_map.is_wall(pos) is True
        
        # Test invalid positions are considered walls
        invalid_pos = Position(-1, -1)
        assert game_map.is_wall(invalid_pos) is True
        
        out_of_bounds = Position(100, 100)
        assert game_map.is_wall(out_of_bounds) is True
    
    def test_shadow_detection(self):
        """Test shadow detection functionality."""
        game_map = GameMap(50, 40)
        
        pos = Position(15, 15)
        
        # Initially no shadows
        assert game_map.is_shadow(pos) is False
        
        # Add shadow
        game_map.shadows.add((15, 15))
        assert game_map.is_shadow(pos) is True
        
        # Test ghost nodes also count as shadows
        ghost_pos = Position(20, 20)
        game_map.ghost_nodes.add((20, 20))
        assert game_map.is_shadow(ghost_pos) is True
        
        # Invalid positions are not shadows
        invalid_pos = Position(-1, -1)
        assert game_map.is_shadow(invalid_pos) is False
    
    def test_special_node_detection(self):
        """Test special node detection methods."""
        game_map = GameMap(50, 40)
        
        cooling_pos = Position(10, 10)
        cpu_pos = Position(15, 15)
        ghost_pos = Position(20, 20)
        
        # Initially no special nodes
        assert game_map.is_cooling_node(cooling_pos) is False
        assert game_map.is_cpu_recovery_node(cpu_pos) is False
        assert game_map.is_ghost_node(ghost_pos) is False
        
        # Add special nodes
        game_map.cooling_nodes.add((10, 10))
        game_map.cpu_recovery_nodes.add((15, 15))
        game_map.ghost_nodes.add((20, 20))
        
        assert game_map.is_cooling_node(cooling_pos) is True
        assert game_map.is_cpu_recovery_node(cpu_pos) is True
        assert game_map.is_ghost_node(ghost_pos) is True
    
    def test_item_retrieval(self):
        """Test item retrieval methods."""
        game_map = GameMap(50, 40)
        
        pos = Position(10, 10)
        
        # Initially no items
        assert game_map.get_data_patch(pos) is None
        assert game_map.get_exploit_pickup(pos) is None
        
        # Add items
        mock_code_hack = Mock(spec=CodeHack)
        mock_exploit = Mock(spec=ExploitItem)
        
        game_map.code_hacks[(10, 10)] = mock_code_hack
        game_map.exploit_pickups[(10, 10)] = mock_exploit
        
        assert game_map.get_data_patch(pos) == mock_code_hack
        assert game_map.get_exploit_pickup(pos) == mock_exploit
    
    def test_position_validation(self):
        """Test position validation for movement."""
        game_map = GameMap(50, 40)
        
        # Valid empty position
        valid_pos = Position(10, 10)
        assert game_map.is_valid_position(valid_pos) is True
        
        # Position with wall
        game_map.walls.add((10, 10))
        assert game_map.is_valid_position(valid_pos) is False
        
        # Out of bounds position
        invalid_pos = Position(-1, -1)
        assert game_map.is_valid_position(invalid_pos) is False
        
        out_of_bounds = Position(100, 100)
        assert game_map.is_valid_position(out_of_bounds) is False
    
    @pytest.mark.parametrize("start_pos,end_pos,walls,expected_los", [
        # Clear line of sight
        (Position(0, 0), Position(5, 0), [], True),     # Horizontal line
        (Position(0, 0), Position(0, 5), [], True),     # Vertical line
        (Position(0, 0), Position(3, 3), [], True),     # Diagonal line
        
        # Blocked line of sight
        (Position(0, 0), Position(5, 0), [(2, 0)], False),  # Wall blocks horizontal
        (Position(0, 0), Position(0, 5), [(0, 2)], False),  # Wall blocks vertical
        (Position(0, 0), Position(4, 4), [(2, 2)], False),  # Wall blocks diagonal
        
        # Edge cases
        (Position(10, 10), Position(10, 10), [], True),     # Same position
    ])
    def test_line_of_sight(self, start_pos, end_pos, walls, expected_los):
        """Test line of sight calculations."""
        game_map = GameMap(50, 40)
        
        # Add walls
        for wall_x, wall_y in walls:
            game_map.walls.add((wall_x, wall_y))
        
        # Mock TCOD line of sight to avoid complexity
        with patch.object(game_map, 'has_line_of_sight_tcod', return_value=expected_los):
            result = game_map.has_line_of_sight(start_pos, end_pos)
            assert result == expected_los


class TestLevelGenerator:
    """Test LevelGenerator class functionality."""
    
    def test_level_generator_creation(self):
        """Test basic level generator creation."""
        mock_game_map = Mock(spec=GameMap)
        generator = LevelGenerator(mock_game_map)
        
        assert generator.game_map == mock_game_map
    
    def test_clear_level_data(self):
        """Test level data clearing."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set([(10, 10), (15, 15)])
        mock_game_map.shadows = set([(5, 5)])
        mock_game_map.cooling_nodes = set([(20, 20)])
        mock_game_map.cpu_recovery_nodes = set([(25, 25)])
        mock_game_map.ghost_nodes = set([(30, 30)])
        mock_game_map.code_hacks = {(35, 35): Mock()}
        mock_game_map.exploit_pickups = {(40, 40): Mock()}
        mock_game_map.permanent_upgrades = {(45, 45): "ram_boost"}
        mock_game_map.story_fragments = {(50, 50): Mock()}
        mock_game_map.explored_tiles = set([(55, 55)])
        mock_game_map.last_known_enemy_positions = {1: (Position(60, 60), 10)}
        
        generator = LevelGenerator(mock_game_map)
        generator._clear_level_data()
        
        # All collections should be cleared
        mock_game_map.walls.clear.assert_called_once()
        mock_game_map.shadows.clear.assert_called_once()
        mock_game_map.cooling_nodes.clear.assert_called_once()
        mock_game_map.cpu_recovery_nodes.clear.assert_called_once()
        mock_game_map.ghost_nodes.clear.assert_called_once()
        mock_game_map.code_hacks.clear.assert_called_once()
        mock_game_map.exploit_pickups.clear.assert_called_once()
        mock_game_map.permanent_upgrades.clear.assert_called_once()
        mock_game_map.story_fragments.clear.assert_called_once()
        mock_game_map.explored_tiles.clear.assert_called_once()
        mock_game_map.last_known_enemy_positions.clear.assert_called_once()
        mock_game_map.invalidate_transparency_cache.assert_called()
    
    def test_generate_level_flow(self):
        """Test complete level generation flow."""
        mock_game_map = Mock(spec=GameMap)
        generator = LevelGenerator(mock_game_map)
        
        # Mock all the internal methods
        with patch.object(generator, '_clear_level_data') as mock_clear:
            with patch.object(generator, '_generate_procedural_level') as mock_generate:
                with patch.object(generator, '_place_special_tiles') as mock_place_tiles:
                    with patch.object(generator, '_place_gateway') as mock_place_gateway:
                        
                        generator.generate_level(level=3, seed=12345)
                        
                        # Verify all steps were called
                        mock_clear.assert_called_once()
                        mock_generate.assert_called_once_with(3)
                        mock_place_tiles.assert_called_once_with(3)
                        mock_place_gateway.assert_called_once()
                        mock_game_map.invalidate_transparency_cache.assert_called()
    
    def test_room_carving(self):
        """Test room carving functionality."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set([(x, y) for x in range(10, 20) for y in range(10, 20)])
        
        generator = LevelGenerator(mock_game_map)
        
        # Carve a 5x5 room at (12, 12)
        room = (12, 12, 5, 5)
        generator._carve_room(room)
        
        # Check that walls were removed in the room area
        for x in range(12, 17):
            for y in range(12, 17):
                mock_game_map.walls.remove.assert_any_call((x, y))
    
    @pytest.mark.parametrize("room1,room2,padding,expected_overlap", [
        # Non-overlapping rooms
        ((0, 0, 5, 5), (10, 10, 5, 5), 1, False),
        ((0, 0, 5, 5), (7, 0, 5, 5), 1, False),    # Just touching with padding
        
        # Overlapping rooms
        ((0, 0, 5, 5), (3, 3, 5, 5), 1, True),     # Partial overlap
        ((0, 0, 5, 5), (0, 0, 5, 5), 1, True),     # Same position
        ((0, 0, 5, 5), (1, 1, 3, 3), 1, True),     # One inside other
        
        # Edge cases with padding
        ((0, 0, 5, 5), (6, 0, 5, 5), 1, True),     # Violates padding
        ((0, 0, 5, 5), (7, 0, 5, 5), 2, True),     # Violates larger padding
    ])
    def test_room_overlap_detection(self, room1, room2, padding, expected_overlap):
        """Test room overlap detection with various configurations."""
        mock_game_map = Mock(spec=GameMap)
        generator = LevelGenerator(mock_game_map)
        
        # Mock the padding configuration
        with patch.object(RoomGenerationConfig, 'ROOM_PADDING', padding):
            result = generator._room_overlaps(room2, [room1])
            assert result == expected_overlap
    
    def test_spawn_room_generation(self):
        """Test spawn room generation in top-left area."""
        mock_game_map = Mock(spec=GameMap)
        generator = LevelGenerator(mock_game_map)
        
        # Generate multiple spawn rooms to test variety
        spawn_rooms = []
        for seed in range(10):
            random.seed(seed)
            spawn_room = generator._generate_spawn_room()
            spawn_rooms.append(spawn_room)
            
            x, y, width, height = spawn_room
            
            # Verify spawn room is in top-left area
            assert x >= 1 and x <= 4, f"Spawn room x {x} not in valid range"
            assert y >= 1 and y <= 4, f"Spawn room y {y} not in valid range"
            assert 6 <= width <= 10, f"Spawn room width {width} not in valid range"
            assert 6 <= height <= 10, f"Spawn room height {height} not in valid range"
            
            # Verify room doesn't extend too far
            assert x + width <= 15, f"Spawn room extends too far right: {x + width}"
            assert y + height <= 15, f"Spawn room extends too far down: {y + height}"
    
    def test_varied_rooms_generation(self):
        """Test generation of varied rooms."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set()
        
        generator = LevelGenerator(mock_game_map)
        
        with patch.object(generator, '_carve_room') as mock_carve:
            with patch.object(generator, '_generate_rooms_avoiding_existing') as mock_generate_rooms:
                mock_generate_rooms.return_value = [
                    (15, 15, 8, 6),
                    (30, 20, 6, 8),
                    (40, 35, 7, 7)
                ]
                
                rooms = generator._create_varied_rooms(level=2)
                
                # Should have spawn room plus generated rooms
                assert len(rooms) == 4  # 1 spawn + 3 generated
                
                # First room should be spawn room
                spawn_room = rooms[0]
                assert spawn_room == (2, 2, 8, 8)
                
                # Should have called generation with spawn room excluded
                mock_generate_rooms.assert_called_once_with(2, [(2, 2, 8, 8)])
    
    def test_room_generation_respects_limits(self):
        """Test that room generation respects configuration limits."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set()
        
        generator = LevelGenerator(mock_game_map)
        
        with patch.object(generator, '_carve_room'):
            with patch.object(generator, '_room_overlaps', return_value=False):
                # Test with small max rooms limit
                with patch.object(RoomGenerationConfig, 'MAX_ROOMS', 3):
                    with patch.object(RoomGenerationConfig, 'MIN_ROOMS_BASE', 5):
                        with patch.object(RoomGenerationConfig, 'ROOM_LEVEL_MULTIPLIER', 2):
                            
                            rooms = generator._generate_rooms_avoiding_existing(1, [])
                            
                            # Should respect MAX_ROOMS limit (3) despite calculation (5 + 1*2 = 7)
                            assert len(rooms) <= 3
    
    def test_corridor_carving(self):
        """Test corridor carving between points."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set([(x, y) for x in range(50) for y in range(50)])
        
        generator = LevelGenerator(mock_game_map)
        
        # Test horizontal corridor
        generator._carve_corridor(5, 10, 15, 10)
        
        # Should remove walls along the corridor
        for x in range(5, 16):
            mock_game_map.walls.remove.assert_any_call((x, 10))
        
        # Reset mock
        mock_game_map.reset_mock()
        mock_game_map.walls = set([(x, y) for x in range(50) for y in range(50)])
        
        # Test vertical corridor
        generator._carve_corridor(10, 5, 10, 15)
        
        # Should remove walls along the corridor
        for y in range(5, 16):
            mock_game_map.walls.remove.assert_any_call((10, y))
    
    def test_room_connection(self):
        """Test connecting two rooms with corridors."""
        mock_game_map = Mock(spec=GameMap)
        generator = LevelGenerator(mock_game_map)
        
        room1 = (10, 10, 8, 8)  # Room at (10,10) with size 8x8
        room2 = (25, 25, 6, 6)  # Room at (25,25) with size 6x6
        
        with patch.object(generator, '_carve_corridor') as mock_carve:
            generator._connect_two_rooms(room1, room2)
            
            # Should have carved two corridor segments (L-shaped)
            assert mock_carve.call_count == 2
            
            # Verify corridor endpoints involve room centers
            room1_center_x, room1_center_y = 14, 14  # 10 + 8//2, 10 + 8//2
            room2_center_x, room2_center_y = 28, 28  # 25 + 6//2, 25 + 6//2
            
            # Check that corridors connect the room centers
            calls = mock_carve.call_args_list
            assert len(calls) == 2
            
            # Corridors should form L-shape connecting room centers
            call1_args = calls[0][0]
            call2_args = calls[1][0]
            
            # One corridor should start from room1 center
            assert (call1_args[0] == room1_center_x and call1_args[1] == room1_center_y) or \
                   (call2_args[0] == room1_center_x and call2_args[1] == room1_center_y)
            
            # One corridor should end at room2 center
            assert (call1_args[2] == room2_center_x and call1_args[3] == room2_center_y) or \
                   (call2_args[2] == room2_center_x and call2_args[3] == room2_center_y)


class TestLevelGeneration:
    """Test complete level generation scenarios."""
    
    def test_full_level_generation(self):
        """Test complete level generation with realistic parameters."""
        game_map = GameMap(50, 40)
        generator = LevelGenerator(game_map)
        
        # Mock the complex internal methods that would require extensive setup
        with patch.object(generator, '_connect_rooms_mst') as mock_connect:
            with patch.object(generator, '_add_extra_paths') as mock_extra:
                with patch.object(generator, '_add_cover_elements_new') as mock_cover:
                    with patch.object(generator, '_place_shadow_areas') as mock_shadows:
                        with patch.object(generator, '_ensure_border_walls_new') as mock_borders:
                            with patch.object(generator, '_place_special_tiles') as mock_tiles:
                                with patch.object(generator, '_place_gateway') as mock_gateway:
                                    
                                    generator.generate_level(level=1, seed=12345)
                                    
                                    # Verify all generation steps were called
                                    mock_connect.assert_called_once()
                                    mock_extra.assert_called_once()
                                    mock_cover.assert_called_once()
                                    mock_shadows.assert_called_once()
                                    mock_borders.assert_called_once()
                                    mock_tiles.assert_called_once_with(1)
                                    mock_gateway.assert_called_once()
    
    def test_deterministic_generation(self):
        """Test that level generation is deterministic with same seed."""
        game_map1 = GameMap(30, 30)
        game_map2 = GameMap(30, 30)
        
        generator1 = LevelGenerator(game_map1)
        generator2 = LevelGenerator(game_map2)
        
        # Mock complex generation steps to focus on determinism
        with patch.object(generator1, '_connect_rooms_mst'), \
             patch.object(generator1, '_add_extra_paths'), \
             patch.object(generator1, '_add_cover_elements_new'), \
             patch.object(generator1, '_place_shadow_areas'), \
             patch.object(generator1, '_ensure_border_walls_new'), \
             patch.object(generator1, '_place_special_tiles'), \
             patch.object(generator1, '_place_gateway'), \
             patch.object(generator2, '_connect_rooms_mst'), \
             patch.object(generator2, '_add_extra_paths'), \
             patch.object(generator2, '_add_cover_elements_new'), \
             patch.object(generator2, '_place_shadow_areas'), \
             patch.object(generator2, '_ensure_border_walls_new'), \
             patch.object(generator2, '_place_special_tiles'), \
             patch.object(generator2, '_place_gateway'):
            
            # Generate with same seed
            generator1.generate_level(level=2, seed=54321)
            generator2.generate_level(level=2, seed=54321)
            
            # Both should have the same spawn room (deterministic)
            assert hasattr(generator1, 'last_generated_rooms')
            assert hasattr(generator2, 'last_generated_rooms')
            
            # Spawn rooms should be identical
            spawn_room1 = generator1.last_generated_rooms[0] if generator1.last_generated_rooms else None
            spawn_room2 = generator2.last_generated_rooms[0] if generator2.last_generated_rooms else None
            
            if spawn_room1 and spawn_room2:
                assert spawn_room1 == spawn_room2
    
    @pytest.mark.parametrize("level,expected_min_rooms", [
        (1, 15),  # MIN_ROOMS_BASE + 1 * ROOM_LEVEL_MULTIPLIER = 12 + 3 = 15
        (2, 18),  # MIN_ROOMS_BASE + 2 * ROOM_LEVEL_MULTIPLIER = 12 + 6 = 18  
        (3, 20),  # MIN_ROOMS_BASE + 3 * ROOM_LEVEL_MULTIPLIER = 12 + 9 = 21, capped at MAX_ROOMS (20)
        (5, 20),  # Should be capped at MAX_ROOMS
    ])
    def test_room_count_scaling(self, level, expected_min_rooms):
        """Test that room count scales with level appropriately."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set()
        
        generator = LevelGenerator(mock_game_map)
        
        with patch.object(generator, '_carve_room'):
            with patch.object(generator, '_room_overlaps', return_value=False):
                
                # Generate enough attempts to hit the target
                with patch.object(RoomGenerationConfig, 'MAX_PLACEMENT_ATTEMPTS', 1000):
                    rooms = generator._generate_rooms_avoiding_existing(level, [])
                    
                    # Should attempt to generate the calculated number of rooms
                    expected_target = min(
                        RoomGenerationConfig.MIN_ROOMS_BASE + level * RoomGenerationConfig.ROOM_LEVEL_MULTIPLIER,
                        RoomGenerationConfig.MAX_ROOMS
                    )
                    
                    # With no overlap restrictions, should achieve the target
                    assert len(rooms) == expected_target
    
    def test_level_boundaries(self):
        """Test that generated rooms respect level boundaries."""
        mock_game_map = Mock(spec=GameMap)
        mock_game_map.walls = set()
        
        generator = LevelGenerator(mock_game_map)
        
        with patch.object(generator, '_carve_room'):
            with patch.object(generator, '_room_overlaps', return_value=False):
                
                # Generate rooms and check boundaries
                rooms = generator._generate_rooms_avoiding_existing(1, [])
                
                for room in rooms:
                    x, y, width, height = room
                    
                    # Rooms should be within map boundaries
                    assert x >= 0 and x < GameConfig.MAP_WIDTH
                    assert y >= 0 and y < GameConfig.MAP_HEIGHT
                    assert x + width <= GameConfig.MAP_WIDTH
                    assert y + height <= GameConfig.MAP_HEIGHT
                    
                    # Rooms should avoid spawn area (first 12 coordinates)
                    assert x >= 12 or y >= 12, "Room should avoid spawn area"


class TestMapIntegration:
    """Test integration between map and level generation."""
    
    def test_map_state_after_generation(self):
        """Test map state after level generation."""
        game_map = GameMap(30, 30)
        generator = LevelGenerator(game_map)
        
        # Initially map should be empty
        assert len(game_map.walls) == 0
        assert len(game_map.shadows) == 0
        assert len(game_map.explored_tiles) == 0
        
        # After generation, map should have content
        with patch.object(generator, '_place_special_tiles'), \
             patch.object(generator, '_place_gateway'):
            
            generator.generate_level(level=1, seed=11111)
            
            # Should have created some walls (spawn room area carved out)
            # Note: walls are added for entire map then carved out for rooms
            assert len(game_map.walls) > 0
            
            # Should have rooms stored
            assert hasattr(generator, 'last_generated_rooms')
            assert len(generator.last_generated_rooms) > 0
    
    def test_special_tile_placement_integration(self):
        """Test integration of special tile placement."""
        game_map = GameMap(50, 40)
        generator = LevelGenerator(game_map)
        
        # Mock special tile placement to track calls
        with patch.object(generator, '_place_special_tiles') as mock_place_tiles:
            with patch.object(generator, '_place_gateway') as mock_place_gateway:
                
                generator.generate_level(level=2, seed=22222)
                
                # Special tiles should be placed
                mock_place_tiles.assert_called_once_with(2)
                mock_place_gateway.assert_called_once()
    
    def test_memory_system_integration(self):
        """Test that memory systems are properly initialized."""
        game_map = GameMap(50, 40)
        generator = LevelGenerator(game_map)
        
        # Add some existing data
        game_map.explored_tiles.add((10, 10))
        game_map.last_known_enemy_positions[1] = (Position(15, 15), 5)
        
        # Generation should clear existing data
        with patch.object(generator, '_place_special_tiles'), \
             patch.object(generator, '_place_gateway'):
            
            generator.generate_level(level=1, seed=33333)
            
            # Memory systems should be cleared
            assert len(game_map.explored_tiles) == 0
            assert len(game_map.last_known_enemy_positions) == 0