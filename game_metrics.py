"""
Metrics tracking system for RogueSignalProtocol.

Tracks all gameplay events for future achievement system and game balance analytics.
Uses dual storage (JSON + SQLite) with lifetime statistics that survive permadeath.
"""

import json
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Directory for metrics storage
METRICS_DIR = Path("metrics")
SESSION_DB = METRICS_DIR / "sessions.db"
MAX_JSON_FILES = 100

# Global metrics instance (initialized by GameEngine)
_current_session: Optional['SessionMetrics'] = None


@dataclass
class SessionMetrics:
    """Tracks metrics for a single game session."""

    session_id: str
    timestamp_start: float
    victory: bool = False
    death_cause: Optional[str] = None  # "combat", "overheat", "trace"
    death_level: int = 0

    # Combat
    enemies_killed: Counter = field(default_factory=Counter)
    damage_dealt: int = 0
    damage_taken: int = 0
    stealth_kills: int = 0

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
    total_heat_when_dealing_damage: int = 0  # For heat efficiency

    # Environmental/Tactical
    turns_in_shadows: int = 0
    turns_on_special_nodes: int = 0
    ambushes_from_shadows: int = 0
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling Counter and set objects."""
        return {
            'session_id': self.session_id,
            'timestamp_start': self.timestamp_start,
            'victory': self.victory,
            'death_cause': self.death_cause,
            'death_level': self.death_level,
            # Combat
            'enemies_killed': dict(self.enemies_killed),
            'damage_dealt': self.damage_dealt,
            'damage_taken': self.damage_taken,
            'stealth_kills': self.stealth_kills,
            # Exploration
            'steps_taken': self.steps_taken,
            'levels_completed': self.levels_completed,
            'turns_taken': self.turns_taken,
            # Items
            'exploits_used': dict(self.exploits_used),
            'exploits_equipped': dict(self.exploits_equipped),
            'exploits_unequipped': dict(self.exploits_unequipped),
            'code_hacks_used': dict(self.code_hacks_used),
            # System state
            'heat_generated': self.heat_generated,
            'overheating_events': self.overheating_events,
            'trace_increases': self.trace_increases,
            'admin_spawns': self.admin_spawns,
            # Combo/Streak
            'current_stealth_streak': self.current_stealth_streak,
            'max_stealth_streak': self.max_stealth_streak,
            'current_no_damage_streak': self.current_no_damage_streak,
            'max_no_damage_streak': self.max_no_damage_streak,
            'aoe_multi_kills': dict(self.aoe_multi_kills),
            # Efficiency
            'max_single_hit_damage': self.max_single_hit_damage,
            'turns_with_kills': self.turns_with_kills,
            'total_heat_when_dealing_damage': self.total_heat_when_dealing_damage,
            # Environmental
            'turns_in_shadows': self.turns_in_shadows,
            'turns_on_special_nodes': self.turns_on_special_nodes,
            'ambushes_from_shadows': self.ambushes_from_shadows,
            'gateway_reached_undetected': self.gateway_reached_undetected,
            # Challenge flags
            'took_any_damage': self.took_any_damage,
            'used_any_exploits': self.used_any_exploits,
            'used_any_code_hacks': self.used_any_code_hacks,
            'ever_detected': self.ever_detected,
            # Mastery (sets -> lists for JSON)
            'unique_enemies_encountered': list(self.unique_enemies_encountered),
            'unique_exploits_used_this_run': list(self.unique_exploits_used_this_run),
            'unique_code_hacks_used_this_run': list(self.unique_code_hacks_used_this_run),
            'special_nodes_discovered': list(self.special_nodes_discovered),
            # Peak performance
            'most_enemies_killed_one_turn': self.most_enemies_killed_one_turn,
            'highest_heat_reached': self.highest_heat_reached,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetrics':
        """Create SessionMetrics from dictionary, restoring Counter and set objects."""
        # Convert dicts back to Counter objects
        for key in ['enemies_killed', 'exploits_used', 'exploits_equipped',
                   'exploits_unequipped', 'code_hacks_used', 'aoe_multi_kills']:
            if key in data and isinstance(data[key], dict):
                data[key] = Counter(data[key])

        # Convert lists back to sets
        for key in ['unique_enemies_encountered', 'unique_exploits_used_this_run',
                   'unique_code_hacks_used_this_run', 'special_nodes_discovered']:
            if key in data and isinstance(data[key], list):
                data[key] = set(data[key])

        # Provide defaults for new fields (backward compatibility)
        defaults = {
            'current_stealth_streak': 0, 'max_stealth_streak': 0,
            'current_no_damage_streak': 0, 'max_no_damage_streak': 0,
            'aoe_multi_kills': Counter(), 'max_single_hit_damage': 0,
            'turns_with_kills': 0, 'total_heat_when_dealing_damage': 0,
            'turns_in_shadows': 0, 'turns_on_special_nodes': 0,
            'ambushes_from_shadows': 0, 'gateway_reached_undetected': False,
            'took_any_damage': False, 'used_any_exploits': False,
            'used_any_code_hacks': False, 'ever_detected': False,
            'unique_enemies_encountered': set(), 'unique_exploits_used_this_run': set(),
            'unique_code_hacks_used_this_run': set(), 'special_nodes_discovered': set(),
            'most_enemies_killed_one_turn': 0, 'highest_heat_reached': 0,
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
    fastest_victory_turns: Optional[int] = None
    longest_survival_turns: int = 0

    # Aggregates from all sessions
    total_enemies_killed: Counter = field(default_factory=Counter)
    total_exploits_used: Counter = field(default_factory=Counter)
    total_damage_dealt: int = 0
    total_damage_taken: int = 0
    total_stealth_kills: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling Counter objects."""
        return {
            'total_games': self.total_games,
            'total_victories': self.total_victories,
            'total_turns': self.total_turns,
            'fastest_victory_turns': self.fastest_victory_turns,
            'longest_survival_turns': self.longest_survival_turns,
            'total_enemies_killed': dict(self.total_enemies_killed),
            'total_exploits_used': dict(self.total_exploits_used),
            'total_damage_dealt': self.total_damage_dealt,
            'total_damage_taken': self.total_damage_taken,
            'total_stealth_kills': self.total_stealth_kills
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LifetimeMetrics':
        """Create LifetimeMetrics from dictionary, restoring Counter objects."""
        # Convert dicts back to Counter objects
        for key in ['total_enemies_killed', 'total_exploits_used']:
            if key in data and isinstance(data[key], dict):
                data[key] = Counter(data[key])
        return cls(**data)


def init_session_metrics() -> SessionMetrics:
    """Initialize a new session metrics tracker."""
    global _current_session

    session_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    _current_session = SessionMetrics(
        session_id=session_id,
        timestamp_start=time.time()
    )

    logging.info(f"Metrics tracking initialized for session: {session_id}")
    return _current_session


def get_current_session() -> Optional[SessionMetrics]:
    """Get the current session metrics."""
    return _current_session


def track(metric_name: str, category: Optional[str] = None, amount: int = 1) -> None:
    """
    Track a gameplay event.

    Args:
        metric_name: Name of the metric to track
        category: Optional category (for Counter metrics like enemy type, exploit name)
        amount: Amount to add (default 1)

    Examples:
        track("enemies_killed", category="virus")
        track("damage_dealt", amount=25)
        track("exploits_used", category="code_injection")
        track("stealth_kills")
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

    except AttributeError:
        logging.error(f"Unknown metric: '{metric_name}'")
    except Exception as e:
        logging.error(f"Error tracking metric '{metric_name}': {e}")


def finalize_session(victory: bool, death_cause: Optional[str] = None,
                     death_level: int = 0) -> SessionMetrics:
    """
    Finalize the current session with outcome information.

    Args:
        victory: Whether the player won the game
        death_cause: Cause of death if applicable ("combat", "overheat", "trace")
        death_level: Level where death occurred (1-3)

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

    logging.info(f"Session finalized: victory={victory}, cause={death_cause}, level={death_level}")
    return _current_session


def save_session_to_json(session: SessionMetrics) -> None:
    """Save session metrics to JSON file."""
    METRICS_DIR.mkdir(exist_ok=True)

    json_file = METRICS_DIR / f"{session.session_id}.json"

    try:
        with open(json_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        logging.info(f"Session metrics saved to {json_file}")

        # Cleanup old JSON files if we exceed the limit
        _cleanup_old_json_files()

    except Exception as e:
        logging.error(f"Failed to save session JSON: {e}")


def save_session_to_sqlite(session: SessionMetrics) -> None:
    """Save session metrics to SQLite database."""
    METRICS_DIR.mkdir(exist_ok=True)

    try:
        _init_sqlite_schema()

        conn = sqlite3.connect(SESSION_DB)
        cursor = conn.cursor()

        # Insert session record
        cursor.execute("""
            INSERT INTO sessions (
                session_id, timestamp_start, victory, death_cause, death_level,
                damage_dealt, damage_taken, stealth_kills,
                steps_taken, levels_completed, turns_taken,
                heat_generated, overheating_events, trace_increases, admin_spawns
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.session_id, session.timestamp_start, session.victory,
            session.death_cause, session.death_level,
            session.damage_dealt, session.damage_taken, session.stealth_kills,
            session.steps_taken, session.levels_completed, session.turns_taken,
            session.heat_generated, session.overheating_events,
            session.trace_increases, session.admin_spawns
        ))

        # Insert combat events
        for enemy_type, count in session.enemies_killed.items():
            cursor.execute("""
                INSERT INTO combat_events (session_id, enemy_type, kills)
                VALUES (?, ?, ?)
            """, (session.session_id, enemy_type, count))

        # Insert exploit events
        for exploit_name, uses in session.exploits_used.items():
            cursor.execute("""
                INSERT INTO exploit_events (session_id, exploit_name, uses, equipped, unequipped)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session.session_id, exploit_name, uses,
                session.exploits_equipped.get(exploit_name, 0),
                session.exploits_unequipped.get(exploit_name, 0)
            ))

        # Insert item events
        for hack_name, uses in session.code_hacks_used.items():
            cursor.execute("""
                INSERT INTO item_events (session_id, item_name, uses)
                VALUES (?, ?, ?)
            """, (session.session_id, hack_name, uses))

        conn.commit()
        conn.close()

        logging.info(f"Session metrics saved to SQLite: {session.session_id}")

    except Exception as e:
        logging.error(f"Failed to save session to SQLite: {e}")


def load_lifetime_metrics() -> LifetimeMetrics:
    """Load lifetime metrics from rogue_signal_progress.json."""
    progress_file = Path("rogue_signal_progress.json")

    try:
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                data = json.load(f)
                if 'lifetime_metrics' in data:
                    return LifetimeMetrics.from_dict(data['lifetime_metrics'])
    except Exception as e:
        logging.error(f"Failed to load lifetime metrics: {e}")

    # Return fresh metrics if loading fails
    return LifetimeMetrics()


def load_unlocked_achievements() -> list:
    """Load unlocked achievements from rogue_signal_progress.json."""
    progress_file = Path("rogue_signal_progress.json")

    try:
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return data.get('unlocked_achievements', [])
    except Exception as e:
        logging.error(f"Failed to load unlocked achievements: {e}")

    return []


def save_unlocked_achievements(achievements: list) -> None:
    """Save unlocked achievements to rogue_signal_progress.json."""
    progress_file = Path("rogue_signal_progress.json")

    try:
        # Load existing progress data
        data = {}
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                data = json.load(f)

        # Update unlocked achievements
        data['unlocked_achievements'] = achievements

        # Save back to file
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)

        logging.info(f"Saved {len(achievements)} unlocked achievements to progress file")

    except Exception as e:
        logging.error(f"Failed to save unlocked achievements: {e}")


