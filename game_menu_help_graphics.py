#!/usr/bin/env python3
"""
Rogue Signal Protocol - Graphical Help Menu

Graphics-mode help screen with sprite visualization and paginated layout.
Displays enemy sprites, item sprites alongside descriptions using SDL rendering.
Uses same sprite scale as in-game for consistency. Supports page navigation.
"""

import tcod
import logging
from typing import List, Tuple, Optional

from game_config import GameConfig, GameBalance
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe
from game_input import UniversalInputHandler
from data_loading import DataLoader
from game_color_manager import ColorManager
from game_coordinate_helpers import CoordinateHelpers


class GraphicalHelpMenu:
    """
    Graphics-mode help menu displaying enemy sprites and item sprites
    alongside descriptive text in a paginated layout.

    Uses the same sprite scale as the game renderer for consistency.
    Renders sprites via SDL layer, text via console overlay with transparency.
    """

    def __init__(self, context, settings, tile_manager):
        """
        Initialize graphical help menu.

        Args:
            context: TCOD context with SDL renderer access
            settings: GameSettings instance
            tile_manager: TileManager instance (must be pre-initialized)
        """
        self.context = context
        self.settings = settings
        self.tile_manager = tile_manager

        if self.tile_manager is None:
            raise ValueError("GraphicalHelpMenu requires a valid TileManager instance")

        # Current page
        self.current_page = 0

        # Load colors from config
        self._load_colors()

        # Build pages (deferred until first render to ensure data loaded)
        self.pages = []
        self.pages_built = False

    def _load_colors(self):
        """Load enemy and UI colors from game config."""
        # Use base colors (help screen doesn't need darkened variants)
        self.ENEMY_UNAWARE = ColorManager.get_enemy_state_color("unaware")
        self.ENEMY_ALERT = ColorManager.get_enemy_state_color("alert")
        self.ENEMY_HOSTILE = ColorManager.get_enemy_state_color("hostile")
        self.NEON_PINK = Colors.NEON_PINK

    def _build_pages(self):
        """Build all help pages with content."""
        if self.pages_built:
            return

        # 3 pages total: Items/Map, Enemies, Controls/Mechanics
        self.pages = [
            self._build_page_items_and_map(),    # Page 1: Items + map symbols (with sprites!)
            self._build_page_enemies(),          # Page 2: ALL 8 enemies (2 columns)
            self._build_page_controls_mechanics(), # Page 3: Controls + mechanics (multi-column text)
        ]

        self.pages_built = True

    def _build_page_enemies(self) -> dict:
        """Page 2: All 8 enemies - better vertical spacing."""
        return {
            'title': 'ENEMY TYPES (Page 2/3)',
            'sprites': [
                # Blank line after title, then sprites
                # Left column
                ('Scanner', 4, 6, 1.0),
                ('Patrol', 4, 13, 1.0),
                ('Bot', 4, 20, 1.0),
                ('Firewall', 4, 27, 1.0),
                # Right column
                ('Hunter', 45, 6, 1.0),
                ('Virus', 45, 13, 1.0),
                ('Inhibitor', 45, 20, 1.0),
                ('Admin Avatar', 45, 27, 1.0),
            ],
            'text_lines': [
                # Blank line after title

                # Left column - 3 lines each
                (6, 6, "Scanner (S)", self.ENEMY_UNAWARE),
                (6, 7, "HP:35 Vis:5 Dmg:None", Colors.LIGHT_GRAY),
                (6, 8, "Static, alerts others", Colors.LIGHT_GRAY),

                (6, 13, "Patrol (P)", self.ENEMY_UNAWARE),
                (6, 14, "HP:40 Vis:4 Dmg:10", Colors.LIGHT_GRAY),
                (6, 15, "Follows patrol routes", Colors.LIGHT_GRAY),

                (6, 20, "Bot (B)", self.ENEMY_UNAWARE),
                (6, 21, "HP:25 Vis:3 Dmg:8", Colors.LIGHT_GRAY),
                (6, 22, "Random movement", Colors.LIGHT_GRAY),

                (6, 27, "Firewall (F)", self.ENEMY_ALERT),
                (6, 28, "HP:80 Vis:3 Dmg:5", Colors.LIGHT_GRAY),
                (6, 29, "Defensive wall", Colors.LIGHT_GRAY),

                # Right column - 3 lines each
                (47, 6, "Hunter (H)", self.ENEMY_HOSTILE),
                (47, 7, "HP:50 Vis:6 Dmg:15", Colors.LIGHT_GRAY),
                (47, 8, "Actively seeks player", Colors.LIGHT_GRAY),

                (47, 13, "Virus (V)", self.ENEMY_HOSTILE),
                (47, 14, "HP:35 Vis:4 Dmg:Virus", Colors.LIGHT_GRAY),
                (47, 15, "3CPU/turn DoT", Colors.LIGHT_GRAY),

                (47, 20, "Inhibitor (I)", self.ENEMY_UNAWARE),
                (47, 21, "HP:30 Vis:4 Dmg:Slow", Colors.LIGHT_GRAY),
                (47, 22, "Move every 2nd turn", Colors.LIGHT_GRAY),

                (47, 27, "Admin Avatar (A)", self.ENEMY_HOSTILE),
                (47, 28, "HP:250 Vis:8 Dmg:45", Colors.RED),
                (47, 29, "EXTREME DANGER!", Colors.RED),

                # Footer - centered
                (15, 37, "COLORS: Yellow=Unaware  Orange=Alert  Red=Hostile", Colors.CYAN),
                (13, 39, "Enemies alert nearby allies when they spot you!", Colors.YELLOW),
                (12, 41, "Use blind spots (♠) to hide and watch patrol patterns!", Colors.ELECTRIC_PURPLE),
            ]
        }

    def _build_page_items_and_map(self) -> dict:
        """Page 1: Map symbols at top, then collectibles, nodes, upgrades."""
        return {
            'title': 'ITEMS & MAP SYMBOLS (Page 1/3)',
            'sprites': [
                # Row 1 - Map symbols (5 columns) - shifted right for better centering
                ('player', 5, 6, 1.0),
                ('floor', 19, 6, 1.0),
                ('wall', 33, 6, 1.0),
                ('blind_spot', 47, 6, 1.0),
                ('gateway', 61, 6, 1.0),
                # Row 2 - Collectibles (3 centered)
                ('codehack', 19, 13, 1.0),
                ('exploit', 33, 13, 1.0),
                ('story_fragment', 47, 13, 1.0),
                # Row 3 - Resource Nodes (3 centered)
                ('cpu_node', 19, 20, 1.0),
                ('cooling_node', 33, 20, 1.0),
                ('ghost_node', 47, 20, 1.0),
                # Row 4 - Upgrades (3 centered)
                ('cpu_upgrade', 19, 27, 1.0),
                ('ram_upgrade', 33, 27, 1.0),
                ('cooling_upgrade', 47, 27, 1.0),
            ],
            'text_lines': [
                # Blank line after title

                # Row 1 - Map symbols
                (7, 6, "Player", Colors.WHITE),
                (7, 7, "You!", Colors.LIGHT_GRAY),

                (21, 6, "Floor", Colors.LIGHT_GRAY),
                (21, 7, "Walk", Colors.LIGHT_GRAY),

                (35, 6, "Wall", Colors.WHITE),
                (35, 7, "Blocks", Colors.LIGHT_GRAY),

                (49, 6, "Blind Spot", Colors.ELECTRIC_PURPLE),
                (49, 7, "HIDE!", Colors.YELLOW),

                (63, 6, "Gateway", Colors.CYAN),
                (63, 7, "Exit!", Colors.LIGHT_GRAY),

                # Row 2 - Collectibles
                (21, 13, "CodePatch", Colors.ELECTRIC_PURPLE),
                (21, 14, "Random buff", Colors.LIGHT_GRAY),

                (35, 13, "Exploit", self.NEON_PINK),
                (35, 14, "Combat/Util", Colors.LIGHT_GRAY),

                (49, 13, "Story Fragment", Colors.CYAN),
                (49, 14, "Lore", Colors.LIGHT_GRAY),

                # Row 3 - Resource Nodes
                (21, 20, "CPU Node", Colors.RED),
                (21, 21, "Full HP", Colors.LIGHT_GRAY),

                (35, 20, "Cool Node", Colors.CYAN),
                (35, 21, "-50C heat", Colors.LIGHT_GRAY),

                (49, 20, "Ghost Node", Colors.ELECTRIC_PURPLE),
                (49, 21, "-30% trace", Colors.LIGHT_GRAY),

                # Row 4 - Upgrades
                (21, 27, "CPU Upgrade", Colors.ELECTRIC_BLUE),
                (21, 28, "PERMANENT", Colors.YELLOW),

                (35, 27, "RAM Upgrade", Colors.ELECTRIC_BLUE),
                (35, 28, "PERMANENT", Colors.YELLOW),

                (49, 27, "Cool Upgrade", Colors.ELECTRIC_BLUE),
                (49, 28, "PERMANENT", Colors.YELLOW),

                # Bottom info - centered
                (9, 35, "UPGRADES: Permanent stat increases - keep across ALL levels", Colors.CYAN),
                (13, 37, "RESOURCE NODES: CPU=Health  Cooling=Heat  Ghost=Trace", Colors.CYAN),
                (13, 39, "STEALTH: Hide in blind spots (♠) to avoid enemy detection!", Colors.ELECTRIC_PURPLE),
            ]
        }

    def _build_page_controls_mechanics(self) -> dict:
        """Page 3: 2-column layout with full-width tips at bottom."""
        return {
            'title': 'CONTROLS & MECHANICS (Page 3/3)',
            'sprites': [],  # Text-only page
            'text_lines': [
                # Blank line after title

                # Left column - Controls & Objective
                (5, 5, "CONTROLS:", Colors.CYAN),
                (5, 6, "Move: ↑↓←→/WASD/QEZC/Numpad", Colors.WHITE),
                (5, 7, "1-5: Use exploits", Colors.WHITE),
                (5, 8, "I: Inventory", Colors.WHITE),
                (5, 9, "L: Look mode", Colors.WHITE),
                (5, 10, "F: Story fragments", Colors.WHITE),
                (5, 11, "V: Achievements", Colors.WHITE),
                (5, 12, "?: Help  ESC: Menu", Colors.WHITE),
                (5, 13, "Shift+F12: Export debug pkg", Colors.WHITE),

                (5, 15, "OBJECTIVE:", Colors.CYAN),
                (5, 16, "Reach gateway to advance", Colors.WHITE),
                (5, 17, "Avoid trace/detection", Colors.YELLOW),
                (5, 18, "Death = Save deleted!", Colors.RED),

                (5, 20, "HEAT:", Colors.CYAN),
                (5, 21, "Builds from exploits", Colors.WHITE),
                (5, 22, "Damage at 100C+", Colors.RED),
                (5, 23, "Use cooling nodes", Colors.LIGHT_GRAY),

                (5, 25, "TRACE:", Colors.CYAN),
                (5, 26, "Rises when spotted", Colors.WHITE),
                (5, 27, "Admin spawns @ max", Colors.RED),
                (5, 28, "Ghost nodes reduce", Colors.LIGHT_GRAY),

                # Right column - Exploits & Shadows
                (45, 5, "COMBAT EXPLOITS:", Colors.CYAN),
                (45, 6, "BufferOverflow: 40dmg melee", self.NEON_PINK),
                (45, 7, "CodeInject: 25dmg 5range", self.NEON_PINK),
                (45, 8, "LogicBomb: 15dmg area", self.NEON_PINK),
                (45, 9, "DenialOfService: Disable", self.NEON_PINK),

                (45, 11, "UTILITY/STEALTH:", Colors.CYAN),
                (45, 12, "SystemHop: Teleport", self.NEON_PINK),
                (45, 13, "TrafficMasq: Invisible", self.NEON_PINK),
                (45, 14, "DecoySwarm: Distract", self.NEON_PINK),
                (45, 15, "ThreatScan: See enemies", self.NEON_PINK),
                (45, 16, "NetworkScan: See nodes", self.NEON_PINK),
                (45, 17, "LogWiper/Antivirus/Leak", self.NEON_PINK),

                (45, 19, "BLIND SPOTS (♠):", Colors.CYAN),
                (45, 20, "Hide from enemies", Colors.ELECTRIC_PURPLE),
                (45, 21, "+10 damage bonus!", Colors.YELLOW),

                (45, 23, "RAM:", Colors.CYAN),
                (45, 24, "Limits exploit slots", Colors.WHITE),
                (45, 25, "Max 5 equipped", Colors.LIGHT_GRAY),

                # Full-width tips at bottom - centered, non-bulleted
                (30, 31, "SURVIVAL TIPS:", Colors.YELLOW),
                (8, 33, "Attacking from blind spots gives +10 damage bonus to all attacks!", Colors.WHITE),
                (11, 34, "Move between attacks! Attacking from same spot adds +1 heat", Colors.YELLOW),
                (6, 36, "Watch your trace level to avoid the Admin Avatar and use ghost nodes", Colors.RED),
                (18, 37, "or log wiper to reduce your trace level", Colors.RED),
                (8, 39, "If you overheat, you take CPU damage but can still use exploits", Colors.CYAN),
            ]
        }

    def render(self, console: tcod.console.Console) -> None:
        """
        Render the current help page.

        IMPORTANT: This method only renders to the console.
        The SDL sprite rendering is done separately in render_sprites() method.
        The calling code (game_loop.py) will handle compositing:
        1. Clear SDL renderer
        2. Call render_sprites() to render sprites to SDL
        3. Call render() to render text to console
        4. Convert console to texture and composite over sprites
        5. Present

        This method renders text with transparency zones for sprites.
        """
        # Build pages on first render
        self._build_pages()

        if not self.pages or self.current_page >= len(self.pages):
            logging.error(f"Invalid page state: current={self.current_page}, total={len(self.pages)}")
            return

        # Get current page data
        page = self.pages[self.current_page]

        # Render text layer (Console with transparency)
        self._render_text_layer(console, page)

    def render_sprites(self):
        """
        Render sprites directly to SDL renderer.
        Must be called BEFORE render() to ensure sprites appear behind text.
        Only called when in graphics mode.
        """
        # Build pages on first render
        self._build_pages()

        if not self.pages or self.current_page >= len(self.pages):
            logging.warning(f"No pages built or invalid page index: {self.current_page}/{len(self.pages)}")
            return

        # Get current page data
        page = self.pages[self.current_page]

        # Render sprite layer (SDL)
        self._render_sprite_layer(page)

    def _render_sprite_layer(self, page: dict):
        """Render sprites directly to SDL renderer."""
        if not hasattr(self.context, 'sdl_renderer'):
            logging.warning("SDL renderer not available for sprite rendering")
            return

        renderer = self.context.sdl_renderer
        if renderer is None:
            logging.warning("SDL renderer is None, cannot render sprites")
            return

        # Note: Don't clear renderer here - caller should handle that
        # We only render our sprites

        sprite_count = len(page.get('sprites', []))
        logging.debug(f"Rendering {sprite_count} sprites for page '{page.get('title', 'Unknown')}'")

        for sprite_data in page.get('sprites', []):
            sprite_name, console_x, console_y, scale = sprite_data
            self._render_sprite(renderer, sprite_name, console_x, console_y, scale)

    def _render_sprite(self, renderer, sprite_name: str, console_x: int, console_y: int, scale: float):
        """
        Render a single sprite at the specified console position.

        Args:
            renderer: SDL renderer
            sprite_name: Name of sprite to render (from tile mappings)
            console_x: X position in console grid
            console_y: Y position in console grid
            scale: Scale multiplier (1.0 = normal game scale)
        """
        # Get texture from tile manager
        texture = self.tile_manager.get_tile(sprite_name)

        if texture is None:
            # Fail hard - no fallback
            raise RuntimeError(f"Failed to load sprite '{sprite_name}' for graphical help")

        # Calculate pixel rect for sprite
        tile_rect = self._get_tile_rect(console_x, console_y, scale)

        logging.debug(f"Rendering sprite '{sprite_name}' at console ({console_x},{console_y}) -> pixel rect {tile_rect}")

        # Render sprite
        renderer.copy(texture, dest=tile_rect)

    def _get_tile_rect(self, console_x: int, console_y: int, scale: float = 1.0):
        """
        Calculate pixel rectangle for a sprite at console position.

        CRITICAL: Sprites must be the SAME SIZE as in-game (tile_width x tile_height).
        The console is scaled to fit the window, so we calculate pixels per character
        based on window size divided by console size.

        Args:
            console_x: Console grid X coordinate (0-79 for 80-wide console)
            console_y: Console grid Y coordinate (0-49 for 50-tall console)
            scale: Scale multiplier for sprite size (usually 1.0)

        Returns:
            Tuple of (x, y, width, height) in pixels for SDL rendering
        """
        # Calculate positioning using window scaling (console coords -> pixels)
        pixel_x, pixel_y = self._console_to_pixels(console_x, console_y)

        # Use TileManager for size (same as in-game for consistency)
        sprite_width = int(self.tile_manager.tile_width * scale)
        sprite_height = int(self.tile_manager.tile_height * scale)

        return (pixel_x, pixel_y, sprite_width, sprite_height)

    def _console_to_pixels(self, console_x: int, console_y: int) -> Tuple[int, int]:
        """
        Convert console coordinates to pixel coordinates for menu sprite positioning.

        Args:
            console_x: Console X coordinate (0-79)
            console_y: Console Y coordinate (0-49)

        Returns:
            Tuple of (pixel_x, pixel_y)
        """
        # Get window size from SDL
        try:
            if hasattr(self.context, 'sdl_window') and self.context.sdl_window:
                window_width, window_height = self.context.sdl_window.size
            else:
                window_width, window_height = 800, 600
        except (AttributeError, TypeError):
            window_width, window_height = 800, 600

        # Use CoordinateHelpers for consistent coordinate conversion
        return CoordinateHelpers.char_to_pixel_coords(
            console_x, console_y, window_width, window_height
        )

    def _render_text_layer(self, console: tcod.console.Console, page: dict):
        """
        Render text overlay with transparency for sprite areas.

        Args:
            console: Console to render to
            page: Page data dictionary
        """
        # Clear console
        console.clear()

        # Make ENTIRE console transparent first (like the game does for the game area)
        # This allows ALL sprites to show through
        # Use CoordinateHelpers to handle transparency correctly across all console orders
        CoordinateHelpers.set_alpha_region(
            console, x=0, y=0, width=console.width, height=console.height, alpha=0
        )

        # Now render text - text areas will become opaque automatically
        # Render title
        title = page.get('title', 'HELP')
        title_x = GameConfig.SCREEN_WIDTH // 2 - len(title) // 2
        render_char_safe(console, title_x, 2, title, fg=Colors.YELLOW, bg=Colors.BLACK)

        # Render page indicator
        page_indicator = f"Page {self.current_page + 1}/{len(self.pages)}"
        indicator_x = GameConfig.SCREEN_WIDTH - len(page_indicator) - 2
        render_char_safe(console, indicator_x, 2, page_indicator, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)

        # Render text lines
        for text_data in page.get('text_lines', []):
            x, y, text, color = text_data
            render_char_safe(console, x, y, text, fg=color, bg=Colors.BLACK)

        # Render navigation help at bottom
        nav_text = "←→: Change Page  │  ESC: Back"
        nav_x = GameConfig.SCREEN_WIDTH // 2 - len(nav_text) // 2
        render_char_safe(console, nav_x, GameConfig.SCREEN_HEIGHT - 2, nav_text, fg=Colors.CYAN, bg=Colors.BLACK)


    def handle_input(self, event) -> str:
        """
        Handle input for graphical help menu.

        Args:
            event: TCOD event

        Returns:
            'back' to exit, '' to continue
        """
        # Handle page navigation keys
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.KeySym.LEFT or event.sym == tcod.event.KeySym.UP:
                self._previous_page()
                return ""  # Stay in help
            elif event.sym == tcod.event.KeySym.RIGHT or event.sym == tcod.event.KeySym.DOWN:
                self._next_page()
                return ""  # Stay in help
            elif UniversalInputHandler.is_escape_key(event):
                return "back"

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion - hover zones for page navigation."""
        # Could add visual feedback for hover zones in the future
        return False

    def handle_mouse_click(self, event) -> str:
        """
        Handle mouse click - click left/right zones to navigate pages.

        Left third of screen: previous page
        Right third of screen: next page
        """
        if not hasattr(event, 'position') or not event.position:
            return ""

        from game_config import GameConfig

        # Divide screen into thirds
        left_zone = GameConfig.SCREEN_WIDTH // 3
        right_zone = GameConfig.SCREEN_WIDTH * 2 // 3

        if event.position.x < left_zone:
            # Left zone - previous page
            self._previous_page()
        elif event.position.x > right_zone:
            # Right zone - next page
            self._next_page()
        else:
            # Middle zone - close help menu
            return "back"

        return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - scroll pages."""
        if hasattr(event, 'y'):
            if event.y > 0:
                # Scroll up = previous page
                self._previous_page()
            elif event.y < 0:
                # Scroll down = next page
                self._next_page()
            return True
        return False

    def _previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            logging.debug(f"Help page: {self.current_page + 1}/{len(self.pages)}")

    def _next_page(self):
        """Navigate to next page."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            logging.debug(f"Help page: {self.current_page + 1}/{len(self.pages)}")
