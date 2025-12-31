"""
Unit tests for achievement progress tracking.

Tests the AchievementManager.get_achievement_progress() method that provides
progress towards achievements for display in the achievements UI.
"""

import pytest

from rsp.systems.achievements import (
    BLIND_SPOT_AMBUSHES_THRESHOLD,
    CROWD_CONTROL_AOE_THRESHOLD,
    EFFICIENT_KILLER_TURNS_THRESHOLD,
    ENEMY_DATABASE_UNIQUE_THRESHOLD,
    EXPLORER_NODES_THRESHOLD,
    LEGENDARY_VICTORIES_THRESHOLD,
    MASSACRE_KILLS_THRESHOLD,
    OVERKILL_DAMAGE_THRESHOLD,
    PERSISTENT_VICTORIES_THRESHOLD,
    SILENT_ASSASSIN_STREAK_THRESHOLD,
    SURVIVOR_TURNS_THRESHOLD,
    TOTAL_CODE_HACK_TYPES,
    TOTAL_EXPLOITS,
    VETERAN_GAMES_THRESHOLD,
    AchievementManager,
)
from rsp.systems.metrics import LifetimeMetrics, SessionMetrics


@pytest.fixture
def fresh_achievements():
    """Reset achievement manager state before each test."""
    AchievementManager._unlocked_achievements = set()
    AchievementManager._pending_popups = []
    yield
    AchievementManager._unlocked_achievements = set()
    AchievementManager._pending_popups = []


@pytest.fixture
def sample_session():
    """Create a sample session with some progress."""
    session = SessionMetrics(session_id="test", timestamp_start=0.0)
    return session


@pytest.fixture
def sample_lifetime():
    """Create a sample lifetime metrics."""
    return LifetimeMetrics()


class TestCombatAchievementProgress:
    """Tests for combat achievement progress tracking."""

    def test_massacre_progress_with_kills(self, fresh_achievements, sample_session):
        """Massacre progress shows kills vs threshold."""
        sample_session.enemies_killed["scanner"] = 8
        sample_session.enemies_killed["virus"] = 4
        # Total = 12

        progress = AchievementManager.get_achievement_progress("massacre", sample_session)
        assert progress == (12, MASSACRE_KILLS_THRESHOLD)

    def test_massacre_progress_no_kills(self, fresh_achievements, sample_session):
        """Massacre progress shows 0 when no kills."""
        progress = AchievementManager.get_achievement_progress("massacre", sample_session)
        assert progress == (0, MASSACRE_KILLS_THRESHOLD)

    def test_overkill_progress(self, fresh_achievements, sample_session):
        """Overkill progress shows max damage vs threshold."""
        sample_session.max_single_hit_damage = 35

        progress = AchievementManager.get_achievement_progress("overkill", sample_session)
        assert progress == (35, OVERKILL_DAMAGE_THRESHOLD)

    def test_crowd_control_progress(self, fresh_achievements, sample_session):
        """Crowd control progress shows max AOE hits vs threshold."""
        sample_session.aoe_multi_kills[3] = 2  # Hit 3 enemies twice
        sample_session.aoe_multi_kills[4] = 1  # Hit 4 enemies once

        progress = AchievementManager.get_achievement_progress("crowd_control", sample_session)
        assert progress == (4, CROWD_CONTROL_AOE_THRESHOLD)

    def test_efficient_killer_progress(self, fresh_achievements, sample_session):
        """Efficient killer progress shows turns with kills vs threshold."""
        sample_session.turns_with_kills = 3

        progress = AchievementManager.get_achievement_progress("efficient_killer", sample_session)
        assert progress == (3, EFFICIENT_KILLER_TURNS_THRESHOLD)

    def test_efficient_killer_progress_no_kills(self, fresh_achievements, sample_session):
        """Efficient killer shows 0 progress when no turns with kills."""
        progress = AchievementManager.get_achievement_progress("efficient_killer", sample_session)
        assert progress == (0, EFFICIENT_KILLER_TURNS_THRESHOLD)


class TestStealthAchievementProgress:
    """Tests for stealth achievement progress tracking."""

    def test_silent_assassin_progress(self, fresh_achievements, sample_session):
        """Silent assassin progress shows stealth streak vs threshold."""
        sample_session.max_stealth_streak = 7

        progress = AchievementManager.get_achievement_progress("silent_assassin", sample_session)
        assert progress == (7, SILENT_ASSASSIN_STREAK_THRESHOLD)

    def test_blind_spot_master_progress(self, fresh_achievements, sample_session):
        """Blind spot master progress shows ambushes vs threshold."""
        sample_session.ambushes_from_blind_spots = 3

        progress = AchievementManager.get_achievement_progress("blind_spot_master", sample_session)
        assert progress == (3, BLIND_SPOT_AMBUSHES_THRESHOLD)


