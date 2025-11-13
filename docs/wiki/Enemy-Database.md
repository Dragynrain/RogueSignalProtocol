# Enemy Database
Complete reference for all enemy types in Rogue Signal Protocol.
## Overview
There are **8 unique enemy types** with different behaviors, stats, and threat levels.
## Enemy Types
### Static Enemies
Stationary enemies that guard fixed positions.
#### Scanner (S)
**Stats:**
- CPU: 35
- Vision: 5 tiles
- Damage: 0
- Movement: STATIC

Stationary surveillance node with enhanced detection arrays. Cannot attack but sees farther than most security programs.
**Tactical Notes:**
- Cannot attack but alerts nearby enemies
- Extended vision range makes them dangerous sentries
- Eliminate early if stealth approach required

#### Firewall (F)
**Stats:**
- CPU: 80
- Vision: 3 tiles
- Damage: 5
- Movement: STATIC

Heavily fortified security barrier process. Extremely resilient but slow to respond to threats.
**Tactical Notes:**
- Extremely high CPU makes them hard to kill
- Often blocks critical paths
- Consider avoiding rather than fighting

### Mobile Enemies
Enemies that patrol or pursue actively.
#### Patrol (P)
**Stats:**
- CPU: 40
- Vision: 4 tiles
- Damage: 10
- Movement: PATROL

Automated security routine that follows predetermined routes. Equipped with basic defensive protocols.
**Tactical Notes:**
- Shows next 3 planned moves - highly predictable
- Easy to avoid with proper timing
- Alerts other enemies when detecting player

#### Bot (B)
**Stats:**
- CPU: 25
- Vision: 3 tiles
- Damage: 8
- Movement: RANDOM

Autonomous cleaning script with pattern recognition. Wanders unpredictably while scanning for anomalies.
**Tactical Notes:**
- Unpredictable movement makes them dangerous
- Lower stats compensate for chaos factor
- Can accidentally discover you in blind spots

#### Hunter (H)
**Stats:**
- CPU: 50
- Vision: 6 tiles
- Damage: 15
- Movement: RANDOM

Elite security algorithm with advanced threat detection and powerful attack protocols. Highly dangerous.
**Tactical Notes:**
- Highest vision range of standard enemies
- Very dangerous in combat (15 damage)
- Avoid or ambush from blind spots

#### Virus (V)
**Stats:**
- CPU: 35
- Vision: 4 tiles
- Damage: 0
- Movement: VIRUS

Hostile malware that corrupts on contact. Doesn't deal direct damage but infects systems with degrading code.
**Tactical Notes:**
- No direct damage but inflicts virus status
- Virus deals 3 CPU per turn for 3-10 turns
- Use Antivirus exploit to cure infection

#### Inhibitor (I)
**Stats:**
- CPU: 30
- Vision: 4 tiles
- Damage: 0
- Movement: RANDOM

Traffic control daemon that throttles unauthorized processes. Slows your execution speed without causing damage.
**Tactical Notes:**
- Slows your movement on contact
- No damage but tactical nuisance
- Use Antivirus exploit to remove slow effect

### Boss Enemy
Special enemy that only appears under specific conditions.
#### Admin Avatar (A)
**Stats:**
- CPU: 250
- Vision: 8 tiles
- Damage: 45
- Damage Resistance: 50% (min 5)
- Movement: ADMIN

System administrator's digital enforcer. Heavily armed, relentless, and commands root-level privileges.

**Spawn Conditions:**
- Appears on Military Backbone (Level 3) at high trace levels
- Can spawn when trace reaches critical thresholds

**Tactical Notes:**
- **EXTREMELY DANGEROUS** - avoid if possible
- 50% damage resistance makes it very tanky
- 45 damage can kill you in 3 hits
- Best strategy: Keep trace low to prevent spawning
- If spawned: Use System Hop to escape, avoid direct combat

## Stats Comparison
| Enemy | Symbol | CPU | Vision | Damage | Movement |
|-------|--------|-----|--------|--------|----------|
| Bot | B | 25 | 3 | 8 | Random |
| Inhibitor | I | 30 | 4 | 0 | Random |
| Scanner | S | 35 | 5 | 0 | Static |
| Virus | V | 35 | 4 | 0 | Virus |
| Patrol | P | 40 | 4 | 10 | Patrol |
| Hunter | H | 50 | 6 | 15 | Random |
| Firewall | F | 80 | 3 | 5 | Static |
| Admin Avatar | A | 250 | 8 | 45 | Admin |

## Movement Behaviors
### STATIC
Remains in one position. Does not move unless pushed by game mechanics.

### PATROL
Follows predetermined routes. Shows next 3 planned moves for player prediction.

### RANDOM
Moves unpredictably. Can change direction at any moment.

### VIRUS
Special movement pattern for Virus enemies. Wanders while seeking targets.

### ADMIN
Advanced AI behavior. Relentlessly pursues player with optimal pathfinding.

## Detection & Alert System
All enemies have three awareness states:

### Unaware (Yellow)
- Default state
- Following normal behavior pattern
- Has not detected player

### Alert (Orange)
- Investigating suspicious activity
- Lasts 1 turn only
- Can escalate to hostile if player seen again

### Hostile (Red)
- Actively pursuing player
- Alerts nearby enemies within 8 tile radius
- Uses optimal pathfinding to chase

## Tips & Strategies
1. **Know your enemy:** Study movement patterns and vision ranges
2. **Use blind spots:** Hide in monitoring dead zones to avoid detection
3. **Watch the queue:** Enemy movement predictions show 3 moves ahead
4. **Ambush bonus:** Attacking from blind spots grants +10 damage
5. **Avoid Admin Avatar:** Keep trace low to prevent spawning
6. **Status effects matter:** Carry Antivirus for virus/slow effects
7. **Target priority:** Eliminate Scanners first, avoid Firewalls
8. **Stealth over combat:** Killing alerts nearby enemies
