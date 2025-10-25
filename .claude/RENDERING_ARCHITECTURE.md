# Rendering Architecture Documentation

This document explains the multi-layer rendering architecture and why the game uses `tcod.render.SDLConsoleRender` instead of `context.present()`.

---

## Overview: Multi-Layer Rendering

The game uses **TCOD's official `tcod.render` module** to composite multiple rendering layers in a single frame:

```
Layer 1: High-Resolution Backgrounds
         ↓
Layer 2: High-Resolution Sprites
         ↓
Layer 3: Console UI Overlay (with transparency)
         ↓
Final Frame
```

**Key Implementation** (see `game_loop.py:86-91`):
```python
from tcod import render as tcod_render
atlas = tcod_render.SDLTilesetAtlas(context.sdl_renderer, tileset)
console_render = tcod_render.SDLConsoleRender(atlas)
context.console_render = console_render
```

This is the **official TCOD API** for mixing SDL graphics with console rendering.

---

## Why Not Use `context.present()`?

### The Standard Approach (Console-Only Games)
```python
# Works for ASCII-only roguelikes
console.clear()
console.print(x=10, y=5, string="@", fg=(255,255,255))
context.present(console)  # Renders and displays console
```

### Why This Game Can't Use It

**Problem**: `context.present()` clears the SDL backbuffer before rendering.

From SDL documentation:
> "The backbuffer should be considered invalidated after each present"

**What this means:**
```python
# This DOESN'T work:
renderer.copy(background_texture)  # Render background
renderer.copy(sprite_texture)      # Render sprites
context.present(console)           # ← CLEARS everything above!
```

**Our solution:**
```python
# This DOES work (using tcod.render):
renderer.copy(background_texture)           # Layer 1: Background
renderer.copy(sprite_texture)               # Layer 2: Sprites
console_texture = console_render.render(console)  # Layer 3: Console to texture
renderer.copy(console_texture)              # Composite console
renderer.present()                          # Display final frame
```

---

## Multi-Layer Rendering Details

### Layer 1: High-Resolution Backgrounds (Menu Only)

**Implementation**: `game_menu_background.py`

**What it does:**
- Loads random PNG backgrounds (1920x1080 or higher resolution)
- 25 available cyberpunk-themed images
- Renders directly to SDL with aspect ratio preservation

**Code:**
```python
# Load PNG as SDL texture
from PIL import Image
pil_image = Image.open("main_menu/main_menu_1.png")
pixels = np.array(pil_image, dtype=np.uint8)
background_texture = renderer.upload_texture(pixels)

# Render to SDL
renderer.copy(background_texture, dest=bg_rect)
```

**Why SDL texture (not console)?**
- Full window resolution (2560x1440, 1920x1080, etc.)
- Much higher quality than console character grid (80x50)
- Professional appearance for main menu

---

### Layer 2: High-Resolution Sprites (Gameplay)

**Implementation**: `game_rendering_graphics.py`

**What it does:**
- Renders all gameplay sprites at viewport-scaled resolution
- Example: At 2x zoom, each tile is 97x80 pixels
- Includes terrain, items, enemies, player

**Code:**
```python
# Sprites are pre-loaded as SDL textures
texture = tile_manager.get_tile("player")  # 97x80 pixel texture
tile_rect = (pixel_x, pixel_y, 97, 80)
renderer.copy(texture, dest=tile_rect)
```

**Why SDL sprites (not console glyphs)?**
- Viewport-scaled to fit window dimensions
- Much smoother visuals than 10x16 tileset glyphs
- Allows tinting, transparency effects
- Professional graphics quality

**Sprite resolution calculation:**
```python
# For 2560x1440 window with 27x21 viewport:
tile_width = 2560 / 27 = 94.8 → 97 pixels
tile_height = (1440 - status_bar) / 21 = 80 pixels
```

---

### Layer 3: Console UI Overlay

**Implementation**: All UI modules

**What it does:**
- Renders all text-based UI using standard TCOD console
- Status bars, dialogue boxes, menus, inventory
- Uses 80x50 character grid

