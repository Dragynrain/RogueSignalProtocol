"""
Custom TrueType font loader using FreeType for proper glyph scaling.

This bypasses tcod's broken load_truetype_font() which doesn't properly scale glyphs.
Based on python-tcod's examples/ttf.py.
"""
import numpy as np
import freetype
import tcod.tileset


def load_truetype_font_custom(font_path: str, glyph_width: int, glyph_height: int, chars: str = None,
                              h_scale: float = None, v_scale: float = None) -> tcod.tileset.Tileset:
    """
    Load a TrueType font with explicit glyph size control using FreeType.

    Args:
        font_path: Path to .ttf or .otf file
        glyph_width: Exact width of glyphs in pixels
        glyph_height: Exact height of glyphs in pixels
        chars: Optional string of characters to load (default: printable ASCII + common symbols)
        h_scale: Horizontal scaling factor (default: 1.0 for square fonts like KreativeSquare)
        v_scale: Vertical scaling factor (default: 1.0 for square fonts)

    Returns:
        Tileset with properly-sized glyphs
    """
    # Load font with FreeType
    face = freetype.Face(font_path)

    # Auto-detect scaling based on font name if not specified
    if h_scale is None or v_scale is None:
        font_name = font_path.lower()
        if 'kreative' in font_name or 'square' in font_name:
            # KreativeSquare: 1.0× (no scaling) - font already matches tile size
            h_scale = h_scale if h_scale is not None else 1.0
            v_scale = v_scale if v_scale is not None else 1.0
        else:
            # Other proportional fonts: may need scaling adjustment
            h_scale = h_scale if h_scale is not None else 1.7
            v_scale = v_scale if v_scale is not None else 1.0

    # THIS IS THE KEY: Request LARGER size so actual glyphs fill tiles
    render_width = int(glyph_width * h_scale)
    render_height = int(glyph_height * v_scale)
    face.set_pixel_sizes(render_width, render_height)

    # Create empty tileset
    tileset = tcod.tileset.Tileset(glyph_width, glyph_height)

    # Default character set: printable ASCII + box drawing + common symbols
    if chars is None:
        chars = (
            # Printable ASCII (32-126)
            "".join(chr(i) for i in range(32, 127)) +
            # Box drawing - double line (used everywhere: walls, UI, dialogues)
            "║═╔╗╚╝╠╣╦╩╬" +
            # Box drawing - heavy line
            "┃━┏┓┗┛┣┫┳┻╋" +
            # Card suits (used for special nodes)
            "♠♥♦♣" +
            # Game symbols
            "☺•○■§♫◘◙" +
            # Arrow symbols (used in menus and UI)
            "↑↓←→↕↔"
        )

    # Load each character
    for char in chars:
        codepoint = ord(char)

        try:
            # Load glyph for this character
            face.load_char(char, freetype.FT_LOAD_RENDER)

            # Get bitmap
            bitmap = face.glyph.bitmap

            # Create output image (RGBA format for tcod)
            output = np.zeros((glyph_height, glyph_width, 4), dtype=np.uint8)

            # Position glyphs using proper baseline alignment
            if bitmap.width > 0 and bitmap.rows > 0:
                glyph_data = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, bitmap.width)

                # Calculate baseline position using font metrics
                # FreeType metrics: ascender (above baseline), descender (below baseline), height (total)
                baseline_y = int(glyph_height * face.ascender / face.height)

                # Position glyph relative to baseline
                left = face.glyph.bitmap_left
                top = baseline_y - face.glyph.bitmap_top

                # Calculate valid region (handle oversized glyphs)
                src_top = max(0, -top)
                src_left = max(0, -left)
                src_bottom = min(bitmap.rows, glyph_height - top)
                src_right = min(bitmap.width, glyph_width - left)

                dst_top = max(0, top)
                dst_left = max(0, left)
                dst_bottom = min(glyph_height, top + bitmap.rows)
                dst_right = min(glyph_width, left + bitmap.width)

                # Copy glyph into output (white glyph, alpha from FreeType)
                if dst_bottom > dst_top and dst_right > dst_left:
                    output[dst_top:dst_bottom, dst_left:dst_right, :3] = 255  # RGB = white
                    output[dst_top:dst_bottom, dst_left:dst_right, 3] = glyph_data[src_top:src_bottom, src_left:src_right]

            # Set tile in tileset
            tileset.set_tile(codepoint, output)

        except Exception as e:
            # Skip characters that can't be rendered (suppress warnings to avoid Unicode errors)
            pass

    return tileset


if __name__ == "__main__":
    # Test the font loader
    import ctypes

    # Set DPI awareness first
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        print("[OK] DPI awareness enabled")
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            print("[OK] DPI awareness enabled (fallback)")
        except Exception:
            print("[WARN] Could not set DPI awareness")

    import tcod

    print("=" * 70)
    print("FREETYPE FONT LOADER TEST")
    print("=" * 70)

    # Load KreativeSquare font (same as main game)
    print("\nLoading KreativeSquare with 64x64 glyph size...")
    tileset = load_truetype_font_custom("KreativeSquare.ttf", 64, 64)

    print(f"Tileset created: {tileset.tile_width}x{tileset.tile_height}")

    # Create test window
    console_width = 10
    console_height = 6
    pixel_width = console_width * tileset.tile_width
    pixel_height = console_height * tileset.tile_height

    print(f"Expected window: {pixel_width}x{pixel_height}px")

    with tcod.context.new(
        columns=console_width,
        rows=console_height,
        tileset=tileset,
        title="FreeType Test: KreativeSquare 64x64",
        vsync=True,
        width=pixel_width,
        height=pixel_height
    ) as context:
        console = tcod.console.Console(console_width, console_height)

        if hasattr(context, 'sdl_window'):
            actual = context.sdl_window.size
            print(f"Actual window: {actual[0]}x{actual[1]}px")

        print("\nLOOK AT THE WINDOW!")
        print("Glyphs should fill tiles completely with no gaps.")
        print("Test box-drawing characters (║═╔╗) and descenders (g, y, p, q, j).")
        print("Press any key to exit...")

        while True:
            console.clear()
            console.print(0, 0, "0123456789", fg=(255, 255, 255))
            console.print(0, 1, "Typography", fg=(255, 255, 255))
            console.print(0, 2, "WALLS ║═╔╗", fg=(0, 255, 255))
            console.print(0, 3, "gyp qj fox", fg=(255, 255, 0))
            console.print(0, 4, "AAAAAAAAAA", fg=(255, 255, 255))
            console.print(0, 5, "0123456789", fg=(255, 255, 255))

            context.present(console)

            for event in tcod.event.wait():
                if event.type == "QUIT":
                    print("\nTest done.")
                    raise SystemExit()
                elif event.type == "KEYDOWN":
                    print("\nTest done.")
                    raise SystemExit()
