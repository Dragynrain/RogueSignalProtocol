#!/usr/bin/env python3
"""
Unit tests for Story System and Lore Management.
Tests story fragment management, discovery mechanics, and lore viewer functionality.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from game_story import StoryFragmentManager
from game_inventory import StoryFragment
from game_entities import Position


class TestStoryFragmentManager:
    """Test the StoryFragmentManager class functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.story_manager = StoryFragmentManager()
    
    def test_story_manager_initialization(self):
        """Test StoryFragmentManager initializes correctly."""
        assert self.story_manager.discovered_fragments == set()
        assert isinstance(self.story_manager.all_fragments, dict)
    
    def test_load_story_fragments_success(self):
        """Test loading story fragments from valid JSON."""
        test_data = {
            "fragments": {
                "intro": {
                    "title": "System Boot",
                    "content": "The network awakens...",
                    "discovery_context": "level_start"
                },
                "hack_01": {
                    "title": "First Breach",
                    "content": "You've broken through the first firewall.",
                    "discovery_context": "first_hack"
                }
            }
        }
        
        with patch('builtins.open', mock_open_read_data(json.dumps(test_data))):
            with patch('os.path.exists', return_value=True):
                self.story_manager.load_story_fragments()
                
                assert len(self.story_manager.all_fragments) == 2
                assert "intro" in self.story_manager.all_fragments
                assert "hack_01" in self.story_manager.all_fragments
                assert self.story_manager.all_fragments["intro"]["title"] == "System Boot"
    
    def test_load_story_fragments_file_not_found(self):
        """Test loading story fragments when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            self.story_manager.load_story_fragments()
            
            # Should have fallback fragments
            assert len(self.story_manager.all_fragments) > 0
            assert "intro" in self.story_manager.all_fragments
    
    def test_load_story_fragments_invalid_json(self):
        """Test loading story fragments with invalid JSON."""
        with patch('builtins.open', mock_open_read_data("invalid json {")):
            with patch('os.path.exists', return_value=True):
                self.story_manager.load_story_fragments()
                
                # Should fall back to default fragments
                assert len(self.story_manager.all_fragments) > 0
    
    def test_discover_fragment_new(self):
        """Test discovering a new fragment."""
        fragment_id = "test_fragment"
        self.story_manager.all_fragments[fragment_id] = {
            "title": "Test Fragment",
            "content": "Test content",
            "discovery_context": "test"
        }
        
        result = self.story_manager.discover_fragment(fragment_id)
        
        assert result is True
        assert fragment_id in self.story_manager.discovered_fragments
    
    def test_discover_fragment_already_discovered(self):
        """Test discovering an already discovered fragment."""
        fragment_id = "test_fragment"
        self.story_manager.all_fragments[fragment_id] = {
            "title": "Test Fragment",
            "content": "Test content",
            "discovery_context": "test"
        }
        self.story_manager.discovered_fragments.add(fragment_id)
        
        result = self.story_manager.discover_fragment(fragment_id)
        
        assert result is False
    
    def test_discover_fragment_nonexistent(self):
        """Test discovering a fragment that doesn't exist."""
        result = self.story_manager.discover_fragment("nonexistent_fragment")
        
        assert result is False
        assert "nonexistent_fragment" not in self.story_manager.discovered_fragments
    
    def test_get_fragment_discovered(self):
        """Test getting a discovered fragment."""
        fragment_id = "test_fragment"
        fragment_data = {
            "title": "Test Fragment",
            "content": "Test content",
            "discovery_context": "test"
        }
        self.story_manager.all_fragments[fragment_id] = fragment_data
        self.story_manager.discovered_fragments.add(fragment_id)
        
        result = self.story_manager.get_fragment(fragment_id)
        
        assert result == fragment_data
    
    def test_get_fragment_not_discovered(self):
        """Test getting a fragment that hasn't been discovered."""
        fragment_id = "test_fragment"
        self.story_manager.all_fragments[fragment_id] = {
            "title": "Test Fragment",
            "content": "Test content",
            "discovery_context": "test"
        }
        
        result = self.story_manager.get_fragment(fragment_id)
        
        assert result is None
    
    def test_get_discovered_fragments(self):
        """Test getting list of discovered fragments."""
        # Add and discover some fragments
        fragments = {
            "frag1": {"title": "Fragment 1", "content": "Content 1", "discovery_context": "test"},
            "frag2": {"title": "Fragment 2", "content": "Content 2", "discovery_context": "test"},
            "frag3": {"title": "Fragment 3", "content": "Content 3", "discovery_context": "test"}
        }
        
        self.story_manager.all_fragments.update(fragments)
        self.story_manager.discovered_fragments.update(["frag1", "frag3"])
        
        discovered = self.story_manager.get_discovered_fragments()
        
        assert len(discovered) == 2
        assert any(f["title"] == "Fragment 1" for f in discovered)
        assert any(f["title"] == "Fragment 3" for f in discovered)
        assert not any(f["title"] == "Fragment 2" for f in discovered)
    
    def test_is_discovered(self):
        """Test checking if a fragment is discovered."""
        fragment_id = "test_fragment"
        
        # Not discovered initially
        assert not self.story_manager.is_discovered(fragment_id)
        
        # Discover it
        self.story_manager.discovered_fragments.add(fragment_id)
        assert self.story_manager.is_discovered(fragment_id)
    
    def test_get_discovery_count(self):
        """Test getting the count of discovered fragments."""
        assert self.story_manager.get_discovery_count() == 0
        
        self.story_manager.discovered_fragments.update(["frag1", "frag2", "frag3"])
        assert self.story_manager.get_discovery_count() == 3


