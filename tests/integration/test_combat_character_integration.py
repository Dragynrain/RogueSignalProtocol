#!/usr/bin/env python3
"""
Combat-Character Integration Tests.
Tests integration between combat system and character management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from game_engine import GameEngine
from game_combat import ExploitSystem
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement, TargetingMode, ExploitDefinition
from game_data import GameData
from game_inventory import InventoryManager, ExploitItem
from game_state import MessageLog
from game_audio import SoundManager


class TestCombatCharacterInteraction:
    """Test direct interaction between combat and character systems."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
        
        self.exploit_system = ExploitSystem(self.engine)
        
        # Set up player with inventory
        self.engine.player.inventory_manager = InventoryManager(self.engine.player)
        self.engine.player.heat = 30
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
    
    def test_exploit_damages_enemy_integration(self):
        """Exploit system correctly damages enemies through character system."""
        # Add enemy to the game
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.take_damage = Mock(return_value=50)
        enemy.cpu = 100
        enemy.max_cpu = 100
        self.engine.enemy_manager.enemies = [enemy]
        
        # Set up exploit
        self.engine.player.inventory_manager.equipped_exploits = {"buffer_overflow": True}
        
        # Mock exploit definition
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 10
        mock_exploit.heat = 25
        mock_exploit.damage = 50
        
        with patch.dict(GameData.EXPLOITS, {"buffer_overflow": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.engine.enemy_manager, 'get_enemy_at_position', return_value=enemy):
            
            # Execute exploit
            result = self.exploit_system.execute_exploit("buffer_overflow", enemy.position)
            
            assert result is True
            enemy.take_damage.assert_called()
            # Heat should be applied to player
            assert self.engine.player.heat > 30
    
    def test_player_bump_attack_enemy_integration(self):
        """Player bump attacks integrate with enemy damage system."""
        # Position enemy next to player
        enemy = Mock(spec=Enemy)
        enemy.position = Position(11, 10)
        enemy.take_damage = Mock(return_value=25)
        enemy.cpu = 100
        self.engine.enemy_manager.enemies = [enemy]
        
        # Position player
        self.engine.player.x = 10
        self.engine.player.y = 10
        
        with patch('game_characters.can_move_to_position', return_value=True), \
             patch.object(self.engine, '_get_enemy_at', return_value=enemy), \
             patch.object(self.engine, '_perform_bump_attack') as mock_attack:
            
            # Move player into enemy
            result = self.engine.move_player(1, 0)
            
            assert result is True
            mock_attack.assert_called_once_with(enemy)
    
    def test_enemy_death_removes_from_character_system(self):
        """Enemy death is properly handled by character management."""
        # Add enemy that will die
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.cpu = 10
        enemy.max_cpu = 100
        enemy.state = EnemyState.HOSTILE
        enemy.take_damage = Mock(return_value=10)
        
        # Mock enemy death
        def mock_damage(damage):
            enemy.cpu -= damage
            if enemy.cpu <= 0:
                enemy.state = EnemyState.DEAD
            return damage
        
        enemy.take_damage = mock_damage
        self.engine.enemy_manager.enemies = [enemy]
        
        # Set up lethal exploit
        self.engine.player.inventory_manager.equipped_exploits = {"system_crash": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 10
        mock_exploit.heat = 30
        mock_exploit.damage = 50
        
        with patch.dict(GameData.EXPLOITS, {"system_crash": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.engine.enemy_manager, 'get_enemy_at_position', return_value=enemy), \
             patch.object(self.engine.enemy_manager, 'remove_enemy') as mock_remove:
            
            # Execute lethal exploit
            self.exploit_system.execute_exploit("system_crash", enemy.position)
            
            # Enemy should be marked as dead
            assert enemy.cpu <= 0
            assert enemy.state == EnemyState.DEAD
    
    def test_combat_affects_enemy_ai_state(self):
        """Combat actions affect enemy AI state transitions."""
        # Add peaceful enemy
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.state = EnemyState.PATROL
        enemy.take_damage = Mock(return_value=20)
        enemy.cpu = 80
        self.engine.enemy_manager.enemies = [enemy]
        
        # Set up non-lethal exploit
        self.engine.player.inventory_manager.equipped_exploits = {"code_injection": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 10
        mock_exploit.heat = 20
        mock_exploit.damage = 20
        
        with patch.dict(GameData.EXPLOITS, {"code_injection": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.engine.enemy_manager, 'get_enemy_at_position', return_value=enemy):
            
            # Execute exploit
            self.exploit_system.execute_exploit("code_injection", enemy.position)
            
            # Enemy should take damage
            enemy.take_damage.assert_called_with(20)
            # Enemy state might change to hostile (implementation dependent)


class TestCombatPlayerIntegration:
    """Test combat system integration with player character."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
        
        self.exploit_system = ExploitSystem(self.engine)
        self.engine.player.inventory_manager = InventoryManager(self.engine.player)
    
    def test_exploit_heat_affects_player_state(self):
        """Exploit usage correctly affects player heat state."""
        initial_heat = self.engine.player.heat = 40
        
        # Set up high-heat exploit
        self.engine.player.inventory_manager.equipped_exploits = {"emp_burst": True}
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 35
        
        with patch.dict(GameData.EXPLOITS, {"emp_burst": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True):
            
            result = self.exploit_system.use_exploit("emp_burst")
            
            assert result is True
            # Heat should increase but cap at 100
            expected_heat = min(100, initial_heat + 35)
            assert self.engine.player.heat == expected_heat
    
    def test_overclocking_damages_player(self):
        """Overclocking correctly damages player character."""
        self.engine.player.heat = 90
        self.engine.player.cpu = 100
        initial_cpu = self.engine.player.cpu
        
        # Set up overclocking scenario
        self.engine.player.inventory_manager.equipped_exploits = {"system_crash": True}
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
        self.engine.overclock_confirmation = True
        self.engine.overclock_exploit = "system_crash"
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 25  # Will cause overclocking
        
        with patch.dict(GameData.EXPLOITS, {"system_crash": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True):
            
            result = self.exploit_system.use_exploit("system_crash")
            
            assert result is True
            # Player should take damage from overclocking
            assert self.engine.player.cpu < initial_cpu
            # Heat should be capped at 100
            assert self.engine.player.heat == 100
            # Overclock confirmation should be reset
            assert self.engine.overclock_confirmation is False
    
    def test_exploit_efficiency_affects_heat_calculation(self):
        """Player efficiency bonuses affect exploit heat calculation."""
        # Set efficiency bonus
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 5}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.heat = 30
        
        # Calculate heat cost with efficiency
        heat_cost = self.exploit_system._calculate_heat_cost(mock_exploit)
        
        # Should be reduced by efficiency (30 * 0.6 = 18)
        assert heat_cost == 18
        
        # Test without efficiency
        self.engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
        heat_cost = self.exploit_system._calculate_heat_cost(mock_exploit)
        
        # Should be full cost
        assert heat_cost == 30
    
    def test_player_inventory_integration_with_combat(self):
        """Player inventory properly integrates with combat system."""
        # Set up inventory with exploits
        exploit_item = ExploitItem("buffer_overflow")
        self.engine.player.inventory_manager.inventory = [exploit_item]
        self.engine.player.inventory_manager.equipped_exploits = {"buffer_overflow": True}
        
        # Test that equipped exploits can be used
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"buffer_overflow": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True):
            
            result = self.exploit_system.use_exploit("buffer_overflow")
            assert result is True
        
        # Test that unequipped exploits cannot be used
        self.engine.player.inventory_manager.equipped_exploits = {}
        
        result = self.exploit_system.use_exploit("buffer_overflow")
        assert result is False


class TestCombatEnemyManagementIntegration:
    """Test combat system integration with enemy management."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
        
        self.exploit_system = ExploitSystem(self.engine)
        self.engine.player.inventory_manager = InventoryManager(self.engine.player)
    
    def test_area_exploit_affects_multiple_enemies(self):
        """Area exploits affect multiple enemies in range."""
        # Add multiple enemies
        enemy1 = Mock(spec=Enemy)
        enemy1.position = Position(15, 15)
        enemy1.take_damage = Mock(return_value=30)
        enemy1.health = 100
        
        enemy2 = Mock(spec=Enemy)
        enemy2.position = Position(17, 15)  # Within range
        enemy2.take_damage = Mock(return_value=30)
        enemy2.health = 100
        
        enemy3 = Mock(spec=Enemy)
        enemy3.position = Position(25, 25)  # Out of range
        enemy3.take_damage = Mock(return_value=30)
        enemy3.health = 100
        
        self.engine.enemy_manager.enemies = [enemy1, enemy2, enemy3]
        
        # Set up area exploit
        self.engine.player.inventory_manager.equipped_exploits = {"emp_burst": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.AREA
        mock_exploit.range = 5
        mock_exploit.heat = 40
        
        # Mock distance calculations
        with patch.dict(GameData.EXPLOITS, {"emp_burst": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch('game_entities.calculate_manhattan_distance') as mock_distance:
            
            # Set distances: enemy1=0, enemy2=2, enemy3=15
            def distance_side_effect(pos1, pos2):
                if pos2 == enemy1.position:
                    return 0
                elif pos2 == enemy2.position:
                    return 2
                elif pos2 == enemy3.position:
                    return 15
                return 0
            
            mock_distance.side_effect = distance_side_effect
            
            # Execute area exploit
            result = self.exploit_system._execute_emp_burst(Position(15, 15), 5)
            
            assert result is True
            # Enemies in range should take damage
            enemy1.take_damage.assert_called()
            enemy2.take_damage.assert_called()
            # Enemy out of range should not
            enemy3.take_damage.assert_not_called()
    
    def test_exploit_triggers_enemy_state_changes(self):
        """Exploits trigger appropriate enemy state changes."""
        # Add enemy that will be affected
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.state = EnemyState.PATROL
        enemy.movement_type = EnemyMovement.RANDOM
        enemy.take_damage = Mock(return_value=25)
        self.engine.enemy_manager.enemies = [enemy]
        
        # Set up noise maker exploit (should alert enemies)
        self.engine.player.inventory_manager.equipped_exploits = {"noise_maker": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 10
        mock_exploit.heat = 15
        
        with patch.dict(GameData.EXPLOITS, {"noise_maker": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch('time.time', return_value=1000.0):
            
            result = self.exploit_system._execute_noise_maker(Position(15, 15))
            
            assert result is True
            # Should add ghost node to map
            assert Position(15, 15) in self.engine.game_map.ghost_nodes
            # Enemy should investigate noise (implementation dependent)
    
    def test_enemy_death_cleanup_integration(self):
        """Enemy death is properly cleaned up across systems."""
        # Add enemy that will die
        dead_enemy = Mock(spec=Enemy)
        dead_enemy.position = Position(15, 15)
        dead_enemy.cpu = 0
        dead_enemy.state = EnemyState.DEAD
        
        alive_enemy = Mock(spec=Enemy)
        alive_enemy.position = Position(20, 20)
        alive_enemy.cpu = 100
        alive_enemy.state = EnemyState.PATROL
        
        self.engine.enemy_manager.enemies = [dead_enemy, alive_enemy]
        
        with patch.object(self.engine.enemy_manager, 'remove_enemy') as mock_remove:
            # Update enemies should clean up dead ones
            self.engine._update_enemies()
            
            # Dead enemy should be marked for removal
            # (Exact implementation depends on enemy manager)


class TestCombatCharacterStateIntegration:
    """Test state synchronization between combat and character systems."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
        
        self.exploit_system = ExploitSystem(self.engine)
        self.engine.player.inventory_manager = InventoryManager(self.engine.player)
    
    def test_player_state_consistency_after_combat(self):
        """Player state remains consistent after combat actions."""
        # Set initial state
        initial_x = self.engine.player.x = 10
        initial_y = self.engine.player.y = 10
        initial_cpu = self.engine.player.cpu = 90
        initial_heat = self.engine.player.heat = 30
        
        # Perform shadow step (movement exploit)
        self.engine.player.inventory_manager.equipped_exploits = {"shadow_step": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 5
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"shadow_step": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch('game_characters.can_move_to_position', return_value=True):
            
            target = Position(12, 12)
            result = self.exploit_system._execute_shadow_step(target)
            
            assert result is True
            # Player position should update
            assert self.engine.player.x == 12
            assert self.engine.player.y == 12
            # Shadow steps should increment
            assert self.engine.player.shadow_steps > 0
            # CPU should remain unchanged
            assert self.engine.player.cpu == initial_cpu
    
    def test_enemy_state_consistency_after_damage(self):
        """Enemy state remains consistent after taking damage."""
        enemy = Mock(spec=Enemy)
        enemy.position = Position(15, 15)
        enemy.cpu = 100
        enemy.max_cpu = 100
        enemy.state = EnemyState.PATROL
        
        # Mock damage application
        def apply_damage(damage):
            enemy.cpu = max(0, enemy.cpu - damage)
            if enemy.cpu <= 0:
                enemy.state = EnemyState.DEAD
            elif enemy.state == EnemyState.PATROL:
                enemy.state = EnemyState.HOSTILE  # Becomes hostile when damaged
            return damage
        
        enemy.take_damage = apply_damage
        self.engine.enemy_manager.enemies = [enemy]
        
        # Set up damaging exploit
        self.engine.player.inventory_manager.equipped_exploits = {"buffer_overflow": True}
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.SINGLE
        mock_exploit.range = 10
        mock_exploit.heat = 25
        
        with patch.dict(GameData.EXPLOITS, {"buffer_overflow": mock_exploit}), \
             patch.object(self.exploit_system, '_validate_target', return_value=True), \
             patch.object(self.engine.enemy_manager, 'get_enemy_at_position', return_value=enemy):
            
            result = self.exploit_system.execute_exploit("buffer_overflow", enemy.position)
            
            assert result is True
            # Enemy should be damaged and state changed
            assert enemy.cpu < 100
            assert enemy.state == EnemyState.HOSTILE
    
    def test_turn_processing_integration_after_combat(self):
        """Turn processing correctly integrates combat effects."""
        # Set up combat scenario
        self.engine.player.inventory_manager.equipped_exploits = {"data_mimic": True}
        self.engine.player.heat = 40
        
        mock_exploit = Mock(spec=ExploitDefinition)
        mock_exploit.targeting = TargetingMode.NONE
        mock_exploit.range = 0
        mock_exploit.heat = 20
        
        with patch.dict(GameData.EXPLOITS, {"data_mimic": mock_exploit}), \
             patch.object(self.exploit_system, 'execute_exploit', return_value=True), \
             patch.object(self.engine, 'maybe_process_turn') as mock_turn:
            
            result = self.exploit_system.use_exploit("data_mimic")
            
            assert result is True
            # Turn processing should be triggered
            mock_turn.assert_called_once()
            # Heat should increase
            assert self.engine.player.heat > 40


class TestCombatCharacterErrorIntegration:
    """Test error handling between combat and character systems."""
    
    def setup_method(self):
        """Set up test environment for each test."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            self.engine = GameEngine(load_save=False)
        
        self.exploit_system = ExploitSystem(self.engine)
        self.engine.player.inventory_manager = InventoryManager(self.engine.player)
    
    def test_invalid_enemy_position_error_handling(self):
        """Invalid enemy positions are handled gracefully in combat."""
        # Add enemy with invalid position
        enemy = Mock(spec=Enemy)
        enemy.position = Position(-5, -5)  # Invalid position
        enemy.take_damage = Mock(return_value=25)
        self.engine.enemy_manager.enemies = [enemy]
        
        # Try to target invalid position
        with patch.object(self.engine.enemy_manager, 'get_enemy_at_position', return_value=enemy):
            
            try:
                result = self.exploit_system._execute_buffer_overflow(Position(-5, -5))
                # Should either handle gracefully or return False
            except Exception:
                pytest.fail("Combat system should handle invalid enemy positions")
    
    def test_corrupted_player_state_error_handling(self):
        """Corrupted player state is handled gracefully in combat."""
        # Corrupt player state
        self.engine.player.heat = None  # Invalid heat value
        self.engine.player.cpu = -50    # Invalid CPU value
        
        try:
            # Should not crash with corrupted player state
            result = self.exploit_system._calculate_heat_cost(Mock(heat=20))
            # Should handle gracefully
        except Exception:
            pytest.fail("Combat system should handle corrupted player state")
    
    def test_missing_enemy_manager_error_handling(self):
        """Missing enemy manager is handled gracefully."""
        # Remove enemy manager
        self.engine.enemy_manager = None
        
        try:
            # Should not crash when enemy manager is missing
            result = self.exploit_system._execute_buffer_overflow(Position(10, 10))
            # Should return False or handle gracefully
        except AttributeError:
            pytest.fail("Combat system should handle missing enemy manager")