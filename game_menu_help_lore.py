#!/usr/bin/env python3
"""
Rogue Signal Protocol - Help and Lore Menus

Help menu system with text-based display and factory for mode selection.
LoreMenu displays discovered story fragments from main menu.
Factory function (create_help_menu) selects HelpMenu or GraphicalHelpMenu based on graphics mode.
"""

import tcod
import logging

from game_config import GameConfig
from game_entities import Colors
from game_story import StoryFragmentManager
from game_ui import render_char_safe, UniversalInputHandler
from game_screen_utilities import ScreenRenderingUtils


def create_help_menu(settings, context=None, tile_manager=None):
    """
    Factory function to create appropriate help menu based on graphics mode.

    Args:
        settings: GameSettings instance
        context: TCOD context (required for graphics mode)
        tile_manager: TileManager instance (required for graphics mode)

    Returns:
        HelpMenu or GraphicalHelpMenu instance
    """
    if settings.graphics_mode == "graphics" and tile_manager is not None:
        try:
            from game_menu_help_graphics import GraphicalHelpMenu
            logging.info("Creating GraphicalHelpMenu")
            return GraphicalHelpMenu(context, settings, tile_manager)
        except Exception as e:
            logging.error(f"Failed to create GraphicalHelpMenu: {e}")
            logging.info("Falling back to standard HelpMenu")
            return HelpMenu()
    else:
        logging.info("Creating standard HelpMenu (glyph mode)")
        return HelpMenu()


