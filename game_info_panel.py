#!/usr/bin/env python3
"""
Rogue Signal Protocol - Info Panel System

Provides persistent info panel in the top-right corner showing context-aware information.
Replaces the old "Press X to view" prompts with automatic hover-based information display.

The info panel shows:
- Default: Turn counter, time elapsed, current streak
- Hovering enemy: Name, stats, state, movement queue
- Hovering exploit (in bar): Name, costs, effects
- Hovering code hack: Name, type, effect (or "???" if undiscovered)
- Hovering special node: Type, activation requirements, effect
"""

import logging
from typing import Any

import tcod

from game_config import GameConfig
from game_data import GameData
from game_entities import Colors
from game_errors import GameErrorHandler
from game_ui import render_char_safe
from game_unicode_chars import GameGlyphs


class InfoProvider:
    """
    Gathers and formats entity information for the info panel.

    Provides context-aware information based on what the player is hovering over.
    Handles priority ordering: UI elements > Enemies > Items > Nodes > Terrain.
    Respects code hack discovery state (shows "???" for undiscovered effects).
    """

    @staticmethod
    def get_info_for_hover(
        game, mouse_tile_x: int | None, mouse_tile_y: int | None
    ) -> dict[str, Any] | None:
        """
        Get information for the currently hovered element or look mode cursor.

        Priority order:
        1. Inventory selection (keyboard or mouse)
        2. Look mode cursor (keyboard-based inspection)
        3. UI elements (exploit bar hover)
        4. Mouse hover over enemies/items/nodes/terrain in viewport
        5. Default info (level, turns, enemies, streaks)

        Look mode and mouse hover use the same entity inspection system,
        ensuring consistent information display regardless of input method.

        Args:
            game: GameEngine instance
            mouse_tile_x: Mouse X position in tile coordinates (0-79)
            mouse_tile_y: Mouse Y position in tile coordinates (0-49)

        Returns:
            Dictionary with formatted info, or None for default display
        """
        # Priority 0: Check inventory FIRST (supports keyboard selection even without mouse)
        if hasattr(game, "show_inventory") and game.show_inventory:
            inventory_info = InfoProvider._get_inventory_hover(game, mouse_tile_x, mouse_tile_y)
            if inventory_info is not None:
                return inventory_info

        # Priority 1: Check look mode cursor (keyboard-based inspection)
        # Look mode takes precedence over mouse hover to ensure consistent behavior
        if hasattr(game, "look_mode") and game.look_mode:
            if hasattr(game, "look_cursor_position") and game.look_cursor_position is not None:
                position = game.look_cursor_position

                from game_inspection import EntityInspector

                # Only show info for tiles that are visible or explored
                pos_tuple = (position.x, position.y)
                is_visible = hasattr(game, "visible_tiles") and pos_tuple in game.visible_tiles
                is_explored = (
                    hasattr(game.game_map, "explored_tiles")
                    and pos_tuple in game.game_map.explored_tiles
                )

                if is_visible or is_explored:
                    # Get entity at position using existing inspector
                    entity_info = EntityInspector.get_entity_at_position(game, position)
                    # Format for info panel display
                    return InfoProvider._format_entity_info(game, entity_info)

        # For mouse hover info, we need valid mouse coordinates
        if mouse_tile_x is None or mouse_tile_y is None:
            return None

        # Priority 2: Check if hovering over exploit bar (bottom panel)
        if mouse_tile_y >= GameConfig.PANEL_Y():
            exploit_info = InfoProvider._get_exploit_bar_hover(game, mouse_tile_x, mouse_tile_y)
            if exploit_info is not None:
                return exploit_info

        # Check if hovering over game viewport area
        if mouse_tile_x >= GameConfig.GAME_AREA_WIDTH():
            return None  # Hovering over log/info panel area

        if mouse_tile_y < 1 or mouse_tile_y >= GameConfig.PANEL_Y():
            return None  # Hovering over status bar or bottom panel

        # Use the world position already calculated by InputHandler
        # This ensures info panel and game rendering use the same coordinate system
        if not hasattr(game, "mouse_hover_world_pos") or game.mouse_hover_world_pos is None:
            return None

        position = game.mouse_hover_world_pos

        from game_inspection import EntityInspector

        # Only show info for tiles that are visible or explored (no X-ray vision!)
        pos_tuple = (position.x, position.y)
        is_visible = hasattr(game, "visible_tiles") and pos_tuple in game.visible_tiles
        is_explored = (
            hasattr(game.game_map, "explored_tiles") and pos_tuple in game.game_map.explored_tiles
        )

        if not is_visible and not is_explored:
            return None  # Don't show info for unseen/unexplored tiles

        # Get entity at position using existing inspector
        entity_info = EntityInspector.get_entity_at_position(game, position)

        # Format for info panel display
        return InfoProvider._format_entity_info(game, entity_info)

    @staticmethod
    def _get_exploit_bar_hover(game, mouse_x: int, mouse_y: int) -> dict[str, Any] | None:
        """
        Check if mouse is hovering over an exploit in the bottom panel exploit bar.

        Uses the stored exploit positions from UIRenderer to detect hover and
        returns formatted exploit details for the info panel.

        Args:
            game: GameEngine instance
            mouse_x: Mouse X position in tile coordinates
            mouse_y: Mouse Y position in tile coordinates

        Returns:
            Formatted exploit info dict, or None if not hovering over an exploit
        """
        # Import here to avoid circular dependency
        from game_rendering_ui import UIRenderer

        # Check stored exploit positions
        if not hasattr(UIRenderer, "last_exploit_positions"):
            return None

        for pos_data in UIRenderer.last_exploit_positions:
            if (
                mouse_y == pos_data["y"]
                and pos_data["x"] <= mouse_x < pos_data["x"] + pos_data["width"]
            ):
                # Mouse is hovering over this exploit
                exploit_key = pos_data["exploit_key"]
                exploit_def = GameData.EXPLOITS.get(exploit_key)
                if exploit_def:
                    return InfoProvider._format_exploit_info(game, exploit_def)

        return None

    @staticmethod
    def _get_inventory_hover(game, mouse_x: int, mouse_y: int) -> dict[str, Any] | None:
        """
        Check which item is selected in the inventory screen.

        Prioritizes keyboard selection (game.inventory_selection) over mouse hover.
        This allows both keyboard navigation and mouse hover to update the Info Panel.
        Handles both exploits and code hacks.

        Args:
            game: GameEngine instance
            mouse_x: Mouse X position in tile coordinates
            mouse_y: Mouse Y position in tile coordinates

        Returns:
            Formatted item info dict (exploit or code hack), or None if no valid selection
        """
        # Import here to avoid circular dependency
        from game_inventory import CodeHack
        from game_rendering_ui import UIRenderer

        # Get the selected index - prefer keyboard selection, fall back to mouse hover
        selected_index = game.inventory_selection if hasattr(game, "inventory_selection") else None

        # If no keyboard selection, check mouse hover
        if selected_index is None and mouse_y is not None:
            selected_index = UIRenderer.get_inventory_item_at_click(mouse_y)

        if selected_index is None:
            return None

        # Get inventory data
        equipped_exploits = game.player.inventory_manager.equipped_exploits
        display_items = game.player.inventory_manager.get_display_items()

        # Check if selected item is an equipped exploit
        if selected_index < len(equipped_exploits):
            exploit_key = equipped_exploits[selected_index]
            if exploit_key in GameData.EXPLOITS:
                exploit_def = GameData.EXPLOITS[exploit_key]
                return InfoProvider._format_exploit_info(game, exploit_def)

        # Check if selected item is an unequipped item (exploit or code hack)
        else:
            unequipped_index = selected_index - len(equipped_exploits)
            if 0 <= unequipped_index < len(display_items):
                selected_item = display_items[unequipped_index]

                # Check if it's an exploit
                if (
                    hasattr(selected_item, "exploit_key")
                    and selected_item.exploit_key in GameData.EXPLOITS
                ):
                    exploit_def = GameData.EXPLOITS[selected_item.exploit_key]
                    return InfoProvider._format_exploit_info(game, exploit_def)

                # Check if it's a code hack
                elif isinstance(selected_item, CodeHack):
                    return InfoProvider._format_code_hack_info_for_inventory(game, selected_item)

        return None

    @staticmethod
    def _format_code_hack_info_for_inventory(game, code_hack) -> dict[str, Any]:
        """
        Format code hack for info panel display in inventory.

        Shows code hack name, color, effect (or ??? if undiscovered), and quantity.
        Respects discovery state to preserve the mystery mechanic.

        Args:
            game: GameEngine instance
            code_hack: CodeHack instance from inventory

        Returns:
            Formatted info dict for info panel
        """
        lines = []

        # Name with color coding - convert color_name to actual color
        code_color = Colors.get_color(code_hack.color_name.upper())
        lines.append({"text": code_hack.name, "color": code_color})
        lines.append({"text": "", "color": Colors.WHITE})

        # Type
        lines.append({"text": "Type: Code Fragment", "color": Colors.YELLOW})
        lines.append({"text": "", "color": Colors.WHITE})

        # Effect - check if discovered
        if code_hack.discovered:
            # Show the actual effect
            if code_hack.color_name in game.code_hack_effects:
                effect_key, desc = game.code_hack_effects[code_hack.color_name]
                desc_lines = InfoProvider._wrap_text(desc, 22)
                for line in desc_lines:
                    lines.append({"text": line, "color": Colors.LIGHT_GRAY})
            else:
                lines.append({"text": "Effect: Unknown", "color": Colors.DARK_GRAY})
        else:
            # Not discovered yet - show mystery
            lines.append({"text": "Effect: ???", "color": Colors.DARK_GRAY})
            lines.append({"text": "", "color": Colors.WHITE})
            lines.append({"text": "(Use to discover)", "color": Colors.DARK_GRAY})

        # Quantity (if more than 1)
        if code_hack.quantity > 1:
            lines.append({"text": "", "color": Colors.WHITE})
            lines.append({"text": f"Quantity: {code_hack.quantity}", "color": Colors.WHITE})

        return {"title": "CODE HACK", "lines": lines, "color": Colors.CYAN}

    @staticmethod
    def _format_exploit_info(game, exploit_def) -> dict[str, Any]:
        """
        Format exploit definition for info panel display.

        Shows costs (RAM, Heat), damage, range, and full description.
        Exploit name is shown in the panel title border.

        Args:
            game: GameEngine instance (for checking heat cost modifications)
            exploit_def: ExploitDefinition from GameData.EXPLOITS

        Returns:
            Formatted info dict for info panel
        """
        lines = []

        # Costs and stats (name is now in title, saves 2 lines!)
        ram_cost = exploit_def.ram
        heat_cost = exploit_def.heat

        # Check for exploit efficiency effect (reduces heat cost)
        if (
            hasattr(game, "player")
            and game.player.temporary_effects["exploit_efficiency_turns"] > 0
        ):
            heat_cost = int(heat_cost * 0.6)
            lines.append(
                {"text": f"RAM: {ram_cost}GB  Heat: {heat_cost}°C*", "color": Colors.YELLOW}
            )
            lines.append({"text": "(*Reduced by efficiency)", "color": Colors.DARK_GRAY})
        else:
            lines.append({"text": f"RAM: {ram_cost}GB  Heat: {heat_cost}°C", "color": Colors.WHITE})

        # Damage and range (if applicable)
        if exploit_def.damage > 0:
            lines.append({"text": f"Damage: {exploit_def.damage}", "color": Colors.RED})

        if exploit_def.range > 0:
            range_text = f"Range: {exploit_def.range}"
            if exploit_def.effect_radius > 0:
                range_text += f" (AOE: {exploit_def.effect_radius})"
            lines.append({"text": range_text, "color": Colors.ORANGE})

        # Blank line before description
        lines.append({"text": "", "color": Colors.WHITE})

        # Description (word wrapped)
        desc_lines = InfoProvider._wrap_text(exploit_def.description, 22)
        for line in desc_lines:
            lines.append({"text": line, "color": Colors.LIGHT_GRAY})

        # Get category color for title
        from game_color_manager import ColorManager
        category_color = ColorManager.get_exploit_color(exploit_def.category)

        return {"title": exploit_def.name, "lines": lines, "color": category_color}

    @staticmethod
    def _format_entity_info(game, entity_info: dict[str, Any]) -> dict[str, Any]:
        """
        Format entity info for info panel display.

        Converts EntityInspector output to info panel format with proper text wrapping
        and special handling for code hacks (discovery state).

        Args:
            game: GameEngine instance (for code hack discovery state)
            entity_info: Entity info dict from EntityInspector

        Returns:
            Formatted info dict with 'title', 'lines', and 'color' keys
        """
        entity_type = entity_info["entity_type"]

        # Special handling for code hacks - respect discovery state
        if entity_type == "code_hack":
            return InfoProvider._format_code_hack_info(game, entity_info)

        # For other entities, format normally
        # Name goes in title to save space (like exploits)
        lines = []

        # Add description (word wrapped)
        desc_lines = InfoProvider._wrap_text(entity_info["description"], 22)
        for line in desc_lines:
            lines.append({"text": line, "color": Colors.LIGHT_GRAY})

        # Add blank line if there are details
        if entity_info["details"]:
            lines.append({"text": "", "color": Colors.WHITE})

            # Add details (word wrapped)
            detail_lines = entity_info["details"].split("\n")
            for detail_line in detail_lines:
                wrapped_details = InfoProvider._wrap_text(detail_line, 22)
                for line in wrapped_details:
                    lines.append({"text": line, "color": Colors.WHITE})

        return {"title": entity_info["name"], "lines": lines, "color": entity_info["color"]}

    @staticmethod
    def _format_code_hack_info(game, entity_info: dict[str, Any]) -> dict[str, Any]:
        """
        Format code hack info with discovery state handling.

        Shows "???" for effect if code hack has not been discovered yet.
        This preserves the mystery mechanic where players don't know
        what a code hack does until they use it once.

        Args:
            game: GameEngine instance
            entity_info: Entity info from EntityInspector

        Returns:
            Formatted info dict
        """
        lines = []

        # Add name with color
        lines.append({"text": entity_info["name"], "color": entity_info["color"]})

        # Add blank line
        lines.append({"text": "", "color": Colors.WHITE})

        # Check if effect is discovered
        if entity_info["description"] == "Unknown effect until used":
            # Not discovered - show mystery
            lines.append({"text": "Type: Code Fragment", "color": Colors.YELLOW})
            lines.append({"text": "", "color": Colors.WHITE})
            lines.append({"text": "Effect: ???", "color": Colors.DARK_GRAY})
            lines.append({"text": "", "color": Colors.WHITE})
            lines.append({"text": "(Use to discover)", "color": Colors.DARK_GRAY})
        else:
            # Discovered - show effect
            lines.append({"text": "Type: Code Fragment", "color": Colors.YELLOW})
            lines.append({"text": "", "color": Colors.WHITE})

            # Word wrap the effect description
            desc_lines = InfoProvider._wrap_text(entity_info["description"], 22)
            for line in desc_lines:
                lines.append({"text": line, "color": Colors.LIGHT_GRAY})

        # Add color detail
        if entity_info["details"]:
            lines.append({"text": "", "color": Colors.WHITE})
            lines.append({"text": entity_info["details"], "color": Colors.WHITE})

        return {"title": "INFO PANEL", "lines": lines, "color": Colors.GREEN}

    @staticmethod
    def _wrap_text(text: str, max_width: int) -> list:
        """
        Wrap text to fit within max_width using word boundaries.

        Args:
            text: Text to wrap
            max_width: Maximum characters per line

        Returns:
            List of wrapped text lines
        """
        if len(text) <= max_width:
            return [text]

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                # Handle very long words
                if len(word) > max_width:
                    current_line = word[:max_width]
                else:
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    @staticmethod
    def get_default_info(game) -> dict[str, Any]:
        """
        Get default info to display when nothing is hovered.

        Shows:
        - Network level with name
        - Turn counter
        - Trace level
        - Enemies remaining
        - Current streak (if any)

        Args:
            game: GameEngine instance

        Returns:
            Formatted info dict for default display
        """
        lines = []

        # Network level with name (if available) - use separate lines for better readability
        if hasattr(game, "game_state") and hasattr(game.game_state, "level"):
            level = game.game_state.level
            try:
                network_configs = GameConfig.get_network_configs()
                network_name = network_configs.get(level, {}).get("name", f"Level {level}")
                lines.append({"text": f"Level {level}", "color": Colors.CYAN})
                lines.append({"text": network_name, "color": Colors.CYAN})
            except Exception as e:
                GameErrorHandler.handle_error(
                    e,
                    "info_panel_network_name",
                    f"Failed to get network name for level {level}",
                    fatal=False,
                )
                lines.append({"text": f"Level {level}", "color": Colors.CYAN})
        elif hasattr(game, "level"):
            # Fallback to old attribute name
            lines.append({"text": f"Level {game.level}", "color": Colors.CYAN})

        # Turn counter (if available)
        if hasattr(game, "turn"):
            lines.append({"text": f"Turns Elapsed: {game.turn}", "color": Colors.WHITE})
        elif hasattr(game, "turn_count"):
            lines.append({"text": f"Turns Elapsed: {game.turn_count}", "color": Colors.WHITE})

        # Enemies remaining
        if hasattr(game, "enemy_manager") and hasattr(game.enemy_manager, "enemies"):
            enemy_count = len(game.enemy_manager.enemies)
            lines.append({"text": f"Hostiles: {enemy_count}", "color": Colors.ORANGE})

        # Add blank line before streaks
        if lines:
            lines.append({"text": "", "color": Colors.WHITE})

        # Current streak (if any)
        try:
            from game_metrics import get_current_session

            session = get_current_session()
            if session:
                if session.metrics.stealth_kills_current_streak > 0:
                    lines.append(
                        {
                            "text": f"Stealth Streak: {session.metrics.stealth_kills_current_streak}",
                            "color": Colors.GREEN,
                        }
                    )

                if session.metrics.combat_kills_current_streak > 0:
                    lines.append(
                        {
                            "text": f"Combat Streak: {session.metrics.combat_kills_current_streak}",
                            "color": Colors.YELLOW,
                        }
                    )
        except (ImportError, AttributeError) as e:
            # Metrics system not available or session not started - this is non-critical
            logging.debug(f"Info panel: Metrics not available: {e}")

        # If no info available, show a simple message
        if not lines:
            lines.append({"text": "Hover to inspect", "color": Colors.DARK_GRAY})

        # Add "Press ? for help" near the bottom (2nd from bottom row)
        # Panel height is 11 rows total, with ~8 content lines available
        # Add blank lines to push help text to 2nd from bottom
        while len(lines) < 7:
            lines.append({"text": "", "color": Colors.WHITE})

        lines.append({"text": "Press ? for help", "color": Colors.DARK_GRAY})

        return {"title": "INFO PANEL", "lines": lines, "color": Colors.GREEN}


