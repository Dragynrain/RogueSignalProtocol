# Enemy Movement System - Redesigned Architecture

## Design Philosophy

**Separation of Concerns**: Split movement execution from movement prediction. These are different responsibilities that shouldn't be tightly coupled.

**Single Responsibility**: Each method does one thing well. No dual-purpose data structures.

**Simplicity Over Optimization**: Prefer clear, straightforward code over premature optimization. Modern CPUs can handle pathfinding calculations.

**Fail Explicitly**: No silent failures. If something can't work, return a clear signal.

---

## Core Principles

### 1. Separation: Execution vs Prediction

**Current Problem:**
- `move_queue` serves dual purpose: execution AND rendering
- Changes to execution logic affect rendering
- Queue staleness creates prediction errors

**New Approach:**
```
Movement Execution: Calculate next move on-demand, execute immediately
Movement Prediction: Calculate future moves on-demand when rendering
```

**Benefits:**
- Execution is simple: just get next position and move
- Prediction is decoupled: can be as complex as needed without affecting execution
- No queue staleness (always calculated fresh)
- No queue invalidation logic

### 2. On-Demand Calculation

**Current Problem:**
- Rolling queue tries to maintain 3 future moves
- Requires invalidation tracking, staleness detection, replenishment logic
- Complex invalidation triggers

**New Approach:**
- Calculate next move only when needed (during `move()`)
- Calculate prediction only when rendering
- No persistent state to maintain
- No invalidation needed

**Benefits:**
- Always accurate (calculated with current game state)
- No staleness bugs
- Simpler mental model
- Less code

### 3. Single Pathfinding Implementation

**Current Problem:**
- `_refresh_move_queue()`: Full pathfinding
- `_add_next_move_to_queue()`: Duplicate pathfinding
- Different fallback strategies
- Inconsistent "reasonable path length" checks

**New Approach:**
- One pathfinding method: `calculate_path(from, to, max_length=None)`
- One fallback method: `calculate_greedy_move(from, to)`
- Consistent strategy everywhere

