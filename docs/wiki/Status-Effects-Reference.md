# Status Effects Reference

Complete guide to all temporary status effects in Rogue Signal Protocol.

## Overview

Status effects are temporary conditions that modify player or enemy behavior. They're displayed in the **bottom status panel** with remaining turn counters.

**Key Features:**
- Multiple effects can stack simultaneously
- Turn counters shown next to effect names
- Effects expire automatically after duration
- Some effects can be removed early with Antivirus exploit
- Effects persist across turns but not across level transitions

---

## Positive Effects (Player Buffs)

Beneficial status effects that enhance your capabilities.

### 🔵 Traffic Masquerade (Invisibility)

**Source:** Traffic Masquerade exploit
**Duration:** 5 turns
**RAM Cost:** 2 | **Heat Cost:** 25

**Effect:**
- **Complete invisibility** to all enemies
- Walk past enemies without detection
- Enemies don't enter Alert or Hostile states
- Can move through enemy vision cones freely

**Limitations:**
- **Attacking breaks invisibility** immediately
- Using exploits doesn't break invisibility (except attacks)
- Movement and waiting are safe
- Look mode doesn't break invisibility

**Strategic Uses:**
- Bypass dense enemy clusters
- Reposition for ambushes
- Escape from pursuit
- Explore danger zones safely

**Tips:**
- Use before entering high-threat areas
- Combine with System Hop for maximum mobility
- Don't waste turns - move aggressively while active
- Plan ambush positions for when invisibility expires

---

### ⚡ Speed Boost

**Source:** Code hack (randomized color)
**Duration:** 3 turns
**Cost:** Find and use yellow/gold code hack (random each run)

**Effect:**
- **Two actions per turn** instead of one
- Can move twice, attack twice, or move + attack
- Exploit usage counts as one action
- Waiting counts as one action (wastes potential)

**Strategic Uses:**
- Rapid repositioning
- Double damage output in combat
- Quick escapes from danger
- Explore large areas fast

**Tips:**
- Don't waste on waiting - stay active
- Best used in combat for double attacks
- Combine with high-damage exploits
- Great for speedrun attempts

---

### 👁️ Enhanced Vision

**Source:** Code hack (randomized color)
**Duration:** 5 turns
**Cost:** Find and use purple/blue code hack (random each run)

**Effect:**
- **+2 vision range** added to player base vision (15 → 17 tiles)
- See enemies farther away
- Plan routes more effectively
- Spot threats before they spot you

**Strategic Uses:**
- Scouting ahead in unexplored areas
- Early enemy detection
- Better positioning for ambushes
- Safer navigation

**Tips:**
- Best used when exploring new areas
- Less useful in small rooms
- Combine with Threat Scan for maximum awareness
- Good for stealth-focused runs

---

### 🔥 Exploit Efficiency

**Source:** Code hack (randomized color)
**Duration:** 8 turns
**Cost:** Find and use orange/red code hack (random each run)

**Effect:**
- **-40% heat cost** for all exploits
- Rounded down (e.g., 25 heat → 15 heat)
- Applies to all exploits used during duration
- Passive cooling still works normally

**Strategic Uses:**
- Spam high-heat exploits (System Crash, Denial of Service, Logic Bomb)
- Combat-heavy approaches
- Rapid exploit chaining
- Heat management for long fights

**Tips:**
- Save high-heat exploits for when this is active
- Longest duration buff (8 turns) - use aggressively
- Great for Heat Master achievement (stay under 50 heat)
- Plan ahead: Activate before big fights

---

## Negative Effects (Debuffs)

Harmful status effects that hinder player capabilities.

### 💚 Virus

**Source:** Virus enemy contact
**Duration:** 3-10 turns (random)
**Damage:** 3 CPU per turn

**Effect:**
- **Continuous CPU damage** at start of each turn
- Damage can kill you if CPU reaches 0
- Duration randomized when applied
- Stacks with other sources of damage

**Curing:**
- **Antivirus exploit** removes immediately
- **Time:** Expires after duration
- **Cannot** be cured by CPU restoration

**Strategic Response:**
- **Priority:** Use Antivirus as soon as possible
- **Math:** 10 turns = 30 CPU damage (1/3 of base health!)
- **Avoid:** Stay away from Virus enemies (V symbol)
- **Early game:** More dangerous when CPU is lower

