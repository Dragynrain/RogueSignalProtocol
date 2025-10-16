# Graphics Implementation Plan

## Current Status: ✅ Sprites-Only Architecture

**What Works:**
- PNG sprites render correctly (player, enemies, terrain, items)
- TileManager loads/caches/scales sprites with transparency
- Sprites-only rendering: SDL sprites + console UI overlay
- Status effects render as colored outlines over sprites
- Glyph mode (Classic) unchanged and fully functional
- Settings toggle working (graphics/glyph modes)

**Architecture:** Layered SDL Rendering
```
1. Clear SDL → Black background for unexplored areas
2. Render sprites → Terrain + entities as SDL textures
3. Render status effects → Colored outline boxes over sprites
4. Render console → UI panels (top bar, bottom panel, system log)
5. Present → Display final frame
```

---

## Terminology

**User-Facing:**
- "Graphics Mode" = PNG sprites (512x512 scaled to tile size)
- "Classic Mode" = CP437 glyphs (existing character rendering)

**Code/Internal:**
- `graphics_mode = "graphics"` or `"glyph"`
- Both use TCOD + SDL (difference is sprites vs characters)

---

## Critical Lessons Learned

### What NOT To Do:
1. ❌ **GlyphManager Overlay Complexity** - Tried rendering glyphs as individual SDL textures over sprites. Too complex, caused UI panel issues.
2. ❌ **Selective Console Region Copying** - Attempted copying only UI regions of console texture. Complex coordinate math, failed to show UI panels.
3. ❌ **Mixed Rendering Paths** - Trying to render glyphs in game area while rendering UI separately created coordination nightmares.

### The Right Solution: Sprites-Only
- **Game area:** Sprites only (no glyph overlays)
- **UI panels:** Console rendering (works perfectly for text)
- **Missing sprites:** Fallback to glyph mode or create sprite assets
- **Keep it simple:** One rendering path, minimal complexity

### Why GlyphManager Was Removed:
- Added significant complexity (3 files modified, new class, cache management)
- Caused UI panel rendering issues (bottom panel and system log not showing)
- Console texture opacity made mixing sprites + glyphs difficult
- User feedback: "too complex, just do sprites-only"
- **Decision:** Focus on creating proper sprite assets instead of glyph overlays

---

## Implementation Summary

### Phase 0: Terminology Refactor ✅
- Updated "ASCII" → "glyph" in code
- User-facing "ASCII Mode" → "Classic Mode"
- Migration code for old user settings
- 780/783 tests passing

### Phase 1: Foundation ✅
**Files Created:**
- `game_graphics_tiles.py` - TileManager class for sprite loading/caching
- `graphics_tiles.json` - Sprite mapping configuration

**Key Features:**
- PNG loading with PIL, scaling with LANCZOS
- SDL texture upload with transparency (`BlendMode.BLEND`)
- Lazy loading with caching (load on first access)
- Window resize support (recalculate tile dimensions)
- Tintable flag support (not currently used, for future color mods)

### Phase 2: Rendering Integration ✅
**Files Modified:**
- `game_rendering.py` - Layered SDL rendering
- `game_loop.py` - TileManager initialization

**Rendering Flow:**
```python
# Graphics mode:
sdl_renderer.clear()  # Black background
render_sprites_layer()  # Sprites to SDL
render_status_effects_layer()  # Colored outlines
console.clear()  # Clear console for UI
render_ui_panels()  # UI to console
console_texture = console_render.render(console)
sdl_renderer.copy(console_texture)  # Full console overlay
sdl_renderer.present()

# Glyph mode:
console.clear()
render_map_to_console()  # Everything to console
render_ui_to_console()
context.present(console)  # Direct console present
```

**Status Effects:** Colored outline boxes (Layer 2.5)
- Player virus: Green outline (0, 255, 0)
- Enemy states: Yellow/Orange/Red outlines
- Drawn with `draw_rect()` after sprites, before console

### Phase 7: Simplified to Sprites-Only ✅
**Removed:**
- `game_graphics_glyphs.py` (GlyphManager class)
- GlyphManager initialization from game_loop.py
- render_glyphs_layer() call from rendering
- Complex region-based console copying

**Simplified Rendering:**
- Sprites render to SDL (game area)
- Console renders UI panels (full console texture overlay)
- No glyph overlays in game area
- Clean, simple architecture

---

## Missing Sprites - CREATE THESE

### High Priority (Core Gameplay):
1. **Gateway** (`>`) - Level exit portal (currently missing entirely)
2. **Enemies:**
   - All enemy types have sprites, but could use more variants
3. **Items:**
   - Story fragments (`music note`) - currently using glyph
   - Some exploit types may need sprites

### Medium Priority (Special Nodes):
4. **Cooling Nodes** (`♦` cyan diamond) - Overheat recovery
5. **CPU Recovery Nodes** (`♥` red heart) - CPU regeneration
6. **Ghost Nodes** (`♠` purple spade) - Invisibility powerup

### Low Priority (UI/Indicators):
7. **Targeting Cursor** (`X`) - Red X for abilities
8. **Movement Prediction** (`○`) - Circles showing enemy patrol paths
9. **Vision Overlays** - Colored background patterns (can stay as console)

