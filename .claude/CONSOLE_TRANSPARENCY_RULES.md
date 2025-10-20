# Console Transparency Rules (Graphics Mode)

## 🚨 MANDATORY CHECKLIST - READ BEFORE TOUCHING TRANSPARENCY CODE 🚨

**Every single time you write code involving console.rgba:**

1. ✓ **Console Order Check**: Does the game use `order='F'`? (YES - see game_loop.py:347)
2. ✓ **Indexing Check**: With `order='F'`, use `console.rgba["bg"][x, y, 3]` (NOT `[y, x]`!)
3. ✓ **Use CoordinateHelpers**: ALWAYS use `CoordinateHelpers.set_alpha_region()` - it handles order detection automatically!
4. ✓ **Array Shape**: With `order='F'`, `console.rgba["bg"].shape[:2]` gives `(width, height)` NOT `(height, width)`!

**See `.claude/TCOD_COORDINATE_SYSTEMS.md` for complete explanation of console order!**

**Common Trap:**
```python
# ✗ WRONG - assumes default order (uses [y, x] indexing)
for y in range(height):
    for x in range(width):
        console.rgba["bg"][y, x, 3] = 0  # BUG: game uses order='F'!

# ✓ CORRECT - use CoordinateHelpers (detects order automatically)
CoordinateHelpers.set_alpha_region(console, x=0, y=0, width=width, height=height, alpha=0)

# ✓ CORRECT - manual with order detection
is_fortran = (console.rgba["bg"].shape[0] == console.width)
if is_fortran:
    for x in range(width):
        for y in range(height):
            console.rgba["bg"][x, y, 3] = 0
else:
    for y in range(height):
        for x in range(width):
            console.rgba["bg"][y, x, 3] = 0
```

---

## THE PROBLEM

In graphics mode, the console is rendered as a texture on top of SDL sprites. To make sprites visible, we set the game area background to transparent using:

```python
console.rgba["bg"][y, x, 3] = 0  # Alpha = 0 (transparent)
```

**CRITICAL ISSUE**: When you render text/boxes with `bg=Colors.BLACK`, this sets the RGB values to `(0, 0, 0)` but **DOES NOT SET THE ALPHA CHANNEL**. If alpha was previously set to 0, the background remains transparent even though it's "black".

## THE SOLUTION

### Option 1: Use CoordinateHelpers (RECOMMENDED)

**ALWAYS prefer using CoordinateHelpers.set_alpha_region()** - it handles all the complexity for you:

```python
from game_coordinate_helpers import CoordinateHelpers

# Calculate box dimensions
console_width = console.width
console_height = console.height
box_width = min(60, console_width - 4)
box_height = 12
center_x = console_width // 2
center_y = console_height // 2
box_x = center_x - box_width // 2
box_y = center_y - box_height // 2

# Render dialogue box
draw_bordered_box(console, box_x, box_y, box_width, box_height, border_color, bg_color)
# ... render text ...

# CRITICAL: Set alpha to 255 (opaque) using CoordinateHelpers
# This handles [y,x] indexing, bounds clamping, and array shape checking automatically
CoordinateHelpers.set_alpha_region(console, x=box_x, y=box_y,
                                   width=box_width, height=box_height,
                                   alpha=255)
```

**Benefits**:
- ✓ Handles [y, x] vs [x, y] indexing internally
- ✓ Automatically clamps to array bounds (no crashes)
- ✓ Uses actual array shape, not console.width/height
- ✓ One line instead of 10+ lines of loop code
- ✓ Same code works everywhere (dialogues, menus, game area)

### Option 2: Manual Alpha Setting (For Understanding)

If you need to set alpha manually (e.g., debugging, special cases):

```python
# Get actual console dimensions (CRITICAL - don't use GameConfig!)
console_width = console.width
console_height = console.height

# Calculate box dimensions
box_width = min(60, console_width - 4)
box_height = 12
center_x = console_width // 2
center_y = console_height // 2
box_x = center_x - box_width // 2
box_y = center_y - box_height // 2

# Render dialogue box
draw_bordered_box(console, box_x, box_y, box_width, box_height, border_color, bg_color)
# ... render text ...

# CRITICAL: Explicitly set alpha to 255 (opaque)
# Use ACTUAL array shape, NOT console.width/height (they can be different!)
actual_height, actual_width = console.rgba["bg"].shape[:2]
y_start = max(0, box_y)
y_end = min(actual_height, box_y + box_height)
x_start = max(0, box_x)
x_end = min(actual_width, box_x + box_width)

for y in range(y_start, y_end):
    for x in range(x_start, x_end):
        console.rgba["bg"][y, x, 3] = 255  # TCOD uses [y, x] indexing!
```

## KEY POINTS

1. **RGB ≠ RGBA**: Setting `bg=Colors.BLACK` only sets RGB (0,0,0), not alpha
2. **TCOD Indexing**: Console arrays use `[y, x]` order (like numpy), NOT `[x, y]`!
3. **Order Matters**:
   - ✓ Set game area transparent → Render dialogue → Set dialogue opaque
   - ✗ Render dialogue → Set game area transparent (makes dialogue transparent!)
4. **All Dialogues**: Every dialogue renderer must set alpha=255 after rendering
5. **CRITICAL - Use Array Shape, NOT console.width/height!**
   - `console.width` and `console.height` are LOGICAL dimensions
   - The actual underlying array might be a DIFFERENT size!
   - **ALWAYS use**: `actual_height, actual_width = console.rgba["bg"].shape[:2]`
   - Example: `console.width` might report 54, but array is actually 50x50
6. **Clamp iteration ranges**: Always clamp to the ACTUAL array dimensions
   - ✗ `for y in range(box_y, box_y + box_height):` ← Can exceed array bounds
   - ✓ `for y in range(max(0, box_y), min(actual_height, box_y + box_height)):` ← Safe

