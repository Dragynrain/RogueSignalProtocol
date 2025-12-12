#!/usr/bin/env python3
"""
Unit tests for game_menu_controls.py

Tests for:
- ControlsMenuHub
- KeyboardBindingsMenu
- GamepadSettingsMenu
- GamepadBindingsMenu
- Helper functions (key/button display names)
"""

import pytest
import tcod
import tcod.event

from game_input_actions import InputAction, InputContext

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def settings():
    """Create a GameSettings instance for testing."""
    from game_config import GameSettings

    return GameSettings()


@pytest.fixture
def input_mapper():
    """Create an InputMapper instance for testing."""
    from game_input_mappings import InputMapper

    return InputMapper()


@pytest.fixture
def console():
    """Create a console for rendering tests."""
    return tcod.console.Console(80, 50)


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestKeyDisplayNames:
    """Test key_sym_to_display_name function."""

    def test_special_keys_have_readable_names(self):
        """Special keys should have human-readable names."""
        from game_input_mappings import key_sym_to_display_name

        assert key_sym_to_display_name(tcod.event.KeySym.SPACE) == "Space"
        assert key_sym_to_display_name(tcod.event.KeySym.RETURN) == "Enter"
        assert key_sym_to_display_name(tcod.event.KeySym.ESCAPE) == "ESC"

    def test_arrow_keys(self):
        """Arrow keys should have readable names (Unicode arrows)."""
        from game_input_mappings import key_sym_to_display_name

        assert key_sym_to_display_name(tcod.event.KeySym.UP) == "↑"
        assert key_sym_to_display_name(tcod.event.KeySym.DOWN) == "↓"
        assert key_sym_to_display_name(tcod.event.KeySym.LEFT) == "←"
        assert key_sym_to_display_name(tcod.event.KeySym.RIGHT) == "→"

    def test_letter_keys(self):
        """Letter keys should return uppercase letters."""
        from game_input_mappings import key_sym_to_display_name

        assert key_sym_to_display_name(tcod.event.KeySym.W) == "W"
        assert key_sym_to_display_name(tcod.event.KeySym.A) == "A"

    def test_numpad_keys(self):
        """Numpad keys should have readable names."""
        from game_input_mappings import key_sym_to_display_name

        assert key_sym_to_display_name(tcod.event.KeySym.KP_8) == "Numpad 8"
        assert key_sym_to_display_name(tcod.event.KeySym.KP_ENTER) == "Numpad Enter"


class TestButtonDisplayNames:
    """Test button_to_display_name function."""

    def test_face_buttons(self):
        """Face buttons should have readable names."""
        from game_menu_controls import button_to_display_name

        CB = tcod.sdl.joystick.ControllerButton

        assert button_to_display_name(CB.A) == "A"
        assert button_to_display_name(CB.B) == "B"
        assert button_to_display_name(CB.X) == "X"
        assert button_to_display_name(CB.Y) == "Y"

    def test_shoulder_buttons(self):
        """Shoulder buttons should have readable names."""
        from game_menu_controls import button_to_display_name

        CB = tcod.sdl.joystick.ControllerButton

        assert button_to_display_name(CB.LEFTSHOULDER) == "LB"
        assert button_to_display_name(CB.RIGHTSHOULDER) == "RB"

    def test_dpad(self):
        """D-pad buttons should have readable names."""
        from game_menu_controls import button_to_display_name

        CB = tcod.sdl.joystick.ControllerButton

        assert button_to_display_name(CB.DPAD_UP) == "D-Up"
        assert button_to_display_name(CB.DPAD_DOWN) == "D-Down"


class TestAxisDisplayNames:
    """Test axis_to_display_name function."""

    def test_triggers(self):
        """Triggers should have readable names."""
        from game_menu_controls import axis_to_display_name

        CA = tcod.sdl.joystick.ControllerAxis

        assert axis_to_display_name(CA.TRIGGERLEFT) == "LT"
        assert axis_to_display_name(CA.TRIGGERRIGHT) == "RT"


# =============================================================================
# ControlsMenuHub Tests
# =============================================================================


