#!/usr/bin/env python3
"""
Audio System Tests - Category 5
Tests for rsp.systems.audio sound management functionality.

PHILOSOPHY: Audio is backed by an external dependency (miniaudio). We test:
1. Our wrapper handles miniaudio unavailability and device-init failure gracefully
2. Our exception handling works correctly
3. Our public API behaves as expected (volume math, dedup cooldown, music state)

We DO NOT test:
- miniaudio's internal implementation (trust the library)
- Actual audio output or real device behavior (no audio hardware in CI)

To avoid opening a real audio device, managers are constructed with AUDIO_AVAILABLE
patched off (so no PlaybackDevice is created), then `enabled` is forced True for the
tests that exercise playback logic. The mixer state (_voices, _music, _lock) exists
regardless of whether a device was opened.
"""

import unittest
from unittest.mock import patch

import numpy as np

from rsp.core.config import GameSettings
from rsp.systems.audio import SoundManager


def _make_disabled_manager(settings):
    """Construct a SoundManager without opening a real audio device."""
    with patch("rsp.systems.audio.AUDIO_AVAILABLE", False):
        return SoundManager(settings)


def _fake_samples(frames=10):
    """A small (frames, 2) int16 buffer standing in for a decoded sound."""
    return np.zeros((frames, 2), dtype=np.int16)


class TestSoundManagerAvailability(unittest.TestCase):
    """Test SoundManager handles backend availability correctly."""

    def tearDown(self):
        SoundManager._music_owner = None

    def test_sound_manager_when_miniaudio_unavailable(self):
        """Gracefully disables when miniaudio is not available."""
        with patch("rsp.systems.audio.AUDIO_AVAILABLE", False):
            settings = GameSettings()
            sound_manager = SoundManager(settings)

            self.assertFalse(sound_manager.enabled)
            self.assertEqual(sound_manager.settings, settings)

    def test_sound_manager_when_device_init_fails(self):
        """Handles a PlaybackDevice initialization exception by disabling."""
        with patch("rsp.systems.audio.AUDIO_AVAILABLE", True):
            with patch(
                "rsp.systems.audio.miniaudio.PlaybackDevice",
                side_effect=RuntimeError("no audio device"),
            ):
                sound_manager = SoundManager(GameSettings())

                # Should gracefully disable instead of crashing
                self.assertFalse(sound_manager.enabled)
                self.assertIsNone(sound_manager._device)

    def test_sound_manager_creates_default_settings(self):
        """Creates default settings if none provided."""
        with patch("rsp.systems.audio.AUDIO_AVAILABLE", False):
            sound_manager = SoundManager()

            self.assertIsNotNone(sound_manager.settings)
            self.assertIsInstance(sound_manager.settings, GameSettings)


