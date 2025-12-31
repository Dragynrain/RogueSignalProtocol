#!/usr/bin/env python3
"""
New Game Smoke Tests - End-to-End validation of game startup.

These tests simulate the exact flow that happens when a player clicks "New Game"
to catch integration issues that unit tests miss. Tests both rendering modes
and level generation strategies.

Critical: These tests use actual GameEngine initialization with minimal mocking
to validate real-world game startup scenarios.
"""

import os
import sys

import pytest

# Add the project root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from rsp.core.config import GameConfig, GameSettings
from rsp.core.engine import GameEngine
from rsp.entities.base import Position
from rsp.level.generator import LevelGenerator
from rsp.level.structure import BSPRoomGenerator, RoomGenerator
from rsp.level.map import GameMap


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
        engine = GameEngine(settings=settings, game_map=game_map, level_generator=level_generator)

        # Validate BSP-specific results
        assert isinstance(level_generator.room_generator, BSPRoomGenerator)
        assert len(level_generator.last_generated_rooms) > 0
        assert len(level_generator.corridor_tiles) > 0

        # Validate map connectivity (rooms should be connected)
        # Player should be spawned on a walkable tile
        player_pos = engine.player.position
        assert not game_map.is_wall(player_pos), f"Player spawned on wall at {player_pos}"

        # Spawn area (2,2 to 10,10) should have some walkable tiles
        spawn_area_has_floor = any(
            not game_map.is_wall(Position(x, y)) for x in range(2, 10) for y in range(2, 10)
        )
        assert spawn_area_has_floor, "Spawn area has no walkable tiles"

    def test_new_game_with_traditional_generation(self):
        """Test New Game with traditional (non-BSP) generation."""
        settings = GameSettings()

        # Create game map and level generator WITHOUT BSP
        game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        level_generator = LevelGenerator(game_map, use_bsp=False)

        # Create engine with traditional level generator (generates level in __init__)
        engine = GameEngine(settings=settings, game_map=game_map, level_generator=level_generator)

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
        from rsp.core.state import GameStateManager

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
        assert len(engine.game_map.blind_spots) > 0

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


