#!/usr/bin/env python3
"""
Test Category 4: Game State Persistence Tests
Comprehensive tests for save/load system data integrity and error handling.
"""

import json
import os
import shutil
import tempfile
from unittest.mock import Mock, patch

from game_save import SaveGameManager
from tests.fixtures.simple_fixtures import player


class TestCorruptionRecovery:
    """Test corruption recovery and error handling."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")

    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_corrupted_json(self):
        """Test loading corrupted JSON file."""
        # Create corrupted save file
        with open(SaveGameManager.SAVE_FILE, "w") as f:
            f.write('{"incomplete": "json" missing bracket')

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

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")

    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_with_none_game(self):
        """Test saving with None game object."""
        result = SaveGameManager.save_game(None)
        assert result is False
        assert not SaveGameManager.save_exists()

    def test_save_with_none_player(self):
        """Test saving with None player object."""
        game = Mock()
        game.player = None

        result = SaveGameManager.save_game(game)
        assert result is False
        assert not SaveGameManager.save_exists()


class TestSaveGameUtilities:
    """Test save game utility functions."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_save_file = SaveGameManager.SAVE_FILE
        SaveGameManager.SAVE_FILE = os.path.join(self.temp_dir, "test_save.json")

    def teardown_method(self):
        """Clean up test environment."""
        SaveGameManager.SAVE_FILE = self.original_save_file
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_exists_trace_level(self):
        """Test save file existence trace_level."""
        # No save file exists initially
        assert not SaveGameManager.save_exists()

        # Create save file
        with open(SaveGameManager.SAVE_FILE, "w") as f:
            json.dump({"test": "data"}, f)

        # Now save file should exist
        assert SaveGameManager.save_exists()

    def test_save_deletion(self):
        """Test save file deletion."""
        # Create save file
        with open(SaveGameManager.SAVE_FILE, "w") as f:
            json.dump({"test": "data"}, f)

        assert SaveGameManager.save_exists()

        # Delete save file
        result = SaveGameManager.delete_save()
        assert result is True
        assert not SaveGameManager.save_exists()

    def test_save_deletion_nonexistent(self):
        """Test deletion of nonexistent save file."""
        assert not SaveGameManager.save_exists()

        # Should handle gracefully
        result = SaveGameManager.delete_save()
        assert result is True

    def test_save_timestamp_retrieval(self):
        """Test save timestamp retrieval."""
        import time

        # No save file exists
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is None

        # Create save file with timestamp
        save_data = {"timestamp": time.time(), "test": "data"}

        with open(SaveGameManager.SAVE_FILE, "w") as f:
            json.dump(save_data, f)

        # Should return formatted timestamp
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be formatted date string

    def test_save_timestamp_fallback(self):
        """Test timestamp fallback to file modification time."""
        # Create save file without timestamp
        save_data = {"test": "data"}

        with open(SaveGameManager.SAVE_FILE, "w") as f:
            json.dump(save_data, f)

        # Should fall back to file modification time
        timestamp = SaveGameManager.get_save_timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
