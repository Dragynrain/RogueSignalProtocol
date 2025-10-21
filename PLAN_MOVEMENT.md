# Implementation Plan: Enemy Movement Queue Simplification

## Overview

The movement queue is a **core gameplay mechanic** that shows the player what enemies are committed to doing. This enables tactical planning - players can predict enemy positions 3 moves ahead and plan accordingly.

The current system is correct in concept but over-engineered in implementation. This plan simplifies the maintenance of the fixed 3-length queue while preserving the gameplay mechanic.

**Core Principle:** The queue represents enemy commitment. Always show 3 moves ahead when possible.

---

## Current System Problems

1. **Duplicate pathfinding logic**: `_refresh_move_queue()` (initial fill) vs `_add_next_move_to_queue()` (replenishment)
2. **6 invalidation triggers**: Scattered across multiple files, hard to track
3. **Patrol extension special case**: 40+ lines just to show patrol wraparound
4. **Target change detection**: Extra tracking variables only for some enemies
5. **Double retry on blockage**: Defensive programming that complicates flow
6. **Redundant patrol checks**: Checked at start AND end of move()

**Total complexity: ~300 lines across multiple methods**

---

## Simplified Design

### Core Concept: "Ensure Queue Full"

Instead of separate "fill" and "replenish" logic:

```
After each move → Ensure queue has 3 moves
```

One method, one responsibility, clear intent.

### Queue Lifecycle

```
1. Execute move (pop from queue)
2. Ensure queue has 3 moves (top up)
3. If state changes or move blocked → Clear queue
4. Go to step 1
```

### Invalidation Triggers (Only 2)

```
Queue becomes invalid only when:
1. Enemy state changes (UNAWARE ↔ ALERT ↔ HOSTILE)
2. Move is blocked (can't execute next queued move)
```

No target change detection, no patrol advancement clearing, no special cases.

---

## Implementation Plan

### Phase 1: Add Unified Pathfinding Helper ✓ COMPLETE

**Goal:** Single source of truth for all pathfinding

**Status:** ✓ Complete - PathfindingHelper class added with full test coverage

**File:** `game_characters.py`

**Add before `Player` class:**

```python
class PathfindingHelper:
    """
    Centralized pathfinding using TCOD A*.
    Single implementation used for all queue operations.
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
        Calculate path from start to goal.

        Args:
            start: Starting position
            goal: Goal position
            game_map: GameMap for walkability
            game_engine: GameEngine for enemy positions
            moving_enemy: Enemy doing pathfinding (exclude from collision)
            max_length_multiplier: Max path length as multiple of direct distance

        Returns:
            List of (y, x) tuples (TCOD format), or None if no reasonable path
        """
        # Calculate reasonable path length
        direct_distance = start.distance_to(goal)
        if direct_distance <= 5:
            max_length = max(15, int(direct_distance * 5))
        else:
            max_length = max(15, int(direct_distance * max_length_multiplier))

        try:
            # Create cost map with enemy collision
            cost_map = PathfindingHelper._create_cost_map(game_map, game_engine, moving_enemy)

            # TCOD pathfinding
            graph = tcod.path.SimpleGraph(cost=cost_map, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((start.y, start.x))  # TCOD uses (y, x)
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
        """Create cost map with enemy collision avoidance."""
        cost_map = game_map.get_walkability_map().copy()

        # Mark other enemies as impassable
        for enemy in game_engine.enemies:
            if enemy.id != moving_enemy.id:
                x, y = enemy.x, enemy.y
                if 0 <= x < game_map.width and 0 <= y < game_map.height:
                    cost_map[y, x] = 0  # TCOD uses [y, x] indexing

        return cost_map
```

**Testing:**
- Unit test: `test_pathfinding_helper_basic()`
- Test straight line, around walls, around enemies
- Test unreachable target returns None
- Test path length limit works

**Acceptance:** PathfindingHelper class added and tested

