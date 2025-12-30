# Technical Debt & Future Improvements

## High Priority

### Centralize Version String (DONE)
~~Currently version is hardcoded in 21+ locations~~ - Python files now import from `game_version.py`.

**Completed:**
- Created `game_version.py` that loads version from `game_rules.json`
- Updated: `game_menu_about.py`, `game_menu_main.py`, `game_save.py`, `game_story.py`
- Remaining manual updates: JSON files, Markdown docs, Linux packaging files

**Still needed:** Build script to auto-update docs/packaging files (low priority)

### Build Script: Version-Based Release Names (DONE)
- `build.bat beta 0.9.1` now creates `RogueSignalProtocol_beta_0.9.1.zip`
- Falls back to date-based naming if no version provided
- SHA256 checksums auto-generated

---

## Medium Priority

### Build/Release Automation

#### 1. Automated itch.io Upload in GitHub Actions (DONE - needs setup)
Butler integration added to workflow. To enable:
1. Get API key from https://itch.io/user/settings/api-keys
2. Add secret `BUTLER_API_KEY` in GitHub repo settings
3. Add variable `ENABLE_ITCH_PUSH` = `true` in GitHub repo settings

### AUR Package Automation

#### 2. Simplified AUR Update Process (DONE)
Created `build/update-aur.bat`:
- Takes version and type: `update-aur.bat 0.9.2 beta`
- Downloads tarball, calculates SHA256
- Updates PKGBUILD automatically
- Generates .SRCINFO via Docker
- Copies to AUR repo if present

### CI/CD Improvements (DONE)

#### 3. Automated Smoke Test in CI
Added to GitHub Actions workflow:
- **Pre-build:** Runs `pytest tests/smoke/ tests/integration/test_game_smoke.py`
- **Post-build:** Package structure validation (verifies all required files present)
- Catches import errors, config issues, and missing assets before release

---

## Low Priority / Nice-to-Have

### Version Bump Automation (DONE)

#### 4. Version Bump Script
**Architecture:**
- `game_rules.json` line 2 is the single source of truth
- Python code reads version via `game_version.py` (no hardcoding)
- `bump-version.py` only updates static files that can't read at runtime

**Script handles:**
- `game_rules.json` (source of truth)
- README files (static documentation)
- Linux packaging (PKGBUILD, metainfo.xml, Flatpak manifest)

**Usage:**
```bash
python build/bump-version.py 0.9.1 0.9.2 beta
python build/bump-version.py --check 0.9.2 beta
```

**Still manual:** CHANGELOG.md, .SRCINFO regeneration, PKGBUILD sha256sums

### Testing Matrix Expansion (DEFERRED)

#### 5. Multi-Distro CI Testing
Currently only tests on Ubuntu in CI.

**Deferred because:**
- AppImage bundles all dependencies (glibc, SDL, etc.)
- PyInstaller creates self-contained executable
- No distro-specific code paths in the game
- High effort for limited value

**If needed later:**
- Test AppImage in Docker containers (Fedora, Arch)
- Would catch rare glibc compatibility issues
- Only worth implementing if users report cross-distro issues

### Distribution Expansion

#### 6. Steam Deck Verification Badge
Currently Steam Deck support is "experimental" per checklist.

**Future consideration:**
- Apply for Steam Deck Verified status (requires Steam release)
- Document gamepad control requirements for verification
- Not actionable until Steam release planned

**Effort:** N/A - depends on Steam release decision

---

## Completed

- [x] Butler integration for itch.io uploads
- [x] GitHub Actions CI/CD for Linux builds
- [x] AppImage packaging
- [x] AUR package creation
- [x] Multi-platform build scripts
- [x] Comprehensive release checklist (800 lines)
- [x] Version-based release names in build.bat (`build.bat beta 0.9.1`)
- [x] SHA256 checksum generation in build.bat
- [x] Unified push-all.bat script (Windows + Linux in one command)
- [x] GitHub workflow: Windows naming matches Linux (`RogueSignalProtocol-X.Y.Z-Windows.zip`)
- [x] GitHub workflow: Build type parameter via workflow_dispatch
- [x] Release notes extraction script (`build/extract-release-notes.py`)
- [x] Checklist auto-copy script (`build/new-release.bat`)
- [x] Pre-release validation script (`build/validate-release.py`)
- [x] Centralized version string (`game_version.py` - Python files import from JSON)
- [x] AUR update automation script (`build/update-aur.bat`)
- [x] Butler in GitHub Actions (workflow ready, needs `BUTLER_API_KEY` secret)
- [x] Version bump script (`build/bump-version.py` - updates all 21+ locations)
- [x] Automated smoke tests in CI (pre-build tests + post-build package validation)
