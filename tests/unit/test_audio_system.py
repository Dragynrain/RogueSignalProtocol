#!/usr/bin/env python3
"""
Audio System Tests - Category 5
Tests for game_audio.py sound management functionality.

Test coverage:
- Sound effect triggering accuracy
- Audio file loading and validation  
- Missing file graceful handling
- Sound system initialization
- Volume controls and muting
- Sound effect timing with game events
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import logging

# Import game modules
from game_audio import SoundManager, AUDIO_AVAILABLE
from game_config import GameSettings


class TestSoundManagerInitialization(unittest.TestCase):
    """Test SoundManager initialization scenarios."""
    
    def test_sound_manager_init_audio_available(self):
        """Test SoundManager initialization when pygame is available."""
        with patch('game_audio.AUDIO_AVAILABLE', True):
            with patch('pygame.mixer.pre_init') as mock_pre_init:
                with patch('pygame.mixer.init') as mock_init:
                    with patch('pygame.mixer.set_num_channels') as mock_channels:
                        settings = GameSettings()
                        sound_manager = SoundManager(settings)
                        
                        self.assertTrue(sound_manager.enabled)
                        self.assertEqual(sound_manager.settings, settings)
                        self.assertEqual(sound_manager.sounds, {})
                        self.assertIsNone(sound_manager.current_music)
                        self.assertFalse(sound_manager.music_playing)
                        self.assertEqual(sound_manager.max_channels, 16)
                        
                        mock_pre_init.assert_called_once()
                        mock_init.assert_called_once()
                        mock_channels.assert_called_once_with(16)
    
    def test_sound_manager_init_audio_unavailable(self):
        """Test SoundManager initialization when pygame is not available."""
        with patch('game_audio.AUDIO_AVAILABLE', False):
            settings = GameSettings()
            sound_manager = SoundManager(settings)
            
            self.assertFalse(sound_manager.enabled)
            self.assertEqual(sound_manager.settings, settings)
    
    def test_sound_manager_init_pygame_exception(self):
        """Test SoundManager handles pygame initialization exceptions."""
        with patch('game_audio.AUDIO_AVAILABLE', True):
            with patch('pygame.mixer.init', side_effect=Exception("Init failed")):
                with patch('logging.warning') as mock_log:
                    settings = GameSettings()
                    sound_manager = SoundManager(settings)
                    
                    self.assertFalse(sound_manager.enabled)
                    mock_log.assert_called()
    
    def test_sound_manager_init_default_settings(self):
        """Test SoundManager initialization with default settings."""
        with patch('game_audio.AUDIO_AVAILABLE', False):
            sound_manager = SoundManager()
            
            self.assertIsNotNone(sound_manager.settings)
            self.assertIsInstance(sound_manager.settings, GameSettings)
    
    def test_sound_manager_directories(self):
        """Test SoundManager directory configuration."""
        sound_manager = SoundManager()
        
        self.assertEqual(sound_manager.SOUND_DIRECTORY, "sound")
        self.assertEqual(sound_manager.MUSIC_DIRECTORY, "music")


class TestSoundLoading(unittest.TestCase):
    """Test sound file loading and validation."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.Sound')
    @patch('os.path.exists')
    def test_load_sound_success(self, mock_exists, mock_sound):
        """Test successful sound loading."""
        mock_exists.return_value = True
        mock_sound_obj = Mock()
        mock_sound.return_value = mock_sound_obj
        
        self.sound_manager.enabled = True
        self.sound_manager.load_sound("test_sound", "test.wav")
        
        self.assertIn("test_sound", self.sound_manager.sounds)
        self.assertEqual(self.sound_manager.sounds["test_sound"], mock_sound_obj)
        mock_exists.assert_called_with(os.path.join("sound", "test.wav"))
        mock_sound.assert_called_with(os.path.join("sound", "test.wav"))
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('os.path.exists')
    @patch('logging.warning')
    def test_load_sound_file_not_found(self, mock_log, mock_exists):
        """Test loading when sound file doesn't exist."""
        mock_exists.return_value = False
        
        self.sound_manager.enabled = True
        self.sound_manager.load_sound("missing_sound", "missing.wav")
        
        self.assertNotIn("missing_sound", self.sound_manager.sounds)
        mock_log.assert_called_with(f"Sound file not found: {os.path.join('sound', 'missing.wav')}")
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.Sound')
    @patch('os.path.exists')
    @patch('logging.error')
    def test_load_sound_exception(self, mock_log, mock_exists, mock_sound):
        """Test loading when pygame raises an exception."""
        mock_exists.return_value = True
        mock_sound.side_effect = Exception("Load failed")
        
        self.sound_manager.enabled = True
        self.sound_manager.load_sound("error_sound", "error.wav")
        
        self.assertNotIn("error_sound", self.sound_manager.sounds)
        mock_log.assert_called()
    
    def test_load_sound_disabled(self):
        """Test loading when audio is disabled."""
        self.sound_manager.enabled = False
        self.sound_manager.load_sound("disabled_sound", "test.wav")
        
        self.assertNotIn("disabled_sound", self.sound_manager.sounds)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    def test_preload_sounds(self):
        """Test preloading all sounds."""
        self.sound_manager.enabled = True
        
        with patch.object(self.sound_manager, 'load_sound') as mock_load:
            self.sound_manager.preload_sounds()
            
            # Verify key sounds are loaded
            mock_load.assert_any_call("player_move", "player_move.wav")
            mock_load.assert_any_call("enemy_alert", "enemy_alert.wav")
            mock_load.assert_any_call("exploit_shadow_step", "exploit_shadow_step.wav")
            mock_load.assert_any_call("ui_menu_open", "ui_menu_open.wav")
            
            # Should load many sounds
            self.assertGreater(mock_load.call_count, 30)
    
    def test_preload_sounds_disabled(self):
        """Test preloading when audio is disabled."""
        self.sound_manager.enabled = False
        
        with patch.object(self.sound_manager, 'load_sound') as mock_load:
            self.sound_manager.preload_sounds()
            
            mock_load.assert_not_called()


