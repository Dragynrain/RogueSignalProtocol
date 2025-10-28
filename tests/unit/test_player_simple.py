#!/usr/bin/env python3
"""
Unit tests for Player damage and combat mechanics.
"""

import pytest
from tests.fixtures.simple_fixtures import player


class TestPlayerCombat:
    """Test player combat-related mechanics."""

    def test_player_takes_damage(self):
        """Player takes damage and returns amount taken."""
        test_player = player(10, 10, 100)

        damage_taken = test_player.take_damage(25)

        assert test_player.cpu == 75
        assert damage_taken == 25

    def test_player_death_at_zero_cpu(self):
        """Player dies when CPU reaches 0."""
        test_player = player(10, 10, 100)

        test_player.take_damage(100)

        assert test_player.cpu <= 0

    def test_player_healing(self):
        """Player can be healed (negative damage)."""
        test_player = player(10, 10, 100)
        test_player.cpu = 50

        test_player.take_damage(-20)  # Negative = healing

        assert test_player.cpu == 70

    def test_player_overkill_damage(self):
        """Player CPU can go negative from overkill."""
        test_player = player(10, 10, 100)
        test_player.cpu = 10

        test_player.take_damage(50)  # Overkill

        assert test_player.cpu <= 0