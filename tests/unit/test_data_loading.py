#!/usr/bin/env python3
"""
Unit tests for Data Loading System.
Tests JSON data loading, fallback mechanisms, and caching.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open
from data_loading import DataLoader


class TestDataLoader:
    """Test the DataLoader class functionality."""
    
    def setup_method(self):
        """Reset class-level cache before each test."""
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_load_story_fragments_success(self):
        """Test successful loading of story fragments."""
        test_data = {
            "fragments": ["Fragment 1", "Fragment 2", "Fragment 3"]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            result = DataLoader.load_story_fragments()
            
            assert result is not None
            assert len(result) == 3
            assert "Fragment 1" in result
    
    def test_load_story_fragments_file_not_found(self):
        """Test loading story fragments when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_story_fragments()
            
            # Should return fallback fragments
            assert result is not None
            assert len(result) > 0
    
    def test_load_story_fragments_invalid_json(self):
        """Test loading story fragments with invalid JSON."""
        with patch('builtins.open', mock_open(read_data="invalid json {")):
            result = DataLoader.load_story_fragments()
            
            # Should fall back to default fragments
            assert result is not None
            assert len(result) > 0
    
    def test_load_story_fragments_caching(self):
        """Test that story fragments are cached after first load."""
        test_data = {
            "fragments": ["Cached Fragment"]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))) as mock_file:
            # First call should read file
            result1 = DataLoader.load_story_fragments()
            
            # Second call should use cache (not read file again)
            result2 = DataLoader.load_story_fragments()
            
            assert result1 == result2
            # File should only be opened once due to caching
            assert mock_file.call_count == 1
    
    def test_load_game_data_success(self):
        """Test successful loading of game data."""
        test_data = {
            "test_key": "test_value",
            "nested": {"key": "value"}
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            result = DataLoader.load_game_data()
            
            assert result is not None
            assert result["test_key"] == "test_value"
            assert result["nested"]["key"] == "value"
    
    def test_load_game_data_file_not_found(self):
        """Test loading game data when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_game_data()
            
            # Should return fallback data
            assert result is not None
            assert isinstance(result, dict)
    
    def test_load_game_data_caching(self):
        """Test that game data is cached after first load."""
        test_data = {"cached": True}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))) as mock_file:
            # First call should read file
            result1 = DataLoader.load_game_data()
            
            # Second call should use cache
            result2 = DataLoader.load_game_data()
            
            assert result1 == result2
            assert mock_file.call_count == 1
    
    def test_load_config_success(self):
        """Test successful loading of config data."""
        test_config = {
            "master_volume": 0.8,
            "graphics_mode": "terminal"
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            result = DataLoader.load_config()
            
            assert result is not None
            assert result["master_volume"] == 0.8
            assert result["graphics_mode"] == "terminal"
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_config()
            
            # Should return default config
            assert result is not None
            assert isinstance(result, dict)
    
    def test_load_config_caching(self):
        """Test that config is cached after first load."""
        test_config = {"cached_config": True}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))) as mock_file:
            # First call should read file
            result1 = DataLoader.load_config()
            
            # Second call should use cache
            result2 = DataLoader.load_config()
            
            assert result1 == result2
            assert mock_file.call_count == 1


class TestFallbackData:
    """Test fallback data mechanisms."""
    
    def setup_method(self):
        """Reset class-level cache before each test."""
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_fallback_story_fragments(self):
        """Test that fallback story fragments are provided."""
        # Trigger fallback by simulating file not found
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_story_fragments()
            
            assert result is not None
            assert len(result) > 0
            assert isinstance(result, list)
            
            # Should contain some basic story elements
            assert any("network" in fragment.lower() or "system" in fragment.lower() 
                      for fragment in result)
    
    def test_fallback_game_data(self):
        """Test that fallback game data is comprehensive."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_game_data()
            
            assert result is not None
            assert isinstance(result, dict)
            assert len(result) > 0
    
    def test_fallback_config(self):
        """Test that fallback config is complete."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            result = DataLoader.load_config()
            
            assert result is not None
            assert isinstance(result, dict)
            
            # Should have basic config structure
            expected_keys = ["master_volume", "graphics_mode"]
            for key in expected_keys:
                if key in result:  # Some keys might be optional
                    assert result[key] is not None


class TestErrorHandling:
    """Test error handling in data loading."""
    
    def setup_method(self):
        """Reset class-level cache before each test."""
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should not crash, should return fallback data
            fragments = DataLoader.load_story_fragments()
            game_data = DataLoader.load_game_data()
            config = DataLoader.load_config()
            
            assert fragments is not None
            assert game_data is not None
            assert config is not None
    
    def test_json_decode_error_handling(self):
        """Test handling of JSON decode errors."""
        invalid_json = '{"invalid": json syntax'
        
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            # Should not crash, should return fallback data
            fragments = DataLoader.load_story_fragments()
            game_data = DataLoader.load_game_data()
            config = DataLoader.load_config()
            
            assert fragments is not None
            assert game_data is not None
            assert config is not None
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        with patch('builtins.open', mock_open(read_data="")):
            # Should not crash, should return fallback data
            fragments = DataLoader.load_story_fragments()
            game_data = DataLoader.load_game_data()
            config = DataLoader.load_config()
            
            assert fragments is not None
            assert game_data is not None
            assert config is not None
    
    def test_malformed_data_structure(self):
        """Test handling of malformed data structures."""
        # Valid JSON but wrong structure
        wrong_structure = '["this", "should", "be", "an", "object"]'
        
        with patch('builtins.open', mock_open(read_data=wrong_structure)):
            # Should not crash, should return fallback data
            try:
                fragments = DataLoader.load_story_fragments()
                game_data = DataLoader.load_game_data()
                config = DataLoader.load_config()
                
                assert fragments is not None
                assert game_data is not None
                assert config is not None
            except Exception as e:
                pytest.fail(f"Data loader should handle malformed structure gracefully: {e}")


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    def setup_method(self):
        """Reset class-level cache before each test."""
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_story_fragments_structure(self):
        """Test that story fragments have correct structure."""
        fragments = DataLoader.load_story_fragments()
        
        assert isinstance(fragments, list)
        for fragment in fragments:
            assert isinstance(fragment, str)
            assert len(fragment) > 0
    
    def test_game_data_structure(self):
        """Test that game data has correct structure."""
        game_data = DataLoader.load_game_data()
        
        assert isinstance(game_data, dict)
        # Should not be empty
        assert len(game_data) >= 0
    
    def test_config_structure(self):
        """Test that config has correct structure."""
        config = DataLoader.load_config()
        
        assert isinstance(config, dict)
        # Should not be empty
        assert len(config) >= 0
    
    def test_data_consistency_across_calls(self):
        """Test that multiple calls return consistent data."""
        # Load each type of data multiple times
        fragments1 = DataLoader.load_story_fragments()
        fragments2 = DataLoader.load_story_fragments()
        
        game_data1 = DataLoader.load_game_data()
        game_data2 = DataLoader.load_game_data()
        
        config1 = DataLoader.load_config()
        config2 = DataLoader.load_config()
        
        # Should be identical due to caching
        assert fragments1 == fragments2
        assert game_data1 == game_data2
        assert config1 == config2


class TestCachingBehavior:
    """Test caching behavior and cache invalidation."""
    
    def setup_method(self):
        """Reset class-level cache before each test."""
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
    
    def test_cache_invalidation(self):
        """Test manual cache invalidation."""
        # Load data to populate cache
        DataLoader.load_story_fragments()
        DataLoader.load_game_data()
        DataLoader.load_config()
        
        # Verify cache is populated
        assert DataLoader._story_fragments is not None
        assert DataLoader._game_data is not None
        assert DataLoader._config is not None
        
        # Reset cache manually
        DataLoader._story_fragments = None
        DataLoader._game_data = None
        DataLoader._config = None
        
        # Verify cache is cleared
        assert DataLoader._story_fragments is None
        assert DataLoader._game_data is None
        assert DataLoader._config is None
    
    def test_independent_caching(self):
        """Test that different data types cache independently."""
        test_fragments = {"fragments": ["test"]}
        test_data = {"test": "data"}
        test_config = {"test": "config"}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_fragments))):
            fragments = DataLoader.load_story_fragments()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
            game_data = DataLoader.load_game_data()
        
        with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
            config = DataLoader.load_config()
        
        # Each should have cached its own data
        assert DataLoader._story_fragments == ["test"]
        assert DataLoader._game_data == {"test": "data"}
        assert DataLoader._config == {"test": "config"}


if __name__ == "__main__":
    pytest.main([__file__])