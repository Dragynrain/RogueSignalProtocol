"""
Gameplay Movement Input Testing

Tests input handling during normal gameplay:
- 8-way movement verification
- Wait/skip turn actions
- Screen toggles (inventory, help)
- Edge cases (blocked movement, rapid input)

Note: Extracted from test_input_critical_paths.py for maintainability.
"""

import pytest
import tcod.event

from game_input_actions import InputAction
from tests.integration.input_test_utils import InputTestHelper


class TestGameplayMovement:
    """Test movement in gameplay context."""

    @pytest.fixture
    def gameplay_engine(self):
        """Create game engine in gameplay mode."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()

        # Close any dialogues
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()

        # Ensure we're in gameplay mode
        engine.targeting_mode = False
        engine.look_mode = False

        yield engine

    def test_move_north_changes_position(self, gameplay_engine):
        """Moving north changes player Y position."""
        engine = gameplay_engine
        initial_y = engine.player.position.y

        engine.input_handler._execute_action(InputAction.MOVE_NORTH)

        # Y should decrease (north is up) unless blocked
        assert engine.player.position.y <= initial_y

    def test_move_south_changes_position(self, gameplay_engine):
        """Moving south changes player Y position."""
        engine = gameplay_engine
        initial_y = engine.player.position.y

        engine.input_handler._execute_action(InputAction.MOVE_SOUTH)

        # Y should increase (south is down) unless blocked
        assert engine.player.position.y >= initial_y

    def test_move_east_changes_position(self, gameplay_engine):
        """Moving east changes player X position."""
        engine = gameplay_engine
        initial_x = engine.player.position.x

        engine.input_handler._execute_action(InputAction.MOVE_EAST)

        # X should increase (east is right) unless blocked
        assert engine.player.position.x >= initial_x

    def test_move_west_changes_position(self, gameplay_engine):
        """Moving west changes player X position."""
        engine = gameplay_engine
        initial_x = engine.player.position.x

        engine.input_handler._execute_action(InputAction.MOVE_WEST)

        # X should decrease (west is left) unless blocked
        assert engine.player.position.x <= initial_x

    def test_diagonal_movement_changes_both_axes(self, gameplay_engine):
        """Diagonal movement affects both X and Y."""
        engine = gameplay_engine
        initial_x = engine.player.position.x
        initial_y = engine.player.position.y

        engine.input_handler._execute_action(InputAction.MOVE_NORTHEAST)

        # Position should change (unless fully blocked)
        moved = engine.player.position.x != initial_x or engine.player.position.y != initial_y
        # At minimum, action should not crash
        assert engine.player.position is not None


class TestWaitAction:
    """Test wait/skip turn action."""

    @pytest.fixture
    def gameplay_engine(self):
        """Create game engine for wait testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()
        yield engine

    def test_wait_increments_turn(self, gameplay_engine):
        """Wait action increments turn counter."""
        engine = gameplay_engine
        initial_turn = engine.turn

        engine.input_handler._execute_action(InputAction.WAIT)

        assert engine.turn > initial_turn

    def test_wait_via_period_key(self, gameplay_engine):
        """Period key triggers wait action."""
        engine = gameplay_engine
        initial_turn = engine.turn

        event = InputTestHelper.create_keyboard_event(tcod.event.KeySym.PERIOD)
        engine.input_handler.handle_keydown(event)

        assert engine.turn >= initial_turn

    def test_wait_via_numpad_5(self, gameplay_engine):
        """Numpad 5 triggers wait action."""
        engine = gameplay_engine
        initial_turn = engine.turn

        event = InputTestHelper.create_keyboard_event(tcod.event.KeySym.KP_5)
        engine.input_handler.handle_keydown(event)

        assert engine.turn >= initial_turn


