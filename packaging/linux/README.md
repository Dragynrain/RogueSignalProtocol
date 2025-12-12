# Linux Packaging

This directory contains packaging configurations for Linux distribution formats.

## Package Formats

### 1. AppImage (Universal)

**Files**: `AppImageBuilder.yml`, `build-appimage.sh`

AppImages are portable, self-contained executables that work on any Linux distribution without installation.

**Building locally**:
```bash
# After PyInstaller build completes:
cd /path/to/RogueSignalProtocol
./packaging/linux/build-appimage.sh 0.8.0
```

**Output**: `RogueSignalProtocol-0.8.0-x86_64.AppImage`

**Distribution**: GitHub Releases, itch.io

### 2. Flatpak (Flathub)

**Files**: `com.dragynrain.roguesignalprotocol.yml`, `rogue-signal-protocol.desktop`, `com.dragynrain.roguesignalprotocol.metainfo.xml`

Flatpaks are sandboxed applications distributed via Flathub.

**Local testing**:
```bash
# Install flatpak-builder first
flatpak-builder --user --install --force-clean build-dir com.dragynrain.roguesignalprotocol.yml
flatpak run com.dragynrain.roguesignalprotocol
```

**Flathub submission**:
1. Fork https://github.com/flathub/flathub
2. Create branch with app ID
3. Add `com.dragynrain.roguesignalprotocol.yml`
4. Submit PR
5. Wait for review (1-7 days)

### 3. AUR (Arch Linux)

**Files**: `PKGBUILD`

The Arch User Repository package for Arch-based distributions.

**Local testing**:
```bash
# In the packaging/linux directory:
makepkg -si
```

**AUR submission**:
1. Create account at https://aur.archlinux.org
2. Generate SSH key and add to AUR account
3. Clone: `git clone ssh://aur@aur.archlinux.org/rogue-signal-protocol-bin.git`
4. Copy PKGBUILD and update sha256sums
5. Generate .SRCINFO: `makepkg --printsrcinfo > .SRCINFO`
6. Commit and push

## File Descriptions

| File | Purpose |
|------|---------|
| `AppImageBuilder.yml` | AppImage recipe (alternative builder) |
| `build-appimage.sh` | Shell script for AppImage creation |
| `com.dragynrain.roguesignalprotocol.yml` | Flatpak manifest |
| `rogue-signal-protocol.desktop` | Desktop entry for app menus |
| `com.dragynrain.roguesignalprotocol.metainfo.xml` | AppStream metadata |
| `PKGBUILD` | AUR package build script |

## Updating for New Releases

1. Update version numbers in all files
2. Update sha256sums in PKGBUILD and Flatpak manifest
3. Update release notes in metainfo.xml
4. Test each package format locally before publishing

## Notes

- All packages use the PyInstaller binary (Python is bundled)
- Assets must be in the same directory as the binary (game uses relative paths)
- Wrapper scripts change to the game directory before launching
