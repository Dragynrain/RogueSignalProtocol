"""
Rogue Signal Protocol - Achievements Menu

Displays all unlocked and locked achievements organized by category.
Shows progress tracking and handles hidden achievements.
"""

import tcod

from game_achievements import AchievementManager
from game_config import GameConfig
from game_entities import Colors
from game_help_hints import get_achievements_help
from game_menu_base import BaseMenu
from game_screen_utilities import ScreenRenderingUtils
from game_ui import render_char_safe


class AchievementsMenu(BaseMenu):
    """Achievements viewer menu for main menu."""

    # Per-screen scroll speed configuration
    ARROW_SCROLL_SPEED = 3  # Lines per arrow key press (default: 1, increased for faster scrolling)
    PAGE_SCROLL_SPEED = 35  # Lines per Page Up/Down (full page = max_visible_lines)
    WHEEL_SCROLL_SPEED = 5  # Lines per mouse wheel tick (default: 3)

    def __init__(self, background=None):
        super().__init__(background)
        self.scroll_offset = 0
        self.max_visible_lines = 35  # Lines that fit on screen

    def scroll_up(self):
        """Scroll achievements list up by configured speed."""
        self.scroll_offset = max(0, self.scroll_offset - self.ARROW_SCROLL_SPEED)

    def scroll_down(self):
        """Scroll achievements list down by configured speed."""
        all_lines = self._build_achievement_lines()
        max_scroll = max(0, len(all_lines) - self.max_visible_lines)
        self.scroll_offset = min(max_scroll, self.scroll_offset + self.ARROW_SCROLL_SPEED)

    def render(self, console: tcod.console.Console) -> None:
        """Render the achievements screen with all categories."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
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
            # Calculate current page based on last visible line (not just offset)
            # This ensures we show "Page 3/3" when at max scroll, not "Page 2/3"
            last_visible_line = min(
                self.scroll_offset + self.max_visible_lines - 1, len(all_lines) - 1
            )
            current_page = (last_visible_line // self.max_visible_lines) + 1
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

        # Instructions - dynamically reflects current bindings
        instructions = get_achievements_help(self.input_mapper)
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
            ("ascension", "ASCENSION"),
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

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS
    # ========================================================================

    def get_context(self):
        """Return input context for this menu."""
        from game_input_actions import InputContext

        return InputContext.ACHIEVEMENTS_SCREEN

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        from game_input_actions import InputAction

        # Navigation - scroll up/down
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self.scroll_up()
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self.scroll_down()
            return ""

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        # Page Up/Down (special keys + laptop diagonal keys)
        # PageUp/PageDown keys map to MOVE_NORTHEAST/MOVE_SOUTHEAST globally (laptop diagonals),
        # but in scrolling menus they should work as page navigation
        elif action in (InputAction.NAVIGATE_PAGE_UP, InputAction.MOVE_NORTHEAST):
            self.scroll_offset = max(0, self.scroll_offset - self.PAGE_SCROLL_SPEED)
            return ""
        elif action in (InputAction.NAVIGATE_PAGE_DOWN, InputAction.MOVE_SOUTHEAST):
            all_lines = self._build_achievement_lines()
            max_scroll = max(0, len(all_lines) - self.max_visible_lines)
            self.scroll_offset = min(max_scroll, self.scroll_offset + self.PAGE_SCROLL_SPEED)
            return ""

        # Home/End keys (scroll to top/bottom)
        # Home/End map to MOVE_NORTHWEST/MOVE_SOUTHWEST globally (laptop diagonals)
        elif action == InputAction.MOVE_NORTHWEST:
            self.scroll_offset = 0
            return ""
        elif action == InputAction.MOVE_SOUTHWEST:
            all_lines = self._build_achievement_lines()
            max_scroll = max(0, len(all_lines) - self.max_visible_lines)
            self.scroll_offset = max_scroll
            return ""

        return ""

    # ========================================================================
    # MOUSE HANDLING (override BaseMenu defaults)
    # ========================================================================

    def handle_right_click(self, event) -> str:
        """Handle right click - return to main menu."""
        return "back"

    def handle_mouse_wheel(self, event) -> str:
        """Handle mouse wheel - scroll through achievements."""
        if hasattr(event, "y"):
            all_lines = self._build_achievement_lines()
            max_scroll = max(0, len(all_lines) - self.max_visible_lines)

            if event.y > 0:
                # Scroll up (towards top)
                self.scroll_offset = max(0, self.scroll_offset - self.WHEEL_SCROLL_SPEED)
            elif event.y < 0:
                # Scroll down (towards bottom)
                self.scroll_offset = min(max_scroll, self.scroll_offset + self.WHEEL_SCROLL_SPEED)
        return ""