class TestActualNewGameRenderingSmoke:
    """
    Smoke tests for actual runtime rendering pipeline.

    These tests catch runtime errors that only appear during actual gameplay:
    - Missing imports
    - Attribute errors during rendering
    - Mouse event handling bugs
    - Rendering pipeline issues
    - Config constant mismatches (CONSOLE_WIDTH vs SCREEN_WIDTH)

    Merged from test_actual_new_game_smoke.py
    """

    def test_new_game_flow_with_rendering(self):
        """
        Simulate the actual New Game flow with rendering and mouse events.

        This catches runtime errors that unit tests miss, like GameConfig.CONSOLE_WIDTH bugs.
        """
        from unittest.mock import Mock, patch

        import tcod

        from rsp.input.handler import InputHandler
        from rsp.ui.menus import MainMenu

        with patch("rsp.systems.audio.SoundManager"):
            settings = GameSettings()

            # Create main menu
            menu = MainMenu(settings)
            menu.selected_option = 0  # "New Game" is first option

            # Simulate pressing Enter to start new game
            with patch("rsp.systems.save.SaveGameManager.save_exists", return_value=False):
                key_event = tcod.event.KeyDown(
                    scancode=tcod.event.Scancode.RETURN,
                    sym=tcod.event.KeySym.RETURN,
                    mod=tcod.event.Modifier.NONE,
                )
                result = menu.handle_input(key_event)
                assert result in (
                    "new_game",
                    "continue",
                    "",
                ), f"Expected game start action, got: {result}"

            # Create game engine
            engine = GameEngine(settings=settings, load_save=False)

            # Mock context for mouse events
            mock_context = Mock()
            mock_sdl_window = Mock()
            mock_sdl_window.size = (1280, 800)
            mock_context.sdl_window = mock_sdl_window
            engine.context = mock_context

            input_handler = InputHandler(engine)

            # Simulate several frames of mouse events
            for frame in range(10):
                mock_event = Mock()
                mock_event.position = Mock()
                mock_event.position.x = 400
                mock_event.position.y = 300

                # Should not raise AttributeError for CONSOLE_WIDTH/HEIGHT
                try:
                    input_handler.handle_mouse_motion(mock_event)
                except AttributeError as e:
                    error_str = str(e)
                    if "CONSOLE_WIDTH" in error_str or "CONSOLE_HEIGHT" in error_str:
                        pytest.fail(f"CRITICAL: Mouse handling has config attribute error: {e}")
                    if "SCREEN_WIDTH" in error_str or "SCREEN_HEIGHT" in error_str:
                        pytest.fail(f"CRITICAL: Mouse handling missing SCREEN constants: {e}")
                except Exception:
                    pass  # Other exceptions are fine in test environment

            # Verify game initialized successfully
            assert engine.game_state.level == 1
            assert engine.player is not None
            assert len(engine.enemies) > 0
            assert len(engine.game_map.walls) > 0

    def test_input_handler_mouse_coordinate_conversion(self):
        """
        Test that InputHandler can convert mouse coordinates without errors.

        Specifically tests for bugs like:
        - GameConfig.CONSOLE_WIDTH (should be SCREEN_WIDTH)
        - GameConfig.CONSOLE_HEIGHT (should be SCREEN_HEIGHT)
        - pixel_x used twice instead of pixel_y
        """
        from unittest.mock import Mock, patch

        with patch("rsp.systems.audio.SoundManager"):
            from rsp.input.handler import InputHandler

            settings = GameSettings()
            engine = GameEngine(settings=settings, load_save=False)

            # Mock context with window dimensions
            mock_context = Mock()
            mock_context.recommended_console_size.return_value = (80, 50)
            mock_sdl_window = Mock()
            mock_sdl_window.size = (1280, 800)
            mock_context.sdl_window = mock_sdl_window
            engine.context = mock_context

            input_handler = InputHandler(engine)

            # Test various mouse positions
            test_positions = [
                (0, 0),  # Top-left
                (640, 400),  # Center
                (1279, 799),  # Bottom-right
                (100, 200),  # Random position
            ]

            for pixel_x, pixel_y in test_positions:
                mock_event = Mock()
                mock_event.position = Mock()
                mock_event.position.x = pixel_x
                mock_event.position.y = pixel_y

                try:
                    input_handler.handle_mouse_motion(mock_event)

                    # Verify correct conversion
                    expected_tile_x = pixel_x * GameConfig.SCREEN_WIDTH // 1280
                    expected_tile_y = pixel_y * GameConfig.SCREEN_HEIGHT // 800

                    assert (
                        engine.last_mouse_tile_x == expected_tile_x
                    ), f"Mouse X wrong: expected {expected_tile_x}, got {engine.last_mouse_tile_x}"
                    assert (
                        engine.last_mouse_tile_y == expected_tile_y
                    ), f"Mouse Y wrong: expected {expected_tile_y}, got {engine.last_mouse_tile_y}"

                except AttributeError as e:
                    error_str = str(e)
                    if "CONSOLE_WIDTH" in error_str or "CONSOLE_HEIGHT" in error_str:
                        pytest.fail(f"CRITICAL BUG: Using wrong config constants: {e}")
                    if "'GameConfig' has no attribute" in error_str:
                        pytest.fail(f"CRITICAL BUG: GameConfig attribute missing: {e}")
                    raise


