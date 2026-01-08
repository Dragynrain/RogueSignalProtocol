"""
Metrics tracking system for RogueSignalProtocol.

Tracks all gameplay events for future achievement system and game balance analytics.
Uses dual storage (JSON + SQLite) with lifetime statistics that survive permadeath.
"""

import json
import logging
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from rsp.core.errors import GameErrorHandler
from rsp.core.file_paths import get_data_directory

# Max JSON files to keep
MAX_JSON_FILES = 100


def _get_metrics_dir() -> Path:
    """Get the metrics directory path (supports portable/AppData modes)."""
    return get_data_directory() / "metrics"


def _get_session_db_path() -> Path:
    """Get the session database path (supports portable/AppData modes)."""
    return _get_metrics_dir() / "sessions.db"


def _get_progress_file_path() -> Path:
    """Get the progress file path (supports portable/AppData modes)."""
    return get_data_directory() / "saves" / "rogue_signal_progress.json"


# Global metrics instance (initialized by GameEngine)
_current_session: Optional["SessionMetrics"] = None
_session_finalized: bool = False  # Guard against double finalization


@dataclass
class SessionMetrics:
    """Tracks metrics for a single game session."""

    session_id: str
    timestamp_start: float
    victory: bool = False
    death_cause: str | None = None  # "combat", "overheat", "virus", "self_damage"
    death_level: int = 0

    # Ascension tracking
    ascension_level: int = 0

    # Achievement tracking (for ascension achievements)
    last_exploit_used: str | None = None  # Track last exploit for death context
    admin_kills: int = 0  # For admin_slayer achievement
    final_cpu: int = 0  # Set in finalize_session(), for close_call achievement
    restoration_nodes_used: int = 0  # For floor_is_lava achievement
    full_floor_clears: int = 0  # For full_clear achievement

    # Combat
    enemies_killed: Counter = field(default_factory=Counter)
    damage_dealt: int = 0
    damage_taken: int = 0
    stealth_kills: int = 0

    # Per-level tracking for pacifist achievement
    kills_current_level: int = 0  # Reset when level completes
    min_kills_any_level: int | None = None  # Lowest kills on any completed level

    # Exploration
    steps_taken: int = 0
    levels_completed: int = 0
    turns_taken: int = 0

    # Items
    exploits_used: Counter = field(default_factory=Counter)
    exploits_equipped: Counter = field(default_factory=Counter)
    exploits_unequipped: Counter = field(default_factory=Counter)
    code_hacks_used: Counter = field(default_factory=Counter)

    # System state
    heat_generated: int = 0
    overheating_events: int = 0
    trace_increases: int = 0
    admin_spawns: int = 0

    # === NEW: Achievement-Oriented Metrics ===

    # Combo/Streak tracking
    current_stealth_streak: int = 0
    max_stealth_streak: int = 0
    current_no_damage_streak: int = 0  # Turns without taking damage
    max_no_damage_streak: int = 0
    aoe_multi_kills: Counter = field(default_factory=Counter)  # {num_enemies: count}

    # Efficiency metrics
    max_single_hit_damage: int = 0
    turns_with_kills: int = 0  # For damage-per-turn calculation
    _kill_this_turn: bool = False  # Internal flag, not serialized
    total_heat_when_dealing_damage: int = 0  # For heat efficiency

    # Environmental/Tactical
    turns_in_blind_spots: int = 0
    turns_on_special_nodes: int = 0
    ambushes_from_blind_spots: int = 0
    gateway_reached_undetected: bool = False

    # Challenge run flags (for achievements)
    took_any_damage: bool = False
    used_any_exploits: bool = False
    used_any_code_hacks: bool = False
    ever_detected: bool = False  # For ghost run achievement

    # Mastery/Collection (for one run)
    unique_enemies_encountered: set = field(default_factory=set)
    unique_exploits_used_this_run: set = field(default_factory=set)
    unique_code_hacks_used_this_run: set = field(default_factory=set)
    special_nodes_discovered: set = field(default_factory=set)

    # Peak performance
    most_enemies_killed_one_turn: int = 0
    highest_heat_reached: int = 0
    highest_trace_reached: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, handling Counter and set objects."""
        return {
            "session_id": self.session_id,
            "timestamp_start": self.timestamp_start,
            "victory": self.victory,
            "death_cause": self.death_cause,
            "death_level": self.death_level,
            # Ascension tracking
            "ascension_level": self.ascension_level,
            # Achievement tracking
            "last_exploit_used": self.last_exploit_used,
            "admin_kills": self.admin_kills,
            "final_cpu": self.final_cpu,
            "restoration_nodes_used": self.restoration_nodes_used,
            "full_floor_clears": self.full_floor_clears,
            # Combat
            "enemies_killed": dict(self.enemies_killed),
            "damage_dealt": self.damage_dealt,
            "damage_taken": self.damage_taken,
            "stealth_kills": self.stealth_kills,
            # Per-level tracking
            "kills_current_level": self.kills_current_level,
            "min_kills_any_level": self.min_kills_any_level,
            # Exploration
            "steps_taken": self.steps_taken,
            "levels_completed": self.levels_completed,
            "turns_taken": self.turns_taken,
            # Items
            "exploits_used": dict(self.exploits_used),
            "exploits_equipped": dict(self.exploits_equipped),
            "exploits_unequipped": dict(self.exploits_unequipped),
            "code_hacks_used": dict(self.code_hacks_used),
            # System state
            "heat_generated": self.heat_generated,
            "overheating_events": self.overheating_events,
            "trace_increases": self.trace_increases,
            "admin_spawns": self.admin_spawns,
            # Combo/Streak
            "current_stealth_streak": self.current_stealth_streak,
            "max_stealth_streak": self.max_stealth_streak,
            "current_no_damage_streak": self.current_no_damage_streak,
            "max_no_damage_streak": self.max_no_damage_streak,
            "aoe_multi_kills": dict(self.aoe_multi_kills),
            # Efficiency
            "max_single_hit_damage": self.max_single_hit_damage,
            "turns_with_kills": self.turns_with_kills,
            "total_heat_when_dealing_damage": self.total_heat_when_dealing_damage,
            # Environmental
            "turns_in_blind_spots": self.turns_in_blind_spots,
            "turns_on_special_nodes": self.turns_on_special_nodes,
            "ambushes_from_blind_spots": self.ambushes_from_blind_spots,
            "gateway_reached_undetected": self.gateway_reached_undetected,
            # Challenge flags
            "took_any_damage": self.took_any_damage,
            "used_any_exploits": self.used_any_exploits,
            "used_any_code_hacks": self.used_any_code_hacks,
            "ever_detected": self.ever_detected,
            # Mastery (sets -> lists for JSON)
            "unique_enemies_encountered": list(self.unique_enemies_encountered),
            "unique_exploits_used_this_run": list(self.unique_exploits_used_this_run),
            "unique_code_hacks_used_this_run": list(self.unique_code_hacks_used_this_run),
            "special_nodes_discovered": list(self.special_nodes_discovered),
            # Peak performance
            "most_enemies_killed_one_turn": self.most_enemies_killed_one_turn,
            "highest_heat_reached": self.highest_heat_reached,
            "highest_trace_reached": self.highest_trace_reached,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionMetrics":
        """Create SessionMetrics from dictionary, restoring Counter and set objects."""
        # Convert dicts back to Counter objects
        for key in [
            "enemies_killed",
            "exploits_used",
            "exploits_equipped",
            "exploits_unequipped",
            "code_hacks_used",
            "aoe_multi_kills",
        ]:
            if key in data and isinstance(data[key], dict):
                data[key] = Counter(data[key])

        # Convert lists back to sets
        for key in [
            "unique_enemies_encountered",
            "unique_exploits_used_this_run",
            "unique_code_hacks_used_this_run",
            "special_nodes_discovered",
        ]:
            if key in data and isinstance(data[key], list):
                data[key] = set(data[key])

        # Provide defaults for new fields (backward compatibility)
        defaults = {
            # Ascension tracking
            "ascension_level": 0,
            # Achievement tracking
            "last_exploit_used": None,
            "admin_kills": 0,
            "final_cpu": 0,
            "restoration_nodes_used": 0,
            "full_floor_clears": 0,
            # Per-level tracking
            "kills_current_level": 0,
            "min_kills_any_level": None,
            # Combo/streak tracking
            "current_stealth_streak": 0,
            "max_stealth_streak": 0,
            "current_no_damage_streak": 0,
            "max_no_damage_streak": 0,
            "aoe_multi_kills": Counter(),
            "max_single_hit_damage": 0,
            "turns_with_kills": 0,
            "total_heat_when_dealing_damage": 0,
            "turns_in_blind_spots": 0,
            "turns_on_special_nodes": 0,
            "ambushes_from_blind_spots": 0,
            "gateway_reached_undetected": False,
            "took_any_damage": False,
            "used_any_exploits": False,
            "used_any_code_hacks": False,
            "ever_detected": False,
            "unique_enemies_encountered": set(),
            "unique_exploits_used_this_run": set(),
            "unique_code_hacks_used_this_run": set(),
            "special_nodes_discovered": set(),
            "most_enemies_killed_one_turn": 0,
            "highest_heat_reached": 0,
            "highest_trace_reached": 0.0,
        }

        # Apply defaults for missing fields
        for key, value in defaults.items():
            if key not in data:
                data[key] = value

        return cls(**data)


@dataclass
class LifetimeMetrics:
    """Tracks lifetime statistics across all game sessions."""

    total_games: int = 0
    total_victories: int = 0
    total_turns: int = 0
    fastest_victory_turns: int | None = None
    longest_survival_turns: int = 0

    # Aggregates from all sessions
    total_enemies_killed: Counter = field(default_factory=Counter)
    total_exploits_used: Counter = field(default_factory=Counter)
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    total_stealth_kills: int = 0

    # Ascension tracking
    ascension_victories: Counter = field(default_factory=Counter)  # {level: count}
    highest_ascension_completed: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, handling Counter objects."""
        return {
            "total_games": self.total_games,
            "total_victories": self.total_victories,
            "total_turns": self.total_turns,
            "fastest_victory_turns": self.fastest_victory_turns,
            "longest_survival_turns": self.longest_survival_turns,
            "total_enemies_killed": dict(self.total_enemies_killed),
            "total_exploits_used": dict(self.total_exploits_used),
            "total_damage_dealt": self.total_damage_dealt,
            "total_damage_taken": self.total_damage_taken,
            "total_stealth_kills": self.total_stealth_kills,
            "ascension_victories": dict(self.ascension_victories),
            "highest_ascension_completed": self.highest_ascension_completed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LifetimeMetrics":
        """Create LifetimeMetrics from dictionary, restoring Counter objects."""
        # Provide defaults for missing fields (backwards compatibility)
        defaults = {
            "total_games": 0,
            "total_victories": 0,
            "total_turns": 0,
            "fastest_victory_turns": None,
            "longest_survival_turns": 0,
            "total_enemies_killed": Counter(),
            "total_exploits_used": Counter(),
            "total_damage_dealt": 0,
            "total_damage_taken": 0,
            "total_stealth_kills": 0,
            "ascension_victories": Counter(),
            "highest_ascension_completed": 0,
        }
        # Merge with provided data
        merged = {**defaults, **data}

        # Convert dicts back to Counter objects
        for key in ["total_enemies_killed", "total_exploits_used", "ascension_victories"]:
            if key in merged and isinstance(merged[key], dict):
                merged[key] = Counter(merged[key])

        # Only pass known fields to avoid TypeError on unknown keys
        known_fields = {
            "total_games",
            "total_victories",
            "total_turns",
            "fastest_victory_turns",
            "longest_survival_turns",
            "total_enemies_killed",
            "total_exploits_used",
            "total_damage_dealt",
            "total_damage_taken",
            "total_stealth_kills",
            "ascension_victories",
            "highest_ascension_completed",
        }
        filtered = {k: v for k, v in merged.items() if k in known_fields}
        return cls(**filtered)


def init_session_metrics() -> SessionMetrics:
    """Initialize a new session metrics tracker."""
    global _current_session, _session_finalized

    session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _current_session = SessionMetrics(session_id=session_id, timestamp_start=time.time())
    _session_finalized = False  # Reset finalization guard for new session

    logging.info(f"Metrics tracking initialized for session: {session_id}")
    return _current_session


def get_current_session() -> SessionMetrics | None:
    """Get the current session metrics."""
    return _current_session


def track_stealth_kill() -> None:
    """
    Track a stealth kill and update the stealth streak.

    Call this when an enemy is killed without being alerted.
    Updates current_stealth_streak and max_stealth_streak.
    """
    session = get_current_session()
    if session:
        session.current_stealth_streak += 1
        if session.current_stealth_streak > session.max_stealth_streak:
            session.max_stealth_streak = session.current_stealth_streak


def track_max_damage(damage: int) -> None:
    """
    Track max single hit damage for Overkill achievement.

    Call this when damage is dealt to update the max if exceeded.
    """
    session = get_current_session()
    if session and damage > session.max_single_hit_damage:
        session.max_single_hit_damage = damage


def track_highest_heat(current_heat: int, game: Any = None) -> None:
    """
    Track highest heat reached for cold_blooded/heat_master achievements.

    Call this whenever heat increases to update the max if exceeded.

    Args:
        current_heat: Current heat level
        game: Optional game engine for immediate achievement checking (heat_spike)
    """
    session = get_current_session()
    if session and current_heat > session.highest_heat_reached:
        session.highest_heat_reached = current_heat

        # Trigger immediate achievement check for heat_spike if game provided
        if game is not None:
            from rsp.systems.achievements import AchievementManager

            AchievementManager.check_immediate_achievements_and_notify(session, game)


def track_highest_trace(current_trace: float) -> None:
    """
    Track highest trace level reached for no_trace achievement.

    Call this whenever trace increases to update the max if exceeded.
    """
    session = get_current_session()
    if session and current_trace > session.highest_trace_reached:
        session.highest_trace_reached = current_trace


def track_kill_this_turn() -> None:
    """
    Mark that a kill happened this turn and update turns_with_kills.

    On the first kill of each turn, increments turns_with_kills.
    Subsequent kills in the same turn do not increment the counter.
    Call reset_turn_kill_flag() at the start of each new turn.
    """
    session = get_current_session()
    if session and not session._kill_this_turn:
        session._kill_this_turn = True
        session.turns_with_kills += 1


def reset_turn_kill_flag() -> None:
    """
    Reset the kill-this-turn flag at the start of a new turn.

    Called from advance_turn() to prepare for tracking kills in the new turn.
    """
    session = get_current_session()
    if session:
        session._kill_this_turn = False


def complete_level_metrics() -> None:
    """
    Update metrics when a level is completed.

    Called from game_level_coordinator when player reaches the gateway.
    Updates min_kills_any_level for pacifist achievement and resets kills_current_level.
    """
    session = get_current_session()
    if session:
        # Update minimum kills on any level (for pacifist achievement)
        if (
            session.min_kills_any_level is None
            or session.kills_current_level < session.min_kills_any_level
        ):
            session.min_kills_any_level = session.kills_current_level
            logging.debug(
                f"Level completed with {session.kills_current_level} kills "
                f"(new min: {session.min_kills_any_level})"
            )
        else:
            logging.debug(
                f"Level completed with {session.kills_current_level} kills "
                f"(min remains: {session.min_kills_any_level})"
            )

        # Reset for next level
        session.kills_current_level = 0


def track_enemy_kill(
    enemy_type: str,
    damage: int,
    was_stealth: bool,
    is_admin: bool,
    from_blind_spot: bool,
    enemies_remaining: int,
    game=None,
) -> None:
    """
    Track all metrics for an enemy kill event.

    Consolidates kill tracking logic that was duplicated in game_combat.py
    and game_engine.py. Call this whenever an enemy is killed.

    Args:
        enemy_type: Enemy type (e.g., "virus", "scanner")
        damage: Damage dealt to kill the enemy
        was_stealth: True if enemy was unaware when killed
        is_admin: True if enemy was Admin Avatar
        from_blind_spot: True if player was in a blind spot
        enemies_remaining: Number of enemies left on floor (0 = full clear)
        game: Optional GameEngine for achievement checking
    """
    track("enemies_killed", category=enemy_type)
    track("damage_dealt", amount=damage)
    track_kill_this_turn()

    # Track unique enemies encountered for enemy_database achievement
    session = get_current_session()
    if session:
        session.unique_enemies_encountered.add(enemy_type)
        # Track per-level kills for pacifist achievement
        session.kills_current_level += 1

    if was_stealth:
        track("stealth_kills")
        track_stealth_kill()

    track_max_damage(damage)

    if is_admin:
        track("admin_kills")

    if from_blind_spot:
        track("ambushes_from_blind_spots")

    if enemies_remaining == 0:
        track("full_floor_clears")

    # Check for immediate achievements if game provided
    if game is not None:
        from rsp.systems.achievements import AchievementManager

        session = get_current_session()
        if session:
            AchievementManager.check_immediate_achievements_and_notify(session, game)


def track(metric_name: str, category: str | None = None, amount: int = 1, game: Any = None) -> None:
    """
    Track a gameplay event.

    Args:
        metric_name: Name of the metric to track
        category: Optional category (for Counter metrics like enemy type, exploit name)
        amount: Amount to add (default 1)
        game: Optional game engine for immediate achievement checking

    Examples:
        track("enemies_killed", category="virus")
        track("damage_dealt", amount=25)
        track("exploits_used", category="code_injection")
        track("stealth_kills")
        track("restoration_nodes_used", game=self.game_engine)  # Triggers achievement check
    """
    global _current_session

    if _current_session is None:
        logging.warning(f"Attempted to track metric '{metric_name}' but no session active")
        return

    try:
        # Handle Counter-based metrics
        if category is not None:
            counter_attr = getattr(_current_session, metric_name, None)
            if isinstance(counter_attr, Counter):
                counter_attr[category] += amount
            else:
                logging.error(f"Metric '{metric_name}' is not a Counter type")
        # Handle integer metrics
        else:
            current_value = getattr(_current_session, metric_name, None)
            if isinstance(current_value, int):
                setattr(_current_session, metric_name, current_value + amount)
            else:
                logging.error(f"Metric '{metric_name}' is not an integer type")

        # Check achievements immediately if game provided
        # This fixes timing bugs where achievements trigger on next enemy kill
        # instead of when the action actually happens
        if game is not None:
            from rsp.systems.achievements import AchievementManager

            AchievementManager.check_immediate_achievements_and_notify(_current_session, game)

    except AttributeError as e:
        GameErrorHandler.handle_error(
            e, "metric_track", f"Unknown metric: '{metric_name}'", fatal=False
        )
    except Exception as e:
        GameErrorHandler.handle_error(
            e, "metric_track", f"Error tracking metric '{metric_name}'", fatal=False
        )


def finalize_session(
    victory: bool, death_cause: str | None = None, death_level: int = 0, final_cpu: int = 0
) -> SessionMetrics:
    """
    Finalize the current session with outcome information.

    Args:
        victory: Whether the player won the game
        death_cause: Cause of death if applicable ("combat", "overheat", "virus", "self_damage")
        death_level: Level where death occurred (1-3)
        final_cpu: Player's CPU remaining at session end (for close_call achievement)

    Returns:
        The finalized SessionMetrics
    """
    global _current_session

    if _current_session is None:
        logging.error("Attempted to finalize session but no session active")
        return None

    _current_session.victory = victory
    _current_session.death_cause = death_cause
    _current_session.death_level = death_level
    _current_session.final_cpu = final_cpu

    logging.info(f"Session finalized: victory={victory}, cause={death_cause}, level={death_level}")
    return _current_session


def save_session_to_json(session: SessionMetrics) -> None:
    """Save session metrics to JSON file."""
    try:
        _get_metrics_dir().mkdir(exist_ok=True)
    except Exception as e:
        GameErrorHandler.handle_error(
            e, "create_metrics_dir", "Failed to create metrics directory", fatal=False
        )
        return

    json_file = _get_metrics_dir() / f"{session.session_id}.json"

    try:
        with open(json_file, "w") as f:
            json.dump(session.to_dict(), f, indent=2)
        logging.info(f"Session metrics saved to {json_file}")

        # Cleanup old JSON files if we exceed the limit
        _cleanup_old_json_files()

    except Exception as e:
        GameErrorHandler.handle_error(
            e, "save_session_json", "Failed to save session metrics to JSON", fatal=False
        )


def save_session_to_sqlite(session: SessionMetrics) -> None:
    """Save session metrics to SQLite database."""
    try:
        _get_metrics_dir().mkdir(exist_ok=True)
    except Exception as e:
        GameErrorHandler.handle_error(
            e, "create_metrics_dir", "Failed to create metrics directory", fatal=False
        )
        return

    try:
        _init_sqlite_schema()

        with sqlite3.connect(_get_session_db_path()) as conn:
            cursor = conn.cursor()

            # Insert session record
            cursor.execute(
                """
                INSERT INTO sessions (
                    session_id, timestamp_start, victory, death_cause, death_level,
                    damage_dealt, damage_taken, stealth_kills,
                    steps_taken, levels_completed, turns_taken,
                    heat_generated, overheating_events, trace_increases, admin_spawns
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    session.session_id,
                    session.timestamp_start,
                    session.victory,
                    session.death_cause,
                    session.death_level,
                    session.damage_dealt,
                    session.damage_taken,
                    session.stealth_kills,
                    session.steps_taken,
                    session.levels_completed,
                    session.turns_taken,
                    session.heat_generated,
                    session.overheating_events,
                    session.trace_increases,
                    session.admin_spawns,
                ),
            )

            # Insert combat events
            for enemy_type, count in session.enemies_killed.items():
                cursor.execute(
                    """
                    INSERT INTO combat_events (session_id, enemy_type, kills)
                    VALUES (?, ?, ?)
                """,
                    (session.session_id, enemy_type, count),
                )

            # Insert exploit events
            for exploit_name, uses in session.exploits_used.items():
                cursor.execute(
                    """
                    INSERT INTO exploit_events (session_id, exploit_name, uses, equipped, unequipped)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        session.session_id,
                        exploit_name,
                        uses,
                        session.exploits_equipped.get(exploit_name, 0),
                        session.exploits_unequipped.get(exploit_name, 0),
                    ),
                )

            # Insert item events
            for hack_name, uses in session.code_hacks_used.items():
                cursor.execute(
                    """
                    INSERT INTO item_events (session_id, item_name, uses)
                    VALUES (?, ?, ?)
                """,
                    (session.session_id, hack_name, uses),
                )

            conn.commit()

        logging.info(f"Session metrics saved to SQLite: {session.session_id}")

    except Exception as e:
        GameErrorHandler.handle_error(
            e, "save_session_sqlite", "Failed to save session metrics to SQLite", fatal=False
        )


