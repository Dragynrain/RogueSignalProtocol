#!/usr/bin/env python3
"""
Unit tests for Player damage and combat mechanics.
"""

import pytest
from game_characters import Player


class TestPlayerCombat:
    """Test player combat-related mechanics."""

    def test_player_takes_damage(self):
        """Player takes damage and returns amount taken."""
        player = Player(10, 10)

        damage_taken = player.take_damage(25)

        assert player.cpu == 75
        assert damage_taken == 25

    def test_player_death_at_zero_cpu(self):
        """Player dies when CPU reaches 0."""
        player = Player(10, 10)

        player.take_damage(100)

        assert player.cpu <= 0

    def test_player_healing(self):
        """Player can be healed (negative damage)."""
        player = Player(10, 10)
        player.cpu = 50

        player.take_damage(-20)  # Negative = healing

        assert player.cpu == 70

    def test_player_overkill_damage(self):
        """Player CPU can go negative from overkill."""
        player = Player(10, 10)
        player.cpu = 10

        player.take_damage(50)  # Overkill

        assert player.cpu <= 0