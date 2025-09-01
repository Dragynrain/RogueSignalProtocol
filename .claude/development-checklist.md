# Development Checklist

## Before Making Changes
- [ ] Check if virtual environment is active (`.venv/Scripts/python.exe`)
- [ ] Verify current versions of dependencies being referenced
- [ ] Confirm symbol conventions (letters = enemies, ASCII symbols = everything else)
- [ ] Check existing code patterns to match style

## During Development  
- [ ] Test with virtual environment Python
- [ ] Follow ASCII-only rule (no unicode)
- [ ] Update help text if symbols change
- [ ] Use TCOD built-in functions when available
- [ ] Add proper error handling with logging

## After Changes
- [ ] Test game functionality 
- [ ] Verify all symbols display correctly
- [ ] Check that warnings only appear when appropriate
- [ ] Confirm enemy behavior works as expected
- [ ] Update documentation if needed

## Research Protocol
- [ ] Check latest official documentation first
- [ ] Verify API availability in current version
- [ ] Test actual functionality before concluding limitations
- [ ] Consider timing/initialization order for SDL/TCOD issues