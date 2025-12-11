# Keybindings

Complete keyboard and mouse control reference for Rogue Signal Protocol.

## Movement

### Keyboard Movement
You can use any of the following control schemes:

**Arrow Keys + Diagonals (laptop-friendly):**
- Up/Down/Left/Right - Cardinal directions
- Home - Northwest (up-left)
- PgUp - Northeast (up-right)
- End - Southwest (down-left)
- PgDn - Southeast (down-right)

**WASD + QE/ZC:**
- W/S - Up/Down
- A/D - Left/Right
- Q - Up-Left
- E - Up-Right
- Z - Down-Left
- C - Down-Right

**Numpad (NumLock ON):**
- 8 - Up
- 2 - Down
- 4 - Left
- 6 - Right
- 7 - Up-Left
- 9 - Up-Right
- 1 - Down-Left
- 3 - Down-Right
- 5 - Wait/rest

### Mouse Movement
- **Left-Click** on floor tiles - Move to clicked location (if valid and within range)

## Core Actions

| Key | Action | Description |
|-----|--------|-------------|
| **1-5** | Use Exploits | Activate equipped exploits directly (shown in HUD) |
| **[** / **]** | Cycle Exploits | Switch between equipped exploits (prev/next) |
| **X** | Execute Exploit | Fire currently selected exploit (use with [ ] cycling) |
| **Space** / **.** | Wait/Rest | Pass turn in place, cool down heat |
| **I** | Inventory | Open inventory to manage codes and exploits |
| **L** | Look Mode | Examine entities and terrain with cursor |
| **F** | Lore Fragments | View discovered story fragments |
| **V** | Achievements | View unlocked achievements |
| **?** | Help Menu | Complete controls reference and help |
| **ESC** | Pause Menu | Pause game and access settings |
| **Enter** | Confirm | Confirm dialogues, menu selections |

## Inventory Controls

| Key | Action | Description |
|-----|--------|-------------|
| **Up/Down** | Navigate | Scroll through items in inventory |
| **Enter** | Use/Equip/Unequip | Activate selected item, equip, or unequip exploit |
| **I** / **ESC** | Close | Exit inventory screen |

## Mouse Controls

### Universal Mouse Behavior
Consistent mouse controls across all menus and game screens:

| Action | Behavior | Scope |
|--------|----------|-------|
| **Left-Click** | Select/activate buttons, options, items | All screens |
| **Right-Click** | Go back, cancel, exit mode | All screens |
| **Mouse Wheel** | Scroll through lists and pages | All scrollable content |
| **Hover** | Highlight options, show tooltips | Interactive elements |

### In-Game Mouse Actions
- **Left-Click Floor** - Move to location (if reachable)
- **Left-Click Entity** - Enter look mode focused on entity
- **Left-Click Buttons** - Activate UI buttons and controls
- **Right-Click** - Cancel targeting, exit look mode, go back
- **Mouse Wheel** - Scroll through menus and lists

### Look Mode Mouse
When in Look Mode (L key):
- **Left-Click** - Examine clicked entity or terrain
- **Arrow Keys** / **Movement Keys** - Move cursor
- **Right-Click** / **ESC** / **L** - Exit look mode

## Gamepad Controls

Full Xbox/PlayStation controller support with context-sensitive bindings.

### Gameplay Controls

| Button | Action | Description |
|--------|--------|-------------|
| **Left Stick** | Movement | 8-directional tile movement (time-gated) |
| **D-Pad** | Movement | Alternative movement input |
| **A Button** | Wait/Rest | Pass turn in place, cool down heat |
| **B Button** | Cancel | Cancel targeting, close menus (UI consistency) |
| **X Button** | Exploit 1 | Quick-use first equipped exploit |
| **Y Button** | Inventory | Open/close inventory (toggle) |
| **LB (Left Bumper)** | Cycle Exploits | Switch to previous equipped exploit |
| **RB (Right Bumper)** | Cycle Exploits | Switch to next equipped exploit |
| **LT (Left Trigger)** | Look Mode | Enter look mode to examine entities |
| **RT (Right Trigger)** | Execute Exploit | Use currently selected exploit |
| **Right Stick** | Auto-Look Mode | Move stick to enter look mode (magnitude > 0.3) |
| **L3 (Left Stick Click)** | Lore Fragments | View discovered story fragments |
| **R3 (Right Stick Click)** | Achievements | View unlocked achievements |
| **Start** | Main Menu | Pause game and access main menu (toggle) |
| **Back/Select** | Help | Open help menu (alternative to ? key) |

### Look Mode (Gamepad)

When in Look Mode (LT trigger or right stick):
| Input | Action | Description |
|-------|--------|-------------|
| **Right Stick** | Move Cursor | 8-directional cursor movement with auto-repeat |
| **Left Stick / D-Pad** | Move Cursor | Alternative cursor movement |
| **A Button** | Examine | Inspect entity or terrain at cursor |
| **B Button** / **LT release** | Exit Look Mode | Return to normal gameplay |

### Inventory (Gamepad)

| Input | Action | Description |
|-------|--------|-------------|
| **D-Pad Up/Down** | Navigate | Scroll through inventory items |
| **A Button** | Use/Equip | Activate item or equip/unequip exploit |
| **B Button** / **Y** | Close | Exit inventory screen (toggle) |

### Menus (Gamepad)

