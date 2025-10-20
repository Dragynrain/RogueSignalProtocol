# Claude Code Quick Guidelines

## 0. Planning & Estimates
- **NEVER provide time estimates** (hours, days, weeks) when planning work.
- You are bad at estimating. Focus on tasks, priorities, and dependencies instead.

## 0b. Performance
- **Don't worry about performance** until it's actually a problem affecting user experience.
- No preemptive optimization, benchmarking, or regression analysis.
- Focus on code clarity and correctness first.

---

## 1. Bash & Environment
- Quote paths: `cd "path with spaces"`.  
- Use bash cmds (`rm`, `ls`, `mkdir`), not Windows ones.  
- Run via `.venv/Scripts/python.exe`; install with `.venv/Scripts/pip.exe install <pkg>`.  

---

## 2. Compatibility
- **ASCII only**, no Unicode.  
- Target: Windows 10/11 (cmd/PowerShell).  
- Rendering: ASCII (main) + TCOD graphics (sync both).  

---

## 3. Project Rules
- A–Z = enemies only; everything else ASCII symbols.  
- Use latest deps (esp. `python-tcod`).  
- Delete save on death (no prompt).  

---

## 4. Code & Architecture
- Prefer simple functional code.  
- Keep files <2000 lines; split after ~1800.  
- One purpose per module.  
- No over-engineering or new frameworks.  
- Keep `build/` + `dist/` folders for releases.

---

## 5. Testing (Critical)
- Test with venv Python.  
- Update tests with every code change or API edit.  
- Prefer integration tests (real behavior) over mocks.  
- Use `tests/fixtures/` builders.  
- After refactor, run full suite & fix all, even unrelated tests.  
- Pre-commit: `python test_commands.py full`.

---

## 6. Logging & Errors
- **Console:** tech errors → `print()` / `logging.error()`.  
- **Game log:** gameplay messages → `MessageLog.add_message()`.  
- Don’t mix the two.  

**Config:**  
- Fail fast on missing files.  
- Required: `game_data.json`, `game_config.json`, `story_content.json`.  
- Only `user_settings.json` can default.  
- No hardcoded fallback values — all data from JSON.

---

## 7. Gameplay Systems
- Enemies alert others when spotting player.
- **All enemy movement uses queues**: FIFO, 3 size queue
- **Alert timer = 1 turn only.**
- Use TCOD FOV (`tcod.map.compute_fov`) and pathfinding (`tcod.path`) always.
- For TCOD API details, invoke the `tcod` skill.

---

## 7a. TCOD Array Indexing (CRITICAL - READ EVERY TIME)

**🚨 TCOD ARRAY INDEXING DEPENDS ON CONSOLE ORDER! 🚨**

This is the **#1 source of bugs** in this codebase. **NEVER assume indexing order!**

### The Game Uses order='F' (Fortran Order)

**Game console creation (game_loop.py:347):**
```python
console = tcod.console.Console(80, 50, order='F')
# → Array shape: (80, 50, 4) = (width, height, channels)
# → Indexing: [x, y, channel]
```

### ALWAYS Use CoordinateHelpers

```python
# ✓ CORRECT - handles order detection automatically
from game_coordinate_helpers import CoordinateHelpers

CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=255)
```

### Manual Array Access (ONLY if CoordinateHelpers can't be used)

```python
# ✓ CORRECT - detect order first
is_fortran = (console.rgba["bg"].shape[0] == console.width)

if is_fortran:  # Game uses this
    # order='F': use [x, y] indexing
    for x in range(width):
        for y in range(height):
            console.rgba["bg"][x, y, 3] = 255
else:  # Tests use this
    # default: use [y, x] indexing
    for y in range(height):
        for x in range(width):
            console.rgba["bg"][y, x, 3] = 255
```

### TCOD Functions (Always (x, y))

```python
# High-level TCOD functions ALWAYS use (x, y) regardless of order
console.print(x=10, y=5, "text")  # ✓ Always (x, y)
console.draw_rect(x=10, y=5, width=20, height=10, ...)  # ✓ Always (x, y)
```

**Why this matters:** Using wrong indexing sets values at **transposed coordinates**. The dialogue transparency bug was caused by using `[y, x]` indexing when the game needs `[x, y]` due to `order='F'`.

**See `.claude/TCOD_COORDINATE_SYSTEMS.md` for complete reference.**

---

## 7b. Graphics Rendering & Coordinate Systems (CRITICAL)

**Three Different Coordinate Systems - DO NOT MIX THEM:**

### 1. Console Character Coordinates (80x50 grid)
- Used for: Text rendering, UI layout, sprite positioning
- Range: X: 0-79, Y: 0-49
- Example: `render_char_safe(console, 10, 5, "text")`
- **Console rendered as texture with 10x16 pixel characters (tileset size)**

### 2. Game Viewport Coordinates (27x21 in graphics mode)
- Used for: Game map tile positions during gameplay
- Scaled based on viewport to fit window
- TileManager calculates tile dimensions (e.g., 65x54 pixels per tile)
- **Only used for in-game map rendering, NOT menus/help screens**

### 3. SDL Pixel Coordinates (window resolution, e.g., 2560x1351)
- Used for: Direct SDL sprite rendering
- Full window pixel space
- **Sprites rendered here must align with console texture**

**CRITICAL RULES:**

1. **Menu/Help Screens (GraphicalHelpMenu, etc.)**:
   - Console is ALWAYS 80x50 characters
   - **Sprite POSITIONING**: Calculate from console coords + window scaling
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
   - **Sprite SIZE**: Use TileManager dimensions (SAME AS IN-GAME!)
     ```python
     sprite_width = tile_manager.tile_width  # e.g., 65 pixels
     sprite_height = tile_manager.tile_height  # e.g., 54 pixels
     ```
   - Sprites should be same scale as in-game for consistency

2. **In-Game Rendering**:
   - Use TileManager.tile_width/height for both size AND positioning
   - These dimensions are viewport-scaled (e.g., 65x54 for 2x zoom)
   - Game area uses different coordinate system than menus

3. **Console Transparency**:
   - Set entire console background transparent: `console.rgba["bg"][:, :, 3] = 0`
   - Text rendering makes those areas opaque automatically
   - Sprites underneath show through transparent areas

**Common Mistakes**:
- Using tileset size (10x16) for sprite SIZE → tiny sprites
- Using tile dimensions (65x54) to multiply console coords → wrong positions
- Mixing positioning math between menus and in-game rendering

---

## 8. Docs & Research
- Always check latest official docs.
- Confirm API details before assuming limits and interfaces.
- **TCOD-specific questions**: Use the `tcod` skill (`.claude/skills/tcod.md`).

---

## 9. UI / UX
- Help text must exactly match in-game symbols and be kept up-to-date at all times.

---

## 10. Git & Attribution
- No `Co-Authored-By` or AI/Claude tags.  
- Keep commit messages clean and technical.
