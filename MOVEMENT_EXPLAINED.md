# Current Enemy Movement System - Detailed Explanation

## Overview

The current enemy movement system is built around a **rolling FIFO queue** architecture where each enemy maintains a 3-position queue of planned moves. This queue serves dual purposes: **movement execution** AND **movement prediction rendering**. The system coordinates with a two-phase update cycle and integrates tightly with pathfinding, state management, and rendering.

---

## Core Architecture

### 1. The Movement Queue (FIFO, Size 3)

Each `Enemy` instance has:
```python
self.move_queue: List[Position] = []  # Max size: 3 positions
self._queue_target: Optional[Position] = None  # What target was queue calculated for
self._queue_state: EnemyState = self.state  # What state was enemy in when queue calculated
```

**Queue Lifecycle:**
1. **Initialize**: Queue starts empty when enemy spawns
2. **Refresh**: When queue is empty, call `_refresh_move_queue()` to calculate up to 3 moves
3. **Execute**: Each turn, `pop(0)` the first position and move to it
4. **Replenish**: After moving, call `_add_next_move_to_queue()` to add 1 move to the back
5. **Invalidate**: When state/target changes, clear queue via `invalidate_move_queue()`

This is a **rolling queue** - it maintains 3 future moves by adding one each turn to replace the one consumed.

---

## Movement Flow (Per Turn)

### Phase 1: Two-Pass Update System (`game_session.py::_update_enemies()`)

**Pass 1: Awareness Update (ALL enemies)**
- `_update_all_enemy_awareness()` runs for every enemy
- Updates state machine: UNAWARE -> ALERT -> HOSTILE
- Handles enemy communication (alerting nearby enemies)
- Invalidates queues when state changes
- **Critical**: This must happen for ALL enemies before any movement to ensure proper alert propagation

**Pass 2: Action Processing (Each enemy individually)**
```python
for enemy in enemies:
    if enemy.can_attack_player(player):
        # Adjacent - attack instead of moving
        enemy.attack_player(player)
    else:
        # Not adjacent - execute movement
        enemy.move(game_map, player, game_engine)
```

### Phase 2: Individual Enemy Movement (`game_characters.py::Enemy.move()`)

This is where the complexity lives. Here's the full flow:

#### Step 1: Patrol Waypoint Advancement
```python
if movement_type == EnemyMovement.PATROL and patrol_points:
    current_patrol_target = patrol_points[patrol_index]
    if position.distance_to(current_patrol_target) <= ADJACENT_THRESHOLD:
        patrol_index = (patrol_index + 1) % len(patrol_points)
        move_queue.clear()  # Triggers refresh below
```

**Caveats:**
- This happens at the START of move, before consuming queue
- Also duplicated at the END of move (lines 546-550) - redundant?
- Clearing queue forces recalculation toward new waypoint

#### Step 2: Disability/Cooldown Check
```python
if disabled_turns > 0:
    disabled_turns -= 1
    return False
if move_cooldown > 0 and type != 'admin':
    move_cooldown -= 1
    return False
```

#### Step 3: Queue Refresh (If Empty)
```python
if not move_queue:
    _refresh_move_queue(player, game_map, game_engine)
```

This is where the first complexity bomb explodes (see "Queue Refresh Deep Dive" below).

#### Step 4: Pop and Validate Next Move
```python
next_position = move_queue.pop(0)  # FIFO
if not _is_move_valid(next_position, game_map, player, game_engine):
    # BLOCKED! Clear queue and try again
    move_queue.clear()
    _refresh_move_queue(player, game_map, game_engine)
    if not move_queue:
        return False  # Can't move at all
    next_position = move_queue.pop(0)
    if not _is_move_valid(next_position, ...):
        move_queue.clear()
        return False  # Still blocked - give up
```

**Caveats:**
- If blocked, tries to replan TWICE
- Second failure means enemy stays in place
- Queue cleared on blockage, so next turn will replan from scratch

#### Step 5: Execute Move
```python
position = next_position
```

Simple! Just update position.

#### Step 6: Target Change Detection (Admin/Hostile only)
```python
if type == 'admin' or state == EnemyState.HOSTILE:
    current_target = _get_current_target(player, game_map)
    if current_target != _queue_target:
        # Player moved! Replan entire queue
        move_queue.clear()
        _refresh_move_queue(player, game_map, game_engine)
        return True
```

**Caveats:**
- Only tracking enemies check this
- Non-tracking enemies (patrol, random) don't invalidate on target changes
- This means queue might be 1 turn stale for hostile enemies if player moved

