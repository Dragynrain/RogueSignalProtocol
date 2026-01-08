# Prologue Level Implementation Plan

## Implementation Progress

**ALL PHASES COMPLETED**:
- [x] Phase 1: Data Layer (game_content.json, narrative_content.json, config.py)
- [x] Phase 2: Fixed level generator (fixed_levels.py, fixed_generator.py)
- [x] Phase 3: Prologue level layout (28x24 ASCII map in fixed_levels.py)
- [x] Phase 4.5: Visibility status in status bar (CONCEALED/EXPOSED/TOO CLOSE!)
- [x] Phase 4.6: Reactive internal voice system (prologue_thoughts.py)
- [x] Phase 5: Game flow integration (engine.py, menu_main.py, loop.py, dialogue.py, death.py, coordinator.py)
- [x] Phase 6: Tests passing (1772 unit tests)

---

## Mechanic Reference (from codebase analysis)

**This section documents ACTUAL game mechanics. Tutorial design MUST match these.**

### Enemy States (turn_manager.py)
- **UNAWARE**: Default. Patrols/wanders. No hostility.
- **ALERT**: Triggered when enemy sees player. **1 turn grace period.** Player can break LOS to de-escalate.
- **HOSTILE**: Pursues player, increases trace. 15% chance per turn to de-escalate if player escapes LOS.

### Blind Spots (characters.py lines 359-362)
- **Only block vision at range > 1**
- **Adjacent enemies (grid distance ≤ 1) SEE THROUGH blind spots**
- Provide +10 stealth attack bonus
- Ghost nodes also function as blind spots

### Enemy Movement Types (game_content.json)
- **Scanner**: STATIC (never moves), vision 5, no damage
- **Patrol**: PATROL (follows routes), vision 4, damage 10
- **Bot**: RANDOM (wanders unpredictably), vision 3, damage 8 - NOT USED in prologue (replaced with Patrol)

### Patrol Behavior (enemies.py)
- Follow 2-4 waypoint routes (line, triangle, rectangle patterns)
- When hostile: break pattern, chase player
- When player escapes: **return to exact patrol waypoint**
- Store `original_patrol_index` when going hostile

### Combat (combat.py)
- Player CAN kill any enemy with exploits
- Buffer Overflow: melee, 40 damage
- Code Injection: range 5, 25 damage
- Heat builds up, limiting exploit spam
- **Tutorial cannot force stealth - combat is always an option**

### Vision (characters.py can_see_player)
1. Disabled enemies can't see
2. Admin always sees (omniscient)
3. Range check (Euclidean distance)
4. Invisibility check (Traffic Masquerade)
5. Blind spot check (only at range > 1)
6. TCOD FOV check (walls block)

---

## Design Philosophy: Show Don't Tell

**This prologue teaches through environmental design and internal character voice, not external explanations.**

**CRITICAL CONSTRAINTS:**
1. Use only REAL game mechanics - no tutorial-only elements
2. Player CAN kill any enemy - can't force "must sneak"
3. Blind spots only work at range - can't hide adjacent to enemies
4. Encourage optimal behavior through layout, don't block alternatives

| Instead of... | We do... |
|--------------|----------|
| Popup: "Enemies move when you move" | Patrol visible through wall gap + thought: "It only moves when I do..." |
| Popup: "Blind spots hide you at range" | Layout where blind spot saves you from distant enemy, not adjacent |
| Popup: "Alert gives you 1 turn to escape" | Patrol spots player, they flee to break LOS before HOSTILE |
| Hint: "Use exploits for ranged combat" | Enemy across gap + thought: "Can't reach them... exploit might work" |
| Message: "Nodes restore resources" | Node placed where player naturally needs it |
| Tutorial objectives checklist | Sections where optimal path uses the mechanic |

**Key insight**: Tutorial encourages, doesn't force. Stealth should be EASIER than combat, not mandatory.


---

## Summary of Phases

1. **Phase 1: Data Layer** - Add prologue configuration to JSON files and user settings tracking
2. **Phase 2: Fixed Level Generator** - Create `FixedLevelGenerator` class for hand-designed levels
3. **Phase 3: Prologue Level Design** - Design and implement the tutorial level layout
4. **Phase 4: Tutorial System** - Create tutorial message/hint system with contextual triggers
5. **Phase 5: Game Flow Integration** - Integrate prologue into game startup and completion flow
6. **Phase 6: Testing & Polish** - Unit tests, integration tests, and gameplay polish

---

## Quick Reference: Critical Decisions

**Verified Implementation Paths:**
- `ENTER` key routes to `handle_dismiss()` (NOT `handle_confirm()`) - dialogue checks go there
- `generator.py` does NOT need modification - all fixed level logic goes in `coordinator.py`
- `death_handler.reset()` method already exists - use it for prologue restart
- Tutorial enemies use normal AI with reduced HP - no special behavior modification needed

**Layout Dimensions:** 28 wide x 25 tall

