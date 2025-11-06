#!/usr/bin/env python3
"""
Game Rendering Graphics
SDL sprite/texture-based rendering.
"""

import tcod
from tcod.sdl.render import BlendMode
import logging
import time
import math
from typing import Tuple

from game_config import GameConfig, GameBalance
from game_entities import Position, Colors, EnemyState, TargetingMode, ensure_color_tuple
from game_data import GameData, GameUpgrades
from data_loading import DataLoader
from game_rendering_base import MapRendererBase
from game_color_manager import ColorManager
from game_unicode_chars import GameGlyphs
from game_color_thresholds import ColorThresholdManager


class GraphicsMapRenderer(MapRendererBase):
    """Renders the game map using SDL sprites/textures."""

    def render_sprites_layer(self, game):
        """
        Render all sprite textures directly to SDL renderer (Layers 1 & 2).
        This includes terrain (floors, walls), items, and entities (player, enemies).

        Should only be called in graphics mode.
        """
        if not self._should_use_graphics():
            logging.warning("render_sprites_layer called but graphics mode not available")
            return

        renderer = self.context.sdl_renderer
        camera_offset = self._calculate_camera_offset(game.player, game)
        vision_range = game.player.get_vision_range()

        # LAYER 1: Render terrain sprites (floors, walls) for visible and remembered tiles
        graphics_mode = self._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        for viewport_x in range(viewport_width):
            for viewport_y in range(viewport_height):
                world_x = viewport_x + camera_offset.x
                world_y = viewport_y + camera_offset.y
                world_pos = Position(world_x, world_y)

                if not world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    continue

                # Console coordinates (for SDL rendering)
                console_x = viewport_x
                console_y = viewport_y + GameConfig.STATUS_BAR_HEIGHT()

                # Check visibility
                if game.player.can_see_through_walls():
                    distance = game.player.position.distance_to(world_pos)
                    can_see = distance <= vision_range
                else:
                    can_see = (world_pos.x, world_pos.y) in game.visible_tiles

                # Check if tile has been explored (for fog of war)
                explored = (world_x, world_y) in game.game_map.explored_tiles

                if can_see:
                    # Currently visible - full brightness
                    if game.game_map.is_wall(world_pos):
                        texture = self.tile_manager.get_tile("wall")
                    elif game.game_map.is_blind_spot(world_pos):
                        texture = self.tile_manager.get_tile("blind_spot")
                    else:
                        texture = self.tile_manager.get_tile("floor")

                    if texture:
                        tile_rect = self._get_tile_rect(console_x, console_y)
                        renderer.copy(texture, dest=tile_rect)
                    else:
                        # Fail fast on missing textures - better for debugging
                        if game.game_map.is_wall(world_pos):
                            terrain_type = "wall"
                        elif game.game_map.is_blind_spot(world_pos):
                            terrain_type = "blind_spot"
                        else:
                            terrain_type = "floor"
                        logging.error(f"CRITICAL: Missing required texture for {terrain_type} - graphics mode cannot continue")
                        raise RuntimeError(f"Missing required texture: {terrain_type}")
                elif explored:
                    # Explored but not currently visible - dimmed (fog of war)
                    # Check for undiscovered special nodes - render as floor instead of blind spot
                    has_undiscovered_node = (
                        (game.game_map.is_cooling_node(world_pos) or
                         game.game_map.is_cpu_recovery_node(world_pos) or
                         game.game_map.is_ghost_node(world_pos)) and
                        (not hasattr(game.game_state, 'revealed_special_nodes') or
                         (world_x, world_y) not in game.game_state.revealed_special_nodes)
                    )

                    if game.game_map.is_wall(world_pos):
                        texture = self.tile_manager.get_tile("wall")
                    elif has_undiscovered_node:
                        # Undiscovered special node - render as floor
                        texture = self.tile_manager.get_tile("floor")
                    elif game.game_map.is_blind_spot(world_pos):
                        texture = self.tile_manager.get_tile("blind_spot")
                    else:
                        texture = self.tile_manager.get_tile("floor")

                    if texture:
                        tile_rect = self._get_tile_rect(console_x, console_y)
                        # Dim the texture for fog of war effect
                        explored_tint = ColorManager.get_tint_color("explored")
                        normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                        texture.color_mod = explored_tint
                        renderer.copy(texture, dest=tile_rect)
                        # Reset color mod
                        texture.color_mod = normal_tint

        # LAYER 2A: Render item sprites with tinting for tintable items
        # Code hacks
        for (world_x, world_y), code_hack in game.game_map.code_hacks.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = (world_pos.x, world_pos.y) in game.visible_tiles

            if can_see and self._is_in_viewport(world_x, world_y, camera_offset):
                console_x, console_y = self._world_to_console(world_x, world_y, camera_offset)

                texture = self.tile_manager.get_tile("codehack")
                if texture:
                    # Apply tint if tintable
                    if self.tile_manager.is_tintable("codehack"):
                        # Map color name to RGB
                        color_map = {
                            'crimson': Colors.CRIMSON,
                            'azure': Colors.AZURE,
                            'emerald': Colors.EMERALD,
                            'golden': Colors.GOLDEN,
                            'violet': Colors.VIOLET,
                            'silver': Colors.SILVER
                        }
                        tint_color = color_map.get(code_hack.color_name.lower(), Colors.WHITE)
                        texture.color_mod = tint_color

                    tile_rect = self._get_tile_rect(console_x, console_y)
                    renderer.copy(texture, dest=tile_rect)

                    # Reset color mod
                    if self.tile_manager.is_tintable("codehack"):
                        normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                        texture.color_mod = normal_tint

        # Exploit pickups
        for (world_x, world_y), exploit_item in game.game_map.exploit_pickups.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = (world_pos.x, world_pos.y) in game.visible_tiles

            if can_see and self._is_in_viewport(world_x, world_y, camera_offset):
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                # All exploits use the same "exploit" sprite, tinted by category
                texture = self.tile_manager.get_tile("exploit")

                if texture:
                    # Apply tint if tintable
                    if self.tile_manager.is_tintable("exploit"):
                        if exploit_item.exploit_key in GameData.EXPLOITS:
                            exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                            exploit_category = exploit_def.category
                            # Get exploit color from config
                            tint_color = ColorManager.get_exploit_color(exploit_category)
                            texture.color_mod = tint_color

                    tile_rect = self._get_tile_rect(screen_x, screen_y)
                    renderer.copy(texture, dest=tile_rect)

                    # Reset color mod
                    if self.tile_manager.is_tintable("exploit"):
                        normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                        texture.color_mod = normal_tint

        # Resource nodes (cooling, CPU, ghost)
        for screen_x in range(viewport_width):
            for screen_y in range(viewport_height):
                world_x = screen_x + camera_offset.x
                world_y = screen_y + camera_offset.y
                world_pos = Position(world_x, world_y)
                # Account for status bar offset (sprites rendered at screen_y + 1)
                render_screen_y = screen_y + GameConfig.STATUS_BAR_HEIGHT()

                if not world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    continue

                # Check visibility and discovery state
                if game.player.can_see_through_walls():
                    distance = game.player.position.distance_to(world_pos)
                    can_see = distance <= vision_range
                else:
                    can_see = (world_pos.x, world_pos.y) in game.visible_tiles

                pos_tuple = (world_x, world_y)
                is_explored = pos_tuple in game.game_map.explored_tiles
                is_discovered = (hasattr(game.game_state, 'revealed_special_nodes') and
                               pos_tuple in game.game_state.revealed_special_nodes)

                # Determine node type
                node_type = None
                node_memory_key = None
                if game.game_map.is_cooling_node(world_pos):
                    node_type = "cooling_node"
                    node_memory_key = "cooling"
                elif game.game_map.is_cpu_recovery_node(world_pos):
                    node_type = "cpu_node"
                    node_memory_key = "cpu"
                elif game.game_map.is_ghost_node(world_pos):
                    node_type = "ghost_node"
                    node_memory_key = "ghost"

                if node_type:
                    if can_see:
                        # Currently visible - full brightness, auto-discover
                        if not is_discovered:
                            if not hasattr(game.game_state, 'revealed_special_nodes'):
                                game.game_state.revealed_special_nodes = {}
                            game.game_state.revealed_special_nodes[pos_tuple] = node_memory_key
                        texture = self.tile_manager.get_tile(node_type)
                        if texture:
                            tile_rect = self._get_tile_rect(screen_x, render_screen_y)
                            renderer.copy(texture, dest=tile_rect)
                    elif is_discovered and is_explored:
                        # Discovered and explored but not currently visible - dimmed
                        texture = self.tile_manager.get_tile(node_type)
                        if texture:
                            tile_rect = self._get_tile_rect(screen_x, render_screen_y)
                            # Dim the texture for fog of war effect
                            explored_tint = ColorManager.get_tint_color("explored")
                            normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                            texture.color_mod = explored_tint
                            renderer.copy(texture, dest=tile_rect)
                            # Reset color mod
                            texture.color_mod = normal_tint

        # Permanent upgrades
        for (world_x, world_y), upgrade_key in game.game_map.permanent_upgrades.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = (world_pos.x, world_pos.y) in game.visible_tiles

            if can_see and self._is_in_viewport(world_x, world_y, camera_offset):
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                # Map upgrade key to sprite name
                upgrade_sprite_map = {
                    'ram_boost': 'ram_upgrade',
                    'cpu_boost': 'cpu_upgrade',
                    'heat_boost': 'cooling_upgrade'
                }
                sprite_name = upgrade_sprite_map.get(upgrade_key)
                if sprite_name:
                    texture = self.tile_manager.get_tile(sprite_name)
                    if texture:
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)

        # Story fragments
        for (world_x, world_y), story_fragment in game.game_map.story_fragments.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = (world_pos.x, world_pos.y) in game.visible_tiles

            if can_see and self._is_in_viewport(world_x, world_y, camera_offset):
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                # Render story fragment sprite
                texture = self.tile_manager.get_tile("story_fragment")
                if texture:
                    tile_rect = self._get_tile_rect(screen_x, screen_y)
                    renderer.copy(texture, dest=tile_rect)

                    # Add rainbow pulsing ring around data fragment (uses outline box like enemies)
                    rainbow_color = self._get_rainbow_color()
                    pulse_intensity = self._get_pulse_intensity(pulse_speed=1.34)  # Consistent with enemy pulses
                    pulsed_rainbow = tuple(int(c * pulse_intensity) for c in rainbow_color)
                    self._draw_outline_box(renderer, tile_rect, pulsed_rainbow, thickness=2)

        # Gateway
        if game.game_map.gateway and self._is_in_viewport(game.game_map.gateway.x, game.game_map.gateway.y, camera_offset):
            screen_x = game.game_map.gateway.x - camera_offset.x
            screen_y = game.game_map.gateway.y - camera_offset.y + 1

            distance = game.player.position.distance_to(game.game_map.gateway)
            # Check if player can see the gateway (respecting walls)
            can_see = (distance <= vision_range and
                      (game.player.can_see_through_walls() or
                       game.game_map.has_line_of_sight(game.player.position, game.game_map.gateway)))

            if can_see:
                # Render gateway sprite
                texture = self.tile_manager.get_tile("gateway")
                if texture:
                    tile_rect = self._get_tile_rect(screen_x, screen_y)
                    renderer.copy(texture, dest=tile_rect)
                else:
                    logging.warning("render_sprites_layer: Gateway texture not found!")
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
                    # Render gateway sprite with dimmed appearance
                    texture = self.tile_manager.get_tile("gateway")
                    if texture:
                        dimmed_tint = ColorManager.get_tint_color("dimmed")
                        normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        # Use color_mod to dim the sprite (70% brightness for memory)
                        texture.color_mod = dimmed_tint
                        renderer.copy(texture, dest=tile_rect)
                        # Reset color_mod
                        texture.color_mod = normal_tint

        # LAYER 2B: Render entity sprites (enemies with HP tinting, player)
        # Enemies
        for enemy in game.enemies:
            if self._is_in_viewport(enemy.x, enemy.y, camera_offset):
                screen_x = enemy.x - camera_offset.x
                screen_y = enemy.y - camera_offset.y + 1

                threat_scan_active = game.game_state.threat_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

                if can_see_enemy or threat_scan_active:
                    # Get enemy type name for tile lookup
                    enemy_type_name = enemy.type_data.symbol  # Use symbol as identifier
                    # Map enemy symbols to type names
                    enemy_name_map = {
                        'S': 'Scanner',
                        'P': 'Patrol',
                        'B': 'Bot',
                        'H': 'Hunter',
                        'V': 'Virus',
                        'I': 'Inhibitor',
                        'F': 'Firewall',
                        'A': 'Admin Avatar'
                    }
                    enemy_type = enemy_name_map.get(enemy_type_name, enemy_type_name)
                    texture = self.tile_manager.get_tile(enemy_type)

                    if texture:
                        # Apply subtle HP-based damage tint (graphics mode only shows HP, not alert state)
                        damage_tint = enemy.get_graphics_tint()
                        texture.color_mod = damage_tint

                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)

                        # Reset color mod to prevent affecting other sprites
                        texture.color_mod = (255, 255, 255)

        # Player
        if self._is_in_viewport(game.player.x, game.player.y, camera_offset):
            player_screen_x = game.player.x - camera_offset.x
            player_screen_y = game.player.y - camera_offset.y + 1

            texture = self.tile_manager.get_tile("player")
            if texture:
                tile_rect = self._get_tile_rect(player_screen_x, player_screen_y)
                renderer.copy(texture, dest=tile_rect)

    def render_glyphs_layer(self, console: tcod.console.Console, game):
        """
        Render glyphs for elements that should appear over sprites.
        This includes special nodes, movement predictions, targeting cursor, etc.

        In graphics mode, renders directly to SDL using GlyphManager.
        In glyph mode, renders to console traditionally.
        """
        camera_offset = self._calculate_camera_offset(game.player, game)
        vision_range = game.player.get_vision_range()

        # Check if we're in graphics mode
        use_graphics = self._should_use_graphics() and self.glyph_manager is not None

        # Render special nodes as glyphs (only in glyph mode - sprites are used in graphics mode)
        if not use_graphics:
            for screen_x in range(GameConfig.GAME_AREA_WIDTH()):
                for screen_y in range(1, GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    world_x = screen_x + camera_offset.x
                    world_y = screen_y - 1 + camera_offset.y
                    world_pos = Position(world_x, world_y)

                    if not world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                        continue

                    # Check visibility
                    if game.player.can_see_through_walls():
                        distance = game.player.position.distance_to(world_pos)
                        can_see = distance <= vision_range
                    else:
                        can_see = (world_pos.x, world_pos.y) in game.visible_tiles

                    if can_see:
                        # Render special nodes
                        glyph = None
                        color = None

                        if game.game_map.is_cooling_node(world_pos):
                            glyph = ord(GameGlyphs.COOLING)  # Diamond
                            color = Colors.CYAN
                        elif game.game_map.is_cpu_recovery_node(world_pos):
                            glyph = ord(GameGlyphs.CPU_OVERLOAD)  # Heart
                            color = Colors.RED
                        elif game.game_map.is_ghost_node(world_pos):
                            glyph = ord(GameGlyphs.GHOST_MODE)  # Spade
                            color = Colors.ELECTRIC_PURPLE

                        if glyph and color:
                            # Glyph mode: render to console
                            console.rgb[screen_x, screen_y] = (glyph, color, (0, 0, 0))

    def render_overlay_layer(self, game):
        """
        Render overlay elements in graphics mode (vision ranges, movement prediction, targeting).
        This layer renders between status effects and console UI.
        """
        if not self._should_use_graphics():
            return

        camera_offset = self._calculate_camera_offset(game.player, game)
        vision_range = game.player.get_vision_range()

        # Render enemy vision ranges with corner brackets
        self._render_vision_overlays(game, camera_offset, vision_range)

        # Render enemy movement prediction sprites
        self._render_movement_prediction(game, camera_offset, vision_range)

        # Render targeting cursor for look mode or targeting mode
        self._render_targeting_cursor(game, camera_offset)

        # Render mouse hover highlight (if not in special modes)
        self._render_hover_highlight(game, camera_offset)

    def render_status_effects_layer(self, game):
        """
        Render colored status effect outlines over NON-TINTABLE sprites (Layer 2.5).
        This includes virus effects, slow effects, enemy state indicators, and other status indicators.

        Should only be called in graphics mode.
        """
        if not self._should_use_graphics():
            return

        renderer = self.context.sdl_renderer
        camera_offset = self._calculate_camera_offset(game.player, game)

        # Draw status effect outline for player if has status
        if self._is_in_viewport(game.player.x, game.player.y, camera_offset):
            player_screen_x = game.player.x - camera_offset.x
            player_screen_y = game.player.y - camera_offset.y + 1

            # Check for various player status effects (using centralized thresholds)
            status_color = None
            player_color = ColorThresholdManager.get_player_color(game.player)

            # Map the color from ColorThresholdManager to status colors for outline
            if player_color == Colors.RED:
                status_color = Colors.RED
            elif player_color == Colors.YELLOW:
                status_color = Colors.INVISIBLE
            elif player_color == Colors.VIRUS:
                status_color = Colors.VIRUS
            elif player_color == Colors.CYAN:
                status_color = Colors.SLOW

            if status_color:
                player_tile_rect = self._get_tile_rect(player_screen_x, player_screen_y)
                self._draw_outline_box(renderer, player_tile_rect, status_color, thickness=2)

        # Draw enemy state outlines (yellow/orange/red for normal/alert/hostile)
        for enemy in game.enemies:
            if self._is_in_viewport(enemy.x, enemy.y, camera_offset):
                screen_x = enemy.x - camera_offset.x
                screen_y = enemy.y - camera_offset.y + 1
                threat_scan_active = game.game_state.threat_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

                if can_see_enemy or threat_scan_active:
                    enemy_tile_rect = self._get_tile_rect(screen_x, screen_y)

                    # Get pulse intensity for pulsing animation (slowed down by 33%)
                    pulse_intensity = self._get_pulse_intensity(pulse_speed=1.34)

                    # Determine enemy state color
                    if enemy.disabled_turns > 0:
                        # Disabled enemies get blue outline (no pulsing for disabled)
                        outline_color = ColorManager.get_enemy_state_color("disabled")
                        self._draw_outline_box(renderer, enemy_tile_rect, outline_color, thickness=2)
                    else:
                        # Show enemy state with colored outline + pulsing
                        if enemy.state == EnemyState.HOSTILE:
                            base_color = ColorManager.get_enemy_state_color("hostile")
                        elif enemy.state == EnemyState.ALERT:
                            base_color = ColorManager.get_enemy_state_color("alert")
                        else:  # PATROLLING/IDLE
                            base_color = ColorManager.get_enemy_state_color("unaware")

                        # Apply pulse to color
                        outline_color = tuple(int(c * pulse_intensity) for c in base_color)

                        self._draw_outline_box(renderer, enemy_tile_rect, outline_color, thickness=1)

    def _draw_outline_box(self, renderer, rect: Tuple[int, int, int, int], color: Tuple[int, int, int], thickness: int = 1):
        """
        Draw a colored outline rectangle (not filled).

        SDL renderer's draw_rect fills, so we need to draw 4 lines to create an outline.

        Args:
            renderer: SDL renderer instance
            rect: Rectangle (x, y, width, height) in pixels
            color: RGB color tuple
            thickness: Thickness of outline in pixels
        """
        x, y, w, h = rect

        # Convert RGB to RGBA for SDL (SDL requires 4 values: R, G, B, A)
        if len(color) == 3:
            color_rgba = (*color, 255)  # Add full alpha
        else:
            color_rgba = color

        # Draw outline as 4 separate lines for each thickness level
        for i in range(thickness):
            # Set color for this line
            renderer.draw_color = color_rgba

            # Top line
            renderer.draw_line((x + i, y + i), (x + w - i - 1, y + i))
            # Bottom line
            renderer.draw_line((x + i, y + h - i - 1), (x + w - i - 1, y + h - i - 1))
            # Left line
            renderer.draw_line((x + i, y + i), (x + i, y + h - i - 1))
            # Right line
            renderer.draw_line((x + w - i - 1, y + i), (x + w - i - 1, y + h - i - 1))

        # Reset draw color to avoid affecting other rendering
        renderer.draw_color = (255, 255, 255, 255)

    def _expand_rect(self, rect: Tuple[int, int, int, int], offset: int) -> Tuple[int, int, int, int]:
        """
        Expand rectangle by offset pixels on all sides.

        Args:
            rect: Original rectangle (x, y, width, height)
            offset: Number of pixels to expand

        Returns:
            Expanded rectangle (x, y, width, height)
        """
        return (rect[0] - offset, rect[1] - offset,
                rect[2] + offset * 2, rect[3] + offset * 2)

    def _render_targeting_cursor(self, game, camera_offset: Position):
        """Render targeting cursor for look mode or targeting mode in graphics mode."""
        # Check if either targeting mode or look mode is active
        if not game.targeting_mode and not game.look_mode:
            return

        # Determine which cursor position and color to use
        if game.look_mode:
            cursor_pos = game.look_cursor_position
            cursor_color = Colors.CYAN  # Cyan for look mode
        else:  # targeting_mode
            cursor_pos = game.cursor_position
            cursor_color = Colors.RED  # Red for targeting mode

        renderer = self.context.sdl_renderer

        # Show range indicator and area effect (only for targeting mode)
        if game.targeting_mode and game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            self._render_targeting_range_graphics(renderer, game.player.position, exploit.range, camera_offset)

            # Show area effect for AREA targeting mode
            if exploit.targeting == TargetingMode.AREA:
                self._render_targeting_area_graphics(renderer, cursor_pos, exploit.effect_radius, camera_offset)

        if self._is_in_viewport(cursor_pos.x, cursor_pos.y, camera_offset):
            cursor_screen_x = cursor_pos.x - camera_offset.x
            cursor_screen_y = cursor_pos.y - camera_offset.y + 1

            # Graphics mode: Render targeting cursor sprite
            texture = self.tile_manager.get_tile("targeting")
            if texture:
                normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                tile_rect = self._get_tile_rect(cursor_screen_x, cursor_screen_y)
                # Tint based on mode (red for targeting, cyan for look)
                texture.color_mod = cursor_color
                renderer.copy(texture, dest=tile_rect)
                # Reset color_mod
                texture.color_mod = normal_tint

    def _render_targeting_range_graphics(self, renderer, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator in graphics mode using transparent overlays."""
        range_color = ColorManager.get_targeting_color("range_overlay")

        # Enable alpha blending for transparent overlays
        old_blend_mode = renderer.draw_blend_mode
        renderer.draw_blend_mode = BlendMode.BLEND

        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                # Use Euclidean distance for circular range (matches glyphs mode)
                if dx*dx + dy*dy <= range_val*range_val:
                    world_x = center.x + dx
                    world_y = center.y + dy

                    if self._is_in_viewport(world_x, world_y, camera_offset):
                        screen_x = world_x - camera_offset.x
                        screen_y = world_y - camera_offset.y + 1

                        # Render semi-transparent overlay using SDL rectangles
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.draw_color = (*range_color, 80)  # Semi-transparent
                        renderer.fill_rect(tile_rect)

        # Restore original blend mode
        renderer.draw_blend_mode = old_blend_mode

    def _render_targeting_area_graphics(self, renderer, center: Position, radius: int, camera_offset: Position):
        """
        Render area effect indicator in graphics mode using transparent overlays.

        Uses grid distance (Chebyshev) to match gameplay mechanics.
        For radius 1: 3x3 area, radius 2: 5x5 area, etc.
        """
        area_color = ColorManager.get_targeting_color("area_overlay")

        # Enable alpha blending for transparent overlays
        old_blend_mode = renderer.draw_blend_mode
        renderer.draw_blend_mode = BlendMode.BLEND

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                # Use grid distance (Chebyshev) - matches gameplay
                if max(abs(dx), abs(dy)) <= radius:
                    world_x = center.x + dx
                    world_y = center.y + dy

                    if self._is_in_viewport(world_x, world_y, camera_offset):
                        screen_x = world_x - camera_offset.x
                        screen_y = world_y - camera_offset.y + 1

                        # Render brighter semi-transparent overlay
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.draw_color = (*area_color, 120)  # More opaque than range
                        renderer.fill_rect(tile_rect)

        # Restore original blend mode
        renderer.draw_blend_mode = old_blend_mode

    def _render_hover_highlight(self, game, camera_offset: Position):
        """Render hover highlight for mouse cursor in normal gameplay mode."""
        # Only show hover in normal gameplay (not in look/targeting/menus)
        if game.look_mode or game.targeting_mode or game.show_inventory or game.show_lore_viewer or game.show_help:
            return

        # Only show if mouse is hovering over a valid world position
        if not game.mouse_hover_world_pos:
            return

        renderer = self.context.sdl_renderer
        hover_pos = game.mouse_hover_world_pos

        if self._is_in_viewport(hover_pos.x, hover_pos.y, camera_offset):
            hover_screen_x = hover_pos.x - camera_offset.x
            hover_screen_y = hover_pos.y - camera_offset.y + 1

            tile_rect = self._get_tile_rect(hover_screen_x, hover_screen_y)

            # Determine if this is a valid walkable tile
            from game_characters import PositionValidator
            is_walkable = PositionValidator.is_basic_valid_position(hover_pos, game.game_map)

            # Color: Green for walkable tiles, Yellow for blocked tiles (walls, etc.)
            if is_walkable:
                highlight_color = (0, 255, 0, 180)  # Green, semi-transparent
            else:
                highlight_color = (255, 255, 0, 180)  # Yellow, semi-transparent

            # Draw highlight border (thicker than other overlays for visibility)
            self._draw_outline_box(renderer, tile_rect, highlight_color, thickness=3)

    def _get_status_outline_color(self, status_type: str) -> Tuple[int, int, int]:
        """
        Get outline color for status effect.

        Args:
            status_type: Type of status effect

        Returns:
            RGB color tuple for the outline
        """
        try:
            return ColorManager.get("status_effects", status_type)
        except KeyError:
            # Fallback to white if status type not found
            return Colors.PURE_WHITE

    def _draw_corner_brackets(self, renderer, rect: Tuple[int, int, int, int], color: Tuple[int, int, int], bracket_size: int = 4):
        """
        Draw corner brackets around a tile rectangle.

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
        Calculate cyberspace color based on current time for data fragment highlighting.
        Cycles through neon cyberspace colors used in the game.

        Returns:
            RGB color tuple cycling through cyberspace neon colors
        """
        # Cyberspace neon palette from game_rules.json
        cyberspace_colors = [
            ColorManager.get("data_codes", "combat_red"),
            Colors.ELECTRIC_BLUE,  # azure_blue consolidated to basic.electric_blue
            ColorManager.get("data_codes", "emerald_green"),
            ColorManager.get("data_codes", "utility_gold"),
            ColorManager.get("data_codes", "plasma_violet"),
            Colors.NEON_PINK,
        ]

        current_time = time.time()
        # Cycle through colors every 6 seconds (1 second per color)
        color_index = int(current_time) % len(cyberspace_colors)

        # Smooth transition between colors
        next_index = (color_index + 1) % len(cyberspace_colors)
        blend_factor = (current_time % 1.0)  # 0.0 to 1.0 within the second

        current_color = cyberspace_colors[color_index]
        next_color = cyberspace_colors[next_index]

        # Linear interpolation between colors
        r = int(current_color[0] * (1 - blend_factor) + next_color[0] * blend_factor)
        g = int(current_color[1] * (1 - blend_factor) + next_color[1] * blend_factor)
        b = int(current_color[2] * (1 - blend_factor) + next_color[2] * blend_factor)

        return (r, g, b)

    def _render_vision_overlays(self, game, camera_offset: Position, vision_range: int):
        """Render enemy vision range overlays using corner brackets in graphics mode."""
        if game.player.is_invisible():
            return

        threat_scan_active = game.game_state.threat_scan_turns > 0
        renderer = self.context.sdl_renderer

        for enemy in game.enemies:
            if enemy.disabled_turns > 0:
                continue

            # Show vision overlays for visible enemies OR if Threat Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

            if can_see_enemy or threat_scan_active:
                overlay_color = self._get_vision_overlay_color(enemy.state)

                # If revealed by threat scan, make overlay more translucent
                if threat_scan_active and not can_see_enemy:
                    overlay_color = tuple(c // 2 for c in overlay_color)  # Make it dimmer

                self._render_enemy_vision_range(enemy, camera_offset, overlay_color, game.game_map, renderer)

    def _get_vision_overlay_color(self, enemy_state: EnemyState) -> Tuple[int, int, int]:
        """Get vision overlay color based on enemy state (full brightness for graphics mode)."""
        if enemy_state == EnemyState.HOSTILE:
            return ColorManager.get_enemy_state_color("hostile")
        elif enemy_state == EnemyState.ALERT:
            return ColorManager.get_enemy_state_color("alert")
        else:
            return ColorManager.get_enemy_state_color("unaware")

    def _render_enemy_vision_range(self, enemy, camera_offset: Position, overlay_color: Tuple[int, int, int], game_map, renderer):
        """Render vision range for a single enemy using corner brackets in graphics mode.
        Uses TCOD FOV for perfect consistency with actual enemy vision.

        Vision indicators are hidden on blind spots unless the enemy is adjacent to that blind spot,
        since enemies can only see players in blind spots when adjacent (grid distance <= 1)."""
        actual_vision_range = enemy.type_data.vision

        # Use TCOD FOV to get exactly what the enemy can see (matches enemy vision logic)
        fov = game_map._compute_fov_cached(enemy.x, enemy.y, actual_vision_range)

        # Render brackets for all visible tiles within range
        for dx in range(-actual_vision_range, actual_vision_range + 1):
            for dy in range(-actual_vision_range, actual_vision_range + 1):
                world_x = enemy.x + dx
                world_y = enemy.y + dy

                # Skip out of bounds
                if not (0 <= world_x < game_map.width and 0 <= world_y < game_map.height):
                    continue

                # Skip the enemy's own tile
                if world_x == enemy.x and world_y == enemy.y:
                    continue

                # Skip blind spots - enemies can't see into blind spots unless adjacent
                world_pos = Position(world_x, world_y)
                if game_map.is_blind_spot(world_pos):
                    # Show vision marker if enemy is adjacent to this blind spot
                    enemy_pos = Position(enemy.x, enemy.y)
                    if enemy_pos.grid_distance_to(world_pos) > 1:
                        continue

                # Check if this tile is visible in FOV (TCOD array is [y, x])
                if not fov[world_y, world_x]:
                    continue

                if self._is_in_viewport(world_x, world_y, camera_offset):
                    screen_x = world_x - camera_offset.x
                    screen_y = world_y - camera_offset.y + 1

                    # Draw corner brackets
                    tile_rect = self._get_tile_rect(screen_x, screen_y)
                    self._draw_corner_brackets(renderer, tile_rect, overlay_color, bracket_size=GameConfig.VISION_BRACKET_SIZE())

    def _render_movement_prediction(self, game, camera_offset: Position, vision_range: int):
        """Render next 3 predicted moves for all moving enemies using sprites."""
        renderer = self.context.sdl_renderer

        for enemy in game.enemies:
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

            # Show movement intentions for all visible enemies
            if can_see_enemy:
                next_positions = game.get_enemy_next_positions(enemy, 3)

                for i, point in enumerate(next_positions):
                    # Skip rendering movement prediction if there's an enemy at this position
                    enemy_at_point = any(e.position.x == point.x and e.position.y == point.y for e in game.enemies)
                    if enemy_at_point:
                        continue

                    if self._is_in_viewport(point.x, point.y, camera_offset):
                        screen_x = point.x - camera_offset.x
                        screen_y = point.y - camera_offset.y + 1

                        # Render movement prediction sprite with color_mod
                        texture = self.tile_manager.get_tile("movement_prediction")
                        if texture:
                            normal_tint = Colors.PURE_WHITE  # normal tint consolidated
                            tile_rect = self._get_tile_rect(screen_x, screen_y)
                            # Apply color based on position (brightness fades with distance)
                            if i == 0:
                                texture.color_mod = ColorManager.get_targeting_color("prediction_bright")
                            elif i == 1:
                                texture.color_mod = ColorManager.get_targeting_color("prediction_medium")
                            else:
                                texture.color_mod = ColorManager.get_targeting_color("prediction_dim")
                            renderer.copy(texture, dest=tile_rect)
                            # Reset color_mod
                            texture.color_mod = normal_tint
                        else:
                            logging.warning("_render_movement_prediction: movement_prediction texture not found!")
