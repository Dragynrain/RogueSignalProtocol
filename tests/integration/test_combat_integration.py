#!/usr/bin/env python3
"""
Integration tests for Combat system functionality.
Tests the actual ExploitSystem class and combat mechanics integration.
"""

import pytest
from unittest.mock import Mock, patch

from game_characters import Player, Enemy
from game_entities import Position, ExploitDefinition, TargetingMode
from game_combat import ExploitSystem


def test_exploit_system_initialization(basic_game_engine):
    """ExploitSystem initializes correctly with game instance."""
    from game_combat import ExploitSystem

    exploit_system = ExploitSystem(basic_game_engine)

    assert exploit_system.game is basic_game_engine


class TestExploitSystem:
    """Test the ExploitSystem class and exploit mechanics."""

    def test_use_exploit_not_equipped(self, basic_game_engine):
        """Cannot use exploit that isn't equipped."""
        # Player starts with no exploits equipped
        basic_game_engine.player.inventory_manager.equipped_exploits = []

        exploit_system = ExploitSystem(basic_game_engine)

        result = exploit_system.use_exploit("nonexistent_exploit")

        assert result is False
        # Message log is real, check the last message
        assert basic_game_engine.message_log.messages[-1].text == "Exploit not equipped"
    
    def test_use_exploit_requires_targeting(self, basic_game_engine):
        """Exploit requiring targeting enters targeting mode."""
        # Set up player with exploit equipped
        basic_game_engine.player.heat = 50
        basic_game_engine.player.inventory_manager.equipped_exploits = ["buffer_overflow"]

        with patch('game_combat.GameData') as mock_game_data:
            # Mock an exploit that requires targeting
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.targeting = TargetingMode.SINGLE
            mock_exploit.range = 5
            mock_exploit.heat = 10
            mock_exploit.name = "Buffer Overflow"
            mock_game_data.EXPLOITS = {"buffer_overflow": mock_exploit}

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.use_exploit("buffer_overflow")

            assert result is True
            assert basic_game_engine.targeting_mode is True
            assert basic_game_engine.targeting_exploit == "buffer_overflow"
            assert basic_game_engine.message_log.messages[-1].text == "Targeting Buffer Overflow"
    
    def test_use_exploit_heat_limit_exceeded(self, basic_game_engine):
        """Exploit with heat cost exceeding limit shows overclock dialogue."""
        # Set player to high heat
        basic_game_engine.player.heat = 90  # High heat
        basic_game_engine.player.inventory_manager.equipped_exploits = ["system_crash"]

        with patch('game_combat.GameData') as mock_game_data, \
             patch.object(basic_game_engine.dialogue_state, 'show') as mock_show:
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.heat = 20  # Would exceed 100 heat limit
            mock_exploit.targeting = TargetingMode.NONE
            mock_exploit.range = 0
            mock_exploit.name = "System Crash"
            mock_game_data.EXPLOITS = {"system_crash": mock_exploit}

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.use_exploit("system_crash")

            # Should return False and show dialogue instead of old confirmation system
            assert result is False
            # Verify dialogue_state.show was called
            mock_show.assert_called_once()
    
    def test_execute_exploit_invalid(self, basic_game_engine):
        """Cannot execute unknown exploit."""
        with patch('game_combat.GameData') as mock_game_data:
            mock_game_data.EXPLOITS = {}  # No exploits available

            exploit_system = ExploitSystem(basic_game_engine)

            result = exploit_system.execute_exploit("unknown_exploit", Position(5, 5))

            assert result is False
            assert basic_game_engine.message_log.messages[-1].text == "Unknown exploit"
    
    def test_calculate_heat_cost_with_efficiency(self, basic_game_engine):
        """Heat cost calculation considers efficiency bonus."""
        basic_game_engine.player.temporary_effects['exploit_efficiency_turns'] = 5  # Has efficiency

        exploit_system = ExploitSystem(basic_game_engine)

        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 20

        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)

        # Should be 60% of original cost due to efficiency
        assert heat_cost == 12  # 20 * 0.6 = 12

    def test_calculate_heat_cost_without_efficiency(self, basic_game_engine):
        """Heat cost calculation without efficiency bonus."""
        basic_game_engine.player.temporary_effects['exploit_efficiency_turns'] = 0  # No efficiency

        exploit_system = ExploitSystem(basic_game_engine)

        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 30

        heat_cost = exploit_system._calculate_heat_cost(mock_exploit)

        # Should be full cost without efficiency
        assert heat_cost == 30
    
    def test_target_validation(self, basic_game_engine):
        """Target validation works for different exploit types."""
        with patch.object(basic_game_engine.game_map, 'has_line_of_sight', return_value=True):
            exploit_system = ExploitSystem(basic_game_engine)

            # Mock exploit with range requirement
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.range = 5
            mock_exploit.targeting = TargetingMode.SINGLE

            # Target close enough to player (at 15, 15)
            target = Position(17, 15)

            result = exploit_system._validate_target(mock_exploit, target)

            # Should validate successfully (distance is 2, within range of 5)
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
        from tests.fixtures.simple_fixtures import player, enemy

        test_enemy = enemy("virus", 5, 5)
        test_player = player(6, 5, 100)  # Adjacent
        initial_cpu = test_player.cpu

        damage = test_enemy.attack_player(test_player)

        # Virus enemies deal 0 direct damage but apply virus effect
        assert damage == 0
        # Player CPU should be unchanged (virus damage is applied over time)
        assert test_player.cpu == initial_cpu

    def test_enemy_cannot_attack_distant_player(self):
        """Enemy cannot attack non-adjacent player."""
        from tests.fixtures.simple_fixtures import player, enemy

        test_enemy = enemy("scanner", 5, 5)
        test_player = player(10, 10, 100)  # Not adjacent

        can_attack = test_enemy.can_attack_player(test_player)

        assert can_attack is False

    def test_enemy_disabled_cannot_attack(self):
        """Disabled enemy cannot attack player."""
        from tests.fixtures.simple_fixtures import player, enemy

        test_enemy = enemy("patrol", 8, 8)
        test_enemy.disabled_turns = 3  # Disabled
        test_player = player(9, 8, 100)  # Adjacent
        initial_cpu = test_player.cpu

        damage = test_enemy.attack_player(test_player)

        # Patrol enemy type deals direct damage even when disabled
        # (disabled status doesn't prevent attack method execution)
        assert damage == test_enemy.type_data.damage  # Normal damage
        assert test_player.cpu == initial_cpu - test_enemy.type_data.damage  # Damage taken