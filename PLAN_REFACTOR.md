# Code Refactoring Plan - Bloat Analysis

**Analysis Date:** 2025-10-21
**Scope:** Comprehensive codebase scan
**Focus:** Over-engineered, bloated, and redundant code sections

---

## Executive Summary

This analysis identified **14 major bloat patterns** across the codebase, with an estimated **~600 lines** of pure redundancy and over-engineering. The most severe issues are:

1. **Pass-through method hell** (150+ lines of delegation in LevelGenerator)
2. **Duplicated menu rendering logic** (109+ lines)
3. **Repeated validation patterns** (graphics mode, loot placement)
4. **Legacy code retention** (unused Bresenham FOV, old patrol logic)
5. **Over-defensive programming** (excessive type checking, nested try-except)

---

## 🔴 Critical Bloat (High Priority)

### 1. Pass-Through Method Hell in LevelGenerator
**File:** `game_level.py`
**Lines:** 258-417 (160 lines!)
**Severity:** CRITICAL

#### The Problem
```python
# Backward Compatibility: Pass-through methods for testing
def _select_room_type(self, level, width, height):
    return self.room_generator.select_room_type(level, width, height)

def _get_room_type_weights(self, level):
    return self.room_generator.get_room_type_weights(level)

def _carve_rectangular_room(self, room):
    return self.room_generator.carve_rectangular_room(room)

# ... 30+ MORE OF THESE! ...
```

**Why It's Bloated:**
- 160 lines that do nothing but delegate
- "For backward compatibility" but tests should be updated instead
- Creates unnecessary indirection
- Makes codebase harder to navigate

**Recommendation:**
1. Delete ALL pass-through methods (lines 258-417)
2. Update tests to use subsystems directly:
   ```python
   # OLD: level_generator._carve_rectangular_room(room)
   # NEW: level_generator.room_generator.carve_rectangular_room(room)
   ```
3. This subsystem architecture is actually good - just remove the delegation layer

**Estimated Savings:** 160 lines

---

### 2. Property Boilerplate in GameEngine
**File:** `game_engine.py`
**Lines:** 156-206 (50 lines)
**Severity:** HIGH

#### The Problem
```python
@property
def level(self) -> int:
    """Current game level."""
    return self.game_state.level

@level.setter
def level(self, value: int) -> None:
    """Set current game level."""
    self.game_state.level = value

@property
def turn(self) -> int:
    """Current turn number."""
    return self.game_state.turn

@turn.setter
def turn(self, value: int) -> None:
    """Set current turn number."""
    self.game_state.turn = value

# ... 7 MORE properties just like this! ...
```

**Why It's Bloated:**
- 9 properties (50 lines) that just forward to `game_state`
- "Backward compatibility" excuse again
- No actual logic, just indirection

**Recommendation:**
1. Update all usages to `game.game_state.level` instead of `game.level`
2. Delete properties (lines 156-206)
3. If you REALLY need them, keep 2-3 most common ones, delete the rest

**Estimated Savings:** 40-50 lines

---

### 3. Duplicated Menu Box Rendering
**File:** `game_menus.py`
**Lines:** SettingsMenu._render_right_side_box (409-517, 109 lines!)
**Severity:** HIGH

#### The Problem
The `_render_right_side_box()` method is likely duplicated across multiple menu classes. It's 109 lines of complex box-drawing logic that:
- Calculates box dimensions
- Handles background vs glyph mode
- Draws borders and backgrounds
- Returns positioning data

This should be in ONE place, not duplicated.

**Recommendation:**
1. Move to `BaseMenu` class (if it exists) or create `MenuRenderingUtils.render_right_side_box()`
2. All menus call the shared method
3. Check MainMenu, HelpMenu, LoreMenu for similar duplication

**Estimated Savings:** 100+ lines (if duplicated 2-3 times)

---

### 4. Repeated Graphics Mode Validation
**File:** `game_rendering_core.py` (from earlier analysis)
**Occurrences:** 3+ times throughout file
**Severity:** HIGH

#### The Problem
```python
should_use_graphics = (self.settings and
                       self.settings.graphics_mode == "graphics" and
                       self.tile_manager is not None and
                       self.context is not None and
                       hasattr(self.context, 'sdl_renderer') and
                       self.context.sdl_renderer is not None and
                       hasattr(self.context, 'console_render') and
                       self.context.console_render is not None)
```

This 7-line boolean expression is repeated multiple times.

