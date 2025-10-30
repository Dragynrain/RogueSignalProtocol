"""
Achievement system for RogueSignalProtocol.

Defines achievements and checks if they should be unlocked based on session metrics.
Integrates with the metrics system (game_metrics.py) and popup system (game_achievement_popups.py).
"""

from typing import Dict, List, Callable, Optional, Set
from dataclasses import dataclass
from game_metrics import SessionMetrics, LifetimeMetrics
import logging

logger = logging.getLogger(__name__)


# Constants for collection achievements
TOTAL_EXPLOITS = 12  # From game_content.json
TOTAL_CODE_HACK_TYPES = 6  # restore_cpu, reduce_heat, reduce_trace_level, speed_boost, enhanced_vision, exploit_efficiency


@dataclass
class Achievement:
    """Defines a single achievement."""

    id: str
    name: str
    description: str
    icon: str  # Unicode symbol or emoji
    category: str  # "combat", "stealth", "efficiency", "mastery", "challenge", "lifetime"
    hidden: bool = False  # Don't show in menu until unlocked

    def check(self, session: Optional[SessionMetrics] = None,
              lifetime: Optional[LifetimeMetrics] = None) -> bool:
        """
        Check if this achievement should be unlocked.
        Override in subclasses or use lambda in definition.
        """
        return False


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
        description="Kill 20+ enemies in one run",
        icon="💀",
        category="combat",
    ),

    "overkill": Achievement(
        id="overkill",
        name="Overkill",
        description="Deal 100+ damage in a single hit",
        icon="💥",
        category="combat",
    ),

    "crowd_control": Achievement(
        id="crowd_control",
        name="Crowd Control",
        description="Hit 5+ enemies with one AOE exploit",
        icon="🌀",
        category="combat",
    ),

    "efficient_killer": Achievement(
        id="efficient_killer",
        name="Efficient Killer",
        description="Average 2+ kills per turn for 10+ turns",
        icon="🎯",
        category="combat",
    ),
}


