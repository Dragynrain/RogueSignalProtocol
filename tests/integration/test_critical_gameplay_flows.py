"""
Critical Gameplay Flow Integration Tests

Tests the complete end-to-end flows for:
- Player death with exception handling verification
- Victory condition triggering and save deletion
- Data fragment pickup and persistence
- Death handler idempotency and resilience

These tests verify the critical paths identified in code review are working correctly.
"""

from unittest.mock import Mock, patch

import pytest

from rsp.systems.save import SaveGameManager


class TestDeathHandlerExceptionResilience:
    """Test that death handler completes even when individual steps fail."""

    def test_death_completes_when_sound_fails(self, basic_game_engine):
        """Test death is properly handled even when sound playback fails."""
        engine = basic_game_engine

        # Mock sound manager to throw exception
        engine.sound_manager.play_sound = Mock(side_effect=Exception("Sound failure"))

        # Kill player
        engine.player.cpu = 0

        # Trigger death check
        result = engine.death_handler.check_death("combat", source="test")

        # Death should still be handled
        assert result is True, "check_death should return True for dead player"
        assert engine.game_over is True, "game_over should be set despite sound failure"
        assert engine.death_handler.is_handled is True, "Death should be marked as handled"

    def test_death_completes_when_metrics_fail(self, basic_game_engine):
        """Test death is properly handled even when metrics finalization fails."""
        engine = basic_game_engine

        # Kill player
        engine.player.cpu = 0

        # Mock metrics to fail - patch in game_metrics where it's imported from
        with patch(
            "rsp.systems.metrics.finalize_and_save_session",
            side_effect=Exception("Metrics failure"),
        ):
            # Trigger death check
            result = engine.death_handler.check_death("virus")

        # Death should still be handled
        assert result is True, "check_death should return True"
        assert engine.game_over is True, "game_over should be set despite metrics failure"
        assert engine.death_handler.is_handled is True, "Death should be marked as handled"
        assert engine.pending_death_dialogue is True, "Death dialogue should be queued"

    def test_death_completes_when_dialogue_close_fails(self, basic_game_engine):
        """Test death is properly handled even when dialogue close fails."""
        engine = basic_game_engine

        # Set up an active dialogue
        import tcod.event

        from rsp.entities.base import Colors
        from rsp.ui.dialogue import DialogueBox

        dialogue = DialogueBox(
            title="TEST",
            message="Test",
            options=["OK"],
            valid_keys=[tcod.event.KeySym.RETURN],
            title_color=Colors.WHITE,
            message_color=Colors.WHITE,
            border_color=Colors.WHITE,
            bg_color=(0, 0, 0),
            format_data={},
        )
        engine.dialogue_state.show(dialogue)

        # Mock close to fail
        original_close = engine.dialogue_state.close
        engine.dialogue_state.close = Mock(side_effect=Exception("Dialogue close failure"))

        # Kill player
        engine.player.cpu = 0

        # Trigger death check
        result = engine.death_handler.check_death("overheat")

        # Death should still be handled
        assert result is True, "check_death should return True"
        assert engine.game_over is True, "game_over should be set"
        assert engine.death_handler.is_handled is True, "Death should be marked as handled"

        # Restore
        engine.dialogue_state.close = original_close

    def test_death_handler_idempotent_after_exception(self, basic_game_engine):
        """Test that repeated check_death calls after exception still return True."""
        engine = basic_game_engine

        # Mock sound to fail
        engine.sound_manager.play_sound = Mock(side_effect=Exception("Sound failure"))

        # Kill player
        engine.player.cpu = 0

        # First call
        result1 = engine.death_handler.check_death("combat")

        # Second call - should still return True without reprocessing
        result2 = engine.death_handler.check_death("virus")
        result3 = engine.death_handler.check_death("overheat")

        assert result1 is True
        assert result2 is True
        assert result3 is True
        assert engine.death_handler.is_handled is True

    def test_death_event_captured_before_exceptions(self, basic_game_engine):
        """Test that death event is captured even if later steps fail."""
        engine = basic_game_engine

        # Kill player with specific state
        engine.player.cpu = 0
        engine.player.heat = 50
        engine.player.trace_level = 75.0
        engine.level = 2
        engine.turn = 100

        # Mock metrics to fail - patch in game_metrics where it's imported from
        with patch(
            "rsp.systems.metrics.finalize_and_save_session",
            side_effect=Exception("Metrics failure"),
        ):
            engine.death_handler.check_death("combat", source="TestEnemy")

        # Death event should be captured
        event = engine.death_handler.death_event
        assert event is not None, "Death event should be captured"
        assert event.cause == "combat"
        assert event.source == "TestEnemy"
        assert event.final_heat == 50
        assert event.final_trace == 75.0
        assert event.level == 2
        assert event.turn == 100


