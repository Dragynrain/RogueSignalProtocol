"""Quick diagnostic to check horizontal bearing values for box-drawing chars."""
import freetype

face = freetype.Face("KreativeSquare.ttf")
face.set_pixel_sizes(64, 64)

# Test characters - compare single, double, heavy
test_groups = {
    'SINGLE-LINE': {
        '─': 'horizontal',
        '│': 'vertical',
        '┌': 'top-left corner',
        '┐': 'top-right corner',
        '└': 'bottom-left corner',
        '┘': 'bottom-right corner',
        '├': 'left T',
        '┤': 'right T',
    },
    'DOUBLE-LINE': {
        '═': 'horizontal',
        '║': 'vertical',
        '╔': 'top-left corner',
        '╗': 'top-right corner',
        '╚': 'bottom-left corner',
        '╝': 'bottom-right corner',
        '╠': 'left T',
        '╣': 'right T',
    },
    'HEAVY-LINE': {
        '━': 'horizontal',
        '┃': 'vertical',
        '┏': 'top-left corner',
        '┓': 'top-right corner',
        '┗': 'bottom-left corner',
        '┛': 'bottom-right corner',
        '┣': 'left T',
        '┫': 'right T',
    },
}

print("KreativeSquare Box-Drawing Bearings (64x64):")
print("=" * 80)

for group_name, test_chars in test_groups.items():
    print(f"\n{group_name}:")
    print("-" * 80)
    for char, desc in test_chars.items():
        face.load_char(char, freetype.FT_LOAD_RENDER)
        bitmap = face.glyph.bitmap
        bearing_x = face.glyph.bitmap_left
        bearing_y = face.glyph.bitmap_top
        width = bitmap.width
        height = bitmap.rows

        print(f"U+{ord(char):04X} {desc:20s} - bearingX={bearing_x:3d}, bearingY={bearing_y:3d}, width={width:2d}, height={height:2d}")
