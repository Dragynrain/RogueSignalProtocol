# TODO - Verified Codebase Issues

Last scanned: 2026-01-22

---

## JSON Files

### 1. ~~Version Mismatch in Welcome Message~~ FIXED
**File:** `game_rules.json`
**Lines:** 2 vs 915
**Issue:** File header says `"version": "0.9.2 Beta"` but welcome message at line 915 says `"Welcome to Rogue Signal Protocol v0.9.1 Beta!"`.
**Fix:** Updated line 915 to match v0.9.2.

---

## Test Suite

### 2. time.sleep() Usage Causes Flaky Tests
**Occurrences:** 74 across 16 files
**Impact:** Tests are flaky on CI, slow, timing-dependent.
**Note:** MockTime fixture already exists in conftest.py lines 120-167.

**Files affected:**
- `tests/integration/test_gamepad_look_mode.py` (16 occurrences)
- `tests/integration/test_gamepad_chaos_agent.py` (17 occurrences)
- `tests/integration/test_gamepad_menu_polling.py` (8 occurrences)
- `tests/integration/test_gamepad_context_switch.py` (7 occurrences)
- `tests/integration/test_audio_edge_cases.py` (6 occurrences)
- `tests/integration/test_gamepad_dual_input.py` (4 occurrences)
- `tests/integration/test_gamepad_end_to_end.py` (3 occurrences)
- Several other files with 1-2 occurrences

**Fix:** Replace `time.sleep()` with `mock_time.advance()` using existing MockTime fixture.

---

### 3. Runtime pytest.skip() Calls
**Impact:** Non-deterministic test results, false "all passed" when tests skipped.
**Note:** Deterministic fixtures already exist in conftest.py (lines 661-764).

**Common patterns that should use fixtures instead:**

| Skip reason | Occurrences | Existing fixture |
|-------------|-------------|------------------|
| "No enemies spawned" | 8 | `agent_with_guaranteed_enemy` (line 701) |
| "All fragments already discovered" | 8 | Need new fixture |
| "No damage-dealing enemies" | 4 | Need specialized fixture |
| "No blind spots on this map seed" | 1 | Need new fixture |
| "Exploit did not execute" | 4 | Test logic issue |

**Files with most skips:**
- `tests/integration/test_death_victory_fragment_flows.py` - 6 skips
- `tests/integration/test_exploit_queue_clearing.py` - 10 skips
- `tests/integration/test_combat_death_flow.py` - 4 skips
- `tests/integration/test_critical_gameplay_flows.py` - 4 skips

---

### 4. ~~Unicode Logging Test Only Scans Root Directory~~ FIXED
**File:** `tests/test_no_unicode_in_logging.py:32`
**Issue:** Uses `glob("*.py")` which only scans project root, not `src/rsp/**/*.py` where all logging actually happens.
**Fix:** Changed to `src_dir.rglob("*.py")` to scan all source files.

---

## Action Items - Test Infrastructure Expansion

### 5. Expand MockTime Usage to All Timing Tests
**What:** Replace `time.sleep()` with `mock_time.advance()` in all 16 affected files.
**Infrastructure:** MockTime fixture exists at conftest.py:120-167.
**Files to update:**
- [x] `tests/integration/test_gamepad_look_mode.py` - DONE
- [x] `tests/integration/test_gamepad_context_switch.py` - DONE
- [x] `tests/integration/test_gamepad_menu_polling.py` - DONE
- [x] `tests/integration/test_gamepad_dual_input.py` - DONE
- [x] `tests/integration/test_gamepad_end_to_end.py` - DONE
- [x] `tests/integration/test_gamepad_settings_sync.py` - DONE
- [x] `tests/integration/test_menu_auto_repeat_real.py` - DONE
- [SKIP] `tests/integration/test_gamepad_chaos_agent.py` - Intentionally uses real timing for fuzz testing
- [SKIP] `tests/integration/test_audio_edge_cases.py` - Needs real time for pygame audio
- [x] Other files with 1-2 occurrences - covered in above files

