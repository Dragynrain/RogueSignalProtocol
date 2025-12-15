"""
Unit tests for RestoreNode dataclass - Phase 0.4 Foundation.

Tests cover:
- RestoreNode initialization
- Capacity consumption via use() method
- Depleted state detection
- Unlimited capacity (-1) behavior
- Fair consumption (only consumes actual benefit)
"""

import pytest


class TestRestoreNodeBasics:
    """Test RestoreNode dataclass basic functionality."""

    def test_restore_node_exists(self):
        """RestoreNode dataclass should exist in game_map module."""
        from game_map import RestoreNode

        assert RestoreNode is not None

    def test_restore_node_initialization(self):
        """RestoreNode should initialize with correct defaults."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cooling")
        assert node.node_type == "cooling"
        assert node.total_capacity == -1  # Unlimited by default
        assert node.used_capacity == 0

    def test_restore_node_with_capacity(self):
        """RestoreNode should accept capacity parameter."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cpu", total_capacity=100)
        assert node.total_capacity == 100
        assert node.used_capacity == 0


class TestRestoreNodeUnlimited:
    """Test RestoreNode unlimited capacity behavior."""

    def test_unlimited_node_always_returns_full(self):
        """Unlimited nodes (-1) should always return full requested amount."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cooling", total_capacity=-1)

        # Should always return what's requested
        assert node.use(20) == 20
        assert node.use(50) == 50
        assert node.use(100) == 100

    def test_unlimited_node_never_depleted(self):
        """Unlimited nodes should never report as depleted."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="ghost", total_capacity=-1)
        node.use(1000)  # Use a lot

        assert not node.depleted
        assert node.unlimited


class TestRestoreNodeCapacity:
    """Test RestoreNode capacity consumption."""

    def test_use_consumes_capacity(self):
        """use() should consume capacity and return amount restored."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cooling", total_capacity=100)

        restored = node.use(20)
        assert restored == 20
        assert node.used_capacity == 20

    def test_use_returns_remaining_when_low(self):
        """use() should return only remaining capacity when nearly depleted."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cpu", total_capacity=50)
        node.used_capacity = 45  # Only 5 remaining

        restored = node.use(20)  # Request 20, only 5 available
        assert restored == 5
        assert node.used_capacity == 50  # Now fully used

    def test_depleted_returns_zero(self):
        """use() should return 0 when node is fully depleted."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="ghost", total_capacity=40)
        node.used_capacity = 40  # Fully depleted

        restored = node.use(20)
        assert restored == 0

    def test_depleted_property(self):
        """depleted property should be True when capacity exhausted."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cooling", total_capacity=60)
        assert not node.depleted

        node.used_capacity = 60
        assert node.depleted

    def test_unlimited_property(self):
        """unlimited property should be True only when total_capacity is -1."""
        from game_map import RestoreNode

        unlimited_node = RestoreNode(node_type="cpu", total_capacity=-1)
        limited_node = RestoreNode(node_type="cpu", total_capacity=100)

        assert unlimited_node.unlimited
        assert not limited_node.unlimited


class TestRestoreNodeFairConsumption:
    """Test fair consumption - only consume actual benefit provided."""

    def test_partial_use_fair_consumption(self):
        """Node should only consume capacity equal to actual restoration."""
        from game_map import RestoreNode

        # Scenario: Player at 15 heat, node offers 20 reduction
        # Should only consume 15 capacity (actual benefit)
        node = RestoreNode(node_type="cooling", total_capacity=100)

        # Simulate: player only needs 15 of the 20 offered
        actual_need = 15
        restored = node.use(actual_need)

        assert restored == 15
        assert node.used_capacity == 15  # Only 15 consumed

    def test_multiple_partial_uses(self):
        """Multiple partial uses should accumulate correctly."""
        from game_map import RestoreNode

        node = RestoreNode(node_type="cpu", total_capacity=100)

        node.use(15)  # First use
        assert node.used_capacity == 15

        node.use(20)  # Second use
        assert node.used_capacity == 35

        node.use(10)  # Third use
        assert node.used_capacity == 45


class TestGameMapNodeDicts:
    """Test that GameMap uses dict storage for nodes."""

    def test_cooling_nodes_is_dict(self):
        """GameMap.cooling_nodes should be a dict, not a set."""
        from game_map import GameMap

        gm = GameMap(50, 50)
        assert isinstance(gm.cooling_nodes, dict)

    def test_cpu_recovery_nodes_is_dict(self):
        """GameMap.cpu_recovery_nodes should be a dict, not a set."""
        from game_map import GameMap

        gm = GameMap(50, 50)
        assert isinstance(gm.cpu_recovery_nodes, dict)

    def test_ghost_nodes_is_dict(self):
        """GameMap.ghost_nodes should be a dict, not a set."""
        from game_map import GameMap

        gm = GameMap(50, 50)
        assert isinstance(gm.ghost_nodes, dict)

    def test_node_dict_membership_check(self):
        """Node dict should support membership check like sets."""
        from game_map import GameMap, RestoreNode

        gm = GameMap(50, 50)
        pos = (10, 15)

        # Before adding
        assert pos not in gm.cooling_nodes

        # After adding
        gm.cooling_nodes[pos] = RestoreNode(node_type="cooling")
        assert pos in gm.cooling_nodes

    def test_node_dict_iteration(self):
        """Node dict should iterate over positions like sets."""
        from game_map import GameMap, RestoreNode

        gm = GameMap(50, 50)
        positions = [(5, 5), (10, 10), (15, 15)]

        for pos in positions:
            gm.cpu_recovery_nodes[pos] = RestoreNode(node_type="cpu")

        # Iteration should give positions
        iterated = list(gm.cpu_recovery_nodes)
        assert len(iterated) == 3
        for pos in positions:
            assert pos in iterated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
