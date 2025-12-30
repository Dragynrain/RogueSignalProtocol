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
from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_help_hints import get_about_menu_help
from game_menu_base import BaseMenu
from game_ui import render_char_safe
from game_version import VERSION_DISPLAY


class AboutMenu(BaseMenu):
    """
    About menu displaying game information and community links.

    Shows:
    - Brief game description
    - List of clickable/selectable links (Itch.io, Discord, GitHub)
    - Navigation instructions

    Links open in user's default browser when activated.
    """

    def __init__(self, background=None, test_mode=False):
        """
        Initialize About menu.

        Args:
            background: Optional MenuBackground instance
            test_mode: If True, don't open browser links (for automated testing)
        """
        super().__init__(background)
        self.test_mode = test_mode

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
                "url": "https://discord.gg/5fykUtECqz",
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

    @property
    def settings(self):
        """Get settings from global singleton."""
        return GameSettings.get_instance()

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
                VERSION_DISPLAY,
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
                VERSION_DISPLAY,
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
            # Track where this link ends (for click detection)
            y_end = current_y
            if link["description"]:
                desc_y = current_y + 1
                desc_x = box["center_x"] - len(link["description"]) // 2
                render_char_safe(
                    console,
                    desc_x,
                    desc_y,
                    link["description"],
                    fg=Colors.LIGHT_GRAY if not is_selected else Colors.YELLOW,
                    bg=bg_color,
                )
                y_end = desc_y

            # Store Y range for click detection (both lines are clickable)
            self.link_y_ranges.append((current_y, y_end))

            # Move to next link (skip blank line)
            current_y = y_end + 2

        # Instructions at bottom - dynamically reflects current bindings
        instructions = get_about_menu_help(box["use_background_layout"], self.input_mapper)
        inst_x = box["center_x"] - len(instructions) // 2
        render_char_safe(
            console, inst_x, box["bottom"] - 2, instructions, fg=Colors.CYAN, bg=Colors.BLACK
        )

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS
    # ========================================================================

    def get_context(self):
        """Return input context for this menu."""
        from game_input_actions import InputContext

        return InputContext.ABOUT_MENU

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        from game_input_actions import InputAction

        # Navigation
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self.navigate_up()
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self.navigate_down()
            return ""

        # Confirm (select link)
        elif action == InputAction.CONFIRM:
            return self._activate_selected_link()

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    # ========================================================================
    # MOUSE HANDLING (override BaseMenu defaults for custom link click zones)
    # ========================================================================

    def handle_mouse_motion(self, event) -> str:
        """Handle mouse motion - update selection based on hover (custom link zones)."""
        # Prefer event.tile, fall back to event.position for test compatibility
        # Use try/except because Mock objects pass hasattr checks
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break  # Found valid coordinates
                    except (TypeError, ValueError, AttributeError):
                        continue  # Try next attribute
        if tile_y is None:
            return ""

        # Check which link is being hovered over (both lines count)
        for i, (y_start, y_end) in enumerate(self.link_y_ranges):
            if y_start <= tile_y <= y_end:
                self.selected_option = i
                return ""

        return ""

    def handle_left_click(self, event) -> str:
        """Handle left mouse click - activate clicked link."""
        # Try to update selection based on click position
        self.handle_mouse_motion(event)

        # Activate the link
        return self._activate_selected_link()

    def handle_right_click(self, event) -> str:
        """Handle right mouse click - go back."""
        return "back"

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

        # Open link in browser (unless in test mode)
        if self.test_mode:
            logging.debug(f"[TEST MODE] Skipping browser open: {link['url']}")
            return ""

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
