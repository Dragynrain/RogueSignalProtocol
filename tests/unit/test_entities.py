#!/usr/bin/env python3
"""
Unit tests for game_entities.py - Position class and core data structures.
Tests the foundation classes that all game mechanics depend on.
"""

import pytest
import math
from game_entities import Position, Colors, EnemyState, EnemyMovement, TargetingMode
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition
from game_entities import (
    clamp, safe_divide, validate_coordinates, calculate_manhattan_distance,
    get_adjacent_positions, format_position_key, parse_position_key,
    parse_coordinate_string, validate_position_bounds, ensure_color_tuple
)


class TestPosition:
    """Test Position class functionality."""
    
    def test_position_creation(self):
        """Test basic position creation."""
        pos = Position(5, 10)
        assert pos.x == 5
        assert pos.y == 10
    
    def test_position_creation_edge_cases(self):
        """Test position creation with edge case values."""
        # Zero coordinates
        pos_zero = Position(0, 0)
        assert pos_zero.x == 0 and pos_zero.y == 0
        
        # Negative coordinates (should be allowed for creation)
        pos_neg = Position(-1, -5)
        assert pos_neg.x == -1 and pos_neg.y == -5
        
        # Large coordinates
        pos_large = Position(1000, 2000)
        assert pos_large.x == 1000 and pos_large.y == 2000
    
    @pytest.mark.parametrize("x,y,width,height,expected", [
        (0, 0, 80, 40, True),       # Origin within bounds
        (5, 10, 80, 40, True),      # Normal position within bounds
        (79, 39, 80, 40, True),     # Bottom-right corner (inclusive)
        (-1, 5, 80, 40, False),     # Negative x
        (5, -1, 80, 40, False),     # Negative y
        (80, 20, 80, 40, False),    # x equals width (out of bounds)
        (20, 40, 80, 40, False),    # y equals height (out of bounds)
        (100, 100, 80, 40, False),  # Both coordinates too large
        (5, 10, 0, 40, False),      # Zero width
        (5, 10, 80, 0, False),      # Zero height
        (5, 10, -10, 40, False),    # Negative width
        (5, 10, 80, -10, False),    # Negative height
    ])
    def test_position_validation(self, x, y, width, height, expected):
        """Test position validation with various boundary conditions."""
        pos = Position(x, y)
        assert pos.is_valid(width, height) == expected
    
    def test_distance_calculation(self):
        """Test Euclidean distance calculation."""
        pos1 = Position(0, 0)
        pos2 = Position(3, 4)
        
        # 3-4-5 triangle
        distance = pos1.distance_to(pos2)
        assert abs(distance - 5.0) < 0.001
        
        # Distance to self should be 0
        assert pos1.distance_to(pos1) == 0.0
        
        # Distance should be symmetric
        assert abs(pos1.distance_to(pos2) - pos2.distance_to(pos1)) < 0.001
    
    def test_distance_to_none_raises_error(self):
        """Test that distance calculation to None raises ValueError."""
        pos = Position(5, 5)
        with pytest.raises(ValueError, match="Cannot calculate distance to None position"):
            pos.distance_to(None)
    
    @pytest.mark.parametrize("pos1,pos2,expected", [
        (Position(5, 5), Position(5, 6), True),   # Vertically adjacent
        (Position(5, 5), Position(6, 5), True),   # Horizontally adjacent
        (Position(5, 5), Position(6, 6), True),   # Diagonally adjacent
        (Position(5, 5), Position(4, 4), True),   # Diagonally adjacent
        (Position(5, 5), Position(5, 5), True),   # Same position
        (Position(5, 5), Position(7, 5), False),  # Two spaces apart
        (Position(5, 5), Position(5, 8), False),  # Three spaces apart
        (Position(0, 0), Position(10, 10), False), # Far apart
    ])
    def test_is_adjacent_to(self, pos1, pos2, expected):
        """Test adjacency detection."""
        assert pos1.is_adjacent_to(pos2) == expected
        # Adjacency should be symmetric
        assert pos2.is_adjacent_to(pos1) == expected
    
    def test_is_adjacent_to_none(self):
        """Test adjacency check with None returns False."""
        pos = Position(5, 5)
        assert pos.is_adjacent_to(None) is False
    
    def test_position_equality(self):
        """Test position equality comparison."""
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)
        pos3 = Position(10, 5)
        
        assert pos1 == pos2
        assert pos1 != pos3
        assert pos2 != pos3
        
        # Test equality with non-Position objects
        assert pos1 != (5, 10)
        assert pos1 != "5,10"
        assert pos1 != None
    
    def test_position_hashing(self):
        """Test that Position objects can be used as dictionary keys."""
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)
        pos3 = Position(10, 5)
        
        # Equal positions should have equal hashes
        assert hash(pos1) == hash(pos2)
        
        # Test using positions as dictionary keys
        position_dict = {pos1: "value1", pos3: "value3"}
        assert position_dict[pos2] == "value1"  # pos2 equals pos1
        assert len(position_dict) == 2
    
    def test_position_string_representation(self):
        """Test string representation of Position."""
        pos = Position(5, 10)
        assert str(pos) == "(5,10)"
        
        pos_neg = Position(-3, -7)
        assert str(pos_neg) == "(-3,-7)"
    
    def test_create_safe(self):
        """Test safe position creation."""
        # Valid position
        pos = Position.create_safe(5, 10, 80, 40)
        assert pos is not None
        assert pos.x == 5 and pos.y == 10
        
        # Invalid position
        pos_invalid = Position.create_safe(-1, 10, 80, 40)
        assert pos_invalid is None
        
        pos_invalid2 = Position.create_safe(100, 10, 80, 40)
        assert pos_invalid2 is None
    
    def test_from_tuple(self):
        """Test creating position from tuple."""
        coords = (15, 25)
        pos = Position.from_tuple(coords)
        assert pos.x == 15 and pos.y == 25
    
    def test_to_tuple(self):
        """Test converting position to tuple."""
        pos = Position(15, 25)
        coords = pos.to_tuple()
        assert coords == (15, 25)
        assert isinstance(coords, tuple)


