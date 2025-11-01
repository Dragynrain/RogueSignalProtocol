# Distance Calculation Guide

**CRITICAL: Choose the right distance function!**

The codebase has TWO distance calculation methods with different use cases:

## Quick Reference

```python
# ✅ CORRECT - Gameplay mechanics (exploits, adjacency, AoE)
distance = pos1.grid_distance_to(pos2)
if distance <= 1:  # All 8 adjacent tiles

# ❌ WRONG - Don't use Euclidean for gameplay!
distance = pos1.distance_to(pos2)
if distance <= 1.5:  # Hack to make diagonals work
```

---

## Position.grid_distance_to(other) - Chebyshev Distance

**Use for: Gameplay mechanics**

- ✅ Exploit range validation
- ✅ AoE radius calculations
- ✅ Adjacency checks (melee attacks, waypoint arrival)
- ✅ Enemy alert chains
- ✅ Any gameplay feature that treats diagonals as 1 step

**Why:** Matches 8-directional grid movement. Diagonal = 1 step.

**Examples:**
```python
# Range-1 exploits can target all 8 adjacent tiles
if player.position.grid_distance_to(target) <= 1:
    execute_buffer_overflow(target)

# AoE radius 2 covers a 5x5 grid (25 tiles)
if enemy.position.grid_distance_to(center) <= 2:
    apply_stun(enemy)

# Check if arrived at waypoint
if self.position.grid_distance_to(waypoint) <= 1:
    advance_to_next_waypoint()
```

---

## Position.distance_to(other) - Euclidean Distance

**Use for: Visual/spatial calculations**

- ✅ Vision range (TCOD FOV uses Euclidean internally)
- ✅ Level generation (enemy/node placement from spawn)
- ✅ Pathfinding heuristics (A* typically uses Euclidean)
- ✅ Rendering distance fog/lighting effects
- ✅ UI distance indicators

**Why:** Natural spatial distance, works with TCOD's internal systems.

**Examples:**
```python
# Vision range check (TCOD FOV uses Euclidean)
if enemy.position.distance_to(player.position) <= vision_range:
    can_see = tcod.map.compute_fov(...)

# Level generation - place enemy far from spawn
if enemy_pos.distance_to(spawn) >= min_spawn_distance:
    spawn_enemy(enemy_pos)
```

---

## DEPRECATED: ADJACENT_DISTANCE_THRESHOLD

**❌ DO NOT USE `GameBalance.ADJACENT_DISTANCE_THRESHOLD = 1.5`**

This is a hack to make Euclidean distance work for diagonals (sqrt(2) ≈ 1.414 < 1.5 < 2).

**Replace this:**
```python
# ❌ OLD - Euclidean hack
if pos1.distance_to(pos2) <= GameBalance.ADJACENT_DISTANCE_THRESHOLD:
    # Adjacent
```

**With this:**
```python
# ✅ NEW - Grid distance
if pos1.grid_distance_to(pos2) <= 1:
    # Adjacent (all 8 tiles)
```

---

## Math Details

### Grid Distance (Chebyshev)
```
distance = max(abs(x2 - x1), abs(y2 - y1))

Examples:
(0,0) → (1,0)  = 1  (orthogonal)
(0,0) → (1,1)  = 1  (diagonal)
(0,0) → (2,1)  = 2
(0,0) → (3,2)  = 3
```

### Euclidean Distance
```
distance = sqrt((x2-x1)² + (y2-y1)²)

Examples:
(0,0) → (1,0)  = 1.0    (orthogonal)
(0,0) → (1,1)  = 1.414  (diagonal)
(0,0) → (2,1)  = 2.236
(0,0) → (3,2)  = 3.606
```

---

## Refactoring Checklist

When you see:
- `distance_to()` with gameplay mechanics → Change to `grid_distance_to()`
- `ADJACENT_DISTANCE_THRESHOLD` → Replace with `grid_distance_to() <= 1`
- Distance checks for vision/FOV → Keep as `distance_to()` (TCOD uses Euclidean)
- Distance for level gen placement → Keep as `distance_to()` (spatial distance)

---

## Common Pitfalls

1. **❌ Using distance_to for exploit ranges**
   - Diagonals become ~1.414, failing range-1 checks
   - Fix: Use `grid_distance_to()`

2. **❌ Using grid_distance for TCOD FOV**
   - TCOD's internal FOV uses Euclidean
   - Keep: Use `distance_to()` for vision pre-checks

3. **❌ Mixing distance types**
   - Be consistent within a system
   - Exploits: ALL grid distance
   - Vision: ALL Euclidean distance
