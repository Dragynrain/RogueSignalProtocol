# Dialogue & Input System Redesign Plan

## Problem Summary

**Current Issues**:
- Duplicated transparency-setting code (4 places)
- Duplicated rendering routing logic (3 places in game_rendering_core.py)
- Multiple different dialogue implementations (dedicated vs generic renderers)
- Legacy dead code paths (gateway confirmation, escape handler)
- No reusable coordinate/bounds helpers
- Recurring transparency bugs (TCOD [y,x] indexing confusion)
- Save deletion in renderer (should be in game logic)

**Solution**: Build unified dialogue system with:
- Single renderer for ALL dialogues
- Reusable coordinate helpers (fixes [y,x] indexing once)
- Data-driven dialogues (DialogueBox dataclass)
- Clean state management (DialogueState with priority queue)
- All input handling stays in game_input.py

---

**Architecture Decisions**:
1. **Coordinate Convention**: (x, y) parameter order in our code, [y, x] only when accessing TCOD arrays
2. **Single File**: Start with `game_dialogue_system.py`, split later if needed (>2000 lines)
3. **Keep Priority Queue**: Needed for multiple simultaneous dialogues (overclock warning + attack)
4. **Keep "Don't Show Again"**: User preference checking stays
5. **Input Stays in game_input.py**: Current pattern works, don't change it
6. **Save Deletion**: Move from renderer to `GameTurnManager.process_turn()` (renderers shouldn't have side effects)
7. **Console-Only Dialogues**: No sprite backgrounds, just console overlays with opaque regions

**New Components**:
- `CoordinateHelpers` class - Reusable coordinate/bounds utilities (fixes [y,x] indexing once)
- `DialogueBox` dataclass - Pure data, no logic
- `DialogueState` manager - Replace current DialogueManager, simpler
- `UnifiedRenderer` - ONE renderer for ALL dialogues
- `DialogueInputHandler` - Pure input processing (called from game_input.py)
- Factory functions - `create_gateway_dialogue()`, `create_death_dialogue()`, etc.

**Critical Rendering Order** (graphics mode):
1. SDL sprites (background layer)
2. Console UI panels (opaque)
3. **Transparency pass** (set game area alpha=0)
4. **Dialogues** (render AFTER transparency, set own area alpha=255)
5. Composite and present

---

## Implementation Phases

### Phase 1: Foundation - Coordinate Helpers
**Goal**: Create reusable coordinate utilities (fixes [y,x] indexing bugs once and for all).

**Files**: `game_coordinate_helpers.py`, `tests/unit/test_coordinate_helpers.py`

**Tasks**:
- [x] Create `CoordinateHelpers` class with (x, y) parameter order convention
- [x] `center_box()` - Calculate centered box position
- [x] `clamp_bounds()` - Clamp box to array bounds
- [x] `set_alpha_region()` - Set alpha for rectangle (handles [y,x] indexing internally)
- [x] `char_to_pixel_coords()` - Console chars to SDL pixels (for sprite positioning)
- [x] Write unit tests (center, clamp, alpha, pixel conversion)
- [x] Visual test: Draw boxes at various positions to verify math
- [x] Run test suite: `uv run pytest tests/ -v --tb=short`

**Validation**: ✅ All tests pass (29/29), helpers work with different console sizes (80x50, 54x27).

---

### Phase 2: New Dialogue System (Parallel to Old)
**Goal**: Build complete new system without breaking existing code.

**Files**: `game_dialogue_system.py`, `tests/unit/test_dialogue_system.py`, `tests/integration/test_dialogue_rendering.py`

**Tasks**:
- [ ] `DialogueBox` dataclass (title, message, options, colors, valid_keys, format_data)
- [ ] `DialogueState` manager (show, close, is_active, get_active, should_show_dialogue)
- [ ] Priority queue implementation (List[tuple[DialogueBox, int]])
- [ ] `UnifiedRenderer` using CoordinateHelpers (ONE renderer for ALL dialogues)
- [ ] `DialogueInputHandler` - Pure input processing, returns action strings
- [ ] Factory functions: `create_gateway_dialogue()`, `create_death_dialogue()`, `create_victory_dialogue()`
- [ ] Factory functions: `create_overclock_warning_dialogue()`, `create_inventory_attack_dialogue()`
- [ ] Word-wrap helper (reuse existing `_wrap_dialogue_text()` from game_dialogue_renderer.py)
- [ ] Unit tests (DialogueBox creation, formatting, state management, input handling)
- [ ] Integration tests (rendering with transparency, all dialogue types render without crashes)
- [ ] Manual visual check: Each dialogue type renders correctly in both modes
- [ ] Run test suite: `uv run pytest tests/ -v --tb=short`

**Validation**: All tests pass, new system works in isolation, old system still functional.

---

### Phase 3: Migration - Replace Old System
**Goal**: Switch game to use new system, remove old code.

**Files Modified**: `game_rendering_core.py`, `game_input.py`, `game_engine.py`, `game_turn_manager.py`, `game_combat.py`, all tests
**Files Deleted**: `game_dialogue.py`, `game_dialogue_renderer.py`

**Tasks**:
- [ ] **Death save deletion** (FIRST): Move from renderer to `GameTurnManager.process_turn()` - delete save when `player.cpu <= 0` first detected
- [ ] Replace `game.dialogue_manager` with `game.dialogue_state` in game engine
- [ ] Update all dialogue creation calls to use factory functions with `should_show_dialogue()` checks
- [ ] Remove `show_gateway_confirmation` flag from game_engine.py and game_input.py
- [ ] **Rendering**: Implement full rendering order (sprites → UI → transparency pass → dialogues → composite)
- [ ] **Rendering**: Replace 3 dialogue routing blocks with single unified call to UnifiedRenderer
- [ ] **Rendering**: Ensure transparency pass happens BEFORE dialogue rendering in graphics mode
- [ ] **Input**: Update `_handle_dialogue_input()` to use new `DialogueInputHandler`
- [ ] **Input**: Update action handling to work with DialogueBox instead of DialogueType
- [ ] **Input**: Remove dead code - `_handle_gateway_confirmation_input()` (lines 245-258)
- [ ] **Input**: Remove dead code - gateway check in escape handler (line 118)
- [ ] Delete `game_dialogue.py` and `game_dialogue_renderer.py`
- [ ] Update all tests using dialogue system to use new API
- [ ] Remove/update tests for deleted code
- [ ] Run test suite: `uv run pytest tests/ -v --tb=short`

**Validation**:
- [ ] Save deleted on death (test by dying and checking filesystem)
- [ ] All dialogue types work (gateway, death, victory, overclock, inventory attack)
- [ ] Transparency works in graphics mode (dialogues opaque, game area transparent)
- [ ] Dialogues render correctly in glyph mode
- [ ] Input handling works for all dialogue types
- [ ] "Don't show again" feature works
- [ ] Dialogue queueing works (trigger two simultaneous dialogues)
- [ ] All tests pass

---

### Phase 4: Documentation & Cleanup
**Goal**: Document new system and finalize.

**Files Modified**: `.claude/CONSOLE_TRANSPARENCY_RULES.md`, all new code files

**Tasks**:
- [ ] Update `.claude/CONSOLE_TRANSPARENCY_RULES.md` with CoordinateHelpers approach
- [ ] Add docstrings to CoordinateHelpers (class + all methods)
- [ ] Add docstrings to DialogueBox, DialogueState, UnifiedRenderer, DialogueInputHandler
- [ ] Add docstrings to all factory functions
- [ ] Add inline comments for transparency pass in game_rendering_core.py
- [ ] Add inline comments for [y, x] indexing in CoordinateHelpers.set_alpha_region()
- [ ] Run test suite: `uv run pytest tests/ -v --tb=short`

**Manual Testing Checklist**:
- [ ] Gateway dialogue (graphics + glyph modes)
- [ ] Death dialogue (graphics + glyph modes)
- [ ] Victory dialogue (graphics + glyph modes)
- [ ] Overclock warning (graphics + glyph modes)
- [ ] Inventory attack warning (graphics + glyph modes)
- [ ] Transparency works (no see-through dialogues in graphics mode)
- [ ] "Don't show again" feature works
- [ ] Dialogue queuing works
- [ ] Save deletion works on death

**Validation**: Documentation clear, all docstrings present, all tests pass, all manual checks verified.

---

## Migration Safety & Rollback

**Strategy**:
- Phase 2: Build new system alongside old (no breaking changes)
- Phase 3: Switch in one commit (easy to revert if needed)
- Old system remains in git history for reference

**Testing Approach**:
- Unit tests: Test helpers and components in isolation
- Integration tests: Test dialogue rendering and input end-to-end
- Manual testing: Every dialogue type in both graphics and glyph modes

**Rollback Plan**: If Phase 3 has issues, revert migration commit, cherry-pick fixes to new system, retry.

---

## Success Criteria

1. All dialogues render with opaque backgrounds (no transparency bugs)
2. Zero code duplication for rendering/transparency logic
3. Zero dead code paths (gateway handler, escape handler)
4. All tests pass
5. Code easier to understand than before
6. CoordinateHelpers reusable for menus/help screens
7. No gameplay regressions
8. Save deletion on death (permadeath preserved)

---

## Critical Reminders

**TCOD [y, x] Indexing**: `console.rgba["bg"][y, x, 3]` NOT `[x, y, 3]` - CoordinateHelpers abstracts this away

**Test Both Modes**: Every dialogue in graphics mode (transparency critical) AND glyph mode

**Don't Over-Engineer**: Keep it simple, priority queue is needed (confirmed use case), no extra features

**Performance**: Not a concern - dialogues only rendered when active, focus on correctness

---

## File Changes Summary

**Created**:
- `game_coordinate_helpers.py`
- `game_dialogue_system.py`
- `tests/unit/test_coordinate_helpers.py`
- `tests/unit/test_dialogue_system.py`
- `tests/integration/test_dialogue_rendering.py`

**Modified**:
- `game_rendering_core.py` - Rendering order, unified dialogue routing (3 places → 1)
- `game_input.py` - Use DialogueInputHandler, remove dead code
- `game_engine.py` - Use DialogueState, remove show_gateway_confirmation
- `game_turn_manager.py` - Save deletion on death
- `game_combat.py` - Use factory functions
- `.claude/CONSOLE_TRANSPARENCY_RULES.md` - Document CoordinateHelpers

**Deleted**:
- `game_dialogue.py`
- `game_dialogue_renderer.py`

---

**End of Plan**