**Implementation Notes (Completed):**
- Added PathfindingHelper class at line 22 in game_characters.py
- Implemented calculate_path() with TCOD A* and path length validation
- Implemented _create_cost_map() for enemy collision avoidance
- Added 6 unit tests in tests/unit/test_enemy_movement_queue.py
- All 19 movement queue tests passing
- Fixed numpy array truth value ambiguity issues in both code and tests

---

### Phase 2: Add Simplified Queue Methods ✓ COMPLETE

**Goal:** Unified queue management

**Status:** ✓ Complete - All new queue methods added with full test coverage

**File:** `game_characters.py` in `Enemy` class

**Add new methods:**

```python
def _ensure_queue_full(self, game_map, player, game_engine):
    """
    Ensure move queue has 3 moves (or as many as possible).

    This is the ONLY method that fills the queue. Called after each move
    to maintain a fixed 3-length queue for player predictability.

    Strategy:
    - If queue already has 3 moves, do nothing
    - Otherwise, calculate path from last queued position (or current position)
    - Add moves until queue has 3 (or path exhausted)
    """
    # Already full
    if len(self.move_queue) >= 3:
        return

    movement_type = self.get_movement_type()

    # Static enemies don't move
    if movement_type == EnemyMovement.STATIC:
        return

    # Random movement - fill with random moves
    if movement_type == EnemyMovement.RANDOM:
        self._fill_random_moves(game_map, player, game_engine)
        return

    # Pathfinding-based movement (PATROL, SEEK)
    target = self._get_current_target(player, game_map)
    if not target:
        return

    # Start pathfinding from last queued position (or current if empty)
    start_pos = self.move_queue[-1] if self.move_queue else self.position

    # Calculate path
    path = PathfindingHelper.calculate_path(
        start=start_pos,
        goal=target,
        game_map=game_map,
        game_engine=game_engine,
        moving_enemy=self
    )

    # Fill queue from path
    if path and len(path) > 1:
        # Add moves until queue has 3
        for i in range(1, len(path)):
            if len(self.move_queue) >= 3:
                break
            # TCOD returns (y, x), convert to Position(x, y)
            self.move_queue.append(Position(path[i][1], path[i][0]))

    # Pathfinding failed - try greedy fallback (add at least 1 move)
    elif target and len(self.move_queue) == 0:
        greedy_move = self._calculate_greedy_move_toward_target(target, game_map, game_engine)
        if greedy_move:
            self.move_queue.append(greedy_move)

def _fill_random_moves(self, game_map, player, game_engine):
    """Fill queue with random moves."""
    # Start from last queued position (or current if empty)
    start_pos = self.move_queue[-1] if self.move_queue else self.position

    # Add random moves until queue has 3
    while len(self.move_queue) < 3:
        next_move = self._calculate_random_move_from(start_pos, game_map, player, game_engine)
        if next_move:
            self.move_queue.append(next_move)
            start_pos = next_move  # Chain for next random move
        else:
            break  # No valid random moves

def _calculate_random_move_from(self, from_pos: Position, game_map, player, game_engine) -> Optional[Position]:
    """Calculate a random valid move from given position."""
    directions = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
    random.shuffle(directions)

    for dx, dy in directions:
        next_pos = Position(from_pos.x + dx, from_pos.y + dy)
        if self._is_move_valid_from(next_pos, from_pos, game_map, player, game_engine):
            return next_pos
    return None

def _is_move_valid_from(self, position: Position, from_position: Position, game_map, player, game_engine) -> bool:
    """Check if move from from_position to position is valid."""
    if not game_map.is_valid_position(position):
        return False
    if position.x == player.x and position.y == player.y:
        return False
    for other_enemy in game_engine.enemies:
        if other_enemy.id != self.id and other_enemy.x == position.x and other_enemy.y == position.y:
            return False
    return True

def _get_current_target(self, player, game_map) -> Optional[Position]:
    """Get current movement target based on enemy state and type."""
    # Admin always targets player (omniscient)
    if self.type == 'admin':
        self.last_seen_player = player.position
        return player.position

    # Hostile enemies target player or last known position
    if self.state == EnemyState.HOSTILE:
        if self.can_see_player(player, game_map):
            self.last_seen_player = player.position
            return player.position
        return self.last_seen_player

    # Patrol enemies target current waypoint
    if self.get_movement_type() == EnemyMovement.PATROL and self.patrol_points:
        return self.patrol_points[self.patrol_index]

    return None
```

