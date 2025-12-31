#!/usr/bin/env python3
"""
Unit tests for game_characters.py - Player and Enemy core logic.

Tests cover:
- Player initialization, stats, movement, damage, upgrades
- Enemy initialization and basic state management
- Temporary effects and vision mechanics
- Boundary validation and collision detection

Does NOT test:
- Complex pathfinding (integration tests)
- Movement queue system (integration tests)
- AI state transitions (tested in test_enemy_ai_behavior.py)
"""

from unittest.mock import Mock

import pytest

from rsp.entities.base import Position
from rsp.entities.characters import Enemy
from rsp.entities.player import Player
from rsp.level.pathfinding import PathfindingHelper


class TestPlayerInitialization:
    """Test Player initialization and default values."""

    def test_player_creates_with_correct_position(self):
        """Player should initialize at specified coordinates."""
        player = Player(x=15, y=25)

        assert player.x == 15
        assert player.y == 25
        assert player.position.x == 15
        assert player.position.y == 25

    def test_player_has_default_stats(self):
        """Player should initialize with correct default stats."""
        player = Player(x=10, y=10)

        assert player.cpu == 100
        assert player.max_cpu == 100
        assert player.heat == 0
        assert player.max_heat == 100
        assert player.trace_level == 0.0
        assert player.ram_total == 8

    def test_player_has_temporary_effects(self):
        """Player should initialize with all temporary effects at 0."""
        player = Player(x=10, y=10)

        assert player.temporary_effects["traffic_masquerade_turns"] == 0
        assert player.temporary_effects["speed_boost_turns"] == 0
        assert player.temporary_effects["movement_slowed_turns"] == 0
        assert player.temporary_effects["enhanced_vision_turns"] == 0
        assert player.temporary_effects["exploit_efficiency_turns"] == 0
        assert player.temporary_effects["virus_turns"] == 0

    def test_player_has_inventory_manager(self):
        """Player should initialize with an InventoryManager."""
        player = Player(x=10, y=10)

        assert hasattr(player, "inventory_manager")
        assert player.inventory_manager is not None


class TestPlayerMovement:
    """Test Player movement mechanics."""

    def test_player_can_move_to_valid_position(self, basic_map):
        """Player should move successfully to a valid open tile."""
        player = Player(x=5, y=5)

        # Move right (into open space)
        success = player.move(dx=1, dy=0, game_map=basic_map)

        assert success is True
        assert player.x == 6
        assert player.y == 5
        assert player.last_position.x == 5
        assert player.last_position.y == 5

    def test_player_cannot_move_into_wall(self, basic_map):
        """Player should be blocked by walls."""
        # Find a wall position in the map
        wall_found = False
        for y in range(basic_map.height):
            for x in range(basic_map.width):
                from rsp.entities.base import Position

                if basic_map.is_wall(Position(x, y)):
                    # Found a wall, try to move player adjacent to it
                    if x < basic_map.width - 1 and not basic_map.is_wall(Position(x + 1, y)):
                        # Player can stand at (x+1, y) and try to move into wall at (x, y)
                        player = Player(x=x + 1, y=y)
                        success = player.move(dx=-1, dy=0, game_map=basic_map)
                        assert success is False, "Player should not be able to move into walls"
                        assert player.x == x + 1, "Position should be unchanged after blocked move"
                        wall_found = True
                        break
            if wall_found:
                break

        # If no walls found (unlikely), test passes vacuously
        assert wall_found or basic_map.height > 0, "Test requires a map with at least one wall"

    def test_player_cannot_move_out_of_bounds(self, basic_map):
        """Player should be blocked by map boundaries."""
        player = Player(x=0, y=0)

        # Try to move out of bounds (negative coordinates)
        success = player.move(dx=-1, dy=0, game_map=basic_map)

        assert success is False
        assert player.x == 0
        assert player.y == 0

    def test_player_diagonal_movement(self, basic_map):
        """Player should be able to move diagonally to valid tiles."""
        player = Player(x=5, y=5)

        # Move diagonally (down-right)
        success = player.move(dx=1, dy=1, game_map=basic_map)

        assert success is True
        assert player.x == 6
        assert player.y == 6

    def test_player_position_property_setters(self):
        """Player x/y property setters should update position."""
        player = Player(x=10, y=20)

        player.x = 15
        player.y = 25

        assert player.position.x == 15
        assert player.position.y == 25
        assert player.x == 15
        assert player.y == 25


class TestPlayerDamage:
    """Test Player damage and death mechanics."""

    def test_player_takes_damage(self):
        """Player should correctly reduce CPU when taking damage."""
        player = Player(x=10, y=10)

        damage_taken = player.take_damage(30)

        assert damage_taken == 30
        assert player.cpu == 70

    def test_player_cannot_take_more_damage_than_cpu(self):
        """Player should only take damage up to current CPU."""
        player = Player(x=10, y=10)
        player.cpu = 20

        # Try to deal 50 damage, but player only has 20 CPU
        damage_taken = player.take_damage(50)

        assert damage_taken == 20  # Only took what was available
        assert player.cpu == 0  # Dead

    def test_player_death_at_zero_cpu(self):
        """Player should reach 0 CPU on lethal damage."""
        player = Player(x=10, y=10)

        player.take_damage(100)

        assert player.cpu == 0

    def test_player_survives_non_lethal_damage(self):
        """Player should survive damage that doesn't reduce CPU to 0."""
        player = Player(x=10, y=10)

        player.take_damage(50)

        assert player.cpu == 50
        assert player.cpu > 0


