"""
Achievement system for RogueSignalProtocol.

Defines achievements and checks if they should be unlocked based on session metrics.
Integrates with the metrics system (game_metrics.py) and popup system (game_achievement_popups.py).
"""

import logging
from dataclasses import dataclass

from game_metrics import LifetimeMetrics, SessionMetrics

logger = logging.getLogger(__name__)


# Constants for collection achievements
TOTAL_EXPLOITS = 12  # From game_content.json
# Each code color maps 1:1 to a randomized effect per game session
# Tracks by code name: "Crimson Code", "Azure Code", "Emerald Code", "Golden Code", "Violet Code", "Silver Code"
TOTAL_CODE_HACK_TYPES = 6

# Achievement threshold constants
# Early game / Easy achievements
KILL_STREAK_5_THRESHOLD = 5
KILL_STREAK_10_THRESHOLD = 10
HEAT_SPIKE_THRESHOLD = 50
ROOKIE_GAMES_THRESHOLD = 3

# Combat
MASSACRE_KILLS_THRESHOLD = 20
OVERKILL_DAMAGE_THRESHOLD = 50
CROWD_CONTROL_AOE_THRESHOLD = 5
EFFICIENT_KILLER_TURNS_THRESHOLD = 5
EFFICIENT_KILLER_AVG_KILLS = 1.5

# Stealth
SILENT_ASSASSIN_STREAK_THRESHOLD = 10
BLIND_SPOT_AMBUSHES_THRESHOLD = 5

# Efficiency/Mastery
ENEMY_DATABASE_UNIQUE_THRESHOLD = 5
EXPLORER_NODES_THRESHOLD = 3

# Lifetime
SURVIVOR_TURNS_THRESHOLD = 500
VETERAN_GAMES_THRESHOLD = 10
PERSISTENT_VICTORIES_THRESHOLD = 5
LEGENDARY_VICTORIES_THRESHOLD = 20


@dataclass
class Achievement:
    """Defines a single achievement."""

    id: str
    name: str
    description: str
    icon: str  # Unicode symbol or emoji
    category: str  # "combat", "stealth", "efficiency", "mastery", "challenge", "lifetime"
    hidden: bool = False  # Don't show in menu until unlocked


# ============================================================================
# ACHIEVEMENT DEFINITIONS
# ============================================================================

# Category: Early Game / Easy Dopamine (unlocks quickly to keep players engaged)
EARLY_GAME_ACHIEVEMENTS = {
    "system_failure": Achievement(
        id="system_failure",
        name="System Failure",
        description="Die for the first time",
        icon="[DEATH]",
        category="early",
    ),
    "victory_protocol": Achievement(
        id="victory_protocol",
        name="Victory Protocol",
        description="Win your first game",
        icon="[WIN]",
        category="early",
    ),
    "network_breach": Achievement(
        id="network_breach",
        name="Network Breach",
        description="Complete your first level",
        icon="[GATE]",
        category="early",
    ),
    "payload_deployed": Achievement(
        id="payload_deployed",
        name="Payload Deployed",
        description="Use your first exploit",
        icon="[EXEC]",
        category="early",
    ),
    "hack_activated": Achievement(
        id="hack_activated",
        name="Hack Activated",
        description="Use your first code hack",
        icon="[CODE]",
        category="early",
    ),
    "system_restore": Achievement(
        id="system_restore",
        name="System Restore",
        description="Use a restoration node",
        icon="[NODE]",
        category="early",
    ),
    "kill_streak_5": Achievement(
        id="kill_streak_5",
        name="Kill Streak",
        description=f"Kill {KILL_STREAK_5_THRESHOLD} enemies in one run",
        icon="[KILL5]",
        category="early",
    ),
    "kill_streak_10": Achievement(
        id="kill_streak_10",
        name="Body Count",
        description=f"Kill {KILL_STREAK_10_THRESHOLD} enemies in one run",
        icon="[KILL10]",
        category="early",
    ),
    "rookie": Achievement(
        id="rookie",
        name="Rookie",
        description=f"Complete {ROOKIE_GAMES_THRESHOLD} games",
        icon="[PLAY]",
        category="early",
    ),
    "heat_spike": Achievement(
        id="heat_spike",
        name="Heat Spike",
        description=f"Reach {HEAT_SPIKE_THRESHOLD}+ heat in a run",
        icon="[HOT]",
        category="early",
    ),
}


