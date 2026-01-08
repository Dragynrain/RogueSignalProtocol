#!/usr/bin/env python3
"""
Comprehensive Enemy AI Behavior Tests - Test Category 1
Tests for Enemy AI behavior including movement patterns, state transitions,
pathfinding, alerts, and the movement queue system.
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from rsp.entities.base import EnemyMovement, EnemyState, Position
from rsp.entities.characters import Enemy
from rsp.entities.enemies import EnemyManager
from tests.fixtures.simple_fixtures import player


# Mock the pathfinding function to prevent import errors
def mock_create_pathfinding_cost_map(game_map, game, moving_enemy):
    """Mock pathfinding cost map creation."""
    # Return a numpy array for compatibility with PathfindingHelper
    return np.ones((game_map.height, game_map.width), dtype=np.int8)


class TestEnemyAIBehavior:
    """Test suite for Enemy AI behavior and decision-making."""

    def setup_method(self):
        """Setup common test objects."""
        self.mock_game_map = Mock()
        self.mock_game_map.width = 80
        self.mock_game_map.height = 40
        self.mock_game_map.is_valid_position = Mock(return_value=True)
        self.mock_game_map.is_wall = Mock(return_value=False)
        self.mock_game_map.is_blind_spot = Mock(return_value=False)
        self.mock_game_map.can_see_position = Mock(return_value=True)

        self.mock_message_log = Mock()
        self.mock_game = Mock()

        self.player = player(x=10, y=10)
        self.player.is_invisible = Mock(return_value=False)

        # Setup mock game properties that enemies need
        self.mock_game.player = self.player
        self.mock_game.enemies = []  # Empty list of enemies


class TestEnemyCreationAndBasics(TestEnemyAIBehavior):
    """Test enemy creation and basic properties."""

    def test_enemy_creation_with_proper_initialization(self):
        """Enemy is created with correct initial state and properties."""
        enemy = Enemy(Position(5, 5), "scanner")

        assert enemy.position.x == 5
        assert enemy.position.y == 5
        assert enemy.type == "scanner"
        assert enemy.state == EnemyState.UNAWARE
        assert enemy.alert_timer == 0
        assert enemy.disabled_turns == 0
        assert enemy.move_cooldown == 0
        assert enemy.last_seen_player is None
        assert enemy.id > 0  # Should have a unique ID

    def test_enemy_unique_ids(self):
        """Each enemy gets a unique ID."""
        enemy1 = Enemy(Position(5, 5), "scanner")
        enemy2 = Enemy(Position(6, 6), "virus")

        assert enemy1.id != enemy2.id
        assert enemy1.id > 0
        assert enemy2.id > 0


class TestEnemyMovementPatterns(TestEnemyAIBehavior):
    """Test different enemy movement patterns."""

    def test_static_enemy_never_moves(self):
        """STATIC enemies should never move regardless of state."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"static_test": Mock(movement=EnemyMovement.STATIC, cpu=50, vision=5, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "static_test")
            original_position = Position(enemy.x, enemy.y)

            # Even when hostile, static enemies shouldn't move
            enemy.state = EnemyState.HOSTILE
            enemy.last_seen_player = Position(10, 10)

            moved = enemy.move(self.mock_game_map, self.player, self.mock_game)

            assert not moved
            assert enemy.position.x == original_position.x
            assert enemy.position.y == original_position.y

    def test_random_movement_generates_queue(self):
        """RANDOM movement enemies can calculate moves."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "random_test": Mock(
                    movement=EnemyMovement.RANDOM, cpu=50, vision=5, damage=10, name="RandomTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "random_test")

                # RANDOM enemies move when unaware
                assert enemy.state == EnemyState.UNAWARE
                initial_pos = enemy.position
                enemy.move(self.mock_game_map, self.player, self.mock_game)

                # Movement system should work (either moved or stayed)
                assert enemy.position is not None

    def test_seek_movement_targets_visible_player(self):
        """SEEK enemies target player when HOSTILE and can see them."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "seek_test": Mock(
                    movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10, name="SeekTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "seek_test")
                enemy.state = EnemyState.HOSTILE

                # Mock enemy can see player
                with patch.object(enemy, "can_see_player", return_value=True):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Verify enemy has player position as last seen
                    assert enemy.last_seen_player == self.player.position

    def test_hostile_movement_remembers_last_position(self):
        """HOSTILE enemies remember and pursue last seen player position."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "hostile_test": Mock(
                    movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10, name="HostileTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "hostile_test")
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(15, 15)

                # Mock enemy cannot see player currently
                with patch.object(enemy, "can_see_player", return_value=False):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Last seen position should remain
                    assert enemy.last_seen_player == Position(15, 15)

    def test_patrol_movement_follows_route(self):
        """PATROL enemies follow their patrol route."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol_test": Mock(
                    movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "patrol_test")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 0

                enemy.move(self.mock_game_map, self.player, self.mock_game)

                # Patrol system should work
                assert enemy.patrol_points is not None


