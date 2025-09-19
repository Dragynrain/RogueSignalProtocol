#!/usr/bin/env python3
"""
Unit tests for game_audio.py - Sound and music management system.
Tests audio initialization, sound loading, playback, and volume management.
"""

import pytest
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import os

# Import game modules
from game_audio import SoundManager, AUDIO_AVAILABLE
from game_config import GameSettings


class TestSoundManagerInitialization(unittest.TestCase):
    """Test SoundManager initialization and setup."""

    @patch('game_audio.pygame')
    def test_sound_manager_initialization_with_pygame(self, mock_pygame):
        """Test SoundManager initializes correctly when pygame is available."""
        mock_settings = Mock(spec=GameSettings)
        mock_settings.sfx_volume = 0.8
        mock_settings.music_volume = 0.6
        mock_settings.master_volume = 1.0

        with patch('game_audio.AUDIO_AVAILABLE', True):
            manager = SoundManager(mock_settings)

            self.assertEqual(manager.settings, mock_settings)
            self.assertTrue(manager.enabled)
            self.assertEqual(manager.sounds, {})
            self.assertIsNone(manager.current_music)
            self.assertFalse(manager.music_playing)
            self.assertEqual(manager.max_channels, 16)

            # Should initialize pygame mixer
            mock_pygame.mixer.pre_init.assert_called_once_with(
                frequency=22050, size=-16, channels=2, buffer=512
            )
            mock_pygame.mixer.init.assert_called_once()
            mock_pygame.mixer.set_num_channels.assert_called_once_with(16)

    @patch('game_audio.pygame')
    def test_sound_manager_initialization_without_pygame(self, mock_pygame):
        """Test SoundManager handles missing pygame gracefully."""
        with patch('game_audio.AUDIO_AVAILABLE', False):
            manager = SoundManager()

            self.assertFalse(manager.enabled)
            # Should not attempt to initialize pygame
            mock_pygame.mixer.pre_init.assert_not_called()

    @patch('game_audio.pygame')
    def test_sound_manager_initialization_pygame_error(self, mock_pygame):
        """Test SoundManager handles pygame initialization errors."""
        mock_pygame.mixer.init.side_effect = Exception("Mixer init failed")

        with patch('game_audio.AUDIO_AVAILABLE', True), \
             patch('game_audio.logging') as mock_logging:

            manager = SoundManager()

            # Should disable audio on error
            self.assertFalse(manager.enabled)
            mock_logging.warning.assert_called()

    def test_sound_manager_default_settings(self):
        """Test SoundManager creates default settings when none provided."""
        with patch('game_audio.AUDIO_AVAILABLE', False), \
             patch('game_audio.GameSettings') as mock_settings_class:

            mock_settings = Mock()
            mock_settings_class.return_value = mock_settings

            manager = SoundManager()

            # Should create default settings
            mock_settings_class.assert_called_once()
            self.assertEqual(manager.settings, mock_settings)


