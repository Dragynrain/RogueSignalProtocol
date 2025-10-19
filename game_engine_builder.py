#!/usr/bin/env python3
"""
Game Engine Builder
Simplifies GameEngine initialization with a fluent builder pattern.
"""

from typing import Optional

from game_config import GameSettings, GameConfig
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_level import LevelGenerator
from game_enemies import EnemyManager
from game_combat import ExploitSystem
from game_input import InputHandler
from game_audio import SoundManager


class GameEngineBuilder:
    """
    Builder pattern for GameEngine initialization.

    Simplifies the complex initialization process by providing:
    1. Sensible defaults for all dependencies
    2. Fluent API for optional customization
    3. Clear initialization order

    Example:
        # Simple new game
        game = GameEngineBuilder().build()

        # New game with custom settings
        game = GameEngineBuilder().with_settings(my_settings).build()

        # Load from save
        game = GameEngineBuilder().load_from_save().build()
    """

    def __init__(self):
        """Initialize builder with None for all optional components."""
        # Core dependencies
        self._settings: Optional[GameSettings] = None
        self._game_state_manager: Optional[GameStateManager] = None
        self._game_map: Optional[GameMap] = None
        self._level_generator: Optional[LevelGenerator] = None
        self._enemy_manager: Optional[EnemyManager] = None
        self._exploit_system: Optional[ExploitSystem] = None
        self._input_handler: Optional[InputHandler] = None
        self._sound_manager: Optional[SoundManager] = None

        # Build options
        self._load_save: bool = False

    def with_settings(self, settings: GameSettings) -> 'GameEngineBuilder':
        """
        Set custom game settings.

        Args:
            settings: GameSettings instance

        Returns:
            Self for method chaining
        """
        self._settings = settings
        return self

    def with_game_state_manager(self, manager: GameStateManager) -> 'GameEngineBuilder':
        """Set custom game state manager (usually for testing)."""
        self._game_state_manager = manager
        return self

    def with_game_map(self, game_map: GameMap) -> 'GameEngineBuilder':
        """Set custom game map (usually for testing)."""
        self._game_map = game_map
        return self

    def with_level_generator(self, generator: LevelGenerator) -> 'GameEngineBuilder':
        """Set custom level generator (usually for testing)."""
        self._level_generator = generator
        return self

    def with_enemy_manager(self, manager: EnemyManager) -> 'GameEngineBuilder':
        """Set custom enemy manager (usually for testing)."""
        self._enemy_manager = manager
        return self

    def with_exploit_system(self, system: ExploitSystem) -> 'GameEngineBuilder':
        """Set custom exploit system (usually for testing)."""
        self._exploit_system = system
        return self

    def with_input_handler(self, handler: InputHandler) -> 'GameEngineBuilder':
        """Set custom input handler (usually for testing)."""
        self._input_handler = handler
        return self

    def with_sound_manager(self, manager: SoundManager) -> 'GameEngineBuilder':
        """Set custom sound manager (usually for testing)."""
        self._sound_manager = manager
        return self

    def load_from_save(self) -> 'GameEngineBuilder':
        """
        Configure builder to load game from save file.

        Returns:
            Self for method chaining
        """
        self._load_save = True
        return self

    def build(self) -> 'GameEngine':
        """
        Build and return the GameEngine instance.

        Returns:
            Fully initialized GameEngine
        """
        # Import here to avoid circular dependency
        from game_engine import GameEngine

        return GameEngine(
            game_state_manager=self._game_state_manager,
            game_map=self._game_map,
            level_generator=self._level_generator,
            enemy_manager=self._enemy_manager,
            exploit_system=self._exploit_system,
            input_handler=self._input_handler,
            sound_manager=self._sound_manager,
            load_save=self._load_save,
            settings=self._settings
        )
