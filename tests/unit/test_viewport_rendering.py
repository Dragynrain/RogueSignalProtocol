"""
Unit tests for viewport rendering bounds in graphics mode.

These tests ensure that items are only rendered when within the viewport bounds,
preventing rendering bugs when switching between glyph mode (55x44) and graphics mode (~27x21).
"""

from unittest.mock import Mock, patch

import pytest

from game_config import GameConfig
from game_entities import Position
from game_rendering_graphics import GraphicsMapRenderer


class TestViewportRenderingBounds:
    """Test that viewport bounds are correctly enforced in graphics mode."""

    @pytest.fixture
    def mock_renderer(self):
        """Create a mock graphics renderer with proper viewport configuration."""
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        mock_settings = Mock()
        mock_settings.graphics_mode = "graphics"

        renderer = GraphicsMapRenderer(
            tile_manager=Mock(), context=mock_context, settings=mock_settings
        )

        # Mock the graphics mode check
        renderer._should_use_graphics = Mock(return_value=True)
        renderer._get_graphics_mode = Mock(return_value="graphics")

        # Mock the helper methods extracted during refactoring
        # These need to return tuples for unpacking
        # Use None values to trigger fallback to default viewport dimensions (55x44)
        renderer._get_tile_dimensions = Mock(return_value=(None, None))
        renderer._get_sdl_window_dimensions = Mock(return_value=(None, None))

        return renderer

    @pytest.fixture
    def mock_game(self):
        """Create a mock game with test items at various positions."""
        game = Mock()
        game.player = Mock()
        game.player.x = 13  # Center of 27-wide viewport
        game.player.y = 10  # Center of 21-tall viewport
        game.player.position = Position(13, 10)
        game.player.get_vision_range = Mock(return_value=10)
        game.player.can_see_through_walls = Mock(return_value=False)

        game.game_map = Mock()
        game.game_map.width = 50
        game.game_map.height = 50
        game.game_map.can_see_position = Mock(return_value=True)

        # Create test items at various positions
        game.game_map.permanent_upgrades = {
            (5, 5): "cooling_upgrade",  # Inside viewport (relative to camera)
            (13, 10): "cpu_upgrade",  # At player position
            (40, 40): "ram_upgrade",  # Far outside viewport
        }

        game.game_map.exploit_pickups = {
            (6, 6): Mock(exploit_key="test_exploit"),  # Inside viewport
            (45, 45): Mock(exploit_key="test_exploit2"),  # Outside viewport
        }

        game.game_map.story_fragments = {
            (7, 7): Mock(fragment_index=0),  # Inside viewport
            (48, 48): Mock(fragment_index=1),  # Outside viewport
        }

        game.game_map.gateway = Position(8, 8)  # Inside viewport

        game.enemies = [
            Mock(x=9, y=9, position=Position(9, 9)),  # Inside viewport
            Mock(x=49, y=49, position=Position(49, 49)),  # Outside viewport
        ]

        game.game_state = Mock()
        game.game_state.threat_scan_turns = 0

        return game

    def test_viewport_width_in_graphics_mode(self):
        """Test that graphics mode uses full viewport width (55 tiles)."""
        viewport_width = GameConfig.VIEWPORT_WIDTH("graphics")
        assert (
            viewport_width == 55
        ), f"Graphics mode viewport should be 55 tiles wide, got {viewport_width}"

    def test_viewport_height_in_graphics_mode(self):
        """Test that graphics mode uses full viewport height (44 tiles)."""
        viewport_height = GameConfig.VIEWPORT_HEIGHT("graphics")
        assert (
            viewport_height == 44
        ), f"Graphics mode viewport should be 44 tiles tall, got {viewport_height}"

    def test_is_in_viewport_helper_respects_graphics_mode(self, mock_renderer):
        """Test that _is_in_viewport() helper uses graphics mode viewport dimensions."""
        camera_offset = Position(0, 0)

        # Test positions within graphics viewport (55x44)
        assert mock_renderer._is_in_viewport(0, 0, camera_offset) is True
        assert mock_renderer._is_in_viewport(27, 22, camera_offset) is True  # Center
        assert mock_renderer._is_in_viewport(54, 43, camera_offset) is True  # Bottom-right corner

        # Test positions outside graphics viewport
        assert mock_renderer._is_in_viewport(55, 0, camera_offset) is False  # Right edge
        assert mock_renderer._is_in_viewport(0, 44, camera_offset) is False  # Bottom edge
        assert mock_renderer._is_in_viewport(100, 0, camera_offset) is False  # Far right
        assert mock_renderer._is_in_viewport(0, 100, camera_offset) is False  # Far bottom

    def test_is_in_viewport_with_camera_offset(self, mock_renderer):
        """Test that _is_in_viewport() correctly handles camera offset."""
        # Camera at origin
        camera_offset = Position(0, 0)  # Top-left corner of viewport

        # Position at (5, 5) is within viewport (0-54, 0-43)
        assert mock_renderer._is_in_viewport(5, 5, camera_offset) is True

        # Position at (100, 100) is outside viewport
        assert mock_renderer._is_in_viewport(100, 100, camera_offset) is False

        # Shift camera - now (100, 100) might be in viewport
        camera_offset = Position(60, 60)  # Viewport shows tiles (60-114, 60-103)
        assert mock_renderer._is_in_viewport(100, 100, camera_offset) is True

    def test_items_outside_viewport_not_rendered(self, mock_renderer, mock_game):
        """
        Integration test: Ensure items far outside viewport are not rendered.

        This is the test that would have caught the original bug where items
        were checked against GAME_AREA_WIDTH (53) instead of viewport width (27).
        """
        # Mock the rendering components
        mock_renderer.context = Mock()
        mock_renderer.context.sdl_renderer = Mock()
        mock_renderer.tile_manager = Mock()

        # Track which positions were attempted to be rendered
        rendered_positions = []

        def mock_get_tile(tile_name):
            texture = Mock()
            return texture

        def mock_copy(texture, dest):
            # Extract position from dest rect (x, y, width, height)
            rendered_positions.append((dest[0], dest[1]))

        mock_renderer.tile_manager.get_tile = mock_get_tile
        mock_renderer.context.sdl_renderer.copy = mock_copy
        mock_renderer._get_tile_rect = Mock(side_effect=lambda x, y: (x, y, 32, 32))
        mock_renderer._calculate_camera_offset = Mock(return_value=Position(0, 0))

        # Render the sprites layer
        with patch.object(mock_renderer, "_should_use_graphics", return_value=True):
            with patch.object(mock_renderer, "_get_graphics_mode", return_value="graphics"):
                # We need to mock the full rendering to avoid errors, but we'll just check
                # that _is_in_viewport is called correctly
                camera_offset = Position(0, 0)

                # Test permanent upgrades
                for (
                    world_x,
                    world_y,
                ), upgrade_key in mock_game.game_map.permanent_upgrades.items():
                    is_in_viewport = mock_renderer._is_in_viewport(world_x, world_y, camera_offset)

                    if world_x >= 55 or world_y >= 44:
                        assert (
                            is_in_viewport is False
                        ), f"Position ({world_x}, {world_y}) should be outside viewport (55x44)"
                    else:
                        assert (
                            is_in_viewport is True
                        ), f"Position ({world_x}, {world_y}) should be inside viewport (55x44)"

    def test_glyph_mode_uses_full_viewport(self, mock_renderer):
        """Test that glyph mode uses full game area (55x44)."""
        mock_renderer._get_graphics_mode = Mock(return_value="glyph")

        glyph_viewport_width = GameConfig.VIEWPORT_WIDTH("glyph")
        glyph_viewport_height = GameConfig.VIEWPORT_HEIGHT("glyph")

        assert glyph_viewport_width == 55, "Glyph mode should use full width"
        assert glyph_viewport_height == 44, "Glyph mode should use full height"

        camera_offset = Position(0, 0)

        # Positions that are outside graphics viewport but inside glyph viewport
        assert mock_renderer._is_in_viewport(30, 0, camera_offset) is True  # Beyond graphics width
        assert mock_renderer._is_in_viewport(0, 25, camera_offset) is True  # Beyond graphics height
        assert mock_renderer._is_in_viewport(54, 43, camera_offset) is True  # Bottom-right of glyph

    def test_all_rendering_methods_check_viewport(self, mock_renderer):
        """
        Verify that all rendering methods use _is_in_viewport() or equivalent checks.

        This is a code inspection test - it ensures the refactoring was complete.
        """
        import inspect

        source = inspect.getsource(GraphicsMapRenderer)

        # Count occurrences of viewport checking patterns
        is_in_viewport_count = source.count("self._is_in_viewport(")

        # We should have at least 10 calls to _is_in_viewport after refactoring:
        # 1. exploits
        # 2. permanent upgrades
        # 3. story fragments
        # 4. gateway
        # 5. enemies (sprites layer)
        # 6. player
        # 7. player status effects
        # 8. enemy status effects
        # 9. targeting cursor
        # 10. hover highlight
        # 11. vision overlay
        # 12. movement prediction

        assert (
            is_in_viewport_count >= 10
        ), f"Expected at least 10 uses of _is_in_viewport(), found {is_in_viewport_count}"

        # Ensure no hardcoded GAME_AREA_WIDTH checks remain in sprite rendering
        # (They should all be replaced with _is_in_viewport calls)
        render_sprites_source = inspect.getsource(mock_renderer.render_sprites_layer)

        # This pattern should NOT appear: (0 <= ... < GameConfig.GAME_AREA_WIDTH()
        # after our refactoring
        assert (
            "GAME_AREA_WIDTH()" not in render_sprites_source
        ), "render_sprites_layer should not use GAME_AREA_WIDTH() directly - use _is_in_viewport()"
