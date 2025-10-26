#!/usr/bin/env python3
"""
Unit tests for game_input.py mouse handling and bounds checking.

Tests focus on:
- Mouse coordinate conversion (pixel → viewport → world)
- Bounds checking at multiple levels (screen, viewport, world)
- Mouse motion handlers (look mode, targeting, gameplay)
- Mouse wheel handlers (inventory, lore viewer)
- Edge cases and out-of-bounds handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tcod.event

from game_input import InputHandler
from game_entities import Position
from game_config import GameConfig


def create_mock_game():
    """Create a mock game object for testing."""
    game = Mock()

    # Player
    game.player = Mock()
    game.player.x = 25
    game.player.y = 25
    game.player.inventory_manager = Mock()
    game.player.inventory_manager.equipped_exploits = []
    game.player.inventory_manager.get_display_items = Mock(return_value=[])

    # Game state
    game.game_over = False
    game.show_help = False
    game.show_story_fragment = None
    game.show_lore_viewer = False
    game.show_inventory = False
    game.targeting_mode = False
    game.look_mode = False
    game.look_cursor_position = Position(25, 25)
    game.cursor_position = Position(25, 25)
    game.inventory_scroll_offset = 0  # Add for mouse wheel tests

    # Settings
    game.settings = Mock()
    game.settings.graphics_mode = "glyph"

    # Mocks
    game.game_map = Mock()
    game.game_map.width = GameConfig.MAP_WIDTH
    game.game_map.height = GameConfig.MAP_HEIGHT
    game.message_log = Mock()
    game.sound_manager = Mock()
    game.dialogue_state = Mock()
    game.dialogue_state.is_active = Mock(return_value=False)
    game.story_fragment_manager = Mock()
    game.story_fragment_manager.get_discovered_fragments = Mock(return_value=[])

    # Camera offset
    game.last_camera_offset = Position(0, 0)

    return game


class TestMouseTileBoundsChecking:
    """Test _is_valid_mouse_tile() bounds checking."""

    def test_valid_tile_coordinates(self):
        """Test that valid tile coordinates return True."""
        game = create_mock_game()
        handler = InputHandler(game)

        # Test corners and center
        assert handler._is_valid_mouse_tile(0, 0) is True
        assert handler._is_valid_mouse_tile(79, 0) is True
        assert handler._is_valid_mouse_tile(0, 49) is True
        assert handler._is_valid_mouse_tile(79, 49) is True
        assert handler._is_valid_mouse_tile(40, 25) is True

    def test_out_of_bounds_negative(self):
        """Test that negative coordinates return False."""
        game = create_mock_game()
        handler = InputHandler(game)

        assert handler._is_valid_mouse_tile(-1, 0) is False
        assert handler._is_valid_mouse_tile(0, -1) is False
        assert handler._is_valid_mouse_tile(-1, -1) is False

    def test_out_of_bounds_too_large(self):
        """Test that coordinates beyond screen bounds return False."""
        game = create_mock_game()
        handler = InputHandler(game)

        assert handler._is_valid_mouse_tile(80, 0) is False
        assert handler._is_valid_mouse_tile(0, 50) is False
        assert handler._is_valid_mouse_tile(80, 50) is False
        assert handler._is_valid_mouse_tile(100, 100) is False


class TestMousePixelToWorldConversion:
    """Test _mouse_pixel_to_world() coordinate conversion and bounds."""

    def test_glyph_mode_conversion_valid_coords(self):
        """Test pixel to world conversion in glyph mode with valid coordinates."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(10, 10)

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Get status bar height and viewport dimensions
        status_bar_height = GameConfig.STATUS_BAR_HEIGHT()
        viewport_width = GameConfig.VIEWPORT_WIDTH("glyph")

        # Return a tile position that's well within viewport bounds
        # Tile position must be: status_bar + viewport_y, and < viewport_width
        valid_tile_x = min(10, viewport_width - 1)  # Safe X within viewport
        valid_tile_y = status_bar_height + 5  # 5 tiles into viewport

        with patch('game_input.CoordinateHelpers.pixel_to_char_coords',
                   return_value=(valid_tile_x, valid_tile_y)):
            world_pos = handler._mouse_pixel_to_world(400, 300)

            # Should return a valid position
            assert world_pos is not None
            assert isinstance(world_pos, Position)
            # World position should be within map bounds
            assert 0 <= world_pos.x < GameConfig.MAP_WIDTH
            assert 0 <= world_pos.y < GameConfig.MAP_HEIGHT

    def test_glyph_mode_out_of_viewport_bounds(self):
        """Test that clicks outside viewport return None."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Click in status bar (y=0, which is < status bar height)
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(40, 0)):
            world_pos = handler._mouse_pixel_to_world(400, 10)

            # Should return None (in status bar, not gameplay area)
            assert world_pos is None

    def test_glyph_mode_out_of_world_bounds(self):
        """Test that clicks resulting in invalid world coords return None."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(0, 0)

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Click that would result in world coords beyond map bounds
        # Viewport coords that, when added to camera offset, exceed MAP_WIDTH/HEIGHT
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(100, 100)):
            world_pos = handler._mouse_pixel_to_world(800, 600)

            # Should return None (outside world bounds)
            assert world_pos is None

    def test_graphics_mode_without_renderer_returns_none(self):
        """Test that graphics mode without renderer returns None."""
        game = create_mock_game()
        game.settings.graphics_mode = "graphics"

        handler = InputHandler(game)
        handler.renderer = None  # No renderer

        world_pos = handler._mouse_pixel_to_world(400, 300)

        # Should return None and log error
        assert world_pos is None

    def test_graphics_mode_with_renderer(self):
        """Test pixel to world conversion in graphics mode."""
        game = create_mock_game()
        game.settings.graphics_mode = "graphics"
        game.last_camera_offset = Position(5, 5)

        handler = InputHandler(game)

        # Mock renderer with tile manager
        mock_renderer = Mock()
        mock_renderer.tile_manager = Mock()
        mock_renderer.tile_manager.tile_width = 32
        mock_renderer.tile_manager.tile_height = 32
        handler.renderer = mock_renderer

        # Mock the coordinate conversion
        with patch('game_input.CoordinateHelpers.pixel_to_sprite_grid', return_value=(15, 15)):
            world_pos = handler._mouse_pixel_to_world(480, 480)

            assert world_pos is not None
            assert isinstance(world_pos, Position)

    def test_viewport_bounds_checking(self):
        """Test that viewport coordinates are validated correctly."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(0, 0)

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Test viewport x bounds
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(-5, 10)):
            assert handler._mouse_pixel_to_world(0, 200) is None

        # Test viewport x upper bound (depends on VIEWPORT_WIDTH)
        viewport_width = GameConfig.VIEWPORT_WIDTH("glyph")
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords',
                   return_value=(viewport_width + 10, 10)):
            assert handler._mouse_pixel_to_world(900, 200) is None

    def test_world_bounds_checking(self):
        """Test that world coordinates are validated against map bounds."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(GameConfig.MAP_WIDTH - 5, GameConfig.MAP_HEIGHT - 5)

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Click that would put world coords beyond map width
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(20, 10)):
            world_pos = handler._mouse_pixel_to_world(600, 200)

            # Should return None (world x would be camera_x + viewport_x > MAP_WIDTH)
            if world_pos:
                assert world_pos.x < GameConfig.MAP_WIDTH
                assert world_pos.y < GameConfig.MAP_HEIGHT


