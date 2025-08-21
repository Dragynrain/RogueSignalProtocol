v7.0
**Hacker Stealth Dungeon Crawler**

## Executive Summary

Rogue Signal Protocol is a stealth-focused traditional roguelike where you play as a hacker's consciousness trapped in cyberspace. Navigate procedurally generated network dungeons using stealth, observation, and tactical combat. Master enemy patrol patterns, hide in shadows, and strike from stealth - or face the relentless Admin Avatar hunting you through the network.

**Core Experience:** Classic roguelike structure with stealth focus - observe, hide, strike, escape.

---

## Core Gameplay Loop

### The Stealth-First Structure
- **Movement:** Grid-based, 8-directional, always silent
- **Stealth:** Observe patrols, avoid vision, hide in shadows  
- **Combat:** Bump-to-attack OR stealth strikes for massive damage
- **Time:** Turn-based - everything moves when you do
- **Death:** Permanent - restart from Tutorial (Level 0)
- **Goal:** Reach the gateway while staying undetected

### Network as Dungeon
| Traditional Roguelike | Rogue Signal Protocol |
|----------------------|----------------------|
| Dungeon Floor | A Network |
| Room | Node |
| Corridor | Connection |
| Monster | Security Process |
| Equipment | Exploits and Upgrades |
| Stairs | Network Gateway |
| Potion | Data |

*All references throughout this document use these standardized terms.*

---

## Game World

### Network Size & Layout
**Standard Size:** 50x50 grid for all network systems
- Optimal for tactical stealth gameplay
- Consistent experience across all levels
- Manageable scope for procedural generation

### Network Progression (4 Levels)
0. **Tutorial Network** (First-time only)
   - Fixed, hand-designed layout for consistent learning
   - 3 enemies, basic patrols
   - 50% shadow coverage
   - Detection builds slowly to teach timing
   - Admin Avatar spawns at 100% detection

1. **Corporate Network** (Level 1)
   - 8 enemies, simple patrols
   - 40% shadow coverage
   - Admin Avatar spawns at 100% detection

2. **Government System** (Level 2) 
   - 12 enemies, mixed behaviors
   - 25% shadow coverage
   - Admin Avatar spawns at 75% detection

3. **Military Backbone** (Level 3)
   - 16 enemies, coordinated patrols
   - 15% shadow coverage  
   - Admin Avatar spawns at 50% detection

---

## Stealth System

### Core Mechanics
**Vision:** Each enemy has variable sight ranges (2-6 squares, circular 360°)
**Detection:** Binary system - you're either seen or hidden
**Shadows:** Marked with `◊` symbol, provide complete concealment
**Walls:** Block line of sight for both player and enemies

### Vision Display
**Enemy vision is always visible** when the enemy is within player's sight range, displayed as circular areas around each enemy. This allows players to:
- Study patrol patterns in advance
- See exactly where vision gets blocked by obstacles
- Plan routes through gaps in coverage
- Understand the tactical landscape at all times

### Enemy States
- **Green:** Unaware of your presence
- **Yellow:** Sees you but hasn't alerted yet (1 turn grace period)
- **Red:** Actively tracking and has alerted nearby enemies

### Patrol Types (3 Categories)
All enemy movement will show 3 moves of movement prediction by coloring the floor tiles where each enemy will be heading.
1. **Static (S):** No movement, guards key areas
2. **Linear (L):** Multi-point patterns (A→B→A, A→B→C→A, A→B→C→D→A, etc.)
3. **Random (R):** Unpredictable movement (but with 3-turn UI prediction)

---

## Resources (4 Core Systems)

### 1. CPU (Health/Life Force)
- **Range:** 0-100% CPU
- **Loss:** Combat damage only
- **Recovery:** Data Patches, killing enemies (+5 CPU per kill), CPU recovery spaces
- **Death:** 0 CPU = permanent death

### 2. Heat (Exploit Cooldown)
- **Range:** 0-100°C
- **Increase:** Using exploits generates heat
- **Decrease:** Passive cooling over time, cooling nodes
- **Limit:** Cannot use exploits at 100°C heat

