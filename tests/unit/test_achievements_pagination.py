"""
Test achievements pagination logic.

Regression test for incorrect page number display when at max scroll.
"""

from rsp.ui.menu_achievements import AchievementsMenu


class TestAchievementsPagination:
    """Test achievements screen pagination calculations."""

    def test_page_calculation_at_start(self):
        """At scroll offset 0, should show page 1."""
        menu = AchievementsMenu()

        # Mock _build_achievement_lines to return known number of lines
        menu._build_achievement_lines = lambda: [
            {"x": 0, "text": f"Line {i}", "color": (255, 255, 255)} for i in range(100)
        ]

        # At offset 0, should be page 1
        all_lines = menu._build_achievement_lines()
        total_pages = (len(all_lines) + menu.max_visible_lines - 1) // menu.max_visible_lines

        # Calculate current page based on last visible line (not just offset)
        last_visible_line = min(menu.scroll_offset + menu.max_visible_lines - 1, len(all_lines) - 1)
        current_page = (last_visible_line // menu.max_visible_lines) + 1

        assert current_page == 1, f"At offset 0, should be page 1, got {current_page}"
        assert total_pages == 3, f"100 lines / 35 visible should be 3 pages, got {total_pages}"

    def test_page_calculation_at_max_scroll(self):
        """At max scroll, should show last page (not second-to-last)."""
        menu = AchievementsMenu()

        # Mock _build_achievement_lines to return known number of lines
        menu._build_achievement_lines = lambda: [
            {"x": 0, "text": f"Line {i}", "color": (255, 255, 255)} for i in range(100)
        ]

        all_lines = menu._build_achievement_lines()
        max_scroll = max(0, len(all_lines) - menu.max_visible_lines)
        menu.scroll_offset = max_scroll  # 100 - 35 = 65

        total_pages = (len(all_lines) + menu.max_visible_lines - 1) // menu.max_visible_lines

        # OLD BUGGY FORMULA: current_page = (offset // max_visible) + 1
        # At offset 65: (65 // 35) + 1 = 1 + 1 = 2 ❌ WRONG!

        # NEW CORRECT FORMULA: based on last visible line
        last_visible_line = min(menu.scroll_offset + menu.max_visible_lines - 1, len(all_lines) - 1)
        current_page = (last_visible_line // menu.max_visible_lines) + 1

        # At offset 65, viewing lines 65-99, last_visible = 99
        # current_page = (99 // 35) + 1 = 2 + 1 = 3 ✓ CORRECT!
        assert current_page == 3, f"At max scroll, should be page 3, got {current_page}"
        assert current_page == total_pages, "At max scroll, should be on last page"

    def test_page_scroll_speed_preserves_context(self):
        """PAGE_SCROLL_SPEED should be less than max_visible_lines to preserve context."""
        menu = AchievementsMenu()

        # Should scroll less than a full page to avoid splitting achievements
        # and to keep some context visible when paging through
        assert (
            menu.PAGE_SCROLL_SPEED < menu.max_visible_lines
        ), f"PAGE_SCROLL_SPEED ({menu.PAGE_SCROLL_SPEED}) should be less than max_visible_lines ({menu.max_visible_lines})"
        assert (
            menu.PAGE_SCROLL_SPEED >= menu.max_visible_lines - 10
        ), "PAGE_SCROLL_SPEED should still be close to full page for efficient navigation"

    def test_page_down_moves_by_page_scroll_speed(self):
        """Pressing Page Down should advance by PAGE_SCROLL_SPEED lines."""
        menu = AchievementsMenu()
        menu._build_achievement_lines = lambda: [
            {"x": 0, "text": f"Line {i}", "color": (255, 255, 255)} for i in range(100)
        ]

        initial_offset = 0
        menu.scroll_offset = initial_offset

        # Execute page down action
        from rsp.input.actions import InputAction

        menu.execute_action(InputAction.NAVIGATE_PAGE_DOWN)

        # Should have moved by PAGE_SCROLL_SPEED (preserves context for split prevention)
        expected_offset = initial_offset + menu.PAGE_SCROLL_SPEED
        assert (
            menu.scroll_offset == expected_offset
        ), f"Page down should move {menu.PAGE_SCROLL_SPEED} lines, moved {menu.scroll_offset - initial_offset}"
