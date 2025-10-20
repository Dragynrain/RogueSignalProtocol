#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Loop and Initialization

Main game loop, TCOD context initialization, and window management.
Handles menu navigation, game state transitions, and error recovery.
Coordinates rendering, input handling, and audio systems.
"""

import tcod
import time
import logging
import traceback

from game_config import GameConfig, GameSettings
from game_entities import Colors
from game_ui import render_char_safe, WindowManager
from game_audio import SoundManager
from game_menus import MenuBackground, MainMenu, SettingsMenu
from game_menu_help_lore import create_help_menu, LoreMenu
from game_menu_graphics_preview import GraphicsPreviewMenu
from game_engine import GameEngine
from game_engine_builder import GameEngineBuilder
from game_rendering_core import GameRenderer
from game_input import InputHandler
from game_graphics_tiles import TileManager


def load_tileset():
    """Load terminal tileset - no fallbacks, missing font indicates corrupt installation."""

    # Load terminal tileset
    # terminal10x16 means each glyph is 10 pixels wide x 16 pixels tall
    # The tilesheet has 16 columns x 16 rows of glyphs
    tileset = tcod.tileset.load_tilesheet(
        "terminal10x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )
    return tileset


def initialize_tcod_context():
    """Initialize tcod context with terminal font and SDL validation."""
    tileset = load_tileset()

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

    # Store tileset reference on context for later GlyphManager initialization
    context.tileset = tileset

    # Validate SDL renderer availability and set up console rendering
    if hasattr(context, 'sdl_renderer') and context.sdl_renderer:
        # Create console rendering objects for proper SDL + console mixing
        try:
            from tcod import render as tcod_render
            atlas = tcod_render.SDLTilesetAtlas(context.sdl_renderer, tileset)
            console_render = tcod_render.SDLConsoleRender(atlas)

            # Attach console render to context for later use
            context.console_render = console_render
        except Exception as e:
            logging.warning(f"Failed to initialize console rendering: {e}")
            context.console_render = None
    else:
        logging.warning("SDL renderer unavailable - graphics mode will be disabled")
        context.console_render = None

    return context




def initialize_game_systems(settings: GameSettings, context, menu_background=None, sound_manager=None, tile_manager=None):
    """Initialize menu systems and return menu objects."""
    # Initialize tile manager if not provided and graphics mode is enabled
    if tile_manager is None and settings.graphics_mode == "graphics":
        try:
            tile_manager = TileManager(context, settings)
        except Exception as e:
            logging.warning(f"Failed to initialize TileManager: {e}")
            tile_manager = None

    menus = {
        'main_menu': MainMenu(background=menu_background),  # Pass background here
        'settings_menu': SettingsMenu(settings, menu_background, sound_manager),  # Pass sound manager for live volume updates
        'help_menu': create_help_menu(settings, context, tile_manager),  # Use factory function
        'lore_menu': LoreMenu()
    }

    # Only add graphics preview menu if we have a tile manager
    if tile_manager is not None:
        menus['graphics_preview_menu'] = GraphicsPreviewMenu(context, settings, tile_manager)

    return menus


def handle_menu_navigation(console, context, menus, settings, menu_sound_manager=None, active_game=None):
    """
    Handle the main menu navigation loop.

    Args:
        active_game: If provided, this is a game in progress that should be resumed on "continue"
    """
    main_menu = menus['main_menu']
    main_menu.refresh_options(show_continue=True)
    current_menu = main_menu

    # Create sound manager if not provided
    if menu_sound_manager is None:
        menu_sound_manager = SoundManager(settings)

    # DO NOT start menu music if level music is already playing
    # Level music should continue playing when player returns to menu
    try:
        from game_audio import AUDIO_AVAILABLE
        import pygame

        # Only play menu music if NO music is currently playing
        if AUDIO_AVAILABLE and not pygame.mixer.music.get_busy():
            menu_sound_manager.play_music("main_menu.mp3", loops=-1, fade_in_ms=1000, volume_multiplier=1.56)
    except Exception as e:
        logging.warning(f"Could not play main menu music: {e}")
        # Continue without music
    
    while True:
        # Render console content first
        current_menu.render(console)

        # Check for background graphics (main menu, settings menu, etc.)
        has_background = (hasattr(current_menu, 'background') and
                         current_menu.background and
                         current_menu.background.should_load_background())

        # Check for sprite rendering (graphical help menu)
        has_sprites = hasattr(current_menu, 'render_sprites')

        # CORRECTED RENDERING: Use SDL renderer when available for graphics mode
        graphics_available = (context.sdl_renderer and hasattr(context, 'console_render') and
                            context.console_render and (has_background or has_sprites))

        if graphics_available:
            # Graphics mode: render everything through SDL
            context.sdl_renderer.clear()

            # Render background graphics to SDL first (if menu has background)
            if has_background:
                current_menu.background.render_background(console)

            # Render sprites to SDL (if menu has sprites, like GraphicalHelpMenu)
            if has_sprites:
                current_menu.render_sprites()

            # Render console content as texture to SDL
            console_texture = context.console_render.render(console)

            # Render full console texture to preserve internal character positioning
            # The console has transparent areas for background graphics or sprites
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
                elif action == "graphics_preview":
                    if 'graphics_preview_menu' in menus:
                        # Enter graphics preview mode
                        graphics_preview_menu = menus['graphics_preview_menu']

                        # Flush any pending events to avoid immediate exit
                        tcod.event.get()

                        exit_preview = False
                        while not exit_preview:
                            # Render the preview menu to console
                            graphics_preview_menu.render(console)

                            # Check if we should render graphics
                            graphics_available = (context.sdl_renderer and
                                                hasattr(context, 'console_render') and
                                                context.console_render and
                                                settings.graphics_mode == "graphics")

                            if graphics_available:
                                # Graphics mode: render through SDL with preview map
                                context.sdl_renderer.clear()

                                # Render the preview map graphics FIRST (background)
                                graphics_preview_menu._render_preview_map(console)

                                # Then render console text on top
                                console_texture = context.console_render.render(console)
                                context.sdl_renderer.copy(console_texture)
                                context.sdl_renderer.present()
                            else:
                                # Glyph mode: just show console
                                context.present(console)

                            # Process events (non-blocking for continuous animation)
                            for preview_event in tcod.event.get():
                                if preview_event.type == "QUIT":
                                    # Export selections and return to main menu on quit
                                    graphics_preview_menu.export_selections()
                                    exit_preview = True
                                    break
                                elif preview_event.type == "KEYDOWN":
                                    preview_action = graphics_preview_menu.handle_input(preview_event)
                                    if preview_action == 'exit':
                                        # Export selections and return to main menu
                                        graphics_preview_menu.export_selections()
                                        exit_preview = True
                                        break

                            # Small delay to prevent CPU spinning (60 FPS)
                            time.sleep(1/60)

                        # Cleanup SDL renderer state before returning to main menu
                        if graphics_available and context.sdl_renderer:
                            context.sdl_renderer.draw_color = (0, 0, 0, 255)
                            context.sdl_renderer.clear()

                        # Return to main menu after exiting preview
                        current_menu = main_menu
                    else:
                        # Graphics preview not available
                        logging.warning("Graphics Preview not available")
                elif action == "back":
                    current_menu = main_menu
                elif action == "continue":
                    # Don't stop music if it's level music playing from previous session
                    # Only stop if menu music was actually started (current_music is set)
                    if menu_sound_manager.current_music is not None:
                        menu_sound_manager.stop_music(fade_out_ms=1000)

                    # If there's an active game in progress, resume it
                    # Otherwise, load from save file
                    if active_game is not None:
                        return active_game, False
                    else:
                        game = GameEngineBuilder().with_settings(settings).load_from_save().build()
                        return game, False
                elif action == "new_game":
                    # Stop any music for new game - fresh start
                    menu_sound_manager.stop_music(fade_out_ms=1000)
                    game = GameEngineBuilder().with_settings(settings).build()
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
            # Priority 1: If dialogue is active, let it handle escape first
            if game.dialogue_state.is_active():
                should_continue = input_handler._handle_dialogue_dismiss()
                if not should_continue:
                    # Death/victory dialogue wants to exit to menu
                    return True, None
                return True, game
            # Check if any UI states are open - close those first
            elif (game.show_story_fragment is not None or
                game.show_lore_viewer or
                game.show_help or
                game.show_inventory or
                game.look_mode or
                game.targeting_mode):
                input_handler._handle_escape()
            else:
                # No UI states open, auto-save and go to main menu
                game.auto_save()
                # Don't stop level music - let it continue playing in the menu
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
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
            
            settings = GameSettings()
            
            # Create background manager (loads conditionally based on graphics mode)
            menu_background = MenuBackground(context, settings)
            menu_background.reset_background_system()  # Reset any previous errors
            menu_background.load_random_background()  # Only loads if graphics mode enabled

            # Create persistent sound manager for menus
            menu_sound_manager = SoundManager(settings)
            menu_sound_manager.preload_sounds()  # Preload for sound previews

            # Pass background and sound manager to initialize_game_systems
            menus = initialize_game_systems(settings, context, menu_background, menu_sound_manager)

            game = None

            # Track the active game across menu returns
            active_game_session = None

            while True:
                # Check for graphics mode changes and reload accordingly
                menu_background.reload_if_mode_changed()

                if game is None:
                    # Pass active_game_session to handle_menu_navigation so it can resume
                    game, should_exit = handle_menu_navigation(console, context, menus, settings, menu_sound_manager, active_game_session)
                    if should_exit:
                        # Cleanup background before exit
                        menu_background.cleanup()
                        return
                    
                    # Initialize tile manager for graphics mode
                    tile_manager = None
                    if settings.graphics_mode == "graphics":
                        try:
                            tile_manager = TileManager(context, settings)
                            tile_manager.preload_common_tiles()
                        except Exception as e:
                            logging.error(f"Failed to initialize TileManager: {e}")
                            logging.error("Graphics mode will fall back to glyph mode")

                    # Initialize game rendering systems
                    renderer = GameRenderer(settings, tile_manager=tile_manager, context=context)
                    input_handler = InputHandler(game, renderer=renderer)
                    show_welcome_messages(game)

                # Main game loop
                last_render_time = time.time()
                render_interval = 1.0 / 30.0  # 30 FPS for smooth pulsing animation

                while game is not None:
                    try:
                        game.sound_manager.update()

                        # In graphics mode, render continuously at fixed frame rate
                        # In glyph mode, only render when there are events
                        if settings.graphics_mode == "graphics":
                            current_time = time.time()

                            # Render at fixed frame rate
                            if current_time - last_render_time >= render_interval:
                                renderer.render_game(console, game, context)
                                last_render_time = current_time

                            # Get all available events (non-blocking)
                            events = tcod.event.get()

                            # If no events, sleep briefly to avoid CPU spinning
                            if not events:
                                time.sleep(0.001)  # Sleep 1ms to avoid busy-waiting
                                continue
                        else:
                            # Glyph mode: event-driven rendering
                            renderer.render_game(console, game, context)
                            context.present(console)

                            # Wait for events (blocking)
                            events = list(tcod.event.wait())

                        # Handle input events
                        for event in events:
                            # Save game reference before it potentially becomes None
                            previous_game = game
                            should_continue, game = handle_game_input_events(event, game, input_handler)
                            if not should_continue:
                                return  # Exit program
                            if game is None:
                                # Player returned to menu - save the active game session
                                active_game_session = previous_game

                                # Cleanup SDL renderer state before returning to main menu
                                if context.sdl_renderer:
                                    context.sdl_renderer.draw_color = (0, 0, 0, 255)
                                    context.sdl_renderer.clear()

                                break  # Return to main menu
                        
                    except Exception as e:
                        import traceback
                        tb = traceback.extract_tb(e.__traceback__)
                        line_no = tb[-1].lineno if tb else "?"
                        filename = tb[-1].filename if tb else "unknown"

                        error_msg = f"SYSTEM ERROR: Rendering failure in {filename}:{line_no}"
                        logging.error(error_msg)
                        logging.error(f"Exception: {str(e)}")
                        logging.error(f"Exception type: {type(e).__name__}")

                        # Print full traceback for debugging
                        traceback.print_exc()

                        if handle_error_screen(console, context, e, line_no):
                            return
    
    except Exception as e:
        import traceback
        tb = traceback.extract_tb(e.__traceback__)
        line_no = tb[-1].lineno if tb else "?"
        filename = tb[-1].filename if tb else "unknown"

        error_msg = f"CRITICAL SYSTEM ERROR: Game initialization/main loop failure in {filename}:{line_no}"
        logging.critical(error_msg)
        logging.critical(f"Exception: {str(e)}")
        logging.critical(f"Exception type: {type(e).__name__}")

        # Print full traceback for debugging
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback

        error_msg = f"CRITICAL UNHANDLED EXCEPTION: Program termination"
        logging.critical(error_msg)
        logging.critical(f"Exception: {str(e)}")
        logging.critical(f"Exception type: {type(e).__name__}")

        # Print full traceback for debugging
        traceback.print_exc()
        raise