#!/usr/bin/env python3
"""
Unit tests for game_combat.py - Exploit system and damage calculations.
Tests the core combat mechanics, exploit effects, and targeting system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_combat import ExploitSystem
from game_entities import Position, TargetingMode, EnemyState, EnemyMovement
from game_data import GameData
from game_config import GameBalance


class TestExploitSystem:
    """Test ExploitSystem class functionality."""
    
    def test_exploit_system_creation(self):
        """Test basic exploit system creation."""
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)
        
        assert exploit_system.game == mock_game
    
    def test_heat_cost_calculation_normal(self):
        """Test normal heat cost calculation."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with 30 heat cost
        mock_exploit = Mock()
        mock_exploit.heat = 30
        
        cost = exploit_system._calculate_heat_cost(mock_exploit)
        assert cost == 30
    
    def test_heat_cost_calculation_with_efficiency(self):
        """Test heat cost calculation with efficiency bonus."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 3}
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with 30 heat cost
        mock_exploit = Mock()
        mock_exploit.heat = 30
        
        cost = exploit_system._calculate_heat_cost(mock_exploit)
        assert cost == 18  # 30 * 0.6
    
    def test_validate_target_valid(self):
        """Test valid target validation."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with range 5
        mock_exploit = Mock()
        mock_exploit.range = 5
        
        target = Position(8, 5)  # Distance 3, within range
        
        with patch('game_config.GameConfig.MAP_WIDTH', 50), patch('game_config.GameConfig.MAP_HEIGHT', 50):
            is_valid = exploit_system._validate_target(mock_exploit, target)
            assert is_valid is True
    
    def test_validate_target_out_of_range(self):
        """Test target validation for out of range."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with range 3
        mock_exploit = Mock()
        mock_exploit.range = 3
        
        target = Position(15, 5)  # Distance 10, out of range
        
        with patch('game_config.GameConfig.MAP_WIDTH', 50), patch('game_config.GameConfig.MAP_HEIGHT', 50):
            is_valid = exploit_system._validate_target(mock_exploit, target)
            assert is_valid is False
            mock_game.message_log.add_message.assert_called_with("Out of range (Max: 3)")
    
    def test_validate_target_invalid_position(self):
        """Test target validation for invalid position."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        mock_exploit = Mock()
        mock_exploit.range = 10
        
        target = Position(-1, -1)  # Invalid position
        
        with patch('game_config.GameConfig.MAP_WIDTH', 50), patch('game_config.GameConfig.MAP_HEIGHT', 50):
            is_valid = exploit_system._validate_target(mock_exploit, target)
            assert is_valid is False
            mock_game.message_log.add_message.assert_called_with("Invalid target location")
    
    def test_use_exploit_not_equipped(self):
        """Test using exploit that is not equipped."""
        mock_game = Mock()
        mock_game.player.inventory_manager.equipped_exploits = []
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system.use_exploit('code_injection')
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Exploit not equipped")
    
    def test_use_exploit_overclocking_confirmation(self):
        """Test exploit overclocking confirmation system."""
        mock_game = Mock()
        mock_game.player.inventory_manager.equipped_exploits = ['code_injection']
        mock_game.player.heat = 90
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_game.message_log.add_message = Mock()
        mock_game.sound_manager.play_sound = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit with 20 heat cost (would cause overclocking)
        with patch.dict(GameData.EXPLOITS, {
            'code_injection': Mock(heat=20, targeting=TargetingMode.SINGLE, range=5)
        }):
            result = exploit_system.use_exploit('code_injection')
            
            assert result is False
            assert hasattr(mock_game, 'overclock_confirmation')
            assert mock_game.overclock_confirmation is True
            assert mock_game.overclock_exploit == 'code_injection'
    
    def test_use_exploit_targeting_mode(self):
        """Test exploit that requires targeting."""
        mock_game = Mock()
        mock_game.player.inventory_manager.equipped_exploits = ['code_injection']
        mock_game.player.heat = 10
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_game.player.x = 5
        mock_game.player.y = 5
        mock_game.message_log.add_message = Mock()
        mock_game.sound_manager.play_sound = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock exploit that requires targeting
        mock_exploit = Mock(heat=20, targeting=TargetingMode.SINGLE, range=5)
        mock_exploit.name = "Code Injection"
        with patch.dict(GameData.EXPLOITS, {
            'code_injection': mock_exploit
        }):
            result = exploit_system.use_exploit('code_injection')
            
            assert result is True
            assert mock_game.targeting_mode is True
            assert mock_game.targeting_exploit == 'code_injection'
            mock_game.message_log.add_message.assert_called_with("Targeting Code Injection")
    
    def test_use_exploit_immediate_execution(self):
        """Test exploit that executes immediately (no targeting)."""
        mock_game = Mock()
        mock_game.player.inventory_manager.equipped_exploits = ['data_mimic']
        mock_game.player.heat = 10
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_game.player.position = Position(5, 5)
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock data_mimic exploit (no targeting)
        with patch.dict(GameData.EXPLOITS, {
            'data_mimic': Mock(heat=25, targeting=TargetingMode.NONE, range=0)
        }):
            with patch.object(exploit_system, 'execute_exploit', return_value=True) as mock_execute:
                result = exploit_system.use_exploit('data_mimic')
                
                assert result is True
                mock_execute.assert_called_once_with('data_mimic', mock_game.player.position)


