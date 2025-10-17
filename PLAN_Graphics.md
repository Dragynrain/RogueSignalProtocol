# Rogue Signal Protocol - Graphics Implementation Plan
## Sprites-Only Architecture (Current Implementation)

---

## TABLE OF CONTENTS
1. [Current Implementation Status](#current-implementation-status)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Phases](#implementation-phases)
4. [Missing Sprites Inventory](#missing-sprites-inventory)
5. [Future Enhancements](#future-enhancements)

---

## CURRENT IMPLEMENTATION STATUS

### ✅ **COMPLETED: Sprites-Only Mode (Phase 0 + Phase 1)**

**Commits:**
- Phase 0 complete (cb86ed1)
- Phase 1 complete (d75180f)
- Simplified to sprites-only architecture (bd7f07f)

**What's Working:**
- **TileManager System**: Loads and caches 512x512 PNG sprites
- **Dynamic Scaling**: Sprites scale to window/tile size automatically
- **Transparency Support**: RGBA sprites with alpha channel blending
- **Lazy Loading**: Sprites load on-demand and cache for performance
- **JSON Configuration**: graphics_tiles.json maps entities to sprite files
- **Tintable System**: White sprites support color_mod tinting, colored sprites use outline boxes
- **Dual Rendering Paths**: SDL sprite rendering OR TCOD glyph fallback
- **Window Resize Handling**: Textures reload when window resized >10%
- **Fog of War**: Dimmed sprites for explored but not visible tiles

**Current File Structure:**
```
RogueSignalProtocol/
├── game_graphics_tiles.py          [TileManager - sprite loading/caching]
├── game_rendering.py                [GameRenderer, MapRenderer - rendering logic]
├── graphics_tiles.json              [Entity → sprite filename mappings]
├── graphics/                        [98 PNG sprites in 19 categories]
│   ├── player01.png...05.png
│   ├── scanner01.png...05.png
│   ├── patrol01.png...06.png
│   ├── bot01.png...03.png
│   ├── hunter01.png...07.png
│   ├── virus01.png...04.png
│   ├── inhibitor01.png...04.png
│   ├── firewall01.png...06.png
│   ├── avatar01.png...05.png
│   ├── floor01.png...06.png
│   ├── wall01.png...06.png
│   ├── codehack01.png...06.png       (tintable)
│   ├── exploit01.png...06.png        (tintable)
│   ├── coolingnode01.png...03.png
│   ├── coolingupgrade01.png...08.png
│   ├── cpunode01.png...03.png
│   ├── cpuupgrade01.png...10.png
│   ├── ramupgrade01.png...06.png
│   └── ghostnode01.png...04.png
```

**Rendering Pipeline (Graphics Mode):**
1. **Clear SDL Renderer** - Start with blank canvas
2. **Layer 1: Terrain Sprites** - Floor/wall tiles (with fog of war dimming)
3. **Layer 2A: Item Sprites** - Code hacks, exploits, nodes (with tinting for tintables)
4. **Layer 2B: Entity Sprites** - Player, enemies (with outline boxes for status)
5. **Layer 3: Console Overlay** - Text UI, messages, stats (TCOD console → texture → SDL)
6. **Present** - Composite all layers to screen

---

## ARCHITECTURE OVERVIEW

### Core Classes

#### **TileManager** (`game_graphics_tiles.py`)
**Responsibilities:**
- Load PNG sprites from graphics/ directory
- Scale 512x512 sprites to calculated tile dimensions
- Cache SDL textures for performance
- Track tintable vs non-tintable sprites
- Handle window resize (reload textures at new scale)
- Provide get_tile(), is_tintable(), has_sprite() API

**Key Methods:**
- `get_tile(entity_name)` - Get cached or load sprite texture
- `load_tile(entity_name)` - Load PNG, scale, upload to SDL
- `is_tintable(entity_name)` - Check if sprite uses color_mod tinting
- `check_and_handle_resize()` - Reload textures on window resize
- `preload_common_tiles()` - Load player/floor/wall at startup

#### **GameRenderer** (`game_rendering.py`)
**Responsibilities:**
- Coordinate all rendering (main game, menus, overlays)
- Delegate to MapRenderer for map/entity rendering
- Delegate to UIRenderer for text/UI rendering
- Handle graphics mode vs glyph mode switching
- Manage SDL renderer lifecycle

#### **MapRenderer** (`game_rendering.py`)
**Responsibilities:**
- Render game map in either graphics or glyph mode
- Calculate camera offset for scrolling
- Render terrain, items, entities in correct layers
- Apply fog of war effects (dimming for explored tiles)
- Apply visual effects (tinting, outline boxes, status indicators)

**Key Methods:**
- `render_sprites_layer(game)` - SDL sprite rendering (graphics mode)
- `render_game_area(console, game)` - TCOD glyph rendering (fallback)
- `_render_terrain_layer()` - Floors and walls
- `_render_items_layer()` - Code hacks, exploits, nodes
- `_render_entities_layer()` - Player and enemies
- `_apply_status_effects()` - Outline boxes for alerted/damaged enemies

#### **UIRenderer** (`game_rendering.py`)
**Responsibilities:**
- Render text-based UI elements
- Status bars (health, cooling, CPU, detection)
- Message log and system messages
- Inventory, help, lore screens
- Story fragments and dialogue

---

## IMPLEMENTATION PHASES

### ✅ **PHASE 0: Terminology Refactor (COMPLETED)**
**Goal:** Update codebase from "ASCII/graphics" to "glyph/graphics" terminology

**Tasks Completed:**
- [x] Updated all code references from "ASCII" to "glyph"
- [x] Updated user_settings.json migration (ascii → glyph)
- [x] Updated all test files and parametrized tests
- [x] Updated user-facing text (menus show "Classic Mode")
- [x] Updated documentation and comments
- [x] All tests passing (100% green)
- [x] Verified settings migration works correctly

**Commits:**
- Phase 0 complete (cb86ed1)

### ✅ **PHASE 1: Foundation & Sprite Loading System (COMPLETED)**
**Goal:** Set up TileManager infrastructure for loading and caching PNG sprites

**Tasks Completed:**
- [x] 1.1: Created TileManager class in game_graphics_tiles.py
  - Load PNG with PIL, preserve alpha channel
  - Scale 512x512 to calculated tile size using LANCZOS
  - Upload to SDL as RGBA texture with blend mode
  - Texture caching with lazy loading
  - Window resize detection and texture reload
  - Tintable flag system (white sprites vs colored sprites)
- [x] 1.2: Created graphics_tiles.json mapping configuration
  - Maps entities to PNG filenames
  - Tintable flags for each entity
  - Uses only '01' variants initially
- [x] 1.3: Integrated TileManager into game initialization
  - Initialized in game_loop.py
  - Passed to GameRenderer and MapRenderer
  - Context and settings passed through
- [x] 1.4: Implemented tile dimension calculation
  - Dynamic based on window size and grid
  - Accounts for UI panels
  - Supports window resize

**Commits:**
- Phase 1 complete (d75180f)

### ✅ **PHASE 2: Layered SDL Rendering Architecture (COMPLETED - SIMPLIFIED)**
**Goal:** Render sprites with layered SDL + console overlay system

**Tasks Completed:**
- [x] 2.1: Implemented layered sprite rendering in MapRenderer
  - Layer 1: Terrain sprites (floor/wall) with fog of war dimming
  - Layer 2A: Item sprites with color_mod tinting for tintables
  - Layer 2B: Entity sprites (player, enemies) without tinting
  - Layer 2.5: Status effect outline boxes over colored sprites
  - Layer 3: Console overlay for UI and glyph fallbacks
- [x] 2.2: Handled special rendering cases
  - Targeting cursor remains glyph overlay
  - Movement prediction remains glyph overlay
  - Vision overlays remain console background colors
  - Gateway uses glyph fallback (sprite TODO)
- [x] 2.3: Updated rendering flow in GameRenderer
  - SDL clear → sprites → boxes → console texture → present
  - Transparent console backgrounds in game area
  - Graphics mode vs glyph mode branching
- [x] 2.4: Console transparency coordination
  - Game area backgrounds alpha 0
  - UI panels keep solid backgrounds
  - Glyph fallbacks visible over sprites
- [x] 2.5: Dynamic window scaling
  - Detects >10% window size changes
  - Recalculates tile dimensions
  - Reloads all cached textures at new scale
  - Smart reload strategy (lazy reload on next access)

**Commits:**
- Simplified to sprites-only architecture (bd7f07f)

### 🚧 **PHASE 3: Configuration & Settings Integration (MOSTLY COMPLETE)**
**Goal:** Polish configuration and ensure settings work correctly

**Completed:**
- [x] 3.1: Tile mapping JSON schema
  - graphics_tiles.json structure defined
  - Validation in validate_json_config.py
  - All configured sprites load successfully
- [x] 3.2: Graphics mode toggle integration
  - Settings menu toggle works
  - Setting persists across sessions
  - Mode switches gracefully

**Remaining:**
- [ ] Add ramupgrade to graphics_tiles.json (file exists, not mapped)
- [ ] Validate all entity types have mappings or explicit fallbacks
- [ ] Add graphics quality/scaling settings (future)

### 🚧 **PHASE 4: Testing & Validation (PARTIAL)**
**Goal:** Comprehensive testing of graphics system

**Completed:**
- [x] 4.4: Updated existing tests
  - Tests parametrized for both glyph and graphics modes
  - Fixtures support graphics_mode parameter
  - Complete level playthrough works in both modes

**Remaining:**
- [ ] 4.1: Unit tests for TileManager
  - Test tile loading, caching, retrieval
  - Test dimension calculations
  - Test scaling and transparency
- [ ] 4.2: Integration tests for rendering
  - Test all entity types render correctly
  - Test mode switching
  - Test mixed sprite/glyph rendering
  - Test FOV and camera in graphics mode
- [ ] 4.3: Visual regression testing
  - Screenshot comparison strategy
  - Test maps with all entity types
  - Reference screenshots

### 🚧 **PHASE 5: Polish & Missing Pieces (IN PROGRESS)**
**Goal:** Complete missing sprites and add polish

**Completed:**
- [x] 5.2: Error handling & logging
  - Robust error handling in TileManager
  - Graceful fallback to glyph mode
  - Detailed logging of sprite load failures

**Remaining:**
- [ ] 5.1: Document missing sprites (THIS DOCUMENT NOW INCLUDES THIS)
  - Gateway/exit sprite (CRITICAL)
  - Story fragment sprite (CRITICAL)
  - Vision overlay sprites (OPTIONAL - keep glyphs)
  - Patrol prediction sprites (OPTIONAL - keep glyphs)
  - Targeting cursor sprite (OPTIONAL - keep glyphs)

### 🚧 **PHASE 6: Documentation & Completion (PARTIAL)**
**Goal:** Complete documentation and final polish

**Completed:**
- [x] 6.1: Code documentation
  - Docstrings in TileManager
  - Comments in rendering code
  - JSON format documented

**Remaining:**
- [ ] 6.2: Developer documentation
  - graphics/README.md - sprite creation guide
  - How to add new sprites
  - Testing new sprites
- [ ] 6.3: Final testing checklist (see below)
  - All tests pass in both modes
  - Manual playthroughs complete
  - No memory leaks
  - Performance acceptable
  - All sprites load correctly

---

## MISSING SPRITES INVENTORY

### Critical Missing Sprites (Block Sprites-Only Completion)

#### **1. Gateway/Exit Sprite**
- **Current Rendering:** '>' character in glyph mode, **missing in graphics mode**
- **Purpose:** Exit to next level
- **Location:** game_rendering.py:1643-1647 (_render_gateway)
- **Suggested Specs:**
  - 512x512 PNG with alpha channel
  - Filename: `gateway01.png` (or portal01.png, exit01.png)
  - Visual: Glowing portal/exit/doorway with subtle animation potential
  - Tintable: false (colored sprite)
  - Colors: Cyan/blue glow to stand out from environment

#### **2. Story Fragment Sprite**
- **Current Rendering:** '!' character, **no sprite alternative**
- **Purpose:** Story/lore pickups scattered in levels
- **Location:** Items system, rendered in _render_items_layer
- **Suggested Specs:**
  - 512x512 PNG with alpha channel
  - Filename: `storyfragment01.png` (or lore01.png, document01.png)
  - Visual: Glowing document/data fragment/hologram
  - Tintable: false (colored sprite)
  - Colors: Soft white/gold glow to indicate collectible

### JSON Configuration Updates Needed

#### **3. RAM Upgrade Mapping**
- **Status:** Sprite files exist (ramupgrade01.png through ramupgrade06.png) but not mapped in graphics_tiles.json
- **Action Required:** Add to "items" section:
  ```json
  "ram_upgrade": {
    "file": "ramupgrade01.png",
    "tintable": false,
    "_comment": "RAM permanent upgrade"
  }
  ```

### UI/Overlay Elements (Lower Priority)

#### **4. Targeting Cursor**
- **Current Rendering:** 'X' character overlay (console layer 3)
- **Purpose:** Show which tile player is targeting for abilities
- **Status:** Works fine as glyph overlay, sprite version optional
- **If Implementing:**
  - Could be a semi-transparent crosshair sprite
  - Or keep as glyph overlay (recommended for clarity)

#### **5. Movement Prediction Indicators**
- **Current Rendering:** '.', '1', '2', '3' characters showing enemy next moves
- **Purpose:** Show patrol routes and predicted enemy positions
- **Status:** Works as glyph overlay, sprite version optional
- **If Implementing:**
  - Semi-transparent footprints or directional arrows
  - Or keep as glyph overlay (recommended for performance)

#### **6. Vision Overlay Effects**
- **Current Rendering:** Console background color tinting
- **Purpose:** Show enemy vision cones/ranges
- **Status:** Works with console effects, sprite version optional
- **If Implementing:**
  - Semi-transparent colored overlays for vision cones
  - Or keep as console background tinting (current approach works)

---

## TESTING CHECKLIST

### Graphics Mode Validation:
- [ ] All entities render correctly in graphics mode
- [ ] Fog of war dimming works for explored tiles
- [ ] Tintable sprites show correct colors (code hacks by type)
- [ ] Outline boxes render for alerted/damaged enemies
- [ ] Window resize triggers texture reload correctly
- [ ] Performance stays 60+ FPS in graphics mode
- [ ] Memory usage reasonable (<200MB for textures)
- [ ] Graceful fallback to glyph mode if graphics fail

### Glyph Mode Validation (Fallback):
- [ ] All entities render with correct glyphs if sprites missing
- [ ] Colors preserved in glyph fallback mode
- [ ] No performance degradation in glyph mode
- [ ] Switching between graphics/glyph modes works seamlessly

### Cross-Platform:
- [ ] Sprite loading works on Windows
- [ ] Sprite loading works on Linux (if targeting)
- [ ] File paths use os.path.join for cross-platform compatibility
- [ ] Executable deployment includes graphics/ directory

---

## DEVELOPMENT NOTES

### Code Quality:
- All sprite-related code in game_graphics_tiles.py (single responsibility)
- Rendering logic in game_rendering.py (separation of concerns)
- JSON configuration for easy sprite swapping
- Comprehensive error handling and fallbacks
- Logging for debugging sprite load failures