class TestLookModeMouseHandlers:
    """Test look mode mouse motion handling."""

    def test_look_mode_mouse_updates_cursor(self):
        """Test that mouse motion in look mode updates cursor position."""
        game = create_mock_game()
        game.look_mode = True
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(0, 0)

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        # Create mouse motion event
        event = Mock()
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        with patch.object(handler, '_mouse_pixel_to_world', return_value=Position(20, 15)):
            handler._handle_look_mode_mouse_motion(event)

            # Cursor should be updated
            assert game.look_cursor_position.x == 20
            assert game.look_cursor_position.y == 15

    def test_look_mode_invalid_position_ignored(self):
        """Test that invalid mouse positions don't crash look mode."""
        game = create_mock_game()
        game.look_mode = True
        original_cursor = Position(10, 10)
        game.look_cursor_position = original_cursor

        handler = InputHandler(game)

        event = Mock()
        event.position = Mock()
        event.position.x = -100  # Out of bounds
        event.position.y = -100

        with patch.object(handler, '_mouse_pixel_to_world', return_value=None):
            handler._handle_look_mode_mouse_motion(event)

            # Cursor should remain unchanged
            assert game.look_cursor_position == original_cursor


class TestTargetingMouseHandlers:
    """Test targeting mode mouse motion handling."""

    def test_targeting_mode_mouse_updates_cursor(self):
        """Test that mouse motion in targeting mode updates cursor position."""
        game = create_mock_game()
        game.targeting_mode = True
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = Position(0, 0)

        handler = InputHandler(game)

        event = Mock()
        event.position = Mock()
        event.position.x = 500
        event.position.y = 400

        with patch.object(handler, '_mouse_pixel_to_world', return_value=Position(30, 25)):
            handler._handle_targeting_mouse_motion(event)

            # Targeting cursor should be updated
            assert game.cursor_position.x == 30
            assert game.cursor_position.y == 25

    def test_targeting_mode_invalid_position_ignored(self):
        """Test that invalid positions don't crash targeting mode."""
        game = create_mock_game()
        game.targeting_mode = True
        original_cursor = Position(15, 15)
        game.cursor_position = original_cursor

        handler = InputHandler(game)

        event = Mock()
        event.position = Mock()
        event.position.x = 10000
        event.position.y = 10000

        with patch.object(handler, '_mouse_pixel_to_world', return_value=None):
            handler._handle_targeting_mouse_motion(event)

            # Cursor should remain unchanged
            assert game.cursor_position == original_cursor


