# Test Agent Development Guide

**Quick reference for building GameTestAgent-based agents (combat agents, exploration agents, etc.)**

---

## The Golden Rule

**Test primitives before building complexity.**

Don't add trace management until basic movement works.
Don't add retreats until basic combat works.
Don't add strategy until the agent can clear one level.

---

## Development Checklist

### Step 1: Test Basic Movement (30 lines)
```python
def test_can_move_one_tile():
    agent = YourAgent(seed=1)
    old_pos = (agent.player.x, agent.player.y)
    agent.move_player(1, 0)
    assert (agent.player.x, agent.player.y) != old_pos
```

**Don't proceed until this works.**

### Step 2: Test Basic Combat (50 lines)
```python
def test_can_attack_adjacent_enemy():
    agent = YourAgent(seed=1)
    agent.spawn_enemy('drone', agent.player.x + 1, agent.player.y)
    initial_count = len(agent.enemies)

    agent.move_player(1, 0)  # Bump attack

    assert len(agent.enemies) < initial_count  # Enemy died
```

**Don't proceed until this works.**

### Step 3: Add Time Tracking (Required!)
```python
class YourAgent(GameTestAgent):
    def __init__(self, ...):
        super().__init__(...)
        self.time_combat = 0
        self.time_moving = 0
        self.time_exploring = 0
```

**Red flag: If `time_combat < 30%`, STOP and debug pathfinding.**

### Step 4: Test Can Clear One Level
```python
def test_can_clear_level():
    agent = YourAgent(seed=1, max_turns=500)
    result = agent.run_campaign()

    assert result['status'] == 'cleared', "Should beat level"
    assert result['kills'] == result['total_enemies'], "Should kill all"
    assert result['turns'] < 500, "Should not timeout"
    assert result['combat_turns'] / result['turns'] > 0.3, "Should fight, not wander"
```

**Don't add fancy features until this works.**

### Step 5: Add Features ONE at a Time
Each feature needs its own test:
- HP retreats → Test: survives when low HP
- Choke points → Test: uses chokes when surrounded
- Trace management → Test: clears trace before spawning admins
- Multi-level → Test: proceeds through gateway

---

## Common Mistakes to Avoid

### ❌ Duplicate Logic in Multiple Places
```python
# BAD: Retreat check in charge_and_attack() AND main loop
def charge_and_attack():
    if self.should_retreat_to_healing():  # ❌ Don't check here
        return 'retreat_heal'  # Caller doesn't handle this!
```

**Fix: Only check conditions in ONE place (the caller).**

### ❌ Ignore Return Values
```python
# BAD: Call function, ignore return, re-compute result
old_pos = (self.player.x, self.player.y)
self.move_to(target_x, target_y, max_steps=1)  # ❌ Ignoring return
moved = (old_pos != (self.player.x, self.player.y))  # Re-computing
```

**Fix: Trust the return value:**
```python
# GOOD: Use the return value
moved = self.move_to(target_x, target_y, max_steps=1)
```

### ❌ Test "Survived" Instead of "Cleared"
```python
# BAD: "Survived" might mean timed out!
assert agent.player.cpu > 0

# GOOD: Actually verify success
assert result['status'] == 'cleared'
assert result['kills'] == result['total_enemies']
```

---

## Debug Checklist

Agent is stuck or performing poorly? Check these:

1. **Time breakdown** - Where is time spent?
   - Combat should be >30% for combat agents
   - If <5% combat, pathfinding is broken

2. **Return value handling** - Are all return values used?
   - Search for function calls where return value is ignored
   - Check if caller handles all possible return values

3. **Duplicate logic** - Same check in multiple places?
   - Retreat checks only in main loop OR in action function, not both
   - Victory conditions in one place

4. **Infinite loops** - Is something returning early without progress?
   - Add turn counters to action functions
   - Log why functions exit early

5. **Movement success** - Does bump attack return True?
   - `move_player()` should return True for both moves AND attacks
   - Check if position change is the only success condition

---

## Example: Minimal Combat Agent

```python
class MinimalCombatAgent(GameTestAgent):
    """Simple agent that just fights everything."""

    def __init__(self, seed=None, max_turns=1000):
        super().__init__(seed=seed, level=1)
        self.max_turns = max_turns
        self.kills = 0
        self.combat_turns = 0

    def run(self):
        for turn in range(self.max_turns):
            # Track time
            if self.count_adjacent_enemies() > 0:
                self.combat_turns += 1

            # Simple logic: find enemy, move toward it
            enemy_pos = self.find_nearest_enemy()
            if enemy_pos:
                ex, ey = enemy_pos
                self.move_to(ex, ey, max_steps=1)

            # Check victory
            if len(self.enemies) == 0:
                return {'status': 'cleared', 'kills': self.kills}

        return {'status': 'timeout', 'kills': self.kills}
```

**Build on this foundation. Don't start with 1500 lines.**

---

## References

- Base class: `tests/test_agent.py` - GameTestAgent
- Example agents: `tests/agents/test_barbarian_agent.py`
- Testing guide: `.claude/TESTING_GUIDE.md`
