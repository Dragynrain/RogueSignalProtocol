#!/bin/bash
# Linux build script for Rogue Signal Protocol
# Usage: ./build/build-linux.sh

set -e

echo "=== Building Rogue Signal Protocol for Linux ==="

# Check we're in the right directory
if [ ! -f "RogueSignalProtocol.py" ]; then
    echo "ERROR: Run this script from the project root directory"
    exit 1
fi

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: No virtual environment active. Consider: source .venv/bin/activate"
fi

# Check PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "ERROR: PyInstaller not found. Install with: pip install pyinstaller"
    exit 1
fi

# Build the executable
echo "Building executable..."
pyinstaller RogueSignalProtocol-linux.spec --noconfirm

# Copy assets to dist
echo "Copying assets to dist/..."
cp game_content.json dist/
cp game_rules.json dist/
cp graphics_tiles.json dist/
cp narrative_content.json dist/
cp default_bindings.json dist/
cp KreativeSquare.ttf dist/
cp logo.png dist/
cp -r graphics dist/
cp -r sound dist/
cp -r music dist/

# Copy optional files if they exist
[ -f "LICENSE" ] && cp LICENSE dist/
[ -f "README.txt" ] && cp README.txt dist/

echo ""
echo "=== Build complete ==="
echo "Output: dist/RogueSignalProtocol"
echo "Run with: cd dist && ./RogueSignalProtocol"