class TestSoundManagerVolumeControl(unittest.TestCase):
    """Test volume control and settings management."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_settings.sfx_volume = 0.8
        self.mock_settings.music_volume = 0.6
        self.mock_settings.master_volume = 1.0

        with patch('game_audio.AUDIO_AVAILABLE', False):
            self.manager = SoundManager(self.mock_settings)

    @patch('game_audio.pygame')
    def test_update_volumes(self, mock_pygame):
        """Test volume update from settings."""
        self.manager.enabled = True

        self.manager.update_volumes()

        # Should set music volume (music_volume * master_volume = 0.6 * 1.0 = 0.6)
        mock_pygame.mixer.music.set_volume.assert_called_once_with(0.6)

    @patch('game_audio.pygame')
    def test_update_volumes_disabled_audio(self, mock_pygame):
        """Test volume update when audio is disabled."""
        self.manager.enabled = False

        self.manager.update_volumes()

        # Should not interact with pygame when disabled
        mock_pygame.mixer.music.set_volume.assert_not_called()


class TestSoundManagerSoundLoading(unittest.TestCase):
    """Test sound loading and preloading functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('game_audio.AUDIO_AVAILABLE', False):
            self.manager = SoundManager()

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_load_sound_success(self, mock_exists, mock_pygame):
        """Test successful sound loading."""
        mock_exists.return_value = True
        mock_sound = Mock()
        mock_pygame.mixer.Sound.return_value = mock_sound
        self.manager.enabled = True

        self.manager.load_sound("test_sound", "test.wav")

        # load_sound doesn't return a value, just adds to sounds dict
        self.assertIn("test_sound", self.manager.sounds)
        self.assertEqual(self.manager.sounds["test_sound"], mock_sound)
        mock_pygame.mixer.Sound.assert_called_once_with(os.path.join("sound", "test.wav"))

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_load_sound_file_not_found(self, mock_exists, mock_pygame):
        """Test sound loading when file doesn't exist."""
        mock_exists.return_value = False
        self.manager.enabled = True

        with patch('game_audio.logging') as mock_logging:
            self.manager.load_sound("test_sound", "missing.wav")

            # load_sound returns None when file not found
            self.assertNotIn("test_sound", self.manager.sounds)
            mock_logging.warning.assert_called()

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_load_sound_pygame_error(self, mock_exists, mock_pygame):
        """Test sound loading handles pygame errors."""
        mock_exists.return_value = True
        mock_pygame.mixer.Sound.side_effect = Exception("Sound load failed")
        self.manager.enabled = True

        with patch('game_audio.logging') as mock_logging:
            self.manager.load_sound("test_sound", "test.wav")

            # load_sound returns None on error
            self.assertNotIn("test_sound", self.manager.sounds)
            mock_logging.error.assert_called()

    def test_load_sound_disabled_audio(self):
        """Test sound loading when audio is disabled."""
        self.manager.enabled = False

        self.manager.load_sound("test_sound", "test.wav")

        # load_sound returns None when disabled
        self.assertNotIn("test_sound", self.manager.sounds)

    @patch.object(SoundManager, 'load_sound')
    def test_preload_sounds(self, mock_load_sound):
        """Test preloading of standard game sounds."""
        mock_load_sound.return_value = True
        # Enable the manager so preload_sounds actually works
        self.manager.enabled = True

        self.manager.preload_sounds()

        # Should call load_sound for each expected sound (matching actual implementation)
        expected_sounds = [
            # Movement and actions
            ("player_move", "player_move.wav"),
            ("player_attack", "player_attack.wav"),
            ("stealth_attack", "stealth_attack.wav"),
            # Combat and alerts
            ("enemy_attack", "enemy_attack.wav"),
            ("enemy_death", "enemy_death.wav"),
            ("enemy_alert", "enemy_alert.wav"),
            ("enemy_hostile", "enemy_hostile.wav"),
            ("admin_spawn", "admin_spawn.wav"),
            ("enemies_alerted", "enemies_alerted.wav"),
            # Item interactions
            ("item_pickup_code", "item_pickup_code.wav"),
            ("item_pickup_exploit", "item_pickup_exploit.wav"),
            ("item_pickup_upgrade", "item_pickup_upgrade.wav"),
            ("item_pickup_story", "item_pickup_story.wav"),
            ("item_use_code", "item_use_code.wav"),
            # Environmental
            ("node_activate", "node_activate.wav"),
            # Player status
            ("player_death", "player_death.wav"),
            ("player_overheat", "player_overheat.wav"),
            ("virus_damage", "virus_damage.wav"),
            ("virus_infection", "virus_infection.wav"),
            ("critical_system_failure", "critical_system_failure.wav"),
            ("detection_threshold", "detection_threshold.wav"),
            ("overclocking", "overclocking.wav"),
            # Exploits
            ("exploit_shadow_step", "exploit_shadow_step.wav"),
            ("exploit_buffer_overflow", "exploit_buffer_overflow.wav"),
            ("exploit_code_injection", "exploit_code_injection.wav"),
            ("exploit_system_crash", "exploit_system_crash.wav"),
            ("exploit_threat_scan", "exploit_threat_scan.wav"),
            ("exploit_log_wiper", "exploit_log_wiper.wav"),
            ("exploit_antivirus", "exploit_antivirus.wav"),
            ("exploit_emp_burst", "exploit_emp_burst.wav"),
            ("exploit_memory_leak", "exploit_memory_leak.wav"),
            ("exploit_network_scan", "exploit_network_scan.wav"),
            ("exploit_failed", "exploit_failed.wav"),
            ("exploit_data_mimic", "exploit_data_mimic.wav"),
            ("exploit_noise_maker", "exploit_noise_maker.wav"),
            ("exploit_targeting", "exploit_targeting.wav"),
            # UI and system
            ("ui_menu_open", "ui_menu_open.wav"),
            ("level_complete", "level_complete.wav"),
        ]

        # Check that load_sound was called the expected number of times
        self.assertEqual(mock_load_sound.call_count, len(expected_sounds))

        # Verify individual calls were made
        for sound_id, filename in expected_sounds:
            mock_load_sound.assert_any_call(sound_id, filename)


