"""
Unicode character constants for game rendering.

Replaces CP437 index-based character access with direct Unicode.
All characters verified to exist in CascadiaCode font.
"""


class GameGlyphs:
    """Unicode characters for game rendering."""

    # Player and entities
    PLAYER = '☺'  # U+263A - White smiling face (☻ U+263B not in CascadiaCode)

    # Status effects (overlays)
    COOLING = '♦'       # U+2666 - Diamond
    CPU_OVERLOAD = '♥'  # U+2665 - Heart
    GHOST_MODE = '♠'    # U+2660 - Spade

    # Terrain
    FLOOR_EXPLORED = '•'  # U+2022 - Bullet
    BLIND_SPOT = '◘'      # U+25D8 - Inverse bullet (fallback: '●' U+25CF if needed)

    # UI indicators
    TARGETING = '○'     # U+25CB - Circle
    CIRCLE_DOT = '◙'    # U+25D9 - Inverse circle (fallback: '◉' U+25C9 if needed)

    # Items and special
    STORY_FRAGMENT = '♫'  # U+266B - Musical notes
    SECTION = '§'         # U+00A7 - Section sign

    # Walls - Double-line (used everywhere: gameplay, menus, dialogues, frames)
    WALL_VERTICAL = '║'         # U+2551
    WALL_HORIZONTAL = '═'       # U+2550
    WALL_TOP_LEFT = '╔'         # U+2554
    WALL_TOP_RIGHT = '╗'        # U+2557
    WALL_BOTTOM_LEFT = '╚'      # U+255A
    WALL_BOTTOM_RIGHT = '╝'     # U+255D
    WALL_T_LEFT = '╣'           # U+2563
    WALL_T_RIGHT = '╠'          # U+2560
    WALL_T_UP = '╩'             # U+2569
    WALL_T_DOWN = '╦'           # U+2566
    WALL_CROSS = '╬'            # U+256C
    WALL_ISOLATED = '■'         # U+25A0 - Small square

    # Dialogue boxes use same characters (semantic alias)
    DIALOGUE_VERTICAL = WALL_VERTICAL
    DIALOGUE_HORIZONTAL = WALL_HORIZONTAL
    DIALOGUE_TOP_LEFT = WALL_TOP_LEFT
    DIALOGUE_TOP_RIGHT = WALL_TOP_RIGHT
    DIALOGUE_BOTTOM_LEFT = WALL_BOTTOM_LEFT
    DIALOGUE_BOTTOM_RIGHT = WALL_BOTTOM_RIGHT
