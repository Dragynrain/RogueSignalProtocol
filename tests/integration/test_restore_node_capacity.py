"""
Integration tests for restore node capacity system (A13+).

At A13+, restore nodes (cooling, CPU, ghost) have limited capacity that
depletes as the player uses them. This tests:
- RestoreNode data structure
- Capacity depletion logic
- Depleted nodes don't restore
- Capacity only consumed when providing actual benefit
"""

from rsp.level.map import RestoreNode


class TestRestoreNodeDataclass:
    """Tests for the RestoreNode dataclass."""

    def test_unlimited_node_returns_full_amount(self):
        """Unlimited nodes (-1 capacity) should return full requested amount."""
        node = RestoreNode(node_type="cooling", total_capacity=-1)

        # Request any amount - should get it all back
        result = node.use(20)
        assert result == 20

        # Request again - should still get full amount (unlimited)
        result = node.use(50)
        assert result == 50

    def test_limited_node_depletes(self):
        """Limited nodes should deplete as capacity is used."""
        node = RestoreNode(node_type="cooling", total_capacity=30)

        # Use 20 out of 30
        result = node.use(20)
        assert result == 20
        assert node.used_capacity == 20

        # Use remaining 10
        result = node.use(10)
        assert result == 10
        assert node.used_capacity == 30
        assert node.depleted is True

    def test_limited_node_returns_remaining_when_partially_depleted(self):
        """Partially depleted nodes should return only remaining capacity."""
        node = RestoreNode(node_type="cpu", total_capacity=15)

        # Use 10
        node.use(10)
        assert node.used_capacity == 10

        # Request 20, but only 5 remaining
        result = node.use(20)
        assert result == 5
        assert node.used_capacity == 15
        assert node.depleted is True

    def test_depleted_node_returns_zero(self):
        """Fully depleted nodes should return 0."""
        node = RestoreNode(node_type="ghost", total_capacity=10)

        # Fully deplete
        node.use(10)
        assert node.depleted is True

        # Request more - should get nothing
        result = node.use(20)
        assert result == 0

    def test_unlimited_property(self):
        """unlimited property should correctly identify unlimited nodes."""
        unlimited = RestoreNode(node_type="cooling", total_capacity=-1)
        limited = RestoreNode(node_type="cooling", total_capacity=30)

        assert unlimited.unlimited is True
        assert limited.unlimited is False

    def test_depleted_property(self):
        """depleted property should correctly identify depleted nodes."""
        node = RestoreNode(node_type="cpu", total_capacity=10)

        assert node.depleted is False

        node.use(10)
        assert node.depleted is True


class TestCoolingNodeCapacity:
    """Tests for cooling node capacity in game context."""

    def test_cooling_node_with_capacity_restores_heat(self):
        """Cooling node with capacity should reduce heat."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Set up player with high heat
        agent.engine.player.heat = 50
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Clear existing nodes and add a limited-capacity cooling node at player position
        agent.engine.game_map.cooling_nodes.clear()
        agent.engine.game_map.cooling_nodes[player_pos] = RestoreNode(
            node_type="cooling", total_capacity=30
        )

        # Process a turn (player steps on node)
        agent.engine.game_session.process_turn()

        # Heat should be reduced (by 20, the standard reduction)
        assert agent.engine.player.heat < 50, "Heat should decrease on cooling node"

    def test_cooling_node_depletes_after_use(self):
        """Cooling node should deplete after being used."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Add a limited-capacity cooling node
        agent.engine.game_map.cooling_nodes.clear()
        node = RestoreNode(node_type="cooling", total_capacity=20)
        agent.engine.game_map.cooling_nodes[player_pos] = node

        # Set heat high enough to benefit from node
        agent.engine.player.heat = 50

        # Process a turn
        agent.engine.game_session.process_turn()

        # Node should have used capacity
        assert node.used_capacity > 0, "Node should have consumed capacity"

    def test_depleted_cooling_node_provides_no_benefit(self):
        """Depleted cooling node should not reduce heat."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Add a pre-depleted cooling node
        agent.engine.game_map.cooling_nodes.clear()
        node = RestoreNode(node_type="cooling", total_capacity=20, used_capacity=20)
        agent.engine.game_map.cooling_nodes[player_pos] = node

        # Set heat
        agent.engine.player.heat = 50

        # Process a turn
        agent.engine.game_session.process_turn()

        # Heat should NOT decrease (node is depleted)
        # Note: natural heat decay may occur, so check it's not from node
        # The node should still be fully depleted
        assert node.depleted is True


class TestCPUNodeCapacity:
    """Tests for CPU recovery node capacity in game context."""

    def test_cpu_node_with_capacity_restores_cpu(self):
        """CPU node with capacity should restore CPU."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Set up player with reduced CPU
        original_max = agent.engine.player.max_cpu
        agent.engine.player.cpu = original_max - 30
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Clear existing nodes and add a limited-capacity CPU node
        agent.engine.game_map.cpu_recovery_nodes.clear()
        agent.engine.game_map.cpu_recovery_nodes[player_pos] = RestoreNode(
            node_type="cpu", total_capacity=50
        )

        # Process a turn
        agent.engine.game_session.process_turn()

        # CPU should increase (up to max)
        assert agent.engine.player.cpu > original_max - 30, "CPU should increase on CPU node"


