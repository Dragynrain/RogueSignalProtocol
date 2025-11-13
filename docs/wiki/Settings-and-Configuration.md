# Settings & Configuration

Complete reference for all settings and configuration options in Rogue Signal Protocol.

## Accessing Settings

**From Main Menu:**
- Select "Settings" from main menu

**From In-Game:**
- Press **ESC** to open pause menu
- Select "Settings"

**Navigation:**
- **Up/Down** - Navigate options
- **Left/Right** - Adjust values
- **Enter** - Toggle or confirm settings
- **ESC** - Save and exit settings

---

## Audio Settings

### Master Volume
- **Range:** 0.0 - 1.0 (0% - 100%)
- **Default:** 0.7 (70%)
- **Description:** Controls overall audio output for all sounds and music
- **Effect:** Adjusts both SFX and music together

### SFX Volume
- **Range:** 0.0 - 1.0 (0% - 100%)
- **Default:** 0.75 (75%)
- **Description:** Controls sound effect volume
- **Includes:**
  - Exploit activation sounds
  - Combat hit/miss sounds
  - Item pickup sounds
  - Enemy detection alerts
  - UI interaction sounds
- **Independent:** Works separately from music volume

### Music Volume
- **Range:** 0.0 - 1.0 (0% - 100%)
- **Default:** 0.6 (60%)
- **Description:** Controls background music volume
- **Includes:**
  - Level 1: Corporate Network theme (level1_stealth.ogg)
  - Level 2: Government System theme (level2_infiltration.ogg)
  - Level 3: Military Backbone theme (level3_core.ogg)
  - Menu background music
- **Independent:** Works separately from SFX volume

**Audio Tips:**
- Set Master to 0 to mute everything instantly
- Balance SFX higher than music for gameplay clarity
- Music can be distracting during stealth - lower it for focus

---

## Graphics Settings

### Graphics Mode
- **Options:** Graphics (sprites) | Glyph (ASCII)
- **Default:** Graphics
- **Description:** Choose between sprite-based graphics or classic ASCII/Unicode characters

#### Graphics Mode (Sprites)
- **Visual Style:** Cyberspace sprites rendered as PNG images
- **Features:**
  - 64x64 sprite tiles
  - Particle effects for exploits (if enabled)
  - Smooth animations
  - Full-color sprites
- **Performance:** Slightly higher resource usage
- **Best For:** Modern aesthetic, visual clarity

#### Glyph Mode (ASCII)
- **Visual Style:** Classic roguelike ASCII/Unicode characters
- **Features:**
  - CP437 Unicode character set
  - KreativeSquare TrueType font
  - Faster rendering
  - Traditional roguelike feel
- **Performance:** Lower resource usage
- **Best For:** Classic roguelike fans, lower-end systems, performance

**Switching Modes:**
- Changes take effect immediately
- No game restart required
- Gameplay identical in both modes
- Preference is personal - try both!

### Particle Effects
- **Options:** On | Off
- **Default:** On
- **Description:** Enable/disable particle effects for exploits in graphics mode
- **Includes:**
  - Exploit activation particles
  - Combat effect particles
  - Environmental effects
- **Note:** Only affects Graphics mode, no effect in Glyph mode
- **Performance:** Disable for better FPS on slower systems

---

## UI Settings

### UI Color Theme
- **Options:** 8 color themes
- **Default:** Cyan
- **Description:** Choose UI accent color for menus, borders, and highlights

#### Color Themes

**Cyan** (Default)
- RGB: [20, 255, 200]
- Cool, tech aesthetic
- High contrast on dark backgrounds

**Purple**
- RGB: [200, 60, 255]
- Vibrant, energetic
- Popular alternative

**Magenta**
- RGB: [255, 20, 255]
- Bold, striking
- High visibility

**Golden**
- RGB: [255, 240, 0]
- Warm, classic
- Excellent readability

**Crimson**
- RGB: [255, 20, 80]
- Aggressive, intense
- Warning aesthetic