### 3. RAM (Exploit Capacity)
- **Range:** 8/12 GB (loaded/total capacity)
- **Use:** Limits total exploits equipped simultaneously
- **Management:** Must choose which exploits to load for each node
- **Upgrade:** Find RAM modules to increase capacity

### 4. Detection Level
- **Range:** 0-100% 
- **Increase:** Being seen, killing enemies, time passage
- **Decrease:** Data Cleansers (rare items)
- **Critical:** Admin Avatar spawns at network-specific threshold

---

## Combat & Exploits

### Combat Types
- **Stealth Strike:** Attack unaware enemy for 2x damage + silence
- **Direct Combat:** Standard damage, always creates noise
- **Escape:** Break line of sight to return to stealth

### Targeting System
All ranged exploits use **line-of-sight targeting**:
- Click/select target within range
- Line-of-sight calculated through walls and obstacles
- Visual indicator shows valid targets
- Walls and obstacles block targeting just like vision

### Exploit Categories (4 Groups)

#### Stealth Exploits
1. **Shadow Step** (2GB RAM, +20°C, Range: 8) - Teleport between shadow zones
2. **Data Mimic** (1GB RAM, +15°C, Range: Self) - Appear as harmless data for 5 turns
3. **Noise Maker** (1GB RAM, +10°C, Range: 6) - Create distraction at target location

#### Combat Exploits  
4. **Buffer Overflow** (2GB RAM, +25°C, Range: Adjacent) - High melee damage, armor piercing
5. **Code Injection** (1GB RAM, +15°C, Range: 4) - Ranged attack, bypasses firewalls
6. **System Crash** (3GB RAM, +35°C, Range: 3 radius) - Area damage, disables multiple enemies

#### Utility Exploits
7. **Network Scan** (1GB RAM, +10°C, Range: 8) - Reveals enemy positions and patrol routes
8. **Log Wiper** (1GB RAM, +5°C, Range: Self) - Reduces detection level significantly

#### Emergency Exploits
9. **EMP Burst** (3GB RAM, +40°C, Range: 2 radius) - Disables all nearby enemies temporarily

**RAM Management:** Players can choose which exploits to load for each node, allowing tactical adaptation to different scenarios.

---

## Enemies (6 Types)

### Basic Enemies
1. **Scanner (s)** - CPU: 20, Static guard, 2-square vision
2. **Patrol (p)** - CPU: 25, Linear movement, 3-square vision  
3. **Bot (b)** - CPU: 15, Random movement, 2-square vision

### Advanced Enemies
4. **Firewall (F)** - CPU: 40, Static barrier with 1-square vision, reduces damage by 50%. Functions as an "intelligent barrier" - doesn't move but watches a specific chokepoint with very short range vision.
5. **Hunter (H)** - CPU: 35, Seeks disturbances, 5-square vision
6. **Admin Avatar (A)** - CPU: 100, Perfect tracking, 6-square vision, spawns at high detection

**Firewall Note:** Functions as an "intelligent barrier" - doesn't move but watches a specific chokepoint with very short range vision.

---

## Items (Single System)

### Data Patches (Randomized Each Run)
Six colors with random effects each playthrough:
- **Crimson, Azure, Emerald, Golden, Violet, Silver**

Possible effects:
1. Restore 30-40 CPU
2. Reduce heat by 40°C instantly  
3. -25% detection level
4. Temporary speed boost (50% faster movement for 10 turns)
5. Enhanced vision (see through 1 layer of walls for 15 turns)
6. Exploit efficiency (50% less heat generation for 8 turns)

**Identification:** Unknown until used, then learned for entire run

---

## User Interface

