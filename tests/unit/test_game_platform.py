"""Unit tests for game_platform.py - Cross-platform detection utilities.

Tests platform detection functions using mocked sys.platform values.
These tests verify the game can correctly identify Windows, Linux, and macOS
without requiring actual cross-platform test runs.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import game_platform


class TestPlatformDetection:
    """Tests for is_windows(), is_linux(), is_macos() functions."""

    def test_is_windows_on_windows(self, mock_windows_platform):
        """is_windows() returns True when sys.platform is 'win32'."""
        # Re-import to pick up mocked platform
        assert game_platform.is_windows() is True
        assert game_platform.is_linux() is False
        assert game_platform.is_macos() is False

    def test_is_linux_on_linux(self, mock_linux_platform):
        """is_linux() returns True when sys.platform starts with 'linux'."""
        assert game_platform.is_linux() is True
        assert game_platform.is_windows() is False
        assert game_platform.is_macos() is False

    def test_is_macos_on_darwin(self, mock_macos_platform):
        """is_macos() returns True when sys.platform is 'darwin'."""
        assert game_platform.is_macos() is True
        assert game_platform.is_windows() is False
        assert game_platform.is_linux() is False

    def test_is_linux_handles_linux_variants(self, monkeypatch):
        """is_linux() handles various Linux platform strings."""
        # Test 'linux' (common)
        monkeypatch.setattr(sys, "platform", "linux")
        assert game_platform.is_linux() is True

        # Test 'linux2' (older Python/kernel)
        monkeypatch.setattr(sys, "platform", "linux2")
        assert game_platform.is_linux() is True

        # Test 'linux-armv7l' (ARM Linux)
        monkeypatch.setattr(sys, "platform", "linux-armv7l")
        assert game_platform.is_linux() is True


class TestGetPlatformName:
    """Tests for get_platform_name() function."""

    def test_platform_name_windows(self, mock_windows_platform):
        """get_platform_name() returns 'Windows' on Windows."""
        assert game_platform.get_platform_name() == "Windows"

    def test_platform_name_linux(self, mock_linux_platform):
        """get_platform_name() returns 'Linux' on Linux."""
        assert game_platform.get_platform_name() == "Linux"

    def test_platform_name_macos(self, mock_macos_platform):
        """get_platform_name() returns 'macOS' on macOS."""
        assert game_platform.get_platform_name() == "macOS"

    def test_platform_name_unknown(self, monkeypatch):
        """get_platform_name() returns 'Unknown' for unrecognized platforms."""
        monkeypatch.setattr(sys, "platform", "freebsd12")
        assert game_platform.get_platform_name() == "Unknown"


class TestSetDpiAwareness:
    """Tests for set_dpi_awareness() function."""

    def test_dpi_awareness_noop_on_linux(self, mock_linux_platform):
        """set_dpi_awareness() does nothing on Linux (no crash)."""
        # Should not raise any exception
        game_platform.set_dpi_awareness()

    def test_dpi_awareness_noop_on_macos(self, mock_macos_platform):
        """set_dpi_awareness() does nothing on macOS (no crash)."""
        # Should not raise any exception
        game_platform.set_dpi_awareness()

    @pytest.mark.windows_only
    def test_dpi_awareness_calls_windows_api(self, mock_windows_platform):
        """set_dpi_awareness() calls Windows DPI API on Windows."""
        # Mock the ctypes.windll calls
        mock_shcore = MagicMock()
        mock_user32 = MagicMock()

        with patch.object(game_platform.ctypes, "windll") as mock_windll:
            mock_windll.shcore = mock_shcore
            mock_windll.user32 = mock_user32

            game_platform.set_dpi_awareness()

            # Should try SetProcessDpiAwareness first
            mock_shcore.SetProcessDpiAwareness.assert_called_once_with(2)

    @pytest.mark.windows_only
    def test_dpi_awareness_fallback_on_old_windows(self, mock_windows_platform):
        """set_dpi_awareness() falls back to SetProcessDPIAware on older Windows."""
        mock_shcore = MagicMock()
        mock_user32 = MagicMock()

        # Make SetProcessDpiAwareness fail (simulating Windows 7)
        mock_shcore.SetProcessDpiAwareness.side_effect = Exception("Not available")

        with patch.object(game_platform.ctypes, "windll") as mock_windll:
            mock_windll.shcore = mock_shcore
            mock_windll.user32 = mock_user32

            game_platform.set_dpi_awareness()

            # Should fall back to SetProcessDPIAware
            mock_user32.SetProcessDPIAware.assert_called_once()

    @pytest.mark.windows_only
    def test_dpi_awareness_handles_total_failure(self, mock_windows_platform):
        """set_dpi_awareness() handles case where both APIs fail."""
        mock_shcore = MagicMock()
        mock_user32 = MagicMock()

        # Make both calls fail
        mock_shcore.SetProcessDpiAwareness.side_effect = Exception("Not available")
        mock_user32.SetProcessDPIAware.side_effect = Exception("Also not available")

        with patch.object(game_platform.ctypes, "windll") as mock_windll:
            mock_windll.shcore = mock_shcore
            mock_windll.user32 = mock_user32

            # Should not raise - just logs and continues
            game_platform.set_dpi_awareness()


class TestSteamDeckDetection:
    """Tests for is_steam_deck() function."""

    def test_steam_deck_returns_false_on_windows(self, mock_windows_platform):
        """is_steam_deck() returns False on Windows (non-Linux)."""
        assert game_platform.is_steam_deck() is False

    def test_steam_deck_returns_false_on_macos(self, mock_macos_platform):
        """is_steam_deck() returns False on macOS (non-Linux)."""
        assert game_platform.is_steam_deck() is False

    def test_steam_deck_detects_valve_board_vendor(self, mock_linux_platform):
        """is_steam_deck() returns True when DMI board vendor is Valve."""
        mock_file_content = "Valve"
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=MagicMock(
                        return_value=MagicMock(read=MagicMock(return_value=mock_file_content))
                    ),
                    __exit__=MagicMock(return_value=False),
                )
            ),
        ):
            assert game_platform.is_steam_deck() is True

    def test_steam_deck_returns_false_on_regular_linux(self, mock_linux_platform):
        """is_steam_deck() returns False on regular Linux without Valve hardware."""
        # Simulate file not found (no Valve board vendor file)
        with patch("builtins.open", MagicMock(side_effect=FileNotFoundError)):
            assert game_platform.is_steam_deck() is False

    def test_steam_deck_detects_steamos(self, mock_linux_platform):
        """is_steam_deck() returns True when SteamOS is in os-release."""

        def mock_open_side_effect(path, *args, **kwargs):
            if "board_vendor" in str(path):
                raise FileNotFoundError
            # os-release file with SteamOS
            mock_file = MagicMock()
            mock_file.__enter__ = MagicMock(
                return_value=MagicMock(read=MagicMock(return_value='NAME="SteamOS"\nVERSION="3.0"'))
            )
            mock_file.__exit__ = MagicMock(return_value=False)
            return mock_file

        with patch("builtins.open", MagicMock(side_effect=mock_open_side_effect)):
            assert game_platform.is_steam_deck() is True

    def test_platform_name_returns_steam_deck(self, mock_linux_platform):
        """get_platform_name() returns 'Steam Deck' when detected."""
        mock_file_content = "Valve"
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=MagicMock(
                        return_value=MagicMock(read=MagicMock(return_value=mock_file_content))
                    ),
                    __exit__=MagicMock(return_value=False),
                )
            ),
        ):
            assert game_platform.get_platform_name() == "Steam Deck"


class TestImportSafety:
    """Tests that game_platform.py can be imported on any platform."""

    def test_import_does_not_crash_on_linux(self, mock_linux_platform):
        """Importing game_platform on Linux doesn't crash."""
        # The module is already imported, but we can verify it works
        # by checking that the functions are callable
        assert callable(game_platform.is_windows)
        assert callable(game_platform.is_linux)
        assert callable(game_platform.set_dpi_awareness)

    def test_ctypes_windll_not_accessed_on_linux(self, mock_linux_platform):
        """set_dpi_awareness() doesn't access ctypes.windll on Linux."""
        with patch.object(game_platform, "ctypes") as mock_ctypes:
            game_platform.set_dpi_awareness()

            # windll should never be accessed on Linux
            assert not mock_ctypes.windll.called