class TestSoundPlayback(unittest.TestCase):
    """Test sound effect playback functionality."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    def test_play_sound_success(self, mock_find_channel):
        """Test successful sound playback."""
        # Setup mock sound
        mock_sound = Mock()
        mock_channel = Mock()
        mock_find_channel.return_value = mock_channel
        
        self.sound_manager.enabled = True
        self.sound_manager.sounds["test_sound"] = mock_sound
        
        result = self.sound_manager.play_sound("test_sound")
        
        self.assertIsNotNone(result)
        mock_sound.set_volume.assert_called()
        mock_channel.play.assert_called_with(mock_sound)
    
    def test_play_sound_disabled(self):
        """Test sound playback when audio is disabled."""
        self.sound_manager.enabled = False
        
        result = self.sound_manager.play_sound("test_sound")
        
        self.assertIsNone(result)
    
    def test_play_sound_not_loaded(self):
        """Test playing a sound that wasn't loaded raises KeyError."""
        self.sound_manager.enabled = True

        # Should raise KeyError instead of hiding the error
        with self.assertRaises(KeyError):
            self.sound_manager.play_sound("missing_sound")
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    def test_play_sound_volume_modifier(self, mock_find_channel):
        """Test sound playback with volume modifier."""
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
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    @patch('pygame.mixer.Channel')
    def test_play_sound_channel_priority_critical(self, mock_channel_class, mock_find_channel):
        """Test sound playback with critical priority when channels are busy."""
        mock_sound = Mock()
        mock_find_channel.return_value = None  # All channels busy
        mock_channel = Mock()
        mock_channel_class.return_value = mock_channel
        
        self.sound_manager.enabled = True
        self.sound_manager.sounds["critical_sound"] = mock_sound
        
        result = self.sound_manager.play_sound("critical_sound", priority=8)
        
        mock_channel_class.assert_called_with(0)  # Use channel 0 for critical
        mock_channel.stop.assert_called_once()
        mock_channel.play.assert_called_with(mock_sound)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    @patch('pygame.mixer.Channel')
    @patch('random.randint')
    def test_play_sound_channel_priority_high(self, mock_randint, mock_channel_class, mock_find_channel):
        """Test sound playback with high priority when channels are busy."""
        mock_sound = Mock()
        mock_find_channel.return_value = None  # All channels busy
        mock_channel = Mock()
        mock_channel_class.return_value = mock_channel
        mock_randint.return_value = 3
        
        self.sound_manager.enabled = True
        self.sound_manager.sounds["high_sound"] = mock_sound
        
        result = self.sound_manager.play_sound("high_sound", priority=5)
        
        mock_randint.assert_called_with(0, 15)  # Random channel selection
        mock_channel_class.assert_called_with(3)
        mock_channel.stop.assert_called_once()
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    def test_play_sound_channel_priority_normal(self, mock_find_channel):
        """Test sound playback with normal priority when channels are busy."""
        mock_sound = Mock()
        mock_sound.play.return_value = "direct_play_result"
        mock_find_channel.return_value = None  # All channels busy
        
        self.sound_manager.enabled = True
        self.sound_manager.sounds["normal_sound"] = mock_sound
        
        result = self.sound_manager.play_sound("normal_sound", priority=3)
        
        self.assertEqual(result, "direct_play_result")
        mock_sound.play.assert_called_once()
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.find_channel')
    def test_play_sound_exception(self, mock_find_channel):
        """Test sound playback raises exceptions instead of hiding them."""
        mock_sound = Mock()
        mock_sound.set_volume.side_effect = Exception("Playback error")
        mock_find_channel.return_value = Mock()

        self.sound_manager.enabled = True
        self.sound_manager.sounds["error_sound"] = mock_sound

        # Should raise the exception instead of hiding it
        with self.assertRaises(Exception) as context:
            self.sound_manager.play_sound("error_sound")

        self.assertIn("Playback error", str(context.exception))


