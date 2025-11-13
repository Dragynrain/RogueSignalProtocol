"""
Unit tests for metrics tracking system.
"""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

from game_metrics import (
    METRICS_DIR,
    LifetimeMetrics,
    SessionMetrics,
    finalize_session,
    init_session_metrics,
    load_lifetime_metrics,
    save_session_to_json,
    save_session_to_sqlite,
    track,
    update_lifetime_metrics,
)


@pytest.fixture
def clean_metrics():
    """Clean up metrics directory AND progress file before and after tests."""
    # Clean before test
    if METRICS_DIR.exists():
        for file in METRICS_DIR.glob("*.json"):
            file.unlink()
        db_file = METRICS_DIR / "sessions.db"
        if db_file.exists():
            db_file.unlink()

    # Clean progress file for unit tests (to ensure clean state)
    progress_file = Path("saves/rogue_signal_progress.json")
    if progress_file.exists():
        progress_file.unlink()

    yield

    # Clean after test
    if METRICS_DIR.exists():
        for file in METRICS_DIR.glob("*.json"):
            file.unlink()
        db_file = METRICS_DIR / "sessions.db"
        if db_file.exists():
            db_file.unlink()

    # Clean progress file after test
    if progress_file.exists():
        progress_file.unlink()
    # Tests that need progress data should use mocks or temp files.


def test_session_metrics_initialization():
    """Test session metrics initialization."""
    session = init_session_metrics()

    assert session.session_id is not None
    assert session.timestamp_start > 0
    assert session.victory is False
    assert session.damage_dealt == 0
    assert session.damage_taken == 0
    assert session.steps_taken == 0
    assert isinstance(session.enemies_killed, Counter)
    assert isinstance(session.exploits_used, Counter)


def test_track_integer_metrics():
    """Test tracking integer metrics."""
    session = init_session_metrics()

    track("damage_dealt", amount=25)
    assert session.damage_dealt == 25

    track("damage_dealt", amount=10)
    assert session.damage_dealt == 35

    track("steps_taken")
    assert session.steps_taken == 1

    track("steps_taken")
    assert session.steps_taken == 2


def test_track_counter_metrics():
    """Test tracking Counter-based metrics."""
    session = init_session_metrics()

    track("enemies_killed", category="virus")
    assert session.enemies_killed["virus"] == 1

    track("enemies_killed", category="virus")
    assert session.enemies_killed["virus"] == 2

    track("enemies_killed", category="admin")
    assert session.enemies_killed["admin"] == 1
    assert session.enemies_killed["virus"] == 2


def test_track_exploit_usage():
    """Test tracking exploit usage."""
    session = init_session_metrics()

    track("exploits_used", category="code_injection")
    track("exploits_used", category="code_injection")
    track("exploits_used", category="system_hop")

    assert session.exploits_used["code_injection"] == 2
    assert session.exploits_used["system_hop"] == 1


def test_finalize_session():
    """Test session finalization."""
    session = init_session_metrics()

    track("damage_dealt", amount=100)
    track("enemies_killed", category="virus", amount=5)

    finalized = finalize_session(victory=True, death_cause=None, death_level=0)

    assert finalized.victory is True
    assert finalized.death_cause is None
    assert finalized.damage_dealt == 100
    assert finalized.enemies_killed["virus"] == 5


def test_session_serialization():
    """Test session metrics to/from dict conversion."""
    session = init_session_metrics()

    track("enemies_killed", category="virus", amount=3)
    track("exploits_used", category="system_hop", amount=2)
    track("damage_dealt", amount=50)

    # Convert to dict
    data = session.to_dict()

    assert isinstance(data["enemies_killed"], dict)
    assert data["enemies_killed"]["virus"] == 3
    assert data["damage_dealt"] == 50

    # Restore from dict
    restored = SessionMetrics.from_dict(data)

    assert isinstance(restored.enemies_killed, Counter)
    assert restored.enemies_killed["virus"] == 3
    assert restored.damage_dealt == 50


