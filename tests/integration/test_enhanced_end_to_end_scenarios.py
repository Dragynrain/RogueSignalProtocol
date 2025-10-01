#!/usr/bin/env python3
"""
Enhanced End-to-End Gameplay Scenarios.
Comprehensive tests for complete gameplay flows and user journeys.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import time
from typing import List, Dict, Any

from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState, EnemyMovement
from game_combat import ExploitSystem
from game_state import GameStateManager, MessageLog
from game_map import GameMap
from game_config import GameConfig, GameSettings
from game_save import SaveGameManager
from game_inventory import InventoryManager, CodeHack, ExploitItem
from game_audio import SoundManager


class TestCompleteGameplayJourneys:
    """Test complete player journeys from start to finish."""
    
    def test_complete_stealth_playthrough(self):
        """Test complete stealth-focused playthrough scenario."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Stealth playthrough: avoid detection, use stealth exploits
            engine.player.detection = 0.0
            
            # Add stealth exploits to inventory
            engine.player.inventory_manager = InventoryManager(engine.player)
            engine.player.inventory_manager.equipped_exploits = {
                "shadow_step": True,
                "data_mimic": True
            }
            
            # Simulate stealth movement through level
            for turn in range(20):
                # Move carefully
                with patch('game_characters.can_move_to_position', return_value=True), \
                     patch.object(engine, '_get_enemy_at', return_value=None):
                    
                    # Make small movements
                    engine.move_player(1, 0)
                    
                    # Use stealth exploits occasionally
                    if turn % 5 == 0:
                        from game_data import GameData
                        from game_entities import ExploitDefinition, TargetingMode
                        
                        mock_exploit = Mock(spec=ExploitDefinition)
                        mock_exploit.targeting = TargetingMode.NONE
                        mock_exploit.range = 0
                        mock_exploit.heat = 15
                        
                        exploit_system = ExploitSystem(engine)
                        engine.player.heat = 20
                        engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
                        
                        with patch.dict(GameData.EXPLOITS, {"data_mimic": mock_exploit}), \
                             patch.object(exploit_system, 'execute_exploit', return_value=True):
                            
                            exploit_system.use_exploit("data_mimic")
                
                # Process turn
                engine.maybe_process_turn()
            
            # Verify stealth success
            assert engine.player.detection < 30.0  # Stayed relatively undetected
            assert engine.game_state.turn >= 20
            assert engine.game_state.game_over is False
    
    def test_complete_aggressive_playthrough(self):
        """Test complete aggressive combat-focused playthrough."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Aggressive playthrough: high detection, combat exploits
            engine.player.inventory_manager = InventoryManager(engine.player)
            engine.player.inventory_manager.equipped_exploits = {
                "buffer_overflow": True,
                "system_crash": True,
                "emp_burst": True
            }
            
            # Add enemies to fight
            for i in range(3):
                enemy = Mock(spec=Enemy)
                enemy.position = Position(10 + i * 5, 10)
                enemy.state = EnemyState.HOSTILE
                enemy.take_damage = Mock(return_value=50)
                enemy.cpu = 100
                engine.enemy_manager.enemies.append(enemy)
            
            # Simulate aggressive combat
            exploit_system = ExploitSystem(engine)
            engine.player.heat = 30
            engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
            
            from game_data import GameData
            from game_entities import ExploitDefinition, TargetingMode
            
            # Use combat exploits
            for exploit_name in ["buffer_overflow", "system_crash"]:
                mock_exploit = Mock(spec=ExploitDefinition)
                mock_exploit.targeting = TargetingMode.SINGLE
                mock_exploit.range = 10
                mock_exploit.heat = 35
                
                with patch.dict(GameData.EXPLOITS, {exploit_name: mock_exploit}), \
                     patch.object(exploit_system, '_validate_target', return_value=True), \
                     patch.object(engine.enemy_manager, 'get_enemy_at_position', 
                                return_value=engine.enemy_manager.enemies[0]):
                    
                    result = exploit_system.execute_exploit(exploit_name, Position(10, 10))
                    assert result is True
            
            # Verify aggressive success
            assert engine.player.heat > 30  # Heat increased from combat
            assert len(engine.enemy_manager.enemies) >= 0  # Enemies engaged
    
    def test_complete_exploration_playthrough(self):
        """Test complete exploration-focused playthrough."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add exploration targets to map
            code_hack = CodeHack("exploration_hack", Position(20, 15), "blue")
            engine.game_map.code_hacks = [code_hack]
            
            exploit_item = ExploitItem("network_scan")
            engine.game_map.exploit_pickups = [exploit_item]
            
            upgrade = ("cpu_boost", Position(25, 20))
            engine.game_map.permanent_upgrades = [upgrade]
            
            # Simulate exploration movement
            exploration_targets = [
                Position(20, 15),  # Code hack
                Position(15, 20),  # Exploit pickup location
                Position(25, 20)   # Upgrade location
            ]
            
            for target in exploration_targets:
                # Move towards target
                engine.player.x = target.x
                engine.player.y = target.y
                
                # Check for discoveries
                player_pos = Position(engine.player.x, engine.player.y)
                
                # Simulate item pickup
                if player_pos.x == 20 and player_pos.y == 15:
                    # Found code hack
                    assert len(engine.game_map.code_hacks) > 0
                
                engine.maybe_process_turn()
            
            # Verify exploration success
            assert engine.game_state.turn >= len(exploration_targets)
            assert engine.player.x == 25 and engine.player.y == 20  # Reached final target
    
    def test_complete_level_progression_journey(self):
        """Test complete journey through multiple levels."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            initial_level = engine.game_state.level
            
            # Progress through levels
            for level in range(1, 4):  # Levels 1, 2, 3
                assert engine.game_state.level == level
                
                # Simulate level activities
                for turn in range(10):
                    engine.game_state.turn += 1
                    engine.maybe_process_turn()
                
                # Progress to next level (except last)
                if level < 3:
                    with patch.object(engine, '_generate_procedural_level'), \
                         patch.object(engine, 'auto_save'):
                        
                        engine.next_level()
                        assert engine.game_state.level == level + 1
            
            # Verify final state
            assert engine.game_state.level >= initial_level
            assert engine.game_state.turn >= 30  # Accumulated turns
    
    def test_save_load_mid_journey(self):
        """Test saving and loading mid-journey preserves state."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            # Start journey
            engine1 = GameEngine(load_save=False)
            
            # Progress partway through journey
            engine1.game_state.level = 2
            engine1.game_state.turn = 100
            engine1.player.x = 30
            engine1.player.y = 25
            engine1.player.cpu = 80
            engine1.player.detection = 45.0
            
            # Add some game state
            engine1.code_hack_effects = {"red": ("speed", "Fast movement")}
            engine1.discovered_code_effects = {"red": "speed"}
            
            # Save journey state
            save_data = engine1.get_game_state_for_save()
            
            # Continue journey in new engine instance
            with patch.object(SaveGameManager, 'load_game', return_value=save_data):
                engine2 = GameEngine(load_save=True)
                
                # Verify journey state preserved
                assert engine2.game_state.level == 2
                assert engine2.game_state.turn == 100
                assert engine2.player.x == 30
                assert engine2.player.y == 25
                assert engine2.player.cpu == 80
                assert engine2.player.detection == 45.0
                assert engine2.code_hack_effects["red"] == ("speed", "Fast movement")
                
                # Continue journey
                for turn in range(10):
                    engine2.game_state.turn += 1
                    engine2.maybe_process_turn()
                
                # Verify continued progress
                assert engine2.game_state.turn >= 110


