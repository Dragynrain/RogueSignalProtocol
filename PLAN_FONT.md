# Font Replacement Plan: CascadiaCode TTF

**Objective:** Replace `terminal10x16_gs_ro.png` bitmap tileset with `CascadiaCode-VariableFont_wght.ttf` TrueType font for better scaling and visual quality.

**Current State:**
- Using 10×16 pixel bitmap tileset with CP437 encoding
- 256 character grid (16×16 layout)
- Special symbols accessed via `tcod.tileset.CHARMAP_CP437[index]`

**Target State:**
- Using CascadiaCode TrueType font with Unicode characters
- Scalable to any resolution without blur
- Direct Unicode character usage instead of CP437 indices
- **32×32 tile dimensions** for excellent quality at high resolutions

---

## 📋 Executive Summary

**What:** Replace bitmap PNG tileset with scalable TrueType font
**Why:** Crisp rendering at high resolutions (1440p+), easier to modify
**Effort:** 4-5 hours total implementation + testing
**Risk:** Low - straightforward migration, well-supported by TCOD

### Key Decisions ✅

1. **Tile Size:** 32×32 pixels (high quality for 1440p+ displays)
2. **Player Character:** Use ☺ (U+263A) instead of ☻ (not in CascadiaCode)
3. **Box Drawing:** Double-line boxes (`║ ═ ╔ ╗ ╚ ╝`) for dialogues, single-line for gameplay
4. **Symbol Migration:** Get basic implementation working first, upgrade to fancy Unicode later

### Files to Change

- **Create new:** `game_unicode_chars.py` (character constants)
- **Update:** `game_loop.py` (1 function - font loading)
- **Update:** `game_rendering_glyphs.py` (21 replacements)
- **Update:** `game_rendering_graphics.py` (3 replacements)
- **Update:** `game_dialogue_system.py` (optional - double-line boxes)
- **Update:** `tests/visual_test_coordinate_helpers.py` (1 line)
- **Update:** Build scripts (include TTF)
- **Update:** Documentation (CLAUDE.md, README_DEV.md)

### What Gets Better

✨ **Crisp text at any resolution** (no more pixelation when scaled)
✨ **Better-looking dialogues** (double-line boxes!)
✨ **Easier font customization** (just swap TTF file)
✨ **Smaller font file** (703KB vs PNG + easier to version)

---

## Phase 1: Font File Setup ✅

**Status:** Font file already exists at project root!
- `CascadiaCode-VariableFont_wght.ttf` ✓ (703.4 KB)

**Action Items:**
- [x] Verify font file exists
- [x] Verify required Unicode glyphs (see character mapping below)
- [x] Determine optimal tile dimensions for font → **32×32 decided**

**Tile Dimensions - DECIDED:**
- **Current:** 10×16 pixels (aspect ratio 0.625:1)
- **New:** 32×32 pixels (square, 1:1 aspect ratio)
- **Rationale:** Excellent quality for high-resolution displays, crisp text rendering

---

## Phase 2: Character Mapping (CP437 → Unicode)

### Currently Used CP437 Special Characters

The game uses these CP437 indices that need Unicode equivalents:

