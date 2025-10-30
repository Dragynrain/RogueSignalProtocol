# Info Panel & Achievement Popup System Implementation Plan

## Summary of Recent Changes (Already Committed)

**Commit**: `fc1bfce` - "Add comprehensive metrics tracking system and fix 6 pre-existing test failures"

**New Files**:
- `game_metrics.py` (486 lines) - Dual-storage metrics system (JSON + SQLite)
- `tests/unit/test_metrics.py` (281 lines) - 10 comprehensive tests

**Modified Files**:
- Test fixes: `test_menu_interactions.py`, `test_map.py`, `test_save_load_mid_gameplay.py`
- Metrics hooks: `game_engine.py`, `game_session.py`, `game_characters.py`, `game_state.py`, `game_combat.py`, `game_inventory.py`
- Save integration: `game_save.py`
- Config: `.gitignore` (added `metrics/`)

**Metrics Tracked**: 45+ metrics across combat, exploration, items, streaks, efficiency, environmental, challenges, mastery, and peak performance.

**Test Results**: All 6 pre-existing failures fixed, 1401/1401 tests passing (excluding 1 unrelated flaky test)

---

## 🎯 Info Panel Implementation Plan

### Phase 1: Persistent Info Panel (Top-Right)

**Goal**: Replace current help text area with dedicated info panel showing context-aware information.

**Location**: Top-right corner, above system log
- **Position**: x=55-79, y=0-10 (11 lines total)
- **Width**: 25 characters (matches log panel)
- **Layout**:
  ```
  ╔═══ CONTEXT INFO ═══╗  y=0-1  (header)
  ║ Enemy: Scanner     ║  y=2   (entity name)
  ║ CPU: 45/45  DMG:15 ║  y=3-4 (stats)
  ║ State: Patrolling  ║  y=5
  ║ Range: 8  Vis: 10  ║  y=6
  ║                    ║  y=7
  ║ Next moves:        ║  y=8
  ║  → ↓ ← (queue)     ║  y=9
  ╚════════════════════╝  y=10  (border)

  [System log starts at y=11 instead of y=3]
  ```

**What to Show**:
1. **Default (no hover)**: Current turn info
   - Turn counter
   - Time elapsed
   - Current streak (if any)

2. **Hovering enemy**:
   - Name + type symbol
   - CPU/DMG/Vision/Range stats
   - State (Patrolling/Alert/Hostile)
   - Movement queue preview (3 arrows)
   - Distance from player

3. **Hovering exploit (in bar)**:
   - Name + hotkey
   - RAM cost, Heat cost, Damage
   - Range, Effect
   - Full description (wrapped)

4. **Hovering code hack/pickup**:
   - **UNDISCOVERED**: Show name only (e.g., "Code Fragment [??]")
   - **DISCOVERED**: Show name, type, and full effect description
   - **Note**: Code hacks don't reveal their ability until used once (check `item.discovered` property)

5. **Hovering special node**:
   - Node type (Gateway, Upgrade, Story)
   - Activation requirements
   - Effect preview

**Files to Create**:
- `game_info_panel.py` - New module for info panel logic

**Files to Modify**:
1. `game_rendering_ui.py`:
   - Add `render_info_panel()` method
   - Move help text to bottom panel or remove it
   - Adjust `render_system_log()` to start at y=11

2. `game_rendering_core.py`:
   - Call `render_info_panel()` before system log
   - Ensure alpha channel is set to 255 for panel region

3. `game_inspection.py`:
   - Extract reusable methods for entity data
   - Create `InfoProvider` class for formatting info

4. `game_config.py`:
   - Add `INFO_PANEL_HEIGHT = 11`
   - Update `LOG_START_Y = INFO_PANEL_HEIGHT`

**Implementation Steps**:
1. Create `InfoProvider` class to gather entity/item data
2. Create `InfoPanelRenderer` class with formatting logic
3. Integrate into main render loop
4. Test with enemies, exploits, items, nodes
5. Handle edge cases (no hover, invalid positions)
6. **Respect code hack discovery state** (check `item.discovered` before showing effect)

---

