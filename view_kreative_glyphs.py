"""
Visual Glyph Reference Viewer for KreativeSquare Font

Displays all available glyphs at 64x64 (as they appear in-game) with Unicode codes.
Navigate with arrow keys, press ESC to exit.
"""
import freetype
import tcod
import ctypes

# Set DPI awareness first
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass

from font_loader_freetype import load_truetype_font_custom

# Unicode ranges to check
UNICODE_RANGES = [
    (0x0020, 0x007F, "Basic Latin (ASCII)"),
    (0x00A0, 0x00FF, "Latin-1 Supplement"),
    (0x2500, 0x257F, "Box Drawing"),
    (0x2580, 0x259F, "Block Elements"),
    (0x25A0, 0x25FF, "Geometric Shapes"),
    (0x2600, 0x26FF, "Miscellaneous Symbols"),
    (0x2700, 0x27BF, "Dingbats"),
]

def get_available_glyphs():
    """Scan KreativeSquare font and return all available glyphs."""
    face = freetype.Face("KreativeSquare.ttf")
    available = []

    for start, end, range_name in UNICODE_RANGES:
        for codepoint in range(start, end + 1):
            char_index = face.get_char_index(codepoint)
            if char_index != 0:  # Glyph exists
                try:
                    char = chr(codepoint)
                    available.append((codepoint, char, range_name))
                except:
                    pass

    return available

def main():
    print("=" * 80)
    print("KREATIVE SQUARE GLYPH VIEWER")
    print("=" * 80)
    print("\nScanning font for available glyphs...")

    glyphs = get_available_glyphs()
    print(f"Found {len(glyphs)} glyphs!\n")

    # Load font at 64x64 (as in-game)
    print("Loading KreativeSquare at 64x64...")
    tileset = load_truetype_font_custom("KreativeSquare.ttf", 64, 64)

    # Window setup: show 16 glyphs per row, 12 rows visible at a time
    glyphs_per_row = 16
    rows_visible = 12
    console_width = glyphs_per_row * 6  # Each glyph takes 6 columns (glyph + code)
    console_height = rows_visible + 2   # +2 for header and footer

    # Calculate window size
    pixel_width = console_width * tileset.tile_width
    pixel_height = console_height * tileset.tile_height

    print(f"Window: {pixel_width}x{pixel_height}px")
    print("\nControls:")
    print("  UP/DOWN: Scroll through glyphs")
    print("  ESC/Q: Exit")
    print("\nStarting viewer...")

    with tcod.context.new(
        columns=console_width,
        rows=console_height,
        tileset=tileset,
        title="KreativeSquare Glyph Reference (64x64)",
        vsync=True,
        width=pixel_width,
        height=pixel_height
    ) as context:
        console = tcod.console.Console(console_width, console_height)

        scroll_offset = 0
        total_rows = (len(glyphs) + glyphs_per_row - 1) // glyphs_per_row
        max_scroll = max(0, total_rows - rows_visible)

        running = True
        while running:
            console.clear()

            # Header
            title = f"KreativeSquare Glyphs ({len(glyphs)} total) - Row {scroll_offset + 1}/{total_rows}"
            console.print(0, 0, title, fg=(255, 255, 0))

            # Display glyphs in grid
            for idx, (codepoint, char, range_name) in enumerate(glyphs):
                row = idx // glyphs_per_row
                col = idx % glyphs_per_row

                # Apply scroll offset
                display_row = row - scroll_offset
                if display_row < 0 or display_row >= rows_visible:
                    continue

                # Position on console (each glyph gets 6 chars: "X U+" with spacing)
                x = col * 6
                y = display_row + 1  # +1 for header

                # Display glyph
                console.print(x, y, char, fg=(255, 255, 255))

                # Display unicode code (compact format)
                code_text = f"{codepoint:04X}"
                console.print(x + 2, y, code_text, fg=(128, 128, 255))

            # Footer with navigation hints
            footer = f"UP/DOWN: Scroll | ESC: Exit | Scroll: {scroll_offset}/{max_scroll}"
            console.print(0, console_height - 1, footer, fg=(128, 255, 128))

            context.present(console)

            # Event handling
            for event in tcod.event.wait():
                if event.type == "QUIT":
                    running = False
                elif event.type == "KEYDOWN":
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.q):
                        running = False
                    elif event.sym == tcod.event.KeySym.UP:
                        scroll_offset = max(0, scroll_offset - 1)
                    elif event.sym == tcod.event.KeySym.DOWN:
                        scroll_offset = min(max_scroll, scroll_offset + 1)
                    elif event.sym == tcod.event.KeySym.PAGEUP:
                        scroll_offset = max(0, scroll_offset - rows_visible)
                    elif event.sym == tcod.event.KeySym.PAGEDOWN:
                        scroll_offset = min(max_scroll, scroll_offset + rows_visible)
                    elif event.sym == tcod.event.KeySym.HOME:
                        scroll_offset = 0
                    elif event.sym == tcod.event.KeySym.END:
                        scroll_offset = max_scroll

    print("\nViewer closed.")

if __name__ == "__main__":
    main()
