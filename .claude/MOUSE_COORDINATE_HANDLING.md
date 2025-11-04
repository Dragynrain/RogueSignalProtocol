# Mouse Coordinate Handling - Post-Mortem & Best Practices

## Critical Understanding: Two Different Systems

**This game has TWO distinct mouse coordinate systems:**

### 1. **Menu/UI Coordinates** (Console Tiles)
- **What**: Console character grid (80×50)
- **Used by**: Main menu, settings, graphics preview, help screens, achievements
- **Returns**: Tile position (0-79, 0-49)
- **Tool**: `MenuMouseHandler.convert_to_tile_coords()`
- **File**: `game_mouse_utils.py`

### 2. **World Coordinates** (Game Map)
- **What**: Position on game map (100×100 in this game)
- **Used by**: In-game clicks, targeting, look mode, movement
- **Returns**: World position (0-99, 0-99) or None
- **Tool**: `InputHandler._mouse_pixel_to_world()`
- **File**: `game_input.py`

**These are fundamentally different operations and should NOT be unified.**

---

## What Went Wrong: Graphics Preview Mouse Clicks

### The Problem
Adding mouse support to Graphics Preview took multiple debugging sessions because:
1. Clicks weren't registering at all
2. When they did register, coordinates were always `(0, 0)`
3. Tried to use `context.convert_event()` which is unreliable
4. Didn't check existing documentation in `.claude/TCOD_GUIDE.md`

### Root Causes

#### 1. **Didn't Read Existing Documentation**
`.claude/TCOD_GUIDE.md` lines 48-84 already explained:
- Why `context.convert_event()` doesn't work
- That manual conversion is required
- Exact code examples for both menu and world coordinates

**Lesson: Always search `.claude/` directory for existing guidance before debugging!**

#### 2. **TCOD API Limitation**
- `context.convert_event()` requires `context.present()` to update coordinate state
- This game uses `sdl_renderer.present()` for multi-layer rendering
- Therefore `context.convert_event()` cannot track coordinates properly
- See `.claude/RENDERING_ARCHITECTURE.md` for why we use SDL rendering

#### 3. **Multiple Coordinate Attribute Names**
- `event.pixel`: Raw pixel coordinates from SDL
- `event.position`: Sometimes used by TCOD (inconsistent)
- `event.tile`: Where we manually store converted coordinates
- **Use `event.tile` after manual conversion**

## The Solutions That Work

### For Menu/UI Coordinates

Use `MenuMouseHandler` from `game_mouse_utils.py`:

```python
from game_mouse_utils import MenuMouseHandler

# In menu event loop:
for event in tcod.event.get():
    if event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
        event = MenuMouseHandler.convert_to_tile_coords(event, context)
        if event is None:
            continue

    if event.type == "MOUSEBUTTONDOWN":
        tile_x, tile_y = event.tile
        # Now use tile coordinates (0-79, 0-49)
```

### For World Coordinates

Use `InputHandler._mouse_pixel_to_world()` (already exists):

```python
# In game input handling:
world_pos = self._mouse_pixel_to_world(event.pixel.x, event.pixel.y)
if world_pos:
    # world_pos is Position(x, y) on game map
    self.game.move_to(world_pos.x, world_pos.y)
```

**Why these are separate:**
- Menu coordinates are simple (pixel → console tile)
- World coordinates are complex (pixel → viewport → camera offset → world → validation)
- World conversion needs game state (camera, map bounds, viewport config)
- They're fundamentally different operations

## Implementation Details

### Menu Coordinate Conversion (game_mouse_utils.py)

**Internals:**
- Gets `event.pixel` (x, y in pixels)
- Gets window size from `context.sdl_window.size`
- Calls `CoordinateHelpers.pixel_to_char_coords()`
- Returns new event with `event.tile` set to console tile coordinates

**Simple and stateless** - no game state needed.

### World Coordinate Conversion (game_input.py)

