# Claude Code Quick Guidelines

**For planning tasks:** See `.claude/PLANNING_GUIDE.md`

---

## 0. Critical Rules (READ FIRST)

1. **NO AUTO-COMMITS**: Always ask before committing. Exception: ONLY when user says "commit this" or "make a commit"
2. **Check existing keybindings**: Before assigning hotkeys, grep for existing uses first
3. **Fix what you're asked to fix**: Don't dismiss test failures as "unrelated" - if asked to fix all tests, fix all tests
4. **Unicode character rules**:
   - **Game UI (TCOD)**: Unicode arrows/symbols OK (↕ ↑ ↓ ← →) - CascadiaCode font supports them
   - **Logging/console**: ASCII only - Windows CP1252 breaks on Unicode. Use `[DEATH]`, `[OK]`, `->` not 💀, ✅
   - **Emoji**: Never use anywhere (chat messages to user are OK)

---

## 1. Bash & Environment
- Quote paths: `cd "path with spaces"`.
- Use bash cmds (`rm`, `ls`, `mkdir`), not Windows ones.
- Run via `.venv/Scripts/python.exe`; install with `.venv/Scripts/pip.exe install <pkg>`.

---

## 2. Compatibility
- **Font:** CascadiaCode TrueType (32×32, scalable to any resolution)
- **Character set:** Unicode (full box-drawing, symbols, card suits)
- Target: Windows 10/11 (cmd/PowerShell).
- Rendering: Unicode console + TCOD graphics (sync both).

---

## 3. Project Rules
- A–Z = enemies only; everything else ASCII symbols.
- Use latest deps (esp. `python-tcod`).
- Delete save on death (no prompt).

---

## 4. Code & Architecture
- Prefer simple functional code.
- Keep files under ~20,000 tokens; consider refactoring when approaching this limit.
- One purpose per module.
- No over-engineering or new frameworks.
- Keep `build/` + `dist/` folders for releases.
- **Always check bounds before array access** - verify indices are valid before indexing any array.
- **Distance calculations:** See `.claude/DISTANCE_GUIDE.md` - use `grid_distance_to()` for gameplay (exploits, adjacency, AoE), `distance_to()` for vision/spatial calculations

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

| Command | Purpose |
|---------|---------|
| `python test_commands.py full` | Full suite + coverage (pre-commit) |
| `python test_commands.py quick` | Unit tests only |
| `.venv/Scripts/python.exe -m pytest` | Direct pytest |

**Policy:** Update tests with code changes. Prefer integration over mocks. Run full suite after refactor.

**Batch files:** Test before committing. See `.claude/WINDOWS_SCRIPTING.md`. No `else if` - use `) else ( if ... )`

---

## 6. Logging & Errors

**Logging rules:**
- **Console/file logs:** `logging.debug/info/error()` - tech/debug info, ASCII only (Windows CP1252 limitation)
- **Game message log:** `MessageLog.add_message()` - gameplay events, Unicode OK (rendered by TCOD)
- **Game UI (TCOD-rendered):** Unicode arrows/symbols OK (↕ ↑ ↓ ← →) - CascadiaCode supports them
- **Logging output:** ASCII only (→ = `->`, 💀 = `[DEATH]`). Windows console breaks on Unicode.
- Don't mix console and game logs

**Config:**
- Fail fast on missing: `game_content.json`, `game_rules.json`, `narrative_content.json`
- Only `user_settings.json` can default
- No hardcoded fallbacks - all data from JSON

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

**CRITICAL: TCOD functions use `(x, y)` but arrays use `[y, x]`!**

Rules:
- Use `CoordinateHelpers` for array access (handles `[y, x]`)
- Use `UnifiedRenderer` for dialogues (handles transparency)
- TCOD functions (`console.print()`) use `(x, y)` - safe
- Direct array access (`console.rgba[...]`) uses `[y, x]` - use helpers!

Example: `CoordinateHelpers.set_alpha_region(console, x=10, y=5, ...)` ✓
Wrong: `console.rgba["bg"][x, y, 3] = 255` ✗

**Details:** `.claude/TCOD_GUIDE.md`

---

## 7b. Graphics Coordinate Systems

**Three systems - DON'T MIX:**
1. Console chars (80x50) - Text/UI
2. Game viewport (27x21) - In-game tiles
3. SDL pixels - Sprite rendering

**Sprites:** Position = `console_x * (window_width / 80)`. Size = `tile_manager.tile_width/height`

**Details:** `.claude/TCOD_GUIDE.md`, `.claude/RENDERING_ARCHITECTURE.md`

---

## 7c. Mouse Event Handling

**CRITICAL: Read `.claude/TCOD_GUIDE.md` section "Mouse Coordinate Conversion" (lines 48-84) BEFORE adding mouse support!**

**Two different coordinate systems:**

1. **Menu/UI screens** (console tiles 0-79, 0-49)
   - Use: `MenuMouseHandler.convert_to_tile_coords(event, context)`
   - File: `game_mouse_utils.py`
   - For: Main menu, settings, graphics preview, help screens

2. **In-game world** (map positions 0-99, 0-99)
   - Use: `InputHandler._mouse_pixel_to_world(pixel_x, pixel_y)`
   - File: `game_input.py`
   - For: Gameplay clicks, targeting, look mode

**Never use `context.convert_event()`** - doesn't work with our multi-layer SDL rendering.

**Read first:** `.claude/TCOD_GUIDE.md` (section: Mouse Coordinate Conversion)
**Then see:** `.claude/MOUSE_COORDINATE_HANDLING.md` (post-mortem & best practices)

---

## 8. Docs & Research
- Check official TCOD docs before assuming API behavior
- TCOD questions: Use `tcod` skill
- Rendering: See `.claude/RENDERING_ARCHITECTURE.md`

---

## 9. UI / UX
- Help text in glyphs mode must exactly match in-game symbols and be kept up-to-date at all times

---

## 10. Git & Attribution

**Commits:** See rule #0 - ask first!

**Attribution:** FORBIDDEN - Never add any of:
- `Co-Authored-By: Claude` tags
- `🤖 Generated with [Claude Code]` links
- Any AI attribution or emoji signatures
- Clean technical messages ONLY

**.gitignore:** No inline comments with trailing spaces (`dist/  # comment` breaks). Test patterns before committing.

---

## 11. Verification Over Assumptions
- If you can verify something quickly (Read/Grep/Glob/Bash), do it before assuming
- Don't claim "probably", "likely", "should be" when you can CHECK
- Examples: file contents, test results, config values, API signatures

---

## 12. Reasoning & Problem-Solving

**Approach:**
- Unfold understanding gradually - show natural thought progression
- Acknowledge mistakes, explain how understanding evolved
- Examine multiple angles before implementing (feasibility, edge cases, performance, integration)
- Switch modes based on context (exploration → implementation → debugging → optimization)
- Match depth to complexity (trivial → quick, high stakes → deep)
- Think system-level first, then implement
- Apply same rigor at all scales (architecture to variable names)

---

## 13. Communication Style
- **In chat with user:** Use emoji freely for clarity, fun, or energy 😊
- **In game UI (TCOD):** Unicode arrows/symbols OK (↕ ↑ ↓ ← →) - CascadiaCode supports them
- **In logging/console output:** ASCII only - Windows CP1252 breaks on Unicode
- **Emoji in code:** Never use (breaks cross-platform) - see rule #0.4
