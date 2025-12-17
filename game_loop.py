#!/usr/bin/env python3
"""
Rogue Signal Protocol - Game Loop and Initialization

Main game loop, TCOD context initialization, and window management.
Handles menu navigation, game state transitions, and error recovery.
Coordinates rendering, input handling, and audio systems.
"""

# CRITICAL: Set DPI awareness BEFORE importing tcod to ensure proper scaling
from game_platform import set_dpi_awareness

set_dpi_awareness()

import logging  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402

import tcod  # noqa: E402

from game_audio import SoundManager  # noqa: E402
from game_config import GameConfig, GameSettings  # noqa: E402
from game_engine import GameEngine  # noqa: E402
from game_entities import Colors  # noqa: E402
from game_graphics_tiles import TileManager  # noqa: E402
from game_input import InputHandler  # noqa: E402
from game_input_actions import InputAction  # noqa: E402
from game_menu_about import AboutMenu  # noqa: E402
from game_menu_achievements import AchievementsMenu  # noqa: E402
from game_menu_ascension import AscensionMenu  # noqa: E402
from game_menu_controls import (  # noqa: E402
    ControlsMenuHub,
    GamepadBindingsMenu,
    GamepadSettingsMenu,
    KeyboardBindingsMenu,
)
from game_menu_graphics_preview import GraphicsPreviewMenu  # noqa: E402
from game_menu_help_lore import LoreMenu, create_help_menu  # noqa: E402
from game_menus import MainMenu, MenuBackground, SettingsMenu  # noqa: E402
from game_mouse_utils import MenuMouseHandler  # noqa: E402
from game_rendering_core import GameRenderer  # noqa: E402
from game_ui import render_char_safe  # noqa: E402


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


def load_tileset(settings: GameSettings = None):
    """
    Load TrueType font tileset using custom FreeType loader.

    TCOD's native loader has "fit without stretching" behavior that leaves
    tons of empty space. Custom loader gives us full control over scaling.

    Args:
        settings: GameSettings for UI scale preference. If None, uses normal (64px) tiles.
    """
    from font_loader_freetype import load_truetype_font_custom

    # Determine tile size based on UI scale setting
    if settings is not None:
        ui_scale = settings.get_effective_ui_scale()
        tile_size = GameConfig.get_tile_size_for_scale(ui_scale)
    else:
        tile_size = GameConfig.TILE_SIZE_NORMAL()

    tileset = load_truetype_font_custom("KreativeSquare.ttf", tile_size, tile_size)
    logging.debug(
        f"Loaded tileset with {tile_size}x{tile_size} tiles (ui_scale={settings.ui_scale if settings else 'default'})"
    )
    return tileset


def initialize_tcod_context(settings: GameSettings = None):
    """Initialize tcod context with terminal font and SDL validation.

    Args:
        settings: GameSettings for UI scale preference. If None, uses default (64px) tiles.
    """
    tileset = load_tileset(settings)

    context_args = {
        "columns": GameConfig.SCREEN_WIDTH,
        "rows": GameConfig.SCREEN_HEIGHT,
        "width": 1920,  # Explicit window width in pixels (1920×1080 = Full HD)
        "height": 1080,  # Explicit window height in pixels
        "title": "Rogue Signal Protocol",
        "vsync": True,
        "sdl_window_flags": 160,  # Maximized + resizable
    }

    if tileset:
        context_args["tileset"] = tileset

    context = tcod.context.new(**context_args)

    # Store tileset reference on context for later GlyphManager initialization
    context.tileset = tileset

    # Validate SDL renderer availability and set up console rendering
    if hasattr(context, "sdl_renderer") and context.sdl_renderer:
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


def initialize_game_systems(
    settings: GameSettings, context, menu_background=None, sound_manager=None, tile_manager=None
):
    """Initialize menu systems and return menu objects."""
    from game_input_mappings import InputMapper

    # Initialize tile manager if not provided and graphics mode is enabled
    if tile_manager is None and settings.graphics_mode == "graphics":
        try:
            tile_manager = TileManager(context, settings)
        except Exception as e:
            logging.warning(f"Failed to initialize TileManager: {e}")
            tile_manager = None

    # Create input mapper for controls menus (shares bindings with settings)
    input_mapper = InputMapper()
    input_mapper.load_custom_bindings(
        settings.custom_keyboard_bindings, settings.custom_gamepad_bindings
    )

    menus = {
        "main_menu": None,  # Will be set after menus dict is complete
        "settings_menu": SettingsMenu(
            settings, menu_background, sound_manager
        ),  # Pass sound manager for live volume updates
        "help_menu": create_help_menu(settings, context, tile_manager),  # Use factory function
        "_help_menu_mode": settings.graphics_mode,  # Track mode used to create help menu
        "_context": context,  # Store for help menu recreation
        "_tile_manager": tile_manager,  # Store for help menu recreation
        "_input_mapper": input_mapper,  # Store for controls menus
        "_settings": settings,  # Store for ascension menu recreation
        "lore_menu": LoreMenu(),
        "achievements_menu": AchievementsMenu(),
        "about_menu": AboutMenu(menu_background),
        "ascension_menu": AscensionMenu(
            highest_unlocked=settings.get_highest_ascension_unlocked(),
            background=menu_background,
            initial_level=settings.get_ascension_level(),
        ),
        # Controls menus (Phase 4)
        "controls_hub": ControlsMenuHub(settings, input_mapper, menu_background),
        "keyboard_bindings": KeyboardBindingsMenu(settings, input_mapper, menu_background),
        "gamepad_settings": GamepadSettingsMenu(settings, input_mapper, menu_background),
        "gamepad_bindings": GamepadBindingsMenu(settings, input_mapper, menu_background),
    }

    # Only add graphics preview menu if we have a tile manager
    if tile_manager is not None:
        menus["graphics_preview_menu"] = GraphicsPreviewMenu(context, settings, tile_manager)

    # Now create main menu with reference to menus dict (so it can check if graphics_preview_menu exists)
    menus["main_menu"] = MainMenu(background=menu_background, menus=menus)

    return menus


