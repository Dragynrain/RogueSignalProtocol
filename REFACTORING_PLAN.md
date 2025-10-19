# Refactoring Plan - Rogue Signal Protocol
**Date**: 2025-10-18
**Analysis Version**: 1.0
**Status**: IN PROGRESS

---

## Context for Implementation

**Key Principles (from CLAUDE.md):**
- KISS - Keep it simple, prefer functional over complex OOP
- Fail fast - No hardcoded fallbacks, raise errors if config missing
- ASCII only - No Unicode
- Test after every phase - Run `.venv/Scripts/python.exe -m pytest tests/ -v --tb=short`
- No time estimates - Focus on tasks, not predictions
- No performance concerns - Until it actually affects user experience
- Add JSON config liberally - If you see hardcoded values, move them to JSON!

**Important Files:**
- `game_rules.json` - Main config file (colors, gameplay, rendering constants)
- `game_content.json` - Game data (enemies, exploits, items)
- `story_content.json` - Story fragments
- `user_settings.json` - User preferences (only file that can have defaults)

**Test Command:**
```bash
.venv/Scripts/python.exe -m pytest tests/ -v --tb=short
```

**Current Test Status:** ✅ 874/874 tests passing (baseline established)

---

## Executive Summary

Comprehensive architectural analysis identified **9 significant issues** requiring systematic refactoring:
- **5 HIGH severity**: Hardcoded values, DataLoader coupling, coordinate confusion, color duplication, file sizes
- **4 MEDIUM severity**: Inconsistent object passing, TileManager concerns mixing, rendering duplication, Settings coupling
- **3 LOW severity**: Naming conventions, code organization, test structure

**Overall Code Health**: 7.5/10 (Good architecture, needs refinement)

**Approach**: Phased refactoring over 3 phases, with full test suite validation after each change.

---

## Phase 1: Foundation & Configuration Management

**Goal**: Centralize configuration and color management, eliminate duplication

### Task 1.1: Create ColorManager Service
**Priority**: CRITICAL
**Impact**: 19 files affected

**Implementation**:
```python
# New file: game_color_manager.py

class ColorManager:
    """Centralized color management with lazy loading.

    CRITICAL: No fallback colors! If a color is missing from config, raises KeyError.
    This ensures config errors are caught immediately rather than hidden.
    """
    _config = None
    _colors = None

    @classmethod
    def _ensure_loaded(cls):
        """Load colors from config once."""
        if cls._colors is None:
            from data_loading import DataLoader
            cls._config = DataLoader.load_config()

            # Fail fast if colors section missing
            if "colors" not in cls._config:
                raise KeyError("CRITICAL CONFIG ERROR: Missing 'colors' section in game_rules.json")

            cls._colors = cls._config["colors"]

    @classmethod
    def get(cls, category: str, key: str) -> tuple:
        """
        Get color from config. NO FALLBACKS - raises KeyError if missing.

        Args:
            category: Color category (e.g., "exploits", "graphics_tint", "enemy_states")
            key: Specific color key within category

        Returns:
            tuple: RGB color tuple (r, g, b)

        Raises:
            KeyError: If category or key not found in config (by design - no silent failures)
        """
        cls._ensure_loaded()

        if category not in cls._colors:
            raise KeyError(
                f"CRITICAL CONFIG ERROR: Missing color category '{category}' in game_rules.json. "
                f"Available categories: {list(cls._colors.keys())}"
            )

        category_colors = cls._colors[category]
        if key not in category_colors:
            raise KeyError(
                f"CRITICAL CONFIG ERROR: Missing color '{key}' in category '{category}'. "
                f"Available keys: {list(category_colors.keys())}"
            )

        return ensure_color_tuple(category_colors[key])

    @classmethod
    def get_exploit_color(cls, exploit_type: str) -> tuple:
        """Get exploit-specific color. Raises KeyError if not in config."""
        return cls.get("exploits", exploit_type)

    @classmethod
    def get_tint_color(cls, tint_type: str) -> tuple:
        """Get graphics tint color. Raises KeyError if not in config."""
        return cls.get("graphics_tint", tint_type)

    @classmethod
    def get_enemy_state_color(cls, state: str) -> tuple:
        """Get enemy state color. Raises KeyError if not in config."""
        return cls.get("enemy_states", state)
```