### Phase 2: Remove "X to View" - Enable Hover Everywhere

**Goal**: Make hover work for all interactive elements, remove keyboard prompts.

**Elements to Enable Hover**:
1. ✅ **Exploit bar** (already has hover highlighting)
   - Enhance to show full details in info panel

2. ✅ **Inventory items** (already has tooltips)
   - Move tooltip content to info panel
   - Remove bottom-right tooltip rendering
   - **Code hacks**: Only show effect if `item.discovered == True`

3. **NEW: Enemies in viewport**
   - Detect mouse hover over enemy sprites/glyphs
   - Show enemy details in info panel

4. **NEW: Items in viewport**
   - Detect hover over code hacks, exploits, upgrades
   - Show item details in info panel
   - **Code hacks on ground**: Show "???" for undiscovered effects

5. **NEW: Special nodes**
   - Detect hover over gateways, upgrade nodes, story fragments
   - Show node info in info panel

**Mouse Detection Pattern**:
```python
# In InfoProvider class
def get_hovered_entity(game, mouse_x, mouse_y):
    # Priority order:
    # 1. UI elements (exploit bar, inventory)
    # 2. Enemies at position
    # 3. Items at position
    # 4. Special nodes at position
    # 5. Terrain info (shadow, door, etc.)

    # Reuse EntityInspector.get_entity_at_position()
    # Add item/node detection

def format_code_hack_info(code_hack):
    # Check code_hack.discovered property
    if not code_hack.discovered:
        return f"{code_hack.name}\n[Effect: ???]"
    else:
        return f"{code_hack.name}\n{code_hack.description}"
```

**Files to Modify**:
1. `game_rendering_ui.py`:
   - Remove "Press X to view exploit" text
   - Remove tooltip rendering from inventory
   - Use info panel for all hover details

2. `game_info_panel.py`:
   - Add methods for each entity type
   - Format output for 25-char width
   - **Add `format_code_hack()` with discovery check**

3. `game_inspection.py`:
   - Make `get_entity_at_position()` public
   - Add `get_item_at_position()`
   - Add `get_node_at_position()`

---

### Phase 3: Achievement Popup System

**Goal**: Small, unobtrusive popups for achievement notifications using adapted dialogue system.

**Design**:
```
     ╔═══════════════════════════════╗
     ║  🏆 ACHIEVEMENT UNLOCKED!    ║  Small centered box
     ║  Silent Assassin             ║  30x6 chars
     ║  10 stealth kills in one run ║  (vs 70x14 for dialogues)
     ╚═══════════════════════════════╝

     [Fades after 3 seconds or press any key]
```

**Architecture**:

1. **AchievementPopup** (dataclass):
   ```python
   @dataclass
   class AchievementPopup:
       title: str          # "ACHIEVEMENT UNLOCKED!"
       achievement: str    # "Silent Assassin"
       description: str    # "10 stealth kills"
       icon: str          # "🏆" or game symbol
       duration: float    # 3.0 seconds
       timestamp: float   # when shown
   ```

2. **AchievementManager** (new module):
   ```python
   class AchievementManager:
       def check_achievements(metrics: SessionMetrics) -> List[str]:
           """Check if any achievements were earned."""

       def show_achievement(achievement_id: str):
           """Queue achievement popup."""

       def has_active_popup() -> bool:
           """Check if popup is showing."""
   ```

3. **PopupRenderer** (small dialogue variant):
   ```python
   class PopupRenderer:
       @staticmethod
       def render_achievement_popup(console, popup):
           box_width = 32
           box_height = 6
           # Center on screen
           # Quick fade-in/fade-out animation (optional)
           # Auto-dismiss after duration
   ```

**When to Check Achievements**:
1. **End of turn** - Check streak achievements
2. **End of level** - Check completion achievements
3. **Session end** - Check run completion achievements
4. **Lifetime** - Check meta achievements (tracked in rogue_signal_progress.json)

