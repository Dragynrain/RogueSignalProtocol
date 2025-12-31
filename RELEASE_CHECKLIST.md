# Release Checklist

Reusable checklist for alpha, beta, and stable releases.

**Minor releases (X.Y.Z -> X.Y.Z+1):** Skip Phase 6.2 (video), reduce Phase 8 marketing scope. Save migration testing (1.7) is especially important.

---

## Step 0: Create Your Version-Specific Checklist

**Before doing ANYTHING else:**

1. Copy this file: `RELEASE_CHECKLIST.md`
2. Name the copy with your version: `RELEASE_CHECKLIST_X.Y.Z.md` (e.g., `RELEASE_CHECKLIST_0.9.1.md`)
3. Work from that copy, checking off items as you complete them
4. Keep the copy until the release is fully deployed and verified
5. Delete the version-specific copy after the release is complete (the master checklist stays)

This ensures you have a permanent record of progress for each release and prevents confusion about what's been done.

---

## STOP - READ THIS FIRST

**DO NOT skip or skim this section. These rules exist because of actual release failures.**

### Rule 0: Check off items AS YOU COMPLETE THEM
- Mark each `[ ]` as `[x]` immediately after completing it
- Do NOT batch checkmarks at the end
- If you skip an item, mark it with `[-]` and note why
- This prevents missed steps and provides audit trail

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

---

## Minor Release Fast Path (Skip Testing)

**Use this when:** Testing completed via uncompiled code, no major changes.

**Pre-flight checks (run these FIRST):**
```bash
# Verify clean working tree
git status
# Expected: nothing to commit, working tree clean (or only untracked .coverage files)

# Verify gh is authenticated
gh auth status
# Expected: shows "Logged in to github.com"

# Verify butler is authenticated (if pushing to itch.io)
build\butler\butler.exe status dragynrain/rogue-signal-protocol
# Expected: shows channel list (not "butler login required")

# Get current version
grep '"version"' game_rules.json
# Note the OLD version for bump command
```

**Release steps (replace OLD/NEW with actual versions, e.g., 0.9.1/0.9.2):**
```bash
# 1. Bump version (OLD -> NEW)
python build/bump-version.py OLD NEW beta
python build/bump-version.py --check NEW beta  # VERIFY

# 2. Update CHANGELOG.md manually
# Add section header: ## [NEW Beta] - YYYY-MM-DD - Brief Title
# Document all changes since last release

# 3. Build Windows
build\build.bat beta NEW
dir releases\*NEW*.zip  # VERIFY: zip exists

# 4. Commit, tag, push
git add -A && git commit -m "Release vNEW-beta"
git tag -a vNEW-beta -m "Beta release NEW"
git push origin main && git push origin vNEW-beta
git ls-remote --tags origin | grep "NEW"  # VERIFY: tag on remote

# 5. Create GitHub release (triggers Linux build workflow)
# Extract latest changelog section for release notes
sed -n '/^## \[NEW/,/^## \[/p' CHANGELOG.md | head -n -1 > release_notes.tmp
gh release create vNEW-beta --title "vNEW-beta" --notes-file release_notes.tmp --prerelease "releases/RogueSignalProtocol_beta_NEW.zip"
rm release_notes.tmp
gh release view vNEW-beta  # VERIFY: release exists

# 6. Wait for workflow (~5-10 min)
gh run list --workflow=release.yml -L 1  # Poll until "completed"
gh release view vNEW-beta --json assets -q '.assets[].name'  # VERIFY: tarball + AppImage

# 7. Push to itch.io (skip if ENABLE_ITCH_PUSH=true in GitHub repo vars - workflow does it)
build\push-all.bat NEW beta
build\butler\butler.exe status dragynrain/rogue-signal-protocol  # VERIFY: all channels show NEW

# 8. Update AUR (optional)
build\update-aur.bat NEW beta
cd /d/Projects/aur-rogue-signal-protocol-bin
git add -A && git commit -m "Update to NEW-beta" && git push origin master
```

**STOP at any step if verification fails. Investigate before proceeding.**

**Known gotchas from past releases:**
1. **Workflow uses tag's code, not latest main** - If the workflow fails and you push a fix to main, you must delete and recreate the tag at the new commit. The workflow clones from the tag, not HEAD.
2. **AUR API cache delay** - After pushing to AUR, the version in the API may take a few minutes to update. The git push succeeding is what matters.

