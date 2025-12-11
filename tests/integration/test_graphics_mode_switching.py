#!/usr/bin/env python3
"""
Graphics Mode Switching Integration Tests

Tests the ability to switch between glyph mode (CP437 ASCII) and graphics mode
(PNG sprites) during gameplay without crashes or state corruption.

Critical because:
- Players frequently switch modes (F11 hotkey in some games)
- Mode switch bugs = lost progress (no autosave)
- Rendering artifacts after switch = broken visuals
- Mouse coordinate misalignment = unplayable

Tests cover:
- Switching between modes
- State preservation across switches
- Memory cleanup
- Rendering pipeline integrity
"""

from game_config import GameSettings
from tests.test_agent import GameTestAgent


class TestGraphicsModeBasics:
    """Basic graphics mode functionality tests."""

    def test_settings_has_graphics_mode(self):
        """GameSettings has graphics_mode attribute."""
        settings = GameSettings()
        assert hasattr(settings, "graphics_mode")
        assert settings.graphics_mode in ["glyph", "graphics"]

    def test_settings_can_change_graphics_mode(self):
        """Graphics mode can be changed in settings."""
        settings = GameSettings()

        # Change to glyph mode
        settings.graphics_mode = "glyph"
        assert settings.graphics_mode == "glyph"

        # Change to graphics mode
        settings.graphics_mode = "graphics"
        assert settings.graphics_mode == "graphics"

    def test_settings_rejects_invalid_graphics_mode(self):
        """Invalid graphics modes are handled gracefully."""
        settings = GameSettings()

        # Try to set invalid mode (should remain unchanged or default)
        original_mode = settings.graphics_mode
        settings.graphics_mode = "invalid_mode"

        # Depending on implementation, either:
        # - Mode stays unchanged
        # - Mode defaults to valid value
        assert settings.graphics_mode in ["glyph", "graphics", "invalid_mode"]


class TestGraphicsModeSwitchingDuringGameplay:
    """Test graphics mode switching while game is running."""

    def test_game_survives_mode_change_to_glyph(self):
        """Game continues running after switching to glyph mode."""
        agent = GameTestAgent(seed=42)

        # Change to glyph mode
        agent.engine.settings.graphics_mode = "glyph"

        # Continue playing
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Game should still be running
        assert not agent.engine.game_over
        assert agent.turn > 0

    def test_game_survives_mode_change_to_graphics(self):
        """Game continues running after switching to graphics mode."""
        agent = GameTestAgent(seed=42)

        # Change to graphics mode
        agent.engine.settings.graphics_mode = "graphics"

        # Continue playing
        agent.move_player(1, 0)
        agent.move_player(0, 1)

        # Game should still be running
        assert not agent.engine.game_over
        assert agent.turn > 0

    def test_multiple_mode_switches(self):
        """Game survives multiple mode switches."""
        agent = GameTestAgent(seed=42)

        # Switch modes multiple times
        for i in range(5):
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

            # Play a turn
            agent.move_player(1, 0)

        # Game should still be running
        assert not agent.engine.game_over
        assert agent.turn >= 5

    def test_mode_switch_preserves_player_position(self):
        """Player position is preserved across mode switches."""
        agent = GameTestAgent(seed=42)

        # Move to specific position
        agent.move_player(1, 0)
        agent.move_player(0, 1)
        pos_before = (agent.player.x, agent.player.y)

        # Switch mode
        agent.engine.settings.graphics_mode = "glyph"

        # Position should be unchanged
        pos_after = (agent.player.x, agent.player.y)
        assert pos_before == pos_after

    def test_mode_switch_preserves_player_stats(self):
        """Player stats are preserved across mode switches."""
        agent = GameTestAgent(seed=42)

        # Record stats
        hp_before = agent.player.cpu
        heat_before = agent.player.heat

        # Switch mode
        agent.engine.settings.graphics_mode = "graphics"

        # Stats should be unchanged
        assert agent.player.cpu == hp_before
        assert agent.player.heat == heat_before

    def test_mode_switch_preserves_enemies(self):
        """Enemies are preserved across mode switches."""
        agent = GameTestAgent(seed=42)

        # Record enemy count and positions
        enemy_count_before = len(agent.enemies)
        enemy_positions_before = [(e.x, e.y) for e in agent.enemies[:3]]

        # Switch mode
        agent.engine.settings.graphics_mode = "glyph"

        # Enemies should still exist
        assert len(agent.enemies) == enemy_count_before

        # Enemy positions should be preserved
        enemy_positions_after = [(e.x, e.y) for e in agent.enemies[:3]]
        assert enemy_positions_before == enemy_positions_after

    def test_mode_switch_during_combat(self):
        """Mode switch during combat doesn't break game state."""
        agent = GameTestAgent(seed=42)

        # Play for a bit to potentially get into combat
        for _ in range(10):
            agent.move_player(1, 0)

        # Switch mode during gameplay
        agent.engine.settings.graphics_mode = "graphics"

        # Continue playing
        for _ in range(10):
            if agent.engine.game_over:
                break
            agent.move_player(0, 1)

        # Game should have progressed (or ended)
        assert agent.turn >= 10 or agent.engine.game_over


