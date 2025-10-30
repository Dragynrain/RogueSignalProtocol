# Metrics Tracking System - Implementation Plan

**Goal:** Track all gameplay events to support future achievement system and provide game balance analytics.

**Approach:** Lightweight custom solution using Python stdlib only. Dual storage (JSON + SQLite) for debugging and analytics. Survives permadeath for lifetime statistics.

---

## Phases

**Phase 1: Core Metrics Infrastructure** (Medium complexity)
- Dependencies: None
- Risk: Low - pure data structures and persistence

**Phase 2: Combat & Death Tracking** (Low complexity)
- Dependencies: Phase 1
- Risk: Low - simple hook points already identified

**Phase 3: Movement & Progression Tracking** (Low complexity)
- Dependencies: Phase 1
- Risk: Low - straightforward event capture

**Phase 4: Item & Exploit Tracking** (Medium complexity)
- Dependencies: Phase 1
- Risk: Medium - multiple hook points across inventory system

**Phase 5: Persistence & Testing** (Low complexity)
- Dependencies: All previous phases
- Risk: Low - integration and validation

---

## Phase 1: Core Metrics Infrastructure

**Goal:** Create data structures and storage layer.

### Data Model

Track per-session metrics:
```python
@dataclass
class SessionMetrics:
    session_id: str
    timestamp_start: float
    victory: bool = False

    # Combat
    enemies_killed: Counter  # by enemy type
    damage_dealt: int
    damage_taken: int
    stealth_kills: int

    # Exploration
    steps_taken: int
    levels_completed: int  # 0-3 (victory at level 3)
    turns_taken: int

    # Items
    exploits_used: Counter  # by exploit name
    exploits_equipped: Counter  # by exploit name
    exploits_unequipped: Counter  # by exploit name
    code_hacks_used: Counter  # by hack name

    # System state
    heat_generated: int
    overheating_events: int
    trace_increases: int
    admin_spawns: int
```

Track lifetime metrics:
```python
@dataclass
class LifetimeMetrics:
    total_games: int
    total_victories: int
    total_turns: int
    fastest_victory_turns: Optional[int]
    longest_survival_turns: int

    # Aggregates from all sessions
    total_enemies_killed: Counter
    total_exploits_used: Counter
```

### Simple Tracking API

```python
# Usage throughout codebase:
track("enemies_killed", category="virus")
track("damage_dealt", amount=25)
track("exploits_equipped", category="code_injection")
```

### Storage

**JSON** - Per-session files in `metrics/` directory
- One file per session: `metrics/2025-10-29_143022.json`
- Human-readable for debugging
- Auto-cleanup after 100 files

**SQLite** - Aggregate database at `metrics/sessions.db`
- All sessions in single queryable database
- Schema: `sessions`, `combat_events`, `item_events`, `exploit_events`
- Used for analytics and future achievement checking

**Lifetime** - Extend `rogue_signal_progress.json`
- Survives permadeath (not deleted on death)
- Stores lifetime totals and records

### Tasks

1. Create `game_metrics.py` with data structures
2. Implement `track()` function with category/amount support
3. Add JSON serialization/deserialization for SessionMetrics
4. Create SQLite schema and persistence functions
5. Extend `rogue_signal_progress.json` with lifetime metrics section
6. Add `.gitignore` entry for `metrics/` directory

### Gotchas

- Use `Counter` from `collections` for category tracking
- `dataclasses` with `field(default_factory=Counter)` for initialization
- SQLite transactions for batch inserts (finalize session)
- Don't serialize Counter directly - convert to dict for JSON

---

## Phase 2: Combat & Death Tracking

**Goal:** Hook combat events to track kills, damage, and player death.

### Integration Points

**Enemy Death** - `game_engine.py:432`
```python
# After: self.enemy_manager.remove_enemy(target_enemy)
track("enemies_killed", category=target_enemy.name)
track("damage_dealt", amount=total_damage)
if not target_enemy.alerted:
    track("stealth_kills")
```

**Player Damage** - `game_characters.py` (Player.take_damage)
```python
track("damage_taken", amount=damage)
```

**Player Death** - `game_session.py:128`
```python
# When player.cpu <= 0
metrics = finalize_session(
    victory=False,
    death_cause="combat",  # or "overheat", "trace"
    death_level=game_state.level
)
save_metrics(metrics)
```

### Tasks

