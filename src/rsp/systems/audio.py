#!/usr/bin/env python3
"""
Audio system managing sound effects and background music via miniaudio.

This module handles:
- Sound effect playback with priority queue (16 simultaneous voices)
- Sound deduplication to prevent stacking/doubling (50ms cooldown)
- Background music streaming with fade in/out
- Volume management (master, music, SFX) synced with GameSettings
- Sound preloading at startup for instant playback
- Graceful fallback when miniaudio unavailable

Backend notes:
- miniaudio is self-contained (bundled decoders for WAV/OGG/FLAC/MP3) and builds from
  source with no external native dependencies, which is what Flathub requires.
- A single miniaudio PlaybackDevice is opened at 22050 Hz, 16-bit, stereo. All active
  sounds plus music are mixed together in software (numpy) inside the device callback.
- Decoding is done up front with miniaudio.decode_file, producing interleaved int16
  samples that are reshaped to (frames, 2) numpy arrays and summed at playback time.
"""

import logging
import os
import random
import threading
import time

import numpy as np

from rsp.core.errors import GameErrorHandler

# Audio system
try:
    import miniaudio

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("miniaudio not available. Sound will be disabled.")

# Import game settings
from rsp.core.config import GameConfig, GameSettings

# Audio system constants
AUDIO_MAX_CHANNELS = 16  # Simultaneous sound effect voices
AUDIO_FREQUENCY = 22050  # Sample rate in Hz
AUDIO_CHANNELS = 2  # Stereo output
AUDIO_BUFFER_MSEC = 50  # Device buffer size in milliseconds (low latency for SFX)
AUDIO_SOUND_COOLDOWN = 0.05  # 50ms cooldown to prevent sound stacking


class _Voice:
    """A single playing sound effect: a decoded buffer with a playhead and gain."""

    __slots__ = ("samples", "pos", "gain")

    def __init__(self, samples: np.ndarray, gain: float):
        self.samples = samples  # (frames, 2) int16
        self.pos = 0
        self.gain = gain


class _MusicVoice:
    """Background music: a decoded buffer with looping and linear fade support."""

    __slots__ = ("samples", "pos", "gain", "loops_left", "fade_from", "fade_to", "fade_total", "fade_done", "stopping")

    def __init__(self, samples: np.ndarray, gain: float, loops: int):
        self.samples = samples  # (frames, 2) int16
        self.pos = 0
        self.gain = gain
        # loops: -1 = infinite, 0 = play once, N = play N+1 times
        self.loops_left = loops
        # Linear fade state (in frames). When fade_total == 0 there is no fade.
        self.fade_from = gain
        self.fade_to = gain
        self.fade_total = 0
        self.fade_done = 0
        self.stopping = False  # True once a fade-out completes -> remove

    def start_fade(self, from_gain: float, to_gain: float, fade_ms: int):
        self.fade_from = from_gain
        self.fade_to = to_gain
        self.fade_total = int(fade_ms / 1000.0 * AUDIO_FREQUENCY)
        self.fade_done = 0

    def current_gain(self, block_frames: int) -> float:
        """Gain for the next block; advances the fade by block_frames."""
        if self.fade_total <= 0:
            return self.gain
        t = min(1.0, self.fade_done / self.fade_total)
        g = self.fade_from + (self.fade_to - self.fade_from) * t
        self.fade_done += block_frames
        if self.fade_done >= self.fade_total:
            self.fade_total = 0
            self.gain = self.fade_to
        return g


