# Linux Distribution Strategy for Rogue Signal Protocol

## Executive Summary

**Multi-platform distribution requires 3 package formats to reach 90%+ of Linux users**. No need to submit to dozens of distro-specific repos. Steam Deck is viable via Flatpak + gamepad support.

**Platform Status**:
- **Current**: Windows-only (single .exe via PyInstaller)
- **Target**: Windows + Linux (Steam Deck compatible)
- **Future**: macOS (deferred - see Future Considerations section)

**Current Constraints**:
- Player base: 0 (pre-launch)
- Budget: $0
- Hardware: Windows PC only (Linux testing via VMs)
- Timeline: No deadline

---

## TDD Approach for Linux Compatibility

**Test-Driven Development is critical for cross-platform work** - platform bugs are hard to debug after the fact.

### TDD Principles for This Plan

1. **Write tests BEFORE implementation** - Each platform-specific change gets a failing test first
2. **Tests must pass on BOTH platforms** - Use `pytest` markers to run platform-specific tests
3. **Mock platform APIs in unit tests** - Don't require Linux to test Linux code paths
4. **Integration tests on real platforms** - VM/Steam Deck for actual validation

### Test Categories

| Category | Runs On | Purpose |
|----------|---------|---------|
| **Unit tests (mocked)** | Windows CI | Verify logic without platform |
| **Platform detection tests** | Both | Verify `is_linux()`, `is_windows()` |
| **Path resolution tests** | Both | Verify `platformdirs` integration |
| **Integration tests** | Linux VM/Deck | Full end-to-end validation |

### Pytest Markers for Platform Tests

```python
# conftest.py additions
import pytest
import sys

def pytest_configure(config):
    config.addinivalue_line("markers", "linux_only: mark test to run only on Linux")
    config.addinivalue_line("markers", "windows_only: mark test to run only on Windows")
    config.addinivalue_line("markers", "cross_platform: mark test that must pass on all platforms")

@pytest.fixture
def mock_linux_platform(monkeypatch):
    """Mock sys.platform to simulate Linux environment."""
    monkeypatch.setattr(sys, "platform", "linux")

@pytest.fixture
def mock_windows_platform(monkeypatch):
    """Mock sys.platform to simulate Windows environment."""
    monkeypatch.setattr(sys, "platform", "win32")
```

### Example TDD Workflow

```
1. Write failing test: test_get_data_dir_returns_xdg_path_on_linux()
2. Run test → FAILS (function doesn't exist or returns Windows path)
3. Implement platformdirs integration
4. Run test → PASSES
5. Run ALL tests → Verify no Windows regressions
6. Commit
```

---

## Implementation Phases

### Phase 0: Platform Detection Infrastructure  COMPLETED
Create cross-platform utilities and fix critical Windows-specific code that will crash on Linux.
- Complexity: Low (utility module + targeted fixes)
- Dependencies: None
- Risk: Low (isolated changes, easy to test)
- Status: **COMPLETED** - All changes tested on Windows, all 2393 tests passed

**What Was Fixed**:
1. Created `game_platform.py` utility module for centralized platform detection
2. Fixed DPI awareness code in `game_loop.py` (would crash on Linux at import)
3. Fixed DPI awareness code in `font_loader_freetype.py` (test block)
4. Fixed DPI awareness code in `scripts/view_kreative_glyphs.py`

All DPI calls now use `game_platform.set_dpi_awareness()` which safely no-ops on Linux.

### Phase 1: Platform Compatibility Audit (Medium Complexity)
Identify and catalog all Windows-specific code that needs cross-platform replacements.
- Complexity: Medium (code review, testing needed)
- Dependencies: Phase 0 complete
- Risk: Medium (may discover unexpected platform assumptions)

**TDD Tasks for Phase 1**:
- Write `test_game_platform.py` with tests for `is_linux()`, `is_windows()` using mocked `sys.platform`
- Add tests that verify imports don't crash on Linux (mock `ctypes.windll` to raise `AttributeError`)
- Create test matrix documenting which tests need platform mocking

### Phase 2: Cross-Platform Code Refactoring (High Complexity)
Replace Windows-specific code with cross-platform equivalents.
- Complexity: High (core changes to file paths, error handling)
- Dependencies: Phase 1 complete
- Risk: High (breaking existing Windows functionality)

**TDD Tasks for Phase 2** (write tests BEFORE implementation):
- `test_get_data_dir_returns_xdg_path_on_linux()` - mock Linux, verify `~/.local/share/`
- `test_get_data_dir_returns_localappdata_on_windows()` - mock Windows, verify `%LOCALAPPDATA%`
- `test_portable_mode_works_on_linux()` - verify portable detection logic
- `test_show_fatal_error_creates_pygame_window()` - verify pygame error screen works cross-platform
- Run full test suite after each change to catch regressions

### Phase 3: Linux Build System (Medium Complexity)
Set up PyInstaller spec and build pipeline for Linux.
- Complexity: Medium (build tooling, CI/CD setup)
- Dependencies: Phase 2 complete
- Risk: Medium (platform-specific build quirks)

**TDD Tasks for Phase 3**:
- Add GitHub Actions workflow that runs `pytest` on Ubuntu runner
- Create smoke test: `test_binary_starts_without_crash()` (subprocess launch, check exit code)
- Add asset verification test: `test_all_required_assets_bundled()` (check dist/ contents)
- Integration test on Linux VM: manual launch, verify main menu renders

### Phase 4: Package Creation (Medium Complexity)
Create distribution packages (AppImage, Flatpak, AUR).
- Complexity: Medium (each format has unique requirements)
- Dependencies: Phase 3 complete
- Risk: Low (packaging is well-documented)

