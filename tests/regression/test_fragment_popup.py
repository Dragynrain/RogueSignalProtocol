"""
Regression test for data fragment popup not showing.

Bug: When player picks up a data fragment, the lore viewer popup should
automatically open to show the discovered fragment. This wasn't happening
because game.input_handler.renderer was None - the InputHandler with renderer
was created in game_loop but never assigned back to game.input_handler.
"""

from unittest.mock import Mock

from game_inventory import StoryFragment
from tests.test_agent import GameTestAgent


class TestFragmentPopup:
    """Regression tests for data fragment popup."""

    def test_fragment_pickup_opens_lore_viewer(self):
        """Picking up a data fragment should open lore viewer in reading mode.

        Regression: Lore viewer didn't open because game.input_handler.renderer was None.
        The condition checked input_handler.renderer but GameEngine created its own
        InputHandler without a renderer, while game_loop created another one with
        renderer that was never assigned to game.input_handler.
        """
        agent = GameTestAgent(seed=42)

        # Simulate having a renderer (mock the input_handler to have renderer)
        mock_renderer = Mock()
        agent.engine.input_handler.renderer = mock_renderer

        # Use a fragment index that isn't already discovered
        # Fragment 10 should be undiscovered for testing
        test_fragment_index = 10
        agent.engine.story_fragment_manager.discovered_fragments = []  # Clear for test

        # Place a fragment at the player's current position
        # The fragment will be picked up on next turn processing
        player_pos = (agent.engine.player.x, agent.engine.player.y)
        fragment = StoryFragment(test_fragment_index)
        agent.engine.game_map.story_fragments[player_pos] = fragment

        # Process a turn to trigger fragment pickup (player doesn't need to move)
        agent.engine.process_turn()

        # Verify lore viewer was opened
        assert (
            agent.engine.show_lore_viewer is True
        ), "Lore viewer should open when picking up a data fragment"
        assert (
            agent.engine.lore_viewer_mode == "reading"
        ), "Lore viewer should be in reading mode to show the new fragment"

    def test_fragment_pickup_without_renderer_doesnt_crash(self):
        """Fragment pickup should work even without renderer (headless mode).

        In headless tests, there's no renderer, so lore viewer shouldn't open
        but the fragment should still be discovered and game shouldn't crash.
        """
        agent = GameTestAgent(seed=42)

        # Ensure no renderer (headless mode)
        agent.engine.input_handler.renderer = None

        # Use a fragment index that isn't already discovered
        test_fragment_index = 11
        agent.engine.story_fragment_manager.discovered_fragments = []  # Clear for test

        # Place a fragment at player's position
        player_pos = (agent.engine.player.x, agent.engine.player.y)
        fragment = StoryFragment(test_fragment_index)
        agent.engine.game_map.story_fragments[player_pos] = fragment

        # Process turn to trigger fragment pickup - should not crash
        agent.engine.process_turn()

        # Verify fragment was discovered even without popup
        assert (
            test_fragment_index in agent.engine.story_fragment_manager.discovered_fragments
        ), "Fragment should be discovered even without renderer"
        # Lore viewer should NOT open without renderer
        assert (
            agent.engine.show_lore_viewer is False
        ), "Lore viewer should not open in headless mode (no renderer)"