### 6. ~~Create Missing Deterministic Fixtures~~ DONE
**What:** Add new fixtures to conftest.py for patterns that currently use runtime skip.
**Fixtures created in conftest.py:**
- [x] `agent_with_guaranteed_enemy` - returns (agent, enemy) with adjacent enemy
- [x] `agent_with_executable_exploit` - returns (agent, enemy) with exploit ready to execute
- [x] `agent_with_blind_spot` - returns agent with player in blind spot
- [x] `agent_with_undiscovered_fragments` - returns agent with no discovered fragments

### 7. ~~Update Tests to Use Deterministic Fixtures~~ DONE
**What:** Replace runtime `pytest.skip()` with appropriate fixtures.
**Files updated:**
- [x] `tests/integration/test_death_victory_fragment_flows.py` - DONE (6 skips removed)
- [x] `tests/integration/test_exploit_queue_clearing.py` - DONE (6 enemy skips removed)
- [x] `tests/integration/test_combat_death_flow.py` - DONE (4 skips removed)
- [x] `tests/integration/test_critical_gameplay_flows.py` - DONE (4 skips removed)
- [x] `tests/agents/test_ascension_agent.py` - DONE (1 skip removed)

---

## Source Code

### 8. ~~Missing dest_rect in Graphics Preview Rendering~~ FIXED
**File:** `src/rsp/core/loop.py:320`
**Issue:** Line 225 uses `context.sdl_renderer.copy(console_texture, dest=dest_rect)` to scale console to window size, but line 320 uses `context.sdl_renderer.copy(console_texture)` without dest_rect.
**Impact:** Graphics preview menu may render console at wrong size if window isn't default dimensions.
**Fix:** Added dest_rect calculation matching line 223-225.

---

## Code Quality (Low Priority)

### 9. Broad Exception Catching
**Impact:** Can hide unexpected errors, harder debugging.
**Occurrences:** 28 files catch bare `Exception`.
**Recommendation:** Catch specific exceptions where possible (IOError, ValueError, etc.).

### 10. Magic Numbers Without Constants
**Examples:**
- `src/rsp/level/placement.py:477` - Hardcoded `15` for central distance
- `src/rsp/systems/audio.py:54` - Hardcoded `0.05` for sound cooldown
**Recommendation:** Extract to named constants in GameConfig.

---

## False Positives from Agent Scan (Verified Correct)

The following reported "issues" were verified as intentional or correct:

1. **Distance functions in placement.py** - Uses `distance_to()` which is correct for level generation per DISTANCE_GUIDE.md
2. **turn_manager.py:917** - Uses `distance_to()` for spawn positioning, which is spatial/visual calculation (correct)
3. **Gamepad error handling (166-171)** - Logs error and cannot recover, which is correct behavior per project rules
4. **inventory.py import at line 230** - Intentional lazy import in rare error path
5. **TCOD coordinate usage** - Properly uses `[y, x]` throughout
6. **context.convert_event()** - Correctly avoided per project rules
7. **get_controllers()** - Only called in menu contexts (correct)

---

## Summary

| Priority | Issue | Effort |
|----------|-------|--------|
| ~~Low~~ | ~~#1 Version mismatch~~ | ~~DONE~~ |
| Medium | #2 time.sleep() in tests | Infrastructure exists |
| Medium | #3 Runtime pytest.skip() | Fixtures exist for some |
| ~~High~~ | ~~#4 Unicode logging test bug~~ | ~~DONE~~ |
| Medium | #5 Expand MockTime usage | 16 files, infrastructure exists |
| Medium | #6 Create missing fixtures | ~4 new fixtures |
| Medium | #7 Update tests to use fixtures | ~25 skip replacements |
| ~~Low~~ | ~~#8 Missing dest_rect in graphics preview~~ | ~~DONE~~ |
| Low | #9 Broad exception catching | Gradual refactor |
| Low | #10 Magic numbers | Gradual refactor |
