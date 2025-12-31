# Mouse Coordinate Handling - Post-Mortem & Best Practices

## Critical Understanding: Two Different Systems

**This game has TWO distinct mouse coordinate systems:**

### 1. **Menu/UI Coordinates** (Console Tiles)
- **What**: Console character grid (80×50)
- **Used by**: Main menu, settings, graphics preview, help screens, achievements
- **Returns**: Tile position (0-79, 0-49)
- **Tool**: `MenuMouseHandler.convert_to_tile_coords()`
- **File**: `src/rsp/utils/mouse.py`

### 2. **World Coordinates** (Game Map)
- **What**: Position on game map (50×50 in this game)
- **Used by**: In-game clicks, targeting, look mode, movement
- **Returns**: World position (0-49, 0-49) or None
- **Tool**: `InputCoordinateConverter.pixel_to_world_position()`
- **File**: `src/rsp/input/coordinates.py`

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

Use `MenuMouseHandler` from `rsp.utils.mouse`:

```python
from rsp.utils.mouse import MenuMouseHandler

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

Use `InputCoordinateConverter.pixel_to_world_position()` from `rsp.input.coordinates`:

```python
from rsp.input.coordinates import InputCoordinateConverter

# In game input handling:
world_pos = InputCoordinateConverter.pixel_to_world_position(
    event.pixel.x, event.pixel.y,
    renderer, game, graphics_mode, camera_offset
)
if world_pos:
    # world_pos is Position(x, y) on game map
    game.move_to(world_pos.x, world_pos.y)
```

**Why these are separate:**
- Menu coordinates are simple (pixel → console tile)
- World coordinates are complex (pixel → viewport → camera offset → world → validation)
- World conversion needs game state (camera, map bounds, viewport config)
- They're fundamentally different operations

## Implementation Details

**MenuMouseHandler (rsp.utils.mouse):**
- Converts pixel → console tile (0-79, 0-49)
- Simple and stateless - no game state needed

**InputCoordinateConverter.pixel_to_world_position (rsp.input.coordinates):**
- Converts pixel → world position (0-49, 0-49)
- Complex and stateful - needs graphics mode, camera offset, map bounds, viewport config
- Used by input handlers in `rsp.input.gameplay` and `rsp.input.modals`

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
from rsp.utils.mouse import MenuMouseHandler

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

See `rsp.input.gameplay` and `rsp.input.modals` for examples - use `InputCoordinateConverter.pixel_to_world_position()`

## Key Takeaways

1. **Read `.claude/TCOD_GUIDE.md` first** - documentation already exists!
2. **Never use `context.convert_event()`** - doesn't work with our rendering
3. **Two systems, two tools**:
   - Menu/UI: `MenuMouseHandler.convert_to_tile_coords()`
   - World: `InputCoordinateConverter.pixel_to_world_position()`
4. **Always use `event.tile`** after conversion (not `event.position`)
5. **Test thoroughly** - mouse events are tricky

## Prevention Checklist

**Before adding mouse support:**
- [ ] Read `.claude/TCOD_GUIDE.md` section "Mouse Coordinate Conversion"
- [ ] Determine if you need menu or world coordinates
- [ ] Use the appropriate tool (`MenuMouseHandler` vs `InputCoordinateConverter.pixel_to_world_position`)

**When reviewing PRs with mouse support:**
- [ ] Uses correct conversion tool for the context?
- [ ] Reads from `event.tile` (not `event.position`)?
- [ ] Has basic testing with actual mouse clicks?
- [ ] Works in both glyph and graphics modes (if applicable)?

## Files Modified During Graphics Preview Fix

**What was fixed:**
- `rsp.core.loop` - Manual coordinate conversion in graphics preview loop
- `rsp.ui.menu_graphics_preview` - Mouse handlers using event.tile, arrow region tracking

**What was created:**
- `rsp.utils.mouse` - Menu mouse coordinate conversion utility
- `.claude/MOUSE_COORDINATE_HANDLING.md` - This post-mortem document