class TestSpecificExploits:
    """Test specific exploit implementations."""
    
    def test_shadow_step_valid_target(self):
        """Test shadow step to valid shadow zone."""
        mock_game = Mock()
        mock_game.game_map.is_shadow.return_value = True
        mock_game.game_map.is_valid_position.return_value = True
        mock_game._get_enemy_at.return_value = None
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_shadow_step(target)
        
        assert result is True
        assert mock_game.player.position == target
        mock_game.message_log.add_message.assert_called_with("Shadow Step executed")
        mock_game.sound_manager.play_sound.assert_called_with("exploit_shadow_step")
    
    def test_shadow_step_invalid_target(self):
        """Test shadow step to non-shadow zone."""
        mock_game = Mock()
        mock_game.game_map.is_shadow.return_value = False
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_shadow_step(target)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Must target shadow zone")
    
    def test_shadow_step_occupied_target(self):
        """Test shadow step to occupied shadow zone."""
        mock_game = Mock()
        mock_game.game_map.is_shadow.return_value = True
        mock_game.game_map.is_valid_position.return_value = True
        mock_game._get_enemy_at.return_value = Mock()  # Enemy present
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_shadow_step(target)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Target occupied")
    
    def test_data_mimic_execution(self):
        """Test data mimic exploit execution."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {'data_mimic_turns': 0}
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_data_mimic()
        
        assert result is True
        assert mock_game.player.temporary_effects['data_mimic_turns'] == 5
        mock_game.message_log.add_message.assert_called_with("Data Mimic active")
        mock_game.sound_manager.play_sound.assert_called_with("exploit_data_mimic")
    
    def test_noise_maker_execution(self):
        """Test noise maker exploit execution."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        # Create mock enemies
        mock_enemy1 = Mock()
        mock_enemy1.type_data.movement = EnemyMovement.SEEK
        mock_enemy1.position = Position(8, 8)  # Within range 10
        mock_enemy1.state = EnemyState.UNAWARE
        
        mock_enemy2 = Mock()
        mock_enemy2.type_data.movement = EnemyMovement.PATROL
        mock_enemy2.position = Position(25, 25)  # Clearly out of range (distance > 10)
        
        mock_game.enemies = [mock_enemy1, mock_enemy2]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_noise_maker(target)
        
        assert result is True
        assert mock_enemy1.state == EnemyState.ALERT
        assert mock_enemy1.last_seen_player == target
        mock_game.message_log.add_message.assert_called_with("Noise: 1 enemies attracted")
    
    def test_code_injection_enemy_elimination(self):
        """Test code injection eliminating an enemy."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.player.x = 5
        mock_game.player.y = 5
        mock_game.player.cpu = 80
        mock_game.player.max_cpu = 100
        
        # Create mock enemy
        mock_enemy = Mock()
        mock_enemy.type = 'scanner'
        mock_enemy.type_data.name = "Scanner"
        mock_enemy.take_damage.return_value = True  # Enemy is destroyed
        
        mock_game._get_enemy_at.return_value = mock_enemy
        mock_game.enemies = [mock_enemy]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_code_injection(target)
        
        assert result is True
        mock_enemy.take_damage.assert_called_once_with(30)  # Normal damage for non-firewall
        # Note: enemies list should be mocked differently to test removal
        mock_game.message_log.add_message.assert_called_with("Eliminated Scanner")
    
    def test_code_injection_firewall_bonus_damage(self):
        """Test code injection does bonus damage to firewall."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.player.x = 5
        mock_game.player.y = 5
        
        # Create mock firewall enemy
        mock_firewall = Mock()
        mock_firewall.type = 'firewall'
        mock_firewall.type_data.name = "Firewall"
        mock_firewall.take_damage.return_value = False  # Enemy survives
        
        mock_game._get_enemy_at.return_value = mock_firewall
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_code_injection(target)
        
        assert result is True
        mock_firewall.take_damage.assert_called_once_with(35)  # Bonus damage for firewall
        mock_game.message_log.add_message.assert_called_with("Firewall damaged")
    
    def test_code_injection_no_target(self):
        """Test code injection with no enemy at target."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game._get_enemy_at.return_value = None
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_code_injection(target)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("No target at location")
    
    def test_buffer_overflow_valid_attack(self):
        """Test buffer overflow melee attack."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.player.x = 5
        mock_game.player.y = 5
        mock_game.player.cpu = 80
        mock_game.player.max_cpu = 100
        
        # Create mock enemy adjacent to player
        mock_enemy = Mock()
        mock_enemy.type_data.name = "Bot"
        mock_enemy.take_damage.return_value = True  # Enemy is destroyed
        
        mock_game._get_enemy_at.return_value = mock_enemy
        mock_game.enemies = [mock_enemy]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(6, 5)  # Adjacent position (distance 1)
        result = exploit_system._execute_buffer_overflow(target)
        
        assert result is True
        mock_enemy.take_damage.assert_called_once_with(50)  # High damage
        # Note: enemies list should be mocked differently to test removal
        mock_game.message_log.add_message.assert_called_with("Eliminated Bot")
    
    def test_buffer_overflow_not_adjacent(self):
        """Test buffer overflow requires adjacent target."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)  # Not adjacent
        result = exploit_system._execute_buffer_overflow(target)
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Must target adjacent enemy")
    
    def test_system_crash_area_effect(self):
        """Test system crash area effect."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        # Create mock enemies
        mock_enemy1 = Mock()
        mock_enemy1.position = Position(8, 8)  # Within range 3
        mock_enemy1.disabled_turns = 0
        mock_enemy1.state = EnemyState.HOSTILE
        mock_enemy1.alert_timer = 5
        
        mock_enemy2 = Mock()
        mock_enemy2.position = Position(15, 15)  # Out of range
        
        mock_game.enemies = [mock_enemy1, mock_enemy2]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_system_crash(target, 3)
        
        assert result is True
        # Enemy 1 should be disabled and reset
        assert mock_enemy1.disabled_turns == 4
        assert mock_enemy1.state == EnemyState.UNAWARE
        assert mock_enemy1.alert_timer == 0
        # Enemy 2 should be unchanged
        mock_game.message_log.add_message.assert_called_with("System crash: 1 disabled")
    
    def test_threat_scan_execution(self):
        """Test threat scan exploit execution."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.game_state.threat_scan_turns = 0
        mock_game.turn = 10
        
        # Create mock enemies
        mock_enemy1 = Mock()
        mock_enemy1.id = 1
        mock_enemy1.position = Position(10, 10)
        
        mock_enemy2 = Mock()
        mock_enemy2.id = 2
        mock_enemy2.position = Position(15, 15)
        
        mock_game.enemies = [mock_enemy1, mock_enemy2]
        mock_game.game_map.last_known_enemy_positions = {}
        mock_game.game_map.explored_tiles = set()
        
        exploit_system = ExploitSystem(mock_game)
        
        with patch('game_config.GameConfig.MAP_WIDTH', 50), patch('game_config.GameConfig.MAP_HEIGHT', 50):
            result = exploit_system._execute_threat_scan()
            
            assert result is True
            assert mock_game.game_state.threat_scan_turns == 5
            assert len(mock_game.game_map.last_known_enemy_positions) == 2
            mock_game.message_log.add_message.assert_called_with("THREAT SCAN ACTIVE - 2 hostiles detected!")
    
    def test_log_wiper_execution(self):
        """Test log wiper exploit execution."""
        mock_game = Mock()
        mock_game.player.detection = 80
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_log_wiper()
        
        assert result is True
        assert mock_game.player.detection == 50  # 80 - 30
        mock_game.message_log.add_message.assert_called_with("Detection: -30.0%")
    
    def test_log_wiper_minimum_zero(self):
        """Test log wiper cannot reduce detection below zero."""
        mock_game = Mock()
        mock_game.player.detection = 15
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_log_wiper()
        
        assert result is True
        assert mock_game.player.detection == 0  # Clamped to minimum 0
        mock_game.message_log.add_message.assert_called_with("Detection: -15.0%")
    
    def test_antivirus_with_effects(self):
        """Test antivirus removing negative effects."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {
            'virus_turns': 5,
            'movement_slowed_turns': 3,
            'speed_boost_turns': 2  # Positive effect, should not be removed
        }
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_antivirus()
        
        assert result is True
        assert mock_game.player.temporary_effects['virus_turns'] == 0
        assert mock_game.player.temporary_effects['movement_slowed_turns'] == 0
        assert mock_game.player.temporary_effects['speed_boost_turns'] == 2  # Unchanged
        
        # Should have called add_message multiple times
        assert mock_game.message_log.add_message.call_count >= 2
    
    def test_antivirus_no_effects(self):
        """Test antivirus with no negative effects to remove."""
        mock_game = Mock()
        mock_game.player.temporary_effects = {
            'virus_turns': 0,
            'movement_slowed_turns': 0
        }
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_antivirus()
        
        assert result is True
        mock_game.message_log.add_message.assert_called_with("No negative effects detected")
    
    def test_emp_burst_area_effect(self):
        """Test EMP burst area effect."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        # Create mock enemies
        mock_enemy1 = Mock()
        mock_enemy1.position = Position(8, 8)  # Within range 3
        mock_enemy1.disabled_turns = 0
        mock_enemy1.state = EnemyState.HOSTILE
        mock_enemy1.alert_timer = 5
        
        mock_enemy2 = Mock()
        mock_enemy2.position = Position(15, 15)  # Out of range
        
        mock_game.enemies = [mock_enemy1, mock_enemy2]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_emp_burst(target, 3)
        
        assert result is True
        # Enemy 1 should be disabled longer than system crash
        assert mock_enemy1.disabled_turns == 6
        assert mock_enemy1.state == EnemyState.UNAWARE
        assert mock_enemy1.alert_timer == 0
        mock_game.message_log.add_message.assert_called_with("EMP: 1 disabled")
    
    def test_memory_leak_area_effect(self):
        """Test memory leak area effect."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        
        # Create mock enemies
        mock_enemy1 = Mock()
        mock_enemy1.position = Position(10, 10)  # At target (distance 0)
        mock_enemy1.state = EnemyState.HOSTILE
        mock_enemy1.last_seen_player = Position(5, 5)
        mock_enemy1.alert_timer = 5
        
        mock_enemy2 = Mock()
        mock_enemy2.position = Position(11, 10)  # Adjacent (distance = 1)
        mock_enemy2.state = EnemyState.ALERT
        mock_enemy2.last_seen_player = Position(6, 6)
        mock_enemy2.alert_timer = 3
        
        mock_enemy3 = Mock()
        mock_enemy3.position = Position(15, 15)  # Too far
        
        mock_game.enemies = [mock_enemy1, mock_enemy2, mock_enemy3]
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_memory_leak(target)
        
        assert result is True
        # Both nearby enemies should be reset
        assert mock_enemy1.state == EnemyState.UNAWARE
        assert mock_enemy1.last_seen_player is None
        assert mock_enemy1.alert_timer == 0
        
        assert mock_enemy2.state == EnemyState.UNAWARE
        assert mock_enemy2.last_seen_player is None
        assert mock_enemy2.alert_timer == 0
        
        mock_game.message_log.add_message.assert_called_with("Memory Leak: 2 enemies confused")
    
    def test_memory_leak_no_enemies(self):
        """Test memory leak with no enemies in range."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.enemies = []
        
        exploit_system = ExploitSystem(mock_game)
        
        target = Position(10, 10)
        result = exploit_system._execute_memory_leak(target)
        
        assert result is True
        mock_game.message_log.add_message.assert_called_with("No enemies in range")
    
    def test_network_scan_execution(self):
        """Test network scan exploit execution."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.game_state.revealed_special_nodes = {}
        
        # Mock special nodes
        mock_game.game_map.cooling_nodes = [Position(10, 10), Position(15, 15)]
        mock_game.game_map.cpu_recovery_nodes = [Position(20, 20)]
        mock_game.game_map.ghost_nodes = [Position(25, 25)]
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system._execute_network_scan()
        
        assert result is True
        assert len(mock_game.game_state.revealed_special_nodes) == 4
        
        # Check specific node types are revealed
        assert mock_game.game_state.revealed_special_nodes[Position(10, 10)] == "cooling"
        assert mock_game.game_state.revealed_special_nodes[Position(20, 20)] == "cpu"
        assert mock_game.game_state.revealed_special_nodes[Position(25, 25)] == "ghost"
        
        mock_game.message_log.add_message.assert_called_with("Port Scan: 4 special nodes revealed")