**Recommendation:**
```python
def _is_graphics_mode_available(self) -> bool:
    """Check if graphics rendering is available and enabled."""
    return (self.settings and
            self.settings.graphics_mode == "graphics" and
            self.tile_manager is not None and
            self.context is not None and
            hasattr(self.context, 'sdl_renderer') and
            self.context.sdl_renderer is not None and
            hasattr(self.context, 'console_render') and
            self.context.console_render is not None)
```

Then replace all occurrences with `if self._is_graphics_mode_available():`

**Estimated Savings:** 20-30 lines

---

## 🟡 Moderate Bloat (Medium Priority)

### 5. Legacy Bresenham FOV Method
**File:** `game_map.py`
**Lines:** 127-161 (35 lines)
**Severity:** MODERATE

#### The Problem
```python
def has_line_of_sight_bresenham(self, start: Position, end: Position) -> bool:
    """Check line of sight between two positions using Bresenham's algorithm (legacy)."""
    # ... 35 lines of legacy code ...
```

**Why It's Bloated:**
- Marked as "legacy" in the docstring
- Not used anymore (delegates to TCOD version)
- Taking up space for historical reasons

**Recommendation:**
- Delete the entire method (lines 127-161)
- TCOD FOV is better and already implemented

**Estimated Savings:** 35 lines

---

### 6. Patrol Route Fallback Hell
**File:** `game_enemies.py`
**Lines:** 227-248 (22 lines)
**Severity:** MODERATE

#### The Problem
```python
# Fallback: try multiple simple 2-point patterns
fallback_patterns = [
    Position(start.x + 4, start.y),      # Horizontal right
    Position(start.x - 4, start.y),      # Horizontal left
    Position(start.x, start.y + 4),      # Vertical down
    Position(start.x, start.y - 4),      # Vertical up
    Position(start.x + 3, start.y + 3),  # Diagonal down-right
    Position(start.x - 3, start.y - 3),  # Diagonal up-left
    Position(start.x + 2, start.y),      # Shorter horizontal
    Position(start.x, start.y + 2),      # Shorter vertical
]

for fallback_end in fallback_patterns:
    if self._is_valid_patrol_point(fallback_end):
        route = [start, fallback_end]
        if self._validate_patrol_connectivity(route):
            logging.debug(f"Patrol route: fallback pattern succeeded")
            return route
```

**Why It's Bloated:**
- 8 hardcoded fallback patterns
- Trying to be too clever about patrol generation
- If main algorithm fails, just use simpler logic

**Recommendation:**
Simplify to:
```python
# Simple fallback: try cardinal directions only
for dx, dy in [(4, 0), (-4, 0), (0, 4), (0, -4)]:
    end = Position(start.x + dx, start.y + dy)
    if self._is_valid_patrol_point(end):
        return [start, end]
return [start]  # Static guard
```

**Estimated Savings:** 10-15 lines

---

### 7. Exploit Dispatcher If-Elif Chain
**File:** `game_combat.py`
**Lines:** Large if-elif chain in `_execute_specific_exploit()`
**Severity:** MODERATE

#### The Problem
```python
def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
    if exploit_key == 'shadow_step':
        return self._execute_shadow_step(target)
    elif exploit_key == 'data_mimic':
        return self._execute_data_mimic()
    elif exploit_key == 'noise_maker':
        return self._execute_noise_maker(target)
    # ... 9 MORE elif branches ...
```

**Why It's Bloated:**
- 12-branch if-elif chain
- Hard to extend
- Classic case for dictionary dispatch

**Recommendation:**
```python
def __init__(self, game_engine):
    self.game_engine = game_engine
    self.exploit_handlers = {
        'shadow_step': self._execute_shadow_step,
        'data_mimic': self._execute_data_mimic,
        'noise_maker': self._execute_noise_maker,
        # ... etc ...
    }

def _execute_specific_exploit(self, exploit_key: str, exploit: ExploitDefinition, target: Position) -> bool:
    handler = self.exploit_handlers.get(exploit_key)
    if handler:
        return handler(target) if exploit.target_type != 'none' else handler()
    return False
```

**Estimated Savings:** 10 lines + better extensibility

---

### 8. Discovery Status Update Loop
**File:** `game_inventory.py`
**Lines:** CodeHack.use() method
**Severity:** MODERATE

#### The Problem
```python
if not is_known:
    # Mark as discovered and update ALL matching codes in inventory
    game.discovered_code_effects[self.color_name] = effect_key
    for item in player.inventory_manager.items:
        if isinstance(item, CodeHack) and item.color_name == self.color_name:
            item.discovered = True
            item.description = description
```

