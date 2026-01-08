# Prologue Level Design Reference

## Status: IMPLEMENTED

All phases complete. This document is a design reference for the tutorial level.

---

## Layout (28x24 tiles)

```
Legend:
# = Wall           . = Floor          s = Blind spot
@ = Player spawn   > = Gateway        c = Cooling node
r = CPU recovery   g = Ghost node     S = Scanner (STATIC, vision 5)
X = Damaged Scanner (STATIC, 5 HP, 0 damage)
P = Patrol (fixed routes)
e = Code Injection    E = Threat Scan    d = Code hack

############################
#@..##....+.e.............#  SECTION 1: Observation + Melee
#..X##....#...............#    X blocks exit - must bump-attack
#.#.+..P..#...............#    P at (7,3) patrols corridor after X
#..##.....#...............#    Player must wait/time passage
####+#####################
#sssS#....................#  SECTION 2: Blind Spot Trap
#....#....................#    Wall at (5,6) blocks quick bypass
#....#....................#    Blind spots (1-3,6) adjacent to S = TOO CLOSE
#..ss#....................#    Safe blind spots at (3-4,9-10) range 3+
#..ss#....................#    Door at (5,11) exits to right corridor
#....+....................#
####+#########+###########
#..r.+.........+....sss...#  SECTION 3: Alert Grace Period
#.d..#....P....#....sss...#    P patrols (6,14)-(13,14) - crosses entry
#....#....+....#..XE.ss...#    Rewards on main path: r,d
#....#....+....+....sss...#
################....###+###
#..c.+.....#..............#  SECTION 4: Ranged Combat
#....#.....#......P.......#    P at (18,19) visible from corridor
#....+.....+..............#    Wall at x=11 creates longer melee path
####+######+..........+.###    Cooling node c at (3,18) via left door
#sss.+.....g.......#....+>#  SECTION 5: Synthesis
#sss.#.........P...#..sss.#    P patrols (12,23)-(18,23)
############################    LEFT=stealth+ghost, RIGHT=direct
```

---

## Design Philosophy

**Show don't tell** - teaches through layout and reactive internal voice, not popups.

| Instead of...                    | We do...                                           |
|----------------------------------|---------------------------------------------------|
| "Enemies move when you move"     | P blocks corridor after X - player observes movement |
| "Blind spots hide at range"      | Wall forces blind spot path - adjacent S = TOO CLOSE |
| "Alert gives 1 turn to escape"   | P spots player crossing, they flee to break LOS    |
| "Use exploits for ranged"        | P visible at range 5 from corridor + wall delays melee |

**Constraints:**
- Uses REAL game mechanics only
- Player CAN kill any enemy - stealth encouraged, not forced
- Blind spots only work at range > 1

---

## Mechanic Reference

**Enemy States:** UNAWARE -> ALERT (1 turn grace) -> HOSTILE

**Blind Spots:** Hide at range > 1 only. Adjacent enemies see through.

**Patrol Routes:** Fixed waypoints in prologue (not random):
- Section 1: (5,3)-(9,3)
- Section 3: (6,14)-(13,14)
- Section 4: (17,19)-(20,19)
- Section 5: (12,23)-(18,23)

**Prologue Thoughts:** Reactive triggers in `prologue_thoughts.py`

**Visibility Status:** CONCEALED/EXPOSED/TOO CLOSE indicator (prologue only)

---

## Key Files

| File | Purpose |
|------|---------|
| `fixed_levels.py` | Layout + patrol routes |
| `fixed_generator.py` | Parses layout, creates entities |
| `coordinator.py` | Fixed layout check, assigns patrol routes |
| `prologue_thoughts.py` | Reactive tutorial messages |