**Files to Update**:
1. `game_rendering_graphics.py` - Replace 11 color loading calls
2. `game_rendering_glyphs.py` - Replace 10 color loading calls
3. `game_menu_help_graphics.py` - Replace 1 color loading call
4. Plus 6 other files with DataLoader.load_config() for colors

**Testing**:
- Verify all colors load correctly
- Test with missing color keys (should raise KeyError with helpful message)
- Add test to verify error messages show available options
- Run full test suite
- **IMPORTANT**: This will likely expose missing colors in JSON - fix them in game_rules.json!

---

### Task 1.2: Extract Rendering Constants to JSON
**Priority**: HIGH
**Impact**: 5 files + 1 JSON file

**Add to `game_config.json`**:
```json
{
  "rendering": {
    "status_bar_height": 1,
    "vision_bracket_size": 4,
    "status_outline_thickness": 2,
    "enemy_outline_thickness": 1,
    "min_tile_width": 8,
    "min_tile_height": 8,
    "fallback_tile_width": 10,
    "fallback_tile_height": 16
  }
}
```

**Update `game_config.py`** to expose:
```python
@staticmethod
def STATUS_BAR_HEIGHT():
    config = DataLoader.load_config()
    return config.get("rendering", {}).get("status_bar_height", 1)

@staticmethod
def VISION_BRACKET_SIZE():
    config = DataLoader.load_config()
    return config.get("rendering", {}).get("vision_bracket_size", 4)
```

**Files to Update**:
1. `game_rendering_graphics.py:54` - Replace `+ 1` with `GameConfig.STATUS_BAR_HEIGHT()`
2. `game_rendering_graphics.py:722` - Replace `bracket_size=4` with `GameConfig.VISION_BRACKET_SIZE()`
3. `game_rendering_glyphs.py:62` - Replace `+ 1` with `GameConfig.STATUS_BAR_HEIGHT()`
4. `game_rendering_glyphs.py:439` - Replace `bracket_size=4` with `GameConfig.VISION_BRACKET_SIZE()`
5. `game_config.py:175-190` - Use JSON values instead of hardcoded

**Testing**:
- Verify rendering looks identical
- Test with different config values
- Run visual regression checks

---

### Task 1.3: Document Coordinate Systems
**Priority**: HIGH
**Impact**: 2 files + README

**Add to `game_rendering_base.py`**:
```python
"""
COORDINATE SYSTEMS USED IN THIS CODEBASE:

1. CONSOLE COORDINATES (80x50 grid)
   - Used for: Text rendering, UI layout, menu positioning
   - Range: X: 0-79, Y: 0-49
   - Characters rendered at 10x16 pixels (tileset size)
   - Example: render_char_safe(console, 10, 5, "text")

2. GAME VIEWPORT COORDINATES (27x21 tiles in graphics mode)
   - Used for: Game map tile positions during gameplay
   - Calculated by: GameConfig.VIEWPORT_WIDTH/HEIGHT(graphics_mode)
   - Scaled to fit window using TileManager.tile_width/height
   - Example: viewport_x, viewport_y from camera position

3. SDL PIXEL COORDINATES (window resolution, e.g., 2560x1351)
   - Used for: Direct SDL sprite rendering
   - Full window pixel space
   - Example: SDL_Rect(pixel_x, pixel_y, sprite_w, sprite_h)

CONVERSION METHODS:
- _world_to_console(): World tile -> Console position
- _grid_to_pixel(): Game viewport -> SDL pixels (in-game)
- _console_to_pixel(): Console grid -> SDL pixels (menus)
- _is_in_viewport(): Check if world position is visible

CRITICAL RULES:
1. Menu rendering: Use console coords (80x50) + window scaling
2. Game rendering: Use viewport coords + TileManager dimensions
3. NEVER mix the two - they use different math!
"""
```

**Add inline comments** at critical conversion points:
- `game_rendering_base.py:41-61` - Document _world_to_console
- `game_rendering_base.py:118-134` - Document _grid_to_pixel
- `game_menu_help_graphics.py:381-424` - Document menu-specific conversions

**Testing**:
- Code review for clarity
- Verify documentation matches implementation

