"""
Integration tests for achievement popup system.

Tests popup rendering, auto-dismiss, and integration with achievement manager.
"""

import time

import pytest

from rsp.systems.achievement_popups import AchievementPopup, AchievementPopupManager, get_popup_duration
from rsp.systems.achievements import ALL_ACHIEVEMENTS, AchievementManager

# Note: clean_achievement_state and test_console fixtures now available from conftest.py


@pytest.fixture
def popup_manager():
    """Create a fresh popup manager."""
    return AchievementPopupManager()


# ============================================================================
# Popup Manager Tests
# ============================================================================


def test_popup_manager_initialization(popup_manager):
    """Test popup manager starts with no active popup."""
    assert popup_manager.active_popup is None
    assert len(popup_manager.popup_queue) == 0
    assert not popup_manager.has_active_popup()


def test_show_popup(popup_manager):
    """Test showing a popup."""
    popup_manager.show_popup("first_blood")

    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id == "first_blood"
    assert popup_manager.active_popup.achievement.name == "First Blood"


def test_show_invalid_popup(popup_manager):
    """Test showing a popup with invalid achievement ID."""
    popup_manager.show_popup("invalid_achievement_id")

    # Should not create a popup for invalid ID
    assert not popup_manager.has_active_popup()


def test_popup_queue_management(popup_manager):
    """Test popup queue handles multiple popups."""
    popup_manager.popup_queue.extend(["first_blood", "speedrunner", "ghost_protocol"])

    # Update to show first popup
    popup_manager.update()
    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id == "first_blood"
    assert len(popup_manager.popup_queue) == 2

    # Manually dismiss to show next
    popup_manager.dismiss_active_popup()
    popup_manager.update()
    assert popup_manager.active_popup.achievement_id == "speedrunner"
    assert len(popup_manager.popup_queue) == 1

    # Dismiss again
    popup_manager.dismiss_active_popup()
    popup_manager.update()
    assert popup_manager.active_popup.achievement_id == "ghost_protocol"
    assert len(popup_manager.popup_queue) == 0


def test_manual_dismiss(popup_manager):
    """Test manually dismissing a popup."""
    popup_manager.show_popup("first_blood")
    assert popup_manager.has_active_popup()

    popup_manager.dismiss_active_popup()
    assert not popup_manager.has_active_popup()


def test_auto_dismiss(popup_manager):
    """Test popup auto-dismisses after duration."""
    popup_manager.show_popup("first_blood")

    # Simulate time passing
    popup_manager.active_popup.timestamp = time.time() - get_popup_duration() - 0.5

    # Update should dismiss the popup
    popup_manager.update()
    assert not popup_manager.has_active_popup()


def test_popup_rendering_no_crash(popup_manager, test_console):
    """Test that rendering a popup doesn't crash."""
    popup_manager.show_popup("speedrunner")

    # Should not raise an exception
    popup_manager.render(test_console)


def test_render_no_active_popup(popup_manager, test_console):
    """Test rendering when no popup is active."""
    # Should not crash
    popup_manager.render(test_console)


# ============================================================================
# Integration with AchievementManager
# ============================================================================


def test_integration_with_achievement_manager(clean_achievement_state, popup_manager):
    """Test popup manager integrates with achievement manager."""
    # Queue achievements in the manager
    AchievementManager._pending_popups = ["first_blood", "speedrunner"]

    # Update popup manager (should pull from AchievementManager)
    popup_manager.check_and_show_popups()
    popup_manager.update()

    # Should have pulled achievements from manager and shown first one
    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id == "first_blood"
    assert len(popup_manager.popup_queue) == 1  # speedrunner still queued


def test_popup_data_structure():
    """Test AchievementPopup data structure."""
    achievement = ALL_ACHIEVEMENTS["first_blood"]
    popup = AchievementPopup(
        achievement_id="first_blood", achievement=achievement, timestamp=time.time()
    )

    assert popup.achievement_id == "first_blood"
    assert popup.achievement.name == "First Blood"
    assert not popup.should_dismiss()  # Just created


def test_popup_should_dismiss_after_duration():
    """Test popup should_dismiss returns True after duration."""
    achievement = ALL_ACHIEVEMENTS["first_blood"]
    popup = AchievementPopup(
        achievement_id="first_blood",
        achievement=achievement,
        timestamp=time.time() - get_popup_duration() - 1.0,
    )

    assert popup.should_dismiss()


def test_popup_alpha_fade():
    """Test popup alpha calculation for fade effect."""
    achievement = ALL_ACHIEVEMENTS["first_blood"]
    timestamp = time.time()

    popup = AchievementPopup(
        achievement_id="first_blood", achievement=achievement, timestamp=timestamp
    )

    # Just created - should be fading in or fully visible
    alpha = popup.get_alpha()
    assert 0 <= alpha <= 255

    # Simulate mid-display (should be fully visible)
    popup.timestamp = time.time() - 1.5  # Middle of duration
    alpha = popup.get_alpha()
    assert alpha == 255


# ============================================================================
# End-to-End Workflow
# ============================================================================


def test_full_workflow(clean_achievement_state, popup_manager, test_console):
    """Test full workflow: achievement unlock -> popup display -> dismiss."""
    # Step 1: Unlock achievement via manager
    from rsp.systems.metrics import SessionMetrics

    session = SessionMetrics(
        session_id="test", timestamp_start=1000.0, victory=True, turns_taken=85
    )
    session.enemies_killed["virus"] = 1

    # Check achievements (should unlock first_blood and speedrunner)
    newly_unlocked = AchievementManager.check_achievements(session)
    assert "first_blood" in newly_unlocked
    assert "speedrunner" in newly_unlocked

    # Step 2: Popup manager pulls from achievement manager
    popup_manager.check_and_show_popups()
    popup_manager.update()

    # Should show first unlocked achievement
    assert popup_manager.has_active_popup()
    assert popup_manager.active_popup.achievement_id in newly_unlocked

    # Step 3: Render popup (should not crash)
    popup_manager.render(test_console)

    # Step 4: Manually dismiss
    popup_manager.dismiss_active_popup()
    popup_manager.update()

    # Should show next achievement
    assert popup_manager.has_active_popup()

    # Step 5: Dismiss second popup
    popup_manager.dismiss_active_popup()
    assert not popup_manager.has_active_popup()
