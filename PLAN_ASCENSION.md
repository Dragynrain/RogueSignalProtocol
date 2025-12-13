# Ascension System Design for Rogue Signal Protocol

## Executive Summary

Progressive difficulty system modeled after Slay the Spire and Monster Train. Each successful escape unlocks progressively harder challenge modifiers. Players choose difficulty level (Ascension 0-20) before each run, with each level adding cumulative modifiers that increase challenge while providing goals for skilled players.

**Core Philosophy**: Progressive mastery challenges that reward skilled play while maintaining the game's core tension between stealth, combat, and resource management.

---

## Implementation Phases

### Phase 1: Core Modifier System (Medium Complexity)
Create ascension modifier definitions and calculation logic. No game integration yet.
- Complexity: Medium (new system architecture)
- Dependencies: None
- Risk: Low (isolated from existing code)

**Phase 1 Prerequisites** (must be done first):
- Move enemy spawn weights from hardcoded in `game_level_coordinator.py:558` to `game_rules.json` (enables A12 modifier)
- Lower base alert range from 8→6 in `game_rules.json` (enables A15 modifier to raise it to 10)

### Phase 2: Game Integration (High Complexity)
Apply modifiers to existing game systems (enemies, items, levels, combat).
- Complexity: High (touches many systems)
- Dependencies: Phase 1 complete
- Risk: Medium (potential for subtle bugs in existing systems)

### Phase 3: UI/Menu System (Medium Complexity)
Create ascension selection menu and integrate with main menu/victory screen.
- Complexity: Medium (new UI screens)
- Dependencies: Phase 1 complete (can parallel with Phase 2)
- Risk: Low (UI-only, no gameplay impact)

### Phase 4: Achievements & Metrics (Low Complexity)
Add ascension-specific achievements and tracking.
- Complexity: Low (extends existing achievement system)
- Dependencies: Phases 1-3 complete
- Risk: Low

### Phase 5: Testing & Balance (Medium-High Complexity)
Playtest all ascension levels, tune modifier values, verify integration.
- Complexity: Medium-High (requires extensive playtesting)
- Dependencies: All phases complete
- Risk: High (balance issues hard to predict)

---

## 1. System Overview

### What is Ascension?

- **Unlocked After**: First victory (escape to the internet)
- **Levels**: Ascension 0-20 (21 total levels)
- **Progression**: Each victory at Ascension N unlocks Ascension N+1
- **Selection**: Choose before each run via main menu
- **Persistence**: Stored in `user_settings.json` and `rogue_signal_progress.json`
- **Rewards**: Achievements for milestones (A5, A10, A15, A20)

### Why 20 Levels?

- Genre standard (Slay the Spire)
- Enough variation without overwhelming
- Allows 2-3 modifiers per level
- Natural milestone achievements

---

## 2. Ascension Modifiers (Cumulative)

All modifiers are **cumulative** - Ascension 10 includes all modifiers from A1-A10.

**Player-Facing Descriptions**: The in-game UI descriptions don't need exact numbers. Use approachable language:
- "All enemies have more health" instead of "+10 CPU"
- "Fewer blind spots on each floor" instead of "-1% coverage per floor"
- "Enemies see further" instead of "+1 vision range"
Keep it thematic and understandable - save the crunchy numbers for this design doc.

### Ascension 1: "Enhanced Monitoring"
Scanner vision: +1 tile (5→6)
**Design Note**: Scanners only. Stationary enemies = spatial puzzle. Gentle introduction.

### Ascension 2: "Hardened Processes"
All enemies: +10 CPU
**Effect**: Bot 25→35, Inhibitor 30→40, Scanner/Virus 35→45, Patrol 40→50, Hunter 50→60, Firewall 80→90
**Design Note**: Stealth one-shots fail on Scanner/Virus/Patrol. Exploits still work.

### Ascension 3: "Residual Signatures"
Background trace gain: x2 (1/2/3 → 2/4/6 per 25 turns)
**Design Note**: Passive trace pressure doubled. Rewards efficiency, punishes dawdling.

### Ascension 4: "Aggressive Protocols"
All enemy damage: +20% (truncate decimals)
**Effect**: Firewall 5→6, Bot 8→9 (9.6 truncated), Patrol 10→12, Hunter 15→18, Admin 45→54
**Design Note**: Every hit hurts more. Use `int(base * 1.2)` for all damage calculations.

### Ascension 5: "Wide-Spectrum Sensors"
All enemies: +1 vision (Scanner now +2 total)
**Effect**: Bot 3→4, Patrol 4→5, Virus 4→5, Hunter 6→7, Scanner 5→7
**Achievement**: "Sensor Sweep" (NOTE: "Ghost Protocol" already exists as stealth achievement)

### Ascension 6: "Shrinking Shadows"
Blind spot coverage: -1% per floor (8/7/6 → 7/6/5)
**Design Note**: Fewer hiding spots. Stealth routes tighten.

### Ascension 7: "Trace Persistence"
Continuous hostile trace: +0.2 flat (0.2/0.4/0.6 → 0.4/0.6/0.8)
**Design Note**: Getting spotted accumulates trace faster. Quick kills or clean escapes rewarded.

### Ascension 8: "Thermal Decay"
Heat reduction per turn: 2→1 (minimum 1)
**Design Note**: Passive cooling halved. Rely on nodes and careful play.

### Ascension 9: "Crowded Networks"
+5 enemies per floor (19/28/38 → 24/33/43)
**Design Note**: More threats. Higher density.

### Ascension 10: "Signal Fog"
Player vision range: 15→12 tiles
**Achievement**: "Firewall Breaker"
**Design Note**: Player vision 12 vs max enemy vision 7 (Hunter/Scanner at A5). Still advantage but tighter.

### Ascension 11: "Data Drought"
Data Codes: -2 per floor (min 3)
**Effect**: Floor 1: 12→10, Floor 2: 10→8, Floor 3: 5→3 (hits minimum)
**BALANCE NOTE**: Implement hard floor of minimum 3 codes per level to prevent unwinnable states.
**CLARIFICATION**: The minimum of 3 applies to each floor's RESULT after modification, not as an absolute floor. Formula: `max(3, base_codes - 2)`

### Ascension 12: "Threat Escalation"
Enemy spawn weights rebalanced toward tougher enemies:
| Enemy | Base | A12 | Change |
|-------|------|-----|--------|
| Scanner | 4 (25%) | 4 (15%) | Same count, lower % |
| Patrol | 3 (19%) | 5 (19%) | +2 weight |
| Bot | 2 (12.5%) | 4 (15%) | +2 weight |
| Firewall | 2 (12.5%) | 3 (11%) | +1 weight |
| Hunter | 2 (12.5%) | 4 (15%) | +2 weight |
| Inhibitor | 2 (12.5%) | 4 (15%) | +2 weight |
| Virus | 1 (6%) | 3 (11%) | +2 weight |
**Design Note**: More Hunters, more Viruses. Deadlier enemy mix.

