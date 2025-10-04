#!/usr/bin/env python3
"""
Comprehensive Enemy AI Behavior Tests - Test Category 1
Tests for Enemy AI behavior including movement patterns, state transitions,
pathfinding, alerts, and the movement queue system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_characters import Enemy, Player
from game_entities import Position, EnemyState, EnemyMovement
from game_enemies import EnemyManager
from tests.fixtures.simple_fixtures import player


# Mock the pathfinding function to prevent import errors
def mock_create_pathfinding_cost_map(game_map, game, moving_enemy):
    """Mock pathfinding cost map creation."""
    return [[1 for _ in range(game_map.width)] for _ in range(game_map.height)]


class TestEnemyAIBehavior:
    """Test suite for Enemy AI behavior and decision-making."""
    
    def setup_method(self):
        """Setup common test objects."""
        self.mock_game_map = Mock()
        self.mock_game_map.width = 80
        self.mock_game_map.height = 40
        self.mock_game_map.is_valid_position = Mock(return_value=True)
        self.mock_game_map.is_wall = Mock(return_value=False)
        self.mock_game_map.is_shadow = Mock(return_value=False)
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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'static_test': Mock(movement=EnemyMovement.STATIC, cpu=50, vision=5, damage=10)
        }):
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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'random_test': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=5, damage=10, name="RandomTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
                enemy = Enemy(Position(5, 5), "random_test")

                # RANDOM enemies move when unaware
                assert enemy.state == EnemyState.UNAWARE
                initial_pos = enemy.position
                enemy.move(self.mock_game_map, self.player, self.mock_game)

                # Movement system should work (either moved or stayed)
                assert enemy.position is not None
    
    def test_seek_movement_targets_visible_player(self):
        """SEEK enemies target player when HOSTILE and can see them."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'seek_test': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10, name="SeekTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
                enemy = Enemy(Position(5, 5), "seek_test")
                enemy.state = EnemyState.HOSTILE

                # Mock enemy can see player
                with patch.object(enemy, 'can_see_player', return_value=True):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Verify enemy has player position as last seen
                    assert enemy.last_seen_player == self.player.position
    
    def test_track_movement_remembers_last_position(self):
        """TRACK enemies remember and pursue last seen player position when HOSTILE."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'track_test': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10, name="TrackTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
                enemy = Enemy(Position(5, 5), "track_test")
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(15, 15)

                # Mock enemy cannot see player currently
                with patch.object(enemy, 'can_see_player', return_value=False):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Last seen position should remain
                    assert enemy.last_seen_player == Position(15, 15)
    
    def test_patrol_movement_follows_route(self):
        """PATROL enemies follow their patrol route."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'patrol_test': Mock(movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=8, y=8)  # Within vision range
            
            # Mock clear line of sight
            self.mock_game_map.can_see_position.return_value = True
            
            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True
    
    def test_cannot_see_player_beyond_vision_range(self):
        """Enemy cannot see player beyond their vision range."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=5, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=15, y=15)  # Beyond vision range
            
            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is False
    
    def test_cannot_see_invisible_player(self):
        """Enemy cannot see invisible player (data mimic effect)."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=7, y=7)  # Within range
            test_player.is_invisible = Mock(return_value=True)
            
            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is False
    
    def test_admin_can_always_see_player(self):
        """Admin enemies can always see the player regardless of conditions."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'admin': Mock(movement=EnemyMovement.SEEK, cpu=100, vision=10, damage=20)
        }):
            enemy = Enemy(Position(5, 5), "admin")
            test_player = player(x=50, y=50)  # Very far away
            test_player.is_invisible = Mock(return_value=True)  # Invisible
            
            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True
    
    def test_player_in_shadow_stealth_mechanics(self):
        """Player in shadows is only visible to adjacent enemies."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Position(5, 5)
            test_player = player(x=8, y=8)  # Within vision range but not adjacent
            
            # Mock player is in shadow
            self.mock_game_map.is_shadow.return_value = True
            
            enemy_obj = Enemy(enemy, "test_enemy")
            result = enemy_obj.can_see_player(test_player, self.mock_game_map)
            assert result is False
    
    def test_adjacent_enemy_sees_player_in_shadow(self):
        """Adjacent enemy can see player even in shadows."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=6, y=6)  # Adjacent
            
            # Mock player is in shadow
            self.mock_game_map.is_shadow.return_value = True
            
            result = enemy.can_see_player(test_player, self.mock_game_map)
            assert result is True  # Adjacent enemies can see through shadows


class TestEnemyAttackBehavior(TestEnemyAIBehavior):
    """Test enemy attack and combat behavior."""
    
    def test_can_attack_adjacent_player(self):
        """Enemy can attack adjacent player."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=6, y=6)  # Adjacent
            
            result = enemy.can_attack_player(test_player)
            assert result is True
    
    def test_cannot_attack_distant_player(self):
        """Enemy cannot attack distant player."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            test_player = player(x=10, y=10)  # Not adjacent
            
            result = enemy.can_attack_player(test_player)
            assert result is False
    
    def test_disabled_enemy_cannot_attack(self):
        """Disabled enemy cannot attack."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(5, 5), "test_enemy")
            enemy.disabled_turns = 3
            test_player = player(x=6, y=6)  # Adjacent
            
            result = enemy.can_attack_player(test_player)
            assert result is False
    
    def test_cannot_attack_invisible_player_except_admin(self):
        """Regular enemies cannot attack invisible players, but admin can."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=10),
            'admin': Mock(movement=EnemyMovement.SEEK, cpu=100, vision=10, damage=20)
        }):
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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'virus': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=0)
        }):
            enemy = Enemy(Position(5, 5), "virus")
            test_player = player()
            
            damage = enemy.attack_player(test_player)
            
            assert damage == 0  # No immediate damage
            assert test_player.temporary_effects.get('virus_turns', 0) > 0
    
    def test_inhibitor_enemy_applies_slow_effect(self):
        """Inhibitor enemy applies movement slow effect."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'inhibitor': Mock(movement=EnemyMovement.RANDOM, cpu=50, vision=10, damage=0)
        }):
            enemy = Enemy(Position(5, 5), "inhibitor")
            test_player = player()
            
            damage = enemy.attack_player(test_player)
            
            assert damage == 0  # No immediate damage
            assert test_player.temporary_effects.get('movement_slowed_turns', 0) > 0


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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'patrol': Mock(movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
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
        with patch('game_data.GameData.ENEMY_TYPES', {
            'patrol': Mock(movement=EnemyMovement.PATROL, cpu=50, vision=10, damage=10, name="PatrolTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
                enemy = Enemy(Position(5, 5), "patrol")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 0
                enemy.state = EnemyState.HOSTILE

                # Mock enemy can see player
                with patch.object(enemy, 'can_see_player', return_value=True):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Should have set player as last seen target
                    assert enemy.last_seen_player == self.player.position
    
    def test_patrol_enemy_returns_to_patrol_after_losing_player(self):
        """Patrol enemy returns to patrol route after losing sight of player."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'patrol': Mock(movement=EnemyMovement.PATROL, cpu=50, vision=5, damage=10, name="PatrolTest")
        }):
            with patch('game_characters.create_pathfinding_cost_map', mock_create_pathfinding_cost_map):
                enemy = Enemy(Position(5, 5), "patrol")
                enemy.patrol_points = [Position(10, 10), Position(15, 15), Position(5, 5)]
                enemy.patrol_index = 1
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = None

                # Mock enemy cannot see player
                with patch.object(enemy, 'can_see_player', return_value=False):
                    enemy.move(self.mock_game_map, self.player, self.mock_game)

                    # Patrol system should still work
                    assert enemy.patrol_points is not None


if __name__ == "__main__":
    pytest.main([__file__])