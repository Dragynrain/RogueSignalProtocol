#!/usr/bin/env python3
"""
Test that all colors referenced in code are defined in game_rules.json

This prevents KeyError crashes from missing color definitions.
"""

import json
import re
import pytest
from pathlib import Path


def load_defined_colors():
    """Load all colors defined in game_rules.json"""
    with open('game_rules.json', 'r') as f:
        data = json.load(f)

    colors = data.get('colors', {})
    all_colors = {}

    for category, items in colors.items():
        if category.startswith('_'):
            continue
        if isinstance(items, dict):
            all_colors[category] = set()
            for name, value in items.items():
                if name.startswith('_'):
                    continue
                if isinstance(value, list):
                    all_colors[category].add(name)

    return all_colors


def find_color_references():
    """Find all ColorManager.get() calls in Python source files"""
    references = {}

    # Pattern for ColorManager.get("category", "key")
    pattern = r'ColorManager\.get\(["\'](\w+)["\']\s*,\s*["\'](\w+)["\']\)'

    # Specialized method patterns
    specialized_patterns = {
        'get_basic_color': r'ColorManager\.get_basic_color\(["\'](\w+)["\']\)',
        'get_enemy_state_color': r'ColorManager\.get_enemy_state_color\(["\'](\w+)["\']\)',
        'get_exploit_color': r'ColorManager\.get_exploit_color\(["\'](\w+)["\']\)',
        'get_ui_color': r'ColorManager\.get_ui_color\(["\'](\w+)["\']\)',
        'get_tint_color': r'ColorManager\.get_tint_color\(["\'](\w+)["\']\)',
        'get_terrain_variant_color': r'ColorManager\.get_terrain_variant_color\(["\'](\w+)["\']\)',
    }

    method_to_category = {
        'get_basic_color': 'basic',
        'get_enemy_state_color': 'enemies',
        'get_exploit_color': 'exploits',
        'get_ui_color': 'ui',
        'get_tint_color': 'graphics_tint',
        'get_terrain_variant_color': 'terrain_variants',
    }

    for py_file in Path('.').rglob('*.py'):
        # Skip virtual environments and test files
        if 'venv' in str(py_file) or '.venv' in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8')
        except:
            continue

        # Remove comments to avoid false positives
        content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)

        # Find general get() calls
        for match in re.finditer(pattern, content_no_comments):
            category = match.group(1)
            key = match.group(2)

            if category not in references:
                references[category] = set()
            references[category].add(key)

        # Find specialized method calls
        for method, method_pattern in specialized_patterns.items():
            for match in re.finditer(method_pattern, content_no_comments):
                key = match.group(1)
                category = method_to_category[method]

                if category not in references:
                    references[category] = set()
                references[category].add(key)

    return references


def test_all_referenced_colors_are_defined():
    """
    Verify all ColorManager.get() calls reference colors that exist in game_rules.json

    This test prevents runtime KeyError crashes from missing color definitions.
    """
    defined = load_defined_colors()
    referenced = find_color_references()

    missing_colors = []

    for category in referenced:
        if category not in defined:
            missing_colors.append(f"Category '{category}' is missing entirely")
        else:
            missing_in_category = referenced[category] - defined[category]
            for color in missing_in_category:
                missing_colors.append(f"Color '{color}' missing in category '{category}'")

    if missing_colors:
        error_msg = "\n".join([
            "Missing color definitions found:",
            "",
            "The following colors are referenced in code but not defined in game_rules.json:",
            ""
        ] + [f"  - {msg}" for msg in sorted(missing_colors)] + [
            "",
            "Please add these colors to game_rules.json to prevent KeyError crashes."
        ])
        pytest.fail(error_msg)


def test_color_values_are_valid_rgb():
    """Verify all color values are valid RGB tuples [r, g, b]"""
    with open('game_rules.json', 'r') as f:
        data = json.load(f)

    colors = data.get('colors', {})
    invalid_colors = []

    for category, items in colors.items():
        if category.startswith('_'):
            continue
        if isinstance(items, dict):
            for name, value in items.items():
                if name.startswith('_'):
                    continue
                # Allow both lists and nested arrays (for pattern_colors, etc.)
                if isinstance(value, list):
                    if len(value) == 3 and all(isinstance(x, int) for x in value):
                        # Valid RGB tuple
                        if not all(0 <= x <= 255 for x in value):
                            invalid_colors.append(
                                f"{category}.{name} has values outside 0-255 range: {value}"
                            )
                    elif all(isinstance(x, list) for x in value):
                        # Nested array (like pattern_colors)
                        continue
                    else:
                        invalid_colors.append(
                            f"{category}.{name} is not a valid RGB tuple: {value}"
                        )

    if invalid_colors:
        error_msg = "\n".join([
            "Invalid RGB color values found:",
            ""
        ] + [f"  - {msg}" for msg in invalid_colors])
        pytest.fail(error_msg)


if __name__ == '__main__':
    # Allow running directly for debugging
    test_all_referenced_colors_are_defined()
    test_color_values_are_valid_rgb()
    print("[PASS] All color definition tests passed!")
