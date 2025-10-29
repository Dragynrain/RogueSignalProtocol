"""Test KreativeSquare at its native 32x32 size"""
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

print("Testing KreativeSquare at NATIVE 32x32 size")

# Load at 32x32 (native size for the font)
tileset = load_truetype_font_custom("KreativeSquare.ttf", 32, 32)
print(f"Loaded tileset: {tileset.tile_width}x{tileset.tile_height}")

console_width = 60
console_height = 30

with tcod.context.new(
    columns=console_width,
    rows=console_height,
    tileset=tileset,
    title="KreativeSquare 32x32 (Native Size) Test",
    vsync=True,
) as context:
    console = tcod.console.Console(console_width, console_height)

    print("\nWindow open - check if boxes line up perfectly at native size!")

    while True:
        console.clear()

        console.print(2, 1, "KreativeSquare @ 32x32 (NATIVE)", fg=(0, 255, 255))

        # Visual boxes
        y = 4
        x = 2
        console.print(x, y, "Single-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "┌───┬───┐", fg=(0, 255, 0))
        console.print(x, y+1, "│   │   │", fg=(0, 255, 0))
        console.print(x, y+2, "├───┼───┤", fg=(0, 255, 0))
        console.print(x, y+3, "│   │   │", fg=(0, 255, 0))
        console.print(x, y+4, "└───┴───┘", fg=(0, 255, 0))

        y += 6
        console.print(x, y, "Double-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "╔═══╦═══╗", fg=(0, 255, 255))
        console.print(x, y+1, "║   ║   ║", fg=(0, 255, 255))
        console.print(x, y+2, "╠═══╬═══╣", fg=(0, 255, 255))
        console.print(x, y+3, "║   ║   ║", fg=(0, 255, 255))
        console.print(x, y+4, "╚═══╩═══╝", fg=(0, 255, 255))

        y += 6
        console.print(x, y, "Heavy-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "┏━━━┳━━━┓", fg=(255, 0, 255))
        console.print(x, y+1, "┃   ┃   ┃", fg=(255, 0, 255))
        console.print(x, y+2, "┣━━━╋━━━┫", fg=(255, 0, 255))
        console.print(x, y+3, "┃   ┃   ┃", fg=(255, 0, 255))
        console.print(x, y+4, "┗━━━┻━━━┛", fg=(255, 0, 255))

        console.print(2, console_height - 2, "Press any key to exit", fg=(255, 255, 0))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT" or event.type == "KEYDOWN":
                print("\nTest complete!")
                raise SystemExit()
