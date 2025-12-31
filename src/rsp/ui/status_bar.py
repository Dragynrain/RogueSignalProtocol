#!/usr/bin/env python3
"""
Status bar rendering for top and bottom UI panels.

Handles rendering of:
- Top status bar: CPU, heat, trace, RAM with color-coded values
- Bottom panel: Equipped exploits and temporary conditions

Extracted from game_rendering_ui.py to improve modularity.
"""


import tcod

from rsp.utils.color_thresholds import ColorThresholdManager
from rsp.core.config import GameConfig
from rsp.core.data import GameData
from rsp.entities.base import Colors
from rsp.ui.common import render_char_safe
from rsp.utils.unicode import GameGlyphs


class StatusBarRenderer:
    """
    Renders top and bottom status bars for player information.

    Top bar displays: CPU, heat, trace level, RAM
    Bottom panel displays: Equipped exploits and temporary conditions
    """

    def __init__(self, settings=None):
        """
        Initialize status bar renderer.

        Args:
            settings: GameSettings instance (optional, for UI color)
        """
        self.settings = settings
        # Instance variable to store exploit positions for mouse click detection
        self.last_exploit_positions = []

    def _get_status_parts(self, game) -> list[str]:
        """
        Get the status parts for testing.

        Args:
            game: GameEngine with player stats

        Returns:
            List of status part strings
        """
        parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            f"Heat:{game.player.heat:3d}°C",
            f"Trace:{int(game.player.trace_level):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB",
        ]

        # Add ascension indicator if above A0
        if hasattr(game, "ascension_level") and game.ascension_level > 0:
            parts.append(f"A{game.ascension_level}")

        return parts

    def render_top_status_bar(self, console: tcod.console.Console, game):
        """
        Render the top status bar with player resources.

        Displays CPU, heat, trace, and RAM with color-coded values.
        Stays within game area width (help text is in log panel).

        Args:
            console: TCOD console to render to
            game: GameEngine with player stats
        """
        # Get UI color from settings
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        # Clear the entire top status area (rows 0-1)
        for y in range(2):
            for x in range(GameConfig.SCREEN_WIDTH):
                render_char_safe(console, x, y, " ", fg=Colors.UI_TEXT, bg=Colors.UI_BG)

        # Color coding for status values (using centralized thresholds)
        cpu_color = ColorThresholdManager.get_cpu_color(game.player.cpu)
        heat_color = ColorThresholdManager.get_heat_color(game.player.heat)
        trace_color = ColorThresholdManager.get_trace_color(game.player.trace_level)
        ram_color = Colors.RED if game.player.ram_used > game.player.ram_total else Colors.GREEN

        # Build status line (only left side stats - help text goes in log panel)
        status_parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            (
                f"Heat:{game.player.heat:3d}°C/{game.player.max_heat}°C"
                if game.player.max_heat > 100
                else f"Heat:{game.player.heat:3d}°C"
            ),
            f"Trace:{int(game.player.trace_level):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB",
        ]

        colors = [cpu_color, heat_color, trace_color, ram_color]

        # Add ascension indicator if above A0
        if hasattr(game, "ascension_level") and game.ascension_level > 0:
            status_parts.append(f"A{game.ascension_level}")
            colors.append(Colors.CYAN)

        # Render status text on row 0
        x_pos = 1
        for part, color in zip(status_parts, colors):
            # Keep status bar in game area only
            if x_pos + len(part) <= GameConfig.GAME_AREA_WIDTH() - 1:
                render_char_safe(console, x_pos, 0, part, fg=color, bg=Colors.UI_BG)
                x_pos += len(part) + 2

        # Bottom border of status bar (row 1) - horizontal line with UI color
        # Use T-piece where it meets the vertical log border
        for x in range(GameConfig.SCREEN_WIDTH):
            if x == GameConfig.GAME_AREA_WIDTH():
                # T-piece where horizontal status bar meets vertical log border (╦ points down)
                render_char_safe(
                    console, x, 1, GameGlyphs.WALL_T_DOWN, fg=ui_color, bg=Colors.UI_BG
                )
            else:
                render_char_safe(
                    console, x, 1, GameGlyphs.WALL_HORIZONTAL, fg=ui_color, bg=Colors.UI_BG
                )

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
        # Get UI color from settings
        ui_color = self.settings.get_ui_color_rgb() if self.settings else Colors.CYAN

        # Clear panel area (full screen width to accommodate all exploits)
        for x in range(GameConfig.SCREEN_WIDTH):
            for y in range(GameConfig.PANEL_Y(), GameConfig.SCREEN_HEIGHT):
                render_char_safe(console, x, y, " ", fg=Colors.UI_TEXT, bg=Colors.UI_BG)

        # Panel border - horizontal line with UI color
        # Use T-piece where it meets the vertical log border
        for x in range(GameConfig.SCREEN_WIDTH):
            if x == GameConfig.GAME_AREA_WIDTH():
                # T-piece where horizontal bottom panel meets vertical log border (╩ points up)
                render_char_safe(
                    console,
                    x,
                    GameConfig.PANEL_Y(),
                    GameGlyphs.WALL_T_UP,
                    fg=ui_color,
                    bg=Colors.UI_BG,
                )
            else:
                render_char_safe(
                    console,
                    x,
                    GameConfig.PANEL_Y(),
                    GameGlyphs.WALL_HORIZONTAL,
                    fg=ui_color,
                    bg=Colors.UI_BG,
                )

        # Equipped exploits (2 lines)
        self._render_equipped_exploits_panel(console, game)

        # Temporary conditions/effects (1 line)
        self._render_temporary_conditions(console, game)

        # Render "Inv" button in bottom right corner for mouse users with hover highlighting
        inv_button_text = "[Inv]"
        inv_button_x = GameConfig.SCREEN_WIDTH - len(inv_button_text) - 1
        inv_button_y = GameConfig.SCREEN_HEIGHT - 1  # Bottom row

        # Check if mouse is hovering over Inv button
        mouse_tile_x = game.last_mouse_tile_x
        mouse_tile_y = game.last_mouse_tile_y
        is_inv_hovered = (
            mouse_tile_x is not None
            and mouse_tile_y is not None
            and mouse_tile_y == inv_button_y
            and inv_button_x <= mouse_tile_x < inv_button_x + len(inv_button_text)
        )

        # Use highlight background if hovered
        inv_bg = Colors.UI_HIGHLIGHT if is_inv_hovered else Colors.UI_BG
        render_char_safe(
            console, inv_button_x, inv_button_y, inv_button_text, fg=Colors.YELLOW, bg=inv_bg
        )

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
        self.last_exploit_positions = []

        # Check if mouse is hovering over exploit bar area
        mouse_tile_x = game.last_mouse_tile_x
        mouse_tile_y = game.last_mouse_tile_y

        # Fixed layout: exploits 1,2,3 on first line, 4,5 on second line
        line1_exploits = []
        line2_exploits = []

        for i, exploit_key in enumerate(equipped_exploits):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                heat_cost = exploit.heat
                if game.player.temporary_effects["exploit_efficiency_turns"] > 0:
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
            is_hovered = (
                mouse_tile_x is not None
                and mouse_tile_y is not None
                and mouse_tile_y == y1
                and x_pos <= mouse_tile_x < x_pos + text_width
            )

            # Store position for click detection
            self.last_exploit_positions.append(
                {"slot": slot, "x": x_pos, "y": y1, "width": text_width, "exploit_key": exploit_key}
            )

            # Determine background color (Phase 3.4: Gamepad visual feedback)
            # Priority: selected (gamepad) > hovered (mouse)
            is_selected = (
                slot == game.selected_exploit_index
                if hasattr(game, "selected_exploit_index")
                else False
            )
            if is_selected:
                # Subtle highlight for gamepad-selected exploit (shows which RT will fire)
                bg = Colors.UI_ACCENT  # Use existing UI_ACCENT color from palette
            elif is_hovered:
                # Subtle highlight for mouse hover
                bg = Colors.UI_HIGHLIGHT
            else:
                bg = Colors.UI_BG

            render_char_safe(console, x_pos, y1, exploit_text, fg=color, bg=bg)
            x_pos += text_width + 2

        # Render second line exploits
        if line2_exploits:
            render_char_safe(
                console, 1, y2, "        ", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG
            )  # Indent to align
            x_pos = 11
            for exploit_key, exploit_text, color, slot in line2_exploits:
                # Check if mouse is hovering over this exploit
                text_width = len(exploit_text)
                is_hovered = (
                    mouse_tile_x is not None
                    and mouse_tile_y is not None
                    and mouse_tile_y == y2
                    and x_pos <= mouse_tile_x < x_pos + text_width
                )

                # Store position for click detection
                self.last_exploit_positions.append(
                    {
                        "slot": slot,
                        "x": x_pos,
                        "y": y2,
                        "width": text_width,
                        "exploit_key": exploit_key,
                    }
                )

                # Determine background color (Phase 3.4: Gamepad visual feedback)
                # Priority: selected (gamepad) > hovered (mouse)
                is_selected = (
                    slot == game.selected_exploit_index
                    if hasattr(game, "selected_exploit_index")
                    else False
                )
                if is_selected:
                    # Subtle highlight for gamepad-selected exploit (shows which RT will fire)
                    bg = Colors.UI_ACCENT  # Use existing UI_ACCENT color from palette
                elif is_hovered:
                    # Subtle highlight for mouse hover
                    bg = Colors.UI_HIGHLIGHT
                else:
                    bg = Colors.UI_BG

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
                display_name = effect_name.replace("_turns", "").replace("_", " ").title()
                condition_text = f"{display_name}({turns})"

                # Color conditions based on their type
                if effect_name == "traffic_masquerade_turns":
                    color = Colors.BLUE  # Invisible effect
                elif effect_name == "speed_boost_turns":
                    color = self._get_data_code_color_for_effect(game, "speed_boost", Colors.YELLOW)
                elif effect_name == "movement_slowed_turns":
                    color = Colors.ORANGE  # Movement slowed effect
                elif effect_name == "enhanced_vision_turns":
                    color = self._get_data_code_color_for_effect(
                        game, "enhanced_vision", Colors.ELECTRIC_BLUE
                    )
                elif effect_name == "exploit_efficiency_turns":
                    color = self._get_data_code_color_for_effect(
                        game, "exploit_efficiency", Colors.ELECTRIC_PURPLE
                    )
                elif effect_name == "virus_turns":
                    color = Colors.DARK_GREEN  # Virus effect
                else:
                    color = Colors.WHITE  # Default color for other effects

                conditions.append((condition_text, color))

        # Threat scan effect
        if game.game_state.threat_scan_turns > 0:
            conditions.append(
                (f"Threat Scan({game.game_state.threat_scan_turns})", Colors.ELECTRIC_PURPLE)
            )

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

    def _get_data_code_color_for_effect(
        self, game, effect_key: str, fallback_color: tuple[int, int, int]
    ) -> tuple[int, int, int]:
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
            "crimson": Colors.CRIMSON,
            "azure": Colors.AZURE,
            "emerald": Colors.EMERALD,
            "golden": Colors.GOLDEN,
            "violet": Colors.VIOLET,
            "silver": Colors.SILVER,
        }

        # Find which color has this effect in the current game
        for color_name, (effect, _) in game.code_hack_effects.items():
            if effect == effect_key:
                return color_map.get(color_name, fallback_color)

        return fallback_color
