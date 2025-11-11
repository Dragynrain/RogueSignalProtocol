# Refactoring Plan: File Size Violations

## Summary & Overview

Three core game modules have exceeded the project guideline of ~20,000 tokens (~1,000 lines) and need to be refactored into smaller, focused modules. This refactoring addresses maintenance burden, cognitive load, and adherence to the "one purpose per module" principle.

**Files to refactor:**
- `game_session.py` (1,603 lines) - consolidates 3 separate coordinators
- `game_rendering_ui.py` (1,221 lines) - handles 5+ major rendering responsibilities
- `game_entities.py` (820 lines) - mixes 10 classes including utilities, enums, and entities

**Goals:**
- Reduce file sizes to <500 lines each
- Improve module cohesion and single responsibility
- Maintain or improve test coverage
- Zero breaking changes to external API
- Keep all tests passing throughout

---

## Phases

**Phase 1: game_session.py Split** (High complexity, foundational)
- Extract GameTurnManager, GameLevelCoordinator, GameStatePersistence
- Update ~50-100 import statements across codebase
- Requires careful coordination system refactoring
- Risk: Turn order and game state integrity

**Phase 2: game_rendering_ui.py Split** (Medium complexity)
- Extract DialogueRenderer, InfoPanelRenderer, StatusBarRenderer, UI overlays
- Update rendering pipeline integration points
- Depends on Phase 1 (GameSession is major consumer)
- Risk: Rendering coordinate system errors, alpha channel handling

**Phase 3: game_entities.py Reorganization** (Straightforward)
- Move ColorManager to existing `game_color_manager.py`
- Extract enums, Position class, definitions to separate modules
- Update imports across ~30-40 files
- Depends on Phases 1 & 2 (all systems use entities)
- Risk: Circular import dependencies

---

## Phase 1: game_session.py Split

### Current Structure Analysis

`game_session.py` consolidates three major responsibilities:

1. **GameTurnManager** - Turn execution, action processing, enemy AI coordination
2. **GameLevelCoordinator** - Level transitions, state handoff, progression
3. **GameStatePersistence** - Save/load, serialization, death handling

**Current dependencies:**
- Imported by: `game_engine.py`, `game_input.py`, `RogueSignalProtocol.py`
- Imports: 15+ game modules (combat, entities, level_structure, etc.)

**Complexity:** HIGH
- Tight coupling between turn processing and level coordination
- Save/load touches all game state
- GameEngine expects single GameSession interface

### 1.1: Create game_turn_manager.py

**Extract** GameTurnManager class (~500-600 lines)

**Responsibilities:**
- `process_player_action()` - Execute player moves/attacks/exploits
- `process_enemy_turns()` - Enemy AI coordination and movement
- `advance_turn()` - Turn counter, timed effects, heat reduction
- `update_after_action()` - FOV updates, enemy state changes

**New module API:**
```python
class GameTurnManager:
    def __init__(self, game_engine: GameEngine):
        self.engine = game_engine

    def process_player_action(self, action: Action) -> bool:
        # Process action, update state, advance turn

    def process_enemy_turns(self) -> None:
        # Enemy movement queue execution and AI

    def advance_turn(self) -> None:
        # Increment turn counter, update timed effects
```

**Integration points:**
- `GameSession` becomes thin wrapper calling `turn_manager.process_*`
- `GameEngine` holds reference to `turn_manager`
- Update `game_input.py` to call `engine.turn_manager` where applicable

**Testing approach:**
- Extract existing GameSession turn tests to `test_turn_manager.py`
- Add integration test: "GameSession delegates to GameTurnManager"
- Verify enemy movement tests still pass
- Check turn counter and timed effects work

**Gotchas:**
- Turn manager needs access to full GameEngine (not just player/enemies)
- Death detection happens mid-turn - coordinate with GameStatePersistence
- FOV updates must occur before enemy turns (ordering critical)

### 1.2: Create game_level_coordinator.py

**Extract** GameLevelCoordinator class (~400-500 lines)

**Responsibilities:**
- `transition_to_next_level()` - Level progression, state carry-over
- `validate_level_completion()` - Gateway checks, victory conditions
- `handle_gateway_entry()` - Confirmation dialogue, progression trigger
- `initialize_new_level()` - Map generation, enemy spawning