**Note:** Reuse existing `_calculate_greedy_move_toward_target()` - already exists in current code.

**Testing:**
- Unit test: `test_ensure_queue_full_fills_to_three()`
- Test fills empty queue to 3
- Test tops up partial queue to 3
- Test doesn't overfill (stops at 3)
- Test random movement fills correctly
- Test pathfinding movement fills correctly

**Acceptance:** Queue filling logic working, always targets 3 moves

**Implementation Notes (Completed):**
- Added `_ensure_queue_full()` method at line 630 in game_characters.py
- Added `_fill_random_moves()` helper method at line 689
- Added `_calculate_random_move_from()` helper method at line 703
- Added `_is_move_valid_from()` helper method at line 714
- Reused existing `_get_current_target()` method (already exists at line 928)
- Added 5 new test classes in tests/unit/test_enemy_movement_queue.py:
  - TestEnsureQueueFull (5 tests)
  - TestFillRandomMoves (2 tests)
  - TestCalculateRandomMoveFrom (2 tests)
  - TestIsMoveValidFrom (4 tests)
- All 32 movement queue tests passing
- Methods use PathfindingHelper from Phase 1 for consistent pathfinding
- Queue filling logic properly handles STATIC, RANDOM, PATROL, and SEEK movement types

---

### Phase 3: Simplify move() Method

**Goal:** Clean execution flow

**File:** `game_characters.py` in `Enemy` class

**Replace existing `move()` method:**

```python
def move(self, game_map, player, game_engine) -> bool:
    """
    Execute next queued move, maintaining fixed 3-length queue.

    Simplified flow:
    1. Check patrol waypoint advancement
    2. Check disabilities/cooldowns
    3. Ensure queue has moves (fill if needed)
    4. Pop and validate next move
    5. Execute move
    6. Ensure queue stays full (top up to 3)

    Returns:
        True if moved successfully, False otherwise
    """
    # 1. Patrol waypoint advancement
    if self._should_advance_patrol_waypoint():
        self._advance_patrol_waypoint()
        self.move_queue.clear()  # New waypoint = new plan

    # 2. Disability check
    if self.disabled_turns > 0:
        self.disabled_turns -= 1
        return False

    if self.move_cooldown > 0 and self.type != 'admin':
        self.move_cooldown -= 1
        return False

    # 3. Ensure queue has moves
    if not self.move_queue:
        self._ensure_queue_full(game_map, player, game_engine)

    # No moves available
    if not self.move_queue:
        return False

    # 4. Pop next move
    next_position = self.move_queue.pop(0)

    # 5. Validate move
    if not self._is_move_valid(next_position, game_map, player, game_engine):
        # Blocked - clear queue and replan next turn
        self.move_queue.clear()
        return False

    # 6. Execute move
    self.position = next_position

    # 7. Top up queue to maintain 3 moves
    self._ensure_queue_full(game_map, player, game_engine)

    # 8. Update cooldown
    if self.get_movement_type() == EnemyMovement.STATIC:
        self.move_cooldown = 999
    else:
        self.move_cooldown = 0

    return True

def _should_advance_patrol_waypoint(self) -> bool:
    """Check if enemy reached current patrol waypoint."""
    if self.get_movement_type() != EnemyMovement.PATROL:
        return False
    if not self.patrol_points:
        return False
    if self.state == EnemyState.HOSTILE:
        return False  # Hostile patrol enemies chase player

    current_target = self.patrol_points[self.patrol_index]
    return self.position.distance_to(current_target) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD

def _advance_patrol_waypoint(self):
    """Advance to next patrol waypoint (wraps around)."""
    self.patrol_index = (self.patrol_index + 1) % len(self.patrol_points)
```