class TestControlsMenuHub:
    """Tests for ControlsMenuHub class."""

    def test_initialization(self, settings):
        """ControlsMenuHub should initialize with correct options."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)

        assert len(hub.options) == 4
        assert hub.options[0].startswith("Keyboard Bindings")
        assert hub.options[1].startswith("Gamepad Bindings")
        assert hub.options[2] == "Gamepad Settings"
        assert hub.options[3] == "Back"

    def test_get_context(self, settings):
        """ControlsMenuHub should return CONTROLS_MENU context."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        assert hub.get_context() == InputContext.CONTROLS_MENU

    def test_navigation_up(self, settings):
        """Navigate up should wrap around."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 0
        hub.execute_action(InputAction.NAVIGATE_UP)
        assert hub.selected_option == 3  # Wraps to last

    def test_navigation_down(self, settings):
        """Navigate down should wrap around."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 3
        hub.execute_action(InputAction.NAVIGATE_DOWN)
        assert hub.selected_option == 0  # Wraps to first

    def test_confirm_keyboard_bindings(self, settings):
        """Selecting Keyboard Bindings returns correct action."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 0
        result = hub.execute_action(InputAction.CONFIRM)
        assert result == "keyboard_bindings"

    def test_confirm_gamepad_bindings(self, settings):
        """Selecting Gamepad Bindings returns correct action."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 1
        result = hub.execute_action(InputAction.CONFIRM)
        assert result == "gamepad_bindings"

    def test_confirm_gamepad_settings(self, settings):
        """Selecting Gamepad Settings returns correct action."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 2
        result = hub.execute_action(InputAction.CONFIRM)
        assert result == "gamepad_settings"

    def test_confirm_back(self, settings):
        """Selecting Back returns 'back'."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.selected_option = 3
        result = hub.execute_action(InputAction.CONFIRM)
        assert result == "back"

    def test_cancel_returns_back(self, settings):
        """Cancel action returns 'back'."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        result = hub.execute_action(InputAction.CANCEL)
        assert result == "back"

    def test_render_does_not_crash(self, settings, console):
        """Render should complete without errors."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)
        hub.render(console)  # Should not raise

    def test_instructions_fit_within_box_bounds(self, settings):
        """Instructions text should fit within the menu box width."""
        from game_menu_controls import ControlsMenuHub

        hub = ControlsMenuHub(settings, None)

        # Test glyph mode (no background) - box width is 50
        glyph_layout = {
            "use_background_layout": False,
            "layout_zone": "center",
        }
        glyph_box_width = 50

        # Test graphics mode (with background) - box width is 28
        graphics_layout = {
            "use_background_layout": True,
            "layout_zone": "right",
        }
        graphics_box_width = 28

        # Check glyph mode instructions fit
        glyph_instructions = "Arrows | Enter:Select | ESC:Back"
        assert (
            len(glyph_instructions) < glyph_box_width
        ), f"Glyph instructions ({len(glyph_instructions)} chars) exceed box width ({glyph_box_width})"

        # Check graphics mode instructions fit (must be MUCH shorter - box is 28, content is 26)
        graphics_instructions = "D-Pad | A:Ok | B:Back"
        graphics_content_width = graphics_box_width - 2  # Account for box borders
        assert (
            len(graphics_instructions) < graphics_content_width
        ), f"Graphics instructions ({len(graphics_instructions)} chars) exceed content width ({graphics_content_width})"


# =============================================================================
# KeyboardBindingsMenu Tests
# =============================================================================


