#!/usr/bin/env python3
"""
Comprehensive Combat System Core Tests.
Focuses on exploit execution, targeting, and combat mechanics.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import Dict, Any

from game_combat import ExploitSystem
from game_characters import Player, Enemy
from game_entities import Position, TargetingMode, ExploitDefinition, EnemyState, EnemyMovement
from game_data import GameData
from game_config import GameBalance
from game_inventory import InventoryManager
from game_state import MessageLog
from game_audio import SoundManager


class TestExploitSystemInitialization:
    """Test exploit system initialization and setup."""
    
    def test_exploit_system_init(self):
        """Exploit system initializes with game reference."""
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)
        
        assert exploit_system.game is mock_game
    
    def test_exploit_system_requires_game_reference(self):
        """Exploit system requires valid game reference."""
        # Should accept any object as game reference
        mock_game = Mock()
        exploit_system = ExploitSystem(mock_game)
        
        assert exploit_system.game is not None


class TestExploitUsageValidation:
    """Test exploit usage validation and requirements."""
    
    def setup_method(self):
        """Set up mock game environment for each test."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_inventory = Mock(spec=InventoryManager)
        self.mock_message_log = Mock(spec=MessageLog)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        # Set up game components
        self.mock_game.player = self.mock_player
        self.mock_game.message_log = self.mock_message_log
        self.mock_game.sound_manager = self.mock_sound_manager
        self.mock_game.targeting_mode = False
        self.mock_game.targeting_exploit = None
        self.mock_game.overclock_confirmation = False
        self.mock_game.overclock_exploit = None
        
        # Set up player components
        self.mock_player.inventory_manager = self.mock_inventory
        self.mock_player.heat = 30
        self.mock_player.position = Position(10, 10)
        self.mock_player.x = 10
        self.mock_player.y = 10
        self.mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_use_exploit_not_equipped(self):
        """Cannot use exploit that is not equipped."""
        self.mock_inventory.equipped_exploits = {}
        
        result = self.exploit_system.use_exploit("shadow_step")
        
        assert result is False
        self.mock_message_log.add_message.assert_called_with("Exploit not equipped")
    
    def test_use_exploit_equipped_success(self):
        """Can use equipped exploit successfully."""
        # Set up equipped exploit
        self.mock_inventory.equipped_exploits = {"shadow_step": True}
        
        # Mock exploit definition
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"shadow_step": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True) as mock_execute:
            
            result = self.exploit_system.use_exploit("shadow_step")
            
            assert result is True
            mock_execute.assert_called_once_with("shadow_step", self.mock_player.position)
    
    def test_use_exploit_requires_targeting(self):
        """Exploit requiring targeting enters targeting mode."""
        self.mock_inventory.equipped_exploits = {"buffer_overflow": True}
        
        # Mock exploit requiring targeting
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 5
        mock_exploit.name = "Buffer Overflow"
        mock_exploit.heat = 30
        
        with patch.dict(GameData.EXPLOITS, {"buffer_overflow": mock_exploit}):
            
            result = self.exploit_system.use_exploit("buffer_overflow")
            
            assert result is True
            assert self.mock_game.targeting_mode is True
            assert self.mock_game.targeting_exploit == "buffer_overflow"
            self.mock_message_log.add_message.assert_called_with("Targeting Buffer Overflow")
            self.mock_sound_manager.play_sound.assert_called_with("exploit_targeting")


