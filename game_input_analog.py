"""
game_input_analog.py - Analog Stick Input Handling

Handles gamepad analog stick input with deadzone processing and analog-to-digital
conversion for tile-based movement.

Key features:
- Scaled radial deadzone (industry standard, smooth gradient)
- Analog-to-digital conversion for 8-way tile movement
- Movement cooldown to prevent spam from continuous axis events
- Support for both left and right sticks (movement vs cursor)

Based on TCOD research and SDL best practices.
"""

import math
import time

# SDL joystick axis range constants
SDL_JOYSTICK_AXIS_MAX = 32768.0  # Maximum absolute value for joystick axes (signed -32768 to 32767)
SDL_JOYSTICK_TRIGGER_MAX = 32767.0  # Maximum value for trigger axes (unsigned 0 to 32767)


class AnalogStickHandler:
    """
    Processes analog stick input from gamepad controllers.

    Handles deadzone filtering, analog-to-digital conversion, and movement timing
    for tile-based roguelike gameplay.
    """

    def __init__(self, deadzone: float = 0.15, threshold: float = 0.5, move_cooldown: float = 0.15):
        """
        Initialize analog stick handler.

        Args:
            deadzone: Minimum stick deflection to register (0.0-1.0, default 15%)
            threshold: Stick deflection required for digital movement (0.0-1.0, default 50%)
            move_cooldown: Minimum time between tile moves in seconds (default 150ms)
        """
        self.deadzone = deadzone
        self.threshold = threshold
        self.move_cooldown = move_cooldown

        # Current stick states (raw values from SDL)
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0

        # Movement timing
        self.last_move_time = 0.0

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
        normalized_magnitude = (magnitude - self.deadzone) / (1.0 - self.deadzone)
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
        Convert analog stick input to 8-way digital direction.

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

        # Convert to digital based on threshold
        dx = 0
        dy = 0

        if norm_x > self.threshold:
            dx = 1
        elif norm_x < -self.threshold:
            dx = -1

        if norm_y > self.threshold:
            dy = 1
        elif norm_y < -self.threshold:
            dy = -1

        return (dx, dy)

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

        # Rescale
        return (normalized - self.deadzone) / (1.0 - self.deadzone)

    def can_move(self) -> bool:
        """
        Check if enough time has passed for another tile movement.

        Returns:
            True if cooldown has elapsed, False otherwise
        """
        now = time.time()
        if now - self.last_move_time >= self.move_cooldown:
            self.last_move_time = now
            return True
        return False

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

    def get_left_stick_movement(self) -> tuple[int, int] | None:
        """
        Get left stick as 8-way movement delta, respecting cooldown.

        Returns:
            (dx, dy) tuple if movement available and cooldown elapsed, None otherwise
        """
        # Convert analog to digital
        dx, dy = self.analog_to_8way(self.left_x, self.left_y)

        # Return None if no input
        if dx == 0 and dy == 0:
            return None

        # Check cooldown
        if not self.can_move():
            return None

        return (dx, dy)

    def get_right_stick_position(self) -> tuple[float, float]:
        """
        Get right stick position (for cursor control, no cooldown).

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

    def reset_movement_cooldown(self):
        """Reset movement cooldown (useful when switching contexts)."""
        self.last_move_time = 0.0