**Azure**
- RGB: [0, 200, 255]
- Bright, clean
- Calm vibe

**Emerald**
- RGB: [0, 255, 100]
- Matrix-style green
- Hacker aesthetic

**Ivory**
- RGB: [245, 245, 235]
- Subtle, elegant
- Easy on eyes

**What Colors Affect:**
- Menu borders and highlights
- Button outlines
- Selected items
- UI accents
- Status bar elements

**What Colors DON'T Affect:**
- Gameplay colors (enemies, terrain)
- Message log colors (fixed by message type)
- Health/heat/trace indicators (fixed by value)

### Achievement Popups
- **Options:** On | Off
- **Default:** On
- **Description:** Show popup notifications when achievements unlock
- **When Enabled:**
  - Popup appears at top of screen
  - Shows achievement name, icon, description
  - Fades after 3 seconds
  - Doesn't pause gameplay
- **When Disabled:**
  - Achievements still unlock silently
  - View unlocked achievements in menu (V key)
  - No interruption to gameplay flow
- **Recommendation:** Enable for first playthrough, disable for focused runs

---

## Gameplay Settings

### System Crash Warning
- **Options:** On | Off
- **Default:** On
- **Description:** Show warning dialogue before using System Crash exploit
- **Reason:** System Crash deals self-damage and can kill you
- **Warning Content:**
  - "System Crash deals damage to YOU!"
  - Confirms you want to proceed
  - Prevents accidental deaths
- **When to Disable:** Experienced players who know the risks

### Dialogue Preferences
- **Description:** Per-dialogue toggles to hide specific warnings after seeing them once
- **Format:** Individual dialogues can be disabled
- **Examples:**
  - Overclock warning
  - Tutorial tips
  - First-time help messages
- **Reset:** Delete `saves/user_settings.json` to see all dialogues again

---

## Display Settings

**Note:** Display settings are configured in `game_rules.json` and are not user-adjustable in-game. These are fixed by design.

### Fixed Display Parameters
- **Screen Size:** 80x50 characters
- **Game Viewport:** 27x21 tiles (visible play area)
- **UI Panels:** Fixed layout
- **Status Bar:** Top of screen (1 line height)
- **Message Log:** Bottom of screen (scrollable)

---

## Settings Storage

### Settings File Location
**File:** `saves/user_settings.json`

### What's Saved
All user preferences:
- Master, SFX, and music volumes
- Graphics mode (graphics or glyph)
- Particle effects toggle
- UI color theme
- Achievement popup toggle
- Dialogue preferences
- System Crash warning toggle

### When Settings Are Saved
- Immediately when changed in Settings menu
- On game exit
- Survives game crashes (last saved state restored)

### Settings Persistence
- **Survives:** Death, game uninstall (if file backed up)
- **Doesn't survive:** File deletion, save folder reset
- **Reset Settings:** Delete `saves/user_settings.json` to restore defaults

---

## Default Settings (Fresh Install)

When `user_settings.json` doesn't exist, defaults are:

```json
{
  "master_volume": 0.7,
  "sfx_volume": 0.75,
  "music_volume": 0.6,
  "graphics_mode": "graphics",
  "particle_effects": true,
  "ui_color_theme": "cyan",
  "achievement_popups": true,
  "dialogue_preferences": {},
  "system_crash_warning": true
}
```

---

## Graphics Preview Feature

### Accessing Graphics Preview
**From Settings Menu:**
- Select "Graphics Preview" option
- Available only when in Graphics mode

### Features
- **Browse All Sprites:** View all included sprite variants for each entity
- **Cycle Variants:** Switch between different visual styles for:
  - Player sprites
  - Enemy sprites (all 8 types)
  - Terrain sprites
  - Item sprites
  - UI elements
- **Live Preview:** See sprites rendered in demo environment
- **Animated Demo:** Enemies cycle through alert states (yellow → orange → red)
- **Automatic Saving:** Selected sprites saved on exit

