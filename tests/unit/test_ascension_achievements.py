#!/usr/bin/env python3
"""
Unit tests for Ascension Achievements (Phase 4).

Tests achievement unlock logic for ascension milestones and fun achievements.
TDD-first: Write these tests before implementing achievement logic.
"""



class TestAscensionMilestoneAchievements:
    """Test ascension milestone achievements (A5, A10, A15, A20)."""

    def test_sensor_sweep_unlocks_at_a5_victory(self):
        """Winning at A5+ should unlock sensor_sweep."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 5

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "sensor_sweep" in unlocked

    def test_sensor_sweep_requires_victory(self):
        """Losing at A5 should NOT unlock sensor_sweep."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = False
        session.ascension_level = 5

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "sensor_sweep" not in unlocked

    def test_sensor_sweep_not_unlocked_below_a5(self):
        """Winning at A4 should NOT unlock sensor_sweep."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 4

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "sensor_sweep" not in unlocked

    def test_firewall_breaker_unlocks_at_a10_victory(self):
        """Winning at A10+ should unlock firewall_breaker."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 10

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "firewall_breaker" in unlocked

    def test_firewall_breaker_not_unlocked_at_a5(self):
        """Winning at A5 should NOT unlock firewall_breaker (requires A10)."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 5

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "firewall_breaker" not in unlocked

    def test_silent_running_unlocks_at_a15_victory(self):
        """Winning at A15+ should unlock silent_running."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 15

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "silent_running" in unlocked

    def test_ascension_master_unlocks_at_a20_victory(self):
        """Winning at A20 should unlock ascension_master."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 20

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "ascension_master" in unlocked

    def test_ascension_master_is_hidden(self):
        """ascension_master should be a hidden achievement."""
        from game_achievements import ALL_ACHIEVEMENTS

        assert "ascension_master" in ALL_ACHIEVEMENTS
        assert ALL_ACHIEVEMENTS["ascension_master"].hidden is True

    def test_higher_ascension_unlocks_lower_achievements(self):
        """Winning at A20 should unlock all lower ascension achievements."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.ascension_level = 20

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "sensor_sweep" in unlocked
        assert "firewall_breaker" in unlocked
        assert "silent_running" in unlocked
        assert "ascension_master" in unlocked


class TestFunAchievements:
    """Test fun/hidden achievements."""

    def test_thermal_meltdown_achievement(self):
        """Dying from overheat while using System Crash unlocks thermal_meltdown."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = False
        session.death_cause = "overheat"
        session.last_exploit_used = "system_crash"

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "thermal_meltdown" in unlocked

    def test_thermal_meltdown_requires_system_crash(self):
        """Overheat death alone doesn't unlock thermal_meltdown."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = False
        session.death_cause = "overheat"
        session.last_exploit_used = "buffer_overflow"

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "thermal_meltdown" not in unlocked

    def test_own_worst_enemy_achievement(self):
        """Killing yourself with Logic Bomb unlocks own_worst_enemy."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = False
        session.death_cause = "self_damage"
        session.last_exploit_used = "logic_bomb"

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "own_worst_enemy" in unlocked

    def test_admin_slayer_achievement(self):
        """Defeating the Admin Avatar unlocks admin_slayer."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.admin_kills = 1

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "admin_slayer" in unlocked

    def test_admin_slayer_requires_kill(self):
        """No admin kills means no admin_slayer achievement."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.admin_kills = 0

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "admin_slayer" not in unlocked

    def test_close_call_achievement(self):
        """Winning with 5 or less CPU unlocks close_call."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.final_cpu = 3

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "close_call" in unlocked

    def test_close_call_requires_low_cpu(self):
        """Winning with > 5 CPU doesn't unlock close_call."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.final_cpu = 50

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "close_call" not in unlocked

    def test_close_call_requires_victory(self):
        """Losing with low CPU doesn't unlock close_call."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = False
        session.final_cpu = 3

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "close_call" not in unlocked

    def test_cold_blooded_achievement(self):
        """Winning without exceeding 25 heat unlocks cold_blooded."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.highest_heat_reached = 20

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "cold_blooded" in unlocked

    def test_cold_blooded_fails_above_25(self):
        """Winning with heat exceeding 25 doesn't unlock cold_blooded."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.highest_heat_reached = 30

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "cold_blooded" not in unlocked

    def test_floor_is_lava_achievement(self):
        """Winning without using restoration nodes unlocks floor_is_lava."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.restoration_nodes_used = 0

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "floor_is_lava" in unlocked

    def test_floor_is_lava_fails_with_nodes(self):
        """Winning with restoration nodes used doesn't unlock floor_is_lava."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.victory = True
        session.restoration_nodes_used = 3

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "floor_is_lava" not in unlocked

    def test_full_clear_achievement(self):
        """Eliminating all enemies on a floor unlocks full_clear."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.full_floor_clears = 1

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "full_clear" in unlocked

    def test_shadow_dancer_achievement(self):
        """Spending 100+ turns in blind spots unlocks shadow_dancer."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.turns_in_blind_spots = 100

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "shadow_dancer" in unlocked

    def test_shadow_dancer_requires_100_turns(self):
        """Less than 100 turns in blind spots doesn't unlock shadow_dancer."""
        from game_achievements import AchievementChecker
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        session.turns_in_blind_spots = 99

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "shadow_dancer" not in unlocked