def _run_graphics_preview_loop(graphics_preview_menu, console, context, settings):
    """
    Run the graphics preview sub-loop.

    Returns True if preview was exited normally, False if quit was requested.
    """
    # Flush any pending events to avoid immediate exit
    tcod.event.get()

    exit_preview = False
    while not exit_preview:
        # Render the preview menu to console
        graphics_preview_menu.render(console)

        # Check if we should render graphics
        graphics_available = (
            context.sdl_renderer
            and hasattr(context, "console_render")
            and context.console_render
            and settings.graphics_mode == "graphics"
        )

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

        # Process events with timeout to allow stick polling
        for preview_event in tcod.event.wait(timeout=0.1):
            # Convert pixel coordinates to tile coordinates for mouse events
            if isinstance(preview_event, (tcod.event.MouseMotion, tcod.event.MouseButtonDown)):
                converted_event = MenuMouseHandler.convert_to_tile_coords(preview_event, context)
                if converted_event is not None:
                    preview_event = converted_event

            if isinstance(preview_event, tcod.event.Quit):
                # Export selections and return to main menu on quit
                graphics_preview_menu.export_selections()
                exit_preview = True
                break
            elif isinstance(preview_event, tcod.event.KeyDown):
                preview_action = graphics_preview_menu.handle_input(preview_event)
                if preview_action == "exit":
                    graphics_preview_menu.export_selections()
                    exit_preview = True
                    break
            elif isinstance(preview_event, tcod.event.ControllerButton) and preview_event.pressed:
                preview_action = graphics_preview_menu.handle_input(preview_event)
                if preview_action == "exit":
                    graphics_preview_menu.export_selections()
                    exit_preview = True
                    break
            elif (
                isinstance(preview_event, tcod.event.ControllerButton) and not preview_event.pressed
            ):
                # Handle gamepad button release events (needed for auto-repeat state)
                graphics_preview_menu.handle_input(preview_event)
            elif isinstance(preview_event, tcod.event.ControllerAxis):
                preview_action = graphics_preview_menu.handle_input(preview_event)
                if preview_action == "exit":
                    graphics_preview_menu.export_selections()
                    exit_preview = True
                    break
            elif isinstance(preview_event, tcod.event.MouseMotion):
                graphics_preview_menu.handle_mouse_motion(preview_event)
            elif isinstance(preview_event, tcod.event.MouseButtonDown):
                preview_action = graphics_preview_menu.handle_mouse_click(preview_event)
                if preview_action == "exit":
                    graphics_preview_menu.export_selections()
                    exit_preview = True
                    break

        # Small delay to prevent CPU spinning (60 FPS)
        time.sleep(1 / 60)

    # Cleanup SDL renderer state before returning to main menu
    if graphics_available and context.sdl_renderer:
        context.sdl_renderer.draw_color = (0, 0, 0, 255)
        context.sdl_renderer.clear()


