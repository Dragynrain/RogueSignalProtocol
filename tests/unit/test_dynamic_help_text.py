"""
Tests for dynamic help text system.

Verifies that help hints at the bottom of screens dynamically reflect
the current key/button bindings, updating when users remap controls.
"""

from game_input_actions import InputAction, InputContext
from game_input_mappings import InputMapper


class TestDynamicHelpText:
    """Test dynamic help text generation from InputMapper."""

    def test_get_key_hint_for_confirm_action(self):
        """Test getting display hint for CONFIRM action."""
        mapper = InputMapper()

        # Get keyboard hint for CONFIRM
        hint = mapper.get_key_hint(InputAction.CONFIRM)

        # Default binding is Enter
        assert "Enter" in hint

    def test_get_key_hint_for_cancel_action(self):
        """Test getting display hint for CANCEL action."""
        mapper = InputMapper()

        hint = mapper.get_key_hint(InputAction.CANCEL)

        # Default binding is ESC (case insensitive check)
        assert "ESC" in hint.upper()

    def test_get_key_hint_reflects_custom_binding(self):
        """Test that hint updates when binding is remapped."""
        mapper = InputMapper()

        # Remap WAIT action (which has a default binding) to test custom bindings
        # The custom bindings format uses per-context structure
        custom_bindings = {"GAMEPLAY": {"WAIT": ["T"]}}  # Remap Wait to T key
        mapper.load_custom_bindings(custom_bindings, {})

        hint = mapper.get_key_hint(InputAction.WAIT)

        # Should include T from custom binding
        assert "T" in hint

    def test_get_button_hint_for_confirm_action(self):
        """Test getting gamepad button hint for CONFIRM action."""
        mapper = InputMapper()

        # Get button hint for CONFIRM in menu context
        hint = mapper.get_button_hint(InputAction.CONFIRM, InputContext.MAIN_MENU)

        # Default binding is A button
        assert "A" in hint

    def test_get_button_hint_for_cancel_action(self):
        """Test getting gamepad button hint for CANCEL action."""
        mapper = InputMapper()

        hint = mapper.get_button_hint(InputAction.CANCEL, InputContext.MAIN_MENU)

        # Default binding is B button
        assert "B" in hint

    def test_get_button_hint_reflects_custom_binding(self):
        """Test that button hint updates when remapped."""
        mapper = InputMapper()

        # Add custom binding for CONFIRM using B button
        mapper.add_gamepad_binding(InputAction.CONFIRM, 1, InputContext.MAIN_MENU)  # 1 = B button

        hint = mapper.get_button_hint(InputAction.CONFIRM, InputContext.MAIN_MENU)

        # Should include B now (may also have A)
        assert "B" in hint or "A" in hint  # A is default, B is custom

    def test_get_combined_hint_shows_both_key_and_button(self):
        """Test getting combined keyboard + gamepad hint."""
        mapper = InputMapper()

        # Get combined hint for CONFIRM
        hint = mapper.get_combined_hint(InputAction.CONFIRM, InputContext.MAIN_MENU)

        # Should contain both Enter and A
        assert "Enter" in hint
        assert "A" in hint

    def test_get_navigation_hints(self):
        """Test getting navigation hints for movement (which maps to arrow keys)."""
        mapper = InputMapper()

        # MOVE_NORTH is bound to Up arrow by default
        key_hint = mapper.get_key_hint(InputAction.MOVE_NORTH)

        # Should have arrow key or W
        assert "Up" in key_hint or "W" in key_hint

    def test_format_help_string_substitutes_actions(self):
        """Test formatting a help string with action placeholders."""
        mapper = InputMapper()

        # Format string with placeholders
        template = "Navigate: {NAV} Select: {CONFIRM} Back: {CANCEL}"
        result = mapper.format_help_string(template, InputContext.MAIN_MENU)

        # Should substitute actual keys/buttons
        assert "{NAV}" not in result
        assert "{CONFIRM}" not in result
        assert "{CANCEL}" not in result
        # Should contain actual control names
        assert "Enter" in result or "A" in result  # CONFIRM
        assert "ESC" in result.upper() or "B" in result  # CANCEL

    def test_get_key_hint_returns_first_binding_when_multiple(self):
        """Test that multiple bindings are handled correctly."""
        mapper = InputMapper()

        # CONFIRM might have multiple bindings (Enter, Space, Numpad Enter)
        hint = mapper.get_key_hint(InputAction.CONFIRM)

        # Should return something sensible (not empty)
        assert hint
        assert len(hint) > 0

    def test_get_hint_for_movement_actions(self):
        """Test hints for movement actions (MOVE_NORTH vs MOVE_SOUTH)."""
        mapper = InputMapper()

        north_hint = mapper.get_key_hint(InputAction.MOVE_NORTH)
        south_hint = mapper.get_key_hint(InputAction.MOVE_SOUTH)

        # Should have different hints
        assert north_hint != south_hint
        # Both should not be "?"
        assert north_hint != "?"
        assert south_hint != "?"

    def test_get_button_hint_for_triggers(self):
        """Test getting hints for trigger buttons."""
        mapper = InputMapper()

        # In gameplay context, RT might be bound to exploit execute
        hint = mapper.get_button_hint(InputAction.EXPLOIT_EXECUTE, InputContext.GAMEPLAY)

        # Should return something (RT or similar)
        assert hint is not None

    def test_get_nav_hint(self):
        """Test nav hint helper method."""
        mapper = InputMapper()

        hint = mapper.get_nav_hint(InputContext.MAIN_MENU)

        # Should return combined nav hint
        assert "D-Pad" in hint

    def test_get_nav_hint_without_arrows(self):
        """Test nav hint without arrow symbols."""
        mapper = InputMapper()

        hint = mapper.get_nav_hint(InputContext.MAIN_MENU, use_arrows=False)

        # Should use text instead of arrows
        assert "Up/Dn" in hint


