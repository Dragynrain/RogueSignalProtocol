def render_map(console, game):
    """Render the game map"""
    # Calculate camera offset to center on player
    camera_x = game.player.x - SCREEN_WIDTH // 2
    camera_y = game.player.y - (SCREEN_HEIGHT - PANEL_HEIGHT) // 2
    
    # Enhanced vision range when boosted
    vision_range = game.player.get_vision_range()
    
    # Render floor and basic tiles
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT - PANEL_HEIGHT):
            world_x = x + camera_x
            world_y = y + camera_y
            
            if (0 <= world_x < MAP_WIDTH and 0 <= world_y < MAP_HEIGHT):
                distance = max(abs(world_x - game.player.x), abs(world_y - game.player.y))
                if distance <= vision_range:
                    # Check what's at this position
                    if game.game_map.is_wall(world_x, world_y):
                        # Enhanced vision can see through some walls
                        if game.player.can_see_through_walls() and distance <= vision_range - 5:
                            console.put_char(x, y, ord('▓'), fg=Colors.wall * 0.7, bg=Colors.black)
                        else:
                            console.put_char(x, y, ord('█'), fg=Colors.wall, bg=Colors.black)
                    elif game.game_map.is_shadow(world_x, world_y):
                        console.put_char(x, y, ord('◉'), fg=Colors.green, bg=Colors.shadow)
                    elif game.game_map.is_cooling_node(world_x, world_y):
                        console.put_char(x, y, ord('℺'), fg=Colors.cyan, bg=Colors.black)
                    elif game.game_map.is_cpu_recovery_node(world_x, world_y):
                        console.put_char(x, y, ord('+'), fg=Colors.red, bg=Colors.black)
                    elif (world_x, world_y) in game.game_map.data_patches:
                        patch = game.game_map.data_patches[(world_x, world_y)]
                        color_map = {
                            'crimson': Colors.red, 'azure': Colors.blue, 'emerald': Colors.green,
                            'golden': Colors.yellow, 'violet': Colors.magenta, 'silver': Colors.white
                        }
                        console.put_char(x, y, ord('◈'), fg=color_map.get(patch.color, Colors.white), bg=Colors.black)
                    elif (world_x, world_y) in game.distraction_points:
                        # Show active noise makers
                        console.put_char(x, y, ord('♪'), fg=Colors.yellow, bg=Colors.black)
                    else:
                        console.put_char(x, y, ord('.'), fg=Colors.floor, bg=Colors.black)
                else:
                    # Fog of war
                    console.put_char(x, y, ord(' '), fg=Colors.black, bg=Colors.black)
    
    # Render enemy vision ranges (when not in data mimic mode)
    if not game.player.is_invisible():
        for enemy in game.enemies:
            enemy_screen_x = enemy.x - camera_x
            enemy_screen_y = enemy.y - camera_y
            
            # Check if enemy is visible to player
            distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance_to_player <= vision_range and enemy.disabled_turns == 0:
                # Draw vision range as colored background
                for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                    for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                        if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                            vx = enemy_screen_x + dx
                            vy = enemy_screen_y + dy
                            if (0 <= vx < SCREEN_WIDTH and 0 <= vy < SCREEN_HEIGHT - PANEL_HEIGHT):
                                try:
                                    # Create semi-transparent vision overlay
                                    current_bg = console.bg[vx, vy]
                                    if enemy.state == EnemyState.HOSTILE:
                                        overlay_color = (100, 0, 0)  # Red for hostile
                                    elif enemy.state == EnemyState.ALERT:
                                        overlay_color = (100, 100, 0)  # Yellow for alert
                                    else:
                                        overlay_color = (100, 50, 0)  # Orange for unaware
                                    
                                    # Blend colors safely
                                    if isinstance(current_bg, tuple) and len(current_bg) >= 3:
                                        blended = tuple(min(255, int(current_bg[i] * 0.7 + overlay_color[i] * 0.3)) for i in range(3))
                                        console.bg[vx, vy] = blended
                                except (IndexError, TypeError):
                                    # Skip if there's an issue with color blending
                                    pass
    
    # Render patrol routes if enabled
    if game.show_patrols:
        for enemy in game.enemies:
            if enemy.patrol_points and len(enemy.patrol_points) > 1:
                distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
                if distance_to_player <= vision_range:
                    for point in enemy.patrol_points:
                        px = point.x - camera_x
                        py = point.y - camera_y
                        if (0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT - PANEL_HEIGHT):
                            try:
                                console.put_char(px, py, ord('•'), fg=Colors.yellow, bg=console.bg[px, py])
                            except (IndexError, TypeError):
                                console.put_char(px, py, ord('•'), fg=Colors.yellow, bg=Colors.black)
    
    # Render movement predictions if network scan is active
    if game.show_patrol_predictions:
        for enemy in game.enemies:
            distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance_to_player <= vision_range:
                predictions = enemy.get_predicted_moves(3)
                for i, pred_pos in enumerate(predictions):
                    px = pred_pos.x - camera_x
                    py = pred_pos.y - camera_y
                    if (0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT - PANEL_HEIGHT):
                        # Show prediction with numbers 1,2,3
                        console.put_char(px, py, ord(str(i + 1)), fg=Colors.cyan, bg=Colors.black)
    
    # Render gateway
    if game.game_map.gateway:
        gw_x = game.game_map.gateway.x - camera_x
        gw_y = game.game_map.gateway.y - camera_y
        if (0 <= gw_x < SCREEN_WIDTH and 0 <= gw_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(game.game_map.gateway.x - game.player.x), 
                          abs(game.game_map.gateway.y - game.player.y))
            if distance <= vision_range:
                console.put_char(gw_x, gw_y, ord('>'), fg=Colors.gateway, bg=Colors.black)
    
    # Render enemies
    for enemy in game.enemies:
        enemy_x = enemy.x - camera_x
        enemy_y = enemy.y - camera_y
        if (0 <= enemy_x < SCREEN_WIDTH and 0 <= enemy_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance <= vision_range:
                console.put_char(enemy_x, enemy_y, ord(enemy.type_data.symbol), 
                                fg=enemy.get_color(), bg=Colors.black)
    
    # Render player (with special effects)
    player_x = game.player.x - camera_x
    player_y = game.player.y - camera_y
    if (0 <= player_x < SCREEN_WIDTH and 0 <= player_y < SCREEN_HEIGHT - PANEL_HEIGHT):
        player_color = Colors.player
        if game.player.is_invisible():
            player_color = Colors.blue  # Different color when invisible
        elif game.player.speed_boost_turns > 0:
            player_color = Colors.yellow  # Different color when speed boosted
        
        console.put_char(player_x, player_y, ord('@'), fg=player_color, bg=Colors.black)
    
    # Render targeting cursor
    if game.targeting_mode:
        cursor_x = game.cursor_x - camera_x
        cursor_y = game.cursor_y - camera_y
        if (0 <= cursor_x < SCREEN_WIDTH and 0 <= cursor_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            # Draw targeting crosshair
            console.put_char(cursor_x, cursor_y, ord('X'), fg=Colors.red, bg=Colors.black)
            
            # Show range indicator
            if game.targeting_exploit in EXPLOITS:
                exploit = EXPLOITS[game.targeting_exploit]
                for dx in range(-exploit.range, exploit.range + 1):
                    for dy in range(-exploit.range, exploit.range + 1):
                        if dx*dx + dy*dy <= exploit.range*exploit.range:
                            rx = game.player.x - camera_x + dx
                            ry = game.player.y - camera_y + dy
                            if (0 <= rx < SCREEN_WIDTH and 0 <= ry < SCREEN_HEIGHT - PANEL_HEIGHT):
                                try:
                                    # Highlight valid targeting area
                                    current_bg = console.bg[rx, ry]
                                    if isinstance(current_bg, tuple) and len(current_bg) >= 3:
                                        highlighted = tuple(min(255, int(current_bg[i] + 30)) for i in range(3))
                                        console.bg[rx, ry] = highlighted
                                except (IndexError, TypeError):
                                    # Skip if there's an issue with background color
                                    passdef render_map(console, game):
    """Render the game map"""
    # Calculate camera offset to center on player
    camera_x = game.player.x - SCREEN_WIDTH // 2
    camera_y = game.player.y - (SCREEN_HEIGHT - PANEL_HEIGHT) // 2
    
    # Enhanced vision range when boosted
    vision_range = 20 if game.player.enhanced_vision_turns > 0 else 15
    
    # Render floor and basic tiles
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT - PANEL_HEIGHT):
            world_x = x + camera_x
            world_y = y + camera_y
            
            if (0 <= world_x < MAP_WIDTH and 0 <= world_y < MAP_HEIGHT):
                distance = max(abs(world_x - game.player.x), abs(world_y - game.player.y))
                if distance <= vision_range:
                    # Check what's at this position
                    if game.game_map.is_wall(world_x, world_y):
                        console.put_char(x, y, ord('█'), fg=Colors.wall, bg=Colors.black)
                    elif game.game_map.is_shadow(world_x, world_y):
                        console.put_char(x, y, ord('◉'), fg=Colors.green, bg=Colors.shadow)
                    elif game.game_map.is_cooling_node(world_x, world_y):
                        console.put_char(x, y, ord('℺'), fg=Colors.cyan, bg=Colors.black)
                    elif game.game_map.is_cpu_recovery_node(world_x, world_y):
                        console.put_char(x, y, ord('+'), fg=Colors.red, bg=Colors.black)
                    elif (world_x, world_y) in game.game_map.data_patches:
                        patch = game.game_map.data_patches[(world_x, world_y)]
                        color_map = {
                            'crimson': Colors.red, 'azure': Colors.blue, 'emerald': Colors.green,
                            'golden': Colors.yellow, 'violet': Colors.magenta, 'silver': Colors.white
                        }
                        console.put_char(x, y, ord('◈'), fg=color_map.get(patch.color, Colors.white), bg=Colors.black)
                    else:
                        console.put_char(x, y, ord('.'), fg=Colors.floor, bg=Colors.black)
                else:
                    # Fog of war
                    console.put_char(x, y, ord(' '), fg=Colors.black, bg=Colors.black)
    
    # Render enemy vision ranges (when not in data mimic mode)
    if not game.player.is_invisible():
        for enemy in game.enemies:
            enemy_screen_x = enemy.x - camera_x
            enemy_screen_y = enemy.y - camera_y
            
            # Check if enemy is visible to player
            distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance_to_player <= vision_range and enemy.disabled_turns == 0:
                # Draw vision range as colored background
                for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                    for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                        if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                            vx = enemy_screen_x + dx
                            vy = enemy_screen_y + dy
                            if (0 <= vx < SCREEN_WIDTH and 0 <= vy < SCREEN_HEIGHT - PANEL_HEIGHT):
                                try:
                                    # Create semi-transparent vision overlay
                                    current_bg = console.bg[vx, vy]
                                    if enemy.state == EnemyState.HOSTILE:
                                        overlay_color = (100, 0, 0)  # Red for hostile
                                    elif enemy.state == EnemyState.ALERT:
                                        overlay_color = (100, 100, 0)  # Yellow for alert
                                    else:
                                        overlay_color = (100, 50, 0)  # Orange for unaware
                                    
                                    # Blend colors safely
                                    if isinstance(current_bg, tuple) and len(current_bg) >= 3:
                                        blended = tuple(min(255, int(current_bg[i] * 0.7 + overlay_color[i] * 0.3)) for i in range(3))
                                        console.bg[vx, vy] = blended
                                except (IndexError, TypeError):
                                    # Skip if there's an issue with color blending
                                    pass
    
    # Render patrol routes if enabled
    if game.show_patrols:
        for enemy in game.enemies:
            if enemy.patrol_points and len(enemy.patrol_points) > 1:
                distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
                if distance_to_player <= vision_range:
                    for point in enemy.patrol_points:
                        px = point.x - camera_x
                        py = point.y - camera_y
                        if (0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT - PANEL_HEIGHT):
                            try:
                                console.put_char(px, py, ord('•'), fg=Colors.yellow, bg=console.bg[px, py])
                            except (IndexError, TypeError):
                                console.put_char(px, py, ord('•'), fg=Colors.yellow, bg=Colors.black)
    
    # Render gateway
    if game.game_map.gateway:
        gw_x = game.game_map.gateway.x - camera_x
        gw_y = game.game_map.gateway.y - camera_y
        if (0 <= gw_x < SCREEN_WIDTH and 0 <= gw_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(game.game_map.gateway.x - game.player.x), 
                          abs(game.game_map.gateway.y - game.player.y))
            if distance <= vision_range:
                console.put_char(gw_x, gw_y, ord('>'), fg=Colors.gateway, bg=Colors.black)
    
    # Render enemies
    for enemy in game.enemies:
        enemy_x = enemy.x - camera_x
        enemy_y = enemy.y - camera_y
        if (0 <= enemy_x < SCREEN_WIDTH and 0 <= enemy_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance <= vision_range:
                console.put_char(enemy_x, enemy_y, ord(enemy.type_data.symbol), 
                                fg=enemy.get_color(), bg=Colors.black)
    
    # Render player (with special effects)
    player_x = game.player.x - camera_x
    player_y = game.player.y - camera_y
    if (0 <= player_x < SCREEN_WIDTH and 0 <= player_y < SCREEN_HEIGHT - PANEL_HEIGHT):
        player_color = Colors.player
        if game.player.is_invisible():
            player_color = Colors.blue  # Different color when invisible
        elif game.player.speed_boost_turns > 0:
            player_color = Colors.yellow  # Different color when speed boosted
        
        console.put_char(player_x, player_y, ord('@'), fg=player_color, bg=Colors.black)
    
    # Render targeting cursor
    if game.targeting_mode:
        cursor_x = game.cursor_x - camera_x
        cursor_y = game.cursor_y - camera_y
        if (0 <= cursor_x < SCREEN_WIDTH and 0 <= cursor_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            # Draw targeting crosshair
            console.put_char(cursor_x, cursor_y, ord('X'), fg=Colors.red, bg=Colors.black)
            
            # Show range indicator
            if game.targeting_exploit in EXPLOITS:
                exploit = EXPLOITS[game.targeting_exploit]
                for dx in range(-exploit.range, exploit.range + 1):
                    for dy in range(-exploit.range, exploit.range + 1):
                        if dx*dx + dy*dy <= exploit.range*exploit.range:
                            rx = game.player.x - camera_x + dx
                            ry = game.player.y - camera_y + dy
                            if (0 <= rx < SCREEN_WIDTH and 0 <= ry < SCREEN_HEIGHT - PANEL_HEIGHT):
                                try:
                                    # Highlight valid targeting area
                                    current_bg = console.bg[rx, ry]
                                    if isinstance(current_bg, tuple) and len(current_bg) >= 3:
                                        highlighted = tuple(min(255, int(current_bg[i] + 30)) for i in range(3))
                                        console.bg[rx, ry] = highlighted
                                except (IndexError, TypeError):
                                    # Skip if there's an issue with background color
                                    pass    def process_turn(self):
        """Process one game turn"""
        self.turn += 1
        
        # Update player effects
        self.player.update_effects()
        
        # Cool down heat
        heat_reduction = 3 if self.player.exploit_efficiency_turns > 0 else 2
        self.player.heat = max(0, self.player.heat - heat_reduction)
        #!/usr/bin/env python3
"""
Rogue Signal Protocol v7.0
A stealth-focused traditional roguelike using Python and libtcod
"""

import tcod
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import time

# Constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 50
MAP_HEIGHT = 50
PANEL_HEIGHT = 10
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

# Game balance constants
ADMIN_SPAWN_THRESHOLDS = {0: 100, 1: 100, 2: 75, 3: 50}  # Detection % to spawn Admin Avatar
NETWORK_CONFIGS = {
    1: {"enemies": 8, "shadow_coverage": 0.4, "name": "Corporate Network"},
    2: {"enemies": 12, "shadow_coverage": 0.25, "name": "Government System"},
    3: {"enemies": 16, "shadow_coverage": 0.15, "name": "Military Backbone"}
}

# Colors
class Colors:
    # UI Colors
    white = tcod.Color(255, 255, 255)
    black = tcod.Color(0, 0, 0)
    red = tcod.Color(255, 0, 0)
    green = tcod.Color(0, 255, 0)
    blue = tcod.Color(0, 0, 255)
    yellow = tcod.Color(255, 255, 0)
    cyan = tcod.Color(0, 255, 255)
    magenta = tcod.Color(255, 0, 255)
    
    # Game Colors
    floor = tcod.Color(0, 50, 0)
    wall = tcod.Color(200, 200, 200)
    shadow = tcod.Color(0, 20, 0)
    player = tcod.Color(0, 255, 255)
    gateway = tcod.Color(255, 255, 0)
    
    # Enemy Colors
    enemy_unaware = tcod.Color(255, 136, 0)
    enemy_alert = tcod.Color(255, 255, 0)
    enemy_hostile = tcod.Color(255, 0, 0)
    
    # Vision
    vision_range = tcod.Color(255, 136, 0, 80)  # Semi-transparent orange
    
    # UI
    ui_bg = tcod.Color(0, 20, 0)
    ui_text = tcod.Color(0, 255, 0)

class EnemyState(Enum):
    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"

class EnemyMovement(Enum):
    STATIC = "static"
    LINEAR = "linear"
    RANDOM = "random"
    SEEK = "seek"
    TRACK = "track"

@dataclass
class Position:
    x: int
    y: int

@dataclass
class EnemyType:
    symbol: str
    cpu: int
    vision: int
    movement: EnemyMovement
    name: str

# Enemy type definitions
ENEMY_TYPES = {
    'scanner': EnemyType('s', 20, 2, EnemyMovement.STATIC, "Scanner"),
    'patrol': EnemyType('p', 25, 3, EnemyMovement.LINEAR, "Patrol"),
    'bot': EnemyType('b', 15, 2, EnemyMovement.RANDOM, "Bot"),
    'firewall': EnemyType('F', 40, 1, EnemyMovement.STATIC, "Firewall"),
    'hunter': EnemyType('H', 35, 5, EnemyMovement.SEEK, "Hunter"),
    'admin': EnemyType('A', 100, 6, EnemyMovement.TRACK, "Admin Avatar")
}

@dataclass
class DataPatch:
    """Randomized items with unknown effects until used"""
    color: str
    effect: str
    name: str
    discovered: bool = False

class TargetingMode(Enum):
    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"

@dataclass
class ExploitDef:
    name: str
    ram: int
    heat: int
    range: int
    exploit_type: str
    targeting: TargetingMode = TargetingMode.NONE
    description: str = ""

# Enhanced exploit definitions with targeting
EXPLOITS = {
    'shadow_step': ExploitDef("Shadow Step", 2, 20, 8, "stealth", TargetingMode.SINGLE,
                             "Teleport between shadow zones"),
    'data_mimic': ExploitDef("Data Mimic", 1, 15, 0, "stealth", TargetingMode.NONE,
                            "Appear as harmless data for 5 turns"),
    'noise_maker': ExploitDef("Noise Maker", 1, 10, 6, "stealth", TargetingMode.SINGLE,
                             "Create distraction at target location"),
    'buffer_overflow': ExploitDef("Buffer Overflow", 2, 25, 1, "combat", TargetingMode.SINGLE,
                                 "High melee damage, armor piercing"),
    'code_injection': ExploitDef("Code Injection", 1, 15, 4, "combat", TargetingMode.SINGLE,
                                "Ranged attack, bypasses firewalls"),
    'system_crash': ExploitDef("System Crash", 3, 35, 3, "combat", TargetingMode.AREA,
                              "Area damage, disables multiple enemies"),
    'network_scan': ExploitDef("Network Scan", 1, 10, 8, "utility", TargetingMode.NONE,
                              "Reveals enemy positions and patrol routes"),
    'log_wiper': ExploitDef("Log Wiper", 1, 5, 0, "utility", TargetingMode.NONE,
                           "Reduces detection level significantly"),
    'emp_burst': ExploitDef("EMP Burst", 3, 40, 2, "emergency", TargetingMode.AREA,
                           "Disables all nearby enemies temporarily")
}

class Player:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.cpu = 100
        self.max_cpu = 100
        self.heat = 0
        self.detection = 0
        self.ram_used = 0
        self.ram_total = 8
        self.data_mimic_turns = 0  # Invisibility effect
        self.speed_boost_turns = 0  # Movement boost
        self.enhanced_vision_turns = 0  # See through walls
        self.exploit_efficiency_turns = 0  # Reduced heat
        
        # New features from design document
        self.vision_range = 15  # Player vision range
        self.stealth_bonus_active = False  # For stealth attacks
        self.last_position = Position(x, y)  # For tracking movement
        
    def move(self, dx: int, dy: int, game_map):
        self.last_position = Position(self.x, self.y)
        new_x = self.x + dx
        new_y = self.y + dy
        
        if game_map.is_valid_position(new_x, new_y):
            self.x = new_x
            self.y = new_y
            return True
        return False
    
    def update_effects(self):
        """Update temporary effects each turn"""
        self.data_mimic_turns = max(0, self.data_mimic_turns - 1)
        self.speed_boost_turns = max(0, self.speed_boost_turns - 1)
        self.enhanced_vision_turns = max(0, self.enhanced_vision_turns - 1)
        self.exploit_efficiency_turns = max(0, self.exploit_efficiency_turns - 1)
    
    def is_invisible(self):
        """Check if player is effectively invisible"""
        return self.data_mimic_turns > 0
    
    def get_vision_range(self):
        """Get current vision range including bonuses"""
        base_range = self.vision_range
        if self.enhanced_vision_turns > 0:
            base_range += 5  # Enhanced vision bonus
        return base_range
    
    def can_see_through_walls(self):
        """Check if player can see through walls (enhanced vision)"""
        return self.enhanced_vision_turns > 0

class Enemy:
    def __init__(self, x: int, y: int, enemy_type: str):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.type_data = ENEMY_TYPES[enemy_type]
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.patrol_points = []
        self.patrol_index = 0
        self.disabled_turns = 0  # EMP/stun effects
        self.last_seen_player = None  # For hunting behavior
        
    def get_color(self):
        if self.disabled_turns > 0:
            return Colors.blue  # Disabled
        elif self.state == EnemyState.UNAWARE:
            return Colors.enemy_unaware
        elif self.state == EnemyState.ALERT:
            return Colors.enemy_alert
        else:
            return Colors.enemy_hostile
    
    def can_see_player(self, player, game_map):
        if self.disabled_turns > 0:
            return False
            
        distance = max(abs(self.x - player.x), abs(self.y - player.y))
        if distance > self.type_data.vision:
            return False
            
        # Check if player is invisible
        if player.is_invisible():
            return False
            
        # Check if player is in shadows
        if game_map.is_shadow(player.x, player.y):
            return False
            
        # Check line of sight
        return game_map.has_line_of_sight(self.x, self.y, player.x, player.y)
    
    def move(self, game_map, player):
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return
            
        if self.type_data.movement == EnemyMovement.STATIC:
            return
        elif self.type_data.movement == EnemyMovement.RANDOM:
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            dx, dy = random.choice(directions)
            new_x, new_y = self.x + dx, self.y + dy
            if game_map.is_valid_position(new_x, new_y):
                self.x, self.y = new_x, new_y
        elif self.type_data.movement == EnemyMovement.LINEAR and self.patrol_points:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.patrol_index]
            self.x, self.y = target.x, target.y
        elif self.type_data.movement == EnemyMovement.SEEK:
            # Hunter behavior - move toward disturbances
            if self.state == EnemyState.HOSTILE and self.last_seen_player:
                self.move_toward(self.last_seen_player.x, self.last_seen_player.y, game_map)
        elif self.type_data.movement == EnemyMovement.TRACK:
            # Admin Avatar - perfect tracking
            if self.state == EnemyState.HOSTILE:
                self.move_toward(player.x, player.y, game_map)
    
    def get_predicted_moves(self, count: int = 3) -> List[Position]:
        """Get predicted next moves for UI display"""
        predicted = []
        
        if self.type_data.movement == EnemyMovement.STATIC:
            # Static enemies don't move
            for _ in range(count):
                predicted.append(Position(self.x, self.y))
                
        elif self.type_data.movement == EnemyMovement.LINEAR and self.patrol_points:
            # Predict patrol movement
            current_index = self.patrol_index
            for i in range(count):
                next_index = (current_index + i + 1) % len(self.patrol_points)
                predicted.append(self.patrol_points[next_index])
                
        elif self.type_data.movement == EnemyMovement.RANDOM:
            # Show possible random moves (just indicate uncertainty)
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            for i in range(count):
                # For random movement, show one possible direction
                dx, dy = directions[i % len(directions)]
                predicted.append(Position(self.x + dx, self.y + dy))
                
        else:
            # Default: stay in place
            for _ in range(count):
                predicted.append(Position(self.x, self.y))
                
        return predicted
    
    def move_toward(self, target_x: int, target_y: int, game_map):
        """Move one step toward target using simple pathfinding with validation"""
        if target_x < 0 or target_x >= MAP_WIDTH or target_y < 0 or target_y >= MAP_HEIGHT:
            return  # Invalid target
            
        dx = 0 if self.x == target_x else (1 if target_x > self.x else -1)
        dy = 0 if self.y == target_y else (1 if target_y > self.y else -1)
        
        # Try diagonal first, then cardinal directions, then stay put
        move_attempts = [(dx, dy), (dx, 0), (0, dy), (0, 0)]
        
        for try_dx, try_dy in move_attempts:
            new_x, new_y = self.x + try_dx, self.y + try_dy
            if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and
                game_map.is_valid_position(new_x, new_y)):
                self.x, self.y = new_x, new_y
                break
    
    def take_damage(self, damage: int):
        """Take damage and return True if destroyed"""
        self.cpu -= damage
        return self.cpu <= 0

class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.walls = set()
        self.shadows = set()
        self.cooling_nodes = set()  # Special tiles that reduce heat
        self.cpu_recovery_nodes = set()  # Tiles that restore CPU
        self.data_patches = {}  # Position -> DataPatch
        self.gateway = None
        
    def is_wall(self, x: int, y: int) -> bool:
        return (x, y) in self.walls
    
    def is_shadow(self, x: int, y: int) -> bool:
        return (x, y) in self.shadows
    
    def is_cooling_node(self, x: int, y: int) -> bool:
        return (x, y) in self.cooling_nodes
    
    def is_cpu_recovery_node(self, x: int, y: int) -> bool:
        return (x, y) in self.cpu_recovery_nodes
    
    def get_data_patch(self, x: int, y: int) -> Optional[DataPatch]:
        return self.data_patches.get((x, y))
    
    def is_valid_position(self, x: int, y: int) -> bool:
        return (0 <= x < self.width and 
                0 <= y < self.height and 
                not self.is_wall(x, y))
    
    def has_line_of_sight(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Bresenham's line algorithm for line of sight"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            if x == x2 and y == y2:
                return True
            if self.is_wall(x, y):
                return False
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def generate_room(self, x: int, y: int, width: int, height: int):
        """Generate a rectangular room"""
        # Walls
        for i in range(width):
            self.walls.add((x + i, y))
            self.walls.add((x + i, y + height - 1))
        for i in range(height):
            self.walls.add((x, y + i))
            self.walls.add((x + width - 1, y + i))
    
    def generate_corridor(self, x1: int, y1: int, x2: int, y2: int):
        """Generate a corridor between two points"""
        # Simple L-shaped corridor
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.walls.discard((x, y1))
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.walls.discard((x2, y))

class Game:
    def __init__(self):
        self.player = Player(5, 5)
        self.enemies = []
        self.game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
        self.level = 0  # 0 = tutorial
        self.turn = 0
        self.show_patrols = False
        self.loaded_exploits = ['shadow_step', 'network_scan', 'code_injection']
        self.messages = []
        self.game_over = False
        self.targeting_mode = False
        self.targeting_exploit = None
        self.cursor_x = 0
        self.cursor_y = 0
        self.admin_spawned = False
        self.show_patrol_predictions = False  # Show 3-turn predictions
        self.network_scan_turns = 0  # Turns remaining for network scan
        
        # Tutorial system
        self.tutorial_active = False
        self.tutorial_step = 0
        self.tutorial_completed = False
        
        # Advanced features from design document
        self.noise_locations = []  # Active noise makers
        self.distraction_points = {}  # Position -> turns remaining
        
        # Data patch colors and effects (randomized each run)
        self.data_patch_effects = {}
        self.randomize_data_patches()
        
        # Initialize tutorial network
        self.generate_tutorial_network()
        
        # Update RAM usage
        self.calculate_ram_usage()
        
    def randomize_data_patches(self):
        """Randomize data patch effects for this run"""
        colors = ['crimson', 'azure', 'emerald', 'golden', 'violet', 'silver']
        effects = [
            ('restore_cpu', 'Restore 30-40 CPU'),
            ('reduce_heat', 'Reduce heat by 40°C instantly'),
            ('reduce_detection', '-25% detection level'),
            ('speed_boost', 'Temporary speed boost (10 turns)'),
            ('enhanced_vision', 'Enhanced vision (15 turns)'),
            ('exploit_efficiency', 'Exploit efficiency (8 turns)')
        ]
        
        random.shuffle(effects)
        for color, (effect, desc) in zip(colors, effects):
            self.data_patch_effects[color] = (effect, desc)
        
    def generate_tutorial_network(self):
        """Generate the fixed tutorial network"""
        # Clear existing data
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.enemies.clear()
        
        # Create border walls
        for x in range(MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, MAP_HEIGHT - 1))
        for y in range(MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((MAP_WIDTH - 1, y))
        
        # Add internal wall structure
        for x in range(20, 30):
            self.game_map.walls.add((x, 20))
            self.game_map.walls.add((x, 30))
        for y in range(20, 30):
            self.game_map.walls.add((20, y))
            self.game_map.walls.add((30, y))
        
        # Create shadow zones
        for x in range(10, 18):
            for y in range(10, 18):
                self.game_map.shadows.add((x, y))
        
        for x in range(35, 42):
            for y in range(35, 42):
                self.game_map.shadows.add((x, y))
        
        # Create enemies
        self.enemies = [
            Enemy(15, 15, 'scanner'),
            Enemy(25, 25, 'patrol'),
            Enemy(35, 15, 'bot')
        ]
        
        # Set patrol route for patrol enemy
        self.enemies[1].patrol_points = [
            Position(25, 25),
            Position(30, 25),
            Position(30, 35),
            Position(25, 35)
        ]
        
        # Create gateway
        self.game_map.gateway = Position(45, 45)
        
        # Reset player position
        self.player.x, self.player.y = 5, 5
        
        self.add_message("Tutorial Network loaded. Begin infiltration...")
    
    def add_message(self, text: str):
        """Add a message to the log with automatic truncation"""
        if not text:
            return
        # Truncate message to prevent UI overflow
        max_length = SCREEN_WIDTH - 4
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        self.messages.append(text)
        if len(self.messages) > 10:  # Keep only last 10 messages
            self.messages = self.messages[-10:]
    
    def process_turn(self):
        """Process one game turn"""
        self.turn += 1
        
    def process_turn(self):
        """Process one game turn"""
        self.turn += 1
        
        # Update player effects
        self.player.update_effects()
        
        # Cool down heat
        heat_reduction = 3 if self.player.exploit_efficiency_turns > 0 else 2
        self.player.heat = max(0, self.player.heat - heat_reduction)
        
        # Check for special tiles
        player_pos = (self.player.x, self.player.y)
        
        if self.game_map.is_cooling_node(*player_pos):
            self.player.heat = max(0, self.player.heat - 20)
            self.add_message("Cooling node reduces system heat!")
        
        if self.game_map.is_cpu_recovery_node(*player_pos):
            recovery = min(20, self.player.max_cpu - self.player.cpu)
            self.player.cpu += recovery
            if recovery > 0:
                self.add_message(f"CPU recovery node restores {recovery} CPU!")
        
        # Check for data patches
        if player_pos in self.game_map.data_patches:
            patch = self.game_map.data_patches[player_pos]
            self.use_data_patch(patch)
            del self.game_map.data_patches[player_pos]
        
        # Update enemy states
        self.update_enemy_states()
        
        # Move enemies
        for enemy in self.enemies:
            enemy.move(self.game_map, self.player)
        
        # Check for Admin Avatar spawn
        spawn_threshold = ADMIN_SPAWN_THRESHOLDS.get(self.level, 50)
        if (self.player.detection >= spawn_threshold and 
            not self.admin_spawned and 
            not any(e.type == 'admin' for e in self.enemies)):
            self.spawn_admin_avatar()
        
        # Passive detection increase
        if self.turn % 10 == 0:
            self.player.detection = min(100, self.player.detection + 1)
    
    def use_data_patch(self, patch: DataPatch):
        """Use a data patch and apply its effect"""
        if patch.color not in self.data_patch_effects:
            self.add_message(f"Unknown patch type: {patch.color}")
            return
            
        effect, description = self.data_patch_effects[patch.color]
        
        if not patch.discovered:
            patch.discovered = True
            self.add_message(f"Discovered: {patch.name} - {description}")
        
        if effect == 'restore_cpu':
            restore = random.randint(30, 40)
            actual = min(restore, self.player.max_cpu - self.player.cpu)
            self.player.cpu += actual
            self.add_message(f"CPU restored: +{actual}")
        
        elif effect == 'reduce_heat':
            old_heat = self.player.heat
            self.player.heat = max(0, self.player.heat - 40)
            actual_reduction = old_heat - self.player.heat
            self.add_message(f"System heat reduced by {actual_reduction}°C!")
        
        elif effect == 'reduce_detection':
            old_detection = self.player.detection
            self.player.detection = max(0, self.player.detection - 25)
            actual_reduction = old_detection - self.player.detection
            self.add_message(f"Detection level reduced by {actual_reduction:.1f}%!")
        
        elif effect == 'speed_boost':
            self.player.speed_boost_turns = 10
            self.add_message("Speed boost activated! (10 turns)")
        
        elif effect == 'enhanced_vision':
            self.player.enhanced_vision_turns = 15
            self.add_message("Enhanced vision activated! (15 turns)")
        
        elif effect == 'exploit_efficiency':
            self.player.exploit_efficiency_turns = 8
            self.add_message("Exploit efficiency boosted! (8 turns)")
    
    def spawn_admin_avatar(self):
        """Spawn the Admin Avatar with validation"""
        if self.admin_spawned:
            return  # Prevent multiple spawns
            
        # Find spawn position away from player
        attempts = 0
        spawn_positions = []
        
        # Generate potential spawn positions
        for _ in range(20):
            x = random.randint(5, MAP_WIDTH - 5)
            y = random.randint(5, MAP_HEIGHT - 5)
            if (self.game_map.is_valid_position(x, y) and
                max(abs(x - self.player.x), abs(y - self.player.y)) > 15 and
                not self.get_enemy_at(x, y)):
                spawn_positions.append((x, y))
        
        if spawn_positions:
            x, y = random.choice(spawn_positions)
            admin = Enemy(x, y, 'admin')
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.player.x, self.player.y)
            self.enemies.append(admin)
            self.admin_spawned = True
            self.add_message("*** ADMIN AVATAR HAS SPAWNED! EXTREME DANGER! ***")
        else:
            # Fallback spawn if no good positions found
            x, y = MAP_WIDTH - 10, MAP_HEIGHT - 10
            if self.game_map.is_valid_position(x, y):
                admin = Enemy(x, y, 'admin')
                admin.state = EnemyState.HOSTILE
                admin.last_seen_player = Position(self.player.x, self.player.y)
                self.enemies.append(admin)
                self.admin_spawned = True
                self.add_message("*** ADMIN AVATAR HAS SPAWNED! ***")
    
    def update_enemy_states(self):
        """Update enemy awareness states"""
        for enemy in self.enemies:
            if enemy.can_see_player(self.player, self.game_map):
                if enemy.state == EnemyState.UNAWARE:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 1
                    self.add_message(f"{enemy.type_data.name} is investigating!")
                elif enemy.state == EnemyState.ALERT:
                    enemy.alert_timer -= 1
                    if enemy.alert_timer <= 0:
                        enemy.state = EnemyState.HOSTILE
                        enemy.last_seen_player = Position(self.player.x, self.player.y)
                        self.player.detection = min(100, self.player.detection + 20)
                        self.add_message(f"{enemy.type_data.name} has detected you!")
                else:  # HOSTILE
                    enemy.last_seen_player = Position(self.player.x, self.player.y)
                    self.player.detection = min(100, self.player.detection + 2)
            else:
                if enemy.state == EnemyState.ALERT:
                    enemy.state = EnemyState.UNAWARE
                elif enemy.state == EnemyState.HOSTILE:
                    if random.random() < 0.1:  # 10% chance to calm down
                        enemy.state = EnemyState.UNAWARE
                        enemy.last_seen_player = None
    
    def move_player(self, dx: int, dy: int):
        """Move player and process turn"""
        if self.targeting_mode:
            self.move_cursor(dx, dy)
            return
            
        # Speed boost allows double movement
        moves = 2 if self.player.speed_boost_turns > 0 else 1
        
        for move_count in range(moves):
            old_x, old_y = self.player.x, self.player.y
            
            if self.player.move(dx, dy, self.game_map):
                # Check if reached gateway
                if (self.player.x == self.game_map.gateway.x and 
                    self.player.y == self.game_map.gateway.y):
                    self.add_message("Gateway reached! Moving to next network...")
                    self.next_level()
                    return
                
                # Check for combat - enemy at new position
                enemy = self.get_enemy_at(self.player.x, self.player.y)
                if enemy:
                    # Move back to previous position
                    self.player.x, self.player.y = old_x, old_y
                    self.attack_enemy(enemy)
                    return
            else:
                # Can't move further, break out of speed boost loop
                break
        
        self.process_turn()
    
    def move_cursor(self, dx: int, dy: int):
        """Move targeting cursor"""
        self.cursor_x = max(0, min(MAP_WIDTH - 1, self.cursor_x + dx))
        self.cursor_y = max(0, min(MAP_HEIGHT - 1, self.cursor_y + dy))
    
    def get_enemy_at(self, x: int, y: int) -> Optional[Enemy]:
        """Get enemy at specific position"""
        for enemy in self.enemies:
            if enemy.x == x and enemy.y == y:
                return enemy
        return None
    
    def attack_enemy(self, enemy: Enemy):
        """Attack an enemy in melee combat"""
        damage = 20
        
        # Stealth attack bonus
        if enemy.state == EnemyState.UNAWARE:
            damage *= 2
            self.add_message(f"Stealth attack on {enemy.type_data.name}! Double damage!")
        else:
            self.add_message(f"Direct attack on {enemy.type_data.name}!")
        
        if enemy.take_damage(damage):
            self.enemies.remove(enemy)
            self.player.cpu = min(self.player.max_cpu, self.player.cpu + 5)
            self.player.detection = min(100, self.player.detection + 10)
            self.add_message(f"{enemy.type_data.name} eliminated! +5 CPU, +10 detection")
        else:
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(self.player.x, self.player.y)
            self.player.detection = min(100, self.player.detection + 15)
        
        self.process_turn()
    
    def next_level(self):
        """Progress to next level with proper validation"""
        self.level += 1
        if self.level > 3:
            self.add_message("INFILTRATION COMPLETE! All networks breached!")
            self.game_over = True
        else:
            try:
                self.generate_next_level()
                self.calculate_ram_usage()
            except Exception as e:
                # Fallback if level generation fails
                self.add_message(f"Network generation error: {str(e)[:30]}")
                self.level -= 1  # Revert to previous level
    
    def generate_next_level(self):
        """Generate procedural network for levels 1-3"""
        if self.level not in NETWORK_CONFIGS:
            self.add_message(f"Invalid level: {self.level}")
            return
            
        config = NETWORK_CONFIGS[self.level]
        
        # Clear existing data
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.data_patches.clear()
        self.enemies.clear()
        self.admin_spawned = False
        
        # Generate border walls
        for x in range(MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, MAP_HEIGHT - 1))
        for y in range(MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((MAP_WIDTH - 1, y))
        
        # Generate rooms and corridors
        rooms = []
        max_rooms = 8 + self.level * 2
        attempts = 0
        while len(rooms) < max_rooms and attempts < 100:
            attempts += 1
            room_w = random.randint(4, 8)
            room_h = random.randint(4, 8)
            room_x = random.randint(2, MAP_WIDTH - room_w - 2)
            room_y = random.randint(2, MAP_HEIGHT - room_h - 2)
            
            # Check for overlap with existing rooms
            overlap = False
            for rx, ry, rw, rh in rooms:
                if (room_x < rx + rw + 1 and room_x + room_w + 1 > rx and
                    room_y < ry + rh + 1 and room_y + room_h + 1 > ry):
                    overlap = True
                    break
            
            if not overlap:
                self.game_map.generate_room(room_x, room_y, room_w, room_h)
                rooms.append((room_x, room_y, room_w, room_h))
        
        # Connect rooms with corridors
        for i in range(len(rooms) - 1):
            x1 = rooms[i][0] + rooms[i][2] // 2
            y1 = rooms[i][1] + rooms[i][3] // 2
            x2 = rooms[i + 1][0] + rooms[i + 1][2] // 2
            y2 = rooms[i + 1][1] + rooms[i + 1][3] // 2
            self.game_map.generate_corridor(x1, y1, x2, y2)
        
        # Generate shadow coverage
        shadow_tiles = int(MAP_WIDTH * MAP_HEIGHT * config["shadow_coverage"])
        shadow_attempts = 0
        while len(self.game_map.shadows) < shadow_tiles and shadow_attempts < shadow_tiles * 3:
            shadow_attempts += 1
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if not self.game_map.is_wall(x, y):
                self.game_map.shadows.add((x, y))
        
        # Generate special nodes
        for _ in range(3 + self.level):
            attempts = 0
            while attempts < 50:
                attempts += 1
                x = random.randint(1, MAP_WIDTH - 2)
                y = random.randint(1, MAP_HEIGHT - 2)
                if (not self.game_map.is_wall(x, y) and 
                    (x, y) not in self.game_map.cooling_nodes and
                    (x, y) not in self.game_map.cpu_recovery_nodes):
                    if random.choice([True, False]):
                        self.game_map.cooling_nodes.add((x, y))
                    else:
                        self.game_map.cpu_recovery_nodes.add((x, y))
                    break
        
        # Generate data patches
        for _ in range(5 + self.level * 2):
            attempts = 0
            while attempts < 50:
                attempts += 1
                x = random.randint(1, MAP_WIDTH - 2)
                y = random.randint(1, MAP_HEIGHT - 2)
                if (not self.game_map.is_wall(x, y) and 
                    (x, y) not in self.game_map.data_patches and
                    (x, y) not in self.game_map.cooling_nodes and
                    (x, y) not in self.game_map.cpu_recovery_nodes):
                    color = random.choice(list(self.data_patch_effects.keys()))
                    effect, desc = self.data_patch_effects[color]
                    patch = DataPatch(color, effect, f"{color.title()} Data Patch")
                    self.game_map.data_patches[(x, y)] = patch
                    break
        
        # Generate enemies
        enemy_types = ['scanner', 'patrol', 'bot', 'firewall', 'hunter']
        enemy_count = 0
        attempts = 0
        while enemy_count < config["enemies"] and attempts < config["enemies"] * 10:
            attempts += 1
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            
            # Don't spawn too close to player start position
            if (self.game_map.is_valid_position(x, y) and
                max(abs(x - 5), abs(y - 5)) > 10 and  # Player starts at 5,5
                not self.get_enemy_at(x, y)):
                
                enemy_type = random.choice(enemy_types)
                enemy = Enemy(x, y, enemy_type)
                
                # Generate patrol routes for patrol enemies
                if enemy_type == 'patrol':
                    enemy.patrol_points = self.generate_patrol_route(x, y)
                
                self.enemies.append(enemy)
                enemy_count += 1
        
        # Generate gateway
        gateway_placed = False
        attempts = 0
        while not gateway_placed and attempts < 100:
            attempts += 1
            x = random.randint(1, MAP_WIDTH - 2)
            y = random.randint(1, MAP_HEIGHT - 2)
            if (self.game_map.is_valid_position(x, y) and
                max(abs(x - 5), abs(y - 5)) > 20 and  # Far from player start
                (x, y) not in self.game_map.data_patches and
                (x, y) not in self.game_map.cooling_nodes and
                (x, y) not in self.game_map.cpu_recovery_nodes and
                not self.get_enemy_at(x, y)):
                self.game_map.gateway = Position(x, y)
                gateway_placed = True
        
        # Fallback gateway placement if all else fails
        if not gateway_placed:
            self.game_map.gateway = Position(MAP_WIDTH - 5, MAP_HEIGHT - 5)
        
        # Reset player position to a safe starting area
        self.player.x, self.player.y = 5, 5
        self.player.detection = 0
        
        self.add_message(f"{config['name']} generated. {len(self.enemies)} security processes active.")
    
    def generate_patrol_route(self, start_x: int, start_y: int) -> List[Position]:
        """Generate a patrol route for an enemy"""
        route = [Position(start_x, start_y)]
        route_length = random.randint(2, 4)
        
        current_x, current_y = start_x, start_y
        
        for _ in range(route_length - 1):
            # Try to find a valid patrol point
            attempts = 0
            while attempts < 20:
                attempts += 1
                direction = random.choice([(0, -5), (5, 0), (0, 5), (-5, 0)])
                new_x = current_x + direction[0]
                new_y = current_y + direction[1]
                
                # Ensure the new position is within bounds and valid
                if (1 <= new_x < MAP_WIDTH - 1 and 1 <= new_y < MAP_HEIGHT - 1 and
                    self.game_map.is_valid_position(new_x, new_y)):
                    route.append(Position(new_x, new_y))
                    current_x, current_y = new_x, new_y
                    break
        
        # Ensure we have at least 2 points
        if len(route) < 2:
            route.append(Position(start_x + 1 if start_x < MAP_WIDTH - 2 else start_x - 1, start_y))
        
    def calculate_ram_usage(self):
        """Calculate current RAM usage from loaded exploits"""
        total_ram = 0
        for exploit_key in self.loaded_exploits:
            if exploit_key in EXPLOITS:
                total_ram += EXPLOITS[exploit_key].ram
        self.player.ram_used = total_ram
        return total_ram.randint(2, 4)
        
        current_x, current_y = start_x, start_y
        
        for _ in range(route_length - 1):
            # Try to find a valid patrol point
            attempts = 0
            while attempts < 20:
                direction = random.choice([(0, -5), (5, 0), (0, 5), (-5, 0)])
                new_x = current_x + direction[0]
                new_y = current_y + direction[1]
                
                if self.game_map.is_valid_position(new_x, new_y):
                    route.append(Position(new_x, new_y))
                    current_x, current_y = new_x, new_y
                    break
                attempts += 1
        
        return route
    
    def use_exploit(self, exploit_key: str):
        """Use an exploit"""
        if exploit_key not in self.loaded_exploits:
            self.add_message("Exploit not loaded!")
            return
            
        exploit = EXPLOITS[exploit_key]
        
        if self.player.heat + exploit.heat > 100:
            self.add_message("System too hot! Cannot use exploit.")
            return
        
        # Check if exploit requires targeting
        if exploit.targeting != TargetingMode.NONE and exploit.range > 0:
            self.targeting_mode = True
            self.targeting_exploit = exploit_key
            self.cursor_x = self.player.x
            self.cursor_y = self.player.y
            self.add_message(f"Select target for {exploit.name} (Enter to confirm, ESC to cancel)")
            return
        
        # Execute non-targeting exploits immediately
        self.execute_exploit(exploit_key, self.player.x, self.player.y)
    
    def execute_exploit(self, exploit_key: str, target_x: int, target_y: int):
        """Execute an exploit at target location"""
        exploit = EXPLOITS[exploit_key]
        
        # Check range
        distance = max(abs(target_x - self.player.x), abs(target_y - self.player.y))
        if distance > exploit.range:
            self.add_message("Target out of range!")
            return
        
        # Apply heat with efficiency bonus
        heat_multiplier = 0.5 if self.player.exploit_efficiency_turns > 0 else 1.0
        heat_cost = int(exploit.heat * heat_multiplier)
        self.player.heat = min(100, self.player.heat + heat_cost)
        
        # Execute exploit effects
        if exploit_key == 'shadow_step':
            if self.game_map.is_shadow(target_x, target_y):
                self.player.x = target_x
                self.player.y = target_y
                self.add_message("Shadow Step executed!")
            else:
                self.add_message("Target must be a shadow zone!")
                return
        
        elif exploit_key == 'data_mimic':
            self.player.data_mimic_turns = 5
            self.add_message("Data Mimic activated! You appear as harmless data.")
        
        elif exploit_key == 'noise_maker':
            # Attract nearby enemies to the target location
            attracted = 0
            for enemy in self.enemies:
                if (enemy.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.RANDOM] and
                    max(abs(enemy.x - target_x), abs(enemy.y - target_y)) <= 8):
                    enemy.last_seen_player = Position(target_x, target_y)
                    enemy.state = EnemyState.ALERT
                    attracted += 1
            self.add_message(f"Noise created! {attracted} enemies attracted.")
        
        elif exploit_key == 'code_injection':
            target_enemy = self.get_enemy_at(target_x, target_y)
            if target_enemy:
                damage = 30
                # Bypass firewall armor
                if target_enemy.type == 'firewall':
                    damage = 30  # Full damage to firewalls
                
                if target_enemy.take_damage(damage):
                    self.enemies.remove(target_enemy)
                    self.player.cpu = min(self.player.max_cpu, self.player.cpu + 5)
                    self.add_message(f"Code injection eliminated {target_enemy.type_data.name}!")
                else:
                    self.add_message(f"Code injection damaged {target_enemy.type_data.name}!")
                    target_enemy.state = EnemyState.HOSTILE
                    target_enemy.last_seen_player = Position(self.player.x, self.player.y)
            else:
                self.add_message("No target at location!")
        
        elif exploit_key == 'buffer_overflow':
            target_enemy = self.get_enemy_at(target_x, target_y)
            if target_enemy and distance <= 1:
                damage = 40  # High damage, armor piercing
                if target_enemy.take_damage(damage):
                    self.enemies.remove(target_enemy)
                    self.player.cpu = min(self.player.max_cpu, self.player.cpu + 5)
                    self.add_message(f"Buffer overflow eliminated {target_enemy.type_data.name}!")
                else:
                    self.add_message(f"Buffer overflow damaged {target_enemy.type_data.name}!")
                    target_enemy.state = EnemyState.HOSTILE
            else:
                self.add_message("Must target adjacent enemy!")
        
        elif exploit_key == 'system_crash':
            # Area effect damage
            enemies_hit = []
            for enemy in self.enemies:
                if max(abs(enemy.x - target_x), abs(enemy.y - target_y)) <= exploit.range:
                    enemy.disabled_turns = 3
                    enemy.state = EnemyState.UNAWARE
                    enemies_hit.append(enemy)
            self.add_message(f"System crash disabled {len(enemies_hit)} enemies!")
        
        elif exploit_key == 'emp_burst':
            # Area effect disable around target point, not player
            enemies_hit = []
            for enemy in self.enemies:
                if max(abs(enemy.x - target_x), abs(enemy.y - target_y)) <= exploit.range:
                    enemy.disabled_turns = 5
                    enemy.state = EnemyState.UNAWARE
                    enemies_hit.append(enemy)
            self.add_message(f"EMP burst disabled {len(enemies_hit)} enemies!")
        
        elif exploit_key == 'network_scan':
            self.show_patrols = True
            # Reset patrol visibility after some turns
            def reset_patrols():
                self.show_patrols = False
            # Note: In a real implementation, you'd use a timer system
            self.add_message("Network scan reveals enemy positions and routes!")
        
        elif exploit_key == 'log_wiper':
            self.player.detection = max(0, self.player.detection - 25)
            self.add_message("Detection level reduced by 25%!")
        
        self.targeting_mode = False
        self.targeting_exploit = None
        self.process_turn()