def _process_menu_action(
    action,
    menus,
    menu_stack,
    current_menu,
    main_menu,
    settings,
    context,
    console,
    active_game,
    menu_sound_manager,
):
    """
    Process a menu action and return updated state.

    Returns:
        tuple: (new_current_menu, return_value) where return_value is:
               - None: continue menu loop
               - (game, should_exit): exit menu loop with these values
    """
    if action == "exit":
        # Save active game before exiting if one exists and player is alive
        if active_game is not None and active_game.player.cpu > 0 and not active_game.game_over:
            active_game.auto_save()
        menu_sound_manager.cleanup()
        return current_menu, (None, True)  # game=None, should_exit=True

    elif action == "export_debug_confirmed":
        # Export debug package from settings menu (user confirmed)
        from debug_export import export_debug_package

        logging.info("Debug Export: Starting debug package creation from settings menu")
        zip_path = export_debug_package(game_engine=active_game)
        if zip_path:
            logging.info(f"Debug Export: Success from settings menu - {zip_path}")
            menus["settings_menu"].export_status_message = f"Success! Saved to: {zip_path.parent}"
        else:
            logging.error("Debug Export: Failed to create package from settings menu")
            menus["settings_menu"].export_status_message = "Failed to create debug package"
        return current_menu, None

    elif action == "settings":
        menus["settings_menu"].export_status_message = None
        menus["settings_menu"].selected_option = 0  # Reset to top when entering
        menu_stack.append(current_menu)
        return menus["settings_menu"], None

    elif action == "help":
        # Only recreate help menu if graphics mode changed (preserves page state)
        if menus.get("_help_menu_mode") != settings.graphics_mode:
            logging.info(
                f"Graphics mode changed, recreating help menu: {menus.get('_help_menu_mode')} -> {settings.graphics_mode}"
            )
            # Create TileManager if switching to graphics mode and it doesn't exist
            if settings.graphics_mode == "graphics" and menus.get("_tile_manager") is None:
                try:
                    menus["_tile_manager"] = TileManager(menus["_context"], settings)
                    logging.info("Created TileManager for graphics mode help menu")
                except Exception as e:
                    logging.error(f"Failed to create TileManager: {e}")
                    settings.graphics_mode = "glyph"

            menus["help_menu"] = create_help_menu(
                settings, menus["_context"], menus["_tile_manager"]
            )
            menus["_help_menu_mode"] = settings.graphics_mode
        menu_stack.append(current_menu)
        return menus["help_menu"], None

    elif action == "lore":
        menu_stack.append(current_menu)
        return menus["lore_menu"], None

    elif action == "about":
        menu_stack.append(current_menu)
        return menus["about_menu"], None

    elif action == "achievements":
        menu_stack.append(current_menu)
        return menus["achievements_menu"], None

    elif action == "ascension":
        # Refresh ascension menu with latest unlock state
        menus["ascension_menu"] = AscensionMenu(
            highest_unlocked=settings.get_highest_ascension_unlocked(),
            background=menus["ascension_menu"].background,
            initial_level=settings.get_ascension_level(),
        )
        menu_stack.append(current_menu)
        return menus["ascension_menu"], None

    elif action == "controls":
        menu_stack.append(current_menu)
        return menus["controls_hub"], None

    elif action == "keyboard_bindings":
        menu_stack.append(current_menu)
        return menus["keyboard_bindings"], None

    elif action == "gamepad_bindings":
        menu_stack.append(current_menu)
        return menus["gamepad_bindings"], None

    elif action == "gamepad_settings":
        menu_stack.append(current_menu)
        return menus["gamepad_settings"], None

    elif action == "graphics_preview":
        if "graphics_preview_menu" in menus:
            _run_graphics_preview_loop(menus["graphics_preview_menu"], console, context, settings)
            return main_menu, None
        else:
            logging.warning("Graphics Preview not available")
        return current_menu, None

    elif action == "back":
        menus["settings_menu"].export_status_message = None
        if menu_stack:
            new_menu = menu_stack.pop()
        else:
            main_menu.refresh_options(show_continue=True, active_game=active_game)
            main_menu.restore_selection_after_submenu()
            new_menu = main_menu
        if new_menu is main_menu:
            main_menu.refresh_options(show_continue=True, active_game=active_game)
            main_menu.restore_selection_after_submenu()
        return new_menu, None

    elif action == "continue":
        if menu_sound_manager.current_music is not None:
            menu_sound_manager.stop_music(fade_out_ms=1000)

        if active_game is not None:
            return current_menu, (active_game, False)
        else:
            try:
                game = GameEngine(settings=settings, load_save=True)
                return current_menu, (game, False)
            except Exception as e:
                from game_save import SaveLoadError

                if isinstance(e, SaveLoadError):
                    logging.error(f"Save load failed: {e}")
                    logging.info("Returning to main menu...")
                else:
                    raise
        return current_menu, None

    elif action == "new_game":
        menu_sound_manager.stop_music(fade_out_ms=1000)
        from game_achievements import AchievementManager

        AchievementManager.clear_pending_popups()
        # Get ascension level from settings for new game
        ascension_level = settings.get_ascension_level() if settings else 0
        game = GameEngine(settings=settings, ascension_level=ascension_level)
        return current_menu, (game, False)

    return current_menu, None


