# Game Input Refactoring Plan - Phase 0 Complete

**Status:** Ready for implementation
**Baseline tests:** Phase 0 tests created and passing
**Bug fixes applied:** Targeting visual (Chebyshev distance), Overclock dialogue preference

---

## Executive Summary

Refactor `game_input.py` (1408 lines) into focused, maintainable modules while preserving all functionality. Phase 0 baseline tests provide regression protection. Each phase is independently useful and can be stopped at any boundary.

**Benefits:**
- Better organization (8 responsibilities → 5 focused modules)
- Easier testing (isolated units)
- Clearer code ownership (each module has one job)
- Safer changes (comprehensive test coverage)

---

## Phase 0: Baseline & Bug Fixes ✓ COMPLETE

**Goal:** Create comprehensive tests and fix critical bugs before refactoring

**Completed:**
1. ✓ Created `tests/integration/test_input_system_comprehensive.py`
   - Dialogue input flows (overclock, death, gateway)
   - Modal screen navigation (inventory, look mode, targeting, lore, achievements)
   - Mouse input handling (clicks, hovers, wheels)
   - Input priority system (popup > dialogue > modal > gameplay)
   - Coordinate conversion validation

2. ✓ Created `tests/integration/test_dialogue_user_preferences.py`
   - Overclock warning disabled/enabled behavior
   - "Don't show again" button functionality
   - Dialogue preference persistence
   - **EXPOSED BUG:** Disabled warnings blocked exploits instead of auto-executing

3. ✓ Fixed targeting visual bug (game_rendering_glyphs.py:767)
   - Changed Euclidean distance → Chebyshev distance
   - Now matches gameplay validation (diagonals count as range 1)
   - Affects: buffer_overflow (range 1), memory_leak (range 1)

4. ✓ Fixed overclock dialogue preference bug (game_combat.py:145, game_dialogue_system.py:100)
   - `DialogueState.show()` now returns `bool` (shown vs suppressed)
   - Auto-confirms overclock when warning disabled by user
   - Exploits execute correctly with warnings off

**Test Results:**
- All existing tests pass
- Phase 0 tests provide regression baseline
- Bug fixes verified by new tests

---

## Phase 1: Extract Coordinate Conversion

**Goal:** Create dedicated `InputCoordinateConverter` class

**Complexity:** Low
**Risk:** Minimal (pure functions, no side effects)

### Tasks

1. Create `game_input_coordinates.py`
   ```python
   class InputCoordinateConverter:
       """Handles pixel-to-world coordinate conversion for input system."""

       @staticmethod
       def get_window_dimensions(renderer, game) -> Tuple[int, int]:
           """Get window dimensions from context."""

       @staticmethod
       def pixel_to_world_position(pixel_x, pixel_y, renderer, game,
                                    graphics_mode, camera_offset) -> Optional[Position]:
           """Convert SDL pixel coords to world coords."""
   ```

2. Extract from `game_input.py`:
   - `_get_window_dimensions()` → `get_window_dimensions()`
   - `_mouse_pixel_to_world()` → `pixel_to_world_position()`
   - Pixel-to-tile conversion logic (currently inline)

3. Update `InputHandler` methods:
   - `handle_mouse_motion()` - use converter
   - `handle_mouse_click()` - use converter
   - `_handle_*_mouse_motion()` - use converter
   - `_handle_*_left_click()` - use converter

4. Test:
   - Run Phase 0 mouse tests
   - Manual smoke test (click, hover, wheel)
   - Verify both glyph and graphics modes

**Verification:**
```bash
pytest tests/integration/test_input_system_comprehensive.py::TestMouseInputHandling -v
pytest tests/unit/test_input_mouse_handling.py -v
```

**Files changed:**
- `game_input_coordinates.py` (new, ~100 lines)
- `game_input.py` (remove coordinate methods, import converter)

---

## Phase 2: Extract Dialogue Handler

**Goal:** Centralize dialogue interaction logic

**Complexity:** Medium
**Risk:** Medium (touches game state but well-bounded)

### Tasks

1. Create `game_input_dialogue.py`
   ```python
   class DialogueInputManager:
       """Handles dialogue input and confirmation flows."""

       def __init__(self, game):
           self.game = game

       def handle_dialogue_input(self, event) -> bool:
           """Main dialogue input dispatcher."""

       def handle_confirm(self) -> None:
           """Process dialogue confirmation (Y)."""

       def handle_dismiss(self) -> bool:
           """Process dialogue dismissal (N/ESC)."""

       def handle_dont_show_again(self) -> None:
           """Process 'don't show again' (D)."""

       def handle_dialogue_left_click(self, event) -> bool:
           """Handle mouse clicks on dialogue."""

       def handle_dialogue_mouse_motion(self, event) -> bool:
           """Handle mouse hover over dialogue."""
   ```

2. Extract from `game_input.py`:
   - `_handle_dialogue_input()` → `handle_dialogue_input()`
   - `_handle_dialogue_confirm()` → `handle_confirm()`
   - `_handle_dialogue_dismiss()` → `handle_dismiss()`
   - `_handle_dialogue_dont_show_again()` → `handle_dont_show_again()`
   - `_handle_dialogue_left_click()` → `handle_dialogue_left_click()`
   - `_handle_dialogue_mouse_motion()` → `handle_dialogue_mouse_motion()`