class TestSoundLoading(unittest.TestCase):
    """Test sound file loading behavior."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = _make_disabled_manager(self.settings)

    def tearDown(self):
        SoundManager._music_owner = None

    @patch("os.path.exists")
    def test_load_sound_success(self, mock_exists):
        """Successful sound loading decodes and stores the sound buffer."""
        mock_exists.return_value = True
        samples = _fake_samples()

        self.sound_manager.enabled = True
        with patch.object(self.sound_manager, "_decode", return_value=samples):
            self.sound_manager.load_sound("test_sound", "test.wav")

        self.assertIn("test_sound", self.sound_manager.sounds)
        self.assertIs(self.sound_manager.sounds["test_sound"], samples)

    @patch("os.path.exists")
    def test_load_sound_missing_file_logs_warning(self, mock_exists):
        """Loading a missing file does not crash and stores nothing."""
        mock_exists.return_value = False

        self.sound_manager.enabled = True
        self.sound_manager.load_sound("missing_sound", "missing.wav")

        self.assertNotIn("missing_sound", self.sound_manager.sounds)

    def test_load_sound_when_disabled_does_nothing(self):
        """Loading when audio is disabled does nothing."""
        self.sound_manager.enabled = False
        self.sound_manager.load_sound("disabled_sound", "test.wav")

        self.assertNotIn("disabled_sound", self.sound_manager.sounds)

    def test_preload_sounds_loads_all_game_sounds(self):
        """preload_sounds requests all required game sounds."""
        self.sound_manager.enabled = True

        with patch.object(self.sound_manager, "load_sound") as mock_load:
            self.sound_manager.preload_sounds()

            mock_load.assert_any_call("player_move", "player_move.wav")
            mock_load.assert_any_call("enemy_alert", "enemy_alert.wav")
            mock_load.assert_any_call("exploit_system_hop", "exploit_system_hop.wav")

            # Should load many sounds (30+ in actual game)
            self.assertGreater(mock_load.call_count, 30)


class TestSoundPlayback(unittest.TestCase):
    """Test sound effect playback behavior."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = _make_disabled_manager(self.settings)

    def tearDown(self):
        SoundManager._music_owner = None

    def test_play_sound_when_disabled_returns_none(self):
        """Sound playback when audio is disabled returns None."""
        self.sound_manager.enabled = False

        result = self.sound_manager.play_sound("test_sound")

        self.assertIsNone(result)

    def test_play_sound_missing_raises_key_error(self):
        """Playing a sound that wasn't loaded raises KeyError (fail fast)."""
        self.sound_manager.enabled = True

        with self.assertRaises(KeyError):
            self.sound_manager.play_sound("missing_sound")

    def test_play_sound_calculates_volume_correctly(self):
        """Playback computes voice gain from sfx * master * modifier."""
        self.sound_manager.enabled = True
        self.sound_manager.sounds["test_sound"] = _fake_samples()
        self.settings.sfx_volume = 0.8
        self.settings.master_volume = 0.9

        voice = self.sound_manager.play_sound("test_sound", volume_modifier=0.5)

        expected_volume = 0.8 * 0.9 * 0.5
        self.assertIsNotNone(voice)
        self.assertAlmostEqual(voice.gain, expected_volume)
        self.assertIn(voice, self.sound_manager._voices)

    def test_play_sound_dedup_cooldown_skips_rapid_repeat(self):
        """A second identical play within the cooldown window is skipped."""
        self.sound_manager.enabled = True
        self.sound_manager.sounds["test_sound"] = _fake_samples()
        self.sound_manager.set_sound_cooldown(10.0)  # large window

        first = self.sound_manager.play_sound("test_sound")
        second = self.sound_manager.play_sound("test_sound")

        self.assertIsNotNone(first)
        self.assertIsNone(second)  # deduplicated
        self.assertEqual(len(self.sound_manager._voices), 1)

    def test_cooldown_not_recorded_when_sound_missing(self):
        """Cooldown is NOT recorded when the sound doesn't exist.

        Cooldown must only be recorded AFTER sound validation succeeds, otherwise a
        failed play would block subsequent valid plays of the same id.
        """
        self.sound_manager.enabled = True

        with self.assertRaises(KeyError):
            self.sound_manager.play_sound("nonexistent_sound")

        self.assertNotIn("nonexistent_sound", self.sound_manager._sound_last_played)


