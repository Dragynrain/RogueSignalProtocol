#!/usr/bin/env python3
"""
Audio system managing sound effects and background music via pygame.

This module handles:
- Sound effect playback with priority queue (16 simultaneous channels)
- Background music streaming with fade in/out
- Volume management (master, music, SFX) synced with GameSettings
- Sound preloading at startup for instant playback
- Graceful fallback when pygame unavailable

Key features:
- Priority-based sound playback (higher priority interrupts lower)
- Configurable audio directories (sound/, music/)
- Master volume slider affects all audio (music and SFX)
- Music loops infinitely or plays once based on loops parameter
- Safe initialization with fallback to silent mode if pygame missing

Technical details:
- Uses pygame.mixer with 22050 Hz, 16-bit, stereo, 512 buffer
- 16 channels for simultaneous sound effects
- Music volume set from settings immediately after init (pygame defaults to 0.0)
"""

import os
import logging
import traceback

# Audio system
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("pygame not available. Sound will be disabled.")

# Import game settings
from game_config import GameSettings


class SoundManager:
    """
    Audio manager for sound effects and background music using pygame.mixer.

    Responsibilities:
    - Preload sound effects at startup (instant playback)
    - Play sounds with priority queue (interrupts lower priority)
    - Stream background music with fade in/out
    - Volume management synced with GameSettings
    - Graceful degradation when pygame unavailable

    Key systems:
    - 16 simultaneous sound channels for layered effects
    - Priority-based playback (e.g., player death has priority 10)
    - Configurable audio directories (defaults: sound/, music/)
    - Volume hierarchy: master volume * (music/sfx volume)

    Attributes:
        settings: GameSettings instance for volume preferences
        enabled: Whether pygame audio is available
        sounds: Dict mapping sound keys to pygame.mixer.Sound objects
        current_music: Currently playing music filename
        music_playing: Whether music is currently playing
        max_channels: Number of simultaneous sound channels (16)
    """

    # Centralized audio directory configuration
    @property
    def SOUND_DIRECTORY(self):
        return GameConfig.get('audio.sound_directory', 'sound') if hasattr(self, '_game_config_loaded') else 'sound'

    @property
    def MUSIC_DIRECTORY(self):
        return GameConfig.get('audio.music_directory', 'music') if hasattr(self, '_game_config_loaded') else 'music'
    
    def __init__(self, settings: GameSettings = None):
        """Initialize the sound manager with game settings.
        
        Args:
            settings: Game settings containing audio preferences. Creates default if None.
        """
        self.settings = settings or GameSettings()
        self.enabled = AUDIO_AVAILABLE
        self.sounds = {}
        self.current_music = None
        self.music_playing = False
        self.max_channels = 16  # Allow more simultaneous sound effects
        
        if self.enabled:
            try:
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(self.max_channels)

                # CRITICAL: Set initial volume from settings immediately after init
                # pygame.mixer starts at volume 0.0 by default
                music_vol = self.settings.music_volume * self.settings.master_volume
                pygame.mixer.music.set_volume(music_vol)
                logging.debug(f"Audio: Initialized pygame.mixer - {self.max_channels} channels, music_vol={music_vol:.2f}")
            except Exception as e:
                logging.warning(f"Failed to initialize sound system: {e}")
                logging.debug(traceback.format_exc())
                self.enabled = False
    
    def update_volumes(self):
        """Update volumes from settings"""
        if self.enabled:
            new_vol = self.settings.music_volume * self.settings.master_volume
            pygame.mixer.music.set_volume(new_vol)
            logging.debug(f"Audio: Updated music volume to {new_vol:.2f}")
    
    def preload_sounds(self):
        """
        Preload all sound effects at startup for instant playback.

        Loads all game sound effects into memory to avoid disk I/O during
        gameplay. Missing sound files are logged as warnings but don't
        crash the game (graceful degradation).

        Organized categories:
        - Movement and actions (player_move, player_attack, stealth_attack)
        - Combat and alerts (enemy_attack, enemy_alert, admin_spawn)
        - Item interactions (item_pickup_*, item_use_*)
        - Environmental (node_activate)
        - Player status (player_death, virus_damage, overheat)
        - Exploits (exploit_* for each ability)
        """
        if not self.enabled:
            return
            
        # Define all sound effects that should be loaded
        sound_files = {
            # Movement and actions
            "player_move": "player_move.wav",
            "player_attack": "player_attack.wav",
            "stealth_attack": "stealth_attack.wav",
            
            # Combat and alerts
            "enemy_attack": "enemy_attack.wav",
            "enemy_death": "enemy_death.wav",
            "enemy_alert": "enemy_alert.wav",
            "enemy_hostile": "enemy_hostile.wav",
            "admin_spawn": "admin_spawn.wav",
            "enemies_alerted": "enemies_alerted.wav",
            
            # Item interactions
            "item_pickup_code": "item_pickup_code.wav",
            "item_pickup_exploit": "item_pickup_exploit.wav",
            "item_pickup_upgrade": "item_pickup_upgrade.wav",
            "item_pickup_story": "item_pickup_story.wav",
            "item_use_code": "item_use_code.wav",
            
            # Environmental
            "node_activate": "node_activate.wav",
            
            # Player status
            "player_death": "player_death.wav",
            "player_overheat": "player_overheat.wav",
            "virus_damage": "virus_damage.wav",
            "virus_infection": "virus_infection.wav",
            "critical_system_failure": "critical_system_failure.wav",
            "trace_threshold": "trace_threshold.wav",
            "overclocking": "overclocking.wav",
            
            # Exploits
            "exploit_shadow_step": "exploit_shadow_step.wav",
            "exploit_buffer_overflow": "exploit_buffer_overflow.wav",
            "exploit_code_injection": "exploit_code_injection.wav",
            "exploit_system_crash": "exploit_system_crash.wav",
            "exploit_threat_scan": "exploit_threat_scan.wav",
            "exploit_log_wiper": "exploit_log_wiper.wav",
            "exploit_antivirus": "exploit_antivirus.wav",
            "exploit_denial_of_service": "exploit_denial_of_service.wav",
            "exploit_memory_leak": "exploit_memory_leak.wav",
            "exploit_network_scan": "exploit_network_scan.wav",
            "exploit_failed": "exploit_failed.wav",
            "exploit_data_mimic": "exploit_data_mimic.wav",
            "exploit_noise_maker": "exploit_noise_maker.wav",
            "exploit_targeting": "exploit_targeting.wav",
            
            # UI and system
            "ui_menu_open": "ui_menu_open.wav",
            "level_complete": "level_complete.wav",
        }
        
        # Load each sound file
        logging.debug(f"Audio: Preloading {len(sound_files)} sound effects")
        loaded_count = 0
        for sound_id, filename in sound_files.items():
            if self.load_sound(sound_id, filename):
                loaded_count += 1
        logging.debug(f"Audio: Preloaded {loaded_count}/{len(sound_files)} sounds successfully")
    
    def load_sound(self, sound_id: str, filename: str) -> bool:
        """Load a sound effect from file"""
        if not self.enabled:
            return False

        try:
            sound_path = os.path.join(self.SOUND_DIRECTORY, filename)
            if not os.path.exists(sound_path):
                logging.warning(f"Sound file not found: {sound_path}")
                return False

            self.sounds[sound_id] = pygame.mixer.Sound(sound_path)
            file_size = os.path.getsize(sound_path)
            logging.debug(f"Audio: Loaded sound '{sound_id}' from {filename} ({file_size} bytes)")
            return True
        except Exception as e:
            logging.error(f"Failed to load sound {sound_id}: {e}")
            logging.debug(traceback.format_exc())
            return False
    
    def play_sound(self, sound_id: str, volume_modifier: float = 1.0, priority: int = 0):
        """Play a loaded sound effect with channel management"""
        if not self.enabled:
            return None

        sound = self.sounds[sound_id]  # Let it fail if sound doesn't exist
        final_volume = self.settings.sfx_volume * self.settings.master_volume * volume_modifier
        sound.set_volume(final_volume)

        logging.debug(f"Audio: Playing sound '{sound_id}' (volume={final_volume:.2f}, priority={priority})")

        # Find available channel for simultaneous playback
        channel = pygame.mixer.find_channel()

        if channel is None:
            # All channels busy - handle based on priority
            if priority >= 8:
                # Critical priority: stop oldest channel (channel 0)
                channel = pygame.mixer.Channel(0)
                channel.stop()
            elif priority >= 5:
                # High priority: stop a random channel
                import random
                channel_id = random.randint(0, self.max_channels - 1)
                channel = pygame.mixer.Channel(channel_id)
                channel.stop()
            else:
                # Normal/Low priority: just play on any channel, let pygame handle mixing
                return sound.play()

        return channel.play(sound)
    
    def play_music(self, filename: str, loops: int = -1, fade_in_ms: int = 0):
        """Play background music (OGG format recommended)"""
        if not self.enabled:
            return

        music_path = os.path.join(self.MUSIC_DIRECTORY, filename)

        # Check if file exists first
        if not os.path.exists(music_path):
            logging.warning(f"Music file not found: {music_path}")
            return

        try:
            pygame.mixer.music.load(music_path)

            # Apply volume from settings (OGG files should be pre-normalized)
            volume = self.settings.music_volume * self.settings.master_volume
            pygame.mixer.music.set_volume(min(1.0, volume))  # Cap at 1.0

            if fade_in_ms > 0:
                pygame.mixer.music.play(loops, fade_ms=fade_in_ms)
            else:
                pygame.mixer.music.play(loops)

            self.current_music = filename
            self.music_playing = True
            loop_info = "loop" if loops == -1 else f"{loops} times"
            logging.debug(f"Audio: Playing music '{filename}' ({loop_info}, volume={volume:.2f}, fade_in={fade_in_ms}ms)")
        except Exception as e:
            logging.error(f"Failed to play music {filename}: {e}")
            self.current_music = None
            self.music_playing = False
    
    def stop_music(self, fade_out_ms: int = 0):
        """Stop background music"""
        if not self.enabled:
            return

        try:
            logging.debug(f"Audio: Stopping music (fade_out={fade_out_ms}ms)")
            if fade_out_ms > 0:
                pygame.mixer.music.fadeout(fade_out_ms)
            else:
                pygame.mixer.music.stop()
            self.music_playing = False
            self.current_music = None
        except Exception as e:
            logging.error(f"Failed to stop music: {e}")
            logging.debug(traceback.format_exc())
    
    def pause_music(self):
        """Pause background music"""
        if self.enabled:
            pygame.mixer.music.pause()
    
    def unpause_music(self):
        """Resume paused background music"""
        if self.enabled:
            pygame.mixer.music.unpause()
    
    def is_music_playing(self) -> bool:
        """Check if music is currently playing"""
        if not self.enabled:
            return False
        return pygame.mixer.music.get_busy()
    
    def update(self):
        """Update sound system (call each frame)"""
        if self.enabled and self.music_playing and not pygame.mixer.music.get_busy():
            # Music stopped playing
            self.music_playing = False
            self.current_music = None
    
    def cleanup(self):
        """Clean up sound system"""
        if self.enabled:
            pygame.mixer.music.stop()
            pygame.mixer.stop()
            pygame.mixer.quit()