#!/usr/bin/env python3
"""
Unit tests for prologue thought system.

Tests the reactive internal voice system that guides players through
the tutorial via character thoughts triggered by game events.
"""

from unittest.mock import Mock, patch

import pytest

from rsp.systems.prologue_thoughts import (
    THOUGHT_KEYS,
    THOUGHT_TRIGGER_REGISTRY,
    get_trigger_location,
    has_shown_thought,
    reset_prologue_thoughts,
    show_prologue_thought,
    validate_trigger_registry,
)


class TestThoughtKeys:
    """Test thought key definitions."""

    def test_thought_keys_not_empty(self):
        """THOUGHT_KEYS should contain tutorial thought identifiers."""
        assert len(THOUGHT_KEYS) > 0

    def test_thought_keys_are_strings(self):
        """All thought keys should be strings."""
        for key in THOUGHT_KEYS:
            assert isinstance(key, str)

    def test_expected_thought_keys_exist(self):
        """Critical thought keys should be defined."""
        expected_keys = {
            "diagonal_discover",
            "melee_success",
            "turn_based_observe",
            "wait_fail",
            "wait_success",
            "fov_bidirectional",
            "blindspot_observe",
            "blindspot_adjacent_fail",
            "blindspot_range_success",
            "alert_escape_success",
            "exploit_equip_hint",
            "exploit_success",
            "heat_high",
            "gateway_spotted",
        }
        for key in expected_keys:
            assert key in THOUGHT_KEYS, f"Missing thought key: {key}"


class TestShowPrologueThought:
    """Test show_prologue_thought function."""

    def setup_method(self):
        """Reset thought tracking before each test."""
        reset_prologue_thoughts()

    def test_shows_thought_in_prologue_mode(self):
        """Thought is shown when in prologue mode."""
        game = Mock()
        game.prologue_mode = True
        game.message_log = Mock()

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {"melee_success": "Test message"}
            result = show_prologue_thought("melee_success", game)

        assert result is True
        game.message_log.add_message.assert_called_once()

    def test_does_not_show_outside_prologue_mode(self):
        """Thought is not shown when not in prologue mode."""
        game = Mock()
        game.prologue_mode = False

        result = show_prologue_thought("melee_success", game)

        assert result is False

    def test_does_not_show_when_prologue_mode_missing(self):
        """Thought is not shown when prologue_mode attribute missing."""
        game = Mock(spec=[])  # No prologue_mode attribute

        result = show_prologue_thought("melee_success", game)

        assert result is False

    def test_thought_shown_only_once(self):
        """Same thought is not repeated in a session."""
        game = Mock()
        game.prologue_mode = True
        game.message_log = Mock()

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {"melee_success": "Test message"}

            # First call shows thought
            result1 = show_prologue_thought("melee_success", game)
            # Second call does not
            result2 = show_prologue_thought("melee_success", game)

        assert result1 is True
        assert result2 is False
        assert game.message_log.add_message.call_count == 1

    def test_invalid_thought_key_rejected(self):
        """Invalid thought keys return False."""
        game = Mock()
        game.prologue_mode = True

        result = show_prologue_thought("invalid_key_that_does_not_exist", game)

        assert result is False

    def test_missing_thought_message_returns_false(self):
        """Returns False if thought message not in narrative content."""
        game = Mock()
        game.prologue_mode = True

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {}  # Empty - message not found
            result = show_prologue_thought("melee_success", game)

        assert result is False


class TestResetPrologueThoughts:
    """Test reset_prologue_thoughts function."""

    def test_reset_allows_thoughts_to_show_again(self):
        """After reset, previously shown thoughts can be shown again."""
        game = Mock()
        game.prologue_mode = True
        game.message_log = Mock()

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {"melee_success": "Test message"}

            # Show thought first time
            show_prologue_thought("melee_success", game)
            assert has_shown_thought("melee_success") is True

            # Reset
            reset_prologue_thoughts()

            # Should be able to show again
            assert has_shown_thought("melee_success") is False
            result = show_prologue_thought("melee_success", game)
            assert result is True


class TestHasShownThought:
    """Test has_shown_thought function."""

    def setup_method(self):
        """Reset thought tracking before each test."""
        reset_prologue_thoughts()

    def test_returns_false_for_unshown_thought(self):
        """Returns False for thoughts not yet shown."""
        assert has_shown_thought("melee_success") is False

    def test_returns_true_after_thought_shown(self):
        """Returns True after thought has been shown."""
        game = Mock()
        game.prologue_mode = True
        game.message_log = Mock()

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {"melee_success": "Test message"}
            show_prologue_thought("melee_success", game)

        assert has_shown_thought("melee_success") is True


class TestThoughtMessageColors:
    """Test that thoughts use correct message colors."""

    def setup_method(self):
        """Reset thought tracking before each test."""
        reset_prologue_thoughts()

    def test_thought_uses_dimmed_color(self):
        """Thoughts should use DIMMED color for subtle feedback."""
        from rsp.entities.base import Colors

        game = Mock()
        game.prologue_mode = True
        game.message_log = Mock()

        with patch("rsp.core.data_loading.get_prologue_thoughts") as mock_get:
            mock_get.return_value = {"melee_success": "Test message"}
            show_prologue_thought("melee_success", game)

        # Verify DIMMED color was used
        call_args = game.message_log.add_message.call_args
        assert call_args[0][1] == Colors.DIMMED


class TestTriggerRegistry:
    """Test the thought trigger registry for maintenance."""

    def test_registry_covers_all_thought_keys(self):
        """All THOUGHT_KEYS should have entries in THOUGHT_TRIGGER_REGISTRY."""
        result = validate_trigger_registry()
        assert result["missing_registry"] == [], (
            f"THOUGHT_KEYS without registry entries: {result['missing_registry']}"
        )

    def test_registry_has_no_orphan_keys(self):
        """THOUGHT_TRIGGER_REGISTRY should not have keys not in THOUGHT_KEYS."""
        result = validate_trigger_registry()
        assert result["missing_keys"] == [], (
            f"Registry entries without THOUGHT_KEYS: {result['missing_keys']}"
        )

    def test_registry_entries_have_valid_format(self):
        """Registry entries should be (file:function, condition) tuples."""
        for key, entry in THOUGHT_TRIGGER_REGISTRY.items():
            assert isinstance(entry, tuple), f"{key} entry is not a tuple"
            assert len(entry) == 2, f"{key} entry should have 2 elements"
            assert isinstance(entry[0], str), f"{key} location should be string"
            assert isinstance(entry[1], str), f"{key} condition should be string"
            assert ":" in entry[0], f"{key} location should be 'file:function' format"

    def test_get_trigger_location_returns_info(self):
        """get_trigger_location returns info for valid keys."""
        result = get_trigger_location("melee_success")
        assert result is not None
        assert "engine.py" in result[0]

    def test_get_trigger_location_returns_none_for_invalid(self):
        """get_trigger_location returns None for invalid keys."""
        result = get_trigger_location("invalid_key_12345")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