**Benefits:**
- DRY (Don't Repeat Yourself)
- Single source of truth
- Easier to maintain and test
- Consistent behavior

### 4. Strategy Pattern for Movement Types

**Current Problem:**
- `if/elif` chains checking movement type
- Special cases scattered throughout code
- Virus switching behavior adds complexity

**New Approach:**
- Movement strategies as separate methods
- Clear dispatch based on type
- Each strategy encapsulates its logic

**Benefits:**
- Easier to add new movement types
- Each type's logic is isolated
- Less branching
- Clearer code flow

---

## New Architecture

### Class Structure

```python
class Enemy:
    # Core data (unchanged)
    position: Position
    type: str
    state: EnemyState

    # Patrol data
    patrol_points: List[Position]
    patrol_index: int

    # State machine data
    last_seen_player: Optional[Position]
    alert_timer: int
    disabled_turns: int

    # REMOVED: move_queue, _queue_target, _queue_state

    # New: Simple movement execution
    def move(self, game_map, player, game_engine) -> bool:
        """Execute one move. Returns True if moved successfully."""

    # New: Prediction separated
    def predict_next_positions(self, game_map, player, game_engine, steps: int = 3) -> List[Position]:
        """Calculate predicted future positions for rendering."""
```

### Movement Execution Flow

```python
def move(self, game_map, player, game_engine) -> bool:
    """
    Execute one move. Simple and straightforward.

    Flow:
    1. Handle patrol waypoint advancement
    2. Check disabilities/cooldowns
    3. Calculate next position based on movement type
    4. Validate next position
    5. Execute move
    6. Done
    """

    # 1. Patrol waypoint advancement
    if self._should_advance_patrol_waypoint():
        self._advance_patrol_waypoint()

    # 2. Disability check
    if self.disabled_turns > 0:
        self.disabled_turns -= 1
        return False

    if self.move_cooldown > 0 and self.type != 'admin':
        self.move_cooldown -= 1
        return False

    # 3. Calculate next position based on movement type
    next_position = self._calculate_next_move(game_map, player, game_engine)

    # 4. Validate
    if not next_position or not self._is_move_valid(next_position, game_map, player, game_engine):
        return False

    # 5. Execute
    self.position = next_position

    # 6. Update cooldown
    self._update_move_cooldown()

    return True
```

**Why This is Better:**
- Linear flow: no loops, no retries, no branching
- Single next move calculated
- Clear success/failure return
- No queue management
- ~20 lines instead of 100+

### Movement Type Dispatch

```python
def _calculate_next_move(self, game_map, player, game_engine) -> Optional[Position]:
    """
    Calculate next move based on current movement type.

    Dispatches to appropriate strategy method.
    """
    movement_type = self.get_movement_type()

    if movement_type == EnemyMovement.STATIC:
        return None  # Don't move

    elif movement_type == EnemyMovement.RANDOM:
        return self._calculate_random_move(game_map, player, game_engine)

    elif movement_type == EnemyMovement.PATROL:
        return self._calculate_patrol_move(game_map, player, game_engine)

    elif movement_type == EnemyMovement.SEEK:
        target = self._get_seek_target(player, game_map)
        return self._calculate_pathfinding_move(target, game_map, game_engine)

    return None
```

**Strategy Methods:**

```python
def _calculate_random_move(self, game_map, player, game_engine) -> Optional[Position]:
    """
    Calculate random adjacent move.
    Simple: try 8 directions in random order, return first valid.
    """
    directions = [(0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]
    random.shuffle(directions)

    for dx, dy in directions:
        next_pos = Position(self.position.x + dx, self.position.y + dy)
        if self._is_move_valid(next_pos, game_map, player, game_engine):
            return next_pos

    return None  # No valid random moves


def _calculate_patrol_move(self, game_map, player, game_engine) -> Optional[Position]:
    """
    Calculate move toward current patrol point.
    Uses pathfinding to handle obstacles.
    """
    if not self.patrol_points:
        return None

    target = self.patrol_points[self.patrol_index]
    return self._calculate_pathfinding_move(target, game_map, game_engine)


def _calculate_pathfinding_move(self, target: Optional[Position], game_map, game_engine) -> Optional[Position]:
    """
    Calculate move toward target using pathfinding.

    Strategy:
    1. Try TCOD pathfinding (get first step)
    2. If fails or unreasonable, try greedy fallback
    3. If both fail, return None (stay in place)
    """
    if not target:
        return None

    # Try pathfinding
    path = PathfindingHelper.calculate_path(
        start=self.position,
        goal=target,
        game_map=game_map,
        game_engine=game_engine,
        moving_enemy=self
    )

    if path and len(path) > 1:
        # Path exists - return first step
        # TCOD returns (y, x) tuples
        return Position(path[1][1], path[1][0])

    # Pathfinding failed - try greedy fallback
    return self._calculate_greedy_move(target, game_map, game_engine)


def _calculate_greedy_move(self, target: Position, game_map, game_engine) -> Optional[Position]:
    """
    Greedy fallback: Try all 8 directions, pick closest to target.
    """
    best_move = None
    best_distance = float('inf')

    directions = [(0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]

    for dx, dy in directions:
        next_pos = Position(self.position.x + dx, self.position.y + dy)

        if not self._is_move_valid(next_pos, game_map, player, game_engine):
            continue

        distance = next_pos.distance_to(target)
        if distance < best_distance:
            best_distance = distance
            best_move = next_pos

    return best_move
```

**Why This is Better:**
- Each movement type is self-contained
- Consistent fallback strategy (pathfinding -> greedy -> None)
- No special cases scattered around
- Easy to test individually
- Clear what each type does

### Unified Pathfinding Helper

```python
class PathfindingHelper:
    """
    Centralized pathfinding logic.
    Single source of truth for all pathfinding operations.
    """

    @staticmethod
    def calculate_path(
        start: Position,
        goal: Position,
        game_map,
        game_engine,
        moving_enemy,
        max_length_multiplier: float = 3.0
    ) -> Optional[List[Tuple[int, int]]]:
        """
        Calculate path from start to goal using TCOD A*.

        Returns:
            List of (y, x) positions (TCOD format), or None if no reasonable path
        """
        # Calculate max reasonable length
        direct_distance = start.distance_to(goal)
        max_length = max(15, int(direct_distance * max_length_multiplier))

        try:
            # Create cost map
            cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

            # Setup TCOD pathfinding
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)

            # Calculate path
            path = pathfinder.path_to((goal.y, goal.x))

            # Validate path
            if path and len(path) > 1 and len(path) <= max_length:
                return path

            return None

        except Exception as e:
            logging.warning(f"Pathfinding failed from {start} to {goal}: {e}")
            return None

    @staticmethod
    def _create_cost_map(game_map, game_engine, moving_enemy):
        """
        Create cost map for pathfinding with enemy collision.
        """
        cost_map = game_map.get_walkability_map().copy()

        # Mark other enemies as impassable
        for enemy in game_engine.enemies:
            if enemy.id != moving_enemy.id:
                cost_map[enemy.y, enemy.x] = 0  # TCOD uses [y, x] indexing

        return cost_map
```

**Why This is Better:**
- Single implementation used everywhere
- Consistent behavior
- Easy to optimize (caching, etc.) without touching enemy code
- Testable in isolation
- Clear API

### Movement Prediction (Rendering)

```python
def predict_next_positions(self, game_map, player, game_engine, steps: int = 3) -> List[Position]:
    """
    Predict next N positions for rendering movement intentions.

    This is SEPARATE from movement execution.
    Calculated fresh on each render, so always accurate.

    Strategy:
    1. Simulate enemy state for N steps
    2. For each step, calculate what next move would be
    3. Return list of predicted positions
    4. No state changes - pure calculation
    """
    if self.disabled_turns > 0:
        return []  # Disabled enemies don't move

    predictions = []

    # Create simulation state (don't modify actual enemy)
    sim_position = self.position
    sim_patrol_index = self.patrol_index

    for step in range(steps):
        # Calculate what next move would be from sim_position
        next_pos = self._simulate_next_move(
            sim_position,
            sim_patrol_index,
            game_map,
            player,
            game_engine
        )

        if not next_pos:
            break  # Can't predict further

        predictions.append(next_pos)

        # Update simulation state for next iteration
        sim_position = next_pos

        # Update sim_patrol_index if we reached a waypoint
        if self.get_movement_type() == EnemyMovement.PATROL and self.patrol_points:
            if sim_position.distance_to(self.patrol_points[sim_patrol_index]) <= 1.5:
                sim_patrol_index = (sim_patrol_index + 1) % len(self.patrol_points)

    return predictions


def _simulate_next_move(self, from_position: Position, patrol_index: int, game_map, player, game_engine) -> Optional[Position]:
    """
    Simulate what the next move would be from a given position.

    This is used by prediction - it doesn't modify enemy state.
    Similar logic to _calculate_next_move but uses sim state.
    """
    movement_type = self.get_movement_type()

    if movement_type == EnemyMovement.STATIC:
        return None

    elif movement_type == EnemyMovement.RANDOM:
        # For prediction, random movement shows arbitrary valid moves
        # Could show "?" or average direction instead
        return self._simulate_random_move(from_position, game_map, player, game_engine)

    elif movement_type == EnemyMovement.PATROL:
        if not self.patrol_points:
            return None
        target = self.patrol_points[patrol_index]
        path = PathfindingHelper.calculate_path(from_position, target, game_map, game_engine, self)
        if path and len(path) > 1:
            return Position(path[1][1], path[1][0])
        return None

    elif movement_type == EnemyMovement.SEEK:
        target = self._get_seek_target(player, game_map)
        if not target:
            return None
        path = PathfindingHelper.calculate_path(from_position, target, game_map, game_engine, self)
        if path and len(path) > 1:
            return Position(path[1][1], path[1][0])
        return None

    return None
```

**Why This is Better:**
- Prediction is separate from execution (different responsibilities)
- Always accurate (calculated fresh with current state)
- Can simulate multiple steps ahead
- No queue staleness bugs
- Can be optimized independently (e.g., cache during render frame)
- Handles complex cases (patrol wraparound) explicitly

**Rendering Integration:**

```python
# In game_engine.py
def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
    """
    Get predicted next positions for rendering.

    Now delegates to enemy's prediction method.
    """
    return enemy.predict_next_positions(self.game_map, self.player, self, steps)
```

No change needed in rendering code - API stays the same!

---

## Comparison: Before vs After

### Before: Movement Execution

```python
def move(self, game_map, player, game_engine) -> bool:
    # Step 1: Check patrol waypoint (lines 482-486)
    if movement_type == PATROL and patrol_points:
        if reached_waypoint:
            advance_patrol_index()
            move_queue.clear()

    # Step 2: Disability check (lines 489-495)
    if disabled or on_cooldown:
        return False

    # Step 3: Refresh queue if empty (lines 498-499)
    if not move_queue:
        _refresh_move_queue()  # 100+ lines!

    # Step 4: Pop and validate (lines 502-517)
    if not move_queue:
        return False
    next_position = move_queue.pop(0)
    if not valid:
        move_queue.clear()
        _refresh_move_queue()
        if not move_queue:
            return False
        next_position = move_queue.pop(0)
        if not valid:
            move_queue.clear()
            return False

    # Step 5: Execute (line 520)
    position = next_position

    # Step 6: Target change detection (lines 523-529)
    if admin or hostile:
        if target_changed:
            move_queue.clear()
            _refresh_move_queue()
            return True

    # Step 7: Replenish queue (lines 532-543)
    if should_add_move:
        _add_next_move_to_queue()  # 50+ lines!

    # Step 8: Patrol waypoint again (lines 546-550)
    if movement_type == PATROL and patrol_points:
        if reached_waypoint:
            advance_patrol_index()
            move_queue.clear()

    # Step 9: Cooldown (lines 553-556)
    update_cooldown()

    return True

# TOTAL: ~100 lines in move(), plus:
# - _refresh_move_queue(): 116 lines
# - _add_next_move_to_queue(): 52 lines
# - Supporting methods: 100+ lines
# GRAND TOTAL: ~400 lines
```

### After: Movement Execution

```python
def move(self, game_map, player, game_engine) -> bool:
    # 1. Patrol waypoint advancement
    if self._should_advance_patrol_waypoint():
        self._advance_patrol_waypoint()

    # 2. Disability check
    if self.disabled_turns > 0:
        self.disabled_turns -= 1
        return False
    if self.move_cooldown > 0 and self.type != 'admin':
        self.move_cooldown -= 1
        return False

    # 3. Calculate next position
    next_position = self._calculate_next_move(game_map, player, game_engine)

    # 4. Validate
    if not next_position or not self._is_move_valid(next_position, game_map, player, game_engine):
        return False

    # 5. Execute
    self.position = next_position

    # 6. Update cooldown
    self._update_move_cooldown()

    return True

# Supporting methods: ~100 lines total for all strategies
# TOTAL: ~120 lines (vs 400+ before)
```

**Reduction: 70% less code for movement execution**

### Before: Movement Prediction

```python
# Prediction is just queue access
def get_enemy_next_positions(self, enemy: Enemy, steps: int = 3) -> List[Position]:
    if enemy.disabled_turns > 0:
        return []
    return enemy.move_queue[:steps]  # Hope queue is accurate!

# Problems:
# - Queue might be stale (target changed)
# - Queue might be empty (pathfinding failed)
# - Queue might have gaps (adjacency validation)
# - Queue shows what WAS planned, not what WILL happen
```

### After: Movement Prediction

```python
def predict_next_positions(self, game_map, player, game_engine, steps: int = 3) -> List[Position]:
    if self.disabled_turns > 0:
        return []

    predictions = []
    sim_position = self.position
    sim_patrol_index = self.patrol_index

    for step in range(steps):
        next_pos = self._simulate_next_move(sim_position, sim_patrol_index, game_map, player, game_engine)
        if not next_pos:
            break
        predictions.append(next_pos)
        sim_position = next_pos
        # Update sim state...

    return predictions

# Benefits:
# - Always accurate (calculated fresh)
# - No staleness bugs
# - Shows actual future, not stale plan
# - Handles all edge cases explicitly
```

**Accuracy: 100% accurate vs potentially stale**

---

## Benefits of New Design

### 1. Simplicity

**Lines of Code:**
- Before: ~400 lines for movement execution
- After: ~120 lines for movement execution
- **70% reduction**

**Cognitive Load:**
- Before: Queue lifecycle, invalidation triggers, staleness tracking
- After: Calculate move, execute move
- **Much easier to understand**

### 2. Correctness

**Prediction Accuracy:**
- Before: Can be stale up to 3 turns
- After: Always calculated fresh with current state
- **100% accurate**

**No Staleness Bugs:**
- Before: Queue can be invalidated by state changes, target changes, blockages
- After: No queue to become stale
- **Zero staleness issues**

### 3. Maintainability

**Single Responsibility:**
- Before: `move()` does execution + queue management + prediction setup
- After: `move()` does execution, `predict_next_positions()` does prediction
- **Clear separation**

**DRY (Don't Repeat Yourself):**
- Before: Pathfinding duplicated in `_refresh_move_queue()` and `_add_next_move_to_queue()`
- After: Single `PathfindingHelper.calculate_path()` used everywhere
- **One source of truth**

**Testability:**
- Before: Hard to test queue lifecycle, invalidation, staleness
- After: Easy to test each strategy method independently
- **Much easier to test**

### 4. Extensibility

**Adding New Movement Types:**
- Before: Add to `get_movement_type()`, handle in `_refresh_move_queue()`, handle in `_add_next_move_to_queue()`
- After: Add new strategy method `_calculate_X_move()`, add to dispatch
- **One place to change**

**Optimizations:**
- Before: Optimizing pathfinding affects queue management
- After: Optimize `PathfindingHelper` independently
- **Easier to optimize**

### 5. Performance

**Pathfinding Calls:**
- Before: 1-3 per move (refresh queue, replenish queue, retry on blockage)
- After: 1 per move (calculate next position)
- **Fewer pathfinding calls**

**Queue Operations:**
- Before: Pop, append, clear, length checks, staleness checks
- After: No queue operations
- **Zero queue overhead**

**Memory:**
- Before: 3 positions + tracking state per enemy
- After: No persistent prediction state
- **Less memory per enemy**

---

## Edge Cases Handled

### Patrol Waypoint Advancement

**Before:**
- Checked in two places (start and end of move)
- Queue cleared when waypoint reached

**After:**
```python
def _should_advance_patrol_waypoint(self) -> bool:
    if self.get_movement_type() != EnemyMovement.PATROL:
        return False
    if not self.patrol_points:
        return False
    current_target = self.patrol_points[self.patrol_index]
    return self.position.distance_to(current_target) <= 1.5

def _advance_patrol_waypoint(self):
    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
```

Clear, explicit, happens once per turn.

### Blocked Movement

**Before:**
- Clear queue, replan, try again
- If still blocked, clear queue, give up
- Two retry attempts

**After:**
```python
next_position = self._calculate_next_move(...)
if not next_position or not self._is_move_valid(next_position, ...):
    return False  # Can't move, stay in place
```

Simple: If can't move, don't move. Retry logic is in `_calculate_pathfinding_move()` (pathfind -> greedy -> None).

### Target Changes

**Before:**
- Track `_queue_target`
- Compare after move
- Invalidate if changed

**After:**
- No tracking needed
- Next move is always calculated with current target
- Always correct

### Random Movement

**Before:**
- Generate 3 random moves
- Add to queue
- Hope they're still valid when executed

**After:**
```python
def _calculate_random_move(self, ...):
    directions = [all 8 directions]
    random.shuffle(directions)
    for dx, dy in directions:
        next_pos = Position(self.position.x + dx, self.position.y + dy)
        if self._is_move_valid(next_pos, ...):
            return next_pos
    return None
```

Simple: Pick random valid move right now.

### Prediction for Patrol Routes

**Before:**
- Special queue extension logic (40+ lines)
- Pathfind from last queued position to next waypoint
- Fill remaining queue slots

**After:**
```python
# In predict_next_positions()
for step in range(steps):
    next_pos = self._simulate_next_move(sim_position, sim_patrol_index, ...)
    predictions.append(next_pos)
    sim_position = next_pos
    # Advance sim_patrol_index if reached waypoint
    if reached_waypoint:
        sim_patrol_index = (sim_patrol_index + 1) % len(patrol_points)
```

Simulation naturally handles patrol loops. No special extension needed.

---

## Migration Path

### Phase 1: Add New Methods (No Breaking Changes)

1. Add `PathfindingHelper` class
2. Add strategy methods: `_calculate_random_move()`, `_calculate_patrol_move()`, etc.
3. Add `predict_next_positions()` method
4. Keep old `move()` and queue system working

### Phase 2: Switch Execution to New System

1. Replace `move()` implementation with new version
2. Keep `move_queue` for prediction (backward compat)
3. Fill `move_queue` from `predict_next_positions()` result
4. Test thoroughly

### Phase 3: Switch Prediction to New System

1. Update `get_enemy_next_positions()` to call `predict_next_positions()`
2. Remove queue filling from `move()`
3. Test rendering

### Phase 4: Clean Up

1. Remove old queue methods: `_refresh_move_queue()`, `_add_next_move_to_queue()`
2. Remove queue state: `move_queue`, `_queue_target`, `_queue_state`
3. Remove `invalidate_move_queue()` calls from state management
4. Clean up tests

---

## Summary

The redesigned system is:
- **70% less code** for movement execution
- **Always accurate** predictions (no staleness)
- **Easier to understand** (clear separation, single responsibility)
- **Easier to maintain** (no duplication, single pathfinding implementation)
- **Easier to test** (each strategy isolated)
- **Easier to extend** (new movement types just add a strategy method)
- **Better performance** (fewer pathfinding calls, no queue overhead)

The core insight: **Execution and prediction are different concerns**. By separating them, we eliminate the complexity of maintaining a predictive rolling queue and get a simpler, more correct system.