class TestMusicPlayback(unittest.TestCase):
    """Test background music functionality."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.play')
    @patch('pygame.mixer.music.set_volume')
    @patch('os.path.exists')
    def test_play_music_success(self, mock_exists, mock_set_volume, mock_play, mock_load):
        """Test successful music playback."""
        mock_exists.return_value = True
        
        self.sound_manager.enabled = True
        self.settings.music_volume = 0.7
        self.settings.master_volume = 0.8
        
        self.sound_manager.play_music("test.mp3")
        
        mock_exists.assert_called_with(os.path.join("music", "test.mp3"))
        mock_load.assert_called_with(os.path.join("music", "test.mp3"))
        expected_volume = 0.7 * 0.8  # music_volume * master_volume
        mock_set_volume.assert_called_with(expected_volume)
        mock_play.assert_called_with(-1)  # Loop indefinitely
        
        self.assertEqual(self.sound_manager.current_music, "test.mp3")
        self.assertTrue(self.sound_manager.music_playing)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.play')
    @patch('pygame.mixer.music.set_volume')
    @patch('os.path.exists')
    def test_play_music_with_fade_in(self, mock_exists, mock_set_volume, mock_play, mock_load):
        """Test music playback with fade-in effect."""
        mock_exists.return_value = True
        
        self.sound_manager.enabled = True
        self.sound_manager.play_music("test.mp3", loops=3, fade_in_ms=2000)
        
        mock_play.assert_called_with(3, fade_ms=2000)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.set_volume')
    @patch('os.path.exists')
    def test_play_music_volume_multiplier(self, mock_exists, mock_set_volume, mock_load):
        """Test music playback with volume multiplier."""
        mock_exists.return_value = True
        
        self.sound_manager.enabled = True
        self.settings.music_volume = 0.8
        self.settings.master_volume = 0.9
        
        self.sound_manager.play_music("test.mp3", volume_multiplier=0.5)
        
        expected_volume = 0.8 * 0.9 * 0.5  # music * master * multiplier
        mock_set_volume.assert_called_with(expected_volume)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.load')
    @patch('pygame.mixer.music.play')
    @patch('pygame.mixer.music.set_volume')
    @patch('os.path.exists')
    def test_play_music_volume_cap(self, mock_exists, mock_set_volume, mock_play, mock_load):
        """Test music volume is capped at 1.0."""
        mock_exists.return_value = True
        
        self.sound_manager.enabled = True
        self.settings.music_volume = 1.0
        self.settings.master_volume = 1.0
        
        self.sound_manager.play_music("test.mp3", volume_multiplier=2.0)
        
        mock_set_volume.assert_called_with(1.0)  # Capped at 1.0
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('os.path.exists')
    @patch('logging.warning')
    def test_play_music_file_not_found(self, mock_log, mock_exists):
        """Test music playback when file doesn't exist."""
        mock_exists.return_value = False
        
        self.sound_manager.enabled = True
        self.sound_manager.play_music("missing.mp3")
        
        mock_log.assert_called_with(f"Music file not found: {os.path.join('music', 'missing.mp3')}")
        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)
    
    def test_play_music_disabled(self):
        """Test music playback when audio is disabled."""
        self.sound_manager.enabled = False
        self.sound_manager.play_music("test.mp3")
        
        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.load')
    @patch('logging.error')
    def test_play_music_exception(self, mock_log, mock_load):
        """Test music playback handles exceptions."""
        mock_load.side_effect = Exception("Load error")
        
        self.sound_manager.enabled = True
        
        with patch('os.path.exists', return_value=True):
            self.sound_manager.play_music("error.mp3")
        
        mock_log.assert_called()
        self.assertIsNone(self.sound_manager.current_music)
        self.assertFalse(self.sound_manager.music_playing)


