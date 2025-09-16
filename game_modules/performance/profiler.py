"""
Advanced performance profiling system for production monitoring.
"""

import time
import threading
import psutil
import gc
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from contextlib import contextmanager
import functools
import weakref

from ..core.exceptions import GameError


class ProfilingError(GameError):
    """Exception raised when profiling encounters an error."""
    pass


@dataclass
class PerformanceMetrics:
    """Container for performance metrics data."""
    
    # Timing metrics
    frame_time: float = 0.0
    render_time: float = 0.0
    update_time: float = 0.0
    input_time: float = 0.0
    
    # System metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_peak: float = 0.0
    
    # Game-specific metrics
    entities_count: int = 0
    events_processed: int = 0
    commands_executed: int = 0
    
    # Performance indicators
    fps: float = 0.0
    frame_drops: int = 0
    gc_collections: int = 0
    
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'frame_time': self.frame_time,
            'render_time': self.render_time,
            'update_time': self.update_time,
            'input_time': self.input_time,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'memory_peak': self.memory_peak,
            'entities_count': self.entities_count,
            'events_processed': self.events_processed,
            'commands_executed': self.commands_executed,
            'fps': self.fps,
            'frame_drops': self.frame_drops,
            'gc_collections': self.gc_collections,
            'timestamp': self.timestamp
        }