**Rollback procedures (if something fails mid-release):**
```bash
# If commit/tag pushed but release creation failed:
git tag -d vNEW-beta                    # Delete local tag
git push origin :refs/tags/vNEW-beta    # Delete remote tag
git reset --soft HEAD~1                 # Undo commit (keeps changes staged)

# If release created but workflow failed:
gh release delete vNEW-beta --yes       # Delete the release
# Then fix issue and re-run from step 5

# If itch.io push failed after GitHub release succeeded:
# Just re-run push-all.bat - it's idempotent
```

---

## Phase 1: Pre-Build Preparation

### 1.1 Version String Updates

**Source of truth:** `game_rules.json` line 2 - all Python code reads from `rsp.core.version` which loads this.

**Automated by `bump-version.py`:**
- `game_rules.json` - version field (source of truth)
- `README.txt`, `README.md`, `README_DEV.md` - version strings and badge URLs
- `docs/wiki/Home.md` - current version display
- `packaging/linux/PKGBUILD` - pkgver and _vertag
- `packaging/linux/AppImageBuilder.yml` - version field
- `packaging/linux/info.aforster.roguesignalprotocol.yml` - source URL
- `packaging/linux/info.aforster.roguesignalprotocol.metainfo.xml` - adds new release entry

**Requires manual update:**
- [ ] `CHANGELOG.md` - Add new version section with all changes (content, not version string)
- [ ] `packaging/linux/info.aforster.roguesignalprotocol.metainfo.xml` - release description text (auto-added entry has placeholder)

**NOT needed (centralized via rsp.core.version):**
- ~~rsp.ui.menu_about~~ - imports VERSION_DISPLAY
- ~~rsp.ui.menu_main~~ - imports VERSION_DISPLAY
- ~~rsp.systems.save~~ - imports VERSION
- ~~rsp.utils.story~~ - imports VERSION
- ~~game_content.json~~ - no version field
- ~~narrative_content.json~~ - no version field

**Automated version bump (recommended):**
```bash
python build/bump-version.py OLD_VER NEW_VER beta
# Example: python build/bump-version.py 0.9.1 0.9.2 beta
```

**Verification (STOP if fails):**
```bash
# Verify version was updated correctly
python build/bump-version.py --check NEW_VER beta
# Expected: "All files consistent with version X.Y.Z beta"

# Double-check source of truth
grep '"version"' game_rules.json
# Expected: "version": "X.Y.Z Beta"
```

**Manual files still requiring update:**
- [ ] `CHANGELOG.md` - Add new version section with changes (script cannot write changelog content)

**Quick command to find all version strings:**
```bash
# Replace OLD_VER and NEW_VER with actual versions (escape dots with \)
grep -rn "OLD_VER\|NEW_VER" --include="*.py" --include="*.json" --include="*.md" --include="*.txt" --include="*.xml" --include="*.yml" | grep -v ".venv" | grep -v "node_modules"

# Example: grep -rn "0\.9\.0\|0\.10\.0" --include="*.py" ...
```

### 1.2 Code Quality Checks

**Automated validation (recommended - runs all checks):**
```bash
python build/validate-release.py
```

**Verification (STOP if fails):**
```bash
# Expected output ends with:
# "All checks passed - ready to build!"
# Exit code 0

# If any check fails, fix the issue before proceeding
```

**Individual checks (if needed):**
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

### 1.5 About/Credits Verification

- [ ] Check About screen (`src/rsp/ui/menu_about.py`) credits are current
- [ ] Verify copyright year is current
- [ ] Check any third-party attribution is up to date

### 1.6 CHANGELOG Review

- [ ] Verify CHANGELOG.md has ALL changes since last release documented
- [ ] Check that change descriptions are clear and user-facing (not internal refactors)
- [ ] Ensure new version section header is ready to be filled in

### 1.7 Save Migration Test

- [ ] Locate a save file from the previous release version
- [ ] Load the old save with the new code (before building)
- [ ] Verify gameplay continues correctly with no errors
- [ ] If save format changed, document migration path or breaking change

### 1.8 Dependency Security Audit

- [ ] Run `pip audit` (install with `pip install pip-audit` if needed)
- [ ] Review any reported vulnerabilities
- [ ] Update vulnerable packages or document accepted risks

