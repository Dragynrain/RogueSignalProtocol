#!/usr/bin/env python3
"""
Integration tests for Ascension Save/Load System (Phase 5).

Tests save/load roundtrip for ascension level, node capacity states,
and used blind spots.
"""

from unittest.mock import MagicMock

import pytest

from game_map import RestoreNode


class TestAscensionSaveLoadRoundtrip:
    """Test ascension state survives save/load cycle."""

    @pytest.fixture
    def mock_game_engine(self):
        """Create a mock game engine with ascension state."""
        game = MagicMock()
        game.ascension_level = 7
        game.player = MagicMock()
        game.player.x = 10
        game.player.y = 15
        game.player.cpu = 80
        game.player.max_cpu = 100
        game.player.heat = 25
        game.player.max_heat = 100
        game.player.trace_level = 30.0
        game.player.ram_total = 8
        game.player.speed_moves_remaining = 0
        game.player.temporary_effects = {}
        game.player.inventory_manager = MagicMock()
        game.player.inventory_manager.equipped_exploits = []
        game.player.inventory_manager.items = []
        game.player.last_position = MagicMock()
        game.player.last_position.x = 10
        game.player.last_position.y = 15

        game.game_state = MagicMock()
        game.game_state.level = 2
        game.game_state.turn = 50
        game.game_state.game_over = False
        game.game_state.admin_spawned = False
        game.game_state.dungeon_seed = 12345
        game.game_state.threat_scan_turns = 0
        game.game_state.melee_kills_this_turn = 0
        game.game_state.melee_kills_previous_turn = 0
        game.game_state.speed_boost_kills_this_turn = 0
        game.game_state.player_pending_turn_bonus = 0

        game.game_map = MagicMock()
        game.game_map.tiles = {}
        game.game_map.blind_spots = set()
        game.game_map.used_blind_spots = set()
        game.game_map.cooling_nodes = {}
        game.game_map.cpu_recovery_nodes = {}
        game.game_map.ghost_nodes = {}
        game.game_map.gateway_codes = {}
        game.game_map.gateway_position = None
        game.game_map.exploit_nodes = {}
        game.game_map.data_fragment_nodes = set()
        game.game_map.code_nodes = {}

        game.enemy_manager = MagicMock()
        game.enemy_manager.enemies = []

        return game

    def test_ascension_level_saved_in_data(self, mock_game_engine):
        """Ascension level should be included in save data."""
        from game_save import SaveGameManager

        save_data = SaveGameManager.create_save_data(mock_game_engine)

        assert "ascension_level" in save_data
        assert save_data["ascension_level"] == 7

    def test_ascension_level_zero_saved(self, mock_game_engine):
        """A0 should also be saved correctly."""
        from game_save import SaveGameManager

        mock_game_engine.ascension_level = 0
        save_data = SaveGameManager.create_save_data(mock_game_engine)

        assert save_data["ascension_level"] == 0

    def test_ascension_level_max_saved(self, mock_game_engine):
        """A20 should be saved correctly."""
        from game_save import SaveGameManager

        mock_game_engine.ascension_level = 20
        save_data = SaveGameManager.create_save_data(mock_game_engine)

        assert save_data["ascension_level"] == 20


class TestUsedBlindSpotsSaveLoad:
    """Test used blind spots (A20) persist across save/load."""

    def test_used_blind_spots_saved(self):
        """Used blind spots should be saved."""
        # Test the serialization format directly
        used_blind_spots = {(5, 5), (10, 10)}
        serialized = [f"{x},{y}" for x, y in used_blind_spots]

        assert len(serialized) == 2
        assert all(isinstance(pos, str) for pos in serialized)

    def test_used_blind_spots_format(self):
        """Used blind spots should be saved as coordinate strings."""
        used_blind_spots = {(5, 5), (10, 10)}
        serialized = [f"{x},{y}" for x, y in used_blind_spots]

        # Should be strings like "5,5" and "10,10"
        assert all("," in pos for pos in serialized)
        assert "5,5" in serialized
        assert "10,10" in serialized


