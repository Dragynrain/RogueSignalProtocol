"""
Unit tests for achievement system (game_achievements.py).

Tests achievement checking logic, unlocking conditions, and manager functionality.
"""

from collections import Counter

import pytest

from game_achievements import (
    ALL_ACHIEVEMENTS,
    TOTAL_EXPLOITS,
    AchievementChecker,
    AchievementManager,
)
from game_metrics import LifetimeMetrics, SessionMetrics

# Note: clean_achievement_state fixture is now available from conftest.py


@pytest.fixture
def sample_session():
    """Create a sample session metrics object."""
    return SessionMetrics(
        session_id="test_session",
        timestamp_start=1000.0,
        victory=False,
        death_cause=None,
        death_level=0,
    )


@pytest.fixture
def sample_lifetime():
    """Create a sample lifetime metrics object."""
    return LifetimeMetrics()


# ============================================================================
# Combat Achievements
# ============================================================================


def test_first_blood_achievement(clean_achievement_state, sample_session):
    """Test first_blood achievement unlocks on first kill."""
    sample_session.enemies_killed["virus"] = 1

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "first_blood" in unlocked


def test_massacre_achievement(clean_achievement_state, sample_session):
    """Test massacre achievement unlocks with 20+ kills."""
    sample_session.enemies_killed["virus"] = 15
    sample_session.enemies_killed["scanner"] = 5
    sample_session.enemies_killed["admin"] = 2

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "massacre" in unlocked


def test_overkill_achievement(clean_achievement_state, sample_session):
    """Test overkill achievement unlocks with 100+ damage hit."""
    sample_session.max_single_hit_damage = 150

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "overkill" in unlocked


def test_crowd_control_achievement(clean_achievement_state, sample_session):
    """Test crowd_control achievement unlocks with 5+ AOE hits."""
    sample_session.aoe_multi_kills = Counter({5: 1, 3: 2})  # Hit 5 enemies once

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "crowd_control" in unlocked


def test_efficient_killer_achievement(clean_achievement_state, sample_session):
    """Test efficient_killer achievement with 1.5+ kills/turn average."""
    sample_session.enemies_killed["virus"] = 10
    sample_session.turns_with_kills = 5  # 10 kills / 5 turns = 2.0 avg (above 1.5)

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "efficient_killer" in unlocked


def test_efficient_killer_not_unlocked_low_average(clean_achievement_state, sample_session):
    """Test efficient_killer doesn't unlock with low kill average."""
    sample_session.enemies_killed["virus"] = 5
    sample_session.turns_with_kills = 10  # 0.5 avg (below 1.5 threshold)

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "efficient_killer" not in unlocked


# ============================================================================
# Stealth Achievements
# ============================================================================


def test_silent_assassin_achievement(clean_achievement_state, sample_session):
    """Test silent_assassin achievement with 10+ stealth streak."""
    sample_session.max_stealth_streak = 12

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "silent_assassin" in unlocked


def test_ghost_protocol_achievement(clean_achievement_state, sample_session):
    """Test ghost_protocol achievement (level complete, never detected)."""
    sample_session.levels_completed = 1
    sample_session.ever_detected = False

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "ghost_protocol" in unlocked


def test_ghost_protocol_not_unlocked_if_detected(clean_achievement_state, sample_session):
    """Test ghost_protocol doesn't unlock if player was detected."""
    sample_session.levels_completed = 1
    sample_session.ever_detected = True

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "ghost_protocol" not in unlocked


def test_shadow_master_achievement(clean_achievement_state, sample_session):
    """Test blind_spot_master achievement with 5+ shadow kills."""
    sample_session.ambushes_from_blind_spots = 7

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "blind_spot_master" in unlocked


def test_invisible_victory_achievement(clean_achievement_state, sample_session):
    """Test invisible_victory achievement (win without detection)."""
    sample_session.victory = True
    sample_session.ever_detected = False

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "invisible_victory" in unlocked


# ============================================================================
# Efficiency & Speed Achievements
# ============================================================================


def test_speedrunner_achievement(clean_achievement_state, sample_session):
    """Test speedrunner achievement (win in <100 turns)."""
    sample_session.victory = True
    sample_session.turns_taken = 85

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "speedrunner" in unlocked


def test_speedrunner_not_unlocked_defeat(clean_achievement_state, sample_session):
    """Test speedrunner doesn't unlock on defeat."""
    sample_session.victory = False
    sample_session.turns_taken = 85

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "speedrunner" not in unlocked


def test_heat_master_achievement(clean_achievement_state, sample_session):
    """Test heat_master achievement (win with <50 heat)."""
    sample_session.victory = True
    sample_session.highest_heat_reached = 45

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "heat_master" in unlocked


