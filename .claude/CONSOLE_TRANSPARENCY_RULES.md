# Console Transparency Rules (Graphics Mode)

## 🚨 MANDATORY CHECKLIST - READ BEFORE TOUCHING TRANSPARENCY CODE 🚨

**Every single time you write code involving console.rgba:**

1. ✓ **Indexing Check**: Is it `console.rgba["bg"][y, x, 3]`? (NOT `[x, y]`!)
2. ✓ **Loop Order**: Outer loop = y? Inner loop = x? Indexing = `[y, x]`?
3. ✓ **Variable Names**: When iterating, are loop variables named correctly?
   - `for y in range(...): for x in range(...): rgba[y, x]` ✓
   - `for x in range(...): for y in range(...): rgba[x, y]` ✗
4. ✓ **Array Shape**: Getting dimensions from `console.rgba["bg"].shape[:2]` gives `(height, width)` = `(y_max, x_max)`

**Common Trap:**
```python
# ✗ WRONG - creates TRANSPOSED transparency!
for x in range(width):
    for y in range(height):
        console.rgba["bg"][x, y, 3] = 0  # BUG: should be [y, x]

# ✓ CORRECT
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

**After rendering ANY dialogue/popup**, you MUST explicitly set the alpha channel to 255 for the entire dialogue area:

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

- Victory message (`render_victory_message`)
- Gateway confirmation (`render_gateway_confirmation`)
- Death message (`render_death_message`)
- Generic dialogues (`render_dialogue`)
- ANY popup/overlay in graphics mode

## RENDERING ORDER (game_rendering_core.py)

```python
# 1. Render UI elements to console
self.ui_renderer.render_top_status_bar(console, game)
self.ui_renderer.render_bottom_panel(console, game)

# 2. Set game area to transparent
for x in range(GameConfig.GAME_AREA_WIDTH()):
    for y in range(1, GameConfig.PANEL_Y()):
        console.rgba["bg"][y, x, 3] = 0  # Note: [y, x] order!

# 3. Render dialogues AFTER transparency pass
# Dialogues will set their own alpha to 255 internally
if game.dialogue_manager.is_active():
    self.dialogue_renderer.render_dialogue(console, game)
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