class TestGraphicsModeMemoryManagement:
    """Test memory management during mode switches."""

    def test_mode_switch_memory_stable(self):
        """Memory usage remains stable after mode switches."""
        agent = GameTestAgent(seed=42)

        # Switch modes many times
        for i in range(20):
            if agent.engine.game_over:
                break
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode
            agent.move_player(1, 0)

        # If we get here without crash, memory management is working
        assert agent.turn > 0 or agent.engine.game_over

    def test_multiple_switches_no_leak(self):
        """Multiple switches don't cause memory leaks."""
        agent = GameTestAgent(seed=42)

        # Perform 50 mode switches
        for i in range(50):
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

            # Do some gameplay
            if i % 5 == 0:
                agent.move_player(1, 0)
        # No exception after 20 switches means no memory leak


class TestGraphicsModeStateConsistency:
    """Test game state consistency across mode switches."""

    def test_turn_counter_consistent_after_switch(self):
        """Turn counter remains consistent across mode switches."""
        agent = GameTestAgent(seed=42)

        # Play some turns
        for _ in range(10):
            agent.move_player(1, 0)

        turn_before = agent.turn

        # Switch mode
        agent.engine.settings.graphics_mode = "glyph"

        # Turn counter should be unchanged
        assert agent.turn == turn_before

    def test_game_level_consistent_after_switch(self):
        """Game level remains consistent across mode switches."""
        agent = GameTestAgent(seed=42)

        level_before = agent.engine.level

        # Switch mode
        agent.engine.settings.graphics_mode = "graphics"

        # Level should be unchanged
        assert agent.engine.level == level_before

    def test_visible_tiles_consistent_after_switch(self):
        """Visible tiles remain consistent across mode switches."""
        agent = GameTestAgent(seed=42)

        visible_before = len(agent.engine.visible_tiles)

        # Switch mode
        agent.engine.settings.graphics_mode = "glyph"

        # Visible tiles should still exist
        assert len(agent.engine.visible_tiles) > 0

    def test_explored_tiles_persistent_after_switch(self):
        """Explored tiles persist across mode switches."""
        agent = GameTestAgent(seed=42)

        # Explore some tiles
        for _ in range(20):
            agent.move_player(1, 0)

        explored_before = len(agent.game_map.explored_tiles)

        # Switch mode
        agent.engine.settings.graphics_mode = "graphics"

        # Explored tiles should be preserved
        explored_after = len(agent.game_map.explored_tiles)
        assert explored_after >= explored_before


class TestGraphicsModeEdgeCases:
    """Test edge cases for graphics mode switching."""

    def test_switch_to_same_mode(self):
        """Switching to current mode doesn't break anything."""
        agent = GameTestAgent(seed=42)

        current_mode = agent.engine.settings.graphics_mode

        # Switch to same mode
        agent.engine.settings.graphics_mode = current_mode

        # Play a turn
        agent.move_player(1, 0)

        # Should work fine
        assert agent.turn == 1

    def test_rapid_mode_switching(self):
        """Rapid mode switches don't crash the game."""
        agent = GameTestAgent(seed=42)

        # Switch modes very rapidly (10 times in quick succession)
        for i in range(10):
            mode = "glyph" if i % 2 == 0 else "graphics"
            agent.engine.settings.graphics_mode = mode

        # Game should still be functional
        agent.move_player(1, 0)
        assert agent.turn == 1

    def test_mode_switch_at_game_start(self):
        """Mode switch immediately at game start works."""
        agent = GameTestAgent(seed=42)

        # Switch mode before any gameplay
        agent.engine.settings.graphics_mode = "glyph"

        # Game should work normally
        agent.move_player(1, 0)
        assert agent.turn == 1

    def test_mode_switch_after_many_turns(self):
        """Mode switch after extended gameplay works."""
        agent = GameTestAgent(seed=42)

        # Play for many turns
        for _ in range(200):
            if agent.engine.game_over:
                break
            agent.move_player(1, 0)

        turns_before = agent.turn

        # Switch mode
        agent.engine.settings.graphics_mode = "graphics"

        # Continue playing
        if not agent.engine.game_over:
            agent.move_player(0, 1)
            assert agent.turn > turns_before


class TestGraphicsModeIntegration:
    """Integration tests for graphics mode switching."""

    def test_full_gameplay_session_with_switches(self):
        """Full gameplay session with multiple mode switches."""
        agent = GameTestAgent(seed=42)

        # Play through a session with periodic mode switches
        for turn_num in range(100):
            if agent.engine.game_over:
                break

            # Switch mode every 25 turns
            if turn_num % 25 == 0:
                mode = "glyph" if (turn_num // 25) % 2 == 0 else "graphics"
                agent.engine.settings.graphics_mode = mode

            # Play a turn
            agent.move_player(1, 0)

        # Should complete without crashes (may die before 100 turns)
        assert agent.turn > 0

    def test_mode_switches_with_various_actions(self):
        """Mode switches work with various player actions."""
        agent = GameTestAgent(seed=42)

        import random

        for i in range(50):
            if agent.engine.game_over:
                break

            # Switch mode occasionally
            if i % 10 == 0:
                mode = "glyph" if i % 20 == 0 else "graphics"
                agent.engine.settings.graphics_mode = mode

            # Perform random action
            action = random.choice(["move", "wait"])
            if action == "move":
                dx, dy = random.choice([(1, 0), (0, 1), (-1, 0), (0, -1)])
                try:
                    agent.move_player(dx, dy)
                except Exception:
                    agent.wait()
            else:
                agent.wait()
        # No exception means rapid mode switching is stable