#### Step 7: Queue Replenishment (Rolling Queue)
```python
current_target = _get_current_target(player, game_map)
should_add_move = False

if type == 'admin' or state == EnemyState.HOSTILE:
    should_add_move = current_target and not position.is_adjacent_to(player.position)
elif movement_type == EnemyMovement.RANDOM:
    should_add_move = True
elif current_target:
    should_add_move = True

if should_add_move:
    _add_next_move_to_queue(player, game_map, game_engine)
```

**Caveats:**
- Doesn't add if already adjacent to target (prevents wasted pathfinding)
- Random enemies always add (to maintain 3 moves)
- This is where the second complexity bomb is (see "Queue Replenishment Deep Dive")

#### Step 8: Patrol Waypoint Advancement (Again!)
```python
# DUPLICATE of Step 1!
if movement_type == EnemyMovement.PATROL and patrol_points:
    current_target = patrol_points[patrol_index]
    if position.distance_to(current_target) <= ADJACENT_THRESHOLD:
        patrol_index = (patrol_index + 1) % len(patrol_points)
        move_queue.clear()
```

**Why duplicate?** Seems like defensive programming - ensure we advance even if we somehow missed it earlier.

#### Step 9: Reset Cooldown
```python
if movement_type == EnemyMovement.STATIC:
    move_cooldown = 999  # Never move again
else:
    move_cooldown = 0
```

---

## Queue Refresh Deep Dive

### `_refresh_move_queue()` - 116 lines of complexity

This method recalculates the queue from scratch. Here's the breakdown:

#### Step 1: Clear and Update Tracking
```python
move_queue.clear()
_queue_state = state
_queue_target = _get_current_target(player, game_map)
```

#### Step 2: Early Exit for Static
```python
if movement_type == EnemyMovement.STATIC:
    return  # No moves needed
```

#### Step 3: Pathfinding (Admin/Hostile/Patrol)
```python
if type == 'admin' or state == EnemyState.HOSTILE or movement_type == EnemyMovement.PATROL:
    path = _calculate_path_to_target(_queue_target, game_map, game_engine)

    # Fallback to greedy if pathfinding fails
    if (path is None or len(path) <= 1) and _queue_target:
        fallback_move = _calculate_greedy_move_toward_target(...)
        if fallback_move:
            move_queue.append(fallback_move)
    elif path is not None and len(path) > 1:
        # Add up to 3 moves from path
        prev_pos = position
        for i in range(1, min(len(path), 4)):
            next_pos = Position(path[i][1], path[i][0])  # TCOD returns (y,x)

            # CRITICAL: Validate adjacency
            if not prev_pos.is_adjacent_to(next_pos):
                break  # Path has gap - stop adding

            move_queue.append(next_pos)
            prev_pos = next_pos

            # Stop if adjacent to target
            if _queue_target and next_pos.is_adjacent_to(_queue_target):
                break
```

**Caveats:**
- TCOD pathfinding returns `(y, x)` tuples, must convert to `Position(x, y)`
- Must validate each step is adjacent to prevent "teleporting"
- Greedy fallback only on initial fill, not used in replenishment
- Stops early if path reaches adjacent to target (no need for more moves)

#### Step 4: Patrol Queue Extension (Special Case)
```python
# If queue doesn't have 3 moves and this is a patrol enemy, extend toward next waypoint
if (movement_type == EnemyMovement.PATROL and
    state != EnemyState.HOSTILE and
    patrol_points and
    len(patrol_points) >= 2 and
    len(move_queue) < 3):

    try:
        # Start from last queued position
        last_queued_pos = move_queue[-1] if move_queue else position

        # Get NEXT patrol point (wrap around)
        next_patrol_index = (patrol_index + 1) % len(patrol_points)
        next_patrol_target = patrol_points[next_patrol_index]

        # Pathfind from last queued to next patrol point
        cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((last_queued_pos.y, last_queued_pos.x))
        next_path = pathfinder.path_to((next_patrol_target.y, next_patrol_target.x))

        # Add remaining moves to fill queue to 3
        if next_path and len(next_path) > 1:
            moves_to_add = 3 - len(move_queue)
            for i in range(1, min(len(next_path), moves_to_add + 1)):
                next_pos = Position(next_path[i][1], next_path[i][0])
                if last_queued_pos.is_adjacent_to(next_pos):
                    move_queue.append(next_pos)
                    last_queued_pos = next_pos
                else:
                    break  # Gap detected
    except Exception as e:
        logging.warning(f"Failed to extend patrol queue: {e}")
```

