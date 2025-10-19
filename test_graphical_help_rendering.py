#!/usr/bin/env python3
"""
Quick test script to verify graphical help rendering with detailed logging.
Run this to see debug output about sprite rendering.
"""

import logging
import sys

# Set up detailed logging BEFORE importing game modules
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    stream=sys.stdout
)

# Now import game modules
import tcod
from game_config import GameSettings
from game_loop import initialize_tcod_context, initialize_game_systems
from game_graphics_tiles import TileManager

def main():
    print("=" * 80)
    print("GRAPHICAL HELP RENDERING TEST")
    print("=" * 80)

    # Initialize TCOD context
    print("\n1. Initializing TCOD context...")
    context = initialize_tcod_context()
    console = tcod.console.Console(80, 50)

    # Set graphics mode
    print("\n2. Setting graphics mode...")
    settings = GameSettings()
    settings.graphics_mode = "graphics"
    settings.save_settings()

    # Initialize tile manager
    print("\n3. Initializing TileManager...")
    tile_manager = TileManager(context, settings)

    # Initialize game systems (including help menu)
    print("\n4. Initializing game systems...")
    menus = initialize_game_systems(settings, context, tile_manager=tile_manager)

    help_menu = menus['help_menu']
    print(f"\n5. Help menu type: {type(help_menu).__name__}")
    print(f"   Has render_sprites: {hasattr(help_menu, 'render_sprites')}")

    if hasattr(help_menu, 'render_sprites'):
        print("\n6. Testing sprite rendering...")

        # Clear and render
        console.clear()
        help_menu.render(console)

        # Check SDL availability
        print(f"   Context has sdl_renderer: {hasattr(context, 'sdl_renderer')}")
        if hasattr(context, 'sdl_renderer'):
            print(f"   SDL renderer is not None: {context.sdl_renderer is not None}")

        print(f"   Context has console_render: {hasattr(context, 'console_render')}")
        if hasattr(context, 'console_render'):
            print(f"   Console render is not None: {context.console_render is not None}")

        # Try rendering sprites on page 1 (objective - no sprites)
        print("\n7. Rendering page 1 (OBJECTIVE - no sprites expected)...")
        try:
            if context.sdl_renderer:
                context.sdl_renderer.clear()
                help_menu.render_sprites()
                print("   [OK] Page 1 rendered")
            else:
                print("   [FAIL] SDL renderer not available")
        except Exception as e:
            print(f"   [FAIL] Error rendering sprites: {e}")
            import traceback
            traceback.print_exc()

        # Navigate to page 2 (enemies - has sprites)
        print("\n8. Navigating to page 2 (ENEMY TYPES 1/2 - has sprites)...")
        help_menu.current_page = 1
        console.clear()
        help_menu.render(console)

        print("\n9. Rendering page 2 sprites...")
        try:
            if context.sdl_renderer:
                context.sdl_renderer.clear()
                help_menu.render_sprites()
                print("   [OK] Page 2 sprites rendered")
            else:
                print("   [FAIL] SDL renderer not available")
        except Exception as e:
            print(f"   [FAIL] Error rendering sprites: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n✗ Help menu does not have render_sprites method!")
        print(f"   This means the factory created: {type(help_menu).__name__}")
        print(f"   Expected: GraphicalHelpMenu")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