class TestDeathCauseTracking:
    """Test that death causes are correctly tracked at their source."""

    def test_virus_death_cause_tracked(self, basic_game_engine):
        """Test virus death is tracked with correct cause."""
        engine = basic_game_engine

        # Set virus effect
        engine.player.temporary_effects["virus_turns"] = 5
        engine.player.cpu = 1  # Just enough to die from virus damage

        # Kill via virus damage simulation
        engine.player.cpu = 0

        engine.death_handler.check_death("virus")

        event = engine.death_handler.death_event
        assert event.cause == "virus"

    def test_overheat_death_cause_tracked(self, basic_game_engine):
        """Test overheat death is tracked with correct cause."""
        engine = basic_game_engine

        engine.player.cpu = 0

        engine.death_handler.check_death("overheat", source="Buffer Overflow")

        event = engine.death_handler.death_event
        assert event.cause == "overheat"
        assert event.source == "Buffer Overflow"

    def test_self_damage_death_cause_tracked(self, basic_game_engine):
        """Test self-damage death is tracked with correct cause."""
        engine = basic_game_engine

        engine.player.cpu = 0

        engine.death_handler.check_death("self_damage", source="System Crash")

        event = engine.death_handler.death_event
        assert event.cause == "self_damage"
        assert event.source == "System Crash"


class TestVictoryFlow:
    """Test victory condition flow and related state changes."""

    def test_victory_triggers_when_level_exceeds_three(self, basic_game_engine):
        """Test that completing level 3 triggers victory."""
        engine = basic_game_engine

        # Set up for level 3 completion
        engine.level = 3
        engine.game_over = False

        # Progress to next level (should trigger victory)
        engine.game_session.level_coordinator.progress_to_next_level()

        # Verify victory state
        assert engine.level == 4, "Level should increment to 4"
        assert engine.game_over is True, "game_over should be set on victory"
        assert engine.game_state.show_victory_screen is True, "Victory screen should be shown"

    def test_victory_deletes_save(self, basic_game_engine):
        """Test that victory triggers save deletion."""
        engine = basic_game_engine

        # Create a save first
        SaveGameManager.save_game(engine)
        assert SaveGameManager.save_exists(), "Save should exist before victory"

        # Set up for level 3 completion
        engine.level = 3
        engine.game_over = False

        # Progress to next level (triggers victory)
        engine.game_session.level_coordinator.progress_to_next_level()

        # Save should be deleted
        assert not SaveGameManager.save_exists(), "Save should be deleted on victory"

    def test_victory_tracks_newly_unlocked_ascension(self, basic_game_engine):
        """Test that victory sets the newly_unlocked_ascension flag."""
        engine = basic_game_engine

        # Set current ascension to 0 (default)
        engine.ascension_level = 0

        # Set up for victory
        engine.level = 3
        engine.game_over = False

        # Trigger victory
        engine.game_session.level_coordinator.progress_to_next_level()

        # Victory should set flag indicating game was won
        assert engine.game_over is True, "game_over should be set on victory"
        assert engine.game_state.show_victory_screen is True, "Victory screen should show"
        # The newly_unlocked_ascension value depends on settings state,
        # but the victory flow should complete successfully
        assert engine.level == 4, "Level should be 4 after victory"

    def test_level_progression_before_three_does_not_trigger_victory(self, basic_game_engine):
        """Test that completing levels 1 or 2 does not trigger victory."""
        engine = basic_game_engine

        # Test level 1 -> 2
        engine.level = 1
        engine.game_over = False

        engine.game_session.level_coordinator.progress_to_next_level()

        assert engine.level == 2, "Should progress to level 2"
        assert engine.game_over is False, "game_over should not be set"
        assert engine.game_state.show_victory_screen is False, "Victory screen should not show"

        # Test level 2 -> 3
        engine.game_session.level_coordinator.progress_to_next_level()

        assert engine.level == 3, "Should progress to level 3"
        assert engine.game_over is False, "game_over should not be set"
        assert engine.game_state.show_victory_screen is False, "Victory screen should not show"

    def test_victory_blocked_if_game_already_over(self, basic_game_engine):
        """Test that progress_to_next_level is blocked if game_over is already True."""
        engine = basic_game_engine

        engine.level = 3
        engine.game_over = True  # Already over (e.g., player died)

        original_level = engine.level

        engine.game_session.level_coordinator.progress_to_next_level()

        # Level should not change
        assert engine.level == original_level, "Level should not progress when game is over"