| CP437 Index | CP437 Glyph | Unicode | Unicode Char | In CascadiaCode? | Final Choice |
|-------------|-------------|---------|--------------|------------------|--------------|
| 2 | ☻ | U+263B | ☻ | ❌ NO | **☺ (U+263A)** ✅ |
| 3 | ♥ | U+2665 | ♥ | ✅ YES | ♥ |
| 4 | ♦ | U+2666 | ♦ | ✅ YES | ♦ |
| 6 | ♠ | U+2660 | ♠ | ✅ YES | ♠ |
| 7 | • | U+2022 | • | ✅ YES | • |
| 8 | ◘ | U+25D8 | ◘ | ⚠️ MAYBE | ● (U+25CF) if needed |
| 9 | ○ | U+25CB | ○ | ✅ YES | ○ |
| 10 | ◙ | U+25D9 | ◙ | ⚠️ MAYBE | ◉ (U+25C9) if needed |
| 14 | ♫ | U+266B | ♫ | ✅ YES | ♫ |
| 21 | § | U+00A7 | § | ✅ YES | § |
| 179 | │ | U+2502 | │ | ✅ YES | │ |
| 180 | ┤ | U+2524 | ┤ | ✅ YES | ┤ |
| 191 | ┐ | U+2510 | ┐ | ✅ YES | ┐ |
| 192 | └ | U+2514 | └ | ✅ YES | └ |
| 193 | ┴ | U+2534 | ┴ | ✅ YES | ┴ |
| 194 | ┬ | U+252C | ┬ | ✅ YES | ┬ |
| 195 | ├ | U+251C | ├ | ✅ YES | ├ |
| 196 | ─ | U+2500 | ─ | ✅ YES | ─ |
| 197 | ┼ | U+253C | ┼ | ✅ YES | ┼ |
| 217 | ┘ | U+2518 | ┘ | ✅ YES | ┘ |
| 218 | ┌ | U+250C | ┌ | ✅ YES | ┌ |
| 254 | ■ | U+25A0 | ■ | ✅ YES | ■ |

### Double-Line Box Drawing (For Dialogues)

**New additions for dialogue boxes:**

| Unicode | Character | Usage |
|---------|-----------|-------|
| U+2551 | ║ | Vertical double line |
| U+2550 | ═ | Horizontal double line |
| U+2554 | ╔ | Top-left corner double |
| U+2557 | ╗ | Top-right corner double |
| U+255A | ╚ | Bottom-left corner double |
| U+255D | ╝ | Bottom-right corner double |

**All verified present in CascadiaCode** ✅

**CascadiaCode Compatibility Summary:**
- ✅ All box-drawing characters (single + double line)
- ✅ All card suits (♠ ♥ ♦ ♣)
- ✅ Most geometric shapes (○ ● ■)
- ✅ Musical notes (♫)
- ✅ Common symbols (§ •)
- ❌ Some ornamental characters (☻ not present - using ☺ instead)
- ⚠️ Inverse bullets may need fallbacks (will test during implementation)

---

## Phase 3: Code Changes

### 3.1 Create Unicode Character Constants

**New file:** `game_unicode_chars.py`