3. Replace string-based type detection with constants:
   ```python
   # OLD (game_input.py:220)
   if "OVERCLOCK WARNING" in dialogue.title:

   # NEW (game_input_dialogue.py)
   from game_dialogue_system import DialogueType
   if dialogue.type == DialogueType.OVERCLOCK_WARNING:
   ```

4. Update `InputHandler` to delegate:
   ```python
   def __init__(self, game, renderer=None):
       self.game = game
       self.renderer = renderer
       self.dialogue_manager = DialogueInputManager(game)  # NEW

   def _handle_dialogue_input(self, event) -> bool:
       return self.dialogue_manager.handle_dialogue_input(event)
   ```

5. Test:
   - Run Phase 0 dialogue tests
   - Test all dialogue types (death, gateway, overclock, friendly fire, debug export)
   - Verify mouse + keyboard interaction
   - Test "don't show again" functionality

**Verification:**
```bash
pytest tests/integration/test_input_system_comprehensive.py::TestDialogueInputHandling -v
pytest tests/integration/test_dialogue_user_preferences.py -v
pytest tests/integration/test_dialogue_edge_cases.py -v
```

**Files changed:**
- `game_input_dialogue.py` (new, ~300 lines)
- `game_input.py` (remove dialogue methods, delegate to manager)
- `game_dialogue_system.py` (optional: add DialogueType enum for type-safe detection)

---

## Phase 3: Extract Modal Screen Handlers

**Goal:** Create focused handler classes for each modal screen

**Complexity:** Low-Medium
**Risk:** Low (each modal is independent)

### Tasks

1. Create `game_input_modals.py`
   ```python
   class InventoryInputHandler:
       """Handles inventory screen input."""
       def __init__(self, game):
           self.game = game

       def handle_keyboard(self, event) -> bool:
           """Handle inventory keyboard input."""

       def handle_mouse_motion(self, event) -> bool:
           """Handle inventory mouse hover."""

       def handle_mouse_click(self, event) -> bool:
           """Handle inventory mouse click."""

       def handle_mouse_wheel(self, event) -> bool:
           """Handle inventory scrolling."""

   class LookModeInputHandler:
       """Handles look mode input."""
       # Similar structure

   class TargetingInputHandler:
       """Handles targeting mode input."""
       # Similar structure

   class LoreViewerInputHandler:
       """Handles lore viewer input."""
       # Similar structure

   class AchievementsInputHandler:
       """Handles achievements screen input."""
       # Similar structure
   ```

2. Extract from `game_input.py`:
   - Inventory: `_handle_inventory_input()`, `_navigate_inventory()`, `_use_selected_inventory_item()`, `_unequip_selected_exploit()`, `_open_inventory()`, mouse handlers
   - Look mode: `_handle_look_mode_input()`, `_enter_look_mode()`, `_move_look_cursor()`, mouse handlers
   - Targeting: `_handle_targeting_input()`, mouse handlers
   - Lore: `_handle_lore_viewer_input()`, `_navigate_lore_viewer()`, mouse handlers
   - Achievements: `_handle_achievements_input()`, mouse handlers

3. Update `InputHandler` to delegate:
   ```python
   def __init__(self, game, renderer=None):
       self.game = game
       self.renderer = renderer
       self.dialogue_manager = DialogueInputManager(game)
       self.inventory_handler = InventoryInputHandler(game)  # NEW
       self.look_mode_handler = LookModeInputHandler(game)  # NEW
       # ... etc

   def _handle_inventory_input(self, event) -> bool:
       return self.inventory_handler.handle_keyboard(event)
   ```

4. Test each modal:
   - Inventory: navigation, selection, use, unequip, mouse
   - Look mode: cursor movement, ESC, L, mouse
   - Targeting: cursor movement, Enter, ESC, mouse
   - Lore: navigation, reading mode, mouse
   - Achievements: scrolling, ESC, mouse

**Verification:**
```bash
pytest tests/integration/test_input_system_comprehensive.py::TestModalInputHandling -v
pytest tests/integration/test_menu_interactions.py -v
```

**Files changed:**
- `game_input_modals.py` (new, ~400 lines)
- `game_input.py` (remove modal methods, delegate to handlers)

---

## Phase 4: Extract UI Interaction Detector

**Goal:** Centralize clickable UI element detection

**Complexity:** Low
**Risk:** Minimal (pure detection logic)

### Tasks

1. Create `game_input_ui_detection.py`
   ```python
   class UIClickDetector:
       """Detects clicks on UI elements."""

       @staticmethod
       def check_inv_button_click(pixel_x: int, pixel_y: int,
                                   window_w: int, window_h: int) -> bool:
           """Check if [Inv] button was clicked."""

       @staticmethod
       def check_exploit_bar_click(pixel_x: int, pixel_y: int,
                                    window_w: int, window_h: int) -> Optional[int]:
           """Check if exploit bar was clicked. Returns slot index or None."""
   ```

