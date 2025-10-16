# Claude Code Quick Guidelines

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
- Use TCOD vision and TCOD A* pathfinding always.

---

## 8. Docs & Research
- Always check latest official docs.  
- Confirm API details before assuming limits and interfaces.

---

## 9. UI / UX
- Help text must exactly match in-game symbols and be kept up-to-date at all times.

---

## 10. Git & Attribution
- No `Co-Authored-By` or AI/Claude tags.  
- Keep commit messages clean and technical.
