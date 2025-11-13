"""
Test grid distance calculations for exploits and effects.

Ensures that diagonals are treated as distance 1 for gameplay purposes,
not ~1.414 as with Euclidean distance.
"""

import pytest

from game_entities import Position


class TestGridDistance:
    """Test Chebyshev (grid) distance calculations."""

    def test_orthogonal_distance(self):
        """Test distance to orthogonal neighbors is 1."""
        center = Position(5, 5)

        # North
        assert center.grid_distance_to(Position(5, 4)) == 1
        # South
        assert center.grid_distance_to(Position(5, 6)) == 1
        # East
        assert center.grid_distance_to(Position(6, 5)) == 1
        # West
        assert center.grid_distance_to(Position(4, 5)) == 1

    def test_diagonal_distance(self):
        """Test distance to diagonal neighbors is 1 (NOT ~1.414)."""
        center = Position(5, 5)

        # Northeast
        assert center.grid_distance_to(Position(6, 4)) == 1
        # Southeast
        assert center.grid_distance_to(Position(6, 6)) == 1
        # Southwest
        assert center.grid_distance_to(Position(4, 6)) == 1
        # Northwest
        assert center.grid_distance_to(Position(4, 4)) == 1

    def test_all_8_adjacent_tiles_are_range_1(self):
        """Test that all 8 surrounding tiles are exactly distance 1."""
        center = Position(10, 10)

        # All 8 adjacent tiles
        adjacent = [
            Position(9, 9),  # NW
            Position(10, 9),  # N
            Position(11, 9),  # NE
            Position(11, 10),  # E
            Position(11, 11),  # SE
            Position(10, 11),  # S
            Position(9, 11),  # SW
            Position(9, 10),  # W
        ]

        for adj_pos in adjacent:
            assert (
                center.grid_distance_to(adj_pos) == 1
            ), f"Position {adj_pos} should be distance 1 from {center}"

    def test_distant_positions(self):
        """Test grid distance for non-adjacent positions."""
        center = Position(0, 0)

        # Two steps orthogonal
        assert center.grid_distance_to(Position(2, 0)) == 2
        assert center.grid_distance_to(Position(0, 2)) == 2

        # Two steps diagonal
        assert center.grid_distance_to(Position(2, 2)) == 2

        # Mixed distance (takes max of x/y difference)
        assert center.grid_distance_to(Position(3, 1)) == 3
        assert center.grid_distance_to(Position(1, 3)) == 3
        assert center.grid_distance_to(Position(5, 2)) == 5

    def test_comparison_euclidean_vs_grid(self):
        """Test that Euclidean and grid distances differ for diagonals."""
        center = Position(0, 0)
        diagonal = Position(1, 1)

        # Euclidean distance to diagonal is sqrt(2) ≈ 1.414
        euclidean = center.distance_to(diagonal)
        assert 1.4 < euclidean < 1.5

        # Grid distance to diagonal is exactly 1
        grid = center.grid_distance_to(diagonal)
        assert grid == 1

        # They should be different
        assert euclidean != grid

    def test_zero_distance(self):
        """Test distance to self is 0."""
        pos = Position(5, 5)
        assert pos.grid_distance_to(pos) == 0

    def test_grid_distance_none_raises_error(self):
        """Test that distance to None raises ValueError."""
        pos = Position(5, 5)
        with pytest.raises(ValueError, match="Cannot calculate distance to None"):
            pos.grid_distance_to(None)


class TestBufferOverflowRange:
    """Test that buffer overflow can target diagonals."""

    def test_buffer_overflow_targets_all_8_adjacent(self):
        """
        Test that buffer overflow (range 1) can target all 8 adjacent tiles.

        This is a critical gameplay mechanic - range-1 exploits MUST work
        on diagonals, not just orthogonal neighbors.
        """
        from unittest.mock import Mock

        from game_combat import ExploitSystem
        from game_data import GameData

        # Create mock game
        game = Mock()
        game.player = Mock()
        game.player.position = Position(10, 10)
        game.player.inventory_manager = Mock()
        game.player.inventory_manager.equipped_exploits = ["buffer_overflow"]
        game.player.heat = 0
        game.player.max_heat = 100
        game.player.temporary_effects = {"exploit_efficiency_turns": 0}
        game.message_log = Mock()
        game.sound_manager = Mock()
        game.enemies = []

        # Create exploit system
        exploit_system = ExploitSystem(game)
        exploit = GameData.EXPLOITS["buffer_overflow"]

        # Test all 8 adjacent positions
        adjacent_positions = [
            Position(9, 9),  # NW diagonal
            Position(10, 9),  # N orthogonal
            Position(11, 9),  # NE diagonal
            Position(11, 10),  # E orthogonal
            Position(11, 11),  # SE diagonal
            Position(10, 11),  # S orthogonal
            Position(9, 11),  # SW diagonal
            Position(9, 10),  # W orthogonal
        ]

        for pos in adjacent_positions:
            # Should pass validation (even though no enemy at target)
            result = exploit_system._validate_target(exploit, pos)
            assert result, f"Buffer overflow should be able to target {pos} (adjacent to player)"

        # Test that range 2 is out of range
        out_of_range = Position(12, 12)  # 2 diagonal steps away
        result = exploit_system._validate_target(exploit, out_of_range)
        assert not result, "Buffer overflow should NOT target positions at range 2"


class TestExploitRangeConsistency:
    """Test that all exploit ranges use grid distance."""

    def test_range_1_exploit_covers_8_tiles(self):
        """Test that range-1 exploits can target all 8 adjacent tiles."""
        center = Position(5, 5)

        # All positions at grid distance 1
        range_1_positions = [
            Position(4, 4),
            Position(5, 4),
            Position(6, 4),
            Position(4, 5),
            Position(6, 5),
            Position(4, 6),
            Position(5, 6),
            Position(6, 6),
        ]

        for pos in range_1_positions:
            distance = center.grid_distance_to(pos)
            assert distance == 1, f"{pos} should be at grid distance 1 from {center}"
            # Also verify this wouldn't work with Euclidean for diagonals
            if pos.x != center.x and pos.y != center.y:  # diagonal
                euclidean = center.distance_to(pos)
                assert euclidean > 1, f"Euclidean distance to diagonal {pos} should be > 1"

    def test_range_2_exploit_covers_expected_area(self):
        """Test that range-2 exploits cover a 5x5 grid."""
        center = Position(10, 10)

        # Count tiles at grid distance <= 2
        in_range = 0
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                pos = Position(center.x + dx, center.y + dy)
                if center.grid_distance_to(pos) <= 2:
                    in_range += 1

        # A 5x5 grid has 25 tiles
        assert in_range == 25, "Range-2 should cover a 5x5 grid (25 tiles)"

    def test_aoe_radius_uses_grid_distance(self):
        """Test that AoE effects use grid distance for consistency."""
        # This is more of a documentation test
        # AoE radius should use grid_distance_to, not distance_to

        center = Position(0, 0)
        diagonal = Position(1, 1)

        # With grid distance, diagonal is radius 1
        assert center.grid_distance_to(diagonal) == 1

        # With Euclidean, it would be ~1.414, which might miss the diagonal
        # if radius is exactly 1
        euclidean = center.distance_to(diagonal)
        assert euclidean > 1.4

        # This ensures AoE radius 1 includes diagonals when using grid distance