class TestSoundManagerPlayback(unittest.TestCase):
    """Test sound playback functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_settings.sfx_volume = 0.8
        self.mock_settings.master_volume = 1.0

        with patch('game_audio.AUDIO_AVAILABLE', False):
            self.manager = SoundManager(self.mock_settings)

    @patch('game_audio.pygame')
    def test_play_sound_success(self, mock_pygame):
        """Test successful sound playback."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_pygame.mixer.find_channel.return_value = mock_channel

        self.manager.enabled = True
        self.manager.sounds["test_sound"] = mock_sound

        self.manager.play_sound("test_sound")

        # Should set volume on sound and play with channel
        mock_sound.set_volume.assert_called_once_with(0.8)
        mock_pygame.mixer.find_channel.assert_called_once()
        mock_channel.play.assert_called_once_with(mock_sound)

    @patch('game_audio.pygame')
    def test_play_sound_with_volume_modifier(self, mock_pygame):
        """Test sound playback with volume modifier."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_pygame.mixer.find_channel.return_value = mock_channel

        self.manager.enabled = True
        self.manager.sounds["test_sound"] = mock_sound

        self.manager.play_sound("test_sound", volume_modifier=0.5)

        # Should apply volume modifier (0.8 * 1.0 * 0.5 = 0.4)
        mock_sound.set_volume.assert_called_once_with(0.4)

    @patch('game_audio.pygame')
    def test_play_sound_priority_system(self, mock_pygame):
        """Test sound playback priority system."""
        mock_sound = Mock()
        mock_channel = Mock()
        mock_busy_channel = Mock()
        mock_busy_channel.get_busy.return_value = True

        # Simulate all channels busy
        mock_pygame.mixer.find_channel.return_value = None
        mock_pygame.mixer.Channel.return_value = mock_busy_channel

        self.manager.enabled = True
        self.manager.sounds["test_sound"] = mock_sound

        # Play with high priority should succeed (priority >= 8 stops channel 0)
        self.manager.play_sound("test_sound", priority=10)

        # Should stop channel 0 and use it for critical priority sound
        mock_pygame.mixer.Channel.assert_called_with(0)
        mock_busy_channel.stop.assert_called_once()
        mock_busy_channel.play.assert_called_once_with(mock_sound)

    def test_play_sound_not_loaded(self):
        """Test playing sound that hasn't been loaded."""
        self.manager.enabled = True

        # Should not raise exception, just return None
        result = self.manager.play_sound("nonexistent_sound")
        self.assertIsNone(result)

    def test_play_sound_disabled_audio(self):
        """Test playing sound when audio is disabled."""
        self.manager.enabled = False

        # Should not raise exception or log warnings
        self.manager.play_sound("test_sound")

    @patch('game_audio.pygame')
    def test_play_sound_no_available_channels(self, mock_pygame):
        """Test playing sound when no channels are available."""
        mock_sound = Mock()
        mock_busy_channel = Mock()
        mock_busy_channel.get_busy.return_value = True

        # All channels busy, low priority sound should use sound.play()
        mock_pygame.mixer.find_channel.return_value = None

        self.manager.enabled = True
        self.manager.sounds["test_sound"] = mock_sound

        result = self.manager.play_sound("test_sound", priority=0)

        # Should call sound.play() directly for low priority when no channels available
        mock_sound.play.assert_called_once()