class LoreMenu:
    """Data Fragments viewer menu for main menu."""
    
    def __init__(self):
        self.story_fragment_manager = None
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"  # "list" or "reading"
    
    def _load_story_fragments(self):
        """Load story fragment manager from save data."""
        if self.story_fragment_manager is None:
            self.story_fragment_manager = StoryFragmentManager()
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the lore viewer screen."""
        console.clear()
        
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = self.story_fragment_manager.get_fragment_count()
        
        if self.lore_viewer_mode == "reading" and discovered_fragments:
            self._render_reading_mode(console, discovered_fragments)
        else:
            self._render_list_mode(console, discovered_fragments, discovered_count, total_count)
    
    def _render_list_mode(self, console, discovered_fragments, discovered_count, total_count):
        """Render data fragment list."""
        title = f"DISCOVERED DATA FRAGMENTS ({discovered_count}/{total_count})"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)

        if not discovered_fragments:
            render_char_safe(console, 2, 5, "No data fragments discovered yet.", fg=Colors.WHITE)
            render_char_safe(console, 2, 6, "Start playing to discover the story!", fg=Colors.WHITE)
            render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return", fg=Colors.LIGHT_GRAY)
            return

        start_y = 5
        for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
            # Clamp selection
            if self.lore_viewer_selection >= len(discovered_fragments):
                self.lore_viewer_selection = len(discovered_fragments) - 1

            is_selected = (i == self.lore_viewer_selection)
            color = Colors.CYAN if is_selected else Colors.WHITE
            prefix = "> " if is_selected else "  "

            # Show first line of fragment as title
            first_line = fragment_text.split('\n')[0][:60]
            render_char_safe(console, 2, start_y + i, f"{prefix}Fragment {fragment_index + 1}: {first_line}", fg=color)

        # Instructions
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 4, "Up/Down: Navigate  Enter: Read  Esc: Back", fg=Colors.LIGHT_GRAY)
    
    def _render_reading_mode(self, console, discovered_fragments):
        """Render individual fragment for reading."""
        if self.lore_viewer_selection >= len(discovered_fragments):
            self.lore_viewer_mode = "list"
            return

        fragment_index, fragment_text = discovered_fragments[self.lore_viewer_selection]

        title = f"DATA FRAGMENT {fragment_index + 1}"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)

        # Render fragment text with word wrapping utility
        ScreenRenderingUtils.render_word_wrapped_text(
            console, fragment_text, 2, 5,
            max_width=GameConfig.SCREEN_WIDTH - 4,
            max_height=GameConfig.SCREEN_HEIGHT - 4
        )

        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return to list", fg=Colors.LIGHT_GRAY)
    
    def handle_input(self, event) -> str:
        """Handle lore menu input with proper navigation."""
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        
        if not discovered_fragments:
            # No fragments - any key returns to main menu
            if UniversalInputHandler.handle_any_key_screen(event):
                return "back"
            return ""
        
        if self.lore_viewer_mode == "list":
            # Handle navigation using universal handler
            if UniversalInputHandler.handle_list_navigation(
                self, event, len(discovered_fragments), False, self._navigate_lore_selection
            ):
                return ""
            
            # Handle selection
            if UniversalInputHandler.is_confirm_key(event):
                self.lore_viewer_mode = "reading"
                return ""
            elif UniversalInputHandler.is_escape_key(event):
                return "back"
        
        elif self.lore_viewer_mode == "reading":
            # Any key except ESC returns to list
            if UniversalInputHandler.is_escape_key(event):
                return "back"
            else:
                self.lore_viewer_mode = "list"
                return ""
        
        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - update selection based on hover."""
        if self.lore_viewer_mode != "list":
            return False

        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments or not hasattr(event, 'position') or not event.position:
            return False

        # Fragment list starts at Y=5, 1 line per item (rendered with start_y + i)
        start_y = 5
        spacing = 1
        tile_y = int(event.position.y)

        if tile_y >= start_y:
            index = (tile_y - start_y) // spacing
            if 0 <= index < len(discovered_fragments):
                self.lore_viewer_selection = index
                return True

        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - select fragment or navigate."""
        if not hasattr(event, 'position') or not event.position:
            return ""

        if self.lore_viewer_mode == "reading":
            # Click anywhere in reading mode returns to list
            self.lore_viewer_mode = "list"
            return ""
        else:
            # In list mode, update selection and open
            if self.handle_mouse_motion(event):
                # Mouse was over a valid item, open it
                self.lore_viewer_mode = "reading"
            return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - scroll through fragments."""
        if self.lore_viewer_mode != "list":
            return False

        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments:
            return False

        if hasattr(event, 'y'):
            if event.y > 0:
                # Scroll up
                self._navigate_lore_selection(-1)
            elif event.y < 0:
                # Scroll down
                self._navigate_lore_selection(1)
            return True

        return False

    def _navigate_lore_selection(self, direction: int):
        """Navigate lore selection."""
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        if discovered_fragments:
            if direction == -1:
                self.lore_viewer_selection = max(0, self.lore_viewer_selection - 1)
            else:
                self.lore_viewer_selection = min(len(discovered_fragments) - 1, self.lore_viewer_selection + 1)