**Why This Exists:**
- Short patrol routes (2 points close together) would only fill 1-2 queue slots
- Player sees incomplete movement prediction (only 1-2 ghost positions)
- Solution: Calculate path to NEXT patrol point and fill remaining slots
- Shows patrol enemies circling their route

**Caveats:**
- Only for patrol enemies not in hostile state
- Only if patrol has 2+ points
- Only if queue has fewer than 3 moves
- Pathfinding from last queued position, NOT current position
- Can fail silently (just logs warning)
- Adds significant complexity for visual polish

#### Step 5: Random Movement
```python
elif movement_type == EnemyMovement.RANDOM:
    for i in range(3):
        next_move = _calculate_random_move(game_map, player, game_engine)
        if next_move:
            move_queue.append(next_move)
        else:
            break  # No valid random moves
```

**Caveats:**
- Random moves calculated from last queued position (rolling queue behavior)
- May get fewer than 3 if stuck

---

## Queue Replenishment Deep Dive

### `_add_next_move_to_queue()` - Maintaining the Rolling Queue

Called after moving to add 1 move to the back of the queue.

#### Step 1: Check Queue Size
```python
if len(move_queue) >= 3:
    return  # Already full
```

#### Step 2: Random Movement (Special Case)
```python
if movement_type == EnemyMovement.RANDOM and type != 'admin' and state != EnemyState.HOSTILE:
    next_move = _calculate_random_move(game_map, player, game_engine)
    if next_move:
        move_queue.append(next_move)
    return
```

#### Step 3: Calculate Start Position
```python
start_pos = move_queue[-1] if move_queue else position
target = _get_current_target(player, game_map)

if not target:
    return  # No target, can't add move
```

**Caveat:** Pathfinding starts from LAST QUEUED position, not current position!

#### Step 4: Early Exit if Adjacent
```python
if start_pos.is_adjacent_to(target):
    return  # Already at target, don't add more
```

#### Step 5: Pathfinding (DUPLICATE LOGIC!)
```python
if type == 'admin' or state == EnemyState.HOSTILE or movement_type == EnemyMovement.PATROL:
    try:
        # Check reasonable path length
        direct_distance = start_pos.distance_to(target)
        max_reasonable_path_length = max(6, int(direct_distance * 3))

        # Do pathfinding (SAME LOGIC AS _refresh_move_queue!)
        cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((start_pos.y, start_pos.x))
        path = pathfinder.path_to((target.y, target.x))

        if len(path) > 1:
            # Check if path is reasonable
            if len(path) <= max_reasonable_path_length:
                next_pos = Position(path[1][1], path[1][0])

                # Validate adjacency
                if start_pos.is_adjacent_to(next_pos):
                    move_queue.append(next_pos)
            # else: Path too long, skip this move
    except Exception as e:
        logging.warning(f"Failed to add move: {e}")
```

**Caveats:**
- Duplicates pathfinding setup from `_refresh_move_queue()`
- Has "reasonable path length" check (3x direct distance)
- If path too long, silently skips (queue stays short)
- Must validate adjacency to prevent gaps
- No greedy fallback (unlike refresh)

---

## Movement Prediction Rendering

### How Prediction Works

Rendering code (both graphics and glyph modes) calls:
```python
next_positions = game_engine.get_enemy_next_positions(enemy, steps=3)
```

Which simply returns:
```python
def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
    if enemy.disabled_turns > 0:
        return []
    return enemy.move_queue[:steps]  # Just slice the queue!
```

**Rendering then:**
1. Iterates over predicted positions
2. Skips positions where other enemies are standing
3. Renders ghost sprites with fading brightness:
   - Position 0: Bright
   - Position 1: Medium
   - Position 2: Dim

**Caveats:**
- Prediction is only as good as the queue
- If queue is stale (target changed but not yet detected), prediction is wrong
- If queue has gaps (adjacency validation failed), prediction is incomplete
- If pathfinding failed, queue might be empty (no prediction shown)

---

## Pathfinding System

### `create_pathfinding_cost_map()` - Enemy Collision Avoidance

```python
def create_pathfinding_cost_map(game_map, game_engine, moving_enemy):
    # Start with walkability map (walls = 0, floors = 1+)
    cost_map = game_map.get_walkability_map().copy()

    # Mark all OTHER enemies as impassable
    for enemy in game_engine.enemies:
        if enemy != moving_enemy:
            x, y = enemy.x, enemy.y
            # CRITICAL: TCOD uses [y, x] indexing!
            cost_map[y, x] = 0  # Impassable

    return cost_map
```

