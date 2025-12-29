# Linux Packaging

This directory contains packaging configurations for Linux distribution formats.

## Current Release: 0.9.0-beta

This is a **beta release** targeting community testing before 1.0 stable.

## Package Formats

### 1. AppImage (Universal)

**Files**: `AppImageBuilder.yml`, `build-appimage.sh`

AppImages are portable, self-contained executables that work on any Linux distribution without installation.

**Building locally**:
```bash
# After PyInstaller build completes:
cd /path/to/RogueSignalProtocol
./packaging/linux/build-appimage.sh 0.9.0-beta
```

**Output**: `RogueSignalProtocol-0.9.0-beta-x86_64.AppImage`

**Distribution**: GitHub Releases, itch.io

### 2. Flatpak (Flathub)

**Files**: `info.aforster.roguesignalprotocol.yml`, `info.aforster.roguesignalprotocol.desktop`, `info.aforster.roguesignalprotocol.metainfo.xml`

Flatpaks are sandboxed applications distributed via Flathub.

**Local testing**:
```bash
# Install flatpak-builder first
flatpak-builder --user --install --force-clean build-dir info.aforster.roguesignalprotocol.yml
flatpak run info.aforster.roguesignalprotocol
```

**Flathub BETA submission** (for 0.9.0-beta):
1. Fork https://github.com/flathub/flathub
2. Create branch: `info.aforster.roguesignalprotocol`
3. Add `info.aforster.roguesignalprotocol.yml`
4. Submit PR targeting the **beta branch**
5. Wait for review (1-7 days)

**User installation from beta channel**:
```bash
flatpak remote-add --if-not-exists flathub-beta https://flathub.org/beta-repo/flathub-beta.flatpakrepo
flatpak install flathub-beta info.aforster.roguesignalprotocol
```

**Note**: Beta apps don't appear in main Flathub listings. When ready for 1.0 stable, submit new PR to stable branch (users must reinstall).

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
| `info.aforster.roguesignalprotocol.yml` | Flatpak manifest |
| `info.aforster.roguesignalprotocol.desktop` | Desktop entry for app menus |
| `info.aforster.roguesignalprotocol.metainfo.xml` | AppStream metadata |
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
