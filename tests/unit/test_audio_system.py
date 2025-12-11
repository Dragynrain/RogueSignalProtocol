#!/usr/bin/env python3
"""
Audio System Tests - Category 5
Tests for game_audio.py sound management functionality.

PHILOSOPHY: Audio is an external dependency (pygame). We test:
1. Our wrapper handles pygame unavailability gracefully
2. Our exception handling works correctly
3. Our public API behaves as expected

We DO NOT test:
- pygame's internal implementation (trust the library)
- Simple delegation to pygame (no value)
- Implementation details (internal state)
"""

import unittest
from unittest.mock import Mock, patch

# Import game modules
from game_audio import SoundManager
from game_config import GameSettings


class TestSoundManagerAvailability(unittest.TestCase):
    """Test SoundManager handles pygame availability correctly."""

    def test_sound_manager_when_pygame_unavailable(self):
        """Test SoundManager gracefully disables when pygame is not available."""
        with patch("game_audio.AUDIO_AVAILABLE", False):
            settings = GameSettings()
            sound_manager = SoundManager(settings)

            self.assertFalse(sound_manager.enabled)
            self.assertEqual(sound_manager.settings, settings)

    def test_sound_manager_when_pygame_init_fails(self):
        """Test SoundManager handles pygame initialization exceptions."""
        with patch("game_audio.AUDIO_AVAILABLE", True):
            with patch("pygame.mixer.init", side_effect=Exception("Init failed")):
                settings = GameSettings()
                sound_manager = SoundManager(settings)

                # Should gracefully disable instead of crashing
                self.assertFalse(sound_manager.enabled)

    def test_sound_manager_creates_default_settings(self):
        """Test SoundManager creates default settings if none provided."""
        with patch("game_audio.AUDIO_AVAILABLE", False):
            sound_manager = SoundManager()

            self.assertIsNotNone(sound_manager.settings)
            self.assertIsInstance(sound_manager.settings, GameSettings)


class TestSoundLoading(unittest.TestCase):
    """Test sound file loading behavior."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.Sound")
    @patch("os.path.exists")
    def test_load_sound_success(self, mock_exists, mock_sound):
        """Test successful sound loading stores sound in dictionary."""
        mock_exists.return_value = True
        mock_sound_obj = Mock()
        mock_sound.return_value = mock_sound_obj

        self.sound_manager.enabled = True
        self.sound_manager.load_sound("test_sound", "test.wav")

        self.assertIn("test_sound", self.sound_manager.sounds)
        self.assertEqual(self.sound_manager.sounds["test_sound"], mock_sound_obj)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("os.path.exists")
    def test_load_sound_missing_file_logs_warning(self, mock_exists):
        """Test loading missing file logs warning and doesn't crash."""
        mock_exists.return_value = False

        self.sound_manager.enabled = True
        # Should not raise exception
        self.sound_manager.load_sound("missing_sound", "missing.wav")

        self.assertNotIn("missing_sound", self.sound_manager.sounds)

    def test_load_sound_when_disabled_does_nothing(self):
        """Test loading when audio is disabled does nothing."""
        self.sound_manager.enabled = False
        self.sound_manager.load_sound("disabled_sound", "test.wav")

        self.assertNotIn("disabled_sound", self.sound_manager.sounds)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    def test_preload_sounds_loads_all_game_sounds(self):
        """Test preload_sounds loads all required game sounds."""
        self.sound_manager.enabled = True

        with patch.object(self.sound_manager, "load_sound") as mock_load:
            self.sound_manager.preload_sounds()

            # Verify key gameplay sounds are loaded
            mock_load.assert_any_call("player_move", "player_move.wav")
            mock_load.assert_any_call("enemy_alert", "enemy_alert.wav")
            mock_load.assert_any_call("exploit_system_hop", "exploit_system_hop.wav")

            # Should load many sounds (30+ in actual game)
            self.assertGreater(mock_load.call_count, 30)