### Preview Controls
- **Arrow Keys:** Navigate between entities
- **Enter:** Cycle to next sprite variant
- **ESC:** Exit preview (saves selections)
- **Mouse:** Click sprites to cycle variants

### Sprite Selection Export
**Location:** `logs/graphic-preview.log`
**Contents:**
- Your selected sprite variants
- Instructions for modifying `graphics_tiles.json`
- Perfect for modders wanting to customize sprites

---

## Advanced Configuration

### Modding Settings (JSON Files)

**For Modders:**
Settings beyond user options require editing JSON files:

#### game_rules.json
- Display dimensions
- Gameplay balance values
- Color definitions (non-UI)
- Balance constants
- Room generation parameters

#### game_content.json
- Enemy stats
- Exploit definitions
- Upgrade values
- Network configurations
- Loot tables

#### graphics_tiles.json
- Sprite mappings
- Entity-to-sprite associations
- Variant definitions

**Warning:** Editing JSON files can break the game if done incorrectly. Always backup before modifying.

---

## Troubleshooting Settings

### Settings Won't Save
- **Cause:** File permission issues
- **Fix:** Ensure `saves/` folder is writable
- **Check:** `saves/user_settings.json` exists and isn't read-only

### Audio Not Working
1. Check Master Volume isn't at 0
2. Check SFX/Music volumes aren't at 0
3. Verify audio files exist in `sound/` and `music/` folders
4. Restart game

### Graphics Mode Won't Switch
- **Fix:** Should switch immediately - restart game if stuck
- **Check:** `graphics_tiles.json` and `graphics/` folder exist

### UI Color Theme Not Changing
- **Check:** Color applies to UI elements only, not gameplay
- **Test:** Look at menu borders and button highlights
- **Verify:** Setting saved in `user_settings.json`

### Settings Reset After Update
- **Normal:** Game updates may reset settings if format changed
- **Backup:** Copy `saves/user_settings.json` before updating
- **Restore:** Replace file after update if compatible

---

## Recommended Settings

### For New Players
- **Graphics Mode:** Graphics (easier to read)
- **Achievement Popups:** On (learn what's possible)
- **System Crash Warning:** On (prevent accidents)
- **SFX Volume:** 75% (hear important cues)
- **Music Volume:** 50% (less distraction)

### For Experienced Players
- **Graphics Mode:** Personal preference
- **Achievement Popups:** Off (less distraction)
- **System Crash Warning:** Off (faster gameplay)
- **Volumes:** Adjusted to taste

### For Performance
- **Graphics Mode:** Glyph (faster rendering)
- **Particle Effects:** Off (reduce GPU load)
- **Master Volume:** Lower (reduce CPU audio processing)

### For Streamers/Content Creators
- **Achievement Popups:** On (show progression)
- **Graphics Mode:** Graphics (more visually appealing)
- **Particle Effects:** On (more dynamic)
- **Music Volume:** 40% (allow commentary)
- **UI Color Theme:** High contrast (Crimson, Magenta, or Azure)

---

## Keyboard Shortcuts in Settings

- **Up/Down:** Navigate options
- **Left/Right:** Adjust values (volume, cycle options)
- **Enter:** Confirm/toggle boolean options
- **ESC:** Save and exit
- **Mouse Click:** Select and adjust (mouse support)
- **Mouse Wheel:** Scroll if menu extends beyond screen

---

## Settings Philosophy

**Design Principles:**
1. **Sensible Defaults:** Game playable without touching settings
2. **Non-Intrusive:** Settings don't affect core gameplay balance
3. **Persistent:** Preferences survive across sessions
4. **Accessible:** Easy to find and modify
5. **Forgiving:** Can't break game by changing settings

**What's NOT Configurable:**
- Keybindings (fixed for consistency)
- Difficulty (selected at game start)
- Display resolution (fixed to 80x50 console)
- Game rules (requires JSON modding)

Settings are about **comfort and preference**, not **gameplay advantage**.

---

For modding beyond settings, see the **[Development Guide](Development)**.
