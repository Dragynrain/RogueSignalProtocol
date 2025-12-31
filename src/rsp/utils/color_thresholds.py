#!/usr/bin/env python3
"""
Rogue Signal Protocol - Color Threshold Manager

Centralizes all color threshold logic for status indicators across the game.
Eliminates duplication of threshold values and color selection logic that was
previously scattered across multiple rendering files.

This module provides:
- Consistent threshold values for CPU, heat, trace status indicators
- Centralized color selection logic based on thresholds
- Player status color prioritization (critical > warning > effects > normal)
"""


from rsp.entities.base import Colors


class ColorThresholdManager:
    """
    Manages color thresholds for status indicators throughout the game.

    Previously, these thresholds were duplicated across:
    - game_rendering_ui.py (_get_cpu_color, _get_heat_color, _get_trace_color)
    - game_rendering_glyphs.py (_get_player_color)
    - game_rendering_graphics.py (player status checks)

    Now centralized here for consistency and maintainability.
    """

    # CPU thresholds (lower is worse)
    CPU_CRITICAL = 30  # Red threshold
    CPU_WARNING = 60  # Yellow threshold

    # Heat thresholds (higher is worse)
    HEAT_CRITICAL = 80  # Red threshold
    HEAT_WARNING = 60  # Yellow threshold

    # Trace thresholds (higher is worse)
    TRACE_CRITICAL = 75  # Red threshold
    TRACE_WARNING = 50  # Yellow threshold

    @classmethod
    def get_cpu_color(cls, cpu: int) -> tuple[int, int, int]:
        """
        Get threshold-based color for CPU display.

        Args:
            cpu: Current CPU value

        Returns:
            Color tuple: Red if <30, Yellow if <60, Green otherwise
        """
        if cpu < cls.CPU_CRITICAL:
            return Colors.RED
        elif cpu < cls.CPU_WARNING:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    @classmethod
    def get_heat_color(cls, heat: int) -> tuple[int, int, int]:
        """
        Get threshold-based color for heat display.

        Args:
            heat: Current heat value

        Returns:
            Color tuple: Red if >80, Yellow if >60, Green otherwise
        """
        if heat > cls.HEAT_CRITICAL:
            return Colors.RED
        elif heat > cls.HEAT_WARNING:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    @classmethod
    def get_trace_color(cls, trace_level: float) -> tuple[int, int, int]:
        """
        Get threshold-based color for trace display.

        Args:
            trace_level: Current trace level (0-100)

        Returns:
            Color tuple: Red if >75, Yellow if >50, Green otherwise
        """
        if trace_level > cls.TRACE_CRITICAL:
            return Colors.RED
        elif trace_level > cls.TRACE_WARNING:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    @classmethod
    def is_player_critical(cls, player) -> bool:
        """
        Check if player is in critical status (any stat in red zone).

        Args:
            player: Player instance with cpu, heat, trace_level attributes

        Returns:
            True if any stat is in critical range
        """
        return (
            player.cpu < cls.CPU_CRITICAL
            or player.heat > cls.HEAT_CRITICAL
            or player.trace_level > cls.TRACE_CRITICAL
        )

    @classmethod
    def is_player_warning(cls, player) -> bool:
        """
        Check if player is in warning status (any stat in yellow zone, but not critical).

        Args:
            player: Player instance with cpu, heat, trace_level attributes

        Returns:
            True if any stat is in warning range but none are critical
        """
        if cls.is_player_critical(player):
            return False

        return (
            player.cpu < cls.CPU_WARNING
            or player.heat > cls.HEAT_WARNING
            or player.trace_level > cls.TRACE_WARNING
        )

    @classmethod
    def get_player_color(cls, player) -> tuple[int, int, int]:
        """
        Get player color based on current state with priority.

        Priority order:
        1. Critical status (Red)
        2. Invisible effect (Yellow)
        3. Virus effect (Green)
        4. Movement slowed (Cyan)
        5. Normal (White)

        Args:
            player: Player instance

        Returns:
            Color tuple based on highest priority condition
        """
        # Priority 1: Critical status - Red
        if cls.is_player_critical(player):
            return Colors.RED

        # Priority 2: Warning status - Yellow (invisibility takes precedence)
        if player.is_invisible():
            return Colors.YELLOW

        # Priority 3: Virus effect - Green
        if player.has_active_effect("virus_turns"):
            return Colors.VIRUS

        # Priority 4: Slow effect - Cyan
        if player.has_active_effect("movement_slowed_turns"):
            return Colors.CYAN

        # Default: White
        return Colors.WHITE

    @classmethod
    def get_status_summary(cls, player) -> str:
        """
        Get a text summary of player's current status.

        Args:
            player: Player instance

        Returns:
            Status string like "Critical", "Warning", "Stable", etc.
        """
        if cls.is_player_critical(player):
            return "CRITICAL"
        elif cls.is_player_warning(player):
            return "WARNING"
        elif player.is_invisible():
            return "CLOAKED"
        elif player.has_active_effect("virus_turns"):
            return "INFECTED"
        elif player.has_active_effect("movement_slowed_turns"):
            return "SLOWED"
        else:
            return "STABLE"
