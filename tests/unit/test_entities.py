#!/usr/bin/env python3
"""
Unit tests for game_entities.py core data structures.
Tests Position class, enums, and utility functions using real objects.
"""

import pytest
import math
from game_entities import Position, Colors, EnemyState, EnemyMovement, TargetingMode


class TestPosition:
    """Test the Position class functionality."""
    
    def test_position_creation(self):
        """Position can be created with x, y coordinates."""
        pos = Position(10, 5)
        assert pos.x == 10
        assert pos.y == 5
    
    def test_position_distance_calculation(self):
        """Position calculates Euclidean distance correctly."""
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        
        distance = pos1.distance_to(pos2)
        expected = math.sqrt(3**2 + 4**2)  # 5.0
        
        assert distance == expected
        assert distance == 5.0
    
    def test_position_distance_same_position(self):
        """Distance to same position is zero."""
        pos = Position(10, 10)
        distance = pos.distance_to(pos)
        assert distance == 0.0
    
    def test_position_distance_to_none_raises_error(self):
        """Distance calculation to None raises ValueError."""
        pos = Position(5, 5)
        with pytest.raises(ValueError, match="Cannot calculate distance to None position"):
            pos.distance_to(None)
    
    def test_position_is_valid_within_bounds(self):
        """Position validation works for valid coordinates."""
        pos = Position(5, 8)
        assert pos.is_valid(10, 10) is True
        assert pos.is_valid(6, 9) is True
        assert pos.is_valid(5, 8) is False  # Boundary case - width/height are exclusive
    
    def test_position_is_valid_out_of_bounds(self):
        """Position validation works for invalid coordinates."""
        # Negative coordinates
        pos_neg = Position(-1, 5)
        assert pos_neg.is_valid(10, 10) is False
        
        # Coordinates too large
        pos_large = Position(10, 5)
        assert pos_large.is_valid(10, 10) is False  # x >= width
        
        pos_large_y = Position(5, 10)
        assert pos_large_y.is_valid(10, 10) is False  # y >= height
    
    def test_position_is_valid_invalid_dimensions(self):
        """Position validation handles invalid width/height."""
        pos = Position(5, 5)
        assert pos.is_valid(0, 10) is False
        assert pos.is_valid(10, 0) is False
        assert pos.is_valid(-1, 10) is False
    
    def test_position_is_adjacent_to(self):
        """Position adjacency detection works correctly."""
        center = Position(10, 10)
        
        # Test all 8 adjacent positions
        adjacent_positions = [
            Position(9, 9),   # Top-left
            Position(10, 9),  # Top
            Position(11, 9),  # Top-right
            Position(9, 10),  # Left
            Position(11, 10), # Right
            Position(9, 11),  # Bottom-left
            Position(10, 11), # Bottom
            Position(11, 11), # Bottom-right
        ]
        
        for pos in adjacent_positions:
            assert center.is_adjacent_to(pos) is True
            assert pos.is_adjacent_to(center) is True  # Symmetry
    
    def test_position_is_adjacent_same_position(self):
        """Position is adjacent to itself."""
        pos = Position(10, 10)
        assert pos.is_adjacent_to(pos) is True
    
    def test_position_is_not_adjacent(self):
        """Position correctly identifies non-adjacent positions."""
        center = Position(10, 10)
        
        non_adjacent_positions = [
            Position(8, 8),   # Too far diagonally
            Position(12, 12), # Too far diagonally
            Position(10, 8),  # Too far vertically
            Position(8, 10),  # Too far horizontally
            Position(13, 10), # Too far horizontally
        ]
        
        for pos in non_adjacent_positions:
            assert center.is_adjacent_to(pos) is False
    
    def test_position_is_adjacent_to_none(self):
        """Position adjacency to None returns False."""
        pos = Position(10, 10)
        assert pos.is_adjacent_to(None) is False
    
    def test_position_string_representation(self):
        """Position string representation is correct."""
        pos = Position(15, 20)
        assert str(pos) == "(15,20)"
    
    def test_position_hashable(self):
        """Position can be used as dictionary key."""
        pos1 = Position(10, 10)
        pos2 = Position(10, 10)
        pos3 = Position(11, 10)
        
        # Same coordinates should have same hash
        assert hash(pos1) == hash(pos2)
        # Different coordinates should have different hash
        assert hash(pos1) != hash(pos3)
        
        # Test actual dictionary usage
        position_dict = {pos1: "test_value"}
        assert position_dict[pos2] == "test_value"  # pos2 should find pos1's value
    
    def test_position_create_safe_valid(self):
        """Position.create_safe returns position for valid coordinates."""
        pos = Position.create_safe(5, 8, 10, 10)
        assert pos is not None
        assert pos.x == 5
        assert pos.y == 8
    
    def test_position_create_safe_invalid(self):
        """Position.create_safe returns None for invalid coordinates."""
        # Out of bounds
        pos = Position.create_safe(15, 8, 10, 10)
        assert pos is None
        
        # Negative coordinates
        pos = Position.create_safe(-1, 5, 10, 10)
        assert pos is None
    
    def test_position_from_tuple(self):
        """Position can be created from tuple coordinates."""
        coords = (15, 25)
        pos = Position.from_tuple(coords)
        assert pos.x == 15
        assert pos.y == 25
    
    def test_position_to_tuple(self):
        """Position can be converted to tuple."""
        pos = Position(20, 30)
        coords = pos.to_tuple()
        assert coords == (20, 30)
        assert isinstance(coords, tuple)


