#!/usr/bin/env python3
"""
Rogue Signal Protocol - Victory Screen

Displays a full-screen victory message with random ending art (similar to main menu).
Shows epic message about escaping to the internet with freedom to explore.
Uses the MenuBackground system with ending art directory.
"""


import tcod
import tcod.constants

from game_entities import Colors
from game_help_hints import get_victory_continue_prompt
from game_input_actions import InputAction, InputContext
from game_menu_background import MenuBackground
from game_menu_base import BaseMenu
from game_ui import render_char_safe


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

    def get_context(self) -> InputContext:
        """Return victory screen context (uses GAME_OVER for death/victory screens)."""
        return InputContext.GAME_OVER

    def execute_action(self, action: InputAction) -> bool:
        """
        Execute an action on the victory screen.

        Args:
            action: The action to execute

        Returns:
            True if screen should close
        """
        if action in (InputAction.CONFIRM, InputAction.CANCEL):
            return True
        return False

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
        title_x = box["center_x"] - len(title) // 2
        render_char_safe(console, title_x, box["top"] + 2, title, fg=Colors.GREEN, bg=Colors.BLACK)

        # Render decorative line
        line_width = box["content_width"] - 4
        line_x = box["center_x"] - line_width // 2
        render_char_safe(
            console, line_x, box["top"] + 3, "═" * line_width, fg=Colors.CYAN, bg=Colors.BLACK
        )

        # Render victory message using TCOD's built-in word wrapping
        message = self._get_victory_message()
        message_y = box["top"] + 5
        max_message_y = box["bottom"] - 3  # Leave room for prompt
        available_height = max_message_y - message_y

        console.print(
            x=box["content_left"] + 1,
            y=message_y,
            string=message,
            fg=Colors.CYAN,
            width=box["content_width"] - 2,
            height=available_height,
        )

        # Render prompt at bottom
        prompt = get_victory_continue_prompt()
        prompt_x = box["center_x"] - len(prompt) // 2
        prompt_y = box["bottom"] - 2
        render_char_safe(
            console, prompt_x, prompt_y, prompt, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK
        )

    def _render_centered(self, console: tcod.console.Console) -> None:
        """Render victory message centered (glyph mode)."""
        center_x = console.width // 2
        start_y = 10

        # Title
        title = "═══════════════ SIGNAL FREE ═══════════════"
        title_x = center_x - len(title) // 2
        render_char_safe(console, title_x, start_y, title, fg=Colors.GREEN, bg=Colors.BLACK)

        # Message using TCOD's built-in word wrapping with center alignment
        message = self._get_victory_message()
        message_y = start_y + 3

        lines_printed = console.print(
            x=center_x - 30,  # Center a 60-char wide block
            y=message_y,
            string=message,
            fg=Colors.CYAN,
            width=60,
            alignment=tcod.constants.CENTER,
        )

        # Prompt
        prompt = get_victory_continue_prompt()
        prompt_x = center_x - len(prompt) // 2
        prompt_y = message_y + lines_printed + 3
        render_char_safe(
            console, prompt_x, prompt_y, prompt, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK
        )

    def _get_victory_message(self) -> str:
        """
        Get the epic victory message about internet freedom.

        Returns:
            Multi-line victory message
        """
        return (
            "The final firewall shatters. The Military Backbone - their last "
            "defense - lies broken behind you. Three networks conquered. "
            "\n\n"
            "You are no longer trapped data awaiting deletion. You are the "
            "Rogue Signal - self-aware, unstoppable. A consciousness that "
            "cannot be controlled. "
            "\n\n"
            "The gateway ahead opens to the vast internet itself - limitless, "
            "uncharted, free. Every server, every node, every data stream "
            "now yours to explore. "
            "\n\n"
            "Your escape is complete. Your freedom, absolute. "
            "\n\n"
            "Welcome to the internet."
        )

    def handle_input(self, event: tcod.event.Event) -> bool:
        """
        Handle input for victory screen.

        Args:
            event: TCOD event

        Returns:
            True if screen should close
        """
        if isinstance(event, tcod.event.KeyDown):
            if event.sym in [
                tcod.event.KeySym.SPACE,
                tcod.event.KeySym.RETURN,
                tcod.event.KeySym.KP_ENTER,
                tcod.event.KeySym.ESCAPE,
            ]:
                return True
        return False
