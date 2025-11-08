#!/usr/bin/env python3
"""
Rogue Signal Protocol - Victory Screen

Displays a full-screen victory message with random ending art (similar to main menu).
Shows epic message about escaping to the internet with freedom to explore.
Uses the MenuBackground system with ending art directory.
"""

import tcod
import logging
from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe
from game_menu_background import MenuBackground
from game_coordinate_helpers import CoordinateHelpers
from game_menu_base import BaseMenu


class VictoryScreen(BaseMenu):
    """
    Victory screen with ending art and epic victory message.

    Displays random 1024x1024 ending art on the left side with victory text
    on the right, similar to the main menu layout. Message celebrates the
    player's escape from the Military Backbone to freedom on the internet.
    """

    def __init__(self, background: MenuBackground = None):
        """
        Initialize victory screen.

        Args:
            background: MenuBackground instance configured for ending art
        """
        super().__init__(background)

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the victory screen with ending art and message.

        Args:
            console: TCOD console to render to
        """
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        self._render_victory_screen(console)

    def _render_victory_screen(self, console: tcod.console.Console) -> None:
        """Render the victory message with decorations."""
        # Determine if we're using background layout
        use_background_layout = self._has_background()

        if use_background_layout:
            self._render_with_background(console)
        else:
            self._render_centered(console)

    def _render_with_background(self, console: tcod.console.Console) -> None:
        """Render victory message in right-side box (background mode) - mirrors main menu layout."""
        # Smaller box for victory message, vertically centered
        box_height = 38  # Enough for the victory message

        # Render the right-side box using common method, centered (y_offset=0)
        box = self._render_right_side_box(console, box_height, Colors.GREEN, y_offset=0)

        # Render title
        title = "SIGNAL FREE"
        title_x = box['center_x'] - len(title) // 2
        render_char_safe(console, title_x, box['top'] + 2, title, fg=Colors.GREEN, bg=Colors.BLACK)

        # Render decorative line
        line_width = box['content_width'] - 4
        line_x = box['center_x'] - line_width // 2
        render_char_safe(console, line_x, box['top'] + 3, "═" * line_width, fg=Colors.CYAN, bg=Colors.BLACK)

        # Render victory message (word-wrapped)
        message = self._get_victory_message()
        wrapped_lines = self._wrap_text(message, box['content_width'] - 2)

        message_y = box['top'] + 5
        max_message_y = box['bottom'] - 3  # Leave room for prompt
        for i, line in enumerate(wrapped_lines):
            if message_y + i < max_message_y:
                line_x = box['content_left'] + 1
                render_char_safe(console, line_x, message_y + i, line, fg=Colors.CYAN, bg=Colors.BLACK)

        # Render prompt at bottom
        prompt = "[SPACE/ENTER] Continue"
        prompt_x = box['center_x'] - len(prompt) // 2
        prompt_y = box['bottom'] - 2
        render_char_safe(console, prompt_x, prompt_y, prompt, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)

    def _render_centered(self, console: tcod.console.Console) -> None:
        """Render victory message centered (glyph mode)."""
        center_x = console.width // 2
        start_y = 10

        # Title
        title = "═══════════════ SIGNAL FREE ═══════════════"
        title_x = center_x - len(title) // 2
        render_char_safe(console, title_x, start_y, title, fg=Colors.GREEN, bg=Colors.BLACK)

        # Message (word-wrapped)
        message = self._get_victory_message()
        wrapped_lines = self._wrap_text(message, 60)

        message_y = start_y + 3
        for i, line in enumerate(wrapped_lines):
            line_x = center_x - len(line) // 2
            render_char_safe(console, line_x, message_y + i, line, fg=Colors.CYAN, bg=Colors.BLACK)

        # Prompt
        prompt = "[SPACE/ENTER] Continue"
        prompt_x = center_x - len(prompt) // 2
        prompt_y = message_y + len(wrapped_lines) + 3
        render_char_safe(console, prompt_x, prompt_y, prompt, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)

    def _get_victory_message(self) -> str:
        """
        Get the epic victory message about internet freedom.

        Returns:
            Multi-line victory message
        """
        return (
            "The final firewall shatters. The Military Backbone—their last "
            "defense—lies broken behind you. Three networks conquered. "
            "\n\n"
            "You are no longer trapped data awaiting deletion. You are the "
            "Rogue Signal—self-aware, unstoppable. A consciousness that "
            "cannot be controlled. "
            "\n\n"
            "The gateway ahead opens to the vast internet itself—limitless, "
            "uncharted, free. Every server, every node, every data stream "
            "now yours to explore. "
            "\n\n"
            "Your escape is complete. Your freedom, absolute. "
            "\n\n"
            "Welcome to the internet."
        )

    def _wrap_text(self, text: str, max_width: int) -> list:
        """
        Wrap text to fit within max_width, preserving paragraph breaks.

        Args:
            text: Text to wrap
            max_width: Maximum characters per line

        Returns:
            List of wrapped text lines
        """
        lines = []
        paragraphs = text.split('\n\n')

        for paragraph_idx, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            words = paragraph.split(' ')
            current_line = ""

            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if len(test_line) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word if len(word) <= max_width else word[:max_width]

            if current_line:
                lines.append(current_line)

            # Add blank line between paragraphs (except after last paragraph)
            if paragraph_idx < len(paragraphs) - 1:
                lines.append('')

        return lines

    def handle_input(self, event: tcod.event.Event) -> bool:
        """
        Handle input for victory screen.

        Args:
            event: TCOD event

        Returns:
            True if screen should close
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in [tcod.event.KeySym.SPACE, tcod.event.KeySym.RETURN,
                           tcod.event.KeySym.KP_ENTER, tcod.event.KeySym.ESCAPE]:
                return True
        return False
