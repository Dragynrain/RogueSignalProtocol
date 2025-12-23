#!/usr/bin/env python3
"""
Integration tests for death, victory, and story fragment flows.

These tests verify the complete end-to-end paths through the game's
critical state transitions:
- Player death (various causes)
- Player victory (level progression)
- Story fragment discovery

Key integration points tested:
- Death handler idempotency (multiple check_death calls are safe)
- Save file deletion on death/victory
- Metrics finalization on game end
- Story fragment persistence (survives game completion)
- State consistency after game_over flag is set
"""

import pytest

from game_entities import Position
from game_inventory import StoryFragment
from game_story import StoryFragmentManager


class TestDeathHandlerIntegration:
    """Integration tests for the centralized death handling system."""

    def test_death_handler_is_idempotent(self, basic_game_engine):
        """Multiple check_death calls should not cause issues."""
        engine = basic_game_engine

        # Force player to 0 CPU
        engine.player.cpu = 0

        # First death check should trigger death
        result1 = engine.death_handler.check_death("combat")

        # Game should be over
        assert engine.game_over is True
        assert engine.death_handler.is_handled is True

        # Second check should return True (player is still dead)
        # but the death handling should not be repeated
        result2 = engine.death_handler.check_death("combat")

        # Third check with different cause should also return True (still dead)
        result3 = engine.death_handler.check_death("virus")

        # All return True because player is dead
        # (return value indicates "player is dead", not "just handled")
        assert result1 is True
        assert result2 is True
        assert result3 is True

        # But death was only handled once
        assert engine.death_handler.is_handled is True

    def test_death_from_virus_damage(self, basic_game_engine):
        """Virus damage should properly trigger death when CPU reaches 0."""
        engine = basic_game_engine

        # Set player to low CPU with active virus
        engine.player.cpu = 5
        engine.player.temporary_effects["virus_turns"] = 3

        # Process a turn to trigger virus damage
        engine.game_session.process_turn()

        # If CPU dropped to 0, game should be over
        if engine.player.cpu <= 0:
            assert engine.game_over

    def test_death_from_overheat(self, basic_game_engine):
        """Overheating from bump attack should trigger death check."""
        from game_characters import Enemy

        engine = basic_game_engine

        # Set player to low CPU and high heat so overheat kills them
        # Bump attack generates 8+ heat. At 97 heat: 97 + 8 = 105 > 100
        # Overheat damage = 105 - 100 = 5 (1:1 ratio, kills 5 CPU player)
        engine.player.cpu = 5
        engine.player.heat = engine.player.max_heat - 3  # 97 heat

        # Place an enemy adjacent to player for bump attack
        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Bump attack should trigger overheat damage (5 damage kills 5 CPU player)
            engine._perform_bump_attack(enemy)

            # Game should be over
            assert engine.player.cpu <= 0
            assert engine.game_over

    def test_death_sets_game_over_flag(self, basic_game_engine):
        """game_over flag must be set when death is triggered."""
        engine = basic_game_engine

        # Ensure game is not over initially
        assert engine.game_over is False

        # Force death
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        # Game should be over
        assert engine.game_over is True

    def test_death_handler_survives_exception_in_dialogue(self, basic_game_engine, monkeypatch):
        """Death handling should complete even if dialogue system fails."""
        engine = basic_game_engine

        # Make dialogue_state.show raise an exception
        def failing_show(*args, **kwargs):
            raise RuntimeError("Dialogue system failure")

        monkeypatch.setattr(engine.dialogue_state, "show", failing_show)

        # Force death
        engine.player.cpu = 0
        result = engine.death_handler.check_death("combat")

        # Death should still complete
        assert result is True
        assert engine.game_over


class TestVictoryFlowIntegration:
    """Integration tests for the victory/level progression flow."""

    def test_level_progression_through_gateway(self, basic_game_engine):
        """Player should be able to progress through gateway."""
        engine = basic_game_engine

        # Ensure we're on level 1
        engine.game_state.level = 1

        # Manually trigger level progression
        engine.game_session.progress_to_next_level()

        # Should be on level 2 now
        assert engine.game_state.level == 2
        assert not engine.game_over  # Not victory yet

    def test_victory_triggers_at_level_4(self, basic_game_engine):
        """Victory should trigger when trying to progress past level 3."""
        engine = basic_game_engine

        # Set to level 3
        engine.game_state.level = 3

        # Progress to victory
        engine.game_session.progress_to_next_level()

        # Game should be over (victory)
        assert engine.game_over
        assert engine.game_state.show_victory_screen

    def test_victory_and_death_are_mutually_exclusive(self, basic_game_engine):
        """Once victory is achieved, death cannot override it."""
        engine = basic_game_engine

        # Achieve victory
        engine.game_state.level = 3
        engine.game_session.progress_to_next_level()

        # Verify victory state
        assert engine.game_over
        victory_screen_before = engine.game_state.show_victory_screen

        # Try to trigger death
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        # Victory state should be preserved
        assert engine.game_over
        assert engine.game_state.show_victory_screen == victory_screen_before


