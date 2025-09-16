"""
Sound manager for handling audio effects and background music.
"""

import logging
import os
from typing import Dict, Optional, TYPE_CHECKING

from ..core.exceptions import AudioError

if TYPE_CHECKING:
    from ..data import GameSettings

# Check for pygame availability
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("pygame not available. Sound will be disabled.")


class AudioConfig:
    """Configuration constants for audio system."""
    SOUND_DIRECTORY = "sound"
    MUSIC_DIRECTORY = "music"
    DEFAULT_FREQUENCY = 22050
    DEFAULT_BUFFER_SIZE = 512
    DEFAULT_CHANNELS = 2
    MAX_SOUND_CHANNELS = 16
    
    # Volume defaults
    DEFAULT_MASTER_VOLUME = 0.7
    DEFAULT_SFX_VOLUME = 0.8
    DEFAULT_MUSIC_VOLUME = 0.6


class SoundManager:
    """
    Manages sound effects and background music using pygame.
    
    Provides centralized audio control with volume management,
    sound caching, and error handling.
    """
    
    def __init__(self, settings: Optional['GameSettings'] = None):
        """
        Initialize the sound manager.
        
        Args:
            settings: Game settings object for audio configuration
        """
        self.settings = settings
        self.enabled = AUDIO_AVAILABLE
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music: Optional[str] = None
        self.music_playing = False
        self.max_channels = AudioConfig.MAX_SOUND_CHANNELS
        
        # Initialize pygame mixer if available
        if self.enabled:
            self._initialize_pygame_mixer()
        
        # Set initial volumes
        self._update_volumes()
    
    def _initialize_pygame_mixer(self) -> None:
        """Initialize pygame mixer with error handling."""
        try:
            pygame.mixer.pre_init(
                frequency=AudioConfig.DEFAULT_FREQUENCY,
                size=-16,
                channels=AudioConfig.DEFAULT_CHANNELS,
                buffer=AudioConfig.DEFAULT_BUFFER_SIZE
            )
            pygame.mixer.init()
            pygame.mixer.set_num_channels(self.max_channels)
            logging.info(f"Sound system initialized with {self.max_channels} channels")
            
        except Exception as e:
            logging.error(f"Failed to initialize sound system: {e}")
            self.enabled = False
            raise AudioError(f"Sound system initialization failed: {e}")
    
    def _update_volumes(self) -> None:
        """Update volumes from settings."""
        if not self.enabled:
            return
            
        try:
            if self.settings:
                master_vol = getattr(self.settings, 'master_volume', AudioConfig.DEFAULT_MASTER_VOLUME)
                music_vol = getattr(self.settings, 'music_volume', AudioConfig.DEFAULT_MUSIC_VOLUME)
                pygame.mixer.music.set_volume(music_vol * master_vol)
            else:
                # Use defaults if no settings provided
                pygame.mixer.music.set_volume(
                    AudioConfig.DEFAULT_MUSIC_VOLUME * AudioConfig.DEFAULT_MASTER_VOLUME
                )
        except Exception as e:
            logging.warning(f"Failed to update audio volumes: {e}")
    
    def load_sound(self, sound_name: str, filename: str = None) -> bool:
        """
        Load a sound effect into memory.
        
        Args:
            sound_name: Key to store the sound under
            filename: Sound file name (defaults to sound_name with .wav extension)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        if filename is None:
            filename = f"{sound_name}.wav"
            
        file_path = os.path.join(AudioConfig.SOUND_DIRECTORY, filename)
        
        try:
            if os.path.exists(file_path):
                sound = pygame.mixer.Sound(file_path)
                self.sounds[sound_name] = sound
                logging.debug(f"Loaded sound: {sound_name}")
                return True
            else:
                logging.warning(f"Sound file not found: {file_path}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to load sound {sound_name}: {e}")
            return False
    
    def play_sound(self, sound_name: str, volume: float = 1.0) -> bool:
        """
        Play a sound effect.
        
        Args:
            sound_name: Name of the sound to play
            volume: Volume multiplier (0.0 to 1.0)
            
        Returns:
            True if played successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Load sound if not already loaded
            if sound_name not in self.sounds:
                if not self.load_sound(sound_name):
                    return False
            
            sound = self.sounds[sound_name]
            
            # Apply volume settings
            if self.settings:
                master_vol = getattr(self.settings, 'master_volume', AudioConfig.DEFAULT_MASTER_VOLUME)
                sfx_vol = getattr(self.settings, 'sfx_volume', AudioConfig.DEFAULT_SFX_VOLUME)
                final_volume = volume * sfx_vol * master_vol
            else:
                final_volume = volume * AudioConfig.DEFAULT_SFX_VOLUME * AudioConfig.DEFAULT_MASTER_VOLUME
            
            sound.set_volume(max(0.0, min(1.0, final_volume)))
            sound.play()
            return True
            
        except Exception as e:
            logging.error(f"Failed to play sound {sound_name}: {e}")
            return False
    
    def load_music(self, music_name: str, filename: str = None) -> bool:
        """
        Load background music.
        
        Args:
            music_name: Key to identify the music
            filename: Music file name (defaults to music_name with .ogg extension)
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        if filename is None:
            filename = f"{music_name}.ogg"
            
        file_path = os.path.join(AudioConfig.MUSIC_DIRECTORY, filename)
        
        try:
            if os.path.exists(file_path):
                pygame.mixer.music.load(file_path)
                self.current_music = music_name
                logging.debug(f"Loaded music: {music_name}")
                return True
            else:
                logging.warning(f"Music file not found: {file_path}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to load music {music_name}: {e}")
            return False
    
    def play_music(self, music_name: str = None, loops: int = -1, filename: str = None) -> bool:
        """
        Play background music.
        
        Args:
            music_name: Name of music to play (None to play currently loaded)
            loops: Number of loops (-1 for infinite)
            filename: Music file name override
            
        Returns:
            True if started successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        try:
            # Load music if specified and different from current
            if music_name and music_name != self.current_music:
                if not self.load_music(music_name, filename):
                    return False
            
            pygame.mixer.music.play(loops)
            self.music_playing = True
            self._update_volumes()
            logging.debug(f"Started playing music: {self.current_music}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to play music: {e}")
            return False
    
    def stop_music(self) -> None:
        """Stop background music."""
        if self.enabled:
            try:
                pygame.mixer.music.stop()
                self.music_playing = False
                logging.debug("Stopped music")
            except Exception as e:
                logging.error(f"Failed to stop music: {e}")
    
    def pause_music(self) -> None:
        """Pause background music."""
        if self.enabled and self.music_playing:
            try:
                pygame.mixer.music.pause()
                logging.debug("Paused music")
            except Exception as e:
                logging.error(f"Failed to pause music: {e}")
    
    def unpause_music(self) -> None:
        """Unpause background music."""
        if self.enabled:
            try:
                pygame.mixer.music.unpause()
                logging.debug("Unpaused music")
            except Exception as e:
                logging.error(f"Failed to unpause music: {e}")
    
    def is_music_playing(self) -> bool:
        """Check if music is currently playing."""
        if not self.enabled:
            return False
            
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False
    
    def stop_all_sounds(self) -> None:
        """Stop all currently playing sound effects."""
        if self.enabled:
            try:
                pygame.mixer.stop()
                logging.debug("Stopped all sound effects")
            except Exception as e:
                logging.error(f"Failed to stop sound effects: {e}")
    
    def set_master_volume(self, volume: float) -> None:
        """
        Set master volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.settings:
            self.settings.master_volume = max(0.0, min(1.0, volume))
            self._update_volumes()
    
    def set_music_volume(self, volume: float) -> None:
        """
        Set music volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.settings:
            self.settings.music_volume = max(0.0, min(1.0, volume))
            self._update_volumes()
    
    def set_sfx_volume(self, volume: float) -> None:
        """
        Set sound effects volume level.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        if self.settings:
            self.settings.sfx_volume = max(0.0, min(1.0, volume))
    
    def update(self) -> None:
        """Update the sound manager (call each frame)."""
        if not self.enabled:
            return
            
        try:
            # Update music playing status
            if self.music_playing and not self.is_music_playing():
                self.music_playing = False
                
        except Exception as e:
            logging.warning(f"Sound manager update error: {e}")
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        if self.enabled:
            try:
                self.stop_music()
                self.stop_all_sounds()
                pygame.mixer.quit()
                logging.info("Audio system cleaned up")
            except Exception as e:
                logging.error(f"Audio cleanup error: {e}")
    
    def get_available_sounds(self) -> list[str]:
        """Get list of available sound files."""
        sounds = []
        if os.path.exists(AudioConfig.SOUND_DIRECTORY):
            for filename in os.listdir(AudioConfig.SOUND_DIRECTORY):
                if filename.endswith(('.wav', '.ogg', '.mp3')):
                    sounds.append(os.path.splitext(filename)[0])
        return sounds
    
    def get_available_music(self) -> list[str]:
        """Get list of available music files."""
        music = []
        if os.path.exists(AudioConfig.MUSIC_DIRECTORY):
            for filename in os.listdir(AudioConfig.MUSIC_DIRECTORY):
                if filename.endswith(('.ogg', '.mp3', '.wav')):
                    music.append(os.path.splitext(filename)[0])
        return music
    
    def preload_common_sounds(self) -> None:
        """Preload commonly used sound effects."""
        common_sounds = [
            'exploit_use', 'enemy_alert', 'player_move', 'item_pickup',
            'enemy_disabled', 'heat_warning', 'level_complete'
        ]
        
        for sound_name in common_sounds:
            self.load_sound(sound_name)
    
    def __str__(self) -> str:
        """String representation for debugging."""
        status = "enabled" if self.enabled else "disabled"
        return f"SoundManager({status}, {len(self.sounds)} sounds loaded)"