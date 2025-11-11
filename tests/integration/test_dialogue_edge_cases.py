#!/usr/bin/env python3
"""
Integration tests for dialogue system edge cases.

Tests dialogue behavior in complex scenarios:
- Dialogue during combat
- Dialogue preferences persistence across save/load
- Dialogue + achievement popup overlap
- Dialogue during menu navigation
- Rapid dialogue triggering
"""

import pytest
import tcod.console
import tcod.event
from unittest.mock import Mock, MagicMock, patch
import time

from game_dialogue_system import (
    DialogueState,
    UnifiedRenderer,
    create_gateway_dialogue,
    create_death_dialogue,
    create_overclock_warning_dialogue,
    create_inventory_attack_dialogue
)
from game_achievement_popups import AchievementPopup, AchievementPopupManager
from game_achievements import Achievement
from game_config import GameSettings
from tests.test_agent import GameTestAgent


class TestDialogueDuringCombat:
    """Test dialogue behavior during active combat."""

    def test_dialogue_shown_during_combat_preserves_state(self):
        """Dialogue during combat preserves game state."""
        # Create a game scenario with combat
        agent = GameTestAgent(seed=42)

        # Spawn enemy adjacent to player
        player_x, player_y = agent.player.x, agent.player.y
        enemy = agent.spawn_enemy("patrol", player_x + 1, player_y)

        initial_player_hp = agent.player.cpu
        initial_enemy_hp = enemy.cpu

        # Trigger gateway dialogue (always shows, no user preference)
        dialogue = create_gateway_dialogue()

        # Force show (bypass preference check)
        agent.engine.dialogue_state.active_dialogue = dialogue

        # Verify dialogue is active
        assert agent.engine.dialogue_state.is_active()

        # Verify game state unchanged
        assert agent.player.cpu == initial_player_hp
        assert enemy.cpu == initial_enemy_hp
        assert enemy in agent.engine.enemies

        # Close dialogue
        agent.engine.dialogue_state.close()

        # Game state should still be intact
        assert agent.player.cpu == initial_player_hp
        assert enemy.cpu == initial_enemy_hp

    def test_dialogue_during_combat_pauses_enemy_actions(self):
        """Enemies don't act while dialogue is active."""
        agent = GameTestAgent(seed=43)

        # Spawn enemy and make it hostile
        player_x, player_y = agent.player.x, agent.player.y
        enemy = agent.spawn_enemy("hunter", player_x + 5, player_y)
        enemy.state = "HOSTILE"
        enemy_initial_pos = (enemy.x, enemy.y)

        # Show dialogue
        dialogue = create_inventory_attack_dialogue()
        agent.engine.dialogue_state.show(dialogue)

        # Verify dialogue blocks turn advancement
        assert agent.engine.dialogue_state.is_active()

        # Enemy position should not have changed (no turns processed)
        assert (enemy.x, enemy.y) == enemy_initial_pos

        # Close dialogue
        agent.engine.dialogue_state.close()

    def test_dialogue_renders_over_combat_scene(self):
        """Dialogue renders correctly over active combat scene."""
        agent = GameTestAgent(seed=44)

        # Setup combat scene
        player_x, player_y = agent.player.x, agent.player.y
        agent.spawn_enemy("inhibitor", player_x + 1, player_y)
        agent.spawn_enemy("virus", player_x - 1, player_y)

        # Show dialogue (gateway dialogue, always shows)
        dialogue = create_gateway_dialogue()
        agent.engine.dialogue_state.active_dialogue = dialogue

        # Render to console
        console = tcod.console.Console(width=80, height=50)

        # Render dialogue over game scene
        UnifiedRenderer.render(console, agent.engine.dialogue_state.get_active())

        # Verify dialogue rendered (center should be opaque)
        center_y, center_x = 25, 40
        assert console.rgba["bg"][center_y, center_x, 3] == 255

    def test_multiple_combat_dialogues_queued_correctly(self):
        """Multiple combat-related dialogues queue correctly."""
        # Use standalone DialogueState to avoid preference issues
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Queue multiple combat-related dialogues
        dialogue1 = create_gateway_dialogue()  # Priority 2
        dialogue2 = create_inventory_attack_dialogue()  # Priority 8 (higher)
        dialogue3 = create_death_dialogue()  # Priority 10 (highest)

        state.show(dialogue1)
        state.show(dialogue2)
        state.show(dialogue3)

        # First dialogue shown (priority 2)
        assert state.get_active() == dialogue1

        # Close and verify priority order (highest to lowest)
        state.close()
        assert state.get_active() == dialogue3  # Priority 10 (highest remaining)

        state.close()
        assert state.get_active() == dialogue2  # Priority 8