class SoundManager:
    """
    Audio manager for sound effects and background music using miniaudio.

    Responsibilities:
    - Preload sound effects at startup (instant playback)
    - Play sounds with priority queue (interrupts lower priority)
    - Stream background music with fade in/out
    - Volume management synced with GameSettings
    - Graceful degradation when miniaudio unavailable

    The public interface matches the previous pygame-backed implementation so the rest
    of the game does not change: preload_sounds, load_sound, play_sound, play_music,
    stop_music, is_music_playing, update, update_volumes, set_sound_cooldown, cleanup.

    Attributes:
        settings: GameSettings instance for volume preferences
        enabled: Whether the audio device is available
        sounds: Dict mapping sound keys to decoded (frames, 2) int16 numpy arrays
        current_music: Currently playing music filename
        music_playing: Whether music is currently playing
        max_channels: Number of simultaneous sound voices (16)
    """

    # Class-level registry mirroring pygame's single global music stream: only one
    # SoundManager plays music at a time. The menu and in-game engine each own a separate
    # SoundManager/device, so this lets them see one another's music (e.g. don't restart
    # menu music while level music is still playing).
    _music_owner = None

    # Centralized audio directory configuration
    @property
    def SOUND_DIRECTORY(self):
        return GameConfig._get_required("audio.sound_directory")

    @property
    def MUSIC_DIRECTORY(self):
        return GameConfig._get_required("audio.music_directory")

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
        self.max_channels = AUDIO_MAX_CHANNELS
        self._sound_last_played = {}  # Track last play time for each sound
        self._sound_cooldown = AUDIO_SOUND_COOLDOWN
        self._music_cache = {}  # filename -> decoded (frames, 2) int16

        # Mixer state shared with the audio callback thread (guarded by _lock).
        self._lock = threading.Lock()
        self._voices = []  # list[_Voice]
        self._music = None  # _MusicVoice or None
        self._device = None

        if self.enabled:
            try:
                self._device = miniaudio.PlaybackDevice(
                    output_format=miniaudio.SampleFormat.SIGNED16,
                    nchannels=AUDIO_CHANNELS,
                    sample_rate=AUDIO_FREQUENCY,
                    buffersize_msec=AUDIO_BUFFER_MSEC,
                )
                generator = self._mix_stream()
                next(generator)  # prime the generator
                self._device.start(generator)
                logging.debug(
                    f"Audio: Initialized miniaudio device - {self.max_channels} voices, "
                    f"{AUDIO_FREQUENCY}Hz stereo"
                )
            except Exception as e:
                GameErrorHandler.handle_error(e, "sound_init", "Sound initialization failed")
                self.enabled = False
                self._device = None

    # ------------------------------------------------------------------ mixing

    def _mix_stream(self):
        """miniaudio playback generator: yields (frames, 2) int16 blocks.

        Runs on miniaudio's audio thread. Receives the required frame count from the
        yield and mixes all active voices plus music into a single block.
        """
        frames = yield np.zeros((0, AUDIO_CHANNELS), dtype=np.int16)
        while True:
            block = self._render(int(frames))
            frames = yield block

    def _render(self, frames: int) -> np.ndarray:
        if frames <= 0:
            return np.zeros((0, AUDIO_CHANNELS), dtype=np.int16)

        acc = np.zeros((frames, AUDIO_CHANNELS), dtype=np.float32)

        with self._lock:
            # Sound effects
            still_active = []
            for v in self._voices:
                end = v.pos + frames
                chunk = v.samples[v.pos:end]
                n = chunk.shape[0]
                if n > 0:
                    acc[:n] += chunk.astype(np.float32) * v.gain
                v.pos = end
                if v.pos < v.samples.shape[0]:
                    still_active.append(v)
            self._voices = still_active

            # Music (with looping + fade)
            m = self._music
            if m is not None:
                g = m.current_gain(frames)
                written = 0
                while written < frames:
                    end = m.pos + (frames - written)
                    chunk = m.samples[m.pos:end]
                    n = chunk.shape[0]
                    if n > 0:
                        acc[written:written + n] += chunk.astype(np.float32) * g
                    m.pos += n
                    written += n
                    if m.pos >= m.samples.shape[0]:
                        # Reached end of track
                        if m.loops_left == -1:
                            m.pos = 0  # infinite loop
                        elif m.loops_left > 0:
                            m.loops_left -= 1
                            m.pos = 0
                        else:
                            break  # finished
                # Drop music if it finished playing or a fade-out completed
                finished = m.pos >= m.samples.shape[0] and m.loops_left == 0
                if (m.stopping and m.fade_total == 0) or finished:
                    self._music = None
                    self.music_playing = False
                    self.current_music = None

        np.clip(acc, -32768.0, 32767.0, out=acc)
        return acc.astype(np.int16)

    # ------------------------------------------------------------------ volume

    def _get_effective_music_volume(self) -> float:
        """Calculate effective music volume including optional boost.

        Music boost compensates for audio backend differences where music
        can sound quieter relative to SFX (common on Linux).

        Returns:
            Music volume (0.0-1.0) after applying master volume and boost
        """
        base_vol = self.settings.music_volume * self.settings.master_volume
        if self.settings.get_effective_music_boost():
            return min(1.0, base_vol * 1.5)
        return base_vol

    def update_volumes(self):
        """Update volumes from settings (includes Linux music boost)."""
        if not self.enabled:
            return
        new_vol = self._get_effective_music_volume()
        with self._lock:
            if self._music is not None and self._music.fade_total == 0:
                self._music.gain = new_vol
                self._music.fade_to = new_vol
        logging.debug(f"Audio: Updated music volume to {new_vol:.2f}")

    def set_sound_cooldown(self, cooldown_seconds: float):
        """
        Set the cooldown time for sound deduplication.

        Args:
            cooldown_seconds: Time in seconds before same sound can play again.
                            Default is 0.05 (50ms). Set to 0 to disable deduplication.
        """
        self._sound_cooldown = max(0.0, cooldown_seconds)
        logging.debug(f"Audio: Sound cooldown set to {self._sound_cooldown*1000:.1f}ms")

    # ------------------------------------------------------------------ loading

    def preload_sounds(self):
        """
        Preload all sound effects at startup for instant playback.

        Loads all game sound effects into memory to avoid disk I/O during
        gameplay. Missing sound files are logged as warnings but don't
        crash the game (graceful degradation).
        """
        if not self.enabled:
            return

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
            "exploit_system_hop": "exploit_system_hop.wav",
            "exploit_buffer_overflow": "exploit_buffer_overflow.wav",
            "exploit_code_injection": "exploit_code_injection.wav",
            "exploit_system_crash": "exploit_system_crash.wav",
            "exploit_threat_scan": "exploit_threat_scan.wav",
            "exploit_log_wiper": "exploit_log_wiper.wav",
            "exploit_antivirus": "exploit_antivirus.wav",
            "exploit_denial_of_service": "exploit_denial_of_service.wav",
            "exploit_logic_bomb": "logic_bomb.wav",
            "exploit_memory_leak": "exploit_memory_leak.wav",
            "exploit_network_scan": "exploit_network_scan.wav",
            "exploit_failed": "exploit_failed.wav",
            "exploit_traffic_masquerade": "exploit_traffic_masquerade.wav",
            "exploit_decoy_swarm": "exploit_decoy_swarm.wav",
            "exploit_targeting": "exploit_targeting.wav",
            # UI and system
            "ui_menu_open": "ui_menu_open.wav",
            "level_complete": "level_complete.wav",
        }

        logging.debug(f"Audio: Preloading {len(sound_files)} sound effects")
        loaded_count = 0
        for sound_id, filename in sound_files.items():
            if self.load_sound(sound_id, filename):
                loaded_count += 1
        logging.debug(f"Audio: Preloaded {loaded_count}/{len(sound_files)} sounds successfully")

    def _decode(self, path: str) -> np.ndarray:
        """Decode an audio file to a (frames, 2) int16 numpy array at the device rate."""
        decoded = miniaudio.decode_file(
            path,
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=AUDIO_CHANNELS,
            sample_rate=AUDIO_FREQUENCY,
        )
        return np.asarray(decoded.samples, dtype=np.int16).reshape(-1, AUDIO_CHANNELS)

    def load_sound(self, sound_id: str, filename: str) -> bool:
        """Load and decode a sound effect from file."""
        if not self.enabled:
            return False

        try:
            sound_path = os.path.join(self.SOUND_DIRECTORY, filename)
            if not os.path.exists(sound_path):
                logging.error(f"MISSING AUDIO FILE: Sound file not found: {sound_path}")
                return False

            self.sounds[sound_id] = self._decode(sound_path)
            file_size = os.path.getsize(sound_path)
            logging.debug(f"Audio: Loaded sound '{sound_id}' from {filename} ({file_size} bytes)")
            return True
        except Exception as e:
            GameErrorHandler.handle_error(e, "sound_load", f"Failed to load {sound_id}")
            return False

    # ------------------------------------------------------------------ playback

    def play_sound(self, sound_id: str, volume_modifier: float = 1.0, priority: int = 0):
        """
        Play a loaded sound effect with voice management and deduplication.

        Prevents the same sound from playing multiple times within a short time window
        (50ms by default) to avoid stacking/doubling.

        Args:
            sound_id: ID of the sound to play
            volume_modifier: Volume multiplier (0.0-1.0+)
            priority: Priority level (0-10, higher interrupts lower when voices are full)
        """
        if not self.enabled:
            return None

        # Check cooldown to prevent stacking
        current_time = time.time()
        last_played = self._sound_last_played.get(sound_id, 0)
        time_since_last = current_time - last_played
        if time_since_last < self._sound_cooldown:
            logging.debug(
                f"Audio: Skipped '{sound_id}' (cooldown: {time_since_last*1000:.1f}ms "
                f"< {self._sound_cooldown*1000:.1f}ms)"
            )
            return None

        samples = self.sounds[sound_id]  # Let it fail if sound doesn't exist

        # Update last played time AFTER validating sound exists
        self._sound_last_played[sound_id] = current_time

        final_volume = self.settings.sfx_volume * self.settings.master_volume * volume_modifier
        voice = _Voice(samples, final_volume)

        with self._lock:
            if len(self._voices) >= self.max_channels:
                # Voices full: high priority steals a slot, otherwise drop the oldest.
                if priority >= 8:
                    self._voices.pop(0)
                elif priority >= 5:
                    self._voices.pop(random.randint(0, len(self._voices) - 1))
                else:
                    self._voices.pop(0)
            self._voices.append(voice)
        return voice

    def play_music(self, filename: str, loops: int = -1, fade_in_ms: int = 0):
        """Play background music (OGG or WAV)."""
        if not self.enabled:
            return

        music_path = os.path.join(self.MUSIC_DIRECTORY, filename)
        if not os.path.exists(music_path):
            logging.error(f"MISSING AUDIO FILE: Music file not found: {music_path}")
            return

        try:
            samples = self._music_cache.get(filename)
            if samples is None:
                samples = self._decode(music_path)
                self._music_cache[filename] = samples

            volume = self._get_effective_music_volume()
            voice = _MusicVoice(samples, volume, loops)
            if fade_in_ms > 0:
                voice.start_fade(0.0, volume, fade_in_ms)

            # Single global music stream: stop any other manager's music first.
            prev = SoundManager._music_owner
            if prev is not None and prev is not self:
                prev.stop_music()

            with self._lock:
                self._music = voice
            self.current_music = filename
            self.music_playing = True
            SoundManager._music_owner = self

            loop_info = "loop" if loops == -1 else f"{loops} times"
            logging.debug(
                f"Audio: Playing music '{filename}' ({loop_info}, volume={volume:.2f}, "
                f"fade_in={fade_in_ms}ms)"
            )
        except Exception as e:
            GameErrorHandler.handle_error(e, "music_play", f"Failed to play {filename}")
            self.current_music = None
            self.music_playing = False

    def stop_music(self, fade_out_ms: int = 0):
        """Stop background music, optionally fading out."""
        if not self.enabled:
            return

        try:
            logging.debug(f"Audio: Stopping music (fade_out={fade_out_ms}ms)")
            with self._lock:
                m = self._music
                if m is None:
                    pass
                elif fade_out_ms > 0:
                    m.start_fade(m.current_gain(0), 0.0, fade_out_ms)
                    m.stopping = True
                else:
                    self._music = None
            if fade_out_ms <= 0:
                self.music_playing = False
                self.current_music = None
                if SoundManager._music_owner is self:
                    SoundManager._music_owner = None
        except Exception as e:
            GameErrorHandler.handle_error(e, "music_stop", "Failed to stop music")

    def is_music_playing(self) -> bool:
        """Check if any music is currently playing (single global music stream)."""
        owner = SoundManager._music_owner
        if owner is None or not owner.enabled:
            return False
        with owner._lock:
            return owner._music is not None

    def update(self):
        """Update sound system (call each frame). Music end is detected in the mixer."""
        if not self.enabled:
            return
        with self._lock:
            if self.music_playing and self._music is None:
                self.music_playing = False
                self.current_music = None
                if SoundManager._music_owner is self:
                    SoundManager._music_owner = None

    def cleanup(self):
        """Clean up sound system."""
        if not self.enabled:
            return
        try:
            with self._lock:
                self._voices = []
                self._music = None
            if SoundManager._music_owner is self:
                SoundManager._music_owner = None
            if self._device is not None:
                self._device.close()
                self._device = None
        except Exception as e:
            logging.debug(f"Audio cleanup error (non-fatal): {e}")


