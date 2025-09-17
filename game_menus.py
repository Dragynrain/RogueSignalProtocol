#!/usr/bin/env python3
"""
Menu system and background graphics.
Extracted from RogueSignalProtocol.py for better organization.
"""

import tcod
import logging
import time
import os
import random

# Import game modules
from game_config import GameSettings, GameConfig
from game_entities import Colors
from game_save import SaveGameManager
from game_story import StoryFragmentManager
from game_audio import SoundManager
from game_ui import render_char_safe, WindowManager, UniversalInputHandler


class MenuBackground:
    """Handles high-resolution background images for main menu with conditional loading."""
    
    def __init__(self, context, settings):
        self.context = context
        self.settings = settings
        self.window_manager = WindowManager(context)
        self.background_texture = None
        self.current_image_path = None
        self.enabled = True
        self.last_window_size = None
        self.image_size = None  # Store original image dimensions
        self.last_known_mode = settings.graphics_mode  # Track mode changes
        self.error_count = 0  # Track consecutive errors for adaptive fallback
        self.last_error_time = 0  # Track error frequency
        
    def reset_background_system(self):
        """Reset background system errors and re-enable graphics."""
        self.error_count = 0
        self.enabled = True
        self.last_error_time = 0
        print("Background graphics system reset and re-enabled")
        logging.info("Background graphics system reset and re-enabled")

    def should_load_background(self):
        """Check if background should be loaded based on graphics mode."""
        return (self.settings.graphics_mode == "graphics" and 
                self.enabled and 
                self.context.sdl_renderer is not None)
    
    def _handle_background_error(self, error_type, details, exception=None):
        """Centralized error handling for background operations with adaptive recovery."""
        import time
        
        current_time = time.time()
        self.error_count += 1
        self.last_error_time = current_time
        
        error_messages = {
            'file_not_found': "Background image file not found",
            'sdl_unavailable': "SDL renderer not available for graphics",
            'texture_failed': "SDL texture creation failed",
            'memory_error': "Insufficient memory for background image",
            'corrupted_file': "Background image file corrupted",
            'path_error': "Cross-platform path resolution failed",
            'permission_error': "File access permission denied",
            'format_error': "Unsupported image format or corrupted data"
        }
        
        error_msg = error_messages.get(error_type, 'Unknown background error')
        
        # Show ALL errors to console AND log them
        error_display = f"GRAPHICS ERROR #{self.error_count}: {error_msg}: {details}"
        print(error_display)  # Always show to console
        
        if error_type in ['sdl_unavailable', 'memory_error']:
            logging.error(error_display)
            if exception:
                exception_msg = f"Exception details: {str(exception)}"
                print(exception_msg)
                logging.error(exception_msg)
        else:
            logging.warning(error_display)
            if exception:
                exception_msg = f"Exception details: {str(exception)}"
                print(exception_msg)
                pass
        
        # Adaptive error handling based on error type and frequency
        if error_type in ['sdl_unavailable', 'memory_error']:
            # Permanent disable for session-level issues
            self.enabled = False
            disable_msg = "Background graphics disabled for this session due to system limitations"
            print(disable_msg)
            logging.info(disable_msg)
            return False
        elif self.error_count >= 10:
            # Too many errors - disable for session
            self.enabled = False
            disable_msg = f"Background graphics disabled after {self.error_count} consecutive errors"
            print(disable_msg)
            logging.warning(disable_msg)
            logging.warning(f"Background graphics disabled after {self.error_count} consecutive errors")
            return False
        elif error_type in ['file_not_found', 'corrupted_file', 'format_error']:
            # File-level errors - try alternatives
            return True  # Caller should attempt fallback
        else:
            # Other errors - try limited alternatives
            return self.error_count < 5
    
    def _get_image_base_path(self):
        """Get base path for images with enhanced cross-platform support."""
        import os
        import sys
        
        try:
            # Get directory containing the script with multiple fallback strategies
            if getattr(sys, 'frozen', False):
                # Running as compiled executable (PyInstaller, cx_Freeze, etc.)
                base_path = os.path.dirname(sys.executable)
                pass
            else:
                # Running as script - try multiple path resolution methods
                try:
                    # Method 1: Use __file__ if available
                    base_path = os.path.dirname(os.path.abspath(__file__))
                    pass
                except NameError:
                    # Method 2: Use sys.argv[0] as fallback
                    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
                    pass
            
            # Validate the path exists and is accessible
            if not os.path.exists(base_path):
                raise OSError(f"Base path does not exist: {base_path}")
            
            # Ensure we can read from the directory
            if not os.access(base_path, os.R_OK):
                raise OSError(f"Base path not readable: {base_path}")
            
            return base_path
            
        except Exception as e:
            # Ultimate fallback - use current working directory
            fallback_path = os.getcwd()
            self._handle_background_error('path_error', f"Path resolution failed, using cwd: {fallback_path}", e)
            return fallback_path
    
    def _build_image_path(self, image_number):
        """Build cross-platform image path with comprehensive validation."""
        import os
        
        try:
            base_path = self._get_image_base_path()
            
            # Build path using cross-platform separator
            image_path = os.path.join(base_path, "main_menu", f"main_menu_{image_number}.png")
            
            # Normalize the path for the current platform
            image_path = os.path.normpath(image_path)
            
            # Convert to absolute path
            image_path = os.path.abspath(image_path)
            
            pass
            return image_path
            
        except Exception as e:
            self._handle_background_error('path_error', f"Failed to build path for image {image_number}", e)
            return None
        
    def load_random_background(self):
        """Load one random menu background with enhanced error handling and cross-platform support."""
        if not self.should_load_background():
            logging.info("Background loading skipped - ASCII mode or SDL unavailable")
            return False
            
        # Reset error count on successful mode (if we get this far, SDL is working)
        if self.error_count > 0 and hasattr(self, 'last_error_time'):
            import time
            # Reset error count if it's been a while since last error
            if time.time() - self.last_error_time > 300:  # 5 minutes
                self.error_count = 0
                pass
        
        # Select random number 1-25
        import random
        selected_num = random.randint(1, 25)
        
        try:
            # Use enhanced cross-platform path building
            image_path = self._build_image_path(selected_num)
            if not image_path:
                return self._load_fallback_image_enhanced(selected_num)
            
            # Try to load the selected image
            success = self._load_image_file_enhanced(image_path)
            if success:
                self.current_image_path = image_path
                logging.info(f"Loaded background: main_menu_{selected_num}.png")
                # Reset error count on successful load
                self.error_count = 0
                return True
            else:
                # Fallback: try other images
                return self._load_fallback_image_enhanced(selected_num)
                
        except Exception as e:
            should_retry = self._handle_background_error('texture_failed', f"Exception during background loading", e)
            if should_retry:
                return self._load_fallback_image_enhanced(selected_num)
            return False
    
    def _load_fallback_image_enhanced(self, skip_num):
        """Enhanced fallback system with adaptive retry strategies."""
        import random
        
        # Calculate retry attempts based on error history
        max_attempts = max(3, 8 - self.error_count)  # Fewer attempts as errors increase
        attempted_nums = {skip_num}  # Track to avoid duplicates
        
        pass
        
        for attempt in range(max_attempts):
            # Select a different random number
            fallback_num = random.randint(1, 25)
            if fallback_num in attempted_nums:
                continue
            attempted_nums.add(fallback_num)
            
            try:
                fallback_path = self._build_image_path(fallback_num)
                if not fallback_path:
                    continue
                    
                if self._load_image_file_enhanced(fallback_path):
                    self.current_image_path = fallback_path
                    logging.info(f"Loaded fallback background: main_menu_{fallback_num}.png (attempt {attempt + 1})")
                    # Reset error count on successful fallback
                    self.error_count = max(0, self.error_count - 1)  # Partial recovery
                    return True
                    
            except Exception as e:
                # Continue trying other images, but count this as an error
                self._handle_background_error('corrupted_file', f"Fallback image {fallback_num} failed", e)
        
        # All attempts failed - use centralized error handling
        should_disable = not self._handle_background_error('file_not_found', f"All {max_attempts} fallback attempts failed")
        if should_disable:
            self.enabled = False
        
        return False
    
    def _load_fallback_image(self, skip_num):
        """Legacy fallback method - redirects to enhanced version."""
        return self._load_fallback_image_enhanced(skip_num)
    
    def _load_image_file_enhanced(self, image_path):
        """Enhanced image loading with comprehensive error handling and memory management."""
        import os
        
        # Validate file existence and accessibility
        if not os.path.exists(image_path):
            self._handle_background_error('file_not_found', f"Image file does not exist: {image_path}")
            return False
        
        # Check file accessibility
        if not os.access(image_path, os.R_OK):
            self._handle_background_error('permission_error', f"Cannot read image file: {image_path}")
            return False
        
        # Check file size for memory constraint detection
        try:
            file_size = os.path.getsize(image_path)
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                self._handle_background_error('memory_error', f"Image file too large: {file_size / (1024*1024):.1f}MB")
                return False
        except OSError as e:
            self._handle_background_error('permission_error', f"Cannot stat image file: {image_path}", e)
            return False
            
        try:
            # Import with specific error handling
            try:
                from PIL import Image
                import numpy as np
            except ImportError as e:
                self._handle_background_error('format_error', "PIL or numpy not available", e)
                return False
            
            # Load image with PIL and validate
            try:
                pil_image = Image.open(image_path)
                # Validate image
                pil_image.verify()
                # Reopen after verify (verify closes the file)
                pil_image = Image.open(image_path)
            except (OSError, IOError) as e:
                self._handle_background_error('corrupted_file', f"Cannot open or corrupted image: {image_path}", e)
                return False
            except Exception as e:
                self._handle_background_error('format_error', f"Unsupported image format: {image_path}", e)
                return False
            
            # Store original dimensions and validate
            self.image_size = pil_image.size  # (width, height)
            if self.image_size[0] <= 0 or self.image_size[1] <= 0:
                self._handle_background_error('format_error', f"Invalid image dimensions: {self.image_size}")
                return False
            
            # Memory constraint check for large images
            expected_memory = self.image_size[0] * self.image_size[1] * 3  # RGB bytes
            if expected_memory > 100 * 1024 * 1024:  # 100MB limit
                self._handle_background_error('memory_error', f"Image would use {expected_memory / (1024*1024):.1f}MB")
                return False
            
            # Convert to RGB if needed (some PNGs might be RGBA)
            try:
                if pil_image.mode not in ['RGB', 'RGBA']:
                    pil_image = pil_image.convert('RGB')
                elif pil_image.mode == 'RGBA':
                    # Convert RGBA to RGB with white background
                    background = Image.new('RGB', pil_image.size, (0, 0, 0))
                    background.paste(pil_image, mask=pil_image.split()[-1])  # Use alpha channel as mask
                    pil_image = background
            except Exception as e:
                self._handle_background_error('format_error', f"Image conversion failed: {image_path}", e)
                return False
            
            # Convert to numpy array with memory monitoring
            try:
                pixels = np.array(pil_image, dtype=np.uint8)
                if pixels.size == 0:
                    self._handle_background_error('format_error', f"Empty pixel data: {image_path}")
                    return False
            except MemoryError as e:
                self._handle_background_error('memory_error', f"Insufficient memory for pixel array: {image_path}", e)
                return False
            except Exception as e:
                self._handle_background_error('format_error', f"Numpy conversion failed: {image_path}", e)
                return False
            
            # Get SDL renderer with validation
            renderer = self.context.sdl_renderer
            if not renderer:
                self._handle_background_error('sdl_unavailable', "SDL renderer not available")
                return False
                
            # Create texture with memory error handling
            try:
                self.background_texture = renderer.upload_texture(pixels)
                if not self.background_texture:
                    self._handle_background_error('texture_failed', f"Texture creation returned None: {image_path}")
                    return False
            except MemoryError as e:
                self._handle_background_error('memory_error', f"Insufficient memory for texture: {image_path}", e)
                return False
            except Exception as e:
                self._handle_background_error('texture_failed', f"SDL texture creation failed: {image_path}", e)
                return False
            
            pass
            return True
            
        except Exception as e:
            # Catch-all for unexpected errors
            self._handle_background_error('texture_failed', f"Unexpected error loading {image_path}", e)
            return False
    
    def _load_image_file(self, image_path):
        """Legacy image loading method - redirects to enhanced version."""
        return self._load_image_file_enhanced(image_path)
    
    def get_system_diagnostics(self):
        """Provide comprehensive system diagnostics for troubleshooting."""
        import os
        import sys
        import platform
        import time
        
        diagnostics = {
            'timestamp': time.time(),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'python_version': sys.version,
                'frozen': getattr(sys, 'frozen', False)
            },
            'graphics_system': {
                'enabled': self.enabled,
                'graphics_mode': self.settings.graphics_mode,
                'sdl_renderer_available': self.context.sdl_renderer is not None,
                'current_background': os.path.basename(self.current_image_path) if self.current_image_path else None,
                'image_size': self.image_size,
                'error_count': self.error_count,
                'last_error_time': self.last_error_time
            },
            'paths': {
                'base_path': None,
                'main_menu_dir_exists': False,
                'main_menu_dir_readable': False,
                'image_count': 0
            },
            'memory': {
                'texture_loaded': self.background_texture is not None
            }
        }
        
        # Check path diagnostics
        try:
            base_path = self._get_image_base_path()
            diagnostics['paths']['base_path'] = base_path
            
            main_menu_dir = os.path.join(base_path, "main_menu")
            diagnostics['paths']['main_menu_dir_exists'] = os.path.exists(main_menu_dir)
            
            if diagnostics['paths']['main_menu_dir_exists']:
                diagnostics['paths']['main_menu_dir_readable'] = os.access(main_menu_dir, os.R_OK)
                
                if diagnostics['paths']['main_menu_dir_readable']:
                    # Count available images
                    try:
                        files = os.listdir(main_menu_dir)
                        image_files = [f for f in files if f.startswith('main_menu_') and f.endswith('.png')]
                        diagnostics['paths']['image_count'] = len(image_files)
                        diagnostics['paths']['available_images'] = sorted(image_files)[:10]  # First 10 for brevity
                    except Exception as e:
                        diagnostics['paths']['directory_error'] = str(e)
        except Exception as e:
            diagnostics['paths']['path_error'] = str(e)
        
        # Check window information
        if hasattr(self, 'window_manager') and self.window_manager:
            try:
                window_dims = self.window_manager.get_window_pixel_dimensions()
                diagnostics['window'] = {
                    'dimensions': window_dims,
                    'cached_dimensions': self.window_manager._cached_dimensions,
                    'last_check_time': self.window_manager._last_check_time
                }
            except Exception as e:
                diagnostics['window'] = {'error': str(e)}
        
        return diagnostics
    
    def log_system_health(self):
        """Log comprehensive system health information."""
        diagnostics = self.get_system_diagnostics()
        
        logging.info("=== Background Graphics System Health Report ===")
        logging.info(f"Platform: {diagnostics['platform']['system']} {diagnostics['platform']['release']}")
        logging.info(f"Python: {diagnostics['platform']['python_version'].split()[0]} (Frozen: {diagnostics['platform']['frozen']})")
        logging.info(f"Graphics Mode: {diagnostics['graphics_system']['graphics_mode']}")
        logging.info(f"SDL Renderer: {'Available' if diagnostics['graphics_system']['sdl_renderer_available'] else 'Unavailable'}")
        logging.info(f"System Enabled: {diagnostics['graphics_system']['enabled']}")
        logging.info(f"Error Count: {diagnostics['graphics_system']['error_count']}")
        
        if diagnostics['paths']['base_path']:
            logging.info(f"Base Path: {diagnostics['paths']['base_path']}")
            logging.info(f"Main Menu Directory: {'Exists' if diagnostics['paths']['main_menu_dir_exists'] else 'Missing'}")
            logging.info(f"Directory Access: {'Readable' if diagnostics['paths']['main_menu_dir_readable'] else 'Access Denied'}")
            logging.info(f"Available Images: {diagnostics['paths']['image_count']}")
        
        if 'window' in diagnostics:
            if 'dimensions' in diagnostics['window']:
                logging.info(f"Window Dimensions: {diagnostics['window']['dimensions']}")
            else:
                logging.warning(f"Window Access Error: {diagnostics['window'].get('error', 'Unknown')}")
        
        current_bg = diagnostics['graphics_system']['current_background']
        if current_bg:
            logging.info(f"Current Background: {current_bg} ({diagnostics['graphics_system']['image_size']})")
        
        logging.info("=== End Health Report ===")
        
        return diagnostics
        
    def render_background(self, console):
        """Render background image using SDL renderer."""
        if (not self.should_load_background() or 
            not self.background_texture or 
            not self.image_size):
            return
            
        try:
            # Render the actual PNG background to SDL renderer
            current_window_size = self.window_manager.get_window_pixel_dimensions()
            
            # Calculate background rectangle with aspect ratio preservation
            bg_rect = self.window_manager.calculate_background_rect(self.image_size)
            
            # Use TCOD renderer.copy() method for texture rendering
            renderer = self.context.sdl_renderer
            
            # Destination rectangle (x, y, width, height)
            dest_rect = bg_rect  # Already in (x, y, w, h) format
            
            # Render texture using TCOD's copy method
            renderer.copy(
                texture=self.background_texture,
                dest=dest_rect  # Scale to calculated rectangle
            )
            
            # Background rendered to SDL successfully
            
        except Exception as e:
            self._handle_background_error('texture_failed', f"SDL background rendering failed", e)
    
    def _render_console_background(self, console):
        """Render a visible cyberpunk background pattern to the console."""
        # Create a more visible cyberpunk background with side panels
        
        # Fill left side with cyberpunk pattern (positions 0-25)
        self._render_side_panel(console, 0, 25)
        
        # Fill right side with cyberpunk pattern (positions 55-80) 
        self._render_side_panel(console, 55, console.width)
        
        # Add top/bottom borders
        self._render_borders(console)
        
        # Add some scattered elements in the center for atmosphere
        self._render_center_atmosphere(console)
    
    def _render_side_panel(self, console, start_x, end_x):
        """Render cyberpunk pattern in a side panel."""
        import random
        random.seed(42)  # Consistent pattern
        
        patterns = ['▓', '▒', '░', '·', '▪', '▫']
        colors = [
            (0, 80, 120),    # Cyan blue
            (0, 120, 180),   # Bright blue  
            (80, 0, 120),    # Purple
            (120, 0, 180),   # Bright purple
            (0, 180, 120),   # Teal
        ]
        
        for y in range(console.height):
            for x in range(start_x, min(end_x, console.width)):
                # Higher density for side panels
                if random.random() < 0.25:  # 25% density
                    pattern_char = random.choice(patterns)
                    fg_color = random.choice(colors)
                    # Use dark background to make pattern visible
                    render_char_safe(console, x, y, pattern_char, fg=fg_color, bg=(5, 5, 15))
                else:
                    # Fill with dark background
                    render_char_safe(console, x, y, ' ', fg=(0, 0, 0), bg=(5, 5, 15))
    
    def _render_borders(self, console):
        """Add cyberpunk-style borders."""
        border_color = (0, 150, 200)  # Bright cyan
        
        # Top border
        for x in range(console.width):
            render_char_safe(console, x, 0, '─', fg=border_color, bg=(5, 5, 15))
        
        # Bottom border  
        for x in range(console.width):
            render_char_safe(console, x, console.height - 1, '─', fg=border_color, bg=(5, 5, 15))
    
    def _render_center_atmosphere(self, console):
        """Add subtle atmospheric elements to center area."""
        import random
        random.seed(123)  # Different seed for center
        
        # Very subtle dots in center area (positions 26-54)
        for y in range(2, console.height - 2):
            for x in range(26, 54):
                if random.random() < 0.02:  # Very low density - 2%
                    render_char_safe(console, x, y, '·', fg=(0, 60, 100), bg=(0, 0, 0))
        
    def reload_if_mode_changed(self):
        """Reload or unload background based on current graphics mode."""
        current_mode = self.settings.graphics_mode
        has_texture = self.background_texture is not None
        mode_changed = current_mode != self.last_known_mode
        
        if mode_changed:
            logging.info(f"Graphics mode change detected: {self.last_known_mode} -> {current_mode}")
            self.last_known_mode = current_mode
        
        if current_mode == "graphics" and not has_texture:
            # Mode switched to graphics - load background
            if mode_changed:
                logging.info("Graphics mode enabled - loading background")
            self.load_random_background()
        elif current_mode == "ascii" and has_texture:
            # Mode switched to ASCII - free memory
            if mode_changed:
                logging.info("ASCII mode enabled - cleaning up background")
            self.cleanup()
        
        # Force layout recalculation on next render by clearing cached dimensions
        if hasattr(self, 'window_manager') and self.window_manager:
            self.window_manager._cached_dimensions = None
    
    def force_reload(self):
        """Force immediate background reload regardless of current state."""
        logging.info("Forcing background reload")
        self.cleanup()  # Clean up current background
        if self.settings.graphics_mode == "graphics":
            self.load_random_background()  # Load new background if in graphics mode
    
    def should_log_health_report(self):
        """Determine if a health report should be logged (e.g., on errors or periodically)."""
        # Log health report if there have been errors or it's been a while
        if self.error_count > 0:
            return True
        
        # Optionally log periodically (every hour) for monitoring
        import time
        if hasattr(self, '_last_health_log'):
            return time.time() - self._last_health_log > 3600  # 1 hour
        else:
            self._last_health_log = time.time()
            return True  # First time
        
        return False
            
    def cleanup(self):
        """Free background texture memory."""
        if self.background_texture:
            try:
                # TCOD Texture objects should be garbage collected automatically
                # But we can explicitly release references
                del self.background_texture
                pass
            except Exception as e:
                logging.error(f"Texture cleanup failed: {e}")
            finally:
                self.background_texture = None
                self.current_image_path = None
                self.image_size = None


