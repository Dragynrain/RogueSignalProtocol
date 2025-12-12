"""
Tests for game_input_device_tracker.py - Input Device Type Tracking

Tests the module that tracks which input device (keyboard/mouse vs gamepad)
was last used, enabling dynamic help text that matches the active device.
"""


class TestInputDeviceTracker:
    """Tests for device type tracking."""

    def setup_method(self):
        """Reset tracker state before each test."""
        from game_input_device_tracker import reset_to_default

        reset_to_default()

    def teardown_method(self):
        """Reset tracker state after each test to prevent pollution."""
        from game_input_device_tracker import reset_to_default

        reset_to_default()

    def test_defaults_to_keyboard(self):
        """Default device should be KEYBOARD (safest assumption)."""
        from game_input_device_tracker import InputDeviceType, get_last_device, reset_to_default

        # Use public API to reset
        reset_to_default()

        assert get_last_device() == InputDeviceType.KEYBOARD

    def test_set_gamepad(self):
        """Setting device to GAMEPAD should persist."""
        from game_input_device_tracker import InputDeviceType, get_last_device, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)

        assert get_last_device() == InputDeviceType.GAMEPAD

    def test_set_keyboard(self):
        """Setting device to KEYBOARD should persist."""
        from game_input_device_tracker import InputDeviceType, get_last_device, set_last_device

        # First set to gamepad
        set_last_device(InputDeviceType.GAMEPAD)
        # Then switch back to keyboard
        set_last_device(InputDeviceType.KEYBOARD)

        assert get_last_device() == InputDeviceType.KEYBOARD

    def test_is_gamepad_active_true(self):
        """is_gamepad_active() returns True when GAMEPAD."""
        from game_input_device_tracker import InputDeviceType, is_gamepad_active, set_last_device

        set_last_device(InputDeviceType.GAMEPAD)

        assert is_gamepad_active() is True

    def test_is_gamepad_active_false(self):
        """is_gamepad_active() returns False when KEYBOARD."""
        from game_input_device_tracker import InputDeviceType, is_gamepad_active, set_last_device

        set_last_device(InputDeviceType.KEYBOARD)

        assert is_gamepad_active() is False

    def test_switching_between_devices(self):
        """Switching between devices updates state correctly."""
        from game_input_device_tracker import InputDeviceType, get_last_device, set_last_device

        # Start with keyboard
        set_last_device(InputDeviceType.KEYBOARD)
        assert get_last_device() == InputDeviceType.KEYBOARD

        # Switch to gamepad
        set_last_device(InputDeviceType.GAMEPAD)
        assert get_last_device() == InputDeviceType.GAMEPAD

        # Back to keyboard
        set_last_device(InputDeviceType.KEYBOARD)
        assert get_last_device() == InputDeviceType.KEYBOARD

        # Back to gamepad
        set_last_device(InputDeviceType.GAMEPAD)
        assert get_last_device() == InputDeviceType.GAMEPAD

    def test_enum_values_distinct(self):
        """Enum values should be distinct."""
        from game_input_device_tracker import InputDeviceType

        assert InputDeviceType.KEYBOARD != InputDeviceType.GAMEPAD
        assert InputDeviceType.KEYBOARD.value != InputDeviceType.GAMEPAD.value


class TestInputDeviceTrackerReset:
    """Tests for reset functionality."""

    def test_reset_to_default(self):
        """reset_to_default() should set device back to KEYBOARD."""
        from game_input_device_tracker import (
            InputDeviceType,
            get_last_device,
            reset_to_default,
            set_last_device,
        )

        # Set to gamepad
        set_last_device(InputDeviceType.GAMEPAD)
        assert get_last_device() == InputDeviceType.GAMEPAD

        # Reset
        reset_to_default()
        assert get_last_device() == InputDeviceType.KEYBOARD
