# Rendering Architecture

Multi-layer rendering using TCOD's `tcod.render.SDLConsoleRender` to composite sprites and console UI.

---

## Layer Structure

```
Layer 1: High-Resolution Backgrounds (SDL textures)
         ↓
Layer 2: High-Resolution Sprites (SDL textures)
         ↓
Layer 3: Console UI Overlay (with transparency)
         ↓
Final Frame
```

**Implementation** (game_loop.py:86-91):
```python
from tcod import render as tcod_render
atlas = tcod_render.SDLTilesetAtlas(context.sdl_renderer, tileset)
console_render = tcod_render.SDLConsoleRender(atlas)
context.console_render = console_render
```

This is the **official TCOD API** for mixing SDL graphics with console rendering.

---

## Why Not `context.present()`?

**Problem:** `context.present()` clears the SDL backbuffer before rendering, destroying sprite layers.

**Solution:** Use `tcod.render.SDLConsoleRender` to convert console to texture, then composite all layers with `renderer.present()`.

---

## Layer Details

### Layer 1: High-Resolution Backgrounds (Menu Only)

**Implementation:** `game_menu_background.py`

- Loads random PNG backgrounds (1920x1080+)
- 25 available cyberspace-themed images
- Renders directly to SDL with aspect ratio preservation

```python
# Load PNG as SDL texture
from PIL import Image
pil_image = Image.open("main_menu/main_menu_1.png")
pixels = np.array(pil_image, dtype=np.uint8)
background_texture = renderer.upload_texture(pixels)
renderer.copy(background_texture, dest=bg_rect)
```

**Why SDL texture?**
- Full window resolution (2560x1440, 1920x1080, etc.)
- Much higher quality than 80x50 console grid
- Professional appearance for main menu

### Layer 2: High-Resolution Sprites (Gameplay)

**Implementation:** `game_rendering_graphics.py`

**Graphics mode tile dimensions:**
- Viewport: 27x21 tiles
- Tile size: ~65x54 pixels (scales to window)
- Total: ~1755x1134 pixels for game area

**Sprite rendering:**
```python
# Load sprite as SDL texture
texture = tile_manager.get_tile("player")
tile_rect = _get_tile_rect(screen_x, screen_y)
renderer.copy(texture, dest=tile_rect)
```

**Why high-resolution?**
- Professional pixel art (32x32 source images)
- Scales smoothly to any window size
- Supports tinting/color modulation for damage feedback

### Layer 3: Console UI Overlay

**Implementation:** `game_rendering_ui.py`

**Console rendered as transparent texture:**
- Full 80x50 character grid
- Text/UI elements with alpha transparency
- Rendered on top of sprites in graphics mode

**Critical:** See TCOD_GUIDE.md for transparency handling!

---

## Coordinate Systems

**Three different systems - DO NOT MIX:**

1. **Console chars (80x50)** - Text/UI
2. **Game viewport (27x21)** - In-game tiles
3. **SDL pixels** - Sprite rendering

**Sprite positioning:**
```python
# Convert console coords to pixel coords
pixel_x = console_x * (window_width / 80)
pixel_y = console_y * (window_height / 50)

# Get tile dimensions
tile_width = tile_manager.tile_width
tile_height = tile_manager.tile_height

# Create rect for sprite
tile_rect = (pixel_x, pixel_y, tile_width, tile_height)
```

See TCOD_GUIDE.md for coordinate conversion details.

---

## Key Takeaways

1. **Multi-layer rendering requires `tcod.render.SDLConsoleRender`**
2. **Cannot use `context.present()` - it clears sprite layers**
3. **Console transparency handled manually** (see TCOD_GUIDE.md)
4. **Three coordinate systems** - convert carefully
5. **This is the official TCOD pattern** for mixing graphics and console

---

## Related Docs

- **TCOD_GUIDE.md** - CoordinateHelpers, transparency, mouse conversion
- **game_rendering_core.py** - Main rendering pipeline
- **game_rendering_graphics.py** - SDL sprite rendering
- **game_rendering_glyphs.py** - Console text rendering
