# UI and HUD Guide

Complete reference for the user interface and heads-up display in Rogue Signal Protocol.

## Overview

The game UI is divided into distinct regions, each serving specific purposes. Understanding the HUD helps you make informed tactical decisions.

**Screen Layout (80x50 characters):**
- **Top:** Status bar (1 line)
- **Center:** Game viewport (27x21 tiles)
- **Bottom:** Status panel and message log
- **Right:** Sidebar (when applicable)

---

## Top Status Bar

Located at the very top of the screen, showing critical real-time stats.

### CPU (Health)
**Format:** `CPU: [current]/[max]`
**Example:** `CPU: 75/100`

**Color Coding:**
- **Green:** CPU above 70% (healthy)
- **Yellow:** CPU 40-70% (caution)
- **Red:** CPU below 40% (danger)

**What It Means:**
- Your digital consciousness integrity
- 0 CPU = death and permadeath
- Max CPU increases with Processing Core upgrades (+20 each)
- Default: 100, Max possible: 200

**Monitoring:**
- Watch for red - use CPU nodes or Restore CPU code hacks
- Plan healing before major encounters
- Don't let Virus tick you to death

---

### Heat (Exploit Resource)
**Format:** `Heat: [current]/[max]°C`
**Example:** `Heat: 45/100°C`

**Color Coding:**
- **Cyan/Blue:** Heat below 50°C (safe)
- **Yellow:** Heat 50-80°C (warm)
- **Orange:** Heat 80-95°C (hot)
- **Red:** Heat 95-100°C (critical)

**What It Means:**
- Generated when using exploits
- Exceeding max (100°C default) causes overheat damage
- Passively cools 2°C/turn (3°C with buff)
- Max heat increases with Cooling Matrix upgrades (+20 each)
- Default: 100, Max possible: 200

**Monitoring:**
- Stay below 80°C for safety margin
- Use cooling nodes or Reduce Heat code hacks when orange/red
- Plan exploit usage around heat budget

---

### Trace (Detection Level)
**Format:** `Trace: [percentage]%`
**Example:** `Trace: 42%`

**Color Coding:**
- **Green:** Trace below 30% (safe)
- **Yellow:** Trace 30-60% (elevated)
- **Red:** Trace above 60% (dangerous)

**What It Means:**
- Your detection signature/threat level
- Passively increases 1% every 25 turns
- Increases faster when detected or in combat
- Reduces by 50% when advancing to next level
- High trace (70%+) can spawn Admin Avatar on Level 3

**Monitoring:**
- Use ghost nodes or Log Wiper to reduce
- Critical to watch on Level 3 (Admin Avatar threat)
- For No Trace achievement, keep below 50%

---

### RAM (Exploit Capacity)
**Format:** `RAM: [used]/[max] GB`
**Example:** `RAM: 6/8 GB`

**Color Coding:**
- **Green:** RAM available (can equip more exploits)
- **Red:** RAM full (at capacity)

**What It Means:**
- Determines how many exploits you can equip
- Each exploit costs 1-3 RAM
- Max 5 exploits can be equipped regardless of RAM
- Max RAM increases with Memory Expansion upgrades (+4 each)
- Default: 8 GB, Max possible: 32 GB

**Monitoring:**
- Green = room for more exploits
- Red = at capacity (unequip to add different exploits)
- Plan loadouts around RAM budget

---

## Bottom Status Panel

Located at bottom of screen, shows equipped exploits and active status effects.

### Equipped Exploits (Keys 1-5)
**Format:** `[Number]: [Exploit Name] ([RAM cost]) [Heat indicator]`

**Example Display:**
```
1: System Hop (3) [25°C]
2: Code Injection (2) [20°C]
3: Threat Scan (1) [25°C]
4: -- Empty --
5: -- Empty --
```

**Color Coding:**
- **Green:** Can afford heat cost
- **Red:** Cannot afford heat cost (would overheat)
- **Gray:** Empty slot

**What It Shows:**
- Which exploits are equipped
- Which number key activates each
- RAM cost (in parentheses)
- Heat cost (if affordable)

