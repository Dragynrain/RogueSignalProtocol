"""
Tests for input abstraction layer (Phase 1: Gamepad Support).

Tests InputAction/InputContext enums, InputMapper, and AnalogStickHandler.
"""

import tcod.event

from game_input_actions import InputAction, InputContext
from game_input_analog import AnalogStickHandler
from game_input_mappings import InputMapper


class TestInputActions:
    """Test InputAction and InputContext enums."""

    def test_input_action_enum_exists(self):
        """Test that InputAction enum has expected values."""
        # Movement
        assert InputAction.MOVE_NORTH
        assert InputAction.MOVE_SOUTH
        assert InputAction.MOVE_EAST
        assert InputAction.MOVE_WEST
        assert InputAction.MOVE_NORTHEAST
        assert InputAction.MOVE_NORTHWEST
        assert InputAction.MOVE_SOUTHEAST
        assert InputAction.MOVE_SOUTHWEST

        # Core actions
        assert InputAction.WAIT
        assert InputAction.CONFIRM
        assert InputAction.CANCEL

        # Exploits
        assert InputAction.EXPLOIT_SLOT_1
        assert InputAction.EXPLOIT_SLOT_2
        assert InputAction.EXPLOIT_SLOT_3
        assert InputAction.EXPLOIT_SLOT_4
        assert InputAction.EXPLOIT_SLOT_5

        # NEW: Gamepad exploit cycling
        assert InputAction.EXPLOIT_CYCLE_NEXT
        assert InputAction.EXPLOIT_CYCLE_PREV
        assert InputAction.EXPLOIT_EXECUTE

        # UI toggles
        assert InputAction.TOGGLE_INVENTORY
        assert InputAction.TOGGLE_LOOK_MODE

    def test_input_context_enum_exists(self):
        """Test that InputContext enum has expected values."""
        assert InputContext.GAMEPLAY
        assert InputContext.INVENTORY
        assert InputContext.LOOK_MODE
        assert InputContext.TARGETING
        assert InputContext.DIALOGUE
        assert InputContext.MAIN_MENU
        assert InputContext.SETTINGS_MENU

    def test_action_enum_values_are_unique(self):
        """Test that all InputAction values are unique."""
        values = [action.value for action in InputAction]
        assert len(values) == len(set(values)), "InputAction enum has duplicate values"

    def test_context_enum_values_are_unique(self):
        """Test that all InputContext values are unique."""
        values = [context.value for context in InputContext]
        assert len(values) == len(set(values)), "InputContext enum has duplicate values"