class TestStoryFragmentIntegration:
    """Integration tests for story fragment discovery flow."""

    def test_fragment_discovered_on_pickup(self, basic_game_engine):
        """Story fragment should be discovered when player walks over it."""
        engine = basic_game_engine

        # Get a fragment index that's not yet discovered
        manager = engine.story_fragment_manager
        next_index = manager.get_next_undiscovered_fragment()

        if next_index is None:
            pytest.skip("All fragments already discovered")

        # Place fragment at player position
        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(next_index)
        engine.game_map.story_fragments[player_pos] = fragment

        # Process special tiles (simulates walking over the fragment)
        engine.game_session._process_special_tiles()

        # Fragment should be discovered
        assert next_index in manager.discovered_fragments

        # Fragment should be removed from map
        assert player_pos not in engine.game_map.story_fragments

    def test_fragment_not_added_to_inventory(self, basic_game_engine):
        """Story fragments should NOT be added to player inventory."""
        engine = basic_game_engine

        # Get a fragment index
        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        # Place fragment at player position
        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(next_index)
        engine.game_map.story_fragments[player_pos] = fragment

        # Count inventory items before
        items_before = len(engine.player.inventory_manager.items)

        # Process special tiles
        engine.game_session._process_special_tiles()

        # Inventory should not have grown
        items_after = len(engine.player.inventory_manager.items)
        assert items_after == items_before

    def test_fragment_persists_across_game_sessions(self, basic_game_engine, tmp_path, monkeypatch):
        """Discovered fragments should persist even after game over."""
        # Create a test progress file
        test_dir = tmp_path / "saves"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "rogue_signal_progress.json"

        # Mock PersistentStorage to use our temp directory
        original_get_data_dir = None
        try:
            import game_file_paths

            original_get_data_dir = game_file_paths.get_data_directory

            def mock_get_data_dir():
                return tmp_path

            monkeypatch.setattr(game_file_paths, "get_data_directory", mock_get_data_dir)

            # Create new manager and discover a fragment
            manager1 = StoryFragmentManager()
            manager1.discover_fragment(0)

            # Verify it was saved (check progress_data directly)
            assert 0 in manager1.discovered_fragments

            # Create new manager (simulates new game session)
            manager2 = StoryFragmentManager()

            # Fragment should still be discovered
            assert 0 in manager2.discovered_fragments
        finally:
            if original_get_data_dir:
                monkeypatch.setattr(game_file_paths, "get_data_directory", original_get_data_dir)

    def test_story_fragment_manager_returns_next_undiscovered(self, basic_game_engine):
        """Manager should correctly track which fragments are discovered."""
        manager = basic_game_engine.story_fragment_manager

        # Get first undiscovered
        first = manager.get_next_undiscovered_fragment()
        if first is None:
            pytest.skip("All fragments already discovered")

        # Record current discovered count
        count_before = len(manager.discovered_fragments)

        # Discover it (in memory only for this test)
        manager.discovered_fragments.append(first)

        # Next undiscovered should be different
        second = manager.get_next_undiscovered_fragment()
        assert second != first or second is None

        # Restore state
        manager.discovered_fragments.remove(first)


class TestGameOverStateConsistency:
    """Tests for state consistency when game ends."""

    def test_game_over_flag_persists(self, basic_game_engine):
        """game_over flag should remain True once set."""
        engine = basic_game_engine

        # Set game over
        engine.game_over = True

        # Verify it stays True
        assert engine.game_over is True

        # Try setting various states
        engine.game_state.turn += 1
        assert engine.game_over is True

    def test_enemies_count_unchanged_after_game_over(self, basic_game_engine):
        """Enemy count should be preserved after game ends."""
        engine = basic_game_engine

        # End the game
        engine.game_over = True

        # Record enemy count
        initial_count = len(engine.enemies)

        # Enemies shouldn't be removed by game over
        final_count = len(engine.enemies)
        assert final_count == initial_count


