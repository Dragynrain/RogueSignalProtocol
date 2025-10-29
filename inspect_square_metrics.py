"""Check Square font metrics"""
import freetype

face = freetype.Face("square.ttf")
face.set_pixel_sizes(32, 32)

test_chars = ['A', 'g', 'T', 'y', '─', '│', '╔']

print("Square font metrics at 32x32:")
print("=" * 70)

for char in test_chars:
    face.load_char(char, freetype.FT_LOAD_RENDER)
    bitmap = face.glyph.bitmap

    print(f"{char} - bitmap_top={face.glyph.bitmap_top:3d}, bitmap_left={face.glyph.bitmap_left:3d}, "
          f"width={bitmap.width:2d}, height={bitmap.rows:2d}")

    # Calculate what our loader does
    baseline_at_75 = int(32 * 0.75)  # = 24
    top = baseline_at_75 - face.glyph.bitmap_top

    print(f"     baseline=24, calculated_top={top:3d} ", end="")
    if top < 0:
        print(f"⚠️ NEGATIVE! Will clip {-top} pixels from top!")
    else:
        print("✓")
