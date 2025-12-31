"""
game_input_mappings.py - Input Mapping System

Manages the bidirectional mapping between physical inputs (keyboard keys, gamepad buttons)
and abstract game actions. Supports custom remapping and context-sensitive bindings.

Architecture:
- Default mappings loaded from default_bindings.json (customizable)
- Custom user bindings (loaded from settings, override defaults)
- Context-aware lookups (same key can do different things in different states)
- Conflict detection for remapping UI
- Modifier key support (Shift, Ctrl, Alt combinations)
"""

import json
import logging
import os
from typing import NamedTuple

import tcod.event
import tcod.sdl.joystick

from rsp.input.actions import InputAction, InputContext

# =============================================================================
# KEY BINDING TYPE (with modifier support)
# =============================================================================


class KeyBinding(NamedTuple):
    """
    Represents a keyboard key binding with optional modifier.

    Attributes:
        key: The primary key (tcod.event.KeySym)
        modifier: Modifier flags (tcod.event.Modifier, 0 for no modifier)
    """

    key: tcod.event.KeySym
    modifier: int = 0  # tcod.event.Modifier flags

    def matches(self, key: tcod.event.KeySym, mod: int) -> bool:
        """
        Check if this binding matches a key press.

        For bindings WITH modifiers: both key and modifier must match.
        For bindings WITHOUT modifiers: key must match, and no modifiers pressed.

        Args:
            key: The pressed key
            mod: The modifier flags from the event

        Returns:
            True if this binding matches the key press
        """
        if self.key != key:
            return False

        # Normalize both modifiers to canonical form before comparison
        # This handles LSHIFT vs RSHIFT vs SHIFT equivalence
        pressed_mods = normalize_modifier(mod)
        required_mods = normalize_modifier(self.modifier)

        return pressed_mods == required_mods


# Modifier display names for UI
MODIFIER_DISPLAY_NAMES = {
    tcod.event.Modifier.SHIFT: "Shift",
    tcod.event.Modifier.CTRL: "Ctrl",
    tcod.event.Modifier.ALT: "Alt",
    tcod.event.Modifier.LSHIFT: "Shift",
    tcod.event.Modifier.RSHIFT: "Shift",
    tcod.event.Modifier.LCTRL: "Ctrl",
    tcod.event.Modifier.RCTRL: "Ctrl",
    tcod.event.Modifier.LALT: "Alt",
    tcod.event.Modifier.RALT: "Alt",
}


# Path to default bindings JSON file
DEFAULT_BINDINGS_PATH = "default_bindings.json"


# =============================================================================
# DISPLAY NAME MAPPINGS (Single Source of Truth)
# =============================================================================

# Keyboard key display names
KEY_DISPLAY_NAMES = {
    tcod.event.KeySym.SPACE: "Space",
    tcod.event.KeySym.RETURN: "Enter",
    tcod.event.KeySym.ESCAPE: "ESC",
    tcod.event.KeySym.UP: "↑",
    tcod.event.KeySym.DOWN: "↓",
    tcod.event.KeySym.LEFT: "←",
    tcod.event.KeySym.RIGHT: "→",
    tcod.event.KeySym.KP_ENTER: "Numpad Enter",
    tcod.event.KeySym.KP_1: "Numpad 1",
    tcod.event.KeySym.KP_2: "Numpad 2",
    tcod.event.KeySym.KP_3: "Numpad 3",
    tcod.event.KeySym.KP_4: "Numpad 4",
    tcod.event.KeySym.KP_5: "Numpad 5",
    tcod.event.KeySym.KP_6: "Numpad 6",
    tcod.event.KeySym.KP_7: "Numpad 7",
    tcod.event.KeySym.KP_8: "Numpad 8",
    tcod.event.KeySym.KP_9: "Numpad 9",
    tcod.event.KeySym.PERIOD: ".",
    tcod.event.KeySym.COMMA: ",",
    tcod.event.KeySym.SLASH: "/",
    tcod.event.KeySym.LEFTBRACKET: "[",
    tcod.event.KeySym.RIGHTBRACKET: "]",
    tcod.event.KeySym.PAGEUP: "PgUp",
    tcod.event.KeySym.PAGEDOWN: "PgDn",
    tcod.event.KeySym.TAB: "Tab",
    tcod.event.KeySym.BACKSPACE: "Backspace",
    tcod.event.KeySym.DELETE: "Delete",
    tcod.event.KeySym.HOME: "Home",
    tcod.event.KeySym.END: "End",
    tcod.event.KeySym.N1: "1",
    tcod.event.KeySym.N2: "2",
    tcod.event.KeySym.N3: "3",
    tcod.event.KeySym.N4: "4",
    tcod.event.KeySym.N5: "5",
    tcod.event.KeySym.N6: "6",
    tcod.event.KeySym.N7: "7",
    tcod.event.KeySym.N8: "8",
    tcod.event.KeySym.N9: "9",
    tcod.event.KeySym.N0: "0",
}

# Reserved keys that cannot be rebound
RESERVED_KEYS = {
    tcod.event.KeySym.ESCAPE,  # Always cancel
    tcod.event.KeySym.F12,  # Debug export
}

# Modifier-only keys that should be ignored when capturing key bindings
# Users must press a non-modifier key (e.g., Shift+/ for '?')
MODIFIER_ONLY_KEYS = {
    tcod.event.KeySym.LSHIFT,
    tcod.event.KeySym.RSHIFT,
    tcod.event.KeySym.LCTRL,
    tcod.event.KeySym.RCTRL,
    tcod.event.KeySym.LALT,
    tcod.event.KeySym.RALT,
    tcod.event.KeySym.LGUI,  # Windows/Command key
    tcod.event.KeySym.RGUI,
}


def key_sym_to_display_name(key: tcod.event.KeySym) -> str:
    """
    Convert KeySym to human-readable display name.

    Args:
        key: The key symbol

    Returns:
        Display name (e.g., "W", "↑", "Numpad 8")
    """
    if key in KEY_DISPLAY_NAMES:
        return KEY_DISPLAY_NAMES[key]

    # Default: use the key name (e.g., KeySym.W -> "W")
    name = key.name
    if len(name) == 1:
        return name.upper()
    return name.title()


