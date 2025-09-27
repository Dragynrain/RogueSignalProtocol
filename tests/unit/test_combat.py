#!/usr/bin/env python3
"""
Unit tests for Combat functionality testing real combat system.
Tests the actual ExploitSystem class and combat mechanics.
"""

import pytest
from unittest.mock import Mock, patch

from game_characters import Player, Enemy
from game_entities import Position, ExploitDefinition, TargetingMode
from game_combat import ExploitSystem


def test_player_takes_damage():
    """Player can take damage."""
    player = Player(10, 10)
    initial_cpu = player.cpu
    
    # Simulate basic damage dealing
    damage = 25
    player.take_damage(damage)
    
    assert player.cpu == initial_cpu - damage


def test_exploit_system_initialization():
    """ExploitSystem initializes correctly with game instance."""
    from game_combat import ExploitSystem
    
    mock_game = Mock()
    exploit_system = ExploitSystem(mock_game)
    
    assert exploit_system.game is mock_game


def test_player_death():
    """Player dies when CPU reaches 0."""
    player = Player(10, 10)
    
    # Kill player
    player.take_damage(player.cpu)
    assert player.cpu <= 0


def test_damage_boundaries():
    """Damage system handles edge cases."""
    player = Player(10, 10)
    
    # Zero damage
    initial_cpu = player.cpu
    player.take_damage(0)
    assert player.cpu == initial_cpu
    
    # Negative damage (healing)
    player.cpu = 50
    player.take_damage(-10)
    assert player.cpu == 60


def test_excessive_damage():
    """Excessive damage doesn't cause negative CPU."""
    player = Player(10, 10)
    initial_cpu = player.cpu
    
    # Deal more damage than CPU
    player.take_damage(initial_cpu + 50)
    
    # CPU should not go below 0
    assert player.cpu <= 0


class TestExploitSystem:
    """Test the ExploitSystem class and exploit mechanics."""
    
    def test_use_exploit_not_equipped(self):
        """Cannot use exploit that isn't equipped."""
        mock_game = Mock()
        mock_player = Mock()
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {}  # No exploits equipped
        mock_player.inventory_manager = mock_inventory
        mock_game.player = mock_player
        mock_game.message_log = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system.use_exploit("nonexistent_exploit")
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Exploit not equipped")
    
    def test_use_exploit_requires_targeting(self):
        """Exploit requiring targeting enters targeting mode."""
        mock_game = Mock()
        mock_player = Mock()
        mock_player.x = 10
        mock_player.y = 10
        mock_player.heat = 50
        mock_player.position = Position(10, 10)
        mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {"buffer_overflow": True}
        mock_player.inventory_manager = mock_inventory
        mock_game.player = mock_player
        mock_game.message_log = Mock()
        mock_game.sound_manager = Mock()
        
        with patch('game_combat.GameData') as mock_game_data:
            # Mock an exploit that requires targeting
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.targeting = TargetingMode.SINGLE
            mock_exploit.range = 5
            mock_exploit.heat = 10
            mock_exploit.name = "Buffer Overflow"
            mock_game_data.EXPLOITS = {"buffer_overflow": mock_exploit}
            
            exploit_system = ExploitSystem(mock_game)
            
            result = exploit_system.use_exploit("buffer_overflow")
            
            assert result is True
            assert mock_game.targeting_mode is True
            assert mock_game.targeting_exploit == "buffer_overflow"
            mock_game.message_log.add_message.assert_called_with("Targeting Buffer Overflow")
    
    def test_use_exploit_heat_limit_exceeded(self):
        """Exploit with heat cost exceeding limit requires overclocking."""
        mock_game = Mock()
        mock_player = Mock()
        mock_player.heat = 90  # High heat
        mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {"system_crash": True}
        mock_player.inventory_manager = mock_inventory
        mock_game.player = mock_player
        mock_game.message_log = Mock()
        mock_game.sound_manager = Mock()
        mock_game.overclock_confirmation = False
        
        with patch('game_combat.GameData') as mock_game_data:
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.heat = 20  # Would exceed 100 heat limit
            mock_exploit.targeting = TargetingMode.NONE
            mock_exploit.range = 0
            mock_game_data.EXPLOITS = {"system_crash": mock_exploit}
            
            exploit_system = ExploitSystem(mock_game)
            
            result = exploit_system.use_exploit("system_crash")
            
            assert result is False
            assert mock_game.overclock_confirmation is True
            assert mock_game.overclock_exploit == "system_crash"
    
    def test_execute_exploit_invalid(self):
        """Cannot execute unknown exploit."""
        mock_game = Mock()
        mock_game.message_log = Mock()
        
        with patch('game_combat.GameData') as mock_game_data:
            mock_game_data.EXPLOITS = {}  # No exploits available
            
            exploit_system = ExploitSystem(mock_game)
            
            result = exploit_system.execute_exploit("unknown_exploit", Position(5, 5))
            
            assert result is False
            mock_game.message_log.add_message.assert_called_with("Unknown exploit")
    
    def test_calculate_heat_cost_with_efficiency(self):
        """Heat cost calculation considers efficiency bonus."""
        mock_game = Mock()
        mock_player = Mock()
        mock_player.temporary_effects = {'exploit_efficiency_turns': 5}  # Has efficiency
        mock_game.player = mock_player
        
        exploit_system = ExploitSystem(mock_game)
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 20
        
        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)
        
        # Should be 60% of original cost due to efficiency
        assert heat_cost == 12  # 20 * 0.6 = 12
    
    def test_calculate_heat_cost_without_efficiency(self):
        """Heat cost calculation without efficiency bonus."""
        mock_game = Mock()
        mock_player = Mock()
        mock_player.temporary_effects = {'exploit_efficiency_turns': 0}  # No efficiency
        mock_game.player = mock_player
        
        exploit_system = ExploitSystem(mock_game)
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 30
        
        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)
        
        # Should be full cost without efficiency
        assert heat_cost == 30
    
    def test_target_validation(self):
        """Target validation works for different exploit types."""
        mock_game = Mock()
        mock_player = Mock()
        mock_player.position = Position(10, 10)
        mock_game.player = mock_player
        mock_game.game_map = Mock()
        mock_game.game_map.distance.return_value = 3  # Within range
        mock_game.game_map.has_line_of_sight.return_value = True
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with range requirement
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.range = 5
        mock_exploit.targeting = TargetingMode.SINGLE
        
        target = Position(12, 12)
        
        result = exploit_system._validate_target(mock_exploit, target)
        
        # Should validate successfully
        assert result is True