## WHERE THIS APPLIES

All dialogues now use the **UnifiedRenderer** from `game_dialogue_system.py`:
- Victory dialogues
- Gateway dialogues (auto-show, no confirmation needed)
- Death dialogues
- Overclock warning dialogues
- Inventory attack warning dialogues
- ANY popup/overlay in graphics mode

The UnifiedRenderer uses CoordinateHelpers.set_alpha_region() internally, so individual dialogue renderers don't need to worry about alpha management.

## The "Make Everything Transparent First" Pattern

**Best practice for graphics mode rendering:**

### The Pattern:
1. Clear console (sets alpha=255 by default)
2. **Make ENTIRE console transparent**: `console.rgba["bg"][:, :, 3] = 0`
3. Render text/graphics (doesn't change alpha)
4. **Explicitly set alpha=255 for areas that should be opaque** (UI panels, dialogues)

### Why This Works:
- `console.draw_rect()` and `console.print()` set RGB values but **DO NOT SET ALPHA**
- Making everything transparent first ensures a clean slate
- Then explicitly setting alpha=255 for opaque areas is more reliable
- Simpler than trying to make only certain areas transparent

### Example:
```python
# 1. Clear console
console.clear()

# 2. Make ENTIRE console transparent FIRST (use CoordinateHelpers!)
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                    width=console.width, height=console.height, alpha=0)

# 3. Render UI
render_status_bar(console)
render_panels(console)

# 4. Set UI areas back to opaque (use CoordinateHelpers!)
CoordinateHelpers.set_alpha_region(console, x=0, y=0, width=console.width, height=1, alpha=255)  # Top bar
CoordinateHelpers.set_alpha_region(console, x=0, y=45, width=console.width, height=5, alpha=255)  # Bottom panel

# 5. Render dialogue (sets its own alpha to 255)
if dialogue_active:
    UnifiedRenderer.render(console, dialogue)
```

## RENDERING ORDER (game_rendering_core.py)

```python
from game_coordinate_helpers import CoordinateHelpers
from game_dialogue_system import UnifiedRenderer

# 1. Clear console (alpha=255 by default)
console.clear()

# 2. Make ENTIRE console transparent FIRST (critical pattern)
console.rgba["bg"][:, :, 3] = 0

# 3. Render UI elements
self.ui_renderer.render_top_status_bar(console, game)
self.ui_renderer.render_bottom_panel(console, game)
self.ui_renderer.render_system_log(console, game)

# 4. Set UI areas back to opaque
# Top status bar (y=0)
console.rgba["bg"][0, :, 3] = 255
# Bottom panel (y >= PANEL_Y)
console.rgba["bg"][GameConfig.PANEL_Y():, :, 3] = 255
# System log (x >= GAME_AREA_WIDTH)
console.rgba["bg"][:, GameConfig.GAME_AREA_WIDTH():, 3] = 255

# 5. Render dialogues - UnifiedRenderer sets alpha=255 for dialogue area
if game.dialogue_state.is_active():
    dialogue = game.dialogue_state.get_active()
    UnifiedRenderer.render(console, dialogue)  # Sets alpha=255 internally
```

## COMMON MISTAKES

1. **Using console.width/height instead of array shape for bounds checking**
   ```python
   # ✗ WRONG - console.width might not match array size!
   for x in range(0, console.width):
       console.rgba["bg"][y, x, 3] = 255  # CRASH if array smaller!

   # ✓ CORRECT - use actual array dimensions
   actual_height, actual_width = console.rgba["bg"].shape[:2]
   for x in range(0, actual_width):
       console.rgba["bg"][y, x, 3] = 255
   ```

2. **Wrong array indexing**
   ```python
   # ✗ WRONG - will cause index out of bounds
   console.rgba["bg"][x, y, 3] = 255

   # ✓ CORRECT - TCOD uses [y, x] order
   console.rgba["bg"][y, x, 3] = 255
   ```

3. **Not clamping iteration ranges**
   ```python
   # ✗ WRONG - will crash if box extends beyond console
   for y in range(box_y, box_y + box_height):
       for x in range(box_x, box_x + box_width):
           if 0 <= x < console_width:  # Too late!
               console.rgba["bg"][y, x, 3] = 255

   # ✓ CORRECT - clamp the range itself
   y_start = max(0, box_y)
   y_end = min(console_height, box_y + box_height)
   for y in range(y_start, y_end):  # Never exceeds bounds
       for x in range(x_start, x_end):
           console.rgba["bg"][y, x, 3] = 255
   ```

4. **Rendering dialogue before transparency pass**
   ```python
   # ✗ WRONG - dialogue becomes transparent
   render_dialogue()  # Sets alpha to 255
   set_game_area_transparent()  # Overwrites alpha to 0!

   # ✓ CORRECT - transparency pass first
   set_game_area_transparent()
   render_dialogue()  # Sets alpha to 255 AFTER
   ```

## DEBUGGING

If a dialogue appears transparent:
1. Check if alpha is being set to 255 AFTER rendering
2. Verify using `[y, x]` indexing, not `[x, y]`
3. Ensure the alpha-setting loop covers the entire dialogue box area
4. Check that nothing sets alpha to 0 AFTER the dialogue is rendered

If you get "index out of bounds" errors:
1. **FIRST**: Check if you're using `console.rgba["bg"].shape[:2]` for bounds, NOT `console.width/height`
2. Verify you're using `[y, x]` indexing, not `[x, y]`
3. Print actual array shape: `print(f"Array shape: {console.rgba['bg'].shape}, console.width={console.width}")`
4. Check if dialogue box calculation exceeds actual array bounds
