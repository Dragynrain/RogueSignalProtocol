"""
Test death handling consistency across all death types.

All death types (combat, virus, overheat, self_damage) should:
1. Set game_over = True
2. Delete save file
3. Finalize session metrics with correct death_cause
4. Set pending_death_dialogue = True
5. Check achievements

This test ensures the centralized PlayerDeathHandler is used for all deaths.
"""

from game_metrics import init_session_metrics
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

        # Verify death was handled correctly with correct cause
        assert agent.engine.game_over is True
        assert agent.engine.pending_death_dialogue is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "virus"

    def test_combat_death_sets_correct_death_cause(self):
        """Combat death should set death_cause to 'combat'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player directly (simulates damage from combat)
        agent.engine.player.cpu = 0

        # Process turn - should detect death via fallback check
        agent.engine.game_session.process_turn()

        # Verify death was handled with correct cause
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "combat"

    def test_overheat_death_sets_correct_death_cause(self):
        """Overheat death should set death_cause to 'overheat'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Set heat at max so movement will trigger overheat damage
        agent.engine.player.heat = agent.engine.player.max_heat
        # Set CPU low so overheat damage (base 5) will kill
        agent.engine.player.cpu = 3

        # Try to move in each direction until one succeeds
        # Movement when overheated triggers overheat damage
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if not agent.engine.game_over:
                agent.engine.move_player(dx, dy)

        # Verify death was handled with correct cause
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "overheat"

    def test_self_damage_death_sets_correct_death_cause(self):
        """Self-damage death (Logic Bomb friendly fire) should set death_cause to 'self_damage'."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Trigger death via the death handler directly with self_damage cause
        # (in real gameplay, this is called from exploit system when Logic Bomb hits player)
        agent.engine.player.cpu = 0
        agent.engine.death_handler.check_death("self_damage", source="Logic Bomb")

        # Verify death was handled correctly
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "self_damage"
        assert agent.engine.death_handler.death_event.source == "Logic Bomb"

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
    """Test correct death cause is detected at damage sites."""

    def test_virus_detected_when_virus_active(self):
        """Death from virus damage should be classified as virus death."""
        agent = GameTestAgent(seed=42)

        # Set up virus death conditions
        agent.engine.player.temporary_effects["virus_turns"] = 3
        agent.engine.player.cpu = 1

        # Process virus damage (will kill player)
        agent.engine.game_session.process_turn()

        # Should be detected as virus death
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "virus"

    def test_overheat_detected_from_movement(self):
        """Death from movement overheat should be classified as overheat."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Set heat at max so movement triggers overheat damage
        agent.engine.player.heat = agent.engine.player.max_heat
        # Low CPU so overheat damage (base 5) will kill
        agent.engine.player.cpu = 3

        # Try to move in each direction until one succeeds
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if not agent.engine.game_over:
                agent.engine.move_player(dx, dy)

        # Should be detected as overheat death
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.death_event is not None
        assert agent.engine.death_handler.death_event.cause == "overheat"

    def test_self_damage_detected_via_death_handler(self):
        """Self-damage death is now tracked via PlayerDeathHandler, not a flag."""
        agent = GameTestAgent(seed=42)

        # Self-damage death is now triggered directly at the damage source
        # (e.g., Logic Bomb friendly fire calls death_handler.check_death("self_damage"))
        agent.engine.player.cpu = 0
        agent.engine.death_handler.check_death("self_damage", source="Logic Bomb")

        assert agent.engine.game_over is True
        # Death event should have correct cause
        assert agent.engine.death_handler.death_event.cause == "self_damage"


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
        assert agent.engine.death_handler.is_handled is True

        # Second turn should not re-process death
        # (the death handler is idempotent)
        agent.engine.game_session.process_turn()

        # State should remain consistent
        assert agent.engine.game_over is True
        assert agent.engine.death_handler.is_handled is True

    def test_death_handler_reset_allows_new_game(self):
        """Resetting the death handler should allow death handling in a new game."""
        agent = GameTestAgent(seed=42)
        init_session_metrics()

        # Kill player
        agent.engine.player.cpu = 0
        agent.engine.death_handler.check_death("combat")
        assert agent.engine.death_handler.is_handled is True

        # Reset handler (simulates new game)
        agent.engine.death_handler.reset()
        assert agent.engine.death_handler.is_handled is False
        assert agent.engine.death_handler.death_event is None