**Code:**
```python
# Render to console normally
console.clear()
console.print(x=10, y=0, string="HP: 100", fg=(255,255,255))

# Make game area transparent (so sprites show through)
CoordinateHelpers.set_alpha_region(console, x=0, y=1,
                                   width=80, height=27, alpha=0)

# Set UI areas opaque
CoordinateHelpers.set_alpha_region(console, x=0, y=0,
                                   width=80, height=1, alpha=255)

# Convert console to SDL texture
console_texture = context.console_render.render(console)

# Composite over sprites
context.sdl_renderer.copy(console_texture)
```

**Why console overlay (not pure SDL text)?**
- Consistent with glyph mode rendering
- Leverages all TCOD console features (print, draw_frame, etc.)
- Single UI codebase for both modes
- Alpha transparency allows sprites to show through

---

## Complete Rendering Pipeline

### Graphics Mode Rendering (`game_rendering_core.py:206-267`)

```python
# Setup
context.sdl_renderer.draw_color = (0, 0, 0, 255)
context.sdl_renderer.clear()

# === LAYER 1: Background (menu only) ===
if menu_background:
    menu_background.render_background(console)

# === LAYER 2: Sprites ===
graphics_renderer.render_sprites_layer(game)
graphics_renderer.render_status_effects_layer(game)
graphics_renderer.render_overlay_layer(game)

# === LAYER 3: Console UI ===
console.clear()

# Make entire console transparent first
CoordinateHelpers.set_alpha_region(console, 0, 0, 80, 50, alpha=0)

# Render UI panels
ui_renderer.render_top_status_bar(console, game)
ui_renderer.render_bottom_panel(console, game)

# Set UI areas opaque
CoordinateHelpers.set_alpha_region(console, 0, 0, 80, 1, alpha=255)
CoordinateHelpers.set_alpha_region(console, 0, 45, 80, 5, alpha=255)

# Convert console to texture and composite
console_texture = context.console_render.render(console)
context.sdl_renderer.copy(console_texture)

# === PRESENT FINAL FRAME ===
context.sdl_renderer.present()
```

### Glyph Mode Rendering

```python
# Much simpler - just use context.present()
console.clear()
# Render everything to console (terrain, entities, UI)
context.present(console)
```

---

## Mouse Coordinate Handling

### The Problem

`context.convert_event()` depends on internal state that's ONLY updated by `context.present()`:

```python
# From python-tcod source
def convert_event(self, event):
    # Uses lib.TCOD_ctx.engine for coordinate transformation
    # This is ONLY set when context.present() is called
    return converted_event
```

Since we use `sdl_renderer.present()` instead of `context.present()`, the coordinate transformation state is never established.

### The Solution

Manual pixel-to-tile conversion:

```python
# In event loop (game_loop.py)
window_w, window_h = context.sdl_window.size
tile_x, tile_y = CoordinateHelpers.pixel_to_char_coords(
    event.position.x, event.position.y, window_w, window_h
)

# CoordinateHelpers implementation
pixels_per_tile_x = window_width / console_width   # e.g., 2560 / 80 = 32
pixels_per_tile_y = window_height / console_height  # e.g., 1440 / 50 = 28.8
tile_x = int(pixel_x / pixels_per_tile_x)
tile_y = int(pixel_y / pixels_per_tile_y)
```

**This is necessary and correct** - not a workaround!

---

## Why This Architecture?

### Advantages ✅

1. **Multi-layer compositing**
   - Backgrounds + sprites + UI in single frame
   - Professional visual quality

2. **High-resolution graphics**
   - PNG backgrounds at native resolution
   - Sprites at viewport-scaled resolution
   - Much better than console-only rendering

3. **Consistent UI across modes**
   - Same console-based UI in glyph and graphics modes
   - Single codebase for all UI elements
   - Easy to maintain

4. **Official TCOD pattern**
   - Uses `tcod.render.SDLConsoleRender` as intended
   - Following documented best practices
   - Not a hack or workaround

5. **Performance**
   - Efficient SDL texture caching
   - Only updates changed console regions
   - Smooth 60 FPS rendering

