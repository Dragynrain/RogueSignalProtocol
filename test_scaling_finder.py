"""
Interactive scaling factor finder for KreativeSquare.
Use UP/DOWN arrows to adjust scaling in real-time.
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
import numpy as np
import freetype

def load_font_with_scaling(font_path: str, glyph_width: int, glyph_height: int, h_scale: float, v_scale: float) -> tcod.tileset.Tileset:
    """Load font with custom horizontal and vertical scaling."""
    face = freetype.Face(font_path)

    render_width = int(glyph_width * h_scale)
    render_height = int(glyph_height * v_scale)
    face.set_pixel_sizes(render_width, render_height)

    tileset = tcod.tileset.Tileset(glyph_width, glyph_height)

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

                # Horizontal: center
                left = (glyph_width - bitmap.width) // 2

                # Vertical: baseline at 75%
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


FONT_FILE = "KreativeSquare.ttf"
TARGET_SIZE = 64

# Start with 1.2x as a guess (between 1.0 and 1.7)
h_scale = 1.2
v_scale = 1.2
step = 0.05  # Adjust by 5% each time

print("=" * 70)
print("INTERACTIVE SCALING FACTOR FINDER")
print("=" * 70)
print(f"Font: {FONT_FILE}")
print(f"Target size: {TARGET_SIZE}x{TARGET_SIZE}")
print(f"\nStarting scale: {h_scale:.2f}x (horizontal) {v_scale:.2f}x (vertical)")
print("\nControls:")
print("  LEFT/RIGHT arrows: Horizontal smaller/bigger")
print("  DOWN/UP arrows: Vertical smaller/bigger")
print("  -/+ keys: Both scales smaller/bigger together")
print("  SPACE: Reset to 1.0x")
print("  Q or ESC: Quit")
print("\n" + "=" * 70)

CONSOLE_WIDTH = 30
CONSOLE_HEIGHT = 10

tileset = load_font_with_scaling(FONT_FILE, TARGET_SIZE, TARGET_SIZE, h_scale, v_scale)

with tcod.context.new(
    columns=CONSOLE_WIDTH,
    rows=CONSOLE_HEIGHT,
    tileset=tileset,
    title="Scaling Factor Finder - Use arrows to adjust",
    vsync=True
) as context:
    console = tcod.console.Console(CONSOLE_WIDTH, CONSOLE_HEIGHT)

    running = True
    while running:
        console.clear()

        # Display current scaling
        console.print(0, 0, f"H:{h_scale:.2f}x V:{v_scale:.2f}x", fg=(255, 255, 0))

        # Test content with full sentences
        console.print(0, 2, "The quick brown fox", fg=(255, 255, 255))
        console.print(0, 3, "jumps over the lazy", fg=(255, 255, 255))
        console.print(0, 4, "dog. Typography gyp!", fg=(255, 255, 255))
        console.print(0, 5, "WALLS: ||--┌┐└┘", fg=(0, 255, 255))
        console.print(0, 6, "0123456789 mmmm", fg=(255, 255, 0))
        console.print(0, 7, "Lorem ipsum dolor", fg=(200, 200, 200))

        console.print(0, 9, "Arrows/WS/Space Q=Quit", fg=(128, 128, 128))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT":
                running = False
            elif event.type == "KEYDOWN":
                changed = False

                if event.sym == tcod.event.KeySym.ESCAPE or event.sym == tcod.event.KeySym.Q:
                    running = False

                # Horizontal only (LEFT/RIGHT arrows)
                elif event.sym == tcod.event.KeySym.RIGHT:
                    h_scale += step
                    changed = True
                elif event.sym == tcod.event.KeySym.LEFT:
                    h_scale = max(0.5, h_scale - step)
                    changed = True

                # Vertical only (DOWN/UP arrows)
                elif event.sym == tcod.event.KeySym.UP:
                    v_scale += step
                    changed = True
                elif event.sym == tcod.event.KeySym.DOWN:
                    v_scale = max(0.5, v_scale - step)
                    changed = True

                # Both scales together (+/- keys)
                elif event.sym == tcod.event.KeySym.PLUS or event.sym == tcod.event.KeySym.EQUALS:
                    h_scale += step
                    v_scale += step
                    changed = True
                elif event.sym == tcod.event.KeySym.MINUS:
                    h_scale = max(0.5, h_scale - step)
                    v_scale = max(0.5, v_scale - step)
                    changed = True

                # Reset
                elif event.sym == tcod.event.KeySym.SPACE:
                    h_scale = 1.0
                    v_scale = 1.0
                    changed = True

                if changed:
                    print(f"Scale: H={h_scale:.2f}x V={v_scale:.2f}x")
                    tileset = load_font_with_scaling(FONT_FILE, TARGET_SIZE, TARGET_SIZE, h_scale, v_scale)
                    context.change_tileset(tileset)

print("\n" + "=" * 70)
print(f"FINAL SCALING FACTORS:")
print(f"  Horizontal: {h_scale:.2f}x")
print(f"  Vertical: {v_scale:.2f}x")
print("=" * 70)
print("\nAdd these to your font loader:")
print(f"  render_width = int(glyph_width * {h_scale:.2f})")
print(f"  render_height = int(glyph_height * {v_scale:.2f})")
