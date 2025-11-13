# Look and Inspection System

Complete guide to examining entities, terrain, and items in Rogue Signal Protocol.

## Overview

The **Look Mode** (also called **Inspection System**) allows you to examine any tile on the map for detailed information. It's accessed by pressing the **L** key and provides tactical intelligence crucial for planning your approach.

**Key Features:**
- Examine enemies to see stats and state
- Inspect terrain for descriptions
- View item details before collection
- Check distance and positioning
- No turn cost - look freely

---

## Activating Look Mode

### Basic Activation
**Key:** Press **L** to enter Look Mode

**Visual Changes:**
- Cursor appears (crosshair or bracket symbols)
- Sidebar opens on right showing details
- Game pauses (no turn advancement)
- Status indicator shows "Look Mode" active

**Controls:**
- **Arrow Keys / WASD / QEZC / Numpad:** Move cursor
- **Mouse:** Click tiles to inspect or move cursor
- **L / ESC / Right-Click:** Exit Look Mode
- **Enter:** Select current tile for detailed info

---

## What You Can Inspect

### Entities (Living Things)

#### Player Character
**Information Shown:**
- Current CPU / Max CPU
- Current Heat / Max Heat
- Current Trace %
- Current RAM usage / Max RAM
- Equipped exploits
- Active status effects

**Example:**
```
Player (@)

CPU: 75/100
Heat: 45/100°C
Trace: 42%
RAM: 6/8 GB

Equipped:
- System Hop (3 RAM)
- Code Injection (2 RAM)
- Threat Scan (1 RAM)

Status:
- Invisible (3 turns)
```

#### Enemies
**Information Shown:**
- Enemy type and name
- Current CPU / Max CPU
- Vision range (in tiles)
- Damage value
- Movement behavior
- Current state (Unaware/Alert/Hostile)
- Description

**Example:**
```
Hunter (H)

CPU: 50/50
Vision: 6 tiles
Damage: 15
Movement: Random
State: Hostile

Elite security algorithm
with advanced threat
detection and powerful
attack protocols.
```

**Tactical Value:**
- Check enemy health before engaging
- Know vision range to avoid detection
- See damage to assess threat level
- Understand movement patterns
- Check if enemy is aware/hostile

---

### Terrain (Map Features)

#### Walls
**Name:** Security Barrier
**Description:** Impenetrable firewall protecting restricted network segments. Blocks both movement and line of sight.

**Tactical Notes:**
- Cannot pass through
- Blocks vision (good for hiding)
- Use for cover and positioning

#### Floor
**Name:** Data Corridor
**Description:** Standard network pathway where data flows freely. Visible to security monitoring systems.

**Tactical Notes:**
- Open, traversable space
- No cover or concealment
- Enemies can see you here

#### Blind Spots
**Name:** Digital Shadows
**Description:** Unmonitored network dead zones where surveillance coverage is weak. Concealment reduces enemy detection range.

**Visual:** `.` symbol or darker floor tiles (♠ in some modes)

**Tactical Notes:**
- **+10 damage bonus** when attacking from here
- Reduces enemy vision range by 3x
- Essential for stealth gameplay
- Ghost Nodes also function as blind spots

#### Gateway
**Name:** Network Gateway
**Description:** Secure tunnel to the next network layer. Step here to progress deeper into the system.

**Visual:** `>` symbol

**Tactical Notes:**
- Level exit/goal
- Must reach to advance
- Ends current level

---

### Items (Collectibles)

#### Code Hack (!)
**Name:** Data Code
**Description:** Encrypted payload with randomized beneficial effects. Collect to discover its purpose.

**Additional Info:**
- Color indicates effect type (randomized per session)
- Discovered effects show name
- Unknown effects show "Unknown Code Hack"

**Tactical Value:**
- Identify which code hack type before collecting
- Plan collection routes
- See if already discovered

#### Exploit Pickup (&)
**Name:** Exploit Module
**Description:** Sophisticated hacking tool. Equip to add new tactical capabilities to your arsenal.

**Additional Info:**
- Shows which exploit it is
- Displays RAM cost
- Shows heat cost
- Full description

**Example:**
```
Exploit Module (&)

System Hop
RAM: 3 | Heat: 30

Rapidly pivot to any
monitoring blind spot
within 6 tiles. Instant
relocation through
pre-established network
connections.
```

#### Permanent Upgrades ([ ] =)
**Name:** Varies by type
**Description:** Permanent stat increase

**Types:**
- **Memory Expansion ([):** +4 RAM
- **Processing Core (]):** +20 max CPU
- **Cooling Matrix (=):** +20 max Heat

**Example:**
```
Memory Expansion ([)

+4 RAM Permanent

High-capacity memory
module. Permanently
expands RAM by 4GB -
equip more complex
exploits simultaneously.
```

#### Data Fragment (♫)
**Name:** Data Fragment
**Description:** Corrupted memory dump containing fragments of classified information. Collect to reconstruct the narrative.