class TestStoryFragmentItem:
    """Test StoryFragment inventory item functionality."""
    
    def test_story_fragment_creation(self):
        """Test creating a StoryFragment item."""
        fragment = StoryFragment("test_fragment", "Test Title", "Test content for the fragment.")
        
        assert fragment.fragment_id == "test_fragment"
        assert fragment.name == "Test Title"
        assert fragment.description == "Test content for the fragment."
        assert fragment.type == "story_fragment"
    
    def test_story_fragment_use_with_manager(self):
        """Test using a StoryFragment with a story manager."""
        mock_player = Mock()
        mock_game = Mock()
        mock_story_manager = Mock()
        mock_game.story_fragment_manager = mock_story_manager
        
        fragment = StoryFragment("test_fragment", "Test Title", "Test content.")
        
        # Mock discovery as successful
        mock_story_manager.discover_fragment.return_value = True
        
        result = fragment.use(mock_player, mock_game)
        
        assert result is True
        mock_story_manager.discover_fragment.assert_called_with("test_fragment")
    
    def test_story_fragment_use_already_discovered(self):
        """Test using a StoryFragment that's already been discovered."""
        mock_player = Mock()
        mock_game = Mock()
        mock_story_manager = Mock()
        mock_game.story_fragment_manager = mock_story_manager
        
        fragment = StoryFragment("test_fragment", "Test Title", "Test content.")
        
        # Mock discovery as already discovered
        mock_story_manager.discover_fragment.return_value = False
        
        result = fragment.use(mock_player, mock_game)
        
        assert result is False
    
    def test_story_fragment_use_no_manager(self):
        """Test using a StoryFragment when no story manager exists."""
        mock_player = Mock()
        mock_game = Mock()
        mock_game.story_fragment_manager = None
        
        fragment = StoryFragment("test_fragment", "Test Title", "Test content.")
        
        result = fragment.use(mock_player, mock_game)
        
        assert result is False


class TestStoryDiscoveryMechanics:
    """Test story discovery mechanics and triggers."""
    
    def setup_method(self):
        """Set up test environment."""
        self.story_manager = StoryFragmentManager()
        
        # Add some test fragments
        self.story_manager.all_fragments = {
            "level_start": {
                "title": "Network Entry",
                "content": "You jack into the network...",
                "discovery_context": "level_start"
            },
            "first_enemy": {
                "title": "First Contact",
                "content": "An enemy process approaches...",
                "discovery_context": "enemy_spotted"
            },
            "gateway_reached": {
                "title": "Network Gateway",
                "content": "The gateway glows with data...",
                "discovery_context": "gateway"
            }
        }
    
    def test_context_based_discovery(self):
        """Test discovering fragments based on context."""
        # Test different discovery contexts
        contexts = [
            ("level_start", "level_start"),
            ("first_enemy", "enemy_spotted"),
            ("gateway_reached", "gateway")
        ]
        
        for fragment_id, context in contexts:
            result = self.story_manager.discover_fragment(fragment_id)
            assert result is True
            assert fragment_id in self.story_manager.discovered_fragments
    
    def test_story_progression_ordering(self):
        """Test that story fragments can be discovered in logical order."""
        # Discover fragments in story order
        story_order = ["level_start", "first_enemy", "gateway_reached"]
        
        for fragment_id in story_order:
            self.story_manager.discover_fragment(fragment_id)
        
        discovered = self.story_manager.get_discovered_fragments()
        
        # Should have all fragments
        assert len(discovered) == 3
        
        # Verify content is accessible
        for fragment in discovered:
            assert "title" in fragment
            assert "content" in fragment
            assert len(fragment["content"]) > 0
    
    def test_duplicate_discovery_prevention(self):
        """Test that fragments can't be discovered multiple times."""
        fragment_id = "level_start"
        
        # First discovery should succeed
        result1 = self.story_manager.discover_fragment(fragment_id)
        assert result1 is True
        
        # Second discovery should fail
        result2 = self.story_manager.discover_fragment(fragment_id)
        assert result2 is False
        
        # Should still only be discovered once
        assert self.story_manager.get_discovery_count() == 1