### Always Visible
```
┌─ CPU: 45/60 ── HEAT: ████░░░░░░ 42°C ── DETECTION: ██░░░░░░░░ 23% ──┐
│ RAM: 6/8 GB                                                         │
│                                                                     │
│  ◊◊◊  @  ░░░  ▓▓▓  ║                                              │
│  ◊◊◊     ░░░       ║   ●●●s●●●                                    │
│      p→  ░░░  ◊◊◊  ║                                              │
│  ▓▓▓     ░░░  ◊◊◊  ║         ●F●     >                            │
│                                                                     │
│ @ = You    s/p/F = Enemies    ◊ = Shadow                          │
│ ▓ = Wall   ░ = Floor          > = Gateway                         │
│ ● = Enemy vision range        ❄ = Cooling node                    │
│                                                                     │
│ Random Bot Prediction: ↑→↓ (next 3 moves)                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Context Information (Auto-Show)
- **Enemy vision ranges:** Always visible when enemy is in player's sight
- **Shadow zones:** Only when adjacent
- **Patrol routes:** Press Tab to toggle
- **Detection warnings:** Only when rising quickly
- **Heat warnings:** Only when approaching 75°C

### Visual Language
**Core Symbols (6 Total):**
- `@` Player
- `s/p/F/H/A` Enemies (single character each, variable vision ranges)
- `◊` Shadow zones  
- `▓` Walls
- `>` Gateway
- `●` Enemy vision range (circular display)

**Color Coding:**
- **Red:** Immediate danger (spotted, high detection, overheating)
- **Yellow:** Caution (rising detection, enemy alert, moderate heat)
- **Green:** Safety/opportunity (shadows, unaware enemies, cooling)
- **White:** Neutral (walls, floors, basic info)

---

## Technical Implementation

### Engine: Python + tcod
- **Core:** tcod library for roguelike functionality
- **Graphics:** 64x64 pixel sprites OR ASCII (no hybrid mode)
- **Audio:** Chiptune retro music tracks and simple sound effects
- **Save System:** JSON-based for configuration and progress

### Rendering Modes
**ASCII Mode:** Traditional text display with full feature support
**Graphics Mode:** 64x64 pixel sprite rendering with identical gameplay

**No Hybrid Mode:** Game operates in pure ASCII or pure graphics - no mixing of rendering styles within a single session.

### Audio System
- **Music:** Chiptune-style retro soundtrack with atmospheric cyberpunk tracks
- **Sound Effects:** Retro-styled audio cues for actions, alerts, and events

---

## Tutorial Integration (Dynamic Length)

### Tutorial Network (Level 0) - Fixed Design, First Play Only
**Phase 1:** Movement and basic stealth
- Learn grid movement in nodes
- Discover shadow zones
- Understand enemy vision ranges (always visible)

**Phase 2:** Patrol observation and prediction
- Watch enemy movement patterns
- Learn random patrol prediction system
- Practice timing movement through connections

**Phase 3:** Detection system and CPU recovery
- Experience detection building over time
- Learn CPU recovery through enemy kills (+5 CPU each)
- Find and use CPU recovery nodes
- Discover cooling nodes for heat management

**Phase 4:** Heat and exploit management
- Introduction to exploit system with ranges and targeting
- Heat generation and cooling mechanics
- RAM limitations and per-node loadout choices

**Phase 5:** Items and advanced mechanics
- Find and identify data patches
- Learn temporary effect system
- Practice stealth strikes vs direct combat
- Understand Admin Avatar spawn mechanics

**No Fixed Turn Limit:** Tutorial progresses based on player understanding, with detection building naturally to create urgency and teach timing.

---

## Design Philosophy

### Core Principles
1. **Clarity Over Complexity:** Every system serves the stealth experience
2. **Consistent Language:** Pure cyberpunk terminology throughout (Node/Connection/Gateway)
3. **Progressive Mastery:** Simple rules, deep tactical possibilities
4. **Immediate Feedback:** Clear cause-and-effect for all actions
5. **Predictive Behaviour:** UI should show what will happen in advance to allow puzzles and tactical choices
6. **Focused Experience:** Everything supports stealth gameplay

The game focuses on tense, tactical stealth gameplay where resource management creates meaningful decisions and the network environment mirrors real life network design concepts and names.