#!/usr/bin/env python3
"""
Game Rendering UI - Status
Renders the status bar and bottom panel.
"""

import tcod
from typing import Tuple

from game_config import GameConfig
from game_entities import Colors
from game_data import GameData
from game_ui import render_char_safe


class StatusBarRenderer:
    """Renders player status bar and bottom panel."""

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