class TestInputMapper:
    """Test InputMapper class."""

    def test_mapper_initializes(self):
        """Test that InputMapper initializes without errors."""
        mapper = InputMapper()
        assert mapper is not None

    def test_default_keyboard_mappings_exist(self):
        """Test that default keyboard mappings are initialized."""
        mapper = InputMapper()

        # Movement keys should map to movement actions
        assert mapper.get_action_for_key(tcod.event.KeySym.W) == InputAction.MOVE_NORTH
        assert mapper.get_action_for_key(tcod.event.KeySym.S) == InputAction.MOVE_SOUTH
        assert mapper.get_action_for_key(tcod.event.KeySym.A) == InputAction.MOVE_WEST
        assert mapper.get_action_for_key(tcod.event.KeySym.D) == InputAction.MOVE_EAST

        # Diagonal movement
        assert mapper.get_action_for_key(tcod.event.KeySym.Q) == InputAction.MOVE_NORTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.E) == InputAction.MOVE_NORTHEAST
        assert mapper.get_action_for_key(tcod.event.KeySym.Z) == InputAction.MOVE_SOUTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.C) == InputAction.MOVE_SOUTHEAST

    def test_arrow_keys_map_to_movement(self):
        """Test that arrow keys map to movement actions."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.UP) == InputAction.MOVE_NORTH
        assert mapper.get_action_for_key(tcod.event.KeySym.DOWN) == InputAction.MOVE_SOUTH
        assert mapper.get_action_for_key(tcod.event.KeySym.LEFT) == InputAction.MOVE_WEST
        assert mapper.get_action_for_key(tcod.event.KeySym.RIGHT) == InputAction.MOVE_EAST

    def test_numpad_keys_map_to_movement(self):
        """Test that numpad keys map to movement actions (8-way)."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.KP_8) == InputAction.MOVE_NORTH
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_2) == InputAction.MOVE_SOUTH
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_4) == InputAction.MOVE_WEST
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_6) == InputAction.MOVE_EAST
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_7) == InputAction.MOVE_NORTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_9) == InputAction.MOVE_NORTHEAST
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_1) == InputAction.MOVE_SOUTHWEST
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_3) == InputAction.MOVE_SOUTHEAST

    def test_wait_keys_map_correctly(self):
        """Test that wait/rest keys map to WAIT action."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.SPACE) == InputAction.WAIT
        assert mapper.get_action_for_key(tcod.event.KeySym.PERIOD) == InputAction.WAIT
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_5) == InputAction.WAIT

    def test_exploit_number_keys_map_correctly(self):
        """Test that number keys 1-5 map to exploit slots."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.N1) == InputAction.EXPLOIT_SLOT_1
        assert mapper.get_action_for_key(tcod.event.KeySym.N2) == InputAction.EXPLOIT_SLOT_2
        assert mapper.get_action_for_key(tcod.event.KeySym.N3) == InputAction.EXPLOIT_SLOT_3
        assert mapper.get_action_for_key(tcod.event.KeySym.N4) == InputAction.EXPLOIT_SLOT_4
        assert mapper.get_action_for_key(tcod.event.KeySym.N5) == InputAction.EXPLOIT_SLOT_5

    def test_ui_toggle_keys_map_correctly(self):
        """Test that UI toggle keys map correctly."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.I) == InputAction.TOGGLE_INVENTORY
        assert mapper.get_action_for_key(tcod.event.KeySym.L) == InputAction.TOGGLE_LOOK_MODE
        assert mapper.get_action_for_key(tcod.event.KeySym.F) == InputAction.TOGGLE_LORE_VIEWER
        assert mapper.get_action_for_key(tcod.event.KeySym.V) == InputAction.TOGGLE_ACHIEVEMENTS

    def test_confirm_cancel_keys(self):
        """Test that confirm/cancel keys map correctly."""
        mapper = InputMapper()

        assert mapper.get_action_for_key(tcod.event.KeySym.RETURN) == InputAction.CONFIRM
        assert mapper.get_action_for_key(tcod.event.KeySym.KP_ENTER) == InputAction.CONFIRM
        assert mapper.get_action_for_key(tcod.event.KeySym.ESCAPE) == InputAction.CANCEL

    def test_unmapped_key_returns_none(self):
        """Test that unmapped keys return None."""
        mapper = InputMapper()

        # Random unmapped key
        assert mapper.get_action_for_key(tcod.event.KeySym.TAB) is None
        assert mapper.get_action_for_key(tcod.event.KeySym.BACKSPACE) is None

    def test_movement_delta_conversion(self):
        """Test that movement actions convert to correct (dx, dy) deltas."""
        mapper = InputMapper()

        assert mapper.get_movement_delta(InputAction.MOVE_NORTH) == (0, -1)
        assert mapper.get_movement_delta(InputAction.MOVE_SOUTH) == (0, 1)
        assert mapper.get_movement_delta(InputAction.MOVE_EAST) == (1, 0)
        assert mapper.get_movement_delta(InputAction.MOVE_WEST) == (-1, 0)
        assert mapper.get_movement_delta(InputAction.MOVE_NORTHEAST) == (1, -1)
        assert mapper.get_movement_delta(InputAction.MOVE_NORTHWEST) == (-1, -1)
        assert mapper.get_movement_delta(InputAction.MOVE_SOUTHEAST) == (1, 1)
        assert mapper.get_movement_delta(InputAction.MOVE_SOUTHWEST) == (-1, 1)

    def test_non_movement_action_returns_none_delta(self):
        """Test that non-movement actions return None for delta."""
        mapper = InputMapper()

        assert mapper.get_movement_delta(InputAction.WAIT) is None
        assert mapper.get_movement_delta(InputAction.EXPLOIT_SLOT_1) is None
        assert mapper.get_movement_delta(InputAction.TOGGLE_INVENTORY) is None

    def test_is_movement_action(self):
        """Test that is_movement_action correctly identifies movement actions."""
        mapper = InputMapper()

        # Movement actions
        assert mapper.is_movement_action(InputAction.MOVE_NORTH) is True
        assert mapper.is_movement_action(InputAction.MOVE_SOUTH) is True
        assert mapper.is_movement_action(InputAction.MOVE_NORTHEAST) is True

        # Non-movement actions
        assert mapper.is_movement_action(InputAction.WAIT) is False
        assert mapper.is_movement_action(InputAction.EXPLOIT_SLOT_1) is False
        assert mapper.is_movement_action(InputAction.TOGGLE_INVENTORY) is False

    def test_get_default_keys_for_action(self):
        """Test that we can retrieve default keys for an action."""
        mapper = InputMapper()

        # Movement north has multiple keys (W, UP, KP_8)
        north_keys = mapper.get_default_keys_for_action(InputAction.MOVE_NORTH)
        assert len(north_keys) == 3
        assert "W" in north_keys
        assert "↑" in north_keys
        assert "Numpad 8" in north_keys

        # Wait has multiple keys
        wait_keys = mapper.get_default_keys_for_action(InputAction.WAIT)
        assert len(wait_keys) == 3
        assert "Space" in wait_keys
        assert "." in wait_keys
        assert "Numpad 5" in wait_keys

    def test_context_parameter_accepted(self):
        """Test that context parameter is accepted (even if not used yet)."""
        mapper = InputMapper()

        # Should work with context specified
        action = mapper.get_action_for_key(tcod.event.KeySym.W, InputContext.GAMEPLAY)
        assert action == InputAction.MOVE_NORTH

        # Should work with different context
        action = mapper.get_action_for_key(tcod.event.KeySym.W, InputContext.INVENTORY)
        assert action == InputAction.MOVE_NORTH  # Not context-sensitive yet


class TestAnalogStickHandler:
    """Test AnalogStickHandler class."""

    def test_handler_initializes(self):
        """Test that AnalogStickHandler initializes with defaults."""
        handler = AnalogStickHandler()
        assert handler is not None
        assert handler.deadzone == 0.15
        assert handler.threshold == 0.2  # Default is 0.2 (20% post-scaling)
        assert handler.last_gameplay_move_time == -1.0  # Time-based gating

    def test_handler_initializes_with_custom_values(self):
        """Test that AnalogStickHandler accepts custom parameters."""
        handler = AnalogStickHandler(deadzone=0.2, threshold=0.6)
        assert handler.deadzone == 0.2
        assert handler.threshold == 0.6
        assert handler.last_gameplay_move_time == -1.0  # Time-based gating initialized

    def test_scaled_radial_deadzone_zero_input(self):
        """Test that zero input returns zero after deadzone."""
        handler = AnalogStickHandler()
        x, y = handler.apply_scaled_radial_deadzone(0, 0)
        assert x == 0.0
        assert y == 0.0

    def test_scaled_radial_deadzone_below_threshold(self):
        """Test that input below deadzone returns zero."""
        handler = AnalogStickHandler(deadzone=0.15)
        # 10% deflection (below 15% deadzone)
        raw_x = int(32768 * 0.1)
        raw_y = 0
        x, y = handler.apply_scaled_radial_deadzone(raw_x, raw_y)
        assert x == 0.0
        assert y == 0.0

    def test_scaled_radial_deadzone_above_threshold(self):
        """Test that input above deadzone returns scaled value."""
        handler = AnalogStickHandler(deadzone=0.15)
        # 50% deflection (above 15% deadzone)
        raw_x = int(32768 * 0.5)
        raw_y = 0
        x, y = handler.apply_scaled_radial_deadzone(raw_x, raw_y)
        assert x > 0.0  # Should have some output
        assert abs(y) < 0.01  # Y should be near zero

    def test_scaled_radial_deadzone_max_deflection(self):
        """Test that maximum deflection returns normalized 1.0."""
        handler = AnalogStickHandler(deadzone=0.15)
        # Full deflection
        raw_x = 32767
        raw_y = 0
        x, y = handler.apply_scaled_radial_deadzone(raw_x, raw_y)
        assert abs(x - 1.0) < 0.01  # Should be close to 1.0
        assert abs(y) < 0.01

    def test_scaled_radial_deadzone_preserves_direction(self):
        """Test that deadzone processing preserves direction."""
        handler = AnalogStickHandler(deadzone=0.15)
        # 45-degree angle (northeast)
        raw_x = int(32768 * 0.5)
        raw_y = int(32768 * 0.5)
        x, y = handler.apply_scaled_radial_deadzone(raw_x, raw_y)

        # Should maintain roughly equal X and Y (45 degrees)
        assert abs(x - y) < 0.1
        assert x > 0.0 and y > 0.0

    def test_axial_deadzone_independent_axes(self):
        """Test that axial deadzone treats X and Y independently."""
        handler = AnalogStickHandler(deadzone=0.15)

        # X below deadzone, Y above
        raw_x = int(32768 * 0.1)  # 10% (below)
        raw_y = int(32768 * 0.5)  # 50% (above)
        x, y = handler.apply_axial_deadzone(raw_x, raw_y)

        assert x == 0.0  # X filtered out
        assert y != 0.0  # Y preserved

    def test_analog_to_8way_center(self):
        """Test that centered stick returns (0, 0)."""
        handler = AnalogStickHandler()
        dx, dy = handler.analog_to_8way(0, 0)
        assert dx == 0
        assert dy == 0

    def test_analog_to_8way_north(self):
        """Test that upward stick returns north."""
        handler = AnalogStickHandler(threshold=0.5)
        # Full up (negative Y in SDL)
        raw_x = 0
        raw_y = -32767
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == 0
        assert dy == -1  # North

    def test_analog_to_8way_south(self):
        """Test that downward stick returns south."""
        handler = AnalogStickHandler(threshold=0.5)
        raw_x = 0
        raw_y = 32767
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == 0
        assert dy == 1  # South

    def test_analog_to_8way_east(self):
        """Test that rightward stick returns east."""
        handler = AnalogStickHandler(threshold=0.5)
        raw_x = 32767
        raw_y = 0
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == 1  # East
        assert dy == 0

    def test_analog_to_8way_west(self):
        """Test that leftward stick returns west."""
        handler = AnalogStickHandler(threshold=0.5)
        raw_x = -32767
        raw_y = 0
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == -1  # West
        assert dy == 0

    def test_analog_to_8way_northeast(self):
        """Test that northeast stick returns (1, -1)."""
        handler = AnalogStickHandler(threshold=0.5)
        # 75% deflection northeast
        raw_x = int(32768 * 0.75)
        raw_y = int(-32768 * 0.75)
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == 1
        assert dy == -1

    def test_analog_to_8way_below_threshold(self):
        """Test that input below threshold returns (0, 0)."""
        handler = AnalogStickHandler(threshold=0.5)
        # 40% deflection (below 50% threshold)
        raw_x = int(32768 * 0.4)
        raw_y = 0
        dx, dy = handler.analog_to_8way(raw_x, raw_y)
        assert dx == 0
        assert dy == 0

    def test_trigger_deadzone_zero(self):
        """Test that zero trigger returns 0.0."""
        handler = AnalogStickHandler()
        value = handler.apply_trigger_deadzone(0)
        assert value == 0.0

    def test_trigger_deadzone_max(self):
        """Test that max trigger returns 1.0."""
        handler = AnalogStickHandler(deadzone=0.1)
        value = handler.apply_trigger_deadzone(32767)
        assert abs(value - 1.0) < 0.01

    def test_trigger_deadzone_below_threshold(self):
        """Test that trigger below deadzone returns 0.0."""
        handler = AnalogStickHandler(deadzone=0.15)
        # 10% press (below 15% deadzone)
        raw_value = int(32767 * 0.1)
        value = handler.apply_trigger_deadzone(raw_value)
        assert value == 0.0

    def test_update_left_stick(self):
        """Test that left stick state updates correctly."""
        handler = AnalogStickHandler()
        handler.update_left_stick(x=1000, y=2000)
        assert handler.left_x == 1000
        assert handler.left_y == 2000

        # Update only Y
        handler.update_left_stick(y=3000)
        assert handler.left_x == 1000  # Unchanged
        assert handler.left_y == 3000

    def test_update_right_stick(self):
        """Test that right stick state updates correctly."""
        handler = AnalogStickHandler()
        handler.update_right_stick(x=500, y=1500)
        assert handler.right_x == 500
        assert handler.right_y == 1500

    def test_get_right_stick_magnitude(self):
        """Test that right stick magnitude calculation works."""
        handler = AnalogStickHandler(deadzone=0.1)
        # Set stick to 50% northeast
        raw_value = int(32768 * 0.5)
        handler.update_right_stick(x=raw_value, y=-raw_value)

        magnitude = handler.get_right_stick_magnitude()
        # Magnitude should be roughly 0.5 (after deadzone scaling)
        assert 0.4 < magnitude < 0.7

    def test_movement_time_gating(self):
        """Test that time-based gating prevents multiple moves per frame."""
        import time

        from game_config import GameConfig

        handler = AnalogStickHandler()
        handler.update_left_stick(x=32767, y=0)  # Deflect stick east

        # First call starts settling period (30ms) - returns None
        movement0 = handler.get_left_stick_movement_gameplay(0)
        assert movement0 is None  # Settling started

        # Simulate settling period by backdating the settling start time
        handler._settling_start_time = time.time() - GameConfig.ANALOG_SETTLING_PERIOD - 0.01

        # After settling, first actual move should succeed
        movement1 = handler.get_left_stick_movement_gameplay(0)
        assert movement1 is not None

        # Immediate second move should fail (time gating active)
        movement2 = handler.get_left_stick_movement_gameplay(0)
        assert movement2 is None

        # Simulate initial delay by backdating last move time
        handler.last_gameplay_move_time = (
            time.time() - GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY - 0.05
        )
        movement3 = handler.get_left_stick_movement_gameplay(0)
        assert movement3 is not None

    def test_reset_movement_time_gating(self):
        """Test that time-based gating resets on release."""
        import time

        from game_config import GameConfig

        handler = AnalogStickHandler()

        # Deflect stick - first call starts settling period
        handler.update_left_stick(x=32767, y=0)
        movement0 = handler.get_left_stick_movement_gameplay(0)
        assert movement0 is None  # Settling started

        # Simulate settling period by backdating start time
        handler._settling_start_time = time.time() - GameConfig.ANALOG_SETTLING_PERIOD - 0.01
        movement1 = handler.get_left_stick_movement_gameplay(0)
        assert movement1 is not None

        # Immediate second should be blocked (time gating active)
        movement2 = handler.get_left_stick_movement_gameplay(0)
        assert movement2 is None

        # Release stick - resets timing
        handler.update_left_stick(x=0, y=0)
        handler.get_left_stick_movement_gameplay(0)

        # Re-deflect - starts new settling period
        handler.update_left_stick(x=32767, y=0)
        movement3_settle = handler.get_left_stick_movement_gameplay(0)
        assert movement3_settle is None  # New settling period

        # Simulate settling period by backdating start time
        handler._settling_start_time = time.time() - GameConfig.ANALOG_SETTLING_PERIOD - 0.01
        movement3 = handler.get_left_stick_movement_gameplay(0)
        assert movement3 is not None


class TestInputMapperConflicts:
    """Test conflict detection in InputMapper."""

    def test_get_conflicts_detects_existing_binding(self):
        """Test that get_conflicts finds existing bindings."""
        mapper = InputMapper()

        # W is already bound to MOVE_NORTH
        conflicts = mapper.get_conflicts(InputAction.WAIT, tcod.event.KeySym.W)
        assert InputAction.MOVE_NORTH in conflicts

    def test_get_conflicts_allows_same_action(self):
        """Test that rebinding same action to same key is not a conflict."""
        mapper = InputMapper()

        # Binding MOVE_NORTH to W (already bound) should not conflict with itself
        conflicts = mapper.get_conflicts(InputAction.MOVE_NORTH, tcod.event.KeySym.W)
        assert InputAction.MOVE_NORTH not in conflicts

    def test_get_conflicts_empty_for_unbound_key(self):
        """Test that unbound keys have no conflicts."""
        mapper = InputMapper()

        # Tab is not bound to anything
        conflicts = mapper.get_conflicts(InputAction.WAIT, tcod.event.KeySym.TAB)
        assert len(conflicts) == 0


class TestInputMapperDisplay:
    """Test display name conversion in InputMapper."""

    def test_key_sym_to_display_name_letters(self):
        """Test that letter keys display as uppercase."""
        mapper = InputMapper()

        assert mapper._key_sym_to_display_name(tcod.event.KeySym.W) == "W"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.A) == "A"

    def test_key_sym_to_display_name_arrows(self):
        """Test that arrow keys display as Unicode arrows."""
        mapper = InputMapper()

        assert mapper._key_sym_to_display_name(tcod.event.KeySym.UP) == "↑"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.DOWN) == "↓"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.LEFT) == "←"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.RIGHT) == "→"

    def test_key_sym_to_display_name_special_keys(self):
        """Test that special keys display with readable names."""
        mapper = InputMapper()

        assert mapper._key_sym_to_display_name(tcod.event.KeySym.SPACE) == "Space"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.RETURN) == "Enter"
        assert mapper._key_sym_to_display_name(tcod.event.KeySym.ESCAPE) == "ESC"


class TestModifierKeySupport:
    """Tests for keyboard modifier key (Shift, Ctrl, Alt) support."""

    def test_shift_slash_maps_to_help(self):
        """Test that Shift+/ (?) maps to TOGGLE_HELP by default."""
        mapper = InputMapper()

        # Without modifier - slash alone should NOT trigger help
        action_no_mod = mapper.get_action_for_key(tcod.event.KeySym.SLASH, modifier=0)
        assert action_no_mod != InputAction.TOGGLE_HELP

        # With Shift modifier - should trigger help
        action_with_shift = mapper.get_action_for_key(
            tcod.event.KeySym.SLASH, modifier=tcod.event.Modifier.SHIFT
        )
        assert action_with_shift == InputAction.TOGGLE_HELP

    def test_modifier_binding_requires_correct_modifier(self):
        """Test that modifier bindings only match when modifier is pressed."""
        mapper = InputMapper()

        # Ctrl alone should not match Shift+/ binding
        action_ctrl = mapper.get_action_for_key(
            tcod.event.KeySym.SLASH, modifier=tcod.event.Modifier.CTRL
        )
        assert action_ctrl != InputAction.TOGGLE_HELP

        # Alt alone should not match Shift+/ binding
        action_alt = mapper.get_action_for_key(
            tcod.event.KeySym.SLASH, modifier=tcod.event.Modifier.ALT
        )
        assert action_alt != InputAction.TOGGLE_HELP

    def test_key_binding_display_name_with_modifier(self):
        """Test that KeyBinding display names show symbols for Shift combos."""
        from game_input_mappings import KeyBinding, key_binding_to_display_name

        # Without modifier
        binding_no_mod = KeyBinding(tcod.event.KeySym.SLASH, 0)
        assert key_binding_to_display_name(binding_no_mod) == "/"

        # Shift+/ shows as "?" (the resulting character)
        binding_shift = KeyBinding(tcod.event.KeySym.SLASH, tcod.event.Modifier.SHIFT)
        assert key_binding_to_display_name(binding_shift) == "?"

        # Shift+. shows as ">"
        binding_gt = KeyBinding(tcod.event.KeySym.PERIOD, tcod.event.Modifier.SHIFT)
        assert key_binding_to_display_name(binding_gt) == ">"

        # Ctrl still shows as "Ctrl+key"
        binding_ctrl = KeyBinding(tcod.event.KeySym.S, tcod.event.Modifier.CTRL)
        assert key_binding_to_display_name(binding_ctrl) == "Ctrl+S"

    def test_key_binding_matches_normalized_modifiers(self):
        """Test that left/right modifier keys are treated equivalently."""
        from game_input_mappings import KeyBinding

        binding = KeyBinding(tcod.event.KeySym.SLASH, tcod.event.Modifier.SHIFT)

        # Left Shift should match
        assert binding.matches(tcod.event.KeySym.SLASH, tcod.event.Modifier.LSHIFT)

        # Right Shift should match
        assert binding.matches(tcod.event.KeySym.SLASH, tcod.event.Modifier.RSHIFT)

        # Generic Shift should match
        assert binding.matches(tcod.event.KeySym.SLASH, tcod.event.Modifier.SHIFT)

    def test_binding_without_modifier_rejects_modified_key(self):
        """Test that non-modifier binding doesn't match when modifier is pressed."""
        mapper = InputMapper()

        # W key without modifier should trigger movement
        action_w_alone = mapper.get_action_for_key(tcod.event.KeySym.W, modifier=0)
        assert action_w_alone == InputAction.MOVE_NORTH

        # W key WITH Shift should NOT trigger movement (binding requires no modifier)
        action_w_shift = mapper.get_action_for_key(
            tcod.event.KeySym.W, modifier=tcod.event.Modifier.SHIFT
        )
        assert action_w_shift is None

    def test_custom_modifier_binding_can_be_added(self):
        """Test that custom modifier bindings can be added and used."""
        mapper = InputMapper()

        # Add Ctrl+S as a custom binding for WAIT
        mapper.add_keyboard_binding(
            InputAction.WAIT, tcod.event.KeySym.S, modifier=tcod.event.Modifier.CTRL
        )

        # Ctrl+S should trigger WAIT
        action = mapper.get_action_for_key(tcod.event.KeySym.S, modifier=tcod.event.Modifier.CTRL)
        assert action == InputAction.WAIT

        # S alone should still be MOVE_SOUTH (default binding)
        action_plain = mapper.get_action_for_key(tcod.event.KeySym.S, modifier=0)
        assert action_plain == InputAction.MOVE_SOUTH

    def test_get_all_keys_shows_symbol_for_shifted_key(self):
        """Test that get_all_keys_for_action shows '?' for Shift+/."""
        mapper = InputMapper()

        keys = mapper.get_all_keys_for_action(InputAction.TOGGLE_HELP)
        # Should include "?" for the help key (not "Shift+/")
        assert "?" in keys