def test_resource_efficient_achievement(clean_achievement_state, sample_session):
    """Test resource_efficient achievement (win without code hacks)."""
    sample_session.victory = True
    sample_session.used_any_code_hacks = False

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "resource_efficient" in unlocked


def test_pure_skill_achievement(clean_achievement_state, sample_session):
    """Test pure_skill achievement (win without exploits or code hacks)."""
    sample_session.victory = True
    sample_session.used_any_exploits = False
    sample_session.used_any_code_hacks = False

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "pure_skill" in unlocked


# ============================================================================
# Challenge Achievements
# ============================================================================


def test_untouchable_achievement(clean_achievement_state, sample_session):
    """Test untouchable achievement (win without damage)."""
    sample_session.victory = True
    sample_session.took_any_damage = False

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "untouchable" in unlocked


def test_no_trace_achievement(clean_achievement_state, sample_session):
    """Test no_trace achievement (win with low trace)."""
    sample_session.victory = True
    sample_session.trace_increases = 2  # Very few trace increases

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "no_trace" in unlocked


def test_minimalist_achievement(clean_achievement_state, sample_session):
    """Test minimalist achievement (win with ≤3 exploits)."""
    sample_session.victory = True
    sample_session.exploits_equipped = Counter(
        {"system_hop": 1, "code_injection": 1, "buffer_overflow": 1}
    )

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "minimalist" in unlocked


def test_pacifist_achievement(clean_achievement_state, sample_session):
    """Test pacifist achievement (complete level with ≤5 kills on that level)."""
    sample_session.levels_completed = 1
    # min_kills_any_level tracks the minimum kills on any single completed level
    sample_session.min_kills_any_level = 5

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "pacifist" in unlocked


def test_pacifist_not_unlocked_with_6_kills_on_level(clean_achievement_state, sample_session):
    """Test pacifist NOT unlocked if minimum kills on any level > 5."""
    sample_session.levels_completed = 1
    sample_session.min_kills_any_level = 6

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "pacifist" not in unlocked


def test_pacifist_unlocked_if_any_level_had_low_kills(clean_achievement_state, sample_session):
    """Test pacifist unlocked if ANY completed level had <= 5 kills, even if others had more."""
    sample_session.levels_completed = 3
    # Player completed 3 levels: level 1 with 10 kills, level 2 with 3 kills, level 3 with 8 kills
    # min_kills_any_level = 3 (from level 2)
    sample_session.min_kills_any_level = 3

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "pacifist" in unlocked


# ============================================================================
# Mastery Achievements
# ============================================================================


def test_master_hacker_achievement(clean_achievement_state, sample_session):
    """Test master_hacker achievement (use all 12 exploits)."""
    # Create 12 unique exploits
    sample_session.unique_exploits_used_this_run = {f"exploit_{i}" for i in range(TOTAL_EXPLOITS)}

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "master_hacker" in unlocked


def test_code_collector_achievement(clean_achievement_state, sample_session):
    """Test code_collector achievement (use all 6 code hack colors)."""
    # Code hacks are tracked by name (color), not by effect type
    sample_session.unique_code_hacks_used_this_run = {
        "Crimson Code",
        "Azure Code",
        "Emerald Code",
        "Golden Code",
        "Violet Code",
        "Silver Code",
    }

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "code_collector" in unlocked


def test_enemy_database_achievement(clean_achievement_state, sample_session):
    """Test enemy_database achievement (encounter all enemy types)."""
    sample_session.unique_enemies_encountered = {"virus", "scanner", "firewall", "admin", "hunter"}

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "enemy_database" in unlocked


def test_explorer_achievement(clean_achievement_state, sample_session):
    """Test explorer achievement (discover 3+ special nodes)."""
    sample_session.special_nodes_discovered = {"upgrade", "story", "gateway"}

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "explorer" in unlocked


def test_survivor_achievement(clean_achievement_state, sample_session):
    """Test survivor achievement (survive 500+ turns)."""
    sample_session.turns_taken = 550

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())
    assert "survivor" in unlocked


# ============================================================================
# Lifetime Achievements
# ============================================================================


def test_veteran_achievement(clean_achievement_state, sample_lifetime):
    """Test veteran achievement (10 games played)."""
    sample_lifetime.total_games = 12

    unlocked = AchievementChecker.check_lifetime_achievements(sample_lifetime, set())
    assert "veteran" in unlocked


def test_persistent_achievement(clean_achievement_state, sample_lifetime):
    """Test persistent achievement (5 victories)."""
    sample_lifetime.total_victories = 7

    unlocked = AchievementChecker.check_lifetime_achievements(sample_lifetime, set())
    assert "persistent" in unlocked


