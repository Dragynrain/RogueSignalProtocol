# Rogue Signal Protocol - Project Rules

**Keep both CLAUDE.md files < 100 lines**

## 0. Critical Rules

**Encoding:** TCOD = Unicode OK (↕↑↓←→), Logging = ASCII only (Windows breaks on Unicode, use `[DEATH]` not 💀)
**Before coding:** Grep keybindings `grep -r "key == ord\('[a-z]'\)"`, verify URLs `grep -r "discord.gg\|itch.io"` (you hallucinate!)

**Check docs BEFORE implementing:** Mouse → `MOUSE_COORDINATE_HANDLING.md`, Gamepad → `gamepad.md`, TCOD → `TCOD_GUIDE.md`, Distance → `DISTANCE_GUIDE.md`, Rendering → `RENDERING_ARCHITECTURE.md`, Testing → `TESTING_GUIDE.md`, Batch → `WINDOWS_SCRIPTING.md` (all in `.claude/`)

## 1. Platform & Core Rules

**Target:** Windows 10/11, KreativeSquare TrueType font (64×64), Unicode console + TCOD graphics (sync both modes)
**Enemies:** A-Z ONLY (test-enforced), everything else ASCII symbols
**Death:** Delete save, no prompt (core mechanic)
**Deps:** Use latest (esp. `python-tcod`), keep `build/` + `dist/` folders
**Config:** Fail-fast on missing `game_content.json`, `game_rules.json`, `narrative_content.json`. ONLY `user_settings.json` defaults. No hardcoded fallbacks.

## 2. Build & Test

**Build:** `build\build.bat [alpha|release]` (needs 7zip at `C:\Program Files\7-Zip\7z.exe`)
- Outputs: `dist\RogueSignalProtocol.exe` (37MB), `releases\..._[type]_[date].zip` (103MB)
**Test:** Pre-commit hook auto-runs. Quick: `pytest tests/unit/test_<module>.py -v`, Iterate: `pytest --lf --tb=short`
See `.claude/TESTING_GUIDE.md`

## 3. Two Logging Systems - DO NOT MIX

`logging.debug("text")` = console/file (ASCII only) | `MessageLog.add_message("text", c)` = game UI (Unicode OK, TCOD-rendered)

## 4. Distance

**Gameplay** (exploits/adjacency/AoE): `pos.grid_distance_to(other)` (Chebyshev, diag=1)
**Vision/spatial** (FOV/level gen): `pos.distance_to(other)` (Euclidean, TCOD-compatible)
See `.claude/DISTANCE_GUIDE.md`

## 5. TCOD Gotchas

**Arrays:** `console.rgba["bg"][y, x]` but `console.print(x, y)` - always use `CoordinateHelpers`
**Pathfinding:** Uses `(y, x)` NOT `(x, y)`. `pathfinder.add_root((player_y, player_x))`. Returns `[(y,x),...]` with START at `path[0]` - skip it!
See `.claude/TCOD_GUIDE.md`

## 6. Mouse

**NEVER `context.convert_event()`** (SDL rendering incompatible)
- Menu/UI: `MenuMouseHandler.convert_to_tile_coords(event, context)` → `event.tile`
- World: `input_handler._mouse_pixel_to_world(px, py)` → `Position|None`
See `.claude/MOUSE_COORDINATE_HANDLING.md`

## 7. Gamepad

**NEVER `get_controllers()` during gameplay** (returns empty!)
- Menu: `get_controllers()` OK
- In-game: `input_handler.gamepad_handler.controllers` (pre-stored)
- Actions: `if action == InputAction.NAV_UP` (NOT `.action_type`)
See `.claude/gamepad.md`

## 8. Rendering

**Layers:** Backgrounds (SDL) → Sprites (SDL) → Console (transparent). Can't use `context.present()` (clears sprites).
**Coords:** Console (80x50), Viewport (27x21), SDL pixels - don't mix!
**Transparency:** `UnifiedRenderer.render()` or `CoordinateHelpers.set_alpha_region()`
See `.claude/RENDERING_ARCHITECTURE.md`

## 9. Enemy AI

Movement queue: 3-length, shows commitment, invalidated on state change/blocked move
Alerts: 1 turn only, chain to others when spotting player

## 10. UI/UX

**Help text in glyphs mode must exactly match in-game symbols and be kept up-to-date at all times**

## 11. Batch Files

NO `else if` - use `) else ( if ... )`. Test before commit. See `.claude/WINDOWS_SCRIPTING.md`

## 12. Top 10 Mistakes

1. Unicode in logging → Windows crash
2. `distance_to()` for gameplay → diag break
3. `get_controllers()` in-game → empty
4. `context.convert_event()` → incompatible
5. Direct arrays → `[y,x]` vs `(x,y)` confusion
6. `path[0]` → starting position!
7. `(x,y)` pathfinding → TCOD uses `(y,x)`
8. Untested .bat → syntax fail
9. URLs from memory → hallucinate
10. Skip keybinding check → conflicts