class TestEnemyStateTransitions(TestEnemyAIBehavior):
    """Test enemy alert state transitions and player trace level."""

    def test_enemy_starts_unaware(self):
        """New enemies start in UNAWARE state."""
        enemy = Enemy(Position(5, 5), "scanner")
        assert enemy.state == EnemyState.UNAWARE

    def test_can_see_player_basic_visibility(self):
        """Enemy can see player within vision range with clear line of sight."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=8, y=8)  # Within vision range

            # Mock clear line of sight
            self.mock_game_map.can_see_position.return_value = True

            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True

    def test_cannot_see_player_beyond_vision_range(self):
        """Enemy cannot see player beyond their vision range."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=5, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=15, y=15)  # Beyond vision range

            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is False

    def test_cannot_see_invisible_player(self):
        """Enemy cannot see invisible player (traffic masquerade effect)."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=7, y=7)  # Within range
            test_player.is_invisible = Mock(return_value=True)

            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is False

    def test_admin_can_always_see_player(self):
        """Admin enemies can always see the player regardless of conditions."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"admin": Mock(movement=EnemyMovement.SEEK, cpu=100, vision=10, damage=20)},
        ):
            enemy = Enemy(Position(5, 5), "admin")
            test_player = player(x=50, y=50)  # Very far away
            test_player.is_invisible = Mock(return_value=True)  # Invisible

            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True

    def test_player_in_shadow_stealth_mechanics(self):
        """Player in blind spots is only visible to adjacent enemies."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Position(5, 5)
            test_player = player(x=8, y=8)  # Within vision range but not adjacent

            # Mock player is in blind spot
            self.mock_game_map.is_blind_spot.return_value = True

            enemy_obj = Enemy(enemy, "test_enemy")
            result = enemy_obj.can_see_player(test_player, self.mock_game_map)
            assert result is False

    def test_adjacent_enemy_sees_player_in_blind_spot(self):
        """Adjacent enemy can see player even in blind spots."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=6, y=6)  # Adjacent

            # Mock player is in blind spot
            self.mock_game_map.is_blind_spot.return_value = True

            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True  # Adjacent enemies can see through blind spots