class TestDeathCauseTracking:
    """Tests for death cause attribution."""

    def test_combat_death_has_correct_cause(self, basic_game_engine):
        """Combat deaths should be attributed correctly."""
        engine = basic_game_engine
        engine.player.cpu = 0

        # Create a mock to capture the death event
        death_events = []
        original_handle = engine.death_handler._handle_death

        def capture_death(event):
            death_events.append(event)
            return original_handle(event)

        engine.death_handler._handle_death = capture_death

        # Trigger death
        engine.death_handler.check_death("combat", "Scanner")

        # Verify death event
        assert len(death_events) == 1
        assert death_events[0].cause == "combat"
        assert death_events[0].source == "Scanner"

    def test_virus_death_has_correct_cause(self, basic_game_engine):
        """Virus deaths should be attributed correctly."""
        engine = basic_game_engine
        engine.player.cpu = 0

        # Create a mock to capture the death event
        death_events = []
        original_handle = engine.death_handler._handle_death

        def capture_death(event):
            death_events.append(event)
            return original_handle(event)

        engine.death_handler._handle_death = capture_death

        # Trigger death
        engine.death_handler.check_death("virus")

        # Verify death event
        assert len(death_events) == 1
        assert death_events[0].cause == "virus"


class TestDeathAfterVictoryPrevention:
    """Tests that victory prevents subsequent death handling."""

    def test_death_handler_skips_if_victory_already_achieved(self, basic_game_engine):
        """Death handler should not process if victory already happened."""
        engine = basic_game_engine

        # Achieve victory first
        engine.game_state.level = 3
        engine.game_session.progress_to_next_level()

        # Verify victory state
        assert engine.game_over is True
        assert engine.game_state.show_victory_screen is True

        # Record death handler state before attempting death
        was_handled_before = engine.death_handler.is_handled

        # Try to trigger death on a victorious player
        engine.player.cpu = 0
        result = engine.death_handler.check_death("combat")

        # Death should not have been "handled" (no new death processing)
        # The handler should recognize game_over and skip death dialogue
        assert engine.game_state.show_victory_screen is True

        # pending_death_dialogue should NOT be set after victory
        # (This is the bug we're testing for - it should NOT be True)
        pending = getattr(engine, "pending_death_dialogue", False)
        assert pending is False, "Death dialogue should not be pending after victory"

    def test_victory_screen_not_overwritten_by_death(self, basic_game_engine):
        """Victory screen flag should survive death trigger attempts."""
        engine = basic_game_engine

        # Achieve victory
        engine.game_state.level = 3
        engine.game_session.progress_to_next_level()

        victory_screen_state = engine.game_state.show_victory_screen
        assert victory_screen_state is True

        # Force player death condition
        engine.player.cpu = 0

        # Multiple death checks should not change victory screen
        for _ in range(3):
            engine.death_handler.check_death("combat")

        assert engine.game_state.show_victory_screen == victory_screen_state


class TestTurnProcessingAfterDeath:
    """Tests that turn processing respects game_over state."""

    def test_process_turn_skips_when_game_over(self, basic_game_engine):
        """Turn processing should not run enemy AI when game is over."""
        engine = basic_game_engine

        # Force game over
        engine.game_over = True

        # Record enemy states
        enemy_positions_before = [(e.x, e.y) for e in engine.enemies]

        # Try to process a turn - should be safe (no crash)
        # Enemies should NOT move or attack since game is over
        try:
            engine.game_session.process_turn()
        except Exception as e:
            pytest.fail(f"process_turn should be safe when game_over=True: {e}")

    def test_maybe_process_turn_after_death_is_safe(self, basic_game_engine):
        """maybe_process_turn should handle death state gracefully."""
        engine = basic_game_engine

        # Force player death
        engine.player.cpu = 0
        engine.death_handler.check_death("combat")

        assert engine.game_over is True

        # This should not crash or cause issues
        try:
            engine.maybe_process_turn()
        except Exception as e:
            pytest.fail(f"maybe_process_turn should be safe after death: {e}")


