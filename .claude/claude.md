# Claude Code Quick Guidelines

**BEFORE PLANNING:** READ `.claude/PLANNING_GUIDE.md` FIRST (you are bad at time estimates - never guess!)

---

## 0. Critical Rules (READ FIRST)

1. **VERIFY BEFORE ASSUMING** - Your most common mistake!
   - Use Read/Grep/Glob/Bash to CHECK instead of guessing
   - Examples: file contents, URLs, config values, API signatures
   - **URLs/Links:** ALWAYS grep for existing URLs before writing any link
     ```bash
     grep -r "discord.gg\|itch.io\|github.com" --include="*.md" --include="*.txt"
     ```
   - Never construct URLs from assumptions (you hallucinated "adam-godel" when it's "Dragynrain")

2. **NO AUTO-COMMITS**: Always ask before committing. Exception: ONLY when user says "commit this" or "make a commit"
3. **Check existing keybindings**: Before assigning hotkeys, grep for existing uses first
4. **Fix what you're asked to fix**: Don't dismiss test failures as "unrelated" - if asked to fix all tests, fix all tests
5. **Character encoding rules** - CRITICAL FOR WINDOWS:
   - **Game UI (TCOD)**: Unicode OK (↕ ↑ ↓ ← → ↗ ↖ ↙ ↘) - KreativeSquare font supports
   - **Logging/console**: **ASCII ONLY** - Windows logging handlers SILENTLY FAIL on Unicode!
     - ❌ NEVER: `logging.info("✓ Success")` - causes silent exception, no log output
     - ✅ ALWAYS: `logging.info("[SUCCESS]")` or `logging.info("OK")`
     - Examples: Use `[MATCH]`/`[MISMATCH]`, `[DEATH]`, `->` not ✓/✗, 💀, →
     - **Why**: Windows CP1252 encoding in log files silently drops Unicode, breaking logging
   - **Chat with user**: Emoji OK 😊
   - **Code/commits**: Never use emoji

---

## 1. Bash & Environment (CRITICAL - READ FIRST)

**YOU ARE IN GIT BASH ON WINDOWS** - This means Unix commands only:

- ✅ **USE THESE**: `ls`, `rm`, `mkdir`, `cp`, `mv`, `cat`, `grep`, `find`
- ❌ **NEVER USE**: `dir`, `del`, `md`, `copy`, `move`, `type` (Windows CMD commands)
- **Paths**: Forward slashes preferred but backslashes work: `.venv/Scripts/python.exe`
- **Quote spaces**: Always quote paths with spaces: `cd "path with spaces"`
- **Python**: Always use `.venv/Scripts/python.exe` (not just `python`)
- **Pip**: Always use `.venv/Scripts/pip.exe install <pkg>`

---

## 2. Compatibility
- **Font:** KreativeSquare TrueType (64×64 native, scalable via FreeType)
- Target: Windows 10/11 (cmd/PowerShell)
- Rendering: Unicode console + TCOD graphics (sync both)

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
- **Distance calculations:** READ `.claude/DISTANCE_GUIDE.md` BEFORE implementing - use `grid_distance_to()` for gameplay (exploits, adjacency, AoE), `distance_to()` for vision/spatial calculations

---

## 4a. Build Process

**Commands:**
- `build\build.bat alpha` - Debug build with `debug_mode.flag`
- `build\build.bat release` - Production build

**Requirements:**
- 7zip at `C:\Program Files\7-Zip\7z.exe` (PowerShell Compress-Archive doesn't work)
- Uses `Python -m PyInstaller` (more reliable than `.exe` calls)

**Modifying build process:** READ `.claude/BUILD_REFERENCE.md` FIRST

---

## 5. Testing & Verification

**Pre-commit hook:** Tests run AUTOMATICALLY before every commit via `.git/hooks/pre-commit`
- Runs full test suite (`.venv/Scripts/python.exe -m pytest tests/`)
- Blocks commit if tests fail
- Bypass only in emergencies: `git commit --no-verify`

**Manual test commands:**
- `pytest tests/ --lf` - Re-run last failures (iterating on fixes)
- `pytest tests/unit/test_<module>.py -v` - Single module test
- `pytest tests/ -q --tb=no | tail -20` - Quick sanity check
- Direct pytest: `.venv/Scripts/python.exe -m pytest`

**Policy:** Update tests with code changes. Prefer integration over mocks. READ `.claude/TESTING_GUIDE.md` BEFORE writing tests.

**Batch files:** MUST test before committing. READ `.claude/WINDOWS_SCRIPTING.md` for syntax. No `else if` - use `) else ( if ... )`

**Test Agent Framework:** READ `.claude/AGENT_DEVELOPMENT.md` BEFORE creating new agents
- Development guide: `.claude/AGENT_DEVELOPMENT.md` - Step-by-step agent creation, common mistakes
- Testing strategy: `.claude/TESTING_STRATEGY.md` and `.claude/TESTING_AUTOMATION.md`
- Base class: `GameTestAgent` (tests/test_agent.py) - Headless game simulation
- Examples: Chaos testing (tests/integration/test_chaos_agent.py), Speed/slow agents (tests/test_speed_slow_agent.py)

---

## 6. Logging & Errors

**Logging rules:**
- **Console/file logs:** `logging.debug/info/error()` - tech/debug info (see rule #0.5 for encoding)
- **Game message log:** `MessageLog.add_message()` - gameplay events, Unicode OK (rendered by TCOD)
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
- **TCOD API questions:** INVOKE the `tcod` skill BEFORE making assumptions

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

**Full reference:** READ `.claude/TCOD_GUIDE.md` for complete details

---

## 7b. Graphics Coordinate Systems

**Three systems - DON'T MIX:**
1. Console chars (80x50) - Text/UI
2. Game viewport (27x21) - In-game tiles
3. SDL pixels - Sprite rendering

**Sprites:** Position = `console_x * (window_width / 80)`. Size = `tile_manager.tile_width/height`

**Full reference:** READ `.claude/TCOD_GUIDE.md` and `.claude/RENDERING_ARCHITECTURE.md` BEFORE implementing rendering

---

## 7c. Mouse Event Handling

**CRITICAL: READ `.claude/TCOD_GUIDE.md` Mouse section (lines 48-84) BEFORE adding mouse support!**

- Menu/UI: Use `MenuMouseHandler.convert_to_tile_coords()` (game_mouse_utils.py)
- In-game world: Use `InputHandler._mouse_pixel_to_world()` (game_input.py)
- **Never use `context.convert_event()`** - doesn't work with our SDL rendering
- **Full reference:** READ `.claude/MOUSE_COORDINATE_HANDLING.md` for complete implementation details

---

## 8. Docs & Research
- **ALWAYS** check official TCOD docs BEFORE assuming API behavior (you make wrong assumptions!)
- **TCOD questions:** INVOKE the `tcod` skill FIRST
- **Rendering work:** READ `.claude/RENDERING_ARCHITECTURE.md` BEFORE implementing

---

## 9. UI / UX
- Help text in glyphs mode must exactly match in-game symbols and be kept up-to-date at all times

---

## 10. Git & Attribution

**Shorthand:** "kitchen sink" means to commit and sync, with a brief summary of changes

**Commits:** See rule #0 - ask first!

**Attribution:** FORBIDDEN - Never add any of:
- `Co-Authored-By: Claude` tags
- `🤖 Generated with [Claude Code]` links
- Any AI attribution or emoji signatures
- Clean technical messages ONLY

**.gitignore:** NEVER use inline comments with trailing spaces (`dist/  # comment` breaks). ALWAYS test patterns before committing.

---

## 11. Reasoning & Problem-Solving

**Approach:**
- Unfold understanding gradually - show natural thought progression
- Acknowledge mistakes, explain how understanding evolved
- Examine multiple angles before implementing (feasibility, edge cases, performance, integration)
- Switch modes based on context (exploration → implementation → debugging → optimization)
- Match depth to complexity (trivial → quick, high stakes → deep)
- Think system-level first, then implement
- Apply same rigor at all scales (architecture to variable names)

---

## 12. Communication Style
- Follow rule #0.5 for character encoding (Unicode in game UI, ASCII in logs, emoji OK in chat)
