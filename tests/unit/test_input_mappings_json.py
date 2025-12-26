#!/usr/bin/env python3
"""
Unit tests for default bindings JSON loading in game_input_mappings.py

Tests that default bindings can be loaded from default_bindings.json
instead of being hardcoded in Python.

Includes fail-fast tests to verify behavior when JSON is missing or corrupted
(per CLAUDE.md: fail-fast on missing config, no hardcoded fallbacks).
"""

import json
import os
import tempfile
from unittest.mock import patch

import pytest
import tcod.event
import tcod.sdl.joystick

from game_input_actions import InputAction, InputContext

# =============================================================================
# JSON File Existence and Structure Tests
# =============================================================================


class TestDefaultBindingsFileExists:
    """Tests that the default_bindings.json file exists and is valid JSON."""

    def test_default_bindings_json_exists(self):
        """default_bindings.json should exist in the project root."""
        assert os.path.exists("default_bindings.json"), "default_bindings.json not found"

    def test_default_bindings_is_valid_json(self):
        """default_bindings.json should be valid JSON."""
        with open("default_bindings.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestDefaultBindingsStructure:
    """Tests that default_bindings.json has the correct structure."""

    @pytest.fixture
    def bindings(self):
        """Load default bindings from JSON."""
        with open("default_bindings.json") as f:
            return json.load(f)

    def test_has_keyboard_section(self, bindings):
        """Should have a 'keyboard' section."""
        assert "keyboard" in bindings
        assert isinstance(bindings["keyboard"], dict)

    def test_has_gamepad_section(self, bindings):
        """Should have a 'gamepad' section."""
        assert "gamepad" in bindings
        assert isinstance(bindings["gamepad"], dict)

    def test_gamepad_has_buttons_section(self, bindings):
        """Gamepad section should have a 'buttons' subsection."""
        assert "buttons" in bindings["gamepad"]
        assert isinstance(bindings["gamepad"]["buttons"], dict)

    def test_gamepad_has_axes_section(self, bindings):
        """Gamepad section should have an 'axes' subsection."""
        assert "axes" in bindings["gamepad"]
        assert isinstance(bindings["gamepad"]["axes"], dict)


# =============================================================================
# Keyboard Bindings Tests
# =============================================================================


class TestKeyboardDefaultBindings:
    """Tests that keyboard defaults are correctly loaded from JSON."""

    @pytest.fixture
    def bindings(self):
        """Load default bindings from JSON."""
        with open("default_bindings.json") as f:
            return json.load(f)

    def test_movement_keys_bound(self, bindings):
        """All 8-directional movement keys should be in defaults."""
        kb = bindings["keyboard"]
        # WASD should be bound to movement
        assert "W" in kb and kb["W"] == "MOVE_NORTH"
        assert "S" in kb and kb["S"] == "MOVE_SOUTH"
        assert "A" in kb and kb["A"] == "MOVE_WEST"
        assert "D" in kb and kb["D"] == "MOVE_EAST"
        # QEZC for diagonals
        assert "Q" in kb and kb["Q"] == "MOVE_NORTHWEST"
        assert "E" in kb and kb["E"] == "MOVE_NORTHEAST"
        assert "Z" in kb and kb["Z"] == "MOVE_SOUTHWEST"
        assert "C" in kb and kb["C"] == "MOVE_SOUTHEAST"

    def test_arrow_keys_bound(self, bindings):
        """Arrow keys should be bound to movement."""
        kb = bindings["keyboard"]
        assert "UP" in kb and kb["UP"] == "MOVE_NORTH"
        assert "DOWN" in kb and kb["DOWN"] == "MOVE_SOUTH"
        assert "LEFT" in kb and kb["LEFT"] == "MOVE_WEST"
        assert "RIGHT" in kb and kb["RIGHT"] == "MOVE_EAST"

    def test_numpad_keys_bound(self, bindings):
        """Numpad keys should be bound to 8-directional movement."""
        kb = bindings["keyboard"]
        assert "KP_8" in kb and kb["KP_8"] == "MOVE_NORTH"
        assert "KP_2" in kb and kb["KP_2"] == "MOVE_SOUTH"
        assert "KP_4" in kb and kb["KP_4"] == "MOVE_WEST"
        assert "KP_6" in kb and kb["KP_6"] == "MOVE_EAST"
        assert "KP_7" in kb and kb["KP_7"] == "MOVE_NORTHWEST"
        assert "KP_9" in kb and kb["KP_9"] == "MOVE_NORTHEAST"
        assert "KP_1" in kb and kb["KP_1"] == "MOVE_SOUTHWEST"
        assert "KP_3" in kb and kb["KP_3"] == "MOVE_SOUTHEAST"
        assert "KP_5" in kb and kb["KP_5"] == "WAIT"

    def test_wait_keys_bound(self, bindings):
        """Wait/rest keys should be bound."""
        kb = bindings["keyboard"]
        assert "SPACE" in kb and kb["SPACE"] == "WAIT"
        assert "PERIOD" in kb and kb["PERIOD"] == "WAIT"

    def test_ui_toggles_bound(self, bindings):
        """UI toggle keys should be bound."""
        kb = bindings["keyboard"]
        assert "I" in kb and kb["I"] == "TOGGLE_INVENTORY"
        assert "L" in kb and kb["L"] == "TOGGLE_LOOK_MODE"
        assert "F" in kb and kb["F"] == "TOGGLE_LORE_VIEWER"
        assert "V" in kb and kb["V"] == "TOGGLE_ACHIEVEMENTS"

    def test_confirm_cancel_bound(self, bindings):
        """Confirm and cancel keys should be bound."""
        kb = bindings["keyboard"]
        assert "RETURN" in kb and kb["RETURN"] == "CONFIRM"
        assert "ESCAPE" in kb and kb["ESCAPE"] == "CANCEL"

    def test_exploit_keys_bound(self, bindings):
        """Exploit slot keys should be bound."""
        kb = bindings["keyboard"]
        assert "N1" in kb and kb["N1"] == "EXPLOIT_SLOT_1"
        assert "N2" in kb and kb["N2"] == "EXPLOIT_SLOT_2"
        assert "N3" in kb and kb["N3"] == "EXPLOIT_SLOT_3"
        assert "N4" in kb and kb["N4"] == "EXPLOIT_SLOT_4"
        assert "N5" in kb and kb["N5"] == "EXPLOIT_SLOT_5"


# =============================================================================
# Gamepad Buttons Tests
# =============================================================================


class TestGamepadButtonDefaultBindings:
    """Tests that gamepad button defaults are correctly loaded from JSON."""

    @pytest.fixture
    def bindings(self):
        """Load default bindings from JSON."""
        with open("default_bindings.json") as f:
            return json.load(f)

    def test_gameplay_context_buttons(self, bindings):
        """Gameplay context should have correct button bindings."""
        gp = bindings["gamepad"]["buttons"]["GAMEPLAY"]
        assert gp["A"] == "WAIT"
        assert gp["B"] == "CANCEL"
        assert gp["X"] == "EXPLOIT_SLOT_1"
        assert gp["Y"] == "TOGGLE_INVENTORY"
        assert gp["RIGHTSHOULDER"] == "EXPLOIT_CYCLE_NEXT"
        assert gp["LEFTSHOULDER"] == "EXPLOIT_CYCLE_PREV"
        assert gp["START"] == "EXIT_TO_MENU"
        assert gp["BACK"] == "TOGGLE_HELP"

    def test_gameplay_dpad_movement(self, bindings):
        """Gameplay D-Pad should be bound to movement."""
        gp = bindings["gamepad"]["buttons"]["GAMEPLAY"]
        assert gp["DPAD_UP"] == "MOVE_NORTH"
        assert gp["DPAD_DOWN"] == "MOVE_SOUTH"
        assert gp["DPAD_LEFT"] == "MOVE_WEST"
        assert gp["DPAD_RIGHT"] == "MOVE_EAST"

    def test_inventory_context_buttons(self, bindings):
        """Inventory context should have correct button bindings."""
        gp = bindings["gamepad"]["buttons"]["INVENTORY"]
        assert gp["A"] == "CONFIRM"
        assert gp["B"] == "CANCEL"
        assert gp["Y"] == "TOGGLE_INVENTORY"

    def test_menu_contexts_have_confirm_cancel(self, bindings):
        """All menu contexts should have A=CONFIRM, B=CANCEL."""
        menu_contexts = ["MAIN_MENU", "SETTINGS_MENU", "CONTROLS_MENU", "HELP", "LORE_VIEWER"]
        for ctx in menu_contexts:
            gp = bindings["gamepad"]["buttons"][ctx]
            assert gp["A"] == "CONFIRM", f"{ctx} missing A=CONFIRM"
            assert gp["B"] == "CANCEL", f"{ctx} missing B=CANCEL"

    def test_controls_menu_has_reset_buttons(self, bindings):
        """Controls menu should have X=RESET_DEFAULT, Y=RESET_ALL."""
        gp = bindings["gamepad"]["buttons"]["CONTROLS_MENU"]
        assert gp["X"] == "CONTROLS_RESET_DEFAULT"
        assert gp["Y"] == "CONTROLS_RESET_ALL"


# =============================================================================
# Gamepad Axes Tests
# =============================================================================


class TestGamepadAxisDefaultBindings:
    """Tests that gamepad axis defaults are correctly loaded from JSON."""

    @pytest.fixture
    def bindings(self):
        """Load default bindings from JSON."""
        with open("default_bindings.json") as f:
            return json.load(f)

    def test_gameplay_triggers(self, bindings):
        """Gameplay context should have correct trigger bindings."""
        ga = bindings["gamepad"]["axes"]["GAMEPLAY"]
        assert ga["TRIGGERRIGHT"] == "EXPLOIT_EXECUTE"
        assert ga["TRIGGERLEFT"] == "TOGGLE_LOOK_MODE"

    def test_targeting_trigger(self, bindings):
        """Targeting context should have RT=CONFIRM."""
        ga = bindings["gamepad"]["axes"]["TARGETING"]
        assert ga["TRIGGERRIGHT"] == "CONFIRM"


# =============================================================================
# InputMapper JSON Loading Tests
# =============================================================================


class TestInputMapperLoadsFromJSON:
    """Tests that InputMapper correctly loads defaults from JSON."""

    @pytest.fixture
    def input_mapper(self):
        """Create an InputMapper instance."""
        from game_input_mappings import InputMapper

        return InputMapper()

    def test_keyboard_wasd_loaded(self, input_mapper):
        """InputMapper should have WASD from JSON defaults."""
        assert input_mapper.get_action_for_key(tcod.event.KeySym.W) == InputAction.MOVE_NORTH
        assert input_mapper.get_action_for_key(tcod.event.KeySym.A) == InputAction.MOVE_WEST
        assert input_mapper.get_action_for_key(tcod.event.KeySym.S) == InputAction.MOVE_SOUTH
        assert input_mapper.get_action_for_key(tcod.event.KeySym.D) == InputAction.MOVE_EAST

    def test_keyboard_ui_toggles_loaded(self, input_mapper):
        """InputMapper should have UI toggles from JSON defaults."""
        assert input_mapper.get_action_for_key(tcod.event.KeySym.I) == InputAction.TOGGLE_INVENTORY
        assert input_mapper.get_action_for_key(tcod.event.KeySym.L) == InputAction.TOGGLE_LOOK_MODE

    def test_gamepad_gameplay_buttons_loaded(self, input_mapper):
        """InputMapper should have gamepad gameplay buttons from JSON."""
        CB = tcod.sdl.joystick.ControllerButton
        ctx = InputContext.GAMEPLAY
        assert input_mapper.get_action_for_gamepad_button(CB.A, ctx) == InputAction.WAIT
        assert input_mapper.get_action_for_gamepad_button(CB.B, ctx) == InputAction.CANCEL
        assert input_mapper.get_action_for_gamepad_button(CB.X, ctx) == InputAction.EXPLOIT_SLOT_1

    def test_gamepad_menu_buttons_loaded(self, input_mapper):
        """InputMapper should have gamepad menu buttons from JSON."""
        CB = tcod.sdl.joystick.ControllerButton
        ctx = InputContext.MAIN_MENU
        assert input_mapper.get_action_for_gamepad_button(CB.A, ctx) == InputAction.CONFIRM
        assert input_mapper.get_action_for_gamepad_button(CB.B, ctx) == InputAction.CANCEL

    def test_gamepad_triggers_loaded(self, input_mapper):
        """InputMapper should have gamepad triggers from JSON."""
        CA = tcod.sdl.joystick.ControllerAxis
        ctx = InputContext.GAMEPLAY
        assert (
            input_mapper.get_action_for_gamepad_axis(CA.TRIGGERRIGHT, ctx)
            == InputAction.EXPLOIT_EXECUTE
        )
        assert (
            input_mapper.get_action_for_gamepad_axis(CA.TRIGGERLEFT, ctx)
            == InputAction.TOGGLE_LOOK_MODE
        )


# =============================================================================
# Action Name Validation Tests
# =============================================================================


class TestActionNameValidation:
    """Tests that all action names in JSON are valid InputAction values."""

    @pytest.fixture
    def bindings(self):
        """Load default bindings from JSON."""
        with open("default_bindings.json") as f:
            return json.load(f)

    def test_keyboard_action_names_valid(self, bindings):
        """All keyboard action names should be valid InputAction values."""
        valid_actions = {a.name for a in InputAction}
        for key, action_name in bindings["keyboard"].items():
            if key.startswith("_"):  # Skip comment fields
                continue
            assert action_name in valid_actions, f"Invalid action '{action_name}' for key '{key}'"

    def test_gamepad_button_action_names_valid(self, bindings):
        """All gamepad button action names should be valid InputAction values."""
        valid_actions = {a.name for a in InputAction}
        for context, buttons in bindings["gamepad"]["buttons"].items():
            for button, action_name in buttons.items():
                assert (
                    action_name in valid_actions
                ), f"Invalid action '{action_name}' for {context}/{button}"

    def test_gamepad_axis_action_names_valid(self, bindings):
        """All gamepad axis action names should be valid InputAction values."""
        valid_actions = {a.name for a in InputAction}
        for context, axes in bindings["gamepad"]["axes"].items():
            for axis, action_name in axes.items():
                assert (
                    action_name in valid_actions
                ), f"Invalid action '{action_name}' for {context}/{axis}"


# =============================================================================
# Fail-Fast Tests (per CLAUDE.md: no hardcoded fallbacks)
# =============================================================================


class TestInputMapperFailFast:
    """Tests that InputMapper fails fast when JSON is missing or corrupted.

    Per CLAUDE.md: 'Fail-fast on missing config... No hardcoded fallbacks.'
    """

    def test_raises_when_json_missing(self, tmp_path, monkeypatch):
        """InputMapper should raise FileNotFoundError when JSON is missing."""
        from game_input_mappings import InputMapper

        # Point to non-existent file
        monkeypatch.setattr(
            "game_input_mappings.DEFAULT_BINDINGS_PATH",
            str(tmp_path / "nonexistent.json"),
        )

        with pytest.raises(FileNotFoundError) as exc_info:
            InputMapper()

        assert "not found" in str(exc_info.value).lower()

    def test_raises_when_json_malformed(self, tmp_path, monkeypatch):
        """InputMapper should raise JSONDecodeError when JSON is malformed."""
        from game_input_mappings import InputMapper

        # Create malformed JSON file
        bad_json = tmp_path / "bad_bindings.json"
        bad_json.write_text("{ invalid json }", encoding="utf-8")

        monkeypatch.setattr(
            "game_input_mappings.DEFAULT_BINDINGS_PATH",
            str(bad_json),
        )

        with pytest.raises(json.JSONDecodeError):
            InputMapper()

    def test_raises_when_json_unreadable(self, tmp_path, monkeypatch):
        """InputMapper should raise OSError when JSON file cannot be read."""
        from game_input_mappings import InputMapper

        # Point to the tmp_path directory (not a file)
        monkeypatch.setattr(
            "game_input_mappings.DEFAULT_BINDINGS_PATH",
            str(tmp_path),  # This is a directory, not a file
        )

        # os.path.exists returns True for directories, but open() fails
        with pytest.raises((OSError, PermissionError, IsADirectoryError)):
            InputMapper()

    def test_no_fallback_to_hardcoded_defaults(self, tmp_path, monkeypatch):
        """InputMapper should NOT silently use hardcoded defaults when JSON fails.

        This test ensures we don't regress back to the old fallback behavior.
        """
        from game_input_mappings import InputMapper

        # Point to non-existent file
        monkeypatch.setattr(
            "game_input_mappings.DEFAULT_BINDINGS_PATH",
            str(tmp_path / "missing.json"),
        )

        # Should raise an error, not silently continue with hardcoded defaults
        with pytest.raises(FileNotFoundError):
            mapper = InputMapper()
            # If we got here, the fallback is active (BAD!)
            # Check that mapper has bindings - this would indicate fallback was used
            assert len(mapper._default_keyboard_map) == 0, "Hardcoded fallback was used!"

    def test_valid_json_loads_successfully(self, tmp_path, monkeypatch):
        """InputMapper should load successfully with valid JSON."""
        from game_input_mappings import InputMapper

        # Create minimal valid JSON
        valid_json = tmp_path / "valid_bindings.json"
        valid_json.write_text(
            json.dumps({
                "keyboard": {"W": "MOVE_NORTH"},
                "gamepad": {"buttons": {}, "axes": {}},
            }),
            encoding="utf-8",
        )

        monkeypatch.setattr(
            "game_input_mappings.DEFAULT_BINDINGS_PATH",
            str(valid_json),
        )

        # Should not raise
        mapper = InputMapper()
        assert mapper.get_action_for_key(tcod.event.KeySym.W) == InputAction.MOVE_NORTH
