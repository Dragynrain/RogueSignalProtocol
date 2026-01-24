# Personal Claude Code Preferences

**General preferences across all projects. Keep this file < 100 lines.**

## 0. Critical Rules (READ FIRST)

1. **VERIFY BEFORE ASSUMING** - Your most common mistake!
   - Use Read/Grep/Glob/Bash to CHECK instead of guessing
   - Never construct URLs/paths from assumptions - always grep first

2. **NO AUTO-COMMITS**: Always ask before committing. Exception: user says "commit this"

3. **FIX ALL TEST FAILURES**: Never use `--no-verify` to skip failing tests
   - Don't dismiss failures as "unrelated" - investigate and fix them
   - If a test is flaky, fix the flakiness, don't skip it

4. **BRUTAL HONESTY**: Never claim "done" or "tested" without actual passing tests

## 1. Bash & Environment

**GIT BASH ON WINDOWS** - Unix commands only (`ls`, `rm`, `mkdir`, `cp`, `mv`, `grep`, `find`)
- Never use: `dir`, `del`, `md`, `copy`, `move`, `type` (Windows CMD)
- Quote paths with spaces: `cd "path with spaces"`
- Use venv executables: `.venv/Scripts/python.exe` (not bare `python`)
- **GitHub CLI:** Call explicitly as `/c/Program\ Files/GitHub\ CLI/gh.exe` (not bare `gh`)

**AVOID PIPES & REDIRECTS** - Complex chains trigger permission prompts
- Split into separate commands or save to temp file

## 2. Code & Architecture

- Prefer simple functional code
- Keep files under ~20,000 tokens; refactor when approaching
- One purpose per module; no over-engineering
- **Always check bounds before array access**

**TDD - MANDATORY:**
- NEVER write production code without a failing test first
- Cycle: Write failing test -> Implement minimum fix -> Verify pass

## 3. Documentation & Research

- ALWAYS check official docs BEFORE assuming API behavior
- Research first, implement second
- **PLAN files**: Keep current state only - no revision history, no "Review N" sections. Git tracks history.

## 4. Git & Version Control

**Commits:** Always ask first! Use `/commit` for standard workflow.

**Attribution:** FORBIDDEN - No `Co-Authored-By: Claude`, no AI signatures, clean messages only

**.gitignore:** Never use inline comments with trailing spaces
