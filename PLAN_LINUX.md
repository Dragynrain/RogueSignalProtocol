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

## Implementation Phases

### Phase 1: Platform Compatibility Audit (Medium Complexity)
Identify and catalog all Windows-specific code that needs cross-platform replacements.
- Complexity: Medium (code review, testing needed)
- Dependencies: None
- Risk: Medium (may discover unexpected platform assumptions)

### Phase 2: Cross-Platform Code Refactoring (High Complexity)
Replace Windows-specific code with cross-platform equivalents.
- Complexity: High (core changes to file paths, error handling)
- Dependencies: Phase 1 complete
- Risk: High (breaking existing Windows functionality)

### Phase 3: Linux Build System (Medium Complexity)
Set up PyInstaller spec and build pipeline for Linux.
- Complexity: Medium (build tooling, CI/CD setup)
- Dependencies: Phase 2 complete
- Risk: Medium (platform-specific build quirks)

### Phase 4: Package Creation (Medium Complexity)
Create distribution packages (AppImage, Flatpak, AUR).
- Complexity: Medium (each format has unique requirements)
- Dependencies: Phase 3 complete
- Risk: Low (packaging is well-documented)

### Phase 5: Distribution & Publishing (Low-Medium Complexity)
Submit to package repositories and configure auto-updates.
- Complexity: Low-Medium (mostly administrative)
- Dependencies: Phase 4 complete
- Risk: Low (approval processes take time but are straightforward)

### Phase 6: Testing & Verification (High Complexity)
Test on Linux VMs across multiple distros.
- Complexity: High (need multiple VM configurations)
- Dependencies: Phases 1-5 complete
- Risk: High (platform-specific bugs hard to predict)

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
# PROBLEM: Windows-only MessageBox API
ctypes.windll.user32.MessageBoxW(...)
```
**Impact**: Fatal error dialogs won't work on Linux
**Fix Required**: Cross-platform error dialog or console fallback

```python
# PROBLEM: LOCALAPPDATA environment variable (Windows-only)
appdata = os.getenv("LOCALAPPDATA")
```
**Impact**: User data path resolution fails on Linux
**Fix Required**: Use platformdirs library for XDG paths (Linux)

#### Medium Issues (Should Fix)

**File: `requirements.txt`**
```
pywin32-ctypes==0.2.3  # Windows-only dependency
```
**Impact**: Fails to install on Linux
**Fix Required**: Make conditional or remove (only used for MessageBox)

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

### File: `game_file_paths.py` - Complete Rewrite

**Current Approach**: Windows-specific with LOCALAPPDATA fallback
**New Approach**: platformdirs-based with portable mode

**Changes Required**:

1. Replace `ctypes.windll` MessageBox with cross-platform dialog:
   - **Option A**: pygame messagebox (simple)
   - **Option B**: tkinter messagebox (no extra deps)
   - **Option C**: Console fallback only (simplest)
   - **Recommendation**: Option C for now (console fallback)

2. Replace `_get_appdata_directory()` with platformdirs:
```python
def _get_system_data_directory() -> Path:
    if sys.platform == "win32":
        return Path(user_data_dir("RogueSignalProtocol", "Dragynrain"))
    else:  # Linux
        return Path(user_data_dir("RogueSignalProtocol", "Dragynrain"))
```

3. Update portable mode detection (same logic, different fallback)

**Complexity**: Medium
**Risk**: High (core initialization path)
**Testing**: Must verify on Windows + Linux VM

### File: `requirements.txt` - Remove Windows Dependencies

**Change**:
```diff
- pywin32-ctypes==0.2.3
+ # pywin32-ctypes only needed on Windows for MessageBox (removed)
```

**Alternative**: Make it conditional:
```python
if sys.platform == "win32":
    install_requires.append("pywin32-ctypes")
```

### File: `debug_export.py` - Path Sanitization

**Changes**:
- Verify exported file paths use `Path.joinpath()` not string concatenation
- Test export directory creation on Linux
- Verify platform.system() detection works correctly

**Complexity**: Low
**Risk**: Low (debug feature)

### Platform Detection Pattern

**Add utility module**: `game_platform.py`
```python
import sys

def is_windows() -> bool:
    return sys.platform == "win32"

def is_linux() -> bool:
    return sys.platform.startswith("linux")

def get_platform_name() -> str:
    if is_windows(): return "Windows"
    if is_linux(): return "Linux"
    return "Unknown"