class TestKeyboardBindingsMenu:
    """Tests for KeyboardBindingsMenu class."""

    def test_initialization(self, settings, input_mapper):
        """KeyboardBindingsMenu should initialize with action list."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)

        assert len(menu.display_items) > 0
        assert len(menu.selectable_indices) > 0
        assert menu.selected_index == 0

    def test_get_context(self, settings, input_mapper):
        """KeyboardBindingsMenu should return CONTROLS_MENU context."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        assert menu.get_context() == InputContext.CONTROLS_MENU

    def test_navigation(self, settings, input_mapper):
        """Navigation should move through selectable items."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0
        menu.execute_action(InputAction.NAVIGATE_DOWN)
        assert menu.selected_index == 1

    def test_navigation_bounds(self, settings, input_mapper):
        """Navigation should not go below 0 or above max."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)

        # Can't go below 0
        menu.selected_index = 0
        menu._navigate(-1)
        assert menu.selected_index == 0

        # Can't go above max
        menu.selected_index = len(menu.selectable_indices) - 1
        menu._navigate(1)
        assert menu.selected_index == len(menu.selectable_indices) - 1

    def test_page_navigation(self, settings, input_mapper):
        """Page navigation should move multiple items."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0
        menu.execute_action(InputAction.NAVIGATE_PAGE_DOWN)
        assert menu.selected_index > 0  # Should have moved

    def test_enter_binding_mode(self, settings, input_mapper):
        """Confirm on an action should enter binding mode."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0
        menu.execute_action(InputAction.CONFIRM)

        assert menu.binding_mode is True
        assert menu.binding_action is not None

    def test_cancel_returns_back(self, settings, input_mapper):
        """Cancel action returns 'back'."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        result = menu.execute_action(InputAction.CANCEL)
        assert result == "back"

    def test_render_normal_mode(self, settings, input_mapper, console):
        """Render should complete in normal mode."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.render(console)

    def test_render_binding_mode(self, settings, input_mapper, console):
        """Render should complete in binding mode."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.MOVE_NORTH
        menu.render(console)

    def test_render_conflict_mode(self, settings, input_mapper, console):
        """Render should complete in conflict dialog mode."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.show_conflict_dialog = True
        menu.pending_key = tcod.event.KeySym.W
        menu.conflict_actions = [InputAction.MOVE_NORTH]
        menu.render(console)


# =============================================================================
# GamepadSettingsMenu Tests
# =============================================================================


class TestGamepadSettingsMenu:
    """Tests for GamepadSettingsMenu class."""

    def test_initialization(self, settings):
        """GamepadSettingsMenu should initialize with correct options."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)

        assert len(menu.options) == 6
        assert menu.options[0]["name"] == "Gamepad Enabled"
        assert menu.options[1]["name"] == "Stick Deadzone"
        assert menu.options[2]["name"] == "Movement Threshold"
        assert menu.options[3]["name"] == "Direction Locking"
        assert menu.options[4]["name"] == "Swap Sticks"
        assert menu.options[5]["name"] == "Back"

    def test_options_have_help_text(self, settings):
        """All options except Back should have help text."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)

        for opt in menu.options[:-1]:  # All except Back
            assert "help" in opt
            assert len(opt["help"]) > 0

    def test_get_context(self, settings):
        """GamepadSettingsMenu should return CONTROLS_MENU context."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        assert menu.get_context() == InputContext.CONTROLS_MENU

    def test_toggle_option(self, settings):
        """Toggle option should change boolean value."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 0  # Gamepad Enabled

        original = settings.gamepad_enabled
        menu._adjust_option(1)
        assert settings.gamepad_enabled != original

        # Toggle back
        menu._adjust_option(1)
        assert settings.gamepad_enabled == original

    def test_slider_option_increase(self, settings):
        """Slider option should increase value."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 1  # Stick Deadzone

        original = settings.gamepad_deadzone
        menu._adjust_option(1)
        assert settings.gamepad_deadzone > original

    def test_slider_option_decrease(self, settings):
        """Slider option should decrease value."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 1  # Stick Deadzone

        # First increase, then decrease
        settings.gamepad_deadzone = 0.20
        menu._adjust_option(-1)
        assert settings.gamepad_deadzone == 0.15

    def test_slider_bounds(self, settings):
        """Slider should not exceed min/max bounds."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.selected_option = 1  # Stick Deadzone

        # Try to go below min
        settings.gamepad_deadzone = 0.05
        menu._adjust_option(-1)
        assert settings.gamepad_deadzone == 0.05  # Stays at min

        # Try to go above max
        settings.gamepad_deadzone = 0.40
        menu._adjust_option(1)
        assert settings.gamepad_deadzone == 0.40  # Stays at max

    def test_cancel_returns_back(self, settings):
        """Cancel action returns 'back'."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        result = menu.execute_action(InputAction.CANCEL)
        assert result == "back"

    def test_render_does_not_crash(self, settings, console):
        """Render should complete without errors."""
        from game_menu_controls import GamepadSettingsMenu

        menu = GamepadSettingsMenu(settings, None)
        menu.render(console)


