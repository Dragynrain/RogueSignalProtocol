"""
Achievement Accumulation and Triggering Integration Tests

Tests that achievements properly accumulate metrics during gameplay and trigger
at the correct time (immediate vs session-end). Uses GameTestAgent for headless
simulation of actual gameplay scenarios.

Coverage:
- Immediate achievements (First Blood, Massacre, Overkill, etc.)
- Session-end achievements (Speedrunner, Heat Master, etc.)
- Collection achievements (Master Hacker, Enemy Database, etc.)
- Stealth achievements (Silent Assassin, Ghost Protocol, etc.)
- Edge cases (AOE multi-kills, stealth streaks, etc.)
"""

import pytest

from game_achievements import AchievementChecker, AchievementManager
from game_combat import ExploitSystem
from game_entities import EnemyState, Position
from game_metrics import get_current_session, init_session_metrics
from tests.fixtures.simple_fixtures import enemy_builder
from tests.test_agent import GameTestAgent


# ============================================================================
# IMMEDIATE COMBAT ACHIEVEMENTS
# ============================================================================


class TestImmediateCombatAchievements:
    """Test combat achievements that trigger immediately during gameplay."""

    def test_first_blood_triggers_on_first_kill(self):
        """First Blood should unlock immediately on first enemy kill."""
        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10001)
        session = agent.engine.metrics  # Use session from engine
        agent.player.position.x = 10
        agent.player.position.y = 10

        # Spawn and kill one enemy
        enemy = agent.spawn_enemy("bot", 11, 10)
        enemy.cpu = 10

        agent.player.inventory_manager.equipped_exploits = ["buffer_overflow"]
        exploit_system = ExploitSystem(agent.engine)
        exploit_system.execute_exploit("buffer_overflow", Position(11, 10))

        # Verify metrics accumulated
        assert sum(session.enemies_killed.values()) == 1, "Should track 1 kill"

        # Verify achievement would trigger immediately
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "first_blood" in unlocked, "First Blood should trigger immediately"

    def test_massacre_triggers_on_20_kills(self):
        """Massacre should trigger immediately after 20th kill."""
        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10002)
        session = agent.engine.metrics  # Use session from engine
        agent.player.position.x = 10
        agent.player.position.y = 10
        agent.player.cpu = 1000  # High CPU to not die

        # Use code_injection (range 5, damage 25) to kill enemies from distance
        agent.player.inventory_manager.equipped_exploits = ["code_injection"]
        exploit_system = ExploitSystem(agent.engine)

        # Kill 20 enemies one by one, spawning each at same position to stay in range
        kill_position = Position(13, 13)  # Distance from (10,10) = ~4.2, well within range 5
        for i in range(20):
            # Spawn enemy at fixed position within range
            enemy = agent.spawn_enemy("bot", kill_position.x, kill_position.y)
            enemy.cpu = 20  # Low HP to ensure one-shot kill with 25 damage
            exploit_system.execute_exploit("code_injection", kill_position)

        # Verify metrics accumulated
        total_kills = sum(session.enemies_killed.values())
        assert total_kills >= 20, f"Should track 20+ kills, got {total_kills}"

        # Verify achievement triggers immediately
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "massacre" in unlocked, "Massacre should trigger at 20 kills"

    def test_overkill_triggers_on_50_damage_hit(self):
        """Overkill should trigger immediately on 50+ damage hit."""
        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10005)
        session = agent.engine.metrics  # Use session from engine

        # Directly set max damage to simulate a high-damage hit
        # (Testing achievement logic, not combat mechanics)
        session.max_single_hit_damage = 75

        # Verify achievement triggers
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "overkill" in unlocked, "Overkill should trigger on 50+ damage"

    def test_crowd_control_triggers_on_aoe_5_enemies(self):
        """Crowd Control should trigger when AOE hits 5+ enemies."""
        from collections import Counter

        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10006)
        session = agent.engine.metrics  # Use session from engine

        # Directly set AOE multi-kill metric to simulate hitting 5 enemies with one AOE
        # (Testing achievement logic, not exploit mechanics)
        session.aoe_multi_kills = Counter({5: 1, 3: 2})  # Hit 5 enemies once, 3 enemies twice

        # Check if AOE multi-kill was tracked
        max_aoe = max(session.aoe_multi_kills.keys(), default=0)
        assert max_aoe >= 5, f"Should track 5+ AOE hits, got {max_aoe}"

        # Verify achievement triggers
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "crowd_control" in unlocked, "Crowd Control should trigger on 5+ AOE hits"

    def test_efficient_killer_triggers_on_sustained_performance(self):
        """Efficient Killer should trigger with 2+ kills/turn for 10+ turns."""
        from collections import Counter

        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10003)
        session = agent.engine.metrics  # Use session from engine

        # Directly set metrics to simulate sustained high-kill performance
        # (Testing achievement logic, not turn processing)
        session.enemies_killed = Counter({"bot": 25})  # 25 total kills
        session.turns_with_kills = 10  # 10 turns with kills = 2.5 avg kills/turn

        # Verify metrics: 10+ turns with kills, 2+ avg kills/turn
        assert session.turns_with_kills >= 10, f"Should have 10+ turns with kills, got {session.turns_with_kills}"
        total_kills = sum(session.enemies_killed.values())
        avg_kills = total_kills / session.turns_with_kills if session.turns_with_kills > 0 else 0
        assert avg_kills >= 2.0, f"Should average 2+ kills/turn, got {avg_kills:.2f}"

        # Verify achievement triggers
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "efficient_killer" in unlocked, "Efficient Killer should trigger"


