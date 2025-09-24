#!/usr/bin/env python3
"""
Simple unit tests for Level functionality.
Focus on core game mechanics only.
"""

import pytest
from unittest.mock import Mock

# Import what we can test directly
from game_entities import Position


def test_position_creation():
    """Position creates with correct coordinates."""
    pos = Position(10, 15)
    
    assert pos.x == 10
    assert pos.y == 15


def test_position_equality():
    """Position equality works correctly."""
    pos1 = Position(5, 10)
    pos2 = Position(5, 10)
    pos3 = Position(6, 10)
    
    assert pos1 == pos2
    assert pos1 != pos3


def test_position_boundaries():
    """Position handles boundary values."""
    # Zero position
    pos_zero = Position(0, 0)
    assert pos_zero.x == 0
    assert pos_zero.y == 0
    
    # Negative position
    pos_neg = Position(-5, -10)
    assert pos_neg.x == -5
    assert pos_neg.y == -10


def test_level_coordinates():
    """Basic coordinate system works."""
    # Test that we can create positions across a typical level
    positions = []
    for x in range(0, 80):
        for y in range(0, 40):
            pos = Position(x, y)
            positions.append(pos)
            assert pos.x == x
            assert pos.y == y
    
    # Should have created positions for entire level
    assert len(positions) == 80 * 40


def test_position_distance():
    """Position distance calculation works if available."""
    pos1 = Position(0, 0)
    pos2 = Position(3, 4)
    
    # If distance method exists, test it
    if hasattr(pos1, 'distance_to'):
        distance = pos1.distance_to(pos2)
        assert distance == 5  # 3-4-5 triangle
    
    # Basic coordinate distance
    dx = abs(pos2.x - pos1.x)
    dy = abs(pos2.y - pos1.y)
    assert dx == 3
    assert dy == 4