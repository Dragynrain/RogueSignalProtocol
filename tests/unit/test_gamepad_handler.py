"""
Tests for Phase 2 and Phase 3: Gamepad Event Handling and Default Bindings.

Tests GamepadInputHandler, device management, button/axis event processing,
context detection, action execution, and default gamepad bindings.
"""

import time
from unittest.mock import Mock, PropertyMock

import tcod.event
import tcod.sdl.joystick

from rsp.input.actions import InputAction, InputContext
from rsp.input.analog import AnalogStickHandler
from rsp.input.gamepad import GamepadInputHandler
from rsp.input.mappings import InputMapper

# Shorthand for controller enums
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

# Settling period for analog stick (30ms in implementation, use 35ms for safety)
SETTLING_PERIOD_SEC = 0.035


def get_movement_with_settling(analog, game_turn, x, y):
    """Helper to get movement after simulating settling period (time mocked).

    Uses direct manipulation of settling start time to avoid real sleep.
    """
    analog.update_left_stick(x=x, y=y)
    analog.get_left_stick_movement_gameplay(game_turn)  # Start settling

    # Simulate time passing by backdating the settling start time
    if hasattr(analog, "_settling_start_time") and analog._settling_start_time > 0:
        analog._settling_start_time = time.time() - SETTLING_PERIOD_SEC - 0.001

    return analog.get_left_stick_movement_gameplay(game_turn)


class TestGamepadInputHandler:
    """Test GamepadInputHandler initialization and basic functionality (Phase 2)."""

    def test_handler_initializes_without_controllers(self):
        """Test that handler initializes with no controllers."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        assert handler is not None
        assert len(handler.controllers) == 0
        assert handler.input_mapper is mapper
        assert handler.analog_handler is not None

    def test_handler_initializes_with_controllers(self):
        """Test that handler accepts initial controllers."""
        mapper = InputMapper()
        mock_controller = Mock()
        mock_controller.name = "Test Controller"
        initial_controllers = {mock_controller}

        handler = GamepadInputHandler(mapper, initial_controllers=initial_controllers)

        assert len(handler.controllers) == 1
        assert mock_controller in handler.controllers

    def test_handler_stores_game_reference(self):
        """Test that handler stores game reference for turn tracking."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn_count = 5

        handler = GamepadInputHandler(mapper, game=mock_game)

        assert handler.game is mock_game

    def test_analog_handler_created_automatically(self):
        """Test that analog handler is created during init."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        assert isinstance(handler.analog_handler, AnalogStickHandler)


class TestGamepadDeviceManagement:
    """Test controller device connection/disconnection (Phase 2)."""

    def test_handle_device_added(self):
        """Test that device added event adds controller to set."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Create mock controller with event
        mock_event = Mock(spec=tcod.event.ControllerDevice)
        mock_event.type = "CONTROLLERDEVICEADDED"
        mock_controller = Mock()
        mock_controller.name = "Xbox Controller"
        mock_event.controller = mock_controller

        handler.handle_device_event(mock_event)

        assert len(handler.controllers) == 1
        assert mock_controller in handler.controllers

    def test_handle_device_added_with_game_message(self):
        """Test that device added shows message in game."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.message_log = Mock()
        handler = GamepadInputHandler(mapper, game=mock_game)

        mock_event = Mock(spec=tcod.event.ControllerDevice)
        mock_event.type = "CONTROLLERDEVICEADDED"
        mock_controller = Mock()
        mock_controller.name = "PS5 Controller"
        mock_event.controller = mock_controller

        handler.handle_device_event(mock_event)

        # Verify message was logged
        assert mock_game.message_log.add_message.called

    def test_handle_device_removed(self):
        """Test that device removed event removes controller from set."""
        mapper = InputMapper()
        mock_controller = Mock()
        # Set initial name
        type(mock_controller).name = PropertyMock(return_value="Switch Pro Controller")
        handler = GamepadInputHandler(mapper, initial_controllers={mock_controller})

        assert len(handler.controllers) == 1

        # Create remove event
        mock_event = Mock(spec=tcod.event.ControllerDevice)
        mock_event.type = "CONTROLLERDEVICEREMOVED"
        mock_event.which = 0  # Device ID

        # Make controller.name raise RuntimeError (simulates invalid/removed controller)
        # SDL raises RuntimeError when accessing properties of disconnected controllers
        type(mock_controller).name = PropertyMock(side_effect=RuntimeError("Controller invalid"))

        handler.handle_device_event(mock_event)

        # Controller should be removed
        assert len(handler.controllers) == 0

    def test_handle_device_removed_with_message(self):
        """Test that device removed shows message in game."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.message_log = Mock()
        mock_controller = Mock()
        # Set initial name
        type(mock_controller).name = PropertyMock(return_value="Steam Deck Controller")
        mock_controller.instance_id = 42

        handler = GamepadInputHandler(mapper, game=mock_game, initial_controllers={mock_controller})

        mock_event = Mock(spec=tcod.event.ControllerDevice)
        mock_event.type = "CONTROLLERDEVICEREMOVED"
        mock_event.which = 42

        # Make controller.name raise RuntimeError (simulates invalid/removed controller)
        # SDL raises RuntimeError when accessing properties of disconnected controllers
        type(mock_controller).name = PropertyMock(side_effect=RuntimeError("Controller invalid"))

        handler.handle_device_event(mock_event)

        # Verify message was shown
        assert mock_game.message_log.add_message.called


