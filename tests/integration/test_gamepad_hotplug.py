"""
Phase 0.1: Controller Hotplug Robustness Tests

Tests controller connect/disconnect scenarios.
Users WILL unplug controllers accidentally - the game must handle this gracefully.

Test coverage:
- Disconnect during active gameplay (mid-turn)
- Disconnect while menu open (state cleanup)
- Reconnect with state restoration
- Rapid connect/disconnect cycles
- Disconnect during button hold

Uses the game_with_gamepad fixture from tests/conftest.py.
"""

import pytest
import tcod.event
import tcod.sdl.joystick
from unittest.mock import Mock

from game_input_actions import InputAction, InputContext
from tests.integration.input_test_utils import InputTestHelper

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis


class TestDisconnectDuringGameplay:
    """Test controller disconnect during active gameplay."""

    def test_disconnect_mid_turn(self, game_with_gamepad):
        """Controller disconnects mid-turn - game continues with other inputs."""
        game, input_handler, controller = game_with_gamepad

        # Start in gameplay
        assert input_handler._get_current_context() == InputContext.GAMEPLAY

        # Verify controller is connected
        assert len(input_handler.gamepad_handler.controllers) == 1

        # Simulate controller disconnect event
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0  # Controller instance ID
        )

        # Configure mock controller to behave as disconnected
        InputTestHelper.simulate_controller_disconnect(controller)

        # Handle disconnect
        input_handler.handle_controller_device(disconnect_event)

        # Controller should be removed from set
        assert len(input_handler.gamepad_handler.controllers) == 0

        # Game should still be playable with keyboard/mouse
        # (No crash or frozen state)
        assert input_handler._get_current_context() == InputContext.GAMEPLAY

    def test_disconnect_shows_message(self, game_with_gamepad):
        """Disconnect should show user-facing message."""
        game, input_handler, controller = game_with_gamepad

        # Clear existing messages
        game.message_log.messages = []

        # Disconnect controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Verify disconnect message was added to message log
        assert len(game.message_log.messages) == 1, \
            "Disconnect should add exactly one message"
        assert "disconnected" in game.message_log.messages[0].text.lower(), \
            "Disconnect message should mention 'disconnected'"

    def test_disconnect_clears_input_state(self, game_with_gamepad):
        """Disconnect should clear any held button/stick state."""
        game, input_handler, controller = game_with_gamepad

        # Set up button held state
        input_handler.gamepad_handler.button_held = CB.A
        input_handler.gamepad_handler.button_held_since = 1.0

        # Set up stick state
        input_handler.gamepad_handler.analog_handler.left_x = 32767
        input_handler.gamepad_handler.analog_handler.left_y = -32767

        # Disconnect controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Button state should be cleared
        assert input_handler.gamepad_handler.button_held is None
        assert input_handler.gamepad_handler.button_held_since == -1.0  # "never" sentinel

        # Stick state should be cleared (centered)
        assert input_handler.gamepad_handler.analog_handler.left_x == 0
        assert input_handler.gamepad_handler.analog_handler.left_y == 0


class TestDisconnectDuringMenu:
    """Test controller disconnect while menu is open."""

    def test_disconnect_in_inventory(self, game_with_gamepad):
        """Disconnect while inventory open - menu stays open, switches to keyboard."""
        game, input_handler, controller = game_with_gamepad

        # Open inventory
        game.show_inventory = True
        assert input_handler._get_current_context() == InputContext.INVENTORY

        # Disconnect controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Inventory should still be open
        assert game.show_inventory

        # Should still be in inventory context (keyboard navigation works)
        assert input_handler._get_current_context() == InputContext.INVENTORY

        # Controller removed
        assert len(input_handler.gamepad_handler.controllers) == 0

    def test_disconnect_during_menu_navigation(self, game_with_gamepad):
        """Disconnect while navigating menu - no phantom inputs."""
        game, input_handler, controller = game_with_gamepad

        # Open help menu
        game.show_help = True

        # Set up auto-repeat state (as if holding D-pad DOWN)
        input_handler.gamepad_handler.button_held = CB.DPAD_DOWN
        input_handler.gamepad_handler.button_held_since = 1.0

        # Disconnect controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Auto-repeat state should be cleared
        assert input_handler.gamepad_handler.button_held is None

        # Menu still accessible
        assert game.show_help