def key_binding_to_display_name(binding: KeyBinding) -> str:
    """
    Convert KeyBinding to human-readable display name.

    For Shift+key combos that produce common symbols, shows the symbol
    (e.g., "?" instead of "Shift+/"). This matches user expectations.

    Args:
        binding: The key binding (key + modifier)

    Returns:
        Display name (e.g., "W", "?", "Ctrl+S")
    """
    norm_mod = normalize_modifier(binding.modifier)

    # Shift+key combinations that should display as the resulting symbol
    # (US keyboard layout - covers most common roguelike keys)
    if norm_mod == tcod.event.Modifier.SHIFT:
        shift_symbols = {
            tcod.event.KeySym.SLASH: "?",
            tcod.event.KeySym.PERIOD: ">",
            tcod.event.KeySym.COMMA: "<",
            tcod.event.KeySym.N2: "@",
            tcod.event.KeySym.N3: "#",
            tcod.event.KeySym.N1: "!",
            tcod.event.KeySym.SEMICOLON: ":",
            tcod.event.KeySym.APOSTROPHE: '"',
            tcod.event.KeySym.MINUS: "_",
            tcod.event.KeySym.EQUALS: "+",
        }
        if binding.key in shift_symbols:
            return shift_symbols[binding.key]

    key_name = key_sym_to_display_name(binding.key)

    # For other modifiers (Ctrl, Alt, or Ctrl+Shift, etc.), show the combo
    mod_parts = []
    if norm_mod & tcod.event.Modifier.CTRL:
        mod_parts.append("Ctrl")
    if norm_mod & tcod.event.Modifier.ALT:
        mod_parts.append("Alt")
    if norm_mod & tcod.event.Modifier.SHIFT:
        mod_parts.append("Shift")

    if mod_parts:
        return "+".join(mod_parts) + "+" + key_name
    return key_name


def normalize_modifier(mod: int) -> int:
    """
    Normalize modifier flags to canonical form.

    Converts left/right specific modifiers (LSHIFT, RSHIFT) to generic (SHIFT).
    Only keeps Shift, Ctrl, Alt - ignores GUI/Caps/Num modifiers.

    Args:
        mod: Raw modifier flags from event

    Returns:
        Normalized modifier flags
    """
    result = 0
    if mod & (tcod.event.Modifier.SHIFT | tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT):
        result |= tcod.event.Modifier.SHIFT
    if mod & (tcod.event.Modifier.CTRL | tcod.event.Modifier.LCTRL | tcod.event.Modifier.RCTRL):
        result |= tcod.event.Modifier.CTRL
    if mod & (tcod.event.Modifier.ALT | tcod.event.Modifier.LALT | tcod.event.Modifier.RALT):
        result |= tcod.event.Modifier.ALT
    return result


def button_to_display_name(button: int) -> str:
    """
    Convert a ControllerButton value to display name.

    Args:
        button: ControllerButton value

    Returns:
        Human-readable button name (e.g., "A", "LB", "D-Up")
    """
    CB = tcod.sdl.joystick.ControllerButton

    button_names = {
        CB.A: "A",
        CB.B: "B",
        CB.X: "X",
        CB.Y: "Y",
        CB.LEFTSHOULDER: "LB",
        CB.RIGHTSHOULDER: "RB",
        CB.LEFTSTICK: "L3",
        CB.RIGHTSTICK: "R3",
        CB.START: "Start",
        CB.BACK: "Select",
        CB.DPAD_UP: "D-Up",
        CB.DPAD_DOWN: "D-Down",
        CB.DPAD_LEFT: "D-Left",
        CB.DPAD_RIGHT: "D-Right",
        CB.GUIDE: "Guide",
    }

    return button_names.get(button, f"Btn{button}")


def axis_to_display_name(axis: int) -> str:
    """
    Convert a ControllerAxis value to display name.

    Args:
        axis: ControllerAxis value

    Returns:
        Human-readable axis name (e.g., "LT", "RT", "LS-X")
    """
    CA = tcod.sdl.joystick.ControllerAxis

    axis_names = {
        CA.TRIGGERLEFT: "LT",
        CA.TRIGGERRIGHT: "RT",
        CA.LEFTX: "LS-X",
        CA.LEFTY: "LS-Y",
        CA.RIGHTX: "RS-X",
        CA.RIGHTY: "RS-Y",
    }

    return axis_names.get(axis, f"Axis{axis}")


# Reserved gamepad buttons that cannot be rebound
RESERVED_BUTTONS = {
    tcod.sdl.joystick.ControllerButton.GUIDE,  # System button
}


# =============================================================================
# REVERSE MAPPINGS (JSON name -> enum value)
# =============================================================================


def _build_key_name_to_sym() -> dict[str, tcod.event.KeySym]:
    """Build reverse mapping from key names to KeySym values."""
    result = {}
    # Map all KeySym values by name
    for keysym in tcod.event.KeySym:
        result[keysym.name] = keysym
    return result


def _build_button_name_to_value() -> dict[str, int]:
    """Build reverse mapping from button names to ControllerButton values."""
    CB = tcod.sdl.joystick.ControllerButton
    return {
        "A": CB.A,
        "B": CB.B,
        "X": CB.X,
        "Y": CB.Y,
        "LEFTSHOULDER": CB.LEFTSHOULDER,
        "RIGHTSHOULDER": CB.RIGHTSHOULDER,
        "LEFTSTICK": CB.LEFTSTICK,
        "RIGHTSTICK": CB.RIGHTSTICK,
        "START": CB.START,
        "BACK": CB.BACK,
        "DPAD_UP": CB.DPAD_UP,
        "DPAD_DOWN": CB.DPAD_DOWN,
        "DPAD_LEFT": CB.DPAD_LEFT,
        "DPAD_RIGHT": CB.DPAD_RIGHT,
        "GUIDE": CB.GUIDE,
    }


def _build_axis_name_to_value() -> dict[str, int]:
    """Build reverse mapping from axis names to ControllerAxis values."""
    CA = tcod.sdl.joystick.ControllerAxis
    return {
        "TRIGGERLEFT": CA.TRIGGERLEFT,
        "TRIGGERRIGHT": CA.TRIGGERRIGHT,
        "LEFTX": CA.LEFTX,
        "LEFTY": CA.LEFTY,
        "RIGHTX": CA.RIGHTX,
        "RIGHTY": CA.RIGHTY,
    }


def _build_context_name_to_value() -> dict[str, InputContext]:
    """Build reverse mapping from context names to InputContext values."""
    return {ctx.name: ctx for ctx in InputContext}


def _build_action_name_to_value() -> dict[str, InputAction]:
    """Build reverse mapping from action names to InputAction values."""
    return {action.name: action for action in InputAction}


# Build the reverse mappings once at module load
_KEY_NAME_TO_SYM = _build_key_name_to_sym()
_BUTTON_NAME_TO_VALUE = _build_button_name_to_value()
_AXIS_NAME_TO_VALUE = _build_axis_name_to_value()
_CONTEXT_NAME_TO_VALUE = _build_context_name_to_value()
_ACTION_NAME_TO_VALUE = _build_action_name_to_value()