**New module API:**
```python
class GameLevelCoordinator:
    def __init__(self, game_engine: GameEngine):
        self.engine = game_engine

    def transition_to_next_level(self) -> None:
        # Save player state, generate new level, restore player

    def validate_level_completion(self) -> bool:
        # Check if player can progress (gateway reached, etc.)
```

**Integration points:**
- `GameSession.progress_to_next_level()` delegates to coordinator
- `GameEngine` holds reference to `level_coordinator`
- Level transition dialogue hooks into coordinator

**Testing approach:**
- Extract level transition tests to `test_level_coordinator.py`
- Test state persistence across levels (inventory, upgrades, stats)
- Verify level 1→2→3 transitions work correctly
- Check victory condition on level 3 completion

**Gotchas:**
- Player state must be saved BEFORE map regeneration
- Inventory, upgrades, and story progress must carry over
- Achievement triggers fire during transition (coordinate timing)

### 1.3: Create game_state_persistence.py

**Extract** GameStatePersistence class (~300-400 lines)

**Responsibilities:**
- `save_game()` - Serialize state to saves/save.json
- `load_game()` - Deserialize and restore state
- `handle_player_death()` - Delete save, trigger death dialogue
- `export_debug_state()` - Debug package creation (if in this module)

**New module API:**
```python
class GameStatePersistence:
    def __init__(self, game_engine: GameEngine):
        self.engine = game_engine

    def save_game(self) -> bool:
        # Serialize game state to saves/save.json

    def load_game(self) -> bool:
        # Load and restore game state

    def handle_player_death(self) -> None:
        # Delete save, mark game_over, trigger death dialogue
```

**Integration points:**
- `GameSession` calls `persistence.save_game()` after each turn
- `GameEngine.__init__()` calls `persistence.load_game()` if save exists
- Death detection in turn manager triggers `persistence.handle_player_death()`

**Testing approach:**
- Existing save/load tests move to `test_state_persistence.py`
- Test round-trip: save → load → verify state matches
- Test death: verify save deleted, game_over flag set
- Test corrupted save handling (graceful failure)

**Gotchas:**
- Save must be deleted atomically on death (no partial saves)
- Death can occur mid-turn (virus damage, combat) - coordinate with turn manager
- Debug export might be in different module - check before extracting

### 1.4: Update GameSession to Delegate

**Refactor** GameSession into thin coordinator (~200-300 lines)

**New structure:**
```python
class GameSession:
    def __init__(self, game_engine: GameEngine):
        self.engine = game_engine
        self.turn_manager = GameTurnManager(game_engine)
        self.level_coordinator = GameLevelCoordinator(game_engine)
        self.persistence = GameStatePersistence(game_engine)

    def process_player_action(self, action: Action) -> bool:
        return self.turn_manager.process_player_action(action)

    def progress_to_next_level(self) -> None:
        self.level_coordinator.transition_to_next_level()

    def save_game(self) -> bool:
        return self.persistence.save_game()
```

**Integration checklist:**
- Update `game_engine.py` imports
- Update `game_input.py` to use `engine.session.turn_manager` where needed
- Update `RogueSignalProtocol.py` main loop if it directly calls GameSession
- Verify all 2,042 tests still pass

**Rollback point:** If tests fail, revert to monolithic GameSession and debug extracted classes in isolation

---

## Phase 2: game_rendering_ui.py Split

### Current Structure Analysis

`game_rendering_ui.py` handles 5+ major rendering responsibilities:

1. **DialogueRenderer** - Confirmation dialogues, story fragments, death screens
2. **InfoPanelRenderer** - Right panel (stats, inventory, exploits)
3. **StatusBarRenderer** - Top bar (CPU, heat, level, trace)
4. **MessageLogRenderer** - Bottom panel with game messages
5. **UI Overlays** - Help screen, achievements menu, targeting cursor

**Current dependencies:**
- Imported by: `game_rendering_core.py`, `game_engine.py`
- Uses: `UnifiedRenderer`, `CoordinateHelpers`, `ColorManager`

**Complexity:** MEDIUM
- Rendering order matters (background → sprites → UI)
- Transparency and alpha channel handling critical
- Coordinate system errors can break layout

### 2.1: Create game_dialogue_renderer.py

