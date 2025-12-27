# Release Checklist

Reusable checklist for alpha, beta, and stable releases.

---

## Phase 1: Pre-Build Preparation

### 1.1 Version String Updates

Update version in ALL these locations (search for old version string):

**Code files:**
- [ ] `game_menu_about.py` - Lines ~129, ~145 (2 locations)
- [ ] `game_menu_main.py` - Line ~240
- [ ] `game_save.py` - Line ~81 (save file version)
- [ ] `game_story.py` - Line ~52 (progress data version)

**Config files:**
- [ ] `game_rules.json` - Line ~2 (version), line ~915 (welcome message), line ~962 (metadata)
- [ ] `game_content.json` - Lines ~330, ~333 (metadata section)
- [ ] `narrative_content.json` - Line ~253 (metadata)

**Documentation:**
- [ ] `README.txt` - Line ~3
- [ ] `README.md` - Lines ~5, ~8 (badge URL)
- [ ] `README_DEV.md` - Lines ~3, ~16 (badge URL)
- [ ] `.github/ISSUE_TEMPLATE/bug_report.md` - Line ~29
- [ ] `docs/wiki/Home.md` - Line ~9

**Quick command to find all version strings:**
```bash
grep -rn "0\.8\.0\|0\.9\.0" --include="*.py" --include="*.json" --include="*.md" --include="*.txt" | grep -v ".venv" | grep -v "node_modules"
```

### 1.2 Code Quality Checks

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run Unicode logging test: `pytest tests/test_no_unicode_in_logging.py -v`
- [ ] Check for debug prints: `grep -rn "print(" *.py | grep -v "# DEBUG" | grep -v test`
- [ ] Verify no TODO/FIXME blockers: `grep -rn "TODO\|FIXME" *.py`

### 1.3 Configuration Validation

- [ ] Verify game_content.json loads without errors
- [ ] Verify game_rules.json loads without errors
- [ ] Verify narrative_content.json loads without errors
- [ ] Run config validation test: `pytest tests/integration/test_config_validation.py -v`

---

## Phase 2: Build

### 2.1 Run Build Script

```bash
# For beta/alpha builds (DEBUG logging enabled by default):
build\build.bat alpha
# or
build\build.bat beta

# For stable releases (minimal logging):
build\build.bat release
```

**Build creates:**
- `dist/RogueSignalProtocol.exe` (~39MB)
- `releases/RogueSignalProtocol_[type]_YYYY-MM-DD.zip` (~195MB)

### 2.2 Verify Build Contents

Check the `dist/` folder contains:
- [ ] `RogueSignalProtocol.exe`
- [ ] `game_content.json`
- [ ] `game_rules.json`
- [ ] `narrative_content.json`
- [ ] `graphics_tiles.json`
- [ ] `default_bindings.json`
- [ ] `KreativeSquare.ttf`
- [ ] `README.txt`
- [ ] `LICENSE`
- [ ] `graphics/` folder (with all sprites and backgrounds)
- [ ] `sound/` folder (all .wav files)
- [ ] `music/` folder (all .ogg files)
- [ ] For beta/alpha: NO `release_mode.flag` (DEBUG logging on)
- [ ] For release: `release_mode.flag` present (minimal logging)

---

## Phase 3: Testing the Build

### 3.1 Basic Functionality (on clean system if possible)

- [ ] Game launches without Python installed
- [ ] Main menu renders correctly
- [ ] Settings menu works
- [ ] New game starts successfully
- [ ] Graphics mode toggle works (Settings > Graphics)

### 3.2 Core Gameplay

- [ ] Play through Level 1 (or part of it)
- [ ] Verify enemies spawn and move
- [ ] Verify exploits work (test 2-3 of them)
- [ ] Verify save/load works
- [ ] Verify permadeath deletes save on death

### 3.3 Audio

- [ ] Music plays on main menu
- [ ] Music changes per level
- [ ] Sound effects play (movement, attacks, exploits)
- [ ] Volume controls work

### 3.4 Debug Tools

- [ ] `Shift+F12` creates debug package
- [ ] Settings > Export Debug Package works
- [ ] Debug package includes logs and save

### 3.5 Edge Cases

- [ ] Help menu (`?`) displays correctly
- [ ] Inventory (`I`) works
- [ ] Fragments screen (`F`) works
- [ ] Achievements screen (`V`) works
- [ ] Look mode (`L`) works with mouse and keyboard

---

## Phase 4: Git & Version Control

### 4.1 Commit and Tag

```bash
# Stage all changes
git add -A

# Commit with version message
git commit -m "Release v0.9.0-beta"

# Create annotated tag
git tag -a v0.9.0-beta -m "Beta release 0.9.0"

# Push to remote
git push origin main
git push origin v0.9.0-beta
```

### 4.2 Create GitHub Release (optional)

- [ ] Go to GitHub > Releases > Draft new release
- [ ] Select the tag
- [ ] Upload the .zip from `releases/`
- [ ] Write release notes (use CHANGELOG.md if exists)

---

## Phase 5: Distribution

### 5.1 Itch.io Upload

- [ ] Upload .zip to itch.io project page
- [ ] Update page description if needed
- [ ] Set appropriate tags (roguelike, stealth, cyberpunk, turn-based)
- [ ] Mark build status (Alpha/Beta/Release)

### 5.2 Update Marketing Materials

- [ ] Take new screenshots if UI changed
- [ ] Update itch.io page draft in `marketing/itch_io_page_draft.md`
- [ ] Prepare Reddit post if doing announcement

---

## Phase 6: Post-Release

### 6.1 Monitor for Issues

- [ ] Check itch.io comments
- [ ] Monitor feedback form responses
- [ ] Watch for crash reports in logs

### 6.2 Document Known Issues

- [ ] Note any bugs found after release
- [ ] Add to next version's fix list

---

## Quick Reference: Files with Version Strings

| File | Locations |
|------|-----------|
| `game_menu_about.py` | 2 |
| `game_menu_main.py` | 1 |
| `game_save.py` | 1 |
| `game_story.py` | 1 |
| `game_rules.json` | 3 |
| `game_content.json` | 2 |
| `narrative_content.json` | 1 |
| `README.txt` | 1 |
| `README.md` | 2 |
| `README_DEV.md` | 2 |
| `bug_report.md` | 1 |
| `docs/wiki/Home.md` | 1 |

**Total: ~18 locations to update**

---

## Build Types Reference

| Type | Command | Logging | Flag File |
|------|---------|---------|-----------|
| Alpha | `build.bat alpha` | DEBUG (verbose) | none |
| Beta | `build.bat beta` | DEBUG (verbose) | none |
| Release | `build.bat release` | WARNING (minimal) | `release_mode.flag` |
