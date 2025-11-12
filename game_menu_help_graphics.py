#!/usr/bin/env python3
"""
Rogue Signal Protocol - Graphical Help Menu

Graphics-mode help screen with sprite visualization and paginated layout.
Displays enemy sprites, item sprites alongside descriptions using SDL rendering.
Uses same sprite scale as in-game for consistency. Supports page navigation.
"""

import tcod
import logging
import textwrap
from typing import List, Tuple, Optional

from game_config import GameConfig, GameBalance
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe, UniversalInputHandler
from data_loading import DataLoader
from game_color_manager import ColorManager
from game_coordinate_helpers import CoordinateHelpers
from game_screen_utilities import ScreenRenderingUtils
from game_help_content import HelpContent


class GraphicalHelpMenu:
    """
    Refactored graphics-mode help menu using centralized content.

    Uses HelpContent for all data and Screen Rendering Utils for layout calculations.
    Renders sprites via SDL layer, text via console overlay with transparency.
    """

    def __init__(self, context, settings, tile_manager):
        """Initialize graphical help menu."""
        self.context = context
        self.settings = settings
        self.tile_manager = tile_manager

        if self.tile_manager is None:
            raise ValueError("GraphicalHelpMenu requires a valid TileManager instance")

        self.current_page = 0
        self._load_colors()
        self.pages = []
        self.pages_built = False

    def _load_colors(self):
        """Load enemy and UI colors from game config."""
        self.ENEMY_UNAWARE = ColorManager.get_enemy_state_color("unaware")
        self.ENEMY_ALERT = ColorManager.get_enemy_state_color("alert")
        self.ENEMY_HOSTILE = ColorManager.get_enemy_state_color("hostile")
        self.NEON_PINK = Colors.NEON_PINK

    def _build_pages(self):
        """Build all help pages with content."""
        if self.pages_built:
            return

        self.pages = [
            self._build_page_1(),  # Objectives & Mechanics
            self._build_page_2(),  # Items & Enemies
            self._build_page_3(),  # Exploits & Status Effects
        ]

        self.pages_built = True

    def _build_page_1(self) -> dict:
        """Page 1/3: MAP SYMBOLS, Objectives, Mechanics, Controls with sprites."""
        utils = ScreenRenderingUtils

        text_lines = []

        # Start with MAP SYMBOLS at top
        y = 4  # Start at y=4 to add blank line above
        heading = "MAP SYMBOLS:"
        text_lines.append((utils.center_x(heading), y, heading, Colors.CYAN))

        # Row 1 labels (2 lines down from heading, sprites 2 lines after that)
        # Sprite columns at x=21, 40, 59 (middle column centered at screen center)
        row1_label_y = y + 2
        text_lines.append((18, row1_label_y, "Player", Colors.WHITE))
        text_lines.append((19, row1_label_y + 1, "(you)", Colors.LIGHT_GRAY))

        text_lines.append((38, row1_label_y, "Floor", Colors.LIGHT_GRAY))
        text_lines.append((36, row1_label_y + 1, "Walkable", Colors.LIGHT_GRAY))

        text_lines.append((57, row1_label_y, "Wall", Colors.WHITE))
        text_lines.append((55, row1_label_y + 1, "Blocking", Colors.LIGHT_GRAY))

        # Row 2 labels (8 lines down from row 1 labels)
        row2_label_y = row1_label_y + 8
        text_lines.append((16, row2_label_y, "Blind Spot", Colors.ELECTRIC_PURPLE))
        text_lines.append((16, row2_label_y + 1, "Hide & +10!", Colors.YELLOW))

        text_lines.append((37, row2_label_y, "Gateway", Colors.CYAN))
        text_lines.append((38, row2_label_y + 1, "Exit", Colors.LIGHT_GRAY))

        text_lines.append((53, row2_label_y, "Data Fragment", Colors.CYAN))
        text_lines.append((57, row2_label_y + 1, "Story", Colors.LIGHT_GRAY))

        # Build sprites with calculated y positions (sprites are 2 lines below their labels)
        # Centered layout: left=21, middle=40 (screen center), right=59
        row1_sprite_y = row1_label_y + 2
        row2_sprite_y = row2_label_y + 2
        sprites = [
            # Row 1: Player, Floor, Wall
            ('player', 21, row1_sprite_y, 1.0),
            ('floor', 40, row1_sprite_y, 1.0),
            ('wall', 59, row1_sprite_y, 1.0),
            # Row 2: Blind Spot, Gateway, Story Fragment
            ('blind_spot', 21, row2_sprite_y, 1.0),
            ('gateway', 40, row2_sprite_y, 1.0),
            ('story_fragment', 59, row2_sprite_y, 1.0),
        ]

        # Continue with OBJECTIVE & MECHANICS after map symbols
        y = row2_label_y + 5  # Space after map symbols section (extra blank line)
        heading = "OBJECTIVE & MECHANICS:"
        text_lines.append((utils.center_x(heading), y, heading, Colors.CYAN))

        # Objectives
        y += 2
        for text, color in HelpContent.get_objectives():
            text_lines.append((utils.center_x(text), y, text, color))
            y += 1

        # Core mechanics - left-aligned block, centered as a group
        y += 1
        mechanics_text = [f"{stat}: {desc}" for stat, desc, _ in HelpContent.get_core_mechanics()]
        block_x = utils.center_block_x(mechanics_text)
        for i, (stat, desc, color) in enumerate(HelpContent.get_core_mechanics()):
            text = mechanics_text[i]
            text_lines.append((block_x, y, text, color))
            y += 1

        # CONTROLS section
        y += 2
        heading = "CONTROLS:"
        text_lines.append((utils.center_x(heading), y, heading, Colors.CYAN))

        controls = HelpContent.get_controls()

        # Movement - left-aligned block, centered as group
        y += 2
        movement_text = [f"{label}: {desc}" for label, desc in controls['movement']]
        block_x = utils.center_block_x(movement_text)
        for label, desc in controls['movement']:
            text = f"{label}: {desc}"
            text_lines.append((block_x, y, text, Colors.WHITE))
            y += 1

        # Screen shortcuts - left-aligned block, centered as group
        y += 1
        screens = controls['screens']
        screen_text = [f"{label}: {desc}" for label, desc in screens]
        block_x = utils.center_block_x(screen_text)
        for label, desc in screens:
            text = f"{label}: {desc}"
            text_lines.append((block_x, y, text, Colors.WHITE))
            y += 1

        # Inventory controls - left-aligned block, centered as group
        y += 1
        inventory_text = [f"{label}: {desc}" for label, desc in controls['inventory']]
        block_x = utils.center_block_x(inventory_text)
        for label, desc in controls['inventory']:
            text = f"{label}: {desc}"
            text_lines.append((block_x, y, text, Colors.WHITE))
            y += 1

        # Mouse - left-aligned block, centered as group
        y += 1
        mouse_text = []
        for label, desc in controls['mouse']:
            if "Click" in label:
                mouse_text.append(f"Mouse: {label} to {desc.lower()}")
            elif "Wheel" in label:
                mouse_text.append(f"Wheel to {desc.lower()}")
            else:
                mouse_text.append(f"Right-click to {desc.lower()}")
        block_x = utils.center_block_x(mouse_text)
        for i, (label, desc) in enumerate(controls['mouse']):
            text_lines.append((block_x, y, mouse_text[i], Colors.WHITE if "Right" not in label else Colors.LIGHT_GRAY))
            y += 1

        # Debug
        for label, desc in controls['debug']:
            text = f"{label}: {desc}"
            text_lines.append((utils.center_x(text), y, text, Colors.LIGHT_GRAY))
            y += 1

        return {
            'title': 'MAP, OBJECTIVE, & CONTROLS (Page 1/3)',
            'sprites': sprites,
            'text_lines': text_lines
        }

    def _build_page_2(self) -> dict:
        """Page 2/3: ITEMS & ENEMIES with sprites (two-column centered layout)."""
        utils = ScreenRenderingUtils

        # Load enemy data from HelpContent
        enemies = HelpContent.get_enemy_data()
        enemy_order = ['Scanner', 'Firewall', 'Patrol', 'Bot', 'Hunter', 'Virus', 'Inhibitor', 'Admin Avatar']

        # Calculate centered two-column layout
        # Left column width: ~25 chars, Gap: 8 chars, Right column width: ~30 chars
        # Total: 63 chars, centered on 80-char screen = start at (80-63)/2 = 8.5 ~= 9
        left_col_start = 9
        left_sprite_x = 7  # Sprite slightly left of text
        left_text_x = 9    # Text 2 chars right of sprite position (same gap as right column)

        column_gap = 8
        right_col_start = left_col_start + 25 + column_gap  # = 42
        right_sprite_x = 40  # Sprite slightly left of text
        right_text_x = 42    # Text 2 chars right of sprite position

        # Sprites - left column power-ups, right column enemies
        sprites = [
            # LEFT COLUMN - Power-ups
            ('codehack', left_sprite_x, 8, 1.0),
            ('exploit', left_sprite_x, 13, 1.0),
            ('cpu_node', left_sprite_x, 18, 1.0),
            ('cooling_node', left_sprite_x, 23, 1.0),
            ('ghost_node', left_sprite_x, 28, 1.0),
            ('cpu_upgrade', left_sprite_x, 33, 1.0),
            ('ram_upgrade', left_sprite_x, 38, 1.0),
            ('cooling_upgrade', left_sprite_x, 43, 1.0),
        ]

        # RIGHT COLUMN - Enemy sprites (more spacing between enemies)
        enemy_y_positions = [9, 13, 17, 21, 25, 29, 33, 37]
        for i, enemy_name in enumerate(enemy_order):
            if i < len(enemy_y_positions):
                sprites.append((enemy_name, right_sprite_x, enemy_y_positions[i], 1.0))

        text_lines = []

        # LEFT COLUMN - Power-ups
        text_lines.append((left_text_x, 6, "POWER-UPS:", Colors.CYAN))

        # Code Patch & Exploit
        text_lines.append((left_text_x, 8, "Code Patch", Colors.ELECTRIC_PURPLE))
        text_lines.append((left_text_x, 9, "Random stat bonus", Colors.LIGHT_GRAY))

        text_lines.append((left_text_x, 13, "Exploit", self.NEON_PINK))
        text_lines.append((left_text_x, 14, "Combat/utility tool", Colors.LIGHT_GRAY))

        # Nodes
        text_lines.append((left_text_x, 18, "CPU Node", Colors.RED))
        text_lines.append((left_text_x, 19, "+20 HP restore", Colors.LIGHT_GRAY))

        text_lines.append((left_text_x, 23, "Cooling Node", Colors.CYAN))
        text_lines.append((left_text_x, 24, "-20 heat", Colors.LIGHT_GRAY))

        text_lines.append((left_text_x, 28, "Ghost Node", Colors.ELECTRIC_PURPLE))
        text_lines.append((left_text_x, 29, "-20% trace (blind spot)", Colors.LIGHT_GRAY))

        # Upgrades
        text_lines.append((left_text_x, 31, "PERMANENT UPGRADES:", Colors.CYAN))

        text_lines.append((left_text_x, 33, "CPU Upgrade", Colors.ELECTRIC_BLUE))
        text_lines.append((left_text_x, 34, "+20 max CPU", Colors.YELLOW))

        text_lines.append((left_text_x, 38, "RAM Upgrade", Colors.ELECTRIC_BLUE))
        text_lines.append((left_text_x, 39, "+4 RAM", Colors.YELLOW))

        text_lines.append((left_text_x, 43, "Cooling Upgrade", Colors.ELECTRIC_BLUE))
        text_lines.append((left_text_x, 44, "+20 heat tolerance", Colors.YELLOW))

        # RIGHT COLUMN - Enemies
        text_lines.append((right_text_x, 6, "ENEMIES:", Colors.CYAN))
        text_lines.append((right_text_x, 7, "(HP / Vision / Damage)", Colors.LIGHT_GRAY))

        # Render enemies from HelpContent
        for i, enemy_name in enumerate(enemy_order):
            if enemy_name in enemies and i < len(enemy_y_positions):
                data = enemies[enemy_name]
                y = enemy_y_positions[i]
                behavior = data['behavior']
                color = HelpContent.ENEMY_COLORS[behavior]

                text_lines.append((right_text_x, y, enemy_name, color))

                # Format description line - always white
                desc = f"{data['cpu']} / {data['vision']} / {data['damage']} - {data['description']}"
                text_lines.append((right_text_x, y + 1, desc, Colors.WHITE))

        return {
            'title': 'ITEMS & ENEMIES (Page 2/3)',
            'sprites': sprites,
            'text_lines': text_lines
        }

    def _build_page_3(self) -> dict:
        """Page 3/3: EXPLOITS & STATUS EFFECTS (2-column layout, no sprites)."""
        utils = ScreenRenderingUtils

        text_lines = []

        # Two-column positions (narrower left column with 2-line exploits, wider gap)
        left_x = 5
        right_x = 42  # More gap between columns

        exploits = HelpContent.get_exploits()
        effects = HelpContent.get_status_effects()

        # LEFT COLUMN - COMBAT EXPLOITS (2 lines per exploit)
        y_left = 4
        text_lines.append((left_x, y_left, "COMBAT EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits['combat']:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        y_left += 2  # Spacing between sections

        # LEFT COLUMN - STEALTH EXPLOITS (2 lines per exploit)
        text_lines.append((left_x, y_left, "STEALTH EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits['stealth']:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        y_left += 2  # Spacing between sections

        # LEFT COLUMN - UTILITY EXPLOITS (2 lines per exploit)
        text_lines.append((left_x, y_left, "UTILITY EXPLOITS:", Colors.CYAN))
        y_left += 2

        for name, desc, color in exploits['utility']:
            text_lines.append((left_x + 1, y_left, name, color))  # Name in color
            y_left += 1
            text_lines.append((left_x + 1, y_left, desc, Colors.WHITE))  # Description in white
            y_left += 1

        # RIGHT COLUMN - STATUS EFFECTS (2 lines per effect)
        y_right = 4
        text_lines.append((right_x, y_right, "STATUS EFFECTS:", Colors.CYAN))
        y_right += 2

        for name, desc, color in effects['positive']:
            text_lines.append((right_x + 1, y_right, name, color))  # Name in color
            y_right += 1
            text_lines.append((right_x + 1, y_right, desc, Colors.WHITE))  # Description in white
            y_right += 1

        y_right += 1  # Blank line between positive and negative effects

        for name, desc, color in effects['negative']:
            text_lines.append((right_x + 1, y_right, name, color))  # Name in color
            y_right += 1
            text_lines.append((right_x + 1, y_right, desc, Colors.WHITE))  # Description in white
            y_right += 1

        y_right += 2  # Spacing between sections

        # RIGHT COLUMN - SURVIVAL TIPS (with wrapping for long lines)
        text_lines.append((right_x, y_right, "SURVIVAL TIPS:", Colors.YELLOW))
        y_right += 2

        tips = HelpContent.get_survival_tips()
        max_width = 28  # Right column width (reduced for more right padding)
        for text, color in tips:
            # Word wrap using textwrap
            wrapped_lines = textwrap.wrap(text, width=max_width)
            for line in wrapped_lines:
                text_lines.append((right_x + 1, y_right, line, color))
                y_right += 1
            # Extra blank line after each complete tip
            y_right += 2

        return {
            'title': 'EXPLOITS & STATUS EFFECTS (Page 3/3)',
            'sprites': [],  # Text-only page
            'text_lines': text_lines
        }

    # Rendering methods (unchanged from original)
    def render(self, console: tcod.console.Console) -> None:
        """Render the current help page."""
        self._build_pages()

        if not self.pages or self.current_page >= len(self.pages):
            logging.error(f"Invalid page state: current={self.current_page}, total={len(self.pages)}")
            return

        page = self.pages[self.current_page]
        self._render_text_layer(console, page)

    def render_sprites(self):
        """Render sprites directly to SDL renderer."""
        if not self.pages_built:
            self._build_pages()

        if not self.pages or self.current_page >= len(self.pages):
            return

        page = self.pages[self.current_page]

        if not page.get('sprites'):
            return

        renderer = self.context.sdl_renderer
        # Get actual window dimensions in pixels (not console dimensions!)
        window_width, window_height = self.context.sdl_window.size

        for sprite_data in page['sprites']:
            sprite_name, char_x, char_y, scale = sprite_data

            texture = self.tile_manager.get_tile(sprite_name)
            if texture is None:
                raise RuntimeError(
                    f"Failed to load sprite '{sprite_name}' for help menu.\n"
                    f"This sprite should be available in the TileManager.\n"
                    f"Check that all sprites are properly loaded during initialization."
                )

            # Use CoordinateHelpers to convert console coords to pixels
            pixel_x, pixel_y = CoordinateHelpers.char_to_pixel_coords(
                console_x=char_x,
                console_y=char_y,
                window_width=window_width,
                window_height=window_height,
                console_width=GameConfig.SCREEN_WIDTH,
                console_height=GameConfig.SCREEN_HEIGHT
            )

            scaled_width = int(self.tile_manager.tile_width * scale)
            scaled_height = int(self.tile_manager.tile_height * scale)

            dest_rect = (pixel_x, pixel_y, scaled_width, scaled_height)
            renderer.copy(texture, dest=dest_rect)

    def _render_text_layer(self, console: tcod.console.Console, page: dict):
        """Render text layer with transparency for sprites."""
        console.clear()

        CoordinateHelpers.set_alpha_region(
            console, x=0, y=0, width=console.width, height=console.height, alpha=0
        )

        # Render title
        title = page.get('title', 'HELP')
        title_x = GameConfig.SCREEN_WIDTH // 2 - len(title) // 2
        render_char_safe(console, title_x, 2, title, fg=Colors.YELLOW, bg=Colors.BLACK)

        # Render page indicator
        page_indicator = f"Page {self.current_page + 1}/{len(self.pages)}"
        indicator_x = GameConfig.SCREEN_WIDTH - len(page_indicator) - 2
        render_char_safe(console, indicator_x, 2, page_indicator, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)

        # Render text lines
        for x, y, text, color in page.get('text_lines', []):
            render_char_safe(console, x, y, text, fg=color, bg=Colors.BLACK)

        # Render navigation help
        nav_text = "←→: Change Page  │  ESC: Back"
        nav_x = GameConfig.SCREEN_WIDTH // 2 - len(nav_text) // 2
        render_char_safe(console, nav_x, GameConfig.SCREEN_HEIGHT - 2, nav_text, fg=Colors.CYAN, bg=Colors.BLACK)

    # Input handling methods (unchanged from original)
    def handle_input(self, event) -> str:
        """Handle input for graphical help menu."""
        if isinstance(event, tcod.event.KeyDown):
            if event.sym == tcod.event.KeySym.LEFT or event.sym == tcod.event.KeySym.UP:
                self._previous_page()
                return ""
            elif event.sym == tcod.event.KeySym.RIGHT or event.sym == tcod.event.KeySym.DOWN:
                self._next_page()
                return ""
            elif UniversalInputHandler.is_escape_key(event):
                return "back"

        return ""

    def handle_mouse_motion(self, event) -> bool:
        """Handle mouse motion (not used in graphical help menu)."""
        return False

    def handle_mouse_click(self, event) -> str:
        """Handle mouse clicks - right-click to return."""
        import tcod.event

        # Right-click = go back (standard behavior)
        if hasattr(event, 'button') and event.button == tcod.event.MouseButton.RIGHT:
            return "back"

        return ""

    def handle_mouse_wheel(self, event) -> bool:
        """Handle mouse wheel - navigate pages."""
        if hasattr(event, 'y'):
            if event.y > 0:
                self._previous_page()
            elif event.y < 0:
                self._next_page()
            return True
        return False

    def _next_page(self):
        """Navigate to next page."""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1

    def _previous_page(self):
        """Navigate to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