```python
"""
Unicode character constants for game rendering.

Replaces CP437 index-based character access with direct Unicode.
All characters verified to exist in CascadiaCode font.
"""

class GameGlyphs:
    """Unicode characters for game rendering."""

    # Player and entities
    PLAYER = '☺'  # U+263A - White smiling face (☻ U+263B not in CascadiaCode)

    # Status effects (overlays)
    COOLING = '♦'      # U+2666 - Diamond
    CPU_OVERLOAD = '♥'  # U+2665 - Heart
    GHOST_MODE = '♠'    # U+2660 - Spade

    # Terrain
    FLOOR_EXPLORED = '•'  # U+2022 - Bullet
    SHADOW = '◘'          # U+25D8 - Inverse bullet (fallback: '●' U+25CF if needed)

    # UI indicators
    TARGETING = '○'    # U+25CB - Circle
    CIRCLE_DOT = '◙'   # U+25D9 - Inverse circle (fallback: '◉' U+25C9 if needed)

    # Items and special
    STORY_FRAGMENT = '♫'  # U+266B - Musical notes
    SECTION = '§'         # U+00A7 - Section sign

    # Walls - Single-line (for gameplay/menus)
    WALL_VERTICAL = '│'    # U+2502
    WALL_HORIZONTAL = '─'  # U+2500
    WALL_TOP_LEFT = '┌'    # U+250C
    WALL_TOP_RIGHT = '┐'   # U+2510
    WALL_BOTTOM_LEFT = '└'  # U+2514
    WALL_BOTTOM_RIGHT = '┘' # U+2518
    WALL_T_LEFT = '┤'      # U+2524
    WALL_T_RIGHT = '├'     # U+251C
    WALL_T_UP = '┴'        # U+2534
    WALL_T_DOWN = '┬'      # U+252C
    WALL_CROSS = '┼'       # U+253C
    WALL_ISOLATED = '■'    # U+25A0 - Small square

    # Walls - Double-line (for dialogues only)
    DIALOGUE_VERTICAL = '║'      # U+2551
    DIALOGUE_HORIZONTAL = '═'    # U+2550
    DIALOGUE_TOP_LEFT = '╔'      # U+2554
    DIALOGUE_TOP_RIGHT = '╗'     # U+2557
    DIALOGUE_BOTTOM_LEFT = '╚'   # U+255A
    DIALOGUE_BOTTOM_RIGHT = '╝'  # U+255D

    # Map CP437 indices to Unicode for backwards compatibility during transition
    CP437_MAP = {
        2: PLAYER,
        3: CPU_OVERLOAD,
        4: COOLING,
        6: GHOST_MODE,
        7: FLOOR_EXPLORED,
        8: SHADOW,
        9: TARGETING,
        10: CIRCLE_DOT,
        14: STORY_FRAGMENT,
        21: SECTION,
        179: WALL_VERTICAL,
        180: WALL_T_LEFT,
        191: WALL_TOP_RIGHT,
        192: WALL_BOTTOM_LEFT,
        193: WALL_T_UP,
        194: WALL_T_DOWN,
        195: WALL_T_RIGHT,
        196: WALL_HORIZONTAL,
        197: WALL_CROSS,
        217: WALL_BOTTOM_RIGHT,
        218: WALL_TOP_LEFT,
        254: WALL_ISOLATED,
    }
```

### 3.2 Update Font Loading

**File:** `game_loop.py:50-59`

**Current code:**
```python
def load_tileset():
    """Load terminal tileset - no fallbacks, missing font indicates corrupt installation."""

    # Load terminal tileset
    # terminal10x16 means each glyph is 10 pixels wide x 16 pixels tall
    # The tilesheet has 16 columns x 16 rows of glyphs
    tileset = tcod.tileset.load_tilesheet(
        "terminal10x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437
    )
    return tileset
```

**New code:**
```python
def load_tileset():
    """Load TrueType font for terminal rendering."""

    # Load CascadiaCode TrueType font
    # tile_width/tile_height set the pixel dimensions of each character cell
    # 32×32 provides excellent quality for high-resolution displays
    tileset = tcod.tileset.load_truetype_font(
        "CascadiaCode-VariableFont_wght.ttf",
        tile_width=32,   # 32 pixels wide
        tile_height=32   # 32 pixels tall
    )
    return tileset
```

**Note:** Removed bitmap-specific comment about grid layout. TTF fonts render at specified pixel dimensions.

### 3.3 Update Dialogue Box Rendering (Double-Line Boxes)

**File:** `game_dialogue_system.py`

Search for existing box-drawing characters and replace with double-line variants:

**Find:** `'│'`, `'─'`, `'┌'`, `'┐'`, `'└'`, `'┘'`
**Replace with:** `GameGlyphs.DIALOGUE_VERTICAL`, etc.

**Example (wherever dialogue boxes are rendered):**
```python
# OLD
console.print(x, y, "┌─────────┐")
console.print(x, y+1, "│ Dialogue │")
console.print(x, y+2, "└─────────┘")

# NEW
from game_unicode_chars import GameGlyphs
console.print(x, y, f"{GameGlyphs.DIALOGUE_TOP_LEFT}{'═'*width}{GameGlyphs.DIALOGUE_TOP_RIGHT}")
console.print(x, y+1, f"{GameGlyphs.DIALOGUE_VERTICAL} Dialogue {GameGlyphs.DIALOGUE_VERTICAL}")
console.print(x, y+2, f"{GameGlyphs.DIALOGUE_BOTTOM_LEFT}{'═'*width}{GameGlyphs.DIALOGUE_BOTTOM_RIGHT}")
```