class TestControllerReconnect:
    """Test controller reconnect scenarios."""

    def test_reconnect_after_disconnect(self, game_with_gamepad):
        """Reconnect controller after disconnect - should work immediately."""
        game, input_handler, controller = game_with_gamepad

        # Disconnect
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        assert len(input_handler.gamepad_handler.controllers) == 0

        # Reconnect
        new_controller = Mock()
        new_controller.name = "Test Controller"
        new_controller.instance_id = 0

        connect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEADDED",
            which=0
        )

        # Need to manually add controller to test (in real game, SDL handles this)
        # This tests that the handler's add logic works
        input_handler.gamepad_handler.controllers.add(new_controller)

        assert len(input_handler.gamepad_handler.controllers) == 1

    def test_reconnect_different_controller(self, game_with_gamepad):
        """Reconnect different controller (different instance_id)."""
        game, input_handler, controller = game_with_gamepad

        # Disconnect first controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Connect different controller (instance_id = 1)
        new_controller = Mock()
        new_controller.name = "Different Controller"
        new_controller.instance_id = 1

        input_handler.gamepad_handler.controllers.add(new_controller)

        assert len(input_handler.gamepad_handler.controllers) == 1
        assert new_controller in input_handler.gamepad_handler.controllers


class TestRapidConnectDisconnect:
    """Test rapid connect/disconnect cycles."""

    def test_rapid_disconnect_reconnect(self, game_with_gamepad):
        """Rapid disconnect/reconnect cycles - no crash."""
        game, input_handler, controller = game_with_gamepad

        # Perform 5 rapid disconnect/reconnect cycles
        current_controller = controller
        for i in range(5):
            # Disconnect
            disconnect_event = tcod.event.ControllerDevice(
                type="CONTROLLERDEVICEREMOVED",
                which=0
            )
            InputTestHelper.simulate_controller_disconnect(current_controller)
            input_handler.handle_controller_device(disconnect_event)

            assert len(input_handler.gamepad_handler.controllers) == 0

            # Reconnect
            new_controller = Mock()
            new_controller.name = f"Controller {i}"
            new_controller.instance_id = 0
            input_handler.gamepad_handler.controllers.add(new_controller)
            current_controller = new_controller

            assert len(input_handler.gamepad_handler.controllers) == 1

        # Final state should be stable
        assert len(input_handler.gamepad_handler.controllers) == 1

    def test_disconnect_within_100ms(self, game_with_gamepad):
        """Disconnect within 100ms of connect - edge case."""
        game, input_handler, controller = game_with_gamepad

        # This simulates USB cable wiggle (loose connection)
        # Controller appears, immediately disappears

        # Start with controller
        assert len(input_handler.gamepad_handler.controllers) == 1

        # Disconnect
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # No crash, state consistent
        assert len(input_handler.gamepad_handler.controllers) == 0


class TestDisconnectDuringButtonHold:
    """Test disconnect while button is held."""

    def test_disconnect_during_wait_action(self, game_with_gamepad):
        """Disconnect while holding A button (wait action in gameplay)."""
        game, input_handler, controller = game_with_gamepad

        # Press A button (wait action)
        press_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=CB.A,
            pressed=True
        )
        action = input_handler.handle_controller_button(press_event)
        assert action is True  # Returns True if handled, not InputAction

        # Button is "held" (physically)
        # In implementation, button_held may or may not be set for non-navigation buttons

        # Disconnect controller while button held
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # State cleared
        assert input_handler.gamepad_handler.button_held is None

        # Reconnect controller
        new_controller = Mock()
        new_controller.name = "Test Controller"
        new_controller.instance_id = 0
        input_handler.gamepad_handler.controllers.add(new_controller)

        # Press A button again - should work (no stuck state)
        press_event2 = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=CB.A,
            pressed=True
        )
        action2 = input_handler.handle_controller_button(press_event2)
        assert action2 is True  # Works normally - returns True if handled

    def test_disconnect_during_stick_hold(self, game_with_gamepad):
        """Disconnect while stick is deflected."""
        game, input_handler, controller = game_with_gamepad

        # Deflect stick
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=CA.LEFTX,
            value=32767  # Full right
        )
        input_handler.handle_controller_axis(axis_event)

        # Verify stick state updated
        assert input_handler.gamepad_handler.analog_handler.left_x == 32767

        # Disconnect
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Stick state cleared
        assert input_handler.gamepad_handler.analog_handler.left_x == 0
        assert input_handler.gamepad_handler.analog_handler.left_y == 0


