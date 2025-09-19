# Claude Code Instructions & Guidelines

## Running Unit Tests and Python commands
- **uv for tests**: always run tests using uv run pytest ...
- **uv for python**: always run one-off python commands (debugging, testing imports etc) using uv run python ...

## Bash Command Guidelines
- **Quotes**: ALWAYS use quotes around file paths with spaces: `cd "path with spaces"` not `cd path with spaces`
- **Windows vs Unix Commands**: Use proper Windows commands - `rm` not `del`, `ls` not `dir`
- **File Operations**: Use `rm` for deletion, `ls` for listing, `mkdir` for directories
- **Path Separators**: Use forward slashes in paths even on Windows when possible

## Project-Specific Rules
- **Symbol Conventions**: Letters (A-Z) are ONLY for enemies. Everything else must use ASCII symbols (not unicode)
- **Version References**: Always reference the LATEST version of dependencies (especially python-tcod)
- **Terminal Compatibility**: NO unicode characters - ASCII only for maximum compatibility
- **Virtual Environment**: Always use `.venv/Scripts/python.exe` for running Python scripts
- **Save File Logic**: Check if save exists before showing delete warnings

## Technical Standards
- **Code Style**: Follow existing patterns, avoid complex OOP, prefer functional approaches
- **Error Handling**: Use proper logging and always print errors to the console
- **Testing**: Always test changes with the virtual environment Python
- **Unit Test Updates**: When making code changes, ALWAYS update corresponding unit tests to maintain coverage
- **Performance**: Use TCOD's built-in functions (like A* pathfinding and vision system) instead of manual implementations

## Logging Systems (CRITICAL DISTINCTION)
- **Python Error Logging**: Technical errors, exceptions, debug info → console/stderr with line numbers using `logging.error()`, `logging.warning()`, etc.
- **In-Game System Log**: Gameplay messages like "CPU restored", "enemy detected" → right panel in game UI using `MessageLog.add_message()`
- **NEVER confuse these two systems** - they serve completely different purposes and audiences

## Research Guidelines
- **Documentation**: Always check latest docs, not outdated versions especially for TCOD
- **API Access**: Verify what's actually available in current versions before concluding limitations

