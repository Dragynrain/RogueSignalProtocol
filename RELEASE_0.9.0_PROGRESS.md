# Release Progress: v0.9.0 Beta

**Release Date:** 2025-12-27
**Release Type:** Beta
**This file:** Tracks progress for THIS specific release. Delete after release complete.
**Template:** See `RELEASE_CHECKLIST.md` for the reusable template.

---

## IMPORTANT NOTES FOR THIS RELEASE

1. **GitHub Actions builds Linux automatically** - Publishing a GitHub Release triggers `release.yml` workflow
2. **Don't confuse `git tag` with GitHub Release** - Tag alone doesn't trigger builds; must create Release
3. **Use `gh release create`** - Not just `git push origin v0.9.0-beta`
4. **Old checklist location:** `marketing/pre_release_checklist.md` is OBSOLETE - don't use it

---

## Phase 1: Pre-Build Preparation - COMPLETE

### 1.1 Version String Updates - DONE (prior to this session)
- [x] All version strings updated to 0.9.0 Beta

### 1.2 Code Quality Checks - DONE
- [x] Run full test suite: `pytest tests/ -v` - **4305 passed, 28 skipped**
- [x] Coverage: 74.73% (above 70% threshold)

### 1.4 URL Verification - DONE
- [x] All URLs verified consistent:
  - Discord: `https://discord.gg/5fykUtECqz`
  - Itch.io: `https://dragynrain.itch.io/rogue-signal-protocol`
  - Feedback: `https://forms.gle/jbwGdn8VGPa6NG9p9`

---

## Phase 2: Windows Build - COMPLETE

### 2.1 Run Windows Build Script - DONE
```bash
build\build.bat beta
```
- [x] Build completed successfully
- [x] Output: `dist/RogueSignalProtocol.exe` (38.3 MB)
- [x] Output: `releases/RogueSignalProtocol_beta_2025-12-27.zip` (195 MB)

### 2.2 Verify Windows Build Contents - DONE
- [x] `RogueSignalProtocol.exe` - 38.3 MB
- [x] `game_content.json` - 13 exploits verified
- [x] `game_rules.json` - version 0.9.0 Beta
- [x] `narrative_content.json` - valid JSON
- [x] `graphics_tiles.json` - 3.8 KB
- [x] `default_bindings.json` - 7.6 KB
- [x] `KreativeSquare.ttf` - 720 KB
- [x] `logo.png` - 738 KB
- [x] `README.txt` - version 0.9.0 Beta
- [x] `LICENSE` - present
- [x] `graphics/` - 161 files, 25 menu backgrounds
- [x] `sound/` - 39 files, 15 exploit sounds
- [x] `music/` - 5 files
- [x] `debug_mode.flag` - present (beta build)

---

## Phase 3: Linux Build - IN PROGRESS

### 3.1 Build Linux Binary - DONE (via GitHub Actions)
- [x] Created GitHub Release to trigger workflow
- [x] Command used: `gh release create v0.9.0-beta --title 'v0.9.0 Beta' --notes-file CHANGELOG.md --prerelease releases/RogueSignalProtocol_beta_2025-12-27.zip`
- [ ] Workflow completed: **WAITING** (started ~2 min ago)
- [ ] Linux tarball attached to release
- [ ] AppImage attached to release

### 3.2 Verify Linux Build Contents - PENDING
- [ ] Download and verify tarball contents
- [ ] Download and verify AppImage

### 3.3 Build Linux Packages - PENDING
- [ ] AppImage - built by GitHub Actions
- [ ] Flatpak - manual submission to Flathub
- [ ] AUR - update PKGBUILD checksums after release assets ready

---

## Phase 4: Testing - DONE (user performed)

### 4.1 Windows Basic Functionality - DONE
- [x] User tested locally

### 4.2-4.9 Additional Testing - DONE
- [x] User performed manual testing before upload

---

## Phase 5: Git & Version Control - COMPLETE

### 5.1 Commit and Tag - DONE
- [x] Bug fix committed: `a2f9051` - "Fix immediate achievement triggers for non-combat actions"
- [x] Tag created: `git tag -a v0.9.0-beta -m "Beta release 0.9.0"`
- [x] Tag pushed: `git push origin v0.9.0-beta`

### 5.2 Create GitHub Release - DONE
- [x] GitHub Release created via: `gh release create v0.9.0-beta ...`
- [x] Windows .zip uploaded
- [x] Release marked as pre-release
- [ ] Linux tarball auto-uploaded by workflow (pending)
- [ ] AppImage auto-uploaded by workflow (pending)
- [x] Release URL: https://github.com/Dragynrain/RogueSignalProtocol/releases/tag/v0.9.0-beta

---

## Phase 6: Marketing & Screenshots - PARTIALLY DONE

### 6.1 Update Screenshots - SKIPPED (existing screenshots sufficient)

### 6.2 Record Video - DONE PREVIOUSLY

### 6.3 Update Marketing Materials - DONE
- [x] Created `marketing/itch_090_beta_announcement.html` (HTML version for itch.io)
- [x] Updated to use singular "I" voice instead of "we"

---

## Phase 7: Distribution - IN PROGRESS

### 7.1 Windows Distribution - DONE
**Itch.io:**
- [x] Upload Windows .zip to itch.io
- [x] Update page description
- [x] Post devlog (HTML version)
- [x] Tags set

### 7.2 Linux Distribution - PENDING
**GitHub Releases:**
- [ ] Linux tarball uploaded (auto by workflow)
- [ ] AppImage uploaded (auto by workflow)

**Itch.io:**
- [ ] Upload Linux tarball
- [ ] Upload AppImage
- [ ] Mark as Linux compatible

**Flathub:** - DEFERRED
- [ ] Submit PR to beta branch

**AUR:** - PENDING
- [ ] Update PKGBUILD with new checksums
- [ ] Push to AUR

### 7.3 Verify Feedback Collection - DONE
- [x] Feedback form URL works everywhere

---

## Phase 8: Launch & Promotion - DEFERRED

### 8.1 Reddit Posting - DEFERRED
- [ ] Post to r/roguelikedev or r/roguelikes
- [ ] User will do this later

---

## Phase 9: Post-Release - NOT STARTED

### 9.1 Monitor for Issues
- [ ] Check itch.io comments
- [ ] Monitor feedback form responses
- [ ] Watch GitHub issues

---

## NEXT STEPS (in order)

1. **Wait for GitHub Actions workflow to complete** (~3-5 min)
   - Check: `gh run list --repo Dragynrain/RogueSignalProtocol --limit 1`

2. **Download Linux builds from GitHub release**
   - `RogueSignalProtocol-Linux.tar.gz`
   - `RogueSignalProtocol-0.9.0-beta-x86_64.AppImage`

3. **Upload Linux builds to itch.io**

4. **Update AUR PKGBUILD** (optional)
   - Download tarball, get sha256sum
   - Update `packaging/linux/PKGBUILD`

5. **Test Linux build** (optional but recommended)
   - Run in WSL2 or VM

6. **Reddit post** (when ready)

---

## SESSION LOG

- **12:00** - Started release process
- **12:08** - Tests passed (4305), URLs verified
- **12:09** - Windows build completed
- **12:09** - Build contents verified
- **12:20** - Achievement bug found and fixed
- **12:37** - GitHub Release created, workflow triggered
- **12:38** - Waiting for Linux build workflow

