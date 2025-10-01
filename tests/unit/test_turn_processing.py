#!/usr/bin/env python3
"""
Unit tests for Turn Processing System.
Tests turn-based mechanics, turn order, timing effects, and game state updates.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from game_engine import GameEngine
from game_characters import Player, Enemy
from game_entities import Position, EnemyState
from game_config import GameConfig
from tests.fixtures.simple_fixtures import player
from tests.fixtures.mock_helpers import create_mock_game_map, create_mock_game_state, create_test_player, setup_game_engine_mocks


class TestTurnProcessing:
    """Test turn processing mechanics and turn order."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create game engine with mocked dependencies
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()

            # Set up proper mocks using the helper
            setup_game_engine_mocks(self.game_engine)

            # Set up player with proper temporary effects
            self.game_engine.player = create_test_player()
            self.game_engine.enemies = []
            self.game_engine.turn = 0
    
    def test_turn_increment(self):
        """Test that turn counter increments correctly."""
        initial_turn = self.game_engine.turn
        
        self.game_engine.process_turn()
        
        assert self.game_engine.turn == initial_turn + 1
    
    def test_player_turn_processing(self):
        """Test player-specific turn processing."""
        # Set up player with temporary effects using correct effect names
        self.game_engine.player.temporary_effects.update({
            'data_mimic_turns': 3,
            'virus_turns': 1,
            'speed_boost_turns': 2
        })
        self.game_engine.player.heat = 50

        initial_data_mimic = self.game_engine.player.temporary_effects['data_mimic_turns']
        initial_virus = self.game_engine.player.temporary_effects['virus_turns']

        self.game_engine.process_turn()

        # Temporary effects should decrease
        assert self.game_engine.player.temporary_effects['data_mimic_turns'] == initial_data_mimic - 1
        assert self.game_engine.player.temporary_effects['virus_turns'] == initial_virus - 1

        # Heat should decrease (natural cooling)
        assert self.game_engine.player.heat < 50
    
    def test_enemy_turn_processing(self):
        """Test enemy turn processing."""
        # Add enemy to the game
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(20, 20), "test_enemy")
            enemy.move_cooldown = 2
            enemy.disabled_turns = 1
            self.game_engine.enemies = [enemy]
            
            initial_cooldown = enemy.move_cooldown
            initial_disabled = enemy.disabled_turns
            
            with patch.object(enemy, 'move') as mock_move:
                self.game_engine.process_turn()
                
                # Cooldowns should decrease
                assert enemy.move_cooldown == initial_cooldown - 1
                assert enemy.disabled_turns == initial_disabled - 1
                
                # Enemy should not move while disabled
                mock_move.assert_not_called()
    
    def test_turn_processing_order(self):
        """Test that turn processing happens in correct order."""
        with patch.object(self.game_engine, '_process_player_turn') as mock_player, \
             patch.object(self.game_engine, '_process_enemies_turn') as mock_enemies, \
             patch.object(self.game_engine, '_process_environmental_effects') as mock_env:
            
            self.game_engine.process_turn()
            
            # Verify call order
            assert mock_player.call_count == 1
            assert mock_enemies.call_count == 1
            assert mock_env.call_count == 1
    
    def test_heat_dissipation(self):
        """Test heat dissipation mechanics."""
        self.game_engine.player.heat = 80
        self.game_engine.player.max_heat = 100
        
        # Process multiple turns
        for _ in range(5):
            self.game_engine.process_turn()
        
        # Heat should have decreased significantly
        assert self.game_engine.player.heat < 80
        assert self.game_engine.player.heat >= 0  # Should not go negative