class TestGamepadButtonEvents:
    """Test gamepad button event handling (Phase 2 & 3)."""

    def test_button_event_returns_action(self):
        """Test that button press returns correct action."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Create mock button event (A button in gameplay)
        mock_event = Mock()
        mock_event.button = CB.A
        mock_event.pressed = True  # Pressed

        action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)

        # A button in gameplay should be WAIT (per Phase 3 Option C)
        assert action == InputAction.WAIT

    def test_button_context_sensitive_gameplay_vs_menu(self):
        """Test that same button returns different actions in different contexts."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event = Mock()
        mock_event.button = CB.A
        mock_event.pressed = True

        # A button in gameplay = WAIT
        gameplay_action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert gameplay_action == InputAction.WAIT

        # A button in inventory = CONFIRM (standard Xbox layout: A=confirm, B=cancel)
        menu_action = handler.handle_button_event(mock_event, InputContext.INVENTORY)
        assert menu_action == InputAction.CONFIRM

        # B button in inventory = CANCEL (standard Xbox layout)
        mock_event.button = CB.B
        cancel_action = handler.handle_button_event(mock_event, InputContext.INVENTORY)
        assert cancel_action == InputAction.CANCEL

    def test_dpad_up_maps_to_move_north_in_gameplay(self):
        """Test that D-pad up returns MOVE_NORTH in gameplay."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event = Mock()
        mock_event.button = CB.DPAD_UP
        mock_event.pressed = True

        action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert action == InputAction.MOVE_NORTH

    def test_dpad_navigation_in_menu(self):
        """Test that D-pad works for menu navigation."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event = Mock()
        mock_event.button = CB.DPAD_UP
        mock_event.pressed = True

        action = handler.handle_button_event(mock_event, InputContext.MAIN_MENU)
        assert action == InputAction.NAVIGATE_UP

    def test_shoulder_buttons_cycle_exploits(self):
        """Test that shoulder buttons return exploit cycling actions (Phase 3 Option C)."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Right shoulder = cycle next
        rb_event = Mock()
        rb_event.button = CB.RIGHTSHOULDER
        rb_event.pressed = True

        action = handler.handle_button_event(rb_event, InputContext.GAMEPLAY)
        assert action == InputAction.EXPLOIT_CYCLE_NEXT

        # Left shoulder = cycle prev
        lb_event = Mock()
        lb_event.button = CB.LEFTSHOULDER
        lb_event.pressed = True

        action = handler.handle_button_event(lb_event, InputContext.GAMEPLAY)
        assert action == InputAction.EXPLOIT_CYCLE_PREV

    def test_start_button_opens_main_menu(self):
        """Test that Start button opens main menu (pause) in gameplay."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event = Mock()
        mock_event.button = CB.START
        mock_event.pressed = True

        action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert action == InputAction.EXIT_TO_MENU

    def test_y_button_opens_inventory(self):
        """Test that Y button opens inventory in gameplay."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event = Mock()
        mock_event.button = CB.Y
        mock_event.pressed = True

        action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert action == InputAction.TOGGLE_INVENTORY

    def test_select_button_opens_help(self):
        """Test that Select/Back button opens help (Phase 3)."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)  # Fixed: added required mapper argument

        mock_event = Mock()
        mock_event.button = CB.BACK
        mock_event.pressed = True

        action = handler.handle_button_event(mock_event, InputContext.GAMEPLAY)
        assert action == InputAction.TOGGLE_HELP


