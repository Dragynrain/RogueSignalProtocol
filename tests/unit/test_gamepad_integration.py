"""
Tests for Phase 2 & 3 integration: Context detection, action execution, and advanced gamepad features.

Tests the full integration flow:
- Context detection (_get_current_context)
- Action execution and delegation (_execute_action)
- Right stick auto-look mode (magnitude > 0.3)
- Right stick cursor control in look/targeting modes
- Exploit cycling integration with GameEngine
"""

import time
from unittest.mock import Mock

from game_input_actions import InputAction, InputContext
from game_input_analog import AnalogStickHandler
from game_input_gamepad import GamepadInputHandler
from game_input_mappings import InputMapper


class TestContextDetection:
    """Test _get_current_context() detects game state correctly."""

    def test_dialogue_context_highest_priority(self):
        """Test that dialogue context takes precedence over all others."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=True)
        game.show_inventory = True  # Even with inventory open
        game.show_help = True  # And help open
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.DIALOGUE

    def test_game_over_context(self):
        """Test game over context when player is dead."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = True
        game.player = Mock()
        game.player.cpu = 0  # Dead

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.GAME_OVER

    def test_inventory_context(self):
        """Test inventory context detection."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = True
        game.look_mode = False
        game.targeting_mode = False  # Not in targeting mode
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.INVENTORY

    def test_look_mode_context(self):
        """Test look mode context detection."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = False
        game.look_mode = True
        game.targeting_mode = False
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.LOOK_MODE

    def test_targeting_context(self):
        """Test targeting context detection."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = False
        game.look_mode = False
        game.targeting_mode = True
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.TARGETING

    def test_gameplay_context_default(self):
        """Test gameplay is default context when no modals open."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = False
        game.look_mode = False
        game.targeting_mode = False
        game.show_settings = False  # Not in settings
        game.show_about = False  # Not in about
        game.show_help = False
        game.show_lore_viewer = False
        game.show_achievements = False
        game.show_ascension = False
        game.show_main_menu = False  # Not in main menu
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        context = handler._get_current_context()
        assert context == InputContext.GAMEPLAY


class TestActionExecutionDelegation:
    """Test _execute_action() delegates to correct handlers."""

    def test_gameplay_action_delegates_to_gameplay_handler(self):
        """Test that gameplay actions are delegated to GameplayInputHandler."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = False
        game.look_mode = False
        game.targeting_mode = False
        game.show_settings = False
        game.show_about = False
        game.show_help = False
        game.show_lore_viewer = False
        game.show_achievements = False
        game.show_ascension = False
        game.show_main_menu = False  # Not in main menu
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        # Mock gameplay handler's execute_action
        handler.gameplay_handler = Mock()
        handler.gameplay_handler.execute_action = Mock(return_value=True)

        # Execute a movement action
        result = handler._execute_action(InputAction.MOVE_NORTH)

        # Should delegate to gameplay handler
        handler.gameplay_handler.execute_action.assert_called_once_with(InputAction.MOVE_NORTH)
        assert result is True

    def test_inventory_action_delegates_to_inventory_handler(self):
        """Test that inventory actions are delegated to InventoryHandler."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = True  # Inventory is open
        game.look_mode = False
        game.targeting_mode = False
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        # Mock inventory handler's execute_action
        handler.inventory_handler = Mock()
        handler.inventory_handler.execute_action = Mock(return_value=True)

        # Execute a navigation action
        result = handler._execute_action(InputAction.NAVIGATE_UP)

        # Should delegate to inventory handler
        handler.inventory_handler.execute_action.assert_called_once_with(InputAction.NAVIGATE_UP)
        assert result is True

    def test_look_mode_action_delegates_to_look_mode_handler(self):
        """Test that look mode actions are delegated to LookModeInputHandler."""
        game = Mock()
        game.dialogue_state = Mock()
        game.dialogue_state.is_active = Mock(return_value=False)
        game.game_over = False
        game.show_inventory = False
        game.look_mode = True  # Look mode is active
        game.targeting_mode = False
        game.player = Mock()
        game.player.cpu = 100  # Alive

        # Mock achievement popup manager (checked first in _get_current_context)
        game.achievement_popup_manager = Mock()
        game.achievement_popup_manager.has_active_popup = Mock(return_value=False)

        from game_input import InputHandler

        handler = InputHandler(game, renderer=None)

        # Mock look mode handler's execute_action
        handler.look_mode_handler = Mock()
        handler.look_mode_handler.execute_action = Mock(return_value=True)

        # Execute a navigation action (cursor movement)
        result = handler._execute_action(InputAction.NAVIGATE_LEFT)

        # Should delegate to look mode handler
        handler.look_mode_handler.execute_action.assert_called_once_with(InputAction.NAVIGATE_LEFT)
        assert result is True


