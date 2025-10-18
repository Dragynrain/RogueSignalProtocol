#!/usr/bin/env python3
"""
Game Rendering Graphics
SDL sprite/texture-based rendering.
"""

import tcod
import logging
import time
import math
from typing import Tuple

from game_config import GameConfig, GameBalance
from game_entities import Position, Colors, EnemyState, ensure_color_tuple
from game_data import GameData, GameUpgrades
from data_loading import DataLoader


class GraphicsMapRenderer:
    """Renders the game map using SDL sprites/textures."""

    def __init__(self, tile_manager=None, context=None, settings=None):
        """
        Initialize GraphicsMapRenderer with SDL support.

        Args:
            tile_manager: TileManager instance for sprite loading
            context: TCOD context with SDL renderer
            settings: GameSettings instance for accessing graphics_mode
        """
        self.tile_manager = tile_manager
        self.context = context
        self.settings = settings

    def _get_graphics_mode(self):
        """Get current graphics mode from settings."""
        if self.settings:
            return self.settings.graphics_mode
        return "glyph"

    def _should_use_graphics(self):
        """Check if graphics mode is available and should be used."""
        return (self.tile_manager is not None and
                self.context is not None and
                hasattr(self.context, 'sdl_renderer') and
                self.context.sdl_renderer is not None)

    def _world_to_console(self, world_x: int, world_y: int, camera_offset: Position) -> Tuple[int, int]:
        """
        Convert world coordinates to console coordinates based on viewport.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            camera_offset: Camera offset position

        Returns:
            Tuple of (console_x, console_y)
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

    def _calculate_camera_offset(self, player) -> Position:
        """Calculate camera offset to center on player."""
        graphics_mode = self._get_graphics_mode()
        viewport_width = GameConfig.VIEWPORT_WIDTH(graphics_mode)
        viewport_height = GameConfig.VIEWPORT_HEIGHT(graphics_mode)

        camera_x = max(0, min(GameConfig.MAP_WIDTH - viewport_width,
                             player.x - viewport_width // 2))
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - viewport_height,
                             player.y - viewport_height // 2))
        return Position(camera_x, camera_y)

    def _grid_to_pixel(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert grid coordinates to pixel coordinates."""
        if not self.tile_manager:
            return (0, 0)
        pixel_x = screen_x * self.tile_manager.tile_width
        pixel_y = screen_y * self.tile_manager.tile_height
        return (pixel_x, pixel_y)

    def _get_tile_rect(self, screen_x: int, screen_y: int) -> Tuple[int, int, int, int]:
        """Get pixel rectangle for a tile at grid coordinates."""
        if not self.tile_manager:
            return (0, 0, 0, 0)
        px, py = self._grid_to_pixel(screen_x, screen_y)
        return (px, py, self.tile_manager.tile_width, self.tile_manager.tile_height)

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
        camera_offset = self._calculate_camera_offset(game.player)
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
                console_y = viewport_y + 1

                # Check visibility
                if game.player.can_see_through_walls():
                    distance = game.player.position.distance_to(world_pos)
                    can_see = distance <= vision_range
                else:
                    can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

                # Check if tile has been explored (for fog of war)
                explored = (world_x, world_y) in game.game_map.explored_tiles

                if can_see:
                    # Currently visible - full brightness
                    if game.game_map.is_wall(world_pos):
                        texture = self.tile_manager.get_tile("wall")
                    elif game.game_map.is_shadow(world_pos):
                        texture = self.tile_manager.get_tile("shadow")
                    else:
                        texture = self.tile_manager.get_tile("floor")

                    if texture:
                        tile_rect = self._get_tile_rect(console_x, console_y)
                        renderer.copy(texture, dest=tile_rect)
                    else:
                        # Log first few missing textures for debugging
                        if console_x < 2 and console_y < 3:
                            if game.game_map.is_wall(world_pos):
                                terrain_type = "wall"
                            elif game.game_map.is_shadow(world_pos):
                                terrain_type = "shadow"
                            else:
                                terrain_type = "floor"
                            logging.warning(f"Missing texture for {terrain_type} at console ({console_x},{console_y})")
                elif explored:
                    # Explored but not currently visible - dimmed (fog of war)
                    if game.game_map.is_wall(world_pos):
                        texture = self.tile_manager.get_tile("wall")
                    elif game.game_map.is_shadow(world_pos):
                        texture = self.tile_manager.get_tile("shadow")
                    else:
                        texture = self.tile_manager.get_tile("floor")

                    if texture:
                        tile_rect = self._get_tile_rect(console_x, console_y)
                        # Dim the texture for fog of war effect
                        texture.color_mod = (80, 80, 100)  # Dark blue-gray tint for explored areas
                        renderer.copy(texture, dest=tile_rect)
                        # Reset color mod
                        texture.color_mod = (255, 255, 255)

        # LAYER 2A: Render item sprites with tinting for tintable items
        # Code hacks
        for (world_x, world_y), code_hack in game.game_map.code_hacks.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

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
                        texture.color_mod = (255, 255, 255)

        # Exploit pickups
        for (world_x, world_y), exploit_item in game.game_map.exploit_pickups.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

            if can_see:
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                    1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    # All exploits use the same "exploit" sprite, tinted by category
                    texture = self.tile_manager.get_tile("exploit")

                    if texture:
                        # Apply tint if tintable
                        if self.tile_manager.is_tintable("exploit"):
                            if exploit_item.exploit_key in GameData.EXPLOITS:
                                exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
                                exploit_category = exploit_def.category
                                # Get exploit color from config
                                from data_loading import DataLoader
                                config = DataLoader.load_config()
                                exploit_colors = config.get("colors", {}).get("exploits", {})
                                color_data = exploit_colors.get(exploit_category, [255, 20, 255])
                                tint_color = ensure_color_tuple(color_data)
                                texture.color_mod = tint_color

                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)

                        # Reset color mod
                        if self.tile_manager.is_tintable("exploit"):
                            texture.color_mod = (255, 255, 255)

        # Resource nodes (cooling, CPU, ghost)
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
                    can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

                if can_see:
                    # Render nodes as sprites
                    node_type = None
                    if game.game_map.is_cooling_node(world_pos):
                        node_type = "cooling_node"
                    elif game.game_map.is_cpu_recovery_node(world_pos):
                        node_type = "cpu_node"
                    elif game.game_map.is_ghost_node(world_pos):
                        node_type = "ghost_node"

                    if node_type:
                        texture = self.tile_manager.get_tile(node_type)
                        if texture:
                            tile_rect = self._get_tile_rect(screen_x, screen_y)
                            renderer.copy(texture, dest=tile_rect)

        # Permanent upgrades
        for (world_x, world_y), upgrade_key in game.game_map.permanent_upgrades.items():
            world_pos = Position(world_x, world_y)
            if game.player.can_see_through_walls():
                distance = game.player.position.distance_to(world_pos)
                can_see = distance <= vision_range
            else:
                can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

            if can_see:
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                    1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    # Map upgrade key to sprite name
                    upgrade_sprite_map = {
                        'cooling_upgrade': 'cooling_upgrade',
                        'cpu_upgrade': 'cpu_upgrade',
                        'ram_upgrade': 'ram_upgrade'
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
                can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

            if can_see:
                screen_x = world_x - camera_offset.x
                screen_y = world_y - camera_offset.y + 1

                if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                    1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    # Render story fragment sprite
                    texture = self.tile_manager.get_tile("story_fragment")
                    if texture:
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)

        # Gateway/Portal
        if game.game_map.gateway:
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
                    # Render portal sprite
                    texture = self.tile_manager.get_tile("portal")
                    if texture:
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)
                    else:
                        logging.warning("render_sprites_layer: Portal texture not found!")
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
                        # Render portal sprite with dimmed appearance
                        texture = self.tile_manager.get_tile("portal")
                        if texture:
                            tile_rect = self._get_tile_rect(screen_x, screen_y)
                            # Use color_mod to dim the sprite (70% brightness for memory)
                            texture.color_mod = (179, 179, 179)  # 70% of 255
                            renderer.copy(texture, dest=tile_rect)
                            # Reset color_mod
                            texture.color_mod = (255, 255, 255)

        # LAYER 2B: Render entity sprites (enemies, player - NO tinting)
        # Enemies
        for enemy in game.enemies:
            screen_x = enemy.x - camera_offset.x
            screen_y = enemy.y - camera_offset.y + 1

            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
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
                        tile_rect = self._get_tile_rect(screen_x, screen_y)
                        renderer.copy(texture, dest=tile_rect)

        # Player
        player_screen_x = game.player.x - camera_offset.x
        player_screen_y = game.player.y - camera_offset.y + 1

        if (0 <= player_screen_x < GameConfig.GAME_AREA_WIDTH() and
            1 <= player_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
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
        camera_offset = self._calculate_camera_offset(game.player)
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
                        can_see = game.game_map.can_see_position(game.player.position, world_pos, vision_range)

                    if can_see:
                        # Render special nodes
                        glyph = None
                        color = None

                        if game.game_map.is_cooling_node(world_pos):
                            glyph = ord(chr(tcod.tileset.CHARMAP_CP437[4]))  # Diamond
                            color = Colors.CYAN
                        elif game.game_map.is_cpu_recovery_node(world_pos):
                            glyph = ord(chr(tcod.tileset.CHARMAP_CP437[3]))  # Heart
                            color = Colors.RED
                        elif game.game_map.is_ghost_node(world_pos):
                            glyph = ord(chr(tcod.tileset.CHARMAP_CP437[6]))  # Spade
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

        camera_offset = self._calculate_camera_offset(game.player)
        vision_range = game.player.get_vision_range()

        # TODO: Implement graphics-specific overlay rendering here
        # These overlays (vision ranges, patrol routes, targeting cursor) should be rendered
        # using SDL graphics primitives or sprite textures, not console glyphs.
        # For now, overlays are handled by the glyph renderer layer.
        pass

    def render_status_effects_layer(self, game):
        """
        Render colored status effect outlines over NON-TINTABLE sprites (Layer 2.5).
        This includes virus effects, slow effects, enemy state indicators, and other status indicators.

        Should only be called in graphics mode.
        """
        if not self._should_use_graphics():
            return

        renderer = self.context.sdl_renderer
        camera_offset = self._calculate_camera_offset(game.player)

        # Draw status effect outline for player if has status
        player_screen_x = game.player.x - camera_offset.x
        player_screen_y = game.player.y - camera_offset.y + 1

        if (0 <= player_screen_x < GameConfig.GAME_AREA_WIDTH() and
            1 <= player_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):

            # Check for various player status effects
            status_color = None
            if game.player.temporary_effects['virus_turns'] > 0:
                status_color = (0, 255, 0)  # Bright green for virus
            elif game.player.is_invisible():
                status_color = (255, 255, 0)  # Yellow for invisibility
            elif game.player.temporary_effects['movement_slowed_turns'] > 0:
                status_color = (0, 255, 255)  # Cyan for slow

            if status_color:
                player_tile_rect = self._get_tile_rect(player_screen_x, player_screen_y)
                self._draw_outline_box(renderer, player_tile_rect, status_color, thickness=2)

        # Draw enemy state outlines (yellow/orange/red for normal/alert/hostile)
        for enemy in game.enemies:
            screen_x = enemy.x - camera_offset.x
            screen_y = enemy.y - camera_offset.y + 1

            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH() and
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                threat_scan_active = game.game_state.threat_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)

                if can_see_enemy or threat_scan_active:
                    enemy_tile_rect = self._get_tile_rect(screen_x, screen_y)

                    # Get pulse intensity for pulsing animation
                    pulse_intensity = self._get_pulse_intensity(pulse_speed=2.0)

                    # Determine enemy state color
                    if enemy.disabled_turns > 0:
                        # Disabled enemies get blue outline (no pulsing for disabled)
                        outline_color = (100, 100, 255)  # Blue for disabled
                        self._draw_outline_box(renderer, enemy_tile_rect, outline_color, thickness=2)
                    else:
                        # Show enemy state with colored outline + pulsing
                        if enemy.state == EnemyState.HOSTILE:
                            base_color = (255, 0, 0)  # Red for hostile
                        elif enemy.state == EnemyState.ALERT:
                            base_color = (255, 165, 0)  # Orange for alert
                        else:  # PATROLLING/IDLE
                            base_color = (255, 255, 0)  # Yellow for normal

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

    def _get_status_outline_color(self, status_type: str) -> Tuple[int, int, int]:
        """
        Get outline color for status effect.

        Args:
            status_type: Type of status effect

        Returns:
            RGB color tuple for the outline
        """
        STATUS_COLORS = {
            "virus": (0, 255, 0),              # Green
            "slow": (255, 255, 0),             # Yellow
            "invisible": (100, 100, 255),      # Blue
            "disabled": (100, 100, 255),       # Blue
        }
        return STATUS_COLORS.get(status_type, (255, 255, 255))

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
