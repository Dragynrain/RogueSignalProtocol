#!/usr/bin/env python3
"""
Batch rename shadow → blind_spot across all test files.
Handles:
- shadow_step → system_hop
- data_mimic → traffic_masquerade
- noise_maker → decoy_swarm
- .shadows → .blind_spots
- is_shadow() → is_blind_spot()
- 'shadow' → 'blind_spot' (in context)
- shadow_master achievement → blind_spot_master
- ambushes_from_shadows → ambushes_from_blind_spots
- turns_in_shadows → turns_in_blind_spots
"""

import os
import re
from pathlib import Path

# Define replacement patterns
REPLACEMENTS = [
    # Exploit names (order matters - do exact matches first)
    (r'\bshadow_step\b', 'system_hop'),
    (r'\bdata_mimic\b', 'traffic_masquerade'),
    (r'\bnoise_maker\b', 'decoy_swarm'),

    # Map/method references
    (r'\.shadows\b', '.blind_spots'),
    (r'\bis_shadow\(', 'is_blind_spot('),
    (r'\bcreate_shadow_zones\b', 'create_blind_spot_zones'),
    (r'\bplace_shadow_areas\b', 'place_blind_spot_areas'),
    (r'\btrigger_first_shadow\b', 'trigger_first_blind_spot'),

    # Metrics
    (r'\bturns_in_shadows\b', 'turns_in_blind_spots'),
    (r'\bambushes_from_shadows\b', 'ambushes_from_blind_spots'),

    # Achievement
    (r'\bshadow_master\b', 'blind_spot_master'),

    # String literals and dictionaries (be careful with context)
    (r"'shadow'", "'blind_spot'"),
    (r'"shadow"', '"blind_spot"'),

    # Variable names
    (r'\bshadow_zone', 'blind_spot_zone'),
    (r'\bshadow_remembered\b', 'blind_spot_remembered'),
]

def process_file(file_path):
    """Process a single file with all replacements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        for pattern, replacement in REPLACEMENTS:
            content = re.sub(pattern, replacement, content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all test files."""
    base_dir = Path(__file__).parent
    tests_dir = base_dir / 'tests'

    if not tests_dir.exists():
        print(f"Tests directory not found: {tests_dir}")
        return

    updated_files = []

    # Process all test_*.py files
    for test_file in tests_dir.rglob('test_*.py'):
        if process_file(test_file):
            updated_files.append(test_file)
            print(f"Updated: {test_file.relative_to(base_dir)}")

    print(f"\n✓ Updated {len(updated_files)} test files")

if __name__ == '__main__':
    main()