**TDD Tasks for Phase 4**:
- AppImage: Test extraction and execution on clean Ubuntu VM (no Python installed)
- Flatpak: Test sandbox permissions (can access gamepad? audio? save files?)
- All formats: Verify game assets included (graphics/, sound/, music/, *.json, *.ttf)
- Create manual test script for each package format

### Phase 5: Distribution & Publishing (Low-Medium Complexity)
Submit to package repositories and configure auto-updates.
- Complexity: Low-Medium (mostly administrative)
- Dependencies: Phase 4 complete
- Risk: Low (approval processes take time but are straightforward)

### Phase 6: Testing & Verification (High Complexity)
Test on Linux VMs across multiple distros.
- Complexity: High (need multiple VM configurations)
- Dependencies: Phases 1-5 complete (but incremental testing happens throughout)
- Risk: High (platform-specific bugs hard to predict)

**Important**: Testing should happen incrementally, not just at the end:
- After Phase 2: Verify refactored code runs on WSL2/Steam Deck
- After Phase 3: Verify build works before packaging
- Phase 6 is for comprehensive cross-distro validation

**TDD Tasks for Phase 6**:
- Run full pytest suite on Steam Deck (real Arch Linux)
- Run full pytest suite on Ubuntu VM
- Create platform-specific regression test: `test_linux_specific_paths()`
- Document any tests that fail on Linux but pass on Windows (platform bugs to fix)
- Add `@pytest.mark.linux_only` to tests that can only run on Linux

---

## 1. Distribution Landscape Overview

### Linux Distribution Formats

**Universal Formats** (work across all distros):

1. **Flatpak** → Flathub (centralized store)
   - Coverage: ~80% of desktop Linux
   - Complexity: Medium (manifest creation, review process)
   - Auto-updates: Yes
   - Steam Deck: Native support
   - **Priority: HIGH**

2. **AppImage** → Self-hosted (GitHub, itch.io)
   - Coverage: 100% (no installation needed)
   - Complexity: Low (single executable bundle)
   - Auto-updates: No (manual download)
   - **Priority: HIGH**

**Distribution-Specific Formats**:

3. **AUR** → Arch Linux community repo
   - Coverage: ~5-10% (Arch-based distros)
   - Complexity: Low (PKGBUILD script)
   - Community engagement: High quality users
   - **Priority: MEDIUM**

4. **Snap** → Ubuntu's format
   - Coverage: ~40% (mostly Ubuntu)
   - Complexity: Medium
   - **Recommendation: SKIP** (Flatpak covers same users, controversial in community)

### Recommended Distribution Strategy

**Linux (3 packages = 90% coverage)**:
1. Flatpak (Flathub) - Discoverable, Steam Deck compatible
2. AppImage (itch.io) - Zero-friction downloads
3. AUR - Engaged Arch community

**Total**: 3 distribution formats, $0 cost

---

## 2. Phase 1 Details: Platform Compatibility Audit

### Windows-Specific Code Identified

#### Critical Issues (Must Fix)

**File: `game_file_paths.py`**
```python
# NEEDS FIX: Windows MessageBox with console fallback
ctypes.windll.user32.MessageBoxW(...)  # Console fallback exists but console is temporary!
```
**Impact**: When console is removed, fatal errors will be invisible on Linux
**Fix Required**: Create pygame-based error screen (render error text to SDL window)

```python
# PROBLEM: LOCALAPPDATA environment variable (Windows-only)
appdata = os.getenv("LOCALAPPDATA")
```
**Impact**: User data path resolution fails on Linux
**Fix Required**: Use platformdirs library for XDG paths (Linux)

#### Medium Issues (Should Fix)

**File: `requirements.txt`**
```
pywin32-ctypes==0.2.3  # Windows-only PyInstaller dependency
```
**Impact**: Fails to install on Linux
**Fix Required**: Add environment marker: `; sys_platform == 'win32'`

**File: `debug_export.py`**
```python
platform.system()  # Returns "Windows", "Linux", or "Darwin"
```
**Impact**: Debug exports work, but may have Windows assumptions
**Fix Required**: Verify export paths work cross-platform

### Platform Path Conventions

| Platform | User Data Location | Config Location |
|----------|-------------------|-----------------|
| **Windows** | `%LOCALAPPDATA%\RogueSignalProtocol\` | Same as user data |
| **Linux** | `~/.local/share/RogueSignalProtocol/` | `~/.config/RogueSignalProtocol/` |

**Solution**: Use `platformdirs` library (already in requirements.txt!)
```python
from platformdirs import user_data_dir, user_config_dir
data_dir = user_data_dir("RogueSignalProtocol", "Dragynrain")
```

### Audio System Compatibility

**Current**: pygame for audio (cross-platform)
**Concern**: Audio backends vary by platform
**Testing Required**:
- Linux: ALSA, PulseAudio, or Pipewire
- Verify volume controls work

### Graphics/TCOD Compatibility

**Current**: TCOD with SDL2 backend (cross-platform)
**Expected**: Should work without changes
**Testing Required**:
- Font rendering (FreeType should work)
- Window creation
- Input handling
- Fullscreen mode

---

## 3. Phase 2 Details: Cross-Platform Code Refactoring

** Good News**: `platformdirs==4.4.0` is already in requirements.txt (line 22), so no new dependencies needed!

### File: `game_file_paths.py` - Complete Rewrite

**Current Approach**: Windows-specific with LOCALAPPDATA fallback
**New Approach**: platformdirs-based with portable mode

**Changes Required**:

1. Replace `ctypes.windll` MessageBox with cross-platform pygame error screen:
   - Console fallback exists but **console is temporary** (alpha only)
   - Need pygame-based error dialog that works without console
   - Simple implementation: init minimal pygame, render error text, wait for keypress/click
   ```python
   def show_fatal_error_and_exit(message: str, title: str = "Error") -> None:
       """Display fatal error using pygame (cross-platform)."""
       try:
           import pygame
           pygame.init()
           screen = pygame.display.set_mode((640, 480))
           pygame.display.set_caption(title)
           font = pygame.font.Font(None, 24)
           # Render error message, wait for ESC/click, then exit
           ...
       except Exception:
           print(f"FATAL: {message}")  # Last resort fallback
       sys.exit(1)
   ```

2. Replace `_get_appdata_directory()` with platformdirs:
```python
def _get_system_data_directory() -> Path:
    # platformdirs handles platform detection internally - no conditional needed!
    # Windows: %LOCALAPPDATA%\Dragynrain\RogueSignalProtocol
    # Linux: ~/.local/share/RogueSignalProtocol
    # macOS: ~/Library/Application Support/RogueSignalProtocol
    return Path(user_data_dir("RogueSignalProtocol", "Dragynrain"))
