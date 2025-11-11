#!/usr/bin/env python3
"""
Game session coordinator managing turn processing, level generation, and save/load.

This module provides a thin coordination layer that delegates to specialized managers:
- GameTurnManager: Turn processing and enemy AI
- GameLevelCoordinator: Level generation and progression
- GameStatePersistence: Save/load operations

By delegating to these focused managers, we improve modularity, maintainability,
and adherence to single responsibility principle.

Key responsibilities:
- Coordinate between turn, level, and persistence systems
- Provide unified API for game engine
- Maintain backward compatibility with existing code
"""

from game_turn_manager import GameTurnManager
from game_level_coordinator import GameLevelCoordinator
from game_state_persistence import GameStatePersistence


class GameSession:
    """
    Coordinates game sessions by delegating to specialized managers.

    This thin wrapper maintains the public API while delegating actual work
    to GameTurnManager, GameLevelCoordinator, and GameStatePersistence.
    This design improves modularity and makes each component easier to
    understand and maintain.

    Key methods:
    - process_turn(): Delegates to GameTurnManager
    - generate_procedural_level(): Delegates to GameLevelCoordinator
    - progress_to_next_level(): Delegates to GameLevelCoordinator
    - load_from_save(): Delegates to GameStatePersistence

    Attributes:
        game_engine: GameEngine instance for accessing all game systems
        turn_manager: Handles turn processing and enemy AI
        level_coordinator: Handles level generation and progression
        persistence: Handles save/load operations
    """

    def __init__(self, game_engine):
        """
        Initialize session coordinator with game engine reference.

        Args:
            game_engine: GameEngine instance providing access to all game systems
        """
        self.game_engine = game_engine

        # Initialize specialized managers
        self.turn_manager = GameTurnManager(game_engine)
        self.level_coordinator = GameLevelCoordinator(game_engine)
        self.persistence = GameStatePersistence(game_engine)

    # ========================================================================
    # PUBLIC API - Turn Processing
    # ========================================================================

    def process_turn(self):
        """
        Process one complete game turn in structured phases.

        Delegates to GameTurnManager for all turn processing logic.
        """
        self.turn_manager.process_turn()

    # ========================================================================
    # PUBLIC API - Level Generation and Progression
    # ========================================================================

    def generate_procedural_level(self):
        """
        Generate a complete level with map structure and gameplay elements.

        Delegates to GameLevelCoordinator for all level generation logic.
        """
        self.level_coordinator.generate_procedural_level()

    def progress_to_next_level(self):
        """
        Progress to next level or trigger victory if all levels complete.

        Delegates to GameLevelCoordinator for level progression logic.
        """
        self.level_coordinator.progress_to_next_level()

    # ========================================================================
    # PUBLIC API - Save/Load Operations
    # ========================================================================

    def load_from_save(self) -> bool:
        """
        Load and restore complete game state from save file.

        Delegates to GameStatePersistence for all save/load logic.

        Returns:
            True if load successful, False if no save file or error
        """
        return self.persistence.load_from_save()

    # ========================================================================
    # DELEGATION METHODS - For backward compatibility
    # ========================================================================
    # These private methods are accessed by game_engine.py and tests
    # We delegate to the appropriate manager to maintain compatibility

    def _update_enemies(self):
        """Delegate to GameTurnManager._update_enemies()"""
        self.turn_manager._update_enemies()

    def _process_special_tiles(self):
        """Delegate to GameTurnManager._process_special_tiles()"""
        self.turn_manager._process_special_tiles()

    def _update_all_enemy_awareness(self):
        """Delegate to GameTurnManager._update_all_enemy_awareness()"""
        self.turn_manager._update_all_enemy_awareness()

    def _alert_nearby_enemies(self, enemy):
        """Delegate to GameTurnManager._alert_nearby_enemies()"""
        self.turn_manager._alert_nearby_enemies(enemy)
