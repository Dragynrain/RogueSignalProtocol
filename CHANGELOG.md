# Changelog

All notable changes to Rogue Signal Protocol will be documented in this file.

## [1.0.0] - 2026-06-01 - Official Release

### Added

#### Prologue Tutorial
- **5-section hand-designed level** on a 28x24 fixed layout. Doors gate progression so each section is encountered in order.
- **Section 1 - Melee:** Damaged Scanner (5 HP, 0 damage) blocks the only door. Bumping it is the only way out.
- **Section 2 - Timing:** Patrol oscillates on a fixed route. Wait for the opening.
- **Section 3 - FOV:** Scanner with blind spots adjacent. Distance and cover.
- **Section 4 - Ranged:** Patrol behind a wall with a Code Injection pickup. Some fights need exploits.
- **Section 5:** Timing puzzle with a ghost node and stepping blind spots. Combines all four.
- **Reactive thought system** - 24 internal thoughts triggered by what the player just did
- **Section-specific death hints** that get more direct with repeated deaths in the same section
- **No permadeath in tutorial** - dying does not delete the save
- **"Tutorial [Done]" indicator** on the main menu after completion
- **Completion line:** "The real networks won't be this forgiving..."
- Player vision (15) exceeds enemy vision (4-5) so full patrol routes are visible

#### Menu Improvements
- **Tutorial and Controls options** now respond to mouse clicks in main menu

### Changed
- **Codebase reorganized into `src/rsp/` package** - flat `game_*.py` modules consolidated into namespaced subpackages (`core`, `entities`, `systems`, `ui`, `level`, `input`, `combat`); 331 files moved, ~2400 net lines removed
- **Console window hidden** - Game no longer shows a CMD window on Windows (PyInstaller `console=False`)
- **Debug export hidden from UI** - Shift+F12 still works as undocumented shortcut for bug reports
- **Build system defaults to release** - `build.bat` and GitHub Actions now default to release builds
- **Crash tracebacks logged to file** - `traceback.print_exc()` replaced with `logging.error()` for windowless operation
- **Startup diagnostics moved to logging** - print statements replaced with logging.info after logging init

### Fixed

#### Save System
- **Atomic save writes** - `shutil.move` replaced with `os.replace` so a crash mid-save can't leave a partial file
- **Save version logged on load** - version string from the save file is checked against the game's version, mismatch logs a warning instead of failing silently
- **Persistence warnings** - dropped items and dropped coordinates during save/load now log warnings instead of being silently discarded

#### Pathfinding
- **Enemy pathfinding no longer blocks on player position** - player removed from cost map so enemies can path toward player

#### Input
- **Main menu mouse click off-by-one** - mouse now selects correct menu option
- **Tutorial starting exploit locked** - prevents equipping unintended exploits at tutorial start
- **Dialogue click lower-bound check** - prevents negative `option_index` when clicking outside the option list

#### Combat / Death
- **Player attack tracking initialized in `__init__`** - removed `hasattr` guards on combat metric attributes
- **Prologue death state wrapped in try/except** - tutorial death handler survives unexpected state errors
- **Fallback `check_death` no longer runs every turn** - moved inside its conditional path

#### UI
- **Status bar off-by-one** - text was being truncated one character early
- **Redundant `hasattr`/`getattr` in status bar blind-spot check** - consolidated
- **Always-true condition removed from lore menu click handler**

#### Audio
- **Narrowed exception handling** - bare `except Exception` catches replaced with specific types

#### Testing
- **Session ID collision in parallel tests** - fixed race condition in test fixtures
- **Replaced time.sleep with mock_time** - deterministic test timing, no flaky sleeps
- Removed flaky performance tests

### Technical
- **`validate-release.py` Unicode-logging check** - now passes `--no-cov` so the project's 70% coverage threshold doesn't false-fail on single-file runs
- **GitHub workflow `build_info.txt`** - now reflects the actual `build_type` and log level instead of hardcoded "Alpha (GitHub Actions)" / "DEBUG"

### Removed
- Beta build notice from README.txt
- Feedback survey links from README.md and marketing pages
- Debug export button from Settings menu
- Shift+F12 reference from help text
- Console window references from troubleshooting docs
- All beta-specific language from code and documentation