```

Use this instead of inline `sys.platform` checks throughout codebase.

---

## 4. Phase 3 Details: Build System

### PyInstaller Spec Files

**Current**: Single `RogueSignalProtocol.spec` for Windows

**New Structure**:
- `RogueSignalProtocol-windows.spec` - Windows .exe
- `RogueSignalProtocol-linux.spec` - Linux binary

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
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pyinstaller RogueSignalProtocol-${{ matrix.os }}.spec
```

### Icon Format Conversions

| Platform | Format | Tool |
|----------|--------|------|
| Windows | .ico (multiple sizes) | Current |
| Linux | .png (512x512 recommended) | Convert from .ico |

**Action Required**: Extract 512x512 PNG from existing logo.ico for Linux

---

## 5. Phase 4 Details: Package Creation

### Linux: AppImage Build

**Tool**: `appimagecrafters/appimage-builder`

**Minimal Recipe** (AppImageBuilder.yml):
```yaml
version: 1
AppDir:
  app_info:
    id: com.dragynrain.RogueSignalProtocol
    name: Rogue Signal Protocol
    version: 0.8.0
    exec: usr/bin/RogueSignalProtocol
  files:
    include:
      - dist/RogueSignalProtocol  # PyInstaller output
      - graphics/**
      - sound/**
      - music/**
      - *.json
      - *.ttf
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
  - --socket=x11
  - --socket=pulseaudio
  - --device=all  # Gamepad support
  - --share=ipc

modules:
  - name: RogueSignalProtocol
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=/app .
      - install -Dm755 RogueSignalProtocol.py /app/bin/RogueSignalProtocol
    sources:
      - type: git
        url: https://github.com/Dragynrain/RogueSignalProtocol.git
        tag: v0.8.0
```

**Submission**: PR to github.com/flathub/flathub
**Review Time**: Typically 1-7 days
**Complexity**: Medium (manifest creation + review)

### Linux: AUR Package

**Tool**: PKGBUILD script

