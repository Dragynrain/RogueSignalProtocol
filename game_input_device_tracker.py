"""
game_input_device_tracker.py - Input Device Type Tracking

Tracks which input device (keyboard/mouse vs gamepad) was last used,
enabling dynamic help text that shows hints appropriate for the active device.

Usage:
    # In input handlers - call when receiving input
    from game_input_device_tracker import InputDeviceType, set_last_device
    set_last_device(InputDeviceType.KEYBOARD)  # On keyboard/mouse input
    set_last_device(InputDeviceType.GAMEPAD)   # On gamepad input

    # In help text generation - query current device
    from game_input_device_tracker import get_last_device, is_gamepad_active
    if is_gamepad_active():
        hint = "Press A to confirm"
    else:
        hint = "Press Enter to confirm"
"""

from enum import Enum, auto


class InputDeviceType(Enum):
    """Input device categories for help text switching."""

    KEYBOARD = auto()  # Keyboard and mouse (users typically use both together)
    GAMEPAD = auto()   # Gamepad/controller


# Module-level state - simple and thread-safe for single-threaded game loop
_last_device: InputDeviceType = InputDeviceType.KEYBOARD


def get_last_device() -> InputDeviceType:
    """Get the last input device type used."""
    return _last_device


def set_last_device(device: InputDeviceType) -> None:
    """
    Update the last input device type.

    Call this at the start of input handlers to track device usage.

    Args:
        device: The device type that just received input
    """
    global _last_device
    _last_device = device


def is_gamepad_active() -> bool:
    """
    Check if gamepad is the currently active input device.

    Convenience function for conditionals in help text generation.

    Returns:
        True if last input was from gamepad, False for keyboard/mouse
    """
    return _last_device == InputDeviceType.GAMEPAD


def reset_to_default() -> None:
    """
    Reset device tracking to default (KEYBOARD).

    Useful for testing or when starting a new game session.
    """
    global _last_device
    _last_device = InputDeviceType.KEYBOARD