### Ascension 13: "Degraded Infrastructure"
ALL restoration nodes (cooling, CPU, AND ghost) have hidden random capacity PER NODE and vanish when depleted.
- Floor 1: Each node has 100-200 capacity (at 20 per use = 5-10 uses each)
- Floor 2: Each node has 75-150 capacity (at 20 per use = ~4-7 uses each)
- Floor 3: Each node has 50-100 capacity (at 20 per use = ~2-5 uses each)
**Design Note**: Uncertainty in resource planning - that node might run dry mid-heal. Each node rolls its own capacity independently.
**CLARIFICATION - Fair Consumption**: Nodes only consume capacity equal to the ACTUAL benefit provided, not the maximum possible. Examples:
- Cooling node: Player at 15 heat, node offers 20 reduction → only 15 capacity consumed (reduces to 0)
- CPU node: Player at 95/100 CPU, node offers 20 recovery → only 5 capacity consumed (caps at 100)
- Ghost node: Player at 8% trace, node offers 20% reduction → only 8 capacity consumed (reduces to 0%)
This prevents penalizing players who use nodes efficiently.

### Ascension 14: "Memory Constraints"
Starting RAM: 8→6
**Design Note**: Tighter exploit budget. Can't equip everything you find.

### Ascension 15: "Network Cascade"
Enemy alert range: 6→10 tiles (A0-A14 use base of 6, A15+ raises to 10)
**Achievement**: "Silent Running"
**Design Note**: One hostile enemy cascades alerts across nearly half the map.
**PRE-REQUISITE**: Phase 1 lowers base alert range from 8→6. This affects ALL players (including A0) but makes base game slightly easier - intentional tradeoff to enable A15's dramatic increase.

### Ascension 16: "Exposed Topology"
Level generation favors wide open spaces with less cover:
- `room_generation.min_room_size`: 3→5
- `room_generation.max_room_size`: 7→10
- `room_generation.corridor_width_weights.wide`: 0.05→0.40 (5%→40%)
- `room_generation.corridor_alcove_chance`: 0.15→0.05
- `room_generation.cover_cluster_chance`: 0.50→0.25
**Design Note**: Bigger rooms, wider corridors, fewer hiding spots. Nowhere to run.

### Ascension 17: "Thermal Signature"
Melee/bump attacks generate +5 heat
**Design Note**: Combat has thermal cost. Can't bump-fight without risking overheat.
**BALANCE NOTE**: Combined with A8's slower cooling, needs careful testing.

### Ascension 18: "Streamlined Systems"
Permanent upgrades: -1 per floor (1/2/3 → 0/1/2, total 6→3)
**Design Note**: Halves permanent progression. Must be selective about upgrades.

### Ascension 19: "Failing Infrastructure"
Cooling nodes: -1 per floor, CPU nodes: -1 per floor (6/4/2 → 5/3/1)
**Design Note**: Floor 3 with only 1 of each is brutal - near-perfect play required.

### Ascension 20: "Decaying Shadows"
Blind spots disappear after you step on them (one-time use)
**Achievement**: "Ascension Master"
**Design Note**: The ultimate test. Every hiding spot consumed when used. No fallback positions.

---

## 3. Known Risk Points

These levels require extra playtesting attention:

| Level | Risk | Mitigation |
|-------|------|------------|
| A11 | Unwinnable if codes spawn too low | Hard floor: minimum 3 codes/level |
| A13 | Hidden node capacity feels arbitrary | Clear visual feedback when depleted |
| A15 | Alert cascade range may feel unfair | PRE-REQ: lower base from 8→6 first |
| A16 | Open maps + enemy density = exposure | Manual playtesting for feel |
| A17+A8 | Heat stacking may punish combat too hard | Combined testing required |
| A20 | Cumulative pain may be excessive | Target 3-8% win rate, not 1-5% |

---

## 4. Data Structure & Persistence

**Single Source of Truth**: All ascension state lives in `user_settings.json`. No duplication in `rogue_signal_progress.json` - avoids sync issues.

**Note**: Game only supports one save file at a time. No need to handle multi-save edge cases (backup file manipulation is unsupported).

### user_settings.json Addition
```json
"ascension": {
  "current_level": 5,
  "highest_unlocked": 5,
  "victories_per_level": {
    "0": 12,
    "5": 1
  }
}
```

The `rogue_signal_progress.json` does NOT duplicate this data - query from `user_settings.json` when needed.

---

## 5. Phase 1 Details: Core Modifier System

### New File: `game_ascension.py`

**Core Components**:
- `AscensionModifiers` dataclass: Stores modifier values for a single ascension level
- `calculate_ascension_modifiers(level: int) -> AscensionModifiers`: Cumulative calculation
- `apply_ascension_modifiers(base_config, modifiers)`: Modify game config values
- `is_ascension_unlocked(level, progress)`: Check unlock status
- `unlock_next_ascension(progress, current)`: Unlock progression

**Key Design Decisions**:
- Modifiers stored as deltas, not absolute values ("+1 vision" not "vision = 6")
- Cumulative calculation done once at game start, not per-turn
- No runtime modifier changes (set at initialization)

**IMPORTANT - Modifier Values in JSON**:
All ascension modifier values must be stored in `game_rules.json` under an `"ascension"` section, NOT hardcoded in Python. This allows balance tweaking without code changes.

Example structure in `game_rules.json`:
```json
"ascension": {
  "modifiers": {
    "1": {"scanner_vision_bonus": 1},
    "2": {"enemy_hp_bonus": 10},
    "3": {"trace_gain_multiplier": 2.0},
    "4": {"enemy_damage_multiplier": 1.2},
    "5": {"enemy_vision_bonus": 1},
    ...
  }
}
```

The Python code reads these values and applies them - it doesn't contain the numbers itself.

**Technical Considerations**:
- Must handle clamping (e.g., nodes never go below 0, codes never below 3)
- Must handle percentage modifiers correctly (multiplicative vs additive)
- Clear separation from base game balance values

### Phase 1 TDD Requirements

**Write tests BEFORE implementation** in `tests/unit/test_ascension.py`:

