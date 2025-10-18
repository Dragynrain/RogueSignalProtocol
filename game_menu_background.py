#!/usr/bin/env python3
"""
Menu Background System - Extracted from game_menus.py
Handles high-resolution background images for main menu with conditional loading.
"""

import tcod
import logging
import time
import os
import random
import sys

# Import game modules
from game_config import GameSettings, GameConfig
from game_entities import Colors
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
        self.image_size = None
        self.last_known_mode = settings.graphics_mode
        
    def reset_background_system(self):
        """Reset background system and re-enable graphics."""
        self.enabled = True
        logging.info("Background graphics system reset and re-enabled")

    def should_load_background(self):
        """Check if background should be loaded based on graphics mode."""
        return (self.settings.graphics_mode == "graphics" and 
                self.enabled and 
                self.context.sdl_renderer is not None)
    
    def _handle_background_error(self, message, exception=None):
        """Simple error handling - log and disable graphics."""
        error_msg = f"Background graphics error: {message}"
        print(error_msg)
        logging.warning(error_msg)
        if exception:
            logging.warning(f"Exception: {str(exception)}")
        self.enabled = False
    
    def _get_image_path(self, image_number):
        """Build path to image file."""
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, "main_menu", f"main_menu_{image_number}.png")
        
    def load_random_background(self):
        """Load one random menu background. If it fails, disable graphics mode."""
        if not self.should_load_background():
            return False

        image_num = random.randint(1, 25)
        image_path = self._get_image_path(image_num)

        try:
            if self._load_image_file(image_path):
                self.current_image_path = image_path
                logging.info(f"Loaded background: main_menu_{image_num}.png")
                return True
            return False
        except Exception as e:
            self._handle_background_error(f"Failed to load {image_path}", e)
            return False
    
    
    def _load_image_file(self, image_path):
        """Load image file and create SDL texture."""
        if not os.path.exists(image_path):
            return False

        try:
            from PIL import Image
            import numpy as np

            # Load and convert image
            pil_image = Image.open(image_path)
            if pil_image.mode == 'RGBA':
                background = Image.new('RGB', pil_image.size, (0, 0, 0))
                background.paste(pil_image, mask=pil_image.split()[-1])
                pil_image = background
            elif pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            self.image_size = pil_image.size
            pixels = np.array(pil_image, dtype=np.uint8)

            # Create SDL texture
            renderer = self.context.sdl_renderer
            if not renderer:
                return False

            self.background_texture = renderer.upload_texture(pixels)
            return self.background_texture is not None

        except Exception as e:
            logging.warning(f"Failed to load background image: {str(e)}")
            return False

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
        random.seed(42)  # Consistent pattern
        
        from data_loading import DataLoader
        config = DataLoader.load_config()
        menu_bg_colors = config.get("colors", {}).get("menu_background", {})
        pattern_colors_data = menu_bg_colors.get("pattern_colors", [])
        colors = [ensure_color_tuple(c) for c in pattern_colors_data]
        base_bg = ensure_color_tuple(menu_bg_colors.get("base", [5, 5, 15]))
        black = ensure_color_tuple(config.get("colors", {}).get("basic", {}).get("black", [0, 0, 0]))

        patterns = ['▓', '▒', '░', '·', '▪', '▫']

        for y in range(console.height):
            for x in range(start_x, min(end_x, console.width)):
                # Higher density for side panels
                if random.random() < 0.25:  # 25% density
                    pattern_char = random.choice(patterns)
                    fg_color = random.choice(colors)
                    # Use dark background to make pattern visible
                    render_char_safe(console, x, y, pattern_char, fg=fg_color, bg=base_bg)
                else:
                    # Fill with dark background
                    render_char_safe(console, x, y, ' ', fg=black, bg=base_bg)

    def _render_borders(self, console):
        """Add cyberpunk-style borders."""
        from data_loading import DataLoader
        config = DataLoader.load_config()
        menu_bg_colors = config.get("colors", {}).get("menu_background", {})
        border_color = ensure_color_tuple(menu_bg_colors.get("border", [0, 150, 200]))
        base_bg = ensure_color_tuple(menu_bg_colors.get("base", [5, 5, 15]))

        # Top border
        for x in range(console.width):
            render_char_safe(console, x, 0, '─', fg=border_color, bg=base_bg)

        # Bottom border
        for x in range(console.width):
            render_char_safe(console, x, console.height - 1, '─', fg=border_color, bg=base_bg)
    
    def _render_center_atmosphere(self, console):
        """Add subtle atmospheric elements to center area."""
        random.seed(123)  # Different seed for center
        
        # Very subtle dots in center area (positions 26-54)
        from data_loading import DataLoader
        config = DataLoader.load_config()
        menu_bg_colors = config.get("colors", {}).get("menu_background", {})
        dots_color = ensure_color_tuple(menu_bg_colors.get("dots", [0, 60, 100]))
        black = ensure_color_tuple(config.get("colors", {}).get("basic", {}).get("black", [0, 0, 0]))

        for y in range(2, console.height - 2):
            for x in range(26, 54):
                if random.random() < 0.02:  # Very low density - 2%
                    render_char_safe(console, x, y, '·', fg=dots_color, bg=black)
        
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
        elif current_mode == "glyph" and has_texture:
            # Mode switched to glyph mode - free memory
            if mode_changed:
                logging.info("Glyph mode enabled - cleaning up background")
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
    
    def cleanup(self):
        """Free background texture memory."""
        self.background_texture = None
        self.current_image_path = None
        self.image_size = None