# Movement System Deep Dive Analysis

## Executive Summary

After extensive code review, I've identified several critical issues with the movement system:

### CRITICAL ISSUES

1. **MISSING MOVEMENT QUEUE SYSTEM** ⚠️ HIGH PRIORITY
   - CLAUDE.md explicitly states "ALL enemy movement MUST use the movement queue system"
   - No movement queue implementation exists in the codebase
   - Enemies calculate and execute moves immediately (no queue, no prediction)
   - Movement prediction feature is completely absent

2. **Turn Alternation Issues**
   - Speed boost handling is complex and potentially buggy
   - `maybe_process_turn()` logic with speed_moves_remaining is scattered
   - No clear separation between player turn and enemy turn phases

3. **Buff/Debuff Tick-Down**
   - Temporary effects are processed in `TurnProcessor.process_turn()`
   - Looks correct but spread across multiple files
   - No centralized effect management

4. **Pathfinding**
   - Uses TCOD SimpleGraph correctly
   - Creates cost maps on-demand (no caching, potential performance issue)
   - Fallback to random movement when pathfinding fails
   - No path caching or queue

---

## Detailed Analysis

### 1. Turn Processing Flow

**Current Flow:**
```
Player Action (move/exploit)
  └─> move_player() or use_exploit()
      └─> maybe_process_turn()
          └─> TurnManager.process_turn()
              ├─> TurnProcessor.process_turn(player)
              │   ├─> advance_turn()
              │   ├─> _process_heat_management()
              │   ├─> _process_temporary_effects() ✅
              │   └─> _process_trace_increase()
              ├─> _process_enemies_turn() (legacy cooldowns)
              ├─> _process_environmental_effects() (mostly empty)
              ├─> _process_special_tiles()
              ├─> _update_enemies()
              │   ├─> Phase 1: _update_enemy_awareness()
              │   ├─> Phase 2: _move_enemies()
              │   └─> Phase 3: _process_enemy_attacks()
              ├─> _update_memory_system()
              └─> _check_admin_spawn()
```

**Issues:**
- Speed boost logic scattered (move_player:267-268, process_turn:32-34)
- `maybe_process_turn()` checks speed_moves_remaining but logic is unclear
- No movement queue, so no predictability for player

### 2. Buff/Debuff System

**Location:** `game_state.py:TurnProcessor._process_temporary_effects()`

**Effects Tracked:**
- `speed_boost_turns`
- `enhanced_vision_turns`
- `exploit_efficiency_turns`
- `virus_turns`

**Tick-Down Logic:**
```python
for effect_name in effects_to_update:
    if player.temporary_effects[effect_name] > 0:
        player.temporary_effects[effect_name] -= 1

        if player.temporary_effects[effect_name] == 0:
            # Effect expired - show message
```

**Status:** ✅ WORKING CORRECTLY
- Effects decrement each turn
- Messages displayed when effects expire
- Virus damage applied correctly

### 3. Enemy Pathfinding

**Implementation:** `game_characters.py:Enemy._calculate_hostile_move()`

**Process:**
1. Get target (player position or last_seen_player)
2. Check if adjacent (stop if yes)
3. Create cost map via `create_pathfinding_cost_map()`
4. Use TCOD SimpleGraph + Pathfinder
5. Return next step (path[1])
6. Fallback to random if pathfinding fails

**Issues:**
- ❌ No movement queue - calculates path every turn
- ❌ No path caching - expensive recreation
- ❌ No movement prediction for player
- ❌ Doesn't follow CLAUDE.md requirements

### 4. Movement Queue System

**Current State:** ❌ **DOES NOT EXIST**

**Required Features (per CLAUDE.md):**
- Enemies calculate intended path/moves and store in queue
- Movement prediction shows queue contents to player
- Each turn, execute first item from queue
- Update queue when targets change or paths invalid
- Applies to ALL movement types: RANDOM, SEEK, TRACK, LINEAR