```python
# Test 1: Modifier calculation - cumulative stacking
def test_ascension_modifiers_cumulative():
    """A5 should include all modifiers from A1-A5."""
    mods = calculate_ascension_modifiers(5)
    assert mods.scanner_vision_bonus == 1  # A1
    assert mods.enemy_hp_bonus == 10       # A2
    assert mods.trace_gain_multiplier == 2.0  # A3
    assert mods.enemy_damage_multiplier == 1.2  # A4
    assert mods.enemy_vision_bonus == 1    # A5

# Test 2: A0 returns no modifiers
def test_ascension_zero_no_modifiers():
    """A0 should have no modifiers (base game)."""
    mods = calculate_ascension_modifiers(0)
    assert mods.scanner_vision_bonus == 0
    assert mods.enemy_hp_bonus == 0

# Test 3: Modifiers loaded from JSON, not hardcoded
def test_ascension_modifiers_from_json():
    """All modifier values must come from game_rules.json."""
    # Modify game_rules.json value, verify it changes output
    pass  # Implementation tests JSON loading

# Test 4: Unlock progression
def test_ascension_unlock_progression():
    """Victory at AN unlocks AN+1."""
    progress = {"highest_unlocked": 5}
    unlock_next_ascension(progress, current_level=5)
    assert progress["highest_unlocked"] == 6

# Test 5: Cannot unlock beyond current
def test_ascension_no_skip_unlock():
    """Winning A3 when A5 unlocked doesn't change highest."""
    progress = {"highest_unlocked": 5}
    unlock_next_ascension(progress, current_level=3)
    assert progress["highest_unlocked"] == 5  # Unchanged

# Test 6: Clamping edge cases
def test_ascension_clamping():
    """Values should never go below minimums."""
    # Test code floor (min 3)
    # Test node counts (min 0)
    pass
```

**Test files to create**:
- `tests/unit/test_ascension.py` - Core modifier logic
- `tests/unit/test_ascension_node_capacity.py` - RestoreNode system

### Node Capacity System (A13)

New data structure for limited-capacity nodes with hidden totals:
```python
@dataclass
class RestoreNode:
    node_type: str  # "cooling", "cpu", "ghost"
    position: Tuple[int, int]
    total_capacity: int  # Hidden from player, random per floor
    used_capacity: int = 0

    def use(self, amount_needed: int) -> int:
        """
        Returns actual restoration amount (may be less than requested).

        Args:
            amount_needed: The actual benefit the player needs (not max possible).
                           e.g., if player has 15 heat, pass 15 not 20.

        Only consumes capacity equal to what's actually provided.
        """
        remaining = self.total_capacity - self.used_capacity
        actual = min(amount_needed, remaining)
        self.used_capacity += actual  # Fair: only consume what was used
        return actual

    @property
    def depleted(self) -> bool:
        return self.used_capacity >= self.total_capacity
```

**Capacity Ranges by Floor** (per node, rolled independently):
- Floor 1: 100-200 capacity per node (at 20 restoration per use = 5-10 uses)
- Floor 2: 75-150 capacity per node (at 20 restoration per use = ~4-7 uses)
- Floor 3: 50-100 capacity per node (at 20 restoration per use = ~2-5 uses)

**Applies to**: Cooling nodes (20 heat), CPU nodes (20 CPU), AND ghost nodes (20% trace reduction).

**Integration**: At A13+, all restoration nodes use this system. Below A13, nodes have unlimited uses (`total_capacity = -1` sentinel). Player sees "DEPLETED" message when node runs dry - capacity is never shown numerically.

---

## 6. Phase 2 Details: Game Integration

### Files to Modify

#### `game_config.py`
- Add `AscensionConfig` class
- Modify `GameBalance` to accept ascension deltas
- Add `current_ascension_level` tracking

**Integration Point**: `GameBalance.apply_ascension(modifiers)`

#### `game_engine.py`
- Load ascension level from settings during initialization
- Apply modifiers before game state creation
- Store ascension level in save data

**Integration Point**: Constructor, before subsystem initialization

#### `game_level.py` / `game_level_coordinator.py`
**Modifiers Applied**:
- Enemy counts (A9: +5 per floor)
- Enemy type distribution (A12: weighted spawn)
- Node placement counts (A19: -1 cooling/CPU per floor)
- Node charge limits (A13: limited restoration capacity)
- Blind spot coverage (A6: -1% per floor)
- Blind spot persistence (A20: one-time use)
- Room generation (A16: larger rooms, wider corridors, less cover)
- Code count with floor (A11: -2 per floor, min 3)
- Upgrade placement (A18: -1 per floor)

**Integration Point**: Level generation, after base values loaded from JSON

#### `game_characters.py` / `game_enemies.py`
**Modifiers Applied**:
- Vision range (A1: Scanner +1, A5: all enemies +1)
- Health/CPU (A2: +10 all enemies)
- Damage (A4: +20% all enemies)
- Player vision (A10: 15→12)
- RAM capacity (A14: 8→6)

**Integration Point**: Enemy initialization, stat assignment

#### `game_turn_manager.py`
**Modifiers Applied**:
- Heat reduction per turn (A8: 2→1)
- Heat from combat (A17: melee +5 heat)
- Background trace gain (A3: x2 multiplier)
- Continuous hostile trace (A7: +0.2 flat)
- Enemy alert range (A15: 6→10)

**Integration Point**: Turn processing, state updates

#### `game_nodes.py` (New or Modified)
**Modifiers Applied**:
- Node capacity system (A13: hidden random capacity per floor)
- Node depletion and removal

**Integration Point**: Node interaction, resource restoration

### Technical Gotchas

**Clamping Issues**:
- Nodes reduced below 0 → need `max(0, base - modifier)` (A19)
- Codes reduced below 3 → need `max(3, base - modifier)` (A11)
- Heat reduction floor → `max(1, reduction)` (A8)

**Enemy Spawn Weight System**:
- A12 modifies spawn weights → use weighted random selection
- Must preserve total enemy count expectations

**Node Capacity Display**:
- A13 capacity is HIDDEN from player (uncertainty mechanic)
- Show "DEPLETED" message when node runs dry, not capacity numbers
- Color shift: green → red as restoration provided (but not exact number)

**Blind Spot Persistence (A20)**:
- Blind spots are tile types (no object), so track used positions in a `Set[Tuple[int,int]]` on `GameState`
- When player steps on blind spot at A20+: add position to set, log "SHADOW FADED"
- `is_blind_spot_active(pos)` checks: `is_blind_spot(pos) and pos not in used_blind_spots`
- Set must be saved/loaded with game state

**Save/Load Compatibility**:
- Old saves without ascension data → default to A0
- Ascension level mismatch (saved at A5, settings changed) → trust save data
- Node capacity state must be saved/loaded (A13+)
- Blind spot used state must be saved/loaded (A20+)

### Phase 2 TDD Requirements

**Write tests BEFORE implementation** in `tests/integration/test_ascension_integration.py`:

