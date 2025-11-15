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

### Ascension 1: "Enhanced Monitoring"
Enemy vision range: +1 tile

### Ascension 2: "Optimized Patrols"
Patrol enemies move faster (recalculate paths more frequently)

### Ascension 3: "Hardened Firewalls"
All enemies: +20% max CPU (health)

### Ascension 4: "Trace Amplification"
Background trace buildup: +1 per level (2/3/4 instead of 1/2/3)

### Ascension 5: "Resource Scarcity"
Cooling nodes: -1 per level, CPU recovery nodes: -1 per level
**Achievement**: "Ascension Initiate"

### Ascension 6: "Aggressive Response"
All enemy damage: +20%

### Ascension 7: "Digital Wasteland"
Blind spot coverage: -10%

### Ascension 8: "Admin Vigilance"
Admin spawn trace threshold: -10 (90 instead of 100)

### Ascension 9: "Thermal Instability"
Heat reduction per turn: -1

### Ascension 10: "Elite Security"
Replace 3 Bots/Scanners with Hunters per level
**Achievement**: "Ascension Adept"

### Ascension 11: "Code Scarcity"
Data Codes: -2 per level

### Ascension 12: "Exploit Drought"
Exploit pickups: -1 per level

### Ascension 13: "Aggressive Stance"
Enemy alert timer: 3 turns (instead of 1), memory turns: 30 (instead of 20)

### Ascension 14: "Fortified Networks"
Admin CPU: +50, Admin damage: +10

### Ascension 15: "Total Surveillance"
+2 Scanner enemies per level
**Achievement**: "Ascension Expert"

### Ascension 16: "Hostile Architecture"
Room count: -2 per level

### Ascension 17: "Viral Proliferation"
Replace 2 random enemies with Viruses per level

### Ascension 18: "Upgrade Reduction"
Permanent upgrades: -1 per level

### Ascension 19: "Maximum Security"
Starting trace level: +20, Trace threshold for hostile: -5

### Ascension 20: "Impossible Odds"
Enemy vision: +1 additional, Admin damage resistance: +20%, Heat capacity: -20
**Achievement**: "Ascension Master"

---

## 3. Data Structure & Persistence

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

### rogue_signal_progress.json Addition
```json
"lifetime_metrics": {
  "ascension_victories": {"0": 12, "5": 1},
  "highest_ascension_completed": 5
}
```

---

## 4. Phase 1 Details: Core Modifier System

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

**Technical Considerations**:
- Must handle clamping (e.g., nodes never go below 0)
- Must handle percentage modifiers correctly (multiplicative vs additive)
- Clear separation from base game balance values

---

## 5. Phase 2 Details: Game Integration

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
- Enemy counts (A10: replace types)
- Enemy type distribution (A15: add scanners, A17: add viruses)
- Node placement counts (A5: reduce nodes)
- Blind spot coverage (A7: reduce coverage)
- Room count (A16: fewer rooms)

**Integration Point**: Level generation, after base values loaded from JSON

#### `game_characters.py` / `game_enemies.py`
**Modifiers Applied**:
- Vision range (A1, A20)
- Health/CPU (A3)
- Damage (A6)
- Movement speed (A2: patrol recalculation frequency)
- Admin stats (A14: buffed admin)

**Integration Point**: Enemy initialization, stat assignment

#### `game_turn_manager.py`
**Modifiers Applied**:
- Heat reduction per turn (A9)
- Trace buildup (A4)
- Admin spawn thresholds (A8)
- Enemy alert/memory durations (A13)

**Integration Point**: Turn processing, state updates

### Technical Gotchas

**Clamping Issues**:
- Nodes reduced below 0 → need `max(0, base - modifier)`
- Heat capacity reduced → verify overheat thresholds still work

**Enemy Type Replacement**:
- A10/A15/A17 replace existing enemies → need enemy list mutation
- Must preserve total enemy count expectations

**Save/Load Compatibility**:
- Old saves without ascension data → default to A0
- Ascension level mismatch (saved at A5, settings changed) → trust save data

---

## 6. Phase 3 Details: UI/Menu System

### New File: `game_menu_ascension.py`

**UI Components**:
- Scrollable list of ascension levels
- Lock/unlock indicators
- Current selection highlight
- Active modifiers display (right panel)
- "Next Level" preview
- Victory count per level

**Input Handling**:
- Arrow keys: Navigate levels
- Enter: Select and confirm
- Escape: Cancel, return to main menu
- Mouse: Click to select (optional)

**Layout** (similar to settings menu):
- Left: Level list (0-20)
- Right: Modifier details for selected level
- Bottom: Instructions

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
- Update `rogue_signal_progress.json` via new function
- Play unlock sound effect (optional)

**Integration Point**: Victory screen rendering, post-victory hooks

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

---

## 7. Phase 4 Details: Achievements & Metrics

### Files to Modify

#### `game_achievements.py`
**New Achievements**:
```python
"ascension_initiate": Achievement(
    name="Ascension Initiate",
    description="Complete Ascension 5",
    category="mastery"
)
# Similar for A10, A15, A20
```

**Check Logic**: `session_metrics.victory and session_metrics.ascension_level >= 5`

#### `game_metrics.py`
**New Tracking**:
- `session_ascension_level: int` in `SessionMetrics`
- `ascension_victories: Counter` in `LifetimeMetrics`
- `highest_ascension_completed: int` in `LifetimeMetrics`

**Integration Point**: Victory detection, session end

---

## 8. Phase 5 Details: Testing & Balance

### Automated Tests

**New Test File**: `tests/unit/test_ascension.py`
- Test modifier calculations (cumulative logic)
- Test unlock progression (A0 → A1 → A2)
- Test persistence (save/load ascension data)
- Test edge cases (A20 clamping, negative values)

