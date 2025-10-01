#!/usr/bin/env python3
"""
Game Loop and Initialization - Split from RogueSignalProtocol.py
Contains main game loop, window management, and initialization functions.
"""

import tcod
import time
import logging
import traceback

from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_ui import render_char_safe, WindowManager
from game_audio import SoundManager
from game_menus import MenuBackground, MainMenu, SettingsMenu, HelpMenu, LoreMenu
from game_engine import GameEngine
from game_rendering import Renderer
from game_input import InputHandler


def load_tileset():
    """Load terminal tileset - no fallbacks, missing font indicates corrupt installation."""
    
    # Load terminal tileset
    tileset = tcod.tileset.load_tilesheet(
        "terminal10x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )
    logging.info("Loaded terminal tileset successfully")
    
    return tileset


def initialize_tcod_context():
    """Initialize tcod context with terminal font and SDL validation."""
    tileset = load_tileset()
    
    logging.info("Using terminal font")
    
    context_args = {
        "columns": GameConfig.SCREEN_WIDTH,
        "rows": GameConfig.SCREEN_HEIGHT,
        "title": "Rogue Signal Protocol",
        "vsync": True,
        "sdl_window_flags": 160  # Resizable window
    }
    
    if tileset:
        context_args["tileset"] = tileset
    
    context = tcod.context.new(**context_args)
    
    # Validate SDL renderer availability and set up console rendering
    if hasattr(context, 'sdl_renderer') and context.sdl_renderer:
        logging.info("SDL renderer available for graphics mode")
        
        # Create console rendering objects for proper SDL + console mixing
        try:
            from tcod import render as tcod_render
            atlas = tcod_render.SDLTilesetAtlas(context.sdl_renderer, tileset)
            console_render = tcod_render.SDLConsoleRender(atlas)
            
            # Attach console render to context for later use
            context.console_render = console_render
            logging.info("Console texture rendering initialized successfully")
        except Exception as e:
            logging.warning(f"Failed to initialize console rendering: {e}")
            context.console_render = None
    else:
        logging.warning("SDL renderer unavailable - graphics mode will be disabled")
        context.console_render = None
    
    return context




def initialize_game_systems(settings: GameSettings, menu_background=None):
    """Initialize menu systems and return menu objects."""
    return {
        'main_menu': MainMenu(background=menu_background),  # Pass background here
        'settings_menu': SettingsMenu(settings, menu_background),  # Pass background for immediate updates
        'help_menu': HelpMenu(),
        'lore_menu': LoreMenu()
    }


def handle_menu_navigation(console, context, menus, settings):
    """Handle the main menu navigation loop."""
    main_menu = menus['main_menu']
    main_menu.refresh_options(show_continue=True)
    current_menu = main_menu
    
    # Start main menu music only if no music is already playing
    menu_sound_manager = SoundManager(settings)
    try:
        if not menu_sound_manager.is_music_playing():
            menu_sound_manager.play_music("main_menu.mp3", loops=-1, fade_in_ms=1000, volume_multiplier=1.3)
    except Exception as e:
        logging.warning(f"Could not play main menu music: {e}")
        # Continue without music
    
    while True:
        # Render console content first
        current_menu.render(console)
        
        # CORRECTED RENDERING: Use SDL renderer when available for graphics mode
        graphics_available = (context.sdl_renderer and hasattr(context, 'console_render') and 
                            context.console_render and hasattr(current_menu, 'background') and 
                            current_menu.background and current_menu.background.should_load_background())
        
        if graphics_available:
            # Graphics mode: render everything through SDL
            context.sdl_renderer.clear()
            
            # Render background graphics to SDL first
            current_menu.background.render_background(console)
            
            # Render console content as texture to SDL
            console_texture = context.console_render.render(console)
            
            # Render full console texture to preserve internal character positioning
            # The console has transparent areas on the left side for background graphics
            context.sdl_renderer.copy(console_texture)
            
            # Present everything through SDL
            context.sdl_renderer.present()
            
        else:
            # ASCII mode or fallback: normal console presentation
            context.present(console)
        
        for event in tcod.event.wait():
            if event.type == "QUIT":
                menu_sound_manager.cleanup()
                return None, True  # game=None, should_exit=True
            elif event.type == "KEYDOWN":
                action = current_menu.handle_input(event)
                
                if action == "exit":
                    menu_sound_manager.cleanup()
                    return None, True  # game=None, should_exit=True
                elif action == "settings":
                    current_menu = menus['settings_menu']
                elif action == "help":
                    current_menu = menus['help_menu']
                elif action == "lore":
                    current_menu = menus['lore_menu']
                elif action == "back":
                    current_menu = main_menu
                elif action == "continue":
                    menu_sound_manager.stop_music(fade_out_ms=1000)  # Fade out menu music
                    game = GameEngine(load_save=True, settings=settings)
                    return game, False
                elif action == "new_game":
                    menu_sound_manager.stop_music(fade_out_ms=1000)  # Fade out menu music
                    game = GameEngine(load_save=False, settings=settings)
                    return game, False


def show_welcome_messages(game):
    """Show initial welcome messages for new games."""
    # Welcome messages removed to reduce startup spam
    pass


def handle_game_input_events(event, game, input_handler):
    """Handle game input events and return (should_continue, game)."""
    if event.type == "QUIT":
        game.auto_save()
        game.sound_manager.cleanup()
        return False, None  # Exit program
    elif event.type == "KEYDOWN":
        if event.sym == tcod.event.KeySym.ESCAPE:
            # Check if any UI states are open - close those first
            if (game.show_story_fragment is not None or 
                game.show_lore_viewer or 
                game.show_help or 
                game.show_inventory or 
                game.targeting_mode):
                input_handler._handle_escape()
            else:
                # No UI states open, auto-save and go to main menu
                game.auto_save()
                return True, None  # Return to main menu
        else:
            should_continue = input_handler.handle_keydown(event)
            if not should_continue:
                # Player is dead and pressed ESC - return to main menu
                return True, None
    return True, game


def handle_error_screen(console, context, error_message, line_no):
    """Display error screen and wait for user input."""
    console.clear()
    render_char_safe(console, 1, 1, f"Error: {str(error_message)[:50]} (line {line_no})", fg=Colors.RED)
    render_char_safe(console, 1, 2, "Press ESC to exit", fg=Colors.WHITE)
    context.present(console)
    
    for event in tcod.event.wait():
        if event.type == "QUIT" or (event.type == "KEYDOWN" and event.sym == tcod.event.KeySym.ESCAPE):
            return True
    return False


def main():
    """Main game loop with main menu and save/load functionality."""
    # Initialize JSON configuration system
    GameConfig.load_from_json()
    
    try:
        with initialize_tcod_context() as context:
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT, order='F')
            
            settings = GameSettings()
            
            # Create background manager (loads conditionally based on graphics mode)
            menu_background = MenuBackground(context, settings)
            menu_background.reset_background_system()  # Reset any previous errors
            menu_background.load_random_background()  # Only loads if graphics mode enabled
            
            # Pass background to initialize_game_systems
            menus = initialize_game_systems(settings, menu_background)
            
            game = None
            
            while True:
                # Check for graphics mode changes and reload accordingly
                menu_background.reload_if_mode_changed()
                
                if game is None:
                    game, should_exit = handle_menu_navigation(console, context, menus, settings)
                    if should_exit:
                        # Cleanup background before exit
                        menu_background.cleanup()
                        return
                    
                    # Initialize game rendering systems
                    renderer = Renderer(settings)
                    input_handler = InputHandler(game)
                    show_welcome_messages(game)

                # Main game loop
                while game is not None:
                    try:
                        game.sound_manager.update()
                        renderer.render_game(console, game, context)
                        context.present(console)
                        
                        # Handle input events
                        for event in tcod.event.wait():
                            should_continue, game = handle_game_input_events(event, game, input_handler)
                            if not should_continue:
                                return  # Exit program
                            if game is None:
                                break  # Return to main menu
                        
                    except Exception as e:
                        import traceback
                        tb = traceback.extract_tb(e.__traceback__)
                        line_no = tb[-1].lineno if tb else "?"
                        logging.error(f"Rendering error: {e} (line {line_no})")
                        
                        if handle_error_screen(console, context, e, line_no):
                            return
    
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        line_no = tb[-1].lineno if tb else "?"
        logging.critical(f"Critical error: {e} (line {line_no})")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical(f"Unhandled exception: {e}")
        raise