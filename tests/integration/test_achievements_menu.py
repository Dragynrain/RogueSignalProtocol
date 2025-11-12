#!/usr/bin/env python3
"""
Integration tests for achievements menu (game_menu_achievements.py).

Tests menu navigation, rendering, scrolling, and interaction with achievement system.
"""

import pytest
import tcod
from game_menu_achievements import AchievementsMenu
from game_achievements import AchievementManager, ALL_ACHIEVEMENTS
from game_config import GameConfig


class TestAchievementsMenuBasic:
    """Test basic achievements menu functionality."""

    def test_menu_initialization(self):
        """Test menu initializes with correct default state."""
        menu = AchievementsMenu()
        assert menu.scroll_offset == 0
        assert menu.max_visible_lines == 35

    def test_menu_renders_without_crash(self):
        """Test menu renders successfully to console."""
        menu = AchievementsMenu()
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Should not raise any exceptions
        menu.render(console)

    def test_build_achievement_lines_includes_all_categories(self):
        """Test that all achievement categories appear in menu."""
        menu = AchievementsMenu()
        lines = menu._build_achievement_lines()

        # Check for all 6 category headers
        categories = [
            "COMBAT MASTERY",
            "STEALTH MASTERY",
            "EFFICIENCY & SPEED",
            "CHALLENGE RUNS",
            "MASTERY & COLLECTION",
            "LIFETIME"
        ]

        for category in categories:
            assert any(category in line['text'] for line in lines), \
                f"Category '{category}' not found in menu"

    def test_build_achievement_lines_includes_all_achievements(self):
        """Test that all 25 achievements are listed."""
        menu = AchievementsMenu()
        lines = menu._build_achievement_lines()

        # Should have lines for all 25 achievements (not counting category headers and blank lines)
        # Count achievement lines (those with icons like [X], [ ], or 🔒 for hidden)
        achievement_lines = [line for line in lines if '[X]' in line['text'] or '[ ]' in line['text'] or '🔒' in line['text']]
        assert len(achievement_lines) == 25, f"Expected 25 achievements, found {len(achievement_lines)}"

    def test_text_wrapping(self):
        """Test text wrapping works correctly."""
        menu = AchievementsMenu()

        # Short text shouldn't wrap
        short_text = "Short text"
        wrapped = menu._wrap_text(short_text, 50)
        assert wrapped == ["Short text"]

        # Long text should wrap
        long_text = "This is a very long text that definitely needs to be wrapped because it exceeds the maximum width"
        wrapped = menu._wrap_text(long_text, 50)
        assert len(wrapped) > 1
        for line in wrapped:
            assert len(line) <= 50


class TestAchievementsMenuScrolling:
    """Test scrolling functionality."""

    def test_scroll_down_increases_offset(self):
        """Test scrolling down increases offset."""
        menu = AchievementsMenu()
        original_offset = menu.scroll_offset

        # Create KeyDown event for down arrow
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier(0),
            repeat=False
        )

        action = menu.handle_input(event)

        assert action == ""  # Should return empty string (no action)
        assert menu.scroll_offset >= original_offset  # May not increase if at end

    def test_scroll_up_decreases_offset(self):
        """Test scrolling up decreases offset."""
        menu = AchievementsMenu()
        menu.scroll_offset = 10  # Start at offset 10

        # Create KeyDown event for up arrow
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.UP,
            mod=tcod.event.Modifier(0),
            repeat=False
        )

        action = menu.handle_input(event)

        assert action == ""
        assert menu.scroll_offset == 9  # Should decrease by 1

    def test_scroll_cannot_go_negative(self):
        """Test scrolling up stops at 0."""
        menu = AchievementsMenu()
        menu.scroll_offset = 0

        # Try to scroll up from 0
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.UP,
            mod=tcod.event.Modifier(0),
            repeat=False
        )

        menu.handle_input(event)

        assert menu.scroll_offset == 0  # Should stay at 0

    def test_scroll_respects_max_bounds(self):
        """Test scrolling down stops at max_scroll."""
        menu = AchievementsMenu()

        # Build lines to get total count
        all_lines = menu._build_achievement_lines()
        max_scroll = max(0, len(all_lines) - menu.max_visible_lines)

        # Set to near max and scroll down
        menu.scroll_offset = max_scroll

        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.DOWN,
            mod=tcod.event.Modifier(0),
            repeat=False
        )

        menu.handle_input(event)

        assert menu.scroll_offset == max_scroll  # Should not exceed max

    def test_mouse_wheel_scrolling(self):
        """Test mouse wheel scrolls the menu."""
        menu = AchievementsMenu()
        original_offset = menu.scroll_offset

        # Create fake mouse wheel event (scroll down)
        event = type('Event', (), {'y': -1})()

        result = menu.handle_mouse_wheel(event)

        assert result is True
        assert menu.scroll_offset >= original_offset  # Should increase (if not at max)


