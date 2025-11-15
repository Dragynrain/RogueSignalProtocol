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
        self.last_move_time = 0.0
        self.move_cooldown = 0.15
        self.left_x = 0
        self.left_y = 0
        self.right_x = 0
        self.right_y = 0

    def apply_scaled_radial_deadzone(x, y) -> tuple[float, float]
    def analog_to_8way(x, y) -> tuple[int, int]
    def can_move() -> bool  # Cooldown check for tile movement
    def update_axis(axis: ControllerAxis, value: int)
    def get_movement_delta() -> tuple[int, int] | None
```

**Rationale:** Scaled radial deadzone for smooth feel, cooldown prevents movement spam from continuous axis events.

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
    def __init__(self, input_mapper: InputMapper):
        self.controllers: set[GameController] = set()
        self.input_mapper = input_mapper
        self.analog_handler = AnalogStickHandler()
        self.current_exploit_index = 0  # For cycling

    def handle_device_event(event: ControllerDevice)
    def handle_button_event(event: ControllerButton, context: InputContext) -> InputAction | None
    def handle_axis_event(event: ControllerAxis) -> InputAction | None
    def cycle_exploit(direction: int)  # ±1 for next/prev
    def get_selected_exploit() -> int
```

**Device management:** Track add/remove events, use `discard()` not `remove()` (see TCOD research gotcha #1).

**Axis handling:**
- Left stick → Movement actions (via analog_to_8way)
- Right stick → Look mode cursor (context-sensitive)
- Triggers → Exploit execution, look mode activation

#### 2.3 Integrate with InputHandler Router
**File:** `game_input.py`

Add gamepad handler alongside existing handlers:
```python
class InputHandler:
    def __init__(self, game, renderer=None):
        # ... existing handlers
        self.input_mapper = InputMapper()
        self.gamepad_handler = GamepadInputHandler(self.input_mapper)
        self.input_mapper.load_custom_bindings(game.settings.custom_keyboard_bindings)
```

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

#### 2.4 Create Action Executor
**File:** `game_input.py` (add method to InputHandler)

Unified action execution (works for both keyboard and gamepad):
```python
def _execute_action(self, action: InputAction) -> bool:
    """Execute a game action (from keyboard or gamepad)."""
    context = self._get_current_context()

    # Movement actions
    if action in [InputAction.MOVE_NORTH, ...]:
        dx, dy = self._action_to_movement(action)
        self.game.move_player(dx, dy)
        return True

    # Exploit actions
    elif action == InputAction.EXPLOIT_SLOT_1:
        self.gameplay_handler.use_exploit_slot(0)
        return True

    # NEW: Gamepad exploit cycling
    elif action == InputAction.EXPLOIT_CYCLE_NEXT:
        self.gamepad_handler.cycle_exploit(+1)
        return True
    elif action == InputAction.EXPLOIT_EXECUTE:
        slot = self.gamepad_handler.get_selected_exploit()
        self.gameplay_handler.use_exploit_slot(slot)
        return True

    # UI toggles
    elif action == InputAction.TOGGLE_INVENTORY:
        self._open_inventory()
        return True

    # ... etc for all actions
```

#### 2.5 Add Visual Feedback for Exploit Cycling
**File:** `game_rendering_ui.py`

When gamepad cycles exploits, highlight the currently selected one:
- Add `selected_exploit_index` to rendering state
- Render selection indicator (border, highlight color) around selected exploit
- Update on cycle actions

### Deliverables
- 1 new file: `game_input_gamepad.py`
- Modified: `game_input.py` (router + action executor), `game_loop.py` (init), `game_rendering_ui.py` (visual feedback)
- Functional gamepad support with hardcoded Option C bindings

### Technical Considerations
- **Analog stick cooldown:** 150ms between tile moves feels responsive (see analog handler)
- **Right stick behavior:** In gameplay = no action, in look/targeting = move cursor
- **Button repeat:** Buttons don't auto-repeat like held keys; implement if needed
- **Context detection:** `_get_current_context()` checks game state flags (show_inventory, look_mode, etc.) - mirrors existing priority logic (game_input.py:100-182)

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

### Deliverables
- Complete bindings in `InputMapper` default mappings
- Context-aware action routing
- Full playability via gamepad

### Technical Considerations
- **Right stick look mode:** Requires threshold detection (see analog handler) - if magnitude > 0.3, enter look mode
- **Exploit cycling UI:** Show which exploit is selected (1-5 indicator)
- **Dead zone tuning:** May need per-context adjustment (gameplay vs menus)

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

### 4. Analog Stick Continuous Events
**Problem:** Moving analog stick generates hundreds of ControllerAxis events per second.

**Solution:**
- Apply deadzone first (filter noise)
- Use cooldown timer for tile movement (150ms)
- Store axis state, process on cooldown expiry (not on every event)
- In look mode: update cursor immediately (no cooldown needed)

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

---

## Files Created/Modified Summary

### New Files (7)
1. `game_input_actions.py` - Action/Context enums (Phase 1)
2. `game_input_mappings.py` - InputMapper class (Phase 1)
3. `game_input_analog.py` - Analog stick handling (Phase 1)
4. `game_input_gamepad.py` - Gamepad event handler (Phase 2)
5. `game_menu_controls.py` - Remapping UI (Phases 4-5)

### Modified Files (6)
1. `game_config.py` - GameSettings (custom bindings, gamepad settings)
2. `game_input.py` - Router + action executor
3. `game_loop.py` - SDL joystick init
4. `game_rendering_ui.py` - Exploit cycling visual feedback
5. `game_menus.py` - Add Controls submenu
6. `game_menu_help_lore.py` - Add gamepad controls page

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