```

**NOTE: PATH MIGRATION WARNING**: Verify current code's path matches platformdirs output!
- If current code uses `%LOCALAPPDATA%\RogueSignalProtocol\` (no author)
- But platformdirs returns `%LOCALAPPDATA%\Dragynrain\RogueSignalProtocol\` (with author)
- Existing Windows saves would be orphaned!

**Before implementing**: Check current `_get_appdata_directory()` output and ensure platformdirs call matches, OR add migration logic to move existing saves.

3. Update portable mode detection (same logic, different fallback)

**Complexity**: Medium
**Risk**: High (core initialization path)
**Testing**: Must verify on Windows + Linux VM

**TDD: Write These Tests BEFORE Implementing**:
```python
# tests/unit/test_game_file_paths_linux.py

def test_get_data_dir_returns_xdg_path_on_linux(mock_linux_platform, tmp_path, monkeypatch):
    """On Linux, data dir should be ~/.local/share/RogueSignalProtocol/"""
    monkeypatch.setenv("HOME", str(tmp_path))
    from game_file_paths import _get_system_data_directory
    result = _get_system_data_directory()
    assert ".local/share" in str(result) or "RogueSignalProtocol" in str(result)

def test_get_data_dir_returns_localappdata_on_windows(mock_windows_platform, tmp_path, monkeypatch):
    """On Windows, data dir should be %LOCALAPPDATA%\\RogueSignalProtocol\\"""
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    from game_file_paths import _get_system_data_directory
    result = _get_system_data_directory()
    assert str(tmp_path) in str(result) or "RogueSignalProtocol" in str(result)

def test_portable_mode_detected_correctly_on_linux(mock_linux_platform, tmp_path):
    """Portable mode should work the same on Linux."""
    # Create portable marker file, verify detection works
```

### File: `requirements.txt` - Fix Windows-Only Dependencies

**Problem**: `pywin32-ctypes` fails to install on Linux.

**Analysis**: It's a PyInstaller dependency for Windows builds, not used by game code directly.

**Solution**: Add environment marker to make it Windows-only:
```diff
- pywin32-ctypes==0.2.3
+ pywin32-ctypes==0.2.3 ; sys_platform == 'win32'
```

**Note**: `requirements.txt` DOES support environment markers (PEP 508). This allows the same file to work on both platforms.

### File: `debug_export.py` - Path Sanitization

**Changes**:
- Verify exported file paths use `Path.joinpath()` not string concatenation
- Test export directory creation on Linux
- Verify platform.system() detection works correctly

**Complexity**: Low
**Risk**: Low (debug feature)

### Platform Detection Pattern

** Already Done in Phase 0**: `game_platform.py` utility module created with:
- `is_windows()`, `is_linux()`, `is_macos()` - Platform detection
- `get_platform_name()` - Human-readable platform name
- `set_dpi_awareness()` - Cross-platform DPI handling (no-op on Linux)

Use these functions instead of inline `sys.platform` checks throughout codebase.

---

## 4. Phase 3 Details: Build System

### PyInstaller Spec Files

**Current State**:
- `RogueSignalProtocol.spec` exists (gitignored in line 16 of `.gitignore`)
- Currently configured for Windows builds only
- Need platform-specific modifications for Linux

**Approach**:
- Keep single `RogueSignalProtocol.spec` with platform detection
- OR create separate `RogueSignalProtocol-windows.spec` and `RogueSignalProtocol-linux.spec`
- Recommendation: Separate specs (clearer, easier to maintain)

**Key Differences**:

**Linux Spec**:
```python
a = Analysis(['RogueSignalProtocol.py'], ...)
exe = EXE(pyz, ...,
    name='RogueSignalProtocol',  # No .exe extension
    console=False,  # GUI app
    icon='logo.png')  # PNG for Linux, not .ico
```

### Build Environments

**Option A: Manual Builds**
- Linux: Build on Ubuntu VM
- Windows: Current Windows build machine

**Option B: GitHub Actions (Recommended)**
- Automated builds on push/release
- Matrix builds across platforms
- Artifact storage
- **Free for public repositories**

**Example GitHub Actions**:
```yaml
jobs:
  build:
    strategy:
      matrix:
        include:
          - os: ubuntu-latest
            platform: linux
            spec: RogueSignalProtocol-linux.spec
          - os: windows-latest
            platform: windows
            spec: RogueSignalProtocol-windows.spec
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true  # If using Git LFS for assets

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      # Linux-specific: Install system dependencies for SDL2/audio
      - name: Install Linux dependencies
        if: matrix.platform == 'linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y libsdl2-dev libsdl2-ttf-dev libsdl2-mixer-dev

      - run: pip install -r requirements.txt
      - run: pip install pyinstaller

      - run: pyinstaller ${{ matrix.spec }}

      # Package game assets alongside binary
      - name: Package assets
        run: |
          cp -r graphics sound music *.json *.ttf dist/

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: RogueSignalProtocol-${{ matrix.platform }}
          path: dist/