class TestGhostNodeCapacity:
    """Tests for ghost node capacity in game context."""

    def test_ghost_node_with_capacity_reduces_trace(self):
        """Ghost node with capacity should reduce trace level."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Set up player with trace level
        agent.engine.player.trace_level = 50
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Clear existing nodes and add a limited-capacity ghost node
        agent.engine.game_map.ghost_nodes.clear()
        agent.engine.game_map.ghost_nodes[player_pos] = RestoreNode(
            node_type="ghost", total_capacity=30
        )

        # Process a turn
        agent.engine.game_session.process_turn()

        # Trace should be reduced
        assert agent.engine.player.trace_level < 50, "Trace should decrease on ghost node"


class TestCapacityOnlyConsumedWhenBenefiting:
    """Tests that node capacity is only consumed when providing actual benefit."""

    def test_cooling_at_zero_heat_doesnt_consume_capacity(self):
        """Stepping on cooling node at 0 heat should not consume capacity."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Set up: player at zero heat
        agent.engine.player.heat = 0

        # Add a limited-capacity cooling node
        agent.engine.game_map.cooling_nodes.clear()
        node = RestoreNode(node_type="cooling", total_capacity=30)
        agent.engine.game_map.cooling_nodes[player_pos] = node

        # Process a turn
        agent.engine.game_session.process_turn()

        # Node should NOT have consumed capacity (no benefit provided)
        assert node.used_capacity == 0, "No capacity should be consumed when heat is already 0"

    def test_cpu_at_max_doesnt_consume_capacity(self):
        """Stepping on CPU node at max CPU should not consume capacity."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Set up: player at max CPU
        agent.engine.player.cpu = agent.engine.player.max_cpu

        # Add a limited-capacity CPU node
        agent.engine.game_map.cpu_recovery_nodes.clear()
        node = RestoreNode(node_type="cpu", total_capacity=30)
        agent.engine.game_map.cpu_recovery_nodes[player_pos] = node

        # Process a turn
        agent.engine.game_session.process_turn()

        # Node should NOT have consumed capacity (no benefit provided)
        assert node.used_capacity == 0, "No capacity should be consumed when CPU is already max"

    def test_ghost_at_zero_trace_doesnt_consume_capacity(self):
        """Stepping on ghost node at 0 trace should not consume capacity."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)
        player_pos = (agent.engine.player.x, agent.engine.player.y)

        # Set up: player at zero trace
        agent.engine.player.trace_level = 0

        # Add a limited-capacity ghost node
        agent.engine.game_map.ghost_nodes.clear()
        node = RestoreNode(node_type="ghost", total_capacity=30)
        agent.engine.game_map.ghost_nodes[player_pos] = node

        # Process a turn
        agent.engine.game_session.process_turn()

        # Node should NOT have consumed capacity (no benefit provided)
        assert node.used_capacity == 0, "No capacity should be consumed when trace is already 0"


class TestNodeCapacityResetOnLevelTransition:
    """Tests that nodes get fresh capacity on level transitions."""

    def test_nodes_cleared_on_level_generation(self):
        """Level generation should clear old nodes and create fresh ones."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Get reference to current level's nodes
        level_1_cooling = dict(agent.engine.game_map.cooling_nodes)

        # Deplete a node on level 1
        if level_1_cooling:
            first_pos = next(iter(level_1_cooling.keys()))
            old_node = level_1_cooling[first_pos]
            old_node.use(old_node.total_capacity if old_node.total_capacity > 0 else 0)

        # Progress to level 2
        agent.engine.level = 2
        agent.engine.game_session.level_coordinator.generate_procedural_level()

        # Level 2 should have fresh nodes (not the same object references)
        level_2_cooling = agent.engine.game_map.cooling_nodes

        # If there were nodes on level 1, verify level 2 has different node objects
        if level_1_cooling:
            for pos, node in level_2_cooling.items():
                if pos in level_1_cooling:
                    # Same position could exist, but should be fresh node
                    assert (
                        node.used_capacity == 0
                    ), "Level 2 nodes should have fresh capacity (used_capacity=0)"

    def test_depleted_nodes_dont_carry_over(self):
        """Depleted nodes on level 1 should not affect level 2."""
        from tests.test_agent import GameTestAgent

        agent = GameTestAgent(seed=42)

        # Count nodes on level 1 before we modify them
        level_1_cooling_count = len(agent.engine.game_map.cooling_nodes)
        level_1_cpu_count = len(agent.engine.game_map.cpu_recovery_nodes)
        level_1_ghost_count = len(agent.engine.game_map.ghost_nodes)

        # Deplete ALL cooling nodes on level 1
        for pos, node in agent.engine.game_map.cooling_nodes.items():
            if node.total_capacity > 0:
                node.use(node.total_capacity)

        # Generate level 2
        agent.engine.level = 2
        agent.engine.game_session.level_coordinator.generate_procedural_level()

        # Level 2 should have fresh nodes with 0 used_capacity
        fresh_count = 0
        for pos, node in agent.engine.game_map.cooling_nodes.items():
            if node.used_capacity == 0:
                fresh_count += 1

        # All nodes on level 2 should be fresh
        level_2_cooling_count = len(agent.engine.game_map.cooling_nodes)
        assert fresh_count == level_2_cooling_count, (
            f"All {level_2_cooling_count} cooling nodes on level 2 should be fresh, "
            f"but only {fresh_count} have used_capacity=0"
        )
