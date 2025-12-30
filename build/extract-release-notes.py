#!/usr/bin/env python3
"""Extract release notes from CHANGELOG.md for GitHub releases.

Usage:
    python extract-release-notes.py [version]
    python extract-release-notes.py 0.9.1
    python extract-release-notes.py  # extracts latest version

Output goes to stdout for easy copy-paste or redirection.
"""

import re
import sys
from pathlib import Path


def extract_release_notes(changelog_path: Path, target_version: str | None = None) -> str:
    """Extract release notes for a specific version from CHANGELOG.md."""
    content = changelog_path.read_text(encoding="utf-8")

    # Pattern matches: ## [0.9.1 Beta] - 2025-12-29 - Title
    version_pattern = r"^## \[([^\]]+)\].*$"

    lines = content.split("\n")

    # Find all version headers and their line numbers
    versions = []
    for i, line in enumerate(lines):
        match = re.match(version_pattern, line)
        if match:
            versions.append((match.group(1), i, line))

    if not versions:
        return "ERROR: No version sections found in CHANGELOG.md"

    # If no target specified, use the first (latest) version
    if target_version is None:
        target_idx = 0
    else:
        # Find matching version (partial match allowed)
        target_idx = None
        for i, (ver, _, _) in enumerate(versions):
            # Check if version starts with target (e.g., "0.9.1" matches "0.9.1 Beta")
            if ver.startswith(target_version) or target_version in ver:
                target_idx = i
                break

        if target_idx is None:
            available = ", ".join(v[0] for v in versions[:5])
            return f"ERROR: Version '{target_version}' not found. Available: {available}"

    # Extract lines between this version header and the next (or EOF)
    start_line = versions[target_idx][1]
    if target_idx + 1 < len(versions):
        end_line = versions[target_idx + 1][1]
    else:
        end_line = len(lines)

    # Get the section, skip the header line, trim trailing whitespace
    section_lines = lines[start_line + 1:end_line]

    # Remove trailing empty lines and horizontal rules
    while section_lines and (not section_lines[-1].strip() or section_lines[-1].strip() == "---"):
        section_lines.pop()

    # Remove leading empty lines
    while section_lines and not section_lines[0].strip():
        section_lines.pop(0)

    return "\n".join(section_lines)


def main():
    # Find CHANGELOG.md relative to script location
    script_dir = Path(__file__).parent
    changelog_path = script_dir.parent / "CHANGELOG.md"

    if not changelog_path.exists():
        print(f"ERROR: CHANGELOG.md not found at {changelog_path}", file=sys.stderr)
        sys.exit(1)

    # Get target version from command line
    target_version = sys.argv[1] if len(sys.argv) > 1 else None

    # Extract and print
    notes = extract_release_notes(changelog_path, target_version)
    print(notes)


if __name__ == "__main__":
    main()
