#!/usr/bin/env python3
"""
Simple unit tests for Enemy functionality.
Focus on core game mechanics only.
"""

import pytest
from unittest.mock import Mock

from game_characters import Enemy
from game_entities import Position


def test_enemy_creation():
    """Enemy creates with correct position and type."""
    pos = Position(10, 15)
    enemy = Enemy(pos, "scanner")
    
    assert enemy.position.x == 10
    assert enemy.position.y == 15
    assert enemy.type == "scanner"


def test_enemy_movement():
    """Enemy position updates correctly."""
    pos = Position(5, 10)
    enemy = Enemy(pos, "scanner")
    
    new_pos = Position(20, 25)
    enemy.position = new_pos
    
    assert enemy.position.x == 20
    assert enemy.position.y == 25


def test_enemy_basic_ai():
    """Enemy has basic AI state tracking."""
    pos = Position(10, 10)
    enemy = Enemy(pos, "scanner")
    
    # Enemy should have basic properties
    assert hasattr(enemy, 'type')
    assert enemy.type == "scanner"


def test_enemy_position_property():
    """Enemy position property works correctly."""
    pos = Position(15, 20)
    enemy = Enemy(pos, "scanner")
    
    position = enemy.position
    assert position.x == 15
    assert position.y == 20