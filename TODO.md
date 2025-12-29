# Technical Debt & Future Improvements

## High Priority

### Centralize Version String
Currently version is hardcoded in 21+ locations across Python, JSON, and Markdown files. This makes releases error-prone.

**Proposed solution:**
- Add `"version": "X.Y.Z"` to `game_rules.json` (already exists)
- Create `game_version.py` that loads version from JSON at startup
- All Python files import from `game_version.py`
- Build script reads version from JSON and updates docs/packaging files automatically
- Single source of truth eliminates manual updates

**Files currently requiring manual version updates:**
- game_menu_about.py (2 locations)
- game_menu_main.py
- game_save.py
- game_story.py
- game_rules.json (3 locations)
- game_content.json (2 locations)
- narrative_content.json
- README.txt, README.md, README_DEV.md
- .github/ISSUE_TEMPLATE/bug_report.md
- docs/wiki/Home.md
- packaging/linux/* (4 files)
- CHANGELOG.md

**Effort:** Medium - mostly refactoring imports and build script updates