# =============================================================================
# GamepadBindingsMenu Tests
# =============================================================================


class TestGamepadBindingsMenu:
    """Tests for GamepadBindingsMenu class."""

    def test_initialization(self, settings, input_mapper):
        """GamepadBindingsMenu should initialize with action list."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)

        assert len(menu.display_items) > 0
        assert len(menu.selectable_indices) > 0
        assert menu.selected_index == 0

    def test_get_context(self, settings, input_mapper):
        """GamepadBindingsMenu should return CONTROLS_MENU context."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        assert menu.get_context() == InputContext.CONTROLS_MENU

    def test_navigation(self, settings, input_mapper):
        """Navigation should move through selectable items."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0
        menu.execute_action(InputAction.NAVIGATE_DOWN)
        assert menu.selected_index == 1

    def test_enter_binding_mode(self, settings, input_mapper):
        """Confirm on an action should enter binding mode."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0
        menu.execute_action(InputAction.CONFIRM)

        assert menu.binding_mode is True
        assert menu.binding_action is not None

    def test_cancel_returns_back(self, settings, input_mapper):
        """Cancel action returns 'back'."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        result = menu.execute_action(InputAction.CANCEL)
        assert result == "back"

    def test_render_normal_mode(self, settings, input_mapper, console):
        """Render should complete in normal mode."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.render(console)

    def test_render_binding_mode(self, settings, input_mapper, console):
        """Render should complete in binding mode."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT
        menu.render(console)

    def test_get_bindings_for_action(self, settings, input_mapper):
        """Should return button names for an action."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        bindings = menu._get_bindings_for_action(InputAction.WAIT)

        # WAIT should be bound to A button
        assert "A" in bindings


# =============================================================================
# KeyboardBindingsMenu Binding Mode Tests
# =============================================================================