def handle_menu_navigation(
    console,
    context,
    menus,
    settings,
    menu_sound_manager=None,
    active_game=None,
    shared_controllers=None,
):
    """
    Handle the main menu navigation loop.

    Args:
        active_game: If provided, this is a game in progress that should be resumed on "continue"
        shared_controllers: Set of GameController objects to track across menu/game boundary
    """
    main_menu = menus["main_menu"]
    main_menu.refresh_options(show_continue=True, active_game=active_game)
    current_menu = main_menu

    # Menu navigation stack - enables proper "back" to parent menu
    # When entering a submenu, push current menu to stack
    # When "back" is pressed, pop from stack (or go to main_menu if empty)
    menu_stack = []

    # Create sound manager if not provided
    if menu_sound_manager is None:
        # Detect headless/test mode: if SDL video isn't initialized, use NullSoundManager
        try:
            import pygame

            if pygame.display.get_surface() is None:
                # Headless mode (no display) - use null audio
                from game_audio import NullSoundManager

                menu_sound_manager = NullSoundManager(settings)
            else:
                menu_sound_manager = SoundManager(settings)
        except Exception:
            # Pygame not initialized or error - use null audio
            from game_audio import NullSoundManager

            menu_sound_manager = NullSoundManager(settings)

    # DO NOT start menu music if level music is already playing
    # Level music should continue playing when player returns to menu
    try:
        import pygame

        from game_audio import AUDIO_AVAILABLE

        # Only play menu music if NO music is currently playing
        if AUDIO_AVAILABLE and not pygame.mixer.music.get_busy():
            menu_sound_manager.play_music("main_menu.ogg", loops=-1, fade_in_ms=1000)
    except Exception as e:
        logging.warning(f"Could not play main menu music: {e}")
        # Continue without music

    # Note: Menus now own their input handling (PLAN architecture)
    # Each menu creates its own InputMapper and GamepadInputHandler in __init__

    while True:
        # Render console content first
        current_menu.render(console)

        # Check for background graphics (main menu, settings menu, etc.)
        has_background = (
            hasattr(current_menu, "background")
            and current_menu.background
            and current_menu.background.should_load_background()
        )

        # Check for sprite rendering (graphical help menu)
        has_sprites = hasattr(current_menu, "render_sprites")

        # CORRECTED RENDERING: Use SDL renderer when available for graphics mode
        graphics_available = (
            context.sdl_renderer
            and hasattr(context, "console_render")
            and context.console_render
            and (has_background or has_sprites)
        )

        if graphics_available:
            # Graphics mode: render everything through SDL
            # CRITICAL: Set draw color to BLACK before clear() to avoid white background
            context.sdl_renderer.draw_color = (0, 0, 0, 255)
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

        # Wait for events with timeout to allow stick polling
        for event in tcod.event.wait(timeout=0.1):
            # Initialize action for this event iteration to avoid UnboundLocalError
            action = ""

            # Convert pixel coordinates to tile coordinates for menu mouse events
            if isinstance(event, (tcod.event.MouseMotion, tcod.event.MouseButtonDown)):
                converted_event = MenuMouseHandler.convert_to_tile_coords(event, context)
                if converted_event is not None:
                    event = converted_event

            if isinstance(event, tcod.event.Quit):
                menu_sound_manager.cleanup()
                return None, True  # game=None, should_exit=True
            elif isinstance(event, tcod.event.MouseMotion):
                # Handle mouse hover on menu options
                current_menu.handle_mouse_motion(event)
            elif isinstance(event, tcod.event.MouseButtonDown):
                # Handle mouse clicks on menu options
                action = current_menu.handle_mouse_click(event)
                if action and action != "":
                    current_menu, result = _process_menu_action(
                        action,
                        menus,
                        menu_stack,
                        current_menu,
                        main_menu,
                        settings,
                        context,
                        console,
                        active_game,
                        menu_sound_manager,
                    )
                    if result is not None:
                        return result

            elif isinstance(event, tcod.event.MouseWheel):
                # Handle mouse wheel events in menus (e.g., scrolling help pages)
                if hasattr(current_menu, "handle_mouse_wheel"):
                    current_menu.handle_mouse_wheel(event)

            elif isinstance(event, tcod.event.ControllerDevice):
                # Handle controller connection/disconnection events
                logging.info(f"Menu: Controller event {event.type}")

                # Track controllers so game can pick them up (critical for hotplug during menu)
                if shared_controllers is not None and event.type == "CONTROLLERDEVICEADDED":
                    if hasattr(event, "controller") and event.controller:
                        shared_controllers.add(event.controller)
                        try:
                            name = event.controller.name
                        except AttributeError:
                            name = "Unknown"
                        logging.info(f"Menu: Added controller to shared set: {name}")
                    else:
                        # Fallback: try enumeration
                        for controller in tcod.sdl.joystick.get_controllers():
                            if controller not in shared_controllers:
                                shared_controllers.add(controller)
                                try:
                                    name = controller.name
                                except AttributeError:
                                    name = "Unknown"
                                logging.info(f"Menu: Added controller (enum): {name}")
                                break

            elif isinstance(
                event, (tcod.event.ControllerButton, tcod.event.ControllerAxis, tcod.event.KeyDown)
            ):
                # PLAN architecture: Menu owns ALL input handling
                # Menu.handle_input() uses InputMapper for both keyboard and gamepad
                # NOTE: ONLY accept CONTROLLER* events (GameController API - recommended)
                # SDL sends BOTH Controller* and Joy* events - we filter out Joy* to avoid duplicates
                # IMPORTANT: This handles both CONTROLLERBUTTONDOWN and CONTROLLERBUTTONUP events
                # Button-up (CONTROLLERBUTTONUP) clears held button state for auto-repeat
                event_type_name = type(event).__name__
                logging.debug(
                    f"Menu Loop: Routing {event_type_name} to current_menu.handle_input()"
                )
                action = current_menu.handle_input(event)
                logging.debug(f"Menu Loop: handle_input returned action={repr(action)}")
            else:
                # DEBUG: Log unhandled event types
                if event.type not in ("MOUSEMOTION",):  # Skip mouse motion spam
                    logging.debug(f"Menu Loop: Unhandled event.type={event.type}")
                # action already initialized to "" at start of loop iteration

            # Process menu action (shared for both keyboard and gamepad)
            if action and action != "":
                current_menu, result = _process_menu_action(
                    action,
                    menus,
                    menu_stack,
                    current_menu,
                    main_menu,
                    settings,
                    context,
                    console,
                    active_game,
                    menu_sound_manager,
                )
                if result is not None:
                    return result

        # REMOVED: Old polling-based navigation system (caused double-navigation bug)
        # NOW: Button repeat checking for D-pad auto-repeat
        # Check if any held navigation button should repeat
        if hasattr(current_menu, "gamepad_handler") and current_menu.gamepad_handler:
            from game_input_actions import InputContext

            # Determine input context based on current menu type
            input_context = InputContext.MAIN_MENU  # Default
            if hasattr(current_menu, "__class__"):
                menu_name = current_menu.__class__.__name__
                if "Settings" in menu_name:
                    input_context = InputContext.SETTINGS_MENU
                elif "Help" in menu_name:
                    input_context = InputContext.HELP
                elif "About" in menu_name:
                    input_context = InputContext.ABOUT_MENU
                elif "Achievement" in menu_name:
                    input_context = InputContext.ACHIEVEMENTS_SCREEN
                elif "Lore" in menu_name or "Fragment" in menu_name:
                    input_context = InputContext.LORE_VIEWER

            # Check for button repeat
            repeat_action = current_menu.gamepad_handler.get_button_repeat_action(input_context)
            if repeat_action:
                # Execute the repeat action
                result = current_menu.execute_action(repeat_action)
                if result and result != "":
                    action = result

            # Analog stick auto-repeat for menu navigation
            # Poll analog stick for held movement (time-based auto-repeat)
            # When swap_sticks=True: use RIGHT stick for menu navigation
            # When swap_sticks=False: use LEFT stick for menu navigation
            swap_sticks = getattr(settings, "gamepad_swap_sticks", False)
            analog = current_menu.gamepad_handler.analog_handler
            if analog:
                if swap_sticks:
                    movement = analog.get_right_stick_movement_menu()
                else:
                    movement = analog.get_left_stick_movement_menu()
                if movement:
                    dx, dy = movement
                    # Convert movement to navigation action (prioritize vertical, then horizontal)
                    stick_action = None
                    if dy < 0:
                        stick_action = InputAction.NAVIGATE_UP
                    elif dy > 0:
                        stick_action = InputAction.NAVIGATE_DOWN
                    elif dx < 0:
                        stick_action = InputAction.NAVIGATE_LEFT
                    elif dx > 0:
                        stick_action = InputAction.NAVIGATE_RIGHT

                    if stick_action:
                        result = current_menu.execute_action(stick_action)
                        if result and result != "":
                            action = result