class TestColors:
    """Test Colors class and color utilities."""
    
    def test_color_constants_are_valid_rgb(self):
        """Test that all color constants are valid RGB tuples."""
        color_attributes = [
            'WHITE', 'BLACK', 'RED', 'GREEN', 'BLUE', 'YELLOW', 'CYAN', 'MAGENTA',
            'ORANGE', 'ELECTRIC_PURPLE', 'NEON_PINK', 'ACID_GREEN', 'DARK_GREEN',
            'ELECTRIC_BLUE', 'CYBER_TEAL', 'CRIMSON', 'AZURE', 'EMERALD', 'GOLDEN',
            'VIOLET', 'SILVER', 'FLOOR', 'WALL', 'SHADOW', 'PLAYER', 'GATEWAY'
        ]
        
        for attr_name in color_attributes:
            if hasattr(Colors, attr_name):
                color = getattr(Colors, attr_name)
                assert isinstance(color, tuple), f"{attr_name} should be tuple"
                assert len(color) == 3, f"{attr_name} should have 3 components"
                for component in color:
                    assert isinstance(component, int), f"{attr_name} components should be int"
                    assert 0 <= component <= 255, f"{attr_name} components should be 0-255"
    
    def test_color_interpolation(self):
        """Test color interpolation function."""
        red = (255, 0, 0)
        blue = (0, 0, 255)
        
        # Interpolation at factor 0.0 should return first color
        result = Colors.interpolate_color(red, blue, 0.0)
        assert result == red
        
        # Interpolation at factor 1.0 should return second color
        result = Colors.interpolate_color(red, blue, 1.0)
        assert result == blue
        
        # Interpolation at factor 0.5 should be midpoint
        result = Colors.interpolate_color(red, blue, 0.5)
        assert result == (127, 0, 127)  # Midpoint
        
        # Test factor clamping
        result = Colors.interpolate_color(red, blue, -0.5)
        assert result == red  # Clamped to 0.0
        
        result = Colors.interpolate_color(red, blue, 1.5)
        assert result == blue  # Clamped to 1.0


