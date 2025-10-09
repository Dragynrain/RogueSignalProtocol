# Claude Code Instructions & Guidelines

## Bash Command Guidelines
- **Quotes**: ALWAYS use quotes around file paths with spaces: `cd "path with spaces"` not `cd path with spaces`
- **Windows vs Unix Commands**: Use proper bash commands - `rm` not `del`, `ls` not `dir`
- **File Operations**: Use `rm` for deletion, `ls` for listing, `mkdir` for directories

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

## Test-Driven Development & Quality Assurance (CRITICAL)
- **ALWAYS update tests during refactoring** - API changes MUST be reflected in tests immediately
- **Test Synchronization**: When changing function signatures, object attributes, or return formats, update ALL related tests in the same commit
- **Integration over Unit Tests**: Prefer integration tests that test real game behavior over heavily mocked unit tests
- **Test Real Behavior**: Write tests that verify actual game functionality, not mock interactions
- **Use Test Builders**: Leverage existing test builders and factories in `tests/fixtures/` for consistent, readable test setup
- **Avoid Over-Mocking**: If a test has more mocks than real objects, consider if it's testing the right thing
- **Post-Refactor Verification**: After any refactoring, run full test suite and fix ALL broken tests before considering the refactor complete

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
- **Alert Timer Must Always Be 1**: The enemy alert_timer is intentionally set to 1 turn. Never increase it to 2 or higher as a "fix" for any problem - it's designed to be 1 turn exactly

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

## Error Handling and Debugging (CRITICAL)
- **ALWAYS use detailed error handling that logs to console AND logging functions**
- Never suppress errors or use silent logging.warning() - use `print()` + `logging` together
- Include specific error details, exception messages, and context in error reports
- When error handling disables systems, clearly communicate this to the user via console output
- **MANDATORY error reporting pattern**:
- Use good error reporting patterns to always give proper files and line numbers and exception.

### Configuration Error Handling (CRITICAL)
- **NO FALLBACK DATA** - Missing configuration must cause immediate failure
- **NO SILENT FAILURES** - Configuration errors must be immediately visible to users
- **FAIL FAST** - Raise exceptions immediately when required JSON files or sections are missing
- **Detailed Context** - Always print available keys/sections when reporting missing ones
- **Configuration files are NOT optional** - game_data.json, game_config.json, story_content.json are required
- **User settings fallback is acceptable** - Only user_settings.json may use defaults for first-run scenarios
- **NO FALLBACK VALUES IN CODE** - Never define fallback class attributes for config values. If a value is missing from JSON, the game should crash with a clear error, not silently use wrong data. This applies to ALL balance values, game constants, and configuration data.
- **ALL VALUES FROM JSON** - Code hack effects, exploit costs, balance values, etc. must ALL load from JSON with no hardcoded fallbacks

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

#### Before Committing
- Ensure all tests pass: `python test_commands.py full`
- Check that new code has corresponding tests

### Research Protocol
- Check latest official documentation first
- Verify API availability in current version

## Refactoring Guidelines
- **DO NOT over-engineer solutions or turn this into an enterprise software product**
- Do not add new features, frameworks, or architectural patterns unless explicitly asked
- Keep solutions simple and maintain the game's original functionality
- Prioritize readability and simplicity over complex design patterns
- When refactoring, extract and reorganize existing code rather than creating parallel systems

## Build and Distribution
- **KEEP build/ and dist/ folders** - These contain packaged game distributions for public releases
- build/ contains PyInstaller build artifacts and executable files
- dist/ contains final distribution packages (.exe, .zip files)
- These folders are essential for game deployment and should not be deleted

## Git Commit Guidelines
- **NEVER use Co-Authored-By**: Do not include "Co-Authored-By: Claude <noreply@anthropic.com>" in commit messages
- **NEVER use Claude Code attribution**: Do not include "🤖 Generated with [Claude Code](https://claude.ai/code)" in commit messages
- Keep commit messages clean and focused on the technical changes made