| Input | Action | Description |
|-------|--------|-------------|
| **D-Pad Up/Down** | Navigate | Move through menu options |
| **D-Pad Left/Right** | Adjust Values | Change settings (volume, etc.) |
| **A Button** | Confirm | Select option or confirm action |
| **B Button** | Back | Return to previous menu or cancel |
| **LB/RB** | Page Navigation | Cycle through menu tabs or pages |

### Gamepad Tips

1. **Exploit cycling is visual** - Selected exploit highlighted in YELLOW on HUD
2. **Right stick auto-enters look mode** - No button press needed, just move stick
3. **Time-gated stick movement** - Brief delay between moves (prevents rapid-fire movement)
4. **Controller hotplug** - Connect/disconnect controllers anytime
5. **Bumpers mirror keyboard** - RB/LB = ] and [ keys for exploit cycling

## Settings & Menus

### Settings Menu
- **Up/Down** - Navigate options
- **Left/Right** - Adjust values (volume, colors, etc.)
- **Enter** - Toggle or confirm settings
- **ESC** - Save and exit settings

### Help Menu
- **Up/Down** / **Mouse Wheel** - Scroll through pages
- **Left/Right** - Navigate between help sections
- **ESC** / **Right-Click** - Exit help

### Achievement Menu
- **Up/Down** / **Mouse Wheel** - Scroll through achievements
- **V** / **ESC** / **Right-Click** - Exit achievements

### Fragment Viewer
- **Up/Down** / **Mouse Wheel** - Scroll through story fragments
- **F** / **ESC** / **Right-Click** - Exit fragment viewer

## Debug & Advanced

### Debug Export
- **Shift+F12** - Create debug package for bug reports
  - Exports to `debug_exports/debug_YYYY-MM-DD_HHMM.zip`
  - Includes saves, logs, metrics, system info, screenshot

### Debug Logging Control
Create/delete `debug_mode.flag` file to enable/disable verbose logging.

## Keyboard-Only Play

The game is **fully playable with keyboard only**. All mouse actions have keyboard equivalents:
- **ESC** replaces right-click (go back/cancel)
- **Arrow keys** replace mouse wheel (scrolling)
- **Enter** replaces left-click (confirm/select)
- **Movement keys** replace clicking to move

## Quick Reference

### Most Used Controls
```
Movement:        Arrow Keys + Home/End/PgUp/PgDn, WASD+QEZC, Numpad
Exploits:        1-5 (direct) or [ ] to cycle + X to execute
Wait:            Space or .
Inventory:       I
Look Mode:       L
Help:            ?
Pause:           ESC
```

### Mouse Essentials
```
Left-Click:   Select, move, activate
Right-Click:  Back, cancel, exit
Mouse Wheel:  Scroll everywhere
Hover:        Show info and tooltips
```

## Tips

1. **Right-click is universal back** - Works in all menus, modes, and dialogs
2. **Mouse wheel scrolls everywhere** - Achievements, settings, help, inventory
3. **Arrow keys always work** - Even when mouse is an option
4. **Hover for information** - Most interactive elements show tooltips
5. **ESC pauses the game** - Safe to step away at any time

## Controller Support

### Gamepad Features
- **Full Xbox/PlayStation support** - All features playable with controller
- **Context-sensitive bindings** - Same button does different things in different screens
- **Time-gated analog stick** - Movement rate-limited to prevent rapid-fire input
- **Right stick auto-look** - Automatically enters look mode when moved
- **Hotplug support** - Connect/disconnect controllers anytime
- **Visual feedback** - Selected exploit highlighted in YELLOW

### Keyboard + Gamepad Parity
- **Exploit cycling** - RB/LB (gamepad) = ] and [ (keyboard)
- **Look mode entry** - LT trigger (gamepad) = L key (keyboard)
- **Inventory** - Y button (gamepad) = I key (keyboard)
- **Main menu** - Start button (gamepad) = ESC key (keyboard)
- **All features** - Everything accessible via keyboard or gamepad

## Accessibility

- **Keyboard-only mode** - Complete gameplay without mouse
- **Mouse-only mode** - Minimal keyboard input required
- **Gamepad-only mode** - Full playability with controller
- **Flexible controls** - Multiple input schemes (arrows/WASD/numpad/gamepad)
- **Visual feedback** - Hover highlights, controller prompts, and visual indicators
- **Clear UI** - Large, readable text and intuitive layouts

## Controller Troubleshooting

Most controllers work automatically. If yours isn't recognized:

### Steam Users (Easiest)
1. Add the game to your Steam library (non-Steam game)
2. Enable Steam Input for the game
3. Configure controller in Steam's controller settings

### Manual SDL Configuration
For controllers not in SDL's database, you can create a custom mapping:

1. **Generate mapping string**: Use [SDL2 Gamepad Tool](https://generalarcade.com/gamepadtool/)
2. **Apply mapping**: Set the `SDL_GAMECONTROLLERCONFIG` environment variable to your mapping string
3. **Community mappings**: Check [SDL_GameControllerDB](https://github.com/mdqinc/SDL_GameControllerDB) for pre-made mappings

### Supported Controllers (Automatic)
- Xbox 360, Xbox One, Xbox Series controllers
- PlayStation 4, PlayStation 5 controllers (may need DS4Windows without Steam)
- Nintendo Switch Pro Controller
- Most USB gamepads from major brands (Logitech, 8BitDo, etc.)
