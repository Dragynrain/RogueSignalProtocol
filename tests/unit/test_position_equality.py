#!/usr/bin/env python3
"""
Tests for Position equality and related property helpers.

These tests cover critical bugs that were found during code review:
1. Position equality should use __eq__ not distance_to() == 0
2. Enemy.is_disabled property
3. GameStateManager.is_threat_scan_active property
"""


from rsp.entities.position import Position


class TestPositionEquality:
    """Test Position equality comparisons - NEVER use distance_to() == 0."""

    def test_same_position_equal(self):
        """Identical positions should be equal."""
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)
        assert pos1 == pos2

    def test_different_position_not_equal(self):
        """Different positions should not be equal."""
        pos1 = Position(5, 10)
        pos2 = Position(6, 10)
        assert pos1 != pos2

    def test_equality_vs_distance_zero(self):
        """Position equality is safer than distance_to() == 0.

        This test documents why we use == instead of distance_to() == 0:
        - distance_to() returns float, comparing floats to 0 can be unreliable
        - __eq__ does exact integer comparison
        """
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)

        # The correct way (what we use now)
        assert pos1 == pos2

        # The old buggy way (what we fixed)
        # We still test distance_to() works, but prefer ==
        assert pos1.distance_to(pos2) == 0.0

    def test_equality_with_none(self):
        """Position should not equal None."""
        pos = Position(5, 10)
        assert pos != None  # noqa: E711

    def test_equality_with_different_type(self):
        """Position should not equal non-Position objects."""
        pos = Position(5, 10)
        assert pos != (5, 10)  # Tuple is different type
        assert pos != "5,10"

    def test_position_hash_equals(self):
        """Equal positions should have equal hashes (for dict/set use)."""
        pos1 = Position(5, 10)
        pos2 = Position(5, 10)
        assert hash(pos1) == hash(pos2)

    def test_position_in_set(self):
        """Positions should work in sets (uses __hash__ and __eq__)."""
        pos_set = {Position(1, 2), Position(3, 4), Position(1, 2)}
        assert len(pos_set) == 2  # Duplicate should be deduplicated


class TestEnemyIsDisabledProperty:
    """Test Enemy.is_disabled property."""

    def test_enemy_not_disabled_by_default(self):
        """New enemies should not be disabled."""
        from rsp.entities.characters import Enemy
        from rsp.entities.position import Position

        enemy = Enemy(Position(10, 10), "patrol")
        assert not enemy.is_disabled
        assert enemy.disabled_turns == 0

    def test_enemy_is_disabled_when_turns_positive(self):
        """Enemy with positive disabled_turns should be disabled."""
        from rsp.entities.characters import Enemy
        from rsp.entities.position import Position

        enemy = Enemy(Position(10, 10), "patrol")
        enemy.disabled_turns = 3
        assert enemy.is_disabled

    def test_enemy_not_disabled_when_turns_zero(self):
        """Enemy with zero disabled_turns should not be disabled."""
        from rsp.entities.characters import Enemy
        from rsp.entities.position import Position

        enemy = Enemy(Position(10, 10), "patrol")
        enemy.disabled_turns = 0
        assert not enemy.is_disabled


class TestGameStateIsThreatScanActive:
    """Test GameStateManager.is_threat_scan_active property."""

    def test_threat_scan_inactive_by_default(self):
        """New game state should not have threat scan active."""
        from rsp.core.state import GameStateManager

        state = GameStateManager()
        assert not state.is_threat_scan_active
        assert state.threat_scan_turns == 0

    def test_threat_scan_active_when_turns_positive(self):
        """Threat scan should be active when turns are positive."""
        from rsp.core.state import GameStateManager

        state = GameStateManager()
        state.threat_scan_turns = 5
        assert state.is_threat_scan_active

    def test_threat_scan_inactive_when_turns_zero(self):
        """Threat scan should be inactive when turns are zero."""
        from rsp.core.state import GameStateManager

        state = GameStateManager()
        state.threat_scan_turns = 0
        assert not state.is_threat_scan_active


class TestGhostPositionCleanup:
    """Test that ghost position cleanup uses proper equality."""

    def test_ghost_position_matches_enemy_position(self):
        """Verify ghost cleanup logic works with position equality.

        This tests the fix for the bug where we used distance_to() == 0
        instead of position equality in _cleanup_ghost_positions().
        """
        from rsp.entities.position import Position

        # Simulate the ghost cleanup check
        ghost_pos = Position(15, 20)
        enemy_pos = Position(15, 20)

        # The correct way (what we use now)
        enemy_at_ghost = enemy_pos == ghost_pos
        assert enemy_at_ghost

        # Different positions should not match
        other_pos = Position(16, 20)
        enemy_at_other = other_pos == ghost_pos
        assert not enemy_at_other
