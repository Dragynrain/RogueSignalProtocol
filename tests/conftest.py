#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for RogueSignalProtocol testing.

This file provides commonly-used fixtures for all tests. Import additional
specialized fixtures from tests.fixtures.standard_patterns as needed.

## Fixture Usage Guide

### Game Engine Fixtures (Most Common)

For most tests, use one of these pre-configured game engine fixtures:

- **basic_game_engine**: Minimal game setup with player, empty map, no enemies
  - Use for: Basic gameplay tests, simple scenarios
  - Example: `def test_player_movement(basic_game_engine):`

- **combat_game_engine**: Combat scenario with player + 1 enemy
  - Use for: Combat tests, exploit tests, targeting tests
  - Example: `def test_exploit_damage(combat_game_engine):`

- **stealth_game_engine**: Stealth scenario with shadows and ghost nodes
  - Use for: Stealth tests, blind spot tests, detection tests
  - Example: `def test_shadow_detection(stealth_game_engine):`

- **multi_enemy_engine**: Multiple enemies in different states
  - Use for: Enemy coordination, alert system, area exploits
  - Example: `def test_enemy_alerts(multi_enemy_engine):`

### Entity Fixtures

- **test_player**: Basic player at (10, 10) with 100 CPU
- **test_enemy**: Basic scanner enemy at (15, 15)
- **test_map**: 30x30 test map with real tile data

### Achievement & Rendering Fixtures

- **clean_achievement_state**: Resets achievement manager state (use for achievement tests)
- **test_console**: Standard 80x50 TCOD console (use for rendering tests)

### Settings Fixtures

- **silent_settings**: GameSettings with all audio disabled (prevents audio spam in tests)

### Advanced Fixtures

For complex scenarios, import from tests.fixtures.standard_patterns:
- create_basic_game_environment()
- create_combat_scenario()
- create_stealth_scenario()
- create_multi_enemy_scenario()

