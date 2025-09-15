# RogueSignalProtocol - Key Assumptions

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
- **TCOD 19.x cannot render pixels to text consoles** - use draw_semigraphics for image display
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