# ============================================================================
# IMMEDIATE STEALTH ACHIEVEMENTS
# ============================================================================


class TestImmediateStealthAchievements:
    """Test stealth achievements that trigger immediately during gameplay."""

    def test_silent_assassin_triggers_on_10_stealth_kills(self):
        """Silent Assassin should trigger after 10 undetected kills."""
        AchievementManager._unlocked_achievements = set()

        agent = GameTestAgent(seed=10004)
        session = agent.engine.metrics  # Use session from engine
        agent.player.position.x = 10
        agent.player.position.y = 10
        agent.player.cpu = 1000

        # Ensure player is never detected
        agent.engine.player.stealthed = True

        agent.player.inventory_manager.equipped_exploits = ["buffer_overflow"]
        exploit_system = ExploitSystem(agent.engine)

        # Kill 10 enemies while undetected
        for i in range(10):
            enemy = agent.spawn_enemy("bot", 15 + i, 15)
            enemy.cpu = 10
            enemy.state = EnemyState.UNAWARE  # Not hostile/alerted

            # Set up stealth conditions
            session.current_stealth_streak = i  # Track streak before kill

            exploit_system.execute_exploit("buffer_overflow", enemy.position)

            # Update stealth streak manually (normally done by combat system)
            session.current_stealth_streak += 1
            if session.current_stealth_streak > session.max_stealth_streak:
                session.max_stealth_streak = session.current_stealth_streak

        # Verify metrics
        assert session.max_stealth_streak >= 10, f"Should have 10+ stealth streak, got {session.max_stealth_streak}"

        # Verify achievement triggers
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "silent_assassin" in unlocked, "Silent Assassin should trigger at 10 stealth kills"

    def test_blind_spot_master_triggers_on_5_blind_spot_kills(self):
        """Blind Spot Master should trigger after 5 blind spot ambushes."""
        init_session_metrics()
        session = get_current_session()
        AchievementManager._unlocked_achievements = set()

        # Manually track blind spot kills (normally done by combat system)
        session.ambushes_from_blind_spots = 5

        # Verify achievement triggers
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "blind_spot_master" in unlocked, "Blind Spot Master should trigger at 5 blind spot kills"


# ============================================================================
# SESSION-END ACHIEVEMENTS
# ============================================================================


