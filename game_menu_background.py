#!/usr/bin/env python3
"""
Menu Background System - Split from game_menus.py
Handles high-resolution background images for main menu with conditional loading.
"""

import tcod
import logging
import time
import os
import random

from game_config import GameSettings
from game_ui import render_char_safe, WindowManager


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