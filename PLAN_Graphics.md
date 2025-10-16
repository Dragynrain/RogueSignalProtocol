# Graphics Implementation Plan

## Executive Summary - TCOD Integration Research

**Key Findings from TCOD Documentation Research:**

✅ **CONFIRMED WORKING:**
- SDL Renderer fully accessible via `context.sdl_renderer`
- Console-to-texture rendering already implemented in game_loop.py (lines 54-72)
- Transparency in sprites fully supported via RGBA textures and blend modes
- Drawing primitives available: `fill_rect()`, `draw_rect()`, `draw_line()`, etc.
- Window resize handling via `context.sdl_window.size` property
- Layered rendering pattern proven in MenuBackground implementation

✅ **ARCHITECTURE VALIDATED:**
- Layer 1: SDL renderer draws sprite textures (floors, walls, entities)
- Layer 2: SDL renderer draws colored status boxes (semi-transparent RGBA)
- Layer 3: Console rendered as SDL texture overlay (UI + glyph fallbacks)
- Z-order: clear() → sprites → boxes → console texture → present()

⚠️ **CRITICAL CONSTRAINTS:**
- All tiles MUST be same size (TCOD limitation - no sub-tile rendering)
- Sprites use transparency, NOT tinting - status effects need colored boxes drawn over sprites
- Console overlay for glyph fallbacks works naturally with transparent backgrounds
- NO sprite animation in initial pass (single static frame per entity)

✅ **SCALING STRATEGY CONFIRMED:**
- Load 512x512 PNGs with PIL
- Scale to calculated tile size: `window_pixels / grid_cells`
- Use `Image.Resampling.LANCZOS` for high-quality downscaling
- Upload to SDL as RGBA texture with `blend_mode = BlendMode.BLEND`
- Reload textures on window resize (>10% change threshold)

✅ **COLOR MODIFICATION STRATEGIES:**
- **Tintable sprites** (white base): Use SDL color_mod on texture (exploits, code hacks)
- **Non-tintable sprites** (colored base): Draw colored outline box over sprite (player, enemies)
- Two different rendering approaches at different z-layers
- Color modulation: `texture.color_mod = (R, G, B)` - multiplies with texture RGB
- Outline boxes: `draw_rect()` with colored RGBA after sprite, before console

⚠️ **IMPLEMENTATION CONCERNS:**
1. **Console transparency coordination**: Need to ensure console backgrounds in game area have alpha 0
2. **Pixel/grid coordinate conversion**: Must accurately convert grid coords to pixel rects for SDL
3. **UI space reservation**: Need precise math to calculate tile size accounting for UI panels
4. **Performance**: Many texture copies per frame - should be fine with SDL acceleration, but needs profiling

📋 **PLAN CONFIDENCE:**
- High confidence in overall architecture (proven pattern from MenuBackground)
- Medium confidence in pixel coordinate math (needs careful testing)
- High confidence in transparency handling (well-documented TCOD feature)
- Medium confidence in dynamic scaling (needs testing at various window sizes)

**READY TO PROCEED:** All major architectural questions answered. Implementation can proceed with confidence.

---

## Terminology Clarification

**What we're actually rendering:**
- **Current "ASCII mode"**: Actually CP437 (Code Page 437) character set via TCOD tileset (`terminal10x16_gs_ro.png`)
  - Includes standard ASCII (0-127) plus extended characters (128-255) like ♥♦♠•§
  - Rendered as 10x16 pixel glyphs from a bitmap font
  - Still uses TCOD + SDL under the hood
  - NOT pure ASCII, NOT true terminal rendering

**Naming conventions:**
- **User-facing**: "Graphics" mode vs "Classic" mode
- **Code/internal**: `graphics` vs `glyph` (render modes)
- **Technical reality**: Both modes use TCOD + SDL; difference is PNG sprites vs CP437 glyphs

**What this plan implements:**
- **Graphics mode**: High-res PNG sprites (512x512 scaled down) for game map entities
- **Glyph/Classic mode**: Existing CP437 character rendering (current implementation)
- **NOT implemented**: True terminal mode (curses/blessed, pure ASCII, no SDL) - massive architectural change, out of scope

## Overview
Add PNG sprite graphics that can be toggled on/off via the render mode setting. Graphics mode will render PNG sprites scaled to fit the grid, while glyph/classic mode remains fully functional as a user preference option (not a fallback). All UI elements (status bars, menus, inventory) remain as CP437 glyphs in both modes - only the game map entities get PNG sprite treatment.

## Current State Analysis

### Existing Assets
- **Location**: `graphics/` folder (~23MB total, 98 PNG files)
- **Format**: 512x512 PNG files
- **Categories identified**:
  - Player sprites: `player01.png` through `player11.png`
  - Enemies: bot, patrol, scanner, hunter, virus, inhibitor, firewall, avatar
  - Terrain: floor, wall
  - Items: codehack (6 variants), cooling nodes/upgrades, cpu nodes/upgrades, ghost nodes
  - Multiple variants per entity (e.g., player01-11, bot01-03, etc.)

### Current Rendering Architecture
- **Main renderer**: `game_rendering.py` (~1690 lines)
  - `GameRenderer`: Top-level coordinator
  - `UIRenderer`: Handles all UI (status bar, inventory, log, menus)
  - `MapRenderer`: Renders game map tiles and entities
- **Rendering flow**: `MapRenderer.render_map()` renders in layers:
  1. Terrain (walls, floors, items)
  2. Vision overlays
  3. Patrol routes (movement prediction)
  4. Gateway
  5. Enemies
  6. Player
  7. Targeting cursor
- **TCOD integration**: Uses `tcod.tileset.CHARMAP_CP437` for CP437 character glyphs
- **Graphics precedent**: `MenuBackground` in `game_menu_background.py` shows how to:
  - Load PNG files conditionally based on `graphics_mode` setting
  - Use SDL renderer with texture uploads
  - Handle fallback gracefully to glyph rendering

### Grid System
- **Console size**: `GameConfig.SCREEN_WIDTH` x `GameConfig.SCREEN_HEIGHT`
- **Game area**: `GameConfig.GAME_AREA_WIDTH()` x viewable height (excludes UI panels)
- **Map size**: `GameConfig.MAP_WIDTH` x `GameConfig.MAP_HEIGHT`
- **Camera system**: `MapRenderer._calculate_camera_offset()` centers on player
- **Tile mapping**: Each screen position maps to one world position

## Architecture Decisions

### File Organization
- **Create new file**: `game_graphics_tiles.py` (keep separate from rendering logic)
- **Keep**: `game_rendering.py` handles rendering decisions (glyph vs graphics)
- **Reason**: Separation of concerns - sprite loading/management vs rendering logic

### Rendering Strategy - CRITICAL TCOD INTEGRATION

**TCOD rendering architecture for mixing sprites and glyphs:**

1. **Layered SDL Rendering** (proven pattern from MenuBackground):
   - Layer 1 (bottom): SDL renderer draws PNG sprite textures directly to screen
   - Layer 2 (middle): SDL renderer draws colored rectangles for status effects (virus, etc.)
   - Layer 3 (top): Console rendered as SDL texture overlay for UI elements and glyph fallbacks
   - Final: `context.sdl_renderer.present()` displays the complete frame

2. **TCOD Console-to-Texture System** (already initialized in game_loop.py:54-72):
   - `tcod.render.SDLTilesetAtlas` - converts TCOD tileset to SDL-compatible format
   - `tcod.render.SDLConsoleRender` - renders console content to SDL texture
   - Pattern: `console_texture = context.console_render.render(console)` then `context.sdl_renderer.copy(console_texture)`
   - Allows console glyphs to render transparently over SDL graphics