**Extract** DialogueRenderer class (~250-300 lines)

**Responsibilities:**
- `render_dialogue_box()` - Modal dialogue rendering
- `render_confirmation()` - Yes/No prompts
- `render_story_fragment()` - Multi-line narrative text
- `render_death_screen()` - Game over dialogue

**New module API:**
```python
class DialogueRenderer:
    def render_dialogue(self, console: Console, dialogue: Dialogue) -> None:
        # Render modal dialogue with transparency
        # Use UnifiedRenderer for proper alpha handling
```

**Integration points:**
- `game_rendering_core.py` imports and instantiates DialogueRenderer
- Rendering pipeline calls `dialogue_renderer.render()` after sprites
- Dialogue state tracked in `GameEngine.dialogue_state`

**Testing approach:**
- Existing dialogue rendering tests move to `test_dialogue_renderer.py`
- Test transparency: dialogue should not fully occlude background
- Test multi-line text wrapping
- Test coordinate system: dialogue should be centered

**Gotchas:**
- Must use `UnifiedRenderer.render_with_alpha()` for transparency
- Coordinate system: 80x50 console coords, not game viewport
- DialogueState.get_active() must be checked before rendering

### 2.2: Create game_info_panel_renderer.py

**Extract** InfoPanelRenderer class (~300-350 lines)

**Responsibilities:**
- `render_player_stats()` - CPU, RAM, heat, trace
- `render_inventory()` - Code hacks, exploit pickups
- `render_equipped_exploits()` - Hotkeys Q/W/E/R
- `render_enemy_info()` - Targeted enemy stats
- `render_movement_queue()` - Enemy predicted moves

**New module API:**
```python
class InfoPanelRenderer:
    def render_info_panel(self, console: Console, game_engine: GameEngine) -> None:
        # Render right panel (x=53 to x=79)
        # Use 80x50 console coordinates
```

**Integration points:**
- `game_rendering_core.py` calls `info_panel_renderer.render()` on each frame
- Panel renders in console coordinates (x=53 to x=79, y=0 to y=49)
- Enemy targeting cursor coordinates from `GameEngine.cursor_position`

**Testing approach:**
- Existing info panel tests move to `test_info_panel_renderer.py`
- Test stat display accuracy (CPU/heat/trace values match game state)
- Test inventory scrolling (if >10 items)
- Test enemy queue rendering (3 moves displayed)

**Gotchas:**
- Coordinate system: console (80x50), not game viewport (27x21)
- Movement queue rendering uses arrow symbols (↑↓←→↗↖↙↘)
- Text wrapping for long exploit names

### 2.3: Create game_status_bar_renderer.py

**Extract** StatusBarRenderer class (~150-200 lines)

**Responsibilities:**
- `render_status_bar()` - Top bar with player stats
- `render_level_indicator()` - "Level X/3"
- `render_turn_counter()` - Turn number display
- `render_heat_warning()` - Heat threshold visual indicator

**New module API:**
```python
class StatusBarRenderer:
    def render_status_bar(self, console: Console, game_engine: GameEngine) -> None:
        # Render top bar (y=0, x=0 to x=52)
```

**Integration points:**
- `game_rendering_core.py` calls `status_bar_renderer.render()` on each frame
- Status bar renders before game viewport (background layer)

**Testing approach:**
- Tests move to `test_status_bar_renderer.py`
- Test heat warning color changes (yellow→red at thresholds)
- Test turn counter accuracy
- Test level indicator shows correct level

**Gotchas:**
- Status bar is separate from game viewport (different coordinate space)
- Heat warning colors must match `ColorManager.heat_color_for_value()`

### 2.4: Extract MessageLogRenderer and UIOverlayRenderer

**MessageLogRenderer** (~150-200 lines):
- `render_message_log()` - Bottom panel with scrolling messages
- Message log uses game viewport width (27 chars)

**UIOverlayRenderer** (~300-350 lines):
- `render_help_screen()` - Hotkey reference overlay
- `render_achievements_menu()` - Achievement list with scrolling
- `render_targeting_cursor()` - Enemy targeting visual

**Integration points:**
- Both renderers called by `game_rendering_core.py`
- Help screen renders as full-screen overlay (blocks game view)
- Achievements menu renders as modal dialogue