def load_lifetime_metrics() -> LifetimeMetrics:
    """Load lifetime metrics from saves/rogue_signal_progress.json."""
    progress_file = _get_progress_file_path()

    if not progress_file.exists():
        # File doesn't exist yet - new player, use defaults
        return LifetimeMetrics()

    try:
        with open(progress_file) as f:
            data = json.load(f)
            if "lifetime_metrics" in data:
                return LifetimeMetrics.from_dict(data["lifetime_metrics"])
            # File exists but has no lifetime_metrics section - use defaults
            return LifetimeMetrics()
    except Exception as e:
        # File exists but is corrupt or unreadable - this is a real problem
        GameErrorHandler.handle_error(
            e,
            "load_lifetime_metrics",
            f"Progress file exists but is corrupt: {progress_file}",
            fatal=True,
        )


def load_unlocked_achievements() -> list:
    """Load unlocked achievements from saves/rogue_signal_progress.json."""
    progress_file = _get_progress_file_path()

    if not progress_file.exists():
        # File doesn't exist yet - new player, no achievements
        return []

    try:
        with open(progress_file) as f:
            data = json.load(f)
            return data.get("unlocked_achievements", [])
    except Exception as e:
        # File exists but is corrupt or unreadable - this is a real problem
        GameErrorHandler.handle_error(
            e,
            "load_unlocked_achievements",
            f"Progress file exists but is corrupt: {progress_file}",
            fatal=True,
        )


