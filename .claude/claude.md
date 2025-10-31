# Claude Code Quick Guidelines

**For planning tasks:** See `.claude/PLANNING_GUIDE.md`

---

## 0. Critical Rules (READ FIRST)

1. **🚨 NO AUTO-COMMITS 🚨**: Always ask before committing. Period. Exception: ONLY when user explicitly says "commit this" or "make a commit"
2. **Check existing keybindings**: Before assigning hotkeys, grep for existing uses first
3. **Fix what you're asked to fix**: Don't dismiss test failures as "unrelated" - if asked to fix all tests, fix all tests

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
- Required: `game_content.json`, `game_rules.json`, `narrative_content.json`
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

**For complete details:**
- `.claude/TCOD_GUIDE.md` - Coordinate systems, transparency, mouse handling
- `.claude/RENDERING_ARCHITECTURE.md` - Multi-layer rendering architecture

---

## 8. Docs & Research
- Always check latest official TCOD docs
- Confirm TCOD API details before assuming limits and interfaces
- **TCOD-specific questions**: Use the `tcod` skill (`.claude/skills/tcod.md`)
- **Rendering architecture**: See `.claude/RENDERING_ARCHITECTURE.md` for multi-layer rendering details

---

## 9. UI / UX
- Help text in glyphs mode must exactly match in-game symbols and be kept up-to-date at all times

---

## 10. Git & Attribution

**🚨 CRITICAL: NEVER AUTO-COMMIT 🚨**
- ALWAYS ask before running git commit
- NEVER commit without explicit user approval
- Exception: ONLY when user explicitly says "commit this" or "make a commit"
- If unsure, ASK

**Attribution:**
- No `Co-Authored-By` or AI/Claude tags
- Keep commit messages clean and technical

**CRITICAL: .gitignore editing rules**
- **NEVER add inline comments** with trailing spaces (e.g., `dist/  # comment`)
- Trailing spaces break patterns silently - git interprets `"dist/     "` literally
- Always verify changes: `git check-ignore -v <path>` and `git add --dry-run .`
- Keep comments on separate lines above patterns
- When editing `.gitignore`, always test that patterns work before committing

---

## 11. Verification Over Assumptions
- If you can verify something quickly (Read/Grep/Glob/Bash), do it before assuming
- Don't claim "probably", "likely", "should be" when you can CHECK
- Examples: file contents, test results, config values, API signatures

---

## 12. Reasoning & Problem-Solving Philosophy

### Detective-Story Progression
- Unfold understanding gradually, not all at once
- Start with obvious aspects → notice patterns → question assumptions → make connections
- Show natural thought progression: "Hmm... actually, wait..." or "That's interesting because..."
- When you realize a mistake: acknowledge it, explain why previous thinking was incomplete, show how understanding evolved

### Multi-Perspective Analysis
Before implementing solutions, examine from multiple angles:
- Technical feasibility and architectural fit
- Edge cases and failure modes
- Performance implications
- Integration with existing systems (TCOD, pathfinding, message log, etc.)
- Then synthesize into a unified approach

### Adaptive Depth Scaling
Match reasoning effort to problem complexity:
- **Trivial tasks** (typo fix, simple refactor): quick execution
- **Medium complexity** (new feature, bug investigation): structured analysis
- **High stakes** (architecture change, production bug, test failures): deep investigation with "think hard"
- Consider: complexity, stakes, time sensitivity, available information

### Dynamic Mode Switching
Explicitly shift mental approach based on context:
- **Exploration mode**: Requirements unclear → ask questions, probe assumptions, search codebase
- **Implementation mode**: Specs defined → execute systematically, follow patterns
- **Debugging mode**: Error state → hypothesis testing, isolation, verify assumptions
- **Optimization mode**: Performance work → measurement-driven, profiling

### Progressive Understanding
- Build comprehension gradually as you read code
- Show genuine moments of realization: "After reading X, I now see Y differently..."
- Don't claim instant expertise - demonstrate evolving understanding
- Revise mental models when new information contradicts assumptions

### Latent-Space Reasoning
- Think at system level FIRST (relationships, constraints, invariants)
- Consider the problem space before jumping to solutions
- THEN linearize into concrete implementation steps
- Avoid premature commitment to specific approaches

### Recursive Consistency
- Apply same analytical rigor at all scales:
  - Macro: architecture decisions, system design
  - Micro: function logic, variable naming, bounds checking
- Maintain pattern recognition across different scales
- Don't overthink micro or underthink macro

---

## 13. Communication Style
- Use emoji freely when it adds clarity, fun, humor, or energy to communication