# Category: Combat Mastery
COMBAT_ACHIEVEMENTS = {
    "first_blood": Achievement(
        id="first_blood",
        name="First Blood",
        description="Kill your first enemy",
        icon="[BLOOD]",
        category="combat",
    ),
    "massacre": Achievement(
        id="massacre",
        name="Massacre",
        description=f"Kill {MASSACRE_KILLS_THRESHOLD}+ enemies in one run",
        icon="[SKULL]",
        category="combat",
    ),
    "overkill": Achievement(
        id="overkill",
        name="Overkill",
        description=f"Deal {OVERKILL_DAMAGE_THRESHOLD}+ damage in a single hit",
        icon="[CRIT]",
        category="combat",
    ),
    "crowd_control": Achievement(
        id="crowd_control",
        name="Crowd Control",
        description=f"Hit {CROWD_CONTROL_AOE_THRESHOLD}+ enemies with one AOE exploit",
        icon="[AOE]",
        category="combat",
    ),
    "efficient_killer": Achievement(
        id="efficient_killer",
        name="Efficient Killer",
        description=f"Average {EFFICIENT_KILLER_AVG_KILLS:.1f}+ kills per turn for {EFFICIENT_KILLER_TURNS_THRESHOLD}+ turns",
        icon="[TARGET]",
        category="combat",
    ),
}


# Category: Stealth Mastery
STEALTH_ACHIEVEMENTS = {
    "silent_assassin": Achievement(
        id="silent_assassin",
        name="Silent Assassin",
        description=f"Kill {SILENT_ASSASSIN_STREAK_THRESHOLD} enemies without being detected",
        icon="[KNIFE]",
        category="stealth",
    ),
    "ghost_protocol": Achievement(
        id="ghost_protocol",
        name="Ghost Protocol",
        description="Complete a level without being detected",
        icon="[GHOST]",
        category="stealth",
    ),
    "blind_spot_master": Achievement(
        id="blind_spot_master",
        name="Blind Spot Master",
        description=f"Kill {BLIND_SPOT_AMBUSHES_THRESHOLD}+ enemies from blind spots in one run",
        icon="[DARK]",
        category="stealth",
    ),
    "invisible_victory": Achievement(
        id="invisible_victory",
        name="Invisible Victory",
        description="Win the game without ever being detected",
        icon="[INVIS]",
        category="stealth",
    ),
}


# Category: Efficiency & Speed
EFFICIENCY_ACHIEVEMENTS = {
    "speedrunner": Achievement(
        id="speedrunner",
        name="Speedrunner",
        description="Win in under 100 turns",
        icon="[FAST]",
        category="efficiency",
    ),
    "heat_master": Achievement(
        id="heat_master",
        name="Heat Master",
        description="Win while staying under 50 heat",
        icon="[HEAT]",
        category="efficiency",
    ),
    "resource_efficient": Achievement(
        id="resource_efficient",
        name="Resource Efficient",
        description="Win without using any code hacks",
        icon="[BOX]",
        category="efficiency",
    ),
    "pure_skill": Achievement(
        id="pure_skill",
        name="Pure Skill",
        description="Win without using exploits or code hacks",
        icon="[BRAIN]",
        category="efficiency",
        hidden=True,
    ),
}


# Category: Challenge Runs
CHALLENGE_ACHIEVEMENTS = {
    "untouchable": Achievement(
        id="untouchable",
        name="Untouchable",
        description="Win without taking any damage",
        icon="[SHIELD]",
        category="challenge",
    ),
    "no_trace": Achievement(
        id="no_trace",
        name="No Trace",
        description="Win without trace level exceeding 50%",
        icon="[SCAN]",
        category="challenge",
    ),
    "minimalist": Achievement(
        id="minimalist",
        name="Minimalist",
        description="Win with only 3 or fewer exploits equipped",
        icon="[CUT]",
        category="challenge",
    ),
    "pacifist": Achievement(
        id="pacifist",
        name="Pacifist",
        description="Complete a level killing 5 or fewer enemies",
        icon="[PEACE]",
        category="challenge",
    ),
}


# Category: Mastery & Collection
MASTERY_ACHIEVEMENTS = {
    "master_hacker": Achievement(
        id="master_hacker",
        name="Master Hacker",
        description="Use all 12 exploits in one run",
        icon="[HACK]",
        category="mastery",
    ),
    "code_collector": Achievement(
        id="code_collector",
        name="Code Collector",
        description="Use all 6 code hack types in one run",
        icon="[BOOK]",
        category="mastery",
    ),
    "enemy_database": Achievement(
        id="enemy_database",
        name="Enemy Database",
        description="Encounter all enemy types in one run",
        icon="[LORE]",
        category="mastery",
    ),
    "explorer": Achievement(
        id="explorer",
        name="Explorer",
        description="Discover all special node types in one run",
        icon="[MAP]",
        category="mastery",
    ),
}


