# TCOD Coordinate Systems - CRITICAL REFERENCE

## 🚨 THE FUNDAMENTAL RULE 🚨

**TCOD console array indexing depends on the console's memory order!**

### Console Creation Determines Indexing

```python
# Game uses Fortran order (order='F')
console = tcod.console.Console(80, 50, order='F')
# → Array shape: (80, 50, 4) = (width, height, channels)
# → Indexing: [x, y, channel]
# → This is what the game uses!

# Tests/default use C order (default)
console = tcod.console.Console(80, 50)
# → Array shape: (50, 80, 4) = (height, width, channels)
# → Indexing: [y, x, channel]
# → This is the TCOD default
```

**You MUST check the console's memory order before indexing arrays!**

---

## How to Detect Console Order

```python
# Detect order by checking if shape matches console dimensions
is_fortran_order = (console.rgba["bg"].shape[0] == console.width)

if is_fortran_order:
    # order='F': array is (width, height, channels)
    console.rgba["bg"][x, y, 3] = 255  # [x, y, channel]
else:
    # default: array is (height, width, channels)
    console.rgba["bg"][y, x, 3] = 255  # [y, x, channel]
```

**CoordinateHelpers.set_alpha_region() handles this automatically - use it!**

---

## Why This Caused the Dialogue Transparency Bug

**The Bug:**
- Game uses `Console(80, 50, order='F')` → requires `[x, y]` indexing
- All alpha-setting code used `[y, x]` indexing (assuming default order)
- Result: Alpha was set at **transposed coordinates**!
- Dialogue at position (20, 17) had alpha set at (17, 20) instead
- Dialogue box stayed transparent because alpha was set in wrong location

**The Fix:**
- CoordinateHelpers now detects console order
- Uses correct indexing based on detected order
- Works with both order='F' (game) and default (tests)

---

## Correct Patterns for the Game (order='F')

### ✓ CORRECT Patterns

```python
# Pattern 1: Use CoordinateHelpers (RECOMMENDED)
from game_coordinate_helpers import CoordinateHelpers

# Set transparency - handles indexing automatically
CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=0)

# Pattern 2: Detect order and index correctly
is_fortran = (console.rgba["bg"].shape[0] == console.width)

if is_fortran:
    # order='F': use [x, y]
    for x in range(10, 40):
        for y in range(5, 20):
            console.rgba["bg"][x, y, 3] = 255
else:
    # default: use [y, x]
    for y in range(5, 20):
        for x in range(10, 40):
            console.rgba["bg"][y, x, 3] = 255

# Pattern 3: Game logic always uses (x, y) for positions
pos = Position(x=10, y=5)
console.print(pos.x, pos.y, "@")  # console.print() uses (x, y)

# Pattern 4: Array slicing for order='F'
# Top row (y=0, all x)
console.rgba["bg"][:, 0, 3] = 255  # [all x, y=0, alpha]
# Right column (x=79, all y)
console.rgba["bg"][79, :, 3] = 255  # [x=79, all y, alpha]
```

### ✗ WRONG Patterns (will cause transparency bugs!)

```python
# Bug 1: Assuming all consoles use [y, x] indexing
for y in range(height):
    for x in range(width):
        console.rgba["bg"][y, x, 3] = 255  # WRONG for order='F'!

# Bug 2: Assuming shape is always (height, width)
height, width = console.rgba["bg"].shape[:2]  # WRONG for order='F'!
# With order='F', shape is (width, height)!

# Bug 3: Array slicing without checking order
console.rgba["bg"][0, :, 3] = 255  # May be top row OR left column!
```

---

## TCOD Functions (Order-Independent)

**Good news:** TCOD's high-level functions always use `(x, y)` order regardless of console memory order!

```python
# These always use (x, y) order
console.print(x=10, y=5, "text")  # Always (x, y)
console.draw_rect(x=10, y=5, width=20, height=10, ...)  # Always x, y, width, height
console.draw_frame(x=10, y=5, width=20, height=10, ...)  # Always x, y, width, height

# Position objects always use (x, y)
pos = Position(x=10, y=5)
```

**BUT:** When accessing `.rgba`, `.ch`, `.fg`, `.bg` arrays directly, order matters!

---

## Quick Decision Tree

```
Are you calling a TCOD function like console.print()?
├─ YES → Use (x, y) order
└─ NO → Are you accessing console.rgba/ch/fg/bg arrays?
    ├─ YES → Detect console order first!
    │   ├─ Use CoordinateHelpers (recommended)
    │   └─ Or check: is_fortran = (shape[0] == width)
    └─ NO → You're fine, carry on
```

---

## The Game's Choice: Why order='F'?

The game uses `order='F'` (Fortran order) which:
- Creates array shape (width, height, channels) instead of (height, width, channels)
- Uses [x, y] indexing which matches console.print(x, y) parameter order
- Was likely chosen for consistency with function call order

**This is fine, but you MUST use [x, y] indexing when accessing arrays!**

---

## Common Mistakes in This Codebase

**Mistake 1:** Copying code from TCOD examples
- Most TCOD examples use default order
- They use [y, x] indexing
- This breaks when used in our order='F' game!

**Mistake 2:** Assuming shape is (height, width)
```python
# ✗ WRONG
height, width = console.rgba["bg"].shape[:2]

# ✓ CORRECT (for game)
width, height = console.rgba["bg"].shape[:2]

# ✓ CORRECT (order-independent)
if console.rgba["bg"].shape[0] == console.width:
    width, height = console.rgba["bg"].shape[:2]
else:
    height, width = console.rgba["bg"].shape[:2]
```

**Mistake 3:** Not using CoordinateHelpers
- CoordinateHelpers handles all this complexity
- It detects order and uses correct indexing
- Always use it for alpha/transparency operations!

---

## The Mnemonic

**"Check the order before you index the array"**

1. High-level TCOD functions → Always (x, y)
2. Array access → Detect order first!
3. When in doubt → Use CoordinateHelpers

---

## Testing Note

**Tests use default order, game uses order='F'**

When writing tests:
- Tests typically create `Console(80, 50)` without order parameter
- This uses default order = [y, x] indexing
- Game creates `Console(80, 50, order='F')` = [x, y] indexing
- **CoordinateHelpers works with both** - that's why we use it!

---

## See Also

- `.claude/CONSOLE_TRANSPARENCY_RULES.md` - Transparency and alpha channel specifics
- `game_coordinate_helpers.py` - Reusable coordinate utilities that handle order detection