```python
# Test 1: Enemy stats modified correctly
def test_ascension_enemy_hp_bonus():
    """A2+ should add +10 CPU to all enemies."""
    game = create_game_at_ascension(2)
    bot = game.spawn_enemy("bot")
    assert bot.cpu == 35  # 25 base + 10

# Test 2: Enemy vision modified correctly
def test_ascension_scanner_vision_bonus():
    """A1+ should give Scanner +1 vision."""
    game = create_game_at_ascension(1)
    scanner = game.spawn_enemy("scanner")
    assert scanner.vision == 6  # 5 base + 1

# Test 3: All enemies vision at A5
def test_ascension_all_enemy_vision_bonus():
    """A5+ should give all enemies +1 vision (Scanner +2 total)."""
    game = create_game_at_ascension(5)
    scanner = game.spawn_enemy("scanner")
    bot = game.spawn_enemy("bot")
    assert scanner.vision == 7  # 5 + 1(A1) + 1(A5)
    assert bot.vision == 4      # 3 + 1(A5)

# Test 4: Enemy count increase
def test_ascension_enemy_count_increase():
    """A9+ should add +5 enemies per floor."""
    game = create_game_at_ascension(9)
    level1_enemies = game.get_enemy_count(floor=1)
    assert level1_enemies == 24  # 19 base + 5

# Test 5: Code floor minimum
def test_ascension_code_minimum_enforced():
    """A11 should never reduce codes below 3."""
    game = create_game_at_ascension(11)
    floor3_codes = game.get_code_count(floor=3)
    assert floor3_codes == 3  # 5 - 2 = 3 (min)

# Test 6: Blind spot persistence (A20)
def test_ascension_blind_spot_consumed():
    """A20 blind spots should vanish after use."""
    game = create_game_at_ascension(20)
    pos = Position(10, 10)
    game.set_tile(pos, TileType.BLIND_SPOT)
    assert game.is_blind_spot_active(pos)
    game.player_step_on(pos)
    assert not game.is_blind_spot_active(pos)  # Consumed

# Test 7: Save/load preserves ascension state
def test_ascension_save_load_roundtrip():
    """Ascension level survives save/load."""
    game = create_game_at_ascension(7)
    save_data = game.save()
    loaded_game = load_game(save_data)
    assert loaded_game.ascension_level == 7

# Test 8: Old saves default to A0
def test_ascension_old_save_migration():
    """Old saves without ascension default to A0."""
    old_save = {"player": {...}, "level": 1}  # No ascension field
    game = load_game(old_save)
    assert game.ascension_level == 0
```

**Test files to create**:
- `tests/integration/test_ascension_integration.py` - Full game integration tests
- `tests/integration/test_ascension_level_gen.py` - Level generation modifier tests

---

## 7. Phase 3 Details: UI/Menu System

### New File: `game_menu_ascension.py`

**UI Components**:
- Scrollable list of ascension levels (0-20)
- Lock/unlock indicators (locked levels grayed out)
- Current selection highlight
- **Modifier details panel**: Shows ALL cumulative modifiers for hovered/selected level
- Victory count per level
- Current highest unlocked indicator

**Input Handling**:
- Arrow keys / D-pad: Navigate levels (wrap-around at top/bottom)
- Enter / A button: Select and confirm
- Escape / B button: Cancel, return to main menu
- Mouse: Hover to preview modifiers, click to select
- Gamepad support required (Steam Deck)
- **Scroll behavior**: 21 levels may not fit on screen. Show ~10 visible with scroll indicator. D-pad up/down moves selection and scrolls view to keep selection visible. No page-up/page-down needed - list is short enough for single-step navigation.

**Layout** (similar to settings menu):
- Left panel: Level list (0-20) with lock icons
- Right panel: All modifiers for currently highlighted level (scrollable if many)
- Bottom: Instructions and current selection

**Modifier Display**:
- Show cumulative list of ALL active modifiers at selected level
- Example for A5: "Scanner +1 vision, All enemies +10 CPU, 2x trace gain, +20% damage, All enemies +1 vision"
- Locked levels show "???" or grayed modifier names

### Files to Modify

#### `game_menu_main.py`
**Changes**:
- Add ascension level display to menu header
- Add "Change Ascension" menu option (conditional: only if A1+ unlocked)
- Link to ascension selection menu
- Show current modifiers in help panel (optional)

**Integration Point**: Menu rendering, option handling

#### `game_victory_screen.py`
**Changes**:
- Display completed ascension level prominently
- Show "ASCENSION X UNLOCKED!" message (if unlocked new level)
- **NEW UNLOCK SCREEN**: When beating highest_unlocked, show a SEPARATE screen (styled like victory screen) after the main victory screen. This screen explains the new ascension level's modifier. Player must dismiss it (Enter/click) to continue - not a "never show again" toggle.
- Update `user_settings.json` ascension data
- Play unlock sound effect (optional)

**Integration Point**: Victory screen rendering, post-victory hooks

### Auto-Advance Behavior
**REQUIREMENT**: Auto-advance ONLY triggers when beating highest_unlocked for the first time. If player manually selects A5 and wins, their selection stays at A5. But if they later beat their max (e.g., A8) for the first time, it auto-advances to A9. Players can always manually select lower levels via the Ascension menu.

#### Status Bar (in `game_rendering_*.py`)
**Changes**:
- Add `[A#]` indicator to status bar
- Keep compact (2-3 characters)
- Position after RAM indicator

**Technical Note**: May need to adjust spacing, verify 80-column fit

**Screen Size Consideration**:
- Minimum viable resolution: 800×600 (10×12 pixel characters)
- Target resolution: 1280×800 (16×16 pixel characters, Steam Deck native)
- Status bar must remain readable at both resolutions
- 80-column layout fits both resolutions comfortably

### Phase 3 TDD Requirements

**Write tests BEFORE implementation** in `tests/unit/test_ascension_menu.py`:

```python
# Test 1: Menu shows correct unlock state
def test_ascension_menu_shows_unlocked_levels():
    """Menu should show all levels up to highest_unlocked as selectable."""
    menu = AscensionMenu(highest_unlocked=5)
    assert menu.is_level_selectable(0)
    assert menu.is_level_selectable(5)
    assert not menu.is_level_selectable(6)

# Test 2: Menu shows cumulative modifiers
def test_ascension_menu_shows_cumulative_modifiers():
    """Selecting A5 should display all A1-A5 modifiers."""
    menu = AscensionMenu(highest_unlocked=10)
    modifiers = menu.get_modifiers_for_level(5)
    assert "Scanner +1 vision" in modifiers  # A1
    assert "All enemies +10 CPU" in modifiers  # A2

# Test 3: Locked levels show placeholder
def test_ascension_menu_locked_level_hidden():
    """Locked levels should show '???' for modifiers."""
    menu = AscensionMenu(highest_unlocked=5)
    modifiers = menu.get_modifiers_for_level(6)
    assert modifiers == "???"

# Test 4: Selection persists after confirm
def test_ascension_menu_selection_saved():
    """Confirming selection should update user_settings."""
    menu = AscensionMenu(highest_unlocked=10)
    menu.select_level(7)
    menu.confirm_selection()
    assert get_current_ascension() == 7

# Test 5: Navigation wraps around
def test_ascension_menu_navigation_wraps():
    """Navigating past top/bottom should wrap."""
    menu = AscensionMenu(highest_unlocked=20)
    menu.current_selection = 0
    menu.navigate_up()
    assert menu.current_selection == 20  # Wrapped to bottom
```

