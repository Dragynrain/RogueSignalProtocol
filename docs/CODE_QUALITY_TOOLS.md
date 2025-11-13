# Code Quality Tools

This document describes the code quality tools installed and configured for Rogue Signal Protocol.

## Tools Installed

### 1. Black - Code Formatter
**Purpose:** Automatic Python code formatting
**Configuration:** `pyproject.toml` (line-length=100)
**Status:** Non-blocking warnings in pre-commit

**Manual usage:**
```bash
# Check formatting
.venv/Scripts/black.exe . --check

# Auto-format all files
.venv/Scripts/black.exe .

# Format specific file
.venv/Scripts/black.exe game_engine.py
```

**Current status:** 3 files need formatting (minor whitespace changes)

---

### 2. Ruff - Fast Python Linter
**Purpose:** Catches common errors, unused imports, deprecated syntax
**Configuration:** `pyproject.toml`
**Status:** Non-blocking warnings in pre-commit

**Manual usage:**
```bash
# Check for issues
.venv/Scripts/ruff.exe check .

# Auto-fix issues
.venv/Scripts/ruff.exe check . --fix

# Check specific file
.venv/Scripts/ruff.exe check game_engine.py
```

**Current findings:**
- Unused imports (mainly in RogueSignalProtocol.py)
- Deprecated `typing.List` (should use `list` in Python 3.13)
- Import sorting suggestions

---

### 3. Mypy - Static Type Checker
**Purpose:** Validates type hints and catches type errors
**Configuration:** `pyproject.toml` (lenient mode)
**Status:** Non-blocking warnings in pre-commit

**Manual usage:**
```bash
# Check all files
.venv/Scripts/mypy.exe .

# Check specific file
.venv/Scripts/mypy.exe game_engine.py

# More verbose output
.venv/Scripts/mypy.exe . --show-error-codes
```

**Current findings:**
- Implicit Optional issues (need `Optional[str]` instead of `str = None`)
- Some unreachable code after `raise` statements
- Return type mismatches

---

### 4. Pydeps - Dependency Analysis
**Purpose:** Visualize module dependencies
**Status:** Text output generated (visual graph requires Graphviz)

**Manual usage:**
```bash
# Generate JSON dependency data
.venv/Scripts/pydeps.exe RogueSignalProtocol.py --show-deps --max-bacon 3 > dependencies.json

# Generate visual graph (requires Graphviz installation)
.venv/Scripts/pydeps.exe RogueSignalProtocol.py -o architecture.svg --max-bacon 2
```

**Note:** Visual graphs require [Graphviz](https://graphviz.org/download/) to be installed separately.

**Generated files:**
- `docs/dependencies.json` - Full dependency data in JSON format

---

## Pre-Commit Hook

The pre-commit hook (`.git/hooks/pre-commit`) now runs 4 checks:

1. **Black** (formatting) - WARNING only
2. **Ruff** (linting) - WARNING only
3. **Mypy** (type checking) - WARNING only
4. **Pytest** (tests) - **BLOCKING**

### Making Checks Blocking

To make formatting/linting checks block commits, edit `.git/hooks/pre-commit`:

```bash
# Configuration: Set to 1 to make formatting/linting blocking
BLOCK_ON_BLACK=1  # Change 0 -> 1
BLOCK_ON_RUFF=1   # Change 0 -> 1
BLOCK_ON_MYPY=1   # Change 0 -> 1
```

### Bypassing Pre-Commit

Emergency bypass (not recommended):
```bash
git commit --no-verify
```

---

## Recommended Workflow

### 1. Before Committing
```bash
# Auto-fix what can be fixed
.venv/Scripts/black.exe .
.venv/Scripts/ruff.exe check . --fix

# Check remaining issues
.venv/Scripts/mypy.exe .
```

### 2. Incremental Improvement

Don't try to fix all issues at once! Instead:

1. **Black:** Run once, commit formatting changes
2. **Ruff:** Fix unused imports gradually as you touch files
3. **Mypy:** Add proper type hints when working on each module

### 3. CI/CD Integration (Future)

These tools can be integrated into GitHub Actions or other CI systems:

```yaml
# Example .github/workflows/quality.yml
- run: black . --check
- run: ruff check .
- run: mypy .
- run: pytest tests/
```

---

## Configuration Files

All tools are configured in `pyproject.toml`:

- **Black:** Line length, Python version, exclusions
- **Ruff:** Linting rules, line length, exclusions
- **Mypy:** Type checking strictness, per-module overrides

---

## Benefits

1. **Consistency:** Black ensures uniform code style
2. **Bug Prevention:** Ruff catches unused code and common mistakes
3. **Type Safety:** Mypy prevents type-related runtime errors
4. **Architecture Visibility:** Pydeps shows module relationships

---

## Next Steps (Optional)

1. **Fix Black formatting:** Run `black .` once and commit
2. **Clean up imports:** Run `ruff check . --fix` to remove unused imports
3. **Gradual type improvement:** Add `Optional[]` hints as you work on files
4. **Install Graphviz:** For visual dependency graphs
5. **Make checks blocking:** Once issues are resolved, enable blocking mode

---

## Documentation

- Black: https://black.readthedocs.io/
- Ruff: https://docs.astral.sh/ruff/
- Mypy: https://mypy.readthedocs.io/
- Pydeps: https://pydeps.readthedocs.io/