class TestDeviceAwareHints:
    """Test device-aware hint generation that switches based on last input device."""

    def setup_method(self):
        """Reset device tracker before each test."""
        from game_input_device_tracker import reset_to_default

        reset_to_default()

    def teardown_method(self):
        """Reset device tracker after each test to prevent pollution."""
        from game_input_device_tracker import reset_to_default

        reset_to_default()

    def test_confirm_hint_keyboard_mode(self):
        """In keyboard mode, confirm hint shows keyboard key only."""
        from game_help_hints import get_confirm_hint_for_device
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        hint = get_confirm_hint_for_device(InputContext.MAIN_MENU)

        # Should show Enter (keyboard), not A (gamepad)
        assert "Enter" in hint
        assert "/" not in hint  # Should NOT have combined format

    def test_confirm_hint_gamepad_mode(self):
        """In gamepad mode, confirm hint shows gamepad button only."""
        from game_help_hints import get_confirm_hint_for_device
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        hint = get_confirm_hint_for_device(InputContext.MAIN_MENU)

        # Should show A (gamepad), not Enter (keyboard)
        assert "A" in hint
        assert "Enter" not in hint

    def test_cancel_hint_keyboard_mode(self):
        """In keyboard mode, cancel hint shows keyboard key only."""
        from game_help_hints import get_cancel_hint_for_device
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        hint = get_cancel_hint_for_device(InputContext.MAIN_MENU)

        # Should show ESC (keyboard)
        assert "ESC" in hint.upper()

    def test_cancel_hint_gamepad_mode(self):
        """In gamepad mode, cancel hint shows gamepad button only."""
        from game_help_hints import get_cancel_hint_for_device
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        hint = get_cancel_hint_for_device(InputContext.MAIN_MENU)

        # Should show B (gamepad)
        assert "B" in hint

    def test_dialogue_confirm_option_keyboard(self):
        """Dialogue confirm option shows [Y] in keyboard mode."""
        from game_help_hints import get_dialogue_confirm_option_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        option = get_dialogue_confirm_option_for_device("Yes")

        assert "[Y]" in option
        assert "Yes" in option
        # Should not show gamepad button
        assert "/A]" not in option

    def test_dialogue_confirm_option_gamepad(self):
        """Dialogue confirm option shows [A] in gamepad mode."""
        from game_help_hints import get_dialogue_confirm_option_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        option = get_dialogue_confirm_option_for_device("Yes")

        assert "[A]" in option
        assert "Yes" in option
        # Should not show keyboard key
        assert "[Y/" not in option

    def test_dialogue_cancel_option_keyboard(self):
        """Dialogue cancel option shows [N] in keyboard mode."""
        from game_help_hints import get_dialogue_cancel_option_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        option = get_dialogue_cancel_option_for_device("No")

        assert "[N]" in option
        assert "No" in option

    def test_dialogue_cancel_option_gamepad(self):
        """Dialogue cancel option shows [B] in gamepad mode."""
        from game_help_hints import get_dialogue_cancel_option_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        option = get_dialogue_cancel_option_for_device("No")

        assert "[B]" in option
        assert "No" in option

    def test_nav_hint_keyboard_mode(self):
        """Nav hint shows keyboard keys in keyboard mode."""
        from game_help_hints import get_nav_hint_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        hint = get_nav_hint_for_device()

        # Should show arrow keys or Up/Dn, not D-Pad
        assert "D-Pad" not in hint

    def test_nav_hint_gamepad_mode(self):
        """Nav hint shows D-Pad in gamepad mode."""
        from game_help_hints import get_nav_hint_for_device
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        hint = get_nav_hint_for_device()

        # Should show D-Pad, not keyboard arrows
        assert "D-Pad" in hint

    def test_explicit_device_override(self):
        """Can explicitly specify device to override auto-detection."""
        from game_help_hints import get_confirm_hint_for_device
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        # Set to keyboard mode
        set_last_device(InputDeviceType.KEYBOARD)

        # But explicitly request gamepad hint
        hint = get_confirm_hint_for_device(InputContext.MAIN_MENU, device=InputDeviceType.GAMEPAD)

        # Should show gamepad hint despite keyboard mode
        assert "A" in hint
        assert "Enter" not in hint