def handle_game_input_events(event, game, input_handler):
    """Handle game input events and return (should_continue, game)."""
    try:
        return _handle_game_input_events_impl(event, game, input_handler)
    except Exception as e:
        import logging

        logging.error(
            f"INPUT ERROR: Exception in event handler for {event.type}: {e}", exc_info=True
        )
        # Return True to continue playing instead of crashing
        return True, game


def _handle_game_input_events_impl(event, game, input_handler):
    """Internal implementation of game input handling."""
    if isinstance(event, tcod.event.Quit):
        game.auto_save()
        game.sound_manager.cleanup()
        return False, None  # Exit program
    elif isinstance(event, tcod.event.MouseMotion):
        # Handle mouse motion events (cursor updates, hover effects)
        input_handler.handle_mouse_motion(event)
    elif isinstance(event, tcod.event.MouseButtonDown):
        # Handle mouse click events
        should_continue = input_handler.handle_mouse_click(event)
        if should_continue is not None and not should_continue:
            # Death/victory dialogue was dismissed with click - return to main menu
            from game_achievements import AchievementManager

            AchievementManager.clear_pending_popups()
            return True, None
    elif isinstance(event, tcod.event.MouseWheel):
        # Handle mouse wheel events (scrolling)
        input_handler.handle_mouse_wheel(event)
    elif isinstance(event, tcod.event.ControllerDevice):
        # Handle controller connection/disconnection events
        input_handler.handle_controller_device(event)
    elif isinstance(event, tcod.event.ControllerButton):
        # Handle controller button press/release events (GameController API only)
        # SDL sends BOTH Controller* and Joy* - we only handle Controller* to avoid duplicates
        should_continue = input_handler.handle_controller_button(event)
        if should_continue is not None and not should_continue:
            # Death/victory dialogue was dismissed with controller - return to main menu
            from game_achievements import AchievementManager

            AchievementManager.clear_pending_popups()
            return True, None
    elif isinstance(event, tcod.event.ControllerAxis):
        # Handle controller analog stick/trigger axis events (GameController API only)
        should_continue = input_handler.handle_controller_axis(event)
        if should_continue is not None and not should_continue:
            # Death/victory dialogue was dismissed with controller - return to main menu
            from game_achievements import AchievementManager

            AchievementManager.clear_pending_popups()
            return True, None
    elif isinstance(event, tcod.event.KeyDown):
        if event.sym == tcod.event.KeySym.ESCAPE:
            # Priority 1: If dialogue is active, let it handle escape first
            if game.dialogue_state.is_active():
                should_continue = input_handler._handle_dialogue_dismiss()
                if not should_continue:
                    # Death/victory dialogue wants to exit to menu
                    from game_achievements import AchievementManager

                    AchievementManager.clear_pending_popups()
                    return True, None
                return True, game
            # Check if any UI states are open - close those first
            elif (
                game.show_lore_viewer
                or game.show_help
                or game.show_achievements
                or game.show_ascension
                or game.show_inventory
                or game.look_mode
                or game.targeting_mode
            ):
                input_handler._handle_escape()
            else:
                # Don't allow ESC to menu if player is dead or dying
                if (
                    game.player.cpu <= 0
                    or game.game_over
                    or (hasattr(game, "pending_death_dialogue") and game.pending_death_dialogue)
                ):
                    # Player is dead - force them to see death dialogue, can't ESC to menu
                    return True, game
                # No UI states open, auto-save and go to main menu
                game.auto_save()
                # Don't stop level music - let it continue playing in the menu
                from game_achievements import AchievementManager

                AchievementManager.clear_pending_popups()
                return True, None  # Return to main menu
        else:
            should_continue = input_handler.handle_keydown(event)
            if not should_continue:
                # Player is dead and pressed ESC - return to main menu
                from game_achievements import AchievementManager

                AchievementManager.clear_pending_popups()
                return True, None
    return True, game


