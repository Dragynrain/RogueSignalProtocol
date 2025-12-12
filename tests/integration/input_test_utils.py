"""
Common utilities for input testing across all screens.

This module provides helper classes and fixtures for creating test events
and verifying input behavior consistently across all integration tests.
"""

from contextlib import contextmanager
from unittest.mock import patch

import pytest
import tcod
import tcod.event
import tcod.sdl.joystick


class MockTime:
    """
    Mock time.time() for reliable testing of time-dependent behavior.

    Instead of using time.sleep() (which is flaky in CI), use this to:
    1. Control what time.time() returns
    2. Advance time instantly without actually waiting

    Usage:
        with MockTime.frozen() as mock_time:
            # time.time() returns 1000.0
            mock_time.advance(0.5)  # Now returns 1000.5
            mock_time.advance(0.1)  # Now returns 1000.6

        # Or as a fixture:
        def test_settling_period(mock_time):
            analog.get_movement()  # Uses initial time
            mock_time.advance(0.035)  # Advance past settling period
            analog.get_movement()  # Now sees time has passed
    """

    def __init__(self, start_time: float = 1000.0):
        self._current_time = start_time
        self._patcher = None

    def time(self) -> float:
        """Return the current mocked time."""
        return self._current_time

    def advance(self, seconds: float) -> float:
        """
        Advance the mocked time by the given number of seconds.

        Args:
            seconds: Time to advance (can be fractional, e.g., 0.035 for 35ms)

        Returns:
            The new current time
        """
        self._current_time += seconds
        return self._current_time

    def set(self, timestamp: float) -> None:
        """Set the mocked time to a specific value."""
        self._current_time = timestamp

    @classmethod
    @contextmanager
    def frozen(cls, start_time: float = 1000.0):
        """
        Context manager that freezes time.time() at a controllable value.

        Args:
            start_time: Initial time value (default 1000.0)

        Yields:
            MockTime instance for controlling time
        """
        mock = cls(start_time)
        with patch("time.time", mock.time):
            yield mock

    def __enter__(self):
        """Start patching time.time()."""
        self._patcher = patch("time.time", self.time)
        self._patcher.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop patching time.time()."""
        if self._patcher:
            self._patcher.stop()
        return False


@pytest.fixture
def mock_time():
    """
    Pytest fixture for mocking time.time().

    Usage:
        def test_auto_repeat(mock_time):
            # Do something at t=1000.0
            mock_time.advance(0.4)  # Advance to t=1000.4
            # Do something after delay
    """
    with MockTime.frozen() as mt:
        yield mt


class InputTestHelper:
    """Helper class for generating repetitive input tests."""

    @staticmethod
    def create_keyboard_event(key_sym, mod=tcod.event.Modifier.NONE):
        """Create a keyboard event."""
        return tcod.event.KeyDown(scancode=tcod.event.Scancode(key_sym), sym=key_sym, mod=mod)

    @staticmethod
    def create_dpad_event(direction, pressed=True):
        """Create a D-pad button event."""
        button_map = {
            "up": tcod.sdl.joystick.ControllerButton.DPAD_UP,
            "down": tcod.sdl.joystick.ControllerButton.DPAD_DOWN,
            "left": tcod.sdl.joystick.ControllerButton.DPAD_LEFT,
            "right": tcod.sdl.joystick.ControllerButton.DPAD_RIGHT,
        }
        return tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN" if pressed else "CONTROLLERBUTTONUP",
            which=0,
            button=button_map[direction],
            pressed=pressed,
        )

    @staticmethod
    def create_stick_event(stick, axis_name, value):
        """
        Create an analog stick axis event.

        Args:
            stick: 'left' or 'right'
            axis_name: 'x' or 'y'
            value: -32767 to 32767
        """
        axis_map = {
            ("left", "x"): tcod.sdl.joystick.ControllerAxis.LEFTX,
            ("left", "y"): tcod.sdl.joystick.ControllerAxis.LEFTY,
            ("right", "x"): tcod.sdl.joystick.ControllerAxis.RIGHTX,
            ("right", "y"): tcod.sdl.joystick.ControllerAxis.RIGHTY,
        }
        return tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=axis_map[(stick, axis_name)], value=value
        )

    @staticmethod
    def create_face_button_event(button, pressed=True):
        """Create a face button event (A/B/X/Y)."""
        button_map = {
            "a": tcod.sdl.joystick.ControllerButton.A,
            "b": tcod.sdl.joystick.ControllerButton.B,
            "x": tcod.sdl.joystick.ControllerButton.X,
            "y": tcod.sdl.joystick.ControllerButton.Y,
        }
        return tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN" if pressed else "CONTROLLERBUTTONUP",
            which=0,
            button=button_map[button],
            pressed=pressed,
        )

    @staticmethod
    def create_shoulder_button_event(button, pressed=True):
        """Create a shoulder button event (LB/RB)."""
        button_map = {
            "lb": tcod.sdl.joystick.ControllerButton.LEFTSHOULDER,
            "rb": tcod.sdl.joystick.ControllerButton.RIGHTSHOULDER,
        }
        return tcod.event.ControllerButton(
            type="CONTROLLERBUTTONDOWN" if pressed else "CONTROLLERBUTTONUP",
            which=0,
            button=button_map[button],
            pressed=pressed,
        )

    @staticmethod
    def create_trigger_event(trigger, value):
        """Create a trigger axis event (LT/RT)."""
        axis_map = {
            "lt": tcod.sdl.joystick.ControllerAxis.TRIGGERLEFT,
            "rt": tcod.sdl.joystick.ControllerAxis.TRIGGERRIGHT,
        }
        return tcod.event.ControllerAxis(
            type="CONTROLLERAXISMOTION", which=0, axis=axis_map[trigger], value=value
        )

    @staticmethod
    def create_mouse_wheel_event(y=0, x=0, flipped=False):
        """
        Create a mouse wheel event.

        Args:
            y: Vertical scroll amount (positive = up, negative = down)
            x: Horizontal scroll amount (positive = right, negative = left)
            flipped: Whether scroll direction is inverted
        """
        return tcod.event.MouseWheel(x=x, y=y, flipped=flipped)

    @staticmethod
    def simulate_controller_disconnect(mock_controller):
        """
        Configure a mock controller to behave as if it's been disconnected.

        When a controller is disconnected in SDL, accessing its properties
        raises an exception. This helper configures the mock to do the same.

        Args:
            mock_controller: Mock controller object to configure
        """
        # Configure mock to raise exception when .name is accessed
        # This simulates SDL behavior for invalid/disconnected controllers
        from unittest.mock import PropertyMock

        type(mock_controller).name = PropertyMock(
            side_effect=RuntimeError("Controller disconnected")
        )


class AutoRepeatTester:
    """Helper for testing auto-repeat behavior (press, hold, release)."""

    @staticmethod
    def test_press_hold_release_cycle(menu, create_event_func, expected_action):
        """
        Test complete press-hold-release cycle for auto-repeat.

        Args:
            menu: Menu object to test
            create_event_func: Function that returns (press_event, release_event)
            expected_action: Expected InputAction for navigation

        Returns:
            dict with test results
        """
        initial_selection = menu.selected_option
        press_event, release_event = create_event_func()

        # Phase 1: Initial press
        menu.handle_input(press_event)
        after_press = menu.selected_option

        # Phase 2: Verify button is held (for D-pad)
        if hasattr(menu, "gamepad_handler") and hasattr(press_event, "button"):
            button_held = menu.gamepad_handler.button_held is not None
        else:
            button_held = None

        # Phase 3: Release
        if release_event:
            menu.handle_input(release_event)
            if hasattr(menu, "gamepad_handler"):
                button_cleared = menu.gamepad_handler.button_held is None
            else:
                button_cleared = None
        else:
            button_cleared = None

        return {
            "initial": initial_selection,
            "after_press": after_press,
            "moved_on_press": after_press != initial_selection,
            "button_held": button_held,
            "button_cleared": button_cleared,
        }
