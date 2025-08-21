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
    
    def save_game(self, engine: GameEngine, filename: str) -> bool:
        """Save current game state to file."""
        if not engine.player or not engine.current_map:
            return False
        
        save_data = SaveData(
            player_class=engine.player.player_class,
            network_level=engine.network_level,
            turn_count=engine.turn_count,
            detection_level=engine.stealth_system.detection_level,
            player_stats=engine.player.stats,
            player_position=engine.player.position,
            loaded_exploits={slot: exploit.exploit_id 
                           for slot, exploit in engine.player.loaded_exploits.items()},
            inventory_items={item_id: count 
                           for item_id, (item, count) in engine.player.inventory.items.items()}
        )
        
        try:
            import pickle
            with open(filename, 'wb') as f:
                pickle.dump(save_data, f)
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False
    
    def load_game(self, filename: str) -> Optional[SaveData]:
        """Load game state from file."""
        try:
            import pickle
            with open(filename, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Load failed: {e}")
            return None

# ============================================================================
# ACHIEVEMENT SYSTEM
# ============================================================================

class AchievementType(Enum):
    KILL_COUNT = "kill_count"
    STEALTH_RUN = "stealth_run"
    COLLECTION = "collection"
    SURVIVAL = "survival"
    COMPLETION = "completion"

@dataclass
class Achievement:
    """Represents an unlockable achievement."""
    achievement_id: str
    name: str
    description: str
    achievement_type: AchievementType
    target_value: int
    current_progress: int = 0
    unlocked: bool = False
    unlocks_class: Optional[PlayerClass] = None

class AchievementSystem:
    """Manages player achievements and class unlocks."""
    
    def __init__(self):
        self.achievements: Dict[str, Achievement] = {}
        self.unlocked_classes: set[PlayerClass] = {PlayerClass.SCRIPT_KIDDIE}
        self._init_achievements()
    
    def _init_achievements(self) -> None:
        """Initialize achievement definitions."""
        self.achievements = {
            "stealth_master": Achievement(
                "stealth_master",
                "Stealth Master",
                "Complete Network 3 without being spotted once",
                AchievementType.STEALTH_RUN,
                1,
                unlocks_class=PlayerClass.GHOST_PROTOCOL
            ),
            "combat_veteran": Achievement(
                "combat_veteran",
                "Combat Veteran", 
                "Kill 100 enemies across all runs",
                AchievementType.KILL_COUNT,
                100,
                unlocks_class=PlayerClass.BATTLE_HACKER
            ),
            "data_collector": Achievement(
                "data_collector",
                "Data Collector",
                "Collect 50 different consumables across runs",
                AchievementType.COLLECTION,
                50,
                unlocks_class=PlayerClass.DATA_ARCHAEOLOGIST
            )
        }
    
    def update_progress(self, achievement_id: str, amount: int = 1) -> bool:
        """Update achievement progress. Returns True if newly unlocked."""
        if achievement_id not in self.achievements:
            return False
        
        achievement = self.achievements[achievement_id]
        if achievement.unlocked:
            return False
        
        achievement.current_progress += amount
        
        if achievement.current_progress >= achievement.target_value:
            achievement.unlocked = True
            if achievement.unlocks_class:
                self.unlocked_classes.add(achievement.unlocks_class)
            return True
        
        return False
    
    def is_class_unlocked(self, player_class: PlayerClass) -> bool:
        """Check if player class is unlocked."""
        return player_class in self.unlocked_classes

# ============================================================================
# RENDERING SYSTEM
# ============================================================================

class RenderMode(Enum):
    ASCII = "ascii"
    GRAPHICS = "graphics" 
    HYBRID = "hybrid"

class Renderer:
    """Handles game rendering in multiple modes."""
    
    def __init__(self, console: tcod.Console):
        self.console = console
        self.render_mode = RenderMode.ASCII
        self.tileset: Optional[tcod.tileset.Tileset] = None
        self.sprite_cache: Dict[str, Any] = {}
    
    def set_render_mode(self, mode: RenderMode) -> bool:
        """Change rendering mode. Returns True if successful."""
        try:
            if mode == RenderMode.GRAPHICS and not self.tileset:
                self._load_tileset()
            self.render_mode = mode
            return True
        except Exception as e:
            print(f"Failed to set render mode: {e}")
            return False
    
    def _load_tileset(self) -> None:
        """Load sprite tileset for graphics mode."""
        self.tileset = tcod.tileset.load_tilesheet(
            "assets/sprites/main_tileset.png",
            32, 32,  # tile width, height
            tcod.tileset.CHARMAP_CP437
        )
    
    def render_map(self, game_map: GameMap, player: Player) -> None:
        """Render the game map."""
        for x in range(game_map.width):
            for y in range(game_map.height):
                position = Position(x, y)
                
                if player.can_see(position):
                    tile = game_map.tiles[x][y]
                    if self.render_mode == RenderMode.ASCII:
                        self.console.print(x, y, tile.symbol, fg=tile.color)
                    else:
                        # Graphics mode rendering
                        sprite_id = self._get_sprite_id(tile.tile_type)
                        self._render_sprite(x, y, sprite_id)
                else:
                    # Fog of war
                    self.console.print(x, y, " ", fg=(100, 100, 100))
    
    def render_entities(self, entities: List[Entity], player: Player) -> None:
        """Render game entities."""
        for entity in entities:
            if player.can_see(entity.position):
                if self.render_mode == RenderMode.ASCII:
                    self.console.print(
                        entity.position.x, 
                        entity.position.y,
                        entity.symbol,
                        fg=entity.color
                    )
                else:
                    sprite_id = self._get_entity_sprite_id(entity)
                    self._render_sprite(
                        entity.position.x,
                        entity.position.y, 
                        sprite_id
                    )
    
    def render_ui(self, player: Player, stealth_system: StealthSystem) -> None:
        """Render user interface elements."""
        # Stats bar
        self._render_stats_bar(player, stealth_system)
        
        # Chat log
        self._render_chat_log()
        
        # Minimap
        self._render_minimap(player)
    
    def _render_stats_bar(self, player: Player, stealth_system: StealthSystem) -> None:
        """Render top status bar."""
        stats_text = (f"HP: {player.stats.current_hp}/{player.stats.max_hp} "
                     f"CPU: {player.stats.current_cpu} "
                     f"HEAT: {player.stats.current_heat}°C "
                     f"DET: {stealth_system.detection_level}% "
                     f"ACCESS: L{player.stats.access_level}")
        
        self.console.print(0, 0, stats_text, fg=(255, 255, 255))
    
    def _render_chat_log(self) -> None:
        """Render message log."""
        # Implementation would show recent game messages
        pass
    
    def _render_minimap(self, player: Player) -> None:
        """Render minimap in corner."""
        # Implementation would show small overview map
        pass
    
    def _get_sprite_id(self, tile_type: TileType) -> int:
        """Get sprite ID for tile type."""
        sprite_map = {
            TileType.FLOOR: 0,
            TileType.WALL: 1,
            TileType.DOOR: 2,
            TileType.DATA_CLUSTER: 3,
            TileType.PROCESSING_CORE: 4,
            TileType.NETWORK_NODE: 5
        }
        return sprite_map.get(tile_type, 0)
    
    def _get_entity_sprite_id(self, entity: Entity) -> int:
        """Get sprite ID for entity."""
        if entity.entity_type == EntityType.PLAYER:
            return 16  # Player sprites start at row 1
        elif entity.entity_type == EntityType.ENEMY:
            return 32 + hash(entity.entity_id) % 16  # Enemy sprites
        return 0
    
    def _render_sprite(self, x: int, y: int, sprite_id: int) -> None:
        """Render sprite at position."""
        # Implementation would render sprite using tileset
        pass

# ============================================================================
# INPUT HANDLING
# ============================================================================

class InputAction(Enum):
    MOVE_NORTH = "move_north"
    MOVE_SOUTH = "move_south"
    MOVE_EAST = "move_east"
    MOVE_WEST = "move_west"
    MOVE_NORTHEAST = "move_northeast"
    MOVE_NORTHWEST = "move_northwest"
    MOVE_SOUTHEAST = "move_southeast"
    MOVE_SOUTHWEST = "move_southwest"
    WAIT = "wait"
    USE_EXPLOIT_1 = "use_exploit_1"
    USE_EXPLOIT_2 = "use_exploit_2"
    USE_EXPLOIT_3 = "use_exploit_3"
    USE_EXPLOIT_4 = "use_exploit_4"
    USE_EXPLOIT_5 = "use_exploit_5"
    USE_EXPLOIT_6 = "use_exploit_6"
    USE_EXPLOIT_7 = "use_exploit_7"
    USE_EXPLOIT_8 = "use_exploit_8"
    USE_EXPLOIT_9 = "use_exploit_9"
    OPEN_INVENTORY = "open_inventory"
    TOGGLE_PATROL_ROUTES = "toggle_patrol_routes"
    RELOAD_EXPLOITS = "reload_exploits"
    ESCAPE = "escape"

class InputHandler:
    """Handles player input and key mapping."""
    
    def __init__(self):
        self.key_bindings: Dict[int, InputAction] = {}
        self._init_default_bindings()
    
    def _init_default_bindings(self) -> None:
        """Set up default key bindings."""
        self.key_bindings = {
            tcod.event.K_UP: InputAction.MOVE_NORTH,
            tcod.event.K_DOWN: InputAction.MOVE_SOUTH,
            tcod.event.K_LEFT: InputAction.MOVE_WEST,
            tcod.event.K_RIGHT: InputAction.MOVE_EAST,
            tcod.event.K_w: InputAction.MOVE_NORTH,
            tcod.event.K_s: InputAction.MOVE_SOUTH,
            tcod.event.K_a: InputAction.MOVE_WEST,
            tcod.event.K_d: InputAction.MOVE_EAST,
            tcod.event.K_SPACE: InputAction.WAIT,
            tcod.event.K_1: InputAction.USE_EXPLOIT_1,
            tcod.event.K_2: InputAction.USE_EXPLOIT_2,
            tcod.event.K_3: InputAction.USE_EXPLOIT_3,
            tcod.event.K_4: InputAction.USE_EXPLOIT_4,
            tcod.event.K_5: InputAction.USE_EXPLOIT_5,
            tcod.event.K_6: InputAction.USE_EXPLOIT_6,
            tcod.event.K_7: InputAction.USE_EXPLOIT_7,
            tcod.event.K_8: InputAction.USE_EXPLOIT_8,
            tcod.event.K_9: InputAction.USE_EXPLOIT_9,
            tcod.event.K_i: InputAction.OPEN_INVENTORY,
            tcod.event.K_TAB: InputAction.TOGGLE_PATROL_ROUTES,
            tcod.event.K_r: InputAction.RELOAD_EXPLOITS,
            tcod.event.K_ESCAPE: InputAction.ESCAPE
        }
    
    def handle_event(self, event: tcod.event.Event) -> Optional[InputAction]:
        """Process input event and return action."""
        if isinstance(event, tcod.event.KeyDown):
            return self.key_bindings.get(event.sym)
        return None
    
    def remap_key(self, key: int, action: InputAction) -> None:
        """Remap key to different action."""
        self.key_bindings[key] = action

# ============================================================================
# LEVEL GENERATION
# ============================================================================

@dataclass
class Room:
    """Represents a generated room."""
    x: int
    y: int
    width: int
    height: int
    
    @property
    def center(self) -> Position:
        return Position(self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        return self.width * self.height
    
    def intersects(self, other: "Room") -> bool:
        """Check if this room intersects with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)

class NetworkGenerator:
    """Generates network levels."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.random = tcod.random.Random()
    
    def generate_network(self, level: int) -> GameMap:
        """Generate a complete network level."""
        network_config = self.data_manager.networks_data.get(f"network_{level}_dmz", {})
        
        width, height = network_config.get("size", [50, 50])
        game_map = GameMap(width, height)
        
        # Generate rooms
        rooms = self._generate_rooms(game_map, network_config)
        
        # Connect rooms with corridors
        self._connect_rooms(game_map, rooms)
        
        # Add obstacles
        self._add_obstacles(game_map, rooms, network_config)
        
        # Place enemies
        self._place_enemies(game_map, rooms, network_config)
        
        # Place loot
        self._place_loot(game_map, rooms, network_config)
        
        # Set start and exit positions
        self._set_start_exit(game_map, rooms)
        
        return game_map
    
    def _generate_rooms(self, game_map: GameMap, config: Dict) -> List[Room]:
        """Generate rooms for the network."""
        min_rooms = config.get("room_generation", {}).get("min_rooms", 6)
        max_rooms = config.get("room_generation", {}).get("max_rooms", 15)
        room_count = self.random.randint(min_rooms, max_rooms)
        
        rooms = []
        for _ in range(room_count * 2):  # Try more times than needed
            if len(rooms) >= room_count:
                break
            
            # Random room dimensions
            width = self.random.randint(6, 12)
            height = self.random.randint(6, 12)
            x = self.random.randint(1, game_map.width - width - 1)
            y = self.random.randint(1, game_map.height - height - 1)
            
            new_room = Room(x, y, width, height)
            
            # Check for intersections
            if not any(new_room.intersects(room) for room in rooms):
                self._carve_room(game_map, new_room)
                rooms.append(new_room)
        
        return rooms
    
    def _carve_room(self, game_map: GameMap, room: Room) -> None:
        """Carve out a room in the map."""
        for x in range(room.x, room.x + room.width):
            for y in range(room.y, room.y + room.height):
                if (x == room.x or x == room.x + room.width - 1 or
                    y == room.y or y == room.y + room.height - 1):
                    # Walls
                    game_map.tiles[x][y] = Tile(TileType.WALL, True, True, "#")
                else:
                    # Floor
                    game_map.tiles[x][y] = Tile(TileType.FLOOR, False, False, ".")
    
    def _connect_rooms(self, game_map: GameMap, rooms: List[Room]) -> None:
        """Connect rooms with corridors."""
        for i in range(1, len(rooms)):
            self._create_corridor(game_map, rooms[i-1].center, rooms[i].center)
        
        # Add some extra connections for loops
        extra_connections = min(3, len(rooms) // 3)
        for _ in range(extra_connections):
            room1 = self.random.choice(rooms)
            room2 = self.random.choice(rooms)
            if room1 != room2:
                self._create_corridor(game_map, room1.center, room2.center)
    
    def _create_corridor(self, game_map: GameMap, start: Position, end: Position) -> None:
        """Create L-shaped corridor between two points."""
        # Horizontal first, then vertical
        current = Position(start.x, start.y)
        
        # Horizontal segment
        while current.x != end.x:
            game_map.tiles[current.x][current.y] = Tile(TileType.FLOOR, False, False, ".")
            current.x += 1 if end.x > current.x else -1
        
        # Vertical segment
        while current.y != end.y:
            game_map.tiles[current.x][current.y] = Tile(TileType.FLOOR, False, False, ".")
            current.y += 1 if end.y > current.y else -1
        
        # Final tile
        game_map.tiles[current.x][current.y] = Tile(TileType.FLOOR, False, False, ".")
    
    def _add_obstacles(self, game_map: GameMap, rooms: List[Room], config: Dict) -> None:
        """Add network obstacles to rooms."""
        obstacle_coverage = config.get("obstacle_coverage", 30) / 100.0
        
        for room in rooms:
            floor_tiles = []
            for x in range(room.x + 1, room.x + room.width - 1):
                for y in range(room.y + 1, room.y + room.height - 1):
                    if game_map.tiles[x][y].tile_type == TileType.FLOOR:
                        floor_tiles.append(Position(x, y))
            
            obstacle_count = int(len(floor_tiles) * obstacle_coverage)
            for _ in range(obstacle_count):
                if floor_tiles:
                    pos = self.random.choice(floor_tiles)
                    floor_tiles.remove(pos)
                    
                    # Random obstacle type
                    obstacle_types = [TileType.DATA_CLUSTER, TileType.PROCESSING_CORE, TileType.NETWORK_NODE]
                    obstacle_type = self.random.choice(obstacle_types)
                    
                    game_map.tiles[pos.x][pos.y] = Tile(
                        obstacle_type, True, True, 
                        "█" if obstacle_type == TileType.DATA_CLUSTER else "▓"
                    )
    
    def _place_enemies(self, game_map: GameMap, rooms: List[Room], config: Dict) -> None:
        """Place enemies in rooms."""
        enemy_types = config.get("enemy_types", ["ping_scanner", "spam_bot"])
        min_enemies, max_enemies = config.get("enemy_count", [8, 12])
        enemy_count = self.random.randint(min_enemies, max_enemies)
        
        for _ in range(enemy_count):
            if len(rooms) > 1:  # Don't put enemies in first room (player start)
                room = self.random.choice(rooms[1:])
                
                # Find valid position in room
                for _ in range(10):  # Try up to 10 times
                    x = self.random.randint(room.x + 1, room.x + room.width - 2)
                    y = self.random.randint(room.y + 1, room.y + room.height - 2)
                    pos = Position(x, y)
                    
                    if (game_map.tiles[x][y].tile_type == TileType.FLOOR and
                        not game_map.get_entity_at(pos)):
                        
                        enemy_type = self.random.choice(enemy_types)
                        enemy = self.data_manager.create_enemy(enemy_type, pos)
                        if enemy:
                            game_map.enemies.append(enemy)
                            game_map.entities.append(enemy)
                        break
    
    def _place_loot(self, game_map: GameMap, rooms: List[Room], config: Dict) -> None:
        """Place loot items in rooms."""
        # Implementation would place items based on loot tables
        pass
    
    def _set_start_exit(self, game_map: GameMap, rooms: List[Room]) -> None:
        """Set player start and exit positions."""
        if rooms:
            # Player starts in first room
            start_room = rooms[0]
            # Exit in last room
            exit_room = rooms[-1]
            
            # Place exit marker
            exit_pos = exit_room.center
            game_map.tiles[exit_pos.x][exit_pos.y] = Tile(
                TileType.FLOOR, False, False, ">", (0, 255, 0)
            )

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_game_setup():
    """Example of setting up the game engine."""
    
    # Initialize core systems
    data_manager = DataManager()
    data_manager.load_all_data()
    
    achievement_system = AchievementSystem()
    save_system = SaveSystem()
    
    # Create game engine
    engine = GameEngine()
    
    # Start new game
    engine.new_game(PlayerClass.SCRIPT_KIDDIE)
    
    # Main game loop would go here
    while True:
        # Handle input
        # Process turn
        # Render
        # Check win/lose conditions
        pass

def example_data_usage():
    """Example of using the data management system."""
    
    data_manager = DataManager()
    data_manager.load_all_data()
    
    # Create exploit from data
    buffer_overflow = data_manager.create_exploit("buffer_overflow")
    
    # Create enemy from data
    scanner = data_manager.create_enemy("ping_scanner", Position(10, 10))
    
    # Use exploit
    player = Player(PlayerClass.SCRIPT_KIDDIE, Position(5, 5))
    if buffer_overflow and buffer_overflow.can_use(player):
        buffer_overflow.use(player, Position(10, 10))

def example_stealth_check():
    """Example of stealth detection calculation."""
    
    player = Player(PlayerClass.GHOST_PROTOCOL, Position(5, 5))
    enemy = Enemy("scanner_1", Position(8, 8), "p", "Ping Scanner", 
                  20, 5, 3, PatrolRoute(PatrolType.LINEAR, []))
    
    stealth_system = StealthSystem()
    
    # Calculate detection chance
    detection_chance = stealth_system.calculate_detection_chance(player, enemy)
    
    print(f"Detection chance: {detection_chance}%")

if __name__ == "__main__":
    example_game_setup()