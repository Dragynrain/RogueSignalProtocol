"""Event system with Observer pattern for decoupled communication."""

from .event_manager import EventManager, Event
from .simple_events import (
    PlayerMoveEvent, EnemyDefeatedEvent, ItemCollectedEvent,
    LevelCompleteEvent, GameOverEvent, ExploitUsedEvent
)

__all__ = [
    'EventManager', 'Event',
    'PlayerMoveEvent', 'EnemyDefeatedEvent', 'ItemCollectedEvent',
    'LevelCompleteEvent', 'GameOverEvent', 'ExploitUsedEvent'
]