1. Add metrics initialization to `GameEngine.__init__()`
2. Hook enemy death in bump attack handler
3. Hook player damage in `Player.take_damage()`
4. Hook player death in `GameSession.process_turn()`
5. Create `finalize_session()` to compute final stats
6. Call `save_metrics()` on death and victory

### Gotchas

- Initialize metrics in `GameEngine` so all systems can access via `self.game_engine.metrics`
- Death can occur from combat, overheating, or trace - track cause separately
- Stealth kill = enemy not alerted when killed

---

## Phase 3: Movement & Progression Tracking

**Goal:** Track player movement and level progression through 3 levels.

### Integration Points

**Movement** - `game_engine.py:340`
```python
# After successful: self.player.move(dx, dy, self.game_map)
track("steps_taken")
```

**Level Completion** - `game_session.py:690` (progress_to_next_level)
```python
# At method start
track("levels_completed")
```

**Victory** - `game_session.py:720` (after level 3)
```python
# When victory triggers
metrics = finalize_session(victory=True, death_cause=None)
save_metrics(metrics)
```

**Turn Processing** - `game_state.py:159` (advance_turn)
```python
track("turns_taken")
```

### Tasks

1. Hook movement in `move_player()`
2. Hook level completion in `progress_to_next_level()`
3. Hook victory condition (after level 3 complete)
4. Hook turn counter in `GameStateManager.advance_turn()`
5. Verify metrics saved on both death and victory

### Gotchas

- Game has exactly 3 levels - victory triggers after level 3 completion
- Save is deleted on both death and victory (permadeath + no continuing after win)
- Level number resets to 1 on new game (stored in `game_state.level`)

---

## Phase 4: Item & Exploit Tracking

**Goal:** Track code hack and exploit usage, equipment changes.

### Integration Points

**Exploit Usage** - `game_combat.py:105+` (use_exploit)
```python
# After heat cost calculated
track("exploits_used", category=exploit_name)
track("heat_generated", amount=heat_cost)
```

**Exploit Equipment** - `game_inventory.py` (equip/unequip methods)
```python
# In equip_exploit()
track("exploits_equipped", category=exploit.name)

# In unequip_exploit()
track("exploits_unequipped", category=exploit.name)
```

**Code Hack Usage** - `game_inventory.py:100` (CodeHack.use)
```python
# After effect applied
track("code_hacks_used", category=hack.name)
```

**Overheating** - `game_engine.py:353-360` (move_player overheat damage)
```python
# When heat > max_heat
track("overheating_events")
```

**System Events** - Various locations
```python
# Trace increase
track("trace_increases")

# Admin spawn
track("admin_spawns")
```

### Tasks

1. Hook exploit usage in `ExploitSystem.use_exploit()`
2. Hook exploit equip/unequip in inventory methods
3. Hook code hack usage in `CodeHack.use()`
4. Hook overheating in movement handler
5. Hook trace increases wherever trace is modified
6. Hook admin spawn in enemy manager

### Gotchas

- Player has 5 exploit slots - track each equip/unequip by exploit name
- Heat cost varies by exploit (from `game_content.json`)
- Overheating occurs when `heat > max_heat` during movement
- Admin spawns at trace threshold (defined in `GameBalance`)

---

## Phase 5: Persistence & Testing

**Goal:** Integrate metrics into save/load system and validate tracking.

### Persistence Integration

**Auto-Save** - `game_engine.py:263-270`
```python
# In auto_save(), add metrics checkpoint
self.metrics.save_checkpoint()
```

**Game Start** - `game_engine.py:158-175`
```python
# Load or initialize metrics
if load_save:
    self.metrics = load_session_metrics(save_data)
else:
    self.metrics = init_session_metrics()
```

**Session Finalization**
```python
# Called on death or victory
metrics = finalize_session(victory, death_cause, death_level)
metrics.save_to_json(f"metrics/{session_id}.json")
metrics.save_to_sqlite("metrics/sessions.db")
update_lifetime_metrics(metrics)
```

### Testing Strategy

**Unit Tests**
- Test `track()` with category and amount
- Test Counter increments correctly
- Test JSON serialization round-trip
- Test SQLite persistence

**Integration Tests**
- Play through sample game, verify JSON output
- Kill enemies, check kill counts by type
- Use exploits, check usage counts
- Trigger death, verify metrics saved
- Complete game, verify victory metrics

