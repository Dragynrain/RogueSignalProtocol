#!/usr/bin/env python3
"""
Game Rendering UI - Message Log
Renders the system message log panel.
"""

import tcod
from typing import List, Tuple

from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe


class MessageLogRenderer:
    """Renders the system message log panel."""

    def render_system_log(self, console: tcod.console.Console, game):
        """Render the system log on the right side."""
        # Draw log border
        for y in range(GameConfig.SCREEN_HEIGHT):
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), y, '│', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Help text in top-right corner (properly positioned in log panel)
        help_text = "Press ? for help"
        help_x = GameConfig.GAME_AREA_WIDTH() + 2  # Leave a space after border
        render_char_safe(console, help_x, 0, help_text, fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)

        # Log header
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 1, "SYSTEM LOG", fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 2, "─" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Clear log area - start from line 3 to account for header repositioning
        for x in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            for y in range(3, GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)

        # Process and display messages (skip if in look mode - inspection panel will use this area)
        if not game.look_mode:
            self._render_log_messages(console, game)

    def _render_log_messages(self, console: tcod.console.Console, game):
        """Render log messages with proper wrapping."""
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.SCREEN_HEIGHT - 3  # Adjusted for header repositioning
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines

        for i, (line, color) in enumerate(visible_lines):
            y_pos = 3 + i  # Start from line 3 to avoid header
            if y_pos < GameConfig.SCREEN_HEIGHT:
                render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)

    def _wrap_messages(self, messages: List) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Wrap long messages across multiple lines."""
        wrapped_lines = []
        max_msg_width = GameConfig.LOG_WIDTH - 2

        for message in messages:
            # Handle both Message objects and tuple formats
            if hasattr(message, 'text') and hasattr(message, 'color'):
                text, color = message.text, message.color
            else:
                text, color = message
            if len(text) <= max_msg_width:
                wrapped_lines.append((text, color))
            else:
                # Wrap long messages
                words = text.split(' ')
                current_line = ""

                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_msg_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_lines.append((current_line, color))
                        current_line = word

                if current_line:
                    wrapped_lines.append((current_line, color))

        return wrapped_lines
