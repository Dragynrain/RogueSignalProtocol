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

## 4a. Build Process

**Commands:**
- `build\build.bat alpha` - Debug build with `debug_mode.flag`
- `build\build.bat release` - Production build

**Requirements:**
- 7zip at `C:\Program Files\7-Zip\7z.exe` (PowerShell Compress-Archive doesn't work)
- Uses `Python -m PyInstaller` (more reliable than `.exe` calls)

**Outputs:**
- `dist\RogueSignalProtocol.exe` (37MB) + assets
- `releases\RogueSignalProtocol_[type]_[date].zip` (103MB)

**Details:** See `.claude/BUILD_REFERENCE.md`

---

## 5. Testing & Verification

**ALWAYS TEST BEFORE COMMITTING. NO EXCEPTIONS.**

### Python Tests

| Command | Purpose |
|---------|---------|
| `python test_commands.py full` | Full suite + coverage + timing (pre-commit) |
| `python test_commands.py quick` | Unit tests only (fast feedback) |
| `python test_commands.py integration` | Integration tests only |
| `python test_commands.py coverage` | Generate htmlcov/ report |
| `python test_commands.py changed` | Test changed files only (git-based) |
| `.venv/Scripts/python.exe -m pytest` | Direct pytest (uses pytest.ini) |

**Test Policy:**
- Update tests with every code change or API edit
- Prefer integration tests (real behavior) over mocks
- Use `tests/fixtures/` builders
- After refactor, run full suite & fix all tests

### Batch Files & Scripts

**NEVER commit .bat files without testing them first!**

- See `.claude/WINDOWS_SCRIPTING.md` for batch syntax rules and testing method
- Key gotcha: **NO `else if` support** - use nested ifs: `) else ( if ... )`

---

## 6. Logging & Errors
- **Console:** tech errors → `print()` / `logging.error()`
- **Game log:** gameplay messages → `MessageLog.add_message()`
- Don't mix the two

**Config:**
- Fail fast on missing files
- Required: `game_content.json`, `game_rules.json`, `story_content.json`
- Only `user_settings.json` can default
- No hardcoded fallback values — all data from JSON

---

## 7. Gameplay Systems

### Enemy Movement Queue

**Fixed 3-length queue** for player predictability:
- Shows enemy commitment (3 moves ahead)
- Enables tactical planning
- Invalidated only on: (1) state change, (2) blocked move
- Single method `_ensure_queue_full()` handles all filling
- Uses `PathfindingHelper` for consistency

### Other Systems
- Enemies alert others when spotting player
- **Alert timer = 1 turn only**
- Use TCOD FOV (`tcod.map.compute_fov`) and pathfinding (`tcod.path`) always
- For TCOD API details, invoke the `tcod` skill

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
- Always check latest official docs
- Confirm API details before assuming limits and interfaces
- **TCOD-specific questions**: Use the `tcod` skill (`.claude/skills/tcod.md`)

---

## 9. UI / UX
- Help text must exactly match in-game symbols and be kept up-to-date at all times

---

## 10. Git & Attribution
- No `Co-Authored-By` or AI/Claude tags
- Keep commit messages clean and technical

**CRITICAL: .gitignore editing rules**
- **NEVER add inline comments** with trailing spaces (e.g., `dist/  # comment`)
- Trailing spaces break patterns silently - git interprets `"dist/     "` literally
- Always verify changes: `git check-ignore -v <path>` and `git add --dry-run .`
- Keep comments on separate lines above patterns
- When editing `.gitignore`, always test that patterns work before committing
