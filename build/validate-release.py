#!/usr/bin/env python3
"""Pre-release validation script.

Automates Phase 1 code quality checks from docs/RELEASE_CHECKLIST.md.
Run before building to catch issues early.

Usage:
    python build/validate-release.py
    python build/validate-release.py --fix  # auto-fix some issues (future)
"""

import json
import re
import subprocess
import sys
from pathlib import Path


class ValidationResult:
    """Result of a single validation check."""

    def __init__(self, name: str, passed: bool, message: str = "", details: list[str] | None = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or []


def run_command(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_test_suite(project_root: Path) -> ValidationResult:
    """Run pytest and check for failures."""
    print("  Running test suite...", end=" ", flush=True)

    # Use venv python
    python = project_root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = project_root / ".venv" / "bin" / "python"

    returncode, stdout, stderr = run_command(
        [str(python), "-m", "pytest", "tests/", "-v", "--tb=short"],
        cwd=project_root,
    )

    if returncode == 0:
        print("PASS")
        return ValidationResult("Test Suite", True, "All tests passed")
    else:
        print("FAIL")
        # Extract failure summary
        failures = []
        for line in stdout.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failures.append(line.strip())
        return ValidationResult(
            "Test Suite",
            False,
            f"Tests failed (exit code {returncode})",
            failures[:10],  # Limit to first 10
        )


def check_unicode_logging(project_root: Path) -> ValidationResult:
    """Check for Unicode characters in logging calls."""
    print("  Checking Unicode in logging...", end=" ", flush=True)

    # Use venv python
    python = project_root / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = project_root / ".venv" / "bin" / "python"

    returncode, stdout, stderr = run_command(
        [str(python), "-m", "pytest", "tests/test_no_unicode_in_logging.py", "-v", "--no-cov"],
        cwd=project_root,
    )

    if returncode == 0:
        print("PASS")
        return ValidationResult("Unicode Logging", True, "No Unicode in logging calls")
    else:
        print("FAIL")
        return ValidationResult(
            "Unicode Logging",
            False,
            "Unicode characters found in logging - Windows will crash",
            ["Run: pytest tests/test_no_unicode_in_logging.py -v for details"],
        )


def check_debug_prints(project_root: Path) -> ValidationResult:
    """Scan for debug print statements in game files."""
    print("  Scanning for debug prints...", end=" ", flush=True)

    game_files = list(project_root.glob("game_*.py"))
    debug_prints = []

    # Pattern to find print() but not console.print()
    pattern = re.compile(r"^\s*print\(")

    for file in game_files:
        content = file.read_text(encoding="utf-8")
        for i, line in enumerate(content.split("\n"), 1):
            if pattern.match(line) and "console.print" not in line:
                debug_prints.append(f"{file.name}:{i}: {line.strip()[:60]}")

    if not debug_prints:
        print("PASS")
        return ValidationResult("Debug Prints", True, "No debug print statements found")
    else:
        print(f"WARN ({len(debug_prints)} found)")
        return ValidationResult(
            "Debug Prints",
            False,
            f"Found {len(debug_prints)} debug print statements",
            debug_prints[:10],
        )


def check_json_configs(project_root: Path) -> ValidationResult:
    """Validate all JSON config files load correctly."""
    print("  Validating JSON configs...", end=" ", flush=True)

    configs = [
        "game_content.json",
        "game_rules.json",
        "narrative_content.json",
        "graphics_tiles.json",
        "default_bindings.json",
    ]

    errors = []
    for config in configs:
        config_path = project_root / config
        if not config_path.exists():
            errors.append(f"{config}: File not found")
            continue
        try:
            with open(config_path, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{config}: {e}")

    if not errors:
        print("PASS")
        return ValidationResult("JSON Configs", True, f"All {len(configs)} configs valid")
    else:
        print("FAIL")
        return ValidationResult("JSON Configs", False, "Config validation failed", errors)


def check_todo_fixme(project_root: Path) -> ValidationResult:
    """Check for TODO/FIXME comments that might be blockers."""
    print("  Scanning TODO/FIXME...", end=" ", flush=True)

    game_files = list(project_root.glob("game_*.py"))
    blockers = []

    # Look for urgent markers
    urgent_patterns = [
        re.compile(r"#\s*TODO.*BLOCKER", re.IGNORECASE),
        re.compile(r"#\s*FIXME.*CRITICAL", re.IGNORECASE),
        re.compile(r"#\s*XXX", re.IGNORECASE),
        re.compile(r"#\s*HACK.*REMOVE", re.IGNORECASE),
    ]

    for file in game_files:
        content = file.read_text(encoding="utf-8")
        for i, line in enumerate(content.split("\n"), 1):
            for pattern in urgent_patterns:
                if pattern.search(line):
                    blockers.append(f"{file.name}:{i}: {line.strip()[:60]}")

    if not blockers:
        print("PASS")
        return ValidationResult("TODO/FIXME", True, "No blocking TODOs found")
    else:
        print(f"WARN ({len(blockers)} blockers)")
        return ValidationResult(
            "TODO/FIXME",
            False,
            f"Found {len(blockers)} blocking comments",
            blockers,
        )


def check_version_consistency(project_root: Path) -> ValidationResult:
    """Check that version strings are consistent across files."""
    print("  Checking version consistency...", end=" ", flush=True)

    # Get version from game_rules.json (source of truth)
    rules_path = project_root / "game_rules.json"
    try:
        with open(rules_path, encoding="utf-8") as f:
            rules = json.load(f)
        expected_version = rules.get("version", "")
    except Exception as e:
        return ValidationResult("Version Consistency", False, f"Cannot read version: {e}")

    if not expected_version:
        return ValidationResult("Version Consistency", False, "No version in game_rules.json")

    # Check a few key files
    mismatches = []

    # Check README.txt
    readme_path = project_root / "README.txt"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        if expected_version not in content:
            mismatches.append(f"README.txt: version {expected_version} not found")

    if not mismatches:
        print("PASS")
        return ValidationResult(
            "Version Consistency",
            True,
            f"Version {expected_version} consistent",
        )
    else:
        print("WARN")
        return ValidationResult(
            "Version Consistency",
            False,
            f"Version mismatches (expected {expected_version})",
            mismatches,
        )


def main():
    # Find project root (parent of build/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print()
    print("=" * 50)
    print("Pre-Release Validation")
    print("=" * 50)
    print()

    # Run all checks
    results = [
        check_json_configs(project_root),
        check_unicode_logging(project_root),
        check_debug_prints(project_root),
        check_todo_fixme(project_root),
        check_version_consistency(project_root),
        check_test_suite(project_root),  # Run last as it's slowest
    ]

    # Summary
    print()
    print("=" * 50)
    print("Results")
    print("=" * 50)
    print()

    passed = 0
    failed = 0

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        icon = "[OK]" if result.passed else "[!!]"
        print(f"{icon} {result.name}: {result.message}")

        if result.details:
            for detail in result.details:
                print(f"      {detail}")

        if result.passed:
            passed += 1
        else:
            failed += 1

    print()
    print("-" * 50)
    print(f"Total: {passed} passed, {failed} failed")
    print()

    if failed > 0:
        print("Fix the issues above before building.")
        sys.exit(1)
    else:
        print("All checks passed - ready to build!")
        sys.exit(0)


if __name__ == "__main__":
    main()
