#!/usr/bin/env python3
"""
Property-based tests for Position and coordinate system.
Uses Hypothesis to generate test data and verify invariants.
"""

import pytest
from hypothesis import given, strategies as st, assume, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant

from game_entities import Position, validate_coordinates, calculate_manhattan_distance
from game_entities import get_adjacent_positions, validate_position_bounds


# Custom strategies for game-specific data
positions = st.builds(
    Position,
    x=st.integers(min_value=-100, max_value=200),
    y=st.integers(min_value=-100, max_value=200)
)

valid_map_positions = st.builds(
    Position,
    x=st.integers(min_value=0, max_value=79),
    y=st.integers(min_value=0, max_value=39)
)

map_dimensions = st.tuples(
    st.integers(min_value=1, max_value=200),  # width
    st.integers(min_value=1, max_value=200)   # height
)


class TestPositionProperties:
    """Property-based tests for Position class."""
    
    @given(st.integers(), st.integers())
    def test_position_creation_always_succeeds(self, x, y):
        """Position creation should never fail with any integers."""
        pos = Position(x, y)
        assert pos.x == x
        assert pos.y == y
    
    @given(positions)
    def test_position_equality_reflexive(self, pos):
        """Position should always equal itself."""
        assert pos == pos
    
    @given(positions, positions)
    def test_position_equality_symmetric(self, pos1, pos2):
        """If pos1 == pos2, then pos2 == pos1."""
        if pos1 == pos2:
            assert pos2 == pos1
    
    @given(positions, positions, positions)
    def test_position_equality_transitive(self, pos1, pos2, pos3):
        """If pos1 == pos2 and pos2 == pos3, then pos1 == pos3."""
        if pos1 == pos2 and pos2 == pos3:
            assert pos1 == pos3
    
    @given(positions)
    def test_position_hash_consistent(self, pos):
        """Position hash should be consistent across calls."""
        hash1 = hash(pos)
        hash2 = hash(pos)
        assert hash1 == hash2
    
    @given(positions, positions)
    def test_equal_positions_same_hash(self, pos1, pos2):
        """Equal positions should have the same hash."""
        if pos1 == pos2:
            assert hash(pos1) == hash(pos2)


class TestCoordinateValidation:
    """Property-based tests for coordinate validation functions."""
    
    @given(st.integers(min_value=0), st.integers(min_value=0), map_dimensions)
    def test_valid_coordinates_accepted(self, x, y, dimensions):
        """Valid coordinates within bounds should be accepted."""
        width, height = dimensions
        assume(x < width and y < height)
        
        result = validate_coordinates(x, y, width, height)
        assert result is True
    
    @given(st.integers(), st.integers(), map_dimensions)
    def test_invalid_coordinates_rejected(self, x, y, dimensions):
        """Invalid coordinates should be rejected."""
        width, height = dimensions
        assume(x < 0 or y < 0 or x >= width or y >= height)
        
        result = validate_coordinates(x, y, width, height)
        assert result is False
    
    @given(valid_map_positions, map_dimensions)
    def test_position_bounds_validation(self, pos, dimensions):
        """Position bounds validation should be consistent."""
        width, height = dimensions
        assume(pos.x < width and pos.y < height and pos.x >= 0 and pos.y >= 0)
        
        result = validate_position_bounds(pos, width, height)
        assert result is True


class TestManhattanDistance:
    """Property-based tests for Manhattan distance calculation."""
    
    @given(positions)
    def test_distance_to_self_is_zero(self, pos):
        """Distance from a position to itself should be 0."""
        distance = calculate_manhattan_distance(pos, pos)
        assert distance == 0
    
    @given(positions, positions)
    def test_distance_symmetric(self, pos1, pos2):
        """Distance should be symmetric: d(A,B) = d(B,A)."""
        dist1 = calculate_manhattan_distance(pos1, pos2)
        dist2 = calculate_manhattan_distance(pos2, pos1)
        assert dist1 == dist2
    
    @given(positions, positions, positions)
    def test_triangle_inequality(self, pos1, pos2, pos3):
        """Triangle inequality: d(A,C) <= d(A,B) + d(B,C)."""
        dist_ac = calculate_manhattan_distance(pos1, pos3)
        dist_ab = calculate_manhattan_distance(pos1, pos2)
        dist_bc = calculate_manhattan_distance(pos2, pos3)
        
        assert dist_ac <= dist_ab + dist_bc
    
    @given(positions)
    def test_distance_always_non_negative(self, pos1):
        """Distance should always be non-negative."""
        # Test with a known position
        pos2 = Position(0, 0)
        distance = calculate_manhattan_distance(pos1, pos2)
        assert distance >= 0
    
    @given(st.integers(), st.integers())
    @example(0, 0)
    @example(1, 1)
    @example(-5, 3)
    def test_distance_calculation_correct(self, dx, dy):
        """Manhattan distance calculation should be correct."""
        pos1 = Position(0, 0)
        pos2 = Position(dx, dy)
        
        expected = abs(dx) + abs(dy)
        actual = calculate_manhattan_distance(pos1, pos2)
        
        assert actual == expected


