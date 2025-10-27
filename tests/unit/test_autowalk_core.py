#!/usr/bin/env python3
"""
Unit tests for auto-walk core functionality.

Tests the AutoWalk class methods and state management without
complex game engine setup.
"""

import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from game_autowalk import AutoWalk
from game_entities import Position


class TestAutoWalkState(unittest.TestCase):
    """Test auto-walk state management."""

    def setUp(self):
        """Set up test fixtures."""
        self.autowalk = AutoWalk()

    def test_initial_state_inactive(self):
        """Test auto-walk starts inactive."""
        self.assertFalse(self.autowalk.is_active())
        self.assertEqual(len(self.autowalk.path), 0)
        self.assertEqual(self.autowalk.current_step, 0)

    def test_stop_sets_inactive(self):
        """Test stop() deactivates auto-walk."""
        # Manually set active for testing
        self.autowalk.active = True
        self.autowalk.path = [Position(1, 1), Position(2, 2)]

        self.autowalk.stop("Test stop")

        self.assertFalse(self.autowalk.is_active())
        self.assertEqual(len(self.autowalk.path), 0)
        self.assertEqual(self.autowalk.current_step, 0)
        self.assertEqual(self.autowalk.stop_reason, "Test stop")

    def test_cancel_stops_with_reason(self):
        """Test cancel() stops with user cancellation reason."""
        self.autowalk.active = True

        self.autowalk.cancel()

        self.assertFalse(self.autowalk.is_active())
        self.assertIsNotNone(self.autowalk.stop_reason)
        self.assertIn("cancel", self.autowalk.stop_reason.lower())

    def test_advance_step_increments(self):
        """Test advance_step() increments step counter."""
        self.autowalk.active = True
        self.autowalk.path = [Position(1, 1), Position(2, 2), Position(3, 3)]
        self.autowalk.current_step = 0

        self.autowalk.advance_step()

        self.assertEqual(self.autowalk.current_step, 1)

    def test_get_remaining_path_when_inactive(self):
        """Test get_remaining_path returns empty list when inactive."""
        result = self.autowalk.get_remaining_path()

        self.assertEqual(len(result), 0)

    def test_get_remaining_path_returns_subset(self):
        """Test get_remaining_path returns remaining positions."""
        self.autowalk.active = True
        self.autowalk.path = [Position(1, 1), Position(2, 2), Position(3, 3)]
        self.autowalk.current_step = 1

        remaining = self.autowalk.get_remaining_path()

        self.assertEqual(len(remaining), 2)
        self.assertEqual(remaining[0], Position(2, 2))
        self.assertEqual(remaining[1], Position(3, 3))


class TestAutoWalkPathManagement(unittest.TestCase):
    """Test path management without full game setup."""

    def setUp(self):
        """Set up test fixtures."""
        self.autowalk = AutoWalk()

    def test_path_storage(self):
        """Test path can be stored and retrieved."""
        test_path = [Position(1, 1), Position(2, 2), Position(3, 3)]
        self.autowalk.path = test_path
        self.autowalk.active = True

        self.assertEqual(len(self.autowalk.path), 3)
        self.assertEqual(self.autowalk.path[0], Position(1, 1))
        self.assertEqual(self.autowalk.path[-1], Position(3, 3))

    def test_destination_tracking(self):
        """Test destination is stored."""
        dest = Position(10, 10)
        self.autowalk.destination = dest

        self.assertEqual(self.autowalk.destination, dest)


if __name__ == '__main__':
    unittest.main()