def save_unlocked_achievements(achievements: list) -> None:
    """Save unlocked achievements to saves/rogue_signal_progress.json."""
    progress_file = _get_progress_file_path()

    try:
        # Ensure saves directory exists
        progress_file.parent.mkdir(exist_ok=True)

        # Load existing progress data
        data = {}
        if progress_file.exists():
            with open(progress_file) as f:
                data = json.load(f)

        # Update unlocked achievements
        data["unlocked_achievements"] = achievements

        # Save back to file
        with open(progress_file, "w") as f:
            json.dump(data, f, indent=2)

        logging.info(
            f"Saved {len(achievements)} unlocked achievements to saves/rogue_signal_progress.json"
        )

    except Exception as e:
        # Achievements are critical player progress - fail loudly so the issue is noticed
        GameErrorHandler.handle_error(
            e, "save_unlocked_achievements", "Failed to save unlocked achievements", fatal=True
        )


def save_lifetime_metrics(lifetime: LifetimeMetrics) -> None:
    """Save lifetime metrics to saves/rogue_signal_progress.json."""
    progress_file = _get_progress_file_path()

    try:
        # Ensure saves directory exists
        progress_file.parent.mkdir(exist_ok=True)

        # Load existing progress data
        data = {}
        if progress_file.exists():
            with open(progress_file) as f:
                data = json.load(f)

        # Update lifetime metrics section
        data["lifetime_metrics"] = lifetime.to_dict()

        # Save back to file
        with open(progress_file, "w") as f:
            json.dump(data, f, indent=2)

        logging.info("Lifetime metrics saved to saves/rogue_signal_progress.json")

    except Exception as e:
        # Lifetime metrics are critical player progress - fail loudly so the issue is noticed
        GameErrorHandler.handle_error(
            e, "save_lifetime_metrics", "Failed to save lifetime metrics", fatal=True
        )