**Integration Tests**: `tests/integration/test_ascension_integration.py`
- Verify modifiers applied to enemy stats
- Verify modifiers applied to level generation
- Verify save data includes ascension level

### Manual Playtesting

**Test Each Milestone**:
- A0: Baseline (no modifiers)
- A5: First major challenge
- A10: Mid-tier difficulty
- A15: High difficulty
- A20: Maximum challenge

**Balance Questions**:
- Is A20 completable by skilled players?
- Are milestones (A5/A10/A15) appropriately spaced in difficulty?
- Do modifiers feel fair or arbitrary?
- Are early ascensions too easy/hard?

### Balance Tuning

**Adjustable Values**:
- Modifier magnitudes (+20% → +15%?)
- Node reduction amounts (-1 → -2?)
- Enemy type replacement counts (3 → 2?)
- Admin buff values (+50 CPU → +75?)

**Tuning Process**:
1. Playtest current values
2. Identify too-easy or too-hard levels
3. Adjust single modifier at a time
4. Re-test
5. Iterate

---

## 9. Balance Philosophy

### Difficulty Curve Goals

- **A0-5**: Learning curve, introduces concepts
- **A6-10**: Intermediate, requires tactical thinking
- **A11-15**: Advanced, mastery required
- **A16-20**: Expert, minimal mistakes allowed

### Modifier Stacking Strategy

**Focus by Tier**:
- Early (A1-5): Awareness and scarcity
- Mid (A6-10): Enemy power and composition
- Late (A11-15): Item scarcity and persistence
- Expert (A16-20): Map pressure and extremes

### Win Rate Targets (Community Average)

- A0: ~30-40% (learning)
- A5: ~20-25% (competent)
- A10: ~10-15% (skilled)
- A15: ~5-10% (expert)
- A20: ~1-5% (mastery)

**Note**: These are aspirational targets based on genre norms, not requirements.

---

## 10. Technical Gotchas & Edge Cases

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
**Solution**: Clamp all values (`max(1, base - modifier)`)

### Display Overflow
**Issue**: Too many modifiers at high ascensions
**Solution**: Scrollable list, category grouping

---

## 11. Alternative Considerations

### Ascension Blessings (NOT RECOMMENDED)
Provide small player buffs at certain levels (e.g., start with extra exploit at A10).

**Why Not**: Pure difficulty is cleaner, easier to balance. Avoid feature creep for initial implementation.

### Ascension-Specific Challenges (NOT RECOMMENDED)
Unique gameplay twists (e.g., A13: no minimap).

**Why Not**: Standard modifiers more predictable. Save for potential future "Challenge Mode."

### Custom Ascension Toggles (NOT RECOMMENDED)
Allow players to mix/match modifiers.

**Why Not**: Too complex for UI, dilutes achievement value. Standard progression is clearer.

---

## 12. Success Metrics

### Engagement Indicators
- Do players attempt higher ascensions after unlocking?
- What's the most popular ascension level? (engagement sweet spot)
- Do players return to push higher?

### Balance Indicators
- Win rate per ascension (decreasing appropriately?)
- Average attempts before first victory at each level
- Abandonment rate (quit at certain ascensions?)

**Tracking**: Use existing metrics system, add ascension-specific queries

---

## 13. Future Expansion Ideas

**Post-Launch Possibilities**:
- Ascension 21-30: "Mythic Tiers"
- Leaderboards: Fastest clears per ascension
- Daily Challenge: Fixed seed + random ascension
- Ascension Cosmetics: UI themes at milestones
- Ascension Lore: Unique fragments at A10/A20

**Don't Implement Now**: Focus on core 0-20 system first.

---

## 14. Open Design Questions

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
**Recommendation**: Yes. Add "(Ascension +X)" notes to affected stats.

### Unlock Triggers
Unlock A6 after ANY A5 attempt, or only victory?
**Recommendation**: Victory only. Maintains prestige.

---

## 15. Comparison to Genre Examples

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

## 16. Narrative Integration

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
- [ ] Create `game_ascension.py` with `AscensionModifiers` dataclass
- [ ] Implement `calculate_ascension_modifiers()` cumulative logic
- [ ] Define all 20 ascension modifier sets
- [ ] Update `user_settings.json` schema
- [ ] Update `rogue_signal_progress.json` schema
- [ ] Write unit tests for modifier calculations

**Phase 2: Game Integration**
- [ ] Modify `game_config.py` for ascension support
- [ ] Modify `game_engine.py` to load and apply modifiers
- [ ] Update enemy systems (`game_characters.py`, `game_enemies.py`)
- [ ] Update level generation (`game_level.py`, `game_level_coordinator.py`)
- [ ] Update turn management (`game_turn_manager.py`)
- [ ] Write integration tests for applied modifiers

**Phase 3: UI/Menu**
- [ ] Create `game_menu_ascension.py` selection screen
- [ ] Modify `game_menu_main.py` for ascension display
- [ ] Modify `game_victory_screen.py` for unlock messaging
- [ ] Add status bar indicator
- [ ] Test UI navigation and rendering

**Phase 4: Achievements**
- [ ] Add ascension achievements (A5/A10/A15/A20)
- [ ] Update `game_metrics.py` for ascension tracking
- [ ] Test achievement unlock conditions

**Phase 5: Testing & Balance**
- [ ] Playtest A0 (baseline verification)
- [ ] Playtest A5 (first milestone)
- [ ] Playtest A10 (mid-tier)
- [ ] Playtest A15 (high difficulty)
- [ ] Playtest A20 (maximum challenge)
- [ ] Tune modifier values based on feedback
- [ ] Document system in README_DEV.md

---

**END OF PLAN**
