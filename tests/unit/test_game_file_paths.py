"""Unit tests for game_file_paths.py - Windows file I/O with portable/AppData fallback."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test (after ensuring it's in the path)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import game_file_paths

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

        # Mock _get_appdata_directory to return writable temp path
        appdata_dir = tmp_path / "appdata"
        appdata_dir.mkdir()
        monkeypatch.setattr(game_file_paths, "_get_appdata_directory", lambda: appdata_dir)

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
        monkeypatch.setattr(game_file_paths, "_get_appdata_directory", lambda: appdata_dir)

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


class TestAppDataDirectory:
    """Tests for AppData directory detection."""

    def test_appdata_uses_localappdata_env(self, monkeypatch):
        """Test that AppData path uses LOCALAPPDATA environment variable."""
        test_appdata = "C:\\Users\\TestUser\\AppData\\Local"
        monkeypatch.setenv("LOCALAPPDATA", test_appdata)

        result = game_file_paths._get_appdata_directory()

        assert result == Path(test_appdata) / "RogueSignalProtocol"

    def test_appdata_fallback_when_env_not_set(self, monkeypatch):
        """Test AppData fallback when LOCALAPPDATA not set."""
        monkeypatch.delenv("LOCALAPPDATA", raising=False)

        result = game_file_paths._get_appdata_directory()

        # Should fall back to ~\AppData\Local
        assert "AppData" in str(result)
        assert "Local" in str(result)
        assert "RogueSignalProtocol" in str(result.name)


class TestApplicationDirectory:
    """Tests for application directory detection."""

    def test_application_directory_frozen_exe(self, monkeypatch):
        """Test application directory when running as frozen exe."""
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

        # The function will use __file__ from game_file_paths module
        result = game_file_paths.get_application_directory()

        # Should return parent of game_file_paths.py
        assert result.exists()
        assert (result / "game_file_paths.py").exists()


class TestFatalErrorDisplay:
    """Tests for fatal error display (MessageBox)."""

    @patch("ctypes.windll.user32.MessageBoxW")
    @patch("sys.exit")
    def test_show_fatal_error_displays_messagebox(self, mock_exit, mock_msgbox):
        """Test that fatal error shows Windows MessageBox."""
        game_file_paths.show_fatal_error_and_exit("Test error message", "Test Title")

        # Should call MessageBoxW
        mock_msgbox.assert_called_once()
        call_args = mock_msgbox.call_args[0]
        assert "Test error message" in call_args
        assert "Test Title" in call_args

        # Should exit with code 1
        mock_exit.assert_called_once_with(1)

    @patch("ctypes.windll.user32.MessageBoxW", side_effect=Exception("MessageBox failed"))
    @patch("sys.exit")
    @patch("builtins.print")
    def test_show_fatal_error_fallback_to_console(self, mock_print, mock_exit, mock_msgbox):
        """Test that fatal error falls back to console if MessageBox fails."""
        game_file_paths.show_fatal_error_and_exit("Test error message", "Test Title")

        # Should attempt MessageBox first
        mock_msgbox.assert_called_once()

        # Should fall back to print
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