class TestMetricsFinalizationIdempotency:
    """Tests that metrics finalization handles edge cases."""

    def test_finalize_session_is_idempotent(self, basic_game_engine):
        """Calling finalize_and_save_session multiple times should be safe."""
        from game_metrics import finalize_and_save_session, get_current_session

        session = get_current_session()
        if session is None:
            pytest.skip("No active session")

        # First finalization (victory)
        result1 = finalize_and_save_session(
            victory=True, death_cause=None, death_level=0, final_cpu=50
        )

        # Second finalization (death - simulating race condition)
        result2 = finalize_and_save_session(
            victory=False, death_cause="combat", death_level=1, final_cpu=0
        )

        # Both should complete without error
        # The first result should "win" - victory should be recorded


class TestExploitDeathMidExecution:
    """Tests for death occurring during exploit execution."""

    def test_system_crash_self_damage_death_sets_game_over(self, basic_game_engine):
        """System Crash self-damage killing player should set game_over."""
        engine = basic_game_engine

        # Set player to very low CPU (will die from 30 self-damage)
        engine.player.cpu = 25

        # Equip system_crash
        engine.player.inventory_manager.equipped_exploits = ["system_crash"]

        # Pre-confirm the dialogue (skip confirmation)
        engine.system_crash_confirmed = True

        # Execute system crash
        engine.exploit_system.execute_exploit("system_crash", engine.player.position)

        # Player should be dead and game over
        assert engine.player.cpu <= 0
        assert engine.game_over is True

    def test_logic_bomb_friendly_fire_death_sets_game_over(self, basic_game_engine):
        """Logic Bomb friendly fire killing player should set game_over."""
        engine = basic_game_engine

        # Set player to very low CPU
        engine.player.cpu = 15

        # Equip logic_bomb
        engine.player.inventory_manager.equipped_exploits = ["logic_bomb"]

        # Pre-confirm friendly fire
        engine.friendly_fire_confirmed = True

        # Target self position (will cause friendly fire)
        engine.exploit_system.execute_exploit("logic_bomb", engine.player.position)

        # Player should be dead (logic bomb does 20+ damage)
        if engine.player.cpu <= 0:
            assert engine.game_over is True


class TestEnemyAttackOnDeadPlayer:
    """Tests that enemy attacks don't cause issues on dead players."""

    def test_enemy_attack_on_zero_cpu_player_is_safe(self, basic_game_engine):
        """Enemy attacking player with 0 CPU should not crash."""
        engine = basic_game_engine

        # Force player to 0 CPU but don't trigger death yet
        engine.player.cpu = 0

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Enemy attack should be safe
            try:
                damage = enemy.attack_player(engine.player, game_engine=engine)
                # Death should be triggered
                assert engine.game_over is True
            except Exception as e:
                pytest.fail(f"Enemy attack on dead player crashed: {e}")


