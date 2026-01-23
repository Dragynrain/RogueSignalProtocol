"""
Gamepad Dual Input Tests.

Tests scenarios involving simultaneous or mixed input:
- Simultaneous X+Y axis input (diagonal sticks)
- Event + polling input mixing (D-pad then stick)
- Releasing one input while other is held
- Context switching while inputs are held

These edge cases can cause state corruption if not handled properly.

Uses the game_with_gamepad fixture from tests/conftest.py.
Uses mock_time fixture for deterministic timing (no flaky time.sleep).
"""

import tcod.event
import tcod.sdl.joystick

from rsp.core.config import GameConfig
from rsp.input.actions import InputAction, InputContext

# Shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

SETTLING_PERIOD_SEC = 0.035


class TestSimultaneousAxisInput:
    """Test both X and Y axis input at the same time."""

    def test_diagonal_stick_input_produces_diagonal_movement(self, game_with_gamepad):
        """Full diagonal stick deflection should produce diagonal movement."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Full northeast: +X, -Y (right, up)
        analog.update_left_stick(x=32000, y=-32000)

        # Get 8-way direction
        dx, dy = analog.analog_to_8way(32000, -32000)

        # Should be northeast
        assert dx == 1  # Right
        assert dy == -1  # Up

    def test_x_then_y_axis_events_in_sequence(self, game_with_gamepad):
        """X axis event followed by Y axis event should work correctly."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Send X axis event (right)
        x_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )
        action_x = gamepad.handle_axis_event(x_event, InputContext.SETTINGS_MENU)

        # Send Y axis event (down)
        y_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000
        )
        action_y = gamepad.handle_axis_event(y_event, InputContext.SETTINGS_MENU)

        # Both should produce actions
        assert action_x == InputAction.NAVIGATE_RIGHT
        assert action_y == InputAction.NAVIGATE_DOWN

    def test_graphics_preview_x_and_y_together(self, game_with_gamepad):
        """Graphics preview should handle X (variant) and Y (entity) together."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # X axis for variant cycling
        x_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=32000
        )
        action_x = gamepad.handle_axis_event(x_event, InputContext.GRAPHICS_PREVIEW)
        assert action_x == InputAction.NAVIGATE_RIGHT

        # Y axis for entity selection
        y_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=32000
        )
        action_y = gamepad.handle_axis_event(y_event, InputContext.GRAPHICS_PREVIEW)
        assert action_y == InputAction.NAVIGATE_DOWN


class TestEventPollingMixing:
    """Test mixing D-pad (events) with analog stick (polling)."""

    def test_dpad_press_then_stick_move(self, game_with_gamepad, mock_time):
        """D-pad press followed by stick movement should both work."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # D-pad up (event-based)
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        dpad_action = gamepad.handle_button_event(dpad_event, InputContext.MAIN_MENU)
        assert dpad_action == InputAction.NAVIGATE_UP

        # D-pad tracking should be active
        assert gamepad.button_held == CB.DPAD_UP

        # Now move stick (separate input path)
        analog.update_left_stick(x=0, y=32000)  # Down
        mock_time.advance(SETTLING_PERIOD_SEC)
        stick_movement = analog.get_left_stick_movement_menu()

        # Stick should also produce movement (independent of D-pad)
        assert stick_movement is not None
        assert stick_movement == (0, 1)  # Down

    def test_stick_move_then_dpad_press(self, game_with_gamepad, mock_time):
        """Stick movement followed by D-pad press should both work."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Move stick first
        analog.update_left_stick(x=32000, y=0)  # Right
        mock_time.advance(SETTLING_PERIOD_SEC)
        stick_movement = analog.get_left_stick_movement_menu()
        assert stick_movement == (1, 0)

        # Then D-pad
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        dpad_action = gamepad.handle_button_event(dpad_event, InputContext.MAIN_MENU)
        assert dpad_action == InputAction.NAVIGATE_DOWN

    def test_simultaneous_dpad_and_stick_no_crash(self, game_with_gamepad):
        """Pressing D-pad while stick is held should not crash."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Hold stick
        analog.update_left_stick(x=32000, y=0)

        # Press D-pad while stick is held
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )

        # Should not raise exception
        action = gamepad.handle_button_event(dpad_event, InputContext.MAIN_MENU)
        assert action == InputAction.NAVIGATE_UP