**Note:** This is optional enhancement - can be done after basic migration works!

### 3.4 Update Rendering Code (Main Changes)

**Files to update:**
- `game_rendering_glyphs.py` (21 occurrences)
- `game_rendering_graphics.py` (3 occurrences)
- `game_dialogue_system.py` (optional - double-line boxes)

**Pattern to replace:**

**OLD:**
```python
chr(tcod.tileset.CHARMAP_CP437[4])  # Diamond
```

**NEW:**
```python
from game_unicode_chars import GameGlyphs
GameGlyphs.COOLING  # Direct Unicode character
```

**Detailed changes by file:**

#### `game_rendering_glyphs.py`

**Line 101:** Cooling effect
```python
# OLD
render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[4]), fg=cooling_color, bg=Colors.BLACK)
# NEW
render_char_safe(console, screen_x, screen_y, GameGlyphs.COOLING, fg=cooling_color, bg=Colors.BLACK)
```

**Line 105:** CPU overload
```python
# OLD
render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[3]), fg=cpu_color, bg=Colors.BLACK)
# NEW
render_char_safe(console, screen_x, screen_y, GameGlyphs.CPU_OVERLOAD, fg=cpu_color, bg=Colors.BLACK)
```

**Line 109:** Ghost mode
```python
# OLD
render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[6]), fg=ghost_color, bg=Colors.BLACK)
# NEW
render_char_safe(console, screen_x, screen_y, GameGlyphs.GHOST_MODE, fg=ghost_color, bg=Colors.BLACK)
```

**Lines 121, 125, 129:** Walls and floors (remembered/explored)
```python
# Line 121 - Wall character (uses dynamic function, see below)
# Line 125 - Shadow
render_char_safe(console, screen_x, screen_y, GameGlyphs.SHADOW, fg=shadow_remembered, bg=Colors.BLACK)
# Line 129 - Floor explored
render_char_safe(console, screen_x, screen_y, GameGlyphs.FLOOR_EXPLORED, fg=floor_explored, bg=Colors.BLACK)
```

**Lines 157, 161, 176, 180, 195, 199:** Status effects (visible tiles)
- Same pattern as above, use GameGlyphs constants

**Line 219:** Enemy marker
```python
# OLD
render_char_safe(console, screen_x, screen_y, chr(tcod.tileset.CHARMAP_CP437[21]), fg=actual_color, bg=Colors.BLACK)
# NEW
render_char_safe(console, screen_x, screen_y, GameGlyphs.SECTION, fg=actual_color, bg=Colors.BLACK)
```

**Lines 254, 258, 261, 264:** Items
```python
# Line 254
render_char_safe(console, screen_x, screen_y, GameGlyphs.CIRCLE_DOT, fg=color, bg=Colors.BLACK)
# Line 258
render_char_safe(console, screen_x, screen_y, GameGlyphs.STORY_FRAGMENT, fg=fragment_color, bg=Colors.BLACK)
# Line 261
render_char_safe(console, screen_x, screen_y, GameGlyphs.SHADOW, fg=(80, 40, 120), bg=Colors.BLACK)
# Line 264
render_char_safe(console, screen_x, screen_y, GameGlyphs.FLOOR_EXPLORED, fg=Colors.FLOOR, bg=Colors.BLACK)
```

**Lines 515, 520, 525:** Targeting circles
```python
symbol = GameGlyphs.TARGETING
```

**Line 659:** Player character
```python
# OLD
render_char_safe(console, console_x, console_y, chr(tcod.tileset.CHARMAP_CP437[2]), fg=player_color, bg=Colors.BLACK)
# NEW
render_char_safe(console, console_x, console_y, GameGlyphs.PLAYER, fg=player_color, bg=Colors.BLACK)
```

