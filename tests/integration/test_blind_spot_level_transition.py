"""
Integration tests for blind spot position tracking across level transitions.

Verifies that _last_blind_spot_position is properly reset when transitioning
between levels, preventing incorrect blind spot consumption on new levels.
"""

from game_entities import Position
from tests.test_agent import GameTestAgent


class TestBlindSpotLevelTransition:
    """Tests for blind spot tracking across level transitions."""

    def test_blind_spot_position_reset_on_level_generation(self):
        """_last_blind_spot_position should be reset when generating a new level."""
        agent = GameTestAgent(seed=42)

        # Simulate player was in a blind spot at position (15, 15)
        agent.engine.game_session.turn_manager._last_blind_spot_position = Position(15, 15)

        # Verify it was set
        assert agent.engine.game_session.turn_manager._last_blind_spot_position == Position(15, 15)

        # Generate a new level (simulates level transition)
        agent.engine.level = 2
        agent.engine.game_session.level_coordinator.generate_procedural_level()

        # _last_blind_spot_position should be reset to None
        assert agent.engine.game_session.turn_manager._last_blind_spot_position is None

    def test_blind_spot_not_incorrectly_consumed_after_level_transition(self):
        """Blind spots on new level shouldn't be consumed due to old level position."""
        agent = GameTestAgent(seed=42)

        # Enable A20 blind spot consuming
        agent.engine.ascension_modifiers.blind_spots_consumable = True

        # Simulate player was in a blind spot at (20, 20) on level 1
        old_pos = Position(20, 20)
        agent.engine.game_session.turn_manager._last_blind_spot_position = old_pos

        # Generate level 2
        agent.engine.level = 2
        agent.engine.game_session.level_coordinator.generate_procedural_level()

        # Add a blind spot at position (20, 20) on the NEW level
        # (same coordinates as old level position)
        test_pos = (20, 20)
        agent.engine.game_map.blind_spots.add(test_pos)

        # Move player to a different position and process a turn
        # This would have incorrectly consumed the (20,20) blind spot
        # if _last_blind_spot_position wasn't reset
        agent.engine.player.position = Position(10, 10)
        agent.engine.game_session.process_turn()

        # The blind spot at (20, 20) should NOT have been consumed
        # because _last_blind_spot_position was reset on level generation
        assert test_pos in agent.engine.game_map.blind_spots, (
            "Blind spot should not be consumed just because previous level "
            "had player at same coordinates"
        )

    def test_blind_spot_consumed_normally_within_same_level(self):
        """A20: Blind spots should still be consumed when player leaves within same level."""
        agent = GameTestAgent(seed=42)

        # Enable A20 blind spot consuming
        agent.engine.ascension_modifiers.blind_spots_consumable = True

        # Add a blind spot adjacent to player
        player_pos = agent.engine.player.position
        blind_spot_pos = Position(player_pos.x + 1, player_pos.y)
        agent.engine.game_map.blind_spots.add((blind_spot_pos.x, blind_spot_pos.y))

        # Move player into blind spot
        agent.engine.player.position = blind_spot_pos
        agent.engine.game_session.process_turn()

        # Verify the blind spot is being tracked
        assert agent.engine.game_session.turn_manager._last_blind_spot_position == blind_spot_pos

        # Move player out of blind spot
        new_pos = Position(blind_spot_pos.x + 1, blind_spot_pos.y)
        # Ensure new position is not a wall
        agent.engine.game_map.walls.discard((new_pos.x, new_pos.y))
        agent.engine.player.position = new_pos
        agent.engine.game_session.process_turn()

        # The blind spot should have been consumed
        assert (
            blind_spot_pos.x,
            blind_spot_pos.y,
        ) not in agent.engine.game_map.blind_spots, (
            "Blind spot should be consumed when player leaves it"
        )
        assert (
            blind_spot_pos.x,
            blind_spot_pos.y,
        ) in agent.engine.game_map.used_blind_spots, (
            "Consumed blind spot should be in used_blind_spots set"
        )
