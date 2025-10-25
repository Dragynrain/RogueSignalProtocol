# TCOD Graphics & Rendering Guide

Complete reference for working with python-tcod in this project, covering coordinate systems, transparency, and common patterns.

---

## 🚨 THE #1 THING TO REMEMBER: Array Indexing

**CRITICAL**: TCOD console arrays use `[y, x]` indexing, which is opposite from function parameters!

### Quick Reference

```python
# Console creation (game_loop.py:336)
console = tcod.console.Console(80, 50)

# Array shape: (50, 80, 4) = (height, width, channels)
# Array indexing: console.rgba["bg"][y, x, channel]  ← NOTE: [y, x]!

# But function calls use (x, y):
console.print(x=10, y=5, "text")  ← NOTE: (x, y)!
```

**The Rule**: Function parameters use `(x, y)`, but direct array access uses `[y, x]`. Use CoordinateHelpers to avoid confusion!

---

## Part 1: Coordinate Systems

### Overview: Three Different Coordinate Systems

**DO NOT MIX THESE!**

1. **Console Character Coordinates** (80x50 grid)
   - Used for: Text rendering, UI layout
   - Range: X: 0-79, Y: 0-49
   - Example: `console.print(x=10, y=5, "text")`

2. **Game Viewport Coordinates** (27x21 in graphics mode)
   - Used for: In-game map tile positions
   - Scaled based on viewport to fit window
   - TileManager calculates pixel dimensions (e.g., 65x54 per tile)

3. **SDL Pixel Coordinates** (window resolution, e.g., 2560x1351)
   - Used for: Direct SDL sprite rendering
   - Full window pixel space
   - Must align with console texture

### TCOD Functions Always Use (x, y)

**Good news**: High-level TCOD functions always use `(x, y)` regardless of console memory order!

```python
# These ALWAYS use (x, y) order - safe!
console.print(x=10, y=5, "text")
console.draw_rect(x=10, y=5, width=20, height=10, ...)
console.draw_frame(x=10, y=5, width=20, height=10, ...)
```

### Direct Array Access Uses [y, x]!

**Danger zone**: When accessing `.rgba`, `.ch`, `.fg`, `.bg` arrays, use `[y, x]` indexing!

```python
# ✓ CORRECT - Use CoordinateHelpers (handles indexing internally)
from game_coordinate_helpers import CoordinateHelpers
CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=255)

# ✓ CORRECT - Manual with proper [y, x] indexing
for y in range(5, 20):
    for x in range(10, 40):
        console.rgba["bg"][y, x, 3] = 255  # [y, x] order!

# ✗ WRONG - Using [x, y] indexing
console.rgba["bg"][x, y, 3] = 255  # BUG! Transposed coordinates!
```

### Why [y, x]?

TCOD uses numpy arrays with standard row-major (C) order:
- Shape is `(height, width, channels)` = `(rows, columns, channels)`
- Standard numpy indexing: `array[row, col]` = `array[y, x]`
- Function calls use `(x, y)` because that's the cartesian convention
- This mismatch is why we have CoordinateHelpers!

---

## Part 2: Mouse Coordinate Conversion

### ⚠️ Why We Can't Use `context.convert_event()`

**IMPORTANT**: This game uses TCOD's official **`tcod.render.SDLConsoleRender`** API to composite multiple layers (sprites + console UI). This pattern requires bypassing `context.present()` and directly using SDL rendering. Since `context.convert_event()` **requires `context.present()` to establish coordinate transformation state**, it cannot be used with manual SDL rendering.

Therefore, we use **manual pixel-to-tile conversion** for all mouse handling.

**Technical Details:**
- `context.convert_event()` depends on `lib.TCOD_ctx.engine` internal state
- This state is ONLY updated when `context.present()` is called
- The game uses `tcod.render.SDLConsoleRender` for multi-layer compositing:
  - Layer 1: High-resolution sprite textures (backgrounds, gameplay sprites)
  - Layer 2: Console texture with transparency (UI overlays)
  - Final: `sdl_renderer.present()` (not `context.present()`)