#### `game_rendering_glyphs.py` - Wall Character Function

**Lines 267-309:** `_get_smart_wall_character()` function

**Current approach:** Returns CP437 index (int)
**New approach:** Return Unicode character (str)

**OLD:**
```python
def _get_smart_wall_character(self, game_map, x: int, y: int) -> int:
    """Get the appropriate wall character based on neighboring walls."""
    # ... logic ...
    if n and s and e and w:
        return 197  # ┼ cross
    # ... etc ...
```

**NEW:**
```python
def _get_smart_wall_character(self, game_map, x: int, y: int) -> str:
    """Get the appropriate wall character based on neighboring walls."""
    from game_unicode_chars import GameGlyphs

    # Check which directions have walls
    n = game_map.is_wall(Position(x, y - 1))
    s = game_map.is_wall(Position(x, y + 1))
    e = game_map.is_wall(Position(x + 1, y))
    w = game_map.is_wall(Position(x - 1, y))

    # Return Unicode box-drawing characters
    if n and s and e and w:
        return GameGlyphs.WALL_CROSS  # ┼
    elif n and s and e and not w:
        return GameGlyphs.WALL_T_RIGHT  # ├
    elif n and s and not e and w:
        return GameGlyphs.WALL_T_LEFT  # ┤
    elif n and not s and e and w:
        return GameGlyphs.WALL_T_UP  # ┴
    elif not n and s and e and w:
        return GameGlyphs.WALL_T_DOWN  # ┬
    elif n and not s and e and not w:
        return GameGlyphs.WALL_BOTTOM_LEFT  # └
    elif n and not s and not e and w:
        return GameGlyphs.WALL_BOTTOM_RIGHT  # ┘
    elif not n and s and e and not w:
        return GameGlyphs.WALL_TOP_LEFT  # ┌
    elif not n and s and not e and w:
        return GameGlyphs.WALL_TOP_RIGHT  # ┐
    elif n and s and not e and not w:
        return GameGlyphs.WALL_VERTICAL  # │
    elif not n and not s and e and w:
        return GameGlyphs.WALL_HORIZONTAL  # ─
    # Handle stubs
    elif n and not s and not e and not w:
        return GameGlyphs.WALL_VERTICAL  # │
    elif not n and s and not e and not w:
        return GameGlyphs.WALL_VERTICAL  # │
    elif not n and not s and e and not w:
        return GameGlyphs.WALL_HORIZONTAL  # ─
    elif not n and not s and not e and w:
        return GameGlyphs.WALL_HORIZONTAL  # ─
    # Isolated wall
    else:
        return GameGlyphs.WALL_ISOLATED  # ■
```

**Update call sites:**
```python
# Lines 119, 121 (remembered walls)
wall_char = self._get_smart_wall_character(game_map, world_pos.x, world_pos.y)
render_char_safe(console, screen_x, screen_y, wall_char, fg=wall_dark, bg=Colors.BLACK)

# Lines 141, 142 (visible walls)
wall_char = self._get_smart_wall_character(game_map, world_pos.x, world_pos.y)
render_char_safe(console, screen_x, screen_y, wall_char, fg=Colors.WALL, bg=Colors.BLACK)
```

**Note:** Remove `chr(tcod.tileset.CHARMAP_CP437[wall_char])` wrapper - function now returns string directly!

#### `game_rendering_graphics.py`

**Lines 394, 397, 400:** Status effect glyphs in graphics mode

```python
# Line 394
glyph = ord(GameGlyphs.COOLING)  # Keep ord() to get Unicode codepoint
# Line 397
glyph = ord(GameGlyphs.CPU_OVERLOAD)
# Line 400
glyph = ord(GameGlyphs.GHOST_MODE)
```

**Note:** `ord()` is still needed here because these are used as glyph indices, not direct rendering.

### 3.4 Update Build Scripts

