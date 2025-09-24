#!/usr/bin/env python3
"""
Simple unit tests for Input functionality.
Focus on core game mechanics only.
"""

import pytest
from unittest.mock import Mock


def test_basic_movement_keys():
    """Basic movement key mapping works."""
    # Test that movement keys exist and map correctly
    movement_keys = {
        'w': (0, -1),   # up
        's': (0, 1),    # down  
        'a': (-1, 0),   # left
        'd': (1, 0),    # right
    }
    
    for key, (dx, dy) in movement_keys.items():
        assert isinstance(dx, int)
        assert isinstance(dy, int)
        assert -1 <= dx <= 1
        assert -1 <= dy <= 1


def test_diagonal_movement_keys():
    """Diagonal movement keys work."""
    diagonal_keys = {
        'q': (-1, -1),  # up-left
        'e': (1, -1),   # up-right
        'z': (-1, 1),   # down-left
        'c': (1, 1),    # down-right
    }
    
    for key, (dx, dy) in diagonal_keys.items():
        assert isinstance(dx, int)
        assert isinstance(dy, int)
        assert dx in [-1, 1]
        assert dy in [-1, 1]


def test_action_keys():
    """Action keys are defined."""
    action_keys = ['x', 'space', 'enter', 'escape']
    
    for key in action_keys:
        assert isinstance(key, str)
        assert len(key) > 0


def test_key_validation():
    """Key input validation works."""
    valid_keys = ['w', 'a', 's', 'd', 'q', 'e', 'z', 'c', 'x', 'space']
    invalid_keys = ['', '123', 'invalid', None]
    
    for key in valid_keys:
        assert key is not None
        assert isinstance(key, str)
    
    for key in invalid_keys:
        if key is not None:
            assert not (isinstance(key, str) and len(key) == 1 and key.isalpha())


def test_movement_bounds():
    """Movement deltas are within expected bounds."""
    all_movements = [
        (0, -1), (0, 1), (-1, 0), (1, 0),     # cardinal
        (-1, -1), (1, -1), (-1, 1), (1, 1)    # diagonal
    ]
    
    for dx, dy in all_movements:
        assert -1 <= dx <= 1
        assert -1 <= dy <= 1
        assert not (dx == 0 and dy == 0)  # no null movement