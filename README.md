# Rogue Signal Protocol - Enhanced Edition

A stealth-focused cyberpunk roguelike built with Python and TCOD.

## Development Setup

### Prerequisites
- Python 3.10+
- Virtual environment (`.venv`)

### Running the Game
```bash
# Always use the virtual environment Python
.venv/Scripts/python.exe RogueSignalProtocol.py

# NOT this (uses system Python without pygame):
python RogueSignalProtocol.py
```

### Dependencies
- **python-tcod 19.4.0+** (latest version for SDL functions)
- **pygame 2.6.1+** (for audio support)

## Development Conventions

### Symbol Standards
- **Letters (A-Z)**: Reserved exclusively for enemies (S=Scanner, P=Patrol, etc.)
- **ASCII Symbols**: Used for all other game elements (walls, items, terrain)
- **NO Unicode**: Terminal compatibility requires ASCII-only symbols

### Code Standards
- Use TCOD built-in functions (A* pathfinding, etc.) instead of manual implementations
- Follow existing functional patterns, avoid complex OOP
- Use proper logging instead of print statements
- Test all changes with virtual environment Python

### Game Mechanics
- **Stealth-focused**: Enemies immediately alert nearby allies when spotting player
- **Permadeath**: Save deleted on death (no warning dialog in this case)
- **ASCII Graphics**: All symbols must render correctly in standard terminals

## File Structure
```
.claude/                    # Claude Code configuration
├── assumptions.md          # Persistent development assumptions
└── development-checklist.md # Pre-flight checks

RogueSignalProtocol.py     # Main game file (~6000 lines)
.venv/                     # Python virtual environment
```

## Important Notes
- **Always reference latest TCOD docs** - API capabilities change between versions
- **Virtual environment required** - pygame/tcod won't work with system Python
- **ASCII symbols only** - unicode characters cause display issues in terminals