#!/usr/bin/env python3
"""
Unit tests for debug export system.

Tests the debug package creation, file collection, and ZIP generation.
"""

import json
import zipfile
from unittest.mock import Mock, patch

import pytest

from debug_export import DebugExporter, export_crash_report, export_debug_package


@pytest.fixture
def temp_export_dir(tmp_path, monkeypatch):
    """Create temporary export directory."""
    export_dir = tmp_path / "debug_exports"
    export_dir.mkdir()

    # Mock the _get_export_dir function to use temp directory
    from debug_export import DebugExporter

    monkeypatch.setattr(DebugExporter, "_get_export_dir", lambda: export_dir)

    yield export_dir


@pytest.fixture
def temp_game_dirs(tmp_path, monkeypatch):
    """Create temporary game directories with sample files."""
    # Create saves directory with sample files
    saves_dir = tmp_path / "saves"
    saves_dir.mkdir()
    (saves_dir / "rogue_signal_save.json").write_text('{"level": 1}')
    (saves_dir / "rogue_signal_progress.json").write_text('{"fragments": [0, 1, 2]}')
    (saves_dir / "user_settings.json").write_text('{"volume": 0.7}')

    # Create logs directory with sample files
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "game_debug.log").write_text("DEBUG: Test log entry\n")
    (logs_dir / "game_errors.log").write_text("ERROR: Test error\n")

    # Create metrics directory with sample file
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    (metrics_dir / "session_12345.json").write_text('{"session": "test"}')

    # Mock get_data_directory to return tmp_path
    import game_file_paths

    monkeypatch.setattr(game_file_paths, "get_data_directory", lambda: tmp_path)

    yield tmp_path


@pytest.fixture
def mock_game_engine():
    """Create a mock game engine for testing."""
    game = Mock()
    game.level = 3
    game.turn = 42
    game.game_over = False

    # Mock game state
    game.game_state = Mock()
    game.game_state.dungeon_seed = 12345

    # Mock player
    game.player = Mock()
    game.player.x = 10
    game.player.y = 15
    game.player.cpu = 85
    game.player.max_cpu = 100
    game.player.heat = 20
    game.player.trace_level = 1
    game.player.position = Mock(x=10, y=15)

    # Mock inventory manager
    game.player.inventory_manager = Mock()
    game.player.inventory_manager.equipped_exploits = ["code_injection", "system_hop"]

    # Mock enemies
    enemy1 = Mock()
    enemy1.type = "virus"
    enemy1.position = Mock(x=5, y=5)
    enemy1.state = Mock(value="HUNTING")
    enemy1.cpu = 50

    enemy2 = Mock()
    enemy2.type = "scanner"
    enemy2.position = Mock(x=20, y=20)
    enemy2.state = Mock(value="PATROLLING")
    enemy2.cpu = 30

    game.enemies = [enemy1, enemy2]

    return game


def test_create_debug_package_basic(temp_export_dir, temp_game_dirs):
    """Test basic debug package creation."""
    zip_path = DebugExporter.create_debug_package()

    assert zip_path is not None
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"
    assert "debug_" in zip_path.name

    # Verify it's a valid ZIP
    assert zipfile.is_zipfile(zip_path)


def test_debug_package_contains_system_info(temp_export_dir, temp_game_dirs):
    """Test that debug package includes system_info.txt."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "system_info.txt" in zipf.namelist()

        # Read and verify system info content
        system_info = zipf.read("system_info.txt").decode("utf-8")
        assert "SYSTEM INFORMATION" in system_info
        assert "Python Version" in system_info
        assert "Platform" in system_info
        assert "Export Time" in system_info


def test_debug_package_includes_saves(temp_export_dir, temp_game_dirs):
    """Test that debug package includes saves directory."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        filenames = zipf.namelist()

        # Check for saves files
        assert any("saves/rogue_signal_save.json" in f for f in filenames)
        assert any("saves/rogue_signal_progress.json" in f for f in filenames)
        assert any("saves/user_settings.json" in f for f in filenames)


def test_debug_package_includes_logs(temp_export_dir, temp_game_dirs):
    """Test that debug package includes logs directory."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        filenames = zipf.namelist()

        # Check for log files
        assert any("logs/game_debug.log" in f for f in filenames)
        assert any("logs/game_errors.log" in f for f in filenames)


def test_debug_package_includes_metrics(temp_export_dir, temp_game_dirs):
    """Test that debug package includes metrics directory."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        filenames = zipf.namelist()

        # Check for metrics files
        assert any("metrics/" in f for f in filenames)


