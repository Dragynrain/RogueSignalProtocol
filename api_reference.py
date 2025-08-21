"""
Rogue Signal Protocol - Core API Reference
This file documents the main classes and interfaces for the game engine.
"""

from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass
import tcod

# ============================================================================
# CORE GAME ENTITIES
# ============================================================================

class EntityType(Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    ITEM = "item"
    OBSTACLE = "obstacle"
    EXIT = "exit"

class Direction(Enum):
    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)
    NORTHEAST = (1, -1)
    NORTHWEST = (-1, -1)
    SOUTHEAST = (1, 1)
    SOUTHWEST = (-1, 1)

@dataclass
class Position:
    """Represents a 2D position in the game world."""
    x: int
    y: int
    
    def __add__(self, other: "Position") -> "Position":
        return Position(self.x + other.x, self.y + other.y)
    
    def distance_to(self, other: "Position") -> float:
        """Calculate Euclidean distance to another position."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
    
    def manhattan_distance(self, other: "Position") -> int:
        """Calculate Manhattan distance to another position."""
        return abs(self.x - other.x) + abs(self.y - other.y)

class Entity:
    """Base class for all game entities."""
    
    def __init__(self, 
                 entity_id: str,
                 entity_type: EntityType,
                 position: Position,
                 symbol: str,
                 color: Tuple[int, int, int] = (255, 255, 255)):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.position = position
        self.symbol = symbol
        self.color = color
        self.blocks_movement = False
        self.blocks_vision = False
    
    def move_to(self, new_position: Position) -> bool:
        """Move entity to new position. Returns True if successful."""
        self.position = new_position
        return True

# ============================================================================
# PLAYER SYSTEM
# ============================================================================

class PlayerClass(Enum):
    SCRIPT_KIDDIE = "script_kiddie"
    GHOST_PROTOCOL = "ghost_protocol"
    BATTLE_HACKER = "battle_hacker"
    DATA_ARCHAEOLOGIST = "data_archaeologist"
    QUANTUM_INFILTRATOR = "quantum_infiltrator"
    ADMIN_IMPERSONATOR = "admin_impersonator"
    ZERO_DAY = "zero_day"

@dataclass
class PlayerStats:
    """Player character statistics."""
    max_hp: int
    current_hp: int
    max_cpu: int
    current_cpu: int
    heat_capacity: int
    current_heat: int
    max_ram: int
    used_ram: int
    detection_resistance: int
    access_level: int

class Player(Entity):
    """Player character entity."""
    
    def __init__(self, player_class: PlayerClass, position: Position):
        super().__init__("player", EntityType.PLAYER, position, "@")
        self.player_class = player_class
        self.stats = PlayerStats(60, 60, 100, 100, 75, 0, 8, 0, 0, 0)
        self.loaded_exploits: Dict[int, "Exploit"] = {}
        self.inventory: "Inventory" = Inventory()
        self.visible_positions: set[Position] = set()
    
    def take_damage(self, amount: int) -> bool:
        """Take damage. Returns True if player dies."""
        self.stats.current_hp = max(0, self.stats.current_hp - amount)
        return self.stats.current_hp <= 0
    
    def heal(self, amount: int) -> None:
        """Heal player by specified amount."""
        self.stats.current_hp = min(self.stats.max_hp, 
                                   self.stats.current_hp + amount)
    
    def add_heat(self, amount: int) -> bool:
        """Add heat. Returns True if overheated."""
        self.stats.current_heat = min(self.stats.heat_capacity,
                                     self.stats.current_heat + amount)
        return self.stats.current_heat >= self.stats.heat_capacity
    
    def can_see(self, position: Position) -> bool:
        """Check if player can see given position."""
        return position in self.visible_positions

# ============================================================================
# ENEMY SYSTEM
# ============================================================================

class PatrolType(Enum):
    LINEAR = "linear"
    CIRCULAR = "circular"
    RANDOM_WALK = "random_walk"
    STATIC = "static"
    HUNTER = "hunter"

class EnemyState(Enum):
    UNAWARE = "unaware"      # Green - doesn't know player exists
    SPOTTED = "spotted"      # Yellow - sees player, 1 turn grace
    ALERTED = "alerted"      # Red - hunting player
    HUNTING = "hunting"      # Red - moving to last known position

@dataclass
class PatrolRoute:
    """Defines an enemy's patrol pattern."""
    patrol_type: PatrolType
    waypoints: List[Position]
    current_waypoint: int = 0
    cycle_length: int = 8
    direction_change_frequency: Tuple[int, int] = (3, 5)