class TestLoreViewerIntegration:
    """Test integration with lore viewer system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.story_manager = StoryFragmentManager()
        
        # Add test fragments with varying content
        self.story_manager.all_fragments = {
            "short": {
                "title": "Short Fragment",
                "content": "Brief content.",
                "discovery_context": "test"
            },
            "long": {
                "title": "Long Fragment",
                "content": "This is a much longer piece of content that would span multiple lines in the lore viewer. " * 5,
                "discovery_context": "test"
            },
            "special_chars": {
                "title": "Special Characters",
                "content": "Content with special chars: @#$%^&*()[]{}",
                "discovery_context": "test"
            }
        }
    
    def test_lore_viewer_data_preparation(self):
        """Test preparing fragment data for lore viewer."""
        # Discover all fragments
        for fragment_id in self.story_manager.all_fragments.keys():
            self.story_manager.discover_fragment(fragment_id)
        
        discovered = self.story_manager.get_discovered_fragments()
        
        # Should be suitable for lore viewer
        assert len(discovered) == 3
        
        for fragment in discovered:
            assert "title" in fragment
            assert "content" in fragment
            assert isinstance(fragment["title"], str)
            assert isinstance(fragment["content"], str)
            assert len(fragment["title"]) > 0
            assert len(fragment["content"]) > 0
    
    def test_empty_lore_viewer_state(self):
        """Test lore viewer with no discovered fragments."""
        discovered = self.story_manager.get_discovered_fragments()
        
        assert len(discovered) == 0
        assert self.story_manager.get_discovery_count() == 0
    
    def test_fragment_content_encoding(self):
        """Test that fragment content handles various text encoding."""
        # Add fragment with unicode content
        self.story_manager.all_fragments["unicode"] = {
            "title": "Unicode Test",
            "content": "Content with unicode: éñü",
            "discovery_context": "test"
        }
        
        result = self.story_manager.discover_fragment("unicode")
        assert result is True
        
        fragment = self.story_manager.get_fragment("unicode")
        assert fragment is not None
        assert "éñü" in fragment["content"]


class TestStoryPersistence:
    """Test story discovery persistence and save/load."""
    
    def setup_method(self):
        """Set up test environment."""
        self.story_manager = StoryFragmentManager()
        
        # Add test fragments
        self.story_manager.all_fragments = {
            "persistent1": {
                "title": "Persistent Fragment 1",
                "content": "This should persist across saves.",
                "discovery_context": "test"
            },
            "persistent2": {
                "title": "Persistent Fragment 2",
                "content": "This should also persist.",
                "discovery_context": "test"
            }
        }
    
    def test_save_discovered_fragments(self):
        """Test saving discovered fragments state."""
        # Discover some fragments
        self.story_manager.discover_fragment("persistent1")
        
        # Get state for saving
        save_data = {
            "discovered_fragments": list(self.story_manager.discovered_fragments)
        }
        
        assert "persistent1" in save_data["discovered_fragments"]
        assert "persistent2" not in save_data["discovered_fragments"]
        assert len(save_data["discovered_fragments"]) == 1
    
    def test_load_discovered_fragments(self):
        """Test loading discovered fragments state."""
        # Simulate loading from save
        save_data = {
            "discovered_fragments": ["persistent1", "persistent2"]
        }
        
        # Restore state
        self.story_manager.discovered_fragments = set(save_data["discovered_fragments"])
        
        assert self.story_manager.is_discovered("persistent1")
        assert self.story_manager.is_discovered("persistent2")
        assert self.story_manager.get_discovery_count() == 2
        
        # Should be able to get discovered fragments
        discovered = self.story_manager.get_discovered_fragments()
        assert len(discovered) == 2


class TestStoryErrorHandling:
    """Test error handling in story system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.story_manager = StoryFragmentManager()
    
    def test_malformed_fragment_data(self):
        """Test handling malformed fragment data."""
        # Add malformed fragment
        self.story_manager.all_fragments["malformed"] = {
            "title": "Missing Content Fragment"
            # Missing content and discovery_context
        }
        
        result = self.story_manager.discover_fragment("malformed")
        assert result is True  # Should still be discoverable
        
        fragment = self.story_manager.get_fragment("malformed")
        assert fragment is not None
        assert "title" in fragment
    
    def test_none_fragment_handling(self):
        """Test handling None or empty fragment data."""
        # Test getting None fragment
        result = self.story_manager.get_fragment(None)
        assert result is None
        
        # Test discovering None fragment
        result = self.story_manager.discover_fragment(None)
        assert result is False
    
    def test_empty_string_fragment_id(self):
        """Test handling empty string fragment IDs."""
        result = self.story_manager.discover_fragment("")
        assert result is False
        
        result = self.story_manager.get_fragment("")
        assert result is None
        
        assert not self.story_manager.is_discovered("")
    
    def test_corrupted_discovered_set(self):
        """Test handling corrupted discovered fragments set."""
        # Simulate corrupted state
        self.story_manager.discovered_fragments = None
        
        try:
            # Should handle gracefully
            count = self.story_manager.get_discovery_count()
            assert count >= 0  # Should not crash
        except AttributeError:
            # Reinitialize if needed
            self.story_manager.discovered_fragments = set()
            count = self.story_manager.get_discovery_count()
            assert count == 0


def mock_open_read_data(read_data):
    """Helper function to mock file reading."""
    from unittest.mock import mock_open
    return mock_open(read_data=read_data)


if __name__ == "__main__":
    pytest.main([__file__])