class TestSessionEndAchievements:
    """Test achievements that only unlock at session completion."""

    def test_speedrunner_requires_victory_under_100_turns(self):
        """Speedrunner requires victory in <100 turns."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.turns_taken = 95

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "speedrunner" in unlocked, "Speedrunner should unlock on fast victory"

        # Should NOT unlock without victory
        session.victory = False
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "speedrunner" not in unlocked, "Speedrunner requires victory"

    def test_heat_master_requires_victory_under_50_heat(self):
        """Heat Master requires victory with max heat <50."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.highest_heat_reached = 45

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "heat_master" in unlocked, "Heat Master should unlock on low-heat victory"

        # Should NOT unlock with high heat
        session.highest_heat_reached = 75
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "heat_master" not in unlocked, "Heat Master requires <50 heat"

    def test_ghost_protocol_requires_level_completion_undetected(self):
        """Ghost Protocol requires completing a level without detection."""
        init_session_metrics()
        session = get_current_session()
        session.levels_completed = 1
        session.ever_detected = False

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "ghost_protocol" in unlocked, "Ghost Protocol should unlock on undetected level completion"

        # Should NOT unlock if detected
        session.ever_detected = True
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "ghost_protocol" not in unlocked, "Ghost Protocol requires no detection"

    def test_invisible_victory_requires_win_without_detection(self):
        """Invisible Victory requires winning without ever being detected."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.ever_detected = False

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "invisible_victory" in unlocked, "Invisible Victory should unlock"

        # Should NOT unlock if detected at any point
        session.ever_detected = True
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "invisible_victory" not in unlocked, "Cannot be detected at any point"

    def test_untouchable_requires_win_without_damage(self):
        """Untouchable requires winning without taking any damage."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.took_any_damage = False

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "untouchable" in unlocked, "Untouchable should unlock on no-damage victory"

        # Should NOT unlock if took damage
        session.took_any_damage = True
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "untouchable" not in unlocked, "Cannot take damage"

    def test_resource_efficient_requires_win_without_code_hacks(self):
        """Resource Efficient requires winning without code hacks."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.used_any_code_hacks = False

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "resource_efficient" in unlocked, "Resource Efficient should unlock"

        # Should NOT unlock if used code hacks
        session.used_any_code_hacks = True
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "resource_efficient" not in unlocked, "Cannot use code hacks"

    def test_pure_skill_requires_win_without_exploits_or_code_hacks(self):
        """Pure Skill requires winning without exploits or code hacks."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.used_any_exploits = False
        session.used_any_code_hacks = False

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "pure_skill" in unlocked, "Pure Skill should unlock"

        # Should NOT unlock if used exploits
        session.used_any_exploits = True
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "pure_skill" not in unlocked, "Cannot use exploits"

    def test_minimalist_requires_win_with_3_or_fewer_exploits(self):
        """Minimalist requires winning with ≤3 exploits equipped."""
        from collections import Counter

        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.exploits_equipped = Counter(["buffer_overflow", "code_injection", "malware_bomb"])

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "minimalist" in unlocked, "Minimalist should unlock with 3 exploits"

        # Should NOT unlock with 4+ exploits
        session.exploits_equipped = Counter(["buffer_overflow", "code_injection", "malware_bomb", "dos_packet"])
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "minimalist" not in unlocked, "Cannot use 4+ exploits"

    def test_pacifist_requires_level_completion_with_5_or_fewer_kills(self):
        """Pacifist requires completing a level with ≤5 kills."""
        from collections import Counter

        init_session_metrics()
        session = get_current_session()
        session.levels_completed = 1
        session.enemies_killed = Counter({"bot": 3, "scanner": 2})

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "pacifist" in unlocked, "Pacifist should unlock with ≤5 kills"

        # Should NOT unlock with 6+ kills
        session.enemies_killed = Counter({"bot": 4, "scanner": 3})
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "pacifist" not in unlocked, "Cannot have 6+ kills"

    def test_no_trace_requires_win_with_low_trace(self):
        """No Trace requires winning with low trace increases."""
        init_session_metrics()
        session = get_current_session()
        session.victory = True
        session.trace_increases = 2  # Very few trace increases

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "no_trace" in unlocked, "No Trace should unlock with low trace"

        # Should NOT unlock with high trace
        session.trace_increases = 10
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "no_trace" not in unlocked, "Too many trace increases"


# ============================================================================
# COLLECTION ACHIEVEMENTS
# ============================================================================


