#!/usr/bin/env python3
"""
Game Rendering Glyphs
ASCII/console-based map rendering.
"""

import tcod
import logging
import traceback
import math
from typing import Tuple

from game_config import GameConfig, GameBalance
from game_entities import Position, Colors, EnemyState, TargetingMode, ensure_color_tuple
from game_data import GameData, GameUpgrades
from data_loading import DataLoader
from game_ui import render_char_safe


class GlyphsMapRenderer:
    """Renders the game map in ASCII/glyph mode."""

    def __init__(self, settings=None):
        """
        Initialize GlyphsMapRenderer.

        Args:
            settings: GameSettings instance for accessing graphics_mode
        """
        self.settings = settings

    """Renders the game map and entities."""

    def __init__(self, tile_manager=None, context=None, settings=None):
        """
        Initialize MapRenderer with optional graphics support.

        Args:
            tile_manager: TileManager instance for sprite loading (None for glyph mode)
            context: TCOD context with SDL renderer (None for glyph mode)
            settings: GameSettings instance for accessing graphics_mode
        """
        self.tile_manager = tile_manager
        self.context = context
        self.settings = settings

    def _should_use_graphics(self):
        """Check if graphics mode is available and should be used."""
        return (self.tile_manager is not None and
                self.context is not None and
                hasattr(self.context, 'sdl_renderer') and
                self.context.sdl_renderer is not None)

    def _get_graphics_mode(self):
        """Get current graphics mode from settings."""
        if self.settings:
            return self.settings.graphics_mode
        return "glyph"

    def _world_to_console(self, world_x: int, world_y: int, camera_offset: Position) -> Tuple[int, int]:
        """
        Convert world coordinates to console coordinates based on viewport.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            camera_offset: Camera offset position

        Returns:
            Tuple of (console_x, console_y) or None if out of viewport
        """
        # Calculate viewport position
        viewport_x = world_x - camera_offset.x
        viewport_y = world_y - camera_offset.y

        # Console position accounts for status bar at row 0
        console_x = viewport_x
        console_y = viewport_y + 1

        return (console_x, console_y)

    def _is_in_viewport(self, world_x: int, world_y: int, camera_offset: Position) -> bool:
        """
        Check if world coordinates are within the current viewport.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            camera_offset: Camera offset position

        Returns:
            True if position is in viewport
        """
        graphics_mode = self._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        viewport_x = world_x - camera_offset.x
        viewport_y = world_y - camera_offset.y

        return (0 <= viewport_x < viewport_width and
                0 <= viewport_y < viewport_height)

    def _grid_to_pixel(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """
        Convert grid coordinates to pixel coordinates.

        Args:
            screen_x: Grid x coordinate (0 to GAME_AREA_WIDTH)
            screen_y: Grid y coordinate (0 to SCREEN_HEIGHT)

        Returns:
            Tuple of (pixel_x, pixel_y)
        """
        if not self.tile_manager:
            return (0, 0)

        pixel_x = screen_x * self.tile_manager.tile_width
        pixel_y = screen_y * self.tile_manager.tile_height
        return (pixel_x, pixel_y)

    def _get_tile_rect(self, screen_x: int, screen_y: int) -> Tuple[int, int, int, int]:
        """
        Get pixel rectangle for a tile at grid coordinates.

        Args:
            screen_x: Grid x coordinate
            screen_y: Grid y coordinate

        Returns:
            Tuple of (x, y, width, height) in pixels for SDL rendering
        """
        if not self.tile_manager:
            return (0, 0, 0, 0)

        px, py = self._grid_to_pixel(screen_x, screen_y)
        return (px, py, self.tile_manager.tile_width, self.tile_manager.tile_height)

    def render_map(self, console: tcod.console.Console, game):
        """Render the complete game map."""
        try:
            camera_offset = self._calculate_camera_offset(game.player)
            vision_range = game.player.get_vision_range()
            
            # Render in layers for proper z-ordering
            self._render_terrain(console, game, camera_offset, vision_range)
            self._render_vision_overlays(console, game, camera_offset, vision_range)
            self._render_patrol_routes(console, game, camera_offset, vision_range)
            self._render_gateway(console, game, camera_offset, vision_range)
            self._render_enemies(console, game, camera_offset, vision_range)
            self._render_player(console, game, camera_offset)
            self._render_targeting_cursor(console, game, camera_offset)
            
        except Exception as e:
            # Fallback error display
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            error_msg = f"Map Error: {str(e)[:50]} (line {line_no})"
            render_char_safe(console, 1, 1, error_msg, fg=Colors.RED, bg=Colors.BLACK)
            # Also log to console and file
            logging.error(f"Map rendering error: {e}")
            logging.error(traceback.format_exc())
    
    def _calculate_camera_offset(self, player) -> Position:
        """
        Calculate camera offset to center on player.

        Uses viewport dimensions based on graphics mode - smaller viewport
        in graphics mode for larger sprite appearance.
        """
        graphics_mode = self._get_graphics_mode()

        # Get viewport dimensions (tiles visible, not console grid size)
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        # Center camera on player within the viewport
        camera_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                             player.x - viewport_width // 2))
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                             player.y - viewport_height // 2))

        return Position(camera_x, camera_y)
    
    def _render_terrain(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render basic terrain (floors, walls, items)."""
        graphics_mode = self._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        for viewport_x in range(viewport_width):
            for viewport_y in range(viewport_height):
                # World position from viewport coordinates
                world_pos = Position(viewport_x + camera_offset.x, viewport_y + camera_offset.y)

                # Console position (account for status bar at row 0)
                console_x = viewport_x
                console_y = viewport_y + 1

                if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    # Check if player can see this position using TCOD FOV
                    if game.player.can_see_through_walls():
                        # Enhanced vision can see through walls within range
                        distance = game.player.position.distance_to(world_pos)
                        can_see = distance <= vision_range
                    else:
                        # Use TCOD FOV system for proper corner visibility
                        can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

                    # Check if this tile has been explored (memory system)
                    explored = (world_pos.x, world_pos.y) in game.game_map.explored_tiles

                    if can_see:
                        self._render_tile(console, console_x, console_y, world_pos, game)
                    elif explored:
                        # Render remembered tile with dimmed colors
                        self._render_remembered_tile(console, console_x, console_y, world_pos, game)
                    else:
                        # Fog of war
                        render_char_safe(console, console_x, console_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
                else:
                    # Outside map bounds
                    render_char_safe(console, console_x, console_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
    
    def _render_remembered_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game):
        """Render a tile from memory with dimmed neon colors."""
        # Check if this position has a revealed special node
        pos_tuple = (world_pos.x, world_pos.y)
        if pos_tuple in game.game_state.revealed_special_nodes:
            node_type = game.game_state.revealed_special_nodes[pos_tuple]
            if node_type == "cooling":
                # Position 4 = ♦ for cooling nodes, faded cyan
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=(0, 120, 120), bg=Colors.BLACK)
            elif node_type == "cpu":
                # Position 3 = ♥ for CPU nodes, faded red
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=(120, 0, 0), bg=Colors.BLACK)
            elif node_type == "ghost":
                # Position 6 = ♠ for ghost nodes, faded purple
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=(80, 0, 120), bg=Colors.BLACK)
            elif node_type == "gateway":
                # Gateway in memory - darker yellow
                darker_yellow = (180, 150, 0)
                render_char_safe(console, screen_x, screen_y, '>', fg=darker_yellow, bg=Colors.BLACK)
            return
        
        # Only render basic terrain in memory, not dynamic elements
        if game.game_map.is_wall(world_pos):
            # Smart wall system for remembered walls too
            wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[wall_char]), fg=(60, 70, 90), bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            # Position 8 = ◘ (inverse bullet) for remembered shadows
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[8]), fg=(50, 20, 80), bg=Colors.BLACK)
        else:
            # Position 7 = • (bullet) for remembered empty spaces
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[7]), fg=(90, 90, 130), bg=Colors.BLACK)
    
    def _render_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game):
        """Render a single tile."""
        # SYMBOL CONVENTIONS:
        # - Letters (A-Z): Reserved for enemies only (Scanner=S, Patrol=P, Bot=B, etc.)
        # - CP437 symbols: Used for everything else (walls, items, terrain, etc.)
        # - NO unicode characters allowed for terminal compatibility
        
        # Priority order for tile rendering
        if game.game_map.is_wall(world_pos):
            # Smart wall system - analyze neighbors to pick correct wall piece
            wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[wall_char]), fg=Colors.WALL, bg=Colors.BLACK)
        elif game.game_map.is_cooling_node(world_pos):
            # Position 4 = ♦ (diamond) 
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "cooling"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=Colors.CYAN, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=(0, 120, 120), bg=Colors.BLACK)
        elif game.game_map.is_cpu_recovery_node(world_pos):
            # Position 3 = ♥ (heart)
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "cpu"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=Colors.RED, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=(120, 0, 0), bg=Colors.BLACK)
        elif game.game_map.is_ghost_node(world_pos):
            # Position 6 = ♠ (spade)
            pos_tuple = (world_pos.x, world_pos.y)
            is_currently_visible = (game.player.position.distance_to(world_pos) <= game.player.get_vision_range() and 
                                   game.game_map.has_line_of_sight(game.player.position, world_pos))
            is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and 
                           pos_tuple in game.game_state.revealed_special_nodes)
            
            if is_currently_visible:
                # Full color when currently visible - auto-discover when seen
                if not is_discovered:
                    if not hasattr(game.game_state, 'revealed_special_nodes'):
                        game.game_state.revealed_special_nodes = {}
                    game.game_state.revealed_special_nodes[pos_tuple] = "ghost"
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=(80, 0, 120), bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.code_hacks:
            patch = game.game_map.code_hacks[(world_pos.x, world_pos.y)]
            # Map patch color names to actual color tuples
            color_map = {
                'crimson': Colors.CRIMSON,
                'azure': Colors.AZURE,
                'emerald': Colors.EMERALD,
                'golden': Colors.GOLDEN,
                'violet': Colors.VIOLET,
                'silver': Colors.SILVER
            }
            # Handle color_name (should always be string)
            if isinstance(patch.color_name, str):
                actual_color = color_map.get(patch.color_name.lower(), Colors.WHITE)
            else:
                # This should never happen, but fallback to white
                logging.warning(f"CodeHack color_name is not string: {patch.color_name} (type: {type(patch.color_name)})")
                actual_color = Colors.WHITE
            # Position 21 = § (section) for code fragments  
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[21]), fg=actual_color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.exploit_pickups:
            try:
                exploit_item = game.game_map.exploit_pickups[(world_pos.x, world_pos.y)]
                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    exploit_category = exploit_def.category  # Fixed: was exploit_class, should be category
                    # Get color from config, fallback to magenta
                    from data_loading import DataLoader
                    config = DataLoader.load_config()
                    exploit_colors = config.get("colors", {}).get("exploits", {})
                    color_data = exploit_colors.get(exploit_category, [255, 20, 255])
                    
                    # Validate color data and convert to tuple
                    color_tuple = ensure_color_tuple(color_data)
                    
                    render_char_safe(console, screen_x, screen_y, '&', fg=color_tuple, bg=Colors.BLACK)
                else:
                    logging.error(f"Unknown exploit key: {exploit_item.exploit_key}")
                    render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
            except AttributeError as e:
                logging.error(f"ExploitDefinition attribute error at {world_pos}: {e}")
                logging.error(f"Available attributes: {dir(exploit_def) if 'exploit_def' in locals() else 'exploit_def not defined'}")
                logging.error(traceback.format_exc())
                # Fallback to default magenta color - don't change appearance due to errors
                render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
            except Exception as e:
                logging.error(f"Unexpected error rendering exploit at {world_pos}: {e}")
                logging.error(traceback.format_exc())
                # Fallback to default magenta color - don't change appearance due to errors
                render_char_safe(console, screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.permanent_upgrades:
            upgrade_key = game.game_map.permanent_upgrades[(world_pos.x, world_pos.y)]
            upgrade = GameUpgrades.UPGRADES[upgrade_key]
            # upgrade.color is already a tuple, use it directly
            color = ensure_color_tuple(upgrade.color)
            # Position 10 = ◙ (inverse circle) for permanent upgrades (different from movement prediction)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[10]), fg=color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.story_fragments:
            # Position 14 = ♫ (double music note) for lore scraps with cycling colors
            fragment_color = self._get_story_fragment_color(game.turn)
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[14]), fg=fragment_color, bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            # Position 8 = ◘ (inverse bullet) for shadows
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[8]), fg=(80, 40, 120), bg=Colors.BLACK)
        else:
            # Position 7 = • (bullet) for empty space
            render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[7]), fg=Colors.FLOOR, bg=Colors.BLACK)
    
    
    def _get_smart_wall_character(self, game_map, x: int, y: int) -> int:
        """Get the appropriate wall character based on neighboring walls."""
        # Check which directions have walls
        n = game_map.is_wall(Position(x, y - 1))  # North
        s = game_map.is_wall(Position(x, y + 1))  # South  
        e = game_map.is_wall(Position(x + 1, y))  # East
        w = game_map.is_wall(Position(x - 1, y))  # West
        
        # Use proper box-drawing characters from game config
        if n and s and e and w:
            return 197  # ┼ cross (4-way intersection)
        elif n and s and e and not w:
            return 195  # ├ T pointing right  
        elif n and s and not e and w:
            return 180  # ┤ T pointing left
        elif n and not s and e and w:
            return 193  # ┴ T pointing up
        elif not n and s and e and w:
            return 194  # ┬ T pointing down
        elif n and not s and e and not w:
            return 192  # └ bottom-left corner
        elif n and not s and not e and w:
            return 217  # ┘ bottom-right corner
        elif not n and s and e and not w:
            return 218  # ┌ top-left corner
        elif not n and s and not e and w:
            return 191  # ┐ top-right corner
        elif n and s and not e and not w:
            return 179  # │ vertical line
        elif not n and not s and e and w:
            return 196  # ─ horizontal line
        # Handle single-connection walls (stubs)
        elif n and not s and not e and not w:
            return 179  # │ vertical stub pointing up
        elif not n and s and not e and not w:
            return 179  # │ vertical stub pointing down  
        elif not n and not s and e and not w:
            return 196  # ─ horizontal stub pointing right
        elif not n and not s and not e and w:
            return 196  # ─ horizontal stub pointing left
        # Isolated wall - use a different character instead of solid block
        else:
            return 254  # ■ small solid square instead of full block

    def _get_upgrade_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple for permanent upgrade."""
        color_map = {
            'BRIGHT_BLUE': Colors.ELECTRIC_BLUE,
            'BRIGHT_GREEN': Colors.ACID_GREEN, 
            'BRIGHT_CYAN': Colors.CYAN
        }
        return color_map.get(color_name, Colors.WHITE)

    def _get_story_fragment_color(self, turn: int) -> Tuple[int, int, int]:
        """Get cycling color for story fragment based on game turn."""
        import math

        # Define our cyberpunk color palette for cycling
        cyberpunk_colors = [
            Colors.ELECTRIC_BLUE,    # Electric blue
            Colors.ELECTRIC_PURPLE,  # Electric purple
            Colors.ACID_GREEN,       # Acid green
            Colors.YELLOW,           # Golden yellow
            Colors.CRIMSON,          # Crimson red
            Colors.CYAN,             # Cyan
            Colors.VIOLET,           # Violet
            Colors.EMERALD           # Emerald green
        ]

        # Cycle through colors every 5 turns for a nice pulsing effect
        color_index = (turn // 5) % len(cyberpunk_colors)
        base_color = cyberpunk_colors[color_index]

        # Add a subtle brightness pulse within each color phase
        pulse_phase = (turn % 5) / 5.0
        pulse_intensity = 0.7 + 0.3 * math.sin(pulse_phase * 2 * math.pi)

        # Apply the pulse to the color brightness
        pulsed_color = tuple(int(c * pulse_intensity) for c in base_color)

        return pulsed_color

    def _render_vision_overlays(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int, use_graphics=False):
        """Render enemy vision range overlays."""
        if game.player.is_invisible():
            return

        threat_scan_active = game.game_state.threat_scan_turns > 0

        # Get renderer for graphics mode
        renderer = None
        if use_graphics and self.context and hasattr(self.context, 'sdl_renderer'):
            renderer = self.context.sdl_renderer

        for enemy in game.enemies:
            if enemy.disabled_turns > 0:
                continue

            # Show vision overlays for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

            if can_see_enemy or threat_scan_active:
                overlay_color = self._get_vision_overlay_color(enemy.state, use_graphics)

                # If revealed by threat scan, make overlay more translucent
                if threat_scan_active and not can_see_enemy:
                    overlay_color = tuple(c // 2 for c in overlay_color)  # Make it dimmer

                self._render_enemy_vision_range(console, enemy, camera_offset, overlay_color, game.game_map, use_graphics, renderer)

    def _get_vision_overlay_color(self, enemy_state: EnemyState, use_graphics=False) -> Tuple[int, int, int]:
        """Get vision overlay color based on enemy state.

        In graphics mode, returns brighter colors for better visibility.
        In classic mode, returns standard darkened colors.
        """
        if use_graphics:
            # Use full-brightness enemy colors for graphics mode brackets
            if enemy_state == EnemyState.HOSTILE:
                return Colors.ENEMY_HOSTILE
            elif enemy_state == EnemyState.ALERT:
                return Colors.ENEMY_ALERT
            else:
                return Colors.ENEMY_UNAWARE
        else:
            # Use standard darkened colors for classic mode
            if enemy_state == EnemyState.HOSTILE:
                return Colors.VISION_HOSTILE
            elif enemy_state == EnemyState.ALERT:
                return Colors.VISION_ALERT
            else:
                return Colors.VISION_UNAWARE
    
    def _render_enemy_vision_range(self, console: tcod.console.Console, enemy, camera_offset: Position, overlay_color: Tuple[int, int, int], game_map, use_graphics=False, renderer=None):
        """
        Render vision range for a single enemy.

        In classic mode: Highlights tile backgrounds with overlay_color
        In graphics mode: Draws corner brackets with overlay_color
        """
        # Enemies have full vision range regardless of whether they're in shadow
        # The shadow mechanic only affects whether they can see players IN shadow
        actual_vision_range = enemy.type_data.vision

        for dx in range(-actual_vision_range, actual_vision_range + 1):
            for dy in range(-actual_vision_range, actual_vision_range + 1):
                # Use Euclidean distance to match the actual trace_level logic
                if dx*dx + dy*dy <= actual_vision_range*actual_vision_range:
                    world_x = enemy.x + dx
                    world_y = enemy.y + dy

                    # Skip the enemy's own tile (no redundant indicators)
                    if world_x == enemy.x and world_y == enemy.y:
                        continue

                    screen_x = world_x - camera_offset.x
                    screen_y = world_y - camera_offset.y + 1

                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        if use_graphics and renderer:
                            # Graphics mode: Draw corner brackets
                            tile_rect = self._get_tile_rect(screen_x, screen_y)
                            self._draw_corner_brackets(renderer, tile_rect, overlay_color, bracket_size=4)
                        else:
                            # Classic mode: Highlight background
                            self._safely_overlay_tile(console, screen_x, screen_y, overlay_color)
    
    def _safely_overlay_tile(self, console: tcod.console.Console, x: int, y: int, bg_color: Tuple[int, int, int]):
        """Safely overlay background color on existing tile."""
        try:
            current_char = console.ch[x, y]
            if current_char != ord(' '):  # Don't overlay fog of war
                current_fg = console.fg[x, y]
                if hasattr(current_fg, '__iter__') and len(current_fg) >= 3:
                    fg_tuple = tuple(current_fg[:3])
                    render_char_safe(console, x, y, chr(current_char), fg=fg_tuple, bg=bg_color)
        except (IndexError, ValueError) as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            # Silent fail for overlay errors, but could log line_no if needed for debugging
            pass
    
    def _render_patrol_routes(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int, use_graphics=False):
        """Render next 3 predicted moves for all moving enemies."""
        threat_scan_active = game.game_state.threat_scan_turns > 0

        # Get renderer for graphics mode
        renderer = None
        if use_graphics and self.context and hasattr(self.context, 'sdl_renderer'):
            renderer = self.context.sdl_renderer

        visible_count = 0
        for enemy in game.enemies:
            # Show patrol routes for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

            # Show movement intentions for all visible enemies (permanent ability)
            if can_see_enemy:
                visible_count += 1
                next_positions = game.get_enemy_next_positions(enemy, 3)

                for i, point in enumerate(next_positions):
                    # Skip rendering movement prediction if there's an enemy at this position
                    enemy_at_point = any(e.position.x == point.x and e.position.y == point.y for e in game.enemies)
                    if enemy_at_point:
                        continue

                    screen_x = point.x - camera_offset.x
                    screen_y = point.y - camera_offset.y + 1
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        if use_graphics and renderer:
                            # Graphics mode: Render movement prediction sprite with color_mod
                            texture = self.tile_manager.get_tile("movement_prediction")
                            if texture:
                                tile_rect = self._get_tile_rect(screen_x, screen_y)
                                # Apply color based on position (brightness fades with distance)
                                if i == 0:
                                    texture.color_mod = (255, 255, 50)  # Brightest
                                elif i == 1:
                                    texture.color_mod = (240, 240, 30)  # Slightly dimmer
                                else:
                                    texture.color_mod = (220, 220, 20)  # Dimmest
                                renderer.copy(texture, dest=tile_rect)
                                # Reset color_mod
                                texture.color_mod = (255, 255, 255)
                            else:
                                logging.warning("_render_patrol_routes: movement_prediction texture not found!")
                        else:
                            # Classic mode: Preserve existing background color if present (e.g., vision overlay)
                            try:
                                current_bg = tuple(console.bg[screen_x, screen_y][:3])
                                # Use current background if it's not black, otherwise use black
                                bg_color = current_bg if current_bg != (0, 0, 0) else Colors.BLACK
                            except (IndexError, AttributeError):
                                bg_color = Colors.BLACK

                            # Ensure bg_color is a proper tuple to prevent TCOD ColorRGB errors
                            bg_color = ensure_color_tuple(bg_color)

                            # Large bright yellow shapes for all enemy movement prediction
                            if i == 0:
                                # Next immediate move - brightest and largest
                                color = (255, 255, 50)
                                # Position 9 = ○ (circle) for enemy move intent
                                symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                            elif i == 1:
                                # Second move - slightly dimmer but still bright
                                color = (240, 240, 30)
                                # Position 9 = ○ (circle) for enemy move intent
                                symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                            else:
                                # Third+ moves - still bright yellow
                                color = (220, 220, 20)
                                # Position 9 = ○ (circle) for enemy move intent
                                symbol = chr(tcod.tileset.CHARMAP_CP437[9])
                            render_char_safe(console, screen_x, screen_y, symbol, fg=color, bg=bg_color)

    def _render_gateway(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int, use_graphics=False):
        """Render the level gateway (classic mode only - graphics mode renders in sprite layer)."""
        if use_graphics:
            return
        if not game.game_map.gateway:
            return
        
        screen_x = game.game_map.gateway.x - camera_offset.x
        screen_y = game.game_map.gateway.y - camera_offset.y + 1
        
        if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and 
            1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            distance = game.player.position.distance_to(game.game_map.gateway)
            # Check if player can see the gateway (respecting walls)
            can_see = (distance <= vision_range and 
                      (game.player.can_see_through_walls() or 
                       game.game_map.has_line_of_sight(game.player.position, game.game_map.gateway)))
            
            if can_see:
                # Gateway is currently visible - render in full brightness and remember it
                render_char_safe(console, screen_x, screen_y, '>', fg=Colors.GATEWAY, bg=Colors.BLACK)
                # Add to memory system
                if not hasattr(game.game_state, 'revealed_special_nodes'):
                    game.game_state.revealed_special_nodes = {}
                gateway_pos = (game.game_map.gateway.x, game.game_map.gateway.y)
                game.game_state.revealed_special_nodes[gateway_pos] = "gateway"
            else:
                # Check if gateway was previously seen (in memory)
                gateway_pos = (game.game_map.gateway.x, game.game_map.gateway.y)
                if (hasattr(game.game_state, 'revealed_special_nodes') and 
                    gateway_pos in game.game_state.revealed_special_nodes and
                    game.game_state.revealed_special_nodes[gateway_pos] == "gateway"):
                    # Render remembered gateway in darker yellow
                    darker_yellow = (180, 150, 0)  # Darker version of gateway color
                    render_char_safe(console, screen_x, screen_y, '>', fg=darker_yellow, bg=Colors.BLACK)
    
    def _render_enemies(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int):
        """Render all enemies and their last known positions."""
        # First, render last known positions as ghosts
        for enemy_id, (position, turn_seen) in game.game_map.last_known_enemy_positions.items():
            # Find if this enemy is still alive and currently visible
            current_enemy = None
            currently_visible = False
            for enemy in game.enemies:
                if enemy.id == enemy_id:
                    current_enemy = enemy
                    if game.player.can_see_enemy(enemy, game.game_map):
                        currently_visible = True
                    break

            # Only show ghost if enemy is not currently visible and was seen recently
            from game_config import GameBalance
            if not currently_visible and turn_seen > game.turn - GameBalance.ENEMY_MEMORY_TURNS:
                if self._is_in_viewport(position.x, position.y, camera_offset):
                    console_x, console_y = self._world_to_console(position.x, position.y, camera_offset)
                    if current_enemy:
                        # Dimmed ghost of living enemy
                        ghost_color = tuple(c // 3 for c in current_enemy.get_color())
                        render_char_safe(console, console_x, console_y, '?', fg=ghost_color, bg=Colors.BLACK)

        # Then render currently visible enemies
        for enemy in game.enemies:
            if self._is_in_viewport(enemy.x, enemy.y, camera_offset):
                console_x, console_y = self._world_to_console(enemy.x, enemy.y, camera_offset)

                # Check if Threat Scan is active (shows all enemies)
                threat_scan_active = game.game_state.threat_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

                if can_see_enemy or threat_scan_active:
                    if threat_scan_active and not can_see_enemy:
                        # Threat scan reveals enemy with special highlighting
                        render_char_safe(console, console_x, console_y, enemy.type_data.symbol,
                                    fg=Colors.CYAN, bg=(20, 0, 20))  # Cyan text on dark purple bg
                    else:
                        # Normal enemy rendering
                        render_char_safe(console, console_x, console_y, enemy.type_data.symbol,
                                    fg=enemy.get_color(), bg=Colors.BLACK)

    def _render_enemy_movement_prediction(self, console: tcod.console.Console, enemy, camera_offset: Position, game):
        """Render faint indicators showing where enemy will move."""
        # Show up to 3 queued moves
        prediction_color = tuple(c // 2 for c in enemy.get_color())  # Half brightness

        for i, next_pos in enumerate(enemy.move_queue[:3]):
            screen_x = next_pos.x - camera_offset.x
            screen_y = next_pos.y - camera_offset.y + 1

            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                # Render dot or small indicator for predicted position
                # Use '·' (small dot) for movement prediction
                render_char_safe(console, screen_x, screen_y, '·', fg=prediction_color, bg=Colors.BLACK)

    def _render_player(self, console: tcod.console.Console, game, camera_offset: Position):
        """Render the player character."""
        if self._is_in_viewport(game.player.x, game.player.y, camera_offset):
            console_x, console_y = self._world_to_console(game.player.x, game.player.y, camera_offset)
            player_color = self._get_player_color(game.player)
            # Position 2 = ☻ (inverse smiley)
            try:
                render_char_safe(console, console_x, console_y, chr(tcod.tileset.CHARMAP_CP437[2]), fg=player_color, bg=Colors.BLACK)
            except Exception as e:
                import logging
                logging.error(f"PLAYER RENDER ERROR: {e}, color={player_color}")
                # Fallback to simple @ character
                render_char_safe(console, console_x, console_y, '@', fg=Colors.WHITE, bg=Colors.BLACK)
        else:
            # Only log when player is actually off screen - this shouldn't happen often
            import logging
            logging.error(f"PLAYER OFF SCREEN: world=({game.player.x}, {game.player.y}), "
                         f"camera=({camera_offset.x}, {camera_offset.y}), "
                         f"screen=({player_screen_x}, {player_screen_y})")
    
    def _get_player_color(self, player) -> Tuple[int, int, int]:
        """Get player color based on current state with priority: Red > Yellow > Green(virus) > Cyan(slow) > White(normal)."""
        # Priority 1: Critical status - Red
        if player.cpu < 30 or player.heat > 80 or player.trace_level > 75:
            return Colors.RED

        # Priority 2: Warning status - Yellow (invisibility takes precedence over other effects)
        if player.is_invisible():
            return Colors.YELLOW

        # Priority 3: Virus effect - Green
        if player.temporary_effects['virus_turns'] > 0:
            return Colors.DARK_GREEN

        # Priority 4: Slow effect - Cyan
        if player.temporary_effects['movement_slowed_turns'] > 0:
            return Colors.CYAN

        # Default: White
        return Colors.WHITE
    
    def _render_targeting_cursor(self, console: tcod.console.Console, game, camera_offset: Position, use_graphics=False):
        """Render targeting cursor and look mode cursor."""
        # Check if either targeting mode or look mode is active
        if not game.targeting_mode and not game.look_mode:
            return

        # Determine which cursor position and color to use
        if game.look_mode:
            cursor_pos = game.look_cursor_position
            cursor_color = Colors.CYAN  # Cyan for look mode
            char = 'X'
        else:  # targeting_mode
            cursor_pos = game.cursor_position
            cursor_color = Colors.RED  # Red for targeting mode
            char = 'X'

        # Get renderer for graphics mode
        renderer = None
        if use_graphics and self.context and hasattr(self.context, 'sdl_renderer'):
            renderer = self.context.sdl_renderer

        cursor_screen_x = cursor_pos.x - camera_offset.x
        cursor_screen_y = cursor_pos.y - camera_offset.y + 1

        if (0 <= cursor_screen_x < GameConfig.GAME_AREA_WIDTH() and
            1 <= cursor_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            if use_graphics and renderer:
                # Graphics mode: Render targeting cursor sprite
                texture = self.tile_manager.get_tile("targeting")
                if texture:
                    tile_rect = self._get_tile_rect(cursor_screen_x, cursor_screen_y)
                    # Tint based on mode (red for targeting, cyan for look)
                    texture.color_mod = cursor_color
                    renderer.copy(texture, dest=tile_rect)
                    # Reset color_mod
                    texture.color_mod = (255, 255, 255)
            else:
                # Classic mode: Render 'X' character
                render_char_safe(console, cursor_screen_x, cursor_screen_y, char, fg=cursor_color, bg=Colors.BLACK)

        # Show range indicator and area effect (only for targeting mode)
        if game.targeting_mode and game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            self._render_targeting_range(console, game.player.position, exploit.range, camera_offset)

            # Show area effect for AREA targeting mode
            if exploit.targeting == TargetingMode.AREA:
                self._render_targeting_area(console, cursor_pos, camera_offset)
    
    def _render_targeting_range(self, console: tcod.console.Console, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator."""
        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                if dx*dx + dy*dy <= range_val*range_val:
                    range_screen_x = center.x - camera_offset.x + dx
                    range_screen_y = center.y - camera_offset.y + dy + 1
                    
                    if (0 <= range_screen_x < GameConfig.GAME_AREA_WIDTH() and 
                        1 <= range_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, range_screen_x, range_screen_y, (40, 40, 40))
    
    def _render_targeting_area(self, console: tcod.console.Console, center: Position, camera_offset: Position):
        """Render 3x3 area effect indicator for area targeting."""
        for dx in range(-1, 2):  # -1, 0, 1 for 3x3 area
            for dy in range(-1, 2):
                area_screen_x = center.x - camera_offset.x + dx
                area_screen_y = center.y - camera_offset.y + dy + 1

                if (0 <= area_screen_x < GameConfig.GAME_AREA_WIDTH() and
                    1 <= area_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    # Use a brighter overlay to distinguish from range indicator
                    self._safely_overlay_tile(console, area_screen_x, area_screen_y, (60, 60, 20))

    # ===== GRAPHICS MODE SPRITE RENDERING =====