**Tactical Value:**
- Story content (no spoilers in inspection)
- Safe to collect
- No gameplay impact

---

### Special Nodes

#### Cooling Node (♢)
**Name:** Cooling Node
**Description:** Thermal regulation system that dissipates 20 degrees of excess heat. Single-use per visit.

**Effect:** -20°C heat instantly
**Visual:** Diamond symbol, cyan color

**Tactical Value:**
- Plan paths to cooling nodes
- Know locations for heat management
- Use Network Scan to reveal all

#### CPU Recovery Node (♡)
**Name:** CPU Recovery Node
**Description:** Emergency processing restoration point. Recovers 20 CPU when accessed.

**Effect:** +20 CPU instantly
**Visual:** Heart symbol, red color

**Tactical Value:**
- Emergency healing locations
- Plan combat near CPU nodes
- Save for critical moments

#### Ghost Node (♤)
**Name:** Ghost Node
**Description:** Trace obfuscation relay that reduces detection signature by 20%. Also functions as monitoring blind spot for concealment.

**Effect:** -20% trace reduction + blind spot benefits
**Visual:** Spade symbol, purple color

**Tactical Value:**
- Dual purpose (trace reduction + stealth)
- Critical on Level 3 for trace management
- Plan routes through ghost nodes

---

## Inspection Sidebar

Located on right side of screen during Look Mode.

### Sidebar Sections

**Top Section: Entity/Terrain Name**
- Large, bold text
- Symbol in parentheses
- E.g., "Hunter (H)"

**Middle Section: Stats (if applicable)**
- CPU, Vision, Damage (enemies)
- Effects, costs (items)
- No stats for terrain

**Bottom Section: Description**
- Lore-friendly explanation
- Tactical hints
- Flavor text

**Controls Hint (Bottom)**
- Reminder of Look Mode controls
- "L/ESC to exit"

---

## Quick Inspection (Mouse)

### Single-Click Inspection
**Method:** Left-click any tile while not in Look Mode

**Effect:**
- Instantly enters Look Mode focused on that tile
- Cursor positioned on clicked tile
- Sidebar shows details immediately

**Use Case:**
- Quick enemy checks during gameplay
- Rapid terrain inspection
- Faster than keyboard navigation

**Example Workflow:**
1. See unknown enemy
2. Click enemy tile
3. Read stats in sidebar
4. Press L or ESC to exit
5. Make tactical decision

---

## Tactical Applications

### Pre-Combat Scouting

**Check Enemy Stats:**
1. Enter Look Mode (L)
2. Navigate to enemy
3. Read CPU, damage, vision
4. Assess threat level
5. Plan approach accordingly

**Identify Priorities:**
- High-damage enemies (Hunters: 15 dmg)
- High-health tanks (Firewalls: 80 CPU)
- Non-combat threats (Scanners: 0 dmg but alert)
- Special abilities (Viruses: status effects)

### Stealth Planning

**Vision Range Assessment:**
1. Inspect enemy
2. Note vision range (3-8 tiles)
3. Calculate safe paths
4. Use blind spots for approach

**Movement Prediction:**
- Check enemy movement type
- PATROL = predictable (shows queue)
- RANDOM = unpredictable
- STATIC = stationary

### Resource Management

**Node Location:**
1. Use Network Scan exploit (reveals all nodes)
2. Inspect nodes via Look Mode
3. Plan routes to cooling/CPU/ghost nodes
4. Prioritize based on needs

**Item Prioritization:**
- Inspect upgrades to know type
- Check exploit pickups for loadout decisions
- Identify code hack colors (if discovered)

### Distance Calculation

**Manual Distance Check:**
- Move cursor from player to target
- Count tiles (slow but accurate)
- Determine if in exploit range

**Better Method:**
- Use exploit targeting mode (shows range automatically)
- Threat Scan reveals vision ranges
- Network Scan reveals node locations

---

## Look Mode Best Practices

### For New Players
1. **Inspect everything** - Learn enemy types and terrain
2. **Check unknown enemies** - See stats before engaging
3. **Read item descriptions** - Understand what you're collecting
4. **Learn symbols** - Associate symbols with types
5. **Use freely** - No turn cost, look as much as needed

### For Experienced Players
1. **Quick mouse clicks** - Faster than keyboard navigation
2. **Focus on unknowns** - Skip inspecting familiar enemies
3. **Priority checks** - Only inspect when decision-critical
4. **Muscle memory** - Recognize enemies by color/state without inspecting

### For Speedrunners
1. **Minimal inspection** - Only when absolutely necessary
2. **Enemy state colors** - Yellow/Orange/Red identification without inspection
3. **Item skipping** - Don't inspect items you're not collecting
4. **Pre-run knowledge** - Memorize enemy stats to skip inspection

---

## Advanced Inspection Techniques

### Enemy State Analysis
**Unaware (Yellow):**
- Following patrol/random behavior
- Hasn't detected player
- Safe to approach carefully

**Alert (Orange):**
- Investigating suspicious activity
- Short duration (1 turn)
- May become hostile or return to unaware

