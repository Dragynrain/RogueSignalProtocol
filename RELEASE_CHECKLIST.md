# Release Checklist

Reusable checklist for alpha, beta, and stable releases.

---

## STOP - READ THIS FIRST

**DO NOT skip or skim this section. These rules exist because of actual release failures.**

### Rule 1: This is THE ONLY release checklist
- **USE THIS FILE:** `RELEASE_CHECKLIST.md` (project root)
- **DO NOT USE:** `marketing/pre_release_checklist.md` (OBSOLETE - kept for historical reference only)
- If you find yourself in a different checklist file, STOP and come back here.

### Rule 2: Follow phases IN ORDER
- Complete Phase 1 before Phase 2, Phase 2 before Phase 3, etc.
- Do not skip ahead to "save time" - it creates more work fixing mistakes.
- Each phase depends on the previous phase being complete.

### Rule 3: Read referenced files BEFORE acting
- Phase 3 references `.github/workflows/release.yml` - READ IT before creating a release
- Phase 4.10 references `packaging/linux/TEST_CHECKLIST.md` - READ IT before testing
- If a step says "see [file]", open and read that file first.

### Rule 4: Test environments are documented
- **Windows:** Local machine
- **Linux Mint:** Dedicated test machine (see `packaging/linux/TEST_CHECKLIST.md`)
- **Steam Deck:** Real hardware if available
- Do not guess or ask about test environments - they are documented.

### Rule 5: GitHub Release triggers Linux builds
- Pushing a git tag does NOT build Linux packages
- Creating a GitHub Release DOES trigger `.github/workflows/release.yml`
- Use `gh release create` (GitHub CLI), not just `git push origin [tag]`
- The workflow needs `permissions: contents: write` to upload assets

### Rule 6: Create a progress tracking file for each release
- Copy this checklist to `RELEASE_X.Y.Z_PROGRESS.md`
- Check off items as you complete them
- Add session notes and timestamps
- Delete the progress file after release is complete

---

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
- [ ] `CHANGELOG.md` - Add new version section with all changes

**Linux packaging files:**
- [ ] `packaging/linux/README.md` - Line ~5
- [ ] `packaging/linux/info.aforster.roguesignalprotocol.metainfo.xml` - Line ~83 (release version)
- [ ] `packaging/linux/PKGBUILD` - Line ~3 (pkgver)
- [ ] `packaging/linux/AppImageBuilder.yml` - version field
- [ ] `packaging/linux/info.aforster.roguesignalprotocol.yml` - source URL

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

### 1.4 URL Verification

- [ ] Verify all URLs are correct: `grep -rn "discord.gg\|itch.io\|forms.gle" --include="*.py" --include="*.md" --include="*.txt" --include="*.html"`
- [ ] Test feedback form URL is accessible
- [ ] Test itch.io page URL is correct

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

### 2.3 Create Backup

