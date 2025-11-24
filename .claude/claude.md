# Personal Claude Code Preferences

**General preferences across all projects. Keep this file < 100 lines.**

---

## 0. Critical Rules (READ FIRST)

1. **VERIFY BEFORE ASSUMING** - Your most common mistake!
   - Use Read/Grep/Glob/Bash to CHECK instead of guessing
   - Examples: file contents, URLs, config values, API signatures
   - Never construct URLs/paths from assumptions - always grep first

2. **NO AUTO-COMMITS**: Always ask before committing. Exception: ONLY when user says "commit this" or "make a commit"

3. **Fix what you're asked to fix**: Don't dismiss test failures as "unrelated" - if asked to fix all tests, fix all tests

4. **BRUTAL HONESTY REQUIRED**: Always be brutally honest at all times
   - NEVER claim something is "done" or "tested" unless you have ACTUAL passing tests
   - NEVER say "all tests pass" when you only tested 10% of functionality
   - If you don't know, say "I don't know"

---

## 1. Bash & Environment

**GIT BASH ON WINDOWS** - Unix commands only:

- ✅ **USE THESE**: `ls`, `rm`, `mkdir`, `cp`, `mv`, `cat`, `grep`, `find`
- ❌ **NEVER USE**: `dir`, `del`, `md`, `copy`, `move`, `type` (Windows CMD commands)
- **Quote spaces**: Always quote paths with spaces: `cd "path with spaces"`
- **Python/Pip**: Use venv-specific executables to avoid triggering system dialogs:
  - ✅ GOOD: `.venv/Scripts/python.exe`, `.venv/Scripts/pip.exe`
  - ❌ BAD: bare `python`, `pip`, `pytest` (may trigger MS Store popup)

**AVOID PIPES & REDIRECTS** - Work around Claude Code permission bug:
- ❌ **BAD**: `pytest tests/ -v 2>&1 | tail -30` (triggers permission prompts)
- ✅ **GOOD**: Split into separate commands or save to temp file
- **Exception**: Simple single-pipe commands rarely cause issues, but complex chains always do

---

## 2. Code & Architecture

**General Principles:**
- Prefer simple functional code
- Keep files under ~20,000 tokens; refactor when approaching this limit
- One purpose per module
- No over-engineering or new frameworks
- **Always check bounds before array access** - verify indices are valid

**Test-Driven Development (TDD):**
- All development follows TDD cycle: Write failing test → Implement solution → Verify test passes
- Never write production code without a failing test first
- After test passes: Analyze if test should be kept as-is, expanded to catch edge cases, or refactored for clarity

---

## 3. Documentation & Research

**Before Implementing:**
- **ALWAYS** check official docs BEFORE assuming API behavior (you make wrong assumptions!)
- Use available documentation/skills when working with unfamiliar libraries
- Research first, implement second

---

## 4. Git & Version Control

**Commits:** See rule #0.2 - always ask first! Use `/commit` for standard workflow.

**Attribution:** FORBIDDEN - Never add any of:
- `Co-Authored-By: Claude` tags
- `🤖 Generated with [Claude Code]` links
- Any AI attribution or emoji signatures
- Clean technical messages ONLY

**.gitignore:** NEVER use inline comments with trailing spaces (`dist/  # comment` breaks). ALWAYS test patterns before committing.

---

## 5. Reasoning & Problem-Solving

**Approach:**
- Unfold understanding gradually - show natural thought progression
- Acknowledge mistakes, explain how understanding evolved
- Examine multiple angles before implementing (feasibility, edge cases, performance, integration)
- Switch modes based on context (exploration → implementation → debugging → optimization)
- Match depth to complexity (trivial → quick, high stakes → deep)
- Think system-level first, then implement
- Apply same rigor at all scales (architecture to variable names)

---

## 6. Communication Style

**General Guidelines:**
- Be clear, concise, and precise
- Avoid unnecessary emoji in code/commits
- Save emoji for user chat when appropriate
