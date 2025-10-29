"""
Check if glyphs actually RENDER (not just exist in the font).
FreeType may report a glyph exists but it could be empty/broken.
"""
import freetype
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_glyph_rendering(font_path: str, size: int = 64):
    """Check if glyphs actually produce bitmap data when rendered."""
    face = freetype.Face(font_path)
    face.set_pixel_sizes(size, size)

    print(f"\n{'='*70}")
    print(f"GLYPH BITMAP RENDERING CHECK: {font_path}")
    print(f"Font: {face.family_name.decode('utf-8')}")
    print(f"Size: {size}x{size}px")
    print(f"{'='*70}")

    tests = [
        ("Single-Line Box", [
            ('─', 0x2500, "Horizontal"),
            ('│', 0x2502, "Vertical"),
            ('┌', 0x250C, "Top-left"),
            ('┐', 0x2510, "Top-right"),
        ]),
        ("Double-Line Box", [
            ('═', 0x2550, "Horizontal"),
            ('║', 0x2551, "Vertical"),
            ('╔', 0x2554, "Top-left"),
            ('╗', 0x2557, "Top-right"),
        ]),
        ("Heavy-Line Box", [
            ('━', 0x2501, "Horizontal"),
            ('┃', 0x2503, "Vertical"),
            ('┏', 0x250F, "Top-left"),
            ('┓', 0x2513, "Top-right"),
            ('╋', 0x254B, "Cross"),
        ]),
        ("ASCII", [
            ('A', 0x0041, "Letter A"),
            ('|', 0x007C, "Pipe"),
            ('-', 0x002D, "Dash"),
        ]),
    ]

    for category, chars in tests:
        print(f"\n[{category}]")

        for char, codepoint, desc in chars:
            glyph_idx = face.get_char_index(codepoint)

            if glyph_idx == 0:
                print(f"  {char} U+{codepoint:04X} {desc:15s} >> NOT IN FONT")
                continue

            # Try to render it
            try:
                face.load_char(char, freetype.FT_LOAD_RENDER)
                bitmap = face.glyph.bitmap

                # Check if bitmap has actual content
                if bitmap.width == 0 or bitmap.rows == 0:
                    status = f">> EMPTY (glyph #{glyph_idx}, no pixels)"
                else:
                    # Count non-zero pixels
                    import numpy as np
                    bitmap_data = np.array(bitmap.buffer, dtype=np.uint8)
                    non_zero = np.count_nonzero(bitmap_data)
                    total = bitmap.width * bitmap.rows
                    coverage = (non_zero / total * 100) if total > 0 else 0

                    if non_zero == 0:
                        status = f">> ALL BLACK (glyph #{glyph_idx}, {bitmap.width}x{bitmap.rows}, 0 pixels drawn)"
                    else:
                        status = f">> OK (glyph #{glyph_idx}, {bitmap.width}x{bitmap.rows}, {non_zero}/{total} pixels = {coverage:.1f}%)"

                # Also show metrics
                metrics = face.glyph.metrics
                adv = metrics.horiAdvance / 64
                bearing_y = metrics.horiBearingY / 64

                print(f"  {char} U+{codepoint:04X} {desc:15s} {status}")
                print(f"      advance={adv:.1f}px, bearingY={bearing_y:.1f}px, top={face.glyph.bitmap_top}")

            except Exception as e:
                print(f"  {char} U+{codepoint:04X} {desc:15s} >> ERROR: {e}")


if __name__ == "__main__":
    check_glyph_rendering("KreativeSquare.ttf", 64)
    print("\n" + "="*70)
    print("COMPARISON:")
    print("="*70)
    check_glyph_rendering("CascadiaCode-Regular.ttf", 64)