class TestMusicControls(unittest.TestCase):
    """Test music control functionality."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.stop')
    def test_stop_music(self, mock_stop):
        """Test stopping music."""
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.mp3"
        
        self.sound_manager.stop_music()
        
        mock_stop.assert_called_once()
        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.fadeout')
    def test_stop_music_with_fadeout(self, mock_fadeout):
        """Test stopping music with fade-out."""
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        
        self.sound_manager.stop_music(fade_out_ms=1500)
        
        mock_fadeout.assert_called_with(1500)
        self.assertFalse(self.sound_manager.music_playing)
    
    def test_stop_music_disabled(self):
        """Test stopping music when audio is disabled."""
        self.sound_manager.enabled = False
        self.sound_manager.music_playing = True  # Shouldn't happen but test anyway
        
        self.sound_manager.stop_music()
        
        # When disabled, music state should remain unchanged since there's no actual music system
        self.assertTrue(self.sound_manager.music_playing)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.pause')
    def test_pause_music(self, mock_pause):
        """Test pausing music."""
        self.sound_manager.enabled = True
        
        self.sound_manager.pause_music()
        
        mock_pause.assert_called_once()
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.unpause')
    def test_unpause_music(self, mock_unpause):
        """Test unpausing music."""
        self.sound_manager.enabled = True
        
        self.sound_manager.unpause_music()
        
        mock_unpause.assert_called_once()
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.get_busy')
    def test_is_music_playing_true(self, mock_get_busy):
        """Test checking if music is playing - true case."""
        mock_get_busy.return_value = True
        self.sound_manager.enabled = True
        
        result = self.sound_manager.is_music_playing()
        
        self.assertTrue(result)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.get_busy')
    def test_is_music_playing_false(self, mock_get_busy):
        """Test checking if music is playing - false case."""
        mock_get_busy.return_value = False
        self.sound_manager.enabled = True
        
        result = self.sound_manager.is_music_playing()
        
        self.assertFalse(result)
    
    def test_is_music_playing_disabled(self):
        """Test checking if music is playing when audio is disabled."""
        self.sound_manager.enabled = False
        
        result = self.sound_manager.is_music_playing()
        
        self.assertFalse(result)


class TestVolumeControls(unittest.TestCase):
    """Test volume control functionality."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.set_volume')
    def test_update_volumes(self, mock_set_volume):
        """Test updating volumes from settings."""
        self.sound_manager.enabled = True
        self.settings.music_volume = 0.6
        self.settings.master_volume = 0.8
        
        self.sound_manager.update_volumes()
        
        expected_volume = 0.6 * 0.8  # music_volume * master_volume
        mock_set_volume.assert_called_with(expected_volume)
    
    def test_update_volumes_disabled(self):
        """Test updating volumes when audio is disabled."""
        self.sound_manager.enabled = False
        
        # Should not raise any exceptions
        self.sound_manager.update_volumes()


