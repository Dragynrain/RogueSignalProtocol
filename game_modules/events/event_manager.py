"""
Event management system using Observer pattern for decoupled communication.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Set, Callable, Any, Optional, Type
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor

from ..core.exceptions import GameError


class EventError(GameError):
    """Exception raised when event system encounters an error."""
    pass


@dataclass
class Event(ABC):
    """
    Base class for all events in the game.
    
    Uses dataclass for easy serialization and automatic __init__.
    All events should inherit from this class.
    """
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None
    handled: bool = False
    
    def mark_handled(self) -> None:
        """Mark this event as handled."""
        self.handled = True
    
    def is_handled(self) -> bool:
        """Check if this event has been handled."""
        return self.handled
    
    @abstractmethod
    def get_event_type(self) -> str:
        """Get the event type identifier."""
        pass


class EventHandler:
    """
    Wrapper for event handler functions with metadata.
    """
    
    def __init__(self, handler_func: Callable[[Event], None], 
                 priority: int = 0, async_handler: bool = False):
        """
        Initialize event handler.
        
        Args:
            handler_func: Function to call when event occurs
            priority: Handler priority (higher = called first)
            async_handler: Whether handler should run asynchronously
        """
        self.handler_func = handler_func
        self.priority = priority
        self.async_handler = async_handler
        self.call_count = 0
        self.total_time = 0.0
        self.last_error = None
    
    def __call__(self, event: Event) -> None:
        """Execute the handler function."""
        start_time = time.time()
        try:
            self.handler_func(event)
            self.call_count += 1
        except Exception as e:
            self.last_error = e
            logging.error(f"Error in event handler {self.handler_func.__name__}: {e}")
            raise EventError(f"Event handler failed: {e}")
        finally:
            self.total_time += time.time() - start_time
    
    def get_avg_time(self) -> float:
        """Get average execution time per call."""
        return self.total_time / max(1, self.call_count)
    
    def __lt__(self, other: 'EventHandler') -> bool:
        """Compare handlers by priority for sorting."""
        return self.priority > other.priority  # Higher priority first


class EventManager:
    """
    Central event management system using Observer pattern.
    
    Provides decoupled communication between game systems through events.
    Supports synchronous and asynchronous event handling with priorities.
    """
    
    def __init__(self, max_workers: int = 4, enable_async: bool = True):
        """
        Initialize event manager.
        
        Args:
            max_workers: Maximum async handler threads
            enable_async: Whether to enable asynchronous handlers
        """
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: List[EventHandler] = []
        self._event_queue: deque = deque()
        self._processing = False
        self._lock = threading.Lock()
        
        # Async handling
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if enable_async else None
        self._enable_async = enable_async
        
        # Statistics
        self._stats = {
            'events_processed': 0,
            'handlers_called': 0,
            'total_processing_time': 0.0,
            'errors_encountered': 0
        }
        
        # Event history for debugging
        self._event_history: deque = deque(maxlen=100)
        
        logging.info(f"Event manager initialized (async={enable_async})")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None],
                 priority: int = 0, async_handler: bool = False) -> None:
        """
        Subscribe to a specific event type.
        
        Args:
            event_type: Type of event to listen for
            handler: Function to call when event occurs
            priority: Handler priority (higher = called first)
            async_handler: Whether to run handler asynchronously
        """
        if not callable(handler):
            raise EventError("Event handler must be callable")
        
        event_handler = EventHandler(handler, priority, async_handler)
        
        with self._lock:
            self._handlers[event_type].append(event_handler)
            self._handlers[event_type].sort()  # Sort by priority
        
        logging.debug(f"Subscribed {handler.__name__} to {event_type} (priority={priority})")
    
    def subscribe_all(self, handler: Callable[[Event], None],
                     priority: int = 0, async_handler: bool = False) -> None:
        """
        Subscribe to all event types (wildcard subscription).
        
        Args:
            handler: Function to call for any event
            priority: Handler priority
            async_handler: Whether to run handler asynchronously
        """
        if not callable(handler):
            raise EventError("Event handler must be callable")
        
        event_handler = EventHandler(handler, priority, async_handler)
        
        with self._lock:
            self._wildcard_handlers.append(event_handler)
            self._wildcard_handlers.sort()
        
        logging.debug(f"Subscribed {handler.__name__} to all events (priority={priority})")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from a specific event type.
        
        Args:
            event_type: Type of event to stop listening for
            handler: Handler function to remove
            
        Returns:
            True if handler was found and removed, False otherwise
        """
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            original_count = len(handlers)
            
            # Remove matching handlers
            self._handlers[event_type] = [
                h for h in handlers if h.handler_func != handler
            ]
            
            removed = original_count - len(self._handlers[event_type])
            
        if removed > 0:
            logging.debug(f"Unsubscribed {handler.__name__} from {event_type}")
            return True
        return False
    
    def unsubscribe_all(self, handler: Callable[[Event], None]) -> bool:
        """
        Unsubscribe from all event types.
        
        Args:
            handler: Handler function to remove
            
        Returns:
            True if handler was found and removed, False otherwise
        """
        removed = False
        
        with self._lock:
            # Remove from wildcard handlers
            original_count = len(self._wildcard_handlers)
            self._wildcard_handlers = [
                h for h in self._wildcard_handlers if h.handler_func != handler
            ]
            removed = len(self._wildcard_handlers) < original_count
            
            # Remove from specific event handlers
            for event_type in list(self._handlers.keys()):
                if self.unsubscribe(event_type, handler):
                    removed = True
        
        if removed:
            logging.debug(f"Unsubscribed {handler.__name__} from all events")
        
        return removed
    
    def emit(self, event: Event, immediate: bool = False) -> None:
        """
        Emit an event to all registered handlers.
        
        Args:
            event: Event to emit
            immediate: Whether to process immediately (skip queue)
        """
        if not isinstance(event, Event):
            raise EventError("Event must inherit from Event base class")
        
        # Add to history for debugging
        self._event_history.append({
            'event': event,
            'timestamp': time.time(),
            'immediate': immediate
        })
        
        if immediate:
            self._process_event(event)
        else:
            with self._lock:
                self._event_queue.append(event)
        
        logging.debug(f"Emitted {event.get_event_type()} (immediate={immediate})")
    
    def process_events(self) -> int:
        """
        Process all queued events.
        
        Returns:
            Number of events processed
        """
        if self._processing:
            return 0  # Prevent recursive processing
        
        self._processing = True
        events_processed = 0
        
        try:
            while True:
                event = None
                with self._lock:
                    if not self._event_queue:
                        break
                    event = self._event_queue.popleft()
                
                if event:
                    self._process_event(event)
                    events_processed += 1
        
        finally:
            self._processing = False
        
        return events_processed
    
    def _process_event(self, event: Event) -> None:
        """
        Process a single event by calling all registered handlers.
        
        Args:
            event: Event to process
        """
        start_time = time.time()
        handlers_called = 0
        
        try:
            event_type = event.get_event_type()
            
            # Get all relevant handlers
            all_handlers = []
            
            # Add specific handlers
            with self._lock:
                all_handlers.extend(self._handlers.get(event_type, []))
                # Add wildcard handlers
                all_handlers.extend(self._wildcard_handlers)
            
            # Sort by priority
            all_handlers.sort()
            
            # Execute handlers
            for handler in all_handlers:
                if event.is_handled():
                    break  # Stop if event was marked as handled
                
                try:
                    if handler.async_handler and self._enable_async and self._executor:
                        # Submit to thread pool for async execution
                        self._executor.submit(handler, event)
                    else:
                        # Execute synchronously
                        handler(event)
                    
                    handlers_called += 1
                    
                except Exception as e:
                    self._stats['errors_encountered'] += 1
                    logging.error(f"Error processing event {event_type}: {e}")
            
            # Update statistics
            processing_time = time.time() - start_time
            self._stats['events_processed'] += 1
            self._stats['handlers_called'] += handlers_called
            self._stats['total_processing_time'] += processing_time
            
            logging.debug(f"Processed {event_type} ({handlers_called} handlers, {processing_time:.3f}s)")
            
        except Exception as e:
            self._stats['errors_encountered'] += 1
            logging.error(f"Critical error processing event: {e}")
            raise EventError(f"Event processing failed: {e}")
    
    def clear_queue(self) -> int:
        """
        Clear all queued events.
        
        Returns:
            Number of events cleared
        """
        with self._lock:
            count = len(self._event_queue)
            self._event_queue.clear()
        
        logging.info(f"Cleared {count} queued events")
        return count
    
    def get_queue_size(self) -> int:
        """Get number of queued events."""
        with self._lock:
            return len(self._event_queue)
    
    def get_handler_count(self, event_type: str = None) -> int:
        """
        Get number of registered handlers.
        
        Args:
            event_type: Specific event type (None for total)
            
        Returns:
            Number of handlers
        """
        with self._lock:
            if event_type:
                return len(self._handlers.get(event_type, []))
            else:
                total = len(self._wildcard_handlers)
                for handlers in self._handlers.values():
                    total += len(handlers)
                return total
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event system statistics."""
        stats = self._stats.copy()
        stats.update({
            'queue_size': self.get_queue_size(),
            'total_handlers': self.get_handler_count(),
            'registered_event_types': len(self._handlers),
            'avg_processing_time': (
                self._stats['total_processing_time'] / 
                max(1, self._stats['events_processed'])
            )
        })
        return stats
    
    def get_event_history(self) -> List[Dict[str, Any]]:
        """Get recent event history for debugging."""
        return list(self._event_history)
    
    def shutdown(self) -> None:
        """Shutdown the event manager and cleanup resources."""
        logging.info("Shutting down event manager")
        
        # Process remaining events
        remaining = self.process_events()
        if remaining > 0:
            logging.info(f"Processed {remaining} remaining events during shutdown")
        
        # Shutdown thread pool
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        # Clear handlers and queue
        with self._lock:
            self._handlers.clear()
            self._wildcard_handlers.clear()
            self._event_queue.clear()
        
        logging.info("Event manager shutdown complete")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            self.shutdown()
        except Exception:
            pass  # Ignore errors during cleanup