**Testing approach:**
- Separate test files for each renderer
- Test message log scrolling and line wrapping
- Test help screen hotkey accuracy (must match actual keybindings)
- Test achievements menu scrolling

**Gotchas:**
- Help screen symbols in glyphs mode must exactly match game symbols
- Message log must handle Unicode symbols (rendered by TCOD, not logged)
- Achievements menu uses mouse scroll wheel (coordinate conversion)

### 2.5: Update game_rendering_ui.py as Facade

**Refactor** game_rendering_ui.py into thin facade (~100-150 lines)

**New structure:**
```python
class UIRenderer:
    def __init__(self):
        self.dialogue_renderer = DialogueRenderer()
        self.info_panel_renderer = InfoPanelRenderer()
        self.status_bar_renderer = StatusBarRenderer()
        self.message_log_renderer = MessageLogRenderer()
        self.overlay_renderer = UIOverlayRenderer()

    def render_ui(self, console: Console, game_engine: GameEngine) -> None:
        # Delegate to appropriate renderer
        self.status_bar_renderer.render(console, game_engine)
        self.message_log_renderer.render(console, game_engine)
        self.info_panel_renderer.render(console, game_engine)

        # Render overlays last (modal)
        if game_engine.dialogue_state.has_active():
            self.dialogue_renderer.render(console, game_engine)
```

**Integration checklist:**
- Update `game_rendering_core.py` imports
- Verify rendering order: status bar → viewport → info panel → message log → overlays
- Test transparency and alpha channel handling
- Run full test suite

**Rollback point:** If rendering breaks, revert to monolithic game_rendering_ui.py

---

## Phase 3: game_entities.py Reorganization

### Current Structure Analysis

`game_entities.py` contains 10 disparate classes:

1. **ColorManager** - Color palette and utilities (already exists in `game_color_manager.py`!)
2. **Colors** - Static color constants
3. **EnemyState, EnemyMovement, TargetingMode** - Enums
4. **Position** - Core position class with distance calculations
5. **EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition** - Data classes
6. **PositionValidator** - Utility class

**Current dependencies:**
- Imported by: ~40 files across entire codebase
- Most imports are specific: `from game_entities import Position, EnemyState`

**Complexity:** STRAIGHTFORWARD
- Classes are largely independent
- Enums have no dependencies
- Main risk is circular imports (Position used everywhere)

### 3.1: Move ColorManager to game_color_manager.py

**Action:** Delete ColorManager from game_entities.py

**Rationale:**
- `game_color_manager.py` already exists and contains ColorManager
- Duplicate definition creates confusion
- Current imports already use `from game_color_manager import ColorManager`

**Integration steps:**
1. Verify no imports use `from game_entities import ColorManager`
2. Delete ColorManager class from game_entities.py
3. Delete Colors class if it's redundant with game_color_manager.py

**Testing approach:**
- Run `grep -r "from game_entities import.*ColorManager" --include="*.py"`
- If no matches, safe to delete
- Run full test suite

**Gotchas:**
- Check if Colors class is used separately from ColorManager
- Some tests might import from game_entities out of habit

### 3.2: Create game_state_enums.py

**Extract** all enum classes (~80-100 lines)

**Enums to extract:**
- `EnemyState` - IDLE, PATROL, ALERT, HOSTILE, DISABLED
- `EnemyMovement` - STATIONARY, PATROL, SEEK, HOSTILE
- `TargetingMode` - SINGLE, AREA, SELF, DIRECTION
- Plus any other enums in the file

**New module API:**
```python
# game_state_enums.py
from enum import Enum, auto

class EnemyState(Enum):
    IDLE = auto()
    PATROL = auto()
    # etc.
```

**Integration steps:**
1. Create `game_state_enums.py` with all enum definitions
2. Update imports: `from game_entities import EnemyState` → `from game_state_enums import EnemyState`
3. Update game_entities.py to import and re-export for backwards compatibility (temporary)

**Backwards compatibility shim:**
```python
# game_entities.py (temporary)
from game_state_enums import EnemyState, EnemyMovement, TargetingMode

# Re-export for backwards compatibility
__all__ = ['EnemyState', 'EnemyMovement', 'TargetingMode', 'Position', ...]
```