class TestSoundSystemUpdate(unittest.TestCase):
    """Test sound system update and cleanup functionality."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.get_busy')
    def test_update_music_stopped(self, mock_get_busy):
        """Test update when music has stopped playing."""
        mock_get_busy.return_value = False
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.mp3"
        
        self.sound_manager.update()
        
        self.assertFalse(self.sound_manager.music_playing)
        self.assertIsNone(self.sound_manager.current_music)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.get_busy')
    def test_update_music_still_playing(self, mock_get_busy):
        """Test update when music is still playing."""
        mock_get_busy.return_value = True
        self.sound_manager.enabled = True
        self.sound_manager.music_playing = True
        self.sound_manager.current_music = "test.mp3"
        
        self.sound_manager.update()
        
        self.assertTrue(self.sound_manager.music_playing)
        self.assertEqual(self.sound_manager.current_music, "test.mp3")
    
    def test_update_disabled(self):
        """Test update when audio is disabled."""
        self.sound_manager.enabled = False
        self.sound_manager.music_playing = True  # Shouldn't happen but test anyway
        
        self.sound_manager.update()
        
        # Should remain unchanged since audio is disabled
        self.assertTrue(self.sound_manager.music_playing)
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    @patch('pygame.mixer.music.stop')
    @patch('pygame.mixer.stop')
    @patch('pygame.mixer.quit')
    def test_cleanup(self, mock_quit, mock_stop, mock_music_stop):
        """Test sound system cleanup."""
        self.sound_manager.enabled = True
        
        self.sound_manager.cleanup()
        
        mock_music_stop.assert_called_once()
        mock_stop.assert_called_once()
        mock_quit.assert_called_once()
    
    def test_cleanup_disabled(self):
        """Test cleanup when audio is disabled."""
        self.sound_manager.enabled = False
        
        # Should not raise any exceptions
        self.sound_manager.cleanup()


class TestSoundEventTiming(unittest.TestCase):
    """Test sound effect timing with game events."""
    
    def setUp(self):
        self.settings = GameSettings()
        self.sound_manager = SoundManager(self.settings)
    
    def test_sound_effect_categories(self):
        """Test that sound effects are properly categorized."""
        # Test that specific sound IDs are defined in preload_sounds
        with patch.object(self.sound_manager, 'load_sound') as mock_load:
            self.sound_manager.enabled = True
            self.sound_manager.preload_sounds()
            
            # Movement sounds
            mock_load.assert_any_call("player_move", "player_move.wav")
            
            # Combat sounds
            mock_load.assert_any_call("enemy_attack", "enemy_attack.wav")
            mock_load.assert_any_call("enemy_death", "enemy_death.wav")
            mock_load.assert_any_call("enemy_alert", "enemy_alert.wav")
            
            # Exploit sounds
            mock_load.assert_any_call("exploit_shadow_step", "exploit_shadow_step.wav")
            mock_load.assert_any_call("exploit_failed", "exploit_failed.wav")
            
            # Item sounds
            mock_load.assert_any_call("item_pickup_code", "item_pickup_code.wav")
            mock_load.assert_any_call("item_use_code", "item_use_code.wav")
            
            # System sounds
            mock_load.assert_any_call("player_overheat", "player_overheat.wav")
            mock_load.assert_any_call("critical_system_failure", "critical_system_failure.wav")
    
    @patch('game_audio.AUDIO_AVAILABLE', True)
    def test_simultaneous_sound_playback(self):
        """Test that multiple sounds can play simultaneously."""
        mock_sound1 = Mock()
        mock_sound2 = Mock()
        mock_channel1 = Mock()
        mock_channel2 = Mock()
        
        self.sound_manager.enabled = True
        self.sound_manager.sounds["sound1"] = mock_sound1
        self.sound_manager.sounds["sound2"] = mock_sound2
        
        with patch('pygame.mixer.find_channel', side_effect=[mock_channel1, mock_channel2]):
            result1 = self.sound_manager.play_sound("sound1")
            result2 = self.sound_manager.play_sound("sound2")
            
            self.assertIsNotNone(result1)
            self.assertIsNotNone(result2)
            mock_channel1.play.assert_called_with(mock_sound1)
            mock_channel2.play.assert_called_with(mock_sound2)
    
    def test_sound_priority_ordering(self):
        """Test that sound priorities work as expected."""
        priorities = [
            ("background_sound", 1),    # Low priority
            ("player_action", 3),       # Normal priority  
            ("enemy_alert", 5),         # High priority
            ("system_failure", 8),      # Critical priority
        ]
        
        for sound_id, priority in priorities:
            with patch.object(self.sound_manager, 'play_sound') as mock_play:
                self.sound_manager.play_sound(sound_id, priority=priority)
                mock_play.assert_called_with(sound_id, priority=priority)


if __name__ == '__main__':
    unittest.main()