def update_lifetime_metrics(session: SessionMetrics) -> None:
    """Update lifetime metrics with data from completed session."""
    lifetime = load_lifetime_metrics()

    # Update totals
    lifetime.total_games += 1
    if session.victory:
        lifetime.total_victories += 1

        # Track ascension victories and highest completion
        # Use string key for consistency with JSON serialization
        ascension = session.ascension_level
        lifetime.ascension_victories[str(ascension)] += 1
        if ascension > lifetime.highest_ascension_completed:
            lifetime.highest_ascension_completed = ascension
            logging.info(f"New highest ascension completed: A{ascension}")

    lifetime.total_turns += session.turns_taken
    lifetime.total_damage_dealt += session.damage_dealt
    lifetime.total_damage_taken += session.damage_taken
    lifetime.total_stealth_kills += session.stealth_kills

    # Update records
    if session.victory:
        if (
            lifetime.fastest_victory_turns is None
            or session.turns_taken < lifetime.fastest_victory_turns
        ):
            lifetime.fastest_victory_turns = session.turns_taken

    if session.turns_taken > lifetime.longest_survival_turns:
        lifetime.longest_survival_turns = session.turns_taken

    # Update aggregated counters
    for enemy_type, count in session.enemies_killed.items():
        lifetime.total_enemies_killed[enemy_type] += count

    for exploit_name, uses in session.exploits_used.items():
        lifetime.total_exploits_used[exploit_name] += uses

    # Save updated lifetime metrics
    save_lifetime_metrics(lifetime)

    logging.info(
        f"Lifetime metrics updated: {lifetime.total_games} games, {lifetime.total_victories} victories"
    )


