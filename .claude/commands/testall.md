---
description: Run tests and fix failures
argument-hint: [optional: specific test pattern]
---

Run tests: $ARGUMENTS (defaults to full suite if empty)

Requirements:
- Run pytest with appropriate verbosity
- Analyze any failing tests
- Fix by either correcting test or fixing code
- Don't claim tests pass without proof
- Use TDD cycle: keep test failures visible until fixed