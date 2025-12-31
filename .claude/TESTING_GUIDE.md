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
- **AUTOMATED** - Pre-commit hook runs full test suite automatically
- Manual bypass: `git commit --no-verify` (emergencies only)

---

## Token Budget (CRITICAL)

- Single file: 1-3k (good)
- Pattern match (`-k`): 3-7k (good)
- Last-failed (`--lf`): 2-5k (good)
- Summary only: 1k (good)
- **Full suite: 20-30k** AVOID

**Goal:** < 10k tokens per session on testing

---

## Common Test Patterns

| Changed File | Run This |
|--------------|----------|
| rsp/systems/audio.py | `pytest tests/unit/test_audio_system.py -v` |
| rsp/core/config.py | `pytest tests/unit/test_config_loading.py -v` |
| rsp/entities/characters.py | `pytest tests/integration/test_enemy_pathfinding_fixes.py -v` |
| rsp/combat/combat.py | `pytest tests/ -k "combat" -v` |
| rsp/input/*.py | `pytest tests/unit/test_input_validation.py -v` |
| rsp/rendering/*.py | `pytest tests/ -k "rendering" --tb=short` |

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

BAD: Running full suite multiple times
BAD: Not using `--lf` when iterating
BAD: Seeing `[XXX characters truncated]`
BAD: Using `-v` on full suite

GOOD: Use `-q --tb=no | tail -20` for quick checks
GOOD: Use `--lf` when fixing failures
GOOD: Run smallest relevant subset
GOOD: Save full suite for final validation
