# Build System Reference

## Quick Commands

```bash
build\build.bat alpha      # Debug build (default)
build\build.bat release    # Production build
```

## Requirements

- **7zip** installed at `C:\Program Files\7-Zip\7z.exe`
- Python with PyInstaller (`uv pip install pyinstaller`)
- Uses `Python -m PyInstaller` (more reliable than direct exe calls)
- Script uses `%~dp0` for directory navigation (works from any location)

## Build Process Details

### What Gets Built

1. **Clean previous artifacts**
   - Removes `dist/` and `build/` directories
   - Clears any previous PyInstaller cache

2. **PyInstaller execution**
   - Creates single-file executable
   - Output: `dist\RogueSignalProtocol.exe` (~37MB)

3. **Asset copying**
   - JSON configs: `game_content.json`, `game_rules.json`, `story_content.json`, `user_settings.json`
   - Font files: `*.png` tilesets
   - LICENSE and README files
   - Directories: `graphics/`, `sound/`, `music/`

4. **Build type specific**
   - **Alpha builds**: Creates `debug_mode.flag` for verbose logging
   - **Release builds**: No debug flag

5. **Archive creation**
   - Uses 7zip to create timestamped archive
   - Output: `releases/RogueSignalProtocol_[type]_[date].zip` (~103MB)

## Build Outputs

```
dist/
├── RogueSignalProtocol.exe (37MB)
├── *.json (configs)
├── *.png (fonts)
├── graphics/ (sprites)
├── sound/ (audio)
├── music/ (tracks)
├── LICENSE
├── README.md
└── debug_mode.flag (alpha only)

releases/
└── RogueSignalProtocol_alpha_2025-10-21.zip (103MB)
```

## Archive Format

7zip creates archives with these settings:
- Compression: Standard (not ultra)
- Includes all `dist/` contents
- Preserves directory structure
- Filename format: `RogueSignalProtocol_[type]_[YYYY-MM-DD].zip`

## Troubleshooting

**Build fails with "7z not found":**
- Install 7zip to default location: `C:\Program Files\7-Zip\`
- Or update `build.bat` with custom path

**PyInstaller errors:**
- Clear cache: Delete `build/` directory manually
- Check dependencies: `uv pip list`
- Verify all imports work: `python -c "import tcod; import numpy"`

**Archive is wrong size:**
- Check if all asset folders copied correctly
- Verify `dist/graphics/` exists and has sprites
- Missing assets = smaller archive
