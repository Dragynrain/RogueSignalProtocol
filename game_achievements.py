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
TOTAL_CODE_HACK_TYPES = 6  # restore_cpu, reduce_heat, reduce_trace_level, speed_boost, enhanced_vision, exploit_efficiency

# Achievement threshold constants
# Combat
MASSACRE_KILLS_THRESHOLD = 20
OVERKILL_DAMAGE_THRESHOLD = 50
CROWD_CONTROL_AOE_THRESHOLD = 5
EFFICIENT_KILLER_TURNS_THRESHOLD = 10
EFFICIENT_KILLER_AVG_KILLS = 2.0

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

# Category: Combat Mastery
COMBAT_ACHIEVEMENTS = {
    "first_blood": Achievement(
        id="first_blood",
        name="First Blood",
        description="Kill your first enemy",
        icon="⚔️",
        category="combat",
    ),
    "massacre": Achievement(
        id="massacre",
        name="Massacre",
        description=f"Kill {MASSACRE_KILLS_THRESHOLD}+ enemies in one run",
        icon="💀",
        category="combat",
    ),
    "overkill": Achievement(
        id="overkill",
        name="Overkill",
        description=f"Deal {OVERKILL_DAMAGE_THRESHOLD}+ damage in a single hit",
        icon="💥",
        category="combat",
    ),
    "crowd_control": Achievement(
        id="crowd_control",
        name="Crowd Control",
        description=f"Hit {CROWD_CONTROL_AOE_THRESHOLD}+ enemies with one AOE exploit",
        icon="🌀",
        category="combat",
    ),
    "efficient_killer": Achievement(
        id="efficient_killer",
        name="Efficient Killer",
        description=f"Average {int(EFFICIENT_KILLER_AVG_KILLS)}+ kills per turn for {EFFICIENT_KILLER_TURNS_THRESHOLD}+ turns",
        icon="🎯",
        category="combat",
    ),
}


# Category: Stealth Mastery
STEALTH_ACHIEVEMENTS = {
    "silent_assassin": Achievement(
        id="silent_assassin",
        name="Silent Assassin",
        description=f"Kill {SILENT_ASSASSIN_STREAK_THRESHOLD} enemies without being detected",
        icon="🔪",
        category="stealth",
    ),
    "ghost_protocol": Achievement(
        id="ghost_protocol",
        name="Ghost Protocol",
        description="Complete a level without being detected",
        icon="👻",
        category="stealth",
    ),
    "blind_spot_master": Achievement(
        id="blind_spot_master",
        name="Blind Spot Master",
        description=f"Kill {BLIND_SPOT_AMBUSHES_THRESHOLD}+ enemies from blind spots in one run",
        icon="🌑",
        category="stealth",
    ),
    "invisible_victory": Achievement(
        id="invisible_victory",
        name="Invisible Victory",
        description="Win the game without ever being detected",
        icon="🕶️",
        category="stealth",
    ),
}


# Category: Efficiency & Speed
EFFICIENCY_ACHIEVEMENTS = {
    "speedrunner": Achievement(
        id="speedrunner",
        name="Speedrunner",
        description="Win in under 100 turns",
        icon="⚡",
        category="efficiency",
    ),
    "heat_master": Achievement(
        id="heat_master",
        name="Heat Master",
        description="Win while staying under 50 heat",
        icon="🔥",
        category="efficiency",
    ),
    "resource_efficient": Achievement(
        id="resource_efficient",
        name="Resource Efficient",
        description="Win without using any code hacks",
        icon="📦",
        category="efficiency",
    ),
    "pure_skill": Achievement(
        id="pure_skill",
        name="Pure Skill",
        description="Win without using exploits or code hacks",
        icon="🧠",
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
        icon="🛡️",
        category="challenge",
    ),
    "no_trace": Achievement(
        id="no_trace",
        name="No Trace",
        description="Win without trace level exceeding 50%",
        icon="🔍",
        category="challenge",
    ),
    "minimalist": Achievement(
        id="minimalist",
        name="Minimalist",
        description="Win with only 3 or fewer exploits equipped",
        icon="✂️",
        category="challenge",
    ),
    "pacifist": Achievement(
        id="pacifist",
        name="Pacifist",
        description="Complete a level killing 5 or fewer enemies",
        icon="☮️",
        category="challenge",
    ),
}