### Disadvantages ❌

1. **Manual mouse coordinate conversion**
   - ~85 lines of conversion code
   - Must maintain in multiple event loops
   - Can't use `context.convert_event()`

2. **More complex rendering pipeline**
   - Three layers to manage
   - Alpha transparency management
   - More potential for bugs

**The tradeoff is heavily in favor** of the current approach. Manual coordinate conversion is simple and well-abstracted, while multi-layer rendering provides huge visual quality benefits.

---

## Alternative Approaches Considered

### Option 1: Use `context.present()` Only

**Change required:**
- Remove all SDL backgrounds (25 PNG images)
- Remove all SDL sprites (97x80 pixel tiles)
- Use ASCII glyphs only

**Result:**
- Mouse events would work with `context.convert_event()` ✅
- Lose all high-resolution graphics ❌
- Lose modern graphics mode entirely ❌
- Massive visual downgrade ❌

**Verdict:** Not viable. Graphics mode is core feature.

---

### Option 2: Eliminate Console in Graphics Mode

**Change required:**
- Remove console/tileset from graphics mode
- Implement custom text rendering (SDL_ttf or PIL)
- Rewrite all UI modules (~15 files)

**Estimated effort:**
- ~1200+ lines of new text rendering code
- ~30-40 hours of development
- Extensive testing burden

**Technical challenges:**
- Need font manager, text layout engine
- Word wrapping, alignment, line spacing
- Two completely different UI codebases
- **Still need manual mouse conversion** (no console = no `convert_event()`)

**Result:**
- Prettier TrueType fonts ✅
- Inconsistent with glyph mode ❌
- Massive development effort ❌
- Doesn't solve mouse conversion problem ❌
- High maintenance burden ❌

**Verdict:** Not worth it. Huge effort for minimal benefit.

---

### Option 3: Current Approach (CHOSEN)

**What we have:**
- `tcod.render.SDLConsoleRender` for multi-layer compositing
- High-res backgrounds and sprites in graphics mode
- Console-based UI in both modes
- Manual mouse coordinate conversion

**Advantages:**
- Official TCOD pattern ✅
- Professional graphics quality ✅
- Consistent UI across modes ✅
- Simple coordinate conversion ✅
- Well-tested and stable ✅

**Disadvantages:**
- ~85 lines of manual conversion code ❌
- Can't use `context.convert_event()` ❌

**Verdict:** Best approach. Small code cost for huge visual benefit.

---

## Key Learnings

1. **`tcod.render.SDLConsoleRender` is the official TCOD API** for mixing SDL graphics with console rendering

2. **`context.convert_event()` requires `context.present()`** to work - this is a fundamental TCOD limitation, not a bug

3. **Multi-layer rendering requires manual SDL compositing** - you cannot use `context.present()` when mixing SDL textures with console

4. **Manual coordinate conversion is simple and correct** - not a workaround, but the proper approach for this architecture

5. **The current architecture follows TCOD best practices** - from official documentation and community patterns

---

## References

- **TCOD Render Module**: https://python-tcod.readthedocs.io/en/latest/tcod/render.html
- **TCOD Context**: https://python-tcod.readthedocs.io/en/latest/tcod/context.html
- **SDL Rendering**: https://python-tcod.readthedocs.io/en/latest/sdl/render.html

**From TCOD documentation:**
> "The tcod.render module allows you to render a console to an SDL Texture directly, letting you have full control over how consoles are displayed, including rendering multiple tilesets in a single frame and rendering consoles on top of each other."

> "For sprite-based rendering it can be useful to use an alternative library for graphics rendering while continuing to use python-tcod's pathfinding and field-of-view algorithms."

---

## See Also

- `.claude/TCOD_GUIDE.md` - Complete TCOD rendering guide
- `.claude/CLAUDE.md` - Graphics coordinate systems (Section 7b)
- `game_loop.py:86-91` - Console renderer initialization
- `game_rendering_core.py:206-267` - Multi-layer rendering pipeline
- `game_coordinate_helpers.py` - Coordinate conversion utilities