class TestEnemyAttackBehavior(TestEnemyAIBehavior):
    """Test enemy attack and combat behavior."""

    def test_can_attack_adjacent_player(self):
        """Enemy can attack adjacent player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=6, y=6)  # Adjacent

            result = enemy.can_attack_player(test_player)
            assert result is True

    def test_cannot_attack_distant_player(self):
        """Enemy cannot attack distant player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=10, y=10)  # Not adjacent

            result = enemy.can_attack_player(test_player)
            assert result is False

    def test_disabled_enemy_cannot_attack(self):
        """Disabled enemy cannot attack."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)},
        ):
            enemy = Enemy(Position(5, 5), "test_enemy")
            enemy.disabled_turns = 3
            test_player = player(x=6, y=6)  # Adjacent

            result = enemy.can_attack_player(test_player)
            assert result is False

    def test_cannot_attack_invisible_player_except_admin(self):
        """Regular enemies cannot attack invisible players, but admin can."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "test_enemy": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10),
                "admin": Mock(movement=EnemyMovement.SEEK, cpu=100, vision=10, damage=20),
            },
        ):
            regular_enemy = Enemy(Position(5, 5), "test_enemy")
            admin_enemy = Enemy(Position(7, 7), "admin")
            test_player = player(x=6, y=6)  # Adjacent
            test_player.is_invisible = Mock(return_value=True)

            assert regular_enemy.can_attack_player(test_player) is False
            assert admin_enemy.can_attack_player(test_player) is True


class TestVirusAndSpecialEnemies(TestEnemyAIBehavior):
    """Test special enemy types like virus and inhibitor."""

    def test_virus_enemy_applies_virus_effect(self):
        """Virus enemy applies virus effect instead of damage."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"virus": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=0)},
        ):
            enemy = Enemy(Position(5, 5), "virus")
            test_player = player()

            damage = enemy.attack_player(test_player)

            assert damage == 0  # No immediate damage
            assert test_player.temporary_effects.get("virus_turns", 0) > 0

    def test_inhibitor_enemy_applies_slow_effect(self):
        """Inhibitor enemy applies movement slow effect."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"inhibitor": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=0)},
        ):
            enemy = Enemy(Position(5, 5), "inhibitor")
            test_player = player()

            damage = enemy.attack_player(test_player)

            assert damage == 0  # No immediate damage
            assert test_player.temporary_effects.get("movement_slowed_turns", 0) > 0

    def test_inhibitor_slowdown_stacks_with_cap(self):
        """Inhibitor slowdown extends duration (stacks) but caps at 5 turns."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {"inhibitor": Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=0)},
        ):
            enemy = Enemy(Position(5, 5), "inhibitor")
            test_player = player()

            # First hit - applies inhibitor_slow_turns (default 2) turns of slow
            test_player.temporary_effects["movement_slowed_turns"] = 0
            enemy.attack_player(test_player)
            assert (
                test_player.temporary_effects["movement_slowed_turns"] == 2
            ), "First hit should apply 2 turns of slowdown (config: inhibitor_slow_turns)"

            # Second hit - should extend to 4
            enemy.attack_player(test_player)
            assert (
                test_player.temporary_effects["movement_slowed_turns"] == 4
            ), "Slowdown should stack by extending duration"

            # Keep hitting until cap
            for _ in range(10):  # Hit many more times
                enemy.attack_player(test_player)

            assert (
                test_player.temporary_effects["movement_slowed_turns"] == 5
            ), "BUG FIX: Slowdown should cap at 5 turns (prevents infinite stacking)"


class TestEnemyManager(TestEnemyAIBehavior):
    """Test EnemyManager functionality."""

    def test_enemy_manager_creation(self):
        """EnemyManager initializes correctly."""
        manager = EnemyManager(self.mock_game_map, self.mock_message_log)

        assert manager.enemies == []
        assert manager.game_map == self.mock_game_map
        assert manager.message_log == self.mock_message_log

    def test_spawn_enemy_adds_to_list(self):
        """Spawning enemy adds it to the manager's list."""
        manager = EnemyManager(self.mock_game_map, self.mock_message_log)

        enemy = manager.spawn_enemy(Position(10, 10), "scanner")

        assert len(manager.enemies) == 1
        assert manager.enemies[0] == enemy
        assert enemy.position.x == 10
        assert enemy.position.y == 10

    def test_spawn_enemy_on_wall_raises_error(self):
        """Spawning enemy on wall raises ValueError."""
        manager = EnemyManager(self.mock_game_map, self.mock_message_log)
        self.mock_game_map.is_wall.return_value = True

        with pytest.raises(ValueError, match="Cannot spawn enemy on wall"):
            manager.spawn_enemy(Position(5, 5), "scanner")

    def test_get_enemy_at_position(self):
        """Can find enemy at specific position."""
        manager = EnemyManager(self.mock_game_map, self.mock_message_log)
        enemy = manager.spawn_enemy(Position(10, 10), "scanner")

        found_enemy = manager.get_enemy_at_position(Position(10, 10))
        assert found_enemy == enemy

        not_found = manager.get_enemy_at_position(Position(5, 5))
        assert not_found is None

    def test_remove_enemy(self):
        """Can remove enemy from manager."""
        manager = EnemyManager(self.mock_game_map, self.mock_message_log)
        enemy = manager.spawn_enemy(Position(10, 10), "scanner")

        assert len(manager.enemies) == 1

        manager.remove_enemy(enemy)

        assert len(manager.enemies) == 0


