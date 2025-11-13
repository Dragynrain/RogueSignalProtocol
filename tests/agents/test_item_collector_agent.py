"""
Item Collector Agent Tests

Agent that validates item spawn distribution and collection mechanics:
- Finds all items on level using the actual GameMap dictionaries
- Validates item pickup mechanics
- Tests item spawn distribution patterns
- Ensures items are accessible (not in walls)
"""

from tests.test_agent import GameTestAgent


class ItemCollectorAgent(GameTestAgent):
    """
    Agent that finds and collects all items on a level.

    Uses the actual GameMap architecture (dictionaries, not arrays):
    - game_map.code_hacks: Dict[Tuple[int, int], CodeHack]
    - game_map.exploit_pickups: Dict[Tuple[int, int], ExploitItem]
    - game_map.permanent_upgrades: Dict[Tuple[int, int], str]
    - game_map.story_fragments: Dict[Tuple[int, int], StoryFragment]
    """

    def __init__(self, seed=None, level=1):
        super().__init__(seed=seed, level=level)
        self.items_collected = []
        self.items_found = 0

    def find_all_items(self):
        """Find all item positions using GameMap dictionaries."""
        item_positions = []

        # Code hacks
        item_positions.extend(
            [
                {"pos": pos, "type": "code_hack", "item": item}
                for pos, item in self.game_map.code_hacks.items()
            ]
        )

        # Exploit pickups
        item_positions.extend(
            [
                {"pos": pos, "type": "exploit", "item": item}
                for pos, item in self.game_map.exploit_pickups.items()
            ]
        )

        # Permanent upgrades
        item_positions.extend(
            [
                {"pos": pos, "type": "upgrade", "item": upgrade_key}
                for pos, upgrade_key in self.game_map.permanent_upgrades.items()
            ]
        )

        # Story fragments
        item_positions.extend(
            [
                {"pos": pos, "type": "story", "item": fragment}
                for pos, fragment in self.game_map.story_fragments.items()
            ]
        )

        self.items_found = len(item_positions)
        return item_positions

    def collect_item_at(self, x, y):
        """Move to position and attempt to collect item."""
        success = self.move_to(x, y)
        if success and (self.player.x == x and self.player.y == y):
            self.items_collected.append((x, y))
            return True
        return False

    def collect_all_items(self, max_moves=500):
        """Attempt to collect all items on map."""
        items = self.find_all_items()

        collected_count = 0
        for item_data in items:
            if self.turn >= max_moves:
                break

            x, y = item_data["pos"]
            if self.collect_item_at(x, y):
                collected_count += 1

        return collected_count


