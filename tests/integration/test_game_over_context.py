"""Game Over Context Tests - Death/victory screen input validation.

Tests validate game over screen behavior with:
- Keyboard (Enter, ESC, Q)
- Gamepad (A/B buttons)
- Mouse (click to continue)

Game over screen handles death and victory conditions!
"""

from unittest.mock import Mock

from rsp.core.engine import GameEngine
from rsp.input.handler import InputHandler
from rsp.input.actions import InputAction, InputContext


class TestGameOverActions:
    """Test game over screen actions."""

    def test_any_key_continues_from_game_over(self):
        """Most keys should exit game over screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.game_over = True
        handler = InputHandler(game, renderer=None)

        # Press a navigation key (should be consumed)
        result = handler._execute_action(InputAction.CONFIRM)

        # Action was handled (game over screen consumes most input)
        assert result is True

    def test_cancel_exits_game_over(self):
        """ESC/B button exits game over screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.game_over = True
        handler = InputHandler(game, renderer=None)

        # Cancel action
        result = handler._execute_action(InputAction.CANCEL)

        # Action was handled
        assert result is True

    def test_gamepad_confirm_continues(self):
        """A button continues from game over."""
        game = GameEngine()
        game.dialogue_state.close()
        game.game_over = True
        handler = InputHandler(game, renderer=None)

        # Confirm action
        result = handler._execute_action(InputAction.CONFIRM)

        assert result is True


class TestGameOverContextPriority:
    """Test that game over screen blocks other input."""

    def test_movement_blocked_in_game_over(self):
        """Player shouldn't move while game over screen is active."""
        game = GameEngine()
        game.dialogue_state.close()
        game.game_over = True
        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should be consumed by game over screen)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_game_over_context_detected(self):
        """_get_current_context returns GAME_OVER when player is dead."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = True
        game.player = Mock()
        game.player.cpu = 0  # Dead
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.GAME_OVER

    def test_game_over_takes_priority_over_modals(self):
        """Game over screen takes priority over inventory/help."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = True
        game.show_inventory = True  # Inventory open
        game.show_help = True  # Help open
        game.player = Mock()
        game.player.cpu = 0
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Game over takes priority
        assert context == InputContext.GAME_OVER


class TestGameOverStateManagement:
    """Test game over state is properly managed."""

    def test_cpu_zero_triggers_game_over_context(self):
        """CPU = 0 should trigger game over context."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False  # Game over flag not set
        game.player = Mock()
        game.player.cpu = 0  # But CPU is 0 (dead)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # CPU = 0 should trigger game over context
        assert context == InputContext.GAME_OVER