**Validation**
- Query SQLite for aggregate stats
- Verify lifetime metrics update across sessions
- Check metrics survive permadeath (not deleted)

### Tasks

1. Add metrics to save/load in `SaveGameManager`
2. Integrate checkpoint saves with auto-save
3. Write unit tests for core tracking
4. Write integration test for full session
5. Verify JSON and SQLite output manually
6. Create basic analytics queries (most killed enemy, most used exploit)

### Gotchas

- Metrics persist in `rogue_signal_progress.json`, not deleted on death
- Save file (`rogue_signal_save.json`) IS deleted on death
- Session metrics saved to `metrics/` before save deletion
- SQLite needs proper locking for concurrent access (shouldn't be issue for single-player)

---

## Data We Track

**What matters for achievements and balance:**

Add more if you come across something juicy!!!

Combat:
- Enemies killed by type (which enemies are encountered/killed most)
- Stealth kills (player stealth skill)
- Damage dealt/taken (combat effectiveness)

Progression:
- Levels completed (how far players get)
- Turns taken (session length)
- Victory rate (win/loss ratio)

Exploits:
- Usage by exploit (which are popular/ignored)
- Equip/unequip patterns (which exploits equipped together)
- Heat generated (exploit cost tracking)

Items:
- Code hacks used (which hacks are valuable)

System:
- Overheating events (heat management skill)
- Trace increases (stealth effectiveness)
- Admin spawns (high trace consequences)

Death:
- Death cause (combat vs overheat vs trace)
- Death level (where players die most)
- Death turn (how long players survive)

**What we DON'T track:**
- Hit/miss rates (exploits auto-hit in your system)
- Movement distance (steps is sufficient)
- Individual tile types stepped on (too granular) [but turns spent in shadows or turns spent on special nodes might be interesting]

---

## Analytics Queries

**Balance insights:**

```sql
-- Which enemies kill players most?
SELECT death_cause, COUNT(*) FROM sessions
WHERE victory = 0 GROUP BY death_cause;

-- Which exploits are underused?
SELECT exploit_name, SUM(uses) FROM exploit_events
GROUP BY exploit_name ORDER BY SUM(uses) ASC;

-- What's the win rate?
SELECT
  SUM(CASE WHEN victory = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
FROM sessions;

-- Average session length by outcome
SELECT victory, AVG(turns_taken) FROM sessions GROUP BY victory;
```

**Achievement potential:**

Example achievements (not implemented in this plan):
- "First Blood" - Kill first enemy
- "Exterminator" - Kill 100 total enemies (lifetime)
- "Shadow Master" - 50% stealth kills in a run
- "Heat Management" - Win without overheating
- "Network Breaker" - Win the game (beat level 3)
- "Virus Hunter" - Kill 50 viruses (lifetime)
- "Speedrunner" - Win in under 300 turns

Achievement implementation is future work, but metrics collect all necessary data.

---

## File Structure

```
D:\Projects\RogueSignalProtocol\
├── game_metrics.py              # New: Core tracking system
├── rogue_signal_progress.json   # Modified: Add lifetime_metrics section
├── metrics/                     # New: Session data directory
│   ├── .gitignore              # Exclude from git
│   ├── sessions.db             # SQLite database
│   └── 2025-10-29_*.json       # Per-session JSON files
└── tests/
    └── test_metrics.py          # New: Metrics tests
```

**Modified files:**
- `game_engine.py` - Initialize metrics, hook combat/movement
- `game_session.py` - Hook level progression, death, victory
- `game_combat.py` - Hook exploit usage
- `game_inventory.py` - Hook item usage, equipment
- `game_state.py` - Hook turn counter
- `game_characters.py` - Hook player damage

---

## Success Criteria

✅ All gameplay events tracked without performance impact (<1ms per event)
✅ JSON files generated per session for debugging
✅ SQLite database queryable for analytics
✅ Lifetime metrics survive permadeath
✅ Metrics integrated into save/load system
✅ Tests verify tracking accuracy
✅ Zero external dependencies (stdlib only)

---

## Future Enhancements (Not in This Plan)

- Achievement system using tracked metrics
- Analytics dashboard script
- In-game stats viewer
- "Best run" comparisons
- Balance recommendations based on data
- Optional cloud sync for cross-device stats

These are explicitly out of scope for initial implementation. Focus is purely on data collection infrastructure.