class TestEnums:
    """Test game enums."""
    
    def test_enemy_state_enum(self):
        """Test EnemyState enum values."""
        assert EnemyState.UNAWARE.value == "unaware"
        assert EnemyState.ALERT.value == "alert"
        assert EnemyState.HOSTILE.value == "hostile"
        
        # Test that all states are different
        states = [EnemyState.UNAWARE, EnemyState.ALERT, EnemyState.HOSTILE]
        assert len(set(states)) == 3
    
    def test_enemy_movement_enum(self):
        """Test EnemyMovement enum values."""
        assert EnemyMovement.STATIC.value == "static"
        assert EnemyMovement.PATROL.value == "patrol"
        assert EnemyMovement.RANDOM.value == "random"
        assert EnemyMovement.SEEK.value == "seek"
        assert EnemyMovement.TRACK.value == "track"
        
        # Test that all movement types are different
        movements = [EnemyMovement.STATIC, EnemyMovement.PATROL, EnemyMovement.RANDOM,
                    EnemyMovement.SEEK, EnemyMovement.TRACK]
        assert len(set(movements)) == 5
    
    def test_targeting_mode_enum(self):
        """Test TargetingMode enum values."""
        assert TargetingMode.NONE.value == "none"
        assert TargetingMode.SINGLE.value == "single"
        assert TargetingMode.AREA.value == "area"
        assert TargetingMode.DIRECTION.value == "direction"


class TestDataClassDefinitions:
    """Test dataclass definitions for game objects."""
    
    def test_enemy_type_definition(self):
        """Test EnemyTypeDefinition dataclass."""
        enemy_def = EnemyTypeDefinition(
            symbol="S",
            cpu=30,
            vision=8,
            movement="patrol",
            name="Scanner",
            damage=15
        )
        
        assert enemy_def.symbol == "S"
        assert enemy_def.cpu == 30
        assert enemy_def.vision == 8
        assert enemy_def.movement == "patrol"
        assert enemy_def.name == "Scanner"
        assert enemy_def.damage == 15
    
    def test_exploit_definition(self):
        """Test ExploitDefinition dataclass."""
        exploit_def = ExploitDefinition(
            name="code_injection",
            ram=2,
            heat=25,
            range=6,
            category="offensive",
            damage=20,
            targeting="single",
            description="Test exploit"
        )
        
        assert exploit_def.name == "code_injection"
        assert exploit_def.ram == 2
        assert exploit_def.heat == 25
        assert exploit_def.range == 6
        assert exploit_def.category == "offensive"
        assert exploit_def.damage == 20
        assert exploit_def.targeting == "single"
        assert exploit_def.description == "Test exploit"
    
    def test_upgrade_definition(self):
        """Test UpgradeDefinition dataclass."""
        upgrade_def = UpgradeDefinition(
            name="CPU Cooler",
            symbol="+",
            color=(0, 255, 255),
            stat_type="heat_efficiency",
            bonus_amount=10,
            description="Test upgrade"
        )
        
        assert upgrade_def.name == "CPU Cooler"
        assert upgrade_def.symbol == "+"
        assert upgrade_def.color == (0, 255, 255)
        assert upgrade_def.stat_type == "heat_efficiency"
        assert upgrade_def.bonus_amount == 10
        assert upgrade_def.description == "Test upgrade"