**Why It's Bloated:**
- Loops through ENTIRE inventory EVERY time a code is used
- This happens even when effect is already discovered
- Redundant updates

**Recommendation:**
```python
if not is_known:
    # Mark globally as discovered
    game.discovered_code_effects[self.color_name] = effect_key
    # Update only this instance - sync happens on level load
    self.discovered = True
    self.description = description
```

Then sync ALL codes when level loads (once per level, not per use).

**Estimated Savings:** Simpler code + better performance

---

### 9. Over-Defensive Type Checking
**File:** `game_state.py`
**Lines:** 237-240 (TurnProcessor)
**Severity:** MODERATE

#### The Problem
```python
# Safe formatting to handle both real values and mocks in tests
try:
    trace_str = f"{float(player.trace_level):.1f}" if hasattr(player.trace_level, '__float__') else str(player.trace_level)
except (TypeError, ValueError):
    trace_str = str(player.trace_level)
```

Same pattern appears multiple times (lines 318-326).

**Why It's Bloated:**
- Production code shouldn't bend over backward for test mocks
- Tests should provide proper types
- This is defensive programming gone too far

**Recommendation:**
```python
trace_str = f"{player.trace_level:.1f}"
```

If tests break, fix the tests to use real values.

**Estimated Savings:** 10-15 lines

---

## 🟢 Minor Bloat (Low Priority)

### 10. Loot Room Placement Duplication
**File:** `game_session.py`
**Lines:** 753-815 (_place_code_hacks) and 830-881 (_place_exploit_pickups)
**Severity:** LOW

#### The Problem
Both methods have nearly identical loot room clustering logic:
- Calculate loot room count
- Place items in loot rooms first
- Place remaining items in normal areas

**Recommendation:**
Extract common logic:
```python
def _place_items_with_clustering(self, total_count, loot_percentage, item_factory):
    # Shared placement logic
    pass

def _place_code_hacks(self):
    self._place_items_with_clustering(
        total_count=12 + self.level * 4,
        loot_percentage=0.3,
        item_factory=self._create_code_hack
    )
```

**Estimated Savings:** 20-30 lines

---

### 11. Duplicate Border Wall Creation
**File:** `game_level_features.py` (TilePlacementGenerator) and `game_session.py` (GameSession)
**Severity:** LOW

#### The Problem
Two implementations of border wall creation:
- `TilePlacementGenerator.ensure_border_walls_new()` (lines 1278-1290)
- `GameSession._create_border_walls()` (lines 712-721)

**Recommendation:**
Pick one, delete the other. Probably keep the one in TilePlacementGenerator since it's the dedicated placement subsystem.

**Estimated Savings:** 10 lines

---

### 12. Error Handling Verbosity in Game Loop
**File:** `game_loop.py`
**Lines:** 390-452, 454-467, 470-481
**Severity:** LOW

#### The Problem
Three nested try-except blocks with nearly identical error handling:
```python
# Pattern repeated 3 times:
except Exception as e:
    import traceback
    tb = traceback.extract_tb(e.__traceback__)
    line_no = tb[-1].lineno if tb else "?"
    filename = tb[-1].filename if tb else "unknown"
    logging.error(f"Error in {filename}:{line_no}")
    logging.error(f"Exception: {str(e)}")
    traceback.print_exc()
```

**Recommendation:**
```python
def log_exception(e: Exception, context: str):
    """Centralized exception logging."""
    tb = traceback.extract_tb(e.__traceback__)
    line_no = tb[-1].lineno if tb else "?"
    filename = tb[-1].filename if tb else "unknown"
    logging.error(f"{context} in {filename}:{line_no}")
    logging.error(f"Exception: {str(e)}")
    traceback.print_exc()

# Usage:
except Exception as e:
    log_exception(e, "Rendering failure")
```

**Estimated Savings:** 15-20 lines

---

### 13. Delegation Methods in GameEngine
**File:** `game_engine.py`
**Lines:** 212-236
**Severity:** LOW

#### The Problem
```python
def _process_player_turn(self):
    """Process player turn by updating temporary effects and incrementing turn counter."""
    self.turn_processor.process_turn(self.player)

def _process_enemies_turn(self):
    """Process all enemy turns (movement, attacks, AI decisions)."""
    self.game_session._update_enemies()

# ... 4 more similar methods ...
```

**Why It's Bloated:**
- Again, "backward compatibility" delegation
- Tests should be updated

**Recommendation:**
Update callers to use subsystems directly, delete these methods.