class TestSoundManagerMusicPlayback(unittest.TestCase):
    """Test music playback functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_settings = Mock(spec=GameSettings)
        self.mock_settings.music_volume = 0.7
        self.mock_settings.master_volume = 1.0

        with patch('game_audio.AUDIO_AVAILABLE', False):
            self.manager = SoundManager(self.mock_settings)

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_play_music_success(self, mock_exists, mock_pygame):
        """Test successful music playback."""
        mock_exists.return_value = True
        self.manager.enabled = True

        self.manager.play_music("background.wav")

        # Should load and play music
        mock_pygame.mixer.music.load.assert_called_once_with(os.path.join("music", "background.wav"))
        mock_pygame.mixer.music.play.assert_called_once_with(-1)
        mock_pygame.mixer.music.set_volume.assert_called_once_with(0.7)

        self.assertEqual(self.manager.current_music, "background.wav")
        self.assertTrue(self.manager.music_playing)

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_play_music_with_fade_in(self, mock_exists, mock_pygame):
        """Test music playback with fade in effect."""
        mock_exists.return_value = True
        self.manager.enabled = True

        self.manager.play_music("background.wav", fade_in_ms=2000)

        mock_pygame.mixer.music.play.assert_called_once_with(-1, fade_ms=2000)

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_play_music_with_volume_multiplier(self, mock_exists, mock_pygame):
        """Test music playback with volume multiplier."""
        mock_exists.return_value = True
        self.manager.enabled = True

        self.manager.play_music("background.wav", volume_multiplier=0.5)

        # Should apply volume multiplier (0.7 * 1.0 * 0.5 = 0.35)
        mock_pygame.mixer.music.set_volume.assert_called_once_with(0.35)

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_play_music_file_not_found(self, mock_exists, mock_pygame):
        """Test music playback when file doesn't exist."""
        mock_exists.return_value = False
        self.manager.enabled = True

        with patch('game_audio.logging') as mock_logging:
            self.manager.play_music("missing.wav")

            mock_logging.warning.assert_called()
            mock_pygame.mixer.music.load.assert_not_called()

    @patch('game_audio.pygame')
    @patch('os.path.exists')
    def test_play_music_pygame_error(self, mock_exists, mock_pygame):
        """Test music playback handles pygame errors."""
        mock_exists.return_value = True
        mock_pygame.mixer.music.load.side_effect = Exception("Music load failed")
        self.manager.enabled = True

        with patch('game_audio.logging') as mock_logging:
            self.manager.play_music("background.wav")

            mock_logging.error.assert_called()

    def test_play_music_disabled_audio(self):
        """Test music playback when audio is disabled."""
        self.manager.enabled = False

        # Should not raise exception
        self.manager.play_music("background.wav")

    @patch('game_audio.pygame')
    def test_stop_music(self, mock_pygame):
        """Test stopping music playback."""
        self.manager.enabled = True
        self.manager.music_playing = True
        self.manager.current_music = "background.wav"

        self.manager.stop_music()

        mock_pygame.mixer.music.stop.assert_called_once()
        self.assertFalse(self.manager.music_playing)
        self.assertIsNone(self.manager.current_music)

    @patch('game_audio.pygame')
    def test_stop_music_with_fade_out(self, mock_pygame):
        """Test stopping music with fade out effect."""
        self.manager.enabled = True
        self.manager.music_playing = True

        self.manager.stop_music(fade_out_ms=1000)

        mock_pygame.mixer.music.fadeout.assert_called_once_with(1000)

    @patch('game_audio.pygame')
    def test_pause_unpause_music(self, mock_pygame):
        """Test pausing and unpausing music."""
        self.manager.enabled = True

        # Test pause
        self.manager.pause_music()
        mock_pygame.mixer.music.pause.assert_called_once()

        # Test unpause
        self.manager.unpause_music()
        mock_pygame.mixer.music.unpause.assert_called_once()

    @patch('game_audio.pygame')
    def test_is_music_playing(self, mock_pygame):
        """Test checking if music is playing."""
        self.manager.enabled = True

        # Test when music is playing
        mock_pygame.mixer.music.get_busy.return_value = True
        self.assertTrue(self.manager.is_music_playing())

        # Test when music is not playing
        mock_pygame.mixer.music.get_busy.return_value = False
        self.assertFalse(self.manager.is_music_playing())

    def test_is_music_playing_disabled_audio(self):
        """Test checking music status when audio is disabled."""
        self.manager.enabled = False

        self.assertFalse(self.manager.is_music_playing())