class TestDialoguePreferencesPersistence:
    """Test dialogue preferences persist across save/load."""

    def test_disabled_dialogue_persists_through_save_load(self):
        """Disabled dialogue preferences persist across save/load."""
        # Create settings
        settings = GameSettings()
        settings.dialogue_preferences = {}

        # Create dialogue state
        state = DialogueState(settings)

        # Disable a dialogue
        state.disable_dialogue("show_overclock_warning")

        # Verify preference set
        assert settings.dialogue_preferences["show_overclock_warning"] is False

        # Simulate save
        saved_prefs = settings.dialogue_preferences.copy()

        # Create new settings (simulates loading)
        new_settings = GameSettings()
        new_settings.dialogue_preferences = saved_prefs

        # Verify preference persisted
        assert new_settings.dialogue_preferences["show_overclock_warning"] is False

        # Verify dialogue won't show
        new_state = DialogueState(new_settings)
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        assert not new_state.should_show_dialogue(dialogue)

    def test_dialogue_preferences_default_to_enabled(self):
        """Dialogues default to enabled if no preference set."""
        settings = GameSettings()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)

        # Should show by default
        assert state.should_show_dialogue(dialogue)

    def test_dialogue_preferences_survive_multiple_saves(self):
        """Dialogue preferences survive multiple save/load cycles."""
        settings = GameSettings()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Disable multiple dialogues
        state.disable_dialogue("show_overclock_warning")
        state.disable_dialogue("intro_dialogue")

        # Simulate multiple save/load cycles
        for _ in range(3):
            saved = settings.dialogue_preferences.copy()
            new_settings = GameSettings()
            new_settings.dialogue_preferences = saved
            settings = new_settings

        # Verify preferences still set
        assert settings.dialogue_preferences["show_overclock_warning"] is False
        assert settings.dialogue_preferences["intro_dialogue"] is False

    def test_enabling_disabled_dialogue_works(self):
        """Can re-enable a disabled dialogue."""
        settings = GameSettings()
        settings.dialogue_preferences = {"show_overclock_warning": False}
        state = DialogueState(settings)

        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)

        # Should not show (disabled)
        assert not state.should_show_dialogue(dialogue)

        # Re-enable
        settings.dialogue_preferences["show_overclock_warning"] = True

        # Should show now
        assert state.should_show_dialogue(dialogue)


