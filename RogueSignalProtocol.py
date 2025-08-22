#!/usr/bin/env python3
"""
Rogue Signal Protocol v65 - Enhanced Combat & Inventory System
A stealth-focused traditional roguelike using Python and tcod

Refactored for better code organization and maintainability.
"""

import tcod
import logging
import random
import math
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Set
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

class GameConfig:
    """Central configuration for game constants."""
    # Screen dimensions
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    
    # Map dimensions
    MAP_WIDTH = 50
    MAP_HEIGHT = 50
    
    # UI layout
    LOG_WIDTH = 25
    GAME_AREA_WIDTH = SCREEN_WIDTH - LOG_WIDTH
    PANEL_HEIGHT = 5
    PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
    
    # Game balance - Remove level 0 (tutorial)
    ADMIN_SPAWN_THRESHOLDS = {1: 90, 2: 75, 3: 60}
    NETWORK_CONFIGS = {
        1: {"enemies": 8, "shadow_coverage": 0.4, "name": "Corporate Network"},
        2: {"enemies": 12, "shadow_coverage": 0.25, "name": "Government System"},
        3: {"enemies": 16, "shadow_coverage": 0.15, "name": "Military Backbone"}
    }

class Colors:
    """Color definitions for the game."""
    # Basic colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 136, 0)
    
    # Game-specific colors
    FLOOR = (0, 50, 0)
    WALL = (200, 200, 200)
    SHADOW = (0, 20, 0)
    PLAYER = (0, 255, 255)
    GATEWAY = (255, 255, 0)
    
    # Enemy colors by state
    ENEMY_UNAWARE = (255, 136, 0)
    ENEMY_ALERT = (255, 255, 0)
    ENEMY_HOSTILE = (255, 0, 0)
    
    # Vision overlays
    VISION_UNAWARE = (40, 20, 0)
    VISION_ALERT = (40, 40, 0)
    VISION_HOSTILE = (40, 0, 0)
    
    # UI colors
    UI_BG = (0, 20, 0)
    UI_TEXT = (0, 255, 0)
    LOG_BG = (0, 15, 0)
    LOG_BORDER = (0, 100, 0)

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class EnemyState(Enum):
    """Enemy awareness states."""
    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"

class EnemyMovement(Enum):
    """Enemy movement patterns."""
    STATIC = "static"
    LINEAR = "linear"
    RANDOM = "random"
    SEEK = "seek"
    TRACK = "track"

class TargetingMode(Enum):
    """Exploit targeting modes."""
    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"

@dataclass
class Position:
    """2D position with x, y coordinates."""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> int:
        """Calculate Chebyshev distance to another position."""
        return max(abs(self.x - other.x), abs(self.y - other.y))
    
    def is_valid(self, width: int, height: int) -> bool:
        """Check if position is within bounds."""
        return 0 <= self.x < width and 0 <= self.y < height

@dataclass
class EnemyTypeDefinition:
    """Definition of an enemy type with all its properties."""
    symbol: str
    cpu: int
    vision: int
    movement: EnemyMovement
    name: str
    damage: int

@dataclass
class ExploitDefinition:
    """Definition of an exploit with its properties."""
    name: str
    ram: int
    heat: int
    range: int
    exploit_type: str
    targeting: TargetingMode = TargetingMode.NONE
    description: str = ""

# ============================================================================
# GAME DATA DEFINITIONS
# ============================================================================

class GameData:
    """Static game data definitions."""
    
    ENEMY_TYPES = {
        'scanner': EnemyTypeDefinition('s', 20, 2, EnemyMovement.STATIC, "Scanner", 10),
        'patrol': EnemyTypeDefinition('p', 25, 3, EnemyMovement.LINEAR, "Patrol", 15),
        'bot': EnemyTypeDefinition('b', 15, 2, EnemyMovement.RANDOM, "Bot", 8),
        'firewall': EnemyTypeDefinition('F', 40, 1, EnemyMovement.STATIC, "Firewall", 20),
        'hunter': EnemyTypeDefinition('H', 35, 5, EnemyMovement.SEEK, "Hunter", 25),
        'admin': EnemyTypeDefinition('A', 100, 6, EnemyMovement.TRACK, "Admin Avatar", 40)
    }
    
    EXPLOITS = {
        'shadow_step': ExploitDefinition("Shadow Step", 2, 20, 8, "stealth", TargetingMode.SINGLE,
                                       "Teleport between shadow zones"),
        'data_mimic': ExploitDefinition("Data Mimic", 1, 15, 0, "stealth", TargetingMode.NONE,
                                      "Appear as harmless data for 5 turns"),
        'noise_maker': ExploitDefinition("Noise Maker", 1, 10, 6, "stealth", TargetingMode.SINGLE,
                                       "Create distraction at target location"),
        'buffer_overflow': ExploitDefinition("Buffer Overflow", 2, 25, 1, "combat", TargetingMode.SINGLE,
                                           "High melee damage, armor piercing"),
        'code_injection': ExploitDefinition("Code Injection", 1, 15, 4, "combat", TargetingMode.SINGLE,
                                          "Ranged attack, bypasses firewalls"),
        'system_crash': ExploitDefinition("System Crash", 3, 35, 3, "combat", TargetingMode.AREA,
                                        "Area damage, disables multiple enemies"),
        'network_scan': ExploitDefinition("Network Scan", 1, 10, 8, "utility", TargetingMode.NONE,
                                        "Reveals enemy positions and patrol routes"),
        'log_wiper': ExploitDefinition("Log Wiper", 1, 5, 0, "utility", TargetingMode.NONE,
                                     "Reduces detection level significantly"),
        'emp_burst': ExploitDefinition("EMP Burst", 3, 40, 2, "emergency", TargetingMode.AREA,
                                     "Disables all nearby enemies temporarily")
    }

# ============================================================================
# INVENTORY SYSTEM
# ============================================================================

class InventoryItem(ABC):
    """Base class for all inventory items."""
    
    def __init__(self, name: str, item_type: str, description: str = ""):
        self.name = name
        self.item_type = item_type
        self.description = description
    
    @abstractmethod
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Use the item. Returns True if successful."""
        pass

class DataPatch(InventoryItem):
    """Randomized data patches with unknown effects until used."""
    
    def __init__(self, color: str, effect: str, name: str, description: str = ""):
        super().__init__(name, "data_patch", description)
        self.color = color
        self.effect = effect
        self.discovered = False
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Apply the data patch effect to the player."""
        if self.color not in game.data_patch_effects:
            return False
        
        effect_key, description = game.data_patch_effects[self.color]
        
        if not self.discovered:
            self.discovered = True
            game.message_log.add_message(f"Used {self.name}: {description}")
        else:
            game.message_log.add_message(f"Used {self.name}")
        
        return self._apply_effect(effect_key, player, game)
    
    def _apply_effect(self, effect_key: str, player: 'Player', game: 'Game') -> bool:
        """Apply the specific effect."""
        if effect_key == 'restore_cpu':
            restore = random.randint(30, 40)
            actual = min(restore, player.max_cpu - player.cpu)
            player.cpu += actual
            game.message_log.add_message(f"CPU restored: +{actual}")
        
        elif effect_key == 'reduce_heat':
            old_heat = player.heat
            player.heat = max(0, player.heat - 40)
            actual_reduction = old_heat - player.heat
            game.message_log.add_message(f"Heat reduced: -{actual_reduction}°C")
        
        elif effect_key == 'reduce_detection':
            old_detection = player.detection
            player.detection = max(0, player.detection - 25)
            actual_reduction = old_detection - player.detection
            game.message_log.add_message(f"Detection: -{actual_reduction:.1f}%")
        
        elif effect_key == 'speed_boost':
            player.speed_boost_turns = 10
            game.message_log.add_message("Speed boost active (10 turns)")
        
        elif effect_key == 'enhanced_vision':
            player.enhanced_vision_turns = 15
            game.message_log.add_message("Enhanced vision active (15 turns)")
        
        elif effect_key == 'exploit_efficiency':
            player.exploit_efficiency_turns = 8
            game.message_log.add_message("Exploit efficiency active (8 turns)")
        
        return True

