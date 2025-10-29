"""
Debug script to see what FreeType is actually generating.
"""
import freetype
import numpy as np

# Load font
face = freetype.Face("CascadiaCode-Regular.ttf")

# Test different sizes
for requested_size in [64, 72, 80, 88, 96, 104, 112, 128]:
    face.set_pixel_sizes(requested_size, requested_size)

    print(f"\n{'='*60}")
    print(f"REQUESTED SIZE: {requested_size}×{requested_size}")
    print(f"{'='*60}")

    # Test a few characters
    test_chars = [
        ('A', 'Letter A'),
        ('g', 'Letter g (with descender)'),
        ('─', 'Horizontal line (box-drawing)'),
        ('│', 'Vertical line (box-drawing)'),
        ('┌', 'Top-left corner (box-drawing)'),
    ]

    for char, desc in test_chars:
        face.load_char(char, freetype.FT_LOAD_RENDER)
        bitmap = face.glyph.bitmap

        print(f"\n  {desc} ('{char}'):")
        print(f"    Actual bitmap size: {bitmap.width}×{bitmap.rows}")
        print(f"    bitmap_left: {face.glyph.bitmap_left}")
        print(f"    bitmap_top: {face.glyph.bitmap_top}")
        print(f"    Coverage: {bitmap.width/requested_size*100:.1f}% horizontal, {bitmap.rows/requested_size*100:.1f}% vertical")