# Category: Mastery & Collection
MASTERY_ACHIEVEMENTS = {
    "master_hacker": Achievement(
        id="master_hacker",
        name="Master Hacker",
        description="Use all 12 exploits in one run",
        icon="💻",
        category="mastery",
    ),
    "code_collector": Achievement(
        id="code_collector",
        name="Code Collector",
        description="Use all 6 code hack types in one run",
        icon="📚",
        category="mastery",
    ),
    "enemy_database": Achievement(
        id="enemy_database",
        name="Enemy Database",
        description="Encounter all enemy types in one run",
        icon="📖",
        category="mastery",
    ),
    "explorer": Achievement(
        id="explorer",
        name="Explorer",
        description="Discover all special node types in one run",
        icon="🗺️",
        category="mastery",
    ),
}


# Category: Lifetime Achievements
LIFETIME_ACHIEVEMENTS = {
    "veteran": Achievement(
        id="veteran",
        name="Veteran",
        description=f"Complete {VETERAN_GAMES_THRESHOLD} games",
        icon="🎖️",
        category="lifetime",
    ),
    "persistent": Achievement(
        id="persistent",
        name="Persistent",
        description=f"Win {PERSISTENT_VICTORIES_THRESHOLD} games",
        icon="🏆",
        category="lifetime",
    ),
    "legendary": Achievement(
        id="legendary",
        name="Legendary",
        description=f"Win {LEGENDARY_VICTORIES_THRESHOLD} games",
        icon="👑",
        category="lifetime",
        hidden=True,
    ),
    "survivor": Achievement(
        id="survivor",
        name="Survivor",
        description=f"Survive {SURVIVOR_TURNS_THRESHOLD}+ turns in a single run",
        icon="⏱️",
        category="lifetime",
    ),
}


# Combine all achievements
ALL_ACHIEVEMENTS: dict[str, Achievement] = {
    **COMBAT_ACHIEVEMENTS,
    **STEALTH_ACHIEVEMENTS,
    **EFFICIENCY_ACHIEVEMENTS,
    **CHALLENGE_ACHIEVEMENTS,
    **MASTERY_ACHIEVEMENTS,
    **LIFETIME_ACHIEVEMENTS,
}


# ============================================================================
# ACHIEVEMENT CHECKING LOGIC
# ============================================================================


