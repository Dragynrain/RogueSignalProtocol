# Distance Calculation Refactor Summary

## Problem

Range-1 exploits like Buffer Overflow were failing on diagonal targets because the code used **Euclidean distance** where diagonals = ~1.414, not 1.

The codebase had a hack: `ADJACENT_DISTANCE_THRESHOLD = 1.5` to make Euclidean work for "adjacency" checks. This was confusing and inconsistent.

## Solution

Added `Position.grid_distance_to()` using **Chebyshev distance** where diagonals = 1 (matches 8-directional grid movement).

**Key principle:**
- **Gameplay mechanics** (exploits, AoE, adjacency) → Use `grid_distance_to()`
- **Vision/spatial** (TCOD FOV, level gen) → Use `distance_to()` (Euclidean)

## Files Changed

### 1. game_entities.py
- Added `Position.grid_distance_to()` method with comprehensive documentation
- Added warning to `distance_to()` directing to grid distance for gameplay

### 2. game_combat.py
- `_validate_target()`: Now uses `grid_distance_to()` for exploit range
- `_execute_buffer_overflow()`: Uses grid distance, checks `> 1`
- `_execute_noise_maker()`: AoE radius uses grid distance
- `_disable_area_enemies()`: AoE radius uses grid distance
- `_execute_system_crash()`: AoE radius uses grid distance
- `_execute_memory_leak()`: AoE radius uses grid distance
- Added comments throughout explaining "diagonals count as 1"

### 3. game_characters.py
- Line 708: Shadow adjacency check → `grid_distance_to() > 1`
- Line 473: Player sees adjacent enemy → `grid_distance_to() <= 1`
- Line 482: Enemy in shadow visibility → `grid_distance_to() > 1`
- Line 853: Patrol waypoint arrival → `grid_distance_to() <= 1`
- Line 1036: Patrol waypoint skip → `grid_distance_to() <= 1`

### 4. game_session.py
- Line 561: Enemy alert chain radius → `grid_distance_to()`

### 5. .claude/CLAUDE.md
- Added distance calculation guidance to section 4

### 6. .claude/DISTANCE_GUIDE.md (NEW)
- Comprehensive guide on when to use each distance method
- Examples and refactoring checklist
- Documents the ADJACENT_DISTANCE_THRESHOLD deprecation

### 7. tests/unit/test_grid_distance.py (NEW)
- Tests for grid distance calculations
- Tests that all 8 adjacent tiles are distance 1
- Tests that Buffer Overflow can target diagonals
- Tests AoE radius consistency

## Impact

### Fixed
✅ Range-1 exploits (Buffer Overflow) now work on all 8 adjacent tiles
✅ AoE effects use consistent grid distance
✅ Patrol waypoint arrival uses proper adjacency
✅ Shadow visibility uses proper adjacency
✅ Enemy alert chains use proper distance

### Preserved
✅ Vision range checks still use Euclidean (matches TCOD FOV)
✅ Level generation still uses Euclidean (spatial placement)
✅ Pathfinding heuristics still use Euclidean

### Deprecated
❌ `GameBalance.ADJACENT_DISTANCE_THRESHOLD = 1.5` is now a hack
   - Should be phased out completely
   - All uses replaced with `grid_distance_to() <= 1`

## Testing

All 1519 tests pass, including:
- 11 new grid distance tests
- Existing combat/exploit tests
- Existing enemy AI tests
- Integration tests

## Future Work

Consider removing `ADJACENT_DISTANCE_THRESHOLD` from:
- `game_config.py` (line 550)
- `game_rules.json` (balance.adjacent_distance_threshold)

It's no longer needed now that we use proper grid distance.

## Migration Guide

**Old pattern:**
```python
if pos1.distance_to(pos2) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
    # Adjacent
```

**New pattern:**
```python
if pos1.grid_distance_to(pos2) <= 1:
    # Adjacent (all 8 tiles)
```

**When to keep Euclidean:**
```python
# Vision - TCOD uses Euclidean internally
if player.position.distance_to(enemy.position) <= vision_range:
    can_see = tcod.map.compute_fov(...)
```

See `.claude/DISTANCE_GUIDE.md` for complete details.