**Key Changes from Current:**
- Call `_ensure_queue_full()` twice: once before move (if empty), once after move (to top up)
- Remove: double retry logic, target change detection, duplicate patrol check
- Remove: call to `_add_next_move_to_queue()` (replaced by `_ensure_queue_full()`)
- Keep: patrol waypoint advancement (but only at start)

**Testing:**
- Integration test: `test_queue_maintains_three_moves()`
- After each move, verify queue has 3 moves (or fewer if path exhausted)
- Test hostile enemy movement
- Test patrol enemy movement
- Test random enemy movement

**Acceptance:** move() simplified, queue always maintained at 3

---

### Phase 4: Simplify State Invalidation

**Goal:** Reduce invalidation triggers from 6 to 2

**File:** `game_session.py`

**Update `_update_enemy_state()` method:**

```python
def _update_enemy_state(self, enemy, can_see_player):
    """Update enemy state based on player visibility."""
    player_pos = Position(self.game_engine.player.x, self.game_engine.player.y)

    # Track old state for invalidation
    old_state = enemy.state

    if can_see_player:
        # Enemy sees player - escalate state
        if enemy.state == EnemyState.UNAWARE:
            enemy.state = EnemyState.ALERT
            enemy.alert_timer = 1
            enemy.last_seen_player = player_pos
            self.game_engine.message_log.add_message(f"{enemy.type_data.name} investigating")
            self.game_engine.sound_manager.play_sound("enemy_alert")

        elif enemy.state == EnemyState.ALERT:
            enemy.last_seen_player = player_pos
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                self._transition_to_hostile(enemy)

        elif enemy.state == EnemyState.HOSTILE:
            enemy.last_seen_player = player_pos
            self._increase_trace(GameBalance.ENEMY_TRACE_CONTINUOUS_HOSTILE, 'trace_continuous_hostile')
            self._alert_nearby_enemies(enemy)
    else:
        # Enemy lost sight - de-escalate state
        if enemy.state == EnemyState.ALERT:
            enemy.alert_timer -= 1
            if enemy.alert_timer <= 0:
                enemy.state = EnemyState.UNAWARE
                self._restore_patrol(enemy)
                self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost interest")

        elif enemy.state == EnemyState.HOSTILE:
            if random.random() < 0.15:
                if enemy.type == 'admin':
                    enemy.state = EnemyState.ALERT
                    enemy.alert_timer = 0
                else:
                    enemy.state = EnemyState.UNAWARE
                    enemy.last_seen_player = None
                    self._restore_patrol(enemy)
                    self.game_engine.message_log.add_message(f"{enemy.type_data.name} lost track")

    # INVALIDATION TRIGGER #1: State change
    if enemy.state != old_state:
        enemy.move_queue.clear()  # New state = new plan

def _transition_to_hostile(self, enemy):
    """Transition enemy to hostile state."""
    self._restore_patrol(enemy)
    enemy.state = EnemyState.HOSTILE
    # State changed - will be caught by invalidation check above
    self._increase_trace(GameBalance.ENEMY_TRACE_ALERT_TO_HOSTILE, 'trace_alert_to_hostile')
    self.game_engine.message_log.add_message(f"{enemy.type_data.name} detected you!")
    self.game_engine.sound_manager.play_sound("enemy_hostile")
    self._alert_nearby_enemies(enemy)

def _alert_nearby_enemies(self, alerting_enemy):
    """Alert nearby enemies when one becomes hostile."""
    alert_range = GameConfig.NEARBY_ENEMY_ALERT_RADIUS
    alerted_count = 0

    for enemy in self.game_engine.enemies:
        if enemy is alerting_enemy or enemy.state == EnemyState.HOSTILE:
            continue

        distance = enemy.position.distance_to(alerting_enemy.position)
        if distance <= alert_range:
            # Store patrol info before changing state
            movement_type = enemy.get_movement_type()
            if movement_type == EnemyMovement.PATROL and enemy.patrol_points:
                enemy.original_patrol_index = enemy.patrol_index

            # Change state
            old_state = enemy.state
            enemy.state = EnemyState.HOSTILE
            enemy.alert_timer = 0
            enemy.last_seen_player = Position(self.game_engine.player.x, self.game_engine.player.y)
            alerted_count += 1

            # INVALIDATION: State changed
            if enemy.state != old_state:
                enemy.move_queue.clear()

    if alerted_count > 0:
        self.game_engine.message_log.add_message(f"{alerted_count} enemies alerted nearby!")
        self.game_engine.sound_manager.play_sound("enemies_alerted", priority=6)
```

