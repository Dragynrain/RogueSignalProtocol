"""
Achievement popup system for RogueSignalProtocol.

Displays small, unobtrusive achievement notifications using the same
rendering principles as the dialogue system but with smaller dimensions
and auto-dismiss functionality.
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional, List
import tcod.console
import tcod.constants

from game_coordinate_helpers import CoordinateHelpers
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe
from game_achievements import AchievementManager, ALL_ACHIEVEMENTS, Achievement

logger = logging.getLogger(__name__)

from game_config import GameConfig

# Popup configuration loaded from JSON
def get_popup_width():
    return GameConfig._get_required("ui.achievement_popup_width")

def get_popup_height():
    return GameConfig._get_required("ui.achievement_popup_height")

def get_popup_duration():
    return GameConfig._get_required("ui.achievement_popup_duration")

def get_popup_fade_duration():
    return GameConfig._get_required("ui.achievement_popup_fade_duration")

def get_max_description_lines():
    return GameConfig._get_required("ui.achievement_popup_max_description_lines")


@dataclass
class AchievementPopup:
    """Data structure for an achievement popup."""

    achievement_id: str
    achievement: Achievement
    timestamp: float  # When the popup was created

    def should_dismiss(self) -> bool:
        """Check if this popup should be auto-dismissed."""
        elapsed = time.time() - self.timestamp
        return elapsed >= get_popup_duration()

    def get_alpha(self) -> int:
        """
        Get alpha value for fade-in/fade-out effect.

        Returns:
            Alpha value (0-255) for transparency
        """
        elapsed = time.time() - self.timestamp

        # Fade in
        fade_duration = get_popup_fade_duration()
        if elapsed < fade_duration:
            progress = elapsed / fade_duration
            return int(255 * progress)

        # Fully visible
        elif elapsed < get_popup_duration() - fade_duration:
            return 255

        # Fade out
        else:
            remaining = get_popup_duration() - elapsed
            progress = remaining / fade_duration
            return max(0, int(255 * progress))


class AchievementPopupManager:
    """
    Manages achievement popup display and auto-dismiss.

    Works with AchievementManager to show popups for newly unlocked achievements.
    Handles popup queue, rendering, and auto-dismiss timing.
    """

    def __init__(self):
        """Initialize the popup manager."""
        self.active_popup: Optional[AchievementPopup] = None
        self.popup_queue: List[str] = []  # Achievement IDs waiting to be shown

    def check_and_show_popups(self) -> None:
        """
        Check for new achievements from AchievementManager and queue them.

        This is called each frame to check if new achievements are ready to display.
        """
        while AchievementManager.has_pending_popups():
            achievement_id = AchievementManager.get_next_popup()
            if achievement_id:
                self.popup_queue.append(achievement_id)

    def update(self) -> None:
        """
        Update popup state - handle auto-dismiss and show next queued popup.

        This is called each frame from the main game loop.
        """
        # Check and show any new achievements
        self.check_and_show_popups()

        # Handle active popup
        if self.active_popup:
            if self.active_popup.should_dismiss():
                logger.info(f"Auto-dismissing achievement popup: {self.active_popup.achievement_id}")
                self.active_popup = None

        # Show next queued popup if none active
        if not self.active_popup and self.popup_queue:
            achievement_id = self.popup_queue.pop(0)
            self.show_popup(achievement_id)

    def show_popup(self, achievement_id: str) -> None:
        """
        Show a popup for a specific achievement.

        Args:
            achievement_id: ID of the achievement to display
        """
        achievement = ALL_ACHIEVEMENTS.get(achievement_id)
        if not achievement:
            logger.error(f"Unknown achievement ID: {achievement_id}")
            return

        self.active_popup = AchievementPopup(
            achievement_id=achievement_id,
            achievement=achievement,
            timestamp=time.time()
        )
        logger.info(f"Showing achievement popup: {achievement.name}")

    def dismiss_active_popup(self) -> None:
        """Manually dismiss the active popup (e.g., user pressed a key)."""
        if self.active_popup:
            logger.info(f"Manually dismissed achievement popup: {self.active_popup.achievement_id}")
            self.active_popup = None

    def has_active_popup(self) -> bool:
        """Check if there's a popup currently being displayed."""
        return self.active_popup is not None

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the active achievement popup.

        Args:
            console: TCOD console to render to
        """
        if not self.active_popup:
            return

        achievement = self.active_popup.achievement

        # Get popup dimensions from config
        popup_width = get_popup_width()
        popup_height = get_popup_height()

        # Center the popup
        box_x, box_y = CoordinateHelpers.center_box(
            popup_width, popup_height, console.width, console.height
        )

        # Set popup area to opaque (critical for graphics mode)
        CoordinateHelpers.set_alpha_region(
            console, x=box_x, y=box_y, width=popup_width, height=popup_height, alpha=255
        )

        # Color scheme using consolidated colors
        from game_entities import Colors
        border_color = Colors.NEON_GOLD  # Consolidated from achievement_popup.border
        bg_color = Colors.POPUP  # Consolidated from achievement_popup.background to backgrounds.popup
        title_color = Colors.NEON_GOLD  # Consolidated from achievement_popup.title
        achievement_name_color = Colors.PURE_WHITE  # Consolidated from achievement_popup.name
        description_color = ensure_color_tuple(GameConfig._get_required("colors.achievement_popup.description"))

        # Draw box background and border
        from game_rendering_core import draw_bordered_box
        draw_bordered_box(console, box_x, box_y, popup_width, popup_height, border_color, bg_color)

        # Render title with icon
        title_text = f"{achievement.icon} ACHIEVEMENT UNLOCKED!"
        title_x = box_x + (popup_width - len(title_text)) // 2
        render_char_safe(console, title_x, box_y + 1, title_text,
                        fg=title_color, bg=bg_color)

        # Render achievement name (centered)
        name_x = box_x + (popup_width - len(achievement.name)) // 2
        render_char_safe(console, name_x, box_y + 3, achievement.name,
                        fg=achievement_name_color, bg=bg_color)

        # Render description (word-wrapped using TCOD's built-in wrapping)
        max_desc_lines = get_max_description_lines()
        # Note: TCOD's print() with LEFT alignment doesn't center individual wrapped lines,
        # so we still need to calculate centering for multi-line text. However, TCOD handles
        # the wrapping itself. For centered text, we'd need to wrap manually or accept left-aligned.
        # Let's use TCOD's wrapping with left alignment for consistency.
        console.print(
            x=box_x + 2,
            y=box_y + 4,
            string=achievement.description,
            fg=description_color,
            width=popup_width - 4,
            alignment=tcod.constants.CENTER
        )

        # Optionally show hint at bottom (very subtle)
        hint_text = "(press any key or click)"
        hint_x = box_x + (popup_width - len(hint_text)) // 2
        hint_color = ensure_color_tuple(GameConfig._get_required("colors.achievement_popup.hint"))
        render_char_safe(console, hint_x, box_y + popup_height - 1, hint_text,
                        fg=hint_color, bg=bg_color)



# Global popup manager instance (initialized by GameEngine)
_popup_manager: Optional[AchievementPopupManager] = None


def initialize_popup_manager():
    """Initialize the global popup manager."""
    global _popup_manager
    _popup_manager = AchievementPopupManager()
    logger.info("Achievement popup manager initialized")


def get_popup_manager() -> Optional[AchievementPopupManager]:
    """Get the global popup manager instance."""
    return _popup_manager


def show_achievement_popup(achievement_id: str):
    """
    Convenience function to show an achievement popup.

    Args:
        achievement_id: ID of the achievement to display
    """
    if _popup_manager:
        _popup_manager.show_popup(achievement_id)
    else:
        logger.warning("Popup manager not initialized")


def update_popups():
    """Convenience function to update popup state (called each frame)."""
    if _popup_manager:
        _popup_manager.update()


def render_popups(console: tcod.console.Console):
    """
    Convenience function to render active popup.

    Args:
        console: TCOD console to render to
    """
    if _popup_manager:
        _popup_manager.render(console)


def dismiss_active_popup():
    """Convenience function to manually dismiss the active popup."""
    if _popup_manager:
        _popup_manager.dismiss_active_popup()


def has_active_popup() -> bool:
    """Convenience function to check if there's an active popup."""
    if _popup_manager:
        return _popup_manager.has_active_popup()
    return False
