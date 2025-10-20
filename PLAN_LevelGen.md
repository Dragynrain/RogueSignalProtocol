# Level Generation Improvements - Detailed Plan

## Overview
This document outlines practical improvements to the procedural level generation system for RogueSignalProtocol. The current system creates functional but basic rectangular room-and-corridor layouts. These enhancements will make levels more interesting, varied, and better suited to stealth/combat gameplay without requiring massive architectural changes.

**Current System Summary:**
- 12-20 rectangular rooms (3-8 tiles each)
- MST-based connectivity + 2-4 extra connections
- L-shaped corridors
- Random shadow placement
- Basic 2-tile cover elements on grid
- 50x50 map size

---

## 1. Room Shape Variety

**Problem:** All rooms are rectangular, making the game feel repetitive and predictable.

**Solution: Add Non-Rectangular Room Templates**

### Implementation Strategy:
Create a room template system where each room type is defined by a pattern of tiles to carve out.

### Specific Room Types:

#### 1.1 L-Shaped Rooms
```
XXXXX...
XXXXX...
XXXXX...
XXX.....
XXX.....
```
**Gameplay Value:** Creates natural ambush corners and multiple approach angles. Good for stealth as enemies can't see the entire room at once.

**Implementation:**
- Generate two overlapping rectangles
- One large (e.g., 5x7), one small (e.g., 5x3) offset to create L
- 15% chance to replace rectangular room

#### 1.2 Cross/Plus-Shaped Rooms
```
...XXX...
...XXX...
XXXXXXXXX
XXXXXXXXX
XXXXXXXXX
...XXX...
...XXX...
```
**Gameplay Value:** Natural "junction" rooms with 4 cardinal exit points. Creates interesting sightlines and forces players to check multiple directions.

**Implementation:**
- Start with vertical rectangle
- Add horizontal rectangle intersecting at center
- 10% chance to replace rectangular room
- Minimum size: 7x7 total

#### 1.3 Irregular/Damaged Rooms
```
.XXXXX...
XXXXXXX..
XXXXXXXX.
XXXXXX...
XXXX.....
```
**Gameplay Value:** Adds visual variety and feels more "realistic" - looks like damaged network infrastructure. Creates unpredictable cover positions.

**Implementation:**
- Start with rectangular room
- Randomly remove 2-5 corner sections (1-3 tiles each)
- Don't remove more than 30% of total room area
- 20% chance to replace rectangular room

#### 1.4 Circular/Oval Rooms
```
..XXXXX..
.XXXXXXX.
XXXXXXXXX
XXXXXXXXX
XXXXXXXXX
.XXXXXXX.
..XXXXX..
```
**Gameplay Value:** No corners to hide in - forces different tactical approach. Good for "server core" themed rooms.

**Implementation:**
- Use midpoint circle algorithm or approximation
- Fill interior with flood fill
- Minimum radius: 3 tiles
- 10% chance to replace rectangular room

#### 1.5 Pillar Rooms (Server Halls)
```
XXXXXXXXX
X.X.X.X.X
X.......X
X.X.X.X.X
X.......X
X.X.X.X.X
XXXXXXXXX
```
**Gameplay Value:** Excellent for stealth gameplay - many breaking points for line of sight. Creates tactical cover opportunities.

**Implementation:**
- Start with rectangular room
- Place 1-tile "pillar" walls in grid pattern
- Grid spacing: 2-3 tiles
- Only apply to larger rooms (7x7+)
- 15% chance for large rooms

---

## 2. Corridor Improvements

**Problem:** All corridors are 1-tile wide L-shapes, making them feel samey and limiting tactical options.

### 2.1 Variable Width Corridors

**Narrow Corridors (1 tile):**
- 50% of corridors
- Good for choke points
- Forces single-file movement

**Medium Corridors (2 tiles wide):**
- 35% of corridors
- Allows side-by-side movement
- Can place cover in corridor

**Wide Corridors (3 tiles wide):**
- 15% of corridors
- Feels like a hallway/transitional space
- Good for patrol routes

**Implementation:**
- When carving corridor, remove walls in N-wide path
- For L-shapes, maintain width through both segments
- Ensure pathfinding still works (TCOD handles multi-tile corridors fine)

### 2.2 T-Junction and 4-Way Intersections