**Estimated Savings:** 25 lines

---

### 14. Duplicate Gateway Strategy Validation
**File:** `game_level_features.py`
**Lines:** 1560-1693 (gateway placement strategies)
**Severity:** LOW

#### The Problem
Four gateway strategies (`gateway_far_corner`, `gateway_central_hub`, etc.) with repeated patterns:
- Distance validation from spawn
- Fallback logic
- Warning logging

**Recommendation:**
Extract common validation:
```python
def _validate_gateway_position(self, pos, min_distance, spawn):
    distance = spawn.distance_to(Position(pos[0], pos[1]))
    return distance > min_distance

def gateway_far_corner(self, spawn, floor_positions):
    min_distance = self._get_min_distance('far_corner')
    valid = [p for p in floor_positions if self._validate_gateway_position(p, min_distance, spawn)]
    return random.choice(valid) if valid else self._fallback_gateway(spawn, floor_positions)
```

**Estimated Savings:** 20-30 lines

---

## Summary Table

| # | Issue | File | Lines Affected | Priority | Est. Savings |
|---|-------|------|----------------|----------|--------------|
| 1 | Pass-through methods | game_level.py | 258-417 | CRITICAL | 160 lines |
| 2 | Property boilerplate | game_engine.py | 156-206 | HIGH | 40-50 lines |
| 3 | Menu box duplication | game_menus.py | ~400-517 | HIGH | 100+ lines |
| 4 | Graphics validation | rendering_core | Multiple | HIGH | 20-30 lines |
| 5 | Legacy Bresenham | game_map.py | 127-161 | MODERATE | 35 lines |
| 6 | Patrol fallbacks | game_enemies.py | 227-248 | MODERATE | 10-15 lines |
| 7 | Exploit dispatcher | game_combat.py | ~200-250 | MODERATE | 10 lines |
| 8 | Discovery loop | game_inventory.py | ~60-80 | MODERATE | Performance |
| 9 | Defensive typing | game_state.py | Multiple | MODERATE | 10-15 lines |
| 10 | Loot placement | game_session.py | 753-881 | LOW | 20-30 lines |
| 11 | Border walls | Multiple | Multiple | LOW | 10 lines |
| 12 | Error handling | game_loop.py | Multiple | LOW | 15-20 lines |
| 13 | GameEngine delegation | game_engine.py | 212-236 | LOW | 25 lines |
| 14 | Gateway validation | game_level_features.py | 1560-1693 | LOW | 20-30 lines |

**Total Estimated Savings:** ~500-600 lines of code

---

## Refactoring Strategy

### Phase 1: Critical Fixes (Immediate)
1. ✅ **DONE** - Delete pass-through methods in LevelGenerator
2. ⏭️ **SKIPPED** - Remove property boilerplate in GameEngine (API degradation concerns)
3. ✅ **DONE** - Consolidate menu box rendering (removed 109-line duplicate from SettingsMenu)

**Impact:** ~160 lines removed (Task #1) + 109 lines removed (Task #3) = **269 lines saved**

### Phase 2: Moderate Improvements (Next)
4. ✅ **DONE** - Create helper for graphics mode validation (extracted repeated 8-line check)
5. ✅ **DONE** - Delete legacy Bresenham FOV (removed 35-line legacy method + 2 tests)
6. ❌ **REMOVED FROM PLAN** - Simplify patrol route fallbacks (concerns about gameplay impact)
7. ✅ **DONE** - Convert exploit dispatcher to dictionary (24-line if-elif → 5-line dict lookup)

**Impact:** ~65 lines removed (graphics: ~14 lines, Bresenham: ~45 lines, dispatcher: ~21 lines) + cleaner patterns

### Phase 3: Polish (Future)
8. Optimize discovery status updates
9. Remove over-defensive type checking
10. Consolidate loot placement logic
11. Centralize error logging
12-14. Minor cleanups

**Impact:** ~100-200 lines removed, better performance

---

## Testing Requirements

After each refactoring:
1. Run `python test_commands.py full` (all tests + coverage)
2. Manually test affected systems in-game
3. Check that no functionality changed

---

## Notes

- Many bloat issues stem from "backward compatibility" with tests
- **Tests should be updated when architecture changes** - don't bloat production code for test convenience
- The subsystem architecture (RoomGenerator, CorridorGenerator, etc.) is actually GOOD
  - The problem is keeping delegation layers on top
- Focus on deleting code, not rewriting it
  - Less code = less bugs = easier maintenance