See tests/fixtures/standard_patterns.py for details on each fixture.
"""

import os
import random
import sys
from unittest.mock import patch

import pytest

# Add project root and src directory to Python path for rsp package imports
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'src'))

from rsp.core.config import GameSettings
from rsp.entities.base import Position
from tests.fixtures.simple_fixtures import create_test_map, enemy, player
from tests.fixtures.standard_patterns import (
    create_basic_game_environment,
    create_combat_scenario,
    create_multi_enemy_scenario,
    create_stealth_scenario,
)

# ===== Platform Mocking for Cross-Platform Tests =====


@pytest.fixture
def mock_linux_platform(monkeypatch):
    """Mock sys.platform to simulate Linux environment.

    Usage:
        def test_linux_paths(mock_linux_platform):
            # sys.platform is now 'linux'
            assert is_linux() is True
    """
    monkeypatch.setattr(sys, "platform", "linux")


@pytest.fixture
def mock_windows_platform(monkeypatch):
    """Mock sys.platform to simulate Windows environment.

    Usage:
        def test_windows_paths(mock_windows_platform):
            # sys.platform is now 'win32'
            assert is_windows() is True
    """
    monkeypatch.setattr(sys, "platform", "win32")


@pytest.fixture
def mock_macos_platform(monkeypatch):
    """Mock sys.platform to simulate macOS environment.

    Usage:
        def test_macos_paths(mock_macos_platform):
            # sys.platform is now 'darwin'
            assert is_macos() is True
    """
    monkeypatch.setattr(sys, "platform", "darwin")


# ===== Time Mocking for Reliable Tests =====


class MockTime:
    """
    Mock time.time() for reliable testing of time-dependent behavior.

    Instead of using time.sleep() (which is flaky in CI), use this to:
    1. Control what time.time() returns
    2. Advance time instantly without actually waiting

    Usage:
        def test_settling_period(mock_time):
            analog.get_movement()  # Uses initial time
            mock_time.advance(0.035)  # Advance past settling period
            analog.get_movement()  # Now sees time has passed
    """

    def __init__(self, start_time: float = 1000.0):
        self._current_time = start_time

    def time(self) -> float:
        """Return the current mocked time."""
        return self._current_time

    def advance(self, seconds: float) -> float:
        """Advance the mocked time by the given number of seconds."""
        self._current_time += seconds
        return self._current_time

    def set(self, timestamp: float) -> None:
        """Set the mocked time to a specific value."""
        self._current_time = timestamp


@pytest.fixture
def mock_time():
    """
    Pytest fixture for mocking time.time().

    Replaces time.sleep()-based tests with instant, reliable time control.

    Usage:
        def test_auto_repeat(mock_time):
            handler.handle_button(press_event)  # At t=1000.0
            mock_time.advance(0.4)  # Advance to t=1000.4 (past initial delay)
            handler.poll_repeat()  # Should now trigger repeat
    """
    mock = MockTime()
    with patch("time.time", mock.time):
        yield mock


# ===== Test Infrastructure Fixtures =====


@pytest.fixture(scope="session")
def worker_id(request):
    """Get the xdist worker ID for parallel test isolation.

    Returns 'master' for non-parallel runs, or worker ID (gw0, gw1, etc.) for parallel.
    """
    if hasattr(request.config, "workerinput"):
        return request.config.workerinput["workerid"]
    return "master"


@pytest.fixture(scope="session")
def isolated_data_dir(tmp_path_factory, worker_id):
    """Create isolated data directory for each test worker.

    This prevents parallel test workers from competing for the same files:
    - saves/
    - logs/
    - metrics/
    - debug_exports/

    Each worker gets its own temporary directory hierarchy.
    """
    base_temp = tmp_path_factory.mktemp(f"rogue_signal_{worker_id}")

    # Create subdirectories that the game expects
    (base_temp / "saves").mkdir(exist_ok=True)
    (base_temp / "logs").mkdir(exist_ok=True)
    (base_temp / "metrics").mkdir(exist_ok=True)
    (base_temp / "debug_exports").mkdir(exist_ok=True)

    return base_temp


@pytest.fixture(scope="function", autouse=True)
def global_file_isolation(request, isolated_data_dir, monkeypatch):
    """Global autouse fixture that isolates ALL file operations for every test.

    Patches get_data_directory() to return a per-worker isolated directory.
    This automatically isolates:
    - SaveGameManager (uses get_data_directory() / "saves")
    - DebugExporter (uses get_data_directory() / "debug_exports")
    - MetricsManager (uses get_data_directory() / "metrics")
    - Logging (uses get_data_directory() / "logs")

    Scope: function (every test gets a fresh patch)
    Applied: automatically to all tests (except those marked with skip_file_isolation)
    """
    # Skip isolation for tests that specifically test file path initialization
    if "skip_file_isolation" in request.keywords:
        return

    import rsp.core.file_paths as game_file_paths

    # Patch the main entry point for all file paths
    monkeypatch.setattr(game_file_paths, "get_data_directory", lambda: isolated_data_dir)

    # Also ensure the module-level cache is set
    monkeypatch.setattr(game_file_paths, "_data_directory", isolated_data_dir)
    monkeypatch.setattr(game_file_paths, "_is_portable_mode", True)


@pytest.fixture(scope="session", autouse=True)
def initialize_file_paths():
    """
    Initialize file path system for all tests (parallel-safe).

    This prevents "get_data_directory() called before initialize_data_directories()"
    errors throughout the test suite.

    Scope: session (initialized once per worker in parallel mode)
    Note: Individual tests use tmp_path/monkeypatch for isolation
    """
    import rsp.core.file_paths as game_file_paths

    # Initialize paths for test environment (will use portable mode in cwd)
    # Each worker process gets its own initialization
    try:
        game_file_paths.initialize_data_directories()
    except RuntimeError:
        pass  # Already initialized in this worker

    yield

    # No cleanup needed


@pytest.fixture(scope="session", autouse=True)
def load_game_config_once():
    """
    Load game configuration once per test session.

    This optimization prevents reloading JSON files for every test,
    providing ~30-50% speedup on the full test suite.

    Scope: session (loads once for entire pytest run)
    Safety: GameConfig and GameBalance are read-only during tests
    """
    from rsp.core.config import GameBalance, GameConfig

    # Load config once for all tests
    GameConfig.load_from_json()
    GameBalance.load_from_json()

    yield

    # No cleanup needed - data remains loaded


@pytest.fixture(autouse=True)
def isolate_config_state():
    """
    Isolate GameConfig state between tests to prevent cache pollution.

    Some tests mock or modify GameConfig._config_data, which pollutes the cache
    for subsequent tests. This fixture ensures every test starts with fresh config.

    Strategy:
    - Clear ONLY GameConfig._config_data (the polluted cache)
    - Immediately reload GameConfig and GameBalance (they're coupled)
    - Leave DataLoader alone (independent, loads from different JSON file)

    This prevents test pollution without breaking DataLoader-dependent tests.
    """
    yield

    # After each test, reset GameConfig to clean state
    from rsp.core.config import GameBalance, GameConfig

    # Clear only GameConfig cache (not DataLoader - it's independent)
    GameConfig._config_data = None

    # Immediately reload so next test has fresh, clean config
    try:
        GameConfig.load_from_json()
        GameBalance.load_from_json()
    except Exception:
        pass  # Ignore errors during cleanup (some tests intentionally break config)


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

    # Get current test name for deterministic per-test seeding
    test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown")
    test_hash = int(hashlib.md5(test_name.encode()).hexdigest()[:8], 16)

    # Seed with test-specific value for determinism
    random.seed(test_hash)

    # Reset TCOD RNG with same test-specific seed
    try:
        from rsp.level.structure import seed_rng

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
        "top_right": Position(width - 1, 0),
        "bottom_left": Position(0, height - 1),
        "bottom_right": Position(width - 1, height - 1),
        "center": Position(width // 2, height // 2),
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


# ===== Achievement Test Fixtures =====


@pytest.fixture
def clean_achievement_state():
    """Reset achievement manager state before and after tests.

    Use this fixture when testing achievements to ensure test isolation.
    Clears both unlocked achievements and pending popups.
    """
    from rsp.systems.achievements import AchievementManager

    # Clear state before test
    AchievementManager.reset()

    yield

    # Clean up after test
    AchievementManager.reset()


# ===== Rendering Test Fixtures =====


@pytest.fixture
def test_console():
    """Create a test console for rendering tests.

    Returns a standard 80x50 TCOD console for testing rendering code.
    """
    import tcod.console

    return tcod.console.Console(80, 50)


@pytest.fixture(scope="session")
def real_game_data():
    """Fixture that ensures game data is loaded (for testing data-dependent logic)."""
    # GameData loads automatically on import, but this fixture
    # makes the dependency explicit for tests
    from rsp.core.data import GameData, GameUpgrades

    GameUpgrades._ensure_loaded()
    return GameData


@pytest.fixture
def basic_map(test_map):
    """Alias for test_map fixture (for backward compatibility)."""
    return test_map


# ===== Gamepad Test Fixtures =====

# Settling period for analog stick (30ms in implementation, use 35ms for safety)
SETTLING_PERIOD_SEC = 0.035


def get_movement_with_settling(analog, game_or_turn, x, y, mock_time, settling_sec=None):
    """
    Get movement after waiting for the settling period.

    The analog handler has a 30ms settling period before locking direction.
    This helper sets the stick position, waits, and then gets the movement.

    Args:
        analog: The AnalogStickHandler instance
        game_or_turn: Either GameEngine instance (uses .turn) or turn number directly
        x, y: Stick coordinates to set
        mock_time: MockTime instance for advancing time (required for reliable tests)
        settling_sec: How long to wait for settling (default SETTLING_PERIOD_SEC)

    Returns:
        The movement tuple (dx, dy) or None
    """
    if settling_sec is None:
        settling_sec = SETTLING_PERIOD_SEC

    # Handle both game object and raw turn number
    turn = game_or_turn.turn if hasattr(game_or_turn, "turn") else game_or_turn

    # Set the stick position
    analog.update_left_stick(x=x, y=y)

    # First call starts the settling timer
    analog.get_left_stick_movement_gameplay(turn)

    # Advance mock time past settling period
    mock_time.advance(settling_sec)

    # Now get the actual movement (should have direction locked)
    return analog.get_left_stick_movement_gameplay(turn)


@pytest.fixture
def game_with_gamepad():
    """Create game instance with mock gamepad for gamepad input tests.

    Returns (game, input_handler, mock_controller) tuple.
    Use for testing gamepad input handling, analog stick behavior, etc.
    """
    from unittest.mock import Mock

    from rsp.systems.audio import NullSoundManager
    from rsp.core.engine import GameEngine
    from rsp.input.handler import InputHandler

    settings = GameSettings()
    settings.graphics_mode = "text"
    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)

    # Mock controller
    mock_controller = Mock()
    mock_controller.name = "Test Controller"
    mock_controller.instance_id = 0
    controllers = {mock_controller}

    # Create input handler with controllers
    input_handler = InputHandler(game, renderer=None, controllers=controllers)

    # Clear starting dialogue
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.dialogue_history = []

    return game, input_handler, mock_controller


# ===== Audio Test Configuration =====


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--audio",
        action="store_true",
        default=False,
        help="Run audio tests that play real music/sound effects",
    )
    parser.addoption(
        "--full",
        action="store_true",
        default=False,
        help="Run full test suite including audio tests",
    )


def pytest_configure(config):
    """Configure pytest based on command line options."""
    config.addinivalue_line("markers", "audio: Tests that play real audio (skip by default)")
    config.addinivalue_line("markers", "linux_only: mark test to run only on Linux")
    config.addinivalue_line("markers", "windows_only: mark test to run only on Windows")
    config.addinivalue_line("markers", "cross_platform: mark test that must pass on all platforms")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on markers and command line options."""
    # Skip audio tests unless --audio or --full flags are provided
    skip_audio = None
    if not (config.getoption("--audio") or config.getoption("--full")):
        skip_audio = pytest.mark.skip(reason="Audio test skipped (use --audio or --full to run)")

    # Platform-specific test skipping
    skip_windows = None
    skip_linux = None

    if sys.platform != "win32":
        skip_windows = pytest.mark.skip(
            reason=f"Windows-only test (current platform: {sys.platform})"
        )
    if not sys.platform.startswith("linux"):
        skip_linux = pytest.mark.skip(reason=f"Linux-only test (current platform: {sys.platform})")

    for item in items:
        # Audio test skipping
        if skip_audio and "audio" in item.keywords:
            item.add_marker(skip_audio)

        # Platform-specific test skipping
        if skip_windows and "windows_only" in item.keywords:
            item.add_marker(skip_windows)
        if skip_linux and "linux_only" in item.keywords:
            item.add_marker(skip_linux)


# ===== Deterministic Test Agent Fixtures =====
# These fixtures guarantee specific test conditions exist,
# eliminating non-deterministic pytest.skip() calls.


@pytest.fixture
def agent_with_walkable_adjacent():
    """
    Create a GameTestAgent with guaranteed walkable tile adjacent to player.

    This fixture ensures there's at least one direction the player can move,
    eliminating the need for runtime pytest.skip() when testing movement.

    The fixture will clear a wall adjacent to the player if all directions
    are blocked.
    """
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=42)

    # Check if player has any walkable adjacent tile
    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W
    has_walkable = False

    for dx, dy in directions:
        adj_x = agent.player.x + dx
        adj_y = agent.player.y + dy
        if (adj_x, adj_y) not in agent.game_map.walls:
            if 0 <= adj_x < agent.game_map.width and 0 <= adj_y < agent.game_map.height:
                has_walkable = True
                break

    # If no walkable adjacent, clear the tile to the east
    if not has_walkable:
        east_x = agent.player.x + 1
        east_y = agent.player.y
        agent.game_map.walls.discard((east_x, east_y))

    return agent