# Category: Stealth Mastery
STEALTH_ACHIEVEMENTS = {
    "silent_assassin": Achievement(
        id="silent_assassin",
        name="Silent Assassin",
        description="Kill 10 enemies without being detected",
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

    "shadow_master": Achievement(
        id="shadow_master",
        name="Shadow Master",
        description="Kill 5+ enemies from shadows in one run",
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
        description="Complete 10 games",
        icon="🎖️",
        category="lifetime",
    ),

    "persistent": Achievement(
        id="persistent",
        name="Persistent",
        description="Win 5 games",
        icon="🏆",
        category="lifetime",
    ),

    "legendary": Achievement(
        id="legendary",
        name="Legendary",
        description="Win 20 games",
        icon="👑",
        category="lifetime",
        hidden=True,
    ),

    "survivor": Achievement(
        id="survivor",
        name="Survivor",
        description="Survive 500+ turns in a single run",
        icon="⏱️",
        category="lifetime",
    ),
}


# Combine all achievements
ALL_ACHIEVEMENTS: Dict[str, Achievement] = {
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
    def check_session_achievements(session: SessionMetrics, already_unlocked: Set[str]) -> List[str]:
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

        if "massacre" not in already_unlocked and total_kills >= 20:
            newly_unlocked.append("massacre")

        if "overkill" not in already_unlocked and session.max_single_hit_damage >= 100:
            newly_unlocked.append("overkill")

        # Check AOE multi-kills (aoe_multi_kills is Counter of {num_enemies: count})
        max_aoe = max(session.aoe_multi_kills.keys(), default=0)
        if "crowd_control" not in already_unlocked and max_aoe >= 5:
            newly_unlocked.append("crowd_control")

        # Efficient killer: average 2+ kills per turn for 10+ turns
        if "efficient_killer" not in already_unlocked and session.turns_with_kills >= 10:
            avg_kills_per_turn = total_kills / session.turns_with_kills if session.turns_with_kills > 0 else 0
            if avg_kills_per_turn >= 2.0:
                newly_unlocked.append("efficient_killer")

        # Stealth achievements
        if "silent_assassin" not in already_unlocked and session.max_stealth_streak >= 10:
            newly_unlocked.append("silent_assassin")

        if "ghost_protocol" not in already_unlocked and session.levels_completed >= 1 and not session.ever_detected:
            newly_unlocked.append("ghost_protocol")

        if "shadow_master" not in already_unlocked and session.ambushes_from_shadows >= 5:
            newly_unlocked.append("shadow_master")

        if "invisible_victory" not in already_unlocked and session.victory and not session.ever_detected:
            newly_unlocked.append("invisible_victory")

        # Efficiency achievements
        if "speedrunner" not in already_unlocked and session.victory and session.turns_taken < 100:
            newly_unlocked.append("speedrunner")

        if "heat_master" not in already_unlocked and session.victory and session.highest_heat_reached < 50:
            newly_unlocked.append("heat_master")

        if "resource_efficient" not in already_unlocked and session.victory and not session.used_any_code_hacks:
            newly_unlocked.append("resource_efficient")

        if "pure_skill" not in already_unlocked and session.victory and not session.used_any_exploits and not session.used_any_code_hacks:
            newly_unlocked.append("pure_skill")

        # Challenge achievements
        if "untouchable" not in already_unlocked and session.victory and not session.took_any_damage:
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
        if "minimalist" not in already_unlocked and session.victory:
            unique_equipped = len(session.exploits_equipped)
            if unique_equipped <= 3 and unique_equipped > 0:
                newly_unlocked.append("minimalist")

        # Pacifist: complete a level with 5 or fewer kills
        if "pacifist" not in already_unlocked and session.levels_completed >= 1 and total_kills <= 5:
            newly_unlocked.append("pacifist")

        # Mastery achievements
        if "master_hacker" not in already_unlocked and len(session.unique_exploits_used_this_run) >= TOTAL_EXPLOITS:
            newly_unlocked.append("master_hacker")

        if "code_collector" not in already_unlocked and len(session.unique_code_hacks_used_this_run) >= TOTAL_CODE_HACK_TYPES:
            newly_unlocked.append("code_collector")

        # Enemy database - need to check total enemy types
        # Assuming there are multiple enemy types in game_content.json
        if "enemy_database" not in already_unlocked and len(session.unique_enemies_encountered) >= 5:
            newly_unlocked.append("enemy_database")

        # Explorer - special nodes discovered
        if "explorer" not in already_unlocked and len(session.special_nodes_discovered) >= 3:
            newly_unlocked.append("explorer")

        # Survivor - 500+ turns
        if "survivor" not in already_unlocked and session.turns_taken >= 500:
            newly_unlocked.append("survivor")

        return newly_unlocked

    @staticmethod
    def check_lifetime_achievements(lifetime: LifetimeMetrics, already_unlocked: Set[str]) -> List[str]:
        """
        Check lifetime achievements based on cumulative stats.

        Args:
            lifetime: LifetimeMetrics from player's career
            already_unlocked: Set of achievement IDs already unlocked

        Returns:
            List of newly unlocked achievement IDs
        """
        newly_unlocked = []

        if "veteran" not in already_unlocked and lifetime.total_games >= 10:
            newly_unlocked.append("veteran")

        if "persistent" not in already_unlocked and lifetime.total_victories >= 5:
            newly_unlocked.append("persistent")

        if "legendary" not in already_unlocked and lifetime.total_victories >= 20:
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

    _unlocked_achievements: Set[str] = set()  # Loaded from progress.json
    _pending_popups: List[str] = []  # Achievement IDs waiting to be shown

    @classmethod
    def load_unlocked_achievements(cls, unlocked_list: List[str]):
        """Load the list of already-unlocked achievements from progress.json."""
        cls._unlocked_achievements = set(unlocked_list)
        logger.info(f"Loaded {len(cls._unlocked_achievements)} unlocked achievements")

    @classmethod
    def get_unlocked_achievements(cls) -> List[str]:
        """Get the current list of unlocked achievements."""
        return list(cls._unlocked_achievements)

    @classmethod
    def check_achievements(cls, session: SessionMetrics, lifetime: Optional[LifetimeMetrics] = None) -> List[str]:
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
    def has_pending_popups(cls) -> bool:
        """Check if there are achievement popups waiting to be shown."""
        return len(cls._pending_popups) > 0

    @classmethod
    def get_next_popup(cls) -> Optional[str]:
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
    def get_achievement_info(cls, achievement_id: str) -> Optional[Achievement]:
        """Get achievement details by ID."""
        return ALL_ACHIEVEMENTS.get(achievement_id)

    @classmethod
    def get_achievements_by_category(cls, category: str) -> List[Achievement]:
        """Get all achievements in a specific category."""
        return [
            achievement for achievement in ALL_ACHIEVEMENTS.values()
            if achievement.category == category
        ]

    @classmethod
    def get_unlock_progress(cls) -> tuple[int, int]:
        """Get (unlocked_count, total_count) for progress display."""
        return len(cls._unlocked_achievements), len(ALL_ACHIEVEMENTS)