class Enemy(Entity):
    """Enemy entity with AI behavior."""
    
    def __init__(self, 
                 enemy_id: str,
                 position: Position,
                 symbol: str,
                 name: str,
                 hp: int,
                 damage: int,
                 vision_range: int,
                 patrol_route: PatrolRoute):
        super().__init__(enemy_id, EntityType.ENEMY, position, symbol)
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.damage = damage
        self.vision_range = vision_range
        self.patrol_route = patrol_route
        self.state = EnemyState.UNAWARE
        self.last_known_player_pos: Optional[Position] = None
        self.alert_timer = 0
        self.visible_positions: set[Position] = set()
    
    def can_see_player(self, player_pos: Position) -> bool:
        """Check if enemy can see player at given position."""
        distance = self.position.distance_to(player_pos)
        return (distance <= self.vision_range and 
                player_pos in self.visible_positions)
    
    def update_ai(self, player: Player, game_map: "GameMap") -> None:
        """Update enemy AI behavior."""
        if self.can_see_player(player.position):
            if self.state == EnemyState.UNAWARE:
                self.state = EnemyState.SPOTTED
                self.alert_timer = 1
            elif self.state == EnemyState.SPOTTED:
                self.state = EnemyState.ALERTED
                self.last_known_player_pos = player.position
                self._alert_nearby_enemies(game_map)
        else:
            if self.state == EnemyState.SPOTTED:
                self.state = EnemyState.UNAWARE
                self.alert_timer = 0
            elif self.state == EnemyState.ALERTED:
                if self.alert_timer > 0:
                    self.alert_timer -= 1
                else:
                    self.state = EnemyState.UNAWARE
    
    def _alert_nearby_enemies(self, game_map: "GameMap") -> None:
        """Alert enemies within 5 squares."""
        for enemy in game_map.enemies:
            if (enemy != self and 
                self.position.distance_to(enemy.position) <= 5):
                enemy.state = EnemyState.ALERTED
                enemy.last_known_player_pos = self.last_known_player_pos

# ============================================================================
# STEALTH SYSTEM
# ============================================================================

class StealthSystem:
    """Manages stealth detection and visibility."""
    
    def __init__(self):
        self.detection_level = 0
        self.max_detection = 100
        self.detection_areas: Dict[Position, int] = {}
    
    def calculate_detection_chance(self, 
                                   player: Player, 
                                   enemy: Enemy) -> float:
        """Calculate chance of detection based on various factors."""
        base_chance = 100.0  # 100% if in vision and no modifiers
        
        # Apply access level reduction
        if enemy.can_see_player(player.position):
            access_reduction = player.stats.access_level * 25
            base_chance -= access_reduction
            
            # Apply detection resistance
            base_chance -= player.stats.detection_resistance
            
            # Check if enemy type is bypassed by access level
            if self._enemy_bypassed_by_access(enemy, player.stats.access_level):
                base_chance = 0
        else:
            base_chance = 0
        
        return max(0, min(100, base_chance))
    
    def _enemy_bypassed_by_access(self, enemy: Enemy, access_level: int) -> bool:
        """Check if enemy is bypassed by player's access level."""
        bypassed_enemies = {
            1: ["ping_scanner", "spam_bot", "log_process"],
            2: ["ping_scanner", "spam_bot", "log_process", 
                "firewall_daemon", "ids_monitor"]
        }
        return enemy.name in bypassed_enemies.get(access_level, [])
    
    def increase_detection(self, amount: int) -> None:
        """Increase global detection level."""
        self.detection_level = min(self.max_detection, 
                                  self.detection_level + amount)
    
    def decrease_detection(self, amount: int) -> None:
        """Decrease global detection level."""
        self.detection_level = max(0, self.detection_level - amount)
    
    def should_spawn_admin_avatar(self) -> bool:
        """Check if Admin Avatar should spawn."""
        return self.detection_level >= 91

# ============================================================================
# EXPLOIT SYSTEM
# ============================================================================

class ExploitType(Enum):
    STEALTH = "stealth"
    COMBAT = "combat"
    UTILITY = "utility"