---

## Phase 2: Rendering Consolidation

**Goal**: Eliminate rendering duplication, fix coordinate inconsistencies

### Task 2.1: Consolidate Sprite Positioning Logic
**Priority**: HIGH
**Impact**: 3 files

**Problem**: Menu sprite positioning uses different math than in-game rendering

**Solution**: Extract common positioning to base class

**Update `game_rendering_base.py`**:
```python
def _console_to_pixels(self, console_x: int, console_y: int) -> tuple:
    """
    Convert console coordinates to pixel coordinates.
    Used for menu rendering where sprites must align with console text.
    """
    window_width, window_height = self._get_window_size()
    pixels_per_char_x = window_width / GameConfig.SCREEN_WIDTH
    pixels_per_char_y = window_height / GameConfig.SCREEN_HEIGHT

    pixel_x = int(console_x * pixels_per_char_x)
    pixel_y = int(console_y * pixels_per_char_y)

    return (pixel_x, pixel_y)

def _get_window_size(self) -> tuple:
    """Get current window dimensions with fallback."""
    try:
        if hasattr(self.context, 'sdl_window') and self.context.sdl_window:
            return self.context.sdl_window.size
    except (AttributeError, TypeError):
        pass
    return (800, 600)  # Fallback
```

**Update `game_menu_help_graphics.py`**:
```python
def _get_tile_rect(self, console_x: int, console_y: int, scale: float = 1.0):
    """Get sprite rect for menu rendering - uses base class conversion."""
    # Use base class for positioning
    pixel_x, pixel_y = self._console_to_pixels(console_x, console_y)

    # Use TileManager for size (same as in-game)
    sprite_width = int(self.tile_manager.tile_width * scale)
    sprite_height = int(self.tile_manager.tile_height * scale)

    return (pixel_x, pixel_y, sprite_width, sprite_height)
```

**Delete duplicate code**:
- Remove lines 409-418 from `game_menu_help_graphics.py` (now uses base class)

**Testing**:
- Visual verification: Help menu sprites same size as in-game
- Test multiple window resolutions
- Test both ASCII and graphics modes

---

### Task 2.2: Monitor File Sizes (No Action Needed)
**Priority**: LOW
**Impact**: Informational only

**Current Status**:
- `game_rendering_graphics.py` - 764 lines (42% of 1800 threshold)
- `game_rendering_glyphs.py` - 761 lines (42% of 1800 threshold)
- `game_menu_graphics_preview.py` - 886 lines (49% of 1800 threshold)

**Decision**: No splitting needed. These files are well under the threshold and splitting them now would add unnecessary complexity. Revisit if any file approaches 1500+ lines.

---

### Task 2.3: Extract DialogueRenderer
**Priority**: LOW
**Impact**: 2 files

**Extract from `game_rendering_core.py`**:

**New file**: `game_dialogue_renderer.py`
```python
class DialogueRenderer:
    """Handles all popup/dialogue rendering."""

    def render_victory_message(...):
        # Lines 170-195 from game_rendering_core.py
        pass

    def render_gateway_confirmation(...):
        # Lines 196-215 from game_rendering_core.py
        pass

    def render_dialogue(...):
        # Lines 216-265 from game_rendering_core.py
        pass

    def render_death_message(...):
        # Lines 311-338 from game_rendering_core.py
        pass
```

**Update `game_rendering_core.py`**:
```python
class GameRenderer:
    def __init__(self, ...):
        self.dialogue_renderer = DialogueRenderer(...)

    def render(...):
        # Delegate dialogue rendering
        if self.game_engine.show_victory_message:
            self.dialogue_renderer.render_victory_message(...)
```

**Testing**:
- Test all dialogue types appear correctly
- Run full test suite

---

## Phase 3: Architecture Improvements

**Goal**: Simplify initialization, reduce coupling

### Task 3.1: Implement GameEngineBuilder Pattern
**Priority**: MEDIUM
**Impact**: Many files, many tests