**Hostile (Red):**
- Actively pursuing player
- Uses optimal pathfinding
- Alerts nearby enemies

**Disabled (Blue):**
- Cannot move or act
- From Denial of Service exploit
- Safe to ignore or eliminate

### Movement Queue Reading
**When Visible (Patrol enemies):**
- Shows next 3 planned moves
- Arrows indicate direction (→ ↑ ← ↓)
- Diagonals (↗ ↖ ↙ ↘)
- Plan around predicted positions

**Queue Invalidation:**
- Changes when enemy state changes
- Recalculates when move blocked
- Hostile enemies get new paths

### Threat Assessment Matrix

**High Threat (Inspect Always):**
- Admin Avatar (250 CPU, 45 damage, 50% resist)
- Hunter (50 CPU, 15 damage, 6 vision)
- Hostile enemies near player

**Medium Threat (Inspect If Uncertain):**
- Patrol (40 CPU, 10 damage, predictable)
- Firewall (80 CPU, 5 damage, blocks paths)
- Virus (35 CPU, 0 damage, inflicts status)

**Low Threat (Rarely Inspect):**
- Scanner (35 CPU, 0 damage, static)
- Bot (25 CPU, 8 damage, but low health)
- Inhibitor (30 CPU, 0 damage, slows only)

---

## Keyboard vs Mouse Inspection

### Keyboard Method
**Pros:**
- Precise tile-by-tile navigation
- Good for methodical exploration
- Works without mouse

**Cons:**
- Slower for distant targets
- Requires entering Look Mode first
- More button presses

**Best For:**
- Keyboard-only players
- Scanning large areas systematically
- When precision navigation needed

### Mouse Method
**Pros:**
- Instant targeting (single click)
- Fast for specific tiles
- Natural and intuitive

**Cons:**
- Requires accurate clicking
- Can misclick small tiles
- Mouse required (obviously)

**Best For:**
- Quick enemy checks
- Rapid item inspection
- Casual exploration

---

## Common Inspection Scenarios

### Scenario 1: Unknown Enemy Ahead
1. **Spot** unfamiliar symbol
2. **Enter Look Mode** (L or left-click)
3. **Inspect** enemy
4. **Read** stats (CPU, damage, vision)
5. **Decide** approach (fight, avoid, stealth)
6. **Exit** Look Mode (L/ESC)

### Scenario 2: Planning Stealth Route
1. **Enter Look Mode**
2. **Inspect** each enemy on path
3. **Note** vision ranges
4. **Check** blind spot positions
5. **Calculate** safe route
6. **Execute** plan

### Scenario 3: Pre-Combat Assessment
1. **Inspect** all nearby enemies
2. **Prioritize** targets (high damage first)
3. **Check** if in exploit range
4. **Plan** attack sequence
5. **Estimate** heat cost of plan
6. **Engage** or reposition

### Scenario 4: Resource Location
1. **Use Network Scan** (reveals all nodes)
2. **Enter Look Mode**
3. **Inspect** revealed nodes
4. **Note** closest cooling/CPU/ghost node
5. **Plan** route to resources
6. **Navigate** accordingly

---

## Inspection Shortcuts

### Quick Reference
- **L:** Enter/Exit Look Mode
- **ESC:** Exit Look Mode
- **Enter:** Confirm selection
- **Arrows/WASD:** Navigate cursor
- **Mouse:** Instant targeting

### Pro Tips
1. **Double-tap L** - Enter and exit quickly for refresh
2. **Mouse hover** - Some UI elements show tooltips without Look Mode
3. **Exploit targeting** - Built-in range indicators (better than manual distance)
4. **Threat Scan** - Reveals enemy vision without inspecting each
5. **Network Scan** - Reveals all nodes without inspecting individually

---

## Troubleshooting

**Problem: Sidebar not showing details**
- **Solution:** Ensure you're targeting a tile with something on it (not empty floor)

**Problem: Can't exit Look Mode**
- **Solution:** Press L, ESC, or right-click

**Problem: Cursor not visible**
- **Solution:** Move cursor - it may be off-screen or same color as background

**Problem: Mouse click not working**
- **Solution:** Ensure game window has focus, click directly on tile

**Problem: Stats not updating**
- **Solution:** Exit and re-enter Look Mode to refresh

---

## Inspection Philosophy

**Design Intent:**
- **No hidden information** - All stats visible
- **No turn cost** - Look freely without penalty
- **Tactical empowerment** - Make informed decisions
- **Accessibility** - Both keyboard and mouse supported

**Player Advantage:**
- Know enemy stats
- Plan before engaging
- Understand terrain
- No surprises (except random movement)

---

For related systems:
- **[UI and HUD Guide](UI-and-HUD-Guide)** - Understanding the interface
- **[Enemy Database](Enemy-Database)** - Complete enemy stats reference
- **[Gameplay Mechanics](Gameplay-Mechanics)** - Core game systems
- **[Keybindings](Keybindings)** - All controls including Look Mode
