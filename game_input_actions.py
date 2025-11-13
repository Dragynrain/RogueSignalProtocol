"""
game_input_actions.py - Input Action Abstraction

Defines abstract actions that can be triggered by keyboard, mouse, or gamepad inputs.
Provides context-sensitive input handling where the same physical input can trigger
different actions depending on game state.

This abstraction layer enables:
- Custom key/button remapping
- Multi-input support (keyboard + gamepad simultaneously)
- Context-aware input handling (A button = wait in gameplay, confirm in menus)
"""

from enum import Enum, auto


class InputAction(Enum):
    """
    Abstract game actions that can be triggered by any input device.

    These represent what the player wants to DO, not which button they pressed.
    """

    # ============================================================================
    # MOVEMENT (8-directional)
    # ============================================================================
    MOVE_NORTH = auto()
    MOVE_SOUTH = auto()
    MOVE_EAST = auto()
    MOVE_WEST = auto()
    MOVE_NORTHEAST = auto()
    MOVE_NORTHWEST = auto()
    MOVE_SOUTHEAST = auto()
    MOVE_SOUTHWEST = auto()

    # ============================================================================
    # CORE ACTIONS
    # ============================================================================
    WAIT = auto()  # Pass turn / rest
    CONFIRM = auto()  # Generic confirm (menus, dialogues, targeting)
    CANCEL = auto()  # Generic cancel (close menus, exit modes)

    # ============================================================================
    # EXPLOITS
    # ============================================================================
    EXPLOIT_SLOT_1 = auto()
    EXPLOIT_SLOT_2 = auto()
    EXPLOIT_SLOT_3 = auto()
    EXPLOIT_SLOT_4 = auto()
    EXPLOIT_SLOT_5 = auto()

    # NEW: Gamepad-style exploit controls (also usable with keyboard)
    EXPLOIT_CYCLE_NEXT = auto()  # Cycle to next exploit (RB on gamepad, ] on keyboard)
    EXPLOIT_CYCLE_PREV = auto()  # Cycle to previous exploit (LB on gamepad, [ on keyboard)
    EXPLOIT_EXECUTE = auto()  # Execute currently selected exploit (RT on gamepad)

    # ============================================================================
    # UI TOGGLES
    # ============================================================================
    TOGGLE_INVENTORY = auto()
    TOGGLE_LOOK_MODE = auto()
    TOGGLE_HELP = auto()
    TOGGLE_LORE_VIEWER = auto()
    TOGGLE_ACHIEVEMENTS = auto()

    # ============================================================================
    # NAVIGATION (for menus, scrolling, etc.)
    # ============================================================================
    NAVIGATE_UP = auto()
    NAVIGATE_DOWN = auto()
    NAVIGATE_LEFT = auto()
    NAVIGATE_RIGHT = auto()
    NAVIGATE_PAGE_UP = auto()
    NAVIGATE_PAGE_DOWN = auto()

    # ============================================================================
    # SPECIAL
    # ============================================================================
    DEBUG_EXPORT = auto()  # Shift+F12 - export debug package


class InputContext(Enum):
    """
    Game state contexts that determine how inputs are interpreted.

    Same physical input can trigger different actions in different contexts.
    For example: A button = WAIT in gameplay, CONFIRM in menus.

    Priority order (highest to lowest):
    1. ACHIEVEMENT_POPUP
    2. DIALOGUE
    3. GAME_OVER
    4. Modal screens (INVENTORY, LOOK_MODE, TARGETING, HELP, LORE, ACHIEVEMENTS)
    5. GAMEPLAY
    6. MAIN_MENU, SETTINGS_MENU, etc.
    """

    # In-game contexts (priority order matches game_input.py:115-182)
    ACHIEVEMENT_POPUP = auto()  # Highest priority - dismisses on any input
    DIALOGUE = auto()  # Active dialogue overlay
    GAME_OVER = auto()  # Death/victory screen

    # Modal screens
    INVENTORY = auto()
    LOOK_MODE = auto()
    TARGETING = auto()
    HELP = auto()
    LORE_VIEWER = auto()
    ACHIEVEMENTS_SCREEN = auto()

    # Normal gameplay
    GAMEPLAY = auto()

    # Main menu contexts
    MAIN_MENU = auto()
    SETTINGS_MENU = auto()
    CONTROLS_MENU = auto()
    ABOUT_MENU = auto()
    GRAPHICS_PREVIEW = auto()
