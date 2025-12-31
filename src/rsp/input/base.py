"""
game_input_base.py - Base Input Handler

Unified input handling for all game contexts (menus + gameplay).
All handlers inherit from BaseInputHandler for consistent behavior.

Architecture:
- Per-handler InputMapper and GamepadHandler instances (no shared state)
- Unified handle_input() for keyboard, gamepad, and mouse events
- Subclasses override execute_action() for context-specific behavior
- Return type specified by subclass (str for menus, bool for gameplay)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import tcod.event

from rsp.input.actions import InputAction, InputContext
from rsp.input.device_tracker import InputDeviceType, set_last_device
from rsp.input.gamepad import GamepadInputHandler
from rsp.input.mappings import InputMapper


class BaseInputHandler(ABC):
    """
    Base class for all input handlers (menus and gameplay).

    Provides unified event processing with proper BUTTONUP handling.
    Subclasses must implement: get_context(), execute_action(), get_default_return()
    """

    def __init__(
        self,
        game=None,
        renderer=None,
        input_mapper: InputMapper | None = None,
        controllers: set | None = None,
        gamepad_handler=None,
    ):
        """
        Initialize base input handler.

        Args:
            game: Game instance (None for menus, required for gameplay)
            renderer: GameRenderer instance (None for headless tests)
            input_mapper: Shared InputMapper instance. If None, creates a new one.
                         Sharing the mapper allows custom bindings to apply across
                         all handlers.
            controllers: Set of connected controller objects. If None, empty set is used.
                        IMPORTANT: Must be passed for gamepad input to work!
            gamepad_handler: Shared GamepadInputHandler instance. If provided, uses it
                           instead of creating a new one. This ensures gamepad state
                           (button_held, analog stick, settings) stays in sync across
                           all handlers.
        """
        self.game = game
        self.renderer = renderer

        # InputMapper is stateless (lookup tables only) - safe to share
        self.input_mapper = input_mapper if input_mapper is not None else InputMapper()

        # GamepadInputHandler has state - share it if provided to keep state in sync
        if gamepad_handler is not None:
            self.gamepad_handler = gamepad_handler
        else:
            self.gamepad_handler = GamepadInputHandler(
                self.input_mapper, game, initial_controllers=controllers or set()
            )

        # Load custom bindings if game has settings (only if we created the mapper)
        if input_mapper is None and game and hasattr(game, "settings"):
            keyboard_bindings = getattr(game.settings, "custom_keyboard_bindings", {})
            gamepad_bindings = getattr(game.settings, "custom_gamepad_bindings", {})
            self.input_mapper.load_custom_bindings(keyboard_bindings, gamepad_bindings)

    # ========================================================================
    # ABSTRACT METHODS (subclasses must implement)
    # ========================================================================

    @abstractmethod
    def get_context(self) -> InputContext:
        """
        Get current input context (determines action mapping).

        Returns:
            InputContext enum value
        """
        pass

    @abstractmethod
    def execute_action(self, action: InputAction) -> Any:
        """
        Execute a game action.

        Args:
            action: The InputAction to execute

        Returns:
            Handler-specific return value (str for menus, bool for gameplay)
        """
        pass

    @abstractmethod
    def get_default_return(self) -> Any:
        """
        Get default return value when no action is executed.

        Returns:
            "" for menus, True for gameplay
        """
        pass

    def _is_headless(self) -> bool:
        """Check if running in headless mode (no renderer available)."""
        return self.renderer is None

    # ========================================================================
    # UNIFIED EVENT PROCESSING
    # ========================================================================

    def handle_input(self, event) -> Any:
        """
        Unified entry point for ALL input events.

        Handles keyboard, gamepad, and mouse events.
        Routes to appropriate handler, executes actions, handles errors.
        Also updates device tracker for dynamic help text.

        Args:
            event: TCOD event (KeyDown, ControllerButton, MouseMotion, etc.)

        Returns:
            Handler-specific return value (str for menus, bool for gameplay)
        """
        context = self.get_context()
        action = None

        # Keyboard events
        if isinstance(event, tcod.event.KeyDown):
            set_last_device(InputDeviceType.KEYBOARD)
            # Pass modifier flags to support Shift+key, Ctrl+key combinations
            modifier = getattr(event, "mod", 0)
            action = self.input_mapper.get_action_for_key(event.sym, context, modifier)

        # Gamepad button events
        elif isinstance(event, tcod.event.ControllerButton):
            set_last_device(InputDeviceType.GAMEPAD)
            action = self.gamepad_handler.handle_button_event(event, context)

        # Gamepad axis events (analog sticks, triggers)
        elif isinstance(event, tcod.event.ControllerAxis):
            set_last_device(InputDeviceType.GAMEPAD)
            action = self.gamepad_handler.handle_axis_event(event, context)

        # Mouse motion events
        elif isinstance(event, tcod.event.MouseMotion):
            # Don't update device on motion - only meaningful inputs
            return self.handle_mouse_motion(event)

        # Mouse button events
        elif isinstance(event, tcod.event.MouseButtonDown):
            set_last_device(InputDeviceType.KEYBOARD)  # Mouse = keyboard mode
            if event.button == tcod.event.MouseButton.LEFT:
                return self.handle_left_click(event)
            elif event.button == tcod.event.MouseButton.RIGHT:
                return self.handle_right_click(event)

        # Mouse wheel events
        elif isinstance(event, tcod.event.MouseWheel):
            set_last_device(InputDeviceType.KEYBOARD)  # Mouse = keyboard mode
            return self.handle_mouse_wheel(event)

        # Execute action if found, with error handling
        if action:
            try:
                return self.execute_action(action)
            except AttributeError as e:
                # Wrong context (e.g., menu trying to execute gameplay action)
                logging.error(f"execute_action failed (wrong context?): {action.name} - {e}")
                return self.get_default_return()
            except Exception as e:
                # Unexpected error - log and continue
                logging.error(f"execute_action crashed: {action.name} - {e}", exc_info=True)
                return self.get_default_return()

        return self.get_default_return()

    # ========================================================================
    # MOUSE HANDLING (default no-ops, subclasses override as needed)
    # ========================================================================

    def handle_mouse_click(self, event: tcod.event.MouseButtonDown) -> Any:
        """
        Handle mouse click events - dispatch to left/right click handlers.

        This is the main entry point for mouse clicks from the game loop.
        Dispatches to handle_left_click or handle_right_click based on button.

        Args:
            event: Mouse button down event

        Returns:
            Handler-specific return value
        """
        set_last_device(InputDeviceType.KEYBOARD)  # Mouse = keyboard mode

        if not hasattr(event, "button"):
            return self.get_default_return()

        if event.button == tcod.event.MouseButton.LEFT:
            return self.handle_left_click(event)
        elif event.button == tcod.event.MouseButton.RIGHT:
            return self.handle_right_click(event)

        return self.get_default_return()

    def handle_mouse_motion(self, event: tcod.event.MouseMotion) -> Any:
        """
        Handle mouse motion events.

        Default: do nothing (return default value).
        Subclasses override for hover effects, cursor updates, etc.

        Args:
            event: Mouse motion event with position

        Returns:
            Handler-specific return value
        """
        # Headless mode or no mouse processing needed
        if self._is_headless():
            return self.get_default_return()

        # Default: do nothing
        return self.get_default_return()

    def handle_left_click(self, event: tcod.event.MouseButtonDown) -> Any:
        """
        Handle left mouse button click.

        Default: do nothing (return default value).
        Subclasses override for click actions.

        Args:
            event: Mouse button down event

        Returns:
            Handler-specific return value
        """
        # Headless mode: no renderer, can't process mouse
        if self._is_headless():
            return self.get_default_return()

        # Default: do nothing
        return self.get_default_return()

    def handle_right_click(self, event: tcod.event.MouseButtonDown) -> Any:
        """
        Handle right mouse button click.

        Default: do nothing (return default value).
        Subclasses override for context menus, cancel actions, etc.

        Args:
            event: Mouse button down event

        Returns:
            Handler-specific return value
        """
        # Headless mode: no renderer, can't process mouse
        if self._is_headless():
            return self.get_default_return()

        # Default: universal "back" or "cancel" for menus
        return self.get_default_return()

    def handle_mouse_wheel(self, event: tcod.event.MouseWheel) -> Any:
        """
        Handle mouse wheel scrolling.

        Default: do nothing (return default value).
        Subclasses override for scrolling lists, zooming, etc.

        Args:
            event: Mouse wheel event

        Returns:
            Handler-specific return value
        """
        # Headless mode: no renderer, can't process mouse
        if self._is_headless():
            return self.get_default_return()

        # Default: do nothing
        return self.get_default_return()