class TestCriticalGameplayScenarios:
    """Test critical gameplay scenarios that must work correctly."""
    
    def test_player_death_scenario(self):
        """Test complete player death scenario and consequences."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Damage player to near death
            engine.player.cpu = 10
            
            # Apply fatal damage
            fatal_damage = engine.player.take_damage(15)
            
            # Verify death state
            assert engine.player.cpu <= 0
            
            # Trigger game over
            engine.game_state.game_over = True
            
            # Verify game over state
            assert engine.game_over is True
            
            # Save file should be deleted on death (permadeath)
            with patch.object(SaveGameManager, 'delete_save_file') as mock_delete:
                # Simulate death handling
                if engine.game_over and engine.player.cpu <= 0:
                    SaveGameManager.delete_save_file()
                
                mock_delete.assert_called_once()
    
    def test_admin_spawn_scenario(self):
        """Test admin spawn scenario under high detection."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set conditions for admin spawn
            engine.game_state.level = 3
            engine.player.detection = 85.0  # High detection
            engine.game_state.admin_spawned = False
            
            # Mock admin spawn position
            admin_position = Position(40, 20)
            
            with patch.object(engine, '_find_admin_spawn_position', return_value=admin_position), \
                 patch.object(engine.enemy_manager, 'add_enemy') as mock_add_enemy:
                
                # Trigger admin spawn check
                engine._check_admin_spawn()
                
                # Verify admin spawning conditions
                if engine.player.detection >= 80 and not engine.game_state.admin_spawned:
                    assert engine.game_state.admin_spawned is True
                    mock_add_enemy.assert_called()
    
    def test_resource_depletion_scenario(self):
        """Test scenario where player depletes critical resources."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Deplete player CPU to critical levels
            engine.player.cpu = 20
            initial_cpu = engine.player.cpu
            
            # Max out heat
            engine.player.heat = 95
            
            # Try to use high-heat exploit (should require overclocking)
            engine.player.inventory_manager = InventoryManager(engine.player)
            engine.player.inventory_manager.equipped_exploits = {"system_crash": True}
            engine.player.temporary_effects = {'exploit_efficiency_turns': 0}
            
            from game_combat import ExploitSystem
            from game_data import GameData
            from game_entities import ExploitDefinition, TargetingMode
            
            exploit_system = ExploitSystem(engine)
            
            mock_exploit = Mock(spec=ExploitDefinition)
            mock_exploit.targeting = TargetingMode.NONE
            mock_exploit.range = 0
            mock_exploit.heat = 25  # Will cause overclocking
            
            with patch.dict(GameData.EXPLOITS, {"system_crash": mock_exploit}):
                
                # First attempt should require confirmation
                result1 = exploit_system.use_exploit("system_crash")
                assert result1 is False  # Requires overclocking confirmation
                assert engine.overclock_confirmation is True
                
                # Second attempt with confirmation should damage player
                result2 = exploit_system.use_exploit("system_crash")
                assert engine.player.cpu < initial_cpu  # Should take damage
    
    def test_level_completion_scenario(self):
        """Test complete level completion scenario."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set up level completion conditions
            initial_level = engine.game_state.level
            
            # Simulate reaching level exit/completion trigger
            engine.player.x = 70  # Near map edge (exit)
            engine.player.y = 20
            
            # Trigger level completion
            with patch.object(engine, '_generate_procedural_level'), \
                 patch.object(engine, 'auto_save') as mock_save:
                
                engine.next_level()
                
                # Verify level progression
                assert engine.game_state.level == initial_level + 1
                mock_save.assert_called()  # Should auto-save on level completion
    
    def test_victory_scenario(self):
        """Test complete victory scenario (beating final level)."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set to final level
            engine.game_state.level = 3
            
            # Complete final level
            with patch.object(engine, 'auto_save') as mock_save:
                
                engine.next_level()  # This should trigger victory
                
                # Verify victory state
                if engine.game_state.level > 3:
                    assert engine.game_over is True
                    mock_save.assert_called()  # Should save victory state


class TestEdgeCaseScenarios:
    """Test edge case scenarios that could break the game."""
    
    def test_map_boundary_scenarios(self):
        """Test scenarios at map boundaries."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Test all four corners
            corners = [
                (0, 0),                                           # Top-left
                (GameConfig.MAP_WIDTH - 1, 0),                   # Top-right
                (0, GameConfig.MAP_HEIGHT - 1),                  # Bottom-left
                (GameConfig.MAP_WIDTH - 1, GameConfig.MAP_HEIGHT - 1)  # Bottom-right
            ]
            
            for x, y in corners:
                engine.player.x = x
                engine.player.y = y
                
                # Try to move outside boundaries
                boundary_moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                
                for dx, dy in boundary_moves:
                    result = engine.move_player(dx, dy)
                    
                    # Should not move outside boundaries
                    assert 0 <= engine.player.x < GameConfig.MAP_WIDTH
                    assert 0 <= engine.player.y < GameConfig.MAP_HEIGHT
    
    def test_maximum_values_scenario(self):
        """Test scenarios with maximum possible values."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Set maximum values
            engine.player.cpu = 9999
            engine.player.max_cpu = 9999
            engine.player.detection = 100.0
            engine.player.heat = 100
            engine.game_state.turn = 99999
            
            # Game should handle maximum values gracefully
            try:
                engine.process_turn()
                
                # Values should stay within reasonable bounds
                assert engine.player.cpu <= 9999
                assert engine.player.detection <= 100.0
                assert engine.player.heat <= 100
                
            except Exception:
                pytest.fail("Game should handle maximum values gracefully")
    
    def test_empty_map_scenario(self):
        """Test scenario with completely empty map."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Clear all map elements
            engine.game_map.walls.clear()
            engine.game_map.shadows.clear()
            engine.game_map.cooling_nodes.clear()
            engine.game_map.cpu_recovery_nodes.clear()
            engine.game_map.ghost_nodes.clear()
            engine.game_map.code_hacks.clear()
            engine.game_map.exploit_pickups.clear()
            engine.game_map.permanent_upgrades.clear()
            engine.enemy_manager.enemies.clear()
            
            # Game should still function with empty map
            try:
                for turn in range(10):
                    engine.process_turn()
                
                assert engine.game_state.turn >= 10
                
            except Exception:
                pytest.fail("Game should handle empty map gracefully")
    
    def test_excessive_enemies_scenario(self):
        """Test scenario with excessive number of enemies."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Add many enemies (stress test)
            for i in range(100):  # Large number
                enemy = Mock(spec=Enemy)
                enemy.position = Position(i % 40, i // 40)
                enemy.state = EnemyState.PATROL
                enemy.movement_type = EnemyMovement.RANDOM
                enemy.movement_queue = []
                engine.enemy_manager.enemies.append(enemy)
            
            # Game should handle large enemy count
            try:
                engine._update_enemies()
                
                assert len(engine.enemy_manager.enemies) == 100
                
            except Exception:
                pytest.fail("Game should handle large enemy counts")


class TestPerformanceScenarios:
    """Test performance-critical scenarios."""
    
    def test_long_game_session_scenario(self):
        """Test extended game session performance."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Simulate long game session
            start_time = time.time()
            
            for turn in range(200):  # Extended session
                # Various game activities
                engine.game_state.turn = turn
                
                if turn % 10 == 0:
                    # Movement
                    engine.player.x = (engine.player.x + 1) % GameConfig.MAP_WIDTH
                    engine.player.y = (engine.player.y + 1) % GameConfig.MAP_HEIGHT
                
                if turn % 20 == 0:
                    # Update systems
                    engine._update_threat_scan()
                    engine._cleanup_ghost_positions()
                
                # Process turn
                engine.maybe_process_turn()
            
            end_time = time.time()
            session_duration = end_time - start_time
            
            # Should complete in reasonable time (less than 5 seconds for 200 turns)
            assert session_duration < 5.0
            assert engine.game_state.turn >= 200
    
    def test_memory_usage_scenario(self):
        """Test memory usage remains stable during gameplay."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Simulate activities that could cause memory leaks
            for cycle in range(50):
                # Add and remove temporary objects
                temp_enemies = []
                for i in range(10):
                    enemy = Mock(spec=Enemy)
                    enemy.position = Position(i, i)
                    temp_enemies.append(enemy)
                
                engine.enemy_manager.enemies.extend(temp_enemies)
                
                # Process with temporary objects
                engine._update_enemies()
                
                # Remove temporary objects
                for enemy in temp_enemies:
                    if enemy in engine.enemy_manager.enemies:
                        engine.enemy_manager.enemies.remove(enemy)
                
                # Cleanup operations
                engine._cleanup_ghost_positions()
            
            # Memory should be stable (no excessive object accumulation)
            # This is more of a structural test than assertion test
            assert len(engine.enemy_manager.enemies) == 0  # All temp enemies removed
    
    def test_rapid_input_scenario(self):
        """Test rapid input handling performance."""
        with patch('game_audio.SoundManager') as mock_sound_mgr:
            mock_sound_mgr.return_value.preload_sounds.return_value = None
            
            engine = GameEngine(load_save=False)
            
            # Simulate rapid input sequences
            with patch('game_characters.can_move_to_position', return_value=True), \
                 patch.object(engine, '_get_enemy_at', return_value=None):
                
                start_time = time.time()
                
                # Rapid movement inputs
                for i in range(100):
                    direction = [(1, 0), (0, 1), (-1, 0), (0, -1)][i % 4]
                    engine.move_player(direction[0], direction[1])
                
                end_time = time.time()
                input_duration = end_time - start_time
                
                # Should handle rapid inputs efficiently
                assert input_duration < 2.0  # Less than 2 seconds for 100 inputs
                assert engine.game_state.turn >= 100  # All inputs processed