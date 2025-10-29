"""Quick test of multiple fonts using TCOD's built-in loader"""
import ctypes

# TEST: Disable DPI awareness to see if that fixes sizing
# try:
#     ctypes.windll.shcore.SetProcessDpiAwareness(2)
# except:
#     try:
#         ctypes.windll.user32.SetProcessDPIAware()
#     except:
#         pass

import tcod

# Test different fonts at various sizes (window will be console*size pixels)
# Use smaller console to fit large tiles on screen
fonts_to_test = [
    ("CascadiaCode-Regular.ttf", 48, "CascadiaCode 48x48", 40, 25),  # Window: 1920x1200
    ("CascadiaCode-Regular.ttf", 64, "CascadiaCode 64x64", 30, 20),  # Window: 1920x1280
    ("KreativeSquare.ttf", 64, "KreativeSquare 64x64", 30, 20),      # Window: 1920x1280
]

for font_path, size, name, cols, rows in fonts_to_test:
    print(f"\n{'='*70}")
    print(f"Testing: {name} ({cols}x{rows} console)")
    print('='*70)

    try:
        # Use TCOD's built-in loader - no custom code!
        tileset = tcod.tileset.load_truetype_font(font_path, size, size)
        print(f"Loaded: {tileset.tile_width}x{tileset.tile_height}")

        # Calculate window size: console grid * tile size
        window_width = cols * size
        window_height = rows * size
        print(f"Window: {window_width}x{window_height}")

        with tcod.context.new(
            columns=cols,
            rows=rows,
            tileset=tileset,
            title=f"Font Test: {name}",
            width=window_width,
            height=window_height,
            vsync=True,
        ) as context:
            console = tcod.console.Console(cols, rows)

            print("Window open - press any key to test next font")

            while True:
                console.clear()

                console.print(2, 1, name, fg=(0, 255, 255))

                y = 4
                console.print(2, y, "Single: ┌───┬───┐", fg=(0, 255, 0))
                console.print(2, y+1, "        │   │   │", fg=(0, 255, 0))
                console.print(2, y+2, "        └───┴───┘", fg=(0, 255, 0))

                y += 4
                console.print(2, y, "Double: ╔═══╦═══╗", fg=(0, 255, 255))
                console.print(2, y+1, "        ║   ║   ║", fg=(0, 255, 255))
                console.print(2, y+2, "        ╚═══╩═══╝", fg=(0, 255, 255))

                y += 4
                console.print(2, y, "Heavy:  ┏━━━┳━━━┓", fg=(255, 0, 255))
                console.print(2, y+1, "        ┃   ┃   ┃", fg=(255, 0, 255))
                console.print(2, y+2, "        ┗━━━┻━━━┛", fg=(255, 0, 255))

                y += 4
                console.print(2, y, "Text: The quick brown fox", fg=(200, 200, 200))
                console.print(2, y+1, "Suits: ♠ ♥ ♦ ♣", fg=(200, 200, 200))

                console.print(2, rows - 2, "Press any key for next font", fg=(255, 255, 0))

                context.present(console)

                for event in tcod.event.wait():
                    if event.type == "QUIT":
                        print("Exiting...")
                        raise SystemExit()
                    elif event.type == "KEYDOWN":
                        raise StopIteration()

    except StopIteration:
        print(f"Moving to next font...")
        continue
    except Exception as e:
        print(f"Error loading {name}: {e}")
        continue

print("\n\nAll fonts tested!")