**Enemy Behavior:**
- Virus enemies (V) have 0 damage but apply virus on contact
- Contact = adjacent tile or same tile
- One touch can apply virus
- Virus enemies found on all 3 levels

**Tips:**
- Always equip Antivirus when Viruses are present
- Don't let virus stack with combat damage
- Avoid Virus enemies in tight corridors
- Use ranged attacks (Code Injection) to kill from safety

---

### 🐌 Movement Slowed

**Source:** Inhibitor enemy contact
**Duration:** Until cured or combat ends
**Effect Type:** Movement restriction

**Effect:**
- **Move every 2nd turn only**
- Turn 1: Can't move (can still use exploits, wait, inventory)
- Turn 2: Can move normally
- Pattern repeats until cured
- Exploit usage unaffected

**Curing:**
- **Antivirus exploit** removes immediately
- **Killing Inhibitor** that applied it may remove it
- **Time:** Persists until manually removed

**Strategic Response:**
- **Immediate threat:** Use Antivirus
- **Alternative:** Kill the Inhibitor enemy
- **Workaround:** Use System Hop (teleport isn't affected by slow)
- **Combat:** Can still attack even when can't move

**Enemy Behavior:**
- Inhibitor enemies (I) have 0 direct damage
- 30 CPU, 4 vision, random movement
- Applies slow on contact
- Found on all 3 levels

**Tips:**
- Slow is less dangerous than Virus (no damage)
- System Hop ignores movement restrictions
- Kite enemies even while slowed using exploit attacks
- Antivirus is lower priority than virus cure

---

### 🚫 Disabled (Enemy-Only)

**Source:** Denial of Service exploit (player uses on enemies)
**Duration:** 5 turns
**Targets:** Enemies in radius 1 of target point

**Effect on Enemies:**
- **Cannot move or act** for 5 turns
- Completely incapacitated
- Still visible and targetable
- Still counts toward enemy count

**Strategic Uses:**
- Crowd control for grouped enemies
- Create safe paths through enemy clusters
- Temporary removal of threats
- Buying time for positioning

**Notes:**
- Player cannot be disabled
- Exploit-only effect (no enemy can disable you)
- Duration fixed at 5 turns (generous)

---

### 😵 Stunned (Enemy-Only)

**Source:** System Crash exploit (affects all in radius 3, including you!)
**Duration:** 3 turns
**Targets:** All entities (player AND enemies) in radius

**Effect on Enemies:**
- **Cannot move or act** for 3 turns
- Similar to Disabled but shorter
- Applied via AOE damage ability

**Effect on Player:**
- **You also take 30 damage**
- **You are also stunned** for 3 turns
- High risk, high reward
- Desperation move only

**Strategic Uses:**
- Last resort when surrounded
- Take multiple enemies out of combat
- Buy time when overwhelmed
- Emergency escape (enemies stunned while you can't act, but then you escape after)

**Warning:**
- Self-damage can kill you!
- System Crash Warning dialogue prevents accidents (can be disabled in settings)
- Only use when surrounded and out of options

---

## Effect Interactions

### Stacking Rules

**Multiple Buffs:**
- ✅ Can have multiple positive effects simultaneously
- Example: Invisibility + Speed Boost + Enhanced Vision all active
- No diminishing returns

**Multiple Debuffs:**
- ✅ Can have Virus + Slowed simultaneously
- Both effects apply independently
- Very dangerous situation

**Buff + Debuff:**
- ✅ Can have positive and negative effects together
- Example: Speed Boost while Virus is ticking
- Must manage both

### Effect Priorities

**Critical (Remove ASAP):**
1. Virus (deals damage over time)
2. Stunned (can't act)

**Important (Remove When Convenient):**
3. Slowed (hinders movement)

**Low Priority:**
4. Disabled (enemy-only, working as intended)

### Antivirus Exploit

**What It Removes:**
- ✅ Virus
- ✅ Movement Slowed
- ❌ Does NOT remove buffs (only debuffs)
- ❌ Does NOT remove Disabled/Stunned (those expire naturally)

**Cost:**
- **RAM:** 2
- **Heat:** 25
- **Range:** 0 (self-only)
- **Targeting:** None (instant cleanse)

**When to Use:**
- Virus active and ticking
- Movement Slowed hindering strategy
- Both debuffs active (panic situation)

**When NOT to Use:**
- No debuffs active (wastes turn and heat)
- Debuff about to expire naturally (1 turn left)
- Better options available (kill Inhibitor instead)

---

## Status Effect Display

### Bottom Status Panel

**Location:** Bottom of screen in UI panel
**Format:** `Effect Name (X turns)`

**Examples:**
- `Invisible (5)` - Traffic Masquerade active for 5 more turns
- `Virus (7)` - Virus ticking for 7 more turns
- `Speed Boost (2)` - 2 turns of double actions left
- `Slowed` - Movement restriction active (no turn counter)

**Multiple Effects:**
Effects listed on separate lines or in sequence.

### Turn Counter Behavior

**Decrements:**
- At **end of each turn**
- Visible countdown lets you plan ahead

**Expiration:**
- Effect removes when counter reaches 0
- No lingering effects after expiration

**No Counter:**
- Some effects (Slowed) don't show turn counter
- Must be manually removed

---

## Strategic Effect Usage

### Offensive Combinations

**Speed Boost + High Damage:**
- Speed Boost → Attack twice with Buffer Overflow
- 40 + 40 = 80 damage in one turn!

**Invisibility + Ambush:**
- Traffic Masquerade → Position in blind spot → Wait for expire → Ambush attack
- Combines invisibility safety with blind spot damage bonus (+10)

**Exploit Efficiency + AOE Spam:**
- Exploit Efficiency (-40% heat) → Logic Bomb spam
- Normally 35 heat → 21 heat with buff
- Can use multiple times

### Defensive Combinations

**Invisibility + Speed Boost:**
- Invisible → Move twice per turn
- Maximum escape potential
- Cover huge distance safely

**Enhanced Vision + Threat Scan:**
- See enemies farther (Enhanced Vision +2)
- See their vision cones (Threat Scan)
- Ultimate awareness

**Invisibility + System Hop:**
- Already invisible → Teleport for repositioning
- Extremely safe

### Recovery Combinations

**Antivirus + CPU Node:**
- Clear virus debuff → Restore CPU
- Stops damage + heals
- Priority when low health

**Exploit Efficiency + Cooling Node:**
- Use high-heat exploits cheaply → Cool down
- Maximum exploit usage

---

## Tips & Best Practices

### For Status Management

1. **Track durations** - Plan around expiration times
2. **Use buffs aggressively** - Don't waste turns
3. **Cure debuffs quickly** - Don't let Virus tick for full duration
4. **Combine effects** - Synergies are powerful
5. **Save Antivirus** - Keep it equipped when Viruses present

### For Buff Optimization

1. **Speed Boost** - Plan 2 actions before using
2. **Invisibility** - Use for high-risk areas, not safe zones
3. **Enhanced Vision** - Best for exploration, not combat
4. **Exploit Efficiency** - Save high-heat exploits for this buff

### For Debuff Prevention

1. **Avoid Virus enemies** - Stay out of melee range
2. **Kill Inhibitors first** - Remove slow source
3. **Carry Antivirus** - Always available when needed
4. **Don't use System Crash** - Unless truly desperate

### For Combat

1. **Buff before boss fights** - Prepare with code hacks
2. **Debuff enemies** - Disabled and Stunned are powerful
3. **Time buffs carefully** - Don't activate too early
4. **Chain effects** - Use multiple buffs in sequence

---

## Effect Reference Table

| Effect | Type | Duration | Source | Removable | Notes |
|--------|------|----------|--------|-----------|-------|
| Traffic Masquerade | Buff | 5 turns | Exploit | Expires | Breaks on attack |
| Speed Boost | Buff | 3 turns | Code hack | Expires | 2 actions/turn |
| Enhanced Vision | Buff | 5 turns | Code hack | Expires | +2 vision range |
| Exploit Efficiency | Buff | 8 turns | Code hack | Expires | -40% heat cost |
| Virus | Debuff | 3-10 turns | Enemy | Antivirus | 3 CPU/turn damage |
| Movement Slowed | Debuff | Until cured | Enemy | Antivirus | Move every 2nd turn |
| Disabled | Debuff | 5 turns | Player exploit | Expires | Enemy-only |
| Stunned | Debuff | 3 turns | System Crash | Expires | Affects player too! |

---

For exploit details, see **[Exploit Database](Exploit-Database)**
For code hack system, see **[Code Hacks System](Code-Hacks-System)**
For enemy behaviors, see **[Enemy Database](Enemy-Database)**