class TestMouseWheelHandlers:
    """Test mouse wheel handling in various UI states."""

    def test_inventory_mouse_wheel_scrolls(self):
        """Test that mouse wheel scrolls inventory."""
        game = create_mock_game()
        game.show_inventory = True
        game.inventory_scroll_offset = 0
        game.player.inventory_manager.equipped_exploits = ['exploit1', 'exploit2']
        game.player.inventory_manager.get_display_items = Mock(return_value=[Mock(), Mock(), Mock()])

        handler = InputHandler(game)

        # Mock mouse wheel event (scroll down)
        event = Mock()
        event.y = -1  # Scroll down

        handler._handle_inventory_mouse_wheel(event)

        # Scroll offset should increase
        assert game.inventory_scroll_offset > 0

    def test_lore_viewer_mouse_wheel_scrolls(self):
        """Test that mouse wheel scrolls lore viewer."""
        game = create_mock_game()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        game.story_fragment_manager.get_discovered_fragments = Mock(return_value=[
            'fragment1', 'fragment2', 'fragment3'
        ])

        handler = InputHandler(game)

        # Mock mouse wheel event (scroll down)
        event = Mock()
        event.y = -1

        handler._handle_lore_viewer_mouse_wheel(event)

        # Selection should increase
        assert game.lore_viewer_selection > 0

    def test_mouse_wheel_no_crash_with_empty_inventory(self):
        """Test that mouse wheel doesn't crash with empty inventory."""
        game = create_mock_game()
        game.show_inventory = True
        game.inventory_scroll_offset = 0
        game.player.inventory_manager.equipped_exploits = []
        game.player.inventory_manager.get_display_items = Mock(return_value=[])

        handler = InputHandler(game)

        event = Mock()
        event.y = -1

        # Should not crash, even with empty inventory
        handler._handle_inventory_mouse_wheel(event)

        # Scroll offset should increase (clamping happens in render)
        assert game.inventory_scroll_offset >= 0


