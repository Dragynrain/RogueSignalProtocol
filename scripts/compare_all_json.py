#!/usr/bin/env python3
"""
Compare ALL JSON configuration files to find duplicate keys.
Uses ASCII-only output to avoid Windows terminal encoding issues.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def flatten_dict(d, parent_key="", sep="."):
    """Flatten nested dictionary into dot-notation keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def compare_all_json_files(file_paths):
    """Compare multiple JSON files and find duplicate keys."""

    # Load and flatten all files
    all_data = {}
    for file_path in file_paths:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        all_data[file_path.name] = flatten_dict(data)

    # Find keys that appear in multiple files
    key_locations = defaultdict(list)

    for filename, flat_data in all_data.items():
        for key in flat_data.keys():
            key_locations[key].append((filename, flat_data[key]))

    # Filter to only keys that appear in 2+ files
    duplicates = {
        "metadata": [],  # Metadata fields (intentionally duplicated)
        "matching": [],  # Same key, same value across files
        "conflicting": [],  # Same key, different values
    }

    for key, locations in key_locations.items():
        if len(locations) < 2:
            continue  # Not a duplicate

        # Check if it's a metadata field
        if key.startswith("metadata."):
            duplicates["metadata"].append((key, locations))
            continue

        # Check if all values match
        first_value = locations[0][1]
        all_match = all(loc[1] == first_value for loc in locations)

        if all_match:
            duplicates["matching"].append((key, locations))
        else:
            duplicates["conflicting"].append((key, locations))

    return duplicates


def main():
    """Compare all JSON config files for duplicates."""

    print("=" * 80)
    print("COMPREHENSIVE JSON DUPLICATE CHECK")
    print("=" * 80)
    print()

    # List of all JSON config files
    json_files = [
        Path("game_rules.json"),
        Path("game_content.json"),
        Path("narrative_content.json"),
        Path("graphics_tiles.json"),
    ]

    # Check all files exist
    missing = [f for f in json_files if not f.exists()]
    if missing:
        print(f"WARNING: Missing files: {', '.join(str(f) for f in missing)}")
        json_files = [f for f in json_files if f.exists()]

    if len(json_files) < 2:
        print("ERROR: Need at least 2 JSON files to compare")
        return 1

    print(f"Comparing {len(json_files)} files:")
    for f in json_files:
        print(f"  - {f.name}")
    print()

    duplicates = compare_all_json_files(json_files)

    total_duplicates = (
        len(duplicates["metadata"]) + len(duplicates["matching"]) + len(duplicates["conflicting"])
    )

    if total_duplicates == 0:
        print("[OK] No duplicate keys found across files")
        return 0

    print(f"[INFO] Found {total_duplicates} duplicate keys across files")
    print()

    # Report conflicting duplicates (CRITICAL)
    if duplicates["conflicting"]:
        print("=" * 80)
        print(f"CONFLICTING DUPLICATES ({len(duplicates['conflicting'])})")
        print("Same key exists in multiple files with DIFFERENT values - CRITICAL ISSUE")
        print("=" * 80)
        print()

        for key, locations in duplicates["conflicting"]:
            print(f"Key: {key}")
            for filename, value in locations:
                print(f"  {filename}: {value}")
            print()

    # Report metadata duplicates (INTENTIONAL)
    if duplicates["metadata"]:
        print("=" * 80)
        print(f"METADATA DUPLICATES ({len(duplicates['metadata'])})")
        print("Metadata fields (version tracking) - INTENTIONAL")
        print("=" * 80)
        print()

        for key, locations in duplicates["metadata"]:
            print(f"Key: {key}")
            for filename, value in locations:
                print(f"  {filename}: {value}")
            print()

    # Report matching duplicates (REDUNDANT)
    if duplicates["matching"]:
        print("=" * 80)
        print(f"MATCHING DUPLICATES ({len(duplicates['matching'])})")
        print("Same key exists in multiple files with SAME value - REDUNDANT")
        print("=" * 80)
        print()

        for key, locations in duplicates["matching"]:
            print(f"Key: {key}")
            print(f"  Value: {locations[0][1]}")
            print(f"  Files: {', '.join(loc[0] for loc in locations)}")
            print()

    print("=" * 80)
    print("SUMMARY & RECOMMENDATIONS:")
    print("=" * 80)
    print()

    if duplicates["conflicting"]:
        print("CRITICAL: CONFLICTING DUPLICATES FOUND")
        print("  - Same key with different values in different files")
        print("  - Code may be using wrong value depending on load order")
        print("  - ACTION REQUIRED: Remove from one file, establish single source of truth")
        print()

    if duplicates["metadata"]:
        print("METADATA DUPLICATES:")
        print("  - These are intentional for version consistency tracking")
        print("  - test_config_consistency.py verifies versions match")
        print("  - NO ACTION NEEDED (working as designed)")
        print()

    if duplicates["matching"]:
        print("MATCHING DUPLICATES:")
        print("  - These are redundant but not breaking")
        print("  - Consider removing duplicates to reduce maintenance burden")
        print("  - ACTION OPTIONAL: Consolidate to single source of truth")
        print()

    if not duplicates["conflicting"]:
        print("[OK] No critical issues found - all duplicates are intentional or benign")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