### Notes:
- **Sprite Specs:** 512x512 PNG with transparency
- **Style:** Match existing sprite aesthetic
- **Mapping:** Add to `graphics_tiles.json` after creating
- **Fallback:** Missing sprites will use glyph mode rendering (fallback to Classic mode for that element)

---

## Sprite Mapping Configuration

**File:** `graphics_tiles.json`

**Structure:**
```json
{
  "player": {"file": "player01.png", "tintable": false},
  "enemies": {
    "Scanner": {"file": "scanner01.png", "tintable": false},
    "Patrol": {"file": "patrol01.png", "tintable": false},
    "Bot": {"file": "bot01.png", "tintable": false},
    "Hunter": {"file": "hunter01.png", "tintable": false},
    "Virus": {"file": "virus01.png", "tintable": false},
    "Inhibitor": {"file": "inhibitor01.png", "tintable": false},
    "Firewall": {"file": "firewall01.png", "tintable": false},
    "Avatar": {"file": "avatar01.png", "tintable": false}
  },
  "terrain": {
    "floor": {"file": "floor01.png", "tintable": false},
    "wall": {"file": "wall01.png", "tintable": false}
  },
  "items": {
    "codehack": {"file": "codehack01.png", "tintable": true},
    "exploit_cpu": {"file": "cpu_upgrade01.png", "tintable": false},
    "exploit_cooling": {"file": "cooling_upgrade01.png", "tintable": false},
    "cooling_node": {"file": "cooling_node01.png", "tintable": false},
    "cpu_node": {"file": "cpu_node01.png", "tintable": false},
    "ghost_node": {"file": "ghost_node01.png", "tintable": false},
    "exploit_stealth": {"file": "exploit01.png", "tintable": true}
  }
}
```

**Tintable Flag:** Currently not used. Reserved for future color modulation feature.

---

## Technical Details

### TileManager Key Methods:
- `load_tile(filepath)` - Load PNG, scale to tile size, upload to SDL
- `get_tile(entity_type)` - Get cached texture for entity
- `_calculate_tile_dimensions(window_size)` - Calculate tile pixel size
- `preload_common_tiles()` - Preload player/floor/wall at startup
- `cleanup()` - Free all SDL textures

### Coordinate Conversion:
```python
# Grid → Pixel:
pixel_x = screen_x * tile_width
pixel_y = screen_y * tile_height

# Tile size calculation:
window_width, window_height = sdl_window.size
tile_width = window_width / console.width
tile_height = window_height / console.height
```

### Status Effect Rendering:
```python
def _draw_outline_box(renderer, rect, color, thickness):
    # Convert RGB to RGBA (SDL requires 4 values)
    if len(color) == 3:
        color_rgba = (*color, 255)
    renderer.draw_color = color_rgba

    # Draw outline (not filled)
    for offset in range(thickness):
        expanded_rect = expand_rect(rect, offset)
        renderer.draw_rect(expanded_rect)
```

---

## File Organization

### New Files:
- `game_graphics_tiles.py` (~450 lines) - TileManager sprite loading system
- `graphics_tiles.json` (~80 lines) - Sprite configuration

### Modified Files:
- `game_rendering.py` (+200 lines) - Layered SDL rendering
- `game_loop.py` (+30 lines) - TileManager initialization
- `validate_json_config.py` (+50 lines) - Tile mapping validation

**Total:** ~810 lines new/modified code

---

## Future Enhancements (Out of Scope)

**Not Implemented (But Architecture Supports):**
1. Zoom levels - Different tile sizes
2. Animated sprites - Frame sequences
3. Color tinting - Dynamic sprite coloring (tintable flag reserved)
4. Graphical UI - Sprite-based menus/panels
5. Dynamic lighting - Glow effects, shadows
6. Particle effects - Explosions, trails
7. Sprite atlases - Combined texture sheets for performance

---

## Testing Status

**Completed:**
- TileManager initialization ✅
- Sprite loading with transparency ✅
- Graphics mode rendering ✅
- Glyph mode unchanged ✅
- Settings toggle ✅
- Window resize support ✅

**Remaining:**
- Full gameplay playthrough in graphics mode
- Create missing sprite assets
- Performance profiling with many sprites
- Memory usage monitoring

---

## Success Criteria

✅ Graphics mode renders PNG sprites for configured entities
✅ Glyph/classic mode fully functional and unchanged
✅ Settings toggle works and persists
✅ Sprites render with proper transparency
✅ Status effects show as colored outlines
✅ UI panels render correctly
⬜ All missing sprites created (gateway, nodes, cursor, etc.)
⬜ Full playthrough tested in both modes
⬜ No performance issues observed

---

## Quick Reference: Adding New Sprites

1. **Create sprite:** 512x512 PNG with transparency
2. **Add to graphics_tiles.json:**
   ```json
   "entity_name": {"file": "sprite01.png", "tintable": false}
   ```
3. **Test in-game:** Launch graphics mode, verify sprite loads
4. **Fallback:** If sprite missing, element won't render (no automatic glyph fallback)

---

## Current Issues: NONE

Graphics rendering working correctly with sprites-only architecture. UI panels render properly. No known bugs.

**Next Steps:**
1. Create missing sprite assets (gateway, special nodes, etc.)
2. Test full playthrough in graphics mode
3. Performance testing if needed
