# Gamepad Input - Critical Patterns

## CRITICAL PATTERNS

### 1. Action Comparison
```python
# Actions ARE InputAction enum values
if action == InputAction.NAVIGATE_UP:
if action in (InputAction.NAVIGATE_UP, InputAction.NAVIGATE_DOWN):
```

### 2. Renderer Access for Modal Actions
In-game modals (help, achievements) need renderer to call navigation methods:
- Check `self.renderer` exists and has required methods
- Get menu object via `_get_or_create_help_menu()`
- Call navigation method directly (e.g. `help_menu._navigate_page(direction)`)
- If renderer is None: InputHandler wasn't initialized with renderer parameter

### 3. Auto-Repeat for Menus

**Two code paths:**
1. Event-driven (rsp.input.handler) - Button presses create actions, NO auto-repeat
2. Polling (rsp.core.loop) - Checks stick/D-pad state, HAS auto-repeat

**Timing constants (tested):**
```python
initial_delay = 0.3s   # 300ms before repeat starts
repeat_rate = 0.12s    # 120ms between repeats
# Stick: Immediate on direction change
# D-pad: NO immediate on direction change (prevents double-tap)
```

**D-pad double-move fix:**
```python
if direction_changed:
    # Reset timing but DON'T act immediately (event handler already acted)
    handle_menu_navigation._dpad_acted = False
    handle_menu_navigation._dpad_last_direction = direction_value
    handle_menu_navigation._dpad_last_action_time = current_time
```

### 4. Menu Polling Setup

**CRITICAL: `tcod.sdl.joystick.get_controllers()` RETURNS EMPTY DURING GAMEPLAY!**

Must use pre-stored controller references:

```python
# Main menu context - OK to call get_controllers()
if shared_controllers:
    controllers = list(shared_controllers)
else:
    controllers = tcod.sdl.joystick.get_controllers()

# In-game context - NEVER call get_controllers()!
if hasattr(input_handler.gamepad_handler, 'controllers'):
    controllers = list(input_handler.gamepad_handler.controllers)  # Use pre-stored!
```

### 5. Context Detection

```python
def _get_current_context(self) -> InputContext:
    if self.game.dialogue_state.is_active():
        return InputContext.DIALOGUE
    elif self.game.show_help:
        return InputContext.HELP
    elif self.game.show_inventory:
        return InputContext.INVENTORY
    # ... etc
    else:
        return InputContext.GAMEPLAY
```

### 6. Direction Locking & Settling Period (Gameplay Movement)

**Settling period:** 30ms wait before locking direction (allows stick to reach target position)
**Direction locking:** After settling, direction is locked until stick released (prevents multi-move from diagonal swipes)

Setting: `settings.gamepad_direction_locking` (passed to AnalogStickHandler)
Config: `GameConfig.ANALOG_SETTLING_PERIOD` (30ms default)

## COMMON MISTAKES

### 1. Time-based vs Turn-based
Gameplay movement uses TIME-based gating, NOT turn-based (turns increment after move)
```python
# Both use time.time() for gating
self.last_gameplay_move_time  # Gameplay
self.last_menu_move_time      # Menus
```

### 2. Forgetting renderer parameter
```python
# WRONG: input_handler = InputHandler(game)
# RIGHT: input_handler = InputHandler(game, renderer=my_renderer)
```

### 3. Creating actions instead of direct calls for menus
```python
# WRONG for help menu polling: action = _delta_to_navigation_action(0, dy); _execute_action(action)
# RIGHT: help_menu = renderer._get_or_create_help_menu(); help_menu._navigate_page(-1 if dy < 0 else 1)
```

## CRITICAL BUG PATTERNS

### Polling Conditional Logic (rsp.core.loop)
When adding new modal screens, must update BOTH branches:
```python
# Branch 1: Gameplay movement - EXCLUDE all modals
if (not game.show_inventory and not game.show_help and ...):  # Add new modals here!
    # Gameplay stick movement

# Branch 2: Modal scrolling - INCLUDE modal
elif game.show_inventory or game.show_help or ...:  # And here!
    # Modal stick scrolling
```

### Event vs Polling
- Buttons/D-pad → Send events to modal's `handle_input()` for timing
- Stick → Poll and call methods directly (timing in analog handler)

## ARCHITECTURE

**Event Flow:**
1. SDL events → TCOD event loop → rsp.core.loop → input_handler
2. input_handler determines context → gamepad_handler converts to action
3. _execute_action() routes to context handler → executes game logic

**Polling Flow (auto-repeat):**
1. rsp.core.loop checks stick/D-pad every frame
2. analog_handler.get_left_stick_movement() checks timing
3. Direct modal navigation (bypasses action system)