class TestUtilityFunctions:
    """Test utility functions in game_entities.py."""
    
    @pytest.mark.parametrize("value,min_val,max_val,expected", [
        (5, 0, 10, 5),      # Value within range
        (-5, 0, 10, 0),     # Value below minimum
        (15, 0, 10, 10),    # Value above maximum
        (0, 0, 10, 0),      # Value at minimum
        (10, 0, 10, 10),    # Value at maximum
        (5.5, 0.0, 10.0, 5.5),  # Float values
    ])
    def test_clamp(self, value, min_val, max_val, expected):
        """Test value clamping function."""
        result = clamp(value, min_val, max_val)
        assert result == expected
    
    @pytest.mark.parametrize("numerator,denominator,default,expected", [
        (10, 2, 0, 5),      # Normal division
        (10, 0, 99, 99),    # Division by zero returns default
        (0, 5, 99, 0),      # Zero numerator
        (10, -2, 0, -5),    # Negative denominator
        (-10, 2, 0, -5),    # Negative numerator
    ])
    def test_safe_divide(self, numerator, denominator, default, expected):
        """Test safe division function."""
        result = safe_divide(numerator, denominator, default)
        assert result == expected
    
    @pytest.mark.parametrize("x,y,width,height,expected", [
        (5, 10, 80, 40, True),      # Valid coordinates
        (0, 0, 80, 40, True),       # Origin
        (79, 39, 80, 40, True),     # Bottom-right corner
        (-1, 10, 80, 40, False),    # Negative x
        (10, -1, 80, 40, False),    # Negative y
        (80, 20, 80, 40, False),    # x equals width
        (20, 40, 80, 40, False),    # y equals height
    ])
    def test_validate_coordinates(self, x, y, width, height, expected):
        """Test coordinate validation function."""
        result = validate_coordinates(x, y, width, height)
        assert result == expected
    
    @pytest.mark.parametrize("pos1,pos2,expected_distance", [
        (Position(0, 0), Position(3, 4), 7),      # 3+4 = 7
        (Position(5, 5), Position(5, 5), 0),      # Same position
        (Position(0, 0), Position(1, 1), 2),      # 1+1 = 2
        (Position(10, 5), Position(7, 9), 7),     # |10-7| + |5-9| = 3+4 = 7
    ])
    def test_calculate_manhattan_distance(self, pos1, pos2, expected_distance):
        """Test Manhattan distance calculation."""
        result = calculate_manhattan_distance(pos1, pos2)
        assert result == expected_distance
    
    def test_get_adjacent_positions(self):
        """Test getting adjacent positions."""
        center = Position(5, 5)
        adjacent = get_adjacent_positions(center, 80, 40)
        
        # Should have 8 adjacent positions for a center position
        assert len(adjacent) == 8
        
        # Check all positions are actually adjacent
        for pos in adjacent:
            assert center.is_adjacent_to(pos)
            assert pos != center  # Should not include center itself
        
        # Test corner position (fewer adjacent positions)
        corner = Position(0, 0)
        adjacent_corner = get_adjacent_positions(corner, 80, 40)
        assert len(adjacent_corner) == 3  # Only 3 valid adjacent positions at corner
    
    def test_format_and_parse_position_key(self):
        """Test position key formatting and parsing."""
        pos = Position(15, 25)
        
        # Format to key
        key = format_position_key(pos)
        assert key == "15,25"
        
        # Parse back from key
        parsed_pos = parse_position_key(key)
        assert parsed_pos == pos
    
    def test_parse_position_key_invalid(self):
        """Test parsing invalid position keys."""
        invalid_keys = ["", "15", "a,b", "15,", ",25", "15,25,30"]
        
        for invalid_key in invalid_keys:
            result = parse_position_key(invalid_key)
            assert result is None
    
    @pytest.mark.parametrize("coord_str,expected", [
        ("10,20", Position(10, 20)),
        ("0,0", Position(0, 0)),
        (" 5 , 15 ", Position(5, 15)),  # With spaces
        ("100,200", Position(100, 200)),
        ("5", None),                     # Invalid format
        ("a,b", None),                   # Non-numeric
        ("", None),                      # Empty string
        ("5,", None),                    # Missing y
        (",10", None),                   # Missing x
    ])
    def test_parse_coordinate_string(self, coord_str, expected):
        """Test coordinate string parsing."""
        result = parse_coordinate_string(coord_str)
        assert result == expected
    
    def test_validate_position_bounds(self):
        """Test position bounds validation."""
        pos_valid = Position(10, 15)
        pos_invalid = Position(100, 200)
        
        assert validate_position_bounds(pos_valid, 80, 40) is True
        assert validate_position_bounds(pos_invalid, 80, 40) is False
    
    @pytest.mark.parametrize("color_input,expected", [
        ("WHITE", Colors.WHITE),
        ("RED", Colors.RED),
        ((255, 128, 0), (255, 128, 0)),         # Tuple input
        ([100, 200, 50], (100, 200, 50)),       # List input
        ("INVALID_COLOR", Colors.WHITE),         # Invalid string -> default
        (None, Colors.WHITE),                    # None -> default
        (123, Colors.WHITE),                     # Invalid type -> default
    ])
    def test_ensure_color_tuple(self, color_input, expected):
        """Test color tuple validation and conversion."""
        result = ensure_color_tuple(color_input)
        assert result == expected
        assert isinstance(result, tuple)
        assert len(result) == 3