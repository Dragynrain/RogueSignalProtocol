#!/usr/bin/env python3
"""
Game Rendering UI
All UI overlays and HUD elements.
"""

import tcod
from typing import List, Tuple

from game_config import GameConfig
from game_entities import Colors
from game_data import GameData
from game_menus import HelpMenu
from data_loading import get_story_fragments
from game_ui import render_char_safe


class UIRenderer:
    """Renders UI elements."""

    def _clear_game_area(self, console: tcod.console.Console) -> None:
        """Clear only the main game area, preserving UI elements."""
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(1, GameConfig.PANEL_Y()):
                render_char_safe(console, x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)

    def _render_centered_title(self, console: tcod.console.Console, title: str, y: int, color: tuple = Colors.YELLOW) -> None:
        """Render a centered title in the game area."""
        title_x = GameConfig.GAME_AREA_WIDTH() // 2 - len(title) // 2
        render_char_safe(console, title_x, y, title, fg=color)

    def _render_screen_header(self, console: tcod.console.Console, title: str, subtitle: str = None) -> int:
        """Render a standardized screen header with title and optional subtitle.
        Returns the y position after the header for content to start."""
        # Top border
        render_char_safe(console, 2, 1, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)

        # Main title (centered)
        title_x = GameConfig.SCREEN_WIDTH // 2 - len(title) // 2
        render_char_safe(console, title_x, 2, title, fg=Colors.CYAN)

        # Subtitle if provided
        if subtitle:
            subtitle_x = GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2
            render_char_safe(console, subtitle_x, 3, subtitle, fg=Colors.WHITE)
            # Bottom border after subtitle
            render_char_safe(console, 2, 4, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 6  # Content starts at line 6
        else:
            # Bottom border after title
            render_char_safe(console, 2, 3, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 5  # Content starts at line 5

    def _render_screen_footer(self, console: tcod.console.Console, instructions: str, additional_line: str = None) -> None:
        """Render a standardized screen footer with instructions."""
        footer_y = GameConfig.SCREEN_HEIGHT - 4 if additional_line else GameConfig.SCREEN_HEIGHT - 3

        # Footer border
        render_char_safe(console, 2, footer_y, "─" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)

        # Instructions (centered)
        instructions_x = GameConfig.SCREEN_WIDTH // 2 - len(instructions) // 2
        render_char_safe(console, instructions_x, footer_y + 1, instructions, fg=Colors.YELLOW)

        # Additional line if provided
        if additional_line:
            additional_x = GameConfig.SCREEN_WIDTH // 2 - len(additional_line) // 2
            render_char_safe(console, additional_x, footer_y + 2, additional_line, fg=Colors.YELLOW)

    def _render_content_area_with_word_wrap(self, console: tcod.console.Console, text: str, start_y: int, end_y: int) -> None:
        """Render text content with word wrapping within the specified y bounds."""
        lines = text.split('\n')
        y_offset = start_y
        max_width = GameConfig.SCREEN_WIDTH - 6  # Leave margins

        for line in lines:
            if y_offset >= end_y:
                render_char_safe(console, 3, y_offset, "... [Text continues]", fg=Colors.YELLOW)
                break

            line = line.strip()
            if not line:
                y_offset += 1
                continue

            # Word wrap long lines
            if len(line) <= max_width:
                render_char_safe(console, 3, y_offset, line, fg=Colors.WHITE)
                y_offset += 1
            else:
                words = line.split(' ')
                current_line = ""

                for word in words:
                    if len(current_line + word) + 1 <= max_width:
                        current_line += (word if not current_line else " " + word)
                    else:
                        if current_line:
                            render_char_safe(console, 3, y_offset, current_line, fg=Colors.WHITE)
                            y_offset += 1
                            if y_offset >= end_y:
                                break
                        current_line = word

                if current_line and y_offset < end_y:
                    render_char_safe(console, 3, y_offset, current_line, fg=Colors.WHITE)
                    y_offset += 1

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

    def render_help_screen(self, console: tcod.console.Console):
        """Render the help screen using HelpMenu content."""
        # Create a temporary HelpMenu and use its render method
        help_menu = HelpMenu()
        help_menu.render(console)


    def render_inventory_screen(self, console: tcod.console.Console, game):
        """Render the inventory screen with scrolling support."""
        # Clear only the main game area, preserve UI elements
        self._clear_game_area(console)

        # Title (centered in game area only)
        self._render_centered_title(console, "INVENTORY SYSTEM", 2)

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

        # Adjust scroll offset to keep selection visible
        self._adjust_scroll_for_selection(game, total_lines, max_content_height)

        # Render visible portion
        y = content_start_y
        scroll_offset = game.inventory_scroll_offset
        visible_end = min(scroll_offset + max_content_height, total_lines)

        for i in range(scroll_offset, visible_end):
            line_data = inventory_lines[i]
            render_char_safe(console, line_data['x'], y, line_data['text'], fg=line_data['color'])
            y += 1

        # Show scroll indicators if needed
        if scroll_offset > 0:
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH() - 8, content_start_y, "^ MORE ^", fg=Colors.YELLOW)
        if visible_end < total_lines:
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH() - 8, controls_y - 2, "v MORE v", fg=Colors.YELLOW)

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

    def _adjust_scroll_for_selection(self, game, total_lines: int, max_visible: int):
        """Adjust scroll offset to keep selected item visible."""
        if total_lines <= max_visible:
            game.inventory_scroll_offset = 0
            return

        # Find which line the selection is on
        selection_line = self._find_selection_line(game)

        if selection_line < game.inventory_scroll_offset:
            # Selection is above viewport, scroll up
            game.inventory_scroll_offset = selection_line
        elif selection_line >= game.inventory_scroll_offset + max_visible:
            # Selection is below viewport, scroll down
            game.inventory_scroll_offset = selection_line - max_visible + 1

        # Clamp scroll offset
        max_scroll = max(0, total_lines - max_visible)
        game.inventory_scroll_offset = max(0, min(game.inventory_scroll_offset, max_scroll))

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

    def _render_equipped_exploits(self, console: tcod.console.Console, game, y: int) -> int:
        """Render equipped exploits section."""
        render_char_safe(console, 2, y, "EQUIPPED EXPLOITS:", fg=Colors.CYAN)
        y += 1

        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            # Check if this equipped exploit is selected
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
                status_text = f"{prefix} {i+1}. {exploit.name}"
            else:
                status_text = f"{prefix} {i+1}. INVALID: {exploit_key}"

            render_char_safe(console, 4, y, status_text, fg=color)
            y += 1

        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            render_char_safe(console, 4, y, f"[{equipped_count}/{max_exploits} slots used]", fg=Colors.YELLOW)
            y += 1

        return y

    def _render_code_hacks(self, console: tcod.console.Console, game, y: int) -> int:
        """Render codes section."""
        code_hacks = game.player.inventory_manager.get_items_by_type("code_hack")
        render_char_safe(console, 2, y, f"CODES ({len(code_hacks)}):", fg=Colors.CYAN)
        y += 1

        if not code_hacks:
            render_char_safe(console, 4, y, "No codes collected", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)

            for i, patch in enumerate(code_hacks):
                display_index = display_items.index(patch)
                # Adjust selection index to account for equipped exploits
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

                # Truncate text to fit in game area
                max_width = GameConfig.GAME_AREA_WIDTH() - 6  # 4 indent + 2 margin
                if len(patch_text) > max_width:
                    patch_text = patch_text[:max_width-3] + "..."
                render_char_safe(console, 4, y, patch_text, fg=color)
                y += 1

        return y

    def _render_unequipped_exploits(self, console: tcod.console.Console, game, y: int) -> int:
        """Render unequipped exploits section."""
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        render_char_safe(console, 2, y, f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):", fg=Colors.CYAN)
        y += 1

        if not exploit_items:
            render_char_safe(console, 4, y, "No unequipped exploits", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)

            for i, exploit_item in enumerate(exploit_items):
                try:
                    display_index = display_items.index(exploit_item)
                    # Adjust selection index to account for equipped exploits
                    adjusted_selection_index = display_index + equipped_count
                except ValueError:
                    adjusted_selection_index = -1

                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "

                # Get exploit definition for stats
                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]

                    # Show name and stats breakdown
                    name_text = f"{prefix} {exploit_item.name}"
                    render_char_safe(console, 4, y, name_text, fg=color)
                    y += 1

                    # Show stats on second line with smaller indentation
                    stats_text = f"    RAM:{exploit_def.ram} Heat:{exploit_def.heat}"
                    if exploit_def.damage > 0:
                        stats_text += f" Damage:{exploit_def.damage}"
                    if exploit_def.range > 0:
                        stats_text += f" Range:{exploit_def.range}"
                    render_char_safe(console, 4, y, stats_text, fg=Colors.LIGHT_GRAY)
                    y += 1
                else:
                    # Fallback for unknown exploits
                    exploit_text = f"{prefix} {exploit_item.name} - Unknown exploit"
                    render_char_safe(console, 4, y, exploit_text, fg=color)
                    y += 1

        return y

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

        # Render using shared components
        content_start_y = self._render_screen_header(console, "DATA FRAGMENT RECOVERED")
        content_end_y = GameConfig.SCREEN_HEIGHT - 6  # Leave room for 2-line footer

        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)

        self._render_screen_footer(console, "Press any key to continue...", "Press 'L' to view all lore")

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
        content_start_y = self._render_screen_header(console, title)

        if not discovered_fragments:
            # No fragments discovered yet - center the message
            no_fragments_y = GameConfig.SCREEN_HEIGHT // 2
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 15, no_fragments_y, "No data fragments discovered yet.", fg=Colors.YELLOW)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, no_fragments_y + 2, "Reach the Military Network (Level 3) to find them.", fg=Colors.WHITE)
            self._render_screen_footer(console, "Press ESC to close")
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

            self._render_screen_footer(console, "Up/Down: Navigate, Enter: Read, ESC: Close")

    def _render_lore_reading_mode(self, console: tcod.console.Console, game, discovered_fragments):
        """Render the lore viewer reading mode."""
        if game.lore_viewer_selection >= len(discovered_fragments):
            game.lore_viewer_selection = 0

        fragment_index, fragment_text = discovered_fragments[game.lore_viewer_selection]

        title = f"DATA FRAGMENT #{fragment_index + 1}"
        content_start_y = self._render_screen_header(console, title)
        content_end_y = GameConfig.SCREEN_HEIGHT - 4  # Leave room for footer

        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)

        self._render_screen_footer(console, "Any key: Back to list, ESC: Close")

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """Render the top status bar across the full width."""
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
        """Get color for CPU display."""
        if cpu < 30:
            return Colors.RED
        elif cpu < 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def _get_heat_color(self, heat: int) -> Tuple[int, int, int]:
        """Get color for heat display."""
        if heat > 80:
            return Colors.RED
        elif heat > 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def _get_trace_color(self, trace_level: float) -> Tuple[int, int, int]:
        """Get color for trace_level display."""
        if trace_level > 75:
            return Colors.RED
        elif trace_level > 50:
            return Colors.YELLOW
        else:
            return Colors.GREEN

    def render_bottom_panel(self, console: tcod.console.Console, game):
        """Render the bottom information panel."""
        # Clear panel area
        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(GameConfig.PANEL_Y(), GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)

        # Panel border
        border = "┌" + "─" * (GameConfig.GAME_AREA_WIDTH() - 2) + "┐"
        render_char_safe(console, 0, GameConfig.PANEL_Y(), border, fg=Colors.LOG_BORDER, bg=Colors.UI_BG)

        # Equipped exploits (2 lines)
        self._render_equipped_exploits_panel(console, game)

        # Temporary conditions/effects (1 line)
        self._render_temporary_conditions(console, game)


    def _render_equipped_exploits_panel(self, console: tcod.console.Console, game):
        """Render equipped exploits in bottom panel using 2 lines."""
        y1 = GameConfig.PANEL_Y() + 1
        y2 = GameConfig.PANEL_Y() + 2

        render_char_safe(console, 1, y1, "Exploits:", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)

        equipped_exploits = game.player.inventory_manager.equipped_exploits[:5]

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
                    line1_exploits.append((exploit_key, exploit_text, color, i+1))
                else:
                    line2_exploits.append((exploit_key, exploit_text, color, i+1))

        # Render first line exploits
        x_pos = 11
        for exploit_key, exploit_text, color, slot_num in line1_exploits:
            render_char_safe(console, x_pos, y1, exploit_text, fg=color, bg=Colors.UI_BG)
            x_pos += len(exploit_text) + 2

        # Render second line exploits
        if line2_exploits:
            render_char_safe(console, 1, y2, "        ", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)  # Indent to align
            x_pos = 11
            for exploit_key, exploit_text, color, slot_num in line2_exploits:
                render_char_safe(console, x_pos, y2, exploit_text, fg=color, bg=Colors.UI_BG)
                x_pos += len(exploit_text) + 2

    def _render_temporary_conditions(self, console: tcod.console.Console, game):
        """Render all temporary conditions with turn counts remaining."""
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
        """Get the code color for a specific effect based on the current game's randomization."""
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


    def render_system_log(self, console: tcod.console.Console, game):
        """Render the system log on the right side."""
        # Draw log border
        for y in range(GameConfig.SCREEN_HEIGHT):
            render_char_safe(console, GameConfig.GAME_AREA_WIDTH(), y, '│', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Help text in top-right corner (properly positioned in log panel)
        help_text = "Press ? for help"
        help_x = GameConfig.GAME_AREA_WIDTH() + 2  # Leave a space after border
        render_char_safe(console, help_x, 0, help_text, fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)

        # Log header
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 1, "SYSTEM LOG", fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)
        render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, 2, "─" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)

        # Clear log area - start from line 3 to account for header repositioning
        for x in range(GameConfig.GAME_AREA_WIDTH() + 1, GameConfig.SCREEN_WIDTH):
            for y in range(3, GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)

        # Process and display messages
        self._render_log_messages(console, game)

    def _render_log_messages(self, console: tcod.console.Console, game):
        """Render log messages with proper wrapping."""
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.SCREEN_HEIGHT - 3  # Adjusted for header repositioning
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines

        for i, (line, color) in enumerate(visible_lines):
            y_pos = 3 + i  # Start from line 3 to avoid header
            if y_pos < GameConfig.SCREEN_HEIGHT:
                render_char_safe(console, GameConfig.GAME_AREA_WIDTH() + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)

    def _wrap_messages(self, messages: List) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Wrap long messages across multiple lines."""
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