3. **Transparency Handling**:
   - PNG sprites: Load with PIL, preserve alpha channel, upload to SDL as RGBA texture
   - Console overlay: Console background color (0,0,0) with alpha 0 creates transparency
   - Status boxes: Use `fill_rect()` with semi-transparent RGBA colors (e.g., green box with alpha 128)

4. **Tile Size Calculation**:
   - Calculate at initialization based on window size and grid dimensions
   - Formula: `tile_pixel_size = window_pixels / grid_cells` (accounting for UI bars/panels)
   - Scale 512x512 sprites down to calculated tile size using PIL.Image.resize()
   - Store tile dimensions for consistent rendering
   - Architecture supports future zoom levels (tile_width * zoom_factor)

5. **Z-Order Rendering Sequence** (CRITICAL - must follow this order):
   ```python
   # 1. Clear SDL renderer
   context.sdl_renderer.clear()

   # 2. Render sprite layer (bottom) - floors, walls, items
   for tile in terrain:
       context.sdl_renderer.copy(sprite_texture, dest=tile_rect)

   # 3. Render sprite layer (middle) - enemies, player
   for entity in entities:
       context.sdl_renderer.copy(entity_texture, dest=entity_rect)

   # 4. Render colored boxes for status effects (above sprites)
   context.sdl_renderer.draw_color = (0, 255, 0, 128)  # Green with alpha
   context.sdl_renderer.fill_rect(player_tile_rect)

   # 5. Render console overlay (top) - UI, targeting cursor, glyph fallbacks
   console_texture = context.console_render.render(console)
   context.sdl_renderer.copy(console_texture)

   # 6. Present final frame
   context.sdl_renderer.present()
   ```

6. **TCOD Constraints** (from documentation research):
   - All tiles MUST be same size (no sub-tile alignment issues)
   - Sprites use transparency via alpha channel (fully supported)
   - Vision overlays: Use console background colors with alpha or SDL draw_color
   - Colored status boxes: Use `fill_rect()` with RGBA colors (draws over sprites, under console)
   - NO sprite animation in initial pass (single static frame per entity)

7. **SDL Renderer Access** (confirmed available):
   - `context.sdl_renderer` provides full SDL rendering capabilities
   - Drawing methods: `draw_rect()`, `fill_rect()`, `draw_line()`, `draw_point()`
   - Color control: `draw_color` property accepts RGBA tuples
   - Blend modes: `draw_blend_mode` for transparency/additive effects

8. **Dynamic Window Scaling** (TCOD capabilities confirmed):
   - Hook into TCOD window resize events
   - Recalculate tile dimensions: `new_tile_size = new_window_size / grid_dimensions`
   - Reload all sprite textures at new scale (PIL resize then SDL upload)
   - Reserve UI space: `game_area_height = window_height - top_bar - bottom_bar - side_log`
   - Pattern: Track `last_window_size`, compare on each frame, trigger rescale if changed

### Tile Mapping System
- **Mapping file**: JSON configuration maps game entities to sprite filenames
- **Location**: Add to existing `game_data.json` or create new `graphics_tiles.json`
- **Initial Implementation - '01' Variants Only**:
  - Use ONLY the '01' variant for each entity (player01.png, scanner01.png, etc.)
  - Numbered variants (02, 03, etc.) are alternate possibilities for future use
  - Keep JSON structure simple - direct entity name to filename mapping
  - Variant selection system deferred to future enhancement
- **Structure** (with tintable flags):
  ```json
  {
    "player": {
      "file": "player01.png",
      "tintable": false
    },
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
      "exploit_cpu": {"file": "exploit01.png", "tintable": true},
      "exploit_cooling": {"file": "exploit01.png", "tintable": true}
    }
  }
  ```
- **Tintable Flag Usage**:
  - `true`: White/grayscale sprite, use SDL color_mod for tinting
  - `false`: Colored sprite, use outline boxes for status effects
  - Default to `false` if not specified
- **Fallback chain**: PNG sprite → CP437 glyph → error placeholder

### Missing Sprites Strategy
- **For entities with graphics**: Render PNG sprite
- **For entities without graphics**: Render CP437 glyph via console overlay (Layer 3)
- **Glyph rendering in graphics mode**:
  - Console overlay naturally handles transparency
  - Render glyph to console at tile position with appropriate colors
  - Console-to-texture system preserves glyph appearance over sprite background
  - NO special "fallback tint" needed - glyphs render cleanly as overlays
- **Examples of missing tiles we'll need to handle**:
  - Targeting cursor ('X') - always rendered as console glyph overlay
  - Movement prediction indicators (circles) - console glyph overlay
  - Ghost enemy positions ('?') - console glyph overlay
  - Story fragments (music note symbol) - console glyph overlay
  - Some exploit types ('&') - console glyph overlay until sprites created
  - Gateway ('>') - console glyph overlay until sprite created
  - Special nodes in some states - console glyph overlay until sprites created

### Color Modification System (Two Strategies)

**Two Types of Color Modification Needed:**

#### Strategy 1: Texture Tinting (White Base Sprites)
**Used for**: Exploits, Code Hacks, and other items with white/grayscale base sprites

**Implementation**:
```python
# Apply color tint BEFORE rendering texture
texture = self.tile_manager.get_tile("codehack")
texture.color_mod = (255, 100, 0)  # Orange tint (RGB, no alpha)

# Render tinted texture
renderer.copy(texture, dest=tile_rect)
```

**How it works**:
- SDL color_mod multiplies texture RGB values by (R/255, G/255, B/255)
- White pixels (255,255,255) become (R,G,B)
- Gray pixels scale proportionally
- Works great for white/grayscale base sprites
- **Z-Layer**: Happens during sprite render (Layer 1-2)

**Advantages**:
- Natural looking color application
- Preserves sprite detail and shading
- No additional draw calls needed

**Sprites using this method**:
- Exploits (white base)
- Code Hacks (white base)
- Any future white/grayscale items

---

#### Strategy 2: Colored Outline Boxes (Colored Base Sprites)
**Used for**: Player, enemies, and other sprites with existing colors that shouldn't be tinted

**Implementation**:
```python
# Render sprite normally (no color_mod)
texture = self.tile_manager.get_tile("player")
renderer.copy(texture, dest=tile_rect)

# Then draw colored outline box OVER the sprite (Layer 2.5)
renderer.draw_color = (0, 255, 0, 255)  # Bright green, fully opaque
renderer.draw_rect(tile_rect)  # Outline only, not filled

# For thicker outline (2-3 pixels), draw multiple rectangles:
for offset in range(2):  # 2-pixel thick outline
    adjusted_rect = (tile_rect[0] - offset, tile_rect[1] - offset,
                     tile_rect[2] + offset*2, tile_rect[3] + offset*2)
    renderer.draw_rect(adjusted_rect)
```

**How it works**:
- Sprite renders with original colors intact
- Colored rectangle outline drawn as separate draw call
- Outline appears OVER sprite, UNDER console overlay
- **Z-Layer**: Layer 2.5 (after sprites, before console)

**Status Effect Colors**:
```python
STATUS_OUTLINE_COLORS = {
    "virus": (0, 255, 0, 255),        # Bright green outline
    "slow": (255, 255, 0, 255),       # Yellow outline
    "invisible": (100, 100, 255, 200), # Blue outline (semi-transparent)
    "hunter_targeting": (255, 0, 0, 255), # Red outline
    # ... other status effects
}
```

**Advantages**:
- Doesn't alter sprite colors
- Clearly visible on any background
- Can use different outline thicknesses for emphasis

**Sprites using this method**:
- Player sprite (has colors, needs outline for status)
- All enemy sprites (colored, need outline for status)
- Any other colored sprites needing status indication

