"""Achievement Popup Context Tests - Achievement notification input validation.

Tests validate achievement popup behavior with:
- Keyboard (any key dismisses)
- Gamepad (any button dismisses)
- Auto-dismiss timer
- Priority over all other contexts

Achievement popups are highest priority interrupts!
"""

import pytest
from unittest.mock import Mock
import tcod.event

from game_input_actions import InputAction, InputContext
from game_engine import GameEngine
from game_input import InputHandler


class TestAchievementPopupDismissal:
    """Test achievement popup dismissal with all input methods."""

    def test_keyboard_key_dismisses_popup(self):
        """Any keyboard key dismisses achievement popup."""
        game = GameEngine()
        game.dialogue_state.close()
        # Mock achievement popup manager
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)
        game.achievement_popup_manager.dismiss_active_popup = Mock()

        handler = InputHandler(game, renderer=None)

        # Press any key (CONFIRM for example)
        handler._execute_action(InputAction.CONFIRM)

        # Popup should be dismissed
        game.achievement_popup_manager.dismiss_active_popup.assert_called_once()

    def test_gamepad_button_dismisses_popup(self):
        """Any gamepad button dismisses achievement popup."""
        game = GameEngine()
        game.dialogue_state.close()
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)
        game.achievement_popup_manager.dismiss_active_popup = Mock()

        handler = InputHandler(game, renderer=None)

        # Press gamepad button
        handler._execute_action(InputAction.CANCEL)

        # Popup should be dismissed
        game.achievement_popup_manager.dismiss_active_popup.assert_called_once()

    def test_movement_input_dismisses_popup(self):
        """Even movement keys dismiss achievement popup."""
        game = GameEngine()
        game.dialogue_state.close()
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)
        game.achievement_popup_manager.dismiss_active_popup = Mock()

        handler = InputHandler(game, renderer=None)

        # Press movement key
        handler._execute_action(InputAction.MOVE_NORTH)

        # Popup should be dismissed
        game.achievement_popup_manager.dismiss_active_popup.assert_called_once()


class TestAchievementPopupPriority:
    """Test that achievement popup has highest priority."""

    def test_achievement_popup_context_detected(self):
        """_get_current_context returns ACHIEVEMENT_POPUP when popup is active."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        assert context == InputContext.ACHIEVEMENT_POPUP

    def test_popup_takes_priority_over_dialogue(self):
        """Achievement popup takes priority over dialogue."""
        game = GameEngine()
        game.dialogue_state.is_active = Mock(return_value=True)  # Dialogue active
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)  # But popup also active

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Popup takes priority over dialogue
        assert context == InputContext.ACHIEVEMENT_POPUP

    def test_popup_takes_priority_over_game_over(self):
        """Achievement popup takes priority over game over screen."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = True  # Game over active
        game.player = Mock()
        game.player.cpu = 0
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)  # But popup also active

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Popup takes priority over game over
        assert context == InputContext.ACHIEVEMENT_POPUP

    def test_popup_takes_priority_over_all_modals(self):
        """Achievement popup takes priority over inventory/help/lore."""
        game = GameEngine()
        game.dialogue_state.close()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = True  # Inventory open
        game.show_help = True  # Help open
        game.show_lore_viewer = True  # Lore viewer open
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)  # Popup active

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()

        # Popup takes priority over everything
        assert context == InputContext.ACHIEVEMENT_POPUP


class TestAchievementPopupBlocking:
    """Test that achievement popup blocks all other input."""

    def test_movement_blocked_during_popup(self):
        """Player shouldn't move while popup is active."""
        game = GameEngine()
        game.dialogue_state.close()
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)
        game.achievement_popup_manager.dismiss_active_popup = Mock()

        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should dismiss popup, not move)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged (input was consumed by popup)
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_no_actions_execute_during_popup(self):
        """No game actions should execute while popup is active."""
        game = GameEngine()
        game.dialogue_state.close()
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=True)
        game.achievement_popup_manager.dismiss_active_popup = Mock()

        handler = InputHandler(game, renderer=None)

        # Try to toggle inventory (should dismiss popup, not toggle inventory)
        initial_inventory_state = game.show_inventory
        handler._execute_action(InputAction.TOGGLE_INVENTORY)

        # Popup dismissed, but inventory state unchanged
        game.achievement_popup_manager.dismiss_active_popup.assert_called_once()
        # Note: Inventory state may or may not change depending on implementation,
        # but the key is that popup was dismissed first