### Files Added
- `src/rsp/systems/prologue_thoughts.py` - Reactive tutorial hint system (24 triggers)
- `src/rsp/level/fixed_levels.py` - Hand-designed prologue level layout
- Tutorial-specific tests for level generation, thought triggers, and death handling

### Files Modified
- `src/rsp/core/engine.py` - Prologue mode initialization, death tracking, thought validation
- `src/rsp/systems/death.py` - Prologue-specific death handling with escalating hints
- `src/rsp/ui/menu_main.py` - Tutorial menu option with completion indicator
- `src/rsp/ui/menu_settings.py` - Removed debug export UI (~200 lines)
- `src/rsp/core/loop.py` - Removed dead export handler, fixed traceback logging
- `RogueSignalProtocol.py` - Removed print statements, console-free startup
- `RogueSignalProtocol.spec` / `RogueSignalProtocol-linux.spec` - `console=False`
- `narrative_content.json` - Prologue thoughts and section-specific death hints
- `.github/workflows/release.yml` - Default build type changed to release

---

## [0.9.2 Beta] - 2025-12-30 - Bug Fixes & Code Quality

### Fixed

#### Gameplay
- **Combat death check now triggers immediately** - explicit check_death after damage ensures enemies die correctly
- **Dialogue hover logic fixed for 3+ options** - hover states now work correctly in dialogues with many choices

#### Audio
- **Audio cooldown now recorded after validation** - fixes timing issue where cooldown was set before confirming sound played

#### Configuration
- **Deep copy for nested config dicts** - prevents mutations from affecting shared config state
- **Max CPU attribute error resolved** - fixed AttributeError in character initialization

#### Input
- **Modal input signature mismatch fixed** - corrected method parameters in game_input_modals.py

#### UI
- **Achievement popup alpha fade now applied** - visual fade effect works correctly

### Technical
- Centralized version management via bump-version.py
- Improved build automation and release process
- Removed dead code branches and unused variables
- Fixed misleading docstrings (single-pass/two-pass terminology)
- Enhanced release checklist with fast path and verification steps

---

## [0.9.1 Beta] - 2025-12-29 - Steam Deck Controller Fixes

### Fixed

#### Gamepad/Controller Support
- **Victory screen now responds to gamepad input** - removed keyboard-only handler, now uses unified input system
- **Ascension unlock popup now responds to gamepad input** - same fix pattern
- **Settings confirmation dialogs now work with gamepad** - action-based flow replaces keyboard-only handling
- **Added WAIT action to victory/unlock screens** - SPACE key and A button both dismiss popups

#### Debug Export
- **Debug export path now displays clearly** - shown on separate line with truncation for long paths
- **Export path persists in settings menu** - path remains visible until leaving menu

#### Input System
- **Unified input handling** - removed redundant handle_input overrides across victory, ascension, and settings screens
- **Added Shift+F12 binding** - DEBUG_EXPORT action now in default_bindings.json

### Technical Details
- Files modified: game_victory_screen.py, game_menu_ascension.py, game_menu_settings.py, game_input_gameplay.py, game_loop.py, default_bindings.json
- Added gamepad tests for victory screen and ascension unlock screen
- This is a hotfix release targeting Steam Deck and controller users

---

## [0.9.0 Beta] - 2025-12-27 - Gamepad, Ascension & Steam Deck Release

### Added

#### Ascension System
- **20-level post-game difficulty scaling** unlocked after first victory
- **Stacking modifiers** - each level adds a new challenge while keeping all previous ones
- **In-game viewer** - press N to view current modifiers and adjust Ascension level
- **Unlock screen** - celebratory popup when Ascension is first unlocked
- **4 Ascension achievements** - Sensor Sweep (A5), Firewall Breaker (A10), Silent Running (A15), Ascension Master (A20)
- **JSON-configured modifiers** - all 20 levels defined in game_rules.json