**Files to update:**
- `build/build.bat`
- `.github/workflows/release.yml` (if exists)
- `build/pyinstaller.spec` (if exists)

**Ensure TTF font is included in build:**

**PyInstaller spec file:**
```python
datas=[
    ('CascadiaCode-VariableFont_wght.ttf', '.'),
    # ... other data files ...
]
```

**Or in build.bat:**
```batch
REM Copy font file to dist
copy CascadiaCode-VariableFont_wght.ttf dist\
```

---

## Phase 3.5: Update Test Files

**File to update:** `tests/visual_test_coordinate_helpers.py`

**Line 59-61 - Current code:**
```python
tileset = tcod.tileset.load_tilesheet(
    "assets/terminal10x16_gs_ro.png", 16, 16, tcod.tileset.CHARMAP_CP437
)
```

**New code:**
```python
tileset = tcod.tileset.load_truetype_font(
    "../CascadiaCode-VariableFont_wght.ttf", 32, 32
)
```

**Note:** This is the ONLY test file that needs updating! Other tests don't directly use tilesets.

---

## Phase 4: Testing

### 4.1 Visual Testing Checklist

**Test each character renders correctly:**

- [ ] Player character (**☺** U+263A - changed from ☻)
- [ ] Walls (all box-drawing variants: │ ─ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼)
- [ ] Dialogue boxes (double-line: ║ ═ ╔ ╗ ╚ ╝)
- [ ] Floor tiles (• for explored)
- [ ] Shadow/remembered tiles (◘ or ● if fallback needed)
- [ ] Status effects:
  - [ ] Cooling (♦)
  - [ ] CPU overload (♥)
  - [ ] Ghost mode (♠)
- [ ] Targeting circles (○)
- [ ] Story fragments (♫)
- [ ] Items and pickups
- [ ] Enemy markers (§)

### 4.2 Functional Testing

- [ ] Run game in glyph mode
- [ ] Run game in graphics mode (console overlay should use new font)
- [ ] Test all game screens:
  - [ ] Main menu
  - [ ] Gameplay
  - [ ] Inventory
  - [ ] Help screen
  - [ ] Lore viewer
  - [ ] Dialogue boxes (verify double-line borders if implemented)
- [ ] Test at different resolutions:
  - [ ] 1920×1080
  - [ ] 2560×1440
  - [ ] Windowed mode
  - [ ] Fullscreen
- [ ] Verify text readability (32×32 should be very crisp!)
- [ ] Check for missing/broken characters (� replacement character)

### 4.3 Performance Testing

- [ ] Measure startup time (TTF loading may be slightly slower than bitmap)
- [ ] Check FPS during gameplay (should be unchanged)
- [ ] Memory usage comparison (TTF in memory vs bitmap)
- [ ] Test on lower-end hardware if possible

### 4.4 Fallback Character Testing

**Characters that may need fallbacks:**

| Character | Primary | Fallback if Needed |
|-----------|---------|-------------------|
| Player | ☺ (U+263A) | @ (U+0040) |
| Shadow | ◘ (U+25D8) | ● (U+25CF) |
| Circle dot | ◙ (U+25D9) | ◉ (U+25C9) |

**During testing:** If you see � (replacement character), use the fallback!

**Document final character choices in code comments.**

---

## Phase 5: Understanding Console vs Graphics Scaling

**Important:** Console (TTF) and Graphics (sprites) are SEPARATE rendering systems!

### Console (TTF Font) - UI Overlay
- **Fixed grid:** 80×50 characters always
- **TTF tile size:** 32×32 pixels = rasterization quality only
- **Actual screen size:** Scales to fill window (e.g., 2560×1440 window)
- **Used for:** Status bars, menus, message log, dialogue boxes

**Example at 2560×1440:**
- Console: 80 columns × 50 rows
- Each character cell: 2560/80 = 32px wide, 1440/50 = 28.8px tall
- TTF 32×32 gets rasterized, then scaled to fit cell
- **Result:** Very crisp text!

