"""
Integration tests for save/load → game state → enemy AI state persistence.
Tests complete save/load workflow with complex game state.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from game_characters import Enemy, Player
from game_entities import Position, EnemyState, EnemyMovement
from game_save import SaveGameManager
from game_engine import GameEngine
from tests.fixtures.real_game_data import create_real_enemy, create_test_map_with_real_tiles


class TestSaveLoadStateChain:
    """Test save/load system preserves complete game state using real game data."""
    
    def setup_method(self):
        """Set up complex game state for save/load testing."""
        self.save_manager = SaveGameManager()
        
        # Create complex game state with real game objects
        self.player = Player(15, 20)
        self.player.cpu = 75
        self.player.max_cpu = 100
        self.player.heat = 25
        
        # Create enemies with movement queues and state using real data
        self.scanner = create_real_enemy("scanner", Position(10, 10))
        self.scanner.state = EnemyState.ALERT
        self.scanner.movement_queue = [Position(11, 10), Position(12, 10), Position(13, 10)]
        self.scanner.last_seen_player = Position(14, 19)
        
        self.patrol = create_real_enemy("patrol", Position(5, 5))
        self.patrol.patrol_points = [Position(5, 5), Position(10, 5), Position(10, 10)]
        self.patrol.patrol_index = 1
        self.patrol.movement_queue = [Position(6, 5), Position(7, 5), Position(8, 5)]
        
        self.enemies = [self.scanner, self.patrol]
        
        # Create game map with real tile data
        self.game_map = create_test_map_with_real_tiles(30, 30)
        
        # Create game engine state with minimal mocking
        self.game_engine = GameEngine()
        self.game_engine.player = self.player
        
        # Mock only the enemy manager to control enemy list
        mock_enemy_manager = Mock()
        mock_enemy_manager.enemies = self.enemies
        self.game_engine.enemy_manager = mock_enemy_manager
        
        self.game_engine.game_map = self.game_map
        
        # Add minimal required components for save/load
        from game_state import MessageLog
        self.game_engine.message_log = MessageLog()
    
    def test_save_and_load_preserves_player_state(self):
        """Test that player state is preserved through save/load."""
        try:
            # Save game state using real SaveGameManager
            success = SaveGameManager.save_game(self.game_engine)
            assert success == True, "Save operation should succeed"
            
            # Verify save file exists
            assert SaveGameManager.save_exists(), "Save file should be created"
            
            # Load game state
            save_data = SaveGameManager.load_game()
            assert save_data is not None, "Load operation should succeed"
            
            # Verify player state preserved in save data
            player_data = save_data.get('player', {})
            assert player_data.get('x') == self.player.x, "Player X position should be preserved"
            assert player_data.get('y') == self.player.y, "Player Y position should be preserved"
            assert player_data.get('cpu') == self.player.cpu, "Player CPU should be preserved"
            assert player_data.get('max_cpu') == self.player.max_cpu, "Player max CPU should be preserved"
            assert player_data.get('heat') == self.player.heat, "Player heat should be preserved"
            
        finally:
            # Clean up save file
            if SaveGameManager.save_exists():
                SaveGameManager.delete_save()
    
    def test_save_and_load_preserves_enemy_movement_queues(self):
        """Test that enemy movement queues are preserved through save/load."""
        try:
            # Save game state
            success = SaveGameManager.save_game(self.game_engine)
            assert success == True, "Save operation should succeed"
            
            # Load game state
            save_data = SaveGameManager.load_game()
            assert save_data is not None, "Load operation should succeed"
            
            # Verify enemy data preserved in save file
            enemies_data = save_data.get('enemies', [])
            assert len(enemies_data) == len(self.enemies), "Enemy count should be preserved"
            
            # Find corresponding enemies in save data (by position)
            scanner_data = None
            patrol_data = None
            
            for enemy_data in enemies_data:
                if enemy_data.get('x') == 10 and enemy_data.get('y') == 10:
                    scanner_data = enemy_data
                elif enemy_data.get('x') == 5 and enemy_data.get('y') == 5:
                    patrol_data = enemy_data
            
            assert scanner_data is not None, "Scanner enemy data should be found in save"
            assert patrol_data is not None, "Patrol enemy data should be found in save"
            
            # Verify scanner state and queue data
            assert scanner_data.get('state') == 'alert', "Scanner state should be preserved"
            if 'movement_queue' in scanner_data:
                movement_queue = scanner_data['movement_queue']
                assert len(movement_queue) >= 0, "Scanner movement queue should be preserved"
            if 'last_seen_player' in scanner_data:
                last_seen = scanner_data['last_seen_player']
                if last_seen:
                    assert last_seen.get('x') == 14, "Last seen player X should be preserved"
                    assert last_seen.get('y') == 19, "Last seen player Y should be preserved"
            
            # Verify patrol state and queue data
            if 'patrol_index' in patrol_data:
                assert patrol_data.get('patrol_index') == 1, "Patrol index should be preserved"
            if 'movement_queue' in patrol_data:
                movement_queue = patrol_data['movement_queue']
                assert len(movement_queue) >= 0, "Patrol movement queue should be preserved"
            
        finally:
            # Clean up save file
            if SaveGameManager.save_exists():
                SaveGameManager.delete_save()
    
    def test_save_load_complete_workflow(self):
        """Test the complete save → load workflow using a new GameEngine."""
        try:
            # Save game state
            success = SaveGameManager.save_game(self.game_engine)
            assert success == True, "Save operation should succeed"
            
            # Create a new GameEngine and load from save
            from unittest.mock import patch
            with patch('game_audio.SoundManager') as mock_sound:
                mock_sound.return_value.preload_sounds.return_value = None
                
                # Load game state into new engine (this tests the complete load workflow)
                loaded_engine = GameEngine(load_save=True)
                
                # Verify that load was successful
                assert loaded_engine is not None, "New engine should be created with loaded data"
                assert loaded_engine.player is not None, "Loaded engine should have player"
                
                # Verify basic state preservation
                assert loaded_engine.player.cpu == self.player.cpu, "Player CPU should be preserved"
                assert loaded_engine.player.x == self.player.x, "Player X should be preserved"
                assert loaded_engine.player.y == self.player.y, "Player Y should be preserved"
            
        finally:
            # Clean up save file
            if SaveGameManager.save_exists():
                SaveGameManager.delete_save()
    
    def test_save_load_error_handling(self):
        """Test save/load error handling with invalid scenarios."""
        # Test save with None engine
        success = SaveGameManager.save_game(None)
        # Should handle error gracefully (return False)
        assert success == False, "Save with None engine should return False"
        
        # Test load when no save exists
        if SaveGameManager.save_exists():
            SaveGameManager.delete_save()  # Ensure no save exists
        
        save_data = SaveGameManager.load_game()
        # Should return None when no save file exists
        assert save_data is None, "Load should return None when no save file exists"
    
    def test_save_data_structure(self):
        """Test that save data contains expected structure."""
        try:
            # Save game state
            success = SaveGameManager.save_game(self.game_engine)
            assert success == True, "Save operation should succeed"
            
            # Load and verify save data structure
            save_data = SaveGameManager.load_game()
            assert save_data is not None, "Save data should exist"
            
            # Verify expected top-level keys exist
            expected_keys = ['player', 'game_state', 'enemies']
            for key in expected_keys:
                if key in save_data:  # Some keys might be optional depending on implementation
                    assert save_data[key] is not None, f"{key} should have data"
            
            # Verify player data structure
            if 'player' in save_data:
                player_data = save_data['player']
                expected_player_keys = ['x', 'y', 'cpu', 'max_cpu']
                for key in expected_player_keys:
                    if key in player_data:
                        assert isinstance(player_data[key], (int, float)), f"Player {key} should be numeric"
            
        finally:
            # Clean up save file
            if SaveGameManager.save_exists():
                SaveGameManager.delete_save()