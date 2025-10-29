"""
Inspect the internal metrics of font files to understand their true aspect ratios.
"""
import freetype

def inspect_font_metrics(font_path: str):
    """Show detailed metrics for a font file."""
    face = freetype.Face(font_path)

    print(f"\n{'='*70}")
    print(f"FONT METRICS: {font_path}")
    print(f"{'='*70}")

    # Font-level metrics
    print(f"\n[Font-Level Metrics]")
    print(f"  Family: {face.family_name.decode('utf-8')}")
    print(f"  Style: {face.style_name.decode('utf-8')}")
    print(f"  Units per EM: {face.units_per_EM}")
    print(f"  Ascender: {face.ascender}")
    print(f"  Descender: {face.descender}")
    print(f"  Height (line spacing): {face.height}")
    print(f"  Max advance width: {face.max_advance_width}")
    print(f"  Max advance height: {face.max_advance_height}")

    # Calculate "natural" aspect ratio from font metrics
    natural_width = face.max_advance_width
    natural_height = face.height
    aspect_ratio = natural_width / natural_height if natural_height else 0

    print(f"\n[Calculated Ratios]")
    print(f"  Max advance width / Height: {natural_width}/{natural_height} = {aspect_ratio:.3f}")

    # Test at a specific pixel size
    test_size = 64
    face.set_pixel_sizes(test_size, test_size)

    print(f"\n[At {test_size}x{test_size} pixel size]")
    print(f"  Size metrics available: {face.size is not None}")
    if face.size:
        print(f"  X scale: {face.size.x_scale}")
        print(f"  Y scale: {face.size.y_scale}")
        print(f"  Ascender: {face.size.ascender / 64:.1f}px")  # Divide by 64 (26.6 format)
        print(f"  Descender: {face.size.descender / 64:.1f}px")
        print(f"  Height: {face.size.height / 64:.1f}px")
        print(f"  Max advance: {face.size.max_advance / 64:.1f}px")

    # Sample some common glyphs (ASCII only to avoid encoding issues)
    print(f"\n[Sample Glyph Metrics at {test_size}x{test_size}px]")
    test_chars = ['A', 'M', 'W', 'i', 'g']

    for char in test_chars:
        try:
            face.load_char(char, freetype.FT_LOAD_DEFAULT)
            metrics = face.glyph.metrics

            # Convert from 26.6 fixed-point format to pixels
            width = metrics.width / 64
            height = metrics.height / 64
            horiBearingX = metrics.horiBearingX / 64
            horiBearingY = metrics.horiBearingY / 64
            horiAdvance = metrics.horiAdvance / 64

            print(f"  {char}: width={width:.1f}px, height={height:.1f}px, advance={horiAdvance:.1f}px")

        except Exception as e:
            print(f"  {char}: (not available)")

    print()


if __name__ == "__main__":
    # Inspect both fonts
    inspect_font_metrics("KreativeSquare.ttf")
    inspect_font_metrics("CascadiaCode-Regular.ttf")
