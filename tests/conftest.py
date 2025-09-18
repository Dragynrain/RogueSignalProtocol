#!/usr/bin/env python3
"""
pytest configuration and common fixtures for RogueSignalProtocol testing.
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add the project root to Python path so we can import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_entities import Position, EnemyState, EnemyMovement, TargetingMode
from game_entities import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition


@pytest.fixture
def sample_position():
    """Provide a basic Position for testing."""
    return Position(5, 10)


@pytest.fixture
def map_dimensions():
    """Standard map dimensions for testing."""
    return {"width": 80, "height": 40}


@pytest.fixture
def edge_positions(map_dimensions):
    """Positions at map boundaries for edge case testing."""
    width, height = map_dimensions["width"], map_dimensions["height"]
    return {
        "origin": Position(0, 0),
        "top_right": Position(width-1, 0),
        "bottom_left": Position(0, height-1),
        "bottom_right": Position(width-1, height-1),
        "center": Position(width//2, height//2)
    }


@pytest.fixture
def invalid_positions():
    """Invalid positions for boundary testing."""
    return [
        Position(-1, 0),
        Position(0, -1),
        Position(-5, -5),
        Position(100, 50),  # Beyond standard map
        Position(50, 100)   # Beyond standard map
    ]


@pytest.fixture
def sample_enemy_definition():
    """Basic enemy type definition for testing."""
    return EnemyTypeDefinition(
        symbol="S",
        cpu=30,
        vision=8,
        movement="patrol", 
        name="Scanner",
        damage=15
    )


@pytest.fixture
def sample_exploit_definition():
    """Basic exploit definition for testing."""
    return ExploitDefinition(
        name="code_injection",
        ram=2,
        heat=25,
        range=6,
        category="offensive",
        damage=20,
        targeting="single",
        description="Inject malicious code into target system"
    )


@pytest.fixture
def sample_upgrade_definition():
    """Basic upgrade definition for testing."""
    return UpgradeDefinition(
        name="CPU Cooler",
        symbol="+",
        color=(0, 255, 255),
        stat_type="heat_efficiency", 
        bonus_amount=10,
        description="Reduces heat generation"
    )


@pytest.fixture
def position_pairs():
    """Pairs of positions for distance and adjacency testing."""
    return [
        (Position(0, 0), Position(3, 4)),  # Distance 5
        (Position(5, 5), Position(5, 6)),  # Adjacent vertically
        (Position(5, 5), Position(6, 5)),  # Adjacent horizontally
        (Position(5, 5), Position(6, 6)),  # Adjacent diagonally
        (Position(0, 0), Position(10, 10)), # Far apart
    ]


@pytest.fixture
def coordinate_test_data():
    """Test data for coordinate parsing and validation."""
    return {
        "valid_strings": ["5,10", "0,0", "25,30", " 10 , 20 "],
        "invalid_strings": ["5", "a,b", "5,", ",10", "5,10,15", ""]
    }


# Test helper functions
def assert_position_equal(pos1: Position, pos2: Position, message: str = ""):
    """Helper to assert two positions are equal with helpful error message."""
    assert pos1.x == pos2.x and pos1.y == pos2.y, f"Positions not equal: {pos1} != {pos2}. {message}"


def assert_valid_rgb_color(color_tuple):
    """Helper to assert a color tuple is valid RGB."""
    assert isinstance(color_tuple, tuple), f"Color must be tuple, got {type(color_tuple)}"
    assert len(color_tuple) == 3, f"Color must have 3 components, got {len(color_tuple)}"
    for component in color_tuple:
        assert isinstance(component, int), f"Color component must be int, got {type(component)}"
        assert 0 <= component <= 255, f"Color component must be 0-255, got {component}"