#!/usr/bin/env python3
"""
Pre-commit hook enforcement - prevents --no-verify commits in CI.

This script should be run in CI to detect if commits were made with --no-verify.
It checks the commit messages and git history for signs of hook bypassing.

Usage:
    python scripts/enforce_hooks.py [number_of_commits_to_check]

Examples:
    python scripts/enforce_hooks.py       # Check last 5 commits
    python scripts/enforce_hooks.py 10    # Check last 10 commits
"""

import subprocess
import sys
import re


def run_command(cmd: list[str]) -> str:
    """Run command and return output."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def check_commit_for_violations(commit_hash: str) -> list[str]:
    """Check a single commit for hook bypass indicators."""
    violations = []

    # Get commit message
    msg = run_command(['git', 'log', '-1', '--format=%B', commit_hash])

    # Get commit stats
    stats = run_command(['git', 'show', '--stat', commit_hash])

    # Check for suspicious patterns in commit message
    if '--no-verify' in msg.lower():
        violations.append("Commit message mentions '--no-verify'")

    if 'bypass' in msg.lower() and 'hook' in msg.lower():
        violations.append("Commit message mentions bypassing hooks")

    # Check if pre-commit hook files were modified suspiciously
    if re.search(r'\.git/hooks/pre-commit.*\|\s*0', stats):
        violations.append("Pre-commit hook was deleted or emptied")

    return violations


def main():
    """Check recent commits for hook bypassing."""
    num_commits = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    print("=" * 70)
    print("PRE-COMMIT HOOK ENFORCEMENT CHECK")
    print("=" * 70)
    print()
    print(f"Checking last {num_commits} commits for hook bypassing...")
    print()

    # Get recent commit hashes
    commits = run_command([
        'git', 'log', f'-{num_commits}', '--format=%H'
    ]).split('\n')

    total_violations = 0
    for commit in commits:
        short_hash = commit[:7]
        subject = run_command(['git', 'log', '-1', '--format=%s', commit])

        violations = check_commit_for_violations(commit)

        if violations:
            print(f"⚠️  {short_hash} - {subject}")
            for violation in violations:
                print(f"     └─ {violation}")
            print()
            total_violations += 1

    print("=" * 70)

    if total_violations > 0:
        print(f"❌ VIOLATIONS DETECTED: {total_violations} commit(s)")
        print()
        print("Action Required:")
        print("1. Review the flagged commits")
        print("2. Ensure tests were actually passing")
        print("3. Run full test suite: pytest tests/")
        print("4. If tests fail, fix them before pushing")
        print()
        print("Note: This is a warning, not a hard block.")
        print("      Use discretion for emergency hotfixes.")
        print()
        return 1
    else:
        print("✓ No hook bypass violations detected")
        print()
        return 0


if __name__ == '__main__':
    sys.exit(main())
