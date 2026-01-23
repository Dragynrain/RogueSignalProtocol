"""
End-to-End Gamepad Integration Tests - REAL gameplay scenarios.

These tests verify that gamepad input actually works for real gameplay,
not just mocked unit tests. They use actual game initialization and
simulate complete user workflows with only gamepad input.

Focus: Can you actually play the game with ONLY a controller?

Uses mock_time fixture for deterministic timing (no flaky time.sleep).
"""

import pytest
import tcod.console
import tcod.context
import tcod.event
import tcod.sdl.joystick
import tcod.tileset

from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.input.actions import InputAction, InputContext
from rsp.input.handler import InputHandler
from rsp.systems.audio import NullSoundManager

# Controller button/axis shortcuts
CB = tcod.sdl.joystick.ControllerButton
CA = tcod.sdl.joystick.ControllerAxis

# Settling period for analog stick (30ms in implementation, use 35ms for safety)
SETTLING_PERIOD_SEC = 0.035


@pytest.fixture
def game_setup():
    """
    Create a real game instance with full initialization.

    This is NOT mocked - it's the actual game engine with real components.
    """
    # Create minimal TCOD context (hidden window for testing)
    tileset = tcod.tileset.load_truetype_font("KreativeSquare.ttf", tile_width=16, tile_height=16)
    context = tcod.context.new(
        width=80,
        height=50,
        tileset=tileset,
        title="Gamepad Test",
        sdl_window_flags=tcod.lib.SDL_WINDOW_HIDDEN,
    )
    console = tcod.console.Console(80, 50)

    # Create game settings
    settings = GameSettings()
    settings.graphics_mode = "text"  # Use text mode for tests

    # Create game engine with actual map generation
    sound_manager = NullSoundManager(settings)
    game = GameEngine(settings=settings, sound_manager=sound_manager)

    # Create input handler with gamepad support
    # Note: We don't have a renderer in this simple setup, but that's okay
    # for most tests. For tests that need renderer, we can create it separately.
    input_handler = InputHandler(game, renderer=None)

    # Clear any starting dialogue so tests start in gameplay mode
    game.dialogue_state.active_dialogue = None
    game.dialogue_state.dialogue_history = []

    yield game, input_handler, console, context

    # Cleanup
    context.close()


class TestGamepadMovement:
    """Test actual player movement with gamepad."""

    def test_dpad_moves_player_north(self, game_setup):
        """D-pad UP actually moves player north."""
        game, input_handler, console, context = game_setup

        initial_x = game.player.x
        initial_y = game.player.y

        # Create D-pad UP event
        dpad_up_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )

        # Handle the event using the controller button handler
        input_handler.handle_controller_button(dpad_up_event)

        # Player should have moved north (y decreased)
        assert game.player.y < initial_y, "Player should move north"
        assert game.player.x == initial_x, "Player X should not change"

    def test_left_stick_moves_player_full_deflection(self, game_setup, mock_time):
        """Left stick at full deflection moves player."""
        game, input_handler, console, context = game_setup
        analog = input_handler.gamepad_handler.analog_handler

        initial_x = game.player.x
        initial_y = game.player.y
        initial_turn = game.turn

        # Set left stick to full right deflection (directly, not via event handler)
        analog.update_left_stick(x=32767, y=0)

        # Wait for settling period before getting movement
        analog.get_left_stick_movement_gameplay(game.turn)  # Start settling
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement = analog.get_left_stick_movement_gameplay(game.turn)

        # Should get movement delta
        assert movement is not None, "Should get movement from stick"
        assert movement == (1, 0), "Should move east"

    def test_time_gating_prevents_double_move(self, game_setup, mock_time):
        """Time-based gating prevents moving twice immediately."""
        game, input_handler, console, context = game_setup
        analog = input_handler.gamepad_handler.analog_handler

        # Set stick to move east (directly, not via event handler)
        analog.update_left_stick(x=32767, y=0)

        # Wait for settling period then get first movement
        analog.get_left_stick_movement_gameplay(game.turn)  # Start settling
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement1 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement1 is not None, "First movement should succeed"

        # Second movement immediately should be blocked (direction locked + time gating)
        movement2 = analog.get_left_stick_movement_gameplay(game.turn)
        assert movement2 is None, "Second movement immediately should be blocked"

    def test_diagonal_movement_with_dpad(self, game_setup):
        """Test 8-way diagonal movement works."""
        game, input_handler, console, context = game_setup

        # Test northeast (UP + RIGHT would require simultaneous button press)
        # Instead test that the mapper knows about diagonal actions
        from rsp.input.mappings import InputMapper

        mapper = InputMapper()

        # Check diagonal actions exist
        assert InputAction.MOVE_NORTHEAST
        assert InputAction.MOVE_NORTHWEST
        assert InputAction.MOVE_SOUTHEAST
        assert InputAction.MOVE_SOUTHWEST

        # Check mapper can convert to deltas
        ne_delta = mapper.get_movement_delta(InputAction.MOVE_NORTHEAST)
        assert ne_delta == (1, -1), "Northeast should be (+1, -1)"