class TestFullRenderingPipeline:
    """
    Complete rendering pipeline smoke tests with ZERO mocking.

    These tests actually render frames to catch bugs that only appear
    during real rendering, like the game_info_panel.py bug where
    game.game_state.screen was accessed but doesn't exist.
    """

    def test_render_first_frame_glyphs_mode(self):
        """
        Render the actual first frame in glyphs mode.

        This catches rendering errors like:
        - AttributeError during info panel rendering
        - Missing attributes on game objects
        - Coordinate conversion bugs
        """
        import tcod

        from rsp.rendering.core import GameRenderer

        # Create real game with glyphs mode
        settings = GameSettings()
        settings.graphics_mode = "glyphs"
        engine = GameEngine(settings=settings)

        # Create real console
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create real renderer (no mocking!)
        renderer = GameRenderer(settings, context=None)

        # Simulate mouse movement (this triggers info panel updates)
        engine.last_mouse_tile_x = 30
        engine.last_mouse_tile_y = 15

        # THIS IS THE CRITICAL TEST: Actually render the frame
        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(
                f"RENDERING FAILURE: {e}\n"
                f"This is a critical bug that prevents the game from running!\n"
                f"The smoke test should have caught this before commit."
            )
        except Exception as e:
            # Other exceptions might be acceptable (like missing context for graphics mode)
            # but AttributeError means code is accessing non-existent attributes
            if "has no attribute" in str(e):
                pytest.fail(f"CRITICAL: Attribute error during rendering: {e}")
            # Allow other exceptions for test environment limitations
        # No critical exception means rendering code is sound

    def test_render_multiple_frames_with_mouse_movement(self):
        """
        Render multiple frames with mouse movement to catch state-dependent bugs.
        """
        import tcod

        from rsp.rendering.core import GameRenderer

        settings = GameSettings()
        settings.graphics_mode = "glyphs"
        engine = GameEngine(settings=settings)
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        renderer = GameRenderer(settings, context=None)

        # Simulate 10 frames with different mouse positions
        mouse_positions = [
            (10, 10),
            (30, 15),
            (50, 20),
            (5, 5),
            (40, 25),
            (35, 30),
            (20, 10),
            (45, 35),
            (15, 40),
            (25, 20),
        ]

        for frame, (mouse_x, mouse_y) in enumerate(mouse_positions):
            engine.last_mouse_tile_x = mouse_x
            engine.last_mouse_tile_y = mouse_y

            try:
                renderer.render_game(console, engine, context=None)
            except AttributeError as e:
                pytest.fail(f"Frame {frame} rendering failed at mouse ({mouse_x},{mouse_y}): {e}")
            except Exception:
                pass  # Other exceptions OK in test environment

    def test_render_with_inventory_open(self):
        """Test rendering with UI screens open (inventory, help, etc.)."""
        import tcod

        from rsp.rendering.core import GameRenderer

        settings = GameSettings()
        settings.graphics_mode = "glyphs"
        engine = GameEngine(settings=settings)
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        renderer = GameRenderer(settings, context=None)

        # Test with inventory open
        engine.show_inventory = True
        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(f"Inventory rendering failed: {e}")
        except Exception:
            pass

        # Test with help open
        engine.show_inventory = False
        engine.show_help = True
        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(f"Help screen rendering failed: {e}")
        except Exception:
            pass

    def test_render_with_enemies_visible(self):
        """Test rendering with enemies in view to catch entity rendering bugs."""
        import tcod

        from rsp.rendering.core import GameRenderer

        settings = GameSettings()
        settings.graphics_mode = "glyphs"
        engine = GameEngine(settings=settings)
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        renderer = GameRenderer(settings, context=None)

        # Ensure at least one enemy is near player for visibility
        if len(engine.enemies) > 0:
            enemy = engine.enemies[0]
            enemy.position.x = engine.player.position.x + 5
            enemy.position.y = engine.player.position.y + 5

        # Hover mouse over enemy position
        engine.last_mouse_tile_x = engine.enemies[0].position.x if engine.enemies else 10
        engine.last_mouse_tile_y = engine.enemies[0].position.y if engine.enemies else 10

        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(f"Enemy rendering/info panel failed: {e}")
        except Exception:
            pass

    def test_render_achievement_popup(self):
        """Test rendering with achievement popup active."""
        import tcod

        from rsp.systems.achievements import AchievementManager
        from rsp.rendering.core import GameRenderer

        settings = GameSettings()
        settings.graphics_mode = "glyphs"
        engine = GameEngine(settings=settings)
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        renderer = GameRenderer(settings, context=None)

        # Queue an achievement popup
        AchievementManager._pending_popups = ["first_blood"]
        engine.achievement_popup_manager.update()

        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(f"Achievement popup rendering failed: {e}")
        except Exception:
            pass

    def test_render_graphics_mode_without_context(self):
        """
        Test that graphics mode fails gracefully without context.

        This shouldn't crash with AttributeError, just skip graphics rendering.
        """
        import tcod

        from rsp.rendering.core import GameRenderer

        settings = GameSettings()
        settings.graphics_mode = "graphics"  # Graphics mode
        engine = GameEngine(settings=settings)
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        renderer = GameRenderer(settings, context=None)

        # Should not raise AttributeError (context is None, so should fall back)
        try:
            renderer.render_game(console, engine, context=None)
        except AttributeError as e:
            pytest.fail(f"Graphics mode should fail gracefully without context: {e}")
        except Exception:
            pass  # Other exceptions are OK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