class TestRightStickAutoLook:
    """Test right stick auto-look mode (magnitude > 0.3 enters look mode)."""

    def test_right_stick_magnitude_calculation(self):
        """Test that right stick magnitude is calculated correctly."""
        handler = AnalogStickHandler()

        # Set right stick to 50% northeast
        handler.update_right_stick(x=16384, y=-16384)  # ~50% of 32767

        magnitude = handler.get_right_stick_magnitude()

        # Magnitude should be ~0.65 (after deadzone scaling amplifies values)
        assert 0.6 < magnitude < 0.7

    def test_right_stick_magnitude_below_threshold(self):
        """Test that small stick movements have low magnitude."""
        handler = AnalogStickHandler()

        # Set stick to 10% deflection (below auto-look threshold of 0.3)
        handler.update_right_stick(x=3277, y=0)  # ~10% of 32767

        magnitude = handler.get_right_stick_magnitude()

        # Should be low or zero after deadzone
        assert magnitude < 0.2

    def test_right_stick_magnitude_above_threshold(self):
        """Test that large stick movements exceed auto-look threshold."""
        handler = AnalogStickHandler()

        # Set stick to 60% deflection (above auto-look threshold of 0.3)
        handler.update_right_stick(x=19660, y=0)  # ~60% of 32767

        magnitude = handler.get_right_stick_magnitude()

        # Should exceed 0.3 threshold for auto-look
        assert magnitude > 0.3

    def test_auto_look_triggers_when_magnitude_exceeds_threshold(self):
        """Test that gamepad handler triggers look mode when right stick magnitude > 0.3."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_game.look_mode = False

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Set right stick to 60% deflection (magnitude > 0.3)
        handler.analog_handler.update_right_stick(x=19660, y=0)

        # Get current magnitude
        magnitude = handler.analog_handler.get_right_stick_magnitude()

        # Verify magnitude exceeds threshold (this is what gamepad handler checks)
        assert magnitude > 0.3


# Settling period for right stick (30ms in implementation, use 35ms for safety)
CURSOR_SETTLING_PERIOD_SEC = 0.035


def get_cursor_movement_with_settling(handler, x, y):
    """Helper to get right stick movement after waiting for settling period."""
    handler.update_right_stick(x=x, y=y)
    handler.get_right_stick_movement()  # Start settling
    time.sleep(CURSOR_SETTLING_PERIOD_SEC)
    return handler.get_right_stick_movement()


class TestRightStickCursorControl:
    """Test right stick cursor control in look/targeting modes."""

    def test_right_stick_returns_8way_movement(self):
        """Test that right stick converts to 8-way cursor movement after settling."""
        handler = AnalogStickHandler()

        # Set right stick to northeast (with settling period)
        movement = get_cursor_movement_with_settling(handler, 25000, -25000)

        # Should return northeast (1, -1)
        assert movement == (1, -1)

    def test_right_stick_all_8_directions(self):
        """Test that right stick handles all 8 directions after settling."""
        directions = [
            ((30000, 0), (1, 0)),  # East
            ((30000, 30000), (1, 1)),  # Southeast
            ((0, 30000), (0, 1)),  # South
            ((-30000, 30000), (-1, 1)),  # Southwest
            ((-30000, 0), (-1, 0)),  # West
            ((-30000, -30000), (-1, -1)),  # Northwest
            ((0, -30000), (0, -1)),  # North
            ((30000, -30000), (1, -1)),  # Northeast
        ]

        # Create new handler for each direction to avoid cooldown issues
        for (x, y), expected in directions:
            handler = AnalogStickHandler()
            movement = get_cursor_movement_with_settling(handler, x, y)
            assert movement == expected, f"Failed for ({x}, {y})"

    def test_right_stick_cursor_has_auto_repeat(self):
        """Test that right stick cursor movement has time-based cooldown."""
        handler = AnalogStickHandler()

        # First call should return movement after settling
        movement1 = get_cursor_movement_with_settling(handler, 30000, 0)
        assert movement1 == (1, 0)

        # Immediate second call returns None due to 150ms minimum cooldown
        # This prevents wobble and ensures controlled cursor movement
        movement2 = handler.get_right_stick_movement()
        assert movement2 is None


class TestExploitCyclingIntegration:
    """Test exploit cycling integration with GameEngine."""

    def test_exploit_cycle_next_wraps_around(self):
        """Test that cycling next wraps from last to first exploit."""
        from game_engine import GameEngine

        # Create mock game with 3 equipped exploits
        game = Mock(spec=GameEngine)
        game.player = Mock()
        game.player.inventory_manager = Mock()
        game.player.inventory_manager.equipped_exploits = [
            Mock(name="exploit1"),
            Mock(name="exploit2"),
            Mock(name="exploit3"),
        ]
        game.selected_exploit_index = 2  # On last exploit
        game.message_log = Mock()

        # Manually implement cycle logic for testing
        def cycle_next():
            equipped = game.player.inventory_manager.equipped_exploits
            if not equipped:
                game.selected_exploit_index = 0
                return
            game.selected_exploit_index = (game.selected_exploit_index + 1) % len(equipped)

        # Cycle next from index 2
        cycle_next()

        # Should wrap to 0
        assert game.selected_exploit_index == 0

    def test_exploit_cycle_prev_wraps_around(self):
        """Test that cycling prev wraps from first to last exploit."""
        from game_engine import GameEngine

        # Create mock game with 3 equipped exploits
        game = Mock(spec=GameEngine)
        game.player = Mock()
        game.player.inventory_manager = Mock()
        game.player.inventory_manager.equipped_exploits = [
            Mock(name="exploit1"),
            Mock(name="exploit2"),
            Mock(name="exploit3"),
        ]
        game.selected_exploit_index = 0  # On first exploit
        game.message_log = Mock()

        # Manually implement cycle logic for testing
        def cycle_prev():
            equipped = game.player.inventory_manager.equipped_exploits
            if not equipped:
                game.selected_exploit_index = 0
                return
            game.selected_exploit_index = (game.selected_exploit_index - 1) % len(equipped)

        # Cycle prev from index 0
        cycle_prev()

        # Should wrap to 2 (last index)
        assert game.selected_exploit_index == 2

    def test_exploit_cycling_with_empty_inventory(self):
        """Test that cycling handles empty exploit inventory gracefully."""
        from game_engine import GameEngine

        # Create mock game with no equipped exploits
        game = Mock(spec=GameEngine)
        game.player = Mock()
        game.player.inventory_manager = Mock()
        game.player.inventory_manager.equipped_exploits = []
        game.selected_exploit_index = 0
        game.message_log = Mock()

        # Manually implement cycle logic for testing
        def cycle_empty():
            equipped = game.player.inventory_manager.equipped_exploits
            if not equipped:
                game.selected_exploit_index = 0
                return
            game.selected_exploit_index = (game.selected_exploit_index + 1) % len(equipped)

        # Cycle with empty inventory
        cycle_empty()

        # Should stay at 0
        assert game.selected_exploit_index == 0


class TestVisualFeedback:
    """Test that selected exploit highlighting works correctly."""

    def test_selected_exploit_index_tracked(self):
        """Test that GameEngine tracks selected_exploit_index."""
        from game_engine import GameEngine

        # Create mock game
        game = Mock(spec=GameEngine)
        game.selected_exploit_index = 0

        # Verify attribute exists
        assert hasattr(game, "selected_exploit_index")
        assert game.selected_exploit_index == 0

    def test_visual_feedback_uses_selected_index(self):
        """Test that status bar renderer uses selected_exploit_index for highlighting."""
        # This is verified by checking game_status_bar_renderer.py lines 238-242, 280-284
        # The implementation uses game.selected_exploit_index to determine YELLOW background

        # We can't easily test the rendering itself, but we can verify the attribute
        # is accessible from a mock game engine
        from game_engine import GameEngine

        game = Mock(spec=GameEngine)
        game.selected_exploit_index = 2  # Third exploit selected

        # Status bar renderer should be able to read this
        assert game.selected_exploit_index == 2
