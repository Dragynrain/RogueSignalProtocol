"""
Visual Glyph Reference Viewer for KreativeSquare Font

Displays all available glyphs at 64x64 (as they appear in-game) with Unicode codes.
Scans comprehensive Unicode ranges to show everything the font supports.

Controls:
  UP/DOWN - Scroll one row
  PgUp/PgDn - Scroll one page
  Home/End - Jump to start/end
  ESC/Q - Exit
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import game modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import freetype
import tcod

# Set DPI awareness first (cross-platform)
from game_platform import set_dpi_awareness

set_dpi_awareness()

from font_loader_freetype import load_truetype_font_custom

# Unicode ranges to check (only ranges where KreativeSquare has glyphs)
UNICODE_RANGES = [
    (0x0020, 0x007F, "Basic Latin (ASCII)"),
    (0x0080, 0x00FF, "Latin-1 Supplement"),
    (0x2190, 0x21FF, "Arrows"),
    (0x2500, 0x257F, "Box Drawing"),
    (0x2580, 0x259F, "Block Elements"),
    (0x25A0, 0x25FF, "Geometric Shapes"),
    (0x2600, 0x26FF, "Miscellaneous Symbols"),
    (0x2700, 0x27BF, "Dingbats"),
]


def get_available_glyphs():
    """Scan KreativeSquare font and return ONLY glyphs that actually exist (no blanks)."""
    face = freetype.Face("KreativeSquare.ttf")
    available = []

    print("\nScanning ranges:")
    for start, end, range_name in UNICODE_RANGES:
        count = 0
        for codepoint in range(start, end + 1):
            char_index = face.get_char_index(codepoint)
            if char_index != 0:  # Glyph exists
                try:
                    char = chr(codepoint)
                    available.append((codepoint, char, range_name))
                    count += 1
                except ValueError:
                    pass
        print(f"  {range_name:25} - {count:3} glyphs")

    return available


def main():
    print("=" * 80)
    print("KREATIVE SQUARE GLYPH VIEWER")
    print("=" * 80)
    print("\nScanning font for available glyphs...")

    glyphs = get_available_glyphs()
    print(f"\nFound {len(glyphs)} total glyphs!\n")

    # Extract all characters to load into tileset
    all_chars = "".join(char for codepoint, char, range_name in glyphs)

    # Load font at 64x64 with ALL available characters (not just the default set)
    print(f"Loading KreativeSquare at 64x64 with all {len(all_chars)} glyphs...")
    tileset = load_truetype_font_custom("KreativeSquare.ttf", 64, 64, chars=all_chars)

    # Window setup: 8 glyphs per row (fits 4K), 20 rows visible at a time
    glyphs_per_row = 8
    rows_visible = 20
    console_width = glyphs_per_row * 6  # Each glyph takes 6 columns (glyph + code)
    console_height = rows_visible + 2  # +2 for header and footer

    # Calculate window size
    pixel_width = console_width * tileset.tile_width
    pixel_height = console_height * tileset.tile_height

    print(f"Window: {pixel_width}x{pixel_height}px")
    print("\nControls:")
    print("  UP/DOWN: Scroll one row")
    print("  PgUp/PgDn: Scroll one page")
    print("  Home/End: Jump to start/end")
    print("  ESC/Q: Exit")
    print("\nStarting viewer...")

    with tcod.context.new(
        columns=console_width,
        rows=console_height,
        tileset=tileset,
        title="KreativeSquare Glyph Reference (64x64)",
        vsync=True,
        width=pixel_width,
        height=pixel_height,
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
                    if event.sym in (tcod.event.KeySym.ESCAPE, tcod.event.KeySym.Q):
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