# Category: Lifetime Achievements
LIFETIME_ACHIEVEMENTS = {
    "veteran": Achievement(
        id="veteran",
        name="Veteran",
        description=f"Complete {VETERAN_GAMES_THRESHOLD} games",
        icon="[MEDAL]",
        category="lifetime",
    ),
    "persistent": Achievement(
        id="persistent",
        name="Persistent",
        description=f"Win {PERSISTENT_VICTORIES_THRESHOLD} games",
        icon="[CUP]",
        category="lifetime",
    ),
    "legendary": Achievement(
        id="legendary",
        name="Legendary",
        description=f"Win {LEGENDARY_VICTORIES_THRESHOLD} games",
        icon="[CROWN]",
        category="lifetime",
        hidden=True,
    ),
    "survivor": Achievement(
        id="survivor",
        name="Survivor",
        description=f"Survive {SURVIVOR_TURNS_THRESHOLD}+ turns in a single run",
        icon="[TIME]",
        category="lifetime",
    ),
}


# Category: Ascension Achievements
ASCENSION_ACHIEVEMENTS = {
    "sensor_sweep": Achievement(
        id="sensor_sweep",
        name="Sensor Sweep",
        description="Complete Ascension 5",
        icon="[A5]",
        category="ascension",
    ),
    "firewall_breaker": Achievement(
        id="firewall_breaker",
        name="Firewall Breaker",
        description="Complete Ascension 10",
        icon="[A10]",
        category="ascension",
    ),
    "silent_running": Achievement(
        id="silent_running",
        name="Silent Running",
        description="Complete Ascension 15",
        icon="[A15]",
        category="ascension",
    ),
    "ascension_master": Achievement(
        id="ascension_master",
        name="Ascension Master",
        description="Complete Ascension 20",
        icon="[A20]",
        category="ascension",
    ),
}


# Category: Fun/Hidden Achievements
FUN_ACHIEVEMENTS = {
    "thermal_meltdown": Achievement(
        id="thermal_meltdown",
        name="Thermal Meltdown",
        description="Die from overheating while using System Crash",
        icon="[MELT]",
        category="challenge",
        hidden=True,
    ),
    "own_worst_enemy": Achievement(
        id="own_worst_enemy",
        name="Own Worst Enemy",
        description="Kill yourself with Logic Bomb friendly fire",
        icon="[BOOM]",
        category="challenge",
        hidden=True,
    ),
    "admin_slayer": Achievement(
        id="admin_slayer",
        name="Admin Slayer",
        description="Defeat the Admin Avatar",
        icon="[ADMIN]",
        category="combat",
    ),
    "close_call": Achievement(
        id="close_call",
        name="Close Call",
        description="Win with 5 or less CPU remaining",
        icon="[CLOSE]",
        category="challenge",
    ),
    "cold_blooded": Achievement(
        id="cold_blooded",
        name="Cold Blooded",
        description="Win without ever exceeding 25 heat",
        icon="[COLD]",
        category="efficiency",
    ),
    "floor_is_lava": Achievement(
        id="floor_is_lava",
        name="The Floor is Lava",
        description="Win without stepping on any restoration nodes",
        icon="[LAVA]",
        category="challenge",
        hidden=True,
    ),
    "full_clear": Achievement(
        id="full_clear",
        name="Full Clear",
        description="Eliminate every enemy on a floor",
        icon="[CLEAR]",
        category="combat",
    ),
    "shadow_dancer": Achievement(
        id="shadow_dancer",
        name="Shadow Dancer",
        description="Spend 100+ turns in blind spots in a single run",
        icon="[SHADOW]",
        category="stealth",
    ),
}


# Combine all achievements
ALL_ACHIEVEMENTS: dict[str, Achievement] = {
    **EARLY_GAME_ACHIEVEMENTS,
    **COMBAT_ACHIEVEMENTS,
    **STEALTH_ACHIEVEMENTS,
    **EFFICIENCY_ACHIEVEMENTS,
    **CHALLENGE_ACHIEVEMENTS,
    **MASTERY_ACHIEVEMENTS,
    **LIFETIME_ACHIEVEMENTS,
    **ASCENSION_ACHIEVEMENTS,
    **FUN_ACHIEVEMENTS,
}


# ============================================================================
# ACHIEVEMENT CHECKING LOGIC
# ============================================================================