**Test files to create**:
- `tests/unit/test_ascension_menu.py` - Menu navigation and display
- `tests/unit/test_ascension_victory_screen.py` - Unlock screen behavior

---

## 8. Phase 4 Details: Achievements & Metrics

### Files to Modify

#### `game_achievements.py`
**New Ascension Achievements** (category: "ascension"):
```python
"sensor_sweep": Achievement(
    id="sensor_sweep",
    name="Sensor Sweep",
    description="Complete Ascension 5",
    icon="[A5]",
    category="ascension"
)
"firewall_breaker": Achievement(
    id="firewall_breaker",
    name="Firewall Breaker",
    description="Complete Ascension 10",
    icon="[A10]",
    category="ascension"
)
"silent_running": Achievement(
    id="silent_running",
    name="Silent Running",
    description="Complete Ascension 15",
    icon="[A15]",
    category="ascension"
)
"ascension_master": Achievement(
    id="ascension_master",
    name="Ascension Master",
    description="Complete Ascension 20",
    icon="[A20]",
    category="ascension",
    hidden=True  # Ultimate achievement - hidden until unlocked
)
```

**Check Logic**: `session_metrics.victory and session_metrics.ascension_level >= N`
**NOTE**: These use bracketed text icons `[A5]` etc. to avoid emoji rendering issues and match the game's cyberpunk aesthetic.

#### `game_metrics.py`
**New Tracking**:
- `session_ascension_level: int` in `SessionMetrics`
- `ascension_victories: Counter` in `LifetimeMetrics`
- `highest_ascension_completed: int` in `LifetimeMetrics`

**Integration Point**: Victory detection, session end

### Phase 4 TDD Requirements

**Write tests BEFORE implementation** in `tests/unit/test_ascension_achievements.py`:

```python
# Test 1: Ascension achievements unlock at correct thresholds
def test_ascension_achievement_a5():
    """Winning at A5+ should unlock sensor_sweep."""
    session = create_session(victory=True, ascension_level=5)
    unlocked = check_session_achievements(session, set())
    assert "sensor_sweep" in unlocked

# Test 2: Lower ascension doesn't unlock higher achievements
def test_ascension_achievement_threshold():
    """Winning at A5 should NOT unlock firewall_breaker (A10)."""
    session = create_session(victory=True, ascension_level=5)
    unlocked = check_session_achievements(session, set())
    assert "firewall_breaker" not in unlocked

# Test 3: Defeat doesn't unlock achievements
def test_ascension_achievement_requires_victory():
    """Losing at A10 should NOT unlock any ascension achievements."""
    session = create_session(victory=False, ascension_level=10)
    unlocked = check_session_achievements(session, set())
    assert "firewall_breaker" not in unlocked

# Test 4: Hidden achievement stays hidden until unlocked
def test_ascension_master_hidden():
    """ascension_master should be hidden until A20 victory."""
    assert ALL_ACHIEVEMENTS["ascension_master"].hidden == True

# Test 5: Metrics track ascension level
def test_session_metrics_tracks_ascension():
    """SessionMetrics should record ascension_level."""
    session = SessionMetrics(session_id="test", timestamp_start=0.0)
    session.ascension_level = 7
    assert session.ascension_level == 7
```

**Test files to create**:
- `tests/unit/test_ascension_achievements.py` - Achievement unlock logic
- `tests/unit/test_ascension_metrics.py` - Metrics tracking

---

## 9. Phase 5 Details: Testing & Balance

### Automated Tests

**New Test File**: `tests/unit/test_ascension.py`
- Test modifier calculations (cumulative logic)
- Test unlock progression (A0 → A1 → A2)
- Test persistence (save/load ascension data)
- Test edge cases (A20 clamping, negative values)
- Test code floor (A11 never drops below 3)
- Test node capacity system (A13 depletion)

**Integration Tests**: `tests/integration/test_ascension_integration.py`
- Verify modifiers applied to enemy stats
- Verify modifiers applied to level generation
- Verify save data includes ascension level
- Verify node capacity state persists across save/load

### Manual Playtesting

**Test Each Milestone**:
- A0: Baseline (no modifiers)
- A5: First major challenge
- A10: Mid-tier difficulty
- A12: Enemy composition shift validation
- A13: Node capacity system validation
- A15: Alert cascade range assessment
- A16: Open map stealth viability
- A20: Maximum challenge

**Balance Questions**:
- Is A20 completable by skilled players?
- Are milestones (A5/A10/A15) appropriately spaced in difficulty?
- Do modifiers feel fair or arbitrary?
- Are early ascensions too easy/hard?
- Does A13's hidden node capacity create interesting tension or frustration?
- Is stealth still viable at A16+?

### Balance Tuning

**Adjustable Values**:
- Modifier magnitudes (+20% damage → +15%?)
- Node capacity ranges (100-200 → 150-250?)
- Enemy spawn weight deltas (+2 → +1?)
- Vision bonuses (+1 → +2?)
- Code floor (3 → 4?)
- Alert cascade range (6→10 → 6→8?)

**Tuning Process**:
1. Playtest current values
2. Identify too-easy or too-hard levels
3. Adjust single modifier at a time
4. Re-test
5. Iterate

---

## 10. Balance Philosophy

### Difficulty Curve Goals

- **A0-5**: Learning curve, introduces concepts
- **A6-10**: Intermediate, requires tactical thinking
- **A11-15**: Advanced, mastery required
- **A16-20**: Expert, minimal mistakes allowed

### Modifier Stacking Strategy

**Focus by Tier**:
- Early (A1-5): Awareness and scarcity
- Mid (A6-10): Enemy power and composition
- Late (A11-15): Resource mechanics and persistence
- Expert (A16-20): Map pressure and extremes

### Win Rate Targets (Community Average)

- A0: ~30-40% (learning)
- A5: ~20-25% (competent)
- A10: ~10-15% (skilled)
- A15: ~5-10% (expert)
- A20: ~3-8% (mastery)

**Note**: These are aspirational targets based on genre norms. A20 target raised from 1-5% to 3-8% to ensure skilled players can still succeed—frustration spikes hurt retention more than achievement dilution.

---

## 11. Technical Gotchas & Edge Cases

### Save File Compatibility
**Issue**: Old saves without ascension field
**Solution**: Migration logic in `GameSettings.load()` defaulting to `ascension_level: 0`

### Mid-Run Ascension Changes
**Issue**: Can player change ascension during active run?
**Solution**: NO. Lock ascension once run starts, store in save data

### Victory Without Unlocking Next
**Issue**: Complete A5 when A6 already unlocked
**Solution**: Check `highest_unlocked`, only increment if needed