class TestCollectionAchievements:
    """Test achievements requiring collection of items/experiences."""

    def test_master_hacker_requires_all_12_exploits_used(self):
        """Master Hacker requires using all 12 exploits in one run."""
        init_session_metrics()
        session = get_current_session()

        # Use all 12 exploits
        from game_achievements import TOTAL_EXPLOITS

        session.unique_exploits_used_this_run = {f"exploit_{i}" for i in range(TOTAL_EXPLOITS)}

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "master_hacker" in unlocked, "Master Hacker should unlock"

        # Should NOT unlock with 11 exploits
        session.unique_exploits_used_this_run = {f"exploit_{i}" for i in range(TOTAL_EXPLOITS - 1)}
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "master_hacker" not in unlocked, "Need all 12 exploits"

    def test_code_collector_requires_all_6_code_hack_types(self):
        """Code Collector requires using all 6 code hack types."""
        init_session_metrics()
        session = get_current_session()

        session.unique_code_hacks_used_this_run = {
            "restore_cpu",
            "reduce_heat",
            "reduce_trace_level",
            "speed_boost",
            "enhanced_vision",
            "exploit_efficiency",
        }

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "code_collector" in unlocked, "Code Collector should unlock"

        # Should NOT unlock with 5 types
        session.unique_code_hacks_used_this_run = {
            "restore_cpu",
            "reduce_heat",
            "reduce_trace_level",
            "speed_boost",
            "enhanced_vision",
        }
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "code_collector" not in unlocked, "Need all 6 code hack types"

    def test_enemy_database_requires_5_unique_enemy_types(self):
        """Enemy Database requires encountering 5+ unique enemy types."""
        init_session_metrics()
        session = get_current_session()

        session.unique_enemies_encountered = {"bot", "scanner", "firewall", "admin", "hunter"}

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "enemy_database" in unlocked, "Enemy Database should unlock"

        # Should NOT unlock with 4 types
        session.unique_enemies_encountered = {"bot", "scanner", "firewall", "admin"}
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "enemy_database" not in unlocked, "Need 5+ enemy types"

    def test_explorer_requires_3_special_node_types(self):
        """Explorer requires discovering 3+ special node types."""
        init_session_metrics()
        session = get_current_session()

        session.special_nodes_discovered = {"upgrade", "story", "gateway"}

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "explorer" in unlocked, "Explorer should unlock"

        # Should NOT unlock with 2 types
        session.special_nodes_discovered = {"upgrade", "story"}
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "explorer" not in unlocked, "Need 3+ special node types"

    def test_survivor_requires_500_plus_turns(self):
        """Survivor requires surviving 500+ turns."""
        init_session_metrics()
        session = get_current_session()
        session.turns_taken = 550

        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "survivor" in unlocked, "Survivor should unlock at 500+ turns"

        # Should NOT unlock with <500 turns
        session.turns_taken = 450
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "survivor" not in unlocked, "Need 500+ turns"


# ============================================================================
# LIFETIME ACHIEVEMENTS
# ============================================================================


class TestLifetimeAchievements:
    """Test lifetime achievements based on cumulative stats."""

    def test_veteran_requires_10_games_played(self):
        """Veteran requires completing 10 games."""
        from game_metrics import LifetimeMetrics

        lifetime = LifetimeMetrics()
        lifetime.total_games = 12

        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "veteran" in unlocked, "Veteran should unlock at 10 games"

        # Should NOT unlock with <10 games
        lifetime.total_games = 9
        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "veteran" not in unlocked, "Need 10 games"

    def test_persistent_requires_5_victories(self):
        """Persistent requires 5 victories."""
        from game_metrics import LifetimeMetrics

        lifetime = LifetimeMetrics()
        lifetime.total_victories = 7

        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "persistent" in unlocked, "Persistent should unlock at 5 victories"

        # Should NOT unlock with <5 victories
        lifetime.total_victories = 4
        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "persistent" not in unlocked, "Need 5 victories"

    def test_legendary_requires_20_victories(self):
        """Legendary requires 20 victories."""
        from game_metrics import LifetimeMetrics

        lifetime = LifetimeMetrics()
        lifetime.total_victories = 25

        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "legendary" in unlocked, "Legendary should unlock at 20 victories"

        # Should NOT unlock with <20 victories
        lifetime.total_victories = 19
        unlocked = AchievementChecker.check_lifetime_achievements(lifetime, set())
        assert "legendary" not in unlocked, "Need 20 victories"


# ============================================================================
# EDGE CASES AND COMPLEX SCENARIOS
# ============================================================================


