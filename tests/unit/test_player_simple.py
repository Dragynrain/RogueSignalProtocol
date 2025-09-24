#!/usr/bin/env python3
"""
Simple unit tests for Player functionality.
Focus on core game mechanics only.
"""

import pytest
from unittest.mock import Mock

from game_characters import Player


def test_player_creation():
    """Player creates with correct position and stats."""
    player = Player(10, 15)
    
    assert player.x == 10
    assert player.y == 15
    assert player.cpu == 100
    assert player.heat == 0


def test_player_movement():
    """Player position updates correctly."""
    player = Player(5, 10)
    
    player.x = 20
    player.y = 25
    
    assert player.x == 20
    assert player.y == 25


def test_player_damage():
    """Player takes damage correctly."""
    player = Player(10, 10)
    
    damage_taken = player.take_damage(25)
    
    assert player.cpu == 75
    assert damage_taken == 25


def test_player_death():
    """Player dies when CPU reaches 0."""
    player = Player(10, 10)
    
    player.take_damage(100)
    
    assert player.cpu <= 0


def test_player_healing():
    """Player can be healed (negative damage)."""
    player = Player(10, 10)
    player.cpu = 50
    
    player.take_damage(-20)  # Negative = healing
    
    assert player.cpu == 70


def test_player_stats_boundaries():
    """Player handles boundary conditions."""
    player = Player(0, 0)  # Corner position
    assert player.x == 0
    assert player.y == 0
    
    player = Player(-1, -1)  # Negative position (should be allowed)
    assert player.x == -1
    assert player.y == -1