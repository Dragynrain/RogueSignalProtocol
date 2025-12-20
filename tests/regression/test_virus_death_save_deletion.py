"""
Regression test for virus death save deletion bug.

Bug: When player died from virus damage, save file was not properly deleted
because game_over flag was not set, allowing auto-save on window close to
restore the dead game state.

This test verifies that:
1. Virus death properly sets game_over = True
2. Save deletion happens during virus death
3. Auto-save is blocked when player is dead from virus
"""

from tests.test_agent import GameTestAgent


class TestVirusDeathSaveDeletion:
    """Regression tests for virus death save deletion."""

    def test_virus_death_sets_game_over_flag(self):
        """Virus death must set game_over = True to prevent auto-save."""
        agent = GameTestAgent(seed=42)

        # Apply lethal virus damage
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 1  # Set to 1 so virus damage kills

        # Trigger virus damage (happens in process_turn via temporary effects)
        initial_cpu = agent.engine.player.cpu
        agent.engine.process_turn()

        # Verify death occurred and game_over is set
        assert agent.engine.player.cpu <= 0, "Player should be dead from virus"
        assert agent.engine.game_over is True, "game_over must be True to prevent auto-save"

    def test_virus_death_deletes_save(self):
        """Virus death must delete save file (permadeath)."""
        agent = GameTestAgent(seed=42)

        # Save the game first
        from game_save import SaveGameManager

        SaveGameManager.save_game(agent.engine)
        assert SaveGameManager.save_exists(), "Save should exist before death"

        # Apply lethal virus damage
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 1

        # Trigger death
        agent.engine.process_turn()

        # Verify save was deleted
        assert not SaveGameManager.save_exists(), "Save must be deleted on virus death"

    def test_auto_save_blocked_after_virus_death(self):
        """Auto-save should be blocked when player is dead from virus."""
        agent = GameTestAgent(seed=42)

        # Apply lethal virus damage
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 1

        # Trigger death
        agent.engine.process_turn()

        # Verify player is dead and game_over is set
        assert agent.engine.player.cpu <= 0
        assert agent.engine.game_over is True

        # Try to auto-save (simulates window close event)
        from game_save import SaveGameManager

        agent.engine.auto_save()

        # Verify auto-save was blocked (no save exists)
        assert not SaveGameManager.save_exists(), "Auto-save must be blocked when game_over=True"

    def test_virus_death_tracks_correct_death_cause(self):
        """Virus death should track 'virus' as death cause in metrics."""
        agent = GameTestAgent(seed=42)

        # Apply lethal virus damage
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 1

        # Trigger death and capture logs
        import logging
        from io import StringIO

        log_capture = StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.WARNING)
        logging.root.addHandler(handler)

        try:
            agent.engine.process_turn()
            log_output = log_capture.getvalue()

            # Verify death was logged with correct cause
            assert "PLAYER DEATH - VIRUS" in log_output, "Death cause should be logged as VIRUS"
        finally:
            logging.root.removeHandler(handler)

    def test_virus_death_pending_dialogue_set(self):
        """Virus death should set pending_death_dialogue for consistent behavior."""
        agent = GameTestAgent(seed=42)

        # Apply lethal virus damage
        agent.engine.player.temporary_effects["virus_turns"] = 5
        agent.engine.player.cpu = 1

        # Trigger death
        agent.engine.process_turn()

        # Verify pending_death_dialogue is set (deferred dialogue pattern)
        assert hasattr(agent.engine, "pending_death_dialogue")
        assert (
            agent.engine.pending_death_dialogue is True
        ), "Virus death should set pending_death_dialogue like other death paths"

    def test_combat_death_deletes_save_immediately(self):
        """Combat death must delete save file immediately, not wait for process_turn.

        Regression: Player could "Continue" after dying from enemy attack because
        save deletion only happened in process_turn, which might not complete.
        """
        agent = GameTestAgent(seed=42)

        # Save the game first
        from game_save import SaveGameManager

        SaveGameManager.save_game(agent.engine)
        assert SaveGameManager.save_exists(), "Save should exist before death"

        # Get an enemy and simulate lethal attack
        # Set player to 1 CPU so any attack kills them
        agent.engine.player.cpu = 1

        # Find an enemy that can deal damage (not inhibitor/virus which do 0 damage)
        enemy = None
        for e in agent.engine.enemies:
            if hasattr(e, "attack_player") and e.type_data.damage > 0:
                enemy = e
                break

        assert enemy is not None, "Need a damage-dealing enemy to test combat death"

        # Position enemy adjacent to player
        enemy.x = agent.engine.player.x + 1
        enemy.y = agent.engine.player.y

        # Attack player - this should delete save immediately
        enemy.attack_player(agent.engine.player, game_engine=agent.engine)

        # Verify save was deleted immediately (not waiting for process_turn)
        assert (
            not SaveGameManager.save_exists()
        ), "Save must be deleted immediately on combat death, not after process_turn"