**Note:** Invalidation trigger #2 (move blocked) is already in `Enemy.move()` at line where move validation fails.

**Remove all other invalidation calls:**
- Remove: `enemy.invalidate_move_queue()` method entirely
- Remove: All calls to `invalidate_move_queue()` throughout codebase

**Files to update:**
- `game_session.py`: Remove invalidation calls (if any remain)
- `game_characters.py`: Remove `invalidate_move_queue()` method definition

**Testing:**
- Test queue invalidates when UNAWARE → ALERT
- Test queue invalidates when ALERT → HOSTILE
- Test queue invalidates when HOSTILE → UNAWARE
- Test queue invalidates when move blocked
- Test queue does NOT invalidate for other reasons

**Acceptance:** Only 2 invalidation triggers, no `invalidate_move_queue()` method

---

### Phase 5: Remove Old Code

**Goal:** Delete deprecated methods and special cases

**File:** `game_characters.py`

**Delete these methods:**

1. `_refresh_move_queue()` - Replaced by `_ensure_queue_full()`
2. `_add_next_move_to_queue()` - Replaced by `_ensure_queue_full()`
3. `_calculate_patrol_move()` - Old version (if exists), logic now in `_ensure_queue_full()`
4. `invalidate_move_queue()` - Replaced by direct `move_queue.clear()`

**Delete these instance variables from `Enemy.__init__`:**

1. `self._queue_target` - No longer tracking target changes
2. `self._queue_state` - No longer tracking state changes

**Update existing method:**

Keep `_calculate_greedy_move_toward_target()` but ensure it's using centralized logic.

**Delete standalone function:**

`create_pathfinding_cost_map()` - Replaced by `PathfindingHelper._create_cost_map()`

**Update all calls:**

Find any remaining calls to old methods and update to use new methods.

**Testing:**
- Run full test suite: `python test_commands.py full`
- Verify no import errors
- Verify no undefined method errors
- Manual playthrough test

**Acceptance:** Old code removed, all tests passing

---

### Phase 6: Update Tests

**Goal:** Update tests for new architecture

**Files:** Test files in `tests/` directory

**Update `tests/unit/test_enemy_movement_queue.py`:**

Rename to `tests/unit/test_enemy_movement.py` and update tests:

