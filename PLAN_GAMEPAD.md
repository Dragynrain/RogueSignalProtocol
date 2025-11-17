# Gamepad Support + Custom Input Remapping - Implementation Plan

## Overview
Add comprehensive gamepad support to Rogue Signal Protocol with custom remapping for both keyboard and gamepad inputs. Uses "Option C" default mapping (shoulder buttons cycle exploits, trigger executes). Includes full remapping UI in Settings menu.

---

## Phase Summary

**Phase 1: Input Abstraction Infrastructure** (High complexity, foundational)
- Create action enum system and input mapping layer
- Minimal code changes, establishes architecture

**Phase 2: Gamepad Event Handling** (Medium complexity, depends on Phase 1)
- Add controller event processing, deadzone handling, device management
- Integrate with existing input routing

**Phase 3: Default Gamepad Bindings** (Low complexity, depends on Phase 2)
- Implement Option C mappings, context-sensitive bindings
- Fully playable with gamepad using defaults

**Phase 4: Custom Remapping UI - Keyboard** (High complexity, depends on Phase 1)
- Build remapping interface for keyboard controls
- Settings menu integration, conflict detection

**Phase 5: Custom Remapping UI - Gamepad** (Medium complexity, depends on Phases 3-4)
- Extend remapping UI for gamepad buttons/axes
- Complete remapping system for both input types

**Phase 6: Testing & Polish** (Medium complexity, depends on all phases)
- Edge case handling, documentation, help screen updates

---

## PHASE 1: Input Abstraction Infrastructure

### Goal
Create an abstraction layer between raw input events (KeySym, ControllerButton) and game actions without breaking existing code.

### Tasks

#### 1.1 Create Action Enum System
**New file:** `game_input_actions.py`

Define comprehensive action enum covering ALL interactions:
```python
from enum import Enum, auto

class InputAction(Enum):
    # Movement (8-directional)
    MOVE_NORTH = auto()
    MOVE_SOUTH = auto()
    MOVE_EAST = auto()
    MOVE_WEST = auto()
    MOVE_NORTHEAST = auto()
    MOVE_NORTHWEST = auto()
    MOVE_SOUTHEAST = auto()
    MOVE_SOUTHWEST = auto()

    # Core actions
    WAIT = auto()
    CONFIRM = auto()
    CANCEL = auto()

    # Exploits
    EXPLOIT_SLOT_1 = auto()
    EXPLOIT_SLOT_2 = auto()
    EXPLOIT_SLOT_3 = auto()
    EXPLOIT_SLOT_4 = auto()
    EXPLOIT_SLOT_5 = auto()

    # NEW: Gamepad-specific exploit controls
    EXPLOIT_CYCLE_NEXT = auto()
    EXPLOIT_CYCLE_PREV = auto()
    EXPLOIT_EXECUTE = auto()

    # UI toggles
    TOGGLE_INVENTORY = auto()
    TOGGLE_LOOK_MODE = auto()
    TOGGLE_HELP = auto()
    TOGGLE_LORE_VIEWER = auto()
    TOGGLE_ACHIEVEMENTS = auto()

    # Navigation
    NAVIGATE_UP = auto()
    NAVIGATE_DOWN = auto()
    NAVIGATE_LEFT = auto()
    NAVIGATE_RIGHT = auto()
    NAVIGATE_PAGE_UP = auto()
    NAVIGATE_PAGE_DOWN = auto()

    # Special
    DEBUG_EXPORT = auto()
```

Also define **InputContext** enum to handle context-sensitive bindings:
```python
class InputContext(Enum):
    GAMEPLAY = auto()
    INVENTORY = auto()
    LOOK_MODE = auto()
    TARGETING = auto()
    DIALOGUE = auto()
    MENU = auto()
    HELP = auto()
    # ... etc
```

#### 1.2 Create Input Mapping System
**New file:** `game_input_mappings.py`

Manages bidirectional mapping: `(event, context) -> action` and `action -> default_bindings`

```python
class InputMapper:
    def __init__(self):
        self._keyboard_map: dict[tuple[KeySym, InputContext], InputAction] = {}
        self._gamepad_button_map: dict[tuple[ControllerButton, InputContext], InputAction] = {}
        self._gamepad_axis_map: dict[ControllerAxis, AxisBinding] = {}
        self._custom_bindings: dict = {}  # Loaded from settings

    def get_action(self, event, context: InputContext) -> InputAction | None
    def set_custom_binding(self, action: InputAction, binding, context: InputContext)
    def load_custom_bindings(self, settings_data: dict)
    def save_custom_bindings(self) -> dict
    def get_conflicts(self, action: InputAction, binding) -> list[InputAction]
    def reset_to_defaults(self, input_type: str)  # "keyboard" or "gamepad"
```

**Default keyboard mappings:** Migrate from `InputMappings.MOVEMENT_MAP` (game_input.py:47-75)

**Default gamepad mappings (Option C):**
- Left Stick/D-Pad: Movement
- A: Confirm/Wait
- B: Cancel
- Y/X: Exploits 1-2 (direct)
- RB: Cycle exploit next
- LB: Cycle exploit prev
- RT: Execute currently selected exploit
- LT: Look mode
- Start: Inventory
- Select: Help

#### 1.3 Add Analog Stick Handling
**New file:** `game_input_analog.py`

Implement deadzone algorithms and analog-to-digital conversion:

```python
class AnalogStickHandler:
    def __init__(self, deadzone: float = 0.15, threshold: float = 0.5):
        self.deadzone = deadzone
        self.threshold = threshold
        self.last_move_turn = -1  # TURN-BASED: Track last turn that processed movement
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0

    def apply_scaled_radial_deadzone(x, y) -> tuple[float, float]
    def analog_to_8way(x, y) -> tuple[int, int]
    def can_move(current_turn: int) -> bool  # Turn-based check (not time-based!)
    def update_axis(axis: ControllerAxis, value: int)
    def get_movement_delta(current_turn: int) -> tuple[int, int] | None
```

**CRITICAL DESIGN DECISION - Turn-Based Movement:**

Rogue Signal Protocol is **turn-based**, not real-time. Therefore:
- ❌ **NO time-based cooldown** (`time.time()` - wrong for turn-based games)
- ✅ **YES turn-based gating** (track `game.turn_count`)

**Implementation:**
```python
def can_move(self, current_turn: int) -> bool:
    """
    Check if player can move this turn.

    Args:
        current_turn: Current game turn number from game.turn_count

    Returns:
        True if this is a new turn (movement allowed), False if same turn (prevent spam)
    """
    if current_turn > self.last_move_turn:
        self.last_move_turn = current_turn
        return True
    return False

def get_left_stick_movement(self, current_turn: int) -> tuple[int, int] | None:
    """Get stick movement for current turn."""
    dx, dy = self.analog_to_8way(self.left_x, self.left_y)
    if dx == 0 and dy == 0:
        return None
    if not self.can_move(current_turn):
        return None  # Already moved this turn
    return (dx, dy)
```