**Achievement Examples**:
```python
ACHIEVEMENTS = {
    "silent_assassin": {
        "name": "Silent Assassin",
        "desc": "Kill 10 enemies without being detected",
        "check": lambda m: m.max_stealth_streak >= 10,
        "icon": "🔪"
    },
    "ghost_protocol": {
        "name": "Ghost Protocol",
        "desc": "Complete a level without being detected",
        "check": lambda m: m.victory and not m.ever_detected,
        "icon": "👻"
    },
    "untouchable": {
        "name": "Untouchable",
        "desc": "Win without taking damage",
        "check": lambda m: m.victory and not m.took_any_damage,
        "icon": "🛡️"
    },
    "heat_master": {
        "name": "Heat Master",
        "desc": "Win while staying under 50 heat",
        "check": lambda m: m.victory and m.highest_heat_reached < 50,
        "icon": "🔥"
    },
    "speedrunner": {
        "name": "Speedrunner",
        "desc": "Win in under 100 turns",
        "check": lambda m: m.victory and m.turns_taken < 100,
        "icon": "⚡"
    },
    "crowd_control": {
        "name": "Crowd Control",
        "desc": "Hit 5+ enemies with one AOE",
        "check": lambda m: max(m.aoe_multi_kills.values(), default=0) >= 5,
        "icon": "💥"
    },
    "master_hacker": {
        "name": "Master Hacker",
        "desc": "Use all exploits in one run",
        "check": lambda m: len(m.unique_exploits_used_this_run) >= TOTAL_EXPLOITS,
        "icon": "🧠"
    },
    "code_collector": {
        "name": "Code Collector",
        "desc": "Use all code hacks in one run",
        "check": lambda m: len(m.unique_code_hacks_used_this_run) >= TOTAL_CODE_HACKS,
        "icon": "📦"
    }
}
```

**Files to Create**:
- `game_achievements.py` - Achievement definitions and checking logic
- `game_achievement_popups.py` - Popup rendering and queue management

**Files to Modify**:
1. `game_metrics.py`:
   - Add hook for achievement checking after finalizing session

2. `game_rendering_core.py`:
   - Render achievement popups (highest z-order)

3. `game_state.py`:
   - Add achievement popup queue to GameState

4. `rogue_signal_progress.json`:
   - Add "unlocked_achievements" list for lifetime tracking

**Integration with Metrics**:
```python
# In game_session.py, after finalize_session()
if metrics:
    save_metrics(metrics)

    # Check for achievements
    from game_achievements import AchievementManager
    unlocked = AchievementManager.check_achievements(metrics)
    for achievement_id in unlocked:
        AchievementManager.show_achievement(achievement_id)
```

---

## Current UI Research Summary