#### 22 New Achievements
- **47 total achievements** across 9 categories (up from 25 in 0.8.0)
- 10 early game achievements: system_failure, victory_protocol, network_breach, payload_deployed, hack_activated, system_restore, kill_streak_5, kill_streak_10, rookie, heat_spike
- 4 ascension achievements: sensor_sweep, firewall_breaker, silent_running, ascension_master
- 6 additional combat/stealth achievements added throughout development

#### Steam Deck & Linux Support
- **Steam Deck detection** - auto-detects SteamOS and handheld mode
- **UI Scale setting** - auto/compact/normal for smaller displays
- **Music Boost setting** - auto/on/off for Linux volume balancing
- **Linux packaging** - tested on Linux Mint with dedicated build process

#### Full Gamepad/Controller Support
- **Xbox and PlayStation controller support** with context-sensitive button mappings
- **Left stick/D-pad movement** with time-based movement gating (prevents accidental rapid moves)
- **Right stick auto-look mode** - deflect right stick to instantly enter look mode and control cursor
- **Analog stick deadzone handling** with scaled radial deadzone algorithm (15% default)
- **Direction locking** prevents diagonal stick movements from registering multiple directions
- **Exploit cycling with shoulder buttons** - LB/RB cycle through equipped exploits, RT fires selected
- **Controller hotplug support** - connect/disconnect controllers during gameplay with graceful degradation
- **Visual exploit selection indicator** - yellow highlight shows which exploit RT will fire

#### New Input Abstraction Layer
- `game_input_actions.py` - InputAction and InputContext enums for unified input handling
- `game_input_mappings.py` - InputMapper class managing keyboard and gamepad bindings
- `game_input_analog.py` - AnalogStickHandler with deadzone, time-gating, and direction locking
- `game_input_gamepad.py` - GamepadInputHandler for controller event processing
- `game_input_base.py` - BaseInputHandler for shared input handling logic
- `game_input_device_tracker.py` - Controller device tracking and management

#### Custom Control Remapping
- **Full keyboard rebinding UI** in Settings > Controls > Keyboard Bindings
- **Full gamepad rebinding UI** in Settings > Controls > Gamepad Bindings
- **Gamepad settings panel** - adjust deadzone, movement threshold, direction locking
- **Conflict detection** - warns when binding conflicts with existing action
- **Multiple bindings per action** - bind W, Up Arrow, and Numpad 8 to same action
- **Reset to defaults** - restore original bindings with one button
- **Persistent bindings** - custom bindings saved to user_settings.json
- **Visual indicators** - asterisk (*) marks customized actions

#### Keyboard Exploit Cycling
- **[ and ] keys** cycle through equipped exploits (same as gamepad LB/RB)
- **X key** executes currently selected exploit (same as gamepad RT)
- Works alongside direct 1-5 slot keys for hybrid playstyle

#### Help System Updates
- **New help page (Page 4)** documenting all gamepad controls by context
- Gamepad controls organized by: Gameplay, Look Mode, Targeting, Menus
- Updated keyboard controls documentation with exploit cycling keys

#### Comprehensive Test Coverage
- 17+ new gamepad-specific test files covering:
  - Auto-repeat behavior
  - Context switching
  - Diagonal movement
  - Dual input (keyboard + gamepad)
  - End-to-end gameplay
  - Exploit cycling
  - Hotplug scenarios
  - Look mode
  - Menu navigation
  - Settings synchronization
  - Stick drift handling
  - Turn gating

### Changed

#### Input System Refactoring
- `game_input.py` - Added InputMapper integration, context detection, action execution
- `game_input_gameplay.py` - Added execute_action() method for abstract input handling
- `game_input_dialogue.py` - Full gamepad support for dialogue navigation
- `game_input_modals.py` - Gamepad support for inventory, help, lore viewer, achievements
- `game_loop.py` - SDL joystick initialization, controller event routing
- `game_engine.py` - Added selected_exploit_index and cycle_exploit_selection()
- `game_config.py` - Gamepad settings (deadzone, enabled, custom bindings)

#### Menu System Updates
- `game_menu_main.py` - Gamepad navigation support
- `game_menu_settings.py` - New Controls submenu
- `game_menu_achievements.py` - Gamepad pagination with LB/RB
- `game_menu_help_lore.py` - 4-page layout with gamepad controls
- `game_menu_help_graphics.py` - 4-page layout with gamepad controls
- `game_menu_about.py` - Gamepad navigation
- `game_menu_graphics_preview.py` - Gamepad support

