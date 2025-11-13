#!/usr/bin/env python3
"""
Graphics Mode Switch Smoke Test

Quick smoke test to validate that graphics mode switching works without
crashes during basic gameplay. This is a simplified version of the full
integration tests, focused on catching obvious regressions.

Critical because:
- Mode switching is a frequently used feature
- Quick test catches major regressions
- Part of CI/CD smoke test suite
"""

from tests.test_agent import GameTestAgent


class TestGraphicsModeSwitchSmoke:
    """Quick smoke tests for graphics mode switching."""

    def test_can_switch_to_glyph_mode(self):
        """Can switch to glyph mode without crash."""
        agent = GameTestAgent(seed=42)

        # Switch to glyph mode
        agent.engine.settings.graphics_mode = "glyph"

        # Play a few turns
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Should complete successfully
        assert agent.turn == 2

    def test_can_switch_to_graphics_mode(self):
        """Can switch to graphics mode without crash."""
        agent = GameTestAgent(seed=42)

        # Switch to graphics mode
        agent.engine.settings.graphics_mode = "graphics"

        # Play a few turns
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Should complete successfully
        assert agent.turn == 2

    def test_can_switch_back_and_forth(self):
        """Can switch between modes multiple times."""
        agent = GameTestAgent(seed=42)

        # Switch glyph -> graphics -> glyph
        agent.engine.settings.graphics_mode = "glyph"
        agent.move_player(1, 0)

        agent.engine.settings.graphics_mode = "graphics"
        agent.move_player(0, 1)

        agent.engine.settings.graphics_mode = "glyph"
        agent.move_player(1, 0)

        # Should complete successfully
        assert agent.turn == 3

    def test_mode_switch_during_gameplay(self):
        """Mode switch during active gameplay works."""
        agent = GameTestAgent(seed=42)

        # Play for 10 turns
        for _ in range(10):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)

        # Switch mode mid-game
        agent.engine.settings.graphics_mode = "graphics"

        # Continue playing
        for _ in range(10):
            if agent.engine.game_over:
                break
            agent.move_player(0, 1)

        # Should complete successfully (or game ended)
        assert agent.turn > 0

    def test_game_state_preserved_after_switch(self):
        """Game state is preserved after mode switch."""
        agent = GameTestAgent(seed=42)

        # Play to build state
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Record state
        hp_before = agent.player.cpu
        pos_before = (agent.player.x, agent.player.y)
        turn_before = agent.turn

        # Switch mode
        agent.engine.settings.graphics_mode = "glyph"

        # State should be preserved
        assert agent.player.cpu == hp_before
        assert (agent.player.x, agent.player.y) == pos_before
        assert agent.turn == turn_before

    def test_multiple_switches_stable(self):
        """Multiple mode switches don't destabilize game."""
        agent = GameTestAgent(seed=42)

        # Switch 10 times
        for i in range(10):
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

            # Play a turn
            agent.move_player(1, 0)

        # Should complete successfully
        assert agent.turn == 10

    def test_switch_with_enemies_present(self):
        """Mode switch works when enemies are active."""
        agent = GameTestAgent(seed=42)

        # Verify enemies exist
        assert len(agent.enemies) > 0

        # Switch mode
        agent.engine.settings.graphics_mode = "graphics"

        # Continue playing
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Should complete successfully
        assert agent.turn == 2

    def test_quick_gameplay_smoke_with_switches(self):
        """Quick gameplay with mode switches completes."""
        agent = GameTestAgent(seed=42)

        # Play 30 turns with occasional mode switches
        for turn_num in range(30):
            if agent.engine.game_over:
                break

            # Switch every 10 turns
            if turn_num % 10 == 0:
                mode = "glyph" if turn_num % 20 == 0 else "graphics"
                agent.engine.settings.graphics_mode = mode

            # Play turn
            agent.move_player(1, 0)

        # Should complete successfully (or game ended)
        assert agent.turn > 0


