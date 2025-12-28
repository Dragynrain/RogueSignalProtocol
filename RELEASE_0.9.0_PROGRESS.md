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

## LESSONS LEARNED (to add to main checklist)

### Linux AppImage Bug Found
- `PersistentStorage` in `data_loading.py` used relative path `"saves"` instead of `get_data_directory() / "saves"`
- AppImage mounts read-only, so any relative paths to data directories fail
- **Fix:** Added test in `test_build_verification.py::TestNoRelativeDataPaths` to catch this in future
- **Rule:** All file operations for saves/logs/metrics/debug_exports MUST use `get_data_directory()`

### Flathub Submission FAILURE
- **DO NOT let Claude submit Flathub PRs** - They explicitly ban AI-generated submissions
- **Flathub does NOT accept beta releases** - Wait for 1.0 stable
- Flathub requires:
  1. PR title exactly: "Add info.aforster.roguesignalprotocol"
  2. Filled-in PR template with checkboxes
  3. **VIDEO of app running on Linux via Flatpak** (must record yourself)
  4. Declaration that YOU are the author
  5. **Stable release only** - no alpha/beta
- Must use GitHub web UI to get the template auto-populated
- Must test Flatpak locally FIRST before submitting

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

## Phase 3: Linux Build - COMPLETE

### 3.1 Build Linux Binary - DONE (via GitHub Actions)
- [x] Created GitHub Release to trigger workflow
- [x] Command used: `gh release create v0.9.0-beta --title 'v0.9.0 Beta' --notes-file CHANGELOG.md --prerelease releases/RogueSignalProtocol_beta_2025-12-27.zip`
- [x] Workflow completed successfully
- [x] Linux tarball attached: `RogueSignalProtocol-Linux.tar.gz`
- [x] AppImage attached: `RogueSignalProtocol-0.9.0-beta-x86_64.AppImage`

**Workflow fixes required during release:**
1. Added `--appimage-extract-and-run` flag to fix FUSE error on GitHub runners
2. Added `permissions: contents: write` to workflow to fix upload permissions

### 3.2 Verify Linux Build Contents - DONE
- [x] Both Linux builds attached to GitHub Release

### 3.3 Build Linux Packages - PARTIALLY DONE
- [x] AppImage - built by GitHub Actions
- [ ] Flatpak - manual submission to Flathub (DEFERRED)
- [ ] AUR - update PKGBUILD checksums (DEFERRED)

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
- [x] Linux tarball auto-uploaded by workflow
- [x] AppImage auto-uploaded by workflow
- [x] Release URL: https://github.com/Dragynrain/RogueSignalProtocol/releases/tag/v0.9.0-beta

---

## Phase 6: Marketing & Screenshots - PARTIALLY DONE

### 6.1 Update Screenshots - SKIPPED (existing screenshots sufficient)

### 6.2 Record Video - DONE PREVIOUSLY

### 6.3 Update Marketing Materials - DONE
- [x] Created `marketing/itch_090_beta_announcement.html` (HTML version for itch.io)
- [x] Updated to use singular "I" voice instead of "we"

---

## Phase 7: Distribution - COMPLETE (pending Flathub review)

### 7.1 Windows Distribution - DONE
**Itch.io:**
- [x] Upload Windows .zip to itch.io
- [x] Update page description
- [x] Post devlog (HTML version)
- [x] Tags set

### 7.2 Linux Distribution - MOSTLY COMPLETE
**GitHub Releases:** DONE
- [x] Linux tarball uploaded (auto by workflow)
- [x] AppImage uploaded (auto by workflow)

**Itch.io:** DONE
- [x] Upload Linux tarball from GitHub Release
- [x] Upload AppImage from GitHub Release
- [x] Mark as Linux compatible

**Flathub:** REJECTED - DEFERRED TO 1.0
- [x] Fork created: https://github.com/Dragynrain/flathub
- [x] Manifest file ready with SHA256: `6b50e04ac2b20bd336d9b8b7570e6693905bfc03de4a1df4019b642258bd9a21`
- [x] Manifest fixed: uses URLs, manual tar extraction (flatpak-builder archive bug workaround)
- [x] Icon upgraded to 256x256 (Flathub requires minimum 256x256)
- [x] Added flathub.json for x86_64-only architecture
- [x] Added 3 screenshots with captions and `type="source"` attribute
- [x] LICENSE path fixed to `/app/share/licenses/...`
- [x] Branch: `info.aforster.roguesignalprotocol` based on `new-pr`
- [x] Tested Flatpak locally - builds and runs successfully
- [x] Recorded video of Flatpak running on Linux
- [x] PR submitted via GitHub web UI: https://github.com/flathub/flathub/pull/7414
- [x] **REJECTED** - Flathub does not accept beta releases, resubmit at 1.0

**AUR:** DONE
- [x] PKGBUILD updated with SHA256
- [x] .SRCINFO generated
- [x] Pushed to AUR: https://aur.archlinux.org/packages/rogue-signal-protocol-bin
- [x] SSH key created and configured for AUR

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

