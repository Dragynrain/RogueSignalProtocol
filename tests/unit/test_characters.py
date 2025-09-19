#!/usr/bin/env python3
"""
Unit tests for game_characters.py - Player and Enemy classes.
Tests core character functionality, movement, stats, and AI behavior.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_characters import Player, Enemy, create_pathfinding_cost_map, pathfind_and_move, can_move_to_position
from game_entities import Position, EnemyState, EnemyMovement
from game_data import GameData


class TestPlayer:
    """Test Player class functionality."""
    
    def test_player_creation(self):
        """Test basic player creation."""
        player = Player(10, 15)
        
        assert player.position.x == 10
        assert player.position.y == 15
        assert player.x == 10  # Property access
        assert player.y == 15  # Property access
        assert player.cpu == 100
        assert player.max_cpu == 100
        assert player.heat == 0
        assert player.detection == 0
        assert player.ram_total == 8
        assert player.base_vision_range == 15
    
    def test_player_position_properties(self):
        """Test position property getters and setters."""
        player = Player(5, 10)
        
        # Test initial values
        assert player.x == 5
        assert player.y == 10
        
        # Test setters
        player.x = 20
        player.y = 25
        assert player.position.x == 20
        assert player.position.y == 25
        assert player.x == 20
        assert player.y == 25
    
    def test_player_stats_validation(self):
        """Test that player stats are within expected ranges."""
        player = Player(0, 0)
        
        assert 0 <= player.cpu <= player.max_cpu
        assert player.heat >= 0
        assert player.detection >= 0
        assert player.ram_total > 0
        assert player.base_vision_range > 0
    
    def test_player_movement_valid(self):
        """Test valid player movement."""
        player = Player(10, 10)
        
        # Mock game map
        mock_map = Mock()
        mock_map.width = 50
        mock_map.height = 50
        mock_map.is_valid_position.return_value = True
        
        # Test movement
        moved = player.move(1, 0, mock_map)
        assert moved is True
        assert player.x == 11
        assert player.y == 10
        assert player.last_position.x == 10
        assert player.last_position.y == 10
    
    def test_player_movement_blocked(self):
        """Test blocked player movement."""
        player = Player(10, 10)
        
        # Mock game map that blocks movement
        mock_map = Mock()
        mock_map.width = 50
        mock_map.height = 50
        mock_map.is_valid_position.return_value = False
        
        # Test blocked movement
        moved = player.move(1, 0, mock_map)
        assert moved is False
        assert player.x == 10  # Should not move
        assert player.y == 10
    
    def test_player_movement_out_of_bounds(self):
        """Test player movement out of bounds."""
        player = Player(0, 0)
        
        mock_map = Mock()
        mock_map.width = 50
        mock_map.height = 50
        
        # Test moving out of bounds
        moved = player.move(-1, 0, mock_map)
        assert moved is False
        assert player.x == 0
        assert player.y == 0
    
    def test_player_temporary_effects_update(self):
        """Test temporary effects system."""
        player = Player(0, 0)
        
        # Set some effects
        player.temporary_effects['data_mimic_turns'] = 3
        player.temporary_effects['speed_boost_turns'] = 2
        player.temporary_effects['virus_turns'] = 1
        
        # Update effects
        player.update_effects()
        
        assert player.temporary_effects['data_mimic_turns'] == 2
        assert player.temporary_effects['speed_boost_turns'] == 1
        assert player.temporary_effects['virus_turns'] == 0
        
        # Update again
        player.update_effects()
        
        assert player.temporary_effects['data_mimic_turns'] == 1
        assert player.temporary_effects['speed_boost_turns'] == 0
        assert player.temporary_effects['virus_turns'] == 0
    
    def test_player_invisibility(self):
        """Test player invisibility from data mimic."""
        player = Player(0, 0)
        
        # Not invisible initially
        assert player.is_invisible() is False
        
        # Apply data mimic effect
        player.temporary_effects['data_mimic_turns'] = 3
        assert player.is_invisible() is True
        
        # Effect wears off
        player.temporary_effects['data_mimic_turns'] = 0
        assert player.is_invisible() is False
    
    def test_player_vision_range(self):
        """Test player vision range calculations."""
        player = Player(0, 0)
        
        # Base vision range
        assert player.get_vision_range() == player.base_vision_range
        
        # Enhanced vision effect
        player.temporary_effects['enhanced_vision_turns'] = 5
        assert player.get_vision_range() == player.base_vision_range + 2
        
        # Effect wears off
        player.temporary_effects['enhanced_vision_turns'] = 0
        assert player.get_vision_range() == player.base_vision_range
    
    def test_player_can_see_through_walls(self):
        """Test player wall-seeing ability."""
        player = Player(0, 0)
        
        # Normally can't see through walls
        assert player.can_see_through_walls() is False
        
        # Enhanced vision allows wall-seeing
        player.temporary_effects['enhanced_vision_turns'] = 3
        assert player.can_see_through_walls() is True
    
    def test_player_can_see_enemy_adjacent(self):
        """Test player can always see adjacent enemies."""
        player = Player(5, 5)
        
        # Create mock enemy adjacent to player
        mock_enemy = Mock()
        mock_enemy.position = Position(6, 5)  # Adjacent
        
        mock_map = Mock()
        
        # Should always see adjacent enemies regardless of other conditions
        can_see = player.can_see_enemy(mock_enemy, mock_map)
        assert can_see is True
    
    def test_player_can_see_enemy_with_enhanced_vision(self):
        """Test player can see enemies through walls with enhanced vision."""
        player = Player(5, 5)
        player.temporary_effects['enhanced_vision_turns'] = 3
        
        mock_enemy = Mock()
        mock_enemy.position = Position(10, 5)  # Within enhanced vision range
        
        mock_map = Mock()
        
        # Enhanced vision should allow seeing regardless of walls
        can_see = player.can_see_enemy(mock_enemy, mock_map)
        assert can_see is True
    
    def test_player_max_heat_property(self):
        """Test max heat property getter and setter."""
        player = Player(0, 0)
        
        # Default max heat
        assert player.max_heat == 100
        
        # Set new max heat
        player.max_heat = 150
        assert player.max_heat == 150
    
    def test_player_take_damage(self):
        """Test player taking damage."""
        player = Player(0, 0)
        player.cpu = 50
        
        # Take normal damage
        actual_damage = player.take_damage(20)
        assert actual_damage == 20
        assert player.cpu == 30
        
        # Take damage exceeding current CPU
        actual_damage = player.take_damage(50)
        assert actual_damage == 30  # Only remaining CPU
        assert player.cpu == 0
    
    @patch('game_data.GameUpgrades')
    def test_player_apply_permanent_upgrade(self, mock_upgrades):
        """Test applying permanent upgrades."""
        player = Player(0, 0)
        
        # Mock upgrade definition
        mock_upgrade = Mock()
        mock_upgrade.stat_type = 'ram'
        mock_upgrade.bonus_amount = 4
        
        mock_upgrades.UPGRADES = {'ram_boost': mock_upgrade}
        
        # Apply upgrade
        result = player.apply_permanent_upgrade('ram_boost')
        assert result is True
        assert player.ram_total == 12  # 8 + 4
        
        # Test unknown upgrade
        result = player.apply_permanent_upgrade('unknown_upgrade')
        assert result is False


class TestEnemy:
    """Test Enemy class functionality."""
    
    def test_enemy_creation(self):
        """Test basic enemy creation."""
        position = Position(10, 15)
        enemy = Enemy(position, 'scanner')
        
        assert enemy.position == position
        assert enemy.x == 10
        assert enemy.y == 15
        assert enemy.type == 'scanner'
        assert enemy.state == EnemyState.UNAWARE
        assert enemy.alert_timer == 0
        assert enemy.disabled_turns == 0
        assert isinstance(enemy.id, int)
        assert enemy.id > 0
    
    def test_enemy_unique_ids(self):
        """Test that enemies get unique IDs."""
        enemy1 = Enemy(Position(0, 0), 'scanner')
        enemy2 = Enemy(Position(1, 1), 'patrol')
        enemy3 = Enemy(Position(2, 2), 'bot')
        
        ids = [enemy1.id, enemy2.id, enemy3.id]
        assert len(set(ids)) == 3  # All unique
        assert all(id > 0 for id in ids)
    
    def test_enemy_stats_from_type_data(self):
        """Test that enemy stats match type definitions."""
        enemy = Enemy(Position(0, 0), 'scanner')
        
        # Should load stats from GameData.ENEMY_TYPES
        scanner_data = GameData.ENEMY_TYPES['scanner']
        assert enemy.cpu == scanner_data.cpu
        assert enemy.max_cpu == scanner_data.cpu
        assert enemy.type_data == scanner_data
    
    def test_enemy_position_properties(self):
        """Test enemy position property getters and setters."""
        enemy = Enemy(Position(5, 10), 'patrol')
        
        # Test initial values
        assert enemy.x == 5
        assert enemy.y == 10
        
        # Test setters
        enemy.x = 20
        enemy.y = 25
        assert enemy.position.x == 20
        assert enemy.position.y == 25
    
    def test_enemy_get_color(self):
        """Test enemy color based on state."""
        enemy = Enemy(Position(0, 0), 'scanner')
        
        # Unaware state
        enemy.state = EnemyState.UNAWARE
        enemy.disabled_turns = 0
        color = enemy.get_color()
        # Should be enemy unaware color (implementation specific)
        assert isinstance(color, tuple)
        assert len(color) == 3
        
        # Alert state
        enemy.state = EnemyState.ALERT
        color = enemy.get_color()
        assert isinstance(color, tuple)
        
        # Hostile state
        enemy.state = EnemyState.HOSTILE
        color = enemy.get_color()
        assert isinstance(color, tuple)
        
        # Disabled state (overrides other states)
        enemy.disabled_turns = 3
        color = enemy.get_color()
        assert isinstance(color, tuple)
    
    def test_enemy_can_see_player_basic(self):
        """Test basic enemy player vision."""
        enemy = Enemy(Position(5, 5), 'scanner')
        
        mock_player = Mock()
        mock_player.position = Position(8, 5)  # Within scanner vision (8 range)
        mock_player.is_invisible.return_value = False
        
        mock_map = Mock()
        mock_map.is_shadow.return_value = False
        mock_map.can_see_position.return_value = True
        
        can_see = enemy.can_see_player(mock_player, mock_map)
        assert can_see is True
    
    def test_enemy_can_see_player_disabled(self):
        """Test disabled enemy cannot see player."""
        enemy = Enemy(Position(5, 5), 'scanner')
        enemy.disabled_turns = 3
        
        mock_player = Mock()
        mock_player.position = Position(6, 5)  # Adjacent
        mock_player.is_invisible.return_value = False
        
        mock_map = Mock()
        
        can_see = enemy.can_see_player(mock_player, mock_map)
        assert can_see is False
    
    def test_enemy_can_see_player_invisible(self):
        """Test enemy cannot see invisible player (except admin)."""
        enemy = Enemy(Position(5, 5), 'scanner')
        
        mock_player = Mock()
        mock_player.position = Position(6, 5)
        mock_player.is_invisible.return_value = True
        
        mock_map = Mock()
        
        # Normal enemy cannot see invisible player
        can_see = enemy.can_see_player(mock_player, mock_map)
        assert can_see is False
        
        # Admin can always see player
        admin_enemy = Enemy(Position(5, 5), 'admin')
        can_see = admin_enemy.can_see_player(mock_player, mock_map)
        assert can_see is True
    
    def test_enemy_can_see_player_out_of_range(self):
        """Test enemy cannot see player beyond vision range."""
        enemy = Enemy(Position(5, 5), 'scanner')  # Vision range 5
        
        mock_player = Mock()
        mock_player.position = Position(20, 5)  # Far away
        mock_player.is_invisible.return_value = False
        
        mock_map = Mock()
        
        can_see = enemy.can_see_player(mock_player, mock_map)
        assert can_see is False
    
    def test_enemy_can_attack_player(self):
        """Test enemy attack range checking."""
        enemy = Enemy(Position(5, 5), 'patrol')
        
        mock_player = Mock()
        mock_player.is_invisible.return_value = False
        
        # Adjacent position - can attack
        mock_player.position = Position(6, 5)
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is True
        
        # Diagonal adjacent - can attack
        mock_player.position = Position(6, 6)
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is True
        
        # Same position - cannot attack (should not happen)
        mock_player.position = Position(5, 5)
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is False
        
        # Too far - cannot attack
        mock_player.position = Position(8, 5)
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is False
    
    def test_enemy_can_attack_disabled(self):
        """Test disabled enemy cannot attack."""
        enemy = Enemy(Position(5, 5), 'patrol')
        enemy.disabled_turns = 2
        
        mock_player = Mock()
        mock_player.position = Position(6, 5)  # Adjacent
        mock_player.is_invisible.return_value = False
        
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is False
    
    def test_enemy_can_attack_invisible_player(self):
        """Test enemy cannot attack invisible player (except admin)."""
        enemy = Enemy(Position(5, 5), 'patrol')
        
        mock_player = Mock()
        mock_player.position = Position(6, 5)
        mock_player.is_invisible.return_value = True
        
        # Normal enemy cannot attack invisible player
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is False
        
        # Admin can attack invisible player
        admin_enemy = Enemy(Position(5, 5), 'admin')
        can_attack = admin_enemy.can_attack_player(mock_player)
        assert can_attack is True
    
    def test_enemy_can_attack_no_damage_types(self):
        """Test enemies with no damage cannot attack (except virus)."""
        # Scanner has 0 damage
        scanner = Enemy(Position(5, 5), 'scanner')
        
        mock_player = Mock()
        mock_player.position = Position(6, 5)
        mock_player.is_invisible.return_value = False
        
        can_attack = scanner.can_attack_player(mock_player)
        assert can_attack is False
        
        # Virus has 0 damage but can still attack (applies status effects)
        virus = Enemy(Position(5, 5), 'virus')
        can_attack = virus.can_attack_player(mock_player)
        assert can_attack is True
    
    def test_enemy_attack_normal_damage(self):
        """Test normal enemy attack damage."""
        enemy = Enemy(Position(5, 5), 'patrol')  # 15 damage
        
        mock_player = Mock()
        mock_player.take_damage.return_value = 15
        
        damage = enemy.attack_player(mock_player)
        assert damage == 15
        mock_player.take_damage.assert_called_once_with(15)
    
    def test_enemy_attack_virus(self):
        """Test virus enemy attack applies status effect."""
        virus = Enemy(Position(5, 5), 'virus')
        
        mock_player = Mock()
        mock_player.temporary_effects = {'virus_turns': 0}
        
        damage = virus.attack_player(mock_player)
        assert damage == 0  # No immediate damage
        assert mock_player.temporary_effects['virus_turns'] > 0
    
    def test_enemy_attack_inhibitor(self):
        """Test inhibitor enemy attack applies slow effect."""
        inhibitor = Enemy(Position(5, 5), 'inhibitor')
        
        mock_player = Mock()
        mock_player.temporary_effects = {
            'speed_boost_turns': 0,
            'movement_slowed_turns': 0
        }
        mock_player.speed_moves_remaining = 0
        
        damage = inhibitor.attack_player(mock_player)
        assert damage == 0  # No immediate damage
        assert mock_player.temporary_effects['movement_slowed_turns'] > 0
    
    def test_enemy_take_damage_normal(self):
        """Test enemy taking normal damage."""
        enemy = Enemy(Position(5, 5), 'scanner')
        enemy.cpu = 35
        
        destroyed = enemy.take_damage(20)
        assert destroyed is False
        assert enemy.cpu == 15
        
        # Take lethal damage
        destroyed = enemy.take_damage(20)
        assert destroyed is True
        assert enemy.cpu <= 0
    
    def test_enemy_take_damage_admin_resistance(self):
        """Test admin enemy damage resistance."""
        admin = Enemy(Position(5, 5), 'admin')
        admin.cpu = 250
        
        # Admin has 50% damage resistance, minimum 5 damage
        destroyed = admin.take_damage(20)
        assert destroyed is False
        assert admin.cpu == 240  # 250 - 10 (20 // 2)
        
        # Test minimum damage
        admin.cpu = 250
        destroyed = admin.take_damage(8)
        assert destroyed is False
        assert admin.cpu == 245  # 250 - 5 (minimum damage)
    
    def test_enemy_movement_static(self):
        """Test static enemy never moves."""
        enemy = Enemy(Position(5, 5), 'firewall')  # Static movement
        
        mock_map = Mock()
        mock_player = Mock()
        mock_game = Mock()
        
        moved = enemy.move(mock_map, mock_player, mock_game)
        assert moved is False
        assert enemy.position.x == 5
        assert enemy.position.y == 5
    
    def test_enemy_movement_disabled(self):
        """Test disabled enemy cannot move."""
        enemy = Enemy(Position(5, 5), 'patrol')
        enemy.disabled_turns = 3
        
        mock_map = Mock()
        mock_player = Mock()
        mock_game = Mock()
        
        moved = enemy.move(mock_map, mock_player, mock_game)
        assert moved is False
        assert enemy.disabled_turns == 2  # Decremented
    
    def test_enemy_movement_cooldown(self):
        """Test enemy movement cooldown system."""
        enemy = Enemy(Position(5, 5), 'patrol')
        enemy.move_cooldown = 2
        
        mock_map = Mock()
        mock_player = Mock()
        mock_game = Mock()
        
        # Should not move due to cooldown
        moved = enemy.move(mock_map, mock_player, mock_game)
        assert moved is False
        assert enemy.move_cooldown == 1  # Decremented
        
        # Move again, cooldown should be 0 now
        moved = enemy.move(mock_map, mock_player, mock_game)
        # Now it depends on movement queue generation
    
    def test_enemy_movement_queue_generation(self):
        """Test enemy movement queue system."""
        enemy = Enemy(Position(5, 5), 'patrol')
        enemy.patrol_points = [Position(10, 10), Position(15, 15)]
        
        mock_map = Mock()
        mock_player = Mock()
        mock_game = Mock()
        
        # Mock the internal methods
        with patch.object(enemy, '_should_regenerate_queue', return_value=True):
            with patch.object(enemy, '_generate_movement_queue') as mock_generate:
                with patch.object(enemy, '_execute_next_move', return_value=True) as mock_execute:
                    moved = enemy.move(mock_map, mock_player, mock_game)
                    
                    mock_generate.assert_called_once()
                    mock_execute.assert_called_once()
                    assert moved is True


class TestEnemyAI:
    """Test enemy AI behavior and movement patterns."""
    
    def test_enemy_state_transitions(self):
        """Test enemy state transitions."""
        enemy = Enemy(Position(5, 5), 'patrol')
        
        # Start unaware
        assert enemy.state == EnemyState.UNAWARE
        
        # Transition to alert
        enemy.state = EnemyState.ALERT
        assert enemy.state == EnemyState.ALERT
        
        # Transition to hostile
        enemy.state = EnemyState.HOSTILE
        assert enemy.state == EnemyState.HOSTILE
    
    def test_enemy_patrol_points_system(self):
        """Test enemy patrol points."""
        enemy = Enemy(Position(5, 5), 'patrol')
        
        # Set patrol points
        patrol_points = [Position(10, 10), Position(15, 15), Position(20, 20)]
        enemy.patrol_points = patrol_points
        enemy.patrol_index = 0
        
        assert enemy.patrol_points == patrol_points
        assert enemy.patrol_index == 0
        
        # Test patrol index cycling
        enemy.patrol_index = (enemy.patrol_index + 1) % len(enemy.patrol_points)
        assert enemy.patrol_index == 1
    
    def test_enemy_last_seen_player_tracking(self):
        """Test enemy tracking of last seen player position."""
        enemy = Enemy(Position(5, 5), 'hunter')
        
        # Initially no last seen position
        assert enemy.last_seen_player is None
        
        # Set last seen position
        player_pos = Position(10, 15)
        enemy.last_seen_player = player_pos
        assert enemy.last_seen_player == player_pos
    
    def test_enemy_movement_queue_system(self):
        """Test enemy movement queue functionality."""
        enemy = Enemy(Position(5, 5), 'bot')
        
        # Initially empty queue
        assert len(enemy.movement_queue) == 0
        
        # Add moves to queue
        enemy.movement_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]
        assert len(enemy.movement_queue) == 3
        
        # Queue state tracking
        enemy.last_queue_state = EnemyState.ALERT
        enemy.last_queue_target = Position(10, 10)
        assert enemy.last_queue_state == EnemyState.ALERT
        assert enemy.last_queue_target == Position(10, 10)


class TestPathfinding:
    """Test pathfinding helper functions."""
    
    def test_create_pathfinding_cost_map(self):
        """Test pathfinding cost map creation."""
        import numpy as np
        
        mock_map = Mock()
        mock_map.width = 10
        mock_map.height = 10
        mock_map.is_valid_position.return_value = True
        
        mock_game = Mock()
        mock_game._get_enemy_at.return_value = None
        
        mock_enemy = Mock()
        
        cost_map = create_pathfinding_cost_map(mock_map, mock_game, mock_enemy)
        
        # Should be a numpy array with correct shape
        assert isinstance(cost_map, np.ndarray)
        assert cost_map.shape == (10, 10)
        assert cost_map.dtype == bool
        
        # All positions should be walkable (True) since mock_map.is_valid_position returns True
        assert np.all(cost_map == True)
    
    def test_can_move_to_position_valid(self):
        """Test valid movement position checking."""
        enemy = Mock()
        destination = Position(10, 10)
        
        mock_map = Mock()
        mock_map.is_valid_position.return_value = True
        
        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 5
        
        mock_game = Mock()
        mock_game.enemies = []
        
        can_move = can_move_to_position(enemy, destination, mock_map, mock_player, mock_game)
        assert can_move is True
    
    def test_can_move_to_position_invalid_position(self):
        """Test invalid position checking."""
        enemy = Mock()
        destination = Position(-1, -1)
        
        mock_map = Mock()
        mock_map.is_valid_position.return_value = False
        
        mock_player = Mock()
        mock_game = Mock()
        
        can_move = can_move_to_position(enemy, destination, mock_map, mock_player, mock_game)
        assert can_move is False
    
    def test_can_move_to_position_player_occupied(self):
        """Test cannot move to player position."""
        enemy = Mock()
        destination = Position(10, 10)
        
        mock_map = Mock()
        mock_map.is_valid_position.return_value = True
        
        mock_player = Mock()
        mock_player.x = 10
        mock_player.y = 10
        
        mock_game = Mock()
        mock_game.enemies = []
        
        can_move = can_move_to_position(enemy, destination, mock_map, mock_player, mock_game)
        assert can_move is False
    
    def test_can_move_to_position_enemy_occupied(self):
        """Test cannot move to position occupied by other enemy."""
        enemy = Mock()
        destination = Position(10, 10)
        
        mock_map = Mock()
        mock_map.is_valid_position.return_value = True
        
        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 5
        
        # Create other enemy at destination
        other_enemy = Mock()
        other_enemy.x = 10
        other_enemy.y = 10
        
        mock_game = Mock()
        mock_game.enemies = [enemy, other_enemy]
        
        can_move = can_move_to_position(enemy, destination, mock_map, mock_player, mock_game)
        assert can_move is False


class TestCharacterIntegration:
    """Test integration between Player and Enemy classes."""
    
    def test_player_enemy_position_interaction(self):
        """Test position-based interactions between player and enemies."""
        player = Player(5, 5)
        enemy = Enemy(Position(6, 5), 'patrol')
        
        # Test distance calculation
        distance = player.position.distance_to(enemy.position)
        assert distance == 1.0
        
        # Test adjacency for attack
        mock_player = Mock()
        mock_player.position = player.position
        mock_player.is_invisible.return_value = False
        
        can_attack = enemy.can_attack_player(mock_player)
        assert can_attack is True
    
    def test_player_enemy_vision_interaction(self):
        """Test vision interactions between player and enemies."""
        player = Player(5, 5)
        enemy = Enemy(Position(10, 5), 'scanner')  # Within scanner range
        
        # Mock map for vision calculations
        mock_map = Mock()
        mock_map.is_shadow.return_value = False
        mock_map.can_see_position.return_value = True
        
        # Test player can see enemy
        can_see_enemy = player.can_see_enemy(enemy, mock_map)
        assert can_see_enemy is True
        
        # Test enemy can see player
        can_see_player = enemy.can_see_player(player, mock_map)
        assert can_see_player is True
    
    def test_combat_interaction(self):
        """Test combat between player and enemy."""
        player = Player(5, 5)
        enemy = Enemy(Position(6, 5), 'patrol')  # Adjacent, 15 damage
        
        initial_cpu = player.cpu
        
        # Mock player for enemy attack
        mock_player = Mock()
        mock_player.take_damage.return_value = 15
        
        damage_dealt = enemy.attack_player(mock_player)
        assert damage_dealt == 15
        mock_player.take_damage.assert_called_once_with(15)
        
        # Test enemy taking damage
        destroyed = enemy.take_damage(30)
        assert destroyed is False  # Should survive (patrol has 40 HP)
        
        destroyed = enemy.take_damage(20)
        assert destroyed is True  # Should be destroyed now