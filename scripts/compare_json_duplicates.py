#!/usr/bin/env python3
"""
Compare all JSON configuration files to find duplicate keys.
Uses ASCII-only output to avoid Windows terminal encoding issues.
"""

import json
import sys
from pathlib import Path


def flatten_dict(d, parent_key='', sep='.'):
    """Flatten nested dictionary into dot-notation keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def compare_json_files(file1_path, file2_path):
    """Compare two JSON files and find duplicate keys."""

    with open(file1_path, 'r', encoding='utf-8') as f:
        data1 = json.load(f)

    with open(file2_path, 'r', encoding='utf-8') as f:
        data2 = json.load(f)

    flat1 = flatten_dict(data1)
    flat2 = flatten_dict(data2)

    # Find keys that exist in both files
    common_keys = set(flat1.keys()) & set(flat2.keys())

    duplicates = {
        'matching': [],      # Same key, same value
        'conflicting': [],   # Same key, different value
    }

    for key in sorted(common_keys):
        val1 = flat1[key]
        val2 = flat2[key]

        if val1 == val2:
            duplicates['matching'].append((key, val1, val2))
        else:
            duplicates['conflicting'].append((key, val1, val2))

    return duplicates


def main():
    """Compare game_rules.json and game_content.json for duplicates."""

    print("=" * 80)
    print("JSON Configuration Duplicate Check")
    print("=" * 80)
    print()

    file1 = Path("game_rules.json")
    file2 = Path("game_content.json")

    if not file1.exists():
        print(f"ERROR: {file1} not found")
        return 1

    if not file2.exists():
        print(f"ERROR: {file2} not found")
        return 1

    print(f"Comparing: {file1.name} vs {file2.name}")
    print()

    duplicates = compare_json_files(file1, file2)

    total_duplicates = len(duplicates['matching']) + len(duplicates['conflicting'])

    if total_duplicates == 0:
        print("[OK] No duplicate keys found across files")
        return 0

    print(f"[WARNING] Found {total_duplicates} duplicate keys across files")
    print()

    # Report conflicting duplicates (same key, different value) - HIGH PRIORITY
    if duplicates['conflicting']:
        print("=" * 80)
        print(f"CONFLICTING DUPLICATES ({len(duplicates['conflicting'])})")
        print("Same key exists in both files but with DIFFERENT values")
        print("=" * 80)
        print()

        for key, val1, val2 in duplicates['conflicting']:
            print(f"Key: {key}")
            print(f"  {file1.name}: {val1}")
            print(f"  {file2.name}: {val2}")
            print()

    # Report matching duplicates (same key, same value) - LOWER PRIORITY
    if duplicates['matching']:
        print("=" * 80)
        print(f"MATCHING DUPLICATES ({len(duplicates['matching'])})")
        print("Same key exists in both files with SAME value")
        print("=" * 80)
        print()

        for key, val1, val2 in duplicates['matching']:
            print(f"Key: {key}")
            print(f"  Value: {val1}")
            print(f"  (appears in both files)")
            print()

    print("=" * 80)
    print("RECOMMENDATIONS:")
    print("=" * 80)
    print()

    if duplicates['conflicting']:
        print("CONFLICTING DUPLICATES:")
        print("  - These are CRITICAL issues - same key with different values")
        print("  - Code may be using wrong value depending on load order")
        print("  - Remove from one file and establish single source of truth")
        print()

    if duplicates['matching']:
        print("MATCHING DUPLICATES:")
        print("  - These are redundant but not breaking")
        print("  - Consider removing duplicates to reduce maintenance burden")
        print("  - Keep in file that makes most logical sense for that key")
        print()

    return 1 if total_duplicates > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