def test_debug_package_includes_reproduction_template(temp_export_dir, temp_game_dirs):
    """Test that debug package includes reproduction steps template."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "PLEASE_FILL_OUT.txt" in zipf.namelist()

        # Verify template content
        template = zipf.read("PLEASE_FILL_OUT.txt").decode("utf-8")
        assert "REPRODUCTION STEPS" in template
        assert "What were you doing" in template
        assert "What did you expect" in template


def test_debug_package_includes_config_hashes(temp_export_dir, temp_game_dirs):
    """Test that debug package includes config file hashes."""
    zip_path = DebugExporter.create_debug_package()

    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "config_hashes.txt" in zipf.namelist()

        # Verify hash content
        hashes = zipf.read("config_hashes.txt").decode("utf-8")
        assert "CONFIG FILE HASHES" in hashes


def test_debug_package_with_game_snapshot(temp_export_dir, temp_game_dirs, mock_game_engine):
    """Test that debug package includes game snapshot when game engine provided."""
    zip_path = DebugExporter.create_debug_package(game_engine=mock_game_engine)

    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "game_snapshot.json" in zipf.namelist()

        # Read and verify snapshot content
        snapshot_data = zipf.read("game_snapshot.json").decode("utf-8")
        snapshot = json.loads(snapshot_data)

        assert snapshot["level"] == 3
        assert snapshot["turn"] == 42
        assert snapshot["dungeon_seed"] == 12345
        assert snapshot["player"]["cpu"] == 85
        assert len(snapshot["enemies"]) == 2


def test_debug_package_with_crash_info(temp_export_dir, temp_game_dirs):
    """Test that crash information is included when provided."""
    crash_info = "Exception: ValueError\nStack trace: line 42"
    zip_path = DebugExporter.create_debug_package(crash_info=crash_info)

    with zipfile.ZipFile(zip_path, "r") as zipf:
        system_info = zipf.read("system_info.txt").decode("utf-8")

        assert "CRASH INFORMATION" in system_info
        assert "ValueError" in system_info
        assert "Stack trace" in system_info


def test_export_debug_package_convenience_function(
    temp_export_dir, temp_game_dirs, mock_game_engine
):
    """Test the convenience function for exporting debug packages."""
    zip_path = export_debug_package(game_engine=mock_game_engine)

    assert zip_path is not None
    assert zip_path.exists()
    assert zipfile.is_zipfile(zip_path)


def test_export_crash_report_function(temp_export_dir, temp_game_dirs, mock_game_engine):
    """Test the crash report export function."""
    try:
        raise ValueError("Test exception for crash report")
    except ValueError as e:
        zip_path = export_crash_report(e, game_engine=mock_game_engine)

    assert zip_path is not None
    assert zip_path.exists()

    # Verify crash info is included
    with zipfile.ZipFile(zip_path, "r") as zipf:
        system_info = zipf.read("system_info.txt").decode("utf-8")
        assert "CRASH INFORMATION" in system_info
        assert "ValueError" in system_info
        assert "Test exception for crash report" in system_info


def test_debug_package_handles_missing_directories(temp_export_dir):
    """Test that debug package creation handles missing directories gracefully."""
    # Don't create temp_game_dirs - test with missing directories
    zip_path = DebugExporter.create_debug_package()

    # Should still create a package even if directories don't exist
    assert zip_path is not None
    assert zip_path.exists()

    # Should still have system info
    with zipfile.ZipFile(zip_path, "r") as zipf:
        assert "system_info.txt" in zipf.namelist()


def test_debug_package_error_handling(temp_export_dir, temp_game_dirs):
    """Test error handling when package creation fails."""
    # Mock zipfile to raise an exception
    with patch("zipfile.ZipFile", side_effect=Exception("Simulated failure")):
        zip_path = DebugExporter.create_debug_package()

        # Should return None on failure
        assert zip_path is None


def test_multiple_debug_packages_unique_names(temp_export_dir, temp_game_dirs):
    """Test that multiple debug packages get unique timestamped names."""
    import time

    zip_path1 = DebugExporter.create_debug_package()
    time.sleep(1.1)  # Sleep >1 second to ensure different timestamps (format is YYYY-MM-DD_HHMMSS)
    zip_path2 = DebugExporter.create_debug_package()

    assert zip_path1 != zip_path2
    assert zip_path1.name != zip_path2.name
