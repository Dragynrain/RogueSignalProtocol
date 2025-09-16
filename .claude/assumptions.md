# Claude Code Assumptions & Guidelines

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
- **Warnings**: Only show when actually necessary (e.g., save exists and would be deleted)
- **Feedback**: Provide clear visual/audio feedback for important game events