class TestGamepadExploitCycling:
    """Test exploit cycling with shoulder buttons."""

    def test_shoulder_button_cycles_exploits(self, game_setup):
        """Right shoulder button cycles to next exploit."""
        game, input_handler, console, context = game_setup

        # Set up 3 exploits for testing
        game.player.inventory_manager.equipped_exploits = [
            "buffer_overflow",
            "system_crash",
            "code_injection",
        ]
        equipped_exploits = [e for e in game.player.exploits if e is not None]

        initial_index = game.selected_exploit_index

        # Press right shoulder to cycle
        rb_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.RIGHTSHOULDER, pressed=True
        )

        input_handler.handle_controller_button(rb_event)

        # Index should have changed
        assert game.selected_exploit_index != initial_index
        expected_index = (initial_index + 1) % len(equipped_exploits)
        assert game.selected_exploit_index == expected_index

    def test_left_shoulder_cycles_backwards(self, game_setup):
        """Left shoulder button cycles to previous exploit."""
        game, input_handler, console, context = game_setup

        # Set up 3 exploits for testing
        game.player.inventory_manager.equipped_exploits = [
            "buffer_overflow",
            "system_crash",
            "code_injection",
        ]
        equipped_exploits = [e for e in game.player.exploits if e is not None]

        # Set to exploit 1
        game.selected_exploit_index = 1

        # Press left shoulder to cycle backwards
        lb_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.LEFTSHOULDER, pressed=True
        )

        input_handler.handle_controller_button(lb_event)

        # Should be back to 0
        assert game.selected_exploit_index == 0

    def test_keyboard_bracket_keys_cycle_exploits(self, game_setup):
        """Keyboard [ and ] keys also cycle exploits."""
        game, input_handler, console, context = game_setup

        # Set up 3 exploits for testing
        game.player.inventory_manager.equipped_exploits = [
            "buffer_overflow",
            "system_crash",
            "code_injection",
        ]
        equipped_exploits = [e for e in game.player.exploits if e is not None]

        initial_index = game.selected_exploit_index

        # Press ] key to cycle forward
        bracket_right = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHTBRACKET,
            sym=tcod.event.KeySym.RIGHTBRACKET,
            mod=tcod.event.Modifier.NONE,
        )

        input_handler.handle_keydown(bracket_right)

        # Index should have incremented
        expected_index = (initial_index + 1) % len(equipped_exploits)
        assert game.selected_exploit_index == expected_index