class InputMapper:
    """
    Maps physical inputs to abstract game actions.

    Handles both default and custom bindings, with context-sensitive support.
    Supports modifier keys (Shift, Ctrl, Alt) for keyboard bindings.
    """

    def __init__(self):
        """Initialize input mapper with default mappings."""
        # Default mappings (context-aware)
        # Now uses KeyBinding (key + modifier) instead of just KeySym
        self._default_keyboard_map: dict[KeyBinding, InputAction] = {}
        self._default_gamepad_button_map: dict[tuple[int, InputContext], InputAction] = (
            {}
        )  # (button, context) -> action
        self._default_gamepad_axis_map: dict[tuple[int, InputContext], InputAction] = (
            {}
        )  # (axis, context) -> action (for triggers)

        # Custom user bindings (loaded from settings)
        # Format: {context: {action: [KeyBinding1, KeyBinding2, ...]}}
        self._custom_keyboard_bindings: dict[InputContext, dict[InputAction, list[KeyBinding]]] = {}
        self._custom_gamepad_bindings: dict[InputContext, dict[InputAction, list[int]]] = {}

        # Load defaults from JSON (fail-fast - no fallbacks per CLAUDE.md rules)
        self._load_defaults_from_json()

    def _load_defaults_from_json(self) -> None:
        """
        Load default bindings from default_bindings.json.

        Raises:
            FileNotFoundError: If default_bindings.json is missing
            json.JSONDecodeError: If JSON is malformed
        """
        if not os.path.exists(DEFAULT_BINDINGS_PATH):
            error_msg = f"CRITICAL CONFIG ERROR: {DEFAULT_BINDINGS_PATH} not found"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(DEFAULT_BINDINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Invalid JSON in {DEFAULT_BINDINGS_PATH}"
            logging.error(f"{error_msg}: {e}")
            raise
        except OSError as e:
            error_msg = f"CRITICAL CONFIG ERROR: Could not read {DEFAULT_BINDINGS_PATH}"
            logging.error(f"{error_msg}: {e}")
            raise

        # Load keyboard bindings
        keyboard_data = data.get("keyboard", {})
        for key_name, action_name in keyboard_data.items():
            if key_name.startswith("_"):  # Skip comment fields
                continue

            # Parse key name - may include modifier prefix (e.g., "Shift+SLASH")
            keysym, modifier = self._parse_key_name(key_name)
            action = _ACTION_NAME_TO_VALUE.get(action_name)

            if keysym is not None and action is not None:
                binding = KeyBinding(keysym, modifier)
                self._default_keyboard_map[binding] = action
            else:
                if keysym is None:
                    logging.warning(f"Unknown key name in JSON: {key_name}")
                if action is None:
                    logging.warning(f"Unknown action name in JSON: {action_name}")

        # Load gamepad button bindings
        gamepad_data = data.get("gamepad", {})
        buttons_data = gamepad_data.get("buttons", {})
        for context_name, buttons in buttons_data.items():
            context = _CONTEXT_NAME_TO_VALUE.get(context_name)
            if context is None:
                logging.warning(f"Unknown context name in JSON: {context_name}")
                continue
            for button_name, action_name in buttons.items():
                button = _BUTTON_NAME_TO_VALUE.get(button_name)
                action = _ACTION_NAME_TO_VALUE.get(action_name)
                if button is not None and action is not None:
                    self._default_gamepad_button_map[(button, context)] = action
                else:
                    if button is None:
                        logging.warning(f"Unknown button name in JSON: {button_name}")
                    if action is None:
                        logging.warning(f"Unknown action name in JSON: {action_name}")

        # Load gamepad axis bindings
        axes_data = gamepad_data.get("axes", {})
        for context_name, axes in axes_data.items():
            context = _CONTEXT_NAME_TO_VALUE.get(context_name)
            if context is None:
                logging.warning(f"Unknown context name in JSON: {context_name}")
                continue
            for axis_name, action_name in axes.items():
                axis = _AXIS_NAME_TO_VALUE.get(axis_name)
                action = _ACTION_NAME_TO_VALUE.get(action_name)
                if axis is not None and action is not None:
                    self._default_gamepad_axis_map[(axis, context)] = action
                else:
                    if axis is None:
                        logging.warning(f"Unknown axis name in JSON: {axis_name}")
                    if action is None:
                        logging.warning(f"Unknown action name in JSON: {action_name}")

        logging.info(f"Loaded defaults from {DEFAULT_BINDINGS_PATH}")

    def _parse_key_name(self, key_name: str) -> tuple[tcod.event.KeySym | None, int]:
        """
        Parse a key name string that may include modifier prefixes.

        Args:
            key_name: Key name like "W", "Shift+SLASH", "Ctrl+S"

        Returns:
            Tuple of (KeySym, modifier_flags)
        """
        modifier = 0
        parts = key_name.split("+")

        # Last part is the key, everything before is modifiers
        key_part = parts[-1]
        mod_parts = parts[:-1]

        for mod in mod_parts:
            mod_upper = mod.upper()
            if mod_upper == "SHIFT":
                modifier |= tcod.event.Modifier.SHIFT
            elif mod_upper == "CTRL":
                modifier |= tcod.event.Modifier.CTRL
            elif mod_upper == "ALT":
                modifier |= tcod.event.Modifier.ALT

        keysym = _KEY_NAME_TO_SYM.get(key_part)
        return keysym, modifier

    def get_action_for_key(
        self,
        key: tcod.event.KeySym,
        context: InputContext = InputContext.GAMEPLAY,
        modifier: int = 0,
    ) -> InputAction | None:
        """
        Get the action for a keyboard key in the given context.

        Args:
            key: The key that was pressed
            context: The current game state context
            modifier: Modifier flags from the event (Shift, Ctrl, Alt)

        Returns:
            The action to perform, or None if no mapping exists
        """
        # Normalize modifier to canonical form
        norm_mod = normalize_modifier(modifier)

        # Check custom bindings first
        if context in self._custom_keyboard_bindings:
            for action, bindings in self._custom_keyboard_bindings[context].items():
                for binding in bindings:
                    if binding.matches(key, norm_mod):
                        return action

        # Fall back to default mapping
        # Check each binding for a match (accounts for modifiers)
        for binding, action in self._default_keyboard_map.items():
            if binding.matches(key, norm_mod):
                return action

        return None

    def get_action_for_gamepad_button(
        self, button: int, context: InputContext = InputContext.GAMEPLAY
    ) -> InputAction | None:
        """
        Get the action for a gamepad button in the given context.

        Args:
            button: The button that was pressed (ControllerButton enum value)
            context: The current game state context

        Returns:
            The action to perform, or None if no mapping exists
        """
        # Check custom bindings first (if implemented)
        if context in self._custom_gamepad_bindings:
            for action, buttons in self._custom_gamepad_bindings[context].items():
                if button in buttons:
                    return action

        # Fall back to default mapping (context-aware)
        return self._default_gamepad_button_map.get((button, context))

    def get_action_for_gamepad_axis(
        self, axis: int, context: InputContext = InputContext.GAMEPLAY
    ) -> InputAction | None:
        """
        Get the action for a gamepad axis (trigger) in the given context.

        Args:
            axis: The axis that was activated (ControllerAxis enum value)
            context: The current game state context

        Returns:
            The action to perform, or None if no mapping exists
        """
        # Note: Axis bindings (triggers LT/RT) use defaults only.
        # Custom axis binding not implemented - standard controller layout assumed.

        # Use default mapping (context-aware)
        return self._default_gamepad_axis_map.get((axis, context))

    def get_movement_delta(self, action: InputAction) -> tuple[int, int] | None:
        """
        Convert a movement action to (dx, dy) delta.

        Args:
            action: The movement action

        Returns:
            (dx, dy) tuple, or None if not a movement action
        """
        movement_map = {
            InputAction.MOVE_NORTH: (0, -1),
            InputAction.MOVE_SOUTH: (0, 1),
            InputAction.MOVE_EAST: (1, 0),
            InputAction.MOVE_WEST: (-1, 0),
            InputAction.MOVE_NORTHEAST: (1, -1),
            InputAction.MOVE_NORTHWEST: (-1, -1),
            InputAction.MOVE_SOUTHEAST: (1, 1),
            InputAction.MOVE_SOUTHWEST: (-1, 1),
        }
        return movement_map.get(action)

    def is_movement_action(self, action: InputAction) -> bool:
        """Check if an action is a movement action."""
        return action in [
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST,
            InputAction.MOVE_WEST,
            InputAction.MOVE_NORTHEAST,
            InputAction.MOVE_NORTHWEST,
            InputAction.MOVE_SOUTHEAST,
            InputAction.MOVE_SOUTHWEST,
        ]

    def get_movement_key_names(self) -> list[str]:
        """
        Get list of key names bound to movement actions.

        Used by help system to detect which key groups are configured
        (Arrows, WASD/QEZC, Numpad).

        Returns:
            List of raw key names (e.g., ["W", "UP", "KP_8"])
        """
        movement_actions = {
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST,
            InputAction.MOVE_WEST,
            InputAction.MOVE_NORTHEAST,
            InputAction.MOVE_NORTHWEST,
            InputAction.MOVE_SOUTHEAST,
            InputAction.MOVE_SOUTHWEST,
        }
        key_names = []
        for binding, action in self._default_keyboard_map.items():
            if action in movement_actions:
                key_names.append(binding.key.name)
        return key_names

    def get_default_keys_for_action(self, action: InputAction) -> list[str]:
        """
        Get list of default key names for an action (for UI display).

        Args:
            action: The action to query

        Returns:
            List of key names (e.g., ["W", "Up", "Numpad8", "Shift+/"])
        """
        keys = []
        for binding, mapped_action in self._default_keyboard_map.items():
            if mapped_action == action:
                keys.append(key_binding_to_display_name(binding))
        return keys

    def get_all_keys_for_action(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> list[str]:
        """
        Get all key names for an action (custom bindings first, then defaults).

        Custom bindings are listed first so they appear as primary in help text
        when users remap keys.

        Args:
            action: The action to query
            context: The input context

        Returns:
            List of key names (e.g., ["T", "W", "Up", "Numpad8", "Shift+/"])
        """
        keys = []

        # Add custom bindings first (user preference takes priority)
        if context in self._custom_keyboard_bindings:
            if action in self._custom_keyboard_bindings[context]:
                for binding in self._custom_keyboard_bindings[context][action]:
                    display_name = key_binding_to_display_name(binding)
                    if display_name not in keys:
                        keys.append(display_name)

        # Add default bindings after custom
        for binding, mapped_action in self._default_keyboard_map.items():
            if mapped_action == action:
                display_name = key_binding_to_display_name(binding)
                if display_name not in keys:
                    keys.append(display_name)

        return keys

    def has_custom_keyboard_bindings(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> bool:
        """Check if action has any custom keyboard bindings."""
        if context in self._custom_keyboard_bindings:
            return action in self._custom_keyboard_bindings[context]
        return False

    def get_all_buttons_for_action(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> list[int]:
        """
        Get all gamepad buttons for an action (custom bindings first, then defaults).

        Custom bindings are listed first so they appear as primary in help text
        when users remap buttons.

        Args:
            action: The action to query
            context: The input context

        Returns:
            List of ControllerButton values
        """
        buttons = []

        # Add custom bindings first (user preference takes priority)
        if context in self._custom_gamepad_bindings:
            if action in self._custom_gamepad_bindings[context]:
                for button in self._custom_gamepad_bindings[context][action]:
                    if button not in buttons:
                        buttons.append(button)

        # Add default bindings after custom
        for (button, ctx), mapped_action in self._default_gamepad_button_map.items():
            if mapped_action == action and ctx == context:
                if button not in buttons:
                    buttons.append(button)

        return buttons

    def has_custom_gamepad_bindings(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> bool:
        """Check if action has any custom gamepad bindings."""
        if context in self._custom_gamepad_bindings:
            return action in self._custom_gamepad_bindings[context]
        return False

    def get_default_buttons_for_action(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> list[int]:
        """
        Get list of default gamepad buttons for an action in a context.

        Args:
            action: The action to query
            context: The input context

        Returns:
            List of ControllerButton values
        """
        buttons = []
        for (button, ctx), mapped_action in self._default_gamepad_button_map.items():
            if mapped_action == action and ctx == context:
                buttons.append(button)
        return buttons

    def get_default_axes_for_action(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> list[int]:
        """
        Get list of default gamepad axes (triggers) for an action in a context.

        Args:
            action: The action to query
            context: The input context

        Returns:
            List of ControllerAxis values
        """
        axes = []
        for (axis, ctx), mapped_action in self._default_gamepad_axis_map.items():
            if mapped_action == action and ctx == context:
                axes.append(axis)
        return axes

    def get_gamepad_conflicts(
        self, action: InputAction, button: int, context: InputContext
    ) -> list[InputAction]:
        """
        Check for gamepad binding conflicts in a specific context.

        Args:
            action: The action to bind
            button: The button to bind it to
            context: The input context

        Returns:
            List of actions currently bound to this button in this context
        """
        conflicts = []
        for (existing_button, ctx), existing_action in self._default_gamepad_button_map.items():
            if existing_button == button and ctx == context and existing_action != action:
                conflicts.append(existing_action)

        # Also check custom bindings
        if context in self._custom_gamepad_bindings:
            for existing_action, buttons in self._custom_gamepad_bindings[context].items():
                if button in buttons and existing_action != action:
                    if existing_action not in conflicts:
                        conflicts.append(existing_action)

        return conflicts

    def _key_sym_to_display_name(self, key: tcod.event.KeySym) -> str:
        """Convert KeySym to human-readable display name. Delegates to module-level function."""
        return key_sym_to_display_name(key)

    def load_custom_bindings(self, keyboard_bindings: dict, gamepad_bindings: dict):
        """
        Load custom bindings from settings.

        Args:
            keyboard_bindings: Custom keyboard bindings from user_settings.json
            gamepad_bindings: Custom gamepad bindings from user_settings.json

        Supports two formats:
        Old flat format (backwards compatible):
            {"MOVE_NORTH": ["W", "UP"], "WAIT": ["SPACE"]}

        New per-context format:
            {"GAMEPLAY": {"WAIT": ["A"]}, "INVENTORY": {"CONFIRM": ["A"]}}
        """
        # Clear existing custom bindings
        self._custom_keyboard_bindings.clear()
        self._custom_gamepad_bindings.clear()

        # Load keyboard bindings
        if keyboard_bindings and isinstance(keyboard_bindings, dict):
            self._load_bindings_dict(
                keyboard_bindings,
                self._custom_keyboard_bindings,
                self._key_name_to_binding,
                "keyboard",
            )

        # Load gamepad bindings
        if gamepad_bindings and isinstance(gamepad_bindings, dict):
            self._load_bindings_dict(
                gamepad_bindings,
                self._custom_gamepad_bindings,
                self._button_name_to_value,
                "gamepad",
            )

    def _load_bindings_dict(
        self, bindings_data: dict, target_dict: dict, name_converter, binding_type: str
    ):
        """
        Load bindings from a dict, handling both flat and per-context formats.

        Args:
            bindings_data: The raw bindings dict from settings
            target_dict: Where to store the bindings (keyboard or gamepad)
            name_converter: Function to convert string names to values
            binding_type: "keyboard" or "gamepad" for logging
        """
        # Detect format: if first value is a dict, it's per-context format
        first_value = next(iter(bindings_data.values()), None) if bindings_data else None
        is_per_context = isinstance(first_value, dict)

        if is_per_context:
            # New per-context format: {"GAMEPLAY": {"WAIT": ["A"]}, ...}
            for context_name, action_bindings in bindings_data.items():
                try:
                    context = InputContext[context_name]
                except KeyError:
                    logging.warning(f"Unknown context in {binding_type} bindings: {context_name}")
                    continue

                if context not in target_dict:
                    target_dict[context] = {}

                for action_name, input_names in action_bindings.items():
                    try:
                        action = InputAction[action_name]
                        inputs = []
                        for input_name in input_names:
                            value = name_converter(input_name)
                            if value is not None:
                                inputs.append(value)
                        if inputs:
                            target_dict[context][action] = inputs
                    except (KeyError, ValueError) as e:
                        logging.warning(f"Invalid {binding_type} binding: {action_name} -> {e}")

            total = sum(len(actions) for actions in target_dict.values())
            logging.debug(
                f"InputMapper: Loaded {total} custom {binding_type} bindings (per-context)"
            )
        else:
            # Old flat format: {"WAIT": ["A"], ...} - load into GAMEPLAY context
            if InputContext.GAMEPLAY not in target_dict:
                target_dict[InputContext.GAMEPLAY] = {}

            for action_name, input_names in bindings_data.items():
                try:
                    action = InputAction[action_name]
                    inputs = []
                    for input_name in input_names:
                        value = name_converter(input_name)
                        if value is not None:
                            inputs.append(value)
                    if inputs:
                        target_dict[InputContext.GAMEPLAY][action] = inputs
                except (KeyError, ValueError) as e:
                    logging.warning(f"Invalid {binding_type} binding: {action_name} -> {e}")

            logging.debug(
                f"InputMapper: Loaded {len(target_dict.get(InputContext.GAMEPLAY, {}))} "
                f"custom {binding_type} bindings (legacy format)"
            )

    def save_custom_bindings(self) -> tuple[dict, dict]:
        """
        Save custom bindings to settings.

        Returns:
            (keyboard_bindings, gamepad_bindings) tuple for user_settings.json

        Format (per-context):
            {
                "GAMEPLAY": {"WAIT": ["A"], ...},
                "INVENTORY": {"CONFIRM": ["A"], ...}
            }
        """
        keyboard_bindings = {}
        gamepad_bindings = {}

        # Save keyboard bindings from all contexts
        for context, action_bindings in self._custom_keyboard_bindings.items():
            context_bindings = {}
            for action, bindings in action_bindings.items():
                binding_names = [key_binding_to_display_name(b) for b in bindings]
                context_bindings[action.name] = binding_names
            if context_bindings:
                keyboard_bindings[context.name] = context_bindings

        # Save gamepad bindings from all contexts
        for context, action_bindings in self._custom_gamepad_bindings.items():
            context_bindings = {}
            for action, buttons in action_bindings.items():
                button_names = [self._button_value_to_name(b) for b in buttons]
                context_bindings[action.name] = button_names
            if context_bindings:
                gamepad_bindings[context.name] = context_bindings

        return (keyboard_bindings, gamepad_bindings)

    def _button_name_to_value(self, button_name: str) -> int | None:
        """
        Convert a button display name to ControllerButton value.

        Args:
            button_name: Human-readable button name (e.g., "A", "LB", "D-Up")

        Returns:
            ControllerButton value, or None if not found
        """
        button_name = button_name.strip()
        CB = tcod.sdl.joystick.ControllerButton

        name_to_button = {
            "A": CB.A,
            "B": CB.B,
            "X": CB.X,
            "Y": CB.Y,
            "LB": CB.LEFTSHOULDER,
            "RB": CB.RIGHTSHOULDER,
            "L3": CB.LEFTSTICK,
            "R3": CB.RIGHTSTICK,
            "Start": CB.START,
            "Select": CB.BACK,
            "D-Up": CB.DPAD_UP,
            "D-Down": CB.DPAD_DOWN,
            "D-Left": CB.DPAD_LEFT,
            "D-Right": CB.DPAD_RIGHT,
            "Guide": CB.GUIDE,
        }

        if button_name in name_to_button:
            return name_to_button[button_name]

        logging.warning(f"Unknown button name: {button_name}")
        return None

    def _button_value_to_name(self, button: int) -> str:
        """Convert a ControllerButton value to display name. Delegates to module-level function."""
        return button_to_display_name(button)

    def _key_name_to_binding(self, key_name: str) -> KeyBinding | None:
        """
        Convert a key name string to KeyBinding.

        Supports modifier prefixes like "Shift+/", "Ctrl+S".

        Args:
            key_name: Human-readable key name (e.g., "W", "Space", "Shift+/")

        Returns:
            KeyBinding with key and modifier, or None if not found
        """
        # Normalize input
        key_name = key_name.strip()

        # Symbol-to-binding mapping (US keyboard shifted symbols)
        # These are saved as symbols but need to load as Shift+key
        symbol_bindings = {
            "?": (tcod.event.KeySym.SLASH, tcod.event.Modifier.SHIFT),
            ">": (tcod.event.KeySym.PERIOD, tcod.event.Modifier.SHIFT),
            "<": (tcod.event.KeySym.COMMA, tcod.event.Modifier.SHIFT),
            "@": (tcod.event.KeySym.N2, tcod.event.Modifier.SHIFT),
            "#": (tcod.event.KeySym.N3, tcod.event.Modifier.SHIFT),
            "!": (tcod.event.KeySym.N1, tcod.event.Modifier.SHIFT),
            ":": (tcod.event.KeySym.SEMICOLON, tcod.event.Modifier.SHIFT),
            '"': (tcod.event.KeySym.APOSTROPHE, tcod.event.Modifier.SHIFT),
            "_": (tcod.event.KeySym.MINUS, tcod.event.Modifier.SHIFT),
            "+": (tcod.event.KeySym.EQUALS, tcod.event.Modifier.SHIFT),
        }
        if key_name in symbol_bindings:
            keysym, mod = symbol_bindings[key_name]
            return KeyBinding(keysym, mod)

        # Parse modifiers from the key name (e.g., "Shift+/" -> modifier=SHIFT, key="/")
        modifier = 0
        if "+" in key_name:
            parts = key_name.split("+")
            key_part = parts[-1]
            for mod_part in parts[:-1]:
                mod_upper = mod_part.upper()
                if mod_upper == "SHIFT":
                    modifier |= tcod.event.Modifier.SHIFT
                elif mod_upper == "CTRL":
                    modifier |= tcod.event.Modifier.CTRL
                elif mod_upper == "ALT":
                    modifier |= tcod.event.Modifier.ALT
        else:
            key_part = key_name

        # Special cases for display names
        name_to_sym = {
            "Space": tcod.event.KeySym.SPACE,
            "Enter": tcod.event.KeySym.RETURN,
            "ESC": tcod.event.KeySym.ESCAPE,
            "Up": tcod.event.KeySym.UP,
            "Down": tcod.event.KeySym.DOWN,
            "Left": tcod.event.KeySym.LEFT,
            "Right": tcod.event.KeySym.RIGHT,
            "Numpad Enter": tcod.event.KeySym.KP_ENTER,
            "Numpad 1": tcod.event.KeySym.KP_1,
            "Numpad 2": tcod.event.KeySym.KP_2,
            "Numpad 3": tcod.event.KeySym.KP_3,
            "Numpad 4": tcod.event.KeySym.KP_4,
            "Numpad 5": tcod.event.KeySym.KP_5,
            "Numpad 6": tcod.event.KeySym.KP_6,
            "Numpad 7": tcod.event.KeySym.KP_7,
            "Numpad 8": tcod.event.KeySym.KP_8,
            "Numpad 9": tcod.event.KeySym.KP_9,
            ".": tcod.event.KeySym.PERIOD,
            ",": tcod.event.KeySym.COMMA,
            "[": tcod.event.KeySym.LEFTBRACKET,
            "]": tcod.event.KeySym.RIGHTBRACKET,
            "/": tcod.event.KeySym.SLASH,
            "PgUp": tcod.event.KeySym.PAGEUP,
            "PgDn": tcod.event.KeySym.PAGEDOWN,
            "Tab": tcod.event.KeySym.TAB,
            "Backspace": tcod.event.KeySym.BACKSPACE,
            "Delete": tcod.event.KeySym.DELETE,
            "Home": tcod.event.KeySym.HOME,
            "End": tcod.event.KeySym.END,
            # Arrow key unicode symbols
            "↑": tcod.event.KeySym.UP,
            "↓": tcod.event.KeySym.DOWN,
            "←": tcod.event.KeySym.LEFT,
            "→": tcod.event.KeySym.RIGHT,
        }

        keysym = None
        if key_part in name_to_sym:
            keysym = name_to_sym[key_part]
        elif len(key_part) == 1:
            upper = key_part.upper()
            if upper.isalpha():
                keysym = getattr(tcod.event.KeySym, upper, None)
            elif upper.isdigit():
                keysym = getattr(tcod.event.KeySym, f"N{upper}", None)
        else:
            # Try direct attribute lookup (e.g., "W" -> KeySym.W)
            try:
                keysym = getattr(tcod.event.KeySym, key_part.upper())
            except AttributeError:
                pass

        if keysym is None:
            logging.warning(f"Unknown key name: {key_name}")
            return None

        return KeyBinding(keysym, modifier)

    def get_conflicts(
        self, action: InputAction, key: tcod.event.KeySym, modifier: int = 0
    ) -> list[InputAction]:
        """
        Check for binding conflicts (for remapping UI).

        Args:
            action: The action to bind
            key: The key to bind it to
            modifier: Modifier flags (Shift, Ctrl, Alt)

        Returns:
            List of actions currently bound to this key+modifier combo
        """
        conflicts = []
        binding = KeyBinding(key, normalize_modifier(modifier))

        # Check default bindings
        for existing_binding, existing_action in self._default_keyboard_map.items():
            if existing_binding == binding and existing_action != action:
                conflicts.append(existing_action)

        # Check custom bindings (all contexts)
        for context, action_bindings in self._custom_keyboard_bindings.items():
            for existing_action, bindings in action_bindings.items():
                if binding in bindings and existing_action != action:
                    if existing_action not in conflicts:
                        conflicts.append(existing_action)

        return conflicts

    def reset_to_defaults(self, input_type: str = "keyboard"):
        """
        Reset bindings to defaults.

        Args:
            input_type: "keyboard" or "gamepad"
        """
        if input_type == "keyboard":
            self._custom_keyboard_bindings.clear()
            logging.info("InputMapper: Reset keyboard bindings to defaults")
        elif input_type == "gamepad":
            self._custom_gamepad_bindings.clear()
            logging.info("InputMapper: Reset gamepad bindings to defaults")

    # =========================================================================
    # KEYBOARD BINDING MODIFICATION (Phase 4)
    # =========================================================================

    def add_keyboard_binding(
        self,
        action: InputAction,
        key: tcod.event.KeySym,
        context: InputContext = InputContext.GAMEPLAY,
        modifier: int = 0,
    ) -> bool:
        """
        Add a keyboard binding for an action.

        Args:
            action: The action to bind
            key: The key to bind it to
            context: The context for this binding (default: GAMEPLAY)
            modifier: Modifier flags (Shift, Ctrl, Alt)

        Returns:
            True if binding was added, False if key is reserved
        """
        # Reserved keys cannot be bound
        reserved_keys = {tcod.event.KeySym.ESCAPE, tcod.event.KeySym.F12}
        if key in reserved_keys:
            logging.warning(f"Cannot bind reserved key {key.name} to {action.name}")
            return False

        binding = KeyBinding(key, normalize_modifier(modifier))

        # Ensure context exists in custom bindings
        if context not in self._custom_keyboard_bindings:
            self._custom_keyboard_bindings[context] = {}

        # Ensure action exists in context
        if action not in self._custom_keyboard_bindings[context]:
            self._custom_keyboard_bindings[context][action] = []

        # Add binding if not already bound
        if binding not in self._custom_keyboard_bindings[context][action]:
            self._custom_keyboard_bindings[context][action].append(binding)
            logging.info(
                f"Added keyboard binding: {key_binding_to_display_name(binding)} -> {action.name} (context: {context.name})"
            )

        return True

    def remove_keyboard_binding(
        self,
        action: InputAction,
        key: tcod.event.KeySym,
        context: InputContext = InputContext.GAMEPLAY,
        modifier: int = 0,
    ) -> bool:
        """
        Remove a specific keyboard binding from an action.

        Args:
            action: The action to unbind from
            key: The key to remove
            context: The context for this binding
            modifier: Modifier flags (Shift, Ctrl, Alt)

        Returns:
            True if binding was removed, False if it didn't exist
        """
        if context not in self._custom_keyboard_bindings:
            return False

        if action not in self._custom_keyboard_bindings[context]:
            return False

        binding = KeyBinding(key, normalize_modifier(modifier))
        if binding in self._custom_keyboard_bindings[context][action]:
            self._custom_keyboard_bindings[context][action].remove(binding)
            logging.info(
                f"Removed keyboard binding: {key_binding_to_display_name(binding)} from {action.name} (context: {context.name})"
            )

            # Clean up empty lists
            if not self._custom_keyboard_bindings[context][action]:
                del self._custom_keyboard_bindings[context][action]
            if not self._custom_keyboard_bindings[context]:
                del self._custom_keyboard_bindings[context]

            return True

        return False

    def clear_keyboard_bindings(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> None:
        """
        Clear all keyboard bindings for an action in a context.

        Args:
            action: The action to clear bindings for
            context: The context to clear bindings in
        """
        if context in self._custom_keyboard_bindings:
            if action in self._custom_keyboard_bindings[context]:
                del self._custom_keyboard_bindings[context][action]
                logging.info(
                    f"Cleared all keyboard bindings for {action.name} (context: {context.name})"
                )

                # Clean up empty context
                if not self._custom_keyboard_bindings[context]:
                    del self._custom_keyboard_bindings[context]

    def replace_keyboard_binding(
        self,
        action: InputAction,
        key: tcod.event.KeySym,
        context: InputContext = InputContext.GAMEPLAY,
        modifier: int = 0,
    ) -> list[InputAction]:
        """
        Replace existing bindings with a new one (removes conflicts).

        Args:
            action: The action to bind
            key: The key to bind it to
            context: The context for this binding
            modifier: Modifier flags (Shift, Ctrl, Alt)

        Returns:
            List of actions that had this key removed
        """
        removed_from = []
        binding = KeyBinding(key, normalize_modifier(modifier))

        # First, remove this binding from any other action in this context
        if context in self._custom_keyboard_bindings:
            for existing_action, bindings in list(self._custom_keyboard_bindings[context].items()):
                if existing_action != action and binding in bindings:
                    bindings.remove(binding)
                    removed_from.append(existing_action)
                    # Clean up empty list
                    if not bindings:
                        del self._custom_keyboard_bindings[context][existing_action]

        # Also check defaults and note conflicts (for UI feedback)
        for existing_binding, existing_action in self._default_keyboard_map.items():
            if existing_binding == binding and existing_action != action:
                if existing_action not in removed_from:
                    removed_from.append(existing_action)

        # Now add the binding
        self.add_keyboard_binding(action, key, context, modifier)

        return removed_from

    # =========================================================================
    # GAMEPAD BINDING MODIFICATION (Phase 5)
    # =========================================================================

    def add_gamepad_binding(
        self, action: InputAction, button: int, context: InputContext = InputContext.GAMEPLAY
    ) -> bool:
        """
        Add a gamepad button binding for an action.

        Args:
            action: The action to bind
            button: The ControllerButton value to bind
            context: The context for this binding

        Returns:
            True if binding was added, False if button is reserved
        """
        # Reserved buttons (e.g., Guide button)
        try:
            CB = tcod.sdl.joystick.ControllerButton
            reserved_buttons = {CB.GUIDE}
            if button in reserved_buttons:
                logging.warning(f"Cannot bind reserved button to {action.name}")
                return False
        except Exception as e:
            # SDL not available (e.g., headless testing) - skip reservation check
            logging.debug(f"Skipping reserved button check (SDL unavailable): {e}")

        # Ensure context exists
        if context not in self._custom_gamepad_bindings:
            self._custom_gamepad_bindings[context] = {}

        # Ensure action exists
        if action not in self._custom_gamepad_bindings[context]:
            self._custom_gamepad_bindings[context][action] = []

        # Add button if not already bound
        if button not in self._custom_gamepad_bindings[context][action]:
            self._custom_gamepad_bindings[context][action].append(button)
            logging.info(
                f"Added gamepad binding: button {button} -> {action.name} (context: {context.name})"
            )

        return True

    def remove_gamepad_binding(
        self, action: InputAction, button: int, context: InputContext = InputContext.GAMEPLAY
    ) -> bool:
        """
        Remove a specific gamepad binding from an action.

        Args:
            action: The action to unbind from
            button: The button to remove
            context: The context for this binding

        Returns:
            True if binding was removed, False if it didn't exist
        """
        if context not in self._custom_gamepad_bindings:
            return False

        if action not in self._custom_gamepad_bindings[context]:
            return False

        if button in self._custom_gamepad_bindings[context][action]:
            self._custom_gamepad_bindings[context][action].remove(button)
            logging.info(
                f"Removed gamepad binding: button {button} from {action.name} (context: {context.name})"
            )

            # Clean up empty lists
            if not self._custom_gamepad_bindings[context][action]:
                del self._custom_gamepad_bindings[context][action]
            if not self._custom_gamepad_bindings[context]:
                del self._custom_gamepad_bindings[context]

            return True

        return False

    def clear_gamepad_bindings(
        self, action: InputAction, context: InputContext = InputContext.GAMEPLAY
    ) -> None:
        """
        Clear all gamepad bindings for an action in a context.

        Args:
            action: The action to clear bindings for
            context: The context to clear bindings in
        """
        if context in self._custom_gamepad_bindings:
            if action in self._custom_gamepad_bindings[context]:
                del self._custom_gamepad_bindings[context][action]
                logging.info(
                    f"Cleared all gamepad bindings for {action.name} (context: {context.name})"
                )

                # Clean up empty context
                if not self._custom_gamepad_bindings[context]:
                    del self._custom_gamepad_bindings[context]

    def replace_gamepad_binding(
        self, action: InputAction, button: int, context: InputContext = InputContext.GAMEPLAY
    ) -> list[InputAction]:
        """
        Replace existing bindings with a new one (removes conflicts).

        Args:
            action: The action to bind
            button: The button to bind it to
            context: The context for this binding

        Returns:
            List of actions that had this button removed
        """
        removed_from = []

        # First, remove this button from any other action in this context
        if context in self._custom_gamepad_bindings:
            for existing_action, buttons in list(self._custom_gamepad_bindings[context].items()):
                if existing_action != action and button in buttons:
                    buttons.remove(button)
                    removed_from.append(existing_action)
                    # Clean up empty list
                    if not buttons:
                        del self._custom_gamepad_bindings[context][existing_action]

        # Also note conflicts with defaults (for UI feedback)
        for (existing_button, ctx), existing_action in self._default_gamepad_button_map.items():
            if existing_button == button and ctx == context and existing_action != action:
                if existing_action not in removed_from:
                    removed_from.append(existing_action)

        # Now add the binding
        self.add_gamepad_binding(action, button, context)

        return removed_from

    # =========================================================================
    # DYNAMIC HELP TEXT (for mini-help at bottom of screens)
    # =========================================================================

    def get_key_hint(self, action: InputAction, max_keys: int = 1) -> str:
        """
        Get keyboard key hint for an action (for help text display).

        Returns the first (primary) key binding for the action, or multiple
        separated by "/" if max_keys > 1.

        Args:
            action: The action to get hint for
            max_keys: Maximum number of keys to show (default 1 = primary only)

        Returns:
            Display string like "Enter" or "Enter/Space"
        """
        keys = self.get_all_keys_for_action(action, InputContext.GAMEPLAY)

        # Fall back to default if no custom bindings
        if not keys:
            keys = self.get_default_keys_for_action(action)

        if not keys:
            return "?"

        # Return requested number of keys
        return "/".join(keys[:max_keys])

    def get_button_hint(self, action: InputAction, context: InputContext) -> str:
        """
        Get gamepad button hint for an action (for help text display).

        Returns the first (primary) button binding for the action in the
        given context.

        Args:
            action: The action to get hint for
            context: Input context (affects button mappings)

        Returns:
            Display string like "A" or "RT"
        """
        buttons = self.get_all_buttons_for_action(action, context)

        # Fall back to default if no custom bindings
        if not buttons:
            buttons = self.get_default_buttons_for_action(action, context)

        if not buttons:
            # Check triggers/axes too
            axes = self.get_default_axes_for_action(action, context)
            if axes:
                return axis_to_display_name(axes[0])
            return "?"

        return self._button_value_to_name(buttons[0])

    def get_combined_hint(
        self,
        action: InputAction,
        context: InputContext,
        separator: str = "/",
        keyboard_first: bool = True,
    ) -> str:
        """
        Get combined keyboard + gamepad hint for an action.

        Args:
            action: The action to get hint for
            context: Input context (affects button mappings)
            separator: String to separate keyboard and gamepad hints
            keyboard_first: If True, show keyboard first (e.g., "Enter/A")

        Returns:
            Display string like "Enter/A" or "A/Enter"
        """
        key_hint = self.get_key_hint(action)
        button_hint = self.get_button_hint(action, context)

        if key_hint == "?" and button_hint == "?":
            return "?"

        if key_hint == "?":
            return button_hint
        if button_hint == "?":
            return key_hint

        if keyboard_first:
            return f"{key_hint}{separator}{button_hint}"
        return f"{button_hint}{separator}{key_hint}"

    def get_nav_hint(self, context: InputContext, use_arrows: bool = True) -> str:
        """
        Get navigation hint (Up/Down or ↕ combined with D-Pad).

        Args:
            context: Input context
            use_arrows: If True, use arrow symbols (↕), else use "Up/Dn"

        Returns:
            Display string like "↕/D-Pad" or "Up/Dn/D-Pad"
        """
        if use_arrows:
            return "↕/D-Pad"
        return "Up/Dn/D-Pad"

    def format_help_string(
        self, template: str, context: InputContext, show_gamepad: bool = True
    ) -> str:
        """
        Format a help string template with current bindings.

        Replaces placeholders like {CONFIRM}, {CANCEL}, {NAV} with actual
        key/button hints.

        Args:
            template: String with placeholders like "Select: {CONFIRM} Back: {CANCEL}"
            context: Input context
            show_gamepad: If True, show combined hints; else keyboard only

        Returns:
            Formatted string with actual bindings

        Supported placeholders:
            {NAV} - Navigation (↕/D-Pad)
            {CONFIRM} - Confirm/Select action
            {CANCEL} - Cancel/Back action
            {PAGE_UP} - Page up
            {PAGE_DOWN} - Page down
            {LEFT} - Navigate left
            {RIGHT} - Navigate right
        """
        result = template

        # Map of placeholder to action
        action_map = {
            "{CONFIRM}": InputAction.CONFIRM,
            "{CANCEL}": InputAction.CANCEL,
            "{PAGE_UP}": InputAction.NAVIGATE_PAGE_UP,
            "{PAGE_DOWN}": InputAction.NAVIGATE_PAGE_DOWN,
            "{LEFT}": InputAction.NAVIGATE_LEFT,
            "{RIGHT}": InputAction.NAVIGATE_RIGHT,
            "{UP}": InputAction.NAVIGATE_UP,
            "{DOWN}": InputAction.NAVIGATE_DOWN,
        }

        # Replace action placeholders
        for placeholder, action in action_map.items():
            if placeholder in result:
                if show_gamepad:
                    hint = self.get_combined_hint(action, context)
                else:
                    hint = self.get_key_hint(action)
                result = result.replace(placeholder, hint)

        # Special placeholder for navigation
        if "{NAV}" in result:
            result = result.replace("{NAV}", self.get_nav_hint(context))

        return result
