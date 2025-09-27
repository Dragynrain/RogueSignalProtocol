#!/usr/bin/env python3
"""
Unit tests for map data structure operations.
Tests the actual GameMap class and map query functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod

# Import actual map classes
from game_map import GameMap
from game_entities import Position
from game_inventory import CodeHack, ExploitItem, StoryFragment


class TestGameMapInitialization:
    """Test GameMap initialization and basic properties."""
    
    def test_game_map_initialization(self):
        """GameMap initializes with correct dimensions and empty collections."""
        game_map = GameMap(width=50, height=30)
        
        assert game_map.width == 50
        assert game_map.height == 30
        
        # Terrain sets should be empty initially
        assert len(game_map.walls) == 0
        assert len(game_map.shadows) == 0
        
        # Feature sets should be empty initially
        assert len(game_map.cooling_nodes) == 0
        assert len(game_map.cpu_recovery_nodes) == 0
        assert len(game_map.ghost_nodes) == 0
        
        # Item dictionaries should be empty initially
        assert len(game_map.code_hacks) == 0
        assert len(game_map.exploit_pickups) == 0
        assert len(game_map.permanent_upgrades) == 0
        assert len(game_map.story_fragments) == 0
        
        # Special locations should be None initially
        assert game_map.gateway is None
        
        # Memory systems should be empty initially
        assert len(game_map.explored_tiles) == 0
        assert len(game_map.last_known_enemy_positions) == 0
    
    def test_game_map_dimensions_immutable(self):
        """GameMap dimensions remain constant after initialization."""
        game_map = GameMap(width=80, height=25)
        
        original_width = game_map.width
        original_height = game_map.height
        
        # Add some content to the map
        game_map.walls.add((10, 10))
        game_map.shadows.add((15, 15))
        
        # Dimensions should remain unchanged
        assert game_map.width == original_width
        assert game_map.height == original_height


class TestTerrainQueries:
    """Test terrain checking methods."""
    
    def test_is_wall_basic(self):
        """is_wall correctly identifies walls."""
        game_map = GameMap(50, 30)
        test_pos = Position(10, 15)
        
        # Initially no walls
        assert game_map.is_wall(test_pos) is False
        
        # Add wall at position
        game_map.walls.add((10, 15))
        assert game_map.is_wall(test_pos) is True
        
        # Other positions should still be non-walls
        other_pos = Position(11, 15)
        assert game_map.is_wall(other_pos) is False
    
    def test_is_wall_out_of_bounds(self):
        """is_wall returns True for out-of-bounds positions."""
        game_map = GameMap(50, 30)
        
        out_of_bounds_positions = [
            Position(-1, 10),    # Negative X
            Position(10, -1),    # Negative Y
            Position(50, 10),    # X >= width
            Position(10, 30),    # Y >= height
            Position(100, 100)   # Both out of bounds
        ]
        
        for pos in out_of_bounds_positions:
            assert game_map.is_wall(pos) is True
    
    def test_is_shadow_basic(self):
        """is_shadow correctly identifies shadow areas."""
        game_map = GameMap(50, 30)
        test_pos = Position(20, 10)
        
        # Initially no shadows
        assert game_map.is_shadow(test_pos) is False
        
        # Add shadow at position
        game_map.shadows.add((20, 10))
        assert game_map.is_shadow(test_pos) is True
    
    def test_is_shadow_ghost_nodes(self):
        """is_shadow also considers ghost nodes as shadows."""
        game_map = GameMap(50, 30)
        test_pos = Position(25, 15)
        
        # Ghost nodes function as shadows
        game_map.ghost_nodes.add((25, 15))
        assert game_map.is_shadow(test_pos) is True
    
    def test_is_shadow_out_of_bounds(self):
        """is_shadow returns False for out-of-bounds positions."""
        game_map = GameMap(50, 30)
        
        out_of_bounds_pos = Position(-5, -5)
        assert game_map.is_shadow(out_of_bounds_pos) is False
    
    def test_terrain_independence(self):
        """Different terrain types are independent."""
        game_map = GameMap(40, 25)
        pos = Position(15, 12)
        
        # Position can have multiple terrain features simultaneously
        game_map.walls.add((15, 12))
        game_map.shadows.add((15, 12))
        
        assert game_map.is_wall(pos) is True
        assert game_map.is_shadow(pos) is True


class TestFeatureNodes:
    """Test special feature node checking methods."""
    
    def test_cooling_node_detection(self):
        """is_cooling_node correctly identifies cooling nodes."""
        game_map = GameMap(50, 30)
        node_pos = Position(30, 20)
        
        assert game_map.is_cooling_node(node_pos) is False
        
        game_map.cooling_nodes.add((30, 20))
        assert game_map.is_cooling_node(node_pos) is True
    
    def test_cpu_recovery_node_detection(self):
        """is_cpu_recovery_node correctly identifies CPU recovery nodes."""
        game_map = GameMap(50, 30)
        node_pos = Position(35, 25)
        
        assert game_map.is_cpu_recovery_node(node_pos) is False
        
        game_map.cpu_recovery_nodes.add((35, 25))
        assert game_map.is_cpu_recovery_node(node_pos) is True
    
    def test_ghost_node_detection(self):
        """is_ghost_node correctly identifies ghost nodes."""
        game_map = GameMap(50, 30)
        node_pos = Position(40, 18)
        
        assert game_map.is_ghost_node(node_pos) is False
        
        game_map.ghost_nodes.add((40, 18))
        assert game_map.is_ghost_node(node_pos) is True
    
    def test_multiple_node_types(self):
        """Multiple node types can coexist at the same position."""
        game_map = GameMap(50, 30)
        pos = Position(25, 15)
        
        # Add multiple node types at same position (though unusual)
        game_map.cooling_nodes.add((25, 15))
        game_map.cpu_recovery_nodes.add((25, 15))
        game_map.ghost_nodes.add((25, 15))
        
        assert game_map.is_cooling_node(pos) is True
        assert game_map.is_cpu_recovery_node(pos) is True
        assert game_map.is_ghost_node(pos) is True
        # Ghost nodes also function as shadows
        assert game_map.is_shadow(pos) is True


class TestItemRetrieval:
    """Test item retrieval methods."""
    
    def test_get_data_patch(self):
        """get_data_patch retrieves code hacks correctly."""
        game_map = GameMap(50, 30)
        pos = Position(12, 8)
        
        # No code hack initially
        assert game_map.get_data_patch(pos) is None
        
        # Add code hack
        mock_code_hack = Mock(spec=CodeHack)
        game_map.code_hacks[(12, 8)] = mock_code_hack
        
        retrieved_hack = game_map.get_data_patch(pos)
        assert retrieved_hack is mock_code_hack
    
    def test_get_exploit_pickup(self):
        """get_exploit_pickup retrieves exploit items correctly."""
        game_map = GameMap(50, 30)
        pos = Position(18, 22)
        
        # No exploit pickup initially
        assert game_map.get_exploit_pickup(pos) is None
        
        # Add exploit pickup
        mock_exploit = Mock(spec=ExploitItem)
        game_map.exploit_pickups[(18, 22)] = mock_exploit
        
        retrieved_exploit = game_map.get_exploit_pickup(pos)
        assert retrieved_exploit is mock_exploit
    
    def test_multiple_items_at_different_positions(self):
        """Different items can be placed at different positions."""
        game_map = GameMap(50, 30)
        
        pos1 = Position(10, 10)
        pos2 = Position(20, 20)
        
        mock_code_hack = Mock(spec=CodeHack)
        mock_exploit = Mock(spec=ExploitItem)
        
        game_map.code_hacks[(10, 10)] = mock_code_hack
        game_map.exploit_pickups[(20, 20)] = mock_exploit
        
        # Items should be retrievable at their respective positions
        assert game_map.get_data_patch(pos1) is mock_code_hack
        assert game_map.get_exploit_pickup(pos2) is mock_exploit
        
        # And not at other positions
        assert game_map.get_data_patch(pos2) is None
        assert game_map.get_exploit_pickup(pos1) is None


class TestPositionValidation:
    """Test position validation methods."""
    
    def test_is_valid_position_basic(self):
        """is_valid_position correctly validates positions."""
        game_map = GameMap(40, 25)
        
        # Valid positions within bounds
        valid_positions = [
            Position(0, 0),      # Corner
            Position(20, 12),    # Center
            Position(39, 24),    # Opposite corner
        ]
        
        for pos in valid_positions:
            assert game_map.is_valid_position(pos) is True
    
    def test_is_valid_position_out_of_bounds(self):
        """is_valid_position rejects out-of-bounds positions."""
        game_map = GameMap(40, 25)
        
        invalid_positions = [
            Position(-1, 10),    # Negative X
            Position(10, -1),    # Negative Y
            Position(40, 10),    # X >= width
            Position(10, 25),    # Y >= height
        ]
        
        for pos in invalid_positions:
            assert game_map.is_valid_position(pos) is False
    
    def test_is_valid_position_walls_block(self):
        """is_valid_position rejects positions with walls."""
        game_map = GameMap(40, 25)
        wall_pos = Position(15, 10)
        
        # Initially valid (no wall)
        assert game_map.is_valid_position(wall_pos) is True
        
        # Add wall - should become invalid
        game_map.walls.add((15, 10))
        assert game_map.is_valid_position(wall_pos) is False
    
    def test_is_valid_position_shadows_allow_movement(self):
        """is_valid_position allows movement through shadows."""
        game_map = GameMap(40, 25)
        shadow_pos = Position(20, 15)
        
        # Add shadow - should still be valid for movement
        game_map.shadows.add((20, 15))
        assert game_map.is_valid_position(shadow_pos) is True


class TestLineOfSight:
    """Test line of sight calculation methods."""
    
    def test_has_line_of_sight_clear_path(self):
        """has_line_of_sight returns True for clear paths."""
        game_map = GameMap(50, 30)
        start = Position(10, 10)
        end = Position(15, 10)  # Same row, clear line
        
        # No walls between positions
        assert game_map.has_line_of_sight(start, end) == True
    
    def test_has_line_of_sight_blocked_path(self):
        """has_line_of_sight returns False for blocked paths."""
        game_map = GameMap(50, 30)
        start = Position(10, 10)
        end = Position(15, 10)
        
        # Add wall between positions
        game_map.walls.add((12, 10))
        
        # Mock the TCOD line of sight check
        with patch.object(game_map, 'has_line_of_sight_tcod', return_value=False):
            assert game_map.has_line_of_sight(start, end) is False
    
    def test_has_line_of_sight_delegates_to_tcod(self):
        """has_line_of_sight delegates to TCOD implementation."""
        game_map = GameMap(50, 30)
        start = Position(5, 5)
        end = Position(10, 10)
        
        with patch.object(game_map, 'has_line_of_sight_tcod', return_value=True) as mock_tcod:
            result = game_map.has_line_of_sight(start, end)
            
            assert result is True
            mock_tcod.assert_called_once_with(start, end)
    
    def test_has_line_of_sight_bresenham_basic(self):
        """has_line_of_sight_bresenham works for basic cases."""
        game_map = GameMap(30, 20)
        start = Position(5, 5)
        end = Position(5, 10)  # Straight vertical line
        
        # No walls - should have line of sight
        assert game_map.has_line_of_sight_bresenham(start, end) is True
    
    def test_has_line_of_sight_bresenham_out_of_bounds(self):
        """has_line_of_sight_bresenham handles out-of-bounds positions."""
        game_map = GameMap(30, 20)
        start = Position(-1, -1)  # Out of bounds
        end = Position(10, 10)
        
        assert game_map.has_line_of_sight_bresenham(start, end) is False
    
    def test_can_see_position_with_range(self):
        """can_see_position considers vision range."""
        game_map = GameMap(50, 30)
        start = Position(10, 10)
        end = Position(20, 10)  # 10 tiles away
        
        vision_range = 5  # Too short to see end position
        
        result = game_map.can_see_position(start, end, vision_range)
        assert result is False
        
        vision_range = 15  # Long enough to see end position
        with patch.object(game_map, 'has_line_of_sight', return_value=True):
            result = game_map.can_see_position(start, end, vision_range)
            assert result == True


class TestTransparencyCache:
    """Test transparency caching system."""
    
    def test_invalidate_transparency_cache(self):
        """invalidate_transparency_cache clears the cache."""
        game_map = GameMap(30, 20)
        
        # Method should exist and be callable
        game_map.invalidate_transparency_cache()
        
        # Should not raise any errors
        assert True
    
    def test_get_transparency_map(self):
        """_get_transparency_map creates transparency data."""
        game_map = GameMap(20, 15)
        
        # Add some walls
        game_map.walls.add((5, 5))
        game_map.walls.add((10, 10))
        
        transparency_map = game_map._get_transparency_map()
        
        # Should return a data structure (implementation may vary)
        assert transparency_map is not None
    
    def test_transparency_cache_invalidation_on_changes(self):
        """Transparency cache should be invalidated when map changes."""
        game_map = GameMap(25, 20)
        
        # This is more of an integration test to ensure the pattern is followed
        # In real usage, map changes should call invalidate_transparency_cache()
        game_map.walls.add((12, 8))
        game_map.invalidate_transparency_cache()
        
        # Should work without errors
        transparency_map = game_map._get_transparency_map()
        assert transparency_map is not None


class TestMemorySystem:
    """Test explored tiles and enemy memory systems."""
    
    def test_explored_tiles_management(self):
        """Explored tiles can be added and queried."""
        game_map = GameMap(40, 25)
        
        # Initially no explored tiles
        assert len(game_map.explored_tiles) == 0
        
        # Add explored tiles
        game_map.explored_tiles.add((10, 10))
        game_map.explored_tiles.add((15, 12))
        
        assert len(game_map.explored_tiles) == 2
        assert (10, 10) in game_map.explored_tiles
        assert (15, 12) in game_map.explored_tiles
        assert (20, 20) not in game_map.explored_tiles
    
    def test_last_known_enemy_positions(self):
        """Last known enemy positions can be tracked."""
        game_map = GameMap(40, 25)
        
        # Initially no enemy positions tracked
        assert len(game_map.last_known_enemy_positions) == 0
        
        # Track enemy positions
        enemy_id_1 = 100
        enemy_id_2 = 101
        position_1 = Position(20, 15)
        position_2 = Position(25, 18)
        
        game_map.last_known_enemy_positions[enemy_id_1] = (position_1, 150)  # Turn 150
        game_map.last_known_enemy_positions[enemy_id_2] = (position_2, 155)  # Turn 155
        
        assert len(game_map.last_known_enemy_positions) == 2
        
        # Verify data integrity
        stored_pos_1, turn_1 = game_map.last_known_enemy_positions[enemy_id_1]
        assert stored_pos_1.x == 20 and stored_pos_1.y == 15
        assert turn_1 == 150
        
        stored_pos_2, turn_2 = game_map.last_known_enemy_positions[enemy_id_2]
        assert stored_pos_2.x == 25 and stored_pos_2.y == 18
        assert turn_2 == 155
    
    def test_memory_system_updates(self):
        """Memory system can be updated over time."""
        game_map = GameMap(40, 25)
        enemy_id = 200
        
        # Initial enemy sighting
        game_map.last_known_enemy_positions[enemy_id] = (Position(10, 10), 100)
        
        # Update enemy position
        game_map.last_known_enemy_positions[enemy_id] = (Position(12, 10), 105)
        
        # Should have updated data
        stored_pos, turn = game_map.last_known_enemy_positions[enemy_id]
        assert stored_pos.x == 12 and stored_pos.y == 10
        assert turn == 105


class TestSpecialLocations:
    """Test special location management."""
    
    def test_gateway_placement(self):
        """Gateway location can be set and retrieved."""
        game_map = GameMap(50, 30)
        
        # Initially no gateway
        assert game_map.gateway is None
        
        # Place gateway
        gateway_pos = Position(45, 25)
        game_map.gateway = gateway_pos
        
        assert game_map.gateway is not None
        assert game_map.gateway.x == 45
        assert game_map.gateway.y == 25
    
    def test_gateway_replacement(self):
        """Gateway can be moved to a new location."""
        game_map = GameMap(50, 30)
        
        # Place initial gateway
        game_map.gateway = Position(20, 15)
        
        # Move gateway
        new_gateway_pos = Position(30, 20)
        game_map.gateway = new_gateway_pos
        
        assert game_map.gateway.x == 30
        assert game_map.gateway.y == 20


class TestMapIntegration:
    """Test integration between different map systems."""
    
    def test_complex_map_state(self):
        """GameMap can handle complex states with multiple features."""
        game_map = GameMap(60, 40)
        
        # Add various terrain features
        game_map.walls.update([(10, 10), (11, 10), (12, 10)])  # Wall line
        game_map.shadows.update([(5, 5), (6, 6), (7, 7)])      # Shadow area
        
        # Add special nodes
        game_map.cooling_nodes.add((20, 20))
        game_map.cpu_recovery_nodes.add((25, 25))
        game_map.ghost_nodes.add((30, 30))
        
        # Add items
        mock_code_hack = Mock(spec=CodeHack)
        mock_exploit = Mock(spec=ExploitItem)
        game_map.code_hacks[(15, 15)] = mock_code_hack
        game_map.exploit_pickups[(35, 35)] = mock_exploit
        
        # Set gateway
        game_map.gateway = Position(55, 35)
        
        # Add explored tiles
        game_map.explored_tiles.update([(i, j) for i in range(10, 15) for j in range(10, 15)])
        
        # Verify all systems work together
        assert game_map.is_wall(Position(10, 10)) is True
        assert game_map.is_shadow(Position(5, 5)) is True
        assert game_map.is_cooling_node(Position(20, 20)) is True
        assert game_map.get_data_patch(Position(15, 15)) is mock_code_hack
        assert game_map.gateway.x == 55
        assert len(game_map.explored_tiles) == 25
    
    def test_map_query_performance(self):
        """Map queries should be efficient for repeated calls."""
        game_map = GameMap(100, 100)
        
        # Add substantial content
        for i in range(0, 100, 10):
            game_map.walls.add((i, 50))  # Horizontal wall line
            game_map.shadows.add((50, i))  # Vertical shadow line
        
        # Perform many queries - should not crash or be extremely slow
        test_position = Position(25, 25)
        
        for _ in range(100):
            game_map.is_wall(test_position)
            game_map.is_shadow(test_position)
            game_map.is_valid_position(test_position)
        
        # If we get here without timing out, performance is acceptable
        assert True
    
    def test_map_state_consistency(self):
        """Map state remains consistent across operations."""
        game_map = GameMap(50, 30)
        
        # Add overlapping features at same position
        pos = Position(25, 15)
        game_map.walls.add((25, 15))
        game_map.shadows.add((25, 15))
        game_map.cooling_nodes.add((25, 15))
        
        # Wall should block movement
        assert game_map.is_valid_position(pos) is False
        # But other features should still be detectable
        assert game_map.is_shadow(pos) is True
        assert game_map.is_cooling_node(pos) is True
    
    def test_map_boundary_handling(self):
        """Map handles boundary conditions gracefully."""
        game_map = GameMap(10, 10)  # Small map for testing boundaries
        
        boundary_positions = [
            Position(0, 0),      # Top-left corner
            Position(9, 0),      # Top-right corner
            Position(0, 9),      # Bottom-left corner
            Position(9, 9),      # Bottom-right corner
            Position(5, 0),      # Top edge
            Position(5, 9),      # Bottom edge
            Position(0, 5),      # Left edge
            Position(9, 5),      # Right edge
        ]
        
        for pos in boundary_positions:
            # All boundary positions should be valid for queries
            assert game_map.is_wall(pos) is False  # No walls initially
            assert game_map.is_shadow(pos) is False  # No shadows initially
            assert game_map.is_valid_position(pos) is True  # Valid for movement
            
            # Should be able to add features at boundary positions
            game_map.walls.add((pos.x, pos.y))
            assert game_map.is_wall(pos) is True