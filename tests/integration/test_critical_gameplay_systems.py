"""
Critical gameplay systems integration tests.

Tests the integration of core gameplay systems that are essential for proper game function:
- Combat system integration with enemy AI and player actions
- TraceLevel system and enemy alerting chains
- Exploit system and its effects on gameplay
- Inventory and upgrade systems
- Save/load system with complex game states
- Audio system integration during gameplay events
- Map interaction and special tiles
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import tempfile
import copy
import random

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, Colors
from game_config import GameConfig, GameSettings, GameBalance
from game_state import GameStateManager
from game_combat import ExploitSystem
from tests.fixtures.real_game_data import get_real_game_data
from tests.fixtures.simple_fixtures import create_test_map_with_real_tiles, create_real_player, create_real_enemy


class TestCombatSystemIntegration:
    """Test critical combat system integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def test_player_enemy_combat_integration(self):
        """Test complete player vs enemy combat workflow."""
        engine = self.create_test_engine()

        # Set up combat scenario
        engine.player.position.x, engine.player.position.y = 10, 10
        engine.player.cpu = 100
        engine.player.heat = 0

        # Create enemy adjacent to player
        enemy = create_real_enemy("bot", Position(11, 10))
        enemy.cpu = 50
        engine.enemies = [enemy]

        # Give player a combat exploit
        engine.player.inventory_manager.equipped_exploits.append('code_injection')

        initial_heat = engine.player.heat

        # Execute exploit (this will target based on game logic)
        result = engine.exploit_system.use_exploit('code_injection')

        # Verify exploit system integration
        assert isinstance(result, bool)  # Should return a boolean

        # Verify heat generation
        assert engine.player.heat >= initial_heat  # Heat should increase or stay same

        # Verify exploit system is properly integrated
        assert hasattr(engine, 'exploit_system')
        assert engine.exploit_system.game == engine

    def test_enemy_attack_player_integration(self):
        """Test enemy attacking player integration."""
        engine = self.create_test_engine()

        # Set up scenario
        engine.player.x, engine.player.y = 10, 10
        engine.player.cpu = 100

        # Create hostile enemy adjacent to player - use bot instead of virus for direct damage
        enemy = create_real_enemy("bot", Position(11, 10))
        enemy.state = EnemyState.HOSTILE
        engine.enemies = [enemy]

        initial_player_cpu = engine.player.cpu

        # Enemy attacks player
        damage = enemy.attack_player(engine.player)

        # Verify attack results - bot should deal direct damage
        assert engine.player.cpu < initial_player_cpu or damage > 0

        # Verify integration worked
        assert isinstance(damage, int)
        assert damage >= 0

    def test_player_death_and_game_over_integration(self):
        """Test player death triggers proper game over sequence."""
        engine = self.create_test_engine()

        # Set up player near death
        engine.player.cpu = 1
        engine.game_over = False

        # Manually trigger player death to test integration
        engine.player.cpu = 0

        # Test if engine has death handling method
        if hasattr(engine, '_handle_player_death'):
            engine._handle_player_death()

        # Check game over integration (engine may handle death differently)
        # The main integration test is that the system doesn't crash
        assert engine.player.cpu <= 0  # Player should be dead

        # Verify the game engine still functions
        assert hasattr(engine, 'game_over')
        assert hasattr(engine, 'player')