class TestSoundManagerUpdates(unittest.TestCase):
    """Test sound manager update and cleanup functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('game_audio.AUDIO_AVAILABLE', False):
            self.manager = SoundManager()

    @patch('game_audio.pygame')
    def test_update_music_state_tracking(self, mock_pygame):
        """Test update method tracks music state changes."""
        self.manager.enabled = True
        self.manager.music_playing = True

        # Music stops playing
        mock_pygame.mixer.music.get_busy.return_value = False

        self.manager.update()

        # Should update internal state
        self.assertFalse(self.manager.music_playing)
        self.assertIsNone(self.manager.current_music)

    def test_update_disabled_audio(self):
        """Test update method when audio is disabled."""
        self.manager.enabled = False

        # Should not raise exception
        self.manager.update()

    @patch('game_audio.pygame')
    def test_cleanup(self, mock_pygame):
        """Test cleanup method."""
        self.manager.enabled = True

        self.manager.cleanup()

        # Should quit pygame mixer
        mock_pygame.mixer.quit.assert_called_once()

    def test_cleanup_disabled_audio(self):
        """Test cleanup when audio is disabled."""
        self.manager.enabled = False

        # Should not raise exception
        self.manager.cleanup()


class TestSoundManagerIntegration(unittest.TestCase):
    """Test integration scenarios and edge cases."""

    @patch('game_audio.pygame')
    def test_full_audio_workflow(self, mock_pygame):
        """Test complete audio workflow."""
        mock_pygame.mixer.find_channel.return_value = Mock()
        mock_sound = Mock()
        mock_pygame.mixer.Sound.return_value = mock_sound

        with patch('os.path.exists', return_value=True), \
             patch('game_audio.AUDIO_AVAILABLE', True):

            manager = SoundManager()

            # Load a sound
            manager.load_sound("test_sound", "test.wav")
            self.assertIn("test_sound", manager.sounds)

            # Play the sound
            manager.play_sound("test_sound")

            # Play music
            manager.play_music("background.wav")

            # Update state
            manager.update()

            # Cleanup
            manager.cleanup()

            # Verify key operations were called
            mock_pygame.mixer.Sound.assert_called()
            mock_pygame.mixer.music.load.assert_called()
            mock_pygame.mixer.quit.assert_called()

    def test_settings_integration(self):
        """Test integration with game settings."""
        mock_settings = Mock(spec=GameSettings)
        mock_settings.sfx_volume = 0.5
        mock_settings.music_volume = 0.3

        with patch('game_audio.AUDIO_AVAILABLE', False):
            manager = SoundManager(mock_settings)

            self.assertEqual(manager.settings.sfx_volume, 0.5)
            self.assertEqual(manager.settings.music_volume, 0.3)

    @patch('game_audio.pygame')
    def test_error_recovery(self, mock_pygame):
        """Test error recovery in various scenarios."""
        self.manager = SoundManager()
        self.manager.enabled = True

        # Test sound playback error recovery
        mock_pygame.mixer.find_channel.side_effect = Exception("Channel error")

        with patch('game_audio.logging'):
            # Should not crash on error
            self.manager.play_sound("test_sound")

        # Test music playback error recovery
        mock_pygame.mixer.music.play.side_effect = Exception("Music error")

        with patch('game_audio.logging'), \
             patch('os.path.exists', return_value=True):
            # Should not crash on error
            self.manager.play_music("test.wav")


if __name__ == '__main__':
    unittest.main()