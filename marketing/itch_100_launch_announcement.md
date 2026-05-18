# Rogue Signal Protocol 1.0

The beta is over. 1.0 ships today.

If you played the betas: same game, long polish pass, plus a new tutorial. If you didn't: keep reading.

## What's new in 1.0

### Prologue tutorial

A 5-section level that teaches the mechanics by making them necessary. No popups.

The first room has a damaged Scanner blocking the only door - 5 HP, 0 damage - and the only way through is to bump it. You figure out you can attack because the level doesn't let you not.

Each section adds one thing:

1. Bump attacks
2. Waiting for openings
3. Distance and blind spots
4. Ranged exploits
5. All four at once

Dying in the prologue doesn't delete your save. Die in the same section twice and the next attempt gets a more specific hint. Main menu shows "Tutorial [Done]" once you clear it.

### Console window is gone

Windows builds used to flash a CMD window behind the game on launch. They don't anymore. PyInstaller `console=False`, startup messages go to the log file, crashes still get full tracebacks written there.

### Pre-release bug sweep

The things that got fixed since the last beta:

- Saves write atomically now. A crash mid-save can't corrupt the file.
- Status bar was truncating text one character early.
- Dialogue clicks could underflow if you clicked outside the option list.
- Enemy pathfinding treated the player tile as blocked. It doesn't anymore.
- Prologue death handler is wrapped against unexpected state.
- A few audio paths used bare `except`. They don't anymore.
- Main menu mouse selection was off by one.
- Tutorial's starting exploit is locked so you can't equip something weird before section 1.

### Codebase reorg

The source moved from ~300 flat `game_*.py` files into a `src/rsp/` package with subpackages for `core`, `entities`, `systems`, `ui`, and a few others. If you've been modding or contributing from source, your imports will break. Contents didn't change, only locations. The dev README has the new layout.

## If you haven't played

- 3 procedurally-generated network levels, 8 enemy types, 13 exploits
- No RNG in combat or movement - only the layout is random
- Each enemy shows its next 3 planned moves on the map
- Permadeath. Save gets deleted on death.
- Stealth via blind spots, distraction, and heat management
- Graphical sprites or ASCII glyphs. Toggle in settings, plays identically.
- 47 achievements that persist across runs
- 20-level Ascension mode for post-victory difficulty
- Full gamepad support (Xbox, PlayStation, Steam Deck), rebindable
- Linux native: tarball, AppImage, AUR. Flatpak pending Flathub.
- No macOS yet.

Runs are 10-15 minutes. The first few will probably go badly.

## Downloads

- itch.io: https://dragynrain.itch.io/rogue-signal-protocol
- GitHub Releases: https://github.com/Dragynrain/RogueSignalProtocol/releases
- AUR: `yay -S rogue-signal-protocol-bin`

## Feedback

Discord, itch.io comments, GitHub issues, email - whatever works. I read all of it.

- Discord: https://discord.gg/5fykUtECqz
- GitHub Issues: https://github.com/Dragynrain/RogueSignalProtocol/issues
- Email: roguesignalprotocol@gmail.com

Bug reports, balance complaints, "this part felt unfair" - all useful. Thanks to everyone who reported things through the betas.