**New file**: `game_engine_builder.py`
```python
class GameEngineBuilder:
    """Builder pattern for GameEngine construction."""

    def __init__(self):
        self.settings = None
        self.load_save = False
        self._overrides = {}

    def with_settings(self, settings: GameSettings):
        """Set settings object."""
        self.settings = settings
        return self

    def with_save_loading(self):
        """Enable loading from save file."""
        self.load_save = True
        return self

    def with_component(self, name: str, component):
        """Override a specific component (for testing)."""
        self._overrides[name] = component
        return self

    def build(self) -> 'GameEngine':
        """Construct the GameEngine."""
        return GameEngine(self)
```

**Refactor `game_engine.py.__init__`**:
```python
def __init__(self, builder: GameEngineBuilder = None):
    """Initialize via builder pattern."""
    if builder is None:
        builder = GameEngineBuilder()

    self.settings = builder.settings or GameSettings()

    # Initialize in logical groups
    self._init_core_systems(builder)
    self._init_game_objects(builder)
    self._init_coordinators(builder)

    # Load save or start new
    if builder.load_save:
        self._load_save_data()
    else:
        self._start_new_game()

def _init_core_systems(self, builder):
    """Initialize core subsystems."""
    self.state_manager = builder._overrides.get('state_manager') or GameStateManager()
    self.sound_manager = builder._overrides.get('sound_manager') or SoundManager(self.settings)
    # ...

def _init_game_objects(self, builder):
    """Initialize game objects."""
    self.game_map = builder._overrides.get('game_map') or GameMap(...)
    self.player = builder._overrides.get('player') or None  # Created later
    # ...

def _init_coordinators(self, builder):
    """Initialize high-level coordinators."""
    self.turn_manager = GameTurnManager(self)
    self.level_coordinator = GameLevelCoordinator(self)
    # ...
```

**Update usage sites**:
```python
# Old way:
engine = GameEngine(settings=settings, load_save=True)

# New way:
engine = GameEngineBuilder().with_settings(settings).with_save_loading().build()
```

**Update tests**:
- Update all test files that create GameEngine
- Use builder pattern in fixtures
- Add builder-specific tests

**Testing**:
- Run FULL test suite
- Manual gameplay verification
- Test save/load functionality

---

### Task 3.2: Reduce Settings Object Coupling
**Priority**: LOW
**Impact**: 15+ files

**Analysis**: Most classes only need `graphics_mode`, not full Settings

**Strategy**: Pass only what's needed

**Before**:
```python
class TileManager:
    def __init__(self, context, settings):
        self.settings = settings
        self.graphics_mode = settings.graphics_mode
```

**After**:
```python
class TileManager:
    def __init__(self, context, graphics_mode: str):
        self.graphics_mode = graphics_mode
```

**Files to Update**:
1. `game_graphics_tiles.py` - TileManager signature
2. `game_rendering_core.py` - GameRenderer signature
3. `game_rendering_base.py` - MapRendererBase signature
4. `game_rendering_graphics.py` - GraphicsMapRenderer signature
5. `game_rendering_glyphs.py` - GlyphsMapRenderer signature
6. Plus callers of these classes

**Keep Settings Object For**:
- Menu classes that modify settings
- Classes that need multiple settings values

**Testing**:
- Verify all renderers work correctly
- Test mode switching
- Run full test suite

---

### Task 3.3: Refactor TileManager Dimension Calculation
**Priority**: LOW
**Impact**: 1 file

**Extract**: `game_tile_dimension_calculator.py`
```python
class TileDimensionCalculator:
    """Pure functions for tile dimension calculations."""

    @staticmethod
    def calculate_from_window(window_size: tuple, graphics_mode: str) -> tuple:
        """Calculate tile dimensions based on window size and mode."""
        width, height = window_size

        if graphics_mode == "graphics":
            return TileDimensionCalculator._calc_graphics_mode(width, height)
        else:
            return TileDimensionCalculator._calc_ascii_mode(width, height)

    @staticmethod
    def _calc_graphics_mode(width: int, height: int) -> tuple:
        """Calculate for graphics mode with viewport scaling."""
        viewport_w = GameConfig.VIEWPORT_WIDTH("graphics")
        viewport_h = GameConfig.VIEWPORT_HEIGHT("graphics")

        tile_w = width // viewport_w
        tile_h = height // viewport_h

        return TileDimensionCalculator.validate_and_clamp(tile_w, tile_h)

    @staticmethod
    def _calc_ascii_mode(width: int, height: int) -> tuple:
        """Calculate for ASCII mode."""
        # Use tileset character dimensions
        return (10, 16)  # Or from config

    @staticmethod
    def validate_and_clamp(width: int, height: int) -> tuple:
        """Ensure minimum tile sizes."""
        min_w = GameConfig.MIN_TILE_WIDTH()
        min_h = GameConfig.MIN_TILE_HEIGHT()
        return (max(min_w, width), max(min_h, height))
```

