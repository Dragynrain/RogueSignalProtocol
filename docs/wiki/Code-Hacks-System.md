# Code Hacks System

Complete guide to the randomized beneficial pickup system in Rogue Signal Protocol.

## Overview

**Code Hacks** (also called **Data Codes**) are randomized beneficial pickups found throughout each level. They appear as **`!` symbols** on the map and provide temporary buffs or resource restoration.

**Key Features:**
- **Color-coded mystery system** - same color = same effect (per session)
- **6 different effect types** with randomized color assignments each run
- **Discovery tracking** - learn what each color does on first use
- **Multiple pickups** - 27 total across all 3 levels
- **Instant effects** - activate immediately when collected

---

## Appearance & Collection

### Visual Representation
- **Symbol:** `!` (exclamation mark)
- **Color:** Random RGB colors assigned to each effect type
- **Location:** Scattered throughout levels in rooms and corridors
- **Collection:** Walk over the tile to collect automatically

### Map Symbol
**In-game:**
- Glyph mode: `!` character
- Graphics mode: Data code sprite

**Look Mode Description:**
- Name: "Data Code"
- Description: "Encrypted payload with randomized beneficial effects. Collect to discover its purpose."

---

## The 6 Code Hack Types

Each run assigns random colors to these 6 effects. Same color = same effect throughout the session.