class TestAdjacentPositions:
    """Property-based tests for adjacent position generation."""
    
    @given(positions)
    def test_adjacent_positions_count(self, pos):
        """Should always return exactly 4 adjacent positions."""
        adjacent = get_adjacent_positions(pos)
        assert len(adjacent) == 4
    
    @given(positions)
    def test_adjacent_positions_distance_one(self, pos):
        """All adjacent positions should be exactly distance 1 away."""
        adjacent = get_adjacent_positions(pos)
        
        for adj_pos in adjacent:
            distance = calculate_manhattan_distance(pos, adj_pos)
            assert distance == 1
    
    @given(positions)
    def test_adjacent_positions_unique(self, pos):
        """All adjacent positions should be unique."""
        adjacent = get_adjacent_positions(pos)
        assert len(set(adjacent)) == len(adjacent)
    
    @given(positions)
    def test_adjacent_positions_correct_offsets(self, pos):
        """Adjacent positions should have correct coordinate offsets."""
        adjacent = get_adjacent_positions(pos)
        
        expected_offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        actual_offsets = [(adj.x - pos.x, adj.y - pos.y) for adj in adjacent]
        
        assert set(actual_offsets) == set(expected_offsets)


class PositionStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for position operations."""
    
    def __init__(self):
        super().__init__()
        self.positions = set()
        self.max_positions = 100
    
    @rule(pos=positions)
    def add_position(self, pos):
        """Add a position to our set."""
        assume(len(self.positions) < self.max_positions)
        self.positions.add(pos)
    
    @rule()
    def clear_positions(self):
        """Clear all positions."""
        self.positions.clear()
    
    @invariant()
    def positions_are_valid(self):
        """All stored positions should be valid Position objects."""
        for pos in self.positions:
            assert isinstance(pos, Position)
            assert isinstance(pos.x, int)
            assert isinstance(pos.y, int)
    
    @invariant()
    def position_set_size_reasonable(self):
        """Position set should not exceed maximum size."""
        assert len(self.positions) <= self.max_positions


# Test the state machine
TestPositionStateMachine = PositionStateMachine.TestCase


class TestGameBoundaryProperties:
    """Property-based tests for game boundary conditions."""
    
    @given(
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=1, max_value=1000)
    )
    def test_map_boundaries_consistent(self, width, height):
        """Map boundary validation should be consistent."""
        # Corner positions
        corners = [
            Position(0, 0),           # Top-left
            Position(width-1, 0),     # Top-right
            Position(0, height-1),    # Bottom-left
            Position(width-1, height-1)  # Bottom-right
        ]
        
        for corner in corners:
            assert validate_position_bounds(corner, width, height) is True
        
        # Out-of-bounds positions
        invalid = [
            Position(-1, 0),
            Position(0, -1),
            Position(width, 0),
            Position(0, height)
        ]
        
        for invalid_pos in invalid:
            assert validate_position_bounds(invalid_pos, width, height) is False
    
    @given(valid_map_positions)
    def test_adjacent_positions_may_be_invalid(self, pos):
        """Adjacent positions may go out of standard map bounds."""
        # Standard map dimensions
        width, height = 80, 40
        
        adjacent = get_adjacent_positions(pos)
        
        # At least some adjacent positions should be valid if pos is not on edge
        valid_adjacent = [
            adj for adj in adjacent 
            if validate_position_bounds(adj, width, height)
        ]
        
        # If position is not on the edge, should have some valid adjacent positions
        if 0 < pos.x < width-1 and 0 < pos.y < height-1:
            assert len(valid_adjacent) == 4  # All should be valid
        elif pos.x == 0 or pos.x == width-1 or pos.y == 0 or pos.y == height-1:
            assert len(valid_adjacent) < 4   # Some should be invalid


# Performance property tests
class TestPerformanceProperties:
    """Property-based tests for performance characteristics."""
    
    @given(st.lists(positions, min_size=1, max_size=1000))
    def test_distance_calculation_scales_linearly(self, position_list):
        """Distance calculations should scale reasonably with input size."""
        import time
        
        start_time = time.time()
        
        # Calculate distances between all pairs
        for i, pos1 in enumerate(position_list):
            for pos2 in position_list[i+1:]:
                calculate_manhattan_distance(pos1, pos2)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete within reasonable time even for large inputs
        # Allowing 1 second for 1000 positions (up to 499,500 calculations)
        max_time = len(position_list) * 0.001  # Very generous timing
        assert elapsed < max_time