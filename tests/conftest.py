#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for RogueSignalProtocol testing.

This file provides commonly-used fixtures for all tests. Import additional
specialized fixtures from tests.fixtures.standard_patterns as needed.
"""

import pytest
import sys
import os

# Add the project root to Python path so we can import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_entities import Position
from game_characters import Player, Enemy
from game_config import GameSettings
from game_engine import GameEngine
from game_map import GameMap
from tests.fixtures.real_game_data import create_real_enemy, create_test_map_with_real_tiles
from tests.fixtures.simple_fixtures import player, enemy, create_test_map
from tests.fixtures.standard_patterns import (
    create_basic_game_environment,
    create_combat_scenario,
    create_stealth_scenario,
    create_multi_enemy_scenario,
)


# ===== Basic Entity Fixtures =====

@pytest.fixture
def sample_position():
    """Provide a basic Position for testing."""
    return Position(5, 10)


@pytest.fixture
def test_player():
    """Create a test player with real game data."""
    return player(10, 10, 100)


@pytest.fixture
def test_enemy():
    """Create a test enemy with real game data."""
    return enemy("scanner", 15, 15)


@pytest.fixture
def test_map():
    """Create a test map with real tile data."""
    return create_test_map(30, 30)


# ===== Dimension & Position Fixtures =====

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


# ===== Game Engine Fixtures =====

@pytest.fixture
def basic_game_engine():
    """Create a basic game engine for testing.

    Returns GameEngine with:
    - Real Player at (15, 15)
    - Real GameMap (30x30)
    - Mocked sound_manager (external dependency)
    - Volume set to 0 (no audio in tests)
    """
    return create_basic_game_environment()


@pytest.fixture
def combat_game_engine():
    """Create game engine with combat scenario.

    Returns GameEngine with:
    - Player at (15, 15) with full resources
    - One enemy at (17, 15) in UNAWARE state
    - Clear line of sight
    """
    return create_combat_scenario()


@pytest.fixture
def stealth_game_engine():
    """Create game engine with stealth scenario.

    Returns GameEngine with:
    - Player in shadow zone
    - Enemy watching from light
    - Ghost node nearby
    """
    return create_stealth_scenario()


@pytest.fixture
def multi_enemy_engine():
    """Create game engine with multiple enemies.

    Returns GameEngine with:
    - Player at (15, 15)
    - 3 enemies scattered around map
    - Mix of enemy types and states
    """
    return create_multi_enemy_scenario()


# ===== Settings Fixtures =====

@pytest.fixture
def silent_settings():
    """Create GameSettings with audio disabled for testing."""
    settings = GameSettings()
    settings.master_volume = 0.0
    settings.sfx_volume = 0.0
    settings.music_volume = 0.0
    settings.graphics_mode = "glyph"
    return settings