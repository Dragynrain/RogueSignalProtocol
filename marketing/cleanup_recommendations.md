# Cleanup Recommendations for Alpha Release

## Files to Consider Removing (Leftover Development Files)

### 1. **Log Files** (Safe to delete)
- `game_debug.log` - Empty debug log
- `graphic-preview.log` - Graphics preview output log
- These regenerate when needed

### 2. **Error Output File** (Safe to delete)
- `nul` - Contains error output from a failed `dir` command
- Not needed in repository

### 3. **Development Scratch Files** (Safe to delete or move to archive)
- `preview_layout_new.py` - Code snippet for graphics preview layout (77 lines)
  - Not imported anywhere, appears to be scratch code
  - Could move to `.archive/` folder if you want to keep it

### 4. **Duplicate/Old Config Files** (Verify before deleting)
- `game_content.json` - Contains enemy/exploit data (309 lines)
  - **CHECK:** Is this used by the game or is `game_data.json` the canonical source?
  - Both have similar structure but slightly different names
  - `game_data.json` referenced in README
  - Search codebase to confirm which is loaded

### 5. **Save Files in Root** (Should be in saves/ folder)
- `rogue_signal_save.json` - Active save file (should be auto-managed)
- `rogue_signal_progress.json` - In saves/ folder (correct location)
- Consider: Should root-level save files be in `.gitignore`?

### 6. **Build Artifacts** (.gitignore check)
- All `__pycache__/` directories (numerous)
- All `.pyc` files in `build/` folder
- **Verify:** These should already be in `.gitignore`

---

## Files to Keep (Important)

### Configuration Files:
- ✅ `game_config.json` - Referenced in README, not found but might be generated
- ✅ `game_data.json` - Main game content (referenced in README)
- ✅ `game_rules.json` - Game balance settings
- ✅ `story_content.json` - All 21 story fragments
- ✅ `graphics_tiles.json` - Sprite mappings
- ✅ `user_settings.json` - Player settings (should be .gitignored if personal)

### Utility Scripts:
- ✅ `validate_json_config.py` - JSON validation utility (not imported but useful tool)
- ✅ `test_commands.py` - Test runner

### Documentation:
- ✅ `README.md` - Developer docs
- ✅ `README.txt` - Player-facing docs (NEW)
- ✅ `LICENSE` - GPL v3
- ✅ `PLAN_graphics.md` - Graphics implementation roadmap

---

## Recommended Actions

### Immediate (Before Alpha Release):

```bash
# 1. Delete temporary/log files
rm game_debug.log
rm graphic-preview.log
rm nul

# 2. Move scratch code to archive
mkdir .archive
mv preview_layout_new.py .archive/

# 3. Verify game_content.json vs game_data.json
# (Check which one is actually loaded by the game)
```

### Check `.gitignore` coverage:

Verify these patterns are in `.gitignore`:
```
__pycache__/
*.pyc
*.log
*.tmp
rogue_signal_save.json
user_settings.json
game_debug.log
```

### Optional Cleanup:

```bash
# Clean all Python cache (regenerates automatically)
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

---

## Important: game_content.json vs game_data.json

**MUST VERIFY** which file the game actually uses:

1. Search codebase for `game_content.json` references
2. Search codebase for `game_data.json` references
3. Determine if one is obsolete or if both serve different purposes
4. Only keep the one(s) actually used

**Why this matters:** Don't want to ship two config files with similar data - confusing for modders and can cause inconsistencies.

---

## Dead Code Analysis

### Scripts Not Imported:
- `validate_json_config.py` - Standalone utility (KEEP - useful for testing)
- `preview_layout_new.py` - Scratch code (DELETE or ARCHIVE)

### All other .py files appear to be part of the game's module system.

---

## Summary

**Safe to delete immediately:**
- `game_debug.log`
- `graphic-preview.log`
- `nul`
- `preview_layout_new.py` (or archive)

**Investigate before deleting:**
- `game_content.json` (vs `game_data.json` - which is used?)

**Add to .gitignore if not already:**
- `*.log`
- `rogue_signal_save.json`
- `__pycache__/`
- `*.pyc`

**Total cleanup impact:** Removes ~5-10 files, mostly clutter. Won't affect functionality.
