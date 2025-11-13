#!/usr/bin/env python3
"""
Rogue Signal Protocol - About Menu

Displays game information and community links.
Links open in user's default browser when selected.
"""

import logging
import webbrowser

import tcod

from game_color_manager import ColorManager
from game_config import GameConfig
from game_entities import Colors
from game_menu_base import BaseMenu
from game_ui import UniversalInputHandler, render_char_safe


class AboutMenu(BaseMenu):
    """
    About menu displaying game information and community links.

    Shows:
    - Brief game description
    - List of clickable/selectable links (Itch.io, Discord, GitHub)
    - Navigation instructions

    Links open in user's default browser when activated.
    """

    def __init__(self, background=None, settings=None):
        """
        Initialize About menu.

        Args:
            background: Optional MenuBackground instance
            settings: GameSettings instance for UI color
        """
        super().__init__(background)
        self.settings = settings

        # Links in order: Itch, Discord, GitHub (as requested)
        # Each link has name on first line, description on second line
        self.links = [
            {
                "name": "Itch.io",
                "description": "Download & Rate",
                "url": "https://dragynrain.itch.io/rogue-signal-protocol",
                "color": Colors.NEON_PINK,
            },
            {
                "name": "Discord",
                "description": "Join Community",
                "url": "https://discord.gg/aUZgmrpU",
                "color": Colors.ELECTRIC_PURPLE,
            },
            {
                "name": "GitHub",
                "description": "Source & Issues",
                "url": "https://github.com/Dragynrain/RogueSignalProtocol",
                "color": Colors.CYAN,
            },
            {
                "name": "Back",
                "description": None,  # No description for Back
                "url": None,  # Special: returns to main menu
                "color": Colors.WHITE,
            },
        ]

        # Set options for base class mouse handling
        self.options = [link["name"] for link in self.links]
        self.selected_option = 0

        # Store Y positions for click detection (set during render)
        # Each entry is (y_start, y_end) for the two-line clickable area
        self.link_y_ranges = []

    def render(self, console: tcod.console.Console) -> None:
        """Render the about menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Calculate menu height - match Main Menu and Settings for consistency
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Same as Main Menu (46 tiles)

        # Get UI color for border
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        # Render the right-side box using common method (match Main Menu y_offset)
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)

        # Title
        title = "ABOUT"
        render_char_safe(
            console,
            box["center_x"] - len(title) // 2,
            box["top"] + 2,
            title,
            fg=Colors.YELLOW,
            bg=Colors.BLACK,
        )

        # Game info - adjust for narrow/wide box
        if box["use_background_layout"]:
            # Narrow box - shorter lines
            info_lines = [
                "Rogue Signal",
                "Protocol",
                "",
                "A coffee break",
                "cyberspace stealth",
                "roguelike where you",
                "exfiltrate from",
                "corporate networks",
                "without being",
                "detected.",
                "",
                "Version 0.8.0 Alpha",
                "by Adam Forster",
                "",
                "roguesignalprotocol",
                "@gmail.com",
            ]
            info_y_start = box["top"] + 5
        else:
            # Wide box - longer lines
            info_lines = [
                "Rogue Signal Protocol",
                "",
                "A coffee break cyberspace stealth",
                "roguelike where you exfiltrate from",
                "corporate networks without detection.",
                "",
                "Version 0.8.0 Alpha",
                "by Adam Forster",
                "",
                "roguesignalprotocol@gmail.com",
            ]
            info_y_start = box["top"] + 5

        # Render info lines
        for i, line in enumerate(info_lines):
            line_x = box["center_x"] - len(line) // 2
            render_char_safe(
                console, line_x, info_y_start + i, line, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
            )

        # Links section
        links_y_start = info_y_start + len(info_lines) + 2

        # Section header
        links_header = "LINKS:"
        render_char_safe(
            console,
            box["center_x"] - len(links_header) // 2,
            links_y_start,
            links_header,
            fg=ui_color,
            bg=Colors.BLACK,
        )

        # Reset link positions for this frame
        self.link_y_ranges = []

        # Render links with spacing (3 lines per link: name, description, blank)
        current_y = links_y_start + 2
        for i, link in enumerate(self.links):
            # Determine colors
            is_selected = i == self.selected_option
            fg_color = Colors.YELLOW if is_selected else link["color"]
            bg_color = (
                ColorManager.get("backgrounds", "menu_highlight") if is_selected else Colors.BLACK
            )

            # Prefix for selected option
            prefix = "> " if is_selected else "  "

            # Line 1: Link name
            link_name = f"{prefix}{link['name']}"
            name_x = box["center_x"] - len(link_name) // 2  # Center based on full text with prefix
            render_char_safe(console, name_x, current_y, link_name, fg=fg_color, bg=bg_color)

            # Line 2: Description (if exists)
            desc_y = current_y + 1
            if link["description"]:
                desc_x = box["center_x"] - len(link["description"]) // 2
                render_char_safe(
                    console,
                    desc_x,
                    desc_y,
                    link["description"],
                    fg=Colors.LIGHT_GRAY if not is_selected else Colors.YELLOW,
                    bg=bg_color,
                )

            # Store Y range for click detection (both lines are clickable)
            y_end = desc_y if link["description"] else current_y
            self.link_y_ranges.append((current_y, y_end))

            # Move to next link (skip blank line)
            current_y = desc_y + 2

        # Instructions at bottom
        if box["use_background_layout"]:
            instructions = ["↕: Navigate", "Enter: Open", "ESC/Right-Click: Back"]
        else:
            instructions = ["↕ or W/S: Navigate", "Enter: Open Link", "ESC/Right-Click: Back"]

        inst_y_start = box["bottom"] - len(instructions) - 1
        for i, instruction in enumerate(instructions):
            inst_x = box["center_x"] - len(instruction) // 2
            render_char_safe(
                console, inst_x, inst_y_start + i, instruction, fg=Colors.CYAN, bg=Colors.BLACK
            )

    def handle_input(self, event) -> str:
        """
        Handle about menu input.

        Returns:
            'back' to exit to main menu, '' to stay in about menu
        """
        # Handle navigation
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.links)):
            return ""

        # Handle selection (Enter key)
        if UniversalInputHandler.is_confirm_key(event):
            return self._activate_selected_link()

        # Handle escape
        if UniversalInputHandler.is_escape_key(event):
            return "back"

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - update selection based on hover."""
        if not hasattr(event, "position") or event.position is None:
            return False

        tile_x = int(event.position.x)
        tile_y = int(event.position.y)

        # Check which link is being hovered over (both lines count)
        for i, (y_start, y_end) in enumerate(self.link_y_ranges):
            if y_start <= tile_y <= y_end:
                self.selected_option = i
                return True

        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - activate clicked link or right-click to go back."""
        import tcod.event

        # Right-click = go back (standard behavior)
        if hasattr(event, "button") and event.button == tcod.event.MouseButton.RIGHT:
            return "back"

        # Try to update selection based on click position (left-click only)
        clicked_on_link = self.handle_mouse_motion(event)

        # If clicked on a link, activate it
        if clicked_on_link:
            return self._activate_selected_link()

        # Left-click on empty space does nothing (removed confusing click-anywhere-to-exit)
        return ""

    def _activate_selected_link(self) -> str:
        """
        Activate the currently selected link.

        Returns:
            'back' if Back was selected, '' otherwise
        """
        if self.selected_option < 0 or self.selected_option >= len(self.links):
            return ""

        link = self.links[self.selected_option]

        # Special case: Back option
        if link["url"] is None:
            return "back"

        # Open link in browser
        try:
            logging.info(f"Opening link in browser: {link['url']}")
            webbrowser.open(link["url"])
            logging.info(f"Link opened successfully: {link['name']}")
        except Exception as e:
            logging.error(f"Failed to open link {link['url']}: {e}")

        # Stay in about menu after opening link
        return ""

    def _get_action_for_option(self, option_index: int) -> str:
        """
        Override base class method for custom action mapping.

        Args:
            option_index: Index of the selected option

        Returns:
            Action string ('back' for back button, '' for links)
        """
        if option_index >= len(self.links):
            return ""

        # Back option returns 'back', links open in browser and return ''
        if self.links[option_index]["url"] is None:
            return "back"

        # Open the link and stay in menu
        return self._activate_selected_link()
