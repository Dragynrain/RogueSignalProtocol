# Rogue Signal Protocol - Future Ideas & Roadmap

This document tracks potential future features and improvements. These are ideas under consideration, not commitments or promises.

---

## Potential Future Features

### Ascension System
- Meta-progression system for additional replayability
- Unlock new challenges, modifiers, or starting conditions after completing runs
- Could include difficulty scaling or variant game modes
- Maintains core roguelike permadeath while adding long-term goals

### Gamepad Support
- Full controller support for accessibility
- Button mapping for all game actions
- Analog stick navigation for menus
- Would complement existing keyboard/mouse support

### Linux/Mac Port
- Cross-platform support for non-Windows systems
- Requires:
  - Platform-specific build scripts (build.sh)
  - Cross-platform file path handling (XDG directories on Linux, Application Support on Mac)
  - Platform-specific error dialogs (replace Windows MessageBox)
  - PyInstaller builds for each platform
  - Testing on each target OS
- Estimated effort: Several hours of platform-specific code adjustments
- Core game logic already uses cross-platform libraries (TCOD, pygame, pathlib)

---

## Notes

- These ideas are exploratory and may or may not be implemented
- Community feedback helps prioritize what gets built
- Contributions welcome - see [README_DEV.md](../README_DEV.md) for developer guidelines