class ExploitItem(InventoryItem):
    """Exploit items that can be equipped."""
    
    def __init__(self, exploit_key: str, exploit_def: ExploitDefinition):
        super().__init__(exploit_def.name, "exploit", exploit_def.description)
        self.exploit_key = exploit_key
        self.ram_cost = exploit_def.ram
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Equip the exploit."""
        return player.inventory_manager.equip_exploit(self)

# ============================================================================
# PLAYER INVENTORY MANAGEMENT
# ============================================================================

class InventoryManager:
    """Manages player inventory and equipped items."""
    
    def __init__(self, player: 'Player'):
        self.player = player
        self.items: List[InventoryItem] = []
        self.equipped_exploits: List[str] = ['shadow_step', 'network_scan', 'code_injection']
        self.max_equipped_exploits = 5
    
    def add_item(self, item: InventoryItem) -> bool:
        """Add an item to inventory."""
        self.items.append(item)
        return True
    
    def remove_item(self, item: InventoryItem) -> bool:
        """Remove an item from inventory."""
        if item in self.items:
            self.items.remove(item)
            return True
        return False
    
    def get_items_by_type(self, item_type: str) -> List[InventoryItem]:
        """Get all items of a specific type."""
        return [item for item in self.items if item.item_type == item_type]
    
    def equip_exploit(self, exploit_item: ExploitItem) -> bool:
        """Equip an exploit from inventory."""
        if exploit_item.exploit_key not in self.equipped_exploits:
            if len(self.equipped_exploits) < self.max_equipped_exploits:
                self.equipped_exploits.append(exploit_item.exploit_key)
                self.remove_item(exploit_item)
                self.player.calculate_ram_usage()
                return True
        return False
    
    def unequip_exploit(self, exploit_key: str) -> bool:
        """Unequip an exploit."""
        if exploit_key in self.equipped_exploits:
            self.equipped_exploits.remove(exploit_key)
            self.player.calculate_ram_usage()
            return True
        return False
    
    def can_use_exploit(self, exploit_key: str) -> bool:
        """Check if player can use the specified exploit."""
        return exploit_key in self.equipped_exploits and exploit_key in GameData.EXPLOITS
    
    def get_ram_usage(self) -> int:
        """Calculate total RAM usage from equipped exploits."""
        total_ram = 0
        for exploit_key in self.equipped_exploits:
            if exploit_key in GameData.EXPLOITS:
                total_ram += GameData.EXPLOITS[exploit_key].ram
        return total_ram

# ============================================================================
# PLAYER CLASS
# ============================================================================

class Player:
    """Player character with stats, position, and abilities."""
    
    def __init__(self, x: int, y: int):
        # Position and movement
        self.position = Position(x, y)
        self.last_position = Position(x, y)
        
        # Core stats
        self.cpu = 100
        self.max_cpu = 100
        self.heat = 0
        self.detection = 0
        self.ram_total = 8
        
        # Vision and abilities
        self.base_vision_range = 15
        
        # Temporary effects
        self.temporary_effects = {
            'data_mimic_turns': 0,
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0
        }
        
        # Inventory system
        self.inventory_manager = InventoryManager(self)
    
    @property
    def x(self) -> int:
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    @property
    def ram_used(self) -> int:
        return self.inventory_manager.get_ram_usage()
    
    def move(self, dx: int, dy: int, game_map: 'GameMap') -> bool:
        """Move player with boundary and collision checking."""
        self.last_position = Position(self.x, self.y)
        new_position = Position(
            max(0, min(GameConfig.MAP_WIDTH - 1, self.x + dx)),
            max(0, min(GameConfig.MAP_HEIGHT - 1, self.y + dy))
        )
        
        if game_map.is_valid_position(new_position):
            self.position = new_position
            return True
        return False
    
    def update_effects(self):
        """Update temporary effects each turn."""
        for effect in self.temporary_effects:
            self.temporary_effects[effect] = max(0, self.temporary_effects[effect] - 1)
    
    def is_invisible(self) -> bool:
        """Check if player is effectively invisible."""
        return self.temporary_effects['data_mimic_turns'] > 0
    
    def get_vision_range(self) -> int:
        """Get current vision range including bonuses."""
        base_range = self.base_vision_range
        if self.temporary_effects['enhanced_vision_turns'] > 0:
            base_range += 5
        return base_range
    
    def can_see_through_walls(self) -> bool:
        """Check if player can see through walls."""
        return self.temporary_effects['enhanced_vision_turns'] > 0
    
    def calculate_ram_usage(self):
        """Update RAM usage calculation."""
        # This is now handled by InventoryManager
        pass
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.cpu)
        self.cpu -= actual_damage
        return actual_damage

# ============================================================================
# ENEMY SYSTEM
# ============================================================================

class Enemy:
    """Enemy character with AI behavior."""
    
    def __init__(self, position: Position, enemy_type: str):
        self.position = position
        self.type = enemy_type
        self.type_data = GameData.ENEMY_TYPES[enemy_type]
        
        # Stats
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu
        
        # AI state
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0
        
        # Movement data
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Position] = None
    
    @property
    def x(self) -> int:
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get the color for rendering this enemy."""
        if self.disabled_turns > 0:
            return Colors.BLUE
        elif self.state == EnemyState.UNAWARE:
            return Colors.ENEMY_UNAWARE
        elif self.state == EnemyState.ALERT:
            return Colors.ENEMY_ALERT
        else:
            return Colors.ENEMY_HOSTILE
    
    def can_see_player(self, player: Player, game_map: 'GameMap') -> bool:
        """Check if enemy can see player."""
        if self.disabled_turns > 0:
            return False
        
        distance = self.position.distance_to(player.position)
        if distance > self.type_data.vision:
            return False
        
        if player.is_invisible():
            return False
        
        if game_map.is_shadow(player.position):
            return False
        
        return game_map.has_line_of_sight(self.position, player.position)
    
    def can_attack_player(self, player: Player) -> bool:
        """Check if enemy can attack player (adjacent)."""
        distance = self.position.distance_to(player.position)
        return distance <= 1 and self.disabled_turns == 0
    
    def attack_player(self, player: Player) -> int:
        """Attack the player and return damage dealt."""
        return player.take_damage(self.type_data.damage)
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        self.cpu -= damage
        return self.cpu <= 0
    
    def move(self, game_map: 'GameMap', player: Player):
        """Move enemy based on its AI behavior."""
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return
        
        # Movement cooldown system
        self.move_cooldown -= 1
        if self.move_cooldown > 0:
            return
        
        self._reset_movement_cooldown()
        
        if self.type_data.movement == EnemyMovement.STATIC:
            return
        elif self.type_data.movement == EnemyMovement.RANDOM:
            self._move_random(game_map, player)
        elif self.type_data.movement == EnemyMovement.LINEAR and self.patrol_points:
            self._move_patrol(game_map, player)
        elif self.type_data.movement == EnemyMovement.SEEK:
            if self.state == EnemyState.HOSTILE and self.last_seen_player:
                self._move_toward(self.last_seen_player, game_map, player)
        elif self.type_data.movement == EnemyMovement.TRACK:
            if self.state == EnemyState.HOSTILE:
                self._move_toward(player.position, game_map, player)
    
    def _reset_movement_cooldown(self):
        """Reset movement cooldown based on enemy type."""
        if self.type_data.movement == EnemyMovement.LINEAR:
            self.move_cooldown = 1
        else:
            self.move_cooldown = 2
    
    def _move_random(self, game_map: 'GameMap', player: Player):
        """Execute random movement pattern."""
        if self.state == EnemyState.HOSTILE:
            self._move_toward(player.position, game_map, player)
            return
        
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            new_position = Position(self.x + dx, self.y + dy)
            if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                game_map.is_valid_position(new_position) and
                not new_position.distance_to(player.position) == 0):
                self.position = new_position
                break
    
    def _move_patrol(self, game_map: 'GameMap', player: Player):
        """Execute patrol movement pattern."""
        if self.state == EnemyState.HOSTILE:
            self._move_toward(player.position, game_map, player)
            return
        
        if not self.patrol_points:
            return
        
        target = self.patrol_points[self.patrol_index]
        
        if self.position.distance_to(target) <= 1:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.patrol_index]
        
        self._move_toward(target, game_map, player)
    
    def _move_toward(self, target: Position, game_map: 'GameMap', player: Player):
        """Move one step toward target position."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            return
        
        dx = 0 if self.x == target.x else (1 if target.x > self.x else -1)
        dy = 0 if self.y == target.y else (1 if target.y > self.y else -1)
        
        # Try different movement directions in order of preference
        move_attempts = [
            (dx, dy), (dx, 0), (0, dy), (dx, -dy), (-dx, dy),
            (-dx, 0), (0, -dy), (-dx, -dy)
        ]
        
        for try_dx, try_dy in move_attempts:
            if try_dx == 0 and try_dy == 0:
                continue
            
            new_position = Position(self.x + try_dx, self.y + try_dy)
            if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                game_map.is_valid_position(new_position) and
                not new_position.distance_to(player.position) == 0):
                self.position = new_position
                break

# ============================================================================
# GAME MAP
# ============================================================================

class GameMap:
    """Game world map with terrain and features."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Terrain sets
        self.walls: Set[Tuple[int, int]] = set()
        self.shadows: Set[Tuple[int, int]] = set()
        
        # Feature sets
        self.cooling_nodes: Set[Tuple[int, int]] = set()
        self.cpu_recovery_nodes: Set[Tuple[int, int]] = set()
        
        # Items
        self.data_patches: Dict[Tuple[int, int], DataPatch] = {}
        
        # Special locations
        self.gateway: Optional[Position] = None
    
    def is_wall(self, position: Position) -> bool:
        """Check if position contains a wall."""
        if not position.is_valid(self.width, self.height):
            return True
        return (position.x, position.y) in self.walls
    
    def is_shadow(self, position: Position) -> bool:
        """Check if position is in shadow."""
        if not position.is_valid(self.width, self.height):
            return False
        return (position.x, position.y) in self.shadows
    
    def is_cooling_node(self, position: Position) -> bool:
        """Check if position contains a cooling node."""
        return (position.x, position.y) in self.cooling_nodes
    
    def is_cpu_recovery_node(self, position: Position) -> bool:
        """Check if position contains a CPU recovery node."""
        return (position.x, position.y) in self.cpu_recovery_nodes
    
    def get_data_patch(self, position: Position) -> Optional[DataPatch]:
        """Get data patch at position."""
        return self.data_patches.get((position.x, position.y))
    
    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid for movement."""
        return (position.is_valid(self.width, self.height) and 
                not self.is_wall(position))
    
    def has_line_of_sight(self, start: Position, end: Position) -> bool:
        """Check line of sight between two positions using Bresenham's algorithm."""
        if not (start.is_valid(self.width, self.height) and 
                end.is_valid(self.width, self.height)):
            return False
        
        dx = abs(end.x - start.x)
        dy = abs(end.y - start.y)
        sx = 1 if start.x < end.x else -1
        sy = 1 if start.y < end.y else -1
        err = dx - dy
        
        x, y = start.x, start.y
        
        while True:
            if x == end.x and y == end.y:
                return True
            if self.is_wall(Position(x, y)):
                return False
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

# ============================================================================
# MESSAGE LOG SYSTEM
# ============================================================================

class MessageLog:
    """Manages game messages and logging."""
    
    def __init__(self, max_messages: int = 100):
        self.messages: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_messages = max_messages
    
    def add_message(self, text: str, color: Optional[Tuple[int, int, int]] = None):
        """Add a message to the log."""
        if not text:
            return
        
        if color is None:
            color = self._determine_message_color(text)
        
        self.messages.append((text, color))
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def _determine_message_color(self, text: str) -> Tuple[int, int, int]:
        """Determine appropriate color for message based on content."""
        text_lower = text.lower()
        text_upper = text.upper()
        
        if ("ADMIN" in text_upper or "CRITICAL" in text_upper or 
            "eliminated" in text_lower):
            return Colors.RED
        elif ("detected" in text_lower or "investigating" in text_lower or 
              "attracted" in text_lower or "attacks" in text_lower):
            return Colors.YELLOW
        elif ("activated" in text_lower or "restored" in text_lower or 
              "reduced" in text_lower or "active" in text_lower):
            return Colors.CYAN
        else:
            return Colors.GREEN
    
    def get_recent_messages(self, count: int) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages

# ============================================================================
# GAME STATE AND MAIN GAME CLASS
# ============================================================================

class Game:
    """Main game class that manages all game state and logic."""
    
    def __init__(self):
        # Core game objects
        self.player = Player(5, 5)
        self.enemies: List[Enemy] = []
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.message_log = MessageLog()
        
        # Game state - Start at level 1 instead of 0
        self.level = 1
        self.turn = 0
        self.game_over = False
        self.admin_spawned = False
        
        # UI state
        self.show_patrols = False
        self.show_patrol_predictions = False
        self.show_inventory = False
        self.show_help = False
        self.inventory_selection = 0
        
        # Targeting system
        self.targeting_mode = False
        self.targeting_exploit: Optional[str] = None
        self.cursor_position = Position(0, 0)
        
        # Game effects
        self.network_scan_turns = 0
        self.noise_locations: List[Position] = []
        self.distraction_points: Dict[Position, int] = {}
        
        # Data patch system
        self.data_patch_effects: Dict[str, Tuple[str, str]] = {}
        self._randomize_data_patches()
        
        # Initialize - Start with first procedural level
        self.dungeon_seed = random.randint(1, 1000000)
        self._generate_procedural_level()
    
    def _randomize_data_patches(self):
        """Randomize data patch effects for this game session."""
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
    
   
    def _clear_map(self):
        """Clear all map data."""
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.data_patches.clear()
        self.enemies.clear()
    
    def _create_border_walls(self):
        """Create walls around the map border."""
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))
        for y in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))
        
    def _reset_player_state(self, x: int, y: int):
        """Reset player to starting state."""
        self.player.position = Position(x, y)
        self.player.cpu = self.player.max_cpu
        self.player.heat = 0
        self.player.detection = 0
        
        # Clear temporary effects
        for effect in self.player.temporary_effects:
            self.player.temporary_effects[effect] = 0
    
    def process_turn(self):
        """Process one complete game turn."""
        self.turn += 1
        
        # Update player effects
        self.player.update_effects()
        
        # Cool down heat
        heat_reduction = 3 if self.player.temporary_effects['exploit_efficiency_turns'] > 0 else 2
        self.player.heat = max(0, self.player.heat - heat_reduction)
        
        # Handle network scan effect
        self._update_network_scan()
        
        # Process special tiles
        self._process_special_tiles()
        
        # Update enemies
        self._update_enemies()
        
        # Check for admin spawn
        self._check_admin_spawn()
        
        # Passive detection increase
        if self.turn % 15 == 0:
            self.player.detection = min(100, self.player.detection + 1)
    
    def _update_network_scan(self):
        """Update network scan effect."""
        if self.network_scan_turns > 0:
            self.network_scan_turns -= 1
            if self.network_scan_turns == 0:
                self.show_patrols = False
                self.message_log.add_message("Network scan expired.")
    
    def _process_special_tiles(self):
        """Process effects of special tiles at player position."""
        player_pos = (self.player.x, self.player.y)
        
        # Cooling node
        if self.game_map.is_cooling_node(self.player.position):
            old_heat = self.player.heat
            self.player.heat = max(0, self.player.heat - 20)
            if old_heat > self.player.heat:
                self.message_log.add_message(f"Cooling node: -{old_heat - self.player.heat}°C")
        
        # CPU recovery node
        if self.game_map.is_cpu_recovery_node(self.player.position):
            recovery = min(20, self.player.max_cpu - self.player.cpu)
            self.player.cpu += recovery
            if recovery > 0:
                self.message_log.add_message(f"CPU recovery: +{recovery}")
        
        # Data patch
        if player_pos in self.game_map.data_patches:
            patch = self.game_map.data_patches[player_pos]
            self.player.inventory_manager.add_item(patch)
            self.message_log.add_message(f"Found {patch.name}")
            del self.game_map.data_patches[player_pos]
    
    def _update_enemies(self):
        """Update all enemy states and actions."""
        self._update_enemy_awareness()
        self._move_enemies()
        self._process_enemy_attacks()
    
    def _update_enemy_awareness(self):
        """Update enemy awareness states."""
        for enemy in self.enemies[:]:
            old_state = enemy.state
            
            if enemy.can_see_player(self.player, self.game_map):
                self._handle_enemy_sees_player(enemy)
            else:
                self._handle_enemy_loses_player(enemy)
    
    def _handle_enemy_sees_player(self, enemy: Enemy):
        """Handle when enemy sees the player."""
        if enemy.state == EnemyState.UNAWARE:
            enemy.state = EnemyState.ALERT
            enemy.alert_timer = 3
            self.message_log.add_message(f"{enemy.type_data.name} investigating")
        elif enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(self.player.x, self.player.y)
                detection_increase = 15 if enemy.type == 'admin' else 10
                self.player.detection = min(100, self.player.detection + detection_increase)
                self.message_log.add_message(f"{enemy.type_data.name} detected you!")
        elif enemy.state == EnemyState.HOSTILE:
            enemy.last_seen_player = Position(self.player.x, self.player.y)
            detection_increase = 3 if enemy.type == 'admin' else 1
            self.player.detection = min(100, self.player.detection + detection_increase)
    
    def _handle_enemy_loses_player(self, enemy: Enemy):
        """Handle when enemy loses sight of player."""
        if enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.UNAWARE
                self.message_log.add_message(f"{enemy.type_data.name} lost interest")
        elif enemy.state == EnemyState.HOSTILE:
            if random.random() < 0.15:  # 15% chance per turn
                if enemy.type == 'admin':
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 5
                else:
                    enemy.state = EnemyState.UNAWARE
                    enemy.last_seen_player = None
                    self.message_log.add_message(f"{enemy.type_data.name} lost track")
    
    def _move_enemies(self):
        """Move all enemies according to their AI."""
        for enemy in self.enemies:
            enemy.move(self.game_map, self.player)
    
    def _process_enemy_attacks(self):
        """Process attacks from enemies adjacent to player."""
        for enemy in self.enemies[:]:
            if enemy.can_attack_player(self.player):
                damage = enemy.attack_player(self.player)
                self.message_log.add_message(f"{enemy.type_data.name} attacks: -{damage} CPU")
                if self.player.cpu <= 0:
                    self.message_log.add_message("CRITICAL SYSTEM FAILURE!")
    
    def _check_admin_spawn(self):
        """Check if admin avatar should spawn."""
        spawn_threshold = GameConfig.ADMIN_SPAWN_THRESHOLDS.get(self.level, 50)
        if (self.player.detection >= spawn_threshold and 
            not self.admin_spawned and 
            not any(e.type == 'admin' for e in self.enemies)):
            self._spawn_admin_avatar()
    
    def _spawn_admin_avatar(self):
        """Spawn the admin avatar enemy."""
        if self.admin_spawned:
            return
        
        spawn_position = self._find_admin_spawn_position()
        if spawn_position:
            admin = Enemy(spawn_position, 'admin')
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.player.x, self.player.y)
            self.enemies.append(admin)
            self.admin_spawned = True
            self.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
    
    def _find_admin_spawn_position(self) -> Optional[Position]:
        """Find a suitable spawn position for admin avatar."""
        for _ in range(50):
            x = random.randint(5, GameConfig.MAP_WIDTH - 5)
            y = random.randint(5, GameConfig.MAP_HEIGHT - 5)
            position = Position(x, y)
            
            if (self.game_map.is_valid_position(position) and
                position.distance_to(self.player.position) > 15 and
                not self._get_enemy_at(position) and
                (x, y) not in self.game_map.data_patches and
                (x, y) not in self.game_map.cooling_nodes and
                (x, y) not in self.game_map.cpu_recovery_nodes):
                return position
        
        # Fallback position
        fallback = Position(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10)
        if self.game_map.is_valid_position(fallback):
            return fallback
        return Position(40, 40)
    
    def move_player(self, dx: int, dy: int):
        """Move player and process the resulting turn."""
        if self.targeting_mode:
            self._move_cursor(dx, dy)
            return
        
        moves = 2 if self.player.temporary_effects['speed_boost_turns'] > 0 else 1
        
        for move_count in range(moves):
            old_position = Position(self.player.x, self.player.y)
            
            if self.player.move(dx, dy, self.game_map):
                # Check for gateway
                if (self.game_map.gateway and 
                    self.player.position.distance_to(self.game_map.gateway) == 0):
                    self.message_log.add_message("Gateway reached! Next network...")
                    self.next_level()
                    return
                
                # Check for enemy collision
                if self._get_enemy_at(self.player.position):
                    self.player.position = old_position
                    self.message_log.add_message("Path blocked by enemy")
                    break
                
                # Check for overheating
                if self.player.heat >= 100:
                    damage = 5 + (self.player.heat - 100)
                    self.player.take_damage(damage)
                    self.player.heat = 95
                    self.message_log.add_message(f"Overheating! -{damage} CPU")
                    if self.player.cpu <= 0:
                        self.message_log.add_message("CRITICAL SYSTEM FAILURE!")
                        return
            else:
                new_pos = Position(self.player.x + dx, self.player.y + dy)
                if not self.game_map.is_valid_position(new_pos):
                    self.message_log.add_message("Wall blocks movement")
                break
        
        self.process_turn()
    
    def _move_cursor(self, dx: int, dy: int):
        """Move targeting cursor."""
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.cursor_position.y + dy))
        self.cursor_position = Position(new_x, new_y)
    
    def _get_enemy_at(self, position: Position) -> Optional[Enemy]:
        """Get enemy at specified position."""
        for enemy in self.enemies:
            if enemy.position.distance_to(position) == 0:
                return enemy
        return None
    
    def next_level(self):
        """Progress to the next level."""
        self.level += 1
        if self.level > 3:
            self.message_log.add_message("INFILTRATION COMPLETE!")
            self.message_log.add_message(f"Stats: Turns:{self.turn} Det:{int(self.player.detection)}%")
            self.game_over = True
        else:
            try:
                self._generate_procedural_level()
            except Exception as e:
                self.message_log.add_message(f"Network error: {str(e)[:15]}")
                self.level -= 1

    def _generate_procedural_level(self):
        """Generate a procedural level based on current level."""
        if self.level not in GameConfig.NETWORK_CONFIGS:
            self.message_log.add_message(f"Invalid level: {self.level}")
            return
        
        config = GameConfig.NETWORK_CONFIGS[self.level]
        
        # Set deterministic seed for this level
        level_seed = self.dungeon_seed + self.level * 12345
        random.seed(level_seed)
        
        try:
            self._clear_map()
            self._create_border_walls()
            
            # Generate level content
            rooms = self._generate_rooms()
            self._connect_rooms(rooms)
            self._generate_shadows(config["shadow_coverage"])
            self._place_special_nodes()
            self._place_data_patches()
            self._place_enemies(config["enemies"])
            self._place_gateway(rooms)
            
            # Reset player state
            self._reset_player_state(5, 5)
            self.player.detection = max(0, self.player.detection - 20)
            self.player.heat = max(0, self.player.heat - 30)
            
            self.message_log.add_message(f"{config['name']} loaded")
            self.message_log.add_message(f"{len(self.enemies)} security processes")
            
        finally:
            # Restore random seed
            random.seed()
        
        self.admin_spawned = False
    
    def _generate_rooms(self) -> List[Tuple[int, int, int, int]]:
        """Generate rooms for the level."""
        rooms = []
        max_rooms = 6 + self.level * 2
        attempts = 0
        
        while len(rooms) < max_rooms and attempts < 200:
            attempts += 1
            room_w = random.randint(4, 10)
            room_h = random.randint(4, 10)
            room_x = random.randint(3, GameConfig.MAP_WIDTH - room_w - 3)
            room_y = random.randint(3, GameConfig.MAP_HEIGHT - room_h - 3)
            
            # Check for overlap and spawn area
            if self._is_room_valid(room_x, room_y, room_w, room_h, rooms):
                self._create_room(room_x, room_y, room_w, room_h)
                rooms.append((room_x, room_y, room_w, room_h))
        
        return rooms
    
    def _is_room_valid(self, x: int, y: int, w: int, h: int, 
                      existing_rooms: List[Tuple[int, int, int, int]]) -> bool:
        """Check if room placement is valid."""
        # Check overlap with existing rooms
        for rx, ry, rw, rh in existing_rooms:
            if (x < rx + rw + 2 and x + w + 2 > rx and
                y < ry + rh + 2 and y + h + 2 > ry):
                return False
        
        # Keep spawn area clear
        if x < 10 and y < 10:
            return False
        
        return True
    
    def _create_room(self, x: int, y: int, width: int, height: int):
        """Create a rectangular room."""
        for i in range(width):
            wall_x = x + i
            if 0 <= wall_x < GameConfig.MAP_WIDTH:
                if 0 <= y < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, y))
                if 0 <= y + height - 1 < GameConfig.MAP_HEIGHT:
                    self.game_map.walls.add((wall_x, y + height - 1))
        
        for i in range(height):
            wall_y = y + i
            if 0 <= wall_y < GameConfig.MAP_HEIGHT:
                if 0 <= x < GameConfig.MAP_WIDTH:
                    self.game_map.walls.add((x, wall_y))
                if 0 <= x + width - 1 < GameConfig.MAP_WIDTH:
                    self.game_map.walls.add((x + width - 1, wall_y))
    
    def _connect_rooms(self, rooms: List[Tuple[int, int, int, int]]):
        """Connect rooms with corridors."""
        for i in range(len(rooms) - 1):
            x1 = rooms[i][0] + rooms[i][2] // 2
            y1 = rooms[i][1] + rooms[i][3] // 2
            x2 = rooms[i + 1][0] + rooms[i + 1][2] // 2
            y2 = rooms[i + 1][1] + rooms[i + 1][3] // 2
            
            # Create L-shaped corridor
            self._create_corridor(x1, y1, x2, y1)
            self._create_corridor(x2, y1, x2, y2)
    
    def _create_corridor(self, x1: int, y1: int, x2: int, y2: int):
        """Create a corridor between two points."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < GameConfig.MAP_WIDTH and 0 <= y1 < GameConfig.MAP_HEIGHT:
                self.game_map.walls.discard((x, y1))
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x2 < GameConfig.MAP_WIDTH and 0 <= y < GameConfig.MAP_HEIGHT:
                self.game_map.walls.discard((x2, y))
    
    def _generate_shadows(self, coverage: float):
        """Generate shadow areas."""
        shadow_clusters = random.randint(5, 10)
        
        for _ in range(shadow_clusters):
            center_x = random.randint(5, GameConfig.MAP_WIDTH - 6)
            center_y = random.randint(5, GameConfig.MAP_HEIGHT - 6)
            cluster_size = random.randint(8, 20)
            
            for _ in range(cluster_size):
                x = center_x + random.randint(-3, 3)
                y = center_y + random.randint(-3, 3)
                position = Position(x, y)
                if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                    not self.game_map.is_wall(position)):
                    self.game_map.shadows.add((x, y))
    
    def _place_special_nodes(self):
        """Place cooling and CPU recovery nodes."""
        node_count = 4 + self.level
        placed_nodes = 0
        attempts = 0
        
        while placed_nodes < node_count and attempts < 100:
            attempts += 1
            x = random.randint(5, GameConfig.MAP_WIDTH - 5)
            y = random.randint(5, GameConfig.MAP_HEIGHT - 5)
            position = Position(x, y)
            
            if self._is_valid_special_placement(position):
                if random.choice([True, False]):
                    self.game_map.cooling_nodes.add((x, y))
                else:
                    self.game_map.cpu_recovery_nodes.add((x, y))
                placed_nodes += 1
    
    def _place_data_patches(self):
        """Place data patches throughout the level."""
        patch_count = 6 + self.level * 2
        placed_patches = 0
        attempts = 0
        
        while placed_patches < patch_count and attempts < 150:
            attempts += 1
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)
            
            if self._is_valid_patch_placement(position):
                color = random.choice(list(self.data_patch_effects.keys()))
                effect, desc = self.data_patch_effects[color]
                patch = DataPatch(color, effect, f"{color.title()} Data Patch", desc)
                self.game_map.data_patches[(x, y)] = patch
                placed_patches += 1
    
    def _place_enemies(self, enemy_count: int):
        """Place enemies throughout the level."""
        enemy_types = ['scanner', 'patrol', 'bot', 'firewall', 'hunter']
        enemy_weights = [3, 2, 3, 1, 1]
        placed_enemies = 0
        attempts = 0
        
        while placed_enemies < enemy_count and attempts < enemy_count * 20:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)
            
            if self._is_valid_enemy_placement(position):
                enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
                enemy = Enemy(position, enemy_type)
                
                if enemy_type == 'patrol':
                    enemy.patrol_points = self._generate_patrol_route(position)
                
                self.enemies.append(enemy)
                placed_enemies += 1
    
    def _place_gateway(self, rooms: List[Tuple[int, int, int, int]]):
        """Place the level gateway."""
        # Try to place in a room first
        for room_x, room_y, room_w, room_h in rooms:
            x = room_x + room_w // 2
            y = room_y + room_h // 2
            position = Position(x, y)
            
            if self._is_valid_gateway_placement(position):
                self.game_map.gateway = position
                return
        
        # Fallback placement
        for x in range(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_WIDTH - 5):
            for y in range(GameConfig.MAP_HEIGHT - 10, GameConfig.MAP_HEIGHT - 5):
                position = Position(x, y)
                if self.game_map.is_valid_position(position):
                    self.game_map.gateway = position
                    return
    
    def _is_valid_special_placement(self, position: Position) -> bool:
        """Check if position is valid for special node placement."""
        return (not self.game_map.is_wall(position) and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                position.distance_to(Position(5, 5)) > 8)
    
    def _is_valid_patch_placement(self, position: Position) -> bool:
        """Check if position is valid for data patch placement."""
        return (not self.game_map.is_wall(position) and
                (position.x, position.y) not in self.game_map.data_patches and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                position.distance_to(Position(5, 5)) > 5)
    
    def _is_valid_enemy_placement(self, position: Position) -> bool:
        """Check if position is valid for enemy placement."""
        return (self.game_map.is_valid_position(position) and
                position.distance_to(Position(5, 5)) > 12 and
                not self._get_enemy_at(position) and
                (position.x, position.y) not in self.game_map.data_patches and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes)
    
    def _is_valid_gateway_placement(self, position: Position) -> bool:
        """Check if position is valid for gateway placement."""
        return (self.game_map.is_valid_position(position) and
                position.distance_to(Position(5, 5)) > 25 and
                (position.x, position.y) not in self.game_map.data_patches and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                not self._get_enemy_at(position))
    
    def _generate_patrol_route(self, start: Position) -> List[Position]:
        """Generate a patrol route starting from given position."""
        route = [start]
        route_length = random.randint(4, 8)
        current = start
        
        for _ in range(route_length - 1):
            attempts = 0
            while attempts < 30:
                attempts += 1
                step_size = random.randint(2, 5)
                direction = random.choice([(0, -step_size), (step_size, 0), 
                                         (0, step_size), (-step_size, 0)])
                new_pos = Position(current.x + direction[0], current.y + direction[1])
                
                if (new_pos.is_valid(GameConfig.MAP_WIDTH - 3, GameConfig.MAP_HEIGHT - 3) and
                    new_pos.x >= 3 and new_pos.y >= 3 and
                    self.game_map.is_valid_position(new_pos)):
                    route.append(new_pos)
                    current = new_pos
                    break
        
        # Ensure minimum route length
        if len(route) < 3:
            if start.x < GameConfig.MAP_WIDTH - 5:
                route.append(Position(start.x + 3, start.y))
            if start.y < GameConfig.MAP_HEIGHT - 5:
                route.append(Position(start.x, start.y + 3))
        
        return route

# ============================================================================
# EXPLOIT SYSTEM
# ============================================================================

class ExploitSystem:
    """Handles exploit usage and effects."""
    
    def __init__(self, game: Game):
        self.game = game
    
    def use_exploit(self, exploit_key: str) -> bool:
        """Attempt to use an exploit."""
        if not self.game.player.inventory_manager.can_use_exploit(exploit_key):
            self.game.message_log.add_message("Exploit not equipped")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]
        
        # Check heat limit
        heat_cost = self._calculate_heat_cost(exploit)
        if self.game.player.heat + heat_cost > 100:
            self.game.message_log.add_message("System too hot! Cannot use")
            return False
        
        # Check if exploit requires targeting
        if exploit.targeting != TargetingMode.NONE and exploit.range > 0:
            self.game.targeting_mode = True
            self.game.targeting_exploit = exploit_key
            self.game.cursor_position = Position(self.game.player.x, self.game.player.y)
            self.game.message_log.add_message(f"Targeting {exploit.name}")
            return True
        
        # Execute non-targeting exploits immediately
        return self.execute_exploit(exploit_key, self.game.player.position)
    
    def execute_exploit(self, exploit_key: str, target: Position) -> bool:
        """Execute an exploit at target location."""
        if exploit_key not in GameData.EXPLOITS:
            self.game.message_log.add_message("Unknown exploit")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]
        
        # Validate target
        if not self._validate_target(exploit, target):
            return False
        
        # Apply heat cost
        heat_cost = self._calculate_heat_cost(exploit)
        self.game.player.heat = min(100, self.game.player.heat + heat_cost)
        
        # Execute specific exploit
        success = self._execute_specific_exploit(exploit_key, exploit, target)
        
        if success:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.process_turn()
        
        return success
    
    def _calculate_heat_cost(self, exploit: ExploitDefinition) -> int:
        """Calculate heat cost with efficiency bonus."""
        multiplier = 0.6 if self.game.player.temporary_effects['exploit_efficiency_turns'] > 0 else 1.0
        return int(exploit.heat * multiplier)
    
    def _validate_target(self, exploit: ExploitDefinition, target: Position) -> bool:
        """Validate targeting for exploit."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            self.game.message_log.add_message("Invalid target location")
            return False
        
        distance = self.game.player.position.distance_to(target)
        if distance > exploit.range:
            self.game.message_log.add_message(f"Out of range (Max: {exploit.range})")
            return False
        
        return True
    
    def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
        """Execute the specific exploit effect."""
        if exploit_key == 'shadow_step':
            return self._execute_shadow_step(target)
        elif exploit_key == 'data_mimic':
            return self._execute_data_mimic()
        elif exploit_key == 'noise_maker':
            return self._execute_noise_maker(target)
        elif exploit_key == 'code_injection':
            return self._execute_code_injection(target)
        elif exploit_key == 'buffer_overflow':
            return self._execute_buffer_overflow(target)
        elif exploit_key == 'system_crash':
            return self._execute_system_crash(target, exploit.range)
        elif exploit_key == 'network_scan':
            return self._execute_network_scan()
        elif exploit_key == 'log_wiper':
            return self._execute_log_wiper()
        elif exploit_key == 'emp_burst':
            return self._execute_emp_burst(target, exploit.range)
        
        return False
    
    def _execute_shadow_step(self, target: Position) -> bool:
        """Execute shadow step exploit."""
        if self.game.game_map.is_shadow(target) and self.game.game_map.is_valid_position(target):
            if not self.game._get_enemy_at(target):
                self.game.player.position = target
                self.game.message_log.add_message("Shadow Step executed")
                return True
            else:
                self.game.message_log.add_message("Target occupied")
        else:
            self.game.message_log.add_message("Must target shadow zone")
        return False
    
    def _execute_data_mimic(self) -> bool:
        """Execute data mimic exploit."""
        self.game.player.temporary_effects['data_mimic_turns'] = 5
        self.game.message_log.add_message("Data Mimic active")
        return True
    
    def _execute_noise_maker(self, target: Position) -> bool:
        """Execute noise maker exploit."""
        attracted = 0
        for enemy in self.game.enemies:
            if (enemy.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.RANDOM, EnemyMovement.LINEAR] and
                enemy.position.distance_to(target) <= 10):
                if enemy.type_data.movement == EnemyMovement.LINEAR:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 3
                else:
                    enemy.last_seen_player = target
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 2
                attracted += 1
        self.game.message_log.add_message(f"Noise: {attracted} enemies attracted")
        return True
    
    def _execute_code_injection(self, target: Position) -> bool:
        """Execute code injection exploit."""
        target_enemy = self.game._get_enemy_at(target)
        if target_enemy:
            damage = 35 if target_enemy.type == 'firewall' else 30
            
            if target_enemy.take_damage(damage):
                self.game.enemies.remove(target_enemy)
                self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + 5)
                self.game.message_log.add_message(f"Eliminated {target_enemy.type_data.name}")
            else:
                self.game.message_log.add_message(f"Damaged {target_enemy.type_data.name}")
                target_enemy.state = EnemyState.HOSTILE
                target_enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
            return True
        else:
            self.game.message_log.add_message("No target at location")
            return False
    
    def _execute_buffer_overflow(self, target: Position) -> bool:
        """Execute buffer overflow exploit."""
        distance = self.game.player.position.distance_to(target)
        if distance <= 1:
            target_enemy = self.game._get_enemy_at(target)
            if target_enemy:
                damage = 50
                if target_enemy.take_damage(damage):
                    self.game.enemies.remove(target_enemy)
                    self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + 5)
                    self.game.message_log.add_message(f"Eliminated {target_enemy.type_data.name}")
                else:
                    self.game.message_log.add_message(f"Damaged {target_enemy.type_data.name}")
                    target_enemy.state = EnemyState.HOSTILE
                    target_enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
                return True
            else:
                self.game.message_log.add_message("No enemy at target")
        else:
            self.game.message_log.add_message("Must target adjacent enemy")
        return False
    
    def _execute_system_crash(self, target: Position, exploit_range: int) -> bool:
        """Execute system crash exploit."""
        enemies_hit = []
        for enemy in self.game.enemies[:]:
            if enemy.position.distance_to(target) <= exploit_range:
                enemy.disabled_turns = 4
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                enemies_hit.append(enemy)
        self.game.message_log.add_message(f"System crash: {len(enemies_hit)} disabled")
        return True
    
    def _execute_network_scan(self) -> bool:
        """Execute network scan exploit."""
        self.game.show_patrols = True
        self.game.network_scan_turns = 15
        self.game.message_log.add_message("Network scan active")
        return True
    
    def _execute_log_wiper(self) -> bool:
        """Execute log wiper exploit."""
        old_detection = self.game.player.detection
        self.game.player.detection = max(0, self.game.player.detection - 30)
        actual_reduction = old_detection - self.game.player.detection
        self.game.message_log.add_message(f"Detection: -{actual_reduction:.1f}%")
        return True
    
    def _execute_emp_burst(self, target: Position, exploit_range: int) -> bool:
        """Execute EMP burst exploit."""
        enemies_hit = []
        for enemy in self.game.enemies[:]:
            if enemy.position.distance_to(target) <= exploit_range:
                enemy.disabled_turns = 6
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                enemies_hit.append(enemy)
        self.game.message_log.add_message(f"EMP: {len(enemies_hit)} disabled")
        return True

