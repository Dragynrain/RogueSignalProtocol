#!/usr/bin/env python3
"""
Unit tests for fixed level layout definitions.

Tests FixedLevelData dataclass and prologue layout.
"""

import pytest

from rsp.level.fixed_levels import (
    PROLOGUE_LAYOUT_RAW,
    FixedLevelData,
    get_prologue_layout,
)


class TestFixedLevelData:
    """Test FixedLevelData dataclass."""

    def test_fixed_level_data_creation(self):
        """FixedLevelData can be created with layout."""
        layout = ["###", "#.#", "###"]
        data = FixedLevelData(layout=layout, name="Test Level")

        assert data.layout == layout
        assert data.name == "Test Level"

    def test_width_property(self):
        """Width returns length of first row."""
        layout = ["#####", "#...#", "#####"]
        data = FixedLevelData(layout=layout)

        assert data.width == 5

    def test_height_property(self):
        """Height returns number of rows."""
        layout = ["###", "#.#", "#.#", "###"]
        data = FixedLevelData(layout=layout)

        assert data.height == 4

    def test_empty_layout_dimensions(self):
        """Empty layout returns 0 for dimensions."""
        data = FixedLevelData(layout=[])

        assert data.width == 0
        assert data.height == 0

    def test_get_char_valid_position(self):
        """get_char returns character at valid position."""
        layout = ["###", "#@#", "###"]
        data = FixedLevelData(layout=layout)

        assert data.get_char(1, 1) == "@"
        assert data.get_char(0, 0) == "#"
        assert data.get_char(2, 2) == "#"

    def test_get_char_out_of_bounds_returns_wall(self):
        """get_char returns '#' for out of bounds positions."""
        layout = ["###", "#.#", "###"]
        data = FixedLevelData(layout=layout)

        # Negative coordinates
        assert data.get_char(-1, 0) == "#"
        assert data.get_char(0, -1) == "#"

        # Beyond bounds
        assert data.get_char(10, 0) == "#"
        assert data.get_char(0, 10) == "#"

    def test_default_values(self):
        """FixedLevelData has sensible defaults."""
        data = FixedLevelData(layout=["###"])

        assert data.name == "Fixed Level"
        assert data.tutorial_triggers == {}
        assert data.enemy_overrides == {}


class TestPrologueLayout:
    """Test the prologue level layout."""

    def test_prologue_layout_raw_not_empty(self):
        """PROLOGUE_LAYOUT_RAW should contain level data."""
        assert len(PROLOGUE_LAYOUT_RAW) > 0

    def test_get_prologue_layout_returns_data(self):
        """get_prologue_layout returns FixedLevelData instance."""
        layout = get_prologue_layout()

        assert isinstance(layout, FixedLevelData)
        assert layout.name == "First Infiltration"

    def test_prologue_has_player_spawn(self):
        """Prologue layout contains player spawn (@)."""
        layout = get_prologue_layout()

        has_spawn = False
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) == "@":
                    has_spawn = True
                    break
            if has_spawn:
                break

        assert has_spawn, "Prologue must have player spawn (@)"

    def test_prologue_has_gateway(self):
        """Prologue layout contains gateway exit (>)."""
        layout = get_prologue_layout()

        has_gateway = False
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) == ">":
                    has_gateway = True
                    break
            if has_gateway:
                break

        assert has_gateway, "Prologue must have gateway exit (>)"

    def test_prologue_has_enemies(self):
        """Prologue layout contains enemy spawns."""
        layout = get_prologue_layout()

        enemy_chars = {"X", "S", "P"}
        enemy_count = 0
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) in enemy_chars:
                    enemy_count += 1

        assert enemy_count > 0, "Prologue must have enemies"

    def test_prologue_has_blind_spots(self):
        """Prologue layout contains blind spots (s)."""
        layout = get_prologue_layout()

        blind_spot_count = 0
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) == "s":
                    blind_spot_count += 1

        assert blind_spot_count > 0, "Prologue must have blind spots for teaching"

    def test_prologue_has_nodes(self):
        """Prologue layout contains resource nodes."""
        layout = get_prologue_layout()

        node_chars = {"c", "r", "g"}
        node_count = 0
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) in node_chars:
                    node_count += 1

        assert node_count > 0, "Prologue must have resource nodes"

    def test_prologue_has_exploit_pickup(self):
        """Prologue layout contains exploit pickups."""
        layout = get_prologue_layout()

        exploit_chars = {"e", "E"}
        exploit_count = 0
        for y in range(layout.height):
            for x in range(layout.width):
                if layout.get_char(x, y) in exploit_chars:
                    exploit_count += 1

        assert exploit_count > 0, "Prologue must have exploit pickups for teaching"

    def test_prologue_dimensions(self):
        """Prologue layout has expected dimensions (28x25)."""
        layout = get_prologue_layout()

        assert layout.width == 28, f"Expected width 28, got {layout.width}"
        assert layout.height == 25, f"Expected height 25, got {layout.height}"

    def test_prologue_spawn_position(self):
        """Player spawn is at expected position (1,1)."""
        layout = get_prologue_layout()

        # According to the layout, @ is at position (1, 1)
        assert layout.get_char(1, 1) == "@", "Player spawn should be at (1,1)"

    def test_prologue_walls_surround_map(self):
        """Map is surrounded by walls."""
        layout = get_prologue_layout()

        # Check top and bottom rows
        for x in range(layout.width):
            assert layout.get_char(x, 0) == "#", f"Top wall missing at x={x}"
            assert layout.get_char(x, layout.height - 1) == "#", f"Bottom wall missing at x={x}"

        # Check left and right columns
        for y in range(layout.height):
            assert layout.get_char(0, y) == "#", f"Left wall missing at y={y}"
            assert layout.get_char(layout.width - 1, y) == "#", f"Right wall missing at y={y}"


class TestLayoutCharacterCounts:
    """Test specific character counts in prologue layout."""

    def setup_method(self):
        """Get prologue layout for counting."""
        self.layout = get_prologue_layout()

    def _count_char(self, char):
        """Count occurrences of character in layout."""
        count = 0
        for y in range(self.layout.height):
            for x in range(self.layout.width):
                if self.layout.get_char(x, y) == char:
                    count += 1
        return count

    def test_exactly_one_player_spawn(self):
        """Layout has exactly one player spawn."""
        assert self._count_char("@") == 1

    def test_exactly_one_gateway(self):
        """Layout has exactly one gateway."""
        assert self._count_char(">") == 1

    def test_damaged_scanner_count(self):
        """Layout has Damaged Scanners (X) for melee teaching."""
        count = self._count_char("X")
        assert count >= 1, "Need at least one Damaged Scanner for melee teaching"

    def test_patrol_count(self):
        """Layout has Patrols (P) for movement teaching."""
        count = self._count_char("P")
        assert count >= 3, "Need multiple Patrols for different sections"

    def test_cooling_node_exists(self):
        """Layout has at least one cooling node."""
        assert self._count_char("c") >= 1

    def test_cpu_node_exists(self):
        """Layout has at least one CPU recovery node."""
        assert self._count_char("r") >= 1

    def test_ghost_node_exists(self):
        """Layout has at least one ghost node."""
        assert self._count_char("g") >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