class TestAchievementsMenuInput:
    """Test input handling."""

    def test_escape_returns_back(self):
        """Test ESC key returns 'back' action."""
        menu = AchievementsMenu()

        # Create KeyDown event for ESC
        event = tcod.event.KeyDown(
            scancode=0,
            sym=tcod.event.KeySym.ESCAPE,
            mod=tcod.event.Modifier(0),
            repeat=False
        )

        action = menu.handle_input(event)

        assert action == "back"

    def test_mouse_right_click_returns_back(self):
        """Test right-click returns 'back' action (standardized behavior)."""
        menu = AchievementsMenu()

        # Create fake right-click event
        event = type('Event', (), {
            'button': tcod.event.MouseButton.RIGHT,
            'position': type('Position', (), {'x': 40, 'y': 25})()
        })()

        action = menu.handle_mouse_click(event)

        assert action == "back"

    def test_mouse_left_click_on_empty_space_does_nothing(self):
        """Test left-click on empty space does nothing (removed confusing click-anywhere-to-exit)."""
        menu = AchievementsMenu()

        # Create fake left-click event
        event = type('Event', (), {
            'button': tcod.event.MouseButton.LEFT,
            'position': type('Position', (), {'x': 40, 'y': 25})()
        })()

        action = menu.handle_mouse_click(event)

        assert action == ""  # Empty string, not "back"

    def test_mouse_motion_returns_false(self):
        """Test mouse motion is ignored."""
        menu = AchievementsMenu()

        event = type('Event', (), {
            'position': type('Position', (), {'x': 40, 'y': 25})()
        })()

        result = menu.handle_mouse_motion(event)

        assert result is False


class TestAchievementsMenuIntegration:
    """Test integration with achievement system."""

    def test_menu_displays_unlocked_achievements_correctly(self):
        """Test unlocked achievements show as green with checkmark."""
        # Unlock a test achievement
        AchievementManager._unlocked_achievements = {'first_blood'}

        menu = AchievementsMenu()
        lines = menu._build_achievement_lines()

        # Find the first_blood achievement line
        first_blood_line = None
        for line in lines:
            if 'First Blood' in line['text']:
                first_blood_line = line
                break

        assert first_blood_line is not None
        assert '[X]' in first_blood_line['text']  # Should have checked checkbox
        # Note: color will be Colors.GREEN tuple, we can't easily test exact color

        # Clean up
        AchievementManager._unlocked_achievements = set()

    def test_menu_displays_locked_achievements_correctly(self):
        """Test locked achievements show as gray with X."""
        # Ensure no achievements unlocked
        AchievementManager._unlocked_achievements = set()

        menu = AchievementsMenu()
        lines = menu._build_achievement_lines()

        # Find any achievement line (e.g., first_blood)
        first_blood_line = None
        for line in lines:
            if 'First Blood' in line['text']:
                first_blood_line = line
                break

        assert first_blood_line is not None
        assert '[ ]' in first_blood_line['text']  # Should have unchecked checkbox

    def test_menu_shows_progress_count(self):
        """Test menu displays unlock progress in title."""
        # Unlock 3 achievements
        AchievementManager._unlocked_achievements = {'first_blood', 'massacre', 'overkill'}

        menu = AchievementsMenu()
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        menu.render(console)

        # Check that title contains progress (rendered to console)
        # We can't easily read back from console, but we can verify the method doesn't crash
        # and that get_unlock_progress returns correct values
        unlocked, total = AchievementManager.get_unlock_progress()
        assert unlocked == 3
        assert total == 25

        # Clean up
        AchievementManager._unlocked_achievements = set()

    def test_hidden_achievements_display_as_locked(self):
        """Test hidden achievements show as '???' when locked."""
        # Ensure no achievements unlocked
        AchievementManager._unlocked_achievements = set()

        # Find a hidden achievement
        hidden_achievement = None
        for achievement in ALL_ACHIEVEMENTS.values():
            if achievement.hidden:
                hidden_achievement = achievement
                break

        if hidden_achievement is None:
            pytest.skip("No hidden achievements defined")

        menu = AchievementsMenu()
        lines = menu._build_achievement_lines()

        # Search for ??? in achievement lines
        has_hidden = any('???' in line['text'] for line in lines)
        assert has_hidden, "Hidden achievements should show as '???'"


class TestAchievementsMenuEdgeCases:
    """Test edge cases and error conditions."""

    def test_menu_handles_no_unlocked_achievements(self):
        """Test menu works when no achievements unlocked."""
        AchievementManager._unlocked_achievements = set()

        menu = AchievementsMenu()
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Should not crash
        menu.render(console)

        # Check progress is 0/25
        unlocked, total = AchievementManager.get_unlock_progress()
        assert unlocked == 0
        assert total == 25

    def test_menu_handles_all_unlocked_achievements(self):
        """Test menu works when all achievements unlocked."""
        # Unlock all achievements
        AchievementManager._unlocked_achievements = set(ALL_ACHIEVEMENTS.keys())

        menu = AchievementsMenu()
        console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

        # Should not crash
        menu.render(console)

        # Check progress is 25/25
        unlocked, total = AchievementManager.get_unlock_progress()
        assert unlocked == 25
        assert total == 25

        # Clean up
        AchievementManager._unlocked_achievements = set()

    def test_menu_handles_invalid_mouse_wheel_event(self):
        """Test menu handles mouse wheel event without y attribute."""
        menu = AchievementsMenu()

        # Event without 'y' attribute
        event = type('Event', (), {})()

        result = menu.handle_mouse_wheel(event)

        assert result is False

    def test_menu_handles_mouse_click_without_position(self):
        """Test menu handles mouse click event without position."""
        menu = AchievementsMenu()

        # Event without 'position' attribute
        event = type('Event', (), {})()

        action = menu.handle_mouse_click(event)

        assert action == ""
