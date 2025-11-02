# Build System Reference

## Quick Commands

```bash
build\build.bat alpha      # Debug build (creates debug_mode.flag)
build\build.bat release    # Production build
```

## Requirements

- **7zip** at `C:\Program Files\7-Zip\7z.exe` (required - PowerShell Compress-Archive doesn't work)
- Python with PyInstaller (`pip install pyinstaller`)
- Script uses `Python -m PyInstaller` (more reliable than direct .exe calls)

## Outputs

```
dist/
├── RogueSignalProtocol.exe (~37MB)
├── *.json, *.png (configs & fonts)
├── graphics/, sound/, music/
└── debug_mode.flag (alpha only)

releases/
└── RogueSignalProtocol_[type]_[YYYY-MM-DD].zip (~103MB)
```

## Troubleshooting

**Build fails with "7z not found":**
- Install 7zip to default location: `C:\Program Files\7-Zip\`
- Or update `build.bat` with custom path

**PyInstaller errors:**
- Clear cache: Delete `build/` directory manually
- Check dependencies: `pip list`
- Verify imports: `python -c "import tcod; import numpy"`

**Archive wrong size:**
- Check if asset folders copied correctly
- Verify `dist/graphics/` exists and has sprites
- Missing assets = smaller archive