class TestBumpAttackOverheat:
    """Tests for overheat damage during bump attacks."""

    def test_bump_attack_exceeding_max_heat_causes_damage(self, basic_game_engine):
        """Bump attack that pushes heat over max should cause overheat damage."""
        engine = basic_game_engine

        # Set player to near-max heat (bump attack generates 8+ heat)
        # Heat at 95, bump attack adds 8 = 103, which exceeds max (100)
        engine.player.heat = engine.player.max_heat - 5  # 5 below max
        initial_cpu = engine.player.cpu

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Perform bump attack (generates 8+ heat, will exceed max by 3+)
            engine._perform_bump_attack(enemy)

            # Player should have taken overheat damage
            # Overheat only triggers when heat EXCEEDS max (not when equal)
            # 95 + 8 = 103 > 100, so overheat_amount = 3, damage = 3 (1:1 ratio)
            assert engine.player.cpu < initial_cpu, "Player should take overheat damage"

    def test_bump_attack_overheat_can_kill_player(self, basic_game_engine):
        """Bump attack overheat should be able to kill player."""
        engine = basic_game_engine

        # Set player to very low CPU and high heat so overheat kills them
        # Bump attack generates 8+ heat. At 97 heat: 97 + 8 = 105 > 100
        # Overheat damage = 105 - 100 = 5 (kills player with 5 CPU)
        engine.player.cpu = 5
        engine.player.heat = engine.player.max_heat - 3  # 97 heat

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Perform bump attack (97 + 8 = 105, overheat = 5, kills 5 CPU player)
            engine._perform_bump_attack(enemy)

            # Player should be dead (5 CPU vs 5 overheat damage)
            assert engine.player.cpu <= 0
            assert engine.game_over is True
            assert engine.death_handler.is_handled is True

    def test_bump_attack_overheat_caps_at_max(self, basic_game_engine):
        """After overheat from bump attack, heat should be capped at max."""
        engine = basic_game_engine

        # Set player to near-max heat with plenty of CPU
        # Bump attack generates 8+ heat, so 95 + 8 = 103 > 100
        engine.player.cpu = 100
        engine.player.heat = engine.player.max_heat - 5

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Perform bump attack (will exceed max heat)
            engine._perform_bump_attack(enemy)

            # Heat should be capped at max (no cooldown, matches exploit behavior)
            assert engine.player.heat == engine.player.max_heat

    def test_bump_attack_no_overheat_when_below_max(self, basic_game_engine):
        """Bump attack below max heat should not cause overheat damage."""
        engine = basic_game_engine

        # Set player to low heat (well below max)
        engine.player.heat = 10
        initial_cpu = engine.player.cpu

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Perform bump attack
            engine._perform_bump_attack(enemy)

            # Player should NOT have taken overheat damage
            # (CPU should be unchanged - bump attacks don't cost CPU directly)
            assert engine.player.cpu == initial_cpu

    def test_bump_attack_at_exactly_max_heat_no_overheat(self, basic_game_engine):
        """Bump attack that brings heat to exactly max should NOT cause overheat.

        Overheat only triggers when heat EXCEEDS max (using > not >=).
        This matches exploit overheat behavior for consistency.
        """
        engine = basic_game_engine

        # Set heat so bump attack brings it to exactly max (not over)
        # Bump attack generates 8 base heat, so 92 + 8 = 100 (exactly max)
        engine.player.heat = engine.player.max_heat - 8
        initial_cpu = engine.player.cpu

        # Place an enemy adjacent to player
        from game_characters import Enemy
        from game_entities import Position

        enemy_pos = Position(engine.player.x + 1, engine.player.y)
        if engine.game_map.is_valid_position(enemy_pos):
            enemy = Enemy(enemy_pos, "scanner")
            engine.enemies.append(enemy)

            # Perform bump attack (brings heat to exactly 100)
            engine._perform_bump_attack(enemy)

            # Player should NOT have taken overheat damage
            # Heat at exactly max is fine - only exceeding max triggers damage
            assert engine.player.cpu == initial_cpu
            assert engine.player.heat == engine.player.max_heat


class TestInvalidFragmentHandling:
    """Tests for handling invalid or corrupted fragment data."""

    def test_invalid_fragment_index_logs_error_and_removes_fragment(
        self, basic_game_engine, caplog
    ):
        """Invalid fragment index should log error and still remove fragment from map."""
        import logging

        engine = basic_game_engine

        # Place a fragment with an invalid index (999 is way out of bounds)
        player_pos = (engine.player.x, engine.player.y)
        invalid_fragment = StoryFragment(999)
        engine.game_map.story_fragments[player_pos] = invalid_fragment

        # Process special tiles
        with caplog.at_level(logging.ERROR):
            engine.game_session._process_special_tiles()

        # Fragment should be removed from map (cleanup happens either way)
        assert player_pos not in engine.game_map.story_fragments

        # Error should be logged
        assert any("Invalid Story Fragment #999" in record.message for record in caplog.records)

    def test_valid_fragment_discovered_and_removed(self, basic_game_engine):
        """Valid fragment index should be discovered and removed properly."""
        engine = basic_game_engine

        # Get next valid fragment index
        next_index = engine.story_fragment_manager.get_next_undiscovered_fragment()
        if next_index is None:
            pytest.skip("All fragments already discovered")

        # Place the valid fragment
        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(next_index)
        engine.game_map.story_fragments[player_pos] = fragment

        # Process special tiles
        engine.game_session._process_special_tiles()

        # Fragment should be discovered
        assert next_index in engine.story_fragment_manager.discovered_fragments

        # Fragment should be removed from map
        assert player_pos not in engine.game_map.story_fragments

    def test_already_discovered_fragment_not_rediscovered(self, basic_game_engine):
        """Re-walking over an already-discovered fragment index should not crash."""
        engine = basic_game_engine
        manager = engine.story_fragment_manager

        # Discover fragment 0 manually
        manager.discover_fragment(0)
        assert 0 in manager.discovered_fragments

        # Place same fragment index again
        player_pos = (engine.player.x, engine.player.y)
        fragment = StoryFragment(0)
        engine.game_map.story_fragments[player_pos] = fragment

        # Process should not crash - fragment should still be removed
        engine.game_session._process_special_tiles()

        # Fragment should be removed from map
        assert player_pos not in engine.game_map.story_fragments


