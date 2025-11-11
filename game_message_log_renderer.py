#!/usr/bin/env python3
"""
Message log rendering for system messages.

Handles rendering of the scrolling system message log with:
- Border and header rendering
- Message wrapping for long lines
- Scrolling display of recent messages

Extracted from game_rendering_ui.py to improve modularity.
"""

import tcod
from typing import List, Tuple

from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe
from game_unicode_chars import GameGlyphs


class MessageLogRenderer:
    """
    Renders the system message log in the right panel.

    Displays scrolling game messages with automatic text wrapping
    and proper border/header formatting.
    """

    def __init__(self, settings=None):
        """
        Initialize message log renderer.

        Args:
            settings: GameSettings instance (optional, for UI color)
        """
        self.settings = settings

    def render_system_log(self, console: tcod.console.Console, game):
        """
        Render the system message log on the right side.

        Draws border, header, and scrolling messages.
        Now starts at y=11 (after info panel) instead of y=3.
        Hides messages when in look mode to avoid overlap with inspection panel.
        Stops at PANEL_Y to make room for bottom panel.

        Args:
            console: TCOD console to render to
            game: GameEngine with message_log and look_mode state
        """
        # Get UI color from settings
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        log_start_y = GameConfig.LOG_START_Y()

        # T-piece at left where log border meets the header line
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), log_start_y, GameGlyphs.WALL_T_RIGHT, fg=ui_color, bg=Colors.LOG_BG)

        # Build header line: "SYSTEM LOG" embedded in ═ border
        header_text = " SYSTEM LOG "
        log_width = GameConfig.SCREEN_WIDTH - GameConfig.GAME_AREA_WIDTH() - 1

        # Center the text in the header line
        header_start = GameConfig.GAME_AREA_WIDTH() + 1 + (log_width - len(header_text)) // 2

        # Render the header line
        for i in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            if i >= header_start and i < header_start + len(header_text):
                # SYSTEM LOG text in bright cyan
                char_idx = i - header_start
                render_char_safe(console, i, log_start_y, header_text[char_idx], fg=Colors.CYAN, bg=Colors.LOG_BG)
            else:
                # ═ character fill
                render_char_safe(console, i, log_start_y, '═', fg=ui_color, bg=Colors.LOG_BG)

        # Draw log border (from LOG_START_Y + 1 to panel start) with UI color
        for y in range(log_start_y + 1, GameConfig.PANEL_Y()):
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), y, '║', fg=ui_color, bg=Colors.LOG_BG)

        # Clear log area - start from log_start_y + 1
        for x in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            for y in range(log_start_y + 1, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)

        # Process and display messages (skip if in look mode - inspection panel will use this area)
        if not game.look_mode:
            self._render_log_messages(console, game)

    def _render_log_messages(self, console: tcod.console.Console, game):
        """
        Render scrolling log messages with automatic wrapping.

        Shows the most recent messages that fit in the available vertical space.
        Starts at LOG_START_Y + 2 (one blank line below header for breathing space).
        Delegates text wrapping to _wrap_messages().

        Args:
            console: TCOD console to render to
            game: GameEngine with message_log
        """
        log_start_y = GameConfig.LOG_START_Y()
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.PANEL_Y() - (log_start_y + 2)  # Available space (with blank line for breathing space)
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines

        for i, (line, color) in enumerate(visible_lines):
            y_pos = log_start_y + 2 + i  # Start from LOG_START_Y + 2 for breathing space
            if y_pos < GameConfig.PANEL_Y():
                render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)

    def _wrap_messages(self, messages: List) -> List[Tuple[str, Tuple[int, int, int]]]:
        """
        Wrap long messages across multiple lines for display.

        Uses word-based wrapping to keep messages readable.
        Handles both Message objects and (text, color) tuples for flexibility.

        Args:
            messages: List of Message objects or (text, color) tuples

        Returns:
            List of (wrapped_text, color) tuples ready for rendering
        """
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
