#!/bin/bash
# Build AppImage for Rogue Signal Protocol
# Run from project root after PyInstaller build completes
#
# Prerequisites:
#   - dist/RogueSignalProtocol exists (PyInstaller output)
#   - dist/ contains all game assets
#   - logo.png exists in project root
#
# Usage:
#   ./packaging/linux/build-appimage.sh [version]
#   Example: ./packaging/linux/build-appimage.sh 0.8.0

set -e

VERSION="${1:-0.8.0}"
APPNAME="RogueSignalProtocol"
APPDIR="AppDir"

echo "Building AppImage for $APPNAME v$VERSION..."

# Check prerequisites
if [ ! -f "dist/RogueSignalProtocol" ]; then
    echo "ERROR: dist/RogueSignalProtocol not found. Run PyInstaller first."
    exit 1
fi

if [ ! -f "logo.png" ]; then
    echo "ERROR: logo.png not found in project root."
    exit 1
fi

# Clean up any previous build
rm -rf "$APPDIR"

# Create AppDir structure
echo "Creating AppDir structure..."
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/512x512/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$APPDIR/usr/share/metainfo"

# Copy executable and all game files
echo "Copying game files..."
cp -r dist/* "$APPDIR/usr/bin/"
chmod +x "$APPDIR/usr/bin/RogueSignalProtocol"

# Copy icon
echo "Setting up icons..."
cp logo.png "$APPDIR/usr/share/icons/hicolor/512x512/apps/rogue-signal-protocol.png"
cp logo.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/rogue-signal-protocol.png"
cp logo.png "$APPDIR/usr/share/icons/hicolor/128x128/apps/rogue-signal-protocol.png"

# Create desktop entry
echo "Creating desktop entry..."
cat > "$APPDIR/usr/share/applications/rogue-signal-protocol.desktop" << 'EOF'
[Desktop Entry]
Name=Rogue Signal Protocol
GenericName=Roguelike Game
Comment=Cyberpunk roguelike game
Exec=RogueSignalProtocol
Icon=rogue-signal-protocol
Terminal=false
Type=Application
Categories=Game;RolePlaying;
Keywords=roguelike;cyberpunk;tactical;turn-based;
EOF

# Create AppStream metainfo (optional but recommended for app stores)
cat > "$APPDIR/usr/share/metainfo/com.dragynrain.roguesignalprotocol.appdata.xml" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>com.dragynrain.roguesignalprotocol</id>
  <name>Rogue Signal Protocol</name>
  <summary>Cyberpunk roguelike game</summary>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <description>
    <p>
      Rogue Signal Protocol is a tactical cyberpunk roguelike where you infiltrate
      corporate networks, hack systems, and fight your way through procedurally
      generated levels.
    </p>
  </description>
  <launchable type="desktop-id">rogue-signal-protocol.desktop</launchable>
  <url type="homepage">https://dragynrain.itch.io/rogue-signal-protocol</url>
  <provides>
    <binary>RogueSignalProtocol</binary>
  </provides>
  <releases>
    <release version="$VERSION" date="$(date +%Y-%m-%d)"/>
  </releases>
  <content_rating type="oars-1.1"/>
</component>
EOF

# Create AppRun script (wrapper that sets working directory)
echo "Creating AppRun..."
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
# AppRun script for Rogue Signal Protocol
# Changes to the game directory before launching (game expects assets in CWD)
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
cd "$HERE/usr/bin"
exec ./RogueSignalProtocol "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create root-level symlinks (AppImage conventions)
ln -sf usr/share/icons/hicolor/256x256/apps/rogue-signal-protocol.png "$APPDIR/.DirIcon"
ln -sf usr/share/icons/hicolor/256x256/apps/rogue-signal-protocol.png "$APPDIR/rogue-signal-protocol.png"
cp "$APPDIR/usr/share/applications/rogue-signal-protocol.desktop" "$APPDIR/rogue-signal-protocol.desktop"

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Build the AppImage
echo "Building AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APPDIR" "RogueSignalProtocol-${VERSION}-x86_64.AppImage"

# Clean up
rm -rf "$APPDIR"

echo ""
echo "AppImage created: RogueSignalProtocol-${VERSION}-x86_64.AppImage"
echo "Test with: ./RogueSignalProtocol-${VERSION}-x86_64.AppImage"