class AchievementChecker:
    """Checks session/lifetime metrics against achievement conditions."""

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
        total_kills = sum(session.enemies_killed.values())

        if "first_blood" not in already_unlocked and total_kills >= 1:
            newly_unlocked.append("first_blood")

        if "massacre" not in already_unlocked and total_kills >= MASSACRE_KILLS_THRESHOLD:
            newly_unlocked.append("massacre")

        if "overkill" not in already_unlocked and session.max_single_hit_damage >= OVERKILL_DAMAGE_THRESHOLD:
            newly_unlocked.append("overkill")

        # Check AOE multi-kills
        max_aoe = max(session.aoe_multi_kills.keys(), default=0)
        if "crowd_control" not in already_unlocked and max_aoe >= CROWD_CONTROL_AOE_THRESHOLD:
            newly_unlocked.append("crowd_control")

        # Efficient killer: average 2+ kills per turn for 10+ turns
        if "efficient_killer" not in already_unlocked and session.turns_with_kills >= EFFICIENT_KILLER_TURNS_THRESHOLD:
            avg_kills_per_turn = (
                total_kills / session.turns_with_kills if session.turns_with_kills > 0 else 0
            )
            if avg_kills_per_turn >= EFFICIENT_KILLER_AVG_KILLS:
                newly_unlocked.append("efficient_killer")

        # Stealth achievements (immediate)
        if "silent_assassin" not in already_unlocked and session.max_stealth_streak >= SILENT_ASSASSIN_STREAK_THRESHOLD:
            newly_unlocked.append("silent_assassin")

        if "blind_spot_master" not in already_unlocked and session.ambushes_from_blind_spots >= BLIND_SPOT_AMBUSHES_THRESHOLD:
            newly_unlocked.append("blind_spot_master")

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

        # Combat achievements
        total_kills = sum(session.enemies_killed.values())

        if "first_blood" not in already_unlocked and total_kills >= 1:
            newly_unlocked.append("first_blood")

        if "massacre" not in already_unlocked and total_kills >= MASSACRE_KILLS_THRESHOLD:
            newly_unlocked.append("massacre")

        if "overkill" not in already_unlocked and session.max_single_hit_damage >= OVERKILL_DAMAGE_THRESHOLD:
            newly_unlocked.append("overkill")

        # Check AOE multi-kills (aoe_multi_kills is Counter of {num_enemies: count})
        max_aoe = max(session.aoe_multi_kills.keys(), default=0)
        if "crowd_control" not in already_unlocked and max_aoe >= CROWD_CONTROL_AOE_THRESHOLD:
            newly_unlocked.append("crowd_control")

        # Efficient killer: average 2+ kills per turn for 10+ turns
        if "efficient_killer" not in already_unlocked and session.turns_with_kills >= EFFICIENT_KILLER_TURNS_THRESHOLD:
            avg_kills_per_turn = (
                total_kills / session.turns_with_kills if session.turns_with_kills > 0 else 0
            )
            if avg_kills_per_turn >= EFFICIENT_KILLER_AVG_KILLS:
                newly_unlocked.append("efficient_killer")

        # Stealth achievements
        if "silent_assassin" not in already_unlocked and session.max_stealth_streak >= SILENT_ASSASSIN_STREAK_THRESHOLD:
            newly_unlocked.append("silent_assassin")

        if (
            "ghost_protocol" not in already_unlocked
            and session.levels_completed >= 1
            and not session.ever_detected
        ):
            newly_unlocked.append("ghost_protocol")

        if "blind_spot_master" not in already_unlocked and session.ambushes_from_blind_spots >= BLIND_SPOT_AMBUSHES_THRESHOLD:
            newly_unlocked.append("blind_spot_master")

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
        # Trace goes from 0-100, so 50% = 50
        if "no_trace" not in already_unlocked and session.victory:
            # We need a new metric for max trace reached, let's use trace_increases as proxy
            # If trace never exceeded 50, they should have very few trace increases
            # For now, check if they won with low trace events
            if session.trace_increases < 5:  # Rough heuristic
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

        # Pacifist: complete a level with 5 or fewer kills
        if (
            "pacifist" not in already_unlocked
            and session.levels_completed >= 1
            and total_kills <= 5
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
        if "explorer" not in already_unlocked and len(session.special_nodes_discovered) >= EXPLORER_NODES_THRESHOLD:
            newly_unlocked.append("explorer")

        # Survivor - 500+ turns
        if "survivor" not in already_unlocked and session.turns_taken >= SURVIVOR_TURNS_THRESHOLD:
            newly_unlocked.append("survivor")

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

        if "veteran" not in already_unlocked and lifetime.total_games >= VETERAN_GAMES_THRESHOLD:
            newly_unlocked.append("veteran")

        if "persistent" not in already_unlocked and lifetime.total_victories >= PERSISTENT_VICTORIES_THRESHOLD:
            newly_unlocked.append("persistent")

        if "legendary" not in already_unlocked and lifetime.total_victories >= LEGENDARY_VICTORIES_THRESHOLD:
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
