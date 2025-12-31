"""
Unit tests for metrics tracking system.
"""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

from rsp.systems.metrics import (
    LifetimeMetrics,
    SessionMetrics,
    _get_metrics_dir,
    _get_progress_file_path,
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
    """Clean up metrics directory AND progress file before and after tests (parallel-safe)."""
    import time

    def safe_cleanup():
        """Safely clean up metrics files, handling parallel test conflicts."""
        # Clean metrics directory (may not be initialized yet in some workers)
        try:
            metrics_dir = _get_metrics_dir()
        except RuntimeError:
            # Paths not initialized yet in this worker, skip cleanup
            return

        if metrics_dir.exists():
            # Clean JSON files
            for file in metrics_dir.glob("*.json"):
                try:
                    file.unlink()
                except (PermissionError, FileNotFoundError, OSError):
                    pass  # Ignore if file is locked by another worker or already deleted

            # Clean SQLite database (may be locked by other workers)
            db_file = metrics_dir / "sessions.db"
            if db_file.exists():
                # Try to close any open connections first
                try:
                    # Force close by attempting to open and close with context manager
                    with sqlite3.connect(str(db_file)) as conn:
                        pass  # Connection will auto-close
                    time.sleep(0.05)  # Small delay to ensure connection closes
                except Exception:
                    pass

                # Now try to delete
                try:
                    db_file.unlink()
                except (PermissionError, FileNotFoundError, OSError):
                    pass  # Ignore if locked by another worker

        # Clean progress file (may not be initialized yet in some workers)
        try:
            progress_file = Path(_get_progress_file_path())
            if progress_file.exists():
                try:
                    progress_file.unlink()
                except (PermissionError, FileNotFoundError, OSError):
                    pass  # Ignore if locked by another worker
        except RuntimeError:
            # Paths not initialized yet in this worker, skip cleanup
            pass

    # Clean before test
    safe_cleanup()

    yield

    # Clean after test
    safe_cleanup()


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
    json_files = list(_get_metrics_dir().glob("*.json"))
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
    db_file = _get_metrics_dir() / "sessions.db"
    assert db_file.exists()

    # Query and verify data
    with sqlite3.connect(db_file) as conn:
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


def test_lifetime_metrics(clean_metrics, tmp_path, monkeypatch):
    """Test lifetime metrics aggregation (isolated)."""
    import rsp.systems.metrics as game_metrics

    # Use isolated progress file for this test to avoid parallel conflicts
    test_progress_file = tmp_path / "test_progress.json"
    monkeypatch.setattr(game_metrics, "_get_progress_file_path", lambda: test_progress_file)

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


def test_lifetime_metrics_fastest_victory(clean_metrics, tmp_path, monkeypatch):
    """Test fastest victory tracking (isolated)."""
    import rsp.systems.metrics as game_metrics

    # Use isolated progress file for this test to avoid parallel conflicts
    test_progress_file = tmp_path / "test_progress.json"
    monkeypatch.setattr(game_metrics, "_get_progress_file_path", lambda: test_progress_file)

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


# Tests for track_enemy_kill helper


def test_track_enemy_kill_basic(clean_metrics):
    """Test track_enemy_kill tracks basic kill metrics."""
    from rsp.systems.metrics import init_session_metrics, track_enemy_kill

    session = init_session_metrics()

    track_enemy_kill(
        enemy_type="virus",
        damage=25,
        was_stealth=False,
        is_admin=False,
        from_blind_spot=False,
        enemies_remaining=5,
        game=None,
    )

    assert session.enemies_killed["virus"] == 1
    assert session.damage_dealt == 25
    assert session.turns_with_kills == 1
    assert session.max_single_hit_damage == 25
    assert session.stealth_kills == 0  # Not a stealth kill


def test_track_enemy_kill_stealth(clean_metrics):
    """Test track_enemy_kill tracks stealth kills."""
    from rsp.systems.metrics import init_session_metrics, track_enemy_kill

    session = init_session_metrics()

    track_enemy_kill(
        enemy_type="scanner",
        damage=30,
        was_stealth=True,
        is_admin=False,
        from_blind_spot=False,
        enemies_remaining=3,
        game=None,
    )

    assert session.enemies_killed["scanner"] == 1
    assert session.stealth_kills == 1
    assert session.current_stealth_streak == 1
    assert session.max_stealth_streak == 1


def test_track_enemy_kill_admin(clean_metrics):
    """Test track_enemy_kill tracks admin kills."""
    from rsp.systems.metrics import init_session_metrics, track_enemy_kill

    session = init_session_metrics()

    track_enemy_kill(
        enemy_type="admin",
        damage=100,
        was_stealth=False,
        is_admin=True,
        from_blind_spot=False,
        enemies_remaining=0,
        game=None,
    )

    assert session.enemies_killed["admin"] == 1
    assert session.admin_kills == 1


def test_track_enemy_kill_blind_spot(clean_metrics):
    """Test track_enemy_kill tracks blind spot ambushes."""
    from rsp.systems.metrics import init_session_metrics, track_enemy_kill

    session = init_session_metrics()

    track_enemy_kill(
        enemy_type="virus",
        damage=20,
        was_stealth=False,
        is_admin=False,
        from_blind_spot=True,
        enemies_remaining=2,
        game=None,
    )

    assert session.ambushes_from_blind_spots == 1


def test_track_enemy_kill_full_clear(clean_metrics):
    """Test track_enemy_kill tracks full floor clears."""
    from rsp.systems.metrics import init_session_metrics, track_enemy_kill

    session = init_session_metrics()

    track_enemy_kill(
        enemy_type="virus",
        damage=20,
        was_stealth=False,
        is_admin=False,
        from_blind_spot=False,
        enemies_remaining=0,  # Last enemy on floor
        game=None,
    )

    assert session.full_floor_clears == 1


def test_track_enemy_kill_multiple_same_turn(clean_metrics):
    """Test track_enemy_kill only increments turns_with_kills once per turn."""
    from rsp.systems.metrics import init_session_metrics, reset_turn_kill_flag, track_enemy_kill

    session = init_session_metrics()

    # Kill 3 enemies in same turn
    for i in range(3):
        track_enemy_kill(
            enemy_type="virus",
            damage=10,
            was_stealth=False,
            is_admin=False,
            from_blind_spot=False,
            enemies_remaining=5 - i,
            game=None,
        )

    assert session.enemies_killed["virus"] == 3
    assert session.turns_with_kills == 1  # Only 1 turn, not 3

    # Reset for next turn and kill again
    reset_turn_kill_flag()
    track_enemy_kill(
        enemy_type="virus",
        damage=10,
        was_stealth=False,
        is_admin=False,
        from_blind_spot=False,
        enemies_remaining=1,
        game=None,
    )

    assert session.enemies_killed["virus"] == 4
    assert session.turns_with_kills == 2  # Now 2 turns


# Tests for ascension victory tracking


def test_ascension_victory_tracking(clean_metrics, tmp_path, monkeypatch):
    """Test that ascension_victories is incremented on victory."""
    import rsp.systems.metrics as game_metrics

    # Use isolated progress file for this test
    test_progress_file = tmp_path / "test_progress.json"
    monkeypatch.setattr(game_metrics, "_get_progress_file_path", lambda: test_progress_file)

    # Session 1: Victory at A5
    session1 = init_session_metrics()
    session1.ascension_level = 5
    track("turns_taken", amount=100)
    finalized1 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized1)

    lifetime = load_lifetime_metrics()
    # After save/load, int keys become strings in JSON
    assert lifetime.ascension_victories["5"] == 1
    assert lifetime.highest_ascension_completed == 5

    # Session 2: Victory at A7 (new high)
    session2 = init_session_metrics()
    session2.ascension_level = 7
    track("turns_taken", amount=100)
    finalized2 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized2)

    lifetime = load_lifetime_metrics()
    assert lifetime.ascension_victories["5"] == 1
    assert lifetime.ascension_victories["7"] == 1
    assert lifetime.highest_ascension_completed == 7

    # Session 3: Victory at A5 again (no new high, but still counts)
    session3 = init_session_metrics()
    session3.ascension_level = 5
    track("turns_taken", amount=100)
    finalized3 = finalize_session(victory=True, death_cause=None, death_level=0)
    update_lifetime_metrics(finalized3)

    lifetime = load_lifetime_metrics()
    assert lifetime.ascension_victories["5"] == 2  # Now 2 victories at A5
    assert lifetime.highest_ascension_completed == 7  # Still 7