def render_ui(console, game):
    """Render the UI panel"""
    # Clear panel area
    console.draw_rect(0, PANEL_Y, SCREEN_WIDTH, PANEL_HEIGHT, 0, bg=Colors.ui_bg)
    
    # Status line 1
    cpu_text = f"CPU: {game.player.cpu}/{game.player.max_cpu}"
    heat_text = f"Heat: {game.player.heat}°C"
    detection_text = f"Detection: {int(game.player.detection)}%"
    
    console.print(1, PANEL_Y + 1, cpu_text, fg=Colors.ui_text)
    console.print(20, PANEL_Y + 1, heat_text, fg=Colors.ui_text)
    console.print(40, PANEL_Y + 1, detection_text, fg=Colors.ui_text)
    
    # Status line 2
    ram_text = f"RAM: {game.player.ram_used}/{game.player.ram_total} GB"
    level_names = {0: "Tutorial", 1: "Corporate", 2: "Government", 3: "Military"}
    level_text = f"Network: {level_names.get(game.level, 'Unknown')}"
    turn_text = f"Turn: {game.turn}"
    
    console.print(1, PANEL_Y + 2, ram_text, fg=Colors.ui_text)
    console.print(25, PANEL_Y + 2, level_text, fg=Colors.ui_text)
    console.print(50, PANEL_Y + 2, turn_text, fg=Colors.ui_text)
    
    # Active effects
    effects = []
    if game.player.data_mimic_turns > 0:
        effects.append(f"Mimic({game.player.data_mimic_turns})")
    if game.player.speed_boost_turns > 0:
        effects.append(f"Speed({game.player.speed_boost_turns})")
    if game.player.enhanced_vision_turns > 0:
        effects.append(f"Vision({game.player.enhanced_vision_turns})")
    if game.player.exploit_efficiency_turns > 0:
        effects.append(f"Efficiency({game.player.exploit_efficiency_turns})")
    if game.network_scan_turns > 0:
        effects.append(f"Scan({game.network_scan_turns})")
    
    if effects:
        effects_text = "Effects: " + " ".join(effects)
        console.print(1, PANEL_Y + 3, effects_text[:SCREEN_WIDTH-2], fg=Colors.cyan)
    
    # Loaded exploits
    console.print(1, PANEL_Y + 4, "Exploits:", fg=Colors.ui_text)
    for i, exploit_key in enumerate(game.loaded_exploits[:5]):  # Show first 5
        if exploit_key in EXPLOITS:
            exploit = EXPLOITS[exploit_key]
            heat_ok = game.player.heat + exploit.heat <= 100
            color = Colors.ui_text if heat_ok else Colors.red
            exploit_text = f"{i+1}.{exploit.name[:8]}"
            console.print(12 + i * 15, PANEL_Y + 4, exploit_text, fg=color)
    
    # Detection warning
    if game.player.detection >= 75:
        warning_text = "*** HIGH DETECTION - ADMIN AVATAR IMMINENT ***"
        console.print(1, PANEL_Y + 5, warning_text, fg=Colors.red)
    elif game.player.detection >= 50:
        warning_text = "** ELEVATED DETECTION LEVEL **"
        console.print(1, PANEL_Y + 5, warning_text, fg=Colors.yellow)
    
    # Messages
    console.print(1, PANEL_Y + 6, "SYSTEM LOG:", fg=Colors.ui_text)
    for i, message in enumerate(game.messages[-3:]):  # Show last 3 messages
        console.print(1, PANEL_Y + 7 + i, message[:SCREEN_WIDTH-2], fg=Colors.green)
    
    # Targeting mode info
    if game.targeting_mode and game.targeting_exploit in EXPLOITS:
        console.print(1, PANEL_Y + 5, f"Targeting: {EXPLOITS[game.targeting_exploit].name}", fg=Colors.yellow)
    
    # Vision range indicator
    vision_info = f"Vision: {game.player.get_vision_range()}"
    if game.player.enhanced_vision_turns > 0:
        vision_info += " (Enhanced)"
    console.print(60, PANEL_Y + 2, vision_info, fg=Colors.ui_text)

