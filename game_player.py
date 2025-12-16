#!/usr/bin/env python3
"""
Player character class managing stats, position, abilities, and inventory.

The Player class coordinates several systems:
- Core stats (CPU health, heat, RAM capacity) with configurable maximums
- Temporary status effects (invisibility, speed, vision enhancements, virus infection)
- Vision system with shadow mechanics and enhanced vision upgrades
- Inventory management (delegated to InventoryManager)
- Permanent upgrades (RAM, CPU, heat capacity)

Movement validation uses centralized PositionValidator to ensure consistency
with enemy movement and other systems.
"""

import logging
from typing import TYPE_CHECKING

from game_config import GameConfig
from game_entities import Position, PositionValidator

if TYPE_CHECKING:
    from game_characters import Enemy


class Player:
    """
    Player character managing stats, position, abilities, and inventory.

    The Player class coordinates several systems:
    - Core stats (CPU health, heat, RAM capacity) with configurable maximums
    - Temporary status effects (invisibility, speed, vision enhancements, virus infection)
    - Vision system with shadow mechanics and enhanced vision upgrades
    - Inventory management (delegated to InventoryManager)
    - Permanent upgrades (RAM, CPU, heat capacity)

    Movement validation uses centralized PositionValidator to ensure consistency
    with enemy movement and other systems.
    """

    def __init__(self, x: int, y: int):
        """Initialize player character at the specified position.

        Args:
            x: Initial X coordinate on the game map
            y: Initial Y coordinate on the game map
        """
        # Position and movement
        self.position = Position(x, y)
        self.last_position = Position(x, y)

        # Core stats
        self.cpu = 100
        self.max_cpu = 100
        self.heat = 0
        self._max_heat = 100  # Initialize max heat capacity
        self.trace_level = 0.0  # Global trace level (float for fractional increments)
        self.ram_total = 8

        # Vision and abilities - load from config for easy balancing
        from game_config import GameConfig

        self.base_vision_range = GameConfig._get_required("gameplay.player_base_vision_range")

        # A10: Vision override from ascension modifiers (None = use base_vision_range)
        self.ascension_vision_override: int | None = None

        # Temporary effects
        self.temporary_effects = {
            "traffic_masquerade_turns": 0,
            "speed_boost_turns": 0,
            "movement_slowed_turns": 0,
            "enhanced_vision_turns": 0,
            "exploit_efficiency_turns": 0,
            "virus_turns": 0,
        }
        self.speed_moves_remaining = 0

        # Inventory system - imported later to avoid circular imports
        # Delayed import to avoid circular dependency
        from game_inventory import InventoryManager

        self.inventory_manager = InventoryManager(self)

    @property
    def x(self) -> int:
        return self.position.x

    @x.setter
    def x(self, value: int) -> None:
        self.position.x = value

    @property
    def y(self) -> int:
        return self.position.y

    @y.setter
    def y(self, value: int) -> None:
        self.position.y = value

    @property
    def ram_used(self) -> int:
        return self.inventory_manager.get_ram_usage()

    @property
    def exploits(self):
        """
        Get equipped exploits as a list of ExploitDefinition objects.

        Returns a 5-element list where each element is either:
        - An ExploitDefinition object from GameData.EXPLOITS (for equipped exploits)
        - None (for empty slots)

        This property enables cycle_exploit_selection() and other systems to access
        exploit data without knowing about InventoryManager internals.
        """
        from game_data import GameData

        # Get equipped exploit keys from inventory manager
        equipped_keys = self.inventory_manager.equipped_exploits
        max_slots = self.inventory_manager.max_equipped_exploits

        # Build list with exploit definitions and empty slots
        exploits_list = []
        for key in equipped_keys:
            if key in GameData.EXPLOITS:
                exploits_list.append(GameData.EXPLOITS[key])
            else:
                exploits_list.append(None)  # Invalid key (shouldn't happen)

        # Pad remaining slots with None
        while len(exploits_list) < max_slots:
            exploits_list.append(None)

        return exploits_list

    def move(self, dx: int, dy: int, game_map) -> bool:
        """
        Move player with boundary and collision checking.

        Uses centralized PositionValidator to ensure movement validation
        is consistent across player and enemy movement systems.

        Args:
            dx: Change in X coordinate (-1, 0, or 1)
            dy: Change in Y coordinate (-1, 0, or 1)
            game_map: GameMap instance for boundary/collision checking

        Returns:
            True if move was successful, False if blocked
        """
        self.last_position = Position(self.x, self.y)

        # Calculate the intended destination (unclamped)
        intended_x = self.x + dx
        intended_y = self.y + dy

        # Create the position and validate it using centralized utilities
        new_position = Position(intended_x, intended_y)

        # Use centralized validation
        if PositionValidator.is_basic_valid_position(new_position, game_map):
            self.position = new_position
            return True

        # Log boundary violations for debugging
        if not PositionValidator.is_within_bounds(new_position, game_map.width, game_map.height):
            logging.warning(
                f"Player movement out of bounds: intended=({intended_x}, {intended_y}), map_bounds=({game_map.width}, {game_map.height})"
            )
        else:
            logging.debug(f"Player movement blocked: intended=({intended_x}, {intended_y})")

        return False

    def update_effects(self) -> None:
        """Update temporary effects each turn."""
        for effect in self.temporary_effects:
            self.temporary_effects[effect] = max(0, self.temporary_effects[effect] - 1)

    def is_invisible(self) -> bool:
        """Check if player is effectively invisible."""
        return self.temporary_effects["traffic_masquerade_turns"] > 0

    def get_vision_range(self) -> int:
        """Get current vision range including bonuses.

        A10 ascension modifier can override the base vision range.
        Enhanced vision buff adds +2 on top of the effective base.
        """
        # A10: Use ascension override if set, otherwise use config base
        base_range = (
            self.ascension_vision_override
            if self.ascension_vision_override is not None
            else self.base_vision_range
        )
        if self.temporary_effects["enhanced_vision_turns"] > 0:
            base_range += 2
        return base_range

    def can_see_through_walls(self) -> bool:
        """Check if player can see through walls."""
        return self.temporary_effects["enhanced_vision_turns"] > 0

    def can_see_enemy(self, enemy_target: "Enemy", game_map) -> bool:
        """
        Check if player can see an enemy using vision range and shadow mechanics.

        Vision rules (checked in order):
        1. Adjacent enemies (distance <= 1.5) are always visible
        2. Enhanced vision ignores walls and sees within extended range
        3. Enemies in shadows are only visible when adjacent (shadows block incoming vision)
        4. Standard TCOD FOV check for line-of-sight within vision range

        Note: Shadows block vision TO targets in shadows, but do NOT block vision
        FROM the player if standing in a shadow. This creates tactical asymmetry.

        Args:
            enemy_target: Enemy to check visibility for
            game_map: GameMap instance for shadow/FOV checking

        Returns:
            True if player can see the enemy
        """
        # Use Euclidean for vision range (TCOD FOV uses Euclidean)
        distance = self.position.distance_to(enemy_target.position)

        # Adjacent enemies always visible (use grid distance for gameplay)
        if self.position.grid_distance_to(enemy_target.position) <= 1:
            return True

        # Enhanced vision sees through walls
        vision_range = self.get_vision_range()
        if self.can_see_through_walls():
            return distance <= vision_range

        # Enemies in shadows only visible when adjacent (use grid distance for gameplay)
        if (
            game_map.is_blind_spot(enemy_target.position)
            and self.position.grid_distance_to(enemy_target.position) > 1
        ):
            # Don't log this - it gets called every frame during rendering
            return False

        # Shadows do NOT block vision going OUT - player standing in shadow has normal vision
        # (Shadows only block vision coming in, not vision going out)

        can_see = game_map.can_see_position(self.position, enemy_target.position, vision_range)
        return can_see

    @property
    def max_heat(self) -> int:
        """Get maximum heat capacity."""
        return getattr(self, "_max_heat", 100)  # Default 100 if not set

    @max_heat.setter
    def max_heat(self, value: int) -> None:
        """Set maximum heat capacity."""
        self._max_heat = value

    def apply_permanent_upgrade(self, upgrade_key: str) -> bool:
        """
        Apply a permanent stat upgrade with configurable caps.

        Each upgrade type has a maximum capacity to prevent unlimited scaling:
        - RAM: Capped at max_ram_capacity (default 32)
        - CPU: Capped at max_cpu_capacity (default 200), also boosts current CPU
        - Heat: Capped at 200 to balance heat-based abilities

        Args:
            upgrade_key: Key into GameUpgrades.UPGRADES dict

        Returns:
            True if upgrade was successfully applied, False if key not found
        """
        # Delayed import to avoid circular dependency
        from game_data import GameUpgrades

        if upgrade_key not in GameUpgrades.UPGRADES:
            return False

        upgrade = GameUpgrades.UPGRADES[upgrade_key]

        max_ram = GameConfig._get_required("gameplay.max_ram_capacity")
        max_cpu = GameConfig._get_required("gameplay.max_cpu_capacity")

        if upgrade.stat_type == "ram":
            old_ram = self.ram_total
            self.ram_total = min(max_ram, self.ram_total + upgrade.bonus_amount)
            logging.debug(
                f"Player upgrade '{upgrade_key}': RAM {old_ram} -> {self.ram_total} (cap={max_ram})"
            )
        elif upgrade.stat_type == "cpu":
            old_max_cpu = self.max_cpu
            old_cpu = self.cpu
            self.max_cpu = min(max_cpu, self.max_cpu + upgrade.bonus_amount)
            self.cpu = min(
                self.max_cpu, self.cpu + upgrade.bonus_amount
            )  # Boost current as well but cap at max
            logging.debug(
                f"Player upgrade '{upgrade_key}': max_CPU {old_max_cpu} -> {self.max_cpu}, CPU {old_cpu} -> {self.cpu} (cap={max_cpu})"
            )
        elif upgrade.stat_type == "heat":
            old_max_heat = self.max_heat
            max_cap = GameConfig._get_required("balance.max_heat_capacity")
            self.max_heat = min(max_cap, self.max_heat + upgrade.bonus_amount)
            logging.debug(
                f"Player upgrade '{upgrade_key}': max_heat {old_max_heat} -> {self.max_heat} (cap={max_cap})"
            )

        return True

    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.cpu)
        old_cpu = self.cpu
        self.cpu -= actual_damage
        logging.debug(
            f"Player: took {actual_damage} damage, CPU {old_cpu} -> {self.cpu}/{self.max_cpu}"
        )

        # Track metrics
        from game_metrics import track

        track("damage_taken", amount=actual_damage)

        return actual_damage