**Testing approach:**
- Run full test suite after extraction
- Gradually update imports across codebase (not required immediately)
- Remove shim in future release

**Gotchas:**
- Enums might be used in game_rules.json validation
- Check if pickle/serialization depends on enum module location

### 3.3: Create game_position.py

**Extract** Position class and PositionValidator (~200-250 lines)

**Responsibilities:**
- Position class with x, y coordinates
- Distance calculations: `distance_to()`, `grid_distance_to()`
- Directional helpers: `direction_to()`, `neighbors()`
- PositionValidator: bounds checking, wall checking

**New module API:**
```python
class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def distance_to(self, other: Position) -> float:
        # Euclidean distance for vision/spatial

    def grid_distance_to(self, other: Position) -> int:
        # Manhattan distance for gameplay mechanics
```

**Integration steps:**
1. Create `game_position.py` with Position and PositionValidator
2. Update imports across ~40 files
3. Keep backwards compatibility shim in game_entities.py (temporary)

**Testing approach:**
- Extract position tests to `test_position.py`
- Test distance calculations match original behavior exactly
- Test direction helpers (8-directional movement)
- Verify FOV and pathfinding still work

**Gotchas:**
- Position is used EVERYWHERE - high import count
- Distance calculations are critical for combat, FOV, pathfinding
- Check .claude/DISTANCE_GUIDE.md for correct usage patterns

### 3.4: Create game_definitions.py

**Extract** data definition classes (~150-200 lines)

**Classes to extract:**
- `EnemyTypeDefinition` - Enemy stats and behavior loaded from JSON
- `ExploitDefinition` - Exploit stats and effects from JSON
- `UpgradeDefinition` - Permanent upgrade data from JSON

**New module API:**
```python
@dataclass
class EnemyTypeDefinition:
    type: str
    name: str
    glyph: str
    color: Tuple[int, int, int]
    cpu: int
    damage: int
    vision_range: int
    # etc.
```

**Integration steps:**
1. Create `game_definitions.py` with all data classes
2. Update imports in config loading code
3. Keep backwards compatibility shim in game_entities.py

**Testing approach:**
- Test JSON loading still works (game_content.json)
- Test definition validation (required fields present)
- Verify enemy/exploit creation uses correct definitions

**Gotchas:**
- Definitions are loaded at startup (game_config.py)
- Check if any serialization/deserialization depends on module location
- Dataclass field ordering might matter for unpacking

### 3.5: Update game_entities.py to Minimal Core

**Final state** (~100-150 lines)

**Remaining in game_entities.py:**
- Player class (if present)
- Entity base class (if present)
- Factory functions for entity creation
- Backwards compatibility shims (temporary)

**Backwards compatibility shims:**
```python
# game_entities.py
# Re-export for backwards compatibility (remove in future release)
from game_state_enums import EnemyState, EnemyMovement, TargetingMode
from game_position import Position, PositionValidator
from game_definitions import EnemyTypeDefinition, ExploitDefinition, UpgradeDefinition

__all__ = [
    'EnemyState', 'EnemyMovement', 'TargetingMode',
    'Position', 'PositionValidator',
    'EnemyTypeDefinition', 'ExploitDefinition', 'UpgradeDefinition',
    # Plus actual classes still in this file
]
```

**Integration checklist:**
- Update all imports across codebase (can be gradual)
- Run full test suite after each module extraction
- Document new module structure in README_DEV.md
- Plan removal of shims in future release

**Rollback point:** Keep backwards compatibility shims indefinitely if removal causes issues

---

## Testing Strategy

### Continuous Testing

**After each extracted module:**
1. Run affected unit tests: `pytest tests/unit/test_<module>.py -v`
2. Run integration tests: `pytest tests/integration/ -v`
3. Run full test suite: `pytest tests/ -q --tb=no`
4. Check test count: should remain 2,042 (no lost tests)

### Integration Testing Checkpoints

**Phase 1 checkpoint:**
- Test turn processing: player moves, enemy turns, action sequences
- Test level transitions: state persistence, progression
- Test save/load: round-trip state preservation

**Phase 2 checkpoint:**
- Test rendering: no visual regressions
- Test UI interactions: mouse clicks, keyboard navigation
- Test transparency: dialogues, overlays render correctly