1. ~~**Wait for GitHub Actions workflow to complete**~~ DONE
2. ~~**Download Linux builds from GitHub release**~~ DONE
3. ~~**Upload Linux builds to itch.io**~~ DONE
4. ~~**Update AUR PKGBUILD**~~ DONE
5. ~~**Submit Flathub PR**~~ DONE (PR #7414)

### REMAINING (waiting/optional):

6. ~~**Monitor Flathub PR #7414**~~ REJECTED - betas not accepted, resubmit at 1.0

7. **Flathub Submission** (at 1.0 release)
   - Update manifest with 1.0 release URL and SHA256
   - Submit new PR via GitHub web UI
   - After acceptance: verify via aforster.info/.well-known/org.flathub.VerifiedApps.txt

8. ~~**Community posts**~~ DONE
   - [x] Reddit r/roguelikes Sharing Saturday
   - [x] RogueTemple forums
   - [x] RogueBasin wiki

9. **Monitor feedback** (ongoing)
   - Check itch.io comments
   - Monitor feedback form responses
   - Watch GitHub issues

---

## SESSION LOG

### Session 1: Initial Release
- **12:00** - Started release process
- **12:08** - Tests passed (4305), URLs verified
- **12:09** - Windows build completed
- **12:09** - Build contents verified
- **12:20** - Achievement bug found and fixed
- **12:37** - GitHub Release created, workflow triggered
- **12:38** - Waiting for Linux build workflow
- **~12:45** - Workflow failed: spec file in .gitignore, FUSE error
- **~12:50** - Fixed: removed spec from .gitignore, added `--appimage-extract-and-run`
- **~12:52** - Workflow failed again: upload permissions error
- **~12:55** - Fixed: added `permissions: contents: write` to release.yml
- **~12:58** - Workflow completed successfully! All 4 assets attached to release

### Session 2: Linux Testing & Distribution (2025-12-27 afternoon)
- **13:15** - User tested AppImage on Linux Mint - CRASHED
- **13:16** - Root cause: `PersistentStorage` using relative path `"saves"` in read-only AppImage mount
- **13:20** - Fixed `data_loading.py` to use `get_data_directory() / "saves"`
- **13:21** - Deleted broken release, committed fix, created new release
- **13:22** - New GitHub Actions build triggered
- **13:25** - Build completed successfully
- **13:30** - User re-tested AppImage on Linux Mint - WORKS
- **13:35** - Added regression test `TestNoRelativeDataPaths` to catch this in future
- **14:00** - Uploaded Windows + Linux builds to itch.io - DONE
- **14:10** - Updated itch.io announcement to note Flathub pending
- **14:15** - Created AUR account (used Docker to solve Arch CAPTCHA)
- **14:20** - Generated SSH key for AUR, configured SSH config
- **14:25** - Cloned AUR repo, generated .SRCINFO via Docker
- **14:30** - Pushed to AUR successfully: https://aur.archlinux.org/packages/rogue-signal-protocol-bin
- **14:32** - Attempted Flathub PR submission via CLI - REJECTED
- **14:34** - Flathub reviewer closed PR: "AI slop", missing template, missing video
- **14:40** - Documented lessons learned for future releases

### Session 3: Flathub Proper Submission (2025-12-27 evening)
- **15:00** - Started proper Flathub local testing
- **15:10** - flatpak-builder `type: archive` was flattening directory structure - bug in flatpak-builder
- **15:20** - Fixed: changed to `type: file` + manual `tar -xzf` extraction
- **15:30** - Build failed: icon too large (1024x1024, max 512x512)
- **15:35** - Fixed: resized logo to 128x128, uploaded to GitHub release
- **15:40** - Flatpak builds and runs successfully locally
- **15:45** - Recorded video proof of Flatpak running
- **16:00** - Rebased flathub fork branch on upstream/master (commit histories diverged)
- **16:10** - Submitted PR via GitHub web UI with video attached
- **16:15** - PR submitted - AUTO-CLOSED (wrong base branch - targeted master instead of new-pr)

### Session 4: Flathub Third Attempt (2025-12-27 ~17:00-21:00)
- **17:00** - PR #7413 auto-closed - Flathub requires PRs against `new-pr` branch, not master
- **17:10** - Cloned fresh: `git clone -b new-pr https://github.com/Dragynrain/flathub.git flathub-submission`
- **17:15** - Created branch `com.dragynrain.roguesignalprotocol-v2` from `new-pr`
- **17:20** - Discovered multiple issues via requirements review:
  1. Missing screenshots in metainfo (REQUIRED for graphical apps)
  2. Icon 128x128 too small (need 256x256 minimum)
  3. Binary is x86_64-only (need flathub.json)
  4. LICENSE installed to wrong path
  5. Missing `type="source"` on screenshot `<image>` tags
- **17:30** - Created 256x256 icon, committed to main repo
- **17:35** - Added screenshots to metainfo (3 screenshots with captions)
- **17:40** - Created flathub.json with `only-arches: ["x86_64"]`
- **17:45** - Fixed LICENSE path to `/app/share/licenses/com.dragynrain.roguesignalprotocol/`
- **17:50** - Added `type="source"` to all screenshot image tags
- **18:00** - User had stale PR page open (30 min old) - caught before submit, refreshed
- **18:05** - PR #7414 submitted: https://github.com/flathub/flathub/pull/7414
- **21:00** - PR verified: 5 commits, all URLs return 200, SHA256 checksums verified
- **STATUS** - Awaiting Flathub CI linter + human review

