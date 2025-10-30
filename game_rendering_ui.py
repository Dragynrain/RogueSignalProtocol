#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Rendering UI

Consolidated UI rendering module combining all UI rendering responsibilities:
- Status bars (top bar with CPU/heat/trace/RAM, bottom panel with exploits/conditions)
- Message log (scrolling system log in right panel)
- Inspection panel (look mode entity details)
- Full-screen overlays (help, inventory, story fragments, lore viewer)

Previously split across 4 separate files, now unified for easier navigation.
"""

import tcod
import logging
from typing import List, Tuple, Optional

from game_config import GameConfig, GameBalance
from game_entities import Colors
from game_data import GameData
from game_ui import render_char_safe
from game_menu_help_lore import create_help_menu
from data_loading import get_story_fragments
from game_screen_utilities import ScreenRenderingUtils, ScrollableListManager


class UIRenderer:
    """
    Unified UI renderer combining all UI rendering responsibilities.

    Handles all UI elements:
    - Status bars: Top resource bar (CPU/heat/trace/RAM) and bottom panel (exploits/conditions)
    - Message log: System message log in right panel with scrolling
    - Inspection panel: Look mode overlay showing entity details
    - Full-screen overlays: Help screen, inventory, story fragments, lore viewer

    Methods are organized by responsibility for easy navigation:
    - Status rendering: render_top_status_bar, render_bottom_panel
    - Message log: render_system_log
    - Inspection: render_inspection_panel
    - Full screens: render_help_screen, render_inventory_screen, etc.
    """

    def __init__(self, settings=None, context=None, tile_manager=None):
        """
        Initialize UI renderer.

        Args:
            settings: GameSettings instance (optional, for graphical help)
            context: TCOD context (optional, for graphical help)
            tile_manager: TileManager instance (optional, for graphical help)
        """
        self.settings = settings
        self.context = context
        self.tile_manager = tile_manager
        self._help_menu = None  # Cached help menu instance

    # ========================================================================
    # STATUS BAR RENDERING
    # ========================================================================

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """
        Render the top status bar with player resources.

        Displays CPU, heat, trace, and RAM with color-coded values.
        Stays within game area width (help text is in log panel).

        Args:
            console: TCOD console to render to
            game: GameEngine with player stats
        """
        # Clear the entire top line (full screen width)
        for x in range(GameConfig.SCREEN_WIDTH):
            render_char_safe(console, x, 0, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)

        # Color coding for status values
        cpu_color = self._get_cpu_color(game.player.cpu)
        heat_color = self._get_heat_color(game.player.heat)
        trace_color = self._get_trace_color(game.player.trace_level)
        ram_color = Colors.RED if game.player.ram_used > game.player.ram_total else Colors.GREEN

        # Build status line (only left side stats - help text goes in log panel)
        status_parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            f"Heat:{game.player.heat:3d}°C/{game.player.max_heat}°C" if game.player.max_heat > 100 else f"Heat:{game.player.heat:3d}°C",
            f"Trace:{int(game.player.trace_level):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB"
        ]

        colors = [cpu_color, heat_color, trace_color, ram_color]

        x_pos = 1
        for part, color in zip(status_parts, colors):
            # Keep status bar in game area only
            if x_pos + len(part) < GameConfig.GAME_AREA_WIDTH() - 1:
                render_char_safe(console, x_pos, 0, part, fg=color, bg=Colors.UI_BG)
                x_pos += len(part) + 2

    def _get_cpu_color(self, cpu: int) -> Tuple[int, int, int]:
        """Get threshold-based color for CPU display (red <30, yellow <60, green ≥60)."""
        if cpu < 30:
            return Colors.RED
        elif cpu < 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def _get_heat_color(self, heat: int) -> Tuple[int, int, int]:
        """Get threshold-based color for heat display (red >80, yellow >60, green ≤60)."""
        if heat > 80:
            return Colors.RED
        elif heat > 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def _get_trace_color(self, trace_level: float) -> Tuple[int, int, int]:
        """Get threshold-based color for trace display (red >75, yellow >50, green ≤50)."""
        if trace_level > 75:
            return Colors.RED
        elif trace_level > 50:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def render_bottom_panel(self, console: tcod.console.Console, game):
        """
        Render the bottom panel with exploits and conditions.

        Displays:
        - Equipped exploits (up to 5, with heat feasibility colors)
        - Active temporary conditions with turn counts

        Args:
            console: TCOD console to render to
            game: GameEngine with player inventory and effects
        """
        # Clear panel area (full screen width to accommodate all exploits)
        for x in range(GameConfig.SCREEN_WIDTH):
            for y in range(GameConfig.PANEL_Y(), GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)

        # Panel border (full screen width)
        border = "╔" + "═" * (GameConfig.SCREEN_WIDTH - 2) + "╗"
        render_char_safe(console, 0, GameConfig.PANEL_Y(), border, fg=Colors.LOG_BORDER, bg=Colors.UI_BG)

        # Equipped exploits (2 lines)
        self._render_equipped_exploits_panel(console, game)

        # Temporary conditions/effects (1 line)
        self._render_temporary_conditions(console, game)

    def _render_equipped_exploits_panel(self, console: tcod.console.Console, game):
        """
        Render equipped exploits across two lines.

        Shows exploits 1-3 on first line, 4-5 on second line.
        Colors exploits green if usable (heat cost fits), red if too hot.
        Accounts for exploit efficiency temporary effect reducing heat cost.
        Stores positions for mouse click detection.

        Args:
            console: TCOD console to render to
            game: GameEngine with player inventory and heat
        """
        y1 = GameConfig.PANEL_Y() + 1
        y2 = GameConfig.PANEL_Y() + 2

        render_char_safe(console, 1, y1, "Exploits:", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)

        equipped_exploits = game.player.inventory_manager.equipped_exploits[:5]

        # Clear stored positions for this render
        UIRenderer.last_exploit_positions = []

        # Check if mouse is hovering over exploit bar area
        mouse_tile_x = game.last_mouse_tile_x
        mouse_tile_y = game.last_mouse_tile_y
        hovered_slot = None

        # Fixed layout: exploits 1,2,3 on first line, 4,5 on second line
        line1_exploits = []
        line2_exploits = []

        for i, exploit_key in enumerate(equipped_exploits):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                heat_cost = exploit.heat
                if game.player.temporary_effects['exploit_efficiency_turns'] > 0:
                    heat_cost = int(heat_cost * 0.6)

                heat_ok = game.player.heat + heat_cost <= game.player.max_heat
                color = Colors.GREEN if heat_ok else Colors.RED
                exploit_text = f"{i+1}.{exploit.name}"

                # First 3 exploits go on first line, remaining on second line
                if i < 3:
                    line1_exploits.append((exploit_key, exploit_text, color, i))
                else:
                    line2_exploits.append((exploit_key, exploit_text, color, i))

        # Render first line exploits
        x_pos = 11
        for exploit_key, exploit_text, color, slot in line1_exploits:
            # Check if mouse is hovering over this exploit
            text_width = len(exploit_text)
            is_hovered = (mouse_tile_x is not None and mouse_tile_y is not None and
                         mouse_tile_y == y1 and
                         x_pos <= mouse_tile_x < x_pos + text_width)

            # Store position for click detection
            UIRenderer.last_exploit_positions.append({
                'slot': slot,
                'x': x_pos,
                'y': y1,
                'width': text_width,
                'exploit_key': exploit_key
            })

            # Use highlight background if hovered
            bg = Colors.UI_HIGHLIGHT if is_hovered else Colors.UI_BG
            if is_hovered:
                hovered_slot = slot

            render_char_safe(console, x_pos, y1, exploit_text, fg=color, bg=bg)
            x_pos += text_width + 2

        # Render second line exploits
        if line2_exploits:
            render_char_safe(console, 1, y2, "        ", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)  # Indent to align
            x_pos = 11
            for exploit_key, exploit_text, color, slot in line2_exploits:
                # Check if mouse is hovering over this exploit
                text_width = len(exploit_text)
                is_hovered = (mouse_tile_x is not None and mouse_tile_y is not None and
                             mouse_tile_y == y2 and
                             x_pos <= mouse_tile_x < x_pos + text_width)

                # Store position for click detection
                UIRenderer.last_exploit_positions.append({
                    'slot': slot,
                    'x': x_pos,
                    'y': y2,
                    'width': text_width,
                    'exploit_key': exploit_key
                })

                # Use highlight background if hovered
                bg = Colors.UI_HIGHLIGHT if is_hovered else Colors.UI_BG
                if is_hovered:
                    hovered_slot = slot

                render_char_safe(console, x_pos, y2, exploit_text, fg=color, bg=bg)
                x_pos += text_width + 2

    def _render_temporary_conditions(self, console: tcod.console.Console, game):
        """
        Render all active temporary conditions with turn counts.

        Displays player effects (speed boost, data mimic, etc.), threat scan,
        and speed moves remaining. Uses color-coded display matching the
        effect type (e.g., data code colors for code effects).

        Args:
            console: TCOD console to render to
            game: GameEngine with player temporary_effects and game_state
        """
        y = GameConfig.PANEL_Y() + 3

        conditions = []

        # Player temporary effects (from codes and other sources)
        for effect_name, turns in game.player.temporary_effects.items():
            if turns > 0:
                display_name = effect_name.replace('_turns', '').replace('_', ' ').title()
                condition_text = f"{display_name}({turns})"

                # Color conditions based on their type
                if effect_name == 'data_mimic_turns':
                    color = Colors.BLUE  # Invisible effect
                elif effect_name == 'speed_boost_turns':
                    color = self._get_data_code_color_for_effect(game, 'speed_boost', Colors.YELLOW)
                elif effect_name == 'movement_slowed_turns':
                    color = Colors.ORANGE  # Movement slowed effect
                elif effect_name == 'enhanced_vision_turns':
                    color = self._get_data_code_color_for_effect(game, 'enhanced_vision', Colors.ELECTRIC_BLUE)
                elif effect_name == 'exploit_efficiency_turns':
                    color = self._get_data_code_color_for_effect(game, 'exploit_efficiency', Colors.ELECTRIC_PURPLE)
                elif effect_name == 'virus_turns':
                    color = Colors.DARK_GREEN  # Virus effect
                else:
                    color = Colors.WHITE  # Default color for other effects

                conditions.append((condition_text, color))

        # Threat scan effect
        if game.game_state.threat_scan_turns > 0:
            conditions.append((f"Threat Scan({game.game_state.threat_scan_turns})", Colors.ELECTRIC_PURPLE))

        # Speed moves remaining (from speed boost)
        if game.player.speed_moves_remaining > 0:
            conditions.append((f"Speed Moves({game.player.speed_moves_remaining})", Colors.YELLOW))

        if conditions:
            # Print the "Conditions:" label
            x = 1
            render_char_safe(console, x, y, "Conditions: ", fg=Colors.CYAN, bg=Colors.UI_BG)
            x += len("Conditions: ")

            # Print each condition with its appropriate color
            for i, (condition_text, color) in enumerate(conditions):
                if i > 0:
                    render_char_safe(console, x, y, " ", fg=Colors.CYAN, bg=Colors.UI_BG)
                    x += 1
                render_char_safe(console, x, y, condition_text, fg=color, bg=Colors.UI_BG)
                x += len(condition_text)
        else:
            render_char_safe(console, 1, y, "Conditions: None", fg=Colors.UI_TEXT, bg=Colors.UI_BG)

    def _get_data_code_color_for_effect(self, game, effect_key: str, fallback_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Get the data code color for a specific effect from current game.

        Looks up which color code provides the given effect in this game
        instance (since code effects are randomized per game). Returns
        the matching color or fallback if not found.

        Args:
            game: GameEngine with code_hack_effects mapping
            effect_key: Effect name (e.g., 'speed_boost', 'enhanced_vision')
            fallback_color: Color to use if effect not found in mapping

        Returns:
            RGB color tuple matching the code that provides this effect
        """
        color_map = {
            'crimson': Colors.CRIMSON,
            'azure': Colors.AZURE,
            'emerald': Colors.EMERALD,
            'golden': Colors.GOLDEN,
            'violet': Colors.VIOLET,
            'silver': Colors.SILVER
        }

        # Find which color has this effect in the current game
        for color_name, (effect, _) in game.code_hack_effects.items():
            if effect == effect_key:
                return color_map.get(color_name, fallback_color)

        return fallback_color

    # ========================================================================
    # INFO PANEL RENDERING
    # ========================================================================

    def render_info_panel(self, console: tcod.console.Console, game):
        """
        Render the info panel in the top-right corner.

        Shows context-aware information based on mouse hover:
        - Enemies: name, stats, state, movement queue
        - Items: name, effects, costs
        - Nodes: type, effect, activation
        - Default: turn counter, level, streaks

        Location: x=55-79, y=0-10 (11 lines, 25 chars wide)

        Args:
            console: TCOD console to render to
            game: GameEngine with current game state
        """
        from game_info_panel import InfoPanelRenderer
        InfoPanelRenderer.render(console, game)

    # ========================================================================
    # MESSAGE LOG RENDERING
    # ========================================================================

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
        log_start_y = GameConfig.LOG_START_Y()

        # Draw log border (from LOG_START_Y to panel start)
        for y in range(log_start_y, GameConfig.PANEL_Y()):
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), y, '║', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Log header
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, log_start_y, "SYSTEM LOG", fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, log_start_y + 1, "═" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Clear log area - start from log_start_y + 2 to account for header, stop at panel start
        for x in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            for y in range(log_start_y + 2, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)

        # Process and display messages (skip if in look mode - inspection panel will use this area)
        if not game.look_mode:
            self._render_log_messages(console, game)

    def _render_log_messages(self, console: tcod.console.Console, game):
        """
        Render scrolling log messages with automatic wrapping.

        Shows the most recent messages that fit in the available vertical space.
        Now starts at LOG_START_Y + 2 (after info panel and log header).
        Delegates text wrapping to _wrap_messages().

        Args:
            console: TCOD console to render to
            game: GameEngine with message_log
        """
        log_start_y = GameConfig.LOG_START_Y()
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.PANEL_Y() - (log_start_y + 2)  # Available space for messages
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines

        for i, (line, color) in enumerate(visible_lines):
            y_pos = log_start_y + 2 + i  # Start from LOG_START_Y + 2 to avoid header
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

    # ========================================================================
    # INSPECTION PANEL RENDERING
    # ========================================================================

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
        render_char_safe(console, panel_x, panel_y, "═" * (GameConfig.LOG_WIDTH - 1), fg=Colors.YELLOW, bg=Colors.LOG_BG)
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
            if panel_y < GameConfig.PANEL_Y() - 1:
                render_char_safe(console, panel_x, panel_y, line, fg=Colors.LIGHT_GRAY, bg=Colors.LOG_BG)
                panel_y += 1

        # Blank line
        if panel_y < GameConfig.PANEL_Y() - 1:
            panel_y += 1

        # Render details if available
        if entity_info['details']:
            detail_lines = entity_info['details'].split('\n')
            for detail_line in detail_lines:
                wrapped_details = self._wrap_text(detail_line, GameConfig.LOG_WIDTH - 2)
                for line in wrapped_details:
                    if panel_y < GameConfig.PANEL_Y() - 1:
                        render_char_safe(console, panel_x, panel_y, line, fg=Colors.WHITE, bg=Colors.LOG_BG)
                        panel_y += 1

        # Draw bottom separator
        if panel_y < GameConfig.PANEL_Y() - 1:
            panel_y += 1
            render_char_safe(console, panel_x, panel_y, "═" * (GameConfig.LOG_WIDTH - 1), fg=Colors.YELLOW, bg=Colors.LOG_BG)

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

    # ========================================================================
    # FULL-SCREEN OVERLAY RENDERING
    # ========================================================================

    def _clear_game_area(self, console: tcod.console.Console) -> None:
        """
        Clear only the main game area, preserving UI panels.

        Clears the viewport but leaves status bar, message log, and bottom panel intact.
        Used by inventory screen to maintain UI consistency.

        Args:
            console: TCOD console to clear
        """
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(1, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)

    def _render_overlay_menu(self, console: tcod.console.Console, title: str, options: list, menu_width: int = 30) -> tuple:
        """
        Render a centered overlay menu with title and options.

        Draws a bordered, centered menu box with title and option list.
        Used by story fragment and other overlay screens.

        Args:
            console: TCOD console to render to
            title: Menu title text
            options: List of option strings
            menu_width: Width of menu box in characters (default 30)

        Returns:
            Tuple of (menu_x, menu_y, menu_height) for additional rendering
        """
        menu_height = 6 + len(options)  # Header + options + padding
        menu_x = (GameConfig.SCREEN_WIDTH - menu_width) // 2
        menu_y = (GameConfig.SCREEN_HEIGHT - menu_height) // 2

        # Menu background
        for y in range(menu_y, menu_y + menu_height):
            for x in range(menu_x, menu_x + menu_width):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.UI_BG)

        # Menu borders (top and bottom)
        for x in range(menu_x, menu_x + menu_width):
            render_char_safe(console, x, menu_y, '═', fg=Colors.CYAN, bg=Colors.UI_BG)
            render_char_safe(console, x, menu_y + menu_height - 1, '═', fg=Colors.CYAN, bg=Colors.UI_BG)

        # Title (centered)
        title_x = menu_x + (menu_width - len(title)) // 2
        render_char_safe(console, title_x, menu_y + 2, title, fg=Colors.YELLOW, bg=Colors.UI_BG)

        # Options
        for i, option in enumerate(options):
            render_char_safe(console, menu_x + 3, menu_y + 4 + i, option, fg=Colors.WHITE, bg=Colors.UI_BG)

        return menu_x, menu_y, menu_height

    # === Help Screen ===

    def render_help_screen(self, console: tcod.console.Console):
        """
        Render the help screen using appropriate help menu.

        Uses GraphicalHelpMenu in graphics mode, HelpMenu in glyph mode.
        """
        # Create help menu if not already created
        if self._help_menu is None:
            if self.settings is not None:
                self._help_menu = create_help_menu(self.settings, self.context, self.tile_manager)
                logging.info(f"Created in-game help menu: {type(self._help_menu).__name__}")
            else:
                # Fallback to standard help menu if settings not provided
                from game_menu_help_lore import HelpMenu
                self._help_menu = HelpMenu()
                logging.warning("Settings not provided to FullScreenRenderer, using standard HelpMenu")

        # Render help menu
        self._help_menu.render(console)

    def render_help_sprites(self):
        """
        Render help screen sprites (for GraphicalHelpMenu only).

        This should be called BEFORE render_help_screen when in graphics mode.
        Only GraphicalHelpMenu has this method.
        """
        if self._help_menu and hasattr(self._help_menu, 'render_sprites'):
            self._help_menu.render_sprites()

    def handle_help_input(self, event) -> str:
        """
        Handle input for help screen.

        Args:
            event: TCOD event

        Returns:
            Result from help menu input handler ('back' to exit, '' to continue)
        """
        if self._help_menu:
            return self._help_menu.handle_input(event)
        return ""

    # === Exploit Bar Click Detection ===

    # Stored coordinates for exploit bar click detection (single source of truth)
    # Each entry: {'slot': int, 'x': int, 'y': int, 'width': int, 'exploit_key': str}
    last_exploit_positions = []

    # === Inventory Screen ===

    # Stored coordinates for inventory click detection (single source of truth)
    last_inventory_lines = None  # List of line data with selectability
    last_inventory_content_start_y = None
    last_inventory_scroll_offset = None
    last_inventory_equipped_count = None

    def render_inventory_screen(self, console: tcod.console.Console, game):
        """
        Render the inventory screen with scrolling support.

        Displays all items grouped by category (exploits, codes, upgrades, fragments).
        Uses ScrollableListManager for automatic scroll handling with selection tracking.
        Preserves status bar and message log for UI consistency.

        Args:
            console: TCOD console to render to
            game: GameEngine with player inventory and scroll state
        """
        # Clear only the main game area, preserve UI elements
        self._clear_game_area(console)

        # Title (centered in game area only)
        ScreenRenderingUtils.render_centered_title_in_area(
            console, "INVENTORY SYSTEM", 2, GameConfig.GAME_AREA_WIDTH()
        )

        # Render preserved UI elements (skip bottom panel to make room for inventory controls)
        self.render_top_status_bar(console, game)
        self.render_system_log(console, game)

        # Calculate available space for content
        content_start_y = 5
        controls_y = GameConfig.SCREEN_HEIGHT - 6
        max_content_height = controls_y - content_start_y - 1  # -1 for spacing

        # Build all inventory lines first
        inventory_lines = self._build_inventory_lines(game)
        total_lines = len(inventory_lines)

        # Use ScrollableListManager for scroll logic
        scroll_manager = ScrollableListManager(total_lines, max_content_height)
        scroll_manager.set_scroll_offset(game.inventory_scroll_offset)

        # Find selection line and adjust scroll
        selection_line = self._find_selection_line(game)
        scroll_manager.adjust_for_selection(selection_line)

        # Update game state with new scroll offset
        game.inventory_scroll_offset = scroll_manager.get_scroll_offset()

        # Render visible portion
        y = content_start_y
        start, end = scroll_manager.get_visible_range()

        for i in range(start, end):
            line_data = inventory_lines[i]
            render_char_safe(console, line_data['x'], y, line_data['text'], fg=line_data['color'])
            y += 1

        # Show scroll indicators using utility
        ScreenRenderingUtils.render_scroll_indicators(
            console,
            x=GameConfig.GAME_AREA_WIDTH() - 8,
            top_y=content_start_y,
            bottom_y=controls_y - 2,
            show_up=scroll_manager.should_show_scroll_up(),
            show_down=scroll_manager.should_show_scroll_down()
        )

        # Controls
        self._render_inventory_controls(console)

        # Store data for mouse click detection (single source of truth)
        UIRenderer.last_inventory_lines = inventory_lines
        UIRenderer.last_inventory_content_start_y = content_start_y
        UIRenderer.last_inventory_scroll_offset = scroll_manager.get_scroll_offset()
        UIRenderer.last_inventory_equipped_count = len(game.player.inventory_manager.equipped_exploits)

        # Note: Exploit details are now shown in the info panel instead of a tooltip
        # The InfoProvider handles hover detection and formatting

    def _build_inventory_lines(self, game):
        """
        Build all inventory lines for rendering with proper formatting.

        Creates a flat list of all inventory items grouped by category:
        - Exploits (with equipped indicators and stats)
        - Code Hacks (with equipped indicators and effects)
        - Upgrades (installed status and descriptions)
        - Story Fragments (discovered count)

        Returns:
            List of dicts with 'x', 'text', 'color' keys for each line
        """
        lines = []

        # Equipped exploits section
        lines.append({'x': 2, 'text': "EQUIPPED EXPLOITS:", 'color': Colors.CYAN, 'selectable': False})

        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            if i == game.inventory_selection:
                color = Colors.YELLOW
                prefix = ">"
            elif exploit_key in GameData.EXPLOITS:
                color = Colors.GREEN
                prefix = " "
            else:
                color = Colors.RED
                prefix = " "

            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                text = f"{prefix} {i+1}. {exploit.name}"
            else:
                text = f"{prefix} {i+1}. INVALID: {exploit_key}"

            lines.append({'x': 4, 'text': text, 'color': color, 'selectable': True})

        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            lines.append({'x': 4, 'text': f"[{equipped_count}/{max_exploits} slots used]", 'color': Colors.YELLOW, 'selectable': False})

        lines.append({'x': 2, 'text': "", 'color': Colors.WHITE, 'selectable': False})  # Spacer

        # Code hacks section
        code_hacks = game.player.inventory_manager.get_items_by_type("code_hack")
        lines.append({'x': 2, 'text': f"CODES ({len(code_hacks)}):", 'color': Colors.CYAN, 'selectable': False})

        if not code_hacks:
            lines.append({'x': 4, 'text': "No codes collected", 'color': Colors.WHITE, 'selectable': False})
        else:
            display_items = game.player.inventory_manager.get_display_items()

            for i, patch in enumerate(code_hacks):
                display_index = display_items.index(patch)
                adjusted_selection_index = display_index + equipped_count

                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "

                description = patch.description if patch.discovered else "Unknown effect"
                quantity_text = f" ({patch.quantity})" if patch.quantity > 1 else ""
                patch_text = f"{prefix} {patch.name}{quantity_text} - {description}"

                max_width = GameConfig.GAME_AREA_WIDTH() - 6
                if len(patch_text) > max_width:
                    patch_text = patch_text[:max_width-3] + "..."

                lines.append({'x': 4, 'text': patch_text, 'color': color, 'selectable': True})

        lines.append({'x': 2, 'text': "", 'color': Colors.WHITE, 'selectable': False})  # Spacer

        # Unequipped exploits section
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        lines.append({'x': 2, 'text': f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):", 'color': Colors.CYAN, 'selectable': False})

        if not exploit_items:
            lines.append({'x': 4, 'text': "No unequipped exploits", 'color': Colors.WHITE, 'selectable': False})
        else:
            display_items = game.player.inventory_manager.get_display_items()

            for i, exploit_item in enumerate(exploit_items):
                try:
                    display_index = display_items.index(exploit_item)
                    adjusted_selection_index = display_index + equipped_count
                except ValueError:
                    adjusted_selection_index = -1

                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "

                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    name_text = f"{prefix} {exploit_item.name}"
                    lines.append({'x': 4, 'text': name_text, 'color': color, 'selectable': True})

                    stats_text = f"    RAM:{exploit_def.ram} Heat:{exploit_def.heat}"
                    if exploit_def.damage > 0:
                        stats_text += f" Damage:{exploit_def.damage}"
                    if exploit_def.range > 0:
                        stats_text += f" Range:{exploit_def.range}"
                    lines.append({'x': 4, 'text': stats_text, 'color': Colors.LIGHT_GRAY, 'selectable': False})
                else:
                    text = f"{prefix} {exploit_item.name} [Unknown]"
                    lines.append({'x': 4, 'text': text, 'color': color, 'selectable': True})

        return lines

    def _find_selection_line(self, game) -> int:
        """
        Find which line contains the currently selected inventory item.

        Scans built inventory lines to locate the selected item's display line.
        Used by scroll manager to ensure selected item is visible.

        Args:
            game: GameEngine with inventory_selector state

        Returns:
            Line index of selected item, or 0 if not found
        """
        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        display_items = game.player.inventory_manager.get_display_items()

        # Count lines before selection
        line_count = 1  # "EQUIPPED EXPLOITS:" header

        if game.inventory_selection < equipped_count:
            # Selection is in equipped exploits
            return line_count + game.inventory_selection

        line_count += equipped_count
        if equipped_count < game.player.inventory_manager.max_equipped_exploits:
            line_count += 1  # Slots used line
        line_count += 2  # Spacer + "CODES" header

        # Check if selection is in codes or unequipped exploits
        code_hacks = game.player.inventory_manager.get_items_by_type("code_hack")
        if game.inventory_selection < equipped_count + len(code_hacks):
            # Selection is in code hacks
            code_index = game.inventory_selection - equipped_count
            return line_count + code_index

        # Selection is in unequipped exploits
        line_count += max(1, len(code_hacks))  # Code hacks or "No codes" line
        line_count += 2  # Spacer + "UNEQUIPPED EXPLOITS" header

        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        exploit_index = game.inventory_selection - equipped_count - len(code_hacks)

        # Account for 2-line exploit display (name + stats)
        for i in range(min(exploit_index, len(exploit_items))):
            exploit_item = exploit_items[i]
            if exploit_item.exploit_key in GameData.EXPLOITS:
                line_count += 2  # Name + stats
            else:
                line_count += 1  # Just name

        return line_count

    def _render_inventory_controls(self, console: tcod.console.Console):
        """
        Render inventory screen controls at the bottom.

        Shows available actions: equip, unequip, install, use, drop, and close.

        Args:
            console: TCOD console to render to
        """
        y_start = GameConfig.SCREEN_HEIGHT - 6

        render_char_safe(console, 2, y_start, "CONTROLS:", fg=Colors.CYAN)
        render_char_safe(console, 4, y_start + 1, "W/S: Navigate  Enter: Use  X: Examine", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 2, "U: Unequip selected exploit", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 3, "ESC/I: Close inventory", fg=Colors.WHITE)

    @staticmethod
    def get_inventory_item_at_click(tile_y: int) -> Optional[int]:
        """
        Get the selection index of the inventory item clicked at the given tile Y coordinate.

        Uses stored rendering data (single source of truth) to map click coordinates
        to inventory selection indices. Only returns indices for selectable items.

        Args:
            tile_y: Y coordinate in tile space (0-49)

        Returns:
            Selection index if a selectable item was clicked, None otherwise
        """
        # Check if inventory data is available
        if UIRenderer.last_inventory_lines is None:
            return None
        if UIRenderer.last_inventory_content_start_y is None:
            return None
        if UIRenderer.last_inventory_scroll_offset is None:
            return None

        # Convert tile_y to line index
        line_index_in_visible = tile_y - UIRenderer.last_inventory_content_start_y
        if line_index_in_visible < 0:
            return None  # Clicked above content area

        # Account for scroll offset
        line_index = line_index_in_visible + UIRenderer.last_inventory_scroll_offset

        # Check if line index is valid
        if line_index < 0 or line_index >= len(UIRenderer.last_inventory_lines):
            return None

        # Get the line data
        line_data = UIRenderer.last_inventory_lines[line_index]

        # Check if this line is selectable
        if not line_data.get('selectable', False):
            return None

        # Count how many selectable lines came before this one to get selection index
        selection_index = 0
        for i in range(line_index):
            if UIRenderer.last_inventory_lines[i].get('selectable', False):
                selection_index += 1

        return selection_index

    @staticmethod
    def get_exploit_at_click(tile_x: int, tile_y: int) -> Optional[int]:
        """
        Get the slot number (0-4) of the exploit clicked at the given tile coordinates.

        Uses stored rendering data (single source of truth) to map click coordinates
        to exploit slot numbers. Returns the slot if clicked, None otherwise.

        Args:
            tile_x: X coordinate in tile space (0-79)
            tile_y: Y coordinate in tile space (0-49)

        Returns:
            Slot number (0-4) if an exploit was clicked, None otherwise
        """
        # Check if exploit position data is available
        if not UIRenderer.last_exploit_positions:
            return None

        # Check each stored exploit position
        for exploit_data in UIRenderer.last_exploit_positions:
            x = exploit_data['x']
            y = exploit_data['y']
            width = exploit_data['width']
            slot = exploit_data['slot']

            # Check if click is within this exploit's bounds
            if y == tile_y and x <= tile_x < x + width:
                return slot

        return None

    # === Story Fragment Screen ===

    def render_story_fragment_screen(self, console: tcod.console.Console, game, fragment_index: int):
        """
        Render a story fragment discovery screen when player picks up a fragment.

        Shows fragment title and content in centered overlay menu.
        Prompts player to press any key to continue.

        Args:
            console: TCOD console to render to
            game: GameEngine (for context)
            fragment_index: Index of fragment to display
        """
        console.clear()

        # Get the fragment text
        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return

        fragment_text = story_fragments[fragment_index]

        # Render using shared utilities
        content_start_y = ScreenRenderingUtils.render_screen_header(console, "DATA FRAGMENT RECOVERED")
        content_end_y = GameConfig.SCREEN_HEIGHT - 6  # Leave room for 2-line footer

        ScreenRenderingUtils.render_word_wrapped_text(
            console, fragment_text, 3, content_start_y,
            max_width=GameConfig.SCREEN_WIDTH - 6,
            max_height=content_end_y
        )

        ScreenRenderingUtils.render_screen_footer(
            console, "Press any key to continue...", "Press 'F' to view all fragments"
        )

    # === Lore Viewer Screen ===

    def render_lore_viewer_screen(self, console: tcod.console.Console, game):
        """
        Render the lore viewer with all discovered story fragments.

        Has two modes:
        - List mode: Shows all discovered fragments with selection
        - Reading mode: Shows selected fragment content

        Uses game.lore_viewer_selected to track selected fragment.

        Args:
            console: TCOD console to render to
            game: GameEngine with story_fragment_manager and lore viewer state
        """
        console.clear()

        discovered_fragments = game.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = game.story_fragment_manager.get_fragment_count()

        if game.lore_viewer_mode == "reading" and discovered_fragments:
            # Reading mode - show full fragment text
            self._render_lore_reading_mode(console, game, discovered_fragments)
        else:
            # List mode - show fragment list with navigation
            self._render_lore_list_mode(console, game, discovered_fragments, discovered_count, total_count)

    def _render_lore_list_mode(self, console: tcod.console.Console, game, discovered_fragments, discovered_count: int, total_count: int):
        """
        Render lore viewer list mode showing all discovered fragments.

        Displays scrollable list of discovered fragments with selection highlighting.
        Shows discovery count and navigation controls.

        Args:
            console: TCOD console to render to
            game: GameEngine with lore_viewer_selected
            discovered_fragments: List of discovered story fragments
            discovered_count: Number of fragments discovered
            total_count: Total number of fragments in game
        """
        title = f"RECOVERED DATA FRAGMENTS ({discovered_count}/{total_count})"
        content_start_y = ScreenRenderingUtils.render_screen_header(console, title)

        if not discovered_fragments:
            # No fragments discovered yet - center the message
            no_fragments_y = GameConfig.SCREEN_HEIGHT // 2
            ScreenRenderingUtils.render_centered_title(
                console, "No data fragments discovered yet.", no_fragments_y, Colors.YELLOW
            )
            ScreenRenderingUtils.render_centered_title(
                console, "Reach the Military Network (Level 3) to find them.", no_fragments_y + 2, Colors.WHITE
            )
            ScreenRenderingUtils.render_screen_footer(console, "Press ESC to close")
        else:
            # Show list of discovered fragments with brief previews
            y_offset = content_start_y
            max_display_height = GameConfig.SCREEN_HEIGHT - 6  # Leave room for footer

            for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
                if y_offset >= max_display_height:
                    render_char_safe(console, 3, y_offset, f"... and {len(discovered_fragments) - i} more fragments", fg=Colors.YELLOW)
                    break

                # Highlight selected entry
                is_selected = (i == game.lore_viewer_selection)
                title_color = Colors.YELLOW if is_selected else Colors.WHITE
                cursor = ">" if is_selected else " "

                # Fragment title (first line of the fragment)
                first_line = fragment_text.split('\n')[0]
                if len(first_line) > 58:  # Leave room for cursor and number
                    first_line = first_line[:55] + "..."

                render_char_safe(console, 2, y_offset, f"{cursor}{fragment_index + 1:2d}. {first_line}", fg=title_color)
                y_offset += 1

                # Brief preview (first few words of actual content)
                content_lines = [line.strip() for line in fragment_text.split('\n') if line.strip()]
                if len(content_lines) > 1:
                    preview = content_lines[1][:70] + "..." if len(content_lines[1]) > 70 else content_lines[1]
                    preview_color = (200, 200, 150) if is_selected else (128, 128, 128)
                    render_char_safe(console, 6, y_offset, preview, fg=preview_color)
                    y_offset += 1

                y_offset += 1  # Space between entries

            ScreenRenderingUtils.render_screen_footer(console, "Up/Down: Navigate, Enter: Read, ESC: Close")

    def _render_lore_reading_mode(self, console: tcod.console.Console, game, discovered_fragments):
        """
        Render lore viewer reading mode for selected fragment.

        Shows full content of selected fragment with text wrapping.
        Displays navigation controls for returning to list or switching fragments.

        Args:
            console: TCOD console to render to
            game: GameEngine with lore_viewer_selected
            discovered_fragments: List of discovered story fragments
        """
        if game.lore_viewer_selection >= len(discovered_fragments):
            game.lore_viewer_selection = 0

        fragment_index, fragment_text = discovered_fragments[game.lore_viewer_selection]

        title = f"DATA FRAGMENT #{fragment_index + 1}"
        content_start_y = ScreenRenderingUtils.render_screen_header(console, title)
        content_end_y = GameConfig.SCREEN_HEIGHT - 4  # Leave room for footer

        ScreenRenderingUtils.render_word_wrapped_text(
            console, fragment_text, 3, content_start_y,
            max_width=GameConfig.SCREEN_WIDTH - 6,
            max_height=content_end_y
        )

        ScreenRenderingUtils.render_screen_footer(console, "Any key: Back to list, ESC: Close")

    # === Achievements Screen ===

    def render_achievements_screen(self, console: tcod.console.Console, game):
        """
        Render the achievements screen.

        Delegates to AchievementsMenu for rendering and creates it if needed.

        Args:
            console: TCOD console to render to
            game: GameEngine (not actively used but kept for consistency)
        """
        # Create achievements menu if not already created
        if not hasattr(self, '_achievements_menu'):
            from game_menu_achievements import AchievementsMenu
            self._achievements_menu = AchievementsMenu()

        self._achievements_menu.render(console)
