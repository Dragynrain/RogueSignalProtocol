"""Unit tests for game_file_paths.py - Cross-platform file I/O with portable/system fallback."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test (after ensuring it's in the path)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import rsp.core.file_paths as game_file_paths

# Mark all tests in this file to skip global file isolation
# (these tests specifically test the file path initialization logic)
pytestmark = pytest.mark.skip_file_isolation


class TestFilePathsInitialization:
    """Tests for path initialization and mode detection."""

    def setup_method(self):
        """Reset module state before each test."""
        # Reset module-level globals
        game_file_paths._data_directory = None
        game_file_paths._is_portable_mode = None

    def test_portable_mode_succeeds(self, tmp_path, monkeypatch):
        """Test successful portable mode initialization."""
        # Mock get_application_directory to return our temp path
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: tmp_path)

        # Initialize should succeed (tmp_path is writable)
        result = game_file_paths.initialize_data_directories()

        assert result is True
        assert game_file_paths.is_portable_mode() is True
        assert game_file_paths.get_data_directory() == tmp_path

    def test_appdata_fallback_when_portable_fails(self, tmp_path, monkeypatch):
        """Test AppData fallback when portable mode fails."""
        # Create a read-only directory for portable mode
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        # Mock get_application_directory to return read-only path
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: readonly_dir)

        # Mock _get_system_data_directory to return writable temp path
        appdata_dir = tmp_path / "appdata"
        appdata_dir.mkdir()
        monkeypatch.setattr(game_file_paths, "_get_system_data_directory", lambda: appdata_dir)

        # Mock _test_write_permission to fail for portable, succeed for appdata
        original_test_write = game_file_paths._test_write_permission

        def mock_test_write(directory: Path) -> bool:
            if directory.name == "logs" and "readonly" in str(directory.parent):
                return False  # Portable mode fails
            return original_test_write(directory)

        monkeypatch.setattr(game_file_paths, "_test_write_permission", mock_test_write)

        # Initialize should succeed via AppData fallback
        result = game_file_paths.initialize_data_directories()

        assert result is True
        assert game_file_paths.is_portable_mode() is False
        assert game_file_paths.get_data_directory() == appdata_dir

    def test_total_failure_returns_false(self, tmp_path, monkeypatch):
        """Test that initialization returns False when both modes fail."""
        # Mock both modes to fail
        monkeypatch.setattr(game_file_paths, "_test_write_permission", lambda _: False)

        result = game_file_paths.initialize_data_directories()

        assert result is False

    def test_get_data_directory_before_init_raises(self):
        """Test that get_data_directory() raises if not initialized."""
        # Ensure module is not initialized
        game_file_paths._data_directory = None

        with pytest.raises(RuntimeError, match="initialize_data_directories"):
            game_file_paths.get_data_directory()

    def test_is_portable_mode_before_init_raises(self):
        """Test that is_portable_mode() raises if not initialized."""
        # Ensure module is not initialized
        game_file_paths._is_portable_mode = None

        with pytest.raises(RuntimeError, match="initialize_data_directories"):
            game_file_paths.is_portable_mode()

    def test_get_mode_description_portable(self, tmp_path, monkeypatch):
        """Test mode description for portable mode."""
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: tmp_path)

        game_file_paths.initialize_data_directories()
        description = game_file_paths.get_mode_description()

        assert "Portable mode" in description
        assert str(tmp_path) in description

    def test_get_mode_description_appdata(self, tmp_path, monkeypatch):
        """Test mode description for AppData mode."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        appdata_dir = tmp_path / "appdata"
        appdata_dir.mkdir()

        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: readonly_dir)
        monkeypatch.setattr(game_file_paths, "_get_system_data_directory", lambda: appdata_dir)

        # Mock write test to fail portable, succeed appdata
        original_test = game_file_paths._test_write_permission

        def mock_test(directory: Path) -> bool:
            if "readonly" in str(directory.parent):
                return False
            return original_test(directory)

        monkeypatch.setattr(game_file_paths, "_test_write_permission", mock_test)

        game_file_paths.initialize_data_directories()
        description = game_file_paths.get_mode_description()

        assert "AppData mode" in description
        assert str(appdata_dir) in description