### 1.9 Clean Build Preparation

- [ ] Delete `dist/` folder to ensure no stale files
- [ ] Delete `build/` folder (PyInstaller build artifacts)
- [ ] Verify `releases/` folder exists for output

---

## Phase 2: Windows Build

### 2.1 Run Windows Build Script

```bash
# For beta/alpha builds (DEBUG logging enabled by default):
build\build.bat beta X.Y.Z
# or
build\build.bat alpha X.Y.Z

# For stable releases (minimal logging):
build\build.bat release X.Y.Z
```

**Verification (STOP if fails):**
```bash
# Verify exe was created
dir dist\RogueSignalProtocol.exe
# Expected: file exists, ~39MB

# Verify release archive was created
dir releases\*X.Y.Z*.zip
# Expected: RogueSignalProtocol_beta_X.Y.Z.zip exists, ~195MB

# Verify checksum file was generated
dir releases\*X.Y.Z*.sha256
# Expected: checksum file exists
```

**Build creates:**
- `dist/RogueSignalProtocol.exe` (~39MB)
- `releases/RogueSignalProtocol_[type]_X.Y.Z.zip` (~195MB)
- `releases/RogueSignalProtocol_[type]_X.Y.Z.zip.sha256`

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

> **CRITICAL:** AppImage mounts as read-only. Any code using relative paths for saves/logs/metrics will FAIL.
> All file operations MUST use `get_data_directory()` from `rsp.core.file_paths`.
> The test `test_build_verification.py::TestNoRelativeDataPaths` catches this - run it before release.

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

### 4.9 Mouse Testing

- [ ] Click to move works correctly
- [ ] Click on enemies shows look info
- [ ] Menu buttons respond to mouse clicks
- [ ] Mouse wheel scrolls where applicable (help, achievements)
- [ ] Tooltips appear on hover (if implemented)

### 4.10 Antivirus False Positive Check

