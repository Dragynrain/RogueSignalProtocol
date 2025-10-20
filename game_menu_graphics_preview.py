#!/usr/bin/env python3
"""
Graphics Preview Menu - Interactive sprite variant explorer

Allows visual preview and selection of all graphic variants in the game.
Navigate between entity types and cycle through available variants to see
how different combinations look together.
"""

import tcod
import logging
import os
import glob
import re
import json
import time
import math
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from game_config import GameSettings, GameConfig
from game_entities import Colors, ensure_color_tuple
from game_ui import render_char_safe
from game_graphics_tiles import TileManager
from data_loading import DataLoader
from game_coordinate_helpers import CoordinateHelpers


class GraphicsPreviewMenu:
    """Interactive graphics preview and variant selector."""

    def __init__(self, context, settings: GameSettings, tile_manager: TileManager):
        """
        Initialize Graphics Preview menu.

        Args:
            context: TCOD context for rendering
            settings: Game settings instance
            tile_manager: Tile manager for loading graphics
        """
        self.context = context
        self.settings = settings
        self.tile_manager = tile_manager

        # Scan available graphics and organize by entity type
        self.entity_types = []  # List of (category, entity_name, display_name)
        self.variants = {}  # Dict: entity_key -> list of variant numbers
        self.selected_variants = {}  # Dict: entity_key -> selected variant number

        # Current selection state
        self.current_entity_index = 0  # Which entity type is selected

        # Texture cache for loaded variants (key: "entityname_variantnum" -> texture)
        self.texture_cache = {}

        # Load color configurations from game_rules.json
        self.codehack_colors = []
        self.exploit_colors = []
        self._load_color_config()

        # Alert ring animation state
        self.alert_color_index = 0  # 0=yellow, 1=orange, 2=red
        config = DataLoader.load_config()
        alert_seq = config.get("colors", {}).get("preview_demo", {}).get("alert_sequence", [])
        self.alert_colors = [ensure_color_tuple(c) for c in alert_seq] if alert_seq else [(255, 255, 0), (255, 165, 0), (255, 0, 0)]

        # Load available graphics
        self._scan_available_graphics()

        # Preview map layout (simple grid showing all elements)
        self._setup_preview_layout()

    def _load_color_config(self):
        """Load color configurations from game_rules.json."""
        try:
            with open("game_rules.json", 'r', encoding='utf-8') as f:
                rules = json.load(f)

            # Load codehack colors (data_codes)
            data_codes = rules.get("colors", {}).get("data_codes", {})
            self.codehack_colors = [
                tuple(data_codes.get("crimson", [220, 20, 60])),
                tuple(data_codes.get("cyan", [0, 255, 255])),
                tuple(data_codes.get("emerald", [50, 205, 50])),
                tuple(data_codes.get("golden", [255, 215, 0])),
                tuple(data_codes.get("violet", [138, 43, 226])),
                tuple(data_codes.get("silver", [192, 192, 192])),
            ]

            # Load exploit colors
            exploits = rules.get("colors", {}).get("exploits", {})
            # Get all 4 unique exploit colors, then repeat 2 for the 2x3 grid
            self.exploit_colors = [
                tuple(exploits.get("stealth", [138, 43, 226])),
                tuple(exploits.get("combat", [220, 20, 60])),
                tuple(exploits.get("utility", [255, 215, 0])),
                tuple(exploits.get("emergency", [255, 120, 20])),
                tuple(exploits.get("stealth", [138, 43, 226])),  # Repeat
                tuple(exploits.get("combat", [220, 20, 60])),    # Repeat
            ]

            logging.info(f"Loaded {len(self.codehack_colors)} codehack colors and {len(self.exploit_colors)} exploit colors")

        except Exception as e:
            logging.error(f"Failed to load color config from game_rules.json: {e}")
            # Fallback to default colors from preview_demo
            config = DataLoader.load_config()
            preview_demo = config.get("colors", {}).get("preview_demo", {})
            enemy_colors_data = preview_demo.get("enemy_colors", [])
            exploit_colors_data = preview_demo.get("exploit_colors", [])
            self.codehack_colors = [ensure_color_tuple(c) for c in enemy_colors_data] if enemy_colors_data else [
                (220, 20, 60), (0, 255, 255), (50, 205, 50),
                (255, 215, 0), (138, 43, 226), (192, 192, 192)
            ]
            self.exploit_colors = [ensure_color_tuple(c) for c in exploit_colors_data] if exploit_colors_data else [
                (138, 43, 226), (220, 20, 60), (255, 215, 0),
                (255, 120, 20), (138, 43, 226), (220, 20, 60)
            ]

    def _get_default_variant_from_config(self, entity_key: str) -> int:
        """
        Get default variant number from graphics_tiles.json.

        Args:
            entity_key: Entity key (e.g., "player", "scanner", "floor")

        Returns:
            Variant number from config, or 1 if not found
        """
        tile_mappings = self.tile_manager.tile_mappings

        # Check player
        if entity_key == "player":
            if "player" in tile_mappings and "file" in tile_mappings["player"]:
                filename = tile_mappings["player"]["file"]
                # Extract variant number from filename (e.g., "player02.png" -> 2)
                match = re.match(r'^[a-z]+(\d+)\.png$', filename)
                if match:
                    return int(match.group(1))

        # Check in categories
        for category in ["enemies", "terrain", "items", "special"]:
            if category in tile_mappings:
                category_data = tile_mappings[category]
                if isinstance(category_data, dict):
                    for name, data in category_data.items():
                        if isinstance(data, dict) and "file" in data:
                            # Extract base name from file (e.g., "scanner02.png" -> "scanner")
                            filename = data["file"]
                            base_name = filename.replace(".png", "").rstrip("0123456789")
                            if base_name == entity_key:
                                # Extract variant number
                                match = re.match(r'^[a-z]+(\d+)\.png$', filename)
                                if match:
                                    return int(match.group(1))

        # Default to variant 1 if not found
        return 1

    def _scan_available_graphics(self):
        """Scan graphics directory to find all available entity types and variants."""
        graphics_dir = self.tile_manager.graphics_dir

        if not os.path.exists(graphics_dir):
            logging.error(f"Graphics directory not found: {graphics_dir}")
            return

        # Find all PNG files and extract entity names and variant numbers
        png_files = glob.glob(os.path.join(graphics_dir, "*.png"))

        # Group files by entity type
        entity_groups = defaultdict(list)

        for filepath in png_files:
            filename = os.path.basename(filepath)

            # Extract entity name and variant number (e.g., "player01.png" -> "player", 1)
            match = re.match(r'^([a-z]+)(\d+)\.png$', filename)
            if match:
                entity_name = match.group(1)
                variant_num = int(match.group(2))
                entity_groups[entity_name].append(variant_num)

        # Build entity types list with proper categorization
        # Use graphics_tiles.json mappings to determine category and display names
        tile_mappings = self.tile_manager.tile_mappings

        # Helper to get display name from mapping
        def get_display_name(entity_key: str) -> str:
            # Check player
            if entity_key == "player":
                return "Player"

            # Check categories
            for category in ["enemies", "terrain", "items", "special"]:
                if category in tile_mappings:
                    category_data = tile_mappings[category]
                    if isinstance(category_data, dict):
                        for name, data in category_data.items():
                            if isinstance(data, dict) and "file" in data:
                                # Extract base name from file (e.g., "scanner01.png" -> "scanner")
                                base_name = data["file"].replace(".png", "").rstrip("0123456789")
                                if base_name == entity_key:
                                    return name

            # Fallback: capitalize entity key
            return entity_key.capitalize()

        # Build organized entity list
        # Order: Terrain, Player, Enemies, Items, Special

        # Terrain
        terrain_order = ["floor", "wall", "shadow"]
        for terrain_type in terrain_order:
            if terrain_type in entity_groups:
                display_name = get_display_name(terrain_type)
                self.entity_types.append(("terrain", terrain_type, display_name))
                self.variants[terrain_type] = sorted(entity_groups[terrain_type])
                # Use default from graphics_tiles.json
                default_variant = self._get_default_variant_from_config(terrain_type)
                self.selected_variants[terrain_type] = default_variant if default_variant in self.variants[terrain_type] else self.variants[terrain_type][0]

        # Player
        if "player" in entity_groups:
            self.entity_types.append(("player", "player", "Player"))
            self.variants["player"] = sorted(entity_groups["player"])
            # Use default from graphics_tiles.json
            default_variant = self._get_default_variant_from_config("player")
            self.selected_variants["player"] = default_variant if default_variant in self.variants["player"] else self.variants["player"][0]

        # Enemies
        enemy_order = ["scanner", "patrol", "bot", "hunter", "virus", "inhibitor", "firewall", "avatar"]
        for enemy_type in enemy_order:
            if enemy_type in entity_groups:
                display_name = get_display_name(enemy_type)
                self.entity_types.append(("enemy", enemy_type, display_name))
                self.variants[enemy_type] = sorted(entity_groups[enemy_type])
                # Use default from graphics_tiles.json
                default_variant = self._get_default_variant_from_config(enemy_type)
                self.selected_variants[enemy_type] = default_variant if default_variant in self.variants[enemy_type] else self.variants[enemy_type][0]

        # Items
        item_order = ["codehack", "exploit", "coolingnode", "coolingupgrade",
                     "cpunode", "cpuupgrade", "ramupgrade", "ghostnode"]
        for item_type in item_order:
            if item_type in entity_groups:
                display_name = get_display_name(item_type)
                self.entity_types.append(("item", item_type, display_name))
                self.variants[item_type] = sorted(entity_groups[item_type])
                # Use default from graphics_tiles.json
                default_variant = self._get_default_variant_from_config(item_type)
                self.selected_variants[item_type] = default_variant if default_variant in self.variants[item_type] else self.variants[item_type][0]

        # Special
        special_order = ["portal", "storyfragment", "movementprediction", "targeting"]
        for special_type in special_order:
            if special_type in entity_groups:
                display_name = get_display_name(special_type)
                self.entity_types.append(("special", special_type, display_name))
                self.variants[special_type] = sorted(entity_groups[special_type])
                # Use default from graphics_tiles.json
                default_variant = self._get_default_variant_from_config(special_type)
                self.selected_variants[special_type] = default_variant if default_variant in self.variants[special_type] else self.variants[special_type][0]

        logging.info(f"Graphics Preview: Found {len(self.entity_types)} entity types")

    def _setup_preview_layout(self):
        """Set up the preview map layout showing all elements."""
        # Layout:
        # TOP-LEFT: Shadow cluster with ghost node
        # TOP-RIGHT: CodeHacks and Exploits (6 each in tight cluster)
        # CENTER: Enemies with alert rings
        # BOTTOM-RIGHT: Combat scene with player and enemy (vision brackets, movement queue of 3)

        # Map size in entity tiles
        self.map_tiles_width = 22
        self.map_tiles_height = 16

        # Console transparent area must be 2× larger because sprites are 2× base tile size
        self.preview_width = 44  # Console grid cells needed for 22 game sprites
        self.preview_height = 32  # Console grid cells needed for 16 game sprites

        self.preview_offset_x = 1
        self.preview_offset_y = 6

    def render(self, console: tcod.console.Console) -> None:
        """Render the graphics preview screen."""
        console.clear()

        # Make preview area transparent so SDL graphics show through
        if self.settings.graphics_mode == "graphics":
            # Use CoordinateHelpers to set transparency correctly regardless of console order
            CoordinateHelpers.set_alpha_region(
                console,
                x=self.preview_offset_x,
                y=self.preview_offset_y,
                width=self.preview_width,
                height=self.preview_height,
                alpha=0
            )

        # Title
        title = "GRAPHICS PREVIEW - VARIANT EXPLORER"
        render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 1,
                        title, fg=Colors.CYAN)

        # Current selection info
        if self.entity_types:
            category, entity_key, display_name = self.entity_types[self.current_entity_index]
            current_variant = self.selected_variants[entity_key]
            total_variants = len(self.variants[entity_key])
            variant_index = self.variants[entity_key].index(current_variant) + 1

            info_text = f"Selected: {display_name} - Variant {variant_index}/{total_variants}"
            render_char_safe(console, 2, 2, info_text, fg=Colors.YELLOW)

            file_text = f"File: {entity_key}{current_variant:02d}.png"
            render_char_safe(console, 2, 3, file_text, fg=Colors.LIGHT_GRAY)

        # Note about graphics mode
        if self.settings.graphics_mode == "graphics":
            note = "Graphics rendering on preview map (left side)"
            render_char_safe(console, 2, 5, note, fg=Colors.GREEN)
        else:
            note = "Enable Graphics Mode in Settings to see preview"
            render_char_safe(console, 2, 5, note, fg=Colors.RED)

        # Render entity list (sidebar)
        self._render_entity_list(console)

        # Instructions
        instructions = [
            "UP/DOWN or W/S: Select entity type",
            "LEFT/RIGHT or A/D: Change variant",
            "SPACE: Cycle alert ring color",
            "ESC: Exit and save log",
        ]

        inst_y = GameConfig.SCREEN_HEIGHT - len(instructions) - 1
        for i, instruction in enumerate(instructions):
            render_char_safe(console, 2, inst_y + i, instruction, fg=Colors.LIGHT_GRAY)

    def _render_preview_map(self, console: tcod.console.Console):
        """Render the preview map showing all selected graphics."""
        # Only render in graphics mode
        if self.settings.graphics_mode != "graphics":
            # Show message in glyph mode
            msg = "Graphics Preview requires Graphics Mode"
            render_char_safe(console, self.preview_offset_x, self.preview_offset_y + 5,
                           msg, fg=Colors.RED)
            msg2 = "Enable Graphics Mode in Settings"
            render_char_safe(console, self.preview_offset_x, self.preview_offset_y + 6,
                           msg2, fg=Colors.LIGHT_GRAY)
            return

        # Calculate pixel positions
        # Use the GAME's sprite tile size (2x enlarged) so preview matches game
        tile_w = self.tile_manager.tile_width
        tile_h = self.tile_manager.tile_height

        # Get base console tile size for calculating preview area offset
        # The preview_offset uses CONSOLE GRID coordinates, not sprite coordinates
        window_size = self.context.sdl_window.size
        base_tile_w = window_size[0] // GameConfig.SCREEN_WIDTH
        base_tile_h = window_size[1] // GameConfig.SCREEN_HEIGHT

        # Calculate preview area offset in pixels (using BASE tile size to match console grid)
        offset_pixel_x = self.preview_offset_x * base_tile_w
        offset_pixel_y = self.preview_offset_y * base_tile_h

        # Render using SDL directly
        renderer = self.context.sdl_renderer
        if not renderer:
            return

        # Map of what to render where (x, y, entity_key, layer)
        render_queue = []

        # Floor tiles (fill area) - use map tile dimensions
        if "floor" in self.selected_variants:
            for y in range(self.map_tiles_height):
                for x in range(self.map_tiles_width):
                    render_queue.append((x, y, "floor", 0))

        # Walls (border) - use map tile dimensions
        if "wall" in self.selected_variants:
            for x in range(self.map_tiles_width):
                render_queue.append((x, 0, "wall", 1))
                render_queue.append((x, self.map_tiles_height - 1, "wall", 1))
            for y in range(1, self.map_tiles_height - 1):  # Avoid corners already done
                render_queue.append((0, y, "wall", 1))
                render_queue.append((self.map_tiles_width - 1, y, "wall", 1))

        # Shadow cluster in top-left (3x3 grid) with ghost node on ONE of them
        if "shadow" in self.selected_variants:
            for sy in range(2, 5):
                for sx in range(2, 5):
                    render_queue.append((sx, sy, "shadow", 1))
            # Ghost node on top of center shadow (demonstrates layering)
            if "ghostnode" in self.selected_variants:
                render_queue.append((3, 3, "ghostnode", 2))

        # Player is rendered explicitly in combat scene section (not in render_queue)

        # Enemies (compact grid in center-left - 2 rows of 4)
        enemy_positions = [
            (2, 7), (4, 7), (6, 7), (8, 7),
            (2, 9), (4, 9), (6, 9), (8, 9)
        ]
        enemy_types = ["scanner", "patrol", "bot", "hunter", "virus", "inhibitor", "firewall", "avatar"]
        for i, enemy_type in enumerate(enemy_types):
            if enemy_type in self.selected_variants and i < len(enemy_positions):
                ex, ey = enemy_positions[i]
                render_queue.append((ex, ey, enemy_type, 2))

        # Items (compact cluster in bottom-left)
        item_positions = [
            (2, 12), (4, 12), (6, 12),  # First row
            (2, 14), (4, 14), (6, 14)  # Second row
        ]
        item_types = ["coolingnode", "coolingupgrade", "cpunode", "cpuupgrade",
                     "ramupgrade", "portal"]
        for i, item_type in enumerate(item_types):
            if item_type in self.selected_variants and i < len(item_positions):
                ix, iy = item_positions[i]
                render_queue.append((ix, iy, item_type, 2))

        # Story fragment
        if "storyfragment" in self.selected_variants:
            render_queue.append((8, 12, "storyfragment", 2))

        # Sort by layer and render base sprites
        render_queue.sort(key=lambda item: item[3])

        for map_x, map_y, entity_key, layer in render_queue:
            # Get texture with current variant
            texture = self._get_variant_texture(entity_key)
            if texture:
                # Calculate screen position
                screen_x = offset_pixel_x + (map_x * tile_w)
                screen_y = offset_pixel_y + (map_y * tile_h)

                # Normal rendering
                renderer.copy(texture, dest=(screen_x, screen_y, tile_w, tile_h))

        # Now render special overlays and effects on top

        # 1. CodeHacks in TOP RIGHT corner - tight 3x2 cluster (full-size sprites)
        if "codehack" in self.selected_variants:
            codehack_texture = self._get_variant_texture("codehack")
            if codehack_texture:
                # Tight cluster: 3 rows x 2 columns starting at (16,1)
                codehack_grid = [
                    (16, 1), (17, 1),  # Top row
                    (16, 2), (17, 2),  # Middle row
                    (16, 3), (17, 3),  # Bottom row
                ]
                for i, color in enumerate(self.codehack_colors):
                    if i < len(codehack_grid):
                        ch_x, ch_y = codehack_grid[i]
                        screen_x = offset_pixel_x + (ch_x * tile_w)
                        screen_y = offset_pixel_y + (ch_y * tile_h)

                        # Apply color tint
                        codehack_texture.color_mod = color
                        renderer.copy(codehack_texture, dest=(screen_x, screen_y, tile_w, tile_h))

                # Reset color mod
                config = DataLoader.load_config()
                normal_tint = ensure_color_tuple(config.get("colors", {}).get("graphics_tint", {}).get("normal", [255, 255, 255]))
                codehack_texture.color_mod = normal_tint

        # 2. Exploits in TOP RIGHT corner - tight 3x2 cluster below CodeHacks
        if "exploit" in self.selected_variants:
            exploit_texture = self._get_variant_texture("exploit")
            if exploit_texture:
                # Tight cluster: 3 rows x 2 columns starting at (19,1)
                exploit_grid = [
                    (19, 1), (20, 1),  # Top row
                    (19, 2), (20, 2),  # Middle row
                    (19, 3), (20, 3),  # Bottom row
                ]
                for i, color in enumerate(self.exploit_colors):
                    if i < len(exploit_grid):
                        ex_x, ex_y = exploit_grid[i]
                        screen_x = offset_pixel_x + (ex_x * tile_w)
                        screen_y = offset_pixel_y + (ex_y * tile_h)

                        # Apply color tint
                        exploit_texture.color_mod = color
                        renderer.copy(exploit_texture, dest=(screen_x, screen_y, tile_w, tile_h))

                # Reset color mod
                config = DataLoader.load_config()
                normal_tint = ensure_color_tuple(config.get("colors", {}).get("graphics_tint", {}).get("normal", [255, 255, 255]))
                exploit_texture.color_mod = normal_tint

        # 3. Pulsing alert rings on all enemies
        # Use EXACT same pulse calculation as game renderer (from game_rendering.py)
        pulse_intensity = self._get_pulse_intensity(pulse_speed=1.34)

        for i, enemy_type in enumerate(enemy_types):
            if enemy_type in self.selected_variants and i < len(enemy_positions):
                ex, ey = enemy_positions[i]
                self._render_alert_ring(renderer, offset_pixel_x, offset_pixel_y,
                                      ex, ey, tile_w, tile_h, pulse_intensity)

        # 3b. Rainbow pulsing ring around story fragment
        if "storyfragment" in self.selected_variants:
            rainbow_color = self._get_rainbow_color()
            pulsed_rainbow = tuple(int(c * pulse_intensity) for c in rainbow_color)
            # Story fragment is at (8, 12)
            sf_x, sf_y = 8, 12
            screen_x = offset_pixel_x + (sf_x * tile_w)
            screen_y = offset_pixel_y + (sf_y * tile_h)

            # Draw rainbow ring (same style as alert rings)
            ring_thickness = 2
            ring_offset = 4
            renderer.draw_color = (*pulsed_rainbow, 255)

            # Top
            renderer.fill_rect((screen_x + ring_offset, screen_y + ring_offset,
                              tile_w - (ring_offset * 2), ring_thickness))
            # Bottom
            renderer.fill_rect((screen_x + ring_offset, screen_y + tile_h - ring_offset - ring_thickness,
                              tile_w - (ring_offset * 2), ring_thickness))
            # Left
            renderer.fill_rect((screen_x + ring_offset, screen_y + ring_offset,
                              ring_thickness, tile_h - (ring_offset * 2)))
            # Right
            renderer.fill_rect((screen_x + tile_w - ring_offset - ring_thickness, screen_y + ring_offset,
                              ring_thickness, tile_h - (ring_offset * 2)))

            # Reset draw color
            renderer.draw_color = (255, 255, 255, 255)

        # 4. Combat scene in BOTTOM RIGHT corner
        # Shows enemy with movement prediction (queue of 3) approaching player
        # Enemy's vision range covers the player (showing vision brackets)
        combat_enemy_x = 17
        combat_enemy_y = 11
        combat_player_x = 13
        combat_player_y = 11
        combat_target_x = 13
        combat_target_y = 10  # Square above player

        scanner_vision_range = 5  # From game_content.json

        # First render combat player sprite
        if "player" in self.selected_variants:
            player_texture = self._get_variant_texture("player")
            if player_texture:
                screen_x = offset_pixel_x + (combat_player_x * tile_w)
                screen_y = offset_pixel_y + (combat_player_y * tile_h)
                renderer.copy(player_texture, dest=(screen_x, screen_y, tile_w, tile_h))

        # Render targeting sprite above player
        if "targeting" in self.selected_variants:
            targeting_texture = self._get_variant_texture("targeting")
            if targeting_texture:
                screen_x = offset_pixel_x + (combat_target_x * tile_w)
                screen_y = offset_pixel_y + (combat_target_y * tile_h)
                renderer.copy(targeting_texture, dest=(screen_x, screen_y, tile_w, tile_h))

        # Draw enemy vision range brackets AROUND player using actual game vision rendering
        # Scanner vision = 5, so draw brackets in a 5-tile radius around enemy centered on player
        for dx in range(-scanner_vision_range, scanner_vision_range + 1):
            for dy in range(-scanner_vision_range, scanner_vision_range + 1):
                # Use Euclidean distance (same as game_rendering.py:1667)
                if dx*dx + dy*dy <= scanner_vision_range*scanner_vision_range:
                    bracket_x = combat_enemy_x + dx
                    bracket_y = combat_enemy_y + dy

                    # Skip enemy's own tile
                    if bracket_x == combat_enemy_x and bracket_y == combat_enemy_y:
                        continue

                    # Only draw brackets in the combat scene area
                    if 11 <= bracket_x <= 19 and 9 <= bracket_y <= 13:
                        bracket_rect = (
                            offset_pixel_x + (bracket_x * tile_w),
                            offset_pixel_y + (bracket_y * tile_h),
                            tile_w,
                            tile_h
                        )
                        # Red brackets for hostile enemy state
                        config = DataLoader.load_config()
                        bracket_color = ensure_color_tuple(config.get("colors", {}).get("targeting", {}).get("corner_bracket", [255, 0, 0]))
                        self._draw_corner_brackets(renderer, bracket_rect, bracket_color, bracket_size=4)

        # Render enemy in combat scene
        if "scanner" in self.selected_variants:
            enemy_texture = self._get_variant_texture("scanner")
            if enemy_texture:
                screen_x = offset_pixel_x + (combat_enemy_x * tile_w)
                screen_y = offset_pixel_y + (combat_enemy_y * tile_h)
                renderer.copy(enemy_texture, dest=(screen_x, screen_y, tile_w, tile_h))

                # Alert ring on this enemy (use same pulse)
                self._render_alert_ring(renderer, offset_pixel_x, offset_pixel_y,
                                      combat_enemy_x, combat_enemy_y, tile_w, tile_h, pulse_intensity)

        # Movement prediction showing enemy's next 3 queued moves TOWARD player
        # Using exact colors from game_rendering.py:1739-1744
        if "movementprediction" in self.selected_variants:
            prediction_texture = self._get_variant_texture("movementprediction")
            if prediction_texture:
                # Queue of 3 moves approaching player (left)
                prediction_positions = [
                    (16, 11),  # First move (brightest)
                    (15, 11),  # Second move
                    (14, 11),  # Third move (dimmest)
                ]
                config = DataLoader.load_config()
                targeting_colors = config.get("colors", {}).get("targeting", {})
                prediction_colors = [
                    ensure_color_tuple(targeting_colors.get("prediction_bright", [255, 255, 50])),
                    ensure_color_tuple(targeting_colors.get("prediction_medium", [240, 240, 30])),
                    ensure_color_tuple(targeting_colors.get("prediction_dim", [220, 220, 20])),
                ]
                for i, (pred_x, pred_y) in enumerate(prediction_positions):
                    screen_x = offset_pixel_x + (pred_x * tile_w)
                    screen_y = offset_pixel_y + (pred_y * tile_h)
                    # Apply color_mod based on queue position
                    prediction_texture.color_mod = prediction_colors[i]
                    renderer.copy(prediction_texture, dest=(screen_x, screen_y, tile_w, tile_h))
                # Reset color mod
                normal_tint = ensure_color_tuple(config.get("colors", {}).get("graphics_tint", {}).get("normal", [255, 255, 255]))
                prediction_texture.color_mod = normal_tint

    def _render_alert_ring(self, renderer, offset_pixel_x, offset_pixel_y,
                          map_x, map_y, tile_w, tile_h, pulse_intensity):
        """Render a pulsing alert ring around an entity."""
        # Get current alert color based on user selection (SPACE key cycles)
        base_color = self.alert_colors[self.alert_color_index]

        # Apply pulse to color (same as game_rendering.py:2453)
        outline_color = tuple(int(c * pulse_intensity) for c in base_color)

        # Calculate screen position
        screen_x = offset_pixel_x + (map_x * tile_w)
        screen_y = offset_pixel_y + (map_y * tile_h)

        # Draw a simple ring using SDL filled rect drawing
        # Ring is drawn as 4 rectangles forming a square outline
        ring_thickness = 2
        ring_offset = 4  # Pixels from edge

        # Set draw color with alpha (RGBA format required)
        renderer.draw_color = (*outline_color, 255)

        # Top
        renderer.fill_rect((screen_x + ring_offset, screen_y + ring_offset,
                          tile_w - (ring_offset * 2), ring_thickness))
        # Bottom
        renderer.fill_rect((screen_x + ring_offset, screen_y + tile_h - ring_offset - ring_thickness,
                          tile_w - (ring_offset * 2), ring_thickness))
        # Left
        renderer.fill_rect((screen_x + ring_offset, screen_y + ring_offset,
                          ring_thickness, tile_h - (ring_offset * 2)))
        # Right
        renderer.fill_rect((screen_x + tile_w - ring_offset - ring_thickness, screen_y + ring_offset,
                          ring_thickness, tile_h - (ring_offset * 2)))

        # Reset draw color to avoid affecting other rendering
        renderer.draw_color = (255, 255, 255, 255)

    def _draw_corner_brackets(self, renderer, rect: Tuple[int, int, int, int], color: Tuple[int, int, int], bracket_size: int = 4):
        """
        Draw corner brackets around a tile rectangle.
        COPIED DIRECTLY from game_rendering.py:2526-2563

        Args:
            renderer: SDL renderer instance
            rect: Rectangle (x, y, width, height) in pixels
            color: RGB color tuple
            bracket_size: Length of each bracket arm in pixels
        """
        x, y, w, h = rect

        # Convert RGB to RGBA for SDL
        if len(color) == 3:
            color_rgba = (*color, 255)
        else:
            color_rgba = color

        renderer.draw_color = color_rgba

        # Top-left corner
        renderer.draw_line((x, y), (x + bracket_size, y))  # Horizontal arm
        renderer.draw_line((x, y), (x, y + bracket_size))  # Vertical arm

        # Top-right corner
        renderer.draw_line((x + w - bracket_size - 1, y), (x + w - 1, y))  # Horizontal arm
        renderer.draw_line((x + w - 1, y), (x + w - 1, y + bracket_size))  # Vertical arm

        # Bottom-left corner
        renderer.draw_line((x, y + h - bracket_size - 1), (x, y + h - 1))  # Vertical arm
        renderer.draw_line((x, y + h - 1), (x + bracket_size, y + h - 1))  # Horizontal arm

        # Bottom-right corner
        renderer.draw_line((x + w - 1, y + h - bracket_size - 1), (x + w - 1, y + h - 1))  # Vertical arm
        renderer.draw_line((x + w - bracket_size - 1, y + h - 1), (x + w - 1, y + h - 1))  # Horizontal arm

        # Reset draw color
        renderer.draw_color = (255, 255, 255, 255)

    def _get_pulse_intensity(self, pulse_speed: float = 2.0) -> float:
        """
        Calculate pulse intensity based on current time.
        COPIED DIRECTLY from game_rendering.py:2565-2578

        Args:
            pulse_speed: Speed of pulsing (higher = faster). Default 2.0 Hz.

        Returns:
            Float between 0.7 and 1.0 representing brightness multiplier
        """
        current_time = time.time()
        pulse_phase = (current_time * pulse_speed) % 1.0  # 0.0 to 1.0
        pulse_intensity = 0.7 + 0.3 * math.sin(pulse_phase * 2 * math.pi)
        return pulse_intensity

    def _get_rainbow_color(self) -> Tuple[int, int, int]:
        """
        Calculate rainbow color based on current time for data fragment highlighting.
        COPIED from game_rendering_graphics.py

        Returns:
            RGB color tuple cycling through rainbow colors
        """
        import colorsys
        current_time = time.time()
        # Cycle through rainbow every 4 seconds
        hue = (current_time * 0.25) % 1.0  # 0.0 to 1.0

        # Convert HSV to RGB (hue cycles, saturation and value fixed)
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))

    def _get_variant_texture(self, entity_key: str) -> Optional[tcod.sdl.render.Texture]:
        """Get texture for entity with currently selected variant (with caching)."""
        if entity_key not in self.selected_variants:
            return None

        variant_num = self.selected_variants[entity_key]
        cache_key = f"{entity_key}_{variant_num}"

        # Check cache first
        if cache_key in self.texture_cache:
            return self.texture_cache[cache_key]

        # Not in cache, load it
        filename = f"{entity_key}{variant_num:02d}.png"
        filepath = os.path.join(self.tile_manager.graphics_dir, filename)

        if not os.path.exists(filepath):
            return None

        try:
            from PIL import Image
            import numpy as np

            # Load and scale image
            pil_image = Image.open(filepath)
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')

            # Use GAME sprite size (2x enlarged) so preview matches how game looks
            pil_image = pil_image.resize(
                (self.tile_manager.tile_width, self.tile_manager.tile_height),
                Image.Resampling.LANCZOS
            )

            pixels = np.array(pil_image, dtype=np.uint8)

            renderer = self.context.sdl_renderer
            if not renderer:
                return None

            texture = renderer.upload_texture(pixels)
            texture.blend_mode = tcod.sdl.render.BlendMode.BLEND

            # Cache the texture
            self.texture_cache[cache_key] = texture

            return texture

        except Exception as e:
            logging.warning(f"Failed to load variant texture {filepath}: {e}")
            return None

    def _render_entity_list(self, console: tcod.console.Console):
        """Render the sidebar list of all entity types."""
        # Position list on far right side (moved further right to avoid graphics overlap)
        list_x = GameConfig.SCREEN_WIDTH - 30
        list_y = 4

        # Header
        render_char_safe(console, list_x, list_y - 1, "ENTITY TYPES:", fg=Colors.CYAN)

        # Render list (with scrolling if needed)
        visible_count = 25  # Max visible items
        scroll_offset = max(0, self.current_entity_index - visible_count + 5)

        for i in range(visible_count):
            entity_index = scroll_offset + i
            if entity_index >= len(self.entity_types):
                break

            category, entity_key, display_name = self.entity_types[entity_index]
            is_selected = (entity_index == self.current_entity_index)

            # Color coding by category
            if is_selected:
                color = Colors.YELLOW
                prefix = "> "
            else:
                if category == "terrain":
                    color = Colors.LIGHT_GRAY
                elif category == "player":
                    color = Colors.CYAN
                elif category == "enemy":
                    color = Colors.RED
                elif category == "item":
                    color = Colors.GREEN
                elif category == "special":
                    color = Colors.ELECTRIC_PURPLE
                else:
                    color = Colors.WHITE
                prefix = "  "

            # Show variant count
            variant_count = len(self.variants[entity_key])
            current_variant = self.selected_variants[entity_key]
            variant_index = self.variants[entity_key].index(current_variant) + 1

            text = f"{prefix}{display_name} ({variant_index}/{variant_count})"
            render_char_safe(console, list_x, list_y + i, text[:32], fg=color)

    def handle_input(self, event) -> str:
        """
        Handle input for graphics preview.

        Returns:
            'exit' to exit and save log, '' to continue
        """
        if not self.entity_types:
            # No entities loaded, any key exits
            return 'exit'

        # Navigation (with wrap-around)
        if event.type == "KEYDOWN":
            if event.sym == tcod.event.KeySym.UP or event.sym == tcod.event.KeySym.W:
                self.current_entity_index = (self.current_entity_index - 1) % len(self.entity_types)
                return ''

            elif event.sym == tcod.event.KeySym.DOWN or event.sym == tcod.event.KeySym.S:
                self.current_entity_index = (self.current_entity_index + 1) % len(self.entity_types)
                return ''

            elif event.sym == tcod.event.KeySym.LEFT or event.sym == tcod.event.KeySym.A:
                # Cycle to previous variant
                self._cycle_variant(-1)
                return ''

            elif event.sym == tcod.event.KeySym.RIGHT or event.sym == tcod.event.KeySym.D:
                # Cycle to next variant
                self._cycle_variant(1)
                return ''

            elif event.sym == tcod.event.KeySym.SPACE:
                # Cycle alert ring color
                self.alert_color_index = (self.alert_color_index + 1) % len(self.alert_colors)
                return ''

            elif event.sym == tcod.event.KeySym.ESCAPE:
                return 'exit'

        return ''

    def _cycle_variant(self, direction: int):
        """Cycle the variant for currently selected entity."""
        if not self.entity_types:
            return

        category, entity_key, display_name = self.entity_types[self.current_entity_index]
        variants = self.variants[entity_key]
        current_variant = self.selected_variants[entity_key]

        current_index = variants.index(current_variant)
        new_index = (current_index + direction) % len(variants)

        self.selected_variants[entity_key] = variants[new_index]

    def export_selections(self, output_file: str = "graphic-preview.log"):
        """Export currently selected variants to a log file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Graphics Preview - Selected Variants\n")
                f.write("=" * 50 + "\n\n")

                # Group by category
                categories = [
                    ("terrain", "TERRAIN"),
                    ("player", "PLAYER"),
                    ("enemy", "ENEMIES"),
                    ("item", "ITEMS"),
                    ("special", "SPECIAL")
                ]

                for category_key, category_name in categories:
                    items_in_category = [
                        (entity_key, display_name)
                        for cat, entity_key, display_name in self.entity_types
                        if cat == category_key
                    ]

                    if items_in_category:
                        f.write(f"{category_name}:\n")
                        f.write("-" * 30 + "\n")

                        for entity_key, display_name in items_in_category:
                            variant_num = self.selected_variants[entity_key]
                            filename = f"{entity_key}{variant_num:02d}.png"
                            f.write(f"  {display_name:20s} -> {filename}\n")

                        f.write("\n")

                f.write("\n")
                f.write("To use these variants, update graphics_tiles.json\n")
                f.write("with the corresponding filenames.\n")

            logging.info(f"Exported graphics selections to {output_file}")

        except Exception as e:
            logging.error(f"Failed to export graphics selections: {e}")
