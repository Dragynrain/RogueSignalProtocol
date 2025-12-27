# Rogue Signal Protocol 0.9.0 Beta - Linux, Gamepad, Steam Deck

The cyberpunk roguelike now runs on Linux and supports gamepads.

This is a beta. I'm looking for feedback before 1.0.

## What's New

### Linux Support

Three ways to play:

- **AppImage** - Download, `chmod +x`, run. Works on any distro.
- **Flatpak** - Available on Flathub beta channel
- **AUR** - `rogue-signal-protocol-bin` for Arch users

### Gamepad Support

Xbox and PlayStation controllers tested. Most other gamepads should work - SDL handles the mapping.

- D-pad or left stick for movement
- Right stick enters look mode and moves the cursor
- Shoulder buttons cycle through your equipped exploits
- Triggers fire them
- Hotplug works - connect or disconnect controllers whenever

### Control Remapping

Both keyboard and gamepad bindings are now customizable:

- Rebind any key or button
- Bind multiple inputs to the same action
- Conflict warnings if you double-bind something
- Settings saved between sessions

### Steam Deck

This is where it all comes together. Linux build plus gamepad support means the game runs natively on Steam Deck - no Proton, no compatibility layers, no fiddling.

The gamepad controls were designed with Steam Deck in mind. Movement feels right on the sticks, the shoulder buttons make exploit cycling fast, and the screen size works well with the tile graphics.

If you have a Steam Deck and try this, please let me know how it runs. I'd love to see it.

To install via Flatpak:

```
flatpak remote-add --if-not-exists flathub-beta https://flathub.org/beta-repo/flathub-beta.flatpakrepo
flatpak install flathub-beta com.dragynrain.roguesignalprotocol
```

### 22 New Achievements (47 Total)

More goals to chase. Early-game achievements give new players direction. Ascension achievements for the masochists. Combat streaks, stealth challenges, speedrun targets.

### Ascension Modes

Beat the game? Ascension gives you 20 levels of increasing difficulty. Each level stacks a new modifier on top of all previous ones:

- Enemies gain HP, damage, and vision range
- Trace accumulates faster
- Fewer blind spots, smaller rooms, less cover
- Reduced starting RAM
- Fewer upgrades and data nodes per floor

The modifiers stack. By high ascension levels, every move matters.

### Bugfixes

Various crashes fixed, error handling improved, help screens updated.

## Feedback Wanted

This is a beta release. I need to know what's broken, what's frustrating, and what's working.

**Feedback form:** https://forms.gle/jbwGdn8VGPa6NG9p9

What I'm most interested in:

1. Does it run? Any crashes or missing libraries?
2. Gamepad feel - is the movement timing right? Any stick drift problems?
3. Balance - what killed you unfairly? What felt too easy?
4. General impressions

Discord comments, itch.io comments, GitHub issues - whatever works for you. I read everything.