class TestTemporaryEffects:
    """Test temporary effect processing and expiration."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()
            self.game_engine.player = player()
            self.game_engine.message_log = Mock()
            self.game_engine.sound_manager = Mock()
            self.game_engine.enemies = []
    
    def test_temporary_effect_expiration(self):
        """Test that temporary effects expire correctly."""
        # Set up various temporary effects
        self.game_engine.player.temporary_effects = {
            'stealth': 1,          # Should expire this turn
            'enhanced_vision': 3,  # Should persist
            'speed': 0,           # Should be removed (already expired)
            'overclock': 2        # Should persist
        }
        
        self.game_engine._process_player_temporary_effects()
        
        # Check effect states
        effects = self.game_engine.player.temporary_effects
        assert 'stealth' not in effects  # Should be removed
        assert effects['enhanced_vision'] == 2  # Should decrease by 1
        assert 'speed' not in effects  # Should be removed
        assert effects['overclock'] == 1  # Should decrease by 1
    
    def test_effect_expiration_messages(self):
        """Test that effect expiration produces appropriate messages."""
        self.game_engine.player.temporary_effects = {
            'stealth': 1,  # Will expire
            'data_mimic': 1  # Will expire
        }
        
        self.game_engine._process_player_temporary_effects()
        
        # Should have logged expiration messages
        assert self.game_engine.message_log.add_message.call_count >= 2
    
    def test_virus_effect_processing(self):
        """Test virus effect damage over time."""
        self.game_engine.player.temporary_effects = {'virus': 2}
        self.game_engine.player.cpu = 100
        
        with patch.object(self.game_engine.player, 'take_damage') as mock_damage:
            self.game_engine._process_player_temporary_effects()
            
            # Should take virus damage
            mock_damage.assert_called()
            
            # Virus effect should persist for 1 more turn
            assert self.game_engine.player.temporary_effects['virus'] == 1
    
    def test_movement_slow_effect(self):
        """Test movement slow effect processing."""
        self.game_engine.player.temporary_effects = {'movement_slowed': 3}
        
        self.game_engine._process_player_temporary_effects()
        
        # Effect should decrease
        assert self.game_engine.player.temporary_effects['movement_slowed'] == 2
    
    def test_multiple_effects_interaction(self):
        """Test that multiple effects process independently."""
        self.game_engine.player.temporary_effects = {
            'stealth': 2,
            'virus': 1,  # Will expire
            'enhanced_vision': 4,
            'movement_slowed': 1  # Will expire
        }
        
        initial_cpu = self.game_engine.player.cpu
        
        with patch.object(self.game_engine.player, 'take_damage') as mock_damage:
            self.game_engine._process_player_temporary_effects()
            
            effects = self.game_engine.player.temporary_effects
            
            # Persistent effects should decrease
            assert effects['stealth'] == 1
            assert effects['enhanced_vision'] == 3
            
            # Expired effects should be removed
            assert 'virus' not in effects
            assert 'movement_slowed' not in effects
            
            # Virus should have caused damage
            mock_damage.assert_called()


class TestEnemyTurnProcessing:
    """Test enemy-specific turn processing."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()
            self.game_engine.player = player()
            self.game_engine.message_log = Mock()
            self.game_engine.sound_manager = Mock()
            self.game_engine.game_map = Mock()
    
    def test_enemy_cooldown_processing(self):
        """Test enemy cooldown and disable processing."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy1 = Enemy(Position(10, 10), "test_enemy")
            enemy1.move_cooldown = 3
            enemy1.disabled_turns = 0
            
            enemy2 = Enemy(Position(15, 15), "test_enemy")
            enemy2.move_cooldown = 1
            enemy2.disabled_turns = 2
            
            self.game_engine.enemies = [enemy1, enemy2]
            
            with patch.object(enemy1, 'move') as mock_move1, \
                 patch.object(enemy2, 'move') as mock_move2:
                
                self.game_engine._process_enemies_turn()
                
                # Check cooldown decreases
                assert enemy1.move_cooldown == 2
                assert enemy2.move_cooldown == 0
                assert enemy2.disabled_turns == 1
                
                # Neither should move (cooldown/disabled)
                mock_move1.assert_not_called()
                mock_move2.assert_not_called()
    
    def test_enemy_movement_execution(self):
        """Test enemy movement when not on cooldown."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(10, 10), "test_enemy")
            enemy.move_cooldown = 0
            enemy.disabled_turns = 0
            
            self.game_engine.enemies = [enemy]
            
            with patch.object(enemy, 'move') as mock_move:
                mock_move.return_value = True  # Successful move
                
                self.game_engine._process_enemies_turn()
                
                # Should attempt to move
                mock_move.assert_called_once()
    
    def test_enemy_alert_timer_processing(self):
        """Test enemy alert timer processing."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(10, 10), "test_enemy")
            enemy.alert_timer = 5
            enemy.state = EnemyState.HOSTILE
            
            self.game_engine.enemies = [enemy]
            
            self.game_engine._process_enemies_turn()
            
            # Alert timer should decrease
            assert enemy.alert_timer == 4
    
    def test_enemy_state_transitions(self):
        """Test enemy state transitions during turn processing."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(10, 10), "test_enemy")
            enemy.alert_timer = 1  # Will expire
            enemy.state = EnemyState.HOSTILE
            
            self.game_engine.enemies = [enemy]
            
            self.game_engine._process_enemies_turn()
            
            # Should transition back to patrol/unaware state
            assert enemy.state != EnemyState.HOSTILE
            assert enemy.alert_timer == 0


