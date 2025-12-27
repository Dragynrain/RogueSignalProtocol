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

**Linux packaging files:**
- [ ] `packaging/linux/README.md` - Line ~5
- [ ] `packaging/linux/com.dragynrain.roguesignalprotocol.metainfo.xml` - Line ~83 (release version)
- [ ] `packaging/linux/PKGBUILD` - Line ~3 (pkgver)
- [ ] `packaging/linux/AppImageBuilder.yml` - version field
- [ ] `packaging/linux/com.dragynrain.roguesignalprotocol.yml` - source URL

**Quick command to find all version strings:**
```bash
# Replace OLD_VER and NEW_VER with actual versions (escape dots with \)
grep -rn "OLD_VER\|NEW_VER" --include="*.py" --include="*.json" --include="*.md" --include="*.txt" --include="*.xml" --include="*.yml" | grep -v ".venv" | grep -v "node_modules"

# Example: grep -rn "0\.9\.0\|0\.10\.0" --include="*.py" ...
```

### 1.2 Code Quality Checks

- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run Unicode logging test: `pytest tests/test_no_unicode_in_logging.py -v`
- [ ] Check for debug prints: `grep -rn "print(" game_*.py | grep -v "console.print"`
- [ ] Verify no TODO/FIXME blockers: `grep -rn "TODO\|FIXME" game_*.py`

### 1.3 Configuration Validation

- [ ] Verify game_content.json loads without errors
- [ ] Verify game_rules.json loads without errors
- [ ] Verify narrative_content.json loads without errors
- [ ] Run config validation test: `pytest tests/integration/test_config_validation.py -v`

---

## Phase 2: Windows Build

### 2.1 Run Windows Build Script

```bash
# For beta/alpha builds (DEBUG logging enabled by default):
build\build.bat beta
# or
build\build.bat alpha

# For stable releases (minimal logging):
build\build.bat release
```

**Build creates:**
- `dist/RogueSignalProtocol.exe` (~39MB)
- `releases/RogueSignalProtocol_[type]_YYYY-MM-DD.zip` (~195MB)

### 2.2 Verify Windows Build Contents

Check the `dist/` folder contains:
- [ ] `RogueSignalProtocol.exe`
- [ ] `game_content.json`
- [ ] `game_rules.json`
- [ ] `narrative_content.json`
- [ ] `graphics_tiles.json`
- [ ] `default_bindings.json`
- [ ] `KreativeSquare.ttf`
- [ ] `logo.png`
- [ ] `README.txt`
- [ ] `LICENSE`
- [ ] `graphics/` folder (with all sprites and backgrounds)
- [ ] `sound/` folder (all .wav files)
- [ ] `music/` folder (all .ogg files)
- [ ] For alpha/beta: `debug_mode.flag` present (DEBUG logging on)
- [ ] For release: NO `debug_mode.flag` (minimal logging)

---

## Phase 3: Linux Build

### 3.1 Build Linux Binary

Linux builds require a Linux environment (native, WSL2, VM, or GitHub Actions).

**Option A: GitHub Actions (Recommended)**
- Create a GitHub Release (not just a tag push) to trigger the workflow
- Go to GitHub > Releases > Draft new release > Create tag on publish
- Artifacts built and uploaded automatically

**Option B: Manual Build**
```bash
# On Linux system
source .venv/bin/activate
pip install pyinstaller
./build/build-linux.sh
```

### 3.2 Verify Linux Build Contents

Check `dist/` folder contains:
- [ ] `RogueSignalProtocol` (no .exe extension)
- [ ] All JSON config files
- [ ] `KreativeSquare.ttf`
- [ ] `logo.png`
- [ ] `graphics/`, `sound/`, `music/` folders
- [ ] `README.txt`, `LICENSE`

### 3.3 Build Linux Packages

**AppImage:**
```bash
./packaging/linux/build-appimage.sh [version]
```
- [ ] AppImage builds successfully
- [ ] Output: `RogueSignalProtocol-[version]-x86_64.AppImage`

**Flatpak (local test):**
```bash
flatpak-builder --user --install --force-clean build-dir packaging/linux/com.dragynrain.roguesignalprotocol.yml
```
- [ ] Flatpak builds successfully
- [ ] Can run: `flatpak run com.dragynrain.roguesignalprotocol`

**AUR (generate checksums):**
```bash
sha256sum RogueSignalProtocol-linux.tar.gz
```
- [ ] Update sha256sums in PKGBUILD

---

## Phase 4: Testing

### 4.1 Windows Testing

**Basic Functionality:**
- [ ] Game launches without Python installed
- [ ] Main menu renders correctly
- [ ] Settings menu works
- [ ] New game starts successfully
- [ ] Graphics mode toggle works

**Core Gameplay:**
- [ ] Play through Level 1 (or part of it)
- [ ] Verify enemies spawn and move
- [ ] Verify exploits work (test 2-3)
- [ ] Verify save/load works
- [ ] Verify permadeath deletes save

**Audio:**
- [ ] Music plays on main menu
- [ ] Music changes per level
- [ ] Sound effects play
- [ ] Volume controls work

