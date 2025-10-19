#!/usr/bin/env python3
"""
Dialogue Renderer
Handles all popup/dialogue rendering including victory, death, gateway, and dialogue boxes.
"""

import os
import logging
from typing import List

import tcod

from game_config import GameConfig
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe


def draw_bordered_box(console: tcod.console.Console, start_x: int, start_y: int,
                     width: int, height: int, border_color: tuple, bg_color: tuple):
    """Draw a bordered box with background fill - utility function for dialogues."""
    # Ensure colors are tuples to prevent TCOD ColorRGB errors
    border_color = ensure_color_tuple(border_color)
    bg_color = ensure_color_tuple(bg_color)

    # Use TCOD's built-in box drawing for efficiency
    console.draw_rect(start_x, start_y, width, height, ord(' '), fg=Colors.WHITE, bg=bg_color)
    console.draw_frame(start_x, start_y, width, height,
                      fg=border_color, bg=bg_color, clear=False)


class DialogueRenderer:
    """Handles all popup/dialogue rendering."""

    def render_victory_message(self, console: tcod.console.Console):
        """Render victory message."""
        # Use console's LOGICAL dimensions for positioning
        center_x = console.width // 2
        center_y = console.height // 2

        box_width = 50  # Increased from 38 to fit longer messages
        box_height = 10
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        draw_bordered_box(console, start_x, start_y, box_width, box_height,
                         Colors.GREEN, Colors.BLACK)

        # Victory message - centered properly within the larger box
        title = "BREAKTHROUGH TO THE INTERNET!"
        line1 = "You've escaped into the digital realm"
        line2 = "The entire world wide web awaits you!"
        line3 = "Freedom at last..."
        instruction = "Press any key to continue"

        render_char_safe(console, center_x - len(title) // 2, start_y + 2, title, fg=Colors.GREEN, bg=Colors.BLACK)
        render_char_safe(console, center_x - len(line1) // 2, start_y + 3, line1, fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - len(line2) // 2, start_y + 4, line2, fg=Colors.CYAN, bg=Colors.BLACK)
        render_char_safe(console, center_x - len(line3) // 2, start_y + 5, line3, fg=Colors.ELECTRIC_BLUE, bg=Colors.BLACK)
        render_char_safe(console, center_x - len(instruction) // 2, start_y + 7, instruction, fg=Colors.YELLOW, bg=Colors.BLACK)

        # CRITICAL: Explicitly set alpha to 255 (opaque) for entire dialogue box
        # This ensures dialogue stays opaque even after game area transparency pass
        # Use ACTUAL array dimensions, not console.width/height!
        actual_height, actual_width = console.rgba["bg"].shape[:2]
        y_start = max(0, start_y)
        y_end = min(actual_height, start_y + box_height)
        x_start = max(0, start_x)
        x_end = min(actual_width, start_x + box_width)

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                console.rgba["bg"][y, x, 3] = 255  # TCOD uses [y, x] indexing!

    def render_gateway_confirmation(self, console: tcod.console.Console):
        """Render gateway confirmation dialog."""
        # Use console's LOGICAL dimensions for positioning
        logging.info(f"Gateway dialogue: console.width={console.width}, console.height={console.height}, array shape={console.rgba['bg'].shape}")
        center_x = console.width // 2
        center_y = console.height // 2

        box_width = 30
        box_height = 6
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        draw_bordered_box(console, start_x, start_y, box_width, box_height,
                         Colors.CYAN, Colors.BLACK)

        # Title and message
        render_char_safe(console, center_x - 7, start_y + 1, "NETWORK GATEWAY", fg=Colors.YELLOW, bg=Colors.BLACK)
        render_char_safe(console, center_x - 12, start_y + 2, "Proceed to next network?", fg=Colors.WHITE, bg=Colors.BLACK)

        # Options
        render_char_safe(console, center_x - 5, start_y + 4, "Y: Yes  N: No", fg=Colors.CYAN, bg=Colors.BLACK)

        # CRITICAL: Explicitly set alpha to 255 (opaque) for entire dialogue box
        # Use ACTUAL array dimensions, not console.width/height!
        actual_height, actual_width = console.rgba["bg"].shape[:2]
        y_start = max(0, start_y)
        y_end = min(actual_height, start_y + box_height)
        x_start = max(0, start_x)
        x_end = min(actual_width, start_x + box_width)

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                console.rgba["bg"][y, x, 3] = 255  # TCOD uses [y, x] indexing!

    def render_dialogue(self, console: tcod.console.Console, game):
        """Render active dialogue popup."""
        config = game.dialogue_manager.get_active_config()
        if not config:
            return

        # Use console's LOGICAL dimensions for positioning
        # Array shape is used for bounds checking in alpha-setting loop
        logging.info(f"Dialogue {game.dialogue_manager.active_dialogue}: console.width={console.width}, console.height={console.height}, array shape={console.rgba['bg'].shape}")
        console_width = console.width
        console_height = console.height

        box_width = min(60, console_width - 4)  # Leave 2 char margin on each side
        box_height = 12
        center_x = console_width // 2
        center_y = console_height // 2
        box_x = center_x - box_width // 2
        box_y = center_y - box_height // 2

        # Ensure colors are tuples
        border_color = ensure_color_tuple(config.color_scheme["border"])
        bg_color = ensure_color_tuple(config.color_scheme["background"])

        # Draw dialogue box using TCOD's built-in box drawing
        console.draw_rect(box_x, box_y, box_width, box_height, ord(' '), fg=Colors.WHITE, bg=bg_color)
        console.draw_frame(box_x, box_y, box_width, box_height, fg=border_color, bg=bg_color, clear=False)

        # Render title (centered)
        title_x = box_x + (box_width - len(config.title)) // 2
        render_char_safe(console, title_x, box_y + 1, config.title,
                        fg=config.color_scheme["title"], bg=bg_color)

        # Format message with context data
        try:
            formatted_message = config.message.format(**game.dialogue_manager.dialogue_data)
        except KeyError as e:
            logging.warning(f"Missing dialogue context data key: {e}")
            formatted_message = config.message

        # Render message (word-wrapped)
        message_lines = self._wrap_dialogue_text(formatted_message, box_width - 4)
        message_y = box_y + 3
        for i, line in enumerate(message_lines):
            if message_y + i < box_y + box_height - 3:  # Leave room for options
                render_char_safe(console, box_x + 2, message_y + i, line,
                               fg=config.color_scheme["message"], bg=bg_color)

        # Render options (centered at bottom)
        options_y = box_y + box_height - 2
        options_text = "  ".join(config.options)
        options_x = box_x + (box_width - len(options_text)) // 2
        render_char_safe(console, options_x, options_y, options_text,
                        fg=Colors.WHITE, bg=bg_color)

        # CRITICAL: Explicitly set alpha to 255 (opaque) for entire dialogue box
        # Use ACTUAL array dimensions for clamping
        actual_height, actual_width = console.rgba["bg"].shape[:2]
        y_start = max(0, box_y)
        y_end = min(actual_height, box_y + box_height)
        x_start = max(0, box_x)
        x_end = min(actual_width, box_x + box_width)

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                console.rgba["bg"][y, x, 3] = 255  # TCOD uses [y, x] indexing!

    def render_death_message(self, console: tcod.console.Console):
        """Render death message with frame and black backgrounds."""
        # Ensure save is deleted on death (permadeath)
        save_path = "save_game.json"
        if os.path.exists(save_path):
            os.remove(save_path)

        # Use console's LOGICAL dimensions for positioning
        center_x = console.width // 2
        center_y = console.height // 2

        # Background box with border
        box_width = 40
        box_height = 12
        start_x = center_x - box_width // 2
        start_y = center_y - box_height // 2

        # Use TCOD's efficient drawing
        console.draw_rect(start_x, start_y, box_width, box_height, ord(' '), fg=Colors.WHITE, bg=Colors.BLACK)
        console.draw_frame(start_x, start_y, box_width, box_height, fg=Colors.RED, bg=Colors.BLACK, clear=False)

        # Death message
        render_char_safe(console, center_x - 10, start_y + 2, "CONSCIOUSNESS PURGED", fg=Colors.RED, bg=Colors.BLACK)
        render_char_safe(console, center_x - 17, start_y + 4, "Your consciousness failed to escape", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 14, start_y + 5, "the network and has been purged", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 10, start_y + 6, "from existence.", fg=Colors.WHITE, bg=Colors.BLACK)
        render_char_safe(console, center_x - 13, start_y + 7, "Other subjects will try again...", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)
        render_char_safe(console, center_x - 11, start_y + 9, "Press SPACE to return to menu", fg=Colors.CYAN, bg=Colors.BLACK)

        # CRITICAL: Explicitly set alpha to 255 (opaque) for entire dialogue box
        # Use ACTUAL array dimensions, not console.width/height!
        actual_height, actual_width = console.rgba["bg"].shape[:2]
        y_start = max(0, start_y)
        y_end = min(actual_height, start_y + box_height)
        x_start = max(0, start_x)
        x_end = min(actual_width, start_x + box_width)

        for y in range(y_start, y_end):
            for x in range(x_start, x_end):
                console.rgba["bg"][y, x, 3] = 255  # TCOD uses [y, x] indexing!

    def _wrap_dialogue_text(self, text: str, max_width: int) -> List[str]:
        """
        Wrap text to fit within max_width characters.
        Handles edge cases like words longer than max_width by breaking them.

        Args:
            text: Text to wrap
            max_width: Maximum line width in characters

        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # If the word itself is longer than max_width, break it
            if word_length > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = []
                    current_length = 0

                # Break long word into chunks
                for i in range(0, word_length, max_width):
                    lines.append(word[i:i+max_width])
                continue

            # If adding this word would exceed max_width, start new line
            if current_length + word_length + len(current_line) > max_width:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length

        # Add remaining words
        if current_line:
            lines.append(" ".join(current_line))

        return lines
