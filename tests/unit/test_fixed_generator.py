#!/usr/bin/env python3
"""
Unit tests for fixed level generator.

Tests FixedLevelGenerator class that creates levels from ASCII layouts.
"""

from unittest.mock import Mock

import pytest

from rsp.core.config import GameConfig
from rsp.entities.base import Position
from rsp.level.fixed_generator import FixedLevelGenerator
from rsp.level.fixed_levels import FixedLevelData, get_prologue_layout
from rsp.level.map import GameMap


class TestFixedLevelGeneratorConstants:
    """Test FixedLevelGenerator class constants."""

    def test_floor_chars_defined(self):
        """FLOOR_CHARS contains walkable tile characters."""
        assert "." in FixedLevelGenerator.FLOOR_CHARS
        assert "@" in FixedLevelGenerator.FLOOR_CHARS
        assert ">" in FixedLevelGenerator.FLOOR_CHARS
        assert "s" in FixedLevelGenerator.FLOOR_CHARS

    def test_enemy_chars_defined(self):
        """ENEMY_CHARS maps characters to enemy types."""
        assert "X" in FixedLevelGenerator.ENEMY_CHARS
        assert "S" in FixedLevelGenerator.ENEMY_CHARS
        assert "P" in FixedLevelGenerator.ENEMY_CHARS

        # X and S are both scanners
        assert FixedLevelGenerator.ENEMY_CHARS["X"] == "scanner"
        assert FixedLevelGenerator.ENEMY_CHARS["S"] == "scanner"
        assert FixedLevelGenerator.ENEMY_CHARS["P"] == "patrol"

    def test_node_chars_defined(self):
        """NODE_CHARS maps characters to node types."""
        assert FixedLevelGenerator.NODE_CHARS["c"] == "cooling"
        assert FixedLevelGenerator.NODE_CHARS["r"] == "cpu"
        assert FixedLevelGenerator.NODE_CHARS["g"] == "ghost"

    def test_item_chars_defined(self):
        """ITEM_CHARS maps characters to item types."""
        assert FixedLevelGenerator.ITEM_CHARS["e"] == "exploit"
        assert FixedLevelGenerator.ITEM_CHARS["E"] == "threat_scan"
        assert FixedLevelGenerator.ITEM_CHARS["d"] == "code_hack"

    def test_damaged_scanner_hp_override(self):
        """Damaged Scanner (X) should have HP override of 5."""
        assert FixedLevelGenerator.ENEMY_HP_OVERRIDES["X"] == 5


class TestFixedLevelGeneratorInitialization:
    """Test FixedLevelGenerator initialization."""

    def test_initialization_with_game_map(self):
        """Generator initializes with game map."""
        game_map = GameMap(80, 50)
        generator = FixedLevelGenerator(game_map)

        assert generator.game_map is game_map
        assert generator.game_engine is None

    def test_initialization_with_game_engine(self):
        """Generator can accept game engine for code hack effects."""
        game_map = GameMap(80, 50)
        game_engine = Mock()
        generator = FixedLevelGenerator(game_map, game_engine)

        assert generator.game_engine is game_engine