```

### Icon Format Conversions

| Platform | Format | Tool |
|----------|--------|------|
| Windows | .ico (multiple sizes) | Current |
| Linux | .png (512x512 recommended) | Convert from .ico or source |

**Action Required**: Create 512x512 PNG for Linux
- **Option A**: Extract largest size from logo.ico (often 256x256 max) and upscale
- **Option B**: Use original vector/high-res source if available (preferred)
- **Tool**: ImageMagick: `convert logo.ico[0] -resize 512x512 logo.png`
- **Note**: .ico files typically max out at 256x256 - may need to upscale or use original artwork

---

## 5. Phase 4 Details: Package Creation

### Linux: AppImage Build

**Tool**: `appimagecrafters/appimage-builder`

**Minimal Recipe** (AppImageBuilder.yml):
```yaml
version: 1
AppDir:
  path: ./AppDir
  app_info:
    id: com.dragynrain.RogueSignalProtocol
    name: Rogue Signal Protocol
    version: 0.8.0
    icon: rogue-signal-protocol
    exec: usr/bin/RogueSignalProtocol

  files:
    include:
      - dist/RogueSignalProtocol  # PyInstaller output
      - graphics/**
      - sound/**
      - music/**
      - *.json
      - *.ttf

  # Desktop entry for Linux app menus
  desktop:
    path: usr/share/applications/rogue-signal-protocol.desktop
    file: |
      [Desktop Entry]
      Name=Rogue Signal Protocol
      Exec=RogueSignalProtocol
      Icon=rogue-signal-protocol
      Type=Application
      Categories=Game;RolePlaying;
      Comment=Cyberpunk roguelike

  # Icon (must provide PNG)
  icons:
    usr/share/icons/hicolor/512x512/apps/rogue-signal-protocol.png: logo.png

AppImage:
  arch: x86_64
  update-information: guess
```

**Output**: `RogueSignalProtocol-0.8.0-x86_64.AppImage`
**Distribution**: Upload to GitHub Releases + itch.io

**Complexity**: Low
**Size**: ~50-80MB (bundles Python + dependencies)

### Linux: Flatpak Manifest

**Tool**: Flatpak builder + Flathub submission

**Minimal Manifest** (com.dragynrain.RogueSignalProtocol.yml):
```yaml
app-id: com.dragynrain.RogueSignalProtocol
runtime: org.freedesktop.Platform
runtime-version: '23.08'
sdk: org.freedesktop.Sdk
command: RogueSignalProtocol

finish-args:
  - --socket=wayland
  - --socket=fallback-x11  # For X11 compatibility
  - --socket=pulseaudio
  - --device=input  # Gamepad support (more restrictive than --device=all)
  - --share=ipc

modules:
  - name: RogueSignalProtocol
    buildsystem: simple
    build-commands:
      # Install binary and assets together (game expects assets in same directory)
      - install -dm755 /app/lib/rogue-signal-protocol
      - install -Dm755 dist/RogueSignalProtocol /app/lib/rogue-signal-protocol/RogueSignalProtocol
      - cp -r graphics sound music *.json *.ttf /app/lib/rogue-signal-protocol/
      # Wrapper script to cd to asset directory before launching
      - |
        cat > /app/bin/RogueSignalProtocol << 'EOF'
        #!/bin/sh
        cd /app/lib/rogue-signal-protocol
        exec ./RogueSignalProtocol "$@"
        EOF
      - chmod +x /app/bin/RogueSignalProtocol
    sources:
      - type: archive
        url: https://github.com/Dragynrain/RogueSignalProtocol/releases/download/v0.8.0/RogueSignalProtocol-linux.tar.gz
        sha256: CHECKSUM_HERE  # Generate with sha256sum after build
```

**Note**: Assets must be in the same directory as the binary (game uses relative paths). The wrapper script ensures correct CWD.

**Submission**: PR to github.com/flathub/flathub
**Review Time**: Typically 1-7 days
**Complexity**: Medium (manifest creation + review)

### Linux: AUR Package

**Tool**: PKGBUILD script

**Minimal PKGBUILD** (binary package - PyInstaller bundles Python):
```bash
# Maintainer: Your Name <your@email.com>
pkgname=rogue-signal-protocol-bin
pkgver=0.8.0
pkgrel=1
pkgdesc="Cyberpunk roguelike game (binary release)"
arch=('x86_64')
url="https://github.com/Dragynrain/RogueSignalProtocol"
license=('custom')
# PyInstaller binary bundles Python - only need runtime libs
depends=('sdl2' 'sdl2_ttf' 'sdl2_mixer')
provides=('rogue-signal-protocol')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/Dragynrain/RogueSignalProtocol/releases/download/v${pkgver}/RogueSignalProtocol-linux.tar.gz")
sha256sums=('SKIP')  # Replace with actual checksum

package() {
  cd "$srcdir"
  install -dm755 "$pkgdir/opt/rogue-signal-protocol"
  install -Dm755 RogueSignalProtocol "$pkgdir/opt/rogue-signal-protocol/RogueSignalProtocol"
  cp -r graphics sound music *.json *.ttf "$pkgdir/opt/rogue-signal-protocol/"

  # Create launcher script
  install -dm755 "$pkgdir/usr/bin"
  echo '#!/bin/sh' > "$pkgdir/usr/bin/rogue-signal-protocol"
  echo 'cd /opt/rogue-signal-protocol && ./RogueSignalProtocol "$@"' >> "$pkgdir/usr/bin/rogue-signal-protocol"
  chmod +x "$pkgdir/usr/bin/rogue-signal-protocol"

  # Install icon
  install -Dm644 "$srcdir/logo.png" "$pkgdir/usr/share/icons/hicolor/512x512/apps/rogue-signal-protocol.png"

  # Desktop entry
  install -Dm644 /dev/stdin "$pkgdir/usr/share/applications/rogue-signal-protocol.desktop" <<EOF
[Desktop Entry]
Name=Rogue Signal Protocol
Exec=rogue-signal-protocol
Icon=rogue-signal-protocol
Type=Application
Categories=Game;RolePlaying;
EOF
}
```

**Submission**: Upload to aur.archlinux.org
**Complexity**: Low
**Maintenance**: Community can help update

---

## 6. Phase 5 Details: Distribution & Publishing

### Linux Distribution Channels

| Channel | Submission Process | Approval Time |
|---------|-------------------|---------------|
| **Flathub** | PR to GitHub repo | 1-7 days (review) |
| **AUR** | Upload PKGBUILD | Immediate |
| **itch.io** | Upload AppImage | Immediate |
| **GitHub Releases** | Tag + upload | Immediate |

### Auto-Update Considerations

**Flatpak**: Automatic via Flathub updates
**AppImage**: Manual (can add AppImageUpdate support later)

**Recommendation**: Start with manual updates, add auto-update in future versions.

---

## 7. Steam Deck Compatibility

### You Own a Steam Deck - Perfect Test Platform!

**Steam Deck as Linux Test Hardware**:
-  You own one (real Linux testing hardware available!)
-  Real Linux environment (SteamOS 3.0 = Arch Linux based)
-  Can test Desktop Mode (keyboard/mouse) AND Gaming Mode (gamepad)
-  Native Flatpak support in Discover
-  Tests actual handheld experience
-  **Perfect screen resolution match**: 1280×800 = exactly 16×16 pixel characters

**Steam Deck provides real Arch Linux testing, but Ubuntu VM is still recommended for distro coverage** (see Testing section).

### Technical Specifications

**Steam Deck Hardware**:
- OS: SteamOS 3.0 (Arch Linux based)
- Display: 1280×800 (16:10 aspect ratio)
- Input: Gamepad + touchscreen
- Storage: Limited (recommend < 500MB installed)

**Your Game Compatibility**:
-  Turn-based (suspend/resume friendly)
-  Low resource usage
-  Python + TCOD (Linux native)
-  **Perfect resolution match**: 80×50 console at 16×16 chars = 1280×800 native
-  **Perfect aspect ratio match**: 80:50 = 16:10, same as Steam Deck screen
- NOTE: Needs gamepad support (see PLAN_GAMEPAD.md)

### Installation Methods

**Method 1: Flatpak via Discover (Recommended)**
1. Switch to Desktop Mode
2. Open Discover (KDE app store)
3. Search "Rogue Signal Protocol"
4. Install Flatpak version
5. Add to Steam library (right-click Steam → Add Non-Steam Game)
6. Launch in Gaming Mode with gamepad

**Method 2: AppImage**
1. Download AppImage to Desktop
2. `chmod +x RogueSignalProtocol.AppImage`
3. Run directly or add to Steam

**Method 3: AUR (Advanced Users)**
1. Enable AUR in pacman
2. `yay -S rogue-signal-protocol`

### Steam Deck Optimization

**Display Resolution (Perfect Match!)**:
- Your console: 80 chars × 50 chars
- Steam Deck: 1280 pixels × 800 pixels
- Character size: Exactly 16×16 pixels
- **No scaling needed** - native perfect fit!
- Aspect ratio: Both are 16:10 (1.6:1)
- Text readability: Excellent at 12-18 inch handheld viewing distance

**Input Mapping**:
- Requires gamepad implementation (PLAN_GAMEPAD.md)
- Map movement to D-pad or analog stick
- Map exploits to buttons
- Map menus to Start/Select
- **You can test immediately** once gamepad support is implemented

**Performance**:
- Game is turn-based, no performance concerns
- Battery life should be excellent (CPU-light, no 3D graphics)
- Estimated battery: 4-6 hours (turn-based games are very efficient)

**Suspend/Resume**:
- SteamOS handles suspend automatically
- Game should save state on suspend (test required)
- Perfect for quick gaming sessions

**Testing Workflow on Your Steam Deck**:
1. Build Linux binary via GitHub Actions (PyInstaller must run on target OS - cannot cross-compile)
2. Download artifact and copy to Steam Deck via USB or network share
3. Test in Desktop Mode with keyboard/mouse first
4. Test gamepad controls in Desktop Mode
5. Add to Steam library (right-click Steam → Add Non-Steam Game)
6. Launch in Gaming Mode
7. Verify text readability at arm's length
8. Test suspend/resume (press power button)
9. Monitor battery drain during gameplay

### Marketing Angle

**Steam Deck Verified Criteria**:
- Input: Full gamepad support ✓ (once implemented)
- Display: Text readable at 800p ✓ (console game)
- Seamlessness: No launchers ✓ (Python game)
- System Support: Suspend/resume ✓ (turn-based)

**Promotional Copy**:
- "Perfect for Steam Deck"
- "Coffee break roguelike - ideal for handheld"
- "Verified Steam Deck Compatible"

---

## 8. Phase 6 Details: Testing & Verification

### Primary Testing Strategy: Steam Deck (Real Hardware!)

**You Own a Steam Deck - Use It!**

Steam Deck is **perfect** for Linux testing:
-  Real Arch Linux (SteamOS)
-  Real hardware (no VM limitations)
-  Tests gamepad + keyboard/mouse
-  Tests handheld experience
-  Tests battery life
-  Tests suspend/resume
-  Tests Flatpak installation
-  Tests at target resolution (1280×800)

**Testing Workflow**:
1. Build Linux binary via GitHub Actions (PyInstaller cannot cross-compile - must build on Linux)
2. Download build artifact and transfer to Steam Deck (USB/network)
3. Test in Desktop Mode (validate functionality)
4. Test in Gaming Mode (validate gamepad)
5. Install Flatpak build from local file
6. Verify everything works

**Steam Deck provides excellent Arch Linux testing, but Ubuntu VM is still recommended** - see Secondary Testing section.

### Secondary Testing: Ubuntu VM (Recommended)

**Ubuntu is the most common desktop Linux** - testing it is strongly recommended, not optional.
Steam Deck (Arch-based) has different libraries and package versions than Ubuntu/Debian family.

**VirtualBox Setup** (Free):
1. Download VirtualBox (free)
2. Download Ubuntu 22.04 ISO (free)
3. Create VM with:
   - 4GB RAM minimum
   - 20GB storage
   - Enable 3D acceleration (helps with graphics)

**Test Distros** (Priority Order):
1. **Steam Deck** (HIGH PRIORITY - you own it!)
   - Arch Linux (SteamOS)
   - Real hardware validation
   - Gamepad testing

2. **Ubuntu 22.04 LTS** (HIGH PRIORITY - VM)
   - Most common desktop Linux (~40% of desktop Linux users)
   - Different library versions than Arch
   - Test Flatpak and AppImage installation
   - **Catches issues Steam Deck won't find**

3. **Fedora Latest** (Low Priority - VM)
   - Flatpak pre-installed
   - Tests Wayland-first environment
   - Only if issues found on Ubuntu

**WSL2 Alternative** (Windows 11):
- Built-in Linux GUI support (WSLg)
- Quick smoke testing
- **Limitation**: Not "real" Linux, may miss issues
- **Use for**: Quick checks only

### Platform Testing Matrix

| OS | Version | Architecture | Testing Method | Priority |
|----|---------|--------------|----------------|----------|
| **Steam Deck** | SteamOS 3.x | x86_64 | **Real Hardware (YOU OWN IT!)** | **HIGH** |
| **Ubuntu** | 22.04 LTS | x86_64 | VirtualBox VM | **HIGH** |
| **Fedora** | Latest | x86_64 | VirtualBox VM | Low |
| **Arch** | Rolling | x86_64 | Covered by Steam Deck | N/A |

**Why Ubuntu is HIGH priority**: Steam Deck uses Arch (rolling release, bleeding edge libraries). Ubuntu LTS uses older, stable library versions. Bugs often appear on one but not the other.

### Testing Requirements

**Functional Testing**:
- Game launches without errors
- Audio plays correctly
- Graphics render correctly
- Input (keyboard/mouse) works
- Save/load persists data correctly
- File paths resolve correctly
- Settings persist

**Platform-Specific Testing**:
- Test on Wayland and X11 (Fedora has both)
- Test font rendering consistency
- Test audio backend compatibility

**Distribution Testing**:
- AppImage runs on multiple distros without installation
- Flatpak installs and runs via Flathub sandbox
- All packages include required assets (graphics, sound, fonts)

### GitHub Actions Testing

**Automated checks**:
- Build succeeds on Ubuntu
- Binary executes without crashes
- Can import all dependencies
- Save file system works

**Limitations**:
- No GUI testing (headless runners)
- No audio testing
- No actual gameplay testing

**Use for**: Smoke tests, not full validation

---

## 9. Technical Gotchas & Edge Cases

### File System Differences

**Case Sensitivity**:
- Linux: Case-sensitive (file.txt ≠ File.txt)
- Windows: Case-insensitive
**Risk**: Asset loading may break if filenames have inconsistent casing
**Solution**: Audit all asset references for consistent casing

**Concrete Audit Steps**:
```bash
# Find all Python files that load assets
grep -rn "open\|Path\|load\|read" --include="*.py" | grep -i "graphics\|sound\|music\|\.json\|\.ttf"

# List all asset files with exact casing
find graphics sound music -type f | sort

# Check for case conflicts (files that differ only by case)
find . -type f | sort -f | uniq -di
```

**Path Separators**:
- Use `pathlib.Path` everywhere (handles separators automatically)
- Never use string concatenation for paths

**Line Endings**:
- Windows: CRLF (`\r\n`)
- Linux: LF (`\n`)
- Git should normalize (`.gitattributes` already exists)

### Font Rendering Differences

**FreeType Behavior**:
- May render slightly differently on Linux vs Windows
- Verify KreativeSquare.ttf renders correctly

**Fallback Fonts**:
- If TrueType fails, TCOD falls back to bitmap font
- Test font loading on Linux

### Audio Backend Differences

**Pygame + SDL2**:
- Linux: PulseAudio, ALSA, or Pipewire
- Windows: DirectSound

**Potential Issues**:
- Volume control may behave differently
- Audio latency may vary
- Some backends require specific SDL2 configuration

**Testing**:
- Verify all sound effects play
- Verify music loops correctly
- Verify volume controls work

### Python Version Differences

**Current**: Python 3.10+
**Linux**: May have older Python by default

**Solution**:
- Bundle Python with PyInstaller (already doing this)
- Don't rely on system Python

---

## 10. Distribution Priority Matrix

### Tier 1: Must-Have (Maximum ROI)

1. **AppImage** → GitHub Releases + itch.io
   - Complexity: Low
   - Reach: High (100% of Linux users can run)
   - Testing: Easy (just download and run)

2. **Flatpak** → Flathub
   - Complexity: Medium
   - Reach: High (80% of Linux, Steam Deck native)
   - Discoverability: Excellent (app stores)

### Tier 2: Should-Have (Good ROI)

3. **AUR** → Arch Linux
   - Complexity: Low
   - Reach: Medium (5-10%, engaged users)
   - Community: High quality feedback

### Tier 3: Skip

4. **Snap** → Ubuntu
   - Complexity: Medium
   - **Skip**: Flatpak covers same users, controversial

---

## 11. Cost Analysis

### Total Cost: $0

**Everything is free**:
- Linux AppImage: Free (self-hosted on GitHub)
- Linux Flatpak: Free (Flathub hosting)
- Linux AUR: Free (community repo)
- itch.io: Free (0-10% optional revenue share)
- GitHub Releases: Free (unlimited for public repos)
- VirtualBox: Free (testing VMs)
- GitHub Actions: Free (public repos get free CI/CD)

**No paid services required**

---

## 12. Long-Term: Steam Distribution

### Steam Platform Support

**Good News**: Steam supports Windows and Linux in a single game entry.

**Requirements**:
- $100 Steam Direct fee (one-time per game)
- Steamworks SDK integration (achievements, cloud saves)
- Steam Input API (gamepad abstraction)
- Platform builds for Windows + Linux

**Revenue Split**:
- 70% developer (you)
- 30% Valve (Steam)

**Benefits**:
- Massive audience (120M+ active users)
- Built-in update system
- Community features
- Steam Deck native integration
- Visibility in store

**When to Consider Steam**:
- **Now** (Alpha): itch.io + direct distribution
- **Beta** (v0.9): Polish based on feedback
- **v1.0**: Consider Steam release if revenue justifies $100 fee

---

## 13. Quick Reference

**See "Implementation Phases" section at top of document for detailed phase breakdown.**

**Phase Summary**:
| Phase | Goal | Key Deliverable |
|-------|------|-----------------|
| 0  | Platform detection | `game_platform.py` utility |
| 1 | Audit Windows code | List of files needing changes |
| 2 | Cross-platform refactor | Linux-compatible codebase |
| 3 | Build system | Working Linux binary |
| 4 | Packaging | AppImage, Flatpak, AUR |
| 5 | Distribution | Published packages |
| 6 | Testing | Verified cross-distro stability |

---

## 14. Success Metrics

### Distribution Metrics
- Downloads per platform (Windows vs Linux)
- Installation success rate
- Platform-specific bug reports
- User feedback by platform

### Platform Engagement
- Which platform has most active players?
- Steam Deck usage (if tracking possible)
- Flatpak vs AppImage popularity

### Cost-Benefit
- Does Linux audience justify development effort?
- Should Steam Deck be formally targeted?

**Tracking**: Use existing metrics system, add platform detection to session data

---

## 15. Minimum Screen Requirements

### Resolution Analysis

**Your Game's Console**: 80 characters wide × 50 characters tall

**Minimum Viable Resolution**: **800×600**
- Character size: 10px width × 12px height
- Text readable without squinting
- Functional UI
- Covers 99.9% of potential players

**Optimal Resolution**: **1280×800** (Steam Deck, modern laptops)
- Character size: 16px width × 16px height
- Crystal clear rendering
- Perfect aspect ratio match (16:10 = 1.6:1, same as 80:50 console)
- Steam Deck native resolution

**Excluded Resolutions**:
- 640×480: Technically possible but poor UX (8-10px chars, eye strain)
- Budget retro handhelds (480×320, 640×480): Too small for comfortable play
- Phones: Not viable for 80×50 console game

**System Requirements**: Recommend listing **800×600 minimum** in documentation.

---

## 16. Future Considerations

### After ASCENSION + GAMEPAD + LINUX are Complete

Consider revisiting macOS support with:

#### Option B: Unsigned "Experimental" macOS Build

**What This Means**:
- Build `.app` via PyInstaller (free)
- Create DMG (free)
- Distribute via itch.io as "Experimental/Community-Tested"
- **NO code signing** (no $99 Apple Developer account)
- **NO notarization**

**User Experience**:
1. Download DMG from itch.io
2. Try to open app
3. macOS Gatekeeper blocks: "App can't be opened because developer cannot be verified"
4. User must bypass:
   - **Method A**: Right-click app → Open → Click "Open" on warning
   - **Method B**: Terminal: `xattr -cr "/Applications/Rogue Signal Protocol.app"`

**Why This Is Actually Viable for Mac Gamers**:

The overlap of "Mac users" + "roguelike players" + "itch.io indie gamers" = **tech-savvy audience**.

**Mac gaming reality**:
- Mac gaming market is only ~5% of total gaming
- **But**: Those who game on Mac despite limited library are self-selected for tech-savviness
- They already bypass Gatekeeper regularly for other indie games
- Tons of itch.io games ship unsigned Mac builds
- Mac indie/roguelike communities have "how to bypass Gatekeeper" as standard knowledge
- Mac gamers use Wine, CrossOver, Parallels, Boot Camp routinely

**This demographic is comfortable with**:
- Terminal commands
- Security bypass procedures
- "Community-tested" experimental builds
- Supporting indie developers with workarounds

**Recommendation**:
- Build unsigned Mac .app after GAMEPAD + LINUX + ASCENSION complete
- Mark as "Mac build - community tested" on itch.io
- Include clear bypass instructions in README
- Let Mac indie gamers help test (free QA from engaged users)
- If build gains traction and revenue justifies it, THEN consider $99 Apple Developer account for proper signing

**This is MORE viable than initially thought** - Mac gamers who would play your roguelike are EXACTLY the demographic comfortable with unsigned indie builds.

---

## Implementation Checklist

**Phase 0: Platform Detection Infrastructure**  COMPLETED
- [x] Create `game_platform.py` utility module
- [x] Fix DPI awareness in `game_loop.py`
- [x] Fix DPI awareness in `font_loader_freetype.py`
- [x] Fix DPI awareness in `scripts/view_kreative_glyphs.py`
- [x] Test on Windows (verify game launches, DPI awareness still works) - All 2393 tests passed

**Phase 1: Audit**
- [ ] Catalog all Windows-specific code (MessageBox, LOCALAPPDATA, etc.)
- [ ] **WSL2 smoke test**: Run `python -c "import game_loop"` to catch import failures early
- [ ] Run case sensitivity audit (see Section 9 for commands)
- [ ] Test existing code on WSL2 or Linux VM (identify import failures)
- [ ] Create platform compatibility matrix
- [ ] Document required changes beyond Phase 0
- [ ] **TDD**: Write `test_game_platform.py` with mocked platform tests
- [ ] **TDD**: Add pytest markers for `linux_only`, `windows_only`, `cross_platform`
- [ ] **TDD**: Create `mock_linux_platform` and `mock_windows_platform` fixtures in conftest.py

**Phase 2: Refactoring**
- [ ] **TDD FIRST**: Write `test_get_data_dir_returns_xdg_path_on_linux()` (expect FAIL)
- [ ] **TDD FIRST**: Write `test_get_data_dir_returns_localappdata_on_windows()` (expect PASS)
- [ ] **NOTE: CRITICAL**: Verify current path matches platformdirs output:
  ```python
  # Run this check BEFORE changing code:
  from platformdirs import user_data_dir
  print(user_data_dir("RogueSignalProtocol", "Dragynrain"))
  # Compare to current _get_appdata_directory() output
  # If different, need migration logic!
  ```
- [ ] Replace `_get_appdata_directory()` in `game_file_paths.py` with `platformdirs.user_data_dir()`
- [ ] Run tests → verify Linux test now PASSES
- [ ] Replace `show_fatal_error_and_exit()` with pygame-based error screen (console is temporary)
- [ ] Add environment marker to `pywin32-ctypes` in requirements.txt: `; sys_platform == 'win32'`
- [ ] Verify `debug_export.py` uses `Path.joinpath()` (not string concat)
- [ ] Run FULL test suite → verify no Windows regressions (all 2393+ tests pass)
- [ ] **Incremental test**: Verify refactored code runs on WSL2/Steam Deck before proceeding

**Rollback Strategy for Phase 2** (High Risk phase):
- Create git branch `linux-compat` before starting changes
- Test each change individually on Windows before moving to next
- If regressions found: `git diff` to identify breaking change, revert specific commit
- Keep Windows CI running to catch regressions automatically

**Phase 3: Build System**
- [ ] Copy `RogueSignalProtocol.spec` to `RogueSignalProtocol-linux.spec`
- [ ] Modify Linux spec: remove `.exe` extension, change icon to `.png`
- [ ] Convert logo.ico to logo.png (512x512 for Linux - may need to upscale from 256x256)
- [ ] Set up GitHub Actions for Linux builds (recommended - builds in cloud, no local Linux needed)
- [ ] **TDD**: Add GitHub Actions step to run `pytest` on Ubuntu runner
- [ ] **TDD**: Create `test_binary_starts_without_crash()` smoke test
- [ ] **TDD**: Create `test_all_required_assets_bundled()` to verify dist/ contents
- [ ] **Alternative**: Build on Steam Deck Desktop Mode (real hardware, but slower iteration)
- [ ] **Alternative**: Build in Ubuntu VM (works but slow)
- [ ] Test binary on Steam Deck Desktop Mode AND Ubuntu VM
- [ ] **Incremental test**: Verify build works before packaging

**Phase 4: Linux Packaging**
- [ ] Build AppImage
- [ ] **TDD**: Test AppImage on clean Ubuntu VM (no Python installed) - verifies bundling
- [ ] Test AppImage on Fedora, Arch VMs
- [ ] Create Flatpak manifest
- [ ] **TDD**: Test Flatpak sandbox permissions (gamepad, audio, save files)
- [ ] Test Flatpak locally
- [ ] Create AUR PKGBUILD
- [ ] Test AUR package on Arch VM
- [ ] **TDD**: Create manual test checklist for each package format (launch, audio, save/load, gamepad)

**Phase 5: Distribution**
- [ ] Upload AppImage to itch.io + GitHub Releases
- [ ] Submit Flatpak to Flathub (PR)
- [ ] Upload AUR PKGBUILD
- [ ] Update README with platform install instructions
- [ ] Update itch.io page with Linux screenshots

**Phase 6: Testing**
- [ ] **TDD**: Run full `pytest` suite on Steam Deck (expect all tests pass)
- [ ] **TDD**: Run full `pytest` suite on Ubuntu VM (expect all tests pass)
- [ ] PRIMARY: Test on Steam Deck (Desktop Mode - you own this hardware!)
- [ ] Verify save/load works on Steam Deck
- [ ] Verify audio works on Steam Deck
- [ ] Verify graphics rendering (1280x800 native resolution)
- [ ] Test suspend/resume on Steam Deck
- [ ] **HIGH PRIORITY**: Test on Ubuntu 22.04 VM (catches different issues than Steam Deck)
- [ ] Verify Flatpak and AppImage work on Ubuntu
- [ ] OPTIONAL: Test on Fedora VM (Wayland-first environment)
- [ ] **TDD**: Document any tests that fail on Linux (create issues, add `@pytest.mark.linux_only` or fix)
- [ ] Collect community feedback from Linux players

---

**END OF PLAN**