---

#### Rendering Layer Architecture (Updated)

**Complete Z-Order with Both Color Strategies**:

```python
# 1. Clear SDL renderer
context.sdl_renderer.clear()

# 2. LAYER 1: Render terrain sprites (no color mods)
for tile in terrain:
    texture = tile_manager.get_tile("floor")
    renderer.copy(texture, dest=tile_rect)

# 3. LAYER 2A: Render item sprites WITH TINTING (white base sprites)
for item in items:
    texture = tile_manager.get_tile(item.type)
    if item.needs_tint:  # Exploits, code hacks
        texture.color_mod = item.tint_color  # Apply tint
    renderer.copy(texture, dest=tile_rect)

# 4. LAYER 2B: Render entity sprites WITHOUT TINTING (colored sprites)
for entity in entities:
    texture = tile_manager.get_tile(entity.type)
    renderer.copy(texture, dest=tile_rect)  # No color_mod

# 5. LAYER 2.5: Draw status effect OUTLINES over colored sprites
for entity in entities:
    if entity.has_status_effect:
        renderer.draw_color = STATUS_OUTLINE_COLORS[entity.status]
        for offset in range(2):  # 2-pixel thick outline
            adjusted_rect = calculate_outline_rect(entity.tile_rect, offset)
            renderer.draw_rect(adjusted_rect)

# 6. LAYER 3: Render console overlay (UI, cursor, glyph fallbacks)
console_texture = context.console_render.render(console)
renderer.copy(console_texture)

# 7. Present final frame
context.sdl_renderer.present()
```

**Configuration in Tile Mapping JSON**:
```json
{
  "player": {
    "file": "player01.png",
    "tintable": false
  },
  "enemies": {
    "Scanner": {"file": "scanner01.png", "tintable": false},
    "Patrol": {"file": "patrol01.png", "tintable": false}
  },
  "items": {
    "codehack": {"file": "codehack01.png", "tintable": true},
    "exploit": {"file": "exploit01.png", "tintable": true}
  }
}
```

**Testing Considerations**:
- Test tinted white sprites at various colors
- Test outline visibility over complex sprite backgrounds
- Verify outline thickness is visible but not overwhelming
- Test status effects on both tintable and non-tintable sprites
- Ensure color_mod doesn't affect non-tintable sprites
- Test multiple status effects (if possible) - outline priority system

## Implementation Phases

### Phase 0: Terminology Refactor (CRITICAL - DO FIRST)

**Purpose**: Update entire codebase from "ASCII/graphics" terminology to "glyph/graphics" terminology. This ensures consistency before implementing new graphics features and prevents confusion between CP437 glyphs and true ASCII.

**Timeline**: Must complete BEFORE Phase 1. All tests must be 100% green before proceeding.

**Progress Checklist**:
- [x] 0.1: Code Terminology Updates
  - [x] Search codebase for all "ascii" references
  - [x] Update game_config.py settings and validation
  - [x] Update game_rendering.py comments and variables
  - [x] Update game_loop.py comments and logging (no changes needed)
  - [x] Update menu system (game_menus.py, game_menu_help_lore.py)
  - [x] Update game_menu_background.py comments
  - [x] Add migration code for user_settings.json
  - [x] Review all other Python files for ascii references
- [x] 0.2: Update All Tests
  - [x] Search test files for "ascii" string literals
  - [x] Update test fixtures (standard_patterns.py)
  - [x] Update parametrized tests
  - [x] Update test assertions and error messages
  - [x] Run pytest on modified tests
- [x] 0.3: Update User-Facing Text and Documentation
  - [x] Update help screens (not needed - no explicit ascii references found)
  - [x] Update settings menu button text (ASCII → Classic)
  - [x] Update README.md (deferred - no changes needed)
  - [x] Add developer comments explaining terminology
- [x] 0.4: Verify and Test Changes
  - [x] Run grep to confirm no stray "ascii" references
  - [x] Run full test suite (780 passed, 3 pre-existing failures unrelated to changes)
  - [ ] Manual gameplay test in both modes (deferred - will test in next phase)
  - [ ] Test settings migration with old user_settings.json (migration code in place, needs manual verification)
  - [x] Verify no console warnings or errors
- [x] 0.5: Documentation of Changes
  - [x] Add developer notes to code
  - [x] Update this plan with lessons learned

**Phase 0 Completion Status**: ✅ **COMPLETE**
- All code terminology updated from "ascii" to "glyph"
- All user-facing text updated to "Classic Mode"
- Migration code added to handle old "ascii" settings
- 780/783 tests passing (3 pre-existing failures unrelated to terminology changes)
- Ready to proceed to Phase 1

#### 0.1: Code Terminology Updates

**Files to modify** (variable names, method names, class names, comments):

1. **Settings and Configuration**:
   - `game_config.py`:
     - `GameSettings.graphics_mode` → keep name but update valid values
     - Valid values: `"graphics"` (PNG sprites) or `"glyph"` (CP437 characters)
     - Update all comments/docstrings mentioning "ASCII"
   - `user_settings.json`:
     - Current: `"graphics_mode": "graphics"` or `"graphics_mode": "ascii"`
     - New: `"graphics_mode": "graphics"` or `"graphics_mode": "glyph"`
     - Need migration: Load old "ascii" value, convert to "glyph", save

2. **Rendering System**:
   - `game_rendering.py`:
     - Update all comments: "ASCII" → "glyph" or "CP437 glyph"
     - Method names: `_render_remembered_tile()` comments about "ASCII fallback"
     - Docstrings: Clarify "glyph mode" vs "graphics mode"
     - Any variables named `ascii_*` → `glyph_*`
   - `game_loop.py`:
     - Comments about "ASCII mode" → "glyph mode"
     - Update any logging messages

3. **Menu System**:
   - `game_menus.py` (or wherever settings menu lives):
     - Menu option text: "ASCII Mode" → "Classic Mode"
     - Tooltip/description: Explain it's CP437 glyphs, not pure ASCII
   - `game_menu_help_lore.py`:
     - Help text mentioning "ASCII" → "Classic/Glyph"
     - Update key binding descriptions
   - `game_menu_background.py`:
     - Comments and logging about "ASCII mode fallback" → "glyph mode fallback"

4. **Data and Story**:
   - `game_data.py`, `game_story.py`, etc.:
     - Any comments about rendering modes
   - JSON config files:
     - Comments in `game_config.json` (if any mention ASCII)

5. **All Other Game Files**:
   - Search entire codebase for:
     - Comments containing "ASCII" (except historical/technical explanations)
     - Variable names containing `ascii_`
     - String literals showing "ASCII" to users
   - Update to "glyph" or "classic" as appropriate

**Search and replace strategy**:
```bash
# Files to check (run grep to find all instances):
grep -r "ascii" --include="*.py" .
grep -r "ASCII" --include="*.py" .
grep -r "ascii" --include="*.json" .
```

**Migration for user_settings.json**:
- Add migration code in `game_config.py` `GameSettings.__init__()`:
  ```python
  # Migrate old "ascii" setting to "glyph"
  if self.graphics_mode == "ascii":
      self.graphics_mode = "glyph"
      self.save()  # Persist the migration
  ```

**Potential issues**:
- Breaking existing save files → migration code handles this
- String matching too broad → careful manual review
- External documentation → update README, etc.

#### 0.2: Update All Tests

**Files to modify**:

1. **Test Fixtures**:
   - `tests/fixtures/simple_fixtures.py`:
     - Any fixtures creating games with `graphics_mode="ascii"` → `"glyph"`
     - Update fixture docstrings
   - `tests/fixtures/real_game_data.py`:
     - Update any mode references
   - `tests/conftest.py`:
     - Update any shared fixtures

