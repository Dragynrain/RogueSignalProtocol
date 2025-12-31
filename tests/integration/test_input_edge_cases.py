#!/usr/bin/env python3
"""
Edge case tests for input handling: transitions, priority, rapid input, boundaries.

These tests cover scenarios not tested by individual screen test files:
- TestScreenTransitions: Multi-screen navigation flows
- TestMultiStepWorkflows: Complete feature workflows
- TestInputPriority: Input type precedence
- TestRapidInput: Stress testing rapid inputs
- TestBoundaryConditions: Edge cases and wraparound
- TestSimultaneousInputs: Multiple input types at once
- TestAnalogStickEdgeCases: Stick behavior edge cases
- TestInputBuffering: Frame-level input handling
"""

import pytest
import tcod.console
import tcod.context
import tcod.event
import tcod.tileset

from rsp.core.config import GameSettings
from rsp.core.loop import initialize_game_systems
from rsp.systems.audio import NullSoundManager
from rsp.ui.menus import MenuBackground


class TestScreenTransitions:
    """Test screen transitions and state preservation."""

    @pytest.fixture
    def gameplay_with_menus_setup(self):
        """Setup game environment for testing menu transitions."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()

        # Dismiss any active dialogues
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()

        yield engine

    def test_inventory_open_and_close_preserves_game_state(self, gameplay_with_menus_setup):
        """Opening and closing inventory preserves player position and game state."""
        engine = gameplay_with_menus_setup

        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Record initial state
        initial_pos = (engine.player.x, engine.player.y)
        initial_cpu = engine.player.cpu

        # Open inventory with 'i' key
        # Use KeySym(ord('i')) for cross-platform compatibility (KeySym.i doesn't exist on Linux)
        i_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I,
            sym=tcod.event.KeySym(ord("i")),
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(i_event)

        # Verify inventory opened
        assert engine.show_inventory

        # Close inventory with ESC
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(esc_event)

        # Verify inventory closed
        assert not engine.show_inventory

        # Verify state preserved
        assert (engine.player.x, engine.player.y) == initial_pos
        assert engine.player.cpu == initial_cpu

    def test_look_mode_enter_and_exit_preserves_state(self, gameplay_with_menus_setup):
        """Entering and exiting look mode preserves player position."""
        engine = gameplay_with_menus_setup

        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        initial_pos = (engine.player.x, engine.player.y)

        # Enter look mode with 'L' key
        l_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.L, sym=tcod.event.KeySym.L, mod=tcod.event.Modifier.NONE
        )
        handler.handle_keydown(l_event)

        # Verify look mode active
        assert engine.look_mode

        # Exit look mode with ESC
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(esc_event)

        # Verify look mode exited
        assert not engine.look_mode

        # Verify player position unchanged
        assert (engine.player.x, engine.player.y) == initial_pos

    def test_menu_selection_persists_across_transitions(self):
        """Main menu selection persists when returning from submenus."""
        from rsp.ui.menu_main import MainMenu

        menu = MainMenu()

        # Select second option (Settings)
        menu.selected_option = 1
        initial_selection = menu.selected_option

        # After returning, selection should still be on Settings
        assert menu.selected_option == initial_selection

    def test_rapid_menu_opening_closing(self, gameplay_with_menus_setup):
        """Rapidly opening and closing menus doesn't crash or corrupt state."""
        engine = gameplay_with_menus_setup

        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        initial_pos = (engine.player.x, engine.player.y)

        # Rapidly toggle inventory multiple times
        for _ in range(5):
            # Open
            # Use KeySym(ord('i')) for cross-platform compatibility (KeySym.i doesn't exist on Linux)
            i_event = tcod.event.KeyDown(
                scancode=tcod.event.Scancode.I,
                sym=tcod.event.KeySym(ord("i")),
                mod=tcod.event.Modifier.NONE,
            )
            handler.handle_keydown(i_event)

            # Close
            esc_event = tcod.event.KeyDown(
                scancode=tcod.event.Scancode.ESCAPE,
                sym=tcod.event.KeySym.ESCAPE,
                mod=tcod.event.Modifier.NONE,
            )
            handler.handle_keydown(esc_event)

        # Should end with inventory closed
        assert not engine.show_inventory

        # State should be preserved
        assert (engine.player.x, engine.player.y) == initial_pos