def test_save_session_to_json(clean_metrics):
    """Test saving session metrics to JSON."""
    session = init_session_metrics()

    track("damage_dealt", amount=100)
    track("enemies_killed", category="virus", amount=5)

    finalized = finalize_session(victory=False, death_cause="combat", death_level=2)
    save_session_to_json(finalized)

    # Verify file exists
    json_files = list(METRICS_DIR.glob("*.json"))
    assert len(json_files) == 1

    # Verify content
    with open(json_files[0]) as f:
        data = json.load(f)

    assert data["damage_dealt"] == 100
    assert data["enemies_killed"]["virus"] == 5
    assert data["victory"] is False
    assert data["death_cause"] == "combat"


def test_save_session_to_sqlite(clean_metrics):
    """Test saving session metrics to SQLite."""
    session = init_session_metrics()

    track("damage_dealt", amount=150)
    track("enemies_killed", category="virus", amount=3)
    track("enemies_killed", category="admin", amount=1)
    track("exploits_used", category="system_hop", amount=2)
    track("turns_taken", amount=50)

    finalized = finalize_session(victory=True, death_cause=None, death_level=0)
    save_session_to_sqlite(finalized)

    # Verify database exists
    db_file = METRICS_DIR / "sessions.db"
    assert db_file.exists()

    # Query and verify data
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Check sessions table
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session.session_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row[2] == 1  # victory
    assert row[5] == 150  # damage_dealt
    assert row[10] == 50  # turns_taken

    # Check combat_events table
    cursor.execute("SELECT * FROM combat_events WHERE session_id = ?", (session.session_id,))
    combat_rows = cursor.fetchall()
    assert len(combat_rows) == 2  # virus and admin

    # Check exploit_events table
    cursor.execute("SELECT * FROM exploit_events WHERE session_id = ?", (session.session_id,))
    exploit_rows = cursor.fetchall()
    assert len(exploit_rows) == 1  # system_hop

    conn.close()


def test_lifetime_metrics(clean_metrics):
    """Test lifetime metrics aggregation."""
    lifetime = LifetimeMetrics()

    # Simulate first session
    session1 = init_session_metrics()
    track("damage_dealt", amount=100)
    track("enemies_killed", category="virus", amount=5)
    track("turns_taken", amount=100)
    finalized1 = finalize_session(victory=False, death_cause="combat", death_level=2)

    update_lifetime_metrics(finalized1)
    lifetime = load_lifetime_metrics()

    assert lifetime.total_games == 1
    assert lifetime.total_victories == 0
    assert lifetime.total_turns == 100
    assert lifetime.total_enemies_killed["virus"] == 5

    # Simulate second session (victory)
    session2 = init_session_metrics()
    track("damage_dealt", amount=200)
    track("enemies_killed", category="virus", amount=10)
    track("enemies_killed", category="admin", amount=1)
    track("turns_taken", amount=150)
    finalized2 = finalize_session(victory=True, death_cause=None, death_level=0)

    update_lifetime_metrics(finalized2)
    lifetime = load_lifetime_metrics()

    assert lifetime.total_games == 2
    assert lifetime.total_victories == 1
    assert lifetime.total_turns == 250
    assert lifetime.total_enemies_killed["virus"] == 15
    assert lifetime.total_enemies_killed["admin"] == 1
    assert lifetime.fastest_victory_turns == 150


def test_lifetime_metrics_fastest_victory(clean_metrics):
    """Test fastest victory tracking."""
    # First victory - 200 turns
    session1 = init_session_metrics()
    track("turns_taken", amount=200)
    finalized1 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized1)

    lifetime = load_lifetime_metrics()
    assert lifetime.fastest_victory_turns == 200

    # Second victory - 150 turns (faster)
    session2 = init_session_metrics()
    track("turns_taken", amount=150)
    finalized2 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized2)

    lifetime = load_lifetime_metrics()
    assert lifetime.fastest_victory_turns == 150

    # Third victory - 180 turns (slower, shouldn't update)
    session3 = init_session_metrics()
    track("turns_taken", amount=180)
    finalized3 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized3)

    lifetime = load_lifetime_metrics()
    assert lifetime.fastest_victory_turns == 150


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