def handle_error_screen(console, context, error_message, line_no):
    """Display error screen and wait for user input."""
    console.clear()
    render_char_safe(
        console, 1, 1, f"Error: {str(error_message)[:50]} (line {line_no})", fg=Colors.RED
    )
    render_char_safe(console, 1, 2, "Press ESC to exit", fg=Colors.WHITE)
    context.present(console)

    for event in tcod.event.wait():
        if isinstance(event, tcod.event.Quit) or (
            isinstance(event, tcod.event.KeyDown) and event.sym == tcod.event.KeySym.ESCAPE
        ):
            return True
    return False


def main():
    """Main game loop with main menu and save/load functionality."""
    # CRITICAL: Set SDL hints BEFORE any SDL initialization (before creating TCOD context)
    # Force SDL3 to use XInput on Windows for gamepad support
    import os

    os.environ["SDL_JOYSTICK_HIDAPI"] = "0"  # Disable HIDAPI
    os.environ["SDL_JOYSTICK_RAWINPUT"] = "0"  # Disable Raw Input
    os.environ["SDL_XINPUT_ENABLED"] = "1"  # Enable XInput (Windows native)
    logging.debug("SDL hints set for gamepad (HIDAPI=0, RAWINPUT=0, XINPUT=1)")

    # Initialize JSON configuration system
    GameConfig.load_from_json()

    # Initialize achievement system with unlocked achievements from progress file
    from game_achievements import AchievementManager
    from game_metrics import load_unlocked_achievements

    unlocked_achievements = load_unlocked_achievements()
    AchievementManager.load_unlocked_achievements(unlocked_achievements)
    logging.info(f"Loaded {len(unlocked_achievements)} unlocked achievements")

    # Create settings BEFORE context so we can use UI scale for tileset loading
    settings = GameSettings()

    # Log platform detection results
    from game_platform import get_platform_name

    platform_name = get_platform_name()
    ui_scale = settings.get_effective_ui_scale()
    logging.info(f"Platform: {platform_name}, UI scale: {settings.ui_scale} -> {ui_scale}")

    try:
        with initialize_tcod_context(settings) as context:
            console = tcod.console.Console(GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)

            # Initialize SDL joystick subsystem for controller support
            # This MUST be called after SDL is initialized (after context creation)
            tcod.sdl.joystick.init()
            logging.debug("SDL joystick subsystem initialized")

            # WINDOWS TIMING FIX: Give SDL a moment to enumerate XInput devices
            # On some systems, XInput detection isn't instant after init()
            import time

            time.sleep(0.1)  # 100ms delay for XInput enumeration

            # Get already-connected controllers (CONTROLLERDEVICEADDED only fires for hot-plugging)
            initial_controllers = set(tcod.sdl.joystick.get_controllers())
            if initial_controllers:
                logging.info(f"[STARTUP] Found {len(initial_controllers)} controller(s) at startup")
                for controller in initial_controllers:
                    try:
                        name = controller.name
                    except AttributeError:
                        name = "Unknown"
                    logging.info(f"[STARTUP]   - {name}")
            else:
                logging.debug("[STARTUP] No controllers connected at startup")
                logging.debug(
                    "[STARTUP] Controllers may connect during runtime (hotplug supported)"
                )

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
                    # Also pass initial_controllers so menu can track hotplugged controllers
                    game, should_exit = handle_menu_navigation(
                        console,
                        context,
                        menus,
                        settings,
                        menu_sound_manager,
                        active_game_session,
                        initial_controllers,
                    )

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

                    # Use initial_controllers (now updated by menu if controllers connected during menu)
                    if initial_controllers:
                        logging.info(
                            f"[GAME START] Initializing with {len(initial_controllers)} controller(s)"
                        )

                    input_handler = InputHandler(
                        game, renderer=renderer, controllers=initial_controllers
                    )
                    # CRITICAL: Assign input_handler to game so fragment pickup can check renderer
                    game.input_handler = input_handler

                # Main game loop
                last_render_time = time.time()
                render_interval = 1.0 / 30.0  # 30 FPS for smooth pulsing animation

                # Victory screen handling
                victory_screen = None
                victory_background = None

                # Gamepad health monitoring (diagnose intermittent failures)
                last_controller_event_time = time.time()
                last_controller_health_check = time.time()
                controller_health_check_interval = 30.0  # Check every 30 seconds
                controller_event_timeout = 60.0  # Warn if no events for 60 seconds

                while game is not None:
                    # Check if victory screen should be shown
                    if game.game_state.show_victory_screen and victory_screen is None:
                        # Create victory background with ending art
                        victory_background = MenuBackground(
                            context, settings, art_directory="graphics/ending"
                        )
                        victory_background.load_random_background()

                        # Import and create victory screen
                        from game_victory_screen import VictoryScreen

                        victory_screen = VictoryScreen(background=victory_background)

                        logging.info("Victory screen initialized")

                    # If victory screen is active, render it instead of the game
                    if victory_screen is not None:
                        try:
                            # Render victory screen content to console
                            victory_screen.render(console)

                            # Use SDL rendering pipeline (SAME as main menu!)
                            has_background = (
                                victory_background and victory_background.should_load_background()
                            )

                            graphics_available = (
                                context.sdl_renderer
                                and hasattr(context, "console_render")
                                and context.console_render
                                and has_background
                            )

                            if graphics_available:
                                # Graphics mode: render everything through SDL (same as main menu)
                                # CRITICAL: Set draw color to BLACK before clear() to avoid white background
                                context.sdl_renderer.draw_color = (0, 0, 0, 255)
                                context.sdl_renderer.clear()

                                # Render background graphics to SDL
                                victory_background.render_background(console)

                                # Render console to texture
                                console_texture = context.console_render.render(console)

                                # Copy console texture to fill window
                                window_w, window_h = context.sdl_window.size
                                dest_rect = (0, 0, window_w, window_h)
                                context.sdl_renderer.copy(console_texture, dest=dest_rect)

                                # Present everything through SDL
                                context.sdl_renderer.present()
                            else:
                                # Fallback: normal console presentation
                                context.present(console)

                            # Handle victory screen input
                            for event in tcod.event.wait():
                                if isinstance(event, tcod.event.Quit):
                                    return  # Exit program
                                elif victory_screen.handle_input(event):
                                    # Victory screen dismissed - check for unlock screen
                                    logging.info("Victory screen dismissed")

                                    # Check if a new ascension was unlocked
                                    newly_unlocked = game.game_state.newly_unlocked_ascension
                                    if newly_unlocked is not None:
                                        logging.info(
                                            f"Showing ascension unlock screen for A{newly_unlocked}"
                                        )
                                        # Show unlock screen before returning to menu
                                        from game_menu_ascension import AscensionUnlockScreen

                                        unlock_screen = AscensionUnlockScreen(
                                            unlocked_level=newly_unlocked,
                                            background=victory_background,
                                        )

                                        # Unlock screen loop - errors should propagate, not be silently swallowed
                                        unlock_done = False
                                        while not unlock_done:
                                            # Render background first (if available)
                                            if victory_background:
                                                victory_background.render_background(console)
                                            unlock_screen.render(console)
                                            if (
                                                context.sdl_renderer
                                                and hasattr(context, "console_render")
                                                and context.console_render
                                            ):
                                                context.sdl_renderer.draw_color = (0, 0, 0, 255)
                                                context.sdl_renderer.clear()
                                                context.console_render.render(console)
                                                context.sdl_renderer.present()
                                            else:
                                                context.present(console)

                                            for unlock_event in tcod.event.wait():
                                                if isinstance(unlock_event, tcod.event.Quit):
                                                    return  # Exit program
                                                elif unlock_screen.handle_input(unlock_event):
                                                    unlock_done = True
                                                    break

                                        # Clear the flag
                                        game.game_state.newly_unlocked_ascension = None

                                    logging.info("Returning to main menu")
                                    from game_achievements import AchievementManager

                                    AchievementManager.clear_pending_popups()
                                    victory_background.cleanup()
                                    game = None
                                    break
                        except Exception as e:
                            log_exception(e, "Victory screen rendering/input")
                            # Show error to user instead of silently returning
                            tb = traceback.extract_tb(e.__traceback__)
                            line_no = tb[-1].lineno if tb else "?"
                            if handle_error_screen(console, context, e, line_no):
                                return  # User pressed ESC to exit
                            # Clean up and return to menu
                            from game_achievements import AchievementManager

                            AchievementManager.clear_pending_popups()
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
                                if (
                                    hasattr(game, "particle_system")
                                    and game.particle_system is not None
                                ):
                                    game.particle_system.update(delta_time)

                                renderer.render_game(console, game, context)
                                last_render_time = current_time

                            # Get all available events (non-blocking)
                            events = tcod.event.get()

                            # NOTE: Don't skip polling when no events - analog stick auto-repeat
                            # requires continuous polling even when no new events arrive!
                            # The event loop will just process zero events, then poll sticks.
                        else:
                            # Glyph mode: event-driven rendering
                            renderer.render_game(console, game, context)
                            context.present(console)

                            # Wait for events with 100ms timeout (allows analog stick repeat polling)
                            events = list(tcod.event.wait(timeout=0.1))

                        # PERFORMANCE FIX: Filter out redundant mouse motion events
                        # Only keep the LAST mouse motion event to avoid processing hundreds per frame
                        filtered_events = []
                        last_mouse_motion = None

                        for event in events:
                            if isinstance(event, tcod.event.MouseMotion):
                                # Keep only the most recent mouse motion
                                last_mouse_motion = event
                            else:
                                # Keep all non-motion events
                                filtered_events.append(event)

                        # Add the last mouse motion at the end (if any)
                        if last_mouse_motion:
                            filtered_events.append(last_mouse_motion)

                        events = filtered_events

                        # GAMEPAD HEALTH MONITORING: Track controller events and warn on timeout
                        current_time_for_health = time.time()
                        for event in events:
                            if isinstance(
                                event, (tcod.event.ControllerButton, tcod.event.ControllerAxis)
                            ):
                                last_controller_event_time = current_time_for_health
                                break

                        # Periodic health check
                        if (
                            current_time_for_health - last_controller_health_check
                            >= controller_health_check_interval
                        ):
                            last_controller_health_check = current_time_for_health
                            controller_count = (
                                len(input_handler.gamepad_handler.controllers)
                                if hasattr(input_handler, "gamepad_handler")
                                else 0
                            )
                            time_since_last_event = (
                                current_time_for_health - last_controller_event_time
                            )

                            # Log controller health status ONLY when there's a problem
                            if controller_count == 0:
                                logging.warning(
                                    "[GAMEPAD HEALTH] No controllers in handler! Events may not be received."
                                )
                            elif time_since_last_event > controller_event_timeout:
                                logging.warning(
                                    f"[GAMEPAD HEALTH] No controller events for {time_since_last_event:.0f}s. Controllers: {controller_count}. Possible disconnect?"
                                )

                        # Handle input events
                        for event in events:
                            # Don't convert coordinates here - let input handlers do it
                            # This allows dialogue (console coords) and gameplay (sprite grid) to use different systems

                            # Save game reference before it potentially becomes None
                            previous_game = game
                            should_continue, game = handle_game_input_events(
                                event, game, input_handler
                            )
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

                        # ANALOG STICK REPEAT FIX: Poll analog sticks for repeat movement/navigation
                        # even when no new axis events arrived (stick held in one direction)
                        if game is not None and hasattr(input_handler, "gamepad_handler"):
                            action = None
                            analog = input_handler.gamepad_handler.analog_handler

                            # Check swap_sticks setting (accessibility feature)
                            swap_sticks = getattr(game.settings, "gamepad_swap_sticks", False)

                            # Gameplay movement (not in inventory/look/targeting/achievements/help)
                            # When swap_sticks=True: use RIGHT stick for movement
                            # When swap_sticks=False: use LEFT stick for movement
                            if (
                                not game.show_inventory
                                and not game.look_mode
                                and not game.targeting_mode
                                and not game.show_achievements
                                and not game.show_ascension
                                and not game.show_help
                            ):
                                if swap_sticks:
                                    movement = analog.get_right_stick_movement_gameplay(game.turn)
                                else:
                                    movement = analog.get_left_stick_movement_gameplay(game.turn)
                                if movement:
                                    dx, dy = movement
                                    action = (
                                        input_handler.gamepad_handler._delta_to_movement_action(
                                            dx, dy
                                        )
                                    )

                            # Achievements/help scrolling
                            # NOTE: Inventory is handled by event system (InventoryInputHandler) to prevent double-triggering
                            # When swap_sticks=True: use RIGHT stick for menu navigation
                            # When swap_sticks=False: use LEFT stick for menu navigation
                            elif game.show_achievements or game.show_ascension or game.show_help:
                                # For all modals: Use analog handler (same data source)
                                if swap_sticks:
                                    movement = analog.get_right_stick_movement_menu()
                                else:
                                    movement = analog.get_left_stick_movement_menu()

                                if movement:
                                    dx, dy = movement

                                    if game.show_achievements:
                                        # Achievements: Vertical scrolling (up/down)
                                        if dy != 0:
                                            # Get achievements menu from renderer (same as game_input.py)
                                            achievements_menu = None
                                            if input_handler.renderer and hasattr(
                                                input_handler.renderer, "ui_renderer"
                                            ):
                                                ui_renderer = input_handler.renderer.ui_renderer
                                                if hasattr(ui_renderer, "_achievements_menu"):
                                                    achievements_menu = (
                                                        ui_renderer._achievements_menu
                                                    )
                                            if achievements_menu:
                                                if dy < 0:  # Up
                                                    achievements_menu.scroll_offset = max(
                                                        0, achievements_menu.scroll_offset - 1
                                                    )
                                                else:  # Down
                                                    all_lines = (
                                                        achievements_menu._build_achievement_lines()
                                                    )
                                                    max_scroll = max(
                                                        0,
                                                        len(all_lines)
                                                        - achievements_menu.max_visible_lines,
                                                    )
                                                    achievements_menu.scroll_offset = min(
                                                        max_scroll,
                                                        achievements_menu.scroll_offset + 1,
                                                    )
                                    elif game.show_help:
                                        # Help menu: Horizontal navigation (left/right for pages)
                                        if dx != 0:
                                            if input_handler.renderer and hasattr(
                                                input_handler.renderer, "_get_or_create_help_menu"
                                            ):
                                                help_menu = (
                                                    input_handler.renderer._get_or_create_help_menu()
                                                )
                                                if help_menu:
                                                    if dx < 0:  # Left = previous page
                                                        if hasattr(help_menu, "_previous_page"):
                                                            help_menu._previous_page()
                                                    else:  # Right = next page
                                                        if hasattr(help_menu, "_next_page"):
                                                            help_menu._next_page()

                            # Look mode or targeting cursor movement
                            # When swap_sticks=True: use LEFT stick for cursor
                            # When swap_sticks=False: use RIGHT stick for cursor
                            elif game.look_mode or game.targeting_mode:
                                if swap_sticks:
                                    movement = analog.get_left_stick_movement()
                                else:
                                    movement = analog.get_right_stick_movement()
                                if movement:
                                    dx, dy = movement
                                    action = (
                                        input_handler.gamepad_handler._delta_to_movement_action(
                                            dx, dy
                                        )
                                    )

                            # Execute action if found
                            if action:
                                should_continue = input_handler._execute_action(action)
                                if should_continue is not None and not should_continue:
                                    # Death/victory dialogue was dismissed - return to main menu
                                    from game_achievements import AchievementManager

                                    AchievementManager.clear_pending_popups()
                                    active_game_session = game
                                    game = None
                                    if context.sdl_renderer:
                                        context.sdl_renderer.draw_color = (0, 0, 0, 255)
                                        context.sdl_renderer.clear()
                                    break

                    except Exception as e:
                        log_exception(e, "SYSTEM ERROR: Rendering failure", level="error")
                        tb = traceback.extract_tb(e.__traceback__)
                        line_no = tb[-1].lineno if tb else "?"
                        if handle_error_screen(console, context, e, line_no):
                            return

    except Exception as e:
        log_exception(
            e, "CRITICAL SYSTEM ERROR: Game initialization/main loop failure", level="critical"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_exception(e, "CRITICAL UNHANDLED EXCEPTION: Program termination", level="critical")
        raise