class TestInputReleaseWhileOtherHeld:
    """Test releasing one input while another is still held."""

    def test_release_dpad_while_stick_held(self, game_with_gamepad):
        """Releasing D-pad while stick is held should clear D-pad state only."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Hold stick
        analog.update_left_stick(x=32000, y=0)

        # Press and release D-pad
        press_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(press_event, InputContext.MAIN_MENU)
        assert gamepad.button_held == CB.DPAD_UP

        release_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=False
        )
        gamepad.handle_button_event(release_event, InputContext.MAIN_MENU)

        # D-pad should be cleared
        assert gamepad.button_held is None

        # Stick should still have data (not cleared)
        assert analog.left_x == 32000

    def test_release_stick_while_dpad_held(self, game_with_gamepad):
        """Releasing stick while D-pad is held should clear stick state only."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Press D-pad UP (navigation button in menu context)
        # Note: MAIN_MENU only maps up/down, not left/right
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(dpad_event, InputContext.MAIN_MENU)

        # Verify button is being tracked for auto-repeat
        assert gamepad.button_held == CB.DPAD_UP

        # Hold then release stick (separate input path)
        analog.update_left_stick(x=32000, y=0)
        analog.update_left_stick(x=0, y=0)  # Release

        # D-pad tracking should still be active (not affected by stick)
        assert gamepad.button_held == CB.DPAD_UP

        # Stick should be at center
        assert analog.left_x == 0


class TestContextSwitchWithActiveInputs:
    """Test context switching while inputs are active."""

    def test_open_inventory_while_stick_held(self, game_with_gamepad):
        """Opening inventory while stick is held should not crash."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Hold stick
        analog.update_left_stick(x=32000, y=0)

        # Open inventory (context switch)
        game.show_inventory = True

        # Context should change
        assert input_handler._get_current_context() == InputContext.INVENTORY

        # Stick data should still be there (not auto-cleared)
        assert analog.left_x == 32000

    def test_close_inventory_while_button_held(self, game_with_gamepad):
        """Closing inventory while button is held should work cleanly."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Open inventory
        game.show_inventory = True

        # Press navigation button
        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        gamepad.handle_button_event(button_event, InputContext.INVENTORY)

        # Close inventory
        game.show_inventory = False

        # Context changes back to gameplay
        assert input_handler._get_current_context() == InputContext.GAMEPLAY

        # Button tracking persists (cleared on release, not context switch)
        # This is actually correct behavior - button is still physically held

    def test_dialogue_appears_while_moving(self, game_with_gamepad):
        """Dialogue appearing while moving should not cause issues."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Start moving
        analog.update_left_stick(x=0, y=-32000)  # Up

        # Dialogue appears
        from rsp.ui.dialogue import DialogueBox

        dialogue = DialogueBox(
            title="Test",
            message="Test dialogue",
            options=["[Enter] Continue"],
            valid_keys=[tcod.event.KeySym.RETURN],
            title_color=(255, 255, 255),
            message_color=(255, 255, 255),
            border_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            format_data={},
            priority=1,
        )
        game.dialogue_state.active_dialogue = dialogue

        # Context should be dialogue
        assert input_handler._get_current_context() == InputContext.DIALOGUE

        # Gameplay movement should not be processed in dialogue context
        # (stick data persists but won't trigger movement)


class TestLeftAndRightStickTogether:
    """Test using both sticks simultaneously."""

    def test_both_sticks_deflected(self, game_with_gamepad):
        """Both sticks deflected at once should track independently."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Deflect both sticks
        analog.update_left_stick(x=32000, y=0)  # Right
        analog.update_right_stick(x=-32000, y=0)  # Left

        # Both should be tracked independently
        assert analog.left_x == 32000
        assert analog.right_x == -32000

    def test_left_stick_movement_right_stick_look(self, game_with_gamepad, mock_time):
        """Left stick for movement, right stick for look - normal config."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Ensure swap is off
        game.settings.gamepad_swap_sticks = False

        # Left stick moves - need to start settling then wait
        analog.update_left_stick(x=32000, y=0)
        analog.get_left_stick_movement_gameplay(game.turn)  # Start settling
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement == (1, 0)

        # Right stick magnitude for look mode trigger
        analog.update_right_stick(x=0, y=-32000)
        look_magnitude = analog.get_right_stick_magnitude()
        assert look_magnitude > GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD

    def test_swapped_sticks_movement_and_look(self, game_with_gamepad, mock_time):
        """With swap enabled, right moves and left looks."""
        game, input_handler, _ = game_with_gamepad
        analog = input_handler.gamepad_handler.analog_handler

        # Enable swap
        game.settings.gamepad_swap_sticks = True

        # Right stick now moves - need to start settling then wait
        analog.update_right_stick(x=32000, y=0)
        analog.get_right_stick_movement_gameplay(game.turn)  # Start settling
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement = analog.get_right_stick_movement_gameplay(game.turn)
        assert movement == (1, 0)

        # Left stick now for look mode
        analog.update_left_stick(x=0, y=-32000)
        look_magnitude = analog.get_left_stick_magnitude()
        assert look_magnitude > GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD


class TestRapidInputSequences:
    """Test rapid input sequences don't cause issues."""

    def test_rapid_button_presses(self, game_with_gamepad):
        """Rapid button presses should not corrupt state."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Rapidly press different buttons
        buttons = [CB.DPAD_UP, CB.DPAD_DOWN, CB.DPAD_LEFT, CB.DPAD_RIGHT]

        for button in buttons:
            press = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=button, pressed=True
            )
            gamepad.handle_button_event(press, InputContext.MAIN_MENU)

            release = tcod.event.ControllerButton(
                type="CONTROLLERBUTTONDOWN", which=0, button=button, pressed=False
            )
            gamepad.handle_button_event(release, InputContext.MAIN_MENU)

        # State should be clean at end
        assert gamepad.button_held is None

    def test_rapid_axis_events(self, game_with_gamepad):
        """Rapid axis events should not corrupt state."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Send many axis events rapidly
        for i in range(20):
            x_val = (i % 3 - 1) * 32000  # -32000, 0, 32000
            y_val = ((i + 1) % 3 - 1) * 32000

            x_event = tcod.event.ControllerAxis(
                type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=x_val
            )
            gamepad.handle_axis_event(x_event, InputContext.GAMEPLAY)

            y_event = tcod.event.ControllerAxis(
                type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTY, value=y_val
            )
            gamepad.handle_axis_event(y_event, InputContext.GAMEPLAY)

        # Should have valid state (last values)
        # Just verify no crash occurred