# ============================================================================
# INPUT HANDLING
# ============================================================================

class InputHandler:
    """Handles all user input and translates it to game actions."""
    
    def __init__(self, game: Game):
        self.game = game
        self.exploit_system = ExploitSystem(game)
    
    def handle_keydown(self, event) -> bool:
        """Handle keydown events. Returns True if game should continue."""
        # Global exit conditions
        if event.sym == tcod.event.KeySym.ESCAPE:
            return self._handle_escape()
        
        # Dead/game over state
        if self.game.player.cpu <= 0 or self.game.game_over:
            return True  # Only allow ESC when dead
        
        # Modal screens
        if self.game.show_help:
            self.game.show_help = False
            return True
        
        if self.game.show_inventory:
            return self._handle_inventory_input(event)
        
        if self.game.targeting_mode:
            return self._handle_targeting_input(event)
        
        # Normal gameplay
        return self._handle_gameplay_input(event)
    
    def _handle_escape(self) -> bool:
        """Handle escape key in different contexts."""
        if self.game.show_help:
            self.game.show_help = False
        elif self.game.show_inventory:
            self.game.show_inventory = False
        elif self.game.targeting_mode:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
        else:
            return False  # Exit game
        return True
    
    def _handle_inventory_input(self, event) -> bool:
        """Handle input while inventory is open."""
        # Navigation keys - expanded to include arrows and numpad
        if event.sym in (tcod.event.KeySym.W, tcod.event.KeySym.UP, tcod.event.KeySym.KP_8):
            self._navigate_inventory(-1)
        elif event.sym in (tcod.event.KeySym.S, tcod.event.KeySym.DOWN, tcod.event.KeySym.KP_2):
            self._navigate_inventory(1)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            self._use_selected_inventory_item()
        elif event.sym == tcod.event.KeySym.I:
            self.game.show_inventory = False
        
        return True

    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
            # WASD + QEZC (original)
            tcod.event.KeySym.W: (0, -1),
            tcod.event.KeySym.Q: (-1, -1),
            tcod.event.KeySym.E: (1, -1),
            tcod.event.KeySym.D: (1, 0),
            tcod.event.KeySym.C: (1, 1),
            tcod.event.KeySym.S: (0, 1),
            tcod.event.KeySym.Z: (-1, 1),
            tcod.event.KeySym.A: (-1, 0),
            # Arrow keys
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            # Numpad
            tcod.event.KeySym.KP_8: (0, -1),
            tcod.event.KeySym.KP_9: (1, -1),
            tcod.event.KeySym.KP_6: (1, 0),
            tcod.event.KeySym.KP_3: (1, 1),
            tcod.event.KeySym.KP_2: (0, 1),
            tcod.event.KeySym.KP_1: (-1, 1),
            tcod.event.KeySym.KP_4: (-1, 0),
            tcod.event.KeySym.KP_7: (-1, -1)
        }
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game._move_cursor(dx, dy)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            self.exploit_system.execute_exploit(
                self.game.targeting_exploit, 
                self.game.cursor_position
            )
        
        return True
    
    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
            # WASD + QEZC (original)
            tcod.event.KeySym.W: (0, -1),
            tcod.event.KeySym.Q: (-1, -1),
            tcod.event.KeySym.E: (1, -1),
            tcod.event.KeySym.D: (1, 0),
            tcod.event.KeySym.C: (1, 1),
            tcod.event.KeySym.S: (0, 1),
            tcod.event.KeySym.Z: (-1, 1),
            tcod.event.KeySym.A: (-1, 0),
            # Arrow keys
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            # Numpad
            tcod.event.KeySym.KP_8: (0, -1),
            tcod.event.KeySym.KP_9: (1, -1),
            tcod.event.KeySym.KP_6: (1, 0),
            tcod.event.KeySym.KP_3: (1, 1),
            tcod.event.KeySym.KP_2: (0, 1),
            tcod.event.KeySym.KP_1: (-1, 1),
            tcod.event.KeySym.KP_4: (-1, 0),
            tcod.event.KeySym.KP_7: (-1, -1)
        }
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game.move_player(dx, dy)
        
        # Wait/rest
        elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.PERIOD, tcod.event.KeySym.KP_5):
            self.game.process_turn()
        
        # UI toggles
        elif event.sym == tcod.event.KeySym.TAB:
            self._toggle_patrol_visibility()
        elif event.sym == tcod.event.KeySym.I:
            self._open_inventory()
        elif event.sym == tcod.event.KeySym.SLASH and event.mod & tcod.event.KMOD_SHIFT:
            self.game.show_help = True
        
        # Exploit usage (1-5 keys)
        elif event.sym == tcod.event.KeySym.N1:
            self._use_exploit_slot(0)
        elif event.sym == tcod.event.KeySym.N2:
            self._use_exploit_slot(1)
        elif event.sym == tcod.event.KeySym.N3:
            self._use_exploit_slot(2)
        elif event.sym == tcod.event.KeySym.N4:
            self._use_exploit_slot(3)
        elif event.sym == tcod.event.KeySym.N5:
            self._use_exploit_slot(4)
        
        return True
    
    def _navigate_inventory(self, direction: int):
        """Navigate inventory selection."""
        total_items = len(self.game.player.inventory_manager.items)
        if total_items > 0:
            self.game.inventory_selection = (self.game.inventory_selection + direction) % total_items
    
    def _use_selected_inventory_item(self):
        """Use the currently selected inventory item."""
        items = self.game.player.inventory_manager.items
        if items and 0 <= self.game.inventory_selection < len(items):
            selected_item = items[self.game.inventory_selection]
            if selected_item.use(self.game.player, self.game):
                # Update selection if item was consumed
                self.game.inventory_selection = min(
                    self.game.inventory_selection, 
                    len(self.game.player.inventory_manager.items) - 1
                )
    
    def _toggle_patrol_visibility(self):
        """Toggle patrol route visibility."""
        self.game.show_patrols = not self.game.show_patrols
        status = "visible" if self.game.show_patrols else "hidden"
        self.game.message_log.add_message(f"Patrol routes {status}")
    
    def _open_inventory(self):
        """Open the inventory screen."""
        self.game.show_inventory = True
        self.game.inventory_selection = 0
    
    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            self.exploit_system.use_exploit(equipped[slot])

