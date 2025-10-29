"""Test the Square font box-drawing characters"""
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

print("Testing Square font (designed for roguelikes)")

# Test at native size first - Square is designed for small sizes
tileset = load_truetype_font_custom("square.ttf", 32, 32)
print(f"Loaded tileset: {tileset.tile_width}x{tileset.tile_height}")

console_width = 60
console_height = 30

with tcod.context.new(
    columns=console_width,
    rows=console_height,
    tileset=tileset,
    title="Square Font (Roguelike-specific) Test",
    vsync=True,
) as context:
    console = tcod.console.Console(console_width, console_height)

    print("\nWindow open - check box-drawing alignment!")

    while True:
        console.clear()

        console.print(2, 1, "Square Font Test (Brogue font)", fg=(0, 255, 255))

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

        # Sample text
        y += 6
        console.print(x, y, "Sample text: The quick brown fox", fg=(200, 200, 200))
        console.print(x, y+1, "Card suits: ♠ ♥ ♦ ♣", fg=(200, 200, 200))

        console.print(2, console_height - 2, "Press any key to exit", fg=(255, 255, 0))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT" or event.type == "KEYDOWN":
                print("\nTest complete!")
                raise SystemExit()