### Screen Layout (80x50 Console)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [0,0] Status Bar (CPU/Heat/Trace/RAM)          Help text (right-aligned)   │ y=0
├──────────────────────────────────────┬──────────────────────────────────────┤
│                                      │║  SYSTEM LOG                         │
│                                      │║═══════════════                      │
│                                      │║                                     │
│    GAME VIEWPORT                     │║  Message 1...                       │
│    (x: 0-54, y: 1-44)               │║  Message 2...                       │ y=1-44
│    27x21 tiles in graphics mode      │║  ...                                │
│    55x44 tiles in glyph mode         │║                                     │
│                                      │║  (or Inspection Panel               │
│                                      │║   when in look mode)                │
├──────────────────────────────────────┴──────────────────────────────────────┤
│ ╔══════════════════════════════════════════════════════════════════════════╗│ y=45-49
│ ║ Exploits: 1.BufferOverflow  2.CodeInjection  3.ShadowStep               ║│
│ ║           4.DataMimic  5.LogWiper                                        ║│
│ ║ Conditions: Speed Boost(3)  Threat Scan(5)                               ║│
│ ╚══════════════════════════════════════════════════════════════════════════╝│
└─────────────────────────────────────────────────────────────────────────────┘
```

**NEW Layout with Info Panel**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [0,0] Status Bar (CPU/Heat/Trace/RAM)                                      │ y=0
├──────────────────────────────────────┬──────────────────────────────────────┤
│                                      │╔═══ CONTEXT INFO ═══╗               │ y=1-10
│                                      │║ Enemy: Scanner     ║               │ (NEW!)
│                                      │║ CPU: 45  DMG: 15   ║               │
│    GAME VIEWPORT                     │║ State: Patrolling  ║               │
│    (x: 0-54, y: 1-44)               │║ Range: 8  Vis: 10  ║               │
│                                      │║ Next: → ↓ ←        ║               │
│                                      │╚════════════════════╝               │
│                                      │                                      │
│                                      │║  SYSTEM LOG                         │ y=11-44
│                                      │║═══════════════                      │ (moved down)
│                                      │║  Message 1...                       │
├──────────────────────────────────────┴──────────────────────────────────────┤
│ ╔══════════════════════════════════════════════════════════════════════════╗│
│ ║ Exploits: 1.BufferOverflow  2.CodeInjection  3.ShadowStep               ║│
│ ║ Conditions: Speed Boost(3)  [Help: Mouse hover for info]                ║│
│ ╚══════════════════════════════════════════════════════════════════════════╝│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Constants
- `SCREEN_WIDTH = 80`
- `SCREEN_HEIGHT = 50`
- `LOG_WIDTH = 25`
- `GAME_AREA_WIDTH = 55` (80 - 25)
- `INFO_PANEL_HEIGHT = 11` (NEW)
- `LOG_START_Y = 11` (NEW, was 3)

### Existing Systems to Leverage

1. **Mouse Tracking** (already working):
   - `game.last_mouse_tile_x` / `game.last_mouse_tile_y`
   - Updated in event loop automatically

2. **Entity Detection** (reuse existing):
   - `EntityInspector.get_entity_at_position()` (from `game_inspection.py`)
   - Already used for look mode

3. **Transparency Management** (CRITICAL for graphics mode):
   ```python
   # Set info panel opaque
   CoordinateHelpers.set_alpha_region(console,
       x=55, y=0, width=25, height=11, alpha=255)
   ```

4. **Dialogue System** (adapt for popups):
   - `UnifiedRenderer.render()` handles centering and transparency
   - `DialogueState` manages queue and priorities
   - Can create smaller variant for achievement popups

---

## File Structure

**New Files**:
```
game_info_panel.py          # InfoProvider + InfoPanelRenderer classes
game_achievements.py        # Achievement definitions + checker
game_achievement_popups.py  # Popup rendering + queue
tests/unit/test_info_panel.py
tests/unit/test_achievements.py
tests/integration/test_achievement_popups.py
```

**Modified Files**:
```
game_rendering_ui.py        # Add info panel, move help text
game_rendering_core.py      # Call info panel + popups
game_inspection.py          # Extract reusable entity data methods
game_config.py              # Add INFO_PANEL_HEIGHT constant
game_metrics.py             # Add achievement checking hook
game_state.py               # Add popup queue
rogue_signal_progress.json  # Add achievement tracking
```

---

## Implementation Phases

### Phase 1: Info Panel (Priority 1)
1. Create `InfoProvider` class with entity data extraction
2. Create `InfoPanelRenderer` class with formatting
3. Integrate into render loop
4. Test with all entity types (enemies, exploits, code hacks, nodes)
5. **Handle code hack discovery state** (undiscovered = "???" effect)
6. Remove old help text from status bar

**Estimated Lines**: ~300 lines

**Key Implementation Details**:
```python
class InfoProvider:
    @staticmethod
    def format_code_hack(code_hack):
        """Format code hack info, respecting discovery state."""
        if not code_hack.discovered:
            return {
                'name': code_hack.name,
                'type': 'Code Fragment',
                'effect': '???',
                'hint': '(Use to discover effect)'
            }
        else:
            return {
                'name': code_hack.name,
                'type': code_hack.color_name.title(),
                'effect': code_hack.description,
                'quantity': code_hack.quantity
            }
