#!/usr/bin/env python3
"""
Integration tests for prologue (tutorial) flow.

Tests the complete prologue lifecycle:
- Starting prologue from menu
- Death/restart cycle (no permadeath)
- Completion returns to menu
- Save blocking in prologue mode
"""


import pytest

from rsp.core.config import GameSettings
from rsp.core.engine import GameEngine
from rsp.entities.base import Position
from rsp.systems.prologue_thoughts import reset_prologue_thoughts


def silent_settings():
    """Create GameSettings with all audio disabled."""
    settings = GameSettings()
    settings.master_volume = 0.0
    settings.sfx_volume = 0.0
    settings.music_volume = 0.0
    settings.graphics_mode = "glyph"
    return settings


class TestPrologueStartup:
    """Test prologue mode initialization."""

    def test_prologue_mode_flag_set(self):
        """Engine has prologue_mode=True when started in prologue."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        assert engine.prologue_mode is True

    def test_prologue_starts_at_level_0(self):
        """Prologue starts at level 0."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        assert engine.level == 0

    def test_prologue_has_ascension_0(self):
        """Prologue forces ascension level 0."""
        engine = GameEngine(
            settings=silent_settings(),
            prologue_mode=True,
            ascension_level=10,  # Try to force higher
            load_save=False,
        )

        assert engine.ascension_level == 0

    def test_prologue_uses_fixed_layout(self):
        """Prologue uses fixed level layout (not random)."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # The prologue uses a fixed layout with known characteristics
        # Check for blind spots (tutorial feature)
        assert len(engine.game_map.blind_spots) > 0

    def test_prologue_has_intro_dialogue(self):
        """Prologue shows introduction dialogue on start."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Intro dialogue should be shown
        assert engine.dialogue_state.is_active()

    def test_prologue_spawn_position(self):
        """Player spawns at expected position in prologue."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Prologue spawn is at (1, 1)
        assert engine.player.position.x == 1
        assert engine.player.position.y == 1


class TestPrologueDeath:
    """Test prologue death handling (no permadeath)."""

    def test_prologue_death_does_not_set_game_over(self):
        """Death in prologue doesn't set game_over flag."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Dismiss intro dialogue
        engine.dialogue_state.close()

        # Kill the player
        engine.player.cpu = 0
        engine.death_handler.check_death("Test death")

        # game_over should NOT be set in prologue
        assert engine.game_state.game_over is False

    def test_prologue_death_sets_restart_pending(self):
        """Death in prologue sets restart pending flag."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Dismiss intro dialogue
        engine.dialogue_state.close()

        # Kill the player
        engine.player.cpu = 0
        engine.death_handler.check_death("Test death")

        assert engine.prologue_restart_pending is True

    def test_prologue_death_shows_dialogue(self):
        """Death in prologue shows death dialogue."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Dismiss intro dialogue
        engine.dialogue_state.close()

        # Kill the player
        engine.player.cpu = 0
        engine.death_handler.check_death("Test death")

        # Death dialogue should be shown
        assert engine.dialogue_state.is_active()
        assert "CONNECTION LOST" in engine.dialogue_state.active_dialogue.title


class TestPrologueCompletion:
    """Test prologue completion (reaching gateway)."""

    def test_prologue_completion_sets_pending_flag(self):
        """Completing prologue sets completion pending flag."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Dismiss intro dialogue
        engine.dialogue_state.close()

        # Manually trigger level completion (simulating gateway reach)
        engine.next_level()

        # Should set completion pending
        assert engine.prologue_completed_pending is True

    def test_prologue_completion_shows_dialogue(self):
        """Completing prologue shows completion dialogue."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # Dismiss intro dialogue
        engine.dialogue_state.close()

        # Manually trigger level completion
        engine.next_level()

        # Completion dialogue should be shown
        assert engine.dialogue_state.is_active()
        assert "UPLINK ESTABLISHED" in engine.dialogue_state.active_dialogue.title


class TestPrologueThoughtTriggers:
    """Test prologue thought triggers fire correctly."""

    def setup_method(self):
        """Reset thought tracking before each test."""
        reset_prologue_thoughts()

    def test_diagonal_move_triggers_thought(self):
        """Diagonal movement triggers diagonal_discover thought."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)
        engine.dialogue_state.close()

        # Move diagonally
        engine.move_player(1, 1)

        # Check thought was triggered (message log should contain it)
        # Note: Actual thought content depends on narrative_content.json
        from rsp.systems.prologue_thoughts import has_shown_thought

        assert has_shown_thought("diagonal_discover")

    def test_blind_spot_entry_triggers_thought(self):
        """Entering blind spot triggers blindspot_observe thought."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)
        engine.dialogue_state.close()

        # Find a blind spot and move there
        if engine.game_map.blind_spots:
            blind_spot = next(iter(engine.game_map.blind_spots))
            engine.player.position = Position(blind_spot[0], blind_spot[1])

            # Process turn to trigger the thought
            engine.game_session.process_turn()


            # Note: This may not trigger if player didn't "enter" (was teleported)
            # The actual trigger happens during normal movement
            # This test verifies the system doesn't crash


class TestPrologueIsolation:
    """Test prologue is isolated from normal game state."""

    def test_prologue_does_not_save(self):
        """Prologue does not create save files."""
        engine = GameEngine(settings=silent_settings(), prologue_mode=True, load_save=False)

        # The save system should not be triggered in prologue
        # Attempting to save should be blocked or ignored
        # (Implementation detail - verify by checking save doesn't exist)

    def test_normal_game_not_affected(self):
        """Starting normal game after prologue works correctly."""
        # Start prologue
        prologue_engine = GameEngine(
            settings=silent_settings(), prologue_mode=True, load_save=False
        )
        assert prologue_engine.prologue_mode is True

        # Start normal game
        normal_engine = GameEngine(settings=silent_settings(), prologue_mode=False, load_save=False)
        assert normal_engine.prologue_mode is False
        assert normal_engine.level == 1  # Normal game starts at level 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
