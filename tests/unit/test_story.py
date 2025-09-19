#!/usr/bin/env python3
"""
Unit tests for game_story.py - Story fragment management system.
Tests story discovery, progress tracking, and fragment retrieval.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import os
import tempfile
import shutil
import json

# Import game modules
from game_story import StoryFragmentManager
from data_loading import PersistentStorage, DataLoader, get_story_fragments


class TestStoryFragmentManager(unittest.TestCase):
    """Test StoryFragmentManager core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test saves
        self.test_dir = tempfile.mkdtemp()

        # Mock story fragments for testing
        self.mock_story_fragments = [
            "Fragment 0: The beginning of the signal...",
            "Fragment 1: Deep in the corporate network...",
            "Fragment 2: The truth about the rogue signal...",
            "Fragment 3: Final revelation of the conspiracy...",
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_initialization_new_game(self, mock_storage_class, mock_get_fragments):
        """Test StoryFragmentManager initialization for new game."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}  # No existing progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()

        # Should create default progress data
        self.assertEqual(manager.discovered_fragments, [])
        self.assertIn("discovered_story_fragments", manager.progress_data)
        self.assertIn("version", manager.progress_data)
        mock_storage.load_data.assert_called_once_with("rogue_signal_progress.json")

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_initialization_existing_progress(self, mock_storage_class, mock_get_fragments):
        """Test StoryFragmentManager initialization with existing progress."""
        existing_progress = {
            "discovered_story_fragments": [0, 2],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()

        # Should load existing progress
        self.assertEqual(manager.discovered_fragments, [0, 2])
        self.assertEqual(manager.progress_data, existing_progress)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_next_undiscovered_fragment_first(self, mock_storage_class, mock_get_fragments):
        """Test getting next undiscovered fragment from beginning."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        next_fragment = manager.get_next_undiscovered_fragment()

        self.assertEqual(next_fragment, 0)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_next_undiscovered_fragment_middle(self, mock_storage_class, mock_get_fragments):
        """Test getting next undiscovered fragment with some discovered."""
        existing_progress = {
            "discovered_story_fragments": [0, 2],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        next_fragment = manager.get_next_undiscovered_fragment()

        # Should return fragment 1 (skipping already discovered 0)
        self.assertEqual(next_fragment, 1)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_next_undiscovered_fragment_all_discovered(self, mock_storage_class, mock_get_fragments):
        """Test getting next undiscovered fragment when all are discovered."""
        existing_progress = {
            "discovered_story_fragments": [0, 1, 2, 3],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        next_fragment = manager.get_next_undiscovered_fragment()

        # Should return None when all fragments are discovered
        self.assertIsNone(next_fragment)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_discover_fragment_success(self, mock_storage_class, mock_get_fragments):
        """Test successful fragment discovery."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        result = manager.discover_fragment(1)

        # Should successfully discover fragment
        self.assertTrue(result)
        self.assertIn(1, manager.discovered_fragments)
        self.assertEqual(manager.progress_data["discovered_story_fragments"], [1])
        mock_storage.save_data.assert_called_once_with(
            "rogue_signal_progress.json", manager.progress_data
        )

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_discover_fragment_already_discovered(self, mock_storage_class, mock_get_fragments):
        """Test discovering fragment that's already discovered."""
        existing_progress = {
            "discovered_story_fragments": [1],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        result = manager.discover_fragment(1)

        # Should return False for already discovered fragment
        self.assertFalse(result)
        mock_storage.save_data.assert_not_called()

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_discover_fragment_invalid_index(self, mock_storage_class, mock_get_fragments):
        """Test discovering fragment with invalid index."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()

        # Test negative index
        result_negative = manager.discover_fragment(-1)
        self.assertFalse(result_negative)

        # Test index beyond available fragments
        result_too_high = manager.discover_fragment(10)
        self.assertFalse(result_too_high)

        mock_storage.save_data.assert_not_called()

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_discover_fragment_maintains_order(self, mock_storage_class, mock_get_fragments):
        """Test that discovered fragments are kept in sorted order."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()

        # Discover fragments out of order
        manager.discover_fragment(3)
        manager.discover_fragment(1)
        manager.discover_fragment(0)

        # Should be stored in sorted order
        self.assertEqual(manager.discovered_fragments, [0, 1, 3])

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_discovered_fragments(self, mock_storage_class, mock_get_fragments):
        """Test getting all discovered fragments with content."""
        existing_progress = {
            "discovered_story_fragments": [0, 2],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        discovered = manager.get_discovered_fragments()

        # Should return tuples of (index, content) in order
        expected = [
            (0, "Fragment 0: The beginning of the signal..."),
            (2, "Fragment 2: The truth about the rogue signal...")
        ]
        self.assertEqual(discovered, expected)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_discovered_fragments_empty(self, mock_storage_class, mock_get_fragments):
        """Test getting discovered fragments when none are discovered."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        discovered = manager.get_discovered_fragments()

        self.assertEqual(discovered, [])

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_discovered_fragments_with_invalid_indices(self, mock_storage_class, mock_get_fragments):
        """Test getting discovered fragments when some indices are invalid."""
        existing_progress = {
            "discovered_story_fragments": [0, 2, 10],  # 10 is beyond available fragments
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        discovered = manager.get_discovered_fragments()

        # Should only return valid fragments, ignoring invalid index 10
        expected = [
            (0, "Fragment 0: The beginning of the signal..."),
            (2, "Fragment 2: The truth about the rogue signal...")
        ]
        self.assertEqual(discovered, expected)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_fragment_count(self, mock_storage_class, mock_get_fragments):
        """Test getting fragment count for UI display."""
        existing_progress = {
            "discovered_story_fragments": [0, 2],
            "version": "1.0"
        }
        mock_storage = Mock()
        mock_storage.load_data.return_value = existing_progress
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        discovered_count, total_count = manager.get_fragment_count()

        self.assertEqual(discovered_count, 2)
        self.assertEqual(total_count, 4)

    @patch('game_story.get_story_fragments')
    @patch('game_story.PersistentStorage')
    def test_get_fragment_count_zero_discovered(self, mock_storage_class, mock_get_fragments):
        """Test getting fragment count when none are discovered."""
        mock_storage = Mock()
        mock_storage.load_data.return_value = {}
        mock_storage_class.return_value = mock_storage
        mock_get_fragments.return_value = self.mock_story_fragments

        manager = StoryFragmentManager()
        discovered_count, total_count = manager.get_fragment_count()

        self.assertEqual(discovered_count, 0)
        self.assertEqual(total_count, 4)


class TestPersistentStorage(unittest.TestCase):
    """Test PersistentStorage functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.storage = PersistentStorage(base_dir=self.test_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_initialization_creates_directory(self):
        """Test that PersistentStorage creates saves directory."""
        new_dir = os.path.join(self.test_dir, "new_saves")
        self.assertFalse(os.path.exists(new_dir))

        storage = PersistentStorage(base_dir=new_dir)

        self.assertTrue(os.path.exists(new_dir))

    def test_save_and_load_data_success(self):
        """Test successful save and load operations."""
        test_data = {
            "discovered_story_fragments": [0, 1, 3],
            "version": "1.0",
            "test_key": "test_value"
        }

        # Save data
        result = self.storage.save_data("test_save.json", test_data)
        self.assertTrue(result)

        # Load data
        loaded_data = self.storage.load_data("test_save.json")
        self.assertEqual(loaded_data, test_data)

    def test_load_data_file_not_found(self):
        """Test loading data when file doesn't exist."""
        with patch('data_loading.logging') as mock_logging:
            loaded_data = self.storage.load_data("nonexistent.json")

            self.assertEqual(loaded_data, {})
            mock_logging.debug.assert_called()

    def test_save_data_permission_error(self):
        """Test save data with permission errors."""
        # Mock the file opening to raise a permission error
        test_data = {"test": "data"}

        with patch('builtins.open', side_effect=PermissionError("Access denied")), \
             patch('data_loading.logging') as mock_logging:

            result = self.storage.save_data("test.json", test_data)

            self.assertFalse(result)
            mock_logging.error.assert_called()

    def test_load_data_invalid_json(self):
        """Test loading data with invalid JSON content."""
        # Create a file with invalid JSON
        invalid_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json content ")

        with patch('data_loading.logging') as mock_logging:
            loaded_data = self.storage.load_data("invalid.json")

            self.assertEqual(loaded_data, {})
            mock_logging.error.assert_called()

    def test_file_exists(self):
        """Test checking if save file exists."""
        # File doesn't exist initially
        self.assertFalse(self.storage.file_exists("test.json"))

        # Create file
        test_data = {"test": "data"}
        self.storage.save_data("test.json", test_data)

        # File should now exist
        self.assertTrue(self.storage.file_exists("test.json"))

    def test_list_save_files(self):
        """Test listing all save files."""
        # Initially no files
        files = self.storage.list_save_files()
        self.assertEqual(files, [])

        # Create some save files
        self.storage.save_data("save1.json", {"data": 1})
        self.storage.save_data("save2.json", {"data": 2})
        self.storage.save_data("config.txt", {"data": 3})  # Not JSON

        files = self.storage.list_save_files()

        # Should only include JSON files, sorted
        self.assertEqual(files, ["save1.json", "save2.json"])

    def test_list_save_files_directory_error(self):
        """Test listing save files when directory doesn't exist or is inaccessible."""
        # Remove the directory
        shutil.rmtree(self.test_dir)

        files = self.storage.list_save_files()
        self.assertEqual(files, [])


class TestDataLoader(unittest.TestCase):
    """Test DataLoader functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset class variables for clean testing
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None

    def tearDown(self):
        """Clean up test fixtures."""
        # Reset class variables after testing
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None

    @patch('builtins.open')
    @patch('data_loading.json.load')
    def test_load_story_fragments_success(self, mock_json_load, mock_open):
        """Test successful loading of story fragments from JSON."""
        mock_fragments = ["Fragment 1", "Fragment 2", "Fragment 3"]
        mock_json_load.return_value = {"fragments": mock_fragments}

        fragments = DataLoader.load_story_fragments()

        self.assertEqual(fragments, mock_fragments)
        mock_open.assert_called_once_with('story_content.json', 'r', encoding='utf-8')

    @patch('builtins.open')
    @patch('data_loading.logging')
    def test_load_story_fragments_file_not_found(self, mock_logging, mock_open):
        """Test loading story fragments when file doesn't exist."""
        mock_open.side_effect = FileNotFoundError("File not found")

        fragments = DataLoader.load_story_fragments()

        # Should return fallback fragments
        self.assertIsInstance(fragments, list)
        self.assertGreater(len(fragments), 0)
        self.assertIn("fallback", fragments[0].lower())
        mock_logging.warning.assert_called()

    @patch('builtins.open')
    @patch('data_loading.json.load')
    @patch('data_loading.logging')
    def test_load_story_fragments_invalid_json(self, mock_logging, mock_json_load, mock_open):
        """Test loading story fragments with invalid JSON."""
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        fragments = DataLoader.load_story_fragments()

        # Should return fallback fragments
        self.assertIsInstance(fragments, list)
        mock_logging.warning.assert_called()

    @patch('builtins.open')
    @patch('data_loading.json.load')
    @patch('data_loading.logging')
    def test_load_story_fragments_missing_key(self, mock_logging, mock_json_load, mock_open):
        """Test loading story fragments when JSON doesn't have fragments key."""
        mock_json_load.return_value = {"other_data": "value"}  # Missing 'fragments' key

        fragments = DataLoader.load_story_fragments()

        # Should return fallback fragments
        self.assertIsInstance(fragments, list)
        mock_logging.warning.assert_called()

    def test_load_story_fragments_caching(self):
        """Test that story fragments are cached after first load."""
        with patch('builtins.open') as mock_open, \
             patch('data_loading.json.load') as mock_json_load:

            mock_fragments = ["Fragment 1", "Fragment 2"]
            mock_json_load.return_value = {"fragments": mock_fragments}

            # Load twice
            fragments1 = DataLoader.load_story_fragments()
            fragments2 = DataLoader.load_story_fragments()

            # Should be the same object and only load once
            self.assertIs(fragments1, fragments2)
            mock_open.assert_called_once()

    @patch('builtins.open')
    @patch('data_loading.json.load')
    def test_load_game_data_success(self, mock_json_load, mock_open):
        """Test successful loading of game data from JSON."""
        mock_data = {"enemy_types": {}, "exploits": {}}
        mock_json_load.return_value = mock_data

        data = DataLoader.load_game_data()

        self.assertEqual(data, mock_data)
        mock_open.assert_called_once_with('game_data.json', 'r', encoding='utf-8')

    @patch('builtins.open')
    @patch('data_loading.logging')
    def test_load_game_data_fallback(self, mock_logging, mock_open):
        """Test loading game data fallback when file doesn't exist."""
        mock_open.side_effect = FileNotFoundError("File not found")

        data = DataLoader.load_game_data()

        # Should return fallback data with required keys
        self.assertIn("enemy_types", data)
        self.assertIn("exploits", data)
        self.assertIn("upgrades", data)
        self.assertIn("network_configs", data)
        mock_logging.warning.assert_called()

    @patch('builtins.open')
    @patch('data_loading.json.load')
    def test_load_config_success(self, mock_json_load, mock_open):
        """Test successful loading of configuration from JSON."""
        mock_config = {"gameplay": {}, "graphics": {}, "audio": {}}
        mock_json_load.return_value = mock_config

        config = DataLoader.load_config()

        self.assertEqual(config, mock_config)
        mock_open.assert_called_once_with('game_config.json', 'r', encoding='utf-8')

    @patch('builtins.open')
    @patch('data_loading.logging')
    def test_load_config_fallback(self, mock_logging, mock_open):
        """Test loading config fallback when file doesn't exist."""
        mock_open.side_effect = FileNotFoundError("File not found")

        config = DataLoader.load_config()

        # Should return fallback config with required keys
        self.assertIn("gameplay", config)
        self.assertIn("graphics", config)
        self.assertIn("audio", config)
        mock_logging.warning.assert_called()

    def test_get_story_fragments_convenience_function(self):
        """Test the convenience function for getting story fragments."""
        with patch.object(DataLoader, 'load_story_fragments') as mock_load:
            mock_fragments = ["Test fragment"]
            mock_load.return_value = mock_fragments

            fragments = get_story_fragments()

            self.assertEqual(fragments, mock_fragments)
            mock_load.assert_called_once()


class TestStoryIntegration(unittest.TestCase):
    """Test integration between story components."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    @patch('game_story.get_story_fragments')
    def test_complete_story_workflow(self, mock_get_fragments):
        """Test complete story discovery workflow."""
        mock_fragments = [
            "Beginning of the story...",
            "Middle of the story...",
            "End of the story..."
        ]
        mock_get_fragments.return_value = mock_fragments

        with patch('game_story.PersistentStorage') as mock_storage_class:
            mock_storage = Mock()
            mock_storage.load_data.return_value = {}
            mock_storage_class.return_value = mock_storage

            manager = StoryFragmentManager()

            # Discover fragments in order
            self.assertTrue(manager.discover_fragment(0))
            self.assertTrue(manager.discover_fragment(2))
            self.assertTrue(manager.discover_fragment(1))

            # Check progress
            discovered_count, total_count = manager.get_fragment_count()
            self.assertEqual(discovered_count, 3)
            self.assertEqual(total_count, 3)

            # Check discovered fragments
            discovered = manager.get_discovered_fragments()
            expected = [
                (0, "Beginning of the story..."),
                (1, "Middle of the story..."),
                (2, "End of the story...")
            ]
            self.assertEqual(discovered, expected)

            # Next undiscovered should be None
            self.assertIsNone(manager.get_next_undiscovered_fragment())

    @patch('game_story.get_story_fragments')
    def test_story_persistence_across_sessions(self, mock_get_fragments):
        """Test that story progress persists across game sessions."""
        mock_fragments = ["Fragment 1", "Fragment 2", "Fragment 3"]
        mock_get_fragments.return_value = mock_fragments

        # First session - discover some fragments
        with patch('game_story.PersistentStorage') as mock_storage_class1:
            mock_storage1 = Mock()
            mock_storage1.load_data.return_value = {}
            mock_storage_class1.return_value = mock_storage1

            manager1 = StoryFragmentManager()
            manager1.discover_fragment(0)
            manager1.discover_fragment(2)

            # Check that progress was saved
            expected_save_data = {
                "discovered_story_fragments": [0, 2],
                "version": "dev"
            }
            mock_storage1.save_data.assert_called_with(
                "rogue_signal_progress.json", expected_save_data
            )

        # Second session - load existing progress
        with patch('game_story.PersistentStorage') as mock_storage_class2:
            mock_storage2 = Mock()
            mock_storage2.load_data.return_value = {
                "discovered_story_fragments": [0, 2],
                "version": "dev"
            }
            mock_storage_class2.return_value = mock_storage2

            manager2 = StoryFragmentManager()

            # Should have loaded previous progress
            self.assertEqual(manager2.discovered_fragments, [0, 2])

            # Next undiscovered should be fragment 1
            self.assertEqual(manager2.get_next_undiscovered_fragment(), 1)


if __name__ == '__main__':
    unittest.main()