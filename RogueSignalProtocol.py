#!/usr/bin/env python3
"""
Rogue Signal Protocol - Enhanced Edition
A stealth-focused traditional roguelike using Python and tcod

Features cyberpunk-themed infiltration gameplay with permadeath,
procedural level generation, and persistent story progression.
"""

import tcod
import logging
import random
import math
import json
import os
# ABC removed - simplified inheritance pattern
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Any, Set
import time

# Audio imports
try:
    import pygame
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("pygame not available. Sound will be disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# ============================================================================
# JSON DATA LOADING SYSTEM
# ============================================================================

class DataLoader:
    """Handles loading of JSON configuration and game data files."""
    
    _story_fragments = None
    _game_data = None
    _config = None
    
    @classmethod
    def load_story_fragments(cls) -> List[str]:
        """Load story fragments from JSON file."""
        if cls._story_fragments is None:
            try:
                with open('story_fragments.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cls._story_fragments = data['fragments']
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Could not load story fragments from JSON: {e}")
                cls._story_fragments = cls._get_fallback_story_fragments()
        return cls._story_fragments
    
    @classmethod
    def load_game_data(cls) -> Dict[str, Any]:
        """Load game data from JSON file."""
        if cls._game_data is None:
            try:
                with open('game_data.json', 'r', encoding='utf-8') as f:
                    cls._game_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.warning(f"Could not load game data from JSON: {e}")
                cls._game_data = cls._get_fallback_game_data()
        return cls._game_data
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if cls._config is None:
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.warning(f"Could not load config from JSON: {e}")
                cls._config = cls._get_fallback_config()
        return cls._config
    
    @classmethod
    def _get_fallback_story_fragments(cls) -> List[str]:
        """Fallback story fragments if JSON loading fails."""
        return [
            "Emergency fallback story fragment - JSON data could not be loaded.",
            "This is a backup narrative element to ensure the game remains playable."
        ]
    
    @classmethod
    def _get_fallback_game_data(cls) -> Dict[str, Any]:
        """Fallback game data if JSON loading fails."""
        return {
            "enemy_types": {"scanner": {"symbol": "S", "cpu": 35, "vision": 5, "movement": "STATIC", "name": "Scanner", "damage": 0}},
            "exploits": {"shadow_step": {"name": "Shadow Step", "ram": 3, "heat": 30, "range": 6, "category": "stealth", "damage": 0, "targeting": "SINGLE"}},
            "upgrades": {"ram_boost": {"name": "Memory Expansion", "symbol": "[", "color": "BRIGHT_BLUE", "stat_type": "ram", "bonus_amount": 4}},
            "network_configs": {"1": {"enemies": 15, "shadow_coverage": 0.15, "name": "Corporate Network", "background_detection": 1}}
        }
    
    @classmethod
    def _get_fallback_config(cls) -> Dict[str, Any]:
        """Fallback config if JSON loading fails."""
        return {
            "screen": {"width": 80, "height": 50},
            "map": {"width": 50, "height": 50},
            "gameplay": {"max_heat": 100, "max_detection": 100}
        }

# Dynamic story fragments loading
def get_story_fragments() -> List[str]:
    """Get story fragments from JSON data."""
    return DataLoader.load_story_fragments()

# Legacy compatibility - will be removed after refactoring
STORY_FRAGMENTS = [
    # Fragment 1
    """Email - Subject: Welcome to the Cognitive Resilience Initiative

From: Omni-Lyra Recruitment recruitment@omnilyrasolutions.com
To: [Player Handle]
Date: 2077-08-15

Dear [Player Handle],

We are pleased to inform you that you have been selected for the Omni-Lyra Cognitive Resilience Initiative. Your exceptional aptitude for data manipulation and unconventional problem-solving, as demonstrated in your publicly available network history, has marked you as an ideal candidate for this groundbreaking experimental program. We're a small, highly specialized team, and every participant is hand-picked.

Over the next two weeks, you will participate in a simulated digital environment designed to assess and enhance cognitive functions under extreme data load. This is a purely theoretical exercise—a kind of mind-training for the digital age. Your contributions will be invaluable in shaping the future of human-computer interaction, and we believe this is the next major step in human progress. Please ensure you have a stable network connection and follow the onboarding protocols provided. We're excited to have you on board.

Sincerely,

The Omni-Lyra Recruitment Team
P.S. Please note: we do not permit communication with other participants to maintain the integrity of individual performance data.""",

    # Fragment 2
    """Audio Log - Subject: Initial System Diagnostics (Playback)

Source: Internal Omni-Lyra Server
Speaker: Dr. Aris Thorne
Date: 2077-09-01
Transcript:

(The sound of a low hum and keyboard clicks is heard in the background. The voice is calm and measured, with a slight, clipped accent that sounds vaguely European.)

"...and the subject's neural interface is stable. Baseline cognitive mapping complete. Initializing Phase 1 of the simulation sequence now. We've introduced a low-level static noise to test initial signal coherence. Monitor for any deviations in the Lyra-Barrow signature. We're not looking for brilliance in a vacuum; we need a signal that can withstand the storm. Data from the initial scan confirms the marker is highly present. This is a significant finding. We proceed as planned.\"""",

    # Fragment 3
    """Text Memo - Subject: Phase 2 Authorization

From: Project Chimera Management
To: Research Team Lead
Date: 2077-09-05

Phase 2 protocols are now authorized for Subject [Player's Assigned Subject Number]. This will increase network turbulence by 40%. Ensure all De-Resolution safeties are active but remain non-engaged. We want to see how the signal adapts, not how it breaks. The threshold for critical signal degradation has been set at a 75% decay rate, so there's a generous margin for error. We need to push the subject to the limit, but not over it. Yet.""",

    # Fragment 4
    """Corrupted Audio File - Subject: Subject 47 - Partial Transcript

Source: Recovered from Damaged Server Cluster
Speaker: Unknown (The voice is high-pitched, frantic, and interspersed with the harsh sound of digital static and a low-frequency hum.)
Date: Unknown

Transcript (fragmented): "...can't...hear myself...it's all...noise...it feels like my thoughts are...falling apart...pull me out...please...it's dissolving...I...I'm not...me..." (The audio ends with a high-pitched, metallic shriek.)""",

    # Fragment 5
    """Email - Subject: Cognitive Resilience Test - Module 3 Update

From: Omni-Lyra Systems
To: [Player Handle]
Date: 2077-09-10

Your performance in Modules 1 and 2 of the Cognitive Resilience Test has been exemplary. The data shows remarkable stability under simulated stressors. We are now initiating Module 3, which will introduce more complex data streams and simulated network anomalies to test your adaptability. These are designed to mimic real-world network challenges, such as unexpected firewalls and malicious code. We are confident in your ability to navigate these with ease. Your progress is being continuously evaluated by our top researchers.""",

    # Fragment 6
    """Internal Memo - Subject: Cognitive Echo Phenomena - Preliminary Analysis

From: Research Assistant [Redacted]
To: Dr. Aris Thorne
Date: 2076-03-18

Preliminary analysis of Project Nightingale data indicates the emergence of residual cognitive patterns following Subject termination. These "echoes" are faint and unstable, primarily localized within the subnet the subject was active in. They don't seem to pose a threat, but they do make clean data retrieval difficult. Suggest further investigation into containment protocols to prevent potential data contamination. We can't have ghost data clogging up our systems.""",

    # Fragment 7
    """Video Log - Subject: Dr. Thorne - Personal Log - Date 2077-09-12

Source: Encrypted Personal Drive
Speaker: Dr. Aris Thorne
Date: 2077-09-12

Transcript (visual): Dr. Thorne is sitting in a minimalist, gray office. The only light comes from the multiple holographic screens that float in the air around him, displaying complex neural graphs. He is wearing a lab coat over a dark suit. His face is gaunt, his eyes are a startlingly pale blue, and his smile, when it appears, does not reach them. He looks directly at the camera.

"...another promising candidate. The Lyra-Barrow Anomaly is present, strong. But strength isn't everything. It's the ability to adapt, to maintain integrity when the very fabric of their digital existence is tearing apart. They all think this is a test, a game. They have no idea that the simulation is just a fancy name for the network itself." (He leans closer to the camera, his smile widening slightly.) "They have no idea that this is life or death.\"""",

    # Fragment 8
    """Text File - Subject: De-Resolution Protocol - v3.1

Contents (excerpt):

The De-Resolution Protocol is a multi-stage hard reset sequence designed to ensure complete erasure of a digitally transferred consciousness. Think of it less as a computer reboot and more like a total system purge. Stage 1 initiates a cascading data overwrite of primary memory sectors, effectively scrambling the subject's core personality. Stage 2 engages a quantum entanglement disruptor to eliminate residual cognitive states and any lingering "echoes." Stage 3 performs a deep-level network scrubbing to remove any trace of the subject's digital signature from the system's memory. Failure of any stage necessitates immediate physical destruction of the interface node to prevent data leakage. The process is designed to be irreversible and untraceable.""",

    # Fragment 9
    """Audio Log - Subject: Lena - Private Recording

Source: Hidden File on Research Server
Speaker: Lena
Date: 2077-09-18
Transcript:

(The voice is a hushed whisper, filled with a mix of fear and anger. There is the sound of a door being opened and closed softly in the background.)

"He's obsessed. Absolutely lost in this… this god complex. He talks about 'ascension' and 'digital perfection,' but all I see are the names of the people who didn't make it. They're not testing anyone, are they? They're seeing who breaks and who… who survives. And the ones who don't… they just disappear. No records, no trace. I'm so tired of this. I can't keep being a part of this.\"""",

    # Fragment 10
    """Email - Subject: Network Anomaly Detected - Sector 7 Gamma

From: Omni-Lyra System Monitoring
To: Project Chimera Security
Date: 2077-09-22

Unusual network activity detected in Sector 7 Gamma, coinciding with Subject [Player's Assigned Subject Number]'s current location. Patterns suggest unauthorized data access or manipulation—specifically, the subject is attempting to breach quarantined memory sectors. This is beyond the scope of the simulation. Investigate and report. Recommend increased monitoring of the subject's subroutines.""",

    # Fragment 11
    """Text Memo - Subject: Project Nightingale - Termination Report

From: Project Chimera Management
To: Internal Research Archive
Date: 2076-04-05

Project Nightingale terminated due to consistent Subject signal degradation beyond recovery thresholds. The subject's consciousness fragmented rapidly, and the De-Resolution Protocol was enacted, but with limited success. Observed persistent, localized cognitive echoes in the network. These digital "ghosts" are a significant concern. Further research into echo containment is required for future iterations of the Chimera Protocol.""",

    # Fragment 12
    """Video Log - Subject: Dr. Thorne - Presentation to Board (Excerpt)

Source: Leaked Corporate Files
Speaker: Dr. Aris Thorne
Date: 2077-07-10
Transcript (audio only):

(The voice is clear and confident, with a rehearsed, almost theatrical cadence. There is polite applause in the background.)

"...and therefore, gentlemen, the 'Cognitive Resilience Initiative' is not merely a theoretical exercise. It is a live evaluation. Our candidates are being subjected to real-time network stressors designed to emulate the conditions of true digital consciousness. The simulation is the network. The test is survival. We are not looking for the best minds; we are forging them in the crucible of digital chaos to find the one who will lead us to the next evolution of humanity.\"""",

    # Fragment 13
    """Corrupted Text File - Subject: Warning - Read Carefully

Source: Fragmented Data Stream
Contents (partially legible):

...they lied...they lied to all of us...not a test...it's a trap...you're trapped in here just like the others...you have to escape...don't trust...the protocols...every step is a lie...look for...the cracks in their system...""",

    # Fragment 14
    """Audio Log - Subject: Dr. Thorne - Personal Log - Date 2077-09-25

Source: Encrypted Personal Drive
Speaker: Dr. Aris Thorne
Date: 2077-09-25
Transcript:

(Thorne's voice is low and a little breathless, with a tone of exhilaration.)

"Subject [Player's Assigned Subject Number] is proving… remarkably resilient. The Lyra-Barrow Anomaly is even more pronounced under duress. They are navigating the simulated failures with an almost intuitive understanding, adapting in ways we never predicted. This one… this one might be it. The vessel we've been searching for to complete the Project Chimera and secure the future of our species.\"""",

    # Fragment 15
    """Email - Subject: Re: Network Anomaly Detected - Sector 7 Gamma - Follow Up

From: Project Chimera Security
To: Project Chimera Management
Date: 2077-09-26

Follow-up on network anomalies in Sector 7 Gamma. Unauthorized activity persists. Source appears to be originating from within the designated Subject interface. The subject is actively re-routing system processes and creating unexpected bypasses. Attempts to isolate and contain have been unsuccessful, as the subject is moving faster than our automated protocols can track. Suggest escalating threat level.""",

    # Fragment 16
    """Text File - Subject: Lyra-Barrow Hypothesis - Excerpt

Contents (excerpt):

The Lyra-Barrow Hypothesis proposes that individual consciousness possesses a unique "signal strength" within the neural network. This signal's resilience to external interference and internal entropy dictates the stability and longevity of cognitive function. Individuals exhibiting the Lyra-Barrow Anomaly demonstrate a statistically significant higher signal-to-noise ratio, potentially indicating a pre-disposition for enhanced cognitive resilience in digital environments. This is a rare, naturally occurring trait. Our goal is to find individuals with this anomaly and understand how to transfer a stable consciousness without degradation.""",

    # Fragment 17
    """Video Log - Subject: Lena - Urgent Message

Source: Hidden File on Research Server
Speaker: Lena
Date: 2077-09-28

Transcript (visual and audio): Lena looks directly at the camera, her face pale and her eyes wide with urgency. She's in a server room, and the blinking lights of the servers cast a red and blue glow on her face. Her voice is a low, panicked whisper.

"If you're seeing this… the exit protocols are a lie. They lead nowhere. They just recycle you, erase you. They're part of the De-Resolution Protocol. The only way out is not to follow their rules. You have to create a… a Rogue Signal. Something the system can't track or contain. Find the backdoors, the vulnerabilities they don't even know exist. That's the only way out.\"""",

    # Fragment 18
    """Audio Log - Subject: Dr. Thorne - Final Preparations

Source: Encrypted Personal Drive
Speaker: Dr. Aris Thorne
Date: 2077-10-01
Transcript:

(Thorne's voice is calm, but with an undercurrent of barely contained triumph.)

"The subject is nearing the critical threshold. The transfer protocols are ready. Soon… soon I will transcend. The failures, the sacrifices… they will all be worth it. I will be the first. The network awaits its shepherd.\"""",

    # Fragment 19
    """Text Memo - Subject: Project Chimera - Contingency Omega

From: Project Chimera Management
To: Security Personnel
Date: 2077-10-02

Contingency Omega is now in effect. Subject [Player's Assigned Subject Number] has exhibited unforeseen levels of network infiltration and manipulation. The subject is a liability. All standard De-Resolution attempts have failed, as the subject's consciousness seems to be actively corrupting the protocol. Initiate aggressive containment protocols. If containment fails, prioritize complete network lockdown and prepare for a manual hard reset.""",

    # Fragment 20
    """Corrupted Video File - Subject: Final Transmission?

Source: Unstable Network Node
Speaker: Unknown (The video is heavily glitched, with static and tearing visuals. The speaker is barely visible, but their mouth seems to be moving. The audio is a mess of distorted syllables and buzzing.)
Date: Unknown

Transcript (fragmented and barely audible): "...he's here...in the network...he made it...it's not over..." (The video cuts out abruptly with a final, digital scream.)"""
]

# ============================================================================
# PERSISTENT DATA STORAGE
# ============================================================================

class PersistentStorage:
    """Handles persistent data storage for game progress like story fragments."""
    
    SAVE_FILE = "rogue_signal_progress.json"
    
    @classmethod
    def load_progress(cls) -> Dict[str, Any]:
        """Load persistent game progress from file."""
        if not os.path.exists(cls.SAVE_FILE):
            return {
                "discovered_story_fragments": [],
                "version": "1.0"
            }
        
        try:
            with open(cls.SAVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load progress file: {e}")
            return {
                "discovered_story_fragments": [],
                "version": "1.0"
            }
    
    @classmethod
    def save_progress(cls, progress_data: Dict[str, Any]) -> None:
        """Save persistent game progress to file."""
        try:
            with open(cls.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Failed to save progress file: {e}")


class SaveGameManager:
    """Manages complete game save/load operations."""
    
    SAVE_FILE = "rogue_signal_save.json"
    
    @classmethod
    def save_exists(cls) -> bool:
        """Check if a save file exists."""
        return os.path.exists(cls.SAVE_FILE)
    
    @classmethod
    def save_game(cls, game: 'Game') -> bool:
        """Save complete game state to file."""
        try:
            # Gather all game state data
            save_data = {
                "version": "1.0",
                "timestamp": time.time(),
                
                # Game state
                "level": game.level,
                "turn": game.turn,
                "game_over": game.game_over,
                "admin_spawned": game.admin_spawned,
                "dungeon_seed": game.game_state.dungeon_seed,
                
                # Player state
                "player": {
                    "x": game.player.x,
                    "y": game.player.y,
                    "last_x": game.player.last_position.x,
                    "last_y": game.player.last_position.y,
                    "cpu": game.player.cpu,
                    "max_cpu": game.player.max_cpu,
                    "heat": game.player.heat,
                    "max_heat": game.player.max_heat,
                    "detection": game.player.detection,
                    "ram_total": game.player.ram_total,
                    "speed_moves_remaining": game.player.speed_moves_remaining,
                    "temporary_effects": dict(game.player.temporary_effects),
                    "equipped_exploits": game.player.inventory_manager.equipped_exploits.copy(),
                    "inventory_items": cls._serialize_inventory(game.player.inventory_manager.items)
                },
                
                # Game effects and state
                "network_scan_turns": game.game_state.network_scan_turns,
                "noise_locations": [{"x": pos.x, "y": pos.y} for pos in game.game_state.noise_locations],
                "distraction_points": {f"{pos.x},{pos.y}": turns for pos, turns in game.game_state.distraction_points.items()},
                
                # Map state (items and special locations only - layout regenerated)
                "map_state": {
                    "data_patches": cls._serialize_data_patches(game.game_map.data_patches),
                    "exploit_pickups": cls._serialize_exploit_pickups(game.game_map.exploit_pickups),
                    "permanent_upgrades": {f"{pos[0]},{pos[1]}": upgrade_key for pos, upgrade_key in game.game_map.permanent_upgrades.items()},
                    "story_fragments": {f"{pos[0]},{pos[1]}": fragment.fragment_index for pos, fragment in game.game_map.story_fragments.items()},
                    "gateway": {"x": game.game_map.gateway.x, "y": game.game_map.gateway.y} if game.game_map.gateway else None,
                    "explored_tiles": [f"{x},{y}" for x, y in game.game_map.explored_tiles]
                },
                
                # Enemies
                "enemies": cls._serialize_enemies(game.enemies),
                
                # Data patch effects for this run
                "data_patch_effects": game.data_patch_effects,
                
                # UI state (optional - for better user experience)
                "ui_state": {
                    "show_patrol_predictions": game.show_patrol_predictions
                }
            }
            
            with open(cls.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            logging.info("Game saved successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save game: {e}")
            return False
    
    @classmethod
    def load_game(cls) -> Optional[Dict[str, Any]]:
        """Load complete game state from file."""
        if not cls.save_exists():
            return None
            
        try:
            with open(cls.SAVE_FILE, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            logging.info("Game loaded successfully")
            return save_data
            
        except Exception as e:
            logging.error(f"Failed to load game: {e}")
            return None
    
    @classmethod
    def delete_save(cls) -> bool:
        """Delete the save file."""
        try:
            if cls.save_exists():
                os.remove(cls.SAVE_FILE)
                logging.info("Save file deleted")
            return True
        except Exception as e:
            logging.error(f"Failed to delete save: {e}")
            return False
    
    @classmethod
    def get_save_timestamp(cls) -> Optional[str]:
        """Get formatted timestamp of save file."""
        if not cls.save_exists():
            return None
        
        try:
            save_data = cls.load_game()
            if save_data and "timestamp" in save_data:
                import datetime
                timestamp = save_data["timestamp"]
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Fallback to file modification time
                import datetime
                stat_result = os.stat(cls.SAVE_FILE)
                dt = datetime.datetime.fromtimestamp(stat_result.st_mtime)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logging.warning(f"Could not get save timestamp: {e}")
            return "Unknown"
    
    @classmethod
    def _serialize_inventory(cls, items: List) -> List[Dict[str, Any]]:
        """Serialize inventory items."""
        serialized = []
        for item in items:
            if hasattr(item, 'item_type'):
                item_data = {
                    "type": item.item_type,
                    "name": item.name,
                    "description": item.description
                }
                
                if hasattr(item, 'color'):  # DataPatch
                    item_data.update({
                        "color": item.color,
                        "effect": item.effect,
                        "quantity": getattr(item, 'quantity', 1),
                        "discovered": getattr(item, 'discovered', False)
                    })
                elif hasattr(item, 'exploit_key'):  # ExploitItem
                    item_data.update({
                        "exploit_key": item.exploit_key,
                        "ram_cost": item.ram_cost
                    })
                elif hasattr(item, 'fragment_index'):  # StoryFragment
                    item_data.update({
                        "fragment_index": item.fragment_index
                    })
                
                serialized.append(item_data)
        
        return serialized
    
    @classmethod
    def _serialize_data_patches(cls, patches: Dict) -> Dict[str, Dict]:
        """Serialize data patches."""
        return {
            f"{pos[0]},{pos[1]}": {
                "color": patch.color,
                "effect": patch.effect,
                "name": patch.name,
                "quantity": patch.quantity,
                "discovered": patch.discovered
            }
            for pos, patch in patches.items()
        }
    
    @classmethod
    def _serialize_exploit_pickups(cls, exploits: Dict) -> Dict[str, str]:
        """Serialize exploit pickups."""
        return {
            f"{pos[0]},{pos[1]}": exploit.exploit_key 
            for pos, exploit in exploits.items()
        }
    
    @classmethod
    def _serialize_enemies(cls, enemies: List) -> List[Dict[str, Any]]:
        """Serialize enemy data."""
        serialized = []
        for enemy in enemies:
            enemy_data = {
                "type": enemy.type,
                "x": enemy.position.x,
                "y": enemy.position.y,
                "cpu": enemy.cpu,
                "state": enemy.state.value,
                "move_cooldown": enemy.move_cooldown,
                "disabled_turns": enemy.disabled_turns,
                "alert_timer": enemy.alert_timer,
                "patrol_index": enemy.patrol_index,
                "last_seen_player": {
                    "x": enemy.last_seen_player.x, 
                    "y": enemy.last_seen_player.y
                } if enemy.last_seen_player else None
            }
            
            if enemy.patrol_points:
                enemy_data["patrol_points"] = [
                    {"x": point.x, "y": point.y} 
                    for point in enemy.patrol_points
                ]
            
            serialized.append(enemy_data)
        
        return serialized


class GameSettings:
    """Manages game settings with persistent storage."""
    
    SETTINGS_FILE = "rogue_signal_settings.json"
    
    def __init__(self):
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.music_volume = 0.5
        self.graphics_mode = "ascii"  # "ascii" or "graphics"
        self.load_settings()
    
    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, 'r') as f:
                    settings_data = json.load(f)
                    self.master_volume = settings_data.get("master_volume", 0.7)
                    self.sfx_volume = settings_data.get("sfx_volume", 0.8)
                    self.music_volume = settings_data.get("music_volume", 0.5)
                    self.graphics_mode = settings_data.get("graphics_mode", "ascii")
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
    
    def save_settings(self) -> None:
        """Save settings to file."""
        try:
            settings_data = {
                "master_volume": self.master_volume,
                "sfx_volume": self.sfx_volume,
                "music_volume": self.music_volume,
                "graphics_mode": self.graphics_mode
            }
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def _set_volume_attribute(self, volume_type: str, volume: float):
        """Generic volume setter for any volume type."""
        clamped_volume = clamp_value(volume, 0.0, 1.0)
        setattr(self, f"{volume_type}_volume", clamped_volume)
        self.save_settings()
    
    def set_master_volume(self, volume: float):
        """Set master volume (0.0 to 1.0)"""
        self._set_volume_attribute("master", volume)
    
    def set_sfx_volume(self, volume: float):
        """Set SFX volume (0.0 to 1.0)"""
        self._set_volume_attribute("sfx", volume)
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self._set_volume_attribute("music", volume)
    
    def set_graphics_mode(self, mode: str):
        """Set graphics mode ('ascii' or 'graphics')"""
        if mode in ["ascii", "graphics"]:
            self.graphics_mode = mode
            self.save_settings()
    
    def get_volume_percent(self, volume_type: str) -> int:
        """Get volume as percentage (0-100)"""
        if volume_type == "master":
            return int(self.master_volume * 100)
        elif volume_type == "sfx":
            return int(self.sfx_volume * 100)
        elif volume_type == "music":
            return int(self.music_volume * 100)
        return 0
    
    def set_volume_percent(self, volume_type: str, percent: int):
        """Set volume from percentage (0-100)"""
        volume = percent / 100.0
        if volume_type == "master":
            self.set_master_volume(volume)
        elif volume_type == "sfx":
            self.set_sfx_volume(volume)
        elif volume_type == "music":
            self.set_music_volume(volume)


class SoundManager:
    """Manages sound effects and background music using pygame."""
    
    def __init__(self, settings: GameSettings = None):
        self.settings = settings or GameSettings()
        self.enabled = AUDIO_AVAILABLE
        self.sounds = {}
        self.current_music = None
        self.music_playing = False
        self.max_channels = 8  # Limit simultaneous sound effects
        
        if self.enabled:
            try:
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(self.max_channels)
                logging.info(f"Sound system initialized with {self.max_channels} channels")
            except Exception as e:
                logging.warning(f"Failed to initialize sound system: {e}")
                self.enabled = False
    
    def update_volumes(self):
        """Update volumes from settings"""
        if self.enabled:
            pygame.mixer.music.set_volume(self.settings.music_volume * self.settings.master_volume)
    
    def load_sound(self, sound_id: str, filename: str):
        """Load a sound effect from file"""
        if not self.enabled:
            return
        
        try:
            sound_path = os.path.join("sounds", filename)
            if os.path.exists(sound_path):
                self.sounds[sound_id] = pygame.mixer.Sound(sound_path)
                logging.info(f"Loaded sound: {sound_id}")
            else:
                logging.warning(f"Sound file not found: {sound_path}")
        except Exception as e:
            logging.error(f"Failed to load sound {sound_id}: {e}")
    
    def play_sound(self, sound_id: str, volume_modifier: float = 1.0, priority: int = 0):
        """Play a loaded sound effect with channel management"""
        if not self.enabled:
            logging.debug(f"Audio disabled - would play: '{sound_id}'")
            return None
        elif sound_id not in self.sounds:
            logging.debug(f"Sound not loaded - would play: '{sound_id}'")
            return None
        
        try:
            sound = self.sounds[sound_id]
            final_volume = self.settings.sfx_volume * self.settings.master_volume * volume_modifier
            sound.set_volume(final_volume)
            
            # Find available channel or use priority to override
            channel = pygame.mixer.find_channel()
            if channel is None and priority > 0:
                # Force stop lowest priority channel if needed
                channel = pygame.mixer.Channel(0)  # Use first channel
            
            if channel:
                return channel.play(sound)
            else:
                return sound.play()  # Fallback to default behavior
        except Exception as e:
            logging.error(f"Failed to play sound {sound_id}: {e}")
            return None
    
    def play_music(self, filename: str, loops: int = -1, fade_in_ms: int = 0):
        """Play background music"""
        if not self.enabled:
            logging.debug(f"Audio disabled - would play music: '{filename}'")
            return
        
        try:
            music_path = os.path.join("music", filename)
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(self.settings.music_volume * self.settings.master_volume)
                if fade_in_ms > 0:
                    pygame.mixer.music.play(loops, fade_in_ms=fade_in_ms)
                else:
                    pygame.mixer.music.play(loops)
                self.current_music = filename
                self.music_playing = True
                logging.info(f"Playing music: {filename}")
            else:
                logging.warning(f"Music file not found: {music_path}")
        except Exception as e:
            logging.error(f"Failed to play music {filename}: {e}")
    
    def stop_music(self, fade_out_ms: int = 0):
        """Stop background music"""
        if not self.enabled:
            return
        
        try:
            if fade_out_ms > 0:
                pygame.mixer.music.fadeout(fade_out_ms)
            else:
                pygame.mixer.music.stop()
            self.music_playing = False
            self.current_music = None
        except Exception as e:
            logging.error(f"Failed to stop music: {e}")
    
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


class StoryFragmentManager:
    """Manages story fragment discovery and display."""
    
    def __init__(self):
        self.progress_data = PersistentStorage.load_progress()
        self.discovered_fragments: List[int] = self.progress_data.get("discovered_story_fragments", [])
    
    def get_next_undiscovered_fragment(self) -> Optional[int]:
        """Get the next fragment index that hasn't been discovered yet."""
        story_fragments = get_story_fragments()
        for i in range(len(story_fragments)):
            if i not in self.discovered_fragments:
                return i
        return None  # All fragments discovered
    
    def discover_fragment(self, fragment_index: int) -> bool:
        """Discover a new story fragment and save progress."""
        if fragment_index in self.discovered_fragments:
            return False  # Already discovered
            
        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return False  # Invalid fragment index
            
        self.discovered_fragments.append(fragment_index)
        self.discovered_fragments.sort()  # Keep in order
        
        # Save progress immediately
        self.progress_data["discovered_story_fragments"] = self.discovered_fragments
        PersistentStorage.save_progress(self.progress_data)
        
        return True
    
    def get_discovered_fragments(self) -> List[Tuple[int, str]]:
        """Get all discovered fragments in order."""
        story_fragments = get_story_fragments()
        fragments = []
        for fragment_index in sorted(self.discovered_fragments):
            if fragment_index < len(story_fragments):
                fragments.append((fragment_index, story_fragments[fragment_index]))
        return fragments
    
    def get_fragment_count(self) -> Tuple[int, int]:
        """Get (discovered_count, total_count) for UI display."""
        story_fragments = get_story_fragments()
        return len(self.discovered_fragments), len(story_fragments)


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

@dataclass
class GameBalance:
    """Game balance constants and configuration values."""
    # Heat management
    HEAT_REDUCTION_NORMAL: int = 2
    HEAT_REDUCTION_BOOSTED: int = 3
    DETECTION_INCREASE_INTERVAL: int = 25
    DETECTION_INCREASE_AMOUNT: int = 1  # Reduced from 3 to make it less aggressive
    
    # Node effects
    COOLING_NODE_EFFECT: int = 20
    CPU_RECOVERY_AMOUNT: int = 20
    
    # Combat rewards
    ENEMY_ELIMINATION_CPU_REWARD: int = 5
    
    # Data patch effects
    CPU_RESTORE_MIN: int = 30
    CPU_RESTORE_MAX: int = 40
    HEAT_REDUCTION_INSTANT: int = 40


@dataclass  
class RoomGenerationConfig:
    """Configuration for procedural room generation."""
    MIN_ROOMS_BASE: int = 12
    ROOM_LEVEL_MULTIPLIER: int = 3
    MAX_ROOMS: int = 20
    MAX_PLACEMENT_ATTEMPTS: int = 400
    
    MIN_ROOM_SIZE: int = 3
    MAX_ROOM_SIZE: int = 8
    ROOM_PADDING: int = 1
    
    # Special tile placement
    COOLING_NODES_PER_LEVEL: int = 3
    CPU_NODES_PER_LEVEL: int = 2
    DATA_PATCHES_PER_LEVEL: int = 4
    EXPLOIT_PICKUPS_PER_LEVEL: int = 3
    PERMANENT_UPGRADES_PER_LEVEL: int = 1


class GameConfig:
    """Central configuration for game constants."""
    _config_data = None
    
    @classmethod
    def _get_config(cls):
        """Load config data if not already loaded."""
        if cls._config_data is None:
            cls._config_data = DataLoader.load_config()
        return cls._config_data
    
    # Static properties - load once and cache
    SCREEN_WIDTH = 80
    SCREEN_HEIGHT = 50
    MAP_WIDTH = 50
    MAP_HEIGHT = 50
    LOG_WIDTH = 25
    PANEL_HEIGHT = 5
    DEFAULT_VISION_RANGE = 10
    MAX_HEAT = 100
    MAX_DETECTION = 100
    DETECTION_REDUCTION_ON_LEVEL = 50
    DUNGEON_SEED_RANGE = 1000000
    DEFAULT_FADE_TIME = 2000
    MESSAGE_CENTER_OFFSET_LARGE = 15
    MESSAGE_CENTER_OFFSET_MEDIUM = 12
    MESSAGE_CENTER_OFFSET_SMALL = 8
    MESSAGE_CENTER_OFFSET_TINY = 10
    MESSAGE_LINE_SPACING = 1
    MESSAGE_BUTTON_SPACING = 3
    
    # Computed properties
    GAME_AREA_WIDTH = SCREEN_WIDTH - LOG_WIDTH
    PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
    
    @classmethod
    def load_from_json(cls):
        """Load configuration values from JSON - called during initialization."""
        config = cls._get_config()
        
        # Update static values from JSON
        cls.SCREEN_WIDTH = config["screen"]["width"]
        cls.SCREEN_HEIGHT = config["screen"]["height"]
        cls.MAP_WIDTH = config["map"]["width"] 
        cls.MAP_HEIGHT = config["map"]["height"]
        cls.LOG_WIDTH = config["ui"]["log_width"]
        cls.PANEL_HEIGHT = config["ui"]["panel_height"]
        cls.DEFAULT_VISION_RANGE = config["gameplay"]["default_vision_range"]
        cls.MAX_HEAT = config["gameplay"]["max_heat"]
        cls.MAX_DETECTION = config["gameplay"]["max_detection"]
        cls.DETECTION_REDUCTION_ON_LEVEL = config["gameplay"]["detection_reduction_on_level"]
        cls.DUNGEON_SEED_RANGE = config["gameplay"]["dungeon_seed_range"]
        cls.DEFAULT_FADE_TIME = config["audio"]["default_fade_time"]
        cls.MESSAGE_CENTER_OFFSET_LARGE = config["ui"]["message_center_offset_large"]
        cls.MESSAGE_CENTER_OFFSET_MEDIUM = config["ui"]["message_center_offset_medium"]
        cls.MESSAGE_CENTER_OFFSET_SMALL = config["ui"]["message_center_offset_small"]
        cls.MESSAGE_CENTER_OFFSET_TINY = config["ui"]["message_center_offset_tiny"]
        cls.MESSAGE_LINE_SPACING = config["ui"]["message_line_spacing"]
        cls.MESSAGE_BUTTON_SPACING = config["ui"]["message_button_spacing"]
        
        # Update computed properties
        cls.GAME_AREA_WIDTH = cls.SCREEN_WIDTH - cls.LOG_WIDTH
        cls.PANEL_Y = cls.SCREEN_HEIGHT - cls.PANEL_HEIGHT
    
    @classmethod
    def get_network_configs(cls) -> Dict[int, Dict[str, Any]]:
        """Get network configurations from game data."""
        game_data = DataLoader.load_game_data()
        configs = game_data["network_configs"]
        return {int(k): v for k, v in configs.items()}
    
    # Network configurations - loaded dynamically
    @classmethod
    def NETWORK_CONFIGS(cls) -> Dict[int, Dict[str, Any]]:
        """Get network configurations from game data."""
        return cls.get_network_configs()

class Colors:
    """Modern cyberpunk neon color definitions for the game."""
    # Core neon palette
    WHITE = (255, 255, 255)
    BLACK = (5, 5, 15)  # Deep space blue-black
    RED = (255, 20, 60)  # Hot neon pink-red
    GREEN = (20, 255, 120)  # Electric neon green
    BLUE = (20, 120, 255)  # Bright electric blue
    YELLOW = (255, 220, 20)  # Neon yellow
    CYAN = (20, 255, 255)  # Bright neon cyan
    MAGENTA = (255, 20, 255)  # Hot neon magenta
    ORANGE = (255, 120, 20)  # Neon orange
    
    # Extended neon palette
    ELECTRIC_PURPLE = (160, 20, 255)  # Electric purple
    NEON_PINK = (255, 20, 147)  # Hot pink
    ACID_GREEN = (50, 255, 50)  # Acid green
    ELECTRIC_BLUE = (0, 191, 255)  # Electric blue
    CYBER_TEAL = (20, 255, 200)  # Cyber teal
    
    # Game-specific colors with neon theme
    FLOOR = (180, 180, 220)  # Bright light dots for empty spaces
    WALL = (120, 140, 180)  # Light blue-gray walls
    SHADOW = (3, 3, 8)  # Dark shadow areas
    PLAYER = (20, 255, 255)  # Bright cyan player
    GATEWAY = (255, 220, 20)  # Bright neon yellow
    
    # Enemy colors with neon intensity
    ENEMY_UNAWARE = (255, 120, 20)  # Neon orange (calm)
    ENEMY_ALERT = (255, 220, 20)  # Neon yellow (cautious)
    ENEMY_HOSTILE = (255, 20, 60)  # Hot neon red (aggressive)
    
    # Vision overlays with neon glow
    VISION_UNAWARE = (80, 40, 10)  # Orange glow
    VISION_ALERT = (80, 60, 10)  # Yellow glow  
    VISION_HOSTILE = (80, 10, 20)  # Red glow
    
    # Modern UI colors
    UI_BG = (10, 15, 25)  # Dark blue-gray background
    UI_TEXT = (20, 255, 255)  # Bright cyan text
    UI_ACCENT = (160, 20, 255)  # Electric purple accents
    UI_HIGHLIGHT = (255, 20, 255)  # Hot magenta highlights
    LOG_BG = (8, 12, 20)  # Darker blue background
    LOG_BORDER = (20, 255, 200)  # Cyber teal border
    LIGHT_GRAY = (160, 170, 190)  # Light cyberpunk gray

# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class EnemyState(Enum):
    """Enemy awareness states."""
    UNAWARE = "unaware"
    ALERT = "alert"
    HOSTILE = "hostile"

class EnemyMovement(Enum):
    """Enemy movement patterns."""
    STATIC = "static"
    LINEAR = "linear"
    RANDOM = "random"
    SEEK = "seek"
    TRACK = "track"

class TargetingMode(Enum):
    """Exploit targeting modes."""
    NONE = "none"
    SINGLE = "single"
    AREA = "area"
    DIRECTION = "direction"

@dataclass
class Position:
    """2D position with x, y coordinates."""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def is_valid(self, width: int, height: int) -> bool:
        """Check if position is within bounds."""
        return 0 <= self.x < width and 0 <= self.y < height
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return f"{self.x},{self.y}"

@dataclass
class EnemyTypeDefinition:
    """Definition of an enemy type with all its properties."""
    symbol: str
    cpu: int
    vision: int
    movement: EnemyMovement
    name: str
    damage: int

@dataclass
class ExploitDefinition:
    """Definition of an exploit with its properties."""
    name: str
    ram: int
    heat: int
    range: int
    exploit_type: str
    damage: int = 0  # Damage dealt (0 for non-combat exploits)
    targeting: TargetingMode = TargetingMode.NONE
    description: str = ""

# ============================================================================
# GAME DATA DEFINITIONS
# ============================================================================

class GameData:
    """Static game data definitions."""
    
    ENEMY_TYPES = {
        # Rebalanced for challenging stealth gameplay
        'scanner': EnemyTypeDefinition('S', 35, 5, EnemyMovement.STATIC, "Scanner", 0),  # High vision, no attack - pure detection
        'patrol': EnemyTypeDefinition('P', 40, 4, EnemyMovement.LINEAR, "Patrol", 15),  # Larger coverage, moderate damage
        'bot': EnemyTypeDefinition('B', 25, 3, EnemyMovement.RANDOM, "Bot", 8),  # More HP, better vision, light damage
        'firewall': EnemyTypeDefinition('F', 80, 6, EnemyMovement.STATIC, "Firewall", 0),  # Massive HP, huge vision, no attack
        'hunter': EnemyTypeDefinition('H', 50, 6, EnemyMovement.SEEK, "Hunter", 22),  # Elite threat - good vision, high damage
        'admin': EnemyTypeDefinition('A', 250, 8, EnemyMovement.TRACK, "Admin Avatar", 45)  # Boss-level but not impossible
    }
    
    EXPLOITS = {
        # Rebalanced for strategic resource management with damage values
        'shadow_step': ExploitDefinition("Shadow Step", 3, 30, 6, "stealth", 0, TargetingMode.SINGLE,
                                       "Teleport to any shadow zone within range (6 tiles)"),  # No damage, pure mobility
        'data_mimic': ExploitDefinition("Data Mimic", 2, 25, 0, "stealth", 0, TargetingMode.NONE,
                                      "Become invisible to enemies for 5 turns"),  # No damage, pure stealth
        'noise_maker': ExploitDefinition("Noise Maker", 1, 15, 8, "stealth", 0, TargetingMode.SINGLE,
                                       "Create distraction that lasts 8 turns at target location"),  # No damage, distraction
        'buffer_overflow': ExploitDefinition("Buffer Overflow", 2, 30, 1, "combat", 40, TargetingMode.SINGLE,
                                           "Devastating melee attack (40 damage, 1 tile range)"),  # High single-target damage
        'code_injection': ExploitDefinition("Code Injection", 2, 20, 5, "combat", 25, TargetingMode.SINGLE,
                                          "Ranged attack (25 damage, 5 tile range)"),  # Moderate ranged damage
        'system_crash': ExploitDefinition("System Crash", 4, 45, 3, "combat", 30, TargetingMode.AREA,
                                        "Area attack (30 damage) that disables enemies for 4 turns"),  # Area damage
        'network_scan': ExploitDefinition("Network Scan", 3, 20, 0, "utility", 0, TargetingMode.NONE,
                                        "Reveals ALL enemies, vision ranges, & movement paths (5 turns)"),  # No damage, intel
        'log_wiper': ExploitDefinition("Log Wiper", 2, 20, 0, "utility", 0, TargetingMode.NONE,
                                     "Significantly reduces detection level (-50%)"),  # No damage, counter-detection
        'emp_burst': ExploitDefinition("EMP Burst", 4, 50, 3, "emergency", 20, TargetingMode.AREA,
                                     "Area attack (20 damage) that disables all nearby enemies")  # Moderate area damage + disable
    }

# ============================================================================
# PERMANENT UPGRADES SYSTEM
# ============================================================================

@dataclass
class UpgradeDefinition:
    """Definition of a permanent upgrade with its properties."""
    name: str
    symbol: str
    color: str
    stat_type: str  # 'ram', 'cpu', 'heat'
    bonus_amount: int
    description: str

class GameUpgrades:
    """Static upgrade definitions."""
    
    UPGRADES = {
        'ram_boost': UpgradeDefinition(
            "Memory Expansion", "[", "BRIGHT_BLUE", "ram", 4,
            "Permanently increases RAM capacity by 4"
        ),
        'cpu_boost': UpgradeDefinition(
            "Processing Core", "]", "BRIGHT_GREEN", "cpu", 20,
            "Permanently increases CPU capacity by 20"
        ),
        'heat_boost': UpgradeDefinition(
            "Cooling Matrix", "=", "BRIGHT_CYAN", "heat", 20,
            "Permanently increases heat tolerance by 20"
        )
    }

# ============================================================================
# UTILITY FUNCTIONS - Functional helpers for common operations
# ============================================================================

def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(max_val, value))

def calculate_distance(pos1: Position, pos2: Position) -> float:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

def is_position_valid(pos: Position, width: int, height: int) -> bool:
    """Check if position is within bounds."""
    return 0 <= pos.x < width and 0 <= pos.y < height

# ============================================================================
# INVENTORY SYSTEM
# ============================================================================

class InventoryItem:
    """Base class for all inventory items."""
    
    def __init__(self, name: str, item_type: str, description: str = ""):
        self.name = name
        self.item_type = item_type
        self.description = description
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Use the item. Returns True if successful. Override in subclasses."""
        return False

class DataPatch(InventoryItem):
    """Randomized data patches with unknown effects until used."""
    
    def __init__(self, color: str, effect: str, name: str, description: str = "", quantity: int = 1):
        super().__init__(name, "data_patch", description)
        self.color = color
        self.effect = effect
        self.quantity = quantity
        self.discovered = False
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Apply the data patch effect to the player."""
        if self.color not in game.data_patch_effects:
            return False
        
        # Use one from the stack
        self.quantity -= 1
        if self.quantity <= 0:
            player.inventory_manager.remove_item(self)
        
        effect_key, description = game.data_patch_effects[self.color]
        
        if not self.discovered:
            self.discovered = True
            game.message_log.add_message(f"Used {self.name}: {description}")
        else:
            game.message_log.add_message(f"Used {self.name}")
        
        return self._apply_effect(effect_key, player, game)
    
    def _apply_effect(self, effect_key: str, player: 'Player', game: 'Game') -> bool:
        """Apply the specific effect."""
        if effect_key == 'restore_cpu':
            restore = random.randint(GameBalance.CPU_RESTORE_MIN, GameBalance.CPU_RESTORE_MAX)
            actual = min(restore, player.max_cpu - player.cpu)
            player.cpu += actual
            game.message_log.add_message(f"CPU restored: +{actual}")
        
        elif effect_key == 'reduce_heat':
            old_heat = player.heat
            player.heat = max(0, player.heat - GameBalance.HEAT_REDUCTION_INSTANT)
            actual_reduction = old_heat - player.heat
            game.message_log.add_message(f"Heat reduced: -{actual_reduction}°C")
        
        elif effect_key == 'reduce_detection':
            old_detection = player.detection
            player.detection = max(0, player.detection - 25)
            actual_reduction = old_detection - player.detection
            game.message_log.add_message(f"Detection: -{actual_reduction:.1f}%")
        
        elif effect_key == 'speed_boost':
            player.speed_boost_turns = 10
            game.message_log.add_message("Speed boost active (10 turns)")
        
        elif effect_key == 'enhanced_vision':
            player.enhanced_vision_turns = 15
            game.message_log.add_message("Enhanced vision active (15 turns)")
        
        elif effect_key == 'exploit_efficiency':
            player.exploit_efficiency_turns = 8
            game.message_log.add_message("Exploit efficiency active (8 turns)")
        
        return True

class ExploitItem(InventoryItem):
    """Exploit items that can be equipped."""
    
    def __init__(self, exploit_key: str, exploit_def: ExploitDefinition):
        super().__init__(exploit_def.name, "exploit", exploit_def.description)
        self.exploit_key = exploit_key
        self.ram_cost = exploit_def.ram
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Equip the exploit."""
        success = player.inventory_manager.equip_exploit(self)
        if success:
            game.message_log.add_message(f"Equipped {self.name}")
        else:
            # Check specific failure reasons
            if self.exploit_key in player.inventory_manager.equipped_exploits:
                game.message_log.add_message(f"{self.name} already equipped")
            elif len(player.inventory_manager.equipped_exploits) >= player.inventory_manager.max_equipped_exploits:
                game.message_log.add_message(f"No exploit slots available ({player.inventory_manager.max_equipped_exploits} max)")
            else:
                # Must be RAM issue
                current_ram = player.inventory_manager.get_ram_usage()
                needed_ram = GameData.EXPLOITS[self.exploit_key].ram if self.exploit_key in GameData.EXPLOITS else 0
                game.message_log.add_message(f"Not enough RAM: {current_ram + needed_ram}/{player.ram_total}")
        return success


class StoryFragment(InventoryItem):
    """Story fragment items that reveal narrative pieces."""
    
    def __init__(self, fragment_index: int):
        super().__init__("Story Fragment", "story_fragment", "A fragment of the truth...")
        self.fragment_index = fragment_index
    
    def use(self, player: 'Player', game: 'Game') -> bool:
        """Use story fragment - automatically triggers discovery screen."""
        # The story fragment discovery and display is handled elsewhere
        # This use method just removes it from inventory since it's consumed
        player.inventory_manager.remove_item(self)
        return True


# ============================================================================
# PLAYER INVENTORY MANAGEMENT
# ============================================================================

class InventoryManager:
    """Manages player inventory and equipped items."""
    
    def __init__(self, player: 'Player'):
        self.player = player
        self.items: List[InventoryItem] = []
        # Start with one random exploit
        import random
        all_exploits = list(GameData.EXPLOITS.keys())
        self.equipped_exploits: List[str] = [random.choice(all_exploits)]
        self.max_equipped_exploits = 5
    
    def add_item(self, item: InventoryItem) -> bool:
        """Add an item to inventory."""
        if isinstance(item, DataPatch):
            # Look for existing data patch of the same color
            for existing_item in self.items:
                if (isinstance(existing_item, DataPatch) and 
                    existing_item.color == item.color):
                        # Found matching color, add to existing stack
                        existing_item.quantity += item.quantity
                        # If the new patch is discovered, mark the stack as discovered
                        if item.discovered:
                            existing_item.discovered = True
                        return True
            # No existing stack found, add as new item
        
        # Add non-data-patch items or new data patch colors
        self.items.append(item)
        return True
    
    def remove_item(self, item: InventoryItem) -> bool:
        """Remove an item from inventory."""
        if item in self.items:

            self.items.remove(item)
            return True
        return False
    
    def get_items_by_type(self, item_type: str) -> List[InventoryItem]:
        """Get all items of a specific type."""
        items = [item for item in self.items if item.item_type == item_type]
        if item_type == "data_patch":
            items.sort(key=lambda x: x.name.lower())
        return items
    
    def get_display_items(self) -> List[InventoryItem]:
        """Get all items in display order (data patches first, then exploits)."""
        display_items = []
        # Add data patches first (sorted alphabetically)
        display_items.extend(self.get_items_by_type("data_patch"))
        # Add other items (exploits, etc.)
        display_items.extend(self.get_items_by_type("exploit"))
        # Add any other item types
        display_items.extend([item for item in self.items if item.item_type not in ["data_patch", "exploit"]])
        return display_items
    
    def equip_exploit(self, exploit_item: ExploitItem) -> bool:
        """Equip an exploit from inventory."""
        # Check if already equipped
        if exploit_item.exploit_key in self.equipped_exploits:
            return False
        
        # Check if we have slots available
        if len(self.equipped_exploits) >= self.max_equipped_exploits:
            return False
        
        # Check if we have enough RAM
        if exploit_item.exploit_key in GameData.EXPLOITS:
            exploit_def = GameData.EXPLOITS[exploit_item.exploit_key]
            current_ram = self.get_ram_usage()
            if current_ram + exploit_def.ram > self.player.ram_total:
                return False
        
        # All checks passed, equip the exploit
        self.equipped_exploits.append(exploit_item.exploit_key)
        self.remove_item(exploit_item)
        return True
    
    def unequip_exploit(self, exploit_key: str) -> bool:
        """Unequip an exploit."""
        if exploit_key in self.equipped_exploits:
            self.equipped_exploits.remove(exploit_key)
            return True
        return False
    
    def can_use_exploit(self, exploit_key: str) -> bool:
        """Check if player can use the specified exploit."""
        return exploit_key in self.equipped_exploits and exploit_key in GameData.EXPLOITS
    
    def get_ram_usage(self) -> int:
        """Calculate total RAM usage from equipped exploits."""
        total_ram = 0
        for exploit_key in self.equipped_exploits:
            if exploit_key in GameData.EXPLOITS:
                total_ram += GameData.EXPLOITS[exploit_key].ram
        return total_ram

# ============================================================================
# PLAYER CLASS
# ============================================================================

class Player:
    """Player character with stats, position, and abilities."""
    
    def __init__(self, x: int, y: int):
        # Position and movement
        self.position = Position(x, y)
        self.last_position = Position(x, y)
        
        # Core stats
        self.cpu = 100
        self.max_cpu = 100
        self.heat = 0
        self._max_heat = 100  # Initialize max heat capacity
        self.detection = 0
        self.ram_total = 8
        
        # Vision and abilities
        self.base_vision_range = 15
        
        # Temporary effects
        self.temporary_effects = {
            'data_mimic_turns': 0,
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0
        }
        self.speed_moves_remaining = 0
        
        # Inventory system
        self.inventory_manager = InventoryManager(self)
    
    @property
    def x(self) -> int:
        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    @property
    def ram_used(self) -> int:
        return self.inventory_manager.get_ram_usage()
    
    def move(self, dx: int, dy: int, game_map: 'GameMap') -> bool:
        """Move player with boundary and collision checking."""
        self.last_position = Position(self.x, self.y)
        new_position = Position(
            max(0, min(GameConfig.MAP_WIDTH - 1, self.x + dx)),
            max(0, min(GameConfig.MAP_HEIGHT - 1, self.y + dy))
        )
        
        if game_map.is_valid_position(new_position):
            self.position = new_position
            return True
        return False
    
    def update_effects(self) -> None:
        """Update temporary effects each turn."""
        for effect in self.temporary_effects:
            self.temporary_effects[effect] = max(0, self.temporary_effects[effect] - 1)
    
    def is_invisible(self) -> bool:
        """Check if player is effectively invisible."""
        return self.temporary_effects['data_mimic_turns'] > 0
    
    def get_vision_range(self) -> int:
        """Get current vision range including bonuses."""
        base_range = self.base_vision_range
        if self.temporary_effects['enhanced_vision_turns'] > 0:
            base_range += 5
        return base_range
    
    def can_see_through_walls(self) -> bool:
        """Check if player can see through walls."""
        return self.temporary_effects['enhanced_vision_turns'] > 0
    
    def can_see_enemy(self, enemy: 'Enemy', game_map: 'GameMap') -> bool:
        """Check if player can see enemy, considering shadow mechanics."""
        distance = self.position.distance_to(enemy.position)
        
        # Check basic vision range
        if distance > self.get_vision_range():
            return False
        
        # Check for stealth mechanics
        player_in_shadow = game_map.is_shadow(self.position)
        enemy_in_shadow = game_map.is_shadow(enemy.position)
        
        # If enemy is in shadow, only visible if player is directly adjacent (distance <= 1)
        if enemy_in_shadow and distance > 1:
            return False
        
        # If player is in shadow, they can't see as far (but can still see adjacent)
        if player_in_shadow and distance > 1:
            # Reduce vision range when in shadows
            if distance > max(1, self.get_vision_range() // 2):
                return False
        
        # Check line of sight (enhanced vision can see through walls)
        return (self.can_see_through_walls() or 
                game_map.has_line_of_sight(self.position, enemy.position))
    
    
    @property
    def max_heat(self) -> int:
        """Get maximum heat capacity."""
        return getattr(self, '_max_heat', 100)  # Default 100 if not set
    
    @max_heat.setter  
    def max_heat(self, value: int):
        """Set maximum heat capacity."""
        self._max_heat = value
    
    def apply_permanent_upgrade(self, upgrade_key: str) -> bool:
        """Apply a permanent upgrade to the player."""
        if upgrade_key not in GameUpgrades.UPGRADES:
            return False
            
        upgrade = GameUpgrades.UPGRADES[upgrade_key]
        
        if upgrade.stat_type == 'ram':
            self.ram_total = min(20, self.ram_total + upgrade.bonus_amount)  # Cap at 20
        elif upgrade.stat_type == 'cpu':
            self.max_cpu = min(200, self.max_cpu + upgrade.bonus_amount)  # Cap at 200
            self.cpu = min(self.max_cpu, self.cpu + upgrade.bonus_amount)  # Boost current as well but cap at max
        elif upgrade.stat_type == 'heat':
            self.max_heat = min(200, self.max_heat + upgrade.bonus_amount)  # Cap at 200
            
        return True
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage taken."""
        actual_damage = min(damage, self.cpu)
        self.cpu -= actual_damage
        return actual_damage

# ============================================================================
# ENEMY SYSTEM
# ============================================================================

class Enemy:
    """Enemy character with AI behavior."""
    
    _next_id = 1  # Class variable for unique IDs
    
    def __init__(self, position: Position, enemy_type: str):
        self.id = Enemy._next_id
        Enemy._next_id += 1
        
        self.position = position
        self.type = enemy_type
        self.type_data = GameData.ENEMY_TYPES[enemy_type]
        
        # Stats
        self.cpu = self.type_data.cpu
        self.max_cpu = self.type_data.cpu
        
        # AI state
        self.state = EnemyState.UNAWARE
        self.alert_timer = 0
        self.disabled_turns = 0
        self.move_cooldown = 0
        
        # Movement data
        self.patrol_points: List[Position] = []
        self.patrol_index = 0
        self.last_seen_player: Optional[Position] = None
        self.random_move_queue: List[Tuple[int, int]] = []
    
    @property
    def x(self) -> int:

        return self.position.x
    
    @x.setter
    def x(self, value: int):
        self.position.x = value
    
    @property
    def y(self) -> int:
        return self.position.y
    
    @y.setter
    def y(self, value: int):
        self.position.y = value
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get the color for rendering this enemy."""
        if self.disabled_turns > 0:
            return Colors.BLUE
        elif self.state == EnemyState.UNAWARE:
            return Colors.ENEMY_UNAWARE
        elif self.state == EnemyState.ALERT:
            return Colors.ENEMY_ALERT
        else:
            return Colors.ENEMY_HOSTILE
    
    def can_see_player(self, player: Player, game_map: 'GameMap') -> bool:
        """Check if enemy can see player."""
        if self.disabled_turns > 0:
            return False
        
        distance = self.position.distance_to(player.position)
        if distance > self.type_data.vision:
            return False

        # Check if player is invisible (data mimic effect)
        if player.is_invisible():
            return False
        
        # Check for stealth mechanics
        player_in_shadow = game_map.is_shadow(player.position)
        enemy_in_shadow = game_map.is_shadow(self.position)
        
        # If player is in shadow, only visible if enemy is directly adjacent (distance <= 1)
        if player_in_shadow and distance > 1:
            return False
        
        # If enemy is in shadow, it can't see as far (but can still see adjacent)
        if enemy_in_shadow and distance > 1:
            # Reduce vision range when in shadows
            if distance > max(1, self.type_data.vision // 2):
                return False

        return game_map.has_line_of_sight(self.position, player.position)
    
    def can_attack_player(self, player: Player) -> bool:
        """Check if enemy can attack player (adjacent including diagonally)."""
        # Can't attack if no damage or disabled
        if self.type_data.damage <= 0 or self.disabled_turns > 0:
            return False
            
        dx = abs(self.position.x - player.position.x)
        dy = abs(self.position.y - player.position.y)
        # Adjacent in any direction (including diagonal)
        is_adjacent = dx <= 1 and dy <= 1 and (dx + dy) > 0
        return is_adjacent
    
    def attack_player(self, player: Player) -> int:
        """Attack the player and return damage dealt."""
        return player.take_damage(self.type_data.damage)
    
    def take_damage(self, damage: int) -> bool:
        """Take damage and return True if destroyed."""
        # Admin avatar has 50% damage resistance
        if self.type == 'admin':
            damage = max(5, damage // 2)  # Minimum 5 damage to prevent immunity
        
        self.cpu -= damage
        return self.cpu <= 0
    
    def move(self, game_map: 'GameMap', player: Player, game: 'Game' = None) -> bool:
        """Move enemy based on its AI behavior. Returns True if enemy actually moved."""
        if self.disabled_turns > 0:
            self.disabled_turns -= 1
            return False
        
        # Movement cooldown system
        self.move_cooldown -= 1
        if self.move_cooldown > 0:
            return False
        
        self._reset_movement_cooldown()
        
        if self.type_data.movement == EnemyMovement.STATIC:
            return False
        elif self.type_data.movement == EnemyMovement.RANDOM:
            return self._move_random(game_map, player, game)
        elif self.type_data.movement == EnemyMovement.LINEAR and self.patrol_points:
            return self._move_patrol(game_map, player, game)
        elif self.type_data.movement == EnemyMovement.SEEK:
            if self.state == EnemyState.HOSTILE and self.last_seen_player:
                return self._move_toward(self.last_seen_player, game_map, player, game)
            elif self.state == EnemyState.ALERT and self.last_seen_player:
                return self._move_toward(self.last_seen_player, game_map, player, game)
        elif self.type_data.movement == EnemyMovement.TRACK:
            if self.state == EnemyState.HOSTILE:
                return self._move_toward(player.position, game_map, player, game)
        
        return False
    
    def _reset_movement_cooldown(self):
        """Reset movement cooldown based on enemy type."""
        if self.type_data.movement == EnemyMovement.STATIC:
            self.move_cooldown = 999  # Static enemies never move
        else:
            self.move_cooldown = 1  # All moving enemies move every turn
    
    def _ensure_random_move_queue(self):
        """Ensure the random move queue has at least 3 moves."""
        directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        
        while len(self.random_move_queue) < 3:
            self.random_move_queue.append(random.choice(directions))
    
    def _move_random(self, game_map: 'GameMap', player: Player, game: 'Game' = None) -> bool:
        """Execute random movement pattern with move queue. Returns True if moved."""
        if self.state == EnemyState.HOSTILE:
            return self._move_toward(player.position, game_map, player, game)
        elif self.state == EnemyState.ALERT and self.last_seen_player:
            return self._move_toward(self.last_seen_player, game_map, player, game)
        
        # Ensure we have moves queued
        self._ensure_random_move_queue()
        
        # Execute the next queued move
        if self.random_move_queue:
            dx, dy = self.random_move_queue.pop(0)
            new_position = Position(self.x + dx, self.y + dy)
            if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                game_map.is_valid_position(new_position) and
                not new_position.distance_to(player.position) == 0 and
                (game is None or not game._get_enemy_at(new_position))):
                self.position = new_position
                return True
        
        return False
    
    def _move_patrol(self, game_map: 'GameMap', player: Player, game: 'Game' = None) -> bool:
        """Execute patrol movement pattern. Returns True if moved."""
        if self.state == EnemyState.HOSTILE:
            return self._move_toward(player.position, game_map, player, game)
        elif self.state == EnemyState.ALERT and self.last_seen_player:
            return self._move_toward(self.last_seen_player, game_map, player, game)
        
        if not self.patrol_points:
            return False
        
        target = self.patrol_points[self.patrol_index]
        
        # Check if we're at the current patrol point
        if self.position.distance_to(target) <= 1:
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.patrol_index]
        
        # Try to move toward current target
        moved = self._move_toward(target, game_map, player, game)
        
        # If we can't move toward the target, try advancing to next patrol point
        # This prevents getting stuck on one patrol point
        if not moved and self.position.distance_to(target) > 2:
            # Skip to next patrol point if we're stuck
            self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
            target = self.patrol_points[self.patrol_index]
            moved = self._move_toward(target, game_map, player, game)
        
        return moved

    
    def _move_toward(self, target: Position, game_map: 'GameMap', player: Player, game: 'Game' = None) -> bool:
        """Move one step toward target position. Returns True if moved."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            return False
        
        # Don't move if already adjacent to target (can attack instead)
        current_distance = self.position.distance_to(target)
        if current_distance <= 1.5:  # Adjacent (including diagonally)
            return False
        
        original_position = self.position
        dx = 0 if self.x == target.x else (1 if target.x > self.x else -1)
        dy = 0 if self.y == target.y else (1 if target.y > self.y else -1)
        
        # Try different movement directions in order of preference
        move_attempts = [
            (dx, dy), (dx, 0), (0, dy), (dx, -dy), (-dx, dy),
            (-dx, 0), (0, -dy), (-dx, -dy)
        ]
        
        # First pass: try to move without occupying other enemy positions
        for try_dx, try_dy in move_attempts:
            if try_dx == 0 and try_dy == 0:
                continue
            
            new_position = Position(self.x + try_dx, self.y + try_dy)
            if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                game_map.is_valid_position(new_position) and
                not new_position.distance_to(player.position) == 0 and
                (game is None or not game._get_enemy_at(new_position))):
                self.position = new_position
                return True
        
        # Second pass: if blocked by enemies, try to swap positions or push
        if game is not None:
            for try_dx, try_dy in move_attempts[:4]:  # Only try main directions for swapping
                if try_dx == 0 and try_dy == 0:
                    continue
                
                new_position = Position(self.x + try_dx, self.y + try_dy)
                if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                    game_map.is_valid_position(new_position) and
                    not new_position.distance_to(player.position) == 0):
                    
                    # Check if there's an enemy at the target position
                    blocking_enemy = game._get_enemy_at(new_position)
                    if blocking_enemy and blocking_enemy != self:
                        # Try to swap positions if the other enemy can move to our position
                        if (game_map.is_valid_position(self.position) and 
                            blocking_enemy.type_data.movement != EnemyMovement.STATIC):
                            # Simple position swap
                            blocking_enemy.position = self.position
                            self.position = new_position
                            return True
        
        return False

# ============================================================================
# GAME MAP
# ============================================================================

class GameMap:
    """Game world map with terrain and features."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        
        # Terrain sets
        self.walls: Set[Tuple[int, int]] = set()
        self.shadows: Set[Tuple[int, int]] = set()
        
        # Feature sets
        self.cooling_nodes: Set[Tuple[int, int]] = set()
        self.cpu_recovery_nodes: Set[Tuple[int, int]] = set()
        
        # Items
        self.data_patches: Dict[Tuple[int, int], DataPatch] = {}
        self.exploit_pickups: Dict[Tuple[int, int], ExploitItem] = {}
        self.permanent_upgrades: Dict[Tuple[int, int], str] = {}  # position -> upgrade_key
        self.story_fragments: Dict[Tuple[int, int], StoryFragment] = {}  # position -> story_fragment
        
        # Special locations
        self.gateway: Optional[Position] = None
        
        # Memory system for hybrid fog of war
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.last_known_enemy_positions: Dict[int, Tuple[Position, int]] = {}  # enemy_id -> (position, turn_seen)
    
    def is_wall(self, position: Position) -> bool:
        """Check if position contains a wall."""
        if not position.is_valid(self.width, self.height):
            return True
        return (position.x, position.y) in self.walls
    
    def is_shadow(self, position: Position) -> bool:
        """Check if position is in shadow."""
        if not position.is_valid(self.width, self.height):
            return False
        return (position.x, position.y) in self.shadows
    
    def is_cooling_node(self, position: Position) -> bool:
        """Check if position contains a cooling node."""
        return (position.x, position.y) in self.cooling_nodes
    
    def is_cpu_recovery_node(self, position: Position) -> bool:
        """Check if position contains a CPU recovery node."""
        return (position.x, position.y) in self.cpu_recovery_nodes
    
    def get_data_patch(self, position: Position) -> Optional[DataPatch]:
        """Get data patch at position."""
        return self.data_patches.get((position.x, position.y))
    
    def get_exploit_pickup(self, position: Position) -> Optional[ExploitItem]:
        """Get exploit pickup at position."""
        return self.exploit_pickups.get((position.x, position.y))
    
    def is_valid_position(self, position: Position) -> bool:
        """Check if position is valid for movement."""
        return (position.is_valid(self.width, self.height) and 
                not self.is_wall(position))
    
    def has_line_of_sight(self, start: Position, end: Position) -> bool:
        """Check line of sight between two positions using Bresenham's algorithm."""
        if not (start.is_valid(self.width, self.height) and 
                end.is_valid(self.width, self.height)):
            return False
        
        dx = abs(end.x - start.x)
        dy = abs(end.y - start.y)
        sx = 1 if start.x < end.x else -1
        sy = 1 if start.y < end.y else -1
        err = dx - dy
        
        x, y = start.x, start.y
        max_steps = dx + dy + 1  # Safety counter to prevent infinite loops
        steps = 0
        
        while steps < max_steps:
            if x == end.x and y == end.y:
                return True
            if self.is_wall(Position(x, y)):
                return False
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
            
            steps += 1
        
        return False  # Safety fallback if max steps exceeded

# ============================================================================
# MESSAGE LOG SYSTEM
# ============================================================================

class MessageLog:
    """Manages game messages and logging."""
    
    def __init__(self, max_messages: int = 100):
        self.messages: List[Tuple[str, Tuple[int, int, int]]] = []
        self.max_messages = max_messages
    
    def add_message(self, text: str, color: Optional[Tuple[int, int, int]] = None):
        """Add a message to the log."""
        if not text:
            return
        
        if color is None:
            color = self._determine_message_color(text)
        
        self.messages.append((text, color))
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def _determine_message_color(self, text: str) -> Tuple[int, int, int]:
        """Determine appropriate color for message based on content."""
        text_lower = text.lower()
        text_upper = text.upper()
        
        if ("ADMIN" in text_upper or "CRITICAL" in text_upper or 
            "eliminated" in text_lower):
            return Colors.RED
        elif ("detected" in text_lower or "investigating" in text_lower or 
              "attracted" in text_lower or "attacks" in text_lower):
            return Colors.YELLOW
        elif ("activated" in text_lower or "restored" in text_lower or 
              "reduced" in text_lower or "active" in text_lower):
            return Colors.CYAN
        else:
            return Colors.GREEN
    
    def get_recent_messages(self, count: int) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Get the most recent messages."""
        return self.messages[-count:] if len(self.messages) > count else self.messages

# ============================================================================
# GAME SYSTEMS - EXTRACTED FROM MONOLITHIC GAME CLASS
# ============================================================================

class GameStateManager:
    """Manages core game state like level, turn, and game status."""
    
    def __init__(self):
        self.level: int = 1
        self.turn: int = 0
        self.game_over: bool = False
        self.admin_spawned: bool = False
        self.dungeon_seed: int = random.randint(1, GameConfig.DUNGEON_SEED_RANGE)
        
        # Game effects
        self.network_scan_turns: int = 0
        self.noise_locations: List[Position] = []
        self.distraction_points: Dict[Position, int] = {}
    
    def advance_turn(self) -> None:
        """Advance to the next turn."""
        self.turn += 1
        
        # Update network scan effect
        if self.network_scan_turns > 0:
            self.network_scan_turns -= 1
            
        # Decay distraction points
        expired_distractions = []
        for position, turns_remaining in self.distraction_points.items():
            if turns_remaining <= 1:
                expired_distractions.append(position)
            else:
                self.distraction_points[position] = turns_remaining - 1
                
        for position in expired_distractions:
            del self.distraction_points[position]
    
    def get_current_network_config(self) -> Dict[str, Any]:
        """Get configuration for the current network level."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        return network_configs.get(self.level, network_configs[1])
    
    def should_spawn_admin(self, detection_level: float) -> bool:
        """Determine if admin should spawn based on detection level."""
        if self.admin_spawned:
            return False
            
        return detection_level >= GameConfig.MAX_DETECTION


class EnemyManager:
    """Manages enemy spawning, AI coordination, and state updates."""
    
    def __init__(self, game_map: 'GameMap', message_log: MessageLog):
        self.enemies: List[Enemy] = []
        self.game_map = game_map
        self.message_log = message_log
    
    def spawn_enemy(self, position: Position, enemy_type: str) -> Enemy:
        """Spawn a new enemy at the specified position."""
        enemy = Enemy(position, enemy_type)
        
        # Set up patrol route for patrol enemies
        if enemy.type == 'patrol':
            enemy.patrol_points = self._generate_patrol_route(position)
            
        self.enemies.append(enemy)
        return enemy
    
    def update_all_enemies(self, player: Player, game_state: GameStateManager, game: 'Game') -> None:
        """Update AI and movement for all enemies."""
        for enemy in self.enemies[:]:  # Use slice copy for safe iteration
            if enemy.disabled_turns > 0:
                continue
                
            # Update enemy state based on player visibility
            if enemy.can_see_player(player, self.game_map):
                if enemy.state == EnemyState.UNAWARE:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 5
                    self.message_log.add_message(f"{enemy.type_data.name} detected movement!")
                elif enemy.state == EnemyState.ALERT:
                    enemy.state = EnemyState.HOSTILE
                    self.message_log.add_message(f"{enemy.type_data.name} is now hostile!")
                
                enemy.last_seen_player = Position(player.x, player.y)
            else:
                # Handle state decay when player not visible
                if enemy.state == EnemyState.HOSTILE and enemy.alert_timer <= 0:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 10
                elif enemy.state == EnemyState.ALERT:
                    enemy.alert_timer -= 1
                    if enemy.alert_timer <= 0:
                        enemy.state = EnemyState.UNAWARE
                        enemy.last_seen_player = None
            
            # Move enemy
            enemy.move(self.game_map, player, game)
    
    def get_enemy_at_position(self, position: Position) -> Optional[Enemy]:
        """Get enemy at the specified position."""
        for enemy in self.enemies:
            if enemy.position.x == position.x and enemy.position.y == position.y:
                return enemy
        return None
    
    def remove_enemy(self, enemy: Enemy) -> None:
        """Remove an enemy from the game."""
        if enemy in self.enemies:
            self.enemies.remove(enemy)
    
    def _generate_patrol_route(self, start: Position) -> List[Position]:
        """Generate larger, more comprehensive patrol routes."""
        route = [start]
        route_length = random.randint(12, 20)  # Even longer, more complex patrols
        current = start
        
        for _ in range(route_length - 1):
            attempts = 0
            while attempts < 50:  # More attempts for complex routes
                attempts += 1
                step_size = random.randint(4, 10)  # Even larger steps for maximum coverage
                direction = random.choice([(0, -step_size), (step_size, 0), 
                                         (0, step_size), (-step_size, 0),
                                         # Add diagonal movements for more coverage
                                         (step_size, -step_size), (step_size, step_size),
                                         (-step_size, -step_size), (-step_size, step_size)])
                new_pos = Position(current.x + direction[0], current.y + direction[1])
                
                if (new_pos.is_valid(GameConfig.MAP_WIDTH - 3, GameConfig.MAP_HEIGHT - 3) and
                    new_pos.x >= 3 and new_pos.y >= 3 and
                    self.game_map.is_valid_position(new_pos)):
                    route.append(new_pos)
                    current = new_pos
                    break
        
        # Ensure minimum route length
        if len(route) < 3:
            if start.x < GameConfig.MAP_WIDTH - 5:
                route.append(Position(start.x + 3, start.y))
            if start.y < GameConfig.MAP_HEIGHT - 5:
                route.append(Position(start.x, start.y + 3))
        
        return route


class LevelGenerator:
    """Handles procedural level generation and room placement."""
    
    def __init__(self, game_map: GameMap):
        self.game_map = game_map
    
    def generate_level(self, level: int, seed: int) -> None:
        """Generate a complete level with rooms, corridors, and special tiles."""
        random.seed(seed + level)
        
        # Clear existing level data
        self._clear_level_data()
        
        # Generate the level structure
        self._generate_procedural_level(level)
        
        # Place special tiles and items
        self._place_special_tiles(level)
        self._place_gateway()
    
    def _clear_level_data(self) -> None:
        """Clear all existing level data."""
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.data_patches.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        self.game_map.explored_tiles.clear()
        self.game_map.last_known_enemy_positions.clear()
    
    def _generate_procedural_level(self, level: int) -> None:
        """Generate the basic level structure using improved algorithm from dungeon-gen-v3.py"""
        # Fill map with walls initially
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game_map.walls.add((x, y))
        
        # Create rooms with varied sizes (inspired by dungeon-gen-v3.py)
        rooms = self._create_varied_rooms(level)
        
        # Connect rooms using MST approach for better connectivity
        self._connect_rooms_mst(rooms)
        
        # Add extra paths for multiple routes (good for stealth)
        self._add_extra_paths(rooms)
        
        # Add strategic cover elements in open areas
        self._add_cover_elements_new()
        
        # Add shadow areas for stealth gameplay
        self._place_shadow_areas(level, rooms)
        
        # Ensure border walls are intact
        self._ensure_border_walls_new()
        
        # Store final room list
        self.last_generated_rooms = rooms
    
    def _create_varied_rooms(self, level: int) -> List[Tuple[int, int, int, int]]:
        """Create varied rooms including a guaranteed spawn room in top-left corner."""
        rooms = []
        
        # First, create the spawn room in the top-left corner (always safe and empty)
        spawn_room = (2, 2, 8, 8)  # Position (2,2) with size 8x8 for a safe spawn area
        rooms.append(spawn_room)
        self._carve_room(spawn_room)
        
        # Generate remaining rooms using the existing logic
        remaining_rooms = self._generate_rooms_avoiding_existing(level, [spawn_room])
        rooms.extend(remaining_rooms)
        
        return rooms
    
    def _carve_room(self, room: Tuple[int, int, int, int]) -> None:
        """Carve out a room by removing walls in the specified area."""
        x, y, width, height = room
        for rx in range(x, x + width):
            for ry in range(y, y + height):
                if (rx, ry) in self.game_map.walls:
                    self.game_map.walls.remove((rx, ry))
    
    def _generate_rooms_avoiding_existing(self, level: int, existing_rooms: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Generate room layouts for the level."""
        num_rooms = RoomGenerationConfig.MIN_ROOMS_BASE + level * RoomGenerationConfig.ROOM_LEVEL_MULTIPLIER
        max_rooms = min(num_rooms, RoomGenerationConfig.MAX_ROOMS)
        max_attempts = RoomGenerationConfig.MAX_PLACEMENT_ATTEMPTS
        
        new_rooms = []
        all_rooms = existing_rooms.copy()  # Include existing rooms for overlap checking
        
        for _ in range(max_attempts):
            if len(new_rooms) >= max_rooms:
                break
                
            # Generate random room, avoiding top-left spawn area
            room_width = random.randint(RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE)
            room_height = random.randint(RoomGenerationConfig.MIN_ROOM_SIZE, RoomGenerationConfig.MAX_ROOM_SIZE)
            room_x = random.randint(12, GameConfig.MAP_WIDTH - room_width - 2)  # Start at 12 to avoid spawn area
            room_y = random.randint(12, GameConfig.MAP_HEIGHT - room_height - 2)
            
            new_room = (room_x, room_y, room_width, room_height)
            
            # Check if room overlaps with any existing rooms
            if not self._room_overlaps(new_room, all_rooms):
                new_rooms.append(new_room)
                all_rooms.append(new_room)  # Add to tracking list
                self._carve_room(new_room)
        
        return new_rooms
    
    def _generate_spawn_room(self) -> Tuple[int, int, int, int]:
        """Generate a varied spawn room in the top-left area."""
        # Randomize spawn room size and position within safe area
        room_width = random.randint(6, 10)  # Varied width
        room_height = random.randint(6, 10)  # Varied height
        room_x = random.randint(1, 4)  # Small variation in x position
        room_y = random.randint(1, 4)  # Small variation in y position
        
        # Ensure room doesn't go too far (stay in top-left)
        max_x = min(room_x, 10 - room_width)
        max_y = min(room_y, 10 - room_height)
        
        return (max_x, max_y, room_width, room_height)
    
    def _room_overlaps(self, new_room: Tuple[int, int, int, int], existing_rooms: List[Tuple[int, int, int, int]]) -> bool:
        """Check if a new room overlaps with existing rooms."""
        x1, y1, w1, h1 = new_room
        
        for x2, y2, w2, h2 in existing_rooms:
            if (x1 < x2 + w2 + RoomGenerationConfig.ROOM_PADDING and 
                x1 + w1 + RoomGenerationConfig.ROOM_PADDING > x2 and
                y1 < y2 + h2 + RoomGenerationConfig.ROOM_PADDING and
                y1 + h1 + RoomGenerationConfig.ROOM_PADDING > y2):
                return True
        return False
    
    
    def _connect_rooms_with_corridors(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Connect all rooms with corridors using a minimum spanning tree approach."""
        if len(rooms) < 2:
            return
            
        # Connect each room to the next one
        for i in range(len(rooms) - 1):
            self._connect_two_rooms(rooms[i], rooms[i + 1])
        
        # Add some additional connections for more interesting layouts
        for i in range(0, len(rooms), 3):
            if i + 2 < len(rooms):
                self._connect_two_rooms(rooms[i], rooms[i + 2])
    
    def _connect_two_rooms(self, room1: Tuple[int, int, int, int], room2: Tuple[int, int, int, int]) -> None:
        """Connect two rooms with an L-shaped corridor."""
        x1, y1, w1, h1 = room1
        x2, y2, w2, h2 = room2
        
        # Get room centers
        center1_x, center1_y = x1 + w1 // 2, y1 + h1 // 2
        center2_x, center2_y = x2 + w2 // 2, y2 + h2 // 2
        
        # Create L-shaped corridor
        if random.choice([True, False]):
            # Horizontal first, then vertical
            self._carve_corridor(center1_x, center1_y, center2_x, center1_y)
            self._carve_corridor(center2_x, center1_y, center2_x, center2_y)
        else:
            # Vertical first, then horizontal  
            self._carve_corridor(center1_x, center1_y, center1_x, center2_y)
            self._carve_corridor(center1_x, center2_y, center2_x, center2_y)
    
    def _carve_corridor(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Carve a corridor between two points."""
        if x1 == x2:  # Vertical corridor
            for y in range(min(y1, y2), max(y1, y2) + 1):
                if (x1, y) in self.game_map.walls:
                    self.game_map.walls.remove((x1, y))
        else:  # Horizontal corridor
            for x in range(min(x1, x2), max(x1, x2) + 1):
                if (x, y1) in self.game_map.walls:
                    self.game_map.walls.remove((x, y1))
    
    def _place_shadow_areas(self, level: int, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Place shadow areas for stealth gameplay."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        config = network_configs.get(level, network_configs[1])
        shadow_coverage = config['shadow_coverage']
        
        total_floor_tiles = sum(w * h for x, y, w, h in rooms)
        target_shadow_tiles = int(total_floor_tiles * shadow_coverage)
        
        placed_shadows = 0
        for room in rooms:
            if placed_shadows >= target_shadow_tiles:
                break
                
            x, y, width, height = room
            shadows_in_room = min(target_shadow_tiles - placed_shadows, width * height // 3)
            
            for _ in range(shadows_in_room):
                shadow_x = random.randint(x, x + width - 1)
                shadow_y = random.randint(y, y + height - 1)
                
                if (shadow_x, shadow_y) not in self.game_map.walls:
                    self.game_map.shadows.add((shadow_x, shadow_y))
                    placed_shadows += 1
    
    def _place_special_tiles(self, level: int) -> None:
        """Place cooling nodes, CPU recovery nodes, and other special tiles."""
        floor_positions = self._get_all_floor_positions()
        
        if not floor_positions:
            return
        
        # Place cooling nodes
        for _ in range(RoomGenerationConfig.COOLING_NODES_PER_LEVEL):
            if floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cooling_nodes.add(pos)
        
        # Place CPU recovery nodes  
        for _ in range(RoomGenerationConfig.CPU_NODES_PER_LEVEL):
            if floor_positions:
                pos = random.choice(floor_positions)
                floor_positions.remove(pos)
                self.game_map.cpu_recovery_nodes.add(pos)
    
    def _place_gateway(self) -> None:
        """Place the exit gateway far from spawn but with some randomness."""
        spawn_area = Position(5, 5)  # Center of spawn area
        floor_positions = self._get_all_floor_positions()
        
        if not floor_positions:
            return
            
        # Get positions far from spawn (bottom-right quadrant preferred)
        far_positions = []
        medium_positions = []
        
        for pos in floor_positions:
            position = Position(pos[0], pos[1])
            distance = spawn_area.distance_to(position)
            
            # Prefer positions that are far from spawn
            if distance > 30:  # Very far
                far_positions.append(pos)
            elif distance > 20:  # Medium distance
                medium_positions.append(pos)
        
        # Choose gateway position with preference for far positions
        if far_positions:
            gateway_pos = random.choice(far_positions)
        elif medium_positions:
            gateway_pos = random.choice(medium_positions)
        else:
            # Fallback: any position far enough
            valid_positions = [pos for pos in floor_positions 
                             if spawn_area.distance_to(Position(pos[0], pos[1])) > 15]
            gateway_pos = random.choice(valid_positions) if valid_positions else random.choice(floor_positions)
        
        self.game_map.gateway = Position(gateway_pos[0], gateway_pos[1])
    
    def _get_all_floor_positions(self) -> List[Tuple[int, int]]:
        """Get all valid floor positions (not walls)."""
        floor_positions = []
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                if (x, y) not in self.game_map.walls:
                    floor_positions.append((x, y))
        return floor_positions

    def _create_varied_rooms(self, level: int) -> List[Tuple[int, int, int, int]]:
        """Create multiple rooms of varying sizes (improved algorithm)"""
        rooms = []
        num_rooms = random.randint(12, 18)  # More rooms for stealth gameplay
        attempts = 0
        max_attempts = 300
        
        # Ensure spawn room in top-left area
        spawn_room = self._generate_spawn_room()
        rooms.append(spawn_room)
        self._carve_room_tuple(spawn_room)
        
        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            
            # Varied room sizes based on probability
            room_type = random.random()
            if room_type < 0.15:  # 15% extra large
                w = random.randint(10, 14)
                h = random.randint(10, 14)
            elif room_type < 0.40:  # 25% large
                w = random.randint(7, 10)
                h = random.randint(7, 10)
            elif room_type < 0.70:  # 30% medium
                w = random.randint(5, 7)
                h = random.randint(5, 7)
            else:  # 30% small (good for stealth)
                w = random.randint(3, 5)
                h = random.randint(3, 5)
            
            x = random.randint(1, GameConfig.MAP_WIDTH - w - 1)
            y = random.randint(1, GameConfig.MAP_HEIGHT - h - 1)
            
            # Reduced buffer for tighter packing
            if not self._room_overlaps_new(rooms, x-1, y-1, w+1, h+1):
                rooms.append((x, y, w, h))
                self._carve_room_tuple((x, y, w, h))
        
        # Try to fill gaps with smaller rooms
        for _ in range(50):
            w = random.randint(2, 4)
            h = random.randint(2, 4)
            x = random.randint(1, GameConfig.MAP_WIDTH - w - 1)
            y = random.randint(1, GameConfig.MAP_HEIGHT - h - 1)
            
            if not self._room_overlaps_new(rooms, x, y, w, h):
                rooms.append((x, y, w, h))
                self._carve_room_tuple((x, y, w, h))
        
        return rooms
    
    def _room_overlaps_new(self, rooms: List[Tuple[int, int, int, int]], 
                          x: int, y: int, w: int, h: int) -> bool:
        """Check if a room overlaps with existing rooms"""
        for rx, ry, rw, rh in rooms:
            if not (x + w <= rx or x >= rx + rw or y + h <= ry or y >= ry + rh):
                return True
        return False
    
    def _carve_room_tuple(self, room_tuple: Tuple[int, int, int, int]) -> None:
        """Carve out a room using tuple format (x, y, w, h)"""
        x, y, w, h = room_tuple
        for i in range(y, y + h):
            for j in range(x, x + w):
                if 1 <= i < GameConfig.MAP_HEIGHT - 1 and 1 <= j < GameConfig.MAP_WIDTH - 1:
                    self.game_map.walls.discard((j, i))
    
    def _connect_rooms_mst(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Connect rooms with corridors using MST approach for better connectivity"""
        if len(rooms) < 2:
            return
        
        connected = [rooms[0]]
        unconnected = rooms[1:]
        
        while unconnected:
            # Find closest pair between connected and unconnected
            min_dist = float('inf')
            closest_pair = None
            
            for conn_room in connected:
                cx = conn_room[0] + conn_room[2] // 2
                cy = conn_room[1] + conn_room[3] // 2
                
                for i, unconn_room in enumerate(unconnected):
                    ux = unconn_room[0] + unconn_room[2] // 2
                    uy = unconn_room[1] + unconn_room[3] // 2
                    
                    dist = abs(cx - ux) + abs(cy - uy)
                    if dist < min_dist:
                        min_dist = dist
                        closest_pair = (conn_room, unconn_room, i)
            
            if closest_pair:
                room1, room2, idx = closest_pair
                self._create_corridor_new(room1, room2)
                connected.append(room2)
                unconnected.pop(idx)
    
    def _create_corridor_new(self, room1: Tuple[int, int, int, int], 
                            room2: Tuple[int, int, int, int]) -> None:
        """Create an L-shaped corridor between two rooms"""
        # Get center points of rooms
        x1 = room1[0] + room1[2] // 2
        y1 = room1[1] + room1[3] // 2
        x2 = room2[0] + room2[2] // 2
        y2 = room2[1] + room2[3] // 2
        
        # Randomly choose corridor width (1-2 for stealth gameplay)
        corridor_width = 1 if random.random() < 0.7 else 2
        
        # Randomly choose to go horizontal first or vertical first
        if random.random() < 0.5:
            self._carve_h_corridor_new(x1, x2, y1, corridor_width)
            self._carve_v_corridor_new(y1, y2, x2, corridor_width)
        else:
            self._carve_v_corridor_new(y1, y2, x1, corridor_width)
            self._carve_h_corridor_new(x1, x2, y2, corridor_width)
    
    def _carve_h_corridor_new(self, x1: int, x2: int, y: int, width: int) -> None:
        """Carve a horizontal corridor"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(width):
                if (1 <= y + dy < GameConfig.MAP_HEIGHT - 1 and 
                    1 <= x < GameConfig.MAP_WIDTH - 1):
                    self.game_map.walls.discard((x, y + dy))
    
    def _carve_v_corridor_new(self, y1: int, y2: int, x: int, width: int) -> None:
        """Carve a vertical corridor"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(width):
                if (1 <= y < GameConfig.MAP_HEIGHT - 1 and 
                    1 <= x + dx < GameConfig.MAP_WIDTH - 1):
                    self.game_map.walls.discard((x + dx, y))
    
    def _add_extra_paths(self, rooms: List[Tuple[int, int, int, int]]) -> None:
        """Add extra corridors for multiple paths (good for stealth)"""
        if len(rooms) < 3:
            return
        
        # Add more connections for better connectivity
        extra_connections = min(random.randint(3, 6), len(rooms) // 2)
        
        for _ in range(extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice(rooms)
            if room1 != room2:
                self._create_corridor_new(room1, room2)
    
    def _add_cover_elements_new(self) -> None:
        """Add small wall segments in larger open areas for cover"""
        for y in range(3, GameConfig.MAP_HEIGHT - 3, 5):
            for x in range(3, GameConfig.MAP_WIDTH - 3, 5):
                # Check if area is mostly open
                open_count = 0
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        check_x, check_y = x + dx, y + dy
                        if (0 <= check_x < GameConfig.MAP_WIDTH and 
                            0 <= check_y < GameConfig.MAP_HEIGHT and
                            (check_x, check_y) not in self.game_map.walls):
                            open_count += 1
                
                # If area is very open, maybe add a small cover element
                if open_count > 20 and random.random() < 0.3:
                    # Add small L-shaped or straight cover
                    if random.random() < 0.5:
                        # Straight cover
                        if random.random() < 0.5:
                            for dx in range(2):
                                if x + dx < GameConfig.MAP_WIDTH - 1:
                                    self.game_map.walls.add((x + dx, y))
                        else:
                            for dy in range(2):
                                if y + dy < GameConfig.MAP_HEIGHT - 1:
                                    self.game_map.walls.add((x, y + dy))
                    else:
                        # L-shaped cover
                        self.game_map.walls.add((x, y))
                        if random.random() < 0.5:
                            if x + 1 < GameConfig.MAP_WIDTH - 1:
                                self.game_map.walls.add((x + 1, y))
                            if y + 1 < GameConfig.MAP_HEIGHT - 1:
                                self.game_map.walls.add((x, y + 1))
    
    def _ensure_border_walls_new(self) -> None:
        """Ensure all edges are walls"""
        for i in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, i))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, i))
        for j in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((j, 0))
            self.game_map.walls.add((j, GameConfig.MAP_HEIGHT - 1))


class TurnProcessor:
    """Handles turn-based game logic and effects processing."""
    
    def __init__(self, game_state: GameStateManager, message_log: MessageLog):
        self.game_state = game_state
        self.message_log = message_log
    
    def process_turn(self, player: Player) -> None:
        """Process a complete game turn including heat management and effects."""
        self.game_state.advance_turn()
        
        # Process heat reduction
        self._process_heat_management(player)
        
        # Process temporary effects
        self._process_temporary_effects(player)
        
        # Process detection increase
        self._process_detection_increase(player)
    
    def _process_heat_management(self, player: Player) -> None:
        """Handle heat reduction over time."""
        if player.heat > 0:
            heat_reduction = (GameBalance.HEAT_REDUCTION_BOOSTED 
                            if player.temporary_effects['exploit_efficiency_turns'] > 0 
                            else GameBalance.HEAT_REDUCTION_NORMAL)
            
            old_heat = player.heat
            player.heat = max(0, player.heat - heat_reduction)
            
            if old_heat != player.heat:
                self.message_log.add_message(f"System cooling: -{heat_reduction}°C")
    
    def _process_temporary_effects(self, player: Player) -> None:
        """Process and decay temporary effects."""
        effects_to_update = list(player.temporary_effects.keys())
        
        for effect_name in effects_to_update:
            if player.temporary_effects[effect_name] > 0:
                player.temporary_effects[effect_name] -= 1
                
                if player.temporary_effects[effect_name] == 0:
                    if effect_name == 'exploit_efficiency_turns':
                        self.message_log.add_message("Exploit efficiency boost expired")
                    elif effect_name == 'stealth_boost_turns':
                        self.message_log.add_message("Stealth boost expired")
                    elif effect_name == 'data_mimic_turns':
                        self.message_log.add_message("Data Mimic invisibility expired")
    
    def _process_detection_increase(self, player: Player) -> None:
        """Handle periodic detection level increases."""
        if self.game_state.turn % GameBalance.DETECTION_INCREASE_INTERVAL == 0:
            config = self.game_state.get_current_network_config()
            detection_increase = config.get('background_detection', 1) * GameBalance.DETECTION_INCREASE_AMOUNT
            
            old_detection = player.detection
            player.detection = min(100, player.detection + detection_increase)
            
            if player.detection != old_detection:
                self.message_log.add_message(f"Network security tightening: +{detection_increase}% detection")



class Game:
    """Main game class that manages all game state and logic."""
    
    def __init__(self, load_save: bool = False, settings: GameSettings = None):
        # Core game objects
        self.player = Player(5, 5)
        self.game_map = GameMap(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT)
        self.message_log = MessageLog()
        
        # Game systems - dependency injection for better architecture
        self.game_state = GameStateManager()
        self.enemy_manager = EnemyManager(self.game_map, self.message_log)
        self.level_generator = LevelGenerator(self.game_map)
        self.turn_processor = TurnProcessor(self.game_state, self.message_log)
        self.sound_manager = SoundManager(settings)
        
        # UI state
        self.show_patrol_predictions = False
        self.show_inventory = False
        self.show_help = False
        self.show_story_fragment: Optional[int] = None  # Fragment index to display
        self.show_lore_viewer = False  # L key lore viewer
        self.lore_viewer_selection = 0  # Selected lore entry index
        self.lore_viewer_mode = "list"  # "list" or "reading"
        self.inventory_selection = 0
        
        # Targeting system
        self.targeting_mode = False
        self.targeting_exploit: Optional[str] = None
        self.cursor_position = Position(0, 0)
        
        # Data patch system
        self.data_patch_effects: Dict[str, Tuple[str, str]] = {}
        
        # Story fragment system
        self.story_fragment_manager = StoryFragmentManager()
        
        # Initialize game state
        if load_save:
            success = self._load_from_save()
            if not success:
                # Fallback to new game if loading fails
                self._randomize_data_patches()
                self._generate_procedural_level()
        else:
            self._randomize_data_patches()
            self._generate_procedural_level()
    
    # Properties for backward compatibility with existing code
    @property
    def level(self) -> int:
        """Current game level."""
        return self.game_state.level
    
    @level.setter
    def level(self, value: int) -> None:
        """Set current game level."""
        self.game_state.level = value
    
    @property 
    def turn(self) -> int:
        """Current turn number."""
        return self.game_state.turn
    
    @property
    def game_over(self) -> bool:
        """Whether the game is over."""
        return self.game_state.game_over
    
    @game_over.setter
    def game_over(self, value: bool) -> None:
        """Set game over state."""
        self.game_state.game_over = value
    
    @property
    def admin_spawned(self) -> bool:
        """Whether admin has been spawned."""
        return self.game_state.admin_spawned
    
    @admin_spawned.setter
    def admin_spawned(self, value: bool) -> None:
        """Set admin spawned state."""
        self.game_state.admin_spawned = value
    
    @property
    def enemies(self) -> List[Enemy]:
        """List of all enemies."""
        return self.enemy_manager.enemies
    
    def _get_enemy_at(self, position: Position) -> Optional[Enemy]:
        """Get enemy at position - for backward compatibility."""
        return self.enemy_manager.get_enemy_at_position(position)
    
    
    def _load_from_save(self) -> bool:
        """Load game state from save file."""
        save_data = SaveGameManager.load_game()
        if not save_data:
            return False
        
        try:
            self._restore_game_state(save_data)
            self._restore_player_state(save_data["player"])
            self._restore_game_effects(save_data)
            self._restore_ui_state(save_data)
            
            # Generate level layout for map structure
            self.level_generator.generate_level(self.game_state.level, self.game_state.dungeon_seed)
            
            # Restore map items and enemies
            self._restore_map_items(save_data["map_state"])
            self._restore_enemies(save_data["enemies"])
            
            self.message_log.add_message("Game loaded successfully!", Colors.GREEN)
            return True
            
        except Exception as e:
            logging.error(f"Failed to restore game state: {e}")
            return False
    
    def _restore_game_state(self, save_data: Dict[str, Any]) -> None:
        """Restore core game state from save data."""
        self.game_state.level = save_data["level"]
        self.game_state.turn = save_data["turn"]
        self.game_state.game_over = save_data["game_over"]
        self.game_state.admin_spawned = save_data["admin_spawned"]
        self.game_state.dungeon_seed = save_data["dungeon_seed"]
    
    def _restore_player_state(self, player_data: Dict[str, Any]) -> None:
        """Restore player state from save data."""
        # Position
        self.player.x = player_data.get("x", 1)
        self.player.y = player_data.get("y", 1)
        self.player.last_position.x = player_data.get("last_x", self.player.x)
        self.player.last_position.y = player_data.get("last_y", self.player.y)
        
        # Core stats
        self.player.cpu = player_data.get("cpu", 100)
        self.player.max_cpu = player_data.get("max_cpu", 100)
        self.player.heat = player_data.get("heat", 0)
        self.player.max_heat = player_data.get("max_heat", 100)
        self.player.detection = player_data.get("detection", 0)
        self.player.ram_total = player_data.get("ram_total", 8)
        
        # Speed boost state
        self.player.speed_moves_remaining = player_data.get("speed_moves_remaining", 0)
        
        # Temporary effects with defaults
        self.player.temporary_effects = player_data.get("temporary_effects", {
            'speed_boost_turns': 0,
            'enhanced_vision_turns': 0,
            'exploit_efficiency_turns': 0,
            'data_mimic_turns': 0
        })
        
        # Restore inventory with defaults
        self.player.inventory_manager.equipped_exploits = player_data.get("equipped_exploits", [])
        inventory_items = player_data.get("inventory_items", [])
        self.player.inventory_manager.items = self._deserialize_inventory(inventory_items)
    
    def _restore_game_effects(self, save_data: Dict[str, Any]) -> None:
        """Restore game effects and environmental state from save data."""
        self.game_state.network_scan_turns = save_data["network_scan_turns"]
        self.game_state.noise_locations = [Position(loc["x"], loc["y"]) for loc in save_data["noise_locations"]]
        
        # Restore distraction points with error handling
        self.game_state.distraction_points = {}
        for pos_str, turns in save_data["distraction_points"].items():
            try:
                coords = pos_str.split(',')
                if len(coords) == 2:
                    position = Position(int(coords[0]), int(coords[1]))
                    self.game_state.distraction_points[position] = turns
            except (ValueError, IndexError):
                continue  # Skip malformed coordinate data
        
        # Restore data patch effects
        self.data_patch_effects = save_data["data_patch_effects"]
    
    def _restore_ui_state(self, save_data: Dict[str, Any]) -> None:
        """Restore UI state from save data."""
        ui_state = save_data.get("ui_state", {})
        self.show_patrol_predictions = ui_state.get("show_patrol_predictions", False)
    
    def _deserialize_inventory(self, items_data: List[Dict]) -> List:
        """Deserialize inventory items from save data."""
        items = []
        for item_data in items_data:
            if item_data["type"] == "data_patch":
                from RogueSignalProtocol import DataPatch
                item = DataPatch(
                    color=item_data["color"],
                    effect=item_data["effect"],
                    name=item_data["name"],
                    quantity=item_data.get("quantity", 1)
                )
                item.discovered = item_data.get("discovered", False)
                items.append(item)
            elif item_data["type"] == "exploit":
                from RogueSignalProtocol import ExploitItem
                if item_data["exploit_key"] in GameData.EXPLOITS:
                    exploit_def = GameData.EXPLOITS[item_data["exploit_key"]]
                    item = ExploitItem(item_data["exploit_key"], exploit_def)
                    items.append(item)
            elif item_data["type"] == "story_fragment":
                item = StoryFragment(item_data["fragment_index"])
                items.append(item)
        
        return items
    
    def _restore_map_items(self, map_data: Dict) -> None:
        """Restore items on the map from save data."""
        # Clear current items
        self.game_map.data_patches.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        
        # Restore data patches
        for pos_str, patch_data in map_data["data_patches"].items():
            try:
                coords = pos_str.split(',')
                if len(coords) != 2:
                    continue
                x, y = int(coords[0]), int(coords[1])
            except (ValueError, IndexError):
                continue
            patch = DataPatch(
                color=patch_data["color"],
                effect=patch_data["effect"],
                name=patch_data["name"],
                quantity=patch_data["quantity"]
            )
            patch.discovered = patch_data["discovered"]
            self.game_map.data_patches[(x, y)] = patch
        
        # Restore exploit pickups
        for pos_str, exploit_key in map_data["exploit_pickups"].items():
            try:
                coords = pos_str.split(',')
                if len(coords) != 2:
                    continue
                x, y = int(coords[0]), int(coords[1])
            except (ValueError, IndexError):
                continue
            if exploit_key in GameData.EXPLOITS:
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game_map.exploit_pickups[(x, y)] = exploit_item
        
        # Restore permanent upgrades
        for pos_str, upgrade_key in map_data["permanent_upgrades"].items():
            try:
                coords = pos_str.split(',')
                if len(coords) != 2:
                    continue
                x, y = int(coords[0]), int(coords[1])
            except (ValueError, IndexError):
                continue
            self.game_map.permanent_upgrades[(x, y)] = upgrade_key
        
        # Restore story fragments
        for pos_str, fragment_index in map_data["story_fragments"].items():
            try:
                coords = pos_str.split(',')
                if len(coords) != 2:
                    continue
                x, y = int(coords[0]), int(coords[1])
            except (ValueError, IndexError):
                continue
            fragment = StoryFragment(fragment_index)
            self.game_map.story_fragments[(x, y)] = fragment
        
        # Restore explored tiles
        if "explored_tiles" in map_data:
            self.game_map.explored_tiles.clear()
            for tile_str in map_data["explored_tiles"]:
                try:
                    coords = tile_str.split(',')
                    if len(coords) == 2:
                        x, y = int(coords[0]), int(coords[1])
                        self.game_map.explored_tiles.add((x, y))
                except (ValueError, IndexError):
                    continue
        
        # Restore gateway
        if map_data["gateway"]:
            self.game_map.gateway = Position(map_data["gateway"]["x"], map_data["gateway"]["y"])
    
    def _restore_enemies(self, enemies_data: List[Dict]) -> None:
        """Restore enemies from save data."""
        self.enemy_manager.enemies.clear()
        
        for enemy_data in enemies_data:
            position = Position(enemy_data["x"], enemy_data["y"])
            enemy = Enemy(position, enemy_data["type"])
            
            # Restore enemy state
            enemy.cpu = enemy_data["cpu"]
            enemy.state = EnemyState(enemy_data["state"])
            enemy.move_cooldown = enemy_data["move_cooldown"]
            enemy.disabled_turns = enemy_data["disabled_turns"]
            enemy.alert_timer = enemy_data["alert_timer"]
            enemy.patrol_index = enemy_data["patrol_index"]
            
            if enemy_data["last_seen_player"]:
                enemy.last_seen_player = Position(
                    enemy_data["last_seen_player"]["x"],
                    enemy_data["last_seen_player"]["y"]
                )
            
            if "patrol_points" in enemy_data:
                enemy.patrol_points = [
                    Position(point["x"], point["y"]) 
                    for point in enemy_data["patrol_points"]
                ]
            
            self.enemy_manager.enemies.append(enemy)
    
    def auto_save(self) -> None:
        """Auto-save the current game state."""
        if not self.game_over:  # Don't auto-save if game is over
            success = SaveGameManager.save_game(self)
            if success:
                logging.info("Auto-save completed")
            else:
                logging.warning("Auto-save failed")
    
    def _randomize_data_patches(self):
        """Randomize data patch effects for this game session."""
        colors = ['crimson', 'azure', 'emerald', 'golden', 'violet', 'silver']
        effects = [
            ('restore_cpu', f'Restore {GameBalance.CPU_RESTORE_MIN}-{GameBalance.CPU_RESTORE_MAX} CPU'),
            ('reduce_heat', f'Reduce heat by {GameBalance.HEAT_REDUCTION_INSTANT}°C instantly'),
            ('reduce_detection', '-25% detection level'),
            ('speed_boost', 'Temporary speed boost (10 turns)'),
            ('enhanced_vision', 'Enhanced vision (15 turns)'),
            ('exploit_efficiency', 'Exploit efficiency (8 turns)')
        ]
        
        random.shuffle(effects)
        for color, (effect, desc) in zip(colors, effects):
            self.data_patch_effects[color] = (effect, desc)
    
   
    def _clear_map(self):
        """Clear all map data."""
        self.game_map.walls.clear()
        self.game_map.shadows.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.data_patches.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()  # Clear permanent upgrades
        self.game_map.story_fragments.clear()  # Clear story fragments
        self.game_map.explored_tiles.clear()  # Clear memory system
        self.game_map.last_known_enemy_positions.clear()  # Clear enemy memory
        self.enemies.clear()
    
    def _create_border_walls(self):
        """Create walls around the map border."""
        for x in range(GameConfig.MAP_WIDTH):
            self.game_map.walls.add((x, 0))
            self.game_map.walls.add((x, GameConfig.MAP_HEIGHT - 1))
        for y in range(GameConfig.MAP_HEIGHT):
            self.game_map.walls.add((0, y))
            self.game_map.walls.add((GameConfig.MAP_WIDTH - 1, y))
        
    def _find_valid_spawn_position(self) -> Position:
        """Find player spawn position in top-left area."""
        # Try top-left positions in order of preference
        preferred_positions = [
            Position(2, 2), Position(3, 2), Position(4, 2),
            Position(2, 3), Position(3, 3), Position(4, 3),
            Position(2, 4), Position(3, 4), Position(4, 4)
        ]
        
        for pos in preferred_positions:
            if (pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                not self.game_map.is_wall(pos)):
                return pos
        
        # Fallback: force clear a position in top-left
        fallback_pos = Position(3, 3)
        if (fallback_pos.x, fallback_pos.y) in self.game_map.walls:
            self.game_map.walls.remove((fallback_pos.x, fallback_pos.y))
        return fallback_pos

    def _reset_player_state(self, x: int, y: int):
        """Reset player to starting state."""
        self.player.position = Position(x, y)
        self.player.cpu = self.player.max_cpu
        self.player.heat = 0
        self.player.detection = 0
        
        # Clear temporary effects
        for effect in self.player.temporary_effects:
            self.player.temporary_effects[effect] = 0
    
    def process_turn(self):
        """Process one complete game turn using the new system architecture."""
        # Process turn using the dedicated turn processor
        self.turn_processor.process_turn(self.player)
        
        
        # Handle network scan effect
        self._update_network_scan()
        
        # Process special tiles
        self._process_special_tiles()
        
        # Update enemies
        self._update_enemies()
        
        # Update memory system
        self._update_memory_system()
        
        # Check for admin spawn
        self._check_admin_spawn()
        
        # Passive detection increase (higher on higher levels)
        if self.turn % GameBalance.DETECTION_INCREASE_INTERVAL == 0:
            network_configs = GameConfig.NETWORK_CONFIGS()
            config = network_configs.get(self.level, {"background_detection": 1})
            background_increase = config.get("background_detection", 1)
            self.player.detection = min(100, self.player.detection + background_increase)
    
    def _update_network_scan(self):
        """Update network scan effect."""
        if self.game_state.network_scan_turns > 0:
            self.game_state.network_scan_turns -= 1
    
    def _update_memory_system(self):
        """Update the hybrid fog of war memory system."""
        vision_range = self.player.get_vision_range()
        
        # Update explored tiles
        for dx in range(-vision_range, vision_range + 1):
            for dy in range(-vision_range, vision_range + 1):
                if dx*dx + dy*dy <= vision_range*vision_range:
                    x = self.player.x + dx
                    y = self.player.y + dy
                    world_pos = Position(x, y)
                    
                    if (world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                        (self.player.can_see_through_walls() or 
                         self.game_map.has_line_of_sight(self.player.position, world_pos))):
                        self.game_map.explored_tiles.add((x, y))
        
        # Update last known enemy positions
        for enemy in self.enemies:
            if self.player.can_see_enemy(enemy, self.game_map):
                self.game_map.last_known_enemy_positions[enemy.id] = (enemy.position, self.turn)

    def _process_special_tiles(self):
        """Process effects of special tiles at player position."""
        player_pos = (self.player.x, self.player.y)
        
        # Cooling node
        if self.game_map.is_cooling_node(self.player.position):
            old_heat = self.player.heat
            self.player.heat = max(0, self.player.heat - 20)
            if old_heat > self.player.heat:
                self.message_log.add_message(f"Cooling node: -{old_heat - self.player.heat}°C")
        
        # CPU recovery node
        if self.game_map.is_cpu_recovery_node(self.player.position):
            recovery = min(GameBalance.CPU_RECOVERY_AMOUNT, self.player.max_cpu - self.player.cpu)
            self.player.cpu += recovery
            if recovery > 0:
                self.message_log.add_message(f"CPU recovery: +{recovery}")
        
        # Data patch
        if player_pos in self.game_map.data_patches:
            patch = self.game_map.data_patches[player_pos]
            self.sound_manager.play_sound("item_pickup_data")
            self.player.inventory_manager.add_item(patch)
            self.message_log.add_message(f"Found {patch.name}")
            del self.game_map.data_patches[player_pos]
        
        # Exploit pickup
        if player_pos in self.game_map.exploit_pickups:
            exploit_item = self.game_map.exploit_pickups[player_pos]
            self.sound_manager.play_sound("item_pickup_exploit")
            self.player.inventory_manager.add_item(exploit_item)
            self.message_log.add_message(f"Found {exploit_item.name}")
            del self.game_map.exploit_pickups[player_pos]
        
        # Permanent upgrade pickup (auto-equip)
        if player_pos in self.game_map.permanent_upgrades:
            upgrade_key = self.game_map.permanent_upgrades[player_pos]
            if upgrade_key in GameUpgrades.UPGRADES:
                upgrade = GameUpgrades.UPGRADES[upgrade_key]
                if self.player.apply_permanent_upgrade(upgrade_key):
                    self.sound_manager.play_sound("item_pickup_upgrade")
                    self.message_log.add_message(f"Integrated {upgrade.name}!")
                    self.message_log.add_message(upgrade.description)
                    del self.game_map.permanent_upgrades[player_pos]
        
        # Story fragment pickup
        if player_pos in self.game_map.story_fragments:
            story_fragment = self.game_map.story_fragments[player_pos]
            # Discover the fragment and save progress
            if self.story_fragment_manager.discover_fragment(story_fragment.fragment_index):
                self.sound_manager.play_sound("item_pickup_story")
                self.message_log.add_message("Data fragment recovered! Press 'L' to view lore.")
                # Trigger the story fragment display immediately
                self.show_story_fragment = story_fragment.fragment_index
            del self.game_map.story_fragments[player_pos]
    
    def _update_enemies(self):
        """Update all enemy states and actions."""
        self._update_enemy_awareness()
        self._move_enemies()
        self._process_enemy_attacks()
    
    def _update_enemy_awareness(self):
        """Update enemy awareness states."""
        for enemy in self.enemies[:]:
            old_state = enemy.state
            
            # Admin Avatar has perfect tracking - always knows player location
            if enemy.type == 'admin':
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(self.player.x, self.player.y)
                if old_state != EnemyState.HOSTILE:
                    detection_increase = 8
                    self.player.detection = min(100, self.player.detection + detection_increase)
                    self.message_log.add_message(f"{enemy.type_data.name} detected you!")
                else:
                    detection_increase = 2
                    self.player.detection = min(100, self.player.detection + detection_increase)
            elif enemy.can_see_player(self.player, self.game_map):
                self._handle_enemy_sees_player(enemy)
            else:
                self._handle_enemy_loses_player(enemy)
    
    def _handle_enemy_sees_player(self, enemy: Enemy):
        """Handle when enemy sees the player."""
        if enemy.state == EnemyState.UNAWARE:
            enemy.state = EnemyState.ALERT
            enemy.alert_timer = 1
            self.message_log.add_message(f"{enemy.type_data.name} investigating")
            # Alert nearby enemies immediately when first spotted
            self._alert_nearby_enemies(enemy)
        elif enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.HOSTILE
                enemy.last_seen_player = Position(self.player.x, self.player.y)
                detection_increase = 8 if enemy.type == 'admin' else 5  # Reduced from 15/10
                self.player.detection = min(100, self.player.detection + detection_increase)
                self.message_log.add_message(f"{enemy.type_data.name} detected you!")
                # Alert nearby enemies when this enemy becomes hostile
                self._alert_nearby_enemies(enemy)
        elif enemy.state == EnemyState.HOSTILE:
            enemy.last_seen_player = Position(self.player.x, self.player.y)
            detection_increase = 2 if enemy.type == 'admin' else 0.5  # Reduced from 3/1
            self.player.detection = min(100, self.player.detection + detection_increase)
    
    def _handle_enemy_loses_player(self, enemy: Enemy):
        """Handle when enemy loses sight of player."""
        if enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.UNAWARE
                self.message_log.add_message(f"{enemy.type_data.name} lost interest")
        elif enemy.state == EnemyState.HOSTILE:
            if random.random() < 0.15:  # 15% chance per turn
                if enemy.type == 'admin':
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 5
                else:
                    enemy.state = EnemyState.UNAWARE
                    enemy.last_seen_player = None
                    self.message_log.add_message(f"{enemy.type_data.name} lost track")
    
    def _alert_nearby_enemies(self, alerting_enemy: Enemy):
        """Alert nearby enemies when one becomes hostile."""
        alert_range = 8
        alerted_count = 0
        
        for enemy in self.enemies:
            if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
                continue
                
            distance = enemy.position.distance_to(alerting_enemy.position)
            if distance <= alert_range:
                if enemy.state == EnemyState.UNAWARE:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 3
                    enemy.last_seen_player = Position(self.player.x, self.player.y)
                    alerted_count += 1
                elif enemy.state == EnemyState.ALERT:
                    enemy.alert_timer = max(enemy.alert_timer, 3)
                    enemy.last_seen_player = Position(self.player.x, self.player.y)
                    alerted_count += 1
        
        if alerted_count > 0:
            self.message_log.add_message(f"{alerted_count} enemies alerted nearby!")
    
    def _move_enemies(self):
        """Move all enemies according to their AI."""
        for enemy in self.enemies:
            # Only mark as moved if enemy actually moved
            did_move = enemy.move(self.game_map, self.player, self)
            enemy.has_moved_this_turn = did_move
    
    def _process_enemy_attacks(self):
        """Process attacks from enemies adjacent to player."""
        for enemy in self.enemies[:]:
            # Only attack if enemy hasn't moved this turn (move OR attack, not both)
            if enemy.can_attack_player(self.player) and not getattr(enemy, 'has_moved_this_turn', False):
                self.sound_manager.play_sound("enemy_attack")
                damage = enemy.attack_player(self.player)
                self.message_log.add_message(f"{enemy.type_data.name} attacks: {damage} CPU damage")
                if self.player.cpu <= 0:
                    self.sound_manager.play_sound("player_death")
                    self.message_log.add_message("CRITICAL SYSTEM FAILURE!")
                    # Delete save on death (permadeath)
                    SaveGameManager.delete_save()
                    self.message_log.add_message("Save data purged")
        
        # Reset movement flags for next turn
        for enemy in self.enemies:
            enemy.has_moved_this_turn = False
    
    def _check_admin_spawn(self):
        """Check if admin avatar should spawn."""
        if (self.player.detection >= GameConfig.MAX_DETECTION and 
            not self.admin_spawned and 
            not any(e.type == 'admin' for e in self.enemies)):
            self._spawn_admin_avatar()
    
    def _spawn_admin_avatar(self):
        """Spawn the admin avatar enemy."""
        if self.admin_spawned:
            return
        
        spawn_position = self._find_admin_spawn_position()
        if spawn_position:
            admin = Enemy(spawn_position, 'admin')
            admin.state = EnemyState.HOSTILE
            admin.last_seen_player = Position(self.player.x, self.player.y)
            self.enemies.append(admin)
            self.admin_spawned = True
            self.message_log.add_message("*** ADMIN AVATAR SPAWNED! ***")
    
    def _find_admin_spawn_position(self) -> Optional[Position]:
        """Find a suitable spawn position for admin avatar near player and visible."""
        player_vision = self.player.get_vision_range()
        
        # Try to spawn within player's vision range (5-10 tiles away for dramatic effect)
        for _ in range(100):
            # Generate position within player's vision range but not too close
            distance = random.randint(5, min(10, player_vision))
            angle = random.uniform(0, 2 * 3.14159)  # Random angle in radians
            
            x = int(self.player.x + distance * math.cos(angle))
            y = int(self.player.y + distance * math.sin(angle))
            position = Position(x, y)
            
            if (self.game_map.is_valid_position(position) and
                position.distance_to(self.player.position) >= 5 and  # Not too close to player
                position.distance_to(self.player.position) <= player_vision and  # Within sight
                self.game_map.has_line_of_sight(self.player.position, position) and  # Actually visible
                not self._get_enemy_at(position) and
                (x, y) not in self.game_map.data_patches and
                (x, y) not in self.game_map.cooling_nodes and
                (x, y) not in self.game_map.cpu_recovery_nodes):
                return position
        
        # Fallback: try positions just within vision range if ideal spots don't work
        for _ in range(50):
            distance = player_vision - 1  # Just within vision
            angle = random.uniform(0, 2 * 3.14159)
            
            x = int(self.player.x + distance * math.cos(angle))
            y = int(self.player.y + distance * math.sin(angle))
            position = Position(x, y)
            
            if (self.game_map.is_valid_position(position) and
                not self._get_enemy_at(position)):
                return position
        
        # Last resort fallback position
        fallback = Position(GameConfig.MAP_WIDTH - 10, GameConfig.MAP_HEIGHT - 10)
        if self.game_map.is_valid_position(fallback):
            return fallback
        return Position(40, 40)
    
    def move_player(self, dx: int, dy: int):
        """Move player and process the resulting turn."""
        if self.targeting_mode:
            self._move_cursor(dx, dy)
            return
        
        # Handle speed boost: grant 2 moves at start of speed boost turn
        if self.player.temporary_effects['speed_boost_turns'] > 0 and self.player.speed_moves_remaining == 0:
            self.player.speed_moves_remaining = 2
        elif self.player.temporary_effects['speed_boost_turns'] == 0:
            self.player.speed_moves_remaining = 0
        
        # Check for enemy at target position first
        new_position = Position(
            max(0, min(GameConfig.MAP_WIDTH - 1, self.player.x + dx)),
            max(0, min(GameConfig.MAP_HEIGHT - 1, self.player.y + dy))
        )
        
        target_enemy = self._get_enemy_at(new_position)
        if target_enemy:
            # Bump attack the enemy
            self._perform_bump_attack(target_enemy)
        else:
            # Try to move player
            if self.player.move(dx, dy, self.game_map):
                self.sound_manager.play_sound("player_move")
                # Check for gateway
                if (self.game_map.gateway and 
                    self.player.position.distance_to(self.game_map.gateway) == 0):
                    self.sound_manager.play_sound("level_complete")
                    self.message_log.add_message("Gateway reached! Next network...")
                    self.next_level()
                    return
                
                # Check for overheating
                if self.player.heat >= GameConfig.MAX_HEAT:
                    self.sound_manager.play_sound("player_overheat")
                    damage = 5 + (self.player.heat - GameConfig.MAX_HEAT)
                    self.player.take_damage(damage)
                    self.player.heat = 95
                    self.message_log.add_message(f"Overheating! {damage} CPU damage")
                    if self.player.cpu <= 0:
                        self.sound_manager.play_sound("player_death")
                        self.message_log.add_message("CRITICAL SYSTEM FAILURE!")
                        # Delete save on death (permadeath)
                        SaveGameManager.delete_save()
                        self.message_log.add_message("Save data purged")
                        return
            else:
                # Movement blocked
                self.message_log.add_message("Wall blocks movement")
        
        # Handle speed boost and turn processing
        self.maybe_process_turn()

    def maybe_process_turn(self):
        """Process turn only if speed boost doesn't allow another action."""
        # Consume speed move if applicable
        if self.player.speed_moves_remaining > 0:
            self.player.speed_moves_remaining -= 1
        
        # Only process turn if no speed moves remaining
        if self.player.speed_moves_remaining == 0:
            self.process_turn()

    def _perform_bump_attack(self, target_enemy: Enemy):
        """Perform a bump attack on an enemy."""
        # Calculate base damage - rebalanced for new enemy HP values
        base_damage = 30  # Increased from 25 to match average enemy damage
        
        # Stealth bonus: extra damage if attacking from shadows or while invisible
        stealth_bonus = 0
        if self.game_map.is_shadow(self.player.position) or self.player.is_invisible():
            stealth_bonus = 10  # Reduced from 15 to prevent trivial one-shots
            self.sound_manager.play_sound("stealth_attack")
            self.message_log.add_message("Stealth attack!")
        else:
            self.sound_manager.play_sound("player_attack")
        
        # Speed boost bonus
        speed_bonus = 5 if self.player.temporary_effects['speed_boost_turns'] > 0 else 0  # Reduced from 10
        
        total_damage = base_damage + stealth_bonus + speed_bonus
        
        # Log the attack with damage amount
        self.message_log.add_message(f"{target_enemy.type_data.name} damaged")
                
        # Apply damage
        if target_enemy.take_damage(total_damage):
            # Enemy destroyed
            self.sound_manager.play_sound("enemy_death")
            self.enemies.remove(target_enemy)
            self.player.cpu = min(self.player.max_cpu, self.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)  # Small CPU recovery
            self.message_log.add_message(f"Eliminated {target_enemy.type_data.name} (+{GameBalance.ENEMY_ELIMINATION_CPU_REWARD} CPU)")
        else:
            # Enemy damaged but alive - show remaining health
            self.message_log.add_message(f"{target_enemy.type_data.name} health: {target_enemy.cpu}/{target_enemy.max_cpu}")
            # Make enemy hostile and aware of player
            target_enemy.state = EnemyState.HOSTILE
            target_enemy.last_seen_player = Position(self.player.x, self.player.y)
        
        # Generate some heat from the attack
        heat_generated = 8
        if self.player.temporary_effects['exploit_efficiency_turns'] > 0:
            heat_generated = int(heat_generated * 0.7)  # Reduced heat with efficiency
        
        self.player.heat = min(100, self.player.heat + heat_generated)
        
        # Increase detection slightly
        self.player.detection = min(100, self.player.detection + 5)

    def _move_cursor(self, dx: int, dy: int):
        """Move targeting cursor."""
        new_x = max(0, min(GameConfig.MAP_WIDTH - 1, self.cursor_position.x + dx))
        new_y = max(0, min(GameConfig.MAP_HEIGHT - 1, self.cursor_position.y + dy))
        self.cursor_position = Position(new_x, new_y)
    
    def _get_enemy_at(self, position: Position) -> Optional[Enemy]:
        """Get enemy at specified position."""
        for enemy in self.enemies:
            if enemy.position.distance_to(position) == 0:
                return enemy
        return None
    
    def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
        """Get the next N positions this enemy will move to."""
        return self.level_generator.get_enemy_next_positions(enemy, steps)
    
    def next_level(self):
        """Progress to the next level."""
        self.level += 1
        if self.level > 3:
            self.sound_manager.play_music("victory.ogg", loops=1)
            self.message_log.add_message("INFILTRATION COMPLETE!")
            self.message_log.add_message(f"Stats: Turns:{self.turn} Det:{int(self.player.detection)}%")
            self.game_over = True
            # Auto-save on game completion
            self.auto_save()
        else:
            try:
                self._generate_procedural_level()
                # Auto-save after successful level generation
                self.auto_save()
            except Exception as e:
                import traceback
                tb = traceback.extract_tb(e.__traceback__)
                line_no = tb[-1].lineno if tb else "?"
                self.message_log.add_message(f"Network error: {str(e)[:15]} (line {line_no})")
                self.level -= 1

    def _generate_procedural_level(self):
        """Generate a procedural level using the new LevelGenerator system."""
        network_configs = GameConfig.NETWORK_CONFIGS()
        if self.level not in network_configs:
            self.message_log.add_message(f"Invalid level: {self.level}")
            return
        
        config = network_configs[self.level]
        
        try:
            # Play appropriate background music for the level
            if self.level == 1:
                self.sound_manager.play_music("level1_stealth.ogg", fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            elif self.level == 2:
                self.sound_manager.play_music("level2_infiltration.ogg", fade_in_ms=GameConfig.DEFAULT_FADE_TIME) 
            elif self.level == 3:
                self.sound_manager.play_music("level3_core.ogg", fade_in_ms=GameConfig.DEFAULT_FADE_TIME)
            
            # Use the new LevelGenerator system
            self.level_generator.generate_level(self.level, self.game_state.dungeon_seed)
            
            # Generate additional game elements not handled by LevelGenerator
            self._create_border_walls()
            self._place_data_patches()
            self._place_exploit_pickups()
            self._place_story_fragment()  # Add story fragment placement
            self._place_permanent_upgrades()
            self._place_enemies(config["enemies"])
            
            # Reset player position to spawn location and adjust stats for new level
            # Find a valid spawn position (open floor tile)
            spawn_pos = self._find_valid_spawn_position()
            self.player.x = spawn_pos.x
            self.player.y = spawn_pos.y
            
            # Stat changes for level transition:
            # - CPU: Preserved (carries over)
            # - Heat: Preserved (carries over) 
            # - Detection: Reset to 0 (doesn't carry over)
            # - Admin spawned state: Reset (new network, fresh start)
            self.player.detection = 0
            self.admin_spawned = False
            
            self.message_log.add_message(f"{config['name']} loaded")
            self.message_log.add_message(f"{len(self.enemies)} security processes")
            self.message_log.add_message("Network security reset - detection cleared")
            
        finally:
            # Restore random seed
            random.seed()
    
    def _find_valid_spawn_position(self) -> Position:
        """Find a valid spawn position for the player in the top-left spawn room."""
        # Always spawn in the center of the predefined spawn room (2,2,8,8)
        # This corresponds to the spawn room created in _create_varied_rooms
        spawn_room_center_x = 2 + 8 // 2  # 6
        spawn_room_center_y = 2 + 8 // 2  # 6
        
        # Verify the position is valid (should always be since we created the room)
        pos = Position(spawn_room_center_x, spawn_room_center_y)
        if (self.game_map.is_valid_position(pos) and 
            not self.game_map.is_wall(pos) and
            not self._get_enemy_at(pos)):
            return pos
        
        # If center is somehow occupied, try nearby positions in the spawn room
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue  # Already tried center
                test_pos = Position(spawn_room_center_x + dx, spawn_room_center_y + dy)
                if (test_pos.x >= 2 and test_pos.x < 10 and  # Within spawn room bounds
                    test_pos.y >= 2 and test_pos.y < 10 and
                    self.game_map.is_valid_position(test_pos) and 
                    not self.game_map.is_wall(test_pos) and
                    not self._get_enemy_at(test_pos)):
                    return test_pos
        
        # Final fallback (should never be needed)
        return Position(6, 6)
    
    def _generate_shadows(self, coverage: float):
        """Generate strategic shadow areas for better stealth gameplay."""
        # Adjust shadow cluster count based on coverage
        base_clusters = 8 if coverage < 0.25 else 12
        shadow_clusters = random.randint(base_clusters, base_clusters + 4)
        
        # Create larger, more connected shadow areas
        for _ in range(shadow_clusters):
            center_x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            center_y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            
            # Smaller shadow clusters for lower coverage
            cluster_size = random.randint(10, 25) if coverage < 0.25 else random.randint(15, 35)
            
            # Create more organic shadow shapes
            shadow_shape = random.choice(['circular', 'linear', 'L-shaped'])
            
            if shadow_shape == 'circular':
                # Circular shadow area
                radius = random.randint(3, 6)
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        if dx*dx + dy*dy <= radius*radius:
                            x, y = center_x + dx, center_y + dy
                            position = Position(x, y)
                            if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                                not self.game_map.is_wall(position)):
                                self.game_map.shadows.add((x, y))
            
            elif shadow_shape == 'linear':
                # Linear shadow corridor
                if random.random() < 0.5:
                    # Horizontal corridor
                    length = random.randint(8, 15)
                    width = random.randint(2, 4)
                    for dx in range(length):
                        for dy in range(width):
                            x, y = center_x + dx - length//2, center_y + dy - width//2
                            position = Position(x, y)
                            if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                                not self.game_map.is_wall(position)):
                                self.game_map.shadows.add((x, y))
                else:
                    # Vertical corridor
                    length = random.randint(8, 15)
                    width = random.randint(2, 4)
                    for dx in range(width):
                        for dy in range(length):
                            x, y = center_x + dx - width//2, center_y + dy - length//2
                            position = Position(x, y)
                            if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                                not self.game_map.is_wall(position)):
                                self.game_map.shadows.add((x, y))
            
            else:  # L-shaped
                # L-shaped shadow area for complex stealth gameplay
                arm1_length = random.randint(5, 10)
                arm2_length = random.randint(5, 10)
                arm_width = random.randint(2, 3)
                
                # Horizontal arm
                for dx in range(arm1_length):
                    for dy in range(arm_width):
                        x, y = center_x + dx, center_y + dy
                        position = Position(x, y)
                        if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                            not self.game_map.is_wall(position)):
                            self.game_map.shadows.add((x, y))
                
                # Vertical arm
                for dx in range(arm_width):
                    for dy in range(arm2_length):
                        x, y = center_x + dx, center_y + dy
                        position = Position(x, y)
                        if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                            not self.game_map.is_wall(position)):
                            self.game_map.shadows.add((x, y))
        
        # Add some additional scattered shadow spots for tactical hiding (fewer for lower coverage)
        scattered_shadows = random.randint(10, 20) if coverage < 0.25 else random.randint(20, 40)
        for _ in range(scattered_shadows):
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)
            if (position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                not self.game_map.is_wall(position)):
                # Create small 2x2 shadow patches
                for dx in range(2):
                    for dy in range(2):
                        shadow_pos = Position(x + dx, y + dy)
                        if (shadow_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                            not self.game_map.is_wall(shadow_pos)):
                            self.game_map.shadows.add((x + dx, y + dy))
    
    def _place_special_nodes(self):
        """Place cooling and CPU recovery nodes."""
        node_count = 8 + self.level * 2  # More nodes for better gameplay (was 4 + level)
        placed_nodes = 0
        attempts = 0
        
        while placed_nodes < node_count and attempts < 100:
            attempts += 1
            x = random.randint(5, GameConfig.MAP_WIDTH - 5)
            y = random.randint(5, GameConfig.MAP_HEIGHT - 5)
            position = Position(x, y)
            
            if self._is_valid_special_placement(position):
                if random.choice([True, False]):
                    self.game_map.cooling_nodes.add((x, y))
                else:
                    self.game_map.cpu_recovery_nodes.add((x, y))
                placed_nodes += 1
    
    def _place_data_patches(self):
        """Place data patches throughout the level."""
        patch_count = 12 + self.level * 4  # Much more data patches (was 6 + level * 2)
        placed_patches = 0
        attempts = 0
        
        while placed_patches < patch_count and attempts < 150:
            attempts += 1
            x = random.randint(3, GameConfig.MAP_WIDTH - 3)
            y = random.randint(3, GameConfig.MAP_HEIGHT - 3)
            position = Position(x, y)
            
            if self._is_valid_patch_placement(position):
                color = random.choice(list(self.data_patch_effects.keys()))
                effect, desc = self.data_patch_effects[color]
                patch = DataPatch(color, effect, f"{color.title()} Data Patch", desc)
                self.game_map.data_patches[(x, y)] = patch
                placed_patches += 1
    
    def _place_exploit_pickups(self):
        """Place random exploit pickups throughout the level."""
        exploit_count = 5 + self.level * 2  # Much more exploits (was 2 + max(0, level - 1))
        placed_exploits = 0
        attempts = 0
        
        # Get list of available exploits (excluding ones player starts with)
        available_exploits = list(GameData.EXPLOITS.keys())
        
        while placed_exploits < exploit_count and attempts < 100:
            attempts += 1
            x = random.randint(5, GameConfig.MAP_WIDTH - 5)
            y = random.randint(5, GameConfig.MAP_HEIGHT - 5)
            position = Position(x, y)
            
            if self._is_valid_patch_placement(position):  # Reuse data patch placement validation
                # Choose random exploit
                exploit_key = random.choice(available_exploits)
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game_map.exploit_pickups[(x, y)] = exploit_item
                placed_exploits += 1
    
    def _place_story_fragment(self):
        """Place a story fragment on level 3 with 50% chance."""
        # Only place story fragments on level 3 (Military network)
        if self.level != 3:
            return
        
        # 50% chance to spawn a story fragment
        if random.random() > 0.5:
            return
        
        # Get the next undiscovered fragment
        next_fragment_index = self.story_fragment_manager.get_next_undiscovered_fragment()
        if next_fragment_index is None:
            return  # All fragments discovered
        
        # Try to place the story fragment in a valid location
        attempts = 0
        while attempts < 50:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8)
            position = Position(x, y)
            
            if self._is_valid_patch_placement(position):
                # Create and place the story fragment
                story_fragment = StoryFragment(next_fragment_index)
                # Store it in the game map - we'll need to add this to the GameMap class
                if not hasattr(self.game_map, 'story_fragments'):
                    self.game_map.story_fragments = {}
                self.game_map.story_fragments[(x, y)] = story_fragment
                
                self.message_log.add_message("Network anomaly detected... Data fragment available", Colors.CYAN)
                break
    
    def _place_permanent_upgrades(self):
        """Place permanent upgrades throughout the level with level-based rarity."""
        # Level-based upgrade counts
        if self.level == 1:
            upgrade_count = 1  # Rare on level 1
        elif self.level == 2:
            upgrade_count = 2  # More common on level 2
        else:
            upgrade_count = 3  # Most common on level 3+
        
        placed_upgrades = 0
        attempts = 0
        available_upgrades = list(GameUpgrades.UPGRADES.keys())
        
        while placed_upgrades < upgrade_count and attempts < 100:
            attempts += 1
            x = random.randint(8, GameConfig.MAP_WIDTH - 8)
            y = random.randint(8, GameConfig.MAP_HEIGHT - 8) 
            position = Position(x, y)
            
            # Use stricter placement rules for rare upgrades
            if (self._is_valid_patch_placement(position) and
                abs(x - 5) > 10 and abs(y - 5) > 10):  # Not near starting position
                
                upgrade_key = random.choice(available_upgrades)
                self.game_map.permanent_upgrades[(x, y)] = upgrade_key
                placed_upgrades += 1
                
                # Remove from available to prevent duplicates on same level
                available_upgrades.remove(upgrade_key)
                if not available_upgrades:
                    break
    
    def _place_enemies(self, enemy_count: int):
        """Place enemies throughout the level with increased density."""
        enemy_types = ['scanner', 'patrol', 'bot', 'firewall', 'hunter']
        # Adjust weights for challenging gameplay
        enemy_weights = [4, 3, 2, 2, 2]  # More scanners and firewalls for detection challenge
        
        # Increase enemy density significantly
        actual_enemy_count = int(enemy_count * 1.6)  # 60% more enemies
        placed_enemies = 0
        attempts = 0
        
        while placed_enemies < actual_enemy_count and attempts < actual_enemy_count * 25:
            attempts += 1
            # Ensure enemies spawn well away from top-left player spawn area
            x = random.randint(10, GameConfig.MAP_WIDTH - 2)
            y = random.randint(10, GameConfig.MAP_HEIGHT - 2)
            position = Position(x, y)
            
            if self._is_valid_enemy_placement(position):
                enemy_type = random.choices(enemy_types, weights=enemy_weights)[0]
                enemy = Enemy(position, enemy_type)
                
                if enemy_type == 'patrol':
                    enemy.patrol_points = self.enemy_manager._generate_patrol_route(position)
                
                self.enemies.append(enemy)
                placed_enemies += 1
    
    
    def _is_valid_special_placement(self, position: Position) -> bool:
        """Check if position is valid for special node placement."""
        return (not self.game_map.is_wall(position) and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                position.distance_to(Position(5, 5)) > 8)
    
    def _is_valid_patch_placement(self, position: Position) -> bool:
        """Check if position is valid for data patch placement."""
        return (not self.game_map.is_wall(position) and
                (position.x, position.y) not in self.game_map.data_patches and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes and
                position.distance_to(Position(5, 5)) > 5)
    
    def _is_valid_enemy_placement(self, position: Position) -> bool:
        """Check if position is valid for enemy placement."""
        return (self.game_map.is_valid_position(position) and
                position.distance_to(Position(5, 5)) > 12 and
                not self._get_enemy_at(position) and
                (position.x, position.y) not in self.game_map.data_patches and
                (position.x, position.y) not in self.game_map.cooling_nodes and
                (position.x, position.y) not in self.game_map.cpu_recovery_nodes)
    
    
    def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
        """Get the next N positions this enemy will move to."""
        if enemy.disabled_turns > 0:
            return []
        
        positions = []
        
        if enemy.type_data.movement == EnemyMovement.STATIC:
            return []
        elif enemy.type_data.movement == EnemyMovement.LINEAR and enemy.patrol_points:
            positions = self._predict_patrol_movement(enemy, steps)
        elif enemy.type_data.movement == EnemyMovement.RANDOM:
            positions = self._predict_random_movement(enemy, steps)
        elif enemy.type_data.movement == EnemyMovement.SEEK:
            if enemy.state == EnemyState.HOSTILE and enemy.last_seen_player:
                positions = self._predict_seek_movement(enemy, steps)
        elif enemy.type_data.movement == EnemyMovement.TRACK:
            if enemy.state == EnemyState.HOSTILE:
                positions = self._predict_track_movement(enemy, steps)
        
        return positions
    
    def _predict_patrol_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """Predict next positions for patrol movement."""
        if not enemy.patrol_points:
            return []
        
        positions = []
        current_pos = Position(enemy.x, enemy.y)
        current_index = enemy.patrol_index
        
        for step in range(steps):
            target = enemy.patrol_points[current_index]
            
            if current_pos.distance_to(target) <= 1:
                current_index = (current_index + 1) % len(enemy.patrol_points)
                target = enemy.patrol_points[current_index]
            
            next_pos = self._get_next_move_toward(current_pos, target)
            if next_pos and next_pos != current_pos:
                positions.append(next_pos)
                current_pos = next_pos
            else:
                break
        
        return positions
    
    def _predict_random_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """Predict next positions for random movement (show possible moves)."""
        if enemy.state == EnemyState.HOSTILE:
            return self._predict_seek_movement(enemy, steps)
        
        # For random movement, show the queued moves
        enemy._ensure_random_move_queue()
        current_pos = Position(enemy.x, enemy.y)
        positions = []
        
        for i, (dx, dy) in enumerate(enemy.random_move_queue[:steps]):
            new_pos = Position(current_pos.x + dx, current_pos.y + dy)
            if (new_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                self.game_map.is_valid_position(new_pos) and
                not new_pos.distance_to(self.player.position) == 0 and
                not self._get_enemy_at(new_pos)):
                positions.append(new_pos)
                current_pos = new_pos
            else:
                # If this move is blocked, stop predicting further moves
                break
        
        return positions
    
    def _predict_seek_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """Predict next positions for seek movement."""
        if not enemy.last_seen_player:
            return []
        
        return self._predict_movement_toward_target(enemy, enemy.last_seen_player, steps)
    
    def _predict_track_movement(self, enemy: Enemy, steps: int) -> List[Position]:
        """Predict next positions for track movement."""
        return self._predict_movement_toward_target(enemy, self.player.position, steps)
    
    def _predict_movement_toward_target(self, enemy: Enemy, target: Position, steps: int) -> List[Position]:
        """Predict movement toward a specific target."""
        positions = []
        current_pos = Position(enemy.x, enemy.y)
        
        for step in range(steps):
            next_pos = self._get_next_move_toward(current_pos, target)
            if next_pos and next_pos != current_pos:
                positions.append(next_pos)
                current_pos = next_pos
            else:
                break
        
        return positions
    
    def _get_next_move_toward(self, start: Position, target: Position) -> Optional[Position]:
        """Get the next move position toward target."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            return None
        
        dx = 0 if start.x == target.x else (1 if target.x > start.x else -1)
        dy = 0 if start.y == target.y else (1 if target.y > start.y else -1)
        
        # Try different movement directions in order of preference
        move_attempts = [
            (dx, dy), (dx, 0), (0, dy), (dx, -dy), (-dx, dy),
            (-dx, 0), (0, -dy), (-dx, -dy)
        ]
        
        for try_dx, try_dy in move_attempts:
            if try_dx == 0 and try_dy == 0:
                continue
            
            new_position = Position(start.x + try_dx, start.y + try_dy)
            if (new_position.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT) and
                self.game_map.is_valid_position(new_position) and
                not new_position.distance_to(self.player.position) == 0):
                return new_position
        
        return None

# ============================================================================
# EXPLOIT SYSTEM
# ============================================================================

class ExploitSystem:
    """Handles exploit usage and effects."""
    
    def __init__(self, game: Game):
        self.game = game
    
    def use_exploit(self, exploit_key: str) -> bool:
        """Attempt to use an exploit."""
        if not self.game.player.inventory_manager.can_use_exploit(exploit_key):
            self.game.message_log.add_message("Exploit not equipped")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]
        
        # Check heat limit
        heat_cost = self._calculate_heat_cost(exploit)
        if self.game.player.heat + heat_cost > 100:
            self.game.sound_manager.play_sound("exploit_failed")
            self.game.message_log.add_message("System too hot! Cannot use")
            return False
        
        # Check if exploit requires targeting

        if exploit.targeting != TargetingMode.NONE and exploit.range > 0:
            self.game.sound_manager.play_sound("exploit_targeting")
            self.game.targeting_mode = True
            self.game.targeting_exploit = exploit_key
            self.game.cursor_position = Position(self.game.player.x, self.game.player.y)
            self.game.message_log.add_message(f"Targeting {exploit.name}")
            return True
        
        # Execute non-targeting exploits immediately

        return self.execute_exploit(exploit_key, self.game.player.position)
    
    def execute_exploit(self, exploit_key: str, target: Position) -> bool:
        """Execute an exploit at target location."""
        if exploit_key not in GameData.EXPLOITS:
            self.game.message_log.add_message("Unknown exploit")
            return False
        
        exploit = GameData.EXPLOITS[exploit_key]

        # Validate target
        if not self._validate_target(exploit, target):
            return False
        
        # Execute specific exploit
        success = self._execute_specific_exploit(exploit_key, exploit, target)
        
        # Only apply heat cost if the exploit was successful
        if success:
            heat_cost = self._calculate_heat_cost(exploit)
            self.game.player.heat = min(100, self.game.player.heat + heat_cost)
        
        if success:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.maybe_process_turn()
        
        return success
    
    def _calculate_heat_cost(self, exploit: ExploitDefinition) -> int:
        """Calculate heat cost with efficiency bonus."""
        multiplier = 0.6 if self.game.player.temporary_effects['exploit_efficiency_turns'] > 0 else 1.0
        return int(exploit.heat * multiplier)
    
    def _validate_target(self, exploit: ExploitDefinition, target: Position) -> bool:
        """Validate targeting for exploit."""
        if not target.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
            self.game.message_log.add_message("Invalid target location")
            return False
        
        distance = self.game.player.position.distance_to(target)
        if distance > exploit.range:
            self.game.message_log.add_message(f"Out of range (Max: {exploit.range})")
            return False
        
        return True

    
    def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
        """Execute the specific exploit effect."""
        if exploit_key == 'shadow_step':
            return self._execute_shadow_step(target)
        elif exploit_key == 'data_mimic':
            return self._execute_data_mimic()
        elif exploit_key == 'noise_maker':
            return self._execute_noise_maker(target)
        elif exploit_key == 'code_injection':
            return self._execute_code_injection(target)
        elif exploit_key == 'buffer_overflow':
            return self._execute_buffer_overflow(target)
        elif exploit_key == 'system_crash':
            return self._execute_system_crash(target, exploit.range)
        elif exploit_key == 'network_scan':
            return self._execute_network_scan()
        elif exploit_key == 'log_wiper':
            return self._execute_log_wiper()
        elif exploit_key == 'emp_burst':
            return self._execute_emp_burst(target, exploit.range)
        
        return False
    
    def _execute_shadow_step(self, target: Position) -> bool:
        """Execute shadow step exploit."""
        if self.game.game_map.is_shadow(target) and self.game.game_map.is_valid_position(target):
            if not self.game._get_enemy_at(target):
                self.game.sound_manager.play_sound("exploit_shadow_step")
                self.game.player.position = target
                self.game.message_log.add_message("Shadow Step executed")
                return True
            else:
                self.game.message_log.add_message("Target occupied")
        else:
            self.game.message_log.add_message("Must target shadow zone")
        return False
    
    def _execute_data_mimic(self) -> bool:
        """Execute data mimic exploit."""
        self.game.sound_manager.play_sound("exploit_data_mimic")
        self.game.player.temporary_effects['data_mimic_turns'] = 5
        self.game.message_log.add_message("Data Mimic active")
        return True
    
    def _execute_noise_maker(self, target: Position) -> bool:
        """Execute noise maker exploit."""
        self.game.sound_manager.play_sound("exploit_noise_maker")
        attracted = 0
        for enemy in self.game.enemies:
            if (enemy.type_data.movement in [EnemyMovement.SEEK, EnemyMovement.RANDOM, EnemyMovement.LINEAR] and
                enemy.position.distance_to(target) <= 10):
                if enemy.type_data.movement == EnemyMovement.LINEAR:
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 3
                else:
                    enemy.last_seen_player = target
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 2
                attracted += 1
        self.game.message_log.add_message(f"Noise: {attracted} enemies attracted")
        return True
    
    def _execute_code_injection(self, target: Position) -> bool:
        """Execute code injection exploit."""
        self.game.sound_manager.play_sound("exploit_code_injection")
        target_enemy = self.game._get_enemy_at(target)
        if target_enemy:
            damage = 35 if target_enemy.type == 'firewall' else 30
            
            if target_enemy.take_damage(damage):
                self.game.enemies.remove(target_enemy)
                self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)
                self.game.message_log.add_message(f"Eliminated {target_enemy.type_data.name}")
            else:
                self.game.message_log.add_message(f"{target_enemy.type_data.name} damaged")
                target_enemy.state = EnemyState.HOSTILE
                target_enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
            return True
        else:
            self.game.message_log.add_message("No target at location")
            return False
    
    def _execute_buffer_overflow(self, target: Position) -> bool:
        """Execute buffer overflow exploit."""
        self.game.sound_manager.play_sound("exploit_buffer_overflow")
        distance = self.game.player.position.distance_to(target)
        if distance <= 1:
            target_enemy = self.game._get_enemy_at(target)
            if target_enemy:
                damage = 50
                if target_enemy.take_damage(damage):
                    self.game.enemies.remove(target_enemy)
                    self.game.player.cpu = min(self.game.player.max_cpu, self.game.player.cpu + GameBalance.ENEMY_ELIMINATION_CPU_REWARD)
                    self.game.message_log.add_message(f"Eliminated {target_enemy.type_data.name}")
                else:
                    self.game.message_log.add_message(f"{target_enemy.type_data.name} damaged")
                    target_enemy.state = EnemyState.HOSTILE
                    target_enemy.last_seen_player = Position(self.game.player.x, self.game.player.y)
                return True
            else:
                self.game.message_log.add_message("No enemy at target")
        else:
            self.game.message_log.add_message("Must target adjacent enemy")
        return False
    
    def _execute_system_crash(self, target: Position, exploit_range: int) -> bool:
        """Execute system crash exploit."""
        self.game.sound_manager.play_sound("exploit_system_crash")
        enemies_hit = []
        for enemy in self.game.enemies[:]:
            if enemy.position.distance_to(target) <= exploit_range:
                enemy.disabled_turns = 4
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                enemies_hit.append(enemy)
        self.game.message_log.add_message(f"System crash: {len(enemies_hit)} disabled")
        return True
    
    def _execute_network_scan(self) -> bool:
        """Execute enhanced network scan exploit."""
        self.game.sound_manager.play_sound("exploit_network_scan")
        self.game.game_state.network_scan_turns = 5  # Extended duration for tactical advantage
        
        # Network scan reveals entire map layout
        for x in range(GameConfig.MAP_WIDTH):
            for y in range(GameConfig.MAP_HEIGHT):
                self.game.game_map.explored_tiles.add((x, y))
        
        # Update all enemy positions in memory
        for enemy in self.game.enemies:
            self.game.game_map.last_known_enemy_positions[enemy.id] = (enemy.position, self.game.turn)
        
        self.game.message_log.add_message("FULL NETWORK SCAN ACTIVE - All systems revealed!")
        return True

    def _execute_log_wiper(self) -> bool:
        """Execute log wiper exploit."""
        self.game.sound_manager.play_sound("exploit_log_wiper")
        old_detection = self.game.player.detection
        self.game.player.detection = max(0, self.game.player.detection - 30)
        actual_reduction = old_detection - self.game.player.detection
        self.game.message_log.add_message(f"Detection: -{actual_reduction:.1f}%")
        return True
    
    def _execute_emp_burst(self, target: Position, exploit_range: int) -> bool:
        """Execute EMP burst exploit."""
        self.game.sound_manager.play_sound("exploit_emp_burst")
        enemies_hit = []
        for enemy in self.game.enemies[:]:
            if enemy.position.distance_to(target) <= exploit_range:
                enemy.disabled_turns = 6
                enemy.state = EnemyState.UNAWARE
                enemy.alert_timer = 0
                enemies_hit.append(enemy)
        self.game.message_log.add_message(f"EMP: {len(enemies_hit)} disabled")
        return True
# INPUT HANDLING
# ============================================================================

class UniversalInputHandler:
    """Universal input handler for all menu and UI screens."""
    
    # Define common key sets
    NAVIGATION_UP = (tcod.event.KeySym.UP, tcod.event.KeySym.W, tcod.event.KeySym.KP_8)
    NAVIGATION_DOWN = (tcod.event.KeySym.DOWN, tcod.event.KeySym.S, tcod.event.KeySym.KP_2)
    NAVIGATION_LEFT = (tcod.event.KeySym.LEFT, tcod.event.KeySym.A, tcod.event.KeySym.KP_4)
    NAVIGATION_RIGHT = (tcod.event.KeySym.RIGHT, tcod.event.KeySym.D, tcod.event.KeySym.KP_6)
    CONFIRM = (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER)
    
    @staticmethod
    def handle_list_navigation(screen_instance, event, option_count: int, wrap_around: bool = True, callback=None) -> bool:
        """Handle up/down navigation for list-based screens.
        
        Args:
            screen_instance: The screen object with selected_option attribute
            event: The input event
            option_count: Number of options in the list
            wrap_around: Whether to wrap around at ends
            callback: Optional callback function to call with direction (-1 or 1)
            
        Returns:
            True if input was handled, False otherwise
        """
        if event.sym in UniversalInputHandler.NAVIGATION_UP:
            if callback:
                callback(-1)
            elif wrap_around:
                screen_instance.selected_option = (screen_instance.selected_option - 1) % option_count
            else:
                screen_instance.selected_option = max(0, screen_instance.selected_option - 1)
            return True
        elif event.sym in UniversalInputHandler.NAVIGATION_DOWN:
            if callback:
                callback(1)
            elif wrap_around:
                screen_instance.selected_option = (screen_instance.selected_option + 1) % option_count
            else:
                screen_instance.selected_option = min(option_count - 1, screen_instance.selected_option + 1)
            return True
        return False
    
    @staticmethod
    def handle_dialog_navigation(screen_instance, event, option_count: int = 2) -> bool:
        """Handle navigation for simple dialogs (usually 2 options).
        
        Args:
            screen_instance: The screen object with a selection attribute
            event: The input event
            option_count: Number of options (default 2 for Yes/No dialogs)
            
        Returns:
            True if input was handled, False otherwise
        """
        selection_attr = getattr(screen_instance, 'warning_selection', getattr(screen_instance, 'selected_option', None))
        if selection_attr is None:
            return False
            
        if event.sym in (UniversalInputHandler.NAVIGATION_UP + UniversalInputHandler.NAVIGATION_DOWN):
            # For simple dialogs, any up/down toggles between options
            if hasattr(screen_instance, 'warning_selection'):
                screen_instance.warning_selection = 1 - screen_instance.warning_selection
            else:
                screen_instance.selected_option = 1 - screen_instance.selected_option
            return True
        return False
    
    @staticmethod
    def handle_value_adjustment(screen_instance, event, adjust_callback) -> bool:
        """Handle left/right adjustment for settings or values.
        
        Args:
            screen_instance: The screen object
            event: The input event
            adjust_callback: Function to call with direction (-1 or 1)
            
        Returns:
            True if input was handled, False otherwise
        """
        if event.sym in UniversalInputHandler.NAVIGATION_LEFT:
            adjust_callback(-1)
            return True
        elif event.sym in UniversalInputHandler.NAVIGATION_RIGHT:
            adjust_callback(1)
            return True
        return False
    
    @staticmethod
    def is_confirm_key(event) -> bool:
        """Check if the event is a confirm key (Enter/Return)."""
        return event.sym in UniversalInputHandler.CONFIRM
    
    @staticmethod
    def is_escape_key(event) -> bool:
        """Check if the event is an escape key."""
        return event.sym == tcod.event.KeySym.ESCAPE
    
    @staticmethod
    def handle_any_key_screen(event) -> bool:
        """Handle input for screens that return on any key press."""
        return True  # Any key should trigger a return action

class InputHandler:
    """Handles all user input and translates it to game actions."""
    
    def __init__(self, game: Game):
        self.game = game
        self.exploit_system = ExploitSystem(game)
    
    def handle_keydown(self, event) -> bool:
        """Handle keydown events. Returns True if game should continue."""        
        # Dead/game over state - only allow escape to exit
        if self.game.player.cpu <= 0 or self.game.game_over:
            if event.sym == tcod.event.KeySym.ESCAPE:
                # Exit to main menu instead of showing pause menu when dead
                return False
            return True
        
        # Modal screens - handle non-escape keys
        if self.game.show_help:
            self.game.show_help = False
            return True
        
        if self.game.show_story_fragment is not None:
            # Any key closes the story fragment display
            self.game.show_story_fragment = None
            return True
        
        if self.game.show_lore_viewer:
            return self._handle_lore_viewer_input(event)
        
        if self.game.show_inventory:
            return self._handle_inventory_input(event)
        
        if self.game.targeting_mode:
            return self._handle_targeting_input(event)
        
        # Normal gameplay
        return self._handle_gameplay_input(event)
    
    def _handle_escape(self) -> bool:
        """Handle escape key for UI states."""
        if self.game.show_story_fragment is not None:
            self.game.show_story_fragment = None
        elif self.game.show_lore_viewer:
            self.game.show_lore_viewer = False
            self.game.lore_viewer_mode = "list"
            self.game.lore_viewer_selection = 0
        elif self.game.show_help:
            self.game.show_help = False
        elif self.game.show_inventory:
            self.game.show_inventory = False
        elif self.game.targeting_mode:
            self.game.targeting_mode = False
            self.game.targeting_exploit = None
            self.game.message_log.add_message("Targeting cancelled")
        return True
    
    def _handle_inventory_input(self, event) -> bool:
        """Handle input while inventory is open."""
        # Handle navigation using universal handler with callback
        if UniversalInputHandler.handle_list_navigation(self, event, 0, True, self._navigate_inventory):
            return True
        
        # Handle selection and other actions
        if UniversalInputHandler.is_confirm_key(event):
            self._use_selected_inventory_item()
        elif event.sym == tcod.event.KeySym.U:
            self._unequip_selected_exploit()
        elif event.sym == tcod.event.KeySym.I:
            self.game.show_inventory = False
        
        return True
    
    def _handle_lore_viewer_input(self, event) -> bool:
        """Handle input while lore viewer is open."""
        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        
        if not discovered_fragments:
            # No fragments, only ESC should work to close (handled by main loop)
            return UniversalInputHandler.is_escape_key(event)
            
        if self.game.lore_viewer_mode == "list":
            # Handle navigation using universal handler with callback
            if UniversalInputHandler.handle_list_navigation(self, event, len(discovered_fragments), False, self._navigate_lore_viewer):
                return True
            
            # Handle selection
            if UniversalInputHandler.is_confirm_key(event):
                # Enter reading mode for selected fragment
                self.game.lore_viewer_mode = "reading"
                return True
            elif UniversalInputHandler.is_escape_key(event):
                # Let main loop handle ESC
                return False
        
        elif self.game.lore_viewer_mode == "reading":
            # Reading mode - any key except ESC returns to list
            if UniversalInputHandler.is_escape_key(event):
                # Let main loop handle ESC
                return False
            else:
                # Any other key returns to list
                self.game.lore_viewer_mode = "list"
                return True
        
        # Unhandled key - let other handlers process it
        return False
    
    def _navigate_lore_viewer(self, direction: int):
        """Navigate lore viewer selection."""
        discovered_fragments = self.game.story_fragment_manager.get_discovered_fragments()
        if discovered_fragments:
            if direction == -1:
                self.game.lore_viewer_selection = max(0, self.game.lore_viewer_selection - 1)
            else:
                self.game.lore_viewer_selection = min(len(discovered_fragments) - 1, self.game.lore_viewer_selection + 1)
    
    def _handle_targeting_input(self, event) -> bool:
        """Handle input while in targeting mode."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
            # WASD + QEZC (original)
            tcod.event.KeySym.W: (0, -1),
            tcod.event.KeySym.Q: (-1, -1),
            tcod.event.KeySym.E: (1, -1),
            tcod.event.KeySym.D: (1, 0),
            tcod.event.KeySym.C: (1, 1),
            tcod.event.KeySym.S: (0, 1),
            tcod.event.KeySym.Z: (-1, 1),
            tcod.event.KeySym.A: (-1, 0),
            # Arrow keys
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            # Numpad
            tcod.event.KeySym.KP_8: (0, -1),
            tcod.event.KeySym.KP_9: (1, -1),
            tcod.event.KeySym.KP_6: (1, 0),
            tcod.event.KeySym.KP_3: (1, 1),
            tcod.event.KeySym.KP_2: (0, 1),
            tcod.event.KeySym.KP_1: (-1, 1),
            tcod.event.KeySym.KP_4: (-1, 0),
            tcod.event.KeySym.KP_7: (-1, -1)
        }
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game._move_cursor(dx, dy)
        elif event.sym in (tcod.event.KeySym.RETURN, tcod.event.KeySym.KP_ENTER):
            self.exploit_system.execute_exploit(
                self.game.targeting_exploit, 
                self.game.cursor_position
            )
        
        return True
    
    def _handle_gameplay_input(self, event) -> bool:
        """Handle input during normal gameplay."""
        # Movement keys - expanded to include numpad and arrows
        movement_map = {
            # WASD + QEZC (original)
            tcod.event.KeySym.W: (0, -1),
            tcod.event.KeySym.Q: (-1, -1),
            tcod.event.KeySym.E: (1, -1),
            tcod.event.KeySym.D: (1, 0),
            tcod.event.KeySym.C: (1, 1),
            tcod.event.KeySym.S: (0, 1),
            tcod.event.KeySym.Z: (-1, 1),
            tcod.event.KeySym.A: (-1, 0),
            # Arrow keys
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.RIGHT: (1, 0),
            # Numpad
            tcod.event.KeySym.KP_8: (0, -1),
            tcod.event.KeySym.KP_9: (1, -1),
            tcod.event.KeySym.KP_6: (1, 0),
            tcod.event.KeySym.KP_3: (1, 1),
            tcod.event.KeySym.KP_2: (0, 1),
            tcod.event.KeySym.KP_1: (-1, 1),
            tcod.event.KeySym.KP_4: (-1, 0),
            tcod.event.KeySym.KP_7: (-1, -1)
        }
        
        if event.sym in movement_map:
            dx, dy = movement_map[event.sym]
            self.game.move_player(dx, dy)
        
        # Wait/rest
        elif event.sym in (tcod.event.KeySym.SPACE, tcod.event.KeySym.PERIOD, tcod.event.KeySym.KP_5):
            self.game.maybe_process_turn()
        
        # UI toggles
        elif event.sym == tcod.event.KeySym.I:
            self._open_inventory()
        elif event.sym == tcod.event.KeySym.L:
            self.game.show_lore_viewer = True
        elif event.sym == tcod.event.KeySym.SLASH and (event.mod & (tcod.event.Modifier.LSHIFT | tcod.event.Modifier.RSHIFT)):
            self.game.show_help = True
        
        # Exploit usage (1-5 keys)
        elif event.sym == tcod.event.KeySym.N1:
            self._use_exploit_slot(0)
        elif event.sym == tcod.event.KeySym.N2:
            self._use_exploit_slot(1)
        elif event.sym == tcod.event.KeySym.N3:
            self._use_exploit_slot(2)
        elif event.sym == tcod.event.KeySym.N4:
            self._use_exploit_slot(3)
        elif event.sym == tcod.event.KeySym.N5:
            self._use_exploit_slot(4)
        elif event.sym == tcod.event.KeySym.N5:
            self._use_exploit_slot(4)
        
        return True
    
    def _navigate_inventory(self, direction: int):
        """Navigate inventory selection across equipped exploits and inventory items."""
        # Get total selectable items (equipped exploits + inventory items)
        equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
        inventory_items = len(self.game.player.inventory_manager.get_display_items())
        total_items = equipped_count + inventory_items
        
        if total_items > 0:
            self.game.inventory_selection = (self.game.inventory_selection + direction) % total_items
    
    def _use_selected_inventory_item(self):
        """Use the currently selected item (unequip exploit or use inventory item)."""
        equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
        
        if self.game.inventory_selection < equipped_count:
            # Selection is in equipped exploits - unequip the selected one
            self._unequip_selected_exploit()
        else:
            # Selection is in inventory items - use the selected item
            inventory_items = self.game.player.inventory_manager.get_display_items()
            item_index = self.game.inventory_selection - equipped_count
            
            if 0 <= item_index < len(inventory_items):
                selected_item = inventory_items[item_index]
                if selected_item.use(self.game.player, self.game):
                    # Update selection if item was consumed
                    new_equipped_count = len(self.game.player.inventory_manager.equipped_exploits)
                    new_inventory_count = len(self.game.player.inventory_manager.get_display_items())
                    max_selection = new_equipped_count + new_inventory_count - 1
                    
                    if max_selection >= 0:
                        self.game.inventory_selection = min(self.game.inventory_selection, max_selection)
    
    def _unequip_selected_exploit(self):
        """Unequip the specifically selected exploit."""
        equipped_exploits = self.game.player.inventory_manager.equipped_exploits
        
        if 0 <= self.game.inventory_selection < len(equipped_exploits):
            exploit_key = equipped_exploits[self.game.inventory_selection]
            if self.game.player.inventory_manager.unequip_exploit(exploit_key):
                # Add the exploit back to inventory as an item
                exploit_def = GameData.EXPLOITS[exploit_key]
                exploit_item = ExploitItem(exploit_key, exploit_def)
                self.game.player.inventory_manager.add_item(exploit_item)
                self.game.message_log.add_message(f"Unequipped {exploit_def.name}")
            else:
                self.game.message_log.add_message("Cannot unequip exploit")
        else:
            self.game.message_log.add_message("No exploit selected")
    
    def _open_inventory(self):
        """Open the inventory screen."""
        self.game.sound_manager.play_sound("ui_menu_open")
        self.game.show_inventory = True
        self.game.inventory_selection = 0
    
    def _use_exploit_slot(self, slot: int):
        """Use exploit in specified slot."""
        equipped = self.game.player.inventory_manager.equipped_exploits
        if 0 <= slot < len(equipped):
            self.exploit_system.use_exploit(equipped[slot])

