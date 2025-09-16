"""
Renderer interface using Strategy pattern for different rendering backends.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import tcod

from ..core.data_structures import Position
from ..core.colors import Color


class RenderingConfig:
    """Configuration for rendering system."""
    DEFAULT_FPS = 60
    DEFAULT_VSYNC = True
    DEFAULT_FULLSCREEN = False
    MIN_CONSOLE_WIDTH = 80
    MIN_CONSOLE_HEIGHT = 25


class RendererInterface(ABC):
    """
    Abstract base class for all renderers using Strategy pattern.
    
    This allows switching between different rendering backends
    (ASCII, graphics, etc.) without changing client code.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize renderer with display dimensions.
        
        Args:
            width: Display width in characters/pixels
            height: Display height in characters/pixels
        """
        self.width = max(width, RenderingConfig.MIN_CONSOLE_WIDTH)
        self.height = max(height, RenderingConfig.MIN_CONSOLE_HEIGHT)
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the rendering system.
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self, color: Optional[Color] = None) -> None:
        """
        Clear the screen with optional background color.
        
        Args:
            color: Background color (None for default black)
        """
        pass
    
    @abstractmethod
    def draw_character(self, x: int, y: int, char: str, 
                      fg_color: Color, bg_color: Optional[Color] = None) -> None:
        """
        Draw a character at specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            char: Character to draw
            fg_color: Foreground color
            bg_color: Background color (None for transparent)
        """
        pass
    
    @abstractmethod
    def draw_string(self, x: int, y: int, text: str, 
                   fg_color: Color, bg_color: Optional[Color] = None) -> None:
        """
        Draw a string starting at specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            text: Text to draw
            fg_color: Foreground color
            bg_color: Background color (None for transparent)
        """
        pass
    
    @abstractmethod
    def draw_rect(self, x: int, y: int, width: int, height: int,
                  fill_char: str, fg_color: Color, 
                  bg_color: Optional[Color] = None) -> None:
        """
        Draw a filled rectangle.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Rectangle width
            height: Rectangle height
            fill_char: Character to fill with
            fg_color: Foreground color
            bg_color: Background color
        """
        pass
    
    @abstractmethod
    def draw_border(self, x: int, y: int, width: int, height: int,
                   border_chars: Optional[Dict[str, str]] = None,
                   fg_color: Color = None, bg_color: Optional[Color] = None) -> None:
        """
        Draw a border rectangle.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Rectangle width
            height: Rectangle height
            border_chars: Custom border characters
            fg_color: Foreground color
            bg_color: Background color
        """
        pass
    
    @abstractmethod
    def present(self) -> None:
        """Present/flush the current frame to screen."""
        pass
    
    @abstractmethod
    def get_mouse_position(self) -> Optional[Tuple[int, int]]:
        """
        Get current mouse position in screen coordinates.
        
        Returns:
            (x, y) tuple or None if unavailable
        """
        pass
    
    @abstractmethod
    def is_key_pressed(self, key: Any) -> bool:
        """
        Check if a key is currently pressed.
        
        Args:
            key: Key to check
            
        Returns:
            True if key is pressed
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up rendering resources."""
        pass
    
    def is_initialized(self) -> bool:
        """Check if renderer is initialized."""
        return self._initialized
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get renderer dimensions."""
        return (self.width, self.height)
    
    def is_position_valid(self, x: int, y: int) -> bool:
        """Check if position is within screen bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def clamp_position(self, x: int, y: int) -> Tuple[int, int]:
        """Clamp position to screen bounds."""
        return (
            max(0, min(x, self.width - 1)),
            max(0, min(y, self.height - 1))
        )


class RenderLayer:
    """Enumeration of rendering layers for proper Z-ordering."""
    BACKGROUND = 0
    TERRAIN = 10
    ITEMS = 20
    ENTITIES = 30
    EFFECTS = 40
    UI_BACKGROUND = 50
    UI_ELEMENTS = 60
    UI_TEXT = 70
    OVERLAYS = 80
    DEBUG = 90


class RenderCommand:
    """
    Represents a single rendering command using Command pattern.
    
    This allows for render call batching, sorting, and deferred execution.
    """
    
    def __init__(self, layer: int, position: Position, 
                 render_func: callable, *args, **kwargs):
        """
        Initialize render command.
        
        Args:
            layer: Rendering layer (Z-order)
            position: Screen position for spatial sorting
            render_func: Function to call for rendering
            *args: Arguments for render function
            **kwargs: Keyword arguments for render function
        """
        self.layer = layer
        self.position = position
        self.render_func = render_func
        self.args = args
        self.kwargs = kwargs
    
    def execute(self, renderer: RendererInterface) -> None:
        """Execute the render command."""
        self.render_func(renderer, *self.args, **self.kwargs)
    
    def __lt__(self, other: 'RenderCommand') -> bool:
        """Compare commands for sorting (by layer, then by position)."""
        if self.layer != other.layer:
            return self.layer < other.layer
        return (self.position.y, self.position.x) < (other.position.y, other.position.x)