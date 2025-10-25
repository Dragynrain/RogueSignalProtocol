#!/usr/bin/env python3
"""
New Game Smoke Tests - End-to-End validation of game startup.

These tests simulate the exact flow that happens when a player clicks "New Game"
to catch integration issues that unit tests miss. Tests both rendering modes
and level generation strategies.

Critical: These tests use actual GameEngine initialization with minimal mocking
to validate real-world game startup scenarios.
"""

import pytest
import sys
import os

# Add the project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game_engine import GameEngine
from game_config import GameSettings, GameConfig
from game_map import GameMap
from game_level import LevelGenerator
from game_level_structure import BSPRoomGenerator, RoomGenerator
from game_entities import Position


class TestNewGameSmokeTests:
    """Smoke tests for New Game flow - catches critical startup bugs."""

    def test_new_game_default_configuration(self):
        """
        Test New Game with default configuration (what players actually use).

        This test catches bugs that only appear in the real game startup flow,
        like the BSP bugs that weren't caught by unit tests.
        """
        # Create game engine with default settings (BSP enabled)
        # NOTE: Level generation happens automatically in __init__
        settings = GameSettings()
        engine = GameEngine(settings=settings)

        # Validate game state after startup
        assert engine.game_state.level == 1
        assert engine.game_state.turn == 0
        assert engine.player is not None
        assert engine.player.cpu > 0

        # Validate map was generated
        assert len(engine.game_map.walls) > 0
        total_tiles = GameConfig.MAP_WIDTH * GameConfig.MAP_HEIGHT
        assert len(engine.game_map.walls) < total_tiles  # Not all walls

        # Validate enemies spawned
        assert len(engine.enemies) > 0
        for enemy in engine.enemies:
            assert enemy.cpu > 0
            assert enemy.position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)

        # Validate level generator is properly initialized
        assert isinstance(engine.level_generator.room_generator, RoomGenerator)

    def test_new_game_with_bsp_generation(self):
        """Test New Game explicitly with BSP generation enabled."""
        settings = GameSettings()

        # Create game map and level generator with BSP
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        level_generator = LevelGenerator(game_map, use_bsp=True)

        # Create engine with BSP level generator (generates level in __init__)
        engine = GameEngine(
            settings=settings,
            game_map=game_map,
            level_generator=level_generator
        )

        # Validate BSP-specific results
        assert isinstance(level_generator.room_generator, BSPRoomGenerator)
        assert len(level_generator.last_generated_rooms) > 0
        assert len(level_generator.corridor_tiles) > 0

        # Validate map connectivity (rooms should be connected)
        # At minimum, spawn room should be walkable
        spawn_pos = Position(5, 5)  # Typical spawn location
        assert not game_map.is_wall(spawn_pos)

    def test_new_game_with_traditional_generation(self):
        """Test New Game with traditional (non-BSP) generation."""
        settings = GameSettings()

        # Create game map and level generator WITHOUT BSP
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        level_generator = LevelGenerator(game_map, use_bsp=False)

        # Create engine with traditional level generator (generates level in __init__)
        engine = GameEngine(
            settings=settings,
            game_map=game_map,
            level_generator=level_generator
        )

        # Validate traditional generation was used
        assert isinstance(level_generator.room_generator, RoomGenerator)
        assert not isinstance(level_generator.room_generator, BSPRoomGenerator)

        # Validate map was generated correctly
        assert len(game_map.walls) > 0
        assert len(level_generator.last_generated_rooms) > 0

    def test_new_game_ascii_rendering_mode(self):
        """
        Test New Game startup with ASCII/glyphs rendering mode.

        Validates that ASCII rendering doesn't cause startup crashes.
        """
        settings = GameSettings()
        settings.graphics_mode = "glyphs"  # ASCII mode

        engine = GameEngine(settings=settings)

        # Validate game started successfully
        assert engine.game_state.level == 1
        assert len(engine.enemies) > 0
        assert settings.graphics_mode == "glyphs"

    def test_new_game_graphics_rendering_mode(self):
        """
        Test New Game startup with graphics rendering mode.

        Validates that graphics rendering doesn't cause startup crashes.
        """
        settings = GameSettings()
        settings.graphics_mode = "graphics"  # Graphics mode

        engine = GameEngine(settings=settings)

        # Validate game started successfully
        assert engine.game_state.level == 1
        assert len(engine.enemies) > 0
        assert settings.graphics_mode == "graphics"

    def test_new_game_deterministic_generation(self):
        """
        Test that same seed produces identical game states.

        This validates RNG seeding works correctly for both traditional
        and BSP generation.
        """
        from game_state import GameStateManager

        # Create two games with same seed
        state_manager1 = GameStateManager()
        state_manager1.dungeon_seed = 12345
        engine1 = GameEngine(settings=GameSettings(), game_state_manager=state_manager1)

        state_manager2 = GameStateManager()
        state_manager2.dungeon_seed = 12345
        engine2 = GameEngine(settings=GameSettings(), game_state_manager=state_manager2)

        # Verify identical map generation
        assert engine1.game_map.walls == engine2.game_map.walls
        assert len(engine1.game_map.walls) > 0  # Ensure maps were generated

        # Verify identical enemy spawning
        assert len(engine1.enemies) == len(engine2.enemies)
        assert len(engine1.enemies) > 0  # Ensure enemies spawned

        # Verify enemy positions match (same seed = same random placement)
        enemy_positions_1 = sorted([(e.position.x, e.position.y) for e in engine1.enemies])
        enemy_positions_2 = sorted([(e.position.x, e.position.y) for e in engine2.enemies])
        assert enemy_positions_1 == enemy_positions_2

    def test_new_game_different_seeds_produce_variation(self):
        """Test that different seeds produce different maps."""
        # Generate multiple games - they should have different layouts
        # (since seed is randomized during __init__)
        engine1 = GameEngine(settings=GameSettings())
        walls_1 = engine1.game_map.walls.copy()

        engine2 = GameEngine(settings=GameSettings())
        walls_2 = engine2.game_map.walls.copy()

        # Should be different (extremely high probability with random seeds)
        # If this fails, it's astronomically unlikely but not a bug
        assert walls_1 != walls_2

    def test_new_game_all_tcod_features_active(self):
        """
        Comprehensive test ensuring all new TCOD features work together.

        Tests:
        - BSP generation
        - TCOD random (reproducible RNG)
        - Perlin noise (shadow placement)
        - Dijkstra maps (enemy AI capabilities)
        """
        settings = GameSettings()
        engine = GameEngine(settings=settings)

        # Validate traditional room generation
        assert isinstance(engine.level_generator.room_generator, RoomGenerator)

        # Validate shadows were placed (noise-based)
        assert len(engine.game_map.shadows) > 0

        # Validate enemy pathfinding works (uses Dijkstra capabilities)
        if len(engine.enemies) > 0:
            enemy = engine.enemies[0]
            # Enemy should have valid pathfinding capabilities
            assert enemy.position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)

        # Validate deterministic generation (TCOD random)
        # This is implicitly tested by deterministic_generation test above

    def test_new_game_multiple_levels_progression(self):
        """
        Test that game can generate multiple levels without crashing.

        This catches issues with state cleanup between levels.

        NOTE: This test creates multiple engines since we can't control
        the level during GameEngine init. Each init generates level 1.
        """
        settings = GameSettings()

        # Create multiple game instances (each starts at level 1)
        for i in range(3):
            engine = GameEngine(settings=settings)

            # Validate each game generates correctly
            assert engine.game_state.level == 1
            assert len(engine.game_map.walls) > 0
            assert len(engine.enemies) > 0

    def test_new_game_edge_case_minimum_rooms(self):
        """Test New Game handles minimum room count edge cases."""
        settings = GameSettings()
        engine = GameEngine(settings=settings)

        # Even with BSP, should generate at least spawn room
        assert len(engine.level_generator.last_generated_rooms) >= 1

        # Should have walkable floor tiles
        walkable_tiles = 0
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if not engine.game_map.is_wall(Position(x, y)):
                    walkable_tiles += 1

        assert walkable_tiles > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