**Phase 3 checkpoint:**
- Test imports: all modules import successfully
- Test JSON loading: enemy/exploit definitions load correctly
- Test gameplay: combat, movement, FOV all function normally

### Rollback Strategy

**If tests fail at any phase:**
1. Identify failing test(s)
2. Debug extracted module in isolation
3. If unfixable, revert to previous working state
4. Keep old monolithic file alongside new modules temporarily
5. Gradually migrate functionality once issues resolved

**Git strategy:**
- One commit per extracted module (atomic changes)
- Tag before each phase: `v0.8.1-pre-phase1`, etc.
- Can revert individual commits if needed

---

## Success Criteria

### Functional Requirements

- ✓ All 2,042 tests pass (or more if new tests added)
- ✓ No visual rendering regressions
- ✓ Game plays identically to pre-refactor
- ✓ Save/load works correctly
- ✓ No performance degradation (>5% FPS drop)

### Code Quality Requirements

- ✓ All files <500 lines
- ✓ Each module has single clear responsibility
- ✓ Import graph has no circular dependencies
- ✓ Test coverage maintained or improved (currently 70%)

### Documentation Requirements

- ✓ Update README_DEV.md with new module structure
- ✓ Update architecture diagrams if they exist
- ✓ Add docstrings to new module files
- ✓ Document backwards compatibility shims and removal plan

---

## Risk Mitigation

### High-Risk Areas

**1. game_session.py split**
- Risk: Turn order corruption, state inconsistency
- Mitigation: Extract one coordinator at a time, test thoroughly between extractions
- Fallback: Keep GameSession as facade delegating to extracted classes

**2. Circular imports**
- Risk: Position used by everything, might create import cycles
- Mitigation: Use forward references `from __future__ import annotations`
- Fallback: Keep backwards compatibility shims in game_entities.py permanently

**3. Rendering coordinate system errors**
- Risk: Mixing console coords (80x50) with viewport coords (27x21)
- Mitigation: Use CoordinateHelpers consistently, add assertions
- Fallback: Keep monolithic game_rendering_ui.py if issues persist

### Low-Risk Areas

- Enum extraction: enums are independent, no dependencies
- Definition extraction: data classes with no logic
- ColorManager deletion: duplicate code removal

---

## Post-Refactor Tasks

### Immediate (Post-Phase 3)

1. Update .gitignore if any new patterns needed
2. Update build.bat if module structure matters for PyInstaller
3. Run full game playthrough manually (not just tests)
4. Check metrics/performance: FPS, memory usage, load times

### Future (Next Release)

1. Remove backwards compatibility shims from game_entities.py
2. Update all imports to use new module paths directly
3. Consider further splits if modules still >500 lines
4. Document refactoring in release notes

### Optional Improvements

1. Create architecture diagram showing new module relationships
2. Add type hints to extracted modules (if missing)
3. Improve test coverage for extracted modules
4. Refactor other large files (game_input.py, game_characters.py, game_menus.py)

---

## Appendix: File Size Targets

| Original File | Original Size | Target Files | Target Size Each |
|---------------|---------------|--------------|------------------|
| game_session.py | 1,603 lines | 4 files | ~400 lines |
| game_rendering_ui.py | 1,221 lines | 5 files | ~250 lines |
| game_entities.py | 820 lines | 4 files | ~200 lines |

**Total:** 3 files (3,644 lines) → 13 files (~300 lines each)

**Complexity ranking:**
1. game_session.py split - HIGH (tight coupling, state management)
2. game_rendering_ui.py split - MEDIUM (coordinate systems, rendering order)
3. game_entities.py reorganization - LOW (independent classes, clear boundaries)

**Estimated effort ranking:**
1. Phase 1 (game_session.py) - Most complex, expect multiple iterations
2. Phase 2 (game_rendering_ui.py) - Moderate complexity, rendering testing needed
3. Phase 3 (game_entities.py) - Straightforward, mostly mechanical

**Dependencies:**
- Phase 2 depends on Phase 1 (GameSession is major consumer of rendering)
- Phase 3 depends on Phases 1 & 2 (entities used by all systems)
- Each phase should be completed and tested before starting next

**Timeline note:** Per PLANNING_GUIDE.md, no time estimates provided. Focus on correctness and testing at each step rather than rushing to completion.