class TestMasteryAchievementProgress:
    """Tests for mastery achievement progress tracking."""

    def test_master_hacker_progress(self, fresh_achievements, sample_session):
        """Master hacker progress shows unique exploits used vs total."""
        sample_session.unique_exploits_used_this_run = {"code_injection", "system_hop", "decoy"}

        progress = AchievementManager.get_achievement_progress("master_hacker", sample_session)
        assert progress == (3, TOTAL_EXPLOITS)

    def test_code_collector_progress(self, fresh_achievements, sample_session):
        """Code collector progress shows unique code hacks vs total types."""
        sample_session.unique_code_hacks_used_this_run = {"Azure Code", "Crimson Code"}

        progress = AchievementManager.get_achievement_progress("code_collector", sample_session)
        assert progress == (2, TOTAL_CODE_HACK_TYPES)

    def test_enemy_database_progress(self, fresh_achievements, sample_session):
        """Enemy database progress shows unique enemies encountered."""
        sample_session.unique_enemies_encountered = {"scanner", "virus", "firewall"}

        progress = AchievementManager.get_achievement_progress("enemy_database", sample_session)
        assert progress == (3, ENEMY_DATABASE_UNIQUE_THRESHOLD)

    def test_explorer_progress(self, fresh_achievements, sample_session):
        """Explorer progress shows special nodes discovered."""
        sample_session.special_nodes_discovered = {"upgrade", "gateway"}

        progress = AchievementManager.get_achievement_progress("explorer", sample_session)
        assert progress == (2, EXPLORER_NODES_THRESHOLD)


class TestLifetimeAchievementProgress:
    """Tests for lifetime achievement progress tracking."""

    def test_veteran_progress(self, fresh_achievements, sample_lifetime):
        """Veteran progress shows total games vs threshold."""
        sample_lifetime.total_games = 5

        progress = AchievementManager.get_achievement_progress("veteran", lifetime=sample_lifetime)
        assert progress == (5, VETERAN_GAMES_THRESHOLD)

    def test_persistent_progress(self, fresh_achievements, sample_lifetime):
        """Persistent progress shows victories vs threshold."""
        sample_lifetime.total_victories = 3

        progress = AchievementManager.get_achievement_progress(
            "persistent", lifetime=sample_lifetime
        )
        assert progress == (3, PERSISTENT_VICTORIES_THRESHOLD)

    def test_legendary_progress(self, fresh_achievements, sample_lifetime):
        """Legendary progress shows victories vs threshold."""
        sample_lifetime.total_victories = 12

        progress = AchievementManager.get_achievement_progress(
            "legendary", lifetime=sample_lifetime
        )
        assert progress == (12, LEGENDARY_VICTORIES_THRESHOLD)


class TestChallengeAchievementProgress:
    """Tests for challenge achievement progress tracking."""

    def test_survivor_progress(self, fresh_achievements, sample_session):
        """Survivor progress shows turns taken vs threshold."""
        sample_session.turns_taken = 350

        progress = AchievementManager.get_achievement_progress("survivor", sample_session)
        assert progress == (350, SURVIVOR_TURNS_THRESHOLD)

    def test_shadow_dancer_progress(self, fresh_achievements, sample_session):
        """Shadow dancer progress shows turns in blind spots."""
        sample_session.turns_in_blind_spots = 75

        progress = AchievementManager.get_achievement_progress("shadow_dancer", sample_session)
        assert progress == (75, 100)


class TestProgressEdgeCases:
    """Tests for edge cases in progress tracking."""

    def test_unlocked_achievement_returns_none(self, fresh_achievements, sample_session):
        """Already unlocked achievements return None for progress."""
        AchievementManager._unlocked_achievements.add("massacre")

        progress = AchievementManager.get_achievement_progress("massacre", sample_session)
        assert progress is None

    def test_non_trackable_achievement_returns_none(self, fresh_achievements, sample_session):
        """Achievements without numeric progress return None."""
        # ghost_protocol requires completing a level undetected - not trackable numerically
        progress = AchievementManager.get_achievement_progress("ghost_protocol", sample_session)
        assert progress is None

    def test_no_session_returns_zero_progress(self, fresh_achievements):
        """Missing session returns (0, threshold) for session-based achievements."""
        progress = AchievementManager.get_achievement_progress("massacre")
        assert progress == (0, MASSACRE_KILLS_THRESHOLD)

    def test_no_lifetime_returns_zero_progress(self, fresh_achievements):
        """Missing lifetime returns (0, threshold) for lifetime-based achievements."""
        progress = AchievementManager.get_achievement_progress("veteran")
        assert progress == (0, VETERAN_GAMES_THRESHOLD)
