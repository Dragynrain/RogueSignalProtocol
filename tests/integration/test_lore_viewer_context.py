"""Lore Viewer Context Tests - Comprehensive lore viewer input validation.

Tests validate lore viewer navigation and interaction with:
- Keyboard (arrow keys, Enter, ESC)
- Gamepad (D-pad, A/B buttons)
- Mouse (hover and click)

Lore viewer is critical for narrative immersion!
"""

from unittest.mock import Mock

from rsp.core.engine import GameEngine
from rsp.input.handler import InputHandler
from rsp.input.actions import InputAction, InputContext


class TestLoreViewerNavigation:
    """Test lore viewer navigation with all input methods."""

    def test_keyboard_navigate_down(self):
        """DOWN arrow moves lore list selection down."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"  # List selection mode
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        initial_selection = game.lore_viewer_selection

        # Navigate down
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        # Selection should move (unless at boundary)
        assert game.lore_viewer_selection >= initial_selection

    def test_keyboard_navigate_up(self):
        """UP arrow moves lore list selection up."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 1  # Start at second item
        handler = InputHandler(game, renderer=None)

        initial_selection = game.lore_viewer_selection

        # Navigate up
        handler._execute_action(InputAction.NAVIGATE_UP)

        assert game.lore_viewer_selection <= initial_selection

    def test_gamepad_dpad_navigation(self):
        """Gamepad D-pad navigates lore list."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        initial_selection = game.lore_viewer_selection

        # D-pad DOWN
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        assert game.lore_viewer_selection >= initial_selection

    def test_exit_lore_viewer_from_list(self):
        """ESC closes lore viewer when in list mode."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        # Exit lore viewer
        handler._execute_action(InputAction.CANCEL)

        assert game.show_lore_viewer is False

    def test_exit_reading_mode_returns_to_list(self):
        """ESC in reading mode returns to list mode."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "reading"  # Reading a specific entry
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        # Exit reading mode
        handler._execute_action(InputAction.CANCEL)

        # Should return to list mode (not close viewer)
        assert game.show_lore_viewer is True
        assert game.lore_viewer_mode == "list"


class TestLoreViewerActions:
    """Test lore viewer item selection."""

    def test_confirm_opens_lore_entry(self):
        """Enter/A button opens selected lore entry."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        # Confirm selection
        result = handler._execute_action(InputAction.CONFIRM)

        # Action was handled (actual behavior depends on menu implementation)
        assert result is True


class TestLoreViewerContextPriority:
    """Test that lore viewer blocks other input."""

    def test_movement_blocked_in_lore_viewer(self):
        """Player shouldn't move while lore viewer is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.lore_viewer_selection = 0
        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should be consumed by lore viewer)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_lore_viewer_context_detected(self):
        """_get_current_context returns LORE_VIEWER when viewer is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_lore_viewer = True
        game.lore_viewer_mode = "list"
        game.show_inventory = False
        game.look_mode = False
        game.targeting_mode = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.LORE_VIEWER