### Graphics Mode (PNG Sprites) - Gameplay Visuals
- **Viewport:** 27×21 tiles (smaller than console for zoom effect)
- **Sprite size:** Dynamically calculated from window size
- **Used for:** Player, enemies, terrain, items

**Example at 2560×1440:**
- Game area: 80 characters wide, ~27 rows tall (after status bar)
- Viewport: 27×21 tiles
- Each sprite: ~94px wide × ~80px tall (calculated dynamically)
- **Result:** Large, zoomed-in sprites

### Why They Don't Match
| System | Purpose | Size at 1440p |
|--------|---------|---------------|
| Console | Text/UI | 32×28.8px per cell |
| Sprites | Gameplay | 94×80px per sprite |
| **Ratio** | Different purposes | ~3× larger |

**This is intentional design:**
- Console provides crisp text overlay
- Sprites provide detailed gameplay visuals
- They're composited as separate layers (see `.claude/RENDERING_ARCHITECTURE.md`)

**32×32 TTF choice:** Excellent for text quality, independent of sprite size!

---

## Phase 5.5: Build Script Updates

**Files to update:**
- `build/build.bat`
- `build/pyinstaller.spec` (if exists)

**Ensure TTF font is included in build:**

**In build.bat** - verify font is copied:
```batch
REM Copy font file to dist
copy CascadiaCode-VariableFont_wght.ttf dist\
```

**In PyInstaller spec** (if using):
```python
datas=[
    ('CascadiaCode-VariableFont_wght.ttf', '.'),
    # ... other data files ...
]
```

**Critical:** Without this, builds will fail with "Font not found" error!

---

## Phase 6: Documentation Updates

### ✅ Files Updated:

**`.claude/CLAUDE.md`:** ✅ DONE
- Changed "ASCII only, no Unicode" to full Unicode support
- Added CascadiaCode TrueType font details (32×32)
- Updated rendering description

**`README_DEV.md`:** ✅ DONE
- Changed "ASCII only (no Unicode in game text)" to Unicode character set
- Added CascadiaCode font details

**Still to update:**

**`build/BUILD_GUIDE.md`:**
- Add `CascadiaCode-VariableFont_wght.ttf` to required files list
- Document that font must be included in dist

**`.gitignore`:**
- Verify CascadiaCode-VariableFont_wght.ttf is NOT ignored
- TTF font is a required asset (703KB - acceptable for git)

---

## Phase 6.5: JSON Config Analysis

### Finding: No Font Config Needed ✅

**Checked files:**
- `game_rules.json` - Has `tile_width/tile_height` but those are for **sprite scaling**, not console font
- `user_settings.json` - Has `graphics_mode` but no font settings

**Decision:** **Do NOT add font config to JSON**

**Rationale:**
1. **Font size (32×32) is a code constant** like console grid (80×50) - not user-configurable
2. **Font path is hardcoded** - users don't swap fonts
3. **Keeps it simple** - one less thing to configure/test
4. **Existing tile_width/tile_height** in game_rules.json are for graphics mode sprites, unrelated to TTF
5. **Can add later if needed** - easy to expose as setting in future

**The tile_width/tile_height in game_rules.json:**
```json
"min_tile_width": 8,
"min_tile_height": 8,
"fallback_tile_width": 10,
"fallback_tile_height": 16
```

These are for **sprite dimensions** (graphics mode), NOT for console font size. Different system entirely!

**Console TTF:** 32×32 pixels (rasterization quality)
**Sprite tiles:** Dynamically calculated from window size (e.g., 94×80px at 1440p)

**No JSON changes needed!** ✅

---

## Phase 7: Cleanup

### Optional: Remove old assets