class TestExploitExecution:
    """Test exploit execution flow."""
    
    def test_execute_exploit_unknown(self):
        """Test executing unknown exploit."""
        mock_game = Mock()
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        result = exploit_system.execute_exploit('unknown_exploit', Position(10, 10))
        
        assert result is False
        mock_game.message_log.add_message.assert_called_with("Unknown exploit")
    
    def test_execute_exploit_invalid_target(self):
        """Test executing exploit with invalid target."""
        mock_game = Mock()
        mock_game.player.position = Position(5, 5)
        mock_game.message_log.add_message = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock validation to fail
        with patch.object(exploit_system, '_validate_target', return_value=False):
            result = exploit_system.execute_exploit('code_injection', Position(10, 10))
            
            assert result is False
    
    def test_execute_exploit_successful(self):
        """Test successful exploit execution."""
        mock_game = Mock()
        mock_game.player.heat = 30
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        mock_game.targeting_mode = True
        mock_game.targeting_exploit = 'code_injection'
        mock_game.maybe_process_turn = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock validation and execution to succeed
        with patch.object(exploit_system, '_validate_target', return_value=True):
            with patch.object(exploit_system, '_execute_specific_exploit', return_value=True):
                with patch.dict(GameData.EXPLOITS, {
                    'code_injection': Mock(heat=20)
                }):
                    result = exploit_system.execute_exploit('code_injection', Position(10, 10))
                    
                    assert result is True
                    assert mock_game.player.heat == 50  # 30 + 20
                    assert mock_game.targeting_mode is False
                    assert mock_game.targeting_exploit is None
                    mock_game.maybe_process_turn.assert_called_once()
    
    def test_execute_exploit_heat_limit(self):
        """Test exploit execution respects heat limit."""
        mock_game = Mock()
        mock_game.player.heat = 95
        mock_game.player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock validation and execution to succeed
        with patch.object(exploit_system, '_validate_target', return_value=True):
            with patch.object(exploit_system, '_execute_specific_exploit', return_value=True):
                with patch.dict(GameData.EXPLOITS, {
                    'code_injection': Mock(heat=20)
                }):
                    result = exploit_system.execute_exploit('code_injection', Position(10, 10))
                    
                    assert result is True
                    assert mock_game.player.heat == 100  # Clamped at maximum