```

### Phase 2: Enhanced Hover (Priority 2)
1. Add enemy hover detection in viewport
2. Add item hover detection in viewport
3. Remove "X to view" prompts from exploit bar
4. Move inventory tooltips to info panel
5. Test mouse detection accuracy
6. **Ensure code hacks on ground show "???" until picked up**

**Estimated Lines**: ~150 lines (mostly modifications)

### Phase 3: Achievement Popups (Priority 3)
1. Define achievement list (20-30 achievements)
2. Create popup rendering system (small dialogue variant)
3. Integrate with metrics finalization
4. Add lifetime achievement tracking to progress.json
5. Test popup triggering, display, and auto-dismiss
6. Add sound effects for achievement unlock (optional)

**Estimated Lines**: ~400 lines

---

## Testing Strategy

1. **Unit Tests**:
   - `test_info_panel.py`:
     - InfoProvider data extraction for all entity types
     - Code hack discovery state handling
     - Text wrapping for 25-char width

   - `test_achievements.py`:
     - Achievement condition checking
     - Unlock detection logic
     - Lifetime achievement persistence

2. **Integration Tests**:
   - `test_info_panel_integration.py`:
     - Hover detection for all entity types
     - Info panel rendering at different mouse positions
     - Panel visibility with/without hover

   - `test_achievement_popups.py`:
     - Achievement unlocking scenarios
     - Popup display and auto-dismiss
     - Queue management (multiple achievements)

3. **Manual Testing**:
   - Hover responsiveness in both graphics and glyph modes
   - Info panel readability and text wrapping
   - Achievement popup timing and dismissal
   - Edge cases (multiple entities at same position, panel overflow)
   - **Code hack reveal mechanic** (before/after first use)

---

## Total Estimated Effort

- **Code**: ~850 lines new + ~200 lines modified
- **Tests**: ~400 lines
- **Time**: 3-4 hours for full implementation + testing
- **Phases**: Can be implemented incrementally (1 → 2 → 3)

---

## Benefits

✅ **Better UX**: No need to press X, instant info on hover
✅ **More screen space**: Help text removed, log space optimized
✅ **Achievement system**: Proper tracking + satisfying popups
✅ **Consistent UI**: Everything uses same info panel pattern
✅ **Extensible**: Easy to add new entity types or achievements
✅ **Preserves mystery**: Code hacks maintain discovery mechanic

---

## Important Implementation Notes

### Code Hack Discovery Mechanic
**CRITICAL**: Code hacks should NOT reveal their effect until used once.

**Current Implementation** (from `game_inventory.py`):
```python
class CodeHack:
    def __init__(self, name, color_name, effect):
        self.name = name
        self.color_name = color_name
        self.effect = effect  # Internal effect ID
        self.description = "???"  # Unknown until first use
        self.discovered = False  # Flag to check
```

**Usage Pattern**:
```python
def use(self, player, game):
    if not self.discovered:
        # First use - reveal the effect
        description = get_description_from_effect(self.effect)
        self.discovered = True
        self.description = description
        game.message_log.add_message(f"Used {self.name} ({description})")

    return self._apply_effect(self.effect, player, game)
```

**Info Panel Integration**:
- Check `code_hack.discovered` before showing effect
- Show "???" or similar placeholder for undiscovered hacks
- Update info panel when hack is discovered (will auto-update on next hover)

### Transparency Management (Graphics Mode)
Remember to set alpha channel to 255 for the info panel region:
```python
# After rendering info panel
CoordinateHelpers.set_alpha_region(console,
    x=55, y=0, width=25, height=11, alpha=255)
```

### Z-Order (Rendering Priority)
```
1. Map/Sprites (background)
2. Status effects overlays
3. UI panels (status bar, message log, bottom panel, info panel)
4. Achievement popups (mid-priority)
5. Dialogue system (highest priority, modal)
```

---

## Future Enhancements (Post-Implementation)

1. **Animated info panel transitions** (fade in/out on hover)
2. **Achievement progress bars** (e.g., "Silent Assassin: 7/10 stealth kills")
3. **Achievement rarity indicators** (common/rare/epic)
4. **Steam/platform achievement integration** (if applicable)
5. **Achievement viewing menu** (see all unlocked/locked achievements)
6. **Sound effects for achievement unlocks** (satisfying audio feedback)
7. **Info panel customization** (user can toggle position/size)
