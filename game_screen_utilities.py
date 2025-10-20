#!/usr/bin/env python3
"""
Screen Rendering Utilities
Shared rendering utilities for all screen types (menus, in-game overlays, etc.)
"""

import tcod
from typing import List, Tuple, Optional
from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe


class ScreenRenderingUtils:
    """
    Shared rendering utilities for screen elements.

    Provides standardized methods for:
    - Centered titles
    - Headers with borders
    - Footers with borders
    - Word-wrapped text rendering
    - Scroll indicators
    """

    @staticmethod
    def render_centered_title(console: tcod.console.Console, title: str, y: int,
                             color: tuple = Colors.YELLOW, width: int = None) -> None:
        """
        Render a centered title.

        Args:
            console: Console to render to
            title: Title text
            y: Y position
            color: Title color (default: yellow)
            width: Width to center within (default: screen width)
        """
        if width is None:
            width = GameConfig.SCREEN_WIDTH

        title_x = width // 2 - len(title) // 2
        render_char_safe(console, title_x, y, title, fg=color)

    @staticmethod
    def render_centered_title_in_area(console: tcod.console.Console, title: str, y: int,
                                     area_width: int, color: tuple = Colors.YELLOW) -> None:
        """
        Render a centered title within a specific area width (e.g., game area only).

        Args:
            console: Console to render to
            title: Title text
            y: Y position
            area_width: Width of area to center within
            color: Title color (default: yellow)
        """
        title_x = area_width // 2 - len(title) // 2
        render_char_safe(console, title_x, y, title, fg=color)

    @staticmethod
    def render_screen_header(console: tcod.console.Console, title: str,
                           subtitle: str = None, border_color: tuple = Colors.CYAN,
                           title_color: tuple = Colors.CYAN) -> int:
        """
        Render a standardized screen header with title, optional subtitle, and borders.

        Args:
            console: Console to render to
            title: Main title text
            subtitle: Optional subtitle text
            border_color: Color for border lines
            title_color: Color for title text

        Returns:
            Y position where content should start (after the header)
        """
        # Top border
        render_char_safe(console, 2, 1, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=border_color)

        # Main title (centered)
        ScreenRenderingUtils.render_centered_title(console, title, 2, title_color)

        # Subtitle if provided
        if subtitle:
            ScreenRenderingUtils.render_centered_title(console, subtitle, 3, Colors.WHITE)
            # Bottom border after subtitle
            render_char_safe(console, 2, 4, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=border_color)
            return 6  # Content starts at line 6
        else:
            # Bottom border after title
            render_char_safe(console, 2, 3, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=border_color)
            return 5  # Content starts at line 5

    @staticmethod
    def render_screen_footer(console: tcod.console.Console, instructions: str,
                           additional_line: str = None,
                           color: tuple = Colors.YELLOW) -> None:
        """
        Render a standardized screen footer with instructions.

        Args:
            console: Console to render to
            instructions: Primary instruction text
            additional_line: Optional second line of instructions
            color: Text color for instructions
        """
        footer_y = GameConfig.SCREEN_HEIGHT - 4 if additional_line else GameConfig.SCREEN_HEIGHT - 3

        # Footer border
        render_char_safe(console, 2, footer_y, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)

        # Instructions (centered)
        ScreenRenderingUtils.render_centered_title(console, instructions, footer_y + 1, color)

        # Additional line if provided
        if additional_line:
            ScreenRenderingUtils.render_centered_title(console, additional_line, footer_y + 2, color)

    @staticmethod
    def render_word_wrapped_text(console: tcod.console.Console, text: str,
                                start_x: int, start_y: int, max_width: int,
                                max_height: int = None, color: tuple = Colors.WHITE) -> int:
        """
        Render text with word wrapping.

        Args:
            console: Console to render to
            text: Text to render (can contain newlines)
            start_x: Starting X position
            start_y: Starting Y position
            max_width: Maximum width for text lines
            max_height: Maximum Y position (optional, for truncation)
            color: Text color

        Returns:
            Final Y position after rendering (or max_height if truncated)
        """
        lines = text.split('\n')
        y_offset = start_y

        for line in lines:
            # Check if we've reached the height limit
            if max_height and y_offset >= max_height:
                render_char_safe(console, start_x, y_offset - 1, "... [Text continues]", fg=Colors.YELLOW)
                return max_height

            line = line.strip()
            if not line:
                y_offset += 1
                continue

            # Word wrap long lines
            if len(line) <= max_width:
                render_char_safe(console, start_x, y_offset, line, fg=color)
                y_offset += 1
            else:
                words = line.split(' ')
                current_line = ""

                for word in words:
                    if len(current_line + word) + 1 <= max_width:
                        current_line += (word if not current_line else " " + word)
                    else:
                        if current_line:
                            render_char_safe(console, start_x, y_offset, current_line, fg=color)
                            y_offset += 1
                            if max_height and y_offset >= max_height:
                                render_char_safe(console, start_x, y_offset - 1, "...", fg=Colors.YELLOW)
                                return max_height
                        current_line = word

                if current_line:
                    if not max_height or y_offset < max_height:
                        render_char_safe(console, start_x, y_offset, current_line, fg=color)
                        y_offset += 1

        return y_offset

    @staticmethod
    def render_scroll_indicators(console: tcod.console.Console, x: int,
                                top_y: int, bottom_y: int,
                                show_up: bool, show_down: bool,
                                color: tuple = Colors.YELLOW) -> None:
        """
        Render scroll indicators (^ MORE ^ / v MORE v).

        Args:
            console: Console to render to
            x: X position for indicators
            top_y: Y position for up indicator
            bottom_y: Y position for down indicator
            show_up: Whether to show up indicator
            show_down: Whether to show down indicator
            color: Indicator color
        """
        if show_up:
            render_char_safe(console, x, top_y, "^ MORE ^", fg=color)

        if show_down:
            render_char_safe(console, x, bottom_y, "v MORE v", fg=color)