**Why This Works:**
1. Player holds stick → continuous ControllerAxis events fire
2. First event on turn N → `can_move(N)` returns True, player moves
3. Subsequent events on turn N → `can_move(N)` returns False, ignored
4. Turn increments (enemies move) → turn N+1 begins
5. Next event on turn N+1 → `can_move(N+1)` returns True, player moves again

**Result:** One movement per turn, just like keyboard. No double-moves, no spam, perfect turn-based behavior.

**Rationale:** Scaled radial deadzone for smooth feel, turn-based gating prevents movement spam from continuous axis events.

#### 1.4 Extend GameSettings for Input Bindings
**File:** `game_config.py` (GameSettings class)

Add new properties:
```python
self.custom_keyboard_bindings: dict = {}
self.custom_gamepad_bindings: dict = {}
self.gamepad_deadzone: float = 0.15
self.gamepad_enabled: bool = True
```

Update `save_settings()` and `load_settings()` to persist these (lines 135-153, 50-114).

### Deliverables
- 3 new files: `game_input_actions.py`, `game_input_mappings.py`, `game_input_analog.py`
- Modified: `game_config.py` (GameSettings)
- No changes to existing input handlers yet (backward compatible)

### Technical Considerations
- **Migration strategy:** Keep existing direct key checks working during transition
- **Conflict resolution:** Last-set-wins for custom bindings, warn user in UI
- **Context sensitivity:** Same button can do different things in different states (A = confirm in menus, wait in gameplay)

---

## PHASE 2: Gamepad Event Handling

### Goal
Detect and process gamepad events, route to abstraction layer, support hotplugging.

### Tasks

#### 2.1 Initialize SDL Joystick Subsystem
**File:** `game_loop.py` or main entry point

Add initialization before main loop:
```python
import tcod.sdl.joystick

tcod.sdl.joystick.init()
controllers: set[tcod.sdl.joystick.GameController] = set()

# Get initially connected controllers
for controller in tcod.sdl.joystick.get_controllers():
    controllers.add(controller)
    logging.info(f"Controller connected: {controller.name_}")
```

#### 2.2 Create Gamepad Input Handler
**New file:** `game_input_gamepad.py`

Handles low-level gamepad events:

```python
class GamepadInputHandler:
    def __init__(self, input_mapper: InputMapper, initial_controllers: set[GameController] = None):
        """
        Initialize gamepad input handler.

        Args:
            input_mapper: InputMapper instance for action lookup
            initial_controllers: Set of already-connected controllers from game loop init
        """
        self.controllers: set[GameController] = initial_controllers or set()
        self.input_mapper = input_mapper
        self.analog_handler = AnalogStickHandler()
        # NOTE: Exploit cycling state moved to game.selected_exploit_index (Phase 2.7)

    def handle_device_event(event: ControllerDevice)
    def handle_button_event(event: ControllerButton, context: InputContext) -> InputAction | None
    def handle_axis_event(event: ControllerAxis, context: InputContext) -> InputAction | None
```