Instead of just connecting rooms, create explicit junction points where 3+ corridors meet.

**Implementation:**
- After MST connections, identify corridor intersection points
- 30% chance to expand intersection into 3x3 or 5x5 junction room
- Place shadows in corners of junctions (stealth advantage)
- Good spots for ambushes or quick escapes

### 2.3 Corridor Alcoves

Small 1-2 tile indentations along corridors for hiding.

```
#######
#....A#  <- A = alcove (1 tile indentation)
#.....#
#....A#
#######
```

**Implementation:**
- After carving corridors, identify straight segments (4+ tiles)
- 40% chance to add 1-2 alcoves along the corridor
- Alcove = remove 1 wall tile adjacent to corridor
- Place shadow in alcove (stealth hiding spot)

### 2.4 Curved Corridors

Add occasional curved/diagonal corridors instead of only L-shapes.

**Implementation:**
- For 20% of corridor connections
- Use Bresenham's line algorithm from room1 center to room2 center
- Widen line to corridor width
- Creates more organic, less grid-aligned feel

---

## 3. Enhanced Cover and Shadow System

**Problem:** Cover is placed on regular grid (every 8 tiles) with 30% chance. Shadows are randomly scattered. Neither feels strategic.

### 3.1 Strategic Cover Clusters

Instead of isolated 2-tile walls, create meaningful cover positions.

**Cover Patterns:**

**Small Cluster (3-4 tiles):**
```
##.
##.
```

**L-Shaped Cover:**
```
###
#..
```

**Scattered Cover (5-6 tiles across larger area):**
```
.#....#.
........
..#..#..
```

**Implementation:**
- Identify large open areas (10x10+ contiguous floor space)
- Instead of grid placement, use Poisson disc sampling for natural distribution
- 50% chance to place cover cluster in large open areas
- Place 2-4 clusters per open area depending on size
- Ensure cover doesn't block critical paths

### 3.2 Defensive Positions

Create pre-made tactical positions that combine cover + shadows + sightlines.

**Example Defensive Position:**
```
#####
#.S.#  S = Shadow, # = Cover walls
#...#
##.##
```

**Implementation:**
- Template-based: define 3-5 defensive position patterns
- Place 1-3 per level in strategic locations:
  - Near gateway (final approach)
  - Near high-value items (code hacks, upgrades)
  - In large rooms
- Ensure shadows are placed in positions that provide stealth advantage

### 3.3 Shadow Zones

Instead of random scatter, create contiguous shadow areas that feel like "dark sectors" of the network.

**Implementation:**
- Identify room clusters (3+ rooms close together)
- 25% chance to designate as "shadow zone"
- Fill 60-80% of floor tiles in those rooms with shadows
- Connect shadow rooms with shadowed corridors
- Creates distinct "stealth path" vs "exposed path" choice

### 3.4 Wall-Adjacent Shadows

Shadows should prefer edges of rooms and along walls (more realistic and tactical).

**Implementation:**
- When placing shadows in room:
  - 60% chance to place along walls (1 tile from wall)
  - 40% chance to place in interior
- Creates natural cover + shadow combinations
- Makes stealthing along walls more viable

---

## 4. Layout Patterns and Connectivity

**Problem:** MST creates minimal connectivity with some extra paths, but no intentional structure or flow.

### 4.1 Hub-and-Spoke Patterns

Designate 1-2 large central "hub" rooms that many other rooms connect to.

**Implementation:**
- After creating all rooms, identify 1-2 most central rooms
- Expand these to larger size (10x12 tiles)
- Force 4-6 connections from hub to other rooms
- Creates natural gathering point and landmark
- Good for placing major objectives or tough encounters

### 4.2 Looping Paths

Ensure players can take circular routes, not just tree-structured paths.

**Implementation:**
- After MST + extra paths, analyze graph
- Identify rooms with only 1 connection (leaf nodes)
- Add 2-3 more connections to create loops
- Target: at least 3-4 distinct loops per level
- Greatly enhances stealth options (can evade by looping around)

### 4.3 Choke Points

Deliberately create bottleneck rooms/corridors.

**Implementation:**
- Identify critical path from spawn to gateway
- Select 2-3 rooms along this path
- Reduce exits to 1-2 (ensure still reachable via loop paths)
- Place tougher enemies near choke points
- Creates tense "must pass through" moments