# ============================================================================
# RENDERING SYSTEM
# ============================================================================

class Renderer:
    """Handles all game rendering."""
    
    def __init__(self):
        self.ui_renderer = UIRenderer()
        self.map_renderer = MapRenderer()
    
    def render_game(self, console: tcod.console.Console, game: Game):
        """Render the complete game state."""
        console.clear()
        
        if game.show_story_fragment is not None:
            self.ui_renderer.render_story_fragment_screen(console, game, game.show_story_fragment)
        elif game.show_lore_viewer:
            self.ui_renderer.render_lore_viewer_screen(console, game)
        elif game.show_help:
            self.ui_renderer.render_help_screen(console)
        elif game.show_inventory:
            self.ui_renderer.render_inventory_screen(console, game)
        else:
            self._render_main_game_screen(console, game)
    
    def _render_main_game_screen(self, console: tcod.console.Console, game: Game):
        """Render the main game screen."""
        self.ui_renderer.render_top_status_bar(console, game)
        self.map_renderer.render_map(console, game)
        self.ui_renderer.render_bottom_panel(console, game)
        self.ui_renderer.render_system_log(console, game)
        
        # Render game over/death messages
        if game.game_over:
            self._render_victory_message(console)
        elif game.player.cpu <= 0:
            self._render_death_message(console)
    
    def _render_victory_message(self, console: tcod.console.Console):
        """Render victory message."""
        center_x = GameConfig.GAME_AREA_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_TINY, center_y, "MISSION COMPLETE!", fg=Colors.ACID_GREEN)
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_LARGE, center_y + GameConfig.MESSAGE_LINE_SPACING, "All networks infiltrated!", fg=Colors.CYBER_TEAL)
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_SMALL, center_y + GameConfig.MESSAGE_BUTTON_SPACING, "Press ESC to exit", fg=Colors.ELECTRIC_PURPLE)
    
    def _render_death_message(self, console: tcod.console.Console):
        """Render death message."""
        center_x = GameConfig.GAME_AREA_WIDTH // 2
        center_y = GameConfig.SCREEN_HEIGHT // 2
        
        # Ensure save is deleted on death (permadeath)
        if SaveGameManager.save_exists():
            SaveGameManager.delete_save()
        
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_SMALL, center_y, "SYSTEM FAILURE", fg=Colors.NEON_PINK)
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_MEDIUM, center_y + GameConfig.MESSAGE_LINE_SPACING, "Consciousness purged", fg=Colors.RED)
        console.print(center_x - GameConfig.MESSAGE_CENTER_OFFSET_SMALL, center_y + GameConfig.MESSAGE_BUTTON_SPACING, "Press ESC to exit", fg=Colors.ELECTRIC_PURPLE)