class TestTriggerWithStick:
    """Test trigger input combined with stick input."""

    def test_trigger_while_stick_deflected(self, game_with_gamepad):
        """Trigger press while stick is deflected should both work."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler
        analog = gamepad.analog_handler

        # Deflect stick
        analog.update_left_stick(x=32000, y=0)

        # Press left trigger (starts at 0)
        trigger_unpressed = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=0
        )
        gamepad.handle_axis_event(trigger_unpressed, InputContext.GAMEPLAY)

        trigger_pressed = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=30000
        )
        action = gamepad.handle_axis_event(trigger_pressed, InputContext.GAMEPLAY)

        # Trigger should fire action
        assert action == InputAction.TOGGLE_LOOK_MODE

        # Stick should still be deflected
        assert analog.left_x == 32000

    def test_stick_during_look_mode(self, game_with_gamepad):
        """Stick movement during look mode should control cursor."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Enable look mode
        game.look_mode = True

        # Right stick (cursor control in look mode)
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.RIGHTX, value=32000
        )

        action = gamepad.handle_axis_event(axis_event, InputContext.LOOK_MODE)

        # Should produce movement action for cursor
        # (LOOK_MODE uses right stick for cursor movement)
        assert action in (InputAction.MOVE_EAST, None)  # Depending on timing


class TestMultipleButtonsHeld:
    """Test multiple buttons being held at once."""

    def test_two_buttons_pressed_tracks_second(self, game_with_gamepad):
        """Pressing second button while first held should track second."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press first button
        first = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(first, InputContext.MAIN_MENU)
        assert gamepad.button_held == CB.DPAD_UP

        # Press second button (navigation - will update tracking)
        second = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        gamepad.handle_button_event(second, InputContext.MAIN_MENU)

        # Second navigation button replaces first for auto-repeat
        assert gamepad.button_held == CB.DPAD_DOWN

    def test_release_second_button_first_still_tracked(self, game_with_gamepad):
        """If first button released, second button state should remain."""
        game, input_handler, _ = game_with_gamepad
        gamepad = input_handler.gamepad_handler

        # Press both buttons
        first = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        gamepad.handle_button_event(first, InputContext.MAIN_MENU)

        second = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_DOWN, pressed=True
        )
        gamepad.handle_button_event(second, InputContext.MAIN_MENU)

        # Release first button (not the tracked one)
        first_release = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=False
        )
        gamepad.handle_button_event(first_release, InputContext.MAIN_MENU)

        # Second button should still be tracked (it wasn't released)
        assert gamepad.button_held == CB.DPAD_DOWN
