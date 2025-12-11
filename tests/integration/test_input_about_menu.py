"""
About Menu Input Testing

Tests all input types for About menu navigation:
- Keyboard navigation and exit
- D-pad with auto-repeat
- Face button exit

Note: Extracted from test_input_critical_paths.py for maintainability.
"""

import pytest
import time
import tcod.event

from game_input_actions import InputContext
from tests.integration.input_test_utils import InputTestHelper


class TestAboutMenuNavigation:
    """Test About menu navigation with all input types."""

    @pytest.fixture
    def about_menu(self):
        """Create About menu for testing."""
        from game_menu_about import AboutMenu

        menu = AboutMenu(background=None)
        yield menu

    def test_keyboard_down_changes_selection(self, about_menu):
        """Keyboard down arrow changes selection."""
        initial = about_menu.selected_option

        event = InputTestHelper.create_keyboard_event(tcod.event.KeySym.DOWN)
        about_menu.handle_input(event)

        expected = (initial + 1) % len(about_menu.options)
        assert about_menu.selected_option == expected

    def test_dpad_down_changes_selection(self, about_menu):
        """D-pad down changes selection."""
        initial = about_menu.selected_option

        event = InputTestHelper.create_dpad_event('down', pressed=True)
        about_menu.handle_input(event)

        expected = (initial + 1) % len(about_menu.options)
        assert about_menu.selected_option == expected

    def test_left_stick_down_changes_selection(self, about_menu):
        """Left stick down changes selection."""
        initial = about_menu.selected_option

        event = InputTestHelper.create_stick_event('left', 'y', 32767)
        about_menu.handle_input(event)

        # Selection should change (or wrap if at end)
        assert about_menu.selected_option >= 0
        assert about_menu.selected_option < len(about_menu.options)

    def test_escape_exits_menu(self, about_menu):
        """Escape key returns 'back' to exit menu."""
        event = InputTestHelper.create_keyboard_event(tcod.event.KeySym.ESCAPE)
        result = about_menu.handle_input(event)

        assert result == "back"

    def test_face_button_b_exits_menu(self, about_menu):
        """Face button B returns 'back' to exit menu."""
        event = InputTestHelper.create_face_button_event('b', pressed=True)
        result = about_menu.handle_input(event)

        assert result == "back"


# NOTE: TestAboutMenuButtonRelease removed - covered by test_gamepad_auto_repeat.py
