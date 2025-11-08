#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Loop and Initialization

Main game loop, TCOD context initialization, and window management.
Handles menu navigation, game state transitions, and error recovery.
Coordinates rendering, input handling, and audio systems.
"""

# CRITICAL: Set DPI awareness BEFORE importing tcod to ensure proper scaling
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback for Windows 7/8
    except Exception:
        pass  # DPI awareness unavailable - game will still run but may be scaled by Windows

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
from game_menu_achievements import AchievementsMenu
from game_menu_graphics_preview import GraphicsPreviewMenu
from game_menu_about import AboutMenu
from game_engine import GameEngine
from game_rendering_core import GameRenderer
from game_input import InputHandler
from game_graphics_tiles import TileManager
from game_coordinate_helpers import CoordinateHelpers
from game_mouse_utils import MenuMouseHandler


def log_exception(e: Exception, context: str, level: str = "error"):
    """
    Centralized exception logging with traceback details.

    Args:
        e: The exception to log
        context: Description of where/what failed (e.g., "Rendering failure", "Game initialization")
        level: Logging level - "error", "critical", or "warning"
    """
    tb = traceback.extract_tb(e.__traceback__)
    line_no = tb[-1].lineno if tb else "?"
    filename = tb[-1].filename if tb else "unknown"

    log_func = getattr(logging, level, logging.error)
    log_func(f"{context} in {filename}:{line_no}")
    log_func(f"Exception: {str(e)}")
    log_func(f"Exception type: {type(e).__name__}")
    traceback.print_exc()


def load_tileset():
    """
    Load TrueType font tileset using custom FreeType loader.

    TCOD's native loader has "fit without stretching" behavior that leaves
    tons of empty space. Custom loader gives us full control over scaling.
    """
    from font_loader_freetype import load_truetype_font_custom

    # Use 64x64 tiles with KreativeSquare (square 1:1 aspect ratio font)
    tileset = load_truetype_font_custom(
        "KreativeSquare.ttf",
        64,  # tile_width
        64   # tile_height
    )
    return tileset


def initialize_tcod_context():
    """Initialize tcod context with terminal font and SDL validation."""
    tileset = load_tileset()

    context_args = {
        "columns": GameConfig.SCREEN_WIDTH,
        "rows": GameConfig.SCREEN_HEIGHT,
        "width": 1920,   # Explicit window width in pixels (1920×1080 = Full HD)
        "height": 1080,  # Explicit window height in pixels
        "title": "Rogue Signal Protocol",
        "vsync": True,
        "sdl_window_flags": 160  # Maximized + resizable
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
        'main_menu': None,  # Will be set after menus dict is complete
        'settings_menu': SettingsMenu(settings, menu_background, sound_manager),  # Pass sound manager for live volume updates
        'help_menu': create_help_menu(settings, context, tile_manager),  # Use factory function
        '_help_menu_mode': settings.graphics_mode,  # Track mode used to create help menu
        '_context': context,  # Store for help menu recreation
        '_tile_manager': tile_manager,  # Store for help menu recreation
        'lore_menu': LoreMenu(),
        'achievements_menu': AchievementsMenu(),
        'about_menu': AboutMenu(menu_background, settings)
    }

    # Only add graphics preview menu if we have a tile manager
    if tile_manager is not None:
        menus['graphics_preview_menu'] = GraphicsPreviewMenu(context, settings, tile_manager)

    # Now create main menu with reference to menus dict (so it can check if graphics_preview_menu exists)
    menus['main_menu'] = MainMenu(background=menu_background, settings=settings, menus=menus)

    return menus


def handle_menu_navigation(console, context, menus, settings, menu_sound_manager=None, active_game=None):
    """
    Handle the main menu navigation loop.

    Args:
        active_game: If provided, this is a game in progress that should be resumed on "continue"
    """
    main_menu = menus['main_menu']
    main_menu.refresh_options(show_continue=True, active_game=active_game)
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
            menu_sound_manager.play_music("main_menu.ogg", loops=-1, fade_in_ms=1000)
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

            # Render console texture to fill entire window (no aspect ratio preservation)
            # This matches the user's expectation for full-screen console
            console_texture = context.console_render.render(console)

            window_w, window_h = context.sdl_window.size

            # Fill entire window - no letterboxing
            dest_rect = (0, 0, window_w, window_h)
            context.sdl_renderer.copy(console_texture, dest=dest_rect)

            # Present everything through SDL
            context.sdl_renderer.present()

        else:
            # ASCII mode or fallback: normal console presentation
            context.present(console)
        
        for event in tcod.event.wait():
            # Convert pixel coordinates to tile coordinates for menu mouse events
            if event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
                converted_event = MenuMouseHandler.convert_to_tile_coords(event, context)
                if converted_event is not None:
                    event = converted_event

            if event.type == "QUIT":
                menu_sound_manager.cleanup()
                return None, True  # game=None, should_exit=True
            elif event.type == "MOUSEMOTION":
                # Handle mouse hover on menu options
                current_menu.handle_mouse_motion(event)
            elif event.type == "MOUSEBUTTONDOWN":
                # Handle mouse clicks on menu options
                action = current_menu.handle_mouse_click(event)

                if action == "exit":
                    # Save active game before exiting if one exists and player is alive
                    if active_game is not None and active_game.player.cpu > 0 and not active_game.game_over:
                        active_game.auto_save()
                    menu_sound_manager.cleanup()
                    return None, True  # game=None, should_exit=True
                elif action == "export_debug_confirmed":
                    # Export debug package from settings menu (user confirmed)
                    from debug_export import export_debug_package

                    logging.info("Debug Export: Starting debug package creation from settings menu")
                    zip_path = export_debug_package(game_engine=active_game)
                    if zip_path:
                        filename = zip_path.name
                        logging.info(f"Debug Export: Success from settings menu - {zip_path}")
                        # Show success message via settings menu
                        # Note: We can't show messages directly in menu context, but logging is sufficient
                        # The user will see the file in debug_exports/ folder
                    else:
                        logging.error("Debug Export: Failed to create package from settings menu")
                    # Stay in settings menu
                elif action == "settings":
                    current_menu = menus['settings_menu']
                elif action == "help":
                    # Only recreate help menu if graphics mode changed (preserves page state)
                    if menus.get('_help_menu_mode') != settings.graphics_mode:
                        logging.info(f"Graphics mode changed, recreating help menu: {menus.get('_help_menu_mode')} -> {settings.graphics_mode}")
                        menus['help_menu'] = create_help_menu(settings, menus['_context'], menus['_tile_manager'])
                        menus['_help_menu_mode'] = settings.graphics_mode
                    current_menu = menus['help_menu']
                elif action == "lore":
                    current_menu = menus['lore_menu']
                elif action == "about":
                    current_menu = menus['about_menu']
                elif action == "achievements":
                    current_menu = menus['achievements_menu']
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
                                # CRITICAL: Set draw color to BLACK before clear() to avoid white background
                                context.sdl_renderer.draw_color = (0, 0, 0, 255)
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
                                # Convert pixel coordinates to tile coordinates for mouse events
                                if preview_event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
                                    converted_event = MenuMouseHandler.convert_to_tile_coords(preview_event, context)
                                    if converted_event is not None:
                                        preview_event = converted_event

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
                                elif preview_event.type == "MOUSEMOTION":
                                    # Handle mouse motion (highlight arrows on hover)
                                    graphics_preview_menu.handle_mouse_motion(preview_event)
                                elif preview_event.type == "MOUSEBUTTONDOWN":
                                    # Handle mouse clicks (cycle variants when clicking arrows)
                                    graphics_preview_menu.handle_mouse_click(preview_event)

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
                    # Refresh main menu options in case graphics mode changed
                    main_menu.refresh_options(show_continue=True, active_game=active_game)
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
                        game = GameEngine(settings=settings, load_save=True)
                        return game, False
                elif action == "new_game":
                    # Stop any music for new game - fresh start
                    menu_sound_manager.stop_music(fade_out_ms=1000)
                    game = GameEngine(settings=settings)
                    return game, False

            elif event.type == "MOUSEWHEEL":
                # Handle mouse wheel events in menus (e.g., scrolling help pages)
                if hasattr(current_menu, 'handle_mouse_wheel'):
                    current_menu.handle_mouse_wheel(event)

            elif event.type == "KEYDOWN":
                action = current_menu.handle_input(event)

                if action == "exit":
                    # Save active game before exiting if one exists and player is alive
                    if active_game is not None and active_game.player.cpu > 0 and not active_game.game_over:
                        active_game.auto_save()
                    menu_sound_manager.cleanup()
                    return None, True  # game=None, should_exit=True
                elif action == "export_debug_confirmed":
                    # Export debug package from settings menu (user confirmed)
                    from debug_export import export_debug_package

                    logging.info("Debug Export: Starting debug package creation from settings menu")
                    zip_path = export_debug_package(game_engine=active_game)
                    if zip_path:
                        filename = zip_path.name
                        logging.info(f"Debug Export: Success from settings menu - {zip_path}")
                        # Show success message via settings menu
                        # Note: We can't show messages directly in menu context, but logging is sufficient
                        # The user will see the file in debug_exports/ folder
                    else:
                        logging.error("Debug Export: Failed to create package from settings menu")
                    # Stay in settings menu
                elif action == "settings":
                    current_menu = menus['settings_menu']
                elif action == "help":
                    # Only recreate help menu if graphics mode changed (preserves page state)
                    if menus.get('_help_menu_mode') != settings.graphics_mode:
                        logging.info(f"Graphics mode changed, recreating help menu: {menus.get('_help_menu_mode')} -> {settings.graphics_mode}")
                        menus['help_menu'] = create_help_menu(settings, menus['_context'], menus['_tile_manager'])
                        menus['_help_menu_mode'] = settings.graphics_mode
                    current_menu = menus['help_menu']
                elif action == "lore":
                    current_menu = menus['lore_menu']
                elif action == "about":
                    current_menu = menus['about_menu']
                elif action == "achievements":
                    current_menu = menus['achievements_menu']
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
                                # CRITICAL: Set draw color to BLACK before clear() to avoid white background
                                context.sdl_renderer.draw_color = (0, 0, 0, 255)
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
                                # Convert pixel coordinates to tile coordinates for mouse events
                                if preview_event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
                                    converted_event = MenuMouseHandler.convert_to_tile_coords(preview_event, context)
                                    if converted_event is not None:
                                        preview_event = converted_event

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
                                elif preview_event.type == "MOUSEMOTION":
                                    # Handle mouse motion (highlight arrows on hover)
                                    graphics_preview_menu.handle_mouse_motion(preview_event)
                                elif preview_event.type == "MOUSEBUTTONDOWN":
                                    # Handle mouse clicks (cycle variants when clicking arrows)
                                    graphics_preview_menu.handle_mouse_click(preview_event)

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
                    # Refresh main menu options in case graphics mode changed
                    main_menu.refresh_options(show_continue=True, active_game=active_game)
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
                        game = GameEngine(settings=settings, load_save=True)
                        return game, False
                elif action == "new_game":
                    # Stop any music for new game - fresh start
                    menu_sound_manager.stop_music(fade_out_ms=1000)
                    game = GameEngine(settings=settings)
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
    elif event.type == "MOUSEMOTION":
        # Handle mouse motion events (cursor updates, hover effects)
        input_handler.handle_mouse_motion(event)
    elif event.type == "MOUSEBUTTONDOWN":
        # Handle mouse click events
        should_continue = input_handler.handle_mouse_click(event)
        if should_continue is not None and not should_continue:
            # Death/victory dialogue was dismissed with click - return to main menu
            return True, None
    elif event.type == "MOUSEWHEEL":
        # Handle mouse wheel events (scrolling)
        input_handler.handle_mouse_wheel(event)
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
                game.show_achievements or
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

    # Initialize achievement system with unlocked achievements from progress file
    from game_achievements import AchievementManager
    from game_metrics import load_unlocked_achievements
    unlocked_achievements = load_unlocked_achievements()
    AchievementManager.load_unlocked_achievements(unlocked_achievements)
    logging.info(f"Loaded {len(unlocked_achievements)} unlocked achievements")

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

                    # Store tile_manager on game object for particle effects
                    game.tile_manager = tile_manager

                    # Initialize game rendering systems
                    renderer = GameRenderer(settings, tile_manager=tile_manager, context=context)
                    input_handler = InputHandler(game, renderer=renderer)
                    show_welcome_messages(game)

                # Main game loop
                last_render_time = time.time()
                render_interval = 1.0 / 30.0  # 30 FPS for smooth pulsing animation

                # Victory screen handling
                victory_screen = None
                victory_background = None

                while game is not None:
                    # Check if victory screen should be shown
                    if game.game_state.show_victory_screen and victory_screen is None:
                        # Create victory background with ending art
                        victory_background = MenuBackground(context, settings, art_directory="ending")
                        victory_background.load_random_background()

                        # Import and create victory screen
                        from game_victory_screen import VictoryScreen
                        victory_screen = VictoryScreen(background=victory_background)

                        logging.info("Victory screen initialized")

                    # If victory screen is active, render it instead of the game
                    if victory_screen is not None:
                        try:
                            # Render victory background
                            if victory_background and victory_background.should_load_background():
                                victory_background.render_background(console)

                            # Render victory screen
                            victory_screen.render(console)
                            context.present(console)

                            # Handle victory screen input
                            for event in tcod.event.wait():
                                if event.type == "QUIT":
                                    return  # Exit program
                                elif victory_screen.handle_input(event):
                                    # Victory screen dismissed - return to main menu
                                    logging.info("Victory screen dismissed - returning to main menu")
                                    victory_background.cleanup()
                                    game = None
                                    break
                        except Exception as e:
                            log_exception(e, "Victory screen rendering/input")
                            # On error, return to main menu
                            if victory_background:
                                victory_background.cleanup()
                            game = None
                        continue  # Skip normal game loop processing
                    try:
                        game.sound_manager.update()

                        # Execute auto-walk if active (before handling other input)
                        if game.autowalk.is_active() and not game.dialogue_state.is_active():
                            # Get next move from auto-walk
                            next_move = game.autowalk.get_next_move(game)

                            if next_move:
                                dx, dy = next_move
                                # Execute the move (processes a turn)
                                game.move_player(dx, dy)
                                game.autowalk.advance_step()

                                # Check stop conditions after the move
                                should_stop, reason = game.autowalk.check_stop_conditions(game)
                                if should_stop:
                                    game.autowalk.stop(reason)
                                    if reason and reason != "Destination reached":
                                        # Notify player why auto-walk stopped (except for normal completion)
                                        game.message_log.add_message(f"Auto-walk stopped: {reason}")
                                # Small delay for auto-walk to feel responsive but not instant
                                time.sleep(0.1)

                        # In graphics mode, render continuously at fixed frame rate
                        # In glyph mode, only render when there are events
                        if settings.graphics_mode == "graphics":
                            current_time = time.time()

                            # Render at fixed frame rate
                            if current_time - last_render_time >= render_interval:
                                # Update particle system with delta time
                                delta_time = current_time - last_render_time
                                if hasattr(game, 'particle_system') and game.particle_system is not None:
                                    game.particle_system.update(delta_time)

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

                        # PERFORMANCE FIX: Filter out redundant mouse motion events
                        # Only keep the LAST mouse motion event to avoid processing hundreds per frame
                        filtered_events = []
                        last_mouse_motion = None

                        for event in events:
                            if event.type == "MOUSEMOTION":
                                # Keep only the most recent mouse motion
                                last_mouse_motion = event
                            else:
                                # Keep all non-motion events
                                filtered_events.append(event)

                        # Add the last mouse motion at the end (if any)
                        if last_mouse_motion:
                            filtered_events.append(last_mouse_motion)

                        events = filtered_events

                        # Handle input events
                        for event in events:
                            # Don't convert coordinates here - let input handlers do it
                            # This allows dialogue (console coords) and gameplay (sprite grid) to use different systems

                            # Save game reference before it potentially becomes None
                            previous_game = game
                            should_continue, game = handle_game_input_events(event, game, input_handler)
                            logging.debug(f"DEBUG: handle_game_input_events returned: should_continue={should_continue}, game={'None' if game is None else 'GameEngine'}")
                            if not should_continue:
                                logging.info("DEBUG: Exiting program (should_continue=False)")
                                return  # Exit program
                            if game is None:
                                logging.info("DEBUG: Returning to main menu (game=None)")
                                # Player returned to menu - save the active game session
                                active_game_session = previous_game

                                # Cleanup SDL renderer state before returning to main menu
                                if context.sdl_renderer:
                                    context.sdl_renderer.draw_color = (0, 0, 0, 255)
                                    context.sdl_renderer.clear()

                                break  # Return to main menu
                        
                    except Exception as e:
                        log_exception(e, "SYSTEM ERROR: Rendering failure", level="error")
                        tb = traceback.extract_tb(e.__traceback__)
                        line_no = tb[-1].lineno if tb else "?"
                        if handle_error_screen(console, context, e, line_no):
                            return
    
    except Exception as e:
        log_exception(e, "CRITICAL SYSTEM ERROR: Game initialization/main loop failure", level="critical")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_exception(e, "CRITICAL UNHANDLED EXCEPTION: Program termination", level="critical")
        raise