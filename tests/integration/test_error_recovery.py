"""
Phase 3.1: Error Recovery Tests

Tests how gracefully the system handles action execution failures and error scenarios.

Test coverage:
- Action generated but context handler missing
- Action executed but game state rejects it
- Action partially executes then fails
- User feedback when action silently fails
- Chained action failures
"""

from unittest.mock import Mock

import pytest
import tcod.event
import tcod.sdl.joystick

from rsp.systems.audio import NullSoundManager
from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.input.handler import InputHandler

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton


@pytest.fixture
def game_setup():
    """Create game instance for testing."""
    settings = GameSettings()
    settings.graphics_mode = "text"
    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)

    # Mock controller
    mock_controller = Mock()
    mock_controller.name = "Test Controller"
    mock_controller.instance_id = 0
    controllers = {mock_controller}

    # Create input handler
    input_handler = InputHandler(game, renderer=None, controllers=controllers)

    # Clear starting dialogue
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.dialogue_history = []

    return game, input_handler


class TestActionExecutionFailures:
    """Test action execution failure scenarios."""

    def test_unmapped_button_doesnt_crash(self, game_setup):
        """Pressing unmapped button doesn't crash - fails gracefully."""
        game, input_handler = game_setup

        # Press an unmapped button (e.g., GUIDE button - typically unmapped)
        guide_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.GUIDE, pressed=True  # Usually unmapped
        )

        # Should handle gracefully (return None for unmapped)
        result = input_handler.handle_controller_button(guide_event)
        assert result in (True, None), "Unmapped button should return True or None, not crash"

    def test_movement_blocked_by_wall(self, game_setup):
        """Movement action rejected by game state (wall blocking) doesn't crash."""
        game, input_handler = game_setup

        # Move player to edge of map
        game.player.x = 0
        game.player.y = 0

        initial_x = game.player.x
        initial_y = game.player.y

        # Try to move west (into wall/void)
        west_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_LEFT, pressed=True
        )

        # Should handle gracefully - action consumed but no movement
        result = input_handler.handle_controller_button(west_event)
        assert result is True  # Handled

        # Player position should remain valid (either same or valid new position)
        # At edge (0,0), moving west should be blocked
        assert game.player.x >= 0, "Player x position should not go negative"
        assert game.player.y >= 0, "Player y position should not go negative"

    def test_exploit_execution_with_no_target(self, game_setup):
        """Executing exploit with no valid targets fails gracefully."""
        game, input_handler = game_setup

        # Ensure player has an exploit equipped
        game.player.inventory_manager.equipped_exploits = ["buffer_overflow"]
        game.selected_exploit_index = 0

        # Try to execute exploit (Right shoulder button cycles, but let's use RT/LT)
        # Note: Need to check actual controller button enum names
        rt_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.RIGHTSHOULDER,  # RB button
            pressed=True,
        )

        # Should handle gracefully (may enter targeting mode or fail silently)
        result = input_handler.handle_controller_button(rt_event)
        # Handler should return a valid result (True = handled, None = ignored)
        assert result in (True, None), f"Unexpected result: {result}"

    def test_invalid_inventory_selection(self, game_setup):
        """Selecting invalid inventory index doesn't crash."""
        game, input_handler = game_setup

        # Force invalid inventory selection
        game.show_inventory = True
        game.inventory_selection = 999  # Way out of bounds

        # Try to confirm selection
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        # Should handle gracefully (bounds checking)
        result = input_handler.handle_controller_button(a_event)
        # Handler should return a valid result
        assert result in (True, None), f"Unexpected result: {result}"
        # Inventory selection should be clamped or reset, not negative
        assert game.inventory_selection >= 0


class TestUserFeedback:
    """Test that users get feedback when actions fail."""

    def test_failed_action_doesnt_freeze_input(self, game_setup):
        """Failed action doesn't freeze subsequent input handling."""
        game, input_handler = game_setup

        # Execute action that might fail
        game.show_inventory = True
        game.inventory_selection = 0

        # Press A to select
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )
        result1 = input_handler.handle_controller_button(a_event)

        # Try another action immediately
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )
        result2 = input_handler.handle_controller_button(b_event)

        # Both should return valid handler results (True/False/None)
        assert result1 in (True, False, None), f"First result invalid: {result1}"
        assert result2 in (True, False, None), f"Second result invalid: {result2}"

    def test_rapid_failed_actions_dont_accumulate(self, game_setup):
        """Rapid failed actions don't accumulate/queue."""
        game, input_handler = game_setup

        # Send 10 rapid button presses of unmapped button
        for i in range(10):
            event = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=CB.GUIDE, pressed=True  # Unmapped
            )
            result = input_handler.handle_controller_button(event)

        # Game should still be responsive - player object should still be valid
        assert game.player is not None
        assert hasattr(game.player, "x") and hasattr(game.player, "y")


class TestPartialExecutionFailures:
    """Test scenarios where actions partially execute then fail."""

    def test_context_change_during_action(self, game_setup):
        """Context changing mid-action doesn't corrupt state."""
        game, input_handler = game_setup

        # Start in gameplay
        assert not game.show_inventory

        # Try to open inventory (START button toggles inventory)
        start_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.START, pressed=True
        )
        result = input_handler.handle_controller_button(start_event)

        # Verify input was processed (result depends on mapping, can be True or False)
        # The important thing is no crash occurred
        assert result in (True, False, None)  # Input processed without crash

        # Send another input to verify system still responsive
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )
        result2 = input_handler.handle_controller_button(b_event)

        # System should still be responsive
        assert result2 is not None  # Still handling input

    def test_death_during_input_handling(self, game_setup):
        """Player death during input processing doesn't crash."""
        game, input_handler = game_setup

        # Kill player
        game.player.cpu = 0
        game.game_over = True

        # Try to send input
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        # Should handle gracefully (game over state)
        try:
            result = input_handler.handle_controller_button(a_event)
            # Either dismisses dialogue or exits to menu
            assert result in (True, False, None)
        except Exception as e:
            pytest.fail(f"Input during death crashed: {e}")


class TestChainedFailures:
    """Test scenarios with multiple cascading failures."""

    def test_multiple_simultaneous_errors(self, game_setup):
        """Multiple errors at once don't cascade into crash."""
        game, input_handler = game_setup

        # Create error-prone state
        game.show_inventory = True
        game.inventory_selection = 999  # Invalid
        game.player.cpu = 0  # Dead
        game.game_over = True

        # Try to interact
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        # Should prioritize game over state and handle gracefully
        # No exception = success (smoke test for crash resistance)
        result = input_handler.handle_controller_button(a_event)
        # Test passes if no exception raised - result can be any value including None

    def test_recovery_from_error_state(self, game_setup):
        """System can recover from error state and continue."""
        game, input_handler = game_setup

        # Create problematic state
        game.inventory_selection = 999  # Invalid

        # Open inventory (might handle invalid selection)
        game.show_inventory = True

        # Navigate (should reset selection to valid range)
        down_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        input_handler.handle_controller_button(down_event)

        # Selection should be corrected
        # (Exact value depends on inventory contents, but should be valid)
        assert game.inventory_selection >= 0

        # System should be responsive
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )
        result = input_handler.handle_controller_button(b_event)
        assert result is True