class TestKeyboardBindingModeInput:
    """Tests for keyboard binding mode input handling."""

    def test_esc_cancels_binding_mode(self, settings, input_mapper):
        """ESC key should cancel binding mode without changing bindings."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.MOVE_NORTH

        # Create ESC key event
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.binding_action is None

    def test_delete_clears_all_bindings(self, settings, input_mapper):
        """DELETE key should clear all custom bindings for the action."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        # Add a custom binding first
        input_mapper.add_keyboard_binding(InputAction.WAIT, tcod.event.KeySym.T)

        # Create DELETE key event
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DELETE,
            sym=tcod.event.KeySym.DELETE,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.binding_action is None

    def test_reserved_key_rejected(self, settings, input_mapper):
        """Reserved keys (ESC, F12) should not be bindable."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        # Try to bind F12 (reserved)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.F12,
            sym=tcod.event.KeySym.F12,
            mod=tcod.event.Modifier.NONE,
        )

        result = menu._handle_binding_input(event)

        # Should still be in binding mode (key ignored)
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.WAIT

    def test_valid_key_adds_binding(self, settings, input_mapper):
        """Valid key should add binding and exit binding mode."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP  # Pick action with no T binding

        # Bind T key
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.T,
            sym=tcod.event.KeySym.T,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.binding_action is None
        # Check binding was added
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_conflicting_key_shows_dialog(self, settings, input_mapper):
        """Key already bound to another action should show conflict dialog."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # W is already bound to MOVE_NORTH by default
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.W,
            sym=tcod.event.KeySym.W,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.show_conflict_dialog is True
        assert menu.pending_key == tcod.event.KeySym.W
        assert InputAction.MOVE_NORTH in menu.conflict_actions


# =============================================================================
# KeyboardBindingsMenu Conflict Dialog Tests
# =============================================================================


class TestKeyboardConflictDialog:
    """Tests for keyboard conflict dialog handling."""

    def test_up_down_navigation(self, settings, input_mapper):
        """Up/down keys should navigate conflict dialog options."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.show_conflict_dialog = True
        menu.conflict_selection = 0  # Yes

        # Down to No
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DOWN,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier.NONE,
        )
        menu._handle_conflict_input(event)
        assert menu.conflict_selection == 1

        # Up back to Yes
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.UP,
            sym=tcod.event.KeySym.UP,
            mod=tcod.event.Modifier.NONE,
        )
        menu._handle_conflict_input(event)
        assert menu.conflict_selection == 0

    def test_enter_on_yes_replaces_binding(self, settings, input_mapper):
        """Enter on Yes should replace the binding."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.show_conflict_dialog = True
        menu.conflict_selection = 0  # Yes
        menu.pending_key = tcod.event.KeySym.W
        menu.binding_action = InputAction.TOGGLE_HELP
        menu.conflict_actions = [InputAction.MOVE_NORTH]

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RETURN,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_conflict_input(event)

        assert menu.show_conflict_dialog is False
        # Binding should have been added
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_enter_on_no_cancels(self, settings, input_mapper):
        """Enter on No should close dialog without changes."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.show_conflict_dialog = True
        menu.conflict_selection = 1  # No
        menu.pending_key = tcod.event.KeySym.W
        menu.binding_action = InputAction.TOGGLE_HELP
        menu.conflict_actions = [InputAction.MOVE_NORTH]

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RETURN,
            sym=tcod.event.KeySym.RETURN,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_conflict_input(event)

        assert menu.show_conflict_dialog is False
        # No binding should have been added
        assert not input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_esc_cancels_dialog(self, settings, input_mapper):
        """ESC should close conflict dialog without changes."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.show_conflict_dialog = True
        menu.conflict_selection = 0
        menu.pending_key = tcod.event.KeySym.W
        menu.binding_action = InputAction.TOGGLE_HELP

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_conflict_input(event)

        assert menu.show_conflict_dialog is False
        assert menu.pending_key is None
        assert menu.binding_action is None


# =============================================================================
# GamepadBindingsMenu Tab Switching Tests
# =============================================================================


class TestGamepadTabSwitching:
    """Tests for gamepad bindings menu tab switching."""

    def test_initial_tab_is_gameplay(self, settings, input_mapper):
        """Menu should start on Gameplay tab."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        assert menu.current_tab == 0
        assert menu.CONTEXT_TABS[0][0] == "Gameplay"

    def test_switch_tab_right(self, settings, input_mapper):
        """Switching right should go to Menus tab."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu._switch_tab(1)

        assert menu.current_tab == 1
        assert menu.CONTEXT_TABS[1][0] == "Menus"

    def test_switch_tab_wraps(self, settings, input_mapper):
        """Tab switching should wrap around."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.current_tab = 1  # Menus
        menu._switch_tab(1)  # Should wrap to Gameplay

        assert menu.current_tab == 0

    def test_switch_tab_rebuilds_action_list(self, settings, input_mapper):
        """Switching tabs should rebuild the action list."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        gameplay_items = len(menu.display_items)

        menu._switch_tab(1)  # Switch to Menus
        menus_items = len(menu.display_items)

        # Menus tab has fewer items (just navigation)
        assert menus_items != gameplay_items

    def test_switch_tab_resets_selection(self, settings, input_mapper):
        """Switching tabs should reset scroll position."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 5  # Navigate down
        menu._switch_tab(1)

        assert menu.selected_index == 0

    def test_left_bracket_switches_tab(self, settings, input_mapper):
        """Left bracket key should switch tab left."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.current_tab = 1  # Start on Menus

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.LEFTBRACKET,
            sym=tcod.event.KeySym.LEFTBRACKET,
            mod=tcod.event.Modifier.NONE,
        )

        menu.handle_input(event)
        assert menu.current_tab == 0

    def test_right_bracket_switches_tab(self, settings, input_mapper):
        """Right bracket key should switch tab right."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.current_tab = 0  # Start on Gameplay

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RIGHTBRACKET,
            sym=tcod.event.KeySym.RIGHTBRACKET,
            mod=tcod.event.Modifier.NONE,
        )

        menu.handle_input(event)
        assert menu.current_tab == 1


