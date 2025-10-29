"""Test TCOD's built-in TTF loader at various sizes"""
import tcod

sizes = [16, 24, 32, 48, 64, 96, 128]

for size in sizes:
    try:
        tileset = tcod.tileset.load_truetype_font("CascadiaCode-Regular.ttf", size, size)
        print(f"Size {size:3d}x{size:3d} -> tileset reports {tileset.tile_width}x{tileset.tile_height}")
    except Exception as e:
        print(f"Size {size:3d}x{size:3d} -> ERROR: {e}")