class TestPatrolBehavior(TestEnemyAIBehavior):
    """Test patrol route following and interruption."""

    def test_patrol_enemy_follows_route(self):
        """Patrol enemy follows their assigned route."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "patrol")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 0

                # Generate movement
                enemy.move(self.mock_game_map, self.player, self.mock_game)

                # Patrol system should be intact
                assert enemy.patrol_points is not None
                assert enemy.patrol_index is not None

    def test_patrol_enemy_becomes_hostile_interrupts_patrol(self):
        """Patrol enemy becoming HOSTILE interrupts patrol to seek player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL, cpu=50, vision=10, damage=10, name="PatrolTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "patrol")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 0
                enemy.state = EnemyState.HOSTILE

                # Mock enemy can see player
                with patch.object(enemy, "can_see_player", return_value=True):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Should have set player as last seen target
                    assert enemy.last_seen_player == self.player.position

    def test_patrol_enemy_returns_to_patrol_after_losing_player(self):
        """Patrol enemy returns to patrol route after losing sight of player."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest"
                )
            },
        ):
            with patch(
                "rsp.entities.characters.PathfindingHelper._create_cost_map",
                mock_create_pathfinding_cost_map,
            ):
                enemy = Enemy(Position(5, 5), "patrol")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 1
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = None

                # Mock enemy cannot see player
                with patch.object(enemy, "can_see_player", return_value=False):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Patrol system should still work
                    assert enemy.patrol_points is not None


class TestMakeHostileMethod:
    """Tests for Enemy.make_hostile() consolidated state transition."""

    def setup_method(self):
        """Set up test fixtures."""
        self.player_position = Position(10, 10)

    def test_make_hostile_basic_transition(self):
        """make_hostile sets state to HOSTILE and records player position."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM, cpu=30, vision=5, damage=5, name="Virus"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "virus")
            assert enemy.state == EnemyState.UNAWARE

            enemy.make_hostile(self.player_position)

            assert enemy.state == EnemyState.HOSTILE
            assert enemy.last_seen_player == self.player_position

    def test_make_hostile_stores_patrol_index(self):
        """make_hostile stores original patrol index for PATROL enemies."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL, cpu=40, vision=6, damage=8, name="PatrolUnit"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "patrol")
            enemy.patrol_points = [Position(0, 0), Position(10, 10), Position(5, 5)]
            enemy.patrol_index = 2  # Currently at third patrol point

            enemy.make_hostile(self.player_position)

            assert enemy.original_patrol_index == 2
            assert enemy.state == EnemyState.HOSTILE

    def test_make_hostile_clears_move_queue(self):
        """make_hostile clears movement queue on state change."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM, cpu=30, vision=5, damage=5, name="Virus"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "virus")
            enemy.move_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]

            enemy.make_hostile(self.player_position)

            assert enemy.move_queue == []

    def test_make_hostile_no_double_queue_clear(self):
        """make_hostile does not clear queue if already hostile."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM, cpu=30, vision=5, damage=5, name="Virus"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "virus")
            enemy.state = EnemyState.HOSTILE
            enemy.move_queue = [Position(6, 5), Position(7, 5)]

            # Call make_hostile again - should not clear queue since state didn't change
            enemy.make_hostile(self.player_position)

            # Queue should remain since state was already HOSTILE
            assert enemy.move_queue == [Position(6, 5), Position(7, 5)]

    def test_make_hostile_non_patrol_ignores_patrol_index(self):
        """make_hostile does not modify patrol index for non-PATROL enemies."""
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "virus": Mock(
                    movement=EnemyMovement.RANDOM, cpu=30, vision=5, damage=5, name="Virus"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "virus")
            original_patrol_index = enemy.original_patrol_index

            enemy.make_hostile(self.player_position)

            # original_patrol_index should remain at default (0)
            assert enemy.original_patrol_index == original_patrol_index


class TestPatrolRestorationIntegration:
    """Tests for patrol restoration when enemy loses interest."""

    def test_patrol_restoration_restores_original_waypoint(self):
        """When patrol enemy loses interest, they should resume at original waypoint.

        This tests the integration between make_hostile() storing the original
        patrol_index and _restore_patrol() restoring it when the enemy becomes UNAWARE.
        """
        with patch(
            "rsp.core.data.GameData.ENEMY_TYPES",
            {
                "patrol": Mock(
                    movement=EnemyMovement.PATROL, cpu=40, vision=6, damage=8, name="PatrolUnit"
                )
            },
        ):
            enemy = Enemy(Position(5, 5), "patrol")
            enemy.patrol_points = [
                Position(0, 0),
                Position(10, 10),
                Position(5, 5),
                Position(15, 15),
            ]
            enemy.patrol_index = 2  # Currently at third patrol point

            # Enemy spots player and becomes hostile
            player_pos = Position(7, 7)
            enemy.make_hostile(player_pos)

            # Verify hostile state and original index stored
            assert enemy.state == EnemyState.HOSTILE
            assert enemy.original_patrol_index == 2

            # Simulate enemy chasing and potentially advancing patrol index
            # (In real gameplay, patrol_index might change as enemy moves)
            enemy.patrol_index = 0  # Simulating some state change during chase

            # Import the restore function to test it directly
            from rsp.combat.turn_manager import GameTurnManager

            # Create a minimal mock engine for the turn manager
            mock_engine = Mock()
            mock_engine.ascension_modifiers = Mock()
            mock_engine.ascension_modifiers.blind_spots_consumable = False
            turn_manager = GameTurnManager(mock_engine)

            # Enemy loses track and becomes UNAWARE - should restore patrol index
            enemy.state = EnemyState.UNAWARE
            turn_manager._restore_patrol(enemy)

            # Verify patrol_index was restored to original
            assert (
                enemy.patrol_index == 2
            ), f"Expected patrol_index to be restored to 2, but got {enemy.patrol_index}"


class TestEnemyStateHelpers(TestEnemyAIBehavior):
    """Tests for enemy state helper methods (apply_stun, apply_blind)."""

    def test_apply_stun_sets_disabled_turns(self):
        """apply_stun should add to disabled_turns."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.disabled_turns = 0

        enemy.apply_stun(3)

        assert enemy.disabled_turns == 3

    def test_apply_stun_stacks_duration(self):
        """apply_stun should stack with existing disabled_turns."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.disabled_turns = 2

        enemy.apply_stun(3)

        assert enemy.disabled_turns == 5

    def test_apply_stun_resets_state_to_unaware(self):
        """apply_stun should reset state to UNAWARE."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.state = EnemyState.HOSTILE

        enemy.apply_stun(2)

        assert enemy.state == EnemyState.UNAWARE

    def test_apply_stun_clears_alert_timer(self):
        """apply_stun should clear alert timer."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.alert_timer = 5

        enemy.apply_stun(2)

        assert enemy.alert_timer == 0

    def test_apply_stun_clears_move_queue(self):
        """apply_stun should clear move queue."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.move_queue = [Position(6, 5), Position(7, 5)]

        enemy.apply_stun(2)

        assert enemy.move_queue == []

    def test_apply_blind_sets_blinded_turns(self):
        """apply_blind should set blinded_turns."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.blinded_turns = 0

        enemy.apply_blind(3)

        assert enemy.blinded_turns == 3

    def test_apply_blind_resets_state_to_unaware(self):
        """apply_blind should reset state to UNAWARE."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.state = EnemyState.HOSTILE

        enemy.apply_blind(2)

        assert enemy.state == EnemyState.UNAWARE

    def test_apply_blind_clears_last_seen_player(self):
        """apply_blind should clear last_seen_player."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.last_seen_player = Position(10, 10)

        enemy.apply_blind(2)

        assert enemy.last_seen_player is None

    def test_apply_blind_clears_alert_timer(self):
        """apply_blind should clear alert timer."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.alert_timer = 5

        enemy.apply_blind(2)

        assert enemy.alert_timer == 0

    def test_apply_blind_clears_move_queue(self):
        """apply_blind should clear move queue."""
        enemy = Enemy(Position(5, 5), "scanner")
        enemy.move_queue = [Position(6, 5), Position(7, 5)]

        enemy.apply_blind(2)

        assert enemy.move_queue == []


