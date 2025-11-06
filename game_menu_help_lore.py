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
            render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "ESC: Back", fg=Colors.CYAN)
            return

        start_y = 5
        for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
            # Clamp selection
            if self.lore_viewer_selection >= len(discovered_fragments):
                self.lore_viewer_selection = len(discovered_fragments) - 1

            is_selected = (i == self.lore_viewer_selection)
            color = Colors.CYAN if is_selected else Colors.WHITE
            prefix = "▶ " if is_selected else "  "

            # Show first line of fragment as title
            first_line = fragment_text.split('\n')[0][:60]
            render_char_safe(console, 2, start_y + i, f"{prefix}Fragment {fragment_index + 1}: {first_line}", fg=color)

        # Instructions
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 4, "↕: Navigate │ Enter: Read │ ESC: Back", fg=Colors.LIGHT_GRAY)
    
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

        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "ESC: Back to list  │  Any other key: Close", fg=Colors.CYAN)
    
    def handle_input(self, event) -> str:
        """Handle lore menu input with proper navigation."""
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()

        if not discovered_fragments:
            # No fragments - ESC returns to main menu
            if UniversalInputHandler.is_escape_key(event):
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
            # ESC returns to list, any other key closes completely
            if UniversalInputHandler.is_escape_key(event):
                self.lore_viewer_mode = "list"
                return ""
            elif UniversalInputHandler.handle_any_key_screen(event):
                return "back"

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
        self.current_page = 0  # 0 = page 1, 1 = page 2
        self.total_pages = 2
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the help screen."""
        console.clear()

        # Title with page indicator
        title = f"ROGUE SIGNAL PROTOCOL - HELP (Page {self.current_page + 1}/{self.total_pages})"
        ScreenRenderingUtils.render_centered_title(console, title, 1, Colors.YELLOW)

        y = 3
        help_sections = self._get_help_sections()

        for text, color in help_sections:
            if y < GameConfig.SCREEN_HEIGHT - 4:  # Leave room for page controls
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

        # Page navigation and back instruction
        nav_text = "← →/PgUp/PgDn: Change page │ ESC: Back"
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, nav_text, fg=Colors.CYAN)
    
    def handle_input(self, event) -> str:
        """Handle help menu input with page navigation. Returns 'back' on ESC."""
        # Check for escape key
        if UniversalInputHandler.is_escape_key(event):
            return "back"

        # Check for page navigation keys
        if event.type == "KEYDOWN":
            if event.sym in (tcod.event.KeySym.LEFT, tcod.event.KeySym.PAGEUP):
                self._navigate_page(-1)
            elif event.sym in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.PAGEDOWN):
                self._navigate_page(1)

        return ""

    def _navigate_page(self, direction: int):
        """Navigate between help pages."""
        self.current_page = (self.current_page + direction) % self.total_pages

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion."""
        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse click - click anywhere to return."""
        if hasattr(event, 'position') and event.position:
            return "back"
        return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - navigate pages."""
        if hasattr(event, 'y'):
            if event.y > 0:
                # Scroll up (go to previous page)
                self._navigate_page(-1)
            elif event.y < 0:
                # Scroll down (go to next page)
                self._navigate_page(1)
            return True
        return False

    def _get_help_sections(self):
        """Get help sections with text and colors based on current page."""
        # Define enemy state colors for help
        from data_loading import DataLoader
        from game_entities import ensure_color_tuple
        config = DataLoader.load_config()
        enemy_colors = config.get("colors", {}).get("enemies", {})
        ui_colors = config.get("colors", {}).get("ui", {})

        # Use base colors (help screen doesn't need darkened variants)
        ENEMY_UNAWARE = ensure_color_tuple(enemy_colors.get("unaware", [255, 255, 0]))
        ENEMY_ALERT = ensure_color_tuple(enemy_colors.get("alert", [255, 165, 0]))
        ENEMY_HOSTILE = ensure_color_tuple(enemy_colors.get("hostile", [220, 20, 60]))
        NEON_PINK = Colors.NEON_PINK

        if self.current_page == 0:
            # Page 1: Basics, Map, Enemies, Items
            return [
                ("OBJECTIVE:", Colors.CYAN),
                ("  Navigate levels stealthily, reach gateway (>), avoid trace", Colors.WHITE),
                ("  Collect codes, exploits, and upgrades", Colors.WHITE),
                ("", Colors.WHITE),

                ("CONTROLS:", Colors.CYAN),
                ("  ↑↓←→/WASD/Numpad: Move  Mouse: Click/hover  1-5: Exploits", Colors.WHITE),
                ("  I: Inventory  L: Look mode  F: Lore  V: Achievements  ESC: Menu", Colors.WHITE),
                ("  Mouse: L-Click=move/select, R-Click=cancel, Scroll=lists", Colors.WHITE),
                ("", Colors.WHITE),

                ("MAP SYMBOLS:", Colors.CYAN),
                ("  ☺  Player (you)", Colors.WHITE),
                ("  •  Empty floor (passable)", Colors.FLOOR),
                ("  ╔╗╚╝╦╩╠╣╬═║  Walls (impassable)", Colors.WALL),
                ("  ◘  Blind Spots (stealth zones)", Colors.ELECTRIC_PURPLE),
                ("  >  Gateway to next level", Colors.GATEWAY),
                ("  ♫  Data fragments (story/lore)", Colors.CYAN),
                ("", Colors.WHITE),

                ("ENEMY TYPES (HP, Vision, Behavior, Damage):", Colors.CYAN),
                ("  S: Scanner (35hp/5vis/static/none) P: Patrol (40hp/4vis/10dmg)", ENEMY_UNAWARE),
                ("  B: Bot (25hp/3vis/8dmg) F: Firewall (80hp/3vis/5dmg)", ENEMY_UNAWARE),
                ("  H: Hunter (50hp/6vis/15dmg) V: Virus (35hp/4vis/virus)", ENEMY_HOSTILE),
                ("  I: Inhibitor (30hp/4vis/slow) A: Admin (250hp/8vis/45dmg)", ENEMY_HOSTILE),
                ("", Colors.WHITE),

                ("ITEMS & PICKUPS:", Colors.CYAN),
                ("  §: Code Patches (bonuses)  &: Exploits  ○: Upgrades", Colors.WHITE),
                ("  ♥: CPU nodes  ♦: Cooling nodes  ♠: Ghost nodes", Colors.WHITE),
            ]
        else:
            # Page 2: Mechanics, Exploits, Status Effects, Tips
            return [
                ("CORE MECHANICS:", Colors.CYAN),
                ("  CPU: Health (0=death)  Heat: Exploit cost (100°C=dmg)", Colors.WHITE),
                ("  Trace: Increases when spotted (Admin spawns at threshold)", Colors.WHITE),
                ("  RAM: Exploit limit (max 5)  Blind Spots: Stealth (+10 dmg)", Colors.WHITE),
                ("", Colors.WHITE),

                ("EXPLOITS - COMBAT:", Colors.CYAN),
                ("  Buffer Overflow (40dmg/melee)  Code Injection (25dmg/range)", Colors.WHITE),
                ("  Logic Bomb (15dmg/area)  Denial of Service (disable)", Colors.WHITE),
                ("", Colors.WHITE),

                ("EXPLOITS - UTILITY/STEALTH:", Colors.CYAN),
                ("  System Hop (teleport)  Traffic Masq (invisible)  Decoy (distract)", Colors.WHITE),
                ("  Network Scan (nodes)  Threat Scan (enemies)  Log Wiper (trace)", Colors.WHITE),
                ("  Antivirus (cure)  Memory Leak (blind)  System Crash (emergency)", Colors.WHITE),
                ("", Colors.WHITE),

                ("STATUS EFFECTS:", Colors.CYAN),
                ("  Virus: 3 CPU dmg/turn (stacks to 12t, cure with Antivirus)", Colors.WHITE),
                ("  Slowed: Move every other turn (offsets speed boosts)", Colors.WHITE),
                ("", Colors.WHITE),

                ("TIPS:", Colors.CYAN),
                ("  Use blind spots for stealth (+10 dmg bonus)", Colors.WHITE),
                ("  Enemies only detect you in blind spots when adjacent", Colors.WHITE),
                ("  Monitor heat/trace levels - Admin spawns at high trace!", Colors.WHITE),
                ("  Plan exploit usage carefully - heat management is critical", Colors.WHITE),
                ("  Use CPU/Ghost nodes often - save cooling for emergencies", Colors.WHITE),
            ]