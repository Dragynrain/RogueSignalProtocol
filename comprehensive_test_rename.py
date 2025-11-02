#!/usr/bin/env python3
"""Comprehensive search-replace for ALL shadow/exploit references in tests."""

import os
import re
from pathlib import Path

# All replacement patterns - order matters!
REPLACEMENTS = [
    # Test method names
    (r'\btest_shadow_step', 'test_system_hop'),
    (r'\btest_data_mimic', 'test_traffic_masquerade'),
    (r'\btest_noise_maker', 'test_decoy_swarm'),

    # Exploit method calls
    (r'_execute_shadow_step', '_execute_system_hop'),
    (r'_execute_data_mimic', '_execute_traffic_masquerade'),
    (r'_execute_noise_maker', '_execute_decoy_swarm'),

    # Exploit names in strings and identifiers
    (r'\bshadow_step\b', 'system_hop'),
    (r'\bdata_mimic\b', 'traffic_masquerade'),
    (r'\bnoise_maker\b', 'decoy_swarm'),

    # Display names in assertions/messages
    (r'"Shadow Step"', '"System Hop"'),
    (r"'Shadow Step'", "'System Hop'"),
    (r'"Data Mimic"', '"Traffic Masquerade"'),
    (r"'Data Mimic'", "'Traffic Masquerade'"),
    (r'"Noise Maker"', '"Decoy Swarm"'),
    (r"'Noise Maker'", "'Decoy Swarm'"),

    # Sound effects
    (r'exploit_shadow_step', 'exploit_system_hop'),
    (r'exploit_data_mimic', 'exploit_traffic_masquerade'),
    (r'exploit_noise_maker', 'exploit_decoy_swarm'),

    # Map/shadow references
    (r'\.shadows\b', '.blind_spots'),
    (r'\bis_shadow\(', 'is_blind_spot('),
    (r'\bshadow_zone', 'blind_spot_zone'),

    # Metrics
    (r'\bturns_in_shadows\b', 'turns_in_blind_spots'),
    (r'\bambushes_from_shadows\b', 'ambushes_from_blind_spots'),

    # Achievement
    (r'\bshadow_master\b', 'blind_spot_master'),

    # Temporary effect keys
    (r'\bdata_mimic_turns\b', 'traffic_masquerade_turns'),

    # String literals
    (r'"shadow"', '"blind_spot"'),
    (r"'shadow'", "'blind_spot'"),

    # Comments and docstrings (case-insensitive where appropriate)
    (r'Shadow step', 'System hop'),
    (r'shadow step', 'system hop'),
    (r'Data mimic', 'Traffic masquerade'),
    (r'data mimic', 'traffic masquerade'),
    (r'Noise maker', 'Decoy swarm'),
    (r'noise maker', 'decoy swarm'),

    # General shadow terminology
    (r'\bshadow zone', 'blind spot zone'),
    (r'\bShadow zone', 'Blind spot zone'),
    (r'\bshadow coverage', 'blind spot coverage'),
    (r'\bin shadows\b', 'in blind spots'),
    (r'\bfrom shadows\b', 'from blind spots'),
    (r'\bto shadow\b', 'to blind spot'),
    (r'\ba shadow\b', 'a blind spot'),
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

    print(f"\nTotal updated: {len(updated_files)} test files")

if __name__ == '__main__':
    main()