def render_map(console, game):
    """Render the game map"""
    # Calculate camera offset to center on player
    camera_x = game.player.x - SCREEN_WIDTH // 2
    camera_y = game.player.y - (SCREEN_HEIGHT - PANEL_HEIGHT) // 2
    
    # Render floor
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT - PANEL_HEIGHT):
            world_x = x + camera_x
            world_y = y + camera_y
            
            if (0 <= world_x < MAP_WIDTH and 0 <= world_y < MAP_HEIGHT):
                # Player vision range (15 tiles)
                distance = max(abs(world_x - game.player.x), abs(world_y - game.player.y))
                if distance <= 15:
                    if game.game_map.is_wall(world_x, world_y):
                        console.put_char(x, y, ord('█'), fg=Colors.wall, bg=Colors.black)
                    elif game.game_map.is_shadow(world_x, world_y):
                        console.put_char(x, y, ord('◉'), fg=Colors.green, bg=Colors.shadow)
                    else:
                        console.put_char(x, y, ord('.'), fg=Colors.floor, bg=Colors.black)
                else:
                    # Fog of war
                    console.put_char(x, y, ord(' '), fg=Colors.black, bg=Colors.black)
    
    # Render enemy vision ranges (semi-transparent)
    for enemy in game.enemies:
        enemy_screen_x = enemy.x - camera_x
        enemy_screen_y = enemy.y - camera_y
        
        # Check if enemy is visible to player
        distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
        if distance_to_player <= 15:
            # Draw vision range
            for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                    if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                        vx = enemy_screen_x + dx
                        vy = enemy_screen_y + dy
                        if (0 <= vx < SCREEN_WIDTH and 0 <= vy < SCREEN_HEIGHT - PANEL_HEIGHT):
                            # Dim the background to show vision range
                            console.rgb[vx, vy] = console.rgb[vx, vy] * 0.7 + (255, 136, 0) * 0.3
    
    # Render gateway
    if game.game_map.gateway:
        gw_x = game.game_map.gateway.x - camera_x
        gw_y = game.game_map.gateway.y - camera_y
        if (0 <= gw_x < SCREEN_WIDTH and 0 <= gw_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(game.game_map.gateway.x - game.player.x), 
                          abs(game.game_map.gateway.y - game.player.y))
            if distance <= 15:
                console.put_char(gw_x, gw_y, ord('>'), fg=Colors.gateway, bg=Colors.black)
    
    # Render enemies
    for enemy in game.enemies:
        enemy_x = enemy.x - camera_x
        enemy_y = enemy.y - camera_y
        if (0 <= enemy_x < SCREEN_WIDTH and 0 <= enemy_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance <= 15:
                console.put_char(enemy_x, enemy_y, ord(enemy.type_data.symbol), 
                                fg=enemy.get_color(), bg=Colors.black)
    
    # Render player
    player_x = game.player.x - camera_x
    player_y = game.player.y - camera_y
    if (0 <= player_x < SCREEN_WIDTH and 0 <= player_y < SCREEN_HEIGHT - PANEL_HEIGHT):
        console.put_char(player_x, player_y, ord('@'), fg=Colors.player, bg=Colors.black)

def main():
    """Main game loop"""
    # Initialize tcod with fallback for missing tileset
    try:
        tileset = tcod.tileset.load_tilesheet(
            "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
        )
    except (FileNotFoundError, ImportError):
        # Use default tileset if font file is missing or tcod import fails
        try:
            tileset = tcod.tileset.load_tilesheet(
                tcod.tileset.get_default(), 16, 16, tcod.tileset.CHARMAP_TCOD
            )
        except:
            # Final fallback - create a minimal tileset
            tileset = None
    
    context_args = {
        "width": SCREEN_WIDTH,
        "height": SCREEN_HEIGHT,
        "title": "Rogue Signal Protocol v7.0 - Hacker Stealth Dungeon Crawler",
        "vsync": True
    }
    
    if tileset:
        context_args["tileset"] = tileset
    
    with tcod.context.new_terminal(**context_args) as context:
        console = tcod.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")
        game = Game()
        
        # Show initial tutorial message
        game.add_message("Welcome to Rogue Signal Protocol v7.0")
        game.add_message("Navigate using stealth. Reach the gateway (>).")
        game.add_message("Hide in shadows (◉) to avoid detection.")
        
        while True:
            console.clear()
            
            # Render game
            render_map(console, game)
            render_ui(console, game)
            
            # Instructions
            if game.targeting_mode:
                console.print(1, 0, "TARGETING MODE: WASD/Arrows: Move cursor | Enter: Confirm | ESC: Cancel", 
                             fg=Colors.yellow)
            else:
                instructions = "WASD/Arrows: Move | Space: Wait | Tab: Patrols | 1-3: Exploits | ESC: Quit"
                if game.player.speed_boost_turns > 0:
                    instructions += " | SPEED BOOST ACTIVE!"
                console.print(1, 0, instructions, fg=Colors.ui_text)
            
            # Game over check
            if game.game_over:
                console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2, 
                             "MISSION COMPLETE!", fg=Colors.green, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 + 1, 
                             "All networks infiltrated successfully!", fg=Colors.green)
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 + 3, 
                             "Press ESC to exit", fg=Colors.ui_text)
            
            # CPU death check
            if game.player.cpu <= 0:
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2, 
                             "SYSTEM FAILURE", fg=Colors.red, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 12, SCREEN_HEIGHT // 2 + 1, 
                             "Your consciousness has been purged", fg=Colors.red)
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 + 3, 
                             "Press ESC to exit", fg=Colors.ui_text)
            
            context.present(console)
            
            # Handle input
            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()
                elif event.type == "KEYDOWN":
                    if event.sym == tcod.event.K_ESCAPE:
                        if game.targeting_mode:
                            game.targeting_mode = False
                            game.targeting_exploit = None
                            game.add_message("Targeting cancelled.")
                        else:
                            raise SystemExit()
                    
                    elif game.player.cpu <= 0 or game.game_over:
                        # Only allow ESC when dead or game over
                        continue
                    
                    elif game.targeting_mode:
                        # Targeting mode controls
                        if event.sym in (tcod.event.K_UP, tcod.event.K_w):
                            game.move_cursor(0, -1)
                        elif event.sym in (tcod.event.K_DOWN, tcod.event.K_s):
                            game.move_cursor(0, 1)
                        elif event.sym in (tcod.event.K_LEFT, tcod.event.K_a):
                            game.move_cursor(-1, 0)
                        elif event.sym in (tcod.event.K_RIGHT, tcod.event.K_d):
                            game.move_cursor(1, 0)
                        elif event.sym in (tcod.event.K_RETURN, tcod.event.K_KP_ENTER):
                            game.execute_exploit(game.targeting_exploit, game.cursor_x, game.cursor_y)
                    
                    else:
                        # Normal game controls
                        if event.sym in (tcod.event.K_UP, tcod.event.K_w):
                            game.move_player(0, -1)
                        elif event.sym in (tcod.event.K_DOWN, tcod.event.K_s):
                            game.move_player(0, 1)
                        elif event.sym in (tcod.event.K_LEFT, tcod.event.K_a):
                            game.move_player(-1, 0)
                        elif event.sym in (tcod.event.K_RIGHT, tcod.event.K_d):
                            game.move_player(1, 0)
                        elif event.sym == tcod.event.K_SPACE:
                            game.process_turn()
                        elif event.sym == tcod.event.K_TAB:
                            game.show_patrols = not game.show_patrols
                            game.add_message("Patrols " + ("visible" if game.show_patrols else "hidden"))
                        elif event.sym == tcod.event.K_1 and len(game.loaded_exploits) > 0:
                            game.use_exploit(game.loaded_exploits[0])
                        elif event.sym == tcod.event.K_2 and len(game.loaded_exploits) > 1:
                            game.use_exploit(game.loaded_exploits[1])
                        elif event.sym == tcod.event.K_3 and len(game.loaded_exploits) > 2:
                            game.use_exploit(game.loaded_exploits[2])
                        elif event.sym == tcod.event.K_4 and len(game.loaded_exploits) > 3:
                            game.use_exploit(game.loaded_exploits[3])
                        elif event.sym == tcod.event.K_5 and len(game.loaded_exploits) > 4:
                            game.use_exploit(game.loaded_exploits[4])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running game: {e}")
        print("Make sure you have 'pip install tcod' and optionally download dejavu10x10_gs_tc.png")
        print("The game will use a fallback font if the PNG is missing.")