### Modifier Conflicts
**Issue**: Modifiers reduce values below minimums
**Solution**: Clamp all values (`max(1, base - modifier)`), special floor for codes (`max(3, ...)`)

### Display Overflow
**Issue**: Too many modifiers at high ascensions
**Solution**: Scrollable list, category grouping

### Node Capacity Edge Cases
**Issue**: Player steps on depleted node
**Solution**: Show "DEPLETED" message, no effect, node remains visible but grayed out

### Blind Spot Depletion Edge Cases
**Issue**: Player steps on previously-used blind spot at A20
**Solution**: Show "SHADOW FADED" in system log, no stealth benefit, tile remains walkable

### Stealth Viability at High Exposure
**Issue**: A16 open maps + A6 fewer blind spots + A9 more enemies = stealth may fail
**Solution**: Determine viability through manual playtesting. No automated metric - "stealth viability" is subjective and best assessed by feel. Adjust map generation parameters if playtesting reveals stealth is unworkable at A16+.

---

## 12. Alternative Considerations

### Ascension Blessings (NOT RECOMMENDED FOR INITIAL RELEASE)
Provide small player buffs at certain levels (e.g., start with extra exploit at A10).

**Why Not Now**: Pure difficulty is cleaner, easier to balance. Avoid feature creep for initial implementation.

**Future Consideration**: If A15+ retention drops significantly, consider "mercy mechanics" like a single starting exploit at A15.

### Ascension-Specific Challenges (NOT RECOMMENDED)
Unique gameplay twists (e.g., A13: no minimap).

**Why Not**: Standard modifiers more predictable. Save for potential future "Challenge Mode."

### Custom Ascension Toggles (NOT RECOMMENDED)
Allow players to mix/match modifiers.

**Why Not**: Too complex for UI, dilutes achievement value. Standard progression is clearer.

### Relief Valve Modifier (CONSIDERED, DEFERRED)
One level that shifts mechanics sideways rather than purely harder (e.g., "enemies deal +30% damage but drop resources on death").

**Why Deferred**: Adds complexity to initial implementation. Revisit if mid-tier retention is poor. Could slot into A9 or A14 position.

---

## 13. Success Metrics

### Engagement Indicators
- Do players attempt higher ascensions after unlocking?
- What's the most popular ascension level? (engagement sweet spot)
- Do players return to push higher?

### Balance Indicators
- Win rate per ascension (decreasing appropriately?)
- Average attempts before first victory at each level
- Abandonment rate (quit at certain ascensions?)

**Tracking**: Use existing metrics system, add ascension-specific queries. Stealth viability assessed through manual playtesting, not automated metrics.

---

## 14. Future Expansion Ideas

**Post-Launch Possibilities**:
- Ascension 21-30: "Mythic Tiers"
- Leaderboards: Fastest clears per ascension
- Daily Challenge: Fixed seed + random ascension
- Ascension Cosmetics: UI themes at milestones
- Ascension Lore: Unique fragments at A10/A20

**Don't Implement Now**: Focus on core 0-20 system first.

---

## 15. Open Design Questions

### Starting Visibility
Should ascension menu appear before first victory?
**Recommendation**: Hide until first victory. Avoid overwhelming new players.

### Tutorial Integration
Should tutorial mention ascension?
**Recommendation**: No. Introduce via popup after first victory.

### Win Screen Emphasis
How prominent should unlock message be?
**Recommendation**: Major emphasis. Clear "ASCENSION X UNLOCKED" celebration.

### Modifier Tooltips
Should in-game tooltips show ascension modifiers?
**REQUIREMENT**: Yes. Add "(Ascension +X)" notes to affected stats. Players must understand why enemies are stronger or resources scarcer - otherwise difficulty feels arbitrary rather than systemic.

