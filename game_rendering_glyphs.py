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
from game_rendering_base import MapRendererBase
from game_color_manager import ColorManager
from game_unicode_chars import GameGlyphs
from game_color_thresholds import ColorThresholdManager


class GlyphsMapRenderer(MapRendererBase):
    """Renders the game map and entities in ASCII/glyph mode."""

    def render_map(self, console: tcod.console.Console, game):
        """Render the complete game map."""
        try:
            camera_offset = self._calculate_camera_offset(game.player, game)
            vision_range = game.player.get_vision_range()
            
            # Render in layers for proper z-ordering
            self._render_terrain(console, game, camera_offset, vision_range)
            self._render_vision_overlays(console, game, camera_offset, vision_range)
            self._render_movement_prediction(console, game, camera_offset, vision_range)
            self._render_autowalk_path(console, game, camera_offset)
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
                console_y = viewport_y + GameConfig.STATUS_BAR_HEIGHT()

                if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    # Check if player can see this position using TCOD FOV
                    if game.player.can_see_through_walls():
                        # Enhanced vision can see through walls within range
                        distance = game.player.position.distance_to(world_pos)
                        can_see = distance <= vision_range
                    else:
                        # Use cached FOV for massive performance gain
                        can_see = (world_pos.x, world_pos.y) in game.visible_tiles

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
                # ♦ for cooling nodes, faded cyan
                cooling_color = ColorManager.get_terrain_variant_color("cooling_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.COOLING, fg=cooling_color, bg=Colors.BLACK)
            elif node_type == "cpu":
                # ♥ for CPU nodes, faded red
                cpu_color = ColorManager.get_terrain_variant_color("cpu_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.CPU_OVERLOAD, fg=cpu_color, bg=Colors.BLACK)
            elif node_type == "ghost":
                # ♠ for ghost nodes, faded purple
                ghost_color = ColorManager.get_terrain_variant_color("ghost_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.GHOST_MODE, fg=ghost_color, bg=Colors.BLACK)
            elif node_type == "gateway":
                # Gateway in memory - darker yellow
                gateway_dark = ColorManager.get_terrain_variant_color("gateway")
                render_char_safe(console, screen_x, screen_y, '>', fg=gateway_dark, bg=Colors.BLACK)
            return

        # Check for undiscovered special nodes (to prevent them rendering as blind spots)
        # Undiscovered nodes should appear as regular floor until seen
        if (game.game_map.is_cooling_node(world_pos) or
            game.game_map.is_cpu_recovery_node(world_pos) or
            game.game_map.is_ghost_node(world_pos)):
            # Render as floor - player hasn't discovered this node yet
            floor_explored = Colors.DIGITAL_FLOOR  # floor consolidated
            render_char_safe(console, screen_x, screen_y, GameGlyphs.FLOOR_EXPLORED, fg=floor_explored, bg=Colors.BLACK)
            return

        # Only render basic terrain in memory, not dynamic elements
        if game.game_map.is_wall(world_pos):
            # Smart wall system for remembered walls too
            wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
            wall_dark = ColorManager.get_terrain_variant_color("wall_dark")
            render_char_safe(console, screen_x, screen_y, wall_char, fg=wall_dark, bg=Colors.BLACK)
        elif game.game_map.is_blind_spot(world_pos):
            # ◘ (inverse bullet) for remembered blind spots
            blind_spot_remembered = Colors.VOID_PURPLE  # blind_spot consolidated
            render_char_safe(console, screen_x, screen_y, GameGlyphs.BLIND_SPOT, fg=blind_spot_remembered, bg=Colors.BLACK)
        else:
            # • (bullet) for remembered empty spaces
            floor_explored = Colors.DIGITAL_FLOOR  # floor consolidated
            render_char_safe(console, screen_x, screen_y, GameGlyphs.FLOOR_EXPLORED, fg=floor_explored, bg=Colors.BLACK)
    
    def _render_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game):
        """Render a single tile."""
        # SYMBOL CONVENTIONS:
        # - Letters (A-Z): Reserved for enemies only (Scanner=S, Patrol=P, Bot=B, etc.)
        # - Unicode characters: Used for everything else (walls, items, terrain, etc.)
        
        # Priority order for tile rendering
        if game.game_map.is_wall(world_pos):
            # Only render walls if they're within vision range (prevent distant walls from being visible)
            distance = game.player.position.distance_to(world_pos)
            if distance <= game.player.get_vision_range() + 1:  # +1 to show walls just outside range
                # Smart wall system - analyze neighbors to pick correct wall piece
                wall_char = self._get_smart_wall_character(game.game_map, world_pos.x, world_pos.y)
                render_char_safe(console, screen_x, screen_y, wall_char, fg=Colors.WALL, bg=Colors.BLACK)
            else:
                # Wall too far away - render as explored memory instead
                pass
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
                render_char_safe(console, screen_x, screen_y, GameGlyphs.COOLING, fg=Colors.CYAN, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                cooling_faded = ColorManager.get_terrain_variant_color("cooling_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.COOLING, fg=cooling_faded, bg=Colors.BLACK)
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
                render_char_safe(console, screen_x, screen_y, GameGlyphs.CPU_OVERLOAD, fg=Colors.RED, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                cpu_faded = ColorManager.get_terrain_variant_color("cpu_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.CPU_OVERLOAD, fg=cpu_faded, bg=Colors.BLACK)
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
                render_char_safe(console, screen_x, screen_y, GameGlyphs.GHOST_MODE, fg=Colors.ELECTRIC_PURPLE, bg=Colors.BLACK)
            elif is_discovered:
                # Faded color when discovered but not currently visible
                ghost_faded = ColorManager.get_terrain_variant_color("ghost_node")
                render_char_safe(console, screen_x, screen_y, GameGlyphs.GHOST_MODE, fg=ghost_faded, bg=Colors.BLACK)
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
            # § (section) for code fragments
            render_char_safe(console, screen_x, screen_y, GameGlyphs.SECTION, fg=actual_color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.exploit_pickups:
            try:
                exploit_item = game.game_map.exploit_pickups[(world_pos.x, world_pos.y)]
                if exploit_item.exploit_key in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                    exploit_category = exploit_def.category  # Fixed: was exploit_class, should be category
                    # Get color from config
                    try:
                        color_tuple = ColorManager.get_exploit_color(exploit_category)
                    except KeyError:
                        # Fallback to magenta if category not found
                        color_tuple = Colors.MAGENTA

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
            # ◙ (inverse circle) for permanent upgrades (different from movement prediction)
            render_char_safe(console, screen_x, screen_y, GameGlyphs.CIRCLE_DOT, fg=color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.story_fragments:
            # ♫ (double music note) for lore scraps with cycling colors
            fragment_color = self._get_story_fragment_color(game.turn)
            render_char_safe(console, screen_x, screen_y, GameGlyphs.STORY_FRAGMENT, fg=fragment_color, bg=Colors.BLACK)
        elif game.game_map.is_blind_spot(world_pos):
            # ◘ (inverse bullet) for blind spots
            render_char_safe(console, screen_x, screen_y, GameGlyphs.BLIND_SPOT, fg=Colors.GHOST_PURPLE, bg=Colors.BLACK)
        else:
            # • (bullet) for empty space
            render_char_safe(console, screen_x, screen_y, GameGlyphs.FLOOR_EXPLORED, fg=Colors.FLOOR, bg=Colors.BLACK)
    
    
    def _get_smart_wall_character(self, game_map, x: int, y: int) -> str:
        """Get the appropriate wall character based on neighboring walls."""
        # Check which directions have walls
        n = game_map.is_wall(Position(x, y - 1))  # North
        s = game_map.is_wall(Position(x, y + 1))  # South
        e = game_map.is_wall(Position(x + 1, y))  # East
        w = game_map.is_wall(Position(x - 1, y))  # West

        # Return Unicode box-drawing characters
        if n and s and e and w:
            return GameGlyphs.WALL_CROSS  # ┼ cross (4-way intersection)
        elif n and s and e and not w:
            return GameGlyphs.WALL_T_RIGHT  # ├ T pointing right
        elif n and s and not e and w:
            return GameGlyphs.WALL_T_LEFT  # ┤ T pointing left
        elif n and not s and e and w:
            return GameGlyphs.WALL_T_UP  # ┴ T pointing up
        elif not n and s and e and w:
            return GameGlyphs.WALL_T_DOWN  # ┬ T pointing down
        elif n and not s and e and not w:
            return GameGlyphs.WALL_BOTTOM_LEFT  # └ bottom-left corner
        elif n and not s and not e and w:
            return GameGlyphs.WALL_BOTTOM_RIGHT  # ┘ bottom-right corner
        elif not n and s and e and not w:
            return GameGlyphs.WALL_TOP_LEFT  # ┌ top-left corner
        elif not n and s and not e and w:
            return GameGlyphs.WALL_TOP_RIGHT  # ┐ top-right corner
        elif n and s and not e and not w:
            return GameGlyphs.WALL_VERTICAL  # │ vertical line
        elif not n and not s and e and w:
            return GameGlyphs.WALL_HORIZONTAL  # ─ horizontal line
        # Handle single-connection walls (stubs)
        elif n and not s and not e and not w:
            return GameGlyphs.WALL_VERTICAL  # │ vertical stub pointing up
        elif not n and s and not e and not w:
            return GameGlyphs.WALL_VERTICAL  # │ vertical stub pointing down
        elif not n and not s and e and not w:
            return GameGlyphs.WALL_HORIZONTAL  # ─ horizontal stub pointing right
        elif not n and not s and not e and w:
            return GameGlyphs.WALL_HORIZONTAL  # ─ horizontal stub pointing left
        # Isolated wall
        else:
            return GameGlyphs.WALL_ISOLATED  # ■ small solid square

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

        # Define our cyberspace color palette for cycling
        cyberspace_colors = [
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
        color_index = (turn // 5) % len(cyberspace_colors)
        base_color = cyberspace_colors[color_index]

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

        Vision indicators are hidden on blind spots unless the enemy is adjacent to that blind spot,
        since enemies can only see players in blind spots when adjacent (grid distance <= 1).
        """
        # Enemies have full vision range regardless of whether they're in a blind spot
        # The blind spot mechanic only affects whether they can see players IN blind spots
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

                    # Skip blind spots - enemies can't see into blind spots unless adjacent
                    world_pos = Position(world_x, world_y)
                    if game_map.is_blind_spot(world_pos):
                        # Show vision marker if enemy is adjacent to this blind spot
                        enemy_pos = Position(enemy.x, enemy.y)
                        if enemy_pos.grid_distance_to(world_pos) > 1:
                            continue

                    screen_x = world_x - camera_offset.x
                    screen_y = world_y - camera_offset.y + 1

                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        if use_graphics and renderer:
                            # Graphics mode: Draw corner brackets
                            tile_rect = self._get_tile_rect(screen_x, screen_y)
                            self._draw_corner_brackets(renderer, tile_rect, overlay_color, bracket_size=GameConfig.VISION_BRACKET_SIZE())
                        else:
                            # Classic mode: Highlight background
                            self._safely_overlay_tile(console, screen_x, screen_y, overlay_color)
    
    def _safely_overlay_tile(self, console: tcod.console.Console, x: int, y: int, bg_color: Tuple[int, int, int]):
        """Safely overlay background color on existing tile."""
        try:
            # CRITICAL: TCOD arrays use [y, x] indexing, not [x, y]!
            current_char = console.ch[y, x]
            if current_char != ord(' '):  # Don't overlay fog of war
                current_fg = console.fg[y, x]
                if hasattr(current_fg, '__iter__') and len(current_fg) >= 3:
                    fg_tuple = tuple(current_fg[:3])
                    render_char_safe(console, x, y, chr(current_char), fg=fg_tuple, bg=bg_color)
        except (IndexError, ValueError) as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            # Silent fail for overlay errors, but could log line_no if needed for debugging
            pass
    
    def _render_movement_prediction(self, console: tcod.console.Console, game, camera_offset: Position, vision_range: int, use_graphics=False):
        """Render next 3 predicted moves for all moving enemies using directional arrows."""
        threat_scan_active = game.game_state.threat_scan_turns > 0

        # Get renderer for graphics mode
        renderer = None
        if use_graphics and self.context and hasattr(self.context, 'sdl_renderer'):
            renderer = self.context.sdl_renderer

        visible_count = 0
        for enemy in game.enemies:
            # Skip disabled enemies - they can't move
            if enemy.disabled_turns > 0:
                continue

            # Show patrol routes for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

            # Show movement intentions for all visible enemies (permanent ability)
            if can_see_enemy:
                visible_count += 1
                next_positions = game.get_enemy_next_positions(enemy, 3)

                # Use enemy's current position as the "from" position for the first arrow
                prev_pos = enemy.position

                for i, point in enumerate(next_positions):
                    # Skip rendering arrow if there's a character (player or enemy) at this position
                    # Don't draw arrows over the player or other enemies
                    player_at_point = (game.player.x == point.x and game.player.y == point.y)
                    enemy_at_point = any(e.position.x == point.x and e.position.y == point.y for e in game.enemies)

                    if player_at_point or enemy_at_point:
                        prev_pos = point  # Update prev_pos for next iteration
                        continue

                    screen_x = point.x - camera_offset.x
                    screen_y = point.y - camera_offset.y + 1
                    in_viewport = (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                                   1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT)

                    if in_viewport:
                        try:
                            # Get enemy color based on alert state (yellow/orange/red/blue)
                            enemy_color = enemy.get_color()

                            # Apply dimming based on position in queue (1st=full, 2nd=75%, 3rd=50%)
                            if i == 0:
                                dimming_factor = 1.0  # Full brightness
                            elif i == 1:
                                dimming_factor = 0.75  # Medium brightness
                            else:
                                dimming_factor = 0.5  # Dim

                            # Apply dimming to enemy color
                            dimmed_color = tuple(int(c * dimming_factor) for c in enemy_color)

                            # Safety check - ensure color is visible
                            if sum(dimmed_color) < 30:  # Too dark
                                dimmed_color = (100, 100, 100)  # Fallback gray

                            # Use black background for arrows (don't preserve vision overlay)
                            bg_color = Colors.BLACK

                            # Get arrow character
                            arrow_char = prev_pos.arrow_char_to(point)
                        except Exception as e:
                            logging.error(f"Error setting up arrow: {e}")
                            continue  # Skip this arrow

                        # Render directional arrow
                        try:
                            render_char_safe(console, screen_x, screen_y, arrow_char, fg=dimmed_color, bg=bg_color)
                        except Exception as e:
                            logging.error(f"Failed to render arrow at ({screen_x},{screen_y}): {e}")
                            # Try fallback rendering with simple values
                            try:
                                render_char_safe(console, screen_x, screen_y, '?', fg=(255, 255, 0), bg=(0, 0, 0))
                            except:
                                pass  # Give up if even fallback fails

                    # Update prev_pos for next arrow
                    prev_pos = point

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
                    gateway_dark = ColorManager.get_terrain_variant_color("gateway_dark")
                    render_char_safe(console, screen_x, screen_y, '>', fg=gateway_dark, bg=Colors.BLACK)
    
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

    def _render_autowalk_path(self, console: tcod.console.Console, game, camera_offset: Position):
        """Render the planned auto-walk path with visual indicators."""
        if not game.autowalk.is_active():
            return

        # Get remaining path positions
        path = game.autowalk.get_remaining_path()
        if not path:
            return

        # Use cyan color for auto-walk path (distinct from enemy movement prediction)
        path_color = ColorManager.get("path_colors", "path_cyan")

        # Render each position in the path
        for i, pos in enumerate(path):
            if self._is_in_viewport(pos.x, pos.y, camera_offset):
                console_x, console_y = self._world_to_console(pos.x, pos.y, camera_offset)

                # Use different symbols for visual clarity
                if i == len(path) - 1:
                    # Destination: use 'X' marker
                    symbol = 'X'
                    color = ColorManager.get("path_colors", "path_bright")
                else:
                    # Path steps: use '·' (small dot)
                    symbol = '·'
                    color = path_color

                render_char_safe(console, console_x, console_y, symbol, fg=color, bg=Colors.BLACK)

    def _render_player(self, console: tcod.console.Console, game, camera_offset: Position):
        """Render the player character."""
        if self._is_in_viewport(game.player.x, game.player.y, camera_offset):
            console_x, console_y = self._world_to_console(game.player.x, game.player.y, camera_offset)
            player_color = self._get_player_color(game.player)
            # ☺ (smiley face)
            try:
                render_char_safe(console, console_x, console_y, GameGlyphs.PLAYER, fg=player_color, bg=Colors.BLACK)
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
        # Use centralized color threshold manager for consistent player colors
        return ColorThresholdManager.get_player_color(player)
    
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
                self._render_targeting_area(console, cursor_pos, exploit.effect_radius, camera_offset)
    
    def _render_targeting_range(self, console: tcod.console.Console, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator."""
        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                if dx*dx + dy*dy <= range_val*range_val:
                    range_screen_x = center.x - camera_offset.x + dx
                    range_screen_y = center.y - camera_offset.y + dy + 1
                    
                    if (0 <= range_screen_x < GameConfig.GAME_AREA_WIDTH() and
                        1 <= range_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        range_color = ColorManager.get_targeting_color("range_overlay")
                        self._safely_overlay_tile(console, range_screen_x, range_screen_y, range_color)
    
    def _render_targeting_area(self, console: tcod.console.Console, center: Position, radius: int, camera_offset: Position):
        """
        Render area effect indicator for area targeting.

        Uses grid distance (Chebyshev) to match gameplay mechanics.
        For radius 1: 3x3 area, radius 2: 5x5 area, etc.
        """
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Use grid distance (Chebyshev) - matches gameplay
                if max(abs(dx), abs(dy)) <= radius:
                    area_screen_x = center.x - camera_offset.x + dx
                    area_screen_y = center.y - camera_offset.y + dy + 1

                    if (0 <= area_screen_x < GameConfig.GAME_AREA_WIDTH() and
                        1 <= area_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        # Use a brighter overlay to distinguish from range indicator
                        area_color = ColorManager.get_targeting_color("area_overlay")
                        self._safely_overlay_tile(console, area_screen_x, area_screen_y, area_color)

    # ===== GRAPHICS MODE SPRITE RENDERING =====

