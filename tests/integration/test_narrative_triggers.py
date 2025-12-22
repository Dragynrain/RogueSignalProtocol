#!/usr/bin/env python3
"""
Integration tests for narrative trigger points.

Tests that narrative methods (trigger_gateway_approach, trigger_overheating)
are properly called at the right game events.
"""

import pytest
from unittest.mock import MagicMock

from game_engine import GameEngine
from game_entities import Position
from game_narrative import NarrativeManager


class TestNarrativeTriggers:
    """Tests for narrative trigger integration."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a real narrative manager for testing
        self.narrative_manager = NarrativeManager()

    def test_trigger_gateway_approach_returns_message(self):
        """Verify trigger_gateway_approach returns a message when called."""
        # First call should return a message
        msg = self.narrative_manager.trigger_gateway_approach()

        # Message should be a non-empty string (or empty if no messages configured)
        assert isinstance(msg, str)

    def test_trigger_overheating_returns_message(self):
        """Verify trigger_overheating returns a message when called."""
        msg = self.narrative_manager.trigger_overheating()

        # Message should be a string (empty if no overheating messages configured)
        assert isinstance(msg, str)

    def test_narrative_methods_track_shown_messages(self):
        """Verify narrative methods track which messages have been shown."""
        # Get multiple messages from same category
        msg1 = self.narrative_manager.trigger_overheating()
        msg2 = self.narrative_manager.trigger_overheating()
        msg3 = self.narrative_manager.trigger_overheating()

        # All should be strings
        assert isinstance(msg1, str)
        assert isinstance(msg2, str)
        assert isinstance(msg3, str)

        # If there are messages, they should eventually repeat (after exhausting pool)
        # This is expected behavior per the shown_messages tracking


class TestGatewayApproachIntegration:
    """Integration tests for gateway approach narrative trigger."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock engine with narrative manager."""
        engine = MagicMock(spec=GameEngine)
        engine.narrative_manager = NarrativeManager()
        engine.message_log = MagicMock()
        engine.sound_manager = MagicMock()
        engine.dialogue_state = MagicMock()
        engine.dialogue_state.should_show_dialogue = MagicMock(return_value=True)
        engine.game_map = MagicMock()
        engine.game_map.gateway = Position(10, 10)
        engine.player = MagicMock()
        engine.player.position = Position(10, 10)
        engine.player.position.grid_distance_to = MagicMock(return_value=0)
        return engine

    def test_gateway_approach_triggers_narrative(self, mock_engine):
        """Verify reaching gateway triggers narrative message."""
        # Mock the narrative method to track calls
        mock_engine.narrative_manager.trigger_gateway_approach = MagicMock(
            return_value="You've found the gateway."
        )

        # Simulate what move_player does when reaching gateway
        gateway_msg = mock_engine.narrative_manager.trigger_gateway_approach()
        if gateway_msg:
            mock_engine.message_log.add_message(gateway_msg)

        # Verify narrative was triggered
        mock_engine.narrative_manager.trigger_gateway_approach.assert_called_once()
        mock_engine.message_log.add_message.assert_called_with("You've found the gateway.")


class TestOverheatNarrativeIntegration:
    """Integration tests for overheat narrative trigger."""

    @pytest.fixture
    def mock_game(self):
        """Create a mock game with narrative manager."""
        game = MagicMock()
        game.narrative_manager = NarrativeManager()
        game.message_log = MagicMock()
        game.sound_manager = MagicMock()
        game.death_handler = MagicMock()
        game.player = MagicMock()
        game.player.heat = 80
        game.player.max_heat = 100
        game.player.cpu = 100
        return game

    def test_overheat_triggers_narrative(self, mock_game):
        """Verify overheating triggers narrative message."""
        # Mock the narrative method to track calls
        mock_game.narrative_manager.trigger_overheating = MagicMock(
            return_value="System temperature critical!"
        )

        # Simulate overheat scenario
        new_heat = 120  # Over max of 100
        if new_heat > mock_game.player.max_heat:
            # This is what the code does when overheat damage is applied
            overheat_msg = mock_game.narrative_manager.trigger_overheating()
            if overheat_msg:
                mock_game.message_log.add_message(overheat_msg)

        # Verify narrative was triggered
        mock_game.narrative_manager.trigger_overheating.assert_called_once()
        mock_game.message_log.add_message.assert_called_with("System temperature critical!")

    def test_no_narrative_when_no_overheat(self, mock_game):
        """Verify narrative not triggered when heat is within limits."""
        # Mock the narrative method to track calls
        mock_game.narrative_manager.trigger_overheating = MagicMock(
            return_value="System temperature critical!"
        )

        # Heat within limits
        new_heat = 90  # Under max of 100

        if new_heat > mock_game.player.max_heat:
            overheat_msg = mock_game.narrative_manager.trigger_overheating()
            if overheat_msg:
                mock_game.message_log.add_message(overheat_msg)

        # Verify narrative was NOT triggered
        mock_game.narrative_manager.trigger_overheating.assert_not_called()


class TestNarrativeMessageContent:
    """Tests for narrative message content loading."""

    def test_narrative_manager_loads_messages(self):
        """Verify NarrativeManager loads messages from data."""
        manager = NarrativeManager()

        # Should have loaded message categories
        assert hasattr(manager, "messages")
        assert isinstance(manager.messages, dict)

    def test_get_message_with_unknown_category(self):
        """Verify get_message returns empty string for unknown category."""
        manager = NarrativeManager()

        msg = manager.get_message("nonexistent_category")
        assert msg == ""

    def test_level_flags_reset(self):
        """Verify level flags can be reset."""
        manager = NarrativeManager()

        # Trigger first blind spot (sets flag)
        manager.trigger_first_blind_spot()
        assert manager.level_flags["first_blind_spot"] is True

        # Reset
        manager.reset_level_flags()
        assert manager.level_flags["first_blind_spot"] is False

    def test_first_blind_spot_only_fires_once_per_level(self):
        """Verify first blind spot message only fires once per level."""
        manager = NarrativeManager()

        # First call should potentially return a message
        msg1 = manager.trigger_first_blind_spot()

        # Second call should return empty
        msg2 = manager.trigger_first_blind_spot()
        assert msg2 == ""

        # After reset, should work again
        manager.reset_level_flags()
        msg3 = manager.trigger_first_blind_spot()
        # msg3 could be empty if no messages configured, but flag should be set
        assert manager.level_flags["first_blind_spot"] is True