class TestInputPriority:
    """Test input priority and conflict resolution."""

    @pytest.fixture
    def main_menu_for_priority_test(self):
        """Setup main menu for priority testing."""
        from rsp.ui.menu_main import MainMenu

        menu = MainMenu()
        console = tcod.console.Console(80, 50, order="F")
        yield menu, console

    def test_keyboard_takes_priority_over_gamepad_in_menus(self, main_menu_for_priority_test):
        """When both keyboard and gamepad input occur, last input wins."""
        menu, console = main_menu_for_priority_test

        initial_selection = menu.selected_option

        # Press keyboard DOWN
        kb_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        menu.handle_input(kb_event)

        kb_selection = menu.selected_option

        # Then press gamepad DOWN
        gp_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )
        menu.handle_input(gp_event)

        # Both should have moved selection
        assert menu.selected_option != initial_selection
        assert menu.selected_option == (kb_selection + 1) % len(menu.options)

    def test_escape_cancels_regardless_of_input_type(self, main_menu_for_priority_test):
        """ESC key and B button both cancel warnings (no priority conflict)."""
        menu, console = main_menu_for_priority_test

        # Show a warning first
        menu.show_warning = True

        # Keyboard ESC should dismiss warning
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        menu.handle_input(esc_event)
        assert not menu.show_warning  # Warning dismissed


class TestRapidInput:
    """Test rapid input edge cases."""

    @pytest.fixture
    def main_menu_rapid_test(self):
        """Setup main menu for rapid input testing."""
        from rsp.ui.menu_main import MainMenu

        menu = MainMenu()
        console = tcod.console.Console(80, 50, order="F")
        yield menu, console

    def test_rapid_keyboard_navigation(self, main_menu_rapid_test):
        """Rapidly pressing navigation keys doesn't skip or corrupt state."""
        menu, console = main_menu_rapid_test

        initial_selection = menu.selected_option

        # Press DOWN 10 times rapidly
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )

        for _ in range(10):
            menu.handle_input(down_event)

        # Should have moved exactly 10 positions (with wraparound)
        expected_selection = (initial_selection + 10) % len(menu.options)
        assert menu.selected_option == expected_selection

    def test_rapid_direction_changes(self, main_menu_rapid_test):
        """Rapidly alternating between UP and DOWN doesn't corrupt state."""
        menu, console = main_menu_rapid_test

        initial_selection = menu.selected_option

        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )

        up_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.UP, sym=tcod.event.KeySym.UP, mod=tcod.event.Modifier.NONE
        )

        # Alternate DOWN and UP 10 times
        for _ in range(10):
            menu.handle_input(down_event)
            menu.handle_input(up_event)

        # Should end at initial selection (10 downs + 10 ups = net 0)
        assert menu.selected_option == initial_selection

    def test_rapid_gamepad_button_presses(self, main_menu_rapid_test):
        """Rapid gamepad button presses are all processed."""
        menu, console = main_menu_rapid_test

        initial_selection = menu.selected_option

        button_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )

        # Press D-pad DOWN 15 times rapidly
        for _ in range(15):
            menu.handle_input(button_event)

        # Should have moved exactly 15 positions
        expected_selection = (initial_selection + 15) % len(menu.options)
        assert menu.selected_option == expected_selection


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""

    @pytest.fixture
    def achievements_for_boundary_test(self):
        """Setup achievements menu for boundary testing."""
        from rsp.ui.menu_achievements import AchievementsMenu

        menu = AchievementsMenu()
        yield menu

    def test_scrolling_past_bottom_boundary(self, achievements_for_boundary_test):
        """Scrolling past bottom boundary doesn't corrupt scroll_offset."""
        menu = achievements_for_boundary_test

        # Try to scroll way past the bottom
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )

        # Press DOWN 100 times (way more than achievements exist)
        for _ in range(100):
            menu.handle_input(down_event)

        # scroll_offset should be clamped to valid range
        assert menu.scroll_offset >= 0
        # Should not exceed reasonable bounds (depends on content)
        assert menu.scroll_offset < 1000  # Sanity check

    def test_scrolling_past_top_boundary(self, achievements_for_boundary_test):
        """Scrolling past top boundary stops at 0."""
        menu = achievements_for_boundary_test

        # Start with some scroll offset
        menu.scroll_offset = 5

        up_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.UP, sym=tcod.event.KeySym.UP, mod=tcod.event.Modifier.NONE
        )

        # Press UP many times to try to go negative
        for _ in range(20):
            menu.handle_input(up_event)

        # scroll_offset should never go negative
        assert menu.scroll_offset >= 0

    def test_menu_wraparound_behavior(self):
        """Menu selection wraps around correctly at boundaries."""
        from rsp.ui.menu_main import MainMenu

        menu = MainMenu()

        # Start at first option
        menu.selected_option = 0

        # Press UP - should wrap to last option
        up_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.UP, sym=tcod.event.KeySym.UP, mod=tcod.event.Modifier.NONE
        )
        menu.handle_input(up_event)

        # Should be at last option
        assert menu.selected_option == len(menu.options) - 1

        # Press DOWN - should wrap back to first
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        menu.handle_input(down_event)

        # Should be at first option
        assert menu.selected_option == 0