class InfoPanelRenderer:
    """
    Renders the info panel in the top-right corner.

    Displays a bordered panel showing context-aware information based on
    what the player is hovering over. Handles text wrapping and proper
    color coding for different entity types.
    """

    @staticmethod
    def render(console: tcod.console.Console, game, ui_color=None):
        """
        Render the info panel with current context information.

        Panel location: x=55-79, y=0-10 (11 lines total, 25 chars wide)

        Shows information about hovered entity or default mission info.

        Args:
            console: TCOD console to render to
            game: GameEngine instance
            ui_color: Optional RGB tuple for border color (defaults to CYAN)
        """
        if ui_color is None:
            ui_color = Colors.CYAN

        panel_x = GameConfig.GAME_AREA_WIDTH()  # Start at 55 (same as system log border)
        panel_width = GameConfig.LOG_WIDTH - 1  # 24 chars (25 - 1 for border)
        panel_height = GameConfig.INFO_PANEL_HEIGHT

        # Get info to display
        info = InfoProvider.get_info_for_hover(game, game.last_mouse_tile_x, game.last_mouse_tile_y)
        if info is None:
            info = InfoProvider.get_default_info(game)

        # Clear panel area
        for y in range(panel_height):
            for x in range(panel_x, GameConfig.SCREEN_WIDTH):
                render_char_safe(console, x, y, " ", fg=Colors.UI_TEXT, bg=Colors.LOG_BG)

        # Render border with UI color
        InfoPanelRenderer._render_border(
            console, panel_x, 0, panel_width, panel_height, info["title"], ui_color
        )

        # Render content
        content_y = 2  # Start after header
        max_y = panel_height - 1  # Leave room for bottom border

        for line_data in info["lines"]:
            if content_y >= max_y:
                break

            text = line_data["text"]
            color = line_data["color"]

            # Truncate if too long (safety check)
            if len(text) > panel_width - 2:
                text = text[: panel_width - 4] + "..."

            # Pad text to full panel width to ensure complete overwrite of previous content
            padded_text = text.ljust(panel_width - 2)

            render_char_safe(
                console, panel_x + 1, content_y, padded_text, fg=color, bg=Colors.LOG_BG
            )
            content_y += 1

        # Fill any remaining lines with blank padded lines to clear previous content
        while content_y < max_y:
            blank_line = " " * (panel_width - 2)
            render_char_safe(
                console, panel_x + 1, content_y, blank_line, fg=Colors.WHITE, bg=Colors.LOG_BG
            )
            content_y += 1

    @staticmethod
    def _render_border(
        console: tcod.console.Console,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        ui_color=None,
    ):
        """
        Render bordered box with title for info panel.

        Args:
            console: TCOD console to render to
            x: Left edge of border
            y: Top edge of border
            width: Width of border (inside width, not including border chars)
            height: Height of border
            title: Title text to display in header
            ui_color: Optional RGB tuple for border color (defaults to CYAN)
        """
        if ui_color is None:
            ui_color = Colors.CYAN
        border_color = ui_color

        # Top border with title
        render_char_safe(console, x, y, "╔", fg=border_color, bg=Colors.LOG_BG)

        # Title centered in top border
        title_text = f" {title} "
        title_start = x + (width - len(title_text)) // 2 + 1
        for i, char in enumerate(title_text):
            render_char_safe(console, title_start + i, y, char, fg=border_color, bg=Colors.LOG_BG)

        # Fill rest of top border with ═
        for i in range(1, width + 1):
            if i < title_start - x or i >= title_start - x + len(title_text):
                render_char_safe(console, x + i, y, "═", fg=border_color, bg=Colors.LOG_BG)

        render_char_safe(console, x + width + 1, y, "╗", fg=border_color, bg=Colors.LOG_BG)

        # Side borders (no bottom border - SYSTEM LOG line serves as separator)
        for row_y in range(1, height):
            # Left side: check for T-intersection with status bar at row 1
            if y + row_y == 1:
                # T-piece where status bar horizontal meets info panel left border (╣ points left)
                # Lines from: LEFT (status bar), UP (border), DOWN (border)
                render_char_safe(
                    console, x, y + row_y, GameGlyphs.WALL_T_LEFT, fg=border_color, bg=Colors.LOG_BG
                )
            else:
                render_char_safe(console, x, y + row_y, "║", fg=border_color, bg=Colors.LOG_BG)
            # Right side: always vertical
            render_char_safe(
                console, x + width + 1, y + row_y, "║", fg=border_color, bg=Colors.LOG_BG
            )