### 4.4 Linear Sections + Open Sections

Vary the density and structure of different map areas.

**Linear Section (Chain of Rooms):**
```
[Room1] -> [Room2] -> [Room3] -> [Room4]
```

**Open Section (Many Interconnections):**
```
    [Room5]
   /   |    \
[Room6][Room7][Room8]
   \   |    /
    [Room9]
```

**Implementation:**
- Divide map into 2-3 zones
- Randomly assign zone type (linear, open, or mixed)
- When placing rooms, bias placement toward zone characteristics
- Adjust connection algorithm to respect zone type

---

## 5. Strategic Element Placement

**Problem:** Special nodes, items, and gateway are placed randomly with simple distance checks.

### 5.1 Gateway Placement Strategies

Instead of always "far from spawn," vary the gateway placement to change level flow.

**Strategy A: Far Corner (Current - 40% chance)**
- Gateway in opposite corner from spawn
- Long trek across level

**Strategy B: Central Hub (30% chance)**
- Gateway in or near central hub room
- Must fight through to center

**Strategy C: Hidden Dead-End (20% chance)**
- Gateway at end of longest branch
- Must explore to find

**Strategy D: Gauntlet (10% chance)**
- Gateway along edge but requires passing through choke point
- More combat-focused

**Implementation:**
- Select strategy at level generation start
- Constrain gateway placement based on chosen strategy
- Communicate strategy subtly via level structure

### 5.2 Item Placement Clustering

Instead of uniform distribution, create "loot rooms" and "empty areas."

**Implementation:**
- Identify 20% of rooms as "high value"
- Place 2-3x more items in these rooms
- Other rooms may have 0-1 items
- Rewards exploration but creates risk/reward (enemies may patrol loot areas)

### 5.3 Objective-Oriented Placement

Place special nodes in tactically interesting positions.

**Cooling Nodes:**
- Place in high-traffic areas (central corridors)
- Forces risk to get reward

**CPU Nodes:**
- Place in safer, peripheral rooms
- Rewards thorough exploration

**Ghost Nodes:**
- Place along stealth paths (shadow zones)
- Encourages stealth gameplay

---

## 6. Level Personality & Themes

**Problem:** All levels feel similar structurally. Level 1/2/3 should feel different beyond just enemy count.

### 6.1 Per-Level Generation Parameters

**Level 1 (Corporate Network) - "Organized Chaos"**
- More regular rectangular rooms (70% rectangular)
- Wider corridors (more 2-3 tile wide)
- Moderate shadow coverage (current)
- More pillar rooms (office server rooms)
- Hub-and-spoke layout preference

**Level 2 (Research Network) - "Experimental"**
- More irregular rooms (50% non-rectangular)
- Variable corridor widths
- Lots of L-shaped and cross rooms (labs and test chambers)
- More defensive positions (security conscious)
- Mixed linear/open layout

**Level 3 (Military Network) - "Fortified"**
- More choke points
- More cover clusters (defensive positions everywhere)
- Shadow zones (cloaking systems)
- Circular rooms (command centers)
- More looping paths (redundant systems)
- Gauntlet or central hub gateway placement more likely

**Implementation:**
- Pass level number to room generation
- Adjust probabilities for room types
- Adjust corridor widths
- Adjust shadow strategy
- Adjust layout pattern weights

### 6.2 Landmark Rooms

Create 1-2 distinctive rooms per level that stand out.

**Ideas:**
- **The Server Core:** Large circular room with pillar pattern, gateway inside
- **The Vault:** Small room behind narrow corridor with upgrade
- **The Junction:** Massive cross-shaped room connecting 6+ other rooms
- **The Maze:** Dense cluster of small rooms with many connections
- **The Arena:** Large open room with scattered cover, major fight

**Implementation:**
- Select 1-2 landmark types per level
- Place during room generation
- Bias special item placement toward landmarks
- Ensure landmarks are on critical paths (not hidden in corner)

---

## 7. Implementation Priority Recommendations

If implementing incrementally, suggest this order:

**Phase 1: Quick Wins (Highest Impact, Lowest Effort)**
1. Variable corridor widths (2.1)
2. Wall-adjacent shadows (3.4)
3. Corridor alcoves (2.3)
4. Strategic cover clusters (3.1)