class TestGamepadAxisEvents:
    """Test gamepad analog stick and trigger events (Phase 2 & 3)."""

    def test_left_stick_updates_analog_handler_state(self):
        """Test that left stick axis events update analog handler."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Simulate left stick X-axis movement
        mock_event = Mock()
        mock_event.axis = CA.LEFTX
        mock_event.value = 16384  # 50% deflection right

        handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)

        # Verify analog handler state updated
        assert handler.analog_handler.left_x == 16384

    def test_right_stick_updates_analog_handler_state(self):
        """Test that right stick updates are tracked."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        mock_event_x = Mock()
        mock_event_x.axis = CA.RIGHTX
        mock_event_x.value = 10000

        mock_event_y = Mock()
        mock_event_y.axis = CA.RIGHTY
        mock_event_y.value = -15000

        handler.handle_axis_event(mock_event_x, InputContext.GAMEPLAY)
        handler.handle_axis_event(mock_event_y, InputContext.GAMEPLAY)

        assert handler.analog_handler.right_x == 10000
        assert handler.analog_handler.right_y == -15000

    def test_trigger_returns_action_when_pressed(self):
        """Test that trigger press returns appropriate action."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0  # Add turn attribute for gameplay context
        handler = GamepadInputHandler(mapper, game=mock_game)

        # Right trigger in gameplay = EXPLOIT_EXECUTE (Phase 3 Option C)
        # First set trigger to unpressed state
        unpressed_event = Mock()
        unpressed_event.axis = CA.TRIGGERRIGHT
        unpressed_event.value = 0
        handler.handle_axis_event(unpressed_event, InputContext.GAMEPLAY)

        # Now press trigger (rising edge should fire action)
        pressed_event = Mock()
        pressed_event.axis = CA.TRIGGERRIGHT
        pressed_event.value = 30000  # ~91% pressed (above threshold)

        action = handler.handle_axis_event(pressed_event, InputContext.GAMEPLAY)

        # Should return EXPLOIT_EXECUTE
        assert action == InputAction.EXPLOIT_EXECUTE

    def test_left_trigger_activates_look_mode(self):
        """Test that left trigger activates look mode (Phase 3 Option C)."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0  # Add turn attribute for gameplay context
        handler = GamepadInputHandler(mapper, game=mock_game)

        # First set trigger to unpressed
        unpressed_event = Mock()
        unpressed_event.axis = CA.TRIGGERLEFT
        unpressed_event.value = 0
        handler.handle_axis_event(unpressed_event, InputContext.GAMEPLAY)

        # Now press trigger (rising edge)
        pressed_event = Mock()
        pressed_event.axis = CA.TRIGGERLEFT
        pressed_event.value = 25000  # ~76% pressed

        action = handler.handle_axis_event(pressed_event, InputContext.GAMEPLAY)

        assert action == InputAction.TOGGLE_LOOK_MODE


class TestGamepadMovementIntegration:
    """Test integrated movement from analog stick to actions (Phase 2 & 3)."""

    def test_left_stick_movement_generates_action(self):
        """Test that left stick deflection generates movement action (after settling)."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn_count = 0
        handler = GamepadInputHandler(mapper, game=mock_game)

        # Set stick to northeast (with settling)
        movement = get_movement_with_settling(
            handler.analog_handler, mock_game.turn_count, 25000, -25000
        )

        # Should return (1, -1) for northeast
        assert movement == (1, -1)

    def test_left_stick_respects_time_gating(self):
        """Test that analog stick movement respects time-based gating."""
        from rsp.core.config import GameConfig

        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn_count = 5
        handler = GamepadInputHandler(mapper, game=mock_game)

        # First movement (with settling)
        movement1 = get_movement_with_settling(
            handler.analog_handler, mock_game.turn_count, 30000, 0
        )
        assert movement1 is not None

        # Second movement immediately after should be blocked (time-based)
        movement2 = handler.analog_handler.get_left_stick_movement_gameplay(mock_game.turn_count)
        assert movement2 is None

        # After initial delay, movement should work again
        # Simulate time passing by backdating the last move time
        handler.analog_handler.last_gameplay_move_time = (
            time.time() - GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY - 0.05
        )
        movement3 = handler.analog_handler.get_left_stick_movement_gameplay(mock_game.turn_count)
        assert movement3 is not None

    def test_stick_below_deadzone_returns_no_movement(self):
        """Test that small stick movements are filtered by deadzone."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn_count = 0
        handler = GamepadInputHandler(mapper, game=mock_game)

        # Set stick to 10% deflection (below 15% deadzone)
        handler.analog_handler.update_left_stick(x=3277, y=0)

        movement = handler.analog_handler.get_left_stick_movement_gameplay(mock_game.turn_count)

        # Should return None (filtered by deadzone)
        assert movement is None