**Why Enemies Block:**
- Prevents enemies from pathfinding through each other
- Forces enemies to wait or route around
- Creates more realistic movement

**Caveats:**
- Cost map is recalculated for EVERY pathfinding call
- No caching between queue operations
- If many enemies are pathfinding, this is expensive

### `_calculate_path_to_target()` - Full Path Calculation

```python
def _calculate_path_to_target(self, target: Optional[Position], game_map, game_engine):
    if not target:
        return None

    try:
        # Calculate direct distance
        direct_distance = self.position.distance_to(target)

        # Set max reasonable path length
        if direct_distance <= 5:
            max_reasonable_path_length = max(15, int(direct_distance * 5))
        else:
            max_reasonable_path_length = max(15, int(direct_distance * 3))

        # TCOD pathfinding
        cost_map = create_pathfinding_cost_map(game_map, game_engine, self)
        graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((self.position.y, self.position.x))  # (y, x) order!
        path = pathfinder.path_to((target.y, target.x))

        # Check if path is reasonable
        if len(path) > 1 and len(path) <= max_reasonable_path_length:
            return path
        return None
    except Exception as e:
        logging.warning(f"Pathfinding failed: {e}")
        return None
```

**"Reasonable Path Length":**
- Prevents enemies from taking absurdly long routes
- Short distances (<=5): Allow 5x direct distance
- Long distances: Allow 3x direct distance
- If path exceeds this, returns None (enemy waits instead)

**Why?** Prevents enemies from routing through entire map when slightly blocked.

### `_calculate_greedy_move_toward_target()` - Fallback When Pathfinding Fails

```python
def _calculate_greedy_move_toward_target(self, target: Position, game_map, game_engine):
    if not target:
        return None

    best_move = None
    best_distance = float('inf')

    # Try all 8 adjacent directions
    directions = [(0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]

    for dx, dy in directions:
        next_pos = Position(self.position.x + dx, self.position.y + dy)

        # Validate position
        if not next_pos.is_valid(game_map.width, game_map.height):
            continue
        if game_map.is_wall(next_pos):
            continue

        # CRITICAL: Skip positions with other enemies
        enemy_blocking = any(e.position.x == next_pos.x and e.position.y == next_pos.y
                           for e in game_engine.enemies if e.id != self.id)
        if enemy_blocking:
            continue

        # Calculate distance to target
        distance = next_pos.distance_to(target)

        # Track best valid move
        if distance < best_distance:
            best_distance = distance
            best_move = next_pos

    return best_move
```

**When Used:**
- Only in `_refresh_move_queue()` when pathfinding fails
- Not used in `_add_next_move_to_queue()` (inconsistency!)
- Simple greedy: Pick adjacent move closest to target

**Caveats:**
- Can get stuck in local minima (blocked by enemies)
- Doesn't avoid walls intelligently
- Only used for initial queue fill, not replenishment

---

## Movement Type Handling

### `get_movement_type()` - Virus Complexity

```python
def get_movement_type(self) -> EnemyMovement:
    if self.type == 'virus':
        if self.state == EnemyState.HOSTILE:
            return EnemyMovement.SEEK  # Chase player
        elif self.original_movement_type is not None:
            return self.original_movement_type  # Use mimicked type
        return self.type_data.movement  # Fallback
    return self.type_data.movement
```

**Virus Special Behavior:**
- Spawns with random `original_movement_type` (STATIC, RANDOM, PATROL, or SEEK)
- When UNAWARE/ALERT: Uses `original_movement_type`
- When HOSTILE: Overrides to SEEK (active chase)
- This creates variety (viruses that patrol, viruses that are static, etc.)

**Caveats:**
- Only virus has this switching behavior
- Other enemies have fixed movement types
- Adds branching to all movement type checks

### Movement Type Behaviors

1. **STATIC**:
   - `move_cooldown = 999` (never move)
   - Queue stays empty
   - No prediction shown

2. **RANDOM**:
   - Generates 3 random valid adjacent moves
   - Each move calculated from last queued position
   - Can get stuck if no valid random moves

3. **PATROL**:
   - Pathfinds to `patrol_points[patrol_index]`
   - When adjacent to waypoint, advances `patrol_index`
   - Special queue extension to show full patrol loop
   - Hostile patrol enemies switch to seeking player

