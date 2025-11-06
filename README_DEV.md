# Rogue Signal Protocol - Developer Guide

**Version 0.8.0 Alpha** - A coffee break cyberpunk stealth roguelike built with Python and TCOD

> 📖 **For Players**: See [README.txt](README.txt) for game instructions
>
> 🔧 **For Developers/Modders**: This guide covers building from source, modding, and contributing

Copyright (C) 2025 Adam Forster

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See LICENSE file for full details.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Version](https://img.shields.io/badge/version-0.8.0%20Alpha-orange.svg)
![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)

## 🎮 Game Overview

Rogue Signal Protocol is a coffee break stealth-focused cyberpunk roguelike where you infiltrate corporate networks as a digital ghost. Complete runs in 10-15 minutes as you navigate procedurally generated levels, avoid sophisticated AI security systems, and discover the dark secrets hidden in the corporate data vaults.

### Key Features

- **🕵️ Stealth-Focused Gameplay**: Hide in shadows, avoid detection, and use cunning over brute force
- **🤖 8 Unique Enemy Types**: From basic Scanners to the terrifying Admin Avatar
- **⚡ 12 Powerful Exploits**: Combat and utility abilities including Buffer Overflow, Shadow Step, and EMP Burst
- **🌐 3 Network Environments**: Corporate Network, Government System, and Military Backbone
- **📚 Rich Narrative**: Discover 20+ story fragments revealing the conspiracy behind Project Chimera
- **🎵 Enhanced Audio**: Full sound effects and atmospheric music
- **💾 Persistent Progression**: Story discoveries and settings carry between runs
- **⚙️ Permadeath Mechanics**: Save files deleted on death - every decision matters

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- Windows 10/11 (primary support)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.git
   cd RogueSignalProtocol
   ```

2. **Set up virtual environment** (recommended)
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**
   ```bash
   .venv\Scripts\python.exe RogueSignalProtocol.py
   ```

## 🎯 How to Play

### Objective
Navigate through 3 increasingly dangerous network levels, reach the gateway (>) on each level, and uncover the truth behind the Omni-Lyra Cognitive Resilience Initiative.

### Controls
- **Movement**: Arrow Keys, WASD, or Numpad
- **Exploits**: 1-5 keys to use equipped exploits
- **Inventory**: I key to manage codes and exploits
- **Look Mode**: L key to examine entities and terrain
- **Lore Fragments**: F key to view discovered story fragments
- **Pause**: ESC key

### Core Mechanics

- **Stealth**: Hide in shadows (*) to avoid enemy detection
- **Heat Management**: Exploit usage generates heat; overheating causes damage
- **Detection System**: High detection levels spawn the Admin Avatar
- **Resource Management**: Balance CPU (health), RAM (exploit capacity), and Heat

### Enemy Types

| Symbol | Name | HP | Vision | Behavior | Damage |
|--------|------|----|---------|---------| -------|
| S | Scanner | 35 | 4 | Static | 0 |
| P | Patrol | 40 | 4 | Patrol Routes | 15 |
| B | Bot | 25 | 3 | Random Movement | 8 |
| F | Firewall | 80 | 5 | Static Guardian | 0 |
| H | Hunter | 50 | 6 | Seeks Players | 22 |
| V | Virus | 35 | 4 | Applies Virus | 0 |
| I | Inhibitor | 30 | 4 | Slows Movement | 5 |
| A | Admin Avatar | 250 | 8 | Perfect Tracking | 45 |

## 🛠️ Development Setup

### Tech Stack
- **Engine**: Python 3.10+ with python-tcod (19.4.0+)
- **Audio**: pygame (2.6.1+)
- **Build**: PyInstaller for exe creation
- **Testing**: pytest with 700+ tests (unit + integration)
- **Architecture**: Modular component system with JSON-driven configuration

### Project Structure
```
RogueSignalProtocol/
├── RogueSignalProtocol.py       # Main entry point
├── game_*.py                    # Core game modules (50+ files)
├── data_loading.py              # Configuration management
│
├── Configuration (JSON-driven):
├── game_content.json            # Items, exploits, loot tables
├── game_rules.json              # Balance, colors, gameplay rules
├── graphics_tiles.json          # Sprite mappings
├── story_content.json           # Narrative fragments
│
├── Assets:
├── graphics/                    # PNG sprites (150+ files)
├── sound/                       # WAV sound effects (40+ files)
├── music/                       # MP3 background music
├── terminal10x16_gs_ro.png      # Font tileset
│
├── Build System:
├── build/
│   ├── build.bat                # Build script (alpha/release)
│   ├── BUILD_GUIDE.md           # Build documentation
│   ├── BUILD_TYPES.md           # Logging system docs
│   └── clean.bat                # Cleanup script
│
├── Testing:
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data builders
├── test_commands.py             # Test runner with coverage
└── pytest.ini                   # Test configuration
```

### Key Architecture Features
- **Modular Design**: Clean separation (rendering, input, AI, combat, etc.)
- **JSON-Driven**: All content easily moddable through JSON files
- **Component System**: Entities use composition over inheritance
- **Event-Driven**: Message log system for game events
- **State Management**: Clean state transitions and save/load
- **Coordinate Helpers**: TCOD coordinate system wrappers (avoid bugs!)

---

## 🧪 Testing

The game has comprehensive test coverage with a custom test runner.

### Quick Testing
```bash
# Run full test suite with coverage
python test_commands.py full

# Quick unit tests only (fast feedback)
python test_commands.py quick

# Integration tests only
python test_commands.py integration

# Generate coverage report
python test_commands.py coverage  # Creates htmlcov/

# Test only changed files
python test_commands.py changed

# Direct pytest (uses pytest.ini config)
.venv\Scripts\python.exe -m pytest
```

### Test Organization
```
tests/
├── unit/                     # Fast, isolated tests
│   ├── test_dialogue_system.py
│   ├── test_enemy_ai.py
│   └── ...
├── integration/              # Full system tests
│   ├── test_combat_scenarios.py
│   ├── test_level_generation.py
│   └── ...
└── fixtures/                 # Reusable test data
    ├── combat_fixtures.py
    ├── enemy_fixtures.py
    └── ...
```

### Testing Best Practices
- **Update tests with code changes** - Always!
- **Use fixtures** - Don't duplicate test setup
- **Integration over mocks** - Test real behavior
- **Run full suite before commits** - `python test_commands.py full`

---

## 🔨 Building Executables

The game uses a sophisticated build system with two build types.

### Alpha Build (For Playtesters)
```bash
cd build
build.bat alpha  # or just: build.bat
```
- Includes DEBUG logging
- Creates `game_debug.log` for bug reports
- Perfect for sending to playtesters

### Release Build (For Public Release)
```bash
cd build
build.bat release
```
- Minimal WARNING-level logging only
- Creates `game_errors.log` (errors only)
- Optimized for end users

### Build Output
```
dist/                         # Complete distribution
├── RogueSignalProtocol.exe   # Main executable
├── README.txt                # End-user instructions
├── build_info.txt            # Build type and date
├── debug_mode.flag           # Present in alpha builds
├── game_content.json         # All JSON configs
├── graphics/                 # All sprites
├── sound/                    # All SFX
└── music/                    # All music

releases/                     # Timestamped archives
└── RogueSignalProtocol_Alpha_2025-01-15_143022.zip
```

### Build Documentation
- **build/BUILD_GUIDE.md** - Complete build instructions
- **build/BUILD_TYPES.md** - Logging system documentation
- **build/FINAL_BUILD_STATUS.md** - Build system status

---

## 🎨 Modding & Configuration

All game content is JSON-driven and easily moddable!

### Configuration Files

#### game_content.json
Defines all items, exploits, and loot:
```json
{
  "exploits": {
    "buffer_overflow": {
      "name": "Buffer Overflow",
      "category": "combat",
      "base_damage": 35,
      "heat_cost": 25,
      "ram_cost": 1,
      "targeting": "single",
      "description": "Overload target with malicious data..."
    }
  },
  "code_hacks": { ... },
  "loot_tables": { ... }
}
```

#### game_rules.json
Defines balance, colors, gameplay rules:
```json
{
  "gameplay": {
    "default_player_cpu": 100,
    "max_heat": 100,
    "trace_increase_amount": 1
  },
  "colors": {
    "basic": { "cyan": [20, 255, 200] },
    "data_codes": {
      "crimson": [255, 20, 80],
      "azure": [0, 200, 255]
    }
  }
}
```

#### graphics_tiles.json
Maps entities to sprite variants:
```json
{
  "player": {
    "variants": ["player01.png", "player02.png", ...]
  },
  "enemies": {
    "scanner": ["scanner01.png", "scanner02.png", ...]
  }
}
```

### What You Can Mod (JSON Only - No Code)

**Modify existing exploits:**
- Change damage, heat cost, RAM cost
- Update descriptions and colors
- Adjust range and targeting

**Change game balance:**
- Edit `game_rules.json` values (player HP, heat limits, etc.)
- No code changes needed!

**Add/modify sprites:**
- Create PNG files in `graphics/`
- Update `graphics_tiles.json` with new variants
- Restart game to see changes

**Modify story:**
- Edit `story_content.json`
- Add/edit fragments
- Changes appear immediately

**Adjust colors:**
- Edit `game_rules.json` color definitions
- All UI colors are JSON-driven

**Tweak enemy stats:**
- Edit `game_content.json` enemy definitions
- Change HP, damage, vision range

### What Requires Code Changes

**Add NEW exploits:**
- ❌ Cannot just add to JSON
- Requires code in `game_combat.py`:
  1. Add to `game_content.json` (stats/description)
  2. Add case in `_execute_specific_exploit()`
  3. Implement `_execute_your_exploit()` method
  4. Add sound file (optional)
  5. Update help screens if needed

**Add NEW enemy behaviors:**
- ❌ Cannot just add to JSON
- Requires code in `game_enemies.py`

**Add NEW mechanics:**
- ❌ Always requires code
- Example: New status effects, new tile types, new systems

---

## 🏗️ Code Architecture

### Module Organization

**Core Systems:**
- `game_loop.py` - Main game loop and rendering coordination
- `game_engine.py` - Turn processing and game state
- `game_session.py` - Session management and level progression

**Rendering:**
- `game_rendering_core.py` - Base rendering system
- `game_rendering_graphics.py` - Graphics mode with sprites
- `game_rendering_glyphs.py` - ASCII/glyph mode
- `game_rendering_ui.py` - UI elements and panels

**Game Logic:**
- `game_combat.py` - Exploit system and damage calculation
- `game_enemies.py` - Enemy AI and behavior management
- `game_characters.py` - Player and Enemy entities
- `game_level.py` - Level generation and management

**Data & Config:**
- `data_loading.py` - JSON loading and validation
- `game_config.py` - Configuration management
- `game_entities.py` - Core entity definitions and enums

**UI Systems:**
- `game_menus.py` - Main menu, settings, etc.
- `game_dialogue_system.py` - Dialogue boxes and prompts
- `game_input.py` - Input handling and key mapping

### Important Design Patterns

**JSON-Driven Configuration:**
```python
# All config loaded from JSON - no hardcoded values!
GameConfig.load_config()  # Loads game_rules.json
GameData.load_data()      # Loads game_content.json
```

**Component System:**
```python
class Enemy:
    def __init__(self):
        self.position = Position(x, y)
        self.state = EnemyState.UNAWARE
        self.movement_queue = []  # Predictable AI
```

**Message Log Pattern:**
```python
# Game events go to message log, not print()
message_log.add_message("Enemy detected!", Colors.RED)
```

---

## ⚠️ TCOD Gotchas & Important Notes

### Coordinate System Nightmare

**🚨 CRITICAL: TCOD uses (x, y) for functions but [y, x] for arrays!**

```python
# ✓ CORRECT - use helpers
from game_coordinate_helpers import CoordinateHelpers
CoordinateHelpers.set_alpha_region(console, x=10, y=5, width=30, height=15, alpha=255)

# ✓ CORRECT - TCOD functions use (x, y)
console.print(x=10, y=5, string="Hello")

# ✗ WRONG - direct array access
console.rgba["bg"][x, y, 3] = 255  # BUG! Should be [y, x]!
```

**Always use CoordinateHelpers for array access!**

### See .claude/TCOD_GUIDE.md for complete details:
- Coordinate system rules
- Graphics rendering
- Console vs SDL pixels
- Common pitfalls

### Graphics Coordinate Systems

**Three separate coordinate systems:**
1. **Console chars (80x50)** - Text rendering
2. **Game viewport (27x21)** - In-game tiles
3. **SDL pixels (window size)** - Direct sprite rendering

**Don't mix them!** See TCOD_GUIDE.md for conversion formulas.

---

## 🎮 Development Workflow

### Running from Source
```bash
# Activate venv
.venv\Scripts\activate

# Run game
python RogueSignalProtocol.py

# Enable debug logging (create flag file)
echo > debug_mode.flag
python RogueSignalProtocol.py

# Run tests before committing
python test_commands.py full
```

### Development Cycle
1. **Make changes** to code or JSON
2. **Test immediately** with `python test_commands.py quick`
3. **Run from source** to verify behavior
4. **Update tests** if you changed APIs
5. **Full test suite** before commit: `python test_commands.py full`
6. **Build alpha** to test exe: `cd build && build.bat alpha`

### Debugging Tips
- **Create debug_mode.flag** for verbose logging
- **Check game_debug.log** after crashes
- **Use logging.debug()** liberally in code
- **Integration tests** catch more bugs than unit tests
- **Test with built exe** - some issues only appear there!

### Common Development Tasks

**Modify existing exploit balance:**
1. Edit `game_content.json` (damage, heat cost, etc.)
2. Run from source to test
3. No code changes needed! ✅

**Add NEW exploit (requires code):**
1. Add to `game_content.json` (definition)
2. Edit `game_combat.py`:
   - Add case in `_execute_specific_exploit()`
   - Implement `_execute_your_exploit()` method
3. Add sound file to `sound/` (optional)
4. Update help screen in `game_menu_help_graphics.py`
5. Write integration test

**Add new enemy type (requires code):**
1. Define in `game_content.json` (stats)
2. Add sprite to `graphics/` and update `graphics_tiles.json`
3. Add AI behavior in `game_enemies.py` if special
4. Update help screen
5. Write integration test for spawning/behavior

**Modify game balance (JSON only):**
1. Edit `game_rules.json` values
2. Run from source to test
3. Update tests if expectations changed
4. No code changes needed! ✅

**Add sound effect:**
1. Add WAV file to `sound/`
2. Reference in code: `sound_manager.play_sound("new_sound")`
3. Test in-game

**Change colors (JSON only):**
1. Edit `game_rules.json` color definitions
2. Changes appear immediately ✅

---

## 📦 Asset Creation

### Graphics (Sprites)
- **Format**: PNG with transparency
- **Size**: Flexible (scaled to tile size)
- **Naming**: `entity##.png` (e.g., `player01.png`, `scanner02.png`)
- **Location**: `graphics/` folder
- **Registration**: Add to `graphics_tiles.json`

### Sound Effects
- **Format**: WAV (uncompressed)
- **Location**: `sound/` folder
- **Naming**: Descriptive (e.g., `exploit_buffer_overflow.wav`)
- **Usage**: `sound_manager.play_sound("sound_name")`

### Music
- **Format**: OGG (normalized volume)
- **Location**: `music/` folder
- **Naming**: `level#_theme.ogg` or descriptive
- **Usage**: Played automatically per level

### Font Tileset
- **File**: `terminal10x16_gs_ro.png`
- **Format**: Monospace bitmap font
- **Size**: 10x16 pixels per glyph
- **Don't modify** unless you know what you're doing!

---

## 🔧 Configuration System Details

### How Config Loading Works

1. **Fail-fast philosophy**: Missing config files = crash immediately
2. **Required files**:
   - `game_content.json` - Items, exploits, loot
   - `game_rules.json` - Balance, colors, rules
   - `story_content.json` - Narrative content
   - `graphics_tiles.json` - Sprite mappings
3. **Optional file**:
   - `user_settings.json` - User preferences (created if missing)

### Config Validation

```python
# Config files validated on load
try:
    GameConfig.load_config()
except FileNotFoundError:
    print("CRITICAL: game_rules.json missing!")
    sys.exit(1)
```

**No fallback values!** All data comes from JSON.

### User Settings

Located in `user_settings.json` (created automatically):
```json
{
  "master_volume": 0.7,
  "sfx_volume": 0.8,
  "music_volume": 0.6,
  "graphics_mode": "graphics",
  "dialogue_preferences": {
    "show_overclock_warning": true
  }
}
```

---

## 🤝 Contributing

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add/update tests** - This is critical!
5. **Run full test suite**: `python test_commands.py full`
6. **Commit changes**: `git commit -m "Add amazing feature"`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Contribution Guidelines

**Code:**
- Keep files under 2000 lines (split at ~1800)
- One purpose per module
- Unicode character set (CascadiaCode TrueType font, full box-drawing support)
- Update tests with every change
- Run full test suite before PR

**Testing:**
- All new features need tests
- Prefer integration tests over mocks
- Use `tests/fixtures/` builders
- Test edge cases and error conditions

**Configuration:**
- New content goes in JSON files when possible
- Don't hardcode values
- Document JSON schema changes
- Validate JSON files after editing

**Commits:**
- Clear, technical commit messages
- No AI attribution tags
- Keep commits focused and atomic

### Reporting Bugs

Use GitHub Issues with:
- **Description** of the bug
- **Steps to reproduce**
- **Expected vs actual behavior**
- **game_debug.log** file (if applicable)
- **System info** (Windows version, Python version)

---

## 🏛️ Project Philosophy

### Design Principles

1. **Simplicity over complexity** - Prefer simple functional code
2. **JSON-driven content** - Easy modding without code changes
3. **Fail fast** - Better to crash than silently fail
4. **ASCII-first** - Graphics are enhancement, not requirement
5. **Test everything** - Integration tests > unit tests
6. **No over-engineering** - YAGNI principle

### Performance

- **Don't worry about performance** until it's actually a problem
- No preemptive optimization
- Focus on code clarity and correctness first
- Optimize only when users report issues

### Code Style

- **Functional where possible** - Minimize state
- **Clear names** - `enemy_vision_range` not `evr`
- **Type hints** - Use them liberally
- **Docstrings** - For public APIs
- **Comments** - For "why", not "what"

---

## 📚 Additional Resources

### Documentation
- **build/BUILD_GUIDE.md** - Building executables
- **build/BUILD_TYPES.md** - Logging system
- **.claude/TCOD_GUIDE.md** - TCOD coordinate systems
- **.claude/CLAUDE.md** - Development guidelines
- **README.txt** - End-user game instructions

### External Links
- [python-tcod Documentation](https://python-tcod.readthedocs.io/)
- [Roguelike Development](https://www.reddit.com/r/roguelikedev/)
- [Project Repository](https://github.com/Dragynrain/RogueSignalProtocol)

---

## ⚖️ License & Redistribution

GPL v3 - Free and Open Source Software

**You can:**
- ✅ Use for any purpose
- ✅ Study and modify the code
- ✅ Redistribute copies
- ✅ Distribute modified versions

**You must:**
- ✅ Keep the GPL v3 license
- ✅ Make source code available
- ✅ Document your changes
- ✅ Use GPL v3 for derivative works

**This ensures the game remains free and open forever!**

## 🎨 Game Features

### Exploit System
Choose from 12 different exploits across 4 categories:

**Combat**: Buffer Overflow, Code Injection, System Crash, EMP Burst
**Stealth**: Shadow Step, Data Mimic, Noise Maker
**Utility**: Threat Scan, Network Scan, Log Wiper, Antivirus
**Special**: Memory Leak

### Procedural Generation
- **Dynamic Level Layouts**: Each run features unique room arrangements
- **Balanced Enemy Placement**: Intelligent spawn systems for fair challenge
- **Resource Distribution**: Strategic placement of upgrades and pickups

### Story Integration
Discover the dark truth through environmental storytelling:
- **Project Chimera**: Uncover the real purpose behind the "testing"
- **Dr. Aris Thorne**: Learn about the obsessed lead researcher
- **Digital Consciousness**: Explore themes of mind uploading and identity

## 🚧 Alpha Status

This is an **Alpha release** focusing on core gameplay and feedback collection.

### What's Implemented
- ✅ Complete stealth gameplay loop
- ✅ All 8 enemy types with unique behaviors
- ✅ Full exploit system with 12 abilities
- ✅ 3-level campaign with escalating difficulty
- ✅ Save/load system with permadeath
- ✅ Audio system with music and SFX
- ✅ Complete story content (20 fragments)

### Known Limitations
- Windows-focused (Linux/Mac compatibility planned)
- Terminal graphics (advanced graphics being considered beyond title screens)

## 🤝 Contributing

We welcome contributions! Please feel free to:
- Report bugs through GitHub Issues
- Suggest gameplay improvements
- Submit pull requests for bug fixes
- Share feedback on game balance

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

**GPL v3 Summary**: This software is free and open source. You can use, modify, and distribute it, but any modifications must also be released under GPL v3. This ensures the game remains free and open for everyone.

Key freedoms under GPL v3:
- ✅ Freedom to run the program for any purpose
- ✅ Freedom to study how the program works and modify it
- ✅ Freedom to redistribute copies
- ✅ Freedom to distribute modified versions

Any derivative works must also be licensed under GPL v3, ensuring the game and its derivatives remain free software forever.

## 👨‍💻 Author

**Adam Forster** ([@Dragynrain](https://github.com/Dragynrain))

## 🙏 Acknowledgments

- Built with [python-tcod](https://github.com/libtcod/python-tcod) - Excellent roguelike development library
- Inspired by classic stealth games and cyberpunk fiction
- Special thanks to the roguelike development community