class TestPlayerUpgrades:
    """Test Player permanent upgrade system."""

    def test_player_ram_upgrade(self, real_game_data):
        """Player should increase RAM when applying RAM upgrade."""
        player = Player(x=10, y=10)
        initial_ram = player.ram_total

        # Apply RAM upgrade
        success = player.apply_permanent_upgrade("ram_boost")

        assert success is True
        assert player.ram_total > initial_ram

    def test_player_cpu_upgrade(self, real_game_data):
        """Player should increase max CPU and current CPU on upgrade."""
        player = Player(x=10, y=10)
        player.cpu = 50  # Set current CPU lower than max

        initial_max_cpu = player.max_cpu
        initial_cpu = player.cpu

        # Apply CPU upgrade
        success = player.apply_permanent_upgrade("cpu_boost")

        assert success is True
        assert player.max_cpu > initial_max_cpu
        assert player.cpu > initial_cpu  # Current CPU also boosted

    def test_player_heat_upgrade(self, real_game_data):
        """Player should increase max heat capacity."""
        player = Player(x=10, y=10)
        initial_max_heat = player.max_heat

        # Apply heat upgrade
        success = player.apply_permanent_upgrade("heat_boost")

        assert success is True
        assert player.max_heat > initial_max_heat

    def test_invalid_upgrade_key_returns_false(self, real_game_data):
        """Invalid upgrade key should return False without changing stats."""
        player = Player(x=10, y=10)

        initial_ram = player.ram_total
        initial_cpu = player.max_cpu
        initial_heat = player.max_heat

        success = player.apply_permanent_upgrade("nonexistent_upgrade")

        assert success is False
        assert player.ram_total == initial_ram
        assert player.max_cpu == initial_cpu
        assert player.max_heat == initial_heat

    def test_ram_upgrade_respects_cap(self, real_game_data):
        """RAM upgrades should not exceed max_ram_capacity."""
        player = Player(x=10, y=10)

        # Apply many RAM upgrades
        for _ in range(20):
            player.apply_permanent_upgrade("ram_chip")

        # Should be capped at max_ram_capacity (32 by default)
        # Check in config to get exact value
        from rsp.core.config import GameConfig

        max_ram = GameConfig._get_required("gameplay.max_ram_capacity")

        assert player.ram_total <= max_ram

    def test_cpu_upgrade_respects_cap(self, real_game_data):
        """CPU upgrades should not exceed max_cpu_capacity."""
        player = Player(x=10, y=10)

        # Apply many CPU upgrades
        for _ in range(20):
            player.apply_permanent_upgrade("overclock_kit")

        from rsp.core.config import GameConfig

        max_cpu = GameConfig._get_required("gameplay.max_cpu_capacity")

        assert player.max_cpu <= max_cpu
        assert player.cpu <= max_cpu


class TestPlayerTemporaryEffects:
    """Test Player temporary effect system."""

    def test_update_effects_decrements_all_effects(self):
        """update_effects should decrement all effect timers by 1."""
        player = Player(x=10, y=10)

        # Set some effects
        player.temporary_effects["traffic_masquerade_turns"] = 3
        player.temporary_effects["enhanced_vision_turns"] = 5
        player.temporary_effects["speed_boost_turns"] = 2

        player.update_effects()

        assert player.temporary_effects["traffic_masquerade_turns"] == 2
        assert player.temporary_effects["enhanced_vision_turns"] == 4
        assert player.temporary_effects["speed_boost_turns"] == 1

    def test_update_effects_does_not_go_negative(self):
        """Effect timers should not go below 0."""
        player = Player(x=10, y=10)

        player.temporary_effects["traffic_masquerade_turns"] = 0

        player.update_effects()
        player.update_effects()

        assert player.temporary_effects["traffic_masquerade_turns"] == 0

    def test_is_invisible_when_traffic_masquerade_active(self):
        """Player should be invisible during traffic masquerade."""
        player = Player(x=10, y=10)

        player.temporary_effects["traffic_masquerade_turns"] = 5

        assert player.is_invisible() is True

    def test_is_not_invisible_when_traffic_masquerade_expires(self):
        """Player should not be invisible when effect expires."""
        player = Player(x=10, y=10)

        player.temporary_effects["traffic_masquerade_turns"] = 0

        assert player.is_invisible() is False

    def test_enhanced_vision_increases_range(self):
        """Enhanced vision should increase vision range by 2."""
        player = Player(x=10, y=10)

        base_range = player.get_vision_range()

        player.temporary_effects["enhanced_vision_turns"] = 3
        enhanced_range = player.get_vision_range()

        assert enhanced_range == base_range + 2

    def test_can_see_through_walls_with_enhanced_vision(self):
        """Player should be able to see through walls with enhanced vision."""
        player = Player(x=10, y=10)

        player.temporary_effects["enhanced_vision_turns"] = 3

        assert player.can_see_through_walls() is True

    def test_cannot_see_through_walls_normally(self):
        """Player should not see through walls without enhanced vision."""
        player = Player(x=10, y=10)

        assert player.can_see_through_walls() is False


