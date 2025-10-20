#!/usr/bin/env python3
"""
Rogue Signal Protocol - Panel Renderer

Renders overlay panels for inspection and other contextual information.
Handles text wrapping and proper positioning within the log area.
Inspection panel appears when in look mode, displaying entity details.
"""

import tcod
from game_config import GameConfig
from game_entities import Colors
from game_ui import render_char_safe


class PanelRenderer:
    """
    Renders overlay panels for contextual information.

    Currently handles inspection panel (look mode) which displays:
    - Entity name with color coding
    - Entity description
    - Detailed stats and status information

    Panel renders in the log area (right side of screen) when active.
    """

    def render_inspection_panel(self, console: tcod.console.Console, game):
        """
        Render the inspection panel when in look mode.

        Shows entity information at cursor position using EntityInspector.
        Renders in log area with proper text wrapping and vertical layout.
        Returns early if not in look mode.

        Args:
            console: TCOD console to render to
            game: GameEngine with look_mode and look_cursor_position
        """
        if not game.look_mode:
            return

        from game_inspection import EntityInspector

        # Get entity info at cursor position
        entity_info = EntityInspector.get_entity_at_position(game, game.look_cursor_position)

        # Panel starts after status bar, in the log area
        panel_x = GameConfig.GAME_AREA_WIDTH() + 1
        panel_y = 3  # Start below log header

        # Draw separator
        render_char_safe(console, panel_x, panel_y, "─" * (GameConfig.LOG_WIDTH - 1), fg=Colors.YELLOW, bg=Colors.LOG_BG)
        panel_y += 1

        # Render inspection header
        header = "INSPECTING:"
        render_char_safe(console, panel_x, panel_y, header, fg=Colors.YELLOW, bg=Colors.LOG_BG)
        panel_y += 1

        # Render entity name (with color)
        name_lines = self._wrap_text(entity_info['name'], GameConfig.LOG_WIDTH - 2)
        for line in name_lines:
            render_char_safe(console, panel_x, panel_y, line, fg=entity_info['color'], bg=Colors.LOG_BG)
            panel_y += 1

        # Blank line
        panel_y += 1

        # Render description
        desc_lines = self._wrap_text(entity_info['description'], GameConfig.LOG_WIDTH - 2)
        for line in desc_lines:
            if panel_y < GameConfig.SCREEN_HEIGHT - 1:
                render_char_safe(console, panel_x, panel_y, line, fg=Colors.LIGHT_GRAY, bg=Colors.LOG_BG)
                panel_y += 1

        # Blank line
        if panel_y < GameConfig.SCREEN_HEIGHT - 1:
            panel_y += 1

        # Render details if available
        if entity_info['details']:
            detail_lines = entity_info['details'].split('\n')
            for detail_line in detail_lines:
                wrapped_details = self._wrap_text(detail_line, GameConfig.LOG_WIDTH - 2)
                for line in wrapped_details:
                    if panel_y < GameConfig.SCREEN_HEIGHT - 1:
                        render_char_safe(console, panel_x, panel_y, line, fg=Colors.WHITE, bg=Colors.LOG_BG)
                        panel_y += 1

        # Draw bottom separator
        if panel_y < GameConfig.SCREEN_HEIGHT - 1:
            panel_y += 1
            render_char_safe(console, panel_x, panel_y, "─" * (GameConfig.LOG_WIDTH - 1), fg=Colors.YELLOW, bg=Colors.LOG_BG)

    def _wrap_text(self, text: str, max_width: int) -> list:
        """
        Wrap text to fit within max_width using word boundaries.

        Uses word-based wrapping to maintain readability.
        Handles single-line text and multi-line wrapping.

        Args:
            text: Text to wrap
            max_width: Maximum characters per line

        Returns:
            List of wrapped text lines
        """
        if len(text) <= max_width:
            return [text]

        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines
