#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Rendering UI Coordinator

Coordinates UI rendering by delegating to specialized modules:
- StatusBarRenderer: Top/bottom status panels (extracted)
- MessageLogRenderer: System message log (extracted)
- InfoPanelRenderer: Info panel (already in game_info_panel.py)
- Full-screen overlays: Help, inventory, lore viewer, achievements (in this file)

Refactored to improve modularity while preserving full functionality.
"""


import tcod

from game_config import GameConfig
from game_data import GameData
from game_entities import Colors
from game_message_log_renderer import MessageLogRenderer
from game_screen_utilities import ScreenRenderingUtils, ScrollableListManager

# Import extracted renderers
from game_status_bar_renderer import StatusBarRenderer
from game_ui import render_char_safe


class UIRenderer:
    """
    UI rendering coordinator delegating to specialized modules.

    Delegates to:
    - StatusBarRenderer: Top/bottom panels (game_status_bar_renderer.py)
    - MessageLogRenderer: Message log (game_message_log_renderer.py)
    - InfoPanelRenderer: Info panel (game_info_panel.py)
    - EntityInspector: Inspection panel (game_inspection.py)

    Directly handles:
    - Full-screen overlays: Help, inventory, lore viewer, achievements
    """

    def __init__(self, settings=None, context=None, tile_manager=None):
        """
        Initialize UI renderer and sub-renderers.

        Args:
            settings: GameSettings instance (optional, for context)
            context: TCOD context (optional, for context)
            tile_manager: TileManager instance (optional, for context)
        """
        self.settings = settings
        self.context = context
        self.tile_manager = tile_manager

        # Initialize extracted renderers
        self.status_bar_renderer = StatusBarRenderer(settings)
        self.message_log_renderer = MessageLogRenderer(settings)

    # ========================================================================
    # STATUS BAR RENDERING (Delegated to StatusBarRenderer)
    # ========================================================================

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """Delegate to StatusBarRenderer."""
        self.status_bar_renderer.render_top_status_bar(console, game)
        # Update class variable for backward compatibility
        UIRenderer.last_exploit_positions = StatusBarRenderer.last_exploit_positions

    def render_bottom_panel(self, console: tcod.console.Console, game):
        """Delegate to StatusBarRenderer."""
        self.status_bar_renderer.render_bottom_panel(console, game)
        # Update class variable for backward compatibility
        UIRenderer.last_exploit_positions = StatusBarRenderer.last_exploit_positions

    # Old implementation removed - now delegated to game_status_bar_renderer.py
    # The following methods are no longer needed here:
    # - render_top_status_bar (original implementation)
    # - render_bottom_panel (original implementation)
    # - _render_equipped_exploits_panel
    # - _render_temporary_conditions
    # - _get_data_code_color_for_effect

    # ========================================================================
    # MESSAGE LOG RENDERING (Delegated to MessageLogRenderer)
    # ========================================================================

    def render_system_log(self, console: tcod.console.Console, game):
        """Delegate to MessageLogRenderer."""
        self.message_log_renderer.render_system_log(console, game)

    # Old implementation removed - now delegated to game_message_log_renderer.py
    # The following methods are no longer needed here:
    # - render_system_log (original implementation)
    # - _render_log_messages
    # - _wrap_messages

    # Preserve the rest of the file starting from INFO PANEL section
    # The line numbers below are adjusted after removal of delegated code

    # ========================================================================
    # INFO PANEL RENDERING (Delegated to InfoPanelRenderer)
    # ========================================================================

    def render_info_panel(self, console: tcod.console.Console, game):
        """
        Render the info panel in the top-right corner.

        Delegates to InfoPanelRenderer (already extracted to game_info_panel.py).
        """
        from game_info_panel import InfoPanelRenderer

        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN
        InfoPanelRenderer.render(console, game, ui_color=ui_color)

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
        from game_coordinate_helpers import CoordinateHelpers

        for x in range(GameConfig.GAME_AREA_WIDTH()):
            for y in range(
                2, GameConfig.PANEL_Y()
            ):  # Start from row 2 (after status bar on rows 0-1)
                render_char_safe(console, x, y, " ", fg=Colors.WHITE, bg=Colors.BLACK)

        # Set alpha to opaque for the cleared area
        CoordinateHelpers.set_alpha_region(
            console,
            x=0,
            y=2,
            width=GameConfig.GAME_AREA_WIDTH(),
            height=GameConfig.PANEL_Y() - 2,
            alpha=255,
        )

    def _render_overlay_menu(
        self, console: tcod.console.Console, title: str, options: list, menu_width: int = 30
    ) -> tuple:
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
                render_char_safe(console, x, y, " ", fg=Colors.WHITE, bg=Colors.UI_BG)

        # Menu borders (top and bottom)
        for x in range(menu_x, menu_x + menu_width):
            render_char_safe(console, x, menu_y, "═", fg=Colors.CYAN, bg=Colors.UI_BG)
            render_char_safe(
                console, x, menu_y + menu_height - 1, "═", fg=Colors.CYAN, bg=Colors.UI_BG
            )

        # Title (centered)
        title_x = menu_x + (menu_width - len(title)) // 2
        render_char_safe(console, title_x, menu_y + 2, title, fg=Colors.YELLOW, bg=Colors.UI_BG)

        # Options
        for i, option in enumerate(options):
            render_char_safe(
                console, menu_x + 3, menu_y + 4 + i, option, fg=Colors.WHITE, bg=Colors.UI_BG
            )

        return menu_x, menu_y, menu_height

    # === Help Screen ===

    def render_help_screen(self, console: tcod.console.Console, help_menu):
        """
        Render the help screen using provided help menu.

        Help menu creation and caching is handled by the orchestration layer
        (GameRenderer) to avoid backwards dependency from rendering layer to menus layer.

        Args:
            console: TCOD console to render to
            help_menu: Pre-created help menu instance to render
        """
        help_menu.render(console)

    def render_help_sprites(self, help_menu):
        """
        Render help screen sprites (for GraphicalHelpMenu only).

        This should be called BEFORE render_help_screen when in graphics mode.
        Only GraphicalHelpMenu has this method.

        Args:
            help_menu: Pre-created help menu instance
        """
        if help_menu and hasattr(help_menu, "render_sprites"):
            help_menu.render_sprites()

    def handle_help_input(self, event, help_menu) -> str:
        """
        Handle input for help screen.

        Args:
            event: TCOD event
            help_menu: Pre-created help menu instance

        Returns:
            Result from help menu input handler ('back' to exit, '' to continue)
        """
        if help_menu:
            return help_menu.handle_input(event)
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
        self.render_info_panel(console, game)  # Render info panel so it's not black
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
            render_char_safe(console, line_data["x"], y, line_data["text"], fg=line_data["color"])
            y += 1

        # Show scroll indicators using utility
        ScreenRenderingUtils.render_scroll_indicators(
            console,
            x=GameConfig.GAME_AREA_WIDTH() - 8,
            top_y=content_start_y,
            bottom_y=controls_y - 2,
            show_up=scroll_manager.should_show_scroll_up(),
            show_down=scroll_manager.should_show_scroll_down(),
        )

        # Controls
        self._render_inventory_controls(console)

        # Store data for mouse click detection (single source of truth)
        UIRenderer.last_inventory_lines = inventory_lines
        UIRenderer.last_inventory_content_start_y = content_start_y
        UIRenderer.last_inventory_scroll_offset = scroll_manager.get_scroll_offset()
        UIRenderer.last_inventory_equipped_count = len(
            game.player.inventory_manager.equipped_exploits
        )

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
        lines.append(
            {"x": 2, "text": "EQUIPPED EXPLOITS:", "color": Colors.CYAN, "selectable": False}
        )

        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            # Get exploit category color
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                from game_color_manager import ColorManager

                category_color = ColorManager.get_exploit_color(exploit.category)
                text = f"{i+1}. {exploit.name}"
            else:
                category_color = Colors.RED
                text = f"{i+1}. INVALID: {exploit_key}"

            # Use yellow for selection, category color otherwise
            if i == game.inventory_selection:
                color = Colors.YELLOW
                prefix = ">"
            else:
                color = category_color
                prefix = " "

            lines.append({"x": 4, "text": f"{prefix} {text}", "color": color, "selectable": True})

        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            lines.append(
                {
                    "x": 4,
                    "text": f"[{equipped_count}/{max_exploits} slots used]",
                    "color": Colors.YELLOW,
                    "selectable": False,
                }
            )

        lines.append({"x": 2, "text": "", "color": Colors.WHITE, "selectable": False})  # Spacer

        # Code hacks section
        code_hacks = game.player.inventory_manager.get_items_by_type("code_hack")
        lines.append(
            {
                "x": 2,
                "text": f"CODES ({len(code_hacks)}):",
                "color": Colors.CYAN,
                "selectable": False,
            }
        )

        if not code_hacks:
            lines.append(
                {"x": 4, "text": "No codes collected", "color": Colors.WHITE, "selectable": False}
            )
        else:
            display_items = game.player.inventory_manager.get_display_items()

            for i, patch in enumerate(code_hacks):
                display_index = display_items.index(patch)
                adjusted_selection_index = display_index + equipped_count

                # Use the code hack's actual color (converted from color_name)
                code_color = Colors.get_color(patch.color_name.upper())

                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW  # Keep yellow for selected item (high visibility)
                    prefix = ">"
                else:
                    color = code_color  # Use actual code color when not selected
                    prefix = " "

                description = patch.description if patch.discovered else "Unknown effect"
                quantity_text = f" ({patch.quantity})" if patch.quantity > 1 else ""
                patch_text = f"{prefix} {patch.name}{quantity_text} - {description}"

                max_width = GameConfig.GAME_AREA_WIDTH() - 6
                if len(patch_text) > max_width:
                    patch_text = patch_text[: max_width - 3] + "..."

                lines.append({"x": 4, "text": patch_text, "color": color, "selectable": True})

        lines.append({"x": 2, "text": "", "color": Colors.WHITE, "selectable": False})  # Spacer

        # Unequipped exploits section
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        lines.append(
            {
                "x": 2,
                "text": f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):",
                "color": Colors.CYAN,
                "selectable": False,
            }
        )

        if not exploit_items:
            lines.append(
                {
                    "x": 4,
                    "text": "No unequipped exploits",
                    "color": Colors.WHITE,
                    "selectable": False,
                }
            )
        else:
            display_items = game.player.inventory_manager.get_display_items()

            for i, exploit_item in enumerate(exploit_items):
                try:
                    display_index = display_items.index(exploit_item)
                    adjusted_selection_index = display_index + equipped_count
                except ValueError:
                    adjusted_selection_index = -1

                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    from game_color_manager import ColorManager

                    category_color = ColorManager.get_exploit_color(exploit_def.category)

                    # Use yellow for selection, category color otherwise
                    if adjusted_selection_index == game.inventory_selection:
                        name_color = Colors.YELLOW
                        prefix = ">"
                    else:
                        name_color = category_color
                        prefix = " "

                    name_text = f"{prefix} {exploit_item.name}"
                    lines.append(
                        {"x": 4, "text": name_text, "color": name_color, "selectable": True}
                    )

                    stats_text = f"    RAM:{exploit_def.ram} Heat:{exploit_def.heat}"
                    if exploit_def.damage > 0:
                        stats_text += f" Damage:{exploit_def.damage}"
                    if exploit_def.range > 0:
                        stats_text += f" Range:{exploit_def.range}"
                    lines.append(
                        {
                            "x": 4,
                            "text": stats_text,
                            "color": Colors.LIGHT_GRAY,
                            "selectable": False,
                        }
                    )
                else:
                    # Unknown exploit - use red
                    if adjusted_selection_index == game.inventory_selection:
                        color = Colors.YELLOW
                        prefix = ">"
                    else:
                        color = Colors.RED
                        prefix = " "
                    text = f"{prefix} {exploit_item.name} [Unknown]"
                    lines.append({"x": 4, "text": text, "color": color, "selectable": True})

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

        Shows available actions: equip, unequip, install, use, and close.

        Args:
            console: TCOD console to render to
        """
        y_start = GameConfig.SCREEN_HEIGHT - 6

        render_char_safe(console, 2, y_start, "CONTROLS:", fg=Colors.CYAN)
        render_char_safe(
            console, 4, y_start + 1, "↑↓/W/S: Navigate │ Enter/Click: Use/Equip/Unequip", fg=Colors.WHITE
        )
        render_char_safe(
            console, 4, y_start + 2, "ESC/I/Right-Click: Close inventory", fg=Colors.WHITE
        )

    @staticmethod
    def get_inventory_item_at_click(tile_y: int) -> int | None:
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
        if not line_data.get("selectable", False):
            return None

        # Count how many selectable lines came before this one to get selection index
        selection_index = 0
        for i in range(line_index):
            if UIRenderer.last_inventory_lines[i].get("selectable", False):
                selection_index += 1

        return selection_index

    @staticmethod
    def get_exploit_at_click(tile_x: int, tile_y: int) -> int | None:
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
            x = exploit_data["x"]
            y = exploit_data["y"]
            width = exploit_data["width"]
            slot = exploit_data["slot"]

            # Check if click is within this exploit's bounds
            if y == tile_y and x <= tile_x < x + width:
                return slot

        return None

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
        if not hasattr(self, "_achievements_menu"):
            from game_menu_achievements import AchievementsMenu

            self._achievements_menu = AchievementsMenu()

        self._achievements_menu.render(console)