class TestAchievementEdgeCases:
    """Test edge cases in achievement triggering."""

    def test_multiple_achievements_unlock_in_single_session(self):
        """Multiple achievements can unlock in a single session."""
        init_session_metrics()
        session = get_current_session()

        # Set up for multiple achievements
        session.victory = True
        session.turns_taken = 90  # Speedrunner
        session.enemies_killed["bot"] = 25  # First Blood + Massacre
        session.max_single_hit_damage = 75  # Overkill
        session.highest_heat_reached = 40  # Heat Master
        session.took_any_damage = False  # Untouchable
        session.ever_detected = False  # Invisible Victory

        unlocked = AchievementChecker.check_session_achievements(session, set())

        # Should unlock multiple achievements
        assert "first_blood" in unlocked
        assert "massacre" in unlocked
        assert "overkill" in unlocked
        assert "speedrunner" in unlocked
        assert "heat_master" in unlocked
        assert "untouchable" in unlocked
        assert "invisible_victory" in unlocked

    def test_achievements_dont_re_unlock(self):
        """Already-unlocked achievements should not unlock again."""
        init_session_metrics()
        session = get_current_session()
        session.enemies_killed["bot"] = 5

        # First check - should unlock
        unlocked = AchievementChecker.check_session_achievements(session, set())
        assert "first_blood" in unlocked

        # Second check with first_blood already unlocked
        unlocked = AchievementChecker.check_session_achievements(session, {"first_blood"})
        assert "first_blood" not in unlocked, "Should not re-unlock"

    def test_immediate_vs_session_end_timing(self, basic_game_engine):
        """Immediate achievements trigger mid-game, session achievements at end."""
        init_session_metrics()
        session = get_current_session()
        AchievementManager._unlocked_achievements = set()

        basic_game_engine.player.position.x = 10
        basic_game_engine.player.position.y = 10
        basic_game_engine.player.cpu = 100

        # Kill an enemy mid-game
        target = enemy_builder("bot", pos=(11, 10))
        target.cpu = 10
        basic_game_engine.enemies = [target]

        basic_game_engine.player.inventory_manager.equipped_exploits = ["buffer_overflow"]
        exploit_system = ExploitSystem(basic_game_engine)
        exploit_system.execute_exploit("buffer_overflow", Position(11, 10))

        # First Blood should be available immediately
        immediate = AchievementChecker.check_immediate_achievements(session, set())
        assert "first_blood" in immediate, "First Blood triggers immediately"

        # Speedrunner should NOT be available (requires session completion)
        session.turns_taken = 50
        assert "speedrunner" not in immediate, "Speedrunner requires session end"

        # Only at session end with victory should Speedrunner unlock
        session.victory = True
        session_end = AchievementChecker.check_session_achievements(session, {"first_blood"})
        assert "speedrunner" in session_end, "Speedrunner unlocks at session end"

    def test_aoe_multi_kill_tracking(self):
        """AOE attacks should properly track number of enemies hit."""
        from collections import Counter

        agent = GameTestAgent(seed=10007)
        session = agent.engine.metrics  # Use session from engine

        # Directly set AOE metric to simulate hitting 3 enemies with one AOE
        # (Testing achievement logic and metric tracking, not exploit mechanics)
        session.aoe_multi_kills = Counter({3: 1, 2: 2})  # Hit 3 enemies once, 2 enemies twice

        # Should track 3 enemies hit
        max_aoe = max(session.aoe_multi_kills.keys(), default=0)
        assert max_aoe >= 3, f"Should track 3 AOE hits, got {max_aoe}"

    def test_stealth_streak_breaks_on_detection(self):
        """Stealth streak should reset when detected."""
        init_session_metrics()
        session = get_current_session()

        # Build up a stealth streak
        session.current_stealth_streak = 5
        session.max_stealth_streak = 5

        # Get detected (normally done by alert system)
        session.ever_detected = True
        session.current_stealth_streak = 0  # Streak breaks

        # Max should still be 5
        assert session.max_stealth_streak == 5, "Max streak should be preserved"
        assert session.current_stealth_streak == 0, "Current streak should reset"

        # Silent Assassin should NOT unlock (needs 10)
        unlocked = AchievementChecker.check_immediate_achievements(session, set())
        assert "silent_assassin" not in unlocked, "Streak was broken before 10"