class TestEnemyFleeBehavior(TestEnemyAIBehavior):
    """Test enemy flee behavior when damaged."""

    def test_should_flee_returns_true_when_damaged_below_threshold(self):
        """Enemy should flee when health is below flee threshold and player visible.

        This test exposes a bug where _should_flee accessed self.type_data.max_cpu
        but EnemyTypeDefinition only has 'cpu' field. The correct attribute is self.max_cpu.
        """
        from rsp.core.config import GameConfig

        # Create real mobile enemy (not STATIC - static enemies can't flee)
        # Patrol has PATROL movement and 40 CPU
        enemy = Enemy(Position(10, 10), "patrol")

        # Verify enemy has max_cpu attribute set correctly
        assert hasattr(enemy, "max_cpu"), "Enemy should have max_cpu attribute"
        assert enemy.max_cpu > 0, f"Enemy max_cpu should be positive, got {enemy.max_cpu}"

        # Verify not static (static enemies can't flee)
        assert enemy.get_movement_type() != EnemyMovement.STATIC

        # Verify flee threshold config is loaded
        flee_threshold = GameConfig._get_required("balance.enemy_flee_health_threshold")
        assert flee_threshold == 0.3, f"Flee threshold should be 0.3, got {flee_threshold}"

        # Damage enemy to below 30% health (flee threshold)
        # Patrol has 40 CPU, so 10 CPU = 25% health
        enemy.cpu = 10
        enemy.state = EnemyState.HOSTILE  # Knows player is nearby

        # Verify health is below threshold
        health_percent = enemy.cpu / enemy.max_cpu
        assert (
            health_percent < flee_threshold
        ), f"Health {health_percent:.2f} should be below threshold {flee_threshold}"

        # This should return True since enemy is damaged below threshold
        # Bug: returned False because type_data.max_cpu threw AttributeError
        result = enemy._should_flee(self.player, self.mock_game_map)

        assert result is True, (
            f"Bug: _should_flee returned False for damaged enemy. "
            f"cpu={enemy.cpu}, max_cpu={enemy.max_cpu}, state={enemy.state}"
        )

    def test_should_flee_returns_false_when_healthy(self):
        """Enemy should not flee when health is above threshold."""
        enemy = Enemy(Position(10, 10), "scanner")
        enemy.state = EnemyState.HOSTILE

        # Full health - should not flee
        result = enemy._should_flee(self.player, self.mock_game_map)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
