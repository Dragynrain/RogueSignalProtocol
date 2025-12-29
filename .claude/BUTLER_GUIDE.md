# Butler (itch.io CLI) Reference

Quick reference for itch.io's command-line build uploader.

## Location

Butler executable: `build/butler/butler.exe`

## Capabilities

**What butler CAN do:**
- Push builds with differential uploads (only changed files after first push)
- Automatic compression (~300MB build transmits ~120MB)
- Version tagging (`--userversion`)
- Channel management (windows, windows-beta, linux, etc.)
- Dry-run testing (`--dry-run`)
- Check channel status
- File utilities: `dl`, `wipe`, `ditto`, `untar`

**What butler CANNOT do:**
- Update page content/description
- Post to devlog/blog
- Upload or manage screenshots
- Edit metadata, tags, or pricing
- Anything besides build file uploads

For page content, use itch.io web interface or the server-side API.

## Commands

```bash
# Check version/installation
butler version

# Authenticate (one-time, opens browser)
butler login

# Check what's currently uploaded
butler status dragynrain/rogue-signal-protocol

# Dry-run (test without uploading)
butler push --dry-run dist dragynrain/rogue-signal-protocol:windows-beta

# Push a build
butler push dist dragynrain/rogue-signal-protocol:windows-beta --userversion 0.9.1
```

## Channel Naming

Channels auto-detect platform from name:
- Contains `win` or `windows` -> Windows
- Contains `linux` -> Linux
- Contains `mac` or `osx` -> Mac

Project channels:
| Build Type | Windows | Linux |
|------------|---------|-------|
| Release | `windows` | `linux` |
| Beta | `windows-beta` | `linux-beta` |
| Alpha | `windows-alpha` | `linux-alpha` |

## Scripts

- `build/push-itch.bat` - Windows push script
- `build/push-itch-linux.sh` - Linux push script

Usage: `build\push-itch.bat [alpha|beta|release] [version]`

## Limits

- Max uncompressed build size: 30GB
- First push: full upload
- Subsequent pushes: differential (typically 5-20% of build)

## Useful Flags

- `--dry-run` - Preview without uploading
- `--userversion X.Y.Z` - Tag with version number
- `--ignore "*.pdb"` - Exclude file patterns
- `--if-changed` - Skip if content matches latest build
