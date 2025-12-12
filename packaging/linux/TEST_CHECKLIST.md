# Linux Package Testing Checklist

Use this checklist to verify each package format before release.

## Test Environments

- [ ] Steam Deck (SteamOS - Arch-based)
- [ ] Ubuntu 22.04 LTS (VM or real hardware)
- [ ] Fedora Latest (optional, for Wayland testing)

---

## AppImage Testing

**Test on clean system (no Python installed)**

### Installation
- [ ] Download AppImage from release
- [ ] Make executable: `chmod +x RogueSignalProtocol-*.AppImage`
- [ ] Execute: `./RogueSignalProtocol-*.AppImage`

### Functionality
- [ ] Game launches without errors
- [ ] Main menu renders correctly
- [ ] Can start new game
- [ ] Gameplay works (movement, actions)

### Audio
- [ ] Sound effects play
- [ ] Music plays
- [ ] Volume controls work

### Input
- [ ] Keyboard controls work
- [ ] Mouse controls work
- [ ] Gamepad detected (if connected)
- [ ] Gamepad controls work

### Save System
- [ ] Can save game (if applicable)
- [ ] Can load save
- [ ] Settings persist between launches
- [ ] Save location correct: `~/.local/share/RogueSignalProtocol/`

### Graphics
- [ ] Fullscreen mode works
- [ ] Windowed mode works
- [ ] Resolution changes work
- [ ] No rendering glitches

### Integration
- [ ] Desktop icon appears in app menu (after running once)
- [ ] Can add to Steam as non-Steam game

---

## Flatpak Testing

### Installation
- [ ] Install from local build: `flatpak-builder --user --install build-dir com.dragynrain.roguesignalprotocol.yml`
- [ ] OR install from Flathub (after submission)
- [ ] Appears in app launcher

### Sandbox Permissions
- [ ] Display works (Wayland and/or X11)
- [ ] Audio works (PulseAudio)
- [ ] Gamepad works (device access)
- [ ] Can write save files

### Functionality
- [ ] Game launches: `flatpak run com.dragynrain.roguesignalprotocol`
- [ ] Main menu renders
- [ ] Gameplay works

### Audio
- [ ] Sound effects play
- [ ] Music plays
- [ ] Volume controls work

### Input
- [ ] Keyboard controls work
- [ ] Mouse controls work
- [ ] Gamepad works

### Save System
- [ ] Save location: `~/.var/app/com.dragynrain.roguesignalprotocol/data/RogueSignalProtocol/` OR `~/.local/share/RogueSignalProtocol/`
- [ ] Settings persist

### Updates
- [ ] Can update via: `flatpak update com.dragynrain.roguesignalprotocol`

---

## AUR Package Testing

### Installation
- [ ] Install with yay: `yay -S rogue-signal-protocol-bin`
- [ ] OR install manually: `makepkg -si`
- [ ] No dependency errors

### Functionality
- [ ] Launch via command: `rogue-signal-protocol`
- [ ] Launch via desktop entry
- [ ] Game runs correctly

### Audio
- [ ] Sound effects play
- [ ] Music plays
- [ ] Volume controls work

### Input
- [ ] Keyboard controls work
- [ ] Mouse controls work
- [ ] Gamepad works

### Save System
- [ ] Save location: `~/.local/share/RogueSignalProtocol/`
- [ ] Settings persist

### Desktop Integration
- [ ] Desktop entry in app menu
- [ ] Icon displays correctly
- [ ] Launches from menu

### Uninstall
- [ ] Clean uninstall: `pacman -R rogue-signal-protocol-bin`
- [ ] No orphaned files in `/opt/rogue-signal-protocol/`

---

## Steam Deck Specific Tests

### Desktop Mode
- [ ] AppImage runs in Desktop Mode
- [ ] Flatpak installs via Discover
- [ ] Game launches from app menu
- [ ] Keyboard/mouse work (with dock)

### Gaming Mode
- [ ] Add as non-Steam game
- [ ] Launches from Steam library
- [ ] Gamepad controls work
- [ ] D-pad navigation works
- [ ] Face buttons work

### Display
- [ ] Renders at 1280x800
- [ ] Text readable at handheld distance
- [ ] UI elements properly sized

### System
- [ ] Suspend/resume works (power button)
- [ ] Battery drain reasonable (< 15W)
- [ ] No thermal throttling

---

## Common Issues to Watch For

1. **Missing libraries**: Game fails to start with "library not found"
   - Check ldd output: `ldd RogueSignalProtocol`
   - Ensure SDL2 libraries are available

2. **Audio not working**: No sound or errors
   - Check PulseAudio/Pipewire status
   - Verify SDL audio driver

3. **Gamepad not detected**: Controller not recognized
   - Check /dev/input permissions
   - Verify Flatpak has device access

4. **Save files not persisting**: Settings reset
   - Check write permissions to data directory
   - Verify platformdirs returns correct path

5. **Resolution issues**: Game too small/large
   - Check display scaling settings
   - Verify fullscreen mode

---

## Test Results Template

```
Package: [AppImage/Flatpak/AUR]
Version: X.X.X
Test Date: YYYY-MM-DD
Tester: [Name]
System: [Distro/Version]

[ ] PASS / [ ] FAIL

Issues Found:
- [Issue 1]
- [Issue 2]

Notes:
[Additional observations]
```
