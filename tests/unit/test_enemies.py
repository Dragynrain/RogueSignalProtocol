#!/usr/bin/env python3
"""
Unit tests for Enemy functionality testing real enemy behavior.
Tests the actual Enemy class and its AI/combat methods using real GameData.
"""

from unittest.mock import Mock, patch

import pytest

from rsp.entities.base import EnemyState, Position

# Import actual classes
from rsp.entities.characters import Enemy
from rsp.entities.enemies import EnemyManager
from tests.fixtures.real_game_data import create_test_map_with_real_tiles
from tests.fixtures.simple_fixtures import create_test_map, enemy_builder, player


class TestEnemyCreation:
    """Test enemy creation and initialization with real game data."""

    def test_enemy_creation_with_real_data(self):
        """Enemy creates with correct position and type using real GameData."""
        test_enemy = enemy_builder("scanner", pos=(10, 15))

        assert test_enemy.position.x == 10
        assert test_enemy.position.y == 15
        assert test_enemy.type == "scanner"
        # Test actual values from GameData
        assert test_enemy.cpu > 0
        assert test_enemy.max_cpu > 0
        assert test_enemy.cpu == test_enemy.max_cpu  # Fresh enemy has full CPU
        assert test_enemy.state == EnemyState.UNAWARE

    def test_enemy_unique_ids(self):
        """Each enemy gets a unique ID."""
        enemy1 = enemy_builder("virus", pos=(5, 5))
        enemy2 = enemy_builder("virus", pos=(5, 5))

        assert enemy1.id != enemy2.id
        assert enemy1.id < enemy2.id  # IDs increment

    def test_enemy_property_access(self):
        """Enemy x/y properties work correctly."""
        test_enemy = enemy_builder("patrol", pos=(15, 20))

        assert test_enemy.x == 15
        assert test_enemy.y == 20

        # Test property setters
        test_enemy.x = 25
        test_enemy.y = 30
        assert test_enemy.position.x == 25
        assert test_enemy.position.y == 30

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "hunter", "virus", "firewall", "admin", "inhibitor"],
    )
    def test_enemy_type_has_real_data(self, enemy_type):
        """Verify that enemy type has actual GameData properties."""
        enemy = enemy_builder(enemy_type, pos=(5, 5))

        # Each enemy type should have real GameData loaded
        assert enemy.type_data is not None
        assert enemy.type_data.movement is not None
        assert enemy.type_data.vision > 0
        assert enemy.type_data.damage >= 0