- This is the **official TCOD pattern** for mixing SDL graphics with console rendering

**Why Multi-Layer Rendering:**
- Graphics mode uses high-res PNG backgrounds (1920x1080+)
- Sprites render at viewport-scaled resolution (e.g., 97x80 pixels per tile)
- Console provides text/UI overlay with alpha transparency
- Can't use `context.present()` because it clears SDL content before rendering

### Manual Conversion (Required for This Game)

**For all console-based UI** (menus, dialogues, inventory, help screens):

```python
# In event loops (game_loop.py)
for event in tcod.event.wait():
    # Manually convert pixel coordinates to tile coordinates
    if hasattr(event, 'position') and event.position:
        window_w, window_h = context.sdl_window.size
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )
        # Create new event with tile coordinates
        import copy
        event = copy.copy(event)
        event.position = type(event.position)(tile_x, tile_y)

# In handlers (game_input.py, game_menus.py)
def handle_mouse_click(self, event):
    if not hasattr(event, 'position') or event.position is None:
        return False
    tile_x, tile_y = event.position  # Already converted to console coords in event loop
    # Use tile_x, tile_y for console-based hit detection
```

**Why Manual Conversion:**
- Using `tcod.render.SDLConsoleRender` for multi-layer compositing
- Bypasses `context.present()` (which would clear sprite layers)
- `context.convert_event()` requires `context.present()` to work
- Manual conversion is simple: `pixel / (window_size / console_size) = tile`

**How It Works:**
- `event.position` initially contains pixel coordinates from SDL
- We manually convert to tile coordinates using window dimensions
- Copy the event and replace position with tile coordinates
- Handlers receive events with tile coordinates in `.position`

### Custom Conversion for Graphics Mode Gameplay

**For world coordinates in graphics mode only:**

```python
def _mouse_tile_to_world(self, event):
    """Convert mouse event to world coordinates."""
    graphics_mode = self.game.settings.graphics_mode

    if graphics_mode == "graphics":
        # Graphics mode: Use sprite grid conversion
        tile_x, tile_y = CoordinateHelpers.pixel_to_sprite_grid(
            event.position.x, event.position.y,
            self.renderer.tile_manager.tile_width,
            self.renderer.tile_manager.tile_height
        )
    else:
        # Glyph mode: Manually convert pixel coordinates
        window_w, window_h = self._get_window_dimensions()
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )

    # Then convert to world coordinates with camera offset
    viewport_x = tile_x
    viewport_y = tile_y - status_bar_height
    world_x = viewport_x + camera_x
    world_y = viewport_y + camera_y
    return Position(world_x, world_y)
```

**When to use custom conversion:**
- Gameplay mouse clicks (move player, targeting, look mode)
- In graphics mode where sprites use custom pixel dimensions
- When converting console/viewport coords to world coords with camera

**Do NOT use custom conversion for:**
- Menus, dialogues, inventory (use `event.tile` directly)
- Glyph mode console UI (use `event.tile` directly)

### Migration From Manual Conversion

**Old approach** (manual conversion - DEPRECATED):
```python
# ❌ DON'T DO THIS ANYMORE
window_w, window_h = context.sdl_window.size
tile_x = int(event.position.x / (window_w / 80))
tile_y = int(event.position.y / (window_h / 50))
```

**New approach** (Manual conversion for stretched rendering):
```python
# ✅ DO THIS INSTEAD
window_w, window_h = context.sdl_window.size
tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
    event.position.x, event.position.y, window_w, window_h
)
```

**Why Not `context.convert_event()`:**
- `convert_event()` requires `context.present()` to update coordinate state
- This game uses `tcod.render.SDLConsoleRender` for multi-layer compositing
- Cannot use `context.present()` because it clears SDL sprite layers
- Manual conversion is necessary and works correctly with SDL rendering

---

## Part 3: Console Transparency (Graphics Mode)

### The Problem

In graphics mode, the console is rendered as a texture on top of SDL sprites. To make sprites visible:

1. Set game area background to transparent: `console.rgba["bg"][:, :, 3] = 0`
2. Render text/UI elements
3. **CRITICAL**: Set UI areas back to opaque: `alpha = 255`

**Why?** TCOD's `console.print()` and `console.draw_rect()` set RGB values but **DO NOT SET ALPHA**!

If alpha was previously 0 (transparent), rendering text with `bg=Colors.BLACK` will still be transparent.

### The Solution: Use UnifiedRenderer

**99% of dialogue rendering should use UnifiedRenderer!**

```python
from game_dialogue_system import UnifiedRenderer

# UnifiedRenderer handles transparency automatically
if dialogue_state.is_active():
    dialogue = dialogue_state.get_active()
    UnifiedRenderer.render(console, dialogue)  # Sets alpha=255 internally
```

**Benefits**:
- Handles alpha channel automatically
- Uses CoordinateHelpers internally (handles order detection)
- Works with all dialogue types
- One line of code instead of manual alpha management

### Manual Transparency (Advanced Cases)

Only use if UnifiedRenderer can't handle your use case:

```python
from game_coordinate_helpers import CoordinateHelpers

# 1. Make console transparent
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                    width=console.width, height=console.height,
                                    alpha=0)

# 2. Render UI elements
console.print(x=10, y=5, string="Status", fg=(255,255,255), bg=(0,0,0))

# 3. Set UI area back to opaque
CoordinateHelpers.set_alpha_region(console, x=9, y=4, width=20, height=3, alpha=255)
```

### The "Transparent First" Pattern

Best practice for graphics mode rendering:

```python
# 1. Clear console (alpha=255 by default)
console.clear()

# 2. Make ENTIRE console transparent FIRST
console.rgba["bg"][:, :, 3] = 0

# 3. Render UI
render_status_bar(console)
render_panels(console)

# 4. Set UI areas back to opaque
# Top bar (y=0)
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                    width=console.width, height=1, alpha=255)
# Bottom panel
CoordinateHelpers.set_alpha_region(console, x=0, y=45,
                                    width=console.width, height=5, alpha=255)

# 5. Render dialogues (UnifiedRenderer sets its own alpha)
if dialogue_active:
    UnifiedRenderer.render(console, dialogue)
```

---

## Part 4: Graphics Rendering Coordinate Systems

### Menu/Help Screens

Console is ALWAYS 80x50 characters. For sprite rendering:

**Sprite POSITIONING**: Convert console coords to pixels
```python
# Get window size
window_width, window_height = context.sdl_window.size

# Calculate pixels per console character
pixels_per_char_x = window_width / 80
pixels_per_char_y = window_height / 50

# Convert console position to pixel position
pixel_x = int(console_x * pixels_per_char_x)
pixel_y = int(console_y * pixels_per_char_y)
```

**Sprite SIZE**: Use TileManager dimensions (same as in-game!)
```python
sprite_width = tile_manager.tile_width   # e.g., 65 pixels
sprite_height = tile_manager.tile_height # e.g., 54 pixels
```

### In-Game Rendering

Use TileManager.tile_width/height for both size AND positioning:
```python
# These dimensions are viewport-scaled (e.g., 65x54 for 2x zoom)
tile_w = tile_manager.tile_width
tile_h = tile_manager.tile_height

# Position and size both use these values
sprite_x = game_x * tile_w
sprite_y = game_y * tile_h
```

### Common Mistakes

❌ Using tileset size (10x16) for sprite SIZE → tiny sprites
❌ Using tile dimensions (65x54) to multiply console coords → wrong positions
❌ Mixing positioning math between menus and in-game rendering

---

## Part 5: CoordinateHelpers - Your Best Friend

**Located in**: `game_coordinate_helpers.py`

### Why Use CoordinateHelpers?

✓ Automatically detects console order (`order='F'` vs default)
✓ Uses correct indexing based on detected order
✓ Handles bounds clamping (no crashes!)
✓ One line instead of 10+ lines of manual code
✓ Same code works in game AND tests

### Main Functions

```python
from game_coordinate_helpers import CoordinateHelpers

# Set alpha for a region
CoordinateHelpers.set_alpha_region(
    console,
    x=10, y=5,
    width=30, height=15,
    alpha=255  # 0 = transparent, 255 = opaque
)

# Center a box on console
box_x, box_y = CoordinateHelpers.center_box(
    console_width=80,
    console_height=50,
    box_width=40,
    box_height=20
)
```

### How It Works

```python
# CoordinateHelpers uses standard [y, x] indexing internally:
for row in range(y_start, y_end):
    for col in range(x_start, x_end):
        console.rgba["bg"][row, col, 3] = alpha
```

**You don't have to write this every time - just call CoordinateHelpers!**

---

## Part 6: Common Bugs & How to Avoid Them

### Bug 1: Wrong Array Indexing

```python
# ✗ WRONG - using [x, y] instead of [y, x]
for y in range(height):
    for x in range(width):
        console.rgba["bg"][x, y, 3] = 255  # BUG! Transposed!

# ✓ CORRECT - use CoordinateHelpers
CoordinateHelpers.set_alpha_region(console, x=0, y=0, width=width, height=height, alpha=255)
```

### Bug 2: Dialogue Stays Transparent

**Symptom**: Dialogue box text visible but background is transparent

**Cause**: Alpha not set to 255 after rendering

**Fix**: Use UnifiedRenderer or manually set alpha:
```python
# After rendering dialogue box
CoordinateHelpers.set_alpha_region(console, x=box_x, y=box_y,
                                    width=box_width, height=box_height,
                                    alpha=255)
```

### Bug 3: Index Out of Bounds

**Symptom**: Crash with "index X is out of bounds for axis Y"

**Cause**: Using `console.width/height` instead of actual array shape

**Fix**: CoordinateHelpers handles this automatically! It uses actual array dimensions.

### Bug 4: Mixing Coordinate Systems

```python
# ✗ WRONG - using game tile dimensions for menu sprite positioning
pixel_x = console_x * tile_manager.tile_width  # BUG!

# ✓ CORRECT - calculate from window scaling
pixel_x = int(console_x * (window_width / 80))
```

---

## Part 7: Testing Considerations

**Both game and tests use default TCOD consoles**

When writing tests:
- Always use standard `[y, x]` indexing for array access
- Use `(x, y)` for function parameters
- CoordinateHelpers handles the conversion automatically

Example test:
```python
def test_dialogue_transparency():
    # Create console (same as game)
    console = tcod.console.Console(80, 50)

    # Use CoordinateHelpers (handles [y, x] internally)
    CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=0)

    # Verify using [y, x] indexing
    assert console.rgba["bg"][5, 10, 3] == 0  # [y=5, x=10]
```

---

## Part 8: Quick Decision Tree

```
What are you doing?

├─ Calling console.print() or console.draw_*()
│  └─ Use (x, y) order - you're safe!
│
├─ Rendering dialogues/popups
│  └─ Use UnifiedRenderer - handles everything!
│
├─ Setting transparency/alpha
│  └─ Use CoordinateHelpers.set_alpha_region() - handles order detection!
│
├─ Positioning sprites on menus
│  └─ Calculate: pixel_pos = console_pos * (window_size / console_size)
│
└─ Direct array access (advanced)
   └─ Use [y, x] indexing: console.rgba["bg"][y, x, 3]
```

---

## Part 9: See Also

- **CLAUDE.md** - General project guidelines
- **skills/tcod.md** - Complete TCOD API reference (FOV, pathfinding, events)
- **game_coordinate_helpers.py** - CoordinateHelpers implementation
- **game_dialogue_system.py** - UnifiedRenderer implementation
- **game_rendering_core.py** - Main rendering pipeline

---

## Summary: The Golden Rules

1. **ALWAYS use CoordinateHelpers** for array access
2. **Use UnifiedRenderer** for dialogues
3. **Function parameters use (x, y)**, **array indexing uses [y, x]**
4. **TCOD functions use (x, y)** - only direct array access needs [y, x]
5. **When in doubt**, use the helpers - they handle everything!
