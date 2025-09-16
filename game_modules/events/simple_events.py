"""
Simplified game event definitions.
"""

import time
from typing import Optional, Any, Dict

from .event_manager import Event
from ..core.data_structures import Position


class PlayerMoveEvent(Event):
    """Event fired when player moves."""
    
    def __init__(self, old_position: Position, new_position: Position, 
                 movement_type: str = "walk"):
        super().__init__()
        self.old_position = old_position
        self.new_position = new_position
        self.movement_type = movement_type
    
    def get_event_type(self) -> str:
        return "player_move"


class EnemyDefeatedEvent(Event):
    """Event fired when an enemy is defeated."""
    
    def __init__(self, enemy_id: int, enemy_type: str, enemy_position: Position,
                 defeated_by: str = "player", experience_gained: int = 0):
        super().__init__()
        self.enemy_id = enemy_id
        self.enemy_type = enemy_type
        self.enemy_position = enemy_position
        self.defeated_by = defeated_by
        self.experience_gained = experience_gained
    
    def get_event_type(self) -> str:
        return "enemy_defeated"


class ItemCollectedEvent(Event):
    """Event fired when player collects an item."""
    
    def __init__(self, item_name: str, item_type: str, position: Position,
                 player_position: Position, auto_collected: bool = False):
        super().__init__()
        self.item_name = item_name
        self.item_type = item_type
        self.position = position
        self.player_position = player_position
        self.auto_collected = auto_collected
    
    def get_event_type(self) -> str:
        return "item_collected"


class ExploitUsedEvent(Event):
    """Event fired when player uses an exploit."""
    
    def __init__(self, exploit_key: str, exploit_name: str,
                 target_position: Optional[Position] = None,
                 heat_cost: int = 0, ram_cost: int = 0,
                 success: bool = True, result_message: str = ""):
        super().__init__()
        self.exploit_key = exploit_key
        self.exploit_name = exploit_name
        self.target_position = target_position
        self.heat_cost = heat_cost
        self.ram_cost = ram_cost
        self.success = success
        self.result_message = result_message
    
    def get_event_type(self) -> str:
        return "exploit_used"


class LevelCompleteEvent(Event):
    """Event fired when level is completed."""
    
    def __init__(self, level_number: int, completion_time: float,
                 enemies_defeated: int, items_collected: int,
                 perfect_stealth: bool = False, score: int = 0):
        super().__init__()
        self.level_number = level_number
        self.completion_time = completion_time
        self.enemies_defeated = enemies_defeated
        self.items_collected = items_collected
        self.perfect_stealth = perfect_stealth
        self.score = score
    
    def get_event_type(self) -> str:
        return "level_complete"


class GameOverEvent(Event):
    """Event fired when game ends."""
    
    def __init__(self, reason: str, final_level: int, final_score: int,
                 play_time: float, statistics: Dict[str, Any] = None):
        super().__init__()
        self.reason = reason
        self.final_level = final_level
        self.final_score = final_score
        self.play_time = play_time
        self.statistics = statistics or {}
    
    def get_event_type(self) -> str:
        return "game_over"