**Debug Tools:**
- [ ] `Shift+F12` creates debug package
- [ ] Settings > Export Debug Package works

### 4.2 Linux Testing

> **Detailed checklist:** See `packaging/linux/TEST_CHECKLIST.md` for comprehensive Linux testing procedures.

**Binary Test (Ubuntu VM or WSL2):**
- [ ] Binary launches without errors
- [ ] Graphics render correctly
- [ ] Audio plays
- [ ] Keyboard/mouse work
- [ ] Save files created in `~/.local/share/RogueSignalProtocol/`

**Steam Deck Test (if available):**
- [ ] Game launches in Desktop Mode
- [ ] Gamepad controls work
- [ ] D-pad navigation works
- [ ] Add as non-Steam game works
- [ ] Suspend/resume works

**AppImage Test:**
- [ ] AppImage runs on clean system
- [ ] No missing library errors

### 4.3 Edge Cases (Both Platforms)

- [ ] Help menu (`?`) displays correctly
- [ ] Inventory (`I`) works
- [ ] Fragments screen (`F`) works
- [ ] Achievements screen (`V`) works
- [ ] Look mode (`L`) works with mouse and keyboard
- [ ] Gamepad controls work

---

## Phase 5: Git & Version Control

### 5.1 Commit and Tag

```bash
# Stage all changes
git add -A

# Commit with version message (replace X.Y.Z with actual version)
git commit -m "Release vX.Y.Z-beta"

# Create annotated tag
git tag -a vX.Y.Z-beta -m "Beta release X.Y.Z"

# Push to remote
git push origin main
git push origin vX.Y.Z-beta
```

**Note:** Replace `X.Y.Z` with actual version and `-beta` with release type (`-alpha`, `-beta`, or nothing for stable).

### 5.2 Create GitHub Release

- [ ] Go to GitHub > Releases > Draft new release
- [ ] Select the tag
- [ ] Upload Windows .zip from `releases/`
- [ ] Upload Linux tarball (`RogueSignalProtocol-linux.tar.gz`)
- [ ] Upload AppImage (`RogueSignalProtocol-*-x86_64.AppImage`)
- [ ] Write release notes

---

## Phase 6: Distribution

### 6.1 Windows Distribution

**Itch.io:**
- [ ] Upload Windows .zip to itch.io
- [ ] Update page description if needed
- [ ] Set appropriate tags
- [ ] Mark build status (Alpha/Beta/Release)

### 6.2 Linux Distribution

**GitHub Releases:**
- [ ] Linux tarball uploaded
- [ ] AppImage uploaded

**Itch.io:**
- [ ] Upload Linux tarball
- [ ] Upload AppImage
- [ ] Mark as Linux compatible

**Flathub (Beta channel):**
- [ ] Fork flathub/flathub repo
- [ ] Create branch: `com.dragynrain.roguesignalprotocol`
- [ ] Add manifest file
- [ ] Submit PR to beta branch
- [ ] Wait for review (1-7 days)

**AUR:**
- [ ] Update PKGBUILD with new version and checksums
- [ ] Generate .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
- [ ] Push to AUR

### 6.3 Update Marketing Materials

- [ ] Take new screenshots if UI changed
- [ ] Update itch.io page with Linux info
- [ ] Prepare Reddit post if doing announcement

---

## Phase 7: Post-Release

### 7.1 Monitor for Issues

- [ ] Check itch.io comments
- [ ] Monitor feedback form responses
- [ ] Watch for crash reports in logs
- [ ] Monitor GitHub issues for Linux-specific bugs

### 7.2 Document Known Issues

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
| `packaging/linux/README.md` | 1 |
| `packaging/linux/*.xml` | 1 |
| `packaging/linux/PKGBUILD` | 1 |

**Total: ~20+ locations to update**

---

## Build Types Reference

| Type | Command | Logging | Flag File | Behavior |
|------|---------|---------|-----------|----------|
| Alpha | `build.bat alpha` | DEBUG | `debug_mode.flag` | Verbose logging for development |
| Beta | `build.bat beta` | DEBUG | `debug_mode.flag` | Verbose logging for playtester bug reports |
| Release | `build.bat release` | WARNING | none | Minimal logging for end users |

**How it works:** The game checks for `debug_mode.flag` at startup. If present, DEBUG logging is enabled. Release builds omit this file for minimal logging by default.

---

## Linux Package Formats Reference

| Format | Distribution | Update Method |
|--------|--------------|---------------|
| AppImage | GitHub, itch.io | Manual download |
| Flatpak | Flathub | `flatpak update` |
| AUR | Arch User Repository | `yay -Syu` |
| Tarball | GitHub, itch.io | Manual download |

---

## Platform Testing Matrix

| Platform | Priority | Method |
|----------|----------|--------|
| Windows 10/11 | HIGH | Local testing |
| Ubuntu 22.04 | HIGH | VM or WSL2 |
| Steam Deck | HIGH | Real hardware |
| Fedora | LOW | VM (Wayland testing) |
| Arch Linux | LOW | Covered by Steam Deck |