class TestMusicPlayback(unittest.TestCase):
    """Test background music functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = _make_disabled_manager(self.settings)

    def tearDown(self):
        SoundManager._music_owner = None

    def test_play_music_when_disabled_does_nothing(self):
        """Music playback when audio is disabled does nothing."""
        self.sound_manager.enabled = False
        self.sound_manager.play_music("test.ogg")

        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)

    @patch("os.path.exists")
    def test_play_music_missing_file_logs_warning(self, mock_exists):
        """Music playback with a missing file logs and leaves state clear."""
        mock_exists.return_value = False

        self.sound_manager.enabled = True
        self.sound_manager.play_music("missing.ogg")

        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)

    @patch("os.path.exists")
    def test_play_music_success_updates_state(self, mock_exists):
        """Successful music playback updates manager state and ownership."""
        mock_exists.return_value = True

        self.sound_manager.enabled = True
        with patch.object(self.sound_manager, "_decode", return_value=_fake_samples(100)):
            self.sound_manager.play_music("test.ogg")

        self.assertEqual(self.sound_manager.current_music, "test.ogg")
        self.assertTrue(self.sound_manager.music_playing)
        self.assertIsNotNone(self.sound_manager._music)
        self.assertIs(SoundManager._music_owner, self.sound_manager)

    @patch("os.path.exists")
    def test_play_music_exception_resets_state(self, mock_exists):
        """A decode/playback exception resets music state."""
        mock_exists.return_value = True

        self.sound_manager.enabled = True
        with patch.object(self.sound_manager, "_decode", side_effect=RuntimeError("decode")):
            self.sound_manager.play_music("error.ogg")

        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)

    def test_music_volume_caps_at_one(self):
        """Effective music volume is capped at 1.0 even with boost applied."""
        self.settings.music_volume = 1.0
        self.settings.master_volume = 1.0
        with patch.object(self.settings, "get_effective_music_boost", return_value=True):
            self.assertLessEqual(self.sound_manager._get_effective_music_volume(), 1.0)


class TestMusicControls(unittest.TestCase):
    """Test music control functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = _make_disabled_manager(self.settings)

    def tearDown(self):
        SoundManager._music_owner = None

    @patch("os.path.exists")
    def test_stop_music_resets_state(self, mock_exists):
        """Stopping music (no fade) resets manager state and ownership."""
        mock_exists.return_value = True
        self.sound_manager.enabled = True
        with patch.object(self.sound_manager, "_decode", return_value=_fake_samples(100)):
            self.sound_manager.play_music("test.ogg")

        self.sound_manager.stop_music()

        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)
        self.assertIsNone(self.sound_manager._music)
        self.assertIsNone(SoundManager._music_owner)

    @patch("os.path.exists")
    def test_is_music_playing_reflects_global_state(self, mock_exists):
        """is_music_playing reports the single global music stream across managers."""
        mock_exists.return_value = True
        self.sound_manager.enabled = True
        with patch.object(self.sound_manager, "_decode", return_value=_fake_samples(100)):
            self.sound_manager.play_music("test.ogg")

        # A different (disabled) manager still sees the global music as playing.
        other = _make_disabled_manager(self.settings)
        self.assertTrue(other.is_music_playing())

    def test_is_music_playing_when_no_music_returns_false(self):
        """is_music_playing returns False when nothing is playing."""
        SoundManager._music_owner = None
        self.assertFalse(self.sound_manager.is_music_playing())


class TestSoundSystemUpdate(unittest.TestCase):
    """Test sound system update and cleanup functionality."""

    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = _make_disabled_manager(self.settings)

    def tearDown(self):
        SoundManager._music_owner = None

    def test_update_detects_music_stopped(self):
        """update detects when the mixer has dropped finished music."""
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.ogg"
        self.sound_manager._music = None  # mixer finished/dropped the track
        SoundManager._music_owner = self.sound_manager

        self.sound_manager.update()

        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)
        self.assertIsNone(SoundManager._music_owner)

    def test_cleanup_clears_state(self):
        """cleanup clears voices/music and releases ownership without a real device."""
        self.sound_manager.enabled = True
        self.sound_manager._voices = [object()]
        self.sound_manager._device = None  # no real device in tests
        SoundManager._music_owner = self.sound_manager

        self.sound_manager.cleanup()

        self.assertEqual(self.sound_manager._voices, [])
        self.assertIsNone(self.sound_manager._music)
        self.assertIsNone(SoundManager._music_owner)


class TestAssetFileCaseSensitivity(unittest.TestCase):
    """Cross-platform tests verifying asset file references match actual files.

    Linux is case-sensitive, so 'Victory.wav' != 'victory.wav'.
    These tests catch case mismatches that would break on Linux.
    """

    def test_victory_music_file_exists_with_correct_case(self):
        """Test that victory.wav exists with lowercase name (Linux-compatible)."""
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent
        music_dir = project_root / "music"
        expected_file = music_dir / "victory.wav"

        self.assertTrue(
            expected_file.exists(),
            f"Music file 'victory.wav' not found at {expected_file}. "
            "Check if file exists with different case (e.g., 'Victory.wav'). "
            "Linux is case-sensitive!",
        )

    def test_all_music_files_are_lowercase(self):
        """Verify all music filenames are lowercase (convention check)."""
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
                    f"Music file '{filename}' should be lowercase for Linux compatibility",
                )


if __name__ == "__main__":
    unittest.main()
