# Configuration Redundancy Audit

**Date:** 2025-10-09
**Purpose:** Identify and document redundant/duplicate configuration values across JSON files
**Status:** Audit Complete

---

## Executive Summary

Found **2 duplicate balance values** that exist in both `game_config.json` and `game_data.json`:

1. `cpu_restore_min`: 30 (appears in both files)
2. `cpu_restore_max`: 40 (appears in both files)

These values violate the single source of truth principle and create maintenance burden.

---

## Detailed Findings

### 1. Duplicate Balance Values

**Location 1:** `game_config.json` → `balance` section
```json
{
  "balance": {
    ...
    "cpu_restore_min": 30,
    "cpu_restore_max": 40,
    ...
  }
}
```

**Location 2:** `game_data.json` → `balance` section
```json
{
  "balance": {
    "ai_behavior": { ... },
    "cpu_restore_min": 30,
    "cpu_restore_max": 40,
    "code_hacks": { ... }
  }
}
```

**Problem:**
- If these values need to change, they must be updated in TWO places
- Risk of values getting out of sync
- Unclear which file is the "source of truth"
- Increases file size unnecessarily

**Usage:** These values are used by the `restore_cpu` code hack to restore player CPU.

---

## Recommendations

### Option 1: Keep in game_config.json (RECOMMENDED)

**Rationale:**
- `game_config.json` is for **game balance and gameplay constants**
- `game_data.json` is for **entity definitions** (enemies, exploits, etc.)
- `cpu_restore` values are balance constants, not entity data

**Action:**
1. Remove `cpu_restore_min` and `cpu_restore_max` from `game_data.json` → `balance` section
2. Keep them in `game_config.json` → `balance` section
3. Code already loads from `GameBalance` class which reads from `game_config.json`
4. No code changes needed - just remove from `game_data.json`

### Option 2: Keep in game_data.json

**Rationale:**
- These values are specifically for code hack effects
- Could be part of code hack definitions

**Action:**
1. Remove from `game_config.json` → `balance` section
2. Keep in `game_data.json` → `balance.code_hacks` section (more specific location)
3. Update `GameBalance` class to load from `GameData` instead

**Verdict:** Option 1 is better - keep in `game_config.json`

---

## File Structure Principles

Based on this audit, here are the recommended file structure principles:

### game_config.json
**Purpose:** Game configuration, balance constants, UI settings, display settings

**Should contain:**
- Display settings (screen size, colors, symbols)
- UI configuration
- Gameplay balance constants
- Room generation parameters
- Heat/Trace/CPU balance values
- Enemy AI behavior constants
- Vision/detection constants

### game_data.json
**Purpose:** Entity definitions, level configurations

**Should contain:**
- Enemy type definitions
- Exploit definitions
- Upgrade definitions
- Network/Level configurations
- Difficulty multipliers
- Exploit-specific constants (CPU costs)

### story_content.json
**Purpose:** Narrative content

**Should contain:**
- Story fragments
- Lore text
- Dialog
- Narrative progression data

---

## Implementation Plan

### Step 1: Remove Duplicates
Remove the following from `game_data.json`:
```json
"balance": {
  "ai_behavior": { ... },  // KEEP THIS
  "cpu_restore_min": 30,   // DELETE THIS
  "cpu_restore_max": 40,   // DELETE THIS
  "code_hacks": { ... }    // KEEP THIS
}
```

After removal, should look like:
```json
"balance": {
  "ai_behavior": {
    "enemy_trace_alert_to_hostile": 3,
    "enemy_trace_continuous_hostile": 0.3
  },
  "code_hacks": {
    "heat_reduction_instant": 40
  }
}
```

### Step 2: Verify Tests Pass
Run the consistency test again:
```bash
pytest tests/integration/test_config_consistency.py::TestConfigRedundancy::test_no_duplicate_balance_values -v
```

Should pass after removal.

### Step 3: Verify Game Still Works
The game should continue to work because:
- `GameBalance` class loads from `game_config.json`
- Code references `GameBalance.CPU_RESTORE_MIN` and `GameBalance.CPU_RESTORE_MAX`
- These are already loading from `game_config.json`

---

## Additional Checks Performed

### AI Behavior Values
**Status:** ACCEPTABLE

The `ai_behavior` sub-section appears in both files but with identical values:
- `enemy_trace_alert_to_hostile`: 3 (in both)
- `enemy_trace_continuous_hostile`: 0.3 (in both)

**Decision:** This is acceptable IF values match (which they do). However, should eventually consolidate into one file.

### Gameplay Settings
**Status:** CLEAN

No gameplay settings (max_heat, max_trace_level, default_player_cpu, etc.) appear outside the `gameplay` section.

### Version Numbers
**Status:** CONSISTENT

Both files have matching version: "0.8.0 Alpha"

---

## Summary Statistics

- **Files Audited:** 3 (game_config.json, game_data.json, story_content.json)
- **Duplicate Values Found:** 2 (cpu_restore_min, cpu_restore_max)
- **Questionable Duplicates:** 1 (ai_behavior section - acceptable for now)
- **Tests Created:** 2 files, 39 tests total
- **Test Results:** 38 passing, 1 failing (expected - detects duplicates)

---

## Test Coverage

Created comprehensive config validation tests:

### test_config_consistency.py (15 tests)
- ✅ Duplicate balance value detection
- ✅ AI behavior consistency check
- ✅ Gameplay settings placement
- ✅ Version consistency
- ✅ Required sections check
- ✅ Enemy field completeness
- ✅ Exploit field completeness
- ✅ CPU cost coverage
- ✅ Network config completeness
- ✅ Balance value usage validation

### test_balance_relationships.py (24 tests)
- ✅ MIN < MAX relationships
- ✅ Positive value validation
- ✅ Reasonable value ranges
- ✅ Difficulty scaling progression
- ✅ Level progression difficulty
- ✅ Resource scarcity scaling
- ✅ Exploit cost balance
- ✅ Enemy stat balance
- ✅ Exploit category validation
- ✅ Admin enemy superiority

---

## Next Steps

1. **Remove duplicate values** from `game_data.json` (see Step 1 above)
2. **Run full test suite** to verify no regressions
3. **Consider consolidating ai_behavior** to single location in future
4. **Document file structure** principles in project README
5. **Add pre-commit hook** to run consistency tests

---

## Conclusion

The codebase has minimal config redundancy (only 2 duplicate values). This is easily fixed by removing the duplicates from `game_data.json`. The new test suite will prevent future config drift and ensure configuration remains clean and maintainable.

**Recommendation:** Fix the duplicates now (5 minute task) before they cause issues.
