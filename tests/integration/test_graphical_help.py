"""
Integration Tests for Graphical Help System

Tests the graphical help menu rendering, navigation, and integration
with the graphics/glyph mode setting system.
"""

from unittest.mock import Mock

import pytest
import tcod
import tcod.event

from game_config import GameSettings
from game_menu_help_graphics import GraphicalHelpMenu
from game_menu_help_lore import HelpMenu, create_help_menu


class TestGraphicalHelpFactory:
    """Test the help menu factory function."""

    def test_creates_help_menu_in_glyph_mode(self):
        """Factory should create HelpMenu when in glyph mode."""
        settings = GameSettings()
        settings.graphics_mode = "glyph"

        help_menu = create_help_menu(settings, context=None, tile_manager=None)

        assert isinstance(help_menu, HelpMenu)
        assert not isinstance(help_menu, GraphicalHelpMenu)

    def test_creates_graphical_help_menu_in_graphics_mode(self):
        """Factory should create GraphicalHelpMenu when in graphics mode with tile_manager."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        # Mock context and tile_manager
        mock_context = Mock()
        mock_context.sdl_renderer = Mock()

        mock_tile_manager = Mock()

        help_menu = create_help_menu(settings, context=mock_context, tile_manager=mock_tile_manager)

        assert isinstance(help_menu, GraphicalHelpMenu)

    def test_raises_error_when_tile_manager_missing(self):
        """Factory should raise RuntimeError if tile_manager is None in graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_context = Mock()

        # Should raise RuntimeError with clear message about missing TileManager
        with pytest.raises(RuntimeError) as exc_info:
            create_help_menu(settings, context=mock_context, tile_manager=None)

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "TileManager" in error_msg
        assert "tile_manager is None" in error_msg
        assert "not initialized properly" in error_msg

    def test_raises_error_when_context_missing(self):
        """Factory should raise RuntimeError if context is None in graphics mode."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_tile_manager = Mock()

        # Should raise RuntimeError with clear message about missing context
        with pytest.raises(RuntimeError) as exc_info:
            create_help_menu(settings, context=None, tile_manager=mock_tile_manager)

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "context" in error_msg
        assert "context is None" in error_msg


class TestGraphicalHelpMenuBasics:
    """Test basic GraphicalHelpMenu functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = GameSettings()
        self.settings.graphics_mode = "graphics"

        self.mock_context = Mock()
        self.mock_context.sdl_renderer = Mock()
        self.mock_context.recommended_console_size = Mock(return_value=(1280, 800))
        self.mock_context.sdl_window.size = (1280, 800)

        self.mock_tile_manager = Mock()
        self.mock_tile_manager.tile_width = 20
        self.mock_tile_manager.tile_height = 32

    def test_initialization(self):
        """Test GraphicalHelpMenu initializes correctly."""
        menu = GraphicalHelpMenu(self.mock_context, self.settings, self.mock_tile_manager)

        assert menu.context == self.mock_context
        assert menu.settings == self.settings
        assert menu.tile_manager == self.mock_tile_manager
        assert menu.current_page == 0
        assert not menu.pages_built

    def test_raises_error_when_tile_manager_none(self):
        """Test GraphicalHelpMenu raises error if tile_manager is None."""
        with pytest.raises(ValueError, match="requires a valid TileManager"):
            GraphicalHelpMenu(self.mock_context, self.settings, None)

    def test_builds_pages_on_first_render(self):
        """Test pages are built on first render."""
        menu = GraphicalHelpMenu(self.mock_context, self.settings, self.mock_tile_manager)
        console = tcod.console.Console(80, 50)

        assert not menu.pages_built

        menu.render(console)

        assert menu.pages_built
        assert len(menu.pages) > 0

    def test_page_structure(self):
        """Test pages have correct structure."""
        menu = GraphicalHelpMenu(self.mock_context, self.settings, self.mock_tile_manager)
        console = tcod.console.Console(80, 50)

        menu.render(console)  # Trigger page build

        # Check each page has required keys
        for page in menu.pages:
            assert "title" in page
            assert "sprites" in page
            assert "text_lines" in page
            assert isinstance(page["title"], str)
            assert isinstance(page["sprites"], list)
            assert isinstance(page["text_lines"], list)