class TestGraphicsModeSwitchQuickValidation:
    """Quick validation of mode switch behavior."""

    def test_settings_object_exists(self):
        """Settings object is accessible."""
        agent = GameTestAgent(seed=42)

        assert hasattr(agent.engine, "settings")
        assert hasattr(agent.engine.settings, "graphics_mode")

    def test_default_graphics_mode_is_valid(self):
        """Default graphics mode is valid."""
        agent = GameTestAgent(seed=42)

        assert agent.engine.settings.graphics_mode in ["glyph", "graphics"]

    def test_can_read_graphics_mode(self):
        """Can read current graphics mode."""
        agent = GameTestAgent(seed=42)

        current_mode = agent.engine.settings.graphics_mode

        assert current_mode is not None
        assert isinstance(current_mode, str)

    def test_can_write_graphics_mode(self):
        """Can write graphics mode setting."""
        agent = GameTestAgent(seed=42)

        # Change mode
        agent.engine.settings.graphics_mode = "glyph"

        # Verify change took effect
        assert agent.engine.settings.graphics_mode == "glyph"

    def test_mode_switch_doesnt_crash_game(self):
        """Mode switch doesn't crash the game engine."""
        agent = GameTestAgent(seed=42)

        # Switch modes
        agent.engine.settings.graphics_mode = "graphics"
        agent.engine.settings.graphics_mode = "glyph"
        agent.engine.settings.graphics_mode = "graphics"

        # Game should still be functional
        agent.move_player(1, 0)
        assert agent.turn == 1


class TestGraphicsModeSwitchRapidFire:
    """Rapid-fire mode switching tests."""

    def test_very_rapid_switches(self):
        """Very rapid mode switches don't crash."""
        agent = GameTestAgent(seed=42)

        # Rapidly switch 20 times
        for i in range(20):
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

        # Game should still work
        agent.move_player(1, 0)
        assert agent.turn == 1

    def test_rapid_switches_with_gameplay(self):
        """Rapid switches interleaved with gameplay."""
        agent = GameTestAgent(seed=42)

        for i in range(10):
            # Switch mode
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

            # Play turn
            agent.move_player(1, 0)

        # Should complete successfully
        assert agent.turn == 10

    def test_switch_every_turn(self):
        """Switching mode every single turn works."""
        agent = GameTestAgent(seed=42)

        for i in range(20):
            if agent.engine.game_over:
                break

            # Alternate mode every turn
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

            # Play turn
            agent.move_player(1, 0)

        # Should complete successfully (or game ended)
        assert agent.turn > 0


class TestGraphicsModeSwitchEdgeCases:
    """Edge case tests for mode switching."""

    def test_switch_to_same_mode_twice(self):
        """Switching to same mode multiple times works."""
        agent = GameTestAgent(seed=42)

        # Switch to same mode multiple times
        agent.engine.settings.graphics_mode = "glyph"
        agent.engine.settings.graphics_mode = "glyph"
        agent.engine.settings.graphics_mode = "glyph"

        # Should still work
        agent.move_player(1, 0)
        assert agent.turn == 1

    def test_switch_at_turn_zero(self):
        """Mode switch at turn 0 (before any gameplay) works."""
        agent = GameTestAgent(seed=42)

        # Switch before any gameplay
        assert agent.turn == 0
        agent.engine.settings.graphics_mode = "graphics"

        # Now play
        agent.move_player(1, 0)
        assert agent.turn == 1

    def test_switch_after_many_turns(self):
        """Mode switch after extended play works."""
        agent = GameTestAgent(seed=42)

        # Play 50 turns
        for _ in range(50):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)

        # Now switch
        agent.engine.settings.graphics_mode = "glyph"

        # Continue playing if still alive
        if not agent.engine.game_over:
            agent.move_player(0, 1)

        # Should work fine
        assert agent.turn > 0