**Tooltip Locations**:
- **Enemy inspection (Look mode)**: Show modified stats with ascension delta, e.g., "CPU: 45 (+10 Ascension)"
- **Player stats panel**: Show RAM/vision with ascension modifier if active
- **Help screen (F1)**: Include "Current Ascension: X" and list active modifiers
- **Node inspection**: At A13+, do NOT show capacity (that's the uncertainty mechanic)

### Unlock Triggers
Unlock A6 after ANY A5 attempt, or only victory?
**Recommendation**: Victory only. Maintains prestige.

### Node Capacity Feedback (A13)
How to indicate node health without revealing exact capacity?
**Recommendation**: Don't show numbers - that's the point (uncertainty). Use subtle color shift (green → yellow → red) based on % of capacity used. Player must intuit when a node might be running low.

---

## 16. Comparison to Genre Examples

### Slay the Spire
- **Similarities**: 20 levels, cumulative, unlock-after-victory
- **Differences**: Character-specific unlocks (we have single character)
- **Lesson**: Keep modifiers visible and understandable

### Monster Train
- **Similarities**: Progressive difficulty, milestones
- **Differences**: 25 levels (we use 20 for accessibility)
- **Lesson**: Modifiers should feel thematic, not arbitrary

### Hades
- **Similarities**: Difficulty modifiers, player choice
- **Differences**: Custom combinations (we use fixed progression)
- **Lesson**: Fixed progression cleaner for achievement tracking

---

## 17. Narrative Integration

Each ascension represents network admins responding to previous escape.

**Victory Screen Hook Example**:
```
"Your escape route has been logged and analyzed.
Security protocols updated.
Countermeasures deployed.

The next infiltration will not be so easy.

ASCENSION 6 UNLOCKED: Aggressive Response"
```

Creates narrative loop: escape → adaptation → overcome → repeat.

---

## Implementation Checklist

**Phase 1: Core System**
- [ ] **PREREQ**: Move enemy spawn weights from `game_level_coordinator.py:558` to `game_rules.json`
- [ ] **PREREQ**: Lower base alert range from 8→6 in `game_rules.json`
- [ ] Create `game_ascension.py` with `AscensionModifiers` dataclass
- [ ] Implement `calculate_ascension_modifiers()` cumulative logic
- [ ] Define all 20 ascension modifier sets in `game_rules.json`
- [ ] Implement `RestoreNode` capacity system for A13 (cooling, CPU, AND ghost nodes)
- [ ] Update `user_settings.json` schema (single source of truth for ascension state)
- [ ] Write unit tests for modifier calculations
- [ ] Write unit tests for node capacity depletion

**Phase 2: Game Integration**
- [ ] Modify `game_config.py` for ascension support
- [ ] Modify `game_engine.py` to load and apply modifiers
- [ ] Update enemy systems (`game_characters.py`, `game_enemies.py`)
- [ ] Update level generation (`game_level.py`, `game_level_coordinator.py`)
- [ ] Update turn management (`game_turn_manager.py`)
- [ ] Implement node capacity system in gameplay (A13)
- [ ] Implement one-time-use blind spots with Set tracking (A20)
- [ ] Add code floor clamping (minimum 3)
- [ ] Write integration tests for applied modifiers

**Phase 3: UI/Menu**
- [ ] Create `game_menu_ascension.py` selection screen
- [ ] Modify `game_menu_main.py` for ascension display
- [ ] Modify `game_victory_screen.py` for unlock messaging
- [ ] Add status bar indicator
- [ ] Add node capacity visual feedback (color shift, no numbers)
- [ ] **REQUIRED**: Implement modifier tooltips in-game
- [ ] Test UI navigation and rendering

**Phase 4: Achievements**
- [ ] Add ascension achievements: sensor_sweep (A5), firewall_breaker (A10), silent_running (A15), ascension_master (A20)
- [ ] Add fun/hidden achievements: thermal_meltdown, own_worst_enemy, admin_slayer, close_call, cold_blooded, floor_is_lava, full_clear, shadow_dancer
- [ ] Add new SessionMetrics fields: ascension_level, last_exploit_used, admin_kills, final_cpu, restoration_nodes_used, full_floor_clears
- [ ] Update `game_metrics.py` for ascension tracking
- [ ] Write unit tests for all new achievements (TDD)
- [ ] Test achievement unlock conditions

**Phase 5: Testing & Balance**
- [ ] Playtest A0 (baseline verification)
- [ ] Playtest A5 (first milestone)
- [ ] Playtest A10 (mid-tier)
- [ ] Playtest A13 (node capacity system)
- [ ] Playtest A15 (alert cascade range)
- [ ] Playtest A16 (open maps/stealth viability)
- [ ] Playtest A17+A8 combo (heat stacking)
- [ ] Playtest A20 (maximum challenge)
- [ ] Tune modifier values based on feedback
- [ ] Document system in README_DEV.md

---

## Modifier Ideas (Maybes)

Unused modifiers for future expansion or A21-30:

1. **"Total Surveillance"** - +2 Scanner enemies per floor

2. **"Noisy Restoration"** - Using a restoration node alerts enemies within 4 tiles

3. **"Lingering Effects"** - Virus and Inhibitor effects last +1 turn longer per application

4. **"Administrative Override"** - Admin spawns at lower trace thresholds (-5 to threshold)

5. **"Fragmented Memory"** - Exploits found on floor only work on that floor (don't persist)

6. **"Broken Protocols"** - Ghost nodes restore less (50% effectiveness)

7. **"Unstable Networks"** - Random node failures (10% chance per turn a node becomes temporarily unusable)

---

## Changelog

### v1.4 (Current - TDD & Achievements)
**Added TDD requirements and new achievements:**

- **FIXED: Achievement name collision**: Renamed A5 achievement from "Ghost Protocol" to "Sensor Sweep" (ghost_protocol already exists as stealth achievement)
- **FIXED: A15 achievement**: Renamed from "Signal Ghost" to "Silent Running" (avoid ghost naming confusion)
- **CLARIFIED: A11 code minimum**: Added explicit formula `max(3, base_codes - 2)` per floor
- **CLARIFIED: A13 fair consumption**: ALL nodes only consume capacity equal to actual benefit provided (not max 20). Prevents penalizing efficient play.
- **ADDED: Phase 1 TDD tests**: Unit tests for modifier calculation, cumulative stacking, unlock progression
- **ADDED: Phase 2 TDD tests**: Integration tests for enemy stats, level gen, save/load, blind spot consumption
- **ADDED: Phase 3 TDD tests**: Menu navigation, unlock state display, selection persistence
- **ADDED: Phase 4 TDD tests**: Achievement unlock thresholds, hidden achievement behavior
- **ADDED: Section 18**: Complete new achievements list with check logic and TDD tests
- **NEW ACHIEVEMENTS - Ascension**: sensor_sweep (A5), firewall_breaker (A10), silent_running (A15), ascension_master (A20)
- **NEW ACHIEVEMENTS - Fun/Hidden**: thermal_meltdown, own_worst_enemy, admin_slayer, close_call, cold_blooded, floor_is_lava, full_clear, shadow_dancer
- **NEW METRICS**: ascension_level, last_exploit_used, admin_kills, final_cpu, restoration_nodes_used, full_floor_clears

### v1.3 (Previous - Audit Fixes)
**Clarifications and fixes from implementation audit:**

- **Auto-advance**: Only triggers when beating highest_unlocked, not any level
- **Persistence**: Single source of truth in `user_settings.json` (no duplication)
- **A13 nodes**: All nodes (cooling, CPU, AND ghost) have capacity; per-node not per-floor
- **A15 prereq**: Base alert range 8→6 happens in Phase 1, affects all players (intentional tradeoff)
- **A16 structure**: Fixed JSON paths (`room_generation.corridor_width_weights.wide`, etc.)
- **A20 tracking**: Blind spots are tile types - use `Set[Tuple[int,int]]` on GameState
- **Unlock screen**: Separate screen after victory (styled similarly), not a dismissable toggle
- **Damage rounding**: Use `int(base * 1.2)` (truncate decimals)
- **Tooltips**: Specified locations (enemy inspection, player stats, help screen)
- **Gamepad scrolling**: Wrap-around navigation, ~10 visible with scroll indicator
- **Stealth viability**: Removed automated metric - determined via manual playtesting
- **Phase 1 prereqs**: Added spawn weights to JSON and alert range change as explicit prereqs

### v1.2 (Previous - Complete Redesign)
**Complete A1-A20 redesign with cyberpunk-themed names and balanced progression:**

**Early Game (A1-A5):**
- A1 "Enhanced Monitoring": Scanner-only vision +1 (gentler intro)
- A2 "Hardened Processes": All enemies +10 CPU
- A3 "Residual Signatures": Background trace x2 (moved from mid-game)
- A4 "Aggressive Protocols": Enemy damage +20%
- A5 "Wide-Spectrum Sensors": All enemies +1 vision

**Mid Game (A6-A10):**
- A6 "Shrinking Shadows": Blind spots -1% per floor (7/6/5)
- A7 "Trace Persistence": Continuous hostile trace +0.2 flat
- A8 "Thermal Decay": Heat reduction 2→1
- A9 "Crowded Networks": +5 enemies per floor
- A10 "Signal Fog": Player vision 15→12

**Late Game (A11-A15):**
- A11 "Data Drought": Codes -2 per floor (min 3)
- A12 "Threat Escalation": Enemy spawn weights rebalanced
- A13 "Degraded Infrastructure": Nodes have hidden random capacity
- A14 "Memory Constraints": Starting RAM 8→6
- A15 "Network Cascade": Alert range 6→10 (PRE-REQ: base 8→6)

**Expert (A16-A20):**
- A16 "Exposed Topology": Open map generation, less cover
- A17 "Thermal Signature": Melee attacks +5 heat
- A18 "Streamlined Systems": Upgrades -1 per floor (6→3 total)
- A19 "Failing Infrastructure": Cooling/CPU nodes -1 per floor
- A20 "Decaying Shadows": Blind spots vanish when stepped on

**Architecture changes:**
- All modifier values must be in game_rules.json (not hardcoded)
- Player-facing descriptions should be thematic, not number-heavy
- Auto-advance behavior: winning at AN sets next run to AN+1 automatically
- Victory screen shows dedicated unlock explanation for new levels

### v1.1 (Previous)
- Initial node charge system concept
- Alert timer experiments
- Thematic achievement names
- Tooltips marked as requirement

---

## 18. New Achievements (Added to Phase 4)

This section defines ALL new achievements to be added as part of the Ascension system implementation.

### Ascension Milestone Achievements

These unlock upon completing specific ascension levels:

| ID | Name | Description | Icon | Category | Hidden |
|----|------|-------------|------|----------|--------|
| `sensor_sweep` | Sensor Sweep | Complete Ascension 5 | `[A5]` | ascension | No |
| `firewall_breaker` | Firewall Breaker | Complete Ascension 10 | `[A10]` | ascension | No |
| `silent_running` | Silent Running | Complete Ascension 15 | `[A15]` | ascension | No |
| `ascension_master` | Ascension Master | Complete Ascension 20 | `[A20]` | ascension | Yes |

### Fun/Hidden Achievements

New achievements for memorable moments and edge cases:

| ID | Name | Description | Icon | Category | Hidden |
|----|------|-------------|------|----------|--------|
| `thermal_meltdown` | Thermal Meltdown | Die from overheating while using System Crash | `[MELT]` | challenge | Yes |
| `own_worst_enemy` | Own Worst Enemy | Kill yourself with Logic Bomb friendly fire | `[BOOM]` | challenge | Yes |
| `admin_slayer` | Admin Slayer | Defeat the Admin Avatar | `[ADMIN]` | combat | No |
| `close_call` | Close Call | Win with 5 or less CPU remaining | `[CLOSE]` | challenge | No |
| `cold_blooded` | Cold Blooded | Win without ever exceeding 25 heat | `[COLD]` | efficiency | No |
| `floor_is_lava` | The Floor is Lava | Win without stepping on any restoration nodes | `[LAVA]` | challenge | Yes |
| `full_clear` | Full Clear | Eliminate every enemy on a floor | `[CLEAR]` | combat | No |
| `shadow_dancer` | Shadow Dancer | Spend 100+ turns in blind spots in a single run | `[SHADOW]` | stealth | No |

### Achievement Check Logic

Add to `AchievementChecker.check_session_achievements()`:

```python
# Ascension achievements
if session.victory and session.ascension_level >= 5:
    if "sensor_sweep" not in already_unlocked:
        newly_unlocked.append("sensor_sweep")
if session.victory and session.ascension_level >= 10:
    if "firewall_breaker" not in already_unlocked:
        newly_unlocked.append("firewall_breaker")
if session.victory and session.ascension_level >= 15:
    if "silent_running" not in already_unlocked:
        newly_unlocked.append("silent_running")
if session.victory and session.ascension_level >= 20:
    if "ascension_master" not in already_unlocked:
        newly_unlocked.append("ascension_master")

# Fun achievements
if session.death_cause == "overheat" and session.last_exploit_used == "system_crash":
    if "thermal_meltdown" not in already_unlocked:
        newly_unlocked.append("thermal_meltdown")

if session.death_cause == "self_damage" and session.last_exploit_used == "logic_bomb":
    if "own_worst_enemy" not in already_unlocked:
        newly_unlocked.append("own_worst_enemy")

if session.admin_kills > 0:
    if "admin_slayer" not in already_unlocked:
        newly_unlocked.append("admin_slayer")

if session.victory and session.final_cpu <= 5:
    if "close_call" not in already_unlocked:
        newly_unlocked.append("close_call")

if session.victory and session.highest_heat_reached <= 25:
    if "cold_blooded" not in already_unlocked:
        newly_unlocked.append("cold_blooded")

if session.victory and session.restoration_nodes_used == 0:
    if "floor_is_lava" not in already_unlocked:
        newly_unlocked.append("floor_is_lava")

if session.full_floor_clears > 0:
    if "full_clear" not in already_unlocked:
        newly_unlocked.append("full_clear")

if session.turns_in_blind_spots >= 100:
    if "shadow_dancer" not in already_unlocked:
        newly_unlocked.append("shadow_dancer")
```

### New SessionMetrics Fields Required

Add these fields to `SessionMetrics` dataclass in `game_metrics.py`:

```python
# Ascension tracking
ascension_level: int = 0

# Fun achievement tracking
last_exploit_used: str | None = None  # Track last exploit for death context
admin_kills: int = 0
final_cpu: int = 0  # Set on death/victory
restoration_nodes_used: int = 0
full_floor_clears: int = 0  # Incremented when all enemies on floor eliminated
```

### TDD Tests for New Achievements

Add to `tests/unit/test_achievements.py`:

```python
# Test thermal_meltdown
def test_thermal_meltdown_achievement():
    """Dying from overheat while using System Crash unlocks thermal_meltdown."""
    session = create_session(
        victory=False,
        death_cause="overheat",
        last_exploit_used="system_crash"
    )
    unlocked = check_session_achievements(session, set())
    assert "thermal_meltdown" in unlocked

def test_thermal_meltdown_requires_system_crash():
    """Overheat death alone doesn't unlock thermal_meltdown."""
    session = create_session(
        victory=False,
        death_cause="overheat",
        last_exploit_used="buffer_overflow"
    )
    unlocked = check_session_achievements(session, set())
    assert "thermal_meltdown" not in unlocked

# Test own_worst_enemy
def test_own_worst_enemy_achievement():
    """Killing yourself with Logic Bomb unlocks own_worst_enemy."""
    session = create_session(
        victory=False,
        death_cause="self_damage",
        last_exploit_used="logic_bomb"
    )
    unlocked = check_session_achievements(session, set())
    assert "own_worst_enemy" in unlocked

# Test close_call
def test_close_call_achievement():
    """Winning with 5 or less CPU unlocks close_call."""
    session = create_session(victory=True, final_cpu=3)
    unlocked = check_session_achievements(session, set())
    assert "close_call" in unlocked

def test_close_call_requires_low_cpu():
    """Winning with > 5 CPU doesn't unlock close_call."""
    session = create_session(victory=True, final_cpu=50)
    unlocked = check_session_achievements(session, set())
    assert "close_call" not in unlocked

# Test floor_is_lava
def test_floor_is_lava_achievement():
    """Winning without using restoration nodes unlocks floor_is_lava."""
    session = create_session(victory=True, restoration_nodes_used=0)
    unlocked = check_session_achievements(session, set())
    assert "floor_is_lava" in unlocked
```

---

**END OF PLAN**