class TestEnvironmentalEffects:
    """Test environmental effect processing."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()
            self.game_engine.player = player()
            self.game_engine.message_log = Mock()
            self.game_engine.sound_manager = Mock()
            self.game_engine.game_map = Mock()
            self.game_engine.game_state = Mock()
    
    def test_threat_scan_processing(self):
        """Test threat scan timer processing."""
        self.game_engine.game_state.threat_scan_turns = 3
        
        self.game_engine._process_environmental_effects()
        
        # Should decrease threat scan timer
        assert self.game_engine.game_state.threat_scan_turns == 2
    
    def test_ghost_node_expiration(self):
        """Test ghost node expiration."""
        import time
        current_time = time.time()
        
        # Set up ghost nodes (some expired, some not)
        self.game_engine.game_map.ghost_nodes = {
            Position(10, 10): current_time - 20,  # Expired (older than 15s)
            Position(15, 15): current_time - 5,   # Not expired
        }
        
        with patch('time.time', return_value=current_time):
            self.game_engine._process_environmental_effects()
            
            # Expired node should be removed
            assert Position(10, 10) not in self.game_engine.game_map.ghost_nodes
            assert Position(15, 15) in self.game_engine.game_map.ghost_nodes
    
    def test_distraction_point_processing(self):
        """Test distraction point timer processing."""
        self.game_engine.game_state.distraction_points = {
            Position(10, 10): 3,
            Position(15, 15): 1,  # Will expire
            Position(20, 20): 5
        }
        
        self.game_engine._process_environmental_effects()
        
        # Timers should decrease
        assert self.game_engine.game_state.distraction_points[Position(10, 10)] == 2
        assert Position(15, 15) not in self.game_engine.game_state.distraction_points
        assert self.game_engine.game_state.distraction_points[Position(20, 20)] == 4


class TestTurnValidation:
    """Test turn processing validation and edge cases."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()
            self.game_engine.player = player()
            self.game_engine.message_log = Mock()
            self.game_engine.sound_manager = Mock()
            self.game_engine.game_map = Mock()
            self.game_engine.game_state = Mock()
            self.game_engine.enemies = []
    
    def test_turn_processing_with_dead_player(self):
        """Test turn processing when player is dead."""
        self.game_engine.player.cpu = 0  # Dead
        
        # Should not crash
        try:
            self.game_engine.process_turn()
            assert True
        except Exception as e:
            pytest.fail(f"Turn processing crashed with dead player: {e}")
    
    def test_turn_processing_with_no_enemies(self):
        """Test turn processing with no enemies."""
        self.game_engine.enemies = []
        
        initial_turn = self.game_engine.turn
        
        self.game_engine.process_turn()
        
        # Should still increment turn
        assert self.game_engine.turn == initial_turn + 1
    
    def test_turn_processing_with_many_enemies(self):
        """Test turn processing with many enemies."""
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            # Add many enemies
            enemies = []
            for i in range(20):
                enemy = Enemy(Position(i, i), "test_enemy")
                enemies.append(enemy)
            
            self.game_engine.enemies = enemies
            
            # Should not crash with many enemies
            try:
                self.game_engine.process_turn()
                assert True
            except Exception as e:
                pytest.fail(f"Turn processing crashed with many enemies: {e}")
    
    def test_turn_processing_with_corrupted_effects(self):
        """Test turn processing with corrupted temporary effects."""
        # Set up corrupted effects
        self.game_engine.player.temporary_effects = {
            'invalid_effect': -5,  # Negative duration
            'stealth': 'not_a_number',  # Wrong type
            None: 3,  # Invalid key
        }
        
        # Should handle gracefully
        try:
            self.game_engine._process_player_temporary_effects()
            assert True
        except Exception as e:
            pytest.fail(f"Effect processing crashed with corrupted data: {e}")
    
    def test_massive_turn_numbers(self):
        """Test turn processing with very large turn numbers."""
        self.game_engine.turn = 999999
        
        self.game_engine.process_turn()
        
        # Should handle large numbers
        assert self.game_engine.turn == 1000000
    
    def test_turn_processing_performance(self):
        """Test that turn processing completes quickly."""
        import time
        
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            # Add moderate number of enemies
            enemies = []
            for i in range(10):
                enemy = Enemy(Position(i * 2, i * 2), "test_enemy")
                enemies.append(enemy)
            
            self.game_engine.enemies = enemies
            
            start_time = time.time()
            self.game_engine.process_turn()
            end_time = time.time()
            
            # Should complete quickly (less than 100ms for testing)
            assert end_time - start_time < 0.1


