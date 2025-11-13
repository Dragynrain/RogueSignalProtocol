"""
Centralized Help Content - Single Source of Truth

This module provides all help menu content in a structured format,
eliminating duplication between glyph and graphics help modes.

All game data is loaded directly from JSON files to ensure accuracy.
"""

import logging
from typing import Any

from game_entities import Colors, ensure_color_tuple


class HelpContent:
    """
    Centralized help content provider.

    Loads data from game JSON files and provides it in a structured format
    for both glyph and graphics help menus.
    """

    # Enemy color coding by behavior type
    ENEMY_COLORS = {
        "static": ensure_color_tuple([255, 255, 0]),  # Yellow - stationary
        "mobile": ensure_color_tuple([255, 165, 0]),  # Orange - mobile
        "aggressive": ensure_color_tuple([220, 20, 60]),  # Red - hunter/admin
    }

    # Exploit category colors (from game_rules.json)
    EXPLOIT_COLORS = {
        "combat": ensure_color_tuple([255, 20, 80]),  # Crimson
        "stealth": ensure_color_tuple([200, 60, 255]),  # Purple
        "utility": ensure_color_tuple([20, 255, 200]),  # Cyan
        "emergency": ensure_color_tuple([255, 140, 0]),  # Orange
    }

    @staticmethod
    def _format_movement_keys() -> str:
        """
        Auto-generate movement key summary from InputMappings.

        Detects which key groups (Arrows, WASD/QEZC, Numpad) are present
        and formats them as a readable string.

        Returns:
            Formatted string like "Arrows / WASD / QEZC / Numpad"
        """
        from game_input import InputMappings

        key_names = [key.name for key in InputMappings.MOVEMENT_MAP.keys()]

        groups = []

        # Check for arrow keys
        if any(name in ["UP", "DOWN", "LEFT", "RIGHT"] for name in key_names):
            groups.append("Arrows")

        # Check for WASD/QEZC
        if any(name in ["W", "A", "S", "D", "Q", "E", "Z", "C"] for name in key_names):
            groups.append("WASD / QEZC")

        # Check for numpad
        if any("KP_" in name for name in key_names):
            groups.append("Numpad")

        return " / ".join(groups) if groups else "Not configured"

    @staticmethod
    def get_objectives() -> list[tuple[str, Any]]:
        """Get objective and core mechanics descriptions."""
        return [
            ("Reach the gateway to advance levels", Colors.WHITE),
        ]

    @staticmethod
    def get_core_mechanics() -> list[tuple[str, str, Any]]:
        """Get core mechanics (stat explanations)."""
        return [
            ("CPU", "Health (0 = death, save deleted!)", Colors.GREEN),
            ("Heat", "From exploits (100C+ = damage)", Colors.YELLOW),
            ("Trace", "From detection (max = Admin spawn)", Colors.RED),
            ("RAM", "Exploit space (max 5 equipped)", Colors.CYAN),
        ]

    @staticmethod
    def get_controls() -> dict[str, list[tuple[str, str]]]:
        """Get control mappings organized by category."""
        # Auto-generate movement key summary from InputMappings
        movement_keys = HelpContent._format_movement_keys()

        return {
            "movement": [
                ("Movement", movement_keys),  # Auto-synced from InputMappings
                ("Wait/Rest", "Space / . / Numpad5"),
                ("Exploits", "1-5 (use equipped)"),
            ],
            "screens": [
                ("I", "Inventory"),
                ("L", "Look Mode"),
                ("?", "Help"),
                ("F", "Lore"),
                ("V", "Achievements"),
                ("ESC", "Menu"),
                ("Enter", "Confirm/Select"),
            ],
            "inventory": [
                ("Up/Down", "Navigate items"),
                ("Enter", "Use/Equip/Unequip"),
                ("I/ESC", "Close inventory"),
            ],
            "mouse": [
                ("Left-Click", "Select/activate items"),
                ("Right-Click", "Go back/cancel"),
                ("Mouse Wheel", "Scroll lists & menus"),
                ("Hover", "Highlight elements"),
            ],
            "debug": [
                ("Shift+F12", "Export debug package"),
            ],
        }

    @staticmethod
    def get_map_symbols() -> list[tuple[str, str, str, Any]]:
        """Get map symbol descriptions (glyph, name, description, color)."""
        return [
            ("☺", "Player", "(you)", Colors.WHITE),
            ("•", "Floor", "(walkable)", Colors.FLOOR),
            ("♠", "Blind Spot", "(hide & +10 dmg!)", Colors.ELECTRIC_PURPLE),
            (">", "Gateway", "(next level)", Colors.GATEWAY),
            ("♫", "Data Fragment", "(story)", Colors.CYAN),
            ("╔╗╚╝╦╩╠╣╬═║", "Walls", "(blocking)", Colors.WALL),
        ]

    @staticmethod
    def get_enemy_data() -> dict[str, dict[str, Any]]:
        """
        Load enemy data from game_content.json.

        Returns dict with enemy stats, behavior type, and descriptions.
        """
        try:
            from data_loading import DataLoader

            game_data = DataLoader.load_game_data()

            # Manual descriptions for each enemy
            descriptions = {
                "Scanner": "Static (alerts!)",
                "Firewall": "Static wall guard",
                "Patrol": "Patrol routes",
                "Bot": "Wanders randomly",
                "Hunter": "Chases you!",
                "Virus": "Infects (no dmg)!",
                "Inhibitor": "Slows (no dmg)!",
                "Admin Avatar": "BOSS!",
            }

            # Behavior type mapping
            behavior_map = {
                "Scanner": "static",
                "Firewall": "static",
                "Patrol": "mobile",
                "Bot": "mobile",
                "Hunter": "aggressive",
                "Virus": "aggressive",
                "Inhibitor": "aggressive",
                "Admin Avatar": "aggressive",
            }

            result = {}
            for enemy_id, enemy_data in game_data["enemy_types"].items():
                # Capitalize the name for display
                enemy_name = enemy_data["name"]
                result[enemy_name] = {
                    "cpu": enemy_data["cpu"],
                    "vision": enemy_data["vision"],
                    "damage": enemy_data["damage"],
                    "behavior": behavior_map.get(enemy_name, "mobile"),
                    "description": descriptions.get(enemy_name, ""),
                    "glyph": enemy_data["symbol"],
                }

            return result

        except Exception as e:
            logging.error(f"Failed to load enemy data: {e}")
            # Return empty dict on error - help menu will handle gracefully
            return {}

    @staticmethod
    def get_power_ups() -> list[tuple[str, str, str, Any]]:
        """Get power-up descriptions (glyph, name, description, color)."""
        return [
            ("❀", "Code Patch", "Random stat bonus", Colors.ELECTRIC_PURPLE),
            ("⚠", "Exploit", "Combat/utility tool", HelpContent.EXPLOIT_COLORS["combat"]),
            ("♫", "Data Fragment", "Story/lore", Colors.CYAN),
        ]

    @staticmethod
    def get_nodes() -> list[tuple[str, str, str, Any]]:
        """Get node descriptions (glyph, name, description, color)."""
        return [
            ("♡", "CPU Node", "+20 HP (restore health)", Colors.RED),
            ("♢", "Cooling Node", "-20 heat", Colors.CYAN),
            ("♤", "Ghost Node", "-20% trace (blind spot)", Colors.ELECTRIC_PURPLE),
        ]

    @staticmethod
    def get_upgrades() -> list[tuple[str, str, str, Any]]:
        """Get upgrade descriptions (glyph, name, description, color)."""
        return [
            ("♥", "CPU Upgrade", "+20 max CPU (PERMANENT!)", Colors.ELECTRIC_BLUE),
            ("♦", "RAM Upgrade", "+4 RAM (PERMANENT!)", Colors.ELECTRIC_BLUE),
            ("▣", "Cooling Upgrade", "+20 heat tol (PERMANENT!)", Colors.ELECTRIC_BLUE),
        ]

    @staticmethod
    def get_exploits() -> dict[str, list[tuple[str, str, Any]]]:
        """
        Get exploit descriptions organized by category.

        Loads help summaries from game_content.json to ensure
        they stay in sync with actual exploit stats.
        """
        colors = HelpContent.EXPLOIT_COLORS

        # Load exploit data from JSON
        try:
            from data_loading import DataLoader

            game_data = DataLoader.load_game_data()
        except Exception as e:
            logging.error(f"Failed to load exploit data: {e}")
            # Return empty dict on error - help menu will handle gracefully
            return {"combat": [], "stealth": [], "utility": [], "emergency": []}

        # Organize by category
        exploits_by_category = {"combat": [], "stealth": [], "utility": [], "emergency": []}

        for exploit_id, exploit_data in game_data["exploits"].items():
            category = exploit_data.get("category", "utility")

            # Get color for this category
            color = colors.get(category, colors["utility"])

            # Use help_summary from JSON, fall back to description if missing
            summary = exploit_data.get("help_summary", exploit_data.get("description", ""))

            # Special case: System Crash is labeled as emergency in utility category
            display_name = exploit_data["name"]
            if category == "emergency":
                display_name = f"{display_name} (emergency)"
                # Add to utility section instead
                exploits_by_category["utility"].append((display_name, summary, color))
            else:
                exploits_by_category[category].append((exploit_data["name"], summary, color))

        return exploits_by_category

    @staticmethod
    def get_status_effects() -> dict[str, list[tuple[str, str, Any]]]:
        """Get status effect descriptions organized by type."""
        return {
            "positive": [
                ("Speed Boost", "2 moves/turn", Colors.GREEN),
                ("Invisibility", "Unseen (5t)", Colors.GREEN),
                ("Vision", "+2 range (5 turns)", Colors.GREEN),
                ("Efficiency", "-40% heat (8t)", Colors.GREEN),
            ],
            "negative": [
                ("Virus", "3 CPU/turn damage", Colors.RED),
                ("Slowed", "Move every 2nd turn", Colors.RED),
            ],
        }

    @staticmethod
    def get_survival_tips() -> list[tuple[str, Any]]:
        """Get survival tips."""
        return [
            ("Blind spots give +10dmg bonus to all attacks!", Colors.ELECTRIC_PURPLE),
            ("Move between attacks! Same spot = +1 heat penalty", Colors.WHITE),
            ("Admin Avatar is nearly unbeatable - avoid high trace!", Colors.RED),
        ]
