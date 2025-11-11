#!/usr/bin/env python3
"""
Dialogue User Preferences Tests - Phase 0

Tests the "Don't show this again" functionality and its interaction
with game systems. This test suite catches the overclock auto-execution bug.

BUG EXPOSED: When overclock warning is disabled, exploits are completely blocked
instead of auto-executing. This is because game_combat.py:145 calls show() which
returns early, but then line 149 always returns False (blocking exploit).
"""

import pytest
import tcod.event
from unittest.mock import Mock

from tests.test_agent import GameTestAgent
from game_config import GameSettings
from game_dialogue_system import (
    DialogueState,
    create_overclock_warning_dialogue
)
from tests.fixtures.simple_fixtures import create_real_enemy


class TestOverclockDialoguePreferences:
    """Test overclock warning dialogue preferences."""

    @pytest.mark.xfail(reason="BUG: Disabled overclock warning blocks exploit instead of auto-executing")
    def test_overclock_warning_disabled_allows_auto_execution(self):
        """BUG TEST: When overclock warning disabled, exploit auto-executes.

        This test SHOULD pass but currently FAILS due to the bug in game_combat.py.

        Expected behavior:
        - User disables overclock warning via settings
        - Player uses exploit that would overheat
        - Exploit executes automatically (no dialogue shown)
        - Overclock damage is applied

        Actual behavior (BUG):
        - Exploit is completely blocked
        - Returns False from execute_exploit()
        - No dialogue shown, no execution
        """
        # Setup game with overclock warning disabled
        agent = GameTestAgent(seed=42)
        agent.engine.settings.dialogue_preferences = {
            "show_overclock_warning": False
        }

        # Setup player near max heat
        agent.player.heat = agent.player.max_heat - 2
        agent.player.inventory_manager.equipped_exploits.append('code_injection')

        # Create target enemy
        enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)
        initial_enemy_cpu = enemy.cpu
        initial_player_cpu = agent.player.cpu
        target_pos = agent.get_position_by_offset(1, 0)

        # Execute exploit that will overheat (bypass targeting mode)
        result = agent.engine.exploit_system.execute_exploit('code_injection', target_pos)

        # SHOULD pass but FAILS: exploit should execute
        assert result is True, "Exploit should execute when warning disabled"
        assert enemy.cpu < initial_enemy_cpu, "Enemy should take damage"
        assert agent.player.heat == agent.player.max_heat, "Heat capped at max"
        assert agent.player.cpu < initial_player_cpu, "Overclock damage applied"
        assert not agent.engine.dialogue_state.is_active(), "No dialogue shown"

    def test_overclock_warning_enabled_shows_dialogue(self):
        """When overclock warning enabled, dialogue shows and blocks."""
        # Setup with warning ENABLED (default)
        agent = GameTestAgent(seed=43)
        # Don't set dialogue_preferences (defaults to enabled)

        agent.player.heat = agent.player.max_heat - 2
        agent.player.inventory_manager.equipped_exploits.append('code_injection')
        enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)
        target_pos = agent.get_position_by_offset(1, 0)

        # Execute exploit (bypass targeting mode)
        result = agent.engine.exploit_system.execute_exploit('code_injection', target_pos)

        # Should block and show dialogue
        assert result is False, "Exploit blocked pending confirmation"
        assert agent.engine.dialogue_state.is_active(), "Dialogue shown"
        assert "OVERCLOCK" in agent.engine.dialogue_state.get_active().title

    def test_overclock_warning_dont_show_again_button_works(self):
        """Pressing 'D' disables warning and executes exploit."""
        agent = GameTestAgent(seed=44)
        agent.player.heat = agent.player.max_heat - 2
        agent.player.inventory_manager.equipped_exploits.append('code_injection')
        enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)
        target_pos = agent.get_position_by_offset(1, 0)

        initial_enemy_cpu = enemy.cpu

        # Execute exploit - dialogue shows
        agent.engine.exploit_system.execute_exploit('code_injection', target_pos)
        assert agent.engine.dialogue_state.is_active()

        # Press 'D' (don't show again)
        event = tcod.event.KeyDown(scancode=0, sym=tcod.event.KeySym.D, mod=tcod.event.Modifier.NONE)
        agent.engine.input_handler.handle_keydown(event)

        # Dialogue should be disabled and exploit executed
        assert agent.engine.settings.dialogue_preferences["show_overclock_warning"] is False
        assert not agent.engine.dialogue_state.is_active()
        assert enemy.cpu < initial_enemy_cpu, "Exploit executed after D press"

    @pytest.mark.xfail(reason="BUG: Disabled overclock warning blocks exploit")
    def test_overclock_warning_disabled_persists_across_turns(self):
        """Once disabled, subsequent overclocks auto-execute."""
        agent = GameTestAgent(seed=45)
        agent.engine.settings.dialogue_preferences = {
            "show_overclock_warning": False
        }

        # Use multiple overheating exploits in a row
        agent.player.heat = agent.player.max_heat - 2
        agent.player.inventory_manager.equipped_exploits.append('code_injection')

        for i in range(3):
            enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y + i)
            target_pos = agent.get_position_by_offset(1, i)
            result = agent.engine.exploit_system.execute_exploit('code_injection', target_pos)

            # All should auto-execute
            assert result is True, f"Exploit {i+1} should auto-execute"
            assert not agent.engine.dialogue_state.is_active()

    def test_overclock_confirmation_flag_resets_after_use(self):
        """Overclock confirmation flag is cleared after exploit executes."""
        agent = GameTestAgent(seed=46)

        agent.player.heat = agent.player.max_heat - 2
        agent.player.inventory_manager.equipped_exploits.append('code_injection')
        enemy = agent.spawn_enemy("bot", agent.player.x + 1, agent.player.y)
        target_pos = agent.get_position_by_offset(1, 0)

        # Execute exploit - dialogue shows
        agent.engine.exploit_system.execute_exploit('code_injection', target_pos)
        assert agent.engine.dialogue_state.is_active()

        # Confirm
        event = tcod.event.KeyDown(scancode=0, sym=tcod.event.KeySym.Y, mod=tcod.event.Modifier.NONE)
        agent.engine.input_handler.handle_keydown(event)

        # Confirmation flag should be cleared
        assert agent.engine.overclock_confirmation is False
        assert agent.engine.overclock_exploit is None