class TestDamageCalculations:
    """Test damage calculation mechanics and combat balance."""
    
    def test_player_damage_resistance_calculations(self):
        """Test player damage resistance and absorption."""
        from game_characters import Player
        
        player = Player(10, 10)
        player.cpu = 80
        
        # Test normal damage (no resistance for players)
        damage_taken = player.take_damage(20)
        assert damage_taken == 20
        assert player.cpu == 60  # 80 - 20
        
        # Test damage exceeding current CPU
        player.cpu = 10
        damage_taken = player.take_damage(20)
        assert damage_taken == 10  # Can't take more than current CPU
        assert player.cpu == 0
    
    def test_enemy_damage_resistance_admin(self):
        """Test admin avatar 50% damage reduction."""
        from game_characters import Enemy
        
        admin = Enemy(Position(15, 15), 'admin')
        admin.cpu = 200
        
        # Admin should take 50% damage with minimum 5
        destroyed = admin.take_damage(40)
        assert not destroyed  # Should not be destroyed
        # 40 damage -> 20 actual damage (50% reduction)
        assert admin.cpu == 180  # 200 - 20
        
        # Test minimum damage threshold
        admin.cpu = 200
        destroyed = admin.take_damage(8)  # 8 -> 4, but minimum 5
        assert admin.cpu == 195  # 200 - 5 (minimum)
    
    def test_enemy_damage_resistance_normal(self):
        """Test normal enemy damage calculations."""
        from game_characters import Enemy
        
        scanner = Enemy(Position(10, 10), 'scanner')
        scanner.cpu = 35
        
        # Normal enemies take full damage
        destroyed = scanner.take_damage(25)
        assert not destroyed
        assert scanner.cpu == 10  # 35 - 25
        
        # Test destruction
        destroyed = scanner.take_damage(15)
        assert destroyed
        assert scanner.cpu <= 0
    
    def test_minimum_damage_thresholds(self):
        """Test minimum damage thresholds are enforced."""
        from game_characters import Enemy
        
        admin = Enemy(Position(20, 20), 'admin')
        admin.cpu = 250
        
        # Even with 50% reduction, minimum 5 damage should be applied
        destroyed = admin.take_damage(2)  # 2 -> 1, but minimum 5
        assert not destroyed
        assert admin.cpu == 245  # 250 - 5 (minimum)
        
        # Test with higher damage that gets reduced
        destroyed = admin.take_damage(10)  # 10 -> 5, meets minimum
        assert admin.cpu == 240  # 245 - 5
    
    def test_critical_hit_stealth_attacks(self):
        """Test critical hit scenarios from stealth."""
        # Note: Stealth bonus damage is not implemented in current system
        # This test documents expected behavior for future implementation
        from game_characters import Player, Enemy
        
        player = Player(5, 5)
        player.temporary_effects['data_mimic_turns'] = 3  # Invisible
        
        enemy = Enemy(Position(6, 6), 'bot')
        enemy.state = EnemyState.UNAWARE
        enemy.cpu = 25
        
        # Currently no stealth bonus implemented, but test framework is ready
        base_damage = 20
        destroyed = enemy.take_damage(base_damage)
        expected_cpu = 25 - base_damage
        assert enemy.cpu == expected_cpu
    
    def test_status_effect_virus_damage(self):
        """Test virus damage over time calculations."""
        from game_characters import Player
        from game_data import GameBalance
        
        player = Player(8, 8)
        player.cpu = 80
        player.temporary_effects['virus_turns'] = 5
        
        # Test virus damage per turn (from GameBalance)
        virus_damage = GameBalance.VIRUS_DAMAGE_PER_TURN
        damage_taken = player.take_damage(virus_damage)
        
        assert damage_taken == virus_damage
        assert player.cpu == 80 - virus_damage
    
    def test_damage_calculation_edge_cases(self):
        """Test edge cases in damage calculations."""
        from game_characters import Enemy
        
        enemy = Enemy(Position(12, 12), 'scanner')
        enemy.cpu = 35
        
        # Test zero damage
        destroyed = enemy.take_damage(0)
        assert not destroyed
        assert enemy.cpu == 35  # No change
        
        # Test massive damage
        destroyed = enemy.take_damage(1000)
        assert destroyed
        assert enemy.cpu <= 0
    
    def test_damage_type_effectiveness(self):
        """Test damage type effectiveness against different enemies."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game._get_enemy_at = Mock()
        
        # Create firewall enemy
        mock_firewall = Mock()
        mock_firewall.type = 'firewall'
        mock_firewall.type_data.name = "Firewall"
        mock_firewall.take_damage.return_value = False
        mock_game._get_enemy_at.return_value = mock_firewall
        
        exploit_system = ExploitSystem(mock_game)
        
        # Test code injection bonus damage vs firewall
        target = Position(10, 10)
        result = exploit_system._execute_code_injection(target)
        
        assert result is True
        # Code injection deals 35 damage to firewalls, 30 to others
        mock_firewall.take_damage.assert_called_once_with(35)
    
    def test_enemy_special_attacks(self):
        """Test special enemy attack behaviors."""
        from game_characters import Enemy, Player
        
        # Test virus enemy (applies status, no direct damage)
        virus = Enemy(Position(5, 5), 'virus')
        player = Player(6, 6)
        
        # Virus attacks should apply virus effect, not direct damage
        damage_dealt = virus.attack_player(player)
        assert damage_dealt == 0  # No direct damage
        
        # Test inhibitor enemy (applies slow, minimal damage)
        inhibitor = Enemy(Position(7, 7), 'inhibitor')
        damage_dealt = inhibitor.attack_player(player)
        assert damage_dealt == 0  # Inhibitor only slows


class TestCombatIntegration:
    """Test integration of combat system components."""
    
    def test_exploit_system_integration(self):
        """Test full exploit system integration."""
        # Create comprehensive mock game
        mock_game = Mock()
        mock_game.player.inventory_manager.equipped_exploits = ['data_mimic']
        mock_game.player.heat = 10
        mock_game.player.position = Position(5, 5)
        mock_game.player.temporary_effects = {'data_mimic_turns': 0, 'exploit_efficiency_turns': 0}
        mock_game.message_log.add_message = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.targeting_mode = False
        mock_game.maybe_process_turn = Mock()
        
        exploit_system = ExploitSystem(mock_game)
        
        # Mock data_mimic exploit
        with patch.dict(GameData.EXPLOITS, {
            'data_mimic': Mock(heat=25, targeting=TargetingMode.NONE, range=0)
        }):
            result = exploit_system.use_exploit('data_mimic')
            
            assert result is True
            assert mock_game.player.heat == 35  # 10 + 25
            assert mock_game.player.temporary_effects['data_mimic_turns'] == 5
            mock_game.maybe_process_turn.assert_called_once()
    
    @pytest.mark.parametrize("exploit_name,expected_targeting", [
        ('data_mimic', False),
        ('log_wiper', False), 
        ('antivirus', False),
        ('threat_scan', False),
        ('network_scan', False),
        ('code_injection', True),
        ('buffer_overflow', True),
        ('shadow_step', True),
        ('system_crash', True),
    ])
    def test_exploit_targeting_requirements(self, exploit_name, expected_targeting):
        """Test that exploits have correct targeting requirements."""
        if exploit_name in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[exploit_name]
            requires_targeting = (exploit.targeting != TargetingMode.NONE and exploit.range > 0)
            assert requires_targeting == expected_targeting
    
    def test_damage_calculation_consistency(self):
        """Test that damage calculations are consistent."""
        mock_game = Mock()
        mock_game.sound_manager.play_sound = Mock()
        mock_game.message_log.add_message = Mock()
        mock_game.player.x = 5
        mock_game.player.y = 5
        
        # Test code injection damage
        mock_enemy = Mock()
        mock_enemy.type = 'scanner'
        mock_enemy.type_data.name = "Scanner"
        mock_enemy.take_damage.return_value = False
        
        mock_game._get_enemy_at.return_value = mock_enemy
        
        exploit_system = ExploitSystem(mock_game)
        
        # Code injection should do 30 damage to non-firewall
        exploit_system._execute_code_injection(Position(10, 10))
        mock_enemy.take_damage.assert_called_with(30)
        
        # Reset mock
        mock_enemy.reset_mock()
        
        # Buffer overflow should do 50 damage
        mock_game.player.position = Position(9, 10)  # Adjacent to target
        exploit_system._execute_buffer_overflow(Position(10, 10))
        mock_enemy.take_damage.assert_called_with(50)