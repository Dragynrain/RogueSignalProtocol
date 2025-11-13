# Gameplay Mechanics

Core gameplay systems and mechanics in Rogue Signal Protocol.

## Core Stats

### CPU (Health)
- **Default:** 100
- **Max Capacity:** 200
- Your primary health pool. When it reaches 0, you're eliminated
- Can be restored with **CPU Recovery Nodes** (+20) and by eliminating enemies (+5)
- Upgraded permanently with **Processing Core** pickups (+20 max)

### RAM (Ability Slots)
- **Default:** 8 GB
- **Max Capacity:** 32 GB
- Determines how many exploits you can equip simultaneously
- Each exploit costs 1-3 RAM
- Upgraded permanently with **Memory Expansion** pickups (+4 max)

### Heat (Ability Resource)
- **Max:** 100 degrees
- **Overheat Threshold:** 100 degrees
- Generated when using exploits
- Passively cools 2 degrees/turn (3 with enhanced cooling)
- Can be reduced with **Cooling Nodes** (-20 instant)
- Upgraded permanently with **Cooling Matrix** pickups (+20 max)

### Trace (Detection Level)
- **Max:** 100%
- Passively increases 1% every 25 turns
- Increases when in enemy vision or performing loud actions
- Reduced by 50% when advancing to next level
- Can be reduced with **Log Wiper** exploit (-30%) or **Ghost Nodes** (-20%)
- At high trace levels, enemies become more aggressive

## Movement & Stealth

### Vision System
- **Player Vision:** 15 tiles
- **Enemy Vision:** Varies by type (3-8 tiles)
- Line of sight blocked by walls
- **Blind Spots** reduce enemy vision range by 3x when player is inside

### Detection States
Enemies have three awareness states:
1. **Unaware (Yellow):** Normal patrol, hasn't detected you
2. **Alert (Orange):** Investigating suspicious activity, lasts 1 turn
3. **Hostile (Red):** Actively pursuing you

### Blind Spots
- Represented by `.` symbol
- Reduce enemy detection range dramatically
- Function as stealth zones for tactical positioning
- Ghost Nodes also function as blind spots

## Enemy Movement Queue

One of the game's core tactical features:
- Enemies display their **next 3 planned moves**
- Allows you to predict and outmaneuver security
- Queue invalidates when:
  - Enemy changes state (unaware -> alert -> hostile)
  - Planned move is blocked
- All enemies use consistent pathfinding for predictability

## Combat System

### Damage Calculation
- Direct damage: Exploit damage value - enemy resistance (if applicable)
- Area damage: Can affect multiple targets including you
- **Admin Avatar** has 50% damage resistance (minimum 5 damage)

### Combat Exploits
- **Buffer Overflow:** 40 damage, melee range (1 tile)
- **Code Injection:** 25 damage, 5 tile range
- **Logic Bomb:** 15 damage, area attack (2 tile radius)
- **Denial of Service:** Disables enemies for 5 turns
- **System Crash:** 30 damage to everything nearby (including you!)

### Shadow Damage Bonus
- Attacking from blind spots grants +10 damage
- Encourages stealth-to-combat transitions

## Exploits

Exploits are your primary abilities, organized into four categories:

### Stealth
- **System Hop:** Teleport up to 6 tiles
- **Traffic Masquerade:** Become invisible for 5 turns
- **Decoy Swarm:** Distract enemies for 8 turns
- **Memory Leak:** Blind enemies in 3x3 area for 3 turns

### Combat
- **Buffer Overflow:** High damage melee (40)
- **Code Injection:** Reliable ranged damage (25)
- **Logic Bomb:** Area damage (15)
- **Denial of Service:** Disable enemies

### Utility
- **Threat Scan:** Reveal enemy vision for 5 turns
- **Network Scan:** Show all special nodes
- **Log Wiper:** Reduce trace by 30%
- **Antivirus:** Cure all negative effects

### Emergency
- **System Crash:** Desperation move, damages everything

See **[Exploit Database](Exploit-Database)** for complete details.

## Level Progression

### Network Types
1. **Corporate Network (Level 1)**
   - 19 enemies
   - More resources (6 cooling/CPU/ghost nodes)
   - 12 data codes, 4 exploit pickups, 1 upgrade

2. **Government System (Level 2)**
   - 28 enemies
   - Moderate resources (4 cooling/CPU/ghost nodes)
   - 10 data codes, 3 exploit pickups, 2 upgrades

3. **Military Backbone (Level 3)**
   - 38 enemies
   - Scarce resources (2 cooling/CPU/ghost nodes)
   - 5 data codes, 2 exploit pickups, 3 upgrades
   - Final level with Admin Avatar boss

### Victory Condition
- Reach and activate the **Gateway** (>) on each level
- Successfully exfiltrate from all 3 networks

## Data Codes

Randomized beneficial pickups (`!` symbol):
- Heat reduction: -40 degrees instant
- CPU restoration: 30-40 CPU
- Trace reduction: -25%
- Speed boost: Extra movement for 3 turns
- Enhanced vision: +2 vision range for 5 turns
- Exploit efficiency: Reduced heat cost for 8 turns

## Special Enemy Behaviors

### Admin Avatar (Boss)
- Only appears on Military Backbone (Level 3)
- 250 CPU, 8 vision range, 45 damage
- 50% damage resistance (min 5 damage)
- Relentless pursuit behavior
- Uses advanced pathfinding

### Virus Enemies
- Don't deal direct damage
- Inflict virus status effect (3-10 turns)
- Virus deals 3 CPU damage per turn
- Cured with **Antivirus** exploit

### Inhibitor Enemies
- Apply slow effect on contact
- Reduces your movement options
- No direct damage

### Scanner Enemies
- Stationary surveillance (0 damage)
- Enhanced vision range (5 tiles)
- Early warning system for other enemies

## Difficulty Modifiers

Four difficulty levels with stat multipliers:
- **Easy:** 0.8x (20% easier)
- **Normal:** 1.0x (baseline)
- **Hard:** 1.3x (30% harder)
- **Nightmare:** 1.6x (60% harder)

Multipliers affect enemy stats and resource availability.

## Permadeath & Saves

- Game auto-saves on exit
- **Save is deleted on death** - true permadeath
- No save scumming or reloading
- Achievement progress persists across runs