**Update `game_graphics_tiles.py`**:
```python
def _calculate_tile_dimensions(self, graphics_mode: str):
    """Calculate tile dimensions - delegates to calculator."""
    window_size = self._get_window_size()
    self.tile_width, self.tile_height = TileDimensionCalculator.calculate_from_window(
        window_size, graphics_mode
    )
```

**Testing**:
- Test multiple window sizes
- Test both graphics modes
- Verify minimum clamping works

---

## Phase 4: Final Cleanup & Validation

### Task 4.1: Extract BaseMenu and Split Menu Files
**Priority**: MEDIUM (upgraded - eliminates significant duplication)
**Impact**: 1 base class + 2 files split + ~100 lines duplication removed

**Problem**: MainMenu and SettingsMenu duplicate 5 methods each:
- `_has_background()` - duplicated
- `_get_menu_layout_params()` - duplicated
- `_calculate_background_aware_layout()` - duplicated (SettingsMenu only)
- `_clear_text_areas_only()` - duplicated
- `_render_right_side_box()` - duplicated (even though MenuRenderingUtils has this!)

**Files to Create**:

**1. `game_menu_base.py`** - Base class with shared functionality:
```python
class BaseMenu:
    """Base class for all menu screens with common functionality."""

    def __init__(self, background=None):
        self.background = background
        self.selected_option = 0
        self.options = []

    def _has_background(self) -> bool:
        """Check if background is available and should be displayed."""
        return (self.background and
                self.background.should_load_background() and
                self.background.background_texture)

    def _get_menu_layout_params(self) -> dict:
        """Calculate menu positioning based on graphics mode."""
        if self._has_background():
            return MenuRenderingUtils.calculate_background_aware_layout(self.background)
        else:
            return {
                'title_x': GameConfig.SCREEN_WIDTH // 2,
                'menu_x': GameConfig.SCREEN_WIDTH // 2,
                'use_background_layout': False,
                'layout_zone': 'center'
            }

    def _clear_text_areas_only(self, console):
        """Create separation between graphics and text areas."""
        layout = self._get_menu_layout_params()
        MenuRenderingUtils.clear_text_areas_only(console, layout)

    def _render_right_side_box(self, console, height, border_color, y_offset=0):
        """Render menu box using shared utilities."""
        layout = self._get_menu_layout_params()
        return MenuRenderingUtils.render_right_side_box(
            console, layout, height, border_color, y_offset
        )

    def render(self, console):
        """Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement render()")

    def handle_input(self, event):
        """Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement handle_input()")
```

**2. `game_menu_main.py`** - MainMenu extending BaseMenu:
```python
class MainMenu(BaseMenu):
    """Main menu for New Game/Continue options."""

    def __init__(self, background=None):
        super().__init__(background)
        self.refresh_options()
        self.show_warning = False
        self.warning_selection = 0
        self.mid_game_mode = False

    # ... rest of MainMenu implementation (no duplicated helper methods!)
```

**3. `game_menu_settings.py`** - SettingsMenu extending BaseMenu:
```python
class SettingsMenu(BaseMenu):
    """Settings menu for audio, graphics, and help options."""

    def __init__(self, settings, menu_background=None, sound_manager=None):
        super().__init__(menu_background)
        self.settings = settings
        self.sound_manager = sound_manager
        # ... setup options

    # ... rest of SettingsMenu implementation (no duplicated helper methods!)
```

**Files to Remove**:
- `game_menus.py` (split into above files)

**Update imports** in:
- Main game loop / entry point
- Test files

**Benefits**:
- Eliminates ~100 lines of duplicated code
- Future menus trivial to add (extend BaseMenu, implement 2 methods)
- Centralized menu behavior (backgrounds, layout, box rendering)
- Easier to add menu-wide features (fade effects, transitions, etc.)