class TestAscensionAchievementDefinitions:
    """Test that all ascension achievements are properly defined."""

    def test_all_ascension_achievements_exist(self):
        """All ascension achievements should be defined in ALL_ACHIEVEMENTS."""
        from game_achievements import ALL_ACHIEVEMENTS

        expected = [
            "sensor_sweep",
            "firewall_breaker",
            "silent_running",
            "ascension_master",
        ]
        for achievement_id in expected:
            assert achievement_id in ALL_ACHIEVEMENTS, f"Missing: {achievement_id}"

    def test_all_fun_achievements_exist(self):
        """All fun achievements should be defined in ALL_ACHIEVEMENTS."""
        from game_achievements import ALL_ACHIEVEMENTS

        expected = [
            "thermal_meltdown",
            "own_worst_enemy",
            "admin_slayer",
            "close_call",
            "cold_blooded",
            "floor_is_lava",
            "full_clear",
            "shadow_dancer",
        ]
        for achievement_id in expected:
            assert achievement_id in ALL_ACHIEVEMENTS, f"Missing: {achievement_id}"

    def test_achievement_icons_are_bracketed_text(self):
        """All achievement icons should use bracketed text, not emojis."""
        from game_achievements import ALL_ACHIEVEMENTS

        for achievement_id, achievement in ALL_ACHIEVEMENTS.items():
            # Icon should start with [ and end with ]
            assert achievement.icon.startswith("["), f"{achievement_id} icon doesn't start with ["
            assert achievement.icon.endswith("]"), f"{achievement_id} icon doesn't end with ]"
            # Icon should not contain emoji characters (basic check)
            for char in achievement.icon:
                assert (
                    ord(char) < 0x1F600 or ord(char) > 0x1F9FF
                ), f"{achievement_id} icon contains emoji"


class TestLifetimeMetricsAscension:
    """Test LifetimeMetrics ascension fields."""

    def test_lifetime_metrics_has_ascension_victories(self):
        """LifetimeMetrics should have ascension_victories field."""
        from game_metrics import LifetimeMetrics

        metrics = LifetimeMetrics()
        assert hasattr(metrics, "ascension_victories")
        assert isinstance(metrics.ascension_victories, dict) or hasattr(
            metrics.ascension_victories, "__getitem__"
        )

    def test_lifetime_metrics_has_highest_ascension_completed(self):
        """LifetimeMetrics should have highest_ascension_completed field."""
        from game_metrics import LifetimeMetrics

        metrics = LifetimeMetrics()
        assert hasattr(metrics, "highest_ascension_completed")
        assert metrics.highest_ascension_completed == 0

    def test_lifetime_metrics_to_dict_includes_ascension(self):
        """LifetimeMetrics.to_dict() should include ascension fields."""
        from game_metrics import LifetimeMetrics

        metrics = LifetimeMetrics()
        metrics.highest_ascension_completed = 5
        data = metrics.to_dict()

        assert "highest_ascension_completed" in data
        assert "ascension_victories" in data

    def test_lifetime_metrics_from_dict_loads_ascension(self):
        """LifetimeMetrics.from_dict() should load ascension fields."""
        from game_metrics import LifetimeMetrics

        data = {
            "total_games": 10,
            "total_victories": 3,
            "total_turns": 500,
            "highest_ascension_completed": 7,
            "ascension_victories": {"5": 2, "7": 1},
        }
        metrics = LifetimeMetrics.from_dict(data)

        assert metrics.highest_ascension_completed == 7
        # Counter or dict should have the values
        assert metrics.ascension_victories.get("5", 0) == 2 or metrics.ascension_victories["5"] == 2


class TestSessionMetricsAscension:
    """Test SessionMetrics has required ascension fields."""

    def test_session_metrics_has_ascension_level(self):
        """SessionMetrics should have ascension_level field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "ascension_level")
        assert session.ascension_level == 0

    def test_session_metrics_has_last_exploit_used(self):
        """SessionMetrics should have last_exploit_used field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "last_exploit_used")

    def test_session_metrics_has_admin_kills(self):
        """SessionMetrics should have admin_kills field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "admin_kills")
        assert session.admin_kills == 0

    def test_session_metrics_has_final_cpu(self):
        """SessionMetrics should have final_cpu field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "final_cpu")
        assert session.final_cpu == 0

    def test_session_metrics_has_restoration_nodes_used(self):
        """SessionMetrics should have restoration_nodes_used field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "restoration_nodes_used")
        assert session.restoration_nodes_used == 0

    def test_session_metrics_has_full_floor_clears(self):
        """SessionMetrics should have full_floor_clears field."""
        from game_metrics import SessionMetrics

        session = SessionMetrics(session_id="test", timestamp_start=0.0)
        assert hasattr(session, "full_floor_clears")
        assert session.full_floor_clears == 0