#### UI Improvements
- `game_status_bar_renderer.py` - Visual exploit selection highlight
- `game_rendering_ui.py` - Updated exploit bar with selection indicator

### Technical Details

#### Gamepad Button Mapping (Default - "Option C")
**Gameplay:**
- Left Stick/D-Pad: 8-way movement
- A: Wait/pass turn
- B: Cancel (consistent across all contexts)
- X: Direct exploit slot 1
- Y: Toggle inventory
- LB: Cycle exploit backward
- RB: Cycle exploit forward
- RT: Execute selected exploit
- Start: Main menu
- Select: Help
- L3 (left stick click): Lore viewer
- R3 (right stick click): Achievements

**Look/Targeting Mode:**
- Right Stick: Auto-enter look mode + move cursor
- Left Stick/D-Pad: Move cursor
- A: Inspect/execute
- B: Exit mode

**Menus:**
- D-Pad/Left Stick: Navigate
- A: Confirm
- B: Back
- LB/RB: Page up/down

#### Analog Stick Implementation
- **Scaled radial deadzone** - removes inner dead zone while preserving outer range
- **Time-based movement gating** - 350ms initial delay, 180ms repeat rate
- **Direction locking** - first deflection locks direction until stick returns to center
- **Equal angular zones** - 45-degree wedges for consistent diagonal/cardinal input
- **Auto-repeat in menus** - separate timing for menu navigation

### Documentation
- Added `docs/wiki/Ascension-System.md` with full modifier reference
- Added `docs/wiki/Achievement-Guide.md` expanded to 47 achievements
- Updated `docs/wiki/Keybindings.md` with full gamepad reference
- Updated `game_help_content.py` with gamepad controls
- Updated README files with gamepad support and Linux instructions
- Implementation plans preserved in `PLAN_GAMEPAD.md`, `PLAN_ASCENSION.md` (historical reference)

### Files Added (14 new files)
- `game_ascension.py` - Ascension system core logic and modifiers
- `game_menu_ascension.py` - Ascension viewer UI and unlock screen
- `game_death_handler.py` - Centralized player death processing
- `game_input_actions.py` - InputAction and InputContext enums
- `game_input_analog.py` - Analog stick handling with deadzone
- `game_input_base.py` - Base input handler class
- `game_input_device_tracker.py` - Controller device management
- `game_input_gamepad.py` - Gamepad event processing
- `game_input_mappings.py` - Input binding configuration
- `game_menu_controls.py` - Control remapping UI
- `game_help_hints.py` - Context-sensitive help hints
- `default_bindings.json` - Default keyboard/gamepad bindings
- `tests/integration/input_test_utils.py` - Gamepad test utilities
- 50+ new test files for gamepad and ascension functionality

### Files Modified (60+ files)
Major changes to input handling, menu system, game loop, and rendering.
See git diff for complete list.

### Fixed

#### Save/Load & Death Handling
- Enemy save/load now correctly persists all fields
- Centralized PlayerDeathHandler prevents duplicate death processing
- Combat death no longer corrupts save state
- Fatal error handling for save operations

#### Achievement System
- Pacifist achievement now correctly tracks kills per-level (not cumulative)
- Fixed duplicate achievement metric tracking
- Consolidated metrics tracking helpers

#### Combat & AI
- Exploits now correctly clear enemy move queue on state change
- Fixed bump attack overheat damage bug
- Fixed patrol restoration after hostile transitions
- Consolidated hostile state transition logic

#### Pathfinding & Movement
- Added pathfinding bounds validation (prevents out-of-bounds crashes)
- Fixed distance comparison bug in Chebyshev calculations

#### UI & Rendering
- Fixed ascension menu mouse handling
- Fixed ascension popup text overflow with word wrap
- Fixed vision rendering edge cases
- Fixed A20 blind spot single-use behavior
- Fixed settings menu navigation wraparound

#### Configuration
- Removed hardcoded JSON fallbacks - fail-fast on missing config
- Fixed graphics mode case sensitivity check