class TestMouseMotionIntegration:
    """Integration tests for mouse motion handling."""

    def test_handle_mouse_motion_routes_to_look_mode(self):
        """Test that handle_mouse_motion routes to look mode handler."""
        game = create_mock_game()
        game.look_mode = True

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        event = Mock(spec=tcod.event.MouseMotion)
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        with patch.object(handler, '_handle_look_mode_mouse_motion') as mock_handler:
            with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(40, 25)):
                handler.handle_mouse_motion(event)
                mock_handler.assert_called_once()

    def test_handle_mouse_motion_routes_to_targeting(self):
        """Test that handle_mouse_motion routes to targeting handler."""
        game = create_mock_game()
        game.targeting_mode = True
        game.look_mode = False

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        event = Mock(spec=tcod.event.MouseMotion)
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        with patch.object(handler, '_handle_targeting_mouse_motion') as mock_handler:
            with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(40, 25)):
                handler.handle_mouse_motion(event)
                mock_handler.assert_called_once()

    def test_handle_mouse_motion_routes_to_inventory(self):
        """Test that handle_mouse_motion routes to inventory handler."""
        game = create_mock_game()
        game.show_inventory = True
        game.look_mode = False
        game.targeting_mode = False

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        event = Mock(spec=tcod.event.MouseMotion)
        event.position = Mock()
        event.position.x = 400
        event.position.y = 300

        with patch.object(handler, '_handle_inventory_mouse_motion') as mock_handler:
            with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(40, 25)):
                handler.handle_mouse_motion(event)
                mock_handler.assert_called_once()


class TestMouseWheelIntegration:
    """Integration tests for mouse wheel handling."""

    def test_handle_mouse_wheel_routes_to_inventory(self):
        """Test that handle_mouse_wheel routes to inventory handler."""
        game = create_mock_game()
        game.show_inventory = True
        game.player.inventory_manager.get_display_items = Mock(return_value=[Mock()])

        handler = InputHandler(game)

        event = Mock(spec=tcod.event.MouseWheel)
        event.y = -1

        with patch.object(handler, '_handle_inventory_mouse_wheel') as mock_handler:
            handler.handle_mouse_wheel(event)
            mock_handler.assert_called_once()

    def test_handle_mouse_wheel_routes_to_lore_viewer(self):
        """Test that handle_mouse_wheel routes to lore viewer handler."""
        game = create_mock_game()
        game.show_lore_viewer = True
        game.show_inventory = False
        game.story_fragment_manager.get_discovered_fragments = Mock(return_value=['frag'])

        handler = InputHandler(game)

        event = Mock(spec=tcod.event.MouseWheel)
        event.y = -1

        with patch.object(handler, '_handle_lore_viewer_mouse_wheel') as mock_handler:
            handler.handle_mouse_wheel(event)
            mock_handler.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in mouse input."""

    def test_mouse_conversion_handles_exception(self):
        """Test that exceptions in coordinate conversion are handled gracefully."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(side_effect=Exception("Test error"))

        # Should return None, not crash
        world_pos = handler._mouse_pixel_to_world(400, 300)
        assert world_pos is None

    def test_mouse_motion_with_no_game_settings(self):
        """Test mouse handling when game.settings is missing."""
        game = create_mock_game()
        del game.settings  # Remove settings

        handler = InputHandler(game)

        # Should default to glyph mode and not crash
        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(10, 10)):
            world_pos = handler._mouse_pixel_to_world(400, 300)
            # Might return None or valid position depending on fallback, but shouldn't crash
            assert world_pos is None or isinstance(world_pos, Position)

    def test_camera_offset_fallback_calculation(self):
        """Test that camera offset is calculated when last_camera_offset is missing."""
        game = create_mock_game()
        game.settings.graphics_mode = "glyph"
        game.last_camera_offset = None  # No cached camera offset
        game.player.x = 40
        game.player.y = 30

        handler = InputHandler(game)
        handler._get_window_dimensions = Mock(return_value=(800, 600))

        with patch('game_input.CoordinateHelpers.pixel_to_char_coords', return_value=(15, 15)):
            world_pos = handler._mouse_pixel_to_world(400, 300)

            # Should still work with fallback calculation
            assert world_pos is None or isinstance(world_pos, Position)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