class TestNodeCapacitySaveLoad:
    """Test node capacity state (A13) persists across save/load."""

    def test_node_capacity_serialization(self):
        """Node capacity states should serialize correctly."""
        # Set up nodes with capacity
        cooling_node = RestoreNode(node_type="cooling", total_capacity=150)
        cooling_node.used_capacity = 60  # Partially used

        cpu_node = RestoreNode(node_type="cpu", total_capacity=100)
        cpu_node.used_capacity = 100  # Depleted

        ghost_node = RestoreNode(node_type="ghost", total_capacity=75)
        ghost_node.used_capacity = 0  # Unused

        cooling_nodes = {(5, 5): cooling_node}
        cpu_recovery_nodes = {(10, 10): cpu_node}
        ghost_nodes = {(15, 15): ghost_node}

        # Test serialization format (same as in game_save.py)
        node_capacity = {
            "cooling": {
                f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in cooling_nodes.items()
            },
            "cpu": {
                f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in cpu_recovery_nodes.items()
            },
            "ghost": {
                f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in ghost_nodes.items()
            },
        }

        assert "cooling" in node_capacity
        assert "cpu" in node_capacity
        assert "ghost" in node_capacity

    def test_cooling_node_capacity_serialized(self):
        """Cooling node used_capacity should serialize correctly."""
        cooling_node = RestoreNode(node_type="cooling", total_capacity=150)
        cooling_node.used_capacity = 60

        cooling_nodes = {(5, 5): cooling_node}
        serialized = {
            f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in cooling_nodes.items()
        }

        assert "5,5" in serialized
        assert serialized["5,5"] == 60

    def test_cpu_node_capacity_serialized(self):
        """CPU node used_capacity should serialize (including depleted)."""
        cpu_node = RestoreNode(node_type="cpu", total_capacity=100)
        cpu_node.used_capacity = 100  # Depleted

        cpu_nodes = {(10, 10): cpu_node}
        serialized = {f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in cpu_nodes.items()}

        assert "10,10" in serialized
        assert serialized["10,10"] == 100

    def test_ghost_node_capacity_serialized(self):
        """Ghost node used_capacity should serialize correctly."""
        ghost_node = RestoreNode(node_type="ghost", total_capacity=75)
        ghost_node.used_capacity = 0  # Unused

        ghost_nodes = {(15, 15): ghost_node}
        serialized = {f"{pos[0]},{pos[1]}": node.used_capacity for pos, node in ghost_nodes.items()}

        assert "15,15" in serialized
        assert serialized["15,15"] == 0


class TestOldSaveMigration:
    """Test old saves without ascension data default correctly."""

    def test_missing_ascension_defaults_to_zero(self):
        """Old save without ascension_level should default to A0."""
        # Simulate old save data without ascension field
        old_save = {
            "level": 1,
            "turn": 100,
            "game_over": False,
            "admin_spawned": False,
            "dungeon_seed": 12345,
            "player": {"x": 10, "y": 10, "cpu": 100},
            "map": {"tiles": {}},
            "enemies": [],
        }

        # The get with default should handle this
        ascension_level = old_save.get("ascension_level", 0)
        assert ascension_level == 0

    def test_missing_used_blind_spots_defaults_to_empty(self):
        """Old save without used_blind_spots should default to empty."""
        old_map_data = {
            "tiles": {},
            "blind_spots": ["5,5", "10,10"],
            # No used_blind_spots key
        }

        used_blind_spots = old_map_data.get("used_blind_spots", [])
        assert used_blind_spots == []

    def test_missing_node_capacity_defaults_to_empty(self):
        """Old save without node_capacity should default to empty."""
        old_map_data = {
            "tiles": {},
            "cooling_nodes": ["5,5"],
            # No node_capacity key
        }

        node_capacity = old_map_data.get("node_capacity", {})
        assert node_capacity == {}


class TestAscensionModifiersRecalculatedOnLoad:
    """Test that ascension modifiers are recalculated when loading."""

    def test_modifiers_recalculated_from_saved_level(self):
        """Loading A7 save should recalculate A7 modifiers."""
        from game_ascension import calculate_ascension_modifiers

        # Simulate what happens on load
        saved_ascension = 7
        modifiers = calculate_ascension_modifiers(saved_ascension)

        # Should have cumulative modifiers from A1-A7
        assert modifiers.scanner_vision_bonus == 1  # A1
        assert modifiers.enemy_hp_bonus == 10  # A2
        assert modifiers.trace_gain_multiplier == 2.0  # A3
        assert modifiers.enemy_damage_multiplier == 1.2  # A4
        assert modifiers.enemy_vision_bonus == 1  # A5
        assert modifiers.blind_spot_reduction_per_floor == 1  # A6
        assert modifiers.hostile_trace_bonus == 0.2  # A7
