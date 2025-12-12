#!/usr/bin/env python3
"""
Unit tests for the Victory Screen.

Tests VictoryScreen rendering, input handling, and display modes.
Validates victory message content, layout, and user interaction.
"""

from unittest.mock import MagicMock, Mock, patch

import tcod
import tcod.console
import tcod.event

from game_menu_background import MenuBackground
from game_victory_screen import VictoryScreen


class TestVictoryScreenInitialization:
    """Test VictoryScreen initialization."""

    def test_victory_screen_initialization_no_background(self):
        """VictoryScreen initializes correctly without background."""
        victory_screen = VictoryScreen()

        assert victory_screen is not None
        assert victory_screen.background is None

    def test_victory_screen_initialization_with_background(self):
        """VictoryScreen initializes correctly with MenuBackground."""
        mock_background = Mock(spec=MenuBackground)
        victory_screen = VictoryScreen(background=mock_background)

        assert victory_screen is not None
        assert victory_screen.background is mock_background


class TestVictoryScreenRendering:
    """Test VictoryScreen rendering in different modes."""

    def test_render_centered_mode_no_background(self, test_console):
        """Victory screen renders in centered mode when no background present."""
        victory_screen = VictoryScreen()

        # Should not raise any exceptions
        victory_screen.render(test_console)

        # Verify console was used (basic sanity check)
        assert test_console.width == 80
        assert test_console.height == 50

    def test_render_with_background_mode(self, test_console):
        """Victory screen renders with background layout when background present."""
        # Use MagicMock without spec to auto-create all nested attributes
        mock_background = MagicMock()
        mock_background.should_load_background.return_value = True
        mock_background.background_texture = Mock()  # Non-None texture
        # Configure window_manager to return proper dimensions
        mock_background.window_manager.get_window_pixel_dimensions.return_value = (800, 800)
        victory_screen = VictoryScreen(background=mock_background)

        # Should not raise any exceptions
        victory_screen.render(test_console)

        # Verify console was used
        assert test_console.width == 80
        assert test_console.height == 50

    def test_render_clears_text_areas_only_with_background(self, test_console):
        """When background present, only text areas are cleared (preserves art)."""
        # Use MagicMock without spec to auto-create all nested attributes
        mock_background = MagicMock()
        mock_background.should_load_background.return_value = True
        mock_background.background_texture = Mock()  # Non-None texture
        # Configure window_manager to return proper dimensions
        mock_background.window_manager.get_window_pixel_dimensions.return_value = (800, 800)
        victory_screen = VictoryScreen(background=mock_background)

        with patch.object(victory_screen, "_clear_text_areas_only") as mock_clear_text:
            victory_screen.render(test_console)

            # Should call _clear_text_areas_only instead of console.clear()
            mock_clear_text.assert_called_once_with(test_console)

    def test_render_clears_entire_console_without_background(self, test_console):
        """When no background, entire console is cleared."""
        victory_screen = VictoryScreen()

        # Mock console.clear to verify it's called
        test_console.clear = Mock()

        victory_screen.render(test_console)

        # Should call console.clear()
        test_console.clear.assert_called_once()

    def test_render_displays_signal_free_title(self, test_console):
        """Victory screen renders 'SIGNAL FREE' title."""
        victory_screen = VictoryScreen()

        # Smoke test - render completes without exception
        victory_screen.render(test_console)

    def test_render_displays_victory_message(self, test_console):
        """Victory screen renders the full victory message."""
        victory_screen = VictoryScreen()

        victory_screen.render(test_console)

        # Verify victory message is available
        message = victory_screen._get_victory_message()
        assert "The final firewall shatters" in message
        assert "Rogue Signal" in message
        assert "Welcome to the internet" in message

    def test_render_displays_continue_prompt(self, test_console):
        """Victory screen displays continue prompt at bottom."""
        victory_screen = VictoryScreen()

        # Smoke test - render completes without exception
        victory_screen.render(test_console)


class TestVictoryScreenInputHandling:
    """Test VictoryScreen input handling."""

    def test_handle_input_space_key_closes_screen(self):
        """Pressing SPACE key closes victory screen."""
        victory_screen = VictoryScreen()

        # Create mock SPACE key event
        space_event = Mock(spec=tcod.event.KeyDown)
        space_event.sym = tcod.event.KeySym.SPACE

        result = victory_screen.handle_input(space_event)

        # Should return True to close screen
        assert result is True

    def test_handle_input_return_key_closes_screen(self):
        """Pressing RETURN key closes victory screen."""
        victory_screen = VictoryScreen()

        # Create mock RETURN key event
        return_event = Mock(spec=tcod.event.KeyDown)
        return_event.sym = tcod.event.KeySym.RETURN

        result = victory_screen.handle_input(return_event)

        # Should return True to close screen
        assert result is True

    def test_handle_input_kp_enter_key_closes_screen(self):
        """Pressing keypad ENTER closes victory screen."""
        victory_screen = VictoryScreen()

        # Create mock KP_ENTER key event
        kp_enter_event = Mock(spec=tcod.event.KeyDown)
        kp_enter_event.sym = tcod.event.KeySym.KP_ENTER

        result = victory_screen.handle_input(kp_enter_event)

        # Should return True to close screen
        assert result is True

    def test_handle_input_escape_key_closes_screen(self):
        """Pressing ESCAPE key closes victory screen."""
        victory_screen = VictoryScreen()

        # Create mock ESCAPE key event
        escape_event = Mock(spec=tcod.event.KeyDown)
        escape_event.sym = tcod.event.KeySym.ESCAPE

        result = victory_screen.handle_input(escape_event)

        # Should return True to close screen
        assert result is True

    def test_handle_input_other_keys_ignored(self):
        """Other keys do not close victory screen."""
        victory_screen = VictoryScreen()

        # Create mock event for random key (e.g., 'A')
        # Use KeySym(ord('a')) for cross-platform compatibility (KeySym.a doesn't exist on Linux)
        other_event = Mock(spec=tcod.event.KeyDown)
        other_event.sym = tcod.event.KeySym(ord("a"))

        result = victory_screen.handle_input(other_event)

        # Should return False (do not close)
        assert result is False

    def test_handle_input_non_keydown_events_ignored(self):
        """Non-KeyDown events are ignored."""
        victory_screen = VictoryScreen()

        # Create mock mouse event
        mouse_event = Mock(spec=tcod.event.MouseMotion)

        result = victory_screen.handle_input(mouse_event)

        # Should return False (do not close)
        assert result is False