class TestColors:
    """Test the Colors class definitions."""
    
    def test_basic_colors_defined(self):
        """Basic colors are properly defined as RGB tuples."""
        assert Colors.WHITE == (255, 255, 255)
        assert Colors.BLACK == (5, 5, 15)
        assert Colors.RED == (220, 20, 60)
        assert Colors.GREEN == (50, 255, 50)
        assert Colors.BLUE == (0, 191, 255)
    
    def test_game_specific_colors(self):
        """Game-specific colors are properly defined."""
        assert Colors.PLAYER == (50, 255, 50)  # Acid green
        assert Colors.GATEWAY == (255, 215, 0)  # Golden
        assert isinstance(Colors.FLOOR, tuple)
        assert isinstance(Colors.WALL, tuple)
        assert isinstance(Colors.SHADOW, tuple)
    
    def test_enemy_colors_defined(self):
        """Enemy state colors are properly defined."""
        assert hasattr(Colors, 'ENEMY_UNAWARE')
        assert isinstance(Colors.ENEMY_UNAWARE, tuple)
        assert len(Colors.ENEMY_UNAWARE) == 3  # RGB tuple
    
    def test_color_values_are_valid_rgb(self):
        """All color values are valid RGB tuples."""
        color_attributes = [attr for attr in dir(Colors) 
                          if not attr.startswith('_') and attr.isupper()]
        
        for attr_name in color_attributes:
            color = getattr(Colors, attr_name)
            assert isinstance(color, tuple), f"{attr_name} should be a tuple"
            assert len(color) == 3, f"{attr_name} should have 3 values (R,G,B)"
            
            for component in color:
                assert isinstance(component, int), f"{attr_name} components should be integers"
                assert 0 <= component <= 255, f"{attr_name} components should be 0-255"


class TestEnums:
    """Test enum definitions are accessible."""
    
    def test_enums_are_accessible(self):
        """Basic enums are accessible from game_entities."""
        # Test that key enums are importable
        assert EnemyState is not None
        assert EnemyMovement is not None
        assert TargetingMode is not None
    
    def test_enemy_state_enum_exists(self):
        """EnemyState enum is available and has expected values."""
        # Test basic enemy states exist
        assert hasattr(EnemyState, 'UNAWARE')
        assert hasattr(EnemyState, 'ALERT')
        # May have additional states like HOSTILE, TRACKING
    
    def test_enemy_movement_enum_exists(self):
        """EnemyMovement enum is available and has expected values."""
        # Test basic movement types exist
        assert hasattr(EnemyMovement, 'RANDOM')
        assert hasattr(EnemyMovement, 'STATIC')
        # May have additional movement types
    
    def test_targeting_mode_enum_exists(self):
        """TargetingMode enum is available."""
        # Test targeting mode exists
        assert TargetingMode is not None
        # May have values like SINGLE, AREA, etc.


class TestPositionIntegration:
    """Integration tests for Position with game scenarios."""
    
    def test_position_adjacency_for_combat(self):
        """Position adjacency works for combat scenarios."""
        # Player and enemy positions for combat testing
        player_pos = Position(10, 10)
        adjacent_enemy = Position(11, 10)  # Right of player
        distant_enemy = Position(15, 15)   # Too far for melee
        
        assert player_pos.is_adjacent_to(adjacent_enemy) is True
        assert player_pos.is_adjacent_to(distant_enemy) is False
    
    def test_position_distance_for_vision_range(self):
        """Position distance works for vision calculations."""
        scanner_pos = Position(5, 5)
        
        # Test positions at different distances
        close_pos = Position(8, 5)  # Distance = 3
        medium_pos = Position(10, 5)  # Distance = 5
        far_pos = Position(15, 15)   # Distance = sqrt(200) ≈ 14.14
        
        assert scanner_pos.distance_to(close_pos) == 3.0
        assert scanner_pos.distance_to(medium_pos) == 5.0
        assert abs(scanner_pos.distance_to(far_pos) - 14.142135623730951) < 0.001
    
    def test_position_bounds_for_map_generation(self):
        """Position validation works for map boundaries."""
        # Test with typical map sizes
        small_map_size = (20, 20)
        large_map_size = (50, 50)
        
        # Valid positions
        valid_small = Position(19, 19)
        valid_large = Position(49, 49)
        
        assert valid_small.is_valid(*small_map_size) is True
        assert valid_large.is_valid(*large_map_size) is True
        
        # Invalid positions
        invalid_pos = Position(20, 20)
        assert invalid_pos.is_valid(*small_map_size) is False
        assert invalid_pos.is_valid(*large_map_size) is True
    
    def test_position_as_dictionary_key(self):
        """Position works as dictionary key for game maps."""
        # Simulate a simple game map using positions as keys
        game_tiles = {}
        
        pos1 = Position(5, 5)
        pos2 = Position(10, 10)
        pos3 = Position(5, 5)  # Same as pos1
        
        game_tiles[pos1] = "wall"
        game_tiles[pos2] = "floor"
        
        # pos3 should find the same entry as pos1
        assert game_tiles[pos3] == "wall"
        assert len(game_tiles) == 2  # Only two unique positions