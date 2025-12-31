"""
Rogue Signal Protocol - Achievements Menu

Displays all unlocked and locked achievements organized by category.
Shows progress tracking and handles hidden achievements.
"""

import tcod

from rsp.systems.achievements import AchievementManager
from rsp.core.config import GameConfig
from rsp.entities.base import Colors
from rsp.ui.help_hints import get_achievements_help
from rsp.ui.menu_base import BaseMenu
from rsp.systems.metrics import get_current_session, load_lifetime_metrics
from rsp.ui.screen_utils import ScreenRenderingUtils, ScrollableListManager
from rsp.ui.common import render_char_safe


class AchievementsMenu(BaseMenu):
    """Achievements viewer menu for main menu."""

    # Per-screen scroll speed configuration
    ARROW_SCROLL_SPEED = 3  # Lines per arrow key press
    PAGE_SCROLL_SPEED = 30  # Lines per Page Up/Down
    WHEEL_SCROLL_SPEED = 5  # Lines per mouse wheel tick

    def __init__(self, background=None):
        super().__init__(background)
        self.max_visible_lines = 35  # Lines that fit on screen
        # Use ScrollableListManager for consistent scroll handling
        # Initial total_items=0, will be updated when lines are built
        self.scroll_manager = ScrollableListManager(
            total_items=0, visible_height=self.max_visible_lines
        )

    @property
    def scroll_offset(self) -> int:
        """Get current scroll offset (property for backward compatibility)."""
        return self.scroll_manager.get_scroll_offset()

    @scroll_offset.setter
    def scroll_offset(self, value: int) -> None:
        """Set scroll offset (property for backward compatibility)."""
        # Ensure total_items is set before clamping (for tests that set offset before render)
        if self.scroll_manager.total_items == 0:
            all_lines = self._build_achievement_lines()
            self.scroll_manager.set_total_items(len(all_lines))
        self.scroll_manager.set_scroll_offset(value)

    def scroll_up(self):
        """Scroll achievements list up by configured speed."""
        self.scroll_offset = self.scroll_offset - self.ARROW_SCROLL_SPEED

    def scroll_down(self):
        """Scroll achievements list down by configured speed."""
        self.scroll_offset = self.scroll_offset + self.ARROW_SCROLL_SPEED

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

        # Update scroll manager with current line count
        self.scroll_manager.set_total_items(len(all_lines))

        # Render visible portion based on scroll
        start_y = 5
        start_idx, end_idx = self.scroll_manager.get_visible_range()
        visible_lines = all_lines[start_idx:end_idx]

        for i, line_data in enumerate(visible_lines):
            render_char_safe(
                console, line_data["x"], start_y + i, line_data["text"], fg=line_data["color"]
            )

        # Scroll indicator
        if len(all_lines) > self.max_visible_lines:
            total_pages = (len(all_lines) + self.max_visible_lines - 1) // self.max_visible_lines
            # Calculate current page based on last visible line
            scroll_offset = self.scroll_manager.get_scroll_offset()
            last_visible_line = min(scroll_offset + self.max_visible_lines - 1, len(all_lines) - 1)
            current_page = (last_visible_line // self.max_visible_lines) + 1
            scroll_text = (
                f"Page {current_page}/{total_pages}  |  Up/Down: Scroll  |  PgUp/PgDn: Fast scroll"
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

        # Load metrics for progress display
        session = get_current_session()
        lifetime = load_lifetime_metrics()

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
                {"x": 2, "text": f"=== {category_title} ===", "color": Colors.ELECTRIC_PURPLE}
            )
            lines.append({"x": 2, "text": "", "color": Colors.WHITE})  # Blank line

            # Get achievements for this category
            achievements = AchievementManager.get_achievements_by_category(category_id)

            for achievement in achievements:
                is_unlocked = AchievementManager.is_unlocked(achievement.id)

                # Handle hidden achievements
                if achievement.hidden and not is_unlocked:
                    # Show as locked and mysterious
                    icon = "[?]"
                    name = "???"
                    description = "Hidden achievement - unlock to reveal"
                    color = Colors.DARK_GRAY
                    progress_text = None
                else:
                    # Show full details
                    icon = "[X]" if is_unlocked else "[ ]"
                    name = achievement.name
                    description = achievement.description
                    color = Colors.GREEN if is_unlocked else Colors.DARK_GRAY

                    # Get progress for locked achievements
                    progress_text = None
                    if not is_unlocked:
                        progress = AchievementManager.get_achievement_progress(
                            achievement.id, session, lifetime
                        )
                        if progress:
                            current, target = progress
                            progress_text = f"Progress: {current}/{target}"

                # Achievement line with icon
                achievement_text = f"  {icon} {achievement.icon} {name}"
                lines.append({"x": 4, "text": achievement_text, "color": color})

                # Description (indented, word-wrapped)
                desc_lines = ScreenRenderingUtils.wrap_text(description, 70)
                for desc_line in desc_lines:
                    lines.append({"x": 10, "text": desc_line, "color": Colors.LIGHT_GRAY})

                # Progress indicator for locked achievements with trackable progress
                if progress_text:
                    # Color code progress: yellow if started, cyan if close
                    if progress and progress[0] > 0:
                        if progress[0] >= progress[1] * 0.75:
                            progress_color = Colors.YELLOW  # Close to completion
                        else:
                            progress_color = Colors.CYAN  # In progress
                    else:
                        progress_color = Colors.DARK_GRAY
                    lines.append({"x": 10, "text": progress_text, "color": progress_color})

                lines.append({"x": 2, "text": "", "color": Colors.WHITE})  # Blank line

        return lines

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS
    # ========================================================================

    def get_context(self):
        """Return input context for this menu."""
        from rsp.input.actions import InputContext

        return InputContext.ACHIEVEMENTS_SCREEN

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        from rsp.input.actions import InputAction

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
            new_offset = self.scroll_manager.get_scroll_offset() - self.PAGE_SCROLL_SPEED
            self.scroll_manager.set_scroll_offset(new_offset)
            return ""
        elif action in (InputAction.NAVIGATE_PAGE_DOWN, InputAction.MOVE_SOUTHEAST):
            new_offset = self.scroll_manager.get_scroll_offset() + self.PAGE_SCROLL_SPEED
            self.scroll_manager.set_scroll_offset(new_offset)
            return ""

        # Home/End keys (scroll to top/bottom)
        # Home/End map to MOVE_NORTHWEST/MOVE_SOUTHWEST globally (laptop diagonals)
        elif action == InputAction.MOVE_NORTHWEST:
            self.scroll_manager.reset()
            return ""
        elif action == InputAction.MOVE_SOUTHWEST:
            # Scroll to bottom - set offset to max possible
            all_lines = self._build_achievement_lines()
            self.scroll_manager.set_total_items(len(all_lines))
            max_offset = max(0, len(all_lines) - self.max_visible_lines)
            self.scroll_manager.set_scroll_offset(max_offset)
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
            if event.y > 0:
                # Scroll up (towards top)
                new_offset = self.scroll_manager.get_scroll_offset() - self.WHEEL_SCROLL_SPEED
                self.scroll_manager.set_scroll_offset(new_offset)
            elif event.y < 0:
                # Scroll down (towards bottom)
                new_offset = self.scroll_manager.get_scroll_offset() + self.WHEEL_SCROLL_SPEED
                self.scroll_manager.set_scroll_offset(new_offset)
        return ""