class TestSoundPlayback(unittest.TestCase):
    """Test sound effect playback behavior."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)

    def test_play_sound_when_disabled_returns_none(self):
        """Test sound playback when audio is disabled returns None."""
        self.sound_manager.enabled = False

        result = self.sound_manager.play_sound("test_sound")

        self.assertIsNone(result)

    def test_play_sound_missing_raises_key_error(self):
        """Test playing a sound that wasn't loaded raises KeyError."""
        self.sound_manager.enabled = True

        # Should raise KeyError - fail fast instead of hiding errors
        with self.assertRaises(KeyError):
            self.sound_manager.play_sound("missing_sound")

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.find_channel")
    def test_play_sound_calculates_volume_correctly(self, mock_find_channel):
        """Test sound playback calculates final volume from settings and modifier."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_find_channel.return_value = mock_channel

        self.sound_manager.enabled = True
        self.sound_manager.sounds["test_sound"] = mock_sound
        self.settings.sfx_volume = 0.8
        self.settings.master_volume = 0.9

        self.sound_manager.play_sound("test_sound", volume_modifier=0.5)

        expected_volume = 0.8 * 0.9 * 0.5  # sfx * master * modifier
        mock_sound.set_volume.assert_called_with(expected_volume)


class TestMusicPlayback(unittest.TestCase):
    """Test background music functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)

    def test_play_music_when_disabled_does_nothing(self):
        """Test music playback when audio is disabled."""
        self.sound_manager.enabled = False
        self.sound_manager.play_music("test.ogg")

        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("os.path.exists")
    def test_play_music_missing_file_logs_warning(self, mock_exists):
        """Test music playback with missing file logs warning."""
        mock_exists.return_value = False

        self.sound_manager.enabled = True
        self.sound_manager.play_music("missing.ogg")

        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.load")
    @patch("pygame.mixer.music.play")
    @patch("pygame.mixer.music.set_volume")
    @patch("os.path.exists")
    def test_play_music_success_updates_state(
        self, mock_exists, mock_set_volume, mock_play, mock_load
    ):
        """Test successful music playback updates manager state."""
        mock_exists.return_value = True

        self.sound_manager.enabled = True
        self.sound_manager.play_music("test.ogg")

        self.assertEqual(self.sound_manager.current_music, "test.ogg")
        self.assertTrue(self.sound_manager.music_playing)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.load")
    @patch("pygame.mixer.music.set_volume")
    @patch("os.path.exists")
    def test_play_music_volume_caps_at_one(self, mock_exists, mock_set_volume, mock_load):
        """Test music volume is capped at 1.0."""
        mock_exists.return_value = True

        self.sound_manager.enabled = True
        self.settings.music_volume = 1.0
        self.settings.master_volume = 1.0

        self.sound_manager.play_music("test.ogg")

        mock_set_volume.assert_called_with(1.0)  # Capped at 1.0

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.load")
    def test_play_music_exception_resets_state(self, mock_load):
        """Test music playback exception handling resets state."""
        mock_load.side_effect = Exception("Load error")

        self.sound_manager.enabled = True

        with patch("os.path.exists", return_value=True):
            self.sound_manager.play_music("error.ogg")

        # Should reset state on error
        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)


class TestMusicControls(unittest.TestCase):
    """Test music control functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.stop")
    def test_stop_music_resets_state(self, mock_stop):
        """Test stopping music resets manager state."""
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.ogg"

        self.sound_manager.stop_music()

        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.get_busy")
    def test_is_music_playing_returns_pygame_state(self, mock_get_busy):
        """Test is_music_playing returns pygame's actual state."""
        mock_get_busy.return_value = True
        self.sound_manager.enabled = True

        result = self.sound_manager.is_music_playing()

        self.assertTrue(result)

    def test_is_music_playing_when_disabled_returns_false(self):
        """Test is_music_playing when audio is disabled returns False."""
        self.sound_manager.enabled = False

        result = self.sound_manager.is_music_playing()

        self.assertFalse(result)


class TestSoundSystemUpdate(unittest.TestCase):
    """Test sound system update and cleanup functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.get_busy")
    def test_update_detects_music_stopped(self, mock_get_busy):
        """Test update detects when music has stopped playing."""
        mock_get_busy.return_value = False
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.ogg"

        self.sound_manager.update()

        # Should detect music stopped and reset state
        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)

    @patch("game_audio.AUDIO_AVAILABLE", True)
    @patch("pygame.mixer.music.stop")
    @patch("pygame.mixer.stop")
    @patch("pygame.mixer.quit")
    def test_cleanup_calls_pygame_cleanup(self, mock_quit, mock_stop, mock_music_stop):
        """Test cleanup calls all pygame cleanup functions."""
        self.sound_manager.enabled = True

        self.sound_manager.cleanup()

        mock_music_stop.assert_called_once()
        mock_stop.assert_called_once()
        mock_quit.assert_called_once()


class TestAssetFileCaseSensitivity(unittest.TestCase):
    """Cross-platform tests verifying asset file references match actual files.

    Linux is case-sensitive, so 'Victory.wav' != 'victory.wav'.
    These tests catch case mismatches that would break on Linux.
    """

    def test_victory_music_file_exists_with_correct_case(self):
        """Test that victory.wav exists with lowercase name (Linux-compatible)."""
        import os
        from pathlib import Path

        # Get the music directory
        project_root = Path(__file__).parent.parent.parent
        music_dir = project_root / "music"

        # The code references "victory.wav" (lowercase)
        expected_file = music_dir / "victory.wav"

        # This test will FAIL if file is named "Victory.wav" (uppercase)
        # because on Linux, case matters
        self.assertTrue(
            expected_file.exists(),
            f"Music file 'victory.wav' not found at {expected_file}. "
            "Check if file exists with different case (e.g., 'Victory.wav'). "
            "Linux is case-sensitive!"
        )

    def test_all_music_files_are_lowercase(self):
        """Verify all music filenames are lowercase (convention check)."""
        import os
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        music_dir = project_root / "music"

        if not music_dir.exists():
            self.skipTest("Music directory not found")

        for music_file in music_dir.iterdir():
            if music_file.is_file():
                filename = music_file.name
                self.assertEqual(
                    filename,
                    filename.lower(),
                    f"Music file '{filename}' should be lowercase for Linux compatibility"
                )


if __name__ == "__main__":
    unittest.main()
