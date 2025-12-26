# RogueSignalProtocol - Build Guide

## Quick Start

### Alpha Build (Default - for playtesters)
```bash
cd build
build.bat alpha
# or just:
build.bat
```

### Release Build (for public release)
```bash
cd build
build.bat release
```

Both will:
1. **Regenerate wiki documentation** from game JSON files (Enemy, Exploit, Network databases)
2. Build the .exe with PyInstaller
3. Copy all assets to `dist/`
4. Configure logging based on build type
5. Create a timestamped zip in `releases/`

**See BUILD_TYPES.md for detailed information about build types and logging.**

## What Gets Built

The `dist/` folder will contain everything needed to run the game:

```
dist/
├── RogueSignalProtocol.exe  (main executable)
├── README.txt               (instructions for users)
├── game_content.json
├── game_rules.json
├── graphics_tiles.json
├── narrative_content.json
├── terminal10x16_gs_ro.png
├── graphics/                (all sprite PNGs)
├── sound/                   (all sound effects)
└── music/                   (all music files)
```

## Build Outputs

- **dist/** - Complete game distribution (distribute this whole folder, or the zip)
- **releases/** - Timestamped zip files of each build (for archiving)
- **build/RogueSignalProtocol/** - PyInstaller temp files (auto-cleaned)

## Distributing Your Game

### Option 1: Distribute the dist/ folder
Just zip up the entire `dist/` folder and share it. Users extract and run `RogueSignalProtocol.exe`.

### Option 2: Use the auto-generated zip
The build script creates `releases/RogueSignalProtocol_YYYY-MM-DD_HHMM.zip` automatically. Share that.

### Option 3: Upload to itch.io
1. Run `build.bat`
2. Upload the contents of `dist/` to itch.io
3. Mark `RogueSignalProtocol.exe` as the main executable

## GitHub Releases (Automated)

The repository includes a GitHub Actions workflow that automatically builds the game when you create a release:

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Choose a tag (e.g., `v1.0.0`)
4. Write release notes
5. Click "Publish release"

GitHub will automatically:
- Build the executable
- Package everything into `RogueSignalProtocol-Windows.zip`
- Attach it to your release

Users can then download the zip directly from GitHub.

## When to Build

### Build when:
- Creating a new version/release
- Sharing with playtesters
- Uploading to itch.io or other platforms
- Testing exe-specific issues
- Archiving a milestone build

### Don't build for:
- Regular development (use `python RogueSignalProtocol.py`)
- Running tests (use `python test_commands.py full`)
- Every git commit
- Debugging gameplay

## Troubleshooting

### Build fails with "module not found"
- Make sure your venv is activated: `.venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Assets missing in dist/
- Check that asset folders exist in project root
- Verify paths in `build.bat`

### Exe won't run
- Test in dist/ folder (not from build/)
- Ensure all assets are present
- Check Windows antivirus isn't blocking it

## File Locations

- Build script: `build/build.bat`
- Output folder: `dist/`
- Release archives: `releases/`
- Distribution README: `build/DIST_README.txt` (copied to dist/README.txt)
- GitHub Actions: `.github/workflows/release.yml`

## gitignore

The following are excluded from git (safe to delete locally):
- `dist/` - Build output
- `releases/` - Archive folder
- `build/RogueSignalProtocol/` - PyInstaller temp files
- `*.spec` - PyInstaller spec files

The build script (`build/build.bat`) IS committed to git so you can rebuild anywhere.