class TestGamepadUINavigation:
    """Test opening and navigating UI screens with gamepad."""

    def test_y_button_opens_inventory(self, game_setup):
        """Y button opens inventory screen (standard Xbox layout)."""
        game, input_handler, console, context = game_setup

        assert game.show_inventory is False, "Inventory should start closed"

        # Press Y button
        y_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.Y, pressed=True
        )

        input_handler.handle_controller_button(y_event)

        # Inventory should be open
        assert game.show_inventory is True, "Y button should open inventory"

    def test_start_button_triggers_menu_exit(self, game_setup):
        """Start button triggers exit to main menu (pause)."""
        game, input_handler, console, context = game_setup

        # Press Start button
        start_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.START, pressed=True
        )

        # This should return False to signal exit to menu
        result = input_handler.handle_controller_button(start_event)

        # Result should be False (exit to main menu)
        assert result is False, "Start button should return False (exit to menu)"

    def test_select_button_opens_help(self, game_setup):
        """Select/Back button opens help screen."""
        game, input_handler, console, context = game_setup

        assert game.show_help is False, "Help should start closed"

        # Press Select/Back button
        select_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.BACK, pressed=True
        )

        input_handler.handle_controller_button(select_event)

        # Help should be open
        assert game.show_help is True, "Select button should open help"

    def test_b_button_closes_inventory(self, game_setup):
        """
        B button closes inventory (standard Xbox layout: B=cancel, A=confirm).

        Note: The game uses standard Xbox controller layout where B=cancel, A=confirm.
        """
        game, input_handler, console, context = game_setup

        # Open inventory first
        game.show_inventory = True

        # Press B button (cancel in standard Xbox layout)
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=CB.B,  # B button = cancel in inventory (standard Xbox layout)
            pressed=True,
        )

        result = input_handler.handle_controller_button(b_event)

        # Inventory should be closed
        assert game.show_inventory is False, "B button (cancel) should close inventory"


class TestGamepadContextDetection:
    """Test that input context is correctly detected for gamepad."""

    def test_gameplay_context_when_no_menus_open(self, game_setup):
        """Context should be GAMEPLAY when no menus are open."""
        game, input_handler, console, context = game_setup

        # Ensure no menus are open and no active dialogue
        game.show_inventory = False
        game.show_help = False
        game.look_mode = False
        game.targeting_mode = False
        game.dialogue_state.active_dialogue = None  # Clear any starting dialogue

        # Get current context
        context_detected = input_handler._get_current_context()

        assert context_detected == InputContext.GAMEPLAY

    def test_inventory_context_when_inventory_open(self, game_setup):
        """Context should be INVENTORY when inventory is open."""
        game, input_handler, console, context = game_setup

        game.show_inventory = True

        context_detected = input_handler._get_current_context()

        assert context_detected == InputContext.INVENTORY

    def test_help_context_when_help_open(self, game_setup):
        """Context should be HELP when help screen is open."""
        game, input_handler, console, context = game_setup

        game.show_help = True

        context_detected = input_handler._get_current_context()

        assert context_detected == InputContext.HELP

    def test_look_mode_context_when_active(self, game_setup):
        """Context should be LOOK_MODE when look mode is active."""
        game, input_handler, console, context = game_setup

        game.look_mode = True

        context_detected = input_handler._get_current_context()

        assert context_detected == InputContext.LOOK_MODE


class TestGamepadLookMode:
    """Test look mode activation and cursor control with gamepad."""

    def test_left_trigger_toggles_look_mode(self, game_setup):
        """Left trigger activates look mode."""
        game, input_handler, console, context = game_setup

        assert game.look_mode is False, "Look mode should start inactive"

        # Set trigger to unpressed first
        lt_unpressed = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=0
        )
        input_handler.handle_controller_axis(lt_unpressed)

        # Now press trigger
        lt_pressed = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.TRIGGERLEFT, value=30000  # ~91% pressed
        )

        input_handler.handle_controller_axis(lt_pressed)

        # Look mode should activate
        assert game.look_mode is True, "Left trigger should activate look mode"