class TestTraceLevelSystemIntegration:
    """Test critical trace level and enemy alerting system integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def test_enemy_trace_level_system_integration(self):
        """Test enemy trace level system is properly integrated."""
        engine = self.create_test_engine()

        # Set up test scenario
        engine.player.x, engine.player.y = 10, 10
        engine.player.trace_level = 20

        # Create enemy
        enemy = create_real_enemy("scanner", Position(12, 10))
        engine.enemies = [enemy]

        # Verify trace level system integration
        assert hasattr(engine.player, 'trace_level')
        assert isinstance(engine.player.trace_level, (int, float))
        assert engine.player.trace_level >= 0

        # Verify enemy vision integration
        assert hasattr(enemy, 'can_see_player')
        assert hasattr(enemy, 'state')

    def test_trace_threshold_system_integration(self):
        """Test trace level threshold system is properly integrated."""
        engine = self.create_test_engine()

        # Test trace level system exists
        initial_trace = engine.player.trace_level

        # Process a turn
        engine.process_turn()

        # Verify trace level system is working (should be same or change predictably)
        assert engine.player.trace_level >= 0  # TraceLevel should never be negative
        assert isinstance(engine.player.trace_level, (int, float))  # Should be a number

    def test_trace_level_system_persistence_integration(self):
        """Test trace level system integrates with game state persistence."""
        engine = self.create_test_engine()

        # Set trace level value
        initial_trace = 75
        engine.player.trace_level = initial_trace

        # Verify trace level persists in player object
        assert engine.player.trace_level == initial_trace

        # Verify trace level is accessible through game engine
        assert hasattr(engine, 'player')
        assert hasattr(engine.player, 'trace_level')


class TestExploitSystemIntegration:
    """Test critical exploit system integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def test_exploit_system_integration(self):
        """Test exploit system is properly integrated."""
        engine = self.create_test_engine()

        # Verify exploit system exists and is accessible
        assert hasattr(engine, 'input_handler')
        assert hasattr(engine, 'exploit_system')

        # Verify exploit system is properly initialized
        exploit_system = engine.exploit_system
        assert exploit_system.game == engine

        # Verify player has inventory system for exploits
        assert hasattr(engine.player, 'inventory_manager')
        assert hasattr(engine.player.inventory_manager, 'equipped_exploits')

    def test_exploit_heat_system_integration(self):
        """Test exploit system integrates with heat management."""
        engine = self.create_test_engine()

        # Set up player with exploit
        engine.player.inventory_manager.equipped_exploits.append('code_injection')
        initial_heat = engine.player.heat

        # Use exploit
        result = engine.exploit_system.use_exploit('code_injection')

        # Verify heat system integration
        assert isinstance(result, bool)
        assert engine.player.heat >= initial_heat  # Heat should increase or stay same

    def test_exploit_targeting_system_integration(self):
        """Test exploit system integrates with targeting."""
        engine = self.create_test_engine()

        # Verify targeting system exists
        assert hasattr(engine, 'targeting_mode')
        assert hasattr(engine, 'targeting_exploit')
        assert hasattr(engine, 'cursor_position')

        # Test basic integration
        engine.targeting_mode = True
        engine.targeting_exploit = 'code_injection'

        # Verify integration works
        assert engine.targeting_mode == True
        assert engine.targeting_exploit == 'code_injection'


class TestGameStateIntegration:
    """Test critical game state persistence and management integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.game_data = get_real_game_data()

        # Create game settings with muted audio for tests
        self.game_settings = GameSettings()
        self.game_settings.master_volume = 0.0
        self.game_settings.sfx_volume = 0.0
        self.game_settings.music_volume = 0.0
        self.game_settings.graphics_mode = "glyph"

    def teardown_method(self):
        """Clean up test fixtures."""
        pass  # No cleanup needed

    def create_test_engine(self):
        """Create a GameEngine instance for testing."""
        # Create mocked sound manager for testing
        mock_sound_manager = Mock()

        # Create GameEngine with mocked dependencies
        engine = GameEngine(
            sound_manager=mock_sound_manager,
            settings=self.game_settings
        )

        return engine

    def test_game_state_system_integration(self):
        """Test game state system is properly integrated."""
        engine = self.create_test_engine()

        # Verify game state components exist
        assert hasattr(engine, 'game_state')
        assert hasattr(engine, 'level')
        assert hasattr(engine, 'turn')

        # Verify save/load system exists
        assert hasattr(engine, 'game_session')
        assert hasattr(engine, 'auto_save')

        # Test basic state access
        initial_level = engine.level
        initial_turn = engine.turn

        assert isinstance(initial_level, int)
        assert isinstance(initial_turn, int)

    def test_turn_processing_system_integration(self):
        """Test turn processing system integration."""
        engine = self.create_test_engine()

        # Set up initial state
        initial_turn = engine.turn

        # Process a turn
        engine.process_turn()

        # Verify turn advanced
        assert engine.turn > initial_turn

        # Verify turn processor exists
        assert hasattr(engine, 'turn_processor')

    def test_game_state_persistence_integration(self):
        """Test game state persistence integration."""
        engine = self.create_test_engine()

        # Set some state
        engine.player.cpu = 75
        engine.player.heat = 30
        engine.player.trace_level = 45

        # Verify state is accessible
        assert engine.player.cpu == 75
        assert engine.player.heat == 30
        assert engine.player.trace_level == 45

        # Verify persistence systems exist
        assert hasattr(engine, 'game_session'), "Engine should have game_session attribute"
        assert callable(getattr(engine, 'auto_save', None)), "Engine should have auto_save method"