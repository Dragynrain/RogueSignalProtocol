"""
Unicode character constants for game rendering.

Replaces CP437 index-based character access with direct Unicode.
All characters verified to exist in CascadiaCode font.
"""


class GameGlyphs:
    """Unicode characters for game rendering."""

    # Player and entities
    PLAYER = '☺'  # U+263A - White smiling face (☻ U+263B not in CascadiaCode)

    # Nodes (consumable map pickups - hollow suits)
    CPU_NODE = '♡'          # U+2661 - Hollow heart (CPU restore)
    COOLING_NODE = '♢'      # U+2662 - Hollow diamond (cooling restore)
    GHOST_NODE = '♤'        # U+2664 - Hollow spade (ghost mode pickup)

    # Permanent upgrades (permanent stat boosts - filled suits + grid)
    CPU_UPGRADE = '♥'       # U+2665 - Filled heart (permanent CPU boost)
    COOLING_UPGRADE = '♦'   # U+2666 - Filled diamond (permanent heat capacity)
    RAM_UPGRADE = '▣'       # U+25A3 - Square with fill (permanent RAM boost)

    # Legacy aliases (for backward compatibility with status effect overlays)
    CPU_OVERLOAD = CPU_UPGRADE    # ♥ - Also used as status overlay
    COOLING = COOLING_UPGRADE     # ♦ - Also used as status overlay
    GHOST_MODE = GHOST_NODE       # ♤ - Also used as status overlay

    # Terrain
    FLOOR_EXPLORED = '•'  # U+2022 - Bullet (visible floor tile)
    BLIND_SPOT = '♠'      # U+2660 - Filled spade (obscured vision area)

    # UI indicators
    TARGETING = '◎'     # U+25CE - Bullseye (targeting/autowalk destination)
    CIRCLE_DOT = '◙'    # U+25D9 - Inverse circle (fallback: '◉' U+25C9 if needed)
    EXPLOIT = '⚠'       # U+26A0 - Warning sign (exploits on map)

    # Items and special
    STORY_FRAGMENT = '♫'  # U+266B - Musical notes
    CODE_HACK = '❀'       # U+2740 - White florette (code fragments/patches)
    PERMANENT_UPGRADE = '★'  # U+2605 - Filled star (permanent upgrades)

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
    WALL_ISOLATED = '□'         # U+25A1 - Hollow square (matches double-line walls better)

    # Dialogue boxes use same characters (semantic alias)
    DIALOGUE_VERTICAL = WALL_VERTICAL
    DIALOGUE_HORIZONTAL = WALL_HORIZONTAL
    DIALOGUE_TOP_LEFT = WALL_TOP_LEFT
    DIALOGUE_TOP_RIGHT = WALL_TOP_RIGHT
    DIALOGUE_BOTTOM_LEFT = WALL_BOTTOM_LEFT
    DIALOGUE_BOTTOM_RIGHT = WALL_BOTTOM_RIGHT