class TestGamepadActionMapping:
    """Test that gamepad buttons map to correct actions in different contexts."""

    def test_a_button_is_wait_in_gameplay(self, game_setup):
        """A button should map to WAIT action in gameplay context."""
        game, input_handler, console, context = game_setup

        # Ensure we're in gameplay context
        game.show_inventory = False
        game.look_mode = False

        # Create A button event
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        # Get the action that would be generated
        action = input_handler.gamepad_handler.handle_button_event(a_event, InputContext.GAMEPLAY)

        assert action == InputAction.WAIT, "A button should be WAIT in gameplay"

    def test_a_button_is_confirm_in_inventory(self, game_setup):
        """A button should map to CONFIRM in inventory (standard Xbox layout)."""
        game, input_handler, console, context = game_setup

        # Create A button event
        a_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )

        # Get action in inventory context
        action = input_handler.gamepad_handler.handle_button_event(a_event, InputContext.INVENTORY)

        # Note: Using standard Xbox layout where A=confirm, B=cancel
        assert (
            action == InputAction.CONFIRM
        ), "A button should be CONFIRM in inventory (standard Xbox layout)"

    def test_b_button_is_cancel_in_inventory(self, game_setup):
        """B button should map to CANCEL in inventory (standard Xbox layout)."""
        game, input_handler, console, context = game_setup

        # Create B button event
        b_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )

        # Get action in inventory context
        action = input_handler.gamepad_handler.handle_button_event(b_event, InputContext.INVENTORY)

        # Note: Using standard Xbox layout where A=confirm, B=cancel
        assert (
            action == InputAction.CANCEL
        ), "B button should be CANCEL in inventory (standard Xbox layout)"


class TestGamepadFullWorkflow:
    """Test complete gameplay workflows using only gamepad."""

    def test_can_move_and_wait_with_gamepad_only(self, game_setup):
        """Verify basic gameplay loop works with only gamepad."""
        game, input_handler, console, context = game_setup

        initial_x = game.player.x
        initial_y = game.player.y
        initial_turn = game.turn

        # Move north with D-pad
        dpad_up = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.DPAD_UP, pressed=True
        )
        input_handler.handle_controller_button(dpad_up)

        # Should have moved
        assert game.player.y < initial_y, "Should move north"
        assert game.turn > initial_turn, "Turn should advance"

        # Wait with A button
        current_turn = game.turn
        a_button = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.A, pressed=True
        )
        input_handler.handle_controller_button(a_button)

        # Turn should advance (waited)
        assert game.turn > current_turn, "Wait should advance turn"

    def test_can_open_and_close_menus_with_gamepad(self, game_setup):
        """Verify menu navigation works with gamepad."""
        game, input_handler, console, context = game_setup

        # Open inventory with Y button (standard Xbox layout)
        y_button = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.Y, pressed=True
        )
        input_handler.handle_controller_button(y_button)
        assert game.show_inventory is True, "Y button should open inventory"

        # Close with B button (standard Xbox layout: B=cancel)
        b_button_cancel = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN", which=0, button=CB.B, pressed=True
        )
        input_handler.handle_controller_button(b_button_cancel)
        assert (
            game.show_inventory is False
        ), "B button should close inventory (standard Xbox layout)"

        # Note: Help menu test skipped because it requires renderer for proper menu handling
        # The individual test_select_button_opens_help verifies help opens correctly


class TestGamepadDeadzone:
    """Test analog stick deadzone handling."""

    def test_small_stick_movement_ignored(self, game_setup):
        """Stick deflection below deadzone should be ignored."""
        game, input_handler, console, context = game_setup

        # 10% deflection (below 15% deadzone)
        small_x = int(32768 * 0.1)

        stick_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=CA.LEFTX, value=small_x
        )
        input_handler.handle_controller_axis(stick_event)

        # Should not generate movement
        movement = input_handler.gamepad_handler.analog_handler.get_left_stick_movement_gameplay(
            game.turn
        )

        assert movement is None, "Small deflection should be filtered by deadzone"

    def test_large_stick_movement_registered(self, game_setup, mock_time):
        """Stick deflection above threshold should register."""
        game, input_handler, console, context = game_setup
        analog = input_handler.gamepad_handler.analog_handler

        # 50% deflection (above threshold) - use direct update to avoid consuming movement
        large_x = int(32768 * 0.5)
        analog.update_left_stick(x=large_x, y=0)

        # Wait for settling period then get movement
        analog.get_left_stick_movement_gameplay(game.turn)  # Start settling
        mock_time.advance(SETTLING_PERIOD_SEC)
        movement = analog.get_left_stick_movement_gameplay(game.turn)

        assert movement is not None, "Large deflection should generate movement"
        assert movement == (1, 0), "Should move east"