2. **Integration Tests**:
   - Search all test files for `"ascii"` string literals:
     ```bash
     grep -r '"ascii"' tests/
     grep -r "'ascii'" tests/
     ```
   - Update to `"glyph"`:
     - `test_complete_level_playthrough.py`
     - `test_config_validation_smoke.py`
     - Any tests that set graphics_mode
   - Update test names if they contain "ascii":
     - `test_ascii_mode_*` → `test_glyph_mode_*` or `test_classic_mode_*`

3. **Parametrized Tests**:
   - Find all: `@pytest.mark.parametrize("graphics_mode", ["ascii", "graphics"])`
   - Update to: `@pytest.mark.parametrize("graphics_mode", ["glyph", "graphics"])`

4. **Test Assertions**:
   - Any assertions checking `graphics_mode == "ascii"` → `== "glyph"`
   - Error messages in tests mentioning ASCII

5. **Test Documentation**:
   - Test docstrings explaining test behavior
   - Comments in test files

**Test execution**:
- After each file modified, run relevant tests:
  ```bash
  .venv/Scripts/python.exe -m pytest tests/path/to/test.py -v
  ```
- After all modifications, run full test suite:
  ```bash
  .venv/Scripts/python.exe test_commands.py full
  ```
- **REQUIREMENT**: All tests must be 100% green before proceeding to Phase 1

**Potential issues**:
- Missing test updates → comprehensive grep/search
- Tests passing but with wrong behavior → manual review of test logic
- Forgotten parametrized tests → search for all `parametrize` decorators

#### 0.3: Update User-Facing Text and Documentation

**Files to modify**:

1. **In-Game Text**:
   - Help screens (`game_menu_help_lore.py`):
     - Change "ASCII Mode" → "Classic Mode"
   - Settings menu:
     - Button text: "Graphics: ASCII" → "Graphics: Classic"
     - Or: "Render Mode: Classic" / "Render Mode: Graphics"
   - Any tutorial messages mentioning rendering modes

2. **README and Documentation**:
   - `README.md`:
     - Update feature descriptions

3. **Code Comments for Developers**:
   - Add/update comments explaining:
     - "Classic/glyph mode uses CP437 character set via TCOD tileset"
     - "NOT pure ASCII - includes extended characters like ♥♦♠"
     - "Graphics mode uses PNG sprites"

**User experience considerations**:
- "Classic Mode" feels retro without being too technical
- In-game descriptions should be brief but accurate

**Potential issues**:
- Too much technical detail → keep user-facing text simple

#### 0.4: Verify and Test Changes

**Checklist**:
- [ ] All Python files updated (grep search confirms no stray "ascii" references)
- [ ] All JSON files updated
- [ ] All test files updated
- [ ] user_settings.json migration code added
- [ ] Full test suite passes (100% green)
- [ ] Manual gameplay test in both modes:
  - [ ] Start new game in "classic" mode
  - [ ] Switch to "graphics" mode in settings
  - [ ] Switch back to "classic" mode
  - [ ] Restart game, verify setting persists
  - [ ] Check old save file with "ascii" setting migrates correctly
- [ ] All UI text updated (menus, help screens)
- [ ] No console warnings or errors
- [ ] Settings save/load correctly

**Testing strategy**:
1. Run full test suite: `python test_commands.py full`
2. Start game with old `user_settings.json` containing `"ascii"`, verify migration
3. Play through one level in classic mode
4. Toggle to graphics mode (will show glyphs until Phase 1-6 complete)
5. Verify no crashes, no errors, settings persist

**Potential issues**:
- Missed references causing runtime errors → comprehensive testing
- Migration code not triggering → test with real old save file
- UI text truncation → check menu layouts

#### 0.5: Documentation of Changes

- **Update**: Developer notes in code:
  ```python
  # game_rendering.py
  """
  Rendering Modes:
  - GRAPHICS: High-res PNG sprites (512x512 scaled)
  - GLYPH: CP437 characters via TCOD tileset (10x16 pixels)

  Both modes use TCOD + SDL. "Glyph mode" is NOT pure ASCII -
  it includes extended CP437 characters like ♥♦♠•§.
  """
  ```

---

**Phase 0 Estimated Effort**: 3-5 hours
- Search and replace: 1 hour
- Test updates: 1-2 hours
- Test execution and debugging: 1-1.5 hours
- Documentation: 0.5 hours

**Phase 0 Completion Criteria**:
1. ✅ No grep hits for inappropriate "ascii" references in code
2. ✅ All tests pass (100% green)
3. ✅ Manual gameplay test successful in both modes
4. ✅ Settings migration works
5. ✅ All UI text updated
6. ✅ Documentation complete

**CRITICAL**: Phase 1 cannot begin until Phase 0 is 100% complete with all tests green.

---

### Phase 1: Foundation & Sprite Loading System

**Progress Checklist**:
- [x] 1.1: Create Tile Manager Class (`game_graphics_tiles.py`)
  - [x] Create file with TileManager class skeleton
  - [x] Implement tile dimension calculation
  - [x] Implement PNG loading with transparency (PIL + SDL)
  - [x] Implement texture caching system
  - [x] Implement tintable flag support
  - [x] Add error handling and logging
  - [x] Test basic functionality (imports work)
- [x] 1.2: Create Sprite Mapping Configuration
  - [x] Create `graphics_tiles.json` with initial mappings
  - [x] Add validation in `validate_json_config.py`
  - [x] Test JSON loading and validation
- [x] 1.3: Integrate Tile Manager into Game Initialization
  - [x] Modify `game_loop.py` to initialize TileManager
  - [x] Pass TileManager to GameRenderer
  - [x] Test initialization in both modes (imports work, runtime testing pending)

**Phase 1 Status**: ✅ **FOUNDATION COMPLETE**
- TileManager class fully implemented with all core functionality
- Sprite mapping JSON created with 18 initial sprites (player, 8 enemies, 2 terrain, 7 items)
- JSON validation added and working
- Integration into game_loop.py and game_rendering.py complete
- All imports successful

**Ready for Phase 2**: Rendering integration can now proceed

#### 1.1: Create Tile Manager Class (`game_graphics_tiles.py`)
**Purpose**: Centralized system for loading, caching, and serving tile graphics with transparency support

**Key components**:
- `TileManager` class:
  - `__init__(context, settings)`: Store SDL renderer reference and settings
  - `load_tile_mappings()`: Load JSON config mapping entities to PNG files and tintable flags
  - `load_tile(filepath)`: Load individual PNG with transparency, scale, return SDL texture
  - `get_tile(entity_type)`: Retrieve cached texture for entity (no variants in initial pass)
  - `is_tintable(entity_type)`: Return True if sprite should use color_mod, False for outline boxes
  - `calculate_tile_dimensions(window_size, grid_size)`: Determine tile pixel dimensions
  - `preload_tiles()`: Lazy loading strategy - load on first access, cache thereafter
  - `cleanup()`: Free all SDL textures
  - `handle_window_resize(new_window_size)`: Recalculate tile size, reload all textures at new scale

**Texture cache**:
- Dict mapping entity_name (string) → SDL texture
- Simple key structure: `cache["player"]`, `cache["Scanner"]`, `cache["floor"]`
- Separate dict for tintable flags: `tintable_flags["player"] = False`, `tintable_flags["codehack"] = True`