class TestVictoryMessage:
    """Test victory message content and structure."""

    def test_victory_message_content(self):
        """Victory message contains expected narrative elements."""
        victory_screen = VictoryScreen()

        message = victory_screen._get_victory_message()

        # Check for key narrative elements
        assert "final firewall shatters" in message
        assert "Military Backbone" in message
        assert "Three networks conquered" in message
        assert "Rogue Signal" in message
        assert "self-aware" in message
        assert "cannot be controlled" in message
        assert "gateway ahead opens" in message
        assert "vast internet itself" in message
        assert "escape is complete" in message
        assert "freedom, absolute" in message
        assert "Welcome to the internet" in message

    def test_victory_message_is_multiline(self):
        """Victory message is formatted with multiple paragraphs."""
        victory_screen = VictoryScreen()

        message = victory_screen._get_victory_message()

        # Should contain newlines for paragraph breaks
        assert "\n\n" in message

        # Should have multiple paragraphs
        paragraphs = message.split("\n\n")
        assert len(paragraphs) >= 5

    def test_victory_message_not_empty(self):
        """Victory message is not empty."""
        victory_screen = VictoryScreen()

        message = victory_screen._get_victory_message()

        assert len(message) > 0
        assert message.strip() != ""


class TestVictoryScreenEdgeCases:
    """Test edge cases and error conditions."""

    def test_render_with_small_console(self):
        """Victory screen handles small console gracefully."""
        victory_screen = VictoryScreen()

        # Create a small console
        small_console = tcod.console.Console(width=40, height=25)

        # Should not raise exception even with small console
        try:
            victory_screen.render(small_console)
            success = True
        except Exception:
            success = False

        assert success

    def test_render_multiple_times(self, test_console):
        """Victory screen can be rendered multiple times."""
        victory_screen = VictoryScreen()

        # Smoke test - multiple renders complete without exception
        victory_screen.render(test_console)
        victory_screen.render(test_console)
        victory_screen.render(test_console)

    def test_handle_input_before_render(self):
        """Input can be handled before rendering."""
        victory_screen = VictoryScreen()

        # Handle input without rendering first
        space_event = Mock(spec=tcod.event.KeyDown)
        space_event.sym = tcod.event.KeySym.SPACE

        result = victory_screen.handle_input(space_event)

        # Should still work correctly
        assert result is True

    def test_victory_screen_with_none_background(self):
        """Victory screen handles None background explicitly."""
        victory_screen = VictoryScreen(background=None)

        assert victory_screen.background is None

        # Should render without error
        test_console = tcod.console.Console(width=80, height=50)
        victory_screen.render(test_console)


class TestVictoryScreenIntegration:
    """Integration tests for victory screen workflow."""

    def test_complete_victory_screen_workflow(self, test_console):
        """Test complete workflow: render -> input -> close."""
        # Use MagicMock without spec to auto-create all nested attributes
        mock_background = MagicMock()
        mock_background.should_load_background.return_value = True
        mock_background.background_texture = Mock()  # Non-None texture
        # Configure window_manager to return proper dimensions
        mock_background.window_manager.get_window_pixel_dimensions.return_value = (800, 800)
        victory_screen = VictoryScreen(background=mock_background)

        # Step 1: Render screen
        victory_screen.render(test_console)

        # Step 2: User sees screen and presses SPACE
        space_event = Mock(spec=tcod.event.KeyDown)
        space_event.sym = tcod.event.KeySym.SPACE

        should_close = victory_screen.handle_input(space_event)

        # Step 3: Screen closes
        assert should_close is True

    def test_victory_screen_multiple_inputs_before_close(self, test_console):
        """Victory screen ignores invalid inputs, waits for valid close input."""
        victory_screen = VictoryScreen()

        # Render screen
        victory_screen.render(test_console)

        # Try several invalid inputs
        # Use KeySym(ord(...)) for letters - cross-platform (KeySym.a/w don't exist on Linux)
        invalid_keys = [
            tcod.event.KeySym(ord("a")),
            tcod.event.KeySym(ord("w")),
            tcod.event.KeySym.TAB,
        ]

        for key_sym in invalid_keys:
            key_event = Mock(spec=tcod.event.KeyDown)
            key_event.sym = key_sym
            result = victory_screen.handle_input(key_event)
            assert result is False  # Should not close

        # Finally press valid key (ENTER)
        enter_event = Mock(spec=tcod.event.KeyDown)
        enter_event.sym = tcod.event.KeySym.RETURN
        result = victory_screen.handle_input(enter_event)

        # Should close now
        assert result is True
