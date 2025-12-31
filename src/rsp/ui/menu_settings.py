#!/usr/bin/env python3
"""
Settings Menu for Rogue Signal Protocol.

Provides settings configuration for:
- Audio (Master/SFX/Music volumes)
- Graphics Mode (Glyph vs Graphics sprites)
- Particle Effects
- UI Color themes
- Dialogue preferences
- Debug package export
"""

import logging

import tcod

from rsp.core.config import GameConfig, GameSettings
from rsp.entities.base import Colors
from rsp.ui.common import render_char_safe
from rsp.ui.help_hints import get_settings_menu_help
from rsp.ui.menu_base import BaseMenu
from rsp.utils.colors import ColorManager


class SettingsMenu(BaseMenu):
    """Settings menu for audio, graphics, and help options."""

    def __init__(self, settings: GameSettings, menu_background=None, sound_manager=None):
        super().__init__(menu_background)
        self.settings = settings  # Store settings for modification
        self.menu_background = menu_background  # Reference to background manager
        self.sound_manager = sound_manager  # For live volume updates and sound previews

        self._build_options()

        # Debug export confirmation dialogue state
        self.show_export_confirmation = False
        self.export_confirmation_selection = 0
        self.export_status_message = None  # Status message after export (success or failure)
        self.export_path = None  # Full path to exported file (shown on second line)

        # Stored coordinates for confirmation dialog click detection
        self.confirm_option_0_x_range = None  # (start_x, end_x) for "Yes"
        self.confirm_option_1_x_range = None  # (start_x, end_x) for "No"
        self.confirm_option_0_y = None  # Y coordinate for "Yes"
        self.confirm_option_1_y = None  # Y coordinate for "No"

    def _build_options(self):
        """Build options list based on current graphics mode.

        Some options (Particle Effects, UI Scale) only apply to graphics mode
        and are hidden in glyph/classic mode.
        """
        is_graphics_mode = self.settings.graphics_mode == "graphics"

        self.options = [
            {"name": "Master Volume", "type": "volume", "key": "master"},
            {"name": "SFX Volume", "type": "volume", "key": "sfx"},
            {"name": "Music Volume", "type": "volume", "key": "music"},
            {"name": "Music Boost", "type": "tristate_toggle", "key": "music_boost"},
            {
                "name": "Graphics Mode",
                "type": "toggle",
                "key": "graphics_mode",
                "values": ["Classic", "Graphics"],
            },
        ]

        # Graphics-only options
        if is_graphics_mode:
            self.options.append(
                {"name": "Particle Effects", "type": "bool_toggle", "key": "show_particle_effects"}
            )
            self.options.append(
                {"name": "UI Scale", "type": "ui_scale", "key": "ui_scale"}  # Restart required
            )

        # Common options that apply to both modes
        self.options.extend(
            [
                {
                    "name": "UI Color",
                    "type": "ui_color",
                    "key": "ui_color",
                    "values": [
                        "Cyan",
                        "Purple",
                        "Magenta",
                        "Golden",
                        "Crimson",
                        "Azure",
                        "Emerald",
                        "Ivory",
                    ],
                },
                {
                    "name": "Overclock Warnings",
                    "type": "dialogue_toggle",
                    "key": "show_overclock_warning",
                },
                {
                    "name": "System Crash Warnings",
                    "type": "dialogue_toggle",
                    "key": "show_system_crash_warning",
                },
                {"type": "separator"},  # Visual separation before utility actions
                {"name": "Export Debug Package", "type": "action"},
                {"name": "Back", "type": "action"},
            ]
        )

    def render(self, console: tcod.console.Console) -> None:
        """Render the settings menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()

        # Show confirmation dialogue if active
        if self.show_export_confirmation:
            self._render_export_confirmation_dialog(console)
            return

        # Calculate menu height - match Main Menu for consistent transitions
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Same as Main Menu (46 tiles)

        # Get UI color for decorations
        ui_color = self.settings.get_ui_color_rgb()

        # Render the right-side box using common method (match Main Menu y_offset)
        box = self._render_right_side_box(console, menu_height, ui_color, y_offset=3)

        # Title
        title = "SETTINGS"
        if box["use_background_layout"]:
            render_char_safe(
                console,
                box["center_x"] - len(title) // 2,
                box["top"] + 2,
                title,
                fg=Colors.WHITE,
                bg=Colors.BLACK,
            )
        else:
            render_char_safe(
                console,
                box["center_x"] - len(title) // 2,
                box["top"] + 2,
                title,
                fg=Colors.WHITE,
                bg=Colors.BLACK,
            )

        # Options - use spacing=3 for both modes for better readability
        # In glyph mode, dialogue_toggle items need space for the checkbox line
        start_y = box["top"] + 5
        spacing = 3  # Same spacing for both modes
        render_index = 0  # Track rendered items separately (skipping separators)
        for i, option in enumerate(self.options):
            # Skip separator - no extra spacing, just continue
            if option.get("type") == "separator":
                # Don't increment render_index - separator adds no space
                continue

            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            bg_color = (
                ColorManager.get("backgrounds", "menu_highlight")
                if i == self.selected_option
                else Colors.BLACK
            )
            option_y = start_y + render_index * spacing
            render_index += 1

            if box["use_background_layout"]:
                # Narrow box layout
                name_x = box["content_left"] + 1

                # Option name (no truncation needed - values are on separate lines)
                name = option["name"]

                # Section headers
                if option["type"] == "section_header":
                    render_char_safe(console, name_x, option_y, name, fg=ui_color, bg=Colors.BLACK)
                else:
                    render_char_safe(console, name_x, option_y, name, fg=color, bg=bg_color)

                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 10  # Slightly longer bar for better visual
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar with block characters - cleaner look
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    # Add triangle arrows to show adjustability
                    bar_text = f"◀ {bar} ▶ {volume_percent:3d}%"
                    render_char_safe(console, name_x, option_y + 1, bar_text, fg=color, bg=bg_color)

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = (
                            "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        )
                        render_char_safe(
                            console,
                            name_x,
                            option_y + 1,
                            f"< {current_value} >",
                            fg=color,
                            bg=bg_color,
                        )

                elif option["type"] == "ui_color":
                    current_value = self.settings.ui_color.capitalize()
                    # Show the color name in its actual color for preview
                    color_rgb = self.settings.get_ui_color_rgb()
                    render_char_safe(
                        console,
                        name_x,
                        option_y + 1,
                        f"< {current_value} >",
                        fg=color_rgb,
                        bg=bg_color,
                    )

                elif option["type"] == "bool_toggle":
                    # Boolean toggle (on/off)
                    is_enabled = getattr(self.settings, option["key"], True)
                    status = "ON " if is_enabled else "OFF"
                    render_char_safe(
                        console, name_x, option_y + 1, f"< {status} >", fg=color, bg=bg_color
                    )

                elif option["type"] == "tristate_toggle":
                    # Tristate: Auto/ON/OFF (for music_boost)
                    value = getattr(self.settings, option["key"], None)
                    if value is None:
                        status = "Auto"
                    elif value:
                        status = "ON"
                    else:
                        status = "OFF"
                    render_char_safe(
                        console, name_x, option_y + 1, f"< {status} >", fg=color, bg=bg_color
                    )

                elif option["type"] == "ui_scale":
                    # UI Scale with restart warning
                    current_value = self.settings.ui_scale.capitalize()
                    # Short text for narrow box
                    render_char_safe(
                        console,
                        name_x,
                        option_y + 1,
                        f"< {current_value} > *",
                        fg=color,
                        bg=bg_color,
                    )

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, "dialogue_preferences", {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    # Render on next line for narrow box (like volume controls)
                    render_char_safe(
                        console, name_x, option_y + 1, f"{status} Enabled", fg=color, bg=bg_color
                    )
            else:
                # Glyph mode - wider layout (shifted 1 left for better fit)
                # Option name
                if option["type"] == "section_header":
                    render_char_safe(
                        console,
                        box["content_left"] + 1,
                        option_y,
                        option["name"],
                        fg=ui_color,
                        bg=Colors.BLACK,
                    )
                else:
                    render_char_safe(
                        console,
                        box["content_left"] + 1,
                        option_y,
                        option["name"],
                        fg=color,
                        bg=bg_color,
                    )

                # Option value (shifted 1 more left for better margin from right edge)
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 16  # Wider bar for classic mode
                    filled_length = int(bar_length * volume_percent / 100)

                    # Volume bar with block characters - cleaner look
                    bar = "█" * filled_length + "░" * (bar_length - filled_length)
                    # Add triangle arrows to show adjustability
                    bar_text = f"◀ {bar} ▶ {volume_percent:3d}%"
                    render_char_safe(
                        console, box["content_left"] + 16, option_y, bar_text, fg=color, bg=bg_color
                    )

                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = (
                            "Graphics" if self.settings.graphics_mode == "graphics" else "Classic"
                        )
                        render_char_safe(
                            console,
                            box["content_left"] + 16,
                            option_y,
                            f"< {current_value} >",
                            fg=color,
                            bg=bg_color,
                        )

                elif option["type"] == "ui_color":
                    current_value = self.settings.ui_color.capitalize()
                    # Show the color name in its actual color for preview
                    color_rgb = self.settings.get_ui_color_rgb()
                    render_char_safe(
                        console,
                        box["content_left"] + 16,
                        option_y,
                        f"< {current_value} >",
                        fg=color_rgb,
                        bg=bg_color,
                    )

                elif option["type"] == "bool_toggle":
                    # Boolean toggle (on/off)
                    is_enabled = getattr(self.settings, option["key"], True)
                    status = "ON " if is_enabled else "OFF"
                    render_char_safe(
                        console,
                        box["content_left"] + 16,
                        option_y,
                        f"< {status} >",
                        fg=color,
                        bg=bg_color,
                    )

                elif option["type"] == "tristate_toggle":
                    # Tristate: Auto/ON/OFF (for music_boost)
                    value = getattr(self.settings, option["key"], None)
                    if value is None:
                        status = "Auto"
                    elif value:
                        status = "ON"
                    else:
                        status = "OFF"
                    render_char_safe(
                        console,
                        box["content_left"] + 16,
                        option_y,
                        f"< {status} >",
                        fg=color,
                        bg=bg_color,
                    )

                elif option["type"] == "ui_scale":
                    # UI Scale with restart warning
                    current_value = self.settings.ui_scale.capitalize()
                    render_char_safe(
                        console,
                        box["content_left"] + 16,
                        option_y,
                        f"< {current_value} > (Restart Required)",
                        fg=color,
                        bg=bg_color,
                    )

                elif option["type"] == "dialogue_toggle":
                    # Get dialogue preference (default to True if not set)
                    dialogue_prefs = getattr(self.settings, "dialogue_preferences", {})
                    is_enabled = dialogue_prefs.get(option["key"], True)
                    status = "[X]" if is_enabled else "[ ]"
                    # Render on next line (like volume controls) to avoid overlap
                    render_char_safe(
                        console,
                        box["content_left"] + 1,
                        option_y + 1,
                        f"{status} Enabled",
                        fg=color,
                        bg=bg_color,
                    )

        # Status message (debug export result) - shown on two lines for readability
        if self.export_status_message:
            msg_color = Colors.GREEN if "Success" in self.export_status_message else Colors.RED
            msg_x = box["center_x"] - len(self.export_status_message) // 2
            msg_y = box["bottom"] - 9
            render_char_safe(
                console,
                msg_x,
                msg_y,
                self.export_status_message,
                fg=msg_color,
                bg=Colors.BLACK,
            )
            # Show path on second line (truncated to fit box if needed)
            if self.export_path:
                path_str = str(self.export_path)
                max_width = box["content_width"] - 4
                if len(path_str) > max_width:
                    # Truncate from start to show the filename
                    path_str = "..." + path_str[-(max_width - 3) :]
                path_x = box["center_x"] - len(path_str) // 2
                render_char_safe(
                    console,
                    path_x,
                    msg_y + 1,
                    path_str,
                    fg=Colors.LIGHT_GRAY,
                    bg=Colors.BLACK,
                )

        # Show "* Restart Required" note in graphics mode (explains the * on UI Scale)
        if box["use_background_layout"]:
            restart_note = "* Restart Required"
            note_x = box["center_x"] - len(restart_note) // 2
            render_char_safe(
                console,
                note_x,
                box["bottom"] - 4,
                restart_note,
                fg=Colors.DARK_GRAY,
                bg=Colors.BLACK,
            )

        # Instructions - dynamically reflects current bindings (always at very bottom)
        instructions = get_settings_menu_help(box["use_background_layout"], self.input_mapper)
        inst_x = box["center_x"] - len(instructions) // 2
        render_char_safe(
            console,
            inst_x,
            box["bottom"] - 2,
            instructions,
            fg=Colors.LIGHT_GRAY,
            bg=Colors.BLACK,
        )

    # ========================================================================
    # BASEINPUTHANDLER ABSTRACT METHODS
    # ========================================================================

    def get_context(self):
        """Return input context - DIALOGUE for confirmation, SETTINGS_MENU otherwise."""
        from rsp.input.actions import InputContext

        return (
            InputContext.DIALOGUE if self.show_export_confirmation else InputContext.SETTINGS_MENU
        )

    def execute_action(self, action) -> str:
        """Execute an InputAction and return menu command."""
        from rsp.input.actions import InputAction

        # Handle confirmation dialog if active
        if self.show_export_confirmation:
            return self._execute_confirmation_action(action)

        # Navigation (UP/DOWN)
        if action in (InputAction.NAVIGATE_UP, InputAction.MOVE_NORTH):
            self._navigate_skip_headers(-1)
            return ""
        elif action in (InputAction.NAVIGATE_DOWN, InputAction.MOVE_SOUTH):
            self._navigate_skip_headers(1)
            return ""

        # Value adjustment (LEFT/RIGHT for volume, toggles, etc.)
        elif action in (InputAction.NAVIGATE_LEFT, InputAction.MOVE_WEST):
            self._adjust_setting(-1)
            return ""
        elif action in (InputAction.NAVIGATE_RIGHT, InputAction.MOVE_EAST):
            self._adjust_setting(1)
            return ""

        # Confirm/Select
        elif action == InputAction.CONFIRM:
            option = self.options[self.selected_option]
            if option["type"] == "action":
                if option["name"] == "Back":
                    return "back"
                elif option["name"] == "Export Debug Package":
                    # Show confirmation dialogue
                    self.show_export_confirmation = True
                    self.export_confirmation_selection = 0
                    return ""
            elif option["type"] in ("toggle", "bool_toggle", "dialogue_toggle"):
                # Trigger toggle with Enter/B button
                self._adjust_setting(1)
                return ""
            return ""

        # Cancel/Back
        elif action == InputAction.CANCEL:
            return "back"

        return ""

    def _execute_confirmation_action(self, action) -> str:
        """Handle confirmation dialog actions through unified input system."""
        from rsp.input.actions import InputAction

        # Navigation (swap between Yes/No)
        if action in (
            InputAction.NAVIGATE_UP,
            InputAction.NAVIGATE_DOWN,
            InputAction.NAVIGATE_LEFT,
            InputAction.NAVIGATE_RIGHT,
            InputAction.MOVE_NORTH,
            InputAction.MOVE_SOUTH,
            InputAction.MOVE_WEST,
            InputAction.MOVE_EAST,
        ):
            self.export_confirmation_selection = 1 - self.export_confirmation_selection
            return ""

        # Confirm selection
        elif action == InputAction.CONFIRM:
            if self.export_confirmation_selection == 0:  # Yes, Export
                self.show_export_confirmation = False
                return "export_debug_confirmed"
            else:  # No, Cancel
                self.show_export_confirmation = False
            return ""

        # Cancel dialogue
        elif action == InputAction.CANCEL:
            self.show_export_confirmation = False
            return ""

        return ""

    # NOTE: handle_input() inherited from BaseInputHandler handles keyboard, gamepad, and mouse.
    # Do NOT override - the base class routes events through execute_action() correctly.
    # Confirmation dialog is handled via get_context() returning DIALOGUE and execute_action().

    def _navigate_skip_headers(self, direction: int):
        """Navigate options while skipping section headers and separators."""
        num_options = len(self.options)

        # Move in the specified direction with wraparound
        self.selected_option = (self.selected_option + direction) % num_options

        # Skip section headers and separators (non-selectable items)
        non_selectable_types = {"section_header", "separator"}
        attempts = 0
        while (
            self.options[self.selected_option].get("type") in non_selectable_types
            and attempts < num_options
        ):
            self.selected_option = (self.selected_option + direction) % num_options
            attempts += 1

    # ========================================================================
    # MOUSE HANDLING (override BaseMenu for confirmation dialog support)
    # ========================================================================

    def handle_mouse_motion(self, event) -> str:
        """Handle mouse motion - update selection in settings menu or confirmation dialogue."""
        # Priority: Handle confirmation dialogue if active
        if self.show_export_confirmation:
            self._handle_confirmation_mouse_motion(event)
            return ""

        from rsp.core.config import GameConfig

        # Check for tile coordinates (set by MenuMouseHandler.convert_to_tile_coords)
        # Prefer event.tile, fall back to event.position for test compatibility
        tile_y = None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_y = int(coord_source.y)
                        break
                    except (TypeError, ValueError, AttributeError):
                        continue
        if tile_y is None:
            return ""

        # Calculate box dimensions the same way render() does
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Must match render() method (46 tiles)
        y_offset = 3  # Must match render() method
        layout = self._get_menu_layout_params()

        # Calculate box top (same logic as _render_right_side_box with y_offset)
        if layout["use_background_layout"]:
            box_top = y_offset - 1  # With y_offset=3, box_top = 2
        else:
            box_top = (GameConfig.SCREEN_HEIGHT - menu_height) // 2

        # Options start at box_top + 5 with spacing 3 for both modes
        start_y = box_top + 5
        spacing = 3  # Must match render() method

        # Calculate which option was hovered
        # Note: separators don't take up space, so we need to map render_index to actual option index
        if tile_y >= start_y:
            render_index = (tile_y - start_y) // spacing

            # Map render_index to actual option index (skipping separators)
            actual_index = 0
            rendered_count = 0
            for idx, opt in enumerate(self.options):
                if opt.get("type") == "separator":
                    continue  # Separators don't count toward render position
                if rendered_count == render_index:
                    actual_index = idx
                    break
                rendered_count += 1

            if 0 <= actual_index < len(self.options):
                # Skip section headers and separators - they're not selectable
                if self.options[actual_index]["type"] in ("section_header", "separator"):
                    return ""

                self.selected_option = actual_index

        return ""

    def _handle_confirmation_mouse_motion(self, event):
        """Handle mouse motion in confirmation dialog - update selection."""
        # Check for tile coordinates (set by MenuMouseHandler.convert_to_tile_coords)
        # Prefer event.tile, fall back to event.position for test compatibility
        tile_x, tile_y = None, None
        for attr_name in ("tile", "position"):
            if hasattr(event, attr_name):
                coord_source = getattr(event, attr_name)
                if coord_source is not None:
                    try:
                        tile_x = int(coord_source.x)
                        tile_y = int(coord_source.y)
                        break
                    except (TypeError, ValueError, AttributeError):
                        continue
        if tile_x is None or tile_y is None:
            return

        # Check if hovering over option 0
        if (
            hasattr(self, "confirm_option_0_y")
            and hasattr(self, "confirm_option_0_x_range")
            and self.confirm_option_0_y is not None
            and self.confirm_option_0_x_range is not None
        ):

            start_x, end_x = self.confirm_option_0_x_range
            if tile_y == self.confirm_option_0_y and start_x <= tile_x < end_x:
                self.export_confirmation_selection = 0
                return

        # Check if hovering over option 1
        if (
            hasattr(self, "confirm_option_1_y")
            and hasattr(self, "confirm_option_1_x_range")
            and self.confirm_option_1_y is not None
            and self.confirm_option_1_x_range is not None
        ):

            start_x, end_x = self.confirm_option_1_x_range
            if tile_y == self.confirm_option_1_y and start_x <= tile_x < end_x:
                self.export_confirmation_selection = 1
                return

    def _handle_confirmation_mouse_click(self, event) -> str:
        """Handle mouse click in confirmation dialog - execute selected option."""
        # Update selection based on click position
        self._handle_confirmation_mouse_motion(event)

        # Execute the selected option (same as pressing Enter)
        if self.export_confirmation_selection == 0:  # Yes, Export
            self.show_export_confirmation = False
            return "export_debug_confirmed"
        else:  # No, Cancel
            self.show_export_confirmation = False
            return ""

    def handle_left_click(self, event) -> str:
        """Handle left click - activate clicked option (for toggle/action types) or confirmation dialogue."""
        # Priority: Handle confirmation dialogue if active
        if self.show_export_confirmation:
            return self._handle_confirmation_mouse_click(event)

        # First update selection based on click position
        self.handle_mouse_motion(event)

        option = self.options[self.selected_option]

        # Handle different option types
        if option["type"] == "action":
            if option["name"] == "Back":
                return "back"
            elif option["name"] == "Export Debug Package":
                # Show confirmation dialogue
                self.show_export_confirmation = True
                self.export_confirmation_selection = 0  # Default to "Yes, Export"
                return ""
        elif option["type"] == "toggle":
            # Toggle the value (same as pressing Enter)
            if option["key"] == "graphics_mode":
                current_mode = self.settings.graphics_mode
                new_mode = "graphics" if current_mode == "glyph" else "glyph"
                self.settings.set_graphics_mode(new_mode)

                # Immediately update background to reflect the change
                if self.menu_background:
                    self.menu_background.reload_if_mode_changed()
                    logging.info(
                        f"Graphics mode changed to {new_mode} via mouse - background updated"
                    )

                # Rebuild options (Particle Effects/UI Scale only in graphics mode)
                self._build_options()
                # Reset selection to Graphics Mode option (index 4)
                self.selected_option = min(self.selected_option, len(self.options) - 1)
        elif option["type"] == "bool_toggle":
            # Toggle boolean setting
            current_value = getattr(self.settings, option["key"], True)
            new_value = not current_value
            setattr(self.settings, option["key"], new_value)
            self.settings.save_settings()
            logging.info(f"Setting '{option['key']}' set to {new_value} via mouse")
        elif option["type"] == "tristate_toggle":
            # Cycle through Auto -> ON -> OFF -> Auto (same as keyboard)
            self._adjust_setting(1)
        elif option["type"] == "ui_scale":
            # Cycle through scales (same as keyboard)
            self._adjust_setting(1)
        elif option["type"] == "dialogue_toggle":
            # Toggle dialogue preference
            dialogue_prefs = getattr(self.settings, "dialogue_preferences", {})
            current_value = dialogue_prefs.get(option["key"], True)
            new_value = not current_value

            # Update preference
            if not hasattr(self.settings, "dialogue_preferences"):
                self.settings.dialogue_preferences = {}
            self.settings.dialogue_preferences[option["key"]] = new_value
            self.settings.save_settings()
            logging.info(f"Dialogue preference '{option['key']}' set to {new_value} via mouse")
        elif option["type"] == "ui_color":
            # UI color selector: clicking left side cycles backward, right side cycles forward
            # Determine which half of the color display was clicked
            try:
                tile_x = int(event.tile.x)
            except (TypeError, ValueError, AttributeError) as e:
                logging.debug(
                    f"Mouse event tile X coordinate conversion failed in ui_color handler: {e}"
                )
                return ""

            # Calculate color display position using actual box dimensions
            layout = self._get_menu_layout_params()

            if layout["use_background_layout"]:
                # Graphics mode - narrow box (28 chars wide)
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1
                # UI color rendered at: name_x = content_left + 1 (on second line, like volume)
                # Text format: "< ColorName >"
                color_start_x = content_left + 1
            else:
                # Glyph mode - wide box (50 chars wide)
                box_width = 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2
                # UI color rendered at: content_left + 16
                # Text format: "< ColorName >"
                color_start_x = content_left + 16

            # The color text is formatted as "< ColorName >"
            # Example: "< Cyan >" has length 8
            # Get current color name to calculate width
            current_color_name = self.settings.ui_color.capitalize()
            color_display_width = len(f"< {current_color_name} >")
            color_mid = color_start_x + (color_display_width // 2)

            # Left half = previous color, right half = next color
            direction = -1 if tile_x < color_mid else 1
            self._adjust_setting(direction)
        elif option["type"] == "volume":
            # Volume sliders: clicking left side decreases, right side increases
            # (left = 0%, right = 100%)
            # Determine which half of the slider bar was clicked
            try:
                tile_x = int(event.tile.x)
            except (TypeError, ValueError, AttributeError) as e:
                logging.debug(
                    f"Mouse event tile X coordinate conversion failed in volume handler: {e}"
                )
                return ""

            # Calculate slider bar position using actual box dimensions
            # Must match the rendering code exactly
            layout = self._get_menu_layout_params()

            if layout["use_background_layout"]:
                # Graphics mode - narrow box (28 chars wide)
                box_width = 28
                box_right = GameConfig.SCREEN_WIDTH - 2 - 3
                box_left = box_right - box_width
                content_left = box_left + 1

                # Bar rendered at: name_x = content_left + 1
                # Bar text: "◀ ██████████ ▶ XXX%"
                bar_start_x = content_left + 1
                bar_length = 10  # Graphics mode bar

                # Bar content starts at bar_start_x + 2 (after "◀ ")
                bar_content_start = bar_start_x + 2
                bar_content_end = bar_content_start + bar_length - 1
                bar_mid = (bar_content_start + bar_content_end) // 2
            else:
                # Classic mode - wide box (50 chars wide)
                box_width = 50
                box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
                content_left = box_left + 2

                # Bar rendered at: content_left + 16
                # Bar text: "◀ ████████████████ ▶ XXX%"
                bar_start_x = content_left + 16
                bar_length = 16  # Classic mode bar

                # Bar content starts at bar_start_x + 2 (after "◀ ")
                bar_content_start = bar_start_x + 2
                bar_content_end = bar_content_start + bar_length - 1
                bar_mid = (bar_content_start + bar_content_end) // 2

            # Left half = decrease (toward 0%), right half = increase (toward 100%)
            direction = -1 if tile_x < bar_mid else 1
            self._adjust_setting(direction)

        return ""

    def handle_right_click(self, event) -> str:
        """Handle right click - go back or cancel confirmation."""
        # If confirmation dialogue is open, right-click closes it
        if self.show_export_confirmation:
            self.show_export_confirmation = False
            return ""
        # Otherwise go back to main menu
        return "back"

    def handle_mouse_wheel(self, event) -> str:
        """Handle mouse wheel - navigate through settings options with wraparound."""
        if not hasattr(event, "y"):
            return ""

        if event.y > 0:
            # Scroll up - move selection up (with wraparound)
            self._navigate_skip_headers(-1)
        elif event.y < 0:
            # Scroll down - move selection down (with wraparound)
            self._navigate_skip_headers(1)

        return ""

    def _render_export_confirmation_dialog(self, console: tcod.console.Console) -> None:
        """Render debug export confirmation dialog with background-aware positioning."""
        # Calculate dialog height
        dialog_height = 26

        # Render the right-side box using common method
        box = self._render_right_side_box(console, dialog_height, Colors.GOLDEN)

        # Title
        render_char_safe(
            console,
            box["center_x"] - 10,
            box["top"] + 2,
            "EXPORT DEBUG PACKAGE",
            fg=Colors.GOLDEN,
            bg=Colors.BLACK,
        )

        # Message - adjust for narrow box
        if box["use_background_layout"]:
            # Narrow box - break text into shorter lines
            messages = [
                "This will create a",
                "debug package with:",
                "",
                "• Save files",
                "• Settings",
                "• Game logs",
                "• Metrics",
                "• System info",
                "",
                "Saved to:",
                "debug_exports/",
                "",
                "This helps devs",
                "fix bugs.",
                "",
                "Continue?",
            ]
        else:
            # Glyph mode - use longer lines
            messages = [
                "This will create a debug package containing:",
                "",
                "• Your save files and settings",
                "• Game logs and metrics",
                "• System information",
                "",
                "This package can help developers fix bugs.",
                "",
                "Package will be saved to:",
                "  debug_exports/debug_YYYY-MM-DD_HHMM.zip",
                "",
                "Continue?",
            ]

        for i, msg in enumerate(messages):
            msg_x = (
                box["content_left"] + 1 if len(msg) <= box["content_width"] else box["content_left"]
            )
            render_char_safe(
                console, msg_x, box["top"] + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK
            )

        # Options
        options = ["Yes, Export", "No, Cancel"]
        options_start_y = box["bottom"] - 4

        for i, option in enumerate(options):
            color = (
                Colors.GOLDEN
                if i == self.export_confirmation_selection and i == 0
                else Colors.YELLOW if i == self.export_confirmation_selection else Colors.WHITE
            )
            prefix = "> " if i == self.export_confirmation_selection else "  "

            if box["use_background_layout"]:
                # Narrow box - shorter option text and center alignment
                short_options = ["Yes, Export", "No, Cancel"]
                option_text = short_options[i]
                option_x = box["center_x"] - len(option_text) // 2 - 1
            else:
                # Glyph mode - use full option text
                option_text = option
                option_x = box["center_x"] - len(option_text) // 2 - 1

            full_text = f"{prefix}{option_text}"
            render_char_safe(
                console, option_x, options_start_y + i, full_text, fg=color, bg=Colors.BLACK
            )

            # Store X range for click detection (includes prefix)
            start_x = option_x
            end_x = option_x + len(full_text)
            if i == 0:
                self.confirm_option_0_x_range = (start_x, end_x)
                self.confirm_option_0_y = options_start_y + i
            else:
                self.confirm_option_1_x_range = (start_x, end_x)
                self.confirm_option_1_y = options_start_y + i

    def _adjust_setting(self, direction: int):
        """Adjust the currently selected setting."""
        option = self.options[self.selected_option]

        if option["type"] == "volume":
            current_percent = self.settings.get_volume_percent(option["key"])
            new_percent = max(0, min(100, current_percent + (direction * 5)))
            self.settings.set_volume_percent(option["key"], new_percent)

            # Update sound manager volumes immediately for live feedback
            if self.sound_manager:
                self.sound_manager.update_volumes()

                # Play a preview sound for the adjusted volume type
                import random

                try:
                    if option["key"] == "sfx":
                        # Play a random sound effect to preview volume
                        preview_sounds = [
                            "player_move",
                            "item_pickup_code",
                            "ui_menu_open",
                            "node_activate",
                            "exploit_system_hop",
                        ]
                        sound_id = random.choice(preview_sounds)
                        if sound_id in self.sound_manager.sounds:
                            self.sound_manager.play_sound(sound_id)
                    elif option["key"] == "music":
                        # Update music volume immediately (if music is playing)
                        pass  # Music volume is already updated by update_volumes()
                except Exception as e:
                    logging.debug(f"Could not play volume preview sound: {e}")

        elif option["type"] == "toggle":
            if option["key"] == "graphics_mode":
                current_mode = self.settings.graphics_mode
                new_mode = "graphics" if current_mode == "glyph" else "glyph"
                self.settings.set_graphics_mode(new_mode)

                # Immediately update background to reflect the change
                if self.menu_background:
                    self.menu_background.reload_if_mode_changed()
                    logging.info(f"Graphics mode changed to {new_mode} - background updated")

                # Rebuild options (Particle Effects/UI Scale only in graphics mode)
                self._build_options()
                # Keep selection valid
                self.selected_option = min(self.selected_option, len(self.options) - 1)

        elif option["type"] == "ui_color":
            # Cycle through UI colors
            colors = ["cyan", "purple", "magenta", "golden", "crimson", "azure", "emerald", "ivory"]
            current_idx = (
                colors.index(self.settings.ui_color) if self.settings.ui_color in colors else 0
            )
            new_idx = (current_idx + direction) % len(colors)
            self.settings.set_ui_color(colors[new_idx])
            logging.info(f"UI color changed to {colors[new_idx]}")

        elif option["type"] == "bool_toggle":
            # Toggle boolean setting
            current_value = getattr(self.settings, option["key"], True)
            new_value = not current_value
            setattr(self.settings, option["key"], new_value)
            self.settings.save_settings()
            logging.info(f"Setting '{option['key']}' set to {new_value}")

        elif option["type"] == "tristate_toggle":
            # Cycle through Auto -> ON -> OFF -> Auto
            current_value = getattr(self.settings, option["key"], None)
            if current_value is None:
                new_value = True  # Auto -> ON
            elif current_value:
                new_value = False  # ON -> OFF
            else:
                new_value = None  # OFF -> Auto
            self.settings.set_music_boost(new_value)

            # Update sound manager volumes immediately for live feedback
            if self.sound_manager:
                self.sound_manager.update_volumes()
            logging.info(f"Setting '{option['key']}' set to {new_value}")

        elif option["type"] == "ui_scale":
            # Cycle through Auto -> Compact -> Normal -> Auto
            scales = ["auto", "compact", "normal"]
            current_idx = (
                scales.index(self.settings.ui_scale) if self.settings.ui_scale in scales else 0
            )
            new_idx = (current_idx + direction) % len(scales)
            self.settings.set_ui_scale(scales[new_idx])
            logging.info(f"UI scale changed to {scales[new_idx]} (restart required)")

        elif option["type"] == "dialogue_toggle":
            # Toggle dialogue preference
            dialogue_prefs = getattr(self.settings, "dialogue_preferences", {})
            current_value = dialogue_prefs.get(option["key"], True)
            new_value = not current_value

            # Update preference
            if not hasattr(self.settings, "dialogue_preferences"):
                self.settings.dialogue_preferences = {}
            self.settings.dialogue_preferences[option["key"]] = new_value
            self.settings.save_settings()