# ============================================================================
# RENDERING SYSTEM
# ============================================================================

class Renderer:
    """Handles all game rendering."""
    
    def __init__(self):
        self.ui_renderer = UIRenderer()
        self.map_renderer = MapRenderer()
    
    def render_game(self, console: tcod.console.Console, game: Game):
        """Render the complete game state."""
        console.clear()
        
        if game.show_help:
            self.ui_renderer.render_help_screen(console)
        elif game.show_inventory:
            self.ui_renderer.render_inventory_screen(console, game)
        else:
            self._render_main_game_screen(console, game)
    
    def _render_main_game_screen(self, console: tcod.console.Console, game: Game):
        """Render the main game screen."""
        self.ui_renderer.render_top_status_bar(console, game)
        self.map_renderer.render_map(console, game)
        self.ui_renderer.render_bottom_panel(console, game)
        self.ui_renderer.render_system_log(console, game)
        
        # Render game over/death messages
        if game.game_over:
            self._render_victory_message(console)
        elif game.player.cpu <= 0:
            self._render_death_message(console)
    
    def _render_victory_message(self, console: tcod.console.Console):
        """Render victory message."""
        center_x = GameConfig.GAME_AREA_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        console.print(center_x - 10, center_y, "MISSION COMPLETE!", fg=Colors.GREEN)
        console.print(center_x - 15, center_y + 1, "All networks infiltrated!", fg=Colors.GREEN)
        console.print(center_x - 8, center_y + 3, "Press ESC to exit", fg=Colors.UI_TEXT)
    
    def _render_death_message(self, console: tcod.console.Console):
        """Render death message."""
        center_x = GameConfig.GAME_AREA_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        console.print(center_x - 8, center_y, "SYSTEM FAILURE", fg=Colors.RED)
        console.print(center_x - 12, center_y + 1, "Consciousness purged", fg=Colors.RED)
        console.print(center_x - 8, center_y + 3, "Press ESC to exit", fg=Colors.UI_TEXT)

