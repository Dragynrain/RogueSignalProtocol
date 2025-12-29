#!/bin/bash
# Push Linux build to itch.io using butler
# Usage: ./push-itch-linux.sh [alpha|beta|release] [version]
# Example: ./push-itch-linux.sh beta 0.9.1

set -e

BUILD_TYPE="${1}"
VERSION="${2}"

if [ -z "$BUILD_TYPE" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./push-itch-linux.sh [alpha|beta|release] [version]"
    echo "Example: ./push-itch-linux.sh beta 0.9.1"
    exit 1
fi

# Verify butler is installed
if ! command -v butler &> /dev/null; then
    echo "ERROR: butler not found in PATH"
    echo "Download from: https://itch.io/docs/butler/installing.html"
    echo "Then run: butler login"
    exit 1
fi

# Verify dist folder exists
if [ ! -f "dist/RogueSignalProtocol" ]; then
    echo "ERROR: dist/RogueSignalProtocol not found"
    echo "Run build-linux.sh first"
    exit 1
fi

# Set channel based on build type
case "$BUILD_TYPE" in
    release)
        CHANNEL="linux"
        ;;
    beta)
        CHANNEL="linux-beta"
        ;;
    alpha)
        CHANNEL="linux-alpha"
        ;;
    *)
        echo "ERROR: Invalid build type. Use: alpha, beta, or release"
        exit 1
        ;;
esac

PROJECT="dragynrain/rogue-signal-protocol"

echo ""
echo "Pushing to itch.io..."
echo "  Project: $PROJECT"
echo "  Channel: $CHANNEL"
echo "  Version: $VERSION"
echo "  Source:  dist/"
echo ""

# Push with version tag
butler push dist "$PROJECT:$CHANNEL" --userversion "$VERSION"

echo ""
echo "Push complete!"
echo "View at: https://dragynrain.itch.io/rogue-signal-protocol"