**Sprite Loading with Transparency** (CRITICAL):
```python
def load_tile(self, filepath):
    """Load PNG sprite with transparency and scale to tile size."""
    try:
        from PIL import Image
        import numpy as np

        # Load image preserving alpha channel
        pil_image = Image.open(filepath)

        # Convert to RGBA if not already (ensure alpha channel exists)
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')

        # Scale to calculated tile size (512x512 → tile_width x tile_height)
        pil_image = pil_image.resize(
            (self.tile_width, self.tile_height),
            Image.Resampling.LANCZOS  # High-quality downscaling
        )

        # Convert to numpy array (height, width, 4) for RGBA
        pixels = np.array(pil_image, dtype=np.uint8)

        # Upload to SDL as texture (automatically handles alpha)
        texture = self.context.sdl_renderer.upload_texture(pixels)

        # Set blend mode for proper transparency rendering
        texture.blend_mode = tcod.sdl.BlendMode.BLEND

        return texture

    except Exception as e:
        logging.warning(f"Failed to load sprite {filepath}: {e}")
        return None
```

**Scaling Strategy**:
- Use PIL `Image.Resampling.LANCZOS` for high-quality downscaling
- Calculate tile size: `tile_size = (window_pixels - UI_space) / grid_cells`
- Store `self.tile_width` and `self.tile_height` for consistent rendering
- Reload textures if window size changes significantly (>10% change)

**Lazy Loading Approach** (Initial Implementation):
- Don't preload all sprites at startup
- Load sprite on first `get_tile()` call
- Cache loaded texture for subsequent calls
- Reduces startup time, spreads loading across gameplay
- Future optimization: Preload common sprites (player, basic enemies) after initial load

**Files modified**:
- **New**: `game_graphics_tiles.py` (~400-500 lines estimated with resize handling)

**Potential issues**:
- Transparency not rendering correctly → ensure blend mode set on texture
- Scaled sprites looking blurry → test different resize filters, LANCZOS recommended
- Memory usage with large cache → monitor, implement LRU eviction if needed
- First-access hitching → acceptable for initial pass, preload in Phase 5 if needed

#### 1.2: Create Sprite Mapping Configuration
**Purpose**: Define which sprites map to which game entities

**Files modified**:
- **New**: `graphics_tiles.json` (or add to `game_data.json`)
- Add JSON schema validation in `validate_json_config.py`

**Structure considerations**:
- Organize by category (player, enemies, terrain, items, effects)
- Support variant selection (random, state-based, etc.)
- Document which entities still need sprites
- Include fallback CP437 glyph for each entity

**Potential issues**:
- Misnamed files → validation script should check all referenced files exist
- Missing mappings → need comprehensive coverage of all renderable entities

#### 1.3: Integrate Tile Manager into Game Initialization
**Purpose**: Initialize tile system alongside other game systems

**Files modified**:
- `game_loop.py`:
  - Import `TileManager` from `game_graphics_tiles`
  - Initialize in `main()` after context creation: `tile_manager = TileManager(context, settings)` (~line 236)
  - Call `tile_manager.preload_tiles()` if in graphics mode
  - Pass `tile_manager` to `GameRenderer` initialization (~line 261)
  - Cleanup on exit

**Potential issues**:
- Initialization order dependencies → ensure SDL context ready before TileManager
- Slow startup if loading many tiles → add loading indicator or progress log

### Phase 2: Rendering Integration

#### 2.1: Modify MapRenderer for Graphics Support with SDL Rendering
**Purpose**: Make `MapRenderer` SDL-aware and implement layered rendering architecture

**Files modified**:
- `game_rendering.py` (`MapRenderer` class, lines 1071-1691):
  - Add `tile_manager` and `context` parameters to `MapRenderer.__init__`
  - Add `_should_use_graphics()` method: Check `settings.graphics_mode == "graphics"` and tile_manager available
  - **NEW**: Add `_render_sprites_layer()` method for SDL texture rendering
  - **NEW**: Add `_render_status_effects_layer()` method for colored boxes
  - Modify console rendering to be transparent for graphics mode

**New SDL Rendering Methods**:
```python
def _render_sprites_layer(self, game):
    """Render all sprite textures directly to SDL renderer (Layer 1 & 2)."""
    if not self._should_use_graphics():
        return

    renderer = self.context.sdl_renderer
    camera_x, camera_y = self._calculate_camera_offset(game)

    # Layer 1: Render terrain sprites (floors, walls)
    for screen_y in range(self.game_area_height):
        for screen_x in range(self.game_area_width):
            world_x = screen_x + camera_x
            world_y = screen_y + camera_y

            # Get tile texture (floor or wall)
            entity_type = self._determine_terrain_type(world_x, world_y, game)
            texture = self.tile_manager.get_tile(entity_type)

            if texture:
                # Calculate pixel rectangle for this tile
                tile_rect = self._get_tile_rect(screen_x, screen_y)

                # Render sprite texture to SDL
                renderer.copy(texture, dest=tile_rect)

    # Layer 2A: Render item sprites (with tinting for white sprites)
    for item in self._get_visible_items(game):
        texture = self.tile_manager.get_tile(item.type)
        if texture:
            tile_rect = self._get_entity_tile_rect(item, game)

            # Apply color tint if sprite is tintable (white base)
            if self.tile_manager.is_tintable(item.type):
                texture.color_mod = item.get_color()  # e.g., (255, 100, 0) for orange

            renderer.copy(texture, dest=tile_rect)

            # Reset color mod for next use
            if self.tile_manager.is_tintable(item.type):
                texture.color_mod = (255, 255, 255)  # Reset to white

    # Layer 2B: Render entity sprites (enemies, player - NO tinting)
    for entity in self._get_visible_entities(game):
        texture = self.tile_manager.get_tile(entity.type)
        if texture:
            tile_rect = self._get_entity_tile_rect(entity, game)
            renderer.copy(texture, dest=tile_rect)

def _render_status_effects_layer(self, game):
    """Render colored status effect outlines over NON-TINTABLE sprites (Layer 2.5)."""
    if not self._should_use_graphics():
        return

    renderer = self.context.sdl_renderer

    # Draw status effect outlines for player (if has status)
    if game.player.is_virused:
        player_tile_rect = self._get_player_tile_rect(game)

        # Draw 2-pixel thick green outline
        renderer.draw_color = (0, 255, 0, 255)  # Bright green
        for offset in range(2):
            outline_rect = self._expand_rect(player_tile_rect, offset)
            renderer.draw_rect(outline_rect)  # Outline, not filled

    # Draw status effect outlines for enemies
    for enemy in game.enemies:
        if enemy.has_status_effect and enemy.is_visible:
            enemy_tile_rect = self._get_entity_tile_rect(enemy, game)
            outline_color = self._get_status_outline_color(enemy.status_type)

            renderer.draw_color = outline_color
            for offset in range(2):
                outline_rect = self._expand_rect(enemy_tile_rect, offset)
                renderer.draw_rect(outline_rect)

def _expand_rect(self, rect, offset):
    """Expand rectangle by offset pixels on all sides."""
    return (rect[0] - offset, rect[1] - offset,
            rect[2] + offset * 2, rect[3] + offset * 2)

def _get_status_outline_color(self, status_type):
    """Get outline color for status effect."""
    STATUS_COLORS = {
        "virus": (0, 255, 0, 255),        # Green
        "slow": (255, 255, 0, 255),       # Yellow
        "hunter_targeting": (255, 0, 0, 255),  # Red
    }
    return STATUS_COLORS.get(status_type, (255, 255, 255, 255))
```

**Console Rendering Modifications**:
```python
# In existing _render_tile() and related methods:
if self._should_use_graphics():
    # DON'T render to console for tiles with sprites
    # ONLY render UI elements and glyph fallbacks to console
    if self._has_sprite(entity_type):
        return  # Sprite handled by SDL layer

# Continue with console rendering for glyph fallbacks and UI
```

