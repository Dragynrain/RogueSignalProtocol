# New Control Binding Checklist

Every time you add or modify a control binding, check ALL these locations:

## Code (Required)
- [ ] **src/rsp/input/mappings.py** - Add the actual binding (keyboard/gamepad)
- [ ] **src/rsp/input/actions.py** - Add InputAction enum if needed
- [ ] **src/rsp/input/gameplay.py** / **src/rsp/input/modals.py** - Handle the action

## Documentation (Required)
- [ ] **src/rsp/ui/help_content.py** - In-game help text (players see this first!)
- [ ] **README.txt** - Player-facing controls section (bundled with download)
- [ ] **docs/wiki/Keybindings.md** - Wiki keybindings page (copy to GitHub Wiki later)
  - Add to appropriate section (Movement, Core Actions, Gamepad Controls, etc.)
  - Update Quick Reference if it's a commonly-used control
- [ ] **PLAN_GAMEPAD.md** (if gamepad) - Gamepad implementation plan

## Tests (Recommended)
- [ ] **tests/integration/test_input_*.py** - Integration test for the control
- [ ] **tests/unit/test_input_*.py** - Unit test if complex logic

## Optional (Context-Dependent)
- [ ] **README.md** - Only if it's a major feature worth mentioning
- [ ] **docs/ROADMAP.md** - If implementing a planned feature
- [ ] **.claude/gamepad.md** - If gamepad-related

---

## Quick Copy-Paste Template

When adding a new control, use this template:

### In src/rsp/ui/help_content.py
```python
("Action Name", "Key / Description"),
```

### In README.txt (CONTROLS section)
```
  Key       - Description of action
```

### In docs/wiki/Keybindings.md
```markdown
| **Key** | Action Name | Description |
```

---

## Why This Matters

**Players find controls in 3 places:**
1. **In-game help (?)** - Most common, auto-shown on first run
2. **README.txt** - Bundled with game download
3. **Wiki** - Online reference, Google-able

**Developers check:**
1. **Code files** - Actual implementation
2. **Plan docs** - Feature specs
3. **Tests** - Validation

Missing ANY of these creates confusion, inconsistent documentation, or untested code!

---

## Automation Ideas for Future

Could we auto-generate documentation from code?

**Potential approaches:**
1. **Single source of truth** - Parse `rsp.input.mappings` to generate docs
2. **Validation script** - Check for mismatches between code and docs
3. **CI check** - Fail builds if docs are out of sync with code

**Trade-offs:**
- Auto-generation loses narrative/explanatory text
- Validation adds complexity but catches errors early
- Manual process is flexible but error-prone

**Recommendation:** Start with a validation script that warns about missing docs,
but doesn't auto-generate them (preserves hand-written explanations).