class TestExploitCycling:
    """Test exploit cycling functionality (Phase 2.7 & 3)."""

    def test_exploit_cycle_next_action_exists(self):
        """Test that EXPLOIT_CYCLE_NEXT action exists."""
        assert InputAction.EXPLOIT_CYCLE_NEXT
        assert InputAction.EXPLOIT_CYCLE_PREV
        assert InputAction.EXPLOIT_EXECUTE

    def test_shoulder_buttons_generate_cycle_actions(self):
        """Test that shoulder buttons map to cycle actions."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Right shoulder
        rb_event = Mock()
        rb_event.button = CB.RIGHTSHOULDER
        rb_event.pressed = True

        action = handler.handle_button_event(rb_event, InputContext.GAMEPLAY)
        assert action == InputAction.EXPLOIT_CYCLE_NEXT

        # Left shoulder
        lb_event = Mock()
        lb_event.button = CB.LEFTSHOULDER
        lb_event.pressed = True

        action = handler.handle_button_event(lb_event, InputContext.GAMEPLAY)
        assert action == InputAction.EXPLOIT_CYCLE_PREV


class TestContextDetection:
    """Test input context detection for context-sensitive bindings."""

    def test_gameplay_context_is_default(self):
        """Test that GAMEPLAY is a valid context."""
        assert InputContext.GAMEPLAY

    def test_menu_contexts_exist(self):
        """Test that menu contexts are defined."""
        assert InputContext.MAIN_MENU
        assert InputContext.SETTINGS_MENU

    def test_modal_contexts_exist(self):
        """Test that modal contexts (inventory, help, etc.) are defined."""
        assert InputContext.INVENTORY
        assert InputContext.HELP
        assert InputContext.LOOK_MODE
        assert InputContext.TARGETING

    def test_dialogue_context_exists(self):
        """Test that dialogue context is defined."""
        assert InputContext.DIALOGUE


class TestDefaultGamepadBindings:
    """Test that default gamepad bindings match Phase 3 Option C specification."""

    def test_option_c_face_buttons_in_gameplay(self):
        """Test Option C face button mappings in gameplay."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # A = Wait
        a_event = Mock()
        a_event.button = CB.A
        a_event.pressed = True
        assert handler.handle_button_event(a_event, InputContext.GAMEPLAY) == InputAction.WAIT

        # B = Cancel (for UI consistency)
        b_event = Mock()
        b_event.button = CB.B
        b_event.pressed = True
        assert handler.handle_button_event(b_event, InputContext.GAMEPLAY) == InputAction.CANCEL

        # Y = Inventory (changed from Exploit 1)
        y_event = Mock()
        y_event.button = CB.Y
        y_event.pressed = True
        assert (
            handler.handle_button_event(y_event, InputContext.GAMEPLAY)
            == InputAction.TOGGLE_INVENTORY
        )

        # X = Exploit 1 (changed from Exploit 2)
        x_event = Mock()
        x_event.button = CB.X
        x_event.pressed = True
        assert (
            handler.handle_button_event(x_event, InputContext.GAMEPLAY)
            == InputAction.EXPLOIT_SLOT_1
        )

    def test_option_c_triggers_in_gameplay(self):
        """Test Option C trigger mappings (RT = execute, LT = look)."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        handler = GamepadInputHandler(mapper, game=mock_game)

        # RT = Execute selected exploit (test rising edge)
        unpressed_rt = Mock()
        unpressed_rt.axis = CA.TRIGGERRIGHT
        unpressed_rt.value = 0
        handler.handle_axis_event(unpressed_rt, InputContext.GAMEPLAY)

        pressed_rt = Mock()
        pressed_rt.axis = CA.TRIGGERRIGHT
        pressed_rt.value = 30000  # Pressed
        assert (
            handler.handle_axis_event(pressed_rt, InputContext.GAMEPLAY)
            == InputAction.EXPLOIT_EXECUTE
        )

        # LT = Look mode (test rising edge)
        unpressed_lt = Mock()
        unpressed_lt.axis = CA.TRIGGERLEFT
        unpressed_lt.value = 0
        handler.handle_axis_event(unpressed_lt, InputContext.GAMEPLAY)

        pressed_lt = Mock()
        pressed_lt.axis = CA.TRIGGERLEFT
        pressed_lt.value = 30000
        assert (
            handler.handle_axis_event(pressed_lt, InputContext.GAMEPLAY)
            == InputAction.TOGGLE_LOOK_MODE
        )

    def test_option_c_menu_buttons(self):
        """Test Option C menu button mappings."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Start = Main menu (pause)
        start_event = Mock()
        start_event.button = CB.START
        start_event.pressed = True
        assert (
            handler.handle_button_event(start_event, InputContext.GAMEPLAY)
            == InputAction.EXIT_TO_MENU
        )

        # Back/Select = Help
        back_event = Mock()
        back_event.button = CB.BACK
        back_event.pressed = True
        assert (
            handler.handle_button_event(back_event, InputContext.GAMEPLAY)
            == InputAction.TOGGLE_HELP
        )

    def test_all_8_dpad_directions_work(self):
        """Test that all 8 D-pad directions map to movement."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        directions = [
            (CB.DPAD_UP, InputAction.MOVE_NORTH),
            (CB.DPAD_DOWN, InputAction.MOVE_SOUTH),
            (CB.DPAD_LEFT, InputAction.MOVE_WEST),
            (CB.DPAD_RIGHT, InputAction.MOVE_EAST),
        ]

        for button, expected_action in directions:
            event = Mock()
            event.button = button
            event.pressed = True
            action = handler.handle_button_event(event, InputContext.GAMEPLAY)
            assert action == expected_action


class TestRightStickBehavior:
    """Test Phase 3 right stick auto-look mode and cursor control."""

    def test_right_stick_magnitude_calculation(self):
        """Test that right stick magnitude is calculated correctly."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Set right stick to 50% northeast
        handler.analog_handler.update_right_stick(x=16384, y=-16384)

        magnitude = handler.analog_handler.get_right_stick_magnitude()

        # Should be roughly 0.5 (after deadzone scaling)
        assert 0.3 < magnitude < 0.7

    def test_right_stick_position_returns_normalized_values(self):
        """Test that right stick position is normalized."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Set stick to full deflection east
        handler.analog_handler.update_right_stick(x=32767, y=0)

        x, y = handler.analog_handler.get_right_stick_position()

        # X should be close to 1.0, Y close to 0.0
        assert abs(x - 1.0) < 0.1
        assert abs(y) < 0.1


class TestTriggerEdgeDetection:
    """Test trigger edge detection (fire once per press, not continuously)."""

    def test_trigger_fires_once_per_press(self):
        """Test that trigger only fires on rising edge, not while held."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # First press should fire
        pressed1 = handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=True)
        assert pressed1 is True

        # Holding trigger should NOT fire again
        pressed2 = handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=True)
        assert pressed2 is False

        # Releasing and pressing again should fire
        handler.analog_handler.check_trigger_pressed(0, is_right_trigger=True)  # Release
        pressed3 = handler.analog_handler.check_trigger_pressed(
            30000, is_right_trigger=True
        )  # Press
        assert pressed3 is True

    def test_left_and_right_triggers_tracked_independently(self):
        """Test that left and right triggers have separate edge detection."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Press right trigger
        rt_pressed = handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=True)
        assert rt_pressed is True

        # Press left trigger (should fire even though RT held)
        lt_pressed = handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=False)
        assert lt_pressed is True

        # Holding both should not fire
        assert handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=True) is False
        assert handler.analog_handler.check_trigger_pressed(30000, is_right_trigger=False) is False


class TestInputMapperGamepadSupport:
    """Test that InputMapper supports gamepad bindings alongside keyboard."""

    def test_mapper_has_gamepad_button_mappings(self):
        """Test that mapper can store gamepad button mappings."""
        mapper = InputMapper()

        # Verify mapper has internal structures for gamepad mappings
        assert hasattr(mapper, "_default_gamepad_button_map")

    def test_mapper_can_get_action_for_gamepad_button(self):
        """Test that mapper can return actions for gamepad buttons."""
        mapper = InputMapper()

        # Get action for A button in gameplay
        action = mapper.get_action_for_gamepad_button(CB.A, InputContext.GAMEPLAY)

        assert action == InputAction.WAIT

    def test_mapper_can_get_action_for_trigger(self):
        """Test that mapper can return actions for triggers."""
        mapper = InputMapper()

        # Get action for right trigger in gameplay
        action = mapper.get_action_for_gamepad_axis(CA.TRIGGERRIGHT, InputContext.GAMEPLAY)

        assert action == InputAction.EXPLOIT_EXECUTE


class TestMovementGatingReset:
    """Test that movement gating can be reset between contexts."""

    def test_reset_movement_gating(self):
        """Test that gameplay movement gating resets correctly."""
        handler = AnalogStickHandler()

        # Set up some gameplay movement state
        handler.last_gameplay_move_time = 123.456
        handler.gameplay_is_repeating = True
        handler.last_gameplay_direction = (1, 0)

        # Reset gating
        handler.reset_movement_gating()

        # Check all state is cleared
        assert handler.last_gameplay_move_time == -1.0
        assert handler.gameplay_is_repeating is False
        assert handler.last_gameplay_direction == (0, 0)

    def test_menu_navigation_reset(self):
        """Test that menu navigation state resets."""
        handler = AnalogStickHandler()

        # Set menu navigation state
        handler.menu_is_repeating = True
        handler.last_menu_move_time = 123.456

        # Reset
        handler.reset_menu_navigation()

        assert handler.menu_is_repeating is False
        assert handler.last_menu_move_time == -1.0  # Reset to "never moved" state


class TestSwapSticksFeature:
    """Test the swap sticks accessibility feature."""

    def test_left_stick_updates_left_handler_without_swap(self):
        """Without swap_sticks, left stick updates left handler state."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = False
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send left stick X event
        mock_event = Mock()
        mock_event.axis = CA.LEFTX
        mock_event.value = 20000

        handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)

        # Left stick should be updated
        assert handler.analog_handler.left_x == 20000
        assert handler.analog_handler.right_x == 0

    def test_left_stick_triggers_look_mode_with_swap(self):
        """With swap_sticks enabled, left stick triggers look mode (not movement)."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = True  # Swap enabled
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send left stick X event with high value (above look mode threshold)
        mock_event = Mock()
        mock_event.axis = CA.LEFTX
        mock_event.value = 25000

        # Physical left stick value is stored in left_x (no storage swap)
        handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)
        assert handler.analog_handler.left_x == 25000

        # With swap enabled, left stick triggers look mode
        result = handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)
        assert result == InputAction.TOGGLE_LOOK_MODE

    def test_right_stick_controls_movement_with_swap(self):
        """With swap_sticks enabled, right stick controls gameplay movement."""
        import time

        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = True  # Swap enabled
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send right stick Y event (downward)
        mock_event = Mock()
        mock_event.axis = CA.RIGHTY
        mock_event.value = 25000  # Strong downward

        # Physical right stick value is stored in right_y (no storage swap)
        handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)
        assert handler.analog_handler.right_y == 25000

        # Bypass settling period by pre-setting the settling start time in the past
        analog = handler.analog_handler
        analog._settling_start_time = time.time() - 0.1  # Started settling 100ms ago
        analog.last_gameplay_move_time = -1.0  # Still in first-deflection state

        # Now call should complete settling and return movement
        result = handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)

        # With swap enabled, right stick triggers movement (south)
        assert result == InputAction.MOVE_SOUTH

    def test_storage_not_swapped_read_is_swapped(self):
        """Test that physical stick data is stored without swap - swap happens at read time."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = True
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send all 4 axis events
        events = [
            (CA.LEFTX, 10000),
            (CA.LEFTY, 11000),
            (CA.RIGHTX, 12000),
            (CA.RIGHTY, 13000),
        ]

        for axis, value in events:
            mock_event = Mock()
            mock_event.axis = axis
            mock_event.value = value
            handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)

        # Storage is NOT swapped - physical values stay in their physical variables
        assert handler.analog_handler.left_x == 10000  # LEFTX -> left_x (physical)
        assert handler.analog_handler.left_y == 11000  # LEFTY -> left_y (physical)
        assert handler.analog_handler.right_x == 12000  # RIGHTX -> right_x (physical)
        assert handler.analog_handler.right_y == 13000  # RIGHTY -> right_y (physical)

        # The swap happens at READ time when calling movement/look methods

    def test_swap_sticks_defaults_to_false(self):
        """Test that swap_sticks defaults to False when setting is missing."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock(spec=[])  # Empty spec - no attributes
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send left stick event
        mock_event = Mock()
        mock_event.axis = CA.LEFTX
        mock_event.value = 20000

        handler.handle_axis_event(mock_event, InputContext.GAMEPLAY)

        # Should use default (no swap) - left stick updates left handler
        assert handler.analog_handler.left_x == 20000
        assert handler.analog_handler.right_x == 0

    def test_swap_sticks_produces_navigation_in_menu_with_right_stick(self):
        """With swap_sticks, right stick should produce navigation actions in menus."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = True  # Swap enabled
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send right stick Y event (with swap, this should control menu navigation)
        mock_event = Mock()
        mock_event.axis = CA.RIGHTY
        mock_event.value = 25000  # Strong downward push

        action = handler.handle_axis_event(mock_event, InputContext.MAIN_MENU)

        # Should produce NAVIGATE_DOWN since right stick now controls menus
        assert action == InputAction.NAVIGATE_DOWN

    def test_swap_sticks_no_navigation_from_left_stick_in_menu(self):
        """With swap_sticks, left stick should NOT produce navigation in menus."""
        mapper = InputMapper()
        mock_game = Mock()
        mock_game.turn = 0
        mock_settings = Mock()
        mock_settings.gamepad_enabled = True
        mock_settings.gamepad_swap_sticks = True  # Swap enabled
        mock_settings.gamepad_deadzone = 0.15
        mock_settings.gamepad_threshold = 0.20
        mock_settings.gamepad_direction_locking = True
        mock_game.settings = mock_settings

        handler = GamepadInputHandler(mapper, game=mock_game)

        # Send left stick Y event (with swap, this controls cursor, not menu nav)
        mock_event = Mock()
        mock_event.axis = CA.LEFTY
        mock_event.value = 25000  # Strong downward push

        action = handler.handle_axis_event(mock_event, InputContext.MAIN_MENU)

        # Should NOT produce navigation action (left stick is for cursor now)
        assert action is None


