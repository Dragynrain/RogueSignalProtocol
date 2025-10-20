#!/usr/bin/env python3
"""
Game Rendering UI - Full Screens
Renders full-screen UIs like help, inventory, and lore viewer.
"""

import tcod
import logging
from game_config import GameConfig
from game_entities import Colors
from game_data import GameData
from game_menu_help_lore import create_help_menu
from data_loading import get_story_fragments
from game_ui import render_char_safe
from game_screen_utilities import ScreenRenderingUtils, ScrollableListManager


class FullScreenRenderer:
    """Renders full-screen UI overlays."""

    def __init__(self, status_renderer, message_log_renderer, settings=None, context=None, tile_manager=None):
        """
        Initialize with references to other renderers for inventory screen.

        Args:
            status_renderer: StatusRenderer instance
            message_log_renderer: MessageLogRenderer instance
            settings: GameSettings instance (optional, for graphical help)
            context: TCOD context (optional, for graphical help)
            tile_manager: TileManager instance (optional, for graphical help)
        """
        self.status_renderer = status_renderer
        self.message_log_renderer = message_log_renderer
        self.settings = settings
        self.context = context
        self.tile_manager = tile_manager

        # Create help menu once (reuse for multiple opens)
        self._help_menu = None

    # === HELPER METHODS ===

    def _clear_game_area(self, console: tcod.console.Console) -> None:
        """Clear only the main game area, preserving UI elements."""
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(1, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)

    def _render_overlay_menu(self, console: tcod.console.Console, title: str, options: list, menu_width: int = 30) -> tuple:
        """Render a centered overlay menu with title and options.
        Returns (menu_x, menu_y, menu_height) for additional rendering."""
        menu_height = 6 + len(options)  # Header + options + padding
        menu_x = (GameConfig.SCREEN_WIDTH - menu_width) // 2
        menu_y = (GameConfig.SCREEN_HEIGHT - menu_height) // 2

        # Menu background
        for y in range(menu_y, menu_y + menu_height):
            for x in range(menu_x, menu_x + menu_width):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.UI_BG)

        # Menu borders (top and bottom)
        for x in range(menu_x, menu_x + menu_width):
            render_char_safe(console, x, menu_y, '=', fg=Colors.CYAN, bg=Colors.UI_BG)
            render_char_safe(console, x, menu_y + menu_height - 1, '─', fg=Colors.CYAN, bg=Colors.UI_BG)

        # Title (centered)
        title_x = menu_x + (menu_width - len(title)) // 2
        render_char_safe(console, title_x, menu_y + 2, title, fg=Colors.YELLOW, bg=Colors.UI_BG)

        # Options
        for i, option in enumerate(options):
            render_char_safe(console, menu_x + 3, menu_y + 4 + i, option, fg=Colors.WHITE, bg=Colors.UI_BG)

        return menu_x, menu_y, menu_height

    # === FULL SCREEN RENDERING METHODS ===

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

    def render_inventory_screen(self, console: tcod.console.Console, game):
        """Render the inventory screen with scrolling support."""
        # Clear only the main game area, preserve UI elements
        self._clear_game_area(console)

        # Title (centered in game area only)
        ScreenRenderingUtils.render_centered_title_in_area(
            console, "INVENTORY SYSTEM", 2, GameConfig.GAME_AREA_WIDTH()
        )

        # Render preserved UI elements (skip bottom panel to make room for inventory controls)
        self.status_renderer.render_top_status_bar(console, game)
        self.message_log_renderer.render_system_log(console, game)

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

    def _build_inventory_lines(self, game):
        """Build all inventory display lines with formatting."""
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
        """Find which line number the current selection is on."""
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
        """Render inventory controls."""
        y_start = GameConfig.SCREEN_HEIGHT - 6

        render_char_safe(console, 2, y_start, "CONTROLS:", fg=Colors.CYAN)
        render_char_safe(console, 4, y_start + 1, "W/S: Navigate  Enter: Use  X: Examine", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 2, "U: Unequip selected exploit", fg=Colors.WHITE)
        render_char_safe(console, 4, y_start + 3, "ESC/I: Close inventory", fg=Colors.WHITE)

    def render_story_fragment_screen(self, console: tcod.console.Console, game, fragment_index: int):
        """Render a single story fragment discovery screen."""
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

    def render_lore_viewer_screen(self, console: tcod.console.Console, game):
        """Render the lore viewer showing all discovered fragments."""
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
        """Render the lore viewer list mode."""
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
        """Render the lore viewer reading mode."""
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
