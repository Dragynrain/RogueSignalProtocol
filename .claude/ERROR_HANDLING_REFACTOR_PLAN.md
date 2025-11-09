# Error Handling Standardization - Refactor Plan

**Created:** 2025-11-08
**Status:** PENDING APPROVAL
**Estimated Effort:** 4-6 hours (across multiple sessions)

---

## Executive Summary

**Problem:** Out of ~200 exception handlers in the codebase:
- Only 15% use the centralized `GameErrorHandler` system
- 25% should use `handle_error()` but use raw logging
- 5% fail silently and hide bugs
- 1.5% use bare `except:` (dangerous)

**Goal:** Standardize all exception handling to use `GameErrorHandler` for consistency, debuggability, and maintainability.

**Risk Level:** MEDIUM-HIGH (touching error handling across 67 files)

**Mitigation:** Phased approach with testing after each phase

---

## Current State Analysis

### What We Have Right Now

**GameErrorHandler (game_errors.py) provides:**
```python
# 1. Standard error handling with consistent logging
GameErrorHandler.handle_error(e, context, user_message, fatal=False)

# 2. Safe operations with fallback values
GameErrorHandler.handle_safe_operation(operation_func, context, fallback_value, user_message)

# 3. Config-specific error handling
GameErrorHandler.handle_config_error(operation, exception)

# 4. Data loading error handling
GameErrorHandler.handle_data_error(data_type, exception)

# 5. Warning handler
GameErrorHandler.handle_warning(message, context)
```

**Current Usage:**
- ✅ `data_loading.py` - Uses correctly throughout
- ✅ `game_data.py` (partial) - Good error messages, but manual logging
- ✅ `game_config.py` (partial) - Good structure but could use helpers
- ❌ Everything else - Raw logging or silent failures

### What's Wrong

**Example of inconsistency:**
```python
# File A (good - uses GameErrorHandler):
try:
    data = load_json(file)
except FileNotFoundError as e:
    GameErrorHandler.handle_config_error("Failed to load config", e)

# File B (bad - raw logging):
try:
    data = load_json(file)
except FileNotFoundError as e:
    logging.error(f"Failed to load: {e}")
    return None

# File C (worse - silent failure):
try:
    data = load_json(file)
except:
    return None  # BUG HIDER!
```

---

## Refactor Phases

### Phase 1: Critical Bugs (HIGH PRIORITY - Do First)
**Goal:** Fix silent failures that actively hide bugs
**Risk:** LOW (making things fail visibly is safer than hiding failures)
**Testing:** Run specific tests for affected modules

**Changes:**
1. **Bare except statements** (3 files):
   - `game_rendering_base.py:131, 181` - Change to `except AttributeError`
   - `game_rendering_glyphs.py:583` - Change to `except Exception`
   - `game_ui.py:70` - Change to `except Exception`

2. **Silent failures** (5 files, 10+ locations):
   - `game_menus.py:496, 831, 871, 967, 1008` - Add debug logging to mouse handlers
   - `game_characters.py:315` - Add debug logging for player blocking
   - `game_menu_help_graphics.py:424` - Add debug logging
   - `game_menu_utilities.py:139` - Add debug logging
   - `game_entities.py:679, 687` - Add explanatory comments + debug logging

**Test command after Phase 1:**
```bash
pytest tests/unit/test_input_validation.py tests/integration/test_enemy_pathfinding_fixes.py -v
pytest tests/ -k "rendering" --tb=short
```

---

### Phase 2: Audio & Graphics (MEDIUM PRIORITY)
**Goal:** Standardize exception handling in non-critical subsystems
**Risk:** LOW-MEDIUM (audio/graphics failures should degrade gracefully)
**Testing:** Audio and graphics tests

**Changes:**
1. **game_audio.py** (4 handlers):
   - Line 106: Sound init → `GameErrorHandler.handle_error(e, "sound_init", "Sound initialization failed")`
   - Line 228: Sound load → `GameErrorHandler.handle_error(e, "sound_load", f"Failed to load {sound_id}")`
   - Line 318: Music play → `GameErrorHandler.handle_error(e, "music_play", f"Failed to play {filename}")`
   - Line 336: Music stop → `GameErrorHandler.handle_error(e, "music_stop", "Failed to stop music")`