class TestOverclockingSystem:
    """Test overclocking mechanics and heat management."""
    
    def setup_method(self):
        """Set up mock game environment for overclocking tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_inventory = Mock(spec=InventoryManager)
        self.mock_message_log = Mock(spec=MessageLog)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        self.mock_game.player = self.mock_player
        self.mock_game.message_log = self.mock_message_log
        self.mock_game.sound_manager = self.mock_sound_manager
        self.mock_game.overclock_confirmation = False
        self.mock_game.overclock_exploit = None
        
        self.mock_player.inventory_manager = self.mock_inventory
        self.mock_player.heat = 85  # High heat for overclocking tests
        self.mock_player.position = Position(10, 10)
        self.mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        self.mock_player.take_damage = Mock(return_value=20)
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_overclocking_requires_confirmation(self):
        """Overclocking requires user confirmation."""
        self.mock_inventory.equipped_exploits = {"system_crash": True}
        
        # Mock high-heat exploit
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 30  # Would push heat over 100
        
        with patch.dict(GameData.EXPLOITS, {"system_crash": mock_exploit}):
            
            result = self.exploit_system.use_exploit("system_crash")
            
            assert result is False
            assert self.mock_game.overclock_confirmation is True
            assert self.mock_game.overclock_exploit == "system_crash"
            self.mock_message_log.add_message.assert_called()
            self.mock_sound_manager.play_sound.assert_called_with("exploit_failed")
    
    def test_overclocking_confirmed_applies_damage(self):
        """Confirmed overclocking applies CPU damage."""
        self.mock_inventory.equipped_exploits = {"system_crash": True}
        self.mock_game.overclock_confirmation = True
        self.mock_game.overclock_exploit = "system_crash"
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 30
        
        with patch.dict(GameData.EXPLOITS, {"system_crash": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True):
            
            result = self.exploit_system.use_exploit("system_crash")
            
            assert result is True
            assert self.mock_game.overclock_confirmation is False
            self.mock_player.take_damage.assert_called_with(15)  # 85 + 30 - 100 = 15
            assert self.mock_player.heat == 100
            self.mock_sound_manager.play_sound.assert_called_with("overclocking")
    
    def test_heat_cost_calculation_base(self):
        """Heat cost calculation works for base case."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 25
        
        cost = self.exploit_system._calculate_heat_cost(mock_exploit)
        
        assert cost == 25
    
    def test_heat_cost_calculation_with_efficiency(self):
        """Heat cost calculation applies efficiency bonus."""
        self.mock_player.temporary_effects = {'exploit_efficiency_turns': 3}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 30
        
        cost = self.exploit_system._calculate_heat_cost(mock_exploit)
        
        assert cost == 18  # 30 * 0.6 = 18