# ============================================================================
# MAIN MENU SYSTEM
# ============================================================================

class MainMenu:
    """Main menu for New Game/Continue options."""
    
    def __init__(self, background=None):
        self.selected_option = 0
        self.options = ["Continue Game", "New Game", "Settings", "Help", "Lore", "Exit"] if SaveGameManager.save_exists() else ["New Game", "Settings", "Help", "Lore", "Exit"]
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False  # Flag to indicate if accessed from mid-game
        self.background = background
    
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
    
    def _has_background(self) -> bool:
        """Check if background is available and should be displayed."""
        return (self.background and 
                self.background.should_load_background() and 
                self.background.background_texture)
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the main menu with optional background."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()
        
        if self.show_warning:
            self._render_warning_dialog(console)
        else:
            self._render_main_menu(console)
    
    def _clear_text_areas_only(self, console):
        """Create true separation: left 60% transparent for graphics, right 40% opaque for menu."""
        layout = self._get_menu_layout_params()
        
        if layout['use_background_layout']:
            # ENFORCED SEPARATION: 60% graphics area, 40% menu area
            graphics_boundary = int(console.width * 0.6)  # Hard boundary at 60%
            
            # Left 60%: Make transparent for SDL graphics
            for y in range(console.height):
                for x in range(0, graphics_boundary):
                    # Set background alpha to 0 (fully transparent)
                    console.rgba[x, y] = (
                        ord(' '),           # Empty character
                        (255, 255, 255, 0), # Transparent foreground
                        (0, 0, 0, 0)        # Transparent background
                    )
            
            # Right 40%: Clear for text menu (opaque)
            for y in range(console.height):
                for x in range(graphics_boundary, console.width):
                    render_char_safe(console, x, y, ' ', fg=(255, 255, 255), bg=(0, 0, 0))
        else:
            # ASCII mode: clear entire console
            console.clear()
    
    def _render_main_menu(self, console: tcod.console.Console) -> None:
        """Render the main menu screen."""
        
        # TCOD is a console-based library, not designed for large background images
        # For true graphics, we would need tcod.sdl.render, but that's complex
        # For now, we'll use the traditional centered menu with optional ASCII art
        
        self._render_enhanced_menu(console)
    
    def _get_menu_layout_params(self):
        """Calculate menu positioning based on graphics mode, window state, and optimal visibility."""
        if self._has_background():
            # Graphics mode with background - calculate optimal positioning
            return self._calculate_background_aware_layout()
        else:
            # ASCII mode or no background - center everything
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }
    
    def _render_right_side_box(self, console: tcod.console.Console, height: int, border_color: tuple, y_offset: int = 0):
        """Render a right-side menu box with consistent positioning and styling.
        
        Args:
            console: The console to render to
            height: Height of the box
            border_color: Color for the box border
            y_offset: Vertical offset for positioning (0 = centered)
            
        Returns:
            dict: Box dimensions and positions for content rendering
        """
        layout = self._get_menu_layout_params()
        
        if layout['use_background_layout']:
            # Graphics mode - narrow box on right side
            box_width = 28
            box_right = GameConfig.SCREEN_WIDTH - 2
            box_left = box_right - box_width
            
            if y_offset == 0:
                # Centered positioning
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                # Custom offset
                box_top = y_offset
                
            box_bottom = box_top + height - 1
            
            # Ensure box fits within screen bounds
            box_top = max(1, min(box_top, GameConfig.SCREEN_HEIGHT - height - 1))
            box_bottom = box_top + height - 1
            
            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0), 
                             bg_blend=tcod.constants.BKGND_SET)
            
            # Draw border with Unicode box characters
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, "│", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, "│", fg=border_color, bg=Colors.BLACK)
            for x in range(box_left, box_right + 1):
                render_char_safe(console, x, box_top, "─", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, "─", fg=border_color, bg=Colors.BLACK)
            # Box corners
            render_char_safe(console, box_left, box_top, "┌", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_top, "┐", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_left, box_bottom, "└", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_bottom, "┘", fg=border_color, bg=Colors.BLACK)
            
            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 1,
                'content_right': box_right - 1,
                'content_top': box_top + 1,
                'content_width': box_width - 2,
                'use_background_layout': True
            }
        else:
            # ASCII mode - larger centered box
            box_width = 50
            box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
            box_right = box_left + box_width - 1
            
            if y_offset == 0:
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                box_top = y_offset
                
            box_bottom = box_top + height - 1
            
            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0), 
                             bg_blend=tcod.constants.BKGND_SET)
            
            # Draw simple ASCII border
            for x in range(box_left, box_left + box_width):
                render_char_safe(console, x, box_top, '=', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, '=', fg=border_color, bg=Colors.BLACK)
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, '|', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, '|', fg=border_color, bg=Colors.BLACK)
            
            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 2,
                'content_right': box_right - 2,
                'content_top': box_top + 1,
                'content_width': box_width - 4,
                'use_background_layout': False
            }
    
    def _calculate_background_aware_layout(self):
        """Calculate sophisticated layout for background mode based on window dimensions."""
        # Get actual window dimensions if available
        window_width, window_height = 800, 800  # Default fallback
        
        if (self.background and 
            self.background.window_manager):
            try:
                window_width, window_height = self.background.window_manager.get_window_pixel_dimensions()
            except:
                pass  # Use defaults if window detection fails
        
        # Calculate dynamic positioning based on window aspect ratio and size
        aspect_ratio = window_width / window_height if window_height > 0 else 1.0
        
        # Position menu to avoid overlap with left-aligned background graphics
        # Since image is left-aligned, menu needs to be positioned far right
        if aspect_ratio > 1.2:
            # Wide window - use far right positioning to avoid image overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.85)  # Move further right
            layout_zone = 'right'
        elif aspect_ratio < 0.8:
            # Very tall window - still avoid left side overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.8)   # Right side, not center
            layout_zone = 'upper'
        else:
            # Square-ish window - use far right positioning
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.82)  # Move further right
            layout_zone = 'right_center'
        
        # Ensure minimum margins
        min_margin = 5
        max_x = GameConfig.SCREEN_WIDTH - min_margin - 20  # 20 chars for longest menu option
        text_x_offset = min(text_x_offset, max_x)
        text_x_offset = max(text_x_offset, min_margin + 10)
        
        layout = {
            'title_x': text_x_offset - 10,
            'menu_x': text_x_offset,
            'use_background_layout': True,
            'layout_zone': layout_zone,
            'window_aspect': aspect_ratio,
            'window_size': (window_width, window_height)
        }
        
        return layout
    
    def _render_enhanced_menu(self, console: tcod.console.Console) -> None:
        """Render an enhanced menu with dynamic positioning based on background state."""
        # Calculate menu height based on content
        menu_height = GameConfig.SCREEN_HEIGHT - 4  # Full height for main menu
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, Colors.CYAN, y_offset=3)
        
        # Title with some ASCII art decoration
        title = "ROGUE SIGNAL PROTOCOL"
        subtitle = "Cyberpunk Stealth Exfiltration"
        
        if box['use_background_layout']:
            # Title content within narrow box - split into multiple lines to fit
            render_char_safe(console, box['center_x'] - 10, 6, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
            # Split title into two lines
            render_char_safe(console, box['center_x'] - 6, 8, "ROGUE SIGNAL", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 4, 9, "PROTOCOL", fg=Colors.CYAN, bg=Colors.BLACK)
            # Split subtitle into two lines
            render_char_safe(console, box['center_x'] - 8, 11, "Cyberpunk Stealth", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 6, 12, "Exfiltration", fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, box['center_x'] - 10, 13, "─" * 20, fg=Colors.CYAN, bg=Colors.BLACK)
        else:
            # ASCII mode - centered positioning
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 6, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 8, title, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(subtitle) // 2, 9, subtitle, fg=Colors.CYAN, bg=Colors.BLACK)
            render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - 20, 10, "─" * 40, fg=Colors.CYAN, bg=Colors.BLACK)
        
        # Version and build info  
        if box['use_background_layout']:
            # Background mode - position within narrow box
            build_info = "Alpha Build"
            author_info = "by Adam Forster"
            render_char_safe(console, 
                box['center_x'] - len(build_info) // 2, 15,
                build_info, fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                box['center_x'] - len(author_info) // 2, 16,
                author_info, fg=(128, 128, 128), bg=Colors.BLACK
            )
        else:
            # ASCII mode - centered
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 13, 12,
                "Alpha Build by Adam Forster", fg=(128, 128, 128), bg=Colors.BLACK
            )
        
        # Menu options
        start_y = 21
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            prefix = "> " if i == self.selected_option else "  "
            
            if box['use_background_layout']:
                # Background mode - centered within narrow box
                x_pos = box['center_x'] - len(option) // 2 - 1
            else:
                # ASCII mode - centered
                x_pos = GameConfig.SCREEN_WIDTH // 2 - len(option) // 2 - 1
                
            render_char_safe(console, 
                x_pos, start_y + i * 2,
                f"{prefix}{option}", fg=color, bg=Colors.BLACK
            )
        
        # Save file info
        if SaveGameManager.save_exists():
            save_timestamp = SaveGameManager.get_save_timestamp()
            if save_timestamp:
                if box['use_background_layout']:
                    # Background mode - position within narrow box
                    save_text = "Save found"
                    continue_text = "Continue to resume"
                    render_char_safe(console, 
                        box['center_x'] - len(save_text) // 2, start_y + len(self.options) * 2 + 2,
                        save_text, fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    render_char_safe(console, 
                        box['center_x'] - len(continue_text) // 2, start_y + len(self.options) * 2 + 3,
                        continue_text, fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    saved_text = f"Saved: {save_timestamp[:16]}"
                    render_char_safe(console, 
                        box['center_x'] - len(saved_text) // 2, start_y + len(self.options) * 2 + 4,
                        saved_text, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
                    )
                else:
                    # ASCII mode - centered
                    render_char_safe(console, 
                        GameConfig.SCREEN_WIDTH // 2 - 15, start_y + len(self.options) * 2 + 2,
                        "Save file found - Continue to resume", fg=Colors.GREEN, bg=Colors.BLACK
                    )
                    render_char_safe(console, 
                        GameConfig.SCREEN_WIDTH // 2 - 12, start_y + len(self.options) * 2 + 3,
                        f"Last saved: {save_timestamp}", fg=Colors.LIGHT_GRAY, bg=Colors.BLACK
                    )
        
        # Controls - position based on layout mode
        if box['use_background_layout']:
            # Background mode - position within narrow box
            nav_text = "↕/W/S: Navigate"
            select_text = "Enter: Select"
            render_char_safe(console, 
                box['center_x'] - len(nav_text) // 2, GameConfig.SCREEN_HEIGHT - 6,
                nav_text, fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                box['center_x'] - len(select_text) // 2, GameConfig.SCREEN_HEIGHT - 5,
                select_text, fg=(128, 128, 128), bg=Colors.BLACK
            )
        else:
            # ASCII mode - centered
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 15, GameConfig.SCREEN_HEIGHT - 6,
                "UP/DOWN or W/S: Navigate", fg=(128, 128, 128), bg=Colors.BLACK
            )
            render_char_safe(console, 
                GameConfig.SCREEN_WIDTH // 2 - 10, GameConfig.SCREEN_HEIGHT - 5,
                "Enter: Select", fg=(128, 128, 128), bg=Colors.BLACK
            )
        
        # Story fragments info - position based on layout mode
        if SaveGameManager.save_exists():
            story_manager = StoryFragmentManager()
            discovered, total = story_manager.get_fragment_count()
            if box['use_background_layout']:
                # Background mode - position within narrow box
                fragment_text = f"Fragments: {discovered}/{total}"
                render_char_safe(console, 
                    box['center_x'] - len(fragment_text) // 2, GameConfig.SCREEN_HEIGHT - 2,
                    fragment_text, fg=Colors.CYAN, bg=Colors.BLACK
                )
            else:
                # ASCII mode - centered
                render_char_safe(console, 
                    GameConfig.SCREEN_WIDTH // 2 - 12, GameConfig.SCREEN_HEIGHT - 2,
                    f"Story Fragments: {discovered}/{total}", fg=Colors.CYAN, bg=Colors.BLACK
                )
    
    
    def _render_warning_dialog(self, console: tcod.console.Console) -> None:
        """Render save deletion warning dialog with background-aware positioning."""
        # Calculate dialog height
        dialog_height = 22
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, dialog_height, Colors.RED)
        
        # Title
        render_char_safe(console, box['center_x'] - 3, box['top'] + 2, "WARNING", fg=Colors.RED, bg=Colors.BLACK)
        
        # Message - adjust for narrow box
        if box['use_background_layout']:
            # Narrow box - break text into shorter lines
            messages = [
                "Starting a new game",
                "will delete your save",
                "file permanently.",
                "",
                "This will erase:",
                "• Current level",
                "• Character state", 
                "• Inventory/upgrades",
                "• Story fragments",
                "  remain safe",
                "",
                "Are you sure you",
                "want to continue?"
            ]
        else:
            # ASCII mode - use original longer lines
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
            msg_x = box['content_left'] + 1 if len(msg) <= box['content_width'] else box['content_left']
            render_char_safe(console, msg_x, box['top'] + 4 + i, msg, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options
        options = ["Yes, Delete Save", "No, Go Back"]
        options_start_y = box['bottom'] - 4
        
        for i, option in enumerate(options):
            color = Colors.RED if i == self.warning_selection and i == 0 else Colors.YELLOW if i == self.warning_selection else Colors.WHITE
            prefix = "> " if i == self.warning_selection else "  "
            
            if box['use_background_layout']:
                # Narrow box - shorter option text and center alignment
                short_options = ["Yes, Delete", "No, Go Back"]
                option_text = short_options[i]
                option_x = box['center_x'] - len(option_text) // 2 - 1
            else:
                # ASCII mode - use full option text
                option_text = option
                option_x = box['center_x'] - len(option_text) // 2 - 1
            
            render_char_safe(console, 
                option_x, 
                options_start_y + i,
                f"{prefix}{option_text}", fg=color, bg=Colors.BLACK
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
        render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        if not discovered_fragments:
            render_char_safe(console, 2, 5, "No lore fragments discovered yet.", fg=Colors.WHITE)
            render_char_safe(console, 2, 6, "Start playing to discover the story!", fg=Colors.WHITE)
            render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return", fg=Colors.LIGHT_GRAY)
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
            render_char_safe(console, 2, start_y + i, f"{prefix}Fragment {fragment_index + 1}: {first_line}", fg=color)
        
        # Instructions
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 4, "Up/Down: Navigate  Enter: Read  Esc: Back", fg=Colors.LIGHT_GRAY)
    
    def _render_reading_mode(self, console, discovered_fragments):
        """Render individual fragment for reading."""
        if self.lore_viewer_selection >= len(discovered_fragments):
            self.lore_viewer_mode = "list"
            return
            
        fragment_index, fragment_text = discovered_fragments[self.lore_viewer_selection]
        
        title = f"DATA FRAGMENT {fragment_index + 1}"
        render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        # Render fragment text with wrapping
        lines = fragment_text.split('\n')
        y = 5
        for line in lines:
            if y < GameConfig.SCREEN_HEIGHT - 4:
                # Simple word wrapping
                if len(line) <= GameConfig.SCREEN_WIDTH - 4:
                    render_char_safe(console, 2, y, line, fg=Colors.WHITE)
                    y += 1
                else:
                    # Basic word wrapping for long lines
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) <= GameConfig.SCREEN_WIDTH - 4:
                            current_line += (" " if current_line else "") + word
                        else:
                            render_char_safe(console, 2, y, current_line, fg=Colors.WHITE)
                            y += 1
                            current_line = word
                            if y >= GameConfig.SCREEN_HEIGHT - 4:
                                break
                    if current_line and y < GameConfig.SCREEN_HEIGHT - 4:
                        render_char_safe(console, 2, y, current_line, fg=Colors.WHITE)
                        y += 1
        
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return to list", fg=Colors.LIGHT_GRAY)
    
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
        render_char_safe(console, GameConfig.SCREEN_WIDTH // 2 - len(title) // 2, 2, title, fg=Colors.YELLOW)
        
        y = 5
        help_sections = self._get_help_sections()
        
        for text, color in help_sections:
            if y < GameConfig.SCREEN_HEIGHT - 2:
                render_char_safe(console, 2, y, text, fg=color)
                y += 1
        
        # Back instruction
        render_char_safe(console, 2, GameConfig.SCREEN_HEIGHT - 2, "Press any key to return", fg=Colors.LIGHT_GRAY)
    
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
            ("  Collect codes, exploits, and upgrades", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MOVEMENT & CONTROLS:", Colors.CYAN),
            ("  Arrow Keys, WASD, or Numpad: Move/Navigate", Colors.WHITE),
            ("  1-9: Use loaded exploits (requires targeting)", Colors.WHITE),
            ("  I: Inventory (manage codes & exploits)", Colors.WHITE),
            ("  Tab: Toggle vision overlays", Colors.WHITE),
            ("  L: View discovered lore fragments", Colors.WHITE),
            ("  ESC: Pause menu / Close screens", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("MAP SYMBOLS:", Colors.CYAN),
            ("  ☻: Player (you)", Colors.PLAYER),
            ("  •: Empty floor (passable)", Colors.FLOOR),
            ("  ┌┐└┘┬┴├┤┼─│: Walls (impassable)", Colors.WALL),
            ("  ◘: Shadows (stealth zones)", Colors.ELECTRIC_PURPLE),
            ("  >: Gateway to next level", Colors.GATEWAY),
            ("  ♫: Story fragments (lore)", Colors.CYAN),
            ("", Colors.WHITE),
            
            ("ENEMY TYPES (HP, Vision, Behavior, Damage):", Colors.CYAN),
            ("  S: Scanner (35hp, 4 vision, static, no attack)", Colors.ENEMY_UNAWARE),
            ("  P: Patrol (40hp, 4 vision, linear routes, 15 dmg)", Colors.ENEMY_UNAWARE),
            ("  B: Bot (25hp, 3 vision, random movement, 8 dmg)", Colors.ENEMY_UNAWARE),
            ("  F: Firewall (80hp, 5 vision, static, no attack)", Colors.ENEMY_ALERT),
            ("  H: Hunter (50hp, 6 vision, seeks players, 22 dmg)", Colors.ENEMY_HOSTILE),
            ("  V: Virus (35hp, 4 vision, seeks players, virus attack)", Colors.ENEMY_HOSTILE),
            ("  I: Inhibitor (30hp, 4 vision, random, slows movement)", Colors.ENEMY_UNAWARE),
            ("  A: Admin Avatar (250hp, 8 vision, perfect tracking, 45 dmg)", Colors.ENEMY_HOSTILE),
            ("", Colors.WHITE),
            
            ("ITEMS & PICKUPS:", Colors.CYAN),
            ("  §: Code Patches (grant random bonuses, restore stats)", Colors.ELECTRIC_PURPLE),
            ("  &: Exploits (combat & utility abilities)", Colors.NEON_PINK),
            ("  ○: Permanent upgrades (Memory/CPU/Heat)", Colors.ELECTRIC_BLUE),
            ("  ♥: CPU recovery nodes (restore health)", Colors.RED),
            ("  ♦: Cooling nodes (reduce heat)", Colors.CYAN),
            ("  ♠: Ghost nodes (reduce detection)", Colors.ELECTRIC_PURPLE),
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
            ("  Log Wiper: Reduce detection level (-30%)", Colors.WHITE),
            ("  Antivirus: Purges negative status effects (virus, slow)", Colors.WHITE),
            ("  Memory Leak: 3x3 area makes enemies forget player location", Colors.WHITE),
            ("  Port Scan: Reveals all special nodes (♥♦♠) on the map", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("STATUS EFFECTS:", Colors.CYAN),
            ("  Virus: 3 CPU damage per turn, cured with Antivirus", Colors.WHITE),
            ("  Virus attacks stack virus duration (max 12 turns)", Colors.WHITE),
            ("  Movement Slowed: Can only move every other turn", Colors.WHITE),
            ("  Speed Boost and Movement Slow offset each other turn-for-turn", Colors.WHITE),
            ("", Colors.WHITE),
            
            ("SURVIVAL TIPS:", Colors.CYAN),
            ("  Use shadows frequently - stealth is key", Colors.WHITE),
            ("  Monitor heat and detection levels constantly", Colors.WHITE),
            ("  Plan exploit usage - heat management is critical", Colors.WHITE),
            ("  Use CPU nodes when low on health", Colors.WHITE),
            ("  Use Ghost nodes to reduce detection continuously", Colors.WHITE),
            ("  Admin Avatar spawns at high detection - be careful!", Colors.WHITE),
            ("  Virus enemies apply virus damage - keep Antivirus exploit handy!", Colors.WHITE),
            ("  Inhibitor enemies add 1 slow turn that offsets speed boosts!", Colors.WHITE),
            ("  Save cooling nodes for emergencies", Colors.WHITE),
        ]


class SettingsMenu:
    """Settings menu for audio, graphics, and help options."""
    
    def __init__(self, settings: GameSettings, menu_background=None):
        self.settings = settings
        self.menu_background = menu_background  # Reference to background manager
        self.background = menu_background  # Alias for consistency with MainMenu
        self.selected_option = 0
        self.options = [
            {"name": "Master Volume", "type": "volume", "key": "master"},
            {"name": "SFX Volume", "type": "volume", "key": "sfx"},
            {"name": "Music Volume", "type": "volume", "key": "music"},
            {"name": "Graphics Mode", "type": "toggle", "key": "graphics_mode", 
             "values": ["ASCII", "Graphics"]},
            {"name": "Back", "type": "action"}
        ]
    
    def _has_background(self) -> bool:
        """Check if background is available and should be displayed."""
        return (self.background and 
                self.background.should_load_background() and 
                self.background.background_texture)
    
    def _get_menu_layout_params(self):
        """Calculate menu positioning based on graphics mode, window state, and optimal visibility."""
        if self._has_background():
            # Graphics mode with background - calculate optimal positioning
            return self._calculate_background_aware_layout()
        else:
            # ASCII mode or no background - center everything
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }
    
    def _calculate_background_aware_layout(self):
        """Calculate sophisticated layout for background mode based on window dimensions."""
        # Get actual window dimensions if available
        window_width, window_height = 800, 800  # Default fallback
        
        if (self.background and 
            self.background.window_manager):
            try:
                window_width, window_height = self.background.window_manager.get_window_pixel_dimensions()
            except:
                pass  # Use defaults if window detection fails
        
        # Calculate dynamic positioning based on window aspect ratio and size
        aspect_ratio = window_width / window_height if window_height > 0 else 1.0
        
        # Position menu to avoid overlap with left-aligned background graphics
        # Since image is left-aligned, menu needs to be positioned far right
        if aspect_ratio > 1.2:
            # Wide window - use far right positioning to avoid image overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.85)  # Move further right
            layout_zone = 'right'
        elif aspect_ratio < 0.8:
            # Very tall window - still avoid left side overlap
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.8)   # Right side, not center
            layout_zone = 'upper'
        else:
            # Square-ish window - use far right positioning
            text_x_offset = int(GameConfig.SCREEN_WIDTH * 0.82)  # Move further right
            layout_zone = 'right_center'
        
        # Ensure minimum margins
        min_margin = 5
        max_x = GameConfig.SCREEN_WIDTH - min_margin - 20  # 20 chars for longest menu option
        text_x_offset = min(text_x_offset, max_x)
        text_x_offset = max(text_x_offset, min_margin + 10)
        
        layout = {
            'title_x': text_x_offset - 10,
            'menu_x': text_x_offset,
            'use_background_layout': True,
            'layout_zone': layout_zone,
            'window_aspect': aspect_ratio,
            'window_size': (window_width, window_height)
        }
        
        return layout
    
    def _render_right_side_box(self, console: tcod.console.Console, height: int, border_color: tuple, y_offset: int = 0):
        """Render a right-side menu box with consistent positioning and styling.
        
        Args:
            console: The console to render to
            height: Height of the box
            border_color: Color for the box border
            y_offset: Vertical offset for positioning (0 = centered)
            
        Returns:
            dict: Box dimensions and positions for content rendering
        """
        layout = self._get_menu_layout_params()
        
        if layout['use_background_layout']:
            # Graphics mode - narrow box on right side
            box_width = 28
            box_right = GameConfig.SCREEN_WIDTH - 2
            box_left = box_right - box_width
            
            if y_offset == 0:
                # Centered positioning
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                # Custom offset
                box_top = y_offset
                
            box_bottom = box_top + height - 1
            
            # Ensure box fits within screen bounds
            box_top = max(1, min(box_top, GameConfig.SCREEN_HEIGHT - height - 1))
            box_bottom = box_top + height - 1
            
            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0), 
                             bg_blend=tcod.constants.BKGND_SET)
            
            # Draw border with Unicode box characters
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, "│", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, "│", fg=border_color, bg=Colors.BLACK)
            for x in range(box_left, box_right + 1):
                render_char_safe(console, x, box_top, "─", fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, "─", fg=border_color, bg=Colors.BLACK)
            # Box corners
            render_char_safe(console, box_left, box_top, "┌", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_top, "┐", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_left, box_bottom, "└", fg=border_color, bg=Colors.BLACK)
            render_char_safe(console, box_right, box_bottom, "┘", fg=border_color, bg=Colors.BLACK)
            
            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 1,
                'content_right': box_right - 1,
                'content_top': box_top + 1,
                'content_width': box_width - 2,
                'use_background_layout': True
            }
        else:
            # ASCII mode - larger centered box
            box_width = 50
            box_left = (GameConfig.SCREEN_WIDTH - box_width) // 2
            box_right = box_left + box_width - 1
            
            if y_offset == 0:
                box_top = (GameConfig.SCREEN_HEIGHT - height) // 2
            else:
                box_top = y_offset
                
            box_bottom = box_top + height - 1
            
            # Draw black background
            console.draw_rect(x=box_left, y=box_top, width=box_width, height=height,
                             ch=ord(' '), fg=(255, 255, 255), bg=(0, 0, 0), 
                             bg_blend=tcod.constants.BKGND_SET)
            
            # Draw simple ASCII border
            for x in range(box_left, box_left + box_width):
                render_char_safe(console, x, box_top, '=', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, x, box_bottom, '=', fg=border_color, bg=Colors.BLACK)
            for y in range(box_top, box_bottom + 1):
                render_char_safe(console, box_left, y, '|', fg=border_color, bg=Colors.BLACK)
                render_char_safe(console, box_right, y, '|', fg=border_color, bg=Colors.BLACK)
            
            return {
                'left': box_left,
                'right': box_right,
                'top': box_top,
                'bottom': box_bottom,
                'width': box_width,
                'height': height,
                'center_x': (box_left + box_right) // 2,
                'content_left': box_left + 2,
                'content_right': box_right - 2,
                'content_top': box_top + 1,
                'content_width': box_width - 4,
                'use_background_layout': False
            }
    
    def _clear_text_areas_only(self, console):
        """Create true separation: left 60% transparent for graphics, right 40% opaque for menu."""
        layout = self._get_menu_layout_params()
        
        if layout['use_background_layout']:
            # ENFORCED SEPARATION: 60% graphics area, 40% menu area
            graphics_boundary = int(console.width * 0.6)  # Hard boundary at 60%
            
            # Left 60%: Make transparent for SDL graphics
            for y in range(console.height):
                for x in range(0, graphics_boundary):
                    # Set background alpha to 0 (fully transparent)
                    console.rgba[x, y] = (
                        ord(' '),           # Empty character
                        (255, 255, 255, 0), # Transparent foreground
                        (0, 0, 0, 0)        # Transparent background
                    )
            
            # Right 40%: Clear for text menu (opaque)
            for y in range(console.height):
                for x in range(graphics_boundary, console.width):
                    render_char_safe(console, x, y, ' ', fg=(255, 255, 255), bg=(0, 0, 0))
        else:
            # ASCII mode: clear entire console
            console.clear()
    
    def render(self, console: tcod.console.Console) -> None:
        """Render the settings menu."""
        if self._has_background():
            self._clear_text_areas_only(console)
        else:
            console.clear()
        
        # Calculate menu height
        menu_height = 25  # Enough for title, options, and instructions
        
        # Render the right-side box using common method
        box = self._render_right_side_box(console, menu_height, Colors.WHITE)
        
        # Title
        title = "SETTINGS"
        if box['use_background_layout']:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        else:
            render_char_safe(console, box['center_x'] - len(title) // 2, box['top'] + 2, title, fg=Colors.WHITE, bg=Colors.BLACK)
        
        # Options
        start_y = box['top'] + 5
        for i, option in enumerate(self.options):
            color = Colors.YELLOW if i == self.selected_option else Colors.WHITE
            option_y = start_y + i * 2
            
            if box['use_background_layout']:
                # Narrow box layout
                name_x = box['content_left'] + 1
                
                # Option name (truncate if needed for narrow box)
                name = option["name"]
                if len(name) > 15:  # Truncate for narrow box
                    name = name[:12] + "..."
                render_char_safe(console, name_x, option_y, name, fg=color, bg=Colors.BLACK)
                
                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 8  # Shorter bar for narrow box
                    filled_length = int(bar_length * volume_percent / 100)
                    
                    # Volume bar - more compact
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    render_char_safe(console, name_x, option_y + 1, f"{bar} {volume_percent}%", fg=color, bg=Colors.BLACK)
                    
                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "ASCII"
                        render_char_safe(console, name_x, option_y + 1, f"< {current_value} >", fg=color, bg=Colors.BLACK)
            else:
                # ASCII mode - wider layout
                # Option name
                render_char_safe(console, box['content_left'] + 2, option_y, option["name"], fg=color, bg=Colors.BLACK)
                
                # Option value
                if option["type"] == "volume":
                    volume_percent = self.settings.get_volume_percent(option["key"])
                    bar_length = 20
                    filled_length = int(bar_length * volume_percent / 100)
                    
                    # Volume bar
                    bar = "[" + "=" * filled_length + "-" * (bar_length - filled_length) + "]"
                    render_char_safe(console, box['content_left'] + 18, option_y, f"{bar} {volume_percent}%", fg=color, bg=Colors.BLACK)
                    
                elif option["type"] == "toggle":
                    if option["key"] == "graphics_mode":
                        current_value = "Graphics" if self.settings.graphics_mode == "graphics" else "ASCII"
                        render_char_safe(console, box['content_left'] + 18, option_y, f"< {current_value} >", fg=color, bg=Colors.BLACK)
        
        # Instructions
        if box['use_background_layout']:
            # Compact instructions for narrow box
            instructions = [
                "↑↓: Navigate",
                "←→: Adjust", 
                "Enter: Select",
                "Esc: Back"
            ]
            inst_start_y = box['bottom'] - 6
        else:
            # Full instructions for ASCII mode
            instructions = [
                "Arrow Keys/WASD: Navigate",
                "Left/Right or A/D: Adjust volumes/toggle options", 
                "Enter: Select",
                "Escape: Back"
            ]
            inst_start_y = box['bottom'] - 6
        
        for i, instruction in enumerate(instructions):
            if box['use_background_layout']:
                # Center in narrow box
                inst_x = box['center_x'] - len(instruction) // 2
            else:
                # Center in wide box
                inst_x = box['center_x'] - len(instruction) // 2
            
            render_char_safe(console, inst_x, inst_start_y + i, instruction, fg=Colors.LIGHT_GRAY, bg=Colors.BLACK)
    
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
                
                # Immediately update background to reflect the change
                if self.menu_background:
                    self.menu_background.reload_if_mode_changed()
                    logging.info(f"Graphics mode changed to {new_mode} - background updated")
    