def test_ascension_defeat_not_tracked(clean_metrics, tmp_path, monkeypatch):
    """Test that ascension_victories is NOT incremented on defeat."""
    import rsp.systems.metrics as game_metrics

    test_progress_file = tmp_path / "test_progress.json"
    monkeypatch.setattr(game_metrics, "_get_progress_file_path", lambda: test_progress_file)

    # Session: Defeat at A10
    session = init_session_metrics()
    session.ascension_level = 10
    track("turns_taken", amount=50)
    finalized = finalize_session(victory=False, death_cause="combat", death_level=3)
    update_lifetime_metrics(finalized)

    lifetime = load_lifetime_metrics()
    assert lifetime.ascension_victories.get(10, 0) == 0
    assert lifetime.highest_ascension_completed == 0


# Tests for highest_trace_reached tracking


def test_highest_trace_reached_tracking(clean_metrics):
    """Test that highest_trace_reached is tracked correctly."""
    from rsp.systems.metrics import init_session_metrics, track_highest_trace

    session = init_session_metrics()
    assert session.highest_trace_reached == 0.0

    # First trace increase
    track_highest_trace(25.0)
    assert session.highest_trace_reached == 25.0

    # Higher trace
    track_highest_trace(45.0)
    assert session.highest_trace_reached == 45.0

    # Lower trace (should not update)
    track_highest_trace(30.0)
    assert session.highest_trace_reached == 45.0  # Still 45

    # Even higher
    track_highest_trace(80.0)
    assert session.highest_trace_reached == 80.0


def test_highest_trace_serialization(clean_metrics):
    """Test that highest_trace_reached survives serialization."""
    session = SessionMetrics(session_id="test", timestamp_start=0.0)
    session.highest_trace_reached = 67.5

    # Serialize and deserialize
    data = session.to_dict()
    assert data["highest_trace_reached"] == 67.5

    restored = SessionMetrics.from_dict(data)
    assert restored.highest_trace_reached == 67.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
