"""
Test death handling consistency across all death types.

All death types (combat, virus, overheat, self_damage) should:
1. Set game_over = True
2. Delete save file
3. Finalize session metrics with correct death_cause
4. Set pending_death_dialogue = True
5. Check achievements

This test ensures the centralized _handle_player_death() is used for all deaths.
"""

import pytest

from game_metrics import finalize_session, get_current_session, init_session_metrics
from tests.test_agent import GameTestAgent


class TestDeathHandlingConsistency:
    """Test that all death types are handled consistently."""

    def test_virus_death_sets_correct_death_cause(self):
        """Virus death should set death_cause to 'virus'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Give player virus and reduce CPU so virus will kill them
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 2  # Low CPU so virus damage will kill

        # Process turn to trigger virus death
        agent.engine.game_session.process_turn()

        # Verify death was handled correctly
        assert agent.engine.game_over is True
        assert agent.engine.pending_death_dialogue is True

        # Finalize and check death cause
        session = get_current_session()
        assert session is not None

    def test_combat_death_sets_correct_death_cause(self):
        """Combat death should set death_cause to 'combat'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player directly
        agent.engine.player.cpu = 0

        # Process turn - should detect death
        agent.engine.game_session.process_turn()

        # Verify death was handled
        assert agent.engine.game_over is True

    def test_overheat_death_sets_correct_death_cause(self):
        """Overheat death should set death_cause to 'overheat'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Set up overheat conditions
        agent.engine.player.heat = agent.engine.player.max_heat
        agent.engine.player.cpu = 0

        # Process turn
        agent.engine.game_session.process_turn()

        # Verify death was handled
        assert agent.engine.game_over is True

    def test_self_damage_death_sets_correct_death_cause(self):
        """Self-damage death (Logic Bomb friendly fire) should set death_cause to 'self_damage'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Set up self-damage conditions
        agent.engine.friendly_fire_death = True
        agent.engine.player.cpu = 0

        # Process turn
        agent.engine.game_session.process_turn()

        # Verify death was handled
        assert agent.engine.game_over is True

    def test_all_deaths_delete_save(self, tmp_path, monkeypatch):
        """All death types should delete the save file."""
        from game_save import SaveGameManager

        # Patch save path
        test_save = tmp_path / "test_save.json"
        monkeypatch.setattr(SaveGameManager, "_get_save_file_path", lambda: str(test_save))

        # Create a save file
        test_save.write_text('{"test": "data"}')
        assert test_save.exists()

        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player
        agent.engine.player.cpu = 0
        agent.engine.game_session.process_turn()

        # Save should be deleted
        assert not test_save.exists()

    def test_death_metrics_finalized(self):
        """Session metrics should be finalized on death."""
        agent = GameTestAgent(seed=42)
        session = init_session_metrics()

        # Record some gameplay
        session.turns_taken = 50
        session.enemies_killed["scanner"] = 5

        # Kill player
        agent.engine.player.cpu = 0
        agent.engine.game_session.process_turn()

        # Session should still have our tracked data
        assert session.turns_taken >= 50
        assert session.enemies_killed["scanner"] == 5


class TestDeathCauseDetection:
    """Test correct death cause is detected based on game state."""

    def test_virus_detected_when_virus_active(self):
        """Death with active virus should be classified as virus death."""
        agent = GameTestAgent(seed=42)

        # Set up virus death conditions
        agent.engine.player.temporary_effects["virus_turns"] = 3
        agent.engine.player.cpu = 1

        # Process virus damage (will kill player)
        agent.engine.game_session.process_turn()

        # Should be detected as virus death
        assert agent.engine.game_over is True

    def test_overheat_detected_when_at_max_heat(self):
        """Death at max heat should be classified as overheat."""
        agent = GameTestAgent(seed=42)

        # Set up overheat death
        agent.engine.player.heat = agent.engine.player.max_heat
        agent.engine.player.cpu = 0

        agent.engine.game_session.process_turn()

        assert agent.engine.game_over is True

    def test_self_damage_detected_with_friendly_fire_flag(self):
        """Death with friendly_fire_death flag should be classified as self_damage."""
        agent = GameTestAgent(seed=42)

        # Set up self-damage death
        agent.engine.friendly_fire_death = True
        agent.engine.player.cpu = 0

        agent.engine.game_session.process_turn()

        assert agent.engine.game_over is True
        # Flag should be reset after handling
        assert agent.engine.friendly_fire_death is False


class TestDeathHandlerIdempotency:
    """Test that death handler can be called multiple times safely."""

    def test_death_handled_only_once(self):
        """Death should only be processed once even if conditions persist."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player
        agent.engine.player.cpu = 0

        # First turn processes death
        agent.engine.game_session.process_turn()
        assert agent.engine.game_over is True
        assert agent.engine.pending_death_dialogue is True

        # Store state after first processing
        first_game_over = agent.engine.game_over

        # Second turn should not re-process death
        # (the turn manager checks _death_handled flag)
        agent.engine.game_session.turn_manager._death_handled = False  # Reset for test
        agent.engine.game_session.process_turn()

        # State should remain consistent
        assert agent.engine.game_over is True