## DEBUG CHECKLIST

When gamepad input doesn't work:
1. Check events reach handler (log in handle_button_event())
2. Check _execute_action() is called (log context handlers)
3. Check renderer availability (log `self.renderer is not None`)
4. Check modal object retrieval (log menu object after `_get_or_create_*()`)
5. Check polling is active (log entering polling branches)
6. Check method names with hasattr() - don't assume they match!

## WORKING PATTERNS

### Achievements Screen (Direct Scroll)
```python
if game.show_achievements:
    movement = analog_handler.get_left_stick_movement()
    if movement and movement[1] != 0:
        dy = movement[1]
        achievements_menu = game.achievements_menu
        if dy < 0:  # Up
            achievements_menu.scroll_offset = max(0, achievements_menu.scroll_offset - 1)
        else:  # Down
            max_scroll = max(0, len(all_lines) - achievements_menu.max_visible_lines)
            achievements_menu.scroll_offset = min(max_scroll, achievements_menu.scroll_offset + 1)
```

### Help Screen (Hybrid Event + Polling)
- **D-pad/buttons**: Event-based via `help_menu.handle_input(event)`
- **Left stick**: Polling via `help_menu._previous_page()` / `_next_page()`
- Why: Events fire once (no auto-repeat), stick must be polled

### Method Name Checks
GraphicalHelpMenu vs HelpMenu have different methods:
```python
if hasattr(help_menu, '_previous_page'):
    help_menu._previous_page()
elif hasattr(help_menu, '_navigate_page'):
    help_menu._navigate_page(-1)
```

### For Menus: Use Direct Polling, NOT Analog Handler
- Analog handler: Gameplay (turn-based, higher threshold)
- Direct polling: Menus (time-based auto-repeat, 0.3 = 30% threshold)

## TCOD EVENT CONSTRUCTORS (FOR TESTS)

Controller events REQUIRE `type` and `which` parameters:

```python
# ControllerButton
event = tcod.event.ControllerButton(
    type="CONTROLLERBUTTONDOWN",  # Required!
    which=0,  # Controller ID - Required!
    button=tcod.sdl.joystick.ControllerButton.DPAD_UP,
    pressed=True
)

# ControllerAxis
event = tcod.event.ControllerAxis(
    type="CONTROLLERAXISMOTION",  # Required!
    which=0,  # Controller ID - Required!
    axis=tcod.sdl.joystick.ControllerAxis.LEFTY,
    value=32767  # Full deflection
)
```

**Axis ranges:** Sticks: -32768 to 32767, Triggers: 0 to 32767
**For tests:** Use full deflection (±32767) for reliable detection
**Threshold:** `abs(event.value) > 10000` (~30% deflection)

## FILE LOCATIONS

- Actions: `rsp.input.actions` (InputAction enum, InputContext enum)
- Mappings: `rsp.input.mappings` (InputMapper, default key/button bindings)
- Base handler: `rsp.input.base` (BaseInputHandler abstract class)
- Gamepad handler: `rsp.input.gamepad` (GamepadInputHandler)
- Analog processing: `rsp.input.analog` (AnalogStickHandler)
- Coordinate conversion: `rsp.input.coordinates` (InputCoordinateConverter)
- Main input handler: `rsp.input.handler` (InputHandler, context routing)
- Gameplay handling: `rsp.input.gameplay` (GameplayInputHandler)
- Modal handling: `rsp.input.modals` (InventoryInputHandler, etc.)
- Polling loop: `rsp.core.loop` (handle_menu_navigation)

## TEST STRUCTURE

**Main test files:**
- `tests/integration/test_input_*.py` - Screen-specific tests (12 files)
- `tests/integration/test_gamepad_end_to_end.py` - Full E2E tests
- `tests/unit/test_gamepad_handler.py` - Unit tests
- `tests/integration/input_test_utils.py` - Test helpers (InputTestHelper, AutoRepeatTester)

**Coverage:** ~790 input/gamepad tests (100% screen coverage, all input types)
**Runtime:** ~9-10s with pytest-xdist

```bash
# Test specific screen
pytest tests/integration/test_input_main_menu.py -v

# Test all input
pytest tests/integration/test_input_*.py --no-cov

# Test gamepad E2E
pytest tests/integration/test_gamepad_end_to_end.py -v
```

## NEXT TIME GAMEPAD BREAKS

1. Check if pattern matches achievements (it works)
2. Check renderer passed to InputHandler
3. Check polling conditionals - is modal excluded/included correctly?
4. Add debug logging - check actual values, don't assume!
5. Check method names with hasattr() - GraphicalHelpMenu vs HelpMenu differ
6. Remember: Same problem, same solution - check what worked before!