class TestGraphicalHelpMenuNavigation:
    """Test navigation between help pages."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = GameSettings()
        self.settings.graphics_mode = "graphics"

        self.mock_context = Mock()
        self.mock_context.sdl_renderer = Mock()
        self.mock_context.recommended_console_size = Mock(return_value=(1280, 800))
        self.mock_context.sdl_window.size = (1280, 800)

        self.mock_tile_manager = Mock()
        self.mock_tile_manager.tile_width = 20
        self.mock_tile_manager.tile_height = 32

        self.menu = GraphicalHelpMenu(self.mock_context, self.settings, self.mock_tile_manager)

        # Build pages
        console = tcod.console.Console(80, 50)
        self.menu.render(console)

    def test_next_page_navigation(self):
        """Test navigating to next page with right arrow."""
        assert self.menu.current_page == 0

        # Simulate right arrow key
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.RIGHT

        result = self.menu.handle_input(event)

        assert result == ""  # Should stay in menu
        assert self.menu.current_page == 1

    def test_previous_page_navigation(self):
        """Test navigating to previous page with left arrow."""
        self.menu.current_page = 2

        # Simulate left arrow key
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.LEFT

        result = self.menu.handle_input(event)

        assert result == ""  # Should stay in menu
        assert self.menu.current_page == 1

    def test_cannot_go_before_first_page(self):
        """Test cannot navigate before first page."""
        assert self.menu.current_page == 0

        # Try to go left from first page
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.LEFT

        self.menu.handle_input(event)

        assert self.menu.current_page == 0  # Should stay at 0

    def test_cannot_go_past_last_page(self):
        """Test cannot navigate past last page."""
        last_page = len(self.menu.pages) - 1
        self.menu.current_page = last_page

        # Try to go right from last page
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.RIGHT

        self.menu.handle_input(event)

        assert self.menu.current_page == last_page  # Should stay at last page

    def test_escape_returns_back(self):
        """Test ESC key returns 'back' to exit help."""
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.ESCAPE

        result = self.menu.handle_input(event)

        assert result == "back"

    def test_up_down_arrows_navigate_pages(self):
        """Test up/down arrows also navigate pages."""
        assert self.menu.current_page == 0

        # Down arrow goes to next page
        event = Mock(spec=tcod.event.KeyDown)
        event.sym = tcod.event.KeySym.DOWN

        self.menu.handle_input(event)
        assert self.menu.current_page == 1

        # Up arrow goes to previous page
        event.sym = tcod.event.KeySym.UP
        self.menu.handle_input(event)
        assert self.menu.current_page == 0


class TestGraphicalHelpMenuRendering:
    """Test rendering behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.settings = GameSettings()
        self.settings.graphics_mode = "graphics"

        self.mock_context = Mock()
        self.mock_context.sdl_renderer = Mock()
        self.mock_context.recommended_console_size = Mock(return_value=(1280, 800))
        self.mock_context.sdl_window.size = (1280, 800)

        self.mock_tile_manager = Mock()
        self.mock_tile_manager.tile_width = 20
        self.mock_tile_manager.tile_height = 32

        # Mock get_tile to return a mock texture
        mock_texture = Mock()
        self.mock_tile_manager.get_tile = Mock(return_value=mock_texture)

        self.menu = GraphicalHelpMenu(self.mock_context, self.settings, self.mock_tile_manager)

    def test_render_creates_console_text(self):
        """Test render method creates text on console."""
        console = tcod.console.Console(80, 50)

        self.menu.render(console)

        # Check that some text was rendered (console should not be empty)
        # At minimum, the title should be rendered
        has_text = False
        for y in range(console.height):
            for x in range(console.width):
                if console.ch[y, x] != 0 and console.ch[y, x] != ord(" "):
                    has_text = True
                    break
            if has_text:
                break

        assert has_text, "Console should have text rendered"

    def test_render_sprites_calls_tile_manager(self):
        """Test render_sprites loads sprites from tile manager."""
        # Build pages first
        console = tcod.console.Console(80, 50)
        self.menu.render(console)

        # Find a page with sprites
        page_with_sprites = None
        for page in self.menu.pages:
            if len(page["sprites"]) > 0:
                page_with_sprites = page
                break

        if page_with_sprites:
            # Navigate to that page
            self.menu.current_page = self.menu.pages.index(page_with_sprites)

            # Reset mock
            self.mock_tile_manager.get_tile.reset_mock()

            # Call render_sprites
            self.menu.render_sprites()

            # Verify get_tile was called for each sprite
            assert self.mock_tile_manager.get_tile.call_count == len(page_with_sprites["sprites"])

    def test_render_sprites_raises_on_missing_sprite(self):
        """Test render_sprites raises error if sprite is missing (no fallback)."""
        # Mock get_tile to return None (sprite not found)
        self.mock_tile_manager.get_tile = Mock(return_value=None)

        # Build pages
        console = tcod.console.Console(80, 50)
        self.menu.render(console)

        # Find a page with sprites
        for i, page in enumerate(self.menu.pages):
            if len(page["sprites"]) > 0:
                self.menu.current_page = i
                break

        # Should raise RuntimeError when sprite is missing
        with pytest.raises(RuntimeError, match="Failed to load sprite"):
            self.menu.render_sprites()