def save_lifetime_metrics(lifetime: LifetimeMetrics) -> None:
    """Save lifetime metrics to rogue_signal_progress.json."""
    progress_file = Path("rogue_signal_progress.json")

    try:
        # Load existing progress data
        data = {}
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                data = json.load(f)

        # Update lifetime metrics section
        data['lifetime_metrics'] = lifetime.to_dict()

        # Save back to file
        with open(progress_file, 'w') as f:
            json.dump(data, f, indent=2)

        logging.info("Lifetime metrics saved to rogue_signal_progress.json")

    except Exception as e:
        logging.error(f"Failed to save lifetime metrics: {e}")


def update_lifetime_metrics(session: SessionMetrics) -> None:
    """Update lifetime metrics with data from completed session."""
    lifetime = load_lifetime_metrics()

    # Update totals
    lifetime.total_games += 1
    if session.victory:
        lifetime.total_victories += 1

    lifetime.total_turns += session.turns_taken
    lifetime.total_damage_dealt += session.damage_dealt
    lifetime.total_damage_taken += session.damage_taken
    lifetime.total_stealth_kills += session.stealth_kills

    # Update records
    if session.victory:
        if lifetime.fastest_victory_turns is None or session.turns_taken < lifetime.fastest_victory_turns:
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

    logging.info(f"Lifetime metrics updated: {lifetime.total_games} games, {lifetime.total_victories} victories")