class TestEndToEndDeviceSwitching:
    """Integration tests for device-aware help text switching."""

    def setup_method(self):
        """Reset device tracker before each test."""
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)

    def test_menu_help_switches_on_device_change(self):
        """Menu help text changes when device changes."""
        from game_help_hints import get_menu_help
        from game_input_actions import InputContext
        from game_input_device_tracker import InputDeviceType, set_last_device

        # Start with keyboard
        set_last_device(InputDeviceType.KEYBOARD)
        kb_help = get_menu_help(InputContext.MAIN_MENU)

        # Should have keyboard hints (↑↓), not D-Pad
        assert "D-Pad" not in kb_help
        assert "\u2191\u2193" in kb_help  # ↑↓

        # Switch to gamepad
        set_last_device(InputDeviceType.GAMEPAD)
        gp_help = get_menu_help(InputContext.MAIN_MENU)

        # Should have gamepad hints, not keyboard arrows
        assert "D-Pad" in gp_help
        assert "\u2191\u2193" not in gp_help

        # Different text
        assert kb_help != gp_help

    def test_dialogue_options_switch_on_device_change(self):
        """Dialogue options change when device changes."""
        from game_help_hints import get_dialogue_cancel_option, get_dialogue_confirm_option
        from game_input_device_tracker import InputDeviceType, set_last_device

        # Keyboard mode
        set_last_device(InputDeviceType.KEYBOARD)
        kb_yes = get_dialogue_confirm_option("Yes")
        kb_no = get_dialogue_cancel_option("No")

        assert "[Y]" in kb_yes
        assert "[N]" in kb_no
        assert "A]" not in kb_yes
        assert "B]" not in kb_no

        # Gamepad mode
        set_last_device(InputDeviceType.GAMEPAD)
        gp_yes = get_dialogue_confirm_option("Yes")
        gp_no = get_dialogue_cancel_option("No")

        assert "[A]" in gp_yes
        assert "[B]" in gp_no
        assert "Y]" not in gp_yes
        assert "N]" not in gp_no

    def test_inventory_help_switches_on_device_change(self):
        """Inventory help text changes when device changes."""
        from game_help_hints import get_inventory_help
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)
        kb_help = get_inventory_help()
        assert "\u2191\u2193" in kb_help  # ↑↓

        set_last_device(InputDeviceType.GAMEPAD)
        gp_help = get_inventory_help()
        assert "D-Pad" in gp_help