**Internals:**
1. Gets graphics mode (glyph vs graphics)
2. Converts pixel → viewport coordinates:
   - Graphics mode: Uses `pixel_to_sprite_grid()` with tile dimensions
   - Glyph mode: Uses `pixel_to_char_coords()`
3. Subtracts status bar height
4. Adds camera offset (from `game.last_camera_offset`)
5. Validates against map bounds
6. Returns world Position or None

**Complex and stateful** - needs game instance, renderer, camera position.

## Why Not Unified?

Attempting to unify these would require:

```python
# Hypothetical unified API - NOT RECOMMENDED
MouseHandler.convert(
    event,
    context,
    mode="world",  # or "menu"
    graphics_mode=None,
    renderer=None,
    camera_offset=None,
    map_bounds=None,
    viewport_config=None,
    status_bar_height=None
)
```

That's **8 parameters** for world conversion! And you'd only use world conversion in one place (InputHandler).

**Keep them separate** because:
- Menu conversion: Simple utility (like string formatting)
- World conversion: Complex operation needing game state (like database query)
- They're used in different contexts by different code
- Unifying them doesn't provide value

## Testing Checklist

When adding mouse support to a new screen:

- [ ] Clicks register at correct tile coordinates
- [ ] Hover highlighting works correctly
- [ ] Mouse events don't interfere with keyboard
- [ ] Works in both glyph mode and graphics mode
- [ ] Works at different window sizes (if applicable)
- [ ] Test at screen edges (0, 0) and (79, 49)
- [ ] Test with rapid clicking

## Quick Reference

### Adding Mouse Support to a Menu/UI Screen

```python
from game_mouse_utils import MenuMouseHandler

# In your menu event loop:
for event in tcod.event.get():
    if event.type in ("MOUSEMOTION", "MOUSEBUTTONDOWN"):
        event = MenuMouseHandler.convert_to_tile_coords(event, context)
        if event is None:
            continue

    if event.type == "MOUSEMOTION":
        menu.handle_mouse_motion(event)
    elif event.type == "MOUSEBUTTONDOWN":
        action = menu.handle_mouse_click(event)

# In your menu handlers:
def handle_mouse_click(self, event) -> str:
    if not hasattr(event, 'tile') or event.tile is None:
        return ""

    tile_x, tile_y = int(event.tile.x), int(event.tile.y)
    # Now use tile coordinates
```

### Adding Mouse Support to In-Game

See `game_input.py` for examples - use `InputHandler._mouse_pixel_to_world()`

## Key Takeaways

1. 📖 **Read `.claude/TCOD_GUIDE.md` first** - documentation already exists!
2. 🚫 **Never use `context.convert_event()`** - doesn't work with our rendering
3. ✅ **Two systems, two tools**:
   - Menu/UI: `MenuMouseHandler.convert_to_tile_coords()`
   - World: `InputHandler._mouse_pixel_to_world()`
4. ✅ **Always use `event.tile`** after conversion (not `event.position`)
5. ✅ **Test thoroughly** - mouse events are tricky

## Prevention Checklist

**Before adding mouse support:**
- [ ] Read `.claude/TCOD_GUIDE.md` section "Mouse Coordinate Conversion"
- [ ] Determine if you need menu or world coordinates
- [ ] Use the appropriate tool (`MenuMouseHandler` vs `_mouse_pixel_to_world`)

**When reviewing PRs with mouse support:**
- [ ] Uses correct conversion tool for the context?
- [ ] Reads from `event.tile` (not `event.position`)?
- [ ] Has basic testing with actual mouse clicks?
- [ ] Works in both glyph and graphics modes (if applicable)?

## Files Modified During Graphics Preview Fix

**What was fixed:**
- `game_loop.py:320-343` - Manual coordinate conversion in graphics preview loop
- `game_menu_graphics_preview.py:967-1020` - Mouse handlers using event.tile
- `game_menu_graphics_preview.py:822-920` - Arrow region tracking for clickable areas

**What was created:**
- `game_mouse_utils.py` - Menu mouse coordinate conversion utility
- `.claude/MOUSE_COORDINATE_HANDLING.md` - This post-mortem document