class HelpMenu:
    """Help menu displaying game information."""
    
    def __init__(self):
        pass
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the help screen."""
        console.clear()

        # Title
        title = "ROGUE SIGNAL PROTOCOL - HELP"
        ScreenRenderingUtils.render_centered_title(console, title, 2, Colors.YELLOW)
        
        y = 5
        help_sections = self._get_help_sections()

        for text, color in help_sections:
            if y < GameConfig.SCREEN_HEIGHT - 2:
                # Special handling for gateway line to color > symbol separately
                if "gateway to advance" in text.lower():
                    # Render text before >
                    render_char_safe(console, 2, y, "  Reach the gateway (", fg=color)
                    # Render > in gateway color
                    render_char_safe(console, 2 + len("  Reach the gateway ("), y, ">", fg=Colors.GATEWAY)
                    # Render text after >
                    render_char_safe(console, 2 + len("  Reach the gateway (>"), y, ") to advance", fg=color)
                else:
                    render_char_safe(console, 2, y, text, fg=color)
                y += 1
        
        # Back instruction
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return", fg=Colors.LIGHT_GRAY)
    
    def handle_input(self, event) -> str:
        """Handle help menu input. Returns 'back' on any key press."""
        if UniversalInputHandler.handle_any_key_screen(event):
            return "back"
        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion."""
        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - click anywhere to return."""
        if hasattr(event, 'position') and event.position:
            return "back"
        return ""

    def _get_help_sections(self):
        """Get help sections with text and colors."""
        # Define enemy state colors for help
        from data_loading import DataLoader
        from game_entities import ensure_color_tuple
        config = DataLoader.load_config()
        enemy_colors = config.get("colors", {}).get("enemies", {})
        ui_colors = config.get("colors", {}).get("ui", {})

        ENEMY_UNAWARE = ensure_color_tuple(enemy_colors.get("unaware_dark", [100, 100, 0]))
        ENEMY_ALERT = ensure_color_tuple(enemy_colors.get("alert_dark", [150, 75, 0]))
        ENEMY_HOSTILE = ensure_color_tuple(enemy_colors.get("hostile_dark", [150, 0, 0]))
        NEON_PINK = ensure_color_tuple(ui_colors.get("neon_pink", [255, 20, 147]))
        
        return [
            ("OBJECTIVE:", Colors.CYAN),
            ("  Navigate network levels using stealth", Colors.WHITE),
            ("  Reach the gateway to advance", Colors.WHITE),  # Will render > separately
            ("  Avoid trace level by enemies and Admin Avatar", Colors.WHITE),
            ("  Collect codes, exploits, and upgrades", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MOVEMENT & CONTROLS:", Colors.CYAN),
            ("  Arrow Keys, WASD, or Numpad: Move/Navigate", Colors.WHITE),
            ("  Mouse: Click adjacent tiles to move, hover/click menus", Colors.WHITE),
            ("  1-5: Use loaded exploits (requires targeting)", Colors.WHITE),
            ("  I: Inventory (manage codes & exploits)", Colors.WHITE),
            ("  L: Look mode (examine map and entities)", Colors.WHITE),
            ("  F: View discovered story fragments", Colors.WHITE),
            ("  ESC: Pause menu / Close screens", Colors.WHITE),
            ("", Colors.WHITE),

            ("MOUSE CONTROLS:", Colors.CYAN),
            ("  Left Click: Move (adjacent tiles), select/activate options", Colors.WHITE),
            ("  Right Click: Cancel/exit current mode", Colors.WHITE),
            ("  Hover: Update cursor position in look/targeting modes", Colors.WHITE),
            ("  Scroll Wheel: Navigate lists (inventory, lore, etc.)", Colors.WHITE),
            ("", Colors.WHITE),

            ("LOOK MODE:", Colors.CYAN),
            ("  L or ESC: Exit look mode", Colors.WHITE),
            ("  Arrow Keys, WASD, Numpad, or Mouse: Move cursor", Colors.WHITE),
            ("  Inspect enemies, items, terrain, and nodes", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MAP SYMBOLS:", Colors.CYAN),
            ("  ☺: Player (you)", Colors.WHITE),
            ("  •: Empty floor (passable)", Colors.FLOOR),
            ("  ╔╗╚╝╦╩╠╣╬═║: Walls (impassable)", Colors.WALL),
            ("  ◘: Shadows (stealth zones)", Colors.ELECTRIC_PURPLE),
            ("  >: Gateway to next level", Colors.GATEWAY),
            ("  ♫: Data fragments (story/lore)", Colors.CYAN),
            ("", Colors.WHITE),
            
            ("ENEMY TYPES (HP, Vision, Behavior, Damage):", Colors.CYAN),
            ("  S: Scanner (35hp, 4 vision, static, no attack)", ENEMY_UNAWARE),
            ("  P: Patrol (40hp, 4 vision, linear routes, 15 dmg)", ENEMY_UNAWARE),
            ("  B: Bot (25hp, 3 vision, random movement, 8 dmg)", ENEMY_UNAWARE),
            ("  F: Firewall (80hp, 5 vision, static, no attack)", ENEMY_ALERT),
            ("  H: Hunter (50hp, 6 vision, seeks players, 22 dmg)", ENEMY_HOSTILE),
            ("  V: Virus (35hp, 4 vision, seeks players, virus attack)", ENEMY_HOSTILE),
            ("  I: Inhibitor (30hp, 4 vision, random, slows movement)", ENEMY_UNAWARE),
            ("  A: Admin Avatar (250hp, 8 vision, perfect tracking, 45 dmg)", ENEMY_HOSTILE),
            ("", Colors.WHITE),
            
            ("ITEMS & PICKUPS:", Colors.CYAN),
            ("  §: Code Patches (grant random bonuses, restore stats)", Colors.ELECTRIC_PURPLE),
            ("  &: Exploits (combat & utility abilities)", NEON_PINK),
            ("  ○: Permanent upgrades (Memory/CPU/Heat)", Colors.ELECTRIC_BLUE),
            ("  ♥: CPU recovery nodes (restore health)", Colors.RED),
            ("  ♦: Cooling nodes (reduce heat)", Colors.CYAN),
            ("  ♠: Ghost nodes (reduce trace level)", Colors.ELECTRIC_PURPLE),
            ("", Colors.WHITE),
            
            ("CORE MECHANICS:", Colors.CYAN),
            ("  Heat: Builds from exploit usage, causes damage at 100°C+", Colors.WHITE),
            ("  Trace Level: Increases when spotted, Admin spawns at threshold", Colors.WHITE),
            ("  CPU: Your health - if it reaches 0, you die permanently", Colors.WHITE),
            ("  RAM: Limits how many exploits you can equip (max 5)", Colors.WHITE),
            ("  Shadows: Hide in purple * tiles to avoid enemy trace level", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("COMBAT EXPLOITS:", Colors.CYAN),
            ("  Buffer Overflow: 40 dmg melee (1 tile range)", Colors.WHITE),
            ("  Code Injection: 25 dmg ranged (5 tile range)", Colors.WHITE),
            ("  System Crash: 30 dmg area (disables enemies 4 turns)", Colors.WHITE),
            ("  EMP Burst: 20 dmg area (disables all nearby enemies)", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("STEALTH & UTILITY EXPLOITS:", Colors.CYAN),
            ("  Shadow Step: Teleport to shadow zones (6 tile range)", Colors.WHITE),
            ("  Data Mimic: Become invisible (5 turns)", Colors.WHITE),
            ("  Noise Maker: Create distraction (8 turn duration)", Colors.WHITE),
            ("  Network Scan: Reveal all cooling, CPU, and ghost nodes", Colors.WHITE),
            ("  Log Wiper: Reduce trace level (-30%)", Colors.WHITE),
            ("  Antivirus: Purges negative status effects (virus, slow)", Colors.WHITE),
            ("  Memory Leak: 3x3 area makes enemies forget player location", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("STATUS EFFECTS:", Colors.CYAN),
            ("  Virus: 3 CPU damage per turn, cured with Antivirus", Colors.WHITE),
            ("  Virus attacks stack virus duration (max 12 turns)", Colors.WHITE),
            ("  Movement Slowed: Can only move every other turn", Colors.WHITE),
            ("  Speed Boost and Movement Slow offset each other turn-for-turn", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("SURVIVAL TIPS:", Colors.CYAN),
            ("  Use shadows frequently - stealth is key", Colors.WHITE),
            ("  Monitor heat and trace levels constantly", Colors.WHITE),
            ("  Plan exploit usage - heat management is critical", Colors.WHITE),
            ("  Use CPU nodes when low on health", Colors.WHITE),
            ("  Use Ghost nodes to reduce trace level continuously", Colors.WHITE),
            ("  Admin Avatar spawns at high trace level - be careful!", Colors.WHITE),
            ("  Virus enemies apply virus damage - keep Antivirus exploit handy!", Colors.WHITE),
            ("  Inhibitor enemies add 1 slow turn that offsets speed boosts!", Colors.WHITE),
            ("  Save cooling nodes for emergencies", Colors.WHITE),
        ]