**Minimal PKGBUILD**:
```bash
pkgname=rogue-signal-protocol
pkgver=0.8.0
depends=('python' 'python-tcod' 'python-pygame')
source=("git+https://github.com/Dragynrain/RogueSignalProtocol.git#tag=v${pkgver}")

package() {
  cd "$srcdir/RogueSignalProtocol"
  install -dm755 "$pkgdir/opt/rogue-signal-protocol"
  cp -r . "$pkgdir/opt/rogue-signal-protocol/"
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
- ✅ You own one (real Linux testing hardware available!)
- ✅ Real Linux environment (SteamOS 3.0 = Arch Linux based)
- ✅ Can test Desktop Mode (keyboard/mouse) AND Gaming Mode (gamepad)
- ✅ Native Flatpak support in Discover
- ✅ Tests actual handheld experience
- ✅ **Perfect screen resolution match**: 1280×800 = exactly 16×16 pixel characters

**This means you can skip VirtualBox VMs entirely and test on real hardware!**

### Technical Specifications

**Steam Deck Hardware**:
- OS: SteamOS 3.0 (Arch Linux based)
- Display: 1280×800 (16:10 aspect ratio)
- Input: Gamepad + touchscreen
- Storage: Limited (recommend < 500MB installed)

**Your Game Compatibility**:
- ✅ Turn-based (suspend/resume friendly)
- ✅ Low resource usage
- ✅ Python + TCOD (Linux native)
- ✅ **Perfect resolution match**: 80×50 console at 16×16 chars = 1280×800 native
- ✅ **Perfect aspect ratio match**: 80:50 = 16:10, same as Steam Deck screen
- ⚠️ Needs gamepad support (see PLAN_GAMEPAD.md)

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
1. Build Linux binary on Windows (PyInstaller)
2. Copy to Steam Deck via USB or network share
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
- ✅ Real Arch Linux (SteamOS)
- ✅ Real hardware (no VM limitations)
- ✅ Tests gamepad + keyboard/mouse
- ✅ Tests handheld experience
- ✅ Tests battery life
- ✅ Tests suspend/resume
- ✅ Tests Flatpak installation
- ✅ Tests at target resolution (1280×800)

**Testing Workflow**:
1. Build Linux binary on Windows
2. Transfer to Steam Deck (USB/network)
3. Test in Desktop Mode (validate functionality)
4. Test in Gaming Mode (validate gamepad)
5. Install Flatpak build from local file
6. Verify everything works

**This replaces the need for VirtualBox VMs!**

### Secondary Testing: Optional VMs

**Only if you want to test other distros** (Steam Deck covers Arch):

**VirtualBox Setup** (Free, Optional):
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

2. **Ubuntu 22.04 LTS** (Medium Priority - VM)
   - Most common desktop Linux
   - Test Flatpak and AppImage
   - Only if you want additional distro coverage

3. **Fedora Latest** (Low Priority - VM)
   - Flatpak pre-installed
   - Tests Wayland
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
| **Ubuntu** | 22.04 LTS | x86_64 | VirtualBox VM (optional) | Medium |
| **Fedora** | Latest | x86_64 | VirtualBox VM (optional) | Low |
| **Arch** | Rolling | x86_64 | Covered by Steam Deck | N/A |

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

## 13. Recommended Action Plan

### Phase 1: Platform Compatibility Audit
**Goal**: Identify all Windows-specific code

**Tasks**:
- Grep for Windows-specific APIs
- Catalog path handling code
- Identify platform assumptions
- Document required changes

**Deliverable**: List of files needing changes

---

### Phase 2: Cross-Platform Refactoring
**Goal**: Make codebase Linux-compatible

**Tasks**:
- Rewrite `game_file_paths.py` with platformdirs
- Remove MessageBox API (use console fallback)
- Remove pywin32-ctypes dependency
- Create `game_platform.py` utility
- Test on Windows (verify no regressions)

**Deliverable**: Cross-platform codebase

---

### Phase 3: Linux Build System
**Goal**: Create Linux executable

**Tasks**:
- Create PyInstaller spec for Linux
- Set up Ubuntu VM for testing
- Build Linux binary
- Test on Ubuntu VM
- Set up GitHub Actions (optional)

**Deliverable**: Working Linux build

---

### Phase 4: Package Creation
**Goal**: Create distribution packages

**Tasks**:
- Build AppImage
- Test AppImage on multiple distros
- Create Flatpak manifest
- Test Flatpak locally
- Create AUR PKGBUILD

**Deliverable**: 3 Linux packages

---

### Phase 5: Distribution
**Goal**: Publish to repositories

**Tasks**:
- Upload AppImage to itch.io + GitHub Releases
- Submit Flatpak to Flathub (wait for review)
- Upload AUR package
- Update README with Linux install instructions

**Deliverable**: Public Linux distribution

---

### Phase 6: Testing & Iteration
**Goal**: Verify stability across distros

**Tasks**:
- Test on Ubuntu, Fedora, Arch VMs
- Collect bug reports
- Fix platform-specific issues
- Update packages

**Deliverable**: Stable Linux support

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

**Phase 1: Audit**
- [ ] Catalog all Windows-specific code
- [ ] Test existing code on Linux VM (identify breaks)
- [ ] Create platform compatibility matrix
- [ ] Document required changes

**Phase 2: Refactoring**
- [ ] Rewrite `game_file_paths.py` with platformdirs
- [ ] Replace MessageBox with console fallback
- [ ] Remove or conditionalize `pywin32-ctypes`
- [ ] Create `game_platform.py` utility module
- [ ] Test on Windows (verify no regressions)

**Phase 3: Build System**
- [ ] Create PyInstaller spec for Linux
- [ ] Convert logo.ico to .png for Linux
- [ ] Set up Ubuntu VM in VirtualBox
- [ ] Set up GitHub Actions for automated builds (optional)
- [ ] Test builds on Linux VM

**Phase 4: Linux Packaging**
- [ ] Build AppImage
- [ ] Test AppImage on Ubuntu, Fedora, Arch VMs
- [ ] Create Flatpak manifest
- [ ] Test Flatpak locally
- [ ] Create AUR PKGBUILD
- [ ] Test AUR package on Arch VM

**Phase 5: Distribution**
- [ ] Upload AppImage to itch.io + GitHub Releases
- [ ] Submit Flatpak to Flathub (PR)
- [ ] Upload AUR PKGBUILD
- [ ] Update README with platform install instructions
- [ ] Update itch.io page with Linux screenshots

**Phase 6: Testing**
- [ ] Test on Ubuntu 22.04 VM
- [ ] Test on Fedora latest VM
- [ ] Test on Arch Linux VM
- [ ] Test on Steam Deck (if hardware available)
- [ ] Verify save/load on all distros
- [ ] Verify audio on all distros
- [ ] Verify graphics rendering consistency
- [ ] Collect community feedback

---

**END OF PLAN**