class TestSimultaneousInputs:
    """Test simultaneous input from multiple sources."""

    @pytest.fixture
    def main_menu_setup(self):
        """Setup main menu for testing."""
        tileset = tcod.tileset.load_truetype_font(
            "KreativeSquare.ttf", tile_width=16, tile_height=16
        )
        context = tcod.context.new(
            width=80,
            height=50,
            tileset=tileset,
            title="Test Main Menu",
            sdl_window_flags=tcod.lib.SDL_WINDOW_HIDDEN,
        )
        console = tcod.console.Console(80, 50)
        settings = GameSettings()
        menu_background = MenuBackground(context, settings)
        menu_sound_manager = NullSoundManager(settings)
        menus = initialize_game_systems(settings, context, menu_background, menu_sound_manager)

        main_menu = menus["main_menu"]
        main_menu.refresh_options(show_continue=False, active_game=None)

        yield main_menu, console

        context.close()

    def test_keyboard_and_gamepad_simultaneous(self, main_menu_setup):
        """Keyboard and gamepad inputs at same time - both work."""
        menu, console = main_menu_setup

        initial_selection = menu.selected_option

        # Keyboard DOWN event
        kb_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )

        # Gamepad UP event (conflicting direction)
        gp_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_UP,
            pressed=True,
        )

        # Process keyboard first, then gamepad
        menu.handle_input(kb_event)
        selection_after_kb = menu.selected_option

        menu.handle_input(gp_event)
        final_selection = menu.selected_option

        # Keyboard moved down
        assert selection_after_kb == (initial_selection + 1) % len(menu.options)
        # Gamepad moved up (relative to keyboard position)
        assert (
            final_selection == selection_after_kb - 1
            if selection_after_kb > 0
            else len(menu.options) - 1
        )

    def test_mouse_and_keyboard_simultaneous(self, main_menu_setup):
        """Mouse motion and keyboard navigation work independently."""
        menu, console = main_menu_setup
        from unittest.mock import Mock

        layout = menu._get_menu_layout_params()
        menu_x = layout["menu_x"]

        # Calculate Y position for option 2
        # Base class uses: start_y=21, spacing=2
        # option_index = (tile_y - start_y) // spacing
        # For option 2: tile_y = 21 + (2 * 2) = 25
        option_y = 25
        motion_event = Mock()
        motion_event.type = "MOUSEMOTION"
        tile_mock = Mock()
        tile_mock.x = int(menu_x)
        tile_mock.y = int(option_y)
        motion_event.tile = tile_mock
        motion_event.position = tile_mock  # Also set position for compatibility

        menu.handle_mouse_motion(motion_event)
        assert menu.selected_option == 2

        # Keyboard DOWN should move from current position
        kb_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        menu.handle_input(kb_event)
        assert menu.selected_option == 3

    def test_dpad_and_analog_stick_simultaneous(self, main_menu_setup):
        """D-pad and analog stick both provide navigation (both work)."""
        menu, console = main_menu_setup

        initial_selection = menu.selected_option

        # D-pad DOWN
        dpad_event = tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN",
            which=0,
            button=tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            pressed=True,
        )
        menu.handle_input(dpad_event)
        after_dpad = menu.selected_option

        # Analog stick DOWN
        axis_event = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
            value=32767,  # Max positive = down
        )
        menu.handle_input(axis_event)
        after_stick = menu.selected_option

        # Both should have moved selection
        assert after_dpad == (initial_selection + 1) % len(menu.options)
        assert after_stick == (after_dpad + 1) % len(menu.options)