**What Needs to be Built:**
```python
class Enemy:
    def __init__(self, ...):
        self.movement_queue: List[Position] = []
        self.movement_type: str = "..."  # RANDOM, SEEK, TRACK, LINEAR

    def update_movement_queue(self, player, game_map):
        """Recalculate and populate movement queue"""
        if self.state == HOSTILE:
            path = calculate_full_path(self.position, target)
            self.movement_queue = path[1:6]  # Next 5 moves
        elif self.type_data.movement == RANDOM:
            self.movement_queue = [random_adjacent_position()]
        # etc.

    def execute_queued_move(self, game_map, player, game_engine):
        """Execute first move from queue"""
        if not self.movement_queue:
            self.update_movement_queue(player, game_map)

        if self.movement_queue:
            next_pos = self.movement_queue.pop(0)
            if self._is_move_valid(next_pos, ...):
                self.position = next_pos
                return True
        return False
```

### 5. Speed Boost System

**Current Implementation:**

`game_engine.py:move_player()` (lines 267-268):
```python
if self.player.temporary_effects['speed_boost_turns'] == 0:
    self.player.speed_moves_remaining = 0
```

`game_turn_manager.py:process_turn()` (lines 32-34):
```python
if self.game_engine.player.temporary_effects['speed_boost_turns'] > 0 and self.game_engine.player.speed_moves_remaining == 0:
    self.game_engine.player.speed_moves_remaining = 2  # Grant 2 moves per enemy turn
```

`game_engine.py:maybe_process_turn()`:
```python
def maybe_process_turn(self):
    """Process turn only if player isn't using speed boost extra moves."""
    if self.player.speed_moves_remaining > 0:
        self.player.speed_moves_remaining -= 1
        return  # Don't process enemy turn yet
    self.process_turn()
```

**Issues:**
- Logic is split across 3 different locations
- Confusing flow: reset if 0 turns, grant 2 moves at start of turn
- `maybe_process_turn()` decrements and skips enemy turn
- Hard to reason about when enemies actually move

### 6. Enemy Movement Execution

**Current Implementation:** `game_turn_manager.py:_move_enemies()` (lines 369-380)

```python
def _move_enemies(self):
    """PHASE 2: Move all enemies according to their current awareness state."""
    for enemy in self.game_engine.enemies:
        if not getattr(enemy, 'has_moved_this_turn', False):
            if enemy.can_attack_player(self.game_engine.player):
                enemy.has_moved_this_turn = False  # Don't move if can attack
            else:
                did_move = enemy.move(game_map, player, game_engine)
                enemy.has_moved_this_turn = did_move
```

**Issues:**
- ❌ Calls `enemy.move()` which immediately calculates AND executes
- ❌ No queue - can't show prediction to player
- ❌ Recalculates path every turn (expensive)

---

## Recommended Fixes

### Priority 1: Implement Movement Queue System

**Changes Required:**

1. **Add queue to Enemy class** (`game_characters.py`)
   ```python
   def __init__(self, position: Position, enemy_type: str):
       # ... existing code ...
       self.movement_queue: List[Position] = []
       self.movement_plan_stale: bool = True
   ```

2. **Split calculate and execute**
   ```python
   def update_movement_plan(self, player, game_map, game_engine):
       """Calculate full movement plan and populate queue"""
       self.movement_queue.clear()

       if self.state == EnemyState.HOSTILE:
           target = self._get_current_target(player, game_map)
           if target:
               path = self._calculate_full_path(target, game_map, game_engine)
               self.movement_queue = path[1:6]  # Next 5 steps
       elif self.type_data.movement == EnemyMovement.PATROL:
           # Calculate path to next patrol point
           pass
       elif self.type_data.movement == EnemyMovement.RANDOM:
           # Add 1 random move
           self.movement_queue = [self._calculate_random_move(...)]

       self.movement_plan_stale = False

   def execute_next_move(self, game_map, player, game_engine) -> bool:
       """Execute first move from queue"""
       if self.disabled_turns > 0 or self.move_cooldown > 0:
           return False

       # Refresh plan if stale or empty
       if self.movement_plan_stale or not self.movement_queue:
           self.update_movement_plan(player, game_map, game_engine)

       if not self.movement_queue:
           return False

       next_pos = self.movement_queue[0]
       if self._is_move_valid(next_pos, game_map, player, game_engine):
           self.position = next_pos
           self.movement_queue.pop(0)
           return True
       else:
           # Path invalid, recalculate
           self.movement_plan_stale = True
           return False
   ```

