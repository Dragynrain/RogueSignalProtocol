#!/usr/bin/env python3
"""
Simple pytest configuration for RogueSignalProtocol testing.
Focus on core game mechanics only.
"""

import pytest
import sys
import os

# Add the project root to Python path so we can import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_entities import Position
from game_characters import Player, Enemy


@pytest.fixture
def sample_position():
    """Provide a basic Position for testing."""
    return Position(5, 10)


@pytest.fixture
def test_player():
    """Create a test player."""
    return Player(10, 10)


@pytest.fixture  
def test_enemy():
    """Create a test enemy."""
    return Enemy(15, 15, "scanner")


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