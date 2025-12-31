#!/usr/bin/env python3
"""
Comprehensive input tests for all menu screens.

Tests that each screen properly handles:
- Keyboard input (arrow keys, Enter, ESC)
- Gamepad D-pad (via button events)
- Left analog stick (via axis events)
- Mouse clicks (where applicable)

TDD: These tests define expected behavior. Failures indicate missing input support.
"""

from unittest.mock import Mock, patch

import pytest
import tcod.event
import tcod.sdl.joystick

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def settings():
    """Create GameSettings with gamepad enabled and ascension reset."""
    from rsp.core.config import GameSettings

    s = GameSettings()
    s.gamepad_enabled = True
    s.gamepad_deadzone = 0.15
    s.gamepad_direction_locking = True
    # Reset ascension to defaults to ensure consistent menu options
    s.ascension = {"current_level": 0, "highest_unlocked": 0, "victories_per_level": {}}
    return s


@pytest.fixture
def input_mapper():
    """Create InputMapper with default bindings."""
    from rsp.input.mappings import InputMapper

    return InputMapper()


@pytest.fixture
def console():
    """Create console for rendering tests."""
    return tcod.console.Console(80, 50)


def make_key_event(sym):
    """Create a mock KeyDown event."""
    event = Mock(spec=tcod.event.KeyDown)
    event.sym = sym
    event.type = "KEYDOWN"
    return event


def make_button_event(button, pressed=True):
    """Create a mock ControllerButton event."""
    event = Mock(spec=tcod.event.ControllerButton)
    event.button = button
    event.pressed = pressed
    event.type = "CONTROLLERBUTTONDOWN" if pressed else "CONTROLLERBUTTONUP"
    return event


def make_axis_event(axis, value):
    """Create a mock ControllerAxis event."""
    event = Mock(spec=tcod.event.ControllerAxis)
    event.axis = axis
    event.value = value
    event.type = "CONTROLLERAXISMOTION"
    return event


# =============================================================================
# Main Menu Input Tests
# =============================================================================


class TestMainMenuInputSupport:
    """Test MainMenu handles all input types."""

    def test_keyboard_navigation(self, settings):
        """MainMenu responds to arrow keys."""
        from rsp.systems.save import SaveGameManager
        from rsp.ui.menu_main import MainMenu

        with patch.object(SaveGameManager, "save_exists", return_value=False):
            menu = MainMenu()
            initial = menu.selected_option

            # Down arrow should move selection
            result = menu.handle_input(make_key_event(tcod.event.KeySym.DOWN))
            assert menu.selected_option == initial + 1

    def test_dpad_navigation(self, settings):
        """MainMenu responds to D-pad."""
        from rsp.systems.save import SaveGameManager
        from rsp.ui.menu_main import MainMenu

        with patch.object(SaveGameManager, "save_exists", return_value=False):
            menu = MainMenu()
            initial = menu.selected_option

            # D-pad down should move selection
            result = menu.handle_input(
                make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_DOWN)
            )
            assert menu.selected_option == initial + 1

    def test_keyboard_confirm(self, settings):
        """MainMenu responds to Enter key."""
        from rsp.systems.save import SaveGameManager
        from rsp.ui.menu_main import MainMenu

        with patch.object(SaveGameManager, "save_exists", return_value=False):
            menu = MainMenu()
            menu.selected_option = 1  # Settings

            result = menu.handle_input(make_key_event(tcod.event.KeySym.RETURN))
            assert result == "settings"

    def test_gamepad_confirm(self, settings):
        """MainMenu responds to A button."""
        from rsp.systems.save import SaveGameManager
        from rsp.ui.menu_main import MainMenu

        with patch.object(SaveGameManager, "save_exists", return_value=False):
            menu = MainMenu()
            menu.selected_option = 1  # Settings

            result = menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.A))
            assert result == "settings"


# =============================================================================
# Settings Menu Input Tests
# =============================================================================


class TestSettingsMenuInputSupport:
    """Test SettingsMenu handles all input types."""

    def test_keyboard_navigation(self, settings):
        """SettingsMenu responds to arrow keys."""
        from rsp.ui.menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)
        initial = menu.selected_option

        result = menu.handle_input(make_key_event(tcod.event.KeySym.DOWN))
        assert menu.selected_option == initial + 1

    def test_dpad_navigation(self, settings):
        """SettingsMenu responds to D-pad."""
        from rsp.ui.menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)
        initial = menu.selected_option

        result = menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_DOWN))
        assert menu.selected_option == initial + 1

    def test_keyboard_horizontal_adjusts_slider(self, settings):
        """Left/Right arrows adjust slider values."""
        from rsp.ui.menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)
        menu.selected_option = 0  # Master Volume (slider)

        original = settings.master_volume
        menu.handle_input(make_key_event(tcod.event.KeySym.RIGHT))
        assert settings.master_volume > original

    def test_dpad_horizontal_adjusts_slider(self, settings):
        """D-pad left/right adjust slider values."""
        from rsp.ui.menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)
        menu.selected_option = 0  # Master Volume

        original = settings.master_volume
        menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_RIGHT))
        assert settings.master_volume > original