class NullSoundManager:
    """
    Null object pattern for SoundManager - does nothing but implements same interface.

    Used in headless mode for testing to avoid needing an audio device.
    All methods are no-ops but maintain the same signature as SoundManager.
    """

    def __init__(self, settings=None):
        """Initialize null sound manager (does nothing)."""
        self.settings = settings
        self.enabled = False
        self.sounds = {}
        self.current_music = None
        self.music_playing = False
        self.max_channels = 0

    @property
    def SOUND_DIRECTORY(self):
        return "sound/"

    @property
    def MUSIC_DIRECTORY(self):
        return "music/"

    def update_volumes(self):
        """No-op: Update volumes."""
        pass

    def set_sound_cooldown(self, cooldown_seconds: float):
        """No-op: Set sound cooldown."""
        pass

    def preload_sounds(self):
        """No-op: Preload sounds."""
        pass

    def load_sound(self, sound_id: str, filename: str) -> bool:
        """No-op: Load sound."""
        return False

    def play_sound(self, sound_id: str, volume_modifier: float = 1.0, priority: int = 0):
        """No-op: Play sound."""
        pass

    def play_music(self, filename: str, loops: int = -1, fade_in_ms: int = 0):
        """No-op: Play music."""
        pass

    def stop_music(self, fade_out_ms: int = 0):
        """No-op: Stop music."""
        pass

    def is_music_playing(self) -> bool:
        """No-op: Check if music playing."""
        return False

    def update(self):
        """No-op: Update sound system."""
        pass

    def cleanup(self):
        """No-op: Clean up sound system."""
        pass
