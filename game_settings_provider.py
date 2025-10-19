#!/usr/bin/env python3
"""
Settings Provider Protocol
Defines interface for settings access without tight coupling to GameSettings class.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SettingsProvider(Protocol):
    """
    Protocol for accessing game settings.

    This allows components to depend on settings interface rather than
    concrete GameSettings class, improving testability and reducing coupling.

    Any class implementing these properties can be used as a settings provider.
    """

    @property
    def graphics_mode(self) -> str:
        """
        Get current graphics mode.

        Returns:
            "graphics" or "glyph"
        """
        ...

    @property
    def audio_enabled(self) -> bool:
        """
        Check if audio is enabled.

        Returns:
            True if audio should play, False otherwise
        """
        ...

    @property
    def music_enabled(self) -> bool:
        """
        Check if music is enabled.

        Returns:
            True if music should play, False otherwise
        """
        ...

    def get_volume_percent(self, volume_type: str) -> int:
        """
        Get volume percentage for a specific type.

        Args:
            volume_type: "master", "sfx", or "music"

        Returns:
            Volume percentage (0-100)
        """
        ...

    def set_volume_percent(self, volume_type: str, percent: int) -> None:
        """
        Set volume percentage for a specific type.

        Args:
            volume_type: "master", "sfx", or "music"
            percent: Volume percentage (0-100)
        """
        ...