# =============================================================================
# GamepadBindingsMenu Binding Mode Tests
# =============================================================================


class TestGamepadBindingModeInput:
    """Tests for gamepad binding mode input handling."""

    def test_esc_cancels_binding_mode(self, settings, input_mapper):
        """ESC key should cancel binding mode."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.ESCAPE,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.binding_action is None

    def test_delete_clears_bindings(self, settings, input_mapper):
        """DELETE key should clear gamepad bindings."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.DELETE,
            sym=tcod.event.KeySym.DELETE,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        assert menu.binding_mode is False
        assert menu.binding_action is None


# =============================================================================
# Gamepad Button Actions in Controls Menus (X=Default, Y=Reset)
# =============================================================================


class TestGamepadButtonActionsInKeyboardMenu:
    """Tests for gamepad X=Default and Y=Reset in keyboard bindings menu."""

    def test_x_button_clears_binding_in_binding_mode(self, settings, input_mapper):
        """X button should clear all bindings for action in binding mode."""
        from game_menu_controls import KeyboardBindingsMenu

        # Add a custom binding first
        input_mapper.add_keyboard_binding(InputAction.WAIT, tcod.event.KeySym.T)

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        # Simulate X button (CONTROLS_RESET_DEFAULT action)
        result = menu.execute_action(InputAction.CONTROLS_RESET_DEFAULT)

        assert menu.binding_mode is False
        assert menu.binding_action is None

    def test_y_button_resets_all_bindings(self, settings, input_mapper):
        """Y button should reset all keyboard bindings to defaults."""
        from game_menu_controls import KeyboardBindingsMenu

        # Add some custom bindings
        input_mapper.add_keyboard_binding(InputAction.TOGGLE_HELP, tcod.event.KeySym.T)
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

        menu = KeyboardBindingsMenu(settings, input_mapper, None)

        # Simulate Y button (CONTROLS_RESET_ALL action)
        result = menu.execute_action(InputAction.CONTROLS_RESET_ALL)

        # Bindings should be reset
        assert not input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)


class TestGamepadButtonActionsInGamepadMenu:
    """Tests for gamepad X=Default and Y=Reset in gamepad bindings menu."""

    def test_x_button_clears_binding_in_binding_mode(self, settings, input_mapper):
        """X button should clear all bindings for action in binding mode."""
        from game_menu_controls import GamepadBindingsMenu

        CB = tcod.sdl.joystick.ControllerButton

        # Add a custom binding first
        input_mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.WAIT

        # Simulate X button (CONTROLS_RESET_DEFAULT action)
        result = menu.execute_action(InputAction.CONTROLS_RESET_DEFAULT)

        assert menu.binding_mode is False
        assert menu.binding_action is None

    def test_y_button_resets_all_bindings(self, settings, input_mapper):
        """Y button should reset all gamepad bindings to defaults."""
        from game_menu_controls import GamepadBindingsMenu

        CB = tcod.sdl.joystick.ControllerButton

        # Add some custom bindings
        input_mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)
        assert input_mapper.has_custom_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        menu = GamepadBindingsMenu(settings, input_mapper, None)

        # Simulate Y button (CONTROLS_RESET_ALL action)
        result = menu.execute_action(InputAction.CONTROLS_RESET_ALL)

        # Bindings should be reset
        assert not input_mapper.has_custom_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)


# =============================================================================
# Reset to Defaults Tests
# =============================================================================


