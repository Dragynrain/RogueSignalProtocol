"""
Rogue Signal Protocol - Achievements Menu

Displays all unlocked and locked achievements organized by category.
Shows progress tracking and handles hidden achievements.
"""

import tcod

from game_achievements import AchievementManager
from game_config import GameConfig
from game_entities import Colors
from game_screen_utilities import ScreenRenderingUtils
from game_ui import UniversalInputHandler, render_char_safe


class AchievementsMenu:
    """Achievements viewer menu for main menu."""

    def __init__(self):
        self.scroll_offset = 0
        self.max_visible_lines = 35  # Lines that fit on screen

    def render(self, console: tcod.console.Console) -> None:
        """Render the achievements screen with all categories."""
        console.clear()

        # Get unlock progress
        unlocked_count, total_count = AchievementManager.get_unlock_progress()

        # Title with progress
        title = f"ACHIEVEMENTS ({unlocked_count}/{total_count} UNLOCKED)"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)

        # Render achievements by category
        all_lines = self._build_achievement_lines()

        # Render visible portion based on scroll
        start_y = 5
        visible_lines = all_lines[self.scroll_offset : self.scroll_offset + self.max_visible_lines]

        for i, line_data in enumerate(visible_lines):
            render_char_safe(
                console, line_data["x"], start_y + i, line_data["text"], fg=line_data["color"]
            )

        # Scroll indicator
        if len(all_lines) > self.max_visible_lines:
            total_pages = (len(all_lines) + self.max_visible_lines - 1) // self.max_visible_lines
            current_page = (self.scroll_offset // self.max_visible_lines) + 1
            scroll_text = (
                f"Page {current_page}/{total_pages}  │  ↑↓ Scroll  │  PgUp/PgDn: Fast scroll"
            )
            render_char_safe(
                console,
                GameConfig.SCREEN_WIDTH // 2 - len(scroll_text) // 2,
                GameConfig.SCREEN_HEIGHT - 4,
                scroll_text,
                fg=Colors.LIGHT_GRAY,
            )

        # Instructions
        instructions = "ESC/Right-Click: Back  │  Mouse Wheel: Scroll"
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, instructions, fg=Colors.CYAN)

    def _build_achievement_lines(self) -> list:
        """Build all achievement lines organized by category."""
        lines = []

        # Category order and titles
        categories = [
            ("combat", "COMBAT MASTERY"),
            ("stealth", "STEALTH MASTERY"),
            ("efficiency", "EFFICIENCY & SPEED"),
            ("challenge", "CHALLENGE RUNS"),
            ("mastery", "MASTERY & COLLECTION"),
            ("lifetime", "LIFETIME"),
        ]

        for category_id, category_title in categories:
            # Category header
            lines.append(
                {"x": 2, "text": f"═══ {category_title} ═══", "color": Colors.ELECTRIC_PURPLE}
            )
            lines.append({"x": 2, "text": "", "color": Colors.WHITE})  # Blank line

            # Get achievements for this category
            achievements = AchievementManager.get_achievements_by_category(category_id)

            for achievement in achievements:
                is_unlocked = AchievementManager.is_unlocked(achievement.id)

                # Handle hidden achievements
                if achievement.hidden and not is_unlocked:
                    # Show as locked and mysterious
                    icon = "🔒"
                    name = "???"
                    description = "Hidden achievement - unlock to reveal"
                    color = Colors.DARK_GRAY
                else:
                    # Show full details
                    icon = "[X]" if is_unlocked else "[ ]"
                    name = achievement.name
                    description = achievement.description
                    color = Colors.GREEN if is_unlocked else Colors.DARK_GRAY

                # Achievement line with icon
                achievement_text = f"  {icon} {achievement.icon} {name}"
                lines.append({"x": 4, "text": achievement_text, "color": color})

                # Description (indented, word-wrapped)
                desc_lines = self._wrap_text(description, 70)
                for desc_line in desc_lines:
                    lines.append({"x": 10, "text": desc_line, "color": Colors.LIGHT_GRAY})

                lines.append({"x": 2, "text": "", "color": Colors.WHITE})  # Blank line

        return lines

    def _wrap_text(self, text: str, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        if len(text) <= max_width:
            return [text]

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            space_needed = word_length + (1 if current_line else 0)

            if current_length + space_needed <= max_width:
                current_line.append(word)
                current_length += space_needed
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def handle_input(self, event) -> str:
        """Handle achievements menu input. Returns 'back' or ''."""
        # Scroll with arrows
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.KeySym.UP or event.sym == tcod.event.KeySym.W:
                self.scroll_offset = max(0, self.scroll_offset - 1)
                return ""
            elif event.sym == tcod.event.KeySym.DOWN or event.sym == tcod.event.KeySym.S:
                all_lines = self._build_achievement_lines()
                max_scroll = max(0, len(all_lines) - self.max_visible_lines)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                return ""
            elif event.sym == tcod.event.KeySym.PAGEUP:
                self.scroll_offset = max(0, self.scroll_offset - 10)
                return ""
            elif event.sym == tcod.event.KeySym.PAGEDOWN:
                all_lines = self._build_achievement_lines()
                max_scroll = max(0, len(all_lines) - self.max_visible_lines)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 10)
                return ""

        # Exit with ESC or any other key
        if UniversalInputHandler.is_escape_key(event):
            return "back"

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion (no-op for achievements menu)."""
        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - right-click to return to main menu."""
        import tcod.event

        # Right-click = go back (standard behavior)
        if hasattr(event, "button") and event.button == tcod.event.MouseButton.RIGHT:
            return "back"

        # Left-click on empty space does nothing (removed confusing click-anywhere-to-exit)
        return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - scroll through achievements."""
        if hasattr(event, "y"):
            all_lines = self._build_achievement_lines()
            max_scroll = max(0, len(all_lines) - self.max_visible_lines)

            if event.y > 0:
                # Scroll up (towards top)
                self.scroll_offset = max(0, self.scroll_offset - 3)
            elif event.y < 0:
                # Scroll down (towards bottom)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 3)
            return True
        return False