2. Extract from `game_input.py`:
   - `_handle_inv_button_click()` → `check_inv_button_click()`
   - `_handle_exploit_bar_click()` → `check_exploit_bar_click()`

3. Update gameplay mouse handler:
   ```python
   def _handle_gameplay_left_click(self, event) -> bool:
       pixel_x, pixel_y = event.position.x, event.position.y
       window_w, window_h = self._get_window_dimensions()

       # Check UI buttons
       if UIClickDetector.check_inv_button_click(pixel_x, pixel_y, window_w, window_h):
           self._open_inventory()
           return True

       exploit_slot = UIClickDetector.check_exploit_bar_click(pixel_x, pixel_y, window_w, window_h)
       if exploit_slot is not None:
           self._use_exploit_slot(exploit_slot)
           return True

       # Gameplay click (move/autowalk)
       world_pos = self._mouse_pixel_to_world(pixel_x, pixel_y)
       # ...
   ```

4. Test:
   - Click inventory button
   - Click each exploit bar slot
   - Click outside UI (ensure gameplay still works)

**Verification:**
```bash
pytest tests/integration/test_input_system_comprehensive.py::TestMouseInputHandling -v
```

**Files changed:**
- `game_input_ui_detection.py` (new, ~100 lines)
- `game_input.py` (remove UI detection methods, import detector)

---

## Phase 5: Consolidate and Document

**Goal:** Clean up remaining code, add documentation

**Complexity:** Low
**Risk:** Minimal (no functional changes)

### Tasks

1. Review `game_input.py` structure:
   - Should now be primarily a router/dispatcher (~400-500 lines)
   - `__init__()` - create delegated managers
   - `handle_keydown()` - route by state priority
   - `handle_mouse_*()` - route by state priority
   - `_handle_gameplay_input()` - core gameplay keys
   - `_handle_escape()` - ESC key routing

2. Add module-level documentation to new files:
   ```python
   """
   game_input_coordinates.py - Coordinate Conversion

   Handles pixel-to-world coordinate conversion for input events.
   Supports both glyph mode (console tiles) and graphics mode (sprite grid).
   """
   ```

3. Update inline comments for clarity:
   - Document state priority system
   - Explain coordinate conversion flow
   - Clarify modal vs dialogue vs gameplay routing

4. Consider method naming consistency:
   - `handle_*` for public methods
   - `_handle_*` for private dispatch
   - No mixing of conventions

5. Run full test suite:
   ```bash
   pytest tests/ -v
   ```

6. Manual play-through:
   - Start game, navigate menus
   - Test keyboard + mouse for all systems
   - Test edge cases (death dialogue, overclock, targeting, etc.)

**Verification:**
```bash
pytest tests/integration/test_input_system_comprehensive.py -v
pytest tests/integration/test_dialogue_user_preferences.py -v
pytest tests/unit/test_input_mouse_handling.py -v
pytest tests/ -k "input"
```

**Files changed:**
- All new modules (add documentation)
- `game_input.py` (clean up, add comments)

---

## File Structure After Refactor

```
game_input.py              (~400-500 lines)  Main router/dispatcher
game_input_coordinates.py  (~100 lines)     Coordinate conversion
game_input_dialogue.py     (~300 lines)     Dialogue handling
game_input_modals.py       (~400 lines)     Modal screen handlers
game_input_ui_detection.py (~100 lines)     UI element detection
```

**Total:** ~1300-1400 lines (same as current, but organized)

---

## Testing Strategy

**After each phase:**
1. Run Phase 0 baseline tests
2. Run relevant unit tests
3. Manual smoke test:
   - Start game
   - Navigate menus
   - Test affected systems (keyboard + mouse)
   - Test edge cases

**Full regression after Phase 5:**
```bash
# Unit tests
pytest tests/unit/test_input*.py -v

# Integration tests
pytest tests/integration/test_input*.py -v
pytest tests/integration/test_dialogue*.py -v
pytest tests/integration/test_menu*.py -v

# Full suite
pytest tests/ -v
```

---

## Risk Mitigation

**Minimize risk:**
- Git commit after each successful phase
- Keep commits small and reversible
- Test before AND after each change
- Can stop at any phase boundary

**If blocked:**
- Roll back to last commit
- Re-evaluate approach
- Ask for clarification
- Proceed to next phase (phases are independent)

---

## Menu Default Fix (Already Correct)

**User concern:** Game should default to "Continue Game" if save exists

**Current behavior (CORRECT):**
- `BaseMenu.__init__()` sets `self.selected_option = 0` (game_menu_base.py:41)
- `MainMenu._build_options_list()` adds "Continue Game" at index 0 if save exists (game_menus.py:80-82)
- Otherwise "New Game" is at index 0

**Result:** ✓ Already working as intended - no changes needed

---

## Summary

This refactor plan provides:
1. **Comprehensive baseline tests** - catch regressions
2. **Incremental phases** - stop at any point
3. **Clear ownership** - each module has one job
4. **Bug fixes included** - targeting visual + overclock dialogue
5. **Low risk** - small changes, heavy testing

Each phase is independently useful. Can proceed with confidence knowing Phase 0 tests will catch any regressions.
