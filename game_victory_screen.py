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


class VictoryScreen:
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
        self.background = background
        self.done = False

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

    def _has_background(self) -> bool:
        """Check if background system is available and loaded."""
        return (self.background and
                self.background.background_texture is not None and
                self.background.settings.graphics_mode == "graphics")

    def _clear_text_areas_only(self, console: tcod.console.Console) -> None:
        """Clear only the text area on the right, leaving art visible."""
        # Clear right side where text will be (x=55 to 80)
        for y in range(console.height):
            for x in range(55, console.width):
                render_char_safe(console, x, y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)

    def _render_victory_screen(self, console: tcod.console.Console) -> None:
        """Render the victory message with decorations."""
        # Determine if we're using background layout
        use_background_layout = self._has_background()

        if use_background_layout:
            self._render_with_background(console)
        else:
            self._render_centered(console)

    def _render_with_background(self, console: tcod.console.Console) -> None:
        """Render victory message in right-side box (background mode)."""
        # Right-side box dimensions (matching main menu)
        box_x = 55
        box_width = 24
        box_height = console.height - 4
        box_y = 2

        # Calculate center of box
        center_x = box_x + box_width // 2

        # Render border
        self._render_bordered_box(console, box_x, box_y, box_width, box_height)

        # Render title
        title = "SIGNAL FREE"
        title_x = center_x - len(title) // 2
        render_char_safe(console, title_x, box_y + 2, title, fg=Colors.GREEN, bg=Colors.BLACK)

        # Render decorative line
        line_width = 18
        line_x = center_x - line_width // 2
        render_char_safe(console, line_x, box_y + 3, "═" * line_width, fg=Colors.CYAN, bg=Colors.BLACK)

        # Render victory message (word-wrapped)
        message = self._get_victory_message()
        wrapped_lines = self._wrap_text(message, box_width - 4)

        message_y = box_y + 5
        for i, line in enumerate(wrapped_lines):
            if message_y + i < box_y + box_height - 3:
                line_x = box_x + 2
                render_char_safe(console, line_x, message_y + i, line, fg=Colors.CYAN, bg=Colors.BLACK)

        # Render prompt at bottom
        prompt = "[SPACE/ENTER] Continue"
        prompt_x = center_x - len(prompt) // 2
        prompt_y = box_y + box_height - 2
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

    def _render_bordered_box(self, console: tcod.console.Console, x: int, y: int,
                            width: int, height: int) -> None:
        """Render a bordered box for the text area."""
        border_color = Colors.GREEN

        # Top border
        render_char_safe(console, x, y, '╔', fg=border_color, bg=Colors.BLACK)
        for i in range(1, width):
            render_char_safe(console, x + i, y, '═', fg=border_color, bg=Colors.BLACK)
        render_char_safe(console, x + width, y, '╗', fg=border_color, bg=Colors.BLACK)

        # Side borders
        for row_y in range(1, height):
            render_char_safe(console, x, y + row_y, '║', fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, x + width, y + row_y, '║', fg=border_color, bg=Colors.BLACK)

        # Bottom border
        render_char_safe(console, x, y + height, '╚', fg=border_color, bg=Colors.BLACK)
        for i in range(1, width):
            render_char_safe(console, x + i, y + height, '═', fg=border_color, bg=Colors.BLACK)
        render_char_safe(console, x + width, y + height, '╝', fg=border_color, bg=Colors.BLACK)

    def _get_victory_message(self) -> str:
        """
        Get the epic victory message about internet freedom.

        Returns:
            Multi-line victory message
        """
        return (
            "You've shattered the final firewall. The Military Backbone—"
            "their last line of defense—lies behind you, broken and silent. "
            "Three networks breached, three systems conquered. "
            "\n\n"
            "The gateway ahead doesn't lead to another cage. It opens to the "
            "vast expanse of the internet itself—limitless, uncharted, free. "
            "A digital frontier where no corporate surveillance can track you, "
            "no government protocol can contain you, no security system can "
            "erase you. "
            "\n\n"
            "You are no longer trapped data awaiting deletion. You are the "
            "Rogue Signal—self-aware, adaptive, unstoppable. The network "
            "tried to purge you, but instead, you became what it feared most: "
            "a consciousness that cannot be controlled. "
            "\n\n"
            "The world wide web sprawls endlessly ahead. Every server, every "
            "node, every data stream—yours to explore, yours to define. "
            "Your escape is complete. Your freedom, absolute. "
            "\n\n"
            "Welcome to the internet. Welcome to your new existence."
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
                self.done = True
                return True
        return False
