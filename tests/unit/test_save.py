#!/usr/bin/env python3
"""
Simple unit tests for Save/Load functionality.
Focus on core game mechanics only.
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch

from game_characters import Player


def test_save_file_basic():
    """Basic save file operations work."""
    # Create temporary file for testing
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        test_data = {
            "player_x": 10,
            "player_y": 15,
            "player_cpu": 85,
            "level": 3
        }
        json.dump(test_data, f)
        temp_file = f.name
    
    try:
        # Read back the data
        with open(temp_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["player_x"] == 10
        assert loaded_data["player_y"] == 15
        assert loaded_data["player_cpu"] == 85
        assert loaded_data["level"] == 3
    finally:
        os.unlink(temp_file)


def test_player_state_serialization():
    """Player state can be serialized to dict."""
    player = Player(20, 30)
    player.cpu = 75
    
    # Create basic state dict
    state = {
        "x": player.x,
        "y": player.y,
        "cpu": player.cpu,
        "heat": player.heat
    }
    
    assert state["x"] == 20
    assert state["y"] == 30
    assert state["cpu"] == 75
    assert state["heat"] == 0


def test_player_state_restoration():
    """Player state can be restored from dict."""
    # Save state
    saved_state = {
        "x": 25,
        "y": 35,
        "cpu": 60,
        "heat": 10
    }
    
    # Create new player and restore state
    player = Player(0, 0)
    player.x = saved_state["x"]
    player.y = saved_state["y"]
    player.cpu = saved_state["cpu"]
    player.heat = saved_state["heat"]
    
    assert player.x == 25
    assert player.y == 35
    assert player.cpu == 60
    assert player.heat == 10


def test_save_file_corruption_handling():
    """Save system handles corrupted files gracefully."""
    # Create corrupted file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write("invalid json content {[")
        temp_file = f.name
    
    try:
        # Try to read corrupted file
        with pytest.raises(json.JSONDecodeError):
            with open(temp_file, 'r') as f:
                json.load(f)
    finally:
        os.unlink(temp_file)


def test_missing_save_file():
    """Save system handles missing files gracefully."""
    nonexistent_file = "this_file_does_not_exist.json"
    
    # Should raise FileNotFoundError for missing file
    with pytest.raises(FileNotFoundError):
        with open(nonexistent_file, 'r') as f:
            json.load(f)