**Phase 2: Room Variety (High Impact, Medium Effort)**
5. L-shaped rooms (1.1)
6. Irregular/damaged rooms (1.3)
7. Pillar rooms (1.5)
8. Per-level generation parameters (6.1)

**Phase 3: Layout Improvements (High Impact, Medium Effort)**
9. Looping paths (4.2)
10. Gateway placement strategies (5.1)
11. Shadow zones (3.3)
12. Hub-and-spoke patterns (4.1)

**Phase 4: Advanced Features (Medium Impact, Higher Effort)**
13. T-junctions and 4-way intersections (2.2)
14. Cross-shaped rooms (1.2)
15. Circular rooms (1.4)
16. Landmark rooms (6.2)
17. Objective-oriented placement (5.3)

**Phase 5: Polish (Nice to Have)**
18. Curved corridors (2.4)
19. Defensive positions (3.2)
20. Item placement clustering (5.2)
21. Choke points (4.3)
22. Linear/open sections (4.4)

---

## 8. Technical Considerations

### 8.1 Pathfinding Compatibility
- TCOD pathfinding handles all proposed changes (multi-tile corridors, irregular rooms, loops)
- Ensure all rooms remain connected (verify with graph traversal after generation)

### 8.2 FOV Compatibility
- TCOD FOV works with any wall configuration
- More irregular walls = more interesting FOV shapes (GOOD for stealth)
- Pillar rooms create natural FOV-breaking elements

### 8.3 Testing Strategy
- After each feature, verify:
  - All rooms reachable from spawn
  - Gateway reachable from spawn
  - No completely enclosed areas
  - Enemy pathfinding works
  - Player spawn never in wall
- Add visualization debug mode to see room types, shadow zones, etc.

### 8.4 Performance
- All proposed changes are O(rooms) or O(floor_tiles)
- No complex algorithms that would slow generation
- Should remain imperceptible to player (<100ms total)

### 8.5 Backward Compatibility
- All changes are in LevelGenerator class
- No changes to save format or game map structure
- Can be incrementally enabled via config flags

---

## 9. Configuration Additions

Recommend adding to `game_config.json` for easy tuning:

```json
"room_generation": {
  "room_type_weights": {
    "rectangular": 0.45,
    "l_shaped": 0.15,
    "irregular": 0.20,
    "cross": 0.10,
    "circular": 0.10
  },
  "corridor_width_weights": {
    "narrow": 0.50,
    "medium": 0.35,
    "wide": 0.15
  },
  "shadow_strategy": "zones",  // "random" or "zones"
  "cover_strategy": "clusters",  // "grid" or "clusters"
  "layout_pattern": "mixed",  // "linear", "open", "mixed"
  "enable_landmarks": true,
  "enable_alcoves": true,
  "pillar_room_chance": 0.15
}
```

Per-level overrides:
```json
"network_configs": {
  "1": {
    "level_generation": {
      "room_type_weights": {"rectangular": 0.70, ...},
      "layout_pattern": "hub_spoke"
    }
  }
}
```

---

## 10. Expected Outcomes

**Gameplay Impact:**
- More varied levels reduce repetition across runs
- Better stealth options (shadow zones, alcoves, cover clusters)
- More tactical combat (defensive positions, choke points)
- Clearer level identity (level 1 feels different from level 3)
- Better risk/reward (loot clustering, strategic placement)

**Technical Impact:**
- Minimal performance impact (<50ms added to generation)
- Maintains all existing systems (FOV, pathfinding, saves)
- Highly configurable via JSON
- Incremental implementation possible

**Player Experience:**
- "This level feels different!" (positive variety)
- "I can approach this multiple ways" (tactical depth)
- "Level 3 feels more dangerous than level 1" (progression)
- "I found a great hiding spot!" (discovery and mastery)

---

## Conclusion

These improvements transform level generation from "functional but basic" to "varied and tactically interesting" without requiring massive architectural changes. The recommendations are practical, implementable incrementally, and directly support the game's stealth/combat core gameplay.

Each improvement has clear gameplay value and technical implementation notes. Priority phases allow for staged rollout. Configuration options ensure fine-tuning without code changes.

The result will be levels that feel hand-crafted in their tactical design while remaining fully procedural and infinitely varied.
