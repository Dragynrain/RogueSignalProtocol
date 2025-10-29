"""
Inspect which glyphs are actually available in a font.
Specifically checks box-drawing characters and other game-critical glyphs.
"""
import freetype
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_glyph_support(font_path: str):
    """Check which specific glyphs are available in the font."""
    face = freetype.Face(font_path)

    print(f"\n{'='*70}")
    print(f"GLYPH SUPPORT CHECK: {font_path}")
    print(f"{'='*70}")
    print(f"Font: {face.family_name.decode('utf-8')} - {face.style_name.decode('utf-8')}")
    print(f"Total glyphs: {face.num_glyphs}")

    # Categories to test
    tests = {
        "Single-Line Box Drawing (gameplay)": [
            ('─', 0x2500, "Horizontal"),
            ('│', 0x2502, "Vertical"),
            ('┌', 0x250C, "Top-left corner"),
            ('┐', 0x2510, "Top-right corner"),
            ('└', 0x2514, "Bottom-left corner"),
            ('┘', 0x2518, "Bottom-right corner"),
            ('├', 0x251C, "T-right"),
            ('┤', 0x2524, "T-left"),
            ('┬', 0x252C, "T-down"),
            ('┴', 0x2534, "T-up"),
            ('┼', 0x253C, "Cross"),
        ],
        "Double-Line Box Drawing (dialogues)": [
            ('═', 0x2550, "Horizontal"),
            ('║', 0x2551, "Vertical"),
            ('╔', 0x2554, "Top-left corner"),
            ('╗', 0x2557, "Top-right corner"),
            ('╚', 0x255A, "Bottom-left corner"),
            ('╝', 0x255D, "Bottom-right corner"),
        ],
        "Heavy-Line Box Drawing (alternative)": [
            ('━', 0x2501, "Horizontal"),
            ('┃', 0x2503, "Vertical"),
            ('┏', 0x250F, "Top-left corner"),
            ('┓', 0x2513, "Top-right corner"),
            ('┗', 0x2517, "Bottom-left corner"),
            ('┛', 0x251B, "Bottom-right corner"),
            ('┣', 0x252B, "T-right"),
            ('┫', 0x2523, "T-left"),
            ('┳', 0x2533, "T-down"),
            ('┻', 0x253B, "T-up"),
            ('╋', 0x254B, "Cross"),
        ],
        "Block Elements (common alternatives)": [
            ('█', 0x2588, "Full block"),
            ('▄', 0x2584, "Lower half block"),
            ('▀', 0x2580, "Upper half block"),
            ('■', 0x25A0, "Black square (isolated wall)"),
            ('□', 0x25A1, "White square"),
        ],
        "Game Glyphs": [
            ('☺', 0x263A, "Player"),
            ('♦', 0x2666, "Diamond"),
            ('♥', 0x2665, "Heart"),
            ('♠', 0x2660, "Spade"),
            ('•', 0x2022, "Bullet"),
            ('○', 0x25CB, "Circle"),
            ('♫', 0x266B, "Musical notes"),
            ('§', 0x00A7, "Section sign"),
        ],
        "ASCII Fallbacks": [
            ('|', 0x007C, "Pipe"),
            ('-', 0x002D, "Dash"),
            ('+', 0x002B, "Plus"),
            ('#', 0x0023, "Hash"),
        ],
    }

    # Check each category
    for category, chars in tests.items():
        print(f"\n[{category}]")
        missing = []
        available = []

        for char, codepoint, description in chars:
            # Try to get the glyph index
            glyph_index = face.get_char_index(codepoint)

            if glyph_index == 0:  # 0 means glyph not found
                missing.append((char, codepoint, description))
                status = "[ ] MISSING"
            else:
                available.append((char, codepoint, description))
                status = f"[X] Available (glyph #{glyph_index})"

            print(f"  {char} U+{codepoint:04X} {description:20s} {status}")

        # Summary
        total = len(chars)
        avail_count = len(available)
        miss_count = len(missing)

        if miss_count == 0:
            print(f"  >> ALL {total} characters available!")
        elif avail_count == 0:
            print(f"  >> NONE available ({miss_count}/{total} missing)")
        else:
            print(f"  >> {avail_count}/{total} available, {miss_count} missing")

    print()


def find_alternatives(font_path: str):
    """Search for ANY box-drawing-like characters in the font."""
    face = freetype.Face(font_path)

    print(f"\n{'='*70}")
    print(f"SCANNING FOR BOX-DRAWING ALTERNATIVES")
    print(f"{'='*70}")

    # Box Drawing Unicode block: U+2500 to U+257F
    box_start = 0x2500
    box_end = 0x257F

    found = []
    for codepoint in range(box_start, box_end + 1):
        glyph_index = face.get_char_index(codepoint)
        if glyph_index != 0:
            try:
                char = chr(codepoint)
                found.append((char, codepoint, glyph_index))
            except:
                pass

    if found:
        print(f"Found {len(found)} box-drawing characters in U+2500-257F range:")
        for char, codepoint, glyph_idx in found:
            print(f"  {char} U+{codepoint:04X} (glyph #{glyph_idx})")
    else:
        print("** NO box-drawing characters found in U+2500-257F range! **")
        print("This font does not support standard box-drawing glyphs.")

    print()


if __name__ == "__main__":
    fonts_to_check = [
        "KreativeSquare.ttf",
        "CascadiaCode-Regular.ttf"
    ]

    for font in fonts_to_check:
        try:
            check_glyph_support(font)
            find_alternatives(font)
        except Exception as e:
            print(f"\n** Error loading {font}: {e}\n")

    print("="*70)
    print("RECOMMENDATION:")
    print("="*70)
    print("If KreativeSquare is missing box-drawing chars, you can:")
    print("  1. Use CascadiaCode (confirmed to have full support)")
    print("  2. Find another square font with box-drawing support")
    print("  3. Use ASCII fallbacks (|, -, +, #) for KreativeSquare")
    print("="*70)
