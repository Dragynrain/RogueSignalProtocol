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

# Import mock factories for testing
from tests.fixtures.mock_factories import (
    MockPlayerFactory, MockEnemyFactory, MockGameMapFactory, 
    MockGameFactory, MockInventoryFactory, MockExploitFactory,
    MockSystemFactory, MockTestScenarios
)


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


# Mock factory fixtures for easy access in tests
@pytest.fixture
def mock_player():
    """Create a basic mock player."""
    return MockPlayerFactory.create_basic_player()


@pytest.fixture
def mock_damaged_player():
    """Create a mock player with reduced CPU."""
    return MockPlayerFactory.create_damaged_player(cpu=50)


@pytest.fixture
def mock_invisible_player():
    """Create a mock player with invisibility."""
    return MockPlayerFactory.create_invisible_player()


@pytest.fixture
def mock_enhanced_vision_player():
    """Create a mock player with enhanced vision."""
    return MockPlayerFactory.create_enhanced_vision_player()


@pytest.fixture
def mock_scanner_enemy():
    """Create a basic mock scanner enemy."""
    return MockEnemyFactory.create_basic_enemy('scanner')


@pytest.fixture
def mock_hostile_hunter():
    """Create a hostile hunter enemy."""
    return MockEnemyFactory.create_hostile_enemy('hunter')


@pytest.fixture
def mock_disabled_enemy():
    """Create a disabled enemy."""
    return MockEnemyFactory.create_disabled_enemy('bot', disabled_turns=3)


@pytest.fixture
def mock_admin_enemy():
    """Create an admin boss enemy."""
    return MockEnemyFactory.create_admin_enemy()


@pytest.fixture
def mock_game_map():
    """Create a basic mock game map."""
    return MockGameMapFactory.create_basic_map()


@pytest.fixture
def mock_map_with_shadows():
    """Create a mock game map with shadow zones."""
    return MockGameMapFactory.create_map_with_shadows()


@pytest.fixture
def mock_map_with_obstacles():
    """Create a mock game map with obstacles."""
    return MockGameMapFactory.create_map_with_obstacles()


@pytest.fixture
def mock_game():
    """Create a basic mock game."""
    return MockGameFactory.create_basic_game()


@pytest.fixture
def mock_game_with_enemies():
    """Create a mock game with various enemies."""
    return MockGameFactory.create_game_with_enemies(['scanner', 'patrol', 'hunter'])


@pytest.fixture
def mock_inventory():
    """Create a basic mock inventory manager."""
    return MockInventoryFactory.create_basic_inventory_manager()


@pytest.fixture
def mock_inventory_with_exploits():
    """Create a mock inventory with exploits."""
    return MockInventoryFactory.create_inventory_with_exploits(['code_injection', 'data_mimic'])


@pytest.fixture
def mock_sound_manager():
    """Create a mock sound manager."""
    return MockSystemFactory.create_mock_sound_manager()


@pytest.fixture
def mock_message_log():
    """Create a mock message log."""
    return MockSystemFactory.create_mock_message_log()


@pytest.fixture
def mock_game_state():
    """Create a mock game state."""
    return MockSystemFactory.create_mock_game_state()


# Test scenario fixtures
@pytest.fixture
def combat_scenario():
    """Create a combat test scenario."""
    return MockTestScenarios.combat_scenario()


@pytest.fixture
def stealth_scenario():
    """Create a stealth test scenario."""
    return MockTestScenarios.stealth_scenario()


@pytest.fixture
def boss_scenario():
    """Create a boss fight test scenario."""
    return MockTestScenarios.boss_scenario()


@pytest.fixture
def exploration_scenario():
    """Create an exploration test scenario."""
    return MockTestScenarios.exploration_scenario()


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


def assert_enemy_state_transition(enemy, from_state: EnemyState, to_state: EnemyState, message: str = ""):
    """Helper to assert enemy state transitions."""
    assert enemy.state == to_state, f"Enemy state transition failed: expected {to_state}, got {enemy.state}. {message}"


def assert_position_within_range(pos1: Position, pos2: Position, max_range: float, message: str = ""):
    """Helper to assert positions are within specified range."""
    distance = pos1.distance_to(pos2)
    assert distance <= max_range, f"Position {pos1} not within range {max_range} of {pos2} (distance: {distance:.2f}). {message}"


def assert_exploit_heat_cost(exploit_def, expected_cost: int, efficiency_bonus: bool = False):
    """Helper to assert exploit heat costs."""
    multiplier = 0.6 if efficiency_bonus else 1.0
    expected = int(exploit_def.heat * multiplier)
    assert expected == expected_cost, f"Heat cost mismatch: expected {expected_cost}, calculated {expected}"