def save_metrics(session: SessionMetrics) -> None:
    """Save session metrics to both JSON and SQLite, then update lifetime stats."""
    save_session_to_json(session)
    save_session_to_sqlite(session)
    update_lifetime_metrics(session)


def _init_sqlite_schema() -> None:
    """Initialize SQLite database schema if it doesn't exist."""
    conn = sqlite3.connect(SESSION_DB)
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
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
    """)

    # Combat events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combat_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            enemy_type TEXT,
            kills INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    # Exploit events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exploit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            exploit_name TEXT,
            uses INTEGER,
            equipped INTEGER,
            unequipped INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    # Item events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            item_name TEXT,
            uses INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    conn.commit()
    conn.close()


def _cleanup_old_json_files() -> None:
    """Remove oldest JSON files if we exceed MAX_JSON_FILES limit."""
    json_files = sorted(METRICS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)

    if len(json_files) > MAX_JSON_FILES:
        files_to_remove = json_files[:-MAX_JSON_FILES]
        for file in files_to_remove:
            try:
                file.unlink()
                logging.info(f"Cleaned up old metrics file: {file.name}")
            except Exception as e:
                logging.error(f"Failed to clean up {file.name}: {e}")


def load_session_metrics(save_data: Dict[str, Any]) -> Optional[SessionMetrics]:
    """Load session metrics from save data."""
    if 'session_metrics' in save_data:
        try:
            return SessionMetrics.from_dict(save_data['session_metrics'])
        except Exception as e:
            logging.error(f"Failed to load session metrics from save: {e}")
    return None


def save_checkpoint() -> Dict[str, Any]:
    """Create a checkpoint of current session metrics for save file."""
    global _current_session

    if _current_session is None:
        return {}

    return _current_session.to_dict()