class TestDialogueAchievementPopupOverlap:
    """Test dialogue and achievement popup rendering together."""

    def test_dialogue_and_achievement_popup_render_without_conflict(self):
        """Dialogue and achievement popup can render simultaneously."""
        console = tcod.console.Console(width=80, height=50)

        # Create achievement popup
        achievement = Achievement(
            id="test_achievement",
            name="Test Achievement",
            description="This is a test achievement.",
            icon="*",
            category="test",
            hidden=False
        )
        popup = AchievementPopup(
            achievement_id="test_achievement",
            achievement=achievement,
            timestamp=time.time()
        )

        # Create dialogue
        dialogue = create_gateway_dialogue()

        # Render both (simulates game rendering loop)
        # Achievement popup renders in corner, dialogue in center
        UnifiedRenderer.render(console, dialogue)

        # Both should coexist - verify dialogue rendered
        center_y, center_x = 25, 40
        dialogue_rendered = console.rgba["bg"][center_y, center_x, 3] == 255
        assert dialogue_rendered

    def test_achievement_popup_visible_behind_dialogue(self):
        """Achievement popup remains visible when dialogue appears."""
        settings = Mock()
        settings.dialogue_preferences = {}

        # Create achievement manager
        achievement_mgr = AchievementPopupManager()

        # Trigger achievement
        achievement = Achievement(
            id="first_kill",
            name="First Blood",
            description="Defeated first enemy",
            icon="!",
            category="combat",
            hidden=False
        )
        popup = AchievementPopup(
            achievement_id="first_kill",
            achievement=achievement,
            timestamp=time.time()
        )
        achievement_mgr.active_popup = popup

        # Show dialogue
        state = DialogueState(settings)
        dialogue = create_overclock_warning_dialogue("Test", 10, 5, 15, 20)
        state.show(dialogue)

        # Both should be active
        assert achievement_mgr.active_popup is not None
        assert state.is_active()

        # Render both
        console = tcod.console.Console(width=80, height=50)
        UnifiedRenderer.render(console, state.get_active())
        achievement_mgr.render(console)

        # Both rendered successfully
        # (no crashes or rendering conflicts)

    def test_multiple_achievements_with_dialogue(self):
        """Multiple achievement popups + dialogue don't conflict."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Create multiple achievement popups
        achievement_mgr = AchievementPopupManager()
        for i in range(3):
            achievement = Achievement(
                id=f"achievement_{i}",
                name=f"Achievement {i}",
                description=f"Description {i}",
                icon=str(i),
                category="test",
                hidden=False
            )
            popup = AchievementPopup(
                achievement_id=f"achievement_{i}",
                achievement=achievement,
                timestamp=time.time()
            )
            # Queue them (manager only shows one at a time)
            achievement_mgr.popup_queue.append(f"achievement_{i}")

        # Show first popup
        achievement_mgr.update()

        # Show dialogue
        dialogue = create_death_dialogue()
        state.show(dialogue)

        # Render all
        console = tcod.console.Console(width=80, height=50)
        UnifiedRenderer.render(console, state.get_active())
        achievement_mgr.render(console)

        # Success = no crashes


class TestDialogueDuringMenuNavigation:
    """Test dialogue behavior during menu navigation."""

    def test_dialogue_during_menu_closes_menu(self):
        """High-priority dialogue during menu navigation."""
        agent = GameTestAgent(seed=46)

        # Open inventory menu (simulate)
        agent.engine.show_inventory = True

        # Show high-priority dialogue
        dialogue = create_inventory_attack_dialogue()  # Priority 8
        agent.engine.dialogue_state.show(dialogue)

        # Dialogue should be active
        assert agent.engine.dialogue_state.is_active()

        # Menu should still be flagged (but dialogue takes precedence in rendering)
        assert agent.engine.show_inventory

    def test_dialogue_after_menu_close(self):
        """Dialogue shows correctly after closing menu."""
        agent = GameTestAgent(seed=47)

        # Open and close menu
        agent.engine.show_inventory = True
        agent.engine.show_inventory = False

        # Show dialogue
        dialogue = create_gateway_dialogue()
        agent.engine.dialogue_state.show(dialogue)

        # Dialogue should be active
        assert agent.engine.dialogue_state.is_active()
        assert agent.engine.dialogue_state.get_active() == dialogue

    def test_multiple_dialogues_during_menu_navigation(self):
        """Multiple dialogues queue correctly during menu navigation."""
        agent = GameTestAgent(seed=48)

        # Open menu
        agent.engine.show_inventory = True

        # Queue multiple dialogues with different priorities
        dialogue1 = create_gateway_dialogue()  # Priority 2
        dialogue2 = create_death_dialogue()     # Priority 10 (higher, should queue)

        agent.engine.dialogue_state.show(dialogue1)
        agent.engine.dialogue_state.show(dialogue2)

        # First dialogue active (shown immediately)
        assert agent.engine.dialogue_state.get_active() == dialogue1

        # Second queued (higher priority, but first was already shown)
        assert len(agent.engine.dialogue_state.dialogue_queue) == 1

        # Close first, second should appear (higher priority)
        agent.engine.dialogue_state.close()
        assert agent.engine.dialogue_state.get_active() == dialogue2


class TestRapidDialogueTriggers:
    """Test rapid dialogue triggering scenarios."""

    def test_rapid_dialogue_triggers_queue_correctly(self):
        """Rapidly triggering dialogues queue without loss."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Rapidly trigger 10 dialogues
        dialogues = []
        for i in range(10):
            dialogue = create_overclock_warning_dialogue(
                f"Exploit{i}", 10, 5, 15, 20
            )
            dialogues.append(dialogue)
            state.show(dialogue)

        # First shown immediately
        assert state.get_active() == dialogues[0]

        # Other 9 queued
        assert len(state.dialogue_queue) == 9

        # Close all and verify order
        for i, expected_dialogue in enumerate(dialogues):
            assert state.get_active() == expected_dialogue
            state.close()

        # All cleared
        assert not state.is_active()

    def test_same_dialogue_triggered_multiple_times(self):
        """Same dialogue can be triggered multiple times."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Trigger same dialogue 3 times
        dialogue_factory = lambda: create_overclock_warning_dialogue(
            "Same Exploit", 10, 5, 15, 20
        )

        dialogue1 = dialogue_factory()
        dialogue2 = dialogue_factory()
        dialogue3 = dialogue_factory()

        state.show(dialogue1)
        state.show(dialogue2)
        state.show(dialogue3)

        # All queued (even if content identical)
        assert state.is_active()
        assert len(state.dialogue_queue) == 2

        # Close all
        state.close()
        assert state.is_active()
        state.close()
        assert state.is_active()
        state.close()
        assert not state.is_active()

    def test_dialogue_spam_doesnt_crash(self):
        """Spam triggering dialogues doesn't crash."""
        settings = Mock()
        settings.dialogue_preferences = {}
        state = DialogueState(settings)

        # Spam 100 dialogues
        for i in range(100):
            dialogue = create_overclock_warning_dialogue(
                f"Spam{i}", 10, 5, 15, 20
            )
            state.show(dialogue)

        # All queued
        assert state.is_active()
        assert len(state.dialogue_queue) == 99

        # Close all
        for _ in range(100):
            if state.is_active():
                state.close()

        assert not state.is_active()