class TestDialoguePreferencePersistence:
    """Test dialogue preferences save/load correctly."""

    def test_disabled_dialogues_persist_after_settings_save(self):
        """Disabled dialogue preferences persist in settings."""
        settings = GameSettings()
        settings.dialogue_preferences = {}

        state = DialogueState(settings)
        state.disable_dialogue("show_overclock_warning")

        # Verify saved
        assert settings.dialogue_preferences["show_overclock_warning"] is False

    def test_multiple_disabled_dialogues_persist(self):
        """Can disable multiple dialogue types independently."""
        settings = GameSettings()
        settings.dialogue_preferences = {}

        state = DialogueState(settings)

        # Disable multiple dialogues
        state.disable_dialogue("show_overclock_warning")
        state.disable_dialogue("show_friendly_fire_warning")

        # Both should be disabled
        assert settings.dialogue_preferences["show_overclock_warning"] is False
        assert settings.dialogue_preferences["show_friendly_fire_warning"] is False

        # Other dialogues should still show (default True)
        dialogue = create_overclock_warning_dialogue("Test", 10, 10, 50, 100)
        assert state.should_show_dialogue(dialogue) is False

    def test_dialogue_preferences_default_to_enabled(self):
        """Dialogues show by default when no preference set."""
        settings = GameSettings()
        settings.dialogue_preferences = {}

        state = DialogueState(settings)

        dialogue = create_overclock_warning_dialogue("Test", 10, 10, 50, 100)
        assert state.should_show_dialogue(dialogue) is True


# Mark as integration tests
pytestmark = pytest.mark.integration
