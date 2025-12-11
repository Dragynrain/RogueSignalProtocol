# Changelog

All notable changes to Rogue Signal Protocol will be documented in this file.

## [Unreleased] - Gamepad Support Release

### Added

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
- Updated `docs/wiki/Keybindings.md` with full gamepad reference
- Updated `game_help_content.py` with gamepad controls
- Updated README files with gamepad support mention
- Implementation plan preserved in `PLAN_GAMEPAD.md` (historical reference)

### Files Added (11 new files)
- `game_input_actions.py`
- `game_input_analog.py`
- `game_input_base.py`
- `game_input_device_tracker.py`
- `game_input_gamepad.py`
- `game_menu_controls.py`
- `game_help_hints.py`
- `default_bindings.json`
- `tests/integration/input_test_utils.py`
- 50+ new test files for gamepad functionality

### Files Modified (60+ files)
Major changes to input handling, menu system, game loop, and rendering.
See git diff for complete list.