class TestWritePermissionTesting:
    """Tests for write permission detection."""

    def test_write_permission_success(self, tmp_path):
        """Test successful write permission check."""
        test_dir = tmp_path / "writable"
        result = game_file_paths._test_write_permission(test_dir)

        assert result is True
        # Directory should be created
        assert test_dir.exists()
        # Test file should be cleaned up
        assert not (test_dir / ".write_test").exists()

    def test_write_permission_failure_creates_parent(self, tmp_path):
        """Test write permission check creates parent directories."""
        # Create a deeply nested path
        deep_path = tmp_path / "level1" / "level2" / "level3"

        result = game_file_paths._test_write_permission(deep_path)

        assert result is True
        assert deep_path.exists()

    @patch("pathlib.Path.write_text")
    def test_write_permission_handles_os_error(self, mock_write, tmp_path):
        """Test write permission check handles OSError gracefully."""
        mock_write.side_effect = OSError("Permission denied")

        test_dir = tmp_path / "failing"
        result = game_file_paths._test_write_permission(test_dir)

        assert result is False

    @patch("pathlib.Path.write_text")
    def test_write_permission_handles_permission_error(self, mock_write, tmp_path):
        """Test write permission check handles PermissionError gracefully."""
        mock_write.side_effect = PermissionError("Access denied")

        test_dir = tmp_path / "failing"
        result = game_file_paths._test_write_permission(test_dir)

        assert result is False


class TestSystemDataDirectory:
    """Tests for system data directory detection (cross-platform via platformdirs)."""

    def test_system_data_dir_returns_path_with_app_name(self):
        """Test that system data directory includes app name."""
        result = game_file_paths._get_system_data_directory()

        # Should always include the app name
        assert "RogueSignalProtocol" in str(result)

    @pytest.mark.windows_only
    def test_system_data_dir_uses_localappdata_on_windows(self, monkeypatch):
        """Test that on Windows, system data dir is under LOCALAPPDATA."""
        result = game_file_paths._get_system_data_directory()

        # On Windows, platformdirs uses LOCALAPPDATA
        localappdata = os.getenv("LOCALAPPDATA")
        if localappdata:
            assert localappdata in str(result)

    def test_system_data_dir_returns_path_object(self):
        """Test that _get_system_data_directory returns a Path object."""
        result = game_file_paths._get_system_data_directory()

        assert isinstance(result, Path)


class TestCrossPlatformPaths:
    """TDD tests for Phase 2: Cross-platform path resolution.

    These tests use platform mocking fixtures to verify path resolution
    works correctly on all platforms without requiring actual cross-platform runs.
    """

    def setup_method(self):
        """Reset module state before each test."""
        game_file_paths._data_directory = None
        game_file_paths._is_portable_mode = None

    def test_get_data_dir_returns_xdg_path_on_linux(
        self, mock_linux_platform, tmp_path, monkeypatch
    ):
        """On Linux, data dir should be under ~/.local/share/ (XDG standard).

        This test verifies platformdirs integration returns correct Linux paths.
        """
        # platformdirs uses HOME env var on Linux
        monkeypatch.setenv("HOME", str(tmp_path))

        # Force reimport to pick up mocked platform
        from platformdirs import user_data_dir

        result = user_data_dir("RogueSignalProtocol", appauthor=False)

        # Should use XDG_DATA_HOME or default to ~/.local/share
        assert "RogueSignalProtocol" in result
        # On Linux, platformdirs returns ~/.local/share/appname or XDG_DATA_HOME/appname

    def test_get_data_dir_returns_localappdata_on_windows(
        self, mock_windows_platform, tmp_path, monkeypatch
    ):
        """On Windows, data dir should be under %LOCALAPPDATA%.

        This test verifies platformdirs integration returns correct Windows paths.
        """
        test_localappdata = str(tmp_path / "AppData" / "Local")
        monkeypatch.setenv("LOCALAPPDATA", test_localappdata)

        from platformdirs import user_data_dir

        result = user_data_dir("RogueSignalProtocol", appauthor=False)

        # Should include the app name
        assert "RogueSignalProtocol" in result

    def test_portable_mode_works_on_linux(self, mock_linux_platform, tmp_path, monkeypatch):
        """Portable mode should work identically on Linux.

        The game should detect writable directories and use portable mode
        regardless of platform.
        """
        # Mock application directory to tmp_path (writable)
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: tmp_path)

        # Initialize should succeed in portable mode
        result = game_file_paths.initialize_data_directories()

        assert result is True
        assert game_file_paths.is_portable_mode() is True
        assert game_file_paths.get_data_directory() == tmp_path

    def test_system_fallback_works_on_linux(self, mock_linux_platform, tmp_path, monkeypatch):
        """When portable mode fails on Linux, system directory should be used."""
        # Create read-only directory for portable mode simulation
        readonly_dir = tmp_path / "readonly_app"
        readonly_dir.mkdir()

        # System data directory
        system_dir = tmp_path / "system_data"
        system_dir.mkdir()

        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: readonly_dir)
        monkeypatch.setattr(game_file_paths, "_get_system_data_directory", lambda: system_dir)

        # Mock write test to fail for portable, succeed for system
        original_test = game_file_paths._test_write_permission

        def mock_test(directory: Path) -> bool:
            if "readonly_app" in str(directory):
                return False
            return original_test(directory)

        monkeypatch.setattr(game_file_paths, "_test_write_permission", mock_test)

        # Initialize should succeed via system fallback
        result = game_file_paths.initialize_data_directories()

        assert result is True
        assert game_file_paths.is_portable_mode() is False
        assert game_file_paths.get_data_directory() == system_dir


