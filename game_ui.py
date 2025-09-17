#!/usr/bin/env python3
"""
UI utilities and functions.
Extracted from RogueSignalProtocol.py for better organization.
"""

import logging
import traceback
import inspect
import time
import tcod.event

# Import game modules
from game_entities import Colors


def render_char_safe(console, x, y, char, fg=None, bg=None):
    """Safe wrapper for console.print that ensures colors are valid tuples with comprehensive error tracking."""
    
    # Helper function to validate and convert colors with comprehensive error tracking
    def validate_color(color, color_name):
        if color is None:
            return None
        
        # Get caller information for better debugging
        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the actual caller
            caller_frame = frame.f_back.f_back  # render_char_safe -> validate_color -> actual caller
            if caller_frame:
                filename = caller_frame.f_code.co_filename.split('\\')[-1]  # Just filename
                line_number = caller_frame.f_lineno
                function_name = caller_frame.f_code.co_name
                caller_info = f"{filename}:{line_number} in {function_name}()"
            else:
                caller_info = "Unknown caller"
        finally:
            del frame  # Prevent reference cycles
        
        if isinstance(color, str):
            # Get full stack trace for string color errors
            stack_trace = ''.join(traceback.format_stack()[:-1])  # Exclude current frame
            error_msg = (
                f"TCOD ColorRGB ERROR: {color_name} is string '{color}' instead of RGB tuple\n"
                f"Called from: {caller_info}\n"
                f"Console position: ({x}, {y}), Character: '{char}'\n"
                f"Full stack trace:\n{stack_trace}"
            )
            logging.error(error_msg)
            print(f"\n{'='*80}\n{error_msg}\n{'='*80}\n")
            # DON'T convert - raise exception to fail loudly so we can fix the source
            raise ValueError(f"String color '{color}' passed to {color_name} - must be RGB tuple")
        
        if isinstance(color, (list, tuple)) and len(color) >= 3:
            try:
                # Ensure we have valid integers
                r, g, b = int(color[0]), int(color[1]), int(color[2])
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    logging.error(f"Color values out of range for {color_name}: {color} at {caller_info}")
                    return Colors.WHITE
                return (r, g, b)
            except (ValueError, TypeError) as e:
                logging.error(f"Invalid color values for {color_name}: {color} - {e} at {caller_info}")
                return Colors.WHITE
        
        # Unknown color format
        error_msg = (
            f"TCOD ColorRGB ERROR: Invalid {color_name} format: {color} (type: {type(color)})\n"
            f"Called from: {caller_info}"
        )
        logging.error(error_msg)
        print(f"\n{'='*80}\n{error_msg}\n{'='*80}\n")
        return Colors.WHITE
    
    try:
        # Validate colors
        fg = validate_color(fg, "foreground")
        bg = validate_color(bg, "background")
        
        # Make the actual console call with validated colors
        if fg is not None and bg is not None:
            console.print(x, y, char, fg=fg, bg=bg)
        elif fg is not None:
            console.print(x, y, char, fg=fg)
        elif bg is not None:
            console.print(x, y, char, bg=bg)
        else:
            console.print(x, y, char)
            
    except Exception as e:
        # Catch any TCOD errors and provide comprehensive information with full stack trace
        stack_trace = ''.join(traceback.format_stack())
        caller_info = "Unknown"
        
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            if caller_frame:
                filename = caller_frame.f_code.co_filename.split('\\')[-1]
                line_number = caller_frame.f_lineno
                function_name = caller_frame.f_code.co_name
                caller_info = f"{filename}:{line_number} in {function_name}()"
        finally:
            del frame
            
        error_msg = (
            f"CONSOLE PRINT ERROR: {str(e)}\n"
            f"Called from: {caller_info}\n"
            f"Position: ({x}, {y}), Character: '{char}'\n"
            f"FG Color: {fg} (type: {type(fg)})\n"
            f"BG Color: {bg} (type: {type(bg)})\n"
            f"Full stack trace:\n{stack_trace}"
        )
        logging.error(error_msg)
        print(f"\n{'='*80}\n{error_msg}\n{'='*80}\n")
        
        # Try fallback rendering
        try:
            console.print(x, y, char, fg=Colors.WHITE, bg=Colors.BLACK)
        except:
            pass  # Give up if even fallback fails


class WindowManager:
    """Manages dynamic window sizing and pixel dimension calculations."""
    
    def __init__(self, context):
        self.context = context
        self._cached_dimensions = None
        self._last_check_time = 0
        
    def get_window_pixel_dimensions(self):
        """Get current window pixel dimensions with caching."""
        # Cache dimensions for 0.1 seconds to avoid excessive SDL calls
        current_time = time.time()
        if (self._cached_dimensions is None or 
            current_time - self._last_check_time > 0.1):
            
            # Get actual window size via SDL
            window = self.context.sdl_window
            if window:
                width, height = window.size
                self._cached_dimensions = (width, height)
                self._last_check_time = current_time
            else:
                # Fallback to estimated dimensions
                self._cached_dimensions = (800, 600)  # Conservative estimate
                
        return self._cached_dimensions
    
    def calculate_background_rect(self, image_size):
        """Calculate rectangle for background image constrained to left portion only."""
        window_width, window_height = self.get_window_pixel_dimensions()
        img_width, img_height = image_size
        
        # CONSTRAINT: Limit graphics to left 60% of screen width for true separation
        graphics_area_width = int(window_width * 0.6)  # Graphics get 60% of width
        
        # Calculate scale to fit within LEFT AREA ONLY (not full screen)
        scale_x = graphics_area_width / img_width  # Scale to fit in left area width
        scale_y = window_height / img_height
        scale = min(scale_x, scale_y)  # Use smaller scale to fit entirely in left area
        
        # Position within left area only
        scaled_width = int(img_width * scale)
        scaled_height = int(img_height * scale)
        x = 0  # Left-align within graphics area
        y = (window_height - scaled_height) // 2  # Center vertically
        
        return (x, y, scaled_width, scaled_height)


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