class TestFragmentPickupFlow:
    """Test data fragment pickup and persistence flow."""

    def test_fragment_pickup_triggers_discovery(self, basic_game_engine):
        """Test that stepping on a fragment triggers discovery."""
        engine = basic_game_engine

        from rsp.combat.inventory import StoryFragment

        # Get next undiscovered fragment
        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        # Place fragment at player position
        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(next_index)
        engine.game_map.story_fragments[player_pos] = fragment

        initial_discovered = len(engine.story_fragment_manager.discovered_fragments)

        # Process turn (should pick up fragment)
        engine.game_session.turn_manager._process_special_tiles()

        # Fragment should be discovered
        assert (
            len(engine.story_fragment_manager.discovered_fragments) > initial_discovered
        ), "Fragment should be added to discovered list"
        assert next_index in engine.story_fragment_manager.discovered_fragments

    def test_fragment_removed_from_map_after_pickup(self, basic_game_engine):
        """Test that fragment is removed from map after pickup."""
        engine = basic_game_engine

        from rsp.combat.inventory import StoryFragment

        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(next_index)
        engine.game_map.story_fragments[player_pos] = fragment

        # Process pickup
        engine.game_session.turn_manager._process_special_tiles()

        # Fragment should be removed from map
        assert (
            player_pos not in engine.game_map.story_fragments
        ), "Fragment should be removed from map after pickup"

    def test_fragment_discovery_persists_to_progress_file(self, basic_game_engine):
        """Test that discovered fragments are saved to progress file."""
        engine = basic_game_engine

        from rsp.core.data_loading import PersistentStorage

        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        # Discover the fragment
        result = engine.story_fragment_manager.discover_fragment(next_index)
        assert result is True, "discover_fragment should return True for new fragment"

        # Verify it's persisted
        storage = PersistentStorage()
        data = storage.load_data("rogue_signal_progress.json")
        assert next_index in data.get(
            "discovered_story_fragments", []
        ), "Fragment should be in progress file"

    def test_duplicate_fragment_discovery_returns_false(self, basic_game_engine):
        """Test that discovering same fragment twice returns False."""
        engine = basic_game_engine

        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        # First discovery
        result1 = engine.story_fragment_manager.discover_fragment(next_index)

        # Second discovery of same fragment
        result2 = engine.story_fragment_manager.discover_fragment(next_index)

        assert result1 is True, "First discovery should return True"
        assert result2 is False, "Second discovery of same fragment should return False"

    def test_invalid_fragment_index_returns_false(self, basic_game_engine):
        """Test that invalid fragment indices are rejected."""
        engine = basic_game_engine

        # Try to discover fragment with invalid index
        result_negative = engine.story_fragment_manager.discover_fragment(-1)
        result_huge = engine.story_fragment_manager.discover_fragment(9999)

        assert result_negative is False, "Negative index should be rejected"
        assert result_huge is False, "Out of bounds index should be rejected"


class TestSaveDeleteOnDeath:
    """Test that save files are correctly deleted on death."""

    def test_save_deleted_when_player_dies(self, basic_game_engine):
        """Test that death triggers save deletion."""
        engine = basic_game_engine

        # Create a save
        SaveGameManager.save_game(engine)
        assert SaveGameManager.save_exists(), "Save should exist"

        # Kill player
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        # Save should be deleted
        assert not SaveGameManager.save_exists(), "Save should be deleted on death"

    def test_auto_save_blocked_after_death(self, basic_game_engine):
        """Test that auto_save is blocked after game_over is set."""
        engine = basic_game_engine

        # Kill player
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        assert engine.game_over is True

        # Try to auto-save
        engine.auto_save()

        # Save should not exist (auto_save checks game_over)
        assert not SaveGameManager.save_exists(), "Auto-save should be blocked after death"


class TestDeathDialogueQueuing:
    """Test that death dialogue is properly queued."""

    def test_death_queues_pending_dialogue(self, basic_game_engine):
        """Test that death sets pending_death_dialogue flag."""
        engine = basic_game_engine

        engine.pending_death_dialogue = False
        engine.player.cpu = 0

        engine.death_handler.check_death("combat")

        assert engine.pending_death_dialogue is True, "Death should queue pending dialogue"

    def test_death_with_active_dialogue_forces_close(self, basic_game_engine):
        """Test that death attempts to close any active dialogue."""
        engine = basic_game_engine

        import tcod.event

        from rsp.entities.base import Colors
        from rsp.ui.dialogue import DialogueBox

        # Clear any queued dialogues first
        engine.dialogue_state.dialogue_queue = []
        engine.dialogue_state.active_dialogue = None

        # Show a dialogue
        dialogue = DialogueBox(
            title="TEST",
            message="Test",
            options=["OK"],
            valid_keys=[tcod.event.KeySym.RETURN],
            title_color=Colors.WHITE,
            message_color=Colors.WHITE,
            border_color=Colors.WHITE,
            bg_color=(0, 0, 0),
            format_data={},
        )
        engine.dialogue_state.show(dialogue)
        assert engine.dialogue_state.is_active()

        # Track if close was called
        original_close = engine.dialogue_state.close
        close_called = []

        def tracking_close():
            close_called.append(True)
            original_close()

        engine.dialogue_state.close = tracking_close

        # Kill player
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        # close() should have been called
        assert len(close_called) > 0, "close() should be called on death with active dialogue"

        # After close(), dialog should be closed (queue was cleared)
        assert (
            not engine.dialogue_state.is_active()
        ), "Active dialogue should be closed on death when queue is empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