def test_legendary_achievement(clean_achievement_state, sample_lifetime):
    """Test legendary achievement (20 victories)."""
    sample_lifetime.total_victories = 25

    unlocked = AchievementChecker.check_lifetime_achievements(sample_lifetime, set())
    assert "legendary" in unlocked


# ============================================================================
# AchievementManager Tests
# ============================================================================


def test_achievement_manager_load_achievements(clean_achievement_state):
    """Test loading unlocked achievements."""
    unlocked_list = ["first_blood", "speedrunner", "ghost_protocol"]
    AchievementManager.load_unlocked_achievements(unlocked_list)

    assert AchievementManager.is_unlocked("first_blood")
    assert AchievementManager.is_unlocked("speedrunner")
    assert AchievementManager.is_unlocked("ghost_protocol")
    assert not AchievementManager.is_unlocked("massacre")


def test_achievement_manager_check_and_queue(clean_achievement_state, sample_session):
    """Test checking achievements and queueing popups."""
    sample_session.enemies_killed["virus"] = 1
    sample_session.victory = True
    sample_session.turns_taken = 95

    newly_unlocked = AchievementManager.check_achievements(sample_session)

    assert "first_blood" in newly_unlocked
    assert "speedrunner" in newly_unlocked
    assert AchievementManager.has_pending_popups()


def test_achievement_manager_popup_queue(clean_achievement_state):
    """Test popup queue management."""
    AchievementManager._pending_popups = ["first_blood", "speedrunner", "massacre"]

    assert AchievementManager.has_pending_popups()

    popup1 = AchievementManager.get_next_popup()
    assert popup1 == "first_blood"
    assert AchievementManager.has_pending_popups()

    popup2 = AchievementManager.get_next_popup()
    assert popup2 == "speedrunner"

    popup3 = AchievementManager.get_next_popup()
    assert popup3 == "massacre"

    assert not AchievementManager.has_pending_popups()
    assert AchievementManager.get_next_popup() is None


def test_achievement_manager_no_duplicate_unlocks(clean_achievement_state, sample_session):
    """Test that already-unlocked achievements aren't re-unlocked."""
    sample_session.enemies_killed["virus"] = 1

    # First unlock
    AchievementManager.check_achievements(sample_session)
    assert AchievementManager.is_unlocked("first_blood")

    # Clear pending popups
    AchievementManager.clear_pending_popups()

    # Try to unlock again
    newly_unlocked = AchievementManager.check_achievements(sample_session)
    assert "first_blood" not in newly_unlocked
    assert not AchievementManager.has_pending_popups()


def test_achievement_manager_get_unlock_progress(clean_achievement_state):
    """Test getting unlock progress statistics."""
    AchievementManager.load_unlocked_achievements(["first_blood", "speedrunner"])

    unlocked, total = AchievementManager.get_unlock_progress()
    assert unlocked == 2
    assert total == len(ALL_ACHIEVEMENTS)


def test_achievement_manager_get_by_category(clean_achievement_state):
    """Test getting achievements by category."""
    combat_achievements = AchievementManager.get_achievements_by_category("combat")
    assert (
        len(combat_achievements) == 7
    )  # first_blood, massacre, overkill, crowd_control, efficient_killer, admin_slayer, full_clear

    stealth_achievements = AchievementManager.get_achievements_by_category("stealth")
    assert (
        len(stealth_achievements) == 5
    )  # silent_assassin, ghost_protocol, blind_spot_master, invisible_victory, shadow_dancer


# ============================================================================
# Edge Cases
# ============================================================================


def test_multiple_achievements_one_session(clean_achievement_state, sample_session):
    """Test unlocking multiple achievements in a single session."""
    # Set up for multiple achievements
    sample_session.victory = True
    sample_session.turns_taken = 95  # speedrunner
    sample_session.enemies_killed["virus"] = 25  # first_blood, massacre
    sample_session.max_single_hit_damage = 120  # overkill
    sample_session.highest_heat_reached = 45  # heat_master
    sample_session.took_any_damage = False  # untouchable
    sample_session.ever_detected = False  # invisible_victory

    unlocked = AchievementChecker.check_session_achievements(sample_session, set())

    assert "first_blood" in unlocked
    assert "massacre" in unlocked
    assert "overkill" in unlocked
    assert "speedrunner" in unlocked
    assert "heat_master" in unlocked
    assert "untouchable" in unlocked
    assert "invisible_victory" in unlocked


def test_achievement_info_retrieval(clean_achievement_state):
    """Test retrieving achievement information."""
    first_blood = AchievementManager.get_achievement_info("first_blood")

    assert first_blood is not None
    assert first_blood.name == "First Blood"
    assert first_blood.icon == "[BLOOD]"
    assert first_blood.category == "combat"