- [ ] Upload `RogueSignalProtocol.exe` to VirusTotal (https://www.virustotal.com/)
- [ ] Document detection ratio (PyInstaller builds commonly trigger 2-5 false positives)
- [ ] If detections > 10, investigate or consider signing the executable
- [ ] Note: Expected false positives from heuristic scanners (e.g., "Gen:Variant.Tedy") are normal

### 4.11 Clean Uninstall/Reinstall Test

- [ ] Delete entire data directory (`%APPDATA%/RogueSignalProtocol` on Windows, `~/.local/share/RogueSignalProtocol` on Linux)
- [ ] Delete any leftover install files
- [ ] Fresh install from the release zip/package
- [ ] Verify game launches and creates new data directory correctly

### 4.12 Memory/Performance Smoke Test

- [ ] Play for 15+ minutes continuously
- [ ] Monitor memory usage (Task Manager or similar)
- [ ] Verify no significant memory growth over time
- [ ] Check for any performance degradation in later levels

### 4.13 Window/Display Testing

- [ ] Fullscreen toggle (Alt+Enter or F11) works
- [ ] Window resize maintains aspect ratio
- [ ] Game recovers from minimize/restore
- [ ] Multi-monitor: game opens on correct display

### 4.14 UI/UX Testing (Both Platforms)

- [ ] Help menu (`?`) displays correctly
- [ ] Inventory (`I`) works
- [ ] Fragments screen (`F`) displays all discovered lore
- [ ] Achievements screen (`V`) works
- [ ] Ascension screen (`N`) works
- [ ] Look mode (`L`) works with mouse and keyboard
- [ ] Keybindings match help text exactly

### 4.15 Linux Testing

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

### 5.1 Backup Previous Release

- [ ] Note current version tag for rollback if needed: `git describe --tags --abbrev=0`
- [ ] Ensure previous release is still available on GitHub/itch.io

### 5.2 Draft Release Notes

- [ ] Write GitHub release description BEFORE creating the release
- [ ] Include: summary of changes, highlights, known issues, upgrade notes
- [ ] Copy key points from CHANGELOG.md
- [ ] Have the text ready to paste when creating the GitHub release

### 5.3 Commit and Tag

- [ ] Stage all changes: `git add -A`
- [ ] Commit with version message: `git commit -m "Release vX.Y.Z-beta"`
- [ ] Create annotated tag: `git tag -a vX.Y.Z-beta -m "Beta release X.Y.Z"`
- [ ] Push commits: `git push origin main`
- [ ] Push tag: `git push origin vX.Y.Z-beta`

**Verification (STOP if any fail):**
```bash
# Verify commit exists
git log -1 --oneline
# Expected: shows "Release vX.Y.Z-beta" message

# Verify tag exists locally
git tag -l "vX.Y.Z*"
# Expected: shows vX.Y.Z-beta

# Verify push succeeded
git status
# Expected: "Your branch is up to date with 'origin/main'"

# Verify tag on remote
git ls-remote --tags origin | grep "vX.Y.Z"
# Expected: shows the tag ref
```

**Note:** Replace `X.Y.Z` with actual version and `-beta` with release type (`-alpha`, `-beta`, or nothing for stable).

### 5.4 Create GitHub Release

**IMPORTANT: Match existing naming conventions!**
- Check previous releases for title/description format
- Check existing tags: `git tag -l` (e.g., `v0.9.0-beta`, `v0.8.0-alpha`)
- Keep consistency with itch.io channel names and version labels

**Option A: GitHub CLI (recommended for automation)**
```bash
# Extract just the latest version's changelog section
sed -n '/^## \[X.Y.Z/,/^## \[/p' CHANGELOG.md | head -n -1 > release_notes.tmp

# Create release with extracted notes
gh release create vX.Y.Z-beta \
  --title "vX.Y.Z-beta" \
  --notes-file release_notes.tmp \
  --prerelease \
  "releases/RogueSignalProtocol_beta_X.Y.Z.zip"

rm release_notes.tmp

# Alternative: simple inline notes (less informative)
gh release create vX.Y.Z-beta \
  --title "vX.Y.Z-beta" \
  --notes "See CHANGELOG.md for full details" \
  --prerelease \
  "releases/RogueSignalProtocol_beta_X.Y.Z.zip"
```

**Option B: GitHub Web UI**
- [ ] Go to GitHub > Releases > Draft new release
- [ ] Select the tag
- [ ] Title format: `v1.0.0` or `v1.0.0-beta` (match tag and previous releases)
- [ ] Upload Windows .zip from `releases/`
- [ ] Write release notes from CHANGELOG.md
- [ ] For pre-releases: check "Set as a pre-release" checkbox

**Verification (STOP if fails):**
```bash
# Verify release was created
gh release view vX.Y.Z-beta
# Expected: shows release title, tag, and attached Windows zip

# Verify workflow was triggered
gh run list --workflow=release.yml -L 1
# Expected: shows "in_progress" or "queued" status
```

### 5.5 Wait for GitHub Actions Workflow

The release workflow builds Linux packages automatically. This takes ~5-10 minutes.

> **Note:** The workflow runs the full test suite with `--no-cov` (coverage already enforced by pre-commit hook locally). This catches Linux-specific issues that can't be caught on Windows.

**Monitor workflow:**
```bash
# Watch workflow status (poll every 30 seconds)
gh run list --workflow=release.yml -L 1

# Or watch a specific run
gh run watch <run-id>
```

**Verification (STOP if fails):**
```bash
# Verify workflow completed successfully
gh run list --workflow=release.yml -L 1 --json status,conclusion -q '.[0]'
# Expected: {"status":"completed","conclusion":"success"}

# Verify Linux artifacts were uploaded to release
gh release view vX.Y.Z-beta --json assets -q '.assets[].name'
# Expected: shows tarball AND AppImage filenames

# If workflow failed, check logs:
gh run view <run-id> --log-failed
```

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

### 7.1 Itch.io Distribution (Butler)

Butler provides incremental updates for itch.io desktop app users. Use consistent channel names so users get automatic updates.

**GitHub Actions auto-push (if enabled):**
The release workflow has a `push-itch` job that automatically pushes all builds to itch.io.
- Requires: `BUTLER_API_KEY` secret set in GitHub repo
- Requires: `ENABLE_ITCH_PUSH` repository variable set to `true`
- If enabled, skip manual push steps below - just verify with `butler status`

**Channels:**
| Channel | Platform | File |
|---------|----------|------|
| `windows` | Windows | Local build zip |
| `linux` | Linux | Tarball from GitHub release |
| `linux-appimage` | Linux | AppImage from GitHub release |

**Windows upload:**
```bash
# Push local build (butler renames to RogueSignalProtocol-windows.zip)
build\butler\butler.exe push releases/RogueSignalProtocol_beta_X.Y.Z.zip dragynrain/rogue-signal-protocol:windows --userversion X.Y.Z
```

**Linux uploads (download from GitHub release first):**
```bash
# Download Linux builds from GitHub release
gh release download vX.Y.Z-beta --pattern "RogueSignalProtocol-*-Linux*" --dir releases/

# Push tarball (preserves filename)
build\butler\butler.exe push releases/RogueSignalProtocol-X.Y.Z-beta-Linux.tar.gz dragynrain/rogue-signal-protocol:linux --userversion X.Y.Z

# Push AppImage (preserves filename)
build\butler\butler.exe push releases/RogueSignalProtocol-X.Y.Z-beta-x86_64.AppImage dragynrain/rogue-signal-protocol:linux-appimage --userversion X.Y.Z
```

**Automated option (recommended):**
```bash
build\push-all.bat X.Y.Z
# Downloads Linux builds from GitHub if not local, pushes all 3 channels
```

**Checklist:**
- [ ] Push Windows build to `windows` channel
- [ ] Download Linux builds from GitHub release
- [ ] Push tarball to `linux` channel
- [ ] Push AppImage to `linux-appimage` channel

**Verification (STOP if any fail):**
```bash
# Verify all channels have correct version
build\butler\butler.exe status dragynrain/rogue-signal-protocol
# Expected output should show:
#   windows: X.Y.Z
#   linux: X.Y.Z
#   linux-appimage: X.Y.Z

# Verify page is accessible
curl -s -o /dev/null -w "%{http_code}" https://dragynrain.itch.io/rogue-signal-protocol
# Expected: 200
```

- [ ] Verify at https://dragynrain.itch.io/rogue-signal-protocol/edit
- [ ] Ensure Linux channels are tagged with Linux platform

### 7.2 GitHub Releases (Automatic)

The release workflow automatically builds and uploads to GitHub when a release is published.

**Naming convention:**
- Windows: `RogueSignalProtocol-Windows.zip`
- Tarball: `RogueSignalProtocol-X.Y.Z-beta-Linux.tar.gz`
- AppImage: `RogueSignalProtocol-X.Y.Z-beta-x86_64.AppImage`

- [ ] Linux tarball uploaded to GitHub release
- [ ] AppImage uploaded to GitHub release
- [ ] Windows zip uploaded to GitHub release

**Flathub (STABLE RELEASES ONLY):**

> **WARNING 1:** Flathub does NOT accept alpha/beta releases. Wait for stable 1.0+.
> **WARNING 2:** Flathub explicitly BANS AI-generated submissions. YOU must submit manually.
> Claude can prepare files but CANNOT submit the PR.

Domain verification (do BEFORE submitting):
- [ ] Verify `https://aforster.info` loads over HTTPS
- [ ] Verify page mentions Rogue Signal Protocol (visible proof of ownership)

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

SSH access is configured via `~/.ssh/config` using the `id_ed25519_aur` key linked to the `dragynrain` AUR account.

**Step 1: Update local files** (in main repo)
```bash
# Update packaging/linux/PKGBUILD:
#   - pkgver=X.Y.Z_beta (underscore, not hyphen)
#   - _vertag=X.Y.Z-beta (hyphen for GitHub tag)
#   - sha256sums from: sha256sum releases/RogueSignalProtocol-X.Y.Z-beta-Linux.tar.gz

# Convert to Unix line endings
sed -i 's/\r$//' packaging/linux/PKGBUILD packaging/linux/*.install

# Generate .SRCINFO using Docker (Windows)
docker run --rm -v "D:/Projects/RogueSignalProtocol/packaging/linux://pkg" -w //pkg archlinux \
  bash -c "pacman -Sy --noconfirm base-devel >/dev/null 2>&1 && useradd builder && \
  su builder -c 'makepkg --printsrcinfo'" > packaging/linux/.SRCINFO
```

**Step 2: Push to AUR**
```bash
# Clone AUR repo (or pull if already cloned)
git clone ssh://aur@aur.archlinux.org/rogue-signal-protocol-bin.git /d/Projects/aur-rogue-signal-protocol-bin

# Copy files
cp packaging/linux/PKGBUILD /d/Projects/aur-rogue-signal-protocol-bin/
cp packaging/linux/.SRCINFO /d/Projects/aur-rogue-signal-protocol-bin/
cp packaging/linux/rogue-signal-protocol-bin.install /d/Projects/aur-rogue-signal-protocol-bin/

# Commit and push
cd /d/Projects/aur-rogue-signal-protocol-bin
git add PKGBUILD .SRCINFO rogue-signal-protocol-bin.install
git commit -m "Update to X.Y.Z-beta"
git push origin master
```

**Automated option (recommended):**
```bash
build\update-aur.bat X.Y.Z beta
# Updates PKGBUILD, generates .SRCINFO via Docker, copies to AUR repo
```

- [ ] Update PKGBUILD with new version and SHA256
- [ ] Generate .SRCINFO
- [ ] Push to AUR

**Verification (STOP if fails):**
```bash
# Verify PKGBUILD has correct version
grep "pkgver=" packaging/linux/PKGBUILD
# Expected: pkgver=X.Y.Z_beta

# Verify SHA256 is set (not placeholder)
grep "sha256sums=" packaging/linux/PKGBUILD
# Expected: sha256sums=('<64-char-hash>')

# After pushing to AUR, verify update (may take a few minutes to propagate)
curl -s "https://aur.archlinux.org/rpc/v5/info?arg[]=rogue-signal-protocol-bin" | grep -o '"Version":"[^"]*"'
# Expected: "Version":"X.Y.Z_beta-1"
```

- [ ] Verify at: https://aur.archlinux.org/packages/rogue-signal-protocol-bin

### 7.3 Download Verification (Smoke Test)

After uploading, download and verify the builds work:
- [ ] Download Windows .zip from itch.io, extract and run
- [ ] Download Linux tarball from GitHub, extract and run
- [ ] Download AppImage from GitHub, make executable and run

### 7.4 Verify Feedback Collection

- [ ] Feedback form URL works in README.txt
- [ ] Feedback form URL works in README.md
- [ ] Feedback form URL visible on itch.io page
- [ ] Feedback form URL in Reddit post draft

### 7.5 Update Wiki

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
- [ ] Post to Discord server (if applicable)

### 9.2 First Week Follow-up

- [ ] Collect survey responses
- [ ] Prioritize bug fixes
- [ ] Plan balance tweaks based on feedback
- [ ] Consider posting to additional subreddits if initial reception is good

### 9.3 Document Known Issues

- [ ] Note any bugs found after release
- [ ] Add to next version's fix list

### 9.4 Rollback Procedure (If Critical Bug Found)

If a critical bug is discovered post-release:
- [ ] Immediately note the issue in GitHub release description
- [ ] If severe: mark release as pre-release or delete it
- [ ] Restore previous version on itch.io (upload old zip, mark as primary)
- [ ] Post update on Reddit/Discord explaining the issue
- [ ] Create hotfix branch: `git checkout -b hotfix/vX.Y.Z+1`
- [ ] Fix, test, and release patched version ASAP

---

## Quick Reference: Files with Version Strings

**Centralized (auto-read from game_rules.json via rsp.core.version):**
| File | Note |
|------|------|
| `rsp.ui.menu_about` | imports VERSION_DISPLAY |
| `rsp.ui.menu_main` | imports VERSION_DISPLAY |
| `rsp.systems.save` | imports VERSION |
| `rsp.utils.story` | imports VERSION |

**Updated by bump-version.py:**
| File | Locations |
|------|-----------|
| `game_rules.json` | 1 (source of truth) |
| `README.txt` | 1 |
| `README.md` | 2 |
| `README_DEV.md` | 2 |
| `docs/wiki/Home.md` | 1 |
| `packaging/linux/README.md` | 1 |
| `packaging/linux/PKGBUILD` | 2 (pkgver, _vertag) |
| `packaging/linux/AppImageBuilder.yml` | 1 |
| `packaging/linux/*.yml` (Flatpak) | 1 |
| `packaging/linux/*.xml` (metainfo) | 1 (adds new release entry) |

**Manual only:**
| File | Note |
|------|------|
| `CHANGELOG.md` | Content must be written manually |

**Total: 1 manual file, ~12 automated by bump-version.py**

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
