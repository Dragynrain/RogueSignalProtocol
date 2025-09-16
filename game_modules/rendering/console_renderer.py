"""
Console-based renderer implementation using TCOD.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import tcod

from .renderer_interface import RendererInterface, RenderCommand, RenderLayer
from ..core.data_structures import Position
from ..core.colors import Color, Colors
from ..core.exceptions import RenderingError


class ConsoleRenderer(RendererInterface):
    """
    TCOD-based console renderer with command batching and optimization.
    
    Implements the RendererInterface using TCOD for efficient console rendering
    with support for command batching, layer sorting, and performance optimization.
    """
    
    def __init__(self, width: int, height: int, tileset_path: str = None):
        """
        Initialize console renderer.
        
        Args:
            width: Console width in characters
            height: Console height in characters
            tileset_path: Path to tileset font file
        """
        super().__init__(width, height)
        self.tileset_path = tileset_path or "dejavu10x10_gs_tc.png"
        
        # TCOD components
        self.console: Optional[tcod.Console] = None
        self.context: Optional[tcod.context.Context] = None
        self.tileset: Optional[tcod.tileset.Tileset] = None
        
        # Rendering state
        self.render_commands: List[RenderCommand] = []
        self._frame_count = 0
        
        # Performance tracking
        self._last_render_time = 0.0
        self._render_stats = {
            'commands_per_frame': 0,
            'avg_render_time': 0.0
        }
    
    def initialize(self) -> bool:
        """
        Initialize TCOD console and context.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Load tileset
            if self.tileset_path:
                try:
                    self.tileset = tcod.tileset.load_tilesheet(
                        self.tileset_path, 32, 8, tcod.tileset.CHARMAP_TCOD
                    )
                    logging.info(f"Loaded tileset: {self.tileset_path}")
                except Exception as e:
                    logging.warning(f"Failed to load tileset {self.tileset_path}: {e}")
                    self.tileset = None
            
            # Create console
            self.console = tcod.Console(self.width, self.height, order='F')
            
            # Create context
            self.context = tcod.context.new_terminal(
                self.width, self.height,
                tileset=self.tileset,
                title="Rogue Signal Protocol",
                vsync=True
            )
            
            self._initialized = True
            logging.info(f"Console renderer initialized: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize console renderer: {e}")
            raise RenderingError(f"Console renderer initialization failed: {e}")
    
    def clear(self, color: Optional[Color] = None) -> None:
        """Clear the console with optional background color."""
        if not self.console:
            return
            
        bg_color = color or Colors.BLACK
        self.console.clear(bg=bg_color)
        self.render_commands.clear()
    
    def draw_character(self, x: int, y: int, char: str, 
                      fg_color: Color, bg_color: Optional[Color] = None) -> None:
        """Draw a character at specified position."""
        if not self.is_position_valid(x, y):
            return
            
        # Add render command for batching
        command = RenderCommand(
            RenderLayer.ENTITIES,
            Position(x, y),
            self._execute_draw_character,
            x, y, char, fg_color, bg_color
        )
        self.render_commands.append(command)
    
    def _execute_draw_character(self, renderer: RendererInterface, 
                               x: int, y: int, char: str,
                               fg_color: Color, bg_color: Optional[Color]) -> None:
        """Execute character drawing command."""
        if not self.console:
            return
            
        bg = bg_color if bg_color else None
        self.console.print(x, y, char, fg=fg_color, bg=bg)
    
    def draw_string(self, x: int, y: int, text: str, 
                   fg_color: Color, bg_color: Optional[Color] = None) -> None:
        """Draw a string starting at specified position."""
        if not self.is_position_valid(x, y) or not text:
            return
            
        command = RenderCommand(
            RenderLayer.UI_TEXT,
            Position(x, y),
            self._execute_draw_string,
            x, y, text, fg_color, bg_color
        )
        self.render_commands.append(command)
    
    def _execute_draw_string(self, renderer: RendererInterface,
                            x: int, y: int, text: str,
                            fg_color: Color, bg_color: Optional[Color]) -> None:
        """Execute string drawing command."""
        if not self.console:
            return
            
        bg = bg_color if bg_color else None
        self.console.print(x, y, text, fg=fg_color, bg=bg)
    
    def draw_rect(self, x: int, y: int, width: int, height: int,
                  fill_char: str, fg_color: Color, 
                  bg_color: Optional[Color] = None) -> None:
        """Draw a filled rectangle."""
        if width <= 0 or height <= 0:
            return
            
        command = RenderCommand(
            RenderLayer.UI_BACKGROUND,
            Position(x, y),
            self._execute_draw_rect,
            x, y, width, height, fill_char, fg_color, bg_color
        )
        self.render_commands.append(command)
    
    def _execute_draw_rect(self, renderer: RendererInterface,
                          x: int, y: int, width: int, height: int,
                          fill_char: str, fg_color: Color, 
                          bg_color: Optional[Color]) -> None:
        """Execute rectangle drawing command."""
        if not self.console:
            return
            
        # Clamp to screen bounds
        x1, y1 = self.clamp_position(x, y)
        x2 = min(x + width, self.width)
        y2 = min(y + height, self.height)
        
        bg = bg_color if bg_color else None
        
        for draw_y in range(y1, y2):
            for draw_x in range(x1, x2):
                self.console.print(draw_x, draw_y, fill_char, fg=fg_color, bg=bg)
    
    def draw_border(self, x: int, y: int, width: int, height: int,
                   border_chars: Optional[Dict[str, str]] = None,
                   fg_color: Color = None, bg_color: Optional[Color] = None) -> None:
        """Draw a border rectangle."""
        if width < 2 or height < 2:
            return
            
        # Default border characters
        chars = border_chars or {
            'horizontal': '─',
            'vertical': '│',
            'top_left': '┌',
            'top_right': '┐',
            'bottom_left': '└',
            'bottom_right': '┘'
        }
        
        fg = fg_color or Colors.WHITE
        
        command = RenderCommand(
            RenderLayer.UI_ELEMENTS,
            Position(x, y),
            self._execute_draw_border,
            x, y, width, height, chars, fg, bg_color
        )
        self.render_commands.append(command)
    
    def _execute_draw_border(self, renderer: RendererInterface,
                            x: int, y: int, width: int, height: int,
                            chars: Dict[str, str], fg_color: Color,
                            bg_color: Optional[Color]) -> None:
        """Execute border drawing command."""
        if not self.console:
            return
            
        bg = bg_color if bg_color else None
        
        # Draw corners
        self.console.print(x, y, chars['top_left'], fg=fg_color, bg=bg)
        self.console.print(x + width - 1, y, chars['top_right'], fg=fg_color, bg=bg)
        self.console.print(x, y + height - 1, chars['bottom_left'], fg=fg_color, bg=bg)
        self.console.print(x + width - 1, y + height - 1, chars['bottom_right'], fg=fg_color, bg=bg)
        
        # Draw horizontal lines
        for i in range(1, width - 1):
            self.console.print(x + i, y, chars['horizontal'], fg=fg_color, bg=bg)
            self.console.print(x + i, y + height - 1, chars['horizontal'], fg=fg_color, bg=bg)
        
        # Draw vertical lines
        for i in range(1, height - 1):
            self.console.print(x, y + i, chars['vertical'], fg=fg_color, bg=bg)
            self.console.print(x + width - 1, y + i, chars['vertical'], fg=fg_color, bg=bg)
    
    def present(self) -> None:
        """Present the current frame to screen."""
        import time
        start_time = time.time()
        
        try:
            # Sort and execute render commands
            self.render_commands.sort()
            
            for command in self.render_commands:
                command.execute(self)
            
            # Present to screen
            if self.context and self.console:
                self.context.present(self.console)
            
            # Update performance stats
            render_time = time.time() - start_time
            self._update_performance_stats(render_time)
            
            self._frame_count += 1
            
        except Exception as e:
            logging.error(f"Error during frame presentation: {e}")
            raise RenderingError(f"Frame presentation failed: {e}")
        
        finally:
            # Clear commands for next frame
            self.render_commands.clear()
    
    def _update_performance_stats(self, render_time: float) -> None:
        """Update rendering performance statistics."""
        self._render_stats['commands_per_frame'] = len(self.render_commands)
        
        # Moving average for render time
        alpha = 0.1  # Smoothing factor
        self._render_stats['avg_render_time'] = (
            alpha * render_time + 
            (1 - alpha) * self._render_stats['avg_render_time']
        )
    
    def get_mouse_position(self) -> Optional[Tuple[int, int]]:
        """Get current mouse position in console coordinates."""
        if not self.context:
            return None
            
        try:
            mouse_pos = self.context.convert_event_coordinates(
                tcod.event.get_mouse_state()
            )
            if mouse_pos:
                return (int(mouse_pos[0]), int(mouse_pos[1]))
        except Exception:
            pass
        
        return None
    
    def is_key_pressed(self, key: Any) -> bool:
        """Check if a key is currently pressed."""
        # This would typically be handled by the input system
        # For now, return False as this is event-driven
        return False
    
    def cleanup(self) -> None:
        """Clean up rendering resources."""
        try:
            if self.context:
                self.context.close()
                self.context = None
            
            self.console = None
            self.tileset = None
            self.render_commands.clear()
            
            logging.info("Console renderer cleaned up")
            
        except Exception as e:
            logging.error(f"Error during renderer cleanup: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics."""
        return {
            'frame_count': self._frame_count,
            'commands_per_frame': self._render_stats['commands_per_frame'],
            'avg_render_time_ms': self._render_stats['avg_render_time'] * 1000,
            'initialized': self._initialized
        }
    
    def add_render_command(self, command: RenderCommand) -> None:
        """Add a render command to the batch."""
        self.render_commands.append(command)
    
    def get_render_command_count(self) -> int:
        """Get number of queued render commands."""
        return len(self.render_commands)