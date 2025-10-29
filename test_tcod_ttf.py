import ctypes

# CRITICAL: Set DPI awareness BEFORE importing tcod
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Fallback for older Windows
    except Exception:
        pass  # If both fail, continue anyway

import tcod

# Define the console dimensions
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

# Define font parameters
FONT_FILE = "cascadia/ttf/static/CascadiaMono-Regular.ttf"
FONT_SIZE = 96  # Font size in pixels (compensate for 200% DPI)

# Load the TrueType font into a Tileset
try:
    tileset = tcod.tileset.load_truetype_font(
        FONT_FILE,
        tile_width=FONT_SIZE,
        tile_height=FONT_SIZE,
    )
except tcod.libtcod.TCODError as e:
    # Handles font loading errors, e.g., if the file is not found
    print(f"Failed to load font '{FONT_FILE}': {e}")
    exit()

# Set the loaded tileset as the default
tcod.tileset.set_default(tileset)

# Create a context and a root console
with tcod.context.new(
    columns=SCREEN_WIDTH,
    rows=SCREEN_HEIGHT,
    title="TrueType Font Example",
    vsync=True,
) as context:
    root_console = tcod.console.Console(SCREEN_WIDTH, SCREEN_HEIGHT, order="F")

    # Main game loop
    while True:
        # Clear the console and print a message
        root_console.clear()
        root_console.print(
            x=1,
            y=1,
            string="Hello, libtcod with a TrueType font!",
        )
        root_console.print(
            x=1,
            y=3,
            string="Typography test with descenders: gyp qj",
        )
        root_console.print(
            x=1,
            y=5,
            string="Box drawing: ││┌┐└┘",
        )

        # Present the console and handle events
        context.present(root_console)

        # Check for window close event
        for event in tcod.event.wait():
            if event.type == "QUIT":
                raise SystemExit()