**After successful migration:**
- Archive `terminal10x16_gs_ro.png` (don't delete immediately!)
- Move to `archive/` folder or rename to `.old`
- Keep for at least one release cycle in case rollback needed

### Update .gitignore if needed

Font files are binary, but TTF is much smaller than PNG tilesets:
- `terminal10x16_gs_ro.png`: ~20KB
- `CascadiaCode-VariableFont_wght.ttf`: ~500KB (variable font)

Both should be committed to git (they're required assets).

---

## Rollback Plan

**If TTF migration fails:**

1. Revert `game_loop.py:load_tileset()` to use PNG
2. Revert rendering code changes (keep GameGlyphs file but use CP437 wrapper)
3. Keep both fonts in project until confident

**Temporary compatibility layer:**

```python
# In game_unicode_chars.py
USE_UNICODE = True  # Toggle for testing

def get_glyph(cp437_index):
    """Get character for rendering (supports both modes)."""
    if USE_UNICODE:
        return GameGlyphs.CP437_MAP.get(cp437_index, '?')
    else:
        return chr(tcod.tileset.CHARMAP_CP437[cp437_index])
```

---

## Risk Assessment

### Low Risk ✅
- Font file already in project
- CascadiaCode has excellent Unicode support
- TTF loading is well-supported by TCOD
- Changes are isolated to rendering code

### Medium Risk ⚠️
- Some ornamental characters might not be in CascadiaCode
- Tile dimensions may need tuning for optimal appearance
- Build scripts need updating

### High Risk ❌
- None identified - this is a straightforward migration

---

## Timeline Estimate

**Phase 1:** ✅ Done (font file exists)
**Phase 2:** ✅ Done (character mapping decided)
**Phase 3:** 2-3 hours (code changes - ~24 occurrences across 3 files)
**Phase 3.5:** 5 minutes (one test file update)
**Phase 4:** 1-2 hours (comprehensive testing)
**Phase 5:** Already done (32×32 decided, no tuning needed)
**Phase 5.5:** 10 minutes (build script updates)
**Phase 6-7:** 30 minutes (documentation + cleanup)

**Total: 4-5 hours** for complete implementation and testing.

---

## Success Criteria

✅ **Complete when:**
1. All CP437 indices replaced with Unicode characters (☺ for player, etc.)
2. Game renders correctly in both glyph and graphics modes
3. All special characters display properly at 32×32 resolution
4. Double-line boxes render in dialogues (optional but cool!)
5. No visual regressions compared to bitmap font (should look better!)
6. Performance is acceptable (startup may be slightly slower)
7. Build includes TTF and produces working executable
8. Test file updated and passes
9. Text is crisp and readable at all resolutions

---

## Next Steps

1. **Run visual test:** Launch game, verify CascadiaCode has all needed glyphs
2. **Create GameGlyphs file** with character constants
3. **Update game_loop.py** font loading
4. **Batch replace** CP437 references in rendering files
5. **Test thoroughly** across all game screens
6. **Tune dimensions** for optimal appearance
7. **Commit changes** with clear commit message

**Recommended commit message:**
```
Replace bitmap tileset with CascadiaCode TrueType font

- Switch from terminal10x16_gs_ro.png to CascadiaCode TTF
- Replace CP437 index-based characters with direct Unicode
- Add game_unicode_chars.py with GameGlyphs constants
- Update all rendering code to use Unicode characters
- Improves scaling quality at high resolutions
- Font now scales cleanly to any size without pixelation
```

---

## ✅ All Questions Answered

1. **Tile dimensions:** ✅ **32×32** (decided)
2. **Player character:** ✅ **☺ (U+263A)** instead of ☻ (decided)
3. **Box drawing:** ✅ **Double-line for dialogues** (decided)
4. **Symbol upgrades:** ✅ **Later - get it working first** (decided)
5. **Keep old font?** ⏸️ **Archive after successful migration** (defer)
6. **Test coverage:** ⏸️ **Run full test suite after implementation** (defer)

**Ready to implement!** All critical decisions made.