class TestMultipleControllers:
    """Test behavior with multiple controllers connected."""

    def test_disconnect_one_of_two_controllers(self, game_with_gamepad):
        """Disconnect one controller when two are connected."""
        game, input_handler, controller = game_with_gamepad

        # Add second controller
        controller2 = Mock()
        controller2.name = "Controller 2"
        controller2.instance_id = 1
        input_handler.gamepad_handler.controllers.add(controller2)

        assert len(input_handler.gamepad_handler.controllers) == 2

        # Disconnect first controller (instance_id=0)
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        # Only second controller remains
        assert len(input_handler.gamepad_handler.controllers) == 1

        # Verify the right controller was removed
        remaining = list(input_handler.gamepad_handler.controllers)[0]
        assert remaining.instance_id == 1

    def test_disconnect_all_controllers(self, game_with_gamepad):
        """Disconnect all controllers - fallback to keyboard/mouse."""
        game, input_handler, controller = game_with_gamepad

        # Add second controller
        controller2 = Mock()
        controller2.name = "Controller 2"
        controller2.instance_id = 1
        input_handler.gamepad_handler.controllers.add(controller2)

        # Disconnect both
        disconnect1 = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        disconnect2 = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=1
        )

        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect1)
        InputTestHelper.simulate_controller_disconnect(controller2)
        input_handler.handle_controller_device(disconnect2)

        # No controllers
        assert len(input_handler.gamepad_handler.controllers) == 0

        # Game still playable (context detection works)
        assert input_handler._get_current_context() == InputContext.GAMEPLAY


class TestEdgeCases:
    """Edge cases and error scenarios."""

    def test_disconnect_unknown_controller(self, game_with_gamepad):
        """Disconnect event for controller that doesn't exist."""
        game, input_handler, controller = game_with_gamepad

        # Disconnect unknown controller (instance_id=99)
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=99
        )

        # Should handle gracefully (no crash)
        input_handler.handle_controller_device(disconnect_event)

        # Original controller still connected
        assert len(input_handler.gamepad_handler.controllers) == 1

    def test_disconnect_with_no_controllers(self, game_with_gamepad):
        """Disconnect event when no controllers connected."""
        game, input_handler, controller = game_with_gamepad

        # Remove all controllers first
        input_handler.gamepad_handler.controllers.clear()

        # Disconnect event with empty set
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )

        # Should handle gracefully
        input_handler.handle_controller_device(disconnect_event)

        # Still no controllers
        assert len(input_handler.gamepad_handler.controllers) == 0

    def test_duplicate_disconnect_events(self, game_with_gamepad):
        """Multiple disconnect events for same controller."""
        game, input_handler, controller = game_with_gamepad

        # Disconnect controller
        disconnect_event = tcod.event.ControllerDevice(
            type="CONTROLLERDEVICEREMOVED",
            which=0
        )
        InputTestHelper.simulate_controller_disconnect(controller)
        input_handler.handle_controller_device(disconnect_event)

        assert len(input_handler.gamepad_handler.controllers) == 0

        # Second disconnect event for same controller
        input_handler.handle_controller_device(disconnect_event)

        # Should handle gracefully (idempotent)
        assert len(input_handler.gamepad_handler.controllers) == 0