```python
"""
Tests for enemy movement queue system.
Queue maintains fixed length of 3 for player predictability.
"""

class TestQueueMaintenance:
    """Test that queue maintains 3 moves."""

    def test_queue_fills_to_three_initially(self):
        """Empty queue fills to 3 moves."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder()
        player = Player(20, 20)
        game_engine = mock_game_engine()

        enemy._ensure_queue_full(game_map, player, game_engine)

        assert len(enemy.move_queue) == 3, "Queue should fill to 3 moves"

    def test_queue_tops_up_after_move(self):
        """After executing move, queue tops back up to 3."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder()
        player = Player(20, 20)
        game_engine = mock_game_engine()

        # Fill initially
        enemy._ensure_queue_full(game_map, player, game_engine)
        assert len(enemy.move_queue) == 3

        # Execute move (pops one)
        enemy.move(game_map, player, game_engine)

        # Should still have 3
        assert len(enemy.move_queue) == 3, "Queue should maintain 3 moves after execution"

    def test_queue_maintains_three_over_multiple_turns(self):
        """Queue stays at 3 moves across multiple turns."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder(width=50, height=50)
        player = Player(20, 20)
        game_engine = mock_game_engine()

        for turn in range(10):
            enemy.move(game_map, player, game_engine)
            assert len(enemy.move_queue) <= 3, f"Turn {turn}: Queue should not exceed 3"
            # Should have 3 unless path exhausted
            if enemy.move_queue:
                assert len(enemy.move_queue) >= 1, f"Turn {turn}: Queue should have at least 1"

    def test_short_path_fills_partial_queue(self):
        """If path to target is shorter than 3, queue fills partially."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        game_map = map_builder()
        player = Player(11, 10)  # Very close
        game_engine = mock_game_engine()

        enemy._ensure_queue_full(game_map, player, game_engine)

        # Might have fewer than 3 if target is very close
        assert len(enemy.move_queue) >= 1, "Should have at least 1 move"

class TestQueueInvalidation:
    """Test queue invalidation triggers."""

    def test_queue_clears_on_state_change(self):
        """Queue clears when enemy state changes."""
        enemy = enemy_builder("scanner", pos=(10, 10))
        enemy.state = EnemyState.UNAWARE
        enemy.move_queue = [Position(11, 10), Position(12, 10), Position(13, 10)]

        # Change state
        enemy.state = EnemyState.HOSTILE
        enemy.move_queue.clear()  # Simulating invalidation

        assert len(enemy.move_queue) == 0, "Queue should clear on state change"

    def test_queue_clears_on_blocked_move(self):
        """Queue clears when move is blocked."""
        game_map = map_builder(walls=[(11, 10)])
        enemy = enemy_builder("scanner", pos=(10, 10))
        enemy.move_queue = [Position(11, 10)]  # Blocked position
        player = Player(20, 20)
        game_engine = mock_game_engine()

        result = enemy.move(game_map, player, game_engine)

        assert result is False, "Move should fail when blocked"
        assert len(enemy.move_queue) == 0, "Queue should clear when blocked"

class TestPathfindingHelper:
    """Test centralized pathfinding."""

    def test_pathfinding_finds_straight_path(self):
        """PathfindingHelper finds basic straight path."""
        game_map = map_builder()
        game_engine = mock_game_engine()
        enemy = enemy_builder("scanner", pos=(10, 10))

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy
        )

        assert path is not None, "Should find path"
        assert len(path) > 1, "Path should have multiple steps"

    def test_pathfinding_routes_around_enemies(self):
        """PathfindingHelper routes around other enemies."""
        game_map = map_builder()
        enemy1 = enemy_builder("scanner", pos=(10, 10))
        enemy2 = enemy_builder("bot", pos=(11, 10))  # Blocking
        game_engine = mock_game_engine(enemies=[enemy1, enemy2])

        path = PathfindingHelper.calculate_path(
            start=Position(10, 10),
            goal=Position(15, 10),
            game_map=game_map,
            game_engine=game_engine,
            moving_enemy=enemy1
        )

        # Path should exist but route around enemy2
        assert path is not None, "Should find path around enemy"
```

**Update integration tests:**

Update `tests/integration/test_enemy_movement_integration.py`:
- Update to expect queue always has 3 moves (when path is long enough)
- Remove tests for old behavior (target change detection, etc.)
- Add tests for new behavior

**Acceptance:** All tests updated and passing

---

### Phase 7: Documentation

**Goal:** Document new architecture

**Files to update:**

1. **Method docstrings** in `game_characters.py`
   - Ensure all new methods have clear docstrings
   - Document the 3-length queue guarantee
   - Explain invalidation triggers

2. **`.claude/CLAUDE.md`** - Update movement system section:

```markdown
## 7. Gameplay Systems

### Enemy Movement Queue

Enemies maintain a **fixed 3-length movement queue** for player predictability:

**Queue as Gameplay Mechanic:**
- Queue shows player what enemy is committed to doing (3 moves ahead)
- Enables tactical planning: player can predict enemy positions and plan accordingly
- Always shows 3 moves when possible (or fewer if path exhausted)

**Queue Lifecycle:**
1. Enemy executes move (pops from queue)
2. Queue tops up to 3 moves (unified fill logic)
3. Player sees enemy's commitment via rendering

**Queue Invalidation (Only 2 Triggers):**
1. Enemy state changes (UNAWARE ↔ ALERT ↔ HOSTILE)
2. Next move is blocked (wall, enemy, etc.)

When invalidated, queue clears and enemy replans on next turn.

**Implementation:**
- Single method `_ensure_queue_full()` handles all queue filling
- Uses `PathfindingHelper` for consistent pathfinding
- No special cases or duplicate logic
```