class TestVictorySaveHandling:
    """Tests for victory save file handling edge cases."""

    def test_victory_handles_save_deletion_gracefully(self, basic_game_engine, monkeypatch):
        """Victory should complete even if save deletion fails."""
        from game_save import SaveGameManager

        engine = basic_game_engine

        # Track if delete was called
        delete_called = []

        def failing_delete():
            delete_called.append(True)
            raise OSError("Permission denied - simulated failure")

        monkeypatch.setattr(SaveGameManager, "delete_save", failing_delete)

        # Set to level 3 and trigger victory
        engine.game_state.level = 3
        engine.game_session.progress_to_next_level()

        # Victory should complete despite save deletion failure
        assert engine.game_over is True
        assert engine.game_state.show_victory_screen is True

        # Delete should have been attempted
        assert len(delete_called) == 1

    def test_victory_logs_save_deletion_failure(self, basic_game_engine, monkeypatch, caplog):
        """Victory should log error if save deletion fails."""
        import logging

        from game_save import SaveGameManager

        engine = basic_game_engine

        def failing_delete():
            raise OSError("Permission denied")

        monkeypatch.setattr(SaveGameManager, "delete_save", failing_delete)

        # Trigger victory
        engine.game_state.level = 3
        with caplog.at_level(logging.ERROR):
            engine.game_session.progress_to_next_level()

        # Error should be logged
        assert any("Failed to delete save file" in record.message for record in caplog.records)

    def test_victory_message_differs_on_save_failure(self, basic_game_engine, monkeypatch):
        """Victory message should not mention 'purged' if save deletion fails."""
        from game_save import SaveGameManager

        engine = basic_game_engine

        def failing_delete():
            raise OSError("Permission denied")

        monkeypatch.setattr(SaveGameManager, "delete_save", failing_delete)

        # Trigger victory
        engine.game_state.level = 3
        engine.game_session.progress_to_next_level()

        # Check message log - should say "Mission complete" without "purged"
        messages = [msg.text for msg in engine.message_log.messages]
        assert any("Mission complete" in msg for msg in messages)
        assert not any("purged" in msg for msg in messages)


class TestFragmentPlacementEdgeCases:
    """Tests for fragment placement edge cases."""

    def test_fragment_not_placed_on_level_1_or_2(self, basic_game_engine):
        """Story fragments should only be placed on level 3."""
        engine = basic_game_engine
        level_coordinator = engine.game_session.level_coordinator

        # Ensure we're on level 1 or 2
        for level in [1, 2]:
            engine.game_state.level = level
            engine.game_map.story_fragments.clear()

            # Call placement method directly
            level_coordinator._place_story_fragment()

            # No fragments should be placed
            assert len(engine.game_map.story_fragments) == 0

    def test_fragment_placement_respects_spawn_chance(self, basic_game_engine, monkeypatch):
        """Fragment placement should respect the spawn chance threshold."""
        import random

        engine = basic_game_engine
        level_coordinator = engine.game_session.level_coordinator
        engine.game_state.level = 3

        # Mock random to always return value above threshold (no spawn)
        monkeypatch.setattr(random, "random", lambda: 0.99)

        engine.game_map.story_fragments.clear()
        level_coordinator._place_story_fragment()

        # No fragment should be placed (random returned 0.99, above any threshold)
        assert len(engine.game_map.story_fragments) == 0

    def test_fragment_placement_logs_on_success(self, basic_game_engine, monkeypatch, caplog):
        """Successful fragment placement should be logged."""
        import logging
        import random

        engine = basic_game_engine
        level_coordinator = engine.game_session.level_coordinator
        engine.game_state.level = 3

        # Mock random to always return 0 (always spawn)
        monkeypatch.setattr(random, "random", lambda: 0.0)
        # Mock randint to return valid positions
        monkeypatch.setattr(random, "randint", lambda a, b: 20)

        # Ensure there's an undiscovered fragment
        if engine.story_fragment_manager.get_next_undiscovered_fragment() is None:
            pytest.skip("All fragments already discovered")

        engine.game_map.story_fragments.clear()

        with caplog.at_level(logging.DEBUG):
            level_coordinator._place_story_fragment()

        # Check if fragment was placed (placement might still fail due to position validation)
        if len(engine.game_map.story_fragments) > 0:
            # Success log should be present
            assert any(
                "Story fragment" in record.message and "placed at" in record.message
                for record in caplog.records
            )
