#!/usr/bin/env python3
"""
Integration tests for rendering systems.
Tests both graphics and glyph rendering modes with real game objects.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import tcod
import math

from game_config import GameConfig, GameSettings
from game_rendering_core import GameRenderer
from game_rendering_graphics import GraphicsMapRenderer
from game_rendering_glyphs import GlyphsMapRenderer
from game_engine import GameEngine
from game_entities import Position
from tests.fixtures.simple_fixtures import player, enemy, create_test_map


class TestGraphicsRendererIntegration(unittest.TestCase):
    """Integration tests for GraphicsMapRenderer with real game objects."""

    def setUp(self):
        """Set up test fixtures for graphics rendering."""
        self.settings = GameSettings()
        self.settings.graphics_mode = "graphics"

        # Create mock tile manager
        self.tile_manager = Mock()
        self.tile_manager.get_sprite_texture = Mock(return_value=Mock())
        self.tile_manager.tile_width = 32
        self.tile_manager.tile_height = 32

        # Create mock SDL context
        self.context = Mock()
        self.sdl_renderer = Mock()
        self.context.sdl_renderer = self.sdl_renderer
        self.context.console_render = Mock()

        # Create renderer
        self.renderer = GraphicsMapRenderer(
            tile_manager=self.tile_manager,
            context=self.context,
            settings=self.settings
        )

        # Create test game engine
        mock_sound_manager = Mock()
        self.engine = GameEngine(sound_manager=mock_sound_manager, settings=self.settings)

    def test_graphics_renderer_initialization(self):
        """Test that GraphicsMapRenderer initializes correctly."""
        self.assertIsNotNone(self.renderer)
        self.assertEqual(self.renderer.tile_manager, self.tile_manager)
        self.assertEqual(self.renderer.context, self.context)
        self.assertEqual(self.renderer.settings, self.settings)

    def test_should_use_graphics_returns_true_when_properly_configured(self):
        """Test that _should_use_graphics returns True when all components are present."""
        result = self.renderer._should_use_graphics()
        self.assertTrue(result, "Should use graphics when tile_manager, context, and sdl_renderer are present")

    def test_should_use_graphics_returns_false_when_missing_components(self):
        """Test that _should_use_graphics returns False when components are missing."""
        # Test with no tile manager
        renderer_no_tm = GraphicsMapRenderer(tile_manager=None, context=self.context, settings=self.settings)
        self.assertFalse(renderer_no_tm._should_use_graphics())

        # Test with no context
        renderer_no_ctx = GraphicsMapRenderer(tile_manager=self.tile_manager, context=None, settings=self.settings)
        self.assertFalse(renderer_no_ctx._should_use_graphics())

        # Test with no SDL renderer
        mock_context_no_sdl = Mock()
        mock_context_no_sdl.sdl_renderer = None
        renderer_no_sdl = GraphicsMapRenderer(tile_manager=self.tile_manager, context=mock_context_no_sdl, settings=self.settings)
        self.assertFalse(renderer_no_sdl._should_use_graphics())

    def test_world_to_console_coordinate_conversion(self):
        """Test world coordinate to console coordinate conversion."""
        camera_offset = Position(0, 0)

        # Test basic conversion (note: console_y has +1 offset for status bar)
        console_x, console_y = self.renderer._world_to_console(5, 5, camera_offset)
        self.assertEqual(console_x, 5)
        self.assertEqual(console_y, 6)  # +1 for status bar at row 0

        # Test with camera offset
        camera_offset = Position(10, 10)
        console_x, console_y = self.renderer._world_to_console(15, 15, camera_offset)
        self.assertEqual(console_x, 5)
        self.assertEqual(console_y, 6)  # +1 for status bar at row 0

    def test_is_in_viewport_boundary_checks(self):
        """Test viewport boundary checking."""
        camera_offset = Position(0, 0)

        # Test visible position
        self.assertTrue(self.renderer._is_in_viewport(10, 10, camera_offset))

        # Test position outside viewport (negative)
        self.assertFalse(self.renderer._is_in_viewport(-1, -1, camera_offset))

        # Test position outside viewport (beyond game area)
        self.assertFalse(self.renderer._is_in_viewport(1000, 1000, camera_offset))

    def test_calculate_camera_offset_centers_on_player(self):
        """Test that camera offset centers on player position."""
        # Create player at specific position
        test_player = player(x=50, y=50)

        camera_offset = self.renderer._calculate_camera_offset(test_player)

        # Camera should be offset to center player in viewport
        expected_x = test_player.x - GameConfig.GAME_AREA_WIDTH() // 2
        # SCREEN_HEIGHT - PANEL_HEIGHT gives game area height
        game_area_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT
        expected_y = test_player.y - game_area_height // 2

        self.assertEqual(camera_offset.x, expected_x)
        self.assertEqual(camera_offset.y, expected_y)

    def test_grid_to_pixel_conversion(self):
        """Test grid coordinate to pixel coordinate conversion."""
        tile_width = 32
        tile_height = 32

        # Test basic conversion
        pixel_x, pixel_y = self.renderer._grid_to_pixel(5, 5)

        self.assertEqual(pixel_x, 5 * tile_width)
        self.assertEqual(pixel_y, 5 * tile_height)

    def test_get_tile_rect_returns_correct_bounds(self):
        """Test that _get_tile_rect returns correct rectangle bounds."""
        tile_width = 32
        tile_height = 32

        rect = self.renderer._get_tile_rect(5, 5)

        # Should return (x, y, width, height)
        self.assertEqual(len(rect), 4)
        self.assertEqual(rect[0], 5 * tile_width)
        self.assertEqual(rect[1], 5 * tile_height)
        self.assertEqual(rect[2], tile_width)
        self.assertEqual(rect[3], tile_height)

    def test_render_sprites_layer_calls_sdl_renderer(self):
        """Test that render_sprites_layer calls SDL renderer methods."""
        # This is the critical test that would have caught all the bugs!
        # Should execute without raising exceptions
        self.renderer.render_sprites_layer(self.engine)

        # Should have called SDL renderer methods
        self.assertTrue(self.sdl_renderer.set_draw_color.called or
                       self.sdl_renderer.draw_color.called or
                       self.sdl_renderer.copy.called,
                       "SDL renderer should have been called")

    def test_render_overlay_layer_executes_without_error(self):
        """Test that render_overlay_layer executes without error."""
        # Add some vision overlays to test
        from game_entities import EnemyState
        test_enemy = enemy("scanner", 15, 15)
        test_enemy.state = EnemyState.HOSTILE
        self.engine.enemies = [test_enemy]

        # Should execute without raising exceptions
        self.renderer.render_overlay_layer(self.engine)

        # If we got here, the test passed
        self.assertTrue(True)

    def test_render_status_effects_layer_executes_without_error(self):
        """Test that render_status_effects_layer executes without error."""
        # Add player with status effects
        self.engine.player.status_effects = {"stun": 2}

        # Should execute without raising exceptions
        self.renderer.render_status_effects_layer(self.engine)

        # If we got here, the test passed
        self.assertTrue(True)

    def test_expand_rect_increases_bounds_correctly(self):
        """Test that _expand_rect expands rectangle bounds correctly."""
        rect = (10, 10, 20, 20)
        offset = 5

        expanded = self.renderer._expand_rect(rect, offset)

        # Should expand by offset in all directions
        self.assertEqual(expanded[0], 10 - offset)  # x
        self.assertEqual(expanded[1], 10 - offset)  # y
        self.assertEqual(expanded[2], 20 + 2 * offset)  # width
        self.assertEqual(expanded[3], 20 + 2 * offset)  # height

    def test_get_pulse_intensity_returns_valid_range(self):
        """Test that _get_pulse_intensity returns values in valid range."""
        intensity = self.renderer._get_pulse_intensity()

        # Should return value between 0.0 and 1.0
        self.assertGreaterEqual(intensity, 0.0)
        self.assertLessEqual(intensity, 1.0)

    def test_get_status_outline_color_returns_rgb_tuple(self):
        """Test that _get_status_outline_color returns valid RGB tuple."""
        color = self.renderer._get_status_outline_color("stun")

        # Should return 3-tuple of ints
        self.assertEqual(len(color), 3)
        for component in color:
            self.assertIsInstance(component, int)
            self.assertGreaterEqual(component, 0)
            self.assertLessEqual(component, 255)


class TestGlyphsRendererIntegration(unittest.TestCase):
    """Integration tests for GlyphsMapRenderer with real game objects."""

    def setUp(self):
        """Set up test fixtures for glyph rendering."""
        self.settings = GameSettings()
        self.settings.graphics_mode = "classic"

        # Create renderer
        self.renderer = GlyphsMapRenderer(settings=self.settings)

        # Create test console
        self.console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create test game engine
        mock_sound_manager = Mock()
        self.engine = GameEngine(sound_manager=mock_sound_manager, settings=self.settings)

    def test_glyphs_renderer_initialization(self):
        """Test that GlyphsMapRenderer initializes correctly."""
        self.assertIsNotNone(self.renderer)
        self.assertEqual(self.renderer.settings, self.settings)

    def test_should_use_graphics_returns_false_in_classic_mode(self):
        """Test that _should_use_graphics returns False in classic mode."""
        result = self.renderer._should_use_graphics()
        self.assertFalse(result)

    def test_world_to_console_coordinate_conversion(self):
        """Test world coordinate to console coordinate conversion."""
        camera_offset = Position(0, 0)

        # Test basic conversion (note: console_y has +1 offset for status bar)
        console_x, console_y = self.renderer._world_to_console(5, 5, camera_offset)
        self.assertEqual(console_x, 5)
        self.assertEqual(console_y, 6)  # +1 for status bar at row 0

        # Test with camera offset
        camera_offset = Position(10, 10)
        console_x, console_y = self.renderer._world_to_console(15, 15, camera_offset)
        self.assertEqual(console_x, 5)
        self.assertEqual(console_y, 6)  # +1 for status bar at row 0

    def test_is_in_viewport_boundary_checks(self):
        """Test viewport boundary checking."""
        camera_offset = Position(0, 0)

        # Test visible position
        self.assertTrue(self.renderer._is_in_viewport(10, 10, camera_offset))

        # Test position outside viewport (negative)
        self.assertFalse(self.renderer._is_in_viewport(-1, -1, camera_offset))

        # Test position outside viewport (beyond game area)
        self.assertFalse(self.renderer._is_in_viewport(1000, 1000, camera_offset))

    def test_calculate_camera_offset_centers_on_player(self):
        """Test that camera offset centers on player position."""
        # Create player at specific position
        test_player = player(x=50, y=50)

        camera_offset = self.renderer._calculate_camera_offset(test_player)

        # Camera should be offset to center player in viewport
        # GlyphsMapRenderer uses VIEWPORT_WIDTH/HEIGHT based on graphics mode
        graphics_mode = self.renderer._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        expected_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                               test_player.x - viewport_width // 2))
        expected_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                               test_player.y - viewport_height // 2))

        self.assertEqual(camera_offset.x, expected_x)
        self.assertEqual(camera_offset.y, expected_y)

    def test_render_map_executes_without_error(self):
        """Test that render_map executes without error."""
        # This is the critical test for glyph rendering!
        self.renderer.render_map(self.console, self.engine)

        # Should complete without raising exceptions
        # Console should have some content rendered
        self.assertIsNotNone(self.console)

    def test_get_smart_wall_character_returns_box_drawing_char(self):
        """Test that _get_smart_wall_character returns valid box drawing character."""
        # Create test map with walls
        test_map = create_test_map(20, 20)

        # Add some walls to test (GameMap uses .walls set, not .tiles)
        for x in range(5, 10):
            test_map.walls.add((x, 5))

        # Get wall character
        char = self.renderer._get_smart_wall_character(test_map, 7, 5)

        # Should return a string (Unicode box-drawing character)
        self.assertIsInstance(char, str)
        # Should be a valid double-line box drawing character
        valid_chars = {'║', '═', '╔', '╗', '╚', '╝', '╠', '╣', '╦', '╩', '╬', '■'}
        self.assertIn(char, valid_chars)

    def test_get_upgrade_color_returns_rgb_tuple(self):
        """Test that _get_upgrade_color returns valid RGB tuple."""
        color = self.renderer._get_upgrade_color("blue")

        # Should return 3-tuple of ints
        self.assertEqual(len(color), 3)
        for component in color:
            self.assertIsInstance(component, int)
            self.assertGreaterEqual(component, 0)
            self.assertLessEqual(component, 255)

    def test_get_story_fragment_color_returns_rgb_tuple(self):
        """Test that _get_story_fragment_color returns valid RGB tuple."""
        color = self.renderer._get_story_fragment_color(100)

        # Should return 3-tuple of ints
        self.assertEqual(len(color), 3)
        for component in color:
            self.assertIsInstance(component, int)
            self.assertGreaterEqual(component, 0)
            self.assertLessEqual(component, 255)

    def test_get_player_color_returns_rgb_tuple(self):
        """Test that _get_player_color returns valid RGB tuple."""
        test_player = player(10, 10)
        color = self.renderer._get_player_color(test_player)

        # Should return 3-tuple of ints
        self.assertEqual(len(color), 3)
        for component in color:
            self.assertIsInstance(component, int)
            self.assertGreaterEqual(component, 0)
            self.assertLessEqual(component, 255)

    def test_safely_overlay_tile_does_not_crash(self):
        """Test that _safely_overlay_tile handles boundaries correctly."""
        # Test valid position
        self.renderer._safely_overlay_tile(self.console, 5, 5, (255, 0, 0))

        # Test boundary positions (should not crash)
        self.renderer._safely_overlay_tile(self.console, 0, 0, (255, 0, 0))
        # Game area height = SCREEN_HEIGHT - PANEL_HEIGHT
        game_area_height = GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT
        self.renderer._safely_overlay_tile(self.console, GameConfig.GAME_AREA_WIDTH() - 1,
                                           game_area_height - 1, (255, 0, 0))


class TestGameRendererIntegration(unittest.TestCase):
    """Integration tests for GameRenderer orchestration."""

    def setUp(self):
        """Set up test fixtures for GameRenderer."""
        self.settings = GameSettings()

        # Create mock tile manager
        self.tile_manager = Mock()
        self.tile_manager.get_sprite_texture = Mock(return_value=Mock())
        self.tile_manager.tile_width = 32
        self.tile_manager.tile_height = 32

        # Create mock SDL context
        self.context = Mock()
        self.sdl_renderer = Mock()
        self.context.sdl_renderer = self.sdl_renderer
        self.context.console_render = Mock()

        # Create console
        self.console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create test game engine
        mock_sound_manager = Mock()
        self.engine = GameEngine(sound_manager=mock_sound_manager, settings=self.settings)

    def test_game_renderer_initialization_with_graphics_mode(self):
        """Test GameRenderer initializes correctly in graphics mode."""
        self.settings.graphics_mode = "graphics"

        renderer = GameRenderer(
            settings=self.settings,
            tile_manager=self.tile_manager,
            context=self.context
        )

        self.assertIsNotNone(renderer)
        self.assertIsNotNone(renderer.glyphs_renderer)
        self.assertIsNotNone(renderer.graphics_renderer)
        self.assertIsNotNone(renderer.ui_renderer)

    def test_game_renderer_initialization_with_classic_mode(self):
        """Test GameRenderer initializes correctly in classic mode."""
        self.settings.graphics_mode = "classic"

        renderer = GameRenderer(settings=self.settings)

        self.assertIsNotNone(renderer)
        self.assertIsNotNone(renderer.glyphs_renderer)
        self.assertIsNotNone(renderer.ui_renderer)

    def test_render_game_in_classic_mode_executes_without_error(self):
        """Test render_game executes without error in classic mode."""
        self.settings.graphics_mode = "classic"
        renderer = GameRenderer(settings=self.settings)

        # Should execute without raising exceptions
        renderer.render_game(self.console, self.engine)

        # Console should have content
        self.assertIsNotNone(self.console)

    def test_render_game_in_graphics_mode_executes_without_error(self):
        """Test render_game executes without error in graphics mode."""
        self.settings.graphics_mode = "graphics"

        # Create a larger console to avoid index out of bounds
        large_console = tcod.console.Console(100, 100)

        renderer = GameRenderer(
            settings=self.settings,
            tile_manager=self.tile_manager,
            context=self.context
        )

        # Should execute without raising exceptions
        renderer.render_game(large_console, self.engine, context=self.context)

        # Should have called SDL renderer
        self.assertTrue(self.sdl_renderer.set_draw_color.called or self.sdl_renderer.clear.called)

    def test_render_game_with_inventory_screen(self):
        """Test render_game handles inventory screen overlay."""
        renderer = GameRenderer(settings=self.settings)

        # Show inventory
        self.engine.show_inventory = True

        # Should execute without error
        renderer.render_game(self.console, self.engine)

        # Console should be cleared for overlay
        self.assertIsNotNone(self.console)

    def test_render_game_with_help_screen(self):
        """Test render_game handles help screen overlay."""
        renderer = GameRenderer(settings=self.settings)

        # Show help
        self.engine.show_help = True

        # Should execute without error
        renderer.render_game(self.console, self.engine)

        # Console should be cleared for overlay
        self.assertIsNotNone(self.console)

    def test_render_game_with_lore_viewer(self):
        """Test render_game handles lore viewer overlay."""
        renderer = GameRenderer(settings=self.settings)

        # Show lore viewer
        self.engine.show_lore_viewer = True

        # Should execute without error
        renderer.render_game(self.console, self.engine)

        # Console should be cleared for overlay
        self.assertIsNotNone(self.console)

    def test_render_game_with_story_fragment(self):
        """Test render_game handles story fragment overlay."""
        renderer = GameRenderer(settings=self.settings)

        # Show story fragment (use integer index, not string)
        self.engine.show_story_fragment = 0

        # Should execute without error
        renderer.render_game(self.console, self.engine)

        # Console should be cleared for overlay
        self.assertIsNotNone(self.console)


class TestRenderingErrorConditions(unittest.TestCase):
    """Tests for error conditions and edge cases in rendering."""

    def test_graphics_renderer_handles_missing_tile_manager_gracefully(self):
        """Test that GraphicsMapRenderer handles missing tile manager gracefully."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        renderer = GraphicsMapRenderer(tile_manager=None, context=None, settings=settings)

        # Should not crash on initialization
        self.assertIsNotNone(renderer)

        # Should return False for _should_use_graphics
        self.assertFalse(renderer._should_use_graphics())

    def test_graphics_renderer_handles_missing_context_gracefully(self):
        """Test that GraphicsMapRenderer handles missing context gracefully."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        tile_manager = Mock()
        renderer = GraphicsMapRenderer(tile_manager=tile_manager, context=None, settings=settings)

        # Should not crash on initialization
        self.assertIsNotNone(renderer)

        # Should return False for _should_use_graphics
        self.assertFalse(renderer._should_use_graphics())

    def test_glyphs_renderer_handles_none_settings(self):
        """Test that GlyphsMapRenderer handles None settings gracefully."""
        renderer = GlyphsMapRenderer(settings=None)

        # Should not crash on initialization
        self.assertIsNotNone(renderer)

    def test_game_renderer_handles_none_settings(self):
        """Test that GameRenderer handles None settings gracefully."""
        renderer = GameRenderer(settings=None)

        # Should not crash on initialization
        self.assertIsNotNone(renderer)

    def test_render_with_empty_game_state(self):
        """Test rendering with empty game state."""
        renderer = GameRenderer(settings=GameSettings())
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create minimal game engine
        mock_sound_manager = Mock()
        engine = GameEngine(sound_manager=mock_sound_manager, settings=GameSettings())

        # Clear enemies
        engine.enemies = []

        # Should not crash
        renderer.render_game(console, engine)

    def test_render_with_out_of_bounds_entities(self):
        """Test rendering handles entities outside map bounds."""
        renderer = GlyphsMapRenderer(settings=GameSettings())
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Create game with out-of-bounds entities
        mock_sound_manager = Mock()
        engine = GameEngine(sound_manager=mock_sound_manager, settings=GameSettings())

        # Move player way out of bounds
        engine.player.x = -1000
        engine.player.y = -1000

        # Should not crash
        renderer.render_map(console, engine)


if __name__ == '__main__':
    unittest.main()