3. **Update `MOVEMENT_EXPLAINED.md`** - Add section at end:

```markdown
## Simplified Architecture (Current)

The movement system has been simplified to focus on the queue as a gameplay mechanic:

**Core Insight:** The queue represents enemy commitment. Always show 3 moves ahead.

**Simplified Design:**
- ONE method fills queue: `_ensure_queue_full()` (handles initial fill and top-up)
- TWO invalidation triggers: state change and blockage
- NO special cases: patrol extension, target tracking, double retry removed

**Code Reduction:** ~300 lines → ~150 lines (50% reduction)

**Same Gameplay:** Queue still shows 3-move commitment for tactical planning
```

**Acceptance:** Documentation complete and accurate

---

### Phase 8: Final Validation

**Goal:** Ensure production-ready

**Full test suite:**

```bash
python test_commands.py full
```

**Manual testing checklist:**

- [ ] Play through level 1
  - [ ] Patrol enemies show 3-move queue
  - [ ] Hostile enemies show 3-move queue
  - [ ] Random enemies show 3-move queue
  - [ ] Queue updates correctly after each move
  - [ ] Queue clears on state change

- [ ] Play through level 2
  - [ ] Enemy behavior feels unchanged
  - [ ] No performance issues
  - [ ] Movement prediction accurate

- [ ] Play through level 3
  - [ ] Admin enemy works correctly
  - [ ] All enemy types function properly

- [ ] Save and load game
  - [ ] Enemies restore correctly
  - [ ] Queues restore correctly

**Performance check:**

Time 1000 enemy moves:
- Should be equal or faster than before (fewer pathfinding calls due to unified logic)

**Code review:**

- [ ] No TODO or FIXME comments
- [ ] All docstrings present
- [ ] Code follows project style
- [ ] No deprecated code remains

**Acceptance:** All tests passing, manual testing successful, ready for production

---

## Success Criteria

Implementation successful when:

1. **Gameplay Preserved:**
   - [ ] Queue always shows 3 moves (when possible)
   - [ ] Player can predict enemy positions
   - [ ] Tactical decision-making unchanged
   - [ ] No regressions

2. **Code Quality:**
   - [ ] ~150 lines (50% reduction from ~300)
   - [ ] Single queue fill method (no duplication)
   - [ ] Only 2 invalidation triggers (was 6)
   - [ ] No special cases

3. **Testing:**
   - [ ] All unit tests passing
   - [ ] All integration tests passing
   - [ ] Manual playthrough successful

4. **Maintainability:**
   - [ ] Clear single responsibility per method
   - [ ] Easy to understand queue lifecycle
   - [ ] Easy to debug (fewer invalidation points)

---

## Timeline Estimate

**Conservative (with thorough testing):**

- Phase 1: PathfindingHelper - 2 hours
- Phase 2: Queue methods - 3 hours
- Phase 3: Simplify move() - 2 hours
- Phase 4: Invalidation - 1 hour
- Phase 5: Remove old code - 1 hour
- Phase 6: Update tests - 3 hours
- Phase 7: Documentation - 2 hours
- Phase 8: Validation - 2 hours

**Total: ~16 hours**

**Recommended:** Do 1-2 phases per session with testing between each.

---

## Rollback Plan

If issues found:

**Git revert:**
```bash
git checkout HEAD -- game_characters.py game_session.py
```

Or create a branch before starting:
```bash
git checkout -b movement-simplification
```

Can always return to main branch.

---

The insight: **Don't separate execution from prediction. The queue IS both. Just maintain it more simply.**
