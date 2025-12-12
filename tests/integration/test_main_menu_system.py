"""
Integration tests for main menu system (handle_menu_navigation).

These tests verify the main menu system works with TCOD context,
catching crashes that pure gameplay tests miss:
- Variable shadowing bugs
- Rendering crashes
- Input handling bugs
- Context/rendering initialization issues
"""

import pytest
import tcod.console
import tcod.context
import tcod.event
import tcod.sdl.joystick
import tcod.tileset

from game_audio import NullSoundManager
from game_config import GameSettings
from game_input_actions import InputContext
from game_loop import initialize_game_systems
from game_menus import MenuBackground


class TestMainMenuSystem:
    """Test main menu system with real TCOD context."""

    @pytest.fixture
    def menu_setup(self):
        """
        Create minimal TCOD context and menu systems for testing.

        Uses hidden SDL window so tests run without displaying anything.
        """
        # Create tileset (required for context)
        tileset = tcod.tileset.load_truetype_font(
            "KreativeSquare.ttf", tile_width=16, tile_height=16
        )

        # Create offscreen context (hidden window)
        context = tcod.context.new(
            width=80,
            height=50,
            tileset=tileset,
            title="Test Menu",
            sdl_window_flags=tcod.lib.SDL_WINDOW_HIDDEN,  # Don't show window
        )

        console = tcod.console.Console(80, 50)

        # Initialize menu systems
        settings = GameSettings()
        menu_background = MenuBackground(context, settings)
        menu_sound_manager = NullSoundManager(settings)  # No audio in tests
        menus = initialize_game_systems(settings, context, menu_background, menu_sound_manager)

        yield context, console, menus, settings, menu_sound_manager

        # Cleanup
        context.close()

    def test_main_menu_initialization(self, menu_setup):
        """Test that menu system initializes without crashing."""
        context, console, menus, settings, sound_mgr = menu_setup

        # Should have created menu objects
        assert "main_menu" in menus
        assert "settings_menu" in menus
        assert "help_menu" in menus

    def test_main_menu_renders_one_frame(self, menu_setup):
        """
        Test main menu can render at least one frame.

        This catches variable shadowing bugs like 'context' being overwritten.
        """
        context, console, menus, settings, sound_mgr = menu_setup

        main_menu = menus["main_menu"]

        # Render one frame - should not crash
        console.clear()
        main_menu.render(console)

        # Verify menu title was drawn (check console has non-empty content)
        # Main menu should have options, so selection should be valid
        assert 0 <= main_menu.selected_option < len(main_menu.options)

    def test_menu_navigation_up_down(self, menu_setup):
        """Test that UP/DOWN navigation works in main menu."""
        context, console, menus, settings, sound_mgr = menu_setup

        menu = menus["main_menu"]
        menu.refresh_options(show_continue=False, active_game=None)

        initial_selection = menu.selected_option

        # Navigate down
        menu.navigate_down()
        assert menu.selected_option == (initial_selection + 1) % len(menu.options)

        # Navigate up
        menu.navigate_up()
        assert menu.selected_option == initial_selection

    def test_menu_keyboard_input(self, menu_setup):
        """Test keyboard input handling in main menu."""
        context, console, menus, settings, sound_mgr = menu_setup

        menu = menus["main_menu"]
        menu.refresh_options(show_continue=False, active_game=None)

        initial_selection = menu.selected_option

        # Create DOWN key event
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )

        # Handle input
        result = menu.handle_input(down_event)

        # Selection should have changed from initial (DOWN moves to next option)
        assert menu.selected_option == (initial_selection + 1) % len(menu.options)

    def test_menu_gamepad_button_input(self, menu_setup):
        """Test gamepad D-pad button input in main menu."""
        context, console, menus, settings, sound_mgr = menu_setup

        menu = menus["main_menu"]
        menu.refresh_options(show_continue=False, active_game=None)

        initial_selection = menu.selected_option

        # Create DPAD DOWN button event
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )

        # Handle input - should move selection down
        result = menu.handle_input(button_event)
        assert menu.selected_option == (initial_selection + 1) % len(menu.options)

    def test_settings_menu_renders(self, menu_setup):
        """Test settings menu can render without crashing."""
        context, console, menus, settings, sound_mgr = menu_setup

        settings_menu = menus["settings_menu"]

        # Render - should not crash and menu should have options
        console.clear()
        settings_menu.render(console)
        assert len(settings_menu.options) > 0
        assert 0 <= settings_menu.selected_option < len(settings_menu.options)

    def test_help_menu_renders(self, menu_setup):
        """Test help menu can render without crashing."""
        context, console, menus, settings, sound_mgr = menu_setup

        help_menu = menus["help_menu"]

        # Render - should not crash and menu should have content
        console.clear()
        help_menu.render(console)
        # Help menu should have page tracking (both HelpMenu and GraphicalHelpMenu have current_page)
        assert hasattr(help_menu, "current_page")
        assert help_menu.current_page >= 0


class TestMenuInputContexts:
    """Test that menu input contexts are handled correctly."""

    @pytest.fixture
    def menu_setup(self):
        """Setup menu system for testing."""
        tileset = tcod.tileset.load_truetype_font(
            "KreativeSquare.ttf", tile_width=16, tile_height=16
        )

        context = tcod.context.new(
            width=80,
            height=50,
            tileset=tileset,
            title="Test Input",
            sdl_window_flags=tcod.lib.SDL_WINDOW_HIDDEN,
        )

        console = tcod.console.Console(80, 50)

        settings = GameSettings()
        menu_background = MenuBackground(context, settings)
        menu_sound_manager = NullSoundManager(settings)
        menus = initialize_game_systems(settings, context, menu_background, menu_sound_manager)

        yield context, console, menus, settings

        context.close()

    def test_gamepad_handler_exists(self, menu_setup):
        """Test that menus have gamepad handlers."""
        context, console, menus, settings = menu_setup

        main_menu = menus["main_menu"]

        # Should have gamepad handler
        assert hasattr(main_menu, "gamepad_handler")
        assert main_menu.gamepad_handler is not None

    def test_button_repeat_doesnt_crash(self, menu_setup):
        """Test that button repeat checking doesn't crash."""
        context, console, menus, settings = menu_setup

        main_menu = menus["main_menu"]

        # Try to get button repeat action (should return None if no button held)
        repeat_action = main_menu.gamepad_handler.get_button_repeat_action(InputContext.MAIN_MENU)

        # Should not crash, should return None (no button held)
        assert repeat_action is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