class TestGenerateFromLayout:
    """Test generate_from_layout method."""

    def setup_method(self):
        """Create test fixtures."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.generator = FixedLevelGenerator(self.game_map)

    def test_simple_layout_generation(self):
        """Simple layout generates correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@.>#",
                "#####",
            ]
        )

        spawn_pos, enemies = self.generator.generate_from_layout(layout)

        assert spawn_pos == Position(1, 1)
        assert self.game_map.gateway == Position(3, 1)
        assert len(enemies) == 0

    def test_walls_are_generated(self):
        """Walls are placed correctly from # characters."""
        layout = FixedLevelData(
            layout=[
                "###",
                "#@#",
                "###",
            ]
        )

        self.generator.generate_from_layout(layout)

        # All border positions should be walls
        assert (0, 0) in self.game_map.walls
        assert (1, 0) in self.game_map.walls
        assert (2, 0) in self.game_map.walls
        assert (0, 1) in self.game_map.walls
        assert (2, 1) in self.game_map.walls
        assert (0, 2) in self.game_map.walls
        assert (1, 2) in self.game_map.walls
        assert (2, 2) in self.game_map.walls

        # Center should not be a wall
        assert (1, 1) not in self.game_map.walls

    def test_blind_spots_are_generated(self):
        """Blind spots (s) are placed correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@ss#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout)

        assert (2, 1) in self.game_map.blind_spots
        assert (3, 1) in self.game_map.blind_spots
        # Blind spots should also be walkable (not walls)
        assert (2, 1) not in self.game_map.walls
        assert (3, 1) not in self.game_map.walls

    def test_enemy_creation(self):
        """Enemies are created from layout characters."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@.P#",
                "#####",
            ]
        )

        spawn_pos, enemies = self.generator.generate_from_layout(layout)

        assert len(enemies) == 1
        assert enemies[0].type == "patrol"
        assert enemies[0].position == Position(3, 1)

    def test_damaged_scanner_has_reduced_hp(self):
        """Damaged Scanner (X) has 5 HP instead of normal."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@.X#",
                "#####",
            ]
        )

        spawn_pos, enemies = self.generator.generate_from_layout(layout)

        assert len(enemies) == 1
        assert enemies[0].type == "scanner"
        assert enemies[0].cpu == 5
        assert enemies[0].max_cpu == 5

    def test_normal_scanner_has_normal_hp(self):
        """Normal Scanner (S) has normal HP."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@.S#",
                "#####",
            ]
        )

        spawn_pos, enemies = self.generator.generate_from_layout(layout)

        assert len(enemies) == 1
        assert enemies[0].type == "scanner"
        # Should have default HP (not 5)
        assert enemies[0].cpu != 5

    def test_cooling_node_placement(self):
        """Cooling nodes (c) are placed correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@c>#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout)

        assert (2, 1) in self.game_map.cooling_nodes

    def test_cpu_node_placement(self):
        """CPU recovery nodes (r) are placed correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@r>#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout)

        assert (2, 1) in self.game_map.cpu_recovery_nodes

    def test_ghost_node_placement(self):
        """Ghost nodes (g) are placed correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@g>#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout)

        assert (2, 1) in self.game_map.ghost_nodes

    def test_exploit_pickup_placement_level_0(self):
        """Exploit pickups at level 0 are Code Injection."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@e>#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout, level=0)

        assert (2, 1) in self.game_map.exploit_pickups
        exploit = self.game_map.exploit_pickups[(2, 1)]
        # Check that it's Code Injection (name may be key or display name)
        assert "code_injection" in exploit.name.lower() or "injection" in exploit.name.lower()

    def test_threat_scan_pickup_placement(self):
        """Threat Scan pickups (E) are placed correctly."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#@E>#",
                "#####",
            ]
        )

        self.generator.generate_from_layout(layout, level=0)

        assert (2, 1) in self.game_map.exploit_pickups
        exploit = self.game_map.exploit_pickups[(2, 1)]
        # Check that it's Threat Scan (name may be key or display name)
        assert "threat_scan" in exploit.name.lower() or "threat" in exploit.name.lower()

    def test_code_hack_placement_with_engine(self):
        """Code hacks (d) are placed when game_engine available."""
        game_engine = Mock()
        game_engine.code_hack_effects = {
            "red": ("damage_boost", "Boosts damage"),
        }
        generator = FixedLevelGenerator(self.game_map, game_engine)

        layout = FixedLevelData(
            layout=[
                "#####",
                "#@d>#",
                "#####",
            ]
        )

        generator.generate_from_layout(layout, level=0)

        assert (2, 1) in self.game_map.code_hacks

    def test_missing_spawn_uses_fallback(self):
        """Missing player spawn uses (1,1) as fallback."""
        layout = FixedLevelData(
            layout=[
                "#####",
                "#..>#",
                "#####",
            ]
        )

        spawn_pos, enemies = self.generator.generate_from_layout(layout)

        assert spawn_pos == Position(1, 1)

    def test_map_data_cleared_before_generation(self):
        """Existing map data is cleared before generating."""
        # Add some data that should be cleared
        self.game_map.blind_spots.add((1, 1))
        self.game_map.cooling_nodes[(5, 5)] = Mock()

        layout = FixedLevelData(
            layout=[
                "###",
                "#@#",
                "###",
            ]
        )

        self.generator.generate_from_layout(layout)

        # Old blind spot should be gone (layout doesn't have 's' at 1,1)
        assert (1, 1) not in self.game_map.blind_spots
        # Old cooling node should be gone (layout doesn't have 'c')
        assert (5, 5) not in self.game_map.cooling_nodes

    def test_rest_of_map_filled_with_walls(self):
        """Areas outside layout are filled with walls."""
        layout = FixedLevelData(
            layout=[
                "###",
                "#@#",
                "###",
            ]
        )

        self.generator.generate_from_layout(layout)

        # Positions outside the 3x3 layout should be walls
        # The generator fills entire map with walls first, then carves layout
        assert (10, 10) in self.game_map.walls
        assert (20, 20) in self.game_map.walls


class TestPrologueLayoutGeneration:
    """Test generation using actual prologue layout."""

    def setup_method(self):
        """Create test fixtures."""
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.game_engine = Mock()
        self.game_engine.code_hack_effects = {
            "red": ("damage_boost", "Test"),
            "blue": ("speed_boost", "Test"),
        }
        self.generator = FixedLevelGenerator(self.game_map, self.game_engine)
        self.prologue_layout = get_prologue_layout()

    def test_prologue_generates_without_error(self):
        """Prologue layout generates successfully."""
        spawn_pos, enemies = self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert spawn_pos is not None
        assert isinstance(spawn_pos, Position)

    def test_prologue_spawn_position(self):
        """Prologue spawn is at (1, 1)."""
        spawn_pos, enemies = self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert spawn_pos == Position(1, 1)

    def test_prologue_has_gateway(self):
        """Prologue has gateway placed."""
        self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert self.game_map.gateway is not None

    def test_prologue_has_enemies(self):
        """Prologue generates enemies."""
        spawn_pos, enemies = self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert len(enemies) > 0

    def test_prologue_has_blind_spots(self):
        """Prologue generates blind spots."""
        self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert len(self.game_map.blind_spots) > 0

    def test_prologue_has_resource_nodes(self):
        """Prologue generates resource nodes."""
        self.generator.generate_from_layout(self.prologue_layout, level=0)

        total_nodes = (
            len(self.game_map.cooling_nodes)
            + len(self.game_map.cpu_recovery_nodes)
            + len(self.game_map.ghost_nodes)
        )
        assert total_nodes > 0

    def test_prologue_has_exploit_pickups(self):
        """Prologue generates exploit pickups."""
        self.generator.generate_from_layout(self.prologue_layout, level=0)

        assert len(self.game_map.exploit_pickups) > 0

    def test_prologue_damaged_scanner_has_5hp(self):
        """Damaged Scanner in prologue has 5 HP."""
        spawn_pos, enemies = self.generator.generate_from_layout(self.prologue_layout, level=0)

        # Find the damaged scanner (X is at position near spawn)
        damaged_scanner = None
        for enemy in enemies:
            if enemy.cpu == 5 and enemy.type == "scanner":
                damaged_scanner = enemy
                break

        assert damaged_scanner is not None, "Prologue should have a Damaged Scanner with 5 HP"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
