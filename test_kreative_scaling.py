"""
Test KreativeSquare with proper scaling factor (1.5x instead of 1.7x).
"""
import ctypes
import sys

# Set DPI awareness BEFORE importing tcod
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

import tcod
from font_loader_freetype import load_truetype_font_custom
import numpy as np
import freetype

def load_kreative_custom(glyph_width: int, glyph_height: int) -> tcod.tileset.Tileset:
    """
    Load KreativeSquare with proper 1.5× scaling (not 1.7×).
    """
    face = freetype.Face("KreativeSquare.ttf")

    # For KreativeSquare: glyphs are 67% of requested size
    # So we need to request 1.5× to get 100% fill
    render_width = int(glyph_width * 1.5)
    render_height = int(glyph_height * 1.5)
    face.set_pixel_sizes(render_width, render_height)

    tileset = tcod.tileset.Tileset(glyph_width, glyph_height)

    # Load printable ASCII + box drawing
    chars = (
        "".join(chr(i) for i in range(32, 127)) +
        "│─┌┐└┘├┤┬┴┼" +
        "║═╔╗╚╝"
    )

    for char in chars:
        codepoint = ord(char)
        try:
            face.load_char(char, freetype.FT_LOAD_RENDER)
            bitmap = face.glyph.bitmap

            output = np.zeros((glyph_height, glyph_width, 4), dtype=np.uint8)

            if bitmap.width > 0 and bitmap.rows > 0:
                glyph_data = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, bitmap.width)

                # Horizontal: center in tile
                left = (glyph_width - bitmap.width) // 2

                # Vertical: baseline at 75% down
                baseline_position = int(glyph_height * 0.75)
                top = baseline_position - face.glyph.bitmap_top

                # Calculate valid region
                src_top = max(0, -top)
                src_left = max(0, -left)
                src_bottom = min(bitmap.rows, glyph_height - top)
                src_right = min(bitmap.width, glyph_width - left)

                dst_top = max(0, top)
                dst_left = max(0, left)
                dst_bottom = min(glyph_height, top + bitmap.rows)
                dst_right = min(glyph_width, left + bitmap.width)

                if dst_bottom > dst_top and dst_right > dst_left:
                    output[dst_top:dst_bottom, dst_left:dst_right, :3] = 255
                    output[dst_top:dst_bottom, dst_left:dst_right, 3] = glyph_data[src_top:src_bottom, src_left:src_right]

            tileset.set_tile(codepoint, output)
        except:
            pass

    return tileset


# Test parameters
TARGET_WIDTH = 64
TARGET_HEIGHT = 64

print("=" * 70)
print("KREATIVESQUARE SCALING TEST")
print("=" * 70)
print(f"Target tile size: {TARGET_WIDTH}×{TARGET_HEIGHT}\n")

# Method A: TCOD explicit (for comparison)
print("Method A: TCOD explicit 64×64")
tileset_a = tcod.tileset.load_truetype_font("KreativeSquare.ttf", TARGET_WIDTH, TARGET_HEIGHT)
print(f"  Tileset: {tileset_a.tile_width}×{tileset_a.tile_height}")

# Method B: Custom FreeType with 1.7× (too big)
print("\nMethod B: Custom FreeType 1.7× (original - too big)")
tileset_b = load_truetype_font_custom("KreativeSquare.ttf", TARGET_WIDTH, TARGET_HEIGHT)
print(f"  Tileset: {tileset_b.tile_width}×{tileset_b.tile_height}")

# Method C: Custom FreeType with 1.5× (should be perfect!)
print("\nMethod C: Custom FreeType 1.5× (adjusted for KreativeSquare)")
tileset_c = load_kreative_custom(TARGET_WIDTH, TARGET_HEIGHT)
print(f"  Tileset: {tileset_c.tile_width}×{tileset_c.tile_height}")

print("\n" + "=" * 70)
print("VISUAL COMPARISON")
print("=" * 70)
print("Press 1/2/3 to switch between methods")
print("  1 = TCOD explicit (too small)")
print("  2 = Custom 1.7× (too big - original)")
print("  3 = Custom 1.5× (adjusted - should be just right!)")
print("Press Q or ESC to quit\n")

CONSOLE_WIDTH = 30
CONSOLE_HEIGHT = 10

current_method = 'A'
tilesets = {'A': tileset_a, 'B': tileset_b, 'C': tileset_c}
methods = {
    'A': 'Method A: TCOD explicit (too small)',
    'B': 'Method B: Custom 1.7x (too big)',
    'C': 'Method C: Custom 1.5x (adjusted)'
}

with tcod.context.new(
    columns=CONSOLE_WIDTH,
    rows=CONSOLE_HEIGHT,
    tileset=tileset_a,
    title="KreativeSquare Scaling Test - Press 1/2/3",
    vsync=True
) as context:
    console = tcod.console.Console(CONSOLE_WIDTH, CONSOLE_HEIGHT)

    running = True
    while running:
        console.clear()

        title = methods[current_method]
        console.print(0, 0, title, fg=(255, 255, 0))
        console.print(0, 1, "=" * len(title), fg=(128, 128, 128))

        console.print(0, 3, "0123456789", fg=(255, 255, 255))
        console.print(0, 4, "Typography", fg=(255, 255, 255))
        console.print(0, 5, "WALLS ||--", fg=(0, 255, 255))
        console.print(0, 6, "gyp qj fox mmmm", fg=(255, 255, 0))
        console.print(0, 7, "AAAAAAAAAA", fg=(255, 255, 255))

        console.print(0, 9, "1/2/3=Switch Q=Quit", fg=(128, 128, 128))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT":
                running = False
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.KeySym.ESCAPE or event.sym == tcod.event.KeySym.Q:
                    running = False
                elif event.sym == tcod.event.KeySym.N1:
                    current_method = 'A'
                    context.change_tileset(tilesets['A'])
                    print(f"\nSwitched to {methods['A']}")
                elif event.sym == tcod.event.KeySym.N2:
                    current_method = 'B'
                    context.change_tileset(tilesets['B'])
                    print(f"\nSwitched to {methods['B']}")
                elif event.sym == tcod.event.KeySym.N3:
                    current_method = 'C'
                    context.change_tileset(tilesets['C'])
                    print(f"\nSwitched to {methods['C']}")

print("\nTest complete!")
