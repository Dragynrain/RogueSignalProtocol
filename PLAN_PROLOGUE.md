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
e = Code Injection    + = Door

############################  Row 0
#@..########################  Row 1: SECTION 1 - spawn at (1,1)
#...########################  Row 2
#.X.########################  Row 3: X at (2,3) - melee teaching
###+########################  Row 4: door at (3,4)
#...........################  Row 5: SECTION 2 - patrol timing
#...P.......################  Row 6: P at (4,6) patrols x=5-11
#...........################  Row 7
###+########################  Row 8: door at (3,8)
#ss.S.......################  Row 9: SECTION 3 - S at (4,9), blind spots (1-2,9)
#sss........################  Row 10: blind spots (1-3,10)
#sss########################  Row 11: blind spots (1-3,11)
#...P.r.....################  Row 12: P at (4,12) patrols x=5-11, r at (6,12)
###+########################  Row 13: door at (3,13)
#c.e........################  Row 14: SECTION 4 - c at (1,14), e at (3,14)
#...#.P.....################  Row 15: wall at (4,15), P at (6,15) behind wall
###+########################  Row 16: door at (3,16)
#sss........################  Row 17: SECTION 5 - blind spots start
#sss.g......################  Row 18: g at (5,18)
#sss........################  Row 19
#sss........################  Row 20
#sss.P..........+.........>#  Row 21: P at (5,21) patrols x=6-14, gateway at (26,21)
#...........################  Row 22
############################  Row 23
```

---

## Section Teaching Goals

| Section | Rows | Teaching Focus | Layout Features |
|---------|------|----------------|-----------------|
| 1 | 0-4 | **Melee combat** | X (5 HP) blocks door - bump to attack |
| 2 | 5-8 | **Turn timing** | P patrols corridor - wait for opening |
| 3 | 9-12 | **FOV + Blind spots** | S has vision 5; blind spots at (1-3, 9-11) work at range > 1 |
| 4 | 13-16 | **Ranged combat** | Wall at (4,15) blocks melee; exploit pickup at (3,14) |
| 5 | 17-23 | **Synthesis** | Ghost node, stealth path via blind spots, final patrol to gateway |

---

## Design Philosophy

**Show don't tell** - teaches through layout and reactive internal voice, not popups.

| Instead of...                    | We do...                                           |
|----------------------------------|---------------------------------------------------|
| "Walk into enemies to attack"    | X blocks the only door with 5 HP - must bump-attack |
| "Enemies move when you move"     | P blocks corridor - player observes movement |
| "Blind spots hide at range"      | S vision range 5, blind spots work only at range > 1 |
| "Use exploits for ranged"        | Wall blocks melee path to P; exploit is pickup nearby |

**Constraints:**
- Uses REAL game mechanics only
- Player CAN kill any enemy - stealth encouraged, not forced
- Blind spots only work at range > 1

---

## Patrol Routes (Fixed, Deterministic)

Routes defined in `fixed_levels.py`. Patrols avoid x=3 (door column) to create safe crossing windows.

| Spawn Position | Waypoints | Section |
|----------------|-----------|---------|
| (4, 6) | x=5 to x=11 | Section 2 |
| (4, 12) | x=5 to x=11 | Section 3 |
| (6, 15) | x=6 to x=11 | Section 4 (behind wall) |
| (5, 21) | x=6 to x=14 | Section 5 (final) |

---

## Death Hints (First death per section)

| Section | Hint |
|---------|------|
| 1 | "Walk into them to attack. That one looked weak." |
| 2 | "Next time, wait for an opening..." |
| 3 | "Distance matters. Too close and they see through everything." |
| 4 | "There must be a way to reach them from here..." |
| 5 | "Patience. Watch the pattern." |
| Heat | "Overheated... those nodes might help next time." |

---

## Mechanic Reference

**Enemy States:** UNAWARE -> ALERT (1 turn grace) -> HOSTILE

**Blind Spots:** Hide at range > 1 only. Adjacent enemies see through.

**Prologue Thoughts:** 23 reactive triggers in `prologue_thoughts.py`

**Visibility Status:** CONCEALED/EXPOSED/TOO CLOSE indicator (prologue only)

---

## Key Files

| File | Purpose |
|------|---------|
| `fixed_levels.py` | Layout + patrol routes + section boundaries |
| `fixed_generator.py` | Parses layout, creates entities |
| `coordinator.py` | Fixed layout check, assigns patrol routes |
| `prologue_thoughts.py` | Reactive tutorial messages |
| `narrative_content.json` | Thought text and death hints |