def save_metrics(session: SessionMetrics) -> None:
    """Save session metrics to both JSON and SQLite, then update lifetime stats."""
    save_session_to_json(session)
    save_session_to_sqlite(session)
    update_lifetime_metrics(session)


def finalize_and_save_session(
    victory: bool,
    death_cause: str | None = None,
    death_level: int = 0,
    final_cpu: int = 0,
) -> list[str]:
    """
    Finalize session, save metrics, and check achievements.

    Consolidates the common pattern of:
    1. finalize_session()
    2. save_metrics()
    3. Check achievements against lifetime stats
    4. Save newly unlocked achievements

    This function is idempotent - calling it multiple times after the first
    successful finalization will return an empty list without re-processing.

    Args:
        victory: Whether the player won
        death_cause: Cause of death if applicable
        death_level: Level where death occurred
        final_cpu: Player's final CPU

    Returns:
        List of newly unlocked achievement IDs (empty if none)
    """
    global _session_finalized

    # Guard against double finalization (e.g., victory then death race)
    if _session_finalized:
        logging.debug("finalize_and_save_session called but session already finalized")
        return []

    metrics = finalize_session(
        victory=victory,
        death_cause=death_cause,
        death_level=death_level,
        final_cpu=final_cpu,
    )

    if not metrics:
        return []

    # Mark as finalized before saving (in case save crashes)
    _session_finalized = True

    save_metrics(metrics)

    # Check for newly unlocked achievements
    from rsp.systems.achievements import AchievementManager

    lifetime = load_lifetime_metrics()
    newly_unlocked = AchievementManager.check_achievements(metrics, lifetime)
    if newly_unlocked:
        logging.info(f"Unlocked {len(newly_unlocked)} achievements")
        save_unlocked_achievements(AchievementManager.get_unlocked_achievements())

    return newly_unlocked