- [ ] Copy entire `dist/` folder to `dist_backup_vX.Y.Z/` before testing

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
flatpak-builder --user --install --force-clean build-dir packaging/linux/info.aforster.roguesignalprotocol.yml
```
- [ ] Flatpak builds successfully
- [ ] Can run: `flatpak run info.aforster.roguesignalprotocol`

**AUR (generate checksums):**
```bash
sha256sum RogueSignalProtocol-linux.tar.gz
```
- [ ] Update sha256sums in PKGBUILD

---

## Phase 4: Testing

### 4.1 Windows Basic Functionality

- [ ] Game launches without Python installed (clean Windows 10/11)
- [ ] Main menu renders correctly
- [ ] Settings menu works
- [ ] New game starts successfully
- [ ] Graphics mode toggle works
- [ ] All config files load correctly

### 4.2 Core Gameplay (Full Playthrough)

- [ ] Play through all 3 levels (complete run)
- [ ] Verify enemies spawn and move correctly
- [ ] Verify ALL 13 exploits work correctly
- [ ] Verify save/load works
- [ ] Verify permadeath deletes save completely
- [ ] Test Admin Avatar spawns when trace hits 100%

### 4.3 Audio Verification

- [ ] Music plays on main menu
- [ ] Music changes per level
- [ ] Test ALL 13 exploit sounds play correctly
- [ ] Logic Bomb sound (logic_bomb.wav) plays
- [ ] Volume controls work

### 4.4 Gamepad Testing

**Controller connection:**
- [ ] Xbox controller connects and is recognized
- [ ] PlayStation controller connects (if available)
- [ ] Hotplug works (connect/disconnect during gameplay)

**Gameplay controls:**
- [ ] Left stick/D-pad movement works with proper time-gating
- [ ] Right stick auto-look mode works
- [ ] LB/RB cycle through exploits
- [ ] RT fires selected exploit
- [ ] A=wait, B=cancel, Y=inventory, Start=menu, Select=help

**Menu navigation:**
- [ ] D-pad/stick navigates menus
- [ ] A=confirm, B=back works consistently
- [ ] LB/RB page through achievements/help

**Control remapping:**
- [ ] Settings > Controls > Gamepad Bindings accessible
- [ ] Can rebind gamepad buttons
- [ ] Bindings persist after restart

### 4.5 Ascension System Testing

- [ ] Complete a run to unlock Ascension
- [ ] Press N to open Ascension viewer
- [ ] Verify unlock popup appears on first unlock
- [ ] Test A1 modifier (Scanner Vision +1)
- [ ] Verify Ascension level persists across runs
- [ ] Check Ascension achievements unlock at A5/A10/A15/A20

### 4.6 Achievement System

- [ ] Unlock an achievement and verify it persists
- [ ] Check achievement popups display correctly
- [ ] Verify progress tracking works across deaths

### 4.7 Debug Tools

- [ ] `Shift+F12` creates debug package
- [ ] Settings > Export Debug Package works
- [ ] Verify package includes saves/logs/metrics from data directory
- [ ] Package created in [data directory]/debug_exports/

### 4.8 New Player Experience

- [ ] Delete `user_settings.json` and test fresh start
- [ ] Verify intro dialogue appears
- [ ] Check help menu (?) is comprehensive - verify all pages including gamepad
- [ ] Ensure first death shows feedback link clearly

### 4.9 UI/UX Testing (Both Platforms)

- [ ] Help menu (`?`) displays correctly
- [ ] Inventory (`I`) works
- [ ] Fragments screen (`F`) displays all discovered lore
- [ ] Achievements screen (`V`) works
- [ ] Ascension screen (`N`) works
- [ ] Look mode (`L`) works with mouse and keyboard
- [ ] Keybindings match help text exactly

### 4.10 Linux Testing

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
- [ ] Write release notes from CHANGELOG.md

---

## Phase 6: Marketing & Screenshots

### 6.1 Update Screenshots

- [ ] Verify screenshots show pixel explosion effect (graphics mode)
- [ ] Verify screenshots show queue arrows (directional arrow system)
- [ ] Verify images show both ASCII and graphics modes
- [ ] Ensure one screenshot shows enemy movement queue UI clearly
- [ ] Consider additional shots: gameplay, inventory, lore/fragments, death screen

**Recommended screenshots (5 minimum):**
1. Main menu
2. Stealth gameplay (hiding in shadows)
3. Combat encounter / exploit usage
4. Lore/Fragments screen
5. Inventory screen

### 6.2 Record Video (Optional but Recommended)

- [ ] Record MP4 video showcasing gameplay (10-15 seconds)
- [ ] Show key features: movement queue arrows, pixel explosions, stealth mechanics
- [ ] Keep file size reasonable for Reddit upload (<100 MB)
- [ ] Consider showing: player hiding in blind spot -> enemy moves past -> player escapes

### 6.3 Update Marketing Materials

- [ ] Update itch.io page content from `marketing/itch_io_page.html`
- [ ] Prepare devlog/announcement post if applicable
- [ ] Take new screenshots if UI changed

---

## Phase 7: Distribution

### 7.1 Windows Distribution

**Itch.io:**
- [ ] Upload Windows .zip to itch.io
- [ ] Update page description if needed
- [ ] Set appropriate tags: roguelike, stealth, cyberpunk, turn-based, permadeath, controller-support
- [ ] Mark build status (Alpha/Beta/Release)

### 7.2 Linux Distribution

**GitHub Releases:**
- [ ] Linux tarball uploaded
- [ ] AppImage uploaded

**Itch.io:**
- [ ] Upload Linux tarball
- [ ] Upload AppImage
- [ ] Mark as Linux compatible

**Flathub (STABLE RELEASES ONLY):**

> **WARNING 1:** Flathub does NOT accept alpha/beta releases. Wait for stable 1.0+.
> **WARNING 2:** Flathub explicitly BANS AI-generated submissions. YOU must submit manually.
> Claude can prepare files but CANNOT submit the PR.

Prerequisites (do these FIRST):
- [ ] Update `packaging/linux/info.aforster.roguesignalprotocol.yml` with new SHA256
- [ ] Test Flatpak locally on Linux: `flatpak-builder --user --install --force-clean build-dir packaging/linux/info.aforster.roguesignalprotocol.yml`
- [ ] Verify it runs: `flatpak run info.aforster.roguesignalprotocol`
- [ ] **Record a video** of the app running via Flatpak (REQUIRED by Flathub)

Submission (do manually via GitHub web UI):
- [ ] Fork flathub/flathub repo (uncheck "copy master branch only")
- [ ] Clone with `new-pr` branch: `git clone -b new-pr ...`
- [ ] Create branch: `info.aforster.roguesignalprotocol`
- [ ] Add manifest file, commit, push
- [ ] Create PR via GitHub web UI (NOT CLI) - this auto-populates the template
- [ ] PR title MUST be exactly: `Add info.aforster.roguesignalprotocol`
- [ ] Fill in ALL checkboxes in the template
- [ ] Upload the video
- [ ] Declare you are the author/developer
- [ ] Wait for review (1-7 days)

Post-acceptance (for Verified badge):
- [ ] Log into Flathub Developer Portal
- [ ] Get verification token for `info.aforster.roguesignalprotocol`
- [ ] Create `https://aforster.info/.well-known/org.flathub.VerifiedApps.txt` with token
- [ ] Verify badge appears on Flathub listing