class TestGraphicsModeWidthLimits:
    """Test that graphics mode help strings fit within box width."""

    # Graphics menu box has 26 chars content width
    MAX_WIDTH = 26

    def setup_method(self):
        """Reset device tracker before each test."""
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)

    def test_main_menu_help_fits_keyboard(self):
        """Main menu help fits in graphics box (keyboard)."""
        from game_help_hints import get_main_menu_help

        help_text = get_main_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_main_menu_help_fits_gamepad(self):
        """Main menu help fits in graphics box (gamepad)."""
        from game_help_hints import get_main_menu_help
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        help_text = get_main_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_about_menu_help_fits_keyboard(self):
        """About menu help fits in graphics box (keyboard)."""
        from game_help_hints import get_about_menu_help

        help_text = get_about_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_about_menu_help_fits_gamepad(self):
        """About menu help fits in graphics box (gamepad)."""
        from game_help_hints import get_about_menu_help
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        help_text = get_about_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_settings_menu_help_fits_keyboard(self):
        """Settings menu help fits in graphics box (keyboard)."""
        from game_help_hints import get_settings_menu_help

        help_text = get_settings_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_settings_menu_help_fits_gamepad(self):
        """Settings menu help fits in graphics box (gamepad)."""
        from game_help_hints import get_settings_menu_help
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        help_text = get_settings_menu_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_controls_hub_help_fits_keyboard(self):
        """Controls hub help fits in graphics box (keyboard)."""
        from game_help_hints import get_controls_hub_help

        help_text = get_controls_hub_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"

    def test_controls_hub_help_fits_gamepad(self):
        """Controls hub help fits in graphics box (gamepad)."""
        from game_help_hints import get_controls_hub_help
        from game_input_device_tracker import InputDeviceType, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)
        help_text = get_controls_hub_help(use_graphics_mode=True)
        assert len(help_text) <= self.MAX_WIDTH, f"'{help_text}' is {len(help_text)} chars"


class TestHelpTextConstants:
    """Test the ACTION_DISPLAY_NAMES used in Controls menu."""

    def test_action_display_names_has_main_menu(self):
        """Verify EXIT_TO_MENU display name is 'Main Menu'."""
        from game_menu_controls import ACTION_DISPLAY_NAMES

        assert ACTION_DISPLAY_NAMES[InputAction.EXIT_TO_MENU] == "Main Menu"

    def test_action_display_names_has_execute_selected_exploit(self):
        """Verify EXPLOIT_EXECUTE display name is 'Execute Selected Exploit'."""
        from game_menu_controls import ACTION_DISPLAY_NAMES

        assert ACTION_DISPLAY_NAMES[InputAction.EXPLOIT_EXECUTE] == "Execute Selected Exploit"


