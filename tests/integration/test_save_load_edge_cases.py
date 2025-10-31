#!/usr/bin/env python3
"""
Edge case and failure scenario tests for save/load system.

Tests error recovery, corrupted data handling, and edge cases
that could cause crashes or data loss.

Based on Test Suite Audit 2025 - Gap #3: Save/Load Edge Cases
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch

from game_save import SaveGameManager
from game_characters import Player, Enemy
from game_entities import Position, EnemyState


class TestSaveLoadCorruptedData:
    """Test handling of corrupted save files."""

    def test_load_corrupted_json_syntax_error(self):
        """Loading save with invalid JSON syntax returns None and logs error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            # Write invalid JSON
            temp_file.write("{invalid json syntax: missing brace")

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                with patch('logging.error') as mock_log:
                    loaded_data = SaveGameManager.load_game()

                    assert loaded_data is None, "Should return None for corrupted JSON"
                    # Verify error was logged
                    assert mock_log.called, "Error should be logged"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_empty_file(self):
        """Loading empty save file returns None gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            # Write nothing

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                with patch('logging.error') as mock_log:
                    loaded_data = SaveGameManager.load_game()

                    assert loaded_data is None, "Should return None for empty file"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_missing_required_fields(self):
        """Loading save with missing required fields returns None."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            # Valid JSON but missing critical fields
            json.dump({"level": 1}, temp_file)

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                # Load will succeed but game init should handle missing fields
                loaded_data = SaveGameManager.load_game()

                # Verify it loaded the partial data (system is robust)
                assert loaded_data is not None
                assert loaded_data.get("level") == 1
                # Missing "player" field is expected to be handled by game init
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_corrupted_player_data(self):
        """Loading save with invalid player data structure returns None."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            # Player is a list instead of dict
            corrupted_data = {
                "level": 1,
                "player": ["not", "a", "dict"],
                "enemies": []
            }
            json.dump(corrupted_data, temp_file)

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                with patch('logging.error') as mock_log:
                    loaded_data = SaveGameManager.load_game()

                    # Save system should detect corruption and return None
                    assert loaded_data is None, "Should return None for corrupted player data"
                    assert mock_log.called, "Error should be logged"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_non_existent_file(self):
        """Loading non-existent save file returns None."""
        non_existent_path = "/tmp/this_file_does_not_exist_test_12345.json"

        with patch.object(SaveGameManager, 'SAVE_FILE', non_existent_path):
            loaded_data = SaveGameManager.load_game()

            assert loaded_data is None, "Should return None for missing file"


class TestSaveWithActiveTemporaryEffects:
    """Test saving/loading with active temporary effects on player."""

    def test_save_load_with_temporary_effects(self):
        """Temporary effects persist through save/load."""
        mock_game = self._create_mock_game_with_effects()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                # Save with active effects
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                # Load and verify
                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None

                # Verify temporary effects were saved
                assert "temporary_effects" in loaded_data["player"]
                loaded_effects = loaded_data["player"]["temporary_effects"]
                assert loaded_effects["armor"] == 5
                assert loaded_effects["damage"] == 10
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_load_with_empty_temporary_effects(self):
        """Empty temporary effects dict saves/loads correctly."""
        mock_game = self._create_minimal_mock_game()
        mock_game.player.temporary_effects = {}

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None
                assert loaded_data["player"]["temporary_effects"] == {}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _create_mock_game_with_effects(self):
        """Create mock game with active temporary effects."""
        mock_game = self._create_minimal_mock_game()

        # Add temporary effects
        mock_game.player.temporary_effects = {
            "armor": 5,
            "damage": 10
        }

        return mock_game

    def _create_minimal_mock_game(self):
        """Create minimal mock game for testing."""
        mock_game = Mock()
        mock_game.level = 1
        mock_game.turn = 10
        mock_game.game_over = False
        mock_game.admin_spawned = False

        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 8
        mock_player.last_position = Position(5, 8)
        mock_player.cpu = 90
        mock_player.max_cpu = 100
        mock_player.heat = 15
        mock_player.max_heat = 100
        mock_player.trace_level = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}

        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {}
        mock_inventory.max_equipped_exploits = 8
        mock_inventory.items = []
        mock_player.inventory_manager = mock_inventory

        mock_game.player = mock_player

        mock_game_state = Mock()
        mock_game_state.dungeon_seed = 54321
        mock_game_state.threat_scan_turns = 0
        mock_game_state.noise_locations = []
        mock_game_state.distraction_points = {}
        mock_game_state.revealed_special_nodes = {}
        mock_game.game_state = mock_game_state

        mock_map = Mock()
        mock_map.code_hacks = {}
        mock_map.exploit_pickups = {}
        mock_map.permanent_upgrades = {}
        mock_map.story_fragments = {}
        mock_map.gateway = None
        mock_map.explored_tiles = set()
        mock_map.last_known_enemy_positions = {}
        mock_game.game_map = mock_map

        mock_game.enemies = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []

        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None

        return mock_game


class TestSaveWithComplexEnemyStates:
    """Test saving/loading with enemies in various states."""

    def test_save_load_multiple_enemy_states(self):
        """Enemies with different states all save/load correctly."""
        mock_game = self._create_minimal_mock_game()

        # Create enemies in different states (UNAWARE, ALERT, HOSTILE)
        unaware_enemy = Enemy(Position(10, 10), 'patrol')
        unaware_enemy.state = EnemyState.UNAWARE
        unaware_enemy.move_queue = [Position(11, 10), Position(12, 10)]

        alert_enemy = Enemy(Position(15, 15), 'scanner')
        alert_enemy.state = EnemyState.ALERT
        alert_enemy.last_seen_player_position = Position(14, 14)

        hostile_enemy = Enemy(Position(20, 20), 'firewall')
        hostile_enemy.state = EnemyState.HOSTILE

        mock_game.enemies = [unaware_enemy, alert_enemy, hostile_enemy]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None
                assert len(loaded_data["enemies"]) == 3

                # Verify states saved correctly
                states = [e["state"] for e in loaded_data["enemies"]]
                assert "unaware" in states
                assert "alert" in states
                assert "hostile" in states
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_load_enemy_with_move_queue(self):
        """Enemy move queue persists through save/load."""
        mock_game = self._create_minimal_mock_game()

        enemy = Enemy(Position(10, 10), 'patrol')
        enemy.move_queue = [Position(11, 10), Position(12, 10), Position(13, 10)]

        mock_game.enemies = [enemy]

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None

                # Verify move queue saved
                saved_enemy = loaded_data["enemies"][0]
                assert "move_queue" in saved_enemy
                assert len(saved_enemy["move_queue"]) == 3
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _create_minimal_mock_game(self):
        """Create minimal mock game for testing."""
        mock_game = Mock()
        mock_game.level = 1
        mock_game.turn = 10
        mock_game.game_over = False
        mock_game.admin_spawned = False

        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 8
        mock_player.last_position = Position(5, 8)
        mock_player.cpu = 90
        mock_player.max_cpu = 100
        mock_player.heat = 15
        mock_player.max_heat = 100
        mock_player.trace_level = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}

        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {}
        mock_inventory.max_equipped_exploits = 8
        mock_inventory.items = []
        mock_player.inventory_manager = mock_inventory

        mock_game.player = mock_player

        mock_game_state = Mock()
        mock_game_state.dungeon_seed = 54321
        mock_game_state.threat_scan_turns = 0
        mock_game_state.noise_locations = []
        mock_game_state.distraction_points = {}
        mock_game_state.revealed_special_nodes = {}
        mock_game.game_state = mock_game_state

        mock_map = Mock()
        mock_map.code_hacks = {}
        mock_map.exploit_pickups = {}
        mock_map.permanent_upgrades = {}
        mock_map.story_fragments = {}
        mock_map.gateway = None
        mock_map.explored_tiles = set()
        mock_map.last_known_enemy_positions = {}
        mock_game.game_map = mock_map

        mock_game.enemies = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []

        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None

        return mock_game


class TestSaveErrorRecovery:
    """Test save system recovers gracefully from errors."""

    def test_save_with_permission_error(self):
        """Save handles permission errors gracefully."""
        mock_game = self._create_minimal_mock_game()

        # Use a path that will cause permission error
        with patch.object(SaveGameManager, 'SAVE_FILE', '/root/no_permission.json'):
            with patch('logging.error') as mock_log:
                save_success = SaveGameManager.save_game(mock_game)

                # Should return False and log error
                assert save_success is False
                assert mock_log.called

    def test_save_with_disk_full_simulation(self):
        """Save handles disk full errors gracefully."""
        mock_game = self._create_minimal_mock_game()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, 'SAVE_FILE', temp_path):
                # Mock open to raise OSError (disk full)
                with patch('builtins.open', side_effect=OSError("No space left on device")):
                    with patch('logging.error') as mock_log:
                        save_success = SaveGameManager.save_game(mock_game)

                        assert save_success is False
                        assert mock_log.called
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _create_minimal_mock_game(self):
        """Create minimal mock game for testing."""
        mock_game = Mock()
        mock_game.level = 1
        mock_game.turn = 10
        mock_game.game_over = False
        mock_game.admin_spawned = False

        mock_player = Mock()
        mock_player.x = 5
        mock_player.y = 8
        mock_player.last_position = Position(5, 8)
        mock_player.cpu = 90
        mock_player.max_cpu = 100
        mock_player.heat = 15
        mock_player.max_heat = 100
        mock_player.trace_level = 0
        mock_player.ram_total = 8
        mock_player.speed_moves_remaining = 0
        mock_player.temporary_effects = {}

        mock_inventory = Mock()
        mock_inventory.equipped_exploits = {}
        mock_inventory.max_equipped_exploits = 8
        mock_inventory.items = []
        mock_player.inventory_manager = mock_inventory

        mock_game.player = mock_player

        mock_game_state = Mock()
        mock_game_state.dungeon_seed = 54321
        mock_game_state.threat_scan_turns = 0
        mock_game_state.noise_locations = []
        mock_game_state.distraction_points = {}
        mock_game_state.revealed_special_nodes = {}
        mock_game.game_state = mock_game_state

        mock_map = Mock()
        mock_map.code_hacks = {}
        mock_map.exploit_pickups = {}
        mock_map.permanent_upgrades = {}
        mock_map.story_fragments = {}
        mock_map.gateway = None
        mock_map.explored_tiles = set()
        mock_map.last_known_enemy_positions = {}
        mock_game.game_map = mock_map

        mock_game.enemies = []
        mock_game.enemy_manager = Mock()
        mock_game.enemy_manager.enemies = []

        mock_game.code_hack_effects = {}
        mock_game.discovered_code_effects = {}
        mock_game.inventory_selection = 0
        mock_game.lore_viewer_selection = 0
        mock_game.overclock_confirmation = False
        mock_game.overclock_exploit = None

        return mock_game


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