@pytest.fixture
def agent_with_guaranteed_enemy():
    """
    Create a GameTestAgent with at least one enemy present.

    This fixture spawns an enemy if none exist, eliminating the need for
    runtime pytest.skip() when testing enemy-related functionality.

    Returns:
        GameTestAgent with at least one enemy
    """
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=42)

    # Spawn enemy if none exist
    if len(agent.enemies) == 0:
        # Place enemy 3 tiles east of player (safe distance)
        enemy_x = agent.player.x + 3
        enemy_y = agent.player.y
        # Ensure position is walkable
        agent.game_map.walls.discard((enemy_x, enemy_y))
        agent.spawn_enemy("bot", enemy_x, enemy_y)

    return agent


@pytest.fixture
def agent_with_guaranteed_gateway():
    """
    Create a GameTestAgent with a gateway present on the level.

    This fixture places a gateway if none exists, eliminating the need for
    runtime pytest.skip() when testing gateway/progression functionality.

    The gateway is placed in a walkable position far from the player.

    Returns:
        GameTestAgent with gateway present (agent.game_map.gateway is not None)
    """
    from rsp.entities.base import Position
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=42)

    # Place gateway if none exists
    if agent.game_map.gateway is None:
        # Place gateway in opposite corner from player (far away)
        # Use lower-right area of map
        gateway_x = agent.game_map.width - 10
        gateway_y = agent.game_map.height - 10
        # Ensure position is walkable
        agent.game_map.walls.discard((gateway_x, gateway_y))
        agent.game_map.gateway = Position(gateway_x, gateway_y)

    return agent


