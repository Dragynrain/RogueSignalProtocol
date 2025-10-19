# TCOD Coordinate Systems - CRITICAL REFERENCE

## 🚨 THE FUNDAMENTAL RULE 🚨

**TCOD uses numpy-style [y, x] indexing for ALL array operations.**

```python
# Game logic coordinates: (x, y) - column, row
position = Position(x=10, y=5)

# TCOD array indexing: [y, x] - row, column
console.rgba["bg"][5, 10, 3] = 255  # Note: [y, x] NOT [x, y]!
```

**This is SWAPPED from what you might expect!**

---

## Common Indexing Patterns

### ✓ CORRECT Patterns

```python
# Pattern 1: Nested loops with correct indexing
for y in range(height):
    for x in range(width):
        console.rgba["bg"][y, x, 3] = 255  # [y, x] matches loop order

# Pattern 2: Using Position objects
pos = Position(x=10, y=5)
console.rgba["bg"][pos.y, pos.x, 3] = 255  # Extract y first, x second

# Pattern 3: Getting array dimensions
actual_height, actual_width = console.rgba["bg"].shape[:2]  # shape is (height, width)

# Pattern 4: TCOD FOV/pathfinding
fov = tcod.map.compute_fov(transparency, pov=(y, x), ...)  # (y, x) tuple
path = pathfinder.path_to((y, x))  # (y, x) tuple
```

### ✗ WRONG Patterns (will cause bugs!)

```python
# Bug 1: Loop variables don't match indexing
for x in range(width):
    for y in range(height):
        console.rgba["bg"][x, y, 3] = 255  # BUG: should be [y, x]

# Bug 2: Using Position coordinates in wrong order
pos = Position(x=10, y=5)
console.rgba["bg"][pos.x, pos.y, 3] = 255  # BUG: transposed!

# Bug 3: Assuming shape is (width, height)
width, height = console.rgba["bg"].shape[:2]  # BUG: actually (height, width)!

# Bug 4: TCOD functions with (x, y) tuples
fov = tcod.map.compute_fov(transparency, pov=(x, y), ...)  # BUG: should be (y, x)
```

---

## Why This Matters

**Example Bug: Transparency at wrong location**

```python
# Transparency pass with wrong indexing
for x in range(game_area_width):
    for y in range(game_area_height):
        console.rgba["bg"][x, y, 3] = 0  # Sets transparency at (y=x, x=y)!

# Result: If you want to make (10, 20) transparent,
# this code makes (20, 10) transparent instead.
# Dialogue drawn at (10, 20) stays visible (wrong!)
# Area at (20, 10) becomes transparent (wrong!)
```

---

## Quick Reference Table

| Operation | Coordinate Order | Example |
|-----------|------------------|---------|
| Game Position object | `(x, y)` | `Position(x=10, y=5)` |
| Console print/draw | `(x, y)` | `console.print(x=10, y=5, ...)` |
| Console array indexing | `[y, x]` | `console.rgba["bg"][5, 10, 3]` |
| TCOD FOV pov parameter | `(y, x)` | `compute_fov(..., pov=(5, 10))` |
| TCOD path_to parameter | `(y, x)` | `pathfinder.path_to((5, 10))` |
| Array shape | `(height, width)` | `shape = (50, 80)` means 50 tall, 80 wide |

---

## The Mnemonic

**"Arrays are row-major, positions are column-first"**

- **Arrays**: Think spreadsheet - row then column = `[y, x]`
- **Positions**: Think Cartesian plane - x-axis then y-axis = `(x, y)`

---

## When In Doubt

1. Check if you're working with a **Position object** → use `(x, y)` or extract `pos.y, pos.x`
2. Check if you're **indexing an array** → use `[y, x]`
3. Check if you're calling **TCOD functions** → read the docs, most use `(y, x)`
4. **If confused**: Add a comment explaining the coordinate order!

```python
# Example with defensive commenting
enemy_x, enemy_y = enemy.position.x, enemy.position.y  # Position: (x, y)
cost_map[enemy_y, enemy_x] = 0  # Array indexing: [y, x]
```
