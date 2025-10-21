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

## 5. Testing & Verification (Critical)

**ALWAYS TEST BEFORE COMMITTING. NO EXCEPTIONS.**

### Python Tests
- Test with venv Python.
- Update tests with every code change or API edit.
- Prefer integration tests (real behavior) over mocks.
- Use `tests/fixtures/` builders.
- After refactor, run full suite & fix all, even unrelated tests.

### Batch Files & Scripts
- **NEVER commit batch files without executing them first**
- **Test method for .bat files from bash:**
  ```bash
  powershell.exe -Command "Start-Process -FilePath 'cmd.exe' \
    -ArgumentList '/c','D:\Projects\RogueSignalProtocol\path\to\file.bat','args' \
    -Wait -NoNewWindow \
    -RedirectStandardOutput 'D:\Projects\RogueSignalProtocol\stdout.txt' \
    -RedirectStandardError 'D:\Projects\RogueSignalProtocol\stderr.txt'"
  cat stdout.txt stderr.txt
  ```
- Use full Windows paths (D:\...), not relative paths
- Build incrementally: test after adding every 10-20 lines
- If broken, bisect to find exact failing line

**Batch File Syntax:**
- **NO `else if` support!** Batch files don't have `else if` syntax
- Use nested `if` statements: `) else ( if ... )`
- Use `%~dp0` to get batch file's directory for reliable path handling
- Prefer `Python -m PyInstaller` over direct `.exe` calls
- Files from `git show` have LF line endings - run `unix2dos` if needed

### Verification Rules
1. **Never assume** - always verify
2. **Never commit blindly** - test first
3. **Never claim "it works"** without proof
4. **Never make multiple commits** without testing each one
5. If you can't test it, say so - don't pretend

**Running Tests:**
- **Full suite:** `python test_commands.py full` (with coverage & timing)
- **Quick unit tests:** `python test_commands.py quick` (fast feedback)
- **Integration only:** `python test_commands.py integration`
- **Coverage report:** `python test_commands.py coverage` (generates htmlcov/)
- **Changed files:** `python test_commands.py changed` (git-based)
- **Direct pytest:** `.venv/Scripts/python.exe -m pytest` (uses pytest.ini config)

**Pre-commit:** `python test_commands.py full`

---

## 6. Logging & Errors
- **Console:** tech errors → `print()` / `logging.error()`.  
- **Game log:** gameplay messages → `MessageLog.add_message()`.  
- Don’t mix the two.  

**Config:**
- Fail fast on missing files.
- Required: `game_content.json`, `game_rules.json`, `story_content.json`.
- Only `user_settings.json` can default.
- No hardcoded fallback values — all data from JSON.

---

## 7. Gameplay Systems

### Enemy Movement Queue

Enemies maintain a **fixed 3-length movement queue** for player predictability:

**Queue as Gameplay Mechanic:**
- Queue shows player what enemy is committed to doing (3 moves ahead)
- Enables tactical planning: player can predict enemy positions and plan accordingly
- Always shows 3 moves when possible (or fewer if path exhausted)

**Queue Lifecycle:**
1. Enemy executes move (pops from queue)
2. Queue tops up to 3 moves (unified fill logic)
3. Player sees enemy's commitment via rendering

**Queue Invalidation (Only 2 Triggers):**
1. Enemy state changes (UNAWARE ↔ ALERT ↔ HOSTILE)
2. Next move is blocked (wall, enemy, etc.)

When invalidated, queue clears and enemy replans on next turn.

**Implementation:**
- Single method `_ensure_queue_full()` handles all queue filling
- Uses `PathfindingHelper` for consistent pathfinding
- No special cases or duplicate logic

### Other Systems
- Enemies alert others when spotting player.
- **Alert timer = 1 turn only.**
- Use TCOD FOV (`tcod.map.compute_fov`) and pathfinding (`tcod.path`) always.
- For TCOD API details, invoke the `tcod` skill.

---

## 7a. TCOD Specifics

**🚨 CRITICAL: Array indexing vs function parameters! 🚨**

TCOD functions use `(x, y)` but arrays use `[y, x]` - this mismatch causes bugs!

**The Rules:**
- **ALWAYS use CoordinateHelpers** for array access (handles `[y, x]` internally)
- **Use UnifiedRenderer** for dialogue rendering (handles transparency automatically)
- **TCOD functions** (like `console.print()`) use `(x, y)` - safe!
- **Direct array access** (like `console.rgba[...]`) uses `[y, x]` - use helpers!

**Example:**
```python
# ✓ CORRECT - use helpers
from game_coordinate_helpers import CoordinateHelpers
CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=255)

# ✓ CORRECT - use UnifiedRenderer for dialogues
from game_dialogue_system import UnifiedRenderer
UnifiedRenderer.render(console, dialogue)

# ✗ WRONG - direct array access with [x, y]
console.rgba["bg"][x, y, 3] = 255  # BUG! Should be [y, x]!
```

**For complete details:** See `.claude/TCOD_GUIDE.md`

---

## 7b. Graphics Coordinate Systems

**Three coordinate systems - DO NOT MIX:**

1. **Console chars (80x50)** - Text rendering, UI layout
2. **Game viewport (27x21)** - In-game tile positions (viewport-scaled)
3. **SDL pixels (window size)** - Direct sprite rendering

**Menu/Help Screen Sprites:**
```python
# Position: Convert console coords to pixels
pixel_x = int(console_x * (window_width / 80))
pixel_y = int(console_y * (window_height / 50))

# Size: Use TileManager (same scale as in-game)
sprite_width = tile_manager.tile_width
sprite_height = tile_manager.tile_height
```

**Common mistakes:**
- Using tileset size (10x16) for sprite SIZE → tiny sprites
- Using tile dimensions to multiply console coords → wrong positions

**For complete details:** See `.claude/TCOD_GUIDE.md`

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