@dataclass
class ExploitEffect:
    """Represents an exploit's effect."""
    effect_type: str
    value: Any
    duration: Optional[int] = None
    target: Optional[str] = None

class Exploit:
    """Represents a usable exploit/ability."""
    
    def __init__(self, 
                 exploit_id: str,
                 name: str,
                 exploit_type: ExploitType,
                 ram_cost: int,
                 heat_generated: int,
                 effects: List[ExploitEffect],
                 range_value: int = 1):
        self.exploit_id = exploit_id
        self.name = name
        self.exploit_type = exploit_type
        self.ram_cost = ram_cost
        self.heat_generated = heat_generated
        self.effects = effects
        self.range_value = range_value
        self.cooldown = 0
    
    def can_use(self, player: Player) -> bool:
        """Check if exploit can be used."""
        return (self.cooldown <= 0 and 
                player.stats.used_ram >= self.ram_cost and
                player.stats.current_heat + self.heat_generated <= player.stats.heat_capacity)
    
    def use(self, player: Player, target_pos: Optional[Position] = None) -> bool:
        """Use the exploit. Returns True if successful."""
        if not self.can_use(player):
            return False
        
        player.add_heat(self.heat_generated)
        self._apply_effects(player, target_pos)
        return True
    
    def _apply_effects(self, player: Player, target_pos: Optional[Position]) -> None:
        """Apply exploit effects."""
        for effect in self.effects:
            # Implementation depends on effect type
            pass

# ============================================================================
# INVENTORY SYSTEM
# ============================================================================

class ItemType(Enum):
    DATA_PATCH = "data_patch"
    RUNTIME_SCRIPT = "runtime_script"
    MEMORY_MODULE = "memory_module"
    COOLING_UNIT = "cooling_unit"
    ADMIN_CREDENTIALS = "admin_credentials"

class Item:
    """Represents an inventory item."""
    
    def __init__(self, 
                 item_id: str,
                 name: str,
                 item_type: ItemType,
                 effect: Optional[ExploitEffect] = None,
                 identified: bool = False):
        self.item_id = item_id
        self.name = name
        self.item_type = item_type
        self.effect = effect
        self.identified = identified
        self.stack_size = 1
    
    def use(self, player: Player) -> bool:
        """Use the item. Returns True if consumed."""
        if self.effect:
            # Apply item effect to player
            return True
        return False

class Inventory:
    """Player inventory management."""
    
    def __init__(self):
        self.items: Dict[str, Tuple[Item, int]] = {}  # item_id -> (item, count)
        self.max_stacks = 20
    
    def add_item(self, item: Item, count: int = 1) -> bool:
        """Add item to inventory. Returns True if successful."""
        if item.item_id in self.items:
            current_item, current_count = self.items[item.item_id]
            self.items[item.item_id] = (current_item, current_count + count)
        else:
            if len(self.items) >= self.max_stacks:
                return False
            self.items[item.item_id] = (item, count)
        return True
    
    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """Remove item from inventory. Returns True if successful."""
        if item_id not in self.items:
            return False
        
        current_item, current_count = self.items[item_id]
        if current_count <= count:
            del self.items[item_id]
        else:
            self.items[item_id] = (current_item, current_count - count)
        return True

# ============================================================================
# MAP SYSTEM
# ============================================================================

class TileType(Enum):
    VOID = "void"
    FLOOR = "floor"
    WALL = "wall"
    DOOR = "door"
    DATA_CLUSTER = "data_cluster"
    PROCESSING_CORE = "processing_core"
    NETWORK_NODE = "network_node"

@dataclass
class Tile:
    """Represents a map tile."""
    tile_type: TileType
    blocks_movement: bool = False
    blocks_vision: bool = False
    symbol: str = "."
    color: Tuple[int, int, int] = (255, 255, 255)