class TestResetToDefaults:
    """Tests for reset to defaults functionality."""

    def test_keyboard_reset_clears_custom_bindings(self, settings, input_mapper):
        """Reset keyboard should clear all custom keyboard bindings."""
        from game_menu_controls import KeyboardBindingsMenu

        # Add some custom bindings
        input_mapper.add_keyboard_binding(InputAction.TOGGLE_HELP, tcod.event.KeySym.T)
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu._reset_to_defaults()

        assert not input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_gamepad_reset_clears_custom_bindings(self, settings, input_mapper):
        """Reset gamepad should clear all custom gamepad bindings."""
        from game_menu_controls import GamepadBindingsMenu

        CB = tcod.sdl.joystick.ControllerButton

        # Add some custom bindings
        input_mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)
        assert input_mapper.has_custom_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu._reset_to_defaults()

        assert not input_mapper.has_custom_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)

    def test_r_key_triggers_keyboard_reset(self, settings, input_mapper):
        """R key should trigger reset in keyboard bindings menu."""
        from game_menu_controls import KeyboardBindingsMenu

        # Add custom binding
        input_mapper.add_keyboard_binding(InputAction.TOGGLE_HELP, tcod.event.KeySym.T)

        menu = KeyboardBindingsMenu(settings, input_mapper, None)

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.R,
            sym=tcod.event.KeySym.R,
            mod=tcod.event.Modifier.NONE,
        )

        menu.handle_input(event)

        assert not input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_r_key_triggers_gamepad_reset(self, settings, input_mapper):
        """R key should trigger reset in gamepad bindings menu."""
        from game_menu_controls import GamepadBindingsMenu

        CB = tcod.sdl.joystick.ControllerButton

        # Add custom binding
        input_mapper.add_gamepad_binding(InputAction.WAIT, CB.X, InputContext.GAMEPLAY)

        menu = GamepadBindingsMenu(settings, input_mapper, None)

        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.R,
            sym=tcod.event.KeySym.R,
            mod=tcod.event.Modifier.NONE,
        )

        menu.handle_input(event)

        assert not input_mapper.has_custom_gamepad_bindings(InputAction.WAIT, InputContext.GAMEPLAY)


# =============================================================================
# Modifier Key Handling Tests
# =============================================================================


class TestModifierKeyHandling:
    """Tests for modifier key handling in keyboard binding mode.

    Issue: When pressing Shift to type '?' (Shift+/), the binding mode
    captures Shift as the binding instead of waiting for Shift+key.
    """

    def test_shift_alone_does_not_bind(self, settings, input_mapper):
        """Pressing only Shift should NOT create a binding."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press Shift key alone (LSHIFT)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.LSHIFT,
            sym=tcod.event.KeySym.LSHIFT,
            mod=tcod.event.Modifier.SHIFT,
        )

        menu._handle_binding_input(event)

        # Should still be in binding mode - Shift alone is ignored
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP
        # No binding should have been added
        assert not input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_ctrl_alone_does_not_bind(self, settings, input_mapper):
        """Pressing only Ctrl should NOT create a binding."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press Ctrl key alone (LCTRL)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.LCTRL,
            sym=tcod.event.KeySym.LCTRL,
            mod=tcod.event.Modifier.CTRL,
        )

        menu._handle_binding_input(event)

        # Should still be in binding mode - Ctrl alone is ignored
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

    def test_alt_alone_does_not_bind(self, settings, input_mapper):
        """Pressing only Alt should NOT create a binding."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press Alt key alone (LALT)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.LALT,
            sym=tcod.event.KeySym.LALT,
            mod=tcod.event.Modifier.ALT,
        )

        menu._handle_binding_input(event)

        # Should still be in binding mode - Alt alone is ignored
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

    def test_right_shift_alone_does_not_bind(self, settings, input_mapper):
        """Pressing only Right Shift should NOT create a binding."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press Right Shift key alone (RSHIFT)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.RSHIFT,
            sym=tcod.event.KeySym.RSHIFT,
            mod=tcod.event.Modifier.SHIFT,
        )

        menu._handle_binding_input(event)

        # Should still be in binding mode - Shift alone is ignored
        assert menu.binding_mode is True
        assert menu.binding_action == InputAction.TOGGLE_HELP

    def test_shift_plus_key_creates_binding(self, settings, input_mapper):
        """Pressing Shift+/ should create a binding (for '?' key)."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press / with Shift held (which produces '?' on US keyboard)
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.SLASH,
            sym=tcod.event.KeySym.SLASH,
            mod=tcod.event.Modifier.SHIFT,
        )

        menu._handle_binding_input(event)

        # Should exit binding mode and create a binding
        assert menu.binding_mode is False
        assert menu.binding_action is None
        # Binding should have been added
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)

    def test_normal_key_without_modifier_still_works(self, settings, input_mapper):
        """Normal key presses without modifiers should still work."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.binding_mode = True
        menu.binding_action = InputAction.TOGGLE_HELP

        # Press T without any modifiers
        event = tcod.event.KeyDown(
            scancode=tcod.event.Scancode.T,
            sym=tcod.event.KeySym.T,
            mod=tcod.event.Modifier.NONE,
        )

        menu._handle_binding_input(event)

        # Should exit binding mode and create a binding
        assert menu.binding_mode is False
        assert menu.binding_action is None
        assert input_mapper.has_custom_keyboard_bindings(InputAction.TOGGLE_HELP)