**AUR:**

> **TIP:** Use Docker to generate .SRCINFO if not on Arch:
> `docker run --rm -v "$(pwd):/pkg" -w /pkg archlinux bash -c "pacman -Sy --noconfirm base-devel && useradd builder && su builder -c 'makepkg --printsrcinfo' > .SRCINFO"`

- [ ] Update PKGBUILD with new version and SHA256
- [ ] Convert to Unix line endings: `sed -i 's/\r$//' PKGBUILD`
- [ ] Generate .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
- [ ] Push to AUR: `git clone ssh://aur@aur.archlinux.org/rogue-signal-protocol-bin.git`
- [ ] Verify at: https://aur.archlinux.org/packages/rogue-signal-protocol-bin

### 7.3 Verify Feedback Collection

- [ ] Feedback form URL works in README.txt
- [ ] Feedback form URL works in README.md
- [ ] Feedback form URL visible on itch.io page
- [ ] Feedback form URL in Reddit post draft

### 7.4 Update Wiki

**Auto-generated pages (if game_content.json changed):**
```bash
python docs/generate_wiki.py
```
- [ ] Run wiki generator if enemy/exploit/network data changed
- [ ] Review generated pages for accuracy

**Manual wiki pages to review:**
- [ ] `docs/wiki/Home.md` - Version number (already in Phase 1)
- [ ] `docs/wiki/Keybindings.md` - If controls changed
- [ ] `docs/wiki/Gameplay-Mechanics.md` - If mechanics changed
- [ ] `docs/wiki/UI-and-HUD-Guide.md` - If UI changed
- [ ] `docs/wiki/Settings-and-Configuration.md` - If settings changed

**Sync to GitHub Wiki:**
```bash
cd ..
git clone https://github.com/Dragynrain/RogueSignalProtocol.wiki.git
cp -r RogueSignalProtocol/docs/wiki/*.md RogueSignalProtocol.wiki/
cd RogueSignalProtocol.wiki
git add . && git commit -m "Update wiki for vX.Y.Z" && git push
```
- [ ] Clone wiki repo (first time) or pull latest
- [ ] Copy updated wiki pages
- [ ] Commit and push to wiki

---

## Phase 8: Launch & Promotion

### 8.1 Reddit Posting Strategy

**Option A: r/roguelikedev (friendlier, good for first post)**
- Use `marketing/reddit_post_draft.md`
- Post on weekday morning (9-11 AM EST)
- Respond to comments within first 2 hours

**Option B: r/roguelikes "Sharing Saturday"**
- Every Saturday
- More exposure but more competitive
- Include 2-3 screenshots

**Option C: r/DestroyMyGame (brutal feedback)**
- Use `marketing/reddit_destroymygame_draft.md`
- Specifically for crash reports and balance complaints
- Expect harsh but honest criticism
- Good for beta testing phase

### 8.2 Announcement Posts

**Reddit:**
- [ ] Post to chosen subreddit(s)
- [ ] Include screenshots/video
- [ ] Monitor and respond to comments

**RogueTemple Forums:**
- [ ] Post announcement thread: https://forums.roguetemple.com/
- [ ] Update existing thread if continuing development

**RogueBasin Wiki:**
- [ ] Create/update game page: http://roguebasin.com/
- [ ] Add to appropriate categories (7DRL if applicable, etc.)

---

## Phase 9: Post-Release

### 9.1 Monitor for Issues (First 24 Hours)

- [ ] Check itch.io comments
- [ ] Monitor feedback form responses
- [ ] Respond to Reddit questions
- [ ] Watch for crash reports in logs
- [ ] Monitor GitHub issues for Linux-specific bugs

### 9.2 First Week Follow-up

- [ ] Collect survey responses
- [ ] Prioritize bug fixes
- [ ] Plan balance tweaks based on feedback
- [ ] Consider posting to additional subreddits if initial reception is good

### 9.3 Document Known Issues

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
| `CHANGELOG.md` | 1 |

**Total: ~21 locations to update**

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

---

## Known Issues to Document on Itch.io

**Beta limitations to mention:**
- Windows and Linux only (no macOS yet)
- Ascension system provides difficulty scaling (no easy mode)
- Graphics mode optional (ASCII is primary)
- No tutorial scenario (help menu is comprehensive)
- Steam Deck support is experimental
