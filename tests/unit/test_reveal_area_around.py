"""
Tests for GameMap.reveal_area_around helper method.

This helper consolidates the 3x3 reveal pattern used in threat_scan and network_scan.
"""

from game_entities import Position
from game_map import GameMap


class TestRevealAreaAround:
    """Tests for the reveal_area_around helper method."""

    def test_reveal_area_around_position_object(self):
        """Should reveal 3x3 area when given a Position object."""
        game_map = GameMap(80, 50)
        center = Position(10, 10)

        game_map.reveal_area_around(center, radius=1)

        # Check all 9 tiles in 3x3 area are revealed
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                assert (10 + dx, 10 + dy) in game_map.explored_tiles

    def test_reveal_area_around_tuple(self):
        """Should reveal 3x3 area when given a tuple."""
        game_map = GameMap(80, 50)
        center = (15, 20)

        game_map.reveal_area_around(center, radius=1)

        # Check all 9 tiles in 3x3 area are revealed
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                assert (15 + dx, 20 + dy) in game_map.explored_tiles

    def test_reveal_area_around_larger_radius(self):
        """Should reveal 5x5 area with radius=2."""
        game_map = GameMap(80, 50)
        center = Position(20, 20)

        game_map.reveal_area_around(center, radius=2)

        # Check all 25 tiles in 5x5 area are revealed
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                assert (20 + dx, 20 + dy) in game_map.explored_tiles

    def test_reveal_area_around_clamps_to_bounds(self):
        """Should only reveal tiles within map bounds."""
        game_map = GameMap(80, 50)
        # Place center at corner
        center = Position(0, 0)

        game_map.reveal_area_around(center, radius=1)

        # Only tiles within bounds should be revealed
        # (0,0), (1,0), (0,1), (1,1) should be revealed
        # (-1,-1), (-1,0), etc. should NOT be in explored tiles
        assert (0, 0) in game_map.explored_tiles
        assert (1, 0) in game_map.explored_tiles
        assert (0, 1) in game_map.explored_tiles
        assert (1, 1) in game_map.explored_tiles
        # Out of bounds tiles should not cause issues
        assert (-1, -1) not in game_map.explored_tiles

    def test_reveal_area_around_accumulates(self):
        """Revealing multiple areas should accumulate explored tiles."""
        game_map = GameMap(80, 50)

        game_map.reveal_area_around(Position(10, 10), radius=1)
        game_map.reveal_area_around(Position(20, 20), radius=1)

        # Both areas should be revealed
        assert (10, 10) in game_map.explored_tiles
        assert (20, 20) in game_map.explored_tiles
        # Total should be 18 tiles (2 non-overlapping 3x3 areas)
        assert len(game_map.explored_tiles) == 18

    def test_reveal_area_around_overlapping_areas(self):
        """Overlapping reveals should not duplicate tiles."""
        game_map = GameMap(80, 50)

        game_map.reveal_area_around(Position(10, 10), radius=1)
        game_map.reveal_area_around(Position(11, 10), radius=1)  # Adjacent, overlapping

        # Overlapping tiles should only appear once in set
        assert (10, 10) in game_map.explored_tiles
        assert (11, 10) in game_map.explored_tiles
        # 3x3 at (10,10): x in [9,10,11], y in [9,10,11] = 9 tiles
        # 3x3 at (11,10): x in [10,11,12], y in [9,10,11] = 9 tiles
        # Overlap: x in [10,11], y in [9,10,11] = 6 tiles
        # Total unique: 9 + 9 - 6 = 12 tiles
        assert len(game_map.explored_tiles) == 12

    def test_reveal_area_around_edge_of_map(self):
        """Should handle reveals at edge of map correctly."""
        game_map = GameMap(80, 50)
        # Place at right edge
        center = Position(79, 25)

        game_map.reveal_area_around(center, radius=1)

        # Should reveal partial area (6 tiles: 2 columns x 3 rows)
        assert (79, 24) in game_map.explored_tiles
        assert (79, 25) in game_map.explored_tiles
        assert (79, 26) in game_map.explored_tiles
        assert (78, 24) in game_map.explored_tiles
        assert (78, 25) in game_map.explored_tiles
        assert (78, 26) in game_map.explored_tiles
        # x=80 is out of bounds
        assert (80, 25) not in game_map.explored_tiles