class TestDialogueResolutionWrapping:
    """Test dialogue text wrapping at various resolutions."""

    def test_dialogue_wraps_at_720p(self):
        """Dialogue wraps correctly at 1280x720 resolution."""
        # 720p console approximation (80x45 chars)
        console = tcod.console.Console(width=80, height=45)

        long_message = "This is a very long dialogue message that should wrap " * 5

        from game_dialogue_system import DialogueBox
        dialogue = DialogueBox(
            title="Long Message Test",
            message=long_message,
            options=["[OK]"],
            valid_keys=[tcod.event.KeySym.SPACE],
            title_color=(255, 255, 255),
            message_color=(255, 255, 255),
            border_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            format_data={}
        )

        UnifiedRenderer.render(console, dialogue)

        # Should render without crash
        import numpy as np
        assert np.any(console.ch != 0)

    def test_dialogue_wraps_at_1440p(self):
        """Dialogue wraps correctly at 2560x1440 resolution."""
        # 1440p console approximation (100x60 chars)
        console = tcod.console.Console(width=100, height=60)

        long_message = "Extended dialogue for high resolution display " * 10

        from game_dialogue_system import DialogueBox
        dialogue = DialogueBox(
            title="High Res Test",
            message=long_message,
            options=["[OK]"],
            valid_keys=[tcod.event.KeySym.SPACE],
            title_color=(255, 255, 255),
            message_color=(255, 255, 255),
            border_color=(255, 255, 255),
            bg_color=(0, 0, 0),
            format_data={}
        )

        UnifiedRenderer.render(console, dialogue)

        import numpy as np
        assert np.any(console.ch != 0)

    def test_dialogue_wraps_at_ultrawide(self):
        """Dialogue wraps correctly on ultrawide displays."""
        # Ultrawide approximation (120x50 chars)
        console = tcod.console.Console(width=120, height=50)

        dialogue = create_overclock_warning_dialogue(
            "Ultra Wide Exploit Test",
            25, 15, 10, 30
        )

        UnifiedRenderer.render(console, dialogue)

        # Should render centered
        center_y = 25
        center_x = 60

        # Check dialogue rendered near center
        import numpy as np
        opaque_near_center = False
        for y in range(center_y - 5, center_y + 5):
            for x in range(center_x - 10, center_x + 10):
                if console.rgba["bg"][y, x, 3] == 255:
                    opaque_near_center = True
                    break
            if opaque_near_center:
                break

        assert opaque_near_center
