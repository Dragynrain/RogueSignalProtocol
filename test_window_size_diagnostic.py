"""
Diagnostic test to understand TCOD window sizing behavior.
"""
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

import tcod

# Test with different tile sizes
TILE_SIZES = [12, 16, 24, 32, 64, 96]
CONSOLE_SIZE = (80, 50)

print("=" * 80)
print("WINDOW SIZE DIAGNOSTIC")
print("=" * 80)
print(f"Console size: {CONSOLE_SIZE[0]}×{CONSOLE_SIZE[1]} characters")
print()

for tile_size in TILE_SIZES:
    print(f"\nTesting tile size: {tile_size}×{tile_size}px")
    print("-" * 40)

    # Load font at this tile size
    tileset = tcod.tileset.load_truetype_font(
        "CascadiaCode-Regular.ttf",
        tile_size,
        tile_size
    )

    print(f"  Tileset created: {tileset.tile_width}×{tileset.tile_height}px per tile")

    # Calculate theoretical window size
    theoretical_width = CONSOLE_SIZE[0] * tile_size
    theoretical_height = CONSOLE_SIZE[1] * tile_size
    print(f"  Theoretical window size: {theoretical_width}×{theoretical_height}px")

    # Create context WITHOUT specifying width/height
    with tcod.context.new(
        columns=CONSOLE_SIZE[0],
        rows=CONSOLE_SIZE[1],
        tileset=tileset,
        title=f"Test {tile_size}×{tile_size}",
        vsync=True
    ) as context:
        console = tcod.console.Console(CONSOLE_SIZE[0], CONSOLE_SIZE[1])

        # Try to get actual window size from SDL
        if hasattr(context, 'sdl_window'):
            import ctypes
            from ctypes import c_int, byref

            # Get window size
            w, h = c_int(), c_int()
            # This is a bit hacky but should work
            try:
                # SDL_GetWindowSize
                context.sdl_window.size  # Try to access if available
                print(f"  Actual window size: {context.sdl_window.size}")
            except:
                print(f"  Actual window size: <unable to query>")

        # Render a test frame
        console.clear()
        console.print(0, 0, f"Tile size: {tile_size}×{tile_size}px", fg=(255, 255, 255))
        console.print(0, 1, f"Theoretical: {theoretical_width}×{theoretical_height}px window", fg=(200, 200, 200))
        console.print(0, 3, "AAAAA #####", fg=(0, 255, 0))
        console.print(0, 4, "Press any key to continue...", fg=(255, 255, 0))

        context.present(console)

        # Wait for keypress
        for event in tcod.event.wait():
            if event.type == "KEYDOWN" or event.type == "QUIT":
                break

print("\n" + "=" * 80)
print("Test complete!")
