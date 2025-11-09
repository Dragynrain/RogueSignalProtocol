# Testing Guide - Quick Reference for Claude

## DEFAULT: Always use these patterns

**Changed 1-2 files?**
```bash
pytest tests/unit/test_<module>.py -v
```

**Iterating on fixes?**
```bash
pytest --lf --tb=short
```

**Quick sanity check?**
```bash
pytest tests/ -q --tb=no 2>&1 | tail -20
```

**Before commit?**
```bash
pytest tests/ --tb=short
```

---

## Token Budget (CRITICAL)

- Single file: 1-3k ✅
- Pattern match (`-k`): 3-7k ✅
- Last-failed (`--lf`): 2-5k ✅
- Summary only: 1k ✅
- **Full suite: 20-30k** ⚠️ AVOID

**Goal:** < 10k tokens per session on testing

---

## Common Test Patterns

| Changed File | Run This |
|--------------|----------|
| game_audio.py | `pytest tests/unit/test_audio_system.py -v` |
| game_config.py | `pytest tests/unit/test_config_loading.py -v` |
| game_characters.py | `pytest tests/integration/test_enemy_pathfinding_fixes.py -v` |
| game_combat.py | `pytest tests/ -k "combat" -v` |
| game_input.py | `pytest tests/unit/test_input_validation.py -v` |
| game_rendering_*.py | `pytest tests/ -k "rendering" --tb=short` |

---

## Pytest Flags (Quick Ref)

**Output:**
- `-q` = quiet (summary only)
- `-v` = verbose (show test names)
- `--tb=no` = no traceback (fastest)
- `--tb=short` = short traceback (good default)
- `--tb=line` = one line per failure

**Selection:**
- `--lf` = last-failed only
- `-k "pattern"` = match test name
- `-x` = stop on first failure
- `--maxfail=N` = stop after N failures

---

## RED FLAGS (Stop Wasting Tokens!)

❌ Running full suite multiple times
❌ Not using `--lf` when iterating
❌ Seeing `[XXX characters truncated]`
❌ Using `-v` on full suite

✅ Use `-q --tb=no | tail -20` for quick checks
✅ Use `--lf` when fixing failures
✅ Run smallest relevant subset
✅ Save full suite for final validation