class ScrollableListManager:
    """
    Manages scroll offset and visibility for list-based screens.

    Handles:
    - Scroll offset tracking
    - Automatic adjustment to keep selection visible
    - Visibility range calculation
    - Scroll indicator state

    Usage:
        manager = ScrollableListManager(total_items=50, visible_height=20)
        manager.adjust_for_selection(15)  # Keep item 15 visible
        start, end = manager.get_visible_range()
        # Render items[start:end]
        # Show indicators if manager.should_show_scroll_up/down()
    """

    def __init__(self, total_items: int, visible_height: int):
        """
        Initialize scrollable list manager.

        Args:
            total_items: Total number of items in the list
            visible_height: Number of items visible at once
        """
        self.total_items = total_items
        self.visible_height = visible_height
        self.scroll_offset = 0

    def adjust_for_selection(self, selection_index: int) -> None:
        """
        Adjust scroll offset to keep selected item visible.

        Args:
            selection_index: Index of currently selected item
        """
        if self.total_items <= self.visible_height:
            self.scroll_offset = 0
            return

        if selection_index < self.scroll_offset:
            # Selection is above viewport, scroll up
            self.scroll_offset = selection_index
        elif selection_index >= self.scroll_offset + self.visible_height:
            # Selection is below viewport, scroll down
            self.scroll_offset = selection_index - self.visible_height + 1

        # Clamp scroll offset
        max_scroll = max(0, self.total_items - self.visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def get_visible_range(self) -> Tuple[int, int]:
        """
        Get the range of items currently visible.

        Returns:
            Tuple of (start_index, end_index) for slicing
        """
        start = self.scroll_offset
        end = min(self.scroll_offset + self.visible_height, self.total_items)
        return start, end

    def should_show_scroll_up(self) -> bool:
        """
        Check if up scroll indicator should be shown.

        Returns:
            True if there are items above the visible area
        """
        return self.scroll_offset > 0

    def should_show_scroll_down(self) -> bool:
        """
        Check if down scroll indicator should be shown.

        Returns:
            True if there are items below the visible area
        """
        return self.scroll_offset + self.visible_height < self.total_items

    def reset(self) -> None:
        """Reset scroll offset to top."""
        self.scroll_offset = 0

    def set_total_items(self, total_items: int) -> None:
        """
        Update total item count (e.g., when list contents change).

        Args:
            total_items: New total item count
        """
        self.total_items = total_items

        # Re-clamp scroll offset if needed
        max_scroll = max(0, self.total_items - self.visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    def get_scroll_offset(self) -> int:
        """
        Get current scroll offset.

        Returns:
            Current scroll offset
        """
        return self.scroll_offset

    def set_scroll_offset(self, offset: int) -> None:
        """
        Manually set scroll offset (clamped to valid range).

        Args:
            offset: Desired scroll offset
        """
        max_scroll = max(0, self.total_items - self.visible_height)
        self.scroll_offset = max(0, min(offset, max_scroll))