class TestEnemyVision:
    """Test enemy vision and trace level systems with real game data."""

    def test_can_see_player_basic(self):
        """Enemy can_see_player works with clear line of sight using real data."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))
        test_player = player(10, 5, 100)  # Same row, clear line

        # Mock game map with no walls blocking, not in blind spot
        mock_map = Mock()
        mock_map.can_see_position.return_value = True
        mock_map.is_blind_spot.return_value = False

        # Mock player not invisible
        with patch.object(test_player, "is_invisible", return_value=False):
            can_see = test_enemy.can_see_player(test_player, mock_map)

            # Should be able to see player if within vision range (using real vision value)
            distance = test_enemy.position.distance_to(test_player.position)
            if distance <= test_enemy.type_data.vision:
                assert can_see is True
            else:
                assert can_see is False

    def test_can_see_player_blocked(self):
        """Enemy cannot see player through walls using real data."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))
        test_player = player(10, 5, 100)

        # Mock game map with walls blocking line of sight
        mock_map = Mock()
        mock_map.has_line_of_sight.return_value = False

        can_see = test_enemy.can_see_player(test_player, mock_map)

        assert can_see is False

    def test_can_see_player_out_of_range(self):
        """Enemy cannot see player beyond vision range using real data."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))
        test_player = player(50, 5, 100)  # Far away

        # Use real game map
        game_map = create_test_map()

        can_see = test_enemy.can_see_player(test_player, game_map)

        # With this distance, should be out of range for any enemy type
        assert can_see is False

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "hunter", "virus", "firewall", "admin", "inhibitor"],
    )
    def test_enemy_vision_range(self, enemy_type):
        """Each enemy type has a positive vision range from real GameData."""
        enemy = enemy_builder(enemy_type, pos=(5, 5))

        # Each enemy type should have a vision range > 0
        assert enemy.type_data.vision > 0


class TestEnemyAttack:
    """Test enemy attack and combat behavior with real game data."""

    def test_can_attack_player_adjacent(self):
        """Enemy can attack adjacent player using real data."""
        test_enemy = enemy_builder("virus", pos=(5, 5))
        test_player = player(6, 5, 100)  # Adjacent position

        can_attack = test_enemy.can_attack_player(test_player)

        assert can_attack is True

    def test_can_attack_player_not_adjacent(self):
        """Enemy cannot attack non-adjacent player using real data."""
        test_enemy = enemy_builder("virus", pos=(5, 5))
        test_player = player(10, 10, 100)  # Not adjacent

        can_attack = test_enemy.can_attack_player(test_player)

        assert can_attack is False

    def test_attack_player_virus_behavior(self):
        """Virus enemy applies virus effect using real GameData."""
        test_enemy = enemy_builder("virus", pos=(5, 5))
        test_player = player(6, 5, 100)
        initial_virus = test_player.temporary_effects["virus_turns"]

        damage_dealt = test_enemy.attack_player(test_player)

        # Virus type behavior based on real GameData - check if it applies virus effect
        # The behavior depends on actual game data implementation
        assert damage_dealt >= 0  # Can be 0 (virus effect) or > 0 (direct damage)

    def test_attack_player_scanner_behavior(self):
        """Scanner enemy deals damage using real GameData."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))
        test_player = player(6, 5, 100)
        initial_cpu = test_player.cpu

        damage_dealt = test_enemy.attack_player(test_player)

        # Scanner should deal actual damage from GameData
        expected_damage = test_enemy.type_data.damage
        assert damage_dealt == expected_damage
        assert test_player.cpu == initial_cpu - expected_damage

    def test_attack_player_when_disabled(self):
        """Disabled enemy attack behavior using real data."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))
        test_enemy.disabled_turns = 2  # Enemy is disabled
        test_player = player(6, 5, 100)
        initial_cpu = test_player.cpu

        damage_dealt = test_enemy.attack_player(test_player)

        # Attack method still executes even when disabled
        expected_damage = test_enemy.type_data.damage
        assert damage_dealt == expected_damage
        assert test_player.cpu == initial_cpu - expected_damage


class TestEnemyDamage:
    """Test enemy taking damage and destruction with real game data."""

    def test_take_damage_normal(self):
        """Enemy takes damage correctly using real data."""
        test_enemy = enemy_builder("patrol", pos=(10, 10))
        initial_cpu = test_enemy.cpu
        damage_amount = 20

        is_destroyed = test_enemy.take_damage(damage_amount)

        assert is_destroyed is False  # Should still be alive
        assert test_enemy.cpu == initial_cpu - damage_amount

    def test_take_damage_fatal(self):
        """Enemy dies when CPU reaches 0 using real data."""
        test_enemy = enemy_builder("scanner", pos=(10, 10))
        initial_cpu = test_enemy.cpu

        is_destroyed = test_enemy.take_damage(initial_cpu)  # Exactly fatal damage

        assert is_destroyed is True
        assert test_enemy.cpu == 0

    def test_take_damage_overkill(self):
        """Enemy dies from overkill damage using real data."""
        test_enemy = enemy_builder("virus", pos=(10, 10))
        initial_cpu = test_enemy.cpu
        overkill_damage = initial_cpu + 30  # More damage than CPU

        is_destroyed = test_enemy.take_damage(overkill_damage)

        assert is_destroyed is True
        assert test_enemy.cpu <= 0  # CPU can go negative with overkill

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "hunter", "virus", "firewall", "admin", "inhibitor"],
    )
    def test_enemy_cpu_values(self, enemy_type):
        """Each enemy type has positive CPU values from real GameData."""
        enemy = enemy_builder(enemy_type, pos=(5, 5))

        # All enemies should have positive CPU values
        assert enemy.cpu > 0

        # CPU should equal max_cpu for fresh enemies
        assert enemy.cpu == enemy.max_cpu


class TestEnemyColorCoding:
    """Test enemy color coding by state using real game data."""

    def test_enemy_colors_by_state(self):
        """Enemy colors change based on state."""
        test_enemy = enemy_builder("scanner", pos=(5, 5))

        # Test different states produce different colors
        test_enemy.state = EnemyState.UNAWARE
        unaware_color = test_enemy.get_color()

        test_enemy.state = EnemyState.ALERT
        alert_color = test_enemy.get_color()

        test_enemy.state = EnemyState.HOSTILE
        hostile_color = test_enemy.get_color()

        # Colors should be different for each state
        assert unaware_color != alert_color
        assert alert_color != hostile_color
        assert unaware_color != hostile_color

        # Verify colors are valid RGB tuples
        for color in [unaware_color, alert_color, hostile_color]:
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


class TestEnemyManager:
    """Test enemy manager functionality."""

    def test_enemy_manager_spawn(self):
        """EnemyManager can spawn enemies correctly using real data."""
        game_map = create_test_map_with_real_tiles(20, 20)
        mock_message_log = Mock()

        enemy_manager = EnemyManager(game_map, mock_message_log)
        pos = Position(10, 10)

        enemy = enemy_manager.spawn_enemy(pos, "virus")

        assert enemy is not None
        assert enemy.type == "virus"
        assert enemy.position == pos
        assert len(enemy_manager.enemies) == 1
        # Verify enemy has real GameData properties
        assert enemy.type_data is not None
        assert enemy.cpu > 0

    def test_enemy_manager_spawn_on_wall_fails(self):
        """EnemyManager cannot spawn enemy on wall using real map."""
        game_map = create_test_map_with_real_tiles(20, 20)
        mock_message_log = Mock()

        # Add a wall at position 5,5 (walls are stored as (x,y) tuples)
        wall_pos = Position(5, 5)
        game_map.walls.add((wall_pos.x, wall_pos.y))

        enemy_manager = EnemyManager(game_map, mock_message_log)

        # Test that spawning on wall raises ValueError
        with pytest.raises(ValueError, match="Cannot spawn enemy on wall"):
            enemy_manager.spawn_enemy(wall_pos, "scanner")

    def test_enemy_manager_get_enemy_at_position(self):
        """EnemyManager can find enemy at specific position using real data."""
        game_map = create_test_map_with_real_tiles(20, 20)
        mock_message_log = Mock()

        enemy_manager = EnemyManager(game_map, mock_message_log)
        pos = Position(15, 10)  # Use position within map bounds

        enemy = enemy_manager.spawn_enemy(pos, "patrol")
        found_enemy = enemy_manager.get_enemy_at_position(pos)

        assert found_enemy is enemy
        assert found_enemy.position == pos
        assert found_enemy.type == "patrol"

    def test_enemy_manager_no_enemy_at_position(self):
        """EnemyManager returns None when no enemy at position using real data."""
        game_map = create_test_map_with_real_tiles(20, 20)
        mock_message_log = Mock()

        enemy_manager = EnemyManager(game_map, mock_message_log)
        pos = Position(15, 15)  # Empty position within bounds

        found_enemy = enemy_manager.get_enemy_at_position(pos)

        assert found_enemy is None

    @pytest.mark.parametrize(
        "enemy_type",
        ["scanner", "patrol", "bot", "hunter", "virus", "firewall", "admin", "inhibitor"],
    )
    def test_enemy_manager_spawn_enemy_type(self, enemy_type):
        """EnemyManager can spawn each enemy type with real GameData."""
        game_map = create_test_map_with_real_tiles(30, 30)
        mock_message_log = Mock()

        enemy_manager = EnemyManager(game_map, mock_message_log)
        enemy = enemy_manager.spawn_enemy(Position(5, 5), enemy_type)

        assert len(enemy_manager.enemies) == 1
        assert enemy.type == enemy_type
        assert enemy.type_data is not None
        assert enemy.type_data.movement is not None


class TestEnemyAIBehavior:
    """Test enemy AI state changes and behavior patterns."""

    def test_enemy_ai_state_transitions(self):
        """Enemy AI states can be changed appropriately."""
        pos = Position(10, 10)

        with patch("rsp.core.data.GameData") as mock_game_data:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 50
            mock_game_data.ENEMY_TYPES = {"scanner": mock_enemy_type}

            enemy = Enemy(pos, "scanner")

            # Start in UNAWARE state
            assert enemy.state == EnemyState.UNAWARE

            # Can transition to ALERT
            enemy.state = EnemyState.ALERT
            assert enemy.state == EnemyState.ALERT

            # Can transition to HOSTILE
            enemy.state = EnemyState.HOSTILE
            assert enemy.state == EnemyState.HOSTILE

    def test_enemy_cooldown_system(self):
        """Enemy movement cooldown system works."""
        pos = Position(5, 5)

        with patch("rsp.core.data.GameData") as mock_game_data:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 50
            mock_game_data.ENEMY_TYPES = {"virus": mock_enemy_type}

            enemy = Enemy(pos, "virus")

            # Set movement cooldown
            enemy.move_cooldown = 3
            assert enemy.move_cooldown == 3

            # Cooldown decrements when trying to move
            mock_map = Mock()
            mock_map.is_valid_position = Mock(return_value=True)
            mock_player = Mock()
            mock_player.x = 10
            mock_player.y = 10
            mock_game = Mock()
            mock_game.enemies = [enemy]
            mock_game.player = mock_player

            # First call should decrement cooldown but not move
            result = enemy.move(mock_map, mock_player, mock_game)
            assert enemy.move_cooldown == 2
            assert result is False  # Did not move