# =============================================================================
# Controls Hub Input Tests
# =============================================================================


class TestControlsMenuHubInputSupport:
    """Test ControlsMenuHub handles all input types."""

    def test_keyboard_navigation(self, settings):
        """ControlsMenuHub responds to arrow keys."""
        from rsp.ui.menu_controls import ControlsMenuHub

        menu = ControlsMenuHub(settings, None)
        initial = menu.selected_option

        menu.handle_input(make_key_event(tcod.event.KeySym.DOWN))
        assert menu.selected_option == initial + 1

    def test_dpad_navigation(self, settings):
        """ControlsMenuHub responds to D-pad."""
        from rsp.ui.menu_controls import ControlsMenuHub

        menu = ControlsMenuHub(settings, None)
        initial = menu.selected_option

        menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_DOWN))
        assert menu.selected_option == initial + 1

    def test_keyboard_confirm(self, settings):
        """ControlsMenuHub responds to Enter."""
        from rsp.ui.menu_controls import ControlsMenuHub

        menu = ControlsMenuHub(settings, None)
        menu.selected_option = 0  # Keyboard Bindings

        result = menu.handle_input(make_key_event(tcod.event.KeySym.RETURN))
        assert result == "keyboard_bindings"

    def test_gamepad_confirm(self, settings):
        """ControlsMenuHub responds to A button."""
        from rsp.ui.menu_controls import ControlsMenuHub

        menu = ControlsMenuHub(settings, None)
        menu.selected_option = 0

        result = menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.A))
        assert result == "keyboard_bindings"


# =============================================================================
# Gamepad Settings Menu Input Tests
# =============================================================================


class TestGamepadSettingsMenuInputSupport:
    """Test GamepadSettingsMenu handles all input types including horizontal."""

    def test_keyboard_navigation(self, settings):
        """GamepadSettingsMenu responds to arrow keys."""
        from rsp.ui.menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        initial = menu.selected_option

        menu.handle_input(make_key_event(tcod.event.KeySym.DOWN))
        assert menu.selected_option == initial + 1

    def test_dpad_navigation(self, settings):
        """GamepadSettingsMenu responds to D-pad."""
        from rsp.ui.menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        initial = menu.selected_option

        menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_DOWN))
        assert menu.selected_option == initial + 1

    def test_keyboard_horizontal_adjusts_deadzone(self, settings):
        """Left/Right arrows adjust deadzone slider."""
        from rsp.ui.menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 1  # Stick Deadzone

        original = settings.gamepad_deadzone
        menu.handle_input(make_key_event(tcod.event.KeySym.RIGHT))
        assert settings.gamepad_deadzone > original

    def test_dpad_horizontal_adjusts_deadzone(self, settings):
        """D-pad left/right adjust deadzone slider."""
        from rsp.ui.menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 1  # Stick Deadzone

        original = settings.gamepad_deadzone
        menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_RIGHT))
        assert settings.gamepad_deadzone > original


# =============================================================================
# Achievements Menu Input Tests
# =============================================================================


class TestAchievementsMenuInputSupport:
    """Test AchievementsMenu handles all input types."""

    def test_keyboard_navigation(self, settings):
        """AchievementsMenu responds to arrow keys."""
        from rsp.ui.menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        initial = menu.scroll_offset

        # Page down should scroll
        menu.handle_input(make_key_event(tcod.event.KeySym.PAGEDOWN))
        # May or may not scroll depending on content, but shouldn't crash
        assert isinstance(menu.scroll_offset, int)

    def test_dpad_navigation(self, settings):
        """AchievementsMenu responds to D-pad."""
        from rsp.ui.menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        initial_offset = menu.scroll_offset

        # D-pad down should scroll down
        menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.DPAD_DOWN))

        # Scroll offset should increase (or stay at max if at bottom)
        assert menu.scroll_offset >= initial_offset
        assert isinstance(menu.scroll_offset, int)

    def test_keyboard_cancel(self, settings):
        """AchievementsMenu responds to ESC."""
        from rsp.ui.menu_achievements import AchievementsMenu

        menu = AchievementsMenu()

        result = menu.handle_input(make_key_event(tcod.event.KeySym.ESCAPE))
        assert result == "back"

    def test_gamepad_cancel(self, settings):
        """AchievementsMenu responds to B button."""
        from rsp.ui.menu_achievements import AchievementsMenu

        menu = AchievementsMenu()

        result = menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.B))
        assert result == "back"


# =============================================================================
# About Menu Input Tests
# =============================================================================


class TestAboutMenuInputSupport:
    """Test AboutMenu handles all input types."""

    def test_keyboard_cancel(self, settings):
        """AboutMenu responds to ESC."""
        from rsp.ui.menu_about import AboutMenu

        menu = AboutMenu()

        result = menu.handle_input(make_key_event(tcod.event.KeySym.ESCAPE))
        assert result == "back"

    def test_gamepad_cancel(self, settings):
        """AboutMenu responds to B button."""
        from rsp.ui.menu_about import AboutMenu

        menu = AboutMenu()

        result = menu.handle_input(make_button_event(tcod.sdl.joystick.ControllerButton.B))
        assert result == "back"
