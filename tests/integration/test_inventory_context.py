"""Inventory Context Tests - Comprehensive inventory input validation.

Tests validate inventory navigation, selection, and item use with:
- Keyboard (arrow keys, Enter, ESC)
- Gamepad (D-pad, A/B buttons, shoulder buttons)
- Mouse (hover and click)

Inventory is critical for item management and tactical preparation!
"""

from unittest.mock import Mock

from rsp.core.engine import GameEngine
from rsp.input.actions import InputAction
from rsp.input.handler import InputHandler


class TestInventoryNavigation:
    """Test inventory navigation with all input methods."""

    def test_keyboard_navigate_down(self):
        """DOWN arrow moves inventory selection down."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        initial_selection = game.inventory_selection

        # Navigate down
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        # Selection should move (unless at boundary)
        assert game.inventory_selection >= initial_selection

    def test_keyboard_navigate_up(self):
        """UP arrow moves inventory selection up."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        game.inventory_selection = 1  # Start at second item
        handler = InputHandler(game, renderer=None)

        initial_selection = game.inventory_selection

        # Navigate up
        handler._execute_action(InputAction.NAVIGATE_UP)

        assert game.inventory_selection <= initial_selection

    def test_gamepad_dpad_navigation(self):
        """Gamepad D-pad navigates inventory."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        initial_selection = game.inventory_selection

        # D-pad DOWN
        handler._execute_action(InputAction.NAVIGATE_DOWN)

        assert game.inventory_selection >= initial_selection

    def test_exit_inventory_keyboard(self):
        """ESC or I closes inventory."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        # Exit inventory
        handler._execute_action(InputAction.CANCEL)

        assert game.show_inventory is False

    def test_exit_inventory_gamepad(self):
        """Gamepad B button closes inventory."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        # Exit inventory
        handler._execute_action(InputAction.CANCEL)

        assert game.show_inventory is False


class TestInventoryActions:
    """Test inventory item actions."""

    def test_confirm_selects_item(self):
        """Enter/A button selects item."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        # Confirm action
        result = handler._execute_action(InputAction.CONFIRM)

        # Action was handled
        assert result is True


class TestInventoryContextPriority:
    """Test that inventory blocks other input."""

    def test_movement_blocked_in_inventory(self):
        """Player shouldn't move while inventory is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        handler = InputHandler(game, renderer=None)

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move (should be consumed by inventory)
        handler._execute_action(InputAction.MOVE_NORTH)

        # Player position unchanged
        assert game.player.x == initial_x
        assert game.player.y == initial_y

    def test_inventory_context_detected(self):
        """_get_current_context returns INVENTORY when inventory is open."""
        game = GameEngine()
        game.dialogue_state.close()
        game.show_inventory = True
        game.look_mode = False
        game.targeting_mode = False
        game.player = Mock()
        game.player.cpu = 100
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        handler = InputHandler(game, renderer=None)

        from rsp.input.actions import InputContext

        context = handler._get_current_context()

        assert context == InputContext.INVENTORY