class UIRenderer:
    """Renders UI elements."""
    
    def render_help_screen(self, console: tcod.console.Console):
        """Render the help screen."""
        console.clear()
        
        # Title
        title = "ROGUE SIGNAL PROTOCOL - HELP"
        console.print(GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        y = 5
        help_sections = self._get_help_sections()
        
        for text, color in help_sections:
            if y < GameConfig.SCREEN_HEIGHT - 2:
                console.print(2, y, text, fg=color)
                y += 1
        
        console.print(GameConfig.SCREEN_WIDTH // 2 - 10, GameConfig.SCREEN_HEIGHT - 2, 
                     "Press any key to return", fg=Colors.YELLOW)
    
    def _get_help_sections(self) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Get help text sections."""
        return [
            ("MOVEMENT (8-DIRECTIONAL):", Colors.CYAN),
            ("  WASD + QEZC: Move in 8 directions", Colors.WHITE),
            ("  Arrow Keys: 4-directional movement", Colors.WHITE),
            ("  Numpad 1-9: 8-directional movement", Colors.WHITE),
            ("  Space/./5: Wait/Rest", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("EXPLOITS:", Colors.CYAN),
            ("  1-5: Use equipped exploits", Colors.WHITE),
            ("  Follow targeting prompts for ranged exploits", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("INVENTORY & EQUIPMENT:", Colors.CYAN),
            ("  I: Open inventory", Colors.WHITE),
            ("  W/S or ↑/↓ or 8/2: Navigate selection", Colors.WHITE),
            ("  Enter: Use data patch / Equip exploit", Colors.WHITE),
            ("  Max 5 exploits can be equipped at once", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("INTERFACE:", Colors.CYAN),
            ("  Tab: Toggle patrol route visibility", Colors.WHITE),
            ("  ?: This help screen", Colors.WHITE),
            ("  ESC: Cancel targeting/Close menus/Quit", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("GAMEPLAY TIPS:", Colors.CYAN),
            ("  - Hide in shadows (.) to avoid detection", Colors.WHITE),
            ("  - Use cooling nodes (C) to reduce heat", Colors.WHITE),
            ("  - CPU recovery nodes (+) restore health", Colors.WHITE),
            ("  - Collect data patches (D) for various effects", Colors.WHITE),
            ("  - Stealth attacks deal more damage", Colors.WHITE),
            ("  - Watch your heat and detection levels!", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("ENEMY TYPES:", Colors.CYAN),
            ("  s: Scanner (static, low vision)", Colors.ORANGE),
            ("  p: Patrol (moves on routes)", Colors.ORANGE),
            ("  b: Bot (random movement)", Colors.ORANGE),
            ("  F: Firewall (high health, static)", Colors.RED),
            ("  H: Hunter (seeks players)", Colors.RED),
            ("  A: Admin Avatar (extremely dangerous!)", Colors.RED),
        ]
    
    def render_inventory_screen(self, console: tcod.console.Console, game: Game):
        """Render the inventory screen."""
        console.clear()
        
        # Title
        title = "INVENTORY SYSTEM"
        console.print(GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        y = 5
        
        # Equipped exploits section
        y = self._render_equipped_exploits(console, game, y)
        y += 2
        
        # Data patches section
        y = self._render_data_patches(console, game, y)
        y += 2
        
        # Unequipped exploits section
        y = self._render_unequipped_exploits(console, game, y)
        
        # Controls
        self._render_inventory_controls(console)
    
    def _render_equipped_exploits(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render equipped exploits section."""
        console.print(2, y, "EQUIPPED EXPLOITS:", fg=Colors.CYAN)
        y += 1
        
        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                color = Colors.GREEN
                status_text = f"{i+1}. {exploit.name} (RAM: {exploit.ram}, Heat: {exploit.heat})"
            else:
                color = Colors.RED
                status_text = f"{i+1}. INVALID: {exploit_key}"
            
            console.print(4, y, status_text, fg=color)
            y += 1
        
        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            console.print(4, y, f"[{equipped_count}/{max_exploits} slots used]", fg=Colors.YELLOW)
            y += 1
        
        return y
    
    def _render_data_patches(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render data patches section."""
        data_patches = game.player.inventory_manager.get_items_by_type("data_patch")
        console.print(2, y, f"DATA PATCHES ({len(data_patches)}):", fg=Colors.CYAN)
        y += 1
        
        if not data_patches:
            console.print(4, y, "No data patches collected", fg=Colors.WHITE)
            y += 1
        else:
            for i, patch in enumerate(data_patches):
                if i == game.inventory_selection and len(data_patches) > 0:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                description = patch.description if patch.discovered else "Unknown effect"
                console.print(4, y, f"{prefix} {patch.name} - {description}", fg=color)
                y += 1
        
        return y
    
    def _render_unequipped_exploits(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render unequipped exploits section."""
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        console.print(2, y, f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):", fg=Colors.CYAN)
        y += 1
        
        if not exploit_items:
            console.print(4, y, "No unequipped exploits", fg=Colors.WHITE)
            y += 1
        else:
            data_patches = game.player.inventory_manager.get_items_by_type("data_patch")
            start_selection = len(data_patches)
            
            for i, exploit_item in enumerate(exploit_items):
                selection_index = start_selection + i
                if selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                console.print(4, y, f"{prefix} {exploit_item.name} - {exploit_item.description}", fg=color)
                y += 1
        
        return y
    
    def _render_inventory_controls(self, console: tcod.console.Console):
        """Render inventory controls."""
        y_start = GameConfig.SCREEN_HEIGHT - 6
        
        console.print(2, y_start, "CONTROLS:", fg=Colors.CYAN)
        console.print(4, y_start + 1, "W/S: Navigate selection", fg=Colors.WHITE)
        console.print(4, y_start + 2, "Enter: Use data patch / Equip exploit", fg=Colors.WHITE)
        console.print(4, y_start + 3, "U: Unequip selected exploit (when on equipped list)", fg=Colors.WHITE)
        console.print(4, y_start + 4, "ESC/I: Close inventory", fg=Colors.WHITE)
    
    def render_top_status_bar(self, console: tcod.console.Console, game: Game):
        """Render the top status bar."""
        # Clear the top line
        for x in range(GameConfig.GAME_AREA_WIDTH):
            console.print(x, 0, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Color coding for status values
        cpu_color = self._get_cpu_color(game.player.cpu)
        heat_color = self._get_heat_color(game.player.heat)
        detection_color = self._get_detection_color(game.player.detection)
        ram_color = Colors.RED if game.player.ram_used > game.player.ram_total else Colors.GREEN
        
        # Build status line
        status_parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            f"Heat:{game.player.heat:3d}°C",
            f"Det:{int(game.player.detection):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB",
            f"Turn:{game.turn:4d}",
            "Press ? for help"
        ]
        
        colors = [cpu_color, heat_color, detection_color, ram_color, Colors.UI_TEXT, Colors.YELLOW]
        
        x_pos = 1
        for part, color in zip(status_parts, colors):
            if x_pos + len(part) < GameConfig.GAME_AREA_WIDTH - 1:
                console.print(x_pos, 0, part, fg=color, bg=Colors.UI_BG)
                x_pos += len(part) + 2
    
    def _get_cpu_color(self, cpu: int) -> Tuple[int, int, int]:
        """Get color for CPU display."""
        if cpu < 30:
            return Colors.RED
        elif cpu < 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_heat_color(self, heat: int) -> Tuple[int, int, int]:
        """Get color for heat display."""
        if heat > 80:
            return Colors.RED
        elif heat > 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_detection_color(self, detection: float) -> Tuple[int, int, int]:
        """Get color for detection display."""
        if detection > 75:
            return Colors.RED
        elif detection > 50:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def render_bottom_panel(self, console: tcod.console.Console, game: Game):
        """Render the bottom information panel."""
        # Clear panel area
        for x in range(GameConfig.GAME_AREA_WIDTH):
            for y in range(GameConfig.PANEL_Y, GameConfig.SCREEN_HEIGHT):
                console.print(x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Panel border
        border = "+" + "-" * (GameConfig.GAME_AREA_WIDTH - 2) + "+"
        console.print(0, GameConfig.PANEL_Y, border, fg=Colors.LOG_BORDER, bg=Colors.UI_BG)
        
        # Network and position info
        self._render_network_info(console, game)
        
        # Active effects
        self._render_active_effects(console, game)
        
        # Equipped exploits
        self._render_equipped_exploits_panel(console, game)
        
        # Current status/warnings
        self._render_status_warnings(console, game)
    
    def _render_network_info(self, console: tcod.console.Console, game: Game):
        """Render network and position information."""
        level_names = {1: "Corporate", 2: "Government", 3: "Military"}  # Remove tutorial entry
        y = GameConfig.PANEL_Y + 1
        
        console.print(1, y, f"Network: {level_names.get(game.level, 'Unknown')}", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        console.print(25, y, f"Position: ({game.player.x:2d},{game.player.y:2d})", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        console.print(45, y, f"Vision: {game.player.get_vision_range():2d}", fg=Colors.UI_TEXT, bg=Colors.UI_BG)    

    def _render_active_effects(self, console: tcod.console.Console, game: Game):
        """Render active temporary effects."""
        y = GameConfig.PANEL_Y + 2
        effects = []
        
        for effect_name, turns in game.player.temporary_effects.items():
            if turns > 0:
                display_name = effect_name.replace('_turns', '').replace('_', ' ').title()
                effects.append(f"{display_name}({turns})")
        
        if game.network_scan_turns > 0:
            effects.append(f"Scan({game.network_scan_turns})")
        
        if effects:
            effects_text = "Effects: " + " ".join(effects)
            console.print(1, y, effects_text[:GameConfig.GAME_AREA_WIDTH-2], fg=Colors.CYAN, bg=Colors.UI_BG)
        else:
            console.print(1, y, "Effects: None", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
    
    def _render_equipped_exploits_panel(self, console: tcod.console.Console, game: Game):
        """Render equipped exploits in bottom panel."""
        y = GameConfig.PANEL_Y + 3
        console.print(1, y, "Exploits:", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits[:5]):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                heat_cost = exploit.heat
                if game.player.temporary_effects['exploit_efficiency_turns'] > 0:
                    heat_cost = int(heat_cost * 0.6)
                
                heat_ok = game.player.heat + heat_cost <= 100
                color = Colors.GREEN if heat_ok else Colors.RED
                exploit_text = f"{i+1}.{exploit.name[:8]}"
                x_pos = 11 + i * 12
                if x_pos < GameConfig.GAME_AREA_WIDTH - 10:
                    console.print(x_pos, y, exploit_text, fg=color, bg=Colors.UI_BG)
    
    def _render_status_warnings(self, console: tcod.console.Console, game: Game):
        """Render status warnings and current action."""
        y = GameConfig.PANEL_Y + 4
        
        if game.targeting_mode and game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            console.print(1, y, f"TARGETING: {exploit.name} - Range: {exploit.range}", fg=Colors.YELLOW, bg=Colors.UI_BG)
        elif game.player.detection >= 85:
            console.print(1, y, "*** CRITICAL DETECTION - ADMIN IMMINENT ***", fg=Colors.RED, bg=Colors.UI_BG)
        elif game.player.detection >= 60:
            console.print(1, y, "** ELEVATED DETECTION LEVEL **", fg=Colors.YELLOW, bg=Colors.UI_BG)
        elif game.player.heat >= 90:
            console.print(1, y, "** SYSTEM OVERHEATING - CRITICAL **", fg=Colors.RED, bg=Colors.UI_BG)
        elif game.player.cpu < 30:
            console.print(1, y, "** LOW CPU - CRITICAL **", fg=Colors.RED, bg=Colors.UI_BG)
        else:
            console.print(1, y, "Status: Operational", fg=Colors.GREEN, bg=Colors.UI_BG)
    
    def render_system_log(self, console: tcod.console.Console, game: Game):
        """Render the system log on the right side."""
        # Draw log border
        for y in range(GameConfig.SCREEN_HEIGHT):
            console.print(GameConfig.GAME_AREA_WIDTH, y, '|', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Log header
        console.print(GameConfig.GAME_AREA_WIDTH + 1, 0, "SYSTEM LOG", fg=Colors.CYAN, bg=Colors.LOG_BG)
        console.print(GameConfig.GAME_AREA_WIDTH + 1, 1, "-" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Clear log area
        for x in range(GameConfig.GAME_AREA_WIDTH + 1, GameConfig.SCREEN_WIDTH):
            for y in range(2, GameConfig.SCREEN_HEIGHT):
                console.print(x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)
        
        # Process and display messages
        self._render_log_messages(console, game)
    
    def _render_log_messages(self, console: tcod.console.Console, game: Game):
        """Render log messages with proper wrapping."""
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.SCREEN_HEIGHT - 2
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines
        
        for i, (line, color) in enumerate(visible_lines):
            y_pos = 2 + i
            if y_pos < GameConfig.SCREEN_HEIGHT:
                console.print(GameConfig.GAME_AREA_WIDTH + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)
    
    def _wrap_messages(self, messages: List[Tuple[str, Tuple[int, int, int]]]) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Wrap long messages across multiple lines."""
        wrapped_lines = []
        max_msg_width = GameConfig.LOG_WIDTH - 2
        
        for message, color in messages:
            if len(message) <= max_msg_width:
                wrapped_lines.append((message, color))
            else:
                # Wrap long messages
                words = message.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_msg_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_lines.append((current_line, color))
                        current_line = word
                
                if current_line:
                    wrapped_lines.append((current_line, color))
        
        return wrapped_lines

class MapRenderer:
    """Renders the game map and entities."""
    
    def render_map(self, console: tcod.console.Console, game: Game):
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
            console.print(1, 1, f"Map Error: {str(e)[:50]}", fg=Colors.RED, bg=Colors.BLACK)
    
    def _calculate_camera_offset(self, player: Player) -> Position:
        """Calculate camera offset to center on player."""
        camera_x = max(0, min(GameConfig.MAP_WIDTH - GameConfig.GAME_AREA_WIDTH, 
                             player.x - GameConfig.GAME_AREA_WIDTH // 2))
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - (GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1), 
                             player.y - (GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1) // 2))
        return Position(camera_x, camera_y)
    
    def _render_terrain(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render basic terrain (floors, walls, items)."""
        for screen_x in range(GameConfig.GAME_AREA_WIDTH):
            for screen_y in range(1, GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                world_pos = Position(screen_x + camera_offset.x, screen_y - 1 + camera_offset.y)
                
                if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    distance = game.player.position.distance_to(world_pos)
                    
                    if distance <= vision_range or game.player.can_see_through_walls():
                        self._render_tile(console, screen_x, screen_y, world_pos, game)
                    else:
                        # Fog of war
                        console.print(screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
                else:
                    # Outside map bounds
                    console.print(screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
    
    def _render_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game: Game):
        """Render a single tile."""
        # Priority order for tile rendering
        if game.game_map.is_wall(world_pos):
            console.print(screen_x, screen_y, '#', fg=Colors.WALL, bg=Colors.BLACK)
        elif game.game_map.is_cooling_node(world_pos):
            console.print(screen_x, screen_y, 'C', fg=Colors.CYAN, bg=Colors.BLACK)
        elif game.game_map.is_cpu_recovery_node(world_pos):
            console.print(screen_x, screen_y, '+', fg=Colors.RED, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.data_patches:
            patch = game.game_map.data_patches[(world_pos.x, world_pos.y)]
            color = self._get_patch_color(patch.color)
            console.print(screen_x, screen_y, 'D', fg=color, bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            console.print(screen_x, screen_y, '.', fg=Colors.GREEN, bg=Colors.SHADOW)
        else:
            console.print(screen_x, screen_y, '.', fg=Colors.FLOOR, bg=Colors.BLACK)
    
    def _get_patch_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple for data patch."""
        color_map = {
            'crimson': Colors.RED, 'azure': Colors.BLUE, 'emerald': Colors.GREEN,
            'golden': Colors.YELLOW, 'violet': Colors.MAGENTA, 'silver': Colors.WHITE
        }
        return color_map.get(color_name, Colors.WHITE)
    
    def _render_vision_overlays(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render enemy vision range overlays."""
        if game.player.is_invisible():
            return
        
        for enemy in game.enemies:
            if enemy.disabled_turns > 0:
                continue
            
            distance_to_player = game.player.position.distance_to(enemy.position)
            if distance_to_player <= vision_range:
                overlay_color = self._get_vision_overlay_color(enemy.state)
                self._render_enemy_vision_range(console, enemy, camera_offset, overlay_color)
    
    def _get_vision_overlay_color(self, enemy_state: EnemyState) -> Tuple[int, int, int]:
        """Get vision overlay color based on enemy state."""
        if enemy_state == EnemyState.HOSTILE:
            return Colors.VISION_HOSTILE
        elif enemy_state == EnemyState.ALERT:
            return Colors.VISION_ALERT
        else:
            return Colors.VISION_UNAWARE
    
    def _render_enemy_vision_range(self, console: tcod.console.Console, enemy: Enemy, camera_offset: Position, overlay_color: Tuple[int, int, int]):
        """Render vision range for a single enemy."""
        for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
            for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                    screen_x = enemy.x - camera_offset.x + dx
                    screen_y = enemy.y - camera_offset.y + dy + 1
                    
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, screen_x, screen_y, overlay_color)
    
    def _safely_overlay_tile(self, console: tcod.console.Console, x: int, y: int, bg_color: Tuple[int, int, int]):
        """Safely overlay background color on existing tile."""
        try:
            current_char = console.ch[x, y]
            if current_char != ord(' '):  # Don't overlay fog of war
                current_fg = console.fg[x, y]
                if hasattr(current_fg, '__iter__') and len(current_fg) >= 3:
                    fg_tuple = tuple(current_fg[:3])
                    console.print(x, y, chr(current_char), fg=fg_tuple, bg=bg_color)
        except (IndexError, ValueError):
            pass
    
    def _render_patrol_routes(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render patrol routes if enabled."""
        if not game.show_patrols:
            return
        
        for enemy in game.enemies:
            if enemy.patrol_points and len(enemy.patrol_points) > 1:
                distance_to_player = game.player.position.distance_to(enemy.position)
                if distance_to_player <= vision_range:
                    for point in enemy.patrol_points:
                        screen_x = point.x - camera_offset.x
                        screen_y = point.y - camera_offset.y + 1
                        if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                            1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                            console.print(screen_x, screen_y, '*', fg=Colors.YELLOW, bg=Colors.BLACK)
    
    def _render_gateway(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render the level gateway."""
        if not game.game_map.gateway:
            return
        
        screen_x = game.game_map.gateway.x - camera_offset.x
        screen_y = game.game_map.gateway.y - camera_offset.y + 1
        
        if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            distance = game.player.position.distance_to(game.game_map.gateway)
            if distance <= vision_range:
                console.print(screen_x, screen_y, '>', fg=Colors.GATEWAY, bg=Colors.BLACK)
    
    def _render_enemies(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render all enemies."""
        for enemy in game.enemies:
            screen_x = enemy.x - camera_offset.x
            screen_y = enemy.y - camera_offset.y + 1
            
            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                distance = game.player.position.distance_to(enemy.position)
                if distance <= vision_range:
                    console.print(screen_x, screen_y, enemy.type_data.symbol, 
                                fg=enemy.get_color(), bg=Colors.BLACK)
    
    def _render_player(self, console: tcod.console.Console, game: Game, camera_offset: Position):
        """Render the player character."""
        player_screen_x = game.player.x - camera_offset.x
        player_screen_y = game.player.y - camera_offset.y + 1
        
        if (0 <= player_screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= player_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            player_color = self._get_player_color(game.player)
            console.print(player_screen_x, player_screen_y, '@', fg=player_color, bg=Colors.BLACK)
    
    def _get_player_color(self, player: Player) -> Tuple[int, int, int]:
        """Get player color based on current state."""
        if player.is_invisible():
            return Colors.BLUE
        elif player.temporary_effects['speed_boost_turns'] > 0:
            return Colors.YELLOW
        elif player.heat >= 90:
            return Colors.RED
        else:
            return Colors.PLAYER
    
    def _render_targeting_cursor(self, console: tcod.console.Console, game: Game, camera_offset: Position):
        """Render targeting cursor and range indicator."""
        if not game.targeting_mode:
            return
        
        cursor_screen_x = game.cursor_position.x - camera_offset.x
        cursor_screen_y = game.cursor_position.y - camera_offset.y + 1
        
        if (0 <= cursor_screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= cursor_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            console.print(cursor_screen_x, cursor_screen_y, 'X', fg=Colors.RED, bg=Colors.BLACK)
        
        # Show range indicator
        if game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            self._render_targeting_range(console, game.player.position, exploit.range, camera_offset)
    
    def _render_targeting_range(self, console: tcod.console.Console, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator."""
        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                if dx*dx + dy*dy <= range_val*range_val:
                    range_screen_x = center.x - camera_offset.x + dx
                    range_screen_y = center.y - camera_offset.y + dy + 1
                    
                    if (0 <= range_screen_x < GameConfig.GAME_AREA_WIDTH and 
                        1 <= range_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, range_screen_x, range_screen_y, (40, 40, 40))

# ============================================================================
# MAIN GAME LOOP AND INITIALIZATION
# ============================================================================

def initialize_tcod_context():
    """Initialize tcod context with fallback handling."""
    tileset = None
    try:
        # Try to load the preferred tileset
        tileset = tcod.tileset.load_tilesheet(
            "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
        )
    except (FileNotFoundError, ImportError, Exception):
        try:
            # Try default tileset
            tileset = tcod.tileset.load_tilesheet(
                tcod.tileset.get_default(), 16, 16, tcod.tileset.CHARMAP_TCOD
            )
        except Exception:
            # Use built-in fallback
            pass
    
    context_args = {
        "columns": GameConfig.SCREEN_WIDTH,
        "rows": GameConfig.SCREEN_HEIGHT,
        "title": "Rogue Signal Protocol v51 - Enhanced Combat & Inventory",
        "vsync": True
    }
    
    if tileset:
        context_args["tileset"] = tileset
    
    return tcod.context.new(**context_args)

def main():
    """Main game loop with improved error handling."""
    try:
        with initialize_tcod_context() as context:
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT, order='F')
            game = Game()
            renderer = Renderer()
            input_handler = InputHandler(game)
            
            # Initial welcome messages - Remove tutorial references
            game.message_log.add_message("Welcome to Rogue Signal Protocol v51!")
            game.message_log.add_message("Enhanced UI with right-side system log")
            game.message_log.add_message("8-way movement and improved combat")
            game.message_log.add_message("Navigate using stealth")
            game.message_log.add_message("Reach the gateway (>)")
            game.message_log.add_message("Hide in shadows (.) to avoid detection")
            game.message_log.add_message("Starting Corporate Network infiltration...")

            # Main game loop
            while True:
                try:
                    # Render current game state
                    renderer.render_game(console, game)
                    context.present(console)
                    
                    # Handle input events
                    for event in tcod.event.wait():
                        if event.type == "QUIT":
                            return
                        elif event.type == "KEYDOWN":
                            if not input_handler.handle_keydown(event):
                                return  # Exit game
                        
                except Exception as e:
                    # Handle rendering errors gracefully
                    print(f"Rendering error: {e}")
                    console.clear()
                    console.print(1, 1, f"Error: {str(e)[:50]}", fg=Colors.RED)
                    console.print(1, 2, "Press ESC to exit", fg=Colors.WHITE)
                    context.present(console)
                    
                    for event in tcod.event.wait():
                        if event.type == "QUIT" or (event.type == "KEYDOWN" and event.sym == tcod.event.KeySym.ESCAPE):
                            return
    
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()