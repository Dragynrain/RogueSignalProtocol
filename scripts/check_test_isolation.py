#!/usr/bin/env python3
"""
Test isolation checker - detects tests that pass alone but fail in suite.

This script helps identify test pollution by running tests both ways and
comparing results. Tests that behave differently indicate pollution.

Usage:
    python scripts/check_test_isolation.py [test_file_pattern]

Examples:
    python scripts/check_test_isolation.py                    # Check all tests
    python scripts/check_test_isolation.py tests/unit/*.py    # Check unit tests
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str]:
    """Run command and return (exit_code, output)."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def get_failed_tests(pytest_output: str) -> set[str]:
    """Extract failed test names from pytest output."""
    failed = set()
    for line in pytest_output.split('\n'):
        if line.startswith('FAILED '):
            # Extract test name: "FAILED tests/unit/test_foo.py::TestClass::test_method"
            test_name = line.split(' ')[1].split(' ')[0]
            failed.add(test_name)
    return failed


def main():
    """Check for test isolation issues."""
    test_pattern = sys.argv[1] if len(sys.argv) > 1 else 'tests/'

    print("=" * 70)
    print("TEST ISOLATION CHECKER")
    print("=" * 70)
    print()
    print(f"Checking: {test_pattern}")
    print()

    # Step 1: Run full test suite
    print("[1/2] Running full test suite...")
    suite_exit, suite_output = run_command([
        sys.executable, '-m', 'pytest', test_pattern, '-v', '--tb=no'
    ])
    suite_failed = get_failed_tests(suite_output)

    if not suite_failed:
        print("  ✓ All tests pass in full suite!")
        print()
        print("=" * 70)
        print("RESULT: No isolation issues detected")
        print("=" * 70)
        return 0

    print(f"  Found {len(suite_failed)} failures in full suite")
    print()

    # Step 2: Run each failed test in isolation
    print("[2/2] Re-running failed tests in isolation...")
    isolation_passed = set()
    still_failing = set()

    for i, test_name in enumerate(sorted(suite_failed), 1):
        print(f"  [{i}/{len(suite_failed)}] {test_name}...", end=' ')

        iso_exit, iso_output = run_command([
            sys.executable, '-m', 'pytest', test_name, '-v', '--tb=no'
        ])

        if iso_exit == 0:
            print("PASSES (isolation issue!)")
            isolation_passed.add(test_name)
        else:
            print("still fails")
            still_failing.add(test_name)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    if isolation_passed:
        print(f"⚠️  ISOLATION ISSUES DETECTED: {len(isolation_passed)} tests")
        print()
        print("These tests pass alone but fail in the suite (test pollution):")
        for test in sorted(isolation_passed):
            print(f"  - {test}")
        print()
        print("Recommendation: Check for shared state, mocking issues, or")
        print("class-level caches being polluted across tests.")
        print()

    if still_failing:
        print(f"❌ LEGITIMATE FAILURES: {len(still_failing)} tests")
        print()
        print("These tests fail both ways (not pollution):")
        for test in sorted(still_failing):
            print(f"  - {test}")
        print()

    print("=" * 70)

    # Exit with error if any isolation issues found
    return 1 if isolation_passed else 0


if __name__ == '__main__':
    sys.exit(main())