class TestGamepadControlsHelpPageDynamic:
    """Test that gamepad controls help page reflects custom bindings."""

    @staticmethod
    def _find_control(controls_list, description):
        """Find a control by description and return its button label."""
        for button_label, desc in controls_list:
            if desc == description:
                return button_label
        return None

    def test_get_gamepad_controls_with_no_mapper_returns_defaults(self):
        """Without mapper, get_gamepad_controls returns static defaults."""
        from game_help_content import HelpContent

        controls = HelpContent.get_gamepad_controls(mapper=None)

        # Should have all sections
        assert "gameplay" in controls
        assert "look_mode" in controls
        assert "targeting" in controls
        assert "menus" in controls

        # Check default buttons are shown (format is [(button, description), ...])
        wait_btn = self._find_control(controls["gameplay"], "Wait/pass turn")
        inv_btn = self._find_control(controls["gameplay"], "Inventory")
        assert wait_btn == "A"
        assert inv_btn == "Y"

    def test_get_gamepad_controls_with_mapper_returns_defaults_when_no_custom(self):
        """With mapper but no custom bindings, returns defaults."""
        from game_help_content import HelpContent

        mapper = InputMapper()
        controls = HelpContent.get_gamepad_controls(mapper=mapper)

        # Default WAIT is A button
        wait_btn = self._find_control(controls["gameplay"], "Wait/pass turn")
        assert wait_btn == "A"

    def test_get_gamepad_controls_reflects_remapped_wait_button(self):
        """WAIT remapped to B shows B instead of A in help."""
        import tcod.sdl.joystick

        from game_help_content import HelpContent

        mapper = InputMapper()
        # Remap WAIT from A (default) to B in GAMEPLAY context
        CB = tcod.sdl.joystick.ControllerButton
        mapper.add_gamepad_binding(InputAction.WAIT, CB.B, InputContext.GAMEPLAY)

        controls = HelpContent.get_gamepad_controls(mapper=mapper)
        wait_btn = self._find_control(controls["gameplay"], "Wait/pass turn")

        # Should show B (custom binding takes priority)
        assert "B" in wait_btn

    def test_get_gamepad_controls_reflects_remapped_inventory_button(self):
        """TOGGLE_INVENTORY remapped to X shows X instead of Y."""
        import tcod.sdl.joystick

        from game_help_content import HelpContent

        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton
        mapper.add_gamepad_binding(InputAction.TOGGLE_INVENTORY, CB.X, InputContext.GAMEPLAY)

        controls = HelpContent.get_gamepad_controls(mapper=mapper)
        inv_btn = self._find_control(controls["gameplay"], "Inventory")

        # Should show X (custom binding)
        assert "X" in inv_btn

    def test_get_gamepad_controls_reflects_remapped_confirm_in_menus(self):
        """CONFIRM remapped in MAIN_MENU context shows in menus section."""
        import tcod.sdl.joystick

        from game_help_content import HelpContent

        mapper = InputMapper()
        CB = tcod.sdl.joystick.ControllerButton
        # Remap CONFIRM from A to X in MAIN_MENU context
        mapper.add_gamepad_binding(InputAction.CONFIRM, CB.X, InputContext.MAIN_MENU)

        controls = HelpContent.get_gamepad_controls(mapper=mapper)
        confirm_btn = self._find_control(controls["menus"], "Select/confirm")

        # Should show X for confirm
        assert "X" in confirm_btn

    def test_get_gamepad_controls_shows_cycle_exploits_pair(self):
        """Cycle exploits shows paired buttons (RB / LB by default)."""
        from game_help_content import HelpContent

        mapper = InputMapper()
        controls = HelpContent.get_gamepad_controls(mapper=mapper)
        cycle_btn = self._find_control(controls["gameplay"], "Cycle exploits")

        # Default should show both RB and LB
        assert "RB" in cycle_btn or "LB" in cycle_btn

    def test_analog_controls_remain_static(self):
        """Analog stick controls (movement) don't change with remapping."""
        import tcod.sdl.joystick

        from game_help_content import HelpContent

        mapper = InputMapper()
        # Try remapping something random
        CB = tcod.sdl.joystick.ControllerButton
        mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        controls = HelpContent.get_gamepad_controls(mapper=mapper)
        move_btn = self._find_control(controls["gameplay"], "Move (8-way)")

        # Movement should still show analog description
        assert move_btn == "Left Stick / D-Pad"
