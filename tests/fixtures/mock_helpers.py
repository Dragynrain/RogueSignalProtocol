#!/usr/bin/env python3
"""
Mock helpers for tests.
Provides standardized mock setups to reduce test failures from refactoring.
"""

import numpy as np
from unittest.mock import Mock, MagicMock
from game_characters import Player
from game_entities import Position


def create_mock_game_map(width=80, height=40):
    """Create a properly configured mock GameMap."""
    mock_game_map = Mock()
    mock_game_map.width = width
    mock_game_map.height = height
    mock_game_map.is_valid_position = Mock(return_value=True)
    mock_game_map.is_wall = Mock(return_value=False)
    mock_game_map.is_shadow = Mock(return_value=False)

    # Set up all the map attributes that the game expects
    mock_game_map.code_hacks = {}  # Empty dict for code hacks
    mock_game_map.data_nodes = set()  # Empty set for data nodes
    mock_game_map.gateways = set()  # Empty set for gateways
    mock_game_map.exploit_pickups = {}  # Empty dict for exploit pickups
    mock_game_map.story_fragments = {}  # Empty dict for story fragments
    mock_game_map.permanent_upgrades = {}  # Empty dict for permanent upgrades
    mock_game_map.explored_tiles = set()  # Empty set for explored tiles
    mock_game_map.last_known_enemy_positions = {}  # Empty dict for enemy positions

    # Mock transparency map for FOV calculations
    transparency_map = np.ones((height, width), dtype=bool)  # All tiles transparent
    mock_game_map._get_transparency_map = Mock(return_value=transparency_map)

    return mock_game_map


def create_mock_game_state():
    """Create a properly configured mock GameStateManager."""
    mock_game_state = Mock()
    mock_game_state.level = 1
    mock_game_state.turn = 0
    mock_game_state.game_over = False
    mock_game_state.admin_spawned = False
    mock_game_state.threat_scan_turns = 0
    mock_game_state.noise_locations = []
    mock_game_state.distraction_points = {}
    mock_game_state.revealed_special_nodes = {}  # Dict for revealed nodes
    return mock_game_state


def create_test_player(x=10, y=10):
    """Create a player with properly initialized temporary effects."""
    player = Player(x, y)

    # Ensure all expected temporary effects are present
    player.temporary_effects = {
        'speed_boost_turns': 0,
        'movement_slowed_turns': 0,
        'enhanced_vision_turns': 0,
        'exploit_efficiency_turns': 0,
        'data_mimic_turns': 0,
        'virus_turns': 0,
        'stealth': 0,  # Some tests expect this
        'overclock': 0,  # Some tests expect this
        'speed': 0  # Some tests expect this
    }

    # Initialize other attributes that tests might expect
    player.speed_moves_remaining = 0

    return player


def create_mock_sound_manager():
    """Create a mock SoundManager."""
    mock_sound = Mock()
    mock_sound.play_sound = Mock()
    mock_sound.preload_sounds = Mock()
    return mock_sound


def create_mock_message_log():
    """Create a mock MessageLog."""
    mock_log = Mock()
    mock_log.add_message = Mock()
    mock_log.add_message_typed = Mock()
    mock_log.messages = []
    return mock_log


def setup_game_engine_mocks(game_engine):
    """Set up an existing GameEngine with proper mocks for testing."""
    # Replace the game_map with a proper mock
    game_engine.game_map = create_mock_game_map()

    # Replace game_state with a proper mock
    game_engine.game_state = create_mock_game_state()

    # Set up other mocks
    game_engine.message_log = create_mock_message_log()
    game_engine.sound_manager = create_mock_sound_manager()

    # Ensure player has proper temporary effects
    if hasattr(game_engine, 'player'):
        player = game_engine.player
        if not hasattr(player.temporary_effects, 'get') or 'speed_boost_turns' not in player.temporary_effects:
            player.temporary_effects = {
                'speed_boost_turns': 0,
                'movement_slowed_turns': 0,
                'enhanced_vision_turns': 0,
                'exploit_efficiency_turns': 0,
                'data_mimic_turns': 0,
                'virus_turns': 0,
                'stealth': 0,
                'overclock': 0,
                'speed': 0
            }

        if not hasattr(player, 'speed_moves_remaining'):
            player.speed_moves_remaining = 0

    # Add missing methods that tests expect (for backward compatibility)
    if not hasattr(game_engine, '_process_player_turn'):
        game_engine._process_player_turn = Mock()
    if not hasattr(game_engine, '_process_enemy_turn'):
        game_engine._process_enemy_turn = Mock()
    if not hasattr(game_engine, '_process_player_temporary_effects'):
        game_engine._process_player_temporary_effects = Mock()
    if not hasattr(game_engine, '_process_environmental_effects'):
        game_engine._process_environmental_effects = Mock()

    return game_engine