def _init_sqlite_schema() -> None:
    """Initialize SQLite database schema if it doesn't exist."""
    with sqlite3.connect(_get_session_db_path()) as conn:
        cursor = conn.cursor()

        # Sessions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp_start REAL,
                victory INTEGER,
                death_cause TEXT,
                death_level INTEGER,
                damage_dealt INTEGER,
                damage_taken INTEGER,
                stealth_kills INTEGER,
                steps_taken INTEGER,
                levels_completed INTEGER,
                turns_taken INTEGER,
                heat_generated INTEGER,
                overheating_events INTEGER,
                trace_increases INTEGER,
                admin_spawns INTEGER
            )
        """
        )

        # Combat events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS combat_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                enemy_type TEXT,
                kills INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """
        )

        # Exploit events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS exploit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                exploit_name TEXT,
                uses INTEGER,
                equipped INTEGER,
                unequipped INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """
        )

        # Item events table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS item_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                item_name TEXT,
                uses INTEGER,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """
        )

        conn.commit()


def _cleanup_old_json_files() -> None:
    """Remove oldest JSON files if we exceed MAX_JSON_FILES limit."""
    json_files = sorted(_get_metrics_dir().glob("*.json"), key=lambda p: p.stat().st_mtime)

    if len(json_files) > MAX_JSON_FILES:
        files_to_remove = json_files[:-MAX_JSON_FILES]
        for file in files_to_remove:
            try:
                file.unlink()
                logging.info(f"Cleaned up old metrics file: {file.name}")
            except Exception as e:
                GameErrorHandler.handle_error(
                    e, "cleanup_metrics_file", f"Failed to clean up {file.name}", fatal=False
                )


def load_session_metrics(save_data: dict[str, Any]) -> SessionMetrics | None:
    """Load session metrics from save data."""
    global _session_finalized

    if "session_metrics" in save_data:
        try:
            metrics = SessionMetrics.from_dict(save_data["session_metrics"])
            # Reset finalization flag since we're loading an in-progress session
            _session_finalized = False
            return metrics
        except Exception as e:
            GameErrorHandler.handle_error(
                e,
                "load_session_metrics",
                "Failed to load session metrics from save, continuing without metrics",
                fatal=False,
            )
    return None


def save_checkpoint() -> dict[str, Any]:
    """Create a checkpoint of current session metrics for save file."""
    global _current_session

    if _current_session is None:
        return {}

    return _current_session.to_dict()