class PerformanceTimer:
    """High-precision timer for performance measurements."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_time: float = 0.0
        self.is_running = False
    
    def start(self) -> 'PerformanceTimer':
        """Start the timer."""
        if self.is_running:
            raise ProfilingError(f"Timer {self.name} is already running")
        
        self.start_time = time.perf_counter()
        self.is_running = True
        return self
    
    def stop(self) -> float:
        """Stop the timer and return elapsed time."""
        if not self.is_running:
            raise ProfilingError(f"Timer {self.name} is not running")
        
        self.end_time = time.perf_counter()
        self.elapsed_time = self.end_time - self.start_time
        self.is_running = False
        return self.elapsed_time
    
    def __enter__(self):
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class GameProfiler:
    """
    Advanced profiling system for game performance monitoring.
    
    Provides real-time performance metrics, timing analysis,
    and system resource monitoring.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize the game profiler.
        
        Args:
            max_history_size: Maximum number of metric entries to keep
        """
        self.max_history_size = max_history_size
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=max_history_size)
        self.current_metrics = PerformanceMetrics()
        
        # Timers
        self.active_timers: Dict[str, PerformanceTimer] = {}
        self.timing_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # System monitoring
        self.process = psutil.Process()
        self.system_baseline = self._get_system_baseline()
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.last_gc_count = sum(gc.get_count())
        
        # Profiling state
        self.enabled = True
        self.detailed_profiling = False
        self._lock = threading.Lock()
        
        # Weak references to avoid memory leaks
        self._registered_objects: weakref.WeakSet = weakref.WeakSet()
    
    def _get_system_baseline(self) -> Dict[str, float]:
        """Get baseline system metrics."""
        try:
            return {
                'cpu_percent': self.process.cpu_percent(),
                'memory_mb': self.process.memory_info().rss / 1024 / 1024,
                'memory_peak_mb': self.process.memory_info().peak_wss / 1024 / 1024 if hasattr(self.process.memory_info(), 'peak_wss') else 0
            }
        except Exception:
            return {'cpu_percent': 0.0, 'memory_mb': 0.0, 'memory_peak_mb': 0.0}
    
    def enable(self, detailed: bool = False) -> None:
        """Enable profiling with optional detailed mode."""
        self.enabled = True
        self.detailed_profiling = detailed
    
    def disable(self) -> None:
        """Disable profiling to improve performance."""
        self.enabled = False
        self.detailed_profiling = False
    
    def create_timer(self, name: str) -> PerformanceTimer:
        """Create a new performance timer."""
        if not self.enabled:
            return PerformanceTimer(name)  # Return inactive timer
        
        timer = PerformanceTimer(name)
        with self._lock:
            self.active_timers[name] = timer
        return timer
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing operations."""
        timer = self.create_timer(operation_name)
        timer.start()
        try:
            yield timer
        finally:
            elapsed = timer.stop()
            self.record_timing(operation_name, elapsed)
    
    def record_timing(self, operation: str, elapsed_time: float) -> None:
        """Record timing data for an operation."""
        if not self.enabled:
            return
        
        with self._lock:
            self.timing_history[operation].append(elapsed_time)
    
    def start_frame(self) -> None:
        """Mark the start of a new frame."""
        if not self.enabled:
            return
        
        self.frame_count += 1
        self.current_metrics = PerformanceMetrics()
        self.current_metrics.timestamp = time.time()
        
        # Update system metrics
        self._update_system_metrics()
    
    def end_frame(self) -> None:
        """Mark the end of the current frame and calculate metrics."""
        if not self.enabled:
            return
        
        # Calculate FPS
        current_time = time.time()
        time_since_last_fps = current_time - self.last_fps_time
        
        if time_since_last_fps >= 1.0:  # Update FPS every second
            self.current_metrics.fps = self.frame_count / time_since_last_fps
            self.last_fps_time = current_time
            self.frame_count = 0
        
        # Check for GC activity
        current_gc_count = sum(gc.get_count())
        if current_gc_count != self.last_gc_count:
            self.current_metrics.gc_collections = current_gc_count - self.last_gc_count
            self.last_gc_count = current_gc_count
        
        # Store metrics
        with self._lock:
            self.metrics_history.append(self.current_metrics)
    
    def _update_system_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            # CPU usage
            self.current_metrics.cpu_usage = self.process.cpu_percent()
            
            # Memory usage
            memory_info = self.process.memory_info()
            self.current_metrics.memory_usage = memory_info.rss / 1024 / 1024  # MB
            
            # Peak memory (Windows-specific)
            if hasattr(memory_info, 'peak_wss'):
                self.current_metrics.memory_peak = memory_info.peak_wss / 1024 / 1024
            
        except Exception as e:
            # Gracefully handle system metric errors
            pass
    
    def update_game_metrics(self, entities_count: int = 0, events_processed: int = 0,
                           commands_executed: int = 0) -> None:
        """Update game-specific metrics."""
        if not self.enabled:
            return
        
        self.current_metrics.entities_count = entities_count
        self.current_metrics.events_processed = events_processed
        self.current_metrics.commands_executed = commands_executed
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.current_metrics
    
    def get_average_metrics(self, last_n_frames: int = 60) -> PerformanceMetrics:
        """Get average metrics over the last N frames."""
        if not self.metrics_history:
            return PerformanceMetrics()
        
        recent_metrics = list(self.metrics_history)[-last_n_frames:]
        if not recent_metrics:
            return PerformanceMetrics()
        
        avg_metrics = PerformanceMetrics()
        count = len(recent_metrics)
        
        # Calculate averages
        avg_metrics.frame_time = sum(m.frame_time for m in recent_metrics) / count
        avg_metrics.render_time = sum(m.render_time for m in recent_metrics) / count
        avg_metrics.update_time = sum(m.update_time for m in recent_metrics) / count
        avg_metrics.input_time = sum(m.input_time for m in recent_metrics) / count
        avg_metrics.cpu_usage = sum(m.cpu_usage for m in recent_metrics) / count
        avg_metrics.memory_usage = sum(m.memory_usage for m in recent_metrics) / count
        avg_metrics.fps = sum(m.fps for m in recent_metrics if m.fps > 0) / max(1, sum(1 for m in recent_metrics if m.fps > 0))
        
        # Sums
        avg_metrics.frame_drops = sum(m.frame_drops for m in recent_metrics)
        avg_metrics.gc_collections = sum(m.gc_collections for m in recent_metrics)
        
        return avg_metrics
    
    def get_timing_stats(self, operation: str) -> Dict[str, float]:
        """Get statistical information about operation timing."""
        if operation not in self.timing_history:
            return {}
        
        timings = list(self.timing_history[operation])
        if not timings:
            return {}
        
        timings.sort()
        n = len(timings)
        
        return {
            'count': n,
            'min': min(timings),
            'max': max(timings),
            'mean': sum(timings) / n,
            'median': timings[n // 2],
            'p95': timings[int(n * 0.95)] if n > 20 else timings[-1],
            'p99': timings[int(n * 0.99)] if n > 100 else timings[-1]
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        current = self.get_current_metrics()
        average = self.get_average_metrics()
        
        # Timing statistics
        timing_stats = {}
        for operation in self.timing_history:
            timing_stats[operation] = self.get_timing_stats(operation)
        
        return {
            'current_metrics': current.to_dict(),
            'average_metrics': average.to_dict(),
            'timing_statistics': timing_stats,
            'system_info': {
                'total_frames': len(self.metrics_history),
                'profiling_enabled': self.enabled,
                'detailed_profiling': self.detailed_profiling,
                'memory_baseline_mb': self.system_baseline.get('memory_mb', 0),
                'active_timers': list(self.active_timers.keys())
            }
        }
    
    def clear_history(self) -> None:
        """Clear all metrics history."""
        with self._lock:
            self.metrics_history.clear()
            self.timing_history.clear()
    
    def export_metrics(self, filename: str) -> bool:
        """Export metrics to JSON file."""
        try:
            import json
            report = self.get_performance_report()
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
        except Exception:
            return False


def profile_function(profiler: GameProfiler, operation_name: str = None):
    """Decorator to profile function execution time."""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if profiler.enabled:
                with profiler.time_operation(op_name):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def profile_method(operation_name: str = None):
    """Decorator to profile method execution time (requires self.profiler)."""
    def decorator(func: Callable) -> Callable:
        op_name = operation_name or f"{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'profiler') and self.profiler.enabled:
                with self.profiler.time_operation(op_name):
                    return func(self, *args, **kwargs)
            else:
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator