# TCOD Project-Specific Patterns

**For generic python-tcod knowledge:** Invoke the `tcod` skill.
**This doc covers:** Project-specific TCOD patterns, CoordinateHelpers, and rendering architecture.

---

## Critical: Array Indexing

**TCOD console arrays use `[y, x]` indexing, opposite from function parameters!**

```python
# Console creation
console = tcod.console.Console(80, 50)

# Array shape: (50, 80, 4) = (height, width, channels)
console.rgba["bg"][y, x, channel]  # [y, x] order!

# But function calls use (x, y):
console.print(x=10, y=5, "text")  # (x, y) order!
```

**Always use CoordinateHelpers** to avoid confusion - it handles the ordering internally.

---

## Critical: Pathfinding Returns Include Starting Position

**TCOD's `Pathfinder.path_to()` includes the starting position as the first element!**

```python
# Common mistake:
pathfinder = tcod.path.Pathfinder(graph)
pathfinder.add_root((player_x, player_y))
path = pathfinder.path_to((target_x, target_y))

next_x, next_y = path[0]  # BUG: This is the starting position!
dx = next_x - player_x    # dx = 0, dy = 0 → no movement!
dy = next_y - player_y
```

**Correct approach (this codebase):**

```python
# Use (y, x) order for TCOD pathfinding!
pathfinder.add_root((player_y, player_x))
path = pathfinder.path_to((target_y, target_x))

# Check path length - path[0] is starting position
if len(path) > 1:
    # Skip starting position (path[0]) - use path[1] for first move
    next_y, next_x = path[1]  # Remember: TCOD returns (y, x)
    dx = next_x - player_x
    dy = next_y - player_y
```

**Why this happens:** `path_to()` returns the full path including start → step1 → step2 → ... → goal. Many pathfinding libraries only return the steps (excluding start), but TCOD includes it.

**This codebase's approach:** Instead of filtering, we check `len(path) > 1` and access `path[1]` directly. See `rsp.level.pathfinding` for the actual implementation.

**Symptom if you get this wrong:** Movement fails silently - entities stay at starting position forever, trying to "move" with dx=0, dy=0.

---

## Critical: Pathfinding Uses (y, x) Coordinates

**TCOD's pathfinding functions use (y, x) order, NOT (x, y)!**

```python
# WRONG - will path through walls!
pathfinder.add_root((player_x, player_y))  # X
path = pathfinder.path_to((target_x, target_y))  # X

# CORRECT - swap to (y, x)
pathfinder.add_root((player_y, player_x))  # OK
path = pathfinder.path_to((target_y, target_x))  # OK

# Path output is also (y, x), need to swap back
next_y, next_x = path[1]  # OK (skip starting position at path[0])
dx = next_x - player_x
dy = next_y - player_y
```

**Why:** TCOD's pathfinding matches numpy array indexing [y, x], unlike most function calls which use (x, y).

**Symptom if you get this wrong:** Pathfinder returns paths through walls! It treats X as Y and Y as X, so it's navigating a transposed/rotated map.

---

## Three Coordinate Systems

**DO NOT MIX THESE!**

1. **Console Character Coordinates** (80x50 grid)
   - Text rendering, UI layout
   - Range: X: 0-79, Y: 0-49
   - Example: `console.print(x=10, y=5, "text")`

2. **Game Viewport Coordinates** (27x21 in graphics mode)
   - In-game map tile positions
   - Scaled based on viewport to fit window
   - TileManager calculates pixel dimensions (e.g., 65x54 per tile)

3. **SDL Pixel Coordinates** (window resolution, e.g., 2560x1351)
   - Direct SDL sprite rendering
   - Full window pixel space
   - Must align with console texture

---

## Mouse Coordinate Conversion

### Why We Can't Use `context.convert_event()`

**This game uses `tcod.render.SDLConsoleRender`** for multi-layer compositing:
- Layer 1: High-resolution sprite textures (backgrounds, gameplay sprites)
- Layer 2: Console texture with transparency (UI overlays)
- Final: `sdl_renderer.present()` (NOT `context.present()`)

**Problem:** `context.convert_event()` requires `context.present()` to update coordinate state. We can't use `context.present()` because it clears SDL sprite layers before rendering.

### Manual Conversion (Required)

**For console-based UI** (menus, dialogues, inventory):
```python
# In event loops (rsp.core.loop)
for event in tcod.event.wait():
    if hasattr(event, 'position') and event.position:
        window_w, window_h = context.sdl_window.size
        tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
            event.position.x, event.position.y, window_w, window_h
        )
```

**For gameplay in graphics mode:**
```python
# Graphics mode: Use sprite grid conversion
tile_x, tile_y = CoordinateHelpers.pixel_to_sprite_grid(
    event.position.x, event.position.y,
    tile_manager.tile_width,
    tile_manager.tile_height
)

# Then convert to world coordinates with camera offset
world_x = tile_x + camera_x
world_y = tile_y + camera_y - status_bar_height
```

---

## Console Transparency (Graphics Mode)

### The Problem

In graphics mode, console is rendered as texture on top of SDL sprites. TCOD's `console.print()` and `console.draw_rect()` **DO NOT SET ALPHA**!

If alpha was previously 0 (transparent), rendering text with `bg=Colors.BLACK` will still be transparent.

### Solution: Use UnifiedRenderer

**99% of dialogue rendering should use UnifiedRenderer:**
```python
from rsp.ui.dialogue import UnifiedRenderer

if dialogue_state.is_active():
    dialogue = dialogue_state.get_active()
    UnifiedRenderer.render(console, dialogue)  # Handles alpha automatically
```

**Benefits:**
- Handles alpha channel automatically
- Uses CoordinateHelpers internally
- Works with all dialogue types

### Manual Transparency (Advanced)

Only use if UnifiedRenderer can't handle your use case:
```python
from rsp.rendering.coordinates import CoordinateHelpers

# 1. Make console transparent
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                    width=console.width, height=console.height,
                                    alpha=0)

# 2. Render UI elements
console.print(x=10, y=5, string="Status", fg=(255,255,255), bg=(0,0,0))

# 3. Set UI area back to opaque
CoordinateHelpers.set_alpha_region(console, x=9, y=4, width=20, height=3, alpha=255)
```

---

## CoordinateHelpers Reference

### Core Functions

```python
from rsp.rendering.coordinates import CoordinateHelpers

# Set alpha for a region (handles [y, x] ordering)
CoordinateHelpers.set_alpha_region(
    console, x=10, y=5, width=30, height=15, alpha=255
)

# Convert pixel coords to console character coords
tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
    pixel_x, pixel_y, window_w, window_h
)

# Convert pixel coords to sprite grid (graphics mode)
tile_x, tile_y = CoordinateHelpers.pixel_to_sprite_grid(
    pixel_x, pixel_y, tile_width, tile_height
)

# Center a box on screen
box_x, box_y = CoordinateHelpers.center_box(
    console.width, console.height, box_width, box_height
)
```

### Why Use CoordinateHelpers?

**Problem:** Direct array access mixes (x,y) and [y,x] indexing:
```python
# WRONG - Easy to mess up [y, x] vs (x, y)
for y in range(height):
    for x in range(width):
        console.rgba["bg"][y, x, 3] = 255  # Must remember [y, x]!
```

**Solution:** CoordinateHelpers uses function params (x, y) consistently:
```python
# CORRECT - Always (x, y) order
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                    width=width, height=height, alpha=255)
```

---

## Quick Reference

**For TCOD API questions:** Invoke the `tcod` skill
**For array access:** Use CoordinateHelpers
**For mouse events:** Manual conversion (see above)
**For transparency:** Use UnifiedRenderer or CoordinateHelpers
**For multi-layer rendering:** See RENDERING_ARCHITECTURE.md
