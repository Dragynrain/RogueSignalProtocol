# PLAN_PROLOGUE.md - Issues to Address

This document lists verified issues with PLAN_PROLOGUE.md that must be fixed before or during implementation.

**STATUS: ALL ISSUES FIXED IN PLAN_PROLOGUE.md (2026-01-07)**

---

## Critical Issues (Will Break Implementation)

### 1. Node Types Changed - Plan Uses Wrong API
**Status:** FIXED

**File:** `src/rsp/level/fixed_generator.py` (planned)
**Reference:** `map.py:89-91`

The plan's `_place_node()` method originally used `.add()` for sets, but nodes are now `dict[tuple[int, int], RestoreNode]`.

**Fix Applied:** Updated `_place_node()` in plan to use dict assignment with RestoreNode:
```python
from rsp.level.map import RestoreNode
self.game_map.cooling_nodes[(x, y)] = RestoreNode(node_type="cooling")
```

---

### 2. Dialogue Title Mismatch
**Status:** FIXED

**File:** Plan references in Phase 5.4.1 and Phase 5.6

Plan had inconsistent death dialogue titles:
- Phase 5.6: `title="DE-RESOLVED"`
- Phase 5.4.1: `"SIMULATION FAILURE" in dialogue.title`

**Fix Applied:** Changed all `handle_dismiss()` checks to use `"DE-RESOLVED"` consistently.

---

### 3. Inventory clear_all() - Wrong Implementation
**Status:** FIXED

**File:** Plan GAP 19 / `src/rsp/combat/inventory.py`

Plan originally proposed `equipped_exploits = [None] * 5` but `equipped_exploits` is `list[str]`.

**Fix Applied:**
```python
def clear_all(self):
    self.items.clear()
    self.equipped_exploits.clear()  # list[str] of exploit keys, not fixed-size
```

---

## Medium Priority Issues (Integration Gaps)

### 4. session.py Doesn't Pass Parameters
**Status:** FIXED

**File:** `src/rsp/core/session.py:76-82`

Plan called `generate_procedural_level(skip_level_start_message=True)` but session.py wrapper doesn't forward parameters.

**Fix Applied:** Updated `_restart_prologue()` to call coordinator directly:
```python
game.game_session.level_coordinator.generate_procedural_level(skip_level_start_message=True)
```

---

### 5. engine.py init Structure Mismatch
**Status:** FIXED

**File:** `src/rsp/core/engine.py:239-261`

Plan showed `if prologue_mode: ... elif not load_save:` but actual code is `if load_save: ... else:`.

**Fix Applied:** Updated plan to show correct nested structure with note about integration.

---

### 6. Missing Post-Generation Integration Points
**Status:** FIXED

**File:** `src/rsp/level/coordinator.py:128-149`

Plan was missing calls to:
- `narrative_manager.reset_level_flags()`
- `turn_manager.reset_blind_spot_tracking()`
- Level loaded message
- `visibility_manager.invalidate_cache()`

**Fix Applied:** Added all integration points to fixed level generation path in plan.

---

### 7. Missing visibility_manager.invalidate_cache()
**Status:** FIXED

**File:** Plan's fixed_generator.py

**Fix Applied:** Added to both coordinator fixed level path and `_restart_prologue()`.

---

### 8. Ascension Modifiers Timing
**Status:** FIXED

**File:** `src/rsp/core/engine.py:87-88`

Plan needed to recalculate ascension modifiers in prologue branch.

**Fix Applied:** Added to engine.py prologue initialization:
```python
self.ascension_level = 0
self.ascension_modifiers = calculate_ascension_modifiers(0)
```

---

## Low Priority Issues (Polish/Cleanup)

### 9. Duplicate Menu Logic
**Status:** DOCUMENTED (no code change needed in plan)

**File:** `src/rsp/ui/menu_main.py`

Both `_build_options_list()` and `refresh_options()` have duplicate option-building logic.

**Note:** Plan already mentions adding "Tutorial" to BOTH methods.

---

### 10. Missing Methods to Implement
**Status:** DOCUMENTED IN PLAN

**Files:** Various

Methods to add during implementation:
1. `Player.reset_temporary_effects()` - defined in plan
2. `InventoryManager.clear_all()` - fixed in plan (Issue #3)
3. `_restart_prologue()` - defined in plan

---

### 11. level/__init__.py Exports
**Status:** FIXED

**File:** `src/rsp/level/__init__.py`

**Fix Applied:** Added specific exports to plan:
```python
from rsp.level.fixed_levels import FixedLevelData, get_prologue_layout
from rsp.level.fixed_generator import FixedLevelGenerator
```

---

### 12. Layout Dimension Documentation
**Status:** FIXED

**File:** PLAN_PROLOGUE.md Phase 3.1

**Fix Applied:** Changed "~25x20" to "26x20" to match actual layout.

---

## Verified as Correct (No Issues)

The following aspects were verified and are compatible:

- `death_handler.reset()` exists at `death.py:232-235`
- `Enemy(Position(x,y), enemy_type)` constructor signature is correct
- `DialogueInputManager.handle_dismiss()` is at line 233 as stated
- `loop.py:883` ESC auto_save location is correct
- `config.py` DEFAULTS dict location and auto-persistence mechanism are correct
- `state.py` network config lookup handles level 0 correctly
- `metrics.py` already handles `_current_session = None` gracefully
- `generator.py` doesn't need modification (per plan)

---

## Summary

| Issue | Status |
|-------|--------|
| #1 RestoreNode API | FIXED |
| #2 Dialogue title mismatch | FIXED |
| #3 Inventory clear_all() | FIXED |
| #4 session.py parameter | FIXED |
| #5 engine.py structure | FIXED |
| #6 Post-generation integration | FIXED |
| #7 visibility cache | FIXED |
| #8 Ascension timing | FIXED |
| #9 Duplicate menu logic | DOCUMENTED |
| #10 Missing methods | DOCUMENTED |
| #11 __init__.py exports | FIXED |
| #12 Layout dimension | FIXED |

**All issues have been addressed in PLAN_PROLOGUE.md. The plan is now ready for implementation.**
