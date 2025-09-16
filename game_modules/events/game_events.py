"""
Game-specific event definitions.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict
import time

from .event_manager import Event
from ..core.data_structures import Position


@dataclass
class PlayerMoveEvent(Event):
    """Event fired when player moves."""
    old_position: Position
    new_position: Position
    movement_type: str = "walk"  # walk, teleport, etc.
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    handled: bool = False
    
    def get_event_type(self) -> str:
        return "player_move"


@dataclass
class EnemyDefeatedEvent(Event):
    """Event fired when an enemy is defeated."""
    enemy_id: int
    enemy_type: str
    enemy_position: Position
    defeated_by: str = "player"  # player, environment, etc.
    experience_gained: int = 0
    
    def get_event_type(self) -> str:
        return "enemy_defeated"


@dataclass
class ItemCollectedEvent(Event):
    """Event fired when player collects an item."""
    item_name: str
    item_type: str
    position: Position
    player_position: Position
    auto_collected: bool = False
    
    def get_event_type(self) -> str:
        return "item_collected"


@dataclass
class ExploitUsedEvent(Event):
    """Event fired when player uses an exploit."""
    exploit_key: str
    exploit_name: str
    target_position: Optional[Position] = None
    heat_cost: int = 0
    ram_cost: int = 0
    success: bool = True
    result_message: str = ""
    
    def get_event_type(self) -> str:
        return "exploit_used"


@dataclass
class EnemyAlertEvent(Event):
    """Event fired when enemy becomes alert."""
    enemy_id: int
    enemy_type: str
    enemy_position: Position
    alert_reason: str = "player_spotted"
    alert_level: str = "suspicious"  # suspicious, alert, hostile
    
    def get_event_type(self) -> str:
        return "enemy_alert"


@dataclass
class PlayerDamagedEvent(Event):
    """Event fired when player takes damage."""
    damage_amount: int
    damage_source: str
    player_position: Position
    new_cpu: int
    max_cpu: int
    damage_type: str = "direct"  # direct, heat, virus, etc.
    
    def get_event_type(self) -> str:
        return "player_damaged"


@dataclass
class PlayerHealedEvent(Event):
    """Event fired when player is healed."""
    heal_amount: int
    heal_source: str
    player_position: Position
    new_cpu: int
    max_cpu: int
    
    def get_event_type(self) -> str:
        return "player_healed"


@dataclass
class LevelCompleteEvent(Event):
    """Event fired when level is completed."""
    level_number: int
    completion_time: float
    enemies_defeated: int
    items_collected: int
    perfect_stealth: bool = False
    score: int = 0
    
    def get_event_type(self) -> str:
        return "level_complete"


@dataclass
class GameOverEvent(Event):
    """Event fired when game ends."""
    reason: str  # "death", "victory", "quit"
    final_level: int
    final_score: int
    play_time: float
    statistics: Dict[str, Any] = None
    
    def get_event_type(self) -> str:
        return "game_over"


@dataclass
class SaveGameEvent(Event):
    """Event fired when game is saved."""
    save_filename: str
    save_successful: bool = True
    error_message: str = ""
    save_size_bytes: int = 0
    
    def get_event_type(self) -> str:
        return "save_game"


@dataclass
class LoadGameEvent(Event):
    """Event fired when game is loaded."""
    save_filename: str
    load_successful: bool = True
    error_message: str = ""
    level_loaded: int = 0
    
    def get_event_type(self) -> str:
        return "load_game"


@dataclass
class SettingsChangedEvent(Event):
    """Event fired when game settings change."""
    setting_name: str
    old_value: Any
    new_value: Any
    requires_restart: bool = False
    
    def get_event_type(self) -> str:
        return "settings_changed"


@dataclass
class AudioEvent(Event):
    """Event fired for audio-related actions."""
    audio_type: str  # "sfx", "music"
    action: str  # "play", "stop", "pause", "volume_change"
    asset_name: str = ""
    volume: float = 1.0
    success: bool = True
    
    def get_event_type(self) -> str:
        return "audio"


@dataclass
class UIEvent(Event):
    """Event fired for UI interactions."""
    ui_element: str
    action: str  # "click", "hover", "focus", "open", "close"
    position: Optional[Position] = None
    data: Dict[str, Any] = None
    
    def get_event_type(self) -> str:
        return "ui_interaction"


@dataclass
class InventoryChangedEvent(Event):
    """Event fired when inventory changes."""
    action: str  # "add", "remove", "use", "organize"
    item_name: str = ""
    item_type: str = ""
    new_ram_usage: int = 0
    max_ram: int = 0
    
    def get_event_type(self) -> str:
        return "inventory_changed"


@dataclass
class HeatChangedEvent(Event):
    """Event fired when player heat changes."""
    old_heat: int
    new_heat: int
    max_heat: int
    heat_source: str = ""
    overheated: bool = False
    
    def get_event_type(self) -> str:
        return "heat_changed"


@dataclass
class DetectionChangedEvent(Event):
    """Event fired when detection level changes."""
    old_detection: int
    new_detection: int
    detection_source: str = ""
    enemies_alerted: int = 0
    
    def get_event_type(self) -> str:
        return "detection_changed"


@dataclass
class NetworkNodeActivatedEvent(Event):
    """Event fired when player activates a network node."""
    node_type: str  # "cooling", "cpu_recovery", "ghost"
    position: Position
    effect_applied: str = ""
    cooldown_remaining: int = 0
    
    def get_event_type(self) -> str:
        return "network_node_activated"


@dataclass
class CheatActivatedEvent(Event):
    """Event fired when a cheat/debug command is used."""
    cheat_name: str
    parameters: Dict[str, Any] = None
    success: bool = True
    debug_mode_required: bool = True
    
    def get_event_type(self) -> str:
        return "cheat_activated"