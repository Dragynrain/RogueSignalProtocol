"""
Integration tests for achievement popup input handling.

Tests that popups can be dismissed with keyboard and mouse input,
and that the input is consumed (not processed by other handlers).
"""

from unittest.mock import Mock

import pytest
import tcod.event

from rsp.input.handler import InputHandler
from rsp.systems.achievement_popups import AchievementPopupManager


@pytest.fixture
def popup_manager():
    """Create a fresh popup manager."""
    return AchievementPopupManager()


@pytest.fixture
def mock_game(popup_manager):
    """Create a mock game with achievement popup manager."""
    game = Mock()
    game.achievement_popup_manager = popup_manager
    game.dialogue_state = Mock()
    game.dialogue_state.is_active.return_value = False
    game.game_over = False
    game.player = Mock()
    game.player.cpu = 100
    game.show_help = False
    game.show_lore_viewer = False
    game.show_achievements = False
    game.show_inventory = False
    game.look_mode = False
    game.targeting_mode = False
    return game


@pytest.fixture
def input_handler(mock_game):
    """Create an input handler with the mock game."""
    return InputHandler(mock_game)


def test_keypress_dismisses_popup(popup_manager, input_handler, mock_game):
    """Test that pressing a key dismisses the active popup."""
    # Show a popup
    popup_manager.show_popup("first_blood")
    assert popup_manager.has_active_popup()

    # Simulate pressing ESC
    event = Mock(spec=tcod.event.KeyDown)
    event.sym = tcod.event.KeySym.ESCAPE

    # Handle the key press
    result = input_handler.handle_keydown(event)

    # Popup should be dismissed
    assert not popup_manager.has_active_popup()
    # Event should be consumed (returns True)
    assert result is True


def test_any_key_dismisses_popup(popup_manager, input_handler, mock_game):
    """Test that any key dismisses the popup."""
    # Show a popup
    popup_manager.show_popup("first_blood")
    assert popup_manager.has_active_popup()

    # Try various keys
    for key_sym in [
        tcod.event.KeySym.SPACE,
        tcod.event.KeySym.RETURN,
        tcod.event.KeySym.W,
        tcod.event.KeySym.I,
    ]:
        popup_manager.show_popup("first_blood")

        event = Mock(spec=tcod.event.KeyDown)
        event.sym = key_sym

        result = input_handler.handle_keydown(event)

        assert not popup_manager.has_active_popup(), f"Key {key_sym} didn't dismiss popup"
        assert result is True, f"Key {key_sym} wasn't consumed"


def test_mouse_click_dismisses_popup(popup_manager, input_handler, mock_game):
    """Test that clicking the mouse dismisses the active popup."""
    # Show a popup
    popup_manager.show_popup("speedrunner")
    assert popup_manager.has_active_popup()

    # Simulate left click
    event = Mock(spec=tcod.event.MouseButtonDown)
    event.button = tcod.event.MouseButton.LEFT
    event.position = Mock()
    event.position.x = 400
    event.position.y = 300

    # Handle the click
    result = input_handler._handle_left_click(event)

    # Popup should be dismissed
    assert not popup_manager.has_active_popup()
    # Event should be consumed
    assert result is True


def test_popup_has_priority_over_other_inputs(popup_manager, input_handler, mock_game):
    """Test that popup dismissal has highest priority."""
    # Setup: Show popup AND set other game states
    popup_manager.show_popup("first_blood")
    mock_game.show_inventory = True  # Inventory is also open

    # Simulate pressing 'I' (which normally toggles inventory)
    event = Mock(spec=tcod.event.KeyDown)
    event.sym = tcod.event.KeySym.I

    # Handle the key press
    result = input_handler.handle_keydown(event)

    # Popup should be dismissed
    assert not popup_manager.has_active_popup()
    # Inventory should still be open (key was consumed by popup, not processed)
    assert mock_game.show_inventory is True
    # Event should be consumed
    assert result is True


def test_no_popup_allows_normal_input(popup_manager, input_handler, mock_game):
    """Test that when no popup is active, input is processed normally."""
    # No popup active
    assert not popup_manager.has_active_popup()

    # Simulate pressing ESC (which normally is handled by other systems)
    event = Mock(spec=tcod.event.KeyDown)
    event.sym = tcod.event.KeySym.ESCAPE

    # Since there's no popup, the event should be processed by other handlers
    # This will hit the normal ESC handling logic
    result = input_handler.handle_keydown(event)

    # Should continue (returns True)
    assert result is True
    # Popup should still not be active
    assert not popup_manager.has_active_popup()


def test_multiple_popups_dismissed_one_at_time(popup_manager, input_handler, mock_game):
    """Test that when multiple popups are queued, they're dismissed one at a time."""
    # Queue multiple popups
    popup_manager.popup_queue.extend(["first_blood", "speedrunner", "ghost_protocol"])
    popup_manager.update()  # Show first popup

    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id == "first_blood"

    # Press a key to dismiss
    event = Mock(spec=tcod.event.KeyDown)
    event.sym = tcod.event.KeySym.SPACE
    input_handler.handle_keydown(event)

    # First popup dismissed
    assert not popup_manager.has_active_popup()

    # Update to show next popup
    popup_manager.update()
    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id == "speedrunner"
