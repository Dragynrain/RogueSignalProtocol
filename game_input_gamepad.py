"""
game_input_gamepad.py - Gamepad Input Handler

Handles low-level gamepad events from SDL/TCOD:
- Button press/release events
- Analog stick axis events
- Device connection/disconnection (hotplugging)
- Integration with input mapper for action lookup

Uses time-based movement gating for analog sticks with settling period
and direction locking to ensure one move per stick deflection.
"""

import logging

import tcod.event
import tcod.sdl.joystick

from game_config import GameConfig, GameSettings
from game_input_actions import InputAction, InputContext
from game_input_analog import AnalogStickHandler
from game_input_mappings import InputMapper


class GamepadInputHandler:
    """
    Handles gamepad input events and converts them to game actions.

    Manages controller device lifecycle (connect/disconnect) and processes
    button/axis events through the input mapping layer.
    """

    def __init__(
        self,
        input_mapper: InputMapper,
        game=None,
        initial_controllers: set[tcod.sdl.joystick.GameController] | None = None,
    ):
        """
        Initialize gamepad input handler.

        Args:
            input_mapper: InputMapper instance for action lookup
            game: GameEngine instance (needed for turn tracking in gameplay, optional for menus)
            initial_controllers: Set of already-connected controllers from game loop init
        """
        self.controllers: set[tcod.sdl.joystick.GameController] = (
            initial_controllers if initial_controllers is not None else set()
        )
        self.input_mapper = input_mapper
        self.game = game

        # Create analog handler with settings from game (if available)
        deadzone = None
        threshold = None
        direction_locking = True
        if game and hasattr(game, "settings") and game.settings is not None:
            dz = getattr(game.settings, "gamepad_deadzone", None)
            th = getattr(game.settings, "gamepad_threshold", None)
            dl = getattr(game.settings, "gamepad_direction_locking", None)
            # Only use if actual float/bool (not Mock objects from tests)
            if isinstance(dz, (int, float)):
                deadzone = dz
            if isinstance(th, (int, float)):
                threshold = th
            if isinstance(dl, bool):
                direction_locking = dl
        self.analog_handler = AnalogStickHandler(
            deadzone=deadzone, threshold=threshold, direction_locking=direction_locking
        )

        # Button repeat tracking (for D-pad and face buttons in menus)
        self.button_held = None  # Which button is currently held
        self.button_held_since = -1.0  # When button was pressed (-1 = never)
        self.button_repeat_initial_delay = GameConfig.BUTTON_REPEAT_INITIAL_DELAY
        self.button_repeat_rate = GameConfig.BUTTON_REPEAT_RATE
        self.button_repeat_rate_fast = GameConfig.BUTTON_REPEAT_RATE_FAST
        self.button_last_repeat_time = -1.0  # Last time we sent a repeat action (-1 = never)

        # Contexts that benefit from faster auto-repeat (long scrolling lists)
        self.fast_repeat_contexts = {
            InputContext.ACHIEVEMENTS_SCREEN,
        }

        # Log initial controller state
        if self.controllers:
            logging.info(
                f"GamepadInputHandler: Initialized with {len(self.controllers)} controller(s)"
            )
        else:
            logging.debug("GamepadInputHandler: No controllers connected at startup")

    def _get_settings(self):
        """
        Get effective settings.

        Returns settings from game.settings if available, otherwise returns
        the global GameSettings instance (for menus where game=None).

        Returns:
            Settings object or None if no settings available
        """
        if self.game and hasattr(self.game, "settings") and self.game.settings is not None:
            return self.game.settings
        return GameSettings.get_instance()

    def _is_gamepad_disabled(self) -> bool:
        """Check if gamepad input is disabled in settings."""
        settings = self._get_settings()
        return settings and not getattr(settings, "gamepad_enabled", True)

    def sync_settings_to_analog_handler(self) -> None:
        """
        Sync current settings to the analog handler.

        Call this when gamepad settings change (deadzone, threshold, direction locking)
        to apply the new values without recreating the handler.

        Optimized: Only updates if values actually changed (avoids redundant writes).
        """
        settings = self._get_settings()
        if settings is None:
            return

        # Update deadzone (only if changed)
        dz = getattr(settings, "gamepad_deadzone", None)
        if isinstance(dz, (int, float)) and self.analog_handler.deadzone != dz:
            self.analog_handler.deadzone = dz

        # Update threshold (only if changed)
        th = getattr(settings, "gamepad_threshold", None)
        if isinstance(th, (int, float)) and self.analog_handler.threshold != th:
            self.analog_handler.threshold = th

        # Update direction locking (only if changed)
        dl = getattr(settings, "gamepad_direction_locking", None)
        if isinstance(dl, bool) and self.analog_handler.direction_locking != dl:
            self.analog_handler.direction_locking = dl

    def handle_device_event(self, event: tcod.event.ControllerDevice) -> None:
        """
        Handle controller connection/disconnection events.

        Args:
            event: Controller device add/remove event
        """
        if event.type == "CONTROLLERDEVICEADDED":
            # Get the newly connected controller directly from event
            try:
                # CRITICAL FIX: Use event.controller directly (not get_controllers() enumeration)
                # The event object carries the controller ready to use
                if hasattr(event, "controller") and event.controller:
                    controller = event.controller
                    self.controllers.add(controller)
                    try:
                        name = controller.name
                    except AttributeError:
                        name = "Unknown"
                    logging.info(f"Gamepad connected: {name}")
                    # Show in-game message
                    if self.game and hasattr(self.game, "message_log"):
                        from game_entities import Colors

                        self.game.message_log.add_message("Controller connected", Colors.CYAN)
                else:
                    # CRITICAL: Do NOT call get_controllers() during gameplay - returns empty!
                    # If event.controller is None, we cannot recover safely
                    logging.error(
                        "CONTROLLERDEVICEADDED event missing controller property - "
                        "cannot add controller (get_controllers() forbidden during gameplay)"
                    )
            except (AttributeError, TypeError, RuntimeError, OSError) as e:
                logging.error(f"Failed to add controller: {e}", exc_info=True)

        elif event.type == "CONTROLLERDEVICEREMOVED":
            # Remove ALL disconnected controllers (not just the first)
            # Use discard() not remove() - controller might not be in set
            # (TCOD research gotcha #1)
            removed_controllers = []
            for controller in list(self.controllers):
                # SDL marks removed controllers as invalid
                # Check validity by accessing properties - invalid controllers raise errors
                try:
                    _ = controller.name
                except (AttributeError, RuntimeError, OSError):
                    # Controller is invalid (SDL returns error when accessing removed controller)
                    self.controllers.discard(controller)
                    removed_controllers.append(controller)

            if removed_controllers:
                logging.info(f"Gamepad(s) disconnected: {len(removed_controllers)} controller(s)")
                # Show in-game message (keyboard/mouse still work)
                if self.game and hasattr(self.game, "message_log"):
                    from game_entities import Colors

                    self.game.message_log.add_message(
                        "Controller disconnected - keyboard/mouse active", Colors.YELLOW
                    )

                # Clear button state (prevent phantom inputs)
                self.button_held = None
                self.button_held_since = -1.0  # Reset to "never" state
                self.button_last_repeat_time = -1.0  # Reset to "never" state

                # Clear analog stick state (prevent drift/phantom movement)
                self.analog_handler.left_x = 0
                self.analog_handler.left_y = 0
                self.analog_handler.right_x = 0
                self.analog_handler.right_y = 0

    def handle_button_event(
        self, event: tcod.event.ControllerButton, context: InputContext
    ) -> InputAction | None:
        """
        Handle gamepad button press/release events.

        Args:
            event: Controller button event
            context: Current game state context

        Returns:
            The action to perform, or None if no mapping exists or button released
        """
        import time

        # Check if gamepad is enabled in settings
        if self._is_gamepad_disabled():
            return None

        # Track button releases (clear repeat state)
        if not event.pressed:
            if self.button_held == event.button:
                self.button_held = None
                self.button_held_since = -1.0  # Reset to "never" state
                self.button_last_repeat_time = -1.0
            return None

        # Look up action for this button in current context
        action = self.input_mapper.get_action_for_gamepad_button(event.button, context)

        if action:
            # Track navigation buttons for auto-repeat in menu contexts
            if action in (
                InputAction.NAVIGATE_UP,
                InputAction.NAVIGATE_DOWN,
                InputAction.NAVIGATE_LEFT,
                InputAction.NAVIGATE_RIGHT,
            ):
                if context in [
                    InputContext.MAIN_MENU,
                    InputContext.SETTINGS_MENU,
                    InputContext.CONTROLS_MENU,
                    InputContext.ABOUT_MENU,
                    InputContext.GRAPHICS_PREVIEW,
                    InputContext.HELP,
                    InputContext.ACHIEVEMENTS_SCREEN,
                    InputContext.LORE_VIEWER,
                    InputContext.INVENTORY,
                ]:
                    self.button_held = event.button
                    self.button_held_since = time.time()
                    self.button_last_repeat_time = time.time()

        return action

    def handle_axis_event(
        self, event: tcod.event.ControllerAxis, context: InputContext
    ) -> InputAction | None:
        """
        Handle gamepad analog stick/trigger axis events.

        Args:
            event: Controller axis event
            context: Current game state context

        Returns:
            The action to perform, or None if no action triggered
        """
        # Check if gamepad is enabled in settings
        if self._is_gamepad_disabled():
            return None

        # Sync deadzone/direction_locking from settings (in case user changed them)
        self.sync_settings_to_analog_handler()

        # Import axis constants from correct location
        import tcod.sdl.joystick

        CA = tcod.sdl.joystick.ControllerAxis

        # Check if sticks should be swapped (accessibility setting)
        settings = self._get_settings()
        swap_sticks = getattr(settings, "gamepad_swap_sticks", False) if settings else False

        # Update analog handler state - always store physical stick values directly
        # The swap logic is applied at READ time, not storage time
        if event.axis == CA.LEFTX:
            self.analog_handler.update_left_stick(x=event.value)
        elif event.axis == CA.LEFTY:
            self.analog_handler.update_left_stick(y=event.value)
        elif event.axis == CA.RIGHTX:
            self.analog_handler.update_right_stick(x=event.value)
        elif event.axis == CA.RIGHTY:
            self.analog_handler.update_right_stick(y=event.value)

        # GAMEPLAY context: Turn-based movement gating (PLAN Phase 1.3)
        # When swap_sticks is enabled, use RIGHT stick for movement instead of LEFT
        if context == InputContext.GAMEPLAY:
            if self.game is None:
                logging.error("GamepadInputHandler: game is None in GAMEPLAY context!")
                return None
            if swap_sticks:
                movement = self.analog_handler.get_right_stick_movement_gameplay(self.game.turn)
            else:
                movement = self.analog_handler.get_left_stick_movement_gameplay(self.game.turn)
            if movement:
                dx, dy = movement
                # Convert to movement action
                return self._delta_to_movement_action(dx, dy)

        # MENU contexts: Time-based auto-repeat for navigation (non-turn-based)
        # When swap_sticks is enabled, use RIGHT stick for navigation instead of LEFT
        elif context in [
            InputContext.MAIN_MENU,
            InputContext.SETTINGS_MENU,
            InputContext.CONTROLS_MENU,
            InputContext.ABOUT_MENU,
            InputContext.GRAPHICS_PREVIEW,
            InputContext.INVENTORY,
            InputContext.LORE_VIEWER,
            InputContext.HELP,
            InputContext.ACHIEVEMENTS_SCREEN,
        ]:
            # Determine which physical axes to listen to based on swap_sticks setting
            nav_axis_x = CA.RIGHTX if swap_sticks else CA.LEFTX
            nav_axis_y = CA.RIGHTY if swap_sticks else CA.LEFTY

            # Choose the correct movement method based on swap setting
            def get_nav_movement():
                if swap_sticks:
                    return self.analog_handler.get_right_stick_movement_menu()
                else:
                    return self.analog_handler.get_left_stick_movement_menu()

            # Menus that need both horizontal and vertical navigation
            # - Graphics Preview: variant cycling + entity selection
            # - Settings Menu: value adjustment (volume, toggles) + option selection
            # - Help/Lore Menus: tab switching + content scrolling
            if context in [
                InputContext.GRAPHICS_PREVIEW,
                InputContext.SETTINGS_MENU,
                InputContext.HELP,
                InputContext.LORE_VIEWER,
            ]:
                # Process both X and Y axis
                if event.axis == nav_axis_x:
                    # Horizontal movement for variant cycling / value adjustment / tab switching
                    movement = get_nav_movement()
                    if movement:
                        dx, dy = movement
                        if dx < 0:
                            return InputAction.NAVIGATE_LEFT
                        elif dx > 0:
                            return InputAction.NAVIGATE_RIGHT
                elif event.axis == nav_axis_y:
                    # Vertical movement for entity/option selection
                    movement = get_nav_movement()
                    if movement:
                        dx, dy = movement
                        if dy < 0:
                            return InputAction.NAVIGATE_UP
                        elif dy > 0:
                            return InputAction.NAVIGATE_DOWN
            else:
                # Other menus: Only process when Y-axis changes (avoid processing X-axis separately)
                if event.axis != nav_axis_y:
                    return None

                movement = get_nav_movement()

                if movement:
                    dx, dy = movement
                    # Convert to navigation action (up/down for vertical menus)
                    if dy < 0:
                        return InputAction.NAVIGATE_UP
                    elif dy > 0:
                        return InputAction.NAVIGATE_DOWN
                    # Ignore horizontal movement in vertical-only menus (MAIN_MENU, etc.)

        # Triggers (LT/RT) - edge detection to fire once per press, not continuously
        if event.axis in [CA.TRIGGERLEFT, CA.TRIGGERRIGHT]:
            is_right_trigger = event.axis == CA.TRIGGERRIGHT
            # Check if trigger just crossed threshold (rising edge)
            if self.analog_handler.check_trigger_pressed(event.value, is_right_trigger):
                # Look up trigger binding for current context
                action = self.input_mapper.get_action_for_gamepad_axis(event.axis, context)
                if action:
                    logging.debug(
                        f"Gamepad trigger {event.axis} -> {action.name} (context: {context.name})"
                    )
                    return action

        # Phase 3.3: Right stick auto-look mode + cursor control
        # When swap_sticks is enabled, use LEFT stick for look mode instead of RIGHT
        # IMPORTANT: Only trigger look mode if THIS event is from the look stick
        # (prevents false triggers when movement stick is pushed but look stick has residual data)
        look_axis_x = CA.LEFTX if swap_sticks else CA.RIGHTX
        look_axis_y = CA.LEFTY if swap_sticks else CA.RIGHTY
        is_look_stick_event = event.axis in (look_axis_x, look_axis_y)

        if swap_sticks:
            look_stick_magnitude = self.analog_handler.get_left_stick_magnitude()
        else:
            look_stick_magnitude = self.analog_handler.get_right_stick_magnitude()

        # Auto-enter look mode from gameplay when look stick is moved
        # Only trigger if THIS event is from the look stick (not the movement stick)
        if (
            context == InputContext.GAMEPLAY
            and is_look_stick_event
            and look_stick_magnitude > GameConfig.GAMEPAD_LOOK_MODE_THRESHOLD
        ):
            # Auto-activate look mode (will be handled by caller)
            # Return special action to trigger look mode entry
            return InputAction.TOGGLE_LOOK_MODE

        # In look mode or targeting mode, use look stick for cursor movement (throttled)
        elif context in [InputContext.LOOK_MODE, InputContext.TARGETING]:
            if swap_sticks:
                movement = self.analog_handler.get_left_stick_movement()
            else:
                movement = self.analog_handler.get_right_stick_movement()
            if movement:
                dx, dy = movement
                # Convert to navigation action
                return self._delta_to_movement_action(dx, dy)

        return None

    def _delta_to_movement_action(self, dx: int, dy: int) -> InputAction | None:
        """
        Convert movement delta to InputAction.

        Args:
            dx: X movement delta (-1, 0, 1)
            dy: Y movement delta (-1, 0, 1)

        Returns:
            Corresponding movement action, or None if invalid
        """
        movement_map = {
            (0, -1): InputAction.MOVE_NORTH,
            (0, 1): InputAction.MOVE_SOUTH,
            (1, 0): InputAction.MOVE_EAST,
            (-1, 0): InputAction.MOVE_WEST,
            (1, -1): InputAction.MOVE_NORTHEAST,
            (-1, -1): InputAction.MOVE_NORTHWEST,
            (1, 1): InputAction.MOVE_SOUTHEAST,
            (-1, 1): InputAction.MOVE_SOUTHWEST,
        }
        return movement_map.get((dx, dy))

    def has_controllers(self) -> bool:
        """Check if any controllers are connected."""
        return len(self.controllers) > 0

    def get_controller_count(self) -> int:
        """Get number of connected controllers."""
        return len(self.controllers)

    def get_repeat_rate(self, context: InputContext) -> float:
        """
        Get the repeat rate for a given context.

        Args:
            context: Input context

        Returns:
            Repeat rate in seconds (smaller = faster)
        """
        if context in self.fast_repeat_contexts:
            return self.button_repeat_rate_fast
        return self.button_repeat_rate

    def get_initial_delay(self, context: InputContext) -> float:
        """
        Get the initial delay before repeat starts.

        Args:
            context: Input context (currently same for all contexts)

        Returns:
            Initial delay in seconds
        """
        return self.button_repeat_initial_delay

    def get_button_repeat_action(self, context: InputContext) -> InputAction | None:
        """
        Check if a held button should trigger a repeat action.

        Called once per frame to implement auto-repeat for held D-pad buttons.
        Similar to keyboard repeat: initial delay, then continuous repeat.

        Args:
            context: Current game state context

        Returns:
            Action to perform if button repeat should trigger, None otherwise
        """
        import time

        # Check if gamepad is enabled in settings
        if self._is_gamepad_disabled():
            return None

        if self.button_held is None:
            return None

        # Validate button timing state (sentinel -1.0 means "never pressed")
        if self.button_held_since < 0:
            return None

        current_time = time.time()
        time_held = current_time - self.button_held_since
        time_since_last_repeat = current_time - self.button_last_repeat_time

        # Guard against clock going backwards (system time adjustment)
        if time_held < 0 or time_since_last_repeat < 0:
            self.button_held_since = current_time
            self.button_last_repeat_time = -1.0  # Reset to allow immediate first repeat
            return None

        # Initial delay before repeat starts
        if time_held < self.button_repeat_initial_delay:
            return None

        # Check if enough time has passed for next repeat
        # Use faster rate for scrolling contexts
        repeat_rate = self.get_repeat_rate(context)
        if time_since_last_repeat < repeat_rate:
            return None

        # Time to send repeat action
        self.button_last_repeat_time = current_time

        # Look up action for the held button
        action = self.input_mapper.get_action_for_gamepad_button(self.button_held, context)
        return action
