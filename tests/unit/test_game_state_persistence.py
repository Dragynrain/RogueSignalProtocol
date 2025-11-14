#!/usr/bin/env python3
"""
Test Category 4: Game State Persistence Tests
Comprehensive tests for save/load system data integrity and error handling.
"""

import json
from unittest.mock import Mock, patch

from game_save import SaveGameManager
from tests.fixtures.simple_fixtures import player


class TestCorruptionRecovery:
    """Test corruption recovery and error handling."""

    def test_load_corrupted_json(self, tmp_path, monkeypatch):
        """Test loading corrupted JSON file."""
        save_file = tmp_path / "test_save.json"

        # Mock _get_save_file_path to return our temp file
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        # Create corrupted save file
        save_file.write_text('{"incomplete": "json" missing bracket')

        result = SaveGameManager.load_game()
        assert result is None

    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            result = SaveGameManager.load_game()
            assert result is None

    def test_io_error_recovery(self):
        """Test recovery from I/O errors during save."""
        game = Mock()
        game.player = player()

        with patch("builtins.open", side_effect=OSError("Disk full")):
            result = SaveGameManager.save_game(game)
            assert result is False


class TestPartialSaveScenarios:
    """Test partial save scenarios and edge cases."""

    def test_save_with_none_game(self, tmp_path, monkeypatch):
        """Test saving with None game object."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        result = SaveGameManager.save_game(None)
        assert result is False
        assert not SaveGameManager.save_exists()

    def test_save_with_none_player(self, tmp_path, monkeypatch):
        """Test saving with None player object."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        game = Mock()
        game.player = None

        result = SaveGameManager.save_game(game)
        assert result is False
        assert not SaveGameManager.save_exists()


class TestSaveGameUtilities:
    """Test save game utility functions."""

    def test_save_exists_trace_level(self, tmp_path, monkeypatch):
        """Test save file existence trace_level."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        # No save file exists initially
        assert not SaveGameManager.save_exists()

        # Create save file
        save_file.write_text(json.dumps({"test": "data"}))

        # Now save file should exist
        assert SaveGameManager.save_exists()

    def test_save_deletion(self, tmp_path, monkeypatch):
        """Test save file deletion."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        # Create save file
        save_file.write_text(json.dumps({"test": "data"}))

        assert SaveGameManager.save_exists()

        # Delete save file
        result = SaveGameManager.delete_save()
        assert result is True
        assert not SaveGameManager.save_exists()

    def test_save_deletion_nonexistent(self, tmp_path, monkeypatch):
        """Test deletion of nonexistent save file."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        assert not SaveGameManager.save_exists()

        # Should handle gracefully
        result = SaveGameManager.delete_save()
        assert result is True

    def test_save_timestamp_retrieval(self, tmp_path, monkeypatch):
        """Test save timestamp retrieval."""
        import time

        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        # No save file exists
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is None

        # Create save file with timestamp
        save_data = {"timestamp": time.time(), "test": "data"}
        save_file.write_text(json.dumps(save_data))

        # Should return formatted timestamp
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be formatted date string

    def test_save_timestamp_fallback(self, tmp_path, monkeypatch):
        """Test timestamp fallback to file modification time."""
        save_file = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(save_file))

        # Create save file without timestamp
        save_data = {"test": "data"}
        save_file.write_text(json.dumps(save_data))

        # Should fall back to file modification time
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