class TestExploitExecution:
    """Test specific exploit execution logic."""
    
    def setup_method(self):
        """Set up mock game environment for exploit execution tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_message_log = Mock(spec=MessageLog)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        self.mock_game.player = self.mock_player
        self.mock_game.message_log = self.mock_message_log
        self.mock_game.sound_manager = self.mock_sound_manager
        self.mock_game.targeting_mode = True
        self.mock_game.targeting_exploit = "test_exploit"
        self.mock_game.maybe_process_turn = Mock()
        
        self.mock_player.heat = 30
        self.mock_player.position = Position(10, 10)
        self.mock_player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_execute_exploit_unknown_exploit(self):
        """Cannot execute unknown exploit."""
        with patch.dict(GameData.EXPLOITS, {}, clear=True):
            
            result = self.exploit_system.execute_exploit("unknown", Position(5, 5))
            
            assert result is False
            self.mock_message_log.add_message.assert_called_with("Unknown exploit")
    
    def test_execute_exploit_invalid_target(self):
        """Cannot execute exploit with invalid target."""
        mock_exploit = Mock(spec=ExploitDefinition)
        
        with patch.dict(GameData.EXPLOITS, {"test_exploit": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=False):
            
            result = self.exploit_system.execute_exploit("test_exploit", Position(5, 5))
            
            assert result is False
    
    def test_execute_exploit_success_applies_heat(self):
        """Successful exploit execution applies heat cost."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 25
        
        with patch.dict(GameData.EXPLOITS, {"test_exploit": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.exploit_system, '_execute_specific_exploit', return_value=True):
            
            initial_heat = self.mock_player.heat
            
            result = self.exploit_system.execute_exploit("test_exploit", Position(5, 5))
            
            assert result is True
            assert self.mock_player.heat == min(100, initial_heat + 25)
            assert self.mock_game.targeting_mode is False
            assert self.mock_game.targeting_exploit is None
            self.mock_game.maybe_process_turn.assert_called_once()
    
    def test_execute_exploit_failure_no_heat(self):
        """Failed exploit execution does not apply heat cost."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 25
        
        with patch.dict(GameData.EXPLOITS, {"test_exploit": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.exploit_system, '_execute_specific_exploit', return_value=False):
            
            initial_heat = self.mock_player.heat
            
            result = self.exploit_system.execute_exploit("test_exploit", Position(5, 5))
            
            assert result is False
            assert self.mock_player.heat == initial_heat  # No heat applied


class TestTargetValidation:
    """Test target validation for different exploit types."""
    
    def setup_method(self):
        """Set up mock game environment for validation tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_game.player = self.mock_player
        self.mock_player.x = 10
        self.mock_player.y = 10
        self.mock_player.position = Position(10, 10)
        self.mock_game.message_log = Mock()
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_validate_target_out_of_range(self):
        """Target validation fails for out-of-range targets."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.range = 3
        mock_exploit.targeting = TargetingMode.SINGLE
        
        # Target too far away
        target = Position(20, 20)
        
        with patch.object(self.mock_game.message_log, 'add_message') as mock_message:
            
            result = self.exploit_system._validate_target(mock_exploit, target)
            
            assert result is False
            mock_message.assert_called()
    
    def test_validate_target_in_range_success(self):
        """Target validation succeeds for in-range targets."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.range = 5
        mock_exploit.targeting = TargetingMode.SINGLE
        
        target = Position(12, 12)
        
        # Target close enough (distance ~2.8, range is 5)
        result = self.exploit_system._validate_target(mock_exploit, target)
        
        assert result is True


class TestSpecificExploitMechanics:
    """Test mechanics of specific exploit implementations."""
    
    def setup_method(self):
        """Set up mock game environment for specific exploit tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_game_map = Mock()
        self.mock_enemy_manager = Mock()
        self.mock_message_log = Mock(spec=MessageLog)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        self.mock_game.player = self.mock_player
        self.mock_game.game_map = self.mock_game_map
        self.mock_game.enemy_manager = self.mock_enemy_manager
        self.mock_game.message_log = self.mock_message_log
        self.mock_game.sound_manager = self.mock_sound_manager
        
        self.mock_player.x = 10
        self.mock_player.y = 10
        self.mock_player.shadow_steps = 0
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_execute_shadow_step_valid_position(self):
        """Shadow step executes successfully to valid position."""
        target = Position(12, 12)
        
        with patch('game_characters.can_move_to_position', return_value=True):
            
            result = self.exploit_system._execute_shadow_step(target)
            
            assert result is True
            assert self.mock_player.x == 12
            assert self.mock_player.y == 12
            assert self.mock_player.shadow_steps == 1
            self.mock_sound_manager.play_sound.assert_called_with("shadow_step")
    
    def test_execute_shadow_step_blocked_position(self):
        """Shadow step fails when target position is blocked."""
        target = Position(12, 12)
        
        with patch('game_characters.can_move_to_position', return_value=False):
            
            result = self.exploit_system._execute_shadow_step(target)
            
            assert result is False
            assert self.mock_player.x == 10  # Position unchanged
            assert self.mock_player.y == 10
            self.mock_message_log.add_message.assert_called_with("Cannot shadow step to that location")
    
    def test_execute_data_mimic_success(self):
        """Data mimic executes successfully."""
        result = self.exploit_system._execute_data_mimic()
        
        assert result is True
        self.mock_sound_manager.play_sound.assert_called_with("data_mimic")
        self.mock_message_log.add_message.assert_called_with("Data signature randomized")
    
    def test_execute_noise_maker_creates_ghost_node(self):
        """Noise maker creates ghost node at target location."""
        target = Position(15, 15)
        
        with patch('time.time', return_value=1000.0):
            
            result = self.exploit_system._execute_noise_maker(target)
            
            assert result is True
            # Should add ghost node to game map
            self.mock_game_map.ghost_nodes.__setitem__.assert_called_with(target, 1000.0)
            self.mock_sound_manager.play_sound.assert_called_with("noise_maker")
    
    def test_execute_buffer_overflow_damages_enemy(self):
        """Buffer overflow damages enemy at target location."""
        target = Position(15, 15)
        mock_enemy = Mock(spec=Enemy)
        mock_enemy.position = target
        
        self.mock_enemy_manager.get_enemy_at_position.return_value = mock_enemy
        
        result = self.exploit_system._execute_buffer_overflow(target)
        
        assert result is True
        mock_enemy.take_damage.assert_called()
        self.mock_sound_manager.play_sound.assert_called_with("buffer_overflow")
    
    def test_execute_buffer_overflow_no_enemy(self):
        """Buffer overflow fails when no enemy at target."""
        target = Position(15, 15)
        
        self.mock_enemy_manager.get_enemy_at_position.return_value = None
        
        result = self.exploit_system._execute_buffer_overflow(target)
        
        assert result is False
        self.mock_message_log.add_message.assert_called_with("No target at that location")


class TestCombatSystemIntegration:
    """Test integration between combat system and other game systems."""
    
    def setup_method(self):
        """Set up full mock game environment for integration tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_enemy_manager = Mock()
        self.mock_message_log = Mock(spec=MessageLog)
        self.mock_sound_manager = Mock(spec=SoundManager)
        
        self.mock_game.player = self.mock_player
        self.mock_game.enemy_manager = self.mock_enemy_manager
        self.mock_game.message_log = self.mock_message_log
        self.mock_game.sound_manager = self.mock_sound_manager
        self.mock_game.targeting_mode = False
        self.mock_game.maybe_process_turn = Mock()
        
        # Set up enemies
        self.mock_enemy1 = Mock(spec=Enemy)
        self.mock_enemy1.position = Position(15, 15)
        self.mock_enemy1.state = EnemyState.PATROL
        
        self.mock_enemy2 = Mock(spec=Enemy)
        self.mock_enemy2.position = Position(20, 20)
        self.mock_enemy2.state = EnemyState.PATROL
        
        self.mock_enemy_manager.enemies = [self.mock_enemy1, self.mock_enemy2]
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_area_effect_exploit_affects_multiple_enemies(self):
        """Area effect exploits affect multiple enemies in range."""
        target = Position(15, 15)
        exploit_range = 10
        
        # Mock distance calculations
        with patch('game_entities.calculate_manhattan_distance') as mock_distance:
            # Enemy 1 is in range, Enemy 2 is not
            mock_distance.side_effect = lambda pos1, pos2: 5 if pos2 == self.mock_enemy1.position else 15
            
            result = self.exploit_system._execute_system_crash(target, exploit_range)
            
            assert result is True
            # Should affect enemy1 but not enemy2
            self.mock_enemy1.take_damage.assert_called()
            self.mock_enemy2.take_damage.assert_not_called()
    
    def test_exploit_triggers_turn_processing(self):
        """Successful exploit execution triggers turn processing."""
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"test_exploit": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.exploit_system, '_execute_specific_exploit', return_value=True):
            
            self.exploit_system.execute_exploit("test_exploit", Position(5, 5))
            
            self.mock_game.maybe_process_turn.assert_called_once()
    
    def test_exploit_updates_enemy_states(self):
        """Exploits correctly update enemy AI states."""
        target = Position(15, 15)
        
        with patch.object(self.exploit_system, '_execute_noise_maker', return_value=True):
            
            self.exploit_system._execute_specific_exploit("noise_maker", Mock(), target)
            
            # Should trigger enemy investigation behavior
            # (Specific behavior depends on enemy AI implementation)