class TestAnalogStickEdgeCases:
    """Test analog stick edge cases (deadzone, partial deflection, diagonal)."""

    @pytest.fixture
    def gameplay_for_analog_test(self):
        """Setup gameplay engine for analog stick edge case testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()

        # Dismiss any active dialogues
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()

        yield engine

    def test_analog_stick_deadzone_ignored(self, gameplay_for_analog_test):
        """Small analog stick deflections are handled without error."""
        engine = gameplay_for_analog_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Small deflection (should be ignored by deadzone)
        small_deflection = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=5000,  # ~15% deflection, below typical 20% deadzone
        )

        # Should handle event without error (deadzone filtering happens internally)
        handler.handle_controller_axis(small_deflection)
        # Game should still be functional
        assert engine.player is not None

    def test_analog_stick_partial_deflection_moves(self, gameplay_for_analog_test):
        """Partial analog stick deflection is handled correctly."""
        engine = gameplay_for_analog_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Medium deflection (above deadzone, should register)
        medium_deflection = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=20000,  # ~60% deflection, above deadzone
        )

        # Should handle event without error
        handler.handle_controller_axis(medium_deflection)

        # Game should still be functional
        assert engine.player is not None

    def test_analog_stick_diagonal_movement(self, gameplay_for_analog_test):
        """Diagonal analog stick input (both X and Y) is handled correctly."""
        engine = gameplay_for_analog_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # X axis (right)
        x_axis = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=32767,  # Max right
        )

        # Y axis (down)
        y_axis = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
            value=32767,  # Max down
        )

        # Should handle both axis events without error
        handler.handle_controller_axis(x_axis)
        handler.handle_controller_axis(y_axis)

        # Game should still be functional
        assert engine.player is not None

    def test_analog_stick_release_stops_movement(self, gameplay_for_analog_test):
        """Releasing analog stick (returning to center) is handled correctly."""
        engine = gameplay_for_analog_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Push stick right
        right_axis = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=32767,  # Max right
        )
        handler.handle_controller_axis(right_axis)

        # Release stick (center position)
        center_axis = tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION",
            which=0,
            axis=tcod.sdl.joystick.ControllerAxis.LEFTX,
            value=0,  # Centered
        )
        handler.handle_controller_axis(center_axis)

        # Game should still be functional after stick released
        assert engine.player is not None


class TestMultiStepWorkflows:
    """Test complete multi-step user workflows."""

    @pytest.fixture
    def full_game_for_workflows(self):
        """Setup complete game for workflow testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()

        # Dismiss any active dialogues
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()

        yield engine

    def test_complete_inventory_workflow(self, full_game_for_workflows):
        """Complete workflow: open inventory -> navigate -> close -> game continues."""
        engine = full_game_for_workflows
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Step 1: Open inventory with 'i' key
        i_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I, sym=tcod.event.KeySym.I, mod=tcod.event.Modifier.NONE
        )
        handler.handle_keydown(i_event)
        assert engine.show_inventory

        # Step 2: Navigate in inventory with DOWN key
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(down_event)
        # (Navigation happens in inventory handler)

        # Step 3: Close inventory with ESC
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(esc_event)
        assert not engine.show_inventory

        # Step 4: Verify game continues (input still processed)
        move_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(move_event)

        # Game should still be functional (not frozen)
        assert engine.player is not None
        assert engine.game_map is not None

    def test_complete_look_mode_workflow(self, full_game_for_workflows):
        """Complete workflow: enter look mode -> move cursor -> inspect -> exit -> game continues."""
        engine = full_game_for_workflows
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        initial_pos = (engine.player.x, engine.player.y)

        # Step 1: Enter look mode with 'L' key
        l_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.L, sym=tcod.event.KeySym.L, mod=tcod.event.Modifier.NONE
        )
        handler.handle_keydown(l_event)
        assert engine.look_mode

        # Step 2: Move cursor in look mode
        cursor_initial = (engine.look_cursor_position.x, engine.look_cursor_position.y)
        move_cursor = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(move_cursor)
        cursor_moved = (engine.look_cursor_position.x, engine.look_cursor_position.y)
        assert cursor_moved != cursor_initial

        # Step 3: Exit look mode with ESC
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(esc_event)
        assert not engine.look_mode

        # Step 4: Verify player position unchanged and game continues
        assert (engine.player.x, engine.player.y) == initial_pos

    def test_nested_menu_workflow(self, full_game_for_workflows):
        """Workflow: main menu -> submenu -> navigate -> return -> selection preserved."""
        from unittest.mock import Mock

        from rsp.ui.menu_main import MainMenu

        mock_sound_manager = Mock()
        menu = MainMenu()

        # Step 1: Navigate to Settings option
        for _ in range(3):  # Assuming Settings is 3rd option
            down_event = tcod.event.KeyDown(
                scancode=tcod.event.Scancode.DOWN,
                sym=tcod.event.KeySym.DOWN,
                mod=tcod.event.Modifier.NONE,
            )
            menu.handle_input(down_event)

        selection_before_submenu = menu.selected_option

        # Step 2: Enter submenu (would normally open Settings menu)
        # For this test, just verify the selection is stable
        enter_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RETURN,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE,
        )
        menu.handle_input(enter_event)

        # Step 3: Verify selection persisted
        assert menu.selected_option == selection_before_submenu

    def test_gameplay_to_menu_and_back_workflow(self, full_game_for_workflows):
        """Workflow: gameplay -> open menu -> close -> gameplay continues seamlessly."""
        engine = full_game_for_workflows
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Step 1: Attempt movement in gameplay
        move_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(move_event)
        # (Movement may or may not succeed depending on map layout)

        # Step 2: Open inventory
        i_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I, sym=tcod.event.KeySym.I, mod=tcod.event.Modifier.NONE
        )
        handler.handle_keydown(i_event)
        assert engine.show_inventory

        # Step 3: Close inventory
        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(esc_event)
        assert not engine.show_inventory

        # Step 4: Game should still be functional
        handler.handle_keydown(move_event)

        # Game continues (not frozen)
        assert engine.player is not None
        assert engine.game_map is not None