**Usage:**
- Press 1-5 to activate corresponding exploit
- Green = safe to use
- Red = would exceed max heat (don't use unless accepting overheat)

---

### Active Status Effects
**Format:** `[Effect Name] ([turns remaining])`

**Examples:**
```
Invisible (5)
Speed Boost (3)
Virus (7)
```

**What It Shows:**
- All active buffs and debuffs
- Remaining turn count
- Multiple effects stack

**Color Coding:**
- **Positive effects:** Green/Cyan text
- **Negative effects:** Red/Yellow text

**Monitoring:**
- Plan around buff expirations
- Prioritize removing debuffs (Virus, Slowed)
- Track buff durations for optimal use

---

## Message Log

Scrolling text log of recent game events, displayed in lower portion of screen.

### Message Types & Colors

**Critical (Crimson Red):**
- Enemy eliminations
- Player death
- Level completion
- Admin Avatar events
- `Enemy eliminated!`

**Error (Orange):**
- Failed actions
- Invalid commands
- Blocked movements
- `Cannot use exploit - insufficient heat`

**Warning (Gold/Yellow):**
- Enemy detections
- Alerts
- Hostile state changes
- `Enemy detected you!`

**Alert (Amber):**
- Enemy spawns
- Patrol movements
- Suspicious activity
- `Enemy investigating...`

**Success (Green):**
- Item collection
- Resource restoration
- Completed actions
- `Collected Memory Expansion!`

**Info (Cyan):**
- Exploit activations
- Status changes
- Turn updates
- `Activated System Hop`

**System (Purple):**
- Loading messages
- Save/load confirmations
- `Game saved`

**Combat (Red):**
- Damage dealt/received
- Combat results
- `Dealt 40 damage!`

**Stealth (Blue):**
- Invisibility status
- Blind spot entry
- Stealth events
- `Entered blind spot`

---

### Message Log Features

**Scrolling:**
- Newest messages at bottom
- Automatically scrolls
- Limited history (last ~20 messages visible)

**Reading:**
- Messages appear in real-time
- No need to press anything
- Crucial tactical info displayed here

**Importance:**
- Watch for detection warnings
- Monitor damage dealt/received
- Track resource collection

---

## Game Viewport

**Central play area (27x21 tiles)** showing the game world.

### Viewport Elements

**Player (@):**
- Your character
- Center of viewport (typically)
- White/cyan color

**Enemies (S/P/B/F/H/V/I/A):**
- **Yellow:** Unaware
- **Orange:** Alert
- **Red:** Hostile
- **Blue:** Disabled/Stunned

**Terrain:**
- **Walls:** Box-drawing characters (─│┌┐└┘)
- **Floor:** Gray/purple open space
- **Blind Spots:** `.` symbols or darker floor (♠ in some modes)
- **Gateway:** `>` symbol (goal)

**Items:**
- **Code Hack:** `!` (colored)
- **Exploit Pickup:** `&` (colored)
- **Upgrade:** `[`, `]`, or `=` symbols (colored)
- **Data Fragment:** `♫` symbol (colored)

**Special Nodes:**
- **Cooling Node:** `♢` or diamond symbol (cyan)
- **CPU Node:** `♡` or heart symbol (red)
- **Ghost Node:** `♤` or spade symbol (purple)

### Visual Indicators

**Enemy Movement Queue:**
- Arrows showing next 3 planned moves
- `→ → ↑` = move right, right, up
- Invalidates when blocked or state changes

**Enemy Vision (with Threat Scan):**
- Shaded overlay showing detection ranges
- Darker shade = enemy vision cone
- Helps plan stealth routes

**Targeting Overlay (when using exploits):**
- Range indicator showing valid targets
- AOE indicator for area attacks
- Cursor for aiming

---

## Sidebar (Context-Specific)

Appears in certain modes (look mode, targeting, inventory).

### Inspection Sidebar (Look Mode)
**Activated:** Press L key

**Contents:**
- Entity name
- Description
- Stats (if enemy)
- Status effects
- Special properties

**Example:**
```
Hunter (H)
HP: 50/50
Vision: 6 tiles
Damage: 15
State: Hostile

Elite security algorithm
with advanced threat
detection and powerful
attack protocols.
```

### Inventory Sidebar (Inventory Mode)
**Activated:** Press I key

**Contents:**
- Equipped exploits (top section)
- Collected code hacks (middle section)
- Controls hint (bottom)

**Navigation:**
- Up/Down to navigate
- Enter to use/equip
- U to unequip
- I/ESC to close

---

## Additional UI Elements

### Targeting Cursor
**Appears When:** Using targeted exploits

**Visual:**
- Crosshair or bracket symbols at cursor position
- Shows valid/invalid targets
- Range circle overlay

**Controls:**
- Arrow keys/WASD to move cursor
- Enter to confirm target
- ESC/Right-click to cancel

**Colors:**
- **Green:** Valid target within range
- **Red:** Invalid target or out of range
- **Yellow:** Valid area (for AOE)

---

### Dialogue Boxes
**Appears For:** Confirmations, warnings, story fragments

**Visual:**
- Centered box with border
- Title at top
- Content in middle
- Button options at bottom

**Controls:**
- Enter to confirm
- ESC/Right-click to cancel
- Mouse click on buttons

**Types:**
- **Warning:** System Crash self-damage alert
- **Confirmation:** Level transition prompts
- **Story:** Narrative fragments
- **Tutorial:** First-time tips

---

### Achievement Popup
**Appears When:** Achievement unlocked (if enabled in settings)

**Visual:**
- Top of screen
- Achievement name + icon
- Description
- Fades after 3 seconds

**Example:**
```
🏆 Achievement Unlocked! 🏆
First Blood
Kill your first enemy
```

**Behavior:**
- Doesn't pause gameplay
- Stacks if multiple unlock simultaneously
- Can be disabled in settings

---

## HUD Customization

### UI Color Theme
**Customizable:** Yes (8 color options in settings)
**Affects:**
- Menu borders
- Button highlights
- Selected items
- UI accents

**Does NOT Affect:**
- Status bar colors (fixed by value)
- Message log colors (fixed by type)
- Enemy colors (fixed by state)

**Options:**
- Cyan (default)
- Purple
- Magenta
- Golden
- Crimson
- Azure
- Emerald
- Ivory

---

## Tips for Reading the HUD

### Priority Information (Check Every Turn)
1. **CPU** - Am I low on health?
2. **Heat** - Can I use exploits?
3. **Enemies** - Where are threats?
4. **Message log** - Did I get detected?

### Secondary Information (Check Periodically)
5. **Trace** - Am I close to Admin Avatar spawn?
6. **RAM** - Do I have capacity for new exploits?
7. **Status effects** - Are buffs/debuffs about to expire?

### Situational Information (Check When Relevant)
8. **Movement queues** - Where are enemies going?
9. **Targeting overlay** - What's in range?
10. **Inventory** - What resources do I have?

---

## Common HUD Warnings

**CPU Flashing Red:**
- Critical health (<40%)
- Find CPU node or use Restore CPU code hack ASAP

**Heat Flashing Red:**
- Near overheat (95-100°C)
- Stop using exploits, find cooling node

**Trace Above 70% on Level 3:**
- Admin Avatar spawn risk
- Use Log Wiper or ghost nodes immediately

**All Exploits Showing Red:**
- Heat too high to use any abilities
- Wait for passive cooling or use Reduce Heat code hack

**"Virus (X)" in Status Panel:**
- Taking 3 CPU/turn damage
- Use Antivirus exploit to cure

---

## Accessibility Features

### Visual Clarity
- High contrast colors
- Large readable text
- Clear stat indicators
- Color-blind friendly (multiple cues)

### Information Density
- All critical info visible
- No hidden stats
- Transparent systems
- Real-time feedback

### Customization
- 8 UI color themes
- Graphics vs glyph mode
- Adjustable volumes
- Toggleable popups

---

For more information:
- **[Gameplay Mechanics](Gameplay-Mechanics)** - Core systems explained
- **[Status Effects Reference](Status-Effects-Reference)** - Status panel effects
- **[Settings and Configuration](Settings-and-Configuration)** - UI customization
- **[Keybindings](Keybindings)** - All controls reference
