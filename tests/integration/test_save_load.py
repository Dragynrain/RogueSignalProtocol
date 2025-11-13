#!/usr/bin/env python3
"""
Comprehensive save/load system tests.
Tests SaveGameManager with both mock objects and real game integration.

Covers:
- Basic save/load cycles
- Numpy data type handling
- Corrupted/malformed data recovery
- Enemy states and complex game states
- Temporary effects persistence
- Error recovery and edge cases
- Real game engine integration
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from game_characters import Enemy
from game_engine import GameEngine
from game_entities import EnemyState, Position
from game_save import SaveGameManager
from tests.fixtures.simple_fixtures import enemy_builder, minimal_mock_game


class TestSaveGameManagerValidation:
    """Test SaveGameManager validation and data type handling."""

    def test_numpy_converter_integer(self):
        """_numpy_converter handles numpy integers."""
        import numpy as np

        numpy_int = np.int32(42)
        result = SaveGameManager._numpy_converter(numpy_int)

        assert result == 42
        assert isinstance(result, int)

    def test_numpy_converter_float(self):
        """_numpy_converter handles numpy floats."""
        import numpy as np

        numpy_float = np.float64(3.14)
        result = SaveGameManager._numpy_converter(numpy_float)

        assert result == 3.14
        assert isinstance(result, float)

    def test_numpy_converter_array(self):
        """_numpy_converter handles numpy arrays."""
        import numpy as np

        numpy_array = np.array([1, 2, 3])
        result = SaveGameManager._numpy_converter(numpy_array)

        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_numpy_converter_unsupported_type(self):
        """_numpy_converter raises TypeError for unsupported types."""
        with pytest.raises(TypeError, match="is not JSON serializable"):
            SaveGameManager._numpy_converter({"unsupported": "dict"})

    def test_save_game_none_game_object(self):
        """save_game returns False when game object is None."""
        with patch("logging.error") as mock_log:
            result = SaveGameManager.save_game(None)

            assert result is False
            mock_log.assert_called_with("Cannot save: game object is None")

    def test_save_game_none_player_object(self):
        """save_game returns False when player object is None."""
        mock_game = Mock()
        mock_game.player = None

        with patch("logging.error") as mock_log:
            result = SaveGameManager.save_game(mock_game)

            assert result is False
            mock_log.assert_called_with("Cannot save: player object is None")


class TestSaveLoadBasicCycles:
    """Test basic save/load cycles with mock data."""

    def test_save_load_cycle_basic_data(self):
        """Basic save/load cycle preserves essential data."""
        mock_game = minimal_mock_game()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                # Save the game
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                # Load the game
                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None

                # Verify key data is preserved
                assert loaded_data["level"] == mock_game.level
                assert loaded_data["player"]["x"] == mock_game.player.x
                assert loaded_data["player"]["cpu"] == mock_game.player.cpu
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_load_enemy_state_enum(self):
        """Enemy state enum is properly serialized and deserialized in save/load cycle."""
        enemy = Enemy(Position(10, 10), "scanner")
        enemy.state = EnemyState.ALERT

        mock_game = minimal_mock_game()
        mock_game.enemies = [enemy]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                # Save with enum state
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                # Load the save data
                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None

                # Verify enemy state was saved as a string
                assert len(loaded_data["enemies"]) == 1
                saved_enemy_state = loaded_data["enemies"][0]["state"]
                assert isinstance(saved_enemy_state, str)
                assert saved_enemy_state == "alert"

                # Simulate restoration (string back to enum)
                restored_enemy = Enemy(Position(10, 10), "scanner")
                restored_enemy.state = (
                    EnemyState(saved_enemy_state)
                    if isinstance(saved_enemy_state, str)
                    else saved_enemy_state
                )

                # Verify the restored enemy has proper EnemyState enum
                assert isinstance(restored_enemy.state, EnemyState)
                assert restored_enemy.state == EnemyState.ALERT

                # Now save again to test double-save scenario
                mock_game.enemies = [restored_enemy]
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestCorruptedDataHandling:
    """Test handling of corrupted save files."""

    def test_load_corrupted_json_syntax_error(self):
        """Loading save with invalid JSON syntax returns None and logs error."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name
            temp_file.write("{invalid json syntax: missing brace")

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                with patch("logging.error") as mock_log:
                    loaded_data = SaveGameManager.load_game()

                    assert loaded_data is None, "Should return None for corrupted JSON"
                    assert mock_log.called, "Error should be logged"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_empty_file(self):
        """Loading empty save file returns None gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                with patch("logging.error"):
                    loaded_data = SaveGameManager.load_game()
                    assert loaded_data is None, "Should return None for empty file"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_missing_required_fields(self):
        """Loading save with missing required fields returns partial data."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name
            json.dump({"level": 1}, temp_file)

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                loaded_data = SaveGameManager.load_game()

                # System is robust - loads partial data
                assert loaded_data is not None
                assert loaded_data.get("level") == 1
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_corrupted_player_data(self):
        """Loading save with invalid player data structure returns None."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name
            corrupted_data = {"level": 1, "player": ["not", "a", "dict"], "enemies": []}
            json.dump(corrupted_data, temp_file)

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                with patch("logging.error") as mock_log:
                    loaded_data = SaveGameManager.load_game()

                    assert loaded_data is None, "Should return None for corrupted player data"
                    assert mock_log.called, "Error should be logged"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_non_existent_file(self):
        """Loading non-existent save file returns None."""
        non_existent_path = "/tmp/this_file_does_not_exist_test_12345.json"

        with patch.object(SaveGameManager, "SAVE_FILE", non_existent_path):
            loaded_data = SaveGameManager.load_game()
            assert loaded_data is None, "Should return None for missing file"


class TestTemporaryEffects:
    """Test saving/loading with active temporary effects on player."""

    def test_save_load_with_temporary_effects(self):
        """Temporary effects persist through save/load."""
        mock_game = minimal_mock_game()
        mock_game.player.temporary_effects = {"armor": 5, "damage": 10}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

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
        mock_game = minimal_mock_game()
        mock_game.player.temporary_effects = {}

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                save_success = SaveGameManager.save_game(mock_game)
                assert save_success is True

                loaded_data = SaveGameManager.load_game()
                assert loaded_data is not None
                assert loaded_data["player"]["temporary_effects"] == {}
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestComplexEnemyStates:
    """Test saving/loading with enemies in various states."""

    def test_save_load_multiple_enemy_states(self):
        """Enemies with different states all save/load correctly."""
        mock_game = minimal_mock_game()

        # Create enemies in different states
        unaware_enemy = Enemy(Position(10, 10), "patrol")
        unaware_enemy.state = EnemyState.UNAWARE
        unaware_enemy.move_queue = [Position(11, 10), Position(12, 10)]

        alert_enemy = Enemy(Position(15, 15), "scanner")
        alert_enemy.state = EnemyState.ALERT
        alert_enemy.last_seen_player_position = Position(14, 14)

        hostile_enemy = Enemy(Position(20, 20), "firewall")
        hostile_enemy.state = EnemyState.HOSTILE

        mock_game.enemies = [unaware_enemy, alert_enemy, hostile_enemy]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
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
        mock_game = minimal_mock_game()

        enemy = Enemy(Position(10, 10), "patrol")
        enemy.move_queue = [Position(11, 10), Position(12, 10), Position(13, 10)]

        mock_game.enemies = [enemy]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
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


class TestErrorRecovery:
    """Test save system recovers gracefully from errors."""

    def test_save_with_permission_error(self):
        """Save handles permission errors gracefully."""
        mock_game = minimal_mock_game()

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            with patch("logging.error") as mock_log:
                save_success = SaveGameManager.save_game(mock_game)

                assert save_success is False
                assert mock_log.called

    def test_save_with_disk_full_simulation(self):
        """Save handles disk full errors gracefully."""
        mock_game = minimal_mock_game()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
            temp_path = temp_file.name

        try:
            with patch.object(SaveGameManager, "SAVE_FILE", temp_path):
                with patch("builtins.open", side_effect=OSError("No space left on device")):
                    with patch("logging.error") as mock_log:
                        save_success = SaveGameManager.save_game(mock_game)

                        assert save_success is False
                        assert mock_log.called
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestRealGameEngineIntegration:
    """Test save/load with real GameEngine integration."""

    def setup_method(self):
        """Set up test environment."""
        if SaveGameManager.save_exists():
            SaveGameManager.delete_save()

    def teardown_method(self):
        """Clean up after each test."""
        if SaveGameManager.save_exists():
            SaveGameManager.delete_save()

    def test_save_and_load_basic_player_state(self, basic_game_engine):
        """Test that basic player state is preserved through save/load cycle."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            # Set dungeon seed and regenerate map for deterministic layout
            game.game_state.dungeon_seed = 42
            game.game_session.generate_procedural_level()

            # Store player spawn position
            saved_x = game.player.x
            saved_y = game.player.y

            # Set player stats
            game.player.cpu = 75
            game.player.max_cpu = 100
            game.player.heat = 40
            game.player.max_heat = 100
            game.player.trace_level = 15
            game.player.ram_total = 12

            # Save the game
            success = SaveGameManager.save_game(game)
            assert success, "Save operation should succeed"

            # Load game into new engine
            loaded_game = GameEngine(load_save=True)

            # Verify player state preserved
            assert loaded_game.player.x == saved_x
            assert loaded_game.player.y == saved_y
            assert loaded_game.player.cpu == 75
            assert loaded_game.player.max_cpu == 100
            assert loaded_game.player.heat == 40
            assert loaded_game.player.max_heat == 100
            assert loaded_game.player.ram_total == 12

    def test_save_and_load_enemy_states(self, basic_game_engine):
        """Test that enemy positions, states, and AI data are preserved."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            game.game_state.dungeon_seed = 42
            game.game_session.generate_procedural_level()

            # Create enemies with various states
            scanner = enemy_builder("scanner", pos=(10, 10))
            scanner.state = EnemyState.ALERT
            scanner.alert_timer = 3
            scanner.last_seen_player = Position(15, 15)

            patrol = enemy_builder("patrol", pos=(20, 20))
            patrol.state = EnemyState.HOSTILE
            patrol.patrol_points = [Position(20, 20), Position(25, 20), Position(25, 25)]
            patrol.patrol_index = 1

            bot = enemy_builder("bot", pos=(5, 5))
            bot.state = EnemyState.UNAWARE
            bot.disabled_turns = 2

            game.enemy_manager.enemies = [scanner, patrol, bot]

            # Save the game
            success = SaveGameManager.save_game(game)
            assert success

            # Load game
            loaded_game = GameEngine(load_save=True)

            # Verify enemy count
            assert len(loaded_game.enemy_manager.enemies) == 3

            # Verify enemies by position
            loaded_enemies = {
                (e.position.x, e.position.y): e for e in loaded_game.enemy_manager.enemies
            }

            loaded_scanner = loaded_enemies.get((10, 10))
            assert loaded_scanner is not None
            assert loaded_scanner.state in (EnemyState.ALERT, "alert")
            assert loaded_scanner.alert_timer == 3

            loaded_patrol = loaded_enemies.get((20, 20))
            assert loaded_patrol is not None
            assert loaded_patrol.state in (EnemyState.HOSTILE, "hostile")
            assert loaded_patrol.patrol_index == 1
            assert len(loaded_patrol.patrol_points) == 3

            loaded_bot = loaded_enemies.get((5, 5))
            assert loaded_bot is not None
            assert loaded_bot.state in (EnemyState.UNAWARE, "unaware")
            assert loaded_bot.disabled_turns == 2

    def test_save_and_load_temporary_effects_integration(self, basic_game_engine):
        """Test that player temporary effects are preserved."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            # Set various temporary effects
            game.player.temporary_effects = {
                "speed_boost_turns": 5,
                "movement_slowed_turns": 0,
                "enhanced_vision_turns": 3,
                "exploit_efficiency_turns": 2,
                "traffic_masquerade_turns": 1,
                "virus_turns": 0,
            }
            game.player.speed_moves_remaining = 2

            success = SaveGameManager.save_game(game)
            assert success

            loaded_game = GameEngine(load_save=True)

            # Verify temporary effects preserved
            effects = loaded_game.player.temporary_effects
            assert effects["speed_boost_turns"] == 5
            assert effects["enhanced_vision_turns"] == 3
            assert effects["exploit_efficiency_turns"] == 2
            assert effects["traffic_masquerade_turns"] == 1
            assert loaded_game.player.speed_moves_remaining == 2

    def test_save_and_load_complex_gameplay_scenario(self, basic_game_engine):
        """Integration test: Complex gameplay scenario with multiple systems active."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            # Set dungeon seed for deterministic map
            game.game_state.dungeon_seed = 42

            # Complex player state
            game.player.x = 35
            game.player.y = 28
            game.player.cpu = 65
            game.player.max_cpu = 120
            game.player.heat = 55
            game.player.trace_level = 20
            game.player.ram_total = 16
            game.player.speed_moves_remaining = 1
            game.player.temporary_effects = {
                "speed_boost_turns": 3,
                "enhanced_vision_turns": 5,
                "exploit_efficiency_turns": 2,
                "traffic_masquerade_turns": 0,
                "movement_slowed_turns": 0,
                "virus_turns": 0,
            }

            # Multiple enemies
            scanner = enemy_builder("scanner", pos=(30, 25))
            scanner.state = EnemyState.HOSTILE
            scanner.last_seen_player = Position(35, 28)

            patrol = enemy_builder("patrol", pos=(15, 15))
            patrol.state = EnemyState.ALERT
            patrol.patrol_points = [Position(15, 15), Position(20, 15), Position(20, 20)]
            patrol.patrol_index = 2

            bot = enemy_builder("bot", pos=(40, 40))
            bot.state = EnemyState.UNAWARE

            game.enemy_manager.enemies = [scanner, patrol, bot]

            # Game effects
            game.game_state.threat_scan_turns = 5
            game.game_state.noise_locations = [Position(25, 30), Position(10, 10)]
            game.game_state.distraction_points = {Position(22, 22): 4}

            # Level progression
            game.game_state.level = 1
            game.game_state.turn = 100
            game.game_state.admin_spawned = False

            # Map items
            game.game_map.gateway = Position(45, 45)

            # Save complex state
            success = SaveGameManager.save_game(game)
            assert success

            # Load into new game
            loaded_game = GameEngine(load_save=True)

            # Verify critical state preserved
            assert loaded_game.player.x == 35 and loaded_game.player.y == 28
            assert loaded_game.player.cpu == 65
            assert loaded_game.player.heat == 55
            assert loaded_game.player.temporary_effects["speed_boost_turns"] == 3
            assert len(loaded_game.enemy_manager.enemies) == 3
            assert loaded_game.game_state.level == 1
            assert loaded_game.game_state.turn == 100
            assert loaded_game.game_state.threat_scan_turns == 5
            assert len(loaded_game.game_state.noise_locations) == 2

    def test_load_when_save_doesnt_exist(self):
        """Test that load handles missing save file gracefully."""
        if SaveGameManager.save_exists():
            SaveGameManager.delete_save()

        save_data = SaveGameManager.load_game()
        assert save_data is None

    def test_save_file_timestamp(self, basic_game_engine):
        """Test that save file includes valid timestamp."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            success = SaveGameManager.save_game(game)
            assert success

            timestamp = SaveGameManager.get_save_timestamp()

            assert timestamp is not None
            assert isinstance(timestamp, str)
            assert len(timestamp) > 0

    def test_save_atomic_write_safety(self, basic_game_engine):
        """Test that save uses atomic write (temp file + rename) for safety."""
        with patch("game_audio.SoundManager"):
            game = basic_game_engine

            success = SaveGameManager.save_game(game)
            assert success

            # Verify no temp file left behind
            temp_file = SaveGameManager.SAVE_FILE + ".tmp"
            assert not os.path.exists(temp_file)

            # Verify actual save file exists
            assert SaveGameManager.save_exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