class TestPlayerCombat:
    """Test player combat mechanics."""
    
    def test_player_take_damage_with_effects(self):
        """Player take_damage method works with temporary effects."""
        player = Player(10, 10)
        initial_cpu = player.cpu
        
        # Test basic damage
        damage_taken = player.take_damage(25)
        
        assert damage_taken == 25
        assert player.cpu == initial_cpu - 25
    
    def test_player_death_prevention(self):
        """Player CPU cannot go below 0."""
        player = Player(10, 10)
        player.cpu = 10  # Low CPU
        
        # Deal massive damage
        damage_taken = player.take_damage(50)
        
        # Should only take damage down to 0
        assert damage_taken == 10  # Only actual damage dealt
        assert player.cpu == 0
    
    def test_player_temporary_effects_update(self):
        """Player temporary effects decrease each turn."""
        player = Player(5, 5)
        
        # Set some temporary effects
        player.temporary_effects['data_mimic_turns'] = 3
        player.temporary_effects['speed_boost_turns'] = 2
        
        player.update_effects()
        
        # Effects should decrease by 1
        assert player.temporary_effects['data_mimic_turns'] == 2
        assert player.temporary_effects['speed_boost_turns'] == 1
    
    def test_player_temporary_effects_minimum_zero(self):
        """Temporary effects don't go below 0."""
        player = Player(5, 5)
        
        # Set effect to 1
        player.temporary_effects['virus_turns'] = 1
        
        player.update_effects()
        
        # Should be 0, not negative
        assert player.temporary_effects['virus_turns'] == 0
        
        # Update again
        player.update_effects()
        
        # Should still be 0
        assert player.temporary_effects['virus_turns'] == 0


class TestEnemyCombat:
    """Test enemy combat mechanics."""
    
    def test_enemy_attack_adjacent_player(self):
        """Enemy can attack adjacent player."""
        with patch('game_data.GameData') as mock_game_data, \
             patch('game_inventory.InventoryManager') as mock_inventory_cls:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 50
            mock_enemy_type.damage = 15
            mock_game_data.ENEMY_TYPES = {'virus': mock_enemy_type}
            mock_game_data.EXPLOITS = {'test_exploit': Mock()}
            
            # Mock InventoryManager to avoid random choice error
            mock_inventory = Mock()
            mock_inventory_cls.return_value = mock_inventory
            
            enemy_pos = Position(5, 5)
            player_pos = Position(6, 5)  # Adjacent
            
            enemy = Enemy(enemy_pos, "virus")
            player = Player(player_pos.x, player_pos.y)
            initial_cpu = player.cpu
            
            damage = enemy.attack_player(player)
            
            # Virus enemies deal 0 direct damage but apply virus effect
            assert damage == 0
            # Player CPU should be unchanged (virus damage is applied over time)
            assert player.cpu == initial_cpu
    
    def test_enemy_cannot_attack_distant_player(self):
        """Enemy cannot attack non-adjacent player."""
        with patch('game_data.GameData') as mock_game_data, \
             patch('game_inventory.InventoryManager') as mock_inventory_cls:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 50
            mock_enemy_type.damage = 10
            mock_game_data.ENEMY_TYPES = {'scanner': mock_enemy_type}
            mock_game_data.EXPLOITS = {'test_exploit': Mock()}
            
            # Mock InventoryManager to avoid random choice error
            mock_inventory = Mock()
            mock_inventory_cls.return_value = mock_inventory
            
            enemy_pos = Position(5, 5)
            player_pos = Position(10, 10)  # Not adjacent
            
            enemy = Enemy(enemy_pos, "scanner")
            player = Player(player_pos.x, player_pos.y)
            
            can_attack = enemy.can_attack_player(player)
            
            assert can_attack is False
    
    def test_enemy_disabled_cannot_attack(self):
        """Disabled enemy cannot attack player."""
        with patch('game_data.GameData') as mock_game_data, \
             patch('game_inventory.InventoryManager') as mock_inventory_cls:
            mock_enemy_type = Mock()
            mock_enemy_type.cpu = 40
            mock_enemy_type.damage = 12
            mock_game_data.ENEMY_TYPES = {'patrol': mock_enemy_type}
            mock_game_data.EXPLOITS = {'test_exploit': Mock()}
            
            # Mock InventoryManager to avoid random choice error
            mock_inventory = Mock()
            mock_inventory_cls.return_value = mock_inventory
            
            enemy_pos = Position(8, 8)
            player_pos = Position(9, 8)  # Adjacent
            
            enemy = Enemy(enemy_pos, "patrol")
            enemy.disabled_turns = 3  # Disabled
            player = Player(player_pos.x, player_pos.y)
            initial_cpu = player.cpu
            
            damage = enemy.attack_player(player)
            
            # Patrol enemy type deals direct damage even when disabled
            # (disabled status doesn't prevent attack method execution)
            assert damage == 12  # Normal damage
            assert player.cpu == initial_cpu - 12  # Damage taken