2. **font_loader_freetype.py** (1 handler):
   - Line 125: Font render → `GameErrorHandler.handle_error(e, "font_render", "Font rendering failed")`

3. **game_graphics_tiles.py** (4 handlers):
   - Line 111: Tile mapping → `GameErrorHandler.handle_error(e, "tile_mapping_load", ...)`
   - Line 147: Tile dimensions → `GameErrorHandler.handle_error(e, "tile_dimensions", ...)`
   - Line 230: Sprite load → `GameErrorHandler.handle_error(e, "sprite_load", ...)`
   - Line 453: Color extract → `GameErrorHandler.handle_error(e, "color_extract", ...)`

**Test command after Phase 2:**
```bash
pytest tests/unit/test_audio_system.py -v
pytest tests/ -k "graphics or sprite or tile" --tb=short
```

---

### Phase 3: Core Game Logic (HIGH PRIORITY)
**Goal:** Standardize exception handling in critical game systems
**Risk:** MEDIUM (pathfinding, combat are critical)
**Testing:** Extensive integration testing

**Changes:**
1. **game_characters.py** (4 handlers):
   - Line 100: Pathfinding → `GameErrorHandler.handle_error(e, "pathfinding", "Pathfinding failed", fatal=False)`
   - Line 263: Path exists → `GameErrorHandler.handle_safe_operation(lambda: check_path(), "path_check", False)`
   - Line 298: Simple path → `GameErrorHandler.handle_safe_operation(...)`
   - Line 1203: Enemy serialize → `GameErrorHandler.handle_error(e, "enemy_serialize", ...)`

2. **game_combat.py** (1 handler):
   - Line 396: Combat calc → `GameErrorHandler.handle_error(e, "combat_calc", ...)`

3. **game_engine.py** (1 handler):
   - Line 493: Achievement check → `GameErrorHandler.handle_safe_operation(...)`

4. **game_dialogue_system.py** (1 handler):
   - Line 259: Format error → `GameErrorHandler.handle_config_error("dialogue_format", e)`

**Test command after Phase 3:**
```bash
pytest tests/integration/test_enemy_pathfinding_fixes.py -v
pytest tests/integration/test_combat_mechanics.py -v
pytest tests/ -k "achievement" --tb=short
```

---

### Phase 4: Rendering & UI (MEDIUM PRIORITY)
**Goal:** Standardize rendering error handlers
**Risk:** MEDIUM (rendering bugs can crash game)
**Testing:** Rendering smoke tests

**Changes:**
1. **game_rendering_glyphs.py** (5+ handlers)
2. **game_input.py** (2 handlers)
3. **game_info_panel.py** (1 handler)
4. **game_menus.py** (UI handlers beyond mouse)

**Test command after Phase 4:**
```bash
pytest tests/integration/test_new_game_smoke.py -v
pytest tests/ -k "rendering or menu" --tb=short
```

---

### Phase 5: Metrics & Debug (LOW PRIORITY)
**Goal:** Ensure metrics never crash the game
**Risk:** LOW (metrics are non-critical)
**Testing:** Basic smoke test

**Changes:**
1. **game_metrics.py** (15+ handlers):
   - All exceptions → `GameErrorHandler.handle_safe_operation(lambda: track_metric(), "metric_track", None)`
   - Rationale: Metrics tracking should NEVER crash game, always degrade gracefully

2. **debug_export.py** (6 handlers):
   - Wrap in handle_safe_operation where appropriate

**Test command after Phase 5:**
```bash
pytest tests/ -k "metrics" --tb=short
```

---

### Phase 6: Data Loading (CLEANUP)
**Goal:** Migrate game_data.py to use handle_data_error()
**Risk:** LOW (already has good error handling, just standardizing)
**Testing:** Config and data loading tests