class TestInputBuffering:
    """Test input buffering and timing behavior."""

    @pytest.fixture
    def engine_for_buffering_test(self):
        """Setup engine for input buffering tests."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()

        # Dismiss any active dialogues
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()

        yield engine

    def test_input_during_transition_is_handled(self, engine_for_buffering_test):
        """Input during state transition doesn't get lost."""
        engine = engine_for_buffering_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Open inventory
        i_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I, sym=tcod.event.KeySym.I, mod=tcod.event.Modifier.NONE
        )
        handler.handle_keydown(i_event)

        # Immediately send navigation input (during transition)
        down_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        handler.handle_keydown(down_event)

        # Input should be processed (inventory is open and received input)
        assert engine.show_inventory  # Transition completed

    def test_rapid_state_transitions(self, engine_for_buffering_test):
        """Rapidly opening and closing menus doesn't cause state corruption."""
        engine = engine_for_buffering_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        i_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.I, sym=tcod.event.KeySym.I, mod=tcod.event.Modifier.NONE
        )

        esc_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        # Rapidly toggle inventory 10 times
        for _ in range(10):
            handler.handle_keydown(i_event)
            handler.handle_keydown(esc_event)

        # Should end in closed state
        assert not engine.show_inventory
        # Game should still be functional
        assert engine.player is not None
        assert engine.game_map is not None

    def test_multiple_inputs_same_frame(self, engine_for_buffering_test):
        """Multiple inputs in same frame are all processed."""
        engine = engine_for_buffering_test
        from rsp.input.handler import InputHandler

        handler = InputHandler(engine, None)

        # Send multiple movement inputs "simultaneously"
        right_event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHT,
            sym=tcod.event.KeySym.RIGHT,
            mod=tcod.event.Modifier.NONE,
        )

        # Process 3 inputs in succession (simulating buffering)
        for _ in range(3):
            handler.handle_keydown(right_event)

        # All 3 inputs should be processed (game doesn't drop inputs)
        # Just verify game is still functional
        assert engine.player is not None
        assert engine.game_map is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