class TestGraphicalHelpMenuSpriteNames:
    """Test that sprite names match the tile manager mappings."""

    def test_enemy_sprite_names_are_capitalized(self):
        """Test enemy sprites use capitalized names (Scanner, not scanner)."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_context = Mock()
        mock_context.sdl_renderer = Mock()
        mock_context.recommended_console_size = Mock(return_value=(1280, 800))

        mock_tile_manager = Mock()
        mock_tile_manager.tile_width = 20
        mock_tile_manager.tile_height = 32
        mock_tile_manager.get_tile = Mock(return_value=Mock())

        menu = GraphicalHelpMenu(mock_context, settings, mock_tile_manager)

        # Build pages
        console = tcod.console.Console(80, 50)
        menu.render(console)

        # Find Items & Enemies page (enemies are now on Page 2)
        items_enemies_page = None
        for page in menu.pages:
            if "ITEMS" in page["title"] and "ENEMIES" in page["title"]:
                items_enemies_page = page
                break

        assert items_enemies_page is not None, "Items & Enemies page should exist"

        # Collect all sprite names
        all_sprites = [sprite_data[0] for sprite_data in items_enemies_page["sprites"]]

        # Filter to only enemy sprites (capitalized names)
        enemy_sprites = [name for name in all_sprites if name[0].isupper()]

        # Check all enemies are present and correctly capitalized
        expected_enemies = [
            "Scanner",
            "Patrol",
            "Bot",
            "Firewall",
            "Hunter",
            "Virus",
            "Inhibitor",
            "Admin Avatar",
        ]

        # Verify all expected enemies are in the sprite list
        for expected in expected_enemies:
            assert (
                expected in enemy_sprites
            ), f"Expected enemy '{expected}' not found in sprite list"

        # Verify only expected enemies are present (no extras)
        for sprite_name in enemy_sprites:
            assert sprite_name in expected_enemies, f"Unexpected enemy sprite '{sprite_name}' found"

    def test_items_enemies_page_has_correct_sprites(self):
        """Test Items & Enemies page has correct sprites (items lowercase, enemies capitalized)."""
        settings = GameSettings()
        settings.graphics_mode = "graphics"

        mock_context = Mock()
        mock_context.sdl_renderer = Mock()
        mock_context.recommended_console_size = Mock(return_value=(1280, 800))

        mock_tile_manager = Mock()
        mock_tile_manager.tile_width = 20
        mock_tile_manager.tile_height = 32
        mock_tile_manager.get_tile = Mock(return_value=Mock())

        menu = GraphicalHelpMenu(mock_context, settings, mock_tile_manager)

        # Build pages
        console = tcod.console.Console(80, 50)
        menu.render(console)

        # Find Items & Enemies page (Page 2/3)
        items_enemies_page = None
        for page in menu.pages:
            if "ITEMS" in page["title"] and "ENEMIES" in page["title"]:
                items_enemies_page = page
                break

        assert items_enemies_page is not None, "Items & Enemies page should exist"

        # Collect all sprite names on page
        all_sprites = [sprite_data[0] for sprite_data in items_enemies_page["sprites"]]

        # Expected lowercase sprites (items, nodes, upgrades) - updated for new layout
        expected_lowercase = [
            "codehack",
            "exploit",
            "cpu_node",
            "cooling_node",
            "ghost_node",
            "cpu_upgrade",
            "ram_upgrade",
            "cooling_upgrade",
        ]

        # Expected capitalized sprites (enemies)
        expected_capitalized = [
            "Scanner",
            "Firewall",
            "Patrol",
            "Bot",
            "Hunter",
            "Virus",
            "Inhibitor",
            "Admin Avatar",
        ]

        # Verify all expected sprites are present
        for sprite_name in expected_lowercase + expected_capitalized:
            assert sprite_name in all_sprites, f"Expected sprite '{sprite_name}' not found in page"

        # Verify no unexpected sprites
        for sprite_name in all_sprites:
            assert (
                sprite_name in expected_lowercase + expected_capitalized
            ), f"Unexpected sprite '{sprite_name}' found in page"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