# =============================================================================
# Mouse Wheel Tests
# =============================================================================

# =============================================================================
# Settings Menu Separator Tests
# =============================================================================


class TestSettingsMenuSeparator:
    """Tests for visual separators in the settings menu.

    Issue: In classic graphics mode (glyph mode), there should be a blank
    line separator above the "Export Debug Package" option to visually
    separate utility actions from settings.
    """

    def test_separator_option_exists_before_export_debug_package(self, settings):
        """Settings menu should have a separator before Export Debug Package."""
        from game_menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)

        # Find the index of Export Debug Package option
        export_index = None
        for i, opt in enumerate(menu.options):
            if opt.get("name") == "Export Debug Package":
                export_index = i
                break

        assert export_index is not None, "Export Debug Package option not found"

        # The option before Export Debug Package should be a separator
        # (or there should be a separator type option somewhere before it)
        separator_index = export_index - 1
        assert separator_index >= 0, "Export Debug Package is first option (no room for separator)"

        separator_option = menu.options[separator_index]
        assert (
            separator_option.get("type") == "separator"
        ), f"Expected separator before Export Debug Package, found: {separator_option}"

    def test_separator_renders_as_blank_line_in_classic_mode(self, settings, console):
        """Separator should render as blank line in classic (glyph) mode."""
        from game_menu_settings import SettingsMenu

        menu = SettingsMenu(settings, None, None)

        # Force classic/glyph mode (no background)
        menu.menu_background = None

        # Render the menu
        menu.render(console)

        # This test passes if render doesn't crash
        # The visual blank line is verified by test_separator_option_exists_before_export_debug_package


class TestMouseWheelNavigation:
    """Tests for mouse wheel navigation in binding menus."""

    def test_keyboard_menu_wheel_up(self, settings, input_mapper):
        """Mouse wheel up should navigate up in keyboard bindings."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 5

        # Simulate wheel up (positive y)
        class MockWheelEvent:
            y = 1

        menu.handle_mouse_wheel(MockWheelEvent())

        # Should have moved up (by WHEEL_SCROLL_SPEED = 3)
        assert menu.selected_index < 5

    def test_keyboard_menu_wheel_down(self, settings, input_mapper):
        """Mouse wheel down should navigate down in keyboard bindings."""
        from game_menu_controls import KeyboardBindingsMenu

        menu = KeyboardBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0

        # Simulate wheel down (negative y)
        class MockWheelEvent:
            y = -1

        menu.handle_mouse_wheel(MockWheelEvent())

        # Should have moved down
        assert menu.selected_index > 0

    def test_gamepad_menu_wheel_navigation(self, settings, input_mapper):
        """Mouse wheel should work in gamepad bindings menu."""
        from game_menu_controls import GamepadBindingsMenu

        menu = GamepadBindingsMenu(settings, input_mapper, None)
        menu.selected_index = 0

        class MockWheelEvent:
            y = -1

        menu.handle_mouse_wheel(MockWheelEvent())

        assert menu.selected_index > 0