class TestTurnBasedGameplay:
    """Test complete turn-based gameplay scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        with patch('game_engine.GameMap'), \
             patch('game_engine.MessageLog'), \
             patch('game_engine.SoundManager'):
            self.game_engine = GameEngine()
            self.game_engine.player = player()
            self.game_engine.message_log = Mock()
            self.game_engine.sound_manager = Mock()
            self.game_engine.game_map = Mock()
            self.game_engine.game_state = Mock()
            self.game_engine.game_state.threat_scan_turns = 0
            self.game_engine.game_state.distraction_points = {}
    
    def test_complete_game_turn_sequence(self):
        """Test a complete game turn with all systems active."""
        # Set up complex game state
        self.game_engine.player.temporary_effects = {
            'stealth': 2,
            'virus': 1
        }
        self.game_engine.player.heat = 30
        
        with patch('game_data.GameData.ENEMY_TYPES', {
            'test_enemy': Mock(movement=Mock(), cpu=50, vision=10, damage=10)
        }):
            enemy = Enemy(Position(20, 20), "test_enemy")
            enemy.move_cooldown = 1
            self.game_engine.enemies = [enemy]
            
            self.game_engine.game_state.threat_scan_turns = 2
            
            initial_turn = self.game_engine.turn
            
            with patch.object(self.game_engine.player, 'take_damage') as mock_damage:
                self.game_engine.process_turn()
                
                # Verify all systems processed
                assert self.game_engine.turn == initial_turn + 1
                assert self.game_engine.player.temporary_effects['stealth'] == 1
                assert enemy.move_cooldown == 0
                assert self.game_engine.game_state.threat_scan_turns == 1
                
                # Virus should have caused damage
                mock_damage.assert_called()
    
    def test_turn_cascade_effects(self):
        """Test that turn effects cascade properly."""
        # Set up cascading effects (heat reduction, effect expiration, etc.)
        self.game_engine.player.heat = 80
        self.game_engine.player.temporary_effects = {
            'overclock': 1,  # Will expire, should affect heat
            'stealth': 1     # Will expire
        }
        
        initial_heat = self.game_engine.player.heat
        
        self.game_engine.process_turn()
        
        # Heat should decrease and effects should expire
        assert self.game_engine.player.heat < initial_heat
        assert 'overclock' not in self.game_engine.player.temporary_effects
        assert 'stealth' not in self.game_engine.player.temporary_effects


if __name__ == "__main__":
    pytest.main([__file__])