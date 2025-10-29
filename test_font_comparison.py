"""
Compare three different font loading approaches to see which produces the best results.

Method A: TCOD with explicit width+height (current approach)
Method B: TCOD with width=0 (auto-sizing trick)
Method C: Custom FreeType loader (manual compensation)
"""
import ctypes
import sys

# Set DPI awareness BEFORE importing tcod
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    print("[OK] DPI awareness enabled (PROCESS_PER_MONITOR_DPI_AWARE)")
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        print("[OK] DPI awareness enabled (fallback)")
    except:
        print("[WARN] Could not set DPI awareness")

import tcod
from font_loader_freetype import load_truetype_font_custom

# Test parameters
FONT_FILE = "KreativeSquare.ttf"
TARGET_WIDTH = 64   # Tile size to test
TARGET_HEIGHT = 64

print("\n" + "=" * 70)
print("FONT LOADING COMPARISON TEST")
print("=" * 70)
print(f"Tile size: {TARGET_WIDTH}×{TARGET_HEIGHT}\n")

# Method A: Current approach (explicit width + height)
print("Method A: TCOD with explicit width+height")
print(f"  load_truetype_font('{FONT_FILE}', {TARGET_WIDTH}, {TARGET_HEIGHT})")
try:
    tileset_a = tcod.tileset.load_truetype_font(FONT_FILE, TARGET_WIDTH, TARGET_HEIGHT)
    print(f"  [OK] Created tileset: {tileset_a.tile_width}x{tileset_a.tile_height}")
except Exception as e:
    print(f"  [FAIL] {e}")
    tileset_a = None

# Method B: TCOD with width=0 (auto-sizing - BROKEN, just for testing)
print("\nMethod B: TCOD with width=0 (auto-sizing - creates distorted glyphs)")
print(f"  load_truetype_font('{FONT_FILE}', 0, {TARGET_HEIGHT})")
try:
    tileset_b = tcod.tileset.load_truetype_font(FONT_FILE, 0, TARGET_HEIGHT)
    print(f"  [OK] Created tileset: {tileset_b.tile_width}x{tileset_b.tile_height}")
except Exception as e:
    print(f"  [FAIL] {e}")
    tileset_b = None

# Method C: Custom FreeType loader
print("\nMethod C: Custom FreeType loader (manual compensation)")
print(f"  load_truetype_font_custom('{FONT_FILE}', {TARGET_WIDTH}, {TARGET_HEIGHT})")
try:
    tileset_c = load_truetype_font_custom(FONT_FILE, TARGET_WIDTH, TARGET_HEIGHT)
    print(f"  [OK] Created tileset: {tileset_c.tile_width}x{tileset_c.tile_height}")
except Exception as e:
    print(f"  [FAIL] {e}")
    tileset_c = None

# Create comparison window
print("\n" + "=" * 70)
print("VISUAL COMPARISON")
print("=" * 70)
print("Opening window with side-by-side comparison...")
print("Look for:")
print("  - Glyph size (do they fill the tiles?)")
print("  - Vertical wall gaps (| should be connected)")
print("  - Horizontal wall gaps (- should be connected)")
print("  - Descenders (g, y, p, q, j should have tails)")
print("\nPress 1, 2, or 3 to switch between methods")
print("Press Q or ESC to quit\n")

# Set up window dimensions
CONSOLE_WIDTH = 30
CONSOLE_HEIGHT = 10

# Start with method A
current_method = 'A'
tilesets = {'A': tileset_a, 'B': tileset_b, 'C': tileset_c}
methods = {
    'A': 'Method A: TCOD explicit (current)',
    'B': 'Method B: TCOD width=0 (distorted)',
    'C': 'Method C: Custom FreeType'
}

# Use first available tileset
current_tileset = tileset_a or tileset_b or tileset_c
if not current_tileset:
    print("ERROR: No tilesets loaded successfully!")
    sys.exit(1)

with tcod.context.new(
    columns=CONSOLE_WIDTH,
    rows=CONSOLE_HEIGHT,
    tileset=current_tileset,
    title="Font Loading Comparison - Press 1/2/3 to switch",
    vsync=True
) as context:
    console = tcod.console.Console(CONSOLE_WIDTH, CONSOLE_HEIGHT)

    # Show actual window size
    if hasattr(context, 'sdl_window'):
        actual = context.sdl_window.size
        print(f"Window size: {actual[0]}×{actual[1]}px")
        effective_tile_w = actual[0] / CONSOLE_WIDTH
        effective_tile_h = actual[1] / CONSOLE_HEIGHT
        print(f"Effective tile size: {effective_tile_w:.1f}×{effective_tile_h:.1f}px\n")

    running = True
    while running:
        console.clear()

        # Title showing current method
        title = methods[current_method]
        console.print(0, 0, title, fg=(255, 255, 0))
        console.print(0, 1, "=" * len(title), fg=(128, 128, 128))

        # Test content
        console.print(0, 3, "0123456789", fg=(255, 255, 255))
        console.print(0, 4, "Typography", fg=(255, 255, 255))
        console.print(0, 5, "WALLS ││┌┐└┘─", fg=(0, 255, 255))
        console.print(0, 6, "gyp qj fox", fg=(255, 255, 0))
        console.print(0, 7, "AAAAAAAAAA", fg=(255, 255, 255))

        # Instructions
        console.print(0, 9, "1/2/3=Switch Q=Quit", fg=(128, 128, 128))

        context.present(console)

        for event in tcod.event.wait():
            if event.type == "QUIT":
                running = False
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.KeySym.ESCAPE or event.sym == tcod.event.KeySym.Q:
                    running = False
                elif event.sym == tcod.event.KeySym.N1 and tilesets['A']:
                    current_method = 'A'
                    context.change_tileset(tilesets['A'])
                    print(f"\nSwitched to {methods['A']}")
                    print(f"  Tileset: {tilesets['A'].tile_width}×{tilesets['A'].tile_height}")
                elif event.sym == tcod.event.KeySym.N2 and tilesets['B']:
                    current_method = 'B'
                    context.change_tileset(tilesets['B'])
                    print(f"\nSwitched to {methods['B']}")
                    print(f"  Tileset: {tilesets['B'].tile_width}×{tilesets['B'].tile_height}")
                elif event.sym == tcod.event.KeySym.N3 and tilesets['C']:
                    current_method = 'C'
                    context.change_tileset(tilesets['C'])
                    print(f"\nSwitched to {methods['C']}")
                    print(f"  Tileset: {tilesets['C'].tile_width}×{tilesets['C'].tile_height}")

print("\nComparison test complete.")
print("\nSUMMARY:")
for method in ['A', 'B', 'C']:
    ts = tilesets[method]
    if ts:
        print(f"  {methods[method]}: {ts.tile_width}×{ts.tile_height}")
    else:
        print(f"  {methods[method]}: FAILED")
