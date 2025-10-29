# TCOD TTF Font Sizing Problem - Investigation Summary

## 🔍 The Core Issue

**TCOD's `load_truetype_font()` scales down glyphs to "fit without stretching"**

When you specify both width and height parameters, TCOD internally shrinks the font to ensure it fits within the specified tile dimensions without distortion. This is why fonts always render smaller than expected.

## 📊 Test Results

Using CascadiaCode-Regular.ttf with target size 96×150 (compensating for 200% DPI):

| Method | Parameters | Result | Notes |
|--------|------------|--------|-------|
| **A: Explicit dimensions** | `load_truetype_font(path, 96, 150)` | 96×150 tileset | Glyphs scaled down inside tiles |
| **B: Auto-width (width=0)** | `load_truetype_font(path, 0, 150)` | **346×150 tileset** | 3.6× wider! ⭐ |
| **C: Custom FreeType loader** | `load_truetype_font_custom(path, 96, 150)` | 96×150 tileset | Manual 1.7× horizontal scaling |

## 💡 The Solution: `width=0` Trick

**From TCOD Issue #75 (maintainer recommendation):**

> "Exclude the width (use a width of `0`) of the font, then the font loader will automatically pick the width with the best fit."

### How It Works

When `tile_width=0`, the underlying C library (`TCOD_load_truetype_font_`) automatically calculates an appropriate width based on the font's actual metrics for the specified height.

**Result:** 346×150 tileset (3.6× wider than explicit sizing!)

## 🎯 Recommended Approach

**Use `tile_width=0` for auto-sizing:**

```python
def load_tileset():
    """Load TrueType font with automatic width calculation."""

    # Let TCOD calculate optimal width based on font metrics
    # For 200% DPI scaling, use physical height of 150 (= 75 effective)
    tileset = tcod.tileset.load_truetype_font(
        "CascadiaCode-Regular.ttf",
        tile_width=0,      # Auto-calculate width
        tile_height=150    # Physical height (compensates for DPI)
    )

    # Result: ~346×150 tileset (glyphs properly fill tiles!)
    return tileset
```

## 🔬 Why FreeType Coverage Is Only ~60%

From `test_freetype_sizes.py`:

- Requested: 64×64 pixels
- Actual bitmap: ~36×45 pixels (56% horizontal, 70% vertical)

**Explanation:** FreeType renders glyphs at their natural size based on font metrics, not the requested pixel size. The requested size is a "target" but FreeType respects the font's design metrics (ascent, descent, line spacing).

This is why manual scaling (1.7× horizontal) is needed in the custom loader.

## 📝 Implementation Options

### Option 1: Simple Fix (Recommended) ⭐

**Pros:**
- Single parameter change (`tile_width=0`)
- Uses official TCOD functionality
- Maintainer-recommended approach
- No external dependencies

**Cons:**
- Less control over exact dimensions
- Width is calculated automatically

**Code change:** `game_loop.py:69`
```python
# OLD
tileset = tcod.tileset.load_truetype_font("CascadiaCode-Regular.ttf", 96, 140)

# NEW
tileset = tcod.tileset.load_truetype_font("CascadiaCode-Regular.ttf", 0, 140)
```

### Option 2: Custom FreeType Loader

**Pros:**
- Full control over glyph rendering
- Can fine-tune scaling factors
- Handles baseline alignment precisely
- Better box-drawing character support

**Cons:**
- Additional complexity
- Requires FreeType dependency
- More code to maintain

**Status:** Already implemented in `font_loader_freetype.py`

## 🧪 Visual Comparison Test

Run `test_font_comparison.py` to see all three methods side-by-side:

```bash
python test_font_comparison.py
```

Press **1**, **2**, or **3** to switch between methods:
- **1** = Method A (explicit width+height) - Current approach
- **2** = Method B (width=0 auto-sizing) - Recommended fix
- **3** = Method C (custom FreeType) - Full control

Look for:
- Glyph size (do they fill the tiles?)
- Vertical wall gaps (│ should connect)
- Horizontal wall gaps (─ should connect)
- Descenders (g, y, p, q, j should have tails)

## 🎬 Next Steps

1. **Test Method B visually** - Run `test_font_comparison.py` and compare
2. **Choose approach:**
   - **Quick fix:** Change to `tile_width=0`
   - **Full control:** Switch to custom FreeType loader
3. **Update game_loop.py** with chosen approach
4. **Test in-game** with glyphs mode
5. **Verify box-drawing characters** connect properly

## 📚 References

- [TCOD Issue #75: Better options for TrueType Fonts](https://github.com/libtcod/python-tcod/issues/75)
- [python-tcod documentation: load_truetype_font](https://python-tcod.readthedocs.io/en/latest/tcod/tileset.html)
- FreeType sizing test: `test_freetype_sizes.py`
- Comparison test: `test_font_comparison.py`
- Custom loader: `font_loader_freetype.py`

---

**Date:** 2025-10-28
**Status:** Investigation complete, awaiting implementation decision
