"""
Test KreativeSquare at different scales to find one where box-drawing works.
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

# Test different tile sizes for KreativeSquare
test_sizes = [
    (32, 32, "32x32 (small)"),
    (48, 48, "48x48 (medium)"),
    (64, 64, "64x64 (current)"),
    (96, 96, "96x96 (large)"),
    (128, 128, "128x128 (very large)"),
]

current_test = 0

print("=" * 70)
print("KREATIVESQUARE SCALE FINDER")
print("=" * 70)
print("Testing different tile sizes to find optimal box-drawing alignment")
print("Press SPACE to cycle through sizes, ESC to exit")
print()

# Load all tilesets in advance
tilesets = []
for width, height, desc in test_sizes:
    print(f"Loading {desc}...")
    tileset = load_truetype_font_custom("KreativeSquare.ttf", width, height)
    tilesets.append((tileset, desc))

# Start with first tileset
tileset, desc = tilesets[current_test]

console_width = 60
console_height = 30

with tcod.context.new(
    columns=console_width,
    rows=console_height,
    tileset=tileset,
    title=f"KreativeSquare Scale Test - {desc}",
    vsync=True,
    sdl_window_flags=32
) as context:
    console = tcod.console.Console(console_width, console_height)

    print(f"\nWindow open - Starting with {desc}")
    print("Press SPACE to cycle sizes, ESC to exit")

    running = True
    while running:
        console.clear()

        # Title
        console.print(2, 1, f"Scale Test: {desc}", fg=(0, 255, 255))
        console.print(2, 2, "Press SPACE to change size", fg=(200, 200, 200))

        # Single-line box
        y = 5
        x = 5
        console.print(x, y, "Single-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "┌────┬────┐", fg=(0, 255, 0))
        console.print(x, y+1, "│    │    │", fg=(0, 255, 0))
        console.print(x, y+2, "├────┼────┤", fg=(0, 255, 0))
        console.print(x, y+3, "│    │    │", fg=(0, 255, 0))
        console.print(x, y+4, "└────┴────┘", fg=(0, 255, 0))

        # Double-line box
        y = 5
        x = 25
        console.print(x, y, "Double-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "╔════╦════╗", fg=(0, 255, 255))
        console.print(x, y+1, "║    ║    ║", fg=(0, 255, 255))
        console.print(x, y+2, "╠════╬════╣", fg=(0, 255, 255))
        console.print(x, y+3, "║    ║    ║", fg=(0, 255, 255))
        console.print(x, y+4, "╚════╩════╝", fg=(0, 255, 255))

        # Heavy-line box
        y = 12
        x = 5
        console.print(x, y, "Heavy-line:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "┏━━━━┳━━━━┓", fg=(255, 0, 255))
        console.print(x, y+1, "┃    ┃    ┃", fg=(255, 0, 255))
        console.print(x, y+2, "┣━━━━╋━━━━┫", fg=(255, 0, 255))
        console.print(x, y+3, "┃    ┃    ┃", fg=(255, 0, 255))
        console.print(x, y+4, "┗━━━━┻━━━━┛", fg=(255, 0, 255))

        # Test characters
        y = 12
        x = 25
        console.print(x, y, "Individual chars:", fg=(255, 255, 0))
        y += 1
        console.print(x, y,   "─ │ ┌ ┐ └ ┘", fg=(200, 200, 200))
        y += 1
        console.print(x, y,   "═ ║ ╔ ╗ ╚ ╝", fg=(200, 200, 200))
        y += 1
        console.print(x, y,   "━ ┃ ┏ ┓ ┗ ┛", fg=(200, 200, 200))

        # Rating area
        y = 20
        console.print(2, y, "Look for:", fg=(255, 255, 255))
        console.print(2, y+1, "  [1] All characters visible", fg=(200, 200, 200))
        console.print(2, y+2, "  [2] No gaps in boxes", fg=(200, 200, 200))
        console.print(2, y+3, "  [3] Corners connect perfectly", fg=(200, 200, 200))

        console.print(2, console_height - 2, "SPACE=next size  ESC=exit", fg=(255, 255, 0))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT":
                print("\nTest complete!")
                running = False
                break
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.KeySym.ESCAPE:
                    print("\nTest complete!")
                    running = False
                    break
                elif event.sym == tcod.event.KeySym.SPACE:
                    # Cycle to next size
                    current_test = (current_test + 1) % len(test_sizes)
                    tileset, desc = tilesets[current_test]
                    context.change_tileset(tileset)
                    print(f"Switched to: {desc}")

print("\nRECOMMENDATION: Use the size where all boxes connect without gaps")