class AchievementChecker:
    """Checks session/lifetime metrics against achievement conditions."""

    @staticmethod
    def _check_combat_achievements(
        session: SessionMetrics, already_unlocked: set[str], newly_unlocked: list[str]
    ) -> None:
        """
        Check combat achievements (shared by immediate and session checks).

        Args:
            session: SessionMetrics to check
            already_unlocked: Set of achievement IDs already unlocked
            newly_unlocked: List to append newly unlocked achievement IDs
        """
        total_kills = sum(session.enemies_killed.values())

        if "first_blood" not in already_unlocked and total_kills >= 1:
            newly_unlocked.append("first_blood")

        if "massacre" not in already_unlocked and total_kills >= MASSACRE_KILLS_THRESHOLD:
            newly_unlocked.append("massacre")

        if (
            "overkill" not in already_unlocked
            and session.max_single_hit_damage >= OVERKILL_DAMAGE_THRESHOLD
        ):
            newly_unlocked.append("overkill")

        # Check AOE multi-kills (aoe_multi_kills is Counter of {num_enemies: count})
        max_aoe = max(session.aoe_multi_kills.keys(), default=0) if session.aoe_multi_kills else 0
        if "crowd_control" not in already_unlocked and max_aoe >= CROWD_CONTROL_AOE_THRESHOLD:
            newly_unlocked.append("crowd_control")

        # Efficient killer: average kills per turn threshold
        if (
            "efficient_killer" not in already_unlocked
            and session.turns_with_kills >= EFFICIENT_KILLER_TURNS_THRESHOLD
        ):
            avg_kills_per_turn = (
                total_kills / session.turns_with_kills if session.turns_with_kills > 0 else 0
            )
            if avg_kills_per_turn >= EFFICIENT_KILLER_AVG_KILLS:
                newly_unlocked.append("efficient_killer")

    @staticmethod
    def _check_stealth_achievements_immediate(
        session: SessionMetrics, already_unlocked: set[str], newly_unlocked: list[str]
    ) -> None:
        """
        Check stealth achievements that can unlock immediately (shared logic).

        Args:
            session: SessionMetrics to check
            already_unlocked: Set of achievement IDs already unlocked
            newly_unlocked: List to append newly unlocked achievement IDs
        """
        if (
            "silent_assassin" not in already_unlocked
            and session.max_stealth_streak >= SILENT_ASSASSIN_STREAK_THRESHOLD
        ):
            newly_unlocked.append("silent_assassin")

        if (
            "blind_spot_master" not in already_unlocked
            and session.ambushes_from_blind_spots >= BLIND_SPOT_AMBUSHES_THRESHOLD
        ):
            newly_unlocked.append("blind_spot_master")

    @staticmethod
    def _check_early_game_achievements_immediate(
        session: SessionMetrics, already_unlocked: set[str], newly_unlocked: list[str]
    ) -> None:
        """
        Check early game achievements that can unlock immediately during gameplay.

        These are "easy dopamine" achievements for new player engagement.

        Args:
            session: SessionMetrics to check
            already_unlocked: Set of achievement IDs already unlocked
            newly_unlocked: List to append newly unlocked achievement IDs
        """
        total_kills = sum(session.enemies_killed.values())

        # Kill milestones (lower than Massacre)
        if "kill_streak_5" not in already_unlocked and total_kills >= KILL_STREAK_5_THRESHOLD:
            newly_unlocked.append("kill_streak_5")

        if "kill_streak_10" not in already_unlocked and total_kills >= KILL_STREAK_10_THRESHOLD:
            newly_unlocked.append("kill_streak_10")

        # First exploit use
        if "payload_deployed" not in already_unlocked and session.used_any_exploits:
            newly_unlocked.append("payload_deployed")

        # First code hack use
        if "hack_activated" not in already_unlocked and session.used_any_code_hacks:
            newly_unlocked.append("hack_activated")

        # First restoration node use
        if "system_restore" not in already_unlocked and session.restoration_nodes_used >= 1:
            newly_unlocked.append("system_restore")

        # Heat spike (reach 50+ heat)
        if (
            "heat_spike" not in already_unlocked
            and session.highest_heat_reached >= HEAT_SPIKE_THRESHOLD
        ):
            newly_unlocked.append("heat_spike")

    @staticmethod
    def check_immediate_achievements(
        session: SessionMetrics, already_unlocked: set[str]
    ) -> list[str]:
        """
        Check achievements that can be unlocked immediately during gameplay.

        These are achievements that don't require session completion:
        - Combat achievements (kills, damage)
        - Stealth streaks
        - Resource collection milestones

        Args:
            session: Current SessionMetrics (in progress)
            already_unlocked: Set of achievement IDs already unlocked

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        # Combat achievements (immediate)
        AchievementChecker._check_combat_achievements(session, already_unlocked, newly_unlocked)

        # Stealth achievements (immediate)
        AchievementChecker._check_stealth_achievements_immediate(
            session, already_unlocked, newly_unlocked
        )

        # Early game achievements (immediate)
        AchievementChecker._check_early_game_achievements_immediate(
            session, already_unlocked, newly_unlocked
        )

        return newly_unlocked

    @staticmethod
    def check_session_achievements(
        session: SessionMetrics, already_unlocked: set[str]
    ) -> list[str]:
        """
        Check which achievements should be unlocked based on session metrics.

        Args:
            session: SessionMetrics from the completed game session
            already_unlocked: Set of achievement IDs already unlocked (lifetime)

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        # Combat achievements (shared with immediate)
        AchievementChecker._check_combat_achievements(session, already_unlocked, newly_unlocked)

        # Stealth achievements (shared immediate checks)
        AchievementChecker._check_stealth_achievements_immediate(
            session, already_unlocked, newly_unlocked
        )

        # Early game achievements (shared immediate checks)
        AchievementChecker._check_early_game_achievements_immediate(
            session, already_unlocked, newly_unlocked
        )

        # ============================================
        # Early game achievements (session-only)
        # ============================================

        # Network Breach: complete first level
        if "network_breach" not in already_unlocked and session.levels_completed >= 1:
            newly_unlocked.append("network_breach")

        # Victory Protocol: win first game
        if "victory_protocol" not in already_unlocked and session.victory:
            newly_unlocked.append("victory_protocol")

        # System Failure: die for the first time (not a victory = death)
        if "system_failure" not in already_unlocked and not session.victory:
            newly_unlocked.append("system_failure")

        # Stealth achievements (session-only - require level completion or victory)
        if (
            "ghost_protocol" not in already_unlocked
            and session.levels_completed >= 1
            and not session.ever_detected
        ):
            newly_unlocked.append("ghost_protocol")

        if (
            "invisible_victory" not in already_unlocked
            and session.victory
            and not session.ever_detected
        ):
            newly_unlocked.append("invisible_victory")

        # Efficiency achievements
        if "speedrunner" not in already_unlocked and session.victory and session.turns_taken < 100:
            newly_unlocked.append("speedrunner")

        if (
            "heat_master" not in already_unlocked
            and session.victory
            and session.highest_heat_reached < 50
        ):
            newly_unlocked.append("heat_master")

        if (
            "resource_efficient" not in already_unlocked
            and session.victory
            and not session.used_any_code_hacks
        ):
            newly_unlocked.append("resource_efficient")

        if (
            "pure_skill" not in already_unlocked
            and session.victory
            and not session.used_any_exploits
            and not session.used_any_code_hacks
        ):
            newly_unlocked.append("pure_skill")

        # Challenge achievements
        if (
            "untouchable" not in already_unlocked
            and session.victory
            and not session.took_any_damage
        ):
            newly_unlocked.append("untouchable")

        # No trace (trace level < 50% throughout)
        # Uses highest_trace_reached to track the maximum trace level during the run
        if "no_trace" not in already_unlocked and session.victory:
            if session.highest_trace_reached < 50:
                newly_unlocked.append("no_trace")

        # Minimalist: win with 3 or fewer unique exploits equipped
        # If player never changed equipment (exploits_equipped is empty), check if they used <= 3 exploits total
        # If player did change equipment, check if they equipped <= 3 unique exploits
        if "minimalist" not in already_unlocked and session.victory:
            unique_equipped = len(session.exploits_equipped)
            unique_used = len(session.exploits_used)

            # Award if player used minimal exploits (never changed equipment or equipped few)
            if (unique_equipped == 0 and unique_used <= 3) or (
                unique_equipped > 0 and unique_equipped <= 3
            ):
                newly_unlocked.append("minimalist")

        # Pacifist: complete a level with 5 or fewer kills on that level
        if (
            "pacifist" not in already_unlocked
            and session.levels_completed >= 1
            and session.min_kills_any_level is not None
            and session.min_kills_any_level <= 5
        ):
            newly_unlocked.append("pacifist")

        # Mastery achievements
        if (
            "master_hacker" not in already_unlocked
            and len(session.unique_exploits_used_this_run) >= TOTAL_EXPLOITS
        ):
            newly_unlocked.append("master_hacker")

        if (
            "code_collector" not in already_unlocked
            and len(session.unique_code_hacks_used_this_run) >= TOTAL_CODE_HACK_TYPES
        ):
            newly_unlocked.append("code_collector")

        # Enemy database - need to check total enemy types
        # Assuming there are multiple enemy types in game_content.json
        if (
            "enemy_database" not in already_unlocked
            and len(session.unique_enemies_encountered) >= ENEMY_DATABASE_UNIQUE_THRESHOLD
        ):
            newly_unlocked.append("enemy_database")

        # Explorer - special nodes discovered
        if (
            "explorer" not in already_unlocked
            and len(session.special_nodes_discovered) >= EXPLORER_NODES_THRESHOLD
        ):
            newly_unlocked.append("explorer")

        # Survivor - 500+ turns
        if "survivor" not in already_unlocked and session.turns_taken >= SURVIVOR_TURNS_THRESHOLD:
            newly_unlocked.append("survivor")

        # ============================================
        # Ascension achievements
        # ============================================
        if session.victory and session.ascension_level >= 5:
            if "sensor_sweep" not in already_unlocked:
                newly_unlocked.append("sensor_sweep")
        if session.victory and session.ascension_level >= 10:
            if "firewall_breaker" not in already_unlocked:
                newly_unlocked.append("firewall_breaker")
        if session.victory and session.ascension_level >= 15:
            if "silent_running" not in already_unlocked:
                newly_unlocked.append("silent_running")
        if session.victory and session.ascension_level >= 20:
            if "ascension_master" not in already_unlocked:
                newly_unlocked.append("ascension_master")

        # ============================================
        # Fun/hidden achievements
        # ============================================

        # Thermal Meltdown: die from overheat while using System Crash
        if session.death_cause == "overheat" and session.last_exploit_used == "system_crash":
            if "thermal_meltdown" not in already_unlocked:
                newly_unlocked.append("thermal_meltdown")

        # Own Worst Enemy: kill yourself with Logic Bomb
        if session.death_cause == "self_damage" and session.last_exploit_used == "logic_bomb":
            if "own_worst_enemy" not in already_unlocked:
                newly_unlocked.append("own_worst_enemy")

        # Admin Slayer: defeat the Admin Avatar
        if session.admin_kills > 0:
            if "admin_slayer" not in already_unlocked:
                newly_unlocked.append("admin_slayer")

        # Close Call: win with 5 or less CPU
        if session.victory and session.final_cpu <= 5:
            if "close_call" not in already_unlocked:
                newly_unlocked.append("close_call")

        # Cold Blooded: win without exceeding 25 heat
        if session.victory and session.highest_heat_reached <= 25:
            if "cold_blooded" not in already_unlocked:
                newly_unlocked.append("cold_blooded")

        # Floor is Lava: win without using restoration nodes
        if session.victory and session.restoration_nodes_used == 0:
            if "floor_is_lava" not in already_unlocked:
                newly_unlocked.append("floor_is_lava")

        # Full Clear: eliminate all enemies on a floor
        if session.full_floor_clears > 0:
            if "full_clear" not in already_unlocked:
                newly_unlocked.append("full_clear")

        # Shadow Dancer: spend 100+ turns in blind spots
        if session.turns_in_blind_spots >= 100:
            if "shadow_dancer" not in already_unlocked:
                newly_unlocked.append("shadow_dancer")

        return newly_unlocked

    @staticmethod
    def check_lifetime_achievements(
        lifetime: LifetimeMetrics, already_unlocked: set[str]
    ) -> list[str]:
        """
        Check lifetime achievements based on cumulative stats.

        Args:
            lifetime: LifetimeMetrics from player's career
            already_unlocked: Set of achievement IDs already unlocked

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        # Early game: complete 3 games (before veteran's 10)
        if "rookie" not in already_unlocked and lifetime.total_games >= ROOKIE_GAMES_THRESHOLD:
            newly_unlocked.append("rookie")

        if "veteran" not in already_unlocked and lifetime.total_games >= VETERAN_GAMES_THRESHOLD:
            newly_unlocked.append("veteran")

        if (
            "persistent" not in already_unlocked
            and lifetime.total_victories >= PERSISTENT_VICTORIES_THRESHOLD
        ):
            newly_unlocked.append("persistent")

        if (
            "legendary" not in already_unlocked
            and lifetime.total_victories >= LEGENDARY_VICTORIES_THRESHOLD
        ):
            newly_unlocked.append("legendary")

        return newly_unlocked


# ============================================================================
# ACHIEVEMENT MANAGER
# ============================================================================


class AchievementManager:
    """
    Central manager for achievement unlocking and notification.

    This is called after a game session ends to check for newly unlocked achievements.
    Works with the popup system to display achievement notifications.
    """

    _unlocked_achievements: set[str] = set()  # Loaded from progress.json
    _pending_popups: list[str] = []  # Achievement IDs waiting to be shown

    @classmethod
    def reset(cls):
        """Reset all achievement state. Used for testing and new game sessions."""
        cls._unlocked_achievements = set()
        cls._pending_popups = []

    @classmethod
    def load_unlocked_achievements(cls, unlocked_list: list[str]):
        """Load the list of already-unlocked achievements from progress.json."""
        cls._unlocked_achievements = set(unlocked_list)
        logger.info(f"Loaded {len(cls._unlocked_achievements)} unlocked achievements")

    @classmethod
    def get_unlocked_achievements(cls) -> list[str]:
        """Get the current list of unlocked achievements."""
        return list(cls._unlocked_achievements)

    @classmethod
    def check_achievements(
        cls, session: SessionMetrics, lifetime: LifetimeMetrics | None = None
    ) -> list[str]:
        """
        Check for newly unlocked achievements and queue popups.

        Args:
            session: SessionMetrics from the completed game
            lifetime: Optional LifetimeMetrics for lifetime achievements

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        # Check session-based achievements
        session_unlocks = AchievementChecker.check_session_achievements(
            session, cls._unlocked_achievements
        )
        newly_unlocked.extend(session_unlocks)

        # Check lifetime-based achievements
        if lifetime:
            lifetime_unlocks = AchievementChecker.check_lifetime_achievements(
                lifetime, cls._unlocked_achievements
            )
            newly_unlocked.extend(lifetime_unlocks)

        # Add to unlocked set and pending popups
        for achievement_id in newly_unlocked:
            cls._unlocked_achievements.add(achievement_id)
            cls._pending_popups.append(achievement_id)
            logger.info(f"Achievement unlocked: {achievement_id}")

        return newly_unlocked

    @classmethod
    def check_immediate_achievements_and_notify(
        cls, session: SessionMetrics, game_engine
    ) -> list[str]:
        """
        Check for immediately unlockable achievements during gameplay and show popups.

        This is called during gameplay (e.g., after killing an enemy) to provide
        instant feedback for achievements like First Blood, Massacre, Overkill, etc.

        Args:
            session: Current SessionMetrics (in progress)
            game_engine: GameEngine instance to access achievement_popup_manager

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        # Check immediate achievements
        immediate_unlocks = AchievementChecker.check_immediate_achievements(
            session, cls._unlocked_achievements
        )

        # Add to unlocked set and queue popups
        for achievement_id in immediate_unlocks:
            cls._unlocked_achievements.add(achievement_id)
            newly_unlocked.append(achievement_id)

            # Show popup immediately if popup manager exists
            if hasattr(game_engine, "achievement_popup_manager"):
                game_engine.achievement_popup_manager.show_popup(achievement_id)

            logger.info(f"Achievement unlocked (immediate): {achievement_id}")

        # Save progress immediately
        if newly_unlocked:
            from game_metrics import save_unlocked_achievements

            save_unlocked_achievements(list(cls._unlocked_achievements))

        return newly_unlocked

    @classmethod
    def has_pending_popups(cls) -> bool:
        """Check if there are achievement popups waiting to be shown."""
        return len(cls._pending_popups) > 0

    @classmethod
    def get_next_popup(cls) -> str | None:
        """Get the next achievement ID to display as a popup."""
        if cls._pending_popups:
            return cls._pending_popups.pop(0)
        return None

    @classmethod
    def clear_pending_popups(cls):
        """Clear all pending achievement popups (e.g., when returning to menu)."""
        cls._pending_popups.clear()

    @classmethod
    def is_unlocked(cls, achievement_id: str) -> bool:
        """Check if a specific achievement is unlocked."""
        return achievement_id in cls._unlocked_achievements

    @classmethod
    def get_achievement_info(cls, achievement_id: str) -> Achievement | None:
        """Get achievement details by ID."""
        return ALL_ACHIEVEMENTS.get(achievement_id)

    @classmethod
    def get_achievements_by_category(cls, category: str) -> list[Achievement]:
        """Get all achievements in a specific category."""
        return [
            achievement
            for achievement in ALL_ACHIEVEMENTS.values()
            if achievement.category == category
        ]

    @classmethod
    def get_unlock_progress(cls) -> tuple[int, int]:
        """Get (unlocked_count, total_count) for progress display."""
        return len(cls._unlocked_achievements), len(ALL_ACHIEVEMENTS)

    @classmethod
    def get_achievement_progress(
        cls, achievement_id: str, session=None, lifetime=None
    ) -> tuple[int, int] | None:
        """
        Get progress towards an achievement as (current, target).

        Returns None if achievement has no trackable progress (e.g., victory-based).
        Only shows progress for unlocked achievements if they have cumulative tracking.

        Args:
            achievement_id: The achievement to check
            session: Optional SessionMetrics for in-progress tracking
            lifetime: Optional LifetimeMetrics for lifetime achievements

        Returns:
            (current_value, target_value) or None if not trackable
        """
        # Already unlocked - no progress needed
        if cls.is_unlocked(achievement_id):
            return None

        # Combat achievements
        if achievement_id == "massacre":
            if session:
                kills = sum(session.enemies_killed.values())
                return (kills, MASSACRE_KILLS_THRESHOLD)
            return (0, MASSACRE_KILLS_THRESHOLD)

        if achievement_id == "overkill":
            if session:
                return (session.max_single_hit_damage, OVERKILL_DAMAGE_THRESHOLD)
            return (0, OVERKILL_DAMAGE_THRESHOLD)

        if achievement_id == "crowd_control":
            if session and session.aoe_multi_kills:
                max_aoe = max(session.aoe_multi_kills.keys(), default=0)
                return (max_aoe, CROWD_CONTROL_AOE_THRESHOLD)
            return (0, CROWD_CONTROL_AOE_THRESHOLD)

        if achievement_id == "efficient_killer":
            # Track turns_with_kills toward the threshold
            # Once threshold is met, the average kills per turn determines unlock
            if session:
                return (session.turns_with_kills, EFFICIENT_KILLER_TURNS_THRESHOLD)
            return (0, EFFICIENT_KILLER_TURNS_THRESHOLD)

        # Early game achievements (kill milestones)
        if achievement_id == "kill_streak_5":
            if session:
                kills = sum(session.enemies_killed.values())
                return (kills, KILL_STREAK_5_THRESHOLD)
            return (0, KILL_STREAK_5_THRESHOLD)

        if achievement_id == "kill_streak_10":
            if session:
                kills = sum(session.enemies_killed.values())
                return (kills, KILL_STREAK_10_THRESHOLD)
            return (0, KILL_STREAK_10_THRESHOLD)

        if achievement_id == "heat_spike":
            if session:
                return (session.highest_heat_reached, HEAT_SPIKE_THRESHOLD)
            return (0, HEAT_SPIKE_THRESHOLD)

        # Stealth achievements
        if achievement_id == "silent_assassin":
            if session:
                return (session.max_stealth_streak, SILENT_ASSASSIN_STREAK_THRESHOLD)
            return (0, SILENT_ASSASSIN_STREAK_THRESHOLD)

        if achievement_id == "blind_spot_master":
            if session:
                return (session.ambushes_from_blind_spots, BLIND_SPOT_AMBUSHES_THRESHOLD)
            return (0, BLIND_SPOT_AMBUSHES_THRESHOLD)

        # Mastery achievements
        if achievement_id == "master_hacker":
            if session:
                return (len(session.unique_exploits_used_this_run), TOTAL_EXPLOITS)
            return (0, TOTAL_EXPLOITS)

        if achievement_id == "code_collector":
            if session:
                return (len(session.unique_code_hacks_used_this_run), TOTAL_CODE_HACK_TYPES)
            return (0, TOTAL_CODE_HACK_TYPES)

        if achievement_id == "enemy_database":
            if session:
                return (len(session.unique_enemies_encountered), ENEMY_DATABASE_UNIQUE_THRESHOLD)
            return (0, ENEMY_DATABASE_UNIQUE_THRESHOLD)

        if achievement_id == "explorer":
            if session:
                return (len(session.special_nodes_discovered), EXPLORER_NODES_THRESHOLD)
            return (0, EXPLORER_NODES_THRESHOLD)

        # Lifetime achievements
        if achievement_id == "rookie":
            if lifetime:
                return (lifetime.total_games, ROOKIE_GAMES_THRESHOLD)
            return (0, ROOKIE_GAMES_THRESHOLD)

        if achievement_id == "veteran":
            if lifetime:
                return (lifetime.total_games, VETERAN_GAMES_THRESHOLD)
            return (0, VETERAN_GAMES_THRESHOLD)

        if achievement_id == "persistent":
            if lifetime:
                return (lifetime.total_victories, PERSISTENT_VICTORIES_THRESHOLD)
            return (0, PERSISTENT_VICTORIES_THRESHOLD)

        if achievement_id == "legendary":
            if lifetime:
                return (lifetime.total_victories, LEGENDARY_VICTORIES_THRESHOLD)
            return (0, LEGENDARY_VICTORIES_THRESHOLD)

        if achievement_id == "survivor":
            if session:
                return (session.turns_taken, SURVIVOR_TURNS_THRESHOLD)
            return (0, SURVIVOR_TURNS_THRESHOLD)

        # Challenge achievements with trackable progress
        if achievement_id == "shadow_dancer":
            if session:
                return (session.turns_in_blind_spots, 100)
            return (0, 100)

        # No trackable progress for other achievements
        return None