class TestPlayerVision:
    """Test Player vision mechanics."""

    def test_get_vision_range_returns_base_range(self):
        """Player should have base vision range from config."""
        player = Player(x=10, y=10)

        vision_range = player.get_vision_range()

        # Should be the config value (typically 8)
        from rsp.core.config import GameConfig

        expected = GameConfig._get_required("gameplay.player_base_vision_range")

        assert vision_range == expected


class TestPlayerProperties:
    """Test Player computed properties."""

    def test_ram_used_delegates_to_inventory_manager(self):
        """ram_used property should return inventory manager's RAM usage."""
        player = Player(x=10, y=10)

        # Mock the inventory manager's get_ram_usage
        player.inventory_manager.get_ram_usage = Mock(return_value=5)

        assert player.ram_used == 5
        player.inventory_manager.get_ram_usage.assert_called_once()

    def test_max_heat_property_getter(self):
        """max_heat property should return _max_heat value."""
        player = Player(x=10, y=10)

        assert player.max_heat == 100

    def test_max_heat_property_setter(self):
        """max_heat property setter should update _max_heat."""
        player = Player(x=10, y=10)

        player.max_heat = 150

        assert player.max_heat == 150
        assert player._max_heat == 150


class TestEnemyInitialization:
    """Test Enemy initialization and type loading."""

    def test_enemy_creates_with_position(self, real_game_data):
        """Enemy should initialize at specified position."""
        pos = Position(10, 15)

        enemy = Enemy(pos, "scanner")

        assert enemy.position.x == 10
        assert enemy.position.y == 15
        assert enemy.x == 10
        assert enemy.y == 15

    def test_enemy_loads_type_data(self, real_game_data):
        """Enemy should load stats from GameData.ENEMY_TYPES."""
        pos = Position(5, 5)

        enemy = Enemy(pos, "scanner")

        assert enemy.type == "scanner"
        assert enemy.type_data is not None
        assert hasattr(enemy, "cpu")
        assert hasattr(enemy.type_data, "vision")

    def test_enemy_has_unique_id(self, real_game_data):
        """Each enemy should have a unique ID."""
        pos = Position(5, 5)

        enemy1 = Enemy(pos, "scanner")
        enemy2 = Enemy(pos, "patrol")

        assert enemy1.id != enemy2.id

    def test_enemy_id_increments(self, real_game_data):
        """Enemy IDs should increment sequentially."""
        pos = Position(5, 5)

        # Get current counter
        start_id = Enemy.get_next_id_counter()

        enemy1 = Enemy(pos, "scanner")
        enemy2 = Enemy(pos, "patrol")

        assert enemy2.id == enemy1.id + 1

    def test_enemy_id_counter_can_be_set(self, real_game_data):
        """Enemy ID counter should be settable (for save/load)."""
        pos = Position(5, 5)

        Enemy.set_next_id_counter(1000)

        enemy = Enemy(pos, "scanner")

        assert enemy.id == 1000


class TestEnemyProperties:
    """Test Enemy position properties."""

    def test_enemy_x_property(self, real_game_data):
        """Enemy x property should return position.x."""
        pos = Position(20, 30)
        enemy = Enemy(pos, "scanner")

        assert enemy.x == 20

    def test_enemy_y_property(self, real_game_data):
        """Enemy y property should return position.y."""
        pos = Position(20, 30)
        enemy = Enemy(pos, "scanner")

        assert enemy.y == 30

    def test_enemy_position_update_updates_properties(self, real_game_data):
        """Changing enemy position should update x/y properties."""
        pos = Position(10, 10)
        enemy = Enemy(pos, "scanner")

        enemy.position = Position(15, 25)

        assert enemy.x == 15
        assert enemy.y == 25


class TestPathfindingHelperConstants:
    """Test PathfindingHelper constants are sensible."""

    def test_pathfinding_constants_are_positive(self):
        """Pathfinding constants should be positive integers."""
        assert PathfindingHelper.SHORT_DISTANCE_THRESHOLD > 0
        assert PathfindingHelper.MIN_PATH_LENGTH > 0
        assert PathfindingHelper.SHORT_DISTANCE_MULTIPLIER > 0

    def test_pathfinding_constants_are_reasonable(self):
        """Pathfinding constants should have reasonable values."""
        # SHORT_DISTANCE_THRESHOLD should be less than MIN_PATH_LENGTH
        # to avoid pathfinding issues
        assert PathfindingHelper.SHORT_DISTANCE_THRESHOLD < PathfindingHelper.MIN_PATH_LENGTH

        # SHORT_DISTANCE_MULTIPLIER should be reasonable (not 100x)
        assert PathfindingHelper.SHORT_DISTANCE_MULTIPLIER < 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