class TestDeltaToMovementAction:
    """Test the _delta_to_movement_action helper method."""

    def test_delta_to_movement_action_exists(self):
        """Verify _delta_to_movement_action method exists (catches typos like _delta_to_navigation_action)."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        # Method should exist
        assert hasattr(handler, "_delta_to_movement_action")
        assert callable(handler._delta_to_movement_action)

    def test_delta_to_movement_action_cardinal_directions(self):
        """Test cardinal direction conversions."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        assert handler._delta_to_movement_action(0, -1) == InputAction.MOVE_NORTH
        assert handler._delta_to_movement_action(0, 1) == InputAction.MOVE_SOUTH
        assert handler._delta_to_movement_action(1, 0) == InputAction.MOVE_EAST
        assert handler._delta_to_movement_action(-1, 0) == InputAction.MOVE_WEST

    def test_delta_to_movement_action_diagonal_directions(self):
        """Test diagonal direction conversions."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        assert handler._delta_to_movement_action(1, -1) == InputAction.MOVE_NORTHEAST
        assert handler._delta_to_movement_action(-1, -1) == InputAction.MOVE_NORTHWEST
        assert handler._delta_to_movement_action(1, 1) == InputAction.MOVE_SOUTHEAST
        assert handler._delta_to_movement_action(-1, 1) == InputAction.MOVE_SOUTHWEST

    def test_delta_to_movement_action_invalid_returns_none(self):
        """Test that invalid deltas return None."""
        mapper = InputMapper()
        handler = GamepadInputHandler(mapper)

        assert handler._delta_to_movement_action(0, 0) is None
        assert handler._delta_to_movement_action(2, 0) is None
        assert handler._delta_to_movement_action(0, 2) is None
