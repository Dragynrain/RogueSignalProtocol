"""
Visualize what's actually being written to tileset tiles.
Shows the exact bitmap data for each character.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Force reload of font_loader_freetype module
import importlib
if 'font_loader_freetype' in sys.modules:
    del sys.modules['font_loader_freetype']

import numpy as np
import freetype

def visualize_glyph_in_tile(font_path: str, glyph_width: int, glyph_height: int,
                            h_scale: float = 1.0, v_scale: float = 1.0):
    """Show exactly what gets written to each tile."""

    face = freetype.Face(font_path)
    render_width = int(glyph_width * h_scale)
    render_height = int(glyph_height * v_scale)
    face.set_pixel_sizes(render_width, render_height)

    print(f"\n{'='*70}")
    print(f"TILESET VISUALIZATION: {font_path}")
    print(f"Tile size: {glyph_width}x{glyph_height}")
    print(f"Render size: {render_width}x{render_height} (scale: {h_scale}x, {v_scale}x)")
    print(f"{'='*70}")

    test_chars = [
        ('A', 0x0041, "Letter A (baseline test)"),
        ('─', 0x2500, "Single horizontal"),
        ('│', 0x2502, "Single vertical"),
        ('┌', 0x250C, "Single corner"),
        ('═', 0x2550, "Double horizontal"),
        ('║', 0x2551, "Double vertical"),
        ('╔', 0x2554, "Double corner"),
        ('━', 0x2501, "Heavy horizontal"),
        ('┃', 0x2503, "Heavy vertical"),
        ('┏', 0x250F, "Heavy corner"),
    ]

    for char, codepoint, desc in test_chars:
        print(f"\n{'-'*70}")
        print(f"{char} U+{codepoint:04X} - {desc}")
        print(f"{'-'*70}")

        try:
            face.load_char(char, freetype.FT_LOAD_RENDER)
            bitmap = face.glyph.bitmap

            if bitmap.width == 0 or bitmap.rows == 0:
                print("  >> EMPTY BITMAP (no pixels)")
                continue

            # Create tile exactly as the font loader does
            output = np.zeros((glyph_height, glyph_width, 4), dtype=np.uint8)
            glyph_data = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, bitmap.width)

            # Horizontal: center
            left = (glyph_width - bitmap.width) // 2

            # Vertical: use the EXACT formula from font_loader_freetype.py
            if 0x2500 <= codepoint <= 0x259F:  # Box drawing
                # Use baseline for box-drawing (respects font designer's alignment)
                baseline_position = int(glyph_height * 0.75)
                top = baseline_position - face.glyph.bitmap_top
                positioning = f"baseline at 75% (top={top})"
            else:
                # Baseline alignment for text
                baseline_position = int(glyph_height * 0.75)
                top = baseline_position - face.glyph.bitmap_top
                positioning = f"baseline at 75% (top={top})"

            print(f"  Bitmap: {bitmap.width}x{bitmap.rows} pixels")
            print(f"  bearingY: {face.glyph.metrics.horiBearingY / 64:.1f}px, bitmap_top: {face.glyph.bitmap_top}")
            print(f"  Positioning: {positioning}")
            print(f"  Position in tile: left={left}, top={top}")

            # Calculate clipping
            src_top = max(0, -top)
            src_left = max(0, -left)
            src_bottom = min(bitmap.rows, glyph_height - top)
            src_right = min(bitmap.width, glyph_width - left)

            dst_top = max(0, top)
            dst_left = max(0, left)
            dst_bottom = min(glyph_height, top + bitmap.rows)
            dst_right = min(glyph_width, left + bitmap.width)

            print(f"  Source region: [{src_top}:{src_bottom}, {src_left}:{src_right}]")
            print(f"  Dest region: [{dst_top}:{dst_bottom}, {dst_left}:{dst_right}]")

            # Copy data
            if dst_bottom > dst_top and dst_right > dst_left:
                output[dst_top:dst_bottom, dst_left:dst_right, :3] = 255
                output[dst_top:dst_bottom, dst_left:dst_right, 3] = glyph_data[src_top:src_bottom, src_left:src_right]

                # Count pixels written
                alpha_channel = output[:, :, 3]
                non_zero = np.count_nonzero(alpha_channel)
                print(f"  Pixels written to tile: {non_zero}/{glyph_width * glyph_height}")

                # ASCII art visualization of the tile
                print(f"\n  Tile visualization ({glyph_width}x{glyph_height}):")

                # Show a scaled-down version if tile is large
                scale = 1
                if glyph_width > 40:
                    scale = glyph_width // 40

                print("  " + "+" + "-" * (glyph_width // scale) + "+")
                for y in range(0, glyph_height, scale):
                    row = "  |"
                    for x in range(0, glyph_width, scale):
                        # Sample alpha at this position
                        alpha = alpha_channel[y, x]
                        if alpha > 200:
                            row += "█"
                        elif alpha > 150:
                            row += "▓"
                        elif alpha > 100:
                            row += "▒"
                        elif alpha > 50:
                            row += "░"
                        else:
                            row += " "
                    row += "|"
                    print(row)
                print("  " + "+" + "-" * (glyph_width // scale) + "+")
            else:
                print(f"  >> CLIPPED OUT (dst region invalid)")

        except Exception as e:
            print(f"  >> ERROR: {e}")


if __name__ == "__main__":
    # Test at the current game settings: 64x64, 1.0x scale
    visualize_glyph_in_tile("KreativeSquare.ttf", 64, 64, 1.0, 1.0)

    print("\n" + "="*70)
    print("COMPARISON: CascadiaCode (known working)")
    print("="*70)
    # CascadiaCode uses 1.7x horizontal, 1.0x vertical
    visualize_glyph_in_tile("CascadiaCode-Regular.ttf", 64, 64, 1.7, 1.0)
