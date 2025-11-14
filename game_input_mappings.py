"""
game_input_mappings.py - Input Mapping System

Manages the bidirectional mapping between physical inputs (keyboard keys, gamepad buttons)
and abstract game actions. Supports custom remapping and context-sensitive bindings.

Architecture:
- Default mappings for keyboard and gamepad (hardcoded)
- Custom user bindings (loaded from settings, override defaults)
- Context-aware lookups (same key can do different things in different states)
- Conflict detection for remapping UI
"""

import logging

import tcod.event

from game_input_actions import InputAction, InputContext


class InputMapper:
    """
    Maps physical inputs to abstract game actions.

    Handles both default and custom bindings, with context-sensitive support.
    """

    def __init__(self):
        """Initialize input mapper with default mappings."""
        # Default mappings (context-agnostic for now - context handling added later)
        self._default_keyboard_map: dict[tcod.event.KeySym, InputAction] = {}
        self._default_gamepad_button_map: dict[int, InputAction] = (
            {}
        )  # ControllerButton enum values

        # Custom user bindings (loaded from settings)
        # Format: {context: {action: [key1, key2, ...]}}
        self._custom_keyboard_bindings: dict[
            InputContext, dict[InputAction, list[tcod.event.KeySym]]
        ] = {}
        self._custom_gamepad_bindings: dict[InputContext, dict[InputAction, list[int]]] = {}

        # Initialize default keyboard mappings (migrated from InputMappings.MOVEMENT_MAP)
        self._init_default_keyboard_mappings()

    def _init_default_keyboard_mappings(self):
        """
        Initialize default keyboard mappings.

        Migrated from game_input.py InputMappings.MOVEMENT_MAP (lines 51-75).
        """
        # ====================================================================
        # MOVEMENT (8-directional)
        # ====================================================================
        # WASD + QEZC
        self._default_keyboard_map[tcod.event.KeySym.W] = InputAction.MOVE_NORTH
        self._default_keyboard_map[tcod.event.KeySym.Q] = InputAction.MOVE_NORTHWEST
        self._default_keyboard_map[tcod.event.KeySym.E] = InputAction.MOVE_NORTHEAST
        self._default_keyboard_map[tcod.event.KeySym.D] = InputAction.MOVE_EAST
        self._default_keyboard_map[tcod.event.KeySym.C] = InputAction.MOVE_SOUTHEAST
        self._default_keyboard_map[tcod.event.KeySym.S] = InputAction.MOVE_SOUTH
        self._default_keyboard_map[tcod.event.KeySym.Z] = InputAction.MOVE_SOUTHWEST
        self._default_keyboard_map[tcod.event.KeySym.A] = InputAction.MOVE_WEST

        # Arrow keys
        self._default_keyboard_map[tcod.event.KeySym.UP] = InputAction.MOVE_NORTH
        self._default_keyboard_map[tcod.event.KeySym.DOWN] = InputAction.MOVE_SOUTH
        self._default_keyboard_map[tcod.event.KeySym.LEFT] = InputAction.MOVE_WEST
        self._default_keyboard_map[tcod.event.KeySym.RIGHT] = InputAction.MOVE_EAST

        # Numpad
        self._default_keyboard_map[tcod.event.KeySym.KP_8] = InputAction.MOVE_NORTH
        self._default_keyboard_map[tcod.event.KeySym.KP_9] = InputAction.MOVE_NORTHEAST
        self._default_keyboard_map[tcod.event.KeySym.KP_6] = InputAction.MOVE_EAST
        self._default_keyboard_map[tcod.event.KeySym.KP_3] = InputAction.MOVE_SOUTHEAST
        self._default_keyboard_map[tcod.event.KeySym.KP_2] = InputAction.MOVE_SOUTH
        self._default_keyboard_map[tcod.event.KeySym.KP_1] = InputAction.MOVE_SOUTHWEST
        self._default_keyboard_map[tcod.event.KeySym.KP_4] = InputAction.MOVE_WEST
        self._default_keyboard_map[tcod.event.KeySym.KP_7] = InputAction.MOVE_NORTHWEST

        # ====================================================================
        # WAIT/REST
        # ====================================================================
        self._default_keyboard_map[tcod.event.KeySym.SPACE] = InputAction.WAIT
        self._default_keyboard_map[tcod.event.KeySym.PERIOD] = InputAction.WAIT
        self._default_keyboard_map[tcod.event.KeySym.KP_5] = InputAction.WAIT

        # ====================================================================
        # EXPLOITS (direct slot activation)
        # ====================================================================
        self._default_keyboard_map[tcod.event.KeySym.N1] = InputAction.EXPLOIT_SLOT_1
        self._default_keyboard_map[tcod.event.KeySym.N2] = InputAction.EXPLOIT_SLOT_2
        self._default_keyboard_map[tcod.event.KeySym.N3] = InputAction.EXPLOIT_SLOT_3
        self._default_keyboard_map[tcod.event.KeySym.N4] = InputAction.EXPLOIT_SLOT_4
        self._default_keyboard_map[tcod.event.KeySym.N5] = InputAction.EXPLOIT_SLOT_5

        # NEW: Exploit cycling (for keyboard users who want gamepad-style controls)
        # Unbound by default - users can optionally bind [ and ] keys
        # self._default_keyboard_map[tcod.event.KeySym.LEFTBRACKET] = InputAction.EXPLOIT_CYCLE_PREV
        # self._default_keyboard_map[tcod.event.KeySym.RIGHTBRACKET] = InputAction.EXPLOIT_CYCLE_NEXT

        # ====================================================================
        # UI TOGGLES
        # ====================================================================
        self._default_keyboard_map[tcod.event.KeySym.I] = InputAction.TOGGLE_INVENTORY
        self._default_keyboard_map[tcod.event.KeySym.L] = InputAction.TOGGLE_LOOK_MODE
        self._default_keyboard_map[tcod.event.KeySym.F] = InputAction.TOGGLE_LORE_VIEWER
        self._default_keyboard_map[tcod.event.KeySym.V] = InputAction.TOGGLE_ACHIEVEMENTS
        # Help requires Shift+/ so handled separately in existing code

        # ====================================================================
        # NAVIGATION (for menus/scrolling - context-sensitive)
        # ====================================================================
        # Navigation overlaps with movement keys - context determines meaning
        # In menus: W/S/arrows = navigate, in gameplay: W/S/arrows = move

        # ====================================================================
        # CONFIRM/CANCEL (context-sensitive)
        # ====================================================================
        self._default_keyboard_map[tcod.event.KeySym.RETURN] = InputAction.CONFIRM
        self._default_keyboard_map[tcod.event.KeySym.KP_ENTER] = InputAction.CONFIRM
        self._default_keyboard_map[tcod.event.KeySym.ESCAPE] = InputAction.CANCEL

        # ====================================================================
        # SPECIAL
        # ====================================================================
        # Debug export (Shift+F12) handled separately due to modifier requirement

    def get_action_for_key(
        self, key: tcod.event.KeySym, context: InputContext = InputContext.GAMEPLAY
    ) -> InputAction | None:
        """
        Get the action for a keyboard key in the given context.

        Args:
            key: The key that was pressed
            context: The current game state context

        Returns:
            The action to perform, or None if no mapping exists
        """
        # Check custom bindings first (if implemented)
        if context in self._custom_keyboard_bindings:
            # Search through custom actions to find one with this key
            for action, keys in self._custom_keyboard_bindings[context].items():
                if key in keys:
                    return action

        # Fall back to default mapping
        return self._default_keyboard_map.get(key)

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

        # Fall back to default mapping (populated in Phase 2)
        return self._default_gamepad_button_map.get(button)

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

    def get_default_keys_for_action(self, action: InputAction) -> list[str]:
        """
        Get list of default key names for an action (for UI display).

        Args:
            action: The action to query

        Returns:
            List of key names (e.g., ["W", "Up", "Numpad8"])
        """
        keys = []
        for key_sym, mapped_action in self._default_keyboard_map.items():
            if mapped_action == action:
                keys.append(self._key_sym_to_display_name(key_sym))
        return keys

    def _key_sym_to_display_name(self, key: tcod.event.KeySym) -> str:
        """
        Convert KeySym to human-readable display name.

        Args:
            key: The key symbol

        Returns:
            Display name (e.g., "W", "Up Arrow", "Numpad 8")
        """
        # Special cases for better display
        display_names = {
            tcod.event.KeySym.UP: "↑",
            tcod.event.KeySym.DOWN: "↓",
            tcod.event.KeySym.LEFT: "←",
            tcod.event.KeySym.RIGHT: "→",
            tcod.event.KeySym.SPACE: "Space",
            tcod.event.KeySym.PERIOD: ".",
            tcod.event.KeySym.RETURN: "Enter",
            tcod.event.KeySym.KP_ENTER: "Numpad Enter",
            tcod.event.KeySym.ESCAPE: "ESC",
            tcod.event.KeySym.KP_1: "Numpad 1",
            tcod.event.KeySym.KP_2: "Numpad 2",
            tcod.event.KeySym.KP_3: "Numpad 3",
            tcod.event.KeySym.KP_4: "Numpad 4",
            tcod.event.KeySym.KP_5: "Numpad 5",
            tcod.event.KeySym.KP_6: "Numpad 6",
            tcod.event.KeySym.KP_7: "Numpad 7",
            tcod.event.KeySym.KP_8: "Numpad 8",
            tcod.event.KeySym.KP_9: "Numpad 9",
            tcod.event.KeySym.N1: "1",
            tcod.event.KeySym.N2: "2",
            tcod.event.KeySym.N3: "3",
            tcod.event.KeySym.N4: "4",
            tcod.event.KeySym.N5: "5",
        }

        if key in display_names:
            return display_names[key]

        # Default: use the key name (e.g., KeySym.W -> "W")
        name = key.name
        if len(name) == 1:
            return name.upper()
        return name.title()

    def load_custom_bindings(self, keyboard_bindings: dict, gamepad_bindings: dict):
        """
        Load custom bindings from settings.

        Args:
            keyboard_bindings: Custom keyboard bindings from user_settings.json
            gamepad_bindings: Custom gamepad bindings from user_settings.json

        Format of bindings dict:
        {
            "MOVE_NORTH": ["W", "UP", "KP_8"],
            "WAIT": ["SPACE", "PERIOD"],
            ...
        }
        """
        # TODO: Implement in Phase 4 (Custom Remapping UI)
        # For now, just log that custom bindings are not yet supported
        if keyboard_bindings:
            logging.debug(
                f"InputMapper: Custom keyboard bindings found ({len(keyboard_bindings)} actions) - not yet implemented"
            )
        if gamepad_bindings:
            logging.debug(
                f"InputMapper: Custom gamepad bindings found ({len(gamepad_bindings)} actions) - not yet implemented"
            )

    def save_custom_bindings(self) -> tuple[dict, dict]:
        """
        Save custom bindings to settings.

        Returns:
            (keyboard_bindings, gamepad_bindings) tuple for user_settings.json
        """
        # TODO: Implement in Phase 4 (Custom Remapping UI)
        return ({}, {})

    def get_conflicts(self, action: InputAction, key: tcod.event.KeySym) -> list[InputAction]:
        """
        Check for binding conflicts (for remapping UI).

        Args:
            action: The action to bind
            key: The key to bind it to

        Returns:
            List of actions currently bound to this key
        """
        # TODO: Implement in Phase 4 (Custom Remapping UI)
        conflicts = []
        for existing_key, existing_action in self._default_keyboard_map.items():
            if existing_key == key and existing_action != action:
                conflicts.append(existing_action)
        return conflicts

    def reset_to_defaults(self, input_type: str = "keyboard"):
        """
        Reset bindings to defaults.

        Args:
            input_type: "keyboard" or "gamepad"
        """
        # TODO: Implement in Phase 4 (Custom Remapping UI)
        if input_type == "keyboard":
            self._custom_keyboard_bindings.clear()
            logging.info("InputMapper: Reset keyboard bindings to defaults")
        elif input_type == "gamepad":
            self._custom_gamepad_bindings.clear()
            logging.info("InputMapper: Reset gamepad bindings to defaults")