### 1. 💊 Restore CPU
**Effect:** Restores 30-40 CPU (randomized amount)
**Use Case:** Emergency healing, sustain during combat
**Value:** High - equivalent to 1.5-2 CPU nodes
**Tips:**
- Save for emergencies (don't use at full health)
- More valuable on Level 3 (only 2 CPU nodes)
- Can overheal beyond max CPU temporarily? **No** - caps at max

### 2. 🧊 Reduce Heat
**Effect:** Instant -40°C heat reduction
**Use Case:** Heat management, enable exploit spam
**Value:** Very High - equivalent to 2 cooling nodes
**Tips:**
- Use before heat-heavy exploit chains
- Enables multiple high-heat exploits in succession
- Critical for Heat Master achievement (stay under 50 heat)
- More valuable than CPU restore on average

### 3. 👻 Reduce Trace Level
**Effect:** -25% trace reduction
**Use Case:** Detection management, prevent Admin Avatar spawn
**Value:** High - equivalent to 1.25 ghost nodes
**Tips:**
- Use when trace exceeds 50%
- Critical on Level 3 to avoid Admin Avatar
- Combines with Log Wiper exploit (-30%) for massive trace reduction
- Essential for No Trace achievement (stay under 50%)

### 4. ⚡ Speed Boost
**Effect:** 2 actions per turn for 3 turns
**Use Case:** Combat burst, rapid repositioning, exploration
**Value:** Situational but powerful
**Duration:** 3 turns
**Tips:**
- Use in combat for double attacks
- Don't waste on waiting - stay active
- Great for speedrun attempts
- Combine with high-damage exploits for burst

### 5. 👁️ Enhanced Vision
**Effect:** +2 vision range for 5 turns
**Use Case:** Exploration, scouting, early threat detection
**Value:** Moderate - useful for awareness
**Duration:** 5 turns
**Tips:**
- Best when exploring new areas
- Less useful in small rooms
- Combine with Threat Scan for maximum awareness
- Good for stealth-focused runs

### 6. 🔥 Exploit Efficiency
**Effect:** -40% heat cost for all exploits for 8 turns
**Use Case:** Exploit spam, combat-heavy approaches
**Value:** Very High in combat situations
**Duration:** 8 turns (longest buff)
**Tips:**
- Save high-heat exploits for when active
- Enables aggressive exploit usage
- Great for Heat Master achievement
- Plan ahead: Activate before big fights

---

## Color Randomization System

### How It Works

**Per Session Randomization:**
- Each new game assigns random colors to the 6 effect types
- Colors remain consistent throughout that entire run
- Colors reset on death or new game start

**Discovery Mechanic:**
- First pickup: "Discovered [Effect Name]!"
- Subsequent pickups of same color: "Collected [Effect Name]"
- Inventory shows discovered effects
- Unknown colors show as "Unknown Code Hack"

**Color Assignment:**
- RGB colors chosen from game's color palette
- Visually distinct for identification
- Same color always = same effect in that run

### Learning the Colors

**Method 1: Trial and Discovery**
- Collect code hacks as you find them
- Learn what each color does through use
- Build mental map of colors for that run

**Method 2: Inventory Inspection**
- Collected code hacks shown in inventory
- Discovered effects labeled
- Unknown effects show as "???"

**Method 3: Pattern Recognition**
- After using several, predict remaining colors
- Process of elimination
- Experienced players learn to identify quickly

---

## Distribution Across Levels

### Level 1: Corporate Network
- **Total Code Hacks:** 12
- **Abundance:** High
- **Strategy:** Experiment to learn colors early
- **Recommendation:** Use liberally - plenty available

### Level 2: Government System
- **Total Code Hacks:** 10
- **Abundance:** Moderate
- **Strategy:** Use strategically for key moments
- **Recommendation:** Save high-value ones (heat, CPU, trace)

### Level 3: Military Backbone
- **Total Code Hacks:** 5
- **Abundance:** Scarce
- **Strategy:** Emergency use only
- **Recommendation:** Critical resource management required

**Total Across Run:** 27 code hacks
**Guaranteed 6 Types:** Yes, if you collect enough (distribution ensures all 6 types appear)

---

## Strategic Usage

### Priority Tier List

**S-Tier (Always Use Strategically):**
1. **Reduce Heat** (-40°C) - Most universally valuable
2. **Restore CPU** (30-40 HP) - Life-saving potential

**A-Tier (High Value, Situational):**
3. **Reduce Trace** (-25%) - Critical on Level 3
4. **Exploit Efficiency** (-40% heat, 8 turns) - Amazing for combat

**B-Tier (Useful, Less Critical):**
5. **Speed Boost** (2 actions, 3 turns) - Situational power
6. **Enhanced Vision** (+2 range, 5 turns) - Nice but not essential

### When to Use Each Type

**Restore CPU:**
- ✅ When CPU below 50%
- ✅ Before boss encounter
- ✅ After taking heavy damage
- ❌ At full health (waste)
- ❌ When CPU nodes available nearby

**Reduce Heat:**
- ✅ Before exploit-heavy combat
- ✅ When heat above 70
- ✅ To enable back-to-back high-heat exploits
- ❌ At low heat (waste)
- ❌ When cooling nodes available nearby

**Reduce Trace:**
- ✅ When trace exceeds 50%
- ✅ On Level 3 to prevent Admin Avatar
- ✅ Before heavy combat (reduces trace gain)
- ❌ Below 30% trace (not urgent)
- ❌ When ghost nodes available

**Speed Boost:**
- ✅ In combat for double attacks
- ✅ For rapid repositioning
- ✅ When surrounded
- ❌ In safe areas (waste potential)
- ❌ Right before level transition

**Enhanced Vision:**
- ✅ When exploring new areas
- ✅ In large open rooms
- ✅ Combined with Threat Scan
- ❌ In small rooms (limited benefit)
- ❌ When already using Threat Scan

**Exploit Efficiency:**
- ✅ Before major combat encounter
- ✅ When planning exploit-heavy strategy
- ✅ On Level 3 (scarce resources)
- ❌ In stealth-only approaches
- ❌ When not planning to use exploits

---

## Achievement Interactions

### Code Collector Achievement
**Requirement:** Use all 6 code hack types in one run
**Difficulty:** Medium
**Strategy:**
- Collect and test all unknown colors on Level 1
- Track which types you've used
- Ensure you use at least one of each before finishing Level 3
- 27 total available makes this easier

### Resource Efficient Achievement
**Requirement:** Win without using any code hacks
**Difficulty:** Medium-Hard
**Strategy:**
- **Avoid picking up** `!` symbols entirely
- Use cooling/CPU/ghost nodes instead
- More challenging than expected - those buffs are tempting!
- Conflicts with Code Collector in same run

### Pure Skill Achievement (Hidden)
**Requirement:** Win without exploits or code hacks
**Difficulty:** Extreme
**Includes:** Cannot use code hacks
**Strategy:** Same as Resource Efficient but also no exploits

---

## Inventory Management

### Code Hack Storage
- **Collected code hacks** shown in inventory (I key)
- **Stacking:** Multiple of same color stack
- **Usage:** Select in inventory → Press Enter to use
- **Instant effect:** Activates immediately when used

### Inventory Display
**Format:**
```
Code Hack - [Color Name]
Effect: [Effect Description]
Quantity: [X]
```

**Examples:**
```
Code Hack - Crimson
Effect: Restores 30-40 CPU
Quantity: 2
```

```
Code Hack - Azure
Effect: Unknown
Quantity: 1
```

### Using From Inventory
1. Press **I** to open inventory
2. Navigate to code hack with **Up/Down**
3. Press **Enter** to use
4. Effect activates instantly
5. Inventory closes automatically

---

## Tips & Best Practices

### For New Players
1. **Collect everything on Level 1** - Learn all 6 colors
2. **Test unknowns in safe situations** - Not during combat
3. **Note which colors are which** - Mental tracking
4. **Save valuable ones** - Heat/CPU/Trace for Level 3
5. **Don't hoard excessively** - Use them, you'll find more

### For Experienced Players
1. **Quick color identification** - Recognize patterns
2. **Strategic stockpiling** - Save S-tier for Level 3
3. **Buff stacking** - Combine with exploits
4. **Achievement planning** - Know which to avoid for Resource Efficient
5. **Efficiency routing** - Collect on optimal paths

### For Speedrunners
1. **Skip most code hacks** - Only collect if on direct path
2. **Exception:** Speed Boost - always grab if convenient
3. **Reduce Heat** can enable aggressive combat routing
4. **Don't explore for code hacks** - Time waste

### For Challenge Runs
**Untouchable:** Restore CPU still useful (for margin)
**No Trace:** Reduce Trace is essential
**Heat Master:** Reduce Heat and Exploit Efficiency critical
**Resource Efficient:** Avoid all code hacks entirely
**Pure Skill:** Avoid all code hacks entirely

---

## Common Questions

**Q: Do code hacks carry between levels?**
A: Yes! Collected code hacks in inventory persist across level transitions.

**Q: What if I don't find all 6 types?**
A: Distribution ensures enough variety. Collect 10+ and you'll likely see all 6.

**Q: Can I drop code hacks?**
A: No. Once collected, they stay in inventory until used.

**Q: Do colors ever repeat between runs?**
A: Colors are randomized each session, but probability means occasional repeats.

**Q: What if I forget which color is which?**
A: Check inventory - discovered effects are labeled. Or test one to remember.

**Q: Can enemies use code hacks?**
A: No. Player-only items.

**Q: What happens if I die with unused code hacks?**
A: Lost forever with permadeath. Use them or lose them!

**Q: Can I use code hacks while invisible?**
A: Yes! Using code hacks doesn't break Traffic Masquerade invisibility.

---

## Advanced Tactics

### Buff Stacking
- **Speed Boost + Exploit Efficiency** = Spam exploits twice per turn cheaply
- **Enhanced Vision + Threat Scan** = Ultimate awareness
- **Multiple CPU Restores** = Full heal from critical damage

### Resource Conversion
Think of code hacks as "portable nodes":
- Reduce Heat = 2 cooling nodes
- Restore CPU = 1.5 CPU nodes
- Reduce Trace = 1.25 ghost nodes

### Optimal Collection Routes
1. Explore Level 1 thoroughly (12 available)
2. Collect 6-8 on Level 2 (10 available)
3. Cherry-pick 2-3 on Level 3 (5 available)
4. Total: 10-13 code hacks used per run

### Emergency Reserve
Always keep in inventory:
- 1x Restore CPU (emergency heal)
- 1x Reduce Heat (emergency cooldown)
- Rest can be used freely

---

## Synergies

### With Exploits
- **Exploit Efficiency + Logic Bomb** = Cheap AOE spam
- **Speed Boost + Buffer Overflow** = 80 damage in one turn
- **Reduce Heat + System Crash** = Make desperation move safer

### With Nodes
- **Reduce Heat before Cooling Node** = Maximize heat headroom
- **Restore CPU before CPU Node** = Overheal isn't possible
- **Reduce Trace before Ghost Node** = Stack trace reduction

### With Achievements
- **Code Collector** = Use all 6 types
- **Resource Efficient** = Use zero code hacks
- **Heat Master** = Reduce Heat essential
- **No Trace** = Reduce Trace essential

---

For related systems:
- **[Status Effects Reference](Status-Effects-Reference)** - Buff durations and effects
- **[Exploit Database](Exploit-Database)** - Abilities that synergize with code hacks
- **[Achievement Guide](Achievement-Guide)** - Code Collector and Resource Efficient achievements
- **[Gameplay Mechanics](Gameplay-Mechanics)** - Core systems overview