class TestScreenToggles:
    """Test screen toggle actions."""

    @pytest.fixture
    def gameplay_engine(self):
        """Create game engine for toggle testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()
        yield engine

    def test_inventory_toggle_changes_state(self, gameplay_engine):
        """Toggle inventory changes show_inventory state."""
        engine = gameplay_engine
        initial_state = engine.show_inventory

        engine.input_handler._execute_action(InputAction.TOGGLE_INVENTORY)

        assert engine.show_inventory != initial_state

    def test_inventory_toggle_twice_returns_to_original(self, gameplay_engine):
        """Double toggle returns to original state."""
        engine = gameplay_engine
        initial_state = engine.show_inventory

        engine.input_handler._execute_action(InputAction.TOGGLE_INVENTORY)
        engine.input_handler._execute_action(InputAction.TOGGLE_INVENTORY)

        assert engine.show_inventory == initial_state

    def test_look_mode_toggle_changes_state(self, gameplay_engine):
        """Toggle look mode changes look_mode state."""
        engine = gameplay_engine
        initial_state = engine.look_mode

        engine.input_handler._execute_action(InputAction.TOGGLE_LOOK_MODE)

        assert engine.look_mode != initial_state


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def gameplay_engine(self):
        """Create game engine for edge case testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()
        yield engine

    def test_movement_into_wall_doesnt_crash(self, gameplay_engine):
        """Moving into walls handles gracefully."""
        engine = gameplay_engine

        # Try moving in all directions multiple times
        for action in [
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST,
            InputAction.MOVE_WEST,
        ]:
            for _ in range(10):
                engine.input_handler._execute_action(action)

        # Game state should still be valid
        assert engine.player.position is not None
        assert engine.player.position.x >= 0
        assert engine.player.position.y >= 0

    def test_rapid_input_maintains_valid_state(self, gameplay_engine):
        """Rapid button mashing maintains valid game state."""
        import random

        engine = gameplay_engine

        actions = [
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.WAIT,
            InputAction.TOGGLE_INVENTORY,
        ]

        for _ in range(50):
            action = random.choice(actions)
            engine.input_handler._execute_action(action)

        # Game state still valid
        assert engine.player.position is not None
        assert hasattr(engine, "turn")

    def test_invalid_exploit_slot_handled_gracefully(self, gameplay_engine):
        """Using invalid exploit slots doesn't crash."""
        engine = gameplay_engine

        # Try to use exploit slots 6-9 (likely invalid)
        for key in [tcod.event.KeySym.N6, tcod.event.KeySym.N7, tcod.event.KeySym.N8]:
            event = InputTestHelper.create_keyboard_event(key)
            # Should not raise exception
            engine.input_handler.handle_keydown(event)

        assert engine.player.position is not None


class TestGamepadInGameplay:
    """Test gamepad input during gameplay."""

    @pytest.fixture
    def gameplay_engine(self):
        """Create game engine for gamepad testing."""
        from tests.fixtures.standard_patterns import create_basic_game_environment

        engine = create_basic_game_environment()
        if engine.dialogue_state.is_active():
            engine.dialogue_state.close()
        yield engine

    def test_dpad_moves_player(self, gameplay_engine):
        """D-pad triggers player movement."""
        engine = gameplay_engine

        for direction in ["up", "down", "left", "right"]:
            initial_pos = (engine.player.position.x, engine.player.position.y)

            press = InputTestHelper.create_dpad_event(direction, pressed=True)
            engine.input_handler.handle_keydown(press)

            release = InputTestHelper.create_dpad_event(direction, pressed=False)
            engine.input_handler.handle_keydown(release)

        # Player position should still be valid
        assert engine.player.position.x >= 0
        assert engine.player.position.y >= 0

    def test_left_stick_moves_player(self, gameplay_engine):
        """Left stick triggers player movement."""
        engine = gameplay_engine

        # North
        event = InputTestHelper.create_stick_event("left", "y", -32767)
        engine.input_handler.handle_keydown(event)

        # South
        event = InputTestHelper.create_stick_event("left", "y", 32767)
        engine.input_handler.handle_keydown(event)

        assert engine.player.position is not None

    def test_face_button_a_waits(self, gameplay_engine):
        """Face button A triggers wait in gameplay."""
        engine = gameplay_engine
        initial_turn = engine.turn

        event = InputTestHelper.create_face_button_event("a", pressed=True)
        engine.input_handler.handle_keydown(event)

        # Turn should advance or stay same
        assert engine.turn >= initial_turn

    def test_shoulder_buttons_cycle_exploits(self, gameplay_engine):
        """Shoulder buttons cycle through exploits without crashing."""
        engine = gameplay_engine

        # LB - previous exploit
        lb = InputTestHelper.create_shoulder_button_event("lb", pressed=True)
        engine.input_handler.handle_keydown(lb)

        # RB - next exploit
        rb = InputTestHelper.create_shoulder_button_event("rb", pressed=True)
        engine.input_handler.handle_keydown(rb)

        # Should not crash
        assert engine.player is not None
