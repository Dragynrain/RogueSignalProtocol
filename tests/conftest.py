#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for RogueSignalProtocol testing.

This file provides commonly-used fixtures for all tests. Import additional
specialized fixtures from tests.fixtures.standard_patterns as needed.
"""

import pytest
import sys
import os
import random

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


# ===== Test Infrastructure Fixtures =====

@pytest.fixture(scope="session", autouse=True)
def load_game_config_once():
    """
    Load game configuration once per test session.

    This optimization prevents reloading JSON files for every test,
    providing ~30-50% speedup on the full test suite.

    Scope: session (loads once for entire pytest run)
    Safety: GameConfig and GameBalance are read-only during tests
    """
    from game_config import GameConfig, GameBalance

    # Load config once for all tests
    GameConfig.load_from_json()
    GameBalance.load_from_json()

    yield

    # No cleanup needed - data remains loaded


@pytest.fixture(autouse=True)
def isolate_random_state():
    """
    Isolate random state between tests to prevent flaky failures.

    This fixture ensures that tests don't pollute the global random state,
    which can cause non-deterministic behavior when tests run in different orders.

    Strategy:
    1. Save current Python random state before test
    2. Set a fresh seed based on test name (deterministic but unique per test)
    3. Restore original state after test
    4. Crucially: Remove the random.seed() call at end of generate_procedural_level()

    This approach ensures:
    - Test isolation: Each test starts with its own clean random state
    - Determinism: Same test always gets same random sequence
    - No forced seed: Tests can use whatever seed makes sense for them
    """
    # Save current Python random state
    saved_state = random.getstate()

    # Import here to avoid circular dependencies
    import hashlib
    import pytest

    # Get current test name for deterministic per-test seeding
    test_name = os.environ.get('PYTEST_CURRENT_TEST', 'unknown')
    test_hash = int(hashlib.md5(test_name.encode()).hexdigest()[:8], 16)

    # Seed with test-specific value for determinism
    random.seed(test_hash)

    # Reset TCOD RNG with same test-specific seed
    try:
        from game_level_structure import seed_rng
        seed_rng(test_hash)
    except ImportError:
        pass

    yield

    # Restore original Python random state
    random.setstate(saved_state)


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