**Design Elements (ALL REAL GAME MECHANICS):**
- `X` = Damaged Scanner (STATIC, 5 HP - Sections 1 & 3: melee teaching + ranged practice)
- `P` = Patrol (PATROL movement - Sections 1, 3, 4, 5: predictable routes for reliable teaching)
- `S` = Scanner (STATIC - Section 2: blind spot trap, can't chase so safe to fail against)
- `s` = Blind spots (hide at range > 1 ONLY - adjacent enemies see through!)
- `c/r/g` = Nodes (real items)
- `e` = Exploit pickup (Code Injection in Section 1)
- `E` = Exploit pickup (Threat Scan in Section 3 - utility, not combat)
- `d` = Code hack (Section 3 - reward after alert escape, teaches color discovery)
- Diagonal corridor segment (Section 1 - teaches 8-directional movement)
- Continuous CONCEALED/EXPOSED/TOO CLOSE status indicator (prologue-only UI, 1.5s flash duration)
- Internal character voice (prologue-only guidance)
- Death hint system (contextual tips after first death per section)

**Key Mechanic Teaching:**
- Section 1a: Diagonal movement (diagonal corridor segment - faster than orthogonal)
- Section 1a: Melee combat (Damaged Scanner blocks exit - must bump to attack)
- Section 1b: Turn-based + WAIT (Patrol blocks corridor - must wait)
- Section 2: Blind spots work at RANGE ONLY (Blind spot trap forces adjacent failure, TOO CLOSE feedback)
- Section 3: Alert grace period + FOV bidirectionality (Patrol crosses path - guaranteed encounter)
- Section 3: Code hack discovery (colored code hack as reward - teaches effect = color pattern)
- Section 3: Utility exploit variety (Threat Scan pickup - not all exploits are combat)
- Section 3: Ranged exploit practice (Damaged Scanner across gap - low stakes practice)
- Section 4: Ranged combat + Heat (Patrol across gap, 2 Code Injection uses, Cooling Node)
- Section 5: Synthesis (Patrol, multiple paths - tests all learned mechanics)

**Must-Add Items Not In Original Phases:**
1. `get_prologue_layout()` function in `fixed_levels.py` (GAP 1)
2. Prologue flag initialization in `engine.py` `__init__` (GAP 3)
3. ESC handler prologue check in `loop.py:883` (GAP 16)
4. `Player.reset_temporary_effects()` method (Pre-Implementation Checklist)
5. `InventoryManager.clear_all()` method (GAP 19)
6. Force `ascension_level=0` in prologue mode (GAP 24)
7. Expanded `_restart_prologue()` with full state reset (GAP 18)
8. `get_visibility_status()` in status_bar.py (prologue UI with TOO CLOSE flash, 1.5s duration)
9. Internal character voice system with `shown_thoughts` tracking
10. `reset_prologue_thoughts()` call on prologue restart
11. `prologue_spotted_in_blind_spot` flag in engine.py (Fourth Review)
12. `ENEMY_HP_OVERRIDES` dict in fixed_generator.py for X character (Fourth Review)
13. New thoughts: `melee_success`, `fov_bidirectional`, `heat_high` (Fourth Review)
14. Death restart message: "Re-establishing uplink... I know more now." (Fifth Review - improved)
15. Second Damaged Scanner in Section 3 for ranged exploit practice (Fifth Review)
16. Threat Scan exploit pickup ('E' character) in Section 3 escape area (teaches exploit variety)
17. Code hack (`d`) in Section 3 escape area (Sixth Review - relocated from Section 2)
18. New thoughts: `exploit_ranged_practice`, `utility_pickup`, `code_hack_discovery`, `intent_observe` (Fifth Review)
19. TOO CLOSE audio cue (reuse alert sound, lower volume) (Fifth Review)
20. Wall gap in Section 3 revealing gateway (Fifth Review)
21. Updated intro dialogue with "1-5 for exploits" (Fifth Review)
22. Diagonal corridor segment in Section 1 (Sixth Review)
23. New thought: `diagonal_discover` (Sixth Review)
24. Death hint system: `DEATH_HINTS` dict, `prologue_death_count`, `last_death_section` (Sixth Review)
25. `get_death_hint()` function and dialogue integration (Sixth Review)
26. New thought: `stealth_choice` for Section 5 left path (Seventh Review)
27. Heat threshold lowered to 40 for `heat_high` trigger (Seventh Review)
28. TOO CLOSE audio cue in `get_visibility_status()` (Seventh Review)
29. New thoughts: `cooling_node_use`, `cpu_node_use`, `ghost_node_use` (Eighth Review)
30. Heat-specific death hint: `heat_death` when player dies with heat > 60 (Eighth Review)
31. Admin foreshadowing in completion dialogue: "Stay too long, and something worse than guards will find you" (Eighth Review)
32. Movement queue teaching explicitly called out in Section 1 design (Eighth Review)

**Key File Touch Points:**
| File | Critical Changes |
|------|-----------------|
| `coordinator.py` | Fixed layout check BEFORE `generate_level()`, music selection at START |
| `loop.py` | Tutorial action handler + ESC auto_save wrap |
| `input/dialogue.py` | Add "UPLINK ESTABLISHED", "CONNECTION LOST", death hints, and "Re-establishing uplink..." |
| `engine.py` | `prologue_mode` param + flags + `_show_prologue_intro()` + `prologue_spotted_in_blind_spot` + `prologue_death_count` + `last_death_section` |
| `turn_manager.py` | Set `prologue_spotted_in_blind_spot` when blind spot adjacency failure detected |
| `combat.py` | Trigger `melee_success` and `heat_high` thoughts |
| `input_handler.py` | Trigger `diagonal_discover` on first diagonal move |
| `systems/death.py` | Track death section, increment `prologue_death_count`, call `get_death_hint()` |

---

## Key Issues Identified and Addressed

During plan review, the following issues were identified and corrected:

### Fixed in This Revision

1. **Return-to-Menu Flow** - Original plan invented new flags (`return_to_menu_after_dialogue`, `clean_exit_to_menu`). Corrected to use existing pattern: dialogue handler returns `False` to propagate menu return through `loop.py`.

2. **`dialogue_state.just_closed` Missing** - `DialogueState` has no such property. Corrected to use flag-based approach (`prologue_completed_pending`, `prologue_restart_pending`) checked in dialogue handler.

3. **Death Restart Missing Details** - Added explicit `pending_death_dialogue` reset and centralized restart logic in `_restart_prologue()` method in dialogue handler.

4. **Music Selection Order** - Clarified that prologue music check must be INSERTED at the START of the existing if-elif chain (after `_clear_map()`, before level checks).

5. **`prologue_completed` Settings Location** - Clarified it goes in `GameSettings.DEFAULTS` dict, not as a class attribute.

6. **Auto-Save Blocking** - Added explicit skip of `auto_save()` in prologue mode.

7. **Tutorial Integration Details** - Added Phase 4.6 with specific instantiation and integration points.

8. **`_show_prologue_intro()` Definition** - Added the missing method definition to engine.py section.

9. **Prologue Flags Initialization** - Added `prologue_completed_pending` and `prologue_restart_pending` to engine __init__.

### Verified as Correct

- Level 0 config lookup works (fallback to level 1 only if key missing)
- Map size difference (28x25 layout in 80x50 map) is handled by filling with walls
- `get_controllers()` is safe in menu context (not during gameplay)

---

## CRITICAL: Integration Points with Existing Code

Before implementing, understand these existing patterns that MUST be respected:

1. **Spawn Room**: Currently hardcoded at (2,2,8,8) with spawn at (6,6). The fixed generator can use any layout size, but the spawn position MUST be returned to `coordinator.py` for player placement.

2. **Level Generator Flow** (`generator.py:112-179`):
   ```
   generate_level() -> _generate_procedural_level() -> room/corridor/tactical generation
   ```
   The fixed level check MUST happen at the START of `generate_level()` before any procedural code runs.

3. **Item/Enemy Placement** (`coordinator.py:96-112`):
   ```
   generate_procedural_level() -> level_generator.generate_level() -> _place_*() methods
   ```
   For fixed levels, we MUST skip the `_place_*()` calls in coordinator and let the fixed generator handle placement.

4. **Music Selection** (`coordinator.py:76-87`): Music is selected AFTER `_clear_map()` but BEFORE `generate_level()`. Prologue music check must be INSERTED at the START of the music if-elif chain (before the `level == 1` check).

5. **Death Handling**: `PlayerDeathHandler` always deletes saves. Prologue exemption requires modifying this behavior. The handler has a `_handled` flag that MUST be reset with `death_handler.reset()` when restarting prologue. Also clear `pending_death_dialogue`.

6. **Network Config Keys**: `get_current_network_config()` in `state.py:226-229` looks up by `self.level` (int). The JSON key `"0"` gets converted to int `0` in `config.py:795-796`, so this works correctly. Fallback to level 1 config means level 0 MUST be explicitly defined.

7. **Main Menu Actions**: `loop.py:380-541` handles menu actions. A new `tutorial` action handler MUST be added alongside `new_game`.

8. **Return-to-Menu Flow**: Existing pattern is dialogue handler returning `False` to input handler, which propagates to `loop.py` to trigger `return True, None`. We must follow this pattern, NOT invent new flags.

9. **Map Size**: Game uses 80x50 tiles (`GameConfig.MAP_WIDTH/HEIGHT`). Fixed level will occupy top-left portion; rest is filled with walls.

10. **Auto-Save Blocking**: `coordinator.py` calls `auto_save()` after level generation. In prologue mode, this MUST be skipped.

---

## Phase 1: Data Layer

### 1.1 Add Prologue Network Config to `game_content.json`

Add a new `"0"` entry to `network_configs` (place BEFORE the `"1"` entry):

```json
"0": {
  "enemies": 3,
  "blind_spot_coverage": 0.15,
  "name": "First Infiltration",
  "background_trace": 0,
  "trace_alert_to_hostile": 5,
  "trace_continuous_hostile": 0,
  "cooling_nodes": 1,
  "cpu_nodes": 1,
  "ghost_nodes": 1,
  "code_hacks": 2,
  "exploit_pickups": 3,
  "permanent_upgrades": 0,
  "is_prologue": true,
  "fixed_layout": true
}
```

**IMPORTANT**: These counts are IGNORED for fixed layouts - they're only here for API compatibility. The fixed layout defines exact positions for all entities. (Note: `exploit_pickups: 3` for Code Injection + Threat Scan + one more if needed)

Key differences from normal levels:
- `background_trace: 0` - No passive trace gain (don't punish slow play)
- `trace_alert_to_hostile: 5` - Small trace penalty when spotted (teaches trace EXISTS)
- `trace_continuous_hostile: 0` - No continuous trace from combat (keeps it simple)
- `is_prologue: true` - Flag for special handling (death behavior, skip logic)
- `fixed_layout: true` - Use hand-designed layout instead of procedural generation

**Design philosophy**: Minimal trace in prologue (5% per alert). Players see the Trace indicator increase when spotted, teaching them that detection has consequences beyond immediate danger. They won't hit 100% in a normal playthrough, but they'll understand trace matters before Level 1.

**NOTE**: The `is_prologue` and `fixed_layout` flags must be checked in:
- `generator.py:generate_level()` - to skip procedural generation
- `coordinator.py:generate_procedural_level()` - to skip random item/enemy placement
- `coordinator.py:progress_to_next_level()` - to handle prologue completion
- `systems/death.py:PlayerDeathHandler` - to skip save deletion in prologue

### 1.2 Add Prologue Narrative Content to `narrative_content.json`

Add new entries:

```json
"prologue_messages": {
  "intro": "Remote uplink active. Reach the gateway.",
  "completion": "Gateway reached. You are ready.\n\nThe real networks won't be this forgiving. Stay too long, and something worse than guards will find you.",
  "death": "CONNECTION LOST",
  "restart": "Re-establishing uplink... I know more now."
},
"prologue_thoughts": {
  "diagonal_discover": "Diagonal movement... that's faster.",
  "melee_success": "Walking into them... that works.",
  "turn_based_observe": "It moves when I move...",
  "wait_fail": "Should have waited for it to pass.",
  "wait_success": "Timing. That's the key.",
  "fov_bidirectional": "If I can see them, they can see me.",
  "blindspot_observe": "A blind spot... they might not see me here.",
  "blindspot_adjacent_fail": "Too close! They can see right past it.",
  "blindspot_range_success": "The blind spot worked... but only because I kept my distance.",
  "alert_to_hostile_fail": "Too slow! Should have broken line of sight faster.",
  "alert_escape_success": "Breaking line of sight... that bought me time.",
  "exploit_observe": "Can't reach them from here... maybe an exploit would work.",
  "exploit_success": "The exploit worked. Good to know.",
  "exploit_ranged_practice": "The exploit worked from a distance. Useful.",
  "utility_pickup": "This one reveals enemy vision... not all exploits are weapons.",
  "code_hack_discovery": "The effect matched the color. Worth remembering.",
  "intent_observe": "I can see where it's going... the next three moves.",
  "heat_high": "Running hot... need to cool down.",
  "cooling_node_use": "Heat dissipating... these nodes are useful.",
  "cpu_node_use": "Systems restored. Good to know these exist.",
  "ghost_node_use": "Invisible... but only for a moment.",
  "stealth_choice": "The quieter route. Worth the extra steps.",
  "gateway_spotted": "The gateway. Almost there."
},
"prologue_death_hints": {
  "section_1": "Next time, wait for an opening...",
  "section_2": "Distance matters. Too close and they see through everything.",
  "section_3": "Need to break their line of sight faster.",
  "section_4": "There must be a way to reach them from here...",
  "section_5": "Patience. Watch the pattern.",
  "heat_death": "Overheated... those nodes might help next time."
}
```

**Design note**: Only four system messages (intro/completion/death/restart). The `prologue_thoughts` are reactive - triggered by player actions (observations, failures, successes), not pre-emptive instructions. This feels like natural internal monologue, not a tutorial system.

**New thoughts added (Fourth Review):**
- `melee_success`: Teaches bump-to-attack after killing Damaged Scanner
- `fov_bidirectional`: Teaches that vision works both ways when first spotted
- `exploit_observe`: Now more helpful - mentions exploits explicitly
- `heat_high`: Teaches heat management when heat exceeds threshold

**New thoughts added (Fifth Review):**
- `exploit_ranged_practice`: Confirms ranged exploit use in low-stakes practice
- `utility_pickup`: Teaches that exploits have variety beyond damage
- `code_hack_discovery`: Teaches color = effect pattern for code hacks
- `intent_observe`: Teaches reading enemy movement queue (next 3 moves visible)
- `gateway_spotted`: Triggers when gateway enters FOV
- `restart`: Updated to acknowledge player learning ("I know more now")

**New elements added (Sixth Review):**
- `diagonal_discover`: Teaches 8-directional movement when player first moves diagonally
- `prologue_death_hints`: Section-specific reflections shown after death (implicit, not explicit tips)
- Code hack relocated from Section 2 to Section 3 (cleaner lesson separation)

**New elements added (Seventh Review):**
- `stealth_choice`: Acknowledges player choice when taking left (stealth) path in Section 5
- `intent_observe`: Updated to explicitly mention "next three moves" (the movement queue)
- Permadeath foreshadowing added to completion dialogue
- Heat threshold for `heat_high` lowered to 40 (triggers after 2 Code Injections at 20 heat each)
- TOO CLOSE audio cue implementation details added to Phase 4.5

**New elements added (Eighth Review):**
- Node usage thoughts: `cooling_node_use`, `cpu_node_use`, `ghost_node_use` (confirms node mechanics work)
- Heat-specific death hint: `heat_death` shown when player dies with heat > 60 (replaces section-based hint)
- Admin foreshadowing: Completion dialogue now hints at 100% trace consequence ("something worse than guards")
- Movement queue teaching: Section 1 explicitly teaches reading the 3-move enemy intent display
- Section 5 branching clarity: LEFT (safer, ghost node reward) vs RIGHT (faster, riskier) tradeoff documented

**Death hints philosophy**: Death hints are phrased as internal reflections ("Next time, wait for an opening...") rather than explicit instructions ("Tip: Press '.' to wait"). This maintains the show-don't-tell approach even when providing post-death guidance.

**Heat death detection**: If player dies with heat > 60 (indicating exploit overuse), show `heat_death` hint instead of section-based hint. This provides specific guidance for the actual cause of death.

**What was removed**: 8 external hint messages (movement, shadow, stealth attack, exploit, node, code hack, gateway). These are replaced by sparse internal thoughts triggered by specific situations.

### 1.3 Add Prologue Tracking to User Settings

File: `src/rsp/core/config.py` - Add to `GameSettings.DEFAULTS` dict (around line 62-87):

```python
DEFAULTS = {
    # ... existing defaults ...
    "prologue_completed": False,  # NEW: Track if player has finished tutorial
}
```

This follows the existing pattern where settings are defined in DEFAULTS and automatically loaded/saved by `_apply_settings_from_dict()` and `_get_settings_as_dict()`.

File: `saves/user_settings.json` schema update (happens automatically on save):
```json
{
  "prologue_completed": false
}
```

### 1.4 Files to Modify

| File | Changes |
|------|---------|
| `game_content.json` | Add `"0"` network config with prologue settings |
| `narrative_content.json` | Add `prologue_messages` section |
| `src/rsp/core/config.py` | Add `prologue_completed` to `GameSettings` |

---

## Phase 2: Fixed Level Generator

### 2.1 Create New Module: `src/rsp/level/fixed_levels.py`

This module defines hand-designed level layouts using a simple ASCII map format.

```python
"""
Fixed level layouts for tutorial and special levels.

Provides hand-designed maps that bypass procedural generation.
Uses ASCII art format for easy level design and modification.

INTEGRATION: Called from LevelGenerator.generate_level() when network_config
has fixed_layout=true. Returns spawn position and skips all procedural generation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from rsp.entities.base import Position

# Map legend:
# '#' = Wall
# '.' = Floor
# 's' = Blind spot
# '@' = Player spawn
# '>' = Gateway (exit)
# 'c' = Cooling node
# 'r' = CPU recovery node
# 'g' = Ghost node
# 'X' = Damaged Scanner (5 HP, 0 damage - melee teaching)
# 'S' = Scanner enemy (STATIC, vision 5)
# 'P' = Patrol enemy (PATROL routes) - used for all mobile enemies in prologue
# 'e' = Exploit pickup (Code Injection - ranged combat)
# 'E' = Exploit pickup (Threat Scan - utility, not combat)
# 'd' = Code hack (data code)
# '+' = Door/passage marker (floor tile, visual only)

@dataclass
class FixedLevelData:
    """Container for fixed level layout data."""
    layout: List[str]                    # ASCII map rows (y=0 is top)
    name: str = "Fixed Level"            # Display name
    tutorial_triggers: Dict[str, Position] = field(default_factory=dict)
    enemy_overrides: Dict[str, Dict] = field(default_factory=dict)  # Per-enemy HP/behavior overrides

    @property
    def width(self) -> int:
        return len(self.layout[0]) if self.layout else 0

    @property
    def height(self) -> int:
        return len(self.layout)

    def get_char(self, x: int, y: int) -> str:
        """Get character at (x, y), '#' if out of bounds."""
        if 0 <= y < len(self.layout) and 0 <= x < len(self.layout[y]):
            return self.layout[y][x]
        return '#'
```

### 2.2 Create Prologue Layout Definition

Design goals for the prologue map:
- Size: 28x25 tiles
- **Teaches correct mechanics**: Blind spots work at RANGE, not adjacent
- Linear progression: Turn-based → Blind Spots → Alert/Escape → Combat → Choice
- Each section can be completed multiple ways (stealth encouraged, combat allowed)
- **ALL REAL MECHANICS**: Only uses elements that exist in the actual game

```python
PROLOGUE_LAYOUT = """
############################
#@..##..P.+.e.............#
#..X##....#...............#
#...+.....#...............#
#...#.....#...............#
####+#####################
#....+....................#
#....#.....sssssS.........#
#....#....................#
#....#..sss...............#
#....#..sss...............#
#....#....................#
####+#########+###########
#....+.........+....sss...#
#....#....P....#....sss...#
#....#....+....#..Edrss...#
#....#....+....+....sss...#
################....###+###
#....#..c..############...#
#....#.....####P####......#
#....+.....####.####......#
####+########.....##..+.###
#sss.+.....g.......#....+>#
#sss.#.........P...#..sss.#
############################
"""
```

**Layout changes from review (2026-01-07):**
1. **Section 1 observation**: Patrol moved to row 1, visible from spawn. Player observes turn-based movement BEFORE killing X.
2. **Section 4 predictability**: Bot replaced with Patrol. Patrols follow routes (predictable), Bots wander (could leave zone). Wall added above to constrain movement.

**Layout changes from Sixth Review (2026-01-07):**
3. **Diagonal corridor added (Section 1)**: L-shaped path from spawn - walls create corner where diagonal cuts through (2 moves diagonal vs 3 orthogonal). Player at (1,1) can reach (3,3) diagonally or go around.
4. **Code hack relocated (Section 2 → 3)**: Moved `d` from Section 2 blind spots to Section 3 escape area (row 15, near `r` CPU node). Section 2 now focuses purely on blind spot range mechanics.

**Layout changes from Seventh Review (2026-01-07):**
5. **Section 2 blind spot trap FIXED**: Blind spot trail (`sssssS`) now leads directly TO Scanner. Old layout had blind spots on wrong side of room.
6. **Threat Scan in Section 3**: Added `E` character for Threat Scan in Section 3 escape area (with code hack and CPU node). Teaches that not all exploits are combat-focused.
7. **Section 5 branching added**: Two distinct paths to gateway (LEFT=stealth with ghost node, RIGHT=combat/direct). Creates meaningful player choice.
8. **Minimal trace added**: Changed `trace_alert_to_hostile` from 0 to 5. Players see trace increase when spotted (teaches mechanic exists).
9. **Death hints simplified**: Removed explicit key instructions ("Press '.' to wait"), replaced with implicit reflections ("Next time, wait for an opening...").

**ALL elements are real game mechanics (from game_content.json):**
- `X` = Damaged Scanner (STATIC - 5 HP, vision 5, 0 damage - teaches melee combat safely)
- `P` = Patrol (PATROL movement - follows routes, damage 10) - used in Sections 1, 3, 4, 5
- `S` = Scanner (STATIC - doesn't move, vision 5, 0 damage)
- `s` = Blind spot (hides player at range > 1 ONLY - adjacent enemies see through!)
- `c/r/g` = Nodes (real items)
- `e` = Code Injection exploit (guaranteed ranged for Section 4)
- `E` = Threat Scan exploit (utility - Section 3 escape reward, teaches exploit variety)
- `d` = Code hack (Section 3 - reward after alert escape)

**Enemy usage reasoning:**
- Patrol (P): Used in ALL sections with mobile enemies - predictable routes enable guaranteed teaching
- Scanner (S): Used in Section 2 - STATIC, can't chase, safe to fail against when learning
- Bot NOT used: RANDOM movement could leave teaching zone; replaced with constrained Patrol

### 2.3 Implement FixedLevelGenerator Class

File: `src/rsp/level/fixed_generator.py`

```python
"""
Fixed level generator for hand-designed levels.

INTEGRATION FLOW:
1. LevelGenerator.generate_level() checks config for fixed_layout=true
2. If true, calls FixedLevelGenerator.generate_from_layout() INSTEAD of _generate_procedural_level()
3. FixedLevelGenerator populates game_map directly and returns spawn position
4. LevelGenerator skips all procedural steps (room gen, corridor gen, etc.)
5. GameLevelCoordinator.generate_procedural_level() checks is_prologue flag
6. If is_prologue=true, skips _place_enemies(), _place_code_hacks(), etc.

This ensures fixed layout content is used without random placement interference.
"""

import logging
import random
from typing import List, Tuple, Dict, Optional

from rsp.combat.inventory import CodeHack, ExploitItem
from rsp.core.data import GameData
from rsp.entities.base import Position
from rsp.entities.characters import Enemy
from rsp.level.fixed_levels import FixedLevelData


class FixedLevelGenerator:
    """
    Generates levels from fixed ASCII layouts.

    Used for tutorial levels and special hand-designed areas.
    Directly populates GameMap with walls, floors, nodes, and entities.

    ALL REAL GAME MECHANICS - no tutorial-only elements.
    """

    # Character to tile type mapping (ALL REAL GAME ELEMENTS)
    FLOOR_CHARS = {'.', '@', '>', 'c', 'r', 'g', 'X', 'S', 'P', 'e', 'E', 'd', '+', 's'}
    ENEMY_CHARS = {'X': 'scanner', 'S': 'scanner', 'P': 'patrol'}  # X = damaged scanner
    NODE_CHARS = {'c': 'cooling', 'r': 'cpu', 'g': 'ghost'}
    ITEM_CHARS = {'e': 'exploit', 'E': 'threat_scan', 'd': 'code_hack'}
    # Special enemy HP overrides (X = damaged scanner, Section 4 patrol needs 2 exploits)
    ENEMY_HP_OVERRIDES = {'X': 5}  # Damaged Scanner has 5 HP (one-shot with melee)

    def __init__(self, game_map, game_engine=None):
        self.game_map = game_map
        self.game_engine = game_engine  # Needed for code_hack_effects

    def generate_from_layout(
        self,
        layout_data: FixedLevelData,
        level: int = 0
    ) -> Tuple[Position, List[Enemy]]:
        """
        Generate map from fixed layout, populating game_map directly.

        IMPORTANT: This method handles ALL placement - walls, floors, blind spots,
        nodes, items, and enemies. The coordinator MUST NOT run its placement methods.

        Args:
            layout_data: FixedLevelData with ASCII layout
            level: Level number (0 for prologue)

        Returns:
            Tuple of (player_spawn_position, list_of_enemies)
        """
        spawn_pos = None
        enemies = []

        # Clear existing map data (walls will be set, everything else cleared)
        self._clear_map_data()

        # First pass: Fill entire map with walls
        for y in range(self.game_map.height):
            for x in range(self.game_map.width):
                self.game_map.walls.add((x, y))

        # Second pass: Parse layout and carve out floors/features
        for y in range(layout_data.height):
            for x in range(layout_data.width):
                char = layout_data.get_char(x, y)

                # Carve floor tiles
                if char in self.FLOOR_CHARS:
                    self.game_map.walls.discard((x, y))

                # Handle special characters (ALL REAL GAME ELEMENTS)
                if char == '@':
                    spawn_pos = Position(x, y)
                elif char == '>':
                    self.game_map.gateway = Position(x, y)
                elif char == 's':
                    self.game_map.blind_spots.add((x, y))
                elif char in self.NODE_CHARS:
                    self._place_node(x, y, self.NODE_CHARS[char])
                elif char in self.ENEMY_CHARS:
                    enemy = self._create_enemy(
                        x, y, self.ENEMY_CHARS[char], layout_data, layout_char=char
                    )
                    enemies.append(enemy)
                elif char in self.ITEM_CHARS:
                    self._place_item(x, y, self.ITEM_CHARS[char], level)

        if spawn_pos is None:
            logging.error("Fixed level has no player spawn (@)! Using (1,1)")
            spawn_pos = Position(1, 1)

        # Invalidate caches
        self.game_map.invalidate_transparency_cache()

        logging.info(
            f"Fixed level generated: {layout_data.width}x{layout_data.height}, "
            f"spawn={spawn_pos}, enemies={len(enemies)}, gateway={self.game_map.gateway}"
        )

        return spawn_pos, enemies

    def _clear_map_data(self):
        """Clear all existing map data before generating."""
        self.game_map.walls.clear()
        self.game_map.blind_spots.clear()
        self.game_map.used_blind_spots.clear()
        self.game_map.cooling_nodes.clear()
        self.game_map.cpu_recovery_nodes.clear()
        self.game_map.ghost_nodes.clear()
        self.game_map.code_hacks.clear()
        self.game_map.exploit_pickups.clear()
        self.game_map.permanent_upgrades.clear()
        self.game_map.story_fragments.clear()
        self.game_map.explored_tiles.clear()
        self.game_map.gateway = None

    def _place_node(self, x: int, y: int, node_type: str):
        """Place a special node at position."""
        from rsp.level.map import RestoreNode
        if node_type == 'cooling':
            self.game_map.cooling_nodes[(x, y)] = RestoreNode(node_type="cooling")
        elif node_type == 'cpu':
            self.game_map.cpu_recovery_nodes[(x, y)] = RestoreNode(node_type="cpu")
        elif node_type == 'ghost':
            self.game_map.ghost_nodes[(x, y)] = RestoreNode(node_type="ghost")

    def _create_enemy(
        self, x: int, y: int, enemy_type: str, layout_data: FixedLevelData,
        layout_char: str = None
    ) -> Enemy:
        """Create enemy with optional tutorial HP overrides.

        Uses REAL enemy types only - scanner, bot, patrol.
        X = Damaged Scanner (5 HP) for melee teaching.

        Args:
            x, y: Position
            enemy_type: The actual enemy type (scanner, bot, patrol)
            layout_data: Layout data with optional overrides
            layout_char: Original character from layout (e.g., 'X' for damaged scanner)
        """
        enemy = Enemy(Position(x, y), enemy_type)

        # Apply HP override from layout character (e.g., X = damaged scanner)
        if layout_char and layout_char in self.ENEMY_HP_OVERRIDES:
            enemy.cpu = self.ENEMY_HP_OVERRIDES[layout_char]
            enemy.max_cpu = self.ENEMY_HP_OVERRIDES[layout_char]
        # Also check layout_data overrides for additional customization
        elif enemy_type in layout_data.enemy_overrides:
            overrides = layout_data.enemy_overrides[enemy_type]
            if 'hp' in overrides:
                enemy.cpu = overrides['hp']
                enemy.max_cpu = overrides['hp']

        return enemy

    def _place_item(self, x: int, y: int, item_type: str, level: int = 0):
        """Place an item at position."""
        if item_type == 'exploit':
            # Prologue: Always place Code Injection (ranged) to guarantee Section 4 works
            # Regular levels: Random exploit from pool
            if level == 0:
                exploit_key = "code_injection"  # Range 5, ensures player can hit Patrol across gap
            else:
                exploit_key = random.choice(list(GameData.EXPLOITS.keys()))
            exploit_def = GameData.EXPLOITS[exploit_key]
            self.game_map.exploit_pickups[(x, y)] = ExploitItem(exploit_key, exploit_def)
        elif item_type == 'threat_scan':
            # Always place Threat Scan - utility exploit that reveals enemy vision
            exploit_key = "threat_scan"
            exploit_def = GameData.EXPLOITS[exploit_key]
            self.game_map.exploit_pickups[(x, y)] = ExploitItem(exploit_key, exploit_def)
        elif item_type == 'code_hack':
            # Create code hack with random color
            if self.game_engine and self.game_engine.code_hack_effects:
                color = random.choice(list(self.game_engine.code_hack_effects.keys()))
                effect, desc = self.game_engine.code_hack_effects[color]
                code = CodeHack(
                    color_name=color, effect=effect,
                    name=f"{color.title()} Code", description=desc
                )
                self.game_map.code_hacks[(x, y)] = code
```

### 2.4 Files to Create

| File | Purpose |
|------|---------|
| `src/rsp/level/fixed_levels.py` | Fixed level data definitions |
| `src/rsp/level/fixed_generator.py` | Fixed level generation logic |

### 2.5 Files to Modify

| File | Changes |
|------|---------|
| `src/rsp/level/coordinator.py` | Add fixed layout check at START of `generate_procedural_level()` |
| `src/rsp/level/__init__.py` | Export new classes |

**`__init__.py` exports to add:**
```python
from rsp.level.fixed_levels import FixedLevelData, get_prologue_layout
from rsp.level.fixed_generator import FixedLevelGenerator
```

**NOTE**: `generator.py` does NOT need modification - all fixed level logic goes in coordinator.

### 2.6 CRITICAL: Coordinator-Based Fixed Level Check (REVISED)

**PROBLEM**: `LevelGenerator` does NOT have a `game_engine` reference (see `generator.py:78`). Adding one would require updating many test files.

**SOLUTION**: Check for fixed layout in `coordinator.py` BEFORE calling `generate_level()`. The coordinator already has `game_engine` access.

**NO changes needed to generator.py** - the fixed level generation happens entirely in coordinator.

File: `src/rsp/level/coordinator.py` - modify `generate_procedural_level()`:

```python
def generate_procedural_level(self, skip_level_start_message: bool = False):
    """Generate a complete level with map structure and gameplay elements."""
    self._clear_map()

    config = self.game_engine.game_state.get_current_network_config()
    is_fixed_layout = config.get("fixed_layout", False)
    is_prologue = getattr(self.game_engine, 'prologue_mode', False)

    # Music selection - INSERT prologue check at START of the chain
    if is_prologue:
        self.game_engine.sound_manager.play_music(
            "level1_stealth.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME
        )
    elif self.game_engine.level == 1:
        # ... existing level 1 music code ...
    elif self.game_engine.level == 2:
        # ... existing level 2 music code ...
    elif self.game_engine.level == 3:
        # ... existing level 3 music code ...

    # CRITICAL: Fixed layout check BEFORE calling generate_level()
    if is_fixed_layout:
        from rsp.level.fixed_generator import FixedLevelGenerator
        from rsp.level.fixed_levels import get_prologue_layout

        fixed_gen = FixedLevelGenerator(self.game_engine.game_map, self.game_engine)
        layout = get_prologue_layout()
        spawn_pos, enemies = fixed_gen.generate_from_layout(layout, self.game_engine.level)

        # Add enemies to enemy_manager
        for enemy in enemies:
            self.game_engine.enemy_manager.enemies.append(enemy)

        # Set player spawn position
        self.game_engine.player.x = spawn_pos.x
        self.game_engine.player.y = spawn_pos.y

        # Post-generation integration (same as procedural path)
        self.game_engine.narrative_manager.reset_level_flags()
        self.game_engine.game_session.turn_manager.reset_blind_spot_tracking()
        self.game_engine.message_log.add_message(f"{config['name']} loaded")
        self.game_engine.game_map.invalidate_transparency_cache()
        self.game_engine.visibility_manager.invalidate_cache()

        # Skip all item/enemy placement for fixed layouts (already handled)
    else:
        # Procedural generation (existing code)
        self.game_engine.level_generator.generate_level(
            self.game_engine.level,
            self.game_engine.game_state.dungeon_seed,
            self.game_engine.ascension_modifiers,
        )

        # Generate additional game elements (existing code)
        # ... _place_code_hacks, _place_exploit_pickups, etc. ...

        # Find spawn position (existing code)
        spawn_pos = self._find_valid_spawn_position()
        self.game_engine.player.x = spawn_pos.x
        self.game_engine.player.y = spawn_pos.y

    # Reset player state (common to both paths)
    self.game_engine.player.trace_level = 0
    self.game_engine.admin_spawned = False
    # ... rest of existing code ...
```

**Also update `progress_to_next_level()`** to skip auto_save in prologue:

```python
def progress_to_next_level(self):
    # ... prologue completion handling from Phase 5.4 ...

    # Near end of existing code, wrap auto_save:
    if not getattr(self.game_engine, 'prologue_mode', False):
        self.game_engine.auto_save()
```

This approach:
- Keeps `generator.py` unchanged
- No test file modifications needed
- All fixed level logic contained in coordinator
- Clear separation of concerns
- Blocks save during prologue

---

## Phase 3: Prologue Level Design

### 3.1 Level Layout Philosophy - Encourage, Don't Force

**Core principle**: Layout makes optimal behavior EASIER, not mandatory. Player can always fight - stealth is just more efficient.

**MECHANIC CONSTRAINTS (from code analysis):**
- Blind spots only hide at range > 1. Adjacent enemies SEE THROUGH.
- Alert state gives 1 turn grace to break LOS before HOSTILE.
- Player CAN kill any enemy with exploits. Can't block combat path.
- Patrols return to routes after player escapes.

**ENEMY SELECTION:**
- **Patrol** (PATROL movement): All mobile enemies - predictable routes for reliable teaching
- **Scanner** (STATIC): For blind spot range lesson (can't chase, safe to learn from)

```
SECTION 1: The Chokepoint (teaches TURN-BASED + WAIT + MOVEMENT QUEUE)
- Narrow corridor with Patrol walking back and forth
- Patrol BLOCKS the only passage - player MUST wait for opening
- Player discovers: when I move, it moves. Pressing '.' lets me wait.
- MOVEMENT QUEUE VISIBLE: Patrol's next 3 moves shown - player can read pattern
- Thought triggers: "It moves when I move..." then "I can see where it's going..."
- Exploit pickup AFTER the chokepoint (reward for learning WAIT)
- CRITICAL: This teaches turn-based, waiting, AND reading enemy intent

SECTION 2: The Blind Spot Trap (teaches blind spots work AT DISTANCE ONLY)
- Scanner at end of corridor (STATIC, vision 5)
- Blind spot tiles line the OBVIOUS direct path to Scanner
- Player walks through blind spots toward Scanner - feels safe
- At range 1 (adjacent): SPOTTED despite being in blind spot!
- Adjacent enemies see PAST blind spots - this is the key lesson
- Scanner is STATIC so consequence is minor (alert, not death)
- Alternate path visible: blind spots at range 3-4 from Scanner
- Thoughts: "Too close! They can see right past it." then later
  "The blind spot worked... but only because I kept my distance."
- CRITICAL: Forces the failure state so player learns the range rule

SECTION 3: The Patrol Route (teaches ALERT grace period)
- Patrol follows predictable route that CROSSES player's entry path
- Player WILL be spotted (guaranteed teaching moment)
- Blind spot cluster at far side (range > 1 from patrol route)
- Player experiences: spotted -> ALERT -> flee -> break LOS -> de-escalate
- CPU recovery node in blind spot rewards successful escape
- Thought: "They saw me! But I broke the line of sight..."
- Uses Patrol (PATROL) for guaranteed encounter - predictable movement

SECTION 4: The Gap (teaches ranged exploits)
- Patrol visible across wall gap (melee clearly impossible)
- Player has exploit from Section 1
- Use ranged exploit OR take long winding path (exploit is faster)
- Cooling node for heat recovery after combat
- Thought: "Can't reach them from here... but my exploit might."

SECTION 5: Final Approach (player choice - branching synthesis)
- TWO distinct paths to gateway (LEFT and RIGHT)
- LEFT path: Stealth approach with blind spots + ghost node reward (safer, slower)
- RIGHT path: Shorter but exposed - faster if you can handle combat (riskier, faster)
- CLEAR TRADEOFF: Ghost node (temporary invisibility) vs speed
- Patrol guards the center area between paths
- Multiple valid strategies:
  a) Left stealth: Time patrol, use blind spots, collect ghost node
  b) Right combat: Fight through, accept trace/resource cost
  c) Mixed: Start one path, adapt based on patrol position
- Gateway clearly visible - player owns their strategy
- This section tests everything learned, doesn't teach new mechanics
- Thought on left path: "The quieter route. Worth the extra steps."
```

**Design principles**:
- **Encourage, don't force**: Stealth is easier/cheaper, not mandatory
- **Teach through consequence**: Getting spotted = trace increase, not instant death
- **Range matters**: Blind spots demonstrated at distance first
- **Combat is valid**: Always an option, just resource-expensive

### 3.2 Detailed ASCII Layout (28x25)

```
Legend:
# = Wall           . = Floor          s = Blind spot
@ = Player spawn   > = Gateway        c = Cooling node
r = CPU recovery   g = Ghost node     S = Scanner (STATIC, vision 5)
X = Damaged Scanner (STATIC, 5 HP, 0 damage - melee teaching)
P = Patrol (PATROL routes)
e = Exploit pickup (Code Injection - ranged combat)
E = Exploit pickup (Threat Scan - utility, not combat)
d = Code hack (teaches color = effect discovery)
+ = Doorway

############################
#@..##..P.+.e.............#  <- SECTION 1a: DIAGONAL + OBSERVATION + MELEE
#..X##....#...............#     Diagonal shortcut past wall corner (2 vs 3 moves)
#...+.....#...............#     Patrol visible - observe turn-based movement
#...#.....#...............#     X blocks exit - teaches bump-to-attack
####+#####################  <- SECTION 1b: THE CHOKEPOINT
#....+....................#     Door leads to corridor - time the Patrol
#....#.....sssssS.........#  <- SECTION 2: THE BLIND SPOT TRAP
#....#....................#     Blind spots lead TO Scanner - feels safe...
#....#..sss...............#     At range 1 (adjacent): SPOTTED! (TOO CLOSE!)
#....#..sss...............#     SAFE blind spots at range 5+ from Scanner
#....#....................#     Learn: blind spots only work at DISTANCE
####+#########+###########
#....+.........+....sss...#  <- SECTION 3: THE PATROL ROUTE
#....#....P....#....sss...#     Patrol route CROSSES player entry
#....#....+....#..Edrss...#     Escape rewards: Threat Scan (E), code hack (d), CPU (r)
#....#....+....+....sss...#     Flee to blind spots, code hack + CPU node reward
################....###+###
#....#..c..############...#  <- SECTION 4: THE GAP
#....#.....####P####......#     Patrol across gap - needs ranged exploit
#....+.....####.####......#     Walls constrain movement, Cooling Node nearby
####+########.....##..+.###  <- SECTION 5: FINAL APPROACH (BRANCHING)
#sss.+.....g.......#....+>#     LEFT: Stealth path (blind spots + ghost node)
#sss.#.........P...#..sss.#     RIGHT: Combat/direct path to gateway
############################     Player chooses strategy - synthesis of all mechanics
```

**How each section teaches mechanics:**

| Section | Mechanic | Layout Design | Why It Works |
|---------|----------|---------------|--------------|
| 1a | Diagonal movement | L-shaped wall corner near spawn | Diagonal cuts corner (2 moves vs 3) - natural discovery |
| 1a | Turn-based observation | Patrol visible from spawn row | Player sees "it moves when I move" BEFORE any risk |
| 1a | Melee combat | Damaged Scanner blocks exit | MUST bump to attack - safe first combat (0 damage enemy) |
| 1b | WAIT action + Movement queue | Patrol blocks corridor access | MUST time entry - movement queue shows next 3 moves to help |
| 2 | Blind spots at RANGE | Blind spot trail leads TO Scanner | Forces failure when adjacent + TOO CLOSE feedback |
| 3 | Alert + FOV bidirectionality | Patrol route crosses entry | Guaranteed encounter - "If I see them, they see me" |
| 3 | Non-combat exploit (Threat Scan) | Threat Scan in escape area | Teaches not all exploits are weapons |
| 3 | Code hack discovery | Code hack near CPU node in escape area | Reward after escaping - teaches color = effect |
| 4 | Ranged exploits + Heat | Patrol across gap (constrained), Code Injection guaranteed | Predictable target, Cooling Node teaches recovery |
| 4 | Node usage (Cooling) | Cooling node after combat | Natural use point - player just generated heat |
| 5 | Synthesis + Branching | LEFT stealth path vs RIGHT combat path | Player chooses strategy - Ghost node vs speed tradeoff |

**Critical layout requirements:**
- Section 1a: L-shaped wall creates diagonal shortcut opportunity (optional but faster)
- Section 1a: Damaged Scanner blocks ONLY exit - player must learn melee to proceed
- Section 1b: Patrol blocks ONLY path - player cannot proceed without waiting
- Section 2: Blind spot trail (`sssssS`) leads directly TO Scanner - trap triggers when adjacent
- Section 2: Safe blind spots at range 5+ from Scanner (alternate path after learning trap)
- Section 3: Patrol route MUST cross player entry point - guaranteed spotting
- Section 3: Escape area rewards: Threat Scan (utility exploit), code hack, CPU node
- Section 3: Blind spots at FAR side - player must flee TO them, not start in them
- Section 4: Wall gap wide enough that melee is clearly impossible
- Section 5: TWO distinct paths to gateway (LEFT=stealth, RIGHT=combat)
- Section 5: Left path has blind spots + ghost node (rewards stealth)
- Section 5: Right path more exposed but direct (combat viable)

### 3.3 Enemy Configuration

| Section | Enemy | Type | Behavior | HP | Why This Enemy |
|---------|-------|------|----------|-----|----------------|
| 1a | X | scanner | STATIC | 5 | Damaged Scanner - teaches melee (0 damage, safe first combat) |
| 1b | P | patrol | PATROL | 40 | Blocks corridor - forces WAIT. Predictable = learnable |
| 2 | S | scanner | STATIC | 35 | Doesn't move/chase - safe to fail against when learning |
| 3 | P | patrol | PATROL | 40 | Predictable route crosses entry - GUARANTEED encounter |
| 4 | P | patrol | PATROL | 40 | Constrained patrol across gap - needs 2 Code Injection hits (25 dmg each) |
| 5 | P | patrol | PATROL | 40 | Predictable route - timing is optional strategy |

**Why these enemy choices work:**

| Enemy | Key Trait | Tutorial Use |
|-------|-----------|--------------|
| Damaged Scanner (X) | STATIC, 5 HP, 0 damage | Perfect for first combat - can't hurt player, teaches bump-to-attack |
| Scanner | STATIC (won't chase) | Perfect for blind spot failure - player learns safely |
| Patrol | PATROL (predictable) | Guarantees teaching moments - player can learn patterns |

**Enemy behaviors (from game_content.json):**
- **Damaged Scanner (X)**: STATIC, vision 5, 0 damage, 5 HP - Special tutorial enemy, same AI as Scanner
- **Scanner**: STATIC, vision 5, 0 damage - Can only watch, never attacks
- **Patrol**: PATROL, vision 4, 10 damage - Follows routes, attacks if hostile

**Important notes:**
1. All enemies use NORMAL AI - no tutorial-specific behavior
2. Damaged Scanner (X) is a regular Scanner with reduced HP (5) - not a new enemy type
3. Scanner in Section 2 can't chase - if player is spotted, they just get alert (safe failure)
4. Section 4 uses Patrol (not Bot) - predictable movement stays in range for ranged combat lesson
5. Section 4 Patrol has 40 HP (default) - requires 2 Code Injection uses (25 damage each), teaches heat
6. Trace has minimal penalty (5% per alert) - teaches trace EXISTS without harsh punishment

### 3.4 Item Placement

| Item | Section | Position Purpose |
|------|---------|-----------------|
| Code Injection (e) | Section 1 | Ranged exploit (range 5) - guarantees Section 4 works |
| Threat Scan (E) | Section 3 escape | Utility exploit - teaches not all exploits are weapons |
| CPU Recovery (r) | Section 3 escape | Reward for fleeing to blind spots after Patrol spots them |
| Code Hack (d) | Section 3 escape | Teaches color = effect pattern |
| Cooling Node (c) | Section 4 | Available after exploit use (teaches heat management naturally) |
| Ghost Node (g) | Section 5 LEFT path | Rewards stealth approach to final area |

**Placement philosophy**: Items are positioned as rewards/tools for the situation they're in, not randomly scattered. Player learns what items do by USING them in context.

**Key timing**:
- Code Injection is picked up in Section 1 but not NEEDED until Section 4. Player has time to notice it.
- Threat Scan, code hack, and CPU recovery are all in the Section 3 escape area - rewards for surviving the patrol encounter.

**Why Code Injection is guaranteed**: Section 4 requires ranged combat across a gap. If the player only had melee exploits (Buffer Overflow), they'd be stuck. Code Injection (range 5, 25 damage) ensures the lesson works.

**Why Threat Scan is in Section 3**: Teaches that exploits aren't just weapons. Player gets a utility exploit as a reward for escaping the patrol, demonstrating variety before Level 1.

### 3.5 Tutorial Triggers - REMOVED

**Design decision**: The original plan included 6 position-based tutorial triggers that would display hint messages. These have been REMOVED.

**Rationale**:
- The redesigned layout teaches through environmental necessity, not text
- Position triggers interrupt flow and feel patronizing
- If the layout requires explanation, the layout needs work

**What remains**: Only the intro dialogue (explains the context) and completion dialogue (celebrates success). No mid-game hints.

**Exception - single optional hint**: If playtesting shows players consistently stuck at Section 4 (the ranged combat gap), we may add ONE message when they bump the wall repeatedly: "Target out of reach. Try your equipped exploit [1-5]." This is a fallback, not a planned feature.

---

## Phase 4: Tutorial System - SIMPLIFIED

**Design change**: The original Phase 4 defined a complex TutorialManager with position triggers, action triggers, and 7-objective progression. This has been **dramatically simplified** because the redesigned layout teaches through environmental design, not text hints.

### 4.1 What's Been Removed

- `TutorialManager` class - NOT NEEDED
- `TutorialState` tracking - NOT NEEDED
- Position-based hint triggers - NOT NEEDED
- Action-based hint triggers - NOT NEEDED
- 7-objective progression system - NOT NEEDED

### 4.2 What Remains

**Only two dialogues**:
1. **Intro dialogue** - Brief context setting when prologue starts
2. **Completion dialogue** - Celebration when player reaches gateway

**No mid-game hints**. The layout teaches through play.

### 4.3 Files to Create

None. No `tutorial.py` file needed.

### 4.4 Files to Modify

None for tutorial hints. All prologue-specific code is in:
- `engine.py` - prologue_mode flag
- `dialogue.py` - intro/completion dialogues
- `death.py` - prologue death handling

### 4.5 Continuous Visibility Feedback (IMPLEMENT)

Show player's visibility state persistently in the status bar during prologue:

```python
# In status bar rendering, when prologue_mode is True:
def get_visibility_status(player_pos, game_map, enemies, spotted_in_blind_spot=False):
    """Return visibility status text and color for prologue.

    Args:
        player_pos: Player's current position
        game_map: The game map with blind_spots set
        enemies: List of enemies to check adjacency
        spotted_in_blind_spot: True if player was just spotted while in blind spot
    """
    in_blind_spot = (player_pos.x, player_pos.y) in game_map.blind_spots

    # Special case: spotted while in blind spot (adjacent enemy saw through)
    if spotted_in_blind_spot and in_blind_spot:
        return "TOO CLOSE!", Colors.ALERT_RED  # Flash red briefly

    if in_blind_spot:
        return "CONCEALED", Colors.ELECTRIC_PURPLE
    else:
        return "EXPOSED", Colors.DIM_WHITE

# Render in status bar area (near HP/Heat display):
status_text, status_color = get_visibility_status(
    player.position, game_map, enemies,
    spotted_in_blind_spot=game_engine.prologue_spotted_in_blind_spot
)
console.print(x=STATUS_X, y=STATUS_Y, string=status_text, fg=status_color)

# Reset the flash flag after rendering
game_engine.prologue_spotted_in_blind_spot = False
```

**Three states:**
- `CONCEALED` (purple) - In blind spot, hidden from enemies at range
- `EXPOSED` (white) - Not in blind spot, visible to enemies with LOS
- `TOO CLOSE!` (red, brief flash) - In blind spot but spotted anyway (adjacent enemy)

**Rationale**: Stealth games constantly show hidden/visible state. The `TOO CLOSE!` flash provides immediate visual feedback when the blind spot range rule fails, reinforcing the lesson before the internal thought fires.

**Implementation location**: Add to `src/rsp/ui/status_bar.py` with a prologue mode check. The `prologue_spotted_in_blind_spot` flag is set in `turn_manager.py` when detecting blind spot adjacency failure.

**Audio cue for TOO CLOSE**: When `spotted_in_blind_spot` is True, play a short audio cue to reinforce the visual feedback. Reuse the alert sound at lower volume:

```python
# In get_visibility_status() or the calling code:
if spotted_in_blind_spot and in_blind_spot:
    # Play audio cue (alert sound at 50% volume)
    game_engine.sound_manager.play_sound("alert", volume=0.5)
    return "TOO CLOSE!", Colors.ALERT_RED
```

This provides multi-sensory feedback: visual (red text flash), audio (alert sound), and narrative (internal thought "Too close!"). The combination reinforces the blind spot range rule through multiple channels.

### 4.6 Reactive Internal Voice System (IMPLEMENT)

Tutorial guidance delivered as the protagonist's internal thoughts - **reactive to player actions**, not pre-emptive instructions. The character reflects on what just happened, teaching through experience.

**Design principles:**
- **Reactive**: Responds to outcomes (success/failure), not pre-emptive hints
- **Reflective**: Character thinks about what just happened and why
- **Paired**: Most mechanics have both failure and success responses
- **Natural**: Feels like internal monologue, not a tutorial system
- **One-shot**: Each thought triggers ONCE per session (but failure/success are separate)

**Philosophy**: Players learn by doing. Pre-emptive hints ("press . to wait") feel like instructions. Reactive thoughts ("Should have waited...") feel like natural learning.

```python
# Reactive internal voice - responds to what the player DOES, not what they should do
PROLOGUE_THOUGHTS = {
    # === SECTION 1a: DIAGONAL MOVEMENT ===
    # Discovery: first diagonal move
    "diagonal_discover": {
        "trigger": "player_moves_diagonally_first_time",
        "message": "Diagonal movement... that's faster.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 1a: MELEE COMBAT ===
    # Success: killed the damaged scanner by bumping
    "melee_success": {
        "trigger": "player_kills_enemy_with_melee",
        "message": "Walking into them... that works.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 1b: TURN-BASED + WAIT ===
    # Observation (first time seeing patrol move)
    "turn_based_observe": {
        "trigger": "player_sees_patrol_move",
        "message": "It moves when I move...",
        "color": Colors.DIM_CYAN,
    },
    # Failure: walked into patrol without waiting
    "wait_fail": {
        "trigger": "patrol_spots_player_in_corridor",
        "message": "Should have waited for it to pass.",
        "color": Colors.DIM_CYAN,
    },
    # Success: timed movement correctly
    "wait_success": {
        "trigger": "player_passes_patrol_undetected",
        "message": "Timing. That's the key.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 2: BLIND SPOTS AT RANGE ===
    # Observation (entering blind spot area)
    "blindspot_observe": {
        "trigger": "player_enters_blind_spot_first_time",
        "message": "A blind spot... they might not see me here.",
        "color": Colors.DIM_CYAN,
    },
    # Failure: spotted in blind spot (adjacent - they see past it)
    "blindspot_adjacent_fail": {
        "trigger": "enemy_spots_player_in_adjacent_blind_spot",
        "message": "Too close! They can see right past it.",
        "color": Colors.DIM_CYAN,
    },
    # Success: blind spot worked at range
    "blindspot_range_success": {
        "trigger": "player_hidden_in_blind_spot_at_range",
        "message": "The blind spot worked... but only because I kept my distance.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 3: ALERT AND ESCAPE ===
    # Observation: FOV is bidirectional (first time spotted)
    "fov_bidirectional": {
        "trigger": "enemy_first_spots_player",
        "message": "If I can see them, they can see me.",
        "color": Colors.DIM_CYAN,
    },
    # Failure: went hostile (didn't escape in time)
    "alert_to_hostile_fail": {
        "trigger": "enemy_transitions_alert_to_hostile",
        "message": "Too slow! Should have broken line of sight faster.",
        "color": Colors.DIM_CYAN,
    },
    # Success: escaped during alert
    "alert_escape_success": {
        "trigger": "player_breaks_los_enemy_deescalates",
        "message": "Breaking line of sight... that bought me time.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 4: RANGED COMBAT + HEAT ===
    # Observation (can't reach enemy)
    "exploit_observe": {
        "trigger": "player_bumps_wall_near_visible_enemy",
        "message": "Can't reach them from here... maybe an exploit would work.",
        "color": Colors.DIM_CYAN,
    },
    # Success: used exploit to kill
    "exploit_success": {
        "trigger": "player_kills_enemy_with_exploit",
        "message": "The exploit worked. Good to know.",
        "color": Colors.DIM_CYAN,
    },
    # Observation: heat is getting high
    "heat_high": {
        "trigger": "player_heat_exceeds_threshold",
        "message": "Running hot... need to cool down.",
        "color": Colors.DIM_CYAN,
    },

    # === NODE USAGE ===
    # Confirmation: cooling node works
    "cooling_node_use": {
        "trigger": "player_uses_cooling_node",
        "message": "Heat dissipating... these nodes are useful.",
        "color": Colors.DIM_CYAN,
    },
    # Confirmation: CPU recovery node works
    "cpu_node_use": {
        "trigger": "player_uses_cpu_node",
        "message": "Systems restored. Good to know these exist.",
        "color": Colors.DIM_CYAN,
    },
    # Confirmation: ghost node works
    "ghost_node_use": {
        "trigger": "player_uses_ghost_node",
        "message": "Invisible... but only for a moment.",
        "color": Colors.DIM_CYAN,
    },

    # === SECTION 5: PLAYER CHOICE ===
    # Acknowledgment: player chooses stealth path
    "stealth_choice": {
        "trigger": "player_enters_section_5_left_path",
        "message": "The quieter route. Worth the extra steps.",
        "color": Colors.DIM_CYAN,
    },
    # Gateway spotted
    "gateway_spotted": {
        "trigger": "gateway_enters_fov",
        "message": "The gateway. Almost there.",
        "color": Colors.DIM_CYAN,
    },
}

# Track shown thoughts - failure and success are tracked separately
shown_thoughts: set[str] = set()

def show_reactive_thought(thought_key: str, game):
    """Show internal thought if not already shown this session."""
    if thought_key in shown_thoughts:
        return False
    if thought_key not in PROLOGUE_THOUGHTS:
        return False

    thought = PROLOGUE_THOUGHTS[thought_key]
    game.message_log.add_message(thought["message"], thought["color"])
    shown_thoughts.add(thought_key)
    return True

def reset_prologue_thoughts():
    """Reset on prologue restart - lets player learn again."""
    shown_thoughts.clear()
```

**Trigger integration points:**

| Thought | Where to Hook | Detection Logic |
|---------|---------------|-----------------|
| `diagonal_discover` | `input_handler.py` move processing | First diagonal move (dx != 0 AND dy != 0) |
| `melee_success` | `combat.py` after melee kill | Enemy killed by bump attack (first melee kill) |
| `turn_based_observe` | `turn_manager.py` after enemy moves | First Patrol move while player has LOS |
| `wait_fail` | `turn_manager.py` enemy state change | Patrol -> ALERT in Section 1 area |
| `wait_success` | `coordinator.py` position check | Player reaches Section 2 without Patrol going ALERT |
| `blindspot_observe` | `game_map.py` tile entry | First blind_spot tile entered |
| `blindspot_adjacent_fail` | `characters.py` can_see_player | Enemy spots player AND player in blind_spot AND distance <= 1 |
| `blindspot_range_success` | `turn_manager.py` end of turn | Player in blind_spot, enemy has LOS blocked by range |
| `fov_bidirectional` | `turn_manager.py` first ALERT | First time any enemy goes ALERT (spotted player) |
| `alert_to_hostile_fail` | `turn_manager.py` state transition | ALERT -> HOSTILE transition |
| `alert_escape_success` | `turn_manager.py` state transition | ALERT -> UNAWARE transition |
| `exploit_observe` | `input_handler.py` bump detection | Move into wall, visible enemy within 5 tiles |
| `exploit_success` | `combat.py` after kill | Enemy killed by exploit (not melee) |
| `heat_high` | `combat.py` after exploit use | Player heat >= 40 (triggers after 2 Code Injections) |
| `cooling_node_use` | `game_map.py` node interaction | First time player uses cooling node |
| `cpu_node_use` | `game_map.py` node interaction | First time player uses CPU recovery node |
| `ghost_node_use` | `game_map.py` node interaction | First time player uses ghost node |
| `stealth_choice` | `input_handler.py` position check | Player enters left path area in Section 5 (x <= 5, y >= 22) |
| `gateway_spotted` | `visibility_manager.py` FOV update | Gateway position enters visible tiles |

**Example player experience:**

```
Section 2 - Player walks through blind spot toward Scanner:

  [Player enters blind spot tile]
  Inner voice: "A blind spot... they might not see me here."

  [Player walks adjacent to Scanner, gets spotted despite blind spot]
  Inner voice: "Too close! They can see right past it."

  [Player retreats, takes alternate path, stays at range 3]
  Inner voice: "The blind spot worked... but only because I kept my distance."
```

**Why reactive voice works better than pre-emptive hints:**

| Pre-emptive (worse) | Reactive (better) |
|---------------------|-------------------|
| "Press . to wait for enemies to pass" | "Should have waited for it to pass." |
| "Blind spots only hide you at range > 1" | "Too close! They can see right past it." |
| "Break line of sight to escape alert" | "Breaking line of sight... that bought me time." |

The reactive approach:
- Teaches through consequence, not instruction
- Feels like natural self-reflection
- Doesn't spoil the learning moment
- Creates "aha!" moments when success thought confirms understanding

**Message styling:**
- Use `Colors.DIM_CYAN` or similar muted color
- Italics if the message log supports it
- Distinct from combat messages and system alerts

---

## Phase 5: Game Flow Integration

### 5.1 Simple Menu Design

The prologue is a **standalone mode** accessible from main menu. No "first time" detection - player chooses freely.

```
Main Menu (always shows same options):
    - New Game      --> Always starts Level 1
    - Tutorial      --> Always visible, launches prologue mode
    - Continue      --> (if save exists)
    - Achievements
    - Ascension
    - Settings
    - Quit

Tutorial flow:
    Player clicks "Tutorial"
        |
        v
    Launch prologue mode
        |
        v
    Complete (reach gateway) OR die/quit
        |
        v
    Set prologue_completed = True (for achievements only)
        |
        v
    Return to main menu
```

### 5.2 Prologue as Standalone Mode

The prologue is a separate game mode:

- Has its own initialization path via `prologue_mode=True`
- No save file created during prologue
- Death restarts prologue (no permadeath)
- Completion returns to main menu
- Always accessible via "Tutorial" menu option

File: `src/rsp/core/engine.py`

Add new parameter for prologue mode:

```python
def __init__(
    self,
    # ... existing params ...
    prologue_mode: bool = False,  # NEW: True when running tutorial
):
    # ... existing init code ...

    self.prologue_mode = prologue_mode

    # Prologue-specific flags (used by dialogue handlers)
    self.prologue_completed_pending = False
    self.prologue_restart_pending = False

    # Prologue visibility feedback flag (set when spotted in blind spot while adjacent)
    self.prologue_spotted_in_blind_spot = False

    # NOTE: This must be integrated into the EXISTING if load_save: ... else: structure
    # The actual pattern in engine.py is:
    #   if load_save:
    #       # load logic (unchanged)
    #   else:
    #       # new game logic (add prologue check here)

    # Inside the existing else: branch, add this check:
    if prologue_mode:
        # Prologue-specific initialization
        self.ascension_level = 0  # Force base difficulty for tutorial
        self.ascension_modifiers = calculate_ascension_modifiers(0)
        self.game_state.level = 0
        self._randomize_code_hacks()
        self.game_session.generate_procedural_level()
        self._show_prologue_intro()
    else:
        # Existing new game initialization (unchanged)
        self._randomize_code_hacks()
        self.game_session.generate_procedural_level()
        # ... existing intro messages and dialogue ...

def _show_prologue_intro(self):
    """Show prologue introduction dialogue."""
    from rsp.ui.dialogue import create_prologue_intro_dialogue
    self.dialogue_state.show(create_prologue_intro_dialogue())
```

### 5.3 Main Menu Changes

File: `src/rsp/ui/menu_main.py`

Add "Tutorial" to the options list (insert after "New Game"):

```python
# In _build_options_list() and refresh_options(), add "Tutorial" after "New Game":
base_options = [
    "New Game",
    "Tutorial",  # NEW: Always visible
]

# In select_current_option(), add handler:
elif option == "Tutorial":
    return "tutorial"  # NEW: Returns tutorial action
```

### 5.3.1 CRITICAL: Main Loop Tutorial Handler

File: `src/rsp/core/loop.py`

Add handler in `_process_menu_action()` after the `new_game` handler (~line 540):

```python
elif action == "tutorial":
    menu_sound_manager.stop_music(fade_out_ms=1000)
    from rsp.systems.achievements import AchievementManager
    AchievementManager.clear_pending_popups()
    # Start in prologue mode - no ascension modifiers in tutorial
    game = GameEngine(settings=settings, prologue_mode=True)
    return current_menu, (game, False)
```

This ensures the "Tutorial" menu option properly launches the game in prologue mode.

### 5.4 Prologue Completion Handling

File: `src/rsp/level/coordinator.py`

Prologue completion returns to main menu.

**IMPORTANT**: The `return_to_menu_after_dialogue` flag needs to be checked in the game loop to actually exit to menu.

```python
def progress_to_next_level(self):
    """Progress to next level or handle prologue completion."""

    if getattr(self.game_engine, 'prologue_mode', False):
        # Prologue completion: mark done (for achievements) and return to menu
        self.game_engine.settings.prologue_completed = True
        self.game_engine.settings.save_settings()

        # Show completion dialogue
        from rsp.ui.dialogue import create_prologue_completion_dialogue
        self.game_engine.dialogue_state.show(
            create_prologue_completion_dialogue()
        )

        # Set flag to return to main menu after dialogue closes
        self.game_engine.return_to_menu_after_dialogue = True
        return

    # ... existing level progression code (unchanged) ...
```

### 5.4.1 CRITICAL: Return-to-Menu Implementation (REVISED)

**PROBLEM**: The original approach invented new flags (`return_to_menu_after_dialogue`, `clean_exit_to_menu`). This doesn't align with existing code patterns.

**EXISTING PATTERN** (from `loop.py:810-815, 827-833, 847-854`):
```python
# Dialogue/input handlers return should_continue (bool or None)
should_continue = input_handler.handle_*()
if should_continue is not None and not should_continue:
    # Death/victory dialogue was dismissed - return to main menu
    AchievementManager.clear_pending_popups()
    return True, None  # This exits the game loop and returns to menu
```

**CORRECT APPROACH**: Use the existing pattern. The `DialogueInputManager.handle_dismiss()` method already returns `False` for death/victory dialogues to signal exit to menu. We extend this for prologue dialogues.

File: `src/rsp/input/dialogue.py` - Modify `handle_dismiss()` (around line 233):

```python
def handle_dismiss(self) -> bool:
    """
    Handle dialogue dismissal/cancellation (user pressed N/ESC or clicked cancel).

    Returns:
        True if game should continue, False if should exit to menu
    """
    dialogue = self.game.dialogue_state.get_active()
    if not dialogue:
        return True

    # Check dialogue type by title
    # ... existing dialogue type checks ...

    # NEW: Prologue completion - return to menu
    elif "UPLINK ESTABLISHED" in dialogue.title:
        self.game.dialogue_state.close()
        return False  # Exit to main menu

    # NEW: Prologue death - restart level
    elif "CONNECTION LOST" in dialogue.title:
        self._restart_prologue()
        self.game.dialogue_state.close()
        return True  # Continue game loop (with restarted level)

    elif (
        "PURGED" in dialogue.title
        or "BREAKTHROUGH" in dialogue.title
        or "ROGUE SIGNAL ESTABLISHED" in dialogue.title
    ):
        # Death/victory messages - any key closes and returns to menu
        self.game.dialogue_state.close()
        return False  # Exit to main menu

    # Close dialogue
    self.game.dialogue_state.close()
    return True  # Continue game
```

**Also add `_restart_prologue()` method to `DialogueInputManager`**:

```python
def _restart_prologue(self):
    """Restart the prologue level after death."""
    from rsp.entities.base import Colors

    game = self.game

    # Reset death handler state
    game.death_handler.reset()
    game.pending_death_dialogue = False

    # Reset player stats
    game.player.cpu = game.player.max_cpu
    game.player.heat = 0
    game.player.trace_level = 0
    game.player.reset_temporary_effects()  # NEW method on Player

    # Clear enemies
    game.enemy_manager.enemies.clear()

    # Regenerate the level (call coordinator directly to pass skip_level_start_message)
    game.game_session.level_coordinator.generate_procedural_level(skip_level_start_message=True)

    # Invalidate FOV cache
    game.visibility_manager.invalidate_cache()

    # Show restart message
    game.message_log.add_message("Uplink re-established", Colors.CYAN)
```

File: `src/rsp/level/coordinator.py` - Set the pending flag instead of inventing new flags:

```python
def progress_to_next_level(self):
    if getattr(self.game_engine, 'prologue_mode', False):
        # Mark prologue completed
        self.game_engine.settings.prologue_completed = True
        self.game_engine.settings.save_settings()

        # Show completion dialogue and SET FLAG for dialogue handler
        from rsp.ui.dialogue import create_prologue_completion_dialogue
        self.game_engine.dialogue_state.show(create_prologue_completion_dialogue())
        self.game_engine.prologue_completed_pending = True  # Flag for dialogue handler
        return

    # ... existing level progression code ...
```

This approach:
- Uses the existing `should_continue = False -> return True, None` pattern
- Requires minimal changes to existing code
- Is consistent with death/victory handling

### 5.5 Coordinator Changes (see Phase 2.6)

The coordinator changes for fixed level generation are detailed in **Phase 2.6**. This section is intentionally left as a cross-reference to avoid duplication.

### 5.7 CRITICAL: Death Handling in Prologue (REVISED)

File: `src/rsp/systems/death.py`

Prologue death restarts the prologue, no save deletion.

**IMPORTANT**: The `PlayerDeathHandler` has a `_handled` flag that prevents re-processing. This MUST be reset when restarting the prologue. Also clear `pending_death_dialogue`.

**ARCHITECTURE DECISION**: Use the SAME dialogue flow pattern as completion - dialogue handler detects prologue death and triggers restart via a flag.

Modify `check_death()` to check prologue mode BEFORE calling `_handle_death`:

```python
def check_death(self, cause: str, source: str | None = None) -> bool:
    """Check if player is dead and handle death if so."""
    if self._handled:
        return True  # Already handled

    if self.game.player.cpu > 0:
        return False

    # Victory check (existing code)
    if self.game.game_state.show_victory_screen:
        return True

    # NEW: Prologue death is handled differently - no permadeath
    if getattr(self.game, 'prologue_mode', False):
        self._handle_prologue_death(cause, source)
        return True  # Player died, but we restart instead of game over

    # Normal death handling (existing _handle_death call)
    # ... rest of existing code ...

def _handle_prologue_death(self, cause: str, source: str | None = None):
    """Handle death in prologue - restart without penalty."""
    from rsp.ui.dialogue import create_prologue_death_dialogue

    # Mark as handled to prevent re-entry during restart
    self._handled = True

    # Play death sounds (still want audio feedback)
    try:
        self.game.sound_manager.play_sound("player_death", priority=10)
    except Exception:
        pass

    # Show death dialogue with tutorial message
    self.game.dialogue_state.show(
        create_prologue_death_dialogue(cause)
    )

    # Set flag for dialogue handler to trigger restart
    self.game.prologue_restart_pending = True

    # NOTE: Do NOT set game_over = True
    # NOTE: Do NOT delete save or finalize metrics
```

**NOTE**: The restart logic is now handled in `DialogueInputManager.handle_dismiss()` and `_restart_prologue()` - see Phase 5.4.1 for the revised implementation that correctly uses the existing dialogue flow pattern.

### 5.6 Add Prologue Dialogues

File: `src/rsp/ui/dialogue.py`

Only 3 dialogues needed. **All text is minimal** - the level teaches, not the dialogues.

**KEY ROUTING NOTE**: All prologue dialogues use `valid_keys=[tcod.event.KeySym.RETURN]`. In the existing codebase, ENTER/SPACE/ESC all route to `handle_dismiss()` (NOT `handle_confirm()`). This is correct - the prologue completion/death handlers in `handle_dismiss()` will catch these.

```python
def create_prologue_intro_dialogue() -> DialogueBox:
    """Create prologue introduction dialogue (shown when prologue starts)."""
    return DialogueBox(
        title="FIRST INFILTRATION",
        message=(
            "Remote uplink active.\n"
            "Reach the gateway.\n"
            "\n"
            "Arrow keys to move. Period (.) to wait. 1-5 for exploits.\n"
            "Press ? anytime for help."
        ),
        options=["[ENTER] Begin"],
        valid_keys=[tcod.event.KeySym.RETURN],
        title_color=Colors.CYAN,
        message_color=Colors.WHITE,
        border_color=Colors.CYAN,
        bg_color=(20, 30, 40),
        format_data={},
        priority=5,
    )

def create_prologue_completion_dialogue() -> DialogueBox:
    """Create prologue completion dialogue (returns to main menu)."""
    return DialogueBox(
        title="UPLINK ESTABLISHED",
        message="Gateway reached. You are ready.\n\nThe real networks won't be this forgiving. Stay too long, and something worse than guards will find you.",
        options=["[ENTER] Continue"],
        valid_keys=[tcod.event.KeySym.RETURN],
        title_color=Colors.GREEN,
        message_color=Colors.WHITE,
        border_color=Colors.GREEN,
        bg_color=(20, 30, 40),
        format_data={},
        priority=5,
    )

def create_prologue_death_dialogue(cause: str) -> DialogueBox:
    """Create prologue death dialogue (restarts training)."""
    return DialogueBox(
        title="CONNECTION LOST",
        message=f"{cause}\n\nRe-establishing uplink... I know more now.",
        options=["[ENTER] Retry"],
        valid_keys=[tcod.event.KeySym.RETURN],
        title_color=Colors.YELLOW,
        message_color=Colors.WHITE,
        border_color=Colors.YELLOW,
        bg_color=(40, 30, 20),
        format_data={},
        priority=10,
    )
```

**What changed from original**:
- Intro: Removed "Welcome", removed explanation of what training teaches, removed "Failure is not permanent" (let them discover that)
- Completion: Removed "Neural interface calibrated" technobabble, removed instructions to select New Game. Added subtle permadeath foreshadowing: "The real networks won't be this forgiving."
- Death: Removed "In live infiltration, this would be permanent" - don't explain permadeath explicitly, just foreshadow it in completion

**Eighth Review changes**:
- Completion dialogue now includes Admin foreshadowing: "Stay too long, and something worse than guards will find you." This hints at 100% trace consequences without explicit explanation.

### 5.7 Files to Modify (Phase 5)

| File | Changes |
|------|---------|
| `src/rsp/core/engine.py` | Add `prologue_mode` parameter to `__init__` |
| `src/rsp/ui/menu_main.py` | Add "Tutorial" option (always visible) |
| `src/rsp/level/coordinator.py` | Handle prologue mode completion (return to menu) |
| `src/rsp/systems/death.py` | Add `_handle_prologue_death()` method |
| `src/rsp/ui/dialogue.py` | Add 3 prologue dialogue creators |

---

## Phase 6: Testing & Polish

### 6.1 Unit Tests

File: `tests/unit/test_fixed_level_generator.py`

```python
def test_prologue_layout_parses():
    """Verify prologue ASCII layout parses without errors."""

def test_prologue_has_required_elements():
    """Verify prologue contains player spawn, gateway, required nodes."""

def test_prologue_enemy_positions_valid():
    """Verify enemies spawn on floor tiles, not walls."""

def test_prologue_chokepoint_is_narrow():
    """Verify Section 2 corridor forces single-file movement past Scanner."""

def test_prologue_section3_no_blindspots_at_entrance():
    """Verify Section 3 has no blind spots near entrance (forces crossing)."""
```

**Removed**: `test_tutorial_manager.py` - no longer needed since TutorialManager was removed.

### 6.2 Integration Tests

File: `tests/integration/test_prologue_flow.py`

```python
def test_new_game_starts_at_level_1():
    """New Game always starts at level 1."""

def test_tutorial_starts_prologue_mode():
    """Tutorial menu option launches prologue mode at level 0."""

def test_prologue_completion_returns_to_menu():
    """Completing prologue sets achievement flag and returns to menu."""

def test_prologue_death_restarts_prologue():
    """Death in prologue restarts level, doesn't trigger permadeath."""

def test_menu_always_shows_tutorial():
    """Tutorial option visible regardless of prologue_completed flag."""
```

### 6.3 Gameplay Polish Checklist

- [ ] Section 2 chokepoint forces waiting for Scanner patrol (can't rush through)
- [ ] Section 3 Patrol spots player entering (guaranteed encounter for alert teaching)
- [ ] Section 3 blind spot escape route is obvious when panicking
- [ ] Section 4 wall gap clearly blocks melee (player tries bumping before using exploit)
- [ ] Section 5 offers viable stealth OR combat path to gateway
- [ ] Enemy HP lets combat resolve in 2-3 hits (not tedious)
- [ ] Trace pressure is noticeable but not lethal
- [ ] Prologue can be completed in 2-4 minutes
- [ ] Death → restart feels smooth, not punishing

### 6.4 Edge Cases to Handle

| Case | Handling |
|------|----------|
| Player dies in prologue | Restart prologue (no permadeath in tutorial) |
| Player quits mid-prologue | Save prologue progress OR restart from beginning |
| Ascension mode with prologue | Skip prologue for A1+ (experienced players) |
| Save file corruption | Prologue state in user_settings, not save file |

---

## File Change Summary

### New Files to Create

| File | Lines (est.) | Purpose |
|------|--------------|---------|
| `src/rsp/level/fixed_levels.py` | ~80 | FixedLevelData class + PROLOGUE_LAYOUT constant (28x25) |
| `src/rsp/level/fixed_generator.py` | ~150 | FixedLevelGenerator class (real game elements only) |
| `tests/unit/test_fixed_level_generator.py` | ~100 | Fixed layout parsing + design verification tests |
| `tests/integration/test_prologue_flow.py` | ~100 | Full prologue flow tests |

**Removed from original plan**:
- `src/rsp/systems/tutorial.py` - NOT NEEDED (layout teaches, not code)
- `tests/unit/test_tutorial_manager.py` - NOT NEEDED (no TutorialManager)

### New Data Structures Required

| Location | Addition | Purpose |
|----------|----------|---------|
| `src/rsp/ui/status_bar.py` | `get_visibility_status()` | Show CONCEALED/EXPOSED status in prologue |

**NOTE**: No new game mechanics needed - prologue uses ONLY existing game elements.

### Files to Modify

| File | Changes | Risk Level |
|------|---------|------------|
| `game_content.json` | Add level 0 network_config | LOW - additive |
| `narrative_content.json` | Add prologue_messages section | LOW - additive |
| `src/rsp/core/config.py` | Add `prologue_completed` to DEFAULTS | LOW - additive |
| `src/rsp/core/engine.py` | Add `prologue_mode` parameter, flags, `_show_prologue_intro()` | MEDIUM - new code path |
| `src/rsp/core/loop.py` | Add `tutorial` action handler, wrap ESC auto_save in prologue check | MEDIUM - menu integration |
| `src/rsp/ui/menu_main.py` | Add "Tutorial" option | LOW - additive |
| `src/rsp/level/coordinator.py` | Handle fixed_layout, prologue completion, music, skip auto_save | HIGH - core generation |
| `src/rsp/systems/death.py` | Add `_handle_prologue_death()` method | MEDIUM - affects permadeath |
| `src/rsp/ui/dialogue.py` | Add 3 prologue dialogue creators | LOW - additive |
| `src/rsp/input/dialogue.py` | Add prologue checks in `handle_dismiss()`, add `_restart_prologue()` | MEDIUM - dialogue flow |
| `src/rsp/entities/player.py` | Add `reset_temporary_effects()` method | LOW - additive |
| `src/rsp/combat/inventory.py` | Add `InventoryManager.clear_all()` method (GAP 19) | LOW - additive |
| `src/rsp/input/gameplay.py` | Skip gateway confirmation in prologue (GAP 20 - optional) | LOW - additive |
| `src/rsp/level/__init__.py` | Export new classes | LOW - imports only |

**NOTE**: `generator.py` does NOT need modification - see Phase 2.6 for rationale.

## Risk Assessment

### HIGH RISK Areas (Test Carefully)

1. **coordinator.py changes**: The `is_fixed_layout` check must correctly skip ALL placement methods. Missing one will cause duplicate enemies/items. The check must happen BEFORE `level_generator.generate_level()` is called.

2. **Death handling changes**: The prologue death path must NOT trigger any of the existing death side effects (save deletion, metrics finalization).

3. **Dialogue flow changes**: The `handle_dismiss()` checks must correctly identify prologue dialogues and return `False` (exit to menu) or restart appropriately.

### TESTING PRIORITY

1. **First**: Test fixed level generator in isolation
2. **Second**: Test Tutorial menu option launches prologue mode
3. **Third**: Test prologue completion returns to menu
4. **Fourth**: Test prologue death/restart behavior
5. **Fifth**: Playtest the layout - verify each section teaches its lesson through design

---

## Implementation Order

Recommended implementation sequence:

1. **Phase 1.1-1.3**: Add JSON config entries (can test loading immediately)
2. **Phase 2.1-2.3**: Create fixed level generator infrastructure
3. **Phase 3.1-3.4**: Design and implement prologue layout
4. **Phase 5.1-5.6**: Integrate into game flow (playable prologue)
5. **Phase 6.1-6.4**: Testing and polish

**Note**: Phase 4 (Tutorial System) is now minimal - just verify the two dialogues work.

This order allows for playable milestones:
- After Phase 3: Prologue level can be generated
- After Phase 5: Full prologue flow works (menu → play → complete/die → menu)
- After Phase 6: Layout playtested and tuned

---

## Resolved Design Decisions

These questions have been resolved based on user input and typical roguelike patterns:

1. **Menu design**: **Simple, static menu (like Hades/Dead Cells/Slay the Spire)**
   - "New Game" and "Tutorial" always both visible in main menu
   - No "first time" detection or conditional prompts
   - Player picks what they want, no forced tutorials

2. **Prologue structure**: **Standalone mode**
   - Prologue is a separate game mode via `prologue_mode=True`
   - Accessed via "Tutorial" menu option
   - Completion returns to main menu (doesn't auto-continue)

3. **New Game behavior**: **Always starts level 1**
   - No prologue checks or prompts
   - Simple, predictable behavior

4. **Death in prologue**: **Restart prologue (no permadeath)**
   - Death shows minimal "DE-RESOLVED" message, restarts immediately
   - No explanation of permadeath - let them discover that in the real game
   - Restart prologue with reset stats
   - No save file created/deleted during prologue

5. **prologue_completed flag**: **For achievements only**
   - Tracks whether player completed tutorial (for achievement)
   - Does NOT affect menu display or game flow

6. **Music**: **Use level 1 music ("level1_stealth.ogg")**
   - Reuses existing asset, calmer track fits tutorial

---

## Pre-Implementation Verification Checklist

Before starting implementation, verify these assumptions are still valid:

### Code Structure Checks (Verified during plan review)
- [x] `LevelGenerator.__init__` signature at `generator.py:78` - confirmed no `game_engine` param
- [x] `coordinator.py:47` - verified `generate_procedural_level()` signature unchanged
- [x] `loop.py:531-539` - verified `new_game` action handler location for adding `tutorial` handler
- [x] `death.py:78-124` - verified `check_death()` structure matches plan's modification points
- [x] `menu_main.py:86-131` - verified `_build_options_list()` structure for adding Tutorial

### Data Structure Checks (Verified during plan review)
- [x] `game_content.json` has `network_configs` dict with string keys "1", "2", "3" (at line 279)
- [x] `config.py:795-796` converts keys to int (confirmed level 0 lookup works)
- [x] `GameSettings.DEFAULTS` at `config.py:62-87` - verified structure for adding `prologue_completed`

### Flow Checks (Verified during plan review)
- [x] Dialogue close is handled in `src/rsp/input/dialogue.py` - `DialogueInputManager.handle_dismiss()` returns False to exit to menu
- [x] `enemy_manager.enemies` is a list (coordinator.py:679 shows `.append()`)
- [x] Player does NOT have `reset_temporary_effects()` method - **MUST BE ADDED** (see below)

### Required Addition: Player.reset_temporary_effects()

File: `src/rsp/entities/player.py` - Add new method after `update_effects()` (around line 211):

```python
def reset_temporary_effects(self):
    """Reset all temporary effects to 0 (used when restarting prologue)."""
    for effect in self.temporary_effects:
        self.temporary_effects[effect] = 0
    self.speed_moves_remaining = 0
```

### Files Verified
- [x] `src/rsp/input/dialogue.py` - `handle_dismiss()` at line 233 returns False for death/victory dialogues
- [x] `src/rsp/core/loop.py:883` - ESC handler calls `auto_save()` (needs prologue check)
- [x] `DialogueInputHandler.handle_input()` at `ui/dialogue.py:457-463` - ENTER routes to "dismiss" not "confirm"

### Test Suite Check
- [x] Run `pytest tests/ -v --collect-only | grep -i prologue` - returned nothing (no conflicts)
- [x] Run `pytest tests/unit/test_level_core.py -v` - all 21 tests passed

---

## REVIEW ADDENDUM: Identified Gaps and Fixes

### GAP 1: Missing `get_prologue_layout()` Function

**Problem**: Phase 2.6 calls `from rsp.level.fixed_levels import get_prologue_layout` but this function is NOT defined in the Phase 2.1 `fixed_levels.py` code.

**Fix**: Add to `src/rsp/level/fixed_levels.py`:

```python
# After PROLOGUE_LAYOUT constant definition:

def get_prologue_layout() -> FixedLevelData:
    """Get the prologue level layout data.

    ALL REAL ENEMY TYPES - each chosen for specific teaching purpose.
    """
    return FixedLevelData(
        layout=[line for line in PROLOGUE_LAYOUT.strip().split('\n') if line],
        name="First Infiltration",
        tutorial_triggers={},  # Not used - layout teaches through design, not triggers
        enemy_overrides={
            # Use default HP from game_content.json - Patrol is 40 HP, Scanner is 35 HP
            # Section 4 Patrol: 40 HP / 25 dmg per Code Injection = 2 hits (teaches heat)
            # All other Patrols: 40 HP (standard combat)
            # Scanner: 35 HP (doesn't matter - it's Section 2 blind spot trap, player usually avoids)
        }
    )
```

### GAP 2: Tutorial Enemy Behavior Not Implemented

**Problem**: Plan says Scanner "won't attack (tutorial)" but doesn't show how to disable enemy attacks.

**SUPERSEDED BY GAP 17**: See GAP 17 for the decision to NOT implement tutorial enemy behavior. Instead, we rely on:
- Reduced HP (enemies die quickly)
- Zero trace penalties (no punishment for combat)
- Normal enemy behavior (teaches real combat)

The `_create_enemy()` method in `fixed_generator.py` should ONLY apply HP overrides, NOT add any `tutorial_mode` flag:

```python
def _create_enemy(
    self, x: int, y: int, enemy_type: str, layout_data: FixedLevelData
) -> Enemy:
    """Create enemy with optional tutorial overrides."""
    enemy = Enemy(Position(x, y), enemy_type)

    # Apply HP overrides (enemies are easier in prologue)
    if enemy_type in layout_data.enemy_overrides:
        overrides = layout_data.enemy_overrides[enemy_type]
        if 'hp' in overrides:
            enemy.cpu = overrides['hp']
            enemy.max_cpu = overrides['hp']

    return enemy
```

~~(Obsolete code removed - see GAP 17 for final decision)~~

### GAP 3: Prologue Flag Initialization Missing

**Problem**: Plan mentions `prologue_completed_pending` and `prologue_restart_pending` flags but doesn't show initialization in `__init__`.

**Fix**: In engine.py `__init__`, after `self.pending_death_dialogue = False`:
```python
# Prologue-specific flags (used by dialogue handlers)
self.prologue_mode = False  # Set True when running tutorial
self.prologue_completed_pending = False
self.prologue_restart_pending = False
```

### GAP 4: Dialogue Title Pattern Mismatch

**Problem**: `handle_dismiss()` in `dialogue.py:273-280` checks for "PURGED", "BREAKTHROUGH", "ROGUE SIGNAL ESTABLISHED". The prologue dialogues use "UPLINK ESTABLISHED" and "CONNECTION LOST" - these need to be added to the check.

**Fix**: The plan already shows adding these checks in Phase 5.4.1. Verify the exact title strings match:
- Completion: `"UPLINK ESTABLISHED"`
- Death: `"CONNECTION LOST"`

### GAP 5: `prologue_completed` Settings Persistence

**Problem**: Adding to `DEFAULTS` dict works for initialization, but need to verify it's included in save/load.

**Fix**: The existing `_apply_settings_from_dict()` and `_get_settings_as_dict()` use `DEFAULTS.keys()` to iterate, so new keys are automatically included. **No additional code needed** - just add to DEFAULTS.

### GAP 6: Auto-Save Skip Location

**Problem**: Plan shows wrapping `auto_save()` in `progress_to_next_level()`, but auto_save is at line 290 inside the `else` branch. The prologue completion returns early (line 1028), so auto_save is naturally skipped.

**Fix**: No change needed for prologue COMPLETION (early return skips it). But for normal level progression in prologue mode (if we ever wanted it), the skip is still needed. **Current plan is correct.**

However, `generate_procedural_level()` doesn't call auto_save - only `progress_to_next_level()` does. So the plan is correct.

### GAP 7: Missing `+` and `E` Characters in FLOOR_CHARS

**Problem**: The ASCII layout uses `+` for doorways and `E` for Threat Scan exploit, but `FLOOR_CHARS` in fixed_generator.py might not include them.

**Fix**: Already included in plan - `FLOOR_CHARS = {'.', '@', '>', 'c', 'r', 'g', 'X', 'S', 'P', 'e', 'E', 'd', '+', 's'}` includes both `+` and `E`. **Verified correct.**

### GAP 8: Enemy Constructor Signature

**Problem**: Plan uses `Enemy(Position(x, y), enemy_type)` but need to verify this is correct.

**Fix**: Check `src/rsp/entities/characters.py`. The Enemy class uses:
```python
def __init__(self, position: Position, enemy_type: str):
```
**Verified correct.**

### GAP 9: Code Hack Initialization for Prologue

**Problem**: Prologue mode needs `_randomize_code_hacks()` called before level generation.

**Fix**: Already shown in plan Phase 5.2:
```python
if prologue_mode:
    # Prologue-specific initialization
    self.game_state.level = 0
    self._randomize_code_hacks()  # <-- This line
    self.game_session.generate_procedural_level()
```
**Verified correct.**

### GAP 10: Missing `tutorial_manager` Reference

**Problem**: Phase 4.6 shows `self.tutorial_manager = None` but Phase 5.2 `__init__` code doesn't include this.

**Fix**: Add to engine.py `__init__` (in prologue section):
```python
# Tutorial system (only active in prologue)
self.tutorial_manager = None
if prologue_mode:
    from rsp.systems.tutorial import TutorialManager
    self.tutorial_manager = TutorialManager(self, self.message_log)
```

### GAP 11: PROLOGUE_LAYOUT Whitespace Issue

**Problem**: The `PROLOGUE_LAYOUT` string uses triple-quoted multiline format. The `get_prologue_layout()` function needs to strip leading/trailing whitespace and handle empty lines.

**Fix**: Already addressed in GAP 1 fix:
```python
layout=[line for line in PROLOGUE_LAYOUT.strip().split('\n') if line],
```

### GAP 12: Menu Option Text

**Problem**: Plan doesn't specify exact menu option text for Tutorial.

**Fix**: Use "Tutorial" (matches plan). Add after "New Game" in both `_build_options_list()` and `refresh_options()`:
```python
base_options = [
    "New Game",
    "Tutorial",  # Always visible
]
```

And in `select_current_option()`:
```python
elif option == "Tutorial":
    return "tutorial"
```

### GAP 13: `_show_prologue_intro()` Not Defined

**Problem**: Phase 5.2 calls `self._show_prologue_intro()` but this method isn't defined.

**Fix**: Already shown later in Phase 5.2:
```python
def _show_prologue_intro(self):
    """Show prologue introduction dialogue."""
    from rsp.ui.dialogue import create_prologue_intro_dialogue
    self.dialogue_state.show(create_prologue_intro_dialogue())
```
**Verified correct**, but ensure this is placed BEFORE the `__init__` that calls it, or make it a proper method definition.

### GAP 14: Fixed Generator `game_engine` Reference

**Problem**: `FixedLevelGenerator.__init__` takes `game_engine` parameter which is used for `code_hack_effects`.

**Fix**: Already correct in plan - coordinator passes `self.game_engine`:
```python
fixed_gen = FixedLevelGenerator(self.game_engine.game_map, self.game_engine)
```

### GAP 15: Prologue Music Selection Order

**Problem**: Plan says insert prologue music check "at START" but doesn't show exact insertion point.

**Fix**: The check should be:
```python
# In generate_procedural_level(), BEFORE existing music selection:
is_prologue = getattr(self.game_engine, 'prologue_mode', False)

if is_prologue:
    self.game_engine.sound_manager.play_music(
        "level1_stealth.ogg", loops=-1, fade_in_ms=GameConfig.DEFAULT_FADE_TIME
    )
elif self.game_engine.level == 1:
    # ... existing code
```

This ensures prologue music plays even though `level == 0` doesn't match any existing case.

### GAP 16: ESC-to-Menu During Prologue Calls auto_save()

**Problem**: In `loop.py:883`, pressing ESC during gameplay calls `game.auto_save()` before returning to menu. In prologue mode, there is no save file, so this will either fail or create an unwanted save.

**Fix**: In `src/rsp/core/loop.py`, wrap the auto_save call at line 883:
```python
# No UI states open, auto-save and go to main menu
if not getattr(game, 'prologue_mode', False):
    game.auto_save()
# Don't stop level music - let it continue playing in the menu
```

This ensures ESC works in prologue but skips save creation.

### GAP 17: Tutorial Enemy Behavior Decision

**Problem**: GAP 2 proposes adding `tutorial_mode` flag to enemies, but this requires modifying core enemy AI code (risky).

**DECISION**: Use the simpler approach - don't modify enemy behavior at all. The network config already has:
- `trace_alert_to_hostile: 0` - No trace penalty when enemies go hostile
- `trace_continuous_hostile: 0` - No continuous trace from hostile enemies
- Reduced HP on all enemies (20/15/25 vs normal 40+)

Enemies WILL attack the player, which is actually better for teaching combat. The reduced HP means players can kill them quickly. This avoids any risky AI modifications.

---

## Summary of Required Additions

1. **Add `get_prologue_layout()` function** to `fixed_levels.py`
2. ~~**Add `tutorial_mode` flag** to tutorial enemies~~ - SKIP, use reduced HP instead
3. **Add flag initialization** in engine.py `__init__`
4. **Add `tutorial_manager = None`** in engine.py `__init__`
5. **Add `_show_prologue_intro()` method** in engine.py (or move call after method def)
6. **Verify title strings match** in dialogue handler checks
7. **Wrap `auto_save()` in prologue check** in loop.py ESC handler

All other aspects of the plan are verified correct.

---

## Friction Points and Simplifications

### FRICTION 1: Tutorial Enemy Behavior Complexity

**Problem**: Adding `tutorial_mode` to enemies and checking it in AI requires touching core enemy code, risking regressions.

**Simplification**: Instead of modifying enemy behavior, use the network config to make enemies functionally harmless:
- `"trace_alert_to_hostile": 0` - Enemies don't raise trace when hostile
- `"trace_continuous_hostile": 0` - No continuous trace damage
- Reduced HP means players can easily defeat them
- The tutorial teaches mechanics; enemies being slightly hostile is fine

**Alternative**: Keep enemies at UNAWARE state permanently by setting their `detection_threshold` very high, or simply accepting that tutorial enemies will attack (teaches combat organically).

### FRICTION 2: Two Menu Build Functions

**Problem**: `_build_options_list()` and `refresh_options()` in `menu_main.py` have duplicate logic for building the options list. Adding "Tutorial" requires updating BOTH.

**Fix**: The plan already accounts for this. Ensure both are updated identically:
```python
base_options = [
    "New Game",
    "Tutorial",  # Add in BOTH methods
]
```

### FRICTION 3: Dialogue Handler String Matching

**Problem**: The `handle_dismiss()` method uses string matching on dialogue titles. This is fragile if titles change.

**Mitigation**:
1. Use constants for dialogue titles (e.g., `PROLOGUE_COMPLETE_TITLE = "UPLINK ESTABLISHED"`)
2. Or use the `user_pref_key` field to identify dialogue types (though this requires more changes)

**Current approach is acceptable** - titles are unlikely to change, and string matching is the existing pattern.

### FRICTION 4: Phase 4 (Tutorial System) Can Be Deferred

**Observation**: The Tutorial System (Phase 4) is a "nice to have" that adds contextual hints. The core prologue is playable WITHOUT it.

**Recommendation**:
1. Implement Phases 1-3, 5 first (playable prologue)
2. Add Phase 4 later as polish
3. The plan's "Implementation Order" section already recommends this

### FRICTION 5: Test Coverage Gap

**Problem**: The plan defines tests but doesn't show exact test locations or fixtures.

**Recommendation**: Create a minimal test fixture first:
```python
# tests/unit/test_fixed_level_generator.py
import pytest
from rsp.level.fixed_levels import get_prologue_layout, FixedLevelData

def test_prologue_layout_valid():
    layout = get_prologue_layout()
    assert isinstance(layout, FixedLevelData)
    assert layout.width == 26
    assert layout.height == 20
    assert '@' in ''.join(layout.layout)  # Has spawn
    assert '>' in ''.join(layout.layout)  # Has gateway
```

### FRICTION 6: `_restart_prologue()` Method Placement

**Problem**: The plan puts `_restart_prologue()` in `DialogueInputManager`, but this class is in the input layer, not the game logic layer. Restarting involves regenerating the level, which is game logic.

**Current approach is acceptable**: `DialogueInputManager` already has access to `self.game` and calls methods like `self.game.exploit_system.execute_exploit()`. The restart logic is similar - it's input-driven game state manipulation.

**Alternative**: Put restart logic in a `PrologueManager` class and have dialogue handler call it. This is cleaner but adds another class.

### FRICTION 7: Intro Dialogue Shows Before Level Is Visible

**Problem**: In Phase 5.2, `_show_prologue_intro()` is called immediately after `generate_procedural_level()`, but the player hasn't seen the level yet. The dialogue covers the screen.

**This is intentional and correct**: The intro explains what the player is about to do. When they dismiss it, the level is revealed. This matches the normal game intro pattern.

---

## Implementation Sequence Recommendation

Based on the gap analysis, here's the refined implementation order:

### Stage 1: Minimal Playable Prologue (No Hints)
1. Phase 1.1: Add level 0 network config to `game_content.json`
2. Phase 1.3: Add `prologue_completed` to settings DEFAULTS
3. Phase 2: Create `fixed_levels.py` and `fixed_generator.py` (with GAP 1 fix)
4. Phase 5.2-5.3: Add `prologue_mode` to engine, menu "Tutorial" option, loop handler (+ GAP 16 ESC fix)
5. Phase 5.4: Prologue completion handling (coordinator + dialogue)
6. Phase 5.7: Death handling (death.py + dialogue handler)
7. Phase 5.6: Add prologue dialogues to `dialogue.py`

**Test**: Can start Tutorial from menu, play level, die/restart, complete/return to menu, ESC to menu.

### Stage 2: Polish and Tutorial System
1. Phase 1.2: Add narrative content (prologue_messages)
2. Phase 4: Tutorial manager and hint system
3. Phase 6: Full test coverage

### Stage 3: Refinement
- Tune enemy HP/behavior for optimal tutorial experience
- Adjust tutorial message timing and content
- Add achievement for completing tutorial (uses `prologue_completed` flag)

---

## Risk Mitigation

### HIGH RISK: Coordinator Changes
The coordinator is touched by many tests. Run the full test suite after each coordinator change:
```bash
pytest tests/unit/test_level_*.py tests/integration/ -v
```

### MEDIUM RISK: Engine __init__ Changes
Adding parameters/flags to engine affects many tests. Use default values to maintain backward compatibility:
```python
prologue_mode: bool = False,  # Default maintains existing behavior
```

### LOW RISK: New Files
New files (`fixed_levels.py`, `fixed_generator.py`, `tutorial.py`) don't affect existing code until imported.

---

## Additional Gaps Found in Review (Post-GAP 17)

### GAP 18: Prologue Restart Missing Critical State Resets

**Problem**: The `_restart_prologue()` method in `dialogue.py` doesn't reset enough state. Missing resets will cause bugs on restart.

**Fix**: Expand `_restart_prologue()` to include all necessary resets:

```python
def _restart_prologue(self):
    """Restart the prologue level after death."""
    from rsp.entities.base import Colors

    game = self.game

    # Reset death handler state
    game.death_handler.reset()
    game.pending_death_dialogue = False

    # Reset player stats
    game.player.cpu = game.player.max_cpu
    game.player.heat = 0
    game.player.trace_level = 0
    game.player.reset_temporary_effects()

    # MISSING FROM ORIGINAL PLAN - Clear player inventory
    game.player.inventory_manager.clear_all()

    # Clear enemies
    game.enemy_manager.enemies.clear()

    # MISSING FROM ORIGINAL PLAN - Reset turn counter (fresh start)
    game.game_state.turn = 0

    # MISSING FROM ORIGINAL PLAN - Reset admin spawned flag
    game.admin_spawned = False

    # MISSING FROM ORIGINAL PLAN - Clear message log (optional but cleaner)
    game.message_log.messages.clear()

    # Reset prologue tutorial flags
    if hasattr(game, '_shown_concealed_message'):
        del game._shown_concealed_message
    if hasattr(game, '_wall_bump_count'):
        del game._wall_bump_count

    # Regenerate the level (call coordinator directly to pass skip_level_start_message)
    game.game_session.level_coordinator.generate_procedural_level(skip_level_start_message=True)

    # Invalidate FOV cache
    game.visibility_manager.invalidate_cache()

    # Show restart message
    game.message_log.add_message("Uplink re-established", Colors.CYAN)
```

### GAP 19: Player.clear_all() Method Missing

**Problem**: GAP 18 calls `inventory_manager.clear_all()` but this method doesn't exist.

**Fix**: Add to `src/rsp/combat/inventory.py` in `InventoryManager` class:

```python
def clear_all(self):
    """Clear all inventory items (used when restarting prologue)."""
    self.items.clear()
    self.equipped_exploits.clear()  # list[str] of exploit keys, not fixed-size
```

### GAP 20: Gateway Confirmation in Prologue

**Problem**: When player steps on gateway in prologue, the normal gateway confirmation dialogue appears. After confirming, it calls `next_level()` which shows level 2 - wrong for prologue.

**DECISION**: Keep gateway confirmation (teaches the mechanic), but modify the confirm handler.

**Fix**: In `src/rsp/input/dialogue.py`, modify `handle_confirm()` GATEWAY case:

```python
elif "GATEWAY" in dialogue.title:
    # Check if in prologue mode
    if getattr(self.game, 'prologue_mode', False):
        # Prologue completion - don't call next_level()
        # Instead, trigger the completion flow
        self.game.game_session.progress_to_next_level()  # This will show UPLINK ESTABLISHED
    else:
        # Normal gateway - proceed to next level
        self.game.sound_manager.play_sound("level_complete")
        self.game.message_log.add_message("Gateway reached! Next network...")
        self.game.next_level()
```

This way:
- Player sees familiar "Proceed through gateway?" dialogue
- Confirming in prologue triggers `progress_to_next_level()` which detects prologue mode and shows "UPLINK ESTABLISHED"
- Confirming in normal game works as before

### GAP 21: Prologue Skips Level Start Message on Restart

**Problem**: The plan's `_restart_prologue()` calls `generate_procedural_level()` without `skip_level_start_message=True`, so the atmospheric level start message will appear on every restart. This is noisy.

**Fix**: Already addressed in GAP 18 code above - pass `skip_level_start_message=True`.

### GAP 22: Layout Dimension Inconsistency

**Problem**: Plan originally said layout is "25x20" in Phase 3.1 but the actual ASCII layout was later redesigned. **FIXED to 28x25 in Third Review.**

**Fix**: Update Phase 3.2 header to match current dimensions:
```
### 3.2 Detailed ASCII Layout (28x25)
```

### GAP 23: Metrics Should Be Disabled in Prologue

**Problem**: The metrics tracking system (`init_session_metrics()`, `track()`, etc.) will record prologue play sessions. This could pollute achievement tracking data.

**Fix Options**:
1. **Skip metrics entirely** - Don't call `init_session_metrics()` in prologue mode
2. **Use separate metrics** - Track tutorial metrics separately (for tutorial completion rate analytics)
3. **Accept it** - Prologue metrics are fine to track

**Recommendation**: Option 1 - skip metrics in prologue. In `engine.py` `__init__`:
```python
if not prologue_mode:
    from rsp.systems.metrics import init_session_metrics
    self.metrics = init_session_metrics()
    self.metrics.ascension_level = self.ascension_level
else:
    self.metrics = None  # No metrics in prologue
```

Then guard all `track()` calls in the codebase with `if self.metrics:`.

**Alternative**: Track metrics but exclude prologue sessions from achievements. Simpler to implement.

### GAP 24: Prologue Should Ignore Ascension Modifiers

**Problem**: If player has ascension level set (e.g., A5), the prologue enemies might inherit ascension-boosted stats, making tutorial harder.

**Fix**: Force ascension_level=0 in prologue mode. In `engine.py`:
```python
if prologue_mode:
    # Tutorial always uses base difficulty
    self.ascension_level = 0
    self.ascension_modifiers = calculate_ascension_modifiers(0)
```

### GAP 25: ESC During Prologue Dialogues

**Problem**: If player presses ESC during prologue intro dialogue, the existing ESC handler at `loop.py:883` might try to auto-save and exit to menu (wrong behavior).

**Fix**: The existing check at `loop.py:875-880` should catch this because dialogue is active. But verify that `dialogue_state.is_active()` returns True during prologue dialogues. The current death dialogue check should work:
```python
if (hasattr(game, "pending_death_dialogue") and game.pending_death_dialogue):
    return True, game  # Block ESC
```

**Additional safety**: Add prologue dialogue check:
```python
if getattr(game, 'prologue_mode', False) and game.dialogue_state.is_active():
    return True, game  # Can't ESC during prologue dialogues
```

---

## Friction Points Summary

| Friction | Impact | Mitigation |
|----------|--------|------------|
| Two menu build functions | LOW | Update both `_build_options_list()` and `refresh_options()` |
| Dialogue title string matching | MEDIUM | Use constants; existing pattern is acceptable |
| Tutorial system deferrable | LOW | Phase 4 can be added after core flow works |
| Enemy behavior modification | HIGH -> LOW | Decided to NOT modify enemy AI - use reduced HP instead |
| restart_prologue placement | MEDIUM | DialogueInputManager has game access; acceptable |
| Metrics in prologue | LOW | Either skip or accept - low impact either way |
| Gateway confirmation | LOW | Can leave as-is to teach mechanic |

---

## Final Checklist Before Implementation

- [ ] Run `pytest tests/` - all tests pass
- [ ] Backup `game_content.json` and `narrative_content.json`
- [ ] Create feature branch: `git checkout -b feature/prologue-level`
- [ ] Commit after each phase for easy rollback