**Device management:** Track add/remove events, use `discard()` not `remove()` (see TCOD research gotcha #1).

**Axis handling:**
- Left stick → Movement actions (via analog_to_8way)
- Right stick → Look mode cursor (context-sensitive)
- Triggers → Exploit execution, look mode activation

#### 2.3 Integrate with InputHandler Router
**File:** `game_input.py`

Add gamepad handler alongside existing handlers. **IMPORTANT:** Pass initial controllers from game loop initialization:

```python
class InputHandler:
    def __init__(self, game, renderer=None, controllers=None):
        # ... existing handlers
        self.input_mapper = InputMapper()
        self.gamepad_handler = GamepadInputHandler(self.input_mapper, controllers or set())

        # Load custom bindings for both keyboard and gamepad
        self.input_mapper.load_custom_bindings(
            game.settings.custom_keyboard_bindings,
            game.settings.custom_gamepad_bindings
        )
```

**Device Ownership Clarified:**
- `game_loop.py` initializes SDL joystick subsystem and gets initial controllers
- Initial controller set passed to `InputHandler.__init__(controllers=...)`
- `InputHandler` owns the controller set going forward
- `GamepadInputHandler` receives and manages this set (add/remove via device events)

Add event routing in main loop:
```python
def handle_event(self, event) -> bool:
    # Route gamepad events
    if isinstance(event, tcod.event.ControllerDevice):
        self.gamepad_handler.handle_device_event(event)
        return True
    elif isinstance(event, tcod.event.ControllerButton):
        action = self.gamepad_handler.handle_button_event(event, self._get_current_context())
        if action:
            return self._execute_action(action)
    elif isinstance(event, tcod.event.ControllerAxis):
        action = self.gamepad_handler.handle_axis_event(event)
        if action:
            return self._execute_action(action)

    # Existing keyboard/mouse handling
    elif isinstance(event, tcod.event.KeyDown):
        return self.handle_keydown(event)
    # ...
```

#### 2.4 Add Context Detection Method
**File:** `game_input.py` (add method to InputHandler)

Create method to determine current input context (referenced throughout Phase 2-6):
```python
def _get_current_context(self) -> InputContext:
    """
    Determine current game state context for input handling.

    Context determines which bindings are active (e.g., A button = wait in gameplay,
    confirm in menus). Mirrors existing priority logic in handle_event.

    Returns:
        Current InputContext enum value
    """
    # Priority order matches existing game_input.py:100-182 logic
    if hasattr(self.game, 'achievement_popup_manager') and \
       self.game.achievement_popup_manager.has_active_popup():
        return InputContext.ACHIEVEMENT_POPUP
    elif self.game.dialogue_state.is_active():
        return InputContext.DIALOGUE
    elif self.game.game_over or self.game.player.cpu <= 0:
        return InputContext.GAME_OVER
    elif self.game.show_inventory:
        return InputContext.INVENTORY
    elif self.game.look_mode:
        return InputContext.LOOK_MODE
    elif self.game.targeting_mode:
        return InputContext.TARGETING
    elif self.game.show_help:
        return InputContext.HELP
    elif self.game.show_lore_viewer:
        return InputContext.LORE_VIEWER
    elif self.game.show_achievements:
        return InputContext.ACHIEVEMENTS_SCREEN
    else:
        return InputContext.GAMEPLAY
```

**Note:** This consolidates the existing scattered priority checks into a single method used by both keyboard and gamepad input.

#### 2.5 Create Action Executor
**File:** `game_input.py` (add method to InputHandler)

Unified action execution that **delegates** to existing handlers (avoids code duplication):
```python
def _execute_action(self, action: InputAction) -> bool:
    """
    Execute a game action (from keyboard or gamepad).

    Delegates to existing specialized handlers to avoid duplicating logic.
    Each handler gets an execute_action() method in Phase 2.6.

    Args:
        action: The InputAction to execute

    Returns:
        True if action was handled, False otherwise
    """
    context = self._get_current_context()

    # Delegate to existing specialized handlers (Phase 2.6 adds execute_action to each)
    if context == InputContext.GAMEPLAY:
        return self.gameplay_handler.execute_action(action)
    elif context == InputContext.INVENTORY:
        return self.inventory_handler.execute_action(action)
    elif context == InputContext.LOOK_MODE:
        return self.look_mode_handler.execute_action(action)
    elif context == InputContext.TARGETING:
        return self.targeting_handler.execute_action(action)
    elif context == InputContext.DIALOGUE:
        return self.dialogue_handler.execute_action(action)
    # ... etc for other contexts

    return False  # Action not handled
```

**Key Design Decision:** Action executor is a **thin routing layer** only. All game logic stays in existing handlers. This:
- Avoids duplicating logic (e.g., exploit slot handling already in GameplayInputHandler)
- Maintains single responsibility principle
- Makes testing easier (test handlers directly, not giant switch statement)
- Allows gradual migration (existing keyboard paths work alongside new abstraction)

#### 2.6 Extend Existing Handlers with Action Support
**Files:** `game_input_gameplay.py`, `game_input_inventory.py`, etc.

Add `execute_action()` method to each specialized handler. Example for GameplayInputHandler:
```python
def execute_action(self, action: InputAction) -> bool:
    """
    Execute an InputAction in gameplay context.

    Translates abstract actions to concrete game logic. Reuses existing methods
    to avoid duplication.

    Args:
        action: The InputAction to execute

    Returns:
        True if action was handled
    """
    # Movement actions
    if action in [InputAction.MOVE_NORTH, InputAction.MOVE_SOUTH, ...]:
        dx, dy = self._action_to_movement(action)
        self.game.move_player(dx, dy)
        return True

    # Exploit actions (reuse existing logic)
    elif action == InputAction.EXPLOIT_SLOT_1:
        return self._use_exploit_slot(0)
    elif action == InputAction.EXPLOIT_SLOT_2:
        return self._use_exploit_slot(1)
    # ... etc

    # NEW: Gamepad exploit cycling
    elif action == InputAction.EXPLOIT_CYCLE_NEXT:
        self.game.cycle_exploit_selection(+1)
        return True
    elif action == InputAction.EXPLOIT_CYCLE_PREV:
        self.game.cycle_exploit_selection(-1)
        return True
    elif action == InputAction.EXPLOIT_EXECUTE:
        slot = self.game.selected_exploit_index
        return self._use_exploit_slot(slot)

    # UI toggles
    elif action == InputAction.TOGGLE_INVENTORY:
        self.game.show_inventory = True
        return True
    # ... etc

    return False

def _action_to_movement(self, action: InputAction) -> tuple[int, int]:
    """Convert movement action to (dx, dy) delta."""
    movement_map = {
        InputAction.MOVE_NORTH: (0, -1),
        InputAction.MOVE_SOUTH: (0, 1),
        InputAction.MOVE_EAST: (1, 0),
        InputAction.MOVE_WEST: (-1, 0),
        InputAction.MOVE_NORTHEAST: (1, -1),
        InputAction.MOVE_NORTHWEST: (-1, -1),
        InputAction.MOVE_SOUTHEAST: (1, 1),
        InputAction.MOVE_SOUTHWEST: (-1, 1),
    }
    return movement_map.get(action, (0, 0))
```

Repeat for other handlers (InventoryInputHandler, LookModeInputHandler, etc.).

#### 2.7 Add Exploit Cycling State to Game Engine
**File:** `game_engine.py`

Add state tracking for selected exploit (single source of truth):
```python
class GameEngine:
    def __init__(self, ...):
        # ... existing init
        self.selected_exploit_index: int = 0  # Currently selected exploit (for cycling)

    def cycle_exploit_selection(self, direction: int):
        """
        Cycle through equipped exploits.

        Args:
            direction: +1 for next, -1 for previous
        """
        equipped_exploits = [e for e in self.player.exploits if e is not None]
        if not equipped_exploits:
            self.message_log.add_message("No exploits equipped", colors.YELLOW)
            return

        self.selected_exploit_index = (self.selected_exploit_index + direction) % len(equipped_exploits)

        # Visual/audio feedback
        exploit_name = equipped_exploits[self.selected_exploit_index].name
        self.message_log.add_message(f"Selected: {exploit_name}", colors.CYAN)
        # Optional: play UI "tick" sound via game_sound.py
```

**State Ownership Clarified:**
- `game.selected_exploit_index` = **single source of truth**
- Keyboard and gamepad both use `game.cycle_exploit_selection()`
- Renderer reads `game.selected_exploit_index` for visual indicator
- No duplication, no synchronization issues

#### 2.8 Add Visual Feedback for Exploit Cycling
**File:** `game_rendering_ui.py`

Show which exploit is currently selected (works for both keyboard and gamepad cycling):

```python
def render_exploit_bar(console, game):
    """Render exploit bar with selection indicator."""
    # ... existing exploit rendering

    # Add selection indicator if cycling feature is used
    if game.selected_exploit_index is not None:
        selected_x, selected_y = calculate_exploit_position(game.selected_exploit_index)
        # Render border or highlight around selected exploit
        console.draw_frame(selected_x-1, selected_y-1, 4, 3, fg=colors.CYAN)
        # Optional: Show "3/5" badge below exploit bar
        console.print(x, y, f"{game.selected_exploit_index+1}/{len(equipped_exploits)}", fg=colors.CYAN)
```

**Visual Indicators:**
- Cyan border around selected exploit slot
- Badge showing position (e.g., "3/5")
- Updates immediately when cycling (both keyboard and gamepad)

### Deliverables
- 1 new file: `game_input_gamepad.py`
- Modified: `game_input.py` (router + context + executor + handler delegation), `game_loop.py` (init), `game_rendering_ui.py` (visual feedback), `game_engine.py` (exploit cycling state)
- Modified: All existing input handlers (add `execute_action()` method)
- Functional gamepad support with hardcoded Option C bindings

### Technical Considerations
- **Turn-based movement:** Analog stick uses `game.turn_count` to gate movement (one move per turn), NOT time-based cooldown
- **Right stick behavior:** In gameplay = auto-activate look mode (magnitude > 0.3), in look/targeting = move cursor
- **Button repeat:** Buttons don't auto-repeat like held keys (use turn gating if needed)
- **Context detection:** `_get_current_context()` consolidates existing priority logic into single method
- **Action delegation:** Existing handlers keep game logic, new `execute_action()` methods provide abstraction interface

---

## PHASE 3: Default Gamepad Bindings (Option C Details)

### Goal
Complete, context-sensitive gamepad bindings for ALL game states.

### Context-Specific Mappings

#### Gameplay Context
- **Left Stick / D-Pad:** 8-way movement
- **Right Stick:** No action (reserved for look mode)
- **A:** Wait/pass turn
- **B:** (No action - could add quick-look)
- **Y:** Exploit slot 1 (direct)
- **X:** Exploit slot 2 (direct)
- **RB:** Cycle exploit forward (highlights in UI)
- **LB:** Cycle exploit backward
- **RT:** Execute selected exploit
- **LT:** Enter look mode
- **Start:** Open inventory
- **Select:** Open help
- **Left Stick Click:** Lore viewer
- **Right Stick Click:** Achievements

#### Look Mode Context
- **Right Stick:** **Auto-enter look mode + move cursor** (your idea!)
  - First movement of right stick from center → enters look mode
  - Continues to move cursor while active
  - Allows "flick to look" without pressing button first
- **Left Stick / D-Pad:** Also move cursor (alternative)
- **A:** Inspect entity at cursor
- **B:** Exit look mode
- **LT Released:** Exit look mode

#### Targeting Mode Context
- **Right Stick / Left Stick / D-Pad:** Move cursor
- **A / RT:** Execute exploit at cursor
- **B:** Cancel targeting

#### Inventory Context
- **Left Stick / D-Pad Up/Down:** Navigate items
- **A:** Use/equip selected item
- **B:** Close inventory
- **Shoulder Buttons:** Scroll (if needed)

#### Dialogue Context
- **D-Pad Left/Right:** Navigate options
- **A:** Confirm
- **B:** Cancel/dismiss
- **Y:** "Don't show again" (if applicable)

#### Menus (Main Menu, Settings, Help, etc.)
- **Left Stick / D-Pad Up/Down:** Navigate
- **Left/Right (or shoulder buttons):** Adjust values (settings)
- **A:** Select/confirm
- **B:** Back
- **Start:** (No action - prevent accidental activation)

### Tasks

#### 3.1 Implement Default Gamepad Mappings
**File:** `game_input_mappings.py` (add to InputMapper class)

Add method to populate default gamepad bindings:

```python
def _init_default_gamepad_mappings(self):
    """
    Initialize default gamepad button mappings (Option C).

    Called during InputMapper.__init__() to set up hardcoded defaults.
    """
    from tcod.event import ControllerButton as CB

    # === GAMEPLAY CONTEXT ===
    gameplay = InputContext.GAMEPLAY

    # Face buttons
    self._set_default_gamepad(CB.A, gameplay, InputAction.WAIT)
    self._set_default_gamepad(CB.Y, gameplay, InputAction.EXPLOIT_SLOT_1)
    self._set_default_gamepad(CB.X, gameplay, InputAction.EXPLOIT_SLOT_2)
    # B button reserved for potential quick-look feature

    # Shoulder buttons (exploit cycling)
    self._set_default_gamepad(CB.RIGHTSHOULDER, gameplay, InputAction.EXPLOIT_CYCLE_NEXT)
    self._set_default_gamepad(CB.LEFTSHOULDER, gameplay, InputAction.EXPLOIT_CYCLE_PREV)

    # Triggers (RT = execute exploit, LT = look mode)
    self._set_default_gamepad_trigger(is_right=True, gameplay, InputAction.EXPLOIT_EXECUTE)
    self._set_default_gamepad_trigger(is_right=False, gameplay, InputAction.TOGGLE_LOOK_MODE)

    # Menu buttons
    self._set_default_gamepad(CB.START, gameplay, InputAction.TOGGLE_INVENTORY)
    self._set_default_gamepad(CB.BACK, gameplay, InputAction.TOGGLE_HELP)  # "Select" button

    # Stick clicks
    self._set_default_gamepad(CB.LEFTSTICK, gameplay, InputAction.TOGGLE_LORE_VIEWER)
    self._set_default_gamepad(CB.RIGHTSTICK, gameplay, InputAction.TOGGLE_ACHIEVEMENTS)

    # D-Pad (movement - handled by analog handler as well)
    self._set_default_gamepad(CB.DPAD_UP, gameplay, InputAction.MOVE_NORTH)
    self._set_default_gamepad(CB.DPAD_DOWN, gameplay, InputAction.MOVE_SOUTH)
    self._set_default_gamepad(CB.DPAD_LEFT, gameplay, InputAction.MOVE_WEST)
    self._set_default_gamepad(CB.DPAD_RIGHT, gameplay, InputAction.MOVE_EAST)

    # === INVENTORY CONTEXT ===
    inv = InputContext.INVENTORY
    self._set_default_gamepad(CB.A, inv, InputAction.CONFIRM)
    self._set_default_gamepad(CB.B, inv, InputAction.CANCEL)
    self._set_default_gamepad(CB.DPAD_UP, inv, InputAction.NAVIGATE_UP)
    self._set_default_gamepad(CB.DPAD_DOWN, inv, InputAction.NAVIGATE_DOWN)

    # === LOOK MODE CONTEXT ===
    look = InputContext.LOOK_MODE
    self._set_default_gamepad(CB.A, look, InputAction.CONFIRM)  # Inspect entity
    self._set_default_gamepad(CB.B, look, InputAction.CANCEL)   # Exit look mode
    # Right stick movement handled specially (see Phase 3.2)

    # === TARGETING CONTEXT ===
    target = InputContext.TARGETING
    self._set_default_gamepad(CB.A, target, InputAction.CONFIRM)
    self._set_default_gamepad(CB.B, target, InputAction.CANCEL)
    self._set_default_gamepad_trigger(is_right=True, target, InputAction.CONFIRM)  # RT also confirms

    # === DIALOGUE CONTEXT ===
    dialogue = InputContext.DIALOGUE
    self._set_default_gamepad(CB.A, dialogue, InputAction.CONFIRM)
    self._set_default_gamepad(CB.B, dialogue, InputAction.CANCEL)
    self._set_default_gamepad(CB.DPAD_LEFT, dialogue, InputAction.NAVIGATE_LEFT)
    self._set_default_gamepad(CB.DPAD_RIGHT, dialogue, InputAction.NAVIGATE_RIGHT)

    # === MENU CONTEXT (main menu, settings, help, etc.) ===
    menu = InputContext.MENU
    self._set_default_gamepad(CB.A, menu, InputAction.CONFIRM)
    self._set_default_gamepad(CB.B, menu, InputAction.CANCEL)
    self._set_default_gamepad(CB.DPAD_UP, menu, InputAction.NAVIGATE_UP)
    self._set_default_gamepad(CB.DPAD_DOWN, menu, InputAction.NAVIGATE_DOWN)
    self._set_default_gamepad(CB.DPAD_LEFT, menu, InputAction.NAVIGATE_LEFT)
    self._set_default_gamepad(CB.DPAD_RIGHT, menu, InputAction.NAVIGATE_RIGHT)
    self._set_default_gamepad(CB.RIGHTSHOULDER, menu, InputAction.NAVIGATE_PAGE_DOWN)
    self._set_default_gamepad(CB.LEFTSHOULDER, menu, InputAction.NAVIGATE_PAGE_UP)

def _set_default_gamepad(self, button: ControllerButton, context: InputContext, action: InputAction):
    """Helper to set default gamepad binding."""
    key = (button, context)
    self._default_gamepad_button_map[key] = action

def _set_default_gamepad_trigger(self, is_right: bool, context: InputContext, action: InputAction):
    """Helper to set default trigger binding (triggers are axes, not buttons)."""
    axis = ControllerAxis.TRIGGERRIGHT if is_right else ControllerAxis.TRIGGERLEFT
    self._default_gamepad_axis_map[(axis, context)] = action
```

#### 3.2 Add Right Stick Auto-Look Implementation
**File:** `game_input_gamepad.py` (GamepadInputHandler class)

Implement right stick auto-activation of look mode:

```python
def handle_axis_event(self, event: ControllerAxis, context: InputContext) -> InputAction | None:
    """Handle gamepad axis events (analog sticks, triggers)."""

    # Update analog handler state
    if event.axis == ControllerAxis.LEFTX:
        self.analog_handler.update_left_stick(x=event.value)
    elif event.axis == ControllerAxis.LEFTY:
        self.analog_handler.update_left_stick(y=event.value)
    elif event.axis == ControllerAxis.RIGHTX:
        self.analog_handler.update_right_stick(x=event.value)
    elif event.axis == ControllerAxis.RIGHTY:
        self.analog_handler.update_right_stick(y=event.value)

    # Right stick auto-activates look mode (only in gameplay context)
    if context == InputContext.GAMEPLAY:
        magnitude = self.analog_handler.get_right_stick_magnitude()
        if magnitude > 0.3 and not self.game.look_mode:
            self.game.look_mode = True
            self.game.message_log.add_message("Look mode activated", colors.CYAN)
            # Don't return action - let look mode handler process cursor movement

    # In look mode or targeting, right stick moves cursor
    if context in [InputContext.LOOK_MODE, InputContext.TARGETING]:
        rx, ry = self.analog_handler.get_right_stick_position()
        if abs(rx) > 0.5 or abs(ry) > 0.5:
            # Convert to 8-way cursor movement
            dx = 1 if rx > 0.5 else (-1 if rx < -0.5 else 0)
            dy = 1 if ry > 0.5 else (-1 if ry < -0.5 else 0)
            # Move cursor (handled by look/targeting handler)
            # This is context-specific, so return appropriate navigation action
            # ... (implementation details in look mode handler)

    # Left stick movement (turn-gated)
    if context == InputContext.GAMEPLAY:
        movement = self.analog_handler.get_left_stick_movement(self.game.turn_count)
        if movement:
            dx, dy = movement
            # Convert to movement action
            return self._delta_to_movement_action(dx, dy)

    # Triggers (threshold > 50% = pressed)
    if event.axis in [ControllerAxis.TRIGGERLEFT, ControllerAxis.TRIGGERRIGHT]:
        normalized = self.analog_handler.apply_trigger_deadzone(event.value)
        if normalized > 0.5:  # Trigger pressed
            # Look up trigger binding for current context
            return self.input_mapper.get_gamepad_axis_action(event.axis, context)

    return None
```

**Right Stick Look Mode Behavior:**
- In gameplay: magnitude > 0.3 → auto-enter look mode, stay active until B or LT
- In look/targeting: always move cursor (no auto-activation needed)
- In menus: no action (prevent accidental activation)

### Deliverables
- Complete bindings in `InputMapper` default mappings (Phase 3.1)
- Right stick auto-look mode (Phase 3.2)
- Context-aware action routing (works for all contexts)
- Full playability via gamepad

### Technical Considerations
- **Right stick look mode:** Magnitude threshold 0.3 (lower than movement threshold 0.5) for quick activation
- **Look mode persistence:** Stays active after stick release (exit via B button or LT release only)
- **Exploit cycling UI:** Visual indicator added in Phase 2.8
- **Dead zone tuning:** Same deadzone for all contexts (15%), but different thresholds for movement (50%) vs look activation (30%)

---

## PHASE 4: Custom Remapping UI - Keyboard

### Goal
Settings menu interface for remapping keyboard controls with conflict detection.

### Tasks

#### 4.1 Add Controls Submenu to Settings
**File:** `game_menus.py` (SettingsMenu class, lines 675-1530)

Add new menu option between "Dialogue Preferences" and "Export Debug Package":
```
Settings Menu:
  Audio
    - Master Volume
    - SFX Volume
    - Music Volume
  Graphics
    - Graphics Mode
    - Particle Effects
    - UI Color
  > Controls  ← NEW
    - Keyboard Bindings
    - Gamepad Bindings
    - Gamepad Settings
  Dialogue Preferences
  Export Debug Package
  Back
```

#### 4.2 Create Keyboard Bindings Screen
**New file:** `game_menu_controls.py`

Scrollable list of all actions with current bindings:

```python
class KeyboardBindingsMenu:
    """
    Remapping interface for keyboard controls.

    Layout:
      Keyboard Bindings               [Page 1/3]
      ═══════════════════════════════════════════
      Movement:
        Move North ................ [W] [↑] [Numpad8]
        Move South ................ [S] [↓] [Numpad2]
        ...

      Actions:
        Wait ...................... [Space] [.]
        Inventory ................. [I]
        Look Mode ................. [L]
        ...

      [Add Binding] [Remove Binding] [Reset to Defaults]
    """

    def __init__(self, game, input_mapper):
        self.categories = [
            "Movement", "Actions", "Exploits", "UI Toggles", "Navigation"
        ]
        self.selected_action: InputAction | None = None
        self.binding_mode = False  # Waiting for key press
        self.scroll_offset = 0

    def handle_input(event) -> str  # "back", "continue", "binding"
    def start_binding(action: InputAction)  # Enter "press key to bind" mode
    def capture_binding(event: KeyDown)  # Capture key press
    def check_conflicts(action, key) -> list[InputAction]
    def show_conflict_dialog(conflicts)  # "Replace existing binding?"
    def render(console)
```

**Binding mode flow:**
1. User selects action (e.g., "Move North")
2. Presses Enter/A → enters binding mode
3. Screen shows: "Press key for Move North... (ESC to cancel)"
4. User presses key (e.g., T)
5. Check for conflicts
6. If conflict: "T is bound to [Action]. Replace? [Y/N]"
7. Save binding, exit binding mode

#### 4.3 Create Gamepad Bindings Screen (Stub for Phase 5)
**File:** `game_menu_controls.py`

Similar structure but captures ControllerButton events. Defer implementation to Phase 5.

#### 4.4 Create Gamepad Settings Screen
**File:** `game_menu_controls.py`

Adjust deadzone, enable/disable gamepad:
```
Gamepad Settings
═════════════════════════════════════════
  Gamepad Enabled ................ [ON/OFF]
  Deadzone ....................... [15%] ←→
  Movement Threshold ............. [50%] ←→

  [Test Gamepad] ← Shows live input visualization
  [Back]
```

Test mode shows real-time stick positions, button states for calibration.

#### 4.5 Integrate with Settings Menu
**File:** `game_menus.py`

Add navigation:
- "Controls" option in main settings
- Submenu navigation (keyboard/gamepad/settings)
- Save bindings on back navigation via `GameSettings.save_settings()`

Update `user_settings.json` structure:
```json
{
  "master_volume": 0.7,
  "custom_keyboard_bindings": {
    "MOVE_NORTH": ["W", "UP", "KP_8"],
    "WAIT": ["SPACE", "PERIOD"],
    ...
  },
  "custom_gamepad_bindings": { ... },
  "gamepad_deadzone": 0.15,
  "gamepad_enabled": true
}
```

### Deliverables
- 1 new file: `game_menu_controls.py`
- Modified: `game_menus.py` (add Controls submenu)
- Modified: `game_config.py` (save/load custom bindings)
- Full keyboard remapping UI with conflict detection

### Technical Considerations
- **Multi-key bindings:** Allow multiple keys per action (W, ↑, Numpad8 all do "Move North")
- **Reserved keys:** Prevent binding to ESC (always cancel), F12 (debug)
- **Validation:** Check for invalid bindings (modifier-only keys)
- **Scrolling:** Use same pattern as achievements menu (PageUp/Down, mouse wheel)
- **Persistence:** Save immediately on binding change (prevents loss on crash)

---

## PHASE 5: Custom Remapping UI - Gamepad

### Goal
Extend remapping UI to support gamepad buttons and axes.

### Tasks

#### 5.1 Implement Gamepad Bindings Screen
**File:** `game_menu_controls.py` (GamepadBindingsMenu class)

Similar to keyboard but captures ControllerButton events:

```
Gamepad Bindings                [Page 1/2]
═══════════════════════════════════════════
Movement:
  Move North ................ [DPad-Up] [LS-Up]
  Move South ................ [DPad-Down] [LS-Down]
  ...

Actions:
  Wait ...................... [A]
  Inventory ................. [Start]
  Confirm ................... [A]
  Cancel .................... [B]
  ...

Exploits:
  Exploit Slot 1 ............ [Y]
  Exploit Slot 2 ............ [X]
  Cycle Next ................ [RB]
  Cycle Previous ............ [LB]
  Execute Selected .......... [RT]
  ...
```

**Axis binding:** For analog sticks, allow directional binding:
- "Left Stick Up" → MOVE_NORTH
- "Right Stick Right" → (disabled in gameplay, used in look mode)

#### 5.2 Add Button Visualization
Show button/stick labels in human-readable format:
- `ControllerButton.A` → "A Button"
- `ControllerButton.LEFTSHOULDER` → "LB / L1"
- `ControllerAxis.LEFTX` → "Left Stick X-Axis"

Support multiple controller types:
- Xbox: A/B/X/Y, LB/RB, LT/RT
- PlayStation: Cross/Circle/Square/Triangle, L1/R1, L2/R2
- Generic: Button 0-20

#### 5.3 Handle Analog Binding
**Challenge:** Axes are continuous, not discrete buttons.

**Solution:** Treat axes as 4 directional bindings:
- Left Stick: Up, Down, Left, Right (applied after deadzone)
- Right Stick: Same
- Triggers: Pressed (> 50%)

Allow user to bind "Left Stick Up" separately from "D-Pad Up" (multi-input per action).

#### 5.4 Conflict Detection for Gamepad
Same logic as keyboard: warn when binding conflicts with existing action.

**Special case:** Context-sensitive bindings (A = wait in gameplay, confirm in menus) are NOT conflicts.

#### 5.5 Controller Detection UI
**File:** `game_menu_controls.py`

In binding mode, show detected controller:
```
Press button for [Action]...

Controller: Xbox Series X Controller
(ESC to cancel)
```

If no controller connected, show warning:
```
No gamepad detected. Please connect a controller.
```

### Deliverables
- Complete `GamepadBindingsMenu` class in `game_menu_controls.py`
- Axis binding support in `InputMapper`
- Full gamepad remapping UI

### Technical Considerations
- **Axis threshold:** Require >50% deflection to register as "pressed" during binding
- **Trigger binding:** Treat triggers as buttons (binary) for binding purposes
- **Stick click:** Support binding to L3/R3 (stick click buttons)
- **D-Pad:** Some controllers report D-Pad as buttons, others as axis (SDL normalizes this)

---

## PHASE 6: Testing & Polish

### Goal
Ensure robust gamepad support, handle edge cases, update documentation.

### Tasks

#### 6.1 Edge Case Handling

**Controller hotplugging:**
- Disconnect during gameplay → pause game, show "Controller disconnected" overlay
- Reconnect → resume with controller working
- Multiple controllers → use first connected, ignore others (or allow selection in settings)

**Simultaneous input:**
- Keyboard + gamepad input → both work, last input wins
- Mouse + gamepad cursor → last input source controls cursor

**Exploit cycling edge cases:**
- Cycle with <5 exploits equipped → wrap around available exploits only
- Unequip exploit while selected → auto-select next available
- No exploits equipped → cycling does nothing, show message

**Binding conflicts:**
- Two actions on same button in same context → warn, prevent
- Same action on multiple buttons → allow (like keyboard W/↑/Numpad8)

#### 6.2 Update Help Screen
**File:** `game_menu_help_lore.py` (HelpMenu)

Add gamepad controls page:
```
Page 3: Gamepad Controls
═══════════════════════════════════════
Movement:
  Left Stick / D-Pad ........ Move (8-way)
  A ......................... Wait

Actions:
  Y / X ..................... Exploits 1-2
  RB / LB ................... Cycle Exploits
  RT ........................ Use Selected Exploit
  Start ..................... Inventory
  Select .................... Help
  LT ........................ Look Mode

In Look Mode:
  Right Stick ............... Move Cursor
  A ......................... Inspect
  B ......................... Exit

(Customizable in Settings > Controls)
```

Update existing pages to mention gamepad alternatives where relevant.

#### 6.3 Settings Menu Help Text
Add tooltips/descriptions for control settings:
- "Deadzone: Minimum stick movement to register (15% recommended)"
- "Threshold: Stick deflection required for movement (50% default)"

#### 6.4 Test with Multiple Controller Types
Test on:
- Xbox controllers (360, One, Series X)
- PlayStation controllers (DS4, DualSense)
- Nintendo Pro Controller
- Generic USB gamepad

Ensure SDL GameControllerDB mappings work correctly (should be automatic).

#### 6.5 Keyboard-Only Exploit Cycling (Optional Enhancement)
**User suggestion:** "Consider this will add new actions (scroll exploit left or right, execute exploit) that aren't present in keyboard (but could be?)"

**Implementation:** Add keyboard bindings for exploit cycling:
- `[` key → Cycle exploit previous (or unbound by default)
- `]` key → Cycle exploit next
- No "execute selected" needed (just press 1-5)

**UI:** Show selected exploit indicator even when using keyboard (consistency).

**Benefit:** Allows keyboard-only players to preview exploits without pressing 1-5.

#### 6.6 Validation & Error Handling

**Settings loading:**
- Invalid binding in JSON → log warning, use default
- Unrecognized action name → ignore, continue
- Missing custom bindings → use all defaults

**Binding mode:**
- Invalid key (modifier-only, system keys) → show error, retry
- ESC during binding → cancel, restore original
- Controller disconnected during binding → cancel, show message

#### 6.7 Performance Testing
- Ensure axis events (continuous) don't cause performance issues
- Profile input handling with 60 FPS target
- Test analog stick responsiveness (should feel smooth, not laggy)

### Deliverables
- Updated help screens with gamepad info
- Edge case handling in all input handlers
- Tested on multiple controller types
- Optional keyboard exploit cycling

---

## Architecture Gotchas & Design Decisions

### 1. Migration from Direct Key Checking
**Problem:** Existing code has ~100+ direct key checks (`event.sym == KeySym.W`).

**Solution:** Gradual migration, NOT big-bang refactor:
- Phase 1-2: Add abstraction layer ALONGSIDE existing checks
- InputMapper can return `None` if no custom binding, fall back to existing code
- Slowly refactor handlers to use `_execute_action()` over time
- Both paths work during transition

### 2. Context-Sensitive Bindings
**Problem:** Same button means different things in different states (A = wait in gameplay, confirm in menus).

**Solution:** `InputContext` enum + context-aware mappings:
```python
# Same button, different actions
(ControllerButton.A, InputContext.GAMEPLAY) → InputAction.WAIT
(ControllerButton.A, InputContext.MENU) → InputAction.CONFIRM
(ControllerButton.A, InputContext.INVENTORY) → InputAction.CONFIRM
```

**Detection:** `_get_current_context()` mirrors existing priority logic (game_input.py:100-182).

### 3. Right Stick Auto-Activate Look Mode
**Problem:** User wants right stick movement to automatically enter look mode (no button press).

**Solution:** In `AnalogStickHandler`:
```python
if not game.look_mode and right_stick_magnitude > 0.3:
    game.look_mode = True
    # Continue processing stick as cursor movement
```

**Edge case:** Don't activate during menus/dialogues (check context first).

### 4. Analog Stick Continuous Events - Turn-Based Gating
**Problem:** Moving analog stick generates hundreds of ControllerAxis events per second, but game is turn-based.

**Solution (TURN-BASED, not time-based):**
- Apply deadzone first (filter noise)
- Track `last_move_turn` instead of `last_move_time`
- Use `game.turn_count` to gate movement: if current turn > last turn → allow move
- Store axis state, process when turn increments (not on time interval)
- In look mode: update cursor immediately (no gating needed - not turn-based)

**Why Turn-Based:**
- Time-based cooldown (150ms) would allow multiple moves per game turn
- Turn-based gating ensures one movement per turn, matching keyboard behavior
- Continuous stick hold = continuous events, but only first event per turn triggers movement
- Turn increments (enemies move) → next stick event triggers next movement

See Phase 1.3 for full implementation details.

### 5. Settings Migration
**Problem:** Existing saves don't have custom binding data.

**Solution:** `GameSettings.load_settings()` uses `.get()` with defaults (lines 89-96):
```python
self.custom_keyboard_bindings = settings_data.get("custom_keyboard_bindings", {})
self.custom_gamepad_bindings = settings_data.get("custom_gamepad_bindings", {})
```

Empty dict → use all default bindings (Phase 1 default mappings).

### 6. Binding Storage Format
**Problem:** How to serialize KeySym/ControllerButton enums?

**Solution:** Store as strings in JSON:
```json
{
  "custom_keyboard_bindings": {
    "MOVE_NORTH": ["W", "UP", "KP_8"]
  },
  "custom_gamepad_bindings": {
    "MOVE_NORTH": ["DPAD_UP", "AXIS_LEFTY_NEGATIVE"]
  }
}
```

**Loading:** `InputMapper` converts strings to enums via lookup dict:
```python
KeySym[key_string]  # "W" → KeySym.W
ControllerButton[button_string]  # "A" → ControllerButton.A
```

### 7. Mouse + Gamepad Cursor Conflict
**Problem:** Look mode can be controlled by mouse OR right stick. Which wins?

**Solution:** Last input source wins:
- Track `last_cursor_input_source` ("mouse" or "gamepad")
- On mouse motion: set source to "mouse", update cursor
- On right stick motion: set source to "gamepad", update cursor
- No conflict, seamless switching

### 8. Exploit Cycling UI Feedback
**Problem:** User won't know which exploit is selected when cycling.

**Solution:** Visual indicator in exploit bar (game_rendering_ui.py):
- Render thick border around selected exploit
- Show number badge "3/5" below exploit bar
- Play UI "tick" sound on cycle (game_sound.py)

### 9. No Gamepad Connected
**Problem:** User tries to open gamepad bindings with no controller.

**Solution:** Show warning message:
```
No gamepad detected.
Please connect a controller to customize bindings.

[Test Connection] [Back]
```

"Test Connection" re-scans for controllers, shows detected devices.

### 10. Reserved Bindings
**Problem:** User tries to bind critical keys (ESC, F12).

**Solution:** Blacklist in `InputMapper`:
```python
RESERVED_KEYS = {KeySym.ESCAPE, KeySym.F12}  # ESC = always cancel, F12 = debug
RESERVED_BUTTONS = {ControllerButton.GUIDE}  # Home button = system reserved
```

Show error: "This button is reserved and cannot be rebound."

### 11. Controller Disconnect/Reconnect Flow
**Problem:** What happens when controller disconnects mid-game?

**Solution:** Graceful degradation with clear feedback:

**Disconnect handling:**
1. ControllerDevice event (removed=True) fires
2. Remove controller from `self.controllers` set
3. If in gameplay (not menu): Show overlay "Controller disconnected - Press any key to continue"
4. Game state pauses (don't process turns)
5. Switch to keyboard input automatically

**Reconnect handling:**
1. ControllerDevice event (added=True) fires
2. Add controller to `self.controllers` set
3. Show brief message: "Controller reconnected"
4. Resume gameplay (unpause if paused)
5. Gamepad input available immediately

**Mid-turn disconnect:** If disconnect happens during enemy turn processing, finish current turn cycle first, THEN show overlay (don't interrupt turn resolution).

### 12. Multi-Controller Priority
**Problem:** Multiple controllers connected - which one to use?

**Solution:** Simple first-wins approach:
- Use `min(controllers, key=lambda c: c.instance_id)` (lowest ID = first connected)
- All events from any controller are accepted (user can plug/unplug to change active controller)
- Future enhancement: Add "Select Controller" in settings to choose specific device

### 13. Analog Cursor Speed in Look/Targeting Mode
**Problem:** How fast should right stick move cursor in look mode?

**Solution:** **Tile-by-tile with turn-gating** (consistent with keyboard):
- Convert analog to 8-way digital (same as movement)
- Apply turn-gating: one cursor move per turn
- Alternative (if too slow): Use time-based cooldown (100ms) for cursor ONLY (not movement)

**Recommendation:** Start with turn-gated, add time-based option if playtesting shows it's too slow.

### 14. Navigation vs Movement Action Overlap
**Problem:** WASD moves in gameplay, navigates in menus - are these separate actions?

**Solution:** **Same action, context-aware behavior:**
- `InputAction.MOVE_NORTH` in GAMEPLAY context → move player north
- `InputAction.MOVE_NORTH` in MENU context → navigate up in menu
- No separate `NAVIGATE_UP` action needed
- Handlers interpret same action differently based on context
- Simplifies bindings (user binds "up" once, works everywhere)

### 15. Modifier Keys and the Abstraction Layer
**Problem:** How to handle modifier-dependent actions (Shift+F12 debug export)?

**Solution:** **Bypass abstraction for modifier combos:**
- Modifier-dependent actions continue using direct key checks
- `event.mod & tcod.event.KMOD_SHIFT` checked before `_execute_action()`
- InputMapper only handles non-modified keys
- Rationale: Modifier combos are rare, complex to remap, low priority for Phase 1-3

**Future enhancement (Phase 4-5):** Add modifier support to remapping UI if needed.

### 16. D-Pad Axis vs Button Reporting
**Problem:** Some controllers report D-Pad as buttons, others as axis events.

**Solution:** **SDL normalizes to buttons, but handle both:**
- Primary bindings: Use `ControllerButton.DPAD_UP/DOWN/LEFT/RIGHT`
- Axis fallback: If D-Pad reports as axis, convert to button events in handler
- SDL's GameController API should handle normalization automatically
- Test with multiple controller types to verify

**Implementation note:** TCOD wraps SDL GameController API, so normalization should "just work" - verify during Phase 6.4 testing.

---

## Files Created/Modified Summary

### New Files (7)
1. `game_input_actions.py` - Action/Context enums (Phase 1)
2. `game_input_mappings.py` - InputMapper class (Phase 1)
3. `game_input_analog.py` - Analog stick handling (Phase 1)
4. `game_input_gamepad.py` - Gamepad event handler (Phase 2)
5. `game_menu_controls.py` - Remapping UI (Phases 4-5)

### Modified Files (8)
1. `game_config.py` - GameSettings (custom bindings, gamepad settings)
2. `game_input.py` - Router + context detection + action executor + handler delegation
3. `game_loop.py` - SDL joystick init, pass controllers to InputHandler
4. `game_engine.py` - Exploit cycling state (selected_exploit_index)
5. `game_rendering_ui.py` - Exploit cycling visual feedback
6. `game_menus.py` - Add Controls submenu
7. `game_menu_help_lore.py` - Add gamepad controls page
8. All input handlers (`game_input_gameplay.py`, `game_input_inventory.py`, etc.) - Add `execute_action()` method

### Configuration Files (1)
1. `saves/user_settings.json` - New fields for custom bindings

---

## Testing Strategy

### Primary Testing Platform: Steam Deck

**You Own a Steam Deck - Perfect for Gamepad Testing!**

Steam Deck provides:
- ✅ Real gamepad hardware (not emulated)
- ✅ Real Linux environment (tests cross-platform simultaneously)
- ✅ Target handheld resolution (1280×800 = 16×16 chars, perfect match)
- ✅ Real suspend/resume testing
- ✅ Text readability validation at arm's length
- ✅ Button mapping validation (A/B/X/Y, triggers, bumpers, D-pad, analog sticks)

**Testing Workflow**:
1. Implement gamepad support on Windows first
2. Test with Xbox controller on Windows (if available) OR Steam Deck in Desktop Mode
3. Build Linux version
4. Copy to Steam Deck
5. Test in Desktop Mode (validate Linux compatibility)
6. Add to Steam library
7. Test in Gaming Mode (full handheld experience)
8. Verify text readability at 12-18 inches
9. Test all button mappings
10. Test analog stick dead zones
11. Test suspend/resume (mid-game state preservation)

**This validates both gamepad AND Linux simultaneously!**

### Secondary Testing: Windows

**If you have Xbox/PlayStation controller for Windows**:
- Test gamepad implementation before Linux build
- Faster iteration (no file transfer to Steam Deck)
- SDL2 gamepad mapping should be identical across platforms

### Testing Checklist

### Unit Tests
- `test_input_mappings.py` - Test action enum, binding serialization, conflict detection
- `test_analog_handling.py` - Test deadzone algorithms, analog-to-digital conversion
- `test_gamepad_events.py` - Mock controller events, verify routing

### Integration Tests
- Test all gameplay with gamepad (movement, exploits, UI navigation)
- Test remapping UI (capture bindings, save/load, conflict resolution)
- Test hotplugging (disconnect/reconnect during gameplay)
- Test simultaneous keyboard + gamepad input

### Manual Test Cases
1. Complete playthrough with gamepad only (no keyboard/mouse)
2. Remap all controls, restart game, verify persistence
3. Create binding conflicts, verify warnings
4. Disconnect controller mid-game, verify graceful handling
5. Test right-stick auto-look mode in various contexts
6. Test exploit cycling with <5 exploits equipped

---

## Phased Rollout Recommendation

**Minimum Viable:** Phases 1-3
- Gamepad support with hardcoded Option C bindings
- Fully playable, no customization yet
- Low risk, high value for gamepad users

**Full Feature:** Phases 1-6
- Custom remapping for keyboard + gamepad
- Complete control customization
- Higher complexity but maximizes accessibility

**User Choice:** Could ship Phase 1-3 in one release, Phase 4-6 in follow-up based on feedback.

---

## Estimated Complexity

- **Phase 1:** High (architecture foundation, careful design needed)
- **Phase 2:** Medium (integrate with existing, handle edge cases)
- **Phase 3:** Low (just mapping data, straightforward)
- **Phase 4:** High (UI work, conflict detection, scrolling, binding capture)
- **Phase 5:** Medium (reuse Phase 4 patterns, adapt for gamepad)
- **Phase 6:** Medium (testing time, edge cases, polish)

**Overall:** This is a large, complex feature. Expect significant testing and iteration, especially for UI/UX polish in remapping screens.

---

## Key References for Implementation

- **TCOD Gamepad Docs:** python-tcod.readthedocs.io (ControllerButton, ControllerAxis APIs)
- **Interaction Map:** See agent research output (comprehensive list of all inputs)
- **Current Input Architecture:** game_input.py (routing), game_input_*.py (handlers)
- **Settings System:** game_config.py (GameSettings class, lines 23-164)
- **Analog Math:** See TCOD research (scaled radial deadzone algorithm)
- **SDL GameControllerDB:** github.com/mdqinc/SDL_GameControllerDB (automatic controller mapping)

---

This plan provides step-by-step implementation with minimal disruption to existing code, context-sensitive bindings for all game states, and comprehensive remapping UI for both input types.
