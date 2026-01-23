"""
Fixed level generator for hand-designed levels.

INTEGRATION FLOW:
1. coordinator.py generate_procedural_level() checks config for fixed_layout=true
2. If true, calls FixedLevelGenerator.generate_from_layout() INSTEAD of procedural
3. FixedLevelGenerator populates game_map directly and returns spawn position
4. Coordinator skips all procedural steps (room gen, corridor gen, etc.)
5. Coordinator skips _place_enemies(), _place_code_hacks(), etc. for fixed layouts

This ensures fixed layout content is used without random placement interference.
"""

import logging
import random

from rsp.combat.inventory import CodeHack, ExploitItem
from rsp.core.data import GameData
from rsp.entities.base import Position
from rsp.entities.characters import Enemy
from rsp.level.fixed_levels import PrologueLayoutData


class FixedLevelGenerator:
    """
    Generates levels from fixed ASCII layouts.

    Used for tutorial levels and special hand-designed areas.
    Directly populates GameMap with walls, floors, nodes, and entities.

    ALL REAL GAME MECHANICS - no tutorial-only elements.
    """

    # Character to tile type mapping (ALL REAL GAME ELEMENTS)
    FLOOR_CHARS = {".", "@", ">", "c", "r", "g", "X", "S", "P", "e", "E", "d", "+", "s"}
    ENEMY_CHARS = {"X": "scanner", "S": "scanner", "P": "patrol"}  # X = damaged scanner
    NODE_CHARS = {"c": "cooling", "r": "cpu", "g": "ghost"}
    ITEM_CHARS = {"e": "exploit", "E": "threat_scan", "d": "code_hack"}
    # Special enemy HP overrides (X = damaged scanner with 5 HP for one-shot melee)
    ENEMY_HP_OVERRIDES = {"X": 5}

    def __init__(self, game_map, game_engine=None):
        self.game_map = game_map
        self.game_engine = game_engine  # Needed for code_hack_effects

    def generate_from_layout(
        self, layout_data: PrologueLayoutData, level: int = 0
    ) -> tuple[Position, list[Enemy], PrologueLayoutData]:
        """
        Generate map from fixed layout, populating game_map directly.

        IMPORTANT: This method handles ALL placement - walls, floors, blind spots,
        nodes, items, and enemies. The coordinator MUST NOT run its placement methods.

        Args:
            layout_data: PrologueLayoutData with ASCII layout
            level: Level number (0 for prologue)

        Returns:
            Tuple of (player_spawn_position, list_of_enemies, layout_data)
            The layout_data is returned for access to patrol_routes etc.
        """
        spawn_pos = None
        enemies = []

        # Clear existing map data (walls will be set, everything else cleared)
        self._clear_map_data()

        # First pass: Fill entire map with walls
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                self.game_map.walls.add((x, y))

        # Second pass: Parse layout and carve out floors/features
        for y in range(layout_data.height):
            for x in range(layout_data.width):
                char = layout_data.get_char(x, y)

                # Carve floor tiles
                if char in self.FLOOR_CHARS:
                    self.game_map.walls.discard((x, y))

                # Handle special characters (ALL REAL GAME ELEMENTS)
                if char == "@":
                    spawn_pos = Position(x, y)
                elif char == ">":
                    self.game_map.gateway = Position(x, y)
                elif char == "s":
                    self.game_map.blind_spots.add((x, y))
                elif char in self.NODE_CHARS:
                    self._place_node(x, y, self.NODE_CHARS[char])
                elif char in self.ENEMY_CHARS:
                    enemy = self._create_enemy(
                        x, y, self.ENEMY_CHARS[char], layout_data, layout_char=char
                    )
                    enemies.append(enemy)
                elif char in self.ITEM_CHARS:
                    self._place_item(x, y, self.ITEM_CHARS[char], level)

        if spawn_pos is None:
            logging.error("Fixed level has no player spawn (@)! Finding fallback...")
            spawn_pos = self._find_valid_spawn_fallback()

        # Invalidate caches
        self.game_map.invalidate_transparency_cache()

        # Validate gateway reachability from spawn
        if self.game_map.gateway:
            self._validate_gateway_reachable(spawn_pos)

        logging.info(
            f"Fixed level generated: {layout_data.width}x{layout_data.height}, "
            f"spawn={spawn_pos}, enemies={len(enemies)}, gateway={self.game_map.gateway}"
        )

        return spawn_pos, enemies, layout_data

    def _find_valid_spawn_fallback(self) -> Position:
        """Find a valid walkable spawn position when @ is missing.

        Searches for first walkable tile, prioritizing interior positions.
        """
        # Try common interior positions first
        for pos in [Position(1, 1), Position(2, 2), Position(3, 3)]:
            if self._is_walkable(pos):
                logging.warning(f"Using fallback spawn position: {pos}")
                return pos

        # Search entire map for any walkable position
        for y in range(1, self.game_map.height - 1):
            for x in range(1, self.game_map.width - 1):
                pos = Position(x, y)
                if self._is_walkable(pos):
                    logging.warning(f"Using fallback spawn position: {pos}")
                    return pos

        # Last resort - this should never happen with a valid layout
        logging.error("No walkable spawn position found! Level may be broken.")
        return Position(1, 1)

    def _is_walkable(self, pos: Position) -> bool:
        """Check if position is walkable (not a wall)."""
        return (pos.x, pos.y) not in self.game_map.walls

    def _validate_gateway_reachable(self, spawn: Position) -> bool:
        """Validate that gateway is reachable from spawn using pathfinding.

        Logs a warning if gateway is unreachable - doesn't fail since
        enemies might need to be killed first to open the path.
        """
        import numpy as np
        import tcod

        # Build walkability array
        walkability = np.ones((self.game_map.height, self.game_map.width), dtype=np.int8)
        for wall in self.game_map.walls:
            walkability[wall[1], wall[0]] = 0

        # Try to find path
        graph = tcod.path.SimpleGraph(cost=walkability, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((spawn.y, spawn.x))

        gateway = self.game_map.gateway
        path = pathfinder.path_to((gateway.y, gateway.x)).tolist()

        if len(path) <= 1:
            logging.warning(
                f"PROLOGUE WARNING: Gateway at {gateway} may not be directly reachable "
                f"from spawn at {spawn}. Path requires killing enemies or layout issue."
            )
            return False

        logging.debug(f"Gateway reachability validated: {len(path)} steps from spawn")
        return True

    def _clear_map_data(self):
        """Clear all existing map data before generating."""
        self.game_map.walls.clear()
        self.game_map.blind_spots.clear()
        self.game_map.used_blind_spots.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.ghost_nodes.clear()
        self.game_map.code_hacks.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        self.game_map.explored_tiles.clear()
        self.game_map.gateway = None

    def _place_node(self, x: int, y: int, node_type: str):
        """Place a special node at position."""
        from rsp.level.map import RestoreNode

        if node_type == "cooling":
            self.game_map.cooling_nodes[(x, y)] = RestoreNode(node_type="cooling")
        elif node_type == "cpu":
            self.game_map.cpu_recovery_nodes[(x, y)] = RestoreNode(node_type="cpu")
        elif node_type == "ghost":
            self.game_map.ghost_nodes[(x, y)] = RestoreNode(node_type="ghost")

    def _create_enemy(
        self,
        x: int,
        y: int,
        enemy_type: str,
        layout_data: PrologueLayoutData,
        layout_char: str = None,
    ) -> Enemy:
        """Create enemy with optional tutorial HP overrides.

        Uses REAL enemy types only - scanner, bot, patrol.
        X = Damaged Scanner (5 HP) for melee teaching.

        Args:
            x, y: Position
            enemy_type: The actual enemy type (scanner, bot, patrol)
            layout_data: Layout data with optional overrides
            layout_char: Original character from layout (e.g., 'X' for damaged scanner)
        """
        enemy = Enemy(Position(x, y), enemy_type)

        # Apply HP override from layout character (e.g., X = damaged scanner)
        if layout_char and layout_char in self.ENEMY_HP_OVERRIDES:
            enemy.cpu = self.ENEMY_HP_OVERRIDES[layout_char]
            enemy.max_cpu = self.ENEMY_HP_OVERRIDES[layout_char]
        # Also check layout_data overrides for additional customization
        elif enemy_type in layout_data.enemy_overrides:
            overrides = layout_data.enemy_overrides[enemy_type]
            if "hp" in overrides:
                enemy.cpu = overrides["hp"]
                enemy.max_cpu = overrides["hp"]

        return enemy

    def _place_item(self, x: int, y: int, item_type: str, level: int = 0):
        """Place an item at position."""
        if item_type == "exploit":
            # Prologue: Always place Code Injection (ranged) for Section 4
            # Regular levels: Random exploit from pool
            if level == 0:
                exploit_key = "code_injection"  # Range 5, player can hit across gap
            else:
                exploit_key = random.choice(list(GameData.EXPLOITS.keys()))
            exploit_def = GameData.EXPLOITS[exploit_key]
            self.game_map.exploit_pickups[(x, y)] = ExploitItem(exploit_key, exploit_def)
        elif item_type == "threat_scan":
            # Always place Threat Scan - utility exploit that reveals enemy vision
            exploit_key = "threat_scan"
            exploit_def = GameData.EXPLOITS[exploit_key]
            self.game_map.exploit_pickups[(x, y)] = ExploitItem(exploit_key, exploit_def)
        elif item_type == "code_hack":
            # Create code hack with random color
            if self.game_engine and self.game_engine.code_hack_effects:
                color = random.choice(list(self.game_engine.code_hack_effects.keys()))
                effect, desc = self.game_engine.code_hack_effects[color]
                code = CodeHack(
                    color_name=color,
                    effect=effect,
                    name=f"{color.title()} Code",
                    description=desc,
                )
                self.game_map.code_hacks[(x, y)] = code
