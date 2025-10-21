===============================================================================
ROGUE SIGNAL PROTOCOL - Alpha 0.8.0
===============================================================================

A coffee break stealth roguelike - Infiltrate corporate networks in quick
10-15 minute runs, evade AI security, and uncover the dark conspiracy of
Project Chimera.

-------------------------------------------------------------------------------
HOW TO PLAY
-------------------------------------------------------------------------------

1. Extract this zip to any folder
2. Run RogueSignalProtocol.exe
3. Press ? in-game for help

-------------------------------------------------------------------------------
CONTROLS
-------------------------------------------------------------------------------

MOVEMENT:
  Arrow Keys / WASD / Numpad      Move your character
  Space / Period / Numpad 5       Wait one turn

EXPLOITS:
  1-5                             Use equipped exploits

MENUS:
  I                               Inventory (equip/unequip exploits, use codes)
  L                               Look mode (examine entities and terrain)
  F                               Fragments (view discovered story lore)
  ?                               Help (detailed info on enemies and mechanics)
  ESC                             Pause menu / Back

-------------------------------------------------------------------------------
OBJECTIVE
-------------------------------------------------------------------------------

Navigate through 3 increasingly dangerous corporate networks. Reach the
gateway (>) on each level to progress. Discover 21 story fragments revealing
the truth behind the Omni-Lyra Cognitive Resilience Initiative.

Use stealth over combat - hide in shadows (*) to avoid detection. High
detection levels spawn the Admin Avatar, a powerful enemy that hunts you
relentlessly.

-------------------------------------------------------------------------------
CORE MECHANICS
-------------------------------------------------------------------------------

STEALTH:    Hide in shadows to avoid enemy vision cones
HEAT:       Exploit usage generates heat - overheating damages you
DETECTION:  High trace levels spawn the Admin Avatar boss
RESOURCES:  CPU (health), RAM (exploit capacity), Heat (cooling)

-------------------------------------------------------------------------------
IMPORTANT
-------------------------------------------------------------------------------

* This game has PERMADEATH - save files delete on death
* Story fragments persist between runs (keep discovering lore)
* Each run takes approximately 10-15 minutes (perfect coffee break game!)
* Stealth and heat management are key to survival

-------------------------------------------------------------------------------
ENEMIES
-------------------------------------------------------------------------------

S = Scanner      (35 HP, vision 4, static guard)
P = Patrol       (40 HP, vision 4, follows patrol routes, 15 damage)
B = Bot          (25 HP, vision 3, random movement, 8 damage)
F = Firewall     (80 HP, vision 5, static guardian)
H = Hunter       (50 HP, vision 6, seeks player, 22 damage)
V = Virus        (35 HP, vision 4, applies virus status)
I = Inhibitor    (30 HP, vision 4, slows movement, 5 damage)
A = Admin Avatar (250 HP, vision 8, perfect tracking, 45 damage)

-------------------------------------------------------------------------------
SYSTEM REQUIREMENTS
-------------------------------------------------------------------------------

* Windows 10 or later
* 4 GB RAM minimum
* Sound card for audio (optional)

-------------------------------------------------------------------------------
TROUBLESHOOTING
-------------------------------------------------------------------------------

WINDOWS SMARTSCREEN WARNING (VERY COMMON):
When you first run the .exe, Windows will show:
"Windows protected your PC"

This is NORMAL for new, unsigned applications.
The game is safe - this happens because it's not code-signed.

To run the game:
1. Click "More info"
2. Click "Run anyway"

You only need to do this ONCE.

ANTIVIRUS FALSE POSITIVES (COMMON):
Some antivirus software may flag the .exe as suspicious.
This is a false positive - the game is safe.

If your antivirus blocks it:
- Add the game folder to your antivirus exclusions
- Temporarily disable real-time protection while running

If the game won't start:
- Make sure all folders and files are present
- Run as Administrator if needed
- Check Windows Event Viewer for specific errors

If graphics don't load:
- Verify the graphics/ folder is in the same location as the .exe
- Check that graphics_tiles.json is present

If sound doesn't work:
- Verify the sound/ and music/ folders are present
- Check Windows audio settings

ALPHA TESTERS - SENDING BUG REPORTS:
If you encounter a crash or bug, please send us:
1. The game_debug.log file (created next to the .exe)
2. A description of what you were doing when it happened
3. Your system info (Windows version, RAM, graphics card)

The debug log contains detailed information that helps us fix bugs!

-------------------------------------------------------------------------------
GAME FILES
-------------------------------------------------------------------------------

DO NOT DELETE these files or folders:
- graphics/       (sprite graphics)
- sound/          (sound effects)
- music/          (background music)
- game_content.json
- game_rules.json
- graphics_tiles.json
- story_content.json
- terminal10x16_gs_ro.png

SAFE TO DELETE (regenerated automatically):
- user_settings.json    (resets your settings)
- rogue_signal_save.json (deletes your save)
- game_debug.log        (debug log - alpha builds only)
- game_errors.log       (error log - release builds only)

ADVANCED - LOGGING CONTROL:
- debug_mode.flag       (if present, enables verbose debug logging)
                        (alpha builds include this, release builds don't)
                        (delete to reduce logging, create to enable it)

-------------------------------------------------------------------------------
FEEDBACK
-------------------------------------------------------------------------------

Found a bug? Have suggestions? We want to hear from you!

Report issues at:
  https://github.com/Dragynrain/RogueSignalProtocol/issues

This is an active alpha release - your feedback shapes development.

-------------------------------------------------------------------------------
LICENSE
-------------------------------------------------------------------------------

GPL v3 (Free and Open Source Software)
See LICENSE file for full details.

Copyright (C) 2025 Adam Forster

===============================================================================