@pytest.fixture
def agent_with_valid_movement_position():
    """
    Create a GameTestAgent with player at a position that has valid adjacent moves.

    This fixture relocates the player if necessary to ensure at least one
    adjacent tile allows movement, eliminating runtime pytest.skip() calls.

    Returns:
        Tuple of (agent, original_position) where original_position is guaranteed
        to have at least one valid adjacent move.
    """
    from rsp.entities.base import Position
    from tests.test_agent import GameTestAgent

    agent = GameTestAgent(seed=42)

    directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W

    # Check if current position has valid adjacent moves
    def has_valid_adjacent(pos):
        for dx, dy in directions:
            adj_x = pos.x + dx
            adj_y = pos.y + dy
            adj_pos = Position(adj_x, adj_y)
            if agent.game_map.is_valid_position(adj_pos):
                return True
        return False

    original_position = Position(agent.player.x, agent.player.y)

    if has_valid_adjacent(original_position):
        return agent, original_position

    # Try alternative positions
    test_positions = [
        Position(15, 15),
        Position(20, 20),
        Position(10, 10),
        Position(25, 25),
    ]

    for test_pos in test_positions:
        if agent.game_map.is_valid_position(test_pos) and has_valid_adjacent(test_pos):
            agent.player.position = test_pos
            return agent, test_pos

    # Last resort: clear walls around player's current position
    agent.player.position = original_position
    clear_x = original_position.x + 1
    clear_y = original_position.y
    agent.game_map.walls.discard((clear_x, clear_y))

    return agent, original_position
