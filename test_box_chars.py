"""
Test script to display all box-drawing characters in KreativeSquare font.
Shows single-line, double-line, and various other line-drawing symbols.
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
from font_loader_freetype import load_truetype_font_custom

print("=" * 70)
print("BOX-DRAWING CHARACTER TEST - KreativeSquare Font")
print("=" * 70)

# Load KreativeSquare with current settings (64x64, 1.0x scale)
tileset = load_truetype_font_custom("KreativeSquare.ttf", 64, 64)
print(f"Loaded tileset: {tileset.tile_width}x{tileset.tile_height}")

# Create test window
console_width = 60
console_height = 30
pixel_width = console_width * tileset.tile_width
pixel_height = console_height * tileset.tile_height

with tcod.context.new(
    columns=console_width,
    rows=console_height,
    tileset=tileset,
    title="KreativeSquare Box-Drawing Characters Test",
    vsync=True,
    sdl_window_flags=32  # Resizable, not maximized
) as context:
    console = tcod.console.Console(console_width, console_height)

    print("\nWindow open - press any key to exit")
    print("Look for characters that are CENTERED in their tiles")

    while True:
        console.clear()

        # Title
        console.print(2, 1, "KreativeSquare Box-Drawing Test", fg=(0, 255, 255))
        console.print(2, 2, "Find characters centered in tiles:", fg=(200, 200, 200))

        # SINGLE-LINE box drawing
        y = 4
        console.print(2, y, "SINGLE-LINE:", fg=(255, 255, 0))
        y += 1
        console.print(2, y, "Horizontal: ─  (U+2500)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Vertical:   │  (U+2502)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Corners:    ┌┐└┘  (U+250C,2510,2514,2518)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "T-shapes:   ├┤┬┴  (U+251C,2524,252C,2534)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Cross:      ┼  (U+253C)", fg=(255, 255, 255))

        # DOUBLE-LINE box drawing
        y += 2
        console.print(2, y, "DOUBLE-LINE:", fg=(255, 255, 0))
        y += 1
        console.print(2, y, "Horizontal: ═  (U+2550)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Vertical:   ║  (U+2551)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Corners:    ╔╗╚╝  (U+2554,2557,255A,255D)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "T-shapes:   ╠╣╦╩  (U+2560,2563,2566,2569)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Cross:      ╬  (U+256C)", fg=(255, 255, 255))

        # ASCII alternatives
        y += 2
        console.print(2, y, "ASCII (always centered):", fg=(255, 255, 0))
        y += 1
        console.print(2, y, "Pipe/dash:  | -  (U+007C, 002D)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Plus:       +  (U+002B)", fg=(255, 255, 255))

        # HEAVY box drawing (often well-centered)
        y += 2
        console.print(2, y, "HEAVY-LINE:", fg=(255, 255, 0))
        y += 1
        console.print(2, y, "Horizontal: ━  (U+2501)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Vertical:   ┃  (U+2503)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Corners:    ┏┓┗┛  (U+250F,2513,2517,251B)", fg=(255, 255, 255))
        y += 1
        console.print(2, y, "Cross:      ╋  (U+254B)", fg=(255, 255, 255))

        # Visual comparison - draw actual boxes
        y = 4
        x = 35
        console.print(x, y, "VISUAL TEST:", fg=(255, 255, 0))

        y += 2
        console.print(x, y, "Single-line box:", fg=(200, 200, 200))
        y += 1
        console.print(x, y,   "┌───┬───┐", fg=(0, 255, 0))
        console.print(x, y+1, "│   │   │", fg=(0, 255, 0))
        console.print(x, y+2, "├───┼───┤", fg=(0, 255, 0))
        console.print(x, y+3, "│   │   │", fg=(0, 255, 0))
        console.print(x, y+4, "└───┴───┘", fg=(0, 255, 0))

        y += 6
        console.print(x, y, "Double-line box:", fg=(200, 200, 200))
        y += 1
        console.print(x, y,   "╔═══╦═══╗", fg=(0, 255, 255))
        console.print(x, y+1, "║   ║   ║", fg=(0, 255, 255))
        console.print(x, y+2, "╠═══╬═══╣", fg=(0, 255, 255))
        console.print(x, y+3, "║   ║   ║", fg=(0, 255, 255))
        console.print(x, y+4, "╚═══╩═══╝", fg=(0, 255, 255))

        y += 6
        console.print(x, y, "Heavy-line box:", fg=(200, 200, 200))
        y += 1
        console.print(x, y,   "┏━━━┳━━━┓", fg=(255, 0, 255))
        console.print(x, y+1, "┃   ┃   ┃", fg=(255, 0, 255))
        console.print(x, y+2, "┣━━━╋━━━┫", fg=(255, 0, 255))
        console.print(x, y+3, "┃   ┃   ┃", fg=(255, 0, 255))
        console.print(x, y+4, "┗━━━┻━━━┛", fg=(255, 0, 255))

        # Instructions
        console.print(2, console_height - 2, "Press any key to exit", fg=(255, 255, 0))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT" or event.type == "KEYDOWN":
                print("\nTest complete!")
                raise SystemExit()