**Changes:**
1. **game_data.py** (4 handlers):
   - Lines 131-133: `GameErrorHandler.handle_data_error("enemy_data", e)`
   - Lines 148-150: `GameErrorHandler.handle_data_error("exploit_data", e)`
   - Lines 165-167: `GameErrorHandler.handle_data_error("upgrade_data", e)`
   - Lines 182-185: `GameErrorHandler.handle_data_error("lore_data", e)`

**Test command after Phase 6:**
```bash
pytest tests/unit/test_config_loading.py -v
pytest tests/integration/test_new_game_smoke.py -v
```

---

### Phase 7: Final Validation (REQUIRED)
**Goal:** Ensure nothing broke
**Risk:** N/A
**Testing:** Full test suite

**Test command:**
```bash
# Quick check first
pytest tests/ -q --tb=no 2>&1 | tail -20

# Full validation
pytest tests/ -v --tb=short
```

---

## Implementation Guidelines

### Before Starting Each Phase
1. ✅ Read the phase description
2. ✅ Understand which files will be changed
3. ✅ Check if phase-specific tests exist
4. ✅ Run baseline tests to confirm current state

### During Implementation
1. ✅ Change ONE file at a time
2. ✅ Add proper imports: `from game_errors import GameErrorHandler`
3. ✅ Preserve existing behavior (same return values, same user-facing errors)
4. ✅ Run file-specific tests after each file change
5. ✅ Commit after each successfully tested file (optional but recommended)

### After Completing Each Phase
1. ✅ Run phase-specific tests
2. ✅ Run quick smoke test: `pytest tests/ -q --tb=no 2>&1 | tail -20`
3. ✅ Document any issues encountered
4. ✅ Get approval before proceeding to next phase

---

## Safety Checklist

**Before changing exception handler:**
- [ ] Do I understand what this exception handler is protecting against?
- [ ] Do I know what the expected failure modes are?
- [ ] Will my change preserve the same behavior?
- [ ] Is there a test that covers this code path?

**Red flags (STOP and ask):**
- Exception handler in critical game loop (game_loop.py main loop)
- Exception handler around pygame initialization
- Exception handler in save/load code
- Unclear what exception is being caught

---

## Rollback Plan

If a phase breaks tests:
1. Identify which file caused the breakage
2. Revert that specific file: `git checkout HEAD -- <file>`
3. Document the issue
4. Skip that file for now, continue with phase
5. Return to problematic file later with more analysis

---

## Success Criteria

**Phase completion:**
- [ ] All changes implemented per phase plan
- [ ] Phase-specific tests pass
- [ ] Quick smoke test passes
- [ ] No new warnings or errors in logs

**Overall completion:**
- [ ] All 7 phases completed
- [ ] Full test suite passes (1637+ tests)
- [ ] No regressions in gameplay
- [ ] Error messages are clearer and more consistent
- [ ] Documentation updated (this plan marked as COMPLETED)

---

## Timeline Estimate

**Per phase (conservative):**
- Phase 1 (Critical): 30-45 min
- Phase 2 (Audio/Graphics): 45-60 min
- Phase 3 (Core Logic): 60-90 min
- Phase 4 (Rendering): 60-90 min
- Phase 5 (Metrics): 30-45 min
- Phase 6 (Data Loading): 15-30 min
- Phase 7 (Validation): 15-30 min

**Total:** 4-6 hours across 2-3 sessions

**Recommended schedule:**
- Session 1: Phases 1-2 (Critical + Audio/Graphics)
- Session 2: Phases 3-4 (Core Logic + Rendering)
- Session 3: Phases 5-7 (Metrics + Data + Validation)

---

## Questions for User (Before Starting)

1. **Should we proceed with Phase 1 now?** (Critical bugs - safest to start)
2. **Test tolerance:** What's acceptable pass rate during refactor? (Suggest: 99%+)
3. **Commit strategy:** After each file, after each phase, or at end?
4. **Any files that are off-limits?** (e.g., don't touch game_loop.py main loop)

---

## Notes for Future

After completion, update:
- [ ] `.claude/CLAUDE.md` - Add error handling policy
- [ ] Add pre-commit hook to catch bare `except:` statements
- [ ] Add linter rule for consistent exception handling
- [ ] Create ERROR_HANDLING_GUIDE.md with examples
