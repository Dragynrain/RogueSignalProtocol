#!/bin/bash
# Push Linux builds to itch.io using butler
# Usage: ./push-itch-linux.sh [version]
# Example: ./push-itch-linux.sh 0.9.1-beta
#
# Pushes both tarball and AppImage to separate channels:
#   - linux: tarball
#   - linux-appimage: AppImage

set -e

VERSION="${1}"

if [ -z "$VERSION" ]; then
    echo "Usage: ./push-itch-linux.sh [version]"
    echo "Example: ./push-itch-linux.sh 0.9.1-beta"
    exit 1
fi

# Verify butler is installed
if ! command -v butler &> /dev/null; then
    echo "ERROR: butler not found in PATH"
    echo "Download from: https://itch.io/docs/butler/installing.html"
    echo "Then run: butler login"
    exit 1
fi

PROJECT="dragynrain/rogue-signal-protocol"

# Expected filenames (from GitHub release workflow)
TARBALL="releases/RogueSignalProtocol-${VERSION}-Linux.tar.gz"
APPIMAGE="releases/RogueSignalProtocol-${VERSION}-x86_64.AppImage"

# Check if files exist
if [ ! -f "$TARBALL" ]; then
    echo "ERROR: $TARBALL not found"
    echo "Download from GitHub release first:"
    echo "  gh release download v${VERSION} --pattern 'RogueSignalProtocol-*-Linux*' --dir releases/"
    exit 1
fi

if [ ! -f "$APPIMAGE" ]; then
    echo "ERROR: $APPIMAGE not found"
    echo "Download from GitHub release first:"
    echo "  gh release download v${VERSION} --pattern 'RogueSignalProtocol-*-Linux*' --dir releases/"
    exit 1
fi

echo ""
echo "Pushing Linux builds to itch.io..."
echo "  Project: $PROJECT"
echo "  Version: $VERSION"
echo ""

# Push tarball to linux channel
echo "Pushing tarball to 'linux' channel..."
butler push "$TARBALL" "$PROJECT:linux" --userversion "$VERSION"

echo ""

# Push AppImage to linux-appimage channel
echo "Pushing AppImage to 'linux-appimage' channel..."
butler push "$APPIMAGE" "$PROJECT:linux-appimage" --userversion "$VERSION"

echo ""
echo "Push complete!"
echo "Verify at: https://dragynrain.itch.io/rogue-signal-protocol/edit"
echo ""
echo "Check status:"
echo "  butler status $PROJECT"