## Game Design Rules
- **Enemy Behavior**: Enemies should immediately alert nearby enemies when spotting player
- **Stealth Mechanics**: Shadows (*) provide concealment, walls (#) block movement/sight  
- **Permadeath**: Save file gets deleted on death - no confirmation dialog needed in this case
- **Pathfinding**: Use TCOD's A* pathfinding for all enemy movement and prediction

## UI/UX Expectations
- **Help Text**: Must match actual in-game symbols exactly

## Enemy Movement System
- **ALL enemy movement MUST use the movement queue system**
- Enemies calculate their intended path/moves and store them in a queue
- Movement prediction shows the contents of this queue to the player
- On each turn, enemies execute the first item from their queue
- Queues are updated when targets change or paths become invalid
- This applies to ALL movement types: RANDOM, SEEK, TRACK, LINEAR

## Enemy Vision and Targeting
- If an enemy can see the player directly, that becomes their "last known location"
- Enemy alerts from other enemies are only useful if the enemy cannot currently see the player
- When an enemy becomes hostile, they should immediately pathfind to their target and populate their movement queue

## Code Clarity
- Use clear, descriptive variable names
- Add useful comments explaining the purpose of each system
- Keep systems simple and maintainable
- Avoid complex nested logic where possible

## Library Dependencies
- **ALWAYS use the latest version of python-tcod library**
- When encountering API errors, check documentation first before attempting complex fixes
- Modern TCOD uses SimpleGraph and boolean cost arrays, not numpy_array functions
- **TCOD 19.x cannot render pixels to text consoles** - use draw_semigraphics for image display which is only for small images
- Load images with tcod.image.load() for numpy arrays, use console.draw_semigraphics() for display

## Error Handling and Debugging
- **ALWAYS use detailed error handling that logs to console AND logging functions**
- Never suppress errors or use silent logging.warning() - use `print()` + `logging` together
- Include specific error details, exception messages, and context in error reports
- When error handling disables systems, clearly communicate this to the user via console output
- Example pattern:
  ```python
  error_msg = f"SYSTEM ERROR: {specific_details}"
  print(error_msg)  # Always visible to user
  logging.error(error_msg)  # Also log for debugging
  if exception:
      print(f"Exception: {str(exception)}")
  ```

## Virtual Environment Dependencies  
- **Project uses virtual environment at: `C:\Projects\RogueSignalProtocol\.venv`**
- When adding new Python modules, install them in the venv: `.venv\Scripts\pip.exe install <package>`
- **If test results differ between your execution and user execution, check venv dependencies**
- Run game using venv Python: `.venv\Scripts\python.exe RogueSignalProtocol.py`
- Missing venv packages cause ImportError exceptions that may be silently handled
- Always verify imports work in venv context when troubleshooting environment-specific issues

## Architectural Principles
- **File Size Limit**: Try to keep ALL Python files under 2000 lines
- **Module Breakdown**: When a file approaches 1800+ lines, plan breakdown into focused modules
- **Single Responsibility**: Each module should have one clear purpose
- **Separation of Concerns**: Separate rendering, game logic, data management, and UI


## Integration Patterns 
**Current Architecture Analysis:**
- **Main Script** (RogueSignalProtocol.py) imports all modules and orchestrates game flow
- **Game Engine** (game_engine.py) is the core game logic hub, imports most other modules
- **Data Flow**: config → entities → characters/enemies → engine → UI/rendering
- **Dependency Hierarchy**: 
  ```
  RogueSignalProtocol.py (main)
  ├── game_engine.py (core logic)
  ├── game_menus.py (UI)
  ├── game_characters.py (player/enemies)
  └── [other specialized modules]
  ```
- **Circular Dependency Prevention**: Use delayed imports in functions when needed
- **Module Communication**: Pass objects/references rather than importing between peer modules
- **Integration Pattern**: New modules should follow existing import hierarchy and avoid cross-dependencies

## Compatibility Requirements 
- **Primary Target**: Windows 10/11 with command prompt/PowerShell terminals
- **Rendering Modes**: 
  - ASCII mode (terminal characters only) - PRIMARY
  - Graphics mode (TCOD graphics) - SECONDARY  
  - **CRITICAL**: Any rendering changes must be implemented in BOTH modes
- **Terminal Requirements**: 
  - No Unicode characters - ASCII only for maximum compatibility
  - Standard Windows terminal color support
  - Monospace font compatibility
- **Future Considerations**: Linux/Mac support possible but Windows-first development

## Common File Locations (#14)
**Core Game Logic:**
- `RogueSignalProtocol.py` - Main game loop, renderers, UI management
- `game_engine.py` - Core game engine, turn processing, game state

**Game Systems:**
- `game_characters.py` - Player class, Enemy class, pathfinding utilities
- `game_level.py` - Level generation, room placement, special tiles
- `game_combat.py` - Exploit system, targeting, combat mechanics 
- `game_enemies.py` - Enemy manager, enemy spawning logic 

**Data & Configuration:**
- `game_config.py` - Game settings, constants, configuration management 
- `game_data.py` - Enemy definitions, exploit data, upgrade definitions 
- `game_entities.py` - Position class, enums, utility functions 
- `data_loading.py` - JSON loading, fallback data, story fragments 

**User Interface:**
- `game_menus.py` - All menu classes, menu backgrounds, help system 
- `game_ui.py` - UI rendering utilities, window management, input handling 
- `game_input.py` - Input processing, key mapping, movement handling 

**Support Systems:**
- `game_save.py` - Save/load system, game state persistence 
- `game_inventory.py` - Inventory management, item definitions 
- `game_audio.py` - Sound management, audio loading, sound effects 
- `game_map.py` - Map data structure, tile management 
- `game_story.py` - Story fragment management, lore system 

## Development Workflow Checklist

### During Development  
- Update help text if symbols change
- Use TCOD built-in functions when available
- Add proper error handling with logging

### After Changes
- Test game functionality 
- Update documentation if needed

### Research Protocol
- Check latest official documentation first
- Verify API availability in current version

## Refactoring Guidelines
- **DO NOT over-engineer solutions or turn this into an enterprise software product**
- Do not add new features, frameworks, or architectural patterns unless explicitly asked
- Keep solutions simple and maintain the game's original functionality
- Prioritize readability and simplicity over complex design patterns
- When refactoring, extract and reorganize existing code rather than creating parallel systems