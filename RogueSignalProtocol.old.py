#!/usr/bin/env python3
"""
Rogue Signal Protocol v49 - Fixed Version
A stealth-focused traditional roguelike using Python and tcod
"""

import tcod
import logging
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Constants
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
MAP_WIDTH = 50
MAP_HEIGHT = 50
PANEL_HEIGHT = 10
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

# Game balance constants
ADMIN_SPAWN_THRESHOLDS = {0: 100, 1: 100, 2: 75, 3: 50}
NETWORK_CONFIGS = {
    1: {"enemies": 8, "shadow_coverage": 0.4, "name": "Corporate Network"},
    2: {"enemies": 12, "shadow_coverage": 0.25, "name": "Government System"},
    3: {"enemies": 16, "shadow_coverage": 0.15, "name": "Military Backbone"}
}

# Colors - Using modern tcod color format
class Colors:
    white = (255, 255, 255)
    black = (0, 0, 0)
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    yellow = (255, 255, 0)
    cyan = (0, 255, 255)
    magenta = (255, 0, 255)
    orange = (255, 136, 0)
    
    # Game Colors
    floor = (0, 50, 0)
    wall = (200, 200, 200)
    shadow = (0, 20, 0)
    player = (0, 255, 255)
    gateway = (255, 255, 0)
    
    # Enemy Colors
    enemy_unaware = (255, 136, 0)
    enemy_alert = (255, 255, 0)
    enemy_hostile = (255, 0, 0)
    
    # Vision overlays
    vision_unaware = (80, 40, 0)
    vision_alert = (80, 80, 0)
    vision_hostile = (80, 0, 0)
    
    # UI
    ui_bg = (0, 20, 0)
    ui_text = (0, 255, 0)

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
        self.data_mimic_turns = 0
        self.speed_boost_turns = 0
        self.enhanced_vision_turns = 0
        self.exploit_efficiency_turns = 0
        self.vision_range = 15
        self.stealth_bonus_active = False
        self.last_position = Position(x, y)
        
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
            base_range += 5
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
        self.disabled_turns = 0
        self.last_seen_player = None
        
    def get_color(self):
        if self.disabled_turns > 0:
            return Colors.blue
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
            
        if player.is_invisible():
            return False
            
        if game_map.is_shadow(player.x, player.y):
            return False
            
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
            # Move towards next patrol point one step at a time
            target = self.patrol_points[self.patrol_index]
            if self.x == target.x and self.y == target.y:
                # Reached current patrol point, move to next
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
                target = self.patrol_points[self.patrol_index]
            
            # Move one step toward target
            self.move_toward(target.x, target.y, game_map)
        elif self.type_data.movement == EnemyMovement.SEEK:
            if self.state == EnemyState.HOSTILE and self.last_seen_player:
                self.move_toward(self.last_seen_player.x, self.last_seen_player.y, game_map)
        elif self.type_data.movement == EnemyMovement.TRACK:
            if self.state == EnemyState.HOSTILE:
                self.move_toward(player.x, player.y, game_map)
    
    def get_predicted_moves(self, count: int = 3) -> List[Position]:
        """Get predicted next moves for UI display"""
        predicted = []
        
        if self.type_data.movement == EnemyMovement.STATIC:
            for _ in range(count):
                predicted.append(Position(self.x, self.y))
                
        elif self.type_data.movement == EnemyMovement.LINEAR and self.patrol_points:
            current_index = self.patrol_index
            for i in range(count):
                next_index = (current_index + i + 1) % len(self.patrol_points)
                predicted.append(self.patrol_points[next_index])
                
        elif self.type_data.movement == EnemyMovement.RANDOM:
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            for i in range(count):
                dx, dy = directions[i % len(directions)]
                predicted.append(Position(self.x + dx, self.y + dy))
                
        else:
            for _ in range(count):
                predicted.append(Position(self.x, self.y))
                
        return predicted
    
    def move_toward(self, target_x: int, target_y: int, game_map):
        """Move one step toward target using simple pathfinding"""
        if target_x < 0 or target_x >= MAP_WIDTH or target_y < 0 or target_y >= MAP_HEIGHT:
            return
            
        dx = 0 if self.x == target_x else (1 if target_x > self.x else -1)
        dy = 0 if self.y == target_y else (1 if target_y > self.y else -1)
        
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
        self.cooling_nodes = set()
        self.cpu_recovery_nodes = set()
        self.data_patches = {}
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
        for i in range(width):
            self.walls.add((x + i, y))
            self.walls.add((x + i, y + height - 1))
        for i in range(height):
            self.walls.add((x, y + i))
            self.walls.add((x + width - 1, y + i))
    
    def generate_corridor(self, x1: int, y1: int, x2: int, y2: int):
        """Generate a corridor between two points"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.walls.discard((x, y1))
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.walls.discard((x2, y))

class Game:
    def __init__(self):
        self.player = Player(5, 5)
        self.enemies = []
        self.game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
        self.level = 0
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
        self.show_patrol_predictions = False
        self.network_scan_turns = 0
        
        self.tutorial_active = False
        self.tutorial_step = 0
        self.tutorial_completed = False
        
        self.noise_locations = []
        self.distraction_points = {}
        
        self.data_patch_effects = {}
        self.randomize_data_patches()
        
        self.generate_tutorial_network()
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
        
        # Set patrol route for patrol enemy - closer points for 1-step movement
        self.enemies[1].patrol_points = [
            Position(25, 25),
            Position(26, 25),
            Position(26, 26),
            Position(25, 26)
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
        max_length = SCREEN_WIDTH - 4
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        self.messages.append(text)
        if len(self.messages) > 10:
            self.messages = self.messages[-10:]
    
    def process_turn(self):
        """Process one game turn"""
        self.turn += 1
        
        # Update player effects
        self.player.update_effects()
        
        # Cool down heat
        heat_reduction = 3 if self.player.exploit_efficiency_turns > 0 else 2
        self.player.heat = max(0, self.player.heat - heat_reduction)
        
        # Decrease network scan timer
        if self.network_scan_turns > 0:
            self.network_scan_turns -= 1
            if self.network_scan_turns == 0:
                self.show_patrols = False
                self.add_message("Network scan expired.")
        
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
            return
            
        spawn_positions = []
        
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
                else:
                    enemy.last_seen_player = Position(self.player.x, self.player.y)
                    self.player.detection = min(100, self.player.detection + 2)
            else:
                if enemy.state == EnemyState.ALERT:
                    enemy.state = EnemyState.UNAWARE
                elif enemy.state == EnemyState.HOSTILE:
                    if random.random() < 0.1:
                        enemy.state = EnemyState.UNAWARE
                        enemy.last_seen_player = None
    
    def move_player(self, dx: int, dy: int):
        """Move player and process turn"""
        if self.targeting_mode:
            self.move_cursor(dx, dy)
            return
            
        moves = 2 if self.player.speed_boost_turns > 0 else 1
        
        for move_count in range(moves):
            old_x, old_y = self.player.x, self.player.y
            
            if self.player.move(dx, dy, self.game_map):
                if (self.player.x == self.game_map.gateway.x and 
                    self.player.y == self.game_map.gateway.y):
                    self.add_message("Gateway reached! Moving to next network...")
                    self.next_level()
                    return
                
                enemy = self.get_enemy_at(self.player.x, self.player.y)
                if enemy:
                    self.player.x, self.player.y = old_x, old_y
                    self.attack_enemy(enemy)
                    return
            else:
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
                self.add_message(f"Network generation error: {str(e)[:30]}")
                self.level -= 1
    
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
            
            if (self.game_map.is_valid_position(x, y) and
                max(abs(x - 5), abs(y - 5)) > 10 and
                not self.get_enemy_at(x, y)):
                
                enemy_type = random.choice(enemy_types)
                enemy = Enemy(x, y, enemy_type)
                
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
                max(abs(x - 5), abs(y - 5)) > 20 and
                (x, y) not in self.game_map.data_patches and
                (x, y) not in self.game_map.cooling_nodes and
                (x, y) not in self.game_map.cpu_recovery_nodes and
                not self.get_enemy_at(x, y)):
                self.game_map.gateway = Position(x, y)
                gateway_placed = True
        
        if not gateway_placed:
            self.game_map.gateway = Position(MAP_WIDTH - 5, MAP_HEIGHT - 5)
        
        self.player.x, self.player.y = 5, 5
        self.player.detection = 0
        
        self.add_message(f"{config['name']} generated. {len(self.enemies)} security processes active.")
    
    def generate_patrol_route(self, start_x: int, start_y: int) -> List[Position]:
        """Generate a patrol route for an enemy - closer points for single-step movement"""
        route = [Position(start_x, start_y)]
        route_length = random.randint(3, 6)  # More points for shorter distances
        
        current_x, current_y = start_x, start_y
        
        for _ in range(route_length - 1):
            attempts = 0
            while attempts < 20:
                attempts += 1
                # Use smaller steps for single-space movement
                direction = random.choice([(0, -2), (2, 0), (0, 2), (-2, 0), (1, 1), (-1, -1)])
                new_x = current_x + direction[0]
                new_y = current_y + direction[1]
                
                if (1 <= new_x < MAP_WIDTH - 1 and 1 <= new_y < MAP_HEIGHT - 1 and
                    self.game_map.is_valid_position(new_x, new_y)):
                    route.append(Position(new_x, new_y))
                    current_x, current_y = new_x, new_y
                    break
        
        if len(route) < 2:
            route.append(Position(start_x + 1 if start_x < MAP_WIDTH - 2 else start_x - 1, start_y))
        
        return route
        
    def calculate_ram_usage(self):
        """Calculate current RAM usage from loaded exploits"""
        total_ram = 0
        for exploit_key in self.loaded_exploits:
            if exploit_key in EXPLOITS:
                total_ram += EXPLOITS[exploit_key].ram
        self.player.ram_used = total_ram
    
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
                if target_enemy.type == 'firewall':
                    damage = 30
                
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
                damage = 40
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
            enemies_hit = []
            for enemy in self.enemies:
                if max(abs(enemy.x - target_x), abs(enemy.y - target_y)) <= exploit.range:
                    enemy.disabled_turns = 3
                    enemy.state = EnemyState.UNAWARE
                    enemies_hit.append(enemy)
            self.add_message(f"System crash disabled {len(enemies_hit)} enemies!")
        
        elif exploit_key == 'emp_burst':
            enemies_hit = []
            for enemy in self.enemies:
                if max(abs(enemy.x - target_x), abs(enemy.y - target_y)) <= exploit.range:
                    enemy.disabled_turns = 5
                    enemy.state = EnemyState.UNAWARE
                    enemies_hit.append(enemy)
            self.add_message(f"EMP burst disabled {len(enemies_hit)} enemies!")
        
        elif exploit_key == 'network_scan':
            self.show_patrols = True
            self.network_scan_turns = 10
            self.add_message("Network scan reveals enemy positions and routes!")
        
        elif exploit_key == 'log_wiper':
            self.player.detection = max(0, self.player.detection - 25)
            self.add_message("Detection level reduced by 25%!")
        
        self.targeting_mode = False
        self.targeting_exploit = None
        self.process_turn()

def render_ui(console, game):
    """Render the UI panel with proper formatting"""
    # Clear panel area
    for x in range(SCREEN_WIDTH):
        for y in range(PANEL_Y, SCREEN_HEIGHT):
            console.print(x, y, ' ', fg=Colors.ui_text, bg=Colors.ui_bg)
    
    # Status line 1 - Core stats
    console.print(1, PANEL_Y + 1, f"CPU:{game.player.cpu:3d}/{game.player.max_cpu:3d}", fg=Colors.ui_text)
    console.print(16, PANEL_Y + 1, f"Heat:{game.player.heat:3d}°C", fg=Colors.ui_text)
    console.print(30, PANEL_Y + 1, f"Detection:{int(game.player.detection):3d}%", fg=Colors.ui_text)
    console.print(50, PANEL_Y + 1, f"Turn:{game.turn:4d}", fg=Colors.ui_text)
    
    # Status line 2 - Resources and location
    console.print(1, PANEL_Y + 2, f"RAM:{game.player.ram_used:2d}/{game.player.ram_total:2d}GB", fg=Colors.ui_text)
    level_names = {0: "Tutorial", 1: "Corporate", 2: "Government", 3: "Military"}
    console.print(16, PANEL_Y + 2, f"Net:{level_names.get(game.level, 'Unknown')}", fg=Colors.ui_text)
    console.print(35, PANEL_Y + 2, f"Vision:{game.player.get_vision_range():2d}", fg=Colors.ui_text)
    console.print(50, PANEL_Y + 2, f"Pos:({game.player.x:2d},{game.player.y:2d})", fg=Colors.ui_text)
    
    # Status line 3 - Active effects
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
    
    # Status line 4 - Loaded exploits with heat check
    console.print(1, PANEL_Y + 4, "Exploits:", fg=Colors.ui_text)
    for i, exploit_key in enumerate(game.loaded_exploits[:5]):
        if exploit_key in EXPLOITS:
            exploit = EXPLOITS[exploit_key]
            heat_ok = game.player.heat + exploit.heat <= 100
            color = Colors.green if heat_ok else Colors.red
            exploit_text = f"{i+1}.{exploit.name[:10]}"
            x_pos = 11 + i * 14
            if x_pos < SCREEN_WIDTH - 10:
                console.print(x_pos, PANEL_Y + 4, exploit_text, fg=color)
    
    # Status line 5 - Warnings and targeting
    if game.targeting_mode and game.targeting_exploit in EXPLOITS:
        console.print(1, PANEL_Y + 5, f"TARGETING: {EXPLOITS[game.targeting_exploit].name}", fg=Colors.yellow)
    elif game.player.detection >= 75:
        console.print(1, PANEL_Y + 5, "*** HIGH DETECTION - ADMIN AVATAR IMMINENT ***", fg=Colors.red)
    elif game.player.detection >= 50:
        console.print(1, PANEL_Y + 5, "** ELEVATED DETECTION LEVEL **", fg=Colors.yellow)
    else:
        console.print(1, PANEL_Y + 5, "Status: Operational", fg=Colors.green)
    
    # System log header
    console.print(1, PANEL_Y + 6, "SYSTEM LOG:", fg=Colors.ui_text)
    
    # Messages - last 3 lines
    for i, message in enumerate(game.messages[-3:]):
        y_pos = PANEL_Y + 7 + i
        if y_pos < SCREEN_HEIGHT:
            console.print(1, y_pos, message[:SCREEN_WIDTH-2], fg=Colors.green)

def render_map(console, game):
    """Render the game map with enemy vision ranges"""
    # Calculate camera offset to center on player
    camera_x = game.player.x - SCREEN_WIDTH // 2
    camera_y = game.player.y - (SCREEN_HEIGHT - PANEL_HEIGHT) // 2
    
    vision_range = game.player.get_vision_range()
    
    # First pass: Render basic terrain
    for x in range(SCREEN_WIDTH):
        for y in range(SCREEN_HEIGHT - PANEL_HEIGHT):
            world_x = x + camera_x
            world_y = y + camera_y
            
            if (0 <= world_x < MAP_WIDTH and 0 <= world_y < MAP_HEIGHT):
                distance = max(abs(world_x - game.player.x), abs(world_y - game.player.y))
                if distance <= vision_range:
                    # Check what's at this position
                    if game.game_map.is_wall(world_x, world_y):
                        console.print(x, y, '#', fg=Colors.wall, bg=Colors.black)
                    elif game.game_map.is_shadow(world_x, world_y):
                        console.print(x, y, '.', fg=Colors.green, bg=Colors.shadow)
                    elif game.game_map.is_cooling_node(world_x, world_y):
                        console.print(x, y, 'C', fg=Colors.cyan, bg=Colors.black)
                    elif game.game_map.is_cpu_recovery_node(world_x, world_y):
                        console.print(x, y, '+', fg=Colors.red, bg=Colors.black)
                    elif (world_x, world_y) in game.game_map.data_patches:
                        patch = game.game_map.data_patches[(world_x, world_y)]
                        color_map = {
                            'crimson': Colors.red, 'azure': Colors.blue, 'emerald': Colors.green,
                            'golden': Colors.yellow, 'violet': Colors.magenta, 'silver': Colors.white
                        }
                        console.print(x, y, 'D', fg=color_map.get(patch.color, Colors.white), bg=Colors.black)
                    elif (world_x, world_y) in game.distraction_points:
                        console.print(x, y, '~', fg=Colors.yellow, bg=Colors.black)
                    else:
                        console.print(x, y, '.', fg=Colors.floor, bg=Colors.black)
                else:
                    # Fog of war
                    console.print(x, y, ' ', fg=Colors.black, bg=Colors.black)
    
    # Second pass: Render enemy vision ranges (when not invisible)
    if not game.player.is_invisible():
        for enemy in game.enemies:
            enemy_screen_x = enemy.x - camera_x
            enemy_screen_y = enemy.y - camera_y
            
            # Check if enemy is visible to player
            distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance_to_player <= vision_range and enemy.disabled_turns == 0:
                # Determine vision overlay color based on enemy state
                if enemy.state == EnemyState.HOSTILE:
                    overlay_color = Colors.vision_hostile
                elif enemy.state == EnemyState.ALERT:
                    overlay_color = Colors.vision_alert
                else:
                    overlay_color = Colors.vision_unaware
                
                # Draw vision range as subtle background overlay
                for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                    for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                        if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                            vx = enemy_screen_x + dx
                            vy = enemy_screen_y + dy
                            if (0 <= vx < SCREEN_WIDTH and 0 <= vy < SCREEN_HEIGHT - PANEL_HEIGHT):
                                # Get current character and modify its background
                                current_char = console.ch[vx, vy]
                                current_fg = console.fg[vx, vy]
                                if current_char != ord(' '):  # Don't overlay fog of war
                                    # Convert numpy array to tuple
                                    if hasattr(current_fg, 'tolist'):
                                        current_fg = tuple(current_fg.tolist())
                                        console.print(vx, vy, chr(current_char), fg=current_fg, bg=overlay_color)
    
    # Third pass: Render patrol routes if enabled
    if game.show_patrols:
        for enemy in game.enemies:
            if enemy.patrol_points and len(enemy.patrol_points) > 1:
                distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
                if distance_to_player <= vision_range:
                    for point in enemy.patrol_points:
                        px = point.x - camera_x
                        py = point.y - camera_y
                        if (0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT - PANEL_HEIGHT):
                            console.print(px, py, '*', fg=Colors.yellow)
    
    # Fourth pass: Render movement predictions if network scan is active
    if game.show_patrol_predictions:
        for enemy in game.enemies:
            distance_to_player = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance_to_player <= vision_range:
                predictions = enemy.get_predicted_moves(3)
                for i, pred_pos in enumerate(predictions):
                    px = pred_pos.x - camera_x
                    py = pred_pos.y - camera_y
                    if (0 <= px < SCREEN_WIDTH and 0 <= py < SCREEN_HEIGHT - PANEL_HEIGHT):
                        console.print(px, py, str(i + 1), fg=Colors.cyan, bg=Colors.black)
    
    # Fifth pass: Render gateway
    if game.game_map.gateway:
        gw_x = game.game_map.gateway.x - camera_x
        gw_y = game.game_map.gateway.y - camera_y
        if (0 <= gw_x < SCREEN_WIDTH and 0 <= gw_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(game.game_map.gateway.x - game.player.x), 
                          abs(game.game_map.gateway.y - game.player.y))
            if distance <= vision_range:
                console.print(gw_x, gw_y, '>', fg=Colors.gateway, bg=Colors.black)
    
    # Sixth pass: Render enemies
    for enemy in game.enemies:
        enemy_x = enemy.x - camera_x
        enemy_y = enemy.y - camera_y
        if (0 <= enemy_x < SCREEN_WIDTH and 0 <= enemy_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            distance = max(abs(enemy.x - game.player.x), abs(enemy.y - game.player.y))
            if distance <= vision_range:
                console.print(enemy_x, enemy_y, enemy.type_data.symbol, 
                                fg=enemy.get_color(), bg=Colors.black)
    
    # Seventh pass: Render player (with special effects)
    player_x = game.player.x - camera_x
    player_y = game.player.y - camera_y
    if (0 <= player_x < SCREEN_WIDTH and 0 <= player_y < SCREEN_HEIGHT - PANEL_HEIGHT):
        player_color = Colors.player
        if game.player.is_invisible():
            player_color = Colors.blue
        elif game.player.speed_boost_turns > 0:
            player_color = Colors.yellow
        
        console.print(player_x, player_y, '@', fg=player_color, bg=Colors.black)
    
    # Final pass: Render targeting cursor
    if game.targeting_mode:
        cursor_x = game.cursor_x - camera_x
        cursor_y = game.cursor_y - camera_y
        if (0 <= cursor_x < SCREEN_WIDTH and 0 <= cursor_y < SCREEN_HEIGHT - PANEL_HEIGHT):
            console.print(cursor_x, cursor_y, 'X', fg=Colors.red, bg=Colors.black)
            
            # Show range indicator for targeted exploit
            if game.targeting_exploit in EXPLOITS:
                exploit = EXPLOITS[game.targeting_exploit]
                for dx in range(-exploit.range, exploit.range + 1):
                    for dy in range(-exploit.range, exploit.range + 1):
                        if dx*dx + dy*dy <= exploit.range*exploit.range:
                            rx = game.player.x - camera_x + dx
                            ry = game.player.y - camera_y + dy
                            if (0 <= rx < SCREEN_WIDTH and 0 <= ry < SCREEN_HEIGHT - PANEL_HEIGHT):
                                current_char = console.ch[rx, ry]
                                current_fg = console.fg[rx, ry]
                                if current_char != ord(' '):
                                    # Convert numpy array to tuple
                                    if hasattr(current_fg, 'tolist'):
                                        current_fg = tuple(current_fg.tolist())
                                        console.print(rx, ry, chr(current_char), fg=current_fg, bg=(40, 40, 40))
def main():
    """Main game loop"""
    # Initialize tcod with fallback handling
    try:
        tileset = tcod.tileset.load_tilesheet(
            "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
        )
    except (FileNotFoundError, ImportError):
        try:
            tileset = tcod.tileset.load_tilesheet(
                tcod.tileset.get_default(), 16, 16, tcod.tileset.CHARMAP_TCOD
            )
        except:
            tileset = None
    
    context_args = {
        "columns": SCREEN_WIDTH,
        "rows": SCREEN_HEIGHT,
        "title": "Rogue Signal Protocol v49 - Fixed Hacker Stealth Dungeon Crawler",
        "vsync": True
    }
    
    if tileset:
        context_args["tileset"] = tileset
    
    with tcod.context.new(**context_args) as context:
        console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order='F')
        game = Game()
        
        game.add_message("Welcome to Rogue Signal Protocol v49 - ALL BUGS FIXED!")
        game.add_message("Navigate using stealth. Reach the gateway (>).")
        game.add_message("Hide in shadows (.) to avoid detection.")
        game.add_message("Enemy vision ranges now visible as colored backgrounds!")
        
        while True:
            console.clear()
            
            render_map(console, game)
            render_ui(console, game)
            
            # Instructions at top
            if game.targeting_mode:
                console.print(1, 0, "TARGETING MODE: WASD/Arrows: Move cursor | Enter: Confirm | ESC: Cancel", 
                             fg=Colors.yellow, bg=Colors.black)
            else:
                instructions = "WASD/Arrows: Move | Space: Wait | Tab: Patrols | 1-5: Exploits | ESC: Quit"
                if game.player.speed_boost_turns > 0:
                    instructions += " | SPEED BOOST ACTIVE!"
                console.print(1, 0, instructions, fg=Colors.ui_text, bg=Colors.black)
            
            # Game over check
            if game.game_over:
                console.print(SCREEN_WIDTH // 2 - 10, SCREEN_HEIGHT // 2, 
                             "MISSION COMPLETE!", fg=Colors.green, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 15, SCREEN_HEIGHT // 2 + 1, 
                             "All networks infiltrated successfully!", fg=Colors.green, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 + 3, 
                             "Press ESC to exit", fg=Colors.ui_text, bg=Colors.black)
            
            # CPU death check
            if game.player.cpu <= 0:
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2, 
                             "SYSTEM FAILURE", fg=Colors.red, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 12, SCREEN_HEIGHT // 2 + 1, 
                             "Your consciousness has been purged", fg=Colors.red, bg=Colors.black)
                console.print(SCREEN_WIDTH // 2 - 8, SCREEN_HEIGHT // 2 + 3, 
                             "Press ESC to exit", fg=Colors.ui_text, bg=Colors.black)
            
            context.present(console)
            
            # Handle input with UPPERCASE KeySym values
            for event in tcod.event.wait():
                if event.type == "QUIT":
                    raise SystemExit()
                elif event.type == "KEYDOWN":
                    if event.sym == tcod.event.KeySym.ESCAPE:
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
                        # Targeting mode controls - FIXED with proper uppercase KeySym
                        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.W):
                            game.move_cursor(0, -1)
                        elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.S):
                            game.move_cursor(0, 1)
                        elif event.sym in (tcod.event.KeySym.LEFT, tcod.event.KeySym.A):
                            game.move_cursor(-1, 0)
                        elif event.sym in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.D):
                            game.move_cursor(1, 0)
                        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
                            game.execute_exploit(game.targeting_exploit, game.cursor_x, game.cursor_y)
                    
                    else:
                        # Normal game controls - FIXED with proper uppercase KeySym
                        if event.sym in (tcod.event.KeySym.UP, tcod.event.KeySym.W):
                            game.move_player(0, -1)
                        elif event.sym in (tcod.event.KeySym.DOWN, tcod.event.KeySym.S):
                            game.move_player(0, 1)
                        elif event.sym in (tcod.event.KeySym.LEFT, tcod.event.KeySym.A):
                            game.move_player(-1, 0)
                        elif event.sym in (tcod.event.KeySym.RIGHT, tcod.event.KeySym.D):
                            game.move_player(1, 0)
                        elif event.sym == tcod.event.KeySym.SPACE:
                            game.process_turn()
                        elif event.sym == tcod.event.KeySym.TAB:
                            game.show_patrols = not game.show_patrols
                            game.add_message("Patrols " + ("visible" if game.show_patrols else "hidden"))
                        elif event.sym == tcod.event.KeySym.N1 and len(game.loaded_exploits) > 0:
                            game.use_exploit(game.loaded_exploits[0])
                        elif event.sym == tcod.event.KeySym.N2 and len(game.loaded_exploits) > 1:
                            game.use_exploit(game.loaded_exploits[1])
                        elif event.sym == tcod.event.KeySym.N3 and len(game.loaded_exploits) > 2:
                            game.use_exploit(game.loaded_exploits[2])
                        elif event.sym == tcod.event.KeySym.N4 and len(game.loaded_exploits) > 3:
                            game.use_exploit(game.loaded_exploits[3])
                        elif event.sym == tcod.event.KeySym.N5 and len(game.loaded_exploits) > 4:
                            game.use_exploit(game.loaded_exploits[4])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error running game: {e}")
        print("Make sure you have 'pip install tcod' and optionally download dejavu10x10_gs_tc.png")
        print("The game will use a fallback font if the PNG is missing.")
        import traceback
        traceback.print_exc()