4. **SEEK**:
   - Admin always uses SEEK
   - Hostile enemies use SEEK
   - Pathfinds to player's last seen position
   - Invalidates queue when player moves

---

## State Management

### State Transitions

```
UNAWARE --(sees player)--> ALERT (1 turn) --(timer expires)--> HOSTILE
   ^                           |
   |                           |
   +---(loses sight)----------+

HOSTILE --(15% chance when loses sight)--> UNAWARE
```

### Queue Invalidation Triggers

The queue is cleared (forcing recalculation) when:

1. **State change** (via `invalidate_move_queue()`):
   - UNAWARE -> ALERT
   - ALERT -> HOSTILE
   - HOSTILE -> UNAWARE
   - Called from `game_session.py::_update_enemy_state()`

2. **Patrol waypoint reached**:
   - When `distance_to(patrol_point) <= ADJACENT_THRESHOLD`
   - Happens in TWO places (start and end of move)

3. **Move blocked**:
   - When `_is_move_valid()` returns False
   - Triggers immediate replan (twice!)

4. **Target changed** (tracking enemies only):
   - When `_queue_target != current_target`
   - Only for admin and hostile enemies
   - Checked after move executes

**Caveats:**
- Non-tracking enemies (patrol, random) don't invalidate on target changes
- Multiple invalidation points can trigger in same turn
- Each invalidation recalculates entire queue (expensive)

---

## Identified Complexity Issues

### 1. Dual Purpose Queue
- Queue is used for BOTH execution AND prediction
- Tightly couples movement logic with rendering
- Can't change one without affecting the other

### 2. Pathfinding Duplication
- `_refresh_move_queue()`: Full pathfinding setup
- `_add_next_move_to_queue()`: Identical pathfinding setup
- No shared logic, maintained separately
- Different fallback strategies (greedy vs skip)

### 3. Patrol Queue Extension
- 40+ lines of special-case logic
- Only for visual polish (showing full patrol loop)
- Can fail silently
- Pathfinds from last queued position to next waypoint

### 4. State Tracking Overhead
- `_queue_target` and `_queue_state` track staleness
- Only used for tracking enemies (admin/hostile)
- Other enemies don't need this
- Adds cognitive load

### 5. Adjacency Validation Everywhere
- Every queue addition checks `is_adjacent_to()`
- Prevents "teleporting" from pathfinding gaps
- Duplicate checks in multiple places
- No guarantee queue is always valid

### 6. Reasonable Path Length Checks
- Present in multiple places with different thresholds
- Prevents infinite pathfinding
- But different values in different methods:
  - `_calculate_path_to_target()`: 3x or 5x direct distance
  - `_add_next_move_to_queue()`: 3x direct distance
- Inconsistent

### 7. Blockage Handling Complexity
- When move blocked: clear queue, replan, try again
- If still blocked: clear queue, give up
- Two retry attempts built into move flow
- Can lead to wasted pathfinding

### 8. Movement Type Branching
- Every movement operation checks movement type
- Virus has special switching behavior
- Patrol has special extension logic
- Random has special generation logic
- No polymorphism, just `if/elif` chains

### 9. Queue Staleness
- Queue can be up to 3 turns old
- Target changes only detected for tracking enemies
- Non-tracking enemies show stale predictions
- No guarantee prediction matches actual future

### 10. Exception Handling Inconsistency
- Patrol extension: `try/except` with logging
- Other pathfinding: No exception handling
- Silent failures vs loud failures
- Hard to debug

---

## Summary of the Current System

**What It Does Well:**
- Shows player 3 moves ahead (when working)
- Enemies route around each other
- Smooth movement without jittering
- Visual feedback of enemy intentions

**What Creates Complexity:**
- Rolling queue maintenance (pop front, add back)
- Dual purpose (execution + prediction)
- Pathfinding duplication
- State tracking for invalidation
- Special cases for patrol extension
- Adjacency validation everywhere
- Multiple invalidation triggers
- Inconsistent retry/fallback strategies
- Movement type branching

**Core Problem:**
The system tries to maintain a **predictive rolling queue** while handling **dynamic environment changes**. This creates tension between:
- Efficiency (don't recalculate every turn)
- Accuracy (react to changes immediately)
- Completeness (always show 3 moves)
- Correctness (validate adjacency, handle blockages)

The result is a complex system with many edge cases, special handling, and defensive programming that's hard to reason about and maintain.