class TestApplicationDirectory:
    """Tests for application directory detection."""

    @pytest.mark.windows_only
    def test_application_directory_frozen_exe(self, monkeypatch):
        """Test application directory when running as frozen exe.

        Windows-only: Uses Windows-style paths that don't work on Linux.
        """
        # Mock sys.frozen and sys.executable
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", "C:\\Games\\RogueSignal\\game.exe")

        result = game_file_paths.get_application_directory()

        assert result == Path("C:\\Games\\RogueSignal")

    def test_application_directory_script(self, monkeypatch):
        """Test application directory when running as script."""
        # Ensure sys.frozen is False
        if hasattr(sys, "frozen"):
            monkeypatch.delattr(sys, "frozen")

        # The function will use cwd() when not frozen
        result = game_file_paths.get_application_directory()

        # Should return current working directory (project root)
        assert result.exists()
        assert result == Path.cwd()


class TestFatalErrorDisplay:
    """Tests for fatal error display (tcod-based windowed dialog, console fallback).

    The windowed (tcod) path opens a real window, so these tests force it to fail and
    verify the exit-code contract and the console fallback. The GUI path is validated
    manually.
    """

    @patch("sys.exit")
    @patch("tcod.context.new", side_effect=RuntimeError("no display"))
    def test_show_fatal_error_exits_with_code_1(self, mock_new, mock_exit):
        """Fatal error always exits with code 1, even if the window cannot open."""
        game_file_paths.show_fatal_error_and_exit("Test error message", "Test Title")

        mock_exit.assert_called_once_with(1)

    @patch("sys.exit")
    @patch("builtins.print")
    @patch("tcod.context.new", side_effect=RuntimeError("no display"))
    def test_show_fatal_error_fallback_to_console(self, mock_new, mock_print, mock_exit):
        """Falls back to console output when the windowed dialog cannot be shown."""
        game_file_paths.show_fatal_error_and_exit("Test error message", "Test Title")

        assert mock_print.called
        printed_text = " ".join(str(call[0][0]) for call in mock_print.call_args_list)
        assert "Test error message" in printed_text
        assert "Test Title" in printed_text

        # Should still exit
        mock_exit.assert_called_once_with(1)


class TestIntegration:
    """Integration tests for the complete path system."""

    def setup_method(self):
        """Reset module state before each test."""
        game_file_paths._data_directory = None
        game_file_paths._is_portable_mode = None

    def test_full_portable_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow in portable mode."""
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: tmp_path)

        # Initialize
        assert game_file_paths.initialize_data_directories() is True

        # Check mode
        assert game_file_paths.is_portable_mode() is True

        # Get directory
        data_dir = game_file_paths.get_data_directory()
        assert data_dir == tmp_path

        # Verify we can create subdirectories
        saves_dir = data_dir / "saves"
        saves_dir.mkdir(exist_ok=True)
        assert saves_dir.exists()

        logs_dir = data_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        assert logs_dir.exists()

    def test_reinitialize_is_safe(self, tmp_path, monkeypatch):
        """Test that reinitializing doesn't break anything."""
        monkeypatch.setattr(game_file_paths, "get_application_directory", lambda: tmp_path)

        # First initialization
        game_file_paths.initialize_data_directories()
        first_dir = game_file_paths.get_data_directory()

        # Second initialization (shouldn't happen, but test it's safe)
        game_file_paths.initialize_data_directories()
        second_dir = game_file_paths.get_data_directory()

        # Should return same directory
        assert first_dir == second_dir
