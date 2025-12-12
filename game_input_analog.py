"""
game_input_analog.py - Analog Stick Input Handling

Handles gamepad analog stick input with deadzone processing and analog-to-digital
conversion for tile-based movement.

Key features:
- Scaled radial deadzone (industry standard, smooth gradient)
- Analog-to-digital conversion for 8-way tile movement
- TIME-BASED movement gating with direction locking
- Support for both left and right sticks (movement vs cursor)

Based on TCOD research and SDL best practices.
"""

import logging
import math
import time

from game_config import GameConfig

# SDL joystick axis range constants
SDL_JOYSTICK_AXIS_MAX = 32768.0  # Maximum absolute value for joystick axes (signed -32768 to 32767)
SDL_JOYSTICK_TRIGGER_MAX = 32767.0  # Maximum value for trigger axes (unsigned 0 to 32767)


class AnalogStickHandler:
    """
    Processes analog stick input from gamepad controllers.

    Handles deadzone filtering, analog-to-digital conversion, and time-based
    movement gating with direction locking for tile-based roguelike gameplay.
    """

    def __init__(
        self,
        deadzone: float | None = None,
        threshold: float | None = None,
        direction_locking: bool = True,
    ):
        """
        Initialize analog stick handler.

        Args:
            deadzone: Minimum stick deflection to register (0.0-1.0). If None, uses 0.15
            threshold: Stick deflection required for digital movement (0.0-1.0)
            direction_locking: Lock direction on first deflection until stick released
        """
        self.deadzone = deadzone if deadzone is not None else GameConfig.GAMEPAD_DEADZONE
        self.threshold = threshold if threshold is not None else GameConfig.GAMEPAD_ANALOG_THRESHOLD
        self.direction_locking = direction_locking

        # Current stick states (raw values from SDL)
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0

        # TIME-BASED movement gating for gameplay (fixes rapid movement bug)
        # Turn-based gating doesn't work because turns increment after each move
        # Using time-based with initial delay + repeat rate like menu navigation
        self.last_gameplay_move_time = -1.0  # -1.0 = never moved
        self.gameplay_initial_delay = GameConfig.GAMEPLAY_MOVEMENT_INITIAL_DELAY
        self.gameplay_repeat_rate = GameConfig.GAMEPLAY_MOVEMENT_REPEAT_RATE
        self.gameplay_is_repeating = False
        self.last_gameplay_direction = (0, 0)  # Track direction for change detection

        # TIME-BASED menu navigation (for non-turn-based contexts)
        # Phase 1: Initial move (immediate)
        # Phase 2: Delay before repeat starts
        # Phase 3: Continuous repeat at fixed rate
        self.last_menu_move_time = -1.0  # -1.0 indicates never moved (avoids time=0.0 bug)
        self.menu_initial_delay = GameConfig.MENU_NAVIGATION_INITIAL_DELAY
        self.menu_repeat_rate = GameConfig.MENU_NAVIGATION_REPEAT_RATE
        self.menu_is_repeating = False
        self.last_menu_direction = (0, 0)  # Track last direction to detect direction changes

        # Separate auto-repeat for cursor movement (right stick)
        # Now includes direction locking and settling period like gameplay movement
        self.last_cursor_move_time = -1.0  # -1.0 = never moved (allows settling detection)
        self.cursor_initial_delay = GameConfig.CURSOR_MOVEMENT_INITIAL_DELAY
        self.cursor_repeat_rate = GameConfig.CURSOR_MOVEMENT_REPEAT_RATE
        self.cursor_is_repeating = False
        self.last_cursor_direction = (0, 0)  # Direction locking for cursor
        self._cursor_settling_start_time = -1.0  # Settling period tracking for cursor
        self._settling_start_time = -1.0  # Settling period tracking for gameplay movement

        # Trigger state tracking (for edge detection - fire once per press, not continuously)
        self.left_trigger_pressed = False
        self.right_trigger_pressed = False

    def apply_scaled_radial_deadzone(self, x: int, y: int) -> tuple[float, float]:
        """
        Apply scaled radial deadzone with smooth gradient.

        This is the industry-standard approach used in most modern games.
        Creates a smooth transition from deadzone edge to maximum deflection,
        eliminating the harsh "snap" of simple radial deadzones.

        Args:
            x: Raw X-axis value (-32768 to 32767)
            y: Raw Y-axis value (-32768 to 32767)

        Returns:
            (normalized_x, normalized_y) tuple in range -1.0 to 1.0
        """
        # Normalize to -1.0 to 1.0
        norm_x = x / SDL_JOYSTICK_AXIS_MAX
        norm_y = y / SDL_JOYSTICK_AXIS_MAX

        # Calculate magnitude
        magnitude = math.sqrt(norm_x**2 + norm_y**2)

        # Apply deadzone - return zero if below threshold
        if magnitude < self.deadzone:
            return (0.0, 0.0)

        # Rescale to create smooth gradient from deadzone edge to max
        # Formula: (magnitude - deadzone) / (1 - deadzone)
        # Guard against division by zero if deadzone >= 1.0 (invalid config)
        divisor = 1.0 - self.deadzone
        if divisor <= 0:
            return (0.0, 0.0)
        normalized_magnitude = (magnitude - self.deadzone) / divisor
        normalized_magnitude = min(normalized_magnitude, 1.0)  # Clamp to 1.0

        # Preserve direction, apply new magnitude
        if magnitude > 0:  # Avoid division by zero
            scale = normalized_magnitude / magnitude
            return (norm_x * scale, norm_y * scale)

        return (0.0, 0.0)

    def apply_axial_deadzone(self, x: int, y: int) -> tuple[float, float]:
        """
        Apply axial (cardinal) deadzone to each axis independently.

        Simpler than radial, works well for 4-way/8-way tile-based movement.
        Less accurate for sweeping diagonal motions but easier to implement.

        Args:
            x: Raw X-axis value (-32768 to 32767)
            y: Raw Y-axis value (-32768 to 32767)

        Returns:
            (normalized_x, normalized_y) tuple in range -1.0 to 1.0
        """
        # Normalize to -1.0 to 1.0
        norm_x = x / SDL_JOYSTICK_AXIS_MAX
        norm_y = y / SDL_JOYSTICK_AXIS_MAX

        # Apply deadzone per axis
        if abs(norm_x) < self.deadzone:
            norm_x = 0.0
        if abs(norm_y) < self.deadzone:
            norm_y = 0.0

        return (norm_x, norm_y)

    def analog_to_8way(self, x: int, y: int, use_radial: bool = True) -> tuple[int, int]:
        """
        Convert analog stick input to 8-way digital direction using equal angular zones.

        Uses 45-degree wedges for each direction (8 directions = 360/8 = 45° each).
        This makes diagonals equally easy to hit as cardinals.

        Args:
            x: Raw X-axis value (-32768 to 32767)
            y: Raw Y-axis value (-32768 to 32767)
            use_radial: Use scaled radial deadzone (True) or axial deadzone (False)

        Returns:
            (dx, dy) where each is -1, 0, or 1
        """
        # Apply deadzone
        if use_radial:
            norm_x, norm_y = self.apply_scaled_radial_deadzone(x, y)
        else:
            norm_x, norm_y = self.apply_axial_deadzone(x, y)

        # Check if stick is past threshold (magnitude check)
        magnitude = math.sqrt(norm_x**2 + norm_y**2)
        if magnitude < self.threshold:
            return (0, 0)

        # Calculate angle using atan2 (returns -180 to 180 degrees)
        # SDL coords: +X = right, +Y = down (screen coords)
        angle_rad = math.atan2(norm_y, norm_x)
        angle_deg = math.degrees(angle_rad)

        # Normalize to 0-360
        if angle_deg < 0:
            angle_deg += 360

        # Equal 45° zones for all 8 directions
        # Zone boundaries (from East at 0°, clockwise):
        # E:  337.5° to 22.5°  (45°)
        # SE: 22.5° to 67.5°   (45°)
        # S:  67.5° to 112.5°  (45°)
        # SW: 112.5° to 157.5° (45°)
        # W:  157.5° to 202.5° (45°)
        # NW: 202.5° to 247.5° (45°)
        # N:  247.5° to 292.5° (45°)
        # NE: 292.5° to 337.5° (45°)

        # Shift by 22.5° so boundaries fall between directions
        shifted_angle = (angle_deg + 22.5) % 360
        sector = int(shifted_angle / 45)

        direction_map = {
            0: (1, 0),  # East
            1: (1, 1),  # Southeast
            2: (0, 1),  # South
            3: (-1, 1),  # Southwest
            4: (-1, 0),  # West
            5: (-1, -1),  # Northwest
            6: (0, -1),  # North
            7: (1, -1),  # Northeast
        }
        result = direction_map.get(sector, (0, 0))

        # Debug logging for analog stick direction detection
        direction_names = {
            (1, 0): "E",
            (1, 1): "SE",
            (0, 1): "S",
            (-1, 1): "SW",
            (-1, 0): "W",
            (-1, -1): "NW",
            (0, -1): "N",
            (1, -1): "NE",
        }
        logging.debug(
            f"analog_to_8way: raw=({x},{y}) norm=({norm_x:.2f},{norm_y:.2f}) "
            f"mag={magnitude:.2f} angle={angle_deg:.1f} -> {direction_names.get(result, '?')}"
        )

        return result

    def analog_to_4way(self, x: int, y: int, use_radial: bool = True) -> tuple[int, int]:
        """
        Convert analog stick input to 4-way digital direction (cardinals only).

        For MENU navigation where diagonals don't make sense - picking "mostly left
        with a bit up" should go LEFT, not trigger both up AND left actions.

        Picks the dominant axis. If equal magnitude, prefers vertical (more common
        for menu navigation).

        Args:
            x: Raw X-axis value (-32768 to 32767)
            y: Raw Y-axis value (-32768 to 32767)
            use_radial: Use scaled radial deadzone (True) or axial deadzone (False)

        Returns:
            (dx, dy) where one is -1/0/1 and the other is always 0
        """
        # Apply deadzone
        if use_radial:
            norm_x, norm_y = self.apply_scaled_radial_deadzone(x, y)
        else:
            norm_x, norm_y = self.apply_axial_deadzone(x, y)

        # Check if stick is past threshold (magnitude check)
        magnitude = math.sqrt(norm_x**2 + norm_y**2)
        if magnitude < self.threshold:
            return (0, 0)

        # Pick dominant axis (if equal, prefer vertical for menu nav)
        if abs(norm_x) > abs(norm_y):
            result = (1 if norm_x > 0 else -1, 0)
        else:
            result = (0, 1 if norm_y > 0 else -1)

        # Debug logging
        direction_names = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}
        logging.debug(
            f"analog_to_4way: raw=({x},{y}) norm=({norm_x:.2f},{norm_y:.2f}) "
            f"mag={magnitude:.2f} -> {direction_names.get(result, '?')}"
        )

        return result

    def apply_trigger_deadzone(self, value: int) -> float:
        """
        Apply deadzone to trigger input.

        Triggers range from 0 to 32767 (not -32768 to 32767 like sticks).

        Args:
            value: Raw trigger value (0 to 32767)

        Returns:
            Normalized value in range 0.0 to 1.0
        """
        # Normalize to 0.0 to 1.0
        normalized = value / SDL_JOYSTICK_TRIGGER_MAX

        # Apply deadzone
        if normalized < self.deadzone:
            return 0.0

        # Rescale (guard against invalid deadzone >= 1.0)
        divisor = 1.0 - self.deadzone
        if divisor <= 0:
            return 0.0
        return (normalized - self.deadzone) / divisor

    def update_left_stick(self, x: int | None = None, y: int | None = None):
        """
        Update left stick state.

        Args:
            x: New X-axis value, or None to keep current
            y: New Y-axis value, or None to keep current
        """
        if x is not None:
            self.left_x = x
        if y is not None:
            self.left_y = y

    def update_right_stick(self, x: int | None = None, y: int | None = None):
        """
        Update right stick state.

        Args:
            x: New X-axis value, or None to keep current
            y: New Y-axis value, or None to keep current
        """
        if x is not None:
            self.right_x = x
        if y is not None:
            self.right_y = y

    def _get_stick_movement_gameplay_impl(
        self, stick_x: int, stick_y: int, stick_name: str = "Stick"
    ) -> tuple[int, int] | None:
        """
        Shared implementation for gameplay movement with settling and direction lock.

        Args:
            stick_x: Raw X axis value for the stick
            stick_y: Raw Y axis value for the stick
            stick_name: Name for debug logging (e.g., "Left stick", "Right stick")

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        # Convert analog to digital
        dx, dy = self.analog_to_8way(stick_x, stick_y)

        # Stick released - reset all state (unlocks direction)
        if dx == 0 and dy == 0:
            self.last_gameplay_move_time = -1.0
            self.gameplay_is_repeating = False
            self.last_gameplay_direction = (0, 0)
            self._settling_start_time = -1.0
            return None

        current_time = time.time()

        # Settling period: let stick reach intended position before locking direction
        settling_period = GameConfig.ANALOG_SETTLING_PERIOD

        # First deflection from center - start settling period
        if self.last_gameplay_move_time < 0.0:
            if self._settling_start_time < 0.0:
                self._settling_start_time = current_time
                logging.debug(f"{stick_name} settling started, current direction: {dx},{dy}")
                return None  # Don't move yet, wait for settling

            # Check if settling period is complete
            if current_time - self._settling_start_time < settling_period:
                # Still settling - update tracked direction but don't move
                logging.debug(
                    f"{stick_name} still settling ({(current_time - self._settling_start_time)*1000:.1f}ms), direction: {dx},{dy}"
                )
                return None

            # Settling complete - NOW lock direction and give movement
            self.last_gameplay_move_time = current_time
            self.gameplay_is_repeating = False
            self.last_gameplay_direction = (dx, dy)  # Lock this direction
            self._settling_start_time = -1.0
            logging.debug(f"{stick_name} settling complete, LOCKED direction: {dx},{dy}")
            return (dx, dy)

        # Direction locking: use locked direction OR current direction based on setting
        if self.direction_locking:
            # Use LOCKED direction, ignore direction changes while held
            use_dx, use_dy = self.last_gameplay_direction
        else:
            # No locking - use current direction (more responsive but may cause multi-moves)
            use_dx, use_dy = dx, dy
            self.last_gameplay_direction = (dx, dy)  # Update for next frame

        # Check time-based auto-repeat
        time_since_last = current_time - self.last_gameplay_move_time

        if not self.gameplay_is_repeating:
            # Waiting for initial delay before repeat kicks in
            if time_since_last >= self.gameplay_initial_delay:
                self.last_gameplay_move_time = current_time
                self.gameplay_is_repeating = True
                return (use_dx, use_dy)
        else:
            # In auto-repeat mode - use repeat rate
            if time_since_last >= self.gameplay_repeat_rate:
                self.last_gameplay_move_time = current_time
                return (use_dx, use_dy)

        return None

    def get_left_stick_movement_gameplay(self, current_turn: int) -> tuple[int, int] | None:
        """
        Get left stick movement for GAMEPLAY with settling period before direction lock.

        Uses a brief settling period (30ms) before locking direction. This allows
        the stick to reach its intended position before we commit to a direction,
        preventing early partial deflections from locking to cardinals when
        the user intended a diagonal.

        Behavior:
        - First deflection: start settling timer, no movement yet
        - During settling (30ms): track current direction but don't move
        - After settling: lock direction, give movement, start auto-repeat cycle
        - Direction change while held: IGNORED after lock (prevents multi-move)
        - Stick release: unlock direction, reset state

        Args:
            current_turn: Unused, kept for API compatibility

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        return self._get_stick_movement_gameplay_impl(self.left_x, self.left_y, "Left stick")

    def _get_stick_movement_menu_impl(self, stick_x: int, stick_y: int) -> tuple[int, int] | None:
        """
        Shared implementation for menu navigation with 4-way input and auto-repeat.

        Args:
            stick_x: Raw X axis value for the stick
            stick_y: Raw Y axis value for the stick

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        # Convert analog to 4-way digital (no diagonals for menus)
        dx, dy = self.analog_to_4way(stick_x, stick_y)

        # Stick released - reset all state (consistent with gameplay behavior)
        # This allows immediate movement on re-push after release
        if dx == 0 and dy == 0:
            self.last_menu_move_time = -1.0
            self.menu_is_repeating = False
            self.last_menu_direction = (0, 0)
            return None

        # Detect direction change (opposite direction pressed)
        direction_changed = False
        if self.last_menu_direction != (0, 0):
            # Check if moved in OPPOSITE direction (e.g., was up, now down)
            if (dx != 0 and dx != self.last_menu_direction[0]) or (
                dy != 0 and dy != self.last_menu_direction[1]
            ):
                direction_changed = True

        # Time-based auto-repeat logic
        current_time = time.time()
        time_since_last = current_time - self.last_menu_move_time

        # If direction changed or first move ever, treat as new input
        if direction_changed or self.last_menu_move_time < 0.0:
            # First move OR direction changed - immediate
            self.last_menu_move_time = current_time
            self.menu_is_repeating = False
            self.last_menu_direction = (dx, dy)
            return (dx, dy)

        if not self.menu_is_repeating:
            # Waiting for initial repeat delay
            if time_since_last >= self.menu_initial_delay:
                self.last_menu_move_time = current_time
                self.menu_is_repeating = True
                self.last_menu_direction = (dx, dy)
                return (dx, dy)
        else:
            # In auto-repeat mode - use faster repeat rate
            if time_since_last >= self.menu_repeat_rate:
                self.last_menu_move_time = current_time
                self.last_menu_direction = (dx, dy)
                return (dx, dy)

        return None

    def get_left_stick_movement_menu(self) -> tuple[int, int] | None:
        """
        Get left stick movement for MENUS (time-based auto-repeat, 4-way only).

        Menus use 4-way (cardinals only) because diagonals don't make sense -
        you don't want "mostly left, bit up" to both navigate AND change a setting.

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        return self._get_stick_movement_menu_impl(self.left_x, self.left_y)

    def reset_movement_gating(self):
        """Reset gameplay movement gating (useful when switching contexts or blocked movement)."""
        self.last_gameplay_move_time = -1.0
        self.gameplay_is_repeating = False
        self.last_gameplay_direction = (0, 0)
        self._settling_start_time = -1.0  # Also reset settling period

    def reset_menu_navigation(self):
        """Reset menu navigation auto-repeat state."""
        self.last_menu_move_time = -1.0  # Reset to "never moved" state
        self.menu_is_repeating = False
        self.last_menu_direction = (0, 0)

    def reset_cursor_movement(self):
        """Reset cursor movement state (useful when exiting look/targeting mode)."""
        self.last_cursor_move_time = -1.0
        self.cursor_is_repeating = False
        self.last_cursor_direction = (0, 0)
        self._cursor_settling_start_time = -1.0

    def _get_stick_movement_cursor_impl(self, stick_x: int, stick_y: int) -> tuple[int, int] | None:
        """
        Shared implementation for cursor movement with settling period and direction locking.

        Used by both get_right_stick_movement() and get_left_stick_movement() to handle
        8-way cursor movement in look/targeting modes with auto-repeat.

        Args:
            stick_x: Raw X axis value for the stick
            stick_y: Raw Y axis value for the stick

        Returns:
            (dx, dy) tuple if cursor movement available, None otherwise
        """
        current_time = time.time()

        # Convert analog to digital
        dx, dy = self.analog_to_8way(stick_x, stick_y)

        # Return None if no input (and reset all state)
        if dx == 0 and dy == 0:
            self.last_cursor_move_time = -1.0
            self.cursor_is_repeating = False
            self.last_cursor_direction = (0, 0)
            self._cursor_settling_start_time = -1.0
            return None

        # Settling period: let stick reach intended position before locking direction
        settling_period = GameConfig.ANALOG_SETTLING_PERIOD

        if self.last_cursor_move_time < 0.0:
            # First deflection detected - start settling
            if self._cursor_settling_start_time < 0.0:
                self._cursor_settling_start_time = current_time
                return None  # Don't move yet, wait for settling

            # Check if settling period has elapsed
            if current_time - self._cursor_settling_start_time < settling_period:
                return None  # Still settling

            # Settling complete - NOW lock direction and allow movement
            self.last_cursor_direction = (dx, dy)
            self.last_cursor_move_time = current_time
            self._cursor_settling_start_time = -1.0  # Reset settling
            self.cursor_is_repeating = False
            return (dx, dy)

        # Direction locking: if direction changed while held, IGNORE (use locked direction)
        if (dx, dy) != self.last_cursor_direction:
            dx, dy = self.last_cursor_direction
            if dx == 0 and dy == 0:
                return None

        # Auto-repeat logic for cursor
        time_since_last = current_time - self.last_cursor_move_time

        if not self.cursor_is_repeating:
            # Waiting for initial delay
            if time_since_last >= self.cursor_initial_delay:
                self.last_cursor_move_time = current_time
                self.cursor_is_repeating = True
                return (dx, dy)
        else:
            # In auto-repeat mode
            if time_since_last >= self.cursor_repeat_rate:
                self.last_cursor_move_time = current_time
                return (dx, dy)

        return None

    def get_right_stick_movement(self) -> tuple[int, int] | None:
        """
        Get right stick as 8-way cursor movement with auto-repeat.

        Includes settling period and direction locking like gameplay movement
        for precise diagonal targeting in look mode.

        Returns:
            (dx, dy) tuple if cursor movement available, None otherwise
        """
        return self._get_stick_movement_cursor_impl(self.right_x, self.right_y)

    def get_right_stick_position(self) -> tuple[float, float]:
        """
        Get right stick position (raw values for analog input).

        Returns:
            (normalized_x, normalized_y) in range -1.0 to 1.0
        """
        return self.apply_scaled_radial_deadzone(self.right_x, self.right_y)

    def get_right_stick_magnitude(self) -> float:
        """
        Get right stick magnitude (for detecting intentional movement).

        Returns:
            Magnitude in range 0.0 to 1.0 (after deadzone applied)
        """
        norm_x, norm_y = self.apply_scaled_radial_deadzone(self.right_x, self.right_y)
        return math.sqrt(norm_x**2 + norm_y**2)

    def get_left_stick_magnitude(self) -> float:
        """
        Get left stick magnitude (for detecting intentional movement).

        Used when swap_sticks is enabled to check if the "look mode" stick is deflected.

        Returns:
            Magnitude in range 0.0 to 1.0 (after deadzone applied)
        """
        norm_x, norm_y = self.apply_scaled_radial_deadzone(self.left_x, self.left_y)
        return math.sqrt(norm_x**2 + norm_y**2)

    def get_right_stick_movement_gameplay(self, current_turn: int) -> tuple[int, int] | None:
        """
        Get right stick movement for GAMEPLAY with settling period before direction lock.

        Mirrors get_left_stick_movement_gameplay but for the right stick.
        Used when swap_sticks is enabled to use right stick for movement.

        Args:
            current_turn: Unused, kept for API compatibility

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        return self._get_stick_movement_gameplay_impl(self.right_x, self.right_y, "Right stick")

    def get_right_stick_movement_menu(self) -> tuple[int, int] | None:
        """
        Get right stick movement for MENUS (time-based auto-repeat, 4-way only).

        Mirrors get_left_stick_movement_menu but for the right stick.
        Used when swap_sticks is enabled to use right stick for menu navigation.

        Returns:
            (dx, dy) tuple if movement available, None otherwise
        """
        return self._get_stick_movement_menu_impl(self.right_x, self.right_y)

    def get_left_stick_movement(self) -> tuple[int, int] | None:
        """
        Get left stick as 8-way cursor movement with auto-repeat.

        Mirrors get_right_stick_movement but for the left stick.
        Used when swap_sticks is enabled to use left stick for cursor control in look mode.

        Returns:
            (dx, dy) tuple if cursor movement available, None otherwise
        """
        return self._get_stick_movement_cursor_impl(self.left_x, self.left_y)

    def check_trigger_pressed(self, value: int, is_right_trigger: bool) -> bool:
        """
        Check if trigger was just pressed (edge detection).

        Returns True only on the transition from unpressed to pressed,
        not continuously while held. This prevents repeated exploit firing.

        Args:
            value: Raw trigger value (0 to 32767)
            is_right_trigger: True for RT, False for LT

        Returns:
            True if trigger just crossed threshold, False otherwise
        """
        normalized = self.apply_trigger_deadzone(value)
        is_pressed_now = normalized > GameConfig.GAMEPAD_TRIGGER_THRESHOLD

        if is_right_trigger:
            was_pressed = self.right_trigger_pressed
            self.right_trigger_pressed = is_pressed_now
        else:
            was_pressed = self.left_trigger_pressed
            self.left_trigger_pressed = is_pressed_now

        # Return True only on rising edge (transition from unpressed to pressed)
        return is_pressed_now and not was_pressed