**Testing**:
- Test all menus accessible
- Test navigation between menus
- Test background rendering in both modes
- Verify layout calculations work identically
- Run full test suite

---

### Task 4.2: Code Review & Documentation
**Priority**: HIGH

**Review**:
- All coordinate conversion methods have inline docs
- All new classes have docstrings
- README updated with architecture changes
- CLAUDE.md updated if needed

**Documentation to Add**:
1. Architecture diagram showing module relationships
2. Rendering pipeline documentation
3. Coordinate system examples
4. Color management usage guide

---

### Task 4.3: Full Integration Testing
**Priority**: CRITICAL

**Test Suite**:
```bash
# Run full suite with verbose output
.venv/Scripts/python.exe -m pytest tests/ -v --tb=short

# Run integration tests specifically
.venv/Scripts/python.exe -m pytest tests/integration/ -v

# Manual gameplay testing checklist:
# [ ] Start new game - ASCII mode
# [ ] Start new game - Graphics mode
# [ ] Switch between modes
# [ ] Save and load game
# [ ] Open all menus (main, settings, help, lore)
# [ ] Trigger all dialogues (victory, death, gateway)
# [ ] Render all sprite types
# [ ] Test multiple window resolutions
# [ ] Verify colors load correctly
```

**Visual Verification**:
- Verify menus look identical before/after
- Check coordinate systems working correctly
- Test sprite positioning in menus and game

---

## Implementation Guidelines

**Work through phases in order. After each phase:**
1. Run full test suite: `.venv/Scripts/python.exe -m pytest tests/ -v --tb=short`
2. Fix any broken tests
3. Check off completed tasks below
4. Git commits happen when you decide

That's it. Keep it simple.

---

## Task Status Tracker

### Phase 1: Foundation
- [x] Task 1.1: Create ColorManager Service
- [x] Task 1.2: Extract Rendering Constants to JSON
- [x] Task 1.3: Document Coordinate Systems

### Phase 2: Rendering Consolidation
- [ ] Task 2.1: Consolidate Sprite Positioning Logic
- [ ] Task 2.2: Monitor File Sizes (informational only - no action)
- [ ] Task 2.3: Extract DialogueRenderer

### Phase 3: Architecture Improvements
- [ ] Task 3.1: Implement GameEngineBuilder Pattern
- [ ] Task 3.2: Reduce Settings Object Coupling
- [ ] Task 3.3: Refactor TileManager Dimension Calculation

### Phase 4: Final Cleanup
- [ ] Task 4.1: Extract BaseMenu and Split Menu Files
- [ ] Task 4.2: Code Review & Documentation
- [ ] Task 4.3: Full Integration Testing

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tests break during refactoring | HIGH | HIGH | Run tests after every small change |
| Introduce new bugs | MEDIUM | HIGH | Thorough manual testing, integration tests |
| Coordinate system bugs | MEDIUM | CRITICAL | Extensive visual testing, multiple resolutions |
| Merge conflicts | LOW | MEDIUM | Work in small batches, merge frequently |
| Scope creep | MEDIUM | MEDIUM | Stick to plan, defer nice-to-haves |

---

## Success Metrics

**What Good Looks Like When We're Done**:
- [ ] All tests pass
- [ ] No visual regressions - game looks and plays identically
- [ ] Zero hardcoded rendering constants
- [ ] ColorManager used everywhere (no DataLoader for colors)
- [ ] Coordinate systems documented inline
- [ ] Menu duplication eliminated (~100 lines removed)
- [ ] Adding new colors is trivial (just edit JSON, no code changes)
- [ ] Adding new menus is trivial (extend BaseMenu, implement 2 methods)

---

## Notes & Open Questions

**Q**: Should we also refactor test files?
**A**: Yes, but only as needed to support main refactoring. Don't restructure test suite separately.

**Q**: Should we use type hints more extensively?
**A**: Yes, add them as we refactor, but don't make it a separate task.

**Q**: What about adding more JSON config options?
**A**: YES! If you see hardcoded values that should be configurable, add them to JSON. This is encouraged throughout the refactoring.

---

---

**END OF PLAN**