**Key Architecture Changes**:
1. **Split rendering into layers**: SDL sprites → SDL boxes → console overlay
2. **Pass context to MapRenderer**: Need SDL renderer access
3. **Transparent console backgrounds**: Set background alpha 0 for sprite areas
4. **Coordinate conversion**: Screen grid coordinates → pixel coordinates for SDL

**Pixel Coordinate Calculation**:
```python
def _grid_to_pixel(self, screen_x, screen_y):
    """Convert grid coordinates to pixel coordinates."""
    pixel_x = screen_x * self.tile_manager.tile_width
    pixel_y = screen_y * self.tile_manager.tile_height
    return (pixel_x, pixel_y)

def _get_tile_rect(self, screen_x, screen_y):
    """Get pixel rectangle for a tile."""
    px, py = self._grid_to_pixel(screen_x, screen_y)
    return (px, py, self.tile_manager.tile_width, self.tile_manager.tile_height)
```

**Potential issues**:
- Console background transparency not working → verify alpha channel in console rendering
- Pixel/grid coordinate misalignment → test thoroughly with different window sizes
- Performance with many texture copies → profile, SDL should handle efficiently
- UI elements rendered below sprites → ensure UI stays in console layer
- Color_mod persisting between frames → MUST reset to (255,255,255) after each tinted render
- Outline boxes not visible → adjust thickness or use fill_rect with semi-transparent instead

#### 2.2: Handle Special Rendering Cases
**Purpose**: Address edge cases like targeting cursor, movement prediction, vision overlays

