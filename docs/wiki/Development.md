# Development Guide

Guide for developers, contributors, and modders.

## Development Setup

### Requirements
- Python 3.10+
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dragynrain/RogueSignalProtocol.git
   cd RogueSignalProtocol
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game**
   ```bash
   python RogueSignalProtocol.py
   ```

## Testing

### Running Tests
```bash
# Full test suite
pytest tests/

# Quick sanity check
pytest tests/ -q --tb=no | tail -20

# Re-run last failures
pytest tests/ --lf

# Single module
pytest tests/unit/test_<module>.py -v
```

### Pre-commit Hook
Tests run automatically before every commit via `.git/hooks/pre-commit`. The hook blocks commits if tests fail.

To bypass (emergencies only):
```bash
git commit --no-verify
```

### Testing Guidelines
- Update tests with code changes
- Prefer integration tests over mocks
- See `.claude/TESTING_GUIDE.md` for complete guidelines

## Building

### Build Commands
```bash
# Debug build (with debug_mode.flag)
build\build.bat alpha

# Production build
build\build.bat release
```

### Build Requirements
- 7zip installed at `C:\Program Files\7-Zip\7z.exe`
- Uses `Python -m PyInstaller` for reliability

See `.claude/BUILD_REFERENCE.md` for complete build documentation.

## Code Architecture

### Key Modules
- **RogueSignalProtocol.py** - Main entry point
- **game_engine.py** - Core game loop and state management
- **game_map.py** - Map generation and terrain
- **game_entities.py** - Player, enemies, items
- **game_input.py** - Input handling and controls
- **game_rendering.py** - Rendering system
- **game_ai.py** - Enemy AI and behaviors

### Configuration Files
All game data is loaded from JSON:
- **game_content.json** - Enemies, exploits, upgrades, networks
- **game_rules.json** - Balance values, colors, gameplay constants
- **narrative_content.json** - Story fragments and narrative
- **user_settings.json** - User preferences (only file with defaults)

### Important Guidelines
- Keep files under ~20,000 tokens
- One purpose per module
- No over-engineering or new frameworks
- Always check array bounds before access
- See `.claude/CLAUDE.md` for complete code guidelines

## Coordinate Systems

The game uses three distinct coordinate systems:
1. **Console chars** (80x50) - Text/UI
2. **Game viewport** (27x21) - In-game tiles
3. **SDL pixels** - Sprite rendering

See `.claude/TCOD_GUIDE.md` and `.claude/RENDERING_ARCHITECTURE.md` for details.

## TCOD Specifics

### Critical Rule
TCOD functions use `(x, y)` but arrays use `[y, x]`!

Always use `CoordinateHelpers` for array access and `UnifiedRenderer` for UI rendering.

See `.claude/TCOD_GUIDE.md` for complete reference.

## Modding

### JSON Configuration
All game content is data-driven and moddable via JSON files:

#### game_content.json
Define custom:
- Enemy types with stats and behaviors
- Exploits with effects and costs
- Upgrades and pickups
- Network configurations and difficulty

#### game_rules.json
Modify:
- Balance values
- Colors and visual themes
- UI layout and sizing
- Gameplay constants

### Adding Custom Content

**New Enemy Type:**
```json
"custom_enemy": {
  "symbol": "C",
  "cpu": 60,
  "vision": 5,
  "movement": "PATROL",
  "name": "Custom Enemy",
  "damage": 20,
  "description": "Your custom enemy description"
}
```

**New Exploit:**
```json
"custom_exploit": {
  "name": "Custom Exploit",
  "ram": 2,
  "heat": 25,
  "range": 4,
  "category": "combat",
  "damage": 30,
  "targeting": "SINGLE",
  "effect_radius": 0,
  "effect_duration": 0,
  "description": "Your exploit description",
  "help_summary": "Short summary"
}
```

## Contributing

### Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit pull request

### Code Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Keep commits focused and atomic

### Communication
- **Discord:** https://discord.gg/aUZgmrpU
- **GitHub Issues:** https://github.com/Dragynrain/RogueSignalProtocol/issues
- **Email:** roguesignalprotocol@gmail.com

## Asset Creation

### Graphics
- Sprites: 64x64 PNG with transparency
- Font: KreativeSquare TrueType
- Target: Windows console + TCOD graphics

### Audio
- Music: OGG format
- SFX: WAV format
- Managed via pygame.mixer

## License

MIT License - Free and Open Source Software

See LICENSE file for full details.

---

**Author:** Adam Forster ([@Dragynrain](https://github.com/Dragynrain))
**Email:** roguesignalprotocol@gmail.com