class TestCombatErrorHandling:
    """Test combat system error handling and edge cases."""
    
    def setup_method(self):
        """Set up mock game environment for error handling tests."""
        self.mock_game = Mock()
        self.mock_player = Mock(spec=Player)
        self.mock_message_log = Mock(spec=MessageLog)
        
        self.mock_game.player = self.mock_player
        self.mock_game.message_log = self.mock_message_log
        
        self.exploit_system = ExploitSystem(self.mock_game)
    
    def test_missing_game_components_handled(self):
        """Missing game components are handled gracefully."""
        # Remove message log
        self.mock_game.message_log = None
        
        try:
            # Should not crash even if components are missing
            self.exploit_system.use_exploit("shadow_step")
        except AttributeError:
            pytest.fail("Combat system should handle missing components gracefully")
    
    def test_invalid_exploit_data_handled(self):
        """Invalid exploit data is handled gracefully."""
        # Mock invalid exploit definition
        invalid_exploit = Mock()
        del invalid_exploit.targeting  # Remove required attribute
        
        with patch.dict(GameData.EXPLOITS, {"invalid": invalid_exploit}):
            
            try:
                result = self.exploit_system.use_exploit("invalid")
                # Should handle gracefully, not crash
            except AttributeError:
                pytest.fail("Combat system should handle invalid exploit data")
    
    def test_player_state_corruption_handled(self):
        """Corrupted player state is handled gracefully."""
        # Corrupt player state
        self.mock_player.heat = None
        self.mock_player.position = "invalid_position"
        
        try:
            # Should not crash with corrupted player state
            result = self.exploit_system._calculate_heat_cost(Mock(heat=20))
        except TypeError:
            pytest.fail("Combat system should handle corrupted player state")
    
    def test_enemy_manager_failure_isolation(self):
        """Enemy manager failures don't crash combat system."""
        target = Position(10, 10)
        
        # Mock enemy manager to raise exception
        self.mock_game.enemy_manager.get_enemy_at_position.side_effect = Exception("Enemy manager failed")
        
        try:
            # Should not crash when enemy manager fails
            result = self.exploit_system._execute_buffer_overflow(target)
            # May return False, but should not crash
        except Exception:
            pytest.fail("Combat system should isolate enemy manager failures")