# Planning Guidelines

When creating implementation plans, follow these principles for clarity and actionability.

---

## Time Estimates

**NEVER provide time estimates** (hours, days, weeks, sprints) unless explicitly requested.

- You are bad at estimating time
- Focus on: complexity, difficulty, risk level, dependencies
- Acceptable qualifiers: "trivial", "straightforward", "complex", "high-risk"
- Not acceptable: "2 hours", "3 days", "1-2 weeks"

---

## Plan Structure

### 1. Summary & Overview
Brief description of what's being built and why.

### 2. Phases (Top-Level)
**List phases immediately** after summary, before detailed breakdowns:

```
Phase 1: Core Infrastructure (high complexity)
Phase 2: Feature Implementation (medium complexity)
Phase 3: Testing & Integration (low complexity, depends on Phase 2)
```

Include: complexity/difficulty/risk, dependencies between phases.

### 3. Detailed Phase Breakdowns
Below the phase list, expand each phase with:
- Specific tasks/subtasks
- Technical considerations
- Gotchas or edge cases
- Dependencies within phase

---

## Code in Plans

**Keep code minimal:**
- ✓ Short examples (5-10 lines max)
- ✓ API references: `use InventorySystem.add_item()`
- ✓ Key signatures: `def process_turn(entities: List[Entity]) -> TurnResult`
- ✗ Full class implementations
- ✗ Complete function bodies
- ✗ Copy-pasted existing code

**Why:** Plans describe *what* and *why*. Implementation shows *how*.

---

## Clarity & Actionability

- Each task should be independently understandable
- Avoid vague language: "handle the system" → "validate input in Entity.move()"
- Call out assumptions: "assumes existing FOV system is stable"
- Flag unknowns: "research: does TCOD support layered transparency?"

---

## Performance & Optimization

**Don't worry about performance** until it's measurably a problem:
- No preemptive optimization in plans
- No benchmarking tasks unless user reports slowness
- Focus on correctness and clarity first

---

## Example Phase Structure

```
## Phase 1: Dialogue System Core (Medium Complexity)

Dependencies: None
Risk: Low - uses existing rendering infrastructure

Tasks:
1. Create DialogueNode data structure (story_content.json schema)
2. Implement DialogueManager.load_dialogues() with validation
3. Add DialogueRenderer.render() using UnifiedRenderer
4. Wire up input handling in Engine.handle_dialogue_input()

Gotchas:
- Must use CoordinateHelpers for transparency (see TCOD_GUIDE.md)
- Validate all node IDs exist before allowing transitions
```