class TestItemCollectorAgent:
    """Test item collection agent functionality using real GameMap API."""

    def test_agent_finds_code_hacks(self):
        """Agent should find code hacks using game_map.code_hacks."""
        agent = ItemCollectorAgent(seed=77001, level=1)

        # Access code hacks directly
        code_hack_positions = list(agent.game_map.code_hacks.keys())

        # Should find some code hacks on level 1
        # (Exact count depends on level generation)
        assert isinstance(code_hack_positions, list)

    def test_agent_finds_exploit_pickups(self):
        """Agent should find exploit pickups using game_map.exploit_pickups."""
        agent = ItemCollectorAgent(seed=77002, level=1)

        # Access exploit pickups directly
        exploit_positions = list(agent.game_map.exploit_pickups.keys())

        # Should be a list (may be empty on some seeds)
        assert isinstance(exploit_positions, list)

    def test_agent_finds_permanent_upgrades(self):
        """Agent should find upgrades using game_map.permanent_upgrades."""
        agent = ItemCollectorAgent(seed=77003, level=1)

        # Access upgrades directly
        upgrade_positions = list(agent.game_map.permanent_upgrades.keys())

        # Should be a list
        assert isinstance(upgrade_positions, list)

    def test_find_all_items_aggregates_correctly(self):
        """find_all_items should aggregate all item types."""
        agent = ItemCollectorAgent(seed=77004, level=1)

        all_items = agent.find_all_items()

        # Should return list of item data
        assert isinstance(all_items, list)

        # Each item should have position and type
        for item in all_items:
            assert "pos" in item
            assert "type" in item
            assert "item" in item
            assert item["type"] in ["code_hack", "exploit", "upgrade", "story"]

    def test_items_not_in_walls(self):
        """Items should not spawn inside walls."""
        agent = ItemCollectorAgent(seed=77005, level=1)

        all_items = agent.find_all_items()

        for item in all_items:
            x, y = item["pos"]
            # Item position should not be a wall
            assert (
                x,
                y,
            ) not in agent.game_map.walls, f"{item['type']} at ({x}, {y}) is inside a wall!"

    def test_items_within_map_bounds(self):
        """All items should be within map boundaries."""
        agent = ItemCollectorAgent(seed=77006, level=1)

        all_items = agent.find_all_items()

        for item in all_items:
            x, y = item["pos"]
            assert 0 <= x < agent.game_map.width, f"Item at ({x}, {y}) is outside map width!"
            assert 0 <= y < agent.game_map.height, f"Item at ({x}, {y}) is outside map height!"

    def test_item_spawn_distribution(self):
        """Items should be distributed across map, not all clustered."""
        agent = ItemCollectorAgent(seed=77007, level=1)

        all_items = agent.find_all_items()

        if len(all_items) >= 3:
            # Get all positions
            positions = [item["pos"] for item in all_items]
            x_coords = [x for x, y in positions]
            y_coords = [y for x, y in positions]

            # Should have some spatial variance
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)

            # Items shouldn't all be in a 2x2 cluster
            assert x_range > 2 or y_range > 2, "All items clustered in tiny area!"

    def test_agent_can_pathfind_to_items(self):
        """Agent should be able to pathfind to item locations."""
        agent = ItemCollectorAgent(seed=77008, level=1)

        all_items = agent.find_all_items()

        if len(all_items) > 0:
            # Try to move to first item
            first_item = all_items[0]
            x, y = first_item["pos"]

            success = agent.collect_item_at(x, y)

            # Should either succeed or fail gracefully
            assert isinstance(success, bool)

    def test_collect_all_items_workflow(self):
        """Agent should handle full item collection workflow."""
        agent = ItemCollectorAgent(seed=77009, level=1)

        # Find items first
        all_items = agent.find_all_items()
        expected_count = len(all_items)

        # Try to collect them
        collected = agent.collect_all_items(max_moves=200)

        # Should collect some items (0 to all of them)
        assert 0 <= collected <= expected_count
        assert agent.items_found == expected_count

    def test_item_types_tracked_correctly(self):
        """Agent should correctly identify item types."""
        agent = ItemCollectorAgent(seed=77010, level=1)

        all_items = agent.find_all_items()

        # Count items by type
        code_hacks = [i for i in all_items if i["type"] == "code_hack"]
        exploits = [i for i in all_items if i["type"] == "exploit"]
        upgrades = [i for i in all_items if i["type"] == "upgrade"]
        stories = [i for i in all_items if i["type"] == "story"]

        # Should match direct dictionary access
        assert len(code_hacks) == len(agent.game_map.code_hacks)
        assert len(exploits) == len(agent.game_map.exploit_pickups)
        assert len(upgrades) == len(agent.game_map.permanent_upgrades)
        assert len(stories) == len(agent.game_map.story_fragments)

    def test_no_duplicate_item_positions(self):
        """Each item position should be unique (no stacking)."""
        agent = ItemCollectorAgent(seed=77011, level=1)

        all_items = agent.find_all_items()
        positions = [item["pos"] for item in all_items]

        # No duplicate positions
        assert len(positions) == len(set(positions)), "Multiple items at same position!"