class GameMap:
    """Represents the game map."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles: List[List[Tile]] = []
        self.entities: List[Entity] = []
        self.enemies: List[Enemy] = []
        self.items: List[Item] = []
        self._init_tiles()
    
    def _init_tiles(self) -> None:
        """Initialize map with void tiles."""
        self.tiles = [[Tile(TileType.VOID, True, True, "#", (100, 100, 100))
                      for _ in range(self.height)]
                     for _ in range(self.width)]
    
    def in_bounds(self, position: Position) -> bool:
        """Check if position is within map bounds."""
        return (0 <= position.x < self.width and 
                0 <= position.y < self.height)
    
    def is_blocked(self, position: Position) -> bool:
        """Check if position blocks movement."""
        if not self.in_bounds(position):
            return True
        
        if self.tiles[position.x][position.y].blocks_movement:
            return True
        
        for entity in self.entities:
            if (entity.position == position and 
                entity.blocks_movement):
                return True
        
        return False
    
    def blocks_vision(self, position: Position) -> bool:
        """Check if position blocks vision."""
        if not self.in_bounds(position):
            return True
        
        return self.tiles[position.x][position.y].blocks_vision
    
    def get_entity_at(self, position: Position) -> Optional[Entity]:
        """Get entity at given position."""
        for entity in self.entities:
            if entity.position == position:
                return entity
        return None

# ============================================================================
# GAME ENGINE
# ============================================================================

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    INVENTORY = "inventory"
    TUTORIAL = "tutorial"
    GAME_OVER = "game_over"

class GameEngine:
    """Main game engine."""
    
    def __init__(self):
        self.state = GameState.MENU
        self.current_map: Optional[GameMap] = None
        self.player: Optional[Player] = None
        self.stealth_system = StealthSystem()
        self.turn_count = 0
        self.network_level = 1
    
    def new_game(self, player_class: PlayerClass) -> None:
        """Start a new game."""
        self.player = Player(player_class, Position(0, 0))
        self.generate_network(1)
        self.state = GameState.PLAYING
    
    def generate_network(self, level: int) -> None:
        """Generate a new network level."""
        # Implementation would use NetworkGenerator
        self.current_map = GameMap(50, 50)
        self.network_level = level
    
    def process_turn(self) -> None:
        """Process one game turn."""
        if self.state != GameState.PLAYING:
            return
        
        # Update enemy AI
        for enemy in self.current_map.enemies:
            enemy.update_ai(self.player, self.current_map)
        
        # Update stealth system
        self.stealth_system.increase_detection(1)  # Passive increase
        
        # Check for Admin Avatar spawn
        if self.stealth_system.should_spawn_admin_avatar():
            self._spawn_admin_avatar()
        
        self.turn_count += 1
    
    def _spawn_admin_avatar(self) -> None:
        """Spawn the Admin Avatar boss."""
        # Implementation would create and place Admin Avatar
        pass

# ============================================================================
# DATA MANAGEMENT
# ============================================================================

class DataManager:
    """Manages loading and validation of JSON data files."""
    
    def __init__(self):
        self.exploits_data: Dict = {}
        self.enemies_data: Dict = {}
        self.items_data: Dict = {}
        self.classes_data: Dict = {}
        self.networks_data: Dict = {}
        self.balance_data: Dict = {}
    
    def load_all_data(self) -> None:
        """Load all JSON data files."""
        self.exploits_data = self._load_json("data/exploits.json")
        self.enemies_data = self._load_json("data/enemies.json")
        self.items_data = self._load_json("data/items.json")
        self.classes_data = self._load_json("data/classes.json")
        self.networks_data = self._load_json("data/networks.json")
        self.balance_data = self._load_json("data/balance.json")
    
    def _load_json(self, filename: str) -> Dict:
        """Load and validate JSON file."""
        import json
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {filename} not found")
            return {}
    
    def create_exploit(self, exploit_id: str) -> Optional[Exploit]:
        """Create exploit instance from data."""
        # Implementation would parse JSON and create Exploit object
        pass
    
    def create_enemy(self, enemy_id: str, position: Position) -> Optional[Enemy]:
        """Create enemy instance from data."""
        # Implementation would parse JSON and create Enemy object
        pass

# ============================================================================
# SAVE SYSTEM
# ============================================================================

@dataclass
class SaveData:
    """Represents saved game data."""
    player_class: PlayerClass
    network_level: int
    turn_count: int
    detection_level: int
    player_stats: PlayerStats
    player_position: Position
    loaded_exploits: Dict[int, str]  # slot -> exploit_id
    inventory_items: Dict[str, int]  # item_id -> count

class SaveSystem:
    """Manages game save/load functionality."""
    
    def save_game(self, engine: GameEngine, filename: str