3. **Mark plans stale when state changes**
   ```python
   def mark_movement_stale(self):
       """Mark movement plan as needing recalculation"""
       self.movement_plan_stale = True
   ```

4. **Update turn manager to use queue system**
   ```python
   def _move_enemies(self):
       for enemy in self.game_engine.enemies:
           if not enemy.has_moved_this_turn:
               if enemy.can_attack_player(...):
                   enemy.has_moved_this_turn = False
               else:
                   did_move = enemy.execute_next_move(...)
                   enemy.has_moved_this_turn = did_move
   ```

5. **Add movement prediction rendering**
   - Read enemy.movement_queue
   - Render faint path indicators on map
   - Show player where enemies will move

### Priority 2: Simplify Speed Boost Logic

**Consolidate into Player class:**
```python
class Player:
    def has_extra_moves(self) -> bool:
        return self.speed_moves_remaining > 0

    def use_extra_move(self):
        if self.speed_moves_remaining > 0:
            self.speed_moves_remaining -= 1

    def grant_speed_moves(self):
        if self.temporary_effects['speed_boost_turns'] > 0:
            self.speed_moves_remaining = 2
```

**Simplify maybe_process_turn:**
```python
def maybe_process_turn(self):
    if self.player.has_extra_moves():
        self.player.use_extra_move()
        # Still process player effects, but not enemies
        self.turn_processor.process_player_effects_only(self.player)
    else:
        self.process_turn()  # Full turn including enemies
```

### Priority 3: Centralize Effect Management

**Create EffectManager class:**
```python
class EffectManager:
    def tick_effects(self, player, message_log):
        """Process all effect tick-downs"""
        for effect_name, turns in player.temporary_effects.items():
            if turns > 0:
                player.temporary_effects[effect_name] -= 1
                if player.temporary_effects[effect_name] == 0:
                    self._handle_effect_expiration(effect_name, player, message_log)
```

---

## Testing Requirements

### Unit Tests Needed:

1. **Movement Queue Tests**
   - `test_enemy_queue_populates_on_hostile`
   - `test_enemy_queue_updates_when_target_changes`
   - `test_enemy_executes_queued_move`
   - `test_enemy_recalculates_on_invalid_path`
   - `test_random_enemy_one_move_queue`
   - `test_patrol_enemy_queue_toward_waypoint`

2. **Turn Alternation Tests**
   - `test_player_move_triggers_enemy_turn`
   - `test_speed_boost_grants_extra_moves`
   - `test_speed_boost_skips_enemy_turns`
   - `test_normal_turn_after_speed_boost_expires`

3. **Pathfinding Tests**
   - `test_pathfinding_around_walls`
   - `test_pathfinding_to_last_known_position`
   - `test_pathfinding_fallback_on_failure`

4. **Effect Tests**
   - `test_all_effects_tick_down_each_turn`
   - `test_effect_expiration_messages`
   - `test_virus_damage_applied_per_turn`

---

## Performance Considerations

**Current Issues:**
- Pathfinding cost map recreated every enemy, every turn
- No path caching

**Optimizations:**
1. Cache cost map per turn (if map unchanged)
2. Only recalculate enemy paths when:
   - State changes (UNAWARE → ALERT → HOSTILE)
   - Target moves significantly
   - Path becomes invalid
3. Use dirty flags on movement queue

**Estimated Improvement:**
- Current: O(n_enemies × pathfinding_cost) per turn
- With queue: O(n_enemies_with_stale_plans × pathfinding_cost) per turn
- Reduction: ~70-90% depending on enemy behavior

---

## Summary

### What Works
✅ Buff/debuff tick-down system
✅ TCOD pathfinding integration
✅ Three-phase enemy update (awareness, movement, attacks)
✅ FOV/vision system
✅ Turn counter and tracking

### What's Broken/Missing
❌ Movement queue system (CRITICAL - violates CLAUDE.md)
❌ Movement prediction for player
❌ Speed boost logic is confusing
❌ No path caching (performance)
❌ Movement plan staleness tracking

### Implementation Order
1. Implement movement queue system (HIGH PRIORITY)
2. Add movement prediction rendering
3. Simplify speed boost logic
4. Add comprehensive tests
5. Optimize with path caching