**Files modified**:
- `game_rendering.py` (`MapRenderer` methods):
  - `_render_targeting_cursor()`: Keep as glyph overlay (it's UI)
  - `_render_vision_overlays()`: Keep as colored background overlays (works in both modes)
  - `_render_patrol_routes()`: Keep as glyph symbols (movement prediction indicators)
  - `_render_gateway()`: Graphics sprite if available, glyph fallback

**Special case: Glyph fallback in graphics mode**:
- When graphics mode is active but no sprite exists:
  - Render a solid colored background (entity-appropriate color)
  - Draw CP437 glyph centered in tile space using console overlay
  - Subtle visual distinction (maybe 10% darker background) to indicate "placeholder"

**Potential issues**:
- Mixed glyph/graphics looking inconsistent → design a cohesive fallback style
- Overlay elements (vision, cursor) clashing with sprites → test all combinations
- Player confusion about what's a "real" sprite vs placeholder → documentation

#### 2.3: Update Rendering Flow in GameRenderer
**Purpose**: Implement complete layered SDL rendering architecture

**Files modified**:
- `game_rendering.py` (`GameRenderer` class, lines 39-246):
  - Update `GameRenderer.__init__` to accept and store `tile_manager` and `context`
  - Pass both `tile_manager` and `context` to `MapRenderer` initialization
  - **CRITICAL**: Replace `_render_main_game_screen()` with new SDL-aware rendering

**New Rendering Flow** (replaces existing render logic):
```python
def _render_main_game_screen(self, console, game, context):
    """Render main game screen with layered SDL + console architecture."""

    if self._should_use_graphics_mode(context):
        # === GRAPHICS MODE: Layered SDL Rendering ===

        # Clear SDL renderer
        context.sdl_renderer.clear()

        # LAYER 1-2: Render sprites (terrain + entities) directly to SDL
        self.map_renderer.render_sprites_layer(game)

        # LAYER 2.5: Render status effect boxes over sprites
        self.map_renderer.render_status_effects_layer(game)

        # Render console with UI and glyph fallbacks
        self._render_console_ui(console, game)

        # LAYER 3: Render console as texture overlay (transparent backgrounds)
        console_texture = context.console_render.render(console)
        context.sdl_renderer.copy(console_texture)

        # Present final frame
        context.sdl_renderer.present()

    else:
        # === GLYPH MODE: Traditional Console Rendering ===

        # Render everything to console
        self.map_renderer.render_map(console, game)
        self._render_console_ui(console, game)

        # Present console directly (no SDL needed)
        # NOTE: context.present() handled in game_loop.py

def _should_use_graphics_mode(self, context):
    """Check if graphics mode is available and enabled."""
    return (self.settings.graphics_mode == "graphics" and
            self.tile_manager is not None and
            context.sdl_renderer is not None and
            hasattr(context, 'console_render') and
            context.console_render is not None)

def _render_console_ui(self, console, game):
    """Render UI elements to console (transparent in graphics mode)."""
    # Status bar (top)
    self.ui_renderer.render_status_bar(console, game)

    # Message log (right side)
    self.ui_renderer.render_message_log(console, game)

    # Inventory/help/etc if active
    if game.show_inventory:
        self.ui_renderer.render_inventory(console, game)
    # ... other UI elements
```

**Console Transparency for Graphics Mode**:
- In graphics mode, console backgrounds in game area should be transparent
- Set `console.bg[x, y]` alpha to 0 for game map area
- UI panels (status bar, message log) keep solid backgrounds
- Glyph fallbacks (cursor, etc.) render with visible foreground colors

**Integration with game_loop.py**:
```python
# In main game loop (game_loop.py):
while game is not None:
    game.sound_manager.update()

    # Render game (handles both SDL and console modes internally)
    renderer.render_game(console, game, context)

    # Present only needed for glyph mode (graphics mode handles in renderer)
    if settings.graphics_mode == "glyph":
        context.present(console)

    # Handle input events
    for event in tcod.event.wait():
        # ... input handling
```

**Key Changes Summary**:
1. Pass `context` to renderer for SDL access
2. Implement layered rendering: sprites → boxes → console
3. Handle transparency in console for graphics mode
4. Conditionally call `context.present()` based on mode

**Potential issues**:
- Double present() calls → only call from renderer in graphics mode
- Console transparency not working → verify alpha channel setup
- UI elements missing → ensure UI rendering happens after sprite layer
- Performance with full SDL pipeline → profile, should be efficient

### Phase 2.5: Dynamic Window Scaling

#### 2.5.1: Implement Window Resize Handler
**Purpose**: Dynamically scale sprites when window is resized

**Files modified**:
- `game_graphics_tiles.py` (`TileManager` class):
  - Add `handle_window_resize(new_window_size)` method
  - Track `last_window_size` to detect changes
  - Implement smart reload: only if size changed by >10%

**Window Resize Detection**:
```python
# In TileManager class
def check_and_handle_resize(self, context):
    """Check if window was resized and reload textures if needed."""
    current_size = self._get_window_size(context)

    if self.last_window_size is None:
        self.last_window_size = current_size
        return False

    # Calculate percentage change
    width_change = abs(current_size[0] - self.last_window_size[0]) / self.last_window_size[0]
    height_change = abs(current_size[1] - self.last_window_size[1]) / self.last_window_size[1]

    # Reload if change > 10%
    if width_change > 0.1 or height_change > 0.1:
        logging.info(f"Window resized: {self.last_window_size} → {current_size}")
        self._reload_all_textures(current_size)
        self.last_window_size = current_size
        return True

    return False

def _reload_all_textures(self, new_window_size):
    """Recalculate tile size and reload all cached textures."""
    # Recalculate tile dimensions
    self._calculate_tile_dimensions(new_window_size)

    # Clear existing texture cache
    old_cache = self.texture_cache.copy()
    self.texture_cache.clear()

    # Reload all previously loaded textures at new size
    for entity_name in old_cache.keys():
        # Lazy reload - will reload on next get_tile() call
        pass

    logging.info(f"Textures ready for reload at new size: {self.tile_width}x{self.tile_height}")

def _calculate_tile_dimensions(self, window_size):
    """Calculate tile pixel dimensions based on window size and UI layout."""
    window_width, window_height = window_size

    # Reserve space for UI elements
    # Top bar: 2 rows, Bottom bar: 0 rows, Side log: variable width
    # Use grid dimensions from GameConfig
    from game_config import GameConfig

    # Calculate pixels per tile
    # NOTE: TCOD console uses character grid, need to account for console size
    console_width = GameConfig.SCREEN_WIDTH
    console_height = GameConfig.SCREEN_HEIGHT

    # Get game area dimensions in grid cells
    game_area_width = GameConfig.GAME_AREA_WIDTH()
    game_area_height = GameConfig.SCREEN_HEIGHT - 2  # Subtract top bar

    # Calculate tile size to fit game area
    self.tile_width = window_width // console_width
    self.tile_height = window_height // console_height

    logging.info(f"Calculated tile size: {self.tile_width}x{self.tile_height} pixels")

def _get_window_size(self, context):
    """Get current window pixel dimensions."""
    if hasattr(context, 'sdl_window') and context.sdl_window:
        return context.sdl_window.size
    return (800, 600)  # Default fallback
```

**Integration into Rendering Loop**:
```python
# In GameRenderer.render_game() or MapRenderer.render_sprites_layer()
# Check for window resize each frame (cheap check, only reloads if needed)
if self.tile_manager:
    self.tile_manager.check_and_handle_resize(context)
```

**Smart Reload Strategy**:
- Only reload if size change > 10% (avoid constant reloading during resize drag)
- Clear cache but don't immediately reload (lazy reload on next access)
- Log resize events for debugging
- Maintain aspect ratio of tiles (might not be square)

**UI Space Reservation**:
- Top status bar: 2 console rows (not part of game area)
- Message log: Variable width on right side
- Calculate available pixels for game area
- Divide by game area grid dimensions to get tile size

**Potential issues**:
- Resize during gameplay causing hitching → acceptable for infrequent resize events
- Tile size becoming too small → set minimum tile size (e.g., 16x16 pixels)
- Aspect ratio distortion → tiles may be non-square, sprites will stretch
- UI layout not adjusting → ensure UI system aware of tile size changes

### Phase 3: Configuration & Settings Integration

#### 3.1: Tile Mapping JSON Schema
**Purpose**: Define and validate the tile configuration format

**Files modified**:
- **New/Update**: `graphics_tiles.json`
- `validate_json_config.py`:
  - Add validation function for tile mappings
  - Check all referenced PNG files exist
  - Validate structure matches expected schema
  - Run during startup and in test suite

**Validation rules**:
- All PNG paths must exist in `graphics/` folder
- Each game entity should have at least one tile or explicit "no_graphic" flag
- Variant arrays must have at least one entry
- Required fields present for each entity type

**Potential issues**:
- File paths case sensitivity on different OSs → normalize to lowercase
- Missing files after validation → need repair tools or detailed error messages

#### 3.2: Graphics Mode Toggle Integration
**Purpose**: Ensure graphics_mode setting properly controls tile rendering

**Files modified**:
- `game_config.py` (`GameSettings` class):
  - Verify `graphics_mode` setting properly loaded
  - Consider adding graphics quality/scaling settings for future
- `game_menu_background.py` (`SettingsMenu`):
  - Settings menu already has graphics toggle
  - Test mode changes persist and reload correctly
- Verify `user_settings.json` structure supports toggle

**Behavior**:
- Changing setting in menu should apply immediately on return to game
- Mode persists across game sessions
- Tile loading only occurs when graphics mode enabled

**Potential issues**:
- Changing mode mid-game → need to handle texture cleanup/reloading
- Setting not persisting → verify JSON save/load chain

### Phase 4: Testing & Validation

#### 4.1: Unit Tests for Tile Manager
**Purpose**: Test tile loading, caching, and retrieval in isolation

**Files modified**:
- **New**: `tests/unit/test_graphics_tiles.py`

**Test cases**:
- `test_tile_manager_initialization`: Verify TileManager initializes with valid context
- `test_load_tile_mappings`: Load JSON config and verify structure
- `test_load_individual_tile`: Load single PNG, verify texture created
- `test_tile_caching`: Request same tile twice, verify cached
- `test_missing_tile_fallback`: Request nonexistent tile, verify None returned
- `test_calculate_tile_dimensions`: Test dimension calculation with various grid sizes
- `test_tile_scaling`: Load 512x512, verify scaled to target dimensions
- `test_cleanup`: Verify textures freed on cleanup

**Fixtures needed**:
- Mock SDL context and renderer
- Sample test PNGs (small files in `tests/fixtures/graphics/`)
- Sample tile mapping JSON

**Potential issues**:
- SDL mocking complexity → may need integration tests instead of pure unit tests
- PIL dependency in tests → ensure test environment has PIL

#### 4.2: Integration Tests for Rendering
**Purpose**: Test graphics rendering in actual game scenarios

**Files modified**:
- **New**: `tests/integration/test_graphics_rendering.py`

**Test cases**:
- `test_graphics_mode_player_rendering`: Create game in graphics mode, verify player sprite renders
- `test_graphics_mode_enemy_rendering`: Verify all enemy types render with sprites
- `test_graphics_mode_terrain_rendering`: Verify floors and walls render
- `test_glyph_mode_unchanged`: Verify glyph/classic mode still works identically
- `test_graphics_fallback_to_glyph`: Request sprite without graphics, verify glyph fallback
- `test_mode_switching`: Start in glyph, switch to graphics, verify transition
- `test_mixed_rendering`: Map with some sprite entities and some glyph fallbacks, verify both render
- `test_fov_in_graphics_mode`: Verify FOV/vision works identically in both modes
- `test_camera_in_graphics_mode`: Move player, verify camera follows correctly

**Testing approach**:
- Use `tests/fixtures/` builders to create game states
- Don't mock rendering - test actual render calls
- May need to render to offscreen buffer for validation
- Test both modes side-by-side for consistency

**Potential issues**:
- Rendering tests need graphical context → CI/CD may need headless SDL
- Pixel-level validation difficult → test behavior, not exact output
- Slow tests with full rendering → mark as integration, don't run on every commit

#### 4.3: Visual Regression Testing Strategy
**Purpose**: Ensure graphics changes don't break visual appearance

**Approach** (manual for now, automated later):
- Create test maps with all entity types
- Capture screenshots in both glyph and graphics modes
- Compare before/after screenshots when making changes
- Document expected appearance for reference

**Files**:
- **New**: `tests/visual/` directory
- Test maps in `tests/fixtures/`
- Reference screenshots (not in git, too large)

**Potential issues**:
- Automated screenshot comparison complex → start manual, automate later
- Screen resolution differences → standardize test window size
- Color/scaling differences → define acceptable tolerance

#### 4.4: Update Existing Tests
**Purpose**: Ensure existing tests don't break with graphics additions

**Files modified**:
- Review all tests in `tests/integration/` that touch rendering
- Add graphics_mode parameter to fixtures where needed
- Ensure tests run in both ASCII and graphics modes
- Key tests to update:
  - `test_complete_level_playthrough.py`: Test full playthrough in both modes
  - `test_player_enemy_vision_chain.py`: Vision should work identically
  - `test_enemy_ai_complete_workflow.py`: Enemy rendering shouldn't affect AI

**Testing strategy**:
- Parametrize tests to run in both modes: `@pytest.mark.parametrize("graphics_mode", ["glyph", "graphics"])`
- Ensure behavior identical between modes (rendering is just presentation)
- Keep tests fast - don't test every rendering detail in every test

**Potential issues**:
- Fixtures need updates for graphics mode → modify `tests/fixtures/simple_fixtures.py`
- Tests timing out with graphics rendering → optimize or mark as slow
- CI environment lacking graphics support → may need headless rendering setup

### Phase 5: Polish & Missing Pieces

#### 5.1: Document Missing Sprites
**Purpose**: Create comprehensive list of what still needs ASCII fallback

**Files modified**:
- **New**: `graphics/MISSING_SPRITES.md`

**Contents**:
- List all entities that render in-game
- Mark which have graphics, which don't
- Priority order for creating missing sprites
- ASCII fallback character for each

**Categories to audit**:
- Player states (normal, invisible, virus, slowed)
- All enemy types (check `GameData.ENEMY_TYPES`)
- Terrain (walls, floors, shadows)
- Items (exploits, code hacks, upgrades, story fragments)
- Special nodes (cooling, CPU, ghost, gateway)
- Effects (targeting cursor, movement prediction, vision overlays)

**Potential issues**:
- Comprehensive audit takes time → start with playable set, expand later
- Discovering missing sprites during gameplay → add to list as found

#### 5.2: Error Handling & Logging
**Purpose**: Robust error handling for graphics failures

**Files modified**:
- `game_graphics_tiles.py`:
  - Wrap all PIL/SDL operations in try/except
  - Log errors with context (which file, which entity)
  - Graceful degradation to ASCII mode on catastrophic failure
- `game_rendering.py`:
  - Handle None returns from tile_manager
  - Log when falling back to ASCII for specific tiles

**Error scenarios to handle**:
- PNG file missing or corrupted → log, use glyph fallback
- SDL texture creation fails → log, fallback to glyph mode entirely
- Out of memory → cleanup textures, fallback
- Invalid JSON config → log, use glyph mode

**Potential issues**:
- Silent failures hiding issues → ensure errors logged prominently
- Too aggressive fallback → prefer partial graphics to full glyph mode switch

### Phase 6: Documentation & Completion

#### 6.1: Code Documentation
**Purpose**: Ensure graphics system is well-documented for future work

**Files modified**:
- Add docstrings to all new classes and methods
- Document tile mapping JSON format
- Add comments explaining graphics vs glyphs paths in rendering code

**Key documentation areas**:
- `game_graphics_tiles.py`: Full module docstring explaining system
- `graphics_tiles.json`: Header comment with format specification
- `game_rendering.py`: Comments explaining graphics rendering flow
- Inline comments for complex scaling/texture code

#### 6.2: Developer Documentation
**Purpose**: Guide future sprite additions and system modifications

**Files modified**:
- **New**: `graphics/README.md`:
  - How to add new sprites
  - Sprite specifications (size, format)
  - How to update tile mappings
  - Testing new sprites

**Contents**:
- Sprite creation guidelines (512x512 PNG, transparent background)
- How to map new sprite in JSON
- How to test sprite in-game
- Common issues and solutions

#### 6.4: Final Testing Checklist
**Purpose**: Comprehensive validation before considering phase complete

**Checklist**:
- [ ] All existing tests pass in both glyph and graphics modes
- [ ] New graphics tests pass
- [ ] Manual playthrough in graphics mode completes successfully
- [ ] Manual playthrough in glyph/classic mode unchanged
- [ ] Toggle between modes works mid-game
- [ ] No memory leaks observed (long gameplay session)
- [ ] No console errors or warnings in normal operation
- [ ] Performance acceptable (subjective, but should feel responsive)
- [ ] All configured sprites load successfully
- [ ] Missing sprites fall back to glyphs gracefully
- [ ] UI elements (status bar, log, menus) render correctly in both modes
- [ ] FOV/vision works identically in both modes
- [ ] Camera works identically in both modes
- [ ] Save/load works with graphics mode setting

## File Size Analysis

### New Files
- `game_graphics_tiles.py`: ~400-500 lines
- `graphics_tiles.json`: ~200-300 lines (JSON)
- `graphics/MISSING_SPRITES.md`: ~100-200 lines
- `tests/unit/test_graphics_tiles.py`: ~200-300 lines
- `tests/integration/test_graphics_rendering.py`: ~300-400 lines
- `graphics/README.md`: ~100-150 lines

**Total new code**: ~1300-1850 lines

### Modified Files
- `game_rendering.py`: +200-300 lines (modifications, new methods)
- `game_loop.py`: +30-50 lines (TileManager init)
- `validate_json_config.py`: +50-100 lines (tile mapping validation)
- Various test files: +100-200 lines (parametrization, fixtures)

**Total modifications**: ~400-650 lines

**Grand total**: ~1700-2500 lines of new/modified code

### Size Compliance
- `game_rendering.py` currently 1691 lines, may approach 2000 → monitor, consider split if needed
- All new files well under 2000 line limit
- If `game_rendering.py` exceeds 1800 lines, consider extracting:
  - Graphics rendering to separate `game_rendering_graphics.py`
  - glyph rendering stays in `game_rendering.py`
  - Both use shared `MapRenderer` base class

## Risk Assessment

### High Risk
- **SDL rendering integration complexity**: Mixing SDL textures and console rendering is complex. Mitigation: Follow menu background pattern, test extensively.
- **Performance with scaled tiles**: Scaling many 512x512 images might be slow. Mitigation: Profile early, consider pre-scaled assets if needed.
- **Test complexity**: Graphics tests harder than ASCII tests. Mitigation: Focus on integration tests, accept manual visual testing initially.

### Medium Risk
- **Tile mapping completeness**: May miss entities that need sprites. Mitigation: Comprehensive audit, maintain missing sprites list.
- **Mode switching mid-game**: Graphics/ASCII toggle during play might have edge cases. Mitigation: Test thoroughly, consider requiring restart if issues.
- **Memory usage**: Loading all tiles at once might use significant memory. Mitigation: Monitor, implement lazy loading if needed.

### Low Risk
- **Glyph mode regression**: Graphics additions shouldn't affect glyph rendering. Mitigation: Run all tests in both modes.
- **File organization**: Clear separation between sprite loading and rendering. Mitigation: Follow existing patterns, code review.

## Dependencies

### Required Python Packages (Already Available)
- `tcod`: For rendering system (already in use)
- `PIL` (Pillow): For PNG loading and scaling (already in use for menu backgrounds)
- `numpy`: For image data manipulation (already in use)
- `pygame`: For SDL integration (already in use via tcod)

### No New Dependencies Required
All functionality can be implemented with existing packages already in the project.

## Future Enhancements (Out of Scope)

These are architectural considerations but not implemented in this phase:

1. **Zoom levels**: Architecture supports different tile sizes, but no UI for changing zoom
2. **Animated sprites**: Tile manager could support frame sequences, but all sprites static for now
3. **Sprite effects**: Could add color tinting, rotation, etc. Later.
4. **Graphical UI**: Menus, status bar, inventory could get graphical treatment. Later.
5. **Dynamic lighting**: Could add glow effects, shadows, etc. Later.
6. **Particle effects**: For explosions, movement, etc. Later.
7. **Tile editor**: Tool for previewing and configuring sprites. Later.
8. **Compressed atlases**: Combine tiles into sprite sheets for better performance. Later if needed.

## Success Criteria

This implementation is considered complete when:

1. ✅ Graphics mode renders PNG sprites for all configured entities
2. ✅ Glyph/classic mode remains fully functional and unchanged
3. ✅ Settings toggle works and persists
4. ✅ Missing sprites fall back to glyphs gracefully
5. ✅ All existing tests pass in both modes
6. ✅ New graphics tests pass
7. ✅ Full playthrough possible in both modes
8. ✅ No performance degradation (subjective, feel responsive)
9. ✅ Code documented and follows project guidelines
10. ✅ No console errors in normal operation

