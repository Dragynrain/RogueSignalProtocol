# Build Types & Logging System

## Overview

RogueSignalProtocol supports two build types with different logging configurations:

- **Alpha** - For playtesters, includes debug logging
- **Release** - For public release, minimal logging

## Build Types

### Alpha Build (Default)

**Purpose**: Playtesting and bug reports

**Logging**:
- Level: DEBUG (verbose)
- Output: Console + game_debug.log file
- Includes: All debug messages, info, warnings, errors

**Files Created**:
- `debug_mode.flag` - Presence enables DEBUG logging
- `game_debug.log` - Full debug log for bug reports
- `build_info.txt` - Build type and timestamp

**When to Use**:
- Sending to playtesters
- Alpha/Beta releases
- Early access builds
- Any build where you need bug reports

**Build Command**:
```bash
cd build
build.bat alpha
# or just:
build.bat  # alpha is default
```

**Archive Name**: `RogueSignalProtocol_Alpha_YYYY-MM-DD_HHMMSS.zip`

---

### Release Build

**Purpose**: Public release, production builds

**Logging**:
- Level: WARNING (minimal)
- Output: game_errors.log file only (no console)
- Includes: Only warnings and errors

**Files Created**:
- `game_errors.log` - Errors only (minimal)
- `build_info.txt` - Build type and timestamp
- NO `debug_mode.flag` (debug logging disabled)

**When to Use**:
- Final public releases
- Steam/itch.io builds
- Stable versions
- When you don't need detailed logs

**Build Command**:
```bash
cd build
build.bat release
```

**Archive Name**: `RogueSignalProtocol_Release_YYYY-MM-DD_HHMMSS.zip`

---

## How Logging Works

### Detection Mechanism

The game checks for `debug_mode.flag` at startup:

```python
DEBUG_MODE = os.path.exists('debug_mode.flag')
```

- **File exists** → DEBUG logging enabled
- **File missing** → WARNING logging only

### For End Users

**Alpha builds** include this message at startup:
```
DEBUG MODE: Verbose logging enabled (Alpha build)
```

**Release builds** show:
```
RELEASE MODE: Minimal logging (Release build)
```

### For Playtesters

Alpha builds create `game_debug.log` with detailed information:
- Every function call
- All game events
- State changes
- Error stack traces

**Tell playtesters**: "If the game crashes, send us the game_debug.log file!"

### For Regular Users

Release builds only log serious errors to `game_errors.log`:
- Exceptions
- Critical failures
- Configuration errors

No performance impact from logging.

---

## User Control

Users can manually control logging by:

**Enable Debug Logging**:
1. Create empty file: `debug_mode.flag`
2. Restart game
3. Check for `game_debug.log`

**Disable Debug Logging**:
1. Delete `debug_mode.flag`
2. Restart game
3. Only `game_errors.log` created

This is documented in README.txt under "ADVANCED - LOGGING CONTROL"

---

## Build Workflow

### Alpha Build Workflow
```
1. Run: build.bat alpha
2. PyInstaller creates exe
3. Script creates debug_mode.flag
4. Script creates build_info.txt
5. Game checks for flag at startup
6. Debug logging enabled
7. game_debug.log created during gameplay
```

### Release Build Workflow
```
1. Run: build.bat release
2. PyInstaller creates exe
3. NO debug_mode.flag created
4. Script creates build_info.txt
5. Game checks for flag at startup (not found)
6. Minimal logging enabled
7. Only game_errors.log created (if errors occur)
```

---

## GitHub Actions

Default: **Alpha builds** (for early releases with bug tracking)

To create a release build via GitHub Actions:
1. Edit `.github/workflows/release.yml`
2. Comment out lines that create `debug_mode.flag`:
```yaml
# Comment these lines for release builds:
# Write-Host "Creating debug_mode.flag for alpha/beta testing..."
# "This file enables DEBUG logging..." | Out-File -FilePath "dist\debug_mode.flag"
```

---

## Files Reference

### Created by Build Script

| File | Alpha | Release | Purpose |
|------|-------|---------|---------|
| `debug_mode.flag` | ✅ | ❌ | Enables DEBUG logging |
| `build_info.txt` | ✅ | ✅ | Build type, date, log level |

### Created at Runtime

| File | Alpha | Release | Purpose |
|------|-------|---------|---------|
| `game_debug.log` | ✅ | ❌ | Verbose debug log |
| `game_errors.log` | ❌ | ✅ | Error log only |

---

## Testing

### Test Alpha Build
```bash
cd build
build.bat alpha
cd ..\dist
dir debug_mode.flag  # Should exist
RogueSignalProtocol.exe
# Should see: "DEBUG MODE: Verbose logging enabled"
dir game_debug.log   # Should be created
```

### Test Release Build
```bash
cd build
build.bat release
cd ..\dist
dir debug_mode.flag  # Should NOT exist
RogueSignalProtocol.exe
# Should see: "RELEASE MODE: Minimal logging"
dir game_errors.log  # Only created if errors occur
```

---

## Best Practices

### For Alpha Testing
- Always use alpha builds
- Ask testers to include game_debug.log with bug reports
- Logs help reproduce and fix issues quickly

### For Public Releases
- Use release builds to reduce log noise
- Errors still logged to game_errors.log
- Can ask users to enable debug mode if needed

### For Development
- Run from source: `python RogueSignalProtocol.py`
- Creates `debug_mode.flag` automatically? No - needs manual creation
- Or run alpha build for testing

---

## Troubleshooting

### "No log file created"
- Release build: Normal, only logs errors
- Alpha build: Check debug_mode.flag exists

### "Too much logging"
- Delete debug_mode.flag
- Restart game
- Will switch to WARNING level

### "Need debug log from user"
- Ask them to create debug_mode.flag
- Have them reproduce issue
- Send you game_debug.log

---

## Summary

| Feature | Alpha | Release |
|---------|-------|---------|
| Console output | Yes | No |
| Debug logging | Yes | No |
| Log file | game_debug.log | game_errors.log |
| Flag file | Present | Absent |
| Use case | Testing | Production |
| Command | `build.bat alpha` | `build.bat release` |

Choose the right build for your distribution needs!