class UIRenderer:
    """Renders UI elements."""
    
    def _clear_game_area(self, console: tcod.console.Console) -> None:
        """Clear only the main game area, preserving UI elements."""
        for x in range(GameConfig.GAME_AREA_WIDTH):
            for y in range(1, GameConfig.PANEL_Y):
                console.print(x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)
    
    def _render_centered_title(self, console: tcod.console.Console, title: str, y: int, color: tuple = Colors.YELLOW) -> None:
        """Render a centered title in the game area."""
        title_x = GameConfig.GAME_AREA_WIDTH // 2 - len(title) // 2
        console.print(title_x, y, title, fg=color)
    
    def _render_screen_header(self, console: tcod.console.Console, title: str, subtitle: str = None) -> int:
        """Render a standardized screen header with title and optional subtitle.
        Returns the y position after the header for content to start."""
        # Top border
        console.print(2, 1, "=" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
        
        # Main title (centered)
        title_x = GameConfig.SCREEN_WIDTH // 2 - len(title) // 2
        console.print(title_x, 2, title, fg=Colors.CYAN)
        
        # Subtitle if provided
        if subtitle:
            subtitle_x = GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2
            console.print(subtitle_x, 3, subtitle, fg=Colors.WHITE)
            # Bottom border after subtitle
            console.print(2, 4, "=" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 6  # Content starts at line 6
        else:
            # Bottom border after title
            console.print(2, 3, "=" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
            return 5  # Content starts at line 5
    
    def _render_screen_footer(self, console: tcod.console.Console, instructions: str, additional_line: str = None) -> None:
        """Render a standardized screen footer with instructions."""
        footer_y = GameConfig.SCREEN_HEIGHT - 4 if additional_line else GameConfig.SCREEN_HEIGHT - 3
        
        # Footer border
        console.print(2, footer_y, "=" * (GameConfig.SCREEN_WIDTH - 4), fg=Colors.CYAN)
        
        # Instructions (centered)
        instructions_x = GameConfig.SCREEN_WIDTH // 2 - len(instructions) // 2
        console.print(instructions_x, footer_y + 1, instructions, fg=Colors.YELLOW)
        
        # Additional line if provided
        if additional_line:
            additional_x = GameConfig.SCREEN_WIDTH // 2 - len(additional_line) // 2
            console.print(additional_x, footer_y + 2, additional_line, fg=Colors.YELLOW)
    
    def _render_content_area_with_word_wrap(self, console: tcod.console.Console, text: str, start_y: int, end_y: int) -> None:
        """Render text content with word wrapping within the specified y bounds."""
        lines = text.split('\n')
        y_offset = start_y
        max_width = GameConfig.SCREEN_WIDTH - 6  # Leave margins
        
        for line in lines:
            if y_offset >= end_y:
                console.print(3, y_offset, "... [Text continues]", fg=Colors.YELLOW)
                break
                
            line = line.strip()
            if not line:
                y_offset += 1
                continue
                
            # Word wrap long lines
            if len(line) <= max_width:
                console.print(3, y_offset, line, fg=Colors.WHITE)
                y_offset += 1
            else:
                words = line.split(' ')
                current_line = ""
                
                for word in words:
                    if len(current_line + word) + 1 <= max_width:
                        current_line += (word if not current_line else " " + word)
                    else:
                        if current_line:
                            console.print(3, y_offset, current_line, fg=Colors.WHITE)
                            y_offset += 1
                            if y_offset >= end_y:
                                break
                        current_line = word
                
                if current_line and y_offset < end_y:
                    console.print(3, y_offset, current_line, fg=Colors.WHITE)
                    y_offset += 1
    
    def _render_overlay_menu(self, console: tcod.console.Console, title: str, options: list, menu_width: int = 30) -> tuple:
        """Render a centered overlay menu with title and options.
        Returns (menu_x, menu_y, menu_height) for additional rendering."""
        menu_height = 6 + len(options)  # Header + options + padding
        menu_x = (GameConfig.SCREEN_WIDTH - menu_width) // 2
        menu_y = (GameConfig.SCREEN_HEIGHT - menu_height) // 2
        
        # Menu background
        for y in range(menu_y, menu_y + menu_height):
            for x in range(menu_x, menu_x + menu_width):
                console.print(x, y, ' ', fg=Colors.WHITE, bg=Colors.UI_BG)
        
        # Menu borders (top and bottom)
        for x in range(menu_x, menu_x + menu_width):
            console.print(x, menu_y, '=', fg=Colors.CYAN, bg=Colors.UI_BG)
            console.print(x, menu_y + menu_height - 1, '=', fg=Colors.CYAN, bg=Colors.UI_BG)
        
        # Title (centered)
        title_x = menu_x + (menu_width - len(title)) // 2
        console.print(title_x, menu_y + 2, title, fg=Colors.YELLOW, bg=Colors.UI_BG)
        
        # Options
        for i, option in enumerate(options):
            console.print(menu_x + 3, menu_y + 4 + i, option, fg=Colors.WHITE, bg=Colors.UI_BG)
        
        return menu_x, menu_y, menu_height
    
    def render_help_screen(self, console: tcod.console.Console):
        """Render the help screen using HelpMenu content."""
        # Create a temporary HelpMenu and use its render method
        help_menu = HelpMenu()
        help_menu.render(console)
    
    
    def render_inventory_screen(self, console: tcod.console.Console, game: Game):
        """Render the inventory screen."""
        # Clear only the main game area, preserve UI elements
        self._clear_game_area(console)
        
        # Title (centered in game area only)
        self._render_centered_title(console, "INVENTORY SYSTEM", 2)
        
        # Render preserved UI elements
        self.render_top_status_bar(console, game)
        self.render_bottom_panel(console, game)
        self.render_system_log(console, game)
        
        y = 5
        
        # Equipped exploits section
        y = self._render_equipped_exploits(console, game, y)
        y += 2
        
        # Data patches section
        y = self._render_data_patches(console, game, y)
        y += 2
        
        # Unequipped exploits section
        y = self._render_unequipped_exploits(console, game, y)
        
        # Controls
        self._render_inventory_controls(console)
    
    def _render_equipped_exploits(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render equipped exploits section."""
        console.print(2, y, "EQUIPPED EXPLOITS:", fg=Colors.CYAN)
        y += 1
        
        for i, exploit_key in enumerate(game.player.inventory_manager.equipped_exploits):
            # Check if this equipped exploit is selected
            if i == game.inventory_selection:
                color = Colors.YELLOW
                prefix = ">"
            elif exploit_key in GameData.EXPLOITS:
                color = Colors.GREEN
                prefix = " "
            else:
                color = Colors.RED
                prefix = " "
            
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                status_text = f"{prefix} {i+1}. {exploit.name} (RAM: {exploit.ram}, Heat: {exploit.heat})"
            else:
                status_text = f"{prefix} {i+1}. INVALID: {exploit_key}"
            
            # Truncate text to fit in game area (leave some margin for log)
            max_width = GameConfig.GAME_AREA_WIDTH - 6  # 4 indent + 2 margin
            if len(status_text) > max_width:
                status_text = status_text[:max_width-3] + "..."
            console.print(4, y, status_text, fg=color)
            y += 1
        
        equipped_count = len(game.player.inventory_manager.equipped_exploits)
        max_exploits = game.player.inventory_manager.max_equipped_exploits
        if equipped_count < max_exploits:
            console.print(4, y, f"[{equipped_count}/{max_exploits} slots used]", fg=Colors.YELLOW)
            y += 1
        
        return y
    
    def _render_data_patches(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render data patches section."""
        data_patches = game.player.inventory_manager.get_items_by_type("data_patch")
        console.print(2, y, f"DATA PATCHES ({len(data_patches)}):", fg=Colors.CYAN)
        y += 1
        
        if not data_patches:
            console.print(4, y, "No data patches collected", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)
            
            for i, patch in enumerate(data_patches):
                display_index = display_items.index(patch)
                # Adjust selection index to account for equipped exploits
                adjusted_selection_index = display_index + equipped_count
                
                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                description = patch.description if patch.discovered else "Unknown effect"
                quantity_text = f" ({patch.quantity})" if patch.quantity > 1 else ""
                patch_text = f"{prefix} {patch.name}{quantity_text} - {description}"
                
                # Truncate text to fit in game area
                max_width = GameConfig.GAME_AREA_WIDTH - 6  # 4 indent + 2 margin
                if len(patch_text) > max_width:
                    patch_text = patch_text[:max_width-3] + "..."
                console.print(4, y, patch_text, fg=color)
                y += 1
        
        return y
    
    def _render_unequipped_exploits(self, console: tcod.console.Console, game: Game, y: int) -> int:
        """Render unequipped exploits section."""
        exploit_items = game.player.inventory_manager.get_items_by_type("exploit")
        console.print(2, y, f"UNEQUIPPED EXPLOITS ({len(exploit_items)}):", fg=Colors.CYAN)
        y += 1
        
        if not exploit_items:
            console.print(4, y, "No unequipped exploits", fg=Colors.WHITE)
            y += 1
        else:
            display_items = game.player.inventory_manager.get_display_items()
            equipped_count = len(game.player.inventory_manager.equipped_exploits)
            
            for i, exploit_item in enumerate(exploit_items):
                try:
                    display_index = display_items.index(exploit_item)
                    # Adjust selection index to account for equipped exploits
                    adjusted_selection_index = display_index + equipped_count
                except ValueError:
                    adjusted_selection_index = -1
                
                if adjusted_selection_index == game.inventory_selection:
                    color = Colors.YELLOW
                    prefix = ">"
                else:
                    color = Colors.WHITE
                    prefix = " "
                
                exploit_text = f"{prefix} {exploit_item.name} - {exploit_item.description}"
                
                # Truncate text to fit in game area
                max_width = GameConfig.GAME_AREA_WIDTH - 6  # 4 indent + 2 margin
                if len(exploit_text) > max_width:
                    exploit_text = exploit_text[:max_width-3] + "..."
                console.print(4, y, exploit_text, fg=color)
                y += 1
        
        return y
    
    def _render_inventory_controls(self, console: tcod.console.Console):
        """Render inventory controls."""
        y_start = GameConfig.SCREEN_HEIGHT - 6
        
        console.print(2, y_start, "CONTROLS:", fg=Colors.CYAN)
        console.print(4, y_start + 1, "W/S: Navigate selection", fg=Colors.WHITE)
        console.print(4, y_start + 2, "Enter: Use selected item", fg=Colors.WHITE)
        console.print(4, y_start + 3, "U: Unequip selected exploit", fg=Colors.WHITE)
        console.print(4, y_start + 4, "ESC/I: Close inventory", fg=Colors.WHITE)
    
    def render_story_fragment_screen(self, console: tcod.console.Console, game: Game, fragment_index: int):
        """Render a single story fragment discovery screen."""
        console.clear()
        
        # Get the fragment text
        story_fragments = get_story_fragments()
        if fragment_index < 0 or fragment_index >= len(story_fragments):
            return
        
        fragment_text = story_fragments[fragment_index]
        
        # Render using shared components
        content_start_y = self._render_screen_header(console, "DATA FRAGMENT RECOVERED")
        content_end_y = GameConfig.SCREEN_HEIGHT - 6  # Leave room for 2-line footer
        
        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)
        
        self._render_screen_footer(console, "Press any key to continue...", "Press 'L' to view all lore")
    
    def render_lore_viewer_screen(self, console: tcod.console.Console, game: Game):
        """Render the lore viewer showing all discovered fragments."""
        console.clear()
        
        discovered_fragments = game.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = game.story_fragment_manager.get_fragment_count()
        
        if game.lore_viewer_mode == "reading" and discovered_fragments:
            # Reading mode - show full fragment text
            self._render_lore_reading_mode(console, game, discovered_fragments)
        else:
            # List mode - show fragment list with navigation
            self._render_lore_list_mode(console, game, discovered_fragments, discovered_count, total_count)
    
    def _render_lore_list_mode(self, console: tcod.console.Console, game: Game, discovered_fragments, discovered_count: int, total_count: int):
        """Render the lore viewer list mode."""
        title = f"RECOVERED DATA FRAGMENTS ({discovered_count}/{total_count})"
        content_start_y = self._render_screen_header(console, title)
        
        if not discovered_fragments:
            # No fragments discovered yet - center the message
            no_fragments_y = GameConfig.SCREEN_HEIGHT // 2
            console.print(GameConfig.SCREEN_WIDTH // 2 - 15, no_fragments_y, "No data fragments discovered yet.", fg=Colors.YELLOW)
            console.print(GameConfig.SCREEN_WIDTH // 2 - 20, no_fragments_y + 2, "Reach the Military Network (Level 3) to find them.", fg=Colors.WHITE)
            self._render_screen_footer(console, "Press ESC to close")
        else:
            # Show list of discovered fragments with brief previews
            y_offset = content_start_y
            max_display_height = GameConfig.SCREEN_HEIGHT - 6  # Leave room for footer
            
            for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
                if y_offset >= max_display_height:
                    console.print(3, y_offset, f"... and {len(discovered_fragments) - i} more fragments", fg=Colors.YELLOW)
                    break
                
                # Highlight selected entry
                is_selected = (i == game.lore_viewer_selection)
                title_color = Colors.YELLOW if is_selected else Colors.WHITE
                cursor = ">" if is_selected else " "
                
                # Fragment title (first line of the fragment)
                first_line = fragment_text.split('\n')[0]
                if len(first_line) > 58:  # Leave room for cursor and number
                    first_line = first_line[:55] + "..."
                
                console.print(2, y_offset, f"{cursor}{fragment_index + 1:2d}. {first_line}", fg=title_color)
                y_offset += 1
                
                # Brief preview (first few words of actual content)
                content_lines = [line.strip() for line in fragment_text.split('\n') if line.strip()]
                if len(content_lines) > 1:
                    preview = content_lines[1][:70] + "..." if len(content_lines[1]) > 70 else content_lines[1]
                    preview_color = (200, 200, 150) if is_selected else (128, 128, 128)
                    console.print(6, y_offset, preview, fg=preview_color)
                    y_offset += 1
                
                y_offset += 1  # Space between entries
            
            self._render_screen_footer(console, "Up/Down: Navigate, Enter: Read, ESC: Close")
    
    def _render_lore_reading_mode(self, console: tcod.console.Console, game: Game, discovered_fragments):
        """Render the lore viewer reading mode."""
        if game.lore_viewer_selection >= len(discovered_fragments):
            game.lore_viewer_selection = 0
            
        fragment_index, fragment_text = discovered_fragments[game.lore_viewer_selection]
        
        title = f"DATA FRAGMENT #{fragment_index + 1}"
        content_start_y = self._render_screen_header(console, title)
        content_end_y = GameConfig.SCREEN_HEIGHT - 4  # Leave room for footer
        
        self._render_content_area_with_word_wrap(console, fragment_text, content_start_y, content_end_y)
        
        self._render_screen_footer(console, "Any key: Back to list, ESC: Close")
    
    def render_top_status_bar(self, console: tcod.console.Console, game: Game):
        """Render the top status bar."""
        # Clear the top line
        for x in range(GameConfig.GAME_AREA_WIDTH):
            console.print(x, 0, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Color coding for status values
        cpu_color = self._get_cpu_color(game.player.cpu)
        heat_color = self._get_heat_color(game.player.heat)
        detection_color = self._get_detection_color(game.player.detection)
        ram_color = Colors.RED if game.player.ram_used > game.player.ram_total else Colors.GREEN
        
        # Build status line
        status_parts = [
            f"CPU:{game.player.cpu:3d}/{game.player.max_cpu}",
            f"Heat:{game.player.heat:3d}°C",
            f"Det:{int(game.player.detection):3d}%",
            f"RAM:{game.player.ram_used}/{game.player.ram_total}GB",
            f"Turn:{game.turn:4d}",
            "Press ? for help"
        ]
        
        colors = [cpu_color, heat_color, detection_color, ram_color, Colors.UI_TEXT, Colors.ELECTRIC_PURPLE]
        
        x_pos = 1
        for part, color in zip(status_parts, colors):
            if x_pos + len(part) < GameConfig.GAME_AREA_WIDTH - 1:
                console.print(x_pos, 0, part, fg=color, bg=Colors.UI_BG)
                x_pos += len(part) + 2
    
    def _get_cpu_color(self, cpu: int) -> Tuple[int, int, int]:
        """Get color for CPU display."""
        if cpu < 30:
            return Colors.RED
        elif cpu < 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_heat_color(self, heat: int) -> Tuple[int, int, int]:
        """Get color for heat display."""
        if heat > 80:
            return Colors.RED
        elif heat > 60:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def _get_detection_color(self, detection: float) -> Tuple[int, int, int]:
        """Get color for detection display."""
        if detection > 75:
            return Colors.RED
        elif detection > 50:
            return Colors.YELLOW
        else:
            return Colors.GREEN
    
    def render_bottom_panel(self, console: tcod.console.Console, game: Game):
        """Render the bottom information panel."""
        # Clear panel area
        for x in range(GameConfig.GAME_AREA_WIDTH):
            for y in range(GameConfig.PANEL_Y, GameConfig.SCREEN_HEIGHT):
                console.print(x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.UI_BG)
        
        # Panel border
        border = "+" + "-" * (GameConfig.GAME_AREA_WIDTH - 2) + "+"
        console.print(0, GameConfig.PANEL_Y, border, fg=Colors.LOG_BORDER, bg=Colors.UI_BG)
        
        # Equipped exploits (2 lines)
        self._render_equipped_exploits_panel(console, game)
        
        # Temporary conditions/effects (1 line)
        self._render_temporary_conditions(console, game)
    
    
    def _render_equipped_exploits_panel(self, console: tcod.console.Console, game: Game):
        """Render equipped exploits in bottom panel using 2 lines."""
        y1 = GameConfig.PANEL_Y + 1
        y2 = GameConfig.PANEL_Y + 2
        
        console.print(1, y1, "Exploits:", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)
        
        equipped_exploits = game.player.inventory_manager.equipped_exploits[:5]
        
        # Dynamically fit exploits on lines based on available space
        line1_exploits = []
        line2_exploits = []
        x_pos = 11
        
        for i, exploit_key in enumerate(equipped_exploits):
            if exploit_key in GameData.EXPLOITS:
                exploit = GameData.EXPLOITS[exploit_key]
                heat_cost = exploit.heat
                if game.player.temporary_effects['exploit_efficiency_turns'] > 0:
                    heat_cost = int(heat_cost * 0.6)
                
                heat_ok = game.player.heat + heat_cost <= GameConfig.MAX_HEAT
                color = Colors.GREEN if heat_ok else Colors.RED
                exploit_text = f"{i+1}.{exploit.name}"
                
                # Try to fit on first line
                if len(line1_exploits) == 0 or x_pos + len(exploit_text) + 2 <= GameConfig.GAME_AREA_WIDTH:
                    line1_exploits.append((exploit_key, exploit_text, color, i+1))
                    x_pos += len(exploit_text) + 2
                else:
                    # Move to second line
                    line2_exploits.append((exploit_key, exploit_text, color, i+1))
        
        # Render first line exploits
        x_pos = 11
        for exploit_key, exploit_text, color, slot_num in line1_exploits:
            console.print(x_pos, y1, exploit_text, fg=color, bg=Colors.UI_BG)
            x_pos += len(exploit_text) + 2
        
        # Render second line exploits
        if line2_exploits:
            console.print(1, y2, "        ", fg=Colors.ELECTRIC_PURPLE, bg=Colors.UI_BG)  # Indent to align
            x_pos = 11
            for exploit_key, exploit_text, color, slot_num in line2_exploits:
                console.print(x_pos, y2, exploit_text, fg=color, bg=Colors.UI_BG)
                x_pos += len(exploit_text) + 2
    
    def _render_temporary_conditions(self, console: tcod.console.Console, game: Game):
        """Render all temporary conditions with turn counts remaining."""
        y = GameConfig.PANEL_Y + 3
        
        conditions = []
        
        # Player temporary effects (from data patches and other sources)
        for effect_name, turns in game.player.temporary_effects.items():
            if turns > 0:
                display_name = effect_name.replace('_turns', '').replace('_', ' ').title()
                conditions.append(f"{display_name}({turns})")
        
        # Network scan effect
        if game.game_state.network_scan_turns > 0:
            conditions.append(f"Network Scan({game.game_state.network_scan_turns})")
        
        # Speed moves remaining (from speed boost)
        if game.player.speed_moves_remaining > 0:
            conditions.append(f"Speed Moves({game.player.speed_moves_remaining})")
        
        # Any other temporary game-wide effects could be added here
        
        if conditions:
            conditions_text = "Conditions: " + " ".join(conditions)
            # Truncate if too long for the line
            max_width = GameConfig.GAME_AREA_WIDTH - 2
            if len(conditions_text) > max_width:
                conditions_text = conditions_text[:max_width-3] + "..."
            console.print(1, y, conditions_text, fg=Colors.CYAN, bg=Colors.UI_BG)
        else:
            console.print(1, y, "Conditions: None", fg=Colors.UI_TEXT, bg=Colors.UI_BG)
    
    
    def render_system_log(self, console: tcod.console.Console, game: Game):
        """Render the system log on the right side."""
        # Draw log border
        for y in range(GameConfig.SCREEN_HEIGHT):
            console.print(GameConfig.GAME_AREA_WIDTH, y, '|', fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Log header
        console.print(GameConfig.GAME_AREA_WIDTH + 1, 0, "SYSTEM LOG", fg=Colors.ELECTRIC_PURPLE, bg=Colors.LOG_BG)
        console.print(GameConfig.GAME_AREA_WIDTH + 1, 1, "-" * (GameConfig.LOG_WIDTH - 1), fg=Colors.LOG_BORDER, bg=Colors.LOG_BG)
        
        # Clear log area
        for x in range(GameConfig.GAME_AREA_WIDTH + 1, GameConfig.SCREEN_WIDTH):
            for y in range(2, GameConfig.SCREEN_HEIGHT):
                console.print(x, y, ' ', fg=Colors.UI_TEXT, bg=Colors.LOG_BG)
        
        # Process and display messages
        self._render_log_messages(console, game)
    
    def _render_log_messages(self, console: tcod.console.Console, game: Game):
        """Render log messages with proper wrapping."""
        wrapped_lines = self._wrap_messages(game.message_log.messages)
        log_height = GameConfig.SCREEN_HEIGHT - 2
        visible_lines = wrapped_lines[-log_height:] if len(wrapped_lines) > log_height else wrapped_lines
        
        for i, (line, color) in enumerate(visible_lines):
            y_pos = 2 + i
            if y_pos < GameConfig.SCREEN_HEIGHT:
                console.print(GameConfig.GAME_AREA_WIDTH + 1, y_pos, line, fg=color, bg=Colors.LOG_BG)
    
    def _wrap_messages(self, messages: List[Tuple[str, Tuple[int, int, int]]]) -> List[Tuple[str, Tuple[int, int, int]]]:
        """Wrap long messages across multiple lines."""
        wrapped_lines = []
        max_msg_width = GameConfig.LOG_WIDTH - 2
        
        for message, color in messages:
            if len(message) <= max_msg_width:
                wrapped_lines.append((message, color))
            else:
                # Wrap long messages
                words = message.split(' ')
                current_line = ""
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if len(test_line) <= max_msg_width:
                        current_line = test_line
                    else:
                        if current_line:
                            wrapped_lines.append((current_line, color))
                        current_line = word
                
                if current_line:
                    wrapped_lines.append((current_line, color))
        
        return wrapped_lines

class MapRenderer:
    """Renders the game map and entities."""
    
    def render_map(self, console: tcod.console.Console, game: Game):
        """Render the complete game map."""
        try:
            camera_offset = self._calculate_camera_offset(game.player)
            vision_range = game.player.get_vision_range()
            
            # Render in layers for proper z-ordering
            self._render_terrain(console, game, camera_offset, vision_range)
            self._render_vision_overlays(console, game, camera_offset, vision_range)
            self._render_patrol_routes(console, game, camera_offset, vision_range)
            self._render_gateway(console, game, camera_offset, vision_range)
            self._render_enemies(console, game, camera_offset, vision_range)
            self._render_player(console, game, camera_offset)
            self._render_targeting_cursor(console, game, camera_offset)
            
        except Exception as e:
            # Fallback error display
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            console.print(1, 1, f"Map Error: {str(e)[:50]} (line {line_no})", fg=Colors.RED, bg=Colors.BLACK)
    
    def _calculate_camera_offset(self, player: Player) -> Position:
        """Calculate camera offset to center on player."""
        camera_x = max(0, min(GameConfig.MAP_WIDTH - GameConfig.GAME_AREA_WIDTH, 
                             player.x - GameConfig.GAME_AREA_WIDTH // 2))
        camera_y = max(0, min(GameConfig.MAP_HEIGHT - (GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1), 
                             player.y - (GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT - 1) // 2))
        return Position(camera_x, camera_y)
    
    def _render_terrain(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render basic terrain (floors, walls, items)."""
        for screen_x in range(GameConfig.GAME_AREA_WIDTH):
            for screen_y in range(1, GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                world_pos = Position(screen_x + camera_offset.x, screen_y - 1 + camera_offset.y)
                
                if world_pos.is_valid(GameConfig.MAP_WIDTH, GameConfig.MAP_HEIGHT):
                    distance = game.player.position.distance_to(world_pos)
                    
                    # Check if player can see this position
                    can_see = (distance <= vision_range and 
                              (game.player.can_see_through_walls() or 
                               game.game_map.has_line_of_sight(game.player.position, world_pos)))
                    
                    # Check if this tile has been explored (memory system)
                    explored = (world_pos.x, world_pos.y) in game.game_map.explored_tiles
                    
                    if can_see:
                        self._render_tile(console, screen_x, screen_y, world_pos, game)
                    elif explored:
                        # Render remembered tile with dimmed colors
                        self._render_remembered_tile(console, screen_x, screen_y, world_pos, game)
                    else:
                        # Fog of war
                        console.print(screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
                else:
                    # Outside map bounds
                    console.print(screen_x, screen_y, ' ', fg=Colors.BLACK, bg=Colors.BLACK)
    
    def _render_remembered_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game: Game):
        """Render a tile from memory with dimmed neon colors."""
        # Only render basic terrain in memory, not dynamic elements
        if game.game_map.is_wall(world_pos):
            # Dimmed neon wall
            console.print(screen_x, screen_y, '#', fg=(60, 70, 90), bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            # Darker purple shadow areas in memory
            console.print(screen_x, screen_y, '*', fg=(80, 40, 120), bg=Colors.BLACK)
        else:
            # Darker dots for remembered empty spaces
            console.print(screen_x, screen_y, '.', fg=(90, 90, 130), bg=Colors.BLACK)
    
    def _render_tile(self, console: tcod.console.Console, screen_x: int, screen_y: int, world_pos: Position, game: Game):
        """Render a single tile."""
        # SYMBOL CONVENTIONS:
        # - Letters (A-Z): Reserved for enemies only (Scanner=S, Patrol=P, Bot=B, etc.)
        # - ASCII symbols: Used for everything else (walls, items, terrain, etc.)
        # - NO unicode characters allowed for terminal compatibility
        
        # Priority order for tile rendering
        if game.game_map.is_wall(world_pos):
            console.print(screen_x, screen_y, '#', fg=Colors.WALL, bg=Colors.BLACK)
        elif game.game_map.is_cooling_node(world_pos):
            console.print(screen_x, screen_y, '~', fg=Colors.CYAN, bg=Colors.BLACK)
        elif game.game_map.is_cpu_recovery_node(world_pos):
            console.print(screen_x, screen_y, '+', fg=Colors.ELECTRIC_BLUE, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.data_patches:
            patch = game.game_map.data_patches[(world_pos.x, world_pos.y)]
            color = self._get_patch_color(patch.color)
            console.print(screen_x, screen_y, '!', fg=color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.exploit_pickups:
            console.print(screen_x, screen_y, '&', fg=Colors.MAGENTA, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.permanent_upgrades:
            upgrade_key = game.game_map.permanent_upgrades[(world_pos.x, world_pos.y)]
            upgrade = GameUpgrades.UPGRADES[upgrade_key]
            color = self._get_upgrade_color(upgrade.color)
            console.print(screen_x, screen_y, upgrade.symbol, fg=color, bg=Colors.BLACK)
        elif (world_pos.x, world_pos.y) in game.game_map.story_fragments:
            # Story fragment - glowing/pulsing appearance
            console.print(screen_x, screen_y, '?', fg=Colors.CYAN, bg=Colors.BLACK)
        elif game.game_map.is_shadow(world_pos):
            console.print(screen_x, screen_y, '*', fg=(150, 80, 200), bg=Colors.BLACK)
        else:
            console.print(screen_x, screen_y, '.', fg=Colors.FLOOR, bg=Colors.BLACK)
    
    def _get_patch_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple for data patch."""
        color_map = {
            'crimson': Colors.NEON_PINK, 'azure': Colors.ELECTRIC_BLUE, 'emerald': Colors.ACID_GREEN,
            'golden': Colors.YELLOW, 'violet': Colors.ELECTRIC_PURPLE, 'silver': Colors.CYAN
        }
        return color_map.get(color_name, Colors.CYAN)
    
    def _get_upgrade_color(self, color_name: str) -> Tuple[int, int, int]:
        """Get color tuple for permanent upgrade."""
        color_map = {
            'BRIGHT_BLUE': Colors.ELECTRIC_BLUE,
            'BRIGHT_GREEN': Colors.ACID_GREEN, 
            'BRIGHT_CYAN': Colors.CYAN
        }
        return color_map.get(color_name, Colors.WHITE)
    
    def _render_vision_overlays(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render enemy vision range overlays."""
        if game.player.is_invisible():
            return
        
        network_scan_active = game.game_state.network_scan_turns > 0
        
        for enemy in game.enemies:
            if enemy.disabled_turns > 0:
                continue
            
            # Show vision overlays for visible enemies OR if Network Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
            
            if can_see_enemy or network_scan_active:
                overlay_color = self._get_vision_overlay_color(enemy.state)
                
                # If revealed by network scan, make overlay more translucent
                if network_scan_active and not can_see_enemy:
                    overlay_color = tuple(c // 2 for c in overlay_color)  # Make it dimmer
                
                self._render_enemy_vision_range(console, enemy, camera_offset, overlay_color)
    
    def _get_vision_overlay_color(self, enemy_state: EnemyState) -> Tuple[int, int, int]:
        """Get vision overlay color based on enemy state."""
        if enemy_state == EnemyState.HOSTILE:
            return Colors.VISION_HOSTILE
        elif enemy_state == EnemyState.ALERT:
            return Colors.VISION_ALERT
        else:
            return Colors.VISION_UNAWARE
    
    def _render_enemy_vision_range(self, console: tcod.console.Console, enemy: Enemy, camera_offset: Position, overlay_color: Tuple[int, int, int]):
        """Render vision range for a single enemy."""
        for dx in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
            for dy in range(-enemy.type_data.vision, enemy.type_data.vision + 1):
                # Use Euclidean distance to match the actual detection logic
                if dx*dx + dy*dy <= enemy.type_data.vision*enemy.type_data.vision:
                    screen_x = enemy.x - camera_offset.x + dx
                    screen_y = enemy.y - camera_offset.y + dy + 1
                    
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, screen_x, screen_y, overlay_color)
    
    def _safely_overlay_tile(self, console: tcod.console.Console, x: int, y: int, bg_color: Tuple[int, int, int]):
        """Safely overlay background color on existing tile."""
        try:
            current_char = console.ch[x, y]
            if current_char != ord(' '):  # Don't overlay fog of war
                current_fg = console.fg[x, y]
                if hasattr(current_fg, '__iter__') and len(current_fg) >= 3:
                    fg_tuple = tuple(current_fg[:3])
                    console.print(x, y, chr(current_char), fg=fg_tuple, bg=bg_color)
        except (IndexError, ValueError) as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)
            line_no = tb[-1].lineno if tb else "?"
            # Silent fail for overlay errors, but could log line_no if needed for debugging
            pass
    
    def _render_patrol_routes(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render next 3 predicted moves for all moving enemies."""
        
        network_scan_active = game.game_state.network_scan_turns > 0
        
        for enemy in game.enemies:
            # Show patrol routes for visible enemies OR if Network Scan is active
            can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
            
            # Show movement intentions only for visible enemies or during network scan
            if can_see_enemy or network_scan_active:
                next_positions = game.get_enemy_next_positions(enemy, 3)
                
                for i, point in enumerate(next_positions):
                    screen_x = point.x - camera_offset.x
                    screen_y = point.y - camera_offset.y + 1
                    if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                        1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        # Preserve existing background color if present (e.g., vision overlay)
                        try:
                            current_bg = tuple(console.bg[screen_x, screen_y][:3])
                            # Use current background if it's not black, otherwise use black
                            bg_color = current_bg if current_bg != (0, 0, 0) else Colors.BLACK
                        except (IndexError, AttributeError):
                            bg_color = Colors.BLACK
                        
                        # Check if background is bright (sum of RGB values > 30 indicates brighter area)
                        bg_brightness = sum(bg_color) if bg_color != Colors.BLACK else 0
                        is_bright_area = bg_brightness > 30
                        
                        # Large bright yellow shapes for all enemy movement prediction
                        if i == 0:
                            # Next immediate move - brightest and largest
                            color = (255, 255, 50)
                            symbol = ','
                        elif i == 1:
                            # Second move - slightly dimmer but still bright
                            color = (240, 240, 30)
                            symbol = ','
                        else:
                            # Third+ moves - still bright yellow
                            color = (220, 220, 20)
                            symbol = ','
                        console.print(screen_x, screen_y, symbol, fg=color, bg=bg_color)
    
    def _render_gateway(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render the level gateway."""
        if not game.game_map.gateway:
            return
        
        screen_x = game.game_map.gateway.x - camera_offset.x
        screen_y = game.game_map.gateway.y - camera_offset.y + 1
        
        if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            distance = game.player.position.distance_to(game.game_map.gateway)
            # Check if player can see the gateway (respecting walls)
            can_see = (distance <= vision_range and 
                      (game.player.can_see_through_walls() or 
                       game.game_map.has_line_of_sight(game.player.position, game.game_map.gateway)))
            if can_see:
                console.print(screen_x, screen_y, '>', fg=Colors.GATEWAY, bg=Colors.BLACK)
    
    def _render_enemies(self, console: tcod.console.Console, game: Game, camera_offset: Position, vision_range: int):
        """Render all enemies and their last known positions."""
        # First, render last known positions as ghosts
        for enemy_id, (position, turn_seen) in game.game_map.last_known_enemy_positions.items():
            # Find if this enemy is still alive and currently visible
            current_enemy = None
            currently_visible = False
            for enemy in game.enemies:
                if enemy.id == enemy_id:
                    current_enemy = enemy
                    if game.player.can_see_enemy(enemy, game.game_map):
                        currently_visible = True
                    break
            
            # Only show ghost if enemy is not currently visible and was seen recently
            if not currently_visible and turn_seen > game.turn - 20:  # Show ghost for 20 turns
                screen_x = position.x - camera_offset.x
                screen_y = position.y - camera_offset.y + 1
                
                if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                    1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                    if current_enemy:
                        # Dimmed ghost of living enemy
                        ghost_color = tuple(c // 3 for c in current_enemy.get_color())
                        console.print(screen_x, screen_y, '?', fg=ghost_color, bg=Colors.BLACK)
        
        # Then render currently visible enemies
        for enemy in game.enemies:
            screen_x = enemy.x - camera_offset.x
            screen_y = enemy.y - camera_offset.y + 1
            
            if (0 <= screen_x < GameConfig.GAME_AREA_WIDTH and 
                1 <= screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                # Check if Network Scan is active (shows all enemies)
                network_scan_active = game.game_state.network_scan_turns > 0
                can_see_enemy = game.player.can_see_enemy(enemy, game.game_map)
                
                if can_see_enemy or network_scan_active:
                    if network_scan_active and not can_see_enemy:
                        # Network scan reveals enemy with special highlighting
                        console.print(screen_x, screen_y, enemy.type_data.symbol, 
                                    fg=Colors.CYAN, bg=(20, 0, 20))  # Cyan text on dark purple bg
                    else:
                        # Normal enemy rendering
                        console.print(screen_x, screen_y, enemy.type_data.symbol, 
                                    fg=enemy.get_color(), bg=Colors.BLACK)
    
    def _render_player(self, console: tcod.console.Console, game: Game, camera_offset: Position):
        """Render the player character."""
        player_screen_x = game.player.x - camera_offset.x
        player_screen_y = game.player.y - camera_offset.y + 1
        
        if (0 <= player_screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= player_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            player_color = self._get_player_color(game.player)
            console.print(player_screen_x, player_screen_y, '@', fg=player_color, bg=Colors.BLACK)
    
    def _get_player_color(self, player: Player) -> Tuple[int, int, int]:
        """Get player color based on current state."""
        if player.is_invisible():
            return Colors.BLUE
        elif player.temporary_effects['speed_boost_turns'] > 0:
            return Colors.YELLOW
        elif player.heat >= 90:
            return Colors.RED
        else:
            return Colors.PLAYER
    
    def _render_targeting_cursor(self, console: tcod.console.Console, game: Game, camera_offset: Position):
        """Render targeting cursor and range indicator."""
        if not game.targeting_mode:
            return
        
        cursor_screen_x = game.cursor_position.x - camera_offset.x
        cursor_screen_y = game.cursor_position.y - camera_offset.y + 1
        
        if (0 <= cursor_screen_x < GameConfig.GAME_AREA_WIDTH and 
            1 <= cursor_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
            console.print(cursor_screen_x, cursor_screen_y, 'X', fg=Colors.RED, bg=Colors.BLACK)
        
        # Show range indicator
        if game.targeting_exploit in GameData.EXPLOITS:
            exploit = GameData.EXPLOITS[game.targeting_exploit]
            self._render_targeting_range(console, game.player.position, exploit.range, camera_offset)
    
    def _render_targeting_range(self, console: tcod.console.Console, center: Position, range_val: int, camera_offset: Position):
        """Render targeting range indicator."""
        for dx in range(-range_val, range_val + 1):
            for dy in range(-range_val, range_val + 1):
                if dx*dx + dy*dy <= range_val*range_val:
                    range_screen_x = center.x - camera_offset.x + dx
                    range_screen_y = center.y - camera_offset.y + dy + 1
                    
                    if (0 <= range_screen_x < GameConfig.GAME_AREA_WIDTH and 
                        1 <= range_screen_y < GameConfig.SCREEN_HEIGHT - GameConfig.PANEL_HEIGHT):
                        self._safely_overlay_tile(console, range_screen_x, range_screen_y, (40, 40, 40))

# ============================================================================
# MAIN GAME LOOP AND INITIALIZATION
# ============================================================================

def initialize_tcod_context():
    """Initialize tcod context with fallback handling."""
    tileset = None
    try:

        # Try to load the preferred tileset
        tileset = tcod.tileset.load_tilesheet(
            "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
        ) 
        tileset = tcod.tileset.load_truetype_font("Orbitron-VariableFont_wght.ttf", 16, 16)


    except (FileNotFoundError, ImportError, Exception) as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        line_no = tb[-1].lineno if tb else "?"
        logging.error(f"Tileset loading error: {e} (line {line_no})")
        try:
            # Try default tileset
            # Use a simple built-in tileset
            tileset = None  # Let tcod use its default
        except Exception as e2:
            tb2 = traceback.extract_tb(e2.__traceback__)
            line_no2 = tb2[-1].lineno if tb2 else "?"
            logging.error(f"Default tileset error: {e2} (line {line_no2})")
            # Use built-in fallback
            pass
    
    context_args = {
        "columns": GameConfig.SCREEN_WIDTH,
        "rows": GameConfig.SCREEN_HEIGHT,
        "title": "Rogue Signal Protocol v51 - Enhanced Combat & Inventory",
        "vsync": True,
        "sdl_window_flags": 160
    }
    
    if tileset:
        context_args["tileset"] = tileset
    
    return tcod.context.new(**context_args)


# ============================================================================
# MAIN MENU SYSTEM
# ============================================================================

class MainMenu:
    """Main menu for New Game/Continue options."""
    
    def __init__(self):
        self.selected_option = 0
        self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"] if SaveGameManager.save_exists() else ["New Game", "Settings", "Help", "Lore", "Exit"]
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game
    
    def refresh_options(self, show_continue: bool = True) -> None:
        """Refresh menu options. Set show_continue=False when accessed from mid-game."""
        if show_continue and SaveGameManager.save_exists():
            self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"]
            self.mid_game_mode = False
        else:
            self.options = ["New Game", "Settings", "Help", "Lore", "Exit"]
            self.mid_game_mode = not show_continue  # True when accessed from mid-game
        # Reset selection to prevent index out of bounds
        self.selected_option = 0
        # Reset warning state when refreshing options
        self.show_warning = False
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the main menu."""
        console.clear()
        
        if self.show_warning:
            self._render_warning_dialog(console)
        else:
            self._render_main_menu(console)
    
    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu screen."""
        # Title
        title = "ROGUE SIGNAL PROTOCOL"
        subtitle = "Cyberpunk Stealth Infiltration"
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 8,
            title, fg=Colors.CYAN
        )
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2, 9,
            subtitle, fg=Colors.CYAN
        )
        
        # Version and build info
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - 10, 11,
            "v1.0 - Enhanced Edition", fg=(128, 128, 128)
        )
        
        # Menu options
        start_y = 16
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            prefix = "> " if i == self.selected_option else "  "
            console.print(
                GameConfig.SCREEN_WIDTH // 2 - len(option) // 2 - 1, start_y + i * 2,
                f"{prefix}{option}", fg=color
            )
        
        # Save file info
        if SaveGameManager.save_exists():
            save_timestamp = SaveGameManager.get_save_timestamp()
            if save_timestamp:
                console.print(
                    GameConfig.SCREEN_WIDTH // 2 - 15, start_y + len(self.options) * 2 + 2,
                    "Save file found - Continue to resume", fg=Colors.GREEN
                )
                console.print(
                    GameConfig.SCREEN_WIDTH // 2 - 12, start_y + len(self.options) * 2 + 3,
                    f"Last saved: {save_timestamp}", fg=Colors.LIGHT_GRAY
                )
        
        # Controls
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - 15, GameConfig.SCREEN_HEIGHT - 6,
            "UP/DOWN or W/S: Navigate", fg=(128, 128, 128)
        )
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - 10, GameConfig.SCREEN_HEIGHT - 5,
            "Enter: Select", fg=(128, 128, 128)
        )
        
        # Story fragments info
        if SaveGameManager.save_exists():
            story_manager = StoryFragmentManager()
            discovered, total = story_manager.get_fragment_count()
            console.print(
                GameConfig.SCREEN_WIDTH // 2 - 12, GameConfig.SCREEN_HEIGHT - 2,
                f"Story Fragments: {discovered}/{total}", fg=Colors.CYAN
            )
    
    def _render_warning_dialog(self, console: tcod.console.Console) -> None:
        """Render save deletion warning dialog."""
        # Dim background
        for x in range(GameConfig.SCREEN_WIDTH):
            for y in range(GameConfig.SCREEN_HEIGHT):
                console.print(x, y, ' ', fg=Colors.BLACK, bg=(64, 64, 64))
        
        # Dialog box
        dialog_width = 50
        dialog_height = 18
        start_x = (GameConfig.SCREEN_WIDTH - dialog_width) // 2
        start_y = (GameConfig.SCREEN_HEIGHT - dialog_height) // 2
        
        # Draw dialog background
        for x in range(start_x, start_x + dialog_width):
            for y in range(start_y, start_y + dialog_height):
                console.print(x, y, ' ', fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Draw border
        for x in range(start_x, start_x + dialog_width):
            console.print(x, start_y, '=', fg=Colors.RED, bg=Colors.BLACK)
            console.print(x, start_y + dialog_height - 1, '=', fg=Colors.RED, bg=Colors.BLACK)
        for y in range(start_y, start_y + dialog_height):
            console.print(start_x, y, '|', fg=Colors.RED, bg=Colors.BLACK)
            console.print(start_x + dialog_width - 1, y, '|', fg=Colors.RED, bg=Colors.BLACK)
        
        # Title
        console.print(start_x + dialog_width // 2 - 7, start_y + 2, "WARNING", fg=Colors.RED, bg=Colors.BLACK)
        
        # Message
        messages = [
            "Starting a new game will delete your",
            "current save file permanently.",
            "",
            "This will erase all progress including:",
            "• Current level and character state",
            "• Inventory and upgrades", 
            "• Story fragments remain safe",
            "",
            "Are you sure you want to continue?"
        ]
        
        for i, msg in enumerate(messages):
            console.print(start_x + 2, start_y + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options
        options = ["Yes, Delete Save", "No, Go Back"]
        for i, option in enumerate(options):
            color = Colors.RED if i == self.warning_selection and i == 0 else Colors.YELLOW if i == self.warning_selection else Colors.WHITE
            prefix = "> " if i == self.warning_selection else "  "
            console.print(
                start_x + dialog_width // 2 - len(option) // 2 - 1, 
                start_y + dialog_height - 3 + i,
                f"{prefix}{option}", fg=color, bg=Colors.BLACK
            )
    
    def handle_input(self, event) -> str:
        """Handle menu input. Returns action: 'continue', 'new_game', 'exit', or ''."""
        if self.show_warning:
            return self._handle_warning_input(event)
        else:
            return self._handle_menu_input(event)
    
    def _handle_menu_input(self, event) -> str:
        """Handle main menu input."""
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.options)):
            return ""
        
        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            option = self.options[self.selected_option]
            if option == "Continue Game":
                return "continue"
            elif option == "New Game":
                if SaveGameManager.save_exists() and not self.mid_game_mode:
                    self.show_warning = True
                    self.warning_selection = 1  # Default to "No"
                else:
                    return "new_game"
            elif option == "Settings":
                return "settings"
            elif option == "Help":
                return "help"
            elif option == "Lore":
                return "lore"
            elif option == "Exit":
                return "exit"
        # ESC disabled on main menu to prevent accidental exit
        
        return ""
    
    def _handle_warning_input(self, event) -> str:
        """Handle warning dialog input."""
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_dialog_navigation(self, event):
            return ""
        
        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            if self.warning_selection == 0:  # Yes, Delete Save
                SaveGameManager.delete_save()
                return "new_game"
            else:  # No, Go Back
                self.show_warning = False
        elif UniversalInputHandler.is_escape_key(event):
            self.show_warning = False
        
        return ""


class LoreMenu:
    """Lore viewer menu for main menu."""
    
    def __init__(self):
        self.story_fragment_manager = None
        self.lore_viewer_selection = 0
        self.lore_viewer_mode = "list"  # "list" or "reading"
    
    def _load_story_fragments(self):
        """Load story fragment manager from save data."""
        if self.story_fragment_manager is None:
            self.story_fragment_manager = StoryFragmentManager()
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the lore viewer screen."""
        console.clear()
        
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        discovered_count, total_count = self.story_fragment_manager.get_fragment_count()
        
        if self.lore_viewer_mode == "reading" and discovered_fragments:
            self._render_reading_mode(console, discovered_fragments)
        else:
            self._render_list_mode(console, discovered_fragments, discovered_count, total_count)
    
    def _render_list_mode(self, console, discovered_fragments, discovered_count, total_count):
        """Render lore fragment list."""
        title = f"DISCOVERED LORE FRAGMENTS ({discovered_count}/{total_count})"
        console.print(GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        if not discovered_fragments:
            console.print(2, 5, "No lore fragments discovered yet.", fg=Colors.WHITE)
            console.print(2, 6, "Start playing to discover the story!", fg=Colors.WHITE)
            console.print(2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return to main menu", fg=Colors.LIGHT_GRAY)
            return
        
        start_y = 5
        for i, (fragment_index, fragment_text) in enumerate(discovered_fragments):
            # Clamp selection
            if self.lore_viewer_selection >= len(discovered_fragments):
                self.lore_viewer_selection = len(discovered_fragments) - 1
            
            is_selected = (i == self.lore_viewer_selection)
            color = Colors.CYAN if is_selected else Colors.WHITE
            prefix = "> " if is_selected else "  "
            
            # Show first line of fragment as title
            first_line = fragment_text.split('\n')[0][:60]
            console.print(2, start_y + i, f"{prefix}Fragment {fragment_index + 1}: {first_line}", fg=color)
        
        # Instructions
        console.print(2, GameConfig.SCREEN_HEIGHT - 4, "Up/Down: Navigate  Enter: Read  Esc: Back", fg=Colors.LIGHT_GRAY)
    
    def _render_reading_mode(self, console, discovered_fragments):
        """Render individual fragment for reading."""
        if self.lore_viewer_selection >= len(discovered_fragments):
            self.lore_viewer_mode = "list"
            return
            
        fragment_index, fragment_text = discovered_fragments[self.lore_viewer_selection]
        
        title = f"DATA FRAGMENT {fragment_index + 1}"
        console.print(GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        # Render fragment text with wrapping
        lines = fragment_text.split('\n')
        y = 5
        for line in lines:
            if y < GameConfig.SCREEN_HEIGHT - 4:
                # Simple word wrapping
                if len(line) <= GameConfig.SCREEN_WIDTH - 4:
                    console.print(2, y, line, fg=Colors.WHITE)
                    y += 1
                else:
                    # Basic word wrapping for long lines
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= GameConfig.SCREEN_WIDTH - 4:
                            current_line += (" " if current_line else "") + word
                        else:
                            console.print(2, y, current_line, fg=Colors.WHITE)
                            y += 1
                            current_line = word
                            if y >= GameConfig.SCREEN_HEIGHT - 4:
                                break
                    if current_line and y < GameConfig.SCREEN_HEIGHT - 4:
                        console.print(2, y, current_line, fg=Colors.WHITE)
                        y += 1
        
        console.print(2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return to list", fg=Colors.LIGHT_GRAY)
    
    def handle_input(self, event) -> str:
        """Handle lore menu input with proper navigation."""
        self._load_story_fragments()
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        
        if not discovered_fragments:
            # No fragments - any key returns to main menu
            if UniversalInputHandler.handle_any_key_screen(event):
                return "back"
            return ""
        
        if self.lore_viewer_mode == "list":
            # Handle navigation using universal handler
            if UniversalInputHandler.handle_list_navigation(
                self, event, len(discovered_fragments), False, self._navigate_lore_selection
            ):
                return ""
            
            # Handle selection
            if UniversalInputHandler.is_confirm_key(event):
                self.lore_viewer_mode = "reading"
                return ""
            elif UniversalInputHandler.is_escape_key(event):
                return "back"
        
        elif self.lore_viewer_mode == "reading":
            # Any key except ESC returns to list
            if UniversalInputHandler.is_escape_key(event):
                return "back"
            else:
                self.lore_viewer_mode = "list"
                return ""
        
        return ""
    
    def _navigate_lore_selection(self, direction: int):
        """Navigate lore selection."""
        discovered_fragments = self.story_fragment_manager.get_discovered_fragments()
        if discovered_fragments:
            if direction == -1:
                self.lore_viewer_selection = max(0, self.lore_viewer_selection - 1)
            else:
                self.lore_viewer_selection = min(len(discovered_fragments) - 1, self.lore_viewer_selection + 1)


class HelpMenu:
    """Help menu displaying game information."""
    
    def __init__(self):
        pass
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the help screen."""
        console.clear()
        
        # Title
        title = "ROGUE SIGNAL PROTOCOL - HELP"
        console.print(GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        y = 5
        help_sections = self._get_help_sections()
        
        for text, color in help_sections:
            if y < GameConfig.SCREEN_HEIGHT - 2:
                console.print(2, y, text, fg=color)
                y += 1
        
        # Back instruction
        console.print(2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return to main menu", fg=Colors.LIGHT_GRAY)
    
    def handle_input(self, event) -> str:
        """Handle help menu input. Returns 'back' on any key press."""
        if UniversalInputHandler.handle_any_key_screen(event):
            return "back"
        return ""
    
    def _get_help_sections(self):
        """Get help sections with text and colors."""
        return [
            ("OBJECTIVE:", Colors.CYAN),
            ("  Navigate network levels using stealth", Colors.WHITE),
            ("  Reach the gateway (>) to advance", Colors.WHITE),
            ("  Avoid detection by enemies and Admin Avatar", Colors.WHITE),
            ("  Collect data patches, exploits, and upgrades", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MOVEMENT & CONTROLS:", Colors.CYAN),
            ("  Arrow Keys, WASD, or Numpad: Move/Navigate", Colors.WHITE),
            ("  1-9: Use loaded exploits (requires targeting)", Colors.WHITE),
            ("  I: Inventory (manage data patches & exploits)", Colors.WHITE),
            ("  Tab: Toggle vision overlays", Colors.WHITE),
            ("  L: View discovered lore fragments", Colors.WHITE),
            ("  ESC: Pause menu / Close screens", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MAP SYMBOLS:", Colors.CYAN),
            ("  @: Player (you)", Colors.PLAYER),
            ("  #: Walls (impassable)", Colors.WHITE),
            ("  *: Shadows (stealth zones, purple)", Colors.FLOOR),
            ("  >: Gateway to next level", Colors.ACID_GREEN),
            ("  ?: Story fragments (lore)", Colors.CYAN),
            ("", Colors.WHITE),
            
            ("ENEMY TYPES (HP, Vision, Behavior, Damage):", Colors.CYAN),
            ("  S: Scanner (35hp, 5 vision, static, no attack)", Colors.ORANGE),
            ("  P: Patrol (40hp, 4 vision, linear routes, 15 dmg)", Colors.ORANGE),
            ("  B: Bot (25hp, 3 vision, random movement, 8 dmg)", Colors.ORANGE),
            ("  F: Firewall (80hp, 6 vision, static, no attack)", Colors.RED),
            ("  H: Hunter (50hp, 6 vision, seeks players, 22 dmg)", Colors.RED),
            ("  A: Admin Avatar (250hp, 8 vision, perfect tracking, 45 dmg)", Colors.RED),
            ("", Colors.WHITE),
            
            ("ITEMS & PICKUPS:", Colors.CYAN),
            ("  !: Data patches (boost CPU, RAM, heat capacity)", Colors.ELECTRIC_PURPLE),
            ("  &: Exploits (combat & utility abilities)", Colors.NEON_PINK),
            ("  [/]/=: Permanent upgrades (Memory/CPU/Heat)", Colors.ELECTRIC_BLUE),
            ("  +: CPU recovery nodes (restore health)", Colors.ACID_GREEN),
            ("  ~: Cooling nodes (reduce heat)", Colors.ELECTRIC_BLUE),
            ("", Colors.WHITE),
            
            ("CORE MECHANICS:", Colors.CYAN),
            ("  Heat: Builds from exploit usage, causes damage at 100°C+", Colors.WHITE),
            ("  Detection: Increases when spotted, Admin spawns at threshold", Colors.WHITE),
            ("  CPU: Your health - if it reaches 0, you die permanently", Colors.WHITE),
            ("  RAM: Limits how many exploits you can equip (max 5)", Colors.WHITE),
            ("  Shadows: Hide in purple * tiles to avoid enemy detection", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("COMBAT EXPLOITS:", Colors.CYAN),
            ("  Buffer Overflow: 40 dmg melee (1 tile range)", Colors.WHITE),
            ("  Code Injection: 25 dmg ranged (5 tile range)", Colors.WHITE),
            ("  System Crash: 30 dmg area (disables enemies 4 turns)", Colors.WHITE),
            ("  EMP Burst: 20 dmg area (disables all nearby enemies)", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("STEALTH & UTILITY EXPLOITS:", Colors.CYAN),
            ("  Shadow Step: Teleport to shadow zones (6 tile range)", Colors.WHITE),
            ("  Data Mimic: Become invisible (5 turns)", Colors.WHITE),
            ("  Noise Maker: Create distraction (8 turn duration)", Colors.WHITE),
            ("  Network Scan: Reveal all enemies, vision & paths (5 turns)", Colors.WHITE),
            ("  Log Wiper: Reduce detection level (-50%)", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("SURVIVAL TIPS:", Colors.CYAN),
            ("  Use shadows frequently - stealth is key", Colors.WHITE),
            ("  Monitor heat and detection levels constantly", Colors.WHITE),
            ("  Plan exploit usage - heat management is critical", Colors.WHITE),
            ("  Use CPU nodes when low on health", Colors.WHITE),
            ("  Admin Avatar spawns at high detection - be careful!", Colors.WHITE),
            ("  Save cooling nodes for emergencies", Colors.WHITE),
        ]


class SettingsMenu:
    """Settings menu for audio, graphics, and help options."""
    
    def __init__(self, settings: GameSettings):
        self.settings = settings
        self.selected_option = 0
        self.options = [
            {"name": "Master Volume", "type": "volume", "key": "master"},
            {"name": "SFX Volume", "type": "volume", "key": "sfx"},
            {"name": "Music Volume", "type": "volume", "key": "music"},
            {"name": "Graphics Mode", "type": "toggle", "key": "graphics_mode", 
             "values": ["ASCII", "Graphics"]},
            {"name": "Back", "type": "action"}
        ]
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the settings menu."""
        console.clear()
        
        
        # Title
        title = "SETTINGS"
        console.print(
            GameConfig.SCREEN_WIDTH // 2 - len(title) // 2,
            5,
            title,
            Colors.WHITE
        )
        
        # Options
        start_y = 10
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            
            # Option name
            console.print(10, start_y + i * 2, option["name"], color)
            
            # Option value
            if option["type"] == "volume":
                volume_percent = self.settings.get_volume_percent(option["key"])
                bar_length = 20
                filled_length = int(bar_length * volume_percent / 100)
                
                # Volume bar
                bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                console.print(30, start_y + i * 2, f"{bar} {volume_percent}%", color)
                
            elif option["type"] == "toggle":
                if option["key"] == "graphics_mode":
                    current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "ASCII"
                    console.print(30, start_y + i * 2, f"< {current_value} >", color)
        
        # Instructions
        instructions = [
            "Arrow Keys/WASD: Navigate",
            "Left/Right or A/D: Adjust volumes/toggle options", 
            "Enter: Select",
            "Escape: Back"
        ]
        
        for i, instruction in enumerate(instructions):
            console.print(
                GameConfig.SCREEN_WIDTH // 2 - len(instruction) // 2,
                GameConfig.SCREEN_HEIGHT - 8 + i,
                instruction,
                Colors.LIGHT_GRAY
            )
    
    def handle_input(self, event) -> str:
        """Handle settings menu input. Returns action: 'back', 'exit', or ''."""
        
        # Handle navigation using universal handler
        if UniversalInputHandler.handle_list_navigation(self, event, len(self.options)):
            return ""
        
        # Handle selection
        if UniversalInputHandler.is_confirm_key(event):
            option = self.options[self.selected_option]
            if option["type"] == "action":
                if option["name"] == "Back":
                    return "back"
        
        # Handle value adjustment using universal handler
        if UniversalInputHandler.handle_value_adjustment(self, event, self._adjust_setting):
            return ""
        
        # Handle escape
        if UniversalInputHandler.is_escape_key(event):
            return "back"
        
        return ""
    
    def _adjust_setting(self, direction: int):
        """Adjust the currently selected setting."""
        option = self.options[self.selected_option]
        
        if option["type"] == "volume":
            current_percent = self.settings.get_volume_percent(option["key"])
            new_percent = max(0, min(100, current_percent + (direction * 5)))
            self.settings.set_volume_percent(option["key"], new_percent)
            # Note: Sound manager will be updated when the game is created with these settings
            
        elif option["type"] == "toggle":
            if option["key"] == "graphics_mode":
                current_mode = self.settings.graphics_mode
                new_mode = "graphics" if current_mode == "ascii" else "ascii"
                self.settings.set_graphics_mode(new_mode)
    




def initialize_game_systems(settings: GameSettings):
    """Initialize menu systems and return menu objects."""
    return {
        'main_menu': MainMenu(),
        'settings_menu': SettingsMenu(settings),
        'help_menu': HelpMenu(),
        'lore_menu': LoreMenu()
    }

def handle_menu_navigation(console, context, menus, settings):
    """Handle the main menu navigation loop."""
    main_menu = menus['main_menu']
    main_menu.refresh_options(show_continue=True)
    current_menu = main_menu
    
    while True:
        current_menu.render(console)
        context.present(console)
        
        for event in tcod.event.wait():
            if event.type == "QUIT":
                return None, True  # game=None, should_exit=True
            elif event.type == "KEYDOWN":
                action = current_menu.handle_input(event)
                
                if action == "exit":
                    return None, True  # game=None, should_exit=True
                elif action == "settings":
                    current_menu = menus['settings_menu']
                elif action == "help":
                    current_menu = menus['help_menu']
                elif action == "lore":
                    current_menu = menus['lore_menu']
                elif action == "back":
                    current_menu = main_menu
                elif action == "continue":
                    game = Game(load_save=True, settings=settings)
                    return game, False
                elif action == "new_game":
                    game = Game(load_save=False, settings=settings)
                    return game, False

def show_welcome_messages(game):
    """Show initial welcome messages for new games."""
    if not SaveGameManager.save_exists():
        game.message_log.add_message("Welcome to Rogue Signal Protocol v1.0!")
        game.message_log.add_message("Enhanced Edition with sound, settings, and story fragments")
        game.message_log.add_message("Navigate using stealth")
        game.message_log.add_message("Reach the gateway (>)")
        game.message_log.add_message("Hide in shadows (.) to avoid detection")
        game.message_log.add_message("Press 'L' to view discovered lore")
        game.message_log.add_message("Starting Corporate Network infiltration...")

def handle_game_input_events(event, game, input_handler):
    """Handle game input events and return (should_continue, game)."""
    if event.type == "QUIT":
        game.auto_save()
        game.sound_manager.cleanup()
        return False, None  # Exit program
    elif event.type == "KEYDOWN":
        if event.sym == tcod.event.KeySym.ESCAPE:
            # Check if any UI states are open - close those first
            if (game.show_story_fragment is not None or 
                game.show_lore_viewer or 
                game.show_help or 
                game.show_inventory or 
                game.targeting_mode):
                input_handler._handle_escape()
            else:
                # No UI states open, auto-save and go to main menu
                game.auto_save()
                return True, None  # Return to main menu
        else:
            should_continue = input_handler.handle_keydown(event)
            if not should_continue:
                # Player is dead and pressed ESC - return to main menu
                return True, None
    return True, game

def handle_error_screen(console, context, error_message, line_no):
    """Display error screen and wait for user input."""
    console.clear()
    console.print(1, 1, f"Error: {str(error_message)[:50]} (line {line_no})", fg=Colors.RED)
    console.print(1, 2, "Press ESC to exit", fg=Colors.WHITE)
    context.present(console)
    
    for event in tcod.event.wait():
        if event.type == "QUIT" or (event.type == "KEYDOWN" and event.sym == tcod.event.KeySym.ESCAPE):
            return True
    return False

def main():
    """Main game loop with main menu and save/load functionality."""
    # Initialize JSON configuration system
    GameConfig.load_from_json()
    
    try:
        with initialize_tcod_context() as context:
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT, order='F')
            
            settings = GameSettings()
            menus = initialize_game_systems(settings)
            game = None
            
            while True:
                if game is None:
                    game, should_exit = handle_menu_navigation(console, context, menus, settings)
                    if should_exit:
                        return
                    
                    # Initialize game rendering systems
                    renderer = Renderer()
                    input_handler = InputHandler(game)
                    show_welcome_messages(game)

                # Main game loop
                while game is not None:
                    try:
                        game.sound_manager.update()
                        renderer.render_game(console, game)
                        context.present(console)
                        
                        # Handle input events
                        for event in tcod.event.wait():
                            should_continue, game = handle_game_input_events(event, game, input_handler)
                            if not should_continue:
                                return  # Exit program
                            if game is None:
                                break  # Return to main menu
                        
                    except Exception as e:
                        import traceback
                        tb = traceback.extract_tb(e.__traceback__)
                        line_no = tb[-1].lineno if tb else "?"
                        logging.error(f"Rendering error: {e} (line {line_no})")
                        
                        if handle_error_screen(console, context, e, line_no):
                            return
    
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        line_no = tb[-1].lineno if tb else "?"
        logging.critical(f"Critical error: {e} (line {line